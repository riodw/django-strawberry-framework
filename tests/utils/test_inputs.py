"""Tests for the shared generated-input substrate (``utils/inputs.py``).

Name collision and ``Meta.fields`` canonicalization are construction-time.
Shipped filter/order input names live in
``examples/fakeshop/test_query/test_library_api.py`` and
``examples/fakeshop/test_query/test_connection_pagination_api.py``.
"""

import sys
from collections.abc import Callable, Collection, Iterator
from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar, NoReturn, cast

import pytest
import strawberry
from django.utils.functional import SimpleLazyObject
from typing_extensions import override

from django_strawberry_framework import strawberry_config
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.filters import inputs as filter_inputs
from django_strawberry_framework.filters import sets as filter_sets
from django_strawberry_framework.mutations import sets as mutation_sets
from django_strawberry_framework.orders import OrderSet
from django_strawberry_framework.orders import inputs as order_inputs
from django_strawberry_framework.orders import sets as order_sets
from django_strawberry_framework.rest_framework import inputs as ser_inputs
from django_strawberry_framework.sets_mixins import (
    ClassBasedTypeNameMixin,
    is_re_readable_field_declaration,
)
from django_strawberry_framework.utils._narrowing import (
    is_dict,
    is_list,
    is_set_or_frozenset,
    is_tuple,
)
from django_strawberry_framework.utils.canonical import base_container_values
from django_strawberry_framework.utils.inputs import (
    FILTERSET_FIELDS_ALIAS,
    GeneratedInputArgumentsFactory,
    GeneratedInputFieldSpec,
    InputFieldSpec,
    _PlainNames,
    _safe_import,
    _sorted_meta_values,
    build_strawberry_input_class,
    canonicalize_set_meta_fields,
    emit_set_input_field_triples,
    get_or_store_shape_build,
    graphql_camel_name,
    iter_input_field_collisions,
    iter_provided_input_fields,
    iter_set_subclasses,
    make_input_namespace,
    make_set_input_namespace,
    make_shape_build_cache,
    materialize_generated_input_class,
    name_set_input_type_name,
    normalize_field_name_sequence,
    optional_field_kwargs,
    optional_input_field,
    pascalize_token,
    plain_set_meta_fields,
    promote_set_meta_fields,
    read_set_meta_fields,
    resolve_set_meta_fields,
    set_input_type_name,
)
from tests._idioms import (
    STR_SUBCLASS_KINDS,
    ClaimsClass,
    ClassReadRaises,
    module_binding,
    str_subclass_name,
)
from tests._soft_dependency import blocked_modules

if TYPE_CHECKING:
    from django_strawberry_framework.utils.inputs import SetInputNamespace

# ---------------------------------------------------------------------------
# build_strawberry_input_class
# ---------------------------------------------------------------------------


def test_build_strawberry_input_class_emits_name_alias_and_description() -> None:
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


def test_builder_pins_names_so_digit_boundary_fields_do_not_silently_collide() -> None:
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

    # stand-in set class; only ``__qualname__`` is read (error path).
    class _ProbeSet(ClassBasedTypeNameMixin):
        pass

    entries = [("field_2", object()), ("field2", object())]
    field_specs: dict[tuple[type[_ProbeSet], str], GeneratedInputFieldSpec] = {}
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
        # basedpyright: Strawberry reads this annotation at runtime; the input class is built by
        # the helper under test
        def probe(self, inp: input_cls) -> int:  # pyright: ignore[reportInvalidTypeForm, reportUnknownParameterType]
            del inp  # Strawberry reads it to put the input class in the SDL under test; never runs
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


def test_builder_rejects_duplicate_python_attributes() -> None:
    """The last defensive layer rejects a duplicate before the namespace drops a field."""
    with pytest.raises(ConfigurationError, match=r"input attribute 'same'.*more than once"):
        build_strawberry_input_class(
            "DuplicateAttrInput",
            [("same", int, {}), ("same", str, {})],
        )


def test_builder_rejects_duplicate_effective_graphql_names() -> None:
    """Explicit aliases cannot collapse two distinct attrs onto one GraphQL field."""
    with pytest.raises(ConfigurationError, match="same GraphQL field name 'same'"):
        build_strawberry_input_class(
            "DuplicateGraphQLInput",
            [("first", int, {"name": "same"}), ("second", str, {"name": "same"})],
        )


