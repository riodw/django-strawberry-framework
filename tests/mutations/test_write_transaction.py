"""The 0.0.14 mutation write-transaction contract (``DjangoSchema`` + ``utils/write_transaction.py``).

System-under-test is the completion-spanning mutation transaction and its
supporting seams:

- ``schema.py::DjangoMutationExecutionContext`` - sync AND async execution hold
  each generated top-level mutation field's ``transaction.atomic`` open through
  GraphQL value completion, roll back on any new execution error, and commit
  clean completions (the live ``/graphql/`` HTTP acceptance is
  ``examples/fakeshop/test_query/test_mutation_atomicity.py``; this module owns
  the async surface and the failure shapes a WSGI request cannot drive);
- the plain-``strawberry.Schema`` refusal (``require_managed_write`` fires
  before any database work);
- the disappearing-row ``conflict`` contract (``force_update=True`` on direct
  model updates, the zero-target-row delete, the missing post-write re-fetch)
  including the Django 5.2 untyped-``DatabaseError`` compat disambiguation;
- alias pinning: the fail-closed hook alias switch, the instance-sensitive
  router divergence check, and the pinned relation checks;
- the strict-boolean authorization contract (``check_permission`` /
  ``has_permission`` / ``user.has_perm`` must return actual bools).

Rows are seeded inline over the real products models (the package-test idiom);
the sharded live-HTTP alias tests are ``examples/fakeshop/test_query/test_multi_db.py``.
"""

from __future__ import annotations

import contextlib
import itertools

import pytest
import strawberry
from apps.products import models as product_models
from django.db import DatabaseError, IntegrityError, connections, transaction
from strawberry import relay

from django_strawberry_framework import (
    DjangoMutation,
    DjangoMutationField,
    DjangoOptimizerExtension,
    DjangoSchema,
    DjangoType,
    finalize_django_types,
)
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.registry import registry
from django_strawberry_framework.utils import write_transaction
from django_strawberry_framework.utils.write_transaction import (
    _enforce_read_only_barrier,
    check_instance_write_alias,
    conflict_error,
    forced_update_conflict_errors,
    not_updated_exceptions,
    pin_write_queryset,
    pipeline_write_phase,
    require_write_pipeline,
    resolve_write_alias,
    write_pipeline,
)


@pytest.fixture(autouse=True)
def _isolate_registry():
    registry.clear()
    yield
    registry.clear()


_category_name_counter = itertools.count(1)


def _category_name() -> str:
    return f"WTCat-{next(_category_name_counter)}"


class _AllowAll:
    """Authorize every write (these tests pin the transaction, not the auth seam)."""

    def has_permission(
        self,
        info,
        mutation,
        operation,
        data,
        instance=None,
    ):
        return True


@strawberry.type
class _Query:
    @strawberry.field
    def ping(self) -> int:
        return 1


def _declare_item_types(*, item_get_queryset=None):
    """Declare the Item/Category primaries (optionally with an Item visibility hook)."""

    class CategoryT(DjangoType, relay.Node):
        class Meta:
            model = product_models.Category
            # ``created_date`` is the completion-failure lever: a raw-SQL
            # corrupted date hydrates to None and fails the non-nullable field
            # at completion (the async rollback tests select it).
            fields = ("id", "name", "created_date")
            primary = True

    item_body: dict = {
        "Meta": type(
            "Meta",
            (),
            {"model": product_models.Item, "fields": ("id", "name", "category"), "primary": True},
        ),
    }
    if item_get_queryset is not None:
        item_body["get_queryset"] = item_get_queryset
    ItemT = type("ItemT", (DjangoType, relay.Node), item_body)
    return CategoryT, ItemT


def _declare_update_mutation(*, permission_classes=None, select_for_update=True):
    meta_attrs = {
        "model": product_models.Item,
        "operation": "update",
        "permission_classes": permission_classes
        if permission_classes is not None
        else [_AllowAll],
        "select_for_update": select_for_update,
    }
    return type("UpdateItem", (DjangoMutation,), {"Meta": type("Meta", (), meta_attrs)})


def _declare_delete_mutation(*, permission_classes=None, select_for_update=True):
    meta_attrs = {
        "model": product_models.Item,
        "operation": "delete",
        "permission_classes": permission_classes
        if permission_classes is not None
        else [_AllowAll],
        "select_for_update": select_for_update,
    }
    return type("DeleteItem", (DjangoMutation,), {"Meta": type("Meta", (), meta_attrs)})


def _mutation_schema(*mutations, schema_cls=DjangoSchema, extra_fields=None):
    body = {
        f"write{index}": DjangoMutationField(mutation_cls)
        for index, mutation_cls in enumerate(mutations)
    }
    if extra_fields:
        body.update(extra_fields)
    body["__annotations__"] = {}
    Mutation = strawberry.type(type("Mutation", (), body))
    finalize_django_types()
    return schema_cls(
        query=_Query,
        mutation=Mutation,
        extensions=[DjangoOptimizerExtension],
    )


def _item_gid(pk) -> str:
    return str(relay.GlobalID(type_name="products.item", node_id=str(pk)))


_UPDATE = (
    "mutation($id: ID!, $d: ItemPartialInput!){ write0(id:$id, data:$d){ "
    "node{ name } errors{ field messages } } }"
)
_DELETE = "mutation($id: ID!){ write0(id:$id){ node{ name } errors{ field messages } } }"


def _seed_item(name: str = "Seeded"):
    category = product_models.Category.objects.create(name=_category_name())
    return product_models.Item.objects.create(name=name, category=category)


