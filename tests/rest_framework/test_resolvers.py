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
    """The leaf path's ROOT segment is re-keyed through the reverse map (F5); children verbatim."""
    reverse_map = {"category": "categoryId"}
    errors = {"category": ["bad relation"], "items": [{"category": ["nested"]}]}
    flat = serializer_resolvers.serializer_errors_to_field_errors(errors, reverse_map)
    by_path = {fe.field: fe.messages for fe in flat}
    # Root `category` re-keyed to `categoryId`; the nested `items.0.category` keeps
    # its child segment verbatim (only the ROOT `items` would re-key, and it has no
    # reverse-map entry, so it stays `items`).
    assert by_path == {"categoryId": ["bad relation"], "items.0.category": ["nested"]}


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
