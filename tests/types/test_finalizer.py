"""Finalizer malformed-state and hostile-metadata boundaries."""

from __future__ import annotations

from collections.abc import Mapping

import pytest
from apps.library.models import Book, Genre
from strawberry import relay

from django_strawberry_framework import DjangoType, finalize_django_types
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.registry import registry
from django_strawberry_framework.types import finalizer as finalizer_module
from django_strawberry_framework.types.finalizer import (
    _annotation_names,
    _audit_model_label_routing,
    _safe_class_name,
    _safe_field_label,
    _safe_qualified_class_name,
    _safe_str,
    _warn_model_label_secondary_collapse,
)
from django_strawberry_framework.types.relations import PendingRelation


@pytest.fixture(autouse=True)
def _isolate_registry(isolate_global_registry):
    """Every test here declares fresh ``DjangoType`` classes - opt the module
    into the shared registry/connection-cache isolation (``tests/conftest.py``)."""


class _HostileNameMeta(type):
    @property
    def __name__(cls):
        raise RuntimeError("hostile model name")


class _HostileName(metaclass=_HostileNameMeta):
    pass


class _HostileString(str):
    def __str__(self):
        raise RuntimeError("hostile field name")


class _HostileAnnotations(Mapping):
    def __init__(self, values):
        self._values = dict(values)

    def __iter__(self):
        return iter(self._values)

    def __len__(self):
        return len(self._values)

    def __getitem__(self, key):
        raise RuntimeError("hostile annotation lookup")


def test_unresolved_relation_diagnostic_survives_hostile_model_name():
    """Malformed pending metadata remains a typed finalization failure."""
    registry.add_pending_relation(
        PendingRelation(
            source_type=_HostileName,
            source_model=_HostileName,
            field_name="books",
            django_field=object(),
            related_model=_HostileName,
            relation_kind="many",
            nullable=False,
        ),
    )

    with pytest.raises(ConfigurationError, match="unresolved"):
        finalize_django_types()


def test_malformed_annotation_key_is_rejected_before_graphql_conversion():
    """A mutated annotation surface cannot leak a Strawberry AttributeError."""

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title")

    BookType.__annotations__[123] = str

    with pytest.raises(ConfigurationError, match="annotation keys must be field-name strings"):
        finalize_django_types()


def test_hostile_annotation_key_string_is_rejected_before_graphql_conversion():
    """A string subclass cannot escape while the finalizer normalizes names."""

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title")

    BookType.__annotations__[_HostileString("bad_name")] = str

    with pytest.raises(ConfigurationError, match="could not be rendered"):
        finalize_django_types()


def test_hostile_annotation_mapping_cannot_escape_relation_rewrite():
    """A mapping that rejects relation assignment remains a typed failure."""

    class GenreType(DjangoType):
        class Meta:
            model = Genre
            fields = ("id", "name")
            interfaces = (relay.Node,)

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title", "genres")
            interfaces = (relay.Node,)
            relation_shapes = {"genres": "connection"}

    BookType.__annotations__ = _HostileAnnotations(BookType.__annotations__)

    with pytest.raises(
        ConfigurationError,
        match="relation annotation genres could not be rewritten",
    ):
        finalize_django_types()


def test_malformed_pending_field_name_is_rejected_before_relation_lookup():
    """A malformed pending record cannot leak ``snake_case`` AttributeError."""

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title", "genres")

    class GenreType(DjangoType):
        class Meta:
            model = Genre
            fields = ("id", "name")

    field = Book._meta.get_field("genres")
    registry.add_pending_relation(
        PendingRelation(
            source_type=BookType,
            source_model=Book,
            field_name=123,
            django_field=field,
            related_model=Genre,
            relation_kind="many",
            nullable=False,
        ),
    )

    with pytest.raises(ConfigurationError, match="invalid field metadata"):
        finalize_django_types()


def test_primary_ambiguity_diagnostic_survives_hostile_model_name():
    """The ambiguity audit keeps malformed registry metadata typed."""
    registry.register(_HostileName, type("FirstType", (), {}))
    registry.register(_HostileName, type("SecondType", (), {}))

    with pytest.raises(ConfigurationError, match="multiple registered"):
        finalize_django_types()


