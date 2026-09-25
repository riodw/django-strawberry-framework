"""Package-only cascade-permission pins that no live GraphQL request can express.

Live HTTP coverage of hidden-target exclusion, the two-deep
``Entry -> Item -> Category`` walk (including mixed-edge hops), and
zero-added-round-trip subquery composition lives in
``examples/fakeshop/test_query/test_products_api.py``
(``test_cascade_anonymous_sees_no_entries_under_private_categories``,
``test_cascade_view_item_user_respects_category_visibility``,
``test_cascade_view_entry_user_nested_selection_drops_hidden_targets``,
``test_cascade_query_count_fixed``) and
``examples/fakeshop/test_query/test_products_visibility_api.py``
(the cascading target hook's effect on the optimizer's relation plan).
Filter/order gate composition on the wire is
``test_cascade_composes_with_filter_and_order_live``.

This file keeps apply-time ``ConfigurationError`` (cycles, GFK preflight,
``fields=`` validation, hook-return / root-seal / alias defects) that a
shipped schema never declares; edge classification over real relation
shapes; ``fields=`` scoping (shipped hooks pass ``fields=None`` or a fixed
subset); SQL-shape of sealed cascade internals a live capture cannot uniquely
show; thread / task ``ContextVar`` isolation; the async ``aapply`` off-loop
contract; identity-hook default-manager composition over products types
(every products type declares a custom ``get_queryset``); mixed-actor
cascade-then-gate composition (anonymous-narrowed queryset + staff
``apply_sync``) that one HTTP request cannot split.
``strictness="raise"`` cascade silence is live
(``test_list_field_api.py::test_cascaded_item_list_stays_silent_under_strictness_raise``).
The MTI parent-link row cascade, the nullable-edge ``IS NULL`` disjunct and a
filtering proxy default manager as the cascade base are live in
``examples/fakeshop/test_query/test_library_inheritance_api.py``.

Fixture mechanics
=================
Relation shapes run over real fakeshop models under test-local types
(``registry.clear()`` around every test): the ``Venue`` <-> ``RepairTicket``
key cycle, ``CirculationDesk`` (every relation kind on one model),
``TaggedItem`` (GFK), ``PatronProfile.favorite_genre`` (``to_field``),
``ScalarSpecimen.parent`` (self key) and ``Shelf.branch`` (concrete target of
the ``ProxyBranch`` proxy). The synthetic models are each declared
``managed = False`` under the installed ``products`` app label (so Django
wires reverse relations into ``_meta.get_fields()``) and, where a test reads
rows, given a real table via ``connection.schema_editor()``. The three-model
ring, the cyclic diamond and the two-parent MTI child are shapes no fakeshop
app carries (a cycle in an acceptance app would change every cascade its
types compose). The acyclic diamond and the ``_Ct*`` hook-return battery
(a target, an MTI child of it, a non-null key into it and an unrelated table)
are shapes fakeshop does carry (``Edition.publisher`` / ``publisher_2``;
``Venue`` / ``LendingDesk`` / ``RepairTicket.venue``). Tests that only
inspect the COMPOSED query assert on ``str(qs.query)`` / ``qs.db`` directly.
The multi-DB pin is ``FAKESHOP_SHARDED``-gated (the ``shard_b`` alias only
exists under that env var) and does not run under a bare ``uv run pytest``.

The mutation update/delete lookup-scoping pin (spec-036) is NOT homed here; a
hidden row must read as not-found with no existence leak, and that is pinned at
``test_products_api.py::test_update_item_anonymous_on_hidden_private_row_is_not_found_before_any_auth_signal``.
"""

import contextlib
import datetime
import os
import re
import uuid
from types import SimpleNamespace

import pytest
from apps.library.models import (
    Branch,
    CirculationDesk,
    Genre,
    Patron,
    PatronProfile,
    ProxyBranch,
    RepairTicket,
    Shelf,
    TaggedItem,
    Venue,
)
from apps.products import services
from apps.products.models import Category, Entry, Item, Property
from apps.scalars.models import ScalarSpecimen
from django.contrib.contenttypes.models import ContentType
from django.db import connection as db_connection
from django.db import models
from django.http import HttpRequest
from graphql import GraphQLError
from strategy_schemas import make_django_type

from django_strawberry_framework import (
    finalize_django_types,
)
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.filters import FilterSet
from django_strawberry_framework.orders import Ordering, OrderSet
from django_strawberry_framework.permissions import (
    SyncMisuseError,
    _cascadable_edge_names,
    _cascade_state,
    _edge_plan,
    _is_cascadable_edge,
    _is_unsupported_forward_edge,
    aapply_cascade_permissions,
    apply_cascade_permissions,
)
from django_strawberry_framework.registry import registry

# ``info`` is threaded into each target hook but never read by the synthetic
# hooks below (they narrow unconditionally), so a placeholder namespace suffices.
_INFO = SimpleNamespace(context=SimpleNamespace(user=None))


@pytest.fixture(autouse=True)
def _isolate_registry():
    """Drop registry state on entry/exit so each test starts clean."""
    registry.clear()
    yield
    registry.clear()


@pytest.fixture(autouse=True)
def _assert_contextvar_clean():
    """The traversal-state var must be reset to ``None`` after every test.

    A test that leaves ``_cascade_state`` set would leak stale traversal state
    into the next test sharing the context - the same request-isolation property
    the token-based ``finally`` resets guarantee in production. Pinning it here
    makes a leak a hard failure rather than a spooky-action-at-a-distance flake.
    """
    yield
    assert _cascade_state.get() is None


@contextlib.contextmanager
def _tables(*model_classes):
    """Create real tables for ``managed = False`` synthetic models, then drop them.

    The ``connection.schema_editor()`` create/delete pattern from
    ``tests/test_relay_connection.py``; models are created in declaration order and
    dropped in reverse so FK constraints resolve.
    """
    with db_connection.schema_editor() as schema_editor:
        for model_class in model_classes:
            schema_editor.create_model(model_class)
    try:
        yield
    finally:
        with db_connection.schema_editor() as schema_editor:
            for model_class in reversed(model_classes):
                schema_editor.delete_model(model_class)


def _make_type(
    name,
    model,
    *,
    get_queryset=None,
    fields=("id",),
    primary=True,
):
    """Declare a ``DjangoType`` over ``model``, optionally with a cascading hook.

    ``get_queryset`` (when given) becomes the type's hook so
    ``has_custom_get_queryset()`` reports ``True``; omitting it leaves the identity
    default (an identity-hook target still composes its registered
    ``_default_manager`` subquery - registration, not hook customization, is
    what puts a target inside the visibility contract). The default ``fields=("id",)``
    keeps the *selected* surface scalar-only so finalization never has to resolve a
    relation field to a (possibly-unregistered) target type - the cascade walks the
    model's ``_meta.get_fields()`` edges regardless of what the type exposes (the
    "Meta.fields-excluded FK edges still cascade" edge case). The declaration
    core is the shared ``examples/fakeshop/strategy_schemas.py::make_django_type``.
    """
    return make_django_type(
        name,
        model,
        fields,
        node=False,
        meta_extra={"primary": primary},
        namespace_extra=(
            {"get_queryset": classmethod(get_queryset)} if get_queryset is not None else None
        ),
    )


def _cascade_only(cls, qs, info):
    """A hook that cascades and nothing else - the pure re-entrant shape.

    Shared by the cycle fixtures (ring / diamond / self) and the transitive-chain
    tests; each used to define a local copy of this exact body.
    """
    return apply_cascade_permissions(cls, qs, info)


# =============================================================================
# Cascade foundation (per spec-034 Decision 5 / 9 / 10), hardened: recursive
# graphs fail closed with a path-rich error; traversal state is immutable and
# token-reset on every root, edge, and nested application.
# =============================================================================


def _cascading_hook(**hidden):
    """Build the recurring cascade-and-hide hook narrowing out the rows matching ``hidden``."""
    return lambda cls, qs, info: apply_cascade_permissions(
        cls,
        qs.exclude(**hidden),
        info,
    )


def test_mutual_cycle_fails_closed_with_path():
    """A<->B mutual cascade raises the path-rich cycle error; state resets.

    ``apps/library/models.py::Venue.lead_ticket`` and
    ``apps/library/models.py::RepairTicket.venue`` close a foreign-key cycle.
    The shipped ``RepairTicketType`` does not cascade back, so the cycle is only
    re-entered by the test-local pair below where both hooks cascade. The
    previous contract returned the re-entered queryset un-narrowed, which skipped
    the re-entered type's OUTGOING visibility edges: the ``RepairTicket``
    subquery's ``venue``-edge constraint would bind ``Venue`` rows WITHOUT the
    venue's own ``lead_ticket``-edge cascade, so a ticket whose venue is led by a
    hidden ticket stayed visible through the nested walk - a leak shape. The
    hardened contract fails closed instead: re-entry into an active type raises
    ``ConfigurationError`` carrying the full edge path, before any SQL runs, and
    every token reset fires so the traversal state is clean after the raise.
    """
    venue_type = _make_type("CycleAType", Venue, get_queryset=_cascading_hook(name="hidden_a"))
    _make_type("CycleBType", RepairTicket, get_queryset=_cascading_hook(code="hidden_b"))
    finalize_django_types()

    with pytest.raises(ConfigurationError) as excinfo:
        apply_cascade_permissions(venue_type, Venue.objects.all(), _INFO)
    message = str(excinfo.value)
    # Path-rich: the full edge chain back to the re-entered type.
    assert "CycleAType.lead_ticket -> CycleBType.venue -> CycleAType" in message
    assert "fields=" in message  # the documented recourse
    # Deterministic: the same walk raises identically on a second root call.
    with pytest.raises(ConfigurationError, match="CycleAType.lead_ticket -> CycleBType.venue"):
        apply_cascade_permissions(venue_type, Venue.objects.all(), _INFO)
    # Every token reset fired despite the raise.
    assert _cascade_state.get() is None


def test_hook_exception_propagates_and_resets_state():
    """A target-hook exception propagates unchanged; every state token resets.

    The hook is reached during the root's walk (inside the ``lead_ticket`` edge
    frame), so the raise unwinds through the edge token AND the root token - both
    ``finally`` resets must fire, leaving ``_cascade_state`` at ``None``.
    """
    raiser_venue = _make_type("RaiserAType", Venue)

    def _boom(cls, qs, info):
        raise RuntimeError("boom")

    _make_type("RaiserBType", RepairTicket, get_queryset=_boom)
    finalize_django_types()

    with pytest.raises(RuntimeError, match="boom"):
        apply_cascade_permissions(raiser_venue, Venue.objects.all(), _INFO)
    # The token resets cleared the traversal state despite the exception.
    assert _cascade_state.get() is None


