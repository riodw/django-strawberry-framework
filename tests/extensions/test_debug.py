"""DjangoDebugExtension tests for payload serialization, SQL capture, errors, and execution isolation.

Everything here is what a live ``/graphql/`` request cannot isolate: the two
wire serializers and the nested ``original_error`` chain handling, the
reference-counted ``force_debug_cursor`` coordinator's restore contract and
partial-acquisition unwind, bounded-log slicing, ``get_results``'
no-stash / idempotence contract (including the real engine's conditional
double call), masking-extension ordering, extensions-map merge precedence and
result-map replacement, the async shared-wrapper overlap restore, nested
same-thread attribution, concurrent sync instance isolation at the
``strawberry-graphql==0.316.0`` floor, the post-execution diagnostic
non-interference degrade, the cursor-construction capture-interval boundary,
transaction-boundary scope, sibling-hook SQL ordering, the fail-closed
``settings.DEBUG`` gate's inert path (spec-048 Decision 5), and the payload
caps' arithmetic (spec-048 Decision 6, exercised directly against the pure
``_apply_payload_caps``).

The suite runs with ``settings.DEBUG`` false, which is now the extension's
fail-closed condition, so every case that expects a published payload declares
the debug posture it exercises: ``override_settings(DEBUG=True)`` where the
case is about the BARE CLASS entry's own semantics (fresh-per-operation
instances, coordinator restore, list ordering), and the acknowledgement factory
``lambda: DjangoDebugExtension(allow_unsafe_production=True)`` only where
keeping ``DEBUG`` false is itself the point.

Deliberate test rules (spec-044 D4-D5):

* Wire keys and the 10-second slow threshold are re-spelled as INDEPENDENT
  literals - never imported from the production module and never built
  through the production serializers - so a key rename cannot pass green.
* The concurrency/lifecycle tests exercise the coordinator's two seams and
  the log-slice clamp, not ``on_operation``'s body; the one fake sits at the
  private acquisition boundary (partial-setup unwind), never at Strawberry's
  runner.
* Real objects everywhere practical: real ``GraphQLError`` wrappers, real
  ``MaskErrors``, real Strawberry execution, real connection wrappers, and a
  real bounded ``deque``.

Live GraphQL HTTP behavior over fakeshop models belongs in
``examples/fakeshop/test_query/test_debug_extension_api.py``.
"""

import asyncio
import itertools
import json
import logging
import threading
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import pytest
import strawberry
from django.db import connection, connections, transaction
from django.test.utils import override_settings
from graphql import GraphQLError
from strawberry.extensions import MaskErrors, SchemaExtension

from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.extensions import DjangoDebugExtension
from django_strawberry_framework.extensions import debug as debug_module
from django_strawberry_framework.extensions.debug import (
    _apply_payload_caps,
    _build_payload,
    _collect_exceptions,
    _ConnectionSnapshot,
    _CursorCaptureCoordinator,
    _query_log_entries_since,
    _serialize_exception,
    _serialize_sql_row,
    _terminal_original_error,
)

# The payload caps re-spelled as INDEPENDENT literals (the module's spec-044
# D4 rule extended to spec-048 Decision 6's constants): a cap that silently
# widened must fail these rows, which importing the production constants would
# make impossible.
_SQL_ROW_CAP = 100
_EXCEPTION_ROW_CAP = 25
_SQL_TEXT_CAP = 4096
_EXCEPTION_MESSAGE_CAP = 4096
_EXCEPTION_STACK_CAP = 16384
_PAYLOAD_CAP = 262144
_MARKER = "... [truncated]"


@strawberry.type
class _OkQuery:
    @strawberry.field
    def ok(self) -> str:
        return "ok"


@strawberry.type
class _BoomQuery:
    @strawberry.field
    def boom(self) -> int:
        raise ValueError("sensitive boom detail")

    @strawberry.field
    def ok(self) -> str:
        return "ok"


@pytest.fixture
def default_wrapper():
    """The current thread's concrete ``default`` wrapper, flag restored after the test."""
    wrapper = connections["default"]
    original = wrapper.force_debug_cursor
    yield wrapper
    wrapper.force_debug_cursor = original


# ---------------------------------------------------------------------------
# Scenario 10 - serializer units and the exception collector.
# ---------------------------------------------------------------------------


def test_exception_serializer_triple_forms():
    try:
        raise ValueError("kaboom message")
    except ValueError as exc:
        caught = exc

    row = _serialize_exception(caught)

    # Independent literals - never the production keys re-imported.
    assert set(row) == {"excType", "message", "stack"}
    assert row["excType"] == "<class 'ValueError'>"
    assert row["message"] == "kaboom message"
    assert "Traceback" in row["stack"]
    assert "kaboom message" in row["stack"]
    assert "test_exception_serializer_triple_forms" in row["stack"]  # the raise site


def test_exception_serializer_chained_traceback_stack():
    """A ``raise ... from`` chain serializes BOTH tracebacks; the triple stays outer-only.

    ``format_exception``'s default ``chain=True`` follows ``__cause__``, so
    the stack carries the cause's traceback joined to the outer one by
    CPython's connector line.
    """
    try:
        try:
            raise KeyError("root cause")
        except KeyError as exc:
            raise ValueError("kaboom message") from exc
    except ValueError as chained:
        caught = chained

    row = _serialize_exception(caught)

    # The triple names the OUTER exception only.
    assert row["excType"] == "<class 'ValueError'>"
    assert row["message"] == "kaboom message"
    # Both tracebacks, joined by the connector - independent literals.
    assert "KeyError" in row["stack"]
    assert "root cause" in row["stack"]
    assert "The above exception was the direct cause of the following exception:" in row["stack"]
    assert "test_exception_serializer_chained_traceback_stack" in row["stack"]  # both raise sites


