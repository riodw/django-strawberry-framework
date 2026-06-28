"""Tests for the shared generated-input substrate (``utils/inputs.py``).

The 0.0.9 DRY pass single-sited the neutral generated-input mechanics that the
filter and order families had grown as parallel copies. These tests pin the
substrate directly and assert that BOTH families route through the one builder /
field-spec / camel-name path, so a future re-divergence is caught here rather
than via a silently drifted second copy (``docs/feedback.md`` Major 1).
"""

import sys

import pytest

from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.utils.inputs import (
    GeneratedInputFieldSpec,
    InputFieldSpec,
    build_strawberry_input_class,
    graphql_camel_name,
    iter_set_subclasses,
    make_input_namespace,
    make_shape_build_cache,
    materialize_generated_input_class,
)

# ---------------------------------------------------------------------------
# build_strawberry_input_class
# ---------------------------------------------------------------------------


def test_build_strawberry_input_class_emits_name_alias_and_description():
    """``name=`` lands as the GraphQL alias and ``description=`` on the field."""
    cls = build_strawberry_input_class(
        "SharedScratchInputType",
        [
            ("in_", list[int] | None, {"name": "in", "default": None}),
            ("note", str | None, {"default": None, "description": "a note"}),
        ],
    )
    assert hasattr(cls, "__strawberry_definition__")
    fields = cls.__strawberry_definition__.fields
    assert any(field.graphql_name == "in" for field in fields)
    note = next(field for field in fields if field.python_name == "note")
    assert note.description == "a note"


# ---------------------------------------------------------------------------
# graphql_camel_name
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("galaxy_name", "galaxyName"),
        ("shelf_code", "shelfCode"),
        ("", ""),
        ("_", "_"),
        ("__", "__"),
    ],
)
def test_graphql_camel_name(value, expected):
    """Head lowercased, rest PascalCased; no-word-token inputs pass through."""
    assert graphql_camel_name(value) == expected


# ---------------------------------------------------------------------------
# Single-siting: both families share ONE substrate path
# ---------------------------------------------------------------------------


def test_filter_and_order_families_share_one_substrate():
    """Both ``inputs`` modules re-export the SAME shared mechanics by identity.

    This is the DRY contract guard: if a future change re-introduces a
    family-local copy of the builder / field-spec / camel-name / subclass
    iterator, these identity assertions fail.
    """
    from django_strawberry_framework.filters import inputs as filter_inputs
    from django_strawberry_framework.orders import inputs as order_inputs

    assert filter_inputs.FieldSpec is GeneratedInputFieldSpec
    assert order_inputs.FieldSpec is GeneratedInputFieldSpec
    assert filter_inputs.build_input_class is build_strawberry_input_class
    assert order_inputs.build_input_class is build_strawberry_input_class
    assert filter_inputs._camel_case is graphql_camel_name
    assert order_inputs._camel_case is graphql_camel_name
    assert filter_inputs._iter_filterset_subclasses is iter_set_subclasses
    assert order_inputs._iter_orderset_subclasses is iter_set_subclasses


# ---------------------------------------------------------------------------
# materialize_generated_input_class -- family-labelled collision
# ---------------------------------------------------------------------------


def test_materialize_generated_input_class_names_family_in_collision():
    """The collision message is parameterized by ``family_label``.

    Proves the family-specific wording (``FilterSet`` / ``OrderSet``) is a
    parameter of the shared helper, not hard-coded -- using a throwaway label
    and a real (this) module so the ``setattr`` target exists.
    """
    module_path = __name__
    module = sys.modules[module_path]
    ledger: dict[str, type] = {}

    class _WidgetA:
        pass

    class _WidgetB:
        pass

    materialize_generated_input_class(
        "WidgetSubstrateInputType",
        _WidgetA,
        module_path=module_path,
        family_label="WidgetSet",
        ledger=ledger,
    )
    # Idempotent on the same pair.
    materialize_generated_input_class(
        "WidgetSubstrateInputType",
        _WidgetA,
        module_path=module_path,
        family_label="WidgetSet",
        ledger=ledger,
    )
    with pytest.raises(ConfigurationError, match="two distinct WidgetSet input classes"):
        materialize_generated_input_class(
            "WidgetSubstrateInputType",
            _WidgetB,
            module_path=module_path,
            family_label="WidgetSet",
            ledger=ledger,
        )
    delattr(module, "WidgetSubstrateInputType")


