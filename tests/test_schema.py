"""Permanent behavioral tests for django_strawberry_framework.schema."""

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
from graphql import ExecutionContext, GraphQLError
from strawberry.extensions.base_extension import SchemaExtension

from django_strawberry_framework.error_policy import ErrorPolicy
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.extensions.error_policy import DjangoErrorPolicyExtension
from django_strawberry_framework.extensions.resource_policy import DjangoResourcePolicyExtension
from django_strawberry_framework.resource_policy import ResourcePolicy, bounded_rows
from django_strawberry_framework.schema import (
    _SCHEMA_ENFORCEMENT,
    _SCHEMA_EXTENSIONS,
    SCHEMA_CONFIGURATION_ERROR_CODE,
    DjangoMutationExecutionContext,
    DjangoSchema,
    _async_mutation_lock,
    _AsyncAliasLock,
    _extension_entry_matches,
    _is_extension,
    _with_error_policy_extension,
    _with_resource_policy_extension,
)
from django_strawberry_framework.utils.querysets import run_in_one_sync_boundary


class CustomErrorPolicyExtension(DjangoErrorPolicyExtension):
    pass


class CustomResourcePolicyExtension(DjangoResourcePolicyExtension):
    pass


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
    assert len(schema_none.extensions) >= 2

    schema_tuple = DjangoSchema(query=DummyQuery, extensions=(CustomErrorPolicyExtension,))
    assert any(
        isinstance(ext, type) and issubclass(ext, CustomErrorPolicyExtension)
        for ext in schema_tuple.extensions
    )

    def ext_gen():
        yield CustomErrorPolicyExtension

    schema_gen = DjangoSchema(query=DummyQuery, extensions=ext_gen())
    assert any(
        isinstance(ext, type) and issubclass(ext, CustomErrorPolicyExtension)
        for ext in schema_gen.extensions
    )


def test_schema_init_with_none_execution_context_class_falls_back():
    schema = DjangoSchema(query=DummyQuery, execution_context_class=None)
    assert schema.execution_context_class is DjangoMutationExecutionContext


def test_with_resource_policy_extension_shapes():
    """The append and its flag: the flag says whether the automatic entry was added."""
    assert _with_resource_policy_extension([]) == ([DjangoResourcePolicyExtension], True)
    assert _with_resource_policy_extension(None) == ([DjangoResourcePolicyExtension], True)
    assert _with_resource_policy_extension([DjangoResourcePolicyExtension]) == (
        [DjangoResourcePolicyExtension],
        False,
    )
    assert _with_resource_policy_extension([CustomResourcePolicyExtension]) == (
        [CustomResourcePolicyExtension],
        False,
    )


def test_with_error_policy_extension_shapes():
    assert _with_error_policy_extension([]) == [DjangoErrorPolicyExtension]
    assert _with_error_policy_extension([DjangoErrorPolicyExtension]) == [
        DjangoErrorPolicyExtension,
    ]
    assert _with_error_policy_extension([CustomErrorPolicyExtension]) == [
        CustomErrorPolicyExtension,
    ]


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

    class BrokenMeta(type):
        def __subclasscheck__(cls, subclass):
            raise TypeError("Hostile metaclass check")

    class BrokenClass(metaclass=BrokenMeta):
        pass

    assert not _extension_entry_matches(DjangoErrorPolicyExtension, BrokenClass)
    assert not _extension_entry_matches(DjangoErrorPolicyExtension(), BrokenClass)


def test_get_extensions_sync_and_async():
    schema = DjangoSchema(query=DummyQuery)
    sync_exts = schema.get_extensions(sync=True)
    async_exts = schema.get_extensions(sync=False)
    assert len(sync_exts) >= 2
    assert len(async_exts) >= 2


def test_get_extensions_with_custom_factory_dedup():
    def error_factory():
        return DjangoErrorPolicyExtension()

    schema = DjangoSchema(query=DummyQuery, extensions=[error_factory])
    exts = schema.get_extensions(sync=True)
    error_exts = [e for e in exts if isinstance(e, DjangoErrorPolicyExtension)]
    assert len(error_exts) == 1


def test_get_extensions_when_explicitly_passed_class():
    schema = DjangoSchema(query=DummyQuery, extensions=[CustomErrorPolicyExtension])
    exts = schema.get_extensions(sync=True)
    error_exts = [e for e in exts if isinstance(e, DjangoErrorPolicyExtension)]
    assert len(error_exts) == 1
    assert isinstance(error_exts[0], CustomErrorPolicyExtension)


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
@pytest.mark.django_db
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


