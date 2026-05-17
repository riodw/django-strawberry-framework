"""Tests for ``convert_choices_to_enum``.

Fakeshop has no choice columns, so the test surface is built around a
session-scoped ``ChoiceFixture`` Django model that lives under a synthetic
``app_label``. Every test in this file uses that fixture as the source of
truth so the behaviour is exercised without polluting the example schema.

Covered behavior:

- enum generation + naming
- registry caching keyed on ``(model, field_name)``
- enum reuse across two ``DjangoType``s pointing at the same column
- grouped-choices rejection
- member-name sanitization (hyphens, leading digits, keywords)
- ``null=True`` widening to exactly ``EnumType | None``

Coverage knock-ons: these tests exercise ``convert_scalar``'s ``null``
widening branch and ``registry.register_enum`` / ``get_enum``.
"""

import enum

import pytest
import strawberry
from django.db import models

from django_strawberry_framework import BigInt, DjangoType, finalize_django_types
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.registry import registry
from django_strawberry_framework.types import converters
from django_strawberry_framework.types.converters import (
    _sanitize_member_name,
    convert_choices_to_enum,
    convert_scalar,
)


@pytest.fixture(autouse=True)
def _isolate_registry():
    """Drop registry state on entry/exit so each test starts clean.

    Note: clears the type + enum dicts but does not affect Django's app
    registry. The ``ChoiceFixture`` model lives under a synthetic
    ``app_label`` and is created once for the test session.
    """
    registry.clear()
    yield
    registry.clear()


@pytest.fixture(scope="session")
def choice_fixture_model():
    """Session-scoped Django model with two choice columns.

    The choice values are deliberately diverse to exercise sanitization:

    - ``active`` / ``archived``      \u2014 plain identifiers (the happy path).
    - ``first-name``                  \u2014 hyphen \u2192 underscore replacement.
    - ``123abc``                      \u2014 leading digit \u2192 ``MEMBER_`` prefix.
    - ``class``                       \u2014 Python keyword \u2192 underscore prefix.
    """
    STATUS_CHOICES = (
        ("active", "Active"),
        ("archived", "Archived"),
        ("first-name", "First-name"),
        ("123abc", "123abc"),
        ("class", "Class"),
    )

    class ChoiceFixture(models.Model):
        status = models.TextField(choices=STATUS_CHOICES)
        nullable_status = models.TextField(choices=STATUS_CHOICES, null=True)

        class Meta:
            app_label = "test_choice_enums"

    return ChoiceFixture


@pytest.fixture
def grouped_choice_field(choice_fixture_model):
    """Yield ``status`` with grouped-choices monkeypatched in.

    Django's grouped-choices form is a sequence of
    ``(group_label, [...inner_pairs])`` tuples. The patch is reversed in
    teardown so subsequent tests see the original flat choices.
    """
    field = choice_fixture_model._meta.get_field("status")
    original = field.choices
    field.choices = (
        (
            "Active States",
            (
                ("active", "Active"),
                ("archived", "Archived"),
            ),
        ),
    )
    yield field
    field.choices = original


# ---------------------------------------------------------------------------
# Choice enum behavior
# ---------------------------------------------------------------------------


def test_choice_field_generates_strawberry_enum(choice_fixture_model):
    """A ``DjangoType`` over the fixture model produces an enum-typed
    annotation on the choice attribute, named per
    ``f\"{type_name}{PascalCase(field_name)}Enum\"``.
    """

    class FixtureType(DjangoType):
        class Meta:
            model = choice_fixture_model
            fields = ("status",)

    enum_cls = FixtureType.__annotations__["status"]
    assert issubclass(enum_cls, enum.Enum)
    assert enum_cls.__name__ == "FixtureTypeStatusEnum"
    # DB values are preserved on the enum's ``.value`` attribute.
    assert {member.value for member in enum_cls} == {
        "active",
        "archived",
        "first-name",
        "123abc",
        "class",
    }


def test_choice_enum_cached_in_registry_keyed_by_model_field(choice_fixture_model):
    """Once generated, the enum is cached on ``(model, field_name)`` and
    ``registry.get_enum`` returns the identical object on subsequent reads.
    """

    class FixtureType(DjangoType):
        class Meta:
            model = choice_fixture_model
            fields = ("status",)

    cached = registry.get_enum(choice_fixture_model, "status")
    assert cached is FixtureType.__annotations__["status"]
    assert registry.get_enum(choice_fixture_model, "status") is cached


def test_two_djangotypes_reading_same_choice_field_share_one_enum(choice_fixture_model):
    """Two ``DjangoType``s pointing at the same column receive the cached enum.

    The first type wins the enum's GraphQL name; later types reuse the
    same object. The enum's ``__name__`` is set by whichever type
    registered first, even though runtime behaviour is identical.
    """

    class FixtureTypeA(DjangoType):
        class Meta:
            model = choice_fixture_model
            fields = ("status",)

    # Re-using the same model on a second DjangoType raises on type
    # registration; clear the type-side maps but leave the enum cache
    # intact so we can verify cross-type enum reuse.
    registry._types.clear()
    registry._models.clear()

    class FixtureTypeB(DjangoType):
        class Meta:
            model = choice_fixture_model
            fields = ("status",)

    assert FixtureTypeA.__annotations__["status"] is FixtureTypeB.__annotations__["status"]
    # First type wins the enum name regardless of who looks it up next.
    assert FixtureTypeA.__annotations__["status"].__name__ == "FixtureTypeAStatusEnum"


def test_grouped_choices_form_rejected(grouped_choice_field):
    """Django's grouped-choices form raises ``ConfigurationError``, not a silent flatten."""
    with pytest.raises(ConfigurationError, match="grouped-choices"):
        convert_choices_to_enum(grouped_choice_field, "FixtureType")


def test_choice_member_name_sanitization():
    """Hyphenated, leading-digit, and keyword choice values produce safe identifiers.

    Direct unit tests of ``_sanitize_member_name`` so the rules are pinned
    independently of Django field plumbing.
    """
    assert _sanitize_member_name("active") == "active"
    assert _sanitize_member_name("first-name") == "first_name"
    assert _sanitize_member_name("123abc") == "MEMBER_123abc"
    assert _sanitize_member_name("class") == "_class"  # Python keyword
    # Integer values from IntegerChoices.
    assert _sanitize_member_name(1) == "MEMBER_1"
    assert _sanitize_member_name(42) == "MEMBER_42"
    # Empty / pure-symbol input still produces something importable.
    assert _sanitize_member_name("") == "MEMBER_"


