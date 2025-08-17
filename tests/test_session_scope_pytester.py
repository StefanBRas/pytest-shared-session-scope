from pathlib import Path
import re
import pytest
from pytest import Pytester
import json


def _add_test_fixtures(conftest_path: Path, tmp_path: Path):
    """Copy the example to a temporary directory and return the path

    Adds a fixture called "reuse" to the conftest.py file that returns the path to the results directory
    making it easier for tests to save results to be asserted on.
    """
    result_dir = get_output_dir(tmp_path)
    try:
        content = conftest_path.read_text()
    except (FileNotFoundError, NotADirectoryError):
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
    conftest_path.write_text(mocked_tmp_dir_factory)


def copy_example(pytester: Pytester, test_id: str, tmp_path: Path):
    """Copy the example to a temporary directory and return the path

    Adds a fixture called "reuse" to the conftest.py file that returns the path to the results directory
    making it easier for tests to save results to be asserted on.
    """
    path = pytester.copy_example(test_id)
    _add_test_fixtures(path / "conftest.py", tmp_path)
    return path


def copy_example_from_markdown(markdown_path: Path, pytester: Pytester, test_id: str, tmp_path: Path):
    markdown_content = markdown_path.read_text().splitlines()
    code_block = ""
    block_start = [i for i, line in enumerate(markdown_content) if f"doctest:{test_id}" in line][0] + 1
    assert markdown_content[block_start].startswith("```python")
    for line in markdown_content[block_start + 1 :]:
        if line == "```":
            break
        code_block += line + "\n"
    test_dir_path = pytester.makepyfile(**{f"test_{test_id}": code_block})
    _add_test_fixtures(test_dir_path.parent / "conftest.py", tmp_path)


def copy_example_from_readme(pytester: Pytester, test_id: str, tmp_path: Path):
    markdown_path = Path(__file__).parent.parent / "README.md"
    return copy_example_from_markdown(markdown_path, pytester, test_id, tmp_path)


def get_output_dir(path: Path) -> Path:
    result_path = path / ".results"
    result_path.mkdir(exist_ok=True, parents=True)
    return result_path


def _get_tests_from_readme():
    markdown_path = Path(__file__).parent.parent / "README.md"
    markdown_content = markdown_path.read_text()
    return re.findall(r"doctest:([\w-]+)", markdown_content)


@pytest.mark.parametrize("test_id", _get_tests_from_readme())
def test_readme(tmp_path, pytester: Pytester, test_id: str):
    copy_example_from_readme(pytester, test_id, tmp_path)
    result = pytester.runpytest("-n", "2", "--basetemp", str(tmp_path))
    outcomes = result.parseoutcomes()
    assert outcomes.get("passed", 0) > 0
    assert outcomes.get("failed", 0) == 0
    assert outcomes.get("errors", 0) == 0


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
    got_setup_token = {
        worker_id: data["time"] for worker_id, data in results.items() if data["is_setup_token"]
    }
    assert len(got_setup_token) == 1

    # Exactly one worker should do cleanup
    got_cleanup_token = {
        worker_id: data["time"] for worker_id, data in results.items() if data["is_cleanup_token"]
    }
    assert len(got_cleanup_token) == 1


@pytest.mark.parametrize("n", [0, 2, 3])
def test_serialize(pytester: Pytester, n: int, tmp_path: Path):
    pytester.copy_example("test_serializer.py")
    pytester.runpytest("-n", str(n), "--basetemp", str(tmp_path)).assert_outcomes(passed=8)


@pytest.mark.parametrize("n", [0, 2, 3])
def test_use_fixture_in_fixture(pytester: Pytester, n: int, tmp_path: Path):
    pytester.copy_example("test_use_fixture_in_pytest_fixture.py")
    pytester.runpytest("-n", str(n), "--basetemp", str(tmp_path)).assert_outcomes(passed=3)


def test_nice_err_msg(pytester: Pytester):
    pytester.copy_example("test_nice_err_msg_on_single_yield.py")
    result = pytester.runpytest("-n", str(2))
    result.assert_outcomes(errors=1)
    result.stdout.fnmatch_lines(["*ValueError*MUST yield exactly twice*"])


@pytest.mark.parametrize("n", [0, pytest.param(2, marks=pytest.mark.xfail(reason="Issue #31"))])
def test_fail_fast(pytester: Pytester, n: int, tmp_path):
    # Test that we correctly do cleanup when using -x
    copy_example(pytester, "fail_fast", tmp_path)
    res = pytester.runpytest("-n", str(n), "--basetemp", str(tmp_path), "-x", "-vvv")
    assert res.parseoutcomes()["failed"] == 1
    assert res.parseoutcomes()["passed"] < 6
    # TODO: should also shows skipped, but the schedulor doesn't support that.

    results = [p.name for p in get_output_dir(tmp_path).iterdir()]

    should_not_have_been_run = [name for name in results if "SHOULD_NOT_RUN" in name]

    assert should_not_have_been_run == []

    # Exactly one worker should calculate the value
    got_setup_token = [name for name in results if name.endswith("start")]
    assert len(got_setup_token) == (n or 1)

    got_cleanup_token = [name for name in results if name.endswith("CleanupToken.LAST")]
    assert len(got_cleanup_token) == 1


@pytest.mark.parametrize("n", [0, pytest.param(2, marks=pytest.mark.xfail(reason="Issue #31"))])
def test_getfixturevalue(pytester: Pytester, n: int, tmp_path):
    copy_example(pytester, "getfixturevalue", tmp_path)
    res = pytester.runpytest("-n", str(n), "--basetemp", str(tmp_path), "-vvv", "-s")
    res.assert_outcomes(passed=6)

    results = [p.name for p in get_output_dir(tmp_path).iterdir()]
    got_setup_token = [name for name in results if name.endswith("start")]
    assert len(got_setup_token) == (n or 1)

    got_cleanup_token = [name for name in results if name.endswith("CleanupToken.LAST")]
    assert len(got_cleanup_token) == 1


@pytest.mark.parametrize("n", [0, 2])
def test_parameterize_fixture(pytester: Pytester, n: int, tmp_path):
    copy_example(pytester, "fixture_params", tmp_path)
    res = pytester.runpytest("-n", str(n), "--basetemp", str(tmp_path), "-vvv")
    res.assert_outcomes(passed=12)

    results = [p.name for p in get_output_dir(tmp_path).iterdir()]
    got_setup_token = [name for name in results if name.endswith("start")]
    assert len(got_setup_token) == (n or 1)

    got_cleanup_token = [name for name in results if name.endswith("CleanupToken.LAST")]
    assert len(got_cleanup_token) == 1
