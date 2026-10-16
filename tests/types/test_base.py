"""DjangoType tests for Meta validation, scalar mapping, relations, registry, and get_queryset.

Scope:

- registry behaviour (``register``, ``get``, collision, ``clear``).
- Meta validation, scalar field synthesis, default ``get_queryset``,
  Strawberry finalization, ``convert_scalar`` direct unit coverage.
- relation conversion (forward FK, reverse FK, nullable widening,
  finalization-time unregistered-target rejection); ``_build_annotations`` dispatch on
  ``field.is_relation`` rather than filtering relations out.

The ``has_custom_get_queryset`` sentinel and override-detection have
shipped and are tested directly. Optimizer downgrade-to-``Prefetch``
coverage belongs in ``tests/optimizer/``; the full forward-reference /
definition-order independence path is covered in
``tests/types/test_definition_order.py`` and
``tests/types/test_definition_order_schema.py``.

Meta-validation tests avoid ``fields = "__all__"`` on ``Category``:
they either declare related types up front (so the registry resolves
``items`` / ``properties``) or use an explicit fields list to keep the
test focused on the behaviour under examination. ``CATEGORY_SCALAR_FIELDS``
captures the scalar-only field list used in those updated tests.
"""

import datetime
import functools
import inspect
import itertools
import sys
import types
from collections.abc import Callable, Collection, Sequence
from typing import NoReturn

import pytest
import pytest_django
import strawberry
from apps.library.models import Patron
from apps.products.models import Category, Entry, Item, Property
from apps.scalars.models import MediaSpecimen
from django.db import models
from django.db.models.expressions import Combinable
from django.utils.functional import Promise, SimpleLazyObject
from django.utils.translation import gettext_lazy
from strawberry import relay
from strawberry.types import get_object_definition
from strawberry.types.auto import StrawberryAuto
from typing_extensions import override

import django_strawberry_framework.types.base as base_mod
from django_strawberry_framework import DjangoType, finalize_django_types
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.filters import FilterSet
from django_strawberry_framework.optimizer.hints import OptimizerHint
from django_strawberry_framework.registry import registry
from django_strawberry_framework.types import converters
from django_strawberry_framework.types.base import (
    ALLOWED_META_KEYS,
    DEFERRED_META_KEYS,
    _detect_custom_get_queryset,
    _meta_optimizer_hints,
    _normalize_fields_spec,
    _normalize_sequence_spec,
    _select_fields,
    _validate_connection,
    _validate_cursor_field,
    _validate_filterset_class,
    _validate_globalid_callable,
    _validate_globalid_strategy,
    _validate_interfaces,
    _validate_orderset_class,
    _validate_relation_shapes,
)
from django_strawberry_framework.types.converters import (
    DjangoFilePathType,
    DjangoFileType,
    DjangoImagePathType,
    DjangoImageType,
    convert_scalar,
    resolved_relation_annotation,
)
from django_strawberry_framework.types.relations import PendingRelationAnnotation
from django_strawberry_framework.types.relay import (
    _resolve_globalid_strategy,
    _validated_globalid_setting,
)
from tests._idioms import ClaimsClass, ClassReadRaisesBase, definition_raises, is_object_dict
from tests.optimizer import _link_models

CATEGORY_SCALAR_FIELDS = (
    "id",
    "name",
    "description",
    "is_private",
    "created_date",
    "updated_date",
)


pytestmark = pytest.mark.usefixtures("isolate_global_registry")


# ---------------------------------------------------------------------------
# Registry behaviour
# ---------------------------------------------------------------------------


def test_registry_get_returns_none_for_unregistered_model() -> None:
    assert registry.get(Category) is None


def test_registry_collision_raises_configuration_error() -> None:
    class CategoryTypeA(DjangoType):
        class Meta:
            model = Category
            fields = CATEGORY_SCALAR_FIELDS
            primary = True

    assert registry.get(Category) is CategoryTypeA

    with pytest.raises(
        ConfigurationError,
        match=(
            r"Cannot register CategoryTypeB as primary for Category;"
            r".*CategoryTypeA is already the primary type"
        ),
    ):

        @definition_raises
        class CategoryTypeB(DjangoType):
            class Meta:
                model = Category
                fields = CATEGORY_SCALAR_FIELDS
                primary = True


def test_registry_clear_drops_types_and_enums() -> None:
    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = CATEGORY_SCALAR_FIELDS

    assert registry.get(Category) is CategoryType
    registry.clear()
    assert registry.get(Category) is None


# ---------------------------------------------------------------------------
# Meta validation
# ---------------------------------------------------------------------------


def test_subclass_without_meta_passes_through() -> None:
    """Intermediate abstract subclasses (no Meta) skip the pipeline."""

    class AbstractType(DjangoType):
        pass

    assert registry.get(Category) is None
    assert not hasattr(AbstractType, "__strawberry_definition__")
    assert AbstractType.has_custom_get_queryset() is False


def test_detect_custom_get_queryset_returns_false_for_non_djangotype_class() -> None:
    """The helper is defensive for classes and objects outside the DjangoType hierarchy."""

    class PlainType:
        pass

    class PlainTypeWithGetQueryset:
        def get_queryset(self) -> None:
            pass

    assert _detect_custom_get_queryset(PlainType) is False
    assert _detect_custom_get_queryset(PlainTypeWithGetQueryset) is False
    assert _detect_custom_get_queryset(None) is False
    assert _detect_custom_get_queryset(123) is False
    assert _detect_custom_get_queryset("not_a_type") is False


def test_meta_required_model_raises_when_missing() -> None:
    with pytest.raises(ConfigurationError, match=r"Meta\.model is required"):

        @definition_raises
        class T(DjangoType):
            class Meta:
                fields = CATEGORY_SCALAR_FIELDS


def test_meta_model_must_be_django_model_class() -> None:
    with pytest.raises(ConfigurationError, match=r"Meta\.model must be a Django model class"):

        @definition_raises
        class T(DjangoType):
            class Meta:
                model = "Category"
                fields = CATEGORY_SCALAR_FIELDS


@pytest.mark.parametrize(
    ("attr", "value", "message"),
    [
        ("fields", 123, "Meta.fields must be '__all__' or a non-string sequence"),
        ("fields", "name", "Meta.fields must be '__all__' or a non-string sequence"),
        ("exclude", 123, "Meta.exclude must be a non-string sequence"),
        ("exclude", "name", "Meta.exclude must be a non-string sequence"),
    ],
)
def test_meta_field_selectors_must_have_valid_shapes(
    attr: str,
    value: object,
    message: str,
) -> None:
    meta_cls = type("Meta", (), {"model": Category, attr: value})
    with pytest.raises(ConfigurationError, match=message):
        type("T", (DjangoType,), {"Meta": meta_cls})


def test_meta_optimizer_hints_must_be_mapping_when_declared() -> None:
    with pytest.raises(ConfigurationError, match=r"Meta\.optimizer_hints must be a mapping"):

        @definition_raises
        class T(DjangoType):
            class Meta:
                model = Category
                fields = CATEGORY_SCALAR_FIELDS
                optimizer_hints = []


def test_meta_optimizer_hints_rejects_non_string_keys() -> None:
    with pytest.raises(
        ConfigurationError,
        match=r"Meta\.optimizer_hints keys must be field name strings",
    ):

        @definition_raises
        class T(DjangoType):
            class Meta:
                model = Category
                fields = ["items"]
                optimizer_hints = {123: OptimizerHint.prefetch_related()}


def test_meta_optimizer_hints_rejects_mixed_non_string_keys_safely() -> None:
    with pytest.raises(
        ConfigurationError,
        match=r"Meta\.optimizer_hints keys must be field name strings",
    ):

        @definition_raises
        class T(DjangoType):
            class Meta:
                model = Category
                fields = ["items"]
                optimizer_hints = {
                    "unknown_field": OptimizerHint.prefetch_related(),
                    123: OptimizerHint.prefetch_related(),
                }


class _HostileMetaValue:
    """A malformed Meta value whose diagnostic representation raises."""

    @override
    def __repr__(self) -> str:
        raise RuntimeError("repr should not escape")


class _HostileMetaSequence(Sequence[object]):
    """A sequence whose item access raises while a Meta value is inspected.

    Both call sites reach ``__getitem__`` through the ``Sequence`` ABC's
    derived iterator, so ``__len__`` is never the failing step.
    """

    @override
    def __getitem__(self, index: int | slice) -> NoReturn:
        raise RuntimeError("sequence access should not escape")

    @override
    def __len__(self) -> int:
        raise RuntimeError("sequence length should not escape")


def test_meta_validator_diagnostics_survive_hostile_values() -> None:
    """Malformed Meta values cannot replace ConfigurationError with repr failures."""
    hostile = _HostileMetaValue()

    class InterfaceMeta:
        interfaces = (hostile,)

    validators = (
        lambda: _validate_filterset_class(Category, hostile),
        lambda: _validate_orderset_class(Category, hostile),
        lambda: _validate_connection(Category, hostile, relay_shaped=False),
        lambda: _validate_cursor_field(Category, hostile, relay_shaped=False),
        lambda: _validate_relation_shapes(Category, hostile, relay_shaped=False),
        lambda: _validate_globalid_strategy(Category, hostile, relay_shaped=False),
        lambda: _validate_interfaces(InterfaceMeta, Category),
    )
    for validator in validators:
        with pytest.raises(ConfigurationError, match="unprintable _HostileMetaValue"):
            validator()


def test_meta_connection_unknown_keys_are_typed_for_mixed_and_hostile_keys() -> None:
    """Unknown connection keys cannot leak sorting or repr exceptions."""
    with pytest.raises(ConfigurationError, match="unknown sub-keys"):
        _validate_connection(Category, {1: True, "bogus": False}, relay_shaped=False)
    with pytest.raises(ConfigurationError, match="unknown sub-keys"):
        _validate_connection(Category, {_HostileMetaValue(): True}, relay_shaped=False)


def test_meta_cursor_field_hostile_sequence_is_typed() -> None:
    """A broken sequence descriptor cannot escape as a raw runtime exception."""
    with pytest.raises(ConfigurationError, match="non-empty non-string sequence"):
        _validate_cursor_field(Category, _HostileMetaSequence(), relay_shaped=True)


@pytest.mark.parametrize("key", ["fields", "exclude"])
def test_meta_field_collections_wrap_hostile_iteration(key: str) -> None:
    """A field collection that raises while iterating stays a typed shape error."""
    meta_cls = type("Meta", (), {"model": Category, key: _HostileMetaSequence()})

    with pytest.raises(ConfigurationError, match=f"Meta.{key} must"):
        type("T", (DjangoType,), {"Meta": meta_cls})


def test_meta_name_rejects_an_empty_string() -> None:
    """An empty ``Meta.name`` is rejected at type creation."""
    with pytest.raises(ConfigurationError, match="empty name"):

        @definition_raises
        class T(DjangoType):
            class Meta:
                model = Category
                fields = CATEGORY_SCALAR_FIELDS
                name = ""


def test_meta_name_rejects_hostile_values_at_type_creation() -> None:
    """A malformed ``Meta.name`` cannot survive to Strawberry schema creation."""

    class HostileName:
        @override
        def __repr__(self) -> str:
            raise RuntimeError("repr should not escape")

    with pytest.raises(
        ConfigurationError,
        match=r"Meta\.name must be a non-empty string; got <unprintable HostileName>",
    ):

        @definition_raises
        class BadNameType(DjangoType):
            class Meta:
                model = Category
                fields = CATEGORY_SCALAR_FIELDS
                name = HostileName()


def test_meta_name_rejects_invalid_graphql_names_at_type_creation() -> None:
    """A syntactically invalid GraphQL name cannot leak Strawberry's GraphQLError."""
    with pytest.raises(ConfigurationError, match="valid GraphQL name"):

        @definition_raises
        class BadNameType(DjangoType):
            class Meta:
                model = Category
                fields = CATEGORY_SCALAR_FIELDS
                name = "bad-name"


def test_globalid_callable_wraps_non_signature_inspection_errors() -> None:
    """A ``__signature__`` descriptor that raises is a typed configuration failure."""

    class _UnreadableSignature:
        @property
        def __signature__(self) -> NoReturn:
            raise RuntimeError("signature exploded")

        def __call__(
            self,
            _type_cls: type[DjangoType],
            _model: type[models.Model],
            _root: object,
        ) -> str:
            return "value"

    with pytest.raises(ConfigurationError, match="could not be inspected"):
        _validate_globalid_callable("Meta.globalid_strategy", _UnreadableSignature())


def test_meta_globalid_callable_hostile_descriptor_is_typed() -> None:
    """A broken callable descriptor cannot escape GlobalID strategy validation."""

    class HostileCallable:
        @property
        def __call__(self) -> NoReturn:
            raise RuntimeError("callable descriptor should not escape")

    with pytest.raises(ConfigurationError, match="could not be inspected"):
        _validate_globalid_strategy(Category, HostileCallable(), relay_shaped=True)


# ---------------------------------------------------------------------------
# Meta values whose class cannot be read, or that claim another class
# ---------------------------------------------------------------------------

_CLASS_READ_ERRORS = [RuntimeError, KeyboardInterrupt]
_CLASS_READ_ERROR_IDS = ["RuntimeError", "KeyboardInterrupt"]


class _ClassReadRaises(ClassReadRaisesBase):
    """A value whose ``__class__`` read raises, so a bare ``isinstance`` on it raises."""

    def __init__(self, raised: type[BaseException]) -> None:
        super().__init__(raised, "class read")

    @override
    def __repr__(self) -> str:
        return "<class-read-raises>"


class _ClaimsClass(ClaimsClass):
    """A value that is not a ``claimed`` instance whose ``__class__`` says it is one."""

    @override
    def __repr__(self) -> str:
        return "<claims-class>"


_HINT = OptimizerHint.prefetch_related()
_STRATEGY_TYPES = "['model', 'type', 'type+model']"
_SHAPES_TAIL = "valid shapes are ['both', 'connection', 'list']."
_CURSOR_SHAPE = (
    "Category.Meta.cursor_field must be a non-empty non-string sequence of order strings; "
    "got {shown}"
)
_FIELDS_SHAPE = "Meta.fields must be '__all__' or a non-string sequence of field names"
_SET_SHAPE = "Meta.{key} must be a non-string sequence or set of field names"

