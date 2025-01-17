from sqlalchemy.sql import func

from web.base import database, hasher


class Piece(database.Model):  # type: ignore
    __tablename__ = 'pieces'
    __table_args__ = (
        database.UniqueConstraint(
            'user_id', 'name', 'instrument', name='unique_piece_name_per_user'),
    )

    id = database.Column(database.Integer, primary_key=True,
                         autoincrement=True, nullable=False)
    name = database.Column(database.Text, nullable=False)
    description = database.Column(database.Text)
    instrument = database.Column(database.Text)
    state = database.Column(database.Integer, nullable=False)
    user_id = database.Column(
        database.Integer, database.ForeignKey('users.id'), nullable=False)
    added_at = database.Column(
        database.DateTime, nullable=False, default=func.now())  # pylint: disable=not-callable
    file_id = database.Column(
        database.Integer, database.ForeignKey('files.id'))
    file_type = database.Column(database.String)

    user = database.relationship('User', back_populates='pieces')
    file = database.relationship('File', back_populates='pieces')

    def to_dict(self):
        return {
            'id': hasher.encode(self.id),
            'name': self.name,
            'description': self.description,
            'instrument': self.instrument,
            'state': self.state,
            'user_id': hasher.encode(self.user_id),
            'added_at': self.added_at.isoformat(),
            'file_id': hasher.encode(self.file_id) if self.file_id else None,
            'file_type': self.file_type,
            "tags": [tag.to_dict() for tag in self.tags]  # type: ignore
        }
