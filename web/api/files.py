from typing import List
from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
import sqlalchemy
from web.api.auth import get_user_by_email
from web.api.pieces import get_piece_by_id
from web.api.result import Result
from web.api.utils import get_json_keys
from web.base import app, database, hasher
from web.exceptions import SonataAlreadyExistsException, SonataNotFoundException
from web.models import User, Piece


def _commit_piece_changes():
    try:
        database.session.commit()
    except sqlalchemy.exc.IntegrityError as e:
        database.session.rollback()
        raise SonataAlreadyExistsException(
            "A piece with this name already exists for this instrument!") from e


def _edit_piece(user: User, new_piece: Piece):
    piece: Piece = get_piece_by_id(new_piece.id)
    if piece.user_id != user.id:
        raise SonataNotFoundException(
            f"Piece with ID {piece.id} not found for this user")

    piece.file_type = new_piece.file_type
    piece.file_id = new_piece.file_id
    _commit_piece_changes()
    return piece


@app.route("/api/files/upload_link", methods=["POST"])
@jwt_required()
def files_upload_link():
    result: Result[List[str]] = Result.instantiate(
        lambda: get_json_keys(request, ["id", "link"])
    )
    if not result.is_ok:
        return result
    piece_id_hash, link = result.value
    piece_id, = hasher.decode(piece_id_hash)  # type: ignore

    user_result = Result.instantiate(get_jwt_identity) \
        .bind(get_user_by_email)

    if not user_result.is_ok:
        return result
    user = user_result.value

    new_piece = Piece(user_id=-1, id=piece_id, file_type=link)  # type: ignore
    return Result.instantiate(lambda: _edit_piece(user, new_piece)) \
        .bind(lambda x: x.to_dict()) \
        .jsonify()
