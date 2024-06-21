from web.base import database, hasher


class File(database.Model):  # type: ignore
    __tablename__ = 'files'

    id = database.Column(database.Integer, primary_key=True,
                         autoincrement=True, nullable=False)
    content = database.Column(database.LargeBinary, nullable=False)

    def to_dict(self):
        return {
            'id': hasher.encode(self.id),
            'content': self.content
        }
