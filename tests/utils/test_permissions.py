"""Tests for the shared active-input permission substrate (``utils/permissions.py``).

The 0.0.9 DRY pass single-sited the active-input permission traversal that the
filter and order families had grown as parallel copies (``docs/feedback.md``
Major 3 -- an authorization surface where a divergence between the two copies is
a real bug class). These tests pin the shared mechanics directly and the
configuration points (the family label, the ``unset_sentinel``) that keep the
two families distinct; the deep behavioral coverage (dedup, double-dispatch,
logic recursion, list aggregation) lives in the family ``test_sets`` suites.
"""

import pytest
import strawberry
from django.http import HttpRequest

from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.utils.permissions import (
    active_permission_field_paths,
    active_related_branches,
    extract_branch_value,
    invoke_permission_method,
    iter_input_items,
    request_from_info,
    run_active_input_permission_checks,
)

# ---------------------------------------------------------------------------
# request_from_info -- family-labelled, shape-tolerant
# ---------------------------------------------------------------------------


class _Ctx:
    def __init__(self, request):
        self.request = request


@pytest.mark.parametrize("family_label", ["FilterSet", "OrderSet"])
def test_request_from_info_resolves_and_names_family(family_label):
    """``info.context.request`` and bare-HttpRequest both resolve; bad shapes name the family."""
    request = HttpRequest()
    info_with_request = type("Info", (), {"context": _Ctx(request)})()
    assert request_from_info(info_with_request, family_label=family_label) is request

    info_bare = type("Info", (), {"context": request})()
    assert request_from_info(info_bare, family_label=family_label) is request

    info_no_ctx = type("Info", (), {"context": None})()
    with pytest.raises(ConfigurationError, match=f"{family_label}.apply requires"):
        request_from_info(info_no_ctx, family_label=family_label)

    info_bad = type("Info", (), {"context": object()})()
    with pytest.raises(ConfigurationError, match=f"{family_label}.apply could not resolve"):
        request_from_info(info_bad, family_label=family_label)


# ---------------------------------------------------------------------------
# iter_input_items / extract_branch_value
# ---------------------------------------------------------------------------


def test_iter_input_items_handles_dict_dataclass_and_non_walkable():
    assert iter_input_items({"a": 1}) == [("a", 1)]
    assert iter_input_items(42) is None

    @strawberry.input
    class _In:
        a: int | None = None

    assert iter_input_items(_In(a=3)) == [("a", 3)]


def test_extract_branch_value_collapses_only_the_configured_sentinel():
    """The order side (default ``unset_sentinel=None``) leaves UNSET intact; filter collapses it."""
    holder = {"branch": strawberry.UNSET, "real": 5}
    # No sentinel configured (order semantics): UNSET passes through unchanged.
    assert extract_branch_value(holder, "branch") is strawberry.UNSET
    # Filter semantics: UNSET collapses to None ("branch not supplied").
    assert extract_branch_value(holder, "branch", unset_sentinel=strawberry.UNSET) is None
    assert extract_branch_value(holder, "real", unset_sentinel=strawberry.UNSET) == 5
    assert extract_branch_value(None, "branch") is None


# ---------------------------------------------------------------------------
# invoke_permission_method -- fire + dedup
# ---------------------------------------------------------------------------


def test_invoke_permission_method_fires_once_and_dedupes():
    calls: list[str] = []

    class _Bare:
        def check_name_permission(self, request):
            calls.append("name")

    fired: set[str] = set()
    invoke_permission_method(_Bare(), "name", HttpRequest(), fired=fired)
    invoke_permission_method(_Bare(), "name", HttpRequest(), fired=fired)
    assert calls == ["name"]
    # A field with no matching method is a silent no-op.
    invoke_permission_method(_Bare(), "absent", HttpRequest(), fired=fired)
    assert calls == ["name"]


# ---------------------------------------------------------------------------
# run_active_input_permission_checks -- core dispatch + per-class dedup
# ---------------------------------------------------------------------------


def test_run_active_input_permission_checks_double_dispatch_and_dedup():
    """Parent per-branch gate + child gate both fire once; child recurses via its own class."""
    calls: list[str] = []

    class _Child:
        @classmethod
        def _run_permission_checks(
            cls,
            input_value,
            request,
            *,
            _fired=None,
        ):
            (_fired if _fired is not None else {}).setdefault(cls, set())
            calls.append("child._run")

    related_obj = type("Rel", (), {"orderset": _Child})()

    class _Parent:
        @classmethod
        def _active_permission_field_paths(cls, input_value):
            return ["name", "name"]  # repeated -> must dedup

        @classmethod
        def _iter_active_related_branches(cls, input_value):
            return [("child", related_obj, {"x": 1})]

        @staticmethod
        def _invoke_permission_method(
            bare,
            field_path,
            request,
            *,
            fired=None,
        ):
            invoke_permission_method(bare, field_path, request, fired=fired)

        def check_name_permission(self, request):
            calls.append("parent.name")

        def check_child_permission(self, request):
            calls.append("parent.child")

    fired: dict[type, set[str]] = {}
    bare = object.__new__(_Parent)
    run_active_input_permission_checks(
        _Parent,
        {"name": "v", "child": {"x": 1}},
        HttpRequest(),
        fired=fired,
        bare=bare,
        target_attr="orderset",
    )
    # ``name`` gate fires ONCE despite the repeated path; the parent's per-branch
    # ``child`` gate fires once AND the child class recurses once.
    assert calls.count("parent.name") == 1
    assert calls.count("parent.child") == 1
    assert calls.count("child._run") == 1


def test_active_related_branches_empty_when_no_related_collection():
    class _NoRel:
        pass

    assert active_related_branches(_NoRel, {"a": 1}, related_attr="related_orders") == []


def test_active_permission_field_paths_excludes_logic_and_related_keys():
    class _Set:
        related_orders = {"shelf": object()}

    paths = active_permission_field_paths(
        _Set,
        {"title": "asc", "shelf": {"code": "x"}, "and_": [{"title": "x"}]},
        field_specs={},
        related_keys={"shelf"},
        logic_keys=frozenset({"and_"}),
        fallback_path=lambda attr: attr,
    )
    # ``shelf`` (related) and ``and_`` (logic) excluded; ``title`` falls back to
    # the python-attr token since ``field_specs`` has no entry.
    assert paths == ["title"]