# ===========================================================================
# The plain-Schema refusal (fail before any database work)
# ===========================================================================


@pytest.mark.django_db
def test_plain_strawberry_schema_refuses_generated_mutations_before_writing():
    """A generated mutation on a plain ``strawberry.Schema`` fails loudly, writing nothing."""
    _declare_item_types()
    UpdateItem = _declare_update_mutation()
    schema = _mutation_schema(UpdateItem, schema_cls=strawberry.Schema)
    item = _seed_item("Untouched")

    result = schema.execute_sync(
        _UPDATE,
        variable_values={"id": _item_gid(item.pk), "d": {"name": "Written"}},
    )

    assert result.errors is not None
    assert "DjangoSchema" in str(result.errors[0])
    item.refresh_from_db()
    assert item.name == "Untouched"


# ===========================================================================
# Async execution: the completion-spanning transaction (open/close in the worker)
# ===========================================================================


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_async_update_completion_failure_rolls_back():
    """Under ``await schema.execute`` a completion failure rolls the write back."""
    from asgiref.sync import sync_to_async

    def _hidden_after_write(cls, queryset, info, **kwargs):
        return queryset

    _declare_item_types()
    UpdateItem = _declare_update_mutation()
    schema = _mutation_schema(UpdateItem)
    item = await sync_to_async(_seed_item)("AsyncOriginal")

    # Corrupt the row's category date AFTER seeding, via raw SQL, so the
    # post-write re-fetch hydrates ``created_date`` to None and the non-nullable
    # ``createdDate`` fails at completion.
    def _corrupt():
        with connections["default"].cursor() as cursor:
            cursor.execute(
                "UPDATE products_category SET created_date = 'not-a-date' WHERE id = %s",
                (item.category_id,),
            )

    await sync_to_async(_corrupt)()

    query = (
        "mutation($id: ID!, $d: ItemPartialInput!){ write0(id:$id, data:$d){ "
        "node{ name category { createdDate } } errors{ field messages } } }"
    )
    result = await schema.execute(
        query,
        variable_values={"id": _item_gid(item.pk), "d": {"name": "AsyncWritten"}},
    )

    assert result.errors is not None  # the completion failure surfaced...
    name = await sync_to_async(lambda: product_models.Item.objects.get(pk=item.pk).name)()
    assert name == "AsyncOriginal"  # ...and the write rolled back.


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_async_update_success_commits():
    """Under ``await schema.execute`` a clean completion commits the write."""
    from asgiref.sync import sync_to_async

    _declare_item_types()
    UpdateItem = _declare_update_mutation()
    schema = _mutation_schema(UpdateItem)
    item = await sync_to_async(_seed_item)("AsyncBefore")

    result = await schema.execute(
        _UPDATE,
        variable_values={"id": _item_gid(item.pk), "d": {"name": "AsyncCommitted"}},
    )

    assert result.errors is None, result.errors
    assert result.data["write0"]["errors"] == []
    name = await sync_to_async(lambda: product_models.Item.objects.get(pk=item.pk).name)()
    assert name == "AsyncCommitted"


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_async_execution_context_exits_transaction_on_raised_base_exception(monkeypatch):
    """A non-GraphQL exception escaping the field still exits the worker transaction."""
    from asgiref.sync import sync_to_async
    from graphql.execution.execute import ExecutionContext as CoreExecutionContext

    _declare_item_types()
    UpdateItem = _declare_update_mutation()
    schema = _mutation_schema(UpdateItem)
    item = await sync_to_async(_seed_item)("AsyncRaise")

    def _boom(
        self,
        parent_type,
        source,
        field_nodes,
        path,
    ):
        raise RuntimeError("execution exploded outside GraphQL error handling")

    monkeypatch.setattr(CoreExecutionContext, "execute_field", _boom)
    # Strawberry's async execution surfaces the unexpected exception as a
    # result-level error; the load-bearing assertion is that the worker
    # transaction was exited (its connection left the atomic block).
    result = await schema.execute(
        _UPDATE,
        variable_values={"id": _item_gid(item.pk), "d": {"name": "AsyncRaised"}},
    )
    assert result.errors is not None
    assert "execution exploded" in str(result.errors[0])
    in_atomic = await sync_to_async(lambda: connections["default"].in_atomic_block)()
    assert in_atomic is False


@pytest.mark.django_db(transaction=True)
def test_sync_execution_context_exits_transaction_on_raised_base_exception(monkeypatch):
    """The sync twin: a non-GraphQL exception escaping the field exits the transaction."""
    from graphql.execution.execute import ExecutionContext as CoreExecutionContext

    _declare_item_types()
    UpdateItem = _declare_update_mutation()
    schema = _mutation_schema(UpdateItem)
    item = _seed_item("SyncRaise")

    def _boom(
        self,
        parent_type,
        source,
        field_nodes,
        path,
    ):
        raise RuntimeError("execution exploded outside GraphQL error handling")

    monkeypatch.setattr(CoreExecutionContext, "execute_field", _boom)
    # Strawberry's sync execution surfaces the unexpected exception as a
    # result-level error rather than re-raising; the load-bearing assertion is
    # that the transaction was exited (the connection left the atomic block).
    result = schema.execute_sync(
        _UPDATE,
        variable_values={"id": _item_gid(item.pk), "d": {"name": "SyncRaised"}},
    )
    assert result.errors is not None
    assert "execution exploded" in str(result.errors[0])
    assert connections["default"].in_atomic_block is False


