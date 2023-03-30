import os
import shutil
import zipfile
from pathlib import Path
from flask import current_app
from memimto.celery import celery
from memimto.models import db, Album, Image, Face
from werkzeug.utils import secure_filename
import face_recognition
import pickle
from sklearn.cluster import OPTICS
from sklearn.gaussian_process import GaussianProcessClassifier
import numpy as np
from uuid import uuid4
import imghdr

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
    data_dir = Path(current_app.config["data_dir"])

    faces = {"image" : [], "encoding": []}
    for (i, image_name) in enumerate(image_list):
        if (i%10 == 0): 
            print(f"Album : {album.name}, Image : {i+1}/{len(image_list)}")
        
        image_db = Image(name=image_name, album=album)
        db_session.add(image_db)
        db_session.commit()

        image = face_recognition.load_image_file(data_dir / image_name)
        boxes = face_recognition.face_locations(image)
        encodings = face_recognition.face_encodings(image, boxes)
        
        faces["encoding"].extend(encodings)
        faces["image"].extend([image_db] * len(encodings))
    
    return faces

def cluster(album_db, faces, db_session):
    encodings = np.vstack(faces["encoding"])
    optics = OPTICS(xi=0.0000001, metric="correlation")
    optics.fit(encodings)

    labels = optics.labels_
    print(f"{len(np.unique(labels))-1} different faces detected")

    classifier = GaussianProcessClassifier()
    classifier.fit(encodings, labels)

    album_db.classifier = pickle.dumps(classifier)
    print("Save")
    faces_db = [Face(image=image, cluster=int(label)) for (label, image) in zip(labels, faces["image"])]
    db_session.add_all(faces_db)
    db_session.commit()

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
        print(e)