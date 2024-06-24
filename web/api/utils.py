from typing import Any, List

from flask import Request

from web.exceptions import SonataMissingParametersException


def get_json_keys(request: Request, keys: List[str]) -> List[Any]:
    data = request.get_json()
    try:
        return [data[key] for key in keys]
    except KeyError as e:
        raise SonataMissingParametersException("Missing fields") from e


def get_data_keys(request: Request, keys: List[str]) -> List[Any]:
    data = request.form
    try:
        return [data[key] for key in keys]
    except KeyError as e:
        raise SonataMissingParametersException("Missing fields") from e