@pytest.mark.parametrize(
    (
        "sql",
        "time",
        "expected_duration",
        "expected_slow",
        "expected_select",
    ),
    [
        (
            "SELECT * FROM t",
            "0.001",
            0.001,
            False,
            True,
        ),
        (
            "  select 1",
            "10.0",
            10.0,
            False,
            True,
        ),  # graphene's threshold is STRICTLY > 10
        (
            "UPDATE t SET x = 1",
            "10.5",
            10.5,
            True,
            False,
        ),
        (
            "3 times: INSERT INTO t VALUES (%s)",
            "0.002",
            0.002,
            False,
            False,
        ),
    ],
)
def test_sql_row_serializer_forms(
    sql,
    time,
    expected_duration,
    expected_slow,
    expected_select,
):
    wrapper = connections["default"]

    row = _serialize_sql_row(wrapper, {"sql": sql, "time": time})

    assert set(row) == {
        "vendor",
        "alias",
        "sql",
        "duration",
        "isSlow",
        "isSelect",
    }
    assert row["vendor"] == wrapper.vendor
    assert row["alias"] == "default"
    assert row["sql"] == sql  # verbatim, including the executemany "<N> times:" form
    assert row["duration"] == expected_duration
    assert isinstance(row["duration"], float)
    assert row["isSlow"] is expected_slow
    assert row["isSelect"] is expected_select


def test_exception_collector_guards_filter_order_and_no_dedup():
    # The two None guards (the sync pre-execution teardown shapes).
    assert _collect_exceptions(None) == []
    assert _collect_exceptions(SimpleNamespace(errors=None)) == []

    validation_error = GraphQLError("unknown field")  # original_error None -> skipped
    first = GraphQLError("first", original_error=ValueError("first original"))
    explicit = GraphQLError("explicit", original_error=GraphQLError("explicitly raised"))
    shared = ValueError("shared original")
    dup_a = GraphQLError("dup a", original_error=shared)
    dup_b = GraphQLError("dup b", original_error=shared)
    result = SimpleNamespace(
        errors=[
            validation_error,
            first,
            explicit,
            dup_a,
            dup_b,
        ],
    )

    rows = _collect_exceptions(result)

    # Result-error order preserved, validation skipped, no speculative dedup.
    assert [row["message"] for row in rows] == [
        "first original",
        "explicitly raised",
        "shared original",
        "shared original",
    ]
    # A terminal explicitly raised GraphQLError is retained, not misclassified.
    assert rows[1]["excType"] == "<class 'graphql.error.graphql_error.GraphQLError'>"


def test_nested_original_error_chain_reaches_the_terminal_python_exception():
    terminal = ValueError("the real one")
    inner = GraphQLError("inner", original_error=terminal)
    outer = GraphQLError("outer", original_error=inner)

    assert _terminal_original_error(outer) is terminal


# ---------------------------------------------------------------------------
# Scenario 21 - the original_error hop policy (cycles + the 64-hop ceiling).
# ---------------------------------------------------------------------------


def test_hop_policy_self_cycle_terminates_deterministically():
    cyclic = GraphQLError("self cycle")
    cyclic.original_error = cyclic
    outer = GraphQLError("outer", original_error=cyclic)

    assert _terminal_original_error(outer) is cyclic


def test_hop_policy_multi_node_cycle_returns_last_unique_candidate():
    node_a = GraphQLError("a")
    node_b = GraphQLError("b")
    node_a.original_error = node_b
    node_b.original_error = node_a
    outer = GraphQLError("outer", original_error=node_a)

    assert _terminal_original_error(outer) is node_b


def test_hop_policy_long_acyclic_chain_stops_at_the_ceiling():
    chain = [GraphQLError(f"hop {index}") for index in range(100)]
    for parent, child in itertools.pairwise(chain):
        parent.original_error = child
    outer = GraphQLError("outer", original_error=chain[0])

    result = _terminal_original_error(outer)

    # 64 hops from chain[0] - the independent literal, never the production constant.
    assert result is chain[64]


# ---------------------------------------------------------------------------
# Scenario 8 - the restore contract: the coordinator's two seams, the partial
# unwind, and the log-slice clamp/rollover.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("prior", [False, True])
def test_coordinator_saved_value_restore_and_depth(default_wrapper, prior):
    coordinator = _CursorCaptureCoordinator()
    default_wrapper.force_debug_cursor = prior

    token_one = coordinator.acquire(default_wrapper)
    assert default_wrapper.force_debug_cursor is True
    token_two = coordinator.acquire(default_wrapper)

    # Keyed by the concrete wrapper object, never the alias string.
    assert set(coordinator._active) == {default_wrapper}
    assert coordinator._active[default_wrapper].depth == 2
    assert coordinator._active[default_wrapper].saved_force_debug_cursor is prior

    coordinator.release(token_one)
    assert default_wrapper.force_debug_cursor is True  # still one bracket active
    assert coordinator._active[default_wrapper].depth == 1

    coordinator.release(token_two)
    assert default_wrapper.force_debug_cursor is prior  # the exact saved value
    assert coordinator._active == {}


def test_coordinator_isolates_distinct_wrappers_for_one_alias(default_wrapper):
    coordinator = _CursorCaptureCoordinator()
    holder = {}

    def _materialize_thread_local_wrapper():
        holder["wrapper"] = connections["default"]

    worker = threading.Thread(target=_materialize_thread_local_wrapper)
    worker.start()
    worker.join()
    other_wrapper = holder["wrapper"]
    assert other_wrapper is not default_wrapper  # one alias, two concrete wrappers

    token_main = coordinator.acquire(default_wrapper)
    token_other = coordinator.acquire(other_wrapper)
    assert set(coordinator._active) == {default_wrapper, other_wrapper}
    assert coordinator._active[default_wrapper].depth == 1
    assert coordinator._active[other_wrapper].depth == 1

    coordinator.release(token_other)
    assert other_wrapper.force_debug_cursor is False
    assert default_wrapper.force_debug_cursor is True  # untouched by the sibling release
    coordinator.release(token_main)
    assert coordinator._active == {}


