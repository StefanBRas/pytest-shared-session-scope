from pathlib import Path
from pytest_shared_session_scope import shared_json_scope_fixture
import pytest
from pytest_shared_session_scope.fixtures import shared_session_scope_fixture
from pytest_shared_session_scope.lock import FileLock
from pytest_shared_session_scope.store import JsonStore


pytest_plugins = ["pytester"]

@shared_json_scope_fixture()
def fixture_with_yield():
    data = yield
    if data is None:
        data = 1
    yield data

@shared_json_scope_fixture()
def fixture_with_cleanup():
    data = yield
    if data is None:
        data = 1
    token = yield data
    print("doing stuff")
    if token == 'last':
        print("do stuff only when last")

@shared_json_scope_fixture()
def fixture_with_return():
    return 1

@shared_session_scope_fixture(storage=JsonStore(), lock=FileLock)
def a():
    ...


