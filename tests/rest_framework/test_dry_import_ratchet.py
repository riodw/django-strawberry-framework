"""The serializer flavor IMPORTS its shared substrate; it never redefines it (spec-039).

`rest_framework/inputs.py` and `rest_framework/serializer_converter.py` are assembled
from the shared input / converter / string helpers and the shared field-spec and
conversion shapes rather than carrying their own copies, and the four input-kind
constants are single-sourced in `utils/inputs.py`. That
is a structural property with no reachable line in `django_strawberry_framework`, so no
real GraphQL query can earn it; it is pinned here instead.

The instrument is OBJECT IDENTITY, not a source grep: a grep is satisfied by a
same-named local with a copied body and breaks on a legitimate import-style change,
while identity catches the redefinition AND the deletion. Factory-produced closures
cannot be object-identical across flavors, so the one-ledger trio's cross-flavor twins
are held by `__code__` identity instead.

When a symbol legitimately moves, edit `SHARED_BINDINGS` / `SHARED_CLOSURE_BODIES`
below deliberately - the manifest is the population this guard covers, and it is meant
to be read against the source.
"""

from __future__ import annotations

import pytest

from django_strawberry_framework.mutations import inputs as mutation_inputs
from django_strawberry_framework.rest_framework import inputs as serializer_inputs
from django_strawberry_framework.rest_framework import serializer_converter
from django_strawberry_framework.utils import converters as utils_converters
from django_strawberry_framework.utils import inputs as utils_inputs
from django_strawberry_framework.utils import strings as utils_strings

# (consumer module, symbol, module that owns the single definition)
SHARED_BINDINGS = (
    (serializer_inputs, "InputFieldSpec", utils_inputs),
    (serializer_inputs, "make_input_namespace", utils_inputs),
    (serializer_inputs, "make_shape_build_cache", utils_inputs),
    (serializer_inputs, "get_or_store_shape_build", utils_inputs),
    (serializer_inputs, "build_strawberry_input_class", utils_inputs),
    (serializer_inputs, "pascalize_token", utils_inputs),
    (serializer_inputs, "normalize_field_name_sequence", utils_inputs),
    (serializer_inputs, "graphql_camel_name", utils_strings),
    (serializer_converter, "convert_with_mro", utils_converters),
    (serializer_converter, "make_kind_converter", utils_converters),
    (serializer_converter, "make_scalar_converter", utils_converters),
    (serializer_converter, "finish_field_conversion", utils_converters),
    (serializer_converter, "FieldConversionBase", utils_inputs),
    (serializer_converter, "InputFieldSpec", utils_inputs),
    (serializer_converter, "SCALAR", utils_inputs),
    (serializer_converter, "FILE", utils_inputs),
    (serializer_converter, "RELATION_SINGLE", utils_inputs),
    (serializer_converter, "RELATION_MULTI", utils_inputs),
    (serializer_converter, "graphql_camel_name", utils_strings),
)

# (consumer module, symbol, the flavor twin whose factory produced the same body)
SHARED_CLOSURE_BODIES = (
    (serializer_inputs, "_materialize_input", mutation_inputs),
    (serializer_inputs, "_clear_input_namespace", mutation_inputs),
)


def _row_id(row):
    """`inputs.pascalize_token` - the module tail plus the symbol, unique per row."""
    module, symbol, _owner = row
    return f"{module.__name__.rsplit('.', 1)[-1]}.{symbol}"


def _bound(module, symbol):
    """Return `module`'s binding for `symbol`, failing (never erroring) when absent."""
    namespace = vars(module)
    if symbol not in namespace:
        pytest.fail(f"{module.__name__} binds no {symbol!r}; the shared symbol was dropped.")
    return namespace[symbol]


@pytest.mark.parametrize(
    "consumer,symbol,owner",
    SHARED_BINDINGS,
    ids=[_row_id(row) for row in SHARED_BINDINGS],
)
def test_serializer_flavor_binds_the_shared_object_itself(consumer, symbol, owner):
    """The consumer's name IS the owner's object - not an equal-looking local copy."""
    assert _bound(consumer, symbol) is _bound(owner, symbol), (
        f"{consumer.__name__}.{symbol} is no longer {owner.__name__}.{symbol}; "
        "import the shared symbol instead of redefining it."
    )


@pytest.mark.parametrize(
    "consumer,symbol,twin",
    SHARED_CLOSURE_BODIES,
    ids=[_row_id(row) for row in SHARED_CLOSURE_BODIES],
)
def test_serializer_flavor_closures_share_one_body(consumer, symbol, twin):
    """Factory-produced closures differ as objects, so the BODY is what must be one."""
    assert _bound(consumer, symbol).__code__ is _bound(twin, symbol).__code__, (
        f"{consumer.__name__}.{symbol} no longer shares a body with "
        f"{twin.__name__}.{symbol}; build both from the one factory."
    )
