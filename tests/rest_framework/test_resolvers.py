"""Serializer-mutation resolver internals a live products `/graphql/` cannot drive (spec-039 Slice 3).

System-under-test is `rest_framework/resolvers.py` - but ONLY the residue the live
products serializer surface (`examples/fakeshop/test_query/test_products_api.py`)
cannot reach. Per the README "Coverage rule.", every consumer-reachable resolver
branch is earned LIVE; this file holds the genuinely-unreachable internals:

- the recursive `serializer_errors_to_field_errors` flattener over deeply-nested
  shapes no `ItemSerializer` error emits (list indexes, nested dicts, nested
  non-field buckets) - direct-called with synthetic `serializer.errors`-shaped
  dicts;
- raw-pk / NON-Relay relation decoding and MANY-relation decoding (products'
  `Category` is Relay-`GlobalID` + single, so the input only ever delivers one
  shape live - these need a synthetic non-Relay / many fixture and a direct call,
  M1);
- the value-preserving `save()`-called-once capture (a save spy);
- the save-time DRF-vs-Django `ValidationError` class split + the `IntegrityError`
  branch (a synthetic serializer whose `save()` raises each);
- the `get_serializer_kwargs` / framework-merge / `partial` / H3 seams + the bare
  `HttpRequest` `request_from_info` fallback;
- the config-assessment grep-guard + the post-finalization
  `_resolve_globalid_strategy` monkeypatch (recorded strategy consumed, not the
  live setting);
- the sync + async boundary and the `SyncMisuseError` async-`get_queryset`-from-sync
  path.

**No create/update happy path, envelope, reverse-map, partial-update, visibility,
write-auth, authorize-before-decode, Upload, request-context, or G2 test is
duplicated here** - those are owned by the live suite.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
import strawberry
from apps.library import models as library_models
from apps.products import models as product_models
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError
from django.http import HttpRequest
from rest_framework import serializers
from strawberry import relay

from django_strawberry_framework import (
    DjangoMutationField,
    DjangoType,
    SerializerMutation,
    finalize_django_types,
)
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.mutations.inputs import NON_FIELD_ERROR_KEY
from django_strawberry_framework.registry import registry
from django_strawberry_framework.rest_framework import resolvers as serializer_resolvers
from django_strawberry_framework.rest_framework.serializer_converter import (
    NESTED_MULTI,
    NESTED_SINGLE,
    SCALAR,
)
from django_strawberry_framework.testing.relay import global_id_for
from django_strawberry_framework.utils.querysets import SyncMisuseError


@pytest.fixture(autouse=True)
def _isolate_registry():
    """Reset the registry (co-clears the serializer-input ledger via the seam) per test."""
    registry.clear()
    yield
    registry.clear()


# ===========================================================================
# Recursive flattener shapes the products serializer never emits
# ===========================================================================
# `ItemSerializer` only ever emits flat field errors / a top-level `"__all__"`,
# so the recursive nesting (list indexes, nested dict child paths, nested
# non-field buckets) is unreachable live and direct-called here.


def test_flattener_list_index_child_error_becomes_dotted_path():
    """A `ListField` / `MultipleChoiceField` indexed child error -> dotted-path `tags.2`."""
    errors = {"tags": {2: ["bad tag"]}}
    flat = serializer_resolvers.serializer_errors_to_field_errors(errors, {})
    assert [(fe.field, fe.messages) for fe in flat] == [("tags.2", ["bad tag"])]


def test_flattener_nested_dict_error_joins_its_path():
    """A nested dict-shaped error joins its dotted path (`items.0.name`)."""
    errors = {"items": [{"name": ["required"]}]}
    flat = serializer_resolvers.serializer_errors_to_field_errors(errors, {})
    assert [(fe.field, fe.messages) for fe in flat] == [("items.0.name", ["required"])]


def test_flattener_nested_non_field_error_normalizes_to_path_all():
    """A nested `non_field_errors` bucket normalizes to `<path>.__all__`, no leaf dropped."""
    drf_key = serializer_resolvers._DRF_NON_FIELD_KEY
    errors = {"items": [{drf_key: ["cross-field at index 0"]}]}
    flat = serializer_resolvers.serializer_errors_to_field_errors(errors, {})
    # `items.0` + the non-field bucket -> the parent path's `"__all__"` at that level.
    assert [(fe.field, fe.messages) for fe in flat] == [
        (f"items.0.{NON_FIELD_ERROR_KEY}", ["cross-field at index 0"]),
    ]


def test_flattener_top_level_non_field_bucket_is_all_sentinel():
    """A top-level `non_field_errors` bucket normalizes to the bare `"__all__"` sentinel."""
    drf_key = serializer_resolvers._DRF_NON_FIELD_KEY
    errors = {drf_key: ["model-wide error"]}
    flat = serializer_resolvers.serializer_errors_to_field_errors(errors, {})
    assert [(fe.field, fe.messages) for fe in flat] == [
        (NON_FIELD_ERROR_KEY, ["model-wide error"]),
    ]


def test_flattener_rekeys_root_segment_through_reverse_map():
    """A top-level field's leaf path is re-keyed through the recursive reverse map (F5)."""
    reverse_map = {"category": ("categoryId", None)}
    errors = {"category": ["bad relation"], "items": [{"category": ["nested"]}]}
    flat = serializer_resolvers.serializer_errors_to_field_errors(errors, reverse_map)
    by_path = {fe.field: fe.messages for fe in flat}
    # `category` re-keyed to `categoryId`; the synthetic `items` has no reverse-map entry
    # (and no child map), so its children stay verbatim.
    assert by_path == {"categoryId": ["bad relation"], "items.0.category": ["nested"]}


def test_flattener_recursively_rekeys_nested_child_fields():
    """Nested child fields are re-keyed to their GraphQL names at EVERY depth (rev6 #17 review P2).

    A nested child field whose GraphQL name differs from its serializer name
    (``alt_branches`` -> ``altBranches``) is re-keyed inside the nested path, not left as the
    serializer name - so nested DRF validation errors match the framework decode-error paths.
    """
    from django_strawberry_framework.utils.inputs import InputFieldSpec

    child_specs = (
        InputFieldSpec(input_attr="code", graphql_name="code", target_name="code", kind=SCALAR),
        InputFieldSpec(
            input_attr="alt_branches",
            graphql_name="altBranches",
            target_name="alt_branches",
            kind=serializer_resolvers.RELATION_MULTI,
        ),
    )
    top_specs = [
        InputFieldSpec(
            input_attr="shelves",
            graphql_name="shelves",
            target_name="shelves",
            kind=NESTED_MULTI,
            nested_specs=child_specs,
        ),
    ]
    fake = type("M", (), {"_input_field_specs": top_specs})
    reverse_map = serializer_resolvers._reverse_map_for(fake)
    errors = {"shelves": [{"alt_branches": ["Bad pk"]}]}
    (fe,) = serializer_resolvers.serializer_errors_to_field_errors(errors, reverse_map)
    assert fe.field == "shelves.0.altBranches"
    assert fe.path == ["shelves", "0", "altBranches"]