def test_execution_errors_reads_both_graphql_core_error_shapes():
    """``_execution_errors`` bridges the graphql-core 3.2.9 errors relocation.

    graphql-core < 3.2.9 exposes the located-error list as
    ``ExecutionContext.errors``; 3.2.9 moved it behind a ``CollectedErrors``
    container at ``collected_errors.errors``. The installed version exercises
    only one shape at runtime, so both are pinned here explicitly.
    """
    from django_strawberry_framework.schema import DjangoMutationExecutionContext

    context = object.__new__(DjangoMutationExecutionContext)

    class _Collected:
        errors = ["located"]

    context.collected_errors = _Collected()
    assert context._execution_errors() == ["located"]

    del context.collected_errors
    context.errors = ["legacy"]
    assert context._execution_errors() == ["legacy"]


@pytest.mark.django_db
def test_unmarked_mutation_fields_and_introspection_execute_unwrapped():
    """Consumer-written mutation fields and ``__typename`` skip the transaction wrapper."""
    _declare_item_types()
    UpdateItem = _declare_update_mutation()

    def _plain() -> int:
        return 41

    schema = _mutation_schema(
        UpdateItem,
        extra_fields={"plain": strawberry.mutation(resolver=_plain)},
    )

    result = schema.execute_sync("mutation { __typename plain }")
    assert result.errors is None
    assert result.data == {"__typename": "Mutation", "plain": 41}


# ===========================================================================
# Disappearing rows: forced update / zero-row delete / missing re-fetch -> conflict
# ===========================================================================


class _DeleteTargetOutFromUnder:
    """An authorizing permission class that deletes the located row out-of-band.

    Runs AFTER the locate (the auth seam's position in the pipeline), so the
    located instance's row is gone by the time the write executes - the
    concurrent-delete race, made deterministic. sqlite ignores ``FOR UPDATE``,
    so the default lock cannot serialize the two "transactions" here; on a
    locking backend the same race surfaces only under ``select_for_update=False``.
    """

    def has_permission(
        self,
        info,
        mutation,
        operation,
        data,
        instance=None,
    ):
        if instance is not None:
            # Stand in for ANOTHER transaction's delete: the phased alias guard
            # polices consumer code (which is read-only pre-save), so the
            # simulated concurrent writer borrows the pipeline's own write-phase
            # seam - the race being made deterministic is the point, not the
            # phase discipline of this fixture.
            with pipeline_write_phase():
                product_models.Item._base_manager.filter(pk=instance.pk).delete()
        return True


@pytest.mark.django_db
def test_update_of_concurrently_deleted_row_returns_conflict_envelope():
    """A forced update matching zero rows is the in-band ``conflict`` envelope, rolled back."""
    _declare_item_types()
    UpdateItem = _declare_update_mutation(permission_classes=[_DeleteTargetOutFromUnder])
    schema = _mutation_schema(UpdateItem)
    item = _seed_item("Vanishing")

    result = schema.execute_sync(
        _UPDATE,
        variable_values={"id": _item_gid(item.pk), "d": {"name": "NeverLands"}},
    )

    assert result.errors is None, result.errors
    payload = result.data["write0"]
    assert payload["node"] is None
    assert [e["field"] for e in payload["errors"]] == ["id"]
    assert "concurrent" in payload["errors"][0]["messages"][0]
    # The conflict envelope rolled the WHOLE transaction back - including the
    # in-transaction out-of-band delete - and the update was never silently
    # converted into an insert: the row survives with its original name.
    item.refresh_from_db()
    assert item.name == "Vanishing"


@pytest.mark.django_db
def test_delete_of_concurrently_deleted_row_returns_conflict_envelope():
    """A delete whose target row vanished after locate is the ``conflict`` envelope."""
    _declare_item_types()
    DeleteItem = _declare_delete_mutation(permission_classes=[_DeleteTargetOutFromUnder])
    schema = _mutation_schema(DeleteItem)
    item = _seed_item("VanishingDelete")

    result = schema.execute_sync(_DELETE, variable_values={"id": _item_gid(item.pk)})

    assert result.errors is None, result.errors
    payload = result.data["write0"]
    assert payload["node"] is None
    assert [e["field"] for e in payload["errors"]] == ["id"]
    assert "concurrent" in payload["errors"][0]["messages"][0]


@pytest.mark.django_db
def test_missing_post_write_refetch_returns_conflict_envelope(monkeypatch):
    """A write whose pk re-fetch finds nothing returns ``conflict``, and rolls back."""
    from django_strawberry_framework.mutations import resolvers as mutation_resolvers

    _declare_item_types()
    UpdateItem = _declare_update_mutation()
    schema = _mutation_schema(UpdateItem)
    item = _seed_item("RefetchGone")

    monkeypatch.setattr(mutation_resolvers, "refetch_optimized", lambda *a, **k: None)
    result = schema.execute_sync(
        _UPDATE,
        variable_values={"id": _item_gid(item.pk), "d": {"name": "RefetchWritten"}},
    )

    assert result.errors is None, result.errors
    payload = result.data["write0"]
    assert payload["node"] is None
    assert [e["field"] for e in payload["errors"]] == ["id"]
    item.refresh_from_db()
    assert item.name == "RefetchGone"  # the conflict envelope rolled the write back


# ===========================================================================
# The Django 5.2 / 6.0 zero-row compat disambiguation (unit level)
# ===========================================================================


