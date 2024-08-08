from collections.abc import Callable
from contextlib import AbstractContextManager
from typing import Any, Generic, Protocol, TypeAlias, TypeVar


_T = TypeVar("_T")


class Storage(Protocol, Generic[_T]):
    fixtures: list[str]

    def read(self, key: str, fixture_values: dict[str, Any]) -> _T: ...
    def write(self, key: str, data: _T, fixture_values: dict[str, Any]) -> _T: ...
    def exists(self, key: str, fixture_values: dict[str, Any]) -> bool: ...
    def get_key(self, func_qual_name: str, fixture_values: dict[str, Any]) -> str: ...


Lock: TypeAlias = AbstractContextManager | Callable[[str], AbstractContextManager]