def test_choice_enum_with_graphql_reserved_and_non_ascii_values_builds_schema(choice_fixture_model):
    """Reserved, non-ASCII, and introspection-prefixed values produce GraphQL-safe enum members."""
    field = choice_fixture_model._meta.get_field("status")
    original = field.choices
    field.choices = (
        ("true", "True"),
        ("FALSE", "False"),
        ("null", "Null"),
        ("café", "Cafe"),
        ("__private", "Private"),
    )
    registry.clear()
    try:
        enum_cls = convert_choices_to_enum(field, "FixtureType")

        assert [member.name for member in enum_cls] == [
            "MEMBER_true",
            "MEMBER_FALSE",
            "MEMBER_null",
            "caf_",
            "MEMBER___private",
        ]

        @strawberry.type
        class Query:
            @strawberry.field
            def statuses(self) -> list[enum_cls]:
                return list(enum_cls)

        schema = strawberry.Schema(query=Query)
        result = schema.execute_sync("{ statuses }")

        assert result.errors is None
        assert result.data == {
            "statuses": [
                "MEMBER_true",
                "MEMBER_FALSE",
                "MEMBER_null",
                "caf_",
                "MEMBER___private",
            ],
        }
    finally:
        field.choices = original
        registry.clear()


def test_choice_field_with_null_widens_to_enum_or_none(choice_fixture_model):
    """A nullable choice column produces *exactly* ``EnumType | None``.

    Strict equality matters \u2014 if a future ``convert_scalar`` reorder
    accidentally widens before the choices branch fires, the annotation
    would collapse via ``str | None`` and we want that to fail loudly
    rather than silently produce an ``EnumType | None | None`` shape.
    """

    class FixtureType(DjangoType):
        class Meta:
            model = choice_fixture_model
            fields = ("nullable_status",)

    enum_cls = registry.get_enum(choice_fixture_model, "nullable_status")
    assert enum_cls is not None
    assert FixtureType.__annotations__["nullable_status"] == (enum_cls | None)


# ---------------------------------------------------------------------------
# Direct unit coverage of the helpers (covers branches the integration
# tests above don't naturally exercise)
# ---------------------------------------------------------------------------


def test_convert_choices_to_enum_raises_on_empty_choices(choice_fixture_model):
    """A field with ``choices=()`` raises rather than producing an empty enum."""
    field = choice_fixture_model._meta.get_field("status")
    original = field.choices
    field.choices = ()
    try:
        with pytest.raises(ConfigurationError, match="empty"):
            convert_choices_to_enum(field, "FixtureType")
    finally:
        field.choices = original


def test_convert_choices_to_enum_raises_on_sanitized_member_collision(choice_fixture_model):
    """Two choice values that sanitize to the same Python identifier raise.

    Pins the Medium fix from ``rev-types__converters.md``: without the
    collision check, the dict comprehension silently kept the last
    value, leaving the GraphQL enum missing one of the choices and
    producing a runtime coercion error long after schema build.
    """
    field = choice_fixture_model._meta.get_field("status")
    original = field.choices
    # ``a-b`` and ``a_b`` both sanitize to ``a_b``.
    field.choices = (("a-b", "Hyphen"), ("a_b", "Underscore"))
    registry.clear()
    try:
        with pytest.raises(ConfigurationError, match="sanitize to the same enum member"):
            convert_choices_to_enum(field, "FixtureType")
    finally:
        field.choices = original
        registry.clear()


def test_convert_choices_to_enum_raises_on_keyword_prefix_collision(choice_fixture_model):
    """Keyword-prefix collisions also raise: ``"if"`` mangles to ``"_if"`` and collides with raw ``"_if"``.

    Pins the second collision shape from ``rev-types__converters.md``:
    the value ``"if"`` is a Python keyword and is sanitized to ``"_if"``;
    a sibling raw value ``"_if"`` would silently overwrite the first
    without the guard.
    """
    field = choice_fixture_model._meta.get_field("status")
    original = field.choices
    field.choices = (("if", "Conditional"), ("_if", "Underscored"))
    registry.clear()
    try:
        with pytest.raises(ConfigurationError, match="sanitize to the same enum member"):
            convert_choices_to_enum(field, "FixtureType")
    finally:
        field.choices = original
        registry.clear()


def test_convert_choices_to_enum_raises_on_graphql_safe_name_collision(choice_fixture_model):
    """Collision detection runs after GraphQL reserved-name rewriting."""
    field = choice_fixture_model._meta.get_field("status")
    original = field.choices
    field.choices = (("true", "Reserved"), ("MEMBER_true", "Already prefixed"))
    registry.clear()
    try:
        with pytest.raises(ConfigurationError, match="sanitize to the same enum member"):
            convert_choices_to_enum(field, "FixtureType")
    finally:
        field.choices = original
        registry.clear()


# ---------------------------------------------------------------------------
# SCALAR_MAP subclass resolution (High fix from rev-types__converters.md)
# ---------------------------------------------------------------------------


class _TrimmedCharField(models.CharField):
    """Consumer-style subclass of ``CharField``.

    Subclassing a Django field is the normal extension path; exact-type
    ``SCALAR_MAP`` lookup would reject this even though the column still
    stores ``str``.
    """


class _NullableTrimmedCharField(models.CharField):
    """Same shape but with ``null=True`` to exercise widening on a subclass."""


def test_convert_scalar_resolves_subclass_of_supported_field_to_parent_scalar():
    """A consumer subclass of ``CharField`` resolves to ``str`` via MRO walk.

    Pins the High fix from ``rev-types__converters.md``: exact-type
    ``SCALAR_MAP`` lookup misses subclasses, breaking the standard Django
    extension path. The walker must find ``models.CharField`` on the
    subclass MRO and return its mapped scalar.
    """

    class _Owner(models.Model):
        slug = _TrimmedCharField(max_length=32)

        class Meta:
            app_label = "test_choice_enums"

    field = _Owner._meta.get_field("slug")
    assert convert_scalar(field, "OwnerType") is str