def test_longer_cycle_renders_full_path():
    """A three-type A->B->C->A cycle raises with every hop in the path.

    Fakeshop's one multi-model foreign-key cycle is the ``Venue`` / ``RepairTicket`` pair, and adding
    a three-model ring to an acceptance app would change the cascade every one of its types
    composes; this synthetic ring alone pins that
    ``django_strawberry_framework/permissions.py::_cycle_error`` renders a path frame for every hop
    ``django_strawberry_framework/permissions.py::_walk`` pushed, not just the first two.
    """

    class RingA(models.Model):
        b = models.ForeignKey("RingB", null=True, on_delete=models.CASCADE, related_name="+")

        class Meta:
            app_label = "products"
            managed = False

    class RingB(models.Model):
        c = models.ForeignKey("RingC", null=True, on_delete=models.CASCADE, related_name="+")

        class Meta:
            app_label = "products"
            managed = False

    class RingC(models.Model):
        a = models.ForeignKey(RingA, null=True, on_delete=models.CASCADE, related_name="+")

        class Meta:
            app_label = "products"
            managed = False

    ring_a = _make_type("RingAType", RingA, get_queryset=_cascade_only)
    _make_type("RingBType", RingB, get_queryset=_cascade_only)
    _make_type("RingCType", RingC, get_queryset=_cascade_only)
    finalize_django_types()

    # Pure composition - the cycle is detected before any SQL executes, so no
    # tables are needed.
    with pytest.raises(ConfigurationError) as excinfo:
        apply_cascade_permissions(ring_a, RingA.objects.all(), _INFO)
    assert "RingAType.b -> RingBType.c -> RingCType.a -> RingAType" in str(excinfo.value)
    assert _cascade_state.get() is None


@pytest.mark.django_db(transaction=True)
def test_root_queryset_filter_override_is_neutralized_by_sealing():
    """A hostile root ``filter`` override cannot erase a cascade predicate."""

    class FilterEraser(models.QuerySet):
        def filter(self, *args, **kwargs):
            return _CtParent.objects.all()

    with _tables(_CtTarget, _CtParent):
        parent_type = _register_ct_pair(
            lambda cls, qs, info: qs.exclude(name="hidden"),
        )
        visible = _CtTarget.objects.create(name="visible")
        hidden = _CtTarget.objects.create(name="hidden")
        _CtParent.objects.create(name="keeps", target=visible)
        _CtParent.objects.create(name="drops", target=hidden)

        hostile_root = FilterEraser(model=_CtParent, using="default")
        result = apply_cascade_permissions(parent_type, hostile_root, _INFO)

        assert sorted(result.values_list("name", flat=True)) == ["keeps"]
        assert _cascade_state.get() is None


def test_cyclic_diamond_fails_closed():
    """A diamond whose sink cascades back to the source raises on either branch.

    Fakeshop's one converging graph (``Printing`` reaching ``Publisher`` directly and through
    ``Edition``) never closes back into its source, and a cyclic one would make every cascading
    type on it raise; this synthetic graph alone pins that
    ``django_strawberry_framework/permissions.py::apply_cascade_permissions`` raises on the first
    branch that re-enters the source rather than after walking both.
    """

    class DmSource(models.Model):
        left = models.ForeignKey("DmLeft", null=True, on_delete=models.CASCADE, related_name="+")
        right = models.ForeignKey("DmRight", null=True, on_delete=models.CASCADE, related_name="+")

        class Meta:
            app_label = "products"
            managed = False

    class DmLeft(models.Model):
        sink = models.ForeignKey("DmSink", null=True, on_delete=models.CASCADE, related_name="+")

        class Meta:
            app_label = "products"
            managed = False

    class DmRight(models.Model):
        sink = models.ForeignKey("DmSink", null=True, on_delete=models.CASCADE, related_name="+")

        class Meta:
            app_label = "products"
            managed = False

    class DmSink(models.Model):
        source = models.ForeignKey(DmSource, null=True, on_delete=models.CASCADE, related_name="+")

        class Meta:
            app_label = "products"
            managed = False

    source_type = _make_type("DmSourceType", DmSource, get_queryset=_cascade_only)
    _make_type("DmLeftType", DmLeft, get_queryset=_cascade_only)
    _make_type("DmRightType", DmRight, get_queryset=_cascade_only)
    _make_type("DmSinkType", DmSink, get_queryset=_cascade_only)
    finalize_django_types()

    with pytest.raises(ConfigurationError) as excinfo:
        apply_cascade_permissions(source_type, DmSource.objects.all(), _INFO)
    # The first branch reaches the sink and cycles back to the source.
    assert "DmSourceType.left -> DmLeftType.sink -> DmSinkType.source -> DmSourceType" in str(
        excinfo.value,
    )
    assert _cascade_state.get() is None


@pytest.mark.django_db(transaction=True)
def test_acyclic_diamond_composes_sink_through_both_branches():
    """An acyclic diamond composes: the sink's visibility applies via BOTH branches.

    Re-reaching the sink type through the second branch is NOT a cycle - the active tuple pops on
    frame exit (token reset), so only genuine in-flight re-entry raises. The sink's hook narrows
    both subquery chains. The active-tuple pop in
    ``django_strawberry_framework/permissions.py::apply_cascade_permissions`` is what tells a second
    arrival at a finished type apart from re-entry into an active one.
    """

    class AdSource(models.Model):
        name = models.TextField()
        left = models.ForeignKey("AdLeft", null=True, on_delete=models.CASCADE, related_name="+")
        right = models.ForeignKey("AdRight", null=True, on_delete=models.CASCADE, related_name="+")

        class Meta:
            app_label = "products"
            managed = False

    class AdLeft(models.Model):
        sink = models.ForeignKey("AdSink", null=True, on_delete=models.CASCADE, related_name="+")

        class Meta:
            app_label = "products"
            managed = False

    class AdRight(models.Model):
        sink = models.ForeignKey("AdSink", null=True, on_delete=models.CASCADE, related_name="+")

        class Meta:
            app_label = "products"
            managed = False

    class AdSink(models.Model):
        name = models.TextField()

        class Meta:
            app_label = "products"
            managed = False

    with _tables(AdSink, AdLeft, AdRight, AdSource):
        source_type = _make_type("AdSourceType", AdSource, get_queryset=_cascade_only)
        _make_type("AdLeftType", AdLeft, get_queryset=_cascade_only)
        _make_type("AdRightType", AdRight, get_queryset=_cascade_only)
        _make_type(
            "AdSinkType",
            AdSink,
            get_queryset=lambda cls, qs, info: qs.exclude(name="hidden_sink"),
        )
        finalize_django_types()

        visible_sink = AdSink.objects.create(name="ok_sink")
        hidden_sink = AdSink.objects.create(name="hidden_sink")
        left_ok = AdLeft.objects.create(sink=visible_sink)
        right_ok = AdRight.objects.create(sink=visible_sink)
        right_bad = AdRight.objects.create(sink=hidden_sink)
        keeps = AdSource.objects.create(name="keeps", left=left_ok, right=right_ok)
        # Hidden sink two edges away through the RIGHT branch -> drops.
        AdSource.objects.create(name="drops_right", left=left_ok, right=right_bad)

        result = apply_cascade_permissions(source_type, AdSource.objects.all(), _INFO)
        assert sorted(result.values_list("name", flat=True)) == ["keeps"]
        assert keeps in result
        assert _cascade_state.get() is None


def test_single_column_scope_skips_m2m_reverse_and_generic():
    """Reverse / M2M / ``GenericRelation`` edges stay skipped; GFK is UNSUPPORTED.

    ``apps/library/models.py::CirculationDesk`` carries every relation kind: a
    forward FK (``branch``), a forward O2O (``shelf``), an M2M (``genres``), a
    ``GenericForeignKey`` (``content_object`` over ``content_type`` /
    ``object_id``), a ``GenericRelation`` (``tags``), a reverse FK
    (``children``) and a reverse O2O (``profile``). The cascadable set is
    exactly the single-column concrete forward relations (``branch`` /
    ``shelf`` / the GFK's backing ``content_type``), the reverse / M2M /
    ``GenericRelation`` edges are outside parent-row cascade semantics
    (skippable), and the virtual ``GenericForeignKey`` itself is classified
    UNSUPPORTED - it can neither be composed as a one-column subquery nor safely
    skipped, so the walk preflights it closed (pinned by the ``test_gfk_*``
    tests below). The shipped ``CirculationDeskType`` scopes its cascade with
    ``fields=``, so no request reaches this classification of the full set.
    """
    # The GFK's *backing* FK is itself an ordinary single-column forward FK and
    # legitimately cascadable; the virtual ``content_object`` is UNSUPPORTED.
    plan = _edge_plan(CirculationDesk)
    assert _cascadable_edge_names(CirculationDesk) == {"branch", "shelf", "content_type"}
    assert plan.unsupported == ("content_object",)

    # Each edge passes / fails the predicates for the documented reason.
    by_name = {f.name: f for f in CirculationDesk._meta.get_fields()}
    assert _is_cascadable_edge(by_name["branch"]) is True
    assert _is_cascadable_edge(by_name["shelf"]) is True
    assert _is_cascadable_edge(by_name["content_type"]) is True  # backing FK, single column
    assert getattr(by_name["genres"], "many_to_many", False) is True
    assert _is_cascadable_edge(by_name["genres"]) is False  # M2M, join table
    assert _is_unsupported_forward_edge(by_name["genres"]) is False  # ...and skippable
    assert _is_cascadable_edge(by_name["content_object"]) is False  # GFK, virtual
    assert _is_unsupported_forward_edge(by_name["content_object"]) is True  # fail-closed
    assert _is_cascadable_edge(by_name["tags"]) is False  # GenericRelation, one-to-many
    assert _is_unsupported_forward_edge(by_name["tags"]) is False
    assert _is_cascadable_edge(by_name["children"]) is False  # reverse FK
    assert _is_unsupported_forward_edge(by_name["children"]) is False
    assert _is_cascadable_edge(by_name["profile"]) is False  # reverse O2O
    assert _is_unsupported_forward_edge(by_name["profile"]) is False


