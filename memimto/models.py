from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

    def __init__(self, name, password):
        self.name = name
        self.password = generate_password_hash(password, method='sha256')

    @classmethod
    def authenticate(self, **kwargs):
        name = kwargs.get('name')
        password = kwargs.get('password')
        
        if not name or not password:
            return None

        user = self.query.filter_by(name=name).first()
        if not user or not check_password_hash(user.password, password):
            return None

        return user

    def to_dict(self):
        return dict(id=self.id, name=self.name)

class Album(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    classifier = db.Column(db.String(100))
    images = db.Relationship("Image", cascade="all,delete", backref="album")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "length": len(self.images),
            "sample": [image.to_dict() for image in self.images[0:4]],
            "classifier": self.classifier is not None
        }

class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    album_id = db.Column(db.Integer, db.ForeignKey("album.id"))
    faces = db.Relationship("Face", cascade="all,delete", backref="image")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "album_id": self.album_id,
            "face_number": len(self.faces)
        }

class Face(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cluster = db.Column(db.Integer)
    image_id = db.Column(db.Integer, db.ForeignKey("image.id"))
    encoding = db.Column((db.PickleType), nullable=False)
    boxe = db.Column((db.PickleType), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "cluster": self.cluster,
            "image_id": self.image_id
        }