# Lets you predetermine which tests run on which workers
from collections import defaultdict
from itertools import chain

from xdist.workermanage import WorkerController
from xdist.workermanage import parse_spec_config
from typing import Sequence
import pytest
import re


class FixedScheduling:
    def __init__(
        self,
        config: pytest.Config,
        exact_test_names: list[list[str]] | dict[int, list[str]] = [],
        literal_test_names: list[list[str]] | dict[int, list[str]] = [],
        re_test_names: list[list[str]] | dict[int, list[str]] = [],
        exhaustive: bool = True,
        all_matchers_must_match: bool = True,
    ) -> None:
        self.numnodes = len(parse_spec_config(config))
        self._nodes: list[WorkerController] = []
        self.registered_collections: dict[WorkerController, list[str]] = {}
        self.collection: list[str] | None = None
        self.assigned_work: dict[WorkerController, dict[str, bool]] = {}
        self.node_to_test_id: dict[WorkerController, list[int]] | None = None
        self.node_to_pending: dict[WorkerController, list[int]] | None = None

        self.exact_test_names = (
            exact_test_names
            if isinstance(exact_test_names, dict)
            else {index: values for index, values in enumerate(exact_test_names)}
        )

        self.literal_test_names = (
            literal_test_names
            if isinstance(literal_test_names, dict)
            else {index: values for index, values in enumerate(literal_test_names)}
        )

        self.re_test_names = (
            re_test_names
            if isinstance(re_test_names, dict)
            else {index: values for index, values in enumerate(re_test_names)}
        )

        self.exhaustive = exhaustive
        self.all_matchers_must_match = all_matchers_must_match
        self.matchers_with_matches = set()

    @property
    def nodes(self) -> list[WorkerController]:
        return self._nodes

    @property
    def collection_is_completed(self) -> bool:
        return len(self.registered_collections) >= self.numnodes

    @property
    def tests_finished(self) -> bool:
        if not self.collection_is_completed:
            return False

        for assigned_unit in self.assigned_work.keys():
            if self._pending_of(assigned_unit) >= 2:
                return False
        return True

    @property
    def has_pending(self) -> bool:
        for worker in self.assigned_work.keys():
            if self._pending_of(worker) > 0:
                return True
        return False

    def _pending_of(self, node: WorkerController) -> int:
        """Return the number of pending tests in a workload."""
        return list(self.assigned_work[node].values()).count(False)

    def add_node(self, node: WorkerController) -> None:
        assert node not in self.nodes
        self.nodes.append(node)
        # TODO: Do natural sort
        self.nodes.sort(key=lambda node: node.workerinfo["id"])
        self.assigned_work[node] = {}

    def remove_node(self, node: WorkerController) -> str | None:
        self.nodes.remove(node)

    def add_node_collection(
        self,
        node: WorkerController,
        collection: Sequence[str],
    ) -> None:
        self.registered_collections[node] = list(collection)

    def mark_test_complete(
        self,
        node: WorkerController,
        item_index: int,
        duration: float = 0,
    ) -> None:
        assert self.node_to_pending
        node_id = self.registered_collections[node][item_index]
        self.assigned_work[node][node_id] = True
        self.node_to_pending[node].remove(item_index)
        self.send_tests_to_workers()

    def mark_test_pending(self, item: str) -> None:
        raise NotImplementedError()

    def remove_pending_tests_from_node(
        self,
        node: WorkerController,
        indices: Sequence[int],
    ) -> None:
        raise NotImplementedError()

    def send_tests_to_workers(self):
        assert self.node_to_test_id
        node_to_pending = self.node_to_pending
        assert node_to_pending is not None

        def get_idle_nodes() -> list[tuple[WorkerController, list[int]]]:
            return [
                (node, pending)
                for node, pending in node_to_pending.items()
                if len(pending) < 2 and not node.shutting_down
            ]

        idle_nodes = get_idle_nodes()

        if not idle_nodes:
            return

        for idle_node, pending in idle_nodes:
            new_tests = 2 - len(pending)
            test_to_sends = self.node_to_test_id[idle_node][:new_tests]
            if test_to_sends:
                del self.node_to_test_id[idle_node][:new_tests]
                node_to_pending[idle_node].extend(test_to_sends)
                idle_node.send_runtest_some(test_to_sends)
            else:
                idle_node.shutdown()

    def schedule(self) -> None:
        self.collection = list(next(iter(self.registered_collections.values())))
        if self.node_to_test_id:
            self.send_tests_to_workers()
        else:
            self.node_to_test_id = defaultdict(list)
            for test_id in self.collection:
                self._assign_to_node(test_id)

            if self.exhaustive:
                if len(self.collection) != sum(len(v) for v in self.node_to_test_id.values()):
                    matched_tests = set(self.collection[idx] for idx in chain(*self.node_to_test_id.values()))
                    missing_tests = set(self.collection) - matched_tests
                    msg = (
                        f"exhaustive is True, but some tests were not mapped. Missing tests: {missing_tests}"
                    )
                    raise ValueError(msg)
            if self.all_matchers_must_match and len(self.matchers_with_matches) != sum(
                sum(len(match_values) for match_values in matchers.values())
                for matchers in [self.exact_test_names, self.literal_test_names, self.re_test_names]
            ):
                all_matchers = set()
                for type_, matchers in [
                    ("exact", self.exact_test_names),
                    ("literal", self.literal_test_names),
                    ("re", self.re_test_names),
                ]:
                    for index, values in matchers.items():
                        for value in values:
                            all_matchers.add((type_, index, value))
                missing_matchers = all_matchers - self.matchers_with_matches
                msg = (
                    f"all_matchers_must_match is True, but some matchers did not match any tests."
                    f" Missing matchers: {missing_matchers}"
                )
                raise ValueError(msg)
            self.node_to_pending = {node: [] for node in self.node_to_test_id.keys()}
            self.send_tests_to_workers()

    def _assign_to_node(self, test_id: str):
        assert self.collection
        node_to_test_id = self.node_to_test_id
        assert node_to_test_id is not None

        def exact_match_fn(x, y):
            return x == y

        def literal_match_fn(x, y):
            return x in y

        def re_match_fn(x, y):
            return re.match(y, x) is not None

        for type_, matchers, fn in [
            ("exact", self.exact_test_names, exact_match_fn),
            ("literal", self.literal_test_names, literal_match_fn),
            ("re", self.re_test_names, re_match_fn),
        ]:
            match type_:
                case "exact":
                    matchers = self.exact_test_names
                case "literal":
                    matchers = self.literal_test_names
                case "re":
                    matchers = self.re_test_names
                case _:
                    msg = f"Unknown matcher type {type_}"
                    raise ValueError(msg)

            for node_index, match_values in matchers.items():
                for match_value in match_values:
                    if fn(match_value, test_id):
                        self.matchers_with_matches.add((type_, match_value))
                        node = self.nodes[node_index]
                        node_to_test_id[node].append(self.collection.index(test_id))
                        self.assigned_work[node][test_id] = False
                        return
