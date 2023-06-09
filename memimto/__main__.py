#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from dotenv import load_dotenv
load_dotenv()

from memimto.models import db, User
from memimto.blueprint.command import command_bp
from memimto.blueprint.album import album_bp
from memimto.blueprint.account import account_bp
from memimto.celery import celery
import os

import argparse
from pathlib import Path

from flask import Flask
from logging.config import dictConfig
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS


dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi']
    }
})

data_dir = Path(os.environ.get("DATA_DIR"))

app = Flask(__name__)

if not os.path.exists(data_dir):
    os.mkdir(data_dir)

app.config["data_dir"] = data_dir
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DB_URI")
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")
db.init_app(app)

celery.init_app(app)

with app.app_context():
    db.create_all()
    if not User.query.filter_by(name="admin").first():
        admin_user = User(name="admin", password=os.environ.get("ADMIN_PASSWORD"))
        db.session.add(admin_user)
        db.session.commit()

app.register_blueprint(command_bp)
app.register_blueprint(album_bp)
app.register_blueprint(account_bp)

CORS(app)

def main():
    app.run("0.0.0.0", port=8000)

if __name__ == "__main__":
    main()