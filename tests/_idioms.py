"""Shared test idioms written so the type checker can follow them.

``definition_raises`` decorates a class statement that a test wraps in ``pytest.raises``
because declaring the class is the call under test. The metaclass raises before the class
object exists, so the decorator never runs and the name is never bound; the decorator is
the read that keeps basedpyright from reporting the never-used local class
(``reportUnusedClass``), so such sites carry no per-site suppression. If the statement
unexpectedly succeeds, the decorator fails the test with a message naming the class, ahead
of ``pytest.raises``'s generic ``DID NOT RAISE``.

``module_binding`` reads a name out of a module's own namespace. A single-source check
asserts that a consumer module holds the SAME object as its owner, so it reads the
consumer's binding rather than importing the owner again; basedpyright flags that attribute
read as use of a private local import (``reportPrivateLocalImportUsage``). ``vars()`` reads
the ``__dict__`` entry, which a package ``__getattr__`` cannot satisfy, so the check is at
least as strict as the attribute read it replaces.

``ModelSerializerBase`` is ``serializers.ModelSerializer`` with the nested ``Meta`` the
stubs declare but the runtime class lacks (``djangorestframework-stubs`` types
``ModelSerializer.Meta``; DRF's class has no such attribute to subclass). Every test
serializer that declares ``class Meta:`` derives from it, so the one override of the stub's
attribute is declared here rather than suppressed at each ``class Meta:``. The annotation
creates no class attribute, so DRF's metaclass and ``__class_getitem__`` see the same class
body and the same ``ModelSerializer`` they see without it.

``websocket_scope`` builds a complete ASGI WebSocket handshake scope, so a row that cares
about only the headers and the ``server`` pair still hands a typed scope to code that
declares asgiref's ``WebSocketScope``.

``relay_hooks`` / ``async_relay_hooks`` read the Relay resolvers ``finalize_django_types()``
installs on a Relay ``DjangoType``. The declared class gains ``relay.Node`` only when the
finalizer injects it, so its static type carries none of them; and ``relay.Node``'s own
signatures type the rows as the node class, not the model rows the installed defaults
return. The accessor asserts the type really is a ``relay.Node`` over ``model`` and hands
it back as a protocol naming the call shapes the tests use: rows typed as ``model``, and
``info`` as ``object`` because the paths under test never read it. ``relay_hooks`` is the
sync executor's shape; ``async_relay_hooks`` is the async one, where ``resolve_node`` and
``resolve_nodes`` return the coroutine the caller awaits.

``declare_django_type`` is ``type(name, (DjangoType,), namespace)`` handed back as
``type[DjangoType]``: the three-argument ``type`` call is typed as returning ``type``, so the
helper checks the subclass relation it built and every later read of the class (its
definition, its hooks) resolves.

``resolver_function`` reads the function a Strawberry field's resolver wraps
(``field.base_resolver.wrapped_func``), asserting the field has a resolver and the wrapped
object is a plain function; Strawberry annotates ``base_resolver`` as the bare generic
``StrawberryResolver``, so the one read that inherits its Unknown lives here.

``pickle_roundtrip`` dumps a value and loads the bytes straight back, typed as the value it
was given, so every pickle test shares the one unpickle (and its one lint suppression) and
reads its result as the original type rather than ``Any``.

``run_capturing`` is the target a test hands a ``threading.Thread`` (``args=(errors, fn)``):
it runs ``fn`` and appends whatever it raises to ``errors``, so the main thread asserts the
list is empty after ``join`` instead of every worker body carrying its own catch-all.

``ClassReadRaises`` / ``ClaimsClass`` are the two hostile values a guard on a consumer-supplied
value is tested against: one whose ``__class__`` read raises (so a bare ``isinstance`` raises
with it), and one whose ``__class__`` claims a class its real type is not (so a bare
``isinstance`` is true and the base slot that follows refuses it). Both render as
``<ClassReadRaises>`` / ``<ClaimsClass>`` so a rejection message that quotes the value is
deterministic.

``comparing_metaclass`` derives a metaclass from ``base`` whose ``__eq__`` answers every
comparison of its classes with ``verdict`` (equal, unequal, or a raised ``RuntimeError``) and
records each call, so a row declares a consumer class under it and asserts both the honest
outcome and that nothing compared the class by equality. ``__hash__`` stays ``base``'s, so
hash-keyed stores keep finding the class by identity. ``against`` narrows the hostile answer
to comparisons with that one class (any other comparison is ``NotImplemented`` and unrecorded),
for a row whose class also passes through a standard-library equality test it cannot avoid.

``str_subclass_name`` spells a field name through one of the ``str`` subclass kinds a
consumer can hand a declaration (``STR_SUBCLASS_KINDS``): an honest subclass, one whose
``__eq__`` / ``__ne__`` answer "never equal", one whose comparisons raise, a ``(str, Enum)``
member and an ``enum.StrEnum`` member (its own shape spelled by hand before 3.11). The three plain
subclasses record every ``__eq__`` / ``__ne__`` / ``__hash__`` / ``__repr__`` / ``__str__``
call into ``calls``, so a row asserts both the honest outcome and that nothing read the name
through its own dunders. Build the declaration first, then clear ``calls``: building a ``set``
or ``dict`` hashes its members.

``is_object_dict`` / ``is_object_list`` narrow an ``object`` (a JSON payload, a GraphQL
result, a hook's input) the way ``isinstance`` does at run time, but to ``dict[object,
object]`` / ``list[object]``: a bare ``isinstance`` on an ``object`` narrows to the class
over Unknown element types, which every later read inherits.
"""

import enum
import inspect
import pickle
from collections.abc import Callable, Iterable, Mapping
from types import FunctionType, ModuleType
from typing import (
    TYPE_CHECKING,
    ClassVar,
    Literal,
    NoReturn,
    Protocol,
    TypeGuard,
    TypeVar,
    cast,
    overload,
)

from django.db.models import Model, QuerySet
from django.test.testcases import SimpleTestCase
from rest_framework import serializers
from strawberry import relay
from typing_extensions import override

from django_strawberry_framework import DjangoType
from django_strawberry_framework.utils.querysets import model_for

if TYPE_CHECKING:
    from asgiref.typing import WebSocketScope
    from strawberry.types.field import StrawberryField
    from typing_extensions import TypeIs

    from django_strawberry_framework.rest_framework.serializer_converter import DRFField

_ClassT = TypeVar("_ClassT", bound=type)
_MetaT = TypeVar("_MetaT", bound=type)
_T = TypeVar("_T")
_ModelT = TypeVar("_ModelT", bound=Model)
_DRFFieldT = TypeVar("_DRFFieldT", bound="DRFField")


class ModelSerializerBase(serializers.ModelSerializer[_ModelT]):
    """``ModelSerializer`` carrying the ``Meta`` the stubs declare and the runtime class lacks."""

    # basedpyright: the DRF stubs declare ModelSerializer.Meta; the runtime class has none
    Meta: ClassVar[type[object]]  # pyright: ignore[reportIncompatibleVariableOverride]


def declare_django_type(name: str, namespace: Mapping[str, object]) -> type[DjangoType]:
    """Declare ``class <name>(DjangoType)`` with ``namespace`` as its body, typed as such."""
    declared = type(name, (DjangoType,), dict(namespace))
    assert issubclass(declared, DjangoType)
    return declared


def comparing_metaclass(
    base: type[_MetaT],
    verdict: Literal["equal", "unequal", "raises"],
    calls: list[str],
    *,
    against: type | None = None,
) -> type[_MetaT]:
    """A metaclass over ``base`` whose ``__eq__`` answers ``verdict`` and records each call."""

    def answer(cls: type, other: object) -> bool:
        if against is not None and other is not against:
            return NotImplemented
        calls.append(cls.__name__)
        if verdict == "raises":
            raise RuntimeError("metaclass __eq__")
        return verdict == "equal"

    namespace = {"__eq__": answer, "__hash__": base.__hash__}
    meta = type(f"{verdict.title()}EqMeta", (base,), namespace)
    assert issubclass(meta, base)
    return meta


