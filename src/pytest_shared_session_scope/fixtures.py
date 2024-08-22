import functools
from contextlib import suppress
import inspect
from collections.abc import Callable
from functools import partial
from typing import Optional

import pytest

from pytest_shared_session_scope.lock import FileLock
from pytest_shared_session_scope.store import JsonStore
from pytest_shared_session_scope.types import Lock, Store, ValueNotExists
from xdist import is_xdist_worker


tests_started = pytest.StashKey[list[str]]()


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_protocol(item, nextitem):
    item.config.stash.setdefault(tests_started, []).append(item.nodeid)


def shared_session_scope_fixture(storage: Store, lock: Optional[Lock], **kwargs):
    # TODO: add docstrings here
    def _inner(func: Callable):
        fixture_names = set(storage.fixtures) | {"request"}

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
        func.__signature__ = signature.replace(parameters=parameters)  # pyright: ignore

        if inspect.isgeneratorfunction(func):

            @pytest.fixture(scope="session", **kwargs)
            @functools.wraps(func)
            def wrapper_generator(*args, **kwargs):
                fixture_values = {k: kwargs[k] for k in fixture_names}
                new_kwargs = {
                    k: v for k, v in kwargs.items() if k in signature.parameters.keys()
                }
                request = fixture_values["request"]

                if not is_xdist_worker(request):  # Not running with xdist, early return
                    res = func(*args, **new_kwargs)
                    next(res)
                    data = res.send(None)
                    yield data
                    try:
                        res.send("last")
                        msg = "This generator should have been exhausted"
                        raise AssertionError(msg)
                    except StopIteration:
                        return

                assert isinstance(request, pytest.FixtureRequest)

                tests_using_fixture = []
                for item in request.session.items:
                    if func.__name__ in item.fixturenames:
                        tests_using_fixture.append(item.nodeid)

                unique_id = f"{func.__module__}.{func.__qualname__}"
                storage_key = storage.get_key(unique_id, fixture_values)
                if lock:
                    resolved_lock = (
                        lock(storage_key) if isinstance(lock, Callable) else lock
                    )
                else:
                    resolved_lock = storage.lock(storage_key)

                with resolved_lock:
                    res = func(*args, **new_kwargs)
                    next(res)
                    try:
                        data = storage.read(storage_key, fixture_values)
                        also_data = res.send(data)
                        assert data == also_data
                    except ValueNotExists:
                        data = res.send(None)
                        storage.write(
                            storage_key + ".testids",
                            tests_using_fixture,
                            fixture_values,
                        )
                        storage.write(storage_key, data, fixture_values)

                yield data

                with resolved_lock:
                    tests_run_in_worker = request.config.stash[tests_started]
                    tests_missing: set[str] = set(
                        storage.read(storage_key + ".testids", fixture_values)
                    )
                    tests_missing -= set(tests_run_in_worker)
                    if not tests_missing:
                        storage.write(
                            storage_key + ".testids",
                            list(tests_missing),
                            fixture_values,
                        )
                        with suppress(StopIteration):
                            res.send(None)
                    else:
                        with suppress(StopIteration):
                            res.send("last")

            return wrapper_generator
        else:
            @pytest.fixture(scope="session", **kwargs)
            @functools.wraps(func)
            def wrapper_return(*args, **kwargs):
                fixture_values = {k: kwargs[k] for k in fixture_names}
                new_kwargs = {
                    k: v for k, v in kwargs.items() if k in signature.parameters.keys()
                }
                request = fixture_values["request"]

                if not is_xdist_worker(request):  # Not running with xdist, early return
                    return func(*args, **new_kwargs)

                unique_id = f"{func.__module__}.{func.__qualname__}"
                storage_key = storage.get_key(unique_id, fixture_values)

                if lock:
                    resolved_lock = (
                        lock(storage_key) if isinstance(lock, Callable) else lock
                    )
                else:
                    resolved_lock = storage.lock(storage_key)

                with resolved_lock:
                    try:
                        data = storage.read(storage_key, fixture_values)
                    except ValueNotExists:
                        data = func(*args, **new_kwargs)
                    return data

            return wrapper_return

    return _inner


shared_json_scope_fixture = partial(shared_session_scope_fixture, JsonStore(), FileLock)
