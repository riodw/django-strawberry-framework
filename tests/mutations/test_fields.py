"""``DjangoMutationField`` factory tests (spec-036 Slice 3).

System-under-test is ``mutations/fields.py``: the per-operation argument-signature
synthesis, the no-class-attribute-annotation form typed via a ``strawberry.lazy``
payload return-ref, the payload-resolves-only-after-bind timing, the runtime
sync-vs-async resolver selection, and the construction-time target guard.
"""

from __future__ import annotations

import sys

import pytest
import strawberry
from apps.products import models as product_models
from strawberry import relay

from django_strawberry_framework import (
    DjangoMutation,
    DjangoMutationField,
    DjangoType,
    finalize_django_types,
)
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.mutations.inputs import INPUTS_MODULE_PATH
from django_strawberry_framework.registry import registry
from django_strawberry_framework.testing.relay import global_id_for


@pytest.fixture(autouse=True)
def _isolate_registry():
    registry.clear()
    yield
    registry.clear()


class _AllowAll:
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


def _declare_item_primaries():
    class CategoryT(DjangoType, relay.Node):
        class Meta:
            model = product_models.Category
            fields = ("id", "name")
            primary = True

    class ItemT(DjangoType, relay.Node):
        class Meta:
            model = product_models.Item
            fields = ("id", "name", "category")
            primary = True

    return CategoryT, ItemT


def _operation_mutations():
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

    return CreateItem, UpdateItem, DeleteItem


def _field_arg_map(schema: strawberry.Schema, field_name: str) -> dict[str, str]:
    """Return ``{arg_name: type_str}`` for a Mutation field from the built schema."""
    mutation_type = schema._schema.mutation_type
    field = mutation_type.fields[field_name]
    return {arg_name: str(arg.type) for arg_name, arg in field.args.items()}


# ---------------------------------------------------------------------------
# Per-operation argument signature (Decision 14)
# ---------------------------------------------------------------------------


def test_per_operation_argument_signatures():
    """create -> ``data: ItemInput!``; update -> ``id`` + ``data: ItemPartialInput!``; delete -> ``id``."""
    _declare_item_primaries()
    CreateItem, UpdateItem, DeleteItem = _operation_mutations()

    @strawberry.type
    class Mutation:
        create_item = DjangoMutationField(CreateItem)
        update_item = DjangoMutationField(UpdateItem)
        delete_item = DjangoMutationField(DeleteItem)

    finalize_django_types()
    schema = strawberry.Schema(query=_Query, mutation=Mutation)

    create_args = _field_arg_map(schema, "createItem")
    assert create_args == {"data": "ItemInput!"}

    update_args = _field_arg_map(schema, "updateItem")
    assert update_args == {"id": "ID!", "data": "ItemPartialInput!"}

    delete_args = _field_arg_map(schema, "deleteItem")
    assert delete_args == {"id": "ID!"}


def test_no_class_attribute_annotation_builds_and_types_payload():
    """A field assigned with NO annotation builds a schema and types to ``<Name>Payload!``.

    The primary-vs-``.field()``-fallback proof (Decision 5 / Decision 7): the
    no-annotation ``create_item = DjangoMutationField(CreateItem)`` form must build
    a schema after finalize and the field must type to the generated payload via
    the lazy ref. (If this assertion ever fails at schema build, that triggers the
    documented ``.field()`` contingency.)
    """
    _declare_item_primaries()
    CreateItem, _UpdateItem, _DeleteItem = _operation_mutations()

    @strawberry.type
    class Mutation:
        create_item = DjangoMutationField(CreateItem)

    finalize_django_types()
    schema = strawberry.Schema(query=_Query, mutation=Mutation)
    mutation_type = schema._schema.mutation_type
    assert str(mutation_type.fields["createItem"].type) == "CreateItemPayload!"


def test_payload_lazy_ref_resolves_to_materialized_payload_after_bind():
    """The field's return type resolves to the payload materialized at finalize phase 2.5."""
    _declare_item_primaries()
    CreateItem, _UpdateItem, _DeleteItem = _operation_mutations()

    @strawberry.type
    class Mutation:
        create_item = DjangoMutationField(CreateItem)

    finalize_django_types()
    # The bind materialized ``CreateItemPayload`` as a module global of
    # ``mutations.inputs``; building the schema resolves the lazy ref to it.
    inputs_module = sys.modules[INPUTS_MODULE_PATH]
    assert hasattr(inputs_module, "CreateItemPayload")
    schema = strawberry.Schema(query=_Query, mutation=Mutation)
    # The schema's CreateItemPayload type is the one bound to the materialized class.
    payload_type = schema._schema.type_map["CreateItemPayload"]
    assert payload_type is not None


