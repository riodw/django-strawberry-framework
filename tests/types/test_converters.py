"""Converter tests for scalars, enums, relations, PostgreSQL containers, and file/image output objects.

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
import itertools

import pytest
import strawberry
from django.db import models

from django_strawberry_framework import (
    BigInt,
    DjangoType,
    finalize_django_types,
    strawberry_config,
)
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.registry import registry
from django_strawberry_framework.types import converters
from django_strawberry_framework.types.converters import (
    FIELD_OUTPUT_TYPE_MAP,
    SCALAR_MAP,
    DjangoFileType,
    DjangoImageType,
    _field_output_type_for,
    _sanitize_member_name,
    convert_choices_to_enum,
    convert_field_output,
    convert_scalar,
    scalar_for_field,
)

_app_label_counter = itertools.count(1)


def _unique_app_label(base: str) -> str:
    """Return a unique ``app_label`` per call to suppress Django's ``Model already registered`` warning.

    Multiple tests in this module declare same-named synthetic ``managed=False``
    models (canonically ``_Owner``) under a shared ``app_label`` such as
    ``test_choice_enums``. Django's app registry raises a ``RuntimeWarning``
    on the second and subsequent registrations because the
    ``(app_label, model_name)`` key collides. Routing the ``app_label``
    through this helper namespaces each test's synthetic model with a
    monotonically increasing suffix so the registry sees a fresh key per
    call. The choice fixture itself (``ChoiceFixture``) is session-scoped
    and registers exactly once, so it does not use this helper.
    """
    return f"{base}__{next(_app_label_counter)}"


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
    field.choices = (("Active States", (("active", "Active"), ("archived", "Archived"))),)
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

    # Drop FixtureTypeA from the registry's type/model maps but leave
    # the enum cache intact so we can verify cross-type enum reuse via
    # FixtureTypeB. ``unregister`` skips ``_enums``.
    registry.unregister(FixtureTypeA)

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


def test_sanitize_member_name_neutralizes_python_enum_reserved_shapes():
    """Values that sanitize to Python-``enum``-reserved member names get ``MEMBER_``-prefixed.

    ``Enum(cls_name, {name: value})`` refuses ``"mro"`` and treats any single-
    underscore ``_sunder_`` name as a reserved directive -- raising for most
    (``_x_`` / ``_name_``) and SILENTLY dropping the recognised ones
    (``_ignore_`` / ``_missing_``). Python 3.11+ also silently omits names in the
    generated class's private namespace. ``_sanitize_member_name`` must rewrite
    every such shape with the same ``MEMBER_`` prefix it already uses for
    GraphQL-reserved and introspection-prefixed names, so no hostile choice value
    escapes as a raw ``enum`` crash, a vanished member, or a version-dependent
    schema.
    """
    # Symbol-wrapped tokens collapse to a ``_word_`` sunder shape and must be
    # neutralised (previously a raw ``ValueError`` from ``Enum(...)``).
    assert _sanitize_member_name("-x-") == "MEMBER__x_"
    assert _sanitize_member_name("[a]") == "MEMBER__a_"
    assert _sanitize_member_name("-1-") == "MEMBER__1_"
    # Recognised sunder directives (previously SILENTLY dropped as members).
    assert _sanitize_member_name("_ignore_") == "MEMBER__ignore_"
    assert _sanitize_member_name("_missing_") == "MEMBER__missing_"
    # The special-cased ``mro`` (case-sensitive: only the lowercase form is reserved).
    assert _sanitize_member_name("mro") == "MEMBER_mro"
    assert _sanitize_member_name("MRO") == "MRO"
    # A generated enum's class-private namespace is class-name-specific and
    # silently becomes an attribute instead of a member without the prefix.
    assert (
        _sanitize_member_name(
            "_FixtureTypeStatusEnum__hidden",
            enum_name="FixtureTypeStatusEnum",
        )
        == "MEMBER__FixtureTypeStatusEnum__hidden"
    )
    assert (
        _sanitize_member_name("_OtherEnum__hidden", enum_name="FixtureTypeStatusEnum")
        == "_OtherEnum__hidden"
    )
    # Non-sunder single-underscore names stay untouched (boundary guards).
    assert _sanitize_member_name("_x") == "_x"  # no trailing underscore
    assert _sanitize_member_name("x_") == "x_"  # no leading underscore
    assert _sanitize_member_name("caf\u00e9") == "caf_"  # trailing-only underscore


def test_choice_enum_with_graphql_reserved_and_non_ascii_values_builds_schema(
    choice_fixture_model,
):
    """Reserved, non-ASCII, and introspection-prefixed values produce GraphQL-safe enum members."""
    field = choice_fixture_model._meta.get_field("status")
    original = field.choices
    field.choices = (
        ("true", "True"),
        ("FALSE", "False"),
        ("null", "Null"),
        ("caf\u00e9", "Cafe"),
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


def test_convert_choices_to_enum_with_python_enum_reserved_values_builds_schema(
    choice_fixture_model,
):
    """Choice values that map to Python-``enum``-reserved member names build a working enum.

    Without the ``_is_enum_reserved_member`` neutralisation in
    ``_sanitize_member_name`` this raised a raw ``ValueError`` from ``Enum(...)``
    for the ``_sunder_``-shaped / ``mro`` values (``"-x-"``, ``"mro"``) and --
    worse -- SILENTLY dropped the recognised-directive value ``"_ignore_"`` from
    the enum. Python 3.11+ also dropped ``"_FixtureTypeStatusEnum__hidden"`` as a
    class-private attribute, making the generated schema interpreter-dependent.
    Every choice must survive as a member with its DB value preserved and the
    schema must build + execute.
    """
    field = choice_fixture_model._meta.get_field("status")
    original = field.choices
    field.choices = (
        ("-x-", "Dash X"),  # -> _x_ sunder shape: previously ValueError at Enum build.
        ("mro", "Method Resolution Order"),  # previously ValueError at Enum build.
        ("_ignore_", "Ignore Directive"),  # previously SILENTLY dropped as a member.
        # Previously SILENTLY installed as a class attribute, not a member.
        ("_FixtureTypeStatusEnum__hidden", "Private Namespace"),
        ("active", "Active"),  # plain control value.
    )
    registry.clear()
    try:
        enum_cls = convert_choices_to_enum(field, "FixtureType")

        # Every choice value survives as a distinct member (none dropped).
        assert {member.value for member in enum_cls} == {
            "-x-",
            "mro",
            "_ignore_",
            "_FixtureTypeStatusEnum__hidden",
            "active",
        }
        assert [member.name for member in enum_cls] == [
            "MEMBER__x_",
            "MEMBER_mro",
            "MEMBER__ignore_",
            "MEMBER__FixtureTypeStatusEnum__hidden",
            "active",
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
                "MEMBER__x_",
                "MEMBER_mro",
                "MEMBER__ignore_",
                "MEMBER__FixtureTypeStatusEnum__hidden",
                "active",
            ],
        }
    finally:
        field.choices = original
        registry.clear()


def test_convert_choices_to_enum_raises_on_enum_reserved_sanitize_collision(choice_fixture_model):
    """Collision detection still fires after the Python-``enum``-reserved rewrite.

    ``"-x-"`` and ``"_x_"`` both sanitize to ``MEMBER__x_``; the collision must
    surface as the localised ``ConfigurationError`` rather than a silently
    dropped member -- the same contract already held for the
    ``true`` / ``MEMBER_true`` GraphQL-reserved collision above.
    """
    field = choice_fixture_model._meta.get_field("status")
    original = field.choices
    field.choices = (("-x-", "Symbol wrapped"), ("_x_", "Sunder shaped"))
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
            app_label = _unique_app_label("test_choice_enums")

    field = _Owner._meta.get_field("slug")
    assert convert_scalar(field, "OwnerType") is str


def test_convert_scalar_subclass_with_null_widens_through_mro_resolution():
    """The MRO-resolved scalar still flows through the ``null=True`` widening branch."""

    class _Owner(models.Model):
        slug = _NullableTrimmedCharField(max_length=32, null=True)

        class Meta:
            app_label = _unique_app_label("test_choice_enums")

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
            app_label = _unique_app_label("test_choice_enums")

    field = _Owner._meta.get_field("weird")
    with pytest.raises(ConfigurationError, match="Unsupported Django field type"):
        convert_scalar(field, "OwnerType")


def test_convert_scalar_duration_field_raises_unsupported():
    """``DurationField`` is intentionally absent from ``SCALAR_MAP``.

    Strawberry refuses ``datetime.timedelta`` at schema construction time
    (no first-party scalar), so leaving the entry in mapped it to a type
    that crashed downstream with a less-localized ``TypeError`` from the
    Strawberry frame. Surfacing the error at class-definition time via the
    standard ``Unsupported Django field type`` raise keeps the failure
    grep-stable for the consumer. A custom scalar is the supported
    extension path (``SCALAR_MAP[DurationField] = MyDurationScalar``).
    """

    class _Owner(models.Model):
        elapsed = models.DurationField()

        class Meta:
            app_label = _unique_app_label("test_choice_enums")

    field = _Owner._meta.get_field("elapsed")
    with pytest.raises(ConfigurationError, match="Unsupported Django field type"):
        convert_scalar(field, "OwnerType")


def test_convert_scalar_binary_field_raises_unsupported():
    """``BinaryField`` is intentionally absent from ``SCALAR_MAP``.

    Same reasoning as ``DurationField``: Strawberry has no first-party
    ``bytes`` scalar so the prior mapping crashed at schema build. The
    documented extension hook is
    ``SCALAR_MAP[BinaryField] = strawberry.scalars.Base64``.
    """

    class _Owner(models.Model):
        blob = models.BinaryField()

        class Meta:
            app_label = _unique_app_label("test_choice_enums")

    field = _Owner._meta.get_field("blob")
    with pytest.raises(ConfigurationError, match="Unsupported Django field type"):
        convert_scalar(field, "OwnerType")


# ---------------------------------------------------------------------------
# BigInt scalar - package-internal contract tests
#
# The field-mapping introspection tests and the basic outbound/inbound
# round-trip tests were migrated to live ``/graphql/`` coverage on the
# scalars app (``examples/fakeshop/test_query/test_scalars_api.py``). What
# remains here is unreachable from a real HTTP path:
#
# - ``test_big_auto_field_still_maps_to_int`` - sibling case asserting
#   ``BigAutoField -> Int`` (NOT BigInt). The scalars app's id columns
#   are also ``BigAutoField`` but the example schema doesn't introspect
#   into the synthetic ``managed=False`` shape this test needs.
# - Four BigInt rejection / edge tests (``null`` input, bool / float
#   argument rejection, bool return-value rejection). The strict parser
#   / serializer error contracts surface as ``GraphQLError`` from
#   Strawberry - reachable via HTTP in principle but the package test is
#   the contract source; HTTP coverage would only re-verify what the
#   library round-trip tests already prove for non-error inputs.
#
# Synthetic models live under ``app_label = "test_bigint"`` so they do not
# collide with the choice-enum fixture's ``app_label = "test_choice_enums"``.
# ``managed = False`` per Decision 7 spec #"every test model hosting `_FakeArrayField` or `_FakeHStoreField` declares `class Meta: managed = False`":
# no migration implication; test rows are instantiated directly when needed.
# ---------------------------------------------------------------------------


def _walk_introspected_type(type_field: dict) -> dict:
    """Walk a GraphQL introspection ``type`` payload to the terminal scalar.

    Wrapping types (``NON_NULL``, ``LIST``) have ``name: None`` per
    Decision 7's introspection note (spec #"walk it explicitly rather than asserting on `field.type.name`"). Walking the chain
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


