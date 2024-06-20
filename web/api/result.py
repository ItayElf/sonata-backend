from __future__ import annotations

from typing import Callable, Generic, NamedTuple, TypeVar

from flask.typing import ResponseReturnValue, ResponseValue

from web.exceptions import SonataException


_T = TypeVar("_T")
_U = TypeVar("_U")


class Result(NamedTuple, Generic[_T]):
    value: _T
    code: int

    @property
    def is_ok(self) -> bool:
        return self.code == 200

    @property
    def response_value(self) -> ResponseReturnValue:
        return self.value, self.code  # type: ignore

    def bind(self, func: Callable[[_T], _U]) -> Result[_U]:
        if not self.is_ok:
            return self  # type: ignore

        try:
            return Result(func(self.value), 200)  # type: ignore
        except SonataException as e:
            return Result(e.error_message, e.code)  # type: ignore

    @classmethod
    def instantiate(cls, func: Callable[..., _T]) -> Result[_T]:
        try:
            return cls(func(), 200)
        except SonataException as e:
            return cls(e.error_message, e.code)
