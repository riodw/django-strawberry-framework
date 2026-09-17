"""The operation-state boundary: what one operation reads, writes, and leaves behind.

``extensions/operation_state.py`` is the package's answer to an engine that
resolves an extension entry into the SAME object for every operation. What it
has to be true of is narrow and hard to see from a response, so the rows here
drive the seams directly:

- the engine's assignment records nothing for a ``DjangoSchema``, so no failure
  and no resolver can leave a request behind in front of the runner;
- one operation's state is bound for the operation, for result collection and
  for every streaming frame, and reset afterwards;
- a failure anywhere in front of the operation - inside the engine's assignment
  loop, inside runner construction, between the runner and ``operation()`` -
  leaves nothing bound and nothing retained;
- a task that copied a binding and outlived the runner reads no state at all;
- the binding carrier is settled once per extension and a second constructor
  call is refused.

The disclosure these prevent is asserted where a client can see it -
``examples/fakeshop/test_query/test_resource_policy_api.py`` and
``test_error_policy_api.py`` carry the shared-entry matrices over both view
colors. This module holds what no request can express.
"""

from __future__ import annotations

import asyncio
import contextvars
import gc
import weakref
from collections.abc import AsyncGenerator
from types import SimpleNamespace

import pytest
import strawberry
from strawberry.extensions.base_extension import SchemaExtension

from django_strawberry_framework import DjangoSchema
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.extensions import (
    DjangoDebugExtension,
    DjangoErrorPolicyExtension,
    DjangoResourcePolicyExtension,
)
from django_strawberry_framework.extensions.operation_state import (
    _OPERATION_CARRIERS,
    _RUNNER_SCOPES,
    OperationState,
    _OperationBoundExtension,
    operation_is_nested,
)
from django_strawberry_framework.optimizer import DjangoOptimizerExtension
from django_strawberry_framework.optimizer._context import active_optimizer, optimizer_value
from django_strawberry_framework.resource_policy import armed_resource_policy


@strawberry.type
class _Query:
    """One field, so an operation exists to bind state for."""

    @strawberry.field
    def hello(self) -> str:
        return "hi"


class _Probe(_OperationBoundExtension):
    """An operation-bound extension that records what it saw, per hook."""

    def __init__(self) -> None:
        super().__init__()
        self.seen: list[object] = []

    def on_operation(self):
        """Record the context bound for this operation, on both halves."""
        self.seen.append(self.execution_context)
        yield
        self.seen.append(self.execution_context)

    def get_results(self) -> dict:
        """Record what result collection sees, which upstream runs after teardown."""
        self.seen.append(("results", self.execution_context))
        return {}


class _SilentProbe(_OperationBoundExtension):
    """An operation-bound extension that holds the hook without holding the operation.

    The retention rows take a weak reference to a request context and assert it
    is collected once the operation is over. ``_Probe`` appends every
    ``execution_context`` it is handed to a list, so using it there would make
    the instrument itself the strong reference the row is looking for - the
    assertion could never pass, and its failure would say nothing about the
    runner. This one binds and records nothing.
    """

    def on_operation(self):
        """Bind for the operation and keep no part of it."""
        yield


class _Unbuilt(_OperationBoundExtension):
    """A subclass whose ``__init__`` never reaches the one that settles the carrier."""

    def __init__(self) -> None:
        pass


def test_a_subclass_that_skipped_the_base_constructor_is_refused_not_approximated():
    """No carrier means no place to bind, and reading the last operation's is the defect.

    An extension whose ``__init__`` never ran this package's would have nowhere
    to put the operation's state, so every read would answer with whatever was
    left over. Refusing names the omission; falling back would reintroduce it.
    """
    extension = _Unbuilt()
    with pytest.raises(ConfigurationError, match="has to call super"):
        _ = extension.execution_context


def test_an_assignment_under_a_django_schema_records_nothing_to_be_read_later():
    """The engine's assignment is compatibility glue, not a source of state.

    Upstream assigns on every resolved member and then hands the runner the same
    context, so a record of the assignment would carry nothing the runner is not
    given - and would be a place for a request to be left when something between
    the two raises. Nothing is written, so the window in front of the runner
    reads as what it is: no operation.
    """
    extension = _Probe()
    context = SimpleNamespace(schema=DjangoSchema(query=_Query))

    extension.execution_context = context

    assert extension.execution_context is None
    assert extension._operation_state() is None
    assert extension.__dict__.get("_compatibility_state") is None


def test_the_runner_builds_every_state_from_the_context_it_is_handed():
    """No assignment is needed for the runner to answer for the operation.

    The runner's argument is the same object upstream assigned, so an extension
    that was never assigned at all still gets this operation's state - and what
    the state names is that context and nothing a previous operation left.
    """
    schema = DjangoSchema(query=_Query, extensions=[_Probe])
    # A stand-in for the engine's ``ExecutionContext``, carrying the three
    # attributes an extension scope reads off one: the schema it belongs to,
    # the request context value, and the document text.
    context = SimpleNamespace(schema=schema, context=_RequestContext(), query="{ hello }")
    extensions = schema.get_extensions(sync=True)
    probe = next(entry for entry in extensions if isinstance(entry, _Probe))

    runner = schema.create_extensions_runner(context, extensions)

    assert probe.execution_context is None  # nothing is bound outside a scope
    with runner.operation():
        assert probe.execution_context is context
    assert probe.execution_context is None


