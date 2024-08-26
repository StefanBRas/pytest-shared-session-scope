from pytest_shared_session_scope import shared_json_scope_fixture
from datetime import datetime


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

@shared_json_scope_fixture(
    deserialize=lambda x: datetime.fromisoformat(x),
    serialize=lambda x: x.isoformat()
)
def fixture_with_deserializor():
    data = yield
    if data is None:
        data = datetime.now()
    yield data

@shared_json_scope_fixture()
def fixture_with_return():
    return 1