def test_convert_scalar_subclass_with_null_widens_through_mro_resolution():
    """The MRO-resolved scalar still flows through the ``null=True`` widening branch."""

    class _Owner(models.Model):
        slug = _NullableTrimmedCharField(max_length=32, null=True)

        class Meta:
            app_label = "test_choice_enums"

    field = _Owner._meta.get_field("slug")
    assert convert_scalar(field, "OwnerType") == (str | None)


def test_convert_scalar_unknown_field_type_still_raises():
    """A field whose MRO does not intersect ``SCALAR_MAP`` still raises.

    Guard against the MRO walk accidentally swallowing the unsupported
    case: ``object`` is on every MRO but is not in ``SCALAR_MAP``.
    """

    class _UnsupportedField(models.Field):
        pass

    class _Owner(models.Model):
        weird = _UnsupportedField()

        class Meta:
            app_label = "test_choice_enums"

    field = _Owner._meta.get_field("weird")
    with pytest.raises(ConfigurationError, match="Unsupported Django field type"):
        convert_scalar(field, "OwnerType")


# ---------------------------------------------------------------------------
# BigInt scalar — schema-execution field-mapping tests (Slice 1)
#
# Synthetic models live under ``app_label = "test_bigint"`` so they do not
# collide with the choice-enum fixture's ``app_label = "test_choice_enums"``.
# Models declared inside test functions per Decision 7's in-function pattern
# (spec lines 641-646) — keeps each test's model declaration adjacent to
# the ``DjangoType`` it powers. ``managed = False`` per spec line 633: no
# migration implication; test rows are instantiated directly when needed.
# ---------------------------------------------------------------------------


def _walk_introspected_type(type_field: dict) -> dict:
    """Walk a GraphQL introspection ``type`` payload to the terminal scalar.

    Wrapping types (``NON_NULL``, ``LIST``) have ``name: None`` per
    Decision 7's introspection note (spec line 167). Walking the chain
    surfaces the inner ``SCALAR { name: "BigInt" }`` regardless of
    nullability / list wrapping.
    """
    current = type_field
    while current.get("ofType") is not None:
        current = current["ofType"]
    return current


def _introspect_field_type(schema: strawberry.Schema, type_name: str, field_name: str) -> dict:
    """Return the introspected ``type`` payload for ``Type.field`` on ``schema``."""
    query = (
        f'{{ __type(name: "{type_name}") {{ fields {{ name type {{ kind name '
        "ofType { kind name ofType { kind name ofType { kind name } } } } } } }"
    )
    result = schema.execute_sync(query)
    assert result.errors is None, result.errors
    fields = result.data["__type"]["fields"]
    for field in fields:
        if field["name"] == field_name:
            return field["type"]
    raise AssertionError(f"field {field_name!r} not found on type {type_name!r}; got {fields!r}")


class _FakeArrayField(models.Field):
    """Test double for ArrayField that does not require django.contrib.postgres.

    Mirrors Django's real ArrayField metadata propagation so base_field has
    model and name attributes when convert_scalar recurses into it. Required
    because convert_choices_to_enum reads field.model.__name__ and field.name
    to build enum_name = f"{type_name}{pascal_case(field.name)}Enum".
    """

    def __init__(self, base_field, **kwargs):
        super().__init__(**kwargs)
        self.base_field = base_field

    def contribute_to_class(self, cls, name, **kwargs):
        super().contribute_to_class(cls, name, **kwargs)
        self.base_field.set_attributes_from_name(name)
        self.base_field.model = cls


class _FakeHStoreField(models.Field):
    """Test double for HStoreField that does not require django.contrib.postgres.

    Tests must call
    monkeypatch.setattr(converters, "_HSTORE_FIELD_CLS", _FakeHStoreField)
    before declaring a DjangoType using this field; otherwise convert_scalar's
    HStore branch never dispatches.
    """

    pass


def test_big_integer_field_maps_to_bigint_in_schema():
    """``BigIntegerField`` (non-null) appears as ``BigInt!`` in the schema."""

    class BigIntOwner(models.Model):
        big = models.BigIntegerField()

        class Meta:
            managed = False
            app_label = "test_bigint"

    class BigIntOwnerType(DjangoType):
        class Meta:
            model = BigIntOwner
            fields = ("big",)

    finalize_django_types()

    @strawberry.type
    class Query:
        @strawberry.field
        def owner(self) -> BigIntOwnerType:
            return BigIntOwner(big=2**62)

    schema = strawberry.Schema(query=Query)
    type_payload = _introspect_field_type(schema, "BigIntOwnerType", "big")
    # NON_NULL wrapper around BigInt scalar.
    assert type_payload["kind"] == "NON_NULL"
    terminal = _walk_introspected_type(type_payload)
    assert terminal["kind"] == "SCALAR"
    assert terminal["name"] == "BigInt"


def test_big_integer_field_nullable_in_schema():
    """``BigIntegerField(null=True)`` appears as ``BigInt`` (nullable)."""

    class BigIntNullableOwner(models.Model):
        big = models.BigIntegerField(null=True)

        class Meta:
            managed = False
            app_label = "test_bigint"

    class BigIntNullableOwnerType(DjangoType):
        class Meta:
            model = BigIntNullableOwner
            fields = ("big",)

    finalize_django_types()

    @strawberry.type
    class Query:
        @strawberry.field
        def owner(self) -> BigIntNullableOwnerType:
            return BigIntNullableOwner(big=None)

    schema = strawberry.Schema(query=Query)
    type_payload = _introspect_field_type(schema, "BigIntNullableOwnerType", "big")
    # Nullable: top-level kind is SCALAR (no NON_NULL wrapper).
    assert type_payload == {"kind": "SCALAR", "name": "BigInt", "ofType": None}


def test_positive_big_integer_field_maps_to_bigint_in_schema():
    """``PositiveBigIntegerField`` now maps to ``BigInt`` (was ``int`` pre-0.0.6)."""

    class PosBigIntOwner(models.Model):
        big_pos = models.PositiveBigIntegerField()

        class Meta:
            managed = False
            app_label = "test_bigint"

    class PosBigIntOwnerType(DjangoType):
        class Meta:
            model = PosBigIntOwner
            fields = ("big_pos",)

    finalize_django_types()

    @strawberry.type
    class Query:
        @strawberry.field
        def owner(self) -> PosBigIntOwnerType:
            return PosBigIntOwner(big_pos=2**62)

    schema = strawberry.Schema(query=Query)
    type_payload = _introspect_field_type(schema, "PosBigIntOwnerType", "bigPos")
    assert type_payload["kind"] == "NON_NULL"
    terminal = _walk_introspected_type(type_payload)
    assert terminal["kind"] == "SCALAR"
    assert terminal["name"] == "BigInt"


