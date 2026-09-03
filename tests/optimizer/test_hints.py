"""OptimizerHint tests for Meta.optimizer_hints normalization and validation.

Covers the SKIP sentinel, the three factory classmethods, frozen
immutability, and the identity/equality contracts consumers and the
walker will rely on.
"""

import pytest
from django.db.models import Prefetch

from django_strawberry_framework.optimizer.hints import OptimizerHint


class TestSkipSentinel:
    """``OptimizerHint.SKIP`` is a singleton-like frozen sentinel."""

    def test_skip_is_an_optimizer_hint(self) -> None:
        """The sentinel is an ``OptimizerHint`` instance."""
        assert isinstance(OptimizerHint.SKIP, OptimizerHint)

    def test_skip_has_skip_flag_true(self) -> None:
        """The sentinel's ``skip`` attribute is ``True``."""
        assert OptimizerHint.SKIP.skip is True

    def test_skip_has_no_other_flags(self) -> None:
        """No force or prefetch flags are set on SKIP."""
        assert OptimizerHint.SKIP.force_select is False
        assert OptimizerHint.SKIP.force_prefetch is False
        assert OptimizerHint.SKIP.prefetch_obj is None

    def test_skip_identity_stable(self) -> None:
        """``SKIP`` is the same object across accesses."""
        assert OptimizerHint.SKIP is OptimizerHint.SKIP

    def test_skip_equality(self) -> None:
        """A fresh ``OptimizerHint(skip=True)`` equals the sentinel."""
        assert OptimizerHint(skip=True) == OptimizerHint.SKIP


class TestSelectRelatedFactory:
    """``OptimizerHint.select_related()`` forces select_related."""

    def test_force_select_flag(self) -> None:
        """The hint has ``force_select=True``."""
        hint = OptimizerHint.select_related()
        assert hint.force_select is True

    def test_no_other_flags(self) -> None:
        """No skip, prefetch, or prefetch_obj flags."""
        hint = OptimizerHint.select_related()
        assert hint.skip is False
        assert hint.force_prefetch is False
        assert hint.prefetch_obj is None


class TestPrefetchRelatedFactory:
    """``OptimizerHint.prefetch_related()`` forces prefetch_related."""

    def test_force_prefetch_flag(self) -> None:
        """The hint has ``force_prefetch=True``."""
        hint = OptimizerHint.prefetch_related()
        assert hint.force_prefetch is True

    def test_no_other_flags(self) -> None:
        """No skip, select, or prefetch_obj flags."""
        hint = OptimizerHint.prefetch_related()
        assert hint.skip is False
        assert hint.force_select is False
        assert hint.prefetch_obj is None


class TestPrefetchFactory:
    """``OptimizerHint.prefetch(obj)`` carries a specific Prefetch object."""

    def test_prefetch_obj_stored(self) -> None:
        """The ``Prefetch`` object is stored on the hint."""
        pf = Prefetch("items")
        hint = OptimizerHint.prefetch(pf)
        assert hint.prefetch_obj is pf

    def test_no_other_flags(self) -> None:
        """No skip, select, or prefetch flags."""
        hint = OptimizerHint.prefetch(Prefetch("items"))
        assert hint.skip is False
        assert hint.force_select is False
        assert hint.force_prefetch is False

    def test_none_rejected(self) -> None:
        """``None`` must not collapse into the empty no-op hint."""
        from django_strawberry_framework.exceptions import ConfigurationError

        with pytest.raises(ConfigurationError, match="Prefetch"):
            OptimizerHint.prefetch(None)  # type: ignore[arg-type]


