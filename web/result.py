from __future__ import annotations

from typing import Callable, Generic, NamedTuple, TypeVar, Union

from web.exceptions import SonataException


_T = TypeVar("_T")
_U = TypeVar("_U")


class Result(NamedTuple, Generic[_T]):
    code: int
    value: Union[_T, str]

    @property
    def is_ok(self) -> bool:
        return self.code == 200

    def bind(self, func: Callable[[_T], _U]) -> Result[_U]:
        if not self.is_ok:
            return self  # type: ignore

        try:
            return Result(200, func(self.value))  # type: ignore
        except SonataException as e:
            return Result(e.code, e.error_message)
