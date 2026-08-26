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
    assert lifecycle.binding_attrs == (
        "_owner",
        "_cache",
        "_guard",
        "_extra1",
        "_extra2",
    )


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


def test_lazy_related_class_mixin_fallback_and_non_class_types():
    import pytest

    from django_strawberry_framework.sets_mixins import LazyRelatedClassMixin

    class _Scope:
        pass

    mixin = LazyRelatedClassMixin()

    # Non-callable non-string returned as-is
    sentinel = 12345
    assert mixin.resolve_lazy_class(sentinel, None) == sentinel

    # Unresolvable relative import with bound_class raises ImportError
    with pytest.raises(ImportError):
        mixin.resolve_lazy_class("NonExistentSiblingClass12345", _Scope)


def test_expanded_once_resets_guard_on_exception():
    import pytest

    from django_strawberry_framework.sets_mixins import expanded_once

    class _ErrorSet:
        _guard = False

    def _failing_build():
        assert _ErrorSet._guard is True
        raise RuntimeError("simulated expansion error")

    with pytest.raises(RuntimeError, match="simulated expansion error"):
        expanded_once(
            _ErrorSet,
            cache_attr="_cache",
            guard_attr="_guard",
            build=_failing_build,
        )

    # Guard is reset via finally block
    assert _ErrorSet._guard is False


def test_active_input_permission_mixin_delegates_and_fires_checks():
    import types
    from dataclasses import dataclass

    from django_strawberry_framework.sets_mixins import (
        ActiveInputPermissionAttrs,
        ActiveInputPermissionMixin,
    )

    @dataclass
    class _FilterInput:
        title: str = "test"

    class _GatedSet(ActiveInputPermissionMixin):
        _permission = ActiveInputPermissionAttrs(
            family_label="Gated",
            related_attr="related_items",
            target_attr="gated_target",
            field_specs={},
            unset_sentinel=None,
        )
        checked_fields: list[str] = []

        def check_title_permission(self, request):
            self.checked_fields.append("title")

    # Delegate test: request_from_info
    mock_request = object()
    mock_info = types.SimpleNamespace(context=types.SimpleNamespace(request=mock_request))
    assert _GatedSet._request_from_info(mock_info) is mock_request

    # Delegate test: extract_branch_value
    input_obj = _FilterInput(title="custom")
    assert _GatedSet._extract_branch_value(input_obj, "title") == "custom"

    # Delegate test: permission fallback path
    assert _GatedSet._permission_fallback_path("custom_field") == "custom_field"

    # Execution test: run_permission_checks triggers check_title_permission
    _GatedSet._run_permission_checks(input_obj, mock_request)
    assert "title" in _GatedSet.checked_fields


def test_collect_related_declarations_diamond_tombstone():
    from django_strawberry_framework.sets_mixins import (
        RelatedSetTargetMixin,
        collect_related_declarations,
    )

    class _Decl(RelatedSetTargetMixin):
        _target_attr = "_t"
        _owner_attr = "_o"

    class _Root:
        pass

    class _BaseLeft(_Root):
        # Left base has no declaration in its collection map and a class-level tombstone
        related_items = {}
        shared_rel = "tombstone_attribute"

    class _BaseRight(_Root):
        related_items = {"shared_rel": _Decl()}

    class _DiamondSubclass:
        pass

    # Left base comes first in bases list, has a tombstone attribute shadowing the declaration
    collected = collect_related_declarations(
        _DiamondSubclass,
        (_BaseLeft, _BaseRight),
        own_items=[],
        declaration_type=_Decl,
        collection_attr="related_items",
        inherit_from_bases=True,
    )
    # The tombstone on _BaseLeft shadows and removes shared_rel
    assert "shared_rel" not in collected


def test_collect_related_declarations_base_declarations_precedence():
    from django_strawberry_framework.sets_mixins import (
        RelatedSetTargetMixin,
        collect_related_declarations,
    )

    class _Decl(RelatedSetTargetMixin):
        _target_attr = "_t"
        _owner_attr = "_o"

    class _NonDecl:
        pass

    rel_decl = _Decl()
    non_decl = _NonDecl()

    class _BaseWithAllDecls:
        related_items = {"rel_key": rel_decl, "scalar_key": _Decl()}
        all_declarations = {
            "rel_key": rel_decl,
            "scalar_key": non_decl,  # scalar declaration shadows related decl
        }

    class _Subclass:
        pass

    collected = collect_related_declarations(
        _Subclass,
        (_BaseWithAllDecls,),
        own_items=[],
        declaration_type=_Decl,
        collection_attr="related_items",
        base_declarations_attr="all_declarations",
        inherit_from_bases=True,
    )
    assert "rel_key" in collected
    assert collected["rel_key"] is rel_decl
    assert "scalar_key" not in collected


