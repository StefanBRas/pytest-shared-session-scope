# from xdist.newhooks import pytest_xdist_make_scheduler
from __future__ import annotations
from typing import TYPE_CHECKING
import pytest

if TYPE_CHECKING:
    from xdist.newhooks import Scheduling
    from xdist.remote import Producer

from pytest_shared_session_scope._scheduler import FixedScheduling


def pytest_xdist_make_scheduler(config: pytest.Config, log: Producer) -> Scheduling | None:
    """Return a node scheduler implementation."""
    return FixedScheduling(
        config,
        [
            ["test_things.py::test_my_thing1", "test_things.py::test_my_thing6"],
            [
                "test_things.py::test_my_thing2",
                "test_things.py::test_my_thing3",
                "test_things.py::test_my_thing4",
                "test_things.py::test_my_thing5",
            ],
        ],
    )