@pytest.mark.parametrize(
    "kwargs",
    [{"name": 5}, {"description": 5}, {"name": b"x", "description": ["d"]}],
    ids=["name", "description", "both"],
)
def test_builder_rejects_non_string_name_and_description(kwargs: dict[str, object]) -> None:
    """The builder forwards only strings into ``strawberry.field``'s ``name`` / ``description``."""
    with pytest.raises(ConfigurationError, match="takes a string name and description"):
        build_strawberry_input_class("NonStringKwargInput", [("field", int, kwargs)])


def test_builder_rejects_malformed_field_kwargs_with_configuration_error() -> None:
    with pytest.raises(ConfigurationError, match="field kwargs must be a mapping"):
        # basedpyright: the non-mapping field kwargs is the hostile input under test;
        # build_strawberry_input_class types each triple's kwargs as Mapping[str, object] | None
        build_strawberry_input_class("MalformedFieldKwargsInput", [("name", int, object())])  # pyright: ignore[reportArgumentType]


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
def test_graphql_camel_name(value: str, expected: str) -> None:
    """Head lowercased, rest PascalCased; no-word-token inputs pass through."""
    assert graphql_camel_name(value) == expected


# ---------------------------------------------------------------------------
# Single-siting: both families share ONE substrate path
# ---------------------------------------------------------------------------


def test_filter_and_order_families_share_one_substrate() -> None:
    """Both ``inputs`` modules re-export the SAME shared mechanics by identity.

    This is the single-substrate contract guard: if a future change re-introduces a
    family-local copy of the builder / field-spec / camel-name / subclass
    iterator, these identity assertions fail.
    """
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


def test_materialize_generated_input_class_names_family_in_collision() -> None:
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


def test_iter_set_subclasses_dedupes_diamond_inheritance() -> None:
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


def test_safe_import_returns_none_for_unimportable_module() -> None:
    """``_safe_import`` swallows ImportError so a partial-load clear continues.

    A ``None`` entry in ``sys.modules`` makes the import raise ImportError --
    the same way the family ``clear_*_input_namespace`` tolerance tests simulate
    an unreachable submodule.
    """
    fake_name = "django_strawberry_framework._nonexistent_substrate_probe"
    with blocked_modules(fake_name):
        assert _safe_import(fake_name, "anything") is None


def test_safe_import_returns_none_for_missing_attribute_on_importable_module() -> None:
    """``_safe_import`` keeps its attr-lenient shape: importable module, absent attr -> ``None``.

    The wrapper deliberately diverges from its ``import_attr_if_importable``
    delegate here (which fails loud on a missing attribute): the partial-load
    lifecycle callers treat a module without the looked-up symbol as "nothing to
    clear", not as a bug.
    """
    assert _safe_import("django_strawberry_framework.utils.inputs", "_not_a_real_attr") is None


# ---------------------------------------------------------------------------
# spec-039 promotions: InputFieldSpec / make_input_namespace / make_shape_build_cache
# ---------------------------------------------------------------------------


def test_input_field_spec_carries_five_axes_and_optional_source() -> None:
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
        # basedpyright: a write to the frozen dataclass is the rejected operation under test
        with_source.source = "other"  # pyright: ignore[reportAttributeAccessIssue]


def test_make_input_namespace_returns_ledger_materialize_clear_trio() -> None:
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


def test_set_input_type_name_delegates_to_type_name_for() -> None:
    """``set_input_type_name`` is the one ``<Class>InputType`` derivation site."""

    class _Named(OrderSet):
        pass

    assert set_input_type_name(_Named) == "_NamedInputType"


