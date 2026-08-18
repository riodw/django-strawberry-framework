"""Tests for the shared write-value decoding substrate."""

from enum import Enum

import pytest
import strawberry
from apps.products.models import Category

from django_strawberry_framework.registry import registry
from django_strawberry_framework.utils.errors import field_error
from django_strawberry_framework.utils.inputs import (
    FILE,
    RELATION_MULTI,
    RELATION_SINGLE,
    SCALAR,
    InputFieldSpec,
)
from django_strawberry_framework.utils.write_values import (
    decode_field_handlers,
    decode_provided_fields,
    decode_scalar_leaf,
    decode_visible_relation,
    decode_visible_relation_ids,
    decoded_into,
    file_into,
    relation_into,
    scalar_into,
    store_decoded,
)


@strawberry.input
class _TriStateInput:
    scalar: str | None = strawberry.UNSET
    relation: int | None = strawberry.UNSET


_TRI_STATE_SPECS = [
    InputFieldSpec(
        input_attr="scalar",
        graphql_name="scalar",
        target_name="scalar",
        kind="scalar",
    ),
    InputFieldSpec(
        input_attr="relation",
        graphql_name="relation",
        target_name="relation",
        kind="relation",
        related_model=Category,
    ),
]


@pytest.fixture(autouse=True)
def _isolate_registry():
    registry.clear()
    yield
    registry.clear()


@pytest.mark.django_db
def test_decode_layers_preserve_omitted_null_and_provided_values():
    """The shared gate never collapses omitted, explicit-null, and provided input states."""
    decoded: dict[str, object] = {}

    def relation_handler(spec, value):
        result, error = decode_visible_relation(
            value,
            graphql_name=spec.graphql_name,
            related_model=spec.related_model,
            info=None,
            async_recourse="Use a synchronous visibility hook.",
            skip=lambda candidate: candidate is None,
            project=lambda obj: obj.pk,
        )
        if error is None:
            decoded[spec.input_attr] = result
        return error

    def scalar_handler(spec, value):
        result, error = decode_scalar_leaf(spec.graphql_name, value)
        if error is None:
            decoded[spec.input_attr] = result
        return error

    error = decode_provided_fields(
        _TRI_STATE_SPECS,
        _TriStateInput(),
        handlers={"relation": relation_handler},
        scalar_handler=scalar_handler,
    )
    assert error is None
    assert decoded == {}

    error = decode_provided_fields(
        _TRI_STATE_SPECS,
        _TriStateInput(scalar=None, relation=None),
        handlers={"relation": relation_handler},
        scalar_handler=scalar_handler,
    )
    assert error is None
    assert decoded == {"scalar": None, "relation": None}

    category = Category.objects.create(name="TriState")
    error = decode_provided_fields(
        _TRI_STATE_SPECS,
        _TriStateInput(scalar="provided", relation=category.pk),
        handlers={"relation": relation_handler},
        scalar_handler=scalar_handler,
    )
    assert error is None
    assert decoded == {"scalar": "provided", "relation": category.pk}


@pytest.mark.django_db
def test_decode_visible_relation_ids_batches_visibility_and_short_circuits():
    """The batched compose type-checks first, queries once, and maps misses to one error."""
    from django.db import connection
    from django.test.utils import CaptureQueriesContext

    first = Category.objects.create(name="BatchA")
    second = Category.objects.create(name="BatchB")
    recourse = "Use a synchronous visibility hook."

    pks, error = decode_visible_relation_ids(
        [],
        graphql_name="categoryIds",
        related_model=Category,
        info=None,
        async_recourse=recourse,
    )
    assert error is None
    assert pks == []

    with CaptureQueriesContext(connection) as ctx:
        pks, error = decode_visible_relation_ids(
            [first.pk, second.pk],
            graphql_name="categoryIds",
            related_model=Category,
            info=None,
            async_recourse=recourse,
        )
    assert error is None
    assert pks == [first.pk, second.pk]
    assert len(ctx.captured_queries) == 1

    pks, error = decode_visible_relation_ids(
        [first.pk, "bad"],
        graphql_name="categoryIds",
        related_model=Category,
        info=None,
        async_recourse=recourse,
    )
    assert pks is None
    assert error is not None
    assert error.field == "categoryIds"