@override_settings(DEBUG=True)
def test_partial_acquisition_failure_unwinds_earlier_connections(default_wrapper, monkeypatch):
    """A later-alias acquire failure restores every earlier alias before propagating.

    The one sanctioned fake, sitting at the private acquisition boundary
    (never a mock of Strawberry's runner): a stub connections handler exposes
    a second 'alias' whose acquisition raises after the real ``default``
    wrapper was already bracketed. ``DEBUG=True`` because the acquisition loop
    this pins runs only past the fail-closed gate.
    """
    original_flag = default_wrapper.force_debug_cursor

    exploding_wrapper = SimpleNamespace(force_debug_cursor=False, queries_log=deque())

    real_acquire = debug_module._coordinator.acquire

    def _acquire(database_connection):
        if database_connection is exploding_wrapper:
            raise RuntimeError("second alias acquisition failed")
        return real_acquire(database_connection)

    monkeypatch.setattr(
        debug_module,
        "connections",
        SimpleNamespace(all=lambda: [default_wrapper, exploding_wrapper]),
    )
    monkeypatch.setattr(debug_module._coordinator, "acquire", _acquire)

    extension = DjangoDebugExtension()
    hook = extension.on_operation()
    with pytest.raises(RuntimeError, match="second alias acquisition failed"):
        next(hook)

    assert default_wrapper.force_debug_cursor is original_flag
    assert debug_module._coordinator._active == {}
    assert extension.get_results() == {}  # no stash was ever published


def test_query_log_slicing_suffix_clamp_and_rollover():
    log = deque(maxlen=5)
    log.append({"sql": "pre-existing", "time": "0.001"})
    wrapper = SimpleNamespace(queries_log=log)
    snapshot = _ConnectionSnapshot(database_connection=wrapper, query_log_start=len(log))

    log.append({"sql": "appended", "time": "0.001"})
    assert [entry["sql"] for entry in _query_log_entries_since(snapshot)] == ["appended"]

    # A reset_queries()-shortened log clamps to [] instead of raising.
    log.clear()
    assert _query_log_entries_since(snapshot) == []

    # Rollover best-effort: a full deque that evicted old rows while staying the
    # same length cannot be distinguished from an untouched one - the documented
    # limitation, pinned without claiming exact rows survive.
    for index in range(5):
        log.append({"sql": f"old {index}", "time": "0.001"})
    full_snapshot = _ConnectionSnapshot(database_connection=wrapper, query_log_start=len(log))
    log.append({"sql": "new after rollover", "time": "0.001"})
    assert len(log) == 5  # same length: the new row evicted an old one
    assert _query_log_entries_since(full_snapshot) == []


# ---------------------------------------------------------------------------
# Scenario 11 - get_results no-stash shape, idempotence, and the real
# engine's conditional double call.
# ---------------------------------------------------------------------------


def test_get_results_no_stash_shape_and_idempotent_read():
    extension = DjangoDebugExtension()  # zero-argument construction succeeds

    assert DjangoDebugExtension._payload is None  # the immutable class-level default
    assert extension.get_results() == {}  # never {"debug": None}

    payload = {"sql": [], "exceptions": []}
    extension._payload = payload
    first = extension.get_results()
    second = extension.get_results()

    assert first == {"debug": {"sql": [], "exceptions": []}}
    assert first == second
    assert first["debug"] is payload  # a pure read - no copy, no mutation, no pop
    assert extension._payload is payload
    json.dumps(first)  # the JSON-serializability guard


@override_settings(DEBUG=True)
def test_validation_failure_with_raising_teardown_calls_get_results_twice():
    """The early-result plus teardown-failure recovery path invokes get_results twice.

    The validation early return evaluates the extension results INSIDE the
    operation context (call one); a sibling teardown then raises while that
    return unwinds, so the engine's recovery handler builds a replacement
    result and reads the extension results again (call two) - the reason
    ``get_results`` is pinned idempotent. Both calls must return ``{}``:
    teardown must not stash a payload unless ``execution_context.result`` is
    a graphql-core ``ExecutionResult``, or the second call would falsely
    publish ``debug``.
    """
    calls = []

    class _CountingDebug(DjangoDebugExtension):
        def get_results(self):
            calls.append(super().get_results())
            return calls[-1]

    class _RaisingTeardown(SchemaExtension):
        def on_operation(self):
            yield
            raise RuntimeError("teardown boom")

    # _RaisingTeardown listed FIRST so it tears down LAST - after the early
    # return already evaluated the first get_results pass.
    schema = strawberry.Schema(query=_OkQuery, extensions=[_RaisingTeardown, _CountingDebug])
    result = schema.execute_sync("{ definitelyNotAField }")

    assert result.errors
    assert len(calls) == 2
    assert calls == [{}, {}]
    assert "debug" not in (result.extensions or {})


@override_settings(DEBUG=True)
def test_parse_failure_with_raising_teardown_publishes_no_debug_key():
    """Parse early-return + sibling teardown raise must still omit ``debug``."""

    class _RaisingTeardown(SchemaExtension):
        def on_operation(self):
            yield
            raise RuntimeError("teardown boom")

    schema = strawberry.Schema(
        query=_OkQuery,
        extensions=[_RaisingTeardown, DjangoDebugExtension],
    )
    result = schema.execute_sync("{ ok")

    assert result.errors
    assert "debug" not in (result.extensions or {})


@override_settings(DEBUG=True)
async def test_async_validation_failure_with_raising_teardown_publishes_no_debug_key():
    """Async validation sets ``PreExecutionError`` on context before teardown.

    That assignment must not be mistaken for GraphQL execution, or the
    recovery path's second ``get_results`` would publish ``debug``.
    """

    class _RaisingTeardown(SchemaExtension):
        def on_operation(self):
            yield
            raise RuntimeError("teardown boom")

    schema = strawberry.Schema(
        query=_OkQuery,
        extensions=[_RaisingTeardown, DjangoDebugExtension],
    )
    result = await schema.execute("{ definitelyNotAField }")

    assert result.errors
    assert "debug" not in (result.extensions or {})


@override_settings(DEBUG=True)
def test_generic_recovery_alone_calls_get_results_once():
    """A teardown failure on an EXECUTED operation is one recovery, one get_results call."""
    calls = []

    class _CountingDebug(DjangoDebugExtension):
        def get_results(self):
            calls.append(1)
            return super().get_results()

    class _RaisingTeardown(SchemaExtension):
        def on_operation(self):
            yield
            raise RuntimeError("teardown boom")

    schema = strawberry.Schema(query=_OkQuery, extensions=[_RaisingTeardown, _CountingDebug])
    result = schema.execute_sync("{ ok }")

    assert result.errors  # the coerced teardown failure
    assert len(calls) == 1