def test_bigint_in_input_position_with_null_via_schema_execution():
    """A nullable ``BigInt`` argument accepts ``null`` - Strawberry strips it before
    the parser runs, so the resolver receives ``None``.
    """

    @strawberry.type
    class Query:
        @strawberry.field
        def echo(self, val: BigInt | None = None) -> str:
            return "null" if val is None else str(val)

    schema = strawberry.Schema(query=Query, config=strawberry_config())
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

    schema = strawberry.Schema(query=Query, config=strawberry_config())
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

    schema = strawberry.Schema(query=Query, config=strawberry_config())
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

    schema = strawberry.Schema(query=Query, config=strawberry_config())
    result = schema.execute_sync("{ boolAsBigint }")
    assert result.errors is not None
    assert len(result.errors) > 0
    # The strict serializer's error message is the contract source; GraphQL wraps
    # the TypeError in a GraphQLError, so assert on the message substring rather
    # than the exception type.
    assert any("BigInt cannot serialize bool" in str(err) for err in result.errors)


# ---------------------------------------------------------------------------
# ArrayField -> list[T] sentinel-guarded recursion (Slice 3)
#
# Synthetic models live under ``app_label = "test_arrayfield"`` so they do
# not collide with the prior synthetic apps (``test_bigint``,
# ``test_choice_enums``). Sentinel-branch tests monkey-patch
# ``converters._ARRAY_FIELD_CLS = _FakeArrayField`` BEFORE declaring the
# ``DjangoType`` (Decision 7 spec #"calls `monkeypatch.setattr(converters, \"_ARRAY_FIELD_CLS\", _FakeArrayField)` *before* declaring the `DjangoType`"). The
# introspection helpers (``_introspect_field_type`` /
# ``_walk_introspected_type``) defined in the BigInt section above are
# reused verbatim by every owner-introspection test below.
#
# Why this section can never migrate to live HTTP: ``ArrayField`` is a
# PostgreSQL-only field type and the fakeshop runs on SQLite. The
# converter-table row is exercised here against synthetic models and the
# sentinel-monkeypatch pattern; consumer-facing coverage stays package-
# internal until the example project gains a postgres test matrix.
# ---------------------------------------------------------------------------


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
            return ArrayIntOwner(
                arr=[1, 2, 3],
            )

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
            return ArrayNullableInnerOwner(
                arr=[1, None, 2],
            )

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


