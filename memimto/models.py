from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Album(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    classifier = db.Column((db.PickleType))
    images = db.Relationship("Image", backref="album")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "length": len(self.images),
            "sample": [image.to_dict() for image in self.images[0:4]]
        }

class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    album_id = db.Column(db.Integer, db.ForeignKey("album.id"))
    faces = db.Relationship("Face", backref="image")

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

    def to_dict(self):
        return {
            "id": self.id,
            "cluster": self.cluster,
            "image_id": self.image_id
        }