def test_finalizer_diagnostic_renderers_survive_hostile_metadata():
    """Every diagnostic renderer falls back to its documented placeholder label.

    Each assertion pins the exact fallback string, so a regression that swaps
    one placeholder for another (or renders hostile metadata verbatim) fails
    instead of passing on mere non-emptiness.
    """

    class _HostileText(str):
        def __str__(self):
            raise RuntimeError("text exploded")

    class _HostileMeta(type):
        def __getattribute__(cls, name):
            if name in {"__name__", "__qualname__", "__module__"}:
                return _HostileText("Hostile")
            return super().__getattribute__(name)

    class _Hostile(metaclass=_HostileMeta):
        pass

    # A hostile ``str`` subclass is NORMALIZED, not discarded: the renderers reach
    # the underlying characters through the base ``str`` slot, so the useful label
    # survives and only the subclass's ``__str__`` is denied a chance to run.
    assert _safe_class_name(_Hostile) == "Hostile"
    assert _safe_qualified_class_name(_Hostile) == "Hostile.Hostile"
    # ``_safe_field_label`` instead calls ``str(value)``, which DOES run the
    # hostile override, so it degrades to the value's type name.
    assert _safe_field_label(_HostileText("field")) == "_HostileText"
    # ``_HostileString.__repr__`` is inherited from ``str`` and stays usable.
    assert _safe_str(_HostileString("value")) == "'value'"

    class _NonStringNameMeta(type):
        def __getattribute__(cls, name):
            if name == "__name__":
                return 123
            return super().__getattribute__(name)

    class _NonStringName(metaclass=_NonStringNameMeta):
        pass

    class _UnreadableModuleMeta(type):
        def __getattribute__(cls, name):
            if name == "__module__":
                raise RuntimeError("module exploded")
            return super().__getattribute__(name)

    class _UnreadableModule(metaclass=_UnreadableModuleMeta):
        pass

    class _NonStringModuleMeta(type):
        def __getattribute__(cls, name):
            if name == "__module__":
                return 123
            return super().__getattribute__(name)

    class _NonStringModule(metaclass=_NonStringModuleMeta):
        pass

    # Non-string / unreadable metadata is rendered through ``repr`` instead.
    assert _safe_class_name(_NonStringName) == "123"
    assert _safe_qualified_class_name(_UnreadableModule) == (
        f"None.{_UnreadableModule.__qualname__}"
    )
    assert _safe_qualified_class_name(_NonStringModule) == f"123.{_NonStringModule.__qualname__}"


def test_annotation_name_snapshot_wraps_unreadable_mapping():
    """An annotation mapping that refuses enumeration is a typed failure."""

    class _UnreadableAnnotations(Mapping):
        def __iter__(self):
            raise RuntimeError("annotation enumeration exploded")

        def __len__(self):
            return 1

        def __getitem__(self, key):
            raise KeyError(key)

    class _Type:
        __annotations__ = _UnreadableAnnotations()

    with pytest.raises(ConfigurationError, match="annotations could not be read"):
        _annotation_names(_Type)


def test_pending_relation_without_source_definition_is_typed():
    """A pending relation whose source type never registered a definition raises."""
    target_type = type("GenreType", (), {})
    registry.register(Genre, target_type)
    registry.add_pending_relation(
        PendingRelation(
            source_type=type("MissingDefinition", (), {}),
            source_model=Book,
            field_name="genres",
            django_field=Book._meta.get_field("genres"),
            related_model=Genre,
            relation_kind="many",
            nullable=False,
        ),
    )

    with pytest.raises(
        ConfigurationError,
        match="pending relation genres has no DjangoTypeDefinition",
    ):
        finalize_django_types()


def test_model_label_routing_audit_rejects_a_missing_primary_definition(monkeypatch):
    """The routing audit rejects a primary type carrying no registered definition."""
    primary = type("Primary", (), {})
    emitter = type("Emitter", (), {})
    monkeypatch.setattr(finalizer_module, "_first_model_label_emitter", lambda model: emitter)
    monkeypatch.setattr(registry, "primary_for", lambda model: primary)
    monkeypatch.setattr(registry, "get_definition", lambda type_cls: None)

    with pytest.raises(ConfigurationError, match="has no registered DjangoTypeDefinition"):
        _audit_model_label_routing((Book,))