@pytest.mark.parametrize(
    "assigned",
    [None, "forged"],
    ids=["none", "a-forged-context-naming-the-real-schema"],
)
def test_a_resolver_assigning_a_context_records_and_retains_nothing(assigned):
    """A resolver holds the extension, so the setter is reachable from a request.

    Assigning a context of its own - including one naming the real schema, which
    is what a handoff protocol would have had to accept as the engine's - must
    leave the running operation reading its own state, retain nothing for the
    next request, and be uncollectible by nothing.
    """
    shared = _Probe()
    schema = DjangoSchema(query=_Query, extensions=[lambda: shared])

    class _Forged:
        """A context object a resolver could build, naming the real schema."""

        def __init__(self, schema):
            self.schema = schema

    forged = None if assigned is None else _Forged(schema)
    forged_ref = None if forged is None else weakref.ref(forged)

    shared.execution_context = forged
    assert shared.execution_context is None
    assert shared._operation_state() is None

    del forged
    gc.collect()
    assert forged_ref is None or forged_ref() is None

    assert schema.execute_sync("{ hello }").data == {"hello": "hi"}
    assert shared.execution_context is None


def test_result_collection_reads_the_operations_own_state():
    """Upstream collects results after the synchronous operation teardown unwound.

    Without a binding around collection, an extension whose payload is operation
    state would answer for no operation - and the way back from that is to leave
    the payload on the shared extension, which is the stale-payload disclosure.
    """
    probe_holder = []

    class _Recording(_Probe):
        def __init__(self) -> None:
            super().__init__()
            probe_holder.append(self)

    schema = DjangoSchema(query=_Query, extensions=[_Recording])
    result = schema.execute_sync("{ hello }")

    assert result.errors is None
    probe = probe_holder[-1]
    collected = [entry for entry in probe.seen if isinstance(entry, tuple)]
    assert len(collected) == 1
    assert collected[0][1] is not None
    assert probe.execution_context is None  # and nothing survives the operation


@pytest.mark.asyncio
async def test_result_collection_reads_the_operations_own_state_on_the_async_path():
    """The async twin, whose collection can also run inside an early-return scope."""
    probe_holder = []

    class _Recording(_Probe):
        def __init__(self) -> None:
            super().__init__()
            probe_holder.append(self)

    schema = DjangoSchema(query=_Query, extensions=[_Recording])
    result = await schema.execute("{ hello }")

    assert result.errors is None
    probe = probe_holder[-1]
    assert [entry for entry in probe.seen if isinstance(entry, tuple)]
    assert probe.execution_context is None


def test_a_failure_between_the_runner_and_the_operation_retains_nothing():
    """The regression that proves the handoff is cleaned up during runner construction.

    A consumer extension whose middleware capability check raises fails upstream
    after ``create_extensions_runner`` returned and before ``operation()`` is
    entered - the one window with no operation ``finally`` behind it. The
    request's context and everything it reached must still be collectable, and
    the shared extension must have no current state.
    """

    class _HostileCapability(SchemaExtension):
        """Refuse the capability probe upstream makes while building the middleware."""

        @classmethod
        def _implements_resolve(cls) -> bool:
            raise RuntimeError("capability probe failed")

    class _RequestContext:
        """A context object a weak reference can be taken of, so reachability is askable."""

    shared = _Probe()
    sentinel = _RequestContext()
    schema = DjangoSchema(query=_Query, extensions=[lambda: shared, _HostileCapability])
    sentinel_ref = weakref.ref(sentinel)

    with pytest.raises(RuntimeError, match="capability probe failed"):
        schema.execute_sync("{ hello }", context_value=sentinel)

    del sentinel
    gc.collect()
    assert sentinel_ref() is None
    assert shared.execution_context is None
    assert shared._operation_state() is None

    schema_without_the_hostile_entry = DjangoSchema(query=_Query, extensions=[lambda: shared])
    assert schema_without_the_hostile_entry.execute_sync("{ hello }").errors is None


def test_a_binding_that_fails_partway_unwinds_the_ones_already_made():
    """All-or-nothing, so a half-bound operation never runs.

    The second extension has no carrier, so binding it raises after the first
    one bound. Leaving that binding in place would leak one operation's state
    into whatever the task did next.
    """
    good = _Probe()
    schema = DjangoSchema(query=_Query, extensions=[lambda: good, lambda: _Unbuilt()])

    with pytest.raises(ConfigurationError, match="has to call super"):
        schema.execute_sync("{ hello }")

    assert good.execution_context is None
    assert good._operation_state() is None


@pytest.mark.asyncio
async def test_a_binding_that_fails_partway_unwinds_on_the_async_path_too():
    """The async twin: one primitive, two protocol adapters, one decision."""
    good = _Probe()
    schema = DjangoSchema(query=_Query, extensions=[lambda: good, lambda: _Unbuilt()])

    with pytest.raises(ConfigurationError, match="has to call super"):
        await schema.execute("{ hello }")

    assert good.execution_context is None
    assert good._operation_state() is None