def test_annotation_override_of_arrayfield_with_nested_array_is_allowed(monkeypatch):
    """Consumer ``arr: list[list[int]]`` annotation bypasses nested-ArrayField rejection."""
    monkeypatch.setattr(converters, "_ARRAY_FIELD_CLS", _FakeArrayField)

    class NestedArrayOverrideOwner(models.Model):
        arr = _FakeArrayField(_FakeArrayField(models.IntegerField()))

        class Meta:
            managed = False
            app_label = "test_arrayfield"

    class NestedArrayOverrideOwnerType(DjangoType):
        arr: list[list[int]]

        class Meta:
            model = NestedArrayOverrideOwner
            fields = ("arr",)

    finalize_django_types()
    assert NestedArrayOverrideOwnerType.__annotations__["arr"] == list[list[int]]


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
            return RealArrayIntOwner(
                arr=[1, 2, 3],
            )

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
# ``test_arrayfield``, ``test_choice_enums``). Sentinel-branch tests
# monkey-patch ``converters._HSTORE_FIELD_CLS = _FakeHStoreField`` BEFORE
# declaring the ``DjangoType`` (Decision 7 spec #"calls `monkeypatch.setattr(converters, \"_HSTORE_FIELD_CLS\", _FakeHStoreField)` *before* declaring the `DjangoType`"). Helper-resolver
# tests use ``sys.modules`` manipulation per Decision 7 spec #"Helper-resolver tests".
#
# Same postgres-only constraint as the ArrayField section: ``HStoreField``
# can never run on the SQLite-backed fakeshop, so the converter-table row
# stays covered here against synthetic models. Migration to live HTTP is
# gated on the example project gaining a postgres test matrix.
# ---------------------------------------------------------------------------


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

    No DB persistence - SQLite cannot store HStore values; the test exercises
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
    ``None`` value preserved inside the dict - mirrors ``HStoreField``'s native
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


