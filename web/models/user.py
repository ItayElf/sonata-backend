from sqlalchemy.sql import func
from web.base import database


class User(database.Model):
    __tablename__ = 'users'

    id = database.Column(database.Integer, primary_key=True,
                         autoincrement=True, nullable=False)
    email = database.Column(database.Text, nullable=False, unique=True)
    name = database.Column(database.Text, nullable=False, unique=True)
    password_hash = database.Column(database.Text, nullable=False)
    salt = database.Column(database.Text, nullable=False)
    joined_at = database.Column(
        database.DateTime, nullable=False, default=func.now())  # pylint: disable=not-callable
    profile_picture_id = database.Column(
        database.Integer, database.ForeignKey('files.id'))

    profile_picture = database.relationship(
        'File', back_populates='users', lazy='dynamic')
    pieces = database.relationship(
        'Piece', back_populates='user', lazy='dynamic')
    tags = database.relationship('Tag', back_populates='user', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'joined_at': self.joined_at.isoformat(),
            'profile_picture_id': self.profile_picture_id
        }
