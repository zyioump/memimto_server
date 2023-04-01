from flask import request, current_app, abort, send_file, make_response, Blueprint
from memimto.models import User
from datetime import datetime, timedelta
import jwt

account_bp = Blueprint('account_bp', __name__)

@account_bp.route('/login/', methods=('POST',))
def login():
    data = request.form
    user = User.authenticate(**data)

    if not user:
        return make_response("Tutut" , 401)

    token = jwt.encode({
        'sub': user.name,
        'iat':datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(minutes=30)},
        current_app.config['SECRET_KEY'], algorithm="HS256")

    return {'token': token}