# ---------------------------------------------------------------------------
# Slice 4 - multi-type relation conversion regressions (H1 always-defer)
# ---------------------------------------------------------------------------


def test_consumer_authored_relation_annotation_override_survives_always_defer():
    """Consumer-authored annotation override targeting a secondary survives H1.

    With ``Meta.primary = True`` on ``ItemType`` and ``AdminItemType`` as a
    secondary, an annotation-only override on ``CategoryType.items`` that
    points at ``AdminItemType`` must win over the primary-resolution path.
    Pins that the ``consumer_authored_fields`` short-circuit still skips
    relation synthesis for consumer-authored fields even though the
    auto-synthesized path is now always-defer.
    """
    from apps.products.models import Category, Item

    class AdminItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")
            primary = True

    class CategoryType(DjangoType):
        items: list[AdminItemType]

        class Meta:
            model = Category
            fields = ("id", "name", "items")

    definition = CategoryType.__django_strawberry_definition__
    assert definition.consumer_authored_fields == frozenset({"items"})
    assert definition.consumer_annotated_relation_fields == frozenset({"items"})

    finalize_django_types()

    # Consumer annotation wins: list[AdminItemType], not list[ItemType].
    assert CategoryType.__annotations__["items"] == list[AdminItemType]


def test_consumer_assigned_strawberry_field_relation_survives_always_defer():
    """Consumer-assigned ``strawberry.field`` on a multi-type relation survives H1."""
    from apps.products.models import Category, Item

    class AdminItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")
            primary = True

    class CategoryType(DjangoType):
        @strawberry.field
        def items(self) -> list[AdminItemType]:
            return []

        class Meta:
            model = Category
            fields = ("id", "name", "items")

    definition = CategoryType.__django_strawberry_definition__
    assert definition.consumer_authored_fields == frozenset({"items"})
    assert definition.consumer_assigned_relation_fields == frozenset({"items"})

    # ``items`` is NOT in synthesized annotations - the consumer-authored
    # short-circuit skipped it, so no PendingRelationAnnotation was recorded.
    assert "items" not in CategoryType.__annotations__

    finalize_django_types()

    # Post-finalize: the consumer's resolver function is preserved and
    # exposed via Strawberry's field definition.
    items_field = next(
        field
        for field in CategoryType.__strawberry_definition__.fields
        if field.python_name == "items"
    )
    assert items_field.base_resolver is not None
    assert items_field.base_resolver.wrapped_func.__qualname__.endswith("CategoryType.items")


