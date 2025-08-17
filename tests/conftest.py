from pytest_shared_session_scope import shared_session_scope_json, shared_session_scope_pickle
from datetime import datetime

from pytest_shared_session_scope.types import CleanupToken, SetupToken


pytest_plugins = ["pytester"]


@shared_session_scope_json()
def fixture_with_yield():
    data = yield
    if data is SetupToken.FIRST:
        data = 1
    yield data


@shared_session_scope_json()
def fixture_with_cleanup():
    data = yield
    if data is SetupToken.FIRST:
        data = 1
    token = yield data
    if token is CleanupToken.LAST:
        pass


@shared_session_scope_json(deserialize=lambda x: datetime.fromisoformat(x), serialize=lambda x: x.isoformat())
def fixture_with_deserializor():
    data = yield
    if data is SetupToken.FIRST:
        data = datetime.now()
    yield data


@shared_session_scope_json()
def fixture_with_return():
    return 1


class CustomPickleObject:
    def __init__(self, value):
        self.value = value

    def __eq__(self, other):
        return isinstance(other, CustomPickleObject) and self.value == other.value


@shared_session_scope_pickle()
def fixture_with_pickle():
    object_instance = yield
    if object_instance is SetupToken.FIRST:
        object_instance = CustomPickleObject(42)
    yield object_instance
