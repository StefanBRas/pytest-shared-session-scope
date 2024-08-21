from pytest_shared_session_scope import shared_json_scope_fixture
import pytest

def test_fixture_with_fixture_storage(my_fixture_with_worker_id_storage, tmp_fixture):
    assert tmp_fixture == 3

class CleanupException(Exception):
    pass

@shared_json_scope_fixture()
def fixture_with_cleanup(worker_id):
    yield 1
    print("Im doing stuff")


def test_fixture_with_cleanup(fixture_with_cleanup):
    assert fixture_with_cleanup == 1

def test_fixture_with_cleanup2(fixture_with_cleanup):
    assert fixture_with_cleanup == 1

def test_fixture_with_cleanup3(fixture_with_cleanup):
    assert fixture_with_cleanup == 1