def test_relation_resolves_to_primary_type_when_target_model_has_multiple():
    """Headline H1: a relation to a multi-type model resolves to the primary."""
    from apps.products.models import Category, Item

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")
            primary = True

    class AdminItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name", "items")

    finalize_django_types()

    @strawberry.type
    class Query:
        @strawberry.field
        def categories(self) -> list[CategoryType]:
            return []

    schema = strawberry.Schema(query=Query)
    items_field_type = _introspect_field_type(schema, "CategoryType", "items")
    terminal = _walk_introspected_type(items_field_type)
    # The reverse FK resolves to the primary ItemType, not AdminItemType.
    assert terminal["name"] == "ItemType"


def test_relation_resolves_to_primary_when_secondary_registered_before_source_before_primary():
    """H1 import-order trap closure: declare secondary -> source -> primary in order.

    Without always-defer, ``CategoryType.items`` would freeze against
    ``AdminItemType`` (the only registered type on ``Item`` at the
    moment ``CategoryType`` ran ``__init_subclass__``) and never pick
    up the primary that registered later.
    """
    from apps.products.models import Category, Item

    # 1. Secondary registers first (no primary flag).
    class AdminItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    # 2. Source references the reverse relation while only the secondary is known.
    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name", "items")

    # 3. Primary registers AFTER the source.
    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")
            primary = True

    finalize_django_types()

    # Post-finalize annotation must resolve to the primary, not the secondary.
    assert CategoryType.__annotations__["items"] == list[ItemType]

    # And the schema-built field type also picks the primary.
    @strawberry.type
    class Query:
        @strawberry.field
        def categories(self) -> list[CategoryType]:
            return []

    schema = strawberry.Schema(query=Query)
    items_field_type = _introspect_field_type(schema, "CategoryType", "items")
    terminal = _walk_introspected_type(items_field_type)
    assert terminal["name"] == "ItemType"


def test_relation_resolves_when_target_model_has_one_type_no_primary():
    """Backward-compat: a single registered type with no primary still resolves."""
    from apps.products.models import Category, Item

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name", "items")

    finalize_django_types()
    assert CategoryType.__annotations__["items"] == list[ItemType]


def test_relation_target_with_multiple_no_primary_surfaces_audit_error_at_finalize():
    """Slice 3 audit fires before unresolved-target when target is multi-type-no-primary."""
    from apps.products.models import Category, Item

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    class AdminItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name", "items")

    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()

    msg = str(exc_info.value)
    # The audit message is what fires - not the "no registered DjangoType"
    # message of the unresolved-target path.
    assert "Declare Meta.primary = True" in msg


