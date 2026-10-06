"""Finalizer malformed-state and hostile-metadata boundaries."""

from __future__ import annotations

from collections.abc import Mapping

import pytest
from apps.library.models import Book, Genre
from strawberry import relay
from typing_extensions import override

from django_strawberry_framework import DjangoType, finalize_django_types
from django_strawberry_framework.exceptions import ConfigurationError, _safe_class_name
from django_strawberry_framework.registry import registry
from django_strawberry_framework.types import finalizer as finalizer_module
from django_strawberry_framework.types.finalizer import (
    _annotation_names,
    _audit_model_label_routing,
    _safe_field_label,
    _safe_qualified_class_name,
    _safe_str,
    _warn_model_label_secondary_collapse,
)
from django_strawberry_framework.types.relations import PendingRelation


@pytest.fixture(autouse=True)
def _isolate_registry(isolate_global_registry: None) -> None:
    """Every test here declares fresh ``DjangoType`` classes - opt the module
    into the shared registry/connection-cache isolation (``tests/conftest.py``)."""


class _HostileNameMeta(type):
    @property
    @override
    # basedpyright: the hostile shape under test, a ``__name__`` property whose read raises; the
    # checker rejects any property overriding a base class attribute
    def __name__(cls):  # pyright: ignore[reportIncompatibleVariableOverride]
        raise RuntimeError("hostile model name")


class _HostileName(metaclass=_HostileNameMeta):
    pass


class _HostileString(str):
    @override
    def __str__(self):
        raise RuntimeError("hostile field name")


class _HostileAnnotations(Mapping[str, object]):
    def __init__(self, values: Mapping[str, object]):
        self._values = dict(values)

    @override
    def __iter__(self):
        return iter(self._values)

    @override
    def __len__(self):
        return len(self._values)

    @override
    def __getitem__(self, key: str):
        raise RuntimeError("hostile annotation lookup")


