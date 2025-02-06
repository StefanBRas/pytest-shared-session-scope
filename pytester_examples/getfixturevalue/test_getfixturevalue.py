"""If we run with -x (fail fast), exactly one fixture should do cleanup"""

from pathlib import Path
import time

from pytest_shared_session_scope import shared_session_scope_json
from pytest_shared_session_scope.types import CleanupToken

delay = 0.1


@shared_session_scope_json()
def my_fixture_yield(results_dir: Path, worker_id):
    (results_dir / f"{worker_id}_start").touch()
    yield 123 
    cleanup_token: CleanupToken = yield 123
    (results_dir / f"{worker_id}_cleanup_{cleanup_token}").touch()


def test_1(my_fixture_yield):
    assert my_fixture_yield == 123
def test_2(my_fixture_yield):
    assert my_fixture_yield == 123
def test_3(my_fixture_yield): 
    assert my_fixture_yield == 123


def test_other_1(request):
    time.sleep(delay)
    assert request.getfixturevalue("my_fixture_yield") == 123


def test_other_2(request):
    time.sleep(delay)
    assert request.getfixturevalue("my_fixture_yield") == 123


def test_other_3(request):
    time.sleep(delay)
    assert request.getfixturevalue("my_fixture_yield") == 123