def test_flattener_nested_non_field_bucket_keeps_all_sentinel_with_recursive_map():
    """A nested non-field bucket normalizes to ``<path>.__all__`` even with the recursive map (rev6 #17 review P2)."""
    from django_strawberry_framework.utils.inputs import InputFieldSpec

    child_specs = (
        InputFieldSpec(input_attr="code", graphql_name="code", target_name="code", kind=SCALAR),
    )
    top_specs = [
        InputFieldSpec(
            input_attr="shelves",
            graphql_name="shelves",
            target_name="shelves",
            kind=NESTED_MULTI,
            nested_specs=child_specs,
        ),
    ]
    fake = type("M", (), {"_input_field_specs": top_specs})
    reverse_map = serializer_resolvers._reverse_map_for(fake)
    drf_key = serializer_resolvers._DRF_NON_FIELD_KEY
    errors = {"shelves": [{drf_key: ["cross-field"]}]}
    (fe,) = serializer_resolvers.serializer_errors_to_field_errors(errors, reverse_map)
    assert fe.field == f"shelves.0.{NON_FIELD_ERROR_KEY}"
    assert fe.path == ["shelves", "0", NON_FIELD_ERROR_KEY]


# ===========================================================================
# Raw-pk / non-Relay + many-relation decode (synthetic, M1 - unreachable live)
# ===========================================================================
# Products' `Category` is Relay-`GlobalID` + single, so the generated input only
# ever delivers one GlobalID shape; the raw-pk / non-Relay and many branches are
# driven by direct call against a synthetic non-Relay primary.


def _declare_nonrelay_genre_primary():
    """A NON-Relay primary `DjangoType` over `Genre` (raw-pk target, no GlobalID)."""

    class GenreT(DjangoType):
        class Meta:
            model = library_models.Genre
            fields = ("id", "name")
            primary = True

    return GenreT


@pytest.mark.django_db
def test_decode_relation_single_raw_pk_hidden_target_is_field_error():
    """A raw-pk single relation whose target is hidden by `get_queryset` -> field-keyed error."""

    class GenreT(DjangoType):
        class Meta:
            model = library_models.Genre
            fields = ("id", "name")
            primary = True

        @classmethod
        def get_queryset(cls, queryset, info):
            # Hide everything: the raw pk resolves to no VISIBLE row.
            return queryset.none()

    del GenreT
    genre = library_models.Genre.objects.create(name="HiddenGenre")
    pk, error = serializer_resolvers._decode_relation_single(
        genre.pk,
        graphql_name="genreId",
        related_model=library_models.Genre,
        info=None,
    )
    assert pk is None
    assert error is not None
    assert error.field == "genreId"


@pytest.mark.django_db
def test_decode_relation_single_raw_pk_visible_reduces_to_pk():
    """A raw-pk single relation whose target is visible reduces to its pk (the DRF write value)."""
    _declare_nonrelay_genre_primary()
    genre = library_models.Genre.objects.create(name="VisibleGenre")
    pk, error = serializer_resolvers._decode_relation_single(
        genre.pk,
        graphql_name="genreId",
        related_model=library_models.Genre,
        info=None,
    )
    assert error is None
    assert pk == genre.pk


@pytest.mark.django_db
def test_decode_relation_single_uncoercible_raw_pk_is_field_error():
    """A raw-pk relation value that does not coerce to the target pk is a field-keyed error."""
    _declare_nonrelay_genre_primary()
    pk, error = serializer_resolvers._decode_relation_single(
        "not-a-pk",
        graphql_name="genreId",
        related_model=library_models.Genre,
        info=None,
    )
    assert pk is None
    assert error is not None
    assert error.field == "genreId"


@pytest.mark.django_db
def test_decode_relation_single_wrong_model_global_id_is_field_error():
    """A well-formed GlobalID for the WRONG model is a field-keyed error (no cross-model lookup)."""

    class GenreT(DjangoType, relay.Node):
        class Meta:
            model = library_models.Genre
            fields = ("id", "name")
            primary = True

    finalize_django_types()
    genre = library_models.Genre.objects.create(name="WrongModelGenre")
    # A GlobalID whose type slot names a DIFFERENT model (`library.shelf`) than the
    # Genre-typed relation: `decode_model_global_id` rejects the model mismatch ->
    # field error, never a cross-model pk lookup.
    wrong_gid = relay.GlobalID(type_name="library.shelf", node_id=str(genre.pk))
    pk, error = serializer_resolvers._decode_relation_single(
        wrong_gid,
        graphql_name="genreId",
        related_model=library_models.Genre,
        info=None,
    )
    assert pk is None
    assert error is not None
    assert error.field == "genreId"


@pytest.mark.django_db
def test_decode_relation_multi_collects_visible_then_short_circuits():
    """A many-relation collects each visible member's pk and short-circuits on a bad element."""
    _declare_nonrelay_genre_primary()
    g1 = library_models.Genre.objects.create(name="MG1")
    g2 = library_models.Genre.objects.create(name="MG2")
    pks, error = serializer_resolvers._decode_relation_multi(
        [g1.pk, g2.pk],
        graphql_name="genreIds",
        related_model=library_models.Genre,
        info=None,
    )
    assert error is None
    assert pks == [g1.pk, g2.pk]

    # A bad (uncoercible) element short-circuits to the field-keyed error.
    pks, error = serializer_resolvers._decode_relation_multi(
        [g1.pk, "bad"],
        graphql_name="genreIds",
        related_model=library_models.Genre,
        info=None,
    )
    assert pks is None
    assert error is not None
    assert error.field == "genreIds"


@pytest.mark.django_db
def test_decode_relation_single_explicit_none_passes_through():
    """An explicit `None` is a clear / no-value passed through (the serializer decides required-ness)."""
    _declare_nonrelay_genre_primary()
    pk, error = serializer_resolvers._decode_relation_single(
        None,
        graphql_name="genreId",
        related_model=library_models.Genre,
        info=None,
    )
    assert error is None
    assert pk is None


@pytest.mark.django_db
def test_decode_relation_multi_explicit_none_passes_through():
    """An explicit `None` whole-list is passed through (the serializer's required-ness decides), no per-member walk."""
    _declare_nonrelay_genre_primary()
    pks, error = serializer_resolvers._decode_relation_multi(
        None,
        graphql_name="genreIds",
        related_model=library_models.Genre,
        info=None,
    )
    assert error is None
    assert pks is None


@pytest.mark.django_db
def test_decode_relation_multi_empty_list_passes_through_without_query():
    """An empty many-relation input returns an empty list before any visibility query."""
    _declare_nonrelay_genre_primary()
    pks, error = serializer_resolvers._decode_relation_multi(
        [],
        graphql_name="genreIds",
        related_model=library_models.Genre,
        info=None,
    )
    assert error is None
    assert pks == []


# ===========================================================================
# Value-preserving save, save-time exception split, IntegrityError
# ===========================================================================


def _bind_item_serializer_mutation(serializer_cls, *, operation="create"):
    """Declare + finalize a minimal `SerializerMutation` over `serializer_cls`."""
    op_value = operation

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

    class _AllowAll:
        def has_permission(
            self,
            info,
            mutation,
            op,
            data,
            instance=None,
        ):
            return True

    class WriteItem(SerializerMutation):
        class Meta:
            serializer_class = serializer_cls
            operation = op_value
            permission_classes = [_AllowAll]

    @strawberry.type
    class Query:
        @strawberry.field
        def ping(self) -> int:
            return 1

    @strawberry.type
    class Mutation:
        write_item = DjangoMutationField(WriteItem)

    finalize_django_types()
    strawberry.Schema(query=Query, mutation=Mutation)
    del CategoryT, ItemT
    return WriteItem