def test_not_updated_exceptions_prefers_the_typed_signal():
    """Django 6.0's per-model ``NotUpdated`` is caught by type; 5.2 falls back to DatabaseError."""
    assert not_updated_exceptions(product_models.Item) == (product_models.Item.NotUpdated,)

    class _LegacyModelStandIn:
        """A Django-5.2-shaped model class: no ``NotUpdated`` attribute."""

    assert not_updated_exceptions(_LegacyModelStandIn) == (DatabaseError,)


@pytest.mark.django_db
def test_forced_update_conflict_requires_a_demonstrably_absent_row():
    """A zero-row signal with the row still present re-raises (not a conflict)."""
    item = _seed_item("StillThere")
    signal = DatabaseError("Forced update did not affect any rows.")
    with pytest.raises(DatabaseError):
        forced_update_conflict_errors(item, "default", signal)


@pytest.mark.django_db
def test_forced_update_conflict_maps_absent_row_to_conflict():
    """A zero-row signal with the row demonstrably gone is the ``conflict`` envelope."""
    item = _seed_item("Gone")
    product_models.Item._base_manager.filter(pk=item.pk).delete()
    signal = DatabaseError("Forced update did not affect any rows.")
    errors = forced_update_conflict_errors(item, "default", signal)
    assert [error.field for error in errors] == ["id"]
    assert errors[0].codes == ["conflict"]


@pytest.mark.django_db
def test_forced_update_conflict_requires_a_usable_transaction():
    """With the connection marked needs-rollback the original error propagates untouched."""
    item = _seed_item("Poisoned")
    signal = DatabaseError("some backend failure")
    connection = connections["default"]
    with transaction.atomic():
        connection.needs_rollback = True
        try:
            with pytest.raises(DatabaseError, match="some backend failure"):
                forced_update_conflict_errors(item, "default", signal)
        finally:
            connection.needs_rollback = False


def test_forced_update_conflict_probe_failure_reraises_the_original():
    """The absence probe itself failing re-raises the ORIGINAL error, not the probe's."""
    signal = DatabaseError("the original failure")

    class _ExplodingQuerySet:
        def filter(self, **kwargs):
            return self

        def exists(self):
            raise DatabaseError("probe failure")

    class _ExplodingManager:
        def using(self, alias):
            return _ExplodingQuerySet()

    class _ProbeStandIn:
        """A model-shaped stand-in whose base manager cannot be queried."""

        _base_manager = _ExplodingManager()
        pk = 1

    with pytest.raises(DatabaseError, match="the original failure"):
        forced_update_conflict_errors(_ProbeStandIn(), "default", signal)


def test_conflict_error_shape():
    error = conflict_error()
    assert error.field == "id"
    assert error.codes == ["conflict"]


# ===========================================================================
# Alias pinning: fail-closed hook switch, instance-sensitive router, helpers
# ===========================================================================


@pytest.mark.django_db
def test_visibility_hook_switching_aliases_fails_closed():
    """A ``get_queryset`` hook re-routing to another alias is a loud refusal, not a write."""

    def _reroute(cls, queryset, info, **kwargs):
        return queryset.using("some_other_alias")

    _declare_item_types(item_get_queryset=classmethod(_reroute))
    UpdateItem = _declare_update_mutation()
    schema = _mutation_schema(UpdateItem)
    item = _seed_item("PinnedAlias")

    result = schema.execute_sync(
        _UPDATE,
        variable_values={"id": _item_gid(item.pk), "d": {"name": "CrossAlias"}},
    )

    assert result.errors is not None
    assert "pinned to alias" in str(result.errors[0])
    item.refresh_from_db()
    assert item.name == "PinnedAlias"


def test_pin_write_queryset_passes_unrouted_and_matching_querysets():
    queryset = product_models.Item.objects.all()
    assert pin_write_queryset(queryset, "default")._db == "default"
    routed = product_models.Item.objects.using("default")
    assert pin_write_queryset(routed, "default")._db == "default"


def test_pin_write_queryset_derives_the_owner_from_the_model():
    queryset = product_models.Item.objects.using("some_other_alias")
    with pytest.raises(ConfigurationError, match="Item get_queryset"):
        pin_write_queryset(queryset, "default")


def test_check_instance_write_alias_fails_closed_on_divergence(monkeypatch):
    monkeypatch.setattr(
        write_transaction.router,
        "db_for_write",
        lambda model, **hints: "shard_x" if hints.get("instance") is not None else "default",
    )
    with pytest.raises(ConfigurationError, match="instance-sensitive"):
        check_instance_write_alias(product_models.Item, "default", object())
    # A None / matching answer passes.
    monkeypatch.setattr(write_transaction.router, "db_for_write", lambda model, **hints: None)
    check_instance_write_alias(product_models.Item, "default", object())


def test_resolve_write_alias_model_less_default():
    assert resolve_write_alias(None) == "default"


def test_require_write_pipeline_outside_the_pipeline_is_a_wiring_error():
    with pytest.raises(ConfigurationError, match="outside the write pipeline"):
        require_write_pipeline()
    with write_pipeline("default", lock=False):
        assert require_write_pipeline().alias == "default"


