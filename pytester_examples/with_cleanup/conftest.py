"""Test that only exactly one worker does cleanup."""

from pytest_shared_session_scope import shared_session_scope_json
import datetime
import json

from pytest_shared_session_scope.types import CleanupToken, SetupToken


@shared_session_scope_json()
def my_fixture(worker_id: str, results_dir):
    setup_token = yield
    if setup_token is SetupToken.FIRST:
        data = 123
    else:
        data = setup_token
    cleanup_token = yield data
    time = datetime.datetime.now().isoformat()
    (results_dir / f"{worker_id}.json").write_text(
        json.dumps(
            {
                "time": time,
                "is_cleanup_token": cleanup_token is CleanupToken.LAST,
                "is_setup_token": setup_token is SetupToken.FIRST,
            }
        )
    )