def test_decode_visible_relation_ids_maps_malformed_containers_to_relation_error():
    """A non-iterable or iterator failure stays inside the field error envelope."""

    class HostileIterator:
        def __iter__(self):
            raise RuntimeError("hostile relation iterator")

    for values in (object(), HostileIterator()):
        pks, error = decode_visible_relation_ids(
            values,
            graphql_name="categoryIds",
            related_model=Category,
            info=None,
            async_recourse="Use a synchronous visibility hook.",
        )
        assert pks is None
        assert error is not None
        assert error.field == "categoryIds"


def _spec(
    *,
    attr: str,
    kind: str,
    target: str | None = None,
    graphql: str | None = None,
):
    return InputFieldSpec(
        input_attr=attr,
        graphql_name=graphql or attr,
        target_name=target or attr,
        kind=kind,
        related_model=object if kind in {RELATION_SINGLE, RELATION_MULTI} else None,
    )


def test_store_decoded_writes_target_or_returns_error():
    """The store glue writes ``target_name`` on success and leaves dest untouched on error."""
    dest: dict[str, object] = {}
    spec = _spec(attr="name", kind=SCALAR, target="title", graphql="displayName")
    assert store_decoded(dest, spec, ("ok", None)) is None
    assert dest == {"title": "ok"}

    error = field_error("displayName", "nope", codes="invalid")
    dest.clear()
    assert store_decoded(dest, spec, (None, error)) is error
    assert dest == {}


def test_decode_scalar_leaf_rejects_hostile_string_subclass_encoding():
    """Unicode preflight must not dispatch a consumer string subclass's ``encode``."""

    class HostileText(str):
        def encode(self, *args, **kwargs):
            return b""

    decoded, error = decode_scalar_leaf("name", HostileText("\ud800"))
    assert decoded is None
    assert error is not None
    assert error.field == "name"


def test_decode_scalar_leaf_normalizes_string_subclass_after_preflight():
    """A valid string subclass is stored as an exact ``str``, not consumer code."""

    class HostileText(str):
        def __str__(self):
            raise AssertionError("storage must not dispatch the override")

    decoded, error = decode_scalar_leaf("name", HostileText("valid"))
    assert error is None
    assert type(decoded) is str
    assert decoded == "valid"


def test_decode_scalar_leaf_checks_choice_value_after_unwrapping():
    """An enum's raw storage string receives the Unicode preflight."""

    class InvalidTextChoice(Enum):
        broken = "\ud800"

    decoded, error = decode_scalar_leaf("status", InvalidTextChoice.broken)
    assert decoded is None
    assert error is not None
    assert error.field == "status"
    assert error.codes == ["invalid"]


def test_scalar_into_stores_decoded_leaf_and_keys_errors_to_field_name():
    """SCALAR handlers share ``decode_scalar_leaf`` + ``store_decoded``; nested paths rekey."""
    dest: dict[str, object] = {}
    spec = _spec(attr="name", kind=SCALAR, target="title", graphql="displayName")
    handler = scalar_into(dest)
    assert handler(spec, "ok") is None
    assert dest == {"title": "ok"}

    dest.clear()
    error = handler(spec, "\ud800")
    assert error is not None
    assert error.field == "displayName"
    assert dest == {}

    nested = scalar_into(dest, field_name=lambda item: f"parent.{item.graphql_name}")
    error = nested(spec, "\ud800")
    assert error is not None
    assert error.field == "parent.displayName"


def test_file_into_stores_upload_on_the_supplied_dest():
    """FILE destination is the flavor policy: form ``files=`` vs serializer ``data``."""
    files: dict[str, object] = {}
    data: dict[str, object] = {}
    spec = _spec(attr="attachment", kind=FILE, target="attachment")
    upload = object()
    assert file_into(files)(spec, upload) is None
    assert files == {"attachment": upload}
    assert data == {}
    assert file_into(data)(spec, upload) is None
    assert data == {"attachment": upload}


