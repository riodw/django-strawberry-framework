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


def test_class_based_type_name_mixin():
    import pytest

    from django_strawberry_framework.exceptions import ConfigurationError
    from django_strawberry_framework.sets_mixins import ClassBasedTypeNameMixin

    class _SampleSet(ClassBasedTypeNameMixin):
        _root_type_suffix = "RootType"
        _field_type_suffix = "FieldType"

    assert _SampleSet.type_name_for() == "_SampleSetRootType"
    assert _SampleSet.type_name_for("author__name") == "_SampleSetAuthorNameFieldType"
    assert _SampleSet.type_name_for("book_title") == "_SampleSetBookTitleFieldType"

    with pytest.raises(ConfigurationError, match="contains no word characters"):
        _SampleSet.type_name_for("")

    with pytest.raises(ConfigurationError, match="contains no word characters"):
        _SampleSet.type_name_for("__")


class _ModuleScopedTargetClass:
    pass


class _BoundScope:
    pass


def test_lazy_related_class_mixin():
    import pytest

    from django_strawberry_framework.sets_mixins import LazyRelatedClassMixin

    mixin = LazyRelatedClassMixin()
    # Class object passed through
    assert mixin.resolve_lazy_class(_ModuleScopedTargetClass, None) is _ModuleScopedTargetClass

    # Callable factory invoked
    assert (
        mixin.resolve_lazy_class(lambda: _ModuleScopedTargetClass, None)
        is _ModuleScopedTargetClass
    )

    # Absolute import string resolved
    resolved = mixin.resolve_lazy_class("django.db.models.Model", None)
    from django.db.models import Model

    assert resolved is Model

    # Relative import string with bound_class
    resolved_local = mixin.resolve_lazy_class("_ModuleScopedTargetClass", _BoundScope)
    assert resolved_local is _ModuleScopedTargetClass

    # Failing import without bound_class raises ImportError
    with pytest.raises(ImportError):
        mixin.resolve_lazy_class("NonExistentDottedPathClass", None)


def test_related_set_target_mixin():
    from django_strawberry_framework.sets_mixins import RelatedSetTargetMixin

    class _TargetStub:
        pass

    class _AlternativeStub:
        pass

    class _RelatedItem(RelatedSetTargetMixin):
        _target_attr = "_target"
        _owner_attr = "bound_owner"

        def __init__(self, target):
            self._target = target

    class _OwnerOne:
        pass

    class _OwnerTwo:
        pass

    item = _RelatedItem(_TargetStub)
    # First bind records owner
    item._bind_owner(_OwnerOne)
    assert item.bound_owner is _OwnerOne

    # Second bind is idempotent no-op
    item._bind_owner(_OwnerTwo)
    assert item.bound_owner is _OwnerOne

    # Resolved target returns resolved class
    assert item._resolved_target() is _TargetStub

    # _set_target updates target slot
    item._set_target(_AlternativeStub)
    assert item._resolved_target() is _AlternativeStub


def test_collect_related_declarations():
    from django_strawberry_framework.sets_mixins import (
        RelatedSetTargetMixin,
        collect_related_declarations,
    )

    class _Decl(RelatedSetTargetMixin):
        _target_attr = "_t"
        _owner_attr = "_o"

    class _BaseA:
        related_items = {"alpha": _Decl(), "beta": _Decl()}

    class _BaseB(_BaseA):
        pass

    class _NewCls:
        pass

    # inherit_from_bases=True merges base declarations and own items
    own_override = _Decl()
    collected = collect_related_declarations(
        _NewCls,
        (_BaseB,),
        own_items=[("beta", own_override), ("gamma", _Decl()), ("alpha", None)],
        declaration_type=_Decl,
        collection_attr="related_items",
        inherit_from_bases=True,
    )
    assert "alpha" not in collected
    assert collected["beta"] is own_override
    assert "gamma" in collected
    assert _NewCls.related_items is collected


def test_expanded_once():
    from django_strawberry_framework.sets_mixins import expanded_once

    class _ProbeSet:
        pass

    # If cached, returns cached without calling build
    _ProbeSet._cache = {"cached": True}
    res = expanded_once(
        _ProbeSet,
        cache_attr="_cache",
        guard_attr="_guard",
        build=lambda: {"cached": False},
    )
    assert res == {"cached": True}

    # If not cached, executes build under guard
    class _UncachedSet:
        pass

    def _build_fn():
        assert getattr(_UncachedSet, "_guard", False) is True
        return {"built": True}

    res2 = expanded_once(
        _UncachedSet,
        cache_attr="_cache",
        guard_attr="_guard",
        build=_build_fn,
    )
    assert res2 == {"built": True}
    assert getattr(_UncachedSet, "_guard", False) is False

    # Reentry fallback when mid-expansion
    class _CycleSet:
        _guard = True

    res3 = expanded_once(
        _CycleSet,
        cache_attr="_cache",
        guard_attr="_guard",
        build=lambda: {"never": True},
        on_reentry=lambda: {"fallback": True},
    )
    assert res3 == {"fallback": True}


def test_set_lifecycle_attrs():
    from django_strawberry_framework.sets_mixins import SetLifecycleAttrs

    lifecycle = SetLifecycleAttrs(
        owner="_owner",
        cache="_cache",
        guard="_guard",
        extra=("_extra1", "_extra2"),
    )
    assert lifecycle.owner == "_owner"
    assert lifecycle.cache == "_cache"
    assert lifecycle.guard == "_guard"
    assert lifecycle.extra == ("_extra1", "_extra2")
    assert lifecycle.binding_attrs == ("_owner", "_cache", "_guard", "_extra1", "_extra2")


def test_active_input_permission_mixin_hooks():
    from django_strawberry_framework.sets_mixins import (
        ActiveInputPermissionAttrs,
        ActiveInputPermissionMixin,
    )

    class _ProbePermissionSet(ActiveInputPermissionMixin):
        _permission = ActiveInputPermissionAttrs(
            family_label="Probe",
            related_attr="related_probe",
            target_attr="probe",
            field_specs={},
            unset_sentinel=None,
        )

    # Hooks execute cleanly as no-ops
    _ProbePermissionSet._prepare_permission_input(None)
    _ProbePermissionSet._check_permission_depth(0)
    _ProbePermissionSet._run_logic_permission_checks(
        None,
        None,
        _fired={},
        _bare=None,
        _depth=0,
    )

    # _run_permission_checks short-circuits on inactive input value
    _ProbePermissionSet._run_permission_checks(None, None)
