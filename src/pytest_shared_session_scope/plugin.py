"""Pytest plugin specific things go here.

An pytest entrypoint points to this file
"""

import pytest
from pytest_shared_session_scope._types import tests_started


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_protocol(item, nextitem):
    item.config.stash.setdefault(tests_started, []).append(item.nodeid)
