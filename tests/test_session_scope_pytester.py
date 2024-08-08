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


@pytest.mark.parametrize("n", [2, 5, 10])
def test_only_one_worker_calculates(pytester: Pytester, tmp_path: Path, n: int):
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

    def create_test(i):
        return f"""
        def test_{i}(my_fixture, result_location):
            result_location.write_text(my_fixture)
        """

    pytester.makepyfile(**{f"test_file_{i}": create_test(i) for i in range(n)})

    # run all tests with pytest
    pytester.runpytest("-n", "2", "-s", "-v").assert_outcomes(passed=n)
    results = set()
    for p in tmp_path.glob("*"):
        results.add(p.read_text())
    assert len(results) == 1
