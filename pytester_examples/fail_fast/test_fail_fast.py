"""If we run with -x (fail fast), exactly one fixture should do cleanup"""

from pathlib import Path
import time

from pytest_shared_session_scope import shared_session_scope_json
from pytest_shared_session_scope.types import CleanupToken

delay = 0.1


@shared_session_scope_json()
def my_fixture_yield(results_dir: Path, worker_id):
    (results_dir / f"{worker_id}_start").touch()
    yield
    cleanup_token: CleanupToken = yield 1
    (results_dir / f"{worker_id}_cleanup_{cleanup_token}").touch()


def test_before_fail(my_fixture_yield):
    pass


def test_fail(my_fixture_yield):
    time.sleep(delay)
    assert False


def test_after_fail(my_fixture_yield, results_dir: Path, worker_id):
    (results_dir / f"{worker_id}_SHOULD_NOT_RUN").touch()


def test_fail_other_worker_1(my_fixture_yield):
    time.sleep(delay)


def test_fail_other_worker_2(my_fixture_yield):
    time.sleep(delay)

def test_fail_other_worker_3(my_fixture_yield):
    time.sleep(delay)

def test_fail_other_worker_4(my_fixture_yield, results_dir: Path, worker_id):
    (results_dir / f"{worker_id}_SHOULD_NOT_RUN").touch()
