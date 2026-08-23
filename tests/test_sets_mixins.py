"""Pins for set-family mixins shared by ``FilterSet`` and ``OrderSet``.

The spec-027 / spec-028 Decision 8 permission facade lives on ``ActiveInputPermissionMixin``;
family apply pipelines stay distinct (visibility/form vs ``order_by``).
"""

from django_strawberry_framework.filters import FilterSet
from django_strawberry_framework.orders import OrderSet
from django_strawberry_framework.sets_mixins import ActiveInputPermissionMixin

_SHARED_PERMISSION_METHODS = (
    "_request_from_info",
    "_extract_branch_value",
    "_iter_active_related_branches",
    "_invoke_permission_method",
    "_active_permission_field_paths",
    "_active_permission_targets",
    "_run_permission_checks",
)


def _unbound(owner: type, name: str):
    attr = getattr(owner, name)
    return getattr(attr, "__func__", attr)


def test_filterset_and_orderset_share_active_input_permission_mixin():
    assert ActiveInputPermissionMixin in FilterSet.__mro__
    assert ActiveInputPermissionMixin in OrderSet.__mro__


def test_permission_facade_methods_are_single_sourced_on_the_mixin():
    for name in _SHARED_PERMISSION_METHODS:
        mixin_fn = _unbound(ActiveInputPermissionMixin, name)
        assert _unbound(FilterSet, name) is mixin_fn
        assert _unbound(OrderSet, name) is mixin_fn


def test_permission_family_config_stays_on_each_set_class():
    assert FilterSet._permission.family_label == "FilterSet"
    assert FilterSet._permission.related_attr == "related_filters"
    assert FilterSet._permission.target_attr == "filterset"
    assert FilterSet._permission.handle_top_level_list is False
    assert OrderSet._permission.family_label == "OrderSet"
    assert OrderSet._permission.related_attr == "related_orders"
    assert OrderSet._permission.target_attr == "orderset"
    assert OrderSet._permission.handle_top_level_list is True


def test_permission_fallback_path_is_the_family_remap_hook():
    assert FilterSet._permission_fallback_path("i_contains") == "icontains"
    assert OrderSet._permission_fallback_path("i_contains") == "i_contains"


def test_apply_pipelines_remain_family_owned():
    assert _unbound(FilterSet, "apply_sync") is not _unbound(OrderSet, "apply_sync")
    assert _unbound(FilterSet, "apply_async") is not _unbound(OrderSet, "apply_async")


def test_sets_mixins_all_exports_are_complete():
    import django_strawberry_framework.sets_mixins as sm

    assert "should_cache_expansion" in sm.__all__
    for symbol in sm.__all__:
        assert hasattr(sm, symbol), f"Symbol {symbol!r} in __all__ but not in sets_mixins"


def test_should_cache_expansion_gates_on_dict_and_unresolved_strings():
    import types

    from django_strawberry_framework.sets_mixins import should_cache_expansion

    class _MockTarget:
        pass

    class _BaseSet:
        related_items = {}

    # Inherited related_items (not in __dict__) fails gate
    class _InheritedSet(_BaseSet):
        pass

    assert (
        should_cache_expansion(
            _InheritedSet,
            related_attr="related_items",
            target_slot="_target",
        )
        is False
    )

    # Own related_items with unresolved string target fails gate
    class _UnresolvedSet:
        related_items = {
            "rel": types.SimpleNamespace(_target="some.unresolved.String"),
        }

    assert (
        should_cache_expansion(
            _UnresolvedSet,
            related_attr="related_items",
            target_slot="_target",
        )
        is False
    )

    # Own related_items with resolved class target passes gate
    class _ResolvedSet:
        related_items = {
            "rel": types.SimpleNamespace(_target=_MockTarget),
        }

    assert (
        should_cache_expansion(
            _ResolvedSet,
            related_attr="related_items",
            target_slot="_target",
        )
        is True
    )
