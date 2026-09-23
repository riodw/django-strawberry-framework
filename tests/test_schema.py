"""Permanent behavioral tests for django_strawberry_framework.schema.

Construction, hostile extension matching, mutation-lock identity, rollback
windows, and the enforcement-seal / WeakKeyDictionary / GC rows a request
cannot express. ``Schema.stream`` stays here: fakeshop has no ASGI/WS mount.
Consumer-visible policy enforcement and masking live in
``examples/fakeshop/test_query/test_resource_policy_api.py`` and
``examples/fakeshop/test_query/test_error_policy_api.py``.
"""

from __future__ import annotations

import asyncio
import gc
import weakref
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
import strawberry
from apps.library.models import Branch
from django.db import connection
from graphql import ExecutionContext, GraphQLError, print_ast
from strawberry.extensions.base_extension import SchemaExtension
from strawberry.extensions.runner import SchemaExtensionsRunner
from strawberry.schema.exceptions import InvalidOperationTypeError
from strawberry.types import ExecutionContext as StrawberryExecutionContext
from strawberry.types.graphql import OperationType

from django_strawberry_framework.error_policy import ErrorPolicy
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.extensions.error_policy import DjangoErrorPolicyExtension
from django_strawberry_framework.extensions.operation_state import _ResumedStream
from django_strawberry_framework.extensions.resource_policy import DjangoResourcePolicyExtension
from django_strawberry_framework.optimizer import DjangoOptimizerExtension
from django_strawberry_framework.resource_policy import ResourcePolicy, bounded_rows
from django_strawberry_framework.schema import (
    _SCHEMA_ENFORCEMENT,
    _SCHEMA_EXTENSIONS,
    SCHEMA_CONFIGURATION_ERROR_CODE,
    DjangoMutationExecutionContext,
    DjangoSchema,
    _async_mutation_lock,
    _AsyncAliasLock,
    _consumer_extension_entries,
    _entry_type,
    _extension_entry_matches,
    _is_extension,
    _refuse_operation_document,
)
from django_strawberry_framework.utils.querysets import run_in_one_sync_boundary

#: ``Schema.stream`` landed in strawberry-graphql 0.319.0. Below it the package
#: has no streamed seam to answer for - ``consumers.py::_StopAwareSchema.stream``
#: delegates to a name that install does not carry and no handler reads - so the
#: rows about it are skipped rather than rewritten onto ``subscribe``, which
#: there serves subscriptions alone and would prove a different contract.
_SKIP_WITHOUT_STREAM = pytest.mark.skipif(
    not hasattr(strawberry.Schema, "stream"),
    reason="Schema.stream landed in strawberry-graphql 0.319.0",
)


class CustomErrorPolicyExtension(DjangoErrorPolicyExtension):
    """A consumer subclass of the masking authority, which is not one."""


class CustomResourcePolicyExtension(DjangoResourcePolicyExtension):
    """A consumer subclass of the bounding authority, which is not one."""


class HybridPolicyExtension(DjangoResourcePolicyExtension, DjangoErrorPolicyExtension):
    """One class answering to both authorities, of which it can dispatch one."""


class ReversedHybridPolicyExtension(DjangoErrorPolicyExtension, DjangoResourcePolicyExtension):
    """The same class with its bases the other way round, which picks the other hook."""


class _ClassClaimingResourcePolicy(DjangoResourcePolicyExtension):
    """An authority subclass whose instances claim to be a class, which ``isinstance`` believes."""

    @property
    def __class__(self):
        """Claim ``type``, so an ``isinstance`` classifier sees a class entry."""
        return type


class _ClassClaimingErrorPolicy(DjangoErrorPolicyExtension):
    """The masking-authority subclass making the same claim."""

    @property
    def __class__(self):
        """Claim ``type``, so an ``isinstance`` classifier sees a class entry."""
        return type


#: Every marker extension that ran, in order, since a test last cleared it.
_MARKS: list[str] = []


class _MarkerExtension(SchemaExtension):
    """A consumer extension that records itself when its operation begins.

    What the membership rows ask is which extensions RUN the next operation, and
    a consumer extension is the honest subject for that question now that
    neither enforcement authority is an entry. The mark is the observation.
    """

    mark = "accepted"

    def on_operation(self):
        """Record that this entry ran the operation."""
        _MARKS.append(self.mark)
        yield


class _ForgedMarkerExtension(_MarkerExtension):
    """The entry a resolver would rather the schema resolved."""

    mark = "forged"


@pytest.fixture(autouse=True)
def _clear_marks():
    """Start every test with no marks recorded."""
    _MARKS.clear()
    yield
    _MARKS.clear()


@strawberry.type
class DummyQuery:
    @strawberry.field
    def hello(self) -> str:
        return "world"


@strawberry.type
class _RowQuery:
    @strawberry.field
    def rows(self, info: strawberry.Info) -> list[str]:
        return list(bounded_rows(["a", "b", "c"], info, None))


@strawberry.type
class DummyMutation:
    @strawberry.mutation
    def plain_mutation(self) -> str:
        return "plain"


def test_schema_init_with_none_and_iterable_extensions():
    schema_none = DjangoSchema(query=DummyQuery, extensions=None)
    assert schema_none.extensions == ()

    schema_tuple = DjangoSchema(query=DummyQuery, extensions=(_MarkerExtension,))
    assert schema_tuple.extensions == (_MarkerExtension,)

    def ext_gen():
        yield _MarkerExtension

    schema_gen = DjangoSchema(query=DummyQuery, extensions=ext_gen())
    assert schema_gen.extensions == (_MarkerExtension,)


def test_schema_init_with_none_execution_context_class_falls_back():
    schema = DjangoSchema(query=DummyQuery, execution_context_class=None)
    assert schema.execution_context_class is DjangoMutationExecutionContext


def test_consumer_extension_entries_shapes():
    """What travels as configuration, and what is read once and folded into the record."""
    assert _consumer_extension_entries(None) == ([], None)
    assert _consumer_extension_entries([]) == ([], None)
    assert _consumer_extension_entries([_MarkerExtension]) == ([_MarkerExtension], None)
    assert _consumer_extension_entries([DjangoResourcePolicyExtension]) == ([], None)
    assert _consumer_extension_entries([DjangoErrorPolicyExtension]) == ([], None)
    assert _consumer_extension_entries([DjangoErrorPolicyExtension()]) == ([], None)

    entries, declared = _consumer_extension_entries(
        [_MarkerExtension, DjangoResourcePolicyExtension(policy=ResourcePolicy(max_list_rows=4))],
    )
    assert entries == [_MarkerExtension]
    assert declared == ResourcePolicy(max_list_rows=4)


def test_an_entry_is_classified_by_its_real_type_whatever_its_class_property_says():
    """A consumer object decides what ``isinstance`` sees, and ``type()`` ignores it.

    A ``__class__`` that raises, and one that claims to be a class, both come
    back as the instance's real type.
    """

    class _HostileClass:
        @property
        def __class__(self):
            raise TypeError("hostile __class__")

    assert _entry_type(_HostileClass()) is _HostileClass
    assert _entry_type(_ClassClaimingResourcePolicy()) is _ClassClaimingResourcePolicy
    assert _entry_type(DjangoResourcePolicyExtension) is DjangoResourcePolicyExtension


def test_extension_entry_matches_adversarial():
    assert _extension_entry_matches(DjangoErrorPolicyExtension(), DjangoErrorPolicyExtension)
    assert not _extension_entry_matches(
        DjangoResourcePolicyExtension(),
        DjangoErrorPolicyExtension,
    )
    assert not _extension_entry_matches(object(), DjangoErrorPolicyExtension)
    assert not _extension_entry_matches(123, DjangoErrorPolicyExtension)
    assert not _extension_entry_matches("string", DjangoErrorPolicyExtension)
    assert not _extension_entry_matches(None, DjangoErrorPolicyExtension)


@pytest.mark.parametrize(
    "entry",
    [
        CustomErrorPolicyExtension,
        CustomResourcePolicyExtension,
        CustomResourcePolicyExtension(),
        HybridPolicyExtension,
        ReversedHybridPolicyExtension,
        HybridPolicyExtension(),
        _ClassClaimingResourcePolicy(),
        _ClassClaimingErrorPolicy(),
    ],
    ids=[
        "error-subclass-class",
        "resource-subclass-class",
        "resource-subclass-instance",
        "hybrid-class",
        "hybrid-class-reversed-bases",
        "hybrid-instance",
        "resource-subclass-instance-claiming-a-class",
        "error-subclass-instance-claiming-a-class",
    ],
)
def test_a_subclass_of_an_enforcement_extension_is_refused_at_construction(entry):
    """Inheriting an authority is not being one, and the census cannot tell them apart.

    A subclass overriding the single hook that charges a document or masks a
    result answers every ``issubclass`` question correctly while enforcing
    nothing, and one class inheriting BOTH answers for two authorities of which
    ordinary method resolution runs exactly one. Neither is distinguishable from
    the real thing by anything but exact type, so neither is admitted as one.
    """
    with pytest.raises(ConfigurationError, match="subclasses the package"):
        DjangoSchema(query=DummyQuery, extensions=[entry])