def test_a_hook_that_raises_while_setting_up_still_resets_every_binding():
    """The wrapped scope failing is not the binding failing, and both have to unwind."""

    class _RaisingSetup(SchemaExtension):
        def on_operation(self):
            raise RuntimeError("setup refused")
            yield  # pragma: no cover - unreachable, the hook raises first

    shared = _Probe()
    schema = DjangoSchema(query=_Query, extensions=[lambda: shared, _RaisingSetup])

    result = schema.execute_sync("{ hello }")

    assert result.errors is not None
    assert shared.execution_context is None
    assert shared._operation_state() is None


@pytest.mark.asyncio
async def test_a_hook_that_raises_while_setting_up_resets_on_the_async_path_too():
    """The async twin of the wrapped-scope failure."""

    class _RaisingSetup(SchemaExtension):
        async def on_operation(self):
            raise RuntimeError("setup refused")
            yield  # pragma: no cover - unreachable, the hook raises first

    shared = _Probe()
    schema = DjangoSchema(query=_Query, extensions=[lambda: shared, _RaisingSetup])

    result = await schema.execute("{ hello }")

    assert result.errors is not None
    assert shared.execution_context is None
    assert shared._operation_state() is None


@pytest.mark.asyncio
async def test_a_closed_stream_leaves_no_state_bound_and_the_next_operation_is_clean():
    """The streaming runner outlives the operation scope, and its binding must not.

    A generator closed before it completes still unwinds its ``finally``, so the
    binding resets there; the following operation has to start with nothing
    inherited - no context pointer, and no payload.
    """
    shared = _Probe()
    schema = DjangoSchema(query=_Query, extensions=[lambda: shared])

    stream = await schema.stream("{ hello }")
    first = await anext(stream)
    assert first.errors is None
    await stream.aclose()

    assert shared.execution_context is None
    assert shared._operation_state() is None

    after = await schema.execute("{ hello }")
    assert after.errors is None
    assert shared.execution_context is None


@pytest.mark.asyncio
async def test_a_cancelled_stream_leaves_no_state_bound_either():
    """Cancellation unwinds the generator's ``finally``, and the binding resets there.

    A transport that drops a subscription cancels the task driving it rather than
    closing it politely. The runner's operation scope is inside that generator,
    so this is the path its reset has to survive; what the NEXT operation starts
    with is the assertion.
    """
    shared = _Probe()
    schema = DjangoSchema(query=_Query, extensions=[lambda: shared])
    started = asyncio.Event()

    async def _drive():
        stream = await schema.stream("{ hello }")
        async for _frame in stream:
            started.set()
            await asyncio.sleep(3600)

    task = asyncio.create_task(_drive())
    await asyncio.wait_for(started.wait(), timeout=5)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    assert shared.execution_context is None
    assert shared._operation_state() is None

    after = await schema.execute("{ hello }")
    assert after.errors is None
    assert shared.execution_context is None


@pytest.mark.parametrize(
    ("factory", "refusal"),
    [
        (DjangoResourcePolicyExtension, "resource-policy extension is configured"),
        (DjangoErrorPolicyExtension, "extension is configured when it is constructed"),
        (DjangoDebugExtension, "debug extension is configured"),
    ],
    ids=["resource-policy", "error-policy", "debug"],
)
def test_rerunning_a_constructor_on_an_accepted_extension_is_refused(factory, refusal):
    """An accepted instance is reachable from every resolver, and so is its ``__init__``.

    A second call would mint a second binding carrier, leaving the runner
    binding one variable while every read answers from another - which is the
    same permanently-absent state a stale one is.
    """
    extension = factory()
    with pytest.raises(ConfigurationError, match=refusal):
        extension.__init__()


def test_rerunning_the_optimizer_constructor_is_refused():
    """The same refusal for the extension whose documented shape IS a singleton.

    Written on its own rather than as a row of the table above: the class may
    not appear inside a sequence literal, which is the shape
    ``tests/test_ci_governance.py`` sweeps for to keep a bare optimizer class out
    of any ``extensions=`` list.
    """
    extension = DjangoOptimizerExtension()
    with pytest.raises(ConfigurationError, match="optimizer extension is configured"):
        extension.__init__()


def test_a_resolver_cannot_replace_the_binding_carrier_or_rerun_the_constructor():
    """The mechanism that CARRIES operation state is state in its own right.

    Distinct from the configuration-tamper rows: those are about the policy a
    request is enforced by, this is about the object every one of those reads
    goes through. A resolver holds the extension through
    ``info.schema.extensions``, so it can assign over the context, write into
    ``__dict__``, and call ``__init__`` again - and none of the three may change
    what this operation reads or what the next one gets.
    """
    shared = _Probe()
    attempts: list[str] = []

    @strawberry.type
    class TamperQuery:
        @strawberry.field
        def tamper(self, info: strawberry.Info) -> str:
            during = shared.execution_context
            for name, attempt in (
                ("assign-the-context", lambda: setattr(shared, "execution_context", None)),
                ("inject-a-carrier", lambda: shared.__dict__.update(_compatibility_state=None)),
                ("rerun-the-constructor", shared.__init__),
            ):
                try:
                    attempt()
                except ConfigurationError:
                    attempts.append(f"{name}: refused")
                else:
                    attempts.append(f"{name}: ignored")
            assert shared.execution_context is during, "the running operation lost its state"
            return "tampered"

        @strawberry.field
        def hello(self) -> str:
            return "hi"

    schema = DjangoSchema(query=TamperQuery, extensions=[lambda: shared])

    attacked = schema.execute_sync("{ tamper }")
    assert attacked.errors is None, attacked.errors
    assert attempts == [
        "assign-the-context: ignored",
        "inject-a-carrier: ignored",
        "rerun-the-constructor: refused",
    ]

    after = schema.execute_sync("{ hello }")
    assert after.data == {"hello": "hi"}
    assert shared.execution_context is None
    assert shared._operation_state() is None