# (route, Meta attributes built from the hostile value, message). ``{shown}`` is the value's
# ``repr`` and ``{kind}`` its class name, the two renderings a rejection prints.
_UNREADABLE_META_ROUTES: tuple[tuple[str, Callable[[object], dict[str, object]], str], ...] = (
    ("model", lambda v: {"model": v}, "Meta.model must be a Django model class"),
    ("name", lambda v: {"name": v}, "Category.Meta.name must be a non-empty string; got {shown}."),
    (
        "description",
        lambda v: {"description": v},
        "Category.Meta.description must be a string or a lazy translation string; got {shown}.",
    ),
    ("primary", lambda v: {"primary": v}, "Meta.primary must be a bool"),
    ("fields", lambda v: {"fields": v}, _FIELDS_SHAPE),
    (
        "fields-entry",
        lambda v: {"fields": ("id", v)},
        "Meta.fields must contain field name strings; got {shown}",
    ),
    ("exclude", lambda v: {"exclude": v}, _SET_SHAPE.format(key="exclude")),
    (
        "exclude-entry",
        lambda v: {"exclude": (v,)},
        "Meta.exclude must contain field name strings; got {shown}",
    ),
    (
        "nullable_overrides",
        lambda v: {"nullable_overrides": v},
        _SET_SHAPE.format(key="nullable_overrides"),
    ),
    (
        "required_overrides",
        lambda v: {"required_overrides": v},
        _SET_SHAPE.format(key="required_overrides"),
    ),
    (
        "filesystem_path_fields",
        lambda v: {"filesystem_path_fields": v},
        _SET_SHAPE.format(key="filesystem_path_fields"),
    ),
    (
        "filesystem_path_fields-entry",
        lambda v: {"filesystem_path_fields": (v,)},
        "Meta.filesystem_path_fields must contain field name strings; got {shown}",
    ),
    (
        "optimizer_hints",
        lambda v: {"optimizer_hints": v},
        (
            "Category.Meta.optimizer_hints must be a mapping of field names to OptimizerHint "
            "instances, got {kind}."
        ),
    ),
    (
        "optimizer_hints-key",
        lambda v: {"optimizer_hints": {v: _HINT}},
        "Category.Meta.optimizer_hints keys must be field name strings; got {shown}.",
    ),
    (
        "optimizer_hints-value",
        lambda v: {"fields": ("id", "items"), "optimizer_hints": {"items": v}},
        (
            "optimizer_hints values must be OptimizerHint instances, "
            "got non-OptimizerHint for: ['items']"
        ),
    ),
    (
        "interfaces",
        lambda v: {"interfaces": v},
        (
            "Category.Meta.interfaces must be a tuple/list of Strawberry interface classes "
            "or a single interface class, got {kind}."
        ),
    ),
    (
        "interfaces-entry",
        lambda v: {"interfaces": (v,)},
        "Category.Meta.interfaces must contain interface classes, got {shown}.",
    ),
    (
        "connection",
        lambda v: {"connection": v, "interfaces": (relay.Node,)},
        "Category.Meta.connection must be a dict; got {shown}",
    ),
    (
        "connection-total_count",
        lambda v: {"connection": {"total_count": v}, "interfaces": (relay.Node,)},
        "Category.Meta.connection['total_count'] must be a bool; got {shown}",
    ),
    (
        "cursor_field",
        lambda v: {"cursor_field": v, "interfaces": (relay.Node,)},
        _CURSOR_SHAPE,
    ),
    (
        "cursor_field-entry",
        lambda v: {"cursor_field": (v,), "interfaces": (relay.Node,)},
        _CURSOR_SHAPE.replace("{shown}", "({shown},)"),
    ),
    (
        "relation_shapes",
        lambda v: {"relation_shapes": v, "interfaces": (relay.Node,)},
        (
            "Category.Meta.relation_shapes must be a dict mapping relation field names to "
            "shapes; got {shown}"
        ),
    ),
    (
        "relation_shapes-key",
        lambda v: {"relation_shapes": {v: "list"}, "interfaces": (relay.Node,)},
        "Category.Meta.relation_shapes keys must be relation field name strings; got {shown}.",
    ),
    (
        "relation_shapes-value",
        lambda v: {"relation_shapes": {"items": v}, "interfaces": (relay.Node,)},
        "Category.Meta.relation_shapes['items'] got unknown shape {shown}; " + _SHAPES_TAIL,
    ),
    (
        "globalid_strategy",
        lambda v: {"globalid_strategy": v, "interfaces": (relay.Node,)},
        (
            f"Category.Meta.globalid_strategy must be one of {_STRATEGY_TYPES} or a callable; "
            "got {shown}."
        ),
    ),
)


@pytest.mark.parametrize("raised", _CLASS_READ_ERRORS, ids=_CLASS_READ_ERROR_IDS)
@pytest.mark.parametrize(
    ("make_meta", "message"),
    [(make_meta, message) for _, make_meta, message in _UNREADABLE_META_ROUTES],
    ids=[route for route, _, _ in _UNREADABLE_META_ROUTES],
)
def test_meta_value_whose_class_cannot_be_read_is_the_typed_rejection(
    make_meta: Callable[[object], dict[str, object]],
    message: str,
    raised: type[BaseException],
) -> None:
    """A ``Meta`` value (or entry) whose ``__class__`` read raises is rejected like any malformed one.

    Every gate asks the value's class through a guarded test, so the rejection each
    key's contract promises is the one raised, never the consumer's own exception.
    """
    meta = type("Meta", (), {"model": Category, **make_meta(_ClassReadRaises(raised))})

    with pytest.raises(ConfigurationError) as excinfo:
        type("T", (DjangoType,), {"Meta": meta})

    assert str(excinfo.value) == message.format(
        shown="<class-read-raises>",
        kind="_ClassReadRaises",
    )


@pytest.mark.parametrize("raised", _CLASS_READ_ERRORS, ids=_CLASS_READ_ERROR_IDS)
def test_relay_globalid_setting_whose_class_cannot_be_read_is_the_typed_rejection(
    settings: pytest_django.Settings,
    raised: type[BaseException],
) -> None:
    """The ``RELAY_GLOBALID_STRATEGY`` setting runs the same gate as ``Meta.globalid_strategy``."""
    settings.DJANGO_STRAWBERRY_FRAMEWORK = {
        "RELAY_GLOBALID_STRATEGY": _ClassReadRaises(raised),
    }

    with pytest.raises(ConfigurationError) as excinfo:
        _validated_globalid_setting()

    assert str(excinfo.value) == (
        f"RELAY_GLOBALID_STRATEGY must be one of {_STRATEGY_TYPES} or a callable; "
        "got <class-read-raises>."
    )


@pytest.mark.parametrize(
    ("route", "value", "message"),
    [
        (
            "name-claims-str",
            _ClaimsClass(str),
            "Category.Meta.name must be a non-empty string; got <claims-class>.",
        ),
        (
            "description-claims-str",
            _ClaimsClass(str),
            (
                "Category.Meta.description must be a string or a lazy translation string; "
                "got <claims-class>."
            ),
        ),
        ("model-claims-type", _ClaimsClass(type), "Meta.model must be a Django model class"),
    ],
    ids=["name-claims-str", "description-claims-str", "model-claims-type"],
)
def test_meta_value_claiming_the_class_it_is_not_is_the_typed_rejection(
    route: str,
    value: object,
    message: str,
) -> None:
    """A value whose ``__class__`` claims ``str`` / ``type`` is refused, never read as one.

    ``Meta.name`` and ``Meta.description`` read the text through the base ``str`` slot and
    ``Meta.model`` is handed to ``issubclass``, both of which refuse a value that is not
    really a ``str`` / class, so the gate asks the real type.
    """
    key = route.split("-", maxsplit=1)[0]
    meta = type("Meta", (), {"model": Category, "fields": CATEGORY_SCALAR_FIELDS, key: value})

    with pytest.raises(ConfigurationError) as excinfo:
        type("T", (DjangoType,), {"Meta": meta})

    assert str(excinfo.value) == message


@pytest.mark.parametrize("key", ["name", "description"])
def test_meta_text_that_is_a_lazy_proxy_of_a_string_is_the_typed_rejection(key: str) -> None:
    """A ``SimpleLazyObject`` around a ``str`` is not a ``str``, so ``Meta.name`` refuses it.

    ``Meta.description`` refuses it the same way.

    The base ``str`` slot refuses a proxy, so the gate asks the real type.
    """
    meta = type(
        "Meta",
        (),
        {
            "model": Category,
            "fields": CATEGORY_SCALAR_FIELDS,
            key: SimpleLazyObject(lambda: "Named"),
        },
    )

    with pytest.raises(ConfigurationError, match=rf"Category\.Meta\.{key} must be a "):
        type("T", (DjangoType,), {"Meta": meta})


def test_meta_class_that_inherits_str_still_contributes_the_text_it_holds() -> None:
    """The real-type test passes a ``str`` subclass, and only its text is kept."""

    class ShoutingName(str):
        @override
        def __str__(self) -> str:
            raise RuntimeError("the subclass's own __str__ is never run")

    class NamedType(DjangoType):
        class Meta:
            model = Category
            fields = CATEGORY_SCALAR_FIELDS
            name = ShoutingName("CategoryNode")
            description = ShoutingName("About categories")

    definition = NamedType.__django_strawberry_definition__
    assert type(definition.name) is str
    assert definition.name == "CategoryNode"
    assert type(definition.description) is str
    assert definition.description == "About categories"


def _lazy(value: object) -> object:
    """A faithful lazy proxy around ``value`` (``isinstance`` answers as the wrapped value)."""
    return SimpleLazyObject(lambda: value)


@pytest.mark.parametrize(
    ("accepts", "expected"),
    [
        (lambda: _normalize_fields_spec(_lazy(("id", "name"))), ("id", "name")),
        (lambda: _normalize_fields_spec(("id", _lazy("name"))), ("id", "name")),
        (lambda: _normalize_sequence_spec(_lazy(["name"])), ("name",)),
        (lambda: _normalize_sequence_spec(_lazy({"name"})), ("name",)),
        (lambda: _validate_connection(Category, _lazy({}), relay_shaped=True), {}),
        (
            lambda: _validate_connection(
                Category,
                {"total_count": SimpleLazyObject(lambda: True)},
                relay_shaped=True,
            ),
            {"total_count": True},
        ),
        (
            lambda: _validate_cursor_field(Category, _lazy(("id",)), relay_shaped=True),
            ("id",),
        ),
        (
            lambda: _validate_cursor_field(Category, (_lazy("id"),), relay_shaped=True),
            ("id",),
        ),
        (
            lambda: _validate_relation_shapes(
                Category,
                _lazy({"items": "both"}),
                relay_shaped=True,
            ),
            {"items": "both"},
        ),
        (lambda: _validate_globalid_strategy(Category, _lazy("type"), relay_shaped=True), "type"),
        (
            lambda: _validate_interfaces(
                type("M", (), {"interfaces": _lazy((relay.Node,))}),
                Category,
            ),
            (relay.Node,),
        ),
        (
            lambda: _meta_optimizer_hints(
                type("M", (), {"optimizer_hints": _lazy({"items": _HINT})}),
                Category,
            ),
            {"items": _HINT},
        ),
    ],
    ids=[
        "fields-proxy",
        "fields-entry-proxy",
        "exclude-list-proxy",
        "exclude-set-proxy",
        "connection-proxy",
        "connection-total_count-proxy",
        "cursor_field-proxy",
        "cursor_field-entry-proxy",
        "relation_shapes-proxy",
        "globalid_strategy-proxy",
        "interfaces-proxy",
        "optimizer_hints-proxy",
    ],
)
def test_meta_gates_keep_accepting_a_faithful_proxy_of_the_right_class(
    accepts: Callable[[], object],
    expected: object,
) -> None:
    """The gates ask ``isinstance``, so a lazy proxy of a valid value passes as the value itself."""
    assert accepts() == expected


def test_meta_model_and_primary_proxies_register_the_type() -> None:
    """A lazy proxy of the model class and of the ``primary`` flag are accepted at class creation."""

    class ProxiedType(DjangoType):
        class Meta:
            model = _lazy(Category)
            fields = CATEGORY_SCALAR_FIELDS
            primary = SimpleLazyObject(lambda: True)

    assert bool(ProxiedType.__django_strawberry_definition__.primary) is True


def _inject_annotation_key(*keys: object) -> type[type]:
    """A metaclass that adds each of ``keys`` to the class annotations before the class exists."""

    class InjectAnnotationKeysMeta(type):
        def __new__(
            mcs,
            name: str,
            bases: tuple[type, ...],
            namespace: dict[str, object],
            **kwargs: object,
        ) -> type:
            namespace["__annotations__"] = dict.fromkeys(keys, str)
            return super().__new__(mcs, name, bases, namespace, **kwargs)

    return InjectAnnotationKeysMeta


_NON_STRING_KEYS_TAIL = (
    ". Annotation keys are field names; non-string keys cannot be synthesized or exposed."
)


@pytest.mark.parametrize(
    ("keys", "shown"),
    [
        ((1,), "[1]"),
        ((2, 1), "[1, 2]"),
        ((_HostileMetaValue(),), "[<unprintable _HostileMetaValue>]"),
        ((_ClassReadRaises(RuntimeError),), "[<class-read-raises>]"),
        ((_ClassReadRaises(KeyboardInterrupt),), "[<class-read-raises>]"),
        ((_ClaimsClass(str),), "[<claims-class>]"),
    ],
    ids=[
        "int",
        "ints-sorted-by-repr",
        "repr-raises",
        "class-read-raises-runtime",
        "class-read-raises-base-exception",
        "class-claims-str",
    ],
)
def test_non_string_annotation_key_is_rejected_whatever_its_class_or_repr(
    keys: tuple[object, ...],
    shown: str,
) -> None:
    """A metaclass-injected annotation key that is not really a ``str`` takes the typed rejection.

    The keys are rendered through the guarded repr and sorted by their rendering, and the test
    asks the key's real type, so a key whose ``__repr__`` raises, whose ``__class__`` raises,
    or whose ``__class__`` claims ``str`` is reported alongside the honest ones.
    """
    with pytest.raises(ConfigurationError) as excinfo:

        @definition_raises
        class ProbeKeysType(DjangoType, metaclass=_inject_annotation_key(*keys)):
            class Meta:
                model = Category
                fields = CATEGORY_SCALAR_FIELDS

    assert str(excinfo.value) == (
        f"ProbeKeysType: class annotations must have string names; got non-string keys {shown}"
        + _NON_STRING_KEYS_TAIL
    )