class TestStrategyFactory:
    """``OptimizerHint.strategy(name)`` overrides the nested-connection strategy."""

    def test_stores_name(self) -> None:
        """The factory carries the strategy name on ``nested_strategy``."""
        hint = OptimizerHint.strategy("windowed")
        assert hint.nested_strategy == "windowed"

    def test_no_other_flags(self) -> None:
        """No skip / select / prefetch flags come along for the ride."""
        hint = OptimizerHint.strategy("lateral")
        assert hint.skip is False
        assert hint.force_select is False
        assert hint.force_prefetch is False
        assert hint.prefetch_obj is None

    def test_default_hint_has_no_strategy(self) -> None:
        """An unspecified ``nested_strategy`` stays ``None``."""
        assert OptimizerHint().nested_strategy is None
        assert OptimizerHint.SKIP.nested_strategy is None

    def test_accepts_lateral_and_auto(self) -> None:
        """``lateral`` and ``auto`` are registered / resolvable names."""
        assert OptimizerHint.strategy("lateral").nested_strategy == "lateral"
        assert OptimizerHint.strategy("auto").nested_strategy == "auto"

    def test_force_prefetch_is_redundant_but_allowed(self) -> None:
        """``force_prefetch`` + ``nested_strategy`` is redundant, not rejected."""
        hint = OptimizerHint(force_prefetch=True, nested_strategy="windowed")
        assert hint.nested_strategy == "windowed"
        assert hint.force_prefetch is True

    def test_none_rejected(self) -> None:
        """``None`` must not collapse into the empty no-op hint."""
        from django_strawberry_framework.exceptions import ConfigurationError

        with pytest.raises(ConfigurationError, match="strategy name"):
            OptimizerHint.strategy(None)  # type: ignore[arg-type]

    def test_bad_name_raises_at_construction(self) -> None:
        """A typo'd strategy name fails loud through ``resolve_strategy``."""
        from django_strawberry_framework.exceptions import ConfigurationError

        with pytest.raises(ConfigurationError, match="Unknown nested_connection_strategy"):
            OptimizerHint.strategy("winowed")
        with pytest.raises(ConfigurationError, match="Unknown nested_connection_strategy"):
            OptimizerHint(nested_strategy="not-a-strategy")

    def test_strategy_with_skip_raises(self) -> None:
        from django_strawberry_framework.exceptions import ConfigurationError

        with pytest.raises(ConfigurationError, match="nested_strategy"):
            OptimizerHint(skip=True, nested_strategy="windowed")

    def test_strategy_with_force_select_raises(self) -> None:
        from django_strawberry_framework.exceptions import ConfigurationError

        with pytest.raises(ConfigurationError, match="nested_strategy"):
            OptimizerHint(force_select=True, nested_strategy="windowed")

    def test_strategy_with_prefetch_obj_raises(self) -> None:
        from django_strawberry_framework.exceptions import ConfigurationError

        with pytest.raises(ConfigurationError, match="nested_strategy"):
            OptimizerHint(prefetch_obj=Prefetch("items"), nested_strategy="windowed")

    def test_strategy_rejects_hostile_type_name_safely(self) -> None:
        """A hostile metaclass cannot replace the typed strategy rejection."""

        class HostileType(type):
            @property
            def __name__(cls):
                raise RuntimeError("type name should never run")

        class NotStrategy(metaclass=HostileType):
            pass

        from django_strawberry_framework.exceptions import ConfigurationError

        with pytest.raises(ConfigurationError, match="nested_connection_strategy"):
            OptimizerHint.strategy(NotStrategy())  # type: ignore[arg-type]

    def test_strategy_rejects_class_with_clean_name(self) -> None:
        """Passing a strategy class instead of an instance names the class, not 'type'."""
        from django_strawberry_framework.exceptions import ConfigurationError
        from django_strawberry_framework.optimizer.nested_fetch import (
            WindowedPrefetchStrategy,
        )

        with pytest.raises(ConfigurationError, match="WindowedPrefetchStrategy"):
            OptimizerHint.strategy(WindowedPrefetchStrategy)  # type: ignore[arg-type]

    def test_strategy_hostile_selection_values_stay_typed(self) -> None:
        """A hostile selection value cannot replace the typed strategy rejection.

        The typed contract is owned by ``resolve_strategy`` itself: its
        dunder reads are guarded (the ``__eq__`` check reads through the
        base ``str`` slot, the registry lookup absorbs a raising
        ``__hash__``, the message renders through ``_safe_arg_repr``, and a
        raising ``plan`` attribute reads as "not a strategy"), so a hostile
        value degrades to the typed ``ConfigurationError`` raised directly -
        no raw exception escapes, and the hint boundary needs no containment.
        """
        from django_strawberry_framework.exceptions import ConfigurationError
        from django_strawberry_framework.optimizer.nested_fetch import (
            WINDOWED_STRATEGY,
            resolve_strategy,
        )

        class HostileRepr(str):
            def __repr__(self):
                raise RuntimeError("repr should never run")

        class HostileEq(str):
            def __eq__(self, other):
                raise RuntimeError("eq should never run")

            def __hash__(self):
                return str.__hash__(self)

        class HostileHash(str):
            def __hash__(self):
                raise RuntimeError("hash should never run")

        class HostileGetattr:
            def __getattr__(self, name):
                raise RuntimeError("getattr should never run")

        # Unknown names raise the unknown-name rejection rendered safely.
        for hostile in (HostileRepr("winowed"), HostileHash("winowed")):
            with pytest.raises(ConfigurationError, match="Unknown nested_connection_strategy"):
                OptimizerHint.strategy(hostile)  # type: ignore[arg-type]
            with pytest.raises(ConfigurationError, match="Unknown nested_connection_strategy"):
                OptimizerHint(nested_strategy=hostile)  # type: ignore[arg-type]
        # A raising ``__getattr__`` reads as "not a strategy", typed the same way.
        with pytest.raises(ConfigurationError, match="must be a strategy name"):
            OptimizerHint.strategy(HostileGetattr())  # type: ignore[arg-type]
        # Content decides through the base ``str`` slot: a hostile ``__eq__``
        # can neither force a false AUTO_STRATEGY match nor break a valid name.
        # (Even the assertion reads through the base slot - ``==`` on the
        # carried instance would dispatch back into the hostile override.)
        carried = OptimizerHint.strategy(HostileEq("windowed")).nested_strategy
        assert str.__eq__(carried, "windowed") is True
        assert resolve_strategy(HostileEq("windowed")) is WINDOWED_STRATEGY

    def test_strategy_hostile_rejection_is_raised_directly(self) -> None:
        """The typed rejection needs no containment chain: nothing escapes first."""
        from django_strawberry_framework.exceptions import ConfigurationError

        class HostileHash(str):
            def __hash__(self):
                raise RuntimeError("hash should never run")

        with pytest.raises(
            ConfigurationError,
            match="Unknown nested_connection_strategy",
        ) as exc_info:
            OptimizerHint.strategy(HostileHash("winowed"))  # type: ignore[arg-type]
        assert exc_info.value.__cause__ is None

    def test_public_annotations_resolve_at_runtime(self) -> None:
        """``typing.get_type_hints(OptimizerHint)`` resolves ``StrategySelection``.

        The public dataclass annotates ``nested_strategy`` (and the
        ``strategy()`` factory) with ``StrategySelection``, whose name must live
        in ``hints``' runtime globals so a docs generator / runtime-validation
        library / IDE bridge doing an ordinary ``get_type_hints`` introspection
        (no custom ``globalns``) does not hit ``NameError``. Regression against
        the ``TYPE_CHECKING``-only import that resolved for static checkers but
        left the postponed annotation unevaluable at runtime.
        """
        import typing

        from django_strawberry_framework.optimizer.nested_fetch import (
            NestedConnectionStrategy,
        )

        resolved = typing.get_type_hints(OptimizerHint)
        assert resolved["nested_strategy"] == (str | NestedConnectionStrategy | None)
        # The factory signature resolves too (no custom globalns workaround).
        factory_hints = typing.get_type_hints(OptimizerHint.strategy)
        assert factory_hints["name"] == (str | NestedConnectionStrategy)


