from sqlalchemy.sql import func

from web.base import database, hasher


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

    pieces = database.relationship('Piece', back_populates='user')
    profile_picture = database.relationship(
        'File', foreign_keys=[profile_picture_id])

    def to_dict(self):
        return {
            'id': hasher.encode(self.id),
            'name': self.name,
            'joined_at': self.joined_at.isoformat(),
            'profile_picture_id': hasher.encode(self.profile_picture_id) if self.profile_picture_id else None
        }