@pytest.mark.django_db
def test_serializer_save_is_called_exactly_once_and_refetch_uses_returned_object():
    """`serializer.save()` is called EXACTLY once; the value-preserving closure captures the return."""
    calls = []

    class SpyItemSerializer(serializers.ModelSerializer):
        class Meta:
            model = product_models.Item
            fields = ("name", "category")

        def save(self, **kwargs):
            calls.append(1)
            return super().save(**kwargs)

    category = product_models.Category.objects.create(name="SpyCat")
    write_step = serializer_resolvers._serializer_write_step

    # Drive the write step directly with a constructed mutation + a faked info.
    mutation_cls = _bind_item_serializer_mutation(SpyItemSerializer)
    request = HttpRequest()
    request.user = SimpleNamespace(username="spy", is_authenticated=True)
    info = SimpleNamespace(context=SimpleNamespace(request=request))

    provided = {"name": "SpyItem", "category": category.pk}
    saved = write_step(mutation_cls, info, None, provided)
    assert calls == [1]  # save() called exactly once
    assert isinstance(saved, product_models.Item)
    assert saved.pk is not None
    assert saved.name == "SpyItem"


@pytest.mark.django_db
def test_save_time_drf_validation_error_uses_recursive_flattener_not_flat_mapper():
    """A save-time DRF `ValidationError` routes `.detail` through the recursive flattener."""

    class DRFRaisingSerializer(serializers.ModelSerializer):
        class Meta:
            model = product_models.Item
            fields = ("name", "category")

        def save(self, **kwargs):
            raise serializers.ValidationError({"name": ["drf save-time"]})

    category = product_models.Category.objects.create(name="DRFRaiseCat")
    mutation_cls = _bind_item_serializer_mutation(DRFRaisingSerializer)
    request = HttpRequest()
    request.user = SimpleNamespace(username="u", is_authenticated=True)
    info = SimpleNamespace(context=SimpleNamespace(request=request))

    result = serializer_resolvers._serializer_write_step(
        mutation_cls,
        info,
        None,
        {"name": "OK", "category": category.pk},
    )
    assert isinstance(result, list)
    assert [(fe.field, fe.messages) for fe in result] == [("name", ["drf save-time"])]


@pytest.mark.django_db
def test_save_time_django_validation_error_uses_flat_mapper_not_detail():
    """A save-time Django `ValidationError` routes through the flat `036` mapper, never `.detail`."""

    class DjangoRaisingSerializer(serializers.ModelSerializer):
        class Meta:
            model = product_models.Item
            fields = ("name", "category")

        def save(self, **kwargs):
            raise DjangoValidationError({"name": ["django save-time"]})

    category = product_models.Category.objects.create(name="DjRaiseCat")
    mutation_cls = _bind_item_serializer_mutation(DjangoRaisingSerializer)
    request = HttpRequest()
    request.user = SimpleNamespace(username="u", is_authenticated=True)
    info = SimpleNamespace(context=SimpleNamespace(request=request))

    result = serializer_resolvers._serializer_write_step(
        mutation_cls,
        info,
        None,
        {"name": "OK", "category": category.pk},
    )
    assert isinstance(result, list)
    # The Django mapper keys to the model field name `name` (NOT a DRF `.detail` read).
    assert [(fe.field, fe.messages) for fe in result] == [("name", ["django save-time"])]


@pytest.mark.django_db
def test_save_time_integrity_error_maps_to_all_sentinel_envelope():
    """A save-time `IntegrityError` (a race) maps to the `"__all__"` envelope via `save_or_field_errors`."""

    class IntegrityRaisingSerializer(serializers.ModelSerializer):
        class Meta:
            model = product_models.Item
            fields = ("name", "category")

        def save(self, **kwargs):
            raise IntegrityError("races to the unique constraint")

    category = product_models.Category.objects.create(name="IntRaiseCat")
    mutation_cls = _bind_item_serializer_mutation(IntegrityRaisingSerializer)
    request = HttpRequest()
    request.user = SimpleNamespace(username="u", is_authenticated=True)
    info = SimpleNamespace(context=SimpleNamespace(request=request))

    result = serializer_resolvers._serializer_write_step(
        mutation_cls,
        info,
        None,
        {"name": "OK", "category": category.pk},
    )
    assert isinstance(result, list)
    assert [fe.field for fe in result] == [NON_FIELD_ERROR_KEY]


# ===========================================================================
# M2 / H3 - required+allow_null omission vs explicit null at the decode
# ===========================================================================


@pytest.mark.django_db
def test_decode_strips_omission_but_preserves_explicit_null():
    """A `required=True, allow_null=True` field: omission is stripped (DRF sees MISSING); explicit null is preserved (spec-039 H3).

    The input field is GraphQL-omittable (UNSET default), so the input dataclass
    constructs WITHOUT the key (no top-level coercion error - the bug H3 flags). The
    decode then strips `UNSET` so DRF sees the key MISSING (and `is_valid()` raises its
    own field-keyed required error in-band), while an explicit `null` is preserved as
    `None` so DRF applies its `allow_null` rule.
    """

    class ReqNullSerializer(serializers.ModelSerializer):
        name = serializers.CharField(allow_null=True)  # required=True, allow_null=True

        class Meta:
            model = product_models.Category
            fields = ("name",)

    mutation_cls = _bind_item_serializer_mutation(ReqNullSerializer)

    # Omission: the input constructs without `name` (UNSET default proves it is
    # omittable, so no top-level construction error), and the decode strips it.
    omitted = mutation_cls._input_class()
    provided_omit, err_omit = serializer_resolvers._decode_serializer_data(
        mutation_cls,
        omitted,
        info=None,
    )
    assert err_omit is None
    assert "name" not in provided_omit  # DRF sees the key MISSING -> its required error

    # Explicit null: preserved as None (reaches DRF, which applies allow_null).
    explicit = mutation_cls._input_class(name=None)
    provided_null, err_null = serializer_resolvers._decode_serializer_data(
        mutation_cls,
        explicit,
        info=None,
    )
    assert err_null is None
    assert provided_null["name"] is None


@pytest.mark.django_db
def test_decode_serializer_data_rejects_unencodable_scalar():
    """A lone-surrogate scalar trips the invalid-Unicode preflight -> field-keyed error, no data (the 036/038 parity).

    A lone surrogate graphql-core accepts as a `String` would otherwise reach the
    serializer's `validate_unique` / `save()` and raise a raw `UnicodeEncodeError`
    escaping the envelope; the decode rejects it here, keyed to the GraphQL field name.
    """

    class NameSerializer(serializers.ModelSerializer):
        class Meta:
            model = product_models.Category
            fields = ("name",)

    mutation_cls = _bind_item_serializer_mutation(NameSerializer)
    data = mutation_cls._input_class(name="\ud800")  # a lone high surrogate (unencodable)
    provided, error = serializer_resolvers._decode_serializer_data(mutation_cls, data, info=None)
    assert provided == {}
    assert error is not None
    assert error.field == "name"


# ===========================================================================
# H6 - a save-time validation error after a partial write rolls back
# ===========================================================================


