import functools
import inspect
from collections.abc import Callable
from functools import partial
from typing import Optional

import pytest

from pytest_shared_session_scope.lock import FileLock
from pytest_shared_session_scope.storage import JsonStorage
from pytest_shared_session_scope.types import Cache, CleanUp, Lock, Storage, ValueNotExists
from xdist import is_xdist_controller

x = (y for y in range(10))

x.close

# TODO: type this better

def shared_session_scope_fixture(
    storage: Storage, lock: Lock, 
    cache: Optional[Cache] = None,
    clean_up: CleanUp = 'last'
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
            storage_key = storage.get_key(func.__qualname__, fixture_values)
            resolved_lock = lock(storage_key) if isinstance(lock, Callable) else lock
            cleanup_generator = None

            def _call():
                new_kwargs = {
                    k: v for k, v in kwargs.items() if k in signature.parameters.keys()
                }
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
                    return storage.write(storage_key, data, fixture_values)

            def call():
                if is_xdist_controller(fixture_values["request"]):
                    return _call()
                return _call_with_storage()

            with resolved_lock:
                if cache:
                    cache_key = cache.get_key(func.__qualname__, fixture_values)
                    try:
                        data = cache.get(cache_key, fixture_values)
                    except KeyError:
                        data = call()
                        cache.set(data, cache_key, fixture_values)
                else:
                    data = call()
            yield data
            if cleanup_generator:
                try:
                    next(cleanup_generator)
                except StopIteration:
                    pass

        return wrapper

    return _inner


shared_json_scope_fixture = partial(
    shared_session_scope_fixture, JsonStorage(), FileLock
)
