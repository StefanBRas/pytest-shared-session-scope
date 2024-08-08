from pytest_shared_session_scope import shared_json_scope_fixture
import pytest


pytest_plugins = ["pytester"]


@shared_json_scope_fixture()
def my_fixture_with_worker_id_storage(worker_id):
    yield worker_id


@pytest.fixture(scope="session")
def tmp_fixture():
    return 3


def _my_fixture_with_worker_id_storage(worker_id):
    yield worker_id
