"""Exception hierarchy: inheritance, GraphQL translation, hostile message args."""

from __future__ import annotations

import copy
import pickle

import strawberry

from django_strawberry_framework.exceptions import (
    ConfigurationError,
    DjangoStrawberryFrameworkError,
    LookupValidationError,
    OptimizerError,
    PathResolutionError,
    _safe_arg_repr,
    _safe_class_name,
    _safe_model_label,
    _safe_terminal_label,
    _safe_type_name,
    describe_value,
)
from django_strawberry_framework.utils.querysets import SyncMisuseError


class _Unprintable:
    """Hostile message arg whose ``str`` / ``repr`` both raise."""

    def __str__(self) -> str:
        raise RuntimeError("str failed")

    def __repr__(self) -> str:
        raise RuntimeError("repr failed")


class _UnprintableBase:
    """Hostile arg whose dunders raise a ``BaseException`` (not ``Exception``)."""

    def __str__(self) -> str:
        raise KeyboardInterrupt

    def __repr__(self) -> str:
        raise KeyboardInterrupt


class _Counting:
    """Arg that counts how many times it is rendered (side-effect probe)."""

    def __init__(self) -> None:
        self.renders = 0

    def __str__(self) -> str:
        self.renders += 1
        return "counted"

    __repr__ = __str__


class _HostileTypeNameMeta(type):
    """Metaclass that makes even the fallback class-name lookup fail."""

    def __getattribute__(cls, name: str):
        if name == "__name__":
            raise RuntimeError("type name failed")
        return super().__getattribute__(name)


class _UnprintableTypeName(metaclass=_HostileTypeNameMeta):
    def __str__(self) -> str:
        raise RuntimeError("str failed")

    def __repr__(self) -> str:
        raise RuntimeError("repr failed")


class _Stateful:
    """Arg whose ``str`` succeeds until ``armed`` flips, then raises (delayed failure)."""

    def __init__(self) -> None:
        self.armed = False

    def __str__(self) -> str:
        if self.armed:
            raise RuntimeError("now broken")
        return "fine-for-now"

    __repr__ = __str__


class _HostileMetadata:
    """Metadata-bearing input whose label lookup raises during error construction."""

    def __getattribute__(self, name: str):
        if name in {"_meta", "name"}:
            raise RuntimeError(f"{name} unavailable")
        return super().__getattribute__(name)


class _NonStringTypeNameMeta(type):
    """Metaclass exposing malformed, non-string class-name metadata."""

    def __getattribute__(cls, name: str):
        if name == "__name__":
            return 42
        return super().__getattribute__(name)


class _NonStringTypeName(metaclass=_NonStringTypeNameMeta):
    pass


class _HostileString(str):
    def __str__(self) -> str:
        raise RuntimeError("string normalization failed")


class _PicklableDummyModelMeta:
    label = "auth.User"


class _PicklableDummyModel:
    _meta = _PicklableDummyModelMeta()


class _PicklableDummyTerminal:
    name = "created_at"


def _execute_raising(exc_factory):
    @strawberry.type
    class Query:
        @strawberry.field
        def boom(self) -> str:
            raise exc_factory()

    return strawberry.Schema(query=Query).execute_sync("{ boom }")


def test_inheritance_lattice():
    assert issubclass(ConfigurationError, DjangoStrawberryFrameworkError)
    assert issubclass(OptimizerError, DjangoStrawberryFrameworkError)
    assert issubclass(SyncMisuseError, ConfigurationError)
    assert issubclass(SyncMisuseError, DjangoStrawberryFrameworkError)
    assert issubclass(SyncMisuseError, RuntimeError)
    assert not issubclass(OptimizerError, ConfigurationError)


def test_unprintable_arg_str_and_repr_never_raise():
    bad = _Unprintable()
    err = ConfigurationError(bad)
    assert str(err) == "<unprintable _Unprintable>"
    assert "<unprintable _Unprintable>" in repr(err)
    # Identity is authoritative: the original object stays in ``.args``; only
    # rendering is made safe (str/repr never touch the hostile object twice).
    assert err.args == (bad,)


