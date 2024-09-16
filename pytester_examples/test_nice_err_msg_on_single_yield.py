"""If we forget a yield, we should get a nice error message"""

from pytest_shared_session_scope import shared_session_scope_json


@shared_session_scope_json()
def fixture():
    yield [1, 2, 3]


def test(fixture):
    assert fixture == [1, 2, 3]
