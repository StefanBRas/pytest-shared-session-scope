from pytest_shared_session_scope._scheduler import FixedScheduling


def pytest_xdist_make_scheduler(config, log):
    return FixedScheduling(
        config,
        exact_test_names=[
            [
                "test_fixture_params.py::test_1[a]",
                "test_fixture_params.py::test_2[a]",
                "test_fixture_params.py::test_3[a]",
                "test_fixture_params.py::test_1[b]",
                "test_fixture_params.py::test_2[b]",
                "test_fixture_params.py::test_3[b]",
            ],
            [
                "test_fixture_params.py::test_other_1[a]",
                "test_fixture_params.py::test_other_2[a]",
                "test_fixture_params.py::test_other_3[a]",
                "test_fixture_params.py::test_other_1[b]",
                "test_fixture_params.py::test_other_2[b]",
                "test_fixture_params.py::test_other_3[b]",
            ],
        ],
    )
