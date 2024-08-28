from pytest_shared_session_scope import shared_json_scope_fixture

@shared_json_scope_fixture()
def my_fixture():
    data = yield
    if data is None:
        data = 123
    yield data

