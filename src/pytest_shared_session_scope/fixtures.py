import functools
import inspect
from collections.abc import Callable
from functools import partial

import pytest

from pytest_shared_session_scope.lock import FileLock
from pytest_shared_session_scope.storage import JsonStorage
from pytest_shared_session_scope.types import Lock, Storage


def shared_session_scope_fixture_loader(
    storage: Storage,
    lock: Lock,
):
    def _inner(func: Callable):
        if fixtures := storage.fixtures:
            fixture_names = set(fixtures) | {"worker_id"}
        else:
            fixture_names = {"worker_id"}

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

        @pytest.fixture(scope="session")
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            fixture_values = {k: kwargs[k] for k in fixture_names}

            def _call():
                new_kwargs = {
                    k: v for k, v in kwargs.items() if k in signature.parameters.keys()
                }
                res = func(*args, **new_kwargs)
                if inspect.isgenerator(res):
                    return next(res)
                return res

            if fixture_values["worker_id"] == "master":
                # not executing in with multiple workers, just produce the data and let
                # pytest's fixture caching do its job
                data = _call()
            else:
                key = storage.get_key(func.__qualname__, fixture_values)
                resolved_lock = lock(key) if isinstance(lock, Callable) else lock
                with resolved_lock:
                    if storage.exists(key, fixture_values):
                        data = storage.read(key, fixture_values)
                    else:
                        data = _call()
                        storage.write(key, data, fixture_values)
            yield data

        return wrapper

    return _inner


shared_json_scope_fixture = partial(
    shared_session_scope_fixture_loader, JsonStorage(), FileLock
)