@pytest.mark.django_db
def test_save_time_validation_after_partial_write_is_rolled_back():
    """A serializer whose `save()` writes a row then raises validation -> the partial write is rolled back (spec-039 H6).

    The shared write skeleton wraps the pipeline in `transaction.atomic()`; a
    `write_step` that made a partial DB write and THEN raised a validation error
    (mapped to the envelope inside the atomic block) marks the transaction for rollback
    so the partial write never commits. Driven through the full `resolve_serializer_sync`
    pipeline (the atomic boundary lives in the shared skeleton, not the write step).
    """
    sentinel = "SIDE_EFFECT_ROW_H6"

    class PartialWriteSerializer(serializers.ModelSerializer):
        class Meta:
            model = product_models.Category
            fields = ("name",)

        def save(self, **kwargs):
            # A partial write BEFORE the failure: insert a side-effect row, then raise.
            product_models.Category.objects.create(name=sentinel)
            raise serializers.ValidationError({"name": ["rejected after a partial write"]})

    mutation_cls = _bind_item_serializer_mutation(PartialWriteSerializer)
    request = HttpRequest()
    request.user = SimpleNamespace(username="u", is_authenticated=True)
    info = SimpleNamespace(context=SimpleNamespace(request=request))
    data = mutation_cls._input_class(name="NewCat")

    result = serializer_resolvers.resolve_serializer_sync(
        mutation_cls,
        info,
        data=data,
        id=strawberry.UNSET,
    )

    # The mutation returns the error envelope (null object + the field error)...
    assert [fe.field for fe in result.errors] == ["name"]
    # ...and the side-effect row is NOT persisted: the atomic block was rolled back (H6).
    assert not product_models.Category.objects.filter(name=sentinel).exists()


# ===========================================================================
# get_serializer_kwargs precedence / framework merge / H3 (hermetic)
# ===========================================================================


def _basic_item_serializer():
    class BasicItemSerializer(serializers.ModelSerializer):
        class Meta:
            model = product_models.Item
            fields = ("name", "category")

    return BasicItemSerializer


@pytest.mark.django_db
def test_merged_kwargs_injects_partial_true_on_update_never_create():
    """The framework injects `partial=True` for update (instance present), never for create."""
    mutation_cls = _bind_item_serializer_mutation(_basic_item_serializer())
    request = HttpRequest()
    request.user = SimpleNamespace(username="u", is_authenticated=True)
    info = SimpleNamespace(context=SimpleNamespace(request=request))

    create_kwargs = serializer_resolvers._merged_serializer_kwargs(
        mutation_cls,
        info,
        provided_data={"name": "X"},
        instance=None,
    )
    assert "partial" not in create_kwargs

    instance = SimpleNamespace(pk=1)
    update_kwargs = serializer_resolvers._merged_serializer_kwargs(
        mutation_cls,
        info,
        provided_data={"name": "X"},
        instance=instance,
    )
    assert update_kwargs["partial"] is True


@pytest.mark.django_db
def test_merged_kwargs_sets_framework_request_unconditionally():
    """`context["request"]` is set to the framework request, defaulting `data` to `provided_data`."""
    mutation_cls = _bind_item_serializer_mutation(_basic_item_serializer())
    request = HttpRequest()
    request.user = SimpleNamespace(username="u", is_authenticated=True)
    info = SimpleNamespace(context=SimpleNamespace(request=request))

    kwargs = serializer_resolvers._merged_serializer_kwargs(
        mutation_cls,
        info,
        provided_data={"name": "X"},
        instance=None,
    )
    assert kwargs["data"] == {"name": "X"}
    assert kwargs["context"]["request"] is request


@pytest.mark.django_db
def test_merged_kwargs_merges_override_context_keys_keeping_framework_request():
    """An override's non-`request` context keys are kept; the framework `request` always wins."""

    class OverridingMutation(SerializerMutation):
        class Meta:
            serializer_class = _basic_item_serializer()
            operation = "create"

        def get_serializer_kwargs(
            self,
            info,
            *,
            data,
            instance=None,
        ):
            kwargs = super().get_serializer_kwargs(info, data=data, instance=instance)
            kwargs["context"] = {"extra": "value"}
            return kwargs

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

    @strawberry.type
    class Query:
        @strawberry.field
        def ping(self) -> int:
            return 1

    @strawberry.type
    class Mutation:
        write_item = DjangoMutationField(OverridingMutation)

    finalize_django_types()
    strawberry.Schema(query=Query, mutation=Mutation)
    del CategoryT, ItemT

    request = HttpRequest()
    request.user = SimpleNamespace(username="u", is_authenticated=True)
    info = SimpleNamespace(context=SimpleNamespace(request=request))
    kwargs = serializer_resolvers._merged_serializer_kwargs(
        OverridingMutation,
        info,
        provided_data={"name": "X"},
        instance=None,
    )
    assert kwargs["context"]["extra"] == "value"  # the override key is kept
    assert kwargs["context"]["request"] is request  # the framework request wins


@pytest.mark.django_db
def test_merged_kwargs_override_returning_partial_is_configuration_error():
    """A `get_serializer_kwargs` override returning `partial` itself is a `ConfigurationError`."""

    class PartialReturningMutation(SerializerMutation):
        class Meta:
            serializer_class = _basic_item_serializer()
            operation = "update"

        def get_serializer_kwargs(
            self,
            info,
            *,
            data,
            instance=None,
        ):
            kwargs = super().get_serializer_kwargs(info, data=data, instance=instance)
            kwargs["partial"] = False
            return kwargs

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

    @strawberry.type
    class Query:
        @strawberry.field
        def ping(self) -> int:
            return 1

    @strawberry.type
    class Mutation:
        write_item = DjangoMutationField(PartialReturningMutation)

    finalize_django_types()
    strawberry.Schema(query=Query, mutation=Mutation)
    del CategoryT, ItemT

    request = HttpRequest()
    request.user = SimpleNamespace(username="u", is_authenticated=True)
    info = SimpleNamespace(context=SimpleNamespace(request=request))
    with pytest.raises(ConfigurationError, match="partial"):
        serializer_resolvers._merged_serializer_kwargs(
            PartialReturningMutation,
            info,
            provided_data={"name": "X"},
            instance=SimpleNamespace(pk=1),
        )


@pytest.mark.django_db
def test_merged_kwargs_override_different_request_object_is_configuration_error():
    """An override supplying a DIFFERENT `context["request"]` object is a `ConfigurationError`."""

    class WrongRequestMutation(SerializerMutation):
        class Meta:
            serializer_class = _basic_item_serializer()
            operation = "create"

        def get_serializer_kwargs(
            self,
            info,
            *,
            data,
            instance=None,
        ):
            kwargs = super().get_serializer_kwargs(info, data=data, instance=instance)
            kwargs["context"] = {"request": HttpRequest()}  # a DIFFERENT request object
            return kwargs

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

    @strawberry.type
    class Query:
        @strawberry.field
        def ping(self) -> int:
            return 1

    @strawberry.type
    class Mutation:
        write_item = DjangoMutationField(WrongRequestMutation)

    finalize_django_types()
    strawberry.Schema(query=Query, mutation=Mutation)
    del CategoryT, ItemT

    request = HttpRequest()
    request.user = SimpleNamespace(username="u", is_authenticated=True)
    info = SimpleNamespace(context=SimpleNamespace(request=request))
    with pytest.raises(ConfigurationError, match="request"):
        serializer_resolvers._merged_serializer_kwargs(
            WrongRequestMutation,
            info,
            provided_data={"name": "X"},
            instance=None,
        )


@pytest.mark.django_db
def test_merged_kwargs_bare_httprequest_info_context_fallback():
    """`request_from_info` resolves a bare `HttpRequest` `info.context` (the no-`.request` fallback)."""
    mutation_cls = _bind_item_serializer_mutation(_basic_item_serializer())
    bare_request = HttpRequest()
    bare_request.user = SimpleNamespace(username="u", is_authenticated=True)
    # `info.context` IS the HttpRequest (no `.request` attribute layer).
    info = SimpleNamespace(context=bare_request)
    kwargs = serializer_resolvers._merged_serializer_kwargs(
        mutation_cls,
        info,
        provided_data={"name": "X"},
        instance=None,
    )
    assert kwargs["context"]["request"] is bare_request


