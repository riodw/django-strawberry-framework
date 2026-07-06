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
    with pytest.raises(ConfigurationError, match=f"{family_label} requires"):
        request_from_info(info_no_ctx, family_label=family_label)

    info_bad = type("Info", (), {"context": object()})()
    with pytest.raises(ConfigurationError, match=f"{family_label} could not resolve"):
        request_from_info(info_bad, family_label=family_label)


# ---------------------------------------------------------------------------
# request_from_info -- the Strawberry-Channels mapping context (spec-041
# Decision 11). Duck-typed fakes only: this branch must work (and be testable)
# with no ``channels`` import anywhere in the helper.
# ---------------------------------------------------------------------------


class _FakeConsumer:
    def __init__(self, scope):
        self.scope = scope


class _FakeChannelsRequest:
    """The ``ChannelsRequest`` duck shape: ``consumer`` + ``body`` + request attrs."""

    def __init__(self, scope):
        self.consumer = _FakeConsumer(scope)
        self.body = b'{"query": "{ ping }"}'
        self.method = "POST"
        self.headers = {"content-type": "application/json"}


def _channels_info(scope):
    context = {"request": _FakeChannelsRequest(scope), "response": object()}
    return type("Info", (), {"context": context})()


def test_channels_context_resolves_to_a_wrapping_adapter():
    """The mapping context resolves; ``.user`` / ``.session`` / ``.scope`` come from the scope."""
    user, session = object(), object()
    scope = {"user": user, "session": session, "type": "http"}
    adapter = request_from_info(_channels_info(scope), family_label="FilterSet")
    assert adapter.user is user
    assert adapter.session is session
    assert adapter.scope is scope


def test_channels_adapter_delegates_unknown_attributes_to_the_wrapped_request():
    """Non-scope attributes fall through to the original ``ChannelsRequest`` (finding P1.1)."""
    scope = {"user": object()}
    info = _channels_info(scope)
    adapter = request_from_info(info, family_label="OrderSet")
    wrapped = info.context["request"]
    assert adapter.method == "POST"
    assert adapter.headers is wrapped.headers
    assert adapter.consumer is wrapped.consumer
    assert adapter.body == wrapped.body
    # A genuinely missing attribute is a normal AttributeError, not a swallow.
    with pytest.raises(AttributeError):
        _ = adapter.definitely_not_a_request_attribute


def test_channels_adapter_scope_fields_default_to_none_when_middleware_absent():
    """No ``AuthMiddlewareStack`` in the stack: ``.user`` / ``.session`` are ``None``, not errors."""
    adapter = request_from_info(_channels_info({"type": "http"}), family_label="FilterSet")
    assert adapter.user is None
    assert adapter.session is None


def test_channels_adapter_supports_permission_hooks_reading_both_kinds_of_attribute():
    """A consumer-style gate reading one scope-backed and one delegated attribute succeeds."""
    user = object()
    adapter = request_from_info(_channels_info({"user": user}), family_label="FilterSet")

    seen = {}

    class _Gate:
        def check_name_permission(self, request):
            seen["user"] = request.user  # scope-backed
            seen["method"] = request.method  # delegated to the wrapped request

    invoke_permission_method(_Gate(), "name", adapter)
    assert seen == {"user": user, "method": "POST"}


@pytest.mark.parametrize(
    "context",
    [
        {"request": object()},  # no ``consumer.scope`` duck shape
        {"response": object()},  # no ``request`` key at all
        {"request": None},
        {},
    ],
)
def test_non_channels_mapping_shapes_still_raise_the_family_labelled_error(context):
    """Mapping contexts that are not Channels-shaped keep the final ``ConfigurationError``."""
    info = type("Info", (), {"context": context})()
    with pytest.raises(ConfigurationError, match="FilterSet could not resolve"):
        request_from_info(info, family_label="FilterSet")


def test_non_mapping_scope_is_not_recognized_as_channels():
    """A ``consumer.scope`` that is not a mapping falls through to the final error."""
    request = _FakeChannelsRequest({})
    request.consumer.scope = ["not", "a", "mapping"]
    info = type("Info", (), {"context": {"request": request}})()
    with pytest.raises(ConfigurationError, match="OrderSet could not resolve"):
        request_from_info(info, family_label="OrderSet")


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
        def _active_permission_targets(cls, input_value):
            # The fused single-pass contract ``run_active_input_permission_checks``
            # now consumes (feedback H3): one call yields BOTH the per-field gate
            # paths (repeated ``name`` -> must dedup) and the related branches.
            return ["name", "name"], [("child", related_obj, {"x": 1})]

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
        related_attr="related_orders",
        logic_keys=frozenset({"and_"}),
        fallback_path=lambda attr: attr,
    )
    # ``shelf`` (related, recognized off ``_Set.related_orders``) and ``and_``
    # (logic) excluded; ``title`` falls back to the python-attr token since
    # ``field_specs`` has no entry.
    assert paths == ["title"]