def test_get_extensions_with_a_custom_resource_factory_dedups():
    """A factory-produced resource extension is the operation's one armed budget.

    A factory cannot be identified at construction without calling it, so the
    automatic entry is appended beside it and dropped here. Left in, it would arm
    last and answer every resolve-time bound with the package defaults while the
    consumer's own policy went on charging the document.
    """

    def resource_factory():
        return CustomResourcePolicyExtension(policy=ResourcePolicy(max_list_rows=1))

    schema = DjangoSchema(query=DummyQuery, extensions=[resource_factory])
    resolved = schema.get_extensions(sync=True)
    resource_exts = [e for e in resolved if isinstance(e, DjangoResourcePolicyExtension)]

    assert len(resource_exts) == 1
    assert isinstance(resource_exts[0], CustomResourcePolicyExtension)


def test_a_factory_configured_bound_is_the_one_a_request_is_held_to():
    """The behavioral half: a second armed budget answers the resolve-time bounds.

    The automatic entry is appended after the consumer's, so it arms last and
    ``policy_from_info`` answers with the package defaults - the consumer's own
    policy goes on charging the document while the rows it meant to bound are
    unbounded.
    """

    @strawberry.type
    class _RowQuery:
        @strawberry.field
        def rows(self, info: strawberry.Info) -> list[str]:
            return list(bounded_rows(["a", "b", "c"], info, None))

    def resource_factory():
        return DjangoResourcePolicyExtension(policy=ResourcePolicy(max_list_rows=1))

    schema = DjangoSchema(query=_RowQuery, extensions=[resource_factory])
    result = schema.execute_sync("{ rows }")

    assert result.errors is None, result.errors
    assert result.data == {"rows": ["a"]}


def test_get_extensions_leaves_an_unrelated_factory_its_automatic_resource_extension():
    """The control: a factory producing something else still gets the package's own entry."""

    def unrelated_factory():
        return DjangoErrorPolicyExtension()

    schema = DjangoSchema(query=DummyQuery, extensions=[unrelated_factory])
    resolved = schema.get_extensions(sync=True)
    resource_exts = [e for e in resolved if isinstance(e, DjangoResourcePolicyExtension)]

    assert len(resource_exts) == 1


def test_get_extensions_keeps_an_explicit_resource_class_alone():
    """A class entry suppresses the append at construction, so nothing is dropped here."""
    schema = DjangoSchema(query=DummyQuery, extensions=[CustomResourcePolicyExtension])
    resolved = schema.get_extensions(sync=True)
    resource_exts = [e for e in resolved if isinstance(e, DjangoResourcePolicyExtension)]

    assert len(resource_exts) == 1
    assert isinstance(resource_exts[0], CustomResourcePolicyExtension)


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


def test_a_resolver_cannot_nominate_a_wider_policy_by_replacing_the_extension_list():
    """Presence of an enforcement extension is not evidence that it was configured.

    A replacement list can carry an ordinary ``DjangoResourcePolicyExtension``
    of its own with a wider policy: deduplication and presence checks both
    succeed on it, and the accepted bound is gone for the life of the process.
    What enforces an operation is what the schema was constructed with, so the
    assignment is refused where it is made rather than reconciled afterwards.
    The refusal reaches the client as any other unexpected exception out of a
    resolver does - masked, with a correlation id - so what the row reads is
    that the operation failed and that the next one is still held to the
    accepted bound.
    """

    @strawberry.type
    class _Query:
        @strawberry.field
        def rows(self, info: strawberry.Info) -> list[str]:
            return list(bounded_rows(["a", "b", "c"], info, None))

        @strawberry.field
        def widen(self, info: strawberry.Info) -> int:
            info.schema.extensions = [
                lambda: DjangoResourcePolicyExtension(
                    policy=ResourcePolicy(max_list_rows=999),
                ),
            ]
            return 1

    schema = DjangoSchema(query=_Query, resource_policy=ResourcePolicy(max_list_rows=1))
    assert schema.execute_sync("{ rows }").data == {"rows": ["a"]}

    attacked = schema.execute_sync("{ widen }")
    assert attacked.errors is not None
    assert "correlationId" in attacked.errors[0].extensions

    assert schema.execute_sync("{ rows }").data == {"rows": ["a"]}


@strawberry.type
class _BoundedRowQuery:
    """One field whose rows are bounded by whatever policy the operation armed."""

    @strawberry.field
    def rows(self, info: strawberry.Info) -> list[str]:
        return list(bounded_rows(["a", "b", "c"], info, None))


