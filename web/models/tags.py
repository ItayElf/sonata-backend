from web.base import database, hasher
from web.models.piece import Piece


class Tag(database.Model):
    __tablename__ = 'tags'
    __table_args__ = (
        database.UniqueConstraint(
            'user_id', 'tag', name='unique_tag_name_per_user'),
    )

    id = database.Column(database.Integer, primary_key=True,
                         autoincrement=True, nullable=False)
    user_id = database.Column(
        database.Integer, database.ForeignKey('users.id'), nullable=False)
    tag = database.Column(database.Text, nullable=False)
    color = database.Column(database.Text, nullable=False)

    user = database.relationship('User', back_populates='tags', lazy='dynamic')

    def to_dict(self):
        return {
            'id': hasher.encode(self.id),
            'user_id': self.user_id,
            'tag': self.tag,
            'color': self.color
        }


# Creating relationships for the many-to-many association between pieces and tags
pieces_tags = database.Table('pieces_tags',
                             database.Column(
                                 'piece_id', database.Integer, database.ForeignKey('pieces.id')),
                             database.Column(
                                 'tag_id', database.Integer, database.ForeignKey('tags.id'))
                             )

Piece.tags = database.relationship('Tag', secondary=pieces_tags, backref=database.backref(  # type: ignore
    'pieces', lazy='dynamic'), lazy='dynamic')
Tag.pieces = database.relationship('Piece', secondary=pieces_tags, backref=database.backref(  # type: ignore
    'tags', lazy='dynamic'), lazy='dynamic')