@pytest.mark.django_db
def test_sync_and_async_resolver_selection():
    """The same field resolves under ``execute_sync`` and ``await execute`` (runtime dispatch)."""
    CategoryT, _ItemT = _declare_item_primaries()
    CreateItem, _UpdateItem, _DeleteItem = _operation_mutations()

    @strawberry.type
    class Mutation:
        create_item = DjangoMutationField(CreateItem)

    finalize_django_types()
    schema = strawberry.Schema(query=_Query, mutation=Mutation)

    query = "mutation($d: ItemInput!){ createItem(data:$d){ node{ name } errors{ field } } }"
    cat = product_models.Category.objects.create(name="Cat-sync")
    sync_res = schema.execute_sync(
        query,
        variable_values={"d": {"name": "S", "categoryId": global_id_for(CategoryT, cat.pk)}},
    )
    assert sync_res.errors is None, sync_res.errors
    assert sync_res.data["createItem"]["node"]["name"] == "S"


@pytest.mark.django_db(transaction=True)
async def test_async_resolver_selection_works():
    """The runtime ``in_async_context()`` dispatch resolves the same field on the async surface.

    ``transaction=True`` is load-bearing (spec-036 FV-1): the async create runs its
    ``transaction.atomic()`` write inside one ``sync_to_async(thread_sensitive=
    True)`` call (AR-M4), committing on asgiref's executor-thread connection, which
    plain ``django_db``'s main-thread rollback cannot reach. Under plain
    ``django_db`` the committed row escapes per-test rollback and pollutes a later
    read-side optimizer execution. ``transaction=True`` (the suite-wide async-ORM
    convention) reaps the cross-thread-committed rows at teardown; the leak is
    pinned by ``test_resolvers.py::test_async_mutation_does_not_leak_into_later_read_optimizer_execution``.
    """
    CategoryT, _ItemT = _declare_item_primaries()
    CreateItem, _UpdateItem, _DeleteItem = _operation_mutations()

    @strawberry.type
    class Mutation:
        create_item = DjangoMutationField(CreateItem)

    finalize_django_types()
    schema = strawberry.Schema(query=_Query, mutation=Mutation)

    query = "mutation($d: ItemInput!){ createItem(data:$d){ node{ name } errors{ field } } }"
    cat = await product_models.Category.objects.acreate(name="Cat-async")
    res = await schema.execute(
        query,
        variable_values={"d": {"name": "A", "categoryId": global_id_for(CategoryT, cat.pk)}},
    )
    assert res.errors is None, res.errors
    assert res.data["createItem"]["node"]["name"] == "A"


# ---------------------------------------------------------------------------
# Construction-time target guard
# ---------------------------------------------------------------------------


def test_non_mutation_target_raises_at_construction():
    """``DjangoMutationField`` over a non-``DjangoMutation`` raises naming the factory."""

    class NotAMutation:
        pass

    with pytest.raises(ConfigurationError, match="DjangoMutationField"):
        DjangoMutationField(NotAMutation)


def test_non_class_target_raises_at_construction():
    """A non-class value raises at the construction line."""
    with pytest.raises(ConfigurationError, match="DjangoMutationField"):
        DjangoMutationField(object())


def test_abstract_base_target_raises_at_construction():
    """The abstract ``DjangoMutation`` base (no ``Meta`` -> no ``_mutation_meta``) is rejected."""
    with pytest.raises(ConfigurationError, match="abstract base"):
        DjangoMutationField(DjangoMutation)


# ---------------------------------------------------------------------------
# Three-axis generalization (spec-038 Slice 3)
# ---------------------------------------------------------------------------


def test_generalized_target_accepts_modelform_and_plain_form_family():
    """``DjangoMutationField`` accepts both form-mutation flavors (the duck-typed target check).

    The Slice-3 generalization recognizes the mutation / form family by the
    duck-typed ``_mutation_meta`` + ``resolve_sync`` / ``resolve_async`` +
    ``input_type_name`` / ``input_module_path`` protocol, NOT
    ``issubclass(DjangoMutation)`` - so a ``DjangoModelFormMutation`` (a
    ``DjangoMutation`` subclass) AND a plain ``DjangoFormMutation`` (NOT a
    ``DjangoMutation`` subclass) both construct without raising.
    """
    from django import forms

    from django_strawberry_framework import DjangoFormMutation, DjangoModelFormMutation

    class ItemModelForm(forms.ModelForm):
        class Meta:
            model = product_models.Item
            fields = ("name", "category")

    class ContactForm(forms.Form):
        message = forms.CharField()

    class CreateItemForm(DjangoModelFormMutation):
        class Meta:
            form_class = ItemModelForm
            operation = "create"
            permission_classes = [_AllowAll]

    class Submit(DjangoFormMutation):
        class Meta:
            form_class = ContactForm
            permission_classes = []

    # Neither construction raises (the family is accepted).
    assert DjangoMutationField(CreateItemForm) is not None
    assert DjangoMutationField(Submit) is not None