# ---------------------------------------------------------------------------
# spec-029 Slice 3 - convert_scalar force_nullable tri-state
#
# These are direct ``convert_scalar`` unit tests (the tri-state seam fires at
# conversion time, unreachable from a live query without the override
# machinery). ``None`` must reproduce the column-native ``field.null`` result
# exactly (regression guard); ``True`` always widens; ``False`` always
# narrows. The choice / Array / HStore branches each read the same single
# ``effective_null`` value, so the override applies uniformly. Synthetic
# models reuse the existing ``_unique_app_label`` namespacing + the
# ``_FakeArrayField`` / ``_FakeHStoreField`` doubles and their monkeypatch
# pattern.
# ---------------------------------------------------------------------------


def _text_field(*, null: bool) -> models.Field:
    """Return a bound ``TextField`` on a synthetic model with the given ``null``."""

    class _Owner(models.Model):
        value = models.TextField(null=null)

        class Meta:
            managed = False
            app_label = _unique_app_label("test_force_nullable")

    return _Owner._meta.get_field("value")


def test_convert_scalar_force_nullable_true_widens_non_null_column():
    """``force_nullable=True`` on a non-null ``TextField`` returns ``str | None``."""
    field = _text_field(null=False)
    assert convert_scalar(field, "OwnerType", force_nullable=True) == (str | None)


def test_convert_scalar_force_nullable_false_narrows_nullable_column():
    """``force_nullable=False`` on a nullable ``TextField`` returns bare ``str``."""
    field = _text_field(null=True)
    assert convert_scalar(field, "OwnerType", force_nullable=False) is str


def test_convert_scalar_force_nullable_none_honors_field_null():
    """``force_nullable=None`` (and the implicit default) reproduce ``field.null``.

    Regression guard for Decision 7's "the ``None`` default is identical to
    today's behavior" contract, checked in both column directions and against
    the no-kwarg call so the new keyword-only parameter cannot drift the
    existing default.
    """
    non_null = _text_field(null=False)
    nullable = _text_field(null=True)
    # Explicit None.
    assert convert_scalar(non_null, "OwnerType", force_nullable=None) is str
    assert convert_scalar(nullable, "OwnerType", force_nullable=None) == (str | None)
    # Implicit default (no kwarg) - the pre-override call shape.
    assert convert_scalar(non_null, "OwnerType") is str
    assert convert_scalar(nullable, "OwnerType") == (str | None)


def test_convert_scalar_force_nullable_on_choice_field(choice_fixture_model):
    """The override flips a choice field's generated enum nullability (Decision 9).

    Widening sits AFTER choice substitution, so ``force_nullable=True`` on the
    non-null ``status`` column yields ``EnumType | None`` and ``False`` on the
    nullable ``nullable_status`` column yields a bare ``EnumType`` - the enum
    members are untouched in both directions.
    """
    registry.clear()
    status = choice_fixture_model._meta.get_field("status")
    widened = convert_scalar(status, "FixtureType", force_nullable=True)
    enum_cls = registry.get_enum(choice_fixture_model, "status")
    assert enum_cls is not None
    assert widened == (enum_cls | None)

    nullable_status = choice_fixture_model._meta.get_field("nullable_status")
    narrowed = convert_scalar(nullable_status, "FixtureType", force_nullable=False)
    nullable_enum = registry.get_enum(choice_fixture_model, "nullable_status")
    assert nullable_enum is not None
    assert narrowed is nullable_enum


def test_convert_scalar_force_nullable_on_array_field(monkeypatch):
    """The override flips the OUTER ``list[inner]`` nullability; inner is unchanged.

    A non-null ``ArrayField(IntegerField())`` with ``force_nullable=True``
    becomes ``list[int] | None`` (outer widened) while the inner element stays
    ``int`` (NOT ``int | None``) - the recursive ``base_field`` conversion is
    left ``force_nullable``-unset, so inner nullability follows
    ``base_field.null`` and is NOT affected by the outer override (Edge cases).
    A nullable-outer ``ArrayField(..., null=True)`` with ``force_nullable=False``
    narrows back to bare ``list[int]``.
    """
    monkeypatch.setattr(converters, "_ARRAY_FIELD_CLS", _FakeArrayField)

    class _ArrOwner(models.Model):
        arr = _FakeArrayField(models.IntegerField())
        nullable_arr = _FakeArrayField(models.IntegerField(), null=True)

        class Meta:
            managed = False
            app_label = _unique_app_label("test_force_nullable_array")

    field = _ArrOwner._meta.get_field("arr")
    widened = convert_scalar(field, "OwnerType", force_nullable=True)
    # Outer widened to | None; inner element stays bare int (override is outer-only).
    assert widened == (list[int] | None)
    # The unforced default on the same non-null-outer field is bare list[int].
    assert convert_scalar(field, "OwnerType") == list[int]

    nullable_field = _ArrOwner._meta.get_field("nullable_arr")
    narrowed = convert_scalar(nullable_field, "OwnerType", force_nullable=False)
    assert narrowed == list[int]