def test_marked_mutation_class_safe_on_none_parent_and_malformed_nodes():
    schema = DjangoSchema(query=DummyQuery)
    graphql_schema = schema._schema

    ctx = DjangoMutationExecutionContext.__new__(DjangoMutationExecutionContext)
    ctx.schema = graphql_schema

    # parent_type is None when schema.mutation_type is None (query-only schema)
    assert ctx._marked_mutation_class(None, []) is None
    assert ctx._marked_mutation_class(None, None) is None

    # Schema with mutation
    schema_with_mut = DjangoSchema(query=DummyQuery, mutation=DummyMutation)
    ctx_mut = DjangoMutationExecutionContext.__new__(DjangoMutationExecutionContext)
    ctx_mut.schema = schema_with_mut._schema
    mut_type = schema_with_mut._schema.mutation_type

    # parent_type is None when schema.mutation_type is present
    assert ctx_mut._marked_mutation_class(None, []) is None

    # field_nodes is empty / None / malformed
    assert ctx_mut._marked_mutation_class(mut_type, []) is None
    assert ctx_mut._marked_mutation_class(mut_type, None) is None
    assert ctx_mut._marked_mutation_class(mut_type, [object()]) is None

    # Introspection field (__typename)
    class FakeNode:
        name = type("Name", (), {"value": "__typename"})()

    assert ctx_mut._marked_mutation_class(mut_type, [FakeNode()]) is None

    # Plain strawberry mutation (unmarked)
    class PlainMutNode:
        name = type("Name", (), {"value": "plainMutation"})()

    assert ctx_mut._marked_mutation_class(mut_type, [PlainMutNode()]) is None

    # Missing field from parent_type.fields
    class MissingNode:
        name = type("Name", (), {"value": "doesNotExist"})()

    assert ctx_mut._marked_mutation_class(mut_type, [MissingNode()]) is None

    # parent_type with non-dict fields
    class NonDictFieldsParent:
        fields = ["not", "a", "dict"]

    ctx_non_dict = DjangoMutationExecutionContext.__new__(DjangoMutationExecutionContext)
    ctx_non_dict.schema = SimpleNamespace(mutation_type=NonDictFieldsParent)
    named_node = SimpleNamespace(name=SimpleNamespace(value="some_mutation"))
    assert ctx_non_dict._marked_mutation_class(NonDictFieldsParent, [named_node]) is None


def test_execution_errors_fallback():
    ctx = DjangoMutationExecutionContext.__new__(DjangoMutationExecutionContext)
    assert ctx._execution_errors() == []

    ctx.collected_errors = object()
    assert ctx._execution_errors() == []


def test_schema_policy_resolution_and_validation():
    s1 = DjangoSchema(
        query=DummyQuery,
        resource_policy={"max_depth": 10},
        error_policy={"enabled": False},
    )
    assert s1.resource_policy.max_depth == 10
    assert s1.error_policy.enabled is False

    rp = ResourcePolicy(max_depth=12)
    ep = ErrorPolicy(enabled=True, message="Custom error")
    s2 = DjangoSchema(query=DummyQuery, resource_policy=rp, error_policy=ep)
    assert s2.resource_policy.max_depth == 12
    assert s2.error_policy.message == "Custom error"

    with pytest.raises(ConfigurationError):
        DjangoSchema(query=DummyQuery, resource_policy={"max_depth": -5})

    with pytest.raises(ConfigurationError):
        DjangoSchema(query=DummyQuery, error_policy={"enabled": "invalid"})


def test_async_mutation_lock_caching_per_alias():
    lock_default_1 = _async_mutation_lock("default")
    lock_default_2 = _async_mutation_lock("default")
    lock_other = _async_mutation_lock("other_alias")

    assert lock_default_1 is lock_default_2
    assert lock_default_1 is not lock_other


@pytest.mark.asyncio
async def test_async_alias_lock_context_manager():
    lock = _AsyncAliasLock()
    async with lock:
        assert lock._lock.locked()
    assert not lock._lock.locked()


@pytest.mark.django_db
def test_execute_mutation_field_sync_exception_rolls_back():
    class DummyMutationCls:
        _mutation_meta = MagicMock(model=None)

    ctx = DjangoMutationExecutionContext.__new__(DjangoMutationExecutionContext)
    ctx.schema = MagicMock()
    ctx.errors = []

    with (
        patch.object(ctx, "_marked_mutation_class", return_value=DummyMutationCls),
        patch.object(
            ExecutionContext,
            "execute_field",
            side_effect=RuntimeError("sync field crash"),
        ),
        pytest.raises(RuntimeError, match="sync field crash"),
    ):
        ctx.execute_field(ctx.schema.mutation_type, None, [MagicMock()], None)


class FlipFlopErrorList:
    """Friendly on the first ``len`` (the window opens), hostile on the second
    (the rollback decision) - the shape that reaches past ``errors_before``."""

    def __init__(self) -> None:
        self.calls = 0

    def __len__(self) -> int:
        self.calls += 1
        if self.calls == 1:
            return 0
        raise RuntimeError("hostile len on rollback read")


class _ModelLessMutationMeta:
    model = None


#: The row the patched resolver writes inside the open window. Both rows below
#: assert its ABSENCE afterwards, which is the half a closed-transaction
#: assertion cannot see: an atomic that exits WITHOUT the rollback mark exits
#: cleanly and commits, so ``connection.in_atomic_block`` is false either way and
#: the row is the only witness that says which of the two happened.
_ROLLBACK_PROBE_NAME = "hostile-error-container-rollback-probe"


def _write_the_rollback_probe_row(*args, **kwargs):
    """Write inside the window, then return cleanly - a resolver that already wrote."""
    del args, kwargs
    Branch.objects.create(name=_ROLLBACK_PROBE_NAME)
    return "ok"


def _rollback_probe_row_exists() -> bool:
    """True when the window committed the probe row instead of rolling it back."""
    return Branch.objects.filter(name=_ROLLBACK_PROBE_NAME).exists()


@pytest.mark.django_db(transaction=True)
def test_sync_window_hostile_error_container_rolls_back_and_leaks_no_transaction():
    """A hostile error container rolls the window back; it cannot abandon it either.

    ``_rollback_for_new_errors`` runs between the atomic enter and exit, so a
    container that reads fine at open and raises at the close-time read must
    fail closed - rollback marked, atomic exited, failure surfaced - and never
    leave an open transaction on the connection
    (schema.py::DjangoMutationExecutionContext._rollback_for_new_errors).

    The row assertion is what pins the ROLLBACK half. Deleting the
    ``transaction.set_rollback(True, using=alias)`` call in that method's
    ``except Exception`` arm - the one guarding the ``len`` read - leaves the
    exception propagating and the ``finally`` in
    ``schema.py::DjangoMutationExecutionContext._execute_mutation_field_sync``
    still exiting the atomic, so the transaction closes and
    ``connection.in_atomic_block`` is false exactly as it is now, but the exit
    COMMITS: the probe row written inside the window survives a window the
    package could not certify. Only the absence assertion below fails there.
    """
    ctx = DjangoMutationExecutionContext.__new__(DjangoMutationExecutionContext)
    ctx.schema = MagicMock()
    ctx.collected_errors = SimpleNamespace(errors=FlipFlopErrorList())

    with (
        patch.object(ctx, "_marked_mutation_class", return_value=_ModelLessMutationMeta),
        patch.object(ExecutionContext, "execute_field", side_effect=_write_the_rollback_probe_row),
        pytest.raises(RuntimeError, match="hostile len"),
    ):
        ctx.execute_field(ctx.schema.mutation_type, None, [MagicMock()], None)

    assert not connection.in_atomic_block
    assert not _rollback_probe_row_exists()


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_async_window_hostile_error_container_rolls_back_and_leaks_no_transaction():
    """The async window's clean exit obeys the same containment, rollback included.

    The rollback decision raising must not skip the atomic exit, which would
    release the alias lock over an abandoned open transaction - and the write
    the window was holding must not survive it either. Deleting the
    ``transaction.set_rollback(True, using=alias)`` call in the ``except
    Exception`` arm of
    ``schema.py::DjangoMutationExecutionContext._rollback_for_new_errors``
    commits the probe row here through ``_exit_clean``'s ``finally``, with the
    transaction still closed and the alias lock still released; the absence
    assertion is the only one that notices.

    Everything that touches the ORM runs through
    ``run_in_one_sync_boundary``'s ``thread_sensitive=True`` worker - the same
    worker the window's ``atomic.__enter__`` / ``__exit__`` run in, and
    therefore the same Django connection the transaction is open on. Writing or
    reading from the event-loop thread would be a different connection (and
    Django's own async-unsafe refusal).
    """
    ctx = DjangoMutationExecutionContext.__new__(DjangoMutationExecutionContext)
    ctx.schema = MagicMock()
    ctx.collected_errors = SimpleNamespace(errors=FlipFlopErrorList())

    def _write_in_the_window_worker(*args, **kwargs):
        return run_in_one_sync_boundary(_write_the_rollback_probe_row, *args, **kwargs)

    with (
        patch.object(ctx, "_marked_mutation_class", return_value=_ModelLessMutationMeta),
        patch.object(ExecutionContext, "execute_field", side_effect=_write_in_the_window_worker),
        pytest.raises(RuntimeError, match="hostile len"),
    ):
        await ctx.execute_field(ctx.schema.mutation_type, None, [MagicMock()], None)

    assert not connection.in_atomic_block
    assert not await run_in_one_sync_boundary(_rollback_probe_row_exists)


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_execute_mutation_field_async_exception_rolls_back():
    class DummyMutationCls:
        _mutation_meta = MagicMock(model=None)

    ctx = DjangoMutationExecutionContext.__new__(DjangoMutationExecutionContext)
    ctx.schema = MagicMock()
    ctx.errors = []
    ctx.is_awaitable = lambda val: asyncio.iscoroutine(val) or hasattr(val, "__await__")

    async def async_failing_resolve(*args, **kwargs):
        raise RuntimeError("async field crash")

    with (
        patch.object(ctx, "_marked_mutation_class", return_value=DummyMutationCls),
        patch.object(
            ExecutionContext,
            "execute_field",
            return_value=async_failing_resolve(),
        ),
        pytest.raises(RuntimeError, match="async field crash"),
    ):
        await ctx.execute_field(ctx.schema.mutation_type, None, [MagicMock()], None)


def test_get_extensions_refuses_a_factory_that_resolves_to_an_authority():
    """A factory cannot be classified at construction, so its product is typed here.

    The entry is accepted - a callable is a callable - and what it returns is
    the question. An extension of either enforcement kind is a second authority
    whichever object produced it, and the one thing acceptance cannot certify is
    what the same callable will hand back next request.
    """

    def resource_factory():
        return CustomResourcePolicyExtension(policy=ResourcePolicy(max_list_rows=1))

    schema = DjangoSchema(query=DummyQuery, extensions=[resource_factory])

    _assert_configuration_refusal(schema.execute_sync("{ hello }"))