# ---------------------------------------------------------------------------
# iter_set_subclasses
# ---------------------------------------------------------------------------


def test_iter_set_subclasses_dedupes_diamond_inheritance():
    """A diamond hierarchy surfaces each subclass once (the dedup ``continue``)."""

    class Root:
        pass

    class B(Root):
        pass

    class C(Root):
        pass

    class D(B, C):
        pass

    found = iter_set_subclasses(Root)
    assert found.count(D) == 1
    assert {B, C, D}.issubset(set(found))


def test_safe_import_returns_none_for_unimportable_module():
    """``_safe_import`` swallows ImportError so a partial-load clear continues.

    A ``None`` entry in ``sys.modules`` makes the import raise ImportError --
    the same way the family ``clear_*_input_namespace`` tolerance tests simulate
    an unreachable submodule.
    """
    from django_strawberry_framework.utils.inputs import _safe_import

    fake_name = "django_strawberry_framework._nonexistent_substrate_probe"
    saved = sys.modules.get(fake_name)
    try:
        sys.modules[fake_name] = None
        assert _safe_import(fake_name, "anything") is None
    finally:
        if saved is None:
            sys.modules.pop(fake_name, None)
        else:
            sys.modules[fake_name] = saved


# ---------------------------------------------------------------------------
# spec-039 promotions: InputFieldSpec / make_input_namespace / make_shape_build_cache
# ---------------------------------------------------------------------------


def test_input_field_spec_carries_five_axes_and_optional_source():
    """``InputFieldSpec`` (P2.1) carries the five axes + the optional ``source`` (default ``None``)."""
    # Default source is None (the form-symmetric shape, no source axis).
    no_source = InputFieldSpec(
        input_attr="name",
        graphql_name="name",
        target_name="name",
        kind="scalar",
    )
    assert no_source.source is None
    # The serializer-only ``source`` axis carries the resolved one-segment source.
    with_source = InputFieldSpec(
        input_attr="category_pk",
        graphql_name="categoryPk",
        target_name="category_pk",
        kind="relation_single",
        source="category",
    )
    assert with_source.source == "category"
    assert with_source.input_attr == "category_pk"
    assert with_source.graphql_name == "categoryPk"
    assert with_source.target_name == "category_pk"
    assert with_source.kind == "relation_single"
    # Frozen.
    with pytest.raises((AttributeError, TypeError)):
        with_source.source = "other"


def test_make_input_namespace_returns_ledger_materialize_clear_trio():
    """``make_input_namespace`` (P2.2) returns ``(ledger, materialize, clear)``; clear empties the ledger.

    ``materialize`` writes a real module global; ``clear`` empties only the ledger
    (the one-ledger shape, NOT the heavy ``clear_generated_input_namespace``). Uses
    THIS test module as the ``setattr`` target so the global slot exists.
    """
    module_path = __name__
    module = sys.modules[module_path]
    ledger, materialize, clear = make_input_namespace(module_path, "ProbeFamily")
    assert ledger == {}

    class _ProbeInput:
        pass

    materialize("ProbeNamespaceInputType", _ProbeInput)
    assert ledger["ProbeNamespaceInputType"] is _ProbeInput
    assert module.ProbeNamespaceInputType is _ProbeInput
    # Idempotent on the same pair; a distinct class under one name raises (the
    # ledger collision, named by the family label).
    materialize("ProbeNamespaceInputType", _ProbeInput)

    class _OtherProbe:
        pass

    with pytest.raises(ConfigurationError, match="two distinct ProbeFamily input classes"):
        materialize("ProbeNamespaceInputType", _OtherProbe)

    clear()
    assert ledger == {}
    # The materialized global stays PARKED (not delattr'd) per the lifecycle.
    assert module.ProbeNamespaceInputType is _ProbeInput
    delattr(module, "ProbeNamespaceInputType")


def test_make_shape_build_cache_returns_dict_and_clear():
    """``make_shape_build_cache`` (P1.3) returns a ``(dict, clear)`` pair; clear empties the dict."""
    cache, clear = make_shape_build_cache()
    assert cache == {}
    cache[("Model", "create", frozenset({"a"}))] = object()
    assert len(cache) == 1
    clear()
    assert cache == {}
