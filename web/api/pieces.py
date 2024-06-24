from typing import Any, List
from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
import sqlalchemy
from web.api.auth import get_user_by_email
from web.api.result import Result
from web.api.tags import get_tag_by_id
from web.api.utils import get_json_keys
from web.base import app, database, hasher
from web.exceptions import SonataAlreadyExistsException, SonataNotFoundException
from web.models.piece import Piece
from web.models.tags import Tag
from web.models.user import User


def _decode_tags(tag_ids_str: List[str]) -> List[int]:
    return [hasher.decode(tag)[0] for tag in tag_ids_str]  # type: ignore


def _get_piece_by_id(piece_id: int):
    piece = Piece.query.filter_by(id=piece_id).first()
    if piece:
        return piece
    raise SonataNotFoundException(f"Piece with ID {piece_id} not found")


def _get_tags(user: User, tag_ids: List[int]) -> List[Tag]:
    tags = []
    for tag_id in tag_ids:
        tag = get_tag_by_id(tag_id)
        if tag.user_id != user.id:
            raise SonataNotFoundException(
                f"Tag with id {tag_id} not found for user")
        tags.append(tag)
    return tags


def _commit_piece_changes():
    try:
        database.session.commit()
    except sqlalchemy.exc.IntegrityError as e:
        database.session.rollback()
        raise SonataAlreadyExistsException(
            "A piece with this name already exists for this instrument!") from e


def _edit_piece(user: User, new_piece: Piece):
    piece: Piece = _get_piece_by_id(new_piece.id)
    if piece.user_id != user.id:
        raise SonataNotFoundException(
            f"Piece with ID {piece.id} not found for this user")

    piece.name = new_piece.name
    piece.description = new_piece.description
    piece.tags = new_piece.tags  # type: ignore
    piece.state = new_piece.state
    piece.instrument = new_piece.instrument
    _commit_piece_changes()
    return piece


def _add_piece(piece: Piece):
    database.session.add(piece)
    _commit_piece_changes()
    return piece


def _delete_piece(user: User, piece_id: int):
    piece: Piece = _get_piece_by_id(piece_id)
    if piece.user_id != user.id:
        raise SonataNotFoundException(
            f"Piece with ID {piece.id} not found for this user")
    database.session.delete(piece)
    database.session.commit()
    return ""


@app.route("/api/pieces/edit", methods=["POST"])
@jwt_required()
def pieces_edit():
    result: Result[List[Any]] = Result.instantiate(
        lambda: get_json_keys(
            request, ["id", "name", "description", "instrument", "state", "tag_ids"])
    )
    if not result.is_ok:
        return result
    piece_id_hash, name, description, instrument, state, tag_ids = result.value
    piece_id, = hasher.decode(piece_id_hash)  # type: ignore

    user_result = Result.instantiate(get_jwt_identity) \
        .bind(get_user_by_email)

    if not user_result.is_ok:
        return result
    user = user_result.value
    tags_result = Result(tag_ids, 200) \
        .bind(_decode_tags) \
        .bind(lambda x: _get_tags(user, x)) \

    if not tags_result.is_ok:
        return tags_result

    new_piece = Piece(id=piece_id, user_id=-1, name=name, description=description,
                      instrument=instrument, state=state, tags=tags_result.value)  # type: ignore
    return Result.instantiate(lambda: _edit_piece(user, new_piece)) \
        .bind(lambda x: x.to_dict()) \
        .jsonify()


@app.route("/api/pieces/add", methods=["POST"])
@jwt_required()
def pieces_add():
    result: Result[List[Any]] = Result.instantiate(
        lambda: get_json_keys(
            request, ["name", "description", "instrument", "state", "tag_ids"])
    )
    if not result.is_ok:
        return result

    name, description, instrument, state, tag_ids = result.value
    user_result = Result.instantiate(get_jwt_identity) \
        .bind(get_user_by_email)

    if not user_result.is_ok:
        return result
    user = user_result.value

    tags_result = Result(tag_ids, 200) \
        .bind(_decode_tags) \
        .bind(lambda x: _get_tags(user, x)) \

    if not tags_result.is_ok:
        return tags_result

    piece = Piece(
        name=name, description=description, instrument=instrument,
        state=state, tags=tags_result.value, user_id=user.id)  # type: ignore
    return Result.instantiate(lambda: _add_piece(piece)) \
        .bind(lambda x: x.to_dict()) \
        .jsonify()


@app.route("/api/pieces/delete", methods=["POST"])
@jwt_required()
def pieces_delete():
    result: Result[int] = Result.instantiate(
        lambda: get_json_keys(request, ["id"])
    ) \
        .bind(lambda x: x[0]) \
        .bind(hasher.decode) \
        .bind(lambda x: x[0])  # type: ignore
    if not result.is_ok:
        return result

    piece_id = result.value
    return Result.instantiate(get_jwt_identity) \
        .bind(get_user_by_email) \
        .bind(lambda x: _delete_piece(x, piece_id))
