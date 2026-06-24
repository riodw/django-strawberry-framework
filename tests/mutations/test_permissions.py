"""``DjangoModelPermission`` class behavior + write-auth enforcement (spec-036 Slice 2 + Slice 3).

Slice 2's class-behavior tests exercise ``DjangoModelPermission.has_permission``
DIRECTLY - a stub ``info`` whose ``context.request.user`` is a real Django ``User``
with / without the relevant ``add`` / ``change`` / ``delete`` model permission -
pinning the operation -> Django-action map and the anonymous-is-denied safe
default.

Slice 3 adds the *enforcement* tests (the second section below): through a
finalized schema, the resolver invokes ``check_permission`` /
``Meta.permission_classes`` at the spec-036 Decision 8 / Decision 15 placement
(before validation for ``create``; after the visibility lookup for ``update`` /
``delete``) and maps a denial to a **top-level ``GraphQLError``**, distinct from the
field-keyed validation envelope. The ``Meta.permission_classes`` override and the
no-existence-leak ordering (hidden row is not-found before any auth signal) are
pinned here too.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
import strawberry
from apps.products import models as product_models
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser, Permission
from strawberry import relay

from django_strawberry_framework import (
    DjangoModelPermission,
    DjangoMutation,
    DjangoMutationField,
    DjangoType,
    finalize_django_types,
)
from django_strawberry_framework.mutations.permissions import _OPERATION_PERMISSION_ACTION
from django_strawberry_framework.registry import registry
from django_strawberry_framework.testing.relay import global_id_for


@pytest.fixture(autouse=True)
def _isolate_registry():
    """Reset the registry (co-clears the mutation declaration registry) per test."""
    registry.clear()
    yield
    registry.clear()


def _info_for(user) -> SimpleNamespace:
    """Build a stub ``info`` whose ``context.request.user`` is ``user``.

    Matches the ``info.context.request`` shape ``request_from_info`` resolves -
    the canonical Strawberry-Django context the read-side permission pipeline uses.
    """
    return SimpleNamespace(context=SimpleNamespace(request=SimpleNamespace(user=user)))


def _create_item_mutation() -> type:
    """A ``create`` ``DjangoMutation`` over the products ``Item`` model."""

    class CreateItem(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "create"

    return CreateItem


def _user_with_perms(*codenames: str):
    """Create a Django user holding exactly the named products permissions."""
    user = get_user_model().objects.create_user(username="perm_probe", password="x")
    for codename in codenames:
        perm = Permission.objects.get(codename=codename, content_type__app_label="products")
        user.user_permissions.add(perm)
    # Re-fetch so the permission cache reflects the freshly added rows.
    return get_user_model().objects.get(pk=user.pk)


def test_operation_action_map_is_pinned():
    """The operation -> Django-action map matches the spec (create/update/delete)."""
    assert _OPERATION_PERMISSION_ACTION == {
        "create": "add",
        "update": "change",
        "delete": "delete",
    }


@pytest.mark.django_db
def test_anonymous_user_is_denied():
    """An ``AnonymousUser`` holds no perms, so the write is denied (safe default)."""
    mutation = _create_item_mutation()
    info = _info_for(AnonymousUser())
    assert DjangoModelPermission().has_permission(info, mutation, "create", data=None) is False


@pytest.mark.django_db
def test_user_lacking_perm_is_denied():
    """An authenticated user without ``add_item`` is denied for ``create``."""
    mutation = _create_item_mutation()
    user = _user_with_perms()  # no perms
    info = _info_for(user)
    assert DjangoModelPermission().has_permission(info, mutation, "create", data=None) is False


@pytest.mark.django_db
def test_user_with_add_perm_allowed_for_create():
    """A user holding ``add_item`` is allowed for ``create``."""
    mutation = _create_item_mutation()
    user = _user_with_perms("add_item")
    info = _info_for(user)
    assert DjangoModelPermission().has_permission(info, mutation, "create", data=None) is True


@pytest.mark.django_db
def test_create_perm_does_not_authorize_update_or_delete():
    """``add_item`` alone does not authorize ``update`` (needs ``change``) or ``delete``."""
    mutation = _create_item_mutation()
    user = _user_with_perms("add_item")
    info = _info_for(user)
    assert DjangoModelPermission().has_permission(info, mutation, "update", data=None) is False
    assert DjangoModelPermission().has_permission(info, mutation, "delete", data=None) is False


@pytest.mark.django_db
def test_change_and_delete_perms_authorize_their_operations():
    """``change_item`` authorizes ``update``; ``delete_item`` authorizes ``delete``."""
    mutation = _create_item_mutation()
    user = _user_with_perms("change_item", "delete_item")
    info = _info_for(user)
    assert DjangoModelPermission().has_permission(info, mutation, "update", data=None) is True
    assert DjangoModelPermission().has_permission(info, mutation, "delete", data=None) is True


# ---------------------------------------------------------------------------
# Slice 3: write-auth ENFORCEMENT through a schema (AR-H3 / Decision 15)
# ---------------------------------------------------------------------------


@strawberry.type
class _Query:
    @strawberry.field
    def ping(self) -> int:
        return 1


def _build_auth_schema(*, create_permission_classes=None):
    """Declare Item/Category primaries + create/update/delete mutations; return (schema, types).

    ``create_permission_classes`` overrides ``CreateItem.Meta.permission_classes``;
    ``None`` keeps the default ``[DjangoModelPermission]`` so the model-perm
    enforcement is exercised end-to-end.
    """

    class CategoryT(DjangoType, relay.Node):
        class Meta:
            model = product_models.Category
            fields = ("id", "name")
            primary = True

    class ItemT(DjangoType, relay.Node):
        class Meta:
            model = product_models.Item
            fields = ("id", "name")
            primary = True

    create_meta_attrs = {"model": product_models.Item, "operation": "create"}
    if create_permission_classes is not None:
        create_meta_attrs["permission_classes"] = create_permission_classes
    CreateItem = type(
        "CreateItem",
        (DjangoMutation,),
        {"Meta": type("Meta", (), create_meta_attrs)},
    )

    class UpdateItem(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "update"

    class DeleteItem(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "delete"

    @strawberry.type
    class Mutation:
        create_item = DjangoMutationField(CreateItem)
        update_item = DjangoMutationField(UpdateItem)
        delete_item = DjangoMutationField(DeleteItem)

    finalize_django_types()
    schema = strawberry.Schema(query=_Query, mutation=Mutation)
    return schema, (CategoryT, ItemT)


def _execute(
    schema,
    query,
    user,
    variables,
):
    """Execute ``query`` with ``info.context.request.user`` set to ``user``."""
    return schema.execute_sync(
        query,
        variable_values=variables,
        context_value=SimpleNamespace(request=SimpleNamespace(user=user)),
    )


_CREATE_Q = "mutation($d: ItemInput!){ createItem(data:$d){ node{ name } errors{ field } } }"


@pytest.mark.django_db
def test_anonymous_create_denied_top_level_error_no_write():
    """An anonymous create is denied with a top-level ``GraphQLError`` and no write (AR-H3)."""
    schema, (CategoryT, _ItemT) = _build_auth_schema()
    cat = product_models.Category.objects.create(name="Cat-anon")
    res = _execute(
        schema,
        _CREATE_Q,
        AnonymousUser(),
        {"d": {"name": "Blocked", "categoryId": global_id_for(CategoryT, cat.pk)}},
    )
    assert res.errors is not None
    assert "authorized" in res.errors[0].message.lower()
    # No payload entry (top-level error nulls the field), no write.
    assert not product_models.Item.objects.filter(name="Blocked").exists()


@pytest.mark.django_db
def test_under_privileged_create_denied():
    """A user lacking ``add_item`` is denied (top-level error), no write."""
    schema, (CategoryT, _ItemT) = _build_auth_schema()
    cat = product_models.Category.objects.create(name="Cat-noperm")
    user = _user_with_perms()  # no perms
    res = _execute(
        schema,
        _CREATE_Q,
        user,
        {"d": {"name": "Blocked", "categoryId": global_id_for(CategoryT, cat.pk)}},
    )
    assert res.errors is not None
    assert not product_models.Item.objects.filter(name="Blocked").exists()


@pytest.mark.django_db
def test_permitted_create_succeeds():
    """A user holding ``add_item`` creates the row (the allow path)."""
    schema, (CategoryT, _ItemT) = _build_auth_schema()
    cat = product_models.Category.objects.create(name="Cat-ok")
    user = _user_with_perms("add_item")
    res = _execute(
        schema,
        _CREATE_Q,
        user,
        {"d": {"name": "Allowed", "categoryId": global_id_for(CategoryT, cat.pk)}},
    )
    assert res.errors is None, res.errors
    assert res.data["createItem"]["node"]["name"] == "Allowed"
    assert product_models.Item.objects.filter(name="Allowed").exists()


@pytest.mark.django_db
def test_denial_raises_top_level_not_field_error_envelope():
    """A denial surfaces in top-level ``errors`` with a null payload, not a ``FieldError`` envelope entry."""
    schema, (CategoryT, _ItemT) = _build_auth_schema()
    cat = product_models.Category.objects.create(name="Cat-distinct")
    res = _execute(
        schema,
        _CREATE_Q,
        AnonymousUser(),
        {"d": {"name": "X", "categoryId": global_id_for(CategoryT, cat.pk)}},
    )
    # Authorization failure: top-level errors, payload null/absent.
    assert res.errors is not None
    assert res.data is None or res.data.get("createItem") is None


@pytest.mark.django_db
def test_hidden_row_is_not_found_before_auth_signal_no_existence_leak():
    """For update, a hidden row is not-found BEFORE any auth signal (no existence leak).

    The visibility lookup runs first; a row the caller cannot see returns a
    not-found ``FieldError`` on ``id`` (the validation envelope), NOT a top-level
    "not authorized" error - so the auth path never reveals the row's existence.
    """

    class CategoryT(DjangoType, relay.Node):
        class Meta:
            model = product_models.Category
            fields = ("id", "name")
            primary = True

    class ItemT(DjangoType, relay.Node):
        get_queryset = classmethod(lambda cls, qs, info, **k: qs.filter(is_private=False))

        class Meta:
            model = product_models.Item
            fields = ("id", "name")
            primary = True

    class UpdateItem(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "update"

    @strawberry.type
    class Mutation:
        update_item = DjangoMutationField(UpdateItem)

    finalize_django_types()
    schema = strawberry.Schema(query=_Query, mutation=Mutation)

    cat = product_models.Category.objects.create(name="Cat-hidden")
    hidden = product_models.Item.objects.create(name="Secret", category=cat, is_private=True)
    # Even an anonymous caller (who would be denied an authorization check) gets
    # not-found first - the row is invisible, so no "not authorized" signal leaks
    # that it exists.
    res = _execute(
        schema,
        "mutation($id: ID!, $d: ItemPartialInput!){ updateItem(id:$id, data:$d){ "
        "node{ name } errors{ field } } }",
        AnonymousUser(),
        {"id": global_id_for(ItemT, hidden.pk), "d": {"name": "Leak"}},
    )
    assert res.errors is None, res.errors
    payload = res.data["updateItem"]
    assert payload["node"] is None
    assert payload["errors"][0]["field"] == "id"


@pytest.mark.django_db
def test_permission_classes_override_allow_all_lets_anonymous_through():
    """A custom allow-all ``permission_classes`` override lets an anonymous caller create."""

    class AllowAll:
        def has_permission(
            self,
            info,
            mutation,
            operation,
            data,
            instance=None,
        ):
            return True

    schema, (CategoryT, _ItemT) = _build_auth_schema(create_permission_classes=[AllowAll])
    cat = product_models.Category.objects.create(name="Cat-allowall")
    res = _execute(
        schema,
        _CREATE_Q,
        AnonymousUser(),
        {"d": {"name": "Open", "categoryId": global_id_for(CategoryT, cat.pk)}},
    )
    assert res.errors is None, res.errors
    assert res.data["createItem"]["node"]["name"] == "Open"


@pytest.mark.django_db
def test_permission_classes_override_deny_blocks_permitted_caller():
    """A custom deny-all override blocks an otherwise-permitted caller (proving the override path)."""

    class DenyAll:
        def has_permission(
            self,
            info,
            mutation,
            operation,
            data,
            instance=None,
        ):
            return False

    schema, (CategoryT, _ItemT) = _build_auth_schema(create_permission_classes=[DenyAll])
    cat = product_models.Category.objects.create(name="Cat-denyall")
    user = _user_with_perms("add_item")  # holds the default perm, still denied by override
    res = _execute(
        schema,
        _CREATE_Q,
        user,
        {"d": {"name": "Nope", "categoryId": global_id_for(CategoryT, cat.pk)}},
    )
    assert res.errors is not None
    assert not product_models.Item.objects.filter(name="Nope").exists()


@pytest.mark.django_db
def test_async_has_permission_is_rejected_not_bypassed():
    """An async ``has_permission`` raises SyncMisuseError, never a silent allow (feedback - async bypass).

    A coroutine is truthy, so a naive ``if not has_permission(...)`` would treat an
    async deny-check as ALLOW - an authorization bypass. The sync pipeline cannot
    await the coroutine, so it is closed and raised as a ``SyncMisuseError`` (surfacing
    as a top-level GraphQL error), and crucially NO row is written: the deny is
    honored, not bypassed.
    """

    class AsyncDeny:
        async def has_permission(
            self,
            info,
            mutation,
            operation,
            data,
            instance=None,
        ):
            return False

    schema, (CategoryT, _ItemT) = _build_auth_schema(create_permission_classes=[AsyncDeny])
    cat = product_models.Category.objects.create(name="Cat-asyncdeny")
    res = _execute(
        schema,
        _CREATE_Q,
        AnonymousUser(),
        {"d": {"name": "AsyncBlocked", "categoryId": global_id_for(CategoryT, cat.pk)}},
    )
    assert res.errors is not None
    assert "coroutine" in res.errors[0].message.lower()
    assert not product_models.Item.objects.filter(name="AsyncBlocked").exists()


@pytest.mark.django_db
def test_async_check_permission_override_is_rejected_not_bypassed():
    """An async ``check_permission`` override raises SyncMisuseError, not a silent allow (feedback).

    The override returns a coroutine; ``authorize_or_raise`` closes it and raises
    ``SyncMisuseError`` rather than treating the truthy coroutine as authorized. No
    row is written.
    """

    class CategoryT(DjangoType, relay.Node):
        class Meta:
            model = product_models.Category
            fields = ("id", "name")
            primary = True

    class ItemT(DjangoType, relay.Node):
        class Meta:
            model = product_models.Item
            fields = ("id", "name")
            primary = True

    class AsyncCheckCreateItem(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "create"

        async def check_permission(
            self,
            info,
            operation,
            data,
            instance=None,
        ):
            return False

    @strawberry.type
    class Mutation:
        create_item = DjangoMutationField(AsyncCheckCreateItem)

    finalize_django_types()
    schema = strawberry.Schema(query=_Query, mutation=Mutation)
    cat = product_models.Category.objects.create(name="Cat-asynccheck")
    res = _execute(
        schema,
        _CREATE_Q,
        AnonymousUser(),
        {"d": {"name": "AsyncCheckBlocked", "categoryId": global_id_for(CategoryT, cat.pk)}},
    )
    assert res.errors is not None
    assert "coroutine" in res.errors[0].message.lower()
    assert not product_models.Item.objects.filter(name="AsyncCheckBlocked").exists()


def test_request_without_user_attribute_is_denied():
    """A request carrying no ``user`` attribute is denied (the ``user is None`` guard).

    Distinct from the ``AnonymousUser`` case (denied later via ``has_perm``): under a
    live request ``AuthenticationMiddleware`` always sets ``request.user``, so this
    guard only fires when the resolved request has no ``user`` at all (a bare context
    / no auth middleware). It returns ``False`` before resolving the model, so the
    branch is unreachable from a live ``/graphql/`` request and is earned here.
    """
    mutation = _create_item_mutation()
    info = SimpleNamespace(context=SimpleNamespace(request=SimpleNamespace()))
    assert DjangoModelPermission().has_permission(info, mutation, "create", data=None) is False