@override_settings(DEBUG=True)
def test_parse_and_validation_failures_have_no_debug_key():
    schema = strawberry.Schema(query=_OkQuery, extensions=[DjangoDebugExtension])

    parse_result = schema.execute_sync("{ ok")  # syntax error
    assert parse_result.errors
    assert "debug" not in (parse_result.extensions or {})

    validation_result = schema.execute_sync("{ definitelyNotAField }")
    assert validation_result.errors
    assert "debug" not in (validation_result.extensions or {})


@override_settings(DEBUG=True)
def test_executed_no_op_operation_carries_both_empty_lists(default_wrapper):
    schema = strawberry.Schema(query=_OkQuery, extensions=[DjangoDebugExtension])

    result = schema.execute_sync("{ __typename }")

    assert result.errors is None
    assert result.extensions["debug"] == {"sql": [], "exceptions": []}


# ---------------------------------------------------------------------------
# Scenario 8 - the restore contract around real sync execution.
# ---------------------------------------------------------------------------


@override_settings(DEBUG=True)
@pytest.mark.parametrize("prior", [False, True])
def test_execute_sync_restores_the_prior_flag_value(default_wrapper, prior):
    default_wrapper.force_debug_cursor = prior
    schema = strawberry.Schema(query=_OkQuery, extensions=[DjangoDebugExtension])

    result = schema.execute_sync("{ ok }")

    assert result.errors is None
    assert result.extensions["debug"]["exceptions"] == []
    # Saved-value restore: the nested-CaptureQueriesContext guarantee.
    assert default_wrapper.force_debug_cursor is prior
    assert debug_module._coordinator._active == {}


# ---------------------------------------------------------------------------
# Scenario 12 - masking-extension ordering, both directions.
# ---------------------------------------------------------------------------


@override_settings(DEBUG=True)
@pytest.mark.parametrize("debug_after_masking", [True, False])
def test_mask_errors_ordering_controls_exception_visibility(debug_after_masking):
    if debug_after_masking:
        extension_list = [lambda: MaskErrors(), DjangoDebugExtension]
    else:
        extension_list = [DjangoDebugExtension, lambda: MaskErrors()]
    schema = strawberry.Schema(query=_BoomQuery, extensions=extension_list)

    result = schema.execute_sync("{ boom }")

    # The GraphQL errors are masked either way.
    assert [error.message for error in result.errors] == ["Unexpected error."]
    exceptions = result.extensions["debug"]["exceptions"]
    if debug_after_masking:
        # Debug tears down FIRST (LIFO), reading the originals.
        assert len(exceptions) == 1
        assert exceptions[0]["excType"] == "<class 'ValueError'>"
        assert exceptions[0]["message"] == "sensitive boom detail"
    else:
        # Masking already stripped original_error before debug's teardown.
        assert exceptions == []


# ---------------------------------------------------------------------------
# Scenario 14 - merge precedence and result-map replacement.
# ---------------------------------------------------------------------------


class _FirstProbe(SchemaExtension):
    def get_results(self):
        return {"probe": "first", "only_first": 1}


class _SecondProbe(SchemaExtension):
    def get_results(self):
        return {"probe": "second"}


class _ContextResultsSeeder(SchemaExtension):
    def on_operation(self):
        self.execution_context.extensions_results = {"probe": "context"}
        yield


class _ResultMapPrepopulator(SchemaExtension):
    def on_operation(self):
        yield
        self.execution_context.result.extensions = {"sentinel": True}


def test_extension_list_order_wins_same_key_collisions_sync():
    schema = strawberry.Schema(query=_OkQuery, extensions=[_FirstProbe, _SecondProbe])

    result = schema.execute_sync("{ ok }")

    assert result.extensions["probe"] == "second"  # later-listed entry wins
    assert result.extensions["only_first"] == 1


async def test_extension_list_order_wins_same_key_collisions_async():
    schema = strawberry.Schema(query=_OkQuery, extensions=[_FirstProbe, _SecondProbe])

    result = await schema.execute("{ ok }")

    assert result.extensions["probe"] == "second"
    assert result.extensions["only_first"] == 1


async def test_async_context_results_overlay_has_final_precedence():
    schema = strawberry.Schema(
        query=_OkQuery,
        extensions=[_FirstProbe, _SecondProbe, _ContextResultsSeeder],
    )

    result = await schema.execute("{ ok }")

    assert result.extensions["probe"] == "context"


def test_sync_runner_has_no_context_results_overlay():
    schema = strawberry.Schema(
        query=_OkQuery,
        extensions=[_FirstProbe, _SecondProbe, _ContextResultsSeeder],
    )

    result = schema.execute_sync("{ ok }")

    assert result.extensions["probe"] == "second"  # the seeded map is never overlaid


async def test_prepopulated_result_extensions_map_is_replaced_not_merged():
    schema = strawberry.Schema(
        query=_OkQuery,
        extensions=[_FirstProbe, _ResultMapPrepopulator],
    )

    async_result = await schema.execute("{ ok }")
    assert "sentinel" not in async_result.extensions
    assert async_result.extensions["probe"] == "first"

    sync_result = schema.execute_sync("{ ok }")
    assert "sentinel" not in sync_result.extensions
    assert sync_result.extensions["probe"] == "first"


# ---------------------------------------------------------------------------
# Scenario 9 - async color: shared-wrapper overlap-safe restore.
# ---------------------------------------------------------------------------