def test_gfk_default_walk_preflights_closed():
    """A full walk (``fields=None``) over a GFK-carrying model fails before any hook.

    ``apps/library/models.py::TaggedItem`` carries a ``GenericForeignKey`` over
    its ``content_type`` key. Silently skipping the GFK would leak rows pointing
    at hidden polymorphic targets; composing it is impossible (no single
    visibility policy). The preflight raises BEFORE any target hook runs - the
    registered ``ContentType`` target's hook observes zero invocations.
    """
    hook_calls = []

    def _counting_hook(cls, qs, info):
        hook_calls.append(cls)
        return qs

    _make_type("GfkContentTypeCountType", ContentType, get_queryset=_counting_hook)
    host_type = _make_type("GfkHostType", TaggedItem, primary=False)
    finalize_django_types()

    with pytest.raises(ConfigurationError) as excinfo:
        apply_cascade_permissions(host_type, TaggedItem.objects.all(), _INFO)
    message = str(excinfo.value)
    assert "content_object" in message  # the offending edge is named
    assert "fields=" in message  # the recourse is named
    # Preflighted: no visibility hook ever ran.
    assert hook_calls == []


def _gfk_host_with_content_type_hook():
    """Register a ContentType hook + the ``TaggedItem`` GFK host; return the host type."""
    _make_type(
        "GfkContentTypeType",
        ContentType,
        get_queryset=lambda cls, qs, info: qs.exclude(model="hiddenmodel"),
    )
    return _make_type("GfkHostSelType", TaggedItem, primary=False)


def test_gfk_explicit_selection_rejected():
    """``fields=["content_object"]`` raises: the virtual GFK has no single-column cascade."""
    host_type = _gfk_host_with_content_type_hook()
    finalize_django_types()

    with pytest.raises(ConfigurationError) as excinfo:
        apply_cascade_permissions(
            host_type,
            TaggedItem.objects.all(),
            _INFO,
            fields=["content_object"],
        )
    assert "content_object" in str(excinfo.value)
    assert "no single-column cascade semantics" in str(excinfo.value)


def test_gfk_backing_content_type_fk_composes():
    """``fields=["content_type"]`` composes a subquery through the backing FK."""
    host_type = _gfk_host_with_content_type_hook()
    finalize_django_types()

    result = apply_cascade_permissions(
        host_type,
        TaggedItem.objects.all(),
        _INFO,
        fields=["content_type"],
    )
    assert "IN (SELECT" in str(result.query)


def test_gfk_object_id_is_not_cascadable():
    """``object_id`` is a scalar, so ``fields=["object_id"]`` is the ordinary unknown-name error."""
    host_type = _gfk_host_with_content_type_hook()
    finalize_django_types()

    with pytest.raises(ConfigurationError, match="not cascadable"):
        apply_cascade_permissions(
            host_type,
            TaggedItem.objects.all(),
            _INFO,
            fields=["object_id"],
        )


def test_mti_multiple_parent_links_both_cascade():
    """A child of TWO concrete MTI parents composes a subquery per parent link.

    Multiple concrete inheritance is outside the single ``Venue`` chain the fakeshop library app
    models, and a second parent there would reshape its documented surface; this synthetic child
    alone pins that ``django_strawberry_framework/permissions.py::_edge_plan`` yields one
    cascadable parent link per concrete parent.
    """

    class MtiLeftBase(models.Model):
        name = models.TextField()

        class Meta:
            app_label = "products"
            managed = False

    class MtiRightBase(models.Model):
        # Explicit pk so the two inherited auto pks cannot clash on the child.
        rid = models.AutoField(primary_key=True)
        label = models.TextField()

        class Meta:
            app_label = "products"
            managed = False

    class MtiBoth(MtiLeftBase, MtiRightBase):
        class Meta:
            app_label = "products"
            managed = False

    _make_type("MtiLeftBaseType", MtiLeftBase)
    # ``MtiRightBase`` has no ``id`` column (explicit ``rid`` pk), so the default
    # ``fields=("id",)`` selection cannot apply.
    _make_type("MtiRightBaseType", MtiRightBase, fields=("rid",))
    both_type = _make_type("MtiBothType", MtiBoth, primary=False)
    finalize_django_types()

    names = _cascadable_edge_names(MtiBoth)
    assert {"mtileftbase_ptr", "mtirightbase_ptr"} <= names

    # Both parent links compose a subquery (identity hooks included - the
    # registered parents' default managers are the visibility base).
    result = apply_cascade_permissions(both_type, MtiBoth.objects.all(), _INFO)
    assert str(result.query).count("IN (SELECT") == 2


def test_cascadable_edge_metadata_scan_is_cached():
    """``fields=`` validation and the walk share one cached relation-descriptor scan."""
    _edge_plan.cache_clear()
    try:
        entry_type = _make_type("CachedEdgeEntryType", Entry, primary=False)

        result = apply_cascade_permissions(entry_type, Entry.objects.all(), _INFO, fields=[])

        assert str(result.query) == str(Entry.objects.all().query)
        cache_info = _edge_plan.cache_info()
        assert cache_info.misses == 1
        assert cache_info.hits >= 1
    finally:
        _edge_plan.cache_clear()


@pytest.mark.skipif(
    os.environ.get("FAKESHOP_SHARDED") != "1",
    reason="multi-DB alias pin needs the FAKESHOP_SHARDED 'shard_b' alias (settings.py)",
)
@pytest.mark.django_db(databases=["default", "shard_b"])
def test_multi_db_subquery_pinned_to_caller_alias():
    """A ``.using("shard_b")`` caller pins every cascade subquery to ``"shard_b"`` (spec-034 Decision 8).

    Assert (via the composed subquery's ``.db``) that the cascade subquery binds to
    the caller's *resolved* alias - ``queryset.db``, the property that falls back to
    router resolution when no explicit ``.using`` was applied, not the private
    ``_db``. Built on the ``tests/optimizer/test_multi_db.py`` in-test alias pattern;
    ``FAKESHOP_SHARDED``-gated, so it does not run under a bare ``uv run pytest``.
    The edge is ``apps/products/models.py::Item.category``.
    """

    # Capture the alias the cascade actually hands the target hook. The walk builds
    # the RHS base as ``related_model._default_manager.using(queryset.db).all()``, so
    # the queryset the hook receives carries the load-bearing alias. Observing that
    # REAL RHS - rather than reconstructing a fresh ``.using(result.db)`` queryset in
    # the assertion, which would still pass against a broken default-alias build - is
    # what actually pins spec-034 Decision 8.
    received_dbs = []

    def _record_alias_hook(cls, qs, info):
        received_dbs.append(qs.db)
        return qs.exclude(name="hidden")

    target_type = _make_type("AliasCategoryType", Category, get_queryset=_record_alias_hook)
    _make_type("AliasItemType", Item, primary=False)
    finalize_django_types()

    # The caller resolved ``shard_b`` explicitly; the cascade subquery must inherit it.
    result = apply_cascade_permissions(
        registry.get(Item),
        Item.objects.using("shard_b").all(),
        _INFO,
    )
    assert result.db == "shard_b"
    assert target_type is registry.get(Category)
    # The cascade composed a constraint (an inlined ``__in`` subquery). ``str(query)``
    # forces ``DEFAULT_DB_ALIAS`` compilation, which cannot render a subquery pinned to
    # a non-default alias ("Subqueries aren't allowed across different databases"), so
    # compile against the caller's own alias (carried by both the outer query and the
    # pinned RHS) to render the inlined ``IN (SELECT ...)``.
    compiled_sql = result.query.get_compiler(using=result.db).as_sql()[0]
    assert "IN (SELECT" in compiled_sql
    # ...and the queryset it ran the target hook against was pinned to the caller's
    # resolved alias - the genuine RHS the walk built, observed inside the hook itself.
    assert received_dbs == ["shard_b"]


# --- the rest of the cascade-foundation contract -----------------------------


@pytest.mark.django_db(transaction=True)
def test_identity_hook_targets_compose_default_manager(django_assert_num_queries):
    """A registered identity-hook target STILL composes its ``_default_manager``.

    The previous ``has_custom_get_queryset() is False`` skip silently bypassed a
    registered type whose filtered ``_default_manager`` IS its visibility policy
    (the ``VisibleBranch`` proxy, whose row-level effect is
    ``test_library_inheritance_api.py::test_signage_on_a_city_less_branch_is_hidden_by_the_proxy_default_manager``).
    Every registered target now contributes a subquery - and the subqueries
    still compile into the caller's single ``SELECT``, so identity composition
    adds zero query round-trips. Every shipped products type declares a custom
    ``get_queryset``, so no live products request carries two identity-hook
    targets on one root; the custom-hook HTTP twin is
    ``test_cascade_query_count_fixed``.
    """
    _make_type("IdentItemType", Item)  # identity default - no get_queryset override
    _make_type("IdentPropertyType", Property)
    entry_type = _make_type("IdentEntryType", Entry, primary=False)
    finalize_django_types()

    assert registry.get(Item).has_custom_get_queryset() is False

    entry = services.seed_cascade_identity_chain()["entry"]

    result = apply_cascade_permissions(entry_type, Entry.objects.all(), _INFO)
    # Both registered targets compose (Item and Property; Category's type is
    # unregistered here so the transitive edge contributes nothing).
    assert str(result.query).count("IN (SELECT") == 2
    # ...at zero added round-trips: one SELECT evaluates the whole shape, and the
    # identity subqueries (unfiltered default managers) preserve every row.
    with django_assert_num_queries(1):
        assert list(result) == [entry]


@pytest.mark.django_db
def test_proxy_hook_return_over_concrete_target_accepted():
    """A hook returning a proxy queryset for a concrete-target edge is compatible.

    ``apps/library/models.py::Shelf.branch`` targets the concrete ``Branch``;
    the target hook answers with a queryset over the ``ProxyBranch`` proxy.
    Proxy and concrete siblings share one concrete table, so the subquery is
    sound; the validator keys on ``_meta.concrete_model``, not the class.
    """
    # The concrete target's hook answers with a PROXY queryset.
    _make_type(
        "PcBranchType",
        Branch,
        get_queryset=lambda cls, qs, info: ProxyBranch.objects.using(qs.db).exclude(
            name="hidden",
        ),
    )
    shelf_type = _make_type("PcShelfType", Shelf, primary=False)
    finalize_django_types()

    visible = Branch.objects.create(name="ok")
    hidden = Branch.objects.create(name="hidden")
    keeps = Shelf.objects.create(code="keeps", branch=visible)
    Shelf.objects.create(code="drops", branch=hidden)

    result = apply_cascade_permissions(shelf_type, Shelf.objects.all(), _INFO)
    assert sorted(result.values_list("code", flat=True)) == ["keeps"]
    assert keeps in result