def test_big_auto_field_still_maps_to_int():
    """``BigAutoField`` stays mapped to ``Int`` (no current-day recourse for 2**31)."""

    class BigAutoOwner(models.Model):
        # An explicit BigAutoField PK keeps the row's wire shape as Int.
        id = models.BigAutoField(primary_key=True)

        class Meta:
            managed = False
            app_label = "test_bigint"

    class BigAutoOwnerType(DjangoType):
        class Meta:
            model = BigAutoOwner
            fields = ("id",)

    finalize_django_types()

    @strawberry.type
    class Query:
        @strawberry.field
        def owner(self) -> BigAutoOwnerType:
            return BigAutoOwner(id=1)

    schema = strawberry.Schema(query=Query)
    type_payload = _introspect_field_type(schema, "BigAutoOwnerType", "id")
    assert type_payload["kind"] == "NON_NULL"
    terminal = _walk_introspected_type(type_payload)
    assert terminal["kind"] == "SCALAR"
    assert terminal["name"] == "Int"


def test_bigint_serializes_query_result_as_string_via_schema_execution():
    """A resolver returning ``2**62`` round-trips as the decimal string ``"4611686018427387904"``."""

    class BigIntQueryOwner(models.Model):
        big = models.BigIntegerField()

        class Meta:
            managed = False
            app_label = "test_bigint"

    class BigIntQueryOwnerType(DjangoType):
        class Meta:
            model = BigIntQueryOwner
            fields = ("big",)

    finalize_django_types()

    @strawberry.type
    class Query:
        @strawberry.field
        def owner(self) -> BigIntQueryOwnerType:
            return BigIntQueryOwner(big=2**62)

    schema = strawberry.Schema(query=Query)
    result = schema.execute_sync("{ owner { big } }")
    assert result.errors is None
    assert result.data == {"owner": {"big": "4611686018427387904"}}


def test_bigint_parses_string_argument_via_schema_execution():
    """Inbound: a ``BigInt!`` argument provided as a decimal string round-trips through the resolver."""

    @strawberry.type
    class Query:
        @strawberry.field
        def echo(self, val: BigInt) -> BigInt:
            return val

    schema = strawberry.Schema(query=Query)
    result = schema.execute_sync(
        'query { echo(val: "4611686018427387904") }',
    )
    assert result.errors is None
    assert result.data == {"echo": "4611686018427387904"}


def test_bigint_parses_int_argument_via_schema_execution():
    """Inbound: a ``BigInt!`` argument provided as an int literal round-trips through the resolver."""

    @strawberry.type
    class Query:
        @strawberry.field
        def echo(self, val: BigInt) -> BigInt:
            return val

    schema = strawberry.Schema(query=Query)
    result = schema.execute_sync("query { echo(val: 42) }")
    assert result.errors is None
    assert result.data == {"echo": "42"}


def test_bigint_in_input_position_with_null_via_schema_execution():
    """A nullable ``BigInt`` argument accepts ``null`` — Strawberry strips it before
    the parser runs, so the resolver receives ``None``.
    """

    @strawberry.type
    class Query:
        @strawberry.field
        def echo(self, val: BigInt | None = None) -> str:
            return "null" if val is None else str(val)

    schema = strawberry.Schema(query=Query)
    result = schema.execute_sync("query { echo(val: null) }")
    assert result.errors is None
    assert result.data == {"echo": "null"}


def test_bigint_rejects_bool_argument_via_schema_execution():
    """Inbound: ``bool`` literals are rejected by the strict parser at the schema boundary."""

    @strawberry.type
    class Query:
        @strawberry.field
        def echo(self, val: BigInt) -> BigInt:
            return val

    schema = strawberry.Schema(query=Query)
    result = schema.execute_sync("query { echo(val: true) }")
    assert result.errors is not None
    assert len(result.errors) > 0


def test_bigint_rejects_float_argument_via_schema_execution():
    """Inbound: float literals are rejected by the strict parser at the schema boundary."""

    @strawberry.type
    class Query:
        @strawberry.field
        def echo(self, val: BigInt) -> BigInt:
            return val

    schema = strawberry.Schema(query=Query)
    result = schema.execute_sync("query { echo(val: 1.9) }")
    assert result.errors is not None
    assert len(result.errors) > 0


def test_bigint_resolver_returning_bool_raises_via_schema_execution():
    """Outbound: a resolver returning ``True`` (a ``bool``) for a ``BigInt`` annotation
    surfaces a ``TypeError`` at the schema boundary via ``_serialize_bigint``.
    """

    @strawberry.type
    class Query:
        @strawberry.field
        def bool_as_bigint(self) -> BigInt:
            return True  # type: ignore[return-value]

    schema = strawberry.Schema(query=Query)
    result = schema.execute_sync("{ boolAsBigint }")
    assert result.errors is not None
    assert len(result.errors) > 0
    # The strict serializer's error message is the contract source; GraphQL wraps
    # the TypeError in a GraphQLError, so assert on the message substring rather
    # than the exception type.
    assert any("BigInt cannot serialize bool" in str(err) for err in result.errors)


# ---------------------------------------------------------------------------
# JSONField -> ``strawberry.scalars.JSON`` schema-execution tests (Slice 2)
#
# Synthetic models live under ``app_label = "test_jsonfield"`` so they do not
# collide with the BigInt synthetic app (``"test_bigint"``) or the
# choice-enum fixture (``"test_choice_enums"``). Models declared inside test
# functions per Decision 7's in-function pattern; ``managed = False`` keeps
# Django from caring about migrations. The introspection helpers
# (``_introspect_field_type`` / ``_walk_introspected_type``) are reused
# verbatim from the BigInt section above.
# ---------------------------------------------------------------------------


