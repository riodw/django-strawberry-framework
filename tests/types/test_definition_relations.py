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

from collections.abc import Callable
from types import SimpleNamespace
from typing import NoReturn, cast

import pytest
from apps.library.models import Book, Genre, Loan, MembershipCard, Patron, Shelf, TaggedItem
from django.utils.functional import SimpleLazyObject
from strawberry import relay
from typing_extensions import override

from django_strawberry_framework import DjangoType, finalize_django_types
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.registry import registry
from django_strawberry_framework.types.definition import (
    DjangoTypeDefinition,
    _is_framework_relay_id_resolver,
    origin_has_custom_id_resolver,
)

pytestmark = pytest.mark.usefixtures("isolate_global_registry")


def test_related_target_for_resolves_fk_m2m_and_reverse() -> None:
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


def test_related_target_for_resolves_one_to_one_relation() -> None:
    """Forward + reverse OneToOne both resolve via ``related_target_for``.

    Covers the canonical OneToOne pair declared in the fakeshop library
    app (``MembershipCard.patron`` ``OneToOneField`` with
    ``related_name="card"``). Both directions are exercised in the same
    test so the lookup's behavior on single-valued reverse relations is
    pinned alongside the FK / M2M variants above.
    """

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


def test_related_target_for_returns_none_when_target_unregistered() -> None:
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


def _malformed_definition(
    *,
    origin: type = object,
    model: object = Book,
    name: object = None,
) -> DjangoTypeDefinition:
    """Build a directly constructed definition carrying malformed metadata.

    The constructor takes eleven arguments of which only three vary across
    the hostile-metadata tests, so every such test declares its variation
    here rather than re-inlining the full call.
    """
    return DjangoTypeDefinition(
        origin=origin,
        # basedpyright: the malformed model and name callers pass are the hostile input under test;
        # DjangoTypeDefinition types them as type[Model] and str | None
        model=model,  # pyright: ignore[reportArgumentType]
        name=name,  # pyright: ignore[reportArgumentType]
        description=None,
        fields_spec=None,
        exclude_spec=None,
        selected_fields=(),
        field_map={},
        optimizer_hints={},
        has_custom_get_queryset=False,
    )


def test_graphql_type_name_wraps_unreadable_origin_and_rejects_empty_name() -> None:
    """An unreadable origin name and an empty ``name`` are both typed failures."""

    class _HostileMeta(type):
        @override
        def __getattribute__(cls, name: str) -> object:
            if name == "__name__":
                raise RuntimeError("name exploded")
            return super().__getattribute__(name)

    class _HostileOrigin(metaclass=_HostileMeta):
        pass

    with pytest.raises(ConfigurationError, match="Could not inspect"):
        _ = _malformed_definition(origin=_HostileOrigin).graphql_type_name
    with pytest.raises(ConfigurationError, match="empty name"):
        _ = _malformed_definition(name="").graphql_type_name


