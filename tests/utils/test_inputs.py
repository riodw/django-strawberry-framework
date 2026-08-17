"""Tests for the shared generated-input substrate (``utils/inputs.py``).

This module single-sites the neutral generated-input mechanics that the filter
and order families had grown as parallel copies. These tests pin the substrate
directly and assert that BOTH families route through the one builder /
field-spec / camel-name path / Layer-6 Meta-cache skeleton, so a future
re-divergence is caught here rather than via a silently drifted second copy.
"""

import sys
from types import SimpleNamespace

import pytest
import strawberry

from django_strawberry_framework import strawberry_config
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.utils.inputs import (
    FILTERSET_FIELDS_ALIAS,
    GeneratedInputFieldSpec,
    InputFieldSpec,
    _base_meta_values,
    _sorted_meta_values,
    build_strawberry_input_class,
    create_dynamic_set_class,
    emit_set_input_field_triples,
    get_or_store_shape_build,
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
    name_set_input_type_name,
    normalize_field_name_sequence,
    normalize_set_meta_for_factory,
    pascalize_token,
    promote_set_meta_fields,
    read_set_meta_fields,
    resolve_set_meta_fields,
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


def test_builder_rejects_malformed_field_kwargs_with_configuration_error():
    with pytest.raises(ConfigurationError, match="field kwargs must be a mapping"):
        build_strawberry_input_class("MalformedFieldKwargsInput", [("name", int, object())])


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


def test_base_meta_values_reads_builtin_dict_items():
    """The container reader exposes built-in dict entries without invoking overrides."""
    assert _base_meta_values({"name": 1}) == (("name", 1),)


def test_normalize_set_meta_wraps_unreadable_reserved_key_membership():
    class _UnreadableReservedKeys:
        def __contains__(self, value: object) -> bool:
            raise RuntimeError("membership unavailable")

    with pytest.raises(ConfigurationError, match="entries could not be read"):
        normalize_set_meta_for_factory(
            {"fields": ("name",)},
            reserved_keys=_UnreadableReservedKeys(),  # type: ignore[arg-type]
        )


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


def test_normalize_field_name_sequence_wraps_hostile_iterators():
    class _HostileSequence:
        def __iter__(self):
            raise RuntimeError("hostile field sequence")

    with pytest.raises(ConfigurationError, match="readable sequence"):
        normalize_field_name_sequence(_HostileSequence(), flavor="Probe")


def test_meta_sorting_wraps_a_hostile_generic_iterator():
    class _HostileIterable:
        def __iter__(self):
            raise RuntimeError("metadata iteration exploded")

    with pytest.raises(ConfigurationError, match="unreadable _HostileIterable container"):
        _sorted_meta_values(_HostileIterable())


def test_set_meta_helpers_reject_non_mapping_metadata():
    with pytest.raises(ConfigurationError, match="must be a mapping"):
        make_set_meta_cache_key([])  # type: ignore[arg-type]
    with pytest.raises(ConfigurationError, match="must be a mapping"):
        normalize_set_meta_for_factory([], reserved_keys=frozenset())  # type: ignore[arg-type]


def test_input_builder_wraps_unreadable_and_malformed_field_specifications():
    class _UnreadableSpecs:
        def __iter__(self):
            raise RuntimeError("field specs exploded")

    with pytest.raises(ConfigurationError, match="field specifications could not be read"):
        build_strawberry_input_class("UnreadableInput", _UnreadableSpecs())  # type: ignore[arg-type]
    with pytest.raises(ConfigurationError, match="must contain.*triples"):
        build_strawberry_input_class("MalformedInput", [("name", int)])  # type: ignore[list-item]


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
        fields_alias=FILTERSET_FIELDS_ALIAS,
    )
    assert "filter_fields" not in normalized
    assert "filterset_base_class" not in normalized
    assert normalized["fields"] == sorted(["a", "b"], key=repr)


def test_normalize_set_meta_for_factory_prefers_fields_over_alias():
    """When both ``fields`` and the synonym are present, ``fields`` wins."""
    normalized = normalize_set_meta_for_factory(
        {"fields": ["name"], "filter_fields": ["other"]},
        reserved_keys=frozenset(),
        fields_alias=FILTERSET_FIELDS_ALIAS,
    )
    assert normalized["fields"] == ["name"]
    assert "filter_fields" not in normalized


def test_resolve_set_meta_fields_promotes_alias_on_dict_and_meta_class():
    """Class Meta and factory kwargs apply the same ``filter_fields`` synonym."""
    alias = {"code": ["exact"]}

    class Meta:
        filter_fields = alias

    assert resolve_set_meta_fields(Meta, fields_alias=FILTERSET_FIELDS_ALIAS) == (alias, True)
    assert resolve_set_meta_fields(
        {"filter_fields": alias},
        fields_alias=FILTERSET_FIELDS_ALIAS,
    ) == (alias, True)


def test_resolve_set_meta_fields_fields_wins_on_dict_and_meta_class():
    """``fields`` wins on both surfaces; ``from_alias`` is False."""

    class Both:
        fields = ["name"]
        filter_fields = ["other"]

    assert resolve_set_meta_fields(Both, fields_alias=FILTERSET_FIELDS_ALIAS) == (["name"], False)
    assert resolve_set_meta_fields(
        {"fields": ["name"], "filter_fields": ["other"]},
        fields_alias=FILTERSET_FIELDS_ALIAS,
    ) == (["name"], False)


