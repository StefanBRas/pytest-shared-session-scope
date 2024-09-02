"""If we forget a yield, we should get a nice error message"""

from pytest_shared_session_scope import shared_json_scope_fixture


@shared_json_scope_fixture()
def fixture():
    yield [1, 2, 3]


def test(fixture):
    assert fixture == [1, 2, 3]