def test_unprintable_configuration_error_keeps_identity_through_graphql():
    """GraphQL-core ``located_error`` calls ``str(exc)``; must not replace the type."""
    result = _execute_raising(lambda: ConfigurationError(_Unprintable()))
    assert result.errors
    oe = result.errors[0].original_error
    assert isinstance(oe, ConfigurationError)
    assert isinstance(oe, DjangoStrawberryFrameworkError)
    assert "<unprintable _Unprintable>" in result.errors[0].message


def test_unprintable_optimizer_error_keeps_identity_through_graphql():
    result = _execute_raising(lambda: OptimizerError(_Unprintable()))
    oe = result.errors[0].original_error
    assert isinstance(oe, OptimizerError)
    assert "<unprintable _Unprintable>" in result.errors[0].message


def test_unprintable_syncmisuse_keeps_identity_through_graphql():
    result = _execute_raising(lambda: SyncMisuseError(_Unprintable()))
    oe = result.errors[0].original_error
    assert isinstance(oe, SyncMisuseError)
    assert isinstance(oe, ConfigurationError)
    assert isinstance(oe, RuntimeError)
    assert "<unprintable _Unprintable>" in result.errors[0].message


def test_normal_string_message_unchanged():
    err = OptimizerError("Unplanned N+1: books")
    assert str(err) == "Unplanned N+1: books"
    assert err.args == ("Unplanned N+1: books",)


def test_empty_args_render_empty_string():
    """No message args: ``str`` is empty and never hits the placeholder path."""
    assert str(DjangoStrawberryFrameworkError()) == ""


def test_multiple_args_mixed_printable_and_unprintable():
    """Multi-arg render is safe, keeps every original arg, and shows both."""
    bad = _Unprintable()
    err = ConfigurationError("ctx", bad)
    rendered = str(err)
    assert "'ctx'" in rendered
    assert "<unprintable _Unprintable>" in rendered
    assert err.args == ("ctx", bad)


def test_render_is_lazy_and_recomputed():
    """Construction is lazy while later renders reflect current value/context."""
    counter = _Counting()
    err = OptimizerError(counter)
    assert counter.renders == 0  # construction does not render
    assert str(err) == "counted"
    assert str(err) == "counted"
    assert counter.renders == 2


def test_args_reassignment_and_pickle_never_leave_stale_render_caches():
    """Standard mutable-``args`` semantics survive rendering and serialization."""
    err = ConfigurationError("first")
    assert str(err) == "first"
    assert repr(err) == "ConfigurationError('first')"

    err.args = ("second",)
    restored = pickle.loads(pickle.dumps(err))

    assert str(err) == "second"
    assert repr(err) == "ConfigurationError('second')"
    assert str(restored) == "second"
    assert repr(restored) == "ConfigurationError('second')"


def test_delayed_stateful_failure_is_handled():
    """An arg that only breaks AFTER construction still renders safely (call-time guard)."""
    arg = _Stateful()
    err = OptimizerError(arg)
    arg.armed = True  # now str(arg) raises - the eager-probe approach could not catch this
    assert str(err) == "<unprintable _Stateful>"
    assert str(err) == "<unprintable _Stateful>"  # cached, still safe


def test_base_exception_from_arg_is_swallowed():
    """A dunder raising ``BaseException`` (not ``Exception``) must not propagate."""
    err = ConfigurationError(_UnprintableBase())
    assert str(err) == "<unprintable _UnprintableBase>"
    assert "<unprintable _UnprintableBase>" in repr(err)


def test_hostile_metaclass_type_name_is_guarded_too():
    """Fallback rendering does not trust ``type(arg).__name__``."""
    err = ConfigurationError(_UnprintableTypeName())
    assert str(err) == "<unprintable object>"
    assert repr(err) == "ConfigurationError(<unprintable object>)"


def test_diagnostic_metadata_helpers_fall_back_for_malformed_consumer_metadata():
    """Typed diagnostics survive non-string names and hostile string-valued labels.

    The fallback still has to NAME something. A model is a class, so it names
    itself: reporting ``type(model).__name__`` would print the metaclass
    (``ModelBase`` for every Django model) and identify nothing.
    """

    class _Model:
        _meta = type("Meta", (), {"label": _HostileString("catalog.Item")})()

    class _Terminal:
        name = _HostileString("category")

    assert _safe_type_name(_NonStringTypeName()) == "object"
    assert _safe_model_label(_Model) == "_Model"
    assert _safe_terminal_label(_Terminal()) == "_Terminal"