# ===========================================================================
# Config assessment: recorded GlobalID strategy consumed, not the live setting
# ===========================================================================


def test_resolvers_source_has_no_live_strategy_reads_grep_guard():
    """DoD grep-guard: `rest_framework/resolvers.py` references neither `conf.settings` nor `_resolve_globalid_strategy`.

    A relation `GlobalID` is decoded against the target type's RECORDED
    `effective_globalid_strategy` via `decode_model_global_id` (resolved once at
    finalization), never a per-request settings re-read / re-validation on the query
    path.
    """
    import inspect

    source = inspect.getsource(serializer_resolvers)
    assert "conf.settings" not in source
    assert "_resolve_globalid_strategy" not in source


@pytest.mark.django_db
def test_relation_decode_consumes_recorded_strategy_after_strategy_resolver_fails(monkeypatch):
    """After finalize, a serializer relation decode still resolves with `_resolve_globalid_strategy` broken.

    The behavioral backstop for the grep-guard: monkeypatch
    `types/relay.py::_resolve_globalid_strategy` to RAISE (as if a per-request
    re-read were attempted), then drive the relation decode - it must still resolve
    through the target type's recorded `effective_globalid_strategy`, proving the
    query path never re-reads the live setting.
    """

    class CategoryT(DjangoType, relay.Node):
        class Meta:
            model = product_models.Category
            fields = ("id", "name")
            primary = True

    finalize_django_types()
    category = product_models.Category.objects.create(name="StrategyCat")
    gid = relay.GlobalID.from_id(global_id_for(CategoryT, category.pk))

    from django_strawberry_framework.types import relay as relay_module

    def _boom(*args, **kwargs):
        raise AssertionError("_resolve_globalid_strategy must not run on the query path")

    monkeypatch.setattr(relay_module, "_resolve_globalid_strategy", _boom)

    pk, error = serializer_resolvers._decode_relation_single(
        gid,
        graphql_name="categoryId",
        related_model=product_models.Category,
        info=None,
    )
    assert error is None
    assert pk == category.pk


# ===========================================================================
# Sync + async boundary + SyncMisuseError
# ===========================================================================


@pytest.mark.django_db
def test_relation_decode_async_get_queryset_from_sync_raises_sync_misuse():
    """A relation target whose `get_queryset` is `async def`, met in the sync decode, raises `SyncMisuseError`."""

    class GenreT(DjangoType):
        class Meta:
            model = library_models.Genre
            fields = ("id", "name")
            primary = True

        @classmethod
        async def get_queryset(cls, queryset, info):  # async hook on the sync path
            return queryset

    del GenreT
    genre = library_models.Genre.objects.create(name="AsyncGenre")
    with pytest.raises(SyncMisuseError):
        serializer_resolvers._decode_relation_single(
            genre.pk,
            graphql_name="genreId",
            related_model=library_models.Genre,
            info=None,
        )


@pytest.mark.django_db(transaction=True)
async def test_async_serializer_resolver_runs_sync_body_under_sync_to_async():
    """The async entry runs the sync body in one `sync_to_async(thread_sensitive=True)` call.

    Driven through the `SerializerMutation.resolve_async` SEAM (not the resolver function
    directly), so the seam's delegation to `resolve_serializer_async` is exercised too; that
    in turn rides the shared `run_pipeline_async` boundary. A create over the async surface
    returns the success payload (the same body the sync path runs), proving the seam +
    boundary are wired.
    """

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

    class _AllowAll:
        def has_permission(
            self,
            info,
            mutation,
            op,
            data,
            instance=None,
        ):
            return True

    class AsyncBasicItemSerializer(serializers.ModelSerializer):
        class Meta:
            model = product_models.Item
            fields = ("name", "category")

    class CreateItemAsync(SerializerMutation):
        class Meta:
            serializer_class = AsyncBasicItemSerializer
            operation = "create"
            permission_classes = [_AllowAll]

    @strawberry.type
    class Query:
        @strawberry.field
        def ping(self) -> int:
            return 1

    @strawberry.type
    class Mutation:
        write_item = DjangoMutationField(CreateItemAsync)

    finalize_django_types()
    strawberry.Schema(query=Query, mutation=Mutation)
    del CategoryT, ItemT

    from asgiref.sync import sync_to_async

    category = await sync_to_async(product_models.Category.objects.create)(name="AsyncCat")
    gid = relay.GlobalID(type_name="products.category", node_id=str(category.pk))

    @strawberry.input
    class _Data:
        name: str
        category_id: strawberry.ID = strawberry.field(name="categoryId")

    request = HttpRequest()
    request.user = SimpleNamespace(username="async-u", is_authenticated=True)
    info = SimpleNamespace(context=SimpleNamespace(request=request))
    data = _Data(name="AsyncItem", category_id=gid)

    payload = await CreateItemAsync.resolve_async(info, data=data, id=None)
    assert payload.errors == []
    assert payload.node is not None
    assert payload.node.name == "AsyncItem"


# ===========================================================================
# Structured error codes + paths (spec-039 rev6 #4 / #13)
# ===========================================================================


def test_flattener_preserves_error_detail_codes_and_path():
    """A DRF ``ErrorDetail.code`` -> ``codes``; the dotted key -> structured ``path`` segments (#4 / #13)."""
    from rest_framework.exceptions import ErrorDetail

    errors = {
        "name": [ErrorDetail("This field is required.", code="required")],
        "items": [{"qty": [ErrorDetail("Not valid.", code="invalid")]}],
    }
    flat = serializer_resolvers.serializer_errors_to_field_errors(errors, {})
    by_field = {fe.field: (fe.codes, fe.path) for fe in flat}
    assert by_field["name"] == (["required"], ["name"])
    assert by_field["items.0.qty"] == (["invalid"], ["items", "0", "qty"])


def test_flattener_root_non_field_error_has_empty_path():
    """A ROOT non-field error is ``field="__all__"`` with an EMPTY ``path`` (the documented rule, #13)."""
    from rest_framework.exceptions import ErrorDetail

    drf_key = serializer_resolvers._DRF_NON_FIELD_KEY
    errors = {drf_key: [ErrorDetail("Model-wide problem.", code="invalid")]}
    (fe,) = serializer_resolvers.serializer_errors_to_field_errors(errors, {})
    assert fe.field == NON_FIELD_ERROR_KEY
    assert fe.path == []
    assert fe.codes == ["invalid"]


def test_flattener_nested_non_field_error_keeps_all_sentinel_segment():
    """A NESTED non-field error keeps the ``"__all__"`` sentinel as its final path segment (#13)."""
    from rest_framework.exceptions import ErrorDetail

    drf_key = serializer_resolvers._DRF_NON_FIELD_KEY
    errors = {"items": [{drf_key: [ErrorDetail("Cross-field.", code="invalid")]}]}
    (fe,) = serializer_resolvers.serializer_errors_to_field_errors(errors, {})
    assert fe.path == ["items", "0", NON_FIELD_ERROR_KEY]