def test_make_set_input_namespace_returns_heavy_ledger_field_specs_materialize_clear() -> None:
    """Heavy quartet: materialize writes the ledger; clear empties ledger AND field_specs.

    Unimportable factory / set modules are tolerated (the same cycle-safe skip
    ``clear_generated_input_namespace`` uses). The materialized global stays
    PARKED -- this is the heavy sibling of ``make_input_namespace``, not a
    ``delattr`` teardown.
    """
    module_path = __name__
    module = sys.modules[module_path]
    namespace: SetInputNamespace[ClassBasedTypeNameMixin] = make_set_input_namespace(
        module_path,
        "ProbeSet",
        factory_module="django_strawberry_framework.not_a_real_factory_module",
        factory_class_name="NoFactory",
        collision_registry_attr="_type_probeset_registry",
        set_module="django_strawberry_framework.not_a_real_set_module",
        set_class_name="ProbeSet",
    )
    ledger, field_specs, materialize, clear = namespace
    assert ledger == {}
    assert field_specs == {}

    class _ProbeSet(ClassBasedTypeNameMixin):
        pass

    class _ProbeInput:
        pass

    materialize("ProbeSetInputType", _ProbeInput)
    assert ledger["ProbeSetInputType"] is _ProbeInput
    assert module.ProbeSetInputType is _ProbeInput
    field_specs[(_ProbeSet, "title")] = GeneratedInputFieldSpec(
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


def test_filter_and_order_input_namespaces_ride_make_set_input_namespace() -> None:
    """Both set families unpack the same factory closures and naming helper."""
    assert filter_inputs._input_type_name_for is set_input_type_name
    assert order_inputs._input_type_name_for is set_input_type_name
    assert filter_inputs._materialize_input.__code__ is order_inputs._materialize_input.__code__
    assert (
        filter_inputs._clear_input_namespace.__code__
        is order_inputs._clear_input_namespace.__code__
    )


def test_base_container_values_reads_builtin_dict_items() -> None:
    """The container reader exposes built-in dict entries without invoking overrides."""
    assert base_container_values({"name": 1}) == (("name", 1),)


def test_normalize_field_name_sequence_wraps_hostile_iterators() -> None:
    class _HostileSequence:
        def __iter__(self) -> NoReturn:
            raise RuntimeError("hostile field sequence")

    with pytest.raises(ConfigurationError, match="readable sequence"):
        normalize_field_name_sequence(_HostileSequence(), flavor="Probe")


def test_normalize_field_name_sequence_rejects_unordered_sets() -> None:
    """A set / frozenset is rejected: its iteration order varies per process.

    The serializer flavor folds the DECLARED order into the generated input
    type name (``rest_framework/inputs.py::serializer_input_type_name``
    concatenates per-field tokens in walk order), so an unordered container
    would make the same declaration produce different type names - and SDL
    field orders - under different ``PYTHONHASHSEED`` values. The model / form
    flavors sort their name sets (``name_set_input_type_name``); the shape
    contract is owned once, here.
    """
    with pytest.raises(ConfigurationError, match="ordered sequence of field name strings"):
        normalize_field_name_sequence({"b", "a"}, label="fields", flavor="SerializerMutation")
    with pytest.raises(ConfigurationError, match="ordered sequence of field name strings"):
        normalize_field_name_sequence(
            frozenset(("b", "a")),
            label="exclude",
            flavor="SerializerMutation",
        )


def test_meta_sorting_wraps_a_hostile_generic_iterator() -> None:
    class _HostileIterable:
        def __iter__(self) -> NoReturn:
            raise RuntimeError("metadata iteration exploded")

    with pytest.raises(ConfigurationError, match="unreadable _HostileIterable container"):
        _sorted_meta_values(_HostileIterable())


def test_input_builder_wraps_unreadable_and_malformed_field_specifications() -> None:
    class _UnreadableSpecs:
        def __iter__(self) -> NoReturn:
            raise RuntimeError("field specs exploded")

    with pytest.raises(ConfigurationError, match="field specifications could not be read"):
        # basedpyright: the unreadable field-spec container is the hostile input under test;
        # build_strawberry_input_class types the parameter as a Sequence of triples
        build_strawberry_input_class("UnreadableInput", _UnreadableSpecs())  # pyright: ignore[reportArgumentType]
    with pytest.raises(ConfigurationError, match=r"must contain.*triples"):
        # basedpyright: the two-member field spec is the hostile input under test;
        # build_strawberry_input_class types the parameter as a Sequence of triples
        build_strawberry_input_class("MalformedInput", [("name", int)])  # pyright: ignore[reportArgumentType]


def test_meta_fields_canonicalization_bypasses_hostile_containers_and_reprs() -> None:
    """``Meta.fields`` canonicalization never trusts consumer container hooks or reprs."""

    class _HostileRepr:
        @override
        def __repr__(self) -> str:
            raise RuntimeError("hostile repr")

    class _HostileDict(dict[str, object]):
        @override
        def items(self) -> NoReturn:
            raise RuntimeError("hostile items")

    class _HostileSet(set[object]):
        @override
        def __iter__(self) -> NoReturn:
            raise RuntimeError("hostile set iterator")

    class _HostileList(list[object]):
        @override
        def __iter__(self) -> NoReturn:
            raise RuntimeError("hostile list iterator")

    hostile_repr = _HostileRepr()
    assert canonicalize_set_meta_fields({hostile_repr}) == [hostile_repr]
    assert canonicalize_set_meta_fields(_HostileSet(["b", "a"])) == ["a", "b"]
    assert canonicalize_set_meta_fields(
        _HostileDict(name=_HostileSet(["exact", "contains"])),
    ) == {"name": ["contains", "exact"]}
    assert _sorted_meta_values(_HostileList(["z", "a"])) == ["a", "z"]


@pytest.mark.parametrize("escape", [RuntimeError, KeyboardInterrupt])
def test_meta_fields_canonicalization_passes_a_value_whose_class_read_raises_through(
    escape: type[BaseException],
) -> None:
    """A value whose ``__class__`` raises is neither a set nor a dict, so it is returned untouched.

    The re-readable gate that follows names it in its typed rejection; the canonicalizer's
    own kind tests must not raise first. The same holds for a lookup-bag value.
    """
    hostile = ClassReadRaises(escape)

    assert canonicalize_set_meta_fields(hostile) is hostile
    bag = canonicalize_set_meta_fields({"name": hostile})
    assert isinstance(bag, dict)
    assert bag["name"] is hostile


def test_meta_fields_canonicalization_keeps_a_lazy_set_a_typed_rejection() -> None:
    """A lazy proxy of a set is judged by its class (a set) and refused as unreadable, as before.

    Letting it through would hand the expansion a set in hash order.
    """
    with pytest.raises(ConfigurationError) as excinfo:
        canonicalize_set_meta_fields(SimpleLazyObject(lambda: {"b", "a"}))
    assert str(excinfo.value) == (
        "Generated set metadata contains an unreadable SimpleLazyObject container."
    )


@pytest.mark.parametrize("escape", [RuntimeError, KeyboardInterrupt])
def test_normalize_field_name_sequence_rejects_a_value_whose_class_read_raises(
    escape: type[BaseException],
) -> None:
    """The bare-string and unordered-set tests tolerate a ``__class__`` that raises.

    Such a value is neither, so it reaches the tuple read, which it fails typed.
    """
    with pytest.raises(ConfigurationError) as excinfo:
        normalize_field_name_sequence(ClassReadRaises(escape), flavor="Probe")
    assert str(excinfo.value) == (
        "Probe Meta.fields must be a readable sequence of field name strings; got ClassReadRaises."
    )


@pytest.mark.parametrize(
    ("entry", "rendered"),
    [
        pytest.param(ClassReadRaises(RuntimeError), "<ClassReadRaises>", id="class-read-raises"),
        pytest.param(
            ClassReadRaises(KeyboardInterrupt),
            "<ClassReadRaises>",
            id="class-read-interrupts",
        ),
        pytest.param(ClaimsClass(str), "<ClaimsClass>", id="claims-str"),
    ],
)
def test_normalize_field_name_sequence_rejects_an_entry_that_is_not_really_a_string(
    entry: object,
    rendered: str,
) -> None:
    """An entry is a name only if its real type is a string: its ``__class__`` is never consulted.

    The base ``str`` slot the accepted names are copied through refuses an object that is not
    really a ``str``, so a ``__class__`` that raises or claims ``str`` must be listed as a
    non-string entry before it gets there.
    """
    with pytest.raises(ConfigurationError) as excinfo:
        normalize_field_name_sequence(["name", entry], flavor="Probe")
    assert str(excinfo.value) == (
        "Probe Meta.fields must be a sequence of field name strings; "
        f"got non-string entry(ies): [{rendered}]."
    )


def test_normalize_field_name_sequence_judges_a_lazy_whole_value_by_its_class() -> None:
    """A lazy proxy of a string is a bare string (refused); a lazy proxy of a list is a list.

    The whole-value tests keep asking the proxied class: reading the real type instead would
    iterate the string into one name per character.
    """
    with pytest.raises(ConfigurationError, match="not a bare string"):
        normalize_field_name_sequence(SimpleLazyObject(lambda: "name"), flavor="Probe")
    assert normalize_field_name_sequence(SimpleLazyObject(lambda: ["name"]), flavor="Probe") == (
        "name",
    )


def test_resolve_set_meta_fields_promotes_the_alias_on_a_meta_class() -> None:
    """A class Meta supplying only ``filter_fields`` resolves through the synonym."""
    alias = {"code": ["exact"]}

    class Meta:
        filter_fields = alias

    assert resolve_set_meta_fields(Meta, fields_alias=FILTERSET_FIELDS_ALIAS) == (alias, True)


def test_resolve_set_meta_fields_fields_wins_over_the_alias() -> None:
    """``fields`` wins over ``filter_fields``; ``from_alias`` is False."""

    class Both:
        fields = ["name"]
        filter_fields = ["other"]

    assert resolve_set_meta_fields(Both, fields_alias=FILTERSET_FIELDS_ALIAS) == (["name"], False)


def test_resolve_set_meta_fields_none_source_and_no_alias_family() -> None:
    """``None`` source and the order-side ``fields_alias=None`` are no-ops."""
    assert resolve_set_meta_fields(None, fields_alias=FILTERSET_FIELDS_ALIAS) == (None, False)

    class AliasOnly:
        filter_fields = ["name"]

    assert resolve_set_meta_fields(AliasOnly, fields_alias=None) == (None, False)


def test_set_metaclasses_share_the_fields_alias_owner() -> None:
    """Both set families promote and read ``Meta.fields`` through one rule."""
    assert module_binding(filter_sets, "FILTERSET_FIELDS_ALIAS") is FILTERSET_FIELDS_ALIAS
    assert module_binding(filter_sets, "promote_set_meta_fields") is promote_set_meta_fields
    assert module_binding(order_sets, "promote_set_meta_fields") is promote_set_meta_fields
    assert module_binding(order_sets, "read_set_meta_fields") is read_set_meta_fields
    assert "promote_set_meta_fields" in filter_sets.FilterSetMetaclass.__new__.__code__.co_names
    assert "promote_set_meta_fields" in order_sets.OrderSetMetaclass.__new__.__code__.co_names
    assert "read_set_meta_fields" in order_sets.OrderSet._expand_meta_fields.__code__.co_names


def test_promote_set_meta_fields_writes_the_alias_onto_class_meta() -> None:
    """Class Meta gets ``.fields``; the consumer's alias attribute stays."""

    class Meta:
        filter_fields = ["code"]
        fields: ClassVar[list[str]]

    assert promote_set_meta_fields(Meta, fields_alias=FILTERSET_FIELDS_ALIAS) == ["code"]
    assert Meta.fields == ["code"]
    assert Meta.filter_fields == ["code"]


def test_read_set_meta_fields_canonicalizes_sets_without_mutating_source() -> None:
    """Expansion reads process-stable order; class Meta keeps the original set."""
    names = {"title", "subtitle"}

    class Meta:
        fields = names

    assert read_set_meta_fields(Meta) == sorted(["title", "subtitle"], key=repr)
    assert Meta.fields is names

    class LookupMeta:
        fields = {"name": {"exact", "contains"}}

    assert read_set_meta_fields(LookupMeta) == {
        "name": sorted(["contains", "exact"], key=repr),
    }
    assert read_set_meta_fields(None) is None


class _Names(Collection[object]):
    """A project ``Collection`` of field names: re-readable, with no base slot to read."""

    def __init__(self, *names: object) -> None:
        super().__init__()
        self._names = names

    @override
    def __iter__(self) -> Iterator[object]:
        return iter(self._names)

    @override
    def __len__(self) -> int:
        return len(self._names)

    @override
    def __contains__(self, item: object) -> bool:
        return item in self._names


class _NameList(list[object]):
    """A ``list`` subclass declaration."""


def _plain_text_only(value: object) -> bool:
    """Whether every ``str`` reachable in ``value`` (keys, members, lookups) is exactly ``str``."""
    if isinstance(value, str):
        return type(value) is str
    if is_dict(value):
        return all(
            _plain_text_only(key) and _plain_text_only(lookups)
            for key, lookups in base_container_values(value)
        )
    if is_list(value) or is_tuple(value) or is_set_or_frozenset(value):
        return all(_plain_text_only(member) for member in base_container_values(value))
    if isinstance(value, _PlainNames):
        return all(_plain_text_only(member) for member in value)
    return True


_PLAIN_SHAPES: dict[str, tuple[Callable[[Callable[[str], str]], object], object]] = {
    "name": (lambda n: n("title"), "title"),
    "top-level __all__": (lambda n: n("__all__"), "__all__"),
    "list": (lambda n: [n("title"), "isbn"], ["title", "isbn"]),
    "list subclass": (lambda n: _NameList([n("title")]), ["title"]),
    "tuple": (lambda n: (n("title"), "isbn"), ("title", "isbn")),
    "set": (lambda n: {n("title"), "isbn"}, {"title", "isbn"}),
    "frozenset": (lambda n: frozenset({n("title")}), frozenset({"title"})),
    "non-str member": (lambda n: [n("title"), None], ["title", None]),
    "dict key": (
        lambda n: {"isbn": ["exact"], n("title"): ["exact", "icontains"]},
        {"isbn": ["exact"], "title": ["exact", "icontains"]},
    ),
    "dict lookup value": (lambda n: {"title": [n("icontains")]}, {"title": ["icontains"]}),
    "dict per-field __all__": (lambda n: {"title": n("__all__")}, {"title": "__all__"}),
    "dict_keys": (lambda n: {n("title"): None}.keys(), _PlainNames(("title",))),
    "custom Collection": (lambda n: _Names(n("title"), "isbn"), _PlainNames(("title", "isbn"))),
}


@pytest.mark.parametrize("kind", STR_SUBCLASS_KINDS)
@pytest.mark.parametrize("shape", list(_PLAIN_SHAPES))
def test_plain_set_meta_fields_reads_every_str_subclass_name_as_plain_text(
    shape: str,
    kind: str,
) -> None:
    """Every name a set-family declaration can hold comes back as the plain ``str`` it spells.

    The container keeps its built-in kind (a ``list`` subclass becomes a
    ``list``; a view or project ``Collection`` becomes a ``tuple``), a lookup-bag
    ``dict`` keeps its key order, a non-``str`` member passes through, and no
    dunder of the subclass runs on the way.
    """
    calls: list[str] = []
    build, expected = _PLAIN_SHAPES[shape]
    declaration = build(lambda text: str_subclass_name(kind, text, calls))
    calls.clear()

    plain = plain_set_meta_fields(declaration)

    assert calls == []
    assert _plain_text_only(plain)
    assert type(plain) is type(expected)
    if isinstance(expected, _PlainNames):
        # No base slot to rebuild from: an ordered, re-readable copy that is, like the
        # declaration, no ``list`` / ``tuple`` / ``set``.
        assert list(cast("_PlainNames", plain)) == list(expected)
        assert list(cast("_PlainNames", plain)) == list(cast("_PlainNames", plain))
        assert is_re_readable_field_declaration(plain)
        assert not isinstance(
            plain,
            (
                list,
                tuple,
                set,
                frozenset,
            ),
        )
    else:
        assert plain == expected
    if is_dict(expected):
        assert list(base_container_values(plain)) == list(base_container_values(expected))


@pytest.mark.parametrize("shape", list(_PLAIN_SHAPES))
def test_plain_set_meta_fields_returns_a_plain_declaration_as_the_same_object(shape: str) -> None:
    """A declaration holding no ``str`` subclass is returned unchanged, by identity."""
    build, _expected = _PLAIN_SHAPES[shape]
    declaration = build(str)
    assert plain_set_meta_fields(declaration) is declaration


@pytest.mark.parametrize(
    "declaration",
    [
        None,
        b"title",
        (name for name in ["title"]),
        {"title": None},
    ],
    ids=[
        "None",
        "bytes",
        "one-shot iterator",
        "lookup-less dict",
    ],
)
def test_plain_set_meta_fields_passes_other_values_through(declaration: object) -> None:
    """A value that names nothing through a ``str`` subclass is left for each family's own gate."""
    assert plain_set_meta_fields(declaration) is declaration


@pytest.mark.parametrize("kind", STR_SUBCLASS_KINDS)
def test_read_set_meta_fields_orders_a_str_subclass_set_as_the_plain_names(kind: str) -> None:
    """A ``set`` declaration holding a ``str`` subclass sorts exactly as the plain names would."""
    calls: list[str] = []

    class Meta:
        fields = {str_subclass_name(kind, "title", calls), "subtitle", "isbn"}

    calls.clear()
    names = read_set_meta_fields(Meta)

    assert calls == []
    assert names == read_set_meta_fields(
        type("PlainMeta", (), {"fields": {"title", "subtitle", "isbn"}}),
    )
    assert _plain_text_only(names)


def test_make_shape_build_cache_returns_dict_and_clear() -> None:
    """``make_shape_build_cache`` returns a ``(dict, clear)`` pair; clear empties the dict."""
    cache_pair: tuple[dict[tuple[str, str, frozenset[str]], object], Callable[[], None]] = (
        make_shape_build_cache()
    )
    cache, clear = cache_pair
    assert cache == {}
    cache[("Model", "create", frozenset({"a"}))] = object()
    assert len(cache) == 1
    clear()
    assert cache == {}


def test_get_or_store_shape_build_stores_on_miss_and_reuses_on_hit() -> None:
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


def test_write_flavor_shape_caches_share_get_or_store_owner() -> None:
    """Model bind, form cached_build_input, and serializer dedupe import one get-or-store."""
    assert module_binding(mutation_sets, "get_or_store_shape_build") is get_or_store_shape_build
    assert module_binding(ser_inputs, "get_or_store_shape_build") is get_or_store_shape_build


def test_pascalize_token_is_injective_across_legal_field_name_boundaries() -> None:
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


def test_name_set_input_type_name_canonical_and_narrowed() -> None:
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


def test_name_set_input_type_name_token_boundaries_do_not_collide() -> None:
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
    assert left == "ItemA_ubCInput"
    assert right == "ItemAB_ucInput"


@dataclass(frozen=True)
class _CollisionSpec:
    """The naming record the collision walker reads, plus the target and source it is asked for."""

    input_attr: str
    graphql_name: str
    target_name: str
    source: str


def test_input_collision_walker_reports_shared_write_sources() -> None:
    """The optional source axis detects two distinct fields writing one attribute."""
    specs = [
        _CollisionSpec(
            input_attr="name",
            graphql_name="name",
            target_name="name",
            source="name",
        ),
        _CollisionSpec(
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


def test_optional_field_kwargs_defaults_none_and_aliases_only_on_divergence() -> None:
    """The A4 helper carries aliases; the builder pins package-default names."""
    assert optional_field_kwargs("exact", "exact") == {"default": None}
    assert optional_field_kwargs("category_name", "categoryName") == {
        "default": None,
        "name": "categoryName",
    }
    assert optional_field_kwargs("field_2", "field_2") == {"default": None}


def test_optional_input_field_widens_and_aliases_per_flags() -> None:
    """The A10 helper widens optional fields and carries only divergent aliases."""
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


def test_iter_provided_input_fields_handles_none_and_non_inputs() -> None:
    """iter_provided_input_fields yields nothing on None or non-Strawberry inputs."""
    assert list(iter_provided_input_fields(None)) == []
    assert list(iter_provided_input_fields({})) == []
    assert list(iter_provided_input_fields(42)) == []


def test_generated_input_arguments_factory_tolerates_none_or_missing_related_attr() -> None:
    """GeneratedInputArgumentsFactory does not crash when related_attr is None or missing."""

    class _ProbeFactory(GeneratedInputArgumentsFactory[ClassBasedTypeNameMixin]):
        _factory_label = "ProbeFactory"
        _family_label = "ProbeSet"
        _rename_noun = "probe set"
        _related_attr = "related_probes"
        _related_target_attr = "target"
        input_object_types = {}
        _collision_registry_attr = "_probe_registry"
        _probe_registry: ClassVar[dict[str, type[ClassBasedTypeNameMixin]]] = {}

        @override
        def _build_input_triples(
            self,
            set_cls: type[ClassBasedTypeNameMixin],
            type_name: str,
            owner_definition: object,
        ) -> list[tuple[str, object, dict[str, object]]]:
            return [("id", int | None, {"default": None})]

    class _SetWithNoneRelated(OrderSet):
        related_probes = None

    factory = _ProbeFactory(_SetWithNoneRelated)
    input_cls = factory.arguments
    assert input_cls is not None
    assert input_cls.__name__ == "_SetWithNoneRelatedInputType"


def test_build_strawberry_input_class_rejects_empty_specs_with_the_callers_remedy() -> None:
    """The zero-field guard lives at the construction site, not only at its callers.

    Strawberry rejects an empty input object at ``Schema(...)`` build with a raw
    ``ValueError`` naming the GENERATED type, which tells a consumer nothing
    about the class they wrote. A caller that knows the better remedy supplies
    it; one that does not is unaffected, because
    ``mutations/inputs.py`` legitimately builds an empty generated REMAINDER
    when a consumer ``input_class`` supplies the fields.
    """
    with pytest.raises(ConfigurationError, match="remedy from the caller"):
        build_strawberry_input_class(
            "EmptyInputType",
            [],
            empty_message="EmptyInputType has no fields; here is the remedy from the caller.",
        )

    # No message: the empty build is permitted, for the merged-override caller.
    built = build_strawberry_input_class("EmptyMergedInputType", [])
    assert built.__name__ == "EmptyMergedInputType"


def test_emit_rejects_graphql_name_collision_across_distinct_python_attrs() -> None:
    """The emit scaffold's SECOND arm: two members collapsing onto one GraphQL name.

    ``foo_bar`` and ``fooBar`` flatten to distinct python attrs, but
    ``graphql_camel_name`` sends both to ``fooBar`` -- the same silent-overwrite
    class as the attr collision, rejected before the later member clobbers the
    earlier one's field in the generated input dataclass.
    """

    class _ProbeSet(ClassBasedTypeNameMixin):
        __qualname__ = "_ProbeSet"

    field_specs: dict[tuple[type[_ProbeSet], str], GeneratedInputFieldSpec] = {}
    with pytest.raises(ConfigurationError, match="GraphQL input field name 'fooBar'"):
        emit_set_input_field_triples(
            _ProbeSet,
            [("foo_bar", object()), ("fooBar", object())],
            related_target_of=lambda _t, _e: (False, None),
            related_source_path_of=lambda t, _e: t,
            leaf_of=lambda _t, _pa, _e: (int | None, _t),
            input_type_name_for=lambda cls: cls.__name__,
            module_path=__name__,
            field_specs=field_specs,
        )
    assert field_specs == {}


def test_emit_rejects_flatten_collision_between_traversal_and_declared_member() -> None:
    """``a__b`` (a relation traversal) flattens onto the declared member ``a_b``."""

    class _ProbeSet(ClassBasedTypeNameMixin):
        __qualname__ = "_ProbeSet"

    with pytest.raises(ConfigurationError, match="both generate the input attribute 'a_b'"):
        emit_set_input_field_triples(
            _ProbeSet,
            [("a_b", object()), ("a__b", object())],
            related_target_of=lambda _t, _e: (False, None),
            related_source_path_of=lambda t, _e: t,
            leaf_of=lambda _t, _pa, _e: (int | None, _t),
            input_type_name_for=lambda cls: cls.__name__,
            module_path=__name__,
            field_specs={},
        )


def _class_name(cls: type) -> str:
    return cls.__name__


def test_emit_stages_field_specs_atomically_across_a_clean_walk_then_collision() -> None:
    """``field_specs`` rows commit only after the WHOLE set walks clean.

    Writing provenance rows as each field is emitted left the family table
    half-populated when a later member collided -- a schema build that failed
    loud but not cleanly. The staged batch is dropped on the collision, so
    rows emitted by earlier clean members do not survive either.
    """

    class _ProbeSet(ClassBasedTypeNameMixin):
        __qualname__ = "_ProbeSet"

    def _emit(
        entries: list[tuple[str, object]],
        field_specs: dict[tuple[type, str], GeneratedInputFieldSpec],
    ) -> list[tuple[str, object, dict[str, object]]]:
        return emit_set_input_field_triples(
            _ProbeSet,
            entries,
            related_target_of=lambda _t, _e: (False, None),
            related_source_path_of=lambda t, _e: t,
            leaf_of=lambda _t, _pa, _e: (int | None, _t),
            input_type_name_for=_class_name,
            module_path=__name__,
            field_specs=field_specs,
        )

    # A collision on the FIRST colliding pair commits nothing.
    collision: dict[tuple[type, str], GeneratedInputFieldSpec] = {}
    with pytest.raises(ConfigurationError, match="both generate the input attribute"):
        _emit([("a_b", object()), ("a__b", object())], collision)
    assert collision == {}

    # Clean members that emit BEFORE the late colliding member drop too.
    late: dict[tuple[type, str], GeneratedInputFieldSpec] = {}
    with pytest.raises(ConfigurationError, match="both generate the input attribute"):
        _emit([("a_b", object()), ("b", object()), ("a__b", object())], late)
    assert late == {}

    # The clean walk still commits every row.
    clean: dict[tuple[type, str], GeneratedInputFieldSpec] = {}
    triples = _emit([("a_b", object()), ("b", object())], clean)
    assert [triple[0] for triple in triples] == ["a_b", "b"]
    assert set(clean) == {(_ProbeSet, "a_b"), (_ProbeSet, "b")}
