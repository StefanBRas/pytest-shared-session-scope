from pytest_shared_session_scope import shared_json_scope_fixture

@shared_json_scope_fixture()
def my_fixture():
    return 123

