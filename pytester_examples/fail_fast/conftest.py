from pytest_shared_session_scope._scheduler import FixedScheduling


def pytest_xdist_make_scheduler(config, log):
    return FixedScheduling(
        config,
        exact_test_names=[
            [
                "test_fail_fast.py::test_before_fail",
                "test_fail_fast.py::test_fail",
                "test_fail_fast.py::test_after_fail",
            ],
            [
                "test_fail_fast.py::test_fail_other_worker_1",
                "test_fail_fast.py::test_fail_other_worker_2",
                "test_fail_fast.py::test_fail_other_worker_3",
                "test_fail_fast.py::test_fail_other_worker_4",
            ],
        ],
    )