class TestFrozenImmutability:
    """Hints are frozen dataclasses - mutation raises."""

    def test_cannot_mutate_skip(self) -> None:
        """Attempting to set an attribute raises ``FrozenInstanceError``."""
        hint = OptimizerHint.select_related()
        with pytest.raises(AttributeError):
            hint.force_select = False  # type: ignore[misc]

    def test_skip_sentinel_cannot_be_mutated(self) -> None:
        """The SKIP sentinel is also frozen."""
        with pytest.raises(AttributeError):
            OptimizerHint.SKIP.skip = False  # type: ignore[misc]


class TestEquality:
    """Frozen dataclass equality works as expected."""

    def test_same_factory_produces_equal_hints(self) -> None:
        """Two ``select_related()`` calls produce equal hints."""
        assert OptimizerHint.select_related() == OptimizerHint.select_related()

    def test_different_factories_not_equal(self) -> None:
        """``select_related()`` != ``prefetch_related()``."""
        assert OptimizerHint.select_related() != OptimizerHint.prefetch_related()

    def test_prefetch_with_different_objects_not_equal(self) -> None:
        """Two prefetch hints with different objects are not equal."""
        assert OptimizerHint.prefetch(Prefetch("a")) != OptimizerHint.prefetch(Prefetch("b"))