@pytest.mark.django_db
def test_unregistered_target_model_skipped():
    """An edge whose target model has no registered ``DjangoType`` is skipped."""
    # Only EntryType is registered; Item / Property / Category have no DjangoType,
    # so ``registry.get`` returns ``None`` for each edge and the walk skips them.
    entry_type = _make_type("LoneEntryType", Entry)
    finalize_django_types()

    assert registry.get(Item) is None
    assert registry.get(Property) is None

    result = apply_cascade_permissions(entry_type, Entry.objects.all(), _INFO)
    assert "IN (SELECT" not in str(result.query)
    assert str(result.query) == str(Entry.objects.all().query)


@pytest.mark.django_db
def test_secondary_type_never_cascade_target():
    """``registry.get`` returns the primary; a stricter secondary hook never cascades."""
    # Category has a permissive PRIMARY (identity) and a stricter SECONDARY that
    # would hide rows. The Item->Category edge resolves via ``registry.get`` to the
    # PRIMARY: the identity primary composes its (unfiltered) default manager, so
    # the subquery is present but the stricter secondary hook does NOT narrow.
    _make_type("CatPrimaryType", Category, primary=True)  # identity, primary
    _make_type(
        "CatSecondaryType",
        Category,
        get_queryset=lambda cls, qs, info: qs.none(),  # would hide everything
        primary=False,
    )
    item_type = _make_type("SecItemType", Item, primary=False)
    finalize_django_types()

    assert registry.get(Category).has_custom_get_queryset() is False  # the primary

    services.seed_public_category_with_item()

    result = apply_cascade_permissions(item_type, Item.objects.all(), _INFO)
    # Resolved through the permissive primary (identity default manager): the
    # subquery composes, and the secondary's ``qs.none()`` never applies - the
    # row survives (a secondary-narrowed walk would return zero rows).
    assert "IN (SELECT" in str(result.query)
    assert result.count() == 1


def test_secondary_root_self_edge_reaches_primary_then_fails_closed():
    """A secondary-rooted self-edge resolves to the PRIMARY, whose recursion fails closed.

    ``apps/scalars/models.py::ScalarSpecimen.parent`` is a self-referential
    key; its ``tag`` edge targets an unregistered model and is skipped. The
    ``parent`` edge re-reaches the same model via ``registry.get`` -> the
    **primary** (a different class from the rooting secondary, so THAT step is
    not a cycle). The primary's own cascading hook then re-enters the primary on
    its self-edge - a genuine recursion - and the walk raises the path-rich
    cycle error instead of silently under-narrowing.
    """
    _make_type(
        "SelfRefPrimaryType",
        ScalarSpecimen,
        get_queryset=lambda cls, qs, info: apply_cascade_permissions(
            cls,
            qs.exclude(label="primary_hidden"),
            info,
        ),
        primary=True,
    )
    secondary = _make_type(
        "SelfRefSecondaryType",
        ScalarSpecimen,
        get_queryset=lambda cls, qs, info: apply_cascade_permissions(
            cls,
            qs.exclude(label="secondary_hidden"),
            info,
        ),
        primary=False,
    )
    finalize_django_types()

    with pytest.raises(ConfigurationError) as excinfo:
        apply_cascade_permissions(secondary, ScalarSpecimen.objects.all(), _INFO)
    # The path shows the secondary root reaching the primary, then the primary
    # re-entering itself: secondary.parent -> primary.parent -> primary.
    assert "SelfRefSecondaryType.parent -> SelfRefPrimaryType.parent -> SelfRefPrimaryType" in str(
        excinfo.value,
    )
    assert _cascade_state.get() is None


class _CtTarget(models.Model):
    """Hook-return-contract fixture target (shared by the battery below).

    The battery composes hostile hooks over this target through ``_CtParent.target`` and returns
    ``_CtTargetChild`` (an MTI child, a different concrete table) and ``_CtOther`` (an unrelated
    table) as wrong-table results, rendered through
    ``django_strawberry_framework/permissions.py::_edge_error_renderer``.
    """

    name = models.TextField()

    class Meta:
        app_label = "products"
        managed = False


class _CtTargetChild(_CtTarget):
    """MTI child of the fixture target - an INCOMPATIBLE hook-return table."""

    extra = models.TextField()

    class Meta:
        app_label = "products"
        managed = False


class _CtOther(models.Model):
    """An unrelated model - an INCOMPATIBLE hook-return table."""

    name = models.TextField()

    class Meta:
        app_label = "products"
        managed = False


class _CtParent(models.Model):
    name = models.TextField()
    target = models.ForeignKey(_CtTarget, on_delete=models.CASCADE, related_name="parents")

    class Meta:
        app_label = "products"
        managed = False


def _register_ct_pair(hook):
    """Register the hook-return fixture pair; return the parent type."""
    _make_type("CtTargetType", _CtTarget, get_queryset=hook)
    parent_type = _make_type("CtParentType", _CtParent, primary=False)
    finalize_django_types()
    return parent_type


def _values_projection(cls, qs, info):
    return qs.exclude(name="hidden").values("id", "name")


def _values_list_projection(cls, qs, info):
    return qs.exclude(name="hidden").values_list("name")


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize(
    "hook",
    [
        pytest.param(_values_projection, id="values"),
        pytest.param(_values_list_projection, id="values-list"),
    ],
)
def test_hook_values_and_values_list_projections_are_normalized(hook):
    """A hook's ``.values(...)`` / ``.values_list(...)`` return is re-projected safely.

    The subquery is normalized to ``field.target_field.attname``, so a consumer
    projection can no longer compare the FK against the wrong column (the old
    contract passed a ``.values("name")`` straight into ``__in`` - a silent
    wrong-column narrowing) and a multi-column ``.values()`` no longer raises at
    evaluation. Both shapes narrow by the hook's FILTER, not its projection.
    """
    with _tables(_CtTarget, _CtParent):
        parent_type = _register_ct_pair(hook)

        visible = _CtTarget.objects.create(name="t")
        hidden = _CtTarget.objects.create(name="hidden")
        keeps = _CtParent.objects.create(name="keeps", target=visible)
        _CtParent.objects.create(name="drops", target=hidden)

        result = apply_cascade_permissions(parent_type, _CtParent.objects.all(), _INFO)
        assert sorted(result.values_list("name", flat=True)) == ["keeps"]
        assert keeps in result


def _profiles_by_genre(*, visible, hidden, attack_code):
    """Seed one ``PatronProfile`` per genre, keyed by genre name through ``favorite_genre``."""
    for postal_code, genre in (("keeps", visible), (attack_code, hidden)):
        PatronProfile.objects.create(
            patron=Patron.objects.create(name=f"patron-{postal_code}"),
            postal_code=postal_code,
            favorite_genre=genre,
        )


@pytest.mark.django_db
def test_to_field_edge_compares_target_column():
    """A ``ForeignKey(to_field=...)`` edge binds the ``to_field`` column, never the pk.

    ``apps/library/models.py::PatronProfile.favorite_genre`` is keyed by
    ``Genre.name``, so the normalization projects ``field.target_field.attname``
    (``name``) and even a hook that explicitly projected the pk narrows by the
    correct column. ``PatronProfile.patron`` targets an unregistered model and
    is skipped. No shipped ``GenreType`` hook exists, so no request composes
    this edge.
    """
    visible = Genre.objects.create(name="ok")
    hidden = Genre.objects.create(name="hx")
    # The hook projects the WRONG column (the pk); normalization overrides it.
    _make_type(
        "TfGenreType",
        Genre,
        get_queryset=lambda cls, qs, info: qs.exclude(pk=hidden.pk).values("id"),
    )
    profile_type = _make_type(
        "TfPatronProfileType",
        PatronProfile,
        fields=("postal_code",),
        primary=False,
    )
    finalize_django_types()
    _profiles_by_genre(visible=visible, hidden=hidden, attack_code="drops")

    result = apply_cascade_permissions(profile_type, PatronProfile.objects.all(), _INFO)
    # The subquery selects the ``name`` column, not ``id``; whether the ``U0``
    # alias is quoted depends on the Django version, so either spelling matches.
    assert re.search(
        r'"favorite_genre_id" IN \(SELECT "?U0"?\."name" AS "name"',
        str(result.query),
    )
    assert sorted(result.values_list("postal_code", flat=True)) == ["keeps"]
    assert PatronProfile.objects.get(postal_code="keeps") in result


def _hook_returns_list(cls, qs, info):
    return []


def _hook_unrelated_model(cls, qs, info):
    return _CtOther.objects.using(qs.db).all()


def _hook_mti_child(cls, qs, info):
    return _CtTargetChild.objects.using(qs.db).all()


def _hook_sliced(cls, qs, info):
    return qs[:5]


def _hook_distinct(cls, qs, info):
    return qs.distinct("name")


def _hook_union(cls, qs, info):
    return qs.union(qs)


def _hook_intersection(cls, qs, info):
    return qs.intersection(qs)


def _hook_grouped_count(cls, qs, info):
    return qs.annotate(n=models.Count("id"))


def _hook_grouped_values(cls, qs, info):
    return qs.values("name").annotate(n=models.Count("id"))


def _hook_extra_shadow(cls, qs, info):
    return qs.extra(select={"id": "name"})


def _hook_annotate_shadow(cls, qs, info):
    return qs.values("name").annotate(id=models.Value(1))


def _hook_off_alias(cls, qs, info):
    return qs.using("bogus_alias")


@pytest.mark.parametrize(
    ("hook", "match"),
    [
        pytest.param(_hook_returns_list, "must return a QuerySet", id="list"),
        pytest.param(_hook_unrelated_model, "concrete table", id="wrong-table"),
        pytest.param(_hook_mti_child, "concrete table", id="mti-child-table"),
        pytest.param(_hook_sliced, "sliced", id="sliced"),
        pytest.param(_hook_distinct, "distinct", id="distinct"),
        pytest.param(_hook_union, "combined", id="union"),
        pytest.param(_hook_intersection, "combined", id="intersection"),
        pytest.param(_hook_grouped_count, "grouped", id="grouped-count"),
        pytest.param(_hook_grouped_values, "grouped", id="grouped-values"),
        pytest.param(_hook_extra_shadow, "shadows", id="extra-shadow"),
        pytest.param(_hook_annotate_shadow, "shadows", id="annotate-shadow"),
        pytest.param(_hook_off_alias, "alias", id="off-alias"),
    ],
)
def test_hook_return_rejections_fail_closed(hook, match):
    """Non-queryset / wrong-table / sliced / distinct / combined / grouped / shadowed / re-aliased returns raise.

    Every shape that would compose a wrong or wrong-database membership predicate
    is a loud ``ConfigurationError`` at composition time - never a silent
    mis-narrowing or a backend-dependent evaluation error. Pure composition: the
    raise fires before any SQL, so no tables are needed. The shape /
    concrete-table / explicit-alias rejections come from the SHARED visibility
    boundary (``utils/querysets.py``), rendered through the cascade's per-edge
    error seam, so the path-rich prose asserted here survives the move; the
    SQL-composability rejections stay cascade-local. A ``Manager`` return is no
    longer in this battery - the boundary coerces it
    (``test_hook_manager_return_is_coerced``). The combined / grouped /
    extra-shadow shapes are the ones where re-projecting to the target column
    would change SEMANTICS, not just the selected column: ``.values(...)`` on a
    union only rewrites the outer projection (each branch keeps its original
    column), on a grouped queryset it changes the GROUP BY (widening the visible
    set), and under a shadowing ``extra(select=...)`` alias it selects the
    raw-SQL expression instead of the model column.
    ``test_annotation_alias_shadow_cannot_bypass_visibility`` proves the
    real-row leak the annotate-shadow rejection closes.
    """
    parent_type = _register_ct_pair(hook)
    with pytest.raises(ConfigurationError, match=match):
        apply_cascade_permissions(parent_type, _CtParent.objects.all(), _INFO)
    assert _cascade_state.get() is None


