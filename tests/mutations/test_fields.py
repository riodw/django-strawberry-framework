"""``DjangoMutationField`` factory tests.

Construction-time factory: annotation-less field typing, lazy payload bind,
target guards, metadata passthrough, and flavor dispatch identity. The shipped
create/update/delete argument map is live in
``examples/fakeshop/test_query/test_products_api.py::test_create_update_delete_item_argument_signatures_over_http``;
async colour of the same field is
``examples/fakeshop/test_query/test_products_api.py::test_create_item_over_graphql_async``.
A request cannot observe ``CreateItemPayload!`` bind identity or a
``ConfigurationError`` raised at ``DjangoMutationField(...)`` construction.
"""

from __future__ import annotations

import sys
from collections.abc import Iterator
from typing import NoReturn

import pytest
import strawberry
from apps.products import models as product_models
from django import forms
from strawberry import relay
from typing_extensions import override

from django_strawberry_framework import (
    DjangoFormMutation,
    DjangoMutation,
    DjangoMutationField,
    DjangoSchema,
    DjangoType,
    finalize_django_types,
)
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.forms.sets import DjangoFormMutationMetaclass
from django_strawberry_framework.mutations.inputs import INPUTS_MODULE_PATH
from django_strawberry_framework.mutations.sets import DjangoMutationMetaclass
from django_strawberry_framework.registry import registry


@pytest.fixture(autouse=True)
def _isolate_registry() -> Iterator[None]:
    registry.clear()
    yield
    registry.clear()


class _AllowAll:
    def has_permission(
        self,
        _info: object,
        _mutation: type[object],
        _operation: str,
        _data: object,
        _instance: object = None,
    ) -> bool:
        return True


@strawberry.type
class _Query:
    @strawberry.field
    def ping(self) -> int:
        return 1


def _declare_item_primaries() -> tuple[type[DjangoType], type[DjangoType]]:
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


def _operation_mutations() -> tuple[type[DjangoMutation], ...]:
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
    assert mutation_type is not None
    field = mutation_type.fields[field_name]
    return {arg_name: str(arg.type) for arg_name, arg in field.args.items()}


def test_no_class_attribute_annotation_builds_and_types_payload() -> None:
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
    schema = DjangoSchema(query=_Query, mutation=Mutation)
    mutation_type = schema._schema.mutation_type
    assert mutation_type is not None
    assert str(mutation_type.fields["createItem"].type) == "CreateItemPayload!"


def test_payload_lazy_ref_resolves_to_materialized_payload_after_bind() -> None:
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
    schema = DjangoSchema(query=_Query, mutation=Mutation)
    # The schema's CreateItemPayload type is the one bound to the materialized class.
    payload_type = schema._schema.type_map["CreateItemPayload"]
    assert payload_type is not None


# ---------------------------------------------------------------------------
# Construction-time target guard
# ---------------------------------------------------------------------------


def test_non_mutation_target_raises_at_construction() -> None:
    """``DjangoMutationField`` over a non-``DjangoMutation`` raises naming the factory."""

    class NotAMutation:
        pass

    with pytest.raises(ConfigurationError, match="DjangoMutationField"):
        # basedpyright: the non-mutation class is the hostile input under test; DjangoMutationField
        # types the parameter as WriteMutationClass
        DjangoMutationField(NotAMutation)  # pyright: ignore[reportArgumentType]


def test_non_class_target_raises_at_construction() -> None:
    """A non-class value raises at the construction line."""
    with pytest.raises(ConfigurationError, match="DjangoMutationField"):
        # basedpyright: the non-class value is the hostile input under test; DjangoMutationField
        # types the parameter as WriteMutationClass
        DjangoMutationField(object())  # pyright: ignore[reportArgumentType]


