"""RelatedOrder binding and lazy-resolution tests plus Meta.orderset_class promotion and validation.

Covers the ``RelatedOrder`` primitive: class / absolute-import / unqualified
target resolution through the shared ``LazyRelatedClassMixin``, the
``bind_orderset`` idempotency contract, and the spec-028 rule that the
mixin's home is the neutral ``sets_mixins`` module (NOT ``filters/base.py``).
Also covers the target-type gate: a target that RESOLVES to a non-``OrderSet``
(the cross-family ``FilterSet``, a plain class, or a factory returning a
non-class) raises ``ConfigurationError`` at the ``.orderset`` read instead of
surviving until the BFS input builder detonates on it.
"""

from __future__ import annotations

import pytest

from django_strawberry_framework import sets_mixins
from django_strawberry_framework.exceptions import ConfigurationError
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

    Pins the contract the finalizer's ``_bind_ordersets`` subpass depends on
    - the finalizer rewraps this ``ImportError`` as ``ConfigurationError``
    with a typed message; the primitive raises the underlying
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
    """The mixin in ``RelatedOrder.__mro__`` is the neutral one (spec-028).

    Re-coupling to ``filters.base`` would force the order subsystem to
    drag the entire filter module into its import graph; the neutral
    ``sets_mixins`` home keeps the Layer-3 packages independent.
    """
    assert sets_mixins.LazyRelatedClassMixin in RelatedOrder.__mro__
    # The mixin lives in the neutral module - confirm by source file.
    mixin = next(base for base in RelatedOrder.__mro__ if base.__name__ == "LazyRelatedClassMixin")
    assert mixin.__module__ == "django_strawberry_framework.sets_mixins"


# ---------------------------------------------------------------------------
# Meta.orderset_class promotion + validator surface
# ---------------------------------------------------------------------------


def test_meta_orderset_class_is_in_allowed_meta_keys():
    """``"orderset_class"`` is now in ``ALLOWED_META_KEYS`` (spec-028)."""
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
    """The ``OrderSet`` import lives inside the function body (spec-028)."""
    import inspect

    import django_strawberry_framework.types.base as base_mod

    # Module-top namespace must NOT expose ``OrderSet`` -- the validator
    # imports it locally to dodge the ``types -> orders -> types``
    # module-load cycle.
    assert "OrderSet" not in vars(base_mod)
    src = inspect.getsource(base_mod._validate_orderset_class)
    assert "from ..orders.sets import OrderSet" in src


# ---------------------------------------------------------------------------
# RelatedOrder.orderset setter
# ---------------------------------------------------------------------------


def test_related_order_orderset_setter_assigns_underscore_orderset():
    """Covers ``orders/base.py::RelatedOrder.orderset`` #"self._set_target(value)".

    The setter delegates to
    ``sets_mixins.py::RelatedSetTargetMixin._set_target``, which assigns
    ``self._orderset``. Re-assignment via the property setter is the
    cookbook contract that lets a caller substitute the target after
    construction (e.g., the lazy-resolution cache write at
    ``RelatedOrder.orderset.fget`` re-stores the resolved class through
    this setter).
    """
    related = RelatedOrder(AOrder, field_name="a")
    related.orderset = BOrder
    assert related._orderset is BOrder


def test_related_order_accepts_callable_factory():
    """Pass a callable factory as target; resolves and caches on first access."""
    invocations = 0

    def factory():
        nonlocal invocations
        invocations += 1
        return AOrder

    related = RelatedOrder(factory, field_name="a")
    assert invocations == 0
    assert related.orderset is AOrder
    assert invocations == 1
    # Subsequent access reads cached class without invoking factory again
    assert related.orderset is AOrder
    assert invocations == 1


def test_related_order_default_field_name_is_none():
    """``field_name`` is optional and defaults to ``None``."""
    related = RelatedOrder(AOrder)
    assert related.field_name is None
    assert related.orderset is AOrder


