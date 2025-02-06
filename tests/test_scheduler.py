from collections import defaultdict
from typing import Iterable
from pytest import Pytester
import pytest
import re


def get_worker_to_test_id(lines: Iterable[str]) -> dict[str, set[str]]:
    worker_to_test: dict[str, set[str]] = defaultdict(set)
    for line in lines:
        # extract worker and test id from these:
        # [gw1] [100%] PASSED test_things.py::test_my_thing5
        if match := re.match(r"\[(.*?)\].* [A-Z]+ +([^ ]*)", line):
            worker_to_test[match.group(1)].add(match.group(2))
    return dict(worker_to_test)


def make_full_name(test_map: dict[str, set[str]], test_file: str) -> dict[str, set[str]]:
    return {key: {f"{test_file}.py::test_{test}" for test in tests} for key, tests in test_map.items()}


def test_scheduler(pytester: Pytester):
    pytester.copy_example("fixed_scheduler")
    result = pytester.runpytest("-n", str(2), "-vvv")
    result.assert_outcomes(passed=6)
    worker_to_test = get_worker_to_test_id(result.stdout.lines)
    assert len(worker_to_test["gw0"]) == 2
    assert len(worker_to_test["gw1"]) == 4


def test_scheduler2(pytester: Pytester):
    pytester.makeconftest("""
from pytest_shared_session_scope._scheduler import FixedScheduling


def pytest_xdist_make_scheduler(config, log):
    return FixedScheduling(
        config,
        [
            ["test_things.py::test_my_thing1", "test_things.py::test_my_thing6"],
            [
                "test_things.py::test_my_thing2",
                "test_things.py::test_my_thing3",
                "test_things.py::test_my_thing4",
                "test_things.py::test_my_thing5",
            ],
        ],
    )
                          """)
    pytester.makepyfile(
        test_things="""
def test_my_thing1(): ...
def test_my_thing2(): ...
def test_my_thing3(): ...
def test_my_thing4(): ...
def test_my_thing5(): ...
def test_my_thing6(): ...
                        """
    )
    result = pytester.runpytest("-n", str(2), "-vvv")
    result.assert_outcomes(passed=6)
    worker_to_test = get_worker_to_test_id(result.stdout.lines)
    assert len(worker_to_test["gw0"]) == 2
    assert len(worker_to_test["gw1"]) == 4


def test_exhaustive(pytester: Pytester):
    pytester.makeconftest("""
from pytest_shared_session_scope._scheduler import FixedScheduling


def pytest_xdist_make_scheduler(config, log):
    return FixedScheduling(
        config,
        exact_test_names=[
            ["test_things.py::test_my_thing1"]
        ],
    )
                          """)
    pytester.makepyfile(
        test_things="""
def test_my_thing1(): ...
def test_my_thing2(): ...
                        """
    )
    result = pytester.runpytest("-n", str(2), "-vvv")
    result.stdout.re_match_lines([".*exhaustive is True, but some tests were not mapped.*"])


def test_all_matcher_must_match(pytester: Pytester):
    pytester.makeconftest("""
from pytest_shared_session_scope._scheduler import FixedScheduling


def pytest_xdist_make_scheduler(config, log):
    return FixedScheduling(
        config,
        exact_test_names=[
            ["test_things.py::test_my_thing1"],
            ["test_things.py::test_my_thing2"]
        ],
        all_matchers_must_match=True
    )
                          """)
    pytester.makepyfile(
        test_things="""
def test_my_thing1(): ...
                        """
    )
    result = pytester.runpytest("-n", str(2), "-vvv")
    result.stdout.re_match_lines([".*all_matchers_must_match is True.*"])


@pytest.mark.parametrize(
    ["matchers", "tests", "expected"],
    [
        (
            {"literal_test_names": [["1"], ["2"]]},
            ["11", "1", "22", "2"],
            {"gw0": {"1", "11"}, "gw1": {"2", "22"}},
        ),
        (
            {
                "exact_test_names": [["test_file.py::test_22"], ["test_file.py::test_11"]],
                "literal_test_names": [["1"], ["2"]],
            },
            ["11", "1", "22", "2"],
            {"gw0": {"1", "22"}, "gw1": {"2", "11"}},
        ),
    ],
)
def test_scheduler_matchers(pytester: Pytester, matchers, tests, expected):
    pytester.makeconftest(f"""
from pytest_shared_session_scope._scheduler import FixedScheduling


def pytest_xdist_make_scheduler(config, log):
    return FixedScheduling(
        config,
        **{repr(matchers)}
    )
                          """)
    pytester.makepyfile(
        test_file="\n".join(f"def test_{test}(): ..." for test in tests),
    )
    result = pytester.runpytest("-n", str(2), "-vvv")
    result.assert_outcomes(passed=len(tests))
    worker_to_test = get_worker_to_test_id(result.stdout.lines)
    assert worker_to_test == make_full_name(expected, "test_file")