@pytest.mark.parametrize(
    ("field", "kind"),
    [("name", "scalar"), ("items", "relation")],
    ids=["scalar", "relation"],
)
@pytest.mark.parametrize("raised", _CLASS_READ_ERRORS, ids=_CLASS_READ_ERROR_IDS)
def test_class_attribute_whose_class_cannot_be_read_is_a_shadow_rejection(
    field: str,
    kind: str,
    raised: type[BaseException],
) -> None:
    """A class attribute shadowing a model field is not a ``StrawberryField`` when its class is unreadable."""
    namespace = {
        "Meta": type("Meta", (), {"model": Category, "fields": ("id", field)}),
        field: _ClassReadRaises(raised),
    }

    with pytest.raises(ConfigurationError) as excinfo:
        type("ProbeShadowType", (DjangoType,), namespace)

    assert str(excinfo.value) == (
        f"ProbeShadowType.{field} shadows a Django {kind} field with an unsupported "
        "class attribute. Use a type annotation for type overrides, or use "
        "strawberry.field(resolver=...) / @strawberry.field for resolver overrides."
    )


@pytest.mark.parametrize(
    "attr",
    [
        "fields",
        "exclude",
        "nullable_overrides",
        "required_overrides",
        "filesystem_path_fields",
    ],
)
def test_meta_name_collections_reject_non_string_entries(attr: str) -> None:
    """All field-name collections reject unhashable entries before set operations."""
    meta = type("Meta", (), {"model": Category, attr: (["name"],)})
    with pytest.raises(ConfigurationError, match=f"Meta.{attr} must contain field name strings"):
        type("InvalidNamesType", (DjangoType,), {"Meta": meta})


def test_meta_fields_and_exclude_mutually_exclusive() -> None:
    with pytest.raises(ConfigurationError, match="mutually exclusive"):

        @definition_raises
        class T(DjangoType):
            class Meta:
                model = Category
                fields = CATEGORY_SCALAR_FIELDS
                exclude = ["description"]


def test_meta_fields_and_exclude_mutually_exclusive_via_inheritance() -> None:
    """A ``fields`` value inherited from a parent ``Meta`` still trips the guard.

    Pins the ``getattr(meta, ..., None) is not None`` semantics: an earlier
    shape that gated on ``meta.__dict__`` membership would miss this case and
    silently let both directives coexist, with confusing field-selection
    semantics downstream. The child only declares ``exclude``; ``fields``
    comes in from the base class.
    """

    class BaseMeta:
        fields = ("id", "name")

    with pytest.raises(ConfigurationError, match="mutually exclusive"):

        @definition_raises
        class T(DjangoType):
            class Meta(BaseMeta):
                model = Category
                exclude = ("description",)


@pytest.mark.parametrize(
    "deferred_key",
    ["aggregate_class", "fields_class", "search_fields"],
)
def test_meta_rejects_each_deferred_key(deferred_key: str) -> None:
    """Every key in DEFERRED_META_KEYS must raise until the spec that owns it ships."""
    meta_attrs = {"model": Category, "fields": CATEGORY_SCALAR_FIELDS, deferred_key: object()}
    meta_cls = type("Meta", (), meta_attrs)
    with pytest.raises(ConfigurationError, match=deferred_key):
        type("T", (DjangoType,), {"Meta": meta_cls})


def test_definition_fields_class_slot_is_reserved_but_unpopulated() -> None:
    """``FieldSet`` has a metadata slot, while ``Meta.fields_class`` stays deferred."""

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = CATEGORY_SCALAR_FIELDS

    definition = registry.get_definition(CategoryType)

    assert definition is not None
    assert definition.fields_class is None


def test_meta_filterset_class_is_promoted_to_allowed_meta_keys() -> None:
    """``Meta.filterset_class`` ships per spec-027 Decision 7 (promotion gate)."""
    assert "filterset_class" in ALLOWED_META_KEYS
    assert "filterset_class" not in DEFERRED_META_KEYS


def test_meta_orderset_class_is_promoted_to_allowed_meta_keys() -> None:
    """``Meta.orderset_class`` ships in spec-028 (Decision-7 promotion gate)."""
    assert "orderset_class" in ALLOWED_META_KEYS
    assert "orderset_class" not in DEFERRED_META_KEYS


def _declare_category_type_with_interface(entry: object) -> None:
    """Declare a ``DjangoType`` subclass with ``entry`` in ``Meta.interfaces``.

    Shared boilerplate for the six named-rejection tests and the
    non-interface-class re-affirmation pin (spec-032 Decision 8); the
    declaration itself raises ``ConfigurationError`` for every entry these
    tests pass.
    """

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = CATEGORY_SCALAR_FIELDS
            interfaces = (entry,)

    assert registry.get(Category) is CategoryType


def test_interfaces_rejects_relay_globalid_named() -> None:
    """``relay.GlobalID`` in ``Meta.interfaces`` is rejected by name (Decision 8)."""
    with pytest.raises(ConfigurationError) as excinfo:
        _declare_category_type_with_interface(relay.GlobalID)
    message = str(excinfo.value)
    assert "relay.GlobalID" in message
    assert "scalar-like id wrapper" in message
    assert "`id: GlobalID!` automatically from `relay.Node`" in message


def test_interfaces_rejects_relay_nodeid_named() -> None:
    """``relay.NodeID`` (an ``Annotated`` alias, not a class) is rejected by name."""
    with pytest.raises(ConfigurationError) as excinfo:
        _declare_category_type_with_interface(relay.NodeID)
    message = str(excinfo.value)
    assert "relay.NodeID" in message
    assert "annotation helper for custom id fields (`id: relay.NodeID[int]`)" in message
    assert "add `relay.Node` to `Meta.interfaces` instead" in message


def test_interfaces_rejects_relay_connection_named() -> None:
    """``relay.Connection`` rejection names ``Meta.connection`` / ``DjangoConnectionField``."""
    with pytest.raises(ConfigurationError) as excinfo:
        _declare_category_type_with_interface(relay.Connection)
    message = str(excinfo.value)
    assert "relay.Connection" in message
    assert "generic output type" in message
    assert "Meta.connection" in message
    assert "DjangoConnectionField" in message


def test_interfaces_rejects_relay_listconnection_named() -> None:
    """``relay.ListConnection`` carries the same connection-surface remediation."""
    with pytest.raises(ConfigurationError) as excinfo:
        _declare_category_type_with_interface(relay.ListConnection)
    message = str(excinfo.value)
    assert "relay.ListConnection" in message
    assert "generic output type" in message
    assert "Meta.connection" in message
    assert "DjangoConnectionField" in message


def test_interfaces_rejects_relay_edge_named() -> None:
    """``relay.Edge`` rejection says the connection machinery instantiates it."""
    with pytest.raises(ConfigurationError) as excinfo:
        _declare_category_type_with_interface(relay.Edge)
    message = str(excinfo.value)
    assert "relay.Edge" in message
    assert "generic output type the connection machinery instantiates" in message
    assert "not consumer-declarable" in message


def test_interfaces_rejects_relay_pageinfo_named() -> None:
    """``relay.PageInfo`` rejection says it is a generated pagination type."""
    with pytest.raises(ConfigurationError) as excinfo:
        _declare_category_type_with_interface(relay.PageInfo)
    message = str(excinfo.value)
    assert "relay.PageInfo" in message
    assert "generated pagination type" in message
    assert "add `relay.Node` to `Meta.interfaces` instead" in message


def test_interfaces_rejects_non_interface_class_named() -> None:
    """Re-affirmation pin: a plain ``@strawberry.type`` class takes the generic branch.

    Pins spec-015 Decision 4's generic non-interface rejection and its
    documented message naming the offending class (spec-032).
    """

    @strawberry.type
    class PlainType:
        name: str

    with pytest.raises(ConfigurationError) as excinfo:
        _declare_category_type_with_interface(PlainType)
    message = str(excinfo.value)
    assert "PlainType" in message
    assert "is not a Strawberry interface" in message


def test_connection_key_requires_relay_node() -> None:
    """Re-affirmation pin: ``Meta.connection`` on a non-Relay-Node type raises.

    No behavior change (spec-030 Decision 8 gate); pins the full documented
    add-``relay.Node``-or-inherit-it-directly remediation (spec-032).
    """
    with pytest.raises(ConfigurationError) as excinfo:

        @definition_raises
        class CategoryType(DjangoType):
            class Meta:
                model = Category
                fields = CATEGORY_SCALAR_FIELDS
                connection = {"total_count": True}

    message = str(excinfo.value)
    assert "requires a Relay-Node-shaped type" in message
    assert "add `relay.Node` to `Meta.interfaces` or inherit `relay.Node` directly." in message


def test_meta_relation_shapes_in_allowed_meta_keys() -> None:
    """``relation_shapes`` is a shipped Meta key (spec-032 Decision 7), not deferred.

    Mirrors ``test_interfaces_is_shipped_not_deferred`` below: a net-new
    ``ALLOWED_META_KEYS`` entry, NOT a ``DEFERRED_META_KEYS`` promotion.
    """
    assert "relation_shapes" in ALLOWED_META_KEYS
    assert "relation_shapes" not in DEFERRED_META_KEYS


def _declare_relation_shapes_type(
    model: type[models.Model],
    fields: Sequence[str],
    relation_shapes: object,
    *,
    relay_node: bool = True,
    namespace_extra: dict[str, object] | None = None,
) -> type[DjangoType]:
    """Declare a throwaway ``DjangoType`` carrying ``Meta.relation_shapes``.

    Shared by the validation-matrix and consumer-authored tests; every case
    raises at type creation, so the class object never leaks.
    """
    meta_attrs = {"model": model, "fields": fields, "relation_shapes": relation_shapes}
    if relay_node:
        meta_attrs["interfaces"] = (relay.Node,)
    namespace: dict[str, object] = {"Meta": type("Meta", (), meta_attrs)}
    if namespace_extra:
        namespace.update(namespace_extra)
    return type("RelationShapesProbeType", (DjangoType,), namespace)


@pytest.mark.parametrize(
    (
        "model",
        "fields",
        "relation_shapes",
        "relay_node",
        "expected",
    ),
    [
        pytest.param(
            Category,
            ("id", "name", "items"),
            "items",
            True,
            "Meta.relation_shapes must be a dict",
            id="non-dict",
        ),
        pytest.param(
            Category,
            ("id", "name", "items"),
            {1: "both"},
            True,
            "keys must be relation field name strings; got 1",
            id="non-str-key",
        ),
        pytest.param(
            Category,
            ("id", "name", "items"),
            {"items": "paginated"},
            True,
            "got unknown shape 'paginated'; valid shapes are ['both', 'connection', 'list']",
            id="bad-value",
        ),
        pytest.param(
            Category,
            ("id", "name", "items"),
            {"items": ["both"]},
            True,
            "got unknown shape ['both']; valid shapes are ['both', 'connection', 'list']",
            id="unhashable-value",
        ),
        pytest.param(
            Category,
            ("id", "name", "items"),
            {"nope": "both"},
            True,
            "Meta.relation_shapes names unknown fields: ['nope']",
            id="unknown-field",
        ),
        pytest.param(
            Category,
            ("id", "name", "items"),
            {"name": "both"},
            True,
            "names non-relation field 'name'",
            id="non-relation-field",
        ),
        pytest.param(
            Item,
            ("id", "name", "category"),
            {"category": "both"},
            True,
            "names single-valued relation 'category' (forward FK / OneToOne)",
            id="single-valued-relation",
        ),
        pytest.param(
            Patron,
            ("id", "name", "profile"),
            {"profile": "both"},
            True,
            "names single-valued relation 'profile' (reverse OneToOne)",
            id="single-valued-reverse-one-to-one",
        ),
        pytest.param(
            _link_models.LnkPairChild,
            ("id", "name", "parent"),
            {"parent": "both"},
            True,
            "names single-valued relation 'parent' (forward ForeignObject)",
            id="single-valued-foreign-object",
        ),
        pytest.param(
            Category,
            ("id", "name"),
            {"items": "both"},
            True,
            "names fields not in the selected set: ['items']",
            id="excluded-field",
        ),
        pytest.param(
            Category,
            ("id", "name", "items"),
            {"items": "both"},
            False,
            "requires a Relay-Node-shaped type; add `relay.Node` to `Meta.interfaces` "
            "or remove the key.",
            id="non-relay-declaring-type",
        ),
    ],
)
def test_relation_shapes_validation_matrix(
    model: type[models.Model],
    fields: Sequence[str],
    relation_shapes: object,
    *,
    relay_node: bool,
    expected: str,
) -> None:
    """Every illegal ``Meta.relation_shapes`` declaration raises at type creation.

    Spec-032 Decision 7 / Error shapes: shape, key-name, and gate failures all
    surface at type creation (only the target-is-Node-shaped check waits for
    finalization). The non-Relay case asserts the shared Relay-Node-gate
    lead-in with the spec-pinned "or remove the key." tail.
    """
    with pytest.raises(ConfigurationError) as excinfo:
        _declare_relation_shapes_type(model, fields, relation_shapes, relay_node=relay_node)
    assert expected in str(excinfo.value)


def test_relation_shapes_on_consumer_annotated_relation_raises() -> None:
    """An explicit key naming a consumer-ANNOTATED relation raises at type creation.

    Spec-032 Decision 7: the consumer annotation owns the
    field's shape; the silent-accept-then-skip path must not exist. (The
    implicit default still skips consumer-authored relations silently -
    only the explicit key fails loud, whatever that default's value is.)
    """
    with pytest.raises(ConfigurationError) as excinfo:
        _declare_relation_shapes_type(
            Category,
            ("id", "name", "items"),
            {"items": "connection"},
            namespace_extra={"__annotations__": {"items": "list[str]"}},
        )
    message = str(excinfo.value)
    assert "names consumer-authored relation 'items'" in message
    assert "owns that field's shape" in message


def test_relation_shapes_on_consumer_assigned_relation_raises() -> None:
    """An explicit key naming a consumer-ASSIGNED relation raises at type creation.

    The ``strawberry.field(resolver=...)`` corner of the four-corner override
    contract; same overrides-own-the-shape message as the annotation corner.
    """

    def _items_resolver() -> list[str]:
        return []  # Never resolved - the class raises at creation.

    with pytest.raises(ConfigurationError) as excinfo:
        _declare_relation_shapes_type(
            Category,
            ("id", "name", "items"),
            {"items": "connection"},
            namespace_extra={"items": strawberry.field(resolver=_items_resolver)},
        )
    message = str(excinfo.value)
    assert "names consumer-authored relation 'items'" in message
    assert "owns that field's shape" in message


