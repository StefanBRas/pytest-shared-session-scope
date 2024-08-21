from pytest import FixtureRequest
from typing import Any, TypedDict
from _pytest.nodes import Function

class _PytestRequestCacheFixtureValues(TypedDict):
    request: "FixtureRequest"


class PytestRequestCache:
    fixtures = ["request"]
    _sentinel = object()

    def get(self, key: str, fixture_values: _PytestRequestCacheFixtureValues) -> Any:
        val = fixture_values["request"].config.cache.get(key, self._sentinel)
        if val is self._sentinel:
            raise KeyError(key)
        return val

    def set(
        self, value: Any, key: str, fixture_values: _PytestRequestCacheFixtureValues
    ) -> Any:
        fixture_values["request"].config.cache.set(key, value)
        return value

    def get_key(self, func_qual_name: str, fixture_values: dict[str, Any]) -> str:
        return func_qual_name
