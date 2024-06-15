from web.base import database


class Piece(database.Model):
    __tablename__ = 'pieces'
    id = database.Column(database.Integer, primary_key=True, nullable=False)
    name = database.Column(database.String, nullable=False)
    tags = database.Column(database.String, nullable=False)
    instrument = database.Column(database.String)
    state = database.Column(database.Integer, nullable=False,
                            comment='todo, learning, or done')
    user_id = database.Column(
        database.Integer, database.ForeignKey('users.id'), nullable=False)
    file_id = database.Column(
        database.Integer, database.ForeignKey('files.id'))
