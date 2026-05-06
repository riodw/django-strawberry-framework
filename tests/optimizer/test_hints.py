"""Tests for ``OptimizerHint`` — the typed wrapper for ``Meta.optimizer_hints``.

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


class TestFrozenImmutability:
    """Hints are frozen dataclasses — mutation raises."""

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


class TestConflictingFlagsRejected:
    """``__post_init__`` rejects flag combinations the walker would silently drop.

    Pins the Medium fix from ``rev-optimizer__hints.md``: combining flags
    beyond the documented four shapes (``SKIP``, ``select_related()``,
    ``prefetch_related()``, ``prefetch(obj)``) lets the walker's priority
    order silently swallow the lower-priority directive.  Each rejected
    combination raises ``ConfigurationError`` at construction time.
    """

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