#: The ``str`` subclass kinds ``str_subclass_name`` builds, as parametrize values.
STR_SUBCLASS_KINDS = (
    "honest",
    "unequal",
    "raises",
    "str-enum-mixin",
    "str-enum",
)


class _StrEnum(str, enum.Enum):
    """``enum.StrEnum``'s shape where the interpreter predates it: ``str()`` is the value."""

    __str__ = str.__str__
    __format__ = str.__format__


#: ``enum.StrEnum`` (Python 3.11+), or the same shape spelled by hand below it; call it with
#: the functional enum API to declare a whole ``StrEnum`` class of field names.
STR_ENUM = cast("type[enum.Enum]", getattr(enum, "StrEnum", _StrEnum))


def str_subclass_name(kind: str, text: str, calls: list[str]) -> str:
    """``text`` as an instance of the ``str`` subclass ``kind`` names; its dunders record into ``calls``."""
    if kind == "str-enum-mixin":
        member: object = enum.Enum("Names", {"MEMBER": text}, type=str)["MEMBER"]
    elif kind == "str-enum":
        member = STR_ENUM("Names", {"MEMBER": text})["MEMBER"]
    else:
        assert kind in ("honest", "unequal", "raises"), kind

        def compare(*, equal: bool) -> Callable[[str, object], bool]:
            def answer(self: str, other: object) -> bool:
                calls.append("__eq__" if equal else "__ne__")
                if kind == "raises":
                    raise RuntimeError("str subclass comparison")
                if kind == "unequal":
                    return not equal
                return str.__eq__(self, other) if equal else str.__ne__(self, other)

            return answer

        def record(name: str, slot: Callable[[str], _T]) -> Callable[[str], _T]:
            def read(self: str) -> _T:
                calls.append(name)
                return slot(self)

            return read

        namespace = {
            "__eq__": compare(equal=True),
            "__ne__": compare(equal=False),
            "__hash__": record("__hash__", str.__hash__),
            "__repr__": record("__repr__", str.__repr__),
            "__str__": record("__str__", str.__str__),
        }
        member = type(f"{kind.title()}Name", (str,), namespace)(text)
    assert isinstance(member, str)
    assert type(member) is not str
    return member


def resolver_function(field: "StrawberryField") -> FunctionType:
    """The plain function ``field``'s resolver wraps (``base_resolver.wrapped_func``)."""
    # basedpyright: Strawberry annotates StrawberryField.base_resolver as the bare generic
    # StrawberryResolver, so the resolver and its wrapped function read as partially Unknown
    resolver = field.base_resolver  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    assert resolver is not None
    wrapped: object = resolver.wrapped_func  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
    assert isinstance(wrapped, FunctionType)
    return wrapped


def is_object_dict(value: object) -> "TypeIs[dict[object, object]]":
    """Whether ``value`` is a ``dict`` (subclasses included), its items typed ``object``."""
    return isinstance(value, dict)


def is_object_list(value: object) -> "TypeIs[list[object]]":
    """Whether ``value`` is a ``list`` (subclasses included), its items typed ``object``."""
    return isinstance(value, list)


class ClassReadRaises:
    """A value whose ``__class__`` read raises ``escape``, so ``isinstance(value, C)`` raises it."""

    def __init__(self, escape: type[BaseException] = RuntimeError) -> None:
        self._escape = escape

    @property
    @override
    # basedpyright: deliberately a read-only ``__class__`` that raises: the hostile object is the
    # guard's input
    def __class__(self) -> NoReturn:  # pyright: ignore[reportIncompatibleMethodOverride]
        raise self._escape("hostile __class__")

    @override
    def __repr__(self) -> str:
        return "<ClassReadRaises>"


