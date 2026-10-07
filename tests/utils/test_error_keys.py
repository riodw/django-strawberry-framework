"""Every write flavor keys a validator error to the GraphQL input field the client sent.

One matrix over the flavors that run a validator ({model ``DjangoMutation``,
``DjangoModelFormMutation``, plain ``DjangoFormMutation``, serializer
``is_valid()``, serializer save-time Django ``ValidationError``, auth
``register``}) x the key shapes a validator name can take against its input
({multi-word, forward-key suffix, forward-key column name, rename, unexposed field,
non-field}). Each cell
raises one error from the flavor's own validator seam under the validator-side
name and asserts the envelope key and ``path``: the GraphQL input name for an
exposed field, the validator-side name verbatim for a field the input does not
expose, and ``"__all__"`` with an empty ``path`` for a non-field error. The
shared key map is ``django_strawberry_framework/utils/errors.py::build_error_key_map``;
a new flavor joins this matrix rather than growing its own keying.

Cells a flavor cannot express are absent, not skipped: forms and ``register``
have no ``Meta.input_class`` rename, and a form error names the form field, never
a forward key's column name. ``register`` x forward-key needs a user model whose
``REQUIRED_FIELDS`` names a forward key; the stock user has none and
``get_user_model()`` cannot be swapped per test, so that cell is left to the model
flavor's forward-key cells, which run the same tail ``register`` delegates to.
The live rows (stock kanban ``setCardStatus``, products ``updateItemViaForm``,
library ``createPublisher`` and ``createShelfViaSubclassedSerializer``) live in
``examples/fakeshop/test_query/``.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from types import SimpleNamespace
from typing import TYPE_CHECKING, NoReturn

import pytest
import strawberry
from apps.products import models as product_models
from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Model, UniqueConstraint
from django.http import HttpRequest
from rest_framework import serializers
from strawberry import relay
from typing_extensions import override

from django_strawberry_framework import (
    DjangoFormMutation,
    DjangoModelFormMutation,
    DjangoMutation,
    DjangoMutationField,
    DjangoSchema,
    DjangoType,
    SerializerMutation,
    finalize_django_types,
)
from django_strawberry_framework.auth import register_mutation
from django_strawberry_framework.mutations.inputs import NON_FIELD_ERROR_KEY
from django_strawberry_framework.registry import registry
from django_strawberry_framework.testing.relay import global_id_for

if TYPE_CHECKING:
    from django_strawberry_framework.rest_framework.serializer_converter import DRFSerializer

#: The error a cell's validator raises: ``(validator-side name, message)``, or
#: ``(None, message)`` for a non-field error.
_Raised = tuple[str | None, str]
#: A flavor runner: ``(shape, raised) -> [(field, path), ...]`` from the payload.
_Runner = Callable[[str, _Raised, pytest.MonkeyPatch], list[tuple[str, list[str]]]]


@pytest.fixture(autouse=True)
def _isolate_registry() -> Iterator[None]:
    """Reset the registry (co-clears the mutation ledger + declaration registry) per test."""
    registry.clear()
    yield
    registry.clear()


class _AllowAll:
    """A permission class that authorizes every write (isolates keying from auth)."""

    def has_permission(
        self,
        info: object,
        mutation: type[object],
        operation: str,
        data: object,
        instance: object = None,
    ):
        return True


@strawberry.type
class _Query:
    @strawberry.field
    def ping(self) -> int:
        return 1


def _django_error(raised: _Raised) -> DjangoValidationError:
    """The Django ``ValidationError`` for ``raised``: field-keyed, or a bare non-field one."""
    name, message = raised
    return (
        DjangoValidationError(message) if name is None else DjangoValidationError({name: message})
    )


def _category_types() -> tuple[type[DjangoType], type[DjangoType]]:
    """Declare the Relay ``Category`` / ``Item`` primaries the product shapes decode against."""

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


def _execute(
    mutation_field: object,
    data_literal: Callable[[], str],
) -> list[tuple[str, list[str]]]:
    """Finalize a one-field ``write`` schema, send ``data_literal()``, return ``(field, path)``s.

    ``data_literal`` runs after finalization, so it can mint GlobalIDs.
    """

    @strawberry.type
    class Mutation:
        write = mutation_field

    finalize_django_types()
    schema = DjangoSchema(query=_Query, mutation=Mutation, error_policy={"enabled": False})
    request = HttpRequest()
    # basedpyright: a duck-typed stand-in user; django-stubs types request.user as
    # AbstractBaseUser | AnonymousUser
    request.user = SimpleNamespace(username="u", is_authenticated=True)  # pyright: ignore[reportAttributeAccessIssue]
    result = schema.execute_sync(
        f"mutation {{ write(data: {{ {data_literal()} }}) {{ errors {{ field path }} }} }}",
        context_value=SimpleNamespace(request=request),
    )
    assert result.errors is None, result.errors
    assert result.data is not None
    keys: list[tuple[str, list[str]]] = []
    for error in result.data["write"]["errors"]:
        field, path = error["field"], error["path"]
        assert isinstance(field, str)
        assert isinstance(path, list)
        keys.append((field, [str(segment) for segment in path]))
    return keys


def _category_gid(category_type: type[DjangoType]) -> str:
    category, _created = product_models.Category.objects.get_or_create(name="Keyed category")
    return global_id_for(category_type, category.pk)


# --------------------------------------------------------------------------- model


def _run_model(shape: str, raised: _Raised, monkeypatch: pytest.MonkeyPatch):
    """``DjangoMutation`` over ``Item``; ``Item.clean`` raises inside ``full_clean()``."""
    category_type, _item_type = _category_types()
    meta: dict[str, object] = {
        "model": product_models.Item,
        "operation": "create",
        "permission_classes": [_AllowAll],
    }
    name_input = "name"
    if shape == "rename":

        @strawberry.input
        class ItemTitle:
            name: str = strawberry.field(name="title")

        meta["input_class"] = ItemTitle
        name_input = "title"
    if shape == "unexposed":
        meta["fields"] = ("name", "category")
    create_item = type("CreateItem", (DjangoMutation,), {"Meta": type("Meta", (), meta)})

    def clean(self: product_models.Item) -> None:
        raise _django_error(raised)

    monkeypatch.setattr(product_models.Item, "clean", clean)
    return _execute(
        DjangoMutationField(create_item),
        lambda: f'{name_input}: "keyed", categoryId: "{_category_gid(category_type)}"',
    )


# --------------------------------------------------------------------------- forms


def _run_modelform(shape: str, raised: _Raised, monkeypatch: pytest.MonkeyPatch):
    """``DjangoModelFormMutation`` over an ``Item`` form whose ``clean()`` raises."""
    del monkeypatch
    category_type, _item_type = _category_types()

    class KeyedItemForm(forms.ModelForm[product_models.Item]):
        class Meta:
            model = product_models.Item
            fields = ("name", "category", "is_private")

        @override
        def clean(self) -> NoReturn:
            raise _django_error(raised)

    meta: dict[str, object] = {
        "form_class": KeyedItemForm,
        "operation": "create",
        "permission_classes": [_AllowAll],
    }
    if shape == "unexposed":
        meta["fields"] = ("name", "category")
    create_item = type(
        "CreateItemViaForm",
        (DjangoModelFormMutation,),
        {"Meta": type("Meta", (), meta)},
    )
    return _execute(
        DjangoMutationField(create_item),
        lambda: f'name: "keyed", categoryId: "{_category_gid(category_type)}"',
    )


def _run_plain_form(shape: str, raised: _Raised, monkeypatch: pytest.MonkeyPatch):
    """Plain ``DjangoFormMutation`` over a form whose ``clean()`` raises."""
    del monkeypatch
    category_type, _item_type = _category_types()

    class KeyedContactForm(forms.Form):
        full_name = forms.CharField()
        category = forms.ModelChoiceField(queryset=product_models.Category.objects.all())
        note = forms.CharField(required=False)

        @override
        def clean(self) -> NoReturn:
            raise _django_error(raised)

    meta: dict[str, object] = {"form_class": KeyedContactForm, "permission_classes": [_AllowAll]}
    if shape == "unexposed":
        meta["fields"] = ("full_name", "category")
    submit = type("SubmitKeyedContact", (DjangoFormMutation,), {"Meta": type("Meta", (), meta)})
    return _execute(
        DjangoMutationField(submit),
        lambda: f'fullName: "keyed", categoryId: "{_category_gid(category_type)}"',
    )


# --------------------------------------------------------------------------- serializer


def _serializer_mutation(serializer_class: type[DRFSerializer]) -> type[SerializerMutation]:
    return type(
        "WriteKeyedItem",
        (SerializerMutation,),
        {
            "Meta": type(
                "Meta",
                (),
                {
                    "serializer_class": serializer_class,
                    "operation": "create",
                    "permission_classes": [_AllowAll],
                },
            ),
        },
    )


def _run_serializer(*, save_time: bool):
    """A serializer runner raising from ``validate()`` or, ``save_time``, from ``create()``."""

    def run(shape: str, raised: _Raised, monkeypatch: pytest.MonkeyPatch):
        del shape, monkeypatch
        category_type, _item_type = _category_types()
        name, message = raised

        class KeyedItemSerializer(serializers.ModelSerializer[product_models.Item]):
            full_name = serializers.CharField(source="name")

            # basedpyright: DRF stubs declare ModelSerializer.Meta; the runtime class has none
            # to subclass
            class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
                model = product_models.Item
                fields = ("full_name", "category", "is_private")

            @override
            def validate(self, attrs: dict[str, object]) -> dict[str, object]:
                if not save_time:
                    raise serializers.ValidationError(
                        message if name is None else {name: [message]},
                    )
                return attrs

            @override
            def create(self, validated_data: dict[str, object]) -> product_models.Item:
                raise _django_error(raised)

        return _execute(
            DjangoMutationField(_serializer_mutation(KeyedItemSerializer)),
            lambda: f'fullName: "keyed", categoryId: "{_category_gid(category_type)}"',
        )

    return run


# --------------------------------------------------------------------------- register


def _run_register(shape: str, raised: _Raised, monkeypatch: pytest.MonkeyPatch):
    """``register_mutation()`` over a user model requiring ``first_name``; ``clean`` raises."""
    del shape

    class UserT(DjangoType, relay.Node):
        class Meta:
            model = User
            fields = ("id", "username")
            primary = True

    assert registry.get(User) is UserT
    monkeypatch.setattr(User, "REQUIRED_FIELDS", ["email", "first_name"])

    def clean(self: User) -> None:
        raise _django_error(raised)

    monkeypatch.setattr(User, "clean", clean)
    return _execute(
        register_mutation(permission_classes=[_AllowAll]),
        lambda: (
            'username: "keyed", email: "keyed@example.com", firstName: "Keyed", '
            'password: "S0me-long-pass-phrase-9"'
        ),
    )


_RUNNERS: dict[str, _Runner] = {
    "model": _run_model,
    "modelform": _run_modelform,
    "plain_form": _run_plain_form,
    "serializer": _run_serializer(save_time=False),
    "serializer_save": _run_serializer(save_time=True),
    "register": _run_register,
}

#: ``(flavor, shape, raised validator-side name, expected key)``; ``None`` name = non-field.
_CELLS: list[tuple[str, str, str | None, str]] = [
    (
        "model",
        "multi_word",
        "is_private",
        "isPrivate",
    ),
    (
        "model",
        "fk_suffix",
        "category",
        "categoryId",
    ),
    (
        "model",
        "fk_attname",
        "category_id",
        "categoryId",
    ),
    (
        "model",
        "rename",
        "name",
        "title",
    ),
    (
        "model",
        "unexposed",
        "is_private",
        "is_private",
    ),
    (
        "model",
        "non_field",
        None,
        NON_FIELD_ERROR_KEY,
    ),
    (
        "modelform",
        "multi_word",
        "is_private",
        "isPrivate",
    ),
    (
        "modelform",
        "fk_suffix",
        "category",
        "categoryId",
    ),
    (
        "modelform",
        "unexposed",
        "is_private",
        "is_private",
    ),
    (
        "modelform",
        "non_field",
        None,
        NON_FIELD_ERROR_KEY,
    ),
    (
        "plain_form",
        "multi_word",
        "full_name",
        "fullName",
    ),
    (
        "plain_form",
        "fk_suffix",
        "category",
        "categoryId",
    ),
    (
        "plain_form",
        "unexposed",
        "note",
        "note",
    ),
    (
        "plain_form",
        "non_field",
        None,
        NON_FIELD_ERROR_KEY,
    ),
    (
        "serializer",
        "multi_word",
        "is_private",
        "isPrivate",
    ),
    (
        "serializer",
        "fk_suffix",
        "category",
        "categoryId",
    ),
    (
        "serializer",
        "rename",
        "full_name",
        "fullName",
    ),
    (
        "serializer",
        "unexposed",
        "description",
        "description",
    ),
    (
        "serializer",
        "non_field",
        None,
        NON_FIELD_ERROR_KEY,
    ),
    (
        "serializer_save",
        "multi_word",
        "is_private",
        "isPrivate",
    ),
    (
        "serializer_save",
        "fk_suffix",
        "category",
        "categoryId",
    ),
    (
        "serializer_save",
        "fk_attname",
        "category_id",
        "categoryId",
    ),
    (
        "serializer_save",
        "rename",
        "name",
        "fullName",
    ),
    (
        "serializer_save",
        "unexposed",
        "description",
        "description",
    ),
    (
        "serializer_save",
        "non_field",
        None,
        NON_FIELD_ERROR_KEY,
    ),
    (
        "register",
        "multi_word",
        "first_name",
        "firstName",
    ),
    (
        "register",
        "unexposed",
        "last_name",
        "last_name",
    ),
    (
        "register",
        "non_field",
        None,
        NON_FIELD_ERROR_KEY,
    ),
]


@pytest.mark.django_db
@pytest.mark.parametrize(
    (
        "flavor",
        "shape",
        "raised_name",
        "expected",
    ),
    _CELLS,
    ids=[f"{flavor}-{shape}" for flavor, shape, _name, _expected in _CELLS],
)
def test_validator_error_keys_to_the_input_field_sent(
    flavor: str,
    shape: str,
    raised_name: str | None,
    expected: str,
    monkeypatch: pytest.MonkeyPatch,
):
    """The flavor's validator error comes back under the input name, one-segment ``path``."""
    errors = _RUNNERS[flavor](shape, (raised_name, "keyed failure"), monkeypatch)

    expected_path = [] if expected == NON_FIELD_ERROR_KEY else [expected]
    assert errors == [(expected, expected_path)]