def test_get_extensions_gives_an_unrelated_factory_both_package_authorities():
    """The control: an ordinary consumer factory runs between the two authorities."""

    def unrelated_factory():
        return _MarkerExtension()

    schema = DjangoSchema(query=DummyQuery, extensions=[unrelated_factory])
    resolved = schema.get_extensions(sync=True)

    assert [type(entry).__name__ for entry in resolved] == [
        "DjangoErrorPolicyExtension",
        "_MarkerExtension",
        "DjangoResourcePolicyExtension",
        "_AdmissionGuard",
        "_OperationModeMarker",
    ]


def test_get_extensions_resolves_one_authority_of_each_kind_for_a_bare_class_entry():
    """A bare class entry declares the automatic extension, so it is not a second one."""
    schema = DjangoSchema(query=DummyQuery, extensions=[DjangoResourcePolicyExtension])
    resolved = schema.get_extensions(sync=True)

    assert schema.extensions == ()
    assert sum(_is_extension(e, DjangoResourcePolicyExtension) for e in resolved) == 1
    assert sum(_is_extension(e, DjangoErrorPolicyExtension) for e in resolved) == 1


def test_get_extensions_sync_and_async():
    schema = DjangoSchema(query=DummyQuery)
    sync_exts = schema.get_extensions(sync=True)
    async_exts = schema.get_extensions(sync=False)
    assert sum(isinstance(e, DjangoErrorPolicyExtension) for e in sync_exts) == 1
    assert sum(isinstance(e, DjangoResourcePolicyExtension) for e in sync_exts) == 1
    assert sum(isinstance(e, DjangoErrorPolicyExtension) for e in async_exts) == 1
    assert sum(isinstance(e, DjangoResourcePolicyExtension) for e in async_exts) == 1


@pytest.mark.parametrize(
    ("attribute", "policy"),
    [
        ("resource_policy", ResourcePolicy(max_list_rows=7)),
        ("error_policy", ErrorPolicy(message="masked")),
    ],
    ids=["resource", "error"],
)
def test_a_schema_policy_attribute_answers_with_a_copy(attribute, policy):
    """``info.schema`` reaches this attribute from every resolver in every request.

    A frozen dataclass refuses ``setattr`` and accepts ``policy.__dict__[name] =
    value``, and the resolved object outlives the request, so handing the stored
    one out would make an attribute documented as configuration into a write seam
    onto every later request's authority.
    """
    schema = DjangoSchema(query=DummyQuery, **{attribute: policy})

    first = getattr(schema, attribute)
    second = getattr(schema, attribute)

    assert first == second
    assert first is not second
    assert first is not policy


@pytest.mark.parametrize(
    "attribute",
    ["resource_policy", "error_policy"],
    ids=["resource", "error"],
)
def test_a_resolver_cannot_install_a_policy_by_writing_the_schema(attribute):
    """``info.schema`` is not a seam onto what the next request is held to.

    The property answers with a copy, which settles what a WRITE THROUGH it can
    do and nothing about what a write BESIDE it can do: an instance attribute is
    an ordinary name, and the schema is process-lived, so one assignment from
    one resolver would have widened - or unmasked - every request the process
    served afterwards. The ``__dict__`` spelling is the one that gets past an
    ordinary property, and it lands nowhere a bound is read from because the
    authority is not an attribute of this object at all.
    """

    @strawberry.type
    class _Query:
        @strawberry.field
        def widen(self, info: strawberry.Info) -> int:
            info.schema.__dict__[attribute] = ResourcePolicy(max_list_rows=999)
            return 1

    schema = DjangoSchema(query=_Query, resource_policy=ResourcePolicy(max_list_rows=2))
    assert schema.execute_sync("{ widen }").data == {"widen": 1}
    assert schema.resource_policy.max_list_rows == 2

    with pytest.raises(AttributeError):
        setattr(schema, attribute, ResourcePolicy(max_list_rows=999))


def test_a_resolver_cannot_disarm_enforcement_by_emptying_the_extension_list():
    """A ``DjangoSchema`` enforces because it is one, not because a list still says so.

    Emptying ``schema.extensions`` would remove the budget and the masking from
    every later operation on the process, which is a wider primitive than
    widening one bound: the next request would run with no policy extension
    instantiated at all. The attribute is a property, so the ``__dict__``
    spelling that gets past an ordinary one lands in a name nothing reads.
    """

    @strawberry.type
    class _Query:
        @strawberry.field
        def rows(self, info: strawberry.Info) -> list[str]:
            info.schema.__dict__["extensions"] = ()
            return list(bounded_rows(["a", "b", "c"], info, None))

    schema = DjangoSchema(query=_Query, resource_policy=ResourcePolicy(max_list_rows=1))
    assert schema.execute_sync("{ rows }").data == {"rows": ["a"]}

    second = schema.execute_sync("{ rows }")
    assert second.errors is None, second.errors
    assert second.data == {"rows": ["a"]}
    resolved = schema.get_extensions(sync=True)
    assert any(isinstance(entry, DjangoResourcePolicyExtension) for entry in resolved)
    assert any(isinstance(entry, DjangoErrorPolicyExtension) for entry in resolved)


@strawberry.type
class _BoundedRowQuery:
    """One field whose rows are bounded by whatever policy the operation armed."""

    @strawberry.field
    def rows(self, info: strawberry.Info) -> list[str]:
        return list(bounded_rows(["a", "b", "c"], info, None))


def _assert_entry_survives_a_replacement_attempt(schema):
    """One accepted configuration keeps running, and keeps bounding, afterwards."""
    assert schema.execute_sync("{ rows }").data == {"rows": ["a"]}
    assert _MARKS == ["accepted"]

    with pytest.raises(ConfigurationError):
        schema.extensions = []

    assert schema.execute_sync("{ rows }").data == {"rows": ["a"]}
    assert _MARKS == ["accepted", "accepted"]
    resolved = schema.get_extensions(sync=True)
    assert sum(isinstance(e, DjangoResourcePolicyExtension) for e in resolved) == 1


@pytest.mark.parametrize(
    "entry",
    [_MarkerExtension, lambda: _MarkerExtension()],
    ids=["class", "factory"],
)
def test_an_accepted_extension_entry_still_runs_after_a_replacement_attempt(entry):
    """Two configuration spellings, one thing to protect.

    A class and a factory are different things to resolve - one is constructed
    per operation by Strawberry, the other is opaque until it is called - and
    the entry the deployment supplied is what each operation is built from,
    whatever a resolver assigns afterwards.
    """
    schema = DjangoSchema(
        query=_BoundedRowQuery,
        extensions=[entry],
        resource_policy=ResourcePolicy(max_list_rows=1),
    )
    _assert_entry_survives_a_replacement_attempt(schema)


def test_an_accepted_extension_instance_still_runs_after_a_replacement_attempt():
    """The third configuration spelling, which Strawberry itself deprecates.

    An instance entry shares one object across every request, so Strawberry
    warns on it; the package still accepts it as configuration, and accepted
    configuration is what runs.
    """
    with pytest.warns(DeprecationWarning):
        schema = DjangoSchema(
            query=_BoundedRowQuery,
            extensions=[_MarkerExtension()],
            resource_policy=ResourcePolicy(max_list_rows=1),
        )
    _assert_entry_survives_a_replacement_attempt(schema)


def test_a_policy_declared_by_an_entry_and_by_the_argument_is_refused():
    """Two declarations of one ceiling are a configuration with two answers."""
    with pytest.raises(ConfigurationError, match="declared twice"):
        DjangoSchema(
            query=DummyQuery,
            extensions=[DjangoResourcePolicyExtension(policy=ResourcePolicy(max_list_rows=5))],
            resource_policy=ResourcePolicy(max_list_rows=3),
        )


def test_two_entries_declaring_a_policy_of_their_own_are_refused():
    """Two entries carrying a policy are the same two answers, spelled differently."""
    with pytest.raises(ConfigurationError, match="two resource-policy"):
        DjangoSchema(
            query=DummyQuery,
            extensions=[
                DjangoResourcePolicyExtension(policy=ResourcePolicy(max_list_rows=5)),
                DjangoResourcePolicyExtension(policy=ResourcePolicy(max_list_rows=3)),
            ],
        )


def test_a_policy_declared_by_an_entry_becomes_the_schemas_own():
    """An entry declaring a policy is read once, where it is accepted, and folded in.

    Keeping the entry would leave the object a resolver reaches through
    ``info.schema.extensions`` deciding what the next request is bounded by;
    dropping what it declared would answer the deployment with a ceiling it did
    not choose. The record takes the declaration and the entry does not travel.
    """
    schema = DjangoSchema(
        query=_BoundedRowQuery,
        extensions=[DjangoResourcePolicyExtension(policy=ResourcePolicy(max_list_rows=1))],
    )

    assert schema.extensions == ()
    assert schema.resource_policy.max_list_rows == 1
    assert schema.execute_sync("{ rows }").data == {"rows": ["a"]}


def test_a_schema_with_no_enforcement_record_is_bounded_by_the_package_defaults():
    """The fail-closed miss path: no record means the package defaults, never none.

    Reachable through a subclass that never completes ``DjangoSchema.__init__``.
    The answer is what a schema that declared nothing gets rather than an error,
    because a schema that cannot say what it was configured with is still a
    schema that has to bound the request in front of it.
    """

    class _Unregistered(DjangoSchema):
        def __init__(self):
            pass

    schema = _Unregistered()
    assert _SCHEMA_ENFORCEMENT.recall(schema) is None
    assert schema.resource_policy == ResourcePolicy()
    assert schema.error_policy == ErrorPolicy()
    assert schema.extensions == ()