def test_hook_manager_return_is_coerced():
    """A ``Manager`` hook return is coerced through ``.all()``, not rejected.

    The shared visibility boundary's canonical-Manager contract (the
    get_queryset-visibility-boundary decision): a hook returning
    ``Model.objects`` composes exactly like ``Model.objects.all()`` - the
    prior contract rejected it. Pure composition, so no tables are needed.
    """
    registry.clear()
    parent_type = _register_ct_pair(lambda cls, qs, info: _CtTarget.objects)
    result = apply_cascade_permissions(parent_type, _CtParent.objects.all(), _INFO)
    assert "IN (SELECT" in str(result.query).upper()
    assert _cascade_state.get() is None


def test_unpinned_hook_return_is_repinned_to_root_alias():
    """An UNROUTED hook return is repinned onto the cascade's root alias.

    The shared boundary's alias contract replaces the old reject-on-``.db``
    check: a hook that builds a fresh queryset (``Model.objects.filter(...)``,
    ``_db`` unset) no longer trips a cross-database rejection when the root
    runs on a non-default alias - the result is normalized onto the root
    alias with ``.using(...)``. Only an EXPLICITLY divergent ``.using(...)``
    fails closed (the ``"alias"`` row in the rejection battery). Alias-state
    only - the alias never resolves a connection, so no secondary database
    (and no table) is needed.
    """
    registry.clear()
    parent_type = _register_ct_pair(
        lambda cls, qs, info: _CtTarget.objects.filter(name="visible"),
    )
    result = apply_cascade_permissions(
        parent_type,
        _CtParent.objects.all().using("bogus_alias"),
        _INFO,
    )
    assert result.db == "bogus_alias"
    assert _cascade_state.get() is None


def test_hostile_hook_clone_override_is_neutralized_by_sealing_in_cascade():
    """A hostile queryset subclass overriding ``.all()`` is neutralized by sealing.

    The boundary seals the hook return into a fresh plain ``QuerySet`` rebuilt
    from its query state, so the overridden ``.all()`` never runs; the cascade
    then re-projects that sealed queryset with a genuine ``.values(...)``. The
    visibility predicate survives, and the composed ``__in`` subquery carries it.
    """

    class _StickyQuerySet(models.QuerySet):
        def all(self):  # a predicate-dropping clone if ever dispatched
            return _CtTarget.objects.all()

    def _hostile_hook(cls, qs, info):
        return models.QuerySet.filter(
            _StickyQuerySet(model=_CtTarget, using=qs.db),
            name="visible",
        )

    registry.clear()
    parent_type = _register_ct_pair(_hostile_hook)
    result = apply_cascade_permissions(parent_type, _CtParent.objects.all(), _INFO)
    assert "visible" in str(result.query)  # the sealed target predicate reached the subquery
    assert _cascade_state.get() is None


@pytest.mark.django_db(transaction=True)
def test_hostile_values_override_end_to_end_is_neutralized_by_sealing():
    """A target hook overriding ``_values`` cannot keep a parent whose target is hidden.

    ``QuerySet.values()`` delegates to ``self._values(...)``; the cascade re-projects
    the sealed target queryset to the FK's target column via ``.values(attname)``. A
    hook returning a subclass whose ``_values`` re-projects the FULL unfiltered target
    set would (if dispatched) compose ``target_id IN (SELECT <all ids>)`` and keep the
    hidden-target parent. The seal rebuilds a plain ``QuerySet`` from the validated
    query state, so the override never runs: the parent pointing at the hidden target
    is filtered out end-to-end. Real visible/hidden rows make the assertion non-vacuous.
    """

    class _ValuesEraser(models.QuerySet):
        def _values(self, *fields, **expressions):  # re-projects the UNFILTERED set
            return models.QuerySet._values(_CtTarget.objects.all(), *fields, **expressions)

    def _hostile_hook(cls, qs, info):
        return models.QuerySet.filter(
            _ValuesEraser(model=_CtTarget, using=qs.db),
            name="visible",
        )

    with _tables(_CtTarget, _CtParent):
        parent_type = _register_ct_pair(_hostile_hook)

        visible = _CtTarget.objects.create(name="visible")
        hidden = _CtTarget.objects.create(name="hidden")
        keeps = _CtParent.objects.create(name="keeps", target=visible)
        _CtParent.objects.create(name="drops", target=hidden)

        result = apply_cascade_permissions(parent_type, _CtParent.objects.all(), _INFO)
        # The sealed re-projection binds only the visible target id; the hidden-target
        # parent drops. A dispatched ``_values`` override would have kept it.
        assert sorted(result.values_list("name", flat=True)) == ["keeps"]
        assert keeps in result
        assert _cascade_state.get() is None


def test_unsealable_hook_query_class_fails_closed_with_cascade_prose():
    """A hook returning a foreign ``Query`` class fails closed with path-rich cascade prose.

    Where sealing is impossible (a foreign ``Query`` subclass cannot be
    faithfully rebuilt into a framework-owned execution queryset) the cascade
    fails closed with the ``untrusted`` defect, routed through the per-edge
    renderer so the prose stays path-rich.
    """
    from django.db.models import sql

    class _ForeignQuery(sql.Query):
        pass

    def _hostile_hook(cls, qs, info):
        target = _CtTarget.objects.filter(name="visible").using(qs.db)
        target._query = _ForeignQuery(_CtTarget)
        return target

    registry.clear()
    parent_type = _register_ct_pair(_hostile_hook)
    with pytest.raises(
        ConfigurationError,
        match="cannot be sealed into a framework-owned execution queryset.*for the cascade subquery",
    ):
        apply_cascade_permissions(parent_type, _CtParent.objects.all(), _INFO)
    assert _cascade_state.get() is None


class _ConsumerUpper(models.Func):
    """A project's own ``Func`` subclass: ordinary Django usage the seal cannot rebuild."""

    function = "UPPER"


def test_a_hook_carrying_a_consumer_expression_names_what_the_cascade_can_rebuild():
    """An edge hook refused as ``untrusted`` names the full cause list and the advice."""

    def _hook(cls, qs, info):
        return _CtTarget.objects.using(qs.db).annotate(u=_ConsumerUpper(models.F("name")))

    registry.clear()
    parent_type = _register_ct_pair(_hook)
    with pytest.raises(ConfigurationError) as excinfo:
        apply_cascade_permissions(parent_type, _CtParent.objects.all(), _INFO)
    message = str(excinfo.value)
    assert "for the cascade subquery" in message
    assert "a consumer-defined expression, lookup" in message
    assert "Build the queryset with Django's own" in message
    assert "Return plain rows" not in message
    assert _cascade_state.get() is None


@pytest.mark.django_db(transaction=True)
def test_annotation_alias_shadow_cannot_bypass_visibility():
    """A hook annotating the target column to a constant cannot smuggle a hidden pk.

    The security-critical vector: Django rejects a bare ``annotate(id=Value(pk))``
    (name conflicts with the field), but ``values("name").annotate(id=Value(pk))``
    is permitted, stays ungrouped (``Value`` is not an aggregate), and would
    re-project to the injected constant -- composing
    ``target_id IN (SELECT <hidden_pk> AS id FROM target WHERE visible)`` and
    letting a parent pointing at a hidden target survive whenever any visible
    target exists. The guard rejects it at composition; this test also builds
    the un-guarded predicate by hand to prove the bypass is real, not theoretical.
    """
    with _tables(_CtTarget, _CtParent):
        visible = _CtTarget.objects.create(name="visible")
        hidden = _CtTarget.objects.create(name="hidden")
        keeps = _CtParent.objects.create(name="keeps", target=visible)
        attack = _CtParent.objects.create(name="attack", target=hidden)

        # The malicious hook: narrow to the nominally visible target, but alias
        # the pk to the hidden row's id so a naive re-projection would select it.
        def _shadow_hook(cls, qs, info):
            return qs.filter(name="visible").values("name").annotate(id=models.Value(hidden.pk))

        parent_type = _register_ct_pair(_shadow_hook)
        with pytest.raises(ConfigurationError, match="shadows"):
            apply_cascade_permissions(parent_type, _CtParent.objects.all(), _INFO)
        assert _cascade_state.get() is None

        # Proof the rejection is load-bearing: the shape the guard blocks, fed
        # through the old ``.values(attname)`` re-projection by hand, selects
        # ONLY the injected constant (the hidden target's pk) -- so exactly the
        # attack row survives, and the row pointing at the visible target is
        # collateral damage. The bypass is real, not theoretical.
        leaked_subquery = _shadow_hook(parent_type, _CtTarget.objects.all(), _INFO).values("id")
        leaked = _CtParent.objects.filter(target__in=leaked_subquery)
        assert list(leaked.values_list("name", flat=True)) == ["attack"]


@pytest.mark.django_db
def test_annotation_alias_shadow_to_field_cannot_bypass_visibility():
    """The ``to_field`` twin: annotating the ``to_field`` column to a constant is rejected.

    ``PatronProfile.favorite_genre`` re-projects to ``Genre.name``; a hook doing
    ``values("id").annotate(name=Value(<hidden_name>))`` would smuggle the
    hidden row's ``name`` exactly as the pk case smuggles its ``id``.
    """
    visible = Genre.objects.create(name="visible")
    hidden = Genre.objects.create(name="hidden")
    _profiles_by_genre(visible=visible, hidden=hidden, attack_code="attack")

    _make_type(
        "TfShadowGenreType",
        Genre,
        get_queryset=lambda cls, qs, info: qs.values("id").annotate(
            name=models.Value(hidden.name),
        ),
    )
    profile_type = _make_type(
        "TfShadowPatronProfileType",
        PatronProfile,
        fields=("postal_code",),
        primary=False,
    )
    finalize_django_types()

    with pytest.raises(ConfigurationError, match="'name'"):
        apply_cascade_permissions(profile_type, PatronProfile.objects.all(), _INFO)
    assert _cascade_state.get() is None


