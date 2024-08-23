import functools
import typing
from contextlib import suppress
import inspect
from collections.abc import Callable
from functools import partial
import json
from typing import Any, Iterable, Optional, TypeVar
from typing_extensions import Generator

import pytest

from pytest_shared_session_scope._types import tests_started
from pytest_shared_session_scope.store import FileStore, JsonStore
from pytest_shared_session_scope.types import Store, ValueNotExists
from xdist import is_xdist_worker

_T = TypeVar("_T")
_V = TypeVar("_V")

def identity(v: _T) -> _T:
    return v

def _send_last(generator: Generator, value):
    with suppress(StopIteration):
        generator.send(value)
        msg = "This generator should have been exhausted"
        raise AssertionError(msg)

def _get_tests_for_fixture(fixture, request: pytest.FixtureRequest) -> list[str]:
    return list({item.nodeid for item in request.session.items if fixture.__name__ in item.fixturenames})

def _add_fixture_to_signature(func, fixture_names: Iterable[str]):
    signature = inspect.signature(func)
    parameters = []
    extra_params = []
    for p in signature.parameters.values():
        if p.kind <= inspect.Parameter.KEYWORD_ONLY:
            parameters.append(p)
        else:
            extra_params.append(p)

    for fixture in fixture_names:
        if fixture not in inspect.signature(func).parameters.keys():
            extra_params.append(
                inspect.Parameter(fixture, inspect.Parameter.POSITIONAL_OR_KEYWORD)
            )
    parameters.extend(extra_params)
    return signature.replace(parameters=parameters)

def shared_session_scope_fixture(
    store: Store[_T],
    serialize: Callable[[_V], _T] = identity,
    deserialize: Callable[[_T], _V] = identity,
    metadata_storage: Store[str] = FileStore(),
    **kwargs,
):
    # TODO: add docstrings here
    def _inner(func: Callable):
        fixture_names = set(store.fixtures) | set(metadata_storage.fixtures) | {"request"}
        original_signature = inspect.signature(func)
        new_signature = _add_fixture_to_signature(func, fixture_names)
        func.__signature__ = new_signature # type: ignore

        if inspect.isgeneratorfunction(func):

            @pytest.fixture(scope="session", **kwargs)
            @functools.wraps(func)
            def wrapper_generator(*args, **kwargs):
                fixture_values = {k: kwargs[k] for k in fixture_names}
                print(fixture_values)
                new_kwargs = {
                    k: v for k, v in kwargs.items() if k in original_signature.parameters.keys()
                }
                print(new_kwargs)
                request = typing.cast(pytest.FixtureRequest, fixture_values["request"])

                if not is_xdist_worker(request):  # Not running with xdist, early return
                    res = func(*args, **new_kwargs)
                    next(res)
                    data = res.send(None)
                    yield data
                    _send_last(res, "last")
                    return

                tests_using_fixture = _get_tests_for_fixture(func, request)

                unique_id = f"{func.__module__}.{func.__qualname__}"

                storage_key = store.get_key(unique_id, fixture_values)
                metadata_key = store.get_key(unique_id + "_metadata", fixture_values)

                with (store.lock(storage_key), metadata_storage.lock(metadata_key)):
                    res = func(*args, **new_kwargs)
                    next(res)
                    try:
                        data = deserialize(store.read(storage_key, fixture_values))
                        also_data = res.send(data)
                        # TODO: maybe remove this, mostly for testing but it costs one extra deserialtion step
                        assert data == deserialize(also_data)
                    except ValueNotExists:
                        data = res.send(None)
                        metadata_storage.write(
                            metadata_key,
                            json.dumps(tests_using_fixture),
                            fixture_values,
                        )
                        store.write(storage_key, serialize(data), fixture_values)

                yield data

                with (store.lock(storage_key), metadata_storage.lock(metadata_key)):
                    tests_run_in_worker = request.config.stash[tests_started]
                    tests_missing: set[str] = set(
                        json.loads(metadata_storage.read(metadata_key, fixture_values))
                    )
                    tests_missing -= set(tests_run_in_worker)
                    if not tests_missing:
                        metadata_storage.write(
                            metadata_key,
                            json.dumps(list(tests_missing)),
                            fixture_values,
                        )
                        _send_last(res, None)
                    else:
                        _send_last(res, None)

            return wrapper_generator
        else:
            @pytest.fixture(scope="session", **kwargs)
            @functools.wraps(func)
            def wrapper_return(*args, **kwargs):
                fixture_values = {k: kwargs[k] for k in fixture_names}
                new_kwargs = {
                    k: v for k, v in kwargs.items() if k in original_signature.parameters.keys()
                }
                request = fixture_values["request"]

                if not is_xdist_worker(request):  # Not running with xdist, early return
                    return func(*args, **new_kwargs)

                unique_id = f"{func.__module__}.{func.__qualname__}"
                store_key = store.get_key(unique_id, fixture_values)

                with store.lock(store_key):
                    try:
                        data = deserialize(store.read(store_key, fixture_values))
                    except ValueNotExists:
                        data = func(*args, **new_kwargs)
                    return data

            return wrapper_return

    return _inner

shared_json_scope_fixture = partial(shared_session_scope_fixture, JsonStore())