def test_flattener_plain_string_leaf_has_no_codes():
    """A plain (non-``ErrorDetail``) string leaf yields no codes (only real codes are surfaced)."""
    flat = serializer_resolvers.serializer_errors_to_field_errors({"name": ["plain string"]}, {})
    (fe,) = flat
    assert fe.codes == []
    assert fe.path == ["name"]


def test_flattener_bare_error_detail_preserves_code():
    """A bare DRF ``ErrorDetail`` leaf still preserves its single code (#4)."""
    from rest_framework.exceptions import ErrorDetail

    flat = serializer_resolvers.serializer_errors_to_field_errors(
        {"name": ErrorDetail("Invalid.", code="invalid")},
        {},
    )
    (fe,) = flat
    assert fe.codes == ["invalid"]
    assert fe.path == ["name"]


# ===========================================================================
# Schema/runtime serializer agreement guard (spec-039 rev6 #1)
# ===========================================================================


def _agreement_specs(**overrides):
    """Build a single ``InputFieldSpec`` (defaults to a scalar ``code``) for the guard tests."""
    from django_strawberry_framework.utils.inputs import InputFieldSpec

    base = {
        "input_attr": "code",
        "graphql_name": "code",
        "target_name": "code",
        "kind": SCALAR,
    }
    base.update(overrides)
    return type("FakeMut", (), {"_input_field_specs": [InputFieldSpec(**base)]})


def _shelf_model_serializer():
    """A ``ModelSerializer`` over ``Shelf`` (``code`` scalar + ``branch`` PK relation)."""

    class ShelfSer(serializers.ModelSerializer):
        class Meta:
            model = library_models.Shelf
            fields = ("code", "branch")

    return ShelfSer(data={})


def test_agreement_guard_raises_when_runtime_lacks_schema_field():
    """A schema field the runtime serializer does not declare fails loud (#1)."""
    fake = _agreement_specs(input_attr="ghost", graphql_name="ghost", target_name="ghost")
    with pytest.raises(ConfigurationError, match="does not declare it"):
        serializer_resolvers._assert_schema_runtime_agreement(fake, _shelf_model_serializer())


def test_agreement_guard_raises_when_runtime_field_read_only():
    """A schema field the runtime declares read_only fails loud (the value would be ignored) (#1)."""

    class ROSer(serializers.ModelSerializer):
        code = serializers.CharField(read_only=True)

        class Meta:
            model = library_models.Shelf
            fields = ("code", "branch")

    with pytest.raises(ConfigurationError, match="read_only"):
        serializer_resolvers._assert_schema_runtime_agreement(_agreement_specs(), ROSer(data={}))


def test_agreement_guard_raises_on_source_mismatch():
    """A runtime field binding a different source than the schema recorded fails loud (#1)."""
    # Schema recorded source "topic"; runtime "code" binds source "code".
    fake = _agreement_specs(source="topic")
    with pytest.raises(ConfigurationError, match="binds source"):
        serializer_resolvers._assert_schema_runtime_agreement(fake, _shelf_model_serializer())


def test_agreement_guard_raises_on_relation_wrong_model():
    """A runtime relation over a DIFFERENT model than the schema recorded fails loud (#1)."""
    fake = _agreement_specs(
        input_attr="branch_id",
        graphql_name="branchId",
        target_name="branch",
        kind=serializer_resolvers.RELATION_SINGLE,
        related_model=library_models.Patron,  # runtime branch targets Branch, not Patron.
    )
    with pytest.raises(ConfigurationError, match="different model"):
        serializer_resolvers._assert_schema_runtime_agreement(fake, _shelf_model_serializer())


def test_agreement_guard_raises_when_scalar_became_relation():
    """A schema scalar that is a relation at runtime fails loud (the kind moved) (#1)."""
    # Schema types "branch" as a SCALAR, but the runtime serializer declares it a relation.
    fake = _agreement_specs(target_name="branch", input_attr="branch", graphql_name="branch")
    with pytest.raises(ConfigurationError, match="scalar in the schema but a relation"):
        serializer_resolvers._assert_schema_runtime_agreement(fake, _shelf_model_serializer())


def test_agreement_guard_raises_when_file_became_scalar():
    """A schema file input that is scalar at runtime fails loud (the kind moved) (#1)."""

    class FileDriftSer(serializers.Serializer):
        upload = serializers.CharField()

    fake = _agreement_specs(
        target_name="upload",
        input_attr="upload",
        graphql_name="upload",
        kind=serializer_resolvers.FILE,
    )
    with pytest.raises(ConfigurationError, match="file input"):
        serializer_resolvers._assert_schema_runtime_agreement(fake, FileDriftSer(data={}))


def test_agreement_guard_raises_when_relation_shape_wrong():
    """A schema relation the runtime declares as a scalar fails loud (#1)."""
    fake = _agreement_specs(
        target_name="code",
        input_attr="code_id",
        graphql_name="codeId",
        kind=serializer_resolvers.RELATION_SINGLE,
        related_model=library_models.Branch,
    )
    with pytest.raises(ConfigurationError, match="primary-key relation"):
        serializer_resolvers._assert_schema_runtime_agreement(fake, _shelf_model_serializer())


def test_agreement_guard_passes_when_schema_and_runtime_agree():
    """The happy path: matching scalar + relation specs pass (no raise) (#1)."""
    from django_strawberry_framework.utils.inputs import InputFieldSpec

    fake = type(
        "OkMut",
        (),
        {
            "_input_field_specs": [
                InputFieldSpec(
                    input_attr="code",
                    graphql_name="code",
                    target_name="code",
                    kind=SCALAR,
                ),
                InputFieldSpec(
                    input_attr="branch_id",
                    graphql_name="branchId",
                    target_name="branch",
                    kind=serializer_resolvers.RELATION_SINGLE,
                    related_model=library_models.Branch,
                ),
            ],
        },
    )
    # No raise.
    serializer_resolvers._assert_schema_runtime_agreement(fake, _shelf_model_serializer())


# ===========================================================================
# Explicit injection contract runtime verification (spec-039 rev6 #2)
# ===========================================================================


def _topic_shelf_serializer_class():
    """A ``Shelf`` serializer declaring a required ``topic`` (the injected-field fixture)."""

    class ShelfSer(serializers.ModelSerializer):
        topic = serializers.CharField(required=True)

        class Meta:
            model = library_models.Shelf
            fields = ("code", "branch", "topic")

    return ShelfSer


def _injected_topic_mut(specs=None):
    """A fake mutation declaring ``injected_fields=("topic",)`` + its stashed schema-time spec."""
    from django_strawberry_framework.utils.inputs import InputFieldSpec

    topic_spec = InputFieldSpec(
        input_attr="topic",
        graphql_name="topic",
        target_name="topic",
        kind=SCALAR,
    )
    return type(
        "InjectMut",
        (),
        {
            "_mutation_meta": SimpleNamespace(injected_fields=("topic",)),
            "_injected_field_specs": [topic_spec] if specs is None else specs,
        },
    )


def test_declared_injected_field_missing_from_data_raises_at_runtime():
    """A ``Meta.injected_fields`` the override did NOT supply into data fails loud (rev6 #2)."""
    # ``topic`` IS a runtime field (agreement passes), but the override did not put it in data.
    serializer = _topic_shelf_serializer_class()(data={"code": "X", "branch": 1})
    with pytest.raises(ConfigurationError, match="did not supply"):
        serializer_resolvers._assert_injected_fields_supplied(_injected_topic_mut(), serializer)