def test_secondary_collapse_warning_survives_unreadable_model_metadata(monkeypatch, caplog):
    """Unreadable model ``_meta`` still yields the identity-collapse warning."""

    class _UnreadableMeta:
        @property
        def app_label(self):
            raise RuntimeError("app label exploded")

    class _Model:
        _meta = _UnreadableMeta()

    primary = type("Primary", (), {})
    secondary = type("Secondary", (), {})
    definition = type("Definition", (), {"effective_globalid_strategy": "model"})()
    monkeypatch.setattr(registry, "primary_for", lambda model: primary)
    monkeypatch.setattr(registry, "types_for", lambda model: (primary, secondary))
    monkeypatch.setattr(registry, "get_definition", lambda type_cls: definition)

    _warn_model_label_secondary_collapse((_Model,))

    assert "identity collapse" in caplog.text


def test_incomplete_registry_registration_is_typed_at_finalize():
    """A bare registry registration cannot leak an AttributeError from the model-label audit."""

    class BareModel:
        pass

    registry.register(BareModel, type("PrimaryType", (), {}), primary=True)
    registry.register(BareModel, type("SecondaryType", (), {}))

    with pytest.raises(
        ConfigurationError,
        match="registered DjangoType PrimaryType has no DjangoTypeDefinition",
    ):
        finalize_django_types()


def test_owner_model_mismatch_formatters_ride_shared_template():
    """FilterSet and OrderSet first-bind model-mismatch messages share one template."""
    from django_strawberry_framework.types.finalizer import (
        _format_owner_model_mismatch_error,
        _format_owner_orderset_model_mismatch_error,
    )

    for fn in (_format_owner_model_mismatch_error, _format_owner_orderset_model_mismatch_error):
        assert "_format_owner_set_model_mismatch_error" in fn.__code__.co_names


def test_field_surface_names_ignores_field_without_python_or_graphql_name():
    """An inherited strawberry field with no python or graphql name is skipped."""
    from django_strawberry_framework.types.finalizer import _field_surface_names

    class _FakeField:
        python_name = None
        graphql_name = None

    class _FakeDefinition:
        fields = [_FakeField()]

    class _BaseWithFakeDef:
        __strawberry_definition__ = _FakeDefinition()

    class _ChildType(_BaseWithFakeDef):
        pass

    surface = _field_surface_names(_ChildType)
    assert surface == {}


def test_filterset_multi_owner_model_mismatch_raises_on_secondary_owner():
    """A secondary owner with an incompatible model is rejected during FilterSet binding."""
    from django_strawberry_framework.filters import FilterSet

    class GenreFilterSet(FilterSet):
        class Meta:
            model = Genre
            fields = {"name": ["exact"]}

    class GenreType(DjangoType):
        class Meta:
            model = Genre
            fields = ("id", "name")
            filterset_class = GenreFilterSet

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title")
            filterset_class = GenreFilterSet

    with pytest.raises(
        ConfigurationError,
        match=r"A filterset's Meta\.model must be its owner's model",
    ):
        finalize_django_types()


def test_orderset_non_class_meta_model_is_typed_at_finalize():
    """A non-class OrderSet ``Meta.model`` is a typed finalize failure, not a ``TypeError``.

    The order side reads the RAW ``Meta.model`` (no metaclass validation, unlike
    the filter side's django-filter-validated ``_meta.model``), so the Django
    lazy-ref string idiom reaches the owner-binding model-compat guard. The
    guard must raise the family model-mismatch ``ConfigurationError`` naming
    the declared value instead of leaking ``issubclass()``'s raw ``TypeError``.
    """
    from django_strawberry_framework.orders import OrderSet

    class GenreOrderSet(OrderSet):
        class Meta:
            model = "library.Genre"
            fields = ("name",)

    class GenreType(DjangoType):
        class Meta:
            model = Genre
            fields = ("id", "name")
            orderset_class = GenreOrderSet

    with pytest.raises(
        ConfigurationError,
        match=r"An orderset's Meta\.model must be its owner's model",
    ) as excinfo:
        finalize_django_types()
    # The shared template names the declared VALUE through the guarded repr.
    assert "'library.Genre'" in str(excinfo.value)


def test_orderset_multi_owner_model_mismatch_raises_on_secondary_owner():
    """A secondary owner with an incompatible model is rejected during OrderSet binding."""
    from django_strawberry_framework.orders import OrderSet

    class GenreOrderSet(OrderSet):
        class Meta:
            model = Genre
            fields = ("name",)

    class GenreType(DjangoType):
        class Meta:
            model = Genre
            fields = ("id", "name")
            orderset_class = GenreOrderSet

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title")
            orderset_class = GenreOrderSet

    with pytest.raises(
        ConfigurationError,
        match=r"An orderset's Meta\.model must be its owner's model",
    ):
        finalize_django_types()
