"""Tests for the shared write-value decoding substrate."""

import pytest
import strawberry
from apps.products.models import Category

from django_strawberry_framework.registry import registry
from django_strawberry_framework.utils.inputs import InputFieldSpec
from django_strawberry_framework.utils.write_values import (
    decode_provided_fields,
    decode_scalar_leaf,
    decode_visible_relation,
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