def test_json_field_maps_to_json_scalar_in_schema():
    """``JSONField`` (non-null) appears as ``JSON!`` in the schema."""

    class JsonOwner(models.Model):
        data = models.JSONField()

        class Meta:
            managed = False
            app_label = "test_jsonfield"

    class JsonOwnerType(DjangoType):
        class Meta:
            model = JsonOwner
            fields = ("data",)

    finalize_django_types()

    @strawberry.type
    class Query:
        @strawberry.field
        def owner(self) -> JsonOwnerType:
            return JsonOwner(data={"k": "v"})

    schema = strawberry.Schema(query=Query)
    type_payload = _introspect_field_type(schema, "JsonOwnerType", "data")
    # NON_NULL wrapper around JSON scalar.
    assert type_payload["kind"] == "NON_NULL"
    terminal = _walk_introspected_type(type_payload)
    assert terminal["kind"] == "SCALAR"
    assert terminal["name"] == "JSON"


def test_json_field_nullable_in_schema():
    """``JSONField(null=True)`` appears as ``JSON`` (nullable)."""

    class JsonNullableOwner(models.Model):
        data = models.JSONField(null=True)

        class Meta:
            managed = False
            app_label = "test_jsonfield"

    class JsonNullableOwnerType(DjangoType):
        class Meta:
            model = JsonNullableOwner
            fields = ("data",)

    finalize_django_types()

    @strawberry.type
    class Query:
        @strawberry.field
        def owner(self) -> JsonNullableOwnerType:
            return JsonNullableOwner(data=None)

    schema = strawberry.Schema(query=Query)
    type_payload = _introspect_field_type(schema, "JsonNullableOwnerType", "data")
    # Nullable: top-level kind is SCALAR (no NON_NULL wrapper).
    assert type_payload == {"kind": "SCALAR", "name": "JSON", "ofType": None}


def test_json_field_round_trips_dict_via_schema_execution():
    """A resolver returning a JSON-shaped dict round-trips verbatim through ``schema.execute_sync``."""

    class JsonRoundTripOwner(models.Model):
        data = models.JSONField()

        class Meta:
            managed = False
            app_label = "test_jsonfield"

    class JsonRoundTripOwnerType(DjangoType):
        class Meta:
            model = JsonRoundTripOwner
            fields = ("data",)

    finalize_django_types()

    payload = {"k1": "v1", "k2": 2, "k3": [1, 2, 3], "k4": None}

    @strawberry.type
    class Query:
        @strawberry.field
        def owner(self) -> JsonRoundTripOwnerType:
            return JsonRoundTripOwner(data=payload)

    schema = strawberry.Schema(query=Query)
    result = schema.execute_sync("{ owner { data } }")
    assert result.errors is None
    assert result.data == {"owner": {"data": payload}}


# ---------------------------------------------------------------------------
# ArrayField -> list[T] sentinel-guarded recursion (Slice 3)
#
# Synthetic models live under ``app_label = "test_arrayfield"`` so they do
# not collide with the prior synthetic apps (``test_bigint``, ``test_jsonfield``,
# ``test_choice_enums``). Sentinel-branch tests monkey-patch
# ``converters._ARRAY_FIELD_CLS = _FakeArrayField`` BEFORE declaring the
# ``DjangoType`` (Decision 7 spec line 635). Helper-resolver tests use
# ``sys.modules`` manipulation per Decision 7 spec lines 661-676.
# ---------------------------------------------------------------------------


def test_resolve_array_field_returns_class_when_postgres_fields_importable(monkeypatch):
    """``_resolve_array_field()`` returns the ``ArrayField`` class when the
    ``django.contrib.postgres.fields`` module is importable.
    """
    import sys
    import types as _types

    fake = _types.ModuleType("django.contrib.postgres.fields")
    fake.ArrayField = _FakeArrayField
    monkeypatch.setitem(sys.modules, "django.contrib.postgres.fields", fake)
    from django_strawberry_framework.types.converters import _resolve_array_field

    assert _resolve_array_field() is _FakeArrayField


def test_resolve_array_field_returns_none_when_postgres_fields_unimportable(monkeypatch):
    """``_resolve_array_field()`` returns ``None`` when the postgres-contrib
    fields module is unavailable. Setting ``sys.modules[name] = None`` forces
    the next ``import name`` to raise ``ImportError``.
    """
    import sys

    monkeypatch.setitem(sys.modules, "django.contrib.postgres.fields", None)
    from django_strawberry_framework.types.converters import _resolve_array_field

    assert _resolve_array_field() is None


def test_array_field_of_int_maps_to_list_int_via_fake_sentinel(monkeypatch):
    """``ArrayField(IntegerField())`` maps to ``list[int]`` (non-null outer + inner)."""
    monkeypatch.setattr(converters, "_ARRAY_FIELD_CLS", _FakeArrayField)

    class ArrayIntOwner(models.Model):
        arr = _FakeArrayField(models.IntegerField())

        class Meta:
            managed = False
            app_label = "test_arrayfield"

    class ArrayIntOwnerType(DjangoType):
        class Meta:
            model = ArrayIntOwner
            fields = ("arr",)

    finalize_django_types()

    @strawberry.type
    class Query:
        @strawberry.field
        def owner(self) -> ArrayIntOwnerType:
            return ArrayIntOwner(arr=[1, 2, 3])

    schema = strawberry.Schema(query=Query)
    type_payload = _introspect_field_type(schema, "ArrayIntOwnerType", "arr")
    # NON_NULL -> LIST -> NON_NULL -> SCALAR { name: "Int" }
    assert type_payload["kind"] == "NON_NULL"
    assert type_payload["ofType"]["kind"] == "LIST"
    assert type_payload["ofType"]["ofType"]["kind"] == "NON_NULL"
    terminal = _walk_introspected_type(type_payload)
    assert terminal["kind"] == "SCALAR"
    assert terminal["name"] == "Int"


def test_array_field_of_char_maps_to_list_str_via_fake_sentinel(monkeypatch):
    """``ArrayField(CharField())`` maps to ``list[str]`` (terminal SCALAR name "String")."""
    monkeypatch.setattr(converters, "_ARRAY_FIELD_CLS", _FakeArrayField)

    class ArrayCharOwner(models.Model):
        arr = _FakeArrayField(models.CharField(max_length=20))

        class Meta:
            managed = False
            app_label = "test_arrayfield"

    class ArrayCharOwnerType(DjangoType):
        class Meta:
            model = ArrayCharOwner
            fields = ("arr",)

    finalize_django_types()

    @strawberry.type
    class Query:
        @strawberry.field
        def owner(self) -> ArrayCharOwnerType:
            return ArrayCharOwner(arr=["a", "b"])

    schema = strawberry.Schema(query=Query)
    type_payload = _introspect_field_type(schema, "ArrayCharOwnerType", "arr")
    assert type_payload["kind"] == "NON_NULL"
    assert type_payload["ofType"]["kind"] == "LIST"
    assert type_payload["ofType"]["ofType"]["kind"] == "NON_NULL"
    terminal = _walk_introspected_type(type_payload)
    assert terminal["kind"] == "SCALAR"
    assert terminal["name"] == "String"


