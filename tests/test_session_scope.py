from pytest_shared_session_scope import shared_json_scope_fixture

def test_fixture_with_fixture_storage(my_fixture_with_worker_id_storage, tmp_fixture):
    assert tmp_fixture == 3


@shared_json_scope_fixture()
def fixture_with_cleanup(worker_id):
    yield worker_id
    assert False

def test_fixture_with_cleanup(fixture_with_cleanup):
    assert fixture_with_cleanup

def test_fixture_with_cleanup2(fixture_with_cleanup):
    assert fixture_with_cleanup

def test_fixture_with_cleanup3(fixture_with_cleanup):
    assert fixture_with_cleanup
