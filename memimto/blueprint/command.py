from flask import Blueprint
from flask import request, make_response, current_app
from werkzeug.utils import secure_filename
from memimto.blueprint.utils import token_required
import logging
from memimto.models import db, Album
import os
from memimto.task import new_album, re_cluster_album

command_bp = Blueprint('command_bp', __name__)

@command_bp.route('/upload', methods=['POST'])
@token_required
def upload():
    if "Filename" in request.headers and "Chunkstart" in request.headers:
        file_name = secure_filename(request.headers["Filename"])
        file_size = int(request.headers["Filesize"])
        chunk_start = int(request.headers["Chunkstart"])
        chunk_size = int(request.headers["Chunksize"])

        with open(current_app.config["data_dir"] / file_name, 'ab') as f:
            f.seek(chunk_start)
            f.write(request.data)
        
        if chunk_start + chunk_size >= file_size:
            logging.info('Upload complete, creating album '+file_name)
            new_album.delay(file_name)
            
        return make_response(('Uploaded Chunk', 200))
    else:
        return make_response(('Missing header', 400))

@command_bp.route('/recluster/<int:album_id>', methods=['GET'])
@token_required
def recluster(album_id):
    logging.warning(f"Reclustering album {album_id}")
    re_cluster_album.delay(album_id)
    return make_response(("Recluster", 200))

@command_bp.route('/delete/<int:album_id>', methods=['GET'])
@token_required
def delete(album_id):
    album = Album.query.get_or_404(album_id)
    logging.warning(f"Delete album {album.name}")
    data_dir = current_app.config["data_dir"]
    for image in album.images:
        if os.path.exists(data_dir / image.name):
            os.remove(data_dir / image.name)
        else:
            logging.warning(f"Image {image.name} was not present")

    db.session.delete(album)
    db.session.commit()
    return make_response(("Recluster", 200))
