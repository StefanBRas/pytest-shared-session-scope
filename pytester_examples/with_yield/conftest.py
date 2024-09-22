from pytest_shared_session_scope import shared_session_scope_json
from pytest_shared_session_scope.types import SetupToken

@shared_session_scope_json()
def my_fixture():
    data = yield
    if data is SetupToken.FIRST:
        data = 123
    yield data

