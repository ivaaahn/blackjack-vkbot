from app.database.gino import db


class AdminModel(db.Model):
    __tablename__ = "admins"
    id = db.Column(db.Integer(), primary_key=True)
    email = db.Column(db.String(), unique=True, nullable=False)
    password = db.Column(db.String(), nullable=False)
