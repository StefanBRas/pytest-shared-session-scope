import pytest


def test_fixture(fixture_a):
    assert fixture_a == 'fixture1'

def test_fixture2(fixture_a):
    assert fixture_a == 'fixture1'
    