def test_convert_scalar_force_nullable_on_hstore_field(monkeypatch):
    """The override flips ``HStoreField`` between ``JSON | None`` and ``JSON``."""
    monkeypatch.setattr(converters, "_HSTORE_FIELD_CLS", _FakeHStoreField)

    class _HStoreOwner(models.Model):
        data = _FakeHStoreField()
        nullable_data = _FakeHStoreField(null=True)

        class Meta:
            managed = False
            app_label = _unique_app_label("test_force_nullable_hstore")

    field = _HStoreOwner._meta.get_field("data")
    widened = convert_scalar(field, "OwnerType", force_nullable=True)
    assert widened == (strawberry.scalars.JSON | None)

    nullable_field = _HStoreOwner._meta.get_field("nullable_data")
    narrowed = convert_scalar(nullable_field, "OwnerType", force_nullable=False)
    assert narrowed is strawberry.scalars.JSON


# ---------------------------------------------------------------------------
# File / image read-output mapping (spec-037 Slice 1, Decision 3 / Decision 4)
# ---------------------------------------------------------------------------


class _SubImageField(models.ImageField):
    """A consumer ``ImageField`` subclass, to pin the MRO precedence walk."""


def test_convert_field_output_filefield_to_djangofiletype():
    """A ``FileField`` resolves to ``DjangoFileType`` via ``FIELD_OUTPUT_TYPE_MAP``.

    The map identity is ``DjangoFileType``; ``convert_field_output`` widens it to
    the default-nullable ``DjangoFileType | None`` (spec-037 Decision 4).
    """

    class _FileOwner(models.Model):
        attachment = models.FileField()

        class Meta:
            managed = False
            app_label = _unique_app_label("test_filefield_output")

    field = _FileOwner._meta.get_field("attachment")
    assert convert_field_output(field, "OwnerType") == (DjangoFileType | None)
    assert _field_output_type_for(field) is DjangoFileType


def test_convert_field_output_imagefield_to_djangoimagetype():
    """An ``ImageField`` resolves to ``DjangoImageType`` via ``FIELD_OUTPUT_TYPE_MAP``.

    Widened to the default-nullable ``DjangoImageType | None`` (spec-037 Decision 4).
    """

    class _ImageOwner(models.Model):
        preview = models.ImageField()

        class Meta:
            managed = False
            app_label = _unique_app_label("test_imagefield_output")

    field = _ImageOwner._meta.get_field("preview")
    assert convert_field_output(field, "OwnerType") == (DjangoImageType | None)


def test_field_output_map_mro_precedence_image_subclass_wins():
    """An ``ImageField`` subclass resolves to ``DjangoImageType``, never ``DjangoFileType``.

    ``ImageField`` is a ``FileField`` subclass, so the MRO walk must hit the
    ``ImageField`` row before the ``FileField`` row (the same precedence as
    ``PositiveBigIntegerField`` -> ``BigInt`` before ``IntegerField``).
    """

    class _SubImageOwner(models.Model):
        preview = _SubImageField()

        class Meta:
            managed = False
            app_label = _unique_app_label("test_subimage_mro")

    field = _SubImageOwner._meta.get_field("preview")
    assert _field_output_type_for(field) is DjangoImageType
    assert convert_field_output(field, "OwnerType") == (DjangoImageType | None)