def test_interfaces_is_shipped_not_deferred() -> None:
    """``interfaces`` is a shipped Meta key (in ``ALLOWED_META_KEYS``), not deferred.

    Guards against the prior regression where ``test_meta_rejects_each_deferred_key``
    silently included ``"interfaces"`` and passed for the wrong reason - the
    ``_validate_interfaces`` shape error happens to contain the substring
    ``"interfaces"``, so the deferred-key ``match=`` regex was satisfied by a
    shape-validation message rather than a deferred-key message. The
    ``_validate_interfaces`` spec-015 Decision 4 validator is the full shipped contract.
    """
    assert "interfaces" in ALLOWED_META_KEYS
    assert "interfaces" not in DEFERRED_META_KEYS


def test_select_fields_signature_accepts_validated_specs() -> None:
    """``_select_fields`` consumes the already-normalized specs from ``_ValidatedMeta``.

    The function does not re-run ``_normalize_fields_spec`` /
    ``_normalize_sequence_spec`` (those ran inside ``_validate_meta``) - it
    takes the model plus the two
    validated specs directly. Calling with both specs ``None`` returns every
    Django field; passing a fields tuple narrows the result.
    """
    all_selected = _select_fields(Category, None, None)
    assert {f.name for f in all_selected} >= set(CATEGORY_SCALAR_FIELDS)

    narrowed = _select_fields(Category, ("id", "name"), None)
    assert tuple(f.name for f in narrowed) == ("id", "name")

    excluded = _select_fields(Category, None, ("description",))
    assert "description" not in {f.name for f in excluded}
    assert "name" in {f.name for f in excluded}


def test_meta_filterset_class_rejects_non_filterset_value() -> None:
    """``_validate_filterset_class`` rejects non-``FilterSet`` values."""
    with pytest.raises(ConfigurationError, match="must be a FilterSet subclass"):

        @definition_raises
        class CategoryType(DjangoType):
            class Meta:
                model = Category
                fields = CATEGORY_SCALAR_FIELDS
                filterset_class = object


def test_filterset_and_orderset_meta_validators_ride_validate_set_sidecar() -> None:
    """Both DjangoType sidecar Meta gates share ``_validate_set_sidecar``.

    The wrappers keep the cycle-safe local imports; the subclass check
    and ``must be {article} {Name} subclass`` wording live once in the
    shared helper.
    """
    for fn in (base_mod._validate_filterset_class, base_mod._validate_orderset_class):
        assert "_validate_set_sidecar" in fn.__code__.co_names
    src_filter = inspect.getsource(base_mod._validate_filterset_class)
    src_order = inspect.getsource(base_mod._validate_orderset_class)
    assert "from django_strawberry_framework.filters.sets import FilterSet" in src_filter
    assert "from django_strawberry_framework.orders.sets import OrderSet" in src_order
    assert "FilterSet" not in vars(base_mod)
    assert "OrderSet" not in vars(base_mod)


def test_meta_filterset_class_accepts_filterset_subclass() -> None:
    """A real ``FilterSet`` subclass is accepted and stored on the definition."""

    class CategoryFilter(FilterSet):
        class Meta:
            model = Category
            fields = {"name": ["exact"]}

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = CATEGORY_SCALAR_FIELDS
            filterset_class = CategoryFilter

    definition = CategoryType.__django_strawberry_definition__
    assert definition.filterset_class is CategoryFilter


def test_meta_connection_in_allowed_meta_keys() -> None:
    """``Meta.connection`` ships in spec-030 - a net-new ALLOWED key.

    Net-new ALLOWED, NOT a DEFERRED_META_KEYS promotion (spec-030 Decision 8;
    mirrors the filterset/orderset precedent).
    """
    assert "connection" in ALLOWED_META_KEYS
    assert "connection" not in DEFERRED_META_KEYS


def test_meta_connection_non_dict_raises() -> None:
    """``Meta.connection`` must be a dict; a non-dict value raises ``ConfigurationError``."""
    with pytest.raises(ConfigurationError, match="must be a dict"):

        @definition_raises
        class CategoryType(DjangoType):
            class Meta:
                model = Category
                fields = CATEGORY_SCALAR_FIELDS
                interfaces = (relay.Node,)
                connection = "nope"


def test_meta_connection_unknown_subkey_raises() -> None:
    """An unrecognized ``Meta.connection`` sub-key raises (typo guard)."""
    with pytest.raises(ConfigurationError, match="unknown sub-keys"):

        @definition_raises
        class CategoryType(DjangoType):
            class Meta:
                model = Category
                fields = CATEGORY_SCALAR_FIELDS
                interfaces = (relay.Node,)
                connection = {"total_count": True, "bogus": 1}


def test_meta_connection_non_bool_total_count_raises() -> None:
    """``Meta.connection['total_count']`` must be a bool; a non-bool raises."""
    with pytest.raises(ConfigurationError, match="must be a bool"):

        @definition_raises
        class CategoryType(DjangoType):
            class Meta:
                model = Category
                fields = CATEGORY_SCALAR_FIELDS
                interfaces = (relay.Node,)
                connection = {"total_count": "yes"}


def test_meta_connection_non_relay_type_raises() -> None:
    """``Meta.connection`` on a type whose ``interfaces`` omits ``relay.Node`` raises."""
    with pytest.raises(ConfigurationError, match=r"relay\.Node"):

        @definition_raises
        class CategoryType(DjangoType):
            class Meta:
                model = Category
                fields = CATEGORY_SCALAR_FIELDS
                connection = {"total_count": True}


def test_meta_connection_accepts_direct_relay_node_inheritance() -> None:
    """``Meta.connection`` opt-in works on a direct ``relay.Node`` subclass.

    ``spec-030-connection_field-0_0_9``: the Relay-shape gate for
    ``Meta.connection`` runs in ``__init_subclass__`` using the canonical
    ``_is_relay_shaped`` predicate, so a direct
    ``class Foo(DjangoType, relay.Node)`` - Relay-shaped WITHOUT
    ``Meta.interfaces`` - can opt into ``total_count``, matching the
    ``DjangoConnectionField`` field guard. One consistent definition of
    "Relay-shaped" across both surfaces.
    """

    class DirectCountNode(DjangoType, relay.Node):
        class Meta:
            model = Category
            fields = CATEGORY_SCALAR_FIELDS
            connection = {"total_count": True}

    definition = DirectCountNode.__django_strawberry_definition__
    # Relay-shaped via direct inheritance, not the Meta-tuple.
    assert relay.Node not in definition.interfaces
    assert definition.connection == {"total_count": True}


def test_meta_connection_stored_on_definition() -> None:
    """The normalized ``Meta.connection`` value lands on ``definition.connection``."""

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = CATEGORY_SCALAR_FIELDS
            interfaces = (relay.Node,)
            connection = {"total_count": True}

    definition = CategoryType.__django_strawberry_definition__
    assert definition.connection == {"total_count": True}


def test_meta_connection_is_snapshotted_on_definition() -> None:
    """Mutating the consumer's config dict cannot rewrite registered type metadata."""
    connection = {"total_count": True}

    meta_cls = type(
        "Meta",
        (),
        {
            "model": Category,
            "fields": CATEGORY_SCALAR_FIELDS,
            "interfaces": (relay.Node,),
            "connection": connection,
        },
    )
    CategoryType = type("CategoryType", (DjangoType,), {"Meta": meta_cls})

    connection["total_count"] = False
    definition = CategoryType.__django_strawberry_definition__
    assert definition.connection == {"total_count": True}
    assert definition.connection is not connection


def test_meta_connection_absent_leaves_definition_none() -> None:
    """A type without ``Meta.connection`` leaves ``definition.connection`` at its ``None`` default."""

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = CATEGORY_SCALAR_FIELDS
            interfaces = (relay.Node,)

    definition = CategoryType.__django_strawberry_definition__
    assert definition.connection is None


# ---------------------------------------------------------------------------
# Meta.globalid_strategy + RELAY_GLOBALID_STRATEGY precedence (spec-031)
# ---------------------------------------------------------------------------


def test_meta_globalid_strategy_in_allowed_meta_keys() -> None:
    """``Meta.globalid_strategy`` ships in spec-031 - a net-new ALLOWED key.

    Net-new ALLOWED, NOT a ``DEFERRED_META_KEYS`` promotion (spec-031 Decision 6;
    mirrors the connection / filterset / orderset precedent).
    """
    assert "globalid_strategy" in ALLOWED_META_KEYS
    assert "globalid_strategy" not in DEFERRED_META_KEYS


def test_meta_globalid_strategy_unknown_string_raises() -> None:
    """A typo'd strategy string raises ``ConfigurationError`` (typo guard)."""
    with pytest.raises(ConfigurationError, match="unknown strategy"):

        @definition_raises
        class CategoryType(DjangoType):
            class Meta:
                model = Category
                fields = CATEGORY_SCALAR_FIELDS
                interfaces = (relay.Node,)
                globalid_strategy = "modle"


def test_meta_globalid_strategy_non_relay_type_raises() -> None:
    """``Meta.globalid_strategy`` on a type whose ``interfaces`` omits ``relay.Node`` raises."""
    with pytest.raises(ConfigurationError, match=r"relay\.Node"):

        @definition_raises
        class CategoryType(DjangoType):
            class Meta:
                model = Category
                fields = CATEGORY_SCALAR_FIELDS
                globalid_strategy = "model"


def test_meta_globalid_strategy_wrong_type_raises() -> None:
    """A non-string, non-callable value (e.g. ``42``) raises ``ConfigurationError``."""
    with pytest.raises(ConfigurationError, match="must be one of"):

        @definition_raises
        class CategoryType(DjangoType):
            class Meta:
                model = Category
                fields = CATEGORY_SCALAR_FIELDS
                interfaces = (relay.Node,)
                globalid_strategy = 42


def test_meta_globalid_strategy_callable_accepted_and_stored() -> None:
    """A well-formed sync three-arg encoder validates and is stored on the definition."""

    def encode(_type_cls: type[DjangoType], _model: type[models.Model], _root: object) -> str:
        return "custom"

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = CATEGORY_SCALAR_FIELDS
            interfaces = (relay.Node,)
            globalid_strategy = encode

    definition = CategoryType.__django_strawberry_definition__
    assert definition.globalid_strategy is encode


def test_meta_globalid_strategy_callable_wrong_arity_raises() -> None:
    """A wrong-arity encoder is rejected at type creation (the ``inspect.signature`` check)."""

    def encode(_type_cls: type[DjangoType], _model: type[models.Model]) -> str:
        return "custom"

    with pytest.raises(ConfigurationError, match=r"\(type_cls, model, root\)"):

        @definition_raises
        class CategoryType(DjangoType):
            class Meta:
                model = Category
                fields = CATEGORY_SCALAR_FIELDS
                interfaces = (relay.Node,)
                globalid_strategy = encode


def test_meta_globalid_strategy_callable_old_four_arg_signature_rejected() -> None:
    """The pre-1.0 4-arg ``(type_cls, model, root, info)`` encoder is now rejected.

    ``info`` was dropped from the callable-encoder contract; a callable that still
    requires the old fourth positional cannot bind the 3-arg probe, so it fails
    loud at type creation naming the new ``(type_cls, model, root)`` shape rather
    than raising an opaque ``TypeError`` at the first encode.
    """

    def encode(
        _type_cls: type[DjangoType],
        _model: type[models.Model],
        _root: object,
        _info: object,
    ) -> str:
        return "custom"

    with pytest.raises(ConfigurationError, match=r"\(type_cls, model, root\)"):

        @definition_raises
        class CategoryType(DjangoType):
            class Meta:
                model = Category
                fields = CATEGORY_SCALAR_FIELDS
                interfaces = (relay.Node,)
                globalid_strategy = encode


def test_meta_globalid_strategy_async_callable_raises() -> None:
    """An ``async def`` encoder is rejected at type creation (the sync-ness check)."""

    async def encode(
        _type_cls: type[DjangoType],
        _model: type[models.Model],
        _root: object,
    ) -> str:
        return "custom"

    with pytest.raises(ConfigurationError, match="must be sync"):

        @definition_raises
        class CategoryType(DjangoType):
            class Meta:
                model = Category
                fields = CATEGORY_SCALAR_FIELDS
                interfaces = (relay.Node,)
                globalid_strategy = encode


def test_meta_globalid_strategy_async_callable_object_raises() -> None:
    """A callable *instance* whose ``__call__`` is ``async def`` is rejected too.

    ``inspect.iscoroutinefunction`` returns ``False`` for the instance itself, so
    without the ``__call__`` arm of the sync-ness check this object would survive
    validation and only blow up at first encode (a coroutine return + an unawaited
    -coroutine warning) instead of failing loud at type creation.
    """

    class Encoder:
        async def __call__(
            self,
            _type_cls: type[DjangoType],
            _model: type[models.Model],
            _root: object,
        ) -> str:
            return "custom.label"

    with pytest.raises(ConfigurationError, match="must be sync"):

        @definition_raises
        class CategoryType(DjangoType):
            class Meta:
                model = Category
                fields = CATEGORY_SCALAR_FIELDS
                interfaces = (relay.Node,)
                globalid_strategy = Encoder()


def test_meta_globalid_strategy_partial_wrapped_async_callable_raises() -> None:
    """A ``functools.partial`` around an async callable instance is rejected too.

    ``inspect.iscoroutinefunction`` only unwraps a partial whose ``.func`` is an
    ``async def`` function - NOT a partial around an async callable *instance*, so
    both the partial and its ``__call__`` read as sync. The validator unwraps
    ``partial.func`` before the sync-ness check, so it fails loud at type creation
    instead of leaking a coroutine at the first encode.
    """

    class Encoder:
        async def __call__(
            self,
            _type_cls: type[DjangoType],
            _model: type[models.Model],
            _root: object,
        ) -> str:
            return "custom.label"

    with pytest.raises(ConfigurationError, match="must be sync"):

        @definition_raises
        class CategoryType(DjangoType):
            class Meta:
                model = Category
                fields = CATEGORY_SCALAR_FIELDS
                interfaces = (relay.Node,)
                globalid_strategy = functools.partial(Encoder())