def test_unresolved_relation_diagnostic_survives_hostile_model_name():
    """Malformed pending metadata remains a typed finalization failure."""
    registry.add_pending_relation(
        PendingRelation(
            # basedpyright: the class whose __name__ raises is the hostile input under test;
            # PendingRelation types source_type as type[DjangoType] and source_model as type[Model]
            source_type=_HostileName,  # pyright: ignore[reportArgumentType]
            source_model=_HostileName,  # pyright: ignore[reportArgumentType]
            field_name="books",
            # basedpyright: a stand-in field the failing path never reads; PendingRelation types
            # django_field as ModelField
            django_field=object(),  # pyright: ignore[reportArgumentType]
            # basedpyright: the class whose __name__ raises is the hostile input under test;
            # PendingRelation types related_model as type[Model]
            related_model=_HostileName,  # pyright: ignore[reportArgumentType]
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

    # basedpyright: the int annotation key is the hostile input under test; typeshed types
    # __annotations__ keys as str
    BookType.__annotations__[123] = str  # pyright: ignore[reportArgumentType]

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

    assert registry.get(Genre) is GenreType

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title", "genres")
            interfaces = (relay.Node,)
            relation_shapes = {"genres": "connection"}

    # basedpyright: the planted _HostileAnnotations mapping is the hostile input under test; the
    # checker types a class's __annotations__ as dict[str, object]
    BookType.__annotations__ = _HostileAnnotations(BookType.__annotations__)  # pyright: ignore[reportAttributeAccessIssue]

    with pytest.raises(
        ConfigurationError,
        match="relation annotation genres could not be rewritten",
    ):
        finalize_django_types()


def test_malformed_pending_field_name_is_rejected_before_relation_lookup():
    """A pending ``field_name`` outside the field map fails finalize as ``ConfigurationError``."""

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title", "genres")

    class GenreType(DjangoType):
        class Meta:
            model = Genre
            fields = ("id", "name")

    assert registry.get(Genre) is GenreType

    field = Book._meta.get_field("genres")
    registry.add_pending_relation(
        PendingRelation(
            source_type=BookType,
            source_model=Book,
            # basedpyright: the non-str field name is the hostile input under test; PendingRelation
            # types field_name as str
            field_name=123,  # pyright: ignore[reportArgumentType]
            django_field=field,
            related_model=Genre,
        ),
    )

    with pytest.raises(ConfigurationError, match="invalid field metadata"):
        finalize_django_types()


def test_primary_ambiguity_diagnostic_survives_hostile_model_name():
    """The ambiguity audit keeps malformed registry metadata typed."""
    # basedpyright: the class whose __name__ raises is the hostile input under test and the plain
    # classes stand in for DjangoTypes; TypeRegistry.register types the parameters as type[Model]
    # and type[DjangoType]
    registry.register(_HostileName, type("FirstType", (), {}))  # pyright: ignore[reportArgumentType]
    registry.register(_HostileName, type("SecondType", (), {}))  # pyright: ignore[reportArgumentType]

    with pytest.raises(ConfigurationError, match="multiple registered"):
        finalize_django_types()


def test_finalizer_diagnostic_renderers_survive_hostile_metadata():
    """Every diagnostic renderer falls back to its documented placeholder label.

    Each assertion pins the exact fallback string, so a regression that swaps
    one placeholder for another (or renders hostile metadata verbatim) fails
    instead of passing on mere non-emptiness.
    """

    class _HostileText(str):
        @override
        def __str__(self):
            raise RuntimeError("text exploded")

    class _HostileMeta(type):
        @override
        def __getattribute__(cls, name: str):
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
        @override
        def __getattribute__(cls, name: str):
            if name == "__name__":
                return 123
            return super().__getattribute__(name)

    class _NonStringName(metaclass=_NonStringNameMeta):
        pass

    class _UnreadableModuleMeta(type):
        @override
        def __getattribute__(cls, name: str):
            if name == "__module__":
                raise RuntimeError("module exploded")
            return super().__getattribute__(name)

    class _UnreadableModule(metaclass=_UnreadableModuleMeta):
        pass

    class _NonStringModuleMeta(type):
        @override
        def __getattribute__(cls, name: str):
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

    class _UnreadableAnnotations(Mapping[str, object]):
        @override
        def __iter__(self):
            raise RuntimeError("annotation enumeration exploded")

        @override
        def __len__(self):
            return 1

        @override
        def __getitem__(self, key: str):
            raise KeyError(key)

    class _Type:
        # basedpyright: an unreadable annotations mapping replaces the dict on purpose; the test
        # proves ``_annotation_names`` turns the failure into a ConfigurationError
        __annotations__ = _UnreadableAnnotations()  # pyright: ignore[reportAssignmentType]

    with pytest.raises(ConfigurationError, match="annotations could not be read"):
        # basedpyright: the class with unreadable annotations is the hostile input under test;
        # _annotation_names types the parameter as type[DjangoType]
        _annotation_names(_Type)  # pyright: ignore[reportArgumentType]


def test_pending_relation_without_source_definition_is_typed():
    """A pending relation whose source type never registered a definition raises."""
    target_type = type("GenreType", (), {})
    # basedpyright: a plain stand-in class carrying only the hooks the code under test reads;
    # TypeRegistry.register types the parameter as type[DjangoType]
    registry.register(Genre, target_type)  # pyright: ignore[reportArgumentType]
    registry.add_pending_relation(
        PendingRelation(
            # basedpyright: the definition-less class is the hostile input under test;
            # PendingRelation types source_type as type[DjangoType]
            source_type=type("MissingDefinition", (), {}),  # pyright: ignore[reportArgumentType]
            source_model=Book,
            field_name="genres",
            django_field=Book._meta.get_field("genres"),
            related_model=Genre,
        ),
    )

    with pytest.raises(
        ConfigurationError,
        match="pending relation genres has no DjangoTypeDefinition",
    ):
        finalize_django_types()


def test_model_label_routing_audit_rejects_a_missing_primary_definition(
    monkeypatch: pytest.MonkeyPatch,
):
    """The routing audit rejects a primary type carrying no registered definition."""
    primary = type("Primary", (), {})
    emitter = type("Emitter", (), {})

    def _emitter_for(model: object) -> type:
        return emitter

    def _primary_for(model: object) -> type:
        return primary

    def _no_definition(type_cls: object) -> None:
        return None

    monkeypatch.setattr(finalizer_module, "_first_model_label_emitter", _emitter_for)
    monkeypatch.setattr(registry, "primary_for", _primary_for)
    monkeypatch.setattr(registry, "get_definition", _no_definition)

    with pytest.raises(ConfigurationError, match="has no registered DjangoTypeDefinition"):
        _audit_model_label_routing((Book,))


def test_secondary_collapse_warning_survives_unreadable_model_metadata(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
):
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

    def _primary_for(model: object) -> type:
        return primary

    def _types_for(model: object) -> tuple[type, type]:
        return (primary, secondary)

    def _definition_for(type_cls: object) -> object:
        return definition

    monkeypatch.setattr(registry, "primary_for", _primary_for)
    monkeypatch.setattr(registry, "types_for", _types_for)
    monkeypatch.setattr(registry, "get_definition", _definition_for)

    # basedpyright: the model whose _meta is unreadable is the hostile input under test;
    # _warn_model_label_secondary_collapse types the parameter as tuple[type[Model], ...]
    _warn_model_label_secondary_collapse((_Model,))  # pyright: ignore[reportArgumentType]

    assert "identity collapse" in caplog.text


def test_incomplete_registry_registration_is_typed_at_finalize():
    """A bare registry registration cannot leak an AttributeError from the model-label audit."""

    class BareModel:
        pass

    # basedpyright: the bare class and plain types are the incomplete registration under test;
    # TypeRegistry.register types the parameters as type[Model] and type[DjangoType]
    registry.register(BareModel, type("PrimaryType", (), {}), primary=True)  # pyright: ignore[reportArgumentType]
    registry.register(BareModel, type("SecondaryType", (), {}))  # pyright: ignore[reportArgumentType]

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

    # basedpyright: a plain stand-in class carrying only the hooks the code under test reads;
    # _field_surface_names types the parameter as type[DjangoType]
    surface = _field_surface_names(_ChildType)  # pyright: ignore[reportArgumentType]
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

    assert registry.get(Genre) is GenreType

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title")
            filterset_class = GenreFilterSet

    assert registry.get(Book) is BookType

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

    assert registry.get(Genre) is GenreType

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

    assert registry.get(Genre) is GenreType

    class BookType(DjangoType):
        class Meta:
            model = Book
            fields = ("id", "title")
            orderset_class = GenreOrderSet

    assert registry.get(Book) is BookType

    with pytest.raises(
        ConfigurationError,
        match=r"An orderset's Meta\.model must be its owner's model",
    ):
        finalize_django_types()