def test_syncmisuse_error_renders_safely_and_keeps_identity():
    """The base overrides reach the multiply-inheriting ``SyncMisuseError`` subclass."""
    bad = _Unprintable()
    err = SyncMisuseError(bad)
    assert str(err) == "<unprintable _Unprintable>"
    assert err.args == (bad,)
    assert isinstance(err, (ConfigurationError, RuntimeError))


def test_path_resolution_error_constructor_survives_hostile_metadata_and_values():
    """Typed path errors remain constructible when diagnostic inputs are hostile."""
    model = _HostileMetadata()
    path = _Unprintable()
    segment = _Unprintable()

    err = PathResolutionError(model, path, segment)

    assert err.model is model
    assert err.field_path is path
    assert err.segment is segment
    assert "Cannot classify path <unprintable _Unprintable>" in str(err)
    assert "model _HostileMetadata" in str(err)


def test_lookup_validation_error_constructor_survives_hostile_metadata_and_values():
    """Typed lookup errors remain constructible when diagnostic inputs are hostile."""
    terminal = _HostileMetadata()
    lookup_expr = _Unprintable()
    part = _Unprintable()

    err = LookupValidationError(terminal, lookup_expr, part)

    assert err.terminal is terminal
    assert err.lookup_expr is lookup_expr
    assert err.part is part
    assert "Invalid lookup expression <unprintable _Unprintable>" in str(err)
    assert "terminal _HostileMetadata" in str(err)


def test_path_resolution_error_pickle_and_copy_fidelity():
    """PathResolutionError roundtrips through pickle, copy, and deepcopy preserving attributes."""
    err = PathResolutionError(_PicklableDummyModel, "groups.permissions", "permissions")
    err.custom_tag = "custom_value"

    # Pickle serialization roundtrip
    restored = pickle.loads(pickle.dumps(err))
    assert isinstance(restored, PathResolutionError)
    assert restored.model is _PicklableDummyModel
    assert restored.field_path == "groups.permissions"
    assert restored.segment == "permissions"
    assert getattr(restored, "custom_tag", None) == "custom_value"
    assert str(restored) == str(err)
    assert repr(restored) == repr(err)

    # copy and deepcopy
    copied = copy.copy(err)
    assert isinstance(copied, PathResolutionError)
    assert copied.model is _PicklableDummyModel
    assert copied.field_path == "groups.permissions"
    assert copied.segment == "permissions"
    assert getattr(copied, "custom_tag", None) == "custom_value"

    deep_copied = copy.deepcopy(err)
    assert isinstance(deep_copied, PathResolutionError)
    assert deep_copied.model is _PicklableDummyModel
    assert deep_copied.field_path == "groups.permissions"
    assert deep_copied.segment == "permissions"
    assert getattr(deep_copied, "custom_tag", None) == "custom_value"


def test_lookup_validation_error_pickle_and_copy_fidelity():
    """LookupValidationError roundtrips through pickle, copy, and deepcopy preserving attributes."""
    term = _PicklableDummyTerminal()
    err = LookupValidationError(term, "created_at__year__invalid", "invalid")
    err.custom_tag = "custom_value"

    # Pickle serialization roundtrip
    restored = pickle.loads(pickle.dumps(err))
    assert isinstance(restored, LookupValidationError)
    assert restored.terminal.name == "created_at"
    assert restored.lookup_expr == "created_at__year__invalid"
    assert restored.part == "invalid"
    assert getattr(restored, "custom_tag", None) == "custom_value"
    assert str(restored) == str(err)
    assert repr(restored) == repr(err)

    # copy and deepcopy
    copied = copy.copy(err)
    assert isinstance(copied, LookupValidationError)
    assert copied.terminal is term
    assert copied.lookup_expr == "created_at__year__invalid"
    assert copied.part == "invalid"
    assert getattr(copied, "custom_tag", None) == "custom_value"

    deep_copied = copy.deepcopy(err)
    assert isinstance(deep_copied, LookupValidationError)
    assert deep_copied.lookup_expr == "created_at__year__invalid"
    assert deep_copied.part == "invalid"
    assert getattr(deep_copied, "custom_tag", None) == "custom_value"


