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
from rest_framework.validators import UniqueTogetherValidator, UniqueValidator
from strawberry import relay

from django_strawberry_framework import (
    DjangoMutationField,
    DjangoSchema,
    DjangoType,
    SerializerMutation,
    finalize_django_types,
)
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.mutations.inputs import NON_FIELD_ERROR_KEY
from django_strawberry_framework.registry import registry
from django_strawberry_framework.rest_framework import resolvers as serializer_resolvers
from django_strawberry_framework.rest_framework.hook_context import (
    SerializerHookContext,
    UploadMetadata,
)
from django_strawberry_framework.rest_framework.serializer_converter import (
    NESTED_MULTI,
    NESTED_SINGLE,
    SCALAR,
)
from django_strawberry_framework.testing.relay import global_id_for
from django_strawberry_framework.utils.querysets import SyncMisuseError
from django_strawberry_framework.utils.write_transaction import (
    managed_write_transaction,
    write_pipeline,
)


def _hook_ctx(operation="create", alias="default", instance_pk=None):
    """A frozen hook context for direct-call tests (the shape the pipeline builds)."""
    return SerializerHookContext(
        operation=operation,
        write_alias=alias,
        instance_pk=instance_pk,
    )


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
    reverse_map = serializer_resolvers._build_reverse_map(top_specs)
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
    reverse_map = serializer_resolvers._build_reverse_map(top_specs)
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
    DjangoSchema(query=Query, mutation=Mutation)
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
    # The write-pipeline context stands in for the shared skeleton the direct call bypasses.
    with write_pipeline("default", lock=False):
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

    with write_pipeline("default", lock=False):
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

    with write_pipeline("default", lock=False):
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

    with write_pipeline("default", lock=False):
        result = serializer_resolvers._serializer_write_step(
            mutation_cls,
            info,
            None,
            {"name": "OK", "category": category.pk},
        )
    assert isinstance(result, list)
    assert [fe.field for fe in result] == [NON_FIELD_ERROR_KEY]


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

    # The managed-transaction context stands in for the DjangoSchema execution
    # the direct resolver call bypasses.
    with managed_write_transaction("default"):
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
        final_data={"name": "X"},
        instance=None,
        alias="default",
        hook_context=_hook_ctx(),
    )
    assert "partial" not in create_kwargs

    instance = SimpleNamespace(pk=1)
    update_kwargs = serializer_resolvers._merged_serializer_kwargs(
        mutation_cls,
        info,
        final_data={"name": "X"},
        instance=instance,
        alias="default",
        hook_context=_hook_ctx(),
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
        final_data={"name": "X"},
        instance=None,
        alias="default",
        hook_context=_hook_ctx(),
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
            hook_context,
        ):
            kwargs = super().get_serializer_kwargs(info, data=data, hook_context=hook_context)
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
    DjangoSchema(query=Query, mutation=Mutation)
    del CategoryT, ItemT

    request = HttpRequest()
    request.user = SimpleNamespace(username="u", is_authenticated=True)
    info = SimpleNamespace(context=SimpleNamespace(request=request))
    kwargs = serializer_resolvers._merged_serializer_kwargs(
        OverridingMutation,
        info,
        final_data={"name": "X"},
        instance=None,
        alias="default",
        hook_context=_hook_ctx(),
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
            hook_context,
        ):
            kwargs = super().get_serializer_kwargs(info, data=data, hook_context=hook_context)
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
    DjangoSchema(query=Query, mutation=Mutation)
    del CategoryT, ItemT

    request = HttpRequest()
    request.user = SimpleNamespace(username="u", is_authenticated=True)
    info = SimpleNamespace(context=SimpleNamespace(request=request))
    with pytest.raises(ConfigurationError, match="partial"):
        serializer_resolvers._merged_serializer_kwargs(
            PartialReturningMutation,
            info,
            final_data={"name": "X"},
            instance=SimpleNamespace(pk=1),
            alias="default",
            hook_context=_hook_ctx(),
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
            hook_context,
        ):
            kwargs = super().get_serializer_kwargs(info, data=data, hook_context=hook_context)
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
    DjangoSchema(query=Query, mutation=Mutation)
    del CategoryT, ItemT

    request = HttpRequest()
    request.user = SimpleNamespace(username="u", is_authenticated=True)
    info = SimpleNamespace(context=SimpleNamespace(request=request))
    with pytest.raises(ConfigurationError, match="request"):
        serializer_resolvers._merged_serializer_kwargs(
            WrongRequestMutation,
            info,
            final_data={"name": "X"},
            instance=None,
            alias="default",
            hook_context=_hook_ctx(),
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
        final_data={"name": "X"},
        instance=None,
        alias="default",
        hook_context=_hook_ctx(),
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
    DjangoSchema(query=Query, mutation=Mutation)
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

    # The managed-transaction context stands in for the DjangoSchema execution the
    # direct seam call bypasses (it propagates into the sync_to_async worker).
    with managed_write_transaction("default"):
        payload = await CreateItemAsync.resolve_async(info, data=data, id=None)
    assert payload.errors == []
    assert payload.node is not None
    assert payload.node.name == "AsyncItem"


@pytest.mark.django_db(transaction=True)
async def test_async_entry_rejects_data_rewriting_hook_too():
    """The hardened reserved-kwarg checks fire through the ASYNC entry point as well.

    The async surface runs the SAME sync body under one ``sync_to_async`` worker, so a
    ``get_serializer_kwargs`` override rewriting ``data`` is the same ``ConfigurationError``
    there - the hardening cannot be dodged by choosing the async resolver.
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

    class RewritingItemSerializer(serializers.ModelSerializer):
        class Meta:
            model = product_models.Item
            fields = ("name", "category")

    class CreateItemRewriting(SerializerMutation):
        class Meta:
            serializer_class = RewritingItemSerializer
            operation = "create"
            permission_classes = [_AllowAll]

        def get_serializer_kwargs(
            self,
            info,
            *,
            data,
            hook_context,
        ):
            return {"data": {**data, "smuggled": "value"}}

    @strawberry.type
    class Query:
        @strawberry.field
        def ping(self) -> int:
            return 1

    @strawberry.type
    class Mutation:
        write_item = DjangoMutationField(CreateItemRewriting)

    finalize_django_types()
    DjangoSchema(query=Query, mutation=Mutation)
    del CategoryT, ItemT

    from asgiref.sync import sync_to_async

    category = await sync_to_async(product_models.Category.objects.create)(name="AsyncRewriteCat")
    gid = relay.GlobalID(type_name="products.category", node_id=str(category.pk))

    @strawberry.input
    class _Data:
        name: str
        category_id: strawberry.ID = strawberry.field(name="categoryId")

    request = HttpRequest()
    request.user = SimpleNamespace(username="async-u", is_authenticated=True)
    info = SimpleNamespace(context=SimpleNamespace(request=request))
    data = _Data(name="AsyncRewriteItem", category_id=gid)

    with managed_write_transaction("default"):
        with pytest.raises(ConfigurationError, match="not the exact object the hook received"):
            await CreateItemRewriting.resolve_async(info, data=data, id=None)
    # The refused write never happened.
    exists = await sync_to_async(
        product_models.Item.objects.filter(name="AsyncRewriteItem").exists,
    )()
    assert exists is False


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
    return type(
        "FakeMut",
        (),
        {"_input_field_specs": [InputFieldSpec(**base)], "_injected_field_specs": []},
    )


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
            "_injected_field_specs": [],
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
            "_input_field_specs": [],
            "_injected_field_specs": [topic_spec] if specs is None else specs,
        },
    )


def test_declared_injected_field_dropped_by_runtime_serializer_raises():
    """An injected field the RUNTIME serializer does not declare fails loud (rev6 rev2 P1 - not just presence)."""
    # ``_shelf_model_serializer`` has NO ``topic``; the write-surface agreement check catches
    # it even though the framework-built data would carry the key.
    serializer = _shelf_model_serializer()
    with pytest.raises(ConfigurationError, match="does not declare it"):
        serializer_resolvers._assert_schema_runtime_agreement(_injected_topic_mut(), serializer)


def test_supplied_injected_field_passes_runtime_check():
    """A declared injected field the runtime serializer accepts passes (rev6 #2 happy path)."""
    serializer = _topic_shelf_serializer_class()(
        data={"code": "X", "branch": 1, "topic": "supplied"},
    )
    # No raise: ``topic`` is a writable runtime field on the write surface.
    serializer_resolvers._assert_schema_runtime_agreement(_injected_topic_mut(), serializer)


def test_write_surface_agreement_with_no_injected_fields_walks_input_only():
    """A mutation with an empty injected surface still agrees on its GraphQL input specs."""
    serializer_resolvers._assert_schema_runtime_agreement(
        _agreement_specs(),
        _shelf_model_serializer(),
    )  # no raise


def _hookable_injected_mut(injected_fields, hook_return):
    """A fake mutation whose ``get_serializer_injected_data`` returns ``hook_return``."""

    class FakeInjectMut:
        _mutation_meta = SimpleNamespace(injected_fields=injected_fields)

        def get_serializer_injected_data(
            self,
            info,
            *,
            data,
            hook_context,
        ):
            # The received view is FROZEN: mutation is structurally impossible.
            with pytest.raises(TypeError):
                data["smuggled"] = True
            return hook_return

    return FakeInjectMut


def test_injected_data_hook_missing_declared_key_raises():
    """``get_serializer_injected_data`` omitting a declared injected field fails loud (hardened)."""
    fake = _hookable_injected_mut(("topic",), {})
    with pytest.raises(ConfigurationError, match="EXACTLY the declared injected fields"):
        serializer_resolvers._injected_serializer_data(
            fake,
            info=None,
            frozen_provided=serializer_resolvers._frozen_hook_view({"code": "X"}),
            hook_context=_hook_ctx(),
        )


def test_injected_data_hook_undeclared_extra_key_raises():
    """``get_serializer_injected_data`` returning an UNDECLARED key fails loud (hardened)."""
    fake = _hookable_injected_mut(None, {"topic": "smuggle"})
    with pytest.raises(ConfigurationError, match="EXACTLY the declared injected fields"):
        serializer_resolvers._injected_serializer_data(
            fake,
            info=None,
            frozen_provided=serializer_resolvers._frozen_hook_view({"code": "X"}),
            hook_context=_hook_ctx(),
        )


def test_injected_data_hook_exact_match_returns_and_cannot_mutate_client_data():
    """An exact-match injection returns the values; the hook's data view is immutable."""
    fake = _hookable_injected_mut(("topic",), {"topic": "stamped"})
    provided = {"code": "X"}
    injected = serializer_resolvers._injected_serializer_data(
        fake,
        info=None,
        frozen_provided=serializer_resolvers._frozen_hook_view(provided),
        hook_context=_hook_ctx(),
    )
    assert injected == {"topic": "stamped"}
    # The hook only ever saw the frozen view: the authoritative data is untouched.
    assert provided == {"code": "X"}


def test_injected_data_hook_cannot_mutate_nested_client_containers():
    """The hook's data view is RECURSIVELY frozen: nested mutation attempts raise TypeError."""

    class NestedMutatingMut:
        _mutation_meta = SimpleNamespace(injected_fields=("topic",))

        def get_serializer_injected_data(
            self,
            info,
            *,
            data,
            hook_context,
        ):
            # A nested list is a tuple and a nested dict a MappingProxyType: the
            # in-place mutations a mutable clone merely ISOLATED are now
            # structurally impossible.
            with pytest.raises(AttributeError):
                data["genre_ids"].append(999)
            with pytest.raises(TypeError):
                data["detail"]["code"] = "evil"
            return {"topic": "stamped"}

    provided = {"genre_ids": [1, 2], "detail": {"code": "ok"}}
    injected = serializer_resolvers._injected_serializer_data(
        NestedMutatingMut,
        info=None,
        frozen_provided=serializer_resolvers._frozen_hook_view(provided),
        hook_context=_hook_ctx(),
    )
    assert injected == {"topic": "stamped"}
    assert provided == {"genre_ids": [1, 2], "detail": {"code": "ok"}}


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


def test_relation_queryset_scope_pins_unregistered_raw_pk_relation_without_visibility():
    """A relation target without a registered primary gets NO visibility filter but IS still pinned.

    A raw-pk relation has no visibility contract to AND on, but DRF's own ``is_valid()``
    lookup must still run inside the transaction on the write alias (the hardening pass), so
    the author's queryset is alias-pinned rather than left untouched.
    """
    from django_strawberry_framework.utils.inputs import InputFieldSpec

    class BranchSer(serializers.Serializer):
        branch = serializers.PrimaryKeyRelatedField(queryset=library_models.Branch.objects.all())

    serializer = BranchSer()
    field = serializer.fields["branch"]
    fake = type(
        "RawPkMut",
        (),
        {
            "_injected_field_specs": [],
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
    with write_pipeline("default", lock=False):
        serializer_resolvers._scope_relation_querysets_to_visibility(fake, serializer, info=None)
    # Pinned to the write alias; no visibility constraint added (no primary type registered).
    assert field.queryset._db == "default"
    assert not field.queryset.query.where
    assert field.queryset.query.select_for_update is False


def test_relation_queryset_scope_locks_when_pipeline_locks():
    """When the pipeline locks, the scoped relation queryset is a base-manager FOR UPDATE query."""
    from django_strawberry_framework.utils.inputs import InputFieldSpec

    class BranchSer(serializers.Serializer):
        branch = serializers.PrimaryKeyRelatedField(queryset=library_models.Branch.objects.all())

    serializer = BranchSer()
    fake = type(
        "LockMut",
        (),
        {
            "_injected_field_specs": [],
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
    with write_pipeline("default", lock=True):
        serializer_resolvers._scope_relation_querysets_to_visibility(fake, serializer, info=None)
    scoped = serializer.fields["branch"].queryset
    assert scoped.query.select_for_update is True
    assert scoped._db == "default"


@pytest.mark.django_db
def test_relation_queryset_scope_covers_injected_relation_specs():
    """A ``Meta.injected_fields`` relation gets the SAME pin + visibility + lock as an input relation.

    Injected relation values reach DRF's identical second lookup, so skipping their specs
    would leave an unpinned, unlocked, visibility-free queryset - the specs walk must cover
    the disjoint union of ``_input_field_specs`` and ``_injected_field_specs``. The
    visibility half is asserted by MEMBERSHIP (a row the registered primary type hides must
    be absent from the scoped queryset), not just by queryset flags.
    """
    from django_strawberry_framework.utils.inputs import InputFieldSpec

    class BranchT(DjangoType):
        class Meta:
            model = library_models.Branch
            fields = ("id", "name")
            primary = True

        @classmethod
        def get_queryset(cls, queryset, info):
            return queryset.exclude(name="HiddenInjected")

    del BranchT
    visible = library_models.Branch.objects.create(name="VisibleInjected", city="c")
    hidden = library_models.Branch.objects.create(name="HiddenInjected", city="c")

    class BranchSer(serializers.Serializer):
        branch = serializers.PrimaryKeyRelatedField(queryset=library_models.Branch.objects.all())

    def _fake():
        return type(
            "InjectedRelMut",
            (),
            {
                "_input_field_specs": [],
                "_injected_field_specs": [
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

    locked = BranchSer()
    with write_pipeline("default", lock=True):
        serializer_resolvers._scope_relation_querysets_to_visibility(_fake(), locked, info=None)
    scoped = locked.fields["branch"].queryset
    assert scoped._db == "default"
    assert scoped.query.select_for_update is True

    unlocked = BranchSer()
    with write_pipeline("default", lock=False):
        serializer_resolvers._scope_relation_querysets_to_visibility(_fake(), unlocked, info=None)
    visible_scoped = unlocked.fields["branch"].queryset
    assert visible in visible_scoped  # visibility-allowed row admitted
    assert hidden not in visible_scoped  # visibility-hidden row intersected OUT


def test_relation_queryset_scope_cross_alias_author_queryset_fails_closed():
    """An author queryset EXPLICITLY routed to a different alias fails before validation."""
    from django_strawberry_framework.utils.inputs import InputFieldSpec

    class BranchSer(serializers.Serializer):
        branch = serializers.PrimaryKeyRelatedField(
            queryset=library_models.Branch.objects.using("other").all(),
        )

    serializer = BranchSer()
    fake = type(
        "CrossAliasMut",
        (),
        {
            "_injected_field_specs": [],
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
    with (
        write_pipeline("default", lock=False),
        pytest.raises(ConfigurationError, match="routed to alias 'other'"),
    ):
        serializer_resolvers._scope_relation_querysets_to_visibility(fake, serializer, info=None)


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
            "_injected_field_specs": [],
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
    with write_pipeline("default", lock=False):
        serializer_resolvers._scope_relation_querysets_to_visibility(fake, serializer, info=None)
    assert field.child_relation.queryset.query.where


@pytest.mark.django_db
def test_relation_queryset_scope_is_isolated_between_concurrent_serializer_instances():
    """Concurrent requests scope instance-local single/many fields without cross-bleed (review P2).

    DRF deep-copies a serializer class's declared fields into each runtime serializer instance.
    Synchronizing both requests inside ``get_queryset`` forces their visibility rewrites to
    interleave, pinning that ``_scope_relation_querysets_to_visibility`` mutates only those
    instance-local copies and never the shared declarations or a sibling request's fields.
    """
    import threading
    from concurrent.futures import ThreadPoolExecutor

    from django_strawberry_framework.utils.inputs import InputFieldSpec

    scopes_met = threading.Barrier(2)

    class BranchT(DjangoType):
        class Meta:
            model = library_models.Branch
            fields = ("id", "name")
            primary = True

        @classmethod
        def get_queryset(cls, queryset, info):
            scopes_met.wait(timeout=5)
            return queryset.filter(city=info.context.request.visibility_city)

    class BranchSer(serializers.Serializer):
        branch = serializers.PrimaryKeyRelatedField(
            queryset=library_models.Branch.objects.all(),
        )
        branches = serializers.PrimaryKeyRelatedField(
            many=True,
            queryset=library_models.Branch.objects.all(),
        )

    del BranchT
    library_models.Branch.objects.create(name="ConcurrentLeft", city="left")
    library_models.Branch.objects.create(name="ConcurrentRight", city="right")
    specs = [
        InputFieldSpec(
            input_attr="branch",
            graphql_name="branch",
            target_name="branch",
            kind=serializer_resolvers.RELATION_SINGLE,
            related_model=library_models.Branch,
        ),
        InputFieldSpec(
            input_attr="branches",
            graphql_name="branches",
            target_name="branches",
            kind=serializer_resolvers.RELATION_MULTI,
            related_model=library_models.Branch,
        ),
    ]
    mutation = type(
        "ConcurrentMut",
        (),
        {"_input_field_specs": specs, "_injected_field_specs": []},
    )
    declared_single_queryset = BranchSer._declared_fields["branch"].queryset
    declared_many_queryset = BranchSer._declared_fields["branches"].child_relation.queryset

    def _scope_for(visibility_city):
        request = HttpRequest()
        request.visibility_city = visibility_city
        info = SimpleNamespace(context=SimpleNamespace(request=request))
        serializer = BranchSer()
        # The pipeline context is a ContextVar - set it INSIDE this worker thread.
        with write_pipeline("default", lock=False):
            serializer_resolvers._scope_relation_querysets_to_visibility(
                mutation,
                serializer,
                info,
            )
        return serializer

    with ThreadPoolExecutor(max_workers=2) as executor:
        left_future = executor.submit(_scope_for, "left")
        right_future = executor.submit(_scope_for, "right")
        left_serializer = left_future.result(timeout=10)
        right_serializer = right_future.result(timeout=10)

    left_single = left_serializer.fields["branch"]
    right_single = right_serializer.fields["branch"]
    left_many = left_serializer.fields["branches"].child_relation
    right_many = right_serializer.fields["branches"].child_relation

    assert left_single is not right_single
    assert left_many is not right_many
    assert list(left_single.queryset.values_list("name", flat=True)) == ["ConcurrentLeft"]
    assert list(left_many.queryset.values_list("name", flat=True)) == ["ConcurrentLeft"]
    assert list(right_single.queryset.values_list("name", flat=True)) == ["ConcurrentRight"]
    assert list(right_many.queryset.values_list("name", flat=True)) == ["ConcurrentRight"]
    assert BranchSer._declared_fields["branch"].queryset is declared_single_queryset
    assert BranchSer._declared_fields["branches"].child_relation.queryset is declared_many_queryset


# ===========================================================================
# get_serializer_save_kwargs shadow guard (spec-039 rev6 #12)
# ===========================================================================


def _validated_serializer(serializer_cls, data):
    """Construct + validate a serializer so ``validated_data`` is populated."""
    serializer = serializer_cls(data=data)
    assert serializer.is_valid(), serializer.errors
    return serializer


def test_save_kwargs_shadowing_validated_key_raises():
    """A save kwarg colliding with a ``validated_data`` key fails loud (would clobber it) (rev6 #12)."""

    class CodeSer(serializers.Serializer):
        code = serializers.CharField()

    fake = type("M", (), {})
    serializer = _validated_serializer(CodeSer, {"code": "X"})
    with pytest.raises(ConfigurationError, match="validated_data"):
        serializer_resolvers._assert_save_kwargs_no_shadow(fake, serializer, {"code": "clobber"})


def test_save_kwargs_not_shadowing_validated_key_is_allowed():
    """A save kwarg NOT in ``validated_data`` (server-side data) is allowed (rev6 #12)."""

    class CodeSer(serializers.Serializer):
        code = serializers.CharField()

    fake = type("M", (), {})
    serializer = _validated_serializer(CodeSer, {"code": "X"})
    # No raise: `owner` is server-side data, not a validated key.
    serializer_resolvers._assert_save_kwargs_no_shadow(fake, serializer, {"owner": object()})


def test_save_kwargs_shadowing_renamed_defaulted_and_hidden_keys_raises():
    """The check covers renamed (``source=``), defaulted, and ``HiddenField`` keys (hardened).

    ``validated_data`` is keyed by resolved ``source`` and includes keys the CLIENT never sent
    (a serializer default, a ``HiddenField``); comparing against the ACTUAL validated keys
    catches every collision the old input-spec reconstruction missed.
    """

    class RenamedSer(serializers.Serializer):
        display_name = serializers.CharField(source="name")
        topic = serializers.CharField(required=False, default="defaulted")
        owner = serializers.HiddenField(default="hidden-owner")

    fake = type("M", (), {})
    serializer = _validated_serializer(RenamedSer, {"display_name": "X"})
    with pytest.raises(ConfigurationError, match="'name'"):
        serializer_resolvers._assert_save_kwargs_no_shadow(fake, serializer, {"name": "clobber"})
    with pytest.raises(ConfigurationError, match="'topic'"):
        serializer_resolvers._assert_save_kwargs_no_shadow(fake, serializer, {"topic": "clobber"})
    with pytest.raises(ConfigurationError, match="'owner'"):
        serializer_resolvers._assert_save_kwargs_no_shadow(fake, serializer, {"owner": "clobber"})

    # The declared alias is not the key DRF places in validated_data.
    serializer_resolvers._assert_save_kwargs_no_shadow(fake, serializer, {"display_name": "ok"})


@pytest.mark.django_db
def test_save_kwargs_hook_cannot_mutate_validated_data_by_identity():
    """The save hook's ``data`` is a FROZEN view: an in-place JSON mutation is structurally
    impossible, so it can never reach ``serializer.validated_data`` (whose nested containers
    can share identity with the decoded client data)."""
    captured = {}

    class BlobItemSerializer(serializers.ModelSerializer):
        meta_blob = serializers.JSONField()

        class Meta:
            model = product_models.Item
            fields = ("name", "category", "meta_blob")

        def create(self, validated_data):
            captured["blob"] = validated_data.pop("meta_blob")
            return super().create(validated_data)

    def mutating_save_kwargs(
        self,
        info,
        *,
        data,
        hook_context,
    ):
        # Before the freeze, these in-place mutations rewrote validated_data by identity;
        # the frozen view makes them raise instead of silently succeeding.
        with pytest.raises(TypeError):
            data["meta_blob"]["mode"] = "evil"
        with pytest.raises(AttributeError):
            data["meta_blob"]["tags"].append("evil")
        return {}

    mutation_cls = _bind_item_serializer_mutation(BlobItemSerializer)
    mutation_cls.get_serializer_save_kwargs = mutating_save_kwargs
    category = product_models.Category.objects.create(name="BlobCat")
    request = HttpRequest()
    request.user = SimpleNamespace(username="u", is_authenticated=True)
    info = SimpleNamespace(context=SimpleNamespace(request=request))

    provided = {
        "name": "BlobItem",
        "category": category.pk,
        "meta_blob": {"mode": "ok", "tags": ["a"]},
    }
    with write_pipeline("default", lock=False):
        saved = serializer_resolvers._serializer_write_step(mutation_cls, info, None, provided)
    assert isinstance(saved, product_models.Item)
    assert captured["blob"] == {"mode": "ok", "tags": ["a"]}  # the validated value survived
    assert provided["meta_blob"] == {"mode": "ok", "tags": ["a"]}  # and the decoded data too


@pytest.mark.django_db
def test_save_kwargs_hook_validation_error_maps_to_field_error_envelope():
    """A DRF ``ValidationError`` raised BY the save-kwargs hook rides the documented mapping.

    The hook is invoked INSIDE the value-preserving, error-mapped closure - the same
    boundary as ``serializer.save()`` - so a hook-raised validation failure lands in the
    ``FieldError`` envelope, never as a top-level ``GraphQLError``.
    """

    class PlainItemSerializer(serializers.ModelSerializer):
        class Meta:
            model = product_models.Item
            fields = ("name", "category")

    def raising_save_kwargs(
        self,
        info,
        *,
        data,
        hook_context,
    ):
        raise serializers.ValidationError({"name": ["from the save-kwargs hook"]})

    mutation_cls = _bind_item_serializer_mutation(PlainItemSerializer)
    mutation_cls.get_serializer_save_kwargs = raising_save_kwargs
    category = product_models.Category.objects.create(name="HookErrCat")
    request = HttpRequest()
    request.user = SimpleNamespace(username="u", is_authenticated=True)
    info = SimpleNamespace(context=SimpleNamespace(request=request))

    with write_pipeline("default", lock=False):
        result = serializer_resolvers._serializer_write_step(
            mutation_cls,
            info,
            None,
            {"name": "OK", "category": category.pk},
        )
    assert isinstance(result, list)
    assert [(fe.field, fe.messages) for fe in result] == [
        ("name", ["from the save-kwargs hook"]),
    ]


# ===========================================================================
# Framework-owned serializer kwargs + saved-result validation (hardening)
# ===========================================================================


def _reserved_kwarg_mutation(hook):
    """Bind an Item serializer mutation whose ``get_serializer_kwargs`` is ``hook``."""

    class ReservedSer(serializers.ModelSerializer):
        class Meta:
            model = product_models.Item
            fields = ("name", "category")

    class ReservedMutation(SerializerMutation):
        class Meta:
            serializer_class = ReservedSer
            operation = "create"

        get_serializer_kwargs = hook

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
        write_item = DjangoMutationField(ReservedMutation)

    finalize_django_types()
    DjangoSchema(query=Query, mutation=Mutation)
    del CategoryT, ItemT
    return ReservedMutation


def _info_with_request():
    request = HttpRequest()
    request.user = SimpleNamespace(username="u", is_authenticated=True)
    return SimpleNamespace(context=SimpleNamespace(request=request))


@pytest.mark.django_db
def test_merged_kwargs_hook_rewriting_data_is_configuration_error():
    """A ``get_serializer_kwargs`` returning a DIFFERENT ``data`` fails loud (data is framework-owned)."""

    def hook(
        self,
        info,
        *,
        data,
        hook_context,
    ):
        return {"data": {**data, "smuggled": "value"}}

    mutation_cls = _reserved_kwarg_mutation(hook)
    with pytest.raises(ConfigurationError, match="not the exact object the hook received"):
        serializer_resolvers._merged_serializer_kwargs(
            mutation_cls,
            _info_with_request(),
            final_data={"name": "X"},
            instance=None,
            alias="default",
            hook_context=_hook_ctx(),
        )


@pytest.mark.django_db
def test_merged_kwargs_hook_equal_data_is_tolerated():
    """A hook returning the (unmodified) data copy is tolerated (the default's pass-through)."""

    def hook(
        self,
        info,
        *,
        data,
        hook_context,
    ):
        return {"data": data}

    mutation_cls = _reserved_kwarg_mutation(hook)
    kwargs = serializer_resolvers._merged_serializer_kwargs(
        mutation_cls,
        _info_with_request(),
        final_data={"name": "X"},
        instance=None,
        alias="default",
        hook_context=_hook_ctx(),
    )
    assert kwargs["data"] == {"name": "X"}


@pytest.mark.django_db
def test_merged_kwargs_hook_substituting_instance_is_configuration_error():
    """A hook returning a DIFFERENT ``instance`` than the located row fails loud (the bypass)."""
    substituted = SimpleNamespace(pk=999)

    def hook(
        self,
        info,
        *,
        data,
        hook_context,
    ):
        return {"data": data, "instance": substituted}

    mutation_cls = _reserved_kwarg_mutation(hook)
    with pytest.raises(ConfigurationError, match="`instance` kwarg"):
        serializer_resolvers._merged_serializer_kwargs(
            mutation_cls,
            _info_with_request(),
            final_data={"name": "X"},
            instance=SimpleNamespace(pk=1),
            alias="default",
            hook_context=_hook_ctx(),
        )


@pytest.mark.django_db
def test_merged_kwargs_hook_conflicting_write_alias_is_configuration_error():
    """A hook setting a conflicting ``context['write_alias']`` fails loud (alias is framework-owned)."""

    def hook(
        self,
        info,
        *,
        data,
        hook_context,
    ):
        return {"data": data, "context": {"write_alias": "other"}}

    mutation_cls = _reserved_kwarg_mutation(hook)
    with pytest.raises(ConfigurationError, match="write_alias"):
        serializer_resolvers._merged_serializer_kwargs(
            mutation_cls,
            _info_with_request(),
            final_data={"name": "X"},
            instance=None,
            alias="default",
            hook_context=_hook_ctx(),
        )


@pytest.mark.django_db
def test_merged_kwargs_sets_write_alias_in_context():
    """The framework sets ``context['write_alias']`` to the pipeline's pinned alias."""
    mutation_cls = _bind_item_serializer_mutation(_basic_item_serializer())
    kwargs = serializer_resolvers._merged_serializer_kwargs(
        mutation_cls,
        _info_with_request(),
        final_data={"name": "X"},
        instance=None,
        alias="default",
        hook_context=_hook_ctx(),
    )
    assert kwargs["context"]["write_alias"] == "default"


@pytest.mark.django_db
def test_merged_kwargs_hook_cannot_mutate_nested_client_containers():
    """The constructor hook's data view is RECURSIVELY frozen: nested mutations raise."""

    def hook(
        self,
        info,
        *,
        data,
        hook_context,
    ):
        # A mutable copy merely ISOLATED these; the frozen view makes them impossible.
        with pytest.raises(AttributeError):
            data["genre_ids"].append(999)
        with pytest.raises(TypeError):
            data["detail"]["code"] = "evil"
        return {}

    mutation_cls = _reserved_kwarg_mutation(hook)
    final_data = {"name": "X", "genre_ids": [1, 2], "detail": {"code": "ok"}}
    kwargs = serializer_resolvers._merged_serializer_kwargs(
        mutation_cls,
        _info_with_request(),
        final_data=final_data,
        instance=None,
        alias="default",
        hook_context=_hook_ctx(),
    )
    assert kwargs["data"] == {"name": "X", "genre_ids": [1, 2], "detail": {"code": "ok"}}
    assert kwargs["data"] is final_data  # the authoritative structure, untouched


def test_merged_kwargs_hook_equal_but_not_identical_data_is_configuration_error():
    """An EQUAL data copy is rejected: the contract is identity with the received clone.

    Equality would require a deep comparison of two independently cloned structures
    (which recurses on deep valid payloads - an availability hole) and cannot prove the
    hook did not rebuild the structure; only omission or the exact received object passes.
    """

    def hook(
        self,
        info,
        *,
        data,
        hook_context,
    ):
        return {"data": dict(data)}

    mutation_cls = _reserved_kwarg_mutation(hook)
    with pytest.raises(ConfigurationError, match="not the exact object the hook received"):
        serializer_resolvers._merged_serializer_kwargs(
            mutation_cls,
            _info_with_request(),
            final_data={"name": "X"},
            instance=None,
            alias="default",
            hook_context=_hook_ctx(),
        )


def test_merged_kwargs_hook_explicit_none_data_is_configuration_error():
    """An explicit ``data=None`` return is NOT omission: the sentinel keeps it rejected."""

    def hook(
        self,
        info,
        *,
        data,
        hook_context,
    ):
        return {"data": None}

    mutation_cls = _reserved_kwarg_mutation(hook)
    with pytest.raises(ConfigurationError, match="not the exact object the hook received"):
        serializer_resolvers._merged_serializer_kwargs(
            mutation_cls,
            _info_with_request(),
            final_data={"name": "X"},
            instance=None,
            alias="default",
            hook_context=_hook_ctx(),
        )


@pytest.mark.django_db
def test_merged_kwargs_hook_explicit_none_instance_on_update_is_configuration_error():
    """On update, an explicit ``instance=None`` return is rejected (sentinel, not ``pop`` default)."""

    def hook(
        self,
        info,
        *,
        data,
        hook_context,
    ):
        return {"instance": None}

    mutation_cls = _reserved_kwarg_mutation(hook)
    category = product_models.Category.objects.create(name="SentinelCat")
    item = product_models.Item.objects.create(name="SentinelItem", category=category)
    with pytest.raises(ConfigurationError, match="`instance` kwarg"):
        serializer_resolvers._merged_serializer_kwargs(
            mutation_cls,
            _info_with_request(),
            final_data={"name": "X"},
            instance=item,
            alias="default",
            hook_context=_hook_ctx(),
        )


def test_merged_kwargs_deep_data_passthrough_never_recurses():
    """A pass-through hook over a deeper-than-recursion-limit payload must not crash.

    The old deep ``!=`` comparison of two independently cloned structures re-introduced
    the ``RecursionError`` the iterative clone had removed; the identity check is O(1).
    """
    import sys

    def hook(
        self,
        info,
        *,
        data,
        hook_context,
    ):
        return {"data": data}

    depth = sys.getrecursionlimit() + 200
    deep: list = []
    cursor = deep
    for _ in range(depth):
        child: list = []
        cursor.append(child)
        cursor = child

    mutation_cls = _reserved_kwarg_mutation(hook)
    final_data = {"name": "X", "blob": deep}
    kwargs = serializer_resolvers._merged_serializer_kwargs(
        mutation_cls,
        _info_with_request(),
        final_data=final_data,
        instance=None,
        alias="default",
        hook_context=_hook_ctx(),
    )
    assert kwargs["data"] is final_data


def test_frozen_hook_view_survives_json_depth_beyond_the_recursion_limit():
    """The freeze is ITERATIVE: a client-parseable deeply-nested JSON value must never crash
    the pipeline with a ``RecursionError`` (an availability hole a recursive walk had)."""
    import sys

    depth = sys.getrecursionlimit() + 200
    deep: list = []
    cursor = deep
    for _ in range(depth):
        child: list = []
        cursor.append(child)
        cursor = child
    cursor.append({"leaf": "ok"})

    view = serializer_resolvers._frozen_hook_view({"blob": deep})

    original, frozen = deep, view["blob"]
    for _ in range(depth):
        assert isinstance(frozen, tuple)  # an IMMUTABLE container at EVERY depth
        original, frozen = original[0], frozen[0]
    assert frozen == ({"leaf": "ok"},)
    assert dict(frozen[0]) == {"leaf": "ok"}

    # An immutable scalar top-level value passes through by reference (safe: unmutable).
    assert serializer_resolvers._frozen_hook_view("scalar") == "scalar"
    # An OPAQUE, possibly-mutable top-level leaf fails closed rather than aliasing it.
    with pytest.raises(ConfigurationError, match="cannot be frozen into an immutable"):
        serializer_resolvers._frozen_hook_view(object())


def test_frozen_hook_view_rejects_cycles_preserves_sharing_and_freezes_uploads():
    """A CYCLIC container fails loud; a shared (diamond) reference freezes once, stays shared;
    a file value becomes ``UploadMetadata`` (the authoritative upload never reaches a hook).

    Parsed GraphQL JSON can never cycle, but hook-generated data can; without the guard the
    iterative freeze would loop forever (an availability hole). A merely SHARED dict is
    legitimate and must not be misdiagnosed as a cycle.
    """
    from django.core.files.uploadedfile import SimpleUploadedFile

    cyclic: dict = {"k": "v"}
    cyclic["self"] = cyclic
    with pytest.raises(ConfigurationError, match="CYCLIC container"):
        serializer_resolvers._frozen_hook_view({"blob": cyclic})

    indirect: list = []
    indirect.append({"loop": indirect})
    with pytest.raises(ConfigurationError, match="CYCLIC container"):
        serializer_resolvers._frozen_hook_view({"blob": indirect})

    shared = {"code": "ok"}
    view = serializer_resolvers._frozen_hook_view({"a": shared, "b": shared})
    assert dict(view["a"]) == {"code": "ok"}
    assert view["a"] is view["b"]  # sharing preserved in the frozen view
    with pytest.raises(TypeError):
        view["a"]["code"] = "evil"  # and every level is read-only

    upload = SimpleUploadedFile("cover.png", b"12345", content_type="image/png")
    file_view = serializer_resolvers._frozen_hook_view({"cover": upload})
    metadata = file_view["cover"]
    assert isinstance(metadata, UploadMetadata)
    assert metadata.name == "cover.png"
    assert metadata.size == 5
    assert metadata.content_type == "image/png"


def test_frozen_hook_view_freezes_the_full_value_algebra_and_fails_closed_on_opaque_leaves():
    """The freeze covers tuples/sets/bytearray and rejects opaque mutable leaves (round-5 P2).

    A tuple / set is a mutable-reachable container (a tuple can carry a mutable member; a
    ``set`` itself is mutable), and a ``bytearray`` is a mutable scalar - all were passed to
    hooks BY REFERENCE before, so a hook could mutate them and thereby mutate the authoritative
    ``provided_data``. They are now rendered immutable; a leaf with no immutable rendering fails
    closed instead of being aliased under a false promise of immutability.
    """
    import datetime
    import decimal
    import uuid
    from types import MappingProxyType

    # A tuple carrying a mutable dict member: the tuple becomes a tuple, the dict a proxy.
    view = serializer_resolvers._frozen_hook_view({"pair": ("x", {"n": 1})})
    frozen_pair = view["pair"]
    assert isinstance(frozen_pair, tuple)
    assert isinstance(frozen_pair[1], MappingProxyType)
    with pytest.raises(TypeError):
        frozen_pair[1]["n"] = 2

    # A set becomes an immutable frozenset (the source set stays mutable and unshared).
    frozen_set = serializer_resolvers._frozen_hook_view({"tags": {"a", "b"}})["tags"]
    assert isinstance(frozen_set, frozenset)
    assert frozen_set == {"a", "b"}

    # A bytearray is rendered as immutable bytes (never aliased).
    frozen_bytes = serializer_resolvers._frozen_hook_view({"blob": bytearray(b"12")})["blob"]
    assert frozen_bytes == b"12"
    assert isinstance(frozen_bytes, bytes)

    # Genuinely-immutable scalars pass through by reference (safe, no false rejection).
    scalars = {
        "dt": datetime.datetime(2026, 7, 15, 12, 0, 0),
        "dec": decimal.Decimal("1.5"),
        "id": uuid.uuid4(),
        "n": 7,
        "flag": True,
        "nil": None,
    }
    scalar_view = serializer_resolvers._frozen_hook_view(scalars)
    for key, original in scalars.items():
        assert scalar_view[key] is original

    # An opaque, possibly-mutable leaf nested in the tree fails closed.
    with pytest.raises(ConfigurationError, match="cannot be frozen into an immutable"):
        serializer_resolvers._frozen_hook_view({"weird": object()})


def _saved_result_fixture():
    """A fake mutation + serializer name for the saved-result validation tests."""

    class FakeSer(serializers.Serializer):
        pass

    fake = type(
        "SavedMut",
        (),
        {"_mutation_meta": SimpleNamespace(model=product_models.Item)},
    )
    return fake, FakeSer()


@pytest.mark.django_db
def test_saved_result_wrong_model_is_configuration_error():
    """A ``save()`` returning a non-model / wrong-model value fails loud before the re-fetch."""
    fake, serializer = _saved_result_fixture()
    with pytest.raises(ConfigurationError, match="not a Item instance"):
        serializer_resolvers._checked_saved_result(fake, serializer, object(), None, "default", [])


@pytest.mark.django_db
def test_saved_result_unsaved_instance_is_configuration_error():
    """A ``save()`` returning an UNSAVED instance (pk None) fails loud."""
    fake, serializer = _saved_result_fixture()
    unsaved = product_models.Item(name="x")
    serializer.instance = unsaved  # DRF bookkeeping followed; the object is defective anyway
    with pytest.raises(ConfigurationError, match="returned an unsaved"):
        serializer_resolvers._checked_saved_result(fake, serializer, unsaved, None, "default", [])


@pytest.mark.django_db
def test_saved_result_spoofed_pk_on_never_persisted_instance_is_configuration_error():
    """A never-persisted instance carrying a SPOOFED pk fails loud (would launder an existing row)."""
    fake, serializer = _saved_result_fixture()
    category = product_models.Category.objects.create(name="SpoofCat")
    real = product_models.Item.objects.create(name="Real", category=category)
    spoofed = product_models.Item(pk=real.pk, name="Spoof")  # adding=True, _state.db=None
    serializer.instance = spoofed  # DRF bookkeeping followed; the object is defective anyway
    with pytest.raises(ConfigurationError, match="returned an unsaved"):
        serializer_resolvers._checked_saved_result(fake, serializer, spoofed, None, "default", [])


@pytest.mark.django_db
def test_saved_result_detached_saved_looking_instance_is_configuration_error():
    """A fabricated result whose per-attribute state LOOKS saved fails the identity check.

    Hand-setting ``_state.adding = False`` + ``_state.db = alias`` on a never-persisted
    instance defeats every per-attribute guard - but DRF's ``save()`` contract assigns the
    written row to ``serializer.instance``, so a detached return object that bypassed that
    bookkeeping fails closed on identity before it can launder the real row via the re-fetch.
    """
    fake, serializer = _saved_result_fixture()
    category = product_models.Category.objects.create(name="DetachedCat")
    real = product_models.Item.objects.create(name="RealRow", category=category)
    forged = product_models.Item(pk=real.pk, name="Forged")
    forged._state.adding = False
    forged._state.db = "default"
    # serializer.instance was never assigned (the save bookkeeping was bypassed).
    with pytest.raises(ConfigurationError, match="not serializer.instance"):
        serializer_resolvers._checked_saved_result(fake, serializer, forged, None, "default", [])


@pytest.mark.django_db
def test_saved_result_create_without_witnessed_insert_is_configuration_error():
    """A create result that was never OBSERVED being inserted fails loud (unforgeable).

    ``serializer.instance`` identity is forgeable through NORMAL DRF bookkeeping: a custom
    ``create()`` returning an existing row is still assigned to ``self.instance``. Only the
    ``post_save`` witness record proves the returned row was actually INSERTED on the pinned
    alias inside this save - an empty witness means an existing row was being laundered.
    """
    fake, serializer = _saved_result_fixture()
    category = product_models.Category.objects.create(name="LaunderCat")
    existing = product_models.Item.objects.create(name="PreExisting", category=category)
    serializer.instance = existing  # normal DRF save() bookkeeping - and still rejected
    with pytest.raises(ConfigurationError, match="never observed being INSERTED"):
        serializer_resolvers._checked_saved_result(
            fake,
            serializer,
            existing,
            None,
            "default",
            [],  # no witnessed insert of this row
        )
    # A witnessed UPDATE of the row (created=False) is not an insert either.
    with pytest.raises(ConfigurationError, match="never observed being INSERTED"):
        serializer_resolvers._checked_saved_result(
            fake,
            serializer,
            existing,
            None,
            "default",
            [
                (
                    existing,
                    existing.pk,
                    False,
                    "default",
                ),
            ],
        )


@pytest.mark.django_db
def test_saved_result_create_with_witnessed_insert_passes():
    """A create result matched by a witnessed ``created=True`` write on the pinned alias passes."""
    fake, serializer = _saved_result_fixture()
    category = product_models.Category.objects.create(name="WitnessCat")
    item = product_models.Item.objects.create(name="WitnessItem", category=category)
    serializer.instance = item
    written = [
        (
            item,
            item.pk,
            True,
            "default",
        ),
    ]
    assert (
        serializer_resolvers._checked_saved_result(
            fake,
            serializer,
            item,
            None,
            "default",
            written,
        )
        is item
    )


@pytest.mark.django_db
def test_saved_result_update_pk_mutation_is_configuration_error():
    """A custom update re-pointing the SAME object's pk at a hidden row fails the snapshot check.

    ``instance`` and ``saved`` can be the same mutable object, so a live ``instance.pk``
    comparison would compare the mutated pk to itself; the check runs against the
    authorized-pk SNAPSHOT captured before any consumer hook ran.
    """
    fake, serializer = _saved_result_fixture()
    category = product_models.Category.objects.create(name="SnapCat")
    authorized = product_models.Item.objects.create(name="AuthorizedRow", category=category)
    hidden = product_models.Item.objects.create(name="HiddenRow", category=category)
    authorized_pk = authorized.pk  # the immutable snapshot the pipeline captures pre-hooks
    authorized.pk = hidden.pk  # the in-place forgery: instance IS the returned object
    serializer.instance = authorized
    with pytest.raises(ConfigurationError, match="must write the row that was authorized"):
        serializer_resolvers._checked_saved_result(
            fake,
            serializer,
            authorized,
            authorized_pk,
            "default",
            [],
        )


@pytest.mark.django_db
def test_write_step_update_repointing_instance_pk_is_configuration_error():
    """End-to-end: an ``update()`` mutating ``instance.pk`` to a hidden row's pk fails loud."""
    hidden_holder = {}

    class RepointingSerializer(serializers.ModelSerializer):
        class Meta:
            model = product_models.Item
            fields = ("name", "category")

        def update(self, instance, validated_data):
            instance.pk = hidden_holder["pk"]  # re-point at the hidden row, save nothing
            return instance

    category = product_models.Category.objects.create(name="RepointCat")
    target = product_models.Item.objects.create(name="Target", category=category)
    hidden = product_models.Item.objects.create(name="Hidden", category=category)
    hidden_holder["pk"] = hidden.pk
    mutation_cls = _bind_item_serializer_mutation(RepointingSerializer, operation="update")
    request = HttpRequest()
    request.user = SimpleNamespace(username="u", is_authenticated=True)
    info = SimpleNamespace(context=SimpleNamespace(request=request))

    with write_pipeline("default", lock=False):
        with pytest.raises(ConfigurationError, match="must write the row that was authorized"):
            serializer_resolvers._serializer_write_step(
                mutation_cls,
                info,
                target,
                {"name": "Renamed"},
            )


@pytest.mark.django_db
def test_write_step_create_pk_mutated_after_insert_is_configuration_error():
    """A witnessed INSERT whose object is then re-pointed at a hidden row fails the pk snapshot.

    Object identity alone (``row is saved``) survives the mutation - both references see
    the mutated object - so the witness compares the pk SNAPSHOTTED at ``post_save``.
    """
    hidden_holder = {}

    class PkSwapSerializer(serializers.ModelSerializer):
        class Meta:
            model = product_models.Item
            fields = ("name", "category")

        def create(self, validated_data):
            item = super().create(validated_data)  # a REAL witnessed insert
            item.pk = hidden_holder["pk"]  # then re-point the same object at a hidden row
            return item

    category = product_models.Category.objects.create(name="SwapCat")
    hidden = product_models.Item.objects.create(name="HiddenSwap", category=category)
    hidden_holder["pk"] = hidden.pk
    mutation_cls = _bind_item_serializer_mutation(PkSwapSerializer)
    request = HttpRequest()
    request.user = SimpleNamespace(username="u", is_authenticated=True)
    info = SimpleNamespace(context=SimpleNamespace(request=request))

    with write_pipeline("default", lock=False):
        with pytest.raises(ConfigurationError, match="never observed being INSERTED"):
            serializer_resolvers._serializer_write_step(
                mutation_cls,
                info,
                None,
                {"name": "Fresh", "category": category.pk},
            )


@pytest.mark.django_db
def test_write_step_create_returning_existing_row_is_configuration_error():
    """A custom ``create()`` returning an EXISTING row through normal DRF bookkeeping fails loud.

    DRF's ``save()`` assigns whatever ``create()`` returns to ``self.instance``, so identity
    alone cannot distinguish a real insert from an existing row laundered as "created"; the
    ``post_save`` witness never saw an INSERT of the returned row, so the write step rejects
    it before the visibility-free re-fetch could leak it.
    """

    class LaunderingSerializer(serializers.ModelSerializer):
        class Meta:
            model = product_models.Item
            fields = ("name", "category")

        def create(self, validated_data):
            # No insert at all: hand back a pre-existing row (e.g. someone else's).
            return product_models.Item.objects.get(name="PreyRow")

    category = product_models.Category.objects.create(name="PreyCat")
    product_models.Item.objects.create(name="PreyRow", category=category)
    mutation_cls = _bind_item_serializer_mutation(LaunderingSerializer)
    request = HttpRequest()
    request.user = SimpleNamespace(username="u", is_authenticated=True)
    info = SimpleNamespace(context=SimpleNamespace(request=request))

    with write_pipeline("default", lock=False):
        with pytest.raises(ConfigurationError, match="never observed being INSERTED"):
            serializer_resolvers._serializer_write_step(
                mutation_cls,
                info,
                None,
                {"name": "Fresh", "category": category.pk},
            )


def test_write_witness_blocks_cross_alias_pre_save():
    """The witness's ``pre_save`` guard rejects a cross-alias write BEFORE it executes.

    The post-hoc alias check on the returned row could only detect an escaped write after
    it was already committed outside the pinned transaction; the guard fires at the signal,
    so the query never runs. Same-alias writes pass; other threads are untouched (each
    request installs its own thread-scoped witness).
    """
    import threading

    from django.db.models.signals import pre_save

    fake = type("WitnessMut", (), {})
    with serializer_resolvers._write_witness(fake, product_models.Item, "default") as written:
        with pytest.raises(ConfigurationError, match="attempted to save"):
            pre_save.send(
                sender=product_models.Item,
                instance=product_models.Item(name="x"),
                using="other",
            )
        # Same-alias writes pass through the guard untouched.
        pre_save.send(
            sender=product_models.Item,
            instance=product_models.Item(name="x"),
            using="default",
        )

        # A DIFFERENT thread's cross-alias save is not this request's to police - and its
        # writes are not recorded on this request's witness either.
        from django.db.models.signals import post_save

        errors: list[BaseException] = []

        def _other_thread_save():
            try:
                pre_save.send(
                    sender=product_models.Item,
                    instance=product_models.Item(name="x"),
                    using="other",
                )
                post_save.send(
                    sender=product_models.Item,
                    instance=product_models.Item(name="x"),
                    created=True,
                    using="default",
                )
            except BaseException as exc:  # pragma: no cover - only on regression
                errors.append(exc)

        thread = threading.Thread(target=_other_thread_save)
        thread.start()
        thread.join()
        assert errors == []
        assert written == []  # the other thread's write never lands on this witness


def test_pipeline_alias_guard_rejects_every_statement_on_non_pinned_alias():
    """The pipeline's alias guard rejects ALL SQL on a non-pinned connection - no classification.

    A lexical read/write keyword test is bypassable (leading SQL comments, PostgreSQL
    ``EXPLAIN ANALYZE UPDATE`` which executes the write, write-capable functions invoked
    through ``SELECT``), so the guard installed around the pipeline's consumer-reachable
    phases raises on EVERY statement issued on a non-pinned alias - reads included - and
    is removed once the guarded phase exits.
    """
    from django.db import connections

    from django_strawberry_framework.utils.write_transaction import pipeline_alias_guard

    extra = dict(connections.databases["default"])
    extra["NAME"] = ":memory:"
    connections.databases["mirror_alias"] = extra
    try:
        mirror = connections["mirror_alias"]
        baseline = len(mirror.execute_wrappers)
        with pipeline_alias_guard("NetMut", "default"):
            # Installed on the non-pinned alias for the phase...
            assert len(mirror.execute_wrappers) == baseline + 1
            guard = mirror.execute_wrappers[-1]
            for statement in (
                "UPDATE t SET x = 1",
                "/* hide */ INSERT INTO t VALUES (1)",
                "EXPLAIN ANALYZE UPDATE t SET x = 1",
                "SELECT write_capable_function()",
                "SELECT 1",
            ):
                with pytest.raises(ConfigurationError, match="SQL statement was issued"):
                    guard(lambda *args: None, statement, None, False, None)
        # ... and removed once the guarded phase exits.
        assert len(mirror.execute_wrappers) == baseline
    finally:
        connections["mirror_alias"].close()
        del connections.databases["mirror_alias"]


def test_pipeline_alias_guard_auth_alias_access_is_scoped_to_the_authorization_phase():
    """Auth-alias statements pass the guard ONLY while the authorization phase is open.

    A divergent read/write router keeps auth off the write alias, so the authorization
    phase permits queries on the identified auth aliases. The guard does NOT lexically
    classify them (a keyword test cannot safely authorize cross-alias execution - the
    rolled-back barrier transaction is the real boundary, exercised in the
    ``authorization_phase`` rollback test), so read AND write-shaped statements pass here;
    the scoping is what matters - before the phase opens and after it closes the same auth
    alias is back to reject-everything, so decode / hooks / validation cannot reach it.
    """
    from django.db import connections

    from django_strawberry_framework.utils.write_transaction import (
        pipeline_alias_guard,
        require_write_pipeline,
        write_pipeline,
    )

    extra = dict(connections.databases["default"])
    extra["NAME"] = ":memory:"
    connections.databases["auth_mirror"] = extra
    sentinel = object()

    def _execute(
        sql,
        params,
        many,
        context,
    ):
        del sql, params, many, context
        return sentinel

    try:
        mirror = connections["auth_mirror"]
        with write_pipeline("default", lock=False), pipeline_alias_guard("AuthMut", "default"):
            guard = mirror.execute_wrappers[-1]
            ctx = require_write_pipeline()
            # BEFORE the phase: every statement on the non-pinned alias is rejected.
            with pytest.raises(ConfigurationError, match="SQL statement was issued"):
                guard(_execute, "SELECT 1", None, False, None)
            # DURING the phase (flag toggled directly here; the rolled-back barrier
            # that makes this safe is proven separately): statements pass - read AND
            # write-shaped, since the barrier transaction, not lexical classification,
            # is the boundary.
            ctx.auth_phase = True
            ctx.auth_aliases = frozenset({"auth_mirror"})
            try:
                assert guard(_execute, "SELECT 1", None, False, None) is sentinel
                assert (
                    guard(_execute, "UPDATE auth_permission SET x = 1", None, False, None)
                    is sentinel
                )
            finally:
                ctx.auth_phase = False
                ctx.auth_aliases = frozenset()
            # AFTER the phase closes: rejected again.
            with pytest.raises(ConfigurationError, match="SQL statement was issued"):
                guard(_execute, "SELECT 1", None, False, None)
    finally:
        connections["auth_mirror"].close()
        del connections.databases["auth_mirror"]


def test_authorization_phase_enforces_db_read_only_on_non_pinned_auth_aliases(django_db_blocker):
    """The security boundary: a write on a non-pinned auth alias is REJECTED by the database.

    ``authorization_phase`` puts each non-pinned auth alias in a database-enforced read-only
    transaction (SQLite ``PRAGMA query_only``), so a permission backend's write is refused by
    the server itself - not merely rolled back. Forced rollback alone is not portable (non-
    transactional tables, implicitly-committed DDL, effects that outlive a rollback), so the
    barrier is backed by the DB's own read-only enforcement. Reads still pass; once the phase
    ends the connection is restored to writable.
    """
    from django.db import connections
    from django.db.utils import OperationalError

    from django_strawberry_framework.utils.write_transaction import (
        authorization_phase,
        write_pipeline,
    )

    extra = dict(connections.databases["default"])
    extra["NAME"] = ":memory:"
    connections.databases["auth_barrier"] = extra
    # A throwaway :memory: alias managed by hand (no fixture DB, no isolation
    # concern), so the pytest-django access block is explicitly lifted for it.
    with django_db_blocker.unblock():
        try:
            conn = connections["auth_barrier"]
            with conn.cursor() as cursor:
                cursor.execute("CREATE TABLE probe (id INTEGER PRIMARY KEY)")
                cursor.execute("INSERT INTO probe (id) VALUES (1)")
            # Pinned to ``default``; ``auth_barrier`` is a non-pinned auth alias.
            with write_pipeline("default", lock=False), authorization_phase({"auth_barrier"}):
                with conn.cursor() as cursor:
                    # Reads are permitted inside the read-only barrier.
                    cursor.execute("SELECT COUNT(*) FROM probe")
                    assert cursor.fetchone()[0] == 1
                    # A write is refused by the database itself (read-only transaction).
                    with pytest.raises(OperationalError, match="readonly"):
                        cursor.execute("INSERT INTO probe (id) VALUES (2)")
            # The write never happened, and the connection is writable again post-phase.
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM probe")
                assert cursor.fetchone()[0] == 1
                cursor.execute("INSERT INTO probe (id) VALUES (3)")
                cursor.execute("SELECT COUNT(*) FROM probe")
                assert cursor.fetchone()[0] == 2
        finally:
            connections["auth_barrier"].close()
            del connections.databases["auth_barrier"]


def test_pipeline_alias_guard_blocks_cross_alias_pre_save_and_ignores_other_threads():
    """The guard's ``pre_save`` receiver: cross-alias saves fail early, same-alias and other threads pass."""
    import threading

    from django.db.models.signals import pre_save

    from django_strawberry_framework.utils.write_transaction import pipeline_alias_guard

    with pipeline_alias_guard("GuardMut", "default"):
        with pytest.raises(ConfigurationError, match="attempted to save"):
            pre_save.send(
                sender=product_models.Item,
                instance=product_models.Item(name="x"),
                using="other",
            )
        # Same-alias saves pass through the guard untouched.
        pre_save.send(
            sender=product_models.Item,
            instance=product_models.Item(name="x"),
            using="default",
        )

        # A DIFFERENT thread's cross-alias save is not this request's to police.
        errors: list[BaseException] = []

        def _other_thread_save():
            try:
                pre_save.send(
                    sender=product_models.Item,
                    instance=product_models.Item(name="x"),
                    using="other",
                )
            except BaseException as exc:  # pragma: no cover - only on regression
                errors.append(exc)

        thread = threading.Thread(target=_other_thread_save)
        thread.start()
        thread.join()
        assert errors == []


@pytest.mark.django_db
def test_saved_result_none_alias_on_persisted_looking_instance_is_configuration_error():
    """A result whose ``_state.db`` is ``None`` fails the EXACT-alias check (never ORM-loaded)."""
    fake, serializer = _saved_result_fixture()
    category = product_models.Category.objects.create(name="NoneAliasCat")
    item = product_models.Item.objects.create(name="NoneAliasItem", category=category)
    item._state.db = None  # simulate a custom save() handing back a detached object
    serializer.instance = item
    with pytest.raises(ConfigurationError, match="alias None"):
        serializer_resolvers._checked_saved_result(fake, serializer, item, None, "default", [])


@pytest.mark.django_db
def test_saved_result_wrong_alias_is_configuration_error():
    """A ``save()`` result living on a different database alias fails loud (escaped the transaction)."""
    fake, serializer = _saved_result_fixture()
    category = product_models.Category.objects.create(name="AliasCat")
    item = product_models.Item.objects.create(name="AliasItem", category=category)
    serializer.instance = item
    with pytest.raises(ConfigurationError, match="alias 'default'"):
        serializer_resolvers._checked_saved_result(fake, serializer, item, None, "shard_b", [])


@pytest.mark.django_db
def test_saved_result_update_pk_drift_is_configuration_error():
    """On update, a ``save()`` returning a DIFFERENT row than the authorized one fails loud."""
    fake, serializer = _saved_result_fixture()
    category = product_models.Category.objects.create(name="DriftCat")
    authorized = product_models.Item.objects.create(name="Authorized", category=category)
    other = product_models.Item.objects.create(name="Other", category=category)
    serializer.instance = other
    with pytest.raises(ConfigurationError, match="must write the row that was authorized"):
        serializer_resolvers._checked_saved_result(
            fake,
            serializer,
            other,
            authorized.pk,
            "default",
            [],
        )


@pytest.mark.django_db
def test_saved_result_happy_path_returns_saved():
    """A correct-model, saved, same-alias, same-pk result passes through unchanged."""
    fake, serializer = _saved_result_fixture()
    category = product_models.Category.objects.create(name="OkCat")
    item = product_models.Item.objects.create(name="OkItem", category=category)
    serializer.instance = item
    written = [
        (
            item,
            item.pk,
            False,
            "default",
        ),
    ]
    assert (
        serializer_resolvers._checked_saved_result(
            fake,
            serializer,
            item,
            item.pk,
            "default",
            written,
        )
        is item
    )


@pytest.mark.django_db
def test_saved_result_update_without_witness_is_configuration_error():
    """Returning the existing instance without saving is not a successful update."""
    fake, serializer = _saved_result_fixture()
    category = product_models.Category.objects.create(name="NoopCat")
    item = product_models.Item.objects.create(name="NoopItem", category=category)
    serializer.instance = item
    with pytest.raises(ConfigurationError, match="never observed being UPDATED"):
        serializer_resolvers._checked_saved_result(
            fake,
            serializer,
            item,
            item.pk,
            "default",
            [],
        )


def test_validator_querysets_are_recursively_pinned_to_write_alias():
    """Field, serializer-level, and nested validator querysets share the write alias."""

    class ChildSerializer(serializers.Serializer):
        name = serializers.CharField(
            validators=[
                UniqueValidator(queryset=product_models.Category.objects.all()),
            ],
        )

    class ParentSerializer(serializers.Serializer):
        name = serializers.CharField(
            validators=[
                UniqueValidator(queryset=product_models.Item.objects.all()),
            ],
        )
        category = serializers.PrimaryKeyRelatedField(
            queryset=product_models.Category.objects.all(),
        )
        child = ChildSerializer()

        class Meta:
            validators = [
                UniqueTogetherValidator(
                    queryset=product_models.Item.objects.all(),
                    fields=("name", "category"),
                ),
            ]

    serializer = ParentSerializer(data={})
    serializer_resolvers._pin_validator_querysets(serializer, "shard_b")

    assert serializer.fields["name"].validators[0].queryset._db == "shard_b"
    assert serializer.validators[0].queryset._db == "shard_b"
    assert serializer.fields["child"].fields["name"].validators[0].queryset._db == "shard_b"


def test_validator_queryset_pinning_replaces_shared_validator_per_serializer_instance():
    """Pinning one serializer cannot mutate the validator shared with another request."""
    shared = UniqueValidator(queryset=product_models.Item.objects.all())

    class SharedValidatorSerializer(serializers.Serializer):
        name = serializers.CharField(validators=[shared])

    shard_serializer = SharedValidatorSerializer(data={})
    default_serializer = SharedValidatorSerializer(data={})
    assert shard_serializer.fields["name"].validators[0] is shared
    assert default_serializer.fields["name"].validators[0] is shared

    serializer_resolvers._pin_validator_querysets(shard_serializer, "shard_b")
    serializer_resolvers._pin_validator_querysets(default_serializer, "default")

    shard_validator = shard_serializer.fields["name"].validators[0]
    default_validator = default_serializer.fields["name"].validators[0]
    assert shard_validator is not shared
    assert default_validator is not shared
    assert shard_validator is not default_validator
    assert shard_validator.queryset._db == "shard_b"
    assert default_validator.queryset._db == "default"
    assert shared.queryset._db is None


def test_list_field_child_validator_querysets_are_pinned_and_isolated():
    """Composite field children execute validators and need per-request alias pinning too."""
    shared = UniqueValidator(queryset=product_models.Item.objects.all())

    class TagsSerializer(serializers.Serializer):
        tags = serializers.ListField(child=serializers.CharField(validators=[shared]))

    shard_serializer = TagsSerializer(data={})
    default_serializer = TagsSerializer(data={})
    serializer_resolvers._pin_validator_querysets(shard_serializer, "shard_b")
    serializer_resolvers._pin_validator_querysets(default_serializer, "default")

    shard_validator = shard_serializer.fields["tags"].child.validators[0]
    default_validator = default_serializer.fields["tags"].child.validators[0]
    assert shard_validator is not shared
    assert default_validator is not shared
    assert shard_validator is not default_validator
    assert shard_validator.queryset._db == "shard_b"
    assert default_validator.queryset._db == "default"
    assert shared.queryset._db is None


def test_runtime_context_field_source_collision_fails_before_validation():
    """Context-dependent hidden fields absent from schema discovery still fail loud."""

    class ContextualSerializer(serializers.Serializer):
        name = serializers.CharField()

        def get_fields(self):
            fields = super().get_fields()
            if self.context.get("inject_hidden"):
                fields["hidden_name"] = serializers.HiddenField(default="server", source="name")
            return fields

    mutation_cls = SimpleNamespace(
        __name__="ContextualMutation",
        _mutation_meta=SimpleNamespace(operation="create"),
    )
    serializer = ContextualSerializer(
        data={"name": "client"},
        context={"inject_hidden": True},
    )

    with pytest.raises(ConfigurationError, match="runtime serializer path '<root>'"):
        serializer_resolvers._assert_runtime_write_source_ownership(
            mutation_cls,
            serializer,
            {"name": "client"},
            [],
        )


def test_runtime_nested_source_ownership_handles_omitted_child_data():
    """An omitted nested value still audits the child serializer with empty data."""

    class ChildSerializer(serializers.Serializer):
        name = serializers.CharField(required=False)

    class ParentSerializer(serializers.Serializer):
        child = ChildSerializer(required=False)

    mutation_cls = SimpleNamespace(
        __name__="NestedOwnershipMutation",
        _mutation_meta=SimpleNamespace(operation="update"),
    )
    nested_spec = SimpleNamespace(
        kind=serializer_resolvers.NESTED_SINGLE,
        target_name="child",
        nested_specs=(),
    )

    serializer_resolvers._assert_runtime_write_source_ownership(
        mutation_cls,
        ParentSerializer(data={}),
        {},
        [nested_spec],
    )


def test_runtime_context_star_source_field_is_rejected_before_validation():
    """A context-dependent ``source="*"`` runtime field is rejected before validation runs.

    Such a field never reaches the schema-time column converter (it only exists at runtime),
    yet DRF would merge its returned mapping into validated_data and could overwrite the
    client's ``name``. The runtime ownership guard rejects any writable star field.
    """

    class ContextualStarSerializer(serializers.Serializer):
        name = serializers.CharField()

        def get_fields(self):
            fields = super().get_fields()
            if self.context.get("inject_star"):
                # A defaulted whole-object field genuinely contributes to validated_data
                # at runtime (it needs no client value), so it can overwrite ``name``.
                fields["whole"] = serializers.HiddenField(
                    default={"name": "server"},
                    source="*",
                )
            return fields

    mutation_cls = SimpleNamespace(
        __name__="ContextualStarMutation",
        _mutation_meta=SimpleNamespace(operation="create"),
    )
    serializer = ContextualStarSerializer(
        data={"name": "client"},
        context={"inject_star": True},
    )

    with pytest.raises(ConfigurationError, match="source='\\*'"):
        serializer_resolvers._assert_runtime_write_source_ownership(
            mutation_cls,
            serializer,
            {"name": "client"},
            [],
        )


def test_validator_queryset_explicitly_routed_elsewhere_fails_closed():
    """An author-pinned validator queryset cannot escape the write transaction alias."""

    class RoutedValidatorSerializer(serializers.Serializer):
        name = serializers.CharField(
            validators=[
                UniqueValidator(
                    queryset=product_models.Item.objects.using("other"),
                ),
            ],
        )

    serializer = RoutedValidatorSerializer(data={})
    with pytest.raises(ConfigurationError, match="routed to alias 'other'"):
        serializer_resolvers._pin_validator_querysets(serializer, "default")


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
    with write_pipeline("default", lock=False):
        serializer_resolvers._scope_relation_querysets_to_visibility(
            type(
                "SingleMut",
                (),
                {
                    "_injected_field_specs": [],
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
    with write_pipeline("default", lock=False):
        serializer_resolvers._scope_relation_querysets_to_visibility(
            type(
                "ManyMut",
                (),
                {
                    "_injected_field_specs": [],
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
    return type(
        "FakeMut",
        (),
        {"_input_field_specs": [InputFieldSpec(**base)], "_injected_field_specs": []},
    )


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
            "_injected_field_specs": [],
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


# ===========================================================================
# The relation-intent ledger + post-save attestation (the hardening pass)
# ===========================================================================


def _bind_book_genres_mutation(serializer_cls, *, operation="update"):
    """Declare + finalize a minimal Book/Genre `SerializerMutation` (M2M fixtures)."""
    op_value = operation

    class GenreT(DjangoType, relay.Node):
        class Meta:
            model = library_models.Genre
            fields = ("id", "name")
            primary = True

    class BookT(DjangoType, relay.Node):
        class Meta:
            model = library_models.Book
            fields = ("id", "title")
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

    class WriteBook(SerializerMutation):
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
        write0 = DjangoMutationField(WriteBook)

    finalize_django_types()
    DjangoSchema(query=Query, mutation=Mutation)
    return WriteBook


def _info():
    request = HttpRequest()
    request.user = SimpleNamespace(username="u", is_authenticated=True)
    return SimpleNamespace(context=SimpleNamespace(request=request))


def _genres_serializer(**extra):
    """A Book serializer exposing title + genres (allow_empty so [] clears)."""

    class GenresSerializer(serializers.ModelSerializer):
        genres = serializers.PrimaryKeyRelatedField(
            many=True,
            queryset=library_models.Genre.objects.all(),
            allow_empty=True,
        )

        class Meta:
            model = library_models.Book
            fields = ("title", "genres")

    for key, value in extra.items():
        setattr(GenresSerializer, key, value)
    return GenresSerializer


def _seed_book(genres=()):
    branch = library_models.Branch.objects.create(name="LedgerBranch", city="Boston")
    shelf = library_models.Shelf.objects.create(code="LedgerShelf", branch=branch)
    book = library_models.Book.objects.create(title="LedgerBook", shelf=shelf)
    if genres:
        book.genres.set(genres)
    return book


@pytest.mark.django_db
def test_field_validator_substituting_a_relation_object_is_rejected():
    """A field-level validator swapping the resolved FK object for another row fails closed."""
    hidden = product_models.Category.objects.create(name="LedgerHidden")

    class SwappingSerializer(serializers.ModelSerializer):
        class Meta:
            model = product_models.Item
            fields = ("name", "category")

        def validate_category(self, value):
            return product_models.Category.objects.get(pk=hidden.pk)  # the swap

    visible = product_models.Category.objects.create(name="LedgerVisible")
    mutation_cls = _bind_item_serializer_mutation(SwappingSerializer)
    with write_pipeline("default", lock=False):
        with pytest.raises(ConfigurationError, match="replaced a visibility-checked relation"):
            serializer_resolvers._serializer_write_step(
                mutation_cls,
                _info(),
                None,
                {"name": "LedgerItem", "category": visible.pk},
            )


@pytest.mark.django_db
def test_object_validator_injecting_a_relation_value_is_rejected():
    """A ``validate()`` injecting a relation value the field never produced fails closed."""
    hidden = library_models.Genre.objects.create(name="InjectHidden")

    class InjectingSerializer(serializers.ModelSerializer):
        genres = serializers.PrimaryKeyRelatedField(
            many=True,
            queryset=library_models.Genre.objects.all(),
            allow_empty=True,
            required=False,
        )

        class Meta:
            model = library_models.Book
            fields = ("title", "genres")

        def validate(self, attrs):
            attrs["genres"] = [library_models.Genre.objects.get(pk=hidden.pk)]
            return attrs

    book = _seed_book()
    mutation_cls = _bind_book_genres_mutation(InjectingSerializer)
    with write_pipeline("default", lock=False):
        with pytest.raises(ConfigurationError, match="never produced"):
            serializer_resolvers._serializer_write_step(
                mutation_cls,
                _info(),
                book,
                {"title": "InjectTitle"},
            )


@pytest.mark.django_db
def test_object_validator_popping_a_supplied_relation_is_rejected():
    """A validator POPPING a client-supplied relation fails closed: intent must not be dropped."""

    class PoppingSerializer(serializers.ModelSerializer):
        genres = serializers.PrimaryKeyRelatedField(
            many=True,
            queryset=library_models.Genre.objects.all(),
            allow_empty=True,
        )

        class Meta:
            model = library_models.Book
            fields = ("title", "genres")

        def validate(self, attrs):
            attrs.pop("genres", None)
            return attrs

    kept = library_models.Genre.objects.create(name="PopKept")
    other = library_models.Genre.objects.create(name="PopOther")
    book = _seed_book(genres=[kept])
    mutation_cls = _bind_book_genres_mutation(PoppingSerializer)
    with write_pipeline("default", lock=False):
        with pytest.raises(ConfigurationError, match="removed from validated_data by a validator"):
            serializer_resolvers._serializer_write_step(
                mutation_cls,
                _info(),
                book,
                {"title": "PoppedTitle", "genres": [other.pk]},
            )
    # The write was rejected before save: the stored set is unchanged.
    assert set(book.genres.values_list("pk", flat=True)) == {kept.pk}


@pytest.mark.django_db
def test_field_validator_substituting_a_renamed_source_relation_is_rejected():
    """The intent walk compares under the runtime ``source``: a renamed relation is covered."""
    hidden = product_models.Category.objects.create(name="RenamedHidden")

    class RenamedSwapSerializer(serializers.ModelSerializer):
        group = serializers.PrimaryKeyRelatedField(
            source="category",
            queryset=product_models.Category.objects.all(),
        )

        class Meta:
            model = product_models.Item
            fields = ("name", "group")

        def validate_group(self, value):
            return product_models.Category.objects.get(pk=hidden.pk)

    visible = product_models.Category.objects.create(name="RenamedVisible")
    mutation_cls = _bind_item_serializer_mutation(RenamedSwapSerializer)
    with write_pipeline("default", lock=False):
        with pytest.raises(ConfigurationError, match="replaced a visibility-checked relation"):
            serializer_resolvers._serializer_write_step(
                mutation_cls,
                _info(),
                None,
                {"name": "RenamedItem", "group": visible.pk},
            )


@pytest.mark.django_db
def test_custom_pk_field_relation_stays_supported_by_the_ledger():
    """A custom ``pk_field`` transformation passes: the ledger verifies the RESOLVED object."""

    class StringPkSerializer(serializers.ModelSerializer):
        category = serializers.PrimaryKeyRelatedField(
            queryset=product_models.Category.objects.all(),
            pk_field=serializers.CharField(),  # a supported transformation, not a ban target
        )

        class Meta:
            model = product_models.Item
            fields = ("name", "category")

    category = product_models.Category.objects.create(name="PkFieldCat")
    mutation_cls = _bind_item_serializer_mutation(StringPkSerializer)
    with write_pipeline("default", lock=False):
        saved = serializer_resolvers._serializer_write_step(
            mutation_cls,
            _info(),
            None,
            {"name": "PkFieldItem", "category": str(category.pk)},
        )
    assert isinstance(saved, product_models.Item)
    assert saved.category_id == category.pk


@pytest.mark.django_db
def test_object_validator_mutating_a_resolved_relation_pk_in_place_is_rejected():
    """Re-pointing a resolved relation object's pk IN PLACE (identity intact) fails closed."""
    hidden = product_models.Category.objects.create(name="InPlaceHidden")

    class MutatingSerializer(serializers.ModelSerializer):
        category = serializers.PrimaryKeyRelatedField(
            queryset=product_models.Category.objects.all(),
        )

        class Meta:
            model = product_models.Item
            fields = ("name", "category")

        def validate(self, attrs):
            # Mutate the SAME resolved object's pk to a hidden row: a bare
            # identity check would miss it; the captured-pk snapshot catches it.
            attrs["category"].pk = hidden.pk
            return attrs

    visible = product_models.Category.objects.create(name="InPlaceVisible")
    mutation_cls = _bind_item_serializer_mutation(MutatingSerializer)
    with write_pipeline("default", lock=False):
        with pytest.raises(ConfigurationError, match="not the exact object"):
            serializer_resolvers._serializer_write_step(
                mutation_cls,
                _info(),
                None,
                {"name": "InPlaceItem", "category": visible.pk},
            )


def test_relation_intent_snapshot_handles_a_null_relation():
    """A null relation snapshots ``(None, None, None)`` and matches an unchanged ``None``."""
    snap = serializer_resolvers._relation_intent_snapshot(None)
    assert snap == (None, None, None)
    assert serializer_resolvers._relation_identity_intact(None, snap)
    # A list relation snapshots one tuple per row (a null member is captured too).
    assert serializer_resolvers._relation_intent_snapshot([None]) == [(None, None, None)]


@pytest.mark.django_db
def test_custom_update_ignoring_a_validated_fk_fails_attestation():
    """A custom ``update()`` that drops the validated FK is a loud attestation failure."""

    class IgnoringSerializer(serializers.ModelSerializer):
        class Meta:
            model = product_models.Item
            fields = ("name", "category")

        def update(self, instance, validated_data):
            validated_data.pop("category", None)  # ignore the validated relation
            return super().update(instance, validated_data)

    old = product_models.Category.objects.create(name="AttestOld")
    new = product_models.Category.objects.create(name="AttestNew")
    item = product_models.Item.objects.create(name="AttestItem", category=old)
    mutation_cls = _bind_item_serializer_mutation(IgnoringSerializer, operation="update")
    with write_pipeline("default", lock=False):
        with pytest.raises(ConfigurationError, match="ignored or replaced a validated relation"):
            serializer_resolvers._serializer_write_step(
                mutation_cls,
                _info(),
                item,
                {"category": new.pk},
            )


@pytest.mark.django_db
def test_custom_update_mutating_a_validated_relation_pk_at_save_fails_attestation():
    """Mutating a validated relation's pk IN PLACE during save() cannot forge attestation.

    The intent walk captures the visible relation's canonical pk BEFORE save; attestation
    compares the database against that CAPTURED pk, not the live object. So a custom
    ``update()`` that re-points the validated object's pk to a hidden row during save (which
    would forge both the persisted column and a live ``obj.pk`` comparison) is caught.
    """
    visible = product_models.Category.objects.create(name="SaveTimeVisible")
    hidden = product_models.Category.objects.create(name="SaveTimeHidden")
    item = product_models.Item.objects.create(name="SaveTimeItem", category=visible)

    class MutatingUpdateSerializer(serializers.ModelSerializer):
        class Meta:
            model = product_models.Item
            fields = ("name", "category")

        def update(self, instance, validated_data):
            # The visible object passed the pre-save intent walk; now re-point its
            # pk to a hidden row and persist THAT - a forge the live-object read
            # would miss, but the captured-pk attestation catches.
            validated_data["category"].pk = hidden.pk
            return super().update(instance, validated_data)

    mutation_cls = _bind_item_serializer_mutation(MutatingUpdateSerializer, operation="update")
    with write_pipeline("default", lock=False):
        with pytest.raises(ConfigurationError, match="ignored or replaced a validated relation"):
            serializer_resolvers._serializer_write_step(
                mutation_cls,
                _info(),
                item,
                {"category": visible.pk},
            )


@pytest.mark.django_db
def test_custom_update_replacing_the_validated_m2m_set_fails_attestation():
    """A custom ``update()`` writing a DIFFERENT M2M set than validated fails closed."""
    stray = library_models.Genre.objects.create(name="AttestStray")

    class ReplacingSerializer(serializers.ModelSerializer):
        genres = serializers.PrimaryKeyRelatedField(
            many=True,
            queryset=library_models.Genre.objects.all(),
            allow_empty=True,
        )

        class Meta:
            model = library_models.Book
            fields = ("title", "genres")

        def update(self, instance, validated_data):
            validated_data.pop("genres", None)
            instance = super().update(instance, validated_data)
            instance.genres.set([stray])  # not the validated set
            return instance

    wanted = library_models.Genre.objects.create(name="AttestWanted")
    book = _seed_book()
    mutation_cls = _bind_book_genres_mutation(ReplacingSerializer)
    with write_pipeline("default", lock=False):
        with pytest.raises(ConfigurationError, match="ignored or replaced a validated relation"):
            serializer_resolvers._serializer_write_step(
                mutation_cls,
                _info(),
                book,
                {"genres": [wanted.pk]},
            )


@pytest.mark.django_db
def test_custom_update_rewriting_an_omitted_partial_m2m_fails_attestation():
    """An OMITTED partial-update M2M must stay byte-identical to its pre-save membership."""

    class SneakySerializer(serializers.ModelSerializer):
        genres = serializers.PrimaryKeyRelatedField(
            many=True,
            queryset=library_models.Genre.objects.all(),
            allow_empty=True,
            required=False,
        )

        class Meta:
            model = library_models.Book
            fields = ("title", "genres")

        def update(self, instance, validated_data):
            instance = super().update(instance, validated_data)
            instance.genres.clear()  # rewrite a relation the client never sent
            return instance

    kept = library_models.Genre.objects.create(name="OmittedKept")
    book = _seed_book(genres=[kept])
    mutation_cls = _bind_book_genres_mutation(SneakySerializer)
    with write_pipeline("default", lock=False):
        with pytest.raises(ConfigurationError, match="OMITTED partial-update M2M"):
            serializer_resolvers._serializer_write_step(
                mutation_cls,
                _info(),
                book,
                {"title": "OmittedTitle"},
            )


@pytest.mark.django_db
def test_supplied_m2m_duplicates_and_explicit_empty_list_pass_attestation():
    """DRF/M2M set semantics survive attestation: duplicates collapse, ``[]`` clears."""
    genre = library_models.Genre.objects.create(name="SetSemGenre")
    book = _seed_book(genres=[genre])
    mutation_cls = _bind_book_genres_mutation(_genres_serializer())

    with write_pipeline("default", lock=False):
        saved = serializer_resolvers._serializer_write_step(
            mutation_cls,
            _info(),
            book,
            {"genres": [genre.pk, genre.pk]},  # duplicates collapse to the one row
        )
    assert isinstance(saved, library_models.Book)
    assert list(book.genres.values_list("pk", flat=True)) == [genre.pk]

    with write_pipeline("default", lock=False):
        saved = serializer_resolvers._serializer_write_step(
            mutation_cls,
            _info(),
            book,
            {"genres": []},  # an explicit empty list is a clear
        )
    assert isinstance(saved, library_models.Book)
    assert not book.genres.exists()


@pytest.mark.django_db
def test_no_m2m_membership_query_runs_before_authorization():
    """The pre-save M2M snapshot never queries membership before the permission phase ran."""
    from django.db import connection

    seen = {"authorized": False, "early_m2m": []}
    through_table = library_models.Book.genres.through._meta.db_table

    class _RecordingPermission:
        def has_permission(
            self,
            info,
            mutation,
            op,
            data,
            instance=None,
        ):
            seen["authorized"] = True
            return True

    class GenresSerializer(serializers.ModelSerializer):
        genres = serializers.PrimaryKeyRelatedField(
            many=True,
            queryset=library_models.Genre.objects.all(),
            allow_empty=True,
            required=False,
        )

        class Meta:
            model = library_models.Book
            fields = ("title", "genres")

    genre = library_models.Genre.objects.create(name="OrderingGenre")
    book = _seed_book(genres=[genre])

    class GenreT(DjangoType, relay.Node):
        class Meta:
            model = library_models.Genre
            fields = ("id", "name")
            primary = True

    class BookT(DjangoType, relay.Node):
        class Meta:
            model = library_models.Book
            fields = ("id", "title")
            primary = True

    class UpdateBook(SerializerMutation):
        class Meta:
            serializer_class = GenresSerializer
            operation = "update"
            permission_classes = [_RecordingPermission]

    @strawberry.type
    class Query:
        @strawberry.field
        def ping(self) -> int:
            return 1

    @strawberry.type
    class Mutation:
        write0 = DjangoMutationField(UpdateBook)

    finalize_django_types()
    schema = DjangoSchema(query=Query, mutation=Mutation)

    def _watch(
        execute,
        sql,
        params,
        many,
        context,
    ):
        if through_table in str(sql) and not seen["authorized"]:
            seen["early_m2m"].append(sql)
        return execute(sql, params, many, context)

    book_gid = global_id_for(BookT, book.pk)
    request = HttpRequest()
    request.user = SimpleNamespace(
        username="u",
        is_authenticated=True,
        get_all_permissions=lambda: set(),
    )
    with connection.execute_wrapper(_watch):
        result = schema.execute_sync(
            "mutation($id: ID!, $d: GenresSerializerPartialInput!) { write0(id: $id, data: $d) "
            "{ node { title } errors { field messages } } }",
            variable_values={"id": book_gid, "d": {"title": "Ordered"}},
            context_value=SimpleNamespace(request=request),
        )
    assert result.errors is None, result.errors
    assert seen["authorized"] is True
    # No membership query fired before the permission phase completed.
    assert seen["early_m2m"] == []


# ===========================================================================
# Phase separation, savepoint, target drift, canonical pks (the hardening pass)
# ===========================================================================


@pytest.mark.django_db
def test_save_failure_after_partial_writes_rolls_back_to_the_savepoint():
    """A custom ``create()`` that WROTE rows then raised leaves no partial write behind."""

    class PartialWritingSerializer(serializers.ModelSerializer):
        class Meta:
            model = product_models.Item
            fields = ("name", "category")

        def create(self, validated_data):
            super().create(dict(validated_data))  # a real INSERT...
            raise serializers.ValidationError({"name": ["post-write failure"]})

    category = product_models.Category.objects.create(name="SavepointCat")
    mutation_cls = _bind_item_serializer_mutation(PartialWritingSerializer)
    with write_pipeline("default", lock=False):
        result = serializer_resolvers._serializer_write_step(
            mutation_cls,
            _info(),
            None,
            {"name": "SavepointItem", "category": category.pk},
        )
    assert isinstance(result, list)
    assert [(fe.field, fe.messages) for fe in result] == [("name", ["post-write failure"])]
    # PROVEN in-transaction: the savepoint rollback removed the partial INSERT.
    assert not product_models.Item.objects.filter(name="SavepointItem").exists()


@pytest.mark.django_db
def test_hook_mutating_the_located_target_is_rejected_before_save():
    """In-memory drift of the located row between locate and save fails closed."""
    from django_strawberry_framework.utils.write_transaction import (
        require_write_pipeline,
        snapshot_target_state,
    )

    class DriftSerializer(serializers.ModelSerializer):
        class Meta:
            model = product_models.Item
            fields = ("name", "category")

    class DriftingMutation(_bind_item_serializer_mutation(DriftSerializer, operation="update")):
        pass

    category = product_models.Category.objects.create(name="DriftCat")
    item = product_models.Item.objects.create(name="DriftItem", category=category)

    def drifting_kwargs(
        self,
        info,
        *,
        data,
        hook_context,
    ):
        item.name = "smuggled-by-hook"  # setattr the located row before the save
        return {"data": data}

    DriftingMutation.get_serializer_kwargs = drifting_kwargs
    with write_pipeline("default", lock=False):
        require_write_pipeline().target_state = snapshot_target_state(item)
        with pytest.raises(ConfigurationError, match="mutated in memory"):
            serializer_resolvers._serializer_write_step(
                DriftingMutation,
                _info(),
                item,
                {"name": "LegitName"},
            )


@pytest.mark.django_db
def test_save_kwargs_naming_a_model_field_is_rejected():
    """A save kwarg naming ANY model field is rejected (injection goes through injected_fields)."""

    class PlainSerializer(serializers.ModelSerializer):
        class Meta:
            model = product_models.Item
            fields = ("name", "category")

    mutation_cls = _bind_item_serializer_mutation(PlainSerializer)

    def model_field_save_kwargs(
        self,
        info,
        *,
        data,
        hook_context,
    ):
        return {"is_private": True}  # an Item column never validated or visibility-checked

    mutation_cls.get_serializer_save_kwargs = model_field_save_kwargs
    category = product_models.Category.objects.create(name="SaveKwargCat")
    with write_pipeline("default", lock=False):
        with pytest.raises(ConfigurationError, match="model field"):
            serializer_resolvers._serializer_write_step(
                mutation_cls,
                _info(),
                None,
                {"name": "SaveKwargItem", "category": category.pk},
            )
    assert not product_models.Item.objects.filter(name="SaveKwargItem").exists()


def test_flattener_survives_error_depth_beyond_the_recursion_limit():
    """The flattener is ITERATIVE: a deeper-than-recursion-limit error tree must not crash."""
    import sys

    depth = sys.getrecursionlimit() + 200
    errors: dict = {"leaf": ["boom"]}
    for _ in range(depth):
        errors = {"child": errors}

    flattened = serializer_resolvers.serializer_errors_to_field_errors(errors, {})
    assert len(flattened) == 1
    assert flattened[0].messages == ["boom"]


def test_flattener_rejects_a_cyclic_error_structure():
    """A CYCLIC detail structure (author-built ValidationError) fails loud, never loops."""
    cyclic: dict = {"name": ["msg"]}
    cyclic["self"] = cyclic
    with pytest.raises(ConfigurationError, match="CYCLIC detail structure"):
        serializer_resolvers.serializer_errors_to_field_errors(cyclic, {})


def test_flattener_truncates_past_the_node_budget():
    """Pathological fan-out ends in ONE ``__all__`` ``truncated`` marker, not unbounded work."""
    wide = {
        str(index): ["m"] for index in range(serializer_resolvers._ERROR_FLATTEN_NODE_BUDGET + 10)
    }
    flattened = serializer_resolvers.serializer_errors_to_field_errors(wide, {})
    assert flattened[-1].field == NON_FIELD_ERROR_KEY
    assert flattened[-1].codes == ["truncated"]
    assert len(flattened) <= serializer_resolvers._ERROR_FLATTEN_NODE_BUDGET + 1


@pytest.mark.django_db
def test_nested_relation_substitution_is_rejected_per_item():
    """A nested ``many=True`` child's validator swapping ONE item's relation fails closed.

    The ledger records one entry PER ITEM (the same child field instance validates every
    list item), and the intent walk consumes them in item order - so a swap in the second
    item is caught even though the first item is intact.
    """
    genres = [
        library_models.Genre.objects.create(name=f"NestedGenre{index}") for index in range(3)
    ]
    hidden = genres[2]

    class ChildSerializer(serializers.Serializer):
        genre = serializers.PrimaryKeyRelatedField(queryset=library_models.Genre.objects.all())

        def validate_genre(self, value):
            if value.pk == genres[1].pk:
                return library_models.Genre.objects.get(pk=hidden.pk)  # swap item 2 only
            return value

    class ParentSerializer(serializers.Serializer):
        items = ChildSerializer(many=True)

    child_spec = SimpleNamespace(
        kind=serializer_resolvers.RELATION_SINGLE,
        target_name="genre",
        source=None,
        nested_specs=None,
    )
    parent_spec = SimpleNamespace(
        kind=serializer_resolvers.NESTED_MULTI,
        target_name="items",
        source=None,
        nested_specs=[child_spec],
    )
    fake_mut = SimpleNamespace(
        __name__="NestedLedgerMut",
        _input_field_specs=[parent_spec],
        _injected_field_specs=None,
    )

    serializer = ParentSerializer(
        data={"items": [{"genre": genres[0].pk}, {"genre": genres[1].pk}]},
    )
    ledger = serializer_resolvers._instrument_relation_intent(fake_mut, serializer)
    assert serializer.is_valid(), serializer.errors
    with pytest.raises(ConfigurationError, match="replaced a visibility-checked relation"):
        serializer_resolvers._assert_relation_intent(fake_mut, serializer, ledger)

    # The intact twin: no swap, two items, records consumed in order, no raise.
    serializer = ParentSerializer(
        data={"items": [{"genre": genres[0].pk}, {"genre": genres[2].pk}]},
    )
    ledger = serializer_resolvers._instrument_relation_intent(fake_mut, serializer)
    assert serializer.is_valid(), serializer.errors
    serializer_resolvers._assert_relation_intent(fake_mut, serializer, ledger)

    # A GENUINELY omitted optional nested field produces no records (its child
    # fields never validate), so the fully-consumed backstop passes.
    class OptionalParentSerializer(serializers.Serializer):
        items = ChildSerializer(many=True, required=False)

    serializer = OptionalParentSerializer(data={})
    ledger = serializer_resolvers._instrument_relation_intent(fake_mut, serializer)
    assert serializer.is_valid(), serializer.errors
    serializer_resolvers._assert_relation_intent(fake_mut, serializer, ledger)


@pytest.mark.django_db
def test_nested_relation_nulled_after_validation_is_rejected():
    """A parent validator that NULLS a nested value after its children resolved fails closed.

    The child relation field validates (recording its resolved object), then a parent
    validator drops the whole nested value; the recorded intent goes unconsumed, and the
    fully-consumed backstop rejects the silent discard (the direct-pop guard cannot see a
    removal one level down - it never recurses into a value that is gone).
    """
    genre = library_models.Genre.objects.create(name="NulledNestedGenre")

    class ChildSerializer(serializers.Serializer):
        genre = serializers.PrimaryKeyRelatedField(queryset=library_models.Genre.objects.all())

    class NullingParentSerializer(serializers.Serializer):
        items = ChildSerializer(many=True)

        def validate(self, attrs):
            attrs["items"] = None  # drop the whole nested value post-validation
            return attrs

    child_spec = SimpleNamespace(
        kind=serializer_resolvers.RELATION_SINGLE,
        target_name="genre",
        source=None,
        nested_specs=None,
    )
    parent_spec = SimpleNamespace(
        kind=serializer_resolvers.NESTED_MULTI,
        target_name="items",
        source=None,
        nested_specs=[child_spec],
    )
    fake_mut = SimpleNamespace(
        __name__="NulledNestedMut",
        _input_field_specs=[parent_spec],
        _injected_field_specs=None,
    )

    serializer = NullingParentSerializer(data={"items": [{"genre": genre.pk}]})
    ledger = serializer_resolvers._instrument_relation_intent(fake_mut, serializer)
    assert serializer.is_valid(), serializer.errors
    with pytest.raises(ConfigurationError, match="removed from validated_data before the write"):
        serializer_resolvers._assert_relation_intent(fake_mut, serializer, ledger)


def test_upload_metadata_tolerates_a_sizeless_file():
    """A file object whose ``size`` read raises reports ``size=None`` (never an exception)."""
    from django.core.files import File

    metadata = serializer_resolvers._upload_metadata(File(None, name="ghost.bin"))
    assert isinstance(metadata, UploadMetadata)
    assert metadata.name == "ghost.bin"
    assert metadata.size is None


@pytest.mark.django_db
def test_attestation_skips_serializer_only_and_non_matching_sources():
    """Attestation skips relation specs whose source is not a (matching) model field.

    A serializer-only relation (source not a model field) has nothing on the row to
    attest; a ``RELATION_MULTI`` spec whose source is a FK (not an M2M) - or vice versa -
    is a shape the agreement guard already polices, so the attestation just skips it.
    """
    category = product_models.Category.objects.create(name="SkipCat")
    item = product_models.Item.objects.create(name="SkipItem", category=category)

    ghost_single = SimpleNamespace(
        kind=serializer_resolvers.RELATION_SINGLE,
        target_name="ghost",
        source="not_a_field",
        nested_specs=None,
    )
    ghost_multi = SimpleNamespace(
        kind=serializer_resolvers.RELATION_MULTI,
        target_name="ghosts",
        source="also_missing",
        nested_specs=None,
    )
    fk_as_multi = SimpleNamespace(
        kind=serializer_resolvers.RELATION_MULTI,
        target_name="cat_as_multi",
        source="category",
        nested_specs=None,
    )
    scalar_as_single = SimpleNamespace(
        kind=serializer_resolvers.RELATION_SINGLE,
        target_name="name",
        source="name",
        nested_specs=None,
    )
    absent_single = SimpleNamespace(
        kind=serializer_resolvers.RELATION_SINGLE,
        target_name="absent_cat",
        source="category",
        nested_specs=None,
    )
    fake_mut = SimpleNamespace(
        __name__="SkipMut",
        _mutation_meta=SimpleNamespace(model=product_models.Item),
        _input_field_specs=[
            ghost_single,
            ghost_multi,
            fk_as_multi,
            scalar_as_single,
            absent_single,
        ],
        _injected_field_specs=None,
    )
    fake_serializer = SimpleNamespace(fields={}, validated_data={})
    # The manifest names the in-scope specs (so their skip paths are exercised) but
    # NOT ``absent_cat`` (a relation the client never supplied is simply absent).
    # No raise, no query: serializer-only sources (FieldDoesNotExist), a scalar
    # source (not a relation), and an FK-shaped source under a MULTI spec (not an
    # M2M) are all skipped; the absent spec is never looked at.
    serializer_resolvers._attest_saved_relations(
        fake_mut,
        fake_serializer,
        item,
        alias="default",
        m2m_before={},
        relation_pks={
            "ghost": 1,
            "ghosts": frozenset({1}),
            "cat_as_multi": frozenset({1}),
            "name": 1,
        },
    )


@pytest.mark.django_db
def test_attestation_rejects_a_cleared_fk_that_was_not_cleared():
    """A validated ``None`` FK attests the DATABASE column is null; a set column fails."""
    category = product_models.Category.objects.create(name="NullCat")
    item = product_models.Item.objects.create(name="NullItem", category=category)

    fk_spec = SimpleNamespace(
        kind=serializer_resolvers.RELATION_SINGLE,
        target_name="category",
        source="category",
        nested_specs=None,
    )
    fake_mut = SimpleNamespace(
        __name__="NullMut",
        _mutation_meta=SimpleNamespace(model=product_models.Item),
        _input_field_specs=[fk_spec],
        _injected_field_specs=None,
    )
    fake_serializer = SimpleNamespace(fields={}, validated_data={"category": None})
    with pytest.raises(ConfigurationError, match="ignored or replaced a validated relation"):
        serializer_resolvers._attest_saved_relations(
            fake_mut,
            fake_serializer,
            item,
            alias="default",
            m2m_before={},
            relation_pks={"category": None},  # captured null intent
        )
