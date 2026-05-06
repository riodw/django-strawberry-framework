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
from django.db import models

from django_strawberry_framework import DjangoType
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.registry import registry
from django_strawberry_framework.types.converters import (
    _sanitize_member_name,
    convert_choices_to_enum,
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
