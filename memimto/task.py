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
from sklearn.linear_model import SGDClassifier
import numpy as np
import PIL.Image
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

def load_image_file(file, mode='RGB'):
    """
    Loads an image file (.jpg, .png, etc) into a numpy array
    :param file: image file name or file object to load
    :param mode: format to convert the image to. Only 'RGB' (8-bit RGB, 3 channels) and 'L' (black and white) are supported.
    :return: image contents as numpy array
    """

    im = PIL.Image.open(file)
    width, height = im.size
    w, h = width, height
    log = logging.getLogger()

    ratio = -1
    # Ratio for resize the image
    # Resize in case of to bigger dimension
    # In first instance manage the HIGH-Dimension photos
    if width > 3600 or height > 3600:
        if width > height:
            ratio = width / 800
        else:
            ratio = height / 800

    elif 1200 <= width <= 1600 or 1200 <= height <= 1600:
        ratio = 1 / 2
    elif 1600 <= width <= 3600 or 1600 <= height <= 3600:
        ratio = 1 / 3

    if 0 < ratio < 1:
        # Scale image in case of width > 1600
        w = width * ratio
        h = height * ratio
    elif ratio > 1:
        # Scale image in case of width > 3600
        w = width / ratio
        h = height / ratio
    if w != width:
        # Check if scaling was applied
        maxsize = (w, h)
        im.thumbnail(maxsize, PIL.Image.ANTIALIAS)

    if mode:
        im = im.convert(mode)

    return np.array(im)

def extract_face(image_list, album, db_session):
    import face_recognition
    data_dir = Path(current_app.config["data_dir"])

    faces = []
    for (i, image_name) in enumerate(image_list):
        if (i%10 == 0 or True): 
            print(f"Album : {album.name}, Image : {i+1}/{len(image_list)}")
        image = load_image_file(data_dir / image_name)
        boxes = face_recognition.face_locations(image, model="cnn")
        encodings = face_recognition.face_encodings(image, boxes)
    
        image_db = Image(name=image_name, album=album)
        db_session.add(image_db)

        faces_db = [Face(image=image_db, encoding=encoding, boxe=boxe) for encoding, boxe in zip(encodings, boxes)]
        db_session.add_all(faces_db)

        faces.extend(faces_db)

        db_session.commit()
    return faces

def cluster(album_db, faces_db, db_session):
    import face_recognition
    encodings = [face.encoding for face in faces_db]
    encodings = np.vstack(encodings)
    optics = OPTICS(xi=0.0000001, metric="correlation")
    optics.fit(encodings)

    labels = optics.labels_
    print(f"{len(np.unique(labels))-1} different faces detected")

    unknow_encodings = encodings[labels == -1]
    unknow_indices = np.argwhere(labels == -1)
    know_encodings = encodings[labels != -1]
    know_label = labels[labels != -1]
    
    for i, encoding in zip(unknow_indices, unknow_encodings):
        comparaison = np.array(face_recognition.compare_faces(know_encodings, encoding))
        label_match = know_label[comparaison]

        if len(label_match) > 0:
            label, count = np.unique(label_match, return_counts=True)
            max_count_indice = np.argmax(count)
            if count[max_count_indice] / len(labels[labels == label[max_count_indice]]) > 0.3:
                labels[i] = label[max_count_indice]

    for i, label in enumerate(labels):
        faces_db[i].cluster = label
    
    db_session.commit()

    print("Train classifier")
    classifier = SGDClassifier()
    classifier.fit(encodings, labels)

    print(f"Save, classifier score : {classifier.score(encodings, labels)}")
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