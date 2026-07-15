"""The BETA-055 write-transaction contract (``DjangoSchema`` + ``utils/write_transaction.py``).

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
    check_instance_write_alias,
    conflict_error,
    forced_update_conflict_errors,
    not_updated_exceptions,
    pin_write_queryset,
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
    """The model flavor shares the BETA-055 validator: default True, non-bool refused."""

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
