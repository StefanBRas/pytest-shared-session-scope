import json
from pathlib import Path
from typing import Any


class FileStorageMixin:
    fixtures = ["tmp_path_factory"]

    def exists(self, key: str, fixture_values: dict[str, Any]) -> bool:
        return Path(key).exists()

    def get_key(self, func_qual_name: str, fixture_values: dict[str, Any]) -> str:
        root_tmp_dir = fixture_values["tmp_path_factory"].getbasetemp().parent
        return str(root_tmp_dir / f"{func_qual_name}.json")


class JsonStorage(FileStorageMixin):
    def read(self, key: str, fixture_values: dict[str, Any]) -> Any:
        return json.loads(Path(key).read_text())

    def write(self, key: str, data: Any, fixture_values: dict[str, Any]) -> Any:
        return Path(key).write_text(json.dumps(data))
