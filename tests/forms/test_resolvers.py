"""Form-mutation resolver-pipeline tests (spec-038 Slice 3).

System-under-test is ``forms/resolvers.py`` - the sync + async form pipeline
(decode -> locate -> authorize -> construct + validate -> write -> re-fetch ->
payload) driven through a finalized package-test ``@strawberry.type Mutation``
(the live ``/graphql/`` surface is Slice 4). Fixtures:

- the products ``Item`` / ``Category`` (FK + ``unique_item_per_category``) cover
  the FK relation decode, the partial-update reconstruction, the ``"__all__"``
  constraint sentinel, the visibility-scoped locate, and the re-fetch G2 plan;
- the library ``Book`` / ``Genre`` / ``Shelf`` (a real M2M + a ``choices`` field)
  cover the M2M relation decode + the choice-enum unwrap;
- the scalars ``MediaSpecimen`` (``FileField`` / ``ImageField``) covers the
  ``files=`` decode split;
- package-local plain ``forms.Form`` fixtures cover the model-less ``{ ok errors }``
  payload + ``perform_mutate``, the kwarg-requiring-form ``get_form_kwargs`` hook,
  and the ``to_field_name`` relation contract.

The relation-visibility tests drive BOTH a Relay-``GlobalID`` primary AND a
non-Relay raw-pk primary, single AND multi, to pin the visibility-on-every-branch
contract that closes the raw-pk gap ``036``'s ``_decode_relation_id_set`` leaves.
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
from django import forms
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from strawberry import relay

from django_strawberry_framework import (
    DjangoFormMutation,
    DjangoModelFormMutation,
    DjangoMutationField,
    DjangoOptimizerExtension,
    DjangoType,
    finalize_django_types,
)
from django_strawberry_framework.forms import resolvers as form_resolvers
from django_strawberry_framework.mutations.inputs import NON_FIELD_ERROR_KEY
from django_strawberry_framework.registry import registry
from django_strawberry_framework.testing.relay import global_id_for
from django_strawberry_framework.utils.querysets import SyncMisuseError


@pytest.fixture(autouse=True)
def _isolate_registry():
    """Reset the registry (co-clears the form + mutation ledgers) per test."""
    registry.clear()
    yield
    registry.clear()


_name_counter = itertools.count(1)


def _uniq(prefix: str) -> str:
    return f"{prefix}-{next(_name_counter)}"


class _AllowAll:
    """A permission class that authorizes every write (isolates the pipeline from auth)."""

    def has_permission(
        self,
        info,
        mutation,
        operation,
        data,
        instance=None,
    ):
        return True


class _DenyAll:
    """A permission class that denies every write (drives the write-auth denial)."""

    def has_permission(
        self,
        info,
        mutation,
        operation,
        data,
        instance=None,
    ):
        return False


@strawberry.type
class _Query:
    @strawberry.field
    def ping(self) -> int:
        return 1


def _schema(mutation_type: type) -> strawberry.Schema:
    return strawberry.Schema(
        query=_Query,
        mutation=mutation_type,
        extensions=[DjangoOptimizerExtension],
    )


# ---------------------------------------------------------------------------
# Products Item/Category ModelForm fixtures (FK + unique_item_per_category)
# ---------------------------------------------------------------------------


def _item_model_form():
    class ItemModelForm(forms.ModelForm):
        class Meta:
            model = product_models.Item
            fields = ("name", "category", "is_private")

    return ItemModelForm


def _build_item_form_schema(
    *,
    category_get_queryset=None,
    item_get_queryset=None,
    permission_classes=None,
):
    """Declare Item/Category Relay primaries + a create/update ModelForm mutation."""
    perms = permission_classes if permission_classes is not None else [_AllowAll]

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

    form_cls = _item_model_form()
    # Build via ``type(...)`` so the ``Meta`` body can carry the parameterized
    # ``permission_classes`` (a nested ``class Meta:`` body cannot read the
    # enclosing function's parameter name).
    create_meta = {"form_class": form_cls, "operation": "create", "permission_classes": perms}
    update_meta = {"form_class": form_cls, "operation": "update", "permission_classes": perms}
    CreateItem = type(
        "CreateItem",
        (DjangoModelFormMutation,),
        {"Meta": type("Meta", (), create_meta)},
    )
    UpdateItem = type(
        "UpdateItem",
        (DjangoModelFormMutation,),
        {"Meta": type("Meta", (), update_meta)},
    )

    @strawberry.type
    class Mutation:
        create_item = DjangoMutationField(CreateItem)
        update_item = DjangoMutationField(UpdateItem)

    finalize_django_types()
    return _schema(Mutation), (
        CategoryT,
        ItemT,
        CreateItem,
        UpdateItem,
    )


_CREATE = (
    "mutation($d: ItemModelFormInput!){ createItem(data:$d){ "
    "node{ id name category{ name } } errors{ field messages } } }"
)
_UPDATE = (
    "mutation($id: ID!, $d: ItemModelFormPartialInput!){ updateItem(id:$id, data:$d){ "
    "node{ name category{ name } } errors{ field messages } } }"
)


# ---------------------------------------------------------------------------
# create / update happy paths
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_modelform_create_writes_and_returns_node():
    """A ModelForm create writes the row + returns the node with its FK relation."""
    (
        schema,
        (
            CategoryT,
            _ItemT,
            _C,
            _U,
        ),
    ) = _build_item_form_schema()
    cat = product_models.Category.objects.create(name=_uniq("Cat"))
    res = schema.execute_sync(
        _CREATE,
        variable_values={"d": {"name": "Made", "categoryId": global_id_for(CategoryT, cat.pk)}},
    )
    assert res.errors is None, res.errors
    payload = res.data["createItem"]
    assert payload["node"]["name"] == "Made"
    assert payload["node"]["category"]["name"] == cat.name
    assert payload["errors"] == []
    assert product_models.Item.objects.filter(name="Made", category=cat).count() == 1


@pytest.mark.django_db
def test_modelform_update_locates_writes_and_returns():
    """A ModelForm update locates the row, writes the change, returns it."""
    (
        schema,
        (
            _CategoryT,
            ItemT,
            _C,
            _U,
        ),
    ) = _build_item_form_schema()
    cat = product_models.Category.objects.create(name=_uniq("Cat"))
    item = product_models.Item.objects.create(name="Before", category=cat)
    res = schema.execute_sync(
        _UPDATE,
        variable_values={"id": global_id_for(ItemT, item.pk), "d": {"name": "After"}},
    )
    assert res.errors is None, res.errors
    assert res.data["updateItem"]["node"]["name"] == "After"
    item.refresh_from_db()
    assert item.name == "After"


# ---------------------------------------------------------------------------
# form.errors -> envelope (incl. NON_FIELD_ERRORS -> "__all__")
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_clean_field_failure_maps_to_field_keyed_error():
    """A ``clean_<field>`` failure surfaces as a field-keyed ``FieldError`` (null node)."""

    class PickyForm(forms.ModelForm):
        class Meta:
            model = product_models.Item
            fields = ("name", "category")

        def clean_name(self):
            value = self.cleaned_data["name"]
            if value == "bad":
                raise forms.ValidationError("name may not be 'bad'.")
            return value

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

    class CreateItem(DjangoModelFormMutation):
        class Meta:
            form_class = PickyForm
            operation = "create"
            permission_classes = [_AllowAll]

    @strawberry.type
    class Mutation:
        create_item = DjangoMutationField(CreateItem)

    finalize_django_types()
    schema = _schema(Mutation)
    cat = product_models.Category.objects.create(name=_uniq("Cat"))
    res = schema.execute_sync(
        "mutation($d: PickyFormInput!){ createItem(data:$d){ node{ name } errors{ field messages } } }",
        variable_values={"d": {"name": "bad", "categoryId": global_id_for(CategoryT, cat.pk)}},
    )
    assert res.errors is None, res.errors
    payload = res.data["createItem"]
    assert payload["node"] is None
    assert [e["field"] for e in payload["errors"]] == ["name"]


@pytest.mark.django_db
def test_non_field_constraint_failure_keys_to_all_sentinel():
    """A ``unique_item_per_category`` (model-wide) failure keys to the ``"__all__"`` sentinel.

    The reused ``validation_error_to_field_errors(ValidationError(form.errors.as_data()))``
    keys the form's ``NON_FIELD_ERRORS`` bucket to ``"__all__"`` byte-identically to
    a model ``full_clean()`` failure.
    """
    (
        schema,
        (
            CategoryT,
            _ItemT,
            _C,
            _U,
        ),
    ) = _build_item_form_schema()
    cat = product_models.Category.objects.create(name=_uniq("Cat"))
    product_models.Item.objects.create(name="Dup", category=cat)
    res = schema.execute_sync(
        _CREATE,
        variable_values={"d": {"name": "Dup", "categoryId": global_id_for(CategoryT, cat.pk)}},
    )
    assert res.errors is None, res.errors
    payload = res.data["createItem"]
    assert payload["node"] is None
    assert NON_FIELD_ERROR_KEY in [e["field"] for e in payload["errors"]]


# ---------------------------------------------------------------------------
# decode split: data= / files= / to_field_name (unit tier)
# ---------------------------------------------------------------------------


def _relay_global_id(type_cls: type, pk: object) -> relay.GlobalID:
    """Build a ``relay.GlobalID`` object (the coerced shape Strawberry hands the resolver).

    The unit-tier decode is called below ``Strawberry``'s argument coercion, so the
    relation value must be a ``relay.GlobalID`` instance (a plain base64 string
    takes the raw-pk branch). Reconstructs the exact GlobalID object from the wire
    string ``global_id_for`` mints (``from_id`` parses the type's actual encoding
    strategy), so the ``type_name`` / ``node_id`` slots match what live emission
    produces.
    """
    return relay.GlobalID.from_id(global_id_for(type_cls, pk))


@pytest.mark.django_db
def test_decode_split_relation_lands_under_form_key_not_id_attr():
    """``categoryId`` decodes to ``{"category": pk}`` in ``provided_data`` (the P1 form-key contract)."""
    (
        _schema,
        (
            CategoryT,
            _ItemT,
            CreateItem,
            _U,
        ),
    ) = _build_item_form_schema()
    cat = product_models.Category.objects.create(name=_uniq("Cat"))
    data = CreateItem._input_class(name="X", category_id=_relay_global_id(CategoryT, cat.pk))
    info = SimpleNamespace(context=SimpleNamespace())
    provided_data, provided_files, error = form_resolvers._decode_form_data(CreateItem, data, info)
    assert error is None
    # The form key is "category" (the form field name), NOT "category_id".
    assert provided_data["category"] == cat.pk
    assert "category_id" not in provided_data
    assert provided_files == {}


@pytest.mark.django_db
def test_decode_split_upload_lands_in_files_never_data():
    """An ``Upload`` field lands in ``provided_files``, never ``provided_data``."""

    class MediaForm(forms.ModelForm):
        class Meta:
            model = scalars_models.MediaSpecimen
            fields = ("label", "attachment", "image")

    class MediaT(DjangoType):
        class Meta:
            model = scalars_models.MediaSpecimen
            fields = ("id", "label")
            primary = True

    class CreateMedia(DjangoModelFormMutation):
        class Meta:
            form_class = MediaForm
            operation = "create"
            permission_classes = [_AllowAll]

    @strawberry.type
    class Mutation:
        create_media = DjangoMutationField(CreateMedia)

    finalize_django_types()
    _schema(Mutation)
    upload = SimpleUploadedFile("a.txt", b"hello")
    image = SimpleUploadedFile("a.png", b"\x89PNG\r\n")
    data = CreateMedia._input_class(label="L", attachment=upload, image=image)
    info = SimpleNamespace(context=SimpleNamespace())
    provided_data, provided_files, error = form_resolvers._decode_form_data(
        CreateMedia,
        data,
        info,
    )
    assert error is None
    assert set(provided_files) == {"attachment", "image"}
    assert "attachment" not in provided_data
    assert "image" not in provided_data
    assert provided_data == {"label": "L"}


@pytest.mark.django_db
def test_decode_unwraps_choice_enum_to_raw_value():
    """A scalar choice-enum member is unwrapped to its raw Django value in ``provided_data``."""

    class BookForm(forms.ModelForm):
        class Meta:
            model = library_models.Book
            fields = ("title", "circulation_status", "shelf")

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

    class CreateBook(DjangoModelFormMutation):
        class Meta:
            form_class = BookForm
            operation = "create"
            permission_classes = [_AllowAll]

    @strawberry.type
    class Mutation:
        create_book = DjangoMutationField(CreateBook)

    finalize_django_types()
    _schema(Mutation)
    input_cls = CreateBook._input_class
    # The circulation_status field resolves to a generated enum; grab the member.
    status_attr = next(
        f.python_name
        for f in input_cls.__strawberry_definition__.fields
        if f.python_name.startswith("circulation")
    )
    enum_def = next(
        f.type for f in input_cls.__strawberry_definition__.fields if f.python_name == status_attr
    )
    # Strawberry wraps a choice enum in a ``StrawberryEnumDefinition``; the python
    # enum is ``.wrapped_cls``. Resolve the member whose value is "available".
    enum_cls = enum_def.wrapped_cls
    member = next(m for m in enum_cls if m.value == "available")
    data = input_cls(**{status_attr: member, "title": "T", "shelf_id": strawberry.UNSET})
    info = SimpleNamespace(context=SimpleNamespace())
    provided_data, _files, error = form_resolvers._decode_form_data(CreateBook, data, info)
    assert error is None
    assert provided_data["circulation_status"] == "available"


# ---------------------------------------------------------------------------
# relation visibility on EVERY branch (Relay x raw-pk, single x multi) - P1
# ---------------------------------------------------------------------------


def _build_relay_category_create_schema(category_get_queryset):
    """A ModelForm create over Item with a Relay-Node Category primary + a visibility hook."""
    (
        schema,
        (
            CategoryT,
            _ItemT,
            _C,
            _U,
        ),
    ) = _build_item_form_schema(
        category_get_queryset=category_get_queryset,
    )
    return schema, CategoryT


@pytest.mark.django_db
def test_relation_visibility_relay_single_hidden_rejected():
    """A hidden Relay-``GlobalID`` FK target -> field-keyed error BEFORE the form."""

    @classmethod
    def hide_all(cls, qs, info):
        return qs.none()

    schema, CategoryT = _build_relay_category_create_schema(hide_all)
    cat = product_models.Category.objects.create(name=_uniq("Cat"))
    res = schema.execute_sync(
        _CREATE,
        variable_values={"d": {"name": "X", "categoryId": global_id_for(CategoryT, cat.pk)}},
    )
    assert res.errors is None, res.errors
    payload = res.data["createItem"]
    assert payload["node"] is None
    assert [e["field"] for e in payload["errors"]] == ["categoryId"]


@pytest.mark.django_db
def test_relation_visibility_raw_pk_single_hidden_rejected():
    """A hidden NON-RELAY raw-pk FK target -> field-keyed error (the raw-pk gap, P1).

    The related primary is NOT Relay-Node-shaped, so the relation id is a raw pk;
    the form decoder must STILL visibility-check it (the gap ``036``'s
    ``_decode_relation_id_set`` leaves on the raw-pk branch).
    """

    @classmethod
    def hide_all(cls, qs, info):
        return qs.none()

    # Category primary is plain (no relay.Node) -> raw-pk relation id.
    CategoryT = type(
        "CategoryT",
        (DjangoType,),
        {
            "Meta": type(
                "Meta",
                (),
                {"model": product_models.Category, "fields": ("id", "name"), "primary": True},
            ),
            "get_queryset": hide_all,
        },
    )

    class ItemT(DjangoType, relay.Node):
        class Meta:
            model = product_models.Item
            fields = ("id", "name")
            primary = True

    form_cls = _item_model_form()

    class CreateItem(DjangoModelFormMutation):
        class Meta:
            form_class = form_cls
            operation = "create"
            permission_classes = [_AllowAll]

    @strawberry.type
    class Mutation:
        create_item = DjangoMutationField(CreateItem)

    finalize_django_types()
    schema = _schema(Mutation)
    cat = product_models.Category.objects.create(name=_uniq("Cat"))
    del CategoryT  # the raw pk is the wire value for a non-relay primary
    res = schema.execute_sync(
        "mutation($d: ItemModelFormInput!){ createItem(data:$d){ node{ name } errors{ field } } }",
        variable_values={"d": {"name": "X", "categoryId": cat.pk}},
    )
    assert res.errors is None, res.errors
    payload = res.data["createItem"]
    assert payload["node"] is None
    assert [e["field"] for e in payload["errors"]] == ["categoryId"]


def _build_book_m2m_schema(*, genre_relay: bool, genre_get_queryset=None):
    """A ModelForm create over Book with a genres M2M; the Genre primary is Relay or plain."""

    class BookForm(forms.ModelForm):
        class Meta:
            model = library_models.Book
            fields = ("title", "shelf", "genres")

    genre_bases = (DjangoType, relay.Node) if genre_relay else (DjangoType,)
    genre_body: dict = {
        "Meta": type(
            "Meta",
            (),
            {"model": library_models.Genre, "fields": ("id", "name"), "primary": True},
        ),
    }
    if genre_get_queryset is not None:
        genre_body["get_queryset"] = genre_get_queryset
    GenreT = type("GenreT", genre_bases, genre_body)

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

    class CreateBook(DjangoModelFormMutation):
        class Meta:
            form_class = BookForm
            operation = "create"
            permission_classes = [_AllowAll]

    @strawberry.type
    class Mutation:
        create_book = DjangoMutationField(CreateBook)

    finalize_django_types()
    return _schema(Mutation), (GenreT, ShelfT, BookT)


@pytest.mark.django_db
def test_relation_visibility_relay_multi_hidden_rejected():
    """A hidden Relay-``GlobalID`` M2M member -> field-keyed error (multi branch, P1)."""

    @classmethod
    def hide_all(cls, qs, info):
        return qs.none()

    schema, (GenreT, ShelfT, _BookT) = _build_book_m2m_schema(
        genre_relay=True,
        genre_get_queryset=hide_all,
    )
    branch = library_models.Branch.objects.create(name=_uniq("Br"))
    shelf = library_models.Shelf.objects.create(code=_uniq("Sh"), branch=branch)
    genre = library_models.Genre.objects.create(name=_uniq("G"))
    res = schema.execute_sync(
        "mutation($d: BookFormInput!){ createBook(data:$d){ node{ title } errors{ field } } }",
        variable_values={
            "d": {
                "title": "B",
                "shelfId": global_id_for(ShelfT, shelf.pk),
                "genres": [global_id_for(GenreT, genre.pk)],
            },
        },
    )
    assert res.errors is None, res.errors
    payload = res.data["createBook"]
    assert payload["node"] is None
    assert [e["field"] for e in payload["errors"]] == ["genres"]


@pytest.mark.django_db
def test_relation_visibility_raw_pk_multi_hidden_rejected():
    """A hidden NON-RELAY raw-pk M2M member -> field-keyed error (multi raw-pk gap, P1)."""

    @classmethod
    def hide_all(cls, qs, info):
        return qs.none()

    schema, (_GenreT, ShelfT, _BookT) = _build_book_m2m_schema(
        genre_relay=False,
        genre_get_queryset=hide_all,
    )
    branch = library_models.Branch.objects.create(name=_uniq("Br"))
    shelf = library_models.Shelf.objects.create(code=_uniq("Sh"), branch=branch)
    genre = library_models.Genre.objects.create(name=_uniq("G"))
    res = schema.execute_sync(
        "mutation($d: BookFormInput!){ createBook(data:$d){ node{ title } errors{ field } } }",
        variable_values={
            "d": {"title": "B", "shelfId": global_id_for(ShelfT, shelf.pk), "genres": [genre.pk]},
        },
    )
    assert res.errors is None, res.errors
    payload = res.data["createBook"]
    assert payload["node"] is None
    assert [e["field"] for e in payload["errors"]] == ["genres"]


@pytest.mark.django_db
def test_wrong_model_relation_id_yields_field_error():
    """A well-formed ``GlobalID`` for the WRONG model -> field-keyed error (AR-H4)."""
    (
        schema,
        (
            _CategoryT,
            ItemT,
            _C,
            _U,
        ),
    ) = _build_item_form_schema()
    cat = product_models.Category.objects.create(name=_uniq("Cat"))
    item = product_models.Item.objects.create(name="X", category=cat)
    wrong = global_id_for(ItemT, item.pk)  # an Item id passed to categoryId
    res = schema.execute_sync(
        _CREATE,
        variable_values={"d": {"name": "New", "categoryId": wrong}},
    )
    assert res.errors is None, res.errors
    payload = res.data["createItem"]
    assert payload["node"] is None
    assert [e["field"] for e in payload["errors"]] == ["categoryId"]


# ---------------------------------------------------------------------------
# to_field_name (P2 #6)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_to_field_name_relation_validates_by_target_field():
    """A ``ModelChoiceField`` with ``to_field_name`` validates the decoded value by that field.

    A valid Relay-``GlobalID`` is decoded to ``obj.serializable_value(to_field_name)``
    (here ``Genre.name``), so the bound form's ``to_python`` resolves it and the
    create succeeds.
    """

    class GenreT(DjangoType, relay.Node):
        class Meta:
            model = library_models.Genre
            fields = ("id", "name")
            primary = True

    class GenrePickForm(forms.Form):
        genre = forms.ModelChoiceField(
            queryset=library_models.Genre.objects.all(),
            to_field_name="name",
        )

    captured = {}

    class PickGenre(DjangoFormMutation):
        class Meta:
            form_class = GenrePickForm
            permission_classes = []

        def perform_mutate(self, form, info):
            captured["genre"] = form.cleaned_data["genre"]

    @strawberry.type
    class Mutation:
        pick = DjangoMutationField(PickGenre)

    finalize_django_types()
    schema = _schema(Mutation)
    genre = library_models.Genre.objects.create(name=_uniq("Genre"))
    res = schema.execute_sync(
        "mutation($d: GenrePickFormInput!){ pick(data:$d){ ok errors{ field messages } } }",
        variable_values={"d": {"genreId": global_id_for(GenreT, genre.pk)}},
    )
    assert res.errors is None, res.errors
    assert res.data["pick"]["ok"] is True
    assert captured["genre"] == genre


# ---------------------------------------------------------------------------
# write-time IntegrityError (P1)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_modelform_save_integrity_error_maps_to_envelope():
    """A ``form.save()`` ``IntegrityError`` race maps to the envelope, not a top-level error (P1)."""
    (
        schema,
        (
            CategoryT,
            _ItemT,
            _C,
            _U,
        ),
    ) = _build_item_form_schema()
    cat = product_models.Category.objects.create(name=_uniq("Cat"))
    with mock.patch.object(
        forms.ModelForm,
        "save",
        side_effect=IntegrityError("race"),
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
def test_plain_form_perform_mutate_integrity_error_maps_to_envelope():
    """A plain-form ``perform_mutate`` ``IntegrityError`` maps to ``{ ok: false }`` (P1)."""

    class ContactForm(forms.Form):
        message = forms.CharField()

    class Submit(DjangoFormMutation):
        class Meta:
            form_class = ContactForm
            permission_classes = []

        def perform_mutate(self, form, info):
            raise IntegrityError("race")

    @strawberry.type
    class Mutation:
        submit = DjangoMutationField(Submit)

    finalize_django_types()
    schema = _schema(Mutation)
    res = schema.execute_sync(
        "mutation($d: ContactFormInput!){ submit(data:$d){ ok errors{ field } } }",
        variable_values={"d": {"message": "hi"}},
    )
    assert res.errors is None, res.errors
    payload = res.data["submit"]
    assert payload["ok"] is False
    assert payload["errors"][0]["field"] == NON_FIELD_ERROR_KEY


# ---------------------------------------------------------------------------
# get_form_kwargs / get_form hooks (P2)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_get_form_kwargs_override_injects_constructor_kwarg():
    """An override injecting ``user=`` drives a form whose ``__init__`` requires it."""

    class KwargForm(forms.Form):
        note = forms.CharField()

        def __init__(self, *args, user=None, **kwargs):
            super().__init__(*args, **kwargs)
            self._user = user

        def clean(self):
            if self._user is None:
                raise forms.ValidationError("user is required.")
            return self.cleaned_data

    captured = {}

    class Submit(DjangoFormMutation):
        class Meta:
            form_class = KwargForm
            permission_classes = []

        def get_form_kwargs(
            self,
            info,
            *,
            data,
            files,
            instance=None,
        ):
            kwargs = {"data": data, "files": files, "user": "alice"}
            if instance is not None:
                kwargs["instance"] = instance
            return kwargs

        def perform_mutate(self, form, info):
            captured["user"] = form._user

    @strawberry.type
    class Mutation:
        submit = DjangoMutationField(Submit)

    finalize_django_types()
    schema = _schema(Mutation)
    res = schema.execute_sync(
        "mutation($d: KwargFormInput!){ submit(data:$d){ ok errors{ field messages } } }",
        variable_values={"d": {"note": "x"}},
    )
    assert res.errors is None, res.errors
    assert res.data["submit"]["ok"] is True
    assert captured["user"] == "alice"


@pytest.mark.django_db
def test_get_form_kwargs_override_waives_create_required_guard():
    """Overriding ``get_form_kwargs`` waives the create-required-narrowing guard.

    A ``Meta.fields`` narrowing dropping a still-required form field would normally
    raise at bind; the override is trusted to inject it, so the bind succeeds.
    """

    class TwoFieldForm(forms.Form):
        keep = forms.CharField()
        injected = forms.CharField()  # required, but dropped by Meta.fields

    class Submit(DjangoFormMutation):
        class Meta:
            form_class = TwoFieldForm
            fields = ("keep",)
            permission_classes = []

        def get_form_kwargs(
            self,
            info,
            *,
            data,
            files,
            instance=None,
        ):
            merged = dict(data)
            merged["injected"] = "supplied"
            return {"data": merged, "files": files}

    @strawberry.type
    class Mutation:
        submit = DjangoMutationField(Submit)

    # Must NOT raise at finalize (the guard is waived).
    finalize_django_types()
    schema = _schema(Mutation)
    res = schema.execute_sync(
        "mutation($d: TwoFieldFormKeepInput!){ submit(data:$d){ ok errors{ field } } }",
        variable_values={"d": {"keep": "k"}},
    )
    assert res.errors is None, res.errors
    assert res.data["submit"]["ok"] is True


# ---------------------------------------------------------------------------
# partial-update reconstruction (P1)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_partial_update_preserves_unprovided_fk_and_validates_constraint():
    """A one-field name change keeps the unprovided FK + validates ``unique_item_per_category``.

    The unchanged ``category`` comes from ``model_to_dict`` (the reconstruction), so
    ``unique_item_per_category`` is evaluated against the stored category - a rename
    to an existing ``(category, name)`` pair is rejected on the ``"__all__"`` key.
    """
    (
        schema,
        (
            _CategoryT,
            ItemT,
            _C,
            _U,
        ),
    ) = _build_item_form_schema()
    cat = product_models.Category.objects.create(name=_uniq("Cat"))
    product_models.Item.objects.create(name="Taken", category=cat)
    item = product_models.Item.objects.create(name="Mine", category=cat)
    res = schema.execute_sync(
        _UPDATE,
        variable_values={"id": global_id_for(ItemT, item.pk), "d": {"name": "Taken"}},
    )
    assert res.errors is None, res.errors
    payload = res.data["updateItem"]
    assert payload["node"] is None
    assert NON_FIELD_ERROR_KEY in [e["field"] for e in payload["errors"]]
    item.refresh_from_db()
    assert item.name == "Mine"  # not written


@pytest.mark.django_db
def test_partial_update_preserves_unprovided_m2m():
    """An omitted M2M is preserved from the located instance (reconstruction via ``model_to_dict``)."""

    class BookForm(forms.ModelForm):
        class Meta:
            model = library_models.Book
            fields = ("title", "shelf", "genres")

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

    class UpdateBook(DjangoModelFormMutation):
        class Meta:
            form_class = BookForm
            operation = "update"
            permission_classes = [_AllowAll]

    @strawberry.type
    class Mutation:
        update_book = DjangoMutationField(UpdateBook)

    finalize_django_types()
    schema = _schema(Mutation)
    branch = library_models.Branch.objects.create(name=_uniq("Br"))
    shelf = library_models.Shelf.objects.create(code=_uniq("Sh"), branch=branch)
    genre = library_models.Genre.objects.create(name=_uniq("G"))
    book = library_models.Book.objects.create(title="Orig", shelf=shelf)
    book.genres.add(genre)
    res = schema.execute_sync(
        "mutation($id: ID!, $d: BookFormPartialInput!){ updateBook(id:$id, data:$d){ "
        "node{ title } errors{ field messages } } }",
        variable_values={"id": global_id_for(BookT, book.pk), "d": {"title": "Renamed"}},
    )
    assert res.errors is None, res.errors
    assert res.data["updateBook"]["node"]["title"] == "Renamed"
    book.refresh_from_db()
    assert list(book.genres.values_list("pk", flat=True)) == [genre.pk]  # preserved


@pytest.mark.django_db
def test_required_extra_field_omitted_on_update_raises_field_error():
    """A required non-model extra field omitted on update -> a required ``FieldError`` (P2).

    The Slice-1 partial input keeps a required non-model extra field required, so
    an omitted one is absent from ``provided_data`` and the bound form fails its
    required validation.
    """

    class ConfirmForm(forms.ModelForm):
        confirm = forms.CharField()  # required non-model extra field

        class Meta:
            model = product_models.Item
            fields = ("name", "category")

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

    class UpdateItem(DjangoModelFormMutation):
        class Meta:
            form_class = ConfirmForm
            operation = "update"
            permission_classes = [_AllowAll]

    @strawberry.type
    class Mutation:
        update_item = DjangoMutationField(UpdateItem)

    finalize_django_types()
    schema = _schema(Mutation)
    cat = product_models.Category.objects.create(name=_uniq("Cat"))
    item = product_models.Item.objects.create(name="X", category=cat)
    res = schema.execute_sync(
        "mutation($id: ID!, $d: ConfirmFormPartialInput!){ updateItem(id:$id, data:$d){ "
        "node{ name } errors{ field messages } } }",
        variable_values={"id": global_id_for(ItemT, item.pk), "d": {"name": "Y"}},
    )
    assert res.errors is None, res.errors
    payload = res.data["updateItem"]
    assert payload["node"] is None
    assert "confirm" in [e["field"] for e in payload["errors"]]


# ---------------------------------------------------------------------------
# plain-form ok + errors payload + perform_mutate default / override
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_plain_form_valid_returns_ok_true():
    """A valid plain-form submit returns ``{ ok: true, errors: [] }``."""

    class ContactForm(forms.Form):
        message = forms.CharField()

    class Submit(DjangoFormMutation):
        class Meta:
            form_class = ContactForm
            permission_classes = []

    @strawberry.type
    class Mutation:
        submit = DjangoMutationField(Submit)

    finalize_django_types()
    schema = _schema(Mutation)
    res = schema.execute_sync(
        "mutation($d: ContactFormInput!){ submit(data:$d){ ok errors{ field } } }",
        variable_values={"d": {"message": "hi"}},
    )
    assert res.errors is None, res.errors
    assert res.data["submit"] == {"ok": True, "errors": []}


@pytest.mark.django_db
def test_plain_form_invalid_returns_ok_false_with_errors():
    """An invalid plain-form submit returns ``{ ok: false, errors: [...] }``."""

    class PickyContactForm(forms.Form):
        message = forms.CharField()

        def clean_message(self):
            raise forms.ValidationError("nope")

    class Submit(DjangoFormMutation):
        class Meta:
            form_class = PickyContactForm
            permission_classes = []

    @strawberry.type
    class Mutation:
        submit = DjangoMutationField(Submit)

    finalize_django_types()
    schema = _schema(Mutation)
    res = schema.execute_sync(
        "mutation($d: PickyContactFormInput!){ submit(data:$d){ ok errors{ field messages } } }",
        variable_values={"d": {"message": "x"}},
    )
    assert res.errors is None, res.errors
    payload = res.data["submit"]
    assert payload["ok"] is False
    assert [e["field"] for e in payload["errors"]] == ["message"]


@pytest.mark.django_db
def test_perform_mutate_override_runs_only_on_success():
    """The ``perform_mutate`` override runs on a valid submit, NOT on a failing one."""
    calls = []

    class ContactForm(forms.Form):
        message = forms.CharField()

        def clean_message(self):
            value = self.cleaned_data["message"]
            if value == "fail":
                raise forms.ValidationError("nope")
            return value

    class Submit(DjangoFormMutation):
        class Meta:
            form_class = ContactForm
            permission_classes = []

        def perform_mutate(self, form, info):
            calls.append(form.cleaned_data["message"])

    @strawberry.type
    class Mutation:
        submit = DjangoMutationField(Submit)

    finalize_django_types()
    schema = _schema(Mutation)
    q = "mutation($d: ContactFormInput!){ submit(data:$d){ ok errors{ field } } }"
    ok_res = schema.execute_sync(q, variable_values={"d": {"message": "go"}})
    assert ok_res.data["submit"]["ok"] is True
    fail_res = schema.execute_sync(q, variable_values={"d": {"message": "fail"}})
    assert fail_res.data["submit"]["ok"] is False
    assert calls == ["go"]  # the override ran only on the successful path


# ---------------------------------------------------------------------------
# visibility-scoped update locate (P1)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_update_hidden_row_is_not_found_no_existence_leak():
    """A caller who cannot SEE the row gets a not-found ``FieldError`` on ``id`` (no leak)."""

    @classmethod
    def hide_private(cls, qs, info):
        return qs.filter(is_private=False)

    (
        schema,
        (
            _CategoryT,
            ItemT,
            _C,
            _U,
        ),
    ) = _build_item_form_schema(item_get_queryset=hide_private)
    cat = product_models.Category.objects.create(name=_uniq("Cat"))
    hidden = product_models.Item.objects.create(name="Secret", category=cat, is_private=True)
    res = schema.execute_sync(
        _UPDATE,
        variable_values={"id": global_id_for(ItemT, hidden.pk), "d": {"name": "Y"}},
    )
    assert res.errors is None, res.errors
    payload = res.data["updateItem"]
    assert payload["node"] is None
    assert [e["field"] for e in payload["errors"]] == ["id"]


@pytest.mark.django_db
def test_update_malformed_id_is_field_error_before_lookup():
    """A malformed / wrong-model ``id:`` -> ``id``-keyed ``FieldError`` before any lookup."""
    (
        schema,
        (
            _CategoryT,
            _ItemT,
            _C,
            _U,
        ),
    ) = _build_item_form_schema()
    res = schema.execute_sync(
        _UPDATE,
        variable_values={"id": "not-a-global-id", "d": {"name": "Y"}},
    )
    assert res.errors is None, res.errors
    payload = res.data["updateItem"]
    assert payload["node"] is None
    assert [e["field"] for e in payload["errors"]] == ["id"]


# ---------------------------------------------------------------------------
# write-auth denial vs success
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_write_auth_denial_raises_top_level_error():
    """A deny permission raises a top-level ``GraphQLError`` (NOT an in-band payload)."""
    (
        schema,
        (
            CategoryT,
            _ItemT,
            _C,
            _U,
        ),
    ) = _build_item_form_schema(permission_classes=[_DenyAll])
    cat = product_models.Category.objects.create(name=_uniq("Cat"))
    res = schema.execute_sync(
        _CREATE,
        variable_values={"d": {"name": "X", "categoryId": global_id_for(CategoryT, cat.pk)}},
    )
    assert res.errors is not None
    assert "Not authorized" in str(res.errors[0].message)


@pytest.mark.django_db
def test_write_auth_runs_before_relation_visibility_decode():
    """An unauthorized caller submitting a HIDDEN relation id gets the auth denial,
    NOT a relation ``FieldError`` -- write-auth runs BEFORE the visibility-scoped
    relation decode, so an unauthorized actor cannot probe related-object
    visibility/existence by id (the authz-ordering side channel).

    Pre-fix the decode ran first, so a hidden ``categoryId`` returned an in-band
    ``FieldError`` payload (``res.errors is None``) while a *visible* one reached the
    denial -- an observable distinction. Post-fix both collapse to the denial.
    """

    @classmethod
    def hide_all(cls, qs, info):
        return qs.none()

    (
        schema,
        (
            CategoryT,
            _ItemT,
            _C,
            _U,
        ),
    ) = _build_item_form_schema(permission_classes=[_DenyAll], category_get_queryset=hide_all)
    cat = product_models.Category.objects.create(name=_uniq("Cat"))
    res = schema.execute_sync(
        _CREATE,
        variable_values={"d": {"name": "X", "categoryId": global_id_for(CategoryT, cat.pk)}},
    )
    # The denial (top-level GraphQLError), not a categoryId FieldError payload:
    # the visibility-scoped relation decode never ran for the unauthorized caller.
    assert res.errors is not None
    assert "Not authorized" in str(res.errors[0].message)
    assert res.data is None or res.data.get("createItem") is None


@pytest.mark.django_db
def test_plain_form_write_auth_denial_names_mutation_class():
    """A plain-form deny raises naming the mutation class (the ``_primary_type is None`` fallback)."""

    class ContactForm(forms.Form):
        message = forms.CharField()

    class Submit(DjangoFormMutation):
        class Meta:
            form_class = ContactForm
            permission_classes = [_DenyAll]

    @strawberry.type
    class Mutation:
        submit = DjangoMutationField(Submit)

    finalize_django_types()
    schema = _schema(Mutation)
    res = schema.execute_sync(
        "mutation($d: ContactFormInput!){ submit(data:$d){ ok errors{ field } } }",
        variable_values={"d": {"message": "hi"}},
    )
    assert res.errors is not None
    assert "Submit" in str(res.errors[0].message)


@pytest.mark.django_db
def test_write_auth_success_returns_payload():
    """An allow permission returns the success payload."""
    (
        schema,
        (
            CategoryT,
            _ItemT,
            _C,
            _U,
        ),
    ) = _build_item_form_schema(permission_classes=[_AllowAll])
    cat = product_models.Category.objects.create(name=_uniq("Cat"))
    res = schema.execute_sync(
        _CREATE,
        variable_values={"d": {"name": "OK", "categoryId": global_id_for(CategoryT, cat.pk)}},
    )
    assert res.errors is None, res.errors
    assert res.data["createItem"]["node"]["name"] == "OK"


# ---------------------------------------------------------------------------
# sync + async + SyncMisuseError
# ---------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
async def test_async_form_create_runs_under_one_sync_to_async():
    """The async surface resolves the same create (the sync body in one ``sync_to_async``).

    ``transaction=True`` is load-bearing (the async create commits on asgiref's
    executor-thread connection, which plain ``django_db`` rollback cannot reach).
    """
    (
        schema,
        (
            CategoryT,
            _ItemT,
            _C,
            _U,
        ),
    ) = _build_item_form_schema()
    cat = await product_models.Category.objects.acreate(name=_uniq("Cat"))
    res = await schema.execute(
        _CREATE,
        variable_values={"d": {"name": "Async", "categoryId": global_id_for(CategoryT, cat.pk)}},
    )
    assert res.errors is None, res.errors
    assert res.data["createItem"]["node"]["name"] == "Async"


@pytest.mark.django_db
def test_sync_create_meeting_async_get_queryset_raises_sync_misuse():
    """A sync form create meeting an ``async def get_queryset`` on a relation raises ``SyncMisuseError``."""

    async def _async_get_queryset(cls, qs, info):
        return qs

    CategoryT = type(
        "CategoryT",
        (DjangoType, relay.Node),
        {
            "Meta": type(
                "Meta",
                (),
                {"model": product_models.Category, "fields": ("id", "name"), "primary": True},
            ),
            "get_queryset": classmethod(_async_get_queryset),
        },
    )

    class ItemT(DjangoType, relay.Node):
        class Meta:
            model = product_models.Item
            fields = ("id", "name")
            primary = True

    form_cls = _item_model_form()

    class CreateItem(DjangoModelFormMutation):
        class Meta:
            form_class = form_cls
            operation = "create"
            permission_classes = [_AllowAll]

    @strawberry.type
    class Mutation:
        create_item = DjangoMutationField(CreateItem)

    finalize_django_types()
    schema = _schema(Mutation)
    cat = product_models.Category.objects.create(name=_uniq("Cat"))
    res = schema.execute_sync(
        "mutation($d: ItemModelFormInput!){ createItem(data:$d){ node{ name } errors{ field } } }",
        variable_values={"d": {"name": "X", "categoryId": global_id_for(CategoryT, cat.pk)}},
    )
    assert res.errors is not None
    assert any(isinstance(e.original_error, SyncMisuseError) for e in res.errors)


# ---------------------------------------------------------------------------
# G2 plan-shape (the ModelForm re-fetch rides the 036 G2 path) - load-bearing
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_modelform_refetch_keeps_select_related_and_suppresses_only():
    """The ModelForm re-fetch plan KEEPS ``select_related`` and applies NO ``.only(...)`` (G2).

    Pins the load-bearing property (BUILD.md "Query-shape tests must pin the
    load-bearing property"): a relation-selecting response keeps
    ``select_related``/``prefetch_related``, and ``.only(...)`` is suppressed
    because the op is a MUTATION - the re-fetch rides the SAME ``036``
    ``refetch_optimized`` G2 path. A bare "the relation came back" assertion would
    be non-distinguishing (identical optimized or N+1).
    """
    (
        schema,
        (
            CategoryT,
            _ItemT,
            _C,
            _U,
        ),
    ) = _build_item_form_schema()
    cat = product_models.Category.objects.create(name=_uniq("Cat"))
    ctx = SimpleNamespace()
    res = schema.execute_sync(
        _CREATE,
        variable_values={"d": {"name": "G", "categoryId": global_id_for(CategoryT, cat.pk)}},
        context_value=ctx,
    )
    assert res.errors is None, res.errors
    plan = ctx.dst_optimizer_plan
    # The relation selection (`category { name }`) is planned via select_related.
    assert plan.select_related == ("category",)
    # No `.only(...)` projection under a MUTATION (the G2 gate suppresses it).
    assert plan.only_fields == ()
