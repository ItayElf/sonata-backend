from typing import List
from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
from werkzeug.datastructures.file_storage import FileStorage
import sqlalchemy

from web.api.auth import get_user_by_email
from web.api.pieces import get_piece_by_id
from web.api.result import Result
from web.api.utils import get_data_keys, get_json_keys
from web.base import app, database, hasher
from web.exceptions import SonataAlreadyExistsException, SonataException, SonataNotFoundException
from web.models import User, Piece, File


def _commit_piece_changes():
    try:
        database.session.commit()
    except sqlalchemy.exc.IntegrityError as e:
        database.session.rollback()
        raise SonataAlreadyExistsException(
            "A piece with this name already exists for this instrument!") from e


def _upload_file(file: FileStorage) -> File:
    new_file = File(content=file.read())  # type: ignore
    database.session.add(new_file)
    database.session.commit()
    return new_file


def _edit_piece(user: User, new_piece: Piece):
    piece: Piece = get_piece_by_id(new_piece.id)
    if piece.user_id != user.id:
        raise SonataNotFoundException(
            f"Piece with ID {piece.id} not found for this user")

    piece.file_type = new_piece.file_type
    piece.file_id = new_piece.file_id
    _commit_piece_changes()
    return piece


def _check_file_size(file: FileStorage):
    max_file_size = 30 * (1024 * 1024)

    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    if size > max_file_size:
        raise SonataException(
            400, f"File too large! ({size / (1024*1024)}MB > 30MB)")
    return file


def _to_piece(piece_id: int, uploaded_file: FileStorage, stored_file: File) -> Piece:
    return Piece(id=piece_id, file_id=stored_file.id,
                 file_type=uploaded_file.content_type)  # type: ignore


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


@app.route("/api/files/upload_file", methods=["POST"])
@jwt_required()
def files_upload_file():
    result: Result[List[str]] = Result.instantiate(
        lambda: get_data_keys(request, ["id"])
    )
    file = request.files["file"]
    if not file.filename or not result.is_ok:
        return result
    piece_id_hash, = result.value
    piece_id, = hasher.decode(piece_id_hash)  # type: ignore

    user_result = Result.instantiate(get_jwt_identity) \
        .bind(get_user_by_email)
    if not user_result.is_ok:
        return result
    user = user_result.value

    return Result(file, 200) \
        .bind(_check_file_size) \
        .bind(_upload_file) \
        .bind(lambda x: _to_piece(piece_id, file, x)) \
        .bind(lambda x: _edit_piece(user, x)) \
        .bind(lambda x: x.to_dict()) \
        .jsonify()
