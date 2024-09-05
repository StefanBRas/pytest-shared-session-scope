from typing_extensions import Self

from pytest_shared_session_scope.fixtures import shared_session_scope_fixture
from pytest_shared_session_scope.store import FileStore
import json


def deserialize(value: str) -> dict:
    return json.loads(value)


def serialize(value: dict) -> str:
    return json.dumps(value)


class Connection:
    def __init__(self, port: int):
        self.port = port

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        return cls(**data)


@shared_session_scope_fixture(
    store=FileStore(),
    parse=Connection.from_dict,
    serialize=serialize,
    deserialize=deserialize,
)
def my_fixture_return():
    return {"port": 123}


@shared_session_scope_fixture(
    store=FileStore(),
    parse=Connection.from_dict,
    serialize=serialize,
    deserialize=deserialize,
)
def my_fixture_yield():
    data = yield
    if data is None:
        data = {"port": 123}
    yield data


def test_return(my_fixture_return):
    assert isinstance(my_fixture_return, Connection)


def test_yield(my_fixture_yield):
    assert isinstance(my_fixture_yield, Connection)


def test_return_1(my_fixture_return):
    assert isinstance(my_fixture_return, Connection)


def test_yield_1(my_fixture_yield):
    assert isinstance(my_fixture_yield, Connection)


def test_return_2(my_fixture_return):
    assert isinstance(my_fixture_return, Connection)


def test_yield_2(my_fixture_yield):
    assert isinstance(my_fixture_yield, Connection)


def test_return_3(my_fixture_return):
    assert isinstance(my_fixture_return, Connection)


def test_yield_3(my_fixture_yield):
    assert isinstance(my_fixture_yield, Connection)