def test_nested_application_off_root_alias_fails_closed():
    """A nested cascade whose queryset left the root alias raises before composing.

    A hook that re-aliases its queryset and then cascades would otherwise build
    subqueries Django cannot legally execute cross-database (or, worse, compose
    against the wrong data). The nested application validates ``queryset.db``
    against the pinned root alias and fails closed.
    """

    def _realiasing_hook(cls, qs, info):
        return apply_cascade_permissions(cls, qs.using("bogus_alias"), info)

    registry.clear()
    parent_type = _register_ct_pair(_realiasing_hook)
    with pytest.raises(ConfigurationError, match="pinned to"):
        apply_cascade_permissions(parent_type, _CtParent.objects.all(), _INFO)
    assert _cascade_state.get() is None


def _root_manager():
    return _CtParent.objects


def _root_list():
    return []


def _root_wrong_table():
    return _CtOther.objects.all()


def _root_sliced():
    return _CtParent.objects.all()[:5]


def _root_combined():
    return _CtParent.objects.all().union(_CtParent.objects.all())


@pytest.mark.parametrize(
    ("root_factory", "match"),
    [
        pytest.param(
            _root_manager,
            "apply_cascade_permissions.*got Manager",
            id="manager",
        ),
        pytest.param(_root_list, "apply_cascade_permissions.*got list", id="list"),
        pytest.param(
            _root_wrong_table,
            "apply_cascade_permissions.*concrete table",
            id="wrong-table",
        ),
        pytest.param(_root_sliced, "apply_cascade_permissions.*sliced", id="sliced"),
        pytest.param(
            _root_combined,
            "apply_cascade_permissions.*combined",
            id="combined",
        ),
    ],
)
def test_root_queryset_shape_rejections(root_factory, match):
    """The root call rejects non-querysets, wrong-model, sliced, and combined roots loudly.

    Sliced and combined roots cannot be ``.filter(...)``-narrowed; without the
    up-front rejection the walk would leak a raw ``TypeError`` /
    ``NotSupportedError`` from Django mid-composition instead of the
    fail-closed configuration error.

    Every message names ``apply_cascade_permissions``: the shape checks are made
    by the shared visibility source boundary, but the consumer called THIS
    helper from inside their own hook, so the cascade's renderer keeps the
    attribution (and the cascade's recourse) rather than telling them about a
    function they never called.
    """
    parent_type = _register_ct_pair(None)
    with pytest.raises(ConfigurationError, match=match):
        apply_cascade_permissions(parent_type, root_factory(), _INFO)
    assert _cascade_state.get() is None


def test_unsealable_root_query_class_fails_closed_with_cascade_prose():
    """A root carrying a foreign ``Query`` class fails closed, attributed to the cascade.

    The root is sealed before the walk narrows it, and a foreign ``Query``
    subclass cannot be faithfully rebuilt into a framework-owned execution
    queryset. The boundary's ``untrusted`` defect is the cascade's to explain:
    the consumer passed this object to ``apply_cascade_permissions``.
    """
    from django.db.models import sql

    class _ForeignRootQuery(sql.Query):
        pass

    parent_type = _register_ct_pair(None)
    hostile_root = _CtParent.objects.all()
    hostile_root._query = _ForeignRootQuery(_CtParent)

    with pytest.raises(
        ConfigurationError,
        match="apply_cascade_permissions.*cannot be sealed into a framework-owned",
    ):
        apply_cascade_permissions(parent_type, hostile_root, _INFO)
    assert _cascade_state.get() is None


def test_a_root_carrying_a_consumer_expression_names_what_the_cascade_can_rebuild():
    """A root refused as ``untrusted`` names the full cause list and the advice."""
    parent_type = _register_ct_pair(None)
    root = _CtParent.objects.annotate(u=_ConsumerUpper(models.F("name")))
    with pytest.raises(ConfigurationError) as excinfo:
        apply_cascade_permissions(parent_type, root, _INFO)
    message = str(excinfo.value)
    assert message.startswith("apply_cascade_permissions for ")
    assert "a consumer-defined expression, lookup" in message
    assert "Build the queryset with Django's own" in message
    assert "Pass plain query state" not in message
    assert _cascade_state.get() is None


@pytest.mark.django_db(transaction=True)
def test_values_root_is_supported_input():
    """A ``.values(...)`` root still cascades - the seal runs model-rows-off here.

    The cascade never iterates the root's rows; it composes ``.filter(...)`` onto
    them, exactly as it accepts a ``.values()`` hook RETURN. Sealing the root
    must not quietly narrow the accepted input to model rows.
    """
    with _tables(_CtTarget, _CtParent):
        parent_type = _register_ct_pair(
            lambda cls, qs, info: qs.exclude(name="hidden"),
        )
        visible = _CtTarget.objects.create(name="visible")
        hidden = _CtTarget.objects.create(name="hidden")
        _CtParent.objects.create(name="keeps", target=visible)
        _CtParent.objects.create(name="drops", target=hidden)

        result = apply_cascade_permissions(
            parent_type,
            _CtParent.objects.values("name"),
            _INFO,
        )

        assert [row["name"] for row in result] == ["keeps"]
        assert _cascade_state.get() is None


@pytest.mark.django_db
def test_fields_scopes_walk():
    """``fields=["item"]`` cascades only ``item`` and leaves ``property`` alone.

    Shipped products hooks pass ``fields=None``; a live request cannot select a
    subset of cascade edges.
    """

    def _exclude_private(cls, qs, info):
        return qs.filter(is_private=False)

    _make_type("FsItemType", Item, get_queryset=_exclude_private)
    _make_type("FsPropertyType", Property, get_queryset=_exclude_private)
    entry_type = _make_type("FsEntryType", Entry, primary=False)
    finalize_django_types()

    # ``survives_prop``'s property is hidden but its item is public; with
    # ``fields=["item"]`` the property edge is NOT cascaded, so the row survives.
    rows = services.seed_field_scope_split()
    keeps = rows["keeps"]
    drops_item = rows["drops_item"]
    survives_prop = rows["survives_prop"]

    result = apply_cascade_permissions(entry_type, Entry.objects.all(), _INFO, fields=["item"])
    names = set(result.values_list("value", flat=True))
    assert names == {keeps.value, survives_prop.value}
    assert keeps in result
    assert survives_prop in result
    assert drops_item not in result


def test_fields_unknown_name_raises():
    """An unknown ``fields=`` name raises ConfigurationError naming field/model/set (spec-034 Decision 9)."""
    _make_type("UnkItemType", Item)
    entry_type = _make_type("UnkEntryType", Entry, primary=False)
    finalize_django_types()

    with pytest.raises(ConfigurationError) as excinfo:
        apply_cascade_permissions(entry_type, Entry.objects.all(), _INFO, fields=["nonexistent"])
    message = str(excinfo.value)
    assert "nonexistent" in message  # the offending entry
    assert "Entry" in message  # the model
    # the cascadable set (Entry's forward FKs)
    assert "item" in message
    assert "property" in message


def test_fields_non_cascadable_name_raises():
    """A known-but-non-cascadable ``fields=`` name (M2M / reverse / scalar) raises (spec-034 Decision 9)."""
    entry_type = _make_type("NonCascItemEntryType", Entry, primary=False)
    finalize_django_types()

    # ``value`` is a real scalar field on Entry but not a cascadable forward relation.
    with pytest.raises(ConfigurationError) as excinfo:
        apply_cascade_permissions(entry_type, Entry.objects.all(), _INFO, fields=["value"])
    message = str(excinfo.value)
    assert "value" in message
    assert "Entry" in message
    assert "item" in message  # the cascadable set is named


@pytest.mark.django_db
def test_fields_valid_but_unregistered_target_accepted():
    """A cascadable edge whose target model has no registered type is accepted+skipped.

    ``item`` is cascadable, but ``Item`` has no registered ``DjangoType`` here ->
    the name validates clean and the walk contributes nothing (no raise, no
    subquery) - there is no visibility policy to apply. Consistent with
    ``fields=None``. (A registered IDENTITY-hook target is the opposite: it
    composes its default manager - see
    ``test_identity_hook_targets_compose_default_manager``.)
    """
    entry_type = _make_type("HooklessEntryType", Entry)
    finalize_django_types()

    assert registry.get(Item) is None

    result = apply_cascade_permissions(entry_type, Entry.objects.all(), _INFO, fields=["item"])
    assert "IN (SELECT" not in str(result.query)
    assert str(result.query) == str(Entry.objects.all().query)


def test_fields_bare_string_raises():
    """``fields="item"`` (a bare string) raises before any name lookup (spec-034 Decision 9).

    Without the ``isinstance(fields, str)`` guard the walk would validate ``'i'``,
    ``'t'``, ``'e'``, ``'m'`` as field names and surface a misleading "'i' is not
    cascadable" - the guard names the non-string-iterable requirement instead.
    """
    entry_type = _make_type("BareStrEntryType", Entry, primary=False)
    finalize_django_types()

    with pytest.raises(ConfigurationError) as excinfo:
        apply_cascade_permissions(entry_type, Entry.objects.all(), _INFO, fields="item")
    message = str(excinfo.value)
    # Names the non-string-iterable requirement and the bracket fix...
    assert "non-string iterable" in message
    assert "['item']" in message or '["item"]' in message
    # ...and does NOT surface a misleading per-character ``'i'`` lookup.
    assert "'i'" not in message


def test_fields_non_iterable_raises_configuration_error():
    """``fields=1`` (a non-iterable) raises ConfigurationError, not a raw TypeError.

    ``set(1)`` would escape as ``TypeError: 'int' object is not iterable`` - harder
    for a consumer to catch consistently and silent about the field-name-iterable
    contract. The validator rethrows it as the package's typed configuration error.
    """
    entry_type = _make_type("NonIterFieldsEntryType", Entry, primary=False)
    finalize_django_types()

    with pytest.raises(ConfigurationError) as excinfo:
        apply_cascade_permissions(entry_type, Entry.objects.all(), _INFO, fields=1)
    message = str(excinfo.value)
    assert "non-string iterable" in message
    assert "1" in message


