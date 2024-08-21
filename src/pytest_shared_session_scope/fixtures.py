import functools
import time
from contextlib import suppress
import inspect
from collections.abc import Callable
from functools import partial
from typing import Optional

import pytest

from pytest_shared_session_scope.lock import FileLock
from pytest_shared_session_scope.storage import JsonStorage
from pytest_shared_session_scope.types import Cache, CleanUp, Lock, Storage, Store, ValueNotExists
from xdist import is_xdist_controller

from pytest_shared_session_scope.utils import count_yields

tests_started = pytest.StashKey[list[str]]()

@pytest.hookimpl(tryfirst=True)
def pytest_runtest_protocol(item, nextitem):
    item.config.stash.setdefault(tests_started, []).append(item.nodeid)

def shared_session_scope_fixture(
    storage: Store, lock: Optional[Lock], 
    cache: Optional[Store] = None,
    clean_up: CleanUp = 'after'
    , **kwargs
):
    # TODO: add docstrings here
    def _inner(func: Callable):
        fixture_names = set(storage.fixtures) | {"request"}
        if cache:
            fixture_names |= set(cache.fixtures)

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

        @pytest.fixture(scope="session", **kwargs)
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            fixture_values = {k: kwargs[k] for k in fixture_names}
            new_kwargs = {
                k: v for k, v in kwargs.items() if k in signature.parameters.keys()
            }
            request = fixture_values["request"]
            if is_xdist_controller(request):
                res = func(*args, **new_kwargs)
                if inspect.isgenerator(res):
                    yield from res
                else:
                    return res
                return

            match count_yields(func):
                case 0:
                    is_generator = False
                case 1:
                    raise ValueError("blablabla")
                case 2:
                    is_generator = True
                case _:
                    raise ValueError("blablabla")

            assert isinstance(request, pytest.FixtureRequest)

            tests_using_fixture = []
            for item in request.session.items:
                if func.__name__ in item.fixturenames:
                    tests_using_fixture.append(item.nodeid)

            storage_key = storage.get_key(func.__qualname__, fixture_values)
            if lock:
                resolved_lock = lock(storage_key) if isinstance(lock, Callable) else lock
            else:
                resolved_lock = storage.lock(storage_key)

            cleanup_generator = None

            def _call():
                nonlocal cleanup_generator
                res = func(*args, **new_kwargs)
                if inspect.isgenerator(res):
                    cleanup_generator = res
                    return next(res)
                return res

            def _call_with_storage():
                try:
                    return storage.read(storage_key, fixture_values)
                except ValueNotExists:
                    data = _call()
                    storage.write(storage_key + ".testids", tests_using_fixture, fixture_values)
                    return storage.write(storage_key, data, fixture_values)

            def call():
                if is_xdist_controller(request):
                    return _call()
                return _call_with_storage()

            with resolved_lock:
                if cache:
                    cache_key = cache.get_key(func.__qualname__, fixture_values)
                    try:
                        data = cache.read(cache_key, fixture_values)
                    except KeyError:
                        data = call()
                        cache.write(data, cache_key, fixture_values)
                else:
                    data = call()

            yield data
            if is_generator:
                match clean_up:
                    case "after":
                        # Since only ONE worker ran the computation, the cleanup must be run in the same worker
                        # because we cant start generators 
                        with resolved_lock:
                            tests_run_in_worker = request.config.stash[tests_started]
                            tests_missing: set[str] = set(storage.read(storage_key + ".testids", fixture_values))
                            tests_missing -= set(tests_run_in_worker)
                            storage.write(storage_key + ".testids", list(tests_missing), fixture_values)
                        if cleanup_generator: # This is the worker that ran the computation
                            while tests_missing: # We must wait for other workers to finish test
                                time.sleep(0.1)
                                with resolved_lock:
                                    if storage.read(storage_key + ".testids", fixture_values) == []:
                                        break
                            with suppress(StopIteration):
                                next(cleanup_generator)
                    case "immediately":
                        if cleanup_generator:
                            with suppress(StopIteration):
                                next(cleanup_generator)

        return wrapper

    return _inner


shared_json_scope_fixture = partial(
    shared_session_scope_fixture, JsonStorage(), FileLock
)