def test_two_schemas_that_compare_equal_keep_their_own_enforcement():
    """An enforcement record belongs to one object, not to everything equal to it.

    A registry that finds its entries by hash and equality hands a consumer
    subclass the choice of which schema's bounds answer for which schema: the
    second construction overwrites the first schema's record, and the first
    schema's collection takes the entry the second is still being enforced by.
    """

    class _EqualSchema(DjangoSchema):
        def __hash__(self):
            return 1

        def __eq__(self, other):
            return isinstance(other, _EqualSchema)

    narrow = _EqualSchema(query=DummyQuery, resource_policy=ResourcePolicy(max_list_rows=1))
    wide = _EqualSchema(query=DummyQuery, resource_policy=ResourcePolicy(max_list_rows=999))

    assert narrow.resource_policy.max_list_rows == 1
    assert wide.resource_policy.max_list_rows == 999

    del narrow
    gc.collect()

    assert wide.resource_policy.max_list_rows == 999


def test_a_schema_that_cannot_be_hashed_is_still_constructible_and_bounded():
    """Identity needs no hash, so declaring ``__eq__`` cannot cost a schema its record."""

    class _UnhashableSchema(DjangoSchema):
        __hash__ = None

        def __eq__(self, other):
            return self is other

    schema = _UnhashableSchema(query=DummyQuery, resource_policy=ResourcePolicy(max_list_rows=3))

    assert schema.resource_policy.max_list_rows == 3


class _ContextSentinel:
    """A value one request's context carries, so a retained context is observable."""


class _FactorySchema(DjangoSchema):
    """A schema configured with a BOUND METHOD, which is the non-deprecated factory."""

    def make_extension(self):
        """Build this schema's consumer extension, fresh per operation."""
        return _MarkerExtension()

    def __init__(self, **kwargs):
        super().__init__(extensions=[self.make_extension], **kwargs)


def _reachability_after_dropping(make_schema, *, execute):
    """Whether the schema, its record, and one request's context survive collection."""
    schema = make_schema()
    record = _SCHEMA_ENFORCEMENT.recall(schema)
    assert record is not None
    schema_ref = weakref.ref(schema)
    record_ref = weakref.ref(record)
    sentinel = _ContextSentinel()
    sentinel_ref = weakref.ref(sentinel)
    if execute:
        result = schema.execute_sync("{ hello }", context_value={"sentinel": sentinel})
        assert result.errors is None, result.errors

    del schema, record, sentinel
    gc.collect()

    return (schema_ref(), record_ref(), sentinel_ref())


@pytest.mark.parametrize(
    ("configure", "execute"),
    [
        (lambda: DjangoSchema(query=DummyQuery), False),
        (lambda: DjangoSchema(query=DummyQuery), True),
        (lambda: _FactorySchema(query=DummyQuery), False),
    ],
    ids=["class-entry", "class-entry-after-execution", "bound-method-factory"],
)
def test_a_schema_stays_collectable_whatever_configured_it(configure, execute):
    """Holding a schema's configuration must not hold the schema.

    An extension instance acquires its execution context when the operation
    runs, and that context owns the schema; a factory can be a bound method,
    which owns the schema before any request at all. Either one reached from a
    module-global root would keep every schema built per test or per tenant
    alive for the life of the process - and with it the last request's context
    and variables. What owns a record is therefore the schema itself, and what
    this package holds is a weak reference to it.
    """
    assert _reachability_after_dropping(configure, execute=execute) == (None, None, None)


def test_an_accepted_extension_instance_does_not_outlive_its_schema():
    """The instance spelling, whose extension holds the execution context it ran under."""
    with pytest.warns(DeprecationWarning):
        alive = _reachability_after_dropping(
            lambda: DjangoSchema(query=DummyQuery, extensions=[_MarkerExtension()]),
            execute=True,
        )
    assert alive == (None, None, None)


@pytest.mark.parametrize(
    "attack",
    [
        lambda schema: schema.__dict__.update(
            _django_enforcement=SimpleNamespace(
                resource_policy=ResourcePolicy(max_list_rows=999),
                error_policy=ErrorPolicy(enabled=False),
            ),
        ),
        lambda schema: schema.__dict__.clear(),
    ],
    ids=["write-an-attribute", "empty-the-schema-dictionary"],
)
def test_the_accepted_policies_survive_every_write_to_the_schema(attack):
    """No name on a schema answers with the policies it was accepted with.

    ``info.schema`` is handed to every resolver, so anything the schema holds a
    reference to is a process-lived seam: rebinding it nominates new policies
    for every later request, and deleting it selects whatever the fallback is.
    Neither is available, because the policies are not held on the schema at
    all - which is why nothing in this row has to be detected before it can be
    refused.
    """
    schema = DjangoSchema(query=DummyQuery, resource_policy=ResourcePolicy(max_list_rows=1))
    assert schema.resource_policy.max_list_rows == 1

    attack(schema)

    assert schema.resource_policy.max_list_rows == 1
    assert schema.error_policy.enabled is True


def test_no_name_on_a_schema_answers_with_a_policy():
    """The census behind the row above, quantified over what the schema carries.

    A row that names the attribute it expects to be absent passes once the
    attribute is renamed. This one asks the question by CONTENT: nothing a
    resolver reaches through ``info.schema`` is a policy, or holds one.
    """
    schema = DjangoSchema(query=DummyQuery, resource_policy=ResourcePolicy(max_list_rows=1))

    held = list(vars(schema).values())
    assert held
    for value in held:
        assert not isinstance(value, (ResourcePolicy, ErrorPolicy))
        assert not isinstance(getattr(value, "resource_policy", None), ResourcePolicy)
        assert not isinstance(getattr(value, "error_policy", None), ErrorPolicy)


def test_a_schema_cannot_be_reconfigured_by_running_its_constructor():
    """A constructed schema is reachable from every resolver, and so is its ``__init__``.

    Re-running it would settle new policies for every later request the process
    serves. The accepted record stays and the base constructor never runs, so
    the schema is left exactly as the deployment built it.
    """
    schema = DjangoSchema(query=DummyQuery, resource_policy=ResourcePolicy(max_list_rows=1))

    with pytest.raises(ConfigurationError, match="configured when it is constructed"):
        schema.__init__(query=DummyQuery, resource_policy=ResourcePolicy(max_list_rows=999))

    assert schema.resource_policy.max_list_rows == 1
    assert schema.execute_sync("{ hello }").errors is None


def _schema_holding_an_unnamed_entry(rows=1):
    """A schema whose accepted entries include one the attribute is the last hold on.

    An entry that is a module-level class outlives any write to the attribute,
    because the module still names it. A factory built into the
    ``extensions=[...]`` argument is named by nothing else, so a write that
    drops it is a write that ENDS it - which is the configuration loss the
    refusal answers, and the one a consumer's own entry is most exposed to. It
    is also the entry the package can say least about in advance: a factory is
    called once per operation, and what it returns is the consumer's.
    """

    def marking_extension():
        return _MarkerExtension()

    return DjangoSchema(
        query=DummyQuery,
        resource_policy=ResourcePolicy(max_list_rows=rows),
        extensions=[marking_extension],
    )


def _widening_factory():
    """An extension entry a resolver would rather the next operation resolved."""
    return _ForgedMarkerExtension()


@pytest.mark.parametrize(
    "attack",
    [
        lambda schema: schema.__dict__.update(_django_extensions=()),
        lambda schema: schema.__dict__.update(_django_extensions=(_widening_factory,)),
        lambda schema: schema.__dict__.pop("_django_extensions"),
    ],
    ids=["empty-the-entries", "replace-the-entries", "delete-the-entries"],
)
def test_the_accepted_extensions_are_answered_for_entry_by_entry(attack):
    """What runs the next operation is a membership, not the identity of a carrier.

    A carrier holding the entries is one whose identity a write to its contents
    leaves exactly as accepted, so nothing about the carrier answers the
    question that matters: WHICH extensions enforce the next request. Each entry
    is therefore answered for on its own, and an entry written over the
    attribute is one no construction accepted - it does not become this schema's
    configuration by being put where the configuration is held.
    """
    schema = DjangoSchema(
        query=_RowQuery,
        resource_policy=ResourcePolicy(max_list_rows=1),
        extensions=[_MarkerExtension],
    )
    assert schema.execute_sync("{ rows }").data == {"rows": ["a"]}

    attack(schema)

    assert schema.extensions == (_MarkerExtension,)
    assert schema.execute_sync("{ rows }").data == {"rows": ["a"]}
    assert _MARKS == ["accepted", "accepted"]
    resolved = schema.get_extensions(sync=True)
    assert any(isinstance(entry, DjangoErrorPolicyExtension) for entry in resolved)
    assert any(isinstance(entry, DjangoResourcePolicyExtension) for entry in resolved)


@pytest.mark.parametrize(
    "attack",
    [
        lambda schema: schema.__dict__.update(_django_extensions=("forged",)),
        lambda schema: schema.__dict__.pop("_django_extensions"),
    ],
    ids=["forge-the-configuration", "delete-the-configuration"],
)
def test_an_operation_is_refused_when_the_accepted_extensions_cannot_be_read_back(attack):
    """The accepted entries are the only record of what the consumer asked to run.

    A factory's extension is built per operation and named by nothing else, so
    once the entries are gone there is nothing to fall back to that is not
    wider than what the deployment chose. The operation is refused, and the
    refusal is published rather than raised so every transport renders it.
    """
    schema = _schema_holding_an_unnamed_entry()
    assert schema.execute_sync("{ hello }").errors is None

    attack(schema)

    assert schema.extensions == ()
    result = schema.execute_sync("{ hello }")
    assert result.data is None
    assert len(result.errors) == 1
    assert result.errors[0].extensions == {"code": SCHEMA_CONFIGURATION_ERROR_CODE}

    resolved = schema.get_extensions(sync=True)
    assert [type(entry).__name__ for entry in resolved] == [
        "DjangoErrorPolicyExtension",
        "_RefusedConfiguration",
        "DjangoResourcePolicyExtension",
        "_OperationModeMarker",
    ]
    assert _MARKS == ["accepted"]


def test_a_refused_schema_does_not_begin_executing_either():
    """The refusal is restated where execution starts, for a path that got that far."""
    schema = _schema_holding_an_unnamed_entry()
    schema.__dict__.pop("_django_extensions")
    refusal = schema.get_extensions(sync=True)[1]

    with pytest.raises(GraphQLError, match="could not be read back"):
        refusal.on_execute()


