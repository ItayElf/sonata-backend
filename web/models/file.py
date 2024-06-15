from web.base import database


class File(database.Model):
    __tablename__ = 'files'
    id = database.Column(database.Integer, primary_key=True, nullable=False)
    content = database.Column(database.LargeBinary, nullable=False)

    pieces = database.relationship('Piece', backref='file', lazy=True)