def test_related_order_unbound_absolute_import_path_resolves():
    """Absolute import string resolves even when ``bound_orderset`` is unset."""
    related = RelatedOrder("tests.orders.test_base.AOrder", field_name="a")
    assert not hasattr(related, "bound_orderset")
    assert related.orderset is AOrder


# ---------------------------------------------------------------------------
# Target-type gate: a RESOLVED target must be None (placeholder) or OrderSet
# ---------------------------------------------------------------------------


class _NotAnOrderSet:
    """A plain class -- legal Python, not an ``OrderSet``."""


def test_related_order_rejects_plain_class_target_with_typed_error():
    """A resolved non-``OrderSet`` class target raises ``ConfigurationError``.

    The gate fires at the ``.orderset`` read -- the one seam every consumer
    (BFS enqueue, input emission, runtime recursion, permission recursion)
    routes through -- naming the owning orderset and the offending target,
    instead of letting the mis-wiring survive until the BFS builder calls
    ``target.type_name_for()`` on it (a raw ``AttributeError`` at finalize
    subpass 4, outside the uniform subpass-2 rewrap).
    """

    class Owner(OrderSet):
        shelf = RelatedOrder(_NotAnOrderSet, field_name="shelf")

    with pytest.raises(ConfigurationError) as exc_info:
        _ = Owner.shelf.orderset
    msg = str(exc_info.value)
    assert "Owner" in msg
    assert "shelf" in msg
    assert "NotAnOrderSet" in msg
    assert "OrderSet subclass" in msg


def test_related_order_rejects_filterset_target():
    """The cross-family twin (``FilterSet``) is rejected, never silently built.

    A ``FilterSet`` carries ``type_name_for`` / a ``get_fields``-shaped
    surface, so without the gate the BFS builder would walk the FILTER
    family's fields into an order input class (or crash on the filter
    objects' missing ``orderset`` attribute) instead of rejecting the
    cross-family mis-wiring at first resolution.
    """
    from django_strawberry_framework.filters import FilterSet

    class ShelfFilter(FilterSet):
        class Meta:
            from apps.library.models import Shelf

            model = Shelf
            fields = ["code"]

    class Owner(OrderSet):
        shelf = RelatedOrder(ShelfFilter, field_name="shelf")

    with pytest.raises(ConfigurationError) as exc_info:
        _ = Owner.shelf.orderset
    msg = str(exc_info.value)
    assert "FilterSet" in msg
    assert "ShelfFilter" in msg


def test_related_order_rejects_factory_returning_non_class():
    """A factory resolving to a non-class is rejected by the same gate."""

    class Owner(OrderSet):
        shelf = RelatedOrder(lambda: object(), field_name="shelf")

    with pytest.raises(ConfigurationError) as exc_info:
        _ = Owner.shelf.orderset
    assert "object" in str(exc_info.value)


def test_related_order_target_gate_names_unbound_owner():
    """A never-bound declaration reports ``<unbound>`` as its owner label."""
    related = RelatedOrder(_NotAnOrderSet, field_name="a")
    with pytest.raises(ConfigurationError) as exc_info:
        _ = related.orderset
    assert "<unbound>" in str(exc_info.value)


def test_related_order_none_placeholder_target_still_reads_none():
    """The ``RelatedOrder(None, ...)`` placeholder keeps its skip-silently read."""
    related = RelatedOrder(None, field_name="shelf")
    assert related.orderset is None


def test_related_order_target_gate_preserves_importerror_for_unresolved_strings():
    """The gate fires AFTER string resolution: unresolvable strings stay ``ImportError``.

    Pins the finalizer's subpass-2 contract -- the rewrap keys on the raw
    ``ImportError`` (``__cause__`` preserved), which the gate must not
    preempt or replace.
    """

    class Owner(OrderSet):
        a = RelatedOrder("NoSuchOrderAnywhereXYZ", field_name="a")

    with pytest.raises(ImportError):
        _ = Owner.a.orderset
