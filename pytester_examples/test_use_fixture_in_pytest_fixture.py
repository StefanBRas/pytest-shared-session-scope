import pytest
from pytest_shared_session_scope import shared_session_scope_json

@shared_session_scope_json()
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

def test_thing_with_ids_2(important_ids, cleanup_important_ids):
    for id in important_ids:
      # assert thing
      cleanup_important_ids(id)

def test_thing_with_ids_3(important_ids, cleanup_important_ids):
    for id in important_ids:
      # assert thing
      cleanup_important_ids(id)
