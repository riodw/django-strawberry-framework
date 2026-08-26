"""DjangoTypeDefinition tests for related-target lookup, GraphQL naming, and Relay ID detection.

Three surfaces, all reached through a directly constructed or
registry-resolved ``DjangoTypeDefinition``:

- ``related_target_for``: the lookup powering the spec-027 Decision 4 owner-aware
  FK/PK conditional in ``FilterSet.filter_for_field`` /
  ``filter_for_lookup``. Covers forward FK, forward M2M, reverse FK (via
  ``Book.loans`` -> ``Loan.book`` with ``related_name="loans"``),
  OneToOne in both directions, scalar non-relation field, missing field,
  ``GenericForeignKey``, unregistered target, primary-wins target
  resolution, the post-finalize memo cache, and malformed model /
  relation metadata degrading to ``None``.
- ``graphql_type_name``: the shared name-derivation rule, including the
  unreadable-origin and invalid-name rejections.
- custom Relay ID-resolver detection (``has_custom_id_resolver_for`` /
  ``origin_has_custom_id_resolver`` / ``_is_framework_relay_id_resolver``):
  memoization, the framework-default exemptions, ``relay.NodeID``
  placement, and fail-closed handling of hostile class metadata.

``Meta.name`` validation at type creation lives with its siblings in
``tests/types/test_base.py``.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
import strawberry
from apps.library.models import Book, Genre, Loan, Shelf
from strawberry import relay

from django_strawberry_framework import DjangoType, finalize_django_types
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.registry import registry
from django_strawberry_framework.types.definition import (
    DjangoTypeDefinition,
    _is_framework_relay_id_resolver,
    origin_has_custom_id_resolver,
)
from django_strawberry_framework.types.relay import _resolve_id_default


@pytest.fixture(autouse=True)
def _isolate_registry(isolate_global_registry):
    """Every test here declares fresh ``DjangoType`` classes - opt the module
    into the shared registry/connection-cache isolation (``tests/conftest.py``)."""


def test_related_target_for_resolves_fk_m2m_and_reverse():
    """Forward FK, forward M2M, reverse FK, scalar, and missing-field cases."""

    class ShelfType(DjangoType):
        class Meta:
            model = Shelf
            fields = ("id", "code")

    class GenreType(DjangoType):
        class Meta:
            model = Genre
            fields = ("id", "name")

    class LoanType(DjangoType):
        class Meta:
            model = Loan
            fields = ("id", "note")

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = (
                "id",
                "title",
                "shelf",
                "genres",
                "loans",
            )

    finalize_django_types()

    book_definition = BookType.__django_strawberry_definition__

    # Forward FK -> (ShelfDefinition, ForeignKey).
    shelf_pair = book_definition.related_target_for("shelf")
    assert shelf_pair is not None
    shelf_definition, shelf_field = shelf_pair
    assert shelf_definition is ShelfType.__django_strawberry_definition__
    assert shelf_field.name == "shelf"
    assert getattr(shelf_field, "many_to_one", False) is True

    # Forward M2M -> (GenreDefinition, ManyToManyField).
    genres_pair = book_definition.related_target_for("genres")
    assert genres_pair is not None
    genres_definition, genres_field = genres_pair
    assert genres_definition is GenreType.__django_strawberry_definition__
    assert genres_field.name == "genres"
    assert getattr(genres_field, "many_to_many", False) is True

    # Reverse FK via ``Loan.book = ForeignKey(Book, related_name="loans")``.
    loans_pair = book_definition.related_target_for("loans")
    assert loans_pair is not None
    loans_definition, loans_field = loans_pair
    assert loans_definition is LoanType.__django_strawberry_definition__
    # The reverse accessor's underlying meta-field is the ``ManyToOneRel``
    # / ``ForeignObject``-shaped reverse field; its ``related_model`` is
    # ``Loan`` (the source of the FK).
    assert loans_field.related_model is Loan

    # Scalar text field -> None (not a relation).
    assert book_definition.related_target_for("title") is None

    # Missing field -> None (FieldDoesNotExist caught).
    assert book_definition.related_target_for("nonexistent_field") is None


def test_related_target_for_resolves_one_to_one_relation():
    """Forward + reverse OneToOne both resolve via ``related_target_for``.

    Covers the canonical OneToOne pair declared in the fakeshop library
    app (``MembershipCard.patron`` ``OneToOneField`` with
    ``related_name="card"``). Both directions are exercised in the same
    test so the lookup's behavior on single-valued reverse relations is
    pinned alongside the FK / M2M variants above.
    """
    from apps.library.models import MembershipCard, Patron

    class PatronType(DjangoType):
        class Meta:
            model = Patron
            fields = ("id", "name")

    class MembershipCardType(DjangoType):
        class Meta:
            model = MembershipCard
            fields = ("id", "barcode", "patron")

    finalize_django_types()

    card_definition = MembershipCardType.__django_strawberry_definition__
    patron_definition = PatronType.__django_strawberry_definition__

    forward = card_definition.related_target_for("patron")
    assert forward is not None
    forward_definition, forward_field = forward
    assert forward_definition is patron_definition
    assert forward_field.related_model is Patron

    reverse = patron_definition.related_target_for("card")
    assert reverse is not None
    reverse_definition, reverse_field = reverse
    assert reverse_definition is card_definition
    assert reverse_field.related_model is MembershipCard


def test_related_target_for_returns_none_when_target_unregistered():
    """A relation whose target ``DjangoType`` was never registered resolves to ``None``."""

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title")

    definition = BookType.__django_strawberry_definition__
    # No ShelfType registered; ``related_target_for("shelf")`` cannot
    # resolve a target definition and returns ``None`` (the defensive
    # registry-miss branch).
    assert definition.related_target_for("shelf") is None


def _malformed_definition(*, origin=object, model=Book, name=None):
    """Build a directly constructed definition carrying malformed metadata.

    The constructor takes eleven arguments of which only three vary across
    the hostile-metadata tests, so every such test declares its variation
    here rather than re-inlining the full call.
    """
    return DjangoTypeDefinition(
        origin=origin,
        model=model,
        name=name,
        description=None,
        fields_spec=None,
        exclude_spec=None,
        selected_fields=(),
        field_map={},
        optimizer_hints={},
        has_custom_get_queryset=False,
    )


def test_graphql_type_name_wraps_unreadable_origin_and_rejects_empty_name():
    """An unreadable origin name and an empty ``name`` are both typed failures."""

    class _HostileMeta(type):
        def __getattribute__(cls, name):
            if name == "__name__":
                raise RuntimeError("name exploded")
            return super().__getattribute__(name)

    class _HostileOrigin(metaclass=_HostileMeta):
        pass

    with pytest.raises(ConfigurationError, match="Could not inspect"):
        _ = _malformed_definition(origin=_HostileOrigin).graphql_type_name
    with pytest.raises(ConfigurationError, match="empty name"):
        _ = _malformed_definition(name="").graphql_type_name


def test_related_target_lookup_degrades_malformed_model_and_relation_metadata(monkeypatch):
    """Every unreadable step of the target walk degrades to ``None``, never an exception."""

    class _UnreadableRelationFlag:
        @property
        def is_relation(self):
            raise RuntimeError("relation flag exploded")

    class _UnreadableTarget:
        is_relation = True

        @property
        def related_model(self):
            raise RuntimeError("target exploded")

    cases = [
        SimpleNamespace(get_field=lambda name: (_ for _ in ()).throw(RuntimeError("field"))),
        SimpleNamespace(get_field=lambda name: _UnreadableRelationFlag()),
        SimpleNamespace(get_field=lambda name: _UnreadableTarget()),
    ]
    for meta in cases:
        definition = _malformed_definition(model=SimpleNamespace(_meta=meta))
        assert definition.related_target_for("relation") is None

    target = object()
    field = SimpleNamespace(is_relation=True, related_model=target)
    definition = _malformed_definition(
        model=SimpleNamespace(_meta=SimpleNamespace(get_field=lambda name: field)),
    )
    monkeypatch.setattr(registry, "get", lambda model: (_ for _ in ()).throw(RuntimeError()))
    assert definition.related_target_for("relation") is None

    target_type = object()
    monkeypatch.setattr(registry, "get", lambda model: target_type)
    monkeypatch.setattr(
        registry,
        "get_definition",
        lambda type_cls: (_ for _ in ()).throw(RuntimeError()),
    )
    assert definition.related_target_for("relation") is None


def test_custom_id_detection_fails_closed_for_hostile_class_metadata():
    """Unreadable ``__mro__`` / ``__dict__`` metadata counts as a custom resolver."""

    class _HostileMroMeta(type):
        def __getattribute__(cls, name):
            if name == "__mro__":
                raise RuntimeError("mro exploded")
            return super().__getattribute__(name)

    class _HostileMro(metaclass=_HostileMroMeta):
        pass

    class _HostileDictMeta(type):
        def __getattribute__(cls, name):
            if name == "__dict__":
                raise RuntimeError("dict exploded")
            return super().__getattribute__(name)

    class _HostileDict(metaclass=_HostileDictMeta):
        pass

    class _UnreadableMro:
        def __iter__(self):
            raise RuntimeError("mro iteration exploded")

    class _UnreadableMroMeta(type):
        def __getattribute__(cls, name):
            if name == "__mro__":
                return _UnreadableMro()
            return super().__getattribute__(name)

    class _UnreadableMroOrigin(metaclass=_UnreadableMroMeta):
        pass

    class _HostileClassProperty:
        @property
        def __class__(self):
            raise RuntimeError("class exploded")

    assert origin_has_custom_id_resolver(_HostileMro, "id") is True
    assert origin_has_custom_id_resolver(_HostileDict, "id") is True
    assert origin_has_custom_id_resolver(_UnreadableMroOrigin, "id") is True
    assert origin_has_custom_id_resolver(_HostileClassProperty(), "id") is True


def test_custom_id_detection_fails_closed_for_hostile_relay_resolver():
    """A ``resolve_id_attr`` that raises or returns a non-string counts as custom."""

    class _RaisingNode(relay.Node):
        @classmethod
        def resolve_id_attr(cls):
            raise RuntimeError("resolver exploded")

    class _NonStringNode(relay.Node):
        @classmethod
        def resolve_id_attr(cls):
            return 123

    assert origin_has_custom_id_resolver(_RaisingNode, "id") is True
    assert origin_has_custom_id_resolver(_NonStringNode, "id") is True


def test_related_target_for_caches_resolved_pair_after_finalize():
    """A second post-finalize lookup for the same field hits the memo cache."""

    class ShelfType(DjangoType):
        class Meta:
            model = Shelf
            fields = ("id", "code")

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title", "shelf")

    finalize_django_types()
    book_definition = BookType.__django_strawberry_definition__

    first = book_definition.related_target_for("shelf")
    # Second call returns the SAME memoized pair via the post-finalize cache.
    second = book_definition.related_target_for("shelf")
    assert first is second
    assert first is not None


def test_has_custom_id_resolver_for_caches_mro_result():
    """Custom id resolver detection is memoized on the definition."""

    class BaseType:
        def resolve_id(self):
            return "custom"

    class BookType(BaseType):
        pass

    definition = DjangoTypeDefinition(
        origin=BookType,
        model=Book,
        name=None,
        description=None,
        fields_spec=None,
        exclude_spec=None,
        selected_fields=(),
        field_map={},
        optimizer_hints={},
        has_custom_get_queryset=False,
    )

    assert definition.has_custom_id_resolver_for("id") is True
    assert definition.has_custom_id_resolver_for("uuid") is False
    assert definition._custom_id_resolver_cache == {"id": True, "uuid": False}


def test_has_custom_id_resolver_for_ignores_framework_relay_default():
    """Framework-installed Relay ``resolve_id`` does not count as consumer custom."""

    class BookType:
        resolve_id = classmethod(_resolve_id_default)

    definition = DjangoTypeDefinition(
        origin=BookType,
        model=Book,
        name=None,
        description=None,
        fields_spec=None,
        exclude_spec=None,
        selected_fields=(),
        field_map={},
        optimizer_hints={},
        has_custom_get_queryset=False,
    )

    assert definition.has_custom_id_resolver_for("id") is False
    assert definition._custom_id_resolver_cache == {"id": False}


def test_has_custom_id_resolver_for_ignores_inherited_relay_default():
    """Inherited Strawberry Relay ``resolve_id`` does not count as consumer custom."""

    class BookType(relay.Node):
        pass

    definition = DjangoTypeDefinition(
        origin=BookType,
        model=Book,
        name=None,
        description=None,
        fields_spec=None,
        exclude_spec=None,
        selected_fields=(),
        field_map={},
        optimizer_hints={},
        has_custom_get_queryset=False,
    )

    assert definition.has_custom_id_resolver_for("id") is False
    assert definition._custom_id_resolver_cache == {"id": False}


def test_has_custom_id_resolver_for_detects_non_id_pk_resolver():
    """A ``resolve_<pk>`` override for a non-``id`` pk column counts as custom.

    Exercises the ``name != "resolve_id"`` short-circuit: any consumer marker
    other than the framework-exempted ``resolve_id`` is taken at face value.
    """

    class BookType:
        def resolve_uuid(self):
            return "custom"

    definition = DjangoTypeDefinition(
        origin=BookType,
        model=Book,
        name=None,
        description=None,
        fields_spec=None,
        exclude_spec=None,
        selected_fields=(),
        field_map={},
        optimizer_hints={},
        has_custom_get_queryset=False,
    )

    assert definition.has_custom_id_resolver_for("uuid") is True
    assert definition._custom_id_resolver_cache == {"uuid": True}


def test_has_custom_id_resolver_for_flags_non_pk_node_id():
    """A ``relay.NodeID`` on a non-pk column makes pk-only FK-id elision unsafe.

    The GlobalID derives from the annotated column (``code``), which the FK-id
    stub does not populate, so the optimizer must treat it as customized even
    though no ``resolve_id`` override is present.
    """

    @strawberry.type
    class BookType(relay.Node):
        code: relay.NodeID[str]
        title: str

    definition = DjangoTypeDefinition(
        origin=BookType,
        model=Book,
        name=None,
        description=None,
        fields_spec=None,
        exclude_spec=None,
        selected_fields=(),
        field_map={},
        optimizer_hints={},
        has_custom_get_queryset=False,
    )

    assert definition.has_custom_id_resolver_for("id") is True
    assert definition._custom_id_resolver_cache == {"id": True}


def test_has_custom_id_resolver_for_allows_pk_node_id():
    """A ``relay.NodeID`` on the pk column itself stays elision-eligible."""

    @strawberry.type
    class BookType(relay.Node):
        id: relay.NodeID[int]
        title: str

    definition = DjangoTypeDefinition(
        origin=BookType,
        model=Book,
        name=None,
        description=None,
        fields_spec=None,
        exclude_spec=None,
        selected_fields=(),
        field_map={},
        optimizer_hints={},
        has_custom_get_queryset=False,
    )

    assert definition.has_custom_id_resolver_for("id") is False
    assert definition._custom_id_resolver_cache == {"id": False}


def test_related_target_for_resolves_to_primary_when_two_types_share_target_model():
    """Two ``DjangoType``s registered for the same target model: the primary wins.

    Pins the consolidation contract relied upon at
    ``django_strawberry_framework/types/definition.py``
    ``DjangoTypeDefinition.related_target_for`` - the call site is
    ``target_type = registry.get(target_model)``, NOT the historical
    ``registry.primary_for(target_model) or registry.get(target_model)``
    chain. The collapse is safe only because ``registry.get`` itself
    honors ``_primaries`` as its first return state; this test pins
    that end-to-end so a future change that breaks the primary-first
    rule in ``registry.get`` surfaces here before the spec-027 Decision 4
    owner-aware FK/PK lookup silently swings to the wrong target.
    """

    class ShelfType(DjangoType):
        class Meta:
            model = Shelf
            fields = ("id", "code")

    class AdminShelfType(DjangoType):
        class Meta:
            model = Shelf
            fields = ("id", "code")
            primary = True

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title", "shelf")

    finalize_django_types()

    book_definition = BookType.__django_strawberry_definition__
    pair = book_definition.related_target_for("shelf")
    assert pair is not None
    shelf_definition, _shelf_field = pair
    # The primary (``AdminShelfType``) wins over the non-primary sibling
    # (``ShelfType``) - ``registry.get(Shelf)`` returns ``AdminShelfType``
    # because ``_primaries[Shelf] is AdminShelfType``.
    assert shelf_definition is AdminShelfType.__django_strawberry_definition__


def test_related_target_for_returns_none_for_generic_foreign_key():
    """A ``GenericForeignKey`` is a relation with no ``related_model`` -> ``None``."""
    from apps.library.models import TaggedItem

    class TaggedItemType(DjangoType):
        class Meta:
            model = TaggedItem
            fields = ("id", "object_id")

    finalize_django_types()
    definition = TaggedItemType.__django_strawberry_definition__
    # ``content_object`` is a GFK: ``is_relation`` is True but
    # ``related_model`` is ``None`` -> the target-model guard returns ``None``.
    assert definition.related_target_for("content_object") is None


def test_related_target_for_rejects_unhashable_field_names():
    """Malformed lookup names fail closed instead of leaking a dict-key TypeError."""

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title")

    finalize_django_types()
    assert BookType.__django_strawberry_definition__.related_target_for([]) is None


def test_graphql_type_name_rejects_hostile_metadata():
    """A malformed definition name raises a typed error with safe diagnostics."""

    class HostileName:
        def __str__(self):
            raise RuntimeError("str should not escape")

        def __repr__(self):
            raise RuntimeError("repr should not escape")

    definition = _malformed_definition(origin=Book, name=HostileName())
    with pytest.raises(
        ConfigurationError,
        match="must be a non-empty string; got <unprintable HostileName>",
    ):
        _ = definition.graphql_type_name


def test_graphql_type_name_rejects_invalid_graphql_names():
    """Directly constructed definitions preserve the GraphQL name contract."""
    definition = _malformed_definition(origin=Book, name="bad-name")
    with pytest.raises(ConfigurationError, match="valid GraphQL name"):
        _ = definition.graphql_type_name


def test_custom_id_resolver_guards_reject_malformed_pk_names():
    """Unhashable primary-key names cannot escape the FK-id safety checks."""
    definition = _malformed_definition(origin=Book)
    assert definition.has_custom_id_resolver_for([]) is False
    assert origin_has_custom_id_resolver(Book, []) is False


def test_framework_id_resolver_guard_survives_hostile_descriptor():
    """A broken ``__func__`` descriptor is treated as consumer-owned."""

    class HostileResolver:
        @property
        def __func__(self):
            raise RuntimeError("descriptor should not escape")

    assert _is_framework_relay_id_resolver(HostileResolver()) is False


def test_definition_equality_ignores_memoization_caches():
    """Internal memoization caches do not participate in dataclass equality."""

    class DummyType:
        pass

    d1 = _malformed_definition(origin=DummyType)
    d2 = _malformed_definition(origin=DummyType)

    assert d1 == d2

    # Populate cache on d1
    assert d1.has_custom_id_resolver_for("id") is False
    assert d1._custom_id_resolver_cache == {"id": False}
    assert d2._custom_id_resolver_cache == {}

    # Dataclass equality ignores private cache fields
    assert d1 == d2

    # Cyclic caches also do not break equality
    fake_field = Book._meta.get_field("shelf")
    d1._related_target_cache["shelf"] = (d2, fake_field)
    d2._related_target_cache["shelf"] = (d1, fake_field)
    assert d1 == d2


def test_custom_id_resolver_guards_reject_empty_pk_names():
    """Empty primary-key names fail closed without polluting cache."""
    definition = _malformed_definition(origin=Book)
    assert definition.has_custom_id_resolver_for("") is False
    assert origin_has_custom_id_resolver(Book, "") is False
    assert "" not in definition._custom_id_resolver_cache
