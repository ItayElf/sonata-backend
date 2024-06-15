from web.base import database


class User(database.Model):
    __tablename__ = 'users'
    id = database.Column(database.Integer, primary_key=True, nullable=False)
    email = database.Column(database.String, nullable=False, unique=True)
    name = database.Column(database.String, nullable=False, unique=True)
    password_hash = database.Column(database.String, nullable=False)
    salt = database.Column(database.String)

    pieces = database.relationship('Piece', backref='user', lazy=True)
