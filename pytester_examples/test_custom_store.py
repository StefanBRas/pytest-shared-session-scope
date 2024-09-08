from typing import Any
from pytest_shared_session_scope import shared_session_scope_fixture
import polars as pl

from pytest_shared_session_scope.store import LocalFileStoreMixin
from pytest_shared_session_scope.types import StoreValueNotExists


class PolarsStore(LocalFileStoreMixin):
    def read(self, identifier: str, fixture_values: dict[str, Any]) -> pl.DataFrame:
        path = self._get_path(identifier, fixture_values["tmp_path_factory"])
        try:
            return pl.read_parquet(path)
        except FileNotFoundError:
            raise StoreValueNotExists()

    def write(self, identifier: str, data: pl.DataFrame, fixture_values: dict[str, Any]):
        path = self._get_path(identifier, fixture_values["tmp_path_factory"])
        data.write_parquet(path)


@shared_session_scope_fixture(PolarsStore())
def my_fixture():
    data = yield
    if data is None:
        data = pl.DataFrame({"a": [1, 2, 3]})
    yield data


def test_yield(my_fixture):
    assert isinstance(my_fixture, pl.DataFrame)


def test_yield_1(my_fixture):
    assert isinstance(my_fixture, pl.DataFrame)


def test_yield_2(my_fixture):
    assert isinstance(my_fixture, pl.DataFrame)