def _assert_entry_survives_a_replacement_attempt(schema):
    """One accepted configuration keeps enforcing, and keeps exactly one entry."""
    assert schema.execute_sync("{ rows }").data == {"rows": ["a"]}

    with pytest.raises(ConfigurationError):
        schema.extensions = []

    assert schema.execute_sync("{ rows }").data == {"rows": ["a"]}
    resolved = schema.get_extensions(sync=True)
    assert sum(isinstance(e, DjangoResourcePolicyExtension) for e in resolved) == 1


@pytest.mark.parametrize(
    "entry",
    [
        DjangoResourcePolicyExtension,
        lambda: DjangoResourcePolicyExtension(policy=ResourcePolicy(max_list_rows=1)),
    ],
    ids=["class", "factory"],
)
def test_an_accepted_extension_entry_still_enforces_after_a_replacement_attempt(entry):
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


def test_an_accepted_extension_instance_still_enforces_after_a_replacement_attempt():
    """The third configuration spelling, which Strawberry itself deprecates.

    An instance entry shares one set of counters across every request, so
    Strawberry warns on it; the package still accepts it as configuration, and
    accepted configuration is what enforces.
    """
    with pytest.warns(DeprecationWarning):
        schema = DjangoSchema(
            query=_BoundedRowQuery,
            extensions=[DjangoResourcePolicyExtension(policy=ResourcePolicy(max_list_rows=1))],
            resource_policy=ResourcePolicy(max_list_rows=1),
        )
    _assert_entry_survives_a_replacement_attempt(schema)


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
        """Build this schema's resource-policy extension, fresh per operation."""
        return DjangoResourcePolicyExtension()

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
            lambda: DjangoSchema(query=DummyQuery, extensions=[DjangoResourcePolicyExtension()]),
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
    is also the entry whose policy this package never sees: the factory is
    called once per operation, and what it returns is the consumer's.
    """

    def narrow_extension():
        return DjangoResourcePolicyExtension(policy=ResourcePolicy(max_list_rows=rows))

    return DjangoSchema(
        query=DummyQuery,
        resource_policy=ResourcePolicy(max_list_rows=rows),
        extensions=[narrow_extension],
    )


def _widening_factory():
    """An extension entry a resolver would rather the next operation resolved."""
    return DjangoResourcePolicyExtension(policy=ResourcePolicy(max_list_rows=999))


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
    schema = DjangoSchema(query=_RowQuery, resource_policy=ResourcePolicy(max_list_rows=1))
    assert schema.execute_sync("{ rows }").data == {"rows": ["a"]}

    attack(schema)

    assert schema.extensions == (DjangoErrorPolicyExtension, DjangoResourcePolicyExtension)
    assert schema.execute_sync("{ rows }").data == {"rows": ["a"]}
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
    """The accepted entries are the only record of what a consumer entry declared.

    A factory's policy was never seen by this package at all, so there is
    nothing to fall back to that is not wider than what the deployment chose.
    The operation is refused, and the refusal is published rather than raised so
    every transport renders it.
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
    assert isinstance(resolved[0], DjangoErrorPolicyExtension)
    assert not any(isinstance(entry, DjangoResourcePolicyExtension) for entry in resolved)


def test_a_refused_schema_does_not_begin_executing_either():
    """The refusal is restated where execution starts, for a path that got that far."""
    schema = _schema_holding_an_unnamed_entry()
    schema.__dict__.pop("_django_extensions")
    refusal = schema.get_extensions(sync=True)[-1]

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
        return DjangoResourcePolicyExtension(policy=ResourcePolicy(max_list_rows=1))


class _InertExtension(SchemaExtension):
    """A module-level entry that enforces nothing and is weak-referenceable.

    The mixed-entry rows need one entry of each memory layout without a second
    enforcement authority in the list, which is a configuration this schema
    refuses on its own terms.
    """


class _WeakReferenceableFactory:
    """The control: the same factory, with the layout a weak reference can be taken of."""

    def __call__(self):
        return DjangoResourcePolicyExtension(policy=ResourcePolicy(max_list_rows=1))


class _WideningSlottedFactory:
    """The entry a resolver would rather the schema resolved, in the same layout."""

    __slots__ = ()

    def __call__(self):
        return DjangoResourcePolicyExtension(policy=ResourcePolicy(max_list_rows=999))