@override_settings(DEBUG=True)
@pytest.mark.parametrize("completion_order", [("a", "b"), ("b", "a")])
async def test_async_overlapping_operations_share_the_wrapper_and_restore(completion_order):
    """Two overlapping async operations refcount one wrapper and restore in any order.

    The wrapper is materialized in the parent async context BEFORE either task
    is created, both tasks inherit it (asserted by identity inside each
    operation), the raising resolvers block until the coordinator depth
    reaches two, and the releases run in both completion orders. SQL content
    is deliberately NOT asserted beyond type - the documented async
    thread-locality caveat.
    """
    parent_wrapper = connections["default"]
    original_flag = parent_wrapper.force_debug_cursor
    release_events = {"a": asyncio.Event(), "b": asyncio.Event()}
    observed_wrappers = {}

    @strawberry.type
    class _AsyncBoomQuery:
        @strawberry.field
        async def boom(self, marker: str) -> int:
            observed_wrappers[marker] = connections["default"]
            await release_events[marker].wait()
            raise ValueError(f"boom-{marker}")

    schema = strawberry.Schema(query=_AsyncBoomQuery, extensions=[DjangoDebugExtension])

    tasks = {
        marker: asyncio.create_task(schema.execute(f'{{ boom(marker: "{marker}") }}'))
        for marker in ("a", "b")
    }
    try:
        for _ in range(10_000):
            state = debug_module._coordinator._active.get(parent_wrapper)
            if state is not None and state.depth == 2:
                break
            await asyncio.sleep(0)
        else:
            raise AssertionError("coordinator never reached depth 2")

        results = {}
        for marker in completion_order:
            release_events[marker].set()
            results[marker] = await tasks[marker]
    finally:
        for event in release_events.values():
            event.set()  # never leave a task blocked on a failed assertion

    for marker in ("a", "b"):
        assert observed_wrappers[marker] is parent_wrapper  # inherited, not re-materialized
        payload = results[marker].extensions["debug"]
        assert isinstance(payload["sql"], list)  # type only - async SQL fidelity not claimed
        assert [row["message"] for row in payload["exceptions"]] == [f"boom-{marker}"]

    assert debug_module._coordinator._active == {}
    assert parent_wrapper.force_debug_cursor is original_flag


# ---------------------------------------------------------------------------
# Scenario 15 - nested / reentrant same-thread attribution.
# ---------------------------------------------------------------------------


@override_settings(DEBUG=True)
@pytest.mark.django_db
def test_nested_sync_operations_share_the_log_and_cross_attribute(default_wrapper):
    original_flag = default_wrapper.force_debug_cursor
    inner_holder = {}

    @strawberry.type
    class _InnerQuery:
        @strawberry.field
        def inner_ping(self) -> int:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 2")
            return 2

    inner_schema = strawberry.Schema(query=_InnerQuery, extensions=[DjangoDebugExtension])

    @strawberry.type
    class _OuterQuery:
        @strawberry.field
        def outer_ping(self) -> int:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            inner_holder["result"] = inner_schema.execute_sync("{ innerPing }")
            return 1

    outer_schema = strawberry.Schema(query=_OuterQuery, extensions=[DjangoDebugExtension])
    outer_result = outer_schema.execute_sync("{ outerPing }")

    assert outer_result.errors is None
    inner_result = inner_holder["result"]
    inner_sql = [row["sql"] for row in inner_result.extensions["debug"]["sql"]]
    outer_sql = [row["sql"] for row in outer_result.extensions["debug"]["sql"]]

    # The inner payload owns its interval only.
    assert any("SELECT 2" in statement for statement in inner_sql)
    assert not any("SELECT 1" in statement for statement in inner_sql)
    # The outer payload intentionally also includes the nested interval.
    assert any("SELECT 1" in statement for statement in outer_sql)
    assert any("SELECT 2" in statement for statement in outer_sql)

    assert debug_module._coordinator._active == {}
    assert default_wrapper.force_debug_cursor is original_flag


# ---------------------------------------------------------------------------
# Scenario 13 - concurrent sync instance isolation at the dependency floor.
#
# The regression that fails under the pre-0.316 cached ``_sync_extensions``
# lifecycle. Maintainers run this same test - selected by node id, never a
# copied script - in an isolated ``strawberry-graphql==0.316.0`` environment:
#
#   uv run pytest -o addopts="-v -n0" \
#     "tests/extensions/test_debug.py::test_concurrent_sync_operations_use_isolated_instances"
# ---------------------------------------------------------------------------


@override_settings(DEBUG=True)
def test_concurrent_sync_operations_use_isolated_instances():
    """Two concurrent sync operations never see each other's exception payloads.

    The resolvers perform NO ORM work in the executor threads (concurrent
    SQLite ORM would add unrelated locking/lifetime problems); isolation is
    proved by distinct resolver exception markers, the per-thread wrapper
    identities, and each thread-local wrapper's restored flag. Distinct
    executor-thread wrappers prove FRESH extension instances - not
    same-wrapper coordinator refcounting, which the async overlap test owns.
    """
    barrier = threading.Barrier(2)

    @strawberry.type
    class _ConcurrentBoomQuery:
        @strawberry.field
        def boom(self, marker: str) -> int:
            barrier.wait(timeout=10)
            raise ValueError(f"marker-{marker}")

    schema = strawberry.Schema(query=_ConcurrentBoomQuery, extensions=[DjangoDebugExtension])
    thread_wrappers = {}
    restored_flags = {}

    def _run(marker):
        thread_wrappers[marker] = connections["default"]
        result = schema.execute_sync(f'{{ boom(marker: "{marker}") }}')
        restored_flags[marker] = connections["default"].force_debug_cursor
        return result

    with ThreadPoolExecutor(max_workers=2) as pool:
        future_a = pool.submit(_run, "a")
        future_b = pool.submit(_run, "b")
        result_a = future_a.result(timeout=30)
        result_b = future_b.result(timeout=30)

    assert thread_wrappers["a"] is not thread_wrappers["b"]  # distinct thread-local wrappers
    messages_a = [row["message"] for row in result_a.extensions["debug"]["exceptions"]]
    messages_b = [row["message"] for row in result_b.extensions["debug"]["exceptions"]]
    assert messages_a == ["marker-a"]  # only its OWN marker - fresh instances
    assert messages_b == ["marker-b"]
    assert restored_flags == {"a": False, "b": False}
    assert debug_module._coordinator._active == {}