def test_model_flavor_dispatch_unchanged():
    """A ``DjangoMutation`` target still names ``mutations.inputs`` for ``data:`` + routes the model pipeline.

    The no-regression pin: the generalized ``data:`` lazy-ref consults the model
    base's ``input_module_path`` default (``mutations.inputs``), the synthesized
    signature is unchanged per operation, and the seam dispatch
    (``resolve_sync`` / ``resolve_async``) delegates to the model pipeline.
    """
    _declare_item_primaries()
    CreateItem, UpdateItem, DeleteItem = _operation_mutations()

    @strawberry.type
    class Mutation:
        create_item = DjangoMutationField(CreateItem)
        update_item = DjangoMutationField(UpdateItem)
        delete_item = DjangoMutationField(DeleteItem)

    finalize_django_types()
    schema = strawberry.Schema(query=_Query, mutation=Mutation)

    # The model ``data:`` input materializes in ``mutations.inputs`` (NOT
    # ``forms.inputs``); the field args are the unchanged per-operation shape.
    inputs_module = sys.modules[INPUTS_MODULE_PATH]
    assert hasattr(inputs_module, "ItemInput")
    assert _field_arg_map(schema, "createItem") == {"data": "ItemInput!"}
    assert _field_arg_map(schema, "updateItem") == {"id": "ID!", "data": "ItemPartialInput!"}
    assert _field_arg_map(schema, "deleteItem") == {"id": "ID!"}
    # The model seam default routes to the model resolver pipeline.
    from django_strawberry_framework.mutations import resolvers as mutation_resolvers

    assert CreateItem.resolve_sync.__func__ is DjangoMutation.resolve_sync.__func__
    assert mutation_resolvers.resolve_mutation_sync is not None


@pytest.mark.django_db
def test_django_mutation_field_generalizes_to_serializer_mutation():
    """`DjangoMutationField` accepts a `SerializerMutation` and routes its resolver seam (Decision 5).

    The spec-038-generalized factory was "for the 0.0.13 serializer flavor"; Slice 3
    VERIFIES the generalization holds with NO `mutations/fields.py` edit: a create
    `SerializerMutation` over the products `ItemSerializer`, wrapped with
    `DjangoMutationField`, finalizes and exposes the `data: ItemSerializerInput!`
    argument (the lazy ref resolves the serializer-derived input in
    `rest_framework.inputs`), and the class routes `resolve_sync` to
    `rest_framework.resolvers`.

    `SerializerMutation` is imported BY NAME from the package root (NOT via the root
    `__all__` / star import, which stays DRF-free while DRF is soft - F1).
    """
    from rest_framework import serializers

    from django_strawberry_framework import SerializerMutation

    _declare_item_primaries()

    class ItemSerializer(serializers.ModelSerializer):
        class Meta:
            model = product_models.Item
            fields = ("name", "category")

    class CreateItemViaSerializer(SerializerMutation):
        class Meta:
            serializer_class = ItemSerializer
            operation = "create"
            permission_classes = [_AllowAll]

    @strawberry.type
    class Mutation:
        create_item_via_serializer = DjangoMutationField(CreateItemViaSerializer)

    finalize_django_types()
    schema = strawberry.Schema(query=_Query, mutation=Mutation)

    # The serializer `data:` input materializes in `rest_framework.inputs` (NOT
    # `mutations.inputs`); the generated create argument is the serializer input.
    from django_strawberry_framework.rest_framework.inputs import SERIALIZER_INPUTS_MODULE_PATH

    serializer_inputs_module = sys.modules[SERIALIZER_INPUTS_MODULE_PATH]
    assert hasattr(serializer_inputs_module, "ItemSerializerInput")
    assert _field_arg_map(schema, "createItemViaSerializer") == {"data": "ItemSerializerInput!"}

    # The serializer seam routes to the serializer resolver pipeline (NOT the model
    # default), and the resolver module exposes the entry the seam delegates to.
    from django_strawberry_framework.rest_framework import resolvers as serializer_resolvers

    assert (
        CreateItemViaSerializer.resolve_sync.__func__ is SerializerMutation.resolve_sync.__func__
    )
    assert (
        CreateItemViaSerializer.resolve_sync.__func__ is not DjangoMutation.resolve_sync.__func__
    )
    assert serializer_resolvers.resolve_serializer_sync is not None
