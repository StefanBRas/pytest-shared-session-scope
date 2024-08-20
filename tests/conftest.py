from pytest_shared_session_scope import shared_json_scope_fixture
import pytest
from _pytest.fixtures import FixtureManager


pytest_plugins = ["pytester"]


@shared_json_scope_fixture()
def my_fixture_with_worker_id_storage(worker_id: str):
    yield worker_id


@pytest.fixture(scope="session")
def tmp_fixture():
    return 3

def _my_fixture_with_worker_id_storage(worker_id):
    yield worker_id


def pytest_collection_modifyitems(session: pytest.Session, config: pytest.Config, items: list[pytest.Item]):
    fixture_manager = session.config.pluginmanager.get_plugin("funcmanage")
    assert isinstance(fixture_manager, FixtureManager)
    for item in items:
        item.keywords