# ---------------------------------------------------------------------------
# Scenario 17 - diagnostic non-interference (the two-phase failure policy's
# post-execution half).
# ---------------------------------------------------------------------------


@override_settings(DEBUG=True)
def test_sql_diagnostic_failure_degrades_payload_and_preserves_the_result(default_wrapper, caplog):
    """A malformed backend log entry degrades ``sql`` to the serialized prefix."""

    @strawberry.type
    class _InjectingQuery:
        @strawberry.field
        def ok(self) -> str:
            # Injected at the log boundary while the bracket is active: one
            # good entry, then one whose duration cannot serialize.
            connections["default"].queries_log.append({"sql": "SELECT 90", "time": "0.001"})
            connections["default"].queries_log.append({"sql": "SELECT 91", "time": "nope"})
            return "ok"

    schema = strawberry.Schema(query=_InjectingQuery, extensions=[DjangoDebugExtension])
    log = connections["default"].queries_log
    entries_before = len(log)

    try:
        with caplog.at_level(logging.ERROR, logger="django_strawberry_framework"):
            result = schema.execute_sync("{ ok }")

        # The real result is untouched - the diagnostic never replaces it.
        assert result.errors is None
        assert result.data == {"ok": "ok"}
        payload = result.extensions["debug"]
        assert [row["sql"] for row in payload["sql"]] == ["SELECT 90"]  # the serialized prefix
        assert payload["exceptions"] == []
        assert any(
            "SQL diagnostic collection failed" in record.message for record in caplog.records
        )
        # Restoration is separately protected from the diagnostic failure.
        assert default_wrapper.force_debug_cursor is False
        assert debug_module._coordinator._active == {}
    finally:
        # Remove exactly what this test appended to the SHARED default log
        # (zero, one, or two entries under every failure mode) - sibling
        # tests snapshot against it.
        while len(log) > entries_before:
            log.pop()


def test_exception_diagnostic_failure_degrades_to_an_empty_list(caplog):
    """A failing errors read degrades ``exceptions`` to [] without raising."""

    class _ExplodingResult:
        @property
        def errors(self):
            raise RuntimeError("diagnostic errors read failed")

    with caplog.at_level(logging.ERROR, logger="django_strawberry_framework"):
        payload = _build_payload([], _ExplodingResult())

    assert payload == {"sql": [], "exceptions": []}
    assert any(
        "exception diagnostic collection failed" in record.message for record in caplog.records
    )


# ---------------------------------------------------------------------------
# Scenario 18 - the cursor-construction capture-interval boundary.
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_cursor_construction_defines_the_capture_interval(default_wrapper):
    pre_opened_cursor = default_wrapper.cursor()  # a NORMAL cursor, created before acquire
    token = debug_module._coordinator.acquire(default_wrapper)
    try:
        start = len(default_wrapper.queries_log)

        # Direction one: the pre-opened normal cursor stays silent inside the bracket.
        pre_opened_cursor.execute("SELECT 10")
        assert len(default_wrapper.queries_log) == start

        inside_cursor = default_wrapper.cursor()  # a DEBUG cursor, created inside
        inside_cursor.execute("SELECT 11")
        assert len(default_wrapper.queries_log) == start + 1
    finally:
        debug_module._coordinator.release(token)

    # Direction two: the retained debug cursor keeps logging after the release.
    inside_cursor.execute("SELECT 12")
    assert len(default_wrapper.queries_log) == start + 2
    assert "SELECT 12" in default_wrapper.queries_log[-1]["sql"]
    pre_opened_cursor.close()
    inside_cursor.close()


# ---------------------------------------------------------------------------
# Scenario 19 - transaction-boundary scope.
# ---------------------------------------------------------------------------


@override_settings(DEBUG=True)
@pytest.mark.django_db(transaction=True)
def test_resolver_owned_atomic_emits_captured_transaction_rows():
    @strawberry.type
    class _AtomicQuery:
        @strawberry.field
        def write(self) -> int:
            with transaction.atomic(), connection.cursor() as cursor:
                cursor.execute("SELECT 20")
            return 1

    schema = strawberry.Schema(query=_AtomicQuery, extensions=[DjangoDebugExtension])

    result = schema.execute_sync("{ write }")

    assert result.errors is None
    statements = [row["sql"].upper() for row in result.extensions["debug"]["sql"]]
    assert any(statement.startswith("BEGIN") for statement in statements)
    assert any(statement.startswith("COMMIT") for statement in statements)
    begin_rows = [
        row for row in result.extensions["debug"]["sql"] if row["sql"].upper().startswith("BEGIN")
    ]
    assert all(row["isSelect"] is False for row in begin_rows)


@override_settings(DEBUG=True)
@pytest.mark.django_db(transaction=True)
def test_enclosing_transaction_boundary_statements_are_not_captured():
    @strawberry.type
    class _AtomicQuery:
        @strawberry.field
        def write(self) -> int:
            with transaction.atomic(), connection.cursor() as cursor:
                cursor.execute("SELECT 21")
            return 1

    schema = strawberry.Schema(query=_AtomicQuery, extensions=[DjangoDebugExtension])

    # The ATOMIC_REQUESTS shape without rebuilding HTTP infrastructure: the
    # enclosing BEGIN runs before the hook entered and the enclosing COMMIT
    # after it tore down, so neither is captured; the resolver's atomic()
    # inside the outer transaction is a savepoint.
    with transaction.atomic():
        result = schema.execute_sync("{ write }")

    assert result.errors is None
    statements = [row["sql"].upper() for row in result.extensions["debug"]["sql"]]
    assert any("SAVEPOINT" in statement for statement in statements)
    assert not any(statement.startswith("BEGIN") for statement in statements)
    assert not any(statement.startswith("COMMIT") for statement in statements)


# ---------------------------------------------------------------------------
# Scenario 20 - sibling-hook SQL ordering.
# ---------------------------------------------------------------------------


class _MarkerSQLExtension(SchemaExtension):
    """A sibling whose ``on_operation`` performs marker SQL around its yield."""

    def on_operation(self):
        with connection.cursor() as cursor:
            cursor.execute("SELECT 31")  # the setup marker
        yield
        with connection.cursor() as cursor:
            cursor.execute("SELECT 32")  # the teardown marker


