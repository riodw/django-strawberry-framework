"""Tests for ``django_strawberry_framework/orders/base.py`` (Slice 1).

Covers the ``RelatedOrder`` primitive: class / absolute-import / unqualified
target resolution through the shared ``LazyRelatedClassMixin``, the
``bind_orderset`` idempotency contract, and the spec-028 Revision 4 H1
rule that the mixin's home is the neutral ``sets_mixins`` module (NOT
``filters/base.py``).
"""

from __future__ import annotations

import pytest

from django_strawberry_framework import sets_mixins
from django_strawberry_framework.orders import OrderSet, RelatedOrder


class AOrder(OrderSet):
    """Minimal ``OrderSet`` subclass used as a resolution target."""


class BOrder(OrderSet):
    """Sibling ``OrderSet`` declared in the same module as ``AOrder``.

    Used by the unqualified-string resolution test: the
    ``LazyRelatedClassMixin`` falls back to
    ``bound_orderset.__module__`` when the absolute import fails, so an
    unqualified ``"AOrder"`` should resolve here.
    """


def test_related_order_accepts_class_reference():
    """Pass an ``OrderSet`` class directly; ``.orderset`` returns it untouched."""
    related = RelatedOrder(AOrder, field_name="a")
    assert related.orderset is AOrder


def test_related_order_accepts_absolute_import_path_string():
    """Pass a fully-qualified path; ``LazyRelatedClassMixin`` resolves it."""
    related = RelatedOrder(
        "tests.orders.test_base.AOrder",
        field_name="a",
    )

    class Owner(OrderSet):
        a = related

    # The metaclass binds the owner; the property triggers Layer-2 lookup.
    assert Owner.a.orderset is AOrder


def test_related_order_accepts_unqualified_name_in_same_module():
    """Unqualified strings resolve against ``bound_orderset.__module__``.

    The first ``import_string`` attempt fails (no absolute module
    ``"AOrder"`` exists); the mixin's fallback prefixes with the owning
    class's module and succeeds.
    """

    class Owner(OrderSet):
        a = RelatedOrder("AOrder", field_name="a")

    assert Owner.a.orderset is AOrder


def test_related_order_unresolved_target_raises_importerror_through_lazy_mixin():
    """Unresolvable strings surface the raw ``ImportError`` from the mixin.

    Pins the contract Slice 3's ``_bind_ordersets`` subpass depends on
    - the finalizer rewraps this ``ImportError`` as ``ConfigurationError``
    with a typed message; Slice 1's primitive raises the underlying
    error unchanged so the finalizer's wrap is observable.
    """

    class Owner(OrderSet):
        a = RelatedOrder("NotAnOrderSet", field_name="a")

    with pytest.raises(ImportError):
        _ = Owner.a.orderset


def test_related_order_bind_orderset_is_idempotent():
    """A second ``bind_orderset`` call does not clobber the first binding."""
    related = RelatedOrder(AOrder, field_name="a")
    related.bind_orderset(AOrder)
    related.bind_orderset(BOrder)  # second call is a no-op.
    assert related.bound_orderset is AOrder


def test_related_order_imports_lazy_mixin_from_sets_mixins_not_filters_base():
    """The mixin in ``RelatedOrder.__mro__`` is the neutral one (spec-028 H1).

    Re-coupling to ``filters.base`` would force the order subsystem to
    drag the entire filter module into its import graph; the neutral
    ``sets_mixins`` home keeps the Layer-3 packages independent.
    """
    assert sets_mixins.LazyRelatedClassMixin in RelatedOrder.__mro__
    # The mixin lives in the neutral module - confirm by source file.
    mixin = next(base for base in RelatedOrder.__mro__ if base.__name__ == "LazyRelatedClassMixin")
    assert mixin.__module__ == "django_strawberry_framework.sets_mixins"


# ---------------------------------------------------------------------------
# Slice 3 -- Meta.orderset_class promotion + validator surface
# ---------------------------------------------------------------------------


def test_meta_orderset_class_is_in_allowed_meta_keys():
    """``"orderset_class"`` is now in ``ALLOWED_META_KEYS`` (spec-028 Slice 3)."""
    from django_strawberry_framework.types.base import ALLOWED_META_KEYS

    assert "orderset_class" in ALLOWED_META_KEYS


def test_meta_orderset_class_is_not_in_deferred_meta_keys():
    """``"orderset_class"`` has been promoted out of ``DEFERRED_META_KEYS``."""
    from django_strawberry_framework.types.base import DEFERRED_META_KEYS

    assert "orderset_class" not in DEFERRED_META_KEYS


def test_validate_orderset_class_returns_none_for_missing_value():
    """The validator short-circuits to ``None`` when ``Meta.orderset_class`` is absent."""
    from django_strawberry_framework.types.base import _validate_orderset_class

    class FakeMeta:
        model = type("FakeModel", (), {})

    assert _validate_orderset_class(FakeMeta, None) is None


def test_validate_orderset_class_accepts_order_set_subclass():
    """The validator returns the class unchanged when it's an ``OrderSet`` subclass."""
    from django_strawberry_framework.types.base import _validate_orderset_class

    class MyOrder(OrderSet):
        pass

    class FakeMeta:
        model = type("FakeModel", (), {})

    assert _validate_orderset_class(FakeMeta, MyOrder) is MyOrder


def test_validate_orderset_class_rejects_non_order_set():
    """The validator raises ``ConfigurationError`` for non-``OrderSet`` types."""
    import pytest as _pytest

    from django_strawberry_framework.exceptions import ConfigurationError
    from django_strawberry_framework.types.base import _validate_orderset_class

    class NotAnOrderSet:
        pass

    class FakeMeta:
        model = type("FakeModel", (), {})

    with _pytest.raises(ConfigurationError) as exc_info:
        _validate_orderset_class(FakeMeta, NotAnOrderSet)
    msg = str(exc_info.value)
    assert "OrderSet subclass" in msg
    assert "FakeModel" in msg
    assert "NotAnOrderSet" in msg


def test_validate_orderset_class_uses_local_import():
    """The ``OrderSet`` import lives inside the function body (spec-028 N3 of rev1)."""
    import inspect

    import django_strawberry_framework.types.base as base_mod

    # Module-top namespace must NOT expose ``OrderSet`` -- the validator
    # imports it locally to dodge the ``types -> orders -> types``
    # module-load cycle.
    assert "OrderSet" not in vars(base_mod)
    src = inspect.getsource(base_mod._validate_orderset_class)
    assert "from ..orders.sets import OrderSet" in src


# ---------------------------------------------------------------------------
# Pass-2 B1 coverage closure -- RelatedOrder.orderset setter
# ---------------------------------------------------------------------------


def test_related_order_orderset_setter_assigns_underscore_orderset():
    """Closes ``orders/base.py:82`` -- ``@orderset.setter`` body.

    The setter mutates ``self._orderset``. Re-assignment via the property
    setter is the cookbook contract that lets a caller substitute the
    target after construction (e.g., the lazy-resolution cache write at
    ``RelatedOrder.orderset.fget`` re-stores the resolved class through
    this setter).
    """
    related = RelatedOrder(AOrder, field_name="a")
    related.orderset = BOrder
    assert related._orderset is BOrder
