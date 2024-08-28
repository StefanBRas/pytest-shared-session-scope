"""Test that only exactly one worker does cleanup."""

from pytest_shared_session_scope import shared_json_scope_fixture
import datetime
import json


@shared_json_scope_fixture()
def my_fixture(worker_id: str, results_dir):
    initial = yield
    if initial is None:
        data = 123
    else:
        data = initial
    token = yield data
    time = datetime.datetime.now().isoformat()
    (results_dir / f"{worker_id}.json").write_text(
        json.dumps({"time": time, "token": token, "initial": initial})
    )
