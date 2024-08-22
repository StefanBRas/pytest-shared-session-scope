from contextlib import contextmanager
import json
from pathlib import Path
from typing import Any
from filelock import FileLock as _FileLock

from pytest_shared_session_scope.types import Store, ValueNotExists


class LocalFileStoreMixin:
    @property
    def fixtures(self) -> list[str]:
        return ["tmp_path_factory"]

    def get_key(self, identifier: str, fixture_values: dict[str, Any]) -> str:
        root_tmp_dir = fixture_values["tmp_path_factory"].getbasetemp().parent
        return str(root_tmp_dir / f"{identifier}.json")

    @contextmanager
    def lock(self, key: str):
        with _FileLock(key + ".lock"):
            yield


class JsonStore(LocalFileStoreMixin):
    def read(self, key: str, fixture_values: dict[str, Any]) -> Any:
        try:
            return json.loads(Path(key).read_text())
        except FileNotFoundError:
            raise ValueNotExists

    def write(self, key: str, data: Any, fixture_values: dict[str, Any]) -> Any:
        Path(key).write_text(json.dumps(data))
        return data

x = JsonStore()

def a(a: Store):
    ...

a(x)
