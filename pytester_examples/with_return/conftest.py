from pytest_shared_session_scope import shared_session_scope_json

@shared_session_scope_json()
def my_fixture():
    return 123