def test_array_field_nullable_inner_via_fake_sentinel(monkeypatch):
    """``ArrayField(IntegerField(null=True))`` maps to ``list[int | None]``.

    Inner ``null=True`` drops the inner ``NON_NULL`` wrapper; outer stays
    non-null. Introspection chain: ``NON_NULL -> LIST -> SCALAR``.
    """
    monkeypatch.setattr(converters, "_ARRAY_FIELD_CLS", _FakeArrayField)

    class ArrayNullableInnerOwner(models.Model):
        arr = _FakeArrayField(models.IntegerField(null=True))

        class Meta:
            managed = False
            app_label = "test_arrayfield"

    class ArrayNullableInnerOwnerType(DjangoType):
        class Meta:
            model = ArrayNullableInnerOwner
            fields = ("arr",)

    finalize_django_types()

    @strawberry.type
    class Query:
        @strawberry.field
        def owner(self) -> ArrayNullableInnerOwnerType:
            return ArrayNullableInnerOwner(arr=[1, None, 2])

    schema = strawberry.Schema(query=Query)
    type_payload = _introspect_field_type(schema, "ArrayNullableInnerOwnerType", "arr")
    assert type_payload["kind"] == "NON_NULL"
    assert type_payload["ofType"]["kind"] == "LIST"
    # Inner-null drops the NON_NULL: directly SCALAR underneath LIST.
    assert type_payload["ofType"]["ofType"]["kind"] == "SCALAR"
    assert type_payload["ofType"]["ofType"]["name"] == "Int"


def test_array_field_outer_nullable_via_fake_sentinel(monkeypatch):
    """``ArrayField(IntegerField(), null=True)`` maps to ``list[int] | None``.

    Outer ``null=True`` drops the outer ``NON_NULL`` wrapper; inner stays
    non-null. Introspection chain: ``LIST -> NON_NULL -> SCALAR``.
    """
    monkeypatch.setattr(converters, "_ARRAY_FIELD_CLS", _FakeArrayField)

    class ArrayOuterNullableOwner(models.Model):
        arr = _FakeArrayField(models.IntegerField(), null=True)

        class Meta:
            managed = False
            app_label = "test_arrayfield"

    class ArrayOuterNullableOwnerType(DjangoType):
        class Meta:
            model = ArrayOuterNullableOwner
            fields = ("arr",)

    finalize_django_types()

    @strawberry.type
    class Query:
        @strawberry.field
        def owner(self) -> ArrayOuterNullableOwnerType:
            return ArrayOuterNullableOwner(arr=None)

    schema = strawberry.Schema(query=Query)
    type_payload = _introspect_field_type(schema, "ArrayOuterNullableOwnerType", "arr")
    # Outer-null drops the NON_NULL: top-level kind is LIST.
    assert type_payload["kind"] == "LIST"
    assert type_payload["ofType"]["kind"] == "NON_NULL"
    assert type_payload["ofType"]["ofType"]["kind"] == "SCALAR"
    assert type_payload["ofType"]["ofType"]["name"] == "Int"


def test_array_field_multidim_rejected_via_fake_sentinel(monkeypatch):
    """Nested ``ArrayField`` raises ``ConfigurationError`` at type creation."""
    monkeypatch.setattr(converters, "_ARRAY_FIELD_CLS", _FakeArrayField)

    class ArrayMultidimOwner(models.Model):
        arr = _FakeArrayField(_FakeArrayField(models.IntegerField()))

        class Meta:
            managed = False
            app_label = "test_arrayfield"

    with pytest.raises(ConfigurationError, match="Nested ArrayField on"):

        class ArrayMultidimOwnerType(DjangoType):
            class Meta:
                model = ArrayMultidimOwner
                fields = ("arr",)


def test_array_field_choices_inner_via_fake_sentinel(monkeypatch):
    """``ArrayField(CharField(choices=...))`` produces ``list[<TypeName><FieldName>Enum]``.

    The recursive ``convert_scalar(field.base_field, type_name)`` call hits
    the existing choice-enum branch on ``base_field``, so the inner type is
    an enum scalar.
    """
    monkeypatch.setattr(converters, "_ARRAY_FIELD_CLS", _FakeArrayField)

    class ArrayChoicesInnerOwner(models.Model):
        arr = _FakeArrayField(
            models.CharField(max_length=5, choices=[("A", "A"), ("B", "B")]),
        )

        class Meta:
            managed = False
            app_label = "test_arrayfield"

    class ArrayChoicesInnerOwnerType(DjangoType):
        class Meta:
            model = ArrayChoicesInnerOwner
            fields = ("arr",)

    finalize_django_types()

    @strawberry.type
    class Query:
        @strawberry.field
        def owner(self) -> ArrayChoicesInnerOwnerType:
            return ArrayChoicesInnerOwner(arr=["A", "B"])

    schema = strawberry.Schema(query=Query)
    type_payload = _introspect_field_type(schema, "ArrayChoicesInnerOwnerType", "arr")
    assert type_payload["kind"] == "NON_NULL"
    assert type_payload["ofType"]["kind"] == "LIST"
    terminal = _walk_introspected_type(type_payload)
    assert terminal["kind"] == "ENUM"


def test_array_field_outer_choices_rejected_via_fake_sentinel(monkeypatch):
    """Outer ``choices`` on ``ArrayField`` raises ``ConfigurationError``.

    Spec-pinned error message mentions ``base_field`` and ``FilterSet`` as
    the consumer recourse.
    """
    monkeypatch.setattr(converters, "_ARRAY_FIELD_CLS", _FakeArrayField)

    class ArrayOuterChoicesOwner(models.Model):
        arr = _FakeArrayField(
            models.IntegerField(),
            choices=[(1, "one"), (2, "two")],
        )

        class Meta:
            managed = False
            app_label = "test_arrayfield"

    with pytest.raises(ConfigurationError, match="declares choices on the outer"):

        class ArrayOuterChoicesOwnerType(DjangoType):
            class Meta:
                model = ArrayOuterChoicesOwner
                fields = ("arr",)


