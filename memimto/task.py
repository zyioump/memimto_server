import os
import shutil
import zipfile
from pathlib import Path
from flask import current_app
from memimto.celery import celery
from memimto.models import db, Album, Image, Face
from werkzeug.utils import secure_filename
import pickle
from sklearn.cluster import OPTICS
from sklearn.gaussian_process import GaussianProcessClassifier
import numpy as np
from uuid import uuid4
import imghdr
import logging

def unzip(file_name, album_name):
    data_dir = Path(current_app.config["data_dir"])
    image_list = []
    with zipfile.ZipFile(data_dir / file_name) as zip_file:
        for member in zip_file.namelist():
            filename = os.path.basename(member)
            # skip directories
            if not filename:
                continue
            
            extension = filename.split(".")[1]
            filename = str(uuid4()) + "." + extension
        
            # copy file (taken from zipfile's extract)
            source = zip_file.open(member)
            target = open(data_dir / filename, "wb")
            with source, target:
                shutil.copyfileobj(source, target)
            
            if imghdr.what(data_dir / filename):
                image_list.append(filename)
            else:
                os.remove(data_dir / filename)
    
    os.remove(data_dir / file_name)
    return image_list

def extract_face(image_list, album, db_session):
    import face_recognition
    data_dir = Path(current_app.config["data_dir"])

    faces = []
    for (i, image_name) in enumerate(image_list):
        if (i%10 == 0 or True): 
            print(f"Album : {album.name}, Image : {i+1}/{len(image_list)}")
        image = face_recognition.load_image_file(data_dir / image_name)
        boxes = face_recognition.face_locations(image, model="cnn")
        encodings = face_recognition.face_encodings(image, boxes)
    
        image_db = Image(name=image_name, album=album)
        db_session.add(image_db)

        faces_db = [Face(image=image_db, encoding=pickle.dumps(encoding)) for encoding in encodings]
        db_session.add_all(faces_db)

        faces.extend(faces_db)

        db_session.commit()
    return faces

def cluster(album_db, faces_db, db_session):
    encodings = [pickle.loads(face.encoding) for face in faces_db]
    encodings = np.vstack(encodings)
    optics = OPTICS(xi=0.0000001, metric="correlation")
    optics.fit(encodings)

    labels = optics.labels_
    print(f"{len(np.unique(labels))-1} different faces detected")

    for i, label in enumerate(labels):
        faces_db[i].cluster = label
    
    db_session.commit()

    print("Train classifier")
    classifier = GaussianProcessClassifier()
    classifier.fit(encodings, labels)

    print("Save")
    classifier_name = str(uuid4()) + ".pickle"

    album_db.classifier = classifier_name

    with open(current_app.config["data_dir"] / classifier_name, "wb") as classifier_file:
        pickle.dump(classifier, classifier_file)

    db_session.commit()

@celery.task()
def re_cluster_album(album_id):
    try:
        album = Album.query.get_or_404(album_id)
        print(f"Reclustering album {album.name}")
        faces = []
        for image in album.images:
            faces.extend(image.faces)

        cluster(album, faces, db.session)
        print("Done")
    except Exception as e:
        logging.exception(e)

@celery.task()
def new_album(file_name):
    try:
        album_name = file_name.split(".")[0]
        print(f"New album : {album_name}")
        db_session = db.session
        album = Album(name=album_name.title())
        db_session.add(album)
        db_session.commit()
        print(f"Unzip : {album_name}")
        images_list = unzip(file_name, album_name)
        print(f"Extract and encode face : {album_name}")
        faces = extract_face(images_list, album, db_session)
        print(f"Clustering face : {album_name}")
        cluster(album, faces, db_session)
        print(f"Album {album_name} done")
    except Exception as e:
        logging.exception(e)