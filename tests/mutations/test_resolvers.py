"""Write-pipeline resolver tests.

Internals a live fakeshop request cannot express: custom ``relay.NodeID`` write
locate (shipped ``CategoryType`` uses pk; changing it would retarget every
Category GlobalID), ``_unprovided_exclude`` / ``coerce_lookup_id`` helpers,
mocked ``IntegrityError`` race, ``async def get_queryset`` ``SyncMisuseError``,
async-row leak isolation, Relay M2M hide on a second ``Genre`` primary
(shipped ``GenreType`` has no hide hook; a second primary cannot coexist in the
live process), raw-pk M2M *update* (no shipped ``updateShelf``), unregistered
primary existence-only decode, ``TaggedItem.object_id`` GFK indexing,
relation-override visibility (no shipped override declares a relation field, so
the composite is package-only), pipeline pk-drift, and ``ScalarSpecimen`` writes
(the scalars app exposes no ``ScalarSpecimen`` mutation). Consumer-visible
create/update/delete, empty-name ``full_clean``, unresolvable relation ids, M2M
replace/clear/omit, choice-enum unwrap, raw-pk create visibility, the
``PROTECT`` / ``RESTRICT`` refused delete and the ``blank=True, null=False`` FK
null guard live in ``examples/fakeshop/test_query/test_products_api.py`` and
``examples/fakeshop/test_query/test_library_api.py``; file-column update omit /
replace / explicit null live in ``examples/fakeshop/test_query/test_uploads_api.py``. Atomicity live in
``examples/fakeshop/test_query/test_mutation_atomicity.py``.
"""

from __future__ import annotations

import itertools
from types import SimpleNamespace
from unittest import mock

import pytest
import strawberry
from apps.library import models as library_models
from apps.products import models as product_models
from apps.scalars import models as scalars_models
from asgiref.sync import sync_to_async
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from strawberry import relay

from django_strawberry_framework import (
    DjangoMutation,
    DjangoMutationField,
    DjangoOptimizerExtension,
    DjangoSchema,
    DjangoType,
    finalize_django_types,
)
from django_strawberry_framework.mutations import resolvers
from django_strawberry_framework.mutations.inputs import NON_FIELD_ERROR_KEY
from django_strawberry_framework.registry import registry
from django_strawberry_framework.testing.relay import global_id_for
from django_strawberry_framework.utils.querysets import SyncMisuseError
from django_strawberry_framework.utils.write_transaction import managed_write_transaction


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
    optimizer = DjangoOptimizerExtension()
    return DjangoSchema(
        query=_Query,
        mutation=mutation_type,
        extensions=[lambda: optimizer],
    )


# ---------------------------------------------------------------------------
# Products Item/Category fixtures (FK + unique_item_per_category)
# ---------------------------------------------------------------------------


def _build_item_schema(*, category_get_queryset=None, input_cls=None):
    """Declare Item/Category primaries + create/update/delete mutations; return (schema, types)."""

    category_body: dict = {
        "Meta": type(
            "Meta",
            (),
            {"model": product_models.Category, "fields": ("id", "name"), "primary": True},
        ),
    }
    if category_get_queryset is not None:
        category_body["get_queryset"] = category_get_queryset
    CategoryT = type("CategoryT", (DjangoType, relay.Node), category_body)

    ItemT = type(
        "ItemT",
        (DjangoType, relay.Node),
        {
            "Meta": type(
                "Meta",
                (),
                {
                    "model": product_models.Item,
                    "fields": ("id", "name", "category"),
                    "primary": True,
                },
            ),
        },
    )

    create_meta = {
        "model": product_models.Item,
        "operation": "create",
        "permission_classes": [_AllowAll],
    }
    if input_cls is not None:
        create_meta["input_class"] = input_cls
    update_meta = {
        "model": product_models.Item,
        "operation": "update",
        "permission_classes": [_AllowAll],
    }
    delete_meta = {
        "model": product_models.Item,
        "operation": "delete",
        "permission_classes": [_AllowAll],
    }

    CreateItem = type("CreateItem", (DjangoMutation,), {"Meta": type("Meta", (), create_meta)})
    UpdateItem = type("UpdateItem", (DjangoMutation,), {"Meta": type("Meta", (), update_meta)})
    DeleteItem = type("DeleteItem", (DjangoMutation,), {"Meta": type("Meta", (), delete_meta)})

    @strawberry.type
    class Mutation:
        create_item = DjangoMutationField(CreateItem)
        update_item = DjangoMutationField(UpdateItem)
        delete_item = DjangoMutationField(DeleteItem)

    finalize_django_types()
    return _schema(Mutation), (CategoryT, ItemT)


def assert_mutation_field_error(result, payload_key, field):
    """Assert the common in-band mutation error envelope.

    Pins the shape every in-band failure test shares: no top-level GraphQL errors
    (the failure is in-band), a null object slot, and exactly one ``FieldError`` on
    ``field``. Returns the payload so a caller can add test-specific assertions
    (e.g. "no row was written"); those DB side-effect checks stay inline.
    """
    assert result.errors is None, result.errors
    payload = result.data[payload_key]
    assert payload["node"] is None
    assert [e["field"] for e in payload["errors"]] == [field], payload["errors"]
    return payload


_CREATE = (
    "mutation($d: ItemInput!){ createItem(data:$d){ "
    "node{ id name category{ name } } errors{ field messages } } }"
)
_DELETE = (
    "mutation($id: ID!){ deleteItem(id:$id){ "
    "node{ id name category{ name } } errors{ field messages } } }"
)


def _item_gid(item_type: type, pk) -> str:
    return global_id_for(item_type, pk)


# ---------------------------------------------------------------------------
# Custom ``relay.NodeID`` write-side
#
# When a primary type encodes a NON-pk column as its Relay id
# (``name: relay.NodeID[str]``), the GlobalID a client holds carries that column's
# value, not the pk. ``decode_model_global_id`` -> ``_resolve_real_pk`` must map it
# to the row's real pk BEFORE the write locate runs ``get(pk=...)``. The unit test
# in ``tests/test_relay_node_field.py`` pins the decode in isolation; these pin a
# real update / delete CONSUMER of that decoded pk end-to-end, with the decoy row
# seeded so its pk's string form IS the target row's ``name`` - the exact pk/name
# confusion the fix guards (the pre-fix value flowed straight into ``get(pk=...)``
# and hit the wrong row).
# ---------------------------------------------------------------------------

