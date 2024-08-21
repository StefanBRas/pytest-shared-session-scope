from filelock import FileLock
from pathlib import Path
import json
import uuid

from pytest_shared_session_scope.utils import count_yields, has_yield_but_no_cleanup


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


def test_count_yields():
    def a():
        yield 1

    assert count_yields(a) == 1

    def b():
        yield 1
        yield 2
    
    assert count_yields(b) == 2

    def c():
        yield 1
        yield 2
        print("stuff")
        yield 3
        print("stuff")

    assert count_yields(c) == 3

    def no_yield():
        my_yield = 1

    assert count_yields(no_yield) == 0

def test_has_yield_but_no_clean_up():
    def a():
        yield 1

    def b():
        yield 1
        yield 2

    def c():
        yield 1
        yield 2
        print("stuff")
        yield 3

    assert has_yield_but_no_cleanup(a)
    assert has_yield_but_no_cleanup(b)
    assert has_yield_but_no_cleanup(c)

    def with_cleanup():
        yield 1
        yield 2
        print("stuff")
        yield 3
        print("stuff")

    def with_cleanup2():
        with open("a") as f:
            yield 3

    assert not has_yield_but_no_cleanup(with_cleanup)
    assert not has_yield_but_no_cleanup(with_cleanup2)

