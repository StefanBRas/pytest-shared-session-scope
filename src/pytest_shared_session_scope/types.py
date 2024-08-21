from collections.abc import Callable
from contextlib import AbstractContextManager
from typing import Any, Generic, Literal, Protocol, TypeAlias, TypeVar


_T = TypeVar("_T")


class ValueNotExists(Exception): ...


class Storage(Protocol, Generic[_T]):
    fixtures: list[str]

    def read(self, key: str, fixture_values: dict[str, Any]) -> _T: ...

    """ Read a value from the storage. 

    Raises:
        ValueNotExists: If the key is not found in the storage.
    """

    def write(self, key: str, data: _T, fixture_values: dict[str, Any]) -> _T: ...
    def get_key(self, func_qual_name: str, fixture_values: dict[str, Any]) -> str: ...
    def lock(self, key: str) -> AbstractContextManager: ...

Lock: TypeAlias = AbstractContextManager | Callable[[str], AbstractContextManager]


class Cache(Protocol, Generic[_T]):
    fixtures: list[str]

    def get(self, key: str, fixture_values: dict[str, Any]) -> _T: ...

    """ Get a value from the cache. 

    Raises:
        KeyError: If the key is not found in the cache.
    """

    def set(self, value: _T, key: str, fixture_values: dict[str, Any]) -> _T: ...
    def get_key(self, func_qual_name: str, fixture_values: dict[str, Any]) -> str: ...
    def lock(self, key: str) -> AbstractContextManager: ...

CleanUp: TypeAlias = Literal['after', 'immediately']


class Store(Protocol, Generic[_T]):
    fixtures: list[str]

    def read(self, key: str, fixture_values: dict[str, Any]) -> _T: ...

    """ Read a value from the storage. 

    Raises:
        ValueNotExists: If the key is not found in the storage.
    """

    def write(self, key: str, data: _T, fixture_values: dict[str, Any]) -> _T: ...
    def get_key(self, func_qual_name: str, fixture_values: dict[str, Any]) -> str: ...
    def lock(self, key: str) -> AbstractContextManager: ...