def test_active_input_permission_mixin_field_paths_and_branches():
    import types
    from dataclasses import dataclass

    from django_strawberry_framework.sets_mixins import (
        ActiveInputPermissionAttrs,
        ActiveInputPermissionMixin,
    )

    @dataclass
    class _ChildInput:
        sub_field: str = "val"

    @dataclass
    class _ParentInput:
        title: str = "hello"
        child: _ChildInput = None

    class _ChildSet(ActiveInputPermissionMixin):
        _permission = ActiveInputPermissionAttrs(
            family_label="ChildSet",
            related_attr="related_children",
            target_attr="childset",
            field_specs={"sub_field": types.SimpleNamespace(django_source_path="sub_field")},
            unset_sentinel=None,
        )

    class _ParentSet(ActiveInputPermissionMixin):
        related_children = {
            "child": types.SimpleNamespace(
                _resolved_target=lambda: _ChildSet,
                _target=_ChildSet,
            ),
        }
        _permission = ActiveInputPermissionAttrs(
            family_label="ParentSet",
            related_attr="related_children",
            target_attr="childset",
            field_specs={"title": types.SimpleNamespace(django_source_path="title")},
            unset_sentinel=None,
        )

    parent_input = _ParentInput(title="custom_title", child=_ChildInput(sub_field="sub"))

    # _active_permission_field_paths returns active leaf source paths
    paths = _ParentSet._active_permission_field_paths(parent_input)
    assert paths == ["title"]

    # _iter_active_related_branches returns active related branches
    branches = _ParentSet._iter_active_related_branches(parent_input)
    assert len(branches) == 1
    assert branches[0][0] == "child"
    assert branches[0][2] == _ChildInput(sub_field="sub")


def test_family_input_traversal_is_derived_from_the_permission_config():
    from strawberry import UNSET as _UNSET

    from django_strawberry_framework.filters.inputs import _field_specs as _filter_specs
    from django_strawberry_framework.orders.inputs import _field_specs as _order_specs
    from django_strawberry_framework.utils.input_values import SetInputTraversal

    filter_traversal = FilterSet._input_traversal()
    assert isinstance(filter_traversal, SetInputTraversal)
    assert filter_traversal.related_attr == "related_filters"
    assert filter_traversal.logic_keys == frozenset({"and_", "or_", "not_"})
    assert filter_traversal.unset_sentinel is _UNSET
    assert filter_traversal.handle_top_level_list is False
    assert filter_traversal.field_specs is _filter_specs

    order_traversal = OrderSet._input_traversal()
    assert order_traversal.related_attr == "related_orders"
    assert order_traversal.logic_keys == frozenset()
    assert order_traversal.unset_sentinel is _UNSET
    assert order_traversal.handle_top_level_list is True
    assert order_traversal.field_specs is _order_specs


def test_order_normalizer_consumes_the_family_permission_traversal(monkeypatch):
    import django_strawberry_framework.orders.inputs as order_inputs
    from django_strawberry_framework.sets_mixins import ActiveInputPermissionAttrs

    sentinel = object()
    captured = {}

    def _spy(set_cls, input_value, config):
        captured["config"] = config
        return iter(())

    monkeypatch.setattr(order_inputs, "iter_active_fields", _spy)

    class _StubFamily(ActiveInputPermissionMixin):
        _permission = ActiveInputPermissionAttrs(
            family_label="StubFamily",
            related_attr="related_stub",
            target_attr="stubset",
            field_specs={"a": "spec-a"},
            logic_keys=frozenset({"custom_op"}),
            unset_sentinel=sentinel,
            handle_top_level_list=True,
        )

    assert order_inputs.normalize_input_value(_StubFamily, None) == []
    config = captured["config"]
    assert config.related_attr == "related_stub"
    assert config.unset_sentinel is sentinel
    assert config.handle_top_level_list is True
    assert config.field_specs == {"a": "spec-a"}
    assert config.logic_keys == frozenset({"custom_op"})


def test_filter_normalizer_consumes_the_family_permission_traversal(monkeypatch):
    """``FilterSet._normalize_input`` classifies through the derived config.

    The filter-side twin of
    ``test_order_normalizer_consumes_the_family_permission_traversal``: the
    normalizer drives ``iter_active_fields`` with ``cls._input_traversal()``, so
    the grammar the apply path reads is the one ``_permission`` declares. This
    replaces an assertion that a module-level singleton NAME was absent, which
    any differently-named singleton would also have satisfied.
    """
    import django_strawberry_framework.filters.sets as filter_sets

    captured = {}

    def _spy(set_cls, input_value, config):
        captured["config"] = config
        return iter(())

    monkeypatch.setattr(filter_sets, "iter_active_fields", _spy)

    assert FilterSet._normalize_input({"title": "anything"}) == {}
    assert captured["config"] == FilterSet._input_traversal()


def test_filter_normalizer_honors_a_subclass_unset_sentinel_override():
    """An overridden ``_permission.unset_sentinel`` governs the apply path too.

    The defect the derived config closes: ``_normalize_input`` used to read a
    module-level singleton pinned to ``UNSET`` while the permission walkers read
    ``_permission``, so a subclass narrowing the sentinel was GATED on one
    grammar and FILTERED on another. Both sides now classify identically.
    """
    from dataclasses import replace

    from apps.library.models import Book
    from strawberry import UNSET

    marker = object()

    class _SentinelOverrideFilter(FilterSet):
        _permission = replace(FilterSet._permission, unset_sentinel=marker)

        class Meta:
            model = Book
            fields = ["title"]

    assert _SentinelOverrideFilter._input_traversal().unset_sentinel is marker
    # ``marker`` is "not supplied" under the override ...
    assert _SentinelOverrideFilter._normalize_input({"title": marker}) == {}
    # ... while ``UNSET`` is an ordinary supplied value, which the default
    # family (whose sentinel IS ``UNSET``) would have skipped instead.
    assert "title" in _SentinelOverrideFilter._normalize_input({"title": UNSET})
    assert FilterSet._normalize_input({"title": UNSET}) == {}
