from pytest_shared_session_scope import shared_session_scope_json
from datetime import datetime


def serialize(value: datetime) -> str:
    return value.isoformat()


def deserialize(value: str) -> datetime:
    return datetime.fromisoformat(value)


@shared_session_scope_json(serialize=serialize, deserialize=deserialize)
def my_fixture_return():
    return datetime.now()

@shared_session_scope_json(serialize=serialize, deserialize=deserialize)
def my_fixture_yield():
    data = yield
    if data is None:
        data = datetime.now()
    yield data.now()

def test_return(my_fixture_return):
    assert isinstance(my_fixture_return, datetime)

def test_yield(my_fixture_yield):
    assert isinstance(my_fixture_yield, datetime)

def test_return_1(my_fixture_return):
    assert isinstance(my_fixture_return, datetime)

def test_yield_1(my_fixture_yield):
    assert isinstance(my_fixture_yield, datetime)

def test_return_2(my_fixture_return):
    assert isinstance(my_fixture_return, datetime)

def test_yield_2(my_fixture_yield):
    assert isinstance(my_fixture_yield, datetime)

def test_return_3(my_fixture_return):
    assert isinstance(my_fixture_return, datetime)

def test_yield_3(my_fixture_yield):
    assert isinstance(my_fixture_yield, datetime)
