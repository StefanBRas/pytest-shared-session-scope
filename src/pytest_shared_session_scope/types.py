from collections.abc import Callable
from contextlib import AbstractContextManager
from typing import Any, Generic, Literal, Protocol, TypeAlias, TypeVar


class ValueNotExists(Exception): ...

Lock: TypeAlias = Callable[[str], AbstractContextManager]

CleanUp: TypeAlias = Literal['after']

_T = TypeVar("_T")

class Store(Protocol, Generic[_T]):

    @property
    def fixtures(self) -> list[str]:
        """ List of fixtures that the store needs. """
        ...
    def read(self, key: str, fixture_values: dict[str, Any]) -> _T:
        """ Read a value from the storage. 

        Raises:
            ValueNotExists: If the key is not found in the storage.
        """
        ...

    def write(self, key: str, data: _T, fixture_values: dict[str, Any]):
        """ Write a value to the storage. """
        ...

    def get_key(self, identifier: str, fixture_values: dict[str, Any]) -> str:
        """ Get the key for the storage. """
        ...
    def lock(self, key: str) -> AbstractContextManager:
        """ Lock to ensure atomicity. """
        ...


