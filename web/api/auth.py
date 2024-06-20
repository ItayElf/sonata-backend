import hashlib
import random
from string import printable
from typing import Any, Dict, List

from flask import request, jsonify
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
import sqlalchemy

from web.base import app, database
from web.api.utils import get_json_keys
from web.exceptions import SonataException, SonataUnauthorizedException
from web.models.user import User
from web.api.result import Result

_SALT_SIZE = 32


def _get_user_by_email(email: str) -> User:
    user = User.query.filter_by(email=email).first()
    if user:
        return user
    raise SonataUnauthorizedException("Invalid Credentials")


def _generate_new_salt() -> str:
    return "".join(random.choices(printable, k=_SALT_SIZE))


def _get_hash(password: str, salt: str) -> str:
    return hashlib.md5(password.encode() + salt.encode()).hexdigest()


def _check_password(password: str, salt: str, hashed: str):
    return _get_hash(password, salt) == hashed


def _get_full_user_dict(user: User) -> Dict[str, Any]:
    return {
        **user.to_dict(),
        "tags": [tag.to_dict() for tag in user.tags],  # type:ignore
        "pieces": [piece.to_dict for piece in user.pieces]  # type:ignore
    }


def _insert_new_user(user: User) -> User:
    try:
        database.session.add(user)
        database.session.commit()
        return user
    except sqlalchemy.exc.IntegrityError as e:
        database.session.rollback()
        if "users.name" in str(e):
            raise SonataException(400, "Username already taken") from e
        raise SonataException(
            400, "A user with this email already exists") from e


@app.route("/api/auth/login", methods=["POST"])
def auth_login():
    result: Result[List[str]] = Result.instantiate(
        lambda: get_json_keys(request, ["email", "password"])
    )
    if not result.is_ok:
        return result.response_value

    password = result.value[1]
    user_result = result.bind(lambda x: x[0]).bind(_get_user_by_email)
    if not user_result.is_ok:
        return user_result.response_value

    user = user_result.value
    if not _check_password(password, user.salt, user.password_hash):
        return "Invalid credentials", 401

    access_token = create_access_token(identity=user.email)
    return jsonify(access_token=access_token)


@app.route("/api/auth/register", methods=["POST"])
def auth_register():
    result: Result[List[str]] = Result.instantiate(
        lambda: get_json_keys(request, ["email", "name", "password"])
    )
    if not result.is_ok:
        return result.response_value
    email, name, password = result.value
    salt = _generate_new_salt()
    password = _get_hash(password, salt)
    user = User(email=email, name=name, password_hash=password,
                salt=salt)  # type: ignore
    return Result(user, 200) \
        .bind(_insert_new_user) \
        .bind(lambda x: create_access_token(x.email)) \
        .jsonify("access_token")


@app.route("/api/auth/current_user")
@jwt_required()
def auth_current_user():
    return Result.instantiate(get_jwt_identity) \
        .bind(_get_user_by_email) \
        .bind(_get_full_user_dict) \
        .jsonify()
