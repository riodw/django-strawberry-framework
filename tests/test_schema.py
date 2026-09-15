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
from graphql import ExecutionContext

from django_strawberry_framework.error_policy import ErrorPolicy
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.extensions.error_policy import DjangoErrorPolicyExtension
from django_strawberry_framework.extensions.resource_policy import DjangoResourcePolicyExtension
from django_strawberry_framework.resource_policy import ResourcePolicy, bounded_rows
from django_strawberry_framework.schema import (
    _SCHEMA_ENFORCEMENT,
    DjangoMutationExecutionContext,
    DjangoSchema,
    _async_mutation_lock,
    _AsyncAliasLock,
    _extension_entry_matches,
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
    assert "settled when the schema is constructed" in attacked.errors[0].message

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


def test_a_forged_enforcement_record_still_leaves_the_operation_enforced():
    """The record a schema carries is read back only through what accepted it.

    Writing the attribute it is held under is a write ``info.schema`` puts in
    reach of every resolver, and a forged record would otherwise nominate its
    own policies. The forgery is not the accepted one, so what answers is the
    fail-closed default - and the entries that enforce it are put back rather
    than taken from a configuration that can no longer be read.
    """
    schema = DjangoSchema(query=DummyQuery, resource_policy=ResourcePolicy(max_list_rows=1))
    assert schema.resource_policy.max_list_rows == 1

    schema.__dict__["_django_enforcement"] = SimpleNamespace(
        resource_policy=ResourcePolicy(max_list_rows=999),
        error_policy=ErrorPolicy(),
        auto_resource_extension=False,
        auto_error_extension=False,
        extensions=(),
    )

    assert schema.resource_policy == ResourcePolicy()
    assert schema.extensions == ()
    resolved = schema.get_extensions(sync=True)
    assert sum(isinstance(entry, DjangoResourcePolicyExtension) for entry in resolved) == 1
    assert sum(isinstance(entry, DjangoErrorPolicyExtension) for entry in resolved) == 1
    assert isinstance(resolved[0], DjangoErrorPolicyExtension)
    assert isinstance(resolved[-1], DjangoResourcePolicyExtension)


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