def test_replacing_the_accepted_extensions_does_not_make_a_schema_unconstructed():
    """Losing an entry must not reopen the one write the setter admits."""
    schema = _schema_holding_an_unnamed_entry()
    schema.__dict__.pop("_django_extensions")

    with pytest.raises(ConfigurationError, match="settled when the schema is constructed"):
        schema.extensions = [DjangoResourcePolicyExtension(policy=ResourcePolicy())]

    assert _SCHEMA_EXTENSIONS.recall(schema) is None


class _SlottedFactory:
    """A valid extension factory whose layout admits no weak reference.

    ``__slots__`` without ``__weakref__`` is an ordinary, supported way to write
    a callable, and Strawberry runs one exactly as it runs any other factory.
    Refusing it would be refusing a memory layout rather than a configuration.
    """

    __slots__ = ()

    def __call__(self):
        return _MarkerExtension()


class _InertExtension(SchemaExtension):
    """A module-level entry that runs nothing and is weak-referenceable."""


class _WeakReferenceableFactory:
    """The control: the same factory, with the layout a weak reference can be taken of."""

    def __call__(self):
        return _MarkerExtension()


class _WideningSlottedFactory:
    """The entry a resolver would rather the schema resolved, in the same layout."""

    __slots__ = ()

    def __call__(self):
        return _ForgedMarkerExtension()


@pytest.mark.parametrize(
    "factory",
    [_SlottedFactory, _WeakReferenceableFactory],
    ids=["slotted-callable", "weak-referenceable-control"],
)
def test_a_slotted_callable_factory_is_accepted_and_runs(factory):
    """A callable factory works whatever its object layout is.

    Strawberry accepts either one, so a schema that refused the slotted form
    would be refusing a configuration for a reason that has nothing to do with
    what runs the operation. Both build the extension per operation and both
    run it.
    """
    schema = DjangoSchema(
        query=_RowQuery,
        resource_policy=ResourcePolicy(max_list_rows=1),
        extensions=[factory()],
    )

    assert schema.execute_sync("{ rows }").data == {"rows": ["a"]}
    assert _MARKS == ["accepted"]


def test_a_slotted_entry_does_not_root_the_schema_that_holds_it():
    """The entry a global table could most easily have ended up holding strongly.

    A slotted entry is the one whose evidence is not a weak reference to itself,
    so the sealed holder is where the temptation to hold it globally lives. The
    holder belongs to the SCHEMA, and the record here keeps one weak reference to
    it - so the schema, its enforcement record and the last request's context all
    stay collectable, exactly as they do for every other spelling
    (``test_a_schema_stays_collectable_whatever_configured_it``).
    """
    alive = _reachability_after_dropping(
        lambda: DjangoSchema(query=DummyQuery, extensions=[_SlottedFactory()]),
        execute=True,
    )
    assert alive == (None, None, None)


def test_a_mixed_entry_list_answers_each_entry_from_its_own_evidence():
    """A rewritten attribute runs nothing it nominated, whichever form an entry takes.

    The weak-referenceable entry here is a module-level class, which the module
    still names after the write, so its evidence still resolves and the accepted
    original is what the next operation runs. The slotted entry is answered from
    the box the schema holds it in, which that same write replaced - and the only
    record of what it declared is gone, so the operation is refused rather than
    resolved against whatever was put there.
    """
    schema = DjangoSchema(
        query=_RowQuery,
        resource_policy=ResourcePolicy(max_list_rows=1),
        extensions=[_InertExtension, _SlottedFactory()],
    )
    assert schema.execute_sync("{ rows }").data == {"rows": ["a"]}
    assert _MARKS == ["accepted"]

    schema.__dict__.update(_django_extensions=(_widening_factory,))
    gc.collect()

    assert schema.extensions == ()
    refused = schema.execute_sync("{ rows }")
    assert refused.data is None
    assert refused.errors[0].extensions == {"code": SCHEMA_CONFIGURATION_ERROR_CODE}


def test_a_weak_only_entry_list_survives_the_same_write():
    """The control that keeps the mixed row honest: nothing here needs the holder.

    Every entry is a class the module still names, so every piece of evidence
    still resolves and the write nominates nothing. The difference between this
    row and the mixed one is the slotted entry alone.
    """
    schema = DjangoSchema(
        query=_RowQuery,
        resource_policy=ResourcePolicy(max_list_rows=1),
        extensions=[_MarkerExtension],
    )
    assert schema.execute_sync("{ rows }").data == {"rows": ["a"]}

    schema.__dict__.update(_django_extensions=(_widening_factory,))
    gc.collect()

    assert schema.extensions == (_MarkerExtension,)
    assert schema.execute_sync("{ rows }").data == {"rows": ["a"]}
    assert _MARKS == ["accepted", "accepted"]


@pytest.mark.parametrize(
    "tamper",
    [
        lambda box, replacement: setattr(box, "__self__", replacement),
        lambda box, replacement: object.__setattr__(box, "__self__", replacement),
        lambda box, replacement: delattr(box, "__self__"),
    ],
    ids=["assign-the-binding", "assign-it-past-the-descriptor", "delete-the-binding"],
)
def test_the_box_a_slotted_entry_is_answered_through_cannot_be_rebound(tamper):
    """Evidence about a carrier certifies nothing if the carrier can be rewritten.

    A slotted entry has no weak reference of its own, so it is answered through
    a box the schema holds - and the box is evidence only while the member it
    hands back is the member it was built on. A Python object cannot promise
    that: whatever its ``__setattr__`` refuses, the primitive its own
    constructor writes the slot with is one a resolver can call too. This box is
    the interpreter's own binding, and the spellings here are the ways there are
    to aim at it.

    What the row reads is the mark: the accepted factory records ``accepted``
    and the replacement records ``forged``, so an admitted replacement is
    visible in what ran.
    """
    accepted = _SlottedFactory()
    replacement = _WideningSlottedFactory()
    schema = DjangoSchema(
        query=_RowQuery,
        resource_policy=ResourcePolicy(max_list_rows=1),
        extensions=[accepted],
    )
    box = next(
        held
        for held in schema.__dict__["_django_extensions"]
        if getattr(held, "__self__", None) is accepted
    )

    with pytest.raises(AttributeError):
        tamper(box, replacement)

    assert box.__self__ is accepted
    assert schema.execute_sync("{ rows }").data == {"rows": ["a"]}
    assert _MARKS == ["accepted"]


def test_rebuilding_the_box_a_slotted_entry_is_answered_through_changes_nothing():
    """The second constructor call, which is not an attribute write and is refused anyway.

    ``__init__`` on an already-built binding is the one spelling that raises
    nothing, so the assertion is the binding itself rather than an exception.
    """
    accepted = _SlottedFactory()
    schema = DjangoSchema(
        query=_RowQuery,
        resource_policy=ResourcePolicy(max_list_rows=1),
        extensions=[accepted],
    )
    box = next(
        held
        for held in schema.__dict__["_django_extensions"]
        if getattr(held, "__self__", None) is accepted
    )

    box.__init__(_WideningSlottedFactory())

    assert box.__self__ is accepted
    assert schema.execute_sync("{ rows }").data == {"rows": ["a"]}
    assert _MARKS == ["accepted"]


@pytest.mark.parametrize(
    "entry",
    [(), "DjangoResourcePolicyExtension", 7],
    ids=["a-tuple", "a-name", "a-number"],
)
def test_an_extension_entry_strawberry_could_not_resolve_is_refused(entry):
    """Acceptance is per entry, and the one reason to refuse one is resolution.

    Strawberry resolves an entry as itself when it is an extension instance and
    by CALLING it otherwise, so a class, an instance and a factory are the three
    shapes that work. A builtin value is none of them and fails at the first
    operation, deep inside the engine, on a schema the deployment already
    started; the refusal names it where it was supplied instead. What is NOT a
    reason is a memory layout - see
    ``test_a_slotted_callable_factory_is_accepted_and_enforces``.
    """
    with pytest.raises(ConfigurationError, match="is none of those"):
        DjangoSchema(query=DummyQuery, extensions=[entry])


@pytest.mark.parametrize(
    (
        "argument",
        "policy",
        "field",
        "widened",
    ),
    [
        (
            "resource_policy",
            ResourcePolicy(max_list_rows=1),
            "max_list_rows",
            999,
        ),
        (
            "error_policy",
            ErrorPolicy(),
            "enabled",
            False,
        ),
    ],
    ids=["resource", "error"],
)
def test_a_retained_policy_argument_is_not_the_one_the_schema_enforces(
    argument,
    policy,
    field,
    widened,
):
    """The caller keeps their object; the schema keeps a duplicate of its values.

    An exact instance used to pass through configuration intake unchanged, so a
    caller who retained the argument - or who left one in ``settings`` - still
    held the object every bound was read from, and a frozen dataclass admits
    ``policy.__dict__[bound] = wider`` by the same route the schema attribute
    does.
    """
    schema = DjangoSchema(query=DummyQuery, **{argument: policy})

    policy.__dict__[field] = widened

    assert getattr(getattr(schema, argument), field) != widened


def test_a_policy_behind_the_setting_is_snapshotted_like_an_explicit_one(settings):
    """The two override slots are one ladder, so they detach on the same terms.

    A settings-supplied instance is the one a deployment is most likely to keep
    a reference to: it lives at module scope for the life of the process.
    """
    policy = ResourcePolicy(max_list_rows=2)
    settings.DJANGO_STRAWBERRY_FRAMEWORK = {"RESOURCE_POLICY": policy}
    schema = DjangoSchema(query=DummyQuery)

    policy.__dict__["max_list_rows"] = 999

    assert schema.resource_policy.max_list_rows == 2


def test_an_exact_policy_corrupted_before_intake_is_rejected_at_construction():
    """``__post_init__`` spoke for the values an instance was BUILT with.

    Admitting an exact instance without re-reading it made the type the evidence
    and the fields an assumption, so a bound written onto the object after it
    validated reached the schema as configuration.
    """
    policy = ResourcePolicy()
    policy.__dict__["max_list_rows"] = 0

    with pytest.raises(ConfigurationError):
        DjangoSchema(query=DummyQuery, resource_policy=policy)