def test_declared_injected_field_dropped_by_runtime_serializer_raises():
    """An injected field the RUNTIME serializer does not declare fails loud (rev6 rev2 P1 - not just presence)."""
    # ``_shelf_model_serializer`` has NO ``topic``; the runtime-agreement check catches it even
    # though a naive presence check would (wrongly) pass once the key were injected.
    serializer = _shelf_model_serializer()
    with pytest.raises(ConfigurationError, match="does not declare it"):
        serializer_resolvers._assert_injected_fields_supplied(_injected_topic_mut(), serializer)


def test_supplied_injected_field_passes_runtime_check():
    """A declared injected field present + runtime-accepted passes (rev6 #2 happy path)."""
    serializer = _topic_shelf_serializer_class()(
        data={"code": "X", "branch": 1, "topic": "supplied"},
    )
    # No raise: ``topic`` is a writable runtime field AND present in the serializer's data.
    serializer_resolvers._assert_injected_fields_supplied(_injected_topic_mut(), serializer)


def test_no_injected_fields_is_a_runtime_noop():
    """A mutation with no ``Meta.injected_fields`` skips the runtime injection check (rev6 #2)."""
    fake = type("PlainMut", (), {"_mutation_meta": SimpleNamespace(injected_fields=None)})
    serializer_resolvers._assert_injected_fields_supplied(
        fake,
        _shelf_model_serializer(),
    )  # no raise


# ===========================================================================
# Batched multi-relation visibility (spec-039 rev6 #3)
# ===========================================================================


@pytest.mark.django_db
def test_decode_relation_multi_uses_a_single_batched_visibility_query():
    """A many-relation confirms the WHOLE set's visibility in ONE ``pk__in`` query (rev6 #3)."""
    from django.db import connection
    from django.test.utils import CaptureQueriesContext

    _declare_nonrelay_genre_primary()
    genres = [library_models.Genre.objects.create(name=f"BatchG{i}") for i in range(3)]
    pks = [g.pk for g in genres]

    with CaptureQueriesContext(connection) as ctx:
        result, error = serializer_resolvers._decode_relation_multi(
            pks,
            graphql_name="genreIds",
            related_model=library_models.Genre,
            info=None,
        )
    assert error is None
    assert result == pks
    # ONE batched pk__in query for all 3 members (not one visibility query per element).
    assert len(ctx.captured_queries) == 1


@pytest.mark.django_db
def test_decode_relation_multi_hidden_member_is_field_error_via_batch():
    """A hidden member in the batched set collapses to the uniform relation error (no leak) (rev6 #3)."""

    class GenreT(DjangoType):
        class Meta:
            model = library_models.Genre
            fields = ("id", "name")
            primary = True

        @classmethod
        def get_queryset(cls, queryset, info):
            return queryset.exclude(name="HiddenBatch")

    del GenreT
    visible = library_models.Genre.objects.create(name="VisibleBatch")
    hidden = library_models.Genre.objects.create(name="HiddenBatch")
    result, error = serializer_resolvers._decode_relation_multi(
        [visible.pk, hidden.pk],
        graphql_name="genreIds",
        related_model=library_models.Genre,
        info=None,
    )
    assert result is None
    assert error is not None
    assert error.field == "genreIds"


def test_relation_queryset_scope_skips_unregistered_raw_pk_relation():
    """A relation target without a registered primary type keeps the serializer queryset unchanged."""
    from django_strawberry_framework.utils.inputs import InputFieldSpec

    class BranchSer(serializers.Serializer):
        branch = serializers.PrimaryKeyRelatedField(queryset=library_models.Branch.objects.all())

    serializer = BranchSer()
    field = serializer.fields["branch"]
    original = field.queryset
    fake = type(
        "RawPkMut",
        (),
        {
            "_input_field_specs": [
                InputFieldSpec(
                    input_attr="branch",
                    graphql_name="branch",
                    target_name="branch",
                    kind=serializer_resolvers.RELATION_SINGLE,
                    related_model=library_models.Branch,
                ),
            ],
        },
    )
    serializer_resolvers._scope_relation_querysets_to_visibility(fake, serializer, info=None)
    assert field.queryset is original


def test_relation_queryset_scope_handles_many_related_field():
    """Many relation fields scope their child relation queryset through target visibility (#3)."""
    from django_strawberry_framework.utils.inputs import InputFieldSpec

    class BranchT(DjangoType):
        class Meta:
            model = library_models.Branch
            fields = ("id", "name")
            primary = True

        @classmethod
        def get_queryset(cls, queryset, info):
            return queryset.exclude(name="HiddenScope")

    class BranchesSer(serializers.Serializer):
        branches = serializers.PrimaryKeyRelatedField(
            many=True,
            queryset=library_models.Branch.objects.all(),
        )

    del BranchT
    serializer = BranchesSer()
    field = serializer.fields["branches"]
    fake = type(
        "ManyMut",
        (),
        {
            "_input_field_specs": [
                InputFieldSpec(
                    input_attr="branches",
                    graphql_name="branches",
                    target_name="branches",
                    kind=serializer_resolvers.RELATION_MULTI,
                    related_model=library_models.Branch,
                ),
            ],
        },
    )
    serializer_resolvers._scope_relation_querysets_to_visibility(fake, serializer, info=None)
    assert field.child_relation.queryset.query.where


# ===========================================================================
# get_serializer_save_kwargs shadow guard (spec-039 rev6 #12)
# ===========================================================================


def test_save_kwargs_shadowing_input_field_raises():
    """A save kwarg whose name matches a serializer INPUT field fails loud (would clobber input) (rev6 #12)."""
    from django_strawberry_framework.utils.inputs import InputFieldSpec

    fake = type(
        "M",
        (),
        {
            "_input_field_specs": [
                InputFieldSpec(
                    input_attr="code",
                    graphql_name="code",
                    target_name="code",
                    kind=SCALAR,
                ),
            ],
        },
    )
    with pytest.raises(ConfigurationError, match="shadow serializer input field"):
        serializer_resolvers._assert_save_kwargs_no_shadow(fake, {"code": "clobber"})


def test_save_kwargs_not_shadowing_input_field_is_allowed():
    """A save kwarg NOT matching an input field (server-side data) is allowed (rev6 #12)."""
    from django_strawberry_framework.utils.inputs import InputFieldSpec

    fake = type(
        "M",
        (),
        {
            "_input_field_specs": [
                InputFieldSpec(
                    input_attr="code",
                    graphql_name="code",
                    target_name="code",
                    kind=SCALAR,
                ),
            ],
        },
    )
    # No raise: `owner` is server-side data, not a serializer input field.
    serializer_resolvers._assert_save_kwargs_no_shadow(fake, {"owner": object()})