class _FakeBarrierCursor:
    def __init__(self, connection: _FakeBarrierConnection) -> None:
        self._connection = connection
        self._last: tuple | None = None

    def __enter__(self) -> _FakeBarrierCursor:
        return self

    def __exit__(self, *exc: object) -> bool:
        return False

    def execute(self, sql: str) -> None:
        self._connection.executed.append(sql)
        # Model SQLite's connection-level ``PRAGMA query_only`` so the read-back +
        # prior-value-restore + reentrancy behavior is exercised, not just the SQL text.
        if sql == "PRAGMA query_only":
            self._last = (1 if self._connection.query_only else 0,)
        elif sql == "PRAGMA query_only = ON":
            self._connection.query_only = True
        elif sql == "PRAGMA query_only = OFF":
            self._connection.query_only = False

    def fetchone(self) -> tuple | None:
        return self._last


class _FakeBarrierConnection:
    def __init__(self, vendor: str, *, query_only: bool = False) -> None:
        self.vendor = vendor
        self.executed: list[str] = []
        self.query_only = query_only

    def cursor(self) -> _FakeBarrierCursor:
        return _FakeBarrierCursor(self)


def _with_fake_barrier_connection(alias: str, connection: object):
    connections.databases[alias] = dict(connections.databases["default"])
    connections[alias] = connection


def _drop_fake_barrier_connection(alias: str) -> None:
    with contextlib.suppress(AttributeError, KeyError):
        del connections[alias]
    connections.databases.pop(alias, None)


def test_enforce_read_only_barrier_postgresql_sets_transaction_read_only():
    """PostgreSQL is armed with ``SET TRANSACTION READ ONLY``; the mode dies with the txn."""
    connection = _FakeBarrierConnection("postgresql")
    _with_fake_barrier_connection("ro_barrier_pg", connection)
    try:
        disarm = _enforce_read_only_barrier("ro_barrier_pg")
        assert connection.executed == ["SET TRANSACTION READ ONLY"]
        # Disarm is a no-op (nothing to restore on the connection; the read-only mode
        # is scoped to the transaction that is about to be rolled back).
        disarm()
        assert connection.executed == ["SET TRANSACTION READ ONLY"]
    finally:
        _drop_fake_barrier_connection("ro_barrier_pg")


def test_enforce_read_only_barrier_sqlite_arms_and_restores_prior_query_only():
    """SQLite reads the PRIOR ``query_only`` and restores exactly it (never a blind OFF)."""
    connection = _FakeBarrierConnection("sqlite", query_only=False)
    _with_fake_barrier_connection("ro_barrier_sqlite", connection)
    try:
        disarm = _enforce_read_only_barrier("ro_barrier_sqlite")
        # Read prior value first, then arm ON.
        assert connection.executed == ["PRAGMA query_only", "PRAGMA query_only = ON"]
        assert connection.query_only is True
        disarm()
        # Prior was OFF, so restore to OFF.
        assert connection.executed[-1] == "PRAGMA query_only = OFF"
        assert connection.query_only is False
    finally:
        _drop_fake_barrier_connection("ro_barrier_sqlite")


def test_enforce_read_only_barrier_sqlite_preserves_a_preexisting_read_only_flag():
    """A pre-existing ``query_only=ON`` (or an ENCLOSING barrier's arming) survives disarm.

    A blind ``PRAGMA query_only = OFF`` would clobber a pre-existing read-only setting and,
    for nested authorization phases on one connection, an inner disarm would reopen the OUTER
    phase - leaving its guard permitting auth-alias SQL on a now-writable connection.
    """
    connection = _FakeBarrierConnection("sqlite", query_only=True)
    _with_fake_barrier_connection("ro_barrier_sqlite_nested", connection)
    try:
        disarm = _enforce_read_only_barrier("ro_barrier_sqlite_nested")
        assert connection.query_only is True
        disarm()
        # Prior was ON, so the connection stays read-only after disarm.
        assert connection.executed[-1] == "PRAGMA query_only = ON"
        assert connection.query_only is True
    finally:
        _drop_fake_barrier_connection("ro_barrier_sqlite_nested")


def test_enforce_read_only_barrier_fails_closed_on_unsupported_backend():
    """A backend that cannot enforce read-only from an open atomic FAILS CLOSED (no arming)."""
    connection = _FakeBarrierConnection("mysql")
    _with_fake_barrier_connection("ro_barrier_mysql", connection)
    try:
        with pytest.raises(ConfigurationError, match="database-enforced read-only"):
            _enforce_read_only_barrier("ro_barrier_mysql")
        # Fail closed BEFORE issuing any statement on the unsupported connection.
        assert connection.executed == []
    finally:
        _drop_fake_barrier_connection("ro_barrier_mysql")


# ===========================================================================
# Lock opt-out (``Meta.select_for_update = False``) end to end
# ===========================================================================


@pytest.mark.django_db
def test_select_for_update_false_update_still_succeeds_unlocked():
    """The explicit lock opt-out updates cleanly (weaker concurrency, same envelope contract)."""
    _declare_item_types()
    UpdateItem = _declare_update_mutation(select_for_update=False)
    schema = _mutation_schema(UpdateItem)
    item = _seed_item("Unlocked")

    result = schema.execute_sync(
        _UPDATE,
        variable_values={"id": _item_gid(item.pk), "d": {"name": "UnlockedUpdated"}},
    )
    assert result.errors is None, result.errors
    assert result.data["write0"]["errors"] == []
    item.refresh_from_db()
    assert item.name == "UnlockedUpdated"