def test_widening_a_schema_policy_copy_leaves_the_schemas_own_bound():
    """The write lands on the reader's duplicate and nowhere a bound is read from."""
    schema = DjangoSchema(query=DummyQuery, resource_policy=ResourcePolicy(max_list_rows=7))

    schema.resource_policy.__dict__["max_list_rows"] = 999

    assert schema.resource_policy.max_list_rows == 7


# ---------------------------------------------------------------------------
# The resolved chain, admitted as one transaction
#
# Live sibling: the wire shape of a refusal, on ``/iso-chain/``.
# ---------------------------------------------------------------------------


class _SlottedConsumerFactory:
    """A valid consumer-extension factory in the layout that takes no weak reference."""

    __slots__ = ()

    def __call__(self):
        return _MarkerExtension()


class _MutableResourceFactory:
    """A stateful factory whose returned bound is decided after it was accepted."""

    def __init__(self, rows=1):
        self.rows = rows

    def __call__(self):
        return DjangoResourcePolicyExtension(policy=ResourcePolicy(max_list_rows=self.rows))


class _SelectingErrorFactory:
    """A factory choosing between two masking extensions, after it was accepted."""

    def __init__(self):
        self.chosen = DjangoErrorPolicyExtension()

    def __call__(self):
        return self.chosen


class _BoundMethodResourceFactory:
    """A bound method, which is a factory whose owner decides what it returns."""

    def __init__(self):
        self.rows = 1

    def build(self):
        """Build the resource extension this owner currently wants."""
        return DjangoResourcePolicyExtension(policy=ResourcePolicy(max_list_rows=self.rows))


class _CountingAuthorityFactory:
    """A factory that records how many times the package called it."""

    def __init__(self):
        self.calls = 0

    def __call__(self):
        self.calls += 1
        return DjangoResourcePolicyExtension()


class _HybridFactory:
    """A factory returning one object that answers to both authorities."""

    def __init__(self, hybrid_type):
        self._hybrid_type = hybrid_type

    def __call__(self):
        return self._hybrid_type()


class _SingletonHybridFactory:
    """The same, handing back one shared object every time."""

    def __init__(self, hybrid_type):
        self._hybrid = hybrid_type()

    def __call__(self):
        return self._hybrid


def _closure_resource_factory():
    """A closure over a mutable cell, which is the same defect without an attribute."""
    cell = {"rows": 1}

    def factory():
        return DjangoResourcePolicyExtension(policy=ResourcePolicy(max_list_rows=cell["rows"]))

    factory.cell = cell
    return factory


def _narrow_resource_factory():
    """A factory producing a resource extension with a bound of its own."""
    return DjangoResourcePolicyExtension(policy=ResourcePolicy(max_aliases=1))


def _wide_resource_factory():
    """The same, with a bound wide enough to admit what the narrow one refuses."""
    return DjangoResourcePolicyExtension(policy=ResourcePolicy(max_aliases=999))


_SHARED_ERROR_EXTENSION = DjangoErrorPolicyExtension()

_SHARED_MARKER_EXTENSION = _MarkerExtension()


def _first_error_factory():
    """A factory producing a masking extension for the operation."""
    return DjangoErrorPolicyExtension()


def _singleton_error_factory():
    """One masking extension, returned every time."""
    return _SHARED_ERROR_EXTENSION


def _fresh_marker_factory():
    """The supported consumer spelling: a new extension per operation."""
    return _MarkerExtension()


def _singleton_marker_factory():
    """The documented shared-instance spelling: one object, returned every time."""
    return _SHARED_MARKER_EXTENSION


class _BoundMethodMarkerFactory:
    """The bound-method spelling, for an extension that is not an authority."""

    def build(self):
        """Build this owner's consumer extension, fresh per operation."""
        return _MarkerExtension()


_SHARED_OPTIMIZER_EXTENSION = DjangoOptimizerExtension()


def _optimizer_singleton_factory():
    """The optimizer's own documented spelling, whose cache is deliberately shared."""
    return _SHARED_OPTIMIZER_EXTENSION


def _assert_configuration_refusal(result):
    """The operation ran nothing and said so with the stable code."""
    assert result.data is None
    assert [error.extensions for error in result.errors] == [
        {"code": SCHEMA_CONFIGURATION_ERROR_CODE},
    ]


@pytest.mark.parametrize(
    "entry",
    [
        _narrow_resource_factory,
        _wide_resource_factory,
        _first_error_factory,
        _singleton_error_factory,
        _MutableResourceFactory(),
        _SelectingErrorFactory(),
        _closure_resource_factory(),
        _BoundMethodResourceFactory().build,
        _HybridFactory(HybridPolicyExtension),
        _HybridFactory(ReversedHybridPolicyExtension),
        _SingletonHybridFactory(HybridPolicyExtension),
        _SingletonHybridFactory(ReversedHybridPolicyExtension),
    ],
    ids=[
        "narrow-resource-factory",
        "wide-resource-factory",
        "fresh-error-factory",
        "singleton-error-factory",
        "mutable-resource-factory",
        "selecting-error-factory",
        "closure-resource-factory",
        "bound-method-resource-factory",
        "hybrid-fresh-factory",
        "hybrid-fresh-factory-reversed-bases",
        "hybrid-singleton-factory",
        "hybrid-singleton-factory-reversed-bases",
    ],
)
def test_a_factory_producing_an_enforcement_authority_refuses_the_operation(entry):
    """A factory is opaque until it runs, so what it produces is typed at resolution.

    Accepting the callable proves which object this schema was configured with,
    and that is all it proves: the object is consumer code, ``info.schema``
    hands it to every resolver, and the extension it returns NEXT request is
    decided after this one. A stateful factory, a closure over a mutable cell
    and a singleton selector are the same fact spelled three ways, and none of
    them can be an enforcement authority.
    """
    schema = DjangoSchema(query=DummyQuery, extensions=[entry])

    _assert_configuration_refusal(schema.execute_sync("{ hello }"))


def test_a_refused_factory_is_called_once_and_never_inspected_again():
    """Resolution calls the entries once, and every check reads what came back.

    Calling a factory a second time to find out what it is would run consumer
    code twice for one operation, and the second answer need not be the first.
    """
    factory = _CountingAuthorityFactory()
    schema = DjangoSchema(query=DummyQuery, extensions=[factory])

    _assert_configuration_refusal(schema.execute_sync("{ hello }"))

    assert factory.calls == 1


def test_a_refusal_carries_no_representation_of_the_member_that_caused_it():
    """The wire gets the stable code; the object stays in the deployment's own log."""
    schema = DjangoSchema(query=DummyQuery, extensions=[_HybridFactory(HybridPolicyExtension)])

    result = schema.execute_sync("{ hello }")

    assert result.errors[0].extensions == {"code": SCHEMA_CONFIGURATION_ERROR_CODE}
    for fragment in (
        "HybridPolicyExtension",
        "ResourcePolicy",
        "max_list_rows",
        "object at 0x",
    ):
        assert fragment not in result.errors[0].message


def test_a_resolver_cannot_widen_a_later_request_through_an_accepted_factory():
    """The attack the refusal exists for, made from inside a resolver.

    The factory is reachable through ``info.schema.extensions`` and its
    membership evidence never changes, so identity proves nothing about the
    ceiling the next operation gets. The schema is refused from its first
    operation rather than served until someone widens it.
    """
    factory = _MutableResourceFactory()

    @strawberry.type
    class WideningQuery:
        @strawberry.field
        def widen(self, info: strawberry.Info) -> bool:
            """Reach the accepted factory the way any resolver can, and widen it."""
            for entry in info.schema.extensions:
                if entry is factory:
                    entry.rows = 999
                    return True
            return False

    schema = DjangoSchema(
        query=WideningQuery,
        extensions=[factory],
        resource_policy=ResourcePolicy(max_list_rows=1),
    )

    _assert_configuration_refusal(schema.execute_sync("{ widen }"))
    assert factory.rows == 1
    assert schema.resource_policy.max_list_rows == 1


@pytest.mark.parametrize(
    "entry",
    [
        _SlottedConsumerFactory(),
        _MarkerExtension,
        _fresh_marker_factory,
        _singleton_marker_factory,
        _BoundMethodMarkerFactory().build,
        _optimizer_singleton_factory,
    ],
    ids=[
        "slotted-factory",
        "class",
        "fresh-factory",
        "singleton-factory",
        "bound-method",
        "optimizer-singleton-factory",
    ],
)
def test_every_supported_entry_spelling_still_resolves_into_one_chain(entry):
    """The controls that keep the refusals honest: every consumer spelling still runs.

    A memory layout that takes no weak reference, a class, a module-level
    function, a factory handing back one shared object and the optimizer's own
    documented singleton-in-a-factory are configurations rather than defects.
    Each resolves between exactly one masking authority and exactly one resource
    authority, both of which are the schema's.
    """
    schema = DjangoSchema(query=DummyQuery, extensions=[entry])
    resolved = schema.get_extensions(sync=True)

    assert schema.execute_sync("{ hello }").data == {"hello": "world"}
    assert sum(_is_extension(e, DjangoErrorPolicyExtension) for e in resolved) == 1
    assert sum(_is_extension(e, DjangoResourcePolicyExtension) for e in resolved) == 1
    assert len(resolved) == 5


@pytest.mark.parametrize(
    ("document", "code"),
    [
        ("{", SCHEMA_CONFIGURATION_ERROR_CODE),
        ("{ hello }", SCHEMA_CONFIGURATION_ERROR_CODE),
        ("query Named { hello }", SCHEMA_CONFIGURATION_ERROR_CODE),
        ("mutation { plainMutation }", SCHEMA_CONFIGURATION_ERROR_CODE),
    ],
    ids=[
        "malformed",
        "valid",
        "named-operation",
        "mutation",
    ],
)
def test_a_refused_schema_answers_every_document_with_the_configuration_code(document, code):
    """Refusing every operation includes the ones that would not have parsed.

    Publishing after the parse would make the claim true only of well-formed
    documents: a syntax error is raised out of the parse itself and upstream
    answers with it before any statement after the hook's ``yield`` runs. The
    refusal is published first and the parse stage is handed a document of the
    package's own, so the client is told the same thing whatever it sent.
    """
    schema = DjangoSchema(query=DummyQuery, mutation=DummyMutation, extensions=[lambda: 7])

    result = schema.execute_sync(document)

    assert result.data is None
    assert [error.extensions for error in result.errors] == [{"code": code}]


