"""If we run with -x (fail fast), exactly one fixture should do cleanup"""

from pathlib import Path
import pytest

from pytest_shared_session_scope import shared_session_scope_json
from pytest_shared_session_scope.types import CleanupToken

delay = 0.1


@shared_session_scope_json(params=["a", "b"])
def my_fixture_yield(results_dir: Path, worker_id, request):
    (results_dir / f"{worker_id}_start").touch()
    yield request.param
    cleanup_token: CleanupToken = yield request.param
    (results_dir / f"{worker_id}_cleanup_{cleanup_token}").touch()


@pytest.fixture
def save_result_path(request, results_dir: Path):
    def _save_val(val):
        (results_dir / f"{request.function.__name__}_val_{val}").touch()

    return _save_val


def test_1(my_fixture_yield, save_result_path):
    assert my_fixture_yield in ["a", "b"]
    save_result_path(my_fixture_yield)


def test_2(my_fixture_yield, save_result_path):
    assert my_fixture_yield in ["a", "b"]
    save_result_path(my_fixture_yield)


def test_3(my_fixture_yield, save_result_path):
    assert my_fixture_yield in ["a", "b"]
    save_result_path(my_fixture_yield)


def test_other_1(my_fixture_yield, save_result_path):
    assert my_fixture_yield in ["a", "b"]
    save_result_path(my_fixture_yield)


def test_other_2(my_fixture_yield, save_result_path):
    assert my_fixture_yield in ["a", "b"]
    save_result_path(my_fixture_yield)


def test_other_3(my_fixture_yield, save_result_path):
    assert my_fixture_yield in ["a", "b"]
    save_result_path(my_fixture_yield)