def test_hostile_non_class_target_repr_still_raises_configuration_error() -> None:
    """A rejected target's repr cannot replace the construction-time configuration error."""

    class HostileTarget:
        @override
        def __repr__(self) -> str:
            raise RuntimeError("repr boom")

    with pytest.raises(ConfigurationError, match="DjangoMutationField") as exc:
        # basedpyright: the non-class value whose repr raises is the hostile input under test;
        # DjangoMutationField types the parameter as WriteMutationClass
        DjangoMutationField(HostileTarget())  # pyright: ignore[reportArgumentType]
    assert "unprintable" in str(exc.value)


def test_abstract_base_target_raises_at_construction() -> None:
    """The abstract ``DjangoMutation`` base (no ``Meta`` -> no ``_mutation_meta``) is rejected."""
    with pytest.raises(ConfigurationError, match="abstract base"):
        DjangoMutationField(DjangoMutation)


def test_inherited_meta_target_rejected_at_construction() -> None:
    """An inherited snapshot cannot make an unregistered child a concrete mutation."""
    from django import forms

    from django_strawberry_framework import DjangoFormMutation
    from django_strawberry_framework.forms.sets import iter_form_mutations
    from django_strawberry_framework.mutations.sets import iter_mutations

    class CreateItem(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "create"
            permission_classes = [_AllowAll]

    # Inherits ``_mutation_meta`` without its own ``Meta`` -> unregistered -> rejected HERE.
    class CreateItemSubclass(CreateItem):
        pass

    class ContactForm(forms.Form):
        message = forms.CharField()

    class Submit(DjangoFormMutation):
        class Meta:
            form_class = ContactForm
            permission_classes = [_AllowAll]

    class SubmitSubclass(Submit):
        pass

    cases = (
        (CreateItem, CreateItemSubclass, iter_mutations),
        (Submit, SubmitSubclass, iter_form_mutations),
    )
    for parent, child, declarations in cases:
        assert child._mutation_meta is parent._mutation_meta
        assert "_mutation_meta" not in child.__dict__
        assert child not in declarations()
        with pytest.raises(ConfigurationError, match="own nested Meta"):
            DjangoMutationField(child)

    class CreateItemRedeclared(CreateItem):
        # basedpyright: DjangoMutation's metaclass reads only the class body's own ``Meta``; the
        # child declares a fresh one, never a subclass of the parent's
        class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
            model = product_models.Item
            operation = "create"
            permission_classes = [_AllowAll]

    assert "_mutation_meta" in CreateItemRedeclared.__dict__
    assert CreateItemRedeclared in iter_mutations()
    assert DjangoMutationField(CreateItemRedeclared) is not None

    registry.clear()
    assert CreateItemRedeclared._mutation_meta is not None
    assert CreateItemRedeclared not in iter_mutations()
    with pytest.raises(ConfigurationError, match="current registry lifecycle"):
        DjangoMutationField(CreateItemRedeclared)


class _ByNameMutationMetaclass(DjangoMutationMetaclass):
    """Equates two mutation classes by qualified name, as a reload-tolerant metaclass might."""

    @override
    def __eq__(self, other: object) -> bool:
        return isinstance(other, type) and other.__qualname__ == self.__qualname__

    __hash__ = DjangoMutationMetaclass.__hash__


class _ByNameFormMutationMetaclass(DjangoFormMutationMetaclass):
    """The plain-form twin of ``_ByNameMutationMetaclass``."""

    @override
    def __eq__(self, other: object) -> bool:
        return isinstance(other, type) and other.__qualname__ == self.__qualname__

    __hash__ = DjangoFormMutationMetaclass.__hash__


def _declare_by_name_mutation(flavor: str) -> type[DjangoMutation | DjangoFormMutation]:
    """Declare one fresh class per call, every call under the same qualified name."""
    if flavor == "model":

        class CreateItem(DjangoMutation, metaclass=_ByNameMutationMetaclass):
            class Meta:
                model = product_models.Item
                operation = "create"
                permission_classes = [_AllowAll]

        return CreateItem

    class ContactForm(forms.Form):
        message = forms.CharField()

    class Submit(DjangoFormMutation, metaclass=_ByNameFormMutationMetaclass):
        class Meta:
            form_class = ContactForm
            permission_classes = [_AllowAll]

    return Submit


@pytest.mark.parametrize(("flavor", "name"), [("model", "CreateItem"), ("form", "Submit")])
def test_stale_target_equal_to_its_redeclaration_rejected_at_construction(
    flavor: str,
    name: str,
) -> None:
    """Ledger membership is identity, so a metaclass ``__eq__`` cannot pass a drained target.

    The class ``registry.clear()`` drained compares equal to its redeclaration in
    the current ledger, yet finalization binds only the redeclaration.
    """
    stale = _declare_by_name_mutation(flavor)
    registry.clear()
    current = _declare_by_name_mutation(flavor)
    assert stale == current
    assert stale is not current
    with pytest.raises(ConfigurationError) as exc:
        DjangoMutationField(stale)
    assert str(exc.value) == (
        f"DjangoMutationField target {name} is not registered for finalization "
        "in the current registry lifecycle. Declare the mutation after the most recent "
        "registry.clear()."
    )
    assert DjangoMutationField(current) is not None


class _RaisingEqMutationMetaclass(DjangoMutationMetaclass):
    """A mutation metaclass whose ``__eq__`` raises."""

    @override
    def __eq__(self, other: object) -> bool:
        raise RuntimeError("eq boom")

    __hash__ = DjangoMutationMetaclass.__hash__


def test_registered_target_with_raising_metaclass_eq_constructs() -> None:
    """The ledger check never compares a target with another declaration."""

    class CreateItem(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "create"
            permission_classes = [_AllowAll]

    class UpdateItem(DjangoMutation, metaclass=_RaisingEqMutationMetaclass):
        class Meta:
            model = product_models.Item
            operation = "update"
            permission_classes = [_AllowAll]

    assert DjangoMutationField(CreateItem) is not None
    assert DjangoMutationField(UpdateItem) is not None


# ---------------------------------------------------------------------------
# Three-axis generalization (spec-038)
# ---------------------------------------------------------------------------


def test_generalized_target_accepts_modelform_and_plain_form_family() -> None:
    """``DjangoMutationField`` accepts both form-mutation flavors (the duck-typed target check).

    The generalization recognizes the mutation / form family by the
    duck-typed ``_mutation_meta`` + ``resolve_sync`` / ``resolve_async`` +
    ``input_type_name`` / ``input_module_path`` protocol, NOT
    ``issubclass(DjangoMutation)`` - so a ``DjangoModelFormMutation`` (a
    ``DjangoMutation`` subclass) AND a plain ``DjangoFormMutation`` (NOT a
    ``DjangoMutation`` subclass) both construct without raising.
    """
    from django import forms

    from django_strawberry_framework import DjangoFormMutation, DjangoModelFormMutation

    class ItemModelForm(forms.ModelForm[product_models.Item]):
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


def test_model_flavor_dispatch_unchanged() -> None:
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
    schema = DjangoSchema(query=_Query, mutation=Mutation)

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
def test_django_mutation_field_generalizes_to_serializer_mutation() -> None:
    """`DjangoMutationField` accepts a `SerializerMutation` and routes its resolver seam (Decision 5).

    The spec-038-generalized factory was written "for the 0.0.13 serializer flavor";
    this VERIFIES the generalization holds with NO `mutations/fields.py` edit: a create
    `SerializerMutation` over the products `ItemSerializer`, wrapped with
    `DjangoMutationField`, finalizes and exposes the `data: ItemSerializerInput!`
    argument (the lazy ref resolves the serializer-derived input in
    `rest_framework.inputs`), and the class routes `resolve_sync` to
    `rest_framework.resolvers`.

    `SerializerMutation` is imported BY NAME from the package root (NOT via the root
    `__all__` / star import, which stays DRF-free while DRF is soft).
    """
    from django_strawberry_framework import SerializerMutation
    from tests._idioms import ModelSerializerBase

    _declare_item_primaries()

    class ItemSerializer(ModelSerializerBase[product_models.Item]):
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
    schema = DjangoSchema(query=_Query, mutation=Mutation)

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


def test_mutation_field_metadata_passthrough() -> None:
    """`DjangoMutationField` forwards description and deprecation_reason to Strawberry."""
    _declare_item_primaries()
    CreateItem, _, _ = _operation_mutations()

    @strawberry.type
    class Mutation:
        create_item = DjangoMutationField(
            CreateItem,
            description="Create a new item entity",
            deprecation_reason="Use createItemV2 instead",
        )

    finalize_django_types()
    schema = DjangoSchema(query=_Query, mutation=Mutation)
    mutation_type = schema._schema.mutation_type
    assert mutation_type is not None
    field = mutation_type.fields["createItem"]
    assert field.description == "Create a new item entity"
    assert field.deprecation_reason == "Use createItemV2 instead"


# ---------------------------------------------------------------------------
# Hostile directives containment (hunt 0.0.15)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("bare", ["@deprecated", b"@deprecated"])
def test_bare_string_or_bytes_directives_raise_at_construction(bare: str | bytes) -> None:
    """A bare str / bytes `directives` is rejected at the construction line.

    Strawberry consumes field directives lazily at class decoration / SDL render,
    so an unvalidated value fails THERE, far from the assignment line: a bare
    `str` is iterated character-wise and raises a raw
    `AttributeError: 'str' object has no attribute '__strawberry_directive__'`
    at schema build, while a `bytes` (iterating into ints) builds silently and
    crashes SDL render the same way. The factory must fail loud as
    `ConfigurationError` naming `DjangoMutationField` at the assignment line -
    the same fail-loud posture the auth fixed-field factories carry (the
    containment is single-sited in
    `utils/directives.py::validated_field_directives` and shared with them).
    """
    _declare_item_primaries()
    CreateItem, _, _ = _operation_mutations()

    with pytest.raises(ConfigurationError, match="directives must be a sequence"):
        DjangoMutationField(CreateItem, directives=bare)


def test_hostile_directives_iterator_raises_at_construction() -> None:
    """An iterator that raises midway fails as ConfigurationError, never ValueError."""
    _declare_item_primaries()
    CreateItem, _, _ = _operation_mutations()

    class HostileDirectives(tuple[object, ...]):
        @override
        def __iter__(self) -> Iterator[object]:
            return self

        def __next__(self) -> NoReturn:
            raise ValueError("boom")

    with pytest.raises(ConfigurationError, match="directives could not be read") as exc:
        DjangoMutationField(CreateItem, directives=HostileDirectives())
    assert isinstance(exc.value.__cause__, ValueError)


def test_non_iterable_directives_raise_configuration_error() -> None:
    """A non-iterable `directives` value fails loud instead of a raw TypeError."""
    _declare_item_primaries()
    CreateItem, _, _ = _operation_mutations()

    with pytest.raises(ConfigurationError, match="directives could not be read") as exc:
        # basedpyright: the non-iterable directives value is the hostile input under test;
        # DjangoMutationField types the parameter as Sequence[object]
        DjangoMutationField(CreateItem, directives=42)  # pyright: ignore[reportArgumentType]
    assert isinstance(exc.value.__cause__, TypeError)


def test_valid_directives_reach_the_built_field() -> None:
    """A real directive sequence survives the containment and lands on the field.

    The happy-path pin over the containment: the tuple conversion must forward a
    genuine directive sequence unchanged, and the built schema renders it on the
    field's SDL - the containment rejects hostile shapes without swallowing the
    supported one.
    """
    from strawberry.schema_directive import Location, schema_directive

    @schema_directive(locations=[Location.FIELD_DEFINITION], name="tagged")
    class Tagged:
        value: str

    _declare_item_primaries()
    CreateItem, _, _ = _operation_mutations()

    @strawberry.type
    class Mutation:
        create_item = DjangoMutationField(CreateItem, directives=[Tagged(value="x")])

    finalize_django_types()
    schema = DjangoSchema(query=_Query, mutation=Mutation)
    sdl = str(schema)
    assert '@tagged(value: "x")' in sdl
