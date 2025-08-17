from pytest_shared_session_scope._scheduler import FixedScheduling


def pytest_xdist_make_scheduler(config, log):
    return FixedScheduling(
        config,
        exact_test_names=[
            [
                "test_getfixturevalue.py::test_1",
                "test_getfixturevalue.py::test_2",
                "test_getfixturevalue.py::test_3",
            ],
            [
                "test_getfixturevalue.py::test_other_1",
                "test_getfixturevalue.py::test_other_2",
                "test_getfixturevalue.py::test_other_3",
            ],
        ],
    )
