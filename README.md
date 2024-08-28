# Pytest Shared Session Fixture

Session scoped fixture that is shared between all workers in a pytest-xdist run.

```python
from pytest_shared_session_scope import shared_json_scope_fixture, CleanupToken

@shared_json_scope_fixture() # This turns below function into a session scope fixture
def my_fixture():
    # First yields returns None if it hasn't been calculated yet and the value if it has
    initial = yield
    if initial is None: # This is the first worker to run the fixture
        data = 123 # Do something expensive
    else: # This is a worker using the fixture after the first worker
        data = initial
    token: CleanupToken = yield data # Second yield yields data to test and returns a token
    if token == CleanupToken.LAST:
      ... # This will only run in the last worker to finish
    else:
      ... # This will run in all workers except the last one
    ... # This will run in all workers
```

It differs from normal fixtures in two ways:
- If it yields it must yield twice - once to optionally calculate the value, once to yield the value to the test
- If it yields, a `CleanupToken` is send back in the second yield. This can be used to determine if the worker should do any cleanup.

If the fixture "just" returns a value it works too without any modifications.

## Why?

This helps avoid one of the most classic pytest pitfalls: session-scoped fixtures are run in each xdist worker.
This is a special case of the more general pytest pitfall of thinking that if something works, it will also work with xdist.


## Why Not?

The double yield makes them different from normal pytest fixtures and can be confusing.
The implementation is a bit hacky - we need to modify the signature of functions to pass fixture values to the inner actual fixture.
I'm also not entirely confident cleanup will work correctly in all cases.

## Recipes

### Non JSON serializable data

The default store uses `json.dumps/json.loads` which cannot handle all objects. Instead of implementing a custom store for
each fixture, you can use the `serialize` and `deserialize` arguments


```python
from pytest_shared_session_scope import shared_json_scope_fixture
from datetime import datetime

def serialize(value: datetime) -> str:
    return value.isoformat()

def deserialize(value: str) -> datetime:
    return datetime.fromisoformat(value)

@shared_json_scope_fixture(serialize=serialize, deserialize=deserialize)
def my_fixture_return():
    return datetime.now()

```

### Returning functions

It's a common pattern to return functions from fixtures - for example to register data needed in the cleanup. Instead, use two fixtures - one to calculate the data and one to use it. But remember that the second fixture is run in each worker! So it won't cover all cases.
```python
import pytest

@shared_json_scope_fixture()
def important_ids():
    return [1,2,3]

@pytest.fixture
def cleanup_important_ids(important_ids):
    ids_to_cleanup = []
    def use_id(id_):
      if id_ not in important_ids:
        raise ValueError(f"{id_} not in important_ids!")
      ids_to_cleanup.append(id_)
    yield use_id
    for id in ids_to_cleanup:
      print(f"Cleaning up {id}")

def test_thing_with_ids(important_ids, cleanup_important_ids):
    for id in important_ids:
      # assert thing
      cleanup_important_ids(id)
```

## How?

The decorator is a generalization of the guide from the pytest-xdist docs of how to [make session scoped fixtures execute only once](https://pytest-xdist.readthedocs.io/en/stable/how-to.html#making-session-scoped-fixtures-execute-only-once) with the added feature of being able to run cleanup code in the last worker to finish. 
To summarize, the first worker to request the fixture will calculate it and them persist it in a `Store`. 
Other workers will load the data from the `Store`.
If these `Stores` needs access to other fixtures (say, `tmp_path_factory`) we modify the signature of the actual wrapped fixture to include these fixtures.

To keep count on what worker is the last to finish, we keep a running track of what tests has been run in each worker (using the 
`pytest_runtest_protocol` and `config.stash`). This information is then yielded back to the worker