def test_a_refused_schema_still_bounds_the_document_it_is_refusing():
    """A broken configuration must not be the one shape with no parsing ceiling.

    The refusal chain keeps the package's own resource extension, reading this
    schema's private policy, so the pre-parse token and depth scan still runs.
    Without it a deployment with one bad factory would have traded "every
    operation fails closed" for an endpoint that lexes and nests whatever it is
    sent before saying no.
    """
    schema = DjangoSchema(
        query=DummyQuery,
        extensions=[lambda: 7],
        resource_policy=ResourcePolicy(max_document_tokens=1),
    )

    assert [type(entry).__name__ for entry in schema.get_extensions(sync=True)] == [
        "DjangoErrorPolicyExtension",
        "_RefusedConfiguration",
        "DjangoResourcePolicyExtension",
        "_OperationModeMarker",
    ]
    over_budget = schema.execute_sync("{ a: hello b: hello }")
    assert [error.extensions["code"] for error in over_budget.errors] == [
        "RESOURCE_LIMIT_EXCEEDED",
    ]


@pytest.mark.parametrize(
    ("document", "code"),
    [
        ("{ hello }", SCHEMA_CONFIGURATION_ERROR_CODE),
        ("{ a: hello b: hello }", "RESOURCE_LIMIT_EXCEEDED"),
    ],
    ids=["refused", "over-budget"],
)
def test_a_refused_request_runs_no_parser_at_all(document, code):
    """Neither answer a refused schema gives is one a parser had to produce.

    The refusal is published at a pre-parse seam and the over-budget rejection
    is raised by the token scan before the parse stage runs at all, so the
    document a broken deployment is sent is never handed to graphql-core's
    recursive parser. The refusal's own substitute documents are parsed once at
    import, so the claim is the whole one - no parser runs on a refused request -
    rather than only the dangerous half.

    Both bindings are patched. The package calls ``parse`` through its own
    module and upstream calls it through ``strawberry.schema.schema``; watching
    one of them proves nothing about the other, and it is the package's own
    binding that a per-request parse would go through.
    """
    schema = DjangoSchema(
        query=DummyQuery,
        extensions=[lambda: 7],
        resource_policy=ResourcePolicy(max_document_tokens=3),
    )
    parsed: list[str] = []

    def _record(source, **kwargs):
        parsed.append(str(source))
        raise AssertionError("a refused configuration must not reach a parser")

    with (
        patch("strawberry.schema.schema.parse", _record),
        patch("django_strawberry_framework.schema.parse", _record),
    ):
        result = schema.execute_sync(document)

    assert result.data is None
    assert [error.extensions["code"] for error in result.errors] == [code]
    assert parsed == []


#: Every operation name a request can arrive with, including the ones no
#: document can carry. A refused schema has discarded the document the name was
#: written against, so each has to reach the same stable answer.
_REFUSED_OPERATION_NAMES = [
    None,
    "Absent",
    "bad-name",
    "",
    "\N{FIRE}",
    0,
]

_REFUSED_OPERATION_NAME_IDS = [
    "none",
    "valid-but-absent",
    "invalid-punctuation",
    "empty",
    "unicode",
    "not-a-string",
]


@pytest.mark.parametrize(
    "operation_name",
    _REFUSED_OPERATION_NAMES,
    ids=_REFUSED_OPERATION_NAME_IDS,
)
def test_a_refused_schema_answers_every_operation_name_the_same_way(operation_name):
    """The name a request asked for selects nothing once the document is the package's.

    Upstream picks the operation to run by looking the requested name up in
    whatever document the parse stage left behind. A refused request's document
    is the package's own, so a name that survived into the selector is a lookup
    that cannot succeed - and upstream raises that failure out of the API,
    over a refusal already published. The name is normalized with the document.
    """
    schema = DjangoSchema(query=DummyQuery, extensions=[lambda: 7])

    result = schema.execute_sync("{ hello }", operation_name=operation_name)

    assert result.data is None
    assert [error.extensions for error in result.errors] == [
        {"code": SCHEMA_CONFIGURATION_ERROR_CODE},
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "operation_name",
    _REFUSED_OPERATION_NAMES,
    ids=_REFUSED_OPERATION_NAME_IDS,
)
async def test_a_refused_schema_answers_an_awaited_operation_name_the_same_way(operation_name):
    """The asynchronous API refuses the same names, and raises out of none of them."""
    schema = DjangoSchema(query=DummyQuery, extensions=[lambda: 7])

    result = await schema.execute("{ hello }", operation_name=operation_name)

    assert result.data is None
    assert [error.extensions for error in result.errors] == [
        {"code": SCHEMA_CONFIGURATION_ERROR_CODE},
    ]


@_SKIP_WITHOUT_STREAM
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "operation_name",
    _REFUSED_OPERATION_NAMES,
    ids=_REFUSED_OPERATION_NAME_IDS,
)
async def test_a_refused_schema_streams_one_refusal_for_every_operation_name(operation_name):
    """A stream owes a FRAME for each of these, not an exception and not a lookup error.

    The stream is the path where the escaped lookup was quietest: upstream
    renders its own "unknown operation" into the first frame, so a transport
    saw a well-formed error frame carrying a different story than the sync API
    told about the same request.
    """
    schema = DjangoSchema(query=DummyQuery, extensions=[lambda: 7])

    stream = await schema.stream("{ hello }", operation_name=operation_name)
    frames = [frame async for frame in stream]

    assert len(frames) == 1
    assert frames[0].data is None
    assert [error.extensions for error in frames[0].errors] == [
        {"code": SCHEMA_CONFIGURATION_ERROR_CODE},
    ]


class _OneShotPolicy:
    """A transport policy that can be traversed exactly once, and counts it.

    ``allowed_operation_types`` is annotated ``Iterable[OperationType]`` on
    every public entry point, so a generator-shaped policy is a value the API
    accepts and a healthy operation consumes once. The traversal count is what
    says the refusal did not become a second consumer of it.
    """

    def __init__(self, *operation_types: OperationType) -> None:
        self._operation_types = operation_types
        self.traversals = 0

    def __iter__(self):
        self.traversals += 1
        if self.traversals > 1:
            raise AssertionError("the transport policy was traversed twice")
        return iter(self._operation_types)


class _HostileBoolPolicy:
    """A reusable policy whose only oddity is a ``__bool__`` that must not run.

    Emptiness is a question about a consumer container, and asking it runs
    consumer code on the request path of a schema whose configuration is
    already broken.
    """

    def __init__(self, *operation_types: OperationType) -> None:
        self._operation_types = operation_types

    def __iter__(self):
        return iter(self._operation_types)

    def __bool__(self):
        raise AssertionError("the transport policy was truth-tested")


def test_a_refused_schema_answers_a_one_shot_transport_policy_synchronously():
    """The refusal reads the caller's policy once, so upstream still reads it too.

    ``execute_sync`` settles the operation type from the policy AFTER the parse
    stage, out of the same object the caller passed. A refusal that searched
    that object for a substitute document would leave upstream an exhausted
    iterable and turn "queries are allowed" into "this operation type is
    forbidden" - an error about the request, raised out of the API, in place of
    the published statement about the schema.
    """
    schema = DjangoSchema(query=DummyQuery, extensions=[lambda: 7])

    result = schema.execute_sync(
        "{ hello }",
        allowed_operation_types=_OneShotPolicy(OperationType.QUERY),
    )

    assert result.data is None
    assert [error.extensions for error in result.errors] == [
        {"code": SCHEMA_CONFIGURATION_ERROR_CODE},
    ]


@pytest.mark.asyncio
async def test_a_refused_schema_answers_a_one_shot_transport_policy_when_awaited():
    """The asynchronous API reads the same snapshot, and raises out of nothing."""
    schema = DjangoSchema(query=DummyQuery, extensions=[lambda: 7])

    result = await schema.execute(
        "{ hello }",
        allowed_operation_types=_OneShotPolicy(OperationType.QUERY),
    )

    assert result.data is None
    assert [error.extensions for error in result.errors] == [
        {"code": SCHEMA_CONFIGURATION_ERROR_CODE},
    ]


@_SKIP_WITHOUT_STREAM
@pytest.mark.asyncio
async def test_a_refused_schema_streams_a_refusal_under_a_one_shot_transport_policy():
    """The stream is where an exhausted policy was quietest.

    Upstream renders its own "queries are not allowed" into the first frame
    with no extensions at all, so a transport saw a well-formed error frame
    carrying a different story than the schema was telling.
    """
    schema = DjangoSchema(query=DummyQuery, extensions=[lambda: 7])

    stream = await schema.stream(
        "{ hello }",
        allowed_operation_types=_OneShotPolicy(OperationType.QUERY),
    )
    frames = [frame async for frame in stream]

    assert len(frames) == 1
    assert frames[0].data is None
    assert [error.extensions for error in frames[0].errors] == [
        {"code": SCHEMA_CONFIGURATION_ERROR_CODE},
    ]


@pytest.mark.parametrize(
    ("allowed", "expected"),
    [
        ((OperationType.QUERY,), "{\n  __typename\n}"),
        ((OperationType.MUTATION,), "mutation {\n  __typename\n}"),
        ((OperationType.SUBSCRIPTION,), "subscription {\n  __typename\n}"),
    ],
    ids=["query", "mutation", "subscription"],
)
def test_the_substitute_document_is_selected_from_a_one_shot_policy_too(allowed, expected):
    """Selection reads the snapshot, so it is not accidentally query-only.

    A mutation or subscription transport that arrived with a one-shot policy
    gets the substitute of its own type, and the fallback that would have hidden
    a broken selection behind a query document never runs.
    """
    schema = DjangoSchema(query=DummyQuery, extensions=[lambda: 7])
    context = StrawberryExecutionContext(
        query="{ hello }",
        schema=schema,
        allowed_operations=_OneShotPolicy(*allowed),
    )

    _refuse_operation_document(context)

    assert print_ast(context.graphql_document) == expected