class ClaimsClass:
    """A plain object whose ``__class__`` claims ``claimed``: ``isinstance(value, claimed)`` is true."""

    def __init__(self, claimed: type) -> None:
        self._claimed = claimed

    @property
    @override
    # basedpyright: deliberately a read-only ``__class__``: the forged type is the guard's input
    def __class__(self) -> type:  # pyright: ignore[reportIncompatibleMethodOverride]
        return self._claimed

    @override
    def __repr__(self) -> str:
        return "<ClaimsClass>"


def pickle_roundtrip(value: _T) -> _T:
    """``value`` after a pickle dump and load: the one place a test unpickles."""
    # The bytes were produced one line up from ``value``, so loading them reads no untrusted input.
    return pickle.loads(pickle.dumps(value))  # noqa: S301 - round-trips the object this test just pickled


def run_capturing(errors: list[BaseException], fn: Callable[[], object]) -> None:
    """Run ``fn`` on a worker thread, recording what it raises in ``errors`` for the main thread.

    An exception escaping a ``threading.Thread`` target prints through ``threading.excepthook``
    and ends only that thread, so the test that started it would pass on a failed worker; the
    thread target is this function and the test asserts ``errors`` is empty after ``join``.
    """
    try:
        fn()
    except BaseException as exc:  # noqa: BLE001 - worker thread reports to the main thread
        errors.append(exc)


def definition_raises(cls: _ClassT) -> _ClassT:
    """Mark a class statement that must raise before its name is bound."""
    raise AssertionError(f"class statement for {cls.__qualname__} did not raise")


def module_binding(module: ModuleType, name: str) -> object:
    """Return ``module``'s own binding for ``name`` (its ``__dict__`` entry)."""
    return vars(module)[name]


def stub_module(name: str, **attributes: object) -> ModuleType:
    """Build a run-time module called ``name`` whose namespace holds ``attributes``."""
    module = ModuleType(name)
    vars(module).update(attributes)
    return module


def _remove_databases_failures_descriptor(
    cls: type[SimpleTestCase],
) -> "classmethod[SimpleTestCase, ..., object]":
    """``cls``'s ``_remove_databases_failures`` descriptor, found along the MRO unbound.

    django-stubs omits this private classmethod, so a test cannot name it on the class.
    ``inspect.getattr_static`` fetches the descriptor without binding it and the
    ``isinstance`` check makes the read assert the shape the callers use.
    """
    descriptor: object = inspect.getattr_static(cls, "_remove_databases_failures")
    assert _is_test_case_classmethod(descriptor)
    return descriptor


def _is_test_case_classmethod(
    value: object,
) -> "TypeGuard[classmethod[SimpleTestCase, ..., object]]":
    """Whether ``value`` is a ``classmethod`` descriptor (a ``SimpleTestCase`` one, by its owner)."""
    return isinstance(value, classmethod)


def remove_databases_failures_function(cls: type[SimpleTestCase]) -> object:
    """The function behind ``cls._remove_databases_failures`` (``classmethod.__func__``)."""
    return _remove_databases_failures_descriptor(cls).__func__


def call_remove_databases_failures(cls: type[SimpleTestCase]) -> None:
    """Run ``cls._remove_databases_failures()``: the descriptor's function called with ``cls``."""
    _remove_databases_failures_descriptor(cls).__func__(cls)


class RelayNodeHooks(Protocol[_ModelT]):
    """The installed Relay resolvers of a finalized type, called on the sync executor."""

    def resolve_id_attr(self) -> str: ...

    def resolve_id(self, root: object, *, info: object) -> str: ...

    @overload
    def resolve_node(
        self,
        node_id: object,
        *,
        info: object,
        required: Literal[True],
    ) -> _ModelT: ...

    @overload
    def resolve_node(
        self,
        node_id: object,
        *,
        info: object,
        required: bool = False,
    ) -> _ModelT | None: ...

    @overload
    def resolve_nodes(
        self,
        *,
        info: object,
        node_ids: None = None,
        required: bool = False,
    ) -> QuerySet[_ModelT]: ...

    @overload
    def resolve_nodes(
        self,
        *,
        info: object,
        node_ids: Iterable[object],
        required: bool = False,
    ) -> list[_ModelT | None]: ...

    def resolve_typename(self, root: object, info: object) -> str: ...


