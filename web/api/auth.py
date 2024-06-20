import hashlib
from typing import List

from flask import request, jsonify
from flask_jwt_extended import create_access_token

from web.base import app
from web.api.utils import get_json_keys
from web.exceptions import SonataUnauthorizedException
from web.models.user import User
from web.api.result import Result


def _get_user_by_email(email: str) -> User:
    user = User.query.filter_by(email=email).first()
    if user:
        return user
    raise SonataUnauthorizedException("Invalid Credentials")


def _check_password(password: str, salt: str, hashed: str):
    return hashlib.md5(password.encode() + salt.encode()).hexdigest() == hashed


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