def test_fields_unhashable_entry_raises_configuration_error():
    """``fields=[["item"]]`` (unhashable entry) raises ConfigurationError, not a raw TypeError.

    A nested list iterates fine but is not a field-name string; the ``list``-first
    validation catches it on the string check before any ``set(...)`` hashing, so
    ``TypeError: unhashable type: 'list'`` never escapes.
    """
    entry_type = _make_type("UnhashableFieldsEntryType", Entry, primary=False)
    finalize_django_types()

    with pytest.raises(ConfigurationError) as excinfo:
        apply_cascade_permissions(entry_type, Entry.objects.all(), _INFO, fields=[["item"]])
    message = str(excinfo.value)
    assert "field-name strings" in message
    assert "['item']" in message or '["item"]' in message


def test_fields_non_string_entry_raises_configuration_error():
    """``fields=[1]`` raises a clear "must be field-name strings" error, not a confusing name diff.

    Before the string check, ``set([1]) - cascadable`` surfaced "[1] ... are not
    cascadable" - implying ``1`` is a (misspelled) field name. The dedicated string
    check names the real contract instead.
    """
    entry_type = _make_type("NonStrFieldsEntryType", Entry, primary=False)
    finalize_django_types()

    with pytest.raises(ConfigurationError) as excinfo:
        apply_cascade_permissions(entry_type, Entry.objects.all(), _INFO, fields=[1])
    message = str(excinfo.value)
    assert "field-name strings" in message
    # Not the misleading "not cascadable" name-diff wording.
    assert "not cascadable" not in message


def test_fields_empty_list_cascades_nothing():
    """``fields=[]`` validates clean and cascades zero edges (a defined no-op).

    An empty iterable is well-formed (``set() - cascadable == set()``) and unambiguous
    (zero edges), so - unlike the bare-string case - it does *not* raise; the walk
    cascades nothing. Distinct from ``fields=None``, which cascades every qualifying
    edge (Edge cases). Supports programmatically-built edge sets that resolve empty.
    """
    _make_type(
        "EmptyItemType",
        Item,
        get_queryset=lambda cls, qs, info: qs.filter(is_private=False),
    )
    entry_type = _make_type("EmptyEntryType", Entry, primary=False)
    finalize_django_types()

    # ``fields=[]`` -> no raise, no subquery composed.
    result = apply_cascade_permissions(entry_type, Entry.objects.all(), _INFO, fields=[])
    assert "IN (SELECT" not in str(result.query)
    assert str(result.query) == str(Entry.objects.all().query)
    # ...distinct from ``fields=None``, which DOES cascade the ``item`` edge.
    cascaded = apply_cascade_permissions(entry_type, Entry.objects.all(), _INFO, fields=None)
    assert "IN (SELECT" in str(cascaded.query)


@pytest.mark.django_db
def test_sync_helper_raises_syncmisuseerror_on_async_target_hook():
    """A target ``async def get_queryset`` reached from the sync walk raises SyncMisuseError.

    Coroutine closed first (no ``RuntimeWarning``); message names the target type.
    spec-034 Decision 10. The unawaited coroutine is closed by ``apply_type_visibility_sync``
    before the raise, so no "coroutine was never awaited" ``RuntimeWarning`` fires -
    the suite's ``filterwarnings = error`` policy (pytest.ini) would turn any such
    warning into a hard error, so a leaked coroutine fails this test by construction.

    The message carries the *cascade-specific* recourse: make the
    target hook sync, or scope ``fields=`` to skip the async-hooked edge. It must
    NOT reach for the Relay-surface wording, because ``aapply_cascade_permissions``
    wraps this same sync walk and cannot await an async hook either - pointing a
    cascade consumer at an "async resolver" would be a dead end.
    """

    async def _async_hook(cls, qs, info):
        return qs

    _make_type("AsyncTargetItemType", Item, get_queryset=_async_hook)
    entry_type = _make_type("AsyncTargetEntryType", Entry, primary=False)
    finalize_django_types()

    with pytest.raises(SyncMisuseError) as excinfo:
        apply_cascade_permissions(entry_type, Entry.objects.all(), _INFO)
    message = str(excinfo.value)
    # Names the offending target type...
    assert "AsyncTargetItemType" in message
    # ...and the cascade recourses (sync hook / fields= skip), not the Relay wording.
    assert "fields=" in message
    assert "get_queryset sync" in message
    assert "Relay node defaults" not in message


async def test_aapply_runs_walk_off_event_loop():
    """``aapply_cascade_permissions`` runs the sync walk via ``sync_to_async`` (spec-034 Decision 10).

    Assert the walk executes and the ``ContextVar`` seen-set installed inside the
    worker (asgiref ``copy_context``) does not leak back into the awaiting task -
    ``_cascade_state.get()`` stays ``None`` in the async caller after the await.
    """
    from asgiref.sync import sync_to_async

    @sync_to_async
    def _setup():
        _make_type(
            "OffLoopItemType",
            Item,
            get_queryset=lambda cls, qs, info: qs.filter(is_private=False),
        )
        entry_type = _make_type("OffLoopEntryType", Entry, primary=False)
        finalize_django_types()
        return entry_type

    entry_type = await _setup()

    # Before the await the var is clean in the event-loop task.
    assert _cascade_state.get() is None
    result = await aapply_cascade_permissions(entry_type, Entry.objects.all(), _INFO)
    # The walk composed a constraint (the cascade ran off the loop)...
    assert "IN (SELECT" in str(result.query)
    # ...and the worker-thread seen-set did NOT leak back into the awaiting task.
    assert _cascade_state.get() is None


async def test_aapply_async_target_hook_still_raises():
    """An ``async def`` target hook raises SyncMisuseError from the async variant too (Decision 10)."""
    from asgiref.sync import sync_to_async

    async def _async_hook(cls, qs, info):
        return qs

    @sync_to_async
    def _setup():
        _make_type("AAsyncTargetItemType", Item, get_queryset=_async_hook)
        entry_type = _make_type("AAsyncTargetEntryType", Entry, primary=False)
        finalize_django_types()
        return entry_type

    entry_type = await _setup()

    with pytest.raises(SyncMisuseError):
        await aapply_cascade_permissions(entry_type, Entry.objects.all(), _INFO)
    assert _cascade_state.get() is None


def _specimen(label, **fields):
    """Create a ``ScalarSpecimen`` row carrying only the columns a cascade pin reads."""
    return ScalarSpecimen.objects.create(
        label=label,
        occurred_on=datetime.date(2024, 1, 1),
        occurred_at=datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc),
        occurred_time=datetime.time(9, 0),
        external_id=uuid.uuid4(),
        **fields,
    )


def test_self_referential_cascading_hook_fails_closed():
    """A ``parent = FK('self')`` edge whose own hook cascades is a genuine recursion.

    ``apps/scalars/models.py::ScalarSpecimen.parent`` points back at its own
    model. The walk invokes the target type's hook (the same type), which
    re-enters the cascade while active - the path-rich cycle error raises
    instead of the old silent depth-1 break (which skipped the parent's OWN
    parent-edge constraint: a chain whose grandparent was hidden stayed
    visible).
    """
    node_type = _make_type(
        "SelfNodeType",
        ScalarSpecimen,
        get_queryset=lambda cls, qs, info: apply_cascade_permissions(
            cls,
            qs.exclude(label="hidden"),
            info,
        ),
    )
    finalize_django_types()

    with pytest.raises(ConfigurationError) as excinfo:
        apply_cascade_permissions(node_type, ScalarSpecimen.objects.all(), _INFO)
    assert "SelfNodeType.parent -> SelfNodeType" in str(excinfo.value)
    assert _cascade_state.get() is None


@pytest.mark.django_db
def test_self_referential_fields_scoping_breaks_recursion():
    """``fields=[]`` inside the self-hook is the documented cycle-breaking recourse.

    The hook narrows its own rows and cascades nothing further, so the root
    walk's single ``parent`` constraint applies the type's direct narrowing
    without re-entering - a row whose parent is hidden drops, and the walk
    terminates cleanly.
    """
    node_type = _make_type(
        "ScopedSelfNodeType",
        ScalarSpecimen,
        get_queryset=lambda cls, qs, info: apply_cascade_permissions(
            cls,
            qs.exclude(label="hidden"),
            info,
            fields=[],
        ),
    )
    finalize_django_types()

    hidden_parent = _specimen("hidden")
    visible_parent = _specimen("visible_parent")
    keeps = _specimen("keeps", parent=visible_parent)
    _specimen("drops", parent=hidden_parent)

    # NOTE the root call walks the ``parent`` edge (its ``fields=None``); only
    # the NESTED application inside the hook is scoped to nothing.
    result = apply_cascade_permissions(node_type, ScalarSpecimen.objects.all(), _INFO)
    names = set(result.values_list("label", flat=True))
    assert "drops" not in names
    assert keeps in result
    assert _cascade_state.get() is None


@pytest.mark.django_db
def test_isnull_disjunct_only_on_nullable_edges():
    """The ``__isnull=True`` disjunct composes for nullable edges ONLY.

    ``Entry.item`` / ``Entry.property`` are non-nullable: the composed SQL
    carries the bare membership tests with no vacuous ``IS NULL`` branch. The
    nullable twin
    ``test_library_inheritance_api.py::test_nullable_lead_ticket_cycle_cascades_one_way``
    pins the disjunct's row-level effect; this pins its absence.
    """
    _make_type(
        "NnItemType",
        Item,
        get_queryset=lambda cls, qs, info: qs.filter(is_private=False),
    )
    entry_type = _make_type("NnEntryType", Entry, primary=False)
    finalize_django_types()

    result = apply_cascade_permissions(entry_type, Entry.objects.all(), _INFO, fields=["item"])
    sql = str(result.query)
    assert "IN (SELECT" in sql
    assert "IS NULL" not in sql


def test_two_overlapping_threads_isolate_traversal_state():
    """Two concurrent walks (one failing) never observe each other's state.

    Each thread runs a root walk whose target hook parks on a shared barrier so
    the two walks provably overlap in real time; one hook then raises. Each
    thread's outcome is its own (one composed queryset, one propagated error)
    and ``_cascade_state`` is ``None`` in both threads afterward - the
    ``ContextVar`` gives each thread its own traversal state and the token
    resets fire independently.
    """
    import threading

    barrier = threading.Barrier(2, timeout=10)

    def _parking_hook(cls, qs, info):
        barrier.wait()  # both walks are provably in-flight together
        if getattr(info.context, "fail", False):
            raise RuntimeError("thread boom")
        return qs.exclude(name="hidden")

    _make_type("ThTargetType", _CtTarget, get_queryset=_parking_hook)
    parent_type = _make_type("ThParentType", _CtParent, primary=False)
    finalize_django_types()

    outcomes = {}

    def _run(label, fail):
        info = SimpleNamespace(context=SimpleNamespace(user=None, fail=fail))
        try:
            result = apply_cascade_permissions(parent_type, _CtParent.objects.all(), info)
            outcomes[label] = ("ok", "IN (SELECT" in str(result.query))
        except RuntimeError as exc:
            outcomes[label] = ("error", str(exc))
        finally:
            outcomes[f"{label}_state"] = _cascade_state.get()

    threads = [
        threading.Thread(target=_run, args=("succeeds", False)),
        threading.Thread(target=_run, args=("fails", True)),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)

    assert outcomes["succeeds"] == ("ok", True)
    assert outcomes["fails"] == ("error", "thread boom")
    # Both threads' contexts are clean - including the one that raised.
    assert outcomes["succeeds_state"] is None
    assert outcomes["fails_state"] is None