# ``name`` is consumed as the Relay id (``relay.NodeID[str]``), so it surfaces as the
# ``id`` field, not a ``name`` field - select ``id`` (the encoded GlobalID) + a plain
# writable column (``description``).
_CATEGORY_UPDATE = (
    "mutation($id: ID!, $d: CategoryPartialInput!){ updateCategory(id:$id, data:$d){ "
    "node{ id description } errors{ field messages } } }"
)
_CATEGORY_DELETE = (
    "mutation($id: ID!){ deleteCategory(id:$id){ node{ id } errors{ field messages } } }"
)


def _build_category_node_schema():
    """Category primary type with ``name: relay.NodeID[str]`` + update/delete mutations.

    The Relay id encodes the non-pk ``name`` column, so the write-side locate must
    resolve the GlobalID payload (a ``name`` string) to the row's real pk via
    ``_resolve_real_pk`` before ``get(pk=...)`` runs. Returns ``(schema, CategoryNode)``
    so the caller can mint the client-held GlobalID with ``global_id_for``.
    """

    class CategoryNode(DjangoType, relay.Node):
        name: relay.NodeID[str]

        class Meta:
            model = product_models.Category
            fields = ("id", "name", "description")
            primary = True

    class UpdateCategory(DjangoMutation):
        class Meta:
            model = product_models.Category
            operation = "update"
            permission_classes = [_AllowAll]

    class DeleteCategory(DjangoMutation):
        class Meta:
            model = product_models.Category
            operation = "delete"
            permission_classes = [_AllowAll]

    @strawberry.type
    class Mutation:
        update_category = DjangoMutationField(UpdateCategory)
        delete_category = DjangoMutationField(DeleteCategory)

    finalize_django_types()
    return _schema(Mutation), CategoryNode


@pytest.mark.django_db
def test_update_custom_node_id_resolves_payload_to_real_pk_not_wrong_row():
    """A write through a custom ``relay.NodeID[str]`` updates the NAME-matched row, not the pk-coincident one.

    Shipped ``CategoryType`` uses the pk as Relay id; retargeting it would change
    every Category GlobalID. Decode isolation is
    ``tests/test_relay_node_field.py``; this is the write consumer. Live
    ``updateItem`` locates by pk GlobalID
    (``test_products_api.py::test_update_item_non_colliding_partial_update``).
    """
    schema, CategoryNode = _build_category_node_schema()
    decoy = product_models.Category.objects.create(name="decoy", description="decoy-untouched")
    target = product_models.Category.objects.create(name=str(decoy.pk), description="before")
    assert target.pk != decoy.pk and target.name == str(decoy.pk)

    gid = global_id_for(CategoryNode, target.name)
    res = schema.execute_sync(
        _CATEGORY_UPDATE,
        variable_values={"id": gid, "d": {"description": "after"}},
    )
    assert res.errors is None, res.errors
    node = res.data["updateCategory"]["node"]
    assert node["description"] == "after"
    # The returned id is rebuilt from the (unchanged) ``name``, so it round-trips to
    # the same GlobalID - the node returned is the target, not the pk-coincident decoy.
    assert node["id"] == gid

    target.refresh_from_db()
    decoy.refresh_from_db()
    assert target.description == "after"  # the row whose NAME matched the payload
    assert decoy.description == "decoy-untouched"  # the pk-coincident row is untouched


@pytest.mark.django_db
def test_custom_node_id_real_pk_lookup_uses_pinned_alias(monkeypatch):
    """A custom NodeID lookup forwards the mutation's pinned database alias.

    The NodeID payload identifies a non-pk column, so
    ``decode_model_global_id`` must resolve that value to a real pk before the
    mutation locates its row. The lookup is part of the write transaction's
    alias contract: a router may send reads to one alias and writes to another,
    and resolving the NodeID through the default manager would miss a row that
    exists only on the write alias. This package-level seam test pins the
    forwarding without requiring a second test database; the live sharded
    fakeshop suite exercises the same contract end to end.
    """
    _schema, CategoryNode = _build_category_node_schema()
    target = product_models.Category.objects.create(name="alias-node-id", description="before")
    gid = global_id_for(CategoryNode, target.name)
    manager = product_models.Category._default_manager
    using = mock.Mock(wraps=manager.using)
    monkeypatch.setattr(manager, "using", using)

    node_id, error = resolvers.coerce_lookup_id(gid, CategoryNode, using="default")

    assert error is None
    assert node_id == target.pk
    using.assert_called_once_with("default")


@pytest.mark.django_db
def test_delete_custom_node_id_resolves_payload_to_real_pk_not_wrong_row():
    """A delete through a custom ``relay.NodeID[str]`` removes the NAME-matched row, not the pk-coincident one.

    The delete twin of the update case: the located instance comes from the resolved
    real pk, so deleting via a GlobalID whose payload is the target's ``name`` removes
    the target - while the row whose pk's string form equals that ``name`` survives.
    """
    schema, CategoryNode = _build_category_node_schema()
    decoy = product_models.Category.objects.create(name="decoy-del", description="x")
    target = product_models.Category.objects.create(name=str(decoy.pk), description="doomed")
    assert target.pk != decoy.pk and target.name == str(decoy.pk)

    gid = global_id_for(CategoryNode, target.name)
    res = schema.execute_sync(_CATEGORY_DELETE, variable_values={"id": gid})
    assert res.errors is None, res.errors
    # The snapshot id (preserved for cache eviction) decodes to the target's name.
    assert res.data["deleteCategory"]["node"]["id"] == gid
    # The NAME-matched target is gone; the row whose pk string equals that name survives.
    assert not product_models.Category.objects.filter(pk=target.pk).exists()
    assert product_models.Category.objects.filter(pk=decoy.pk).exists()