@override_settings(DEBUG=True)
@pytest.mark.django_db
@pytest.mark.parametrize("debug_listed_first", [True, False])
def test_sibling_hook_sql_capture_is_list_order_dependent(debug_listed_first):
    if debug_listed_first:
        extension_list = [DjangoDebugExtension, _MarkerSQLExtension]
    else:
        extension_list = [_MarkerSQLExtension, DjangoDebugExtension]
    schema = strawberry.Schema(query=_OkQuery, extensions=extension_list)

    result = schema.execute_sync("{ ok }")

    assert result.errors is None
    statements = [row["sql"] for row in result.extensions["debug"]["sql"]]
    if debug_listed_first:
        # Debug enters first and tears down last: both sibling markers fall
        # inside its active interval.
        assert any("SELECT 31" in statement for statement in statements)
        assert any("SELECT 32" in statement for statement in statements)
    else:
        # The sibling's setup ran before debug acquired, its teardown after
        # debug released: neither marker is captured.
        assert not any("SELECT 31" in statement for statement in statements)
        assert not any("SELECT 32" in statement for statement in statements)


# ---------------------------------------------------------------------------
# spec-048 Decision 5 - the fail-closed gate: the acknowledgement default, the
# inert path's absence of a bracket, and the acknowledged factory's payload.
#
# Live HTTP proof of the same gate (no key / warning / acknowledged payload
# over a real request) lives in the fakeshop tier; these rows own what a
# request cannot show - that the inert path never even enumerates the
# connections, and that the constructor's default is the safe answer.
# ---------------------------------------------------------------------------


def test_zero_argument_construction_defaults_to_the_safe_answer():
    """A bare class entry is built with no arguments, so the default must fail closed."""
    assert DjangoDebugExtension().allow_unsafe_production is False
    assert DjangoDebugExtension(allow_unsafe_production=True).allow_unsafe_production is True

    with pytest.raises(TypeError):
        DjangoDebugExtension(True)  # keyword-only: acknowledging must be SPELLED


@pytest.mark.parametrize(
    "value",
    [
        "false",
        "0",
        "no",
        "",
        1,
        0,
        None,
        [],
    ],
    ids=[
        "string-false",
        "string-zero",
        "string-no",
        "empty-string",
        "truthy-int",
        "falsy-int",
        "none",
        "empty-list",
    ],
)
def test_a_non_bool_acknowledgement_is_refused_at_construction(value):
    """The acknowledgement is a bool, not a truthiness test.

    ``"false"`` is the case that makes this a security row rather than a typing
    nicety: it is the exact literal a deployment reading an environment variable
    straight through would pass, it is TRUTHY, and under a truthiness test it
    would ARM production disclosure in the very act of trying to refuse it. So
    every non-bool - truthy or falsy - is a ``ConfigurationError`` naming the
    value, on the same rule ``ErrorPolicy.enabled`` follows.
    """
    with pytest.raises(ConfigurationError, match="allow_unsafe_production"):
        DjangoDebugExtension(allow_unsafe_production=value)


@override_settings(DEBUG=False)
def test_a_refused_acknowledgement_never_becomes_an_armed_extension():
    """The refusal happens at construction, so no operation can run with it.

    The consequence worth pinning separately from the message: a schema whose
    extensions list carries the misspelled acknowledgement fails when Strawberry
    builds the instance for the operation, rather than answering that operation
    with the disclosure. Nothing partially constructed is left holding a truthy
    flag.
    """
    schema = strawberry.Schema(
        query=_OkQuery,
        extensions=[lambda: DjangoDebugExtension(allow_unsafe_production="false")],
    )
    with pytest.raises(ConfigurationError, match="allow_unsafe_production"):
        schema.execute_sync("{ ok }")


@override_settings(DEBUG=False)
def test_inert_operation_acquires_no_bracket_and_takes_no_snapshot(monkeypatch, caplog):
    """Refusal is inertness, not payload suppression: no acquire, no snapshot, no flag write.

    The connections handler is replaced by one whose ``all()`` raises: the
    acquisition loop and the query-log snapshot are the only two readers of it,
    so reaching either fails the test outright. The real handler is read
    outside the patch to prove every configured flag survives untouched.
    """
    prior_flags = {
        database_connection.alias: database_connection.force_debug_cursor
        for database_connection in connections.all()
    }
    prior_log_lengths = {
        database_connection.alias: len(database_connection.queries_log)
        for database_connection in connections.all()
    }

    def _refuse():
        raise AssertionError("the inert path must never enumerate the connections")

    monkeypatch.setattr(debug_module, "connections", SimpleNamespace(all=_refuse))
    schema = strawberry.Schema(query=_OkQuery, extensions=[DjangoDebugExtension])

    with caplog.at_level(logging.WARNING, logger="django_strawberry_framework"):
        result = schema.execute_sync("{ ok }")

    # The operation itself is untouched - a refusal to disclose is not a refusal.
    assert result.errors is None
    assert result.data == {"ok": "ok"}
    assert "debug" not in (result.extensions or {})
    assert debug_module._coordinator._active == {}
    for database_connection in connections.all():
        alias = database_connection.alias
        assert database_connection.force_debug_cursor is prior_flags[alias]
        assert len(database_connection.queries_log) == prior_log_lengths[alias]
    warnings = [
        record
        for record in caplog.records
        if record.levelno == logging.WARNING and record.name == "django_strawberry_framework"
    ]
    assert len(warnings) == 1
    assert "allow_unsafe_production" in warnings[0].getMessage()


@override_settings(DEBUG=False)
def test_acknowledged_factory_publishes_the_payload_and_logs_no_warning(default_wrapper, caplog):
    """The acknowledgement is the ONE spelling that keeps the payload under DEBUG false."""
    schema = strawberry.Schema(
        query=_OkQuery,
        extensions=[lambda: DjangoDebugExtension(allow_unsafe_production=True)],
    )

    with caplog.at_level(logging.WARNING, logger="django_strawberry_framework"):
        result = schema.execute_sync("{ ok }")

    assert result.extensions["debug"] == {"sql": [], "exceptions": []}
    assert [
        record for record in caplog.records if record.name == "django_strawberry_framework"
    ] == []
    assert default_wrapper.force_debug_cursor is False  # the bracket still restored
    assert debug_module._coordinator._active == {}


