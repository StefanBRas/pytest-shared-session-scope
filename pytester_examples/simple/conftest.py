import pytest

@pytest.fixture(scope="session")
def fix():
    yield 1