def test_related_target_lookup_degrades_malformed_model_and_relation_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Every unreadable step of the target walk degrades to ``None``, never an exception."""

    class _UnreadableRelationFlag:
        @property
        def is_relation(self) -> NoReturn:
            raise RuntimeError("relation flag exploded")

    class _UnreadableTarget:
        is_relation = True

        @property
        def related_model(self) -> NoReturn:
            raise RuntimeError("target exploded")

    def _exploding_field(_name: str) -> object:
        raise RuntimeError("field")

    def _unreadable_relation_flag(_name: str) -> object:
        return _UnreadableRelationFlag()

    def _unreadable_target(_name: str) -> object:
        return _UnreadableTarget()

    cases = [
        SimpleNamespace(get_field=_exploding_field),
        SimpleNamespace(get_field=_unreadable_relation_flag),
        SimpleNamespace(get_field=_unreadable_target),
    ]
    for meta in cases:
        definition = _malformed_definition(model=SimpleNamespace(_meta=meta))
        assert definition.related_target_for("relation") is None

    target = object()
    field = SimpleNamespace(is_relation=True, related_model=target)

    def _relation_field(_name: str) -> object:
        return field

    def _exploding_get(_model: object) -> object:
        raise RuntimeError

    def _exploding_get_definition(_type_cls: object) -> object:
        raise RuntimeError

    definition = _malformed_definition(
        model=SimpleNamespace(_meta=SimpleNamespace(get_field=_relation_field)),
    )
    monkeypatch.setattr(registry, "get", _exploding_get)
    assert definition.related_target_for("relation") is None

    target_type = object()

    def _target_type_get(_model: object) -> object:
        return target_type

    monkeypatch.setattr(registry, "get", _target_type_get)
    monkeypatch.setattr(registry, "get_definition", _exploding_get_definition)
    assert definition.related_target_for("relation") is None


def test_custom_id_detection_fails_closed_for_hostile_class_metadata() -> None:
    """Unreadable ``__mro__`` / ``__dict__`` metadata counts as a custom resolver."""

    class _HostileMroMeta(type):
        @override
        def __getattribute__(cls, name: str) -> object:
            if name == "__mro__":
                raise RuntimeError("mro exploded")
            return super().__getattribute__(name)

    class _HostileMro(metaclass=_HostileMroMeta):
        pass

    class _HostileDictMeta(type):
        @override
        def __getattribute__(cls, name: str) -> object:
            if name == "__dict__":
                raise RuntimeError("dict exploded")
            return super().__getattribute__(name)

    class _HostileDict(metaclass=_HostileDictMeta):
        pass

    class _UnreadableMro:
        def __iter__(self) -> NoReturn:
            raise RuntimeError("mro iteration exploded")

    class _UnreadableMroMeta(type):
        @override
        def __getattribute__(cls, name: str) -> object:
            if name == "__mro__":
                return _UnreadableMro()
            return super().__getattribute__(name)

    class _UnreadableMroOrigin(metaclass=_UnreadableMroMeta):
        pass

    class _HostileClassProperty:
        @property
        @override
        # basedpyright: deliberately a read-only ``__class__`` that raises: the hostile object
        # is the guard's input
        def __class__(self) -> NoReturn:  # pyright: ignore[reportIncompatibleMethodOverride]
            raise RuntimeError("class exploded")

    assert origin_has_custom_id_resolver(_HostileMro, "id") is True
    assert origin_has_custom_id_resolver(_HostileDict, "id") is True
    assert origin_has_custom_id_resolver(_UnreadableMroOrigin, "id") is True
    # basedpyright: the object whose __class__ raises is the hostile input under test;
    # origin_has_custom_id_resolver types the parameter as type[object]
    assert origin_has_custom_id_resolver(_HostileClassProperty(), "id") is True  # pyright: ignore[reportArgumentType]


def test_custom_id_detection_fails_closed_for_hostile_relay_resolver() -> None:
    """A ``resolve_id_attr`` that raises or returns a non-string counts as custom."""

    class _RaisingNode(relay.Node):
        @classmethod
        @override
        def resolve_id_attr(cls) -> NoReturn:
            raise RuntimeError("resolver exploded")

    class _NonStringNode(relay.Node):
        @classmethod
        @override
        # basedpyright: deliberately a non-str id attribute, the hook result the resolver check refuses
        def resolve_id_attr(cls) -> int:  # pyright: ignore[reportIncompatibleMethodOverride]
            return 123

    assert origin_has_custom_id_resolver(_RaisingNode, "id") is True
    assert origin_has_custom_id_resolver(_NonStringNode, "id") is True


class _ClassReadRaises:
    """An id attribute whose ``__class__`` read raises, so a bare ``isinstance`` on it raises."""

    def __init__(self, raised: type[BaseException]) -> None:
        self._raised = raised

    @property
    @override
    # basedpyright: deliberately a read-only ``__class__`` that raises: the hostile result is the
    # guard's input
    def __class__(self) -> NoReturn:  # pyright: ignore[reportIncompatibleMethodOverride]
        raise self._raised("class read")


class _ClaimsStr:
    """An id attribute that is not a ``str`` whose ``__class__`` says it is one."""

    @property
    @override
    # basedpyright: deliberately a read-only ``__class__`` that forges a type: the forged result
    # is the guard's input
    def __class__(self) -> type[str]:  # pyright: ignore[reportIncompatibleMethodOverride]
        return str


class _LoudStr(str):
    """A ``str`` whose own ``__str__`` is consumer code that must never run."""

    @override
    def __str__(self) -> str:
        raise RuntimeError("the subclass's own __str__ is never run")


_UNREADABLE_ID_ATTRS = [
    pytest.param(lambda: _ClassReadRaises(RuntimeError), True, id="class-read-raises-runtime"),
    pytest.param(
        lambda: _ClassReadRaises(KeyboardInterrupt),
        True,
        id="class-read-raises-base-exception",
    ),
    pytest.param(_ClaimsStr, True, id="class-claims-str"),
    pytest.param(lambda: SimpleLazyObject(lambda: "id"), True, id="lazy-str"),
    pytest.param(lambda: "id", False, id="pk-name"),
    pytest.param(lambda: "pk", False, id="pk-alias"),
    pytest.param(lambda: _LoudStr("id"), False, id="str-subclass-pk-name"),
    pytest.param(lambda: "slug", True, id="other-column"),
    pytest.param(lambda: "", True, id="empty"),
]


@pytest.mark.parametrize(("make_id_attr", "custom"), _UNREADABLE_ID_ATTRS)
def test_custom_id_detection_normalizes_the_resolve_id_attr_result_under_its_guard(
    make_id_attr: Callable[[], object],
    custom: bool,  # noqa: FBT001 - a parametrized expectation, not a call flag
) -> None:
    """The ``resolve_id_attr`` result is read under the guard that contains the call.

    A result whose class cannot be read, one that only claims ``str`` and a lazy proxy of a
    string all fail closed (the type counts as custom); a plain or ``str``-subclass name
    that is the pk name or ``pk`` does not.
    """
    id_attr = make_id_attr()

    class _Node(relay.Node):
        @classmethod
        @override
        # basedpyright: the hook may answer any object; the id attribute is the guard's input
        def resolve_id_attr(cls) -> str:
            return cast("str", id_attr)

    assert origin_has_custom_id_resolver(_Node, "id") is custom


def test_related_target_for_caches_resolved_pair_after_finalize() -> None:
    """A second post-finalize lookup for the same field hits the memo cache."""

    class ShelfType(DjangoType):
        class Meta:
            model = Shelf
            fields = ("id", "code")

    assert registry.get(Shelf) is ShelfType

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


def test_has_custom_id_resolver_for_caches_mro_result() -> None:
    """Custom id resolver detection is memoized on the definition."""

    class BaseType:
        def resolve_id(self) -> str:
            return "custom"

    class BookType(DjangoType, BaseType):
        class Meta:
            model = Book
            fields = ("id", "title")

    definition = BookType.__django_strawberry_definition__

    assert definition.has_custom_id_resolver_for("id") is True
    assert definition.has_custom_id_resolver_for("uuid") is False
    assert definition._custom_id_resolver_cache == {"id": True, "uuid": False}


def test_has_custom_id_resolver_for_ignores_framework_relay_default() -> None:
    """Framework-installed Relay ``resolve_id`` does not count as consumer custom."""

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title")
            interfaces = (relay.Node,)

    finalize_django_types()
    definition = BookType.__django_strawberry_definition__

    assert definition.has_custom_id_resolver_for("id") is False
    assert definition._custom_id_resolver_cache == {"id": False}


def test_has_custom_id_resolver_for_ignores_inherited_relay_default() -> None:
    """Inherited Strawberry Relay ``resolve_id`` does not count as consumer custom."""

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title")
            interfaces = (relay.Node,)

    finalize_django_types()
    definition = BookType.__django_strawberry_definition__

    assert definition.has_custom_id_resolver_for("id") is False
    assert definition._custom_id_resolver_cache == {"id": False}


def test_has_custom_id_resolver_for_detects_non_id_pk_resolver() -> None:
    """A ``resolve_<pk>`` override for a non-``id`` pk column counts as custom.

    Exercises the ``name != "resolve_id"`` short-circuit: any consumer marker
    other than the framework-exempted ``resolve_id`` is taken at face value.
    """

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title")

        def resolve_uuid(self) -> str:
            return "custom"

    definition = BookType.__django_strawberry_definition__

    assert definition.has_custom_id_resolver_for("uuid") is True
    assert definition._custom_id_resolver_cache == {"uuid": True}


def test_has_custom_id_resolver_for_flags_non_pk_node_id() -> None:
    """A ``relay.NodeID`` on a non-pk column makes pk-only FK-id elision unsafe.

    The GlobalID derives from the annotated column (``code``), which the FK-id
    stub does not populate, so the optimizer must treat it as customized even
    though no ``resolve_id`` override is present.
    """

    class BookType(DjangoType):
        title: relay.NodeID[str]

        class Meta:
            model = Book
            fields = ("id", "title")
            interfaces = (relay.Node,)

    finalize_django_types()
    definition = BookType.__django_strawberry_definition__

    assert definition.has_custom_id_resolver_for("id") is True
    assert definition._custom_id_resolver_cache == {"id": True}


def test_has_custom_id_resolver_for_allows_pk_node_id() -> None:
    """A ``relay.NodeID`` on the pk column itself stays elision-eligible."""

    class BookType(DjangoType):
        id: relay.NodeID[int]

        class Meta:
            model = Book
            fields = ("id", "title")
            interfaces = (relay.Node,)

    finalize_django_types()
    definition = BookType.__django_strawberry_definition__

    assert definition.has_custom_id_resolver_for("id") is False
    assert definition._custom_id_resolver_cache == {"id": False}


def test_related_target_for_resolves_to_primary_when_two_types_share_target_model() -> None:
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

    assert registry.get(Shelf) is ShelfType

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


def test_related_target_for_returns_none_for_generic_foreign_key() -> None:
    """A ``GenericForeignKey`` is a relation with no ``related_model`` -> ``None``."""

    class TaggedItemType(DjangoType):
        class Meta:
            model = TaggedItem
            fields = ("id", "object_id")

    finalize_django_types()
    definition = TaggedItemType.__django_strawberry_definition__
    # ``content_object`` is a GFK: ``is_relation`` is True but
    # ``related_model`` is ``None`` -> the target-model guard returns ``None``.
    assert definition.related_target_for("content_object") is None


def test_related_target_for_rejects_unhashable_field_names() -> None:
    """Malformed lookup names fail closed instead of leaking a dict-key TypeError."""

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title")

    finalize_django_types()
    assert BookType.__django_strawberry_definition__.related_target_for([]) is None


def test_graphql_type_name_rejects_hostile_metadata() -> None:
    """A malformed definition name raises a typed error with safe diagnostics."""

    class HostileName:
        @override
        def __str__(self) -> str:
            raise RuntimeError("str should not escape")

        @override
        def __repr__(self) -> str:
            raise RuntimeError("repr should not escape")

    definition = _malformed_definition(origin=Book, name=HostileName())
    with pytest.raises(
        ConfigurationError,
        match="must be a non-empty string; got <unprintable HostileName>",
    ):
        _ = definition.graphql_type_name


def test_graphql_type_name_rejects_invalid_graphql_names() -> None:
    """Directly constructed definitions preserve the GraphQL name contract."""
    definition = _malformed_definition(origin=Book, name="bad-name")
    with pytest.raises(ConfigurationError, match="valid GraphQL name"):
        _ = definition.graphql_type_name


def test_custom_id_resolver_guards_reject_malformed_pk_names() -> None:
    """Unhashable primary-key names cannot escape the FK-id safety checks."""
    definition = _malformed_definition(origin=Book)
    # basedpyright: the unhashable pk name is the hostile input under test;
    # has_custom_id_resolver_for types the parameter as str
    assert definition.has_custom_id_resolver_for([]) is False  # pyright: ignore[reportArgumentType]
    # basedpyright: the unhashable pk name is the hostile input under test;
    # origin_has_custom_id_resolver types the parameter as str
    assert origin_has_custom_id_resolver(Book, []) is False  # pyright: ignore[reportArgumentType]


def test_framework_id_resolver_guard_survives_hostile_descriptor() -> None:
    """A broken ``__func__`` descriptor is treated as consumer-owned."""

    class HostileResolver:
        @property
        def __func__(self) -> NoReturn:
            raise RuntimeError("descriptor should not escape")

    assert _is_framework_relay_id_resolver(HostileResolver()) is False


def test_definition_equality_ignores_memoization_caches() -> None:
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


def test_custom_id_resolver_guards_reject_empty_pk_names() -> None:
    """Empty primary-key names fail closed without polluting cache."""
    definition = _malformed_definition(origin=Book)
    assert definition.has_custom_id_resolver_for("") is False
    assert origin_has_custom_id_resolver(Book, "") is False
    assert "" not in definition._custom_id_resolver_cache