@override_settings(DEBUG=False)
def test_acknowledged_factory_stays_fresh_per_operation(default_wrapper):
    """A factory entry is still one instance per operation - no payload carries over."""
    schema = strawberry.Schema(
        query=_BoomQuery,
        extensions=[lambda: DjangoDebugExtension(allow_unsafe_production=True)],
    )

    failing = schema.execute_sync("{ boom }")
    clean = schema.execute_sync("{ ok }")

    assert [row["message"] for row in failing.extensions["debug"]["exceptions"]] == [
        "sensitive boom detail",
    ]
    # The second operation's payload is its own, not the first one's stash.
    assert clean.errors is None
    assert clean.extensions["debug"] == {"sql": [], "exceptions": []}


# ---------------------------------------------------------------------------
# spec-048 Decision 6 - the payload caps, exercised directly against the pure
# ``_apply_payload_caps``: arithmetic this precise cannot be provoked through a
# real operation, so the live tier owns the wiring proof and these rows own the
# cut points, the tail drops, and the shared budget's stop rule.
# ---------------------------------------------------------------------------


def _sql_row(sql):
    """A wire-shaped SQL row whose ONLY string cost is ``sql`` (empty vendor/alias)."""
    return {
        "vendor": "",
        "alias": "",
        "sql": sql,
        "duration": 0.001,
        "isSlow": False,
        "isSelect": True,
    }


def _exception_row(message, stack=""):
    """A wire-shaped exception row whose string cost is ``message`` plus ``stack``."""
    return {"excType": "", "message": message, "stack": stack}


def test_caps_leave_an_empty_payload_with_both_lists_present():
    assert _apply_payload_caps([], []) == {"sql": [], "exceptions": []}


def test_over_long_row_strings_are_cut_at_their_own_limit_and_marked():
    """Each variable-length string has its OWN limit, and only a cut value is marked."""
    payload = _apply_payload_caps(
        [_sql_row("s" * (_SQL_TEXT_CAP + 1)), _sql_row("SELECT 1")],
        [
            _exception_row("m" * (_EXCEPTION_MESSAGE_CAP + 1), "k" * (_EXCEPTION_STACK_CAP + 1)),
            _exception_row("short message", "short stack"),
        ],
    )

    assert payload["sql"][0]["sql"] == "s" * _SQL_TEXT_CAP + _MARKER
    assert payload["exceptions"][0]["message"] == "m" * _EXCEPTION_MESSAGE_CAP + _MARKER
    assert payload["exceptions"][0]["stack"] == "k" * _EXCEPTION_STACK_CAP + _MARKER
    # A short value is returned verbatim - never marked, never padded.
    assert payload["sql"][1]["sql"] == "SELECT 1"
    assert payload["exceptions"][1] == {
        "excType": "",
        "message": "short message",
        "stack": "short stack",
    }
    # Truncation edits the strings only; the derived scalars ride through.
    assert payload["sql"][0]["isSelect"] is True
    assert payload["sql"][0]["duration"] == 0.001


def test_row_count_caps_keep_exactly_the_earliest_rows():
    """The TAIL is dropped: the first rows explain how the operation started."""
    payload = _apply_payload_caps(
        [_sql_row(f"SELECT {index}") for index in range(_SQL_ROW_CAP + 7)],
        [_exception_row(f"boom {index}") for index in range(_EXCEPTION_ROW_CAP + 3)],
    )

    assert [row["sql"] for row in payload["sql"]] == [
        f"SELECT {index}" for index in range(_SQL_ROW_CAP)
    ]
    assert [row["message"] for row in payload["exceptions"]] == [
        f"boom {index}" for index in range(_EXCEPTION_ROW_CAP)
    ]


def test_shared_budget_admits_exceptions_first_and_stops_at_the_first_over_row():
    """One budget, exceptions first, and admission STOPS - it never skips and continues.

    Both families are given rows already at their per-row ceiling plus one tiny
    trailing row each. The tiny rows would fit the leftover budget under a
    skip-and-continue rule, so their absence is what pins the stop.
    """
    exception_cost = _EXCEPTION_MESSAGE_CAP + _EXCEPTION_STACK_CAP
    big_exception_rows = [
        _exception_row("m" * _EXCEPTION_MESSAGE_CAP, "k" * _EXCEPTION_STACK_CAP)
        for _ in range(_EXCEPTION_ROW_CAP - 1)
    ]
    big_sql_rows = [_sql_row("s" * _SQL_TEXT_CAP) for _ in range(_SQL_ROW_CAP - 1)]

    payload = _apply_payload_caps(
        [*big_sql_rows, _sql_row("SELECT tiny")],
        [*big_exception_rows, _exception_row("tiny boom")],
    )

    admitted_exceptions = _PAYLOAD_CAP // exception_cost
    remaining = _PAYLOAD_CAP - admitted_exceptions * exception_cost
    assert len(payload["exceptions"]) == admitted_exceptions
    # Exceptions were admitted FIRST, so SQL only gets what they left behind.
    assert len(payload["sql"]) == remaining // _SQL_TEXT_CAP
    assert all(row["message"] != "tiny boom" for row in payload["exceptions"])
    assert all(row["sql"] != "SELECT tiny" for row in payload["sql"])


def test_build_payload_routes_its_assembled_rows_through_the_caps():
    """The caps are applied BEFORE the stash, not by the caller - the ordering contract."""
    long_message = "m" * (_EXCEPTION_MESSAGE_CAP + 1)
    result = SimpleNamespace(
        errors=[GraphQLError("outer", original_error=ValueError(long_message))],
    )

    payload = _build_payload([], result)

    assert payload["sql"] == []
    assert payload["exceptions"][0]["message"] == "m" * _EXCEPTION_MESSAGE_CAP + _MARKER
