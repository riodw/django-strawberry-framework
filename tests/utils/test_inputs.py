"""Tests for the shared generated-input substrate (``utils/inputs.py``).

This module single-sites the neutral generated-input mechanics that the filter
and order families had grown as parallel copies. These tests pin the substrate
directly and assert that BOTH families route through the one builder /
field-spec / camel-name path, so a future re-divergence is caught here rather
than via a silently drifted second copy.
"""

import sys
from types import SimpleNamespace

import pytest
import strawberry

from django_strawberry_framework import strawberry_config
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.utils.inputs import (
    GeneratedInputFieldSpec,
    InputFieldSpec,
    build_strawberry_input_class,
    create_dynamic_set_class,
    emit_set_input_field_triples,
    graphql_camel_name,
    iter_input_field_collisions,
    iter_set_subclasses,
    make_dynamic_set_getter,
    make_hashable_meta_value,
    make_input_namespace,
    make_set_input_namespace,
    make_set_meta_cache_key,
    make_shape_build_cache,
    materialize_generated_input_class,
    normalize_set_meta_for_factory,
    pascalize_token,
    set_input_type_name,
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


def test_builder_pins_names_so_digit_boundary_fields_do_not_silently_collide():
    """A ``field_2`` / ``field2`` pair survives as two distinct GraphQL input fields.

    Regression for the silent collision caused by leaving an identity ``name=``
    alias to Strawberry's converter.
    ``graphql_camel_name`` keeps ``field_2`` and ``field2`` distinct (the injective
    camel-name convention), and the emit collision guard compares those values, so
    it does NOT reject the pair. But when the alias was emitted only on divergence,
    ``field_2`` (equal to its own camel-name) carried no ``name=``, so Strawberry's
    ``NameConverter`` collapsed it to ``field2`` -- overwriting the sibling ``field2``
    and dropping one consumer-declared field from the public schema with no error.
    The shared builder now pins every field's package-derived name, so both survive.
    """

    class _ProbeSet:  # stand-in set class; only ``__qualname__`` is read (error path).
        pass

    entries = [("field_2", object()), ("field2", object())]
    field_specs: dict = {}
    triples = emit_set_input_field_triples(
        _ProbeSet,
        entries,
        related_target_of=lambda _t, _e: (False, None),
        related_source_path_of=lambda t, _e: t,
        leaf_of=lambda _t, _pa, _e: (int | None, _t),
        input_type_name_for=lambda cls: cls.__name__,
        module_path=__name__,
        field_specs=field_specs,
    )
    assert [triple[0] for triple in triples] == ["field_2", "field2"]

    input_cls = build_strawberry_input_class("ProbeDigitBoundaryInput", triples)

    @strawberry.type
    class Query:
        @strawberry.field
        def probe(self, inp: input_cls) -> int:  # type: ignore[valid-type]
            return 1

    schema = strawberry.Schema(query=Query, config=strawberry_config())
    sdl = schema.as_str()
    block = sdl[sdl.index("input ProbeDigitBoundaryInput") :]
    block = block[: block.index("}")]
    # Both distinct wire names present -- no silent collapse to a single ``field2``.
    assert "field_2:" in block
    assert "field2:" in block
    # The runtime provenance names match the pinned wire names.
    assert field_specs[(_ProbeSet, "field_2")].graphql_name == "field_2"
    assert field_specs[(_ProbeSet, "field2")].graphql_name == "field2"


def test_builder_rejects_duplicate_python_attributes():
    """The last defensive layer rejects a duplicate before the namespace drops a field."""
    with pytest.raises(ConfigurationError, match="input attribute 'same'.*more than once"):
        build_strawberry_input_class(
            "DuplicateAttrInput",
            [("same", int, {}), ("same", str, {})],
        )


def test_builder_rejects_duplicate_effective_graphql_names():
    """Explicit aliases cannot collapse two distinct attrs onto one GraphQL field."""
    with pytest.raises(ConfigurationError, match="same GraphQL field name 'same'"):
        build_strawberry_input_class(
            "DuplicateGraphQLInput",
            [("first", int, {"name": "same"}), ("second", str, {"name": "same"})],
        )


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

    This is the single-substrate contract guard: if a future change re-introduces a
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


def test_safe_import_returns_none_for_missing_attribute_on_importable_module():
    """``_safe_import`` keeps its attr-lenient shape: importable module, absent attr -> ``None``.

    The wrapper deliberately diverges from its ``import_attr_if_importable``
    delegate here (which fails loud on a missing attribute): the partial-load
    lifecycle callers treat a module without the looked-up symbol as "nothing to
    clear", not as a bug.
    """
    from django_strawberry_framework.utils.inputs import _safe_import

    assert _safe_import("django_strawberry_framework.utils.inputs", "_not_a_real_attr") is None


# ---------------------------------------------------------------------------
# spec-039 promotions: InputFieldSpec / make_input_namespace / make_shape_build_cache
# ---------------------------------------------------------------------------


def test_input_field_spec_carries_five_axes_and_optional_source():
    """``InputFieldSpec`` carries the five axes + the optional ``source`` (default ``None``)."""
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
    """``make_input_namespace`` returns ``(ledger, materialize, clear)``; clear empties the ledger.

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


def test_set_input_type_name_delegates_to_type_name_for():
    """``set_input_type_name`` is the one ``<Class>InputType`` derivation site."""

    class _Named:
        @classmethod
        def type_name_for(cls, _field_path=None):
            return f"{cls.__name__}InputType"

    assert set_input_type_name(_Named) == "_NamedInputType"


def test_make_set_input_namespace_returns_heavy_ledger_field_specs_materialize_clear():
    """Heavy quartet: materialize writes the ledger; clear empties ledger AND field_specs.

    Unimportable factory / set modules are tolerated (the same cycle-safe skip
    ``clear_generated_input_namespace`` uses). The materialized global stays
    PARKED -- this is the heavy sibling of ``make_input_namespace``, not a
    ``delattr`` teardown.
    """
    module_path = __name__
    module = sys.modules[module_path]
    ledger, field_specs, materialize, clear = make_set_input_namespace(
        module_path,
        "ProbeSet",
        factory_module="django_strawberry_framework.not_a_real_factory_module",
        factory_class_name="NoFactory",
        collision_registry_attr="_type_probeset_registry",
        set_module="django_strawberry_framework.not_a_real_set_module",
        set_class_name="ProbeSet",
    )
    assert ledger == {}
    assert field_specs == {}

    class _ProbeInput:
        pass

    materialize("ProbeSetInputType", _ProbeInput)
    assert ledger["ProbeSetInputType"] is _ProbeInput
    assert module.ProbeSetInputType is _ProbeInput
    field_specs[(_ProbeInput, "title")] = GeneratedInputFieldSpec(
        python_attr="title",
        graphql_name="title",
        django_source_path="title",
    )
    materialize("ProbeSetInputType", _ProbeInput)

    class _OtherProbe:
        pass

    with pytest.raises(ConfigurationError, match="two distinct ProbeSet input classes"):
        materialize("ProbeSetInputType", _OtherProbe)

    clear()
    assert ledger == {}
    assert field_specs == {}
    assert module.ProbeSetInputType is _ProbeInput
    delattr(module, "ProbeSetInputType")


def test_filter_and_order_input_namespaces_ride_make_set_input_namespace():
    """Both set families unpack the same factory closures and naming helper."""
    from django_strawberry_framework.filters import inputs as filter_inputs
    from django_strawberry_framework.orders import inputs as order_inputs

    assert filter_inputs._input_type_name_for is set_input_type_name
    assert order_inputs._input_type_name_for is set_input_type_name
    assert filter_inputs._materialize_input.__code__ is order_inputs._materialize_input.__code__
    assert (
        filter_inputs._clear_input_namespace.__code__
        is order_inputs._clear_input_namespace.__code__
    )


def test_make_hashable_meta_value_sorts_mixed_dict_keys():
    """Unordered dict keys sort by ``repr`` so mixed types cannot TypeError."""
    result = make_hashable_meta_value({"a": 1, 0: 2})
    assert isinstance(result, tuple)
    assert set(result) == {("a", 1), (0, 2)}


def test_make_hashable_meta_value_keys_opaque_unhashable_by_identity():
    """Values that refuse ``hash()`` discriminate by type-and-object identity."""

    class Policy:
        __hash__ = None

    policy = Policy()
    first = make_hashable_meta_value(policy)
    second = make_hashable_meta_value(policy)
    other = make_hashable_meta_value(Policy())
    assert first == second
    assert first != other
    hash(first)


def test_meta_cache_helpers_bypass_hostile_containers_and_reprs():
    """Cache canonicalization never trusts consumer container hooks or reprs."""

    class _HostileRepr:
        def __repr__(self):
            raise RuntimeError("hostile repr")

    class _HostileDict(dict):
        def items(self):
            raise RuntimeError("hostile items")

    class _HostileSet(set):
        def __iter__(self):
            raise RuntimeError("hostile set iterator")

    class _HostileList(list):
        def __iter__(self):
            raise RuntimeError("hostile list iterator")

    for value in (
        {_HostileRepr()},
        _HostileDict(name="x"),
        _HostileSet(["b", "a"]),
        _HostileList(["b", "a"]),
    ):
        canonical = make_hashable_meta_value(value)
        hash(canonical)

    normalized = normalize_set_meta_for_factory(
        _HostileDict(
            model=object,
            fields=_HostileDict(name=_HostileSet(["exact", "contains"])),
            exclude=_HostileList(["z", "a"]),
        ),
        reserved_keys=frozenset(),
    )
    assert normalized["fields"]["name"] == ["contains", "exact"]
    assert normalized["exclude"] == ["a", "z"]


def test_make_set_meta_cache_key_tags_fields_shape():
    """Dict / sequence / scalar ``fields`` land on distinct tagged key branches."""

    class _Model:
        pass

    dict_key = make_set_meta_cache_key({"model": _Model, "fields": {"name": ["exact"]}})
    seq_key = make_set_meta_cache_key({"model": _Model, "fields": ["name"]})
    raw_key = make_set_meta_cache_key({"model": _Model, "fields": "__all__"})
    assert dict_key[0] is _Model
    assert dict_key[1][0] == "dict"
    assert seq_key[1] == ("seq", ("name",))
    assert raw_key[1] == ("raw", "__all__")
    hash(dict_key)
    hash(seq_key)
    hash(raw_key)


def test_normalize_set_meta_for_factory_promotes_fields_alias_and_strips_reserved():
    """``fields_alias`` promotes when ``fields`` is absent; reserved keys drop."""
    normalized = normalize_set_meta_for_factory(
        {"model": object, "filter_fields": {"b", "a"}, "filterset_base_class": object},
        reserved_keys=frozenset({"filterset_base_class"}),
        fields_alias="filter_fields",
    )
    assert "filter_fields" not in normalized
    assert "filterset_base_class" not in normalized
    assert normalized["fields"] == sorted(["a", "b"], key=repr)


def test_normalize_set_meta_for_factory_prefers_fields_over_alias():
    """When both ``fields`` and the synonym are present, ``fields`` wins."""
    normalized = normalize_set_meta_for_factory(
        {"fields": ["name"], "filter_fields": ["other"]},
        reserved_keys=frozenset(),
        fields_alias="filter_fields",
    )
    assert normalized["fields"] == ["name"]
    assert "filter_fields" not in normalized


def test_create_dynamic_set_class_requires_model():
    """Missing ``model`` fails loud with the family getter's name in the message."""
    with pytest.raises(ConfigurationError, match="get_probeset_class requires `model`"):
        create_dynamic_set_class(
            {"fields": ["name"]},
            set_base_class=object,
            auto_name_suffix="AutoProbe",
            getter_name="get_probeset_class",
            explicit_param="probeset_class",
        )


def test_make_dynamic_set_getter_collapses_equivalent_meta_and_passthroughs_explicit():
    """The Layer-6 skeleton caches equivalent meta and returns an explicit class."""
    from apps.products.models import Category

    class _ProbeSet:
        pass

    cache: dict = {}
    getter = make_dynamic_set_getter(
        cache=cache,
        set_base_class=_ProbeSet,
        auto_name_suffix="AutoProbe",
        getter_name="get_probeset_class",
        reserved_keys=frozenset({"probeset_base_class"}),
        explicit_param="probeset_class",
    )
    first = getter(None, model=Category, fields=["name"])
    second = getter(None, model=Category, fields=("name",))
    assert first is second
    assert first.__name__ == "CategoryAutoProbe"
    assert issubclass(first, _ProbeSet)
    explicit = type("Explicit", (_ProbeSet,), {})
    assert getter(explicit) is explicit
    stripped = getter(None, model=Category, fields=["title"], probeset_base_class=_ProbeSet)
    assert stripped is not first
    assert stripped.__name__ == "CategoryAutoProbe"


@pytest.mark.django_db
def test_filter_and_order_dynamic_caches_ride_make_dynamic_set_getter():
    """Both family getters share the skeleton closures and keep disjoint caches."""
    from apps.products.models import Category

    from django_strawberry_framework.filters import factories as filter_factories
    from django_strawberry_framework.filters.sets import FilterSet
    from django_strawberry_framework.orders import factories as order_factories
    from django_strawberry_framework.orders.sets import OrderSet

    assert filter_factories._make_hashable is make_hashable_meta_value
    assert order_factories._make_hashable is make_hashable_meta_value
    assert filter_factories._make_cache_key is make_set_meta_cache_key
    assert order_factories._make_cache_key is make_set_meta_cache_key
    assert (
        filter_factories._get_filterset_class.__code__
        is order_factories._get_orderset_class.__code__
    )

    filter_factories._dynamic_filterset_cache.clear()
    order_factories._dynamic_orderset_cache.clear()
    try:
        filt = filter_factories.get_filterset_class(None, model=Category, fields=["name"])
        order = order_factories.get_orderset_class(None, model=Category, fields=["name"])
        assert filt is not order
        assert filt.__name__ == "CategoryAutoFilter"
        assert order.__name__ == "CategoryAutoOrder"
        assert issubclass(filt, FilterSet)
        assert issubclass(order, OrderSet)
    finally:
        filter_factories._dynamic_filterset_cache.clear()
        order_factories._dynamic_orderset_cache.clear()


def test_make_shape_build_cache_returns_dict_and_clear():
    """``make_shape_build_cache`` returns a ``(dict, clear)`` pair; clear empties the dict."""
    cache, clear = make_shape_build_cache()
    assert cache == {}
    cache[("Model", "create", frozenset({"a"}))] = object()
    assert len(cache) == 1
    clear()
    assert cache == {}


def test_pascalize_token_is_injective_across_legal_field_name_boundaries():
    """Underscore, digit, and case distinctions survive without interior capitals."""
    assert pascalize_token("") == ""
    assert pascalize_token("is_private") == "Is_uprivate"
    assert pascalize_token("category") == "Category"
    assert pascalize_token("a_b") == "A_ub"
    assert pascalize_token("field2") == "Field2"
    assert pascalize_token("field_2") == "Field_u2"
    assert pascalize_token("Foo") == "X_hfoo"
    assert pascalize_token("2fa") == "X_d2fa"
    assert pascalize_token("\N{LATIN SMALL LETTER E WITH ACUTE}x") == "X_ze9_x"
    assert pascalize_token("a\N{LATIN SMALL LETTER E WITH ACUTE}") == "A_xe9_"
    for left, right in (
        ("a_b", "ab"),
        ("field_2", "field2"),
        ("field2_x", "field2x"),
        ("fooBar", "foobar"),
        ("_foo", "x_foo"),
    ):
        assert pascalize_token(left) != pascalize_token(right)


def test_input_collision_walker_reports_shared_write_sources():
    """The optional source axis detects two distinct fields writing one attribute."""
    specs = [
        SimpleNamespace(
            input_attr="name",
            graphql_name="name",
            target_name="name",
            source="name",
        ),
        SimpleNamespace(
            input_attr="alias",
            graphql_name="alias",
            target_name="alias",
            source="name",
        ),
    ]

    messages = list(
        iter_input_field_collisions(
            specs,
            subject="Probe",
            field_noun="fields",
            rename_clause="Rename one",
            name_of=lambda spec: spec.target_name,
            source_of=lambda spec: spec.source,
        ),
    )

    assert len(messages) == 1
    assert "'name' and 'alias' sharing one source 'name'" in messages[0]


def test_optional_field_kwargs_defaults_none_and_aliases_only_on_divergence():
    """The A4 helper carries aliases; the builder pins package-default names."""
    from django_strawberry_framework.utils.inputs import optional_field_kwargs

    assert optional_field_kwargs("exact", "exact") == {"default": None}
    assert optional_field_kwargs("category_name", "categoryName") == {
        "default": None,
        "name": "categoryName",
    }
    assert optional_field_kwargs("field_2", "field_2") == {"default": None}


def test_optional_input_field_widens_and_aliases_per_flags():
    """The A10 helper widens optional fields and carries only divergent aliases."""
    from django_strawberry_framework.utils.inputs import optional_input_field

    annotation, kwargs = optional_input_field(
        int,
        python_attr="category_id",
        graphql_name="categoryId",
        widen=True,
    )
    assert annotation == (int | None)
    assert kwargs == {"name": "categoryId", "default": strawberry.UNSET}

    annotation, kwargs = optional_input_field(
        str,
        python_attr="name",
        graphql_name="name",
        widen=False,
    )
    assert annotation is str
    assert kwargs == {}
