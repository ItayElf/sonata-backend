import hashids

from web.base import database


class File(database.Model):
    __tablename__ = 'files'

    id = database.Column(database.Integer, primary_key=True,
                         autoincrement=True, nullable=False)
    content = database.Column(database.LargeBinary, nullable=False)

    pieces = database.relationship(
        'Piece', back_populates='file', lazy='dynamic')
    users = database.relationship(
        'User', back_populates='profile_picture', lazy='dynamic')

    def to_dict(self):
        return {
            'id': hashids.encode(self.id),
            'content': self.content
        }