def test_a_carrier_is_settled_once_per_extension_and_dies_with_it():
    """The carrier is held for the extension, not by anything that outlives it."""
    extension = _Probe()
    assert _OPERATION_CARRIERS.settled(extension)
    assert _OPERATION_CARRIERS.recall(extension) is _OPERATION_CARRIERS.recall(extension)

    reference = weakref.ref(extension)
    del extension
    gc.collect()
    assert reference() is None


def test_a_plain_strawberry_schema_gets_operation_local_state_from_the_instance():
    """No package runner, so the fresh instance itself is the operation.

    A class entry and a fresh factory build one extension per operation on any
    schema, so holding the state on the instance is operation-local for exactly
    the entries a raw schema is documented to use. Nothing is queued for a
    runner that will never claim it.
    """
    extension = _Probe()
    context = SimpleNamespace(schema=strawberry.Schema(query=_Query))

    extension.execution_context = context

    assert extension.execution_context is context
    state = extension._operation_state()
    assert isinstance(state, OperationState)
    assert state.execution_context is context

    extension.execution_context = None
    assert extension.execution_context is None
    assert extension._operation_state() is None


def test_a_context_that_refuses_to_say_which_schema_it_belongs_to_takes_the_local_path():
    """An unreadable ``schema`` is not a claim that a package runner is coming."""

    class _Hostile:
        @property
        def schema(self):
            raise RuntimeError("no")

    extension = _Probe()
    context = _Hostile()

    extension.execution_context = context

    assert extension.execution_context is context


def test_nested_execution_restores_the_outer_operations_state():
    """The inner operation binds its own state and the outer one gets its own back."""
    shared = _Probe()
    outer_during: list[object] = []

    @strawberry.type
    class NestingQuery:
        @strawberry.field
        def nested(self, info: strawberry.Info) -> str:
            before = shared.execution_context
            inner = info.schema.execute_sync("{ hello }")
            assert inner.errors is None, inner.errors
            outer_during.append((before, shared.execution_context))
            return "done"

        @strawberry.field
        def hello(self) -> str:
            return "hi"

    schema = DjangoSchema(query=NestingQuery, extensions=[lambda: shared])
    result = schema.execute_sync("{ nested }")

    assert result.errors is None
    before, after = outer_during[0]
    assert before is after
    assert after.query == "{ nested }"


# ---------------------------------------------------------------------------
# Failures in front of the operation, where no package teardown exists yet.
# ---------------------------------------------------------------------------


class _RefusingAssignment(SchemaExtension):
    """A consumer entry whose ``execution_context`` setter raises, as one may."""

    armed = True

    @property
    def execution_context(self):
        """Whatever this extension was last given, which is nothing while armed."""
        return self.__dict__.get("_context")

    @execution_context.setter
    def execution_context(self, value) -> None:
        if type(self).armed:
            raise RuntimeError("assignment refused")
        self.__dict__["_context"] = value


class _RequestContext:
    """A request context value a weak reference can be taken of."""


async def _run_execute_sync(schema, context_value):
    """Run one synchronous operation, awaited like its two siblings."""
    schema.execute_sync("{ hello }", context_value=context_value)


async def _run_execute(schema, context_value):
    """Run one asynchronous operation."""
    await schema.execute("{ hello }", context_value=context_value)


async def _run_stream(schema, context_value):
    """Consume one streamed operation, which is where its assignment loop runs."""
    stream = await schema.stream("{ hello }", context_value=context_value)
    async for _frame in stream:
        pass


@pytest.mark.parametrize(
    "run",
    [_run_execute_sync, _run_execute, _run_stream],
    ids=["execute_sync", "execute", "stream"],
)
@pytest.mark.asyncio
async def test_a_setter_raising_in_the_engines_assignment_loop_leaves_no_request_behind(run):
    """Upstream spells the assignment loop three times, and all three run before the runner.

    A later entry's setter raising there is a failure with no operation teardown
    to run and no runner to own one: whatever the loop had already handed out
    would be held for as long as the task lived, and the shared extension would
    go on answering with the refused request's context. Nothing is handed out,
    so there is nothing to leave behind.
    """
    shared = _Probe()
    schema = DjangoSchema(query=_Query, extensions=[lambda: shared, _RefusingAssignment])
    sentinel = _RequestContext()
    reference = weakref.ref(sentinel)

    with pytest.raises(RuntimeError, match="assignment refused"):
        await run(schema, sentinel)

    assert shared.execution_context is None
    assert shared._operation_state() is None

    del sentinel
    gc.collect()
    assert reference() is None

    unrefused = DjangoSchema(query=_Query, extensions=[lambda: shared])
    assert unrefused.execute_sync("{ hello }").errors is None
    assert shared.execution_context is None