class AsyncRelayNodeHooks(Protocol[_ModelT]):
    """The installed Relay node lookups of a finalized type, called on the async executor."""

    @overload
    async def resolve_node(
        self,
        node_id: object,
        *,
        info: object,
        required: Literal[True],
    ) -> _ModelT: ...

    @overload
    async def resolve_node(
        self,
        node_id: object,
        *,
        info: object,
        required: bool = False,
    ) -> _ModelT | None: ...

    @overload
    async def resolve_nodes(
        self,
        *,
        info: object,
        node_ids: None = None,
        required: bool = False,
    ) -> QuerySet[_ModelT]: ...

    @overload
    async def resolve_nodes(
        self,
        *,
        info: object,
        node_ids: Iterable[object],
        required: bool = False,
    ) -> list[_ModelT | None]: ...


def _relay_type_over(type_cls: type[DjangoType], model: type[Model]) -> bool:
    """Return whether ``type_cls`` is a finalized ``relay.Node`` type over ``model``."""
    return issubclass(type_cls, relay.Node) and model_for(type_cls) is model


def _sync_hooks_over(
    type_cls: type[DjangoType],
    model: type[_ModelT],
) -> TypeGuard[RelayNodeHooks[_ModelT]]:
    return _relay_type_over(type_cls, model)


def _async_hooks_over(
    type_cls: type[DjangoType],
    model: type[_ModelT],
) -> TypeGuard[AsyncRelayNodeHooks[_ModelT]]:
    return _relay_type_over(type_cls, model)


def relay_hooks(type_cls: type[DjangoType], model: type[_ModelT]) -> RelayNodeHooks[_ModelT]:
    """Return finalized Relay type ``type_cls`` over ``model`` as its sync resolver hooks."""
    assert _sync_hooks_over(type_cls, model), f"{type_cls!r} is not a Relay type over {model!r}"
    return type_cls


def async_relay_hooks(
    type_cls: type[DjangoType],
    model: type[_ModelT],
) -> AsyncRelayNodeHooks[_ModelT]:
    """Return finalized Relay type ``type_cls`` over ``model`` as its async node lookups."""
    assert _async_hooks_over(type_cls, model), f"{type_cls!r} is not a Relay type over {model!r}"
    return type_cls


def websocket_scope(
    headers: Iterable[tuple[bytes, bytes]] = (),
    server: tuple[str, int | None] | None = None,
) -> "WebSocketScope":
    """Return a complete ASGI WebSocket handshake scope carrying ``headers`` and ``server``."""
    return {
        "type": "websocket",
        "asgi": {"spec_version": "2.3", "version": "3.0"},
        "http_version": "1.1",
        "scheme": "ws",
        "path": "/",
        "raw_path": b"/",
        "query_string": b"",
        "root_path": "",
        "headers": list(headers),
        "client": None,
        "server": server,
        "subprotocols": [],
        "extensions": None,
    }


def bind_unparented(field: _DRFFieldT, name: str) -> _DRFFieldT:
    """Bind a serializer field to ``name`` with no parent serializer, and return it.

    DRF populates ``field_name`` / ``source`` / ``source_attrs`` at bind time, and the
    converters read bound fields, as the schema-time discovery hands them. The field a
    row holds directly has no serializer above it.
    """
    # basedpyright: drf-stubs types parent as BaseSerializer; the runtime accepts None (an
    # unparented bound field); drf-stubs also spells that parameter as the bare generic
    # BaseSerializer, so bind reads as partially Unknown
    field.bind(name, None)  # pyright: ignore[reportArgumentType, reportUnknownMemberType]
    return field