@pytest.mark.django_db
def test_relation_queryset_scope_composes_with_author_queryset():
    """Visibility scoping AND-s the author's field queryset - never replaces it (rev6 rev2 P1).

    A serializer author's own ``PrimaryKeyRelatedField(queryset=...)`` restriction is the base
    contract; visibility is an ADDITIONAL constraint. A visible-but-author-DISALLOWED row must
    still be rejected (the earlier reassignment erased the author's queryset and admitted it).
    """
    from django_strawberry_framework.utils.inputs import InputFieldSpec

    class BranchT(DjangoType):
        class Meta:
            model = library_models.Branch
            fields = ("id", "name")
            primary = True  # default get_queryset: every branch is visible

    del BranchT
    allowed = library_models.Branch.objects.create(name="ScopeAllowed", city="allowed")
    other = library_models.Branch.objects.create(name="ScopeOther", city="other")

    class SingleSer(serializers.Serializer):
        branch = serializers.PrimaryKeyRelatedField(
            queryset=library_models.Branch.objects.filter(city="allowed"),
        )

    class ManySer(serializers.Serializer):
        branches = serializers.PrimaryKeyRelatedField(
            many=True,
            queryset=library_models.Branch.objects.filter(city="allowed"),
        )

    single = SingleSer()
    serializer_resolvers._scope_relation_querysets_to_visibility(
        type(
            "SingleMut",
            (),
            {
                "_input_field_specs": [
                    InputFieldSpec(
                        input_attr="branch",
                        graphql_name="branch",
                        target_name="branch",
                        kind=serializer_resolvers.RELATION_SINGLE,
                        related_model=library_models.Branch,
                    ),
                ],
            },
        ),
        single,
        info=None,
    )
    single_qs = single.fields["branch"].queryset
    assert allowed in single_qs  # visible AND author-allowed
    assert other not in single_qs  # visible but author-DISALLOWED - the author's filter survives

    many = ManySer()
    serializer_resolvers._scope_relation_querysets_to_visibility(
        type(
            "ManyMut",
            (),
            {
                "_input_field_specs": [
                    InputFieldSpec(
                        input_attr="branches",
                        graphql_name="branches",
                        target_name="branches",
                        kind=serializer_resolvers.RELATION_MULTI,
                        related_model=library_models.Branch,
                    ),
                ],
            },
        ),
        many,
        info=None,
    )
    many_qs = many.fields["branches"].child_relation.queryset
    assert allowed in many_qs
    assert other not in many_qs


# ===========================================================================
# Nested serializer inputs - decode + agreement internals (spec-039 rev6 #17)
# ===========================================================================


def _nested_single_input_and_specs():
    """Build a single-nested input (``detail`` -> ``{code}``) + its top reverse-map specs."""
    from django_strawberry_framework.rest_framework.inputs import (
        NestedSerializerConfig,
        build_serializer_input_class,
    )

    class Child(serializers.Serializer):
        code = serializers.CharField()

    class Parent(serializers.Serializer):
        detail = Child()

    cls, shape = build_serializer_input_class(
        Parent,
        operation_kind="create",
        nested_configs={"detail": NestedSerializerConfig()},
    )
    return cls, list(shape.field_specs)


def _nested_child_input_cls(top_cls):
    """Return the nested input class referenced by the top input's ``detail`` field."""
    field = next(f for f in top_cls.__strawberry_definition__.fields if f.python_name == "detail")
    return getattr(field.type, "of_type", field.type)


def test_decode_nested_single_recurses_into_child():
    """A single nested input decodes recursively into a nested serializer-keyed dict (rev6 #17)."""
    top_cls, specs = _nested_single_input_and_specs()
    child_cls = _nested_child_input_cls(top_cls)
    data = top_cls(detail=child_cls(code="X"))
    provided, error = serializer_resolvers._decode_input_object(specs, data, info=None)
    assert error is None
    assert provided == {"detail": {"code": "X"}}


def test_decode_nested_explicit_none_passes_through():
    """An explicit ``null`` nested value passes through unchanged (the serializer's validation decides) (rev6 #17)."""
    top_cls, specs = _nested_single_input_and_specs()
    data = top_cls(detail=None)
    provided, error = serializer_resolvers._decode_input_object(specs, data, info=None)
    assert error is None
    assert provided == {"detail": None}


def _nested_agreement_fake(**spec_overrides):
    """Build a fake mutation carrying ONE nested ``InputFieldSpec`` (with nested_specs)."""
    from django_strawberry_framework.utils.inputs import InputFieldSpec

    child_specs = spec_overrides.pop(
        "nested_specs",
        (
            InputFieldSpec(
                input_attr="code",
                graphql_name="code",
                target_name="code",
                kind=SCALAR,
            ),
        ),
    )
    base = {
        "input_attr": "detail",
        "graphql_name": "detail",
        "target_name": "detail",
        "kind": NESTED_SINGLE,
        "nested_specs": child_specs,
    }
    base.update(spec_overrides)
    return type("FakeMut", (), {"_input_field_specs": [InputFieldSpec(**base)]})


def _child_single_serializer():
    class Child(serializers.Serializer):
        code = serializers.CharField()

    class ParentSingle(serializers.Serializer):
        detail = Child()

    return ParentSingle(data={})


def _child_many_serializer():
    class Child(serializers.Serializer):
        code = serializers.CharField()

    class ParentMany(serializers.Serializer):
        detail = Child(many=True)

    return ParentMany(data={})


def test_nested_agreement_multi_spec_over_single_runtime_raises():
    """A schema nested-MULTI field that is a single serializer at runtime fails loud (rev6 #17)."""
    fake = _nested_agreement_fake(kind=NESTED_MULTI)
    with pytest.raises(ConfigurationError, match="nested list of serializers"):
        serializer_resolvers._assert_schema_runtime_agreement(fake, _child_single_serializer())


def test_nested_agreement_single_spec_over_many_runtime_raises():
    """A schema nested-SINGLE field that is a ``ListSerializer`` at runtime fails loud (rev6 #17)."""
    fake = _nested_agreement_fake(kind=NESTED_SINGLE)
    with pytest.raises(ConfigurationError, match="nested serializer"):
        serializer_resolvers._assert_schema_runtime_agreement(fake, _child_many_serializer())


def test_nested_agreement_recurses_into_child_specs():
    """A nested field's child spec is held to the SAME agreement contract (recursion) (rev6 #17)."""
    from django_strawberry_framework.utils.inputs import InputFieldSpec

    ghost_child = (
        InputFieldSpec(
            input_attr="ghost",
            graphql_name="ghost",
            target_name="ghost",
            kind=SCALAR,
        ),
    )
    fake = _nested_agreement_fake(nested_specs=ghost_child)
    # The runtime nested ``Child`` declares ``code``, not ``ghost``.
    with pytest.raises(ConfigurationError, match="does not declare it"):
        serializer_resolvers._assert_schema_runtime_agreement(fake, _child_single_serializer())


def test_agreement_scalar_field_that_became_nested_serializer_raises():
    """A schema SCALAR field that is a nested serializer at runtime fails loud (the kind moved) (rev6 #17)."""
    from django_strawberry_framework.utils.inputs import InputFieldSpec

    class Child(serializers.Serializer):
        x = serializers.CharField()

    class Runtime(serializers.Serializer):
        detail = Child()

    fake = type(
        "M",
        (),
        {
            "_input_field_specs": [
                InputFieldSpec(
                    input_attr="detail",
                    graphql_name="detail",
                    target_name="detail",
                    kind=SCALAR,
                ),
            ],
        },
    )
    with pytest.raises(ConfigurationError, match="nested serializer"):
        serializer_resolvers._assert_schema_runtime_agreement(fake, Runtime(data={}))


def test_decode_nested_single_error_short_circuits():
    """A decode error INSIDE a single nested input short-circuits with the nested error (rev6 #17)."""
    top_cls, specs = _nested_single_input_and_specs()
    child_cls = _nested_child_input_cls(top_cls)
    # A lone surrogate in the nested scalar trips the invalid-Unicode preflight inside the
    # nested decode, so the single-nested branch returns the error (keyed to the full path).
    data = top_cls(detail=child_cls(code="\ud800"))
    provided, error = serializer_resolvers._decode_input_object(specs, data, info=None)
    assert provided == {}
    assert error is not None
    assert error.field == "detail.code"