def test_resolve_set_meta_fields_none_source_and_no_alias_family():
    """``None`` source and the order-side ``fields_alias=None`` are no-ops."""
    assert resolve_set_meta_fields(None, fields_alias=FILTERSET_FIELDS_ALIAS) == (None, False)
    assert resolve_set_meta_fields(
        {"filter_fields": ["name"]},
        fields_alias=None,
    ) == (None, False)


def test_filterset_metaclass_and_factory_share_fields_alias_owner():
    """Class-Meta promotion and Layer-6 kwargs canonicalize through one rule."""
    from django_strawberry_framework.filters import factories as filter_factories
    from django_strawberry_framework.filters import sets as filter_sets
    from django_strawberry_framework.orders import sets as order_sets

    assert filter_sets.FILTERSET_FIELDS_ALIAS is FILTERSET_FIELDS_ALIAS
    assert filter_factories.FILTERSET_FIELDS_ALIAS is FILTERSET_FIELDS_ALIAS
    assert filter_sets.promote_set_meta_fields is promote_set_meta_fields
    assert order_sets.promote_set_meta_fields is promote_set_meta_fields
    assert order_sets.read_set_meta_fields is read_set_meta_fields
    assert "promote_set_meta_fields" in filter_sets.FilterSetMetaclass.__new__.__code__.co_names
    assert "promote_set_meta_fields" in order_sets.OrderSetMetaclass.__new__.__code__.co_names
    assert "read_set_meta_fields" in order_sets.OrderSet._expand_meta_fields.__code__.co_names
    assert "resolve_set_meta_fields" in normalize_set_meta_for_factory.__code__.co_names
    assert "canonicalize_set_meta_fields" in normalize_set_meta_for_factory.__code__.co_names


def test_promote_set_meta_fields_writes_alias_on_class_meta_not_dict():
    """Class Meta gets ``.fields``; kwargs dicts stay untouched for the factory."""

    class Meta:
        filter_fields = ["code"]

    assert promote_set_meta_fields(Meta, fields_alias=FILTERSET_FIELDS_ALIAS) == ["code"]
    assert Meta.fields == ["code"]
    assert Meta.filter_fields == ["code"]

    payload = {"filter_fields": ["name"]}
    assert promote_set_meta_fields(payload, fields_alias=FILTERSET_FIELDS_ALIAS) == ["name"]
    assert "fields" not in payload


def test_read_set_meta_fields_canonicalizes_sets_without_mutating_source():
    """Expansion reads cache-stable order; class Meta keeps the original set."""
    names = {"title", "subtitle"}

    class Meta:
        fields = names

    assert read_set_meta_fields(Meta) == sorted(["title", "subtitle"], key=repr)
    assert Meta.fields is names
    assert read_set_meta_fields({"fields": names}) == sorted(["title", "subtitle"], key=repr)
    assert read_set_meta_fields({"fields": {"name": {"exact", "contains"}}}) == {
        "name": sorted(["contains", "exact"], key=repr),
    }
    assert read_set_meta_fields(None) is None


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

    # Neither family re-exports the hashing helpers under a private alias: the
    # owner is ``utils/inputs.py`` and both getters reach it through the one
    # shared ``make_dynamic_set_getter`` closure below.
    for module in (filter_factories, order_factories):
        assert not hasattr(module, "_make_hashable")
        assert not hasattr(module, "_make_cache_key")
        assert not hasattr(module, "_normalize_meta_for_factory")
    assert make_hashable_meta_value is not None
    assert make_set_meta_cache_key is not None
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


def test_get_or_store_shape_build_stores_on_miss_and_reuses_on_hit():
    """A miss stores ``factory()``; a later hit returns it without calling factory again."""
    cache: dict[str, str] = {}
    calls: list[int] = []

    def factory() -> str:
        calls.append(1)
        return "built"

    assert get_or_store_shape_build(cache, "k", factory) == "built"
    assert get_or_store_shape_build(cache, "k", factory) == "built"
    assert calls == [1]
    assert cache["k"] == "built"


def test_write_flavor_shape_caches_share_get_or_store_owner():
    """Model bind, form cached_build_input, and serializer dedupe import one get-or-store."""
    from django_strawberry_framework.mutations import sets as mutation_sets
    from django_strawberry_framework.rest_framework import inputs as ser_inputs

    assert mutation_sets.get_or_store_shape_build is get_or_store_shape_build
    assert ser_inputs.get_or_store_shape_build is get_or_store_shape_build


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


def test_name_set_input_type_name_canonical_and_narrowed():
    """Full name-set shapes take ``<Base>Input`` / ``PartialInput``; a narrowing is tokenized."""
    full = ("name", "category")
    assert (
        name_set_input_type_name(
            "Item",
            is_partial=False,
            effective_field_names=full,
            full_field_names=full,
        )
        == "ItemInput"
    )
    assert (
        name_set_input_type_name(
            "Item",
            is_partial=True,
            effective_field_names=full,
            full_field_names=full,
        )
        == "ItemPartialInput"
    )
    assert (
        name_set_input_type_name(
            "Item",
            is_partial=False,
            effective_field_names=("name",),
            full_field_names=full,
        )
        == "ItemNameInput"
    )


def test_name_set_input_type_name_token_boundaries_do_not_collide():
    """Sorted ``pascalize_token`` concatenation stays uniquely decomposable."""
    full = ("other",)
    left = name_set_input_type_name(
        "Item",
        is_partial=False,
        effective_field_names=("a_b", "c"),
        full_field_names=full,
    )
    right = name_set_input_type_name(
        "Item",
        is_partial=False,
        effective_field_names=("a", "b_c"),
        full_field_names=full,
    )
    assert left != right
    assert left == "ItemA_ubCInput" and right == "ItemAB_ucInput"


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