def test_array_field_base_field_unsupported_type_raises(monkeypatch):
    """An unsupported ``base_field`` type surfaces the existing
    ``Unsupported Django field type`` error via the recursive call.
    """
    monkeypatch.setattr(converters, "_ARRAY_FIELD_CLS", _FakeArrayField)

    class _Weird(models.Field):
        pass

    class ArrayUnsupportedBaseOwner(models.Model):
        arr = _FakeArrayField(_Weird())

        class Meta:
            managed = False
            app_label = "test_arrayfield"

    with pytest.raises(ConfigurationError, match="Unsupported Django field type"):

        class ArrayUnsupportedBaseOwnerType(DjangoType):
            class Meta:
                model = ArrayUnsupportedBaseOwner
                fields = ("arr",)


def test_array_field_sentinel_none_path(monkeypatch):
    """With ``_ARRAY_FIELD_CLS = None`` the sentinel short-circuits and the
    field falls through to the MRO walk's unsupported-field error.

    Pins the short-circuit guard: without ``_ARRAY_FIELD_CLS is not None``,
    the ``isinstance(field, _ARRAY_FIELD_CLS)`` call would ``TypeError``.
    """
    monkeypatch.setattr(converters, "_ARRAY_FIELD_CLS", None)

    class ArraySentinelNoneOwner(models.Model):
        arr = _FakeArrayField(models.IntegerField())

        class Meta:
            managed = False
            app_label = "test_arrayfield"

    with pytest.raises(ConfigurationError, match="Unsupported Django field type"):

        class ArraySentinelNoneOwnerType(DjangoType):
            class Meta:
                model = ArraySentinelNoneOwner
                fields = ("arr",)


def test_real_array_field_compatible_with_strawberry():
    """Optional gated test: real ``django.contrib.postgres.fields.ArrayField``
    flows through the sentinel branch end-to-end on a postgres-equipped env.
    """
    postgres_fields = pytest.importorskip("django.contrib.postgres.fields")

    class RealArrayIntOwner(models.Model):
        arr = postgres_fields.ArrayField(models.IntegerField())

        class Meta:
            managed = False
            app_label = "test_arrayfield"

    class RealArrayIntOwnerType(DjangoType):
        class Meta:
            model = RealArrayIntOwner
            fields = ("arr",)

    finalize_django_types()

    @strawberry.type
    class Query:
        @strawberry.field
        def owner(self) -> RealArrayIntOwnerType:
            return RealArrayIntOwner(arr=[1, 2, 3])

    schema = strawberry.Schema(query=Query)
    type_payload = _introspect_field_type(schema, "RealArrayIntOwnerType", "arr")
    # NON_NULL -> LIST -> NON_NULL -> SCALAR { name: "Int" }
    assert type_payload["kind"] == "NON_NULL"
    assert type_payload["ofType"]["kind"] == "LIST"
    assert type_payload["ofType"]["ofType"]["kind"] == "NON_NULL"
    terminal = _walk_introspected_type(type_payload)
    assert terminal["kind"] == "SCALAR"
    assert terminal["name"] == "Int"


# ---------------------------------------------------------------------------
# HStoreField -> strawberry.scalars.JSON sentinel-guarded branch (Slice 4)
#
# Synthetic models live under ``app_label = "test_hstorefield"`` so they do
# not collide with the prior synthetic apps (``test_bigint``,
# ``test_jsonfield``, ``test_arrayfield``, ``test_choice_enums``). Sentinel-
# branch tests monkey-patch
# ``converters._HSTORE_FIELD_CLS = _FakeHStoreField`` BEFORE declaring the
# ``DjangoType`` (Decision 7 spec line 635). Helper-resolver tests use
# ``sys.modules`` manipulation per Decision 7 spec lines 661-676.
# ---------------------------------------------------------------------------


def test_resolve_hstore_field_returns_class_when_postgres_fields_importable(monkeypatch):
    """``_resolve_hstore_field()`` returns the ``HStoreField`` class when the
    ``django.contrib.postgres.fields`` module is importable.
    """
    import sys
    import types as _types

    fake = _types.ModuleType("django.contrib.postgres.fields")
    fake.HStoreField = _FakeHStoreField
    monkeypatch.setitem(sys.modules, "django.contrib.postgres.fields", fake)
    from django_strawberry_framework.types.converters import _resolve_hstore_field

    assert _resolve_hstore_field() is _FakeHStoreField


def test_resolve_hstore_field_returns_none_when_postgres_fields_unimportable(monkeypatch):
    """``_resolve_hstore_field()`` returns ``None`` when the postgres-contrib
    fields module is unavailable. Setting ``sys.modules[name] = None`` forces
    the next ``import name`` to raise ``ImportError``.
    """
    import sys

    monkeypatch.setitem(sys.modules, "django.contrib.postgres.fields", None)
    from django_strawberry_framework.types.converters import _resolve_hstore_field

    assert _resolve_hstore_field() is None


def test_hstore_field_maps_to_json_scalar_via_fake_sentinel(monkeypatch):
    """``HStoreField`` (non-null) appears as ``JSON!`` in the schema."""
    monkeypatch.setattr(converters, "_HSTORE_FIELD_CLS", _FakeHStoreField)

    class HStoreOwner(models.Model):
        data = _FakeHStoreField()

        class Meta:
            managed = False
            app_label = "test_hstorefield"

    class HStoreOwnerType(DjangoType):
        class Meta:
            model = HStoreOwner
            fields = ("data",)

    finalize_django_types()

    @strawberry.type
    class Query:
        @strawberry.field
        def owner(self) -> HStoreOwnerType:
            return HStoreOwner(data={"k": "v"})

    schema = strawberry.Schema(query=Query)
    type_payload = _introspect_field_type(schema, "HStoreOwnerType", "data")
    # NON_NULL wrapper around JSON scalar.
    assert type_payload["kind"] == "NON_NULL"
    terminal = _walk_introspected_type(type_payload)
    assert terminal["kind"] == "SCALAR"
    assert terminal["name"] == "JSON"


