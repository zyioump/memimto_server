from flask import Blueprint
from flask import request, current_app, abort, send_file
from memimto.models import db, Album, Image
import face_recognition
from base64 import b64decode
import os
import pickle
import logging
import PIL
import io
import numpy as np

album_bp = Blueprint('album_bp', __name__)

def to_json(ressource):
    return {i: ressource[i] for i in ressource}

@album_bp.route('/albums', methods=['GET'])
def albums():
    albums = Album.query.all()

    return [album.to_dict() for album in albums]

@album_bp.route('/album/<int:id>', methods=["GET"])
def album(id):
    album = Album.query.get_or_404(id)
    response = album.to_dict()
    response["images"] = [image.to_dict() for image in album.images]
    return response

@album_bp.route('/album/<int:album_id>/cluster/<int:cluster>', methods=["GET"])
def album_cluster(album_id, cluster):
    album = Album.query.get_or_404(album_id)
    response = album.to_dict()
    images = Image.query.filter(Image.faces.any(cluster=cluster), Image.album_id == album_id)
    response["images"] = [image.to_dict() for image in images]
    return response

@album_bp.route('/album/<int:album_id>/find_cluster', methods=["POST"])
def find_cluster(album_id):
    album = Album.query.get_or_404(album_id)
    if album.classifier is None:
        return {"cluster": -1}
    
    with open(current_app.config["data_dir"] / album.classifier, "rb") as classifier_file:
        classifier = pickle.load(classifier_file)

    image_b64 = request.data.decode().split("base64,")[1]
    image_data = b64decode(image_b64)
    image = PIL.Image.open(io.BytesIO(image_data))
    image = np.array(image.convert("RGB"))
    boxes = face_recognition.face_locations(image)
    if len(boxes) > 0:
        encodings = face_recognition.face_encodings(image, boxes)
        cluster = classifier.predict(encodings)
        logging.warning(f"Cluster detected : {cluster} for album {album_id}")
        return {"cluster": int(cluster[0])}
    else:
        logging.warning("No face detected")
        return {"cluster": -1}

@album_bp.route('/image/<name>')
def image(name):
    image_path = current_app.config["data_dir"] / name
    if os.path.exists(image_path):
        return send_file(image_path)
    else:
        return abort(404)
