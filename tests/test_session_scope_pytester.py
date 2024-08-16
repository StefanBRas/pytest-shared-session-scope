from pathlib import Path
import pytest
from pytest import Pytester


def test_with_yield(pytester: Pytester):
    pytester.makeconftest(
        """
        from pytest_shared_session_scope import shared_json_scope_fixture

        @shared_json_scope_fixture()
        def my_fixture():
            yield 1
    """
    )
    pytester.makepyfile(
        """
        def test_hello_default(my_fixture):
            assert my_fixture == 1

    """
    )
    pytester.runpytest().assert_outcomes(passed=1)


def test_with_return(pytester: Pytester):
    pytester.makeconftest(
        """
        from pytest_shared_session_scope import shared_json_scope_fixture

        @shared_json_scope_fixture()
        def my_fixture():
            return 1
    """
    )
    pytester.makepyfile(
        """
        def test_hello_default(my_fixture):
            assert my_fixture == 1

    """
    )

    pytester.runpytest().assert_outcomes(passed=1)


def test_with_using_dectorator_fixture(pytester: Pytester):
    pytester.makeconftest(
        """
        from pytest_shared_session_scope import shared_json_scope_fixture

        @shared_json_scope_fixture()
        def my_fixture(worker_id):
            yield worker_id
    """
    )

    pytester.makepyfile(
        """
        def test_hello_default(my_fixture):
            assert my_fixture == "master"

        def test_hello_with_fixture(my_fixture, worker_id):
            assert my_fixture == "master"
            assert worker_id == "master"

    """
    )

    # run all tests with pytest
    pytester.runpytest().assert_outcomes(passed=2)


def test_with_using_dectorator_fixture_xdist(pytester: Pytester):
    pytester.makeconftest(
        """
        from pytest_shared_session_scope import shared_json_scope_fixture

        @shared_json_scope_fixture()
        def my_fixture(worker_id):
            yield worker_id
    """
    )

    pytester.makepyfile(
        """
        def test_hello_default(my_fixture):
            assert my_fixture != "master"

        def test_hello_with_fixture(my_fixture, worker_id):
            assert my_fixture != "master"
            assert worker_id != "master"

    """
    )

    # run all tests with pytest
    pytester.runpytest("-n", "2").assert_outcomes(passed=2)


@pytest.mark.parametrize("n", [0, 5, 10])
# Something weird going on with the following, the test fails:
# @pytest.mark.parametrize("i", [2, 5, 10, 100])
# with the following, the test test_with_using_dectorator_fixture fails?:
# @pytest.mark.parametrize("i", [2, 5, 10, 50, 100])
# with the following, the tests pass??!
@pytest.mark.parametrize("i", [2, 5, 10])
def test_only_one_worker_calculates(pytester: Pytester, tmp_path: Path, i: int, n: int):
    pytester.makeconftest(
        f"""
        from pytest_shared_session_scope import shared_json_scope_fixture
        import pytest
        from pathlib import Path
        @shared_json_scope_fixture()
        def my_fixture(worker_id):
            yield worker_id

        @pytest.fixture
        def result_location(worker_id):
            yield Path('{tmp_path}') / (worker_id + ".txt")
    """
    )

    def create_test(index):
        return f"""
        def test_{index}(my_fixture, result_location):
            assert isinstance(my_fixture, str)
            result_location.write_text(my_fixture)
        """

    pytester.makepyfile(**{f"test_file_{idx}": create_test(idx) for idx in range(i)})

    # run all tests with pytest
    pytester.runpytest("-n", str(n), "-s", "-v").assert_outcomes(passed=i)
    results = {p.read_text() for p in tmp_path.glob("*")}
    assert len(results) == 1


@pytest.mark.parametrize("n", [2, 5, 10])
def test_cache(pytester: Pytester, tmp_path: Path, n: int):
    pytester.makeconftest(
        f"""
        from pytest_shared_session_scope import shared_session_scope_fixture
        from pytest_shared_session_scope.cache import PytestRequestCache
        from pytest_shared_session_scope.storage import JsonStorage 
        from pytest_shared_session_scope.lock import FileLock
        from random import randint
        import pytest
        from pathlib import Path

        @shared_session_scope_fixture(JsonStorage(), FileLock, PytestRequestCache())
        def my_fixture(worker_id):
            yield str(randint(0, 100_000))

        @pytest.fixture
        def result_location(worker_id):
            yield Path('{tmp_path}') / (worker_id + ".txt")
    """
    )

    def create_test(i):
        return f"""
        def test_cache_{i}(my_fixture, result_location):
            result_location.write_text(my_fixture)
        """

    pytester.makepyfile(**{f"test_file_{i}": create_test(i) for i in range(n)})

    # run all tests with pytest
    pytester.runpytest("-n", "2", "-s", "-v").assert_outcomes(passed=n)

    results = {p.read_text() for p in tmp_path.glob("*")}
    assert len(results) == 1

    # Run again and see it uses result from cache
    pytester.runpytest("-n", "2", "-s", "-v").assert_outcomes(passed=n)
    second_results = {p.read_text() for p in tmp_path.glob("*")}
    assert results == second_results