@pytest.mark.parametrize(
    "factory",
    [_SlottedFactory, _WeakReferenceableFactory],
    ids=["slotted-callable", "weak-referenceable-control"],
)
def test_a_slotted_callable_factory_is_accepted_and_enforces(factory):
    """A callable factory works whatever its object layout is.

    Strawberry accepts either one, so a schema that refused the slotted form
    would be refusing a configuration for a reason that has nothing to do with
    what runs the operation. Both build the extension per operation and both
    enforce the bound they carry.
    """
    schema = DjangoSchema(
        query=_RowQuery,
        resource_policy=ResourcePolicy(max_list_rows=3),
        extensions=[factory()],
    )

    # The schema's own policy would pass all three rows; the entry's narrower
    # one is what the operation is actually bounded by.
    assert schema.execute_sync("{ rows }").data == {"rows": ["a"]}


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
    resolved against whatever was put there. It is also the entry carrying this
    schema's resource bound: the other one enforces nothing, so the list has one
    authority the way an accepted configuration has to.
    """
    schema = DjangoSchema(
        query=_RowQuery,
        resource_policy=ResourcePolicy(max_list_rows=1),
        extensions=[_InertExtension, _SlottedFactory()],
    )
    assert schema.execute_sync("{ rows }").data == {"rows": ["a"]}

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
        extensions=[DjangoResourcePolicyExtension],
    )
    assert schema.execute_sync("{ rows }").data == {"rows": ["a"]}

    schema.__dict__.update(_django_extensions=(_widening_factory,))
    gc.collect()

    assert schema.extensions == (DjangoErrorPolicyExtension, DjangoResourcePolicyExtension)
    assert schema.execute_sync("{ rows }").data == {"rows": ["a"]}


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

    What the row reads is the bound: the accepted factory declared one row, the
    replacement would pass three, and the schema's own policy would pass three
    as well - so an admitted replacement is visible in the data.
    """
    accepted = _SlottedFactory()
    replacement = _WideningSlottedFactory()
    schema = DjangoSchema(
        query=_RowQuery,
        resource_policy=ResourcePolicy(max_list_rows=3),
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


def test_rebuilding_the_box_a_slotted_entry_is_answered_through_changes_nothing():
    """The second constructor call, which is not an attribute write and is refused anyway.

    ``__init__`` on an already-built binding is the one spelling that raises
    nothing, so the assertion is the binding itself rather than an exception.
    """
    accepted = _SlottedFactory()
    schema = DjangoSchema(
        query=_RowQuery,
        resource_policy=ResourcePolicy(max_list_rows=3),
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


def test_a_retained_policy_argument_cannot_widen_a_later_request():
    """The observable half: a bound settled at construction stays settled."""

    @strawberry.type
    class _Query:
        @strawberry.field
        def rows(self, info: strawberry.Info) -> list[str]:
            return list(bounded_rows(["a", "b", "c"], info, None))

    policy = ResourcePolicy(max_list_rows=1)
    schema = DjangoSchema(query=_Query, resource_policy=policy)
    assert schema.execute_sync("{ rows }").data == {"rows": ["a"]}

    policy.__dict__["max_list_rows"] = 999

    assert schema.execute_sync("{ rows }").data == {"rows": ["a"]}


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


class _LyingExtension:
    """An object that answers ``__class__`` with an extension class it is not."""

    @property
    def __class__(self):
        """Claim to be the masking extension, which ``isinstance`` would believe."""
        return DjangoErrorPolicyExtension


class _SlottedErrorFactory:
    """A valid error-policy factory in the layout that takes no weak reference."""

    __slots__ = ()

    def __call__(self):
        return DjangoErrorPolicyExtension()


def _narrow_resource_factory():
    """A factory producing a resource extension with a bound of its own."""
    return DjangoResourcePolicyExtension(policy=ResourcePolicy(max_aliases=1))


def _wide_resource_factory():
    """The same, with a bound wide enough to admit what the narrow one refuses."""
    return DjangoResourcePolicyExtension(policy=ResourcePolicy(max_aliases=999))


_SHARED_ERROR_EXTENSION = DjangoErrorPolicyExtension()


def _first_error_factory():
    """A factory producing a masking extension for the operation."""
    return DjangoErrorPolicyExtension()


def _second_error_factory():
    """A second one, so two masking authorities resolve from opaque entries."""
    return DjangoErrorPolicyExtension()


def _singleton_error_factory():
    """The documented shared-instance spelling: one object, returned every time."""
    return _SHARED_ERROR_EXTENSION


def _assert_configuration_refusal(result):
    """The operation ran nothing and said so with the stable code."""
    assert result.data is None
    assert [error.extensions for error in result.errors] == [
        {"code": SCHEMA_CONFIGURATION_ERROR_CODE},
    ]


@pytest.mark.parametrize(
    "entries",
    [
        [DjangoResourcePolicyExtension, CustomResourcePolicyExtension],
        [CustomResourcePolicyExtension, DjangoResourcePolicyExtension],
        [DjangoResourcePolicyExtension, CustomResourcePolicyExtension()],
        [DjangoErrorPolicyExtension, DjangoErrorPolicyExtension],
        [DjangoErrorPolicyExtension(), DjangoErrorPolicyExtension],
    ],
    ids=[
        "resource-classes",
        "resource-classes-reversed",
        "resource-class-and-instance",
        "error-classes",
        "error-instance-and-class",
    ],
)
def test_two_entries_of_one_enforcement_kind_are_refused_at_construction(entries):
    """An entry that names its type is one the deployment can be told about at startup.

    Two of a kind is not a duplicate to tidy: each arms its own scope over the
    whole operation and the last one armed answers every bound, mask and
    deadline check, so the order they were listed in would decide what the
    request is held to. Neither first nor last is a rule anyone can have meant,
    so the schema is refused rather than served.
    """
    with pytest.raises(ConfigurationError):
        DjangoSchema(query=DummyQuery, extensions=entries)


@pytest.mark.parametrize(
    "entries",
    [
        [_narrow_resource_factory, _wide_resource_factory],
        [_wide_resource_factory, _narrow_resource_factory],
        [_first_error_factory, _second_error_factory],
        [_second_error_factory, _first_error_factory],
    ],
    ids=[
        "resource-narrow-then-wide",
        "resource-wide-then-narrow",
        "error-first-then-second",
        "error-second-then-first",
    ],
)
def test_two_opaque_factories_of_one_kind_refuse_the_operation(entries):
    """A factory is opaque until it runs, so the same refusal has to be made later.

    Construction cannot classify these without calling them, which is the one
    thing a per-operation factory must not have done to it. Resolution is where
    both become visible, and both orders refuse identically - the alternative is
    a schema whose enforcement is selected by list position.
    """
    schema = DjangoSchema(query=DummyQuery, extensions=entries)

    _assert_configuration_refusal(schema.execute_sync("{ hello }"))


@pytest.mark.parametrize(
    "entry",
    [
        lambda: (_ for _ in ()).throw(RuntimeError("factory sentinel")),
        lambda: 7,
        lambda: object(),
        lambda: DjangoErrorPolicyExtension,
        lambda: _LyingExtension(),
    ],
    ids=[
        "factory-raises",
        "returns-an-integer",
        "returns-a-plain-object",
        "returns-the-class",
        "returns-a-lying-class",
    ],
)
def test_a_factory_that_does_not_produce_an_extension_refuses_the_operation(entry):
    """Upstream assigns ``execution_context`` on whatever a factory returned.

    That loop runs before the runner exists and outside the block upstream turns
    into a response, so an integer, a bare object or a class produces an
    ``AttributeError`` the package's own error policy never sees, and a raising
    factory puts the consumer's own exception text on the wire. The resolved
    member is typed here instead, by its type rather than by what it claims, and
    the operation is refused with the stable configuration code.
    """
    schema = DjangoSchema(query=DummyQuery, extensions=[entry])

    _assert_configuration_refusal(schema.execute_sync("{ hello }"))


@pytest.mark.parametrize(
    "entry",
    [
        _SlottedErrorFactory(),
        DjangoErrorPolicyExtension,
        _first_error_factory,
        _singleton_error_factory,
    ],
    ids=[
        "slotted-factory",
        "bound-method",
        "fresh-factory",
        "singleton-factory",
    ],
)
def test_every_supported_entry_spelling_still_resolves_into_one_chain(entry):
    """The controls that keep the refusals honest: all four spellings still run.

    A memory layout that takes no weak reference, a class, a module-level
    function and a factory handing back one shared object are configurations
    rather than defects, and each resolves into exactly one masking authority
    beside the package's own resource extension.
    """
    schema = DjangoSchema(query=DummyQuery, extensions=[entry])
    resolved = schema.get_extensions(sync=True)

    assert schema.execute_sync("{ hello }").data == {"hello": "world"}
    assert sum(_is_extension(e, DjangoErrorPolicyExtension) for e in resolved) == 1
    assert sum(_is_extension(e, DjangoResourcePolicyExtension) for e in resolved) == 1


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
