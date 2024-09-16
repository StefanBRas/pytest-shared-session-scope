from pytest_shared_session_scope import shared_session_scope_json

@shared_session_scope_json()
def my_fixture():
    data = yield
    if data is None:
        data = 123
    yield data