def test_a_state_constructor_that_raises_retains_neither_the_context_nor_a_partial_set():
    """Runner construction is in the same window, and fails the same way.

    A subclass may build its own operation state, so its constructor is consumer
    code running while the runner is built. What must not survive it is the
    request it was building state for, or a half-built set of bindings for the
    extensions that came before it.
    """

    class _RefusingState(_OperationBoundExtension):
        """An operation-bound extension whose state constructor refuses."""

        def _new_operation_state(self, execution_context):
            raise RuntimeError("state refused")

    shared = _Probe()
    schema = DjangoSchema(query=_Query, extensions=[lambda: shared, _RefusingState])
    sentinel = _RequestContext()
    reference = weakref.ref(sentinel)

    with pytest.raises(RuntimeError, match="state refused"):
        schema.execute_sync("{ hello }", context_value=sentinel)

    assert shared.execution_context is None
    assert shared._operation_state() is None

    del sentinel
    gc.collect()
    assert reference() is None


# ---------------------------------------------------------------------------
# A task that copied a binding and outlived the runner that made it.
# ---------------------------------------------------------------------------


def _spawning_schema(shared, seen, release):
    """A schema whose resolver starts a task that reads the extension now and later.

    The child's first read happens while the operation is still bound and is
    recorded as a fact, not as the state itself, so the instrument holds nothing
    the retention rows are waiting to see collected. Without it, "never bound"
    and "unbound when the scope ended" would produce the same ``None``.
    """

    @strawberry.type
    class SpawningQuery:
        @strawberry.field
        async def spawn(self, info: strawberry.Info) -> str:
            async def child():
                seen["bound_during"] = shared._operation_state() is not None
                await release.wait()
                seen["state"] = shared._operation_state()
                seen["context"] = shared.execution_context

            seen["task"] = asyncio.ensure_future(child())
            # Yield once so the child takes its first read inside the operation.
            await asyncio.sleep(0)
            return "spawned"

    return DjangoSchema(query=SpawningQuery, extensions=[lambda: shared])


@pytest.mark.asyncio
async def test_a_task_started_inside_the_operation_reads_nothing_once_it_ends():
    """Resetting a token repairs the task that bound it, and only that task.

    A task created while a binding is in force gets a COPY of the context, which
    the reset at teardown does not rewrite. A background job outliving its
    request would therefore keep reading the completed operation's context - and
    keep that request's context value, variables and result alive for as long as
    it ran. The binding is a weak reference to state the runner owns, so the
    copy answers with nothing once the operation is over.
    """
    shared = _SilentProbe()
    seen: dict = {}
    release = asyncio.Event()
    schema = _spawning_schema(shared, seen, release)
    sentinel = _RequestContext()
    reference = weakref.ref(sentinel)

    result = await schema.execute("{ spawn }", context_value=sentinel)
    assert result.errors is None, result.errors

    del sentinel, result
    release.set()
    await seen["task"]

    assert seen["bound_during"] is True
    assert seen["state"] is None
    assert seen["context"] is None
    gc.collect()
    assert reference() is None


@pytest.mark.asyncio
async def test_a_surviving_task_that_starts_its_own_operation_ends_with_nothing_bound():
    """The copied binding is not an outer scope for the task's own operation.

    Restoring a token in that task must return it to no state rather than to the
    first request's - a stale binding would otherwise reappear the moment the
    task's own operation finished. The nesting answer is the same statement
    about the same copy: the task inherited a scope that has since ended, so its
    own operation is top-level, publishes its own optimizer state, and leaves
    the task inside nothing when it finishes.
    """
    shared = _SilentProbe()
    seen: dict = {}
    release = asyncio.Event()

    @strawberry.type
    class SpawningQuery:
        @strawberry.field
        async def spawn(self, info: strawberry.Info) -> str:
            async def child():
                await release.wait()
                seen["before"] = operation_is_nested()
                inner = await info.schema.execute("{ spawnHello }")
                seen["inner"] = inner
                seen["after"] = shared.execution_context
                seen["nested_after"] = operation_is_nested()

            seen["task"] = asyncio.ensure_future(child())
            return "spawned"

        @strawberry.field
        def spawn_hello(self, info: strawberry.Info) -> str:
            seen["nested_rows"] = [*seen.get("nested_rows", []), operation_is_nested()]
            return "hi"

    schema = DjangoSchema(query=SpawningQuery, extensions=[lambda: shared])
    result = await schema.execute("{ spawn }")
    assert result.errors is None, result.errors

    release.set()
    await seen["task"]

    assert seen["inner"].data == {"spawnHello": "hi"}
    assert seen["after"] is None
    assert seen["before"] is False
    assert seen["nested_rows"] == [False]
    assert seen["nested_after"] is False


@pytest.mark.asyncio
async def test_a_child_released_during_result_collection_reads_a_closed_binding():
    """The runner still owns the state; the copy taken inside the operation does not.

    Upstream collects an async operation's extension results after the operation
    scope has unwound, and the runner rebinds for that - so "the runner still
    holds every state" and "this context is inside the operation" are two
    different questions here. A weak reference alone answers the first and gets
    the second wrong, because the state it points at is deliberately alive for
    the collection. The lease closed at the end of the operation scope is what
    answers the second.
    """
    shared = _SilentProbe()
    seen: dict = {}
    release = asyncio.Event()

    class _Collecting(SchemaExtension):
        """Pauses result collection long enough for the resolver's child to run."""

        async def get_results(self) -> dict:
            """Release the child, wait for it, and record what the runner still owns."""
            if "during" in seen:
                return {}
            release.set()
            await seen["task"]
            seen["during"] = shared._operation_state()
            return {}

    @strawberry.type
    class SpawningQuery:
        @strawberry.field
        async def spawn(self, info: strawberry.Info) -> str:
            async def child():
                await release.wait()
                seen["child_state"] = shared._operation_state()
                seen["child_nested"] = operation_is_nested()

            seen["task"] = asyncio.ensure_future(child())
            return "spawned"

    schema = DjangoSchema(query=SpawningQuery, extensions=[_Collecting, lambda: shared])
    result = await schema.execute("{ spawn }")

    assert result.errors is None, result.errors
    assert seen["during"] is not None
    assert seen["child_state"] is None
    assert seen["child_nested"] is False


