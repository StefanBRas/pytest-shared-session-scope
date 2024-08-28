"""Shared Session Scope Fixtures."""

import functools
import typing
from contextlib import suppress
import inspect
from collections.abc import Callable
import json
from typing import Iterable, TypeVar
from typing_extensions import Generator

import pytest

from pytest_shared_session_scope._types import tests_started
from pytest_shared_session_scope.store import FileStore, JsonStore
from pytest_shared_session_scope.types import CleanupToken, Store, StoreValueNotExists
from xdist import is_xdist_worker

_T = TypeVar("_T")
_V = TypeVar("_V")


def identity(v: _T) -> _T:
    return v


def _send_last(generator: Generator, token: CleanupToken | None):
    with suppress(StopIteration):
        generator.send(token)
        msg = "This generator should have been exhausted"
        raise AssertionError(msg)


def _get_tests_for_fixture(fixture, request: pytest.FixtureRequest) -> list[str]:
    return list(
        {
            item.nodeid
            for item in request.session.items
            if fixture.__name__ in item.fixturenames  # type: ignore
        }
    )


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
            extra_params.append(inspect.Parameter(fixture, inspect.Parameter.POSITIONAL_OR_KEYWORD))
    parameters.extend(extra_params)
    return signature.replace(parameters=parameters)


def shared_session_scope_fixture(
    store: Store[_T],
    serialize: Callable[[_V], _T] = identity,
    deserialize: Callable[[_T], _V] = identity,
    metadata_storage: Store[str] = FileStore(),
    **kwargs,
):
    """Create a session scope fixture that is shared among all workers.

    Example:
        ```python
        from pytest_shared_session_scope import shared_session_scope_fixture, JsonStore, CleanupToken

        def expensive_calculation():
            return 123

        @shared_session_scope_fixture(JsonStore())
        def my_fixture():
        initial = yield
        if initial is None:
            data = expensive_calculation()
        else:
            data = initial
        token: CleanupToken = yield data
        if token == CleanupToken.last:
            ... # Cleanup that should only happen once
        ... # Do cleanup that should happend for all workers here

        ```

    Args:
        store: Store to save the fixture data.
        serialize: Function to serialize the data before saving it to the store.
        deserialize: Function to deserialize the data after reading it from the store.
        metadata_storage: Store to save metadata about the current test run.
            This is necessary to determine which worker should do the cleanup.
        **kwargs: Additional arguments to pass to the @pytest.fixture.
    """

    def _inner(func: Callable):
        fixture_names = set(store.fixtures) | set(metadata_storage.fixtures) | {"request"}
        original_signature = inspect.signature(func)
        new_signature = _add_fixture_to_signature(func, fixture_names)
        func.__signature__ = new_signature  # type: ignore

        if inspect.isgeneratorfunction(func):

            @pytest.fixture(scope="session", **kwargs)
            @functools.wraps(func)
            def wrapper_generator(*args, **kwargs):
                fixture_values = {k: kwargs[k] for k in fixture_names}
                new_kwargs = {k: v for k, v in kwargs.items() if k in original_signature.parameters.keys()}
                request = typing.cast(pytest.FixtureRequest, fixture_values["request"])

                if not is_xdist_worker(request):  # Not running with xdist, early return
                    res = func(*args, **new_kwargs)
                    next(res)
                    data = res.send(None)
                    yield data
                    _send_last(res, CleanupToken.LAST)
                    return

                tests_using_fixture = _get_tests_for_fixture(func, request)

                store_identifier = f"{func.__module__}.{func.__qualname__}"
                metadata_identifier = store_identifier + "_metadata"

                store_lock = store.lock(store_identifier, fixture_values)
                metadata_lock = metadata_storage.lock(metadata_identifier, fixture_values)

                # TODO: I feel like the lock scope is broader than it needs to be
                with store_lock:
                    res = func(*args, **new_kwargs)
                    next(res)
                    try:
                        data = deserialize(store.read(store_identifier, fixture_values))
                        res.send(data)
                    except StoreValueNotExists:
                        data = res.send(None)
                        store.write(store_identifier, serialize(data), fixture_values)
                        with metadata_lock:
                            metadata_storage.write(
                                metadata_identifier,
                                json.dumps(tests_using_fixture),
                                fixture_values,
                            )

                yield data

                # We want to release the lock before calling the cleanup function
                # so we use a flag here
                is_last = False

                metadata_lock_after = metadata_storage.lock(metadata_identifier, fixture_values)

                with metadata_lock_after:
                    tests_run_in_worker = request.config.stash[tests_started]
                    tests_missing: set[str] = set(
                        json.loads(metadata_storage.read(metadata_identifier, fixture_values))
                    )
                    tests_missing -= set(tests_run_in_worker)
                    is_last = not tests_missing
                    if not is_last:
                        metadata_storage.write(
                            metadata_identifier,
                            json.dumps(list(tests_missing)),
                            fixture_values,
                        )

                if is_last:
                    _send_last(res, CleanupToken.LAST)
                else:
                    _send_last(res, None)

            return wrapper_generator
        else:

            @pytest.fixture(scope="session", **kwargs)
            @functools.wraps(func)
            def wrapper_return(*args, **kwargs):
                fixture_values = {k: kwargs[k] for k in fixture_names}
                new_kwargs = {k: v for k, v in kwargs.items() if k in original_signature.parameters.keys()}
                request = fixture_values["request"]

                if not is_xdist_worker(request):  # Not running with xdist, early return
                    return func(*args, **new_kwargs)

                store_identifier = f"{func.__module__}.{func.__qualname__}"
                store_lock = store.lock(store_identifier, fixture_values)

                with store_lock:
                    try:
                        data = deserialize(store.read(store_identifier, fixture_values))
                    except StoreValueNotExists:
                        data = func(*args, **new_kwargs)
                    return data

            return wrapper_return

    return _inner


def shared_json_scope_fixture(
    serialize: Callable[[_V], _T] = identity,
    deserialize: Callable[[_T], _V] = identity,
    metadata_storage: Store[str] = FileStore(),
    **kwargs,
):
    """Create a session scope fixture that is shared among all workers.

    Example:
        ```python
        from pytest_shared_session_scope import shared_json_scope_fixture, JsonStore, CleanupToken


        def expensive_calculation():
            return 123

        @shared_json_scope_fixture()
        def my_fixture():
        initial = yield
        if initial is None:
            data = expensive_calculation()
        else:
            data = initial
        token: CleanupToken = yield data
        if token == CleanupToken.last:
            ... # Cleanup that should only happen once
        ... # Do cleanup that should happend for all workers here

        ```

    Args:
        serialize: Function to serialize the data before saving it to the store.
        deserialize: Function to deserialize the data after reading it from the store.
        metadata_storage: Store to save metadata about the current test run.
            This is necessary to determine which worker should do the cleanup.
        **kwargs: Additional arguments to pass to the @pytest.fixture.
    """
    return shared_session_scope_fixture(JsonStore(), serialize, deserialize, metadata_storage, **kwargs)
