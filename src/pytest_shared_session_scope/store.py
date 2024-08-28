"""Stores for sharing data between pytest sessions."""

from contextlib import contextmanager
import json
from pathlib import Path
from typing import Any
from filelock import FileLock as _FileLock
from pytest import TempPathFactory

from pytest_shared_session_scope.types import StoreValueNotExists


class LocalFileStoreMixin:
    """Mixin for file based stores."""

    @property
    def fixtures(self) -> list[str]:
        """List of fixtures that the store needs."""
        return ["tmp_path_factory"]

    def _get_path(self, identifier: str, tmp_path_factory: TempPathFactory) -> Path:
        root_tmp_dir = tmp_path_factory.getbasetemp().parent
        return root_tmp_dir / f"{identifier}.json"

    @contextmanager
    def lock(self, identifier: str, fixture_values: dict[str, Any]):
        """Filelock to ensure atomicity."""
        path = self._get_path(identifier, fixture_values["tmp_path_factory"])
        with _FileLock(str(path) + ".lock"):
            yield


class FileStore(LocalFileStoreMixin):
    """Store that reads and writes data (as strings) from a file."""

    def read(self, identifier: str, fixture_values: dict[str, Any]) -> str:
        """Read data from a file."""
        path = self._get_path(identifier, fixture_values["tmp_path_factory"])
        try:
            return path.read_text()
        except FileNotFoundError:
            raise StoreValueNotExists

    def write(self, identifier: str, data: str, fixture_values: dict[str, Any]):
        """Write data to a file."""
        self._get_path(identifier, fixture_values["tmp_path_factory"]).write_text(data)


class JsonStore(FileStore):
    """Store that reads and writes json data using the buildin json module."""

    def read(self, identifier: str, fixture_values: dict[str, Any]) -> Any:
        """Read data from a file as json using json.loads."""
        return json.loads(super().read(identifier, fixture_values))

    def write(self, identifier: str, data: Any, fixture_values: dict[str, Any]):
        """Write data to a file as json using json.dumps."""
        super().write(identifier, json.dumps(data), fixture_values)