@pytest.mark.asyncio
async def test_a_task_outliving_a_cancelled_stream_reads_nothing_either():
    """A dropped subscription cancels the task driving it, and its children remain.

    A streamed operation is bound around each frame, in the task that pulls it
    (``django_strawberry_framework/extensions/operation_state.py::_ResumedStream``),
    and that binding's lease closes when the frame is yielded. A task the
    resolver started while the frame was produced holds a copy of that binding
    and is neither the task being cancelled nor the one closing the stream:
    what it reads afterwards is nothing, and the request it was started for is
    released once the stream is closed.
    """
    shared = _SilentProbe()
    seen: dict = {}
    release = asyncio.Event()
    started = asyncio.Event()
    schema = _spawning_schema(shared, seen, release)
    request = {"context": _RequestContext()}
    reference = weakref.ref(request["context"])

    async def _drive():
        request["stream"] = await schema.stream(
            "{ spawn }",
            context_value=request["context"],
        )
        async for _frame in request["stream"]:
            started.set()
            await asyncio.sleep(3600)

    task = asyncio.create_task(_drive())
    await asyncio.wait_for(started.wait(), timeout=5)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    # Cancelling the consumer leaves the generator suspended and still holding
    # the request; that task going away is what lets the request be released at
    # all. The child's reads below are settled already - the frame's lease
    # closed when it was yielded - but the request is freed only when the
    # generator finishes, which is what closing it does
    # (``django_strawberry_framework/consumers.py::_stop_aware_results`` closes
    # the source at revocation); left to the asyncgen finalizer, ``reference()``
    # would answer on the interpreter's timing.
    await request.pop("stream").aclose()
    request.clear()
    del task
    release.set()
    await seen["task"]

    assert seen["bound_during"] is True
    assert seen["state"] is None
    assert seen["context"] is None
    gc.collect()
    assert reference() is None


@pytest.mark.asyncio
async def test_result_collection_is_inside_the_operation_it_collects_for():
    """The latest scope a runner owns, and an operation started there is still inside.

    Upstream collects an async operation's extension results after the operation
    scope has unwound, so this is the one place where "the outer operation's
    hooks have all returned" and "the outer operation is over" come apart.
    """
    seen: dict = {"nested_rows": [], "ran": False}

    class _Collecting(SchemaExtension):
        """A consumer extension that runs its own operation while results are collected."""

        async def get_results(self) -> dict:
            """Run one inner operation from the outer operation's collection scope."""
            if seen["ran"]:
                return {}
            seen["ran"] = True
            await self.execution_context.schema.execute("{ hello }")
            return {}

    class _Inner(SchemaExtension):
        """Records the nesting answer of whichever operation it runs in."""

        def on_operation(self):
            """Record what the operation about to run answers, once per operation."""
            seen["nested_rows"].append(operation_is_nested())
            yield

    schema = DjangoSchema(query=_Query, extensions=[_Collecting, _Inner])
    result = await schema.execute("{ hello }")

    assert result.errors is None, result.errors
    assert seen["nested_rows"] == [False, True]


def test_a_nested_runner_knows_it_is_inside_another_operation():
    """ "Nested" is a fact about runners, not about which hook is running.

    The optimizer reads this to decide whether the request's context object is
    its own to clear and publish to
    (``optimizer/_context.py::begin_execution_frame``). An operation started
    from a consumer extension's teardown begins after every optimizer hook of
    the outer operation has already returned, and is still inside it.
    """
    seen: dict = {"nested_rows": [], "ran": False}

    class _Teardown(SchemaExtension):
        """A consumer extension that runs its own operation at teardown."""

        def on_operation(self):
            """Run one inner operation once the outer operation's hooks are done."""
            yield
            if seen["ran"]:
                return
            seen["ran"] = True
            self.execution_context.schema.execute_sync("{ hello }")

    class _Inner(SchemaExtension):
        """Records the nesting answer of whichever operation it runs in."""

        def on_operation(self):
            """Record what the operation about to run answers, once per operation."""
            seen["nested_rows"].append(operation_is_nested())
            yield

    schema = DjangoSchema(query=_Query, extensions=[_Teardown, _Inner])
    assert schema.execute_sync("{ hello }").errors is None

    assert seen["nested_rows"] == [False, True]
    assert operation_is_nested() is False


# ---------------------------------------------------------------------------
# A streamed operation belongs to whichever task drives it.
# ---------------------------------------------------------------------------


#: The documented optimizer spelling: one instance behind a factory, so its plan
#: cache is shared across operations while its state is not.
_STREAM_OPTIMIZER = DjangoOptimizerExtension()


def _ticking_schema(seen, frames=3, extensions=()):
    """A subscription whose resolver records what each frame is bound to."""

    @strawberry.type
    class TickingSubscription:
        @strawberry.subscription
        async def ticks(self) -> AsyncGenerator[str, None]:
            """Record one row per frame, then yield it."""
            try:
                for index in range(frames):
                    seen["rows"].append(
                        (
                            operation_is_nested(),
                            armed_resource_policy() is not None,
                            optimizer_value(None, "probe") is None,
                        ),
                    )
                    seen.setdefault("copied", contextvars.copy_context())
                    yield f"tick-{index}"
            finally:
                seen["closed"] = True

    return DjangoSchema(
        query=_Query,
        subscription=TickingSubscription,
        extensions=list(extensions),
    )


def _read_in_the_copied_context(seen) -> dict:
    """What a context copied while a frame was produced answers afterwards."""
    read: dict = {}

    def _read() -> None:
        read["armed"] = armed_resource_policy()
        read["nested_scope"] = _RUNNER_SCOPES.get()
        read["optimizer"] = active_optimizer()

    seen["copied"].run(_read)
    return read


async def _frame_in_its_own_task(stream):
    """Pull one frame from ``stream`` in a task of its own."""
    return await asyncio.ensure_future(stream.__anext__())


@pytest.mark.asyncio
async def test_a_stream_frame_produced_in_another_task_is_bound_to_its_operation():
    """Python resumes an async generator in the CALLER's context, not the producer's.

    A transport advances the iterator from whatever task holds it, so every
    binding made while the first frame was produced is absent for the second -
    and the operation's own resolvers would then run with no armed budget and no
    runner scope, enforcing the fallback rather than the policy the request was
    admitted under. The runner rebinds around each resumption, so a frame
    produced in a second task is the same operation as the frame before it.
    """
    seen: dict = {"rows": []}
    schema = _ticking_schema(seen, extensions=[lambda: _STREAM_OPTIMIZER])
    stream = await schema.subscribe("subscription { ticks }")

    first = await _frame_in_its_own_task(stream)
    second = await _frame_in_its_own_task(stream)

    assert first.data == {"ticks": "tick-0"}
    assert second.data == {"ticks": "tick-1"}
    assert seen["rows"] == [(False, True, True), (False, True, True)]
    await stream.aclose()


@pytest.mark.asyncio
async def test_a_stream_resumed_with_asend_from_another_task_is_bound_the_same_way():
    """``asend`` is the other way to advance an iterator, and transports use it.

    A started async generator is resumed by ``asend`` exactly as by ``__anext__``
    - upstream's stream discards the value, because its frames come from the
    operation rather than from the caller - so a wrapper that bound one and not
    the other would leave whichever seam a transport happens to drive running
    outside its own operation. The row after this one is the control: the frame
    is the next one either way, and both are bound.
    """
    seen: dict = {"rows": []}
    schema = _ticking_schema(seen, extensions=[lambda: _STREAM_OPTIMIZER])
    stream = await schema.subscribe("subscription { ticks }")

    first = await _frame_in_its_own_task(stream)
    second = await asyncio.ensure_future(stream.asend("discarded"))

    assert first.data == {"ticks": "tick-0"}
    assert second.data == {"ticks": "tick-1"}
    assert seen["rows"] == [(False, True, True), (False, True, True)]
    await stream.aclose()


@pytest.mark.asyncio
async def test_a_stream_closed_from_another_task_leaves_every_scope_terminal():
    """The close is the operation's teardown, and it runs wherever the closer is.

    A cancelled subscription is closed by the connection rather than by the task
    that produced its last frame, and a token belongs to the context that
    created it. Closing has to end the operation regardless: the budget
    disarmed, nothing bound, the resolver's own ``finally`` run, and the request
    released.
    """
    seen: dict = {"rows": []}
    shared = _SilentProbe()
    schema = _ticking_schema(seen, extensions=[lambda: shared, lambda: _STREAM_OPTIMIZER])
    context = _RequestContext()
    reference = weakref.ref(context)
    stream = await schema.subscribe("subscription { ticks }", context_value=context)

    await _frame_in_its_own_task(stream)
    await asyncio.ensure_future(stream.aclose())

    read = _read_in_the_copied_context(seen)

    assert seen["closed"] is True
    assert read["armed"] is None
    assert read["nested_scope"].held() is None
    assert read["optimizer"] is None
    assert shared.execution_context is None
    del stream, context, read
    seen.clear()
    gc.collect()
    assert reference() is None


@pytest.mark.asyncio
async def test_a_stream_cancelled_in_one_task_is_closable_from_another():
    """Cancellation leaves the generator suspended; the close still has to work.

    The frame the cancelled task was waiting for never arrives, so the operation
    is still open when the connection drops it - which is the ordinary shape of
    a client disconnect. Closing from the connection's own task is what runs the
    teardown, and it must not raise a token error on the way.
    """
    seen: dict = {"rows": []}
    schema = _ticking_schema(seen)
    stream = await schema.subscribe("subscription { ticks }")

    await _frame_in_its_own_task(stream)
    pending = asyncio.ensure_future(stream.__anext__())
    await asyncio.sleep(0)
    pending.cancel()
    with pytest.raises(asyncio.CancelledError):
        await pending

    await asyncio.ensure_future(stream.aclose())

    assert seen["closed"] is True
    assert _read_in_the_copied_context(seen)["armed"] is None


