"""Write-pipeline resolver tests (spec-036 Slice 3).

System-under-test is ``mutations/resolvers.py`` - the sync + async create /
update / delete pipeline driven through a package-test ``@strawberry.type
Mutation`` over a finalized schema (per the Slice-3 boundary: the live products
write surface + the ``CaptureQueriesContext`` assertion are Slice 4). Fixtures:

- the realistic products ``Item`` / ``Category`` (FK + ``unique_item_per_category``)
  cover the validation-envelope, ``"__all__"`` sentinel, AR-H2 partial-constraint,
  wrong-type ``GlobalID``, hidden-row, re-fetch-skips-visibility, and the
  sync/async/transaction cases - all over real DB tables;
- the library ``Book`` / ``Genre`` / ``Shelf`` (a real M2M) cover AR-M1 M2M
  replace / clear / omit, which products cannot (no M2M model).

Each test seeds rows inline (library acceptance idiom) or with the products
services where convenient; permission is held open with a local allow-all class so
these tests pin the *resolver*, not the write-auth seam (that is
``test_permissions.py``).
"""

from __future__ import annotations

import itertools
from types import SimpleNamespace
from unittest import mock

import pytest
import strawberry
from apps.library import models as library_models
from apps.products import models as product_models
from asgiref.sync import sync_to_async
from django.db import IntegrityError
from strawberry import relay

from django_strawberry_framework import (
    DjangoMutation,
    DjangoMutationField,
    DjangoOptimizerExtension,
    DjangoType,
    finalize_django_types,
)
from django_strawberry_framework.mutations import resolvers
from django_strawberry_framework.mutations.inputs import NON_FIELD_ERROR_KEY
from django_strawberry_framework.registry import registry
from django_strawberry_framework.testing.relay import global_id_for
from django_strawberry_framework.utils.querysets import SyncMisuseError


@pytest.fixture(autouse=True)
def _isolate_registry():
    """Reset the registry (co-clears the mutation ledger + declaration registry) per test."""
    registry.clear()
    yield
    registry.clear()


_category_name_counter = itertools.count(1)


def _category_name() -> str:
    """A unique ``Category.name`` per call.

    ``Category.name`` is ``unique=True``; one test runs with ``transaction=True``
    (real commits, flushed at teardown rather than rolled back), so a fixed name
    can collide across tests depending on ordering. A per-call name keeps every
    test's category independent.
    """
    return f"Cat-{next(_category_name_counter)}"


class _AllowAll:
    """A permission class that authorizes every write (isolates the resolver from auth)."""

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


def _schema(mutation_type: type) -> strawberry.Schema:
    """Build a finalized schema with the optimizer extension installed."""
    return strawberry.Schema(
        query=_Query,
        mutation=mutation_type,
        extensions=[DjangoOptimizerExtension],
    )


# ---------------------------------------------------------------------------
# Products Item/Category fixtures (FK + unique_item_per_category)
# ---------------------------------------------------------------------------


