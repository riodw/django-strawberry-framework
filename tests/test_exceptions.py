"""Exception hierarchy: inheritance, GraphQL translation, hostile message args."""

from __future__ import annotations

import pickle

import strawberry

from django_strawberry_framework.exceptions import (
    ConfigurationError,
    DjangoStrawberryFrameworkError,
    OptimizerError,
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


def test_syncmisuse_error_renders_safely_and_keeps_identity():
    """The base overrides reach the multiply-inheriting ``SyncMisuseError`` subclass."""
    bad = _Unprintable()
    err = SyncMisuseError(bad)
    assert str(err) == "<unprintable _Unprintable>"
    assert err.args == (bad,)
    assert isinstance(err, (ConfigurationError, RuntimeError))