def test_hstore_field_nullable_via_fake_sentinel(monkeypatch):
    """``HStoreField(null=True)`` appears as ``JSON`` (nullable)."""
    monkeypatch.setattr(converters, "_HSTORE_FIELD_CLS", _FakeHStoreField)

    class HStoreNullableOwner(models.Model):
        data = _FakeHStoreField(null=True)

        class Meta:
            managed = False
            app_label = "test_hstorefield"

    class HStoreNullableOwnerType(DjangoType):
        class Meta:
            model = HStoreNullableOwner
            fields = ("data",)

    finalize_django_types()

    @strawberry.type
    class Query:
        @strawberry.field
        def owner(self) -> HStoreNullableOwnerType:
            return HStoreNullableOwner(data=None)

    schema = strawberry.Schema(query=Query)
    type_payload = _introspect_field_type(schema, "HStoreNullableOwnerType", "data")
    # Nullable: top-level kind is SCALAR (no NON_NULL wrapper).
    assert type_payload == {"kind": "SCALAR", "name": "JSON", "ofType": None}


def test_hstore_field_resolver_dict_serializes_via_schema_execution(monkeypatch):
    """Serializer-level test: a resolver returning a hand-built dict round-trips
    verbatim through the ``JSON`` scalar via ``schema.execute_sync``.

    No DB persistence — SQLite cannot store HStore values; the test exercises
    only the scalar's wire-level serialization through Strawberry.
    """
    monkeypatch.setattr(converters, "_HSTORE_FIELD_CLS", _FakeHStoreField)

    class HStoreSerializeOwner(models.Model):
        data = _FakeHStoreField()

        class Meta:
            managed = False
            app_label = "test_hstorefield"

    class HStoreSerializeOwnerType(DjangoType):
        class Meta:
            model = HStoreSerializeOwner
            fields = ("data",)

    finalize_django_types()

    payload = {"k1": "v1"}

    @strawberry.type
    class Query:
        @strawberry.field
        def owner(self) -> HStoreSerializeOwnerType:
            return HStoreSerializeOwner(data=payload)

    schema = strawberry.Schema(query=Query)
    result = schema.execute_sync("{ owner { data } }")
    assert result.errors is None
    assert result.data == {"owner": {"data": payload}}


def test_hstore_field_resolver_dict_with_none_value_via_schema_execution(monkeypatch):
    """A resolver returning ``{"k1": "v", "k2": None}`` round-trips with the
    ``None`` value preserved inside the dict — mirrors ``HStoreField``'s native
    ``dict[str, str | None]`` shape.
    """
    monkeypatch.setattr(converters, "_HSTORE_FIELD_CLS", _FakeHStoreField)

    class HStoreNoneValueOwner(models.Model):
        data = _FakeHStoreField()

        class Meta:
            managed = False
            app_label = "test_hstorefield"

    class HStoreNoneValueOwnerType(DjangoType):
        class Meta:
            model = HStoreNoneValueOwner
            fields = ("data",)

    finalize_django_types()

    payload = {"k1": "v", "k2": None}

    @strawberry.type
    class Query:
        @strawberry.field
        def owner(self) -> HStoreNoneValueOwnerType:
            return HStoreNoneValueOwner(data=payload)

    schema = strawberry.Schema(query=Query)
    result = schema.execute_sync("{ owner { data } }")
    assert result.errors is None
    assert result.data == {"owner": {"data": payload}}


def test_hstore_field_outer_choices_rejected_via_fake_sentinel(monkeypatch):
    """Outer ``choices`` on ``HStoreField`` raises ``ConfigurationError``.

    HStore stores ``dict[str, str | None]`` with no enum-able shape at the
    GraphQL boundary; the rejection message names that rationale.
    """
    monkeypatch.setattr(converters, "_HSTORE_FIELD_CLS", _FakeHStoreField)

    class HStoreOuterChoicesOwner(models.Model):
        data = _FakeHStoreField(choices=[("a", "A")])

        class Meta:
            managed = False
            app_label = "test_hstorefield"

    with pytest.raises(ConfigurationError, match="declares choices"):

        class HStoreOuterChoicesOwnerType(DjangoType):
            class Meta:
                model = HStoreOuterChoicesOwner
                fields = ("data",)


def test_hstore_field_sentinel_none_path(monkeypatch):
    """With ``_HSTORE_FIELD_CLS = None`` the sentinel short-circuits and the
    field falls through to the MRO walk's unsupported-field error.

    Pins the short-circuit guard: without ``_HSTORE_FIELD_CLS is not None``,
    the ``isinstance(field, _HSTORE_FIELD_CLS)`` call would ``TypeError``.
    """
    monkeypatch.setattr(converters, "_HSTORE_FIELD_CLS", None)

    class HStoreSentinelNoneOwner(models.Model):
        data = _FakeHStoreField()

        class Meta:
            managed = False
            app_label = "test_hstorefield"

    with pytest.raises(ConfigurationError, match="Unsupported Django field type"):

        class HStoreSentinelNoneOwnerType(DjangoType):
            class Meta:
                model = HStoreSentinelNoneOwner
                fields = ("data",)


def test_real_hstore_field_compatible_with_strawberry():
    """Optional gated test: real ``django.contrib.postgres.fields.HStoreField``
    flows through the sentinel branch end-to-end on a postgres-equipped env.

    Asserts both the introspection chain (``NON_NULL -> SCALAR { name: "JSON" }``)
    and resolver round-tripping (``{"k1": "v", "k2": None}`` preserved).
    """
    postgres_fields = pytest.importorskip("django.contrib.postgres.fields")

    class RealHStoreOwner(models.Model):
        data = postgres_fields.HStoreField()

        class Meta:
            managed = False
            app_label = "test_hstorefield"

    class RealHStoreOwnerType(DjangoType):
        class Meta:
            model = RealHStoreOwner
            fields = ("data",)

    finalize_django_types()

    payload = {"k1": "v", "k2": None}

    @strawberry.type
    class Query:
        @strawberry.field
        def owner(self) -> RealHStoreOwnerType:
            return RealHStoreOwner(data=payload)

    schema = strawberry.Schema(query=Query)
    type_payload = _introspect_field_type(schema, "RealHStoreOwnerType", "data")
    # NON_NULL -> SCALAR { name: "JSON" }
    assert type_payload["kind"] == "NON_NULL"
    terminal = _walk_introspected_type(type_payload)
    assert terminal["kind"] == "SCALAR"
    assert terminal["name"] == "JSON"

    result = schema.execute_sync("{ owner { data } }")
    assert result.errors is None
    assert result.data == {"owner": {"data": payload}}
