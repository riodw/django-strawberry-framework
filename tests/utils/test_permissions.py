"""Tests for input permissions, relation-path gates, and Django/Channels request decoding.

This module single-sites the active-input permission traversal that the filter
and order families had grown as parallel copies; on an authorization surface a
divergence between two copies is a real bug class. These tests pin the shared
mechanics directly and the
configuration points (the family label, the ``unset_sentinel``) that keep the
two families distinct; the deep behavioral coverage (dedup, double-dispatch,
logic recursion, list aggregation) lives in the family ``test_sets`` suites.
"""

from collections.abc import Mapping

import pytest
import strawberry
from django.http import HttpRequest

from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.utils.permissions import (
    ChannelsRequestAdapter,
    _channels_request_adapter,
    _channels_scope,
    _fire_flat_relation_path_gates,
    _related_declarations,
    _request_from_context,
    active_permission_field_paths,
    active_related_branches,
    auth_aliases_for_permission_classes,
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
    """Every ordinary Django request context resolves; bad shapes name the family."""
    request = HttpRequest()
    info_with_request = type("Info", (), {"context": _Ctx(request)})()
    assert request_from_info(info_with_request, family_label=family_label) is request

    info_bare = type("Info", (), {"context": request})()
    assert request_from_info(info_bare, family_label=family_label) is request

    info_mapping = type("Info", (), {"context": {"request": request}})()
    assert request_from_info(info_mapping, family_label=family_label) is request

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
    """Non-scope attributes fall through to the original ``ChannelsRequest``."""
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


def test_hostile_channels_scope_descriptors_become_configuration_errors():
    """A malformed Channels request cannot leak a raw scope-descriptor exception."""

    class _HostileConsumer:
        @property
        def scope(self):
            raise RuntimeError("scope descriptor exploded")

    class _HostileRequest:
        consumer = _HostileConsumer()

    info = type("Info", (), {"context": {"request": _HostileRequest()}})()
    with pytest.raises(ConfigurationError, match="FilterSet could not resolve"):
        request_from_info(info, family_label="FilterSet")


def test_hostile_direct_scope_and_context_mapping_reads_fail_closed():
    """A scope or context read that explodes yields no request rather than escaping."""

    class _HostileDirectScope:
        consumer = None

        @property
        def scope(self):
            raise RuntimeError("direct scope exploded")

    class _HostileContext(dict):
        def __getitem__(self, key):
            raise RuntimeError("context mapping exploded")

    context = _HostileContext(request=object())

    assert _channels_scope(_HostileDirectScope()) is None
    assert _channels_request_adapter(context) is None
    assert _request_from_context(context) is None


def test_hostile_attribute_context_request_read_fails_closed():
    """A context whose ``request`` descriptor raises resolves to no request."""

    class _HostileContext:
        @property
        def request(self):
            raise RuntimeError("request descriptor exploded")

    assert _request_from_context(_HostileContext()) is None


def test_hostile_channels_scope_mapping_becomes_configuration_error_on_user_read():
    """A scope mapping that fails during lookup is typed at the adapter boundary."""

    class _HostileScope(dict):
        def __getitem__(self, key):
            raise RuntimeError("scope mapping exploded")

    adapter = ChannelsRequestAdapter(object(), _HostileScope())
    with pytest.raises(ConfigurationError, match="Channels request scope"):
        _ = adapter.user


def test_mapping_request_must_be_a_django_request_or_channels_context():
    """A mapping's arbitrary ``request`` value must not bypass request validation."""

    class _Context(dict):
        pass

    info = type("Info", (), {"context": _Context(request=object())})()
    with pytest.raises(ConfigurationError, match="OrderSet could not resolve"):
        request_from_info(info, family_label="OrderSet")


def test_request_like_attribute_context_remains_supported():
    """Non-mapping wrappers may carry the request-like object used by mutation hooks."""

    request = object()
    context = type("Context", (), {"request": request})()
    info = type("Info", (), {"context": context})()
    assert request_from_info(info, family_label="DjangoMutation") is request


def test_hostile_info_context_descriptor_becomes_configuration_error():
    """A broken ``info.context`` descriptor still follows the typed error boundary."""

    class _Info:
        @property
        def context(self):
            raise RuntimeError("context descriptor exploded")

    with pytest.raises(ConfigurationError, match="FilterSet requires"):
        request_from_info(_Info(), family_label="FilterSet")


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


def test_fire_flat_relation_path_gates_prefers_composite_branch_prefix():
    """A multi-hop RelatedFilter branch wins over a shorter overlapping branch.

    ``milestone`` can be declared over ``target_version__milestone`` while a
    separate ``target_version`` branch also exists. A flat
    ``target_version__milestone__key`` leaf must gate the declared composite
    branch and its target, not descend through the shorter branch and stop
    before the target permission hook.
    """
    calls: list[str] = []

    class Milestone:
        check_key_permission = _record_gate(calls, "Milestone.key")

    class TargetVersion:
        related_filters: dict = {}

    class Card:
        related_filters = {
            "milestone": _Rel(
                "target_version__milestone",
                Milestone,
                target_attr="filterset",
            ),
            "target_version": _Rel(
                "target_version",
                TargetVersion,
                target_attr="filterset",
            ),
        }
        check_milestone_permission = _record_gate(calls, "Card.milestone")

    _fire_flat_relation_path_gates(
        Card,
        "target_version__milestone__key",
        HttpRequest(),
        fired={},
        related_attr="related_filters",
        target_attr="filterset",
    )
    assert calls == ["Card.milestone", "Milestone.key"]


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


def test_fire_flat_relation_path_gates_falls_back_to_declared_attribute_when_field_name_is_none():
    """When field_name is None or omitted, the declared attribute name is used.

    In RelatedOrder(AuthorOrder) or RelatedFilter(AuthorFilter), field_name is None
    on the class declaration. A flat relation traversal (``author__name``) must fall
    back to the declared attribute key (``author``) rather than skipping the branch.
    """
    calls: list[str] = []

    class AuthorOrder:
        check_name_permission = _record_gate(calls, "AuthorOrder.name")

    class BookOrder:
        # field_name is None (the default for RelatedOrder(Target))
        related_orders = {"author": _Rel(None, AuthorOrder, target_attr="orderset")}
        check_author_permission = _record_gate(calls, "BookOrder.author")

    _fire_flat_relation_path_gates(
        BookOrder,
        "author__name",
        HttpRequest(),
        fired={},
        related_attr="related_orders",
        target_attr="orderset",
    )
    assert calls == ["BookOrder.author", "AuthorOrder.name"]


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


def test_flat_relation_gate_rejects_unreadable_branch_metadata_and_skips_non_string_names():
    """An unreadable branch name raises; a non-string one matches no hop and fires no gate."""

    class _UnreadableRelation:
        @property
        def field_name(self):
            raise RuntimeError("field name exploded")

    class _UnreadableSet:
        related_filters = {"category": _UnreadableRelation()}

    with pytest.raises(ConfigurationError, match="unreadable related permission branch"):
        _fire_flat_relation_path_gates(
            _UnreadableSet,
            "category__name",
            HttpRequest(),
            fired={},
            related_attr="related_filters",
            target_attr="filterset",
        )

    calls: list[str] = []

    class _NonStringSet:
        related_filters = {"category": _Rel(123, object(), target_attr="filterset")}
        check_category_permission = _record_gate(calls, "_NonStringSet.category")

    _fire_flat_relation_path_gates(
        _NonStringSet,
        "category__name",
        HttpRequest(),
        fired={},
        related_attr="related_filters",
        target_attr="filterset",
    )

    assert calls == []


def test_related_permission_declarations_fail_closed_for_malformed_metadata():
    """Only a readable mapping declares related branches; absent means none, malformed raises."""

    class _HostileMeta(type):
        def __getattribute__(cls, name):
            if name == "related_filters":
                raise RuntimeError("related descriptor exploded")
            return super().__getattribute__(name)

    class _UnreadableSet(metaclass=_HostileMeta):
        pass

    class _NoneSet:
        related_filters = None

    class _InvalidSet:
        related_filters = []

    class _UnreadableMapping(Mapping):
        def __getitem__(self, key):
            raise KeyError(key)

        def __iter__(self):
            return iter(())

        def __len__(self):
            return 0

        def items(self):
            raise RuntimeError("items exploded")

    mapping_set = type("MappingSet", (), {"related_filters": _UnreadableMapping()})

    with pytest.raises(ConfigurationError, match="could not be read"):
        _related_declarations(_UnreadableSet, "related_filters")
    assert _related_declarations(_NoneSet, "related_filters") == ()
    with pytest.raises(ConfigurationError, match="must be a mapping"):
        _related_declarations(_InvalidSet, "related_filters")
    with pytest.raises(ConfigurationError, match="could not be read"):
        _related_declarations(mapping_set, "related_filters")


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
            # consumes: one call yields BOTH the per-field gate
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
    cap (``_MAX_LOGIC_DEPTH`` when defined, ``DEFAULT_SET_INPUT_TRAVERSAL_DEPTH``
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


# ---------------------------------------------------------------------------
# resolve_auth_aliases (the authorization-phase auth-alias identification)
# ---------------------------------------------------------------------------


def test_auth_aliases_for_permission_classes_gates_alias_resolution(monkeypatch):
    """The explicit no-permissions opt-out grants no auth-alias access."""
    calls = []

    def _resolve():
        calls.append(None)
        return frozenset({"auth"})

    monkeypatch.setattr(
        "django_strawberry_framework.utils.permissions.resolve_auth_aliases",
        _resolve,
    )

    assert auth_aliases_for_permission_classes([]) == frozenset()
    assert calls == []
    assert auth_aliases_for_permission_classes([object()]) == frozenset({"auth"})
    assert calls == [None]


def test_auth_alias_gate_rejects_unreadable_permission_collection_truthiness():
    """A permission collection that cannot be tested for emptiness is a configuration error."""

    class _UnreadablePermissions:
        def __bool__(self):
            raise RuntimeError("permission truthiness exploded")

    with pytest.raises(ConfigurationError, match="could not be inspected"):
        auth_aliases_for_permission_classes(_UnreadablePermissions())


def test_related_depth_error_survives_hostile_child_qualname():
    """The depth-limit error is raised even when the child set's own name cannot be read."""

    class _HostileMeta(type):
        def __getattribute__(cls, name):
            if name == "__qualname__":
                raise RuntimeError("qualname exploded")
            return super().__getattribute__(name)

    class _Child(metaclass=_HostileMeta):
        _MAX_LOGIC_DEPTH = 0

        @classmethod
        def _run_permission_checks(
            cls,
            input_value,
            request,
            *,
            _fired,
            _depth,
        ):
            raise AssertionError("depth gate should fire before recursion")

    related = type("Related", (), {"child_set": _Child})()

    class _Parent:
        @classmethod
        def _active_permission_targets(cls, input_value):
            return [], [("child", related, input_value)]

    with pytest.raises(ConfigurationError, match="nesting exceeded"):
        run_active_input_permission_checks(
            _Parent,
            {"child": {}},
            HttpRequest(),
            fired={},
            bare=object(),
            target_attr="child_set",
            related_attr="related",
        )


def test_run_active_input_permission_checks_falls_back_to_default_traversal_depth():
    """When child set defines no _MAX_LOGIC_DEPTH, traversal uses DEFAULT_SET_INPUT_TRAVERSAL_DEPTH."""

    class _ChildWithoutDepthCap:
        @classmethod
        def _run_permission_checks(
            cls,
            input_value,
            request,
            *,
            _fired,
            _depth,
        ):
            raise AssertionError("depth gate should fire before recursion")

    related = type("Related", (), {"child_set": _ChildWithoutDepthCap})()

    class _Parent:
        @classmethod
        def _active_permission_targets(cls, input_value):
            return [], [("child", related, input_value)]

    # At depth=8, next_depth=9 > DEFAULT_SET_INPUT_TRAVERSAL_DEPTH (8), raising error
    with pytest.raises(
        ConfigurationError,
        match="nesting exceeded the maximum traversal depth \\(8\\)",
    ):
        run_active_input_permission_checks(
            _Parent,
            {"child": {}},
            HttpRequest(),
            fired={},
            bare=object(),
            target_attr="child_set",
            related_attr="related",
            depth=8,
        )


@pytest.mark.django_db
def test_resolve_auth_aliases_returns_the_default_alias_by_default():
    """With no divergent router, every auth model reads ``default``."""
    from django_strawberry_framework.utils.permissions import resolve_auth_aliases

    assert resolve_auth_aliases() == frozenset({"default"})


@pytest.mark.django_db
def test_resolve_auth_aliases_tracks_a_divergent_router_read_answer(settings):
    """The auth alias follows the router's read answer for the auth models."""
    from django.contrib.auth import get_user_model

    from django_strawberry_framework.utils.permissions import resolve_auth_aliases

    auth_app_label = get_user_model()._meta.app_label

    class _AuthToShardRouter:
        def db_for_read(self, model, **hints):
            # Route the auth app (and its perm/contenttype companions) to a
            # non-default alias; everything else keeps the default.
            if model._meta.app_label in {auth_app_label, "auth", "contenttypes"}:
                return "shard_b"
            return None

        def db_for_write(self, model, **hints):
            return None

    settings.DATABASE_ROUTERS = [_AuthToShardRouter()]
    assert resolve_auth_aliases() == frozenset({"shard_b"})


def test_resolve_auth_aliases_skips_uninstalled_models():
    """A model the deployment does not install is skipped, never an error."""
    from django_strawberry_framework.utils.permissions import _safe_get_model

    assert _safe_get_model("nonexistent_app", "Nope") is None
    assert _safe_get_model(None, None) is None


def test_channels_request_in_object_context_is_adapted_to_channels_request_adapter():
    """Channels request stored at context.request resolves to a ChannelsRequestAdapter."""
    from django_strawberry_framework.utils.permissions import (
        ChannelsRequestAdapter,
        request_from_info,
    )

    class _FakeConsumer:
        def __init__(self, scope):
            self.scope = scope

    class _FakeChannelsRequest:
        def __init__(self, scope):
            self.consumer = _FakeConsumer(scope)
            self.method = "POST"

    scope = {"user": "ada", "session": {"key": "456"}}
    raw_req = _FakeChannelsRequest(scope)
    ctx = type("Context", (), {"request": raw_req})()
    info = type("Info", (), {"context": ctx})()

    resolved = request_from_info(info, family_label="FilterSet")
    assert isinstance(resolved, ChannelsRequestAdapter)
    assert resolved.user == "ada"
    assert resolved.session == {"key": "456"}
    assert resolved.scope is scope
    assert resolved.method == "POST"


def test_bare_channels_consumer_in_object_context_is_adapted():
    """A bare Channels WebSocket consumer context resolves to a ChannelsRequestAdapter."""
    from django_strawberry_framework.utils.permissions import (
        ChannelsRequestAdapter,
        request_from_info,
    )

    class _FakeWSConsumer:
        def __init__(self, scope):
            self.scope = scope
            self.channel_name = "specific..inmemory!ws"

    scope = {"user": "grace", "session": None}
    consumer = _FakeWSConsumer(scope)
    info = type("Info", (), {"context": consumer})()

    resolved = request_from_info(info, family_label="OrderSet")
    assert isinstance(resolved, ChannelsRequestAdapter)
    assert resolved.user == "grace"
    assert resolved.session is None
    assert resolved.scope is scope
    assert resolved.channel_name == "specific..inmemory!ws"


def test_run_active_input_permission_checks_safely_handles_missing_target_attr():
    """If a related object lacks target_attr, child recursion is safely skipped without AttributeError."""
    from django_strawberry_framework.utils.permissions import run_active_input_permission_checks

    class _DuckRelatedObj:
        # Does not define 'filterset' or 'target_attr'
        pass

    class _SampleFilter:
        @classmethod
        def _active_permission_targets(cls, input_value):
            return [], [("duck", _DuckRelatedObj(), {"sub": 1})]

        @staticmethod
        def _invoke_permission_method(
            bare,
            field_name,
            request,
            *,
            fired=None,
        ):
            if fired is not None:
                fired.add(f"check_{field_name}_permission")

    fired = {}
    run_active_input_permission_checks(
        _SampleFilter,
        {"duck": {"sub": 1}},
        object(),
        fired=fired,
        bare=object(),
        target_attr="filterset",
        related_attr="related_filters",
    )
    assert fired.get(_SampleFilter) == {"check_duck_permission"}


def test_channels_request_adapter_idempotent_wrapping():
    """Wrapping an existing ChannelsRequestAdapter returns the adapter directly."""
    from django_strawberry_framework.utils.permissions import (
        ChannelsRequestAdapter,
        _channels_request_adapter,
        _request_from_context,
    )

    scope = {"user": "ada", "type": "websocket"}
    adapter = ChannelsRequestAdapter(HttpRequest(), scope)

    assert _channels_request_adapter(adapter) is adapter
    assert _channels_request_adapter({"request": adapter}) is adapter
    assert _channels_request_adapter(type("Ctx", (), {"request": adapter})()) is adapter
    assert _request_from_context(adapter) is adapter
    assert _request_from_context({"request": adapter}) is adapter
    assert _request_from_context(type("Ctx", (), {"request": adapter})()) is adapter
