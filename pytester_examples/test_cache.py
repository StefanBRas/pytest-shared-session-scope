from pytest_shared_session_scope.fixtures import shared_session_scope_json

@shared_session_scope_json()
def my_fixture(pytestconfig):
    data = yield
    if data is None:
        data = pytestconfig.cache.get("example/value", None)
        if data is None:
            data = {"hey": "data"}
            pytestconfig.cache.set("example/value", data)
    yield data


def test_yield(my_fixture):
    assert my_fixture == {"hey": "data"}


def test_yield_1(my_fixture):
    assert my_fixture == {"hey": "data"}

def test_yield_2(my_fixture):
    assert my_fixture == {"hey": "data"}
