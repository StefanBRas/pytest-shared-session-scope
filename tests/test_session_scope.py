from datetime import datetime


def test_fixture_with_cleanup(fixture_with_cleanup):
    assert fixture_with_cleanup == 1


def test_fixture_with_cleanup2(fixture_with_cleanup):
    assert fixture_with_cleanup == 1


def test_fixture_with_cleanup3(fixture_with_cleanup):
    assert fixture_with_cleanup == 1


def test_fixture_with_yield(fixture_with_yield):
    assert fixture_with_yield == 1


def test_fixture_with_yield2(fixture_with_yield):
    assert fixture_with_yield == 1


def test_fixture_with_yield3(fixture_with_yield):
    assert fixture_with_yield == 1


def test_fixture_with_return(fixture_with_return):
    assert fixture_with_return == 1


def test_fixture_with_return2(fixture_with_return):
    assert fixture_with_return == 1


def test_fixture_with_return3(fixture_with_return):
    assert fixture_with_return == 1


def test_fixture_with_serializtion(fixture_with_deserializor):
    assert isinstance(fixture_with_deserializor, datetime)
