from filelock import FileLock
from pathlib import Path
import json
import uuid


class BetweenProcessCounter:
    def __init__(self, tmp_dir: Path):
        self.tmp_dir = tmp_dir
        random_name = str(uuid.uuid4())[:8]
        self.counter_location = self.tmp_dir / f"counter_{random_name}.json"
        self.file_lock = FileLock(str(self.counter_location) + ".lock")

    def get(self) -> int:
        with self.file_lock:
            if self.counter_location.is_file():
                return json.loads(self.counter_location.read_text())
            else:
                return 0

    def increment(self):
        with self.file_lock:
            counter = self.get()
            counter += 1
            self.counter_location.write_text(json.dumps(counter))
