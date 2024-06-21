from typing import List
from flask import request
from flask_jwt_extended import get_jwt_identity, jwt_required
import sqlalchemy
from web.api.auth import get_user_by_email
from web.api.result import Result
from web.api.utils import get_json_keys
from web.base import app, database, hasher
from web.exceptions import SonataAlreadyExistsException, SonataNotFoundException
from web.models.tags import Tag
from web.models.user import User


def _get_tag_by_id(tag_id: int) -> Tag:
    tag = Tag.query.filter_by(id=tag_id).first()
    if tag:
        return tag
    raise SonataNotFoundException(f"Tag with ID {tag_id} not found")


def _commit_tag_changes():
    try:
        database.session.commit()
    except sqlalchemy.exc.IntegrityError as e:
        database.session.rollback()
        raise SonataAlreadyExistsException(
            "A tag with this name already exists!") from e


def _edit_tag(user: User, new_tag: Tag):
    tag = _get_tag_by_id(new_tag.id)
    if tag.user_id != user.id:
        raise SonataNotFoundException(
            f"Tag with ID {new_tag.id} not found for this user")

    tag.tag = new_tag.tag
    tag.color = new_tag.color
    _commit_tag_changes()
    return tag


def _add_tag(user: User, tag: Tag):
    tag.user_id = user.id
    database.session.add(tag)
    _commit_tag_changes()
    return tag


def _delete_tag(user: User, tag_id: int):
    tag = _get_tag_by_id(tag_id)
    if tag.user_id != user.id:
        raise SonataNotFoundException(
            f"Tag with ID {tag_id} not found for this user")
    database.session.delete(tag)
    database.session.commit()
    return ""


@app.route("/api/tags/edit", methods=["POST"])
@jwt_required()
def tags_edit():
    result: Result[List[str]] = Result.instantiate(
        lambda: get_json_keys(request, ["id", "tag", "color"])
    )
    if not result.is_ok:
        return result
    tag_id_hash, name, color = result.value
    tag_id, = hasher.decode(tag_id_hash)  # type: ignore
    new_tag = Tag(id=tag_id, user_id=-1, tag=name, color=color)  # type: ignore

    return Result.instantiate(get_jwt_identity) \
        .bind(get_user_by_email) \
        .bind(lambda x: _edit_tag(x, new_tag)) \
        .bind(lambda x: x.to_dict()) \
        .jsonify()


@app.route("/api/tags/add", methods=["POST"])
@jwt_required()
def tags_add():
    result: Result[List[str]] = Result.instantiate(
        lambda: get_json_keys(request, ["tag", "color"])
    )
    if not result.is_ok:
        return result
    name, color = result.value
    new_tag = Tag(tag=name, color=color)  # type: ignore

    return Result.instantiate(get_jwt_identity) \
        .bind(get_user_by_email) \
        .bind(lambda x: _add_tag(x, new_tag)) \
        .bind(lambda x: x.to_dict()) \
        .jsonify()


@app.route("/api/tags/delete", methods=["POST"])
@jwt_required()
def tags_delete():
    result: Result[List[str]] = Result.instantiate(
        lambda: get_json_keys(request, ["id"])
    )
    if not result.is_ok:
        return result
    tag_id_hashed, = result.value
    tag_id, = hasher.decode(tag_id_hashed)  # type: ignore

    return Result.instantiate(get_jwt_identity) \
        .bind(get_user_by_email) \
        .bind(lambda x: _delete_tag(x, tag_id))
