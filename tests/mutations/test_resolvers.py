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
from contextlib import contextmanager
from types import SimpleNamespace
from unittest import mock

import pytest
import strawberry
from apps.library import models as library_models
from apps.products import models as product_models
from apps.scalars import models as scalars_models
from asgiref.sync import sync_to_async
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.db import connection as db_connection
from django.db import models as djmodels
from django.test import override_settings
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
    return DjangoSchema(
        query=_Query,
        mutation=mutation_type,
        extensions=[DjangoOptimizerExtension],
    )


# ---------------------------------------------------------------------------
# Products Item/Category fixtures (FK + unique_item_per_category)
# ---------------------------------------------------------------------------


def _build_item_schema(
    *,
    item_get_queryset=None,
    category_get_queryset=None,
    input_cls=None,
    partial_input_cls=None,
):
    """Declare Item/Category primaries + create/update/delete mutations; return (schema, types).

    ``item_get_queryset`` injects a visibility hook on the ``Item`` primary type;
    ``category_get_queryset`` does the same on the ``Category`` primary type so the FK
    relation-visibility check (feedback P1) can be driven. Optional ``input_cls`` /
    ``partial_input_cls`` thread a consumer ``Meta.input_class`` /
    ``Meta.partial_input_class`` onto the create / update mutation so the CR-2 merge is
    exercised end-to-end; omitted, the generated inputs are used. One builder for all
    products-mutation resolver tests (DRY-4).
    """

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

    item_meta_attrs = {
        "model": product_models.Item,
        "fields": ("id", "name", "category"),
        "primary": True,
    }
    item_body: dict = {"Meta": type("Meta", (), item_meta_attrs)}
    if item_get_queryset is not None:
        item_body["get_queryset"] = item_get_queryset
    ItemT = type("ItemT", (DjangoType, relay.Node), item_body)

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
    if partial_input_cls is not None:
        update_meta["partial_input_class"] = partial_input_cls
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
    """Assert the common in-band mutation error envelope (DRY-4).

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
_UPDATE = (
    "mutation($id: ID!, $d: ItemPartialInput!){ updateItem(id:$id, data:$d){ "
    "node{ name } errors{ field messages } } }"
)
_DELETE = (
    "mutation($id: ID!){ deleteItem(id:$id){ "
    "node{ id name category{ name } } errors{ field messages } } }"
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
    """A delete returns the pre-deletion snapshot (id preserved) in the slot; the row is gone."""
    schema, (_CategoryT, ItemT) = _build_item_schema()
    cat = product_models.Category.objects.create(name=_category_name())
    item = product_models.Item.objects.create(name="Doomed", category=cat)
    res = schema.execute_sync(_DELETE, variable_values={"id": _item_gid(ItemT, item.pk)})
    assert res.errors is None, res.errors
    node = res.data["deleteItem"]["node"]
    assert node["name"] == "Doomed"
    # The deleted node id is preserved for cache eviction (feedback P1): it decodes
    # to the ORIGINAL pk even though the row is gone. The deletion runs against the
    # located instance, so Django's delete()-nulls-pk never touches this snapshot.
    assert relay.GlobalID.from_id(node["id"]).node_id == str(item.pk)
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


# ---------------------------------------------------------------------------
# Custom ``relay.NodeID`` write-side (feedback #1)
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
    """A write through a custom ``relay.NodeID[str]`` updates the NAME-matched row, not the pk-coincident one (feedback #1).

    ``CategoryNode`` encodes the non-pk ``name`` column as its Relay id, so the
    GlobalID a client holds carries the ``name`` string. The decoy is seeded so its
    pk's STRING form is the target's ``name``: before ``_resolve_real_pk`` the decoded
    ``name`` (``"<decoy.pk>"``) flowed straight into ``locate_instance``'s
    ``get(pk=...)`` and updated the DECOY. The write must change the row whose ``name``
    matches the payload (the target), never the row whose pk coincides with it.
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
def test_delete_custom_node_id_resolves_payload_to_real_pk_not_wrong_row():
    """A delete through a custom ``relay.NodeID[str]`` removes the NAME-matched row, not the pk-coincident one (feedback #1).

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
    assert_mutation_field_error(res, "createItem", "name")


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


def test_coerce_lookup_id_rejects_non_globalid():
    """A non-GlobalID ``id:`` (raw pk string, garbage, non-string) is a ``FieldError`` on ``id``.

    The update/delete ``id:`` MUST be a well-formed GlobalID (the node-field
    server-side-decode contract). A raw pk string carries no type slot to check
    against the target model, and a malformed string cannot decode at all, so both
    are rejected as a ``FieldError`` on ``id`` BEFORE any pk lookup - never coerced
    to a bare pk that would skip the AR-H4 type guard or raise a Django coercion
    error at ``.get(pk=...)`` (feedback #1). ``coerce_lookup_id`` is always called
    with the mutation's resolved primary type, so this unit pin passes a real bound
    ``ItemT`` (the shared ``decode_model_global_id`` reads ``target_type``'s model
    up front); decode fails on the malformed input with no pk lookup or DB read.
    """

    class ItemT(DjangoType, relay.Node):
        class Meta:
            model = product_models.Item
            fields = ("id", "name")
            primary = True

    for bad in ("5", "not-a-global-id", 5):
        node_id, error = resolvers.coerce_lookup_id(bad, ItemT)
        assert node_id is None
        assert error is not None and error.field == "id"


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
    # The catch is broad (``except IntegrityError``), so the message is the honest
    # superset, not an over-claimed "uniqueness" (feedback CR-3).
    assert payload["errors"][0]["messages"] == ["A database constraint was violated."]


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
    assert_mutation_field_error(res, "createItem", "categoryId")
    # No cross-model coercion happened: no second Item was created under the
    # (collided) Category pk path.
    assert product_models.Item.objects.filter(name="New").count() == 0


@pytest.mark.django_db
def test_relation_unresolvable_type_global_id_yields_field_error():
    """A well-formed relation ``GlobalID`` naming an unregistered type -> ``FieldError`` (AR-H4 / feedback #7).

    Distinct from the wrong-MODEL case (which decodes successfully then mismatches):
    here ``decode_global_id`` itself raises (the ``type_name`` resolves to no
    installed / registered Relay-Node type), so ``decode_model_global_id`` returns
    the ``DECODE_FAILED`` status and ``_decode_relation_id_set`` maps it to a
    ``FieldError`` on ``categoryId`` - the uniformly-field-keyed malformed-relation-id
    branch, never a top-level error from inside the resolver.
    """
    schema, (_CategoryT, _ItemT) = _build_item_schema()
    bogus = str(relay.GlobalID(type_name="nope.nonexistent", node_id="1"))
    res = schema.execute_sync(
        _CREATE,
        variable_values={"d": {"name": "X", "categoryId": bogus}},
    )
    assert_mutation_field_error(res, "createItem", "categoryId")
    assert product_models.Item.objects.filter(name="X").count() == 0


@pytest.mark.django_db
def test_update_uncoercible_pk_in_wellformed_id_is_not_found_no_crash():
    """A well-formed ``id:`` whose ``node_id`` is not a valid pk literal -> not-found, no crash (CR-1).

    ``decode_global_id`` validates payload SHAPE only, so a right-type ``ItemT``
    GlobalID can still carry ``node_id="abc"`` for an integer pk. Before CR-1 that
    bare ``"abc"`` reached ``.get(pk="abc")`` and Django raised a top-level
    ``ValueError`` (``"Field 'id' expected a number..."``) leaking the pk column
    type. Now it is coerced through the pk field and treated as not-found - a
    ``FieldError`` on ``id``, exactly like a missing/hidden row - never a top-level
    error.
    """
    schema, (_CategoryT, ItemT) = _build_item_schema()
    bad_id = global_id_for(ItemT, "abc")  # well-formed ItemT id, non-numeric node_id
    res = schema.execute_sync(_UPDATE, variable_values={"id": bad_id, "d": {"name": "X"}})
    # NOT a top-level GraphQLError (CR-1) - an in-band not-found FieldError on ``id``.
    assert_mutation_field_error(res, "updateItem", "id")


@pytest.mark.django_db
def test_create_relation_uncoercible_pk_is_field_error_no_crash():
    """A right-type relation ``GlobalID`` with an uncoercible ``node_id`` -> ``FieldError`` (CR-1).

    A ``CategoryT`` GlobalID carrying ``node_id="abc"`` passes the AR-H4 type check
    (it IS a Category id) but ``"abc"`` is not a valid integer pk. Before CR-1 it
    reached ``filter(pk__in=["abc"])`` and raised a top-level ``ValueError``; now it
    is coerced and mapped to the uniform relation ``FieldError`` on ``categoryId``
    (identifies no row - "not found"), never a crash. No row is written.
    """
    schema, (CategoryT, _ItemT) = _build_item_schema()
    bad_cat = global_id_for(CategoryT, "abc")
    res = schema.execute_sync(
        _CREATE,
        variable_values={"d": {"name": "X", "categoryId": bad_cat}},
    )
    # NOT a top-level GraphQLError (CR-1) - an in-band relation FieldError.
    assert_mutation_field_error(res, "createItem", "categoryId")
    assert product_models.Item.objects.filter(name="X").count() == 0


@pytest.mark.django_db
def test_globalid_relation_override_flows_through_visibility_contract():
    """A ``GlobalID`` relation override is still relation-visibility-checked (AR-M2 / Decision 10).

    The bind-time type-lock (``sets.py::_validate_relation_override_types``) forces a
    relation override to keep the generated ``relay.GlobalID`` id type precisely so the
    override CANNOT bypass the AR-H4 type-check / Decision-10 visibility contract a
    raw-pk override would have skipped. This pins the end-to-end guarantee: a
    ``createItem`` whose ``categoryId`` names a ``Category`` hidden by
    ``Category.get_queryset`` is a ``FieldError`` on ``categoryId`` (hidden
    indistinguishable from missing, no existence leak) - even though ``categoryId``
    came from a consumer ``input_class`` override, not the generated input. A raw-pk
    override would have been passed through unchecked and silently attached the
    unseeable row; the type-lock is what guarantees this path is reached.
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
    assert_mutation_field_error(res, "updateItem", "id")
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
        "refetch_optimized",
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
    schema = DjangoSchema(
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


def _build_book_schema(*, genre_get_queryset=None):
    """Declare Book/Genre/Shelf primaries + create/update mutations over the Book M2M.

    ``genre_get_queryset`` optionally installs a visibility hook on the ``Genre``
    primary type so the M2M relation-visibility check (feedback P1) can be driven.
    """

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


_CREATE_BOOK = (
    "mutation($d: BookGenresShelfTitleInput!){ createBook(data:$d){ "
    "node{ id title } errors{ field messages } } }"
)


@pytest.mark.django_db
def test_m2m_hidden_related_id_is_field_error():
    """An M2M id for a row the related type hides -> ``FieldError`` on the M2M field (feedback P1).

    ``GenreT.get_queryset`` hides the ``"Secret"`` genre, so a ``createBook`` whose
    ``genres`` list includes the hidden genre's id is a ``FieldError`` on ``genres``
    (hidden indistinguishable from missing, no existence leak) - the same
    visibility contract FK ids get, applied to the whole M2M set in one query. No
    book is written.
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


@pytest.mark.django_db
def test_m2m_explicit_null_is_field_error():
    """An explicit ``null`` M2M value -> ``FieldError`` on the M2M field, not a resolver crash (feedback P2).

    The generated optional M2M field is ``list[<id>] | None``, so a client can send
    ``genres: null``. ``null`` is not a valid replace-set (the contract is
    replace/clear/omit - clear is ``[]``), so it is a field-keyed error rather than
    iterating ``None`` into a ``TypeError``.
    """
    schema, (_GenreT, ShelfT, _BookT) = _build_book_schema()
    shelf = _make_branch_shelf()
    res = schema.execute_sync(
        _CREATE_BOOK,
        variable_values={
            "d": {"title": "Dune", "shelfId": global_id_for(ShelfT, shelf.pk), "genres": None},
        },
    )
    assert_mutation_field_error(res, "createBook", "genres")
    assert not library_models.Book.objects.filter(title="Dune").exists()


@pytest.mark.django_db
def test_m2m_wrong_type_id_is_field_error():
    """A wrong-type ``GlobalID`` anywhere in the M2M list -> ``FieldError`` on the M2M field (AR-H4).

    A ``Shelf`` id passed where a ``Genre`` id is expected is type-checked against
    the M2M target (``Genre``) and rejected as a ``FieldError`` on ``genres``,
    before the visibility / assignment steps.
    """
    schema, (_GenreT, ShelfT, _BookT) = _build_book_schema()
    shelf = _make_branch_shelf()
    res = schema.execute_sync(
        _CREATE_BOOK,
        variable_values={
            "d": {
                "title": "Dune",
                "shelfId": global_id_for(ShelfT, shelf.pk),
                "genres": [global_id_for(ShelfT, shelf.pk)],  # a Shelf id, not a Genre id
            },
        },
    )
    assert_mutation_field_error(res, "createBook", "genres")
    assert not library_models.Book.objects.filter(title="Dune").exists()


@pytest.mark.django_db
def test_m2m_uncoercible_pk_id_is_field_error_no_crash():
    """A right-type M2M id with an uncoercible ``node_id`` -> ``FieldError`` on the M2M field (CR-1).

    A ``GenreT`` GlobalID carrying ``node_id="abc"`` is a valid Genre id by type but
    ``"abc"`` is not a valid integer pk. The whole-set visibility query coerces each
    id through the related pk field first, so the uncoercible literal is the uniform
    relation ``FieldError`` on ``genres`` (not found), never the top-level
    ``ValueError`` that ``filter(pk__in=["abc"])`` would raise. No book is written.
    """
    schema, (GenreT, ShelfT, _BookT) = _build_book_schema()
    shelf = _make_branch_shelf()
    res = schema.execute_sync(
        _CREATE_BOOK,
        variable_values={
            "d": {
                "title": "Dune",
                "shelfId": global_id_for(ShelfT, shelf.pk),
                "genres": [global_id_for(GenreT, "abc")],  # right type, uncoercible pk
            },
        },
    )
    assert res.errors is None, res.errors  # NOT a top-level GraphQLError (CR-1)
    payload = res.data["createBook"]
    assert payload["node"] is None
    assert [e["field"] for e in payload["errors"]] == ["genres"]
    assert not library_models.Book.objects.filter(title="Dune").exists()


# ---------------------------------------------------------------------------
# Choice-enum inputs reach Django as the raw choice value (feedback - bug 4)
#
# A ``choices`` column resolves to a generated Strawberry ``Enum`` on BOTH the
# read type and the write input (the symmetric wire contract), so the client's
# enum value arrives at the resolver as the ENUM MEMBER, not the raw string. The
# resolver must unwrap it to its ``.value`` (the Django choice value) before
# ``full_clean`` / ``save``, or a valid choice is rejected. ``Book.circulation_status``
# is the real choice column (products has none, so this is package-tested).
# ---------------------------------------------------------------------------


def _build_book_choices_schema():
    """Declare Branch/Shelf/Book primaries + full-shape create/update over ``Book``.

    The create/update inputs are NOT narrowed, so the generated ``BookInput`` /
    ``BookPartialInput`` include the ``circulation_status`` choice column (a
    generated enum). ``Genre`` is intentionally left unregistered, so the optional
    M2M ``genres`` input is raw-pk and simply omitted by these tests.
    """

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
                "circulation_status",
                "shelf",
            )
            primary = True

    class CreateBook(DjangoMutation):
        class Meta:
            model = library_models.Book
            operation = "create"
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
    return _schema(Mutation), (ShelfT, BookT)


@pytest.mark.django_db
def test_choice_enum_create_saves_raw_choice_value():
    """A valid choice enum on create succeeds and persists the RAW choice value (bug 4).

    The client sends the GraphQL enum value ``available``; it reaches the resolver
    as ``BookCirculationStatusEnum.available``. Unwrapped to ``.value`` it is the
    Django choice ``"available"`` that ``full_clean`` accepts and the column stores.
    Without the unwrap, ``full_clean`` would reject the enum member as an invalid
    choice.
    """
    schema, (ShelfT, _BookT) = _build_book_choices_schema()
    shelf = _make_branch_shelf()
    res = schema.execute_sync(
        "mutation($d: BookInput!){ createBook(data:$d){ node{ id } errors{ field messages } } }",
        variable_values={
            "d": {
                "title": "Dune",
                "shelfId": global_id_for(ShelfT, shelf.pk),
                "circulationStatus": "available",
            },
        },
    )
    assert res.errors is None, res.errors
    assert res.data["createBook"]["errors"] == []
    assert library_models.Book.objects.get(title="Dune").circulation_status == "available"


@pytest.mark.django_db
def test_choice_enum_update_saves_raw_choice_value():
    """A valid choice enum on update persists the raw choice value too (bug 4)."""
    schema, (_ShelfT, BookT) = _build_book_choices_schema()
    shelf = _make_branch_shelf()
    book = library_models.Book.objects.create(
        title="Hyperion",
        shelf=shelf,
        circulation_status="available",
    )
    res = schema.execute_sync(
        "mutation($id: ID!, $d: BookPartialInput!){ updateBook(id:$id, data:$d){ "
        "node{ id } errors{ field messages } } }",
        variable_values={
            "id": global_id_for(BookT, book.pk),
            "d": {"circulationStatus": "repair"},
        },
    )
    assert res.errors is None, res.errors
    assert res.data["updateBook"]["errors"] == []
    book.refresh_from_db()
    assert book.circulation_status == "repair"


# ---------------------------------------------------------------------------
# Raw-pk (non-Relay target) M2M existence check (feedback - bug 5)
#
# An M2M to a NON-Relay-Node target generates a raw-pk ``list[Int]`` input with no
# GlobalID visibility contract. ``instance.<m2m>.set(pks)`` writes a through-table
# row for whatever pks it is handed, so a nonexistent pk would create a dangling FK
# row (an invalid FK SQLite flags at teardown) and return a false success. The
# decode existence-checks the raw-pk M2M set before assignment.
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

    class CreateBook(DjangoMutation):
        class Meta:
            model = library_models.Book
            operation = "create"
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


@pytest.mark.django_db
def test_create_raw_pk_m2m_nonexistent_id_is_field_error_no_dangling_row():
    """A nonexistent raw-pk M2M id on create -> ``FieldError`` on the M2M field, no row (bug 5)."""
    schema, (_GenreT, ShelfT, _BookT) = _build_book_raw_m2m_schema()
    shelf = _make_branch_shelf()
    before = library_models.Book.objects.count()
    res = schema.execute_sync(
        "mutation($d: BookInput!){ createBook(data:$d){ node{ id } errors{ field messages } } }",
        variable_values={
            "d": {
                "title": "Dangling",
                "shelfId": global_id_for(ShelfT, shelf.pk),
                "genres": [99999],
            },
        },
    )
    assert_mutation_field_error(res, "createBook", "genres")
    assert library_models.Book.objects.count() == before
    assert not library_models.Book.objects.filter(title="Dangling").exists()


@pytest.mark.django_db
def test_update_raw_pk_m2m_nonexistent_id_is_field_error_no_dangling_row():
    """A nonexistent raw-pk M2M id on update -> ``FieldError`` on the M2M field, set unchanged (bug 5)."""
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
def test_create_raw_pk_m2m_existing_id_succeeds():
    """A valid raw-pk M2M id on create still succeeds and assigns (positive control, bug 5)."""
    schema, (_GenreT, ShelfT, _BookT) = _build_book_raw_m2m_schema()
    shelf = _make_branch_shelf()
    genre = library_models.Genre.objects.create(name="Sci-Fi")
    res = schema.execute_sync(
        "mutation($d: BookInput!){ createBook(data:$d){ node{ id } errors{ field messages } } }",
        variable_values={
            "d": {
                "title": "Valid",
                "shelfId": global_id_for(ShelfT, shelf.pk),
                "genres": [genre.pk],
            },
        },
    )
    assert res.errors is None, res.errors
    assert res.data["createBook"]["errors"] == []
    book = library_models.Book.objects.get(title="Valid")
    assert set(book.genres.values_list("pk", flat=True)) == {genre.pk}


@pytest.mark.django_db
def test_raw_pk_m2m_existence_check_coerces_out_of_range_pk_no_overflow():
    """An out-of-range raw-pk M2M id is treated as not-found, never a raw ``OverflowError``.

    ``_relation_existence_error`` runs ``pk__in`` on the raw pks. The default
    ``AutoField`` / ``BigAutoField`` pk maps to a 32-bit ``Int`` input (so
    graphql-core caps it), but a target with an explicit ``BigIntegerField`` /
    ``PositiveBigIntegerField`` primary key maps to the arbitrary-precision
    ``BigInt`` input - a pk past SQLite's signed 64-bit range then reaches this
    query and overflows the parameter binding (a raw ``OverflowError`` escaping
    as a top-level error). The pk must be range-coerced first - the coercion the
    GlobalID path already applies via ``decode_model_global_id`` - so an
    out-of-range pk falls out of the existing set and yields the field-keyed
    ``FieldError`` a nonexistent pk yields.

    Driven at ``_relation_existence_error`` directly: no fakeshop model has a
    ``BigInteger`` primary key to carry the value end-to-end, and the overflow is
    at this function's ``pk__in`` regardless of the target's pk column type.
    """
    library_models.Genre.objects.create(name="Real")
    # 2**63: one past SQLite's signed-64-bit maximum (9223372036854775807).
    error = resolvers._relation_existence_error(
        "genres",
        [9223372036854775808],
        library_models.Genre,
    )
    assert error is not None
    assert error.field == "genres"


# ---------------------------------------------------------------------------
# Raw-pk (non-Relay target) relation VISIBILITY (feedback Finding 2)
#
# A relation to a NON-Relay-Node target generates a raw-pk input (no GlobalID). The
# original decode visibility-checked only the GlobalID branch, so a raw-pk relation
# whose related model has a registered (non-Relay) primary type with a get_queryset
# could attach a row that hook hides - the gap the form path already closes.
# _decode_relation_id_set now visibility-checks the raw-pk branch too, for both M2M
# and FK, falling back to existence-only when no primary type is registered.
# ---------------------------------------------------------------------------


def _build_book_raw_visibility_schema(*, genre_get_queryset=None, shelf_get_queryset=None):
    """Declare NON-Relay Genre + Shelf primaries so Book.genres (M2M) and Book.shelf (FK) are raw-pk.

    Optional ``genre_get_queryset`` / ``shelf_get_queryset`` install a visibility
    hook on the related primary so the raw-pk visibility gap (feedback Finding 2)
    can be driven end to end: a related row the hook hides must be a field-keyed
    ``FieldError``, never silently attached.
    """
    type(
        "BranchT",
        (DjangoType, relay.Node),
        {
            "Meta": type(
                "Meta",
                (),
                {"model": library_models.Branch, "fields": ("id", "name"), "primary": True},
            ),
        },
    )

    genre_body: dict = {
        "Meta": type(
            "Meta",
            (),
            {"model": library_models.Genre, "fields": ("id", "name"), "primary": True},
        ),
    }
    if genre_get_queryset is not None:
        genre_body["get_queryset"] = genre_get_queryset
    GenreT = type("GenreT", (DjangoType,), genre_body)  # NON-Relay -> Book.genres is a raw-pk list

    shelf_body: dict = {
        "Meta": type(
            "Meta",
            (),
            {"model": library_models.Shelf, "fields": ("id", "code"), "primary": True},
        ),
    }
    if shelf_get_queryset is not None:
        shelf_body["get_queryset"] = shelf_get_queryset
    ShelfT = type("ShelfT", (DjangoType,), shelf_body)  # NON-Relay -> Book.shelf is a raw-pk FK

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

    class CreateBook(DjangoMutation):
        class Meta:
            model = library_models.Book
            operation = "create"
            permission_classes = [_AllowAll]

    @strawberry.type
    class Mutation:
        create_book = DjangoMutationField(CreateBook)

    finalize_django_types()
    return _schema(Mutation), (GenreT, ShelfT, BookT)


_RAW_CREATE_BOOK = (
    "mutation($d: BookInput!){ createBook(data:$d){ node{ id } errors{ field messages } } }"
)


@pytest.mark.django_db
def test_create_raw_pk_m2m_hidden_member_is_field_error_no_visibility_leak():
    """A raw-pk M2M id the related type's get_queryset hides -> FieldError, never attached (Finding 2)."""

    @classmethod
    def _hide_secret(cls, queryset, info, **kwargs):
        return queryset.exclude(name="Secret")

    schema, (_GenreT, _ShelfT, _BookT) = _build_book_raw_visibility_schema(
        genre_get_queryset=_hide_secret,
    )
    shelf = _make_branch_shelf()
    hidden = library_models.Genre.objects.create(name="Secret")
    res = schema.execute_sync(
        _RAW_CREATE_BOOK,
        variable_values={"d": {"title": "Probe", "shelfId": shelf.pk, "genres": [hidden.pk]}},
    )
    assert_mutation_field_error(res, "createBook", "genres")
    assert not library_models.Book.objects.filter(title="Probe").exists()


@pytest.mark.django_db
def test_create_raw_pk_fk_hidden_target_is_field_error_no_visibility_leak():
    """A raw-pk FK id the related type's get_queryset hides -> FieldError, never attached (Finding 2)."""

    @classmethod
    def _hide_hidden(cls, queryset, info, **kwargs):
        return queryset.exclude(code="HIDDEN")

    schema, (_GenreT, _ShelfT, _BookT) = _build_book_raw_visibility_schema(
        shelf_get_queryset=_hide_hidden,
    )
    branch = library_models.Branch.objects.create(name="Main")
    hidden_shelf = library_models.Shelf.objects.create(code="HIDDEN", branch=branch)
    res = schema.execute_sync(
        _RAW_CREATE_BOOK,
        variable_values={"d": {"title": "Probe", "shelfId": hidden_shelf.pk}},
    )
    assert_mutation_field_error(res, "createBook", "shelfId")
    assert not library_models.Book.objects.filter(title="Probe").exists()


@pytest.mark.django_db
def test_create_raw_pk_relation_visible_members_still_attach():
    """The raw-pk visibility check does not over-reject: a VISIBLE FK + M2M still attach (Finding 2)."""

    @classmethod
    def _hide_decoy(cls, queryset, info, **kwargs):
        return queryset.exclude(name="Decoy")

    schema, (_GenreT, _ShelfT, _BookT) = _build_book_raw_visibility_schema(
        genre_get_queryset=_hide_decoy,
    )
    shelf = _make_branch_shelf()
    library_models.Genre.objects.create(name="Decoy")  # hidden, deliberately not attached
    visible = library_models.Genre.objects.create(name="Visible")
    res = schema.execute_sync(
        _RAW_CREATE_BOOK,
        variable_values={"d": {"title": "Good", "shelfId": shelf.pk, "genres": [visible.pk]}},
    )
    assert res.errors is None, res.errors
    assert res.data["createBook"]["errors"] == []
    book = library_models.Book.objects.get(title="Good")
    assert set(book.genres.values_list("pk", flat=True)) == {visible.pk}


@pytest.mark.django_db
def test_single_fk_explicit_null_on_nullable_clears_not_relation_error():
    """An explicit ``null`` on a nullable FK clears (``None``), never a relation error.

    ``_decode_single_relation_id`` short-circuits ``None`` on a ``null=True`` FK
    without a membership / visibility query - so a registered primary type on the
    related model cannot turn a clear into "Invalid id for relation".
    """
    _build_item_schema()
    # Item.attachment is a nullable FileField, not an FK. Use Category.is_private's
    # sibling: monkeypatch a nullable FK field object that mirrors a real relation.
    fk_field = product_models.Item._meta.get_field("category")
    # Temporarily treat the relation as nullable for the clear-signal branch.
    with mock.patch.object(fk_field, "null", True):
        pk, error = resolvers._decode_single_relation_id("categoryId", None, fk_field, info=None)
    assert error is None
    assert pk is None


@pytest.mark.django_db
def test_single_fk_explicit_null_on_required_is_field_keyed_null_error():
    """Explicit ``null`` on a ``null=False`` FK is a decode-time ``null`` FieldError.

    Rejected before ``full_clean`` / ``save`` so a ``blank=True, null=False`` FK
    cannot slip past validation into the generic ``__all__`` IntegrityError envelope.
    """
    _build_item_schema()
    fk_field = product_models.Item._meta.get_field("category")
    assert fk_field.null is False
    pk, error = resolvers._decode_single_relation_id("categoryId", None, fk_field, info=None)
    assert pk is None
    assert error is not None
    assert error.field == "categoryId"
    assert error.codes == ["null"]
    assert error.messages == ["This field cannot be null."]


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
# Create-validation parity with Model.objects.create (feedback - empty-value
# defaults #11) and naive-datetime tz-coercion (feedback #15).
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
    """Omitting a ``JSONField(default=dict)`` (blank=False) on create succeeds (feedback #11).

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
    """A naive datetime input is coerced to an aware datetime on create (feedback #15).

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
# Consumer input_class MERGE (spec-010 relation-override / AR-M2 / CR-2)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_create_through_merged_input_class_accepts_generated_remainder():
    """A partial consumer ``input_class`` still accepts the generated ``categoryId`` and writes (CR-2).

    The merge fills the generated remainder, so a create supplying BOTH the
    consumer-customized ``name`` and the generated ``categoryId`` succeeds. Under
    the old wholesale-replacement behavior the partial input lacked ``categoryId``
    and this would fail schema validation.
    """

    @strawberry.input
    class CustomItemInput:
        name: str = strawberry.field(description="A custom-described name")

    schema, (CategoryT, _ItemT) = _build_item_schema(input_cls=CustomItemInput)
    cat = product_models.Category.objects.create(name=_category_name())
    res = schema.execute_sync(
        _CREATE,
        variable_values={"d": {"name": "Widget", "categoryId": global_id_for(CategoryT, cat.pk)}},
    )
    assert res.errors is None, res.errors
    payload = res.data["createItem"]
    assert payload["node"]["name"] == "Widget"
    assert payload["node"]["category"]["name"] == cat.name
    assert product_models.Item.objects.filter(name="Widget", category=cat).exists()


@pytest.mark.django_db
def test_update_through_merged_partial_input_class_accepts_generated_remainder():
    """A partial consumer ``partial_input_class`` still accepts the generated fields and updates (CR-2)."""

    @strawberry.input
    class CustomItemPartial:
        name: str | None = strawberry.field(default=strawberry.UNSET, description="custom partial")

    schema, (_CategoryT, ItemT) = _build_item_schema(partial_input_cls=CustomItemPartial)
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
    so it must never enter ``fk_by_attr`` (where ``_decode_relation_id_set`` would
    later compare a decoded model against ``related_model=None``). The real
    ``content_type`` FK is still indexed.
    """
    fk_by_attr, _m2m_by_name = resolvers._relation_field_index(library_models.TaggedItem)
    assert "content_object_id" not in fk_by_attr
    assert "content_type_id" in fk_by_attr


# ---------------------------------------------------------------------------
# File upload assignment (spec-037) - the verify-first contract
# ---------------------------------------------------------------------------
#
# These tests PROVE the shipped generic scalar-assignment path carries an
# uploaded file: ``model(**scalar_and_fk_attrs)`` (create) and the ``setattr``
# loop (update) feed Django's ``FileField`` descriptor a ``SimpleUploadedFile``
# directly, so NO file-specific resolver branch is needed (spec-037 Decision 6).
# The schema is built WITHOUT ``config=strawberry_config()`` via the existing
# ``_schema`` helper: ``Upload`` still resolves because it rides Strawberry's
# built-in ``DEFAULT_SCALAR_REGISTRY`` (Decision 5), which is itself corroborating
# evidence. The synthetic model uses ``app_label="products"`` (installed) +
# ``managed=False`` + ``schema_editor`` + ``override_settings(MEDIA_ROOT=tmp_path)``,
# mirroring Slice 1's ``tests/types/test_resolvers.py`` shape.

_asset_model_counter = itertools.count(1)


def _make_asset_model():
    """Return a synthetic ``managed=False`` model with a required ``FileField`` + a name.

    ``app_label="products"`` (an INSTALLED app) so the table can be created with
    ``schema_editor``; ``attachment`` is required (no blank / no null) so the
    create input is ``Upload!`` and the explicit-``null`` guard fires on update.
    The model NAME is uniquified per call so Django's app registry does not warn on
    re-register.
    """
    suffix = next(_asset_model_counter)
    meta = type("Meta", (), {"app_label": "products", "managed": False})
    return type(
        f"MutAsset{suffix}",
        (djmodels.Model,),
        {
            "__module__": __name__,
            "name": djmodels.TextField(),
            "attachment": djmodels.FileField(upload_to="files/"),
            "Meta": meta,
        },
    )


def _build_asset_schema(model):
    """Declare an Asset primary (Relay-Node) + create/update mutations; return (schema, AssetT, queries).

    Mirrors ``_build_item_schema`` but over the synthetic file model. The primary
    type inherits ``relay.Node`` so the update ``id:`` GlobalID path works. The
    create / update query strings are built from the model's generated input type
    names (``<Model>Input`` / ``<Model>PartialInput``), since the model name is
    uniquified per call.
    """
    asset_meta = {"model": model, "fields": ("id", "name", "attachment"), "primary": True}
    AssetT = type("AssetT", (DjangoType, relay.Node), {"Meta": type("Meta", (), asset_meta)})

    create_meta = {"model": model, "operation": "create", "permission_classes": [_AllowAll]}
    update_meta = {"model": model, "operation": "update", "permission_classes": [_AllowAll]}
    CreateAsset = type("CreateAsset", (DjangoMutation,), {"Meta": type("Meta", (), create_meta)})
    UpdateAsset = type("UpdateAsset", (DjangoMutation,), {"Meta": type("Meta", (), update_meta)})

    @strawberry.type
    class Mutation:
        create_asset = DjangoMutationField(CreateAsset)
        update_asset = DjangoMutationField(UpdateAsset)

    finalize_django_types()
    create_query = (
        f"mutation($d: {model.__name__}Input!){{ createAsset(data:$d){{ "
        "node{ id name } errors{ field messages } } }"
    )
    update_query = (
        f"mutation($id: ID!, $d: {model.__name__}PartialInput!){{ "
        "updateAsset(id:$id, data:$d){ node{ id name } errors{ field messages } } }"
    )
    return _schema(Mutation), AssetT, create_query, update_query


@pytest.mark.django_db(transaction=True)
def test_create_assigns_uploaded_file_through_generic_path(tmp_path):
    """A create with a ``SimpleUploadedFile`` writes the row + the saved file (verify-first).

    PROVES the generic ``model(**scalar_and_fk_attrs)`` path carries the upload: no
    file-specific resolver branch exists, yet the saved ``FieldFile`` holds the
    uploaded name + content.
    """
    model = _make_asset_model()
    with db_connection.schema_editor() as schema_editor:
        schema_editor.create_model(model)
    try:
        with override_settings(MEDIA_ROOT=str(tmp_path)):
            schema, _AssetT, create_query, _update_query = _build_asset_schema(model)
            upload = SimpleUploadedFile("doc.txt", b"hello bytes")
            res = schema.execute_sync(
                create_query,
                variable_values={"d": {"name": "A", "attachment": upload}},
            )
            assert res.errors is None, res.errors
            payload = res.data["createAsset"]
            assert payload["errors"] == []
            assert payload["node"]["name"] == "A"
            row = model.objects.get(name="A")
            assert row.attachment.name.endswith("doc.txt")
            with row.attachment.open("rb") as fh:
                assert fh.read() == b"hello bytes"
    finally:
        with db_connection.schema_editor() as schema_editor:
            schema_editor.delete_model(model)


@pytest.mark.django_db(transaction=True)
def test_partial_update_omitting_file_leaves_stored_file_unchanged(tmp_path):
    """A partial update that omits the file field leaves the stored ``FieldFile`` byte-identical.

    ``UNSET`` is stripped in ``_decode_relations`` before the ``setattr`` loop, so
    the stored file never reaches a re-assignment.
    """
    model = _make_asset_model()
    with db_connection.schema_editor() as schema_editor:
        schema_editor.create_model(model)
    try:
        with override_settings(MEDIA_ROOT=str(tmp_path)):
            schema, AssetT, _create_query, update_query = _build_asset_schema(model)
            row = model()
            row.name = "Old"
            row.attachment.save(
                "orig.txt",
                SimpleUploadedFile("orig.txt", b"original"),
                save=False,
            )
            row.save()
            original_name = row.attachment.name

            res = schema.execute_sync(
                update_query,
                variable_values={"id": global_id_for(AssetT, row.pk), "d": {"name": "New"}},
            )
            assert res.errors is None, res.errors
            assert res.data["updateAsset"]["node"]["name"] == "New"
            row.refresh_from_db()
            assert row.name == "New"
            assert row.attachment.name == original_name  # unprovided -> unchanged
            with row.attachment.open("rb") as fh:
                assert fh.read() == b"original"
    finally:
        with db_connection.schema_editor() as schema_editor:
            schema_editor.delete_model(model)


@pytest.mark.django_db(transaction=True)
def test_partial_update_with_new_upload_replaces_file_through_setattr_path(tmp_path):
    """A partial update providing a new ``SimpleUploadedFile`` replaces the stored file.

    PROVES the generic ``setattr(instance, attr, value)`` update loop carries the
    upload - again with no file-specific branch.
    """
    model = _make_asset_model()
    with db_connection.schema_editor() as schema_editor:
        schema_editor.create_model(model)
    try:
        with override_settings(MEDIA_ROOT=str(tmp_path)):
            schema, AssetT, _create_query, update_query = _build_asset_schema(model)
            row = model()
            row.name = "Old"
            row.attachment.save(
                "orig.txt",
                SimpleUploadedFile("orig.txt", b"original"),
                save=False,
            )
            row.save()

            new_upload = SimpleUploadedFile("replacement.txt", b"replaced bytes")
            res = schema.execute_sync(
                update_query,
                variable_values={
                    "id": global_id_for(AssetT, row.pk),
                    "d": {"attachment": new_upload},
                },
            )
            assert res.errors is None, res.errors
            assert res.data["updateAsset"]["errors"] == []
            row.refresh_from_db()
            assert row.attachment.name.endswith("replacement.txt")
            with row.attachment.open("rb") as fh:
                assert fh.read() == b"replaced bytes"
    finally:
        with db_connection.schema_editor() as schema_editor:
            schema_editor.delete_model(model)


@pytest.mark.django_db(transaction=True)
def test_explicit_null_on_non_nullable_file_column_is_field_error(tmp_path):
    """Explicit ``null`` for a ``null=False`` file column -> field-keyed ``FieldError``.

    The shipped ``_explicit_null_error`` guard rejects a provided ``None`` on a
    ``null=False`` scalar column before any DB work; a file column is a scalar
    input, so it reaches the guard for free (no file-specific code). Omittable is
    not nullable - this is NOT a silent clear (clearing stays a Risks item).
    """
    model = _make_asset_model()
    with db_connection.schema_editor() as schema_editor:
        schema_editor.create_model(model)
    try:
        with override_settings(MEDIA_ROOT=str(tmp_path)):
            schema, AssetT, _create_query, update_query = _build_asset_schema(model)
            row = model()
            row.name = "Keep"
            row.attachment.save(
                "orig.txt",
                SimpleUploadedFile("orig.txt", b"original"),
                save=False,
            )
            row.save()

            res = schema.execute_sync(
                update_query,
                variable_values={"id": global_id_for(AssetT, row.pk), "d": {"attachment": None}},
            )
            assert_mutation_field_error(res, "updateAsset", "attachment")
            # The stored file is untouched (the error fired before any write).
            row.refresh_from_db()
            with row.attachment.open("rb") as fh:
                assert fh.read() == b"original"
    finally:
        with db_connection.schema_editor() as schema_editor:
            schema_editor.delete_model(model)


_fk_null_model_counter = itertools.count(1)


def _make_blank_true_required_fk_models():
    """Synthetic ``blank=True, null=False`` FK pair (the IntegrityError slip case)."""
    suffix = next(_fk_null_model_counter)
    target_meta = type("Meta", (), {"app_label": "products", "managed": False})
    target = type(
        f"MutFkTarget{suffix}",
        (djmodels.Model,),
        {"__module__": __name__, "name": djmodels.TextField(), "Meta": target_meta},
    )
    source_meta = type("Meta", (), {"app_label": "products", "managed": False})
    source = type(
        f"MutFkSource{suffix}",
        (djmodels.Model,),
        {
            "__module__": __name__,
            "target": djmodels.ForeignKey(
                target,
                on_delete=djmodels.CASCADE,
                blank=True,
                null=False,
            ),
            "Meta": source_meta,
        },
    )
    return target, source


@pytest.mark.django_db(transaction=True)
def test_create_blank_true_null_false_fk_explicit_null_is_field_error():
    """Explicit ``null`` on a ``blank=True, null=False`` FK is field-keyed, not ``__all__``.

    Django ``full_clean`` skips ``blank=True`` empty values, so without the
    decode-time FK null guard the write reaches a NOT NULL ``IntegrityError`` and
    the generic constraint envelope. The client must learn WHICH field failed.
    """
    target_model, source_model = _make_blank_true_required_fk_models()
    with db_connection.schema_editor() as schema_editor:
        schema_editor.create_model(target_model)
        schema_editor.create_model(source_model)
    try:

        class TargetT(DjangoType, relay.Node):
            class Meta:
                model = target_model
                fields = ("id", "name")
                primary = True

        class SourceT(DjangoType, relay.Node):
            class Meta:
                model = source_model
                fields = ("id", "target")
                primary = True

        class CreateSource(DjangoMutation):
            class Meta:
                model = source_model
                operation = "create"
                permission_classes = [_AllowAll]

        @strawberry.type
        class Mutation:
            create_source = DjangoMutationField(CreateSource)

        finalize_django_types()
        schema = _schema(Mutation)
        input_name = CreateSource._input_class.__name__
        res = schema.execute_sync(
            f"mutation($d: {input_name}!){{ createSource(data:$d){{ "
            f"node{{ id }} errors{{ field messages codes }} }} }}",
            variable_values={"d": {"targetId": None}},
        )
        payload = assert_mutation_field_error(res, "createSource", "targetId")
        assert payload["errors"][0]["codes"] == ["null"]
        assert source_model.objects.count() == 0
    finally:
        with db_connection.schema_editor() as schema_editor:
            schema_editor.delete_model(source_model)
            schema_editor.delete_model(target_model)


def test_explicit_null_error_allows_null_on_nullable_column():
    """``_explicit_null_error`` yields no error for ``null`` on a ``null=True`` column.

    The complement of ``test_explicit_null_on_non_nullable_file_column_is_field_error``:
    an explicit ``None`` on a nullable scalar column is a valid clear, so the guard
    returns ``None`` (no ``FieldError``). ``NullableScalarSpecimen.score`` is
    ``null=True``. No live products mutation exposes a nullable scalar column, so this
    branch is earned against a real nullable example model rather than a live query.
    """
    assert (
        resolvers._explicit_null_error(
            scalars_models.NullableScalarSpecimen,
            "score",
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
# Structured error codes + paths on the Django flat mapper (spec-039 rev6 #4 / #13)
# ---------------------------------------------------------------------------


def test_validation_error_to_field_errors_preserves_django_codes_and_path():
    """A Django ``ValidationError``'s ``.code``s -> ``codes``; field name -> ``path`` (#4 / #13)."""
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
# Row locking on the update/delete locate (spec-039 rev6 #14, expanded by BETA-055)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_locate_instance_locks_through_base_manager_subquery_by_default():
    """The default locate acquires a base-manager ``FOR UPDATE`` constrained by the visibility pk subquery (BETA-055).

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
    the rollback stays on ``default`` (spec-039 H6 gap).
    """
    from unittest.mock import MagicMock, patch

    from django_strawberry_framework.mutations import resolvers as mutation_resolvers
    from django_strawberry_framework.utils.write_transaction import managed_write_transaction

    mutation_cls = MagicMock()
    mutation_cls._mutation_meta.operation = "create"
    mutation_cls._mutation_meta.select_for_update = False
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


# ---------------------------------------------------------------------------
# Delete refused by a PROTECT / RESTRICT reference (the protected-delete envelope)
# ---------------------------------------------------------------------------

_protector_model_counter = itertools.count(1)


@contextmanager
def _protector_model(on_delete):
    """One stable protector-model fixture: create, yield, then FULLY retire the model.

    Yields a synthetic ``managed=False`` model holding an ``on_delete``-guarded FK
    to ``Item`` (``app_label="products"`` - an INSTALLED app - so the table can be
    created with ``schema_editor``; ``related_name="+"`` skips the reverse
    accessor; the NAME is uniquified per call so re-register never warns).

    The load-bearing part is the TEARDOWN: dropping only the TABLE used to leave
    the model class registered in Django's app registry, so every later
    ``Item.delete()`` anywhere in the process - including the sibling
    parametrized run - had its deletion collector query the now-missing table
    ("no such table", order-/worker-sensitive). Retiring the model means popping
    it from ``apps.all_models`` AND clearing the registry's caches (which rebuilds
    ``Item._meta.related_objects``), so each run is self-contained regardless of
    ordering.
    """
    suffix = next(_protector_model_counter)
    meta = type("Meta", (), {"app_label": "products", "managed": False})
    model = type(
        f"MutProtector{suffix}",
        (djmodels.Model,),
        {
            "__module__": __name__,
            "item": djmodels.ForeignKey(
                product_models.Item,
                related_name="+",
                on_delete=on_delete,
            ),
            "Meta": meta,
        },
    )
    with db_connection.schema_editor() as schema_editor:
        schema_editor.create_model(model)
    try:
        yield model
    finally:
        with db_connection.schema_editor() as schema_editor:
            schema_editor.delete_model(model)
        apps_registry = model._meta.apps
        apps_registry.all_models["products"].pop(model._meta.model_name, None)
        apps_registry.clear_cache()


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    "on_delete",
    [djmodels.PROTECT, djmodels.RESTRICT],
    ids=["protect", "restrict"],
)
def test_delete_refused_by_protected_reference_is_envelope_not_graphql_error(on_delete):
    """A PROTECT / RESTRICT-referenced row's delete returns the envelope; the row survives.

    Without the ``_delete_or_field_errors`` guard the deletion collector's
    ``ProtectedError`` / ``RestrictedError`` escaped ``_run_delete`` as a raw
    top-level ``GraphQLError`` carrying Django's internal message (model and
    relation names - an information leak). Both exceptions subclass
    ``IntegrityError``, so this also pins that the catch is the delete-specific
    one (the message names the protected-reference refusal, not the generic
    constraint fallback) and that it leaks no referencing-model name.
    """
    with _protector_model(on_delete) as model:
        schema, (_CategoryT, ItemT) = _build_item_schema()
        cat = product_models.Category.objects.create(name=_category_name())
        item = product_models.Item.objects.create(name="Guarded", category=cat)
        model.objects.create(item=item)
        res = schema.execute_sync(_DELETE, variable_values={"id": _item_gid(ItemT, item.pk)})
        payload = assert_mutation_field_error(res, "deleteItem", NON_FIELD_ERROR_KEY)
        assert payload["errors"][0]["messages"] == [
            "Cannot delete: other rows reference this one and are protected.",
        ]
        assert model.__name__ not in str(payload["errors"])  # no internal-name leak
        assert product_models.Item.objects.filter(pk=item.pk).exists()  # refused, not deleted


def test_raw_pk_relation_check_skips_an_all_none_set_without_querying():
    """An all-``None`` raw-pk set is a nullable-relation clear: no check, no query.

    ``_raw_pk_relation_error``'s explicit-``None`` contract (see its docstring):
    a ``None`` is not a pk to verify - it decodes to a NULL assignment validated
    by ``full_clean`` - so a set with no real pks returns clean before any
    registry resolve or visibility query (``info`` is never touched).
    """
    error = resolvers._raw_pk_relation_error("branchId", [None], product_models.Category, None)
    assert error is None