@pytest.mark.django_db
def test_rename_onto_an_unexposed_model_name_shares_one_key(monkeypatch: pytest.MonkeyPatch):
    """A rename onto an unexposed field's model name makes two errors share one key.

    ``Meta.input_class`` exposes ``Item.name`` as ``category`` while the FK ``category``
    stays out of the input. An error on each comes back under ``category``: the renamed
    ``name`` because ``category`` is its input name, the FK because an unexposed field
    keeps its model field name. Both entries are kept; nothing refuses the shape.
    """
    _category_types()

    @strawberry.input
    class ItemNameAsCategory:
        name: str = strawberry.field(name="category")

    class CreateItem(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "create"
            input_class = ItemNameAsCategory
            fields = ("name", "description")
            permission_classes = [_AllowAll]

    def clean(self: product_models.Item) -> None:
        raise DjangoValidationError({"name": "on name"})

    monkeypatch.setattr(product_models.Item, "clean", clean)
    errors = _execute(
        DjangoMutationField(CreateItem),
        lambda: 'category: "keyed"',
    )
    # ``full_clean()`` still validates the unexposed FK (it shares
    # ``unique_item_per_category`` with the provided ``name``), so its null error
    # rides beside the renamed field's ``clean()`` error.
    assert errors == [("category", ["category"]), ("category", ["category"])]


@pytest.mark.django_db
def test_decode_error_keeps_its_input_name_under_a_swapped_rename(
    monkeypatch: pytest.MonkeyPatch,
):
    """A decode error already names the input field and never passes through the key map.

    ``Meta.input_class`` swaps ``name`` and ``description`` (``name`` is sent as
    ``description`` and vice versa). An explicit ``null`` on input ``description`` (model
    ``name``, ``null=False``) is a decode error keyed ``description``; re-keying it as if
    it were a model name would report ``name``, the other field. A ``full_clean()`` error
    on model ``name`` in the same shape keys to ``description`` through the map.
    """
    category_type, _item_type = _category_types()

    @strawberry.input
    class ItemSwap:
        name: str | None = strawberry.field(name="description", default=None)
        description: str | None = strawberry.field(name="name", default=None)

    class CreateItem(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "create"
            input_class = ItemSwap
            permission_classes = [_AllowAll]

    decoded = _execute(
        DjangoMutationField(CreateItem),
        lambda: f'description: null, categoryId: "{_category_gid(category_type)}"',
    )
    assert decoded == [("description", ["description"])]

    registry.clear()
    category_type, _item_type = _category_types()

    @strawberry.input
    class ItemSwapAgain:
        name: str | None = strawberry.field(name="description", default=None)
        description: str | None = strawberry.field(name="name", default=None)

    class CreateItemAgain(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "create"
            input_class = ItemSwapAgain
            permission_classes = [_AllowAll]

    def clean(self: product_models.Item) -> None:
        raise DjangoValidationError({"name": "on name"})

    monkeypatch.setattr(product_models.Item, "clean", clean)
    validated = _execute(
        DjangoMutationField(CreateItemAgain),
        lambda: (
            f'description: "keyed", name: "sent", categoryId: "{_category_gid(category_type)}"'
        ),
    )
    assert validated == [("description", ["description"])]


@pytest.mark.django_db
def test_constraint_listing_a_forward_key_column_keys_to_its_input(
    monkeypatch: pytest.MonkeyPatch,
):
    """A constraint naming a forward key by its column (``category_id``) reports ``categoryId``.

    ``Model.validate_constraints()`` keys a single-field unique error by the name the
    constraint lists, so a ``UniqueConstraint(fields=["category_id"])`` duplicate arrives
    under ``category_id``; the model key map answers that column name as well as
    ``category``.
    """
    category_type, _item_type = _category_types()
    category, _created = product_models.Category.objects.get_or_create(name="Keyed category")
    product_models.Item.objects.create(name="first", category=category)
    constraint = UniqueConstraint(fields=["category_id"], name="one_item_per_keyed_category")

    # ``get_constraints`` is the seam ``validate_constraints`` reads; patching it leaves
    # ``Options``' cached constraint views (``total_unique_constraints``) untouched.
    def get_constraints(self: product_models.Item) -> list[tuple[type[Model], list[object]]]:
        return [(product_models.Item, [constraint])]

    monkeypatch.setattr(product_models.Item, "get_constraints", get_constraints)

    class CreateItem(DjangoMutation):
        class Meta:
            model = product_models.Item
            operation = "create"
            permission_classes = [_AllowAll]

    errors = _execute(
        DjangoMutationField(CreateItem),
        lambda: f'name: "second", categoryId: "{_category_gid(category_type)}"',
    )
    assert errors == [("categoryId", ["categoryId"])]
