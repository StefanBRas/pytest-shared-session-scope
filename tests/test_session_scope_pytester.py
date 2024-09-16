from pathlib import Path
import pytest
from pytest import Pytester
import json


def copy_example(pytester: Pytester, test_id: str, tmp_path: Path):
    """Copy the example to a temporary directory and return the path

    Adds a fixture called "reuse" to the conftest.py file that returns the path to the results directory
    making it easier for tests to save results to be asserted on.
    """
    path = pytester.copy_example(test_id)
    result_dir = get_output_dir(tmp_path)
    conftest = path / "conftest.py"
    try:
        content = conftest.read_text()
    except FileNotFoundError:
        content = ""
    mocked_tmp_dir_factory = f"""

import pytest
from pathlib import Path

@pytest.fixture(scope="session")
def results_dir():
    p = Path("{result_dir}")
    p.parent.mkdir(exist_ok=True)
    p.mkdir(exist_ok=True)
    return p

{content}
"""
    conftest.write_text(mocked_tmp_dir_factory)
    return path


def get_output_dir(path: Path) -> Path:
    result_path = path / ".results"
    result_path.mkdir(exist_ok=True)
    return result_path


@pytest.mark.parametrize("n", [0, 2, 3])
def test_with_yield(pytester: Pytester, tmp_path, n: int):
    copy_example(pytester, "with_yield", tmp_path)
    pytester.runpytest("-n", str(n), "--basetemp", str(tmp_path)).assert_outcomes(passed=5)


@pytest.mark.parametrize("n", [0, 2, 3])
def test_with_return(pytester: Pytester, n: int, tmp_path: Path):
    pytester.copy_example("with_return")
    pytester.runpytest("-n", str(n), "--basetemp", str(tmp_path)).assert_outcomes(passed=5)


@pytest.mark.parametrize("n", [0, 2, 3])
def test_with_cleanup(pytester: Pytester, n: int, tmp_path):
    test_id = "with_cleanup"
    copy_example(pytester, test_id, tmp_path)
    res = pytester.runpytest("-n", str(n), "--basetemp", str(tmp_path))
    res.assert_outcomes(passed=5)

    results = {}
    for path in get_output_dir(tmp_path).iterdir():
        results[path.name] = json.loads(path.read_text())

    # Exactly one worker should calculate the value
    initial = {worker_id: data["time"] for worker_id, data in results.items() if data["initial"] is None}
    assert len(initial) == 1

    # Exactly one worker should do cleanup
    last = {worker_id: data["time"] for worker_id, data in results.items() if data["token"] == "last"}
    assert len(last) == 1
    # All other workers should get nothing as token
    not_last = {worker_id: data["time"] for worker_id, data in results.items() if data["token"] is None}
    assert len(not_last) == max(n - 1, 0)


@pytest.mark.parametrize("n", [0, 2, 3])
def test_serialize(pytester: Pytester, n: int, tmp_path: Path):
    pytester.copy_example("test_serializer.py")
    pytester.runpytest("-n", str(n), "--basetemp", str(tmp_path)).assert_outcomes(passed=8)


@pytest.mark.parametrize("n", [0, 2, 3])
def test_parse(pytester: Pytester, n: int, tmp_path: Path):
    pytester.copy_example("test_parse.py")
    pytester.runpytest("-n", str(n), "--basetemp", str(tmp_path)).assert_outcomes(passed=8)


@pytest.mark.parametrize("n", [0, 2, 3])
def test_use_fixture_in_fixture(pytester: Pytester, n: int, tmp_path: Path):
    pytester.copy_example("test_use_fixture_in_pytest_fixture.py")
    pytester.runpytest("-n", str(n), "--basetemp", str(tmp_path)).assert_outcomes(passed=3)


@pytest.mark.parametrize("n", [0, 2, 3])
def test_custom_store(pytester: Pytester, n: int, tmp_path: Path):
    pytester.copy_example("test_custom_store.py")
    pytester.runpytest("-n", str(n), "--basetemp", str(tmp_path)).assert_outcomes(passed=3)


@pytest.mark.parametrize("n", [0, 2, 3])
def test_cache(pytester: Pytester, n: int, tmp_path: Path):
    pytester.copy_example("test_cache.py")
    pytester.runpytest("-n", str(n), "--basetemp", str(tmp_path)).assert_outcomes(passed=3)
    # TODO: assert that we actually use the cache
    pytester.runpytest("-n", str(n), "--basetemp", str(tmp_path)).assert_outcomes(passed=3)


def test_nice_err_msg(pytester: Pytester):
    pytester.copy_example("test_nice_err_msg_on_single_yield.py")
    result = pytester.runpytest("-n", str(2))
    result.assert_outcomes(errors=1)
    result.stdout.fnmatch_lines(["*ValueError*MUST yield exactly twice*"])