def test_meta_globalid_strategy_stored_on_definition() -> None:
    """The normalized string strategy lands on ``definition.globalid_strategy``."""

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = CATEGORY_SCALAR_FIELDS
            interfaces = (relay.Node,)
            globalid_strategy = "model"

    definition = CategoryType.__django_strawberry_definition__
    assert definition.globalid_strategy == "model"


def test_meta_globalid_strategy_absent_leaves_definition_none() -> None:
    """A Relay-Node type without the key leaves the raw slot at its ``None`` default."""

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = CATEGORY_SCALAR_FIELDS
            interfaces = (relay.Node,)

    definition = CategoryType.__django_strawberry_definition__
    assert definition.globalid_strategy is None


def test_resolve_globalid_strategy_precedence(settings: pytest_django.Settings) -> None:
    """``_resolve_globalid_strategy`` is pure precedence: Meta -> snapshot -> ``"model"``.

    The resolver no longer reads or validates the setting - it takes the
    pre-validated snapshot as an argument. ``_validated_globalid_setting`` owns
    the read + validation, including the unknown-setting failure whose message
    names ``RELAY_GLOBALID_STRATEGY`` (the setting framing, distinct from the
    type-named ``Meta`` framing).
    """

    class MetaWinsType(DjangoType):
        class Meta:
            model = Category
            fields = CATEGORY_SCALAR_FIELDS
            interfaces = (relay.Node,)
            globalid_strategy = "type"

    class NoMetaType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")
            interfaces = (relay.Node,)

    meta_def = MetaWinsType.__django_strawberry_definition__
    no_meta_def = NoMetaType.__django_strawberry_definition__

    # Tier 1: Meta override beats the snapshot.
    assert _resolve_globalid_strategy(meta_def, "type+model") == "type"

    # Tier 2: the snapshot beats the package default.
    assert _resolve_globalid_strategy(no_meta_def, "type") == "type"

    # Tier 3: no Meta + no snapshot (None) -> the "model" package default.
    assert _resolve_globalid_strategy(no_meta_def, None) == "model"

    # ``_validated_globalid_setting`` reads + validates the setting.
    settings.DJANGO_STRAWBERRY_FRAMEWORK = {"RELAY_GLOBALID_STRATEGY": "type"}
    assert _validated_globalid_setting() == "type"
    settings.DJANGO_STRAWBERRY_FRAMEWORK = {}
    assert _validated_globalid_setting() is None

    # Unknown setting value -> ConfigurationError naming the setting.
    settings.DJANGO_STRAWBERRY_FRAMEWORK = {"RELAY_GLOBALID_STRATEGY": "nonsense"}
    with pytest.raises(ConfigurationError, match="RELAY_GLOBALID_STRATEGY"):
        _validated_globalid_setting()


def test_meta_rejects_unknown_key() -> None:
    """Typo guard: keys outside the allowed/deferred sets raise."""
    with pytest.raises(ConfigurationError, match="Unknown Meta keys"):

        @definition_raises
        class T(DjangoType):
            class Meta:
                model = Category
                fields = CATEGORY_SCALAR_FIELDS
                bogus_key = "value"


def test_meta_fields_unknown_name_raises() -> None:
    """A typo in ``Meta.fields`` raises ``ConfigurationError`` rather than silently dropping."""
    with pytest.raises(ConfigurationError, match="unknown fields"):

        @definition_raises
        class T(DjangoType):
            class Meta:
                model = Category
                fields = ("id", "nmae")  # typo: "nmae" instead of "name"


def test_meta_fields_unknown_name_includes_model_and_available() -> None:
    """The error names the model and lists available fields so the typo is obvious."""
    with pytest.raises(ConfigurationError) as exc_info:

        @definition_raises
        class T(DjangoType):
            class Meta:
                model = Category
                fields = ("nope",)

    msg = str(exc_info.value)
    assert "Category.Meta.fields" in msg
    assert "nope" in msg
    # Mentions some real fields so the consumer sees the available surface.
    assert "name" in msg


def test_meta_exclude_unknown_name_raises() -> None:
    """A typo in ``Meta.exclude`` raises rather than silently keeping the field."""
    with pytest.raises(ConfigurationError, match="unknown fields"):

        @definition_raises
        class T(DjangoType):
            class Meta:
                model = Category
                exclude = ("descriptoin",)  # typo


def test_meta_optimizer_hints_for_excluded_field_raises() -> None:
    """A hint for a real Django field that is *excluded* from the type raises.

    Without this check the consumer's optimization intent is
    silently dead, because the
    walker never visits an excluded field.
    """
    with pytest.raises(ConfigurationError, match="optimizer_hints names unknown fields"):

        @definition_raises
        class T(DjangoType):
            class Meta:
                model = Category
                fields = ("id", "name")
                optimizer_hints = {"items": OptimizerHint.prefetch_related()}


def test_meta_optimizer_hints_for_selected_scalar_field_raises() -> None:
    with pytest.raises(ConfigurationError, match="optimizer_hints names unknown fields"):

        @definition_raises
        class T(DjangoType):
            class Meta:
                model = Category
                fields = ("id", "name")
                optimizer_hints = {"name": OptimizerHint.SKIP}


def test_meta_optimizer_hints_with_empty_field_selection_raises_configuration_error() -> None:
    """``optimizer_hints`` on an exclude-all selection raises ``ConfigurationError``, not ``IndexError``.

    Earlier shapes inferred the model from ``fields[0].model``; when
    ``Meta.exclude`` covered every concrete + relation field the resulting
    empty ``fields`` tuple ``IndexError``'d before the consumer could see a
    typed error. The fix threads ``meta.model`` through explicitly so the
    selected-relation gate fires with a normal ``ConfigurationError``.
    """
    with pytest.raises(ConfigurationError, match="optimizer_hints names unknown fields"):

        @definition_raises
        class T(DjangoType):
            class Meta:
                model = Category
                exclude = (
                    "id",
                    "name",
                    "description",
                    "is_private",
                    "created_date",
                    "updated_date",
                    "items",
                )
                optimizer_hints = {"items": OptimizerHint.prefetch_related()}


# ---------------------------------------------------------------------------
# Meta.primary recognition
# ---------------------------------------------------------------------------


def test_meta_primary_true_registers_type_as_primary() -> None:
    """``Meta.primary = True`` makes ``registry.primary_for(model)`` return the type."""

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")
            primary = True

    assert registry.primary_for(Item) is ItemType


def test_meta_primary_false_does_not_register_primary() -> None:
    """An explicit ``Meta.primary = False`` is treated identically to absent."""

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")
            primary = False

    assert registry.primary_for(Item) is None
    # Single-type backward-compat: ``get()`` still returns the lone type even
    # without an explicit primary flag (Decision 4).
    assert registry.get(Item) is ItemType


def test_meta_primary_absent_does_not_register_primary() -> None:
    """No ``Meta.primary`` key is the default ``False`` path."""

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    assert registry.primary_for(Item) is None
    assert registry.get(Item) is ItemType


@pytest.mark.parametrize(
    "bad",
    [
        "yes",
        1,
        0,
        [],
        None,
        1.0,
    ],
)
def test_meta_primary_non_bool_raises_configuration_error(bad: object) -> None:
    """``Meta.primary`` must be a ``bool``; any other shape raises.

    ``isinstance(1, bool)`` is ``False`` (``bool`` is a subclass of ``int``,
    not the other way around) so the guard correctly rejects the ``1``/``0``
    integer trap that would otherwise pass a duck-typed bool check.
    """
    with pytest.raises(ConfigurationError, match="must be a bool"):

        @definition_raises
        class T(DjangoType):
            class Meta:
                model = Item
                fields = ("id", "name")
                primary = bad