def _build_item_schema(*, item_get_queryset=None):
    """Declare Item/Category primaries + create/update/delete mutations; return (schema, types)."""

    class CategoryT(DjangoType, relay.Node):
        class Meta:
            model = product_models.Category
            fields = ("id", "name")
            primary = True

    item_meta_attrs = {
        "model": product_models.Item,
        "fields": ("id", "name", "category"),
        "primary": True,
    }
    item_body: dict = {"Meta": type("Meta", (), item_meta_attrs)}
    if item_get_queryset is not None:
        item_body["get_queryset"] = item_get_queryset
    ItemT = type("ItemT", (DjangoType, relay.Node), item_body)

    class CreateItem(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "create"
            permission_classes = [_AllowAll]

    class UpdateItem(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "update"
            permission_classes = [_AllowAll]

    class DeleteItem(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "delete"
            permission_classes = [_AllowAll]

    @strawberry.type
    class Mutation:
        create_item = DjangoMutationField(CreateItem)
        update_item = DjangoMutationField(UpdateItem)
        delete_item = DjangoMutationField(DeleteItem)

    finalize_django_types()
    return _schema(Mutation), (CategoryT, ItemT)


_CREATE = (
    "mutation($d: ItemInput!){ createItem(data:$d){ "
    "node{ id name category{ name } } errors{ field messages } } }"
)
_UPDATE = (
    "mutation($id: ID!, $d: ItemPartialInput!){ updateItem(id:$id, data:$d){ "
    "node{ name } errors{ field messages } } }"
)
_DELETE = (
    "mutation($id: ID!){ deleteItem(id:$id){ "
    "node{ name category{ name } } errors{ field messages } } }"
)


def _item_gid(item_type: type, pk) -> str:
    return global_id_for(item_type, pk)


@pytest.mark.django_db
def test_create_happy_path():
    """A create returns the object in the ``node`` slot, empty ``errors``, and writes the row."""
    schema, (CategoryT, _ItemT) = _build_item_schema()
    cat = product_models.Category.objects.create(name=_category_name())
    res = schema.execute_sync(
        _CREATE,
        variable_values={"d": {"name": "Widget", "categoryId": global_id_for(CategoryT, cat.pk)}},
    )
    assert res.errors is None, res.errors
    payload = res.data["createItem"]
    assert payload["node"]["name"] == "Widget"
    assert payload["node"]["category"]["name"] == cat.name
    assert payload["errors"] == []
    assert product_models.Item.objects.filter(name="Widget", category=cat).exists()


@pytest.mark.django_db
def test_update_happy_path_partial_leaves_unprovided_unchanged():
    """A partial update changes only provided fields; the unprovided FK is unchanged."""
    schema, (_CategoryT, ItemT) = _build_item_schema()
    cat = product_models.Category.objects.create(name=_category_name())
    item = product_models.Item.objects.create(name="Old", category=cat)
    res = schema.execute_sync(
        _UPDATE,
        variable_values={"id": _item_gid(ItemT, item.pk), "d": {"name": "New"}},
    )
    assert res.errors is None, res.errors
    assert res.data["updateItem"]["node"]["name"] == "New"
    item.refresh_from_db()
    assert item.name == "New"
    assert item.category_id == cat.pk  # unprovided -> unchanged


@pytest.mark.django_db
def test_delete_happy_path_returns_snapshot_and_removes_row():
    """A delete returns the pre-deletion snapshot in the slot; the row is gone."""
    schema, (_CategoryT, ItemT) = _build_item_schema()
    cat = product_models.Category.objects.create(name=_category_name())
    item = product_models.Item.objects.create(name="Doomed", category=cat)
    res = schema.execute_sync(_DELETE, variable_values={"id": _item_gid(ItemT, item.pk)})
    assert res.errors is None, res.errors
    assert res.data["deleteItem"]["node"]["name"] == "Doomed"
    assert not product_models.Item.objects.filter(pk=item.pk).exists()


@pytest.mark.django_db
def test_delete_snapshot_materializes_relation_before_delete():
    """The delete snapshot carries the selected relation, loaded before ``delete()`` (AR-M5/Medium-2)."""
    schema, (_CategoryT, ItemT) = _build_item_schema()
    cat = product_models.Category.objects.create(name=_category_name())
    item = product_models.Item.objects.create(name="Doomed", category=cat)
    res = schema.execute_sync(_DELETE, variable_values={"id": _item_gid(ItemT, item.pk)})
    assert res.errors is None, res.errors
    # The related ``category`` is accessible on the detached snapshot after the row
    # (and its FK source) is deleted - it was loaded before delete().
    assert res.data["deleteItem"]["node"]["category"]["name"] == cat.name


@pytest.mark.django_db
def test_full_clean_validation_error_yields_null_object_envelope():
    """A single-field validation failure -> one ``FieldError`` on that field, null object."""
    schema, (CategoryT, _ItemT) = _build_item_schema()
    cat = product_models.Category.objects.create(name=_category_name())
    # ``name`` is required and non-blank; an empty string fails ``full_clean``.
    res = schema.execute_sync(
        _CREATE,
        variable_values={"d": {"name": "", "categoryId": global_id_for(CategoryT, cat.pk)}},
    )
    assert res.errors is None, res.errors
    payload = res.data["createItem"]
    assert payload["node"] is None
    assert [e["field"] for e in payload["errors"]] == ["name"]


@pytest.mark.django_db
def test_unique_constraint_caught_by_validate_constraints_keys_all_sentinel():
    """A duplicate ``(category, name)`` is a ``ValidationError`` (not IntegrityError), keyed ``"__all__"``."""
    schema, (CategoryT, _ItemT) = _build_item_schema()
    cat = product_models.Category.objects.create(name=_category_name())
    product_models.Item.objects.create(name="Dup", category=cat)
    res = schema.execute_sync(
        _CREATE,
        variable_values={"d": {"name": "Dup", "categoryId": global_id_for(CategoryT, cat.pk)}},
    )
    assert res.errors is None, res.errors
    payload = res.data["createItem"]
    assert payload["node"] is None
    assert NON_FIELD_ERROR_KEY in [e["field"] for e in payload["errors"]]
    # Only one row persists - the duplicate was caught before save().
    assert product_models.Item.objects.filter(name="Dup", category=cat).count() == 1


@pytest.mark.django_db
def test_partial_update_constraint_collision_keeps_unprovided_co_member(monkeypatch):
    """Updating only ``name`` to a taken value under the same category fails (AR-H2)."""
    schema, (_CategoryT, ItemT) = _build_item_schema()
    cat = product_models.Category.objects.create(name=_category_name())
    product_models.Item.objects.create(name="Taken", category=cat)
    target = product_models.Item.objects.create(name="Free", category=cat)
    res = schema.execute_sync(
        _UPDATE,
        variable_values={"id": _item_gid(ItemT, target.pk), "d": {"name": "Taken"}},
    )
    assert res.errors is None, res.errors
    payload = res.data["updateItem"]
    assert payload["node"] is None
    assert NON_FIELD_ERROR_KEY in [e["field"] for e in payload["errors"]]


def test_unprovided_exclude_keeps_constrained_co_member_drops_unrelated():
    """``_unprovided_exclude`` pins the AR-H2 carve-out directly on ``Item``.

    A ``name``-only provided set keeps ``category`` OUT of the exclude set (the two
    co-participate in ``unique_item_per_category``) while ``description`` /
    ``is_private`` (unconstrained, unprovided) stay excluded.
    """
    exclude = resolvers._unprovided_exclude(product_models.Item, {"name"})
    assert "category" not in exclude  # co-constrained with provided ``name``
    assert "description" in exclude  # unrelated, unprovided
    assert "is_private" in exclude


def test_unprovided_exclude_single_field_unique_group_kept():
    """A provided single-``unique`` field is its own group; an unprovided unrelated field is excluded."""
    # ``Category.name`` is ``unique=True`` (a 1-element group). Providing ``name``
    # keeps it validating; the unprovided ``description`` is excluded.
    exclude = resolvers._unprovided_exclude(product_models.Category, {"name"})
    assert "name" not in exclude
    assert "description" in exclude


@pytest.mark.django_db
def test_integrity_error_race_fallback_via_mocked_save():
    """A save-time ``IntegrityError`` race maps to the envelope, not a 500 (Major-2)."""
    schema, (CategoryT, _ItemT) = _build_item_schema()
    cat = product_models.Category.objects.create(name=_category_name())
    with mock.patch.object(
        product_models.Item,
        "save",
        side_effect=IntegrityError("races validate_constraints"),
    ):
        res = schema.execute_sync(
            _CREATE,
            variable_values={
                "d": {"name": "Racer", "categoryId": global_id_for(CategoryT, cat.pk)},
            },
        )
    assert res.errors is None, res.errors
    payload = res.data["createItem"]
    assert payload["node"] is None
    assert payload["errors"][0]["field"] == NON_FIELD_ERROR_KEY


@pytest.mark.django_db
def test_wrong_type_globalid_yields_field_error_no_cross_model_lookup():
    """An ``Item`` GlobalID passed to ``categoryId`` -> ``FieldError`` on ``categoryId`` (AR-H4)."""
    schema, (_CategoryT, ItemT) = _build_item_schema()
    cat = product_models.Category.objects.create(name=_category_name())
    item = product_models.Item.objects.create(name="Existing", category=cat)
    # An Item GlobalID with the SAME numeric pk as a real Category would silently
    # succeed under a naive pk strip; AR-H4 requires the type check to reject it.
    wrong_gid = global_id_for(ItemT, item.pk)
    res = schema.execute_sync(
        _CREATE,
        variable_values={"d": {"name": "New", "categoryId": wrong_gid}},
    )
    assert res.errors is None, res.errors
    payload = res.data["createItem"]
    assert payload["node"] is None
    assert payload["errors"][0]["field"] == "categoryId"
    # No cross-model coercion happened: no second Item was created under the
    # (collided) Category pk path.
    assert product_models.Item.objects.filter(name="New").count() == 0


@pytest.mark.django_db
def test_hidden_row_update_is_not_found_no_existence_leak():
    """An update of a row the target ``get_queryset`` hides -> not-found ``FieldError`` on ``id``."""

    @classmethod
    def _hide_private(cls, queryset, info, **kwargs):
        return queryset.filter(is_private=False)

    schema, (_CategoryT, ItemT) = _build_item_schema(item_get_queryset=_hide_private)
    cat = product_models.Category.objects.create(name=_category_name())
    hidden = product_models.Item.objects.create(name="Secret", category=cat, is_private=True)
    res = schema.execute_sync(
        _UPDATE,
        variable_values={"id": _item_gid(ItemT, hidden.pk), "d": {"name": "Leak"}},
    )
    assert res.errors is None, res.errors
    payload = res.data["updateItem"]
    assert payload["node"] is None
    assert payload["errors"][0]["field"] == "id"
    # The hidden row was not mutated.
    hidden.refresh_from_db()
    assert hidden.name == "Secret"


@pytest.mark.django_db
def test_refetch_skips_visibility_filter_after_authorized_write():
    """A create of an ``is_private``-shaped row still returns its object (Medium-1).

    The post-write re-fetch is by pk WITHOUT the visibility filter, so an
    authorized write of a row the ``get_queryset`` would hide still round-trips the
    actor's own write (non-null payload object).
    """

    @classmethod
    def _hide_private(cls, queryset, info, **kwargs):
        return queryset.filter(is_private=False)

    # Expose ``is_private`` on the input so the create can set it.
    class CategoryT(DjangoType, relay.Node):
        class Meta:
            model = product_models.Category
            fields = ("id", "name")
            primary = True

    ItemT = type(
        "ItemT",
        (DjangoType, relay.Node),
        {
            "Meta": type(
                "Meta",
                (),
                {"model": product_models.Item, "fields": ("id", "name"), "primary": True},
            ),
            "get_queryset": _hide_private,
        },
    )

    class CreateItem(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "create"
            permission_classes = [_AllowAll]

    @strawberry.type
    class Mutation:
        create_item = DjangoMutationField(CreateItem)

    finalize_django_types()
    schema = _schema(Mutation)
    cat = product_models.Category.objects.create(name=_category_name())
    res = schema.execute_sync(
        "mutation($d: ItemInput!){ createItem(data:$d){ node{ name } errors{ field } } }",
        variable_values={
            "d": {
                "name": "Hidden",
                "categoryId": global_id_for(CategoryT, cat.pk),
                "isPrivate": True,
            },
        },
    )
    assert res.errors is None, res.errors
    # Even though get_queryset(...) would hide is_private=True rows, the by-pk
    # re-fetch returns the just-written object.
    assert res.data["createItem"]["node"]["name"] == "Hidden"


@pytest.mark.django_db(transaction=True)
def test_transaction_rolls_back_when_post_save_step_fails():
    """A failure after ``save()`` inside the transaction rolls the write back (AR-M4)."""
    schema, (CategoryT, _ItemT) = _build_item_schema()
    cat = product_models.Category.objects.create(name=_category_name())
    # Force the post-save snapshot step to blow up so the atomic block aborts.
    with mock.patch.object(
        resolvers,
        "_refetch_optimized",
        side_effect=RuntimeError("boom after save"),
    ):
        res = schema.execute_sync(
            _CREATE,
            variable_values={
                "d": {"name": "Rollback", "categoryId": global_id_for(CategoryT, cat.pk)},
            },
        )
    # The RuntimeError surfaces as a top-level GraphQL error...
    assert res.errors is not None
    # ...and the write was rolled back: no row persisted.
    assert not product_models.Item.objects.filter(name="Rollback").exists()


@pytest.mark.django_db
def test_sync_misuse_async_get_queryset_from_sync_path():
    """A sync update over a type with an ``async def get_queryset`` raises ``SyncMisuseError``."""

    async def _async_get_queryset(cls, queryset, info, **kwargs):
        return queryset

    ItemT = type(
        "ItemT",
        (DjangoType, relay.Node),
        {
            "Meta": type(
                "Meta",
                (),
                {"model": product_models.Item, "fields": ("id", "name"), "primary": True},
            ),
            "get_queryset": classmethod(_async_get_queryset),
        },
    )

    class CategoryT(DjangoType, relay.Node):
        class Meta:
            model = product_models.Category
            fields = ("id", "name")
            primary = True

    class UpdateItem(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "update"
            permission_classes = [_AllowAll]

    finalize_django_types()
    cat = product_models.Category.objects.create(name=_category_name())
    item = product_models.Item.objects.create(name="X", category=cat)
    # Drive the sync pipeline directly (the locate path runs get_queryset).
    with pytest.raises(SyncMisuseError):
        resolvers.resolve_mutation_sync(
            UpdateItem,
            info=None,
            data=strawberry.UNSET,
            id=str(global_id_for(ItemT, item.pk)),
        )


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_async_pipeline_create_happy_path():
    """The same create through ``await schema.execute`` (async surface) succeeds.

    ``transaction=True`` is load-bearing, not cosmetic. The async pipeline runs
    its whole ORM body - the ``transaction.atomic()`` write included - inside one
    ``sync_to_async(thread_sensitive=True)`` call (AR-M4), so the ``save()``
    commits on asgiref's executor-thread connection, NOT the main-thread
    connection the plain ``django_db`` marker wraps in a rollback transaction.
    Under plain ``django_db`` that committed write escapes the per-test rollback
    and LEAKS into the next test's database (a category + item survive), which
    then corrupts a later read-side optimizer execution (the leaked item has a
    category the read test's visibility hook does not match, so the forward FK
    re-raises ``RelatedObjectDoesNotExist``). ``transaction=True`` is the
    suite-wide convention for every async-ORM test (see ``test_list_field.py`` /
    ``test_relay_connection.py``): real commits with a flush/truncate teardown
    that reaps the cross-thread-committed rows. The cross-test leak this prevents
    is pinned order-independently by
    ``test_async_mutation_does_not_leak_into_later_read_optimizer_execution``.
    """
    schema, (CategoryT, _ItemT) = _build_item_schema()
    cat = await product_models.Category.objects.acreate(name=_category_name())
    res = await schema.execute(
        _CREATE,
        variable_values={
            "d": {"name": "AsyncWidget", "categoryId": global_id_for(CategoryT, cat.pk)},
        },
    )
    assert res.errors is None, res.errors
    assert res.data["createItem"]["node"]["name"] == "AsyncWidget"
    assert await product_models.Item.objects.filter(name="AsyncWidget").aexists()


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_async_mutation_does_not_leak_into_later_read_optimizer_execution():
    """An async mutation must not corrupt a later read-side optimizer execution (spec-036 FV-1).

    The durable regression pin for FV-1. ROOT CAUSE (bisected, not the
    ContextVar-lifecycle hypothesis): the async pipeline runs its whole ORM body -
    the ``transaction.atomic()`` write included - inside one
    ``sync_to_async(thread_sensitive=True)`` call (AR-M4), so the ``save()``
    commits on asgiref's executor-thread connection, NOT the main-thread
    connection that the plain ``django_db`` marker wraps in a rollback
    transaction. Under plain ``django_db`` that committed row escapes per-test
    rollback and persists into the NEXT test's database. The read-side optimizer
    suite (``test_extension.py``) then plans a relation whose visibility-narrowed
    child queryset does not match the leaked row's category, and the forward-FK
    resolver re-raises ``RelatedObjectDoesNotExist`` - the FV-1 symptom. The
    optimizer's per-execution ContextVars are NOT leaked (``on_execute`` resets
    cleanly across the ``sync_to_async`` hop - verified); the corruption is leaked
    ROWS, a test-isolation defect cured by the suite-wide ``transaction=True``
    convention for async-ORM tests.

    This pin reproduces the async-mutation-THEN-read sequence in ONE process and
    is order-independent in BOTH directions:

    * **Canary (catches a prior leaker):** under ``transaction=True`` this test
      reads with a connection that sees committed rows, so an entry guard asserts
      the products tables are empty - if an EARLIER async test reverted to plain
      ``django_db`` and leaked, that committed row is visible here and trips the
      guard, regardless of which leaker ran first.
    * **Self-contained (catches its own regression):** it runs an async create
      then a read-side optimizer execution over a node type whose category target
      carries a user-narrowing ``get_queryset`` (the exact read shape that
      surfaced FV-1), asserting the read plans + resolves the relation, sees
      exactly the row it wrote, and round-trips the relation. Flip this test's own
      decorator to plain ``django_db`` and the cross-test leak it documents
      returns (proven during the fix).
    """
    # Canary entry guard: under ``transaction=True`` this connection sees any
    # committed-but-unrolled-back rows. A non-empty table here means an earlier
    # async-ORM test escaped its rollback (the FV-1 leak) - fail loudly with the
    # offending rows rather than letting the corruption surface downstream.
    leaked_cats = await sync_to_async(
        lambda: list(product_models.Category.objects.values_list("name", flat=True)),
        thread_sensitive=True,
    )()
    leaked_items = await sync_to_async(
        lambda: list(product_models.Item.objects.values_list("name", flat=True)),
        thread_sensitive=True,
    )()
    assert leaked_cats == [] and leaked_items == [], (
        f"FV-1 leak: an earlier async-ORM test committed rows that escaped "
        f"per-test rollback (categories={leaked_cats}, items={leaked_items}). "
        f"Async-ORM tests must use @pytest.mark.django_db(transaction=True)."
    )

    class CategoryT(DjangoType, relay.Node):
        class Meta:
            model = product_models.Category
            fields = ("id", "name")
            primary = True

        @classmethod
        def get_queryset(cls, queryset, info, **kwargs):
            # Narrow the category by a request-user-derived predicate so a leaked
            # row's category (created under a DIFFERENT name) would NOT match,
            # reproducing the read-side ``RelatedObjectDoesNotExist`` FV-1 hit.
            user_name = getattr(getattr(info.context, "user", None), "name", None)
            if user_name is not None:
                queryset = queryset.filter(name=user_name)
            return queryset

    class ItemT(DjangoType, relay.Node):
        class Meta:
            model = product_models.Item
            fields = ("id", "name", "category")
            primary = True

    class CreateItem(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "create"
            permission_classes = [_AllowAll]

    def _all_items(self):
        return product_models.Item.objects.all()

    # ``from __future__ import annotations`` makes a ``-> list[ItemT]`` string
    # annotation unresolvable from module scope (``ItemT`` is function-local), so
    # set the return annotation to the real ``list[ItemT]`` type object before
    # handing the resolver to ``strawberry.field`` - the read field still types to
    # the list of the local node type without depending on global name lookup.
    _all_items.__annotations__["return"] = list[ItemT]

    @strawberry.type
    class Query:
        all_items = strawberry.field(resolver=_all_items)

    @strawberry.type
    class Mutation:
        create_item = DjangoMutationField(CreateItem)

    finalize_django_types()
    schema = strawberry.Schema(
        query=Query,
        mutation=Mutation,
        extensions=[DjangoOptimizerExtension],
    )

    user_name = _category_name()
    cat = await product_models.Category.objects.acreate(name=user_name)
    create = (
        "mutation($d: ItemInput!){ createItem(data:$d){ "
        "node{ name category{ name } } errors{ field messages } } }"
    )
    res = await schema.execute(
        create,
        variable_values={
            "d": {"name": "LeakProbe", "categoryId": global_id_for(CategoryT, cat.pk)},
        },
    )
    assert res.errors is None, res.errors
    assert res.data["createItem"]["node"]["name"] == "LeakProbe"

    # The read-side optimizer execution: the category target's user-narrowing
    # get_queryset means a leaked item (whose category was created under a name
    # that does not match this request's user) would re-raise
    # RelatedObjectDoesNotExist when the optimizer plans the relation. This is the
    # exact read shape FV-1 corrupted, run as a SYNC execution (the failing
    # ``test_extension.py`` read used ``schema.execute_sync``); it is driven
    # through ``sync_to_async`` so the sync ORM runs off the event loop, the
    # suite's standard async-test idiom for a synchronous ORM read.
    ctx = SimpleNamespace(user=SimpleNamespace(name=user_name))
    read = await sync_to_async(schema.execute_sync, thread_sensitive=True)(
        "{ allItems { name category { name } } }",
        context_value=ctx,
    )
    assert read.errors is None, read.errors
    # Exactly the one row this test wrote - no phantom leaked rows.
    names = sorted(row["name"] for row in read.data["allItems"])
    assert names == ["LeakProbe"], names
    # The relation round-trips through the optimizer plan (the FV-1 failure mode
    # is a None relation -> RelatedObjectDoesNotExist; here it resolves).
    assert read.data["allItems"][0]["category"]["name"] == user_name


# ---------------------------------------------------------------------------
# Library Book/Genre M2M fixtures (AR-M1 replace/clear/omit)
# ---------------------------------------------------------------------------


def _build_book_schema():
    """Declare Book/Genre/Shelf primaries + create/update mutations over the Book M2M."""

    class GenreT(DjangoType, relay.Node):
        class Meta:
            model = library_models.Genre
            fields = ("id", "name")
            primary = True

    class ShelfT(DjangoType, relay.Node):
        class Meta:
            model = library_models.Shelf
            fields = ("id", "code")
            primary = True

    class BookT(DjangoType, relay.Node):
        class Meta:
            model = library_models.Book
            fields = ("id", "title")
            primary = True

    class CreateBook(DjangoMutation):
        class Meta:
            model = library_models.Book
            operation = "create"
            fields = ("title", "shelf", "genres")
            permission_classes = [_AllowAll]

    class UpdateBook(DjangoMutation):
        class Meta:
            model = library_models.Book
            operation = "update"
            permission_classes = [_AllowAll]

    @strawberry.type
    class Mutation:
        create_book = DjangoMutationField(CreateBook)
        update_book = DjangoMutationField(UpdateBook)

    finalize_django_types()
    return _schema(Mutation), (GenreT, ShelfT, BookT)


def _make_branch_shelf():
    branch = library_models.Branch.objects.create(name="Main")
    return library_models.Shelf.objects.create(code="S1", branch=branch)


@pytest.mark.django_db
def test_m2m_replace_on_provide():
    """A provided genre list replaces the M2M set on create (AR-M1)."""
    schema, (GenreT, ShelfT, _BookT) = _build_book_schema()
    shelf = _make_branch_shelf()
    g1 = library_models.Genre.objects.create(name="Sci-Fi")
    g2 = library_models.Genre.objects.create(name="Fantasy")
    res = schema.execute_sync(
        "mutation($d: BookGenresShelfTitleInput!){ createBook(data:$d){ "
        "node{ id title } errors{ field messages } } }",
        variable_values={
            "d": {
                "title": "Dune",
                "shelfId": global_id_for(ShelfT, shelf.pk),
                "genres": [global_id_for(GenreT, g1.pk), global_id_for(GenreT, g2.pk)],
            },
        },
    )
    assert res.errors is None, res.errors
    assert res.data["createBook"]["errors"] == []
    book = library_models.Book.objects.get(title="Dune")
    assert set(book.genres.values_list("name", flat=True)) == {"Sci-Fi", "Fantasy"}


@pytest.mark.django_db
def test_m2m_clear_on_empty_and_unchanged_on_omit():
    """A provided empty list clears the M2M; an omitted M2M leaves it unchanged (AR-M1)."""
    schema, (_GenreT, _ShelfT, BookT) = _build_book_schema()
    shelf = _make_branch_shelf()
    g1 = library_models.Genre.objects.create(name="Sci-Fi")
    book = library_models.Book.objects.create(title="Seeded", shelf=shelf)
    book.genres.set([g1])

    update_q = (
        "mutation($id: ID!, $d: BookPartialInput!){ updateBook(id:$id, data:$d){ "
        "node{ title } errors{ field } } }"
    )
    book_gid = global_id_for(BookT, book.pk)

    # Omit genres: unchanged (still has g1).
    res = schema.execute_sync(
        update_q,
        variable_values={"id": book_gid, "d": {"title": "Renamed"}},
    )
    assert res.errors is None, res.errors
    book.refresh_from_db()
    assert set(book.genres.values_list("name", flat=True)) == {"Sci-Fi"}

    # Provide empty list: cleared.
    res = schema.execute_sync(update_q, variable_values={"id": book_gid, "d": {"genres": []}})
    assert res.errors is None, res.errors
    assert book.genres.count() == 0


# ---------------------------------------------------------------------------
# Scalar field named ``<x>_id`` regression (spec-036 M3-1 / L3-1)
#
# ``library.TaggedItem`` has a *scalar* ``object_id`` (a ``PositiveIntegerField``,
# emitted by the input generator) AND a ``GenericForeignKey`` ``content_object``.
# The decode index / provided-name mapping must NOT reverse ``object_id`` to a
# relation field by a blind ``_id`` suffix strip (M3-1), and must NOT index the
# GFK as a decode-able FK (L3-1). Both are reasoned from the relation field index,
# not a string heuristic.
# ---------------------------------------------------------------------------


def _build_tagged_item_schema():
    """Declare a TaggedItem primary + an update mutation; return (schema, TaggedItemT)."""

    class TaggedItemT(DjangoType, relay.Node):
        class Meta:
            model = library_models.TaggedItem
            fields = ("id", "tag", "object_id")
            primary = True

    class UpdateTaggedItem(DjangoMutation):
        class Meta:
            model = library_models.TaggedItem
            operation = "update"
            permission_classes = [_AllowAll]

    @strawberry.type
    class Mutation:
        update_tagged_item = DjangoMutationField(UpdateTaggedItem)

    finalize_django_types()
    return _schema(Mutation), TaggedItemT


@pytest.mark.django_db
def test_partial_update_validates_scalar_field_named_id_suffix():
    """A scalar field literally named ``<x>_id`` IS validated on partial update (spec-036 M3-1).

    ``TaggedItem.object_id`` is a scalar ``PositiveIntegerField``. A partial update
    providing an invalid value (``-5``) must surface as a field-keyed ``FieldError``
    on ``object_id`` from ``full_clean`` - NOT skipped from validation (which the
    old ``_id`` suffix-strip caused: ``object_id`` was mangled to ``object``, read
    as unprovided, excluded from ``full_clean``, and the invalid value slipped to
    the DB as a mis-labeled ``IntegrityError`` / ``"__all__"`` envelope).
    """
    from django.contrib.contenttypes.models import ContentType

    schema, TaggedItemT = _build_tagged_item_schema()
    ct = ContentType.objects.get_for_model(library_models.Branch)
    branch = library_models.Branch.objects.create(name="RegressionBranch")
    tagged = library_models.TaggedItem.objects.create(
        tag="alpha",
        content_type=ct,
        object_id=branch.pk,
    )
    update_q = (
        "mutation($id: ID!, $d: TaggedItemPartialInput!){ "
        "updateTaggedItem(id:$id, data:$d){ "
        "node{ tag } errors{ field messages } } }"
    )
    res = schema.execute_sync(
        update_q,
        variable_values={"id": global_id_for(TaggedItemT, tagged.pk), "d": {"objectId": -5}},
    )
    assert res.errors is None, res.errors
    payload = res.data["updateTaggedItem"]
    # The invalid scalar surfaces as a field-keyed FieldError on ``object_id`` -
    # NOT a swallowed write, NOT a mis-labeled ``"__all__"`` uniqueness envelope.
    assert payload["node"] is None
    fields = [e["field"] for e in payload["errors"]]
    assert "object_id" in fields, payload["errors"]
    assert NON_FIELD_ERROR_KEY not in fields, payload["errors"]
    # The invalid value never reached the DB.
    tagged.refresh_from_db()
    assert tagged.object_id == branch.pk


def test_provided_attr_names_keeps_scalar_id_suffix_field():
    """``_provided_attr_names`` keeps a scalar ``<x>_id`` field under its real name (spec-036 M3-1).

    The FK reversal is index-driven: ``content_type_id`` (a real FK attr) maps to
    ``content_type``, while ``object_id`` (a scalar) stays ``object_id`` - never
    mangled to ``object``.
    """
    provided = resolvers._provided_attr_names(
        library_models.TaggedItem,
        {"object_id": 5, "tag": "x", "content_type_id": 1},
        [],
    )
    assert provided == {"object_id", "tag", "content_type"}


def test_relation_field_index_excludes_generic_foreign_key():
    """``_relation_field_index`` does not index a ``GenericForeignKey`` as a FK (spec-036 L3-1).

    A GFK reports ``is_relation=True`` but ``column=None`` / ``related_model=None``,
    so it must never enter ``fk_by_attr`` (where ``_wrong_type_field_error`` would
    later compare a decoded model against ``related_model=None``). The real
    ``content_type`` FK is still indexed.
    """
    fk_by_attr, _m2m_by_name = resolvers._relation_field_index(library_models.TaggedItem)
    assert "content_object_id" not in fk_by_attr
    assert "content_type_id" in fk_by_attr