async def test_aapply_gather_restores_task_contexts():
    """Two gathered ``aapply`` calls compose independently and leak no state.

    ``run_in_one_sync_boundary`` is ``thread_sensitive=True``, so the two walks
    serialize on one worker thread - the pin here is task-context restoration
    (neither awaiting task observes traversal state afterward), not parallelism.
    """
    import asyncio

    from asgiref.sync import sync_to_async

    @sync_to_async
    def _setup():
        _make_type(
            "GatherItemType",
            Item,
            get_queryset=lambda cls, qs, info: qs.filter(is_private=False),
        )
        entry_type = _make_type("GatherEntryType", Entry, primary=False)
        finalize_django_types()
        return entry_type

    entry_type = await _setup()

    first, second = await asyncio.gather(
        aapply_cascade_permissions(entry_type, Entry.objects.all(), _INFO),
        aapply_cascade_permissions(entry_type, Entry.objects.all(), _INFO),
    )
    assert "IN (SELECT" in str(first.query)
    assert "IN (SELECT" in str(second.query)
    assert _cascade_state.get() is None


# =============================================================================
# Gate-composition pins (connection / node / list pins live in their
# own files). Per spec-034 Decision 11 / 12.
# =============================================================================


def _exclude_private(cls, qs, info):
    """The recurring cascading hook: row-narrow ``is_private=False`` then cascade.

    Re-declared locally, matching its sibling hooks above rather than sharing one
    cross-file fixture. The hook ignores ``info`` (it narrows unconditionally), so any
    context value drives it.
    """
    return apply_cascade_permissions(cls, qs.filter(is_private=False), info)


def _gate_info(*, is_staff):
    """``info``-shaped stub carrying ``info.context.request`` with a ``user``.

    The gate resolves the request through ``utils/permissions.py::request_from_info``
    (``info.context.request``); ``check_name_permission`` keys on ``user.is_staff``.
    Mirrors ``tests/filters/test_sets.py::_make_info`` /
    ``tests/orders/test_sets.py::_make_info``.
    """
    request = HttpRequest()
    request.user = SimpleNamespace(is_staff=is_staff)
    return SimpleNamespace(context=SimpleNamespace(request=request))


class _StaffOnlyCategoryFilter(FilterSet):
    """Local mirror of products ``CategoryFilter.check_name_permission`` (staff-only)."""

    class Meta:
        model = Category
        fields = {"name": ["exact"]}

    def check_name_permission(self, request):
        user = getattr(request, "user", None)
        if not user or not user.is_staff:
            raise GraphQLError("You must be a staff user to filter by Category name.")


class _StaffOnlyCategoryOrder(OrderSet):
    """Local mirror of products ``CategoryOrder.check_name_permission`` (staff-only).

    ``_normalize_input`` is overridden to emit the flat ``[(path, direction)]`` shape
    directly (the ``tests/orders/test_sets.py`` ``_NoneDirectionSyncOrder`` precedent)
    so the apply pipeline produces a deterministic ``order_by`` without standing up
    the ``OrderArgumentsFactory`` input class (whose module-global ``_field_specs`` /
    factory caches this file's autouse fixtures do not clear). The gate's
    active-input walk falls back to the python-attr token, so ``check_name_permission``
    still fires on a ``{"name": ...}`` input.
    """

    class Meta:
        model = Category
        fields = ["name"]

    def check_name_permission(self, request):
        user = getattr(request, "user", None)
        if not user or not user.is_staff:
            raise GraphQLError("You must be a staff user to order by Category name.")

    @classmethod
    def _normalize_input(cls, input_value):
        # Mirror the active-input dict to the flat ordering tuples.
        return list(input_value.items())


class _StaffOnlyItemFilter(FilterSet):
    """Staff-only ``name`` gate on ``Item`` - the no-existence-leak pin's input gate.

    Lets the gate-denial test run over an ``Item`` queryset the cascade genuinely
    narrows (through the non-null ``category`` edge), rather than the chain-top
    ``Category`` whose direct cascade is a no-op.
    """

    class Meta:
        model = Item
        fields = {"name": ["exact"]}

    def check_name_permission(self, request):
        user = getattr(request, "user", None)
        if not user or not user.is_staff:
            raise GraphQLError("You must be a staff user to filter by Item name.")


def _anonymous_narrowed_categories(type_name):
    """Return ``(type, narrowed qs)`` after the type's own anonymous ``get_queryset``."""
    category_type = _make_type(type_name, Category, get_queryset=_exclude_private)
    finalize_django_types()
    return category_type, category_type.get_queryset(Category.objects.all(), _INFO)


@pytest.mark.django_db
def test_cascade_then_filter_gate_denies_gated_input():
    """A gated-field filter is denied on input shape alone, after cascade narrowing.

    One HTTP request cannot split anonymous cascade narrowing from a staff gate
    walk; the consumer-visible denial is
    ``test_cascade_composes_with_filter_and_order_live``.
    """
    rows = services.seed_gate_name_split()
    _type, narrowed = _anonymous_narrowed_categories("FgDenyCategoryType")

    with pytest.raises(GraphQLError, match="staff user to filter by Category name"):
        _StaffOnlyCategoryFilter.apply_sync(
            {"name": rows["public"].name},
            narrowed,
            _gate_info(is_staff=False),
        )


@pytest.mark.django_db
def test_cascade_then_filter_operates_only_on_cascade_narrowed_rows():
    """Passing filter input cannot recover a row the anonymous cascade already dropped.

    Staff ``apply_sync`` over an anonymous-narrowed queryset is not one HTTP
    actor; the consumer-visible filter+order half is
    ``test_cascade_composes_with_filter_and_order_live``.
    """
    rows = services.seed_gate_name_split()
    public, hidden = rows["public"], rows["hidden"]
    _type, narrowed = _anonymous_narrowed_categories("FgKeepCategoryType")

    passed = _StaffOnlyCategoryFilter.apply_sync(
        {"name": hidden.name},
        narrowed,
        _gate_info(is_staff=True),
    )
    assert list(passed) == []
    kept = _StaffOnlyCategoryFilter.apply_sync(
        {"name": public.name},
        narrowed,
        _gate_info(is_staff=True),
    )
    assert list(kept) == [public]


@pytest.mark.django_db
def test_cascade_then_order_gate_denies_gated_input():
    """A gated-field order is denied on input shape alone, after cascade narrowing."""
    services.seed_gate_order_split()
    _type, narrowed = _anonymous_narrowed_categories("OgDenyCategoryType")

    with pytest.raises(GraphQLError, match="staff user to order by Category name"):
        _StaffOnlyCategoryOrder.apply_sync(
            {"name": Ordering.ASC},
            narrowed,
            _gate_info(is_staff=False),
        )


@pytest.mark.django_db
def test_cascade_then_order_arranges_only_cascade_narrowed_rows():
    """Passing order input arranges only rows the anonymous cascade left visible."""
    rows = services.seed_gate_order_split()
    alpha, beta = rows["alpha"], rows["beta"]
    _type, narrowed = _anonymous_narrowed_categories("OgKeepCategoryType")

    ordered = _StaffOnlyCategoryOrder.apply_sync(
        {"name": Ordering.ASC},
        narrowed,
        _gate_info(is_staff=True),
    )
    assert list(ordered) == [alpha, beta]


@pytest.mark.django_db
def test_gate_denial_no_existence_leak():
    """A gate denial fires on input shape alone - identical error with/without hidden rows.

    The no-existence-leak property (spec-034 Decision 11): a field denial and the
    cascade-hidden-row result are produced by independent layers, so the denial
    cannot reveal whether a hidden row exists. Two fixtures differing only in
    whether a hidden-target row exists must yield a byte-identical ``GraphQLError``
    (message and extensions). A live request mints a distinct correlation id per
    envelope, so that identity is not a wire shape; the consumer-visible denial
    is ``test_cascade_composes_with_filter_and_order_live``.

    The queryset under test is one the cascade GENUINELY narrows: ``ItemType``
    cascades through its non-null ``category`` edge to a ``CategoryType`` that hides
    private categories, so an ``Item`` under a private category is dropped by the
    cascade itself.
    """
    _make_type("LeakCategoryType", Category, get_queryset=_exclude_private)
    item_type = _make_type("LeakItemType", Item)
    finalize_django_types()

    # Fixture 1: an Item under the PRIVATE category exists -> the cascade drops it.
    rows = services.seed_gate_existence_split()
    private_cat = rows["private_cat"]
    visible = rows["visible_item"]

    with_hidden = apply_cascade_permissions(item_type, Item.objects.all(), _INFO)
    # Sanity: the cascade actually narrowed (the under-hidden Item is gone), so this
    # fixture genuinely differs from fixture 2 in row content - not just in name.
    assert sorted(with_hidden.values_list("name", flat=True)) == [visible.name]
    with pytest.raises(GraphQLError) as with_hidden_exc:
        _StaffOnlyItemFilter.apply_sync(
            {"name": visible.name},
            with_hidden,
            _gate_info(is_staff=False),
        )

    # Fixture 2: NO Item under a hidden category - delete the private chain entirely.
    Item.objects.filter(category=private_cat).delete()
    private_cat.delete()
    without_hidden = apply_cascade_permissions(item_type, Item.objects.all(), _INFO)
    assert sorted(without_hidden.values_list("name", flat=True)) == [visible.name]
    with pytest.raises(GraphQLError) as without_hidden_exc:
        _StaffOnlyItemFilter.apply_sync(
            {"name": visible.name},
            without_hidden,
            _gate_info(is_staff=False),
        )

    # Byte-identical denial: same message AND same extensions, hidden-present or not.
    assert str(with_hidden_exc.value) == str(without_hidden_exc.value)
    assert with_hidden_exc.value.extensions == without_hidden_exc.value.extensions
