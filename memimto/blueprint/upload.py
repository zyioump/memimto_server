from flask import Blueprint
from flask import request, make_response, current_app
from werkzeug.utils import secure_filename

from memimto.task import new_album 

upload_bp = Blueprint('upload_bp', __name__)

@upload_bp.route('/upload', methods=['POST'])
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
            current_app.logger.info('Upload complete, creating album')
            new_album.delay(file_name)
            
        return make_response(('Uploaded Chunk', 200))
    else:
        return make_response(('Missing header', 400))