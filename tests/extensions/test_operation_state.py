"""The operation-state boundary: what one operation reads, writes, and leaves behind.

``extensions/operation_state.py`` is the package's answer to an engine that
resolves an extension entry into the SAME object for every operation. What it
has to be true of is narrow and hard to see from a response, so the rows here
drive the seams directly:

- the engine's assignment is a handoff, claimed while the runner is built and
  gone before the runner is returned;
- one operation's state is bound for the operation, for result collection and
  for every streaming frame, and reset afterwards;
- a failure between the runner's construction and ``operation()`` leaves nothing
  bound and nothing retained;
- the binding carrier is settled once per extension and a second constructor
  call is refused.

The disclosure these prevent is asserted where a client can see it -
``examples/fakeshop/test_query/test_resource_policy_api.py`` and
``test_error_policy_api.py`` carry the shared-entry matrices over both view
colors. This module holds what no request can express.
"""

from __future__ import annotations

import asyncio
import gc
import weakref
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
    _PENDING_ASSIGNMENTS,
    OperationState,
    _OperationBoundExtension,
)
from django_strawberry_framework.optimizer import DjangoOptimizerExtension


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


def test_the_engines_assignment_is_readable_before_a_runner_claims_it():
    """Between the assignment and the binding, the handoff is what answers.

    Upstream assigns on every resolved member and only then builds the runner.
    Anything reading in that window is reading about the operation being set up,
    and there is no state yet - so the pending handoff answers, and nothing has
    been written that a later operation could inherit.
    """
    extension = _Probe()
    context = SimpleNamespace(schema=DjangoSchema(query=_Query))

    extension.execution_context = context

    assert extension.execution_context is context
    assert extension._operation_state() is None


def test_a_claimed_handoff_is_gone_before_the_runner_factory_returns():
    """The claim happens while the runner is built, not when the operation ends.

    Upstream constructs the middleware manager and the execution machinery
    between the runner factory and ``operation()``; a failure there runs no
    operation teardown. So the handoff has to be consumed by the factory, and
    what is left afterwards is nothing at all.
    """
    schema = DjangoSchema(query=_Query, extensions=[_Probe])
    context = SimpleNamespace(schema=schema)
    extensions = schema.get_extensions(sync=True)
    for extension in extensions:
        extension.execution_context = context

    assert len(_PENDING_ASSIGNMENTS.get()) == 3  # both policies and the probe

    schema.create_extensions_runner(context, extensions)

    assert _PENDING_ASSIGNMENTS.get() == ()
    probe = next(entry for entry in extensions if isinstance(entry, _Probe))
    assert probe.execution_context is None
    assert probe._operation_state() is None


def test_an_assignment_for_another_context_is_left_for_the_runner_it_belongs_to():
    """A handoff names one context, and a later runner does not consume it.

    Two schemas can assign to one shared extension before either runner is
    built. Claiming by identity alone would let the second runner eat the
    first's handoff and leave that operation reading nothing.
    """
    extension = _Probe()
    first = SimpleNamespace(schema=DjangoSchema(query=_Query))
    second = SimpleNamespace(schema=DjangoSchema(query=_Query))
    extension.execution_context = first
    extension.execution_context = second

    DjangoSchema(query=_Query).create_extensions_runner(second, [extension])

    remaining = _PENDING_ASSIGNMENTS.get()
    assert [entry.execution_context for entry in remaining] == [first]
    _PENDING_ASSIGNMENTS.set(())


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
    assert _PENDING_ASSIGNMENTS.get() == ()

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

    assert _PENDING_ASSIGNMENTS.get() == ()
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

    assert _PENDING_ASSIGNMENTS.get() == ()
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