def test_convert_field_output_file_image_nullable_by_default():
    """File/image output is ``<object> | None`` by DEFAULT, regardless of ``blank`` / ``null``.

    The generated parent resolver returns ``None`` for an empty / falsy
    ``FieldFile`` even on a ``null=False, blank=False`` column (legacy rows,
    direct ``Model.objects.create()``, fixtures store ``""``), so the SDL must be
    nullable to match what the resolver can return (spec-037 Decision 4). A
    stronger non-empty invariant is opt-in via ``required_overrides``
    (``force_nullable=False``), covered in the force_nullable test below.
    """

    class _NullabilityOwner(models.Model):
        required = models.FileField()
        blank_file = models.FileField(blank=True)
        null_file = models.FileField(null=True)

        class Meta:
            managed = False
            app_label = _unique_app_label("test_file_nullability")

    required = _NullabilityOwner._meta.get_field("required")
    blank_file = _NullabilityOwner._meta.get_field("blank_file")
    null_file = _NullabilityOwner._meta.get_field("null_file")

    assert convert_field_output(required, "OwnerType") == (DjangoFileType | None)
    assert convert_field_output(blank_file, "OwnerType") == (DjangoFileType | None)
    assert convert_field_output(null_file, "OwnerType") == (DjangoFileType | None)


def test_convert_field_output_force_nullable_overrides_default():
    """``force_nullable`` wins over the default-nullable file/image shape.

    ``required_overrides`` (``force_nullable=False``) forces the bare
    ``DjangoFileType`` even on a ``blank=True`` column -- the opt-in to a stronger
    non-empty invariant; ``nullable_overrides`` (``force_nullable=True``) keeps
    ``DjangoFileType | None`` (the default) on a plain required column.
    """

    class _OverrideOwner(models.Model):
        required = models.FileField()
        blank_file = models.FileField(blank=True)

        class Meta:
            managed = False
            app_label = _unique_app_label("test_file_force_nullable")

    required = _OverrideOwner._meta.get_field("required")
    blank_file = _OverrideOwner._meta.get_field("blank_file")

    assert convert_field_output(required, "OwnerType", force_nullable=True) == (
        DjangoFileType | None
    )
    assert convert_field_output(blank_file, "OwnerType", force_nullable=False) is DjangoFileType


def test_convert_field_output_delegates_scalar_columns():
    """A non-file column delegates to ``convert_scalar`` unchanged."""

    class _ScalarOwner(models.Model):
        title = models.TextField()
        count = models.IntegerField(null=True)

        class Meta:
            managed = False
            app_label = _unique_app_label("test_scalar_delegation")

    title = _ScalarOwner._meta.get_field("title")
    count = _ScalarOwner._meta.get_field("count")
    assert convert_field_output(title, "OwnerType") is str
    assert convert_field_output(count, "OwnerType") == (int | None)
    # The force_nullable tri-state still threads through to the scalar path.
    assert convert_field_output(title, "OwnerType", force_nullable=True) == (str | None)


def test_file_columns_stay_scalar_on_the_filter_input_path():
    """P0 split: the SHARED scalar/filter-input path still sees ``str`` for a file column.

    ``FIELD_OUTPUT_TYPE_MAP`` is read-output-only; ``scalar_for_field`` (the
    lookup ``filters/inputs._scalar_from_model_field`` delegates to) walks
    ``SCALAR_MAP`` only, so a file column resolves to a scalar ``str`` filter
    input and no ``DjangoFileType`` / ``DjangoImageType`` output object ever
    reaches a GraphQL input. ``SCALAR_MAP``'s file/image rows stay ``str``.
    """
    from django_strawberry_framework.filters.inputs import _scalar_from_model_field

    class _FilterOwner(models.Model):
        attachment = models.FileField()
        preview = models.ImageField()

        class Meta:
            managed = False
            app_label = _unique_app_label("test_file_filter_scalar")

    attachment = _FilterOwner._meta.get_field("attachment")
    preview = _FilterOwner._meta.get_field("preview")

    # The package's filter-input scalar lookup keeps file/image columns scalar.
    assert scalar_for_field(attachment) is str
    assert scalar_for_field(preview) is str
    assert _scalar_from_model_field(attachment) is str
    assert _scalar_from_model_field(preview) is str
    # The shared SCALAR_MAP rows are untouched by the new output map.
    assert SCALAR_MAP[models.FileField] is str
    assert SCALAR_MAP[models.ImageField] is str
    assert FIELD_OUTPUT_TYPE_MAP[models.FileField] is DjangoFileType
    assert FIELD_OUTPUT_TYPE_MAP[models.ImageField] is DjangoImageType
