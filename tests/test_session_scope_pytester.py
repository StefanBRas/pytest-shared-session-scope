from pathlib import Path
import pytest
from pytest import Pytester


def makeconftest(pytester: Pytester, source: str, id: str):
    mocked_tmp_dir_factory = f"""
import pytest
from pathlib import Path
@pytest.fixture(scope="session")
def tmp_path_factory(tmp_path_factory):
    original = tmp_path_factory.getbasetemp
    def mocked_getbasetemp():
        old = original()
        new = old.parent / "{id}" / old.stem
        new.parent.mkdir(exist_ok=True)
        new.mkdir(exist_ok=True)
        return new
    tmp_path_factory.getbasetemp = mocked_getbasetemp
    yield tmp_path_factory

"""
    pytester.makeconftest(mocked_tmp_dir_factory + "\n" + source)


def test_with_yield(pytester: Pytester):
    makeconftest(
        pytester,
        """from pytest_shared_session_scope import shared_json_scope_fixture

@shared_json_scope_fixture()
def my_fixture():
    data = yield
    if data is None:
        data = 123
    yield data
    """,
        id="test_with_yield",
    )

    pytester.makepyfile(
        """
        def test_with_yield(my_fixture):
            assert my_fixture == 123

    """
    )
    pytester.runpytest().assert_outcomes(passed=1)


def test_with_return(pytester: Pytester):
    makeconftest(
        pytester,
        """
from pytest_shared_session_scope import shared_json_scope_fixture

@shared_json_scope_fixture()
def my_fixture():
    return 15
""",
        id="test_with_return",
    )
    pytester.makepyfile(
        """
        def test_with_return(my_fixture):
            assert my_fixture == 15

    """
    )

    pytester.runpytest().assert_outcomes(passed=1)


@pytest.mark.parametrize("n", [0, 5, 10])
@pytest.mark.parametrize("i", [2, 5, 10, 50, 100])
def test_with_xdist(pytester: Pytester, tmp_path: Path, i: int, n: int):
    makeconftest(
        pytester,
        f"""
from pytest_shared_session_scope import shared_json_scope_fixture
import pytest
from pathlib import Path
@shared_json_scope_fixture()
def my_fixture(worker_id):
    data = yield
    if data is None:
        data = worker_id
        (Path('{tmp_path}') / worker_id).touch()
    yield data
    """,
        id=f"test_with_xdist_{i}_{n}",
    )

    def create_test(index):
        return f"""
        def test_{index}_a(my_fixture):
            assert isinstance(my_fixture, str)
        """

    pytester.makepyfile(**{f"test_file_{idx}": create_test(idx) for idx in range(i)})

    # run all tests with pytest
    pytester.runpytest("-n", str(n), "-s", "-v").assert_outcomes(passed=i)
    assert len(list(tmp_path.glob("*"))) == 1