def test_unprovided_exclude_keeps_constrained_co_member_drops_unrelated():
    """``_unprovided_exclude`` pins the constrained-co-member carve-out on ``Item``.

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


@pytest.mark.parametrize(
    "raw_id",
    ["5", "not-a-global-id", 5],
    ids=["raw-pk-string", "garbage", "non-string"],
)
def test_coerce_lookup_id_rejects_non_globalid(raw_id):
    """A non-GlobalID ``id:`` is a ``FieldError`` on ``id`` before any pk lookup.

    Live ``updateItem`` covers the string arms over HTTP
    (``test_products_api.py::test_update_item_malformed_id_is_field_error_no_coercion_crash``).
    GraphQL ``ID`` never delivers a Python ``int``, so the non-string arm has no
    wire shape; this helper pin is the remaining coverage.
    """

    class ItemT(DjangoType, relay.Node):
        class Meta:
            model = product_models.Item
            fields = ("id", "name")
            primary = True

    node_id, error = resolvers.coerce_lookup_id(raw_id, ItemT)
    assert node_id is None
    assert error is not None and error.field == "id"


@pytest.mark.django_db
def test_integrity_error_race_fallback_via_mocked_save():
    """A save-time ``IntegrityError`` race maps to the envelope, not a 500."""
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
    # The catch is broad (``except IntegrityError``), so the message is the honest
    # superset, not an over-claimed "uniqueness".
    assert payload["errors"][0]["messages"] == ["A database constraint was violated."]


@pytest.mark.django_db
def test_globalid_relation_override_flows_through_visibility_contract():
    """A ``GlobalID`` relation override is still relation-visibility-checked (Decision 10).

    The bind-time type-lock (``sets.py::_validate_relation_override_types``) forces a
    relation override to keep the generated ``relay.GlobalID`` id type precisely so the
    override CANNOT bypass the id type-check / Decision-10 visibility contract a
    raw-pk override would have skipped. This pins the end-to-end guarantee: a
    ``createItem`` whose ``categoryId`` names a ``Category`` hidden by
    ``Category.get_queryset`` is a ``FieldError`` on ``categoryId`` (hidden
    indistinguishable from missing, no existence leak) - even though ``categoryId``
    came from a consumer ``input_class`` override, not the generated input. A raw-pk
    override would have been passed through unchecked and silently attached the
    unseeable row; the type-lock is what guarantees this path is reached.

    No shipped override declares a relation field, so the composite is package-only.
    """

    @classmethod
    def _hide_private(cls, queryset, info):
        return queryset.filter(is_private=False)

    @strawberry.input
    class GidItemInput:
        category_id: relay.GlobalID = strawberry.field(description="custom category ref")

    schema, (CategoryT, _ItemT) = _build_item_schema(
        category_get_queryset=_hide_private,
        input_cls=GidItemInput,
    )
    hidden = product_models.Category.objects.create(name=_category_name(), is_private=True)
    res = schema.execute_sync(
        _CREATE,
        variable_values={
            "d": {"name": "New", "categoryId": global_id_for(CategoryT, hidden.pk)},
        },
    )
    assert_mutation_field_error(res, "createItem", "categoryId")
    assert product_models.Item.objects.filter(name="New").count() == 0


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
    # Drive the sync pipeline directly (the locate path runs get_queryset); the
    # managed-transaction context stands in for the DjangoSchema execution the
    # direct call bypasses.
    with (
        managed_write_transaction("default"),
        transaction.atomic(),
        pytest.raises(SyncMisuseError),
    ):
        resolvers.resolve_mutation_sync(
            UpdateItem,
            info=None,
            data=strawberry.UNSET,
            id=str(global_id_for(ItemT, item.pk)),
        )


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_async_mutation_does_not_leak_into_later_read_optimizer_execution():
    """An async mutation must not corrupt a later read-side optimizer execution (spec-036 FV-1).

    The durable regression pin for FV-1. ROOT CAUSE (bisected, not the
    ContextVar-lifecycle hypothesis): the async pipeline runs its whole ORM body -
    the ``transaction.atomic()`` write included - inside one
    ``sync_to_async(thread_sensitive=True)`` call, so the ``save()``
    commits on asgiref's executor-thread connection, NOT the main-thread
    connection that the plain ``django_db`` marker wraps in a rollback
    transaction. Under plain ``django_db`` that committed row escapes per-test
    rollback and persists into the NEXT test's database. The read-side optimizer
    suite (``test_extension.py``) then plans a relation whose visibility-narrowed
    child queryset does not match the leaked row's category, and the forward-FK
    resolver re-raises ``RelatedObjectDoesNotExist``. The
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
    optimizer = DjangoOptimizerExtension()
    schema = DjangoSchema(
        query=Query,
        mutation=Mutation,
        extensions=[lambda: optimizer],
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
# Library Book/Genre M2M: hidden Relay member (GenreType has no hide hook)
# ---------------------------------------------------------------------------


def _build_book_schema(*, genre_get_queryset=None):
    """Declare Book/Genre/Shelf primaries + a create mutation over the Book M2M."""

    genre_body: dict = {
        "Meta": type(
            "Meta",
            (),
            {"model": library_models.Genre, "fields": ("id", "name"), "primary": True},
        ),
    }
    if genre_get_queryset is not None:
        genre_body["get_queryset"] = genre_get_queryset
    GenreT = type("GenreT", (DjangoType, relay.Node), genre_body)

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

    @strawberry.type
    class Mutation:
        create_book = DjangoMutationField(CreateBook)

    finalize_django_types()
    return _schema(Mutation), (GenreT, ShelfT, BookT)


def _make_branch_shelf():
    branch = library_models.Branch.objects.create(name="Main")
    return library_models.Shelf.objects.create(code="S1", branch=branch)


_CREATE_BOOK = (
    "mutation($d: BookGenresShelfTitleInput!){ createBook(data:$d){ "
    "node{ id title } errors{ field messages } } }"
)


@pytest.mark.django_db
def test_m2m_hidden_related_id_is_field_error():
    """An M2M id for a row the related type hides -> ``FieldError`` on the M2M field.

    Live ``createBookViaCustomInput`` covers visible Genre GlobalIDs. Shipped
    ``GenreType`` has no ``get_queryset``; adding one (even flag-gated) would
    change every genre read. A second primary ``Genre`` type cannot coexist with
    the shipped type in the live process, so the hide arm stays on a throwaway
    schema. Hidden indistinguishable from missing; no book is written.
    """

    @classmethod
    def _hide_secret(cls, queryset, info):
        return queryset.exclude(name="Secret")

    schema, (GenreT, ShelfT, _BookT) = _build_book_schema(genre_get_queryset=_hide_secret)
    shelf = _make_branch_shelf()
    visible = library_models.Genre.objects.create(name="Sci-Fi")
    hidden = library_models.Genre.objects.create(name="Secret")
    res = schema.execute_sync(
        _CREATE_BOOK,
        variable_values={
            "d": {
                "title": "Dune",
                "shelfId": global_id_for(ShelfT, shelf.pk),
                "genres": [global_id_for(GenreT, visible.pk), global_id_for(GenreT, hidden.pk)],
            },
        },
    )
    assert_mutation_field_error(res, "createBook", "genres")
    assert not library_models.Book.objects.filter(title="Dune").exists()


# ---------------------------------------------------------------------------
# Raw-pk M2M update existence check (no shipped updateShelf)
# ---------------------------------------------------------------------------


def _build_book_raw_m2m_schema():
    """Declare a NON-Relay ``Genre`` primary so ``Book.genres`` is a raw-pk ``list[Int]`` M2M."""
    GenreT = type(
        "GenreT",
        (DjangoType,),
        {
            "Meta": type(
                "Meta",
                (),
                {"model": library_models.Genre, "fields": ("id", "name"), "primary": True},
            ),
        },
    )

    class BranchT(DjangoType, relay.Node):
        class Meta:
            model = library_models.Branch
            fields = ("id", "name")
            primary = True

    class ShelfT(DjangoType, relay.Node):
        class Meta:
            model = library_models.Shelf
            fields = ("id", "code", "branch")
            primary = True

    class BookT(DjangoType, relay.Node):
        class Meta:
            model = library_models.Book
            fields = (
                "id",
                "title",
                "shelf",
                "genres",
            )
            primary = True

    class UpdateBook(DjangoMutation):
        class Meta:
            model = library_models.Book
            operation = "update"
            permission_classes = [_AllowAll]

    @strawberry.type
    class Mutation:
        update_book = DjangoMutationField(UpdateBook)

    finalize_django_types()
    return _schema(Mutation), (GenreT, ShelfT, BookT)


@pytest.mark.django_db
def test_update_raw_pk_m2m_nonexistent_id_is_field_error_no_dangling_row():
    """A nonexistent raw-pk M2M id on update -> ``FieldError`` on the M2M field, set unchanged.

    Live ``createShelf`` covers the create arm
    (``test_library_api.py::test_create_shelf_model_mutation_nonexistent_alt_branch_is_field_error``).
    Fakeshop ships no ``updateShelf`` / ``updateBook`` with a raw-pk M2M, so the
    update arm stays on a throwaway non-Relay ``Genre`` primary.
    """
    schema, (_GenreT, _ShelfT, BookT) = _build_book_raw_m2m_schema()
    shelf = _make_branch_shelf()
    book = library_models.Book.objects.create(title="Seeded", shelf=shelf)
    existing = library_models.Genre.objects.create(name="Sci-Fi")
    book.genres.set([existing])
    res = schema.execute_sync(
        "mutation($id: ID!, $d: BookPartialInput!){ updateBook(id:$id, data:$d){ "
        "node{ id } errors{ field messages } } }",
        variable_values={"id": global_id_for(BookT, book.pk), "d": {"genres": [88888]}},
    )
    assert_mutation_field_error(res, "updateBook", "genres")
    # The pre-existing M2M set is untouched (the failed write rolled back).
    assert set(book.genres.values_list("pk", flat=True)) == {existing.pk}


@pytest.mark.django_db
def test_raw_pk_m2m_existence_check_coerces_out_of_range_pk_no_overflow():
    """An out-of-range raw-pk M2M id is treated as not-found, never a raw ``OverflowError``.

    ``decode_visible_relation_ids`` type-checks each id through the target pk
    field before any ``pk__in`` query. The default ``AutoField`` / ``BigAutoField``
    pk maps to a 32-bit ``Int`` input (so graphql-core caps it), but a target with
    an explicit ``BigIntegerField`` / ``PositiveBigIntegerField`` primary key maps
    to the arbitrary-precision ``BigInt`` input - a pk past SQLite's signed 64-bit
    range would overflow the parameter binding. Coercing first makes an
    out-of-range pk the same field-keyed ``FieldError`` a nonexistent pk yields.
    """
    m2m_field = library_models.Book._meta.get_field("genres")
    _pks, error = resolvers._decode_relation_id_list(
        [9223372036854775808],
        graphql_name="genres",
        related_model=m2m_field.related_model,
        info=None,
        relation_field=m2m_field,
    )
    assert error is not None
    assert error.field == "genres"


# ---------------------------------------------------------------------------
# FK explicit-null decode (required-null is live on updateItem.categoryId)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_single_fk_explicit_null_on_nullable_clears_not_relation_error():
    """An explicit ``null`` on a nullable FK clears (``None``), never a relation error.

    Required-FK ``null`` is live
    (``test_products_api.py::test_update_item_explicit_null_category_id_is_field_error``).
    Fakeshop write surfaces have no ``null=True`` FK, so the clear-signal branch
    is a helper pin with ``category.null`` patched True.
    """
    _build_item_schema()
    # Item.attachment is a nullable FileField, not an FK. Use Category.is_private's
    # sibling: monkeypatch a nullable FK field object that mirrors a real relation.
    fk_field = product_models.Item._meta.get_field("category")
    # Temporarily treat the relation as nullable for the clear-signal branch.
    with mock.patch.object(fk_field, "null", True):
        pk, error = resolvers._decode_single_relation_id(
            None,
            graphql_name="categoryId",
            related_model=fk_field.related_model,
            info=None,
            relation_field=fk_field,
        )
    assert error is None
    assert pk is None


@pytest.mark.django_db
def test_raw_pk_relations_with_no_registered_primary_use_default_manager_existence():
    """An unregistered raw-pk relation has existence validation but no visibility contract.

    Only ``Book`` is registered: the generated ``shelfId`` FK and ``genres`` M2M
    inputs therefore carry raw primary keys with no target ``get_queryset`` policy.
    Existing target rows remain attachable through the default manager, while a
    missing member of either relation fails in-band before validation / write.
    """

    class BookT(DjangoType, relay.Node):
        class Meta:
            model = library_models.Book
            fields = ("id", "title")
            primary = True

    class CreateBook(DjangoMutation):
        class Meta:
            model = library_models.Book
            operation = "create"
            permission_classes = [_AllowAll]

    @strawberry.type
    class Mutation:
        create_book = DjangoMutationField(CreateBook)

    finalize_django_types()
    schema = _schema(Mutation)
    shelf = _make_branch_shelf()
    genre = library_models.Genre.objects.create(name="Real")
    query = (
        "mutation($d: BookInput!){ createBook(data:$d){ "
        "node{ id title } errors{ field messages } } }"
    )

    valid = schema.execute_sync(
        query,
        variable_values={
            "d": {"title": "Valid", "shelfId": shelf.pk, "genres": [genre.pk]},
        },
    )
    assert valid.errors is None, valid.errors
    assert valid.data["createBook"]["errors"] == []
    book = library_models.Book.objects.get(title="Valid")
    assert book.shelf_id == shelf.pk
    assert set(book.genres.values_list("pk", flat=True)) == {genre.pk}

    invalid_cases = (
        ("Missing shelf", {"shelfId": shelf.pk + 9999, "genres": [genre.pk]}, "shelfId"),
        ("Missing genre", {"shelfId": shelf.pk, "genres": [genre.pk + 9999]}, "genres"),
    )
    for title, relations, error_field in invalid_cases:
        result = schema.execute_sync(
            query,
            variable_values={"d": {"title": title, **relations}},
        )
        assert_mutation_field_error(result, "createBook", error_field)
        assert not library_models.Book.objects.filter(title=title).exists()


# ---------------------------------------------------------------------------
# Create-validation parity with Model.objects.create over empty-value defaults,
# plus naive-datetime tz-coercion.
#
# ``ScalarSpecimen`` (scalars app) has ``payload = JSONField(default=dict)``
# (``blank=False``) and ``occurred_at = DateTimeField()``. Neither is reachable
# via a live mutation (the scalars app exposes no write surface), so these are
# package tests over the real model. The mutation is narrowed to the non-BigInt
# scalar columns so the schema builds without the scalar_map config.
# ---------------------------------------------------------------------------

_SPEC_UUID = "12345678-1234-5678-1234-567812345678"


def _build_scalar_specimen_schema():
    """Declare a ScalarSpecimen primary + a create mutation; return (schema, CreateSpec)."""

    class SpecT(DjangoType, relay.Node):
        class Meta:
            model = scalars_models.ScalarSpecimen
            fields = ("id", "label")
            primary = True

    class CreateSpec(DjangoMutation):
        class Meta:
            model = scalars_models.ScalarSpecimen
            operation = "create"
            fields = (
                "label",
                "occurred_on",
                "occurred_at",
                "occurred_time",
                "external_id",
                "payload",
            )
            permission_classes = [_AllowAll]

    @strawberry.type
    class Mutation:
        create_spec = DjangoMutationField(CreateSpec)

    finalize_django_types()
    return _schema(Mutation), CreateSpec


@pytest.mark.django_db
def test_create_omitting_empty_value_default_field_succeeds():
    """Omitting a ``JSONField(default=dict)`` (blank=False) on create succeeds.

    The field is optional in the input (it has a default), so a client may omit it.
    Before the fix, ``full_clean`` validated the model's own empty default (``{}`` is
    in Django's ``empty_values``) and rejected it ("This field cannot be blank") -
    stricter than ``Model.objects.create()``, which applies the default unvalidated.
    Create now excludes unprovided fields from ``full_clean``, so the omission writes
    the default cleanly.
    """
    schema, CreateSpec = _build_scalar_specimen_schema()
    input_name = CreateSpec._input_class.__name__
    res = schema.execute_sync(
        f"mutation($d: {input_name}!){{ createSpec(data:$d){{ node{{ id }} errors{{ field messages }} }} }}",
        variable_values={
            "d": {
                "label": "spec-omit-payload",
                "occurredOn": "2024-01-01",
                "occurredAt": "2024-01-01T12:00:00+00:00",
                "occurredTime": "12:00:00",
                "externalId": _SPEC_UUID,
            },
        },
    )
    assert res.errors is None, res.errors
    assert res.data["createSpec"]["errors"] == []
    assert res.data["createSpec"]["node"] is not None
    assert scalars_models.ScalarSpecimen.objects.get(label="spec-omit-payload").payload == {}


@pytest.mark.django_db
def test_create_naive_datetime_input_is_made_timezone_aware():
    """A naive datetime input is coerced to an aware datetime on create.

    Under ``USE_TZ=True`` a naive datetime would trigger Django's naive-datetime
    ``RuntimeWarning`` at save - which this suite's ``-W error`` config escalates to a
    top-level error. The decode step makes a naive datetime aware (like DRF), so the
    create succeeds warning-free and stores an aware value. (A regression would
    surface as the escalated warning failing this test.)
    """
    schema, CreateSpec = _build_scalar_specimen_schema()
    input_name = CreateSpec._input_class.__name__
    res = schema.execute_sync(
        f"mutation($d: {input_name}!){{ createSpec(data:$d){{ node{{ id }} errors{{ field messages }} }} }}",
        variable_values={
            "d": {
                "label": "spec-naive-dt",
                "occurredOn": "2024-01-01",
                "occurredAt": "2024-01-01T12:00:00",  # naive: no offset
                "occurredTime": "12:00:00",
                "externalId": _SPEC_UUID,
            },
        },
    )
    assert res.errors is None, res.errors
    assert res.data["createSpec"]["errors"] == []
    row = scalars_models.ScalarSpecimen.objects.get(label="spec-naive-dt")
    assert timezone.is_aware(row.occurred_at)


# ---------------------------------------------------------------------------
# Scalar field named ``<x>_id`` regression (spec-036)
#
# ``library.TaggedItem`` has a *scalar* ``object_id`` (a ``PositiveIntegerField``,
# emitted by the input generator) AND a ``GenericForeignKey`` ``content_object``.
# The decode index / provided-name mapping must NOT reverse ``object_id`` to a
# relation field by a blind ``_id`` suffix strip, and must NOT index the
# GFK as a decode-able FK. Both are reasoned from the relation field index,
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
    """A scalar field literally named ``<x>_id`` IS validated on partial update (spec-036).

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
    """``_provided_attr_names`` keeps a scalar ``<x>_id`` field under its real name (spec-036).

    The FK reversal is index-driven: ``content_type_id`` (a real FK attr) maps to
    ``content_type``, while ``object_id`` (a scalar) stays ``object_id`` - never
    mangled to ``object``.
    """
    from django_strawberry_framework.mutations.inputs import mutation_input_field_specs

    @strawberry.input
    class Probe:
        object_id: int
        tag: str
        content_type_id: int

    _specs, model_fields = mutation_input_field_specs(library_models.TaggedItem, Probe)
    provided = resolvers._provided_attr_names(
        model_fields,
        {"object_id": 5, "tag": "x", "content_type_id": 1},
        [],
    )
    assert provided == {"object_id", "tag", "content_type"}


def test_relation_field_index_excludes_generic_foreign_key():
    """``_relation_field_index`` does not index a ``GenericForeignKey`` as a FK (spec-036).

    A GFK reports ``is_relation=True`` but ``column=None`` / ``related_model=None``,
    so it must never enter ``fk_by_attr`` (where ``_decode_relation_id_set`` would
    later compare a decoded model against ``related_model=None``). The real
    ``content_type`` FK is still indexed.
    """
    from django_strawberry_framework.mutations.inputs import _relation_field_index

    fk_by_attr, _m2m_by_name = _relation_field_index(library_models.TaggedItem)
    assert "content_object_id" not in fk_by_attr
    assert "content_type_id" in fk_by_attr


def test_explicit_null_error_allows_null_on_nullable_column():
    """``_explicit_null_error`` yields no error for ``null`` on a ``null=True`` column.

    The complement of the live
    ``test_uploads_api.py::test_update_explicit_null_on_the_required_file_is_a_field_error_over_http``
    row: an explicit ``None`` on a nullable scalar column is a valid clear, so the guard
    returns ``None`` (no ``FieldError``). ``NullableScalarSpecimen.score`` is
    ``null=True``. No live products mutation exposes a nullable scalar column, so this
    branch is earned against a real nullable example model rather than a live query.
    """
    assert (
        resolvers._explicit_null_error(
            scalars_models.NullableScalarSpecimen._meta.get_field("score"),
            "score",
            None,
        )
        is None
    )


def test_validation_error_to_field_errors_non_dict_uses_all_key():
    """A non-dict ``ValidationError`` (``.messages``, no ``.error_dict``) maps under the sentinel.

    ``full_clean()`` always raises with an ``error_dict`` (the keyed path), so this
    ``.messages`` fallback serves a bare ``ValidationError`` - the shape the ``0.0.12``
    form / ``0.0.13`` serializer flavors and a model ``clean()`` raising a plain
    message produce. It is the documented single-source mapper, exercised directly as
    it is unreachable through the current ``full_clean`` path.
    """
    errors = resolvers.validation_error_to_field_errors(ValidationError("a plain message"))
    assert [(error.field, error.messages) for error in errors] == [
        (NON_FIELD_ERROR_KEY, ["a plain message"]),
    ]


# ---------------------------------------------------------------------------
# Structured error codes + paths on the Django flat mapper (spec-039)
# ---------------------------------------------------------------------------


def test_validation_error_to_field_errors_preserves_django_codes_and_path():
    """A Django ``ValidationError``'s ``.code``s -> ``codes``; field name -> ``path``."""
    from django.core.exceptions import ValidationError as DjangoValidationError

    from django_strawberry_framework.mutations.resolvers import validation_error_to_field_errors

    exc = DjangoValidationError(
        {"name": [DjangoValidationError("This field is required.", code="required")]},
    )
    (fe,) = validation_error_to_field_errors(exc)
    assert fe.field == "name"
    assert fe.codes == ["required"]
    assert fe.path == ["name"]


def test_validation_error_to_field_errors_non_dict_root_has_empty_path():
    """A non-dict (model-wide) Django ``ValidationError`` keys ``"__all__"`` with an EMPTY path (#13)."""
    from django.core.exceptions import ValidationError as DjangoValidationError

    from django_strawberry_framework.mutations.inputs import NON_FIELD_ERROR_KEY
    from django_strawberry_framework.mutations.resolvers import validation_error_to_field_errors

    (fe,) = validation_error_to_field_errors(
        DjangoValidationError("Whole-object problem.", code="invalid"),
    )
    assert fe.field == NON_FIELD_ERROR_KEY
    assert fe.path == []
    assert fe.codes == ["invalid"]


# ---------------------------------------------------------------------------
# Row locking on the update/delete locate (spec-039, expanded in 0.0.14)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_locate_instance_locks_through_base_manager_subquery_by_default():
    """The default locate acquires a visibility-constrained base-manager row lock.

    The lock query must NOT be the consumer's visibility queryset with
    ``.select_for_update()`` attached (joins / unions / annotations cannot legally
    carry ``FOR UPDATE``); it is the model's base manager filtered by
    ``pk__in=<visible pks>``. The located row still respects visibility (a row
    outside the subquery is not found).
    """
    from django.db import transaction

    from django_strawberry_framework.mutations import resolvers as mutation_resolvers

    _schema_and_types = _build_item_schema()
    ItemT = _schema_and_types[1][1]
    cat = product_models.Category.objects.create(name=_category_name())
    item = product_models.Item.objects.create(name="Lockable", category=cat)

    with transaction.atomic():
        located = mutation_resolvers.locate_instance(ItemT, item.pk, None, alias="default")
    assert located is not None
    assert located.pk == item.pk
    # The locked read comes from the BASE manager (a plain Item row), and the
    # visibility subquery still gates it: a missing pk is None, not an error.
    with transaction.atomic():
        assert (
            mutation_resolvers.locate_instance(ItemT, item.pk + 999, None, alias="default") is None
        )


def test_locate_instance_opt_out_skips_the_lock(monkeypatch):
    """``select_for_update=False`` locates through the (pinned) visibility queryset, unlocked."""
    from unittest.mock import MagicMock

    from django_strawberry_framework.mutations import resolvers as mutation_resolvers

    sentinel = object()
    visible_qs = MagicMock(name="visible_qs")
    visible_qs._db = None
    pinned_qs = MagicMock(name="pinned_qs")
    visible_qs.using.return_value = pinned_qs
    pinned_qs.get.return_value = sentinel

    monkeypatch.setattr(mutation_resolvers, "model_for", lambda _t: MagicMock())
    monkeypatch.setattr(mutation_resolvers, "initial_queryset", lambda _t: None)
    monkeypatch.setattr(
        mutation_resolvers,
        "apply_type_visibility_sync",
        lambda *a, **k: visible_qs,
    )

    result = mutation_resolvers.locate_instance(
        object(),
        7,
        None,
        alias="default",
        select_for_update=False,
    )
    assert result is sentinel
    visible_qs.using.assert_called_once_with("default")
    pinned_qs.select_for_update.assert_not_called()
    pinned_qs.get.assert_called_once_with(pk=7)


# ---------------------------------------------------------------------------
# Multi-db atomic boundary (the managed write alias)
# ---------------------------------------------------------------------------


def test_write_pipeline_opens_atomic_on_managed_write_alias(monkeypatch):
    """``run_write_pipeline_sync`` opens ``transaction.atomic(using=<managed alias>)``.

    The alias is resolved ONCE (by the ``DjangoSchema`` execution context, from
    ``router.db_for_write``) and published through the managed-transaction
    context; the pipeline's own atomic block - and its rollback - must ride the
    SAME alias, or a multi-db router write commits on the routed alias while
    the rollback stays on ``default``.
    """
    from unittest.mock import MagicMock, patch

    from django_strawberry_framework.mutations import resolvers as mutation_resolvers
    from django_strawberry_framework.utils.write_transaction import managed_write_transaction

    mutation_cls = MagicMock()
    mutation_cls.__name__ = "FakePipelineMutation"  # the alias guard names the mutation
    mutation_cls._mutation_meta.operation = "create"
    mutation_cls._mutation_meta.select_for_update = False
    # No permission classes: this test is about the managed-alias atomic, not auth,
    # so the authorization phase (and its rolled-back auth-alias barrier) is a no-op.
    mutation_cls._mutation_meta.permission_classes = []
    mutation_cls._primary_type = object()
    mutation_cls._payload_type_name = "Unused"

    captured: dict = {}

    class _Atomic:
        def __init__(self, using=None):
            captured["using"] = using

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(mutation_resolvers, "model_for", lambda _t: MagicMock())
    monkeypatch.setattr(mutation_resolvers, "payload_object_slot", lambda _t: "node")
    monkeypatch.setattr(mutation_resolvers, "payload_cls_for", lambda _m: MagicMock())
    monkeypatch.setattr(
        mutation_resolvers,
        "authorize_or_raise",
        lambda *a, **k: None,
    )
    monkeypatch.setattr(
        mutation_resolvers,
        "refetch_optimized",
        lambda *a, **k: MagicMock(pk=1),
    )
    monkeypatch.setattr(
        mutation_resolvers,
        "build_payload",
        lambda *a, **k: "ok",
    )

    with (
        patch.object(mutation_resolvers.transaction, "atomic", side_effect=_Atomic),
        managed_write_transaction("shard_b"),
    ):
        result = mutation_resolvers.run_write_pipeline_sync(
            mutation_cls,
            info=None,
            data=None,
            id=None,
            decode_step=lambda _instance: ("decoded",),
            write_step=lambda _instance, _decoded: MagicMock(pk=7),
        )

    assert result == "ok"
    assert captured["using"] == "shard_b"


def _pipeline_harness(monkeypatch, *, operation="update", authorize=None):
    """Scaffold ``run_write_pipeline_sync`` with mocked locate/authorize/refetch (snapshot tests)."""
    from unittest.mock import MagicMock

    from django_strawberry_framework.mutations import resolvers as mutation_resolvers

    mutation_cls = MagicMock()
    mutation_cls.__name__ = "SnapshotMutation"
    mutation_cls._mutation_meta.operation = operation
    mutation_cls._mutation_meta.select_for_update = False
    mutation_cls._primary_type = object()

    fake_model = MagicMock(__name__="Row")
    # A REAL identity ``to_python``: the canonical pk comparison must not be fed a
    # MagicMock whose repeated calls return one shared (always-equal) child mock.
    fake_model._meta.pk.to_python = lambda value: value
    monkeypatch.setattr(mutation_resolvers, "model_for", lambda _t: fake_model)
    monkeypatch.setattr(mutation_resolvers, "payload_object_slot", lambda _t: "node")
    monkeypatch.setattr(mutation_resolvers, "payload_cls_for", lambda _m: MagicMock())
    # ``**_kwargs`` absorbs the pinned ``using=`` alias the pipeline threads to the
    # real decode; this harness asserts drift handling, not alias propagation
    # (``test_custom_node_id_real_pk_lookup_uses_pinned_alias`` owns that).
    monkeypatch.setattr(
        mutation_resolvers,
        "coerce_lookup_id",
        lambda _id, _t, **_kwargs: (7, None),
    )
    monkeypatch.setattr(mutation_resolvers, "check_instance_write_alias", lambda *a, **k: None)
    monkeypatch.setattr(
        mutation_resolvers,
        "authorize_or_raise",
        authorize if authorize is not None else (lambda *a, **k: None),
    )
    monkeypatch.setattr(mutation_resolvers, "refetch_optimized", lambda *a, **k: MagicMock())
    monkeypatch.setattr(mutation_resolvers, "build_payload", lambda *a, **k: "ok")
    return mutation_cls, mutation_resolvers


def test_pipeline_snapshots_authorized_pk_before_permission_hook(monkeypatch):
    """The authorized pk is captured BEFORE the permission hook can touch the mutable instance.

    A malicious ``check_permission`` re-pointing ``instance.pk`` at a hidden row must not
    poison the snapshot the saved-result validation compares against: the write step
    returning the (mutated) instance fails the flavor-independent backstop.
    """
    from types import SimpleNamespace
    from unittest.mock import patch

    from django_strawberry_framework.exceptions import ConfigurationError
    from django_strawberry_framework.utils.write_transaction import managed_write_transaction

    located = SimpleNamespace(
        pk=7,
        get_deferred_fields=lambda: set(),
        _meta=SimpleNamespace(concrete_fields=[]),
    )

    def evil_authorize(*_args, **_kwargs):
        located.pk = 999  # re-point at a hidden row AFTER authorization

    mutation_cls, mutation_resolvers = _pipeline_harness(monkeypatch, authorize=evil_authorize)
    monkeypatch.setattr(mutation_resolvers, "locate_instance", lambda *a, **k: located)

    with (
        patch.object(mutation_resolvers.transaction, "atomic"),
        managed_write_transaction("default"),
        pytest.raises(ConfigurationError, match="must write the row that was authorized"),
    ):
        mutation_resolvers.run_write_pipeline_sync(
            mutation_cls,
            info=None,
            data=None,
            id="ignored",
            decode_step=lambda _instance: ("decoded",),
            write_step=lambda instance, _decoded: instance,
        )


def test_pipeline_pk_drift_diagnostic_survives_hostile_repr(monkeypatch):
    """A pk forged by a hook cannot replace the typed drift error while formatting it."""
    from unittest.mock import patch

    from django_strawberry_framework.exceptions import ConfigurationError
    from django_strawberry_framework.utils.write_transaction import managed_write_transaction

    class _HostilePk:
        def __repr__(self):
            raise RuntimeError("repr should never escape")

    located = SimpleNamespace(
        pk=7,
        get_deferred_fields=lambda: set(),
        _meta=SimpleNamespace(concrete_fields=[]),
    )

    def evil_authorize(*_args, **_kwargs):
        located.pk = _HostilePk()

    mutation_cls, mutation_resolvers = _pipeline_harness(monkeypatch, authorize=evil_authorize)
    monkeypatch.setattr(mutation_resolvers, "locate_instance", lambda *a, **k: located)

    with (
        patch.object(mutation_resolvers.transaction, "atomic"),
        managed_write_transaction("default"),
        pytest.raises(ConfigurationError, match="must write the row that was authorized"),
    ):
        mutation_resolvers.run_write_pipeline_sync(
            mutation_cls,
            info=None,
            data=None,
            id="ignored",
            decode_step=lambda _instance: ("decoded",),
            write_step=lambda instance, _decoded: instance,
        )


def test_pipeline_publishes_authorized_pk_on_write_context(monkeypatch):
    """The post-locate snapshot is published on the write-pipeline context for the flavors."""
    from types import SimpleNamespace
    from unittest.mock import patch

    from django_strawberry_framework.utils.write_transaction import (
        managed_write_transaction,
        require_write_pipeline,
    )

    located = SimpleNamespace(
        pk=7,
        get_deferred_fields=lambda: set(),
        _meta=SimpleNamespace(concrete_fields=[]),
    )
    seen: dict = {}

    def probe_authorize(*_args, **_kwargs):
        seen["authorized_pk"] = require_write_pipeline().authorized_pk

    mutation_cls, mutation_resolvers = _pipeline_harness(monkeypatch, authorize=probe_authorize)
    monkeypatch.setattr(mutation_resolvers, "locate_instance", lambda *a, **k: located)

    with (
        patch.object(mutation_resolvers.transaction, "atomic"),
        managed_write_transaction("default"),
    ):
        result = mutation_resolvers.run_write_pipeline_sync(
            mutation_cls,
            info=None,
            data=None,
            id="ignored",
            decode_step=lambda _instance: ("decoded",),
            write_step=lambda instance, _decoded: instance,
        )
    assert result == "ok"
    assert seen["authorized_pk"] == 7


def test_delete_pipeline_rejects_pk_drift_during_authorization(monkeypatch):
    """A delete permission hook re-pointing ``instance.pk`` fails closed before any delete."""
    from types import SimpleNamespace
    from unittest.mock import patch

    from django_strawberry_framework.exceptions import ConfigurationError
    from django_strawberry_framework.utils.write_transaction import managed_write_transaction

    located = SimpleNamespace(
        pk=7,
        get_deferred_fields=lambda: set(),
        _meta=SimpleNamespace(concrete_fields=[]),
    )

    def evil_authorize(*_args, **_kwargs):
        located.pk = 999  # re-point at a hidden row AFTER authorization

    mutation_cls, mutation_resolvers = _pipeline_harness(
        monkeypatch,
        operation="delete",
        authorize=evil_authorize,
    )
    mutation_cls._mutation_meta.permission_classes = []
    monkeypatch.setattr(mutation_resolvers, "locate_instance", lambda *a, **k: located)

    with (
        patch.object(mutation_resolvers.transaction, "atomic"),
        managed_write_transaction("default"),
        pytest.raises(ConfigurationError, match="pk changed"),
    ):
        mutation_resolvers._run_delete(mutation_cls, info=None, id="ignored")


def test_delete_pipeline_pk_drift_diagnostic_survives_hostile_repr(monkeypatch):
    """A delete-path pk forged by a hook cannot replace the typed drift error while formatting."""
    from types import SimpleNamespace
    from unittest.mock import patch

    from django_strawberry_framework.exceptions import ConfigurationError
    from django_strawberry_framework.utils.write_transaction import managed_write_transaction

    class _HostilePk:
        def __repr__(self):
            raise RuntimeError("repr should never escape")

    located = SimpleNamespace(
        pk=7,
        get_deferred_fields=lambda: set(),
        _meta=SimpleNamespace(concrete_fields=[]),
    )

    def evil_authorize(*_args, **_kwargs):
        located.pk = _HostilePk()

    mutation_cls, mutation_resolvers = _pipeline_harness(
        monkeypatch,
        operation="delete",
        authorize=evil_authorize,
    )
    mutation_cls._mutation_meta.permission_classes = []
    monkeypatch.setattr(mutation_resolvers, "locate_instance", lambda *a, **k: located)

    with (
        patch.object(mutation_resolvers.transaction, "atomic"),
        managed_write_transaction("default"),
        pytest.raises(ConfigurationError, match="pk changed"),
    ):
        mutation_resolvers._run_delete(mutation_cls, info=None, id="ignored")


def test_delete_pipeline_rides_shared_write_skeleton(monkeypatch):
    """Delete supplies a snapshot ``tail_step``; locate/auth/atomic live in the skeleton."""
    from unittest.mock import MagicMock

    from django_strawberry_framework.mutations import resolvers as mutation_resolvers

    seen: dict = {}

    def fake_pipeline(
        mutation_cls,
        info,
        data,
        id,  # noqa: A002
        *,
        decode_step,
        write_step,
        tail_step=None,
    ):
        seen["data"] = data
        seen["id"] = id
        seen["tail_step"] = tail_step
        return "ridden"

    monkeypatch.setattr(mutation_resolvers, "run_write_pipeline_sync", fake_pipeline)
    monkeypatch.setattr(mutation_resolvers, "payload_cls_for", lambda _m: object)
    monkeypatch.setattr(mutation_resolvers, "payload_object_slot", lambda _t: "node")
    mutation_cls = MagicMock()
    mutation_cls._primary_type = object()
    result = mutation_resolvers._run_delete(mutation_cls, info=None, id="gid")
    assert result == "ridden"
    assert seen["data"] is None
    assert seen["id"] == "gid"
    assert callable(seen["tail_step"])


def test_write_flavors_share_resolver_entry_factory():
    """Model, form, and serializer sync entries all come from ``make_resolver_entries``."""
    from django_strawberry_framework.forms.resolvers import resolve_form_sync
    from django_strawberry_framework.rest_framework.resolvers import resolve_serializer_sync

    assert resolvers.resolve_mutation_sync.__name__ == "resolve_sync"
    assert resolve_form_sync.__name__ == "resolve_sync"
    assert resolve_serializer_sync.__name__ == "resolve_sync"


@pytest.mark.django_db
def test_assign_m2m_integrity_error_contained_in_envelope():
    """IntegrityError during M2M assignment is returned as the constraint FieldError envelope."""
    from unittest.mock import patch

    from django.db import IntegrityError

    from django_strawberry_framework.utils.write_transaction import (
        managed_write_transaction,
        open_write_pipeline,
    )

    class CategoryType(DjangoType, relay.Node):
        class Meta:
            model = product_models.Category
            fields = ("id", "name", "description")

    class CreateCategoryMutation(DjangoMutation):
        class Meta:
            model = product_models.Category
            operation = "create"
            permission_classes = [_AllowAll]

    finalize_django_types()
    cat = product_models.Category(name=_category_name())

    with patch(
        "django_strawberry_framework.mutations.resolvers._assign_m2m",
        side_effect=IntegrityError("constraint failed"),
    ):
        decoded = (cat, [("fake_m2m", [1, 2])], [])
        with managed_write_transaction("default"), open_write_pipeline(CreateCategoryMutation):
            errors = resolvers._model_write_step(None, decoded)
        assert isinstance(errors, list)
        assert len(errors) == 1
        assert errors[0].field == NON_FIELD_ERROR_KEY
        assert errors[0].codes == ["constraint"]


@pytest.mark.django_db
def test_delete_integrity_error_contained_in_envelope():
    """IntegrityError during instance.delete() is returned as the constraint FieldError envelope."""
    from unittest.mock import patch

    from django.db import IntegrityError

    cat = product_models.Category.objects.create(name=_category_name())

    with patch.object(
        product_models.Category,
        "delete",
        side_effect=IntegrityError("FK constraint on delete"),
    ):
        errors = resolvers._delete_or_field_errors(cat)
        assert isinstance(errors, list)
        assert len(errors) == 1
        assert errors[0].field == NON_FIELD_ERROR_KEY
        assert errors[0].codes == ["constraint"]