def test_meta_primary_propagates_to_definition() -> None:
    """The ``primary`` flag is stored on ``DjangoTypeDefinition`` for introspection."""

    class ItemTypePrimary(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")
            primary = True

    definition = registry.get_definition(ItemTypePrimary)
    assert definition is not None
    assert definition.primary is True


def test_meta_primary_absent_definition_primary_defaults_false() -> None:
    """Absent ``Meta.primary`` lands ``False`` on the dataclass default."""

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    definition = registry.get_definition(ItemType)
    assert definition is not None
    assert definition.primary is False


def test_two_types_same_model_one_primary_both_register_successfully() -> None:
    """Two ``DjangoType`` subclasses on one model, exactly one primary, both register."""

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    class AdminItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")
            primary = True

    assert registry.types_for(Item) == (ItemType, AdminItemType)
    assert registry.primary_for(Item) is AdminItemType
    # ``get()`` returns the declared primary even though ``ItemType`` registered
    # first (Decision 4: primary wins over registration order).
    assert registry.get(Item) is AdminItemType


def test_two_primary_types_same_model_raises() -> None:
    """Two ``Meta.primary = True`` declarations for the same model raise at class creation."""

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")
            primary = True

    assert registry.get(Item) is ItemType

    with pytest.raises(
        ConfigurationError,
        match=r"Cannot register AdminItemType as primary for Item;.*ItemType is already the primary type",
    ):

        @definition_raises
        class AdminItemType(DjangoType):
            class Meta:
                model = Item
                fields = ("id", "name")
                primary = True


# ---------------------------------------------------------------------------
# Scalar synthesis
# ---------------------------------------------------------------------------


def test_scalar_mapping_against_category_textfields_booleanfields_datetimefields() -> None:
    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = CATEGORY_SCALAR_FIELDS

    a = CategoryType.__annotations__
    assert a["id"] is int
    assert a["name"] is str
    assert a["description"] is str
    assert a["is_private"] is bool
    assert a["created_date"] is datetime.datetime
    assert a["updated_date"] is datetime.datetime


def test_meta_fields_explicit_list_filters_concrete_fields() -> None:
    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    assert set(CategoryType.__annotations__) == {"id", "name"}


def test_meta_exclude_filters_concrete_fields() -> None:
    """Excluding scalars + reverse rels yields a clean scalar-only annotation set."""

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            # Exclude scalars under test plus the reverse rels (Item /
            # Property are unregistered in this test, so leaving them
            # selected would trip ``convert_relation``).
            exclude = (
                "description",
                "updated_date",
                "items",
                "properties",
            )

    a = CategoryType.__annotations__
    assert "description" not in a
    assert "updated_date" not in a
    assert {
        "id",
        "name",
        "is_private",
        "created_date",
    } <= set(a)


# ---------------------------------------------------------------------------
# Strawberry finalization
# ---------------------------------------------------------------------------


def test_category_type_is_a_strawberry_type() -> None:
    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = CATEGORY_SCALAR_FIELDS

    finalize_django_types()
    assert hasattr(CategoryType, "__strawberry_definition__")
    assert get_object_definition(CategoryType, strict=True).name == "CategoryType"


def test_meta_name_overrides_graphql_type_name() -> None:
    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = CATEGORY_SCALAR_FIELDS
            name = "Category"

    finalize_django_types()

    assert get_object_definition(CategoryType, strict=True).name == "Category"


@pytest.mark.parametrize("description", [5, b"bytes", ["a"]])
def test_meta_description_rejects_a_non_string_at_type_creation(description: object) -> None:
    """A non-string ``Meta.description`` is a typed error, not a schema-build ``TypeError``."""
    meta_cls = type(
        "Meta",
        (),
        {"model": Category, "fields": CATEGORY_SCALAR_FIELDS, "description": description},
    )

    with pytest.raises(
        ConfigurationError,
        match=r"Meta\.description must be a string or a lazy translation string",
    ):
        type("BadDescriptionType", (DjangoType,), {"Meta": meta_cls})


def test_meta_description_lazy_translation_renders_to_str_at_finalize() -> None:
    """A ``gettext_lazy`` description stays lazy on the definition and finalizes as plain text."""

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = CATEGORY_SCALAR_FIELDS
            description = gettext_lazy("A Faker provider.")

    definition = registry.get_definition(CategoryType)
    assert definition is not None
    assert isinstance(definition.description, Promise)

    finalize_django_types()

    description = get_object_definition(CategoryType, strict=True).description
    assert type(description) is str
    assert description == "A Faker provider."


def test_meta_description_str_subclass_keeps_its_plain_text() -> None:
    """A ``str`` subclass's own ``__str__`` never runs; the text it holds is the description."""

    class LoudText(str):
        @override
        def __str__(self) -> str:
            return "overridden"

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = CATEGORY_SCALAR_FIELDS
            description = LoudText("A Faker provider.")

    definition = registry.get_definition(CategoryType)
    assert definition is not None
    assert type(definition.description) is str
    assert definition.description == "A Faker provider."


def test_meta_description_threads_through_to_strawberry() -> None:
    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = CATEGORY_SCALAR_FIELDS
            description = "A Faker provider."

    finalize_django_types()

    assert get_object_definition(CategoryType, strict=True).description == "A Faker provider."


# ---------------------------------------------------------------------------
# Default get_queryset is identity
# ---------------------------------------------------------------------------


def test_get_queryset_default_returns_input_unchanged() -> None:
    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = CATEGORY_SCALAR_FIELDS

    qs = Category.objects.all()
    assert CategoryType.get_queryset(qs, info=None) is qs


def test_has_custom_get_queryset_false_when_using_default() -> None:
    """A subclass that does not override ``get_queryset`` reports False."""

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = CATEGORY_SCALAR_FIELDS

    assert CategoryType._is_default_get_queryset is True
    assert CategoryType.has_custom_get_queryset() is False


def test_has_custom_get_queryset_true_when_overridden() -> None:
    """A subclass that overrides ``get_queryset`` flips the sentinel and reports True."""

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = CATEGORY_SCALAR_FIELDS

        @classmethod
        @override
        def get_queryset(
            cls,
            queryset: models.QuerySet[Category],
            info: object,
            **kwargs: object,
        ) -> models.QuerySet[Category]:
            return queryset.filter(is_private=False)

    assert CategoryType._is_default_get_queryset is False
    assert CategoryType.has_custom_get_queryset() is True


def test_has_custom_get_queryset_inherits_through_intermediate_base() -> None:
    """A subclass without its own ``get_queryset`` whose parent overrides one still reports True.

    The sentinel sits on the class itself - Python's normal attribute
    lookup walks the MRO, so a child that does not redeclare
    ``get_queryset`` inherits the parent's ``False`` flag through the
    class hierarchy without us writing any MRO-walking code.
    """

    class BaseCategoryType(DjangoType):
        class Meta:
            model = Category
            fields = CATEGORY_SCALAR_FIELDS

        @classmethod
        @override
        def get_queryset(
            cls,
            queryset: models.QuerySet[Category],
            info: object,
            **kwargs: object,
        ) -> models.QuerySet[Category]:
            return queryset.filter(is_private=False)

    # Drop the registry collision so we can subclass cleanly.
    registry.clear()

    class ChildCategoryType(BaseCategoryType):
        # basedpyright: DjangoType reads only the class's own ``Meta`` (``cls.__dict__``); the
        # child declares a fresh one, never a subclass of the parent's
        class Meta:  # pyright: ignore[reportIncompatibleVariableOverride]
            model = Category
            fields = CATEGORY_SCALAR_FIELDS

    assert ChildCategoryType.has_custom_get_queryset() is True


def test_has_custom_get_queryset_inherits_through_abstract_base_without_meta() -> None:
    """A concrete subclass inherits override-detection from an abstract base that has no ``Meta``.

    The abstract-shared-base pattern is documented as supported - the
    ``__init_subclass__`` ``meta is None`` early return notes
    "intermediate abstract subclasses without Meta are allowed". For
    that pattern to work end-to-end with the optimizer's
    downgrade-to-Prefetch rule, the sentinel flip must run regardless
    of whether the abstract base declares its own ``Meta``. When the
    flip sat after the ``meta is None`` early return instead, an
    abstract base that overrode ``get_queryset`` without Meta never
    flipped the flag, and concrete subclasses inheriting from it
    silently reported ``has_custom_get_queryset() is False``.
    """

    class TenantScopedType(DjangoType):
        """Abstract base - no Meta, but defines ``get_queryset``."""

        @classmethod
        @override
        def get_queryset(
            cls,
            queryset: models.QuerySet[models.Model],
            info: object,
            **kwargs: object,
        ) -> models.QuerySet[models.Model]:
            return queryset.filter(is_private=False)

    # The abstract base flipped its own sentinel even without Meta.
    assert TenantScopedType._is_default_get_queryset is False

    class CategoryType(TenantScopedType):
        class Meta:
            model = Category
            fields = CATEGORY_SCALAR_FIELDS

    # Concrete subclass does not redefine ``get_queryset`` itself, but
    # inherits the flipped sentinel via normal attribute lookup.
    assert "get_queryset" not in CategoryType.__dict__
    assert CategoryType.has_custom_get_queryset() is True


# ---------------------------------------------------------------------------
# convert_scalar direct unit coverage
# ---------------------------------------------------------------------------


def test_convert_scalar_raises_on_unsupported_field_type(monkeypatch: pytest.MonkeyPatch) -> None:
    """Unsupported field types fail loudly with a message naming the field."""
    monkeypatch.delitem(converters.SCALAR_MAP, models.TextField)
    name_field = Category._meta.get_field("name")
    assert isinstance(name_field, models.Field)
    with pytest.raises(ConfigurationError, match="Unsupported Django field type"):
        convert_scalar(name_field, "CategoryType")


# ---------------------------------------------------------------------------
# Relation conversion via _build_annotations
# ---------------------------------------------------------------------------


def test_relation_fk_to_target_djangotype() -> None:
    """Forward FK on Item maps to the registered ``CategoryType`` post-finalize."""

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = CATEGORY_SCALAR_FIELDS

    class ItemType(DjangoType):
        class Meta:
            model = Item
            # Skip ``entries`` reverse rel - Entry is unregistered in this test.
            fields = ("id", "name", "category")

    finalize_django_types()
    assert ItemType.__annotations__["category"] is CategoryType


def test_relation_reverse_fk_returns_list() -> None:
    """Reverse FK on Category maps to ``list[ItemType]`` and ``list[PropertyType]``."""

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    class PropertyType(DjangoType):
        class Meta:
            model = Property
            fields = ("id", "name")

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = (
                "id",
                "name",
                "items",
                "properties",
            )

    finalize_django_types()
    a = CategoryType.__annotations__
    assert a["items"] == list[ItemType]
    assert a["properties"] == list[PropertyType]


def test_relation_meta_default_when_neither_fields_nor_exclude_set() -> None:
    """Omitting ``fields``/``exclude`` defaults to ``__all__`` and includes relations."""

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name")

    class PropertyType(DjangoType):
        class Meta:
            model = Property
            fields = ("id", "name")

    class CategoryType(DjangoType):
        class Meta:
            model = Category

    finalize_django_types()
    a = CategoryType.__annotations__
    assert {
        "id",
        "name",
        "items",
        "properties",
    } <= set(a)
    assert a["items"] == list[ItemType]
    assert a["properties"] == list[PropertyType]


def test_relation_unregistered_target_raises() -> None:
    """Referencing an unregistered relation target raises during finalization."""

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    assert ItemType.__annotations__["category"] is PendingRelationAnnotation
    assert "finalize_django_types()" in repr(PendingRelationAnnotation)
    with pytest.raises(ConfigurationError) as exc_info:
        finalize_django_types()

    msg = str(exc_info.value)
    assert "Cannot finalize Django types" in msg
    assert "Item.category -> Category" in msg
    assert "no registered DjangoType" in msg


def test_relation_full_chain_when_all_targets_registered() -> None:
    """Every fakeshop relation resolves cleanly when types are declared in order."""

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            # Exclude reverse rels; Item / Property come next.
            fields = CATEGORY_SCALAR_FIELDS

    class PropertyType(DjangoType):
        class Meta:
            model = Property
            # category FK + scalars; entries reverse rel waits for EntryType.
            fields = ("id", "name", "category")

    class ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id", "name", "category")

    class EntryType(DjangoType):
        class Meta:
            model = Entry
            fields = (
                "id",
                "value",
                "property",
                "item",
            )

    finalize_django_types()
    assert PropertyType.__annotations__["category"] is CategoryType
    assert ItemType.__annotations__["category"] is CategoryType
    assert EntryType.__annotations__["property"] is PropertyType
    assert EntryType.__annotations__["item"] is ItemType


def test_resolved_relation_annotation_nullable_fk_widens_to_optional(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Nullable forward FK widens to ``T | None``.

    No fakeshop FK declares ``null=True``, so monkeypatch the Item.category
    field for the duration of this test. ``resolved_relation_annotation``
    reads ``field.null`` via ``FieldMeta.from_django_field``; the widening
    branch is exercised without the rest of the pipeline.
    """

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = CATEGORY_SCALAR_FIELDS

    item_category = Item._meta.get_field("category")
    monkeypatch.setattr(item_category, "null", True)
    annotation = resolved_relation_annotation(item_category, CategoryType)
    assert annotation == (CategoryType | None)


# ---------------------------------------------------------------------------
# Meta.nullable_overrides / Meta.required_overrides (spec-029)
#
# ``_OverrideOwner`` stays synthetic: the override tests need a non-null text
# column, a nullable one, a non-null choices column, a nullable choices column
# and a relation on ONE model, so a single ``Meta.nullable_overrides`` /
# ``Meta.required_overrides`` declaration can name a sibling of each kind, and
# no fakeshop model carries a nullable choices column (all four fakeshop choices
# columns are non-null). It drives the choice-enum arm of
# ``django_strawberry_framework/types/base.py::_build_annotations`` through
# ``Meta`` in both directions.
# ``text_value`` is a non-null column, ``note`` a nullable one (the two
# directions the spec test plan names); ``partner`` is a relation field for the
# non-relation-scope reject. ``_unique_override_app_label`` namespaces each
# synthetic model so Django's app registry does not collide across tests.
# ---------------------------------------------------------------------------

_override_app_label_counter = itertools.count(1)


def _unique_override_app_label() -> str:
    """Return a unique ``app_label`` per call for synthetic override models."""
    return f"test_overrides__{next(_override_app_label_counter)}"


_OVERRIDE_STATUS_CHOICES = (("active", "Active"), ("archived", "Archived"))


def _make_override_model() -> type[models.Model]:
    """Return a synthetic model with a non-null + a nullable scalar, a relation, and choices.

    The two choice columns (``status`` non-null, ``nullable_status`` null=True)
    exist so an override can be driven against a choice-backed field whose
    generated GraphQL type is an enum, exercising the "flip a choice field's
    enum nullability for free" path (Decision 9) through the public ``Meta``
    surface rather than only at the ``convert_scalar`` seam.
    """

    class _OverrideOwner(models.Model):
        text_value: "models.TextField[str | Combinable, str]" = models.TextField()
        note: "models.TextField[str | Combinable | None, str | None]" = models.TextField(null=True)  # noqa: DJ001 - NULL is the fixture input
        status: "models.TextField[str | Combinable, str]" = models.TextField(
            choices=_OVERRIDE_STATUS_CHOICES,
        )
        nullable_status: "models.TextField[str | Combinable | None, str | None]" = (
            models.TextField(choices=_OVERRIDE_STATUS_CHOICES, null=True)  # noqa: DJ001 - NULL is the fixture input
        )
        partner: "models.ForeignKey[_OverrideOwner | Combinable | None, _OverrideOwner | None]" = (
            models.ForeignKey(
                "self",
                null=True,
                on_delete=models.SET_NULL,
                related_name="+",
            )
        )

        class Meta:
            managed = False
            app_label = _unique_override_app_label()

    return _OverrideOwner


def _make_override_type(
    model: type[models.Model],
    *,
    namespace: dict[str, object] | None = None,
    **meta_attrs: object,
) -> type[DjangoType]:
    """Build an ``OverrideType`` subclass for ``model`` with the given Meta attrs.

    Uses ``type(...)`` construction (mirroring ``test_meta_rejects_each_deferred_key``)
    so the synthetic ``model`` local is passed by value rather than referenced from
    a nested ``class Meta`` body (class bodies do not close over function locals).
    ``namespace`` carries consumer-authored annotations / assignments onto the type.
    """
    meta_cls = type("Meta", (), {"model": model, **meta_attrs})
    return type("OverrideType", (DjangoType,), {"Meta": meta_cls, **(namespace or {})})


def test_nullable_overrides_in_allowed_meta_keys() -> None:
    """Both override keys are net-new ALLOWED keys, NOT deferred (Decision 6)."""
    assert "nullable_overrides" in ALLOWED_META_KEYS
    assert "required_overrides" in ALLOWED_META_KEYS
    assert "nullable_overrides" not in DEFERRED_META_KEYS
    assert "required_overrides" not in DEFERRED_META_KEYS


def test_nullable_override_flips_annotation() -> None:
    """``nullable_overrides`` widens a non-null column; ``required_overrides`` narrows a nullable one."""
    override_type = _make_override_type(
        _make_override_model(),
        fields=("id", "text_value", "note"),
        nullable_overrides=("text_value",),
        required_overrides=("note",),
    )

    # text_value is NOT NULL natively (str); the override widens it to str | None.
    assert override_type.__annotations__["text_value"] == (str | None)
    # note is null=True natively (str | None); the override narrows it to bare str.
    assert override_type.__annotations__["note"] is str


def test_override_flips_choice_field_enum_nullability() -> None:
    """An override flips a choice field's generated ENUM nullability through Meta (Decision 9).

    Earns the CHANGELOG "flips a choice field's generated enum nullability for
    free" claim end-to-end through ``Meta.nullable_overrides`` /
    ``Meta.required_overrides`` - not only at the ``convert_scalar`` seam
    (``test_converters.py::test_convert_scalar_force_nullable_on_choice_field``).
    Widening sits AFTER choice substitution, so the non-null ``status`` column
    widens to ``StatusEnum | None`` and the nullable ``nullable_status`` column
    narrows to a bare enum - the enum members are untouched in both directions.
    """
    model = _make_override_model()
    override_type = _make_override_type(
        model,
        fields=("id", "status", "nullable_status"),
        nullable_overrides=("status",),
        required_overrides=("nullable_status",),
    )

    status_enum = registry.get_enum(model, "status")
    nullable_status_enum = registry.get_enum(model, "nullable_status")
    assert status_enum is not None
    assert nullable_status_enum is not None
    # Non-null choice widened to ``Enum | None`` (the generated enum is preserved).
    assert override_type.__annotations__["status"] == (status_enum | None)
    # Nullable choice narrowed to a bare ``Enum``.
    assert override_type.__annotations__["nullable_status"] is nullable_status_enum


def test_override_unknown_field_raises() -> None:
    """A name not on the model raises ``ConfigurationError`` (unknown-field path)."""
    with pytest.raises(ConfigurationError, match="unknown fields"):
        _make_override_type(
            _make_override_model(),
            fields=("id", "text_value"),
            nullable_overrides=("does_not_exist",),
        )


def test_override_excluded_field_raises() -> None:
    """A name excluded from the selected set raises - distinct from unknown (Decision 8 rule 2)."""
    with pytest.raises(ConfigurationError, match="not in the selected set"):
        # ``note`` exists on the model but is excluded from the type.
        _make_override_type(
            _make_override_model(),
            fields=("id", "text_value"),
            required_overrides=("note",),
        )


def test_override_consumer_authored_field_raises() -> None:
    """A name with a consumer annotation raises (the annotation already controls nullability)."""
    with pytest.raises(ConfigurationError, match="consumer-authored"):
        _make_override_type(
            _make_override_model(),
            namespace={"__annotations__": {"text_value": int}},
            fields=("id", "text_value"),
            nullable_overrides=("text_value",),
        )


def test_override_relation_field_raises() -> None:
    """A relation field name raises - non-relation scope (Decision 10)."""
    with pytest.raises(ConfigurationError, match="relation field"):
        _make_override_type(
            _make_override_model(),
            fields=("id", "text_value", "partner"),
            nullable_overrides=("partner",),
        )


def test_override_relay_suppressed_pk_raises() -> None:
    """Naming the Relay-Node-suppressed pk in an override set raises (Decision 8 rule e)."""
    with pytest.raises(ConfigurationError, match="Relay-Node-suppressed pk"):

        @definition_raises
        class CategoryNodeOverride(DjangoType):
            class Meta:
                model = Category
                fields = ("id", "name")
                interfaces = (relay.Node,)
                required_overrides = ("id",)


def test_override_both_sets_collision_raises() -> None:
    """The same name in both sets raises at the shape stage, naming the field."""
    with pytest.raises(ConfigurationError, match="both"):
        _make_override_type(
            _make_override_model(),
            fields=("id", "text_value"),
            nullable_overrides=("text_value",),
            required_overrides=("text_value",),
        )


def test_override_non_sequence_raises() -> None:
    """A bare-string override is rejected by the non-string-sequence shape guard."""
    with pytest.raises(ConfigurationError, match="non-string sequence"):
        # A bare string is an iterable of characters, not a field-name list.
        _make_override_type(
            _make_override_model(),
            fields=("id", "text_value"),
            nullable_overrides="text_value",
        )


def test_override_redundant_is_no_op() -> None:
    """A redundant override (already in the target direction) is accepted, not raised.

    ``nullable_overrides`` on an already-nullable column and
    ``required_overrides`` on an already-non-null column are legitimate
    (if redundant) declarations - pinned as a passing case (Edge cases).
    """
    # note is already nullable; text_value is already non-null.
    override_type = _make_override_type(
        _make_override_model(),
        fields=("id", "text_value", "note"),
        nullable_overrides=("note",),
        required_overrides=("text_value",),
    )

    assert override_type.__annotations__["note"] == (str | None)
    assert override_type.__annotations__["text_value"] is str


# ---------------------------------------------------------------------------
# Consumer file/image override (spec-037 Decision 3)
# ---------------------------------------------------------------------------


def _make_file_override_model() -> type[models.Model]:
    """Return ``scalars.MediaSpecimen``, whose ``attachment`` is a required ``FileField``."""
    return MediaSpecimen


def test_consumer_annotation_override_on_file_column_keeps_str_and_no_resolver() -> None:
    """A consumer ``attachment: str`` keeps the legacy ``str`` shape and gets no file resolver.

    The annotation-only override lands in ``consumer_authored_fields``, so
    ``_build_annotations`` leaves the ``str`` annotation alone (no
    ``DjangoFileType``) AND ``_attach_file_resolvers`` -- keyed on the broader
    ``consumer_authored_fields`` union -- attaches no generated parent resolver
    for the column (spec-037 Decision 3). A generated file column would leave a
    ``resolve_attachment`` function in ``__dict__`` (see the no-override case);
    the overridden column leaves none.
    """
    model = _make_file_override_model()
    override_type = _make_file_override_model_type(
        model,
        namespace={"__annotations__": {"attachment": str}},
    )
    finalize_django_types()

    # Annotation stays ``str``, never widened to ``DjangoFileType``.
    assert override_type.__annotations__["attachment"] is str
    # No generated file parent resolver was attached for the overridden column
    # (a generated column leaves a ``resolve_attachment`` function in __dict__).
    assert "attachment" not in override_type.__dict__


def test_no_override_file_column_gets_generated_resolver() -> None:
    """Without an override, the file column DOES get a generated ``resolve_attachment``.

    The control case for the override test above: it pins that the absence of a
    generated resolver in the override case is the override's doing, not a
    blanket no-attach (spec-037 Decision 3).
    """
    model = _make_file_override_model()
    generated_type = _make_file_override_model_type(model)
    finalize_django_types()

    attr = generated_type.__dict__.get("attachment")
    assert callable(attr)
    assert attr.__name__ == "resolve_attachment"


def test_consumer_assigned_field_resolver_on_file_column_is_not_clobbered() -> None:
    """A consumer-assigned ``strawberry.field(resolver=...)`` on a file column survives.

    The assigned-override path also lands in ``consumer_authored_fields``, so the
    generated file resolver must not replace the consumer's own resolver.
    ``strawberry.type(...)`` unwraps the assigned ``StrawberryField`` back to the
    consumer's bare resolver function in ``__dict__`` at finalize, so the
    distinguishing assertion is that the surviving function is the consumer's
    (named ``attachment_resolver``), NOT the generated ``resolve_attachment``
    (spec-037 Decision 3).
    """

    def attachment_resolver() -> str:
        return "consumer-owned"

    model = _make_file_override_model()
    consumer_field = strawberry.field(resolver=attachment_resolver)
    override_type = _make_file_override_model_type(
        model,
        namespace={"attachment": consumer_field},
    )
    finalize_django_types()

    attr = override_type.__dict__.get("attachment")
    assert callable(attr)
    assert attr.__name__ == "attachment_resolver"


def _make_file_override_model_type(
    model: type[models.Model],
    *,
    namespace: dict[str, object] | None = None,
) -> type[DjangoType]:
    """Build an ``OverrideType`` over ``model`` selecting only ``id`` + ``attachment``."""
    meta_cls = type("Meta", (), {"model": model, "fields": ("id", "attachment")})
    return type("OverrideType", (DjangoType,), {"Meta": meta_cls, **(namespace or {})})


# The three tests below reuse ``_make_path_optin_model`` / ``_make_path_optin_type``
# from the next block: ``MediaSpecimen`` carries a file column, an image column
# and a scalar in one model, which is what a per-column override needs an
# unnamed sibling for.


def test_meta_required_overrides_forces_non_null_file_output() -> None:
    """``Meta.required_overrides`` on a ``FileField`` yields the BARE ``DjangoFileType``.

    The file/image output object is nullable by default (spec-037 Decision 4), and
    ``required_overrides`` is the documented opt-out from that default. This pins
    the whole public path - ``Meta`` through ``_build_annotations``'
    ``force_nullable=False`` into ``convert_field_output``'s file branch - where
    the converter-level tests pin only the ``force_nullable`` keyword one layer
    below the contract's own spelling.

    ``image`` is the control: an unnamed sibling file/image column in the SAME
    type stays ``| None``, so a passing first assertion cannot be explained by
    "file columns are non-null".
    """
    model = _make_path_optin_model()
    override_type = _make_path_optin_type(model, required_overrides=("attachment",))
    finalize_django_types()

    assert override_type.__annotations__["attachment"] is DjangoFileType
    assert override_type.__annotations__["image"] == (DjangoImageType | None)


def test_meta_required_overrides_forces_non_null_image_output() -> None:
    """The override reaches an ``ImageField`` too, so the branch is not ``FileField``-only.

    ``attachment`` is the control in the mirrored direction: the unnamed file
    column stays ``| None`` while the named image column loses it.
    """
    model = _make_path_optin_model()
    override_type = _make_path_optin_type(model, required_overrides=("image",))
    finalize_django_types()

    assert override_type.__annotations__["image"] is DjangoImageType
    assert override_type.__annotations__["attachment"] == (DjangoFileType | None)


def test_meta_nullable_overrides_on_a_file_column_is_a_no_op() -> None:
    """``nullable_overrides`` on an already-nullable file column changes nothing.

    The redundant-declaration direction for the file branch, matching
    ``test_override_redundant_is_no_op``'s shape for scalars: the output object is
    already ``| None`` by default, so naming it must neither raise nor widen it
    twice.
    """
    model = _make_path_optin_model()
    override_type = _make_path_optin_type(model, nullable_overrides=("attachment",))
    finalize_django_types()

    assert override_type.__annotations__["attachment"] == (DjangoFileType | None)


# ---------------------------------------------------------------------------
# Meta.filesystem_path_fields (spec-048 Decision 2)
# ---------------------------------------------------------------------------


def _make_path_optin_model() -> type[models.Model]:
    """Return ``scalars.MediaSpecimen``: a file column, an image column, and a text ``label``."""
    return MediaSpecimen


def _make_path_optin_type(
    model: type[models.Model],
    *,
    namespace: dict[str, object] | None = None,
    fields: Sequence[str] | None = None,
    **meta_attrs: object,
) -> type[DjangoType]:
    """Build a ``PathOptInType`` over ``model`` with the given Meta attrs."""
    meta_cls = type(
        "Meta",
        (),
        {
            "model": model,
            "fields": fields
            or (
                "id",
                "attachment",
                "image",
                "label",
            ),
            **meta_attrs,
        },
    )
    return type("PathOptInType", (DjangoType,), {"Meta": meta_cls, **(namespace or {})})


def test_filesystem_path_fields_is_a_net_new_allowed_meta_key() -> None:
    """``Meta.filesystem_path_fields`` is ALLOWED and not a deferred-key promotion."""
    assert "filesystem_path_fields" in ALLOWED_META_KEYS
    assert "filesystem_path_fields" not in DEFERRED_META_KEYS


def test_filesystem_path_fields_opts_an_image_column_into_the_image_sibling() -> None:
    """An ``ImageField`` opt-in keeps its dimensions and gains the path."""
    model = _make_path_optin_model()
    optin_type = _make_path_optin_type(model, filesystem_path_fields=("image",))
    finalize_django_types()

    assert optin_type.__annotations__["image"] == (DjangoImagePathType | None)


def test_filesystem_path_fields_rejects_an_unknown_field() -> None:
    """A name the model does not have raises the shared unknown-field error."""
    model = _make_path_optin_model()
    with pytest.raises(ConfigurationError, match="filesystem_path_fields"):
        _make_path_optin_type(model, filesystem_path_fields=("does_not_exist",))


def test_filesystem_path_fields_rejects_a_field_outside_the_selected_set() -> None:
    """A real but unselected column raises rather than silently doing nothing.

    A silent no-op here reads to a reviewer as either "the path is exposed" or
    "the path is not exposed" with equal plausibility, which is exactly the
    ambiguity a security opt-in cannot afford.
    """
    model = _make_path_optin_model()
    with pytest.raises(ConfigurationError, match="not in the selected set"):
        _make_path_optin_type(
            model,
            fields=("id", "label"),
            filesystem_path_fields=("attachment",),
        )


def test_filesystem_path_fields_rejects_a_non_file_column() -> None:
    """A scalar column has no path to publish, so naming one raises."""
    model = _make_path_optin_model()
    with pytest.raises(ConfigurationError, match="not a FileField or ImageField"):
        _make_path_optin_type(model, filesystem_path_fields=("label",))


def test_filesystem_path_fields_rejects_a_consumer_authored_column() -> None:
    """A consumer-owned column already owns its output type, so the opt-in raises."""
    model = _make_path_optin_model()
    with pytest.raises(ConfigurationError, match="consumer-authored"):
        _make_path_optin_type(
            model,
            namespace={"__annotations__": {"attachment": str}},
            filesystem_path_fields=("attachment",),
        )


def test_filesystem_path_fields_rejects_a_bare_string() -> None:
    """A bare string reuses the shared collection guard.

    A ``str`` is iterable, so accepting one would read a single field name as a
    sequence of single-character names and then reject every one of them for a
    reason that names no real mistake.
    """
    model = _make_path_optin_model()
    with pytest.raises(ConfigurationError, match=r"Meta\.filesystem_path_fields"):
        _make_path_optin_type(model, filesystem_path_fields="attachment")


@pytest.mark.parametrize(
    "declaration",
    [
        ("attachment",),
        ["attachment"],
        frozenset({"attachment"}),
        {"attachment"},
    ],
    ids=[
        "tuple",
        "list",
        "frozenset",
        "set",
    ],
)
def test_filesystem_path_fields_accepts_every_collection_literal(
    declaration: Collection[str],
) -> None:
    """A set of names may be declared as a set (spec-048 Decision 2).

    The key names an unordered SET of columns and is normalized to a
    ``frozenset`` immediately, so refusing the literal a consumer would reach for
    to spell a set was a shape gate contradicting its own semantics - and the
    documented accepted-values list already said ``frozenset``.
    """
    model = _make_path_optin_model()
    optin_type = _make_path_optin_type(model, filesystem_path_fields=declaration)
    finalize_django_types()

    assert optin_type.__annotations__["attachment"] == (DjangoFilePathType | None)


@pytest.mark.parametrize(
    "key",
    ["nullable_overrides", "required_overrides", "filesystem_path_fields"],
)
def test_the_collection_guard_names_the_key_it_rejected(key: str) -> None:
    """One helper serves four ``Meta`` keys, so its message must name the caller's.

    The message previously said ``Meta.exclude`` whatever key was written, which
    sends a consumer who mistyped ``filesystem_path_fields`` to look at a key
    their class does not declare.
    """
    model = _make_path_optin_model()
    with pytest.raises(ConfigurationError, match=f"Meta.{key} must be a non-string"):
        # basedpyright: a dict splat is checked against every keyword of _make_path_optin_type; the
        # parametrized key only ever names a Meta attribute, which **meta_attrs takes as object
        _make_path_optin_type(model, **{key: "attachment"})  # pyright: ignore[reportArgumentType]


def test_the_collection_guard_still_names_exclude_for_exclude() -> None:
    """``Meta.exclude`` - the first key through the helper - keeps its own message.

    Declared without ``Meta.fields``, which the key is mutually exclusive with, so
    the shape gate under test is the one that runs.
    """
    model = _make_path_optin_model()
    with pytest.raises(ConfigurationError, match=r"Meta\.exclude must be a non-string"):
        type(
            "ExcludeShapeType",
            (DjangoType,),
            {"Meta": type("Meta", (), {"model": model, "exclude": "label"})},
        )


@pytest.mark.parametrize(
    "key",
    ["nullable_overrides", "required_overrides"],
)
def test_the_sibling_collection_keys_accept_a_frozenset_too(key: str) -> None:
    """The sibling keys share the widened guard, so the four cannot drift apart."""
    model = _make_path_optin_model()
    # basedpyright: a dict splat is checked against every keyword of _make_path_optin_type; the
    # parametrized key only ever names a Meta attribute, which **meta_attrs takes as object
    _make_path_optin_type(model, **{key: frozenset({"label"})})  # pyright: ignore[reportArgumentType]
    finalize_django_types()


def test_exclude_accepts_a_frozenset_too() -> None:
    """``Meta.exclude`` names an unordered set of columns as well."""
    model = _make_path_optin_model()
    excluded = type(
        "ExcludeSetType",
        (DjangoType,),
        {"Meta": type("Meta", (), {"model": model, "exclude": frozenset({"label"})})},
    )
    finalize_django_types()

    assert "label" not in excluded.__annotations__
    assert "attachment" in excluded.__annotations__


# =============================================================================
# Meta.cursor_field validation (the keyset-cursor opt-in's class-creation stage)
# =============================================================================


def test_meta_cursor_field_in_allowed_meta_keys() -> None:
    """``Meta.cursor_field`` is a net-new ALLOWED key.

    Net-new ALLOWED, NOT a DEFERRED_META_KEYS promotion - the feature ships in
    the same change that adds the key (the ``Meta.connection`` precedent).
    """
    assert "cursor_field" in ALLOWED_META_KEYS
    assert "cursor_field" not in DEFERRED_META_KEYS


def test_meta_cursor_field_valid_declaration_lands_on_definition() -> None:
    """A valid ``cursor_field`` normalizes to a tuple on the definition."""

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = CATEGORY_SCALAR_FIELDS
            interfaces = (relay.Node,)
            cursor_field = ["-name", "id"]

    assert CategoryType.__django_strawberry_definition__.cursor_field == ("-name", "id")


def test_meta_cursor_field_rejects_non_sequence_shapes() -> None:
    """A string / empty / non-string-entry ``cursor_field`` raises the shape error."""
    for bad_value in ("name", (), ("name", 3)):
        with pytest.raises(ConfigurationError, match="non-empty non-string sequence"):

            @definition_raises
            class CategoryType(DjangoType):
                class Meta:
                    model = Category
                    fields = CATEGORY_SCALAR_FIELDS
                    interfaces = (relay.Node,)
                    cursor_field = bad_value

        registry.clear()


def test_meta_cursor_field_rejects_malformed_and_traversing_entries() -> None:
    """A bare ``-``, a ``__`` traversal, and a duplicate column all raise."""
    for bad_value, match in (
        (("-", "id"), "not a valid order string"),
        (("--name", "id"), "not a valid order string"),
        (("parent__name", "id"), "traverses a relation"),
        (("name", "-name"), "more than once"),
    ):
        with pytest.raises(ConfigurationError, match=match):

            @definition_raises
            class CategoryType(DjangoType):
                class Meta:
                    model = Category
                    fields = CATEGORY_SCALAR_FIELDS
                    interfaces = (relay.Node,)
                    cursor_field = bad_value

        registry.clear()


def test_meta_cursor_field_requires_relay_node_shape() -> None:
    """``cursor_field`` on a non-Relay-Node type raises the shared gate error."""
    with pytest.raises(ConfigurationError, match="requires a Relay-Node-shaped type"):

        @definition_raises
        class CategoryType(DjangoType):
            class Meta:
                model = Category
                fields = CATEGORY_SCALAR_FIELDS
                cursor_field = ("name", "id")


def test_meta_cursor_field_finalization_validates_columns() -> None:
    """Finalization rejects a shape-valid ``cursor_field`` whose terminal is not unique."""

    class CategoryType(DjangoType):
        class Meta:
            model = Category
            fields = CATEGORY_SCALAR_FIELDS
            interfaces = (relay.Node,)
            # ``description`` is a plain non-unique column - shape-valid at
            # class creation, rejected by the finalization column contract.
            cursor_field = ("description",)

    assert registry.get(Category) is CategoryType

    with pytest.raises(ConfigurationError, match="must end in a unique column"):
        finalize_django_types()


def test_has_custom_get_queryset_with_subclasscheck_without_mro() -> None:
    class FakeMeta(type):
        @override
        def __subclasscheck__(cls, subclass: type) -> bool:
            return True

    class FakeType(metaclass=FakeMeta):
        pass

    assert not _detect_custom_get_queryset(FakeType)


def test_post_finalization_registration_raises() -> None:
    class FirstCategoryType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

    assert registry.get(Category) is FirstCategoryType

    finalize_django_types()
    assert registry.is_finalized()

    with pytest.raises(
        ConfigurationError,
        match="finalize_django_types\\(\\) already ran; cannot register LateCategoryType after finalization",
    ):

        @definition_raises
        class LateCategoryType(DjangoType):
            class Meta:
                model = Category
                fields = ("id", "name")


def test_optimizer_hints_unknown_field_raises() -> None:
    with pytest.raises(
        ConfigurationError,
        match=r"Category\.Meta\.optimizer_hints names unknown fields: \['nonexistent'\]\. Available:",
    ):

        @definition_raises
        class BadHintCategoryType(DjangoType):
            class Meta:
                model = Category
                fields = ("id", "name")
                optimizer_hints = {"nonexistent": OptimizerHint.select_related()}


def test_optimizer_hints_bad_value_raises() -> None:
    with pytest.raises(
        ConfigurationError,
        match=(
            r"optimizer_hints values must be OptimizerHint instances, "
            r"got non-OptimizerHint for: \['items'\]"
        ),
    ):

        @definition_raises
        class BadValueCategoryType(DjangoType):
            class Meta:
                model = Category
                fields = ("id", "name", "items")
                optimizer_hints = {"items": "not_a_hint"}


# ---------------------------------------------------------------------------
# PEP 563 (`from __future__ import annotations`) auto handling
# ---------------------------------------------------------------------------


def _exec_pep563_module(program: str, module_name: str) -> dict[str, type[DjangoType]]:
    """Execute ``program`` into a REAL sys.modules entry and return its namespace.

    Strawberry resolves string annotations through ``sys.modules`` for the
    class's ``__module__``; a real consumer module always has an entry, and
    this harness must reproduce that shape for finalize to run.
    """
    module = types.ModuleType(module_name)
    sys.modules[module_name] = module
    exec(program, module.__dict__)  # noqa: S102 - runs a literal PEP 563 test program
    return module.__dict__


def test_pep563_auto_annotation_synthesizes_model_inferred_type() -> None:
    """`name: auto` in a PEP 563 consumer still synthesizes the model type.

    Under ``from __future__ import annotations`` the marker reaches
    ``__init_subclass__`` as the STRING "auto" - raw annotation values are
    never evaluated there. ``_is_auto_annotation`` must accept that spelling
    or the field is misclassified as consumer-authored, no synthesis runs,
    and the literal string rides into ``cls.__annotations__``.
    """
    namespace = _exec_pep563_module(
        """
from __future__ import annotations

from django_strawberry_framework import DjangoType
from strawberry import auto

from apps.products.models import Category


class PEP563AutoType(DjangoType):
    class Meta:
        model = Category
        fields = ("id", "name")

    name: auto
""",
        "test_base_pep563_auto",
    )
    pep563_type = namespace["PEP563AutoType"]
    assert pep563_type.__annotations__["name"] is str
    finalize_django_types()
    assert get_object_definition(pep563_type) is not None


def test_pep563_dotted_auto_annotation_synthesizes_model_inferred_type() -> None:
    """`name: strawberry.auto` in a PEP 563 consumer is the same marker.

    ``auto`` has two source spellings - the imported name and the dotted
    ``strawberry.auto`` attribute - and PEP 563 preserves whichever the
    consumer wrote as the raw annotation STRING. Recognizing only "auto"
    misclassified the dotted spelling as a consumer-authored annotation, so
    no synthesis ran and the literal string rode into
    ``cls.__annotations__``.
    """
    namespace = _exec_pep563_module(
        """
from __future__ import annotations

import strawberry

from django_strawberry_framework import DjangoType

from apps.products.models import Category


class PEP563DottedAutoType(DjangoType):
    class Meta:
        model = Category
        fields = ("id", "name")

    name: strawberry.auto
""",
        "test_base_pep563_dotted_auto",
    )
    pep563_type = namespace["PEP563DottedAutoType"]
    assert pep563_type.__annotations__["name"] is str
    finalize_django_types()
    assert get_object_definition(pep563_type) is not None


def test_pep563_foreign_dotted_auto_is_not_the_marker() -> None:
    """`Something.auto` under a non-``strawberry`` prefix stays consumer-authored.

    Only the ``strawberry`` prefix makes a dotted ``.auto`` the infer marker.
    Any other object's ``auto`` attribute is an ordinary type annotation and
    must keep its own meaning - matching on the ``.auto`` suffix alone would
    hijack it and silently replace the consumer's declared type.
    """
    namespace = _exec_pep563_module(
        """
from __future__ import annotations

from django_strawberry_framework import DjangoType

from apps.products.models import Category


class Aliases:
    auto = str


class PEP563ForeignDottedType(DjangoType):
    class Meta:
        model = Category
        fields = ("id", "name")

    name: Aliases.auto
""",
        "test_base_pep563_foreign_dotted_auto",
    )
    pep563_type = namespace["PEP563ForeignDottedType"]
    # Untouched by synthesis: the consumer's own annotation string survives.
    assert pep563_type.__annotations__["name"] == "Aliases.auto"
    finalize_django_types()
    assert get_object_definition(pep563_type) is not None


def test_pep563_unselected_dotted_auto_annotation_raises() -> None:
    """The unselected-`auto` guard fires for the dotted spelling too."""
    with pytest.raises(ConfigurationError, match=r"not selected in Meta\.fields"):
        _exec_pep563_module(
            """
from __future__ import annotations

import strawberry

from django_strawberry_framework import DjangoType

from apps.products.models import Category


class PEP563UnselectedDottedAutoType(DjangoType):
    class Meta:
        model = Category
        fields = ("id",)

    name: strawberry.auto
""",
            "test_base_pep563_unselected_dotted_auto",
        )


def test_pep563_auto_relation_annotation_registers_pending_relation() -> None:
    """`items: auto` under PEP 563 still defers through a PendingRelation.

    The misclassification this pins used to register ZERO pending records -
    the relation was treated as consumer-authored and the finalizer never
    resolved its target.
    """

    class ProbePEP563ItemType(DjangoType):
        class Meta:
            model = Item
            fields = ("id",)

    assert registry.get(Item) is ProbePEP563ItemType

    namespace = _exec_pep563_module(
        """
from __future__ import annotations

from django_strawberry_framework import DjangoType
from strawberry import auto

from apps.products.models import Category


class PEP563RelationAutoType(DjangoType):
    class Meta:
        model = Category
        fields = ("id", "name", "items")

    items: auto
""",
        "test_base_pep563_relation_auto",
    )
    pep563_type = namespace["PEP563RelationAutoType"]
    pending_for_type = [
        pending
        for pending in registry.iter_pending_relations()
        if pending.source_type is pep563_type
    ]
    assert [pending.field_name for pending in pending_for_type] == ["items"]
    finalize_django_types()
    assert get_object_definition(pep563_type) is not None


def test_pep563_unselected_auto_annotation_raises() -> None:
    """The unselected-`auto` guard fires for the PEP 563 string spelling too."""
    with pytest.raises(ConfigurationError, match=r"not selected in Meta\.fields"):
        _exec_pep563_module(
            """
from __future__ import annotations

from django_strawberry_framework import DjangoType
from strawberry import auto

from apps.products.models import Category


class PEP563UnselectedAutoType(DjangoType):
    class Meta:
        model = Category
        fields = ("id",)

    name: auto
""",
            "test_base_pep563_unselected_auto",
        )


def test_auto_string_spelling_accepted_without_future_import() -> None:
    """An explicit `name: "auto"` asks for the marker without PEP 563."""

    class StringAutoType(DjangoType):
        class Meta:
            model = Category
            fields = ("id", "name")

        # basedpyright: the unimported string spelling of auto is the marker under test
        name: "auto"  # noqa: F821  # pyright: ignore[reportUndefinedVariable]

    assert StringAutoType.__annotations__["name"] is str
    finalize_django_types()
    assert get_object_definition(StringAutoType) is not None


def test_non_string_annotation_keys_raise_configuration_error() -> None:
    """Metaclass-injected non-string annotation keys are rejected, not leaked.

    Class-body syntax can only produce string keys, but a metaclass may
    inject arbitrary keys before ``type.__new__`` runs; the collection
    boundary must reject them instead of raising raw ``TypeError`` from the
    ``sorted()`` calls over the auto-name sets. The ``metaclass=`` KEYWORD
    is the only construction that applies the metaclass: a base-class
    position leaves ``type()`` in charge (verified on 3.14).
    """

    class InjectAnnotationsMeta(type):
        def __new__(
            mcs,
            name: str,
            bases: tuple[type, ...],
            namespace: dict[str, object],
            **kwargs: object,
        ) -> type:
            declared = namespace.get("__annotations__", {})
            assert is_object_dict(declared)
            annotations = dict(declared)
            annotations[1] = StrawberryAuto()
            annotations["zz"] = StrawberryAuto()
            namespace["__annotations__"] = annotations
            return super().__new__(mcs, name, bases, namespace, **kwargs)

    with pytest.raises(ConfigurationError, match="string names"):

        @definition_raises
        class ProbeNonStringKeysType(DjangoType, metaclass=InjectAnnotationsMeta):
            class Meta:
                model = Category
                fields = ("id",)


def test_meta_metaclass_raising_getattr_raises_configuration_error() -> None:
    """A Meta metaclass ``__getattr__`` that raises is contained.

    ``getattr(meta, key, default)`` only swallows ``AttributeError``; every
    Meta attribute read routes through ``_meta_attr`` so hostile attribute
    access surfaces as ``ConfigurationError`` like every other shape
    violation.
    """

    class HostileMeta(type):
        def __getattr__(cls, item: str) -> NoReturn:
            if item in {"fields", "optimizer_hints", "interfaces"}:
                raise RuntimeError(f"hostile Meta access: {item}")
            raise AttributeError(item)

    with pytest.raises(ConfigurationError, match="could not be read"):

        @definition_raises
        class ProbeHostileMetaType(DjangoType):
            class Meta(metaclass=HostileMeta):
                model = Category


@pytest.mark.parametrize(
    ("child_name", "fields_spec", "nullable"),
    [
        ("LnkPairChild", ("id", "name", "parent"), False),
        ("LnkPairChild", "__all__", False),
        ("LnkOptionalPairChild", ("id", "name", "parent"), True),
        ("LnkOptionalPairChild", "__all__", True),
    ],
    ids=[
        "required_explicit",
        "required_all",
        "nullable_explicit",
        "nullable_all",
    ],
)
def test_multi_column_forward_foreign_object_maps_to_its_related_type(
    child_name: str,
    fields_spec: Sequence[str],
    *,
    nullable: bool,
) -> None:
    """A forward ``ForeignObject`` over two columns is a generated relation field.

    Named in ``Meta.fields`` or pulled in through ``"__all__"``, it resolves at
    finalize to the related model's ``DjangoType`` like any forward
    single-valued relation, beside its carrier columns. Nullability is the
    relation's own ``null``, the flag Django's descriptor and join type read: a
    required link is ``LnkParentType``, a ``null=True`` link over nullable
    carriers is ``LnkParentType | None``.
    """
    child_model = getattr(_link_models, child_name)
    parent_type = type(
        "LnkParentType",
        (DjangoType,),
        {"Meta": type("Meta", (), {"model": _link_models.LnkParent, "fields": ("id", "label")})},
    )
    child_type = type(
        f"{child_name}Type",
        (DjangoType,),
        {"Meta": type("Meta", (), {"model": child_model, "fields": fields_spec})},
    )
    finalize_django_types()

    carriers: set[str] = {"p_tenant", "p_code"} if fields_spec == "__all__" else set()
    assert set(child_type.__django_strawberry_definition__.field_map) == {
        "id",
        "name",
        "parent",
        *carriers,
    }
    expected = (parent_type | None) if nullable else parent_type
    assert child_type.__annotations__["parent"] == expected