def test_relation_into_dispatches_single_and_multi_then_stores():
    """One relation handler picks multi vs single, forwards extras, and stores the result."""
    dest: dict[str, object] = {}
    calls: list[tuple] = []

    def single(value, *, graphql_name, related_model, info, **extra):
        calls.append(
            (
                "single",
                value,
                graphql_name,
                info,
                extra,
            ),
        )
        return f"s-{value}", None

    def multi(value, *, graphql_name, related_model, info, **extra):
        calls.append(
            (
                "multi",
                value,
                graphql_name,
                info,
                extra,
            ),
        )
        return ["m", value], None

    spec_single = _spec(
        attr="category_id",
        kind=RELATION_SINGLE,
        target="category",
        graphql="categoryId",
    )
    spec_multi = _spec(attr="tag_ids", kind=RELATION_MULTI, target="tags", graphql="tagIds")
    handler = relation_into(
        dest,
        single=single,
        multi=multi,
        info="info",
        extra=lambda spec: {"form_field": spec.target_name},
    )
    assert handler(spec_single, 7) is None
    assert dest["category"] == "s-7"
    assert calls[0] == (
        "single",
        7,
        "categoryId",
        "info",
        {"form_field": "category"},
    )
    assert handler(spec_multi, [1, 2]) is None
    assert dest["tags"] == ["m", [1, 2]]
    assert calls[1] == (
        "multi",
        [1, 2],
        "tagIds",
        "info",
        {"form_field": "tags"},
    )

    dest.clear()

    def failing(value, *, graphql_name, related_model, info, **extra):
        return None, field_error(graphql_name, "hidden", codes="invalid")

    error_handler = relation_into(dest, single=failing, multi=failing, info=None)
    error = error_handler(spec_single, 7)
    assert error is not None
    assert error.field == "categoryId"
    assert dest == {}


def test_decoded_into_is_the_store_glue_nested_handlers_use():
    """Nested serializer decode is the same store primitive as SCALAR / FILE / RELATION."""
    dest: dict[str, object] = {}
    spec = _spec(attr="shelves", kind="nested_single", target="shelves")
    handler = decoded_into(
        dest,
        lambda item, value: ({"n": value, "k": item.target_name}, None),
    )
    assert handler(spec, {"title": "A"}) is None
    assert dest == {"shelves": {"n": {"title": "A"}, "k": "shelves"}}


def test_decode_field_handlers_split_files_from_data():
    """The compose both walks call: FILE dest is optional; SCALAR/RELATION share dest."""
    data: dict[str, object] = {}
    files: dict[str, object] = {}
    scalar_spec = _spec(attr="name", kind=SCALAR, target="name")
    file_spec = _spec(attr="attachment", kind=FILE, target="attachment")
    relation_spec = _spec(attr="category_id", kind=RELATION_SINGLE, target="category")

    def single(value, *, graphql_name, related_model, info, **extra):
        return f"pk-{value}", None

    def multi(value, *, graphql_name, related_model, info, **extra):
        raise AssertionError("multi should not run")

    handlers, scalar_handler = decode_field_handlers(
        data,
        info=None,
        single=single,
        multi=multi,
        file_dest=files,
    )
    assert scalar_handler(scalar_spec, "Widget") is None
    assert handlers[FILE](file_spec, "upload") is None
    assert handlers[RELATION_SINGLE](relation_spec, 3) is None
    assert data == {"name": "Widget", "category": "pk-3"}
    assert files == {"attachment": "upload"}


def test_form_and_serializer_decode_walks_share_field_handlers():
    """Form and serializer decode walks import the same store-into-dest compose."""
    from django_strawberry_framework.forms import resolvers as form_resolvers
    from django_strawberry_framework.rest_framework import resolvers as serializer_resolvers

    assert form_resolvers.decode_field_handlers is decode_field_handlers
    assert serializer_resolvers.decode_field_handlers is decode_field_handlers
    assert serializer_resolvers.decoded_into is decoded_into
    assert form_resolvers.decode_provided_fields is decode_provided_fields
    assert serializer_resolvers.decode_provided_fields is decode_provided_fields