def test_model_flavor_meta_select_for_update_defaults_true_and_rejects_non_bool():
    """The model flavor shares the row-lock validator: default True, non-bool refused."""

    class DefaultLocked(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "update"
            permission_classes = [_AllowAll]

    assert DefaultLocked._mutation_meta.select_for_update is True

    with pytest.raises(ConfigurationError, match="select_for_update must be a bool"):

        class BadLock(DjangoMutation):
            class Meta:
                model = product_models.Item
                operation = "update"
                permission_classes = [_AllowAll]
                select_for_update = "yes"


def test_modelform_flavor_meta_select_for_update_defaults_true():
    from django import forms

    from django_strawberry_framework import DjangoModelFormMutation

    class ItemForm(forms.ModelForm):
        class Meta:
            model = product_models.Item
            fields = ("name", "category")

    class FormUpdate(DjangoModelFormMutation):
        class Meta:
            form_class = ItemForm
            operation = "update"
            permission_classes = [_AllowAll]

    assert FormUpdate._mutation_meta.select_for_update is True


# ===========================================================================
# Strict-boolean authorization
# ===========================================================================


class _TruthyNonBool:
    """A permission class returning a truthy NON-bool (the silent-allow bug shape)."""

    def has_permission(
        self,
        info,
        mutation,
        operation,
        data,
        instance=None,
    ):
        return "yes"


@pytest.mark.django_db
def test_permission_class_returning_non_bool_is_a_configuration_error():
    _declare_item_types()
    UpdateItem = _declare_update_mutation(permission_classes=[_TruthyNonBool])
    schema = _mutation_schema(UpdateItem)
    item = _seed_item("StrictBool")

    result = schema.execute_sync(
        _UPDATE,
        variable_values={"id": _item_gid(item.pk), "d": {"name": "Allowed?"}},
    )

    assert result.errors is not None
    assert "must return a bool" in str(result.errors[0])
    item.refresh_from_db()
    assert item.name == "StrictBool"  # never written


@pytest.mark.django_db
def test_check_permission_override_returning_non_bool_is_a_configuration_error():
    _declare_item_types()

    class NonBoolCheck(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "update"
            permission_classes = [_AllowAll]

        def check_permission(
            self,
            info,
            operation,
            data,
            instance=None,
        ):
            return 1  # truthy, not a bool

    schema = _mutation_schema(NonBoolCheck)
    item = _seed_item("StrictCheck")

    result = schema.execute_sync(
        _UPDATE,
        variable_values={"id": _item_gid(item.pk), "d": {"name": "Allowed?"}},
    )

    assert result.errors is not None
    assert "check_permission must return a bool" in str(result.errors[0])
    item.refresh_from_db()
    assert item.name == "StrictCheck"


def test_has_perm_returning_non_bool_is_a_configuration_error():
    from types import SimpleNamespace

    from django_strawberry_framework.mutations.permissions import DjangoModelPermission

    class _WeirdUser:
        is_authenticated = True

        def has_perm(self, codename):
            return "granted"  # truthy, not a bool

    class _Mutation:
        Meta = type("Meta", (), {})

        @classmethod
        def _resolve_model(cls, meta):
            return product_models.Item

    request = SimpleNamespace(user=_WeirdUser())
    info = SimpleNamespace(context=SimpleNamespace(request=request))
    with pytest.raises(ConfigurationError, match="has_perm must return a bool"):
        DjangoModelPermission().has_permission(info, _Mutation, "update", None)


@pytest.mark.django_db
def test_forced_update_integrity_error_race_maps_to_the_constraint_envelope():
    """A forced-update ``IntegrityError`` race is the ``"__all__"`` envelope (Major-2 on update).

    ``IntegrityError`` subclasses ``DatabaseError``, so under the Django 5.2
    untyped zero-row catch the ordering matters: the constraint race must hit
    the ``IntegrityError`` arm, never the conflict disambiguation.
    """
    from unittest import mock

    from django_strawberry_framework.mutations.inputs import NON_FIELD_ERROR_KEY

    _declare_item_types()
    UpdateItem = _declare_update_mutation()
    schema = _mutation_schema(UpdateItem)
    item = _seed_item("RaceTarget")

    with mock.patch.object(
        product_models.Item,
        "save",
        side_effect=IntegrityError("races validate_constraints"),
    ):
        result = schema.execute_sync(
            _UPDATE,
            variable_values={"id": _item_gid(item.pk), "d": {"name": "Raced"}},
        )

    assert result.errors is None, result.errors
    payload = result.data["write0"]
    assert payload["node"] is None
    assert payload["errors"][0]["field"] == NON_FIELD_ERROR_KEY
    assert payload["errors"][0]["messages"] == ["A database constraint was violated."]
    item.refresh_from_db()
    assert item.name == "RaceTarget"


# ---------------------------------------------------------------------------
# The phased alias guard + canonical pk equality + target-state drift (hardening)
# ---------------------------------------------------------------------------


def test_is_read_only_sql_uses_a_comment_stripped_allow_list():
    """Read-only classification is an ALLOW-list over the first comment-stripped token."""
    from django_strawberry_framework.utils.write_transaction import is_read_only_sql

    assert is_read_only_sql("SELECT 1")
    assert is_read_only_sql("  /* lead */ -- note\n select name from t")
    assert is_read_only_sql('SAVEPOINT "s1"')
    assert is_read_only_sql('RELEASE SAVEPOINT "s1"')
    assert is_read_only_sql('ROLLBACK TO SAVEPOINT "s1"')
    # Writes, DDL, EXPLAIN (PostgreSQL EXPLAIN ANALYZE executes), and CTE openers
    # (a data-modifying CTE writes through a read-shaped opener) are all rejected.
    assert not is_read_only_sql("INSERT INTO t VALUES (1)")
    assert not is_read_only_sql("/* comment */ UPDATE t SET x = 1")
    assert not is_read_only_sql("EXPLAIN ANALYZE UPDATE t SET x = 1")
    assert not is_read_only_sql("WITH d AS (DELETE FROM t RETURNING 1) SELECT * FROM d")
    # Degenerate shapes fail CLOSED: comment-only / unterminated-comment / empty.
    assert not is_read_only_sql("-- only a comment")
    assert not is_read_only_sql("/* unterminated")
    assert not is_read_only_sql("")


@pytest.mark.django_db
def test_pinned_alias_guard_rejects_writes_outside_the_write_phase():
    """On the PINNED alias, write SQL is rejected in the read-only phase and allowed inside it."""
    from django.db import connection

    from django_strawberry_framework.utils.write_transaction import (
        pipeline_alias_guard,
        pipeline_write_phase,
        write_pipeline,
    )

    with write_pipeline("default", lock=False), pipeline_alias_guard("GuardMut", "default"):
        # Reads pass in the read-only phase.
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        # Write SQL outside the write phase fails closed. (Contained in a
        # savepoint so the rejection does not mark the TEST transaction broken -
        # in the real pipeline the error propagates and rolls the mutation back.)
        with pytest.raises(ConfigurationError, match="OUTSIDE the mutation's write phase"):
            with transaction.atomic():
                product_models.Category.objects.create(name="PhaseCat")
        assert not product_models.Category.objects.filter(name="PhaseCat").exists()
        # The SAME statement inside the write phase succeeds.
        with pipeline_write_phase():
            product_models.Category.objects.create(name="PhaseCat")
        assert product_models.Category.objects.filter(name="PhaseCat").exists()


def test_pks_match_canonicalizes_through_the_pk_field():
    """pk equality goes through the model pk field's ``to_python``, failing closed on garbage."""
    import uuid
    from types import SimpleNamespace

    from django.db import models as django_models

    from django_strawberry_framework.utils.write_transaction import canonical_pk, pks_match

    uuid_model = SimpleNamespace(_meta=SimpleNamespace(pk=django_models.UUIDField()))
    value = uuid.uuid4()
    # The SAME row under three spellings: UUID object, dashed, un-dashed.
    assert pks_match(uuid_model, value, str(value))
    assert pks_match(uuid_model, value, value.hex)
    assert not pks_match(uuid_model, value, uuid.uuid4())
    # A forged pk of the wrong shape is a MISMATCH, never an exception.
    assert not pks_match(uuid_model, value, "not-a-uuid")

    int_model = SimpleNamespace(_meta=SimpleNamespace(pk=django_models.IntegerField()))
    assert pks_match(int_model, 5, "5")
    assert canonical_pk(int_model, "7") == 7


@pytest.mark.django_db
def test_target_state_snapshot_and_drift_rejection():
    """``assert_no_target_drift`` rejects mutated loaded fields; deferred fields never read as drift."""
    from django_strawberry_framework.utils.write_transaction import (
        assert_no_target_drift,
        require_write_pipeline,
        snapshot_target_state,
        write_pipeline,
    )

    category = product_models.Category.objects.create(name="DriftHelperCat")
    item = product_models.Item.objects.create(name="DriftHelperItem", category=category)

    with write_pipeline("default", lock=False):
        pipeline = require_write_pipeline()
        # No snapshot recorded (a direct skeleton-less call): the check is a no-op.
        assert_no_target_drift("NoSnapshotMut", item)

        pipeline.target_state = snapshot_target_state(item)
        assert_no_target_drift("CleanMut", item)  # unchanged: no raise

        item.name = "drifted"
        with pytest.raises(ConfigurationError, match="mutated in memory"):
            assert_no_target_drift("DriftMut", item)

    # A DEFERRED field is absent from the snapshot and skipped by the check.
    deferred_item = product_models.Item.objects.defer("description").get(pk=item.pk)
    with write_pipeline("default", lock=False):
        pipeline = require_write_pipeline()
        pipeline.target_state = snapshot_target_state(deferred_item)
        assert "description" not in pipeline.target_state
        assert_no_target_drift("DeferredMut", deferred_item)  # no lazy-load, no raise

        # And the converse: a field SNAPSHOTTED loaded but deferred at CHECK time is
        # skipped too (comparing it would lazy-load - the check must never query).
        item.refresh_from_db()
        pipeline.target_state = snapshot_target_state(item)
        assert "description" in pipeline.target_state
        assert_no_target_drift("DeferredAtCheckMut", deferred_item)  # skip, no raise


@pytest.mark.django_db
def test_snapshot_target_state_fingerprints_mutable_container_values():
    """A JSONField / ArrayField value is fingerprinted, so in-place mutation reads as drift."""
    from types import SimpleNamespace

    from django_strawberry_framework.utils.write_transaction import (
        _FieldFingerprint,
        assert_no_target_drift,
        require_write_pipeline,
        snapshot_target_state,
        write_pipeline,
    )

    field = SimpleNamespace(attname="payload")
    instance = SimpleNamespace(
        payload={"tier": "gold", "tags": ["a"]},
        _meta=SimpleNamespace(concrete_fields=[field]),
        get_deferred_fields=lambda: set(),
    )

    snapshot = snapshot_target_state(instance)
    # Captured as a structural fingerprint independent of the live container.
    assert isinstance(snapshot["payload"], _FieldFingerprint)

    with write_pipeline("default", lock=False):
        require_write_pipeline().target_state = snapshot
        # An unchanged value re-fingerprints identically: no drift.
        assert_no_target_drift("JsonCleanMut", instance)
        # Mutating the JSON value IN PLACE - a by-reference snapshot would alias
        # the very object being mutated and miss this; the fingerprint catches it.
        instance.payload["tier"] = "platinum"
        with pytest.raises(ConfigurationError, match="mutated in memory"):
            assert_no_target_drift("JsonDriftMut", instance)


def test_snapshot_target_state_captures_filefield_name_not_the_mutable_descriptor():
    """A FieldFile is snapshotted by its ``name``: an in-place name re-point reads as drift.

    ``FieldFile`` is a MUTABLE descriptor - a hook can assign ``instance.<file>.name`` on the
    SAME object, so a by-reference snapshot would alias it and the identity/``==`` check would
    miss the unauthorized file-column change (round-5 P1). Snapshotting the ``name`` catches it.
    """
    from types import SimpleNamespace

    from django.db.models.fields.files import FieldFile

    from django_strawberry_framework.utils.write_transaction import (
        _FileNameSnapshot,
        assert_no_target_drift,
        require_write_pipeline,
        snapshot_target_state,
        write_pipeline,
    )

    fake_field = SimpleNamespace(storage=None, attname="avatar")
    file_value = FieldFile(instance=None, field=fake_field, name="orig.png")
    field = SimpleNamespace(attname="avatar")
    instance = SimpleNamespace(
        avatar=file_value,
        _meta=SimpleNamespace(concrete_fields=[field]),
        get_deferred_fields=lambda: set(),
    )

    snapshot = snapshot_target_state(instance)
    # Captured by its DB-relevant name string, NOT the mutable descriptor object.
    assert isinstance(snapshot["avatar"], _FileNameSnapshot)
    assert snapshot["avatar"].name == "orig.png"

    with write_pipeline("default", lock=False):
        require_write_pipeline().target_state = snapshot
        assert_no_target_drift("FileCleanMut", instance)  # unchanged: no raise
        # Re-point the FieldFile name IN PLACE (same object) - the identity/== path a
        # by-reference snapshot uses would miss this; the name snapshot catches it.
        instance.avatar.name = "evil.png"
        with pytest.raises(ConfigurationError, match="mutated in memory"):
            assert_no_target_drift("FileDriftMut", instance)


@pytest.mark.django_db
def test_snapshot_fingerprint_is_iterative_and_budgeted():
    """A pathologically DEEP field value fingerprints without RecursionError (iterative)."""
    from types import SimpleNamespace

    from django_strawberry_framework.utils.write_transaction import (
        _SNAPSHOT_NODE_BUDGET,
        _field_fingerprint,
        assert_no_target_drift,
        require_write_pipeline,
        snapshot_target_state,
        write_pipeline,
    )

    # Deeper than Python's default recursion limit - copy.deepcopy / recursive
    # comparison would raise RecursionError; the iterative fingerprint does not.
    deep: dict = {}
    node = deep
    for _ in range(5000):
        child: dict = {}
        node["next"] = child
        node = child
    node["leaf"] = 1

    field = SimpleNamespace(attname="payload")
    instance = SimpleNamespace(
        payload=deep,
        _meta=SimpleNamespace(concrete_fields=[field]),
        get_deferred_fields=lambda: set(),
    )
    snapshot = snapshot_target_state(instance)  # no RecursionError
    with write_pipeline("default", lock=False):
        require_write_pipeline().target_state = snapshot
        assert_no_target_drift("DeepCleanMut", instance)  # unchanged: no raise
        node["leaf"] = 2  # mutate the deepest scalar in place
        with pytest.raises(ConfigurationError, match="mutated in memory"):
            assert_no_target_drift("DeepDriftMut", instance)

    # A value exceeding the node budget is rejected loudly, never walked unbounded.
    with pytest.raises(ConfigurationError, match="too large to fingerprint"):
        _field_fingerprint(list(range(_SNAPSHOT_NODE_BUDGET + 2)))


def test_field_fingerprint_covers_container_kinds_and_is_deterministic():
    """The fingerprint handles set / frozenset / bytes / tuple and is order-stable per structure."""
    from django_strawberry_framework.utils.write_transaction import _field_fingerprint

    # Sets/frozensets fingerprint by a deterministic (repr-sorted) member order,
    # so equal sets built in different insertion orders match.
    assert _field_fingerprint({3, 1, 2}) == _field_fingerprint({2, 3, 1})
    assert _field_fingerprint(frozenset({"b", "a"})) == _field_fingerprint(frozenset({"a", "b"}))
    # Dicts fingerprint by sorted keys; lists/tuples keep order.
    assert _field_fingerprint({"a": 1, "b": 2}) == _field_fingerprint({"b": 2, "a": 1})
    assert _field_fingerprint([1, 2, 3]) != _field_fingerprint([3, 2, 1])
    # bytes / bytearray are captured by value; a change in content changes the digest.
    assert _field_fingerprint(b"abc") == _field_fingerprint(bytearray(b"abc"))
    assert _field_fingerprint(b"abc") != _field_fingerprint(b"abd")
    # Scalars are type-tagged: 1 and "1" never collide.
    assert _field_fingerprint([1]) != _field_fingerprint(["1"])
    # A nested mix round-trips stably.
    value = {"tags": [1, 2], "meta": {"seen": True}, "ids": {9, 8}}
    assert _field_fingerprint(value) == _field_fingerprint(dict(value))
