from typing import List

from flask import Request

from web.exceptions import SonataMissingParametersException


def get_json_keys(request: Request, keys: List[str]) -> List[str]:
    data = request.get_json()
    try:
        return [data[key] for key in keys]
    except KeyError as e:
        raise SonataMissingParametersException("Missing fields") from e