@pytest.mark.asyncio
async def test_a_stream_thrown_into_from_another_task_tears_down_its_own_operation():
    """``athrow`` is the other way a transport ends a stream, and it binds the same.

    Upstream renders the thrown exception as the stream's last frame rather than
    re-raising it - the shape a transport turns into an error entry - which
    means the operation is still open when that frame is produced, and the close
    that follows is what ends it. Both halves run in the throwing task here, and
    both have to be the operation's own: the resolver's ``finally``, and the
    teardown that disarms what the operation armed.
    """
    seen: dict = {"rows": []}
    schema = _ticking_schema(seen)
    stream = await schema.subscribe("subscription { ticks }")
    await _frame_in_its_own_task(stream)

    async def _throw_and_close():
        final = await stream.athrow(RuntimeError("dropped"))
        await stream.aclose()
        return final

    final = await asyncio.ensure_future(_throw_and_close())
    read = _read_in_the_copied_context(seen)

    assert [error.message for error in final.errors] == ["dropped"]
    assert seen["closed"] is True
    assert read["armed"] is None
    assert read["nested_scope"].held() is None


# ---------------------------------------------------------------------------
# A package-managed extension takes its state from the runner and nothing else.
# ---------------------------------------------------------------------------


class _Forged:
    """An object graph a resolver would like the process to keep."""


class _RawSchemaShaped:
    """A value shaped like a context belonging to some other schema."""

    def __init__(self) -> None:
        self.schema = object()


class _RefusingToSaySchema:
    """A value whose ``.schema`` raises, which the setter must not depend on."""

    @property
    def schema(self):
        """Refuse to say which schema this context belongs to."""
        raise RuntimeError("no schema here")


@pytest.mark.parametrize(
    "forge",
    [
        _Forged,
        _RawSchemaShaped,
        _RefusingToSaySchema,
        lambda: None,
    ],
    ids=[
        "arbitrary-object",
        "raw-schema-shaped",
        "raising-schema",
        "none",
    ],
)
def test_a_resolver_assigning_to_a_managed_extension_leaves_nothing_behind(forge):
    """The engine's assignment is the package's signal, not the consumer's channel.

    A shared extension is reachable from every resolver the schema serves, and
    the setter is an ordinary attribute write. Every shape here is one no engine
    produces: an arbitrary graph, a context belonging to some other schema, a
    value that refuses to say, and the clearing assignment. An extension the
    runner has managed takes none of them, so a direct read outside the
    operation answers ``None`` and the object the resolver made is released with
    the request.
    """
    shared = _SilentProbe()
    forged: dict = {}

    @strawberry.type
    class TamperingQuery:
        @strawberry.field
        def tamper(self) -> str:
            """Assign one forged value to the shared extension."""
            value = forge()
            forged["value"] = value
            shared.execution_context = value
            return "tampered"

    schema = DjangoSchema(query=TamperingQuery, extensions=[lambda: shared])
    result = schema.execute_sync("{ tamper }")

    assert result.errors is None, result.errors
    assert shared.execution_context is None
    assert shared._operation_state() is None
    value = forged.pop("value")
    reference = None if value is None else weakref.ref(value)
    del value, result
    gc.collect()
    assert reference is None or reference() is None


@pytest.mark.asyncio
async def test_a_surviving_task_cannot_give_a_managed_extension_state_either():
    """The assignment a background task makes is the same assignment, later.

    Nothing about the tamper needs the request to still be running: a task that
    outlived it holds the shared extension just as a resolver does, and the read
    it would poison is every direct read the process makes afterwards.
    """
    shared = _SilentProbe()
    seen: dict = {}
    release = asyncio.Event()

    @strawberry.type
    class SpawningQuery:
        @strawberry.field
        async def spawn(self) -> str:
            """Start a task that assigns to the shared extension after the request."""

            async def child():
                await release.wait()
                forged = _Forged()
                seen["reference"] = weakref.ref(forged)
                shared.execution_context = forged

            seen["task"] = asyncio.ensure_future(child())
            return "spawned"

    schema = DjangoSchema(query=SpawningQuery, extensions=[lambda: shared])
    assert (await schema.execute("{ spawn }")).errors is None

    release.set()
    await seen["task"]

    assert shared.execution_context is None
    gc.collect()
    assert seen["reference"]() is None


def test_an_extension_a_raw_schema_used_first_is_managed_once_a_django_schema_runs_it():
    """The mark is one-way, because the question it answers is.

    A raw ``strawberry.Schema`` has no runner, so the setter is the only signal
    it can give and the state lands on the instance. Once a ``DjangoSchema``
    operation has run the same instance, the runner is the authority and the
    earlier arrangement is dropped: a read outside an operation answers for no
    operation rather than for whatever the raw schema last assigned.
    """
    shared = _SilentProbe()
    raw = strawberry.Schema(query=_Query, extensions=[lambda: shared])

    assert raw.execute_sync("{ hello }").errors is None
    raw_context = shared.execution_context
    assert raw_context is not None

    managed = DjangoSchema(query=_Query, extensions=[lambda: shared])
    assert managed.execute_sync("{ hello }").errors is None
    assert shared.execution_context is None

    assert raw.execute_sync("{ hello }").errors is None
    assert shared.execution_context is None