def test_a_refused_request_snapshots_the_transport_policy_exactly_once():
    """One traversal, and what upstream reads back is an exact built-in tuple.

    The snapshot is the whole fix: package selection and upstream authorization
    have to read one immutable fact, so the materialized value is put back on
    the execution context rather than kept beside the caller's object. An exact
    ``tuple`` is asserted rather than an equal sequence, because a consumer type
    that merely compares equal is the input this replaces.
    """
    schema = DjangoSchema(query=DummyQuery, extensions=[lambda: 7])
    policy = _OneShotPolicy(OperationType.QUERY)
    context = StrawberryExecutionContext(
        query="{ hello }",
        schema=schema,
        allowed_operations=policy,
    )

    _refuse_operation_document(context)

    assert policy.traversals == 1
    assert type(context.allowed_operations) is tuple
    assert context.allowed_operations == (OperationType.QUERY,)


def test_a_refused_request_never_asks_a_transport_policy_whether_it_is_empty():
    """Emptiness is consumer code, and the refusal path is the wrong place to run it.

    The same posture the accepted-entry reader takes one function away: a
    container supplied by a consumer is normalized by being read, never by being
    truth-tested.
    """
    schema = DjangoSchema(query=DummyQuery, extensions=[lambda: 7])

    result = schema.execute_sync(
        "{ hello }",
        allowed_operation_types=_HostileBoolPolicy(OperationType.QUERY),
    )

    assert result.data is None
    assert [error.extensions for error in result.errors] == [
        {"code": SCHEMA_CONFIGURATION_ERROR_CODE},
    ]


@pytest.mark.parametrize(
    "schema_factory",
    [
        lambda: DjangoSchema(query=DummyQuery),
        lambda: DjangoSchema(query=DummyQuery, extensions=[lambda: 7]),
    ],
    ids=["healthy", "refused"],
)
def test_a_transport_policy_that_allows_nothing_stays_a_policy_that_allows_nothing(schema_factory):
    """A refusal owns what the caller supplied; it never widens it.

    A transport that allows no operation type is a deployment decision, and
    upstream's own answer to it is the right one on both schemas. Appending a
    default, substituting the full set, or swallowing the refusal would make a
    broken configuration the one shape that accepts what the transport forbids.
    """
    schema = schema_factory()

    with pytest.raises(InvalidOperationTypeError):
        schema.execute_sync("{ hello }", allowed_operation_types=_OneShotPolicy())


def test_a_refused_request_keeps_the_text_it_arrived_with_and_selects_by_nothing():
    """What arrived stays readable; what upstream reads is the package's own.

    A transport that logs the document it received still has it. The pair
    upstream parses and selects an operation from is replaced wholesale, so
    neither the request's text nor the name it asked for can reach the parser,
    the selector, validation, or execution again.
    """
    schema = DjangoSchema(query=DummyQuery, extensions=[lambda: 7])
    context = StrawberryExecutionContext(
        query="{ hello }",
        schema=schema,
        allowed_operations=(OperationType.QUERY,),
        provided_operation_name="bad-name",
    )

    _refuse_operation_document(context)

    assert context.query == "{ hello }"
    assert context.operation_name is None
    assert print_ast(context.graphql_document) == "{\n  __typename\n}"


@pytest.mark.parametrize(
    ("allowed", "expected"),
    [
        ((OperationType.QUERY,), "{\n  __typename\n}"),
        ((OperationType.MUTATION,), "mutation {\n  __typename\n}"),
        ((OperationType.SUBSCRIPTION,), "subscription {\n  __typename\n}"),
        ((), "{\n  __typename\n}"),
    ],
    ids=[
        "query",
        "mutation",
        "subscription",
        "nothing-allowed",
    ],
)
def test_the_substitute_document_is_of_a_type_the_transport_allows(allowed, expected):
    """Upstream refuses a type the caller did not allow before it can read the refusal.

    A subscription transport allows exactly one type, so a refusal answered with
    a query would be replaced by an "operation type not allowed" error that says
    nothing about the configuration. The documents are the package's own
    constants, so the substitution costs no parse.
    """
    schema = DjangoSchema(query=DummyQuery, extensions=[lambda: 7])
    context = StrawberryExecutionContext(
        query="{ hello }",
        schema=schema,
        allowed_operations=allowed,
    )

    _refuse_operation_document(context)

    assert print_ast(context.graphql_document) == expected


@_SKIP_WITHOUT_STREAM
@pytest.mark.asyncio
async def test_a_refused_schema_answers_a_streamed_operation_with_one_frame():
    """The streaming transport gets the refusal as a frame, not as an exception.

    An exception out of a hook leaves a streamed operation with no frame at all,
    which is why the refusal is published rather than raised - and the stream's
    own resume wrapper has to carry it the same way every other frame is
    carried.
    """
    schema = DjangoSchema(query=DummyQuery, extensions=[lambda: 7])

    stream = await schema.stream("{ hello }")
    frames = [frame async for frame in stream]

    assert len(frames) == 1
    assert frames[0].data is None
    assert [error.extensions for error in frames[0].errors] == [
        {"code": SCHEMA_CONFIGURATION_ERROR_CODE},
    ]


class _HostileReprError(Exception):
    """A consumer exception whose display is as much consumer code as the factory."""

    def __repr__(self):
        """Raise while the containment result is being built."""
        raise RuntimeError("repr bomb")

    def __str__(self):
        """Raise on the other rendering path too."""
        raise RuntimeError("str bomb")


class _HostileArg:
    """An exception argument whose own representation raises."""

    def __repr__(self):
        """Raise while the exception carrying this is being rendered."""
        raise RuntimeError("arg bomb")


class _HostileTypeError(Exception):
    """A consumer exception whose type metadata cannot be read either."""


class _HostileTypeMeta(type):
    @property
    def __name__(cls):
        """Raise when the safe renderer asks the type for its name."""
        raise RuntimeError("name bomb")


class _HostileNameError(Exception, metaclass=_HostileTypeMeta):
    """A consumer exception whose class name raises while it is being rendered."""


@pytest.mark.parametrize(
    "raised",
    [
        RuntimeError("factory sentinel"),
        _HostileReprError("secret"),
        _HostileTypeError(_HostileArg()),
        _HostileNameError("secret"),
    ],
    ids=[
        "ordinary-exception",
        "raising-repr-and-str",
        "raising-argument-representation",
        "raising-type-name",
    ],
)
def test_a_factory_exception_cannot_escape_while_the_refusal_is_being_built(raised):
    """The diagnostic is assembled from a consumer exception, so it is rendered safely.

    Interpolating the exception into the private reason runs its ``__repr__``
    while the containment result is being built - and that is consumer code,
    which may raise and replace the refusal with the very exception the refusal
    exists to keep off the wire. The wire message is the constant either way.
    """

    def factory():
        raise raised

    schema = DjangoSchema(query=DummyQuery, extensions=[factory])

    _assert_configuration_refusal(schema.execute_sync("{ hello }"))


def test_a_refused_chain_runs_no_consumer_hook_and_no_resolver():
    """Refusing means nothing runs, which is the whole difference from reporting.

    What could not be established is what a consumer entry would enforce, so
    running one anyway - or running the resolver it was installed to bound -
    would be enforcing a configuration this schema never accepted.
    """
    seen: list[str] = []

    class _Loud(SchemaExtension):
        """A consumer entry that records every hook it is given."""

        def on_operation(self):
            """Record that a consumer hook ran, which a refusal must not allow."""
            seen.append("on_operation")
            yield

    @strawberry.type
    class ResolverQuery:
        @strawberry.field
        def hello(self) -> str:
            """Record that the resolver ran, which a refusal must not allow."""
            seen.append("resolver")
            return "world"

    schema = DjangoSchema(query=ResolverQuery, extensions=[_Loud, lambda: 7])

    _assert_configuration_refusal(schema.execute_sync("{ hello }"))
    assert seen == []


class _UpstreamRunnerSchema(DjangoSchema):
    """A subclass that opts out of the package's runner, and of what depends on it.

    Both overrides are needed together. Every extension ``DjangoSchema`` installs
    reads its request through the operation state the package's runner binds, so
    a subclass that swapped only the runner would have stripped those extensions
    of their context while still running them; a subclass that meant to use
    upstream's machinery replaces both halves.
    """

    def create_extensions_runner(self, execution_context, extensions):
        """Build the plain upstream runner, as such a subclass may."""
        return SchemaExtensionsRunner(
            execution_context=execution_context,
            extensions=extensions,
        )

    def get_extensions(self, sync: bool = False):
        """Run no extension, so nothing in the operation needs the package's runner."""
        return []


@_SKIP_WITHOUT_STREAM
@pytest.mark.asyncio
async def test_a_stream_whose_runner_is_not_the_packages_is_handed_back_untouched():
    """The resume wrapper binds what a ``DjangoExtensionsRunner`` owns, and nothing else.

    A subclass may build its own runner, and upstream's holds no per-task state:
    wrapping it would put a resume hook around frames whose producer has nothing
    to rebind, so the stream is returned exactly as upstream built it.

    The package's own schema is the other half of the row. Without it, "this one
    is not wrapped" would read the same whether the check discriminates or the
    wrapper had stopped being applied to anything at all.
    """
    foreign = _UpstreamRunnerSchema(query=DummyQuery)
    plain = DjangoSchema(query=DummyQuery)

    foreign_stream = await foreign.stream("{ hello }")
    plain_stream = await plain.stream("{ hello }")
    try:
        assert not isinstance(foreign_stream, _ResumedStream)
        assert isinstance(plain_stream, _ResumedStream)

        assert [frame.errors async for frame in foreign_stream] == [None]
    finally:
        await plain_stream.aclose()