class TestInvalidStatesRejected:
    """``__post_init__`` rejects states the walker would silently misread.

    Pins the Medium fix from ``rev-optimizer__hints.md``: combining flags
    beyond the four directives and the empty no-op form lets the walker's
    priority order silently swallow the lower-priority directive. Each
    rejected state raises ``ConfigurationError`` at construction time.
    """

    def test_non_bool_flags_raise(self) -> None:
        """Truthy and falsy non-booleans must not control dispatch."""
        from django_strawberry_framework.exceptions import ConfigurationError

        for kwargs in ({"force_select": 1}, {"force_prefetch": ""}, {"skip": "false"}):
            with pytest.raises(ConfigurationError, match="bool values"):
                OptimizerHint(**kwargs)  # type: ignore[arg-type]

    def test_skip_with_force_select_raises(self) -> None:
        from django_strawberry_framework.exceptions import ConfigurationError

        with pytest.raises(ConfigurationError, match="skip=True"):
            OptimizerHint(skip=True, force_select=True)

    def test_skip_with_force_prefetch_raises(self) -> None:
        from django_strawberry_framework.exceptions import ConfigurationError

        with pytest.raises(ConfigurationError, match="skip=True"):
            OptimizerHint(skip=True, force_prefetch=True)

    def test_skip_with_prefetch_obj_raises(self) -> None:
        from django_strawberry_framework.exceptions import ConfigurationError

        with pytest.raises(ConfigurationError, match="skip=True"):
            OptimizerHint(skip=True, prefetch_obj=Prefetch("items"))

    def test_force_select_with_force_prefetch_raises(self) -> None:
        from django_strawberry_framework.exceptions import ConfigurationError

        with pytest.raises(ConfigurationError, match="force_select and force_prefetch"):
            OptimizerHint(force_select=True, force_prefetch=True)

    def test_prefetch_obj_with_force_select_raises(self) -> None:
        from django_strawberry_framework.exceptions import ConfigurationError

        with pytest.raises(ConfigurationError, match="prefetch_obj"):
            OptimizerHint(prefetch_obj=Prefetch("items"), force_select=True)

    def test_prefetch_obj_with_force_prefetch_raises(self) -> None:
        from django_strawberry_framework.exceptions import ConfigurationError

        with pytest.raises(ConfigurationError, match="prefetch_obj"):
            OptimizerHint(prefetch_obj=Prefetch("items"), force_prefetch=True)

    def test_prefetch_obj_rejects_non_prefetch_value(self) -> None:
        """Pins ``rev-optimizer__hints.md`` Medium: ``prefetch(obj)`` must
        receive a ``Prefetch`` instance; the previous ``obj: Any`` factory
        signature let strings or other shapes through ``__post_init__`` and
        crash later in the walker.  Reject at construction time instead.
        """
        from django_strawberry_framework.exceptions import ConfigurationError

        with pytest.raises(ConfigurationError, match="Prefetch"):
            OptimizerHint.prefetch("entries__items")  # type: ignore[arg-type]
        with pytest.raises(ConfigurationError, match="Prefetch"):
            OptimizerHint(prefetch_obj="entries__items")  # type: ignore[arg-type]

    def test_prefetch_obj_rejects_hostile_type_name_safely(self) -> None:
        """A hostile metaclass cannot replace the typed Prefetch rejection."""

        class HostileType(type):
            @property
            def __name__(cls):
                raise RuntimeError("type name should never run")

        class NotPrefetch(metaclass=HostileType):
            pass

        from django_strawberry_framework.exceptions import ConfigurationError

        with pytest.raises(ConfigurationError, match="Prefetch"):
            OptimizerHint.prefetch(NotPrefetch())  # type: ignore[arg-type]


class TestSkipPredicate:
    """``hint_is_skip`` keeps schema-audit dispatch fail-closed."""

    def test_hostile_skip_shapes_return_false(self) -> None:
        """Unexpected hint objects cannot break a never-raise schema audit."""
        from django_strawberry_framework.optimizer.hints import hint_is_skip

        class HostileAttribute:
            @property
            def skip(self):
                raise RuntimeError("skip should never run")

        class HostileBoolean:
            def __bool__(self):
                raise RuntimeError("bool should never run")

        class HostileValue:
            skip = HostileBoolean()

        assert hint_is_skip(HostileAttribute()) is False
        assert hint_is_skip(HostileValue()) is False