def test_str_subclass_with_hostile_format_is_stripped_by_helpers():
    """Helpers strip str subclasses so hostile __format__ cannot detonate error message formatting."""

    class _HostileFormatStr(str):
        def __str__(self) -> str:
            return self

        def __format__(self, format_spec: str) -> str:
            raise RuntimeError("hostile __format__ detonated")

    class _HostileFormatRepr:
        def __repr__(self) -> str:
            return _HostileFormatStr("<HostileFormatRepr>")

    class _ModelWithHostileLabel:
        _meta = type("Meta", (), {"label": _HostileFormatStr("app.HostileModel")})()

    class _TerminalWithHostileName:
        name = _HostileFormatStr("hostile_field")

    # Safe helpers strip the subclass
    label = _safe_model_label(_ModelWithHostileLabel)
    assert type(label) is str
    assert label == "app.HostileModel"

    terminal_name = _safe_terminal_label(_TerminalWithHostileName())
    assert type(terminal_name) is str
    assert terminal_name == "hostile_field"

    arg_repr = _safe_arg_repr(_HostileFormatRepr())
    assert type(arg_repr) is str
    assert arg_repr == "<HostileFormatRepr>"

    # PathResolutionError and LookupValidationError construct without detonating
    path_err = PathResolutionError(_ModelWithHostileLabel, _HostileFormatRepr(), "segment")
    assert "app.HostileModel" in str(path_err)
    assert "<HostileFormatRepr>" in str(path_err)

    lookup_err = LookupValidationError(_TerminalWithHostileName(), "field__exact", "exact")
    assert "hostile_field" in str(lookup_err)


def test_safe_diagnostic_helpers_survive_hostile_class_property():
    """Diagnostic helpers survive hostile __class__ properties on inputs."""

    class _HostileClass:
        @property
        def __class__(self):
            raise RuntimeError("hostile __class__")

    bad = _HostileClass()
    assert _safe_type_name(bad) in {"_HostileClass", "object"}
    assert _safe_arg_repr(bad).startswith("<")
    assert _safe_class_name(bad) in {"_HostileClass", "object"}
    assert _safe_model_label(bad) in {"_HostileClass", "object"}
    assert _safe_terminal_label(bad) in {"_HostileClass", "object"}
    assert "unprintable" in describe_value(bad) or "_HostileClass" in describe_value(bad)


def test_safe_class_name_survives_hostile_name_metadata():
    """_safe_class_name survives a name attribute whose __class__ or __bool__ raises."""

    class _HostileClassAndBool:
        @property
        def __class__(self):
            raise RuntimeError("hostile __class__ on name")

        def __bool__(self):
            raise RuntimeError("hostile __bool__ on name")

        def __repr__(self):
            raise RuntimeError("hostile __repr__ on name")

    class _HostileNameObj:
        @property
        def __name__(self):
            return _HostileClassAndBool()

    assert _safe_class_name(_HostileNameObj()) == "<unprintable _HostileClassAndBool>"


def test_safe_type_name_edge_cases(monkeypatch):
    """Test empty string __name__, isinstance exceptions, and str.__str__ exceptions."""
    # Empty string __name__ (line 48)
    empty_cls = type("", (), {})
    assert _safe_type_name(empty_cls) == "type"
    assert _safe_type_name(empty_cls()) == "object"

    # isinstance(name, str) raising BaseException (lines 42-43)
    class _HostileClassDunder:
        @property
        def __class__(self):
            raise KeyboardInterrupt

    class _HostileTypeNameMeta(type):
        @property
        def __name__(cls):
            return _HostileClassDunder()

    class _HostileType(metaclass=_HostileTypeNameMeta):
        pass

    assert _safe_type_name(_HostileType) == "_HostileTypeNameMeta"
    assert _safe_type_name(_HostileType()) == "object"

    # str.__str__(name) raising BaseException (lines 55-56)
    import django_strawberry_framework.exceptions as exc_mod

    class _MockStrMeta(type):
        def __instancecheck__(cls, instance):
            return True

    class _MockStr(metaclass=_MockStrMeta):
        def __str__(self):
            raise KeyboardInterrupt

    monkeypatch.setattr(exc_mod, "str", _MockStr, raising=False)
    assert _safe_type_name(int) == "object"
