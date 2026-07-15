"""Tests for input permissions, relation-path gates, and Django/Channels request decoding.

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
    _fire_flat_relation_path_gates,
    active_permission_field_paths,
    active_related_branches,
    extract_branch_value,
    invoke_permission_method,
    iter_input_items,
    request_from_info,
    run_active_input_permission_checks,
)
from django_strawberry_framework.utils.querysets import SyncMisuseError

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
# request_from_info -- Strawberry's WebSocket context puts the consumer itself
# at context["request"], so its ASGI scope is direct at request.scope.
# ---------------------------------------------------------------------------


class _FakeWSConsumer:
    """The ``GraphQLWSConsumer`` duck shape: the consumer is the request."""

    def __init__(self, scope):
        self.scope = scope
        self.channel_name = "specific..inmemory!probe"


def _channels_ws_info(scope):
    consumer = _FakeWSConsumer(scope)
    context = {"request": consumer, "ws": consumer}
    return type("Info", (), {"context": context})()


def test_channels_websocket_context_resolves_to_a_wrapping_adapter():
    """Direct scope fields resolve and other consumer attributes still delegate."""
    user, session = object(), object()
    scope = {"user": user, "session": session, "type": "websocket"}
    adapter = request_from_info(_channels_ws_info(scope), family_label="FilterSet")
    assert adapter.user is user
    assert adapter.session is session
    assert adapter.scope is scope
    assert adapter.channel_name == "specific..inmemory!probe"


def test_channels_websocket_scope_fields_default_to_none_when_middleware_absent():
    """A WS scope with no ``user`` key -> ``.user`` / ``.session`` are ``None``, not errors."""
    adapter = request_from_info(
        _channels_ws_info({"type": "websocket"}),
        family_label="OrderSet",
    )
    assert adapter.user is None
    assert adapter.session is None


def test_non_mapping_websocket_scope_is_not_recognized_as_channels():
    """A direct WebSocket scope must still be a mapping."""
    info = _channels_ws_info(["not", "a", "mapping"])
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


def test_invoke_permission_method_rejects_an_async_gate_instead_of_silently_allowing():
    """An ``async def check_<field>_permission`` is a loud ``SyncMisuseError``, not a silent allow.

    A filter / order permission gate is fired synchronously (on the async surface it
    runs on the single ``sync_to_async`` worker ``_apply_common_finalize`` wraps), so
    it can never be awaited. An ``async def`` gate returns a truthy, un-awaited
    coroutine whose ``raise`` never executes -- so an intended DENIAL would silently
    become a no-op, an authorization BYPASS. This gate is now guarded the same way
    every sibling authorization seam already is (mutation ``has_permission`` /
    ``check_permission``, the ``get_queryset`` visibility hook), so the async gate is
    rejected loudly rather than passed through as an allow.
    """
    denied: list[str] = []

    class _Bare:
        async def check_name_permission(self, request):
            # Would DENY, but as an ``async def`` it can never run under the sync
            # permission pass; the guard must reject the coroutine, not treat it as
            # a truthy success.
            denied.append("should-not-fire-but-must-not-be-silently-allowed")
            raise AssertionError("async gate body reached in a sync context")

    with pytest.raises(SyncMisuseError, match="check_name_permission returned a coroutine"):
        invoke_permission_method(_Bare(), "name", HttpRequest())

    # The coroutine was closed by the guard, never awaited, and its body never ran.
    assert denied == []


def test_invoke_permission_method_passes_a_normal_sync_return_through():
    """A plain sync gate returning ``None`` (the documented shape) is unaffected by the guard."""
    fired: set[str] = set()

    class _Bare:
        def check_name_permission(self, request):
            return None

    # No raise, and the fire is recorded for the dedup set.
    invoke_permission_method(_Bare(), "name", HttpRequest(), fired=fired)
    assert "check_name_permission" in fired


# ---------------------------------------------------------------------------
# _fire_flat_relation_path_gates -- flat traversal leaves are gated like their
# nested twins (the shared representational-bypass fix, both families).
# ---------------------------------------------------------------------------


class _Rel:
    """Duck-typed RelatedFilter/RelatedOrder: an ORM ``field_name`` + a target set."""

    def __init__(
        self,
        field_name,
        target,
        *,
        target_attr,
    ):
        self.field_name = field_name
        setattr(self, target_attr, target)


def _record_gate(store, label):
    def _check(self, request):
        store.append(label)

    return _check


def test_fire_flat_relation_path_gates_fires_the_deep_target_chain():
    """A deep flat path fires each parent relation gate plus the terminal field gate.

    ``entries__property__category__name`` fires the SAME gates the nested twin
    (``entries: {property: {category: {name}}}``) would: the branch gate on each
    intermediate set and ``check_name_permission`` on the terminal target set.
    """
    calls: list[str] = []

    class Category:
        check_name_permission = _record_gate(calls, "Category.name")

    class Property:
        related_filters = {"category": _Rel("category", Category, target_attr="filterset")}
        check_category_permission = _record_gate(calls, "Property.category")

    class Entry:
        related_filters = {"property": _Rel("property", Property, target_attr="filterset")}
        check_property_permission = _record_gate(calls, "Entry.property")

    class Item:
        related_filters = {"entries": _Rel("entries", Entry, target_attr="filterset")}
        check_entries_permission = _record_gate(calls, "Item.entries")

    _fire_flat_relation_path_gates(
        Item,
        "entries__property__category__name",
        HttpRequest(),
        fired={},
        related_attr="related_filters",
        target_attr="filterset",
    )
    assert calls == [
        "Item.entries",
        "Entry.property",
        "Property.category",
        "Category.name",
    ]


def test_fire_flat_relation_path_gates_resolves_a_renamed_branch_by_field_name():
    """A hop is matched on ``field_name`` (ORM accessor), not the public attr name.

    ``visible_shelves = RelatedFilter(ShelfFilter, field_name="shelves")`` has a
    public attr (``visible_shelves``) that differs from its ORM ``field_name``
    (``shelves``). The flat source path uses the ORM name (``shelves__code``); the
    hop still resolves, and the branch gate fired is keyed on the PUBLIC attr so it
    matches the gate the nested form fires.
    """
    calls: list[str] = []

    class Shelf:
        check_code_permission = _record_gate(calls, "Shelf.code")

    class Book:
        related_filters = {
            "visible_shelves": _Rel("shelves", Shelf, target_attr="filterset"),
        }
        check_visible_shelves_permission = _record_gate(calls, "Book.visible_shelves")

    _fire_flat_relation_path_gates(
        Book,
        "shelves__code",
        HttpRequest(),
        fired={},
        related_attr="related_filters",
        target_attr="filterset",
    )
    assert calls == ["Book.visible_shelves", "Shelf.code"]


def test_fire_flat_relation_path_gates_stops_at_an_unresolved_hop():
    """A relation hop with no declared RelatedFilter stops the walk (no guessing)."""
    calls: list[str] = []

    class Item:
        related_filters: dict = {}  # no ``author`` RelatedFilter declared
        check_author_permission = _record_gate(calls, "Item.author")

    _fire_flat_relation_path_gates(
        Item,
        "author__name",
        HttpRequest(),
        fired={},
        related_attr="related_filters",
        target_attr="filterset",
    )
    # No declared related object for ``author`` -> no target gate is fired and no
    # FilterSet is guessed. The owner's flat-path gate (fired by the caller,
    # not here) remains the authorization point.
    assert calls == []


def test_fire_flat_relation_path_gates_dedupes_against_the_nested_twin():
    """Flat and nested twins share the per-class ``fired`` map: each gate fires once."""
    calls: list[str] = []

    class Category:
        check_name_permission = _record_gate(calls, "Category.name")

    class Item:
        related_filters = {"category": _Rel("category", Category, target_attr="filterset")}
        check_category_permission = _record_gate(calls, "Item.category")

    fired: dict[type, set[str]] = {}
    # First the flat leaf...
    _fire_flat_relation_path_gates(
        Item,
        "category__name",
        HttpRequest(),
        fired=fired,
        related_attr="related_filters",
        target_attr="filterset",
    )
    # ...then the same path again (as the nested twin would, sharing ``fired``).
    _fire_flat_relation_path_gates(
        Item,
        "category__name",
        HttpRequest(),
        fired=fired,
        related_attr="related_filters",
        target_attr="filterset",
    )
    assert calls == ["Item.category", "Category.name"]


def test_fire_flat_relation_path_gates_works_for_the_order_family():
    """The shared fix covers the order family (``related_orders`` / ``orderset``).

    The order side exposes flat relation-traversal order fields via the
    ``Meta.fields = ["category__name"]`` shorthand; the same representational
    bypass is closed by the same shared walk with the order-family config.
    """
    calls: list[str] = []

    class CategoryOrder:
        check_name_permission = _record_gate(calls, "CategoryOrder.name")

    class ItemOrder:
        related_orders = {"category": _Rel("category", CategoryOrder, target_attr="orderset")}
        check_category_permission = _record_gate(calls, "ItemOrder.category")

    _fire_flat_relation_path_gates(
        ItemOrder,
        "category__name",
        HttpRequest(),
        fired={},
        related_attr="related_orders",
        target_attr="orderset",
    )
    assert calls == ["ItemOrder.category", "CategoryOrder.name"]


def test_fire_flat_relation_path_gates_stops_when_a_mid_chain_target_is_unresolved():
    """A hop whose related object's target set resolves to ``None`` stops the walk.

    A ``RelatedFilter``/``RelatedOrder`` whose lazy target has not resolved (or is
    unresolvable) exposes ``None`` at ``target_attr``; the branch gate on the
    current set still fires, but the walk stops rather than descending into
    ``None`` (so no terminal gate is fired on a phantom target).
    """
    calls: list[str] = []

    class Item:
        # ``category`` matches the hop but its target filterset is unresolved.
        related_filters = {"category": _Rel("category", None, target_attr="filterset")}
        check_category_permission = _record_gate(calls, "Item.category")

    _fire_flat_relation_path_gates(
        Item,
        "category__name",
        HttpRequest(),
        fired={},
        related_attr="related_filters",
        target_attr="filterset",
    )
    # The parent branch gate fired; the walk then stopped at the unresolved target.
    assert calls == ["Item.category"]


def test_fire_flat_relation_path_gates_is_a_noop_for_a_non_traversal_leaf():
    """A single-segment source path (no relation hop) fires nothing here."""
    calls: list[str] = []

    class Item:
        related_filters: dict = {}
        check_name_permission = _record_gate(calls, "Item.name")

    _fire_flat_relation_path_gates(
        Item,
        "name",
        HttpRequest(),
        fired={},
        related_attr="related_filters",
        target_attr="filterset",
    )
    # The owner's own field gate is fired by the caller's normal leaf loop, not
    # by the relation-chain walk.
    assert calls == []


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
            _depth=0,
        ):
            (_fired if _fired is not None else {}).setdefault(cls, set())
            calls.append(f"child._run@{_depth}")

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
        related_attr="related_orders",
    )
    # ``name`` gate fires ONCE despite the repeated path; the parent's per-branch
    # ``child`` gate fires once AND the child class recurses once. The shared core
    # threads the depth budget, so the child re-enters at ``_depth=1``.
    assert calls.count("parent.name") == 1
    assert calls.count("parent.child") == 1
    assert calls.count("child._run@1") == 1


def test_active_related_branches_empty_when_no_related_collection():
    class _NoRel:
        pass

    assert active_related_branches(_NoRel, {"a": 1}, related_attr="related_orders") == []


def test_run_active_input_permission_checks_caps_related_recursion():
    """A self-referential related branch is capped with a typed error (report Defect 5).

    The shared core threads a depth budget and refuses to recurse past the set's
    cap (``_MAX_LOGIC_DEPTH`` when defined, ``_MAX_RELATED_RECURSION_DEPTH``
    otherwise), converting an otherwise input-deep ``RecursionError`` into a
    catchable ``ConfigurationError`` at the source.
    """

    class _SelfRef:
        _MAX_LOGIC_DEPTH = 2

        @classmethod
        def _active_permission_targets(cls, input_value):
            # Always yields a related branch pointing back at THIS class -- the
            # runtime shape of ``CardFilter.dependencies`` -> ``CardFilter``.
            return [], [("child", _rel, {"x": 1})]

        @staticmethod
        def _invoke_permission_method(
            bare,
            field_path,
            request,
            *,
            fired=None,
        ):
            pass

        @classmethod
        def _run_permission_checks(
            cls,
            input_value,
            request,
            *,
            _fired=None,
            _depth=0,
        ):
            run_active_input_permission_checks(
                cls,
                input_value,
                request,
                fired=_fired if _fired is not None else {},
                bare=object.__new__(cls),
                target_attr="child_set",
                related_attr="related",
                depth=_depth,
            )

    _rel = type("Rel", (), {"child_set": _SelfRef})()

    with pytest.raises(ConfigurationError, match="nesting exceeded"):
        _SelfRef._run_permission_checks({"child": {"x": 1}}, HttpRequest())


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
