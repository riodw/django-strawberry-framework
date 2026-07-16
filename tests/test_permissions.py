"""Cascade-permission tests - ``apply_cascade_permissions`` / ``aapply_cascade_permissions``.

Mirrors the flat ``django_strawberry_framework/permissions.py`` module per the
one-to-one test rule (Decision 3). Pins the hardened cascade contract:
fail-closed recursive graphs (mutual / self-referential / diamond / longer
cycles raise a path-rich ``ConfigurationError``; acyclic diamonds compose),
single-column concrete forward scope with MTI parent links INCLUDED and
``GenericForeignKey`` / composite forward relations preflighted closed,
identity-hook targets composed from their ``_default_manager`` (registered
proxy visibility), hook-return validation (queryset shape, concrete table,
slice / field-distinct / alias rejections) with target-column normalization
(``to_field`` / ``.values()`` / ``.values_list()``), root-alias pinning across
nested applications, nullable-only ``__isnull`` disjuncts, hidden-target
exclusion, transitive cascade, registry / secondary semantics, ``fields=``
scoping and validation, the sync-misuse contract, the async variant, and
thread / task traversal-state isolation.

Fixture mechanics
=================
Synthetic model graphs the fakeshop schema does not carry (A<->B cycle, MTI
parent-link, the all-relation-kinds scope model, a nullable FK, a self-referential
FK) are declared as ``managed = False`` models under the installed ``products``
app label and given real tables via ``connection.schema_editor()`` (the
``tests/test_relay_connection.py`` / ``tests/optimizer/test_relay_id_projection.py``
pattern); the app label must be an INSTALLED app so Django wires reverse relations
into ``_meta.get_fields()``. Tests that only inspect the COMPOSED query (scope,
MTI, identity-hook, multi-DB) need no table and assert on ``str(qs.query)`` /
``qs.db`` directly. The transitive 2-deep pin reuses the real products
``Entry -> Item -> Category`` chain with synthetic cascading ``DjangoType`` hooks.
The multi-DB pin is ``FAKESHOP_SHARDED``-gated (the ``shard_b`` alias only exists
under that env var) and does not run under a bare ``uv run pytest``.

Test-plan homes (spec-034 Test plan):
  * Slice 1 - the cascade foundation + its four upstream-invariant pins (THIS file).
  * Slice 2 - N+1 / cacheability pins owned here; optimizer-plan pins extend
    ``tests/optimizer/test_extension.py``.
  * Slice 3 - gate-composition pins owned here; connection / node / list pins
    extend ``tests/test_connection.py`` / ``test_relay_node_field.py`` /
    ``test_list_field.py``.
  * Slice 4 - live HTTP coverage extends ``examples/fakeshop/test_query/test_products_api.py``.
"""

# TODO(spec-036 Slice 3): add the package-level permission pin for mutation
# update/delete lookups.
# Pseudocode: declare a mutation target type whose get_queryset hides a real
# row through apply_cascade_permissions, run the mutation lookup helper against
# that row, and assert the resolver receives the same not-found FieldError shape
# as a genuinely missing id with no existence-leak branch.

import contextlib
import os
from types import SimpleNamespace

import pytest
import strawberry
from apps.products.models import Category, Entry, Item, Property
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import connection as db_connection
from django.db import models
from django.http import HttpRequest
from graphql import GraphQLError
from strategy_schemas import make_django_type

from django_strawberry_framework import (
    DjangoOptimizerExtension,
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
# Slice 1 - cascade foundation (per Decision 5 / 9 / 10), hardened: recursive
# graphs fail closed with a path-rich error; traversal state is immutable and
# token-reset on every root, edge, and nested application.
# =============================================================================


class _MutualA(models.Model):
    """A<->B mutual-cycle fixture (module level so both cycle tests share it)."""

    name = models.TextField()
    b = models.ForeignKey(
        "_MutualB",
        null=True,
        on_delete=models.CASCADE,
        related_name="a_set",
    )

    class Meta:
        app_label = "products"
        managed = False


class _MutualB(models.Model):
    name = models.TextField()
    a = models.ForeignKey(
        _MutualA,
        null=True,
        on_delete=models.CASCADE,
        related_name="b_set",
    )

    class Meta:
        app_label = "products"
        managed = False


def _cascading_hook(hidden_name):
    """Build the recurring cascade-and-hide hook narrowing ``name != hidden_name``."""
    return lambda cls, qs, info: apply_cascade_permissions(
        cls,
        qs.exclude(name=hidden_name),
        info,
    )


@pytest.mark.django_db(transaction=True)
def test_mutual_cycle_fails_closed_with_path():
    """A<->B mutual cascade raises the path-rich cycle error; state resets.

    The previous contract returned the re-entered queryset un-narrowed, which
    skipped the re-entered type's OUTGOING visibility edges: here, the ``B``
    subquery's ``a``-edge constraint would bind ``A`` rows WITHOUT ``A``'s own
    ``b``-edge cascade, so a ``B`` row whose ``a`` target itself points at a
    hidden ``B`` stayed visible through the nested walk - a leak shape. The
    hardened contract fails closed instead: re-entry into an active type raises
    ``ConfigurationError`` carrying the full edge path, and every token reset
    fires so the traversal state is clean after the raise.
    """
    with _tables(_MutualA, _MutualB):
        a_type = _make_type("CycleAType", _MutualA, get_queryset=_cascading_hook("hidden_a"))
        _make_type("CycleBType", _MutualB, get_queryset=_cascading_hook("hidden_b"))
        finalize_django_types()

        # The leak-shape data the old re-entry contract mis-served: ``leak_b``'s
        # ``a`` target points at a hidden ``B``, so ``A``'s own cascade would hide
        # ``chained_a`` - but the old nested re-entry skipped that edge.
        hidden_b = _MutualB.objects.create(name="hidden_b")
        chained_a = _MutualA.objects.create(name="chained_a", b=hidden_b)
        _MutualB.objects.create(name="leak_b", a=chained_a)
        _MutualA.objects.create(name="root_a")

        with pytest.raises(ConfigurationError) as excinfo:
            apply_cascade_permissions(a_type, _MutualA.objects.all(), _INFO)
        message = str(excinfo.value)
        # Path-rich: the full edge chain back to the re-entered type.
        assert "CycleAType.b -> CycleBType.a -> CycleAType" in message
        assert "fields=" in message  # the documented recourse
        # Deterministic: the same walk raises identically on a second root call.
        with pytest.raises(ConfigurationError, match="CycleAType.b -> CycleBType.a"):
            apply_cascade_permissions(a_type, _MutualA.objects.all(), _INFO)
        # Every token reset fired despite the raise.
        assert _cascade_state.get() is None


@pytest.mark.django_db(transaction=True)
def test_hook_exception_propagates_and_resets_state():
    """A target-hook exception propagates unchanged; every state token resets.

    The hook is reached during the root's walk (inside the edge frame), so the
    raise unwinds through the edge token AND the root token - both ``finally``
    resets must fire, leaving ``_cascade_state`` at ``None``.
    """
    with _tables(_MutualA, _MutualB):
        raiser_a = _make_type("RaiserAType", _MutualA)

        def _boom(cls, qs, info):
            raise RuntimeError("boom")

        _make_type("RaiserBType", _MutualB, get_queryset=_boom)
        finalize_django_types()

        with pytest.raises(RuntimeError, match="boom"):
            apply_cascade_permissions(raiser_a, _MutualA.objects.all(), _INFO)
        # The token resets cleared the traversal state despite the exception.
        assert _cascade_state.get() is None


def test_longer_cycle_renders_full_path():
    """A three-type A->B->C->A cycle raises with every hop in the path."""

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


def test_cyclic_diamond_fails_closed():
    """A diamond whose sink cascades back to the source raises on either branch."""

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

    Re-reaching the sink type through the second branch is NOT a cycle - the
    active tuple pops on frame exit (token reset), so only genuine in-flight
    re-entry raises. The sink's hook narrows both subquery chains.
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

    A model carrying an M2M, a reverse FK, a reverse O2O, a ``GenericForeignKey``,
    a ``GenericRelation``, and a forward FK + forward O2O: the cascadable set is
    exactly the single-column concrete forward relations (``fk`` / ``o2o`` /
    the GFK's backing ``content_type``), the reverse / M2M / ``GenericRelation``
    edges are outside parent-row cascade semantics (skippable), and the virtual
    ``GenericForeignKey`` itself is classified UNSUPPORTED - it can neither be
    composed as a one-column subquery nor safely skipped, so the walk
    preflights it closed (pinned by the two ``test_gfk_*`` tests below).
    """

    class ScopeTarget(models.Model):
        name = models.TextField()

        class Meta:
            app_label = "products"
            managed = False

    class ScopeOther(models.Model):
        name = models.TextField()

        class Meta:
            app_label = "products"
            managed = False

    class ScopeTag(models.Model):
        label = models.TextField()

        class Meta:
            app_label = "products"
            managed = False

    class ScopeModel(models.Model):
        # forward FK + forward O2O = the two cascadable edges
        fk = models.ForeignKey(ScopeTarget, on_delete=models.CASCADE, related_name="via_fk")
        o2o = models.OneToOneField(ScopeOther, on_delete=models.CASCADE, related_name="via_o2o")
        # M2M (join-table-backed, never a single-column cascade edge)
        m2m = models.ManyToManyField(ScopeTag, related_name="scope_models")
        # GenericForeignKey (``related_model`` absent) + its GenericRelation
        # (virtual, no ``column``) both live on this model so the walk's edge scan
        # sees and skips them.
        content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
        object_id = models.PositiveIntegerField()
        content_object = GenericForeignKey("content_type", "object_id")
        generics = GenericRelation("ScopeModel")

        class Meta:
            app_label = "products"
            managed = False

    # reverse FK: ScopeChild.parent -> ScopeModel (ScopeModel sees ``children``)
    class ScopeChild(models.Model):
        parent = models.ForeignKey(ScopeModel, on_delete=models.CASCADE, related_name="children")

        class Meta:
            app_label = "products"
            managed = False

    # reverse O2O: ScopeProfile.owner -> ScopeModel (ScopeModel sees ``profile``)
    class ScopeProfile(models.Model):
        owner = models.OneToOneField(ScopeModel, on_delete=models.CASCADE, related_name="profile")

        class Meta:
            app_label = "products"
            managed = False

    # The cascadable set is exactly the forward single-column concrete relations:
    # the explicit ``fk`` / ``o2o`` plus ``content_type`` (the GFK's *backing* FK
    # is itself an ordinary single-column forward FK and legitimately cascadable).
    # The M2M, reverse FK, reverse O2O, and GenericRelation all drop out as
    # skippable; the virtual ``content_object`` GFK is UNSUPPORTED (fail-closed).
    plan = _edge_plan(ScopeModel)
    assert _cascadable_edge_names(ScopeModel) == {"fk", "o2o", "content_type"}
    assert plan.unsupported == ("content_object",)

    # Each edge passes / fails the predicates for the documented reason.
    by_name = {f.name: f for f in ScopeModel._meta.get_fields()}
    assert _is_cascadable_edge(by_name["fk"]) is True
    assert _is_cascadable_edge(by_name["o2o"]) is True
    assert _is_cascadable_edge(by_name["content_type"]) is True  # backing FK, single column
    assert getattr(by_name["m2m"], "many_to_many", False) is True
    assert _is_cascadable_edge(by_name["m2m"]) is False  # M2M, join table
    assert _is_unsupported_forward_edge(by_name["m2m"]) is False  # ...and skippable
    assert _is_cascadable_edge(by_name["content_object"]) is False  # GFK, virtual
    assert _is_unsupported_forward_edge(by_name["content_object"]) is True  # fail-closed
    assert _is_cascadable_edge(by_name["generics"]) is False  # GenericRelation, one-to-many
    assert _is_unsupported_forward_edge(by_name["generics"]) is False
    assert _is_cascadable_edge(by_name["children"]) is False  # reverse FK
    assert _is_unsupported_forward_edge(by_name["children"]) is False
    assert _is_cascadable_edge(by_name["profile"]) is False  # reverse O2O
    assert _is_unsupported_forward_edge(by_name["profile"]) is False


class _GfkHost(models.Model):
    """GFK-carrying fixture shared by the preflight / explicit-selection pins."""

    target = models.ForeignKey(
        Category,
        null=True,
        on_delete=models.CASCADE,
        related_name="+",
    )
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    class Meta:
        app_label = "products"
        managed = False


def test_gfk_default_walk_preflights_closed():
    """A full walk (``fields=None``) over a GFK-carrying model fails before any hook.

    Silently skipping the GFK would leak rows pointing at hidden polymorphic
    targets; composing it is impossible (no single visibility policy). The
    preflight raises BEFORE any target hook runs - the registered target's hook
    observes zero invocations.
    """
    hook_calls = []

    def _counting_hook(cls, qs, info):
        hook_calls.append(cls)
        return qs

    _make_type("GfkCategoryType", Category, get_queryset=_counting_hook)
    host_type = _make_type("GfkHostType", _GfkHost, primary=False)
    finalize_django_types()

    with pytest.raises(ConfigurationError) as excinfo:
        apply_cascade_permissions(host_type, _GfkHost.objects.all(), _INFO)
    message = str(excinfo.value)
    assert "content_object" in message  # the offending edge is named
    assert "fields=" in message  # the recourse is named
    # Preflighted: no visibility hook ever ran.
    assert hook_calls == []


def test_gfk_explicit_selection_rejected_backing_fk_supported():
    """``fields=["content_object"]`` raises; ``fields=["content_type"]`` composes.

    The virtual GFK has no single-column cascade semantics even when selected
    explicitly. Its *backing* ``content_type`` FK is an ordinary edge: with a
    registered ``ContentType`` type it composes a real subquery, and
    ``object_id`` stays a scalar (never an edge).
    """
    _make_type(
        "GfkContentTypeType",
        ContentType,
        get_queryset=lambda cls, qs, info: qs.exclude(model="hiddenmodel"),
    )
    host_type = _make_type("GfkHostSelType", _GfkHost, primary=False)
    finalize_django_types()

    with pytest.raises(ConfigurationError) as excinfo:
        apply_cascade_permissions(
            host_type,
            _GfkHost.objects.all(),
            _INFO,
            fields=["content_object"],
        )
    assert "content_object" in str(excinfo.value)
    assert "no single-column cascade semantics" in str(excinfo.value)

    # The backing FK composes: an explicit supported subset bypasses the
    # preflight and narrows through the registered ContentType type's hook.
    result = apply_cascade_permissions(
        host_type,
        _GfkHost.objects.all(),
        _INFO,
        fields=["content_type"],
    )
    assert "IN (SELECT" in str(result.query)
    # ``object_id`` is a scalar, not an edge - selecting it is the ordinary
    # unknown-name error, not the unsupported-relation error.
    with pytest.raises(ConfigurationError, match="not cascadable"):
        apply_cascade_permissions(
            host_type,
            _GfkHost.objects.all(),
            _INFO,
            fields=["object_id"],
        )


# --- MTI parent links now cascade -------------------------------------------


def test_mti_parent_link_edge_included():
    """An MTI child's ``<parent>_ptr`` parent-link IS a cascadable edge.

    The parent link is a real single-column concrete forward OneToOne: a hidden
    MTI parent must hide its child rows, so the previous ``parent_link``
    exclusion (which left a hidden parent reachable through its child type) is
    gone. Classification-level pin; the row-level pins follow.
    """

    class MtiParent(models.Model):
        name = models.TextField()

        class Meta:
            app_label = "products"
            managed = False

    class MtiChild(MtiParent):
        extra = models.TextField()

        class Meta:
            app_label = "products"
            managed = False

    ptr = MtiChild._meta.get_field("mtiparent_ptr")
    assert ptr.related_model is MtiParent
    assert getattr(ptr.remote_field, "parent_link", False) is True
    assert _is_cascadable_edge(ptr) is True
    assert "mtiparent_ptr" in _cascadable_edge_names(MtiChild)


@pytest.mark.django_db(transaction=True)
def test_mti_single_level_parent_visibility_hides_child_rows():
    """A hidden MTI parent hides its child row through the ``<parent>_ptr`` cascade."""

    class MtiOrg(models.Model):
        name = models.TextField()

        class Meta:
            app_label = "products"
            managed = False

    class MtiShop(MtiOrg):
        city = models.TextField()

        class Meta:
            app_label = "products"
            managed = False

    with _tables(MtiOrg, MtiShop):
        _make_type(
            "MtiOrgType",
            MtiOrg,
            get_queryset=lambda cls, qs, info: qs.exclude(name="hidden_org"),
        )
        shop_type = _make_type("MtiShopType", MtiShop, primary=False)
        finalize_django_types()

        keeps = MtiShop.objects.create(name="ok_org", city="a")
        MtiShop.objects.create(name="hidden_org", city="b")

        result = apply_cascade_permissions(shop_type, MtiShop.objects.all(), _INFO)
        # The parent link is non-nullable, so no ``__isnull`` disjunct is added.
        assert "IS NULL" not in str(result.query)
        assert list(result) == [keeps]
        assert _cascade_state.get() is None


@pytest.mark.django_db(transaction=True)
def test_mti_multi_level_parent_links_cascade_transitively():
    """Grandchild -> child -> parent MTI chain narrows transitively via cascading hooks."""

    class MtiBase(models.Model):
        name = models.TextField()

        class Meta:
            app_label = "products"
            managed = False

    class MtiMiddle(MtiBase):
        tier = models.TextField()

        class Meta:
            app_label = "products"
            managed = False

    class MtiLeaf(MtiMiddle):
        leaf = models.TextField()

        class Meta:
            app_label = "products"
            managed = False

    with _tables(MtiBase, MtiMiddle, MtiLeaf):
        _make_type(
            "MtiBaseType",
            MtiBase,
            get_queryset=lambda cls, qs, info: qs.exclude(name="hidden_base"),
        )
        _make_type("MtiMiddleType", MtiMiddle, get_queryset=_cascade_only, primary=False)
        leaf_type = _make_type("MtiLeafType", MtiLeaf, primary=False)
        finalize_django_types()

        keeps = MtiLeaf.objects.create(name="ok", tier="t", leaf="l")
        MtiLeaf.objects.create(name="hidden_base", tier="t", leaf="l")

        # Leaf walk cascades ``mtimiddle_ptr`` -> MtiMiddleType, whose hook
        # cascades ``mtibase_ptr`` -> MtiBaseType (which hides the base row) -
        # the hidden base drops the leaf two parent links away.
        result = apply_cascade_permissions(leaf_type, MtiLeaf.objects.all(), _INFO)
        assert list(result) == [keeps]
        assert _cascade_state.get() is None


def test_mti_multiple_parent_links_both_cascade():
    """A child of TWO concrete MTI parents composes a subquery per parent link."""

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
    """A ``.using("shard_b")`` caller pins every cascade subquery to ``"shard_b"`` (Decision 8).

    Assert (via the composed subquery's ``.db``) that the cascade subquery binds to
    the caller's *resolved* alias - ``queryset.db``, the property that falls back to
    router resolution when no explicit ``.using`` was applied, not the private
    ``_db``. Built on the ``tests/optimizer/test_multi_db.py`` in-test alias pattern;
    ``FAKESHOP_SHARDED``-gated, so it does not run under a bare ``uv run pytest``.
    """

    class AliasTarget(models.Model):
        name = models.TextField()

        class Meta:
            app_label = "products"
            managed = False

    class AliasParent(models.Model):
        target = models.ForeignKey(AliasTarget, on_delete=models.CASCADE, related_name="parents")

        class Meta:
            app_label = "products"
            managed = False

    # Capture the alias the cascade actually hands the target hook. The walk builds
    # the RHS base as ``related_model._default_manager.using(queryset.db).all()``, so
    # the queryset the hook receives carries the load-bearing alias. Observing that
    # REAL RHS - rather than reconstructing a fresh ``.using(result.db)`` queryset in
    # the assertion, which would still pass against a broken default-alias build - is
    # what actually pins Decision 8 (feedback2 M1).
    received_dbs = []

    def _record_alias_hook(cls, qs, info):
        received_dbs.append(qs.db)
        return qs.exclude(name="hidden")

    target_type = _make_type("AliasTargetType", AliasTarget, get_queryset=_record_alias_hook)
    _make_type("AliasParentType", AliasParent, primary=False)
    finalize_django_types()

    # The caller resolved ``shard_b`` explicitly; the cascade subquery must inherit it.
    result = apply_cascade_permissions(
        registry.get(AliasParent),
        AliasParent.objects.using("shard_b").all(),
        _INFO,
    )
    assert result.db == "shard_b"
    assert target_type is registry.get(AliasTarget)
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


@pytest.mark.django_db(transaction=True)
def test_nullable_fk_rows_preserved():
    """``NULL``-FK rows survive a cascade that hides every target row.

    The ``| Q(fk__isnull=True)`` disjunct: a target hook that hides everything
    drops every non-null-FK row but keeps the null-FK rows. No error, no leak.
    """

    class NullTarget(models.Model):
        name = models.TextField()

        class Meta:
            app_label = "products"
            managed = False

    class NullParent(models.Model):
        name = models.TextField()
        target = models.ForeignKey(
            NullTarget,
            null=True,
            on_delete=models.CASCADE,
            related_name="parents",
        )

        class Meta:
            app_label = "products"
            managed = False

    with _tables(NullTarget, NullParent):
        # Target hook hides EVERYTHING.
        _make_type("NullTargetType", NullTarget, get_queryset=lambda cls, qs, info: qs.none())
        parent_type = _make_type("NullParentType", NullParent, primary=False)
        finalize_django_types()

        target = NullTarget.objects.create(name="t")
        NullParent.objects.create(name="has_fk", target=target)
        null_row = NullParent.objects.create(name="null_fk", target=None)

        result = apply_cascade_permissions(parent_type, NullParent.objects.all(), _INFO)
        names = sorted(result.values_list("name", flat=True))
        # The non-null-FK row drops (its target is hidden); the NULL-FK row survives.
        assert names == ["null_fk"]
        assert null_row in result


# --- the rest of the Slice 1 contract -----------------------------------------


@pytest.mark.django_db(transaction=True)
def test_cascade_excludes_rows_with_hidden_targets():
    """A parent row whose FK targets a hook-hidden row is excluded (Decision 6)."""

    class HideTarget(models.Model):
        name = models.TextField()

        class Meta:
            app_label = "products"
            managed = False

    class HideParent(models.Model):
        name = models.TextField()
        target = models.ForeignKey(HideTarget, on_delete=models.CASCADE, related_name="parents")

        class Meta:
            app_label = "products"
            managed = False

    with _tables(HideTarget, HideParent):
        _make_type(
            "HideTargetType",
            HideTarget,
            get_queryset=lambda cls, qs, info: qs.exclude(name="secret"),
        )
        parent_type = _make_type("HideParentType", HideParent, primary=False)
        finalize_django_types()

        visible = HideTarget.objects.create(name="public")
        secret = HideTarget.objects.create(name="secret")
        HideParent.objects.create(name="keeps", target=visible)
        HideParent.objects.create(name="drops", target=secret)

        result = apply_cascade_permissions(parent_type, HideParent.objects.all(), _INFO)
        assert sorted(result.values_list("name", flat=True)) == ["keeps"]


@pytest.mark.django_db(transaction=True)
def test_hidden_and_missing_targets_indistinguishable():
    """A hidden-target row and a missing-target row are equally absent (Decision 6)."""

    class IndistTarget(models.Model):
        name = models.TextField()

        class Meta:
            app_label = "products"
            managed = False

    class IndistParent(models.Model):
        name = models.TextField()
        # ``SET_NULL`` lets us produce a "missing target" row (deleted target -> NULL),
        # but we model "missing" as a never-set NULL FK to keep the two row classes
        # apart: a hidden-target row and a no-target row both fail to surface.
        target = models.ForeignKey(
            IndistTarget,
            null=True,
            on_delete=models.SET_NULL,
            related_name="parents",
        )

        class Meta:
            app_label = "products"
            managed = False

    with _tables(IndistTarget, IndistParent):
        _make_type(
            "IndistTargetType",
            IndistTarget,
            get_queryset=lambda cls, qs, info: qs.exclude(name="hidden"),
        )
        parent_type = _make_type("IndistParentType", IndistParent, primary=False)
        finalize_django_types()

        hidden = IndistTarget.objects.create(name="hidden")
        hidden_row = IndistParent.objects.create(name="points_at_hidden", target=hidden)

        result = apply_cascade_permissions(parent_type, IndistParent.objects.all(), _INFO)
        # The hidden-target row is absent. Now delete the target outright (the FK
        # was the only thing distinguishing it): the row that pointed at a hidden
        # target and a row that points at no target are equally just *gone* from
        # the result - no error, no field that says "you may not see this".
        assert hidden_row not in result
        assert result.filter(name="points_at_hidden").count() == 0


@pytest.mark.django_db
def test_transitive_cascade_two_deep():
    """``Entry -> Item -> Category`` narrows transitively when each hook cascades.

    Uses the real products ``Entry -> Item/Property -> Category`` chain with
    synthetic ``DjangoType`` hooks (the products schema hooks are not uncommented
    until Slice 4). Hiding a ``Category`` must drop the ``Entry`` rows under its
    ``Item`` (and ``Property``) two edges away - the transitive depth emerging from
    each target hook itself calling the helper.
    """

    def _exclude_private(cls, qs, info):
        return apply_cascade_permissions(cls, qs.filter(is_private=False), info)

    _make_type("TxCategoryType", Category, get_queryset=_exclude_private)
    _make_type("TxItemType", Item, get_queryset=_exclude_private)
    _make_type("TxPropertyType", Property, get_queryset=_exclude_private)
    entry_type = _make_type("TxEntryType", Entry, get_queryset=_exclude_private)
    finalize_django_types()

    public_cat = Category.objects.create(name="public_cat", is_private=False)
    private_cat = Category.objects.create(name="private_cat", is_private=True)
    public_item = Item.objects.create(name="pub_item", category=public_cat)
    hidden_item = Item.objects.create(name="hidden_item", category=private_cat)
    public_prop = Property.objects.create(name="pub_prop", category=public_cat)
    other_prop = Property.objects.create(name="other_prop", category=public_cat)

    keeps = Entry.objects.create(value="keeps", item=public_item, property=public_prop)
    # This entry's ITEM is under a private category two edges away -> drops.
    Entry.objects.create(value="drops_via_item", item=hidden_item, property=other_prop)

    result = apply_cascade_permissions(entry_type, Entry.objects.all(), _INFO)
    names = sorted(result.values_list("value", flat=True))
    assert names == ["keeps"]
    assert keeps in result


@pytest.mark.django_db(transaction=True)
def test_identity_hook_targets_compose_default_manager(django_assert_num_queries):
    """A registered identity-hook target STILL composes its ``_default_manager``.

    The previous ``has_custom_get_queryset() is False`` skip silently bypassed a
    registered type whose filtered ``_default_manager`` IS its visibility policy
    (the proxy shape pinned below). Every registered target now contributes a
    subquery - and the subqueries still compile into the caller's single
    ``SELECT``, so identity composition adds zero query round-trips.
    """
    _make_type("IdentItemType", Item)  # identity default - no get_queryset override
    _make_type("IdentPropertyType", Property)
    entry_type = _make_type("IdentEntryType", Entry, primary=False)
    finalize_django_types()

    assert registry.get(Item).has_custom_get_queryset() is False

    category = Category.objects.create(name="c")
    item = Item.objects.create(name="i", category=category)
    prop = Property.objects.create(name="p", category=category)
    entry = Entry.objects.create(value="v", item=item, property=prop)

    result = apply_cascade_permissions(entry_type, Entry.objects.all(), _INFO)
    # Both registered targets compose (Item and Property; Category's type is
    # unregistered here so the transitive edge contributes nothing).
    assert str(result.query).count("IN (SELECT") == 2
    # ...at zero added round-trips: one SELECT evaluates the whole shape, and the
    # identity subqueries (unfiltered default managers) preserve every row.
    with django_assert_num_queries(1):
        assert list(result) == [entry]


@pytest.mark.django_db(transaction=True)
def test_proxy_target_filtered_default_manager_composes():
    """A registered proxy type's filtered ``_default_manager`` narrows the cascade.

    The proxy declares no ``get_queryset`` override - its visibility policy lives
    entirely in the proxy's default manager. The old identity-hook skip bypassed
    it; the hardened walk seeds every edge subquery from the target's
    ``_default_manager``, so the proxy's filter is the subquery base.
    """

    class ProxTarget(models.Model):
        name = models.TextField()

        class Meta:
            app_label = "products"
            managed = False

    class _VisibleOnlyManager(models.Manager):
        def get_queryset(self):
            return super().get_queryset().exclude(name="manager_hidden")

    class ProxVisibleTarget(ProxTarget):
        objects = _VisibleOnlyManager()

        class Meta:
            app_label = "products"
            proxy = True
            managed = False

    class ProxParent(models.Model):
        name = models.TextField()
        target = models.ForeignKey(
            ProxVisibleTarget,
            on_delete=models.CASCADE,
            related_name="parents",
        )

        class Meta:
            app_label = "products"
            managed = False

    with _tables(ProxTarget, ProxParent):
        _make_type("ProxVisibleTargetType", ProxVisibleTarget)  # identity hook
        parent_type = _make_type("ProxParentType", ProxParent, primary=False)
        finalize_django_types()

        visible = ProxTarget.objects.create(name="ok")
        hidden = ProxTarget.objects.create(name="manager_hidden")
        keeps = ProxParent.objects.create(name="keeps", target_id=visible.pk)
        ProxParent.objects.create(name="drops", target_id=hidden.pk)

        result = apply_cascade_permissions(parent_type, ProxParent.objects.all(), _INFO)
        assert "IN (SELECT" in str(result.query)
        # The proxy manager's exclusion is live inside the subquery.
        assert sorted(result.values_list("name", flat=True)) == ["keeps"]
        assert keeps in result


@pytest.mark.django_db(transaction=True)
def test_proxy_hook_return_over_concrete_target_accepted():
    """A hook returning a proxy queryset for a concrete-target edge is compatible.

    Proxy and concrete siblings share one concrete table, so the subquery is
    sound; the validator keys on ``_meta.concrete_model``, not the class.
    """

    class PcTarget(models.Model):
        name = models.TextField()

        class Meta:
            app_label = "products"
            managed = False

    class PcTargetProxy(PcTarget):
        class Meta:
            app_label = "products"
            proxy = True
            managed = False

    class PcParent(models.Model):
        name = models.TextField()
        target = models.ForeignKey(PcTarget, on_delete=models.CASCADE, related_name="parents")

        class Meta:
            app_label = "products"
            managed = False

    with _tables(PcTarget, PcParent):
        # The concrete target's hook answers with a PROXY queryset.
        _make_type(
            "PcTargetType",
            PcTarget,
            get_queryset=lambda cls, qs, info: PcTargetProxy.objects.using(qs.db).exclude(
                name="hidden",
            ),
        )
        parent_type = _make_type("PcParentType", PcParent, primary=False)
        finalize_django_types()

        visible = PcTarget.objects.create(name="ok")
        hidden = PcTarget.objects.create(name="hidden")
        keeps = PcParent.objects.create(name="keeps", target=visible)
        PcParent.objects.create(name="drops", target=hidden)

        result = apply_cascade_permissions(parent_type, PcParent.objects.all(), _INFO)
        assert sorted(result.values_list("name", flat=True)) == ["keeps"]
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

    public_cat = Category.objects.create(name="c", is_private=False)
    Item.objects.create(name="i", category=public_cat)

    result = apply_cascade_permissions(item_type, Item.objects.all(), _INFO)
    # Resolved through the permissive primary (identity default manager): the
    # subquery composes, and the secondary's ``qs.none()`` never applies - the
    # row survives (a secondary-narrowed walk would return zero rows).
    assert "IN (SELECT" in str(result.query)
    assert result.count() == 1


def test_secondary_root_self_edge_reaches_primary_then_fails_closed():
    """A secondary-rooted self-edge resolves to the PRIMARY, whose recursion fails closed.

    The ``parent`` edge re-reaches the same model via ``registry.get`` -> the
    **primary** (a different class from the rooting secondary, so THAT step is
    not a cycle). The primary's own cascading hook then re-enters the primary on
    its self-edge - a genuine recursion - and the walk raises the path-rich
    cycle error instead of silently under-narrowing.
    """

    class SelfRef(models.Model):
        name = models.TextField()
        parent = models.ForeignKey(
            "self",
            null=True,
            on_delete=models.CASCADE,
            related_name="children",
        )

        class Meta:
            app_label = "products"
            managed = False

    _make_type(
        "SelfRefPrimaryType",
        SelfRef,
        get_queryset=lambda cls, qs, info: apply_cascade_permissions(
            cls,
            qs.exclude(name="primary_hidden"),
            info,
        ),
        primary=True,
    )
    secondary = _make_type(
        "SelfRefSecondaryType",
        SelfRef,
        get_queryset=lambda cls, qs, info: apply_cascade_permissions(
            cls,
            qs.exclude(name="secondary_hidden"),
            info,
        ),
        primary=False,
    )
    finalize_django_types()

    with pytest.raises(ConfigurationError) as excinfo:
        apply_cascade_permissions(secondary, SelfRef.objects.all(), _INFO)
    # The path shows the secondary root reaching the primary, then the primary
    # re-entering itself: secondary.parent -> primary.parent -> primary.
    assert "SelfRefSecondaryType.parent -> SelfRefPrimaryType.parent -> SelfRefPrimaryType" in str(
        excinfo.value,
    )
    assert _cascade_state.get() is None


class _CtTarget(models.Model):
    """Hook-return-contract fixture target (shared by the battery below)."""

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


@pytest.mark.django_db(transaction=True)
def test_hook_values_and_values_list_projections_are_normalized():
    """A hook's ``.values(...)`` / ``.values_list(...)`` return is re-projected safely.

    The subquery is normalized to ``field.target_field.attname``, so a consumer
    projection can no longer compare the FK against the wrong column (the old
    contract passed a ``.values("name")`` straight into ``__in`` - a silent
    wrong-column narrowing) and a multi-column ``.values()`` no longer raises at
    evaluation. Both shapes narrow by the hook's FILTER, not its projection.
    """
    with _tables(_CtTarget, _CtParent):
        parent_type = _register_ct_pair(
            lambda cls, qs, info: qs.exclude(name="hidden").values("id", "name"),
        )

        visible = _CtTarget.objects.create(name="t")
        hidden = _CtTarget.objects.create(name="hidden")
        keeps = _CtParent.objects.create(name="keeps", target=visible)
        _CtParent.objects.create(name="drops", target=hidden)

        result = apply_cascade_permissions(parent_type, _CtParent.objects.all(), _INFO)
        assert sorted(result.values_list("name", flat=True)) == ["keeps"]
        assert keeps in result

        # The ``.values_list("name")`` twin - the wrong-column shape - narrows
        # identically after normalization.
        registry.clear()
        parent_type = _register_ct_pair(
            lambda cls, qs, info: qs.exclude(name="hidden").values_list("name"),
        )
        result = apply_cascade_permissions(parent_type, _CtParent.objects.all(), _INFO)
        assert sorted(result.values_list("name", flat=True)) == ["keeps"]


@pytest.mark.django_db(transaction=True)
def test_to_field_edge_compares_target_column():
    """A ``ForeignKey(to_field=...)`` edge binds the ``to_field`` column, never the pk.

    The normalization projects ``field.target_field.attname`` (here ``code``), so
    even a hook that explicitly projected the pk narrows by the correct column.
    """

    class TfTarget(models.Model):
        code = models.TextField(unique=True)
        name = models.TextField()

        class Meta:
            app_label = "products"
            managed = False

    class TfParent(models.Model):
        name = models.TextField()
        target = models.ForeignKey(
            TfTarget,
            to_field="code",
            on_delete=models.CASCADE,
            related_name="parents",
        )

        class Meta:
            app_label = "products"
            managed = False

    with _tables(TfTarget, TfParent):
        # The hook projects the WRONG column (the pk); normalization overrides it.
        _make_type(
            "TfTargetType",
            TfTarget,
            get_queryset=lambda cls, qs, info: qs.exclude(name="hidden").values("id"),
        )
        parent_type = _make_type("TfParentType", TfParent, primary=False)
        finalize_django_types()

        visible = TfTarget.objects.create(code="ok", name="t")
        hidden = TfTarget.objects.create(code="hx", name="hidden")
        keeps = TfParent.objects.create(name="keeps", target=visible)
        TfParent.objects.create(name="drops", target=hidden)

        result = apply_cascade_permissions(parent_type, TfParent.objects.all(), _INFO)
        # The subquery selects the ``code`` column, not ``id``.
        assert '"code"' in str(result.query)
        assert sorted(result.values_list("name", flat=True)) == ["keeps"]
        assert keeps in result


def test_hook_return_rejections_fail_closed():
    """Non-queryset / wrong-table / sliced / distinct / combined / grouped / shadowed / re-aliased returns raise.

    Every shape that would compose a wrong or wrong-database membership predicate
    is a loud ``ConfigurationError`` at composition time - never a silent
    mis-narrowing or a backend-dependent evaluation error. Pure composition: the
    raise fires before any SQL, so no tables are needed. The combined / grouped /
    extra-shadow shapes are the ones where re-projecting to the target column
    would change SEMANTICS, not just the selected column: ``.values(...)`` on a
    union only rewrites the outer projection (each branch keeps its original
    column), on a grouped queryset it changes the GROUP BY (widening the visible
    set), and under a shadowing ``extra(select=...)`` alias it selects the
    raw-SQL expression instead of the model column.
    """
    rejects = [
        # A materialized list (built without evaluating - the raise must fire at
        # composition, not depend on table state).
        (lambda cls, qs, info: [], "must return a QuerySet"),
        (lambda cls, qs, info: _CtTarget.objects, "must return a QuerySet"),
        (lambda cls, qs, info: _CtOther.objects.using(qs.db).all(), "concrete table"),
        # An MTI child queryset lives on ITS OWN concrete table - incompatible.
        (lambda cls, qs, info: _CtTargetChild.objects.using(qs.db).all(), "concrete table"),
        (lambda cls, qs, info: qs[:5], "sliced"),
        (lambda cls, qs, info: qs.distinct("name"), "distinct"),
        # Combined querysets: composition-time rejection, so union/intersection/
        # difference all fail identically via ``query.combinator``.
        (lambda cls, qs, info: qs.union(qs), "combined"),
        (lambda cls, qs, info: qs.intersection(qs), "combined"),
        # A whole-table aggregate annotate sets ``group_by=True``...
        (lambda cls, qs, info: qs.annotate(n=models.Count("id")), "grouped"),
        # ...and a ``values().annotate()`` grouping sets it to a column tuple.
        (lambda cls, qs, info: qs.values("name").annotate(n=models.Count("id")), "grouped"),
        # An ``extra(select=...)`` alias shadowing the edge's target column would
        # make the re-projection select raw SQL, not the model column.
        (lambda cls, qs, info: qs.extra(select={"id": "name"}), "shadows"),
        # An ``annotate(...)`` alias shadowing the target column is the
        # security-critical twin: Django blocks a bare ``annotate(id=Value(pk))``
        # but permits ``values("name").annotate(id=Value(pk))``, which stays
        # ungrouped (``Value`` is no aggregate) and re-projects to the injected
        # constant. ``test_annotation_alias_shadow_cannot_bypass_visibility``
        # proves the real-row leak this rejection closes.
        (lambda cls, qs, info: qs.values("name").annotate(id=models.Value(1)), "shadows"),
        # ``.using(...)`` off the pinned alias - resolved lazily, so the string
        # comparison rejects it before any connection is attempted.
        (lambda cls, qs, info: qs.using("bogus_alias"), "alias"),
    ]
    for hook, match in rejects:
        registry.clear()
        parent_type = _register_ct_pair(hook)
        with pytest.raises(ConfigurationError, match=match):
            apply_cascade_permissions(parent_type, _CtParent.objects.all(), _INFO)
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


@pytest.mark.django_db(transaction=True)
def test_annotation_alias_shadow_to_field_cannot_bypass_visibility():
    """The ``to_field`` twin: annotating the ``to_field`` column to a constant is rejected.

    A ``ForeignKey(to_field="code")`` edge re-projects to ``code``; a hook doing
    ``values("name").annotate(code=Value(<hidden_code>))`` would smuggle the
    hidden row's ``code`` exactly as the pk case smuggles its ``id``.
    """

    class TfShadowTarget(models.Model):
        code = models.TextField(unique=True)
        name = models.TextField()

        class Meta:
            app_label = "products"
            managed = False

    class TfShadowParent(models.Model):
        name = models.TextField()
        target = models.ForeignKey(
            TfShadowTarget,
            to_field="code",
            on_delete=models.CASCADE,
            related_name="parents",
        )

        class Meta:
            app_label = "products"
            managed = False

    with _tables(TfShadowTarget, TfShadowParent):
        visible = TfShadowTarget.objects.create(code="ok", name="visible")
        hidden = TfShadowTarget.objects.create(code="hx", name="hidden")
        TfShadowParent.objects.create(name="keeps", target=visible)
        TfShadowParent.objects.create(name="attack", target=hidden)

        _make_type(
            "TfShadowTargetType",
            TfShadowTarget,
            get_queryset=lambda cls, qs, info: qs.values("name").annotate(
                code=models.Value(hidden.code),
            ),
        )
        parent_type = _make_type("TfShadowParentType", TfShadowParent, primary=False)
        finalize_django_types()

        with pytest.raises(ConfigurationError, match="'code'"):
            apply_cascade_permissions(parent_type, TfShadowParent.objects.all(), _INFO)
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


def test_root_queryset_shape_rejections():
    """The root call rejects non-querysets, wrong-model, sliced, and combined roots loudly.

    Sliced and combined roots cannot be ``.filter(...)``-narrowed; without the
    up-front rejection the walk would leak a raw ``TypeError`` /
    ``NotSupportedError`` from Django mid-composition instead of the
    fail-closed configuration error.
    """
    parent_type = _register_ct_pair(None)

    with pytest.raises(ConfigurationError, match="got Manager"):
        apply_cascade_permissions(parent_type, _CtParent.objects, _INFO)
    with pytest.raises(ConfigurationError, match="got list"):
        apply_cascade_permissions(parent_type, [], _INFO)
    with pytest.raises(ConfigurationError, match="concrete table"):
        apply_cascade_permissions(parent_type, _CtOther.objects.all(), _INFO)
    with pytest.raises(ConfigurationError, match="sliced"):
        apply_cascade_permissions(parent_type, _CtParent.objects.all()[:5], _INFO)
    with pytest.raises(ConfigurationError, match="combined"):
        apply_cascade_permissions(
            parent_type,
            _CtParent.objects.all().union(_CtParent.objects.all()),
            _INFO,
        )
    assert _cascade_state.get() is None


@pytest.mark.django_db
def test_fields_scopes_walk():
    """``fields=["item"]`` cascades only ``item`` and leaves ``property`` alone."""

    def _exclude_private(cls, qs, info):
        return qs.filter(is_private=False)

    _make_type("FsItemType", Item, get_queryset=_exclude_private)
    _make_type("FsPropertyType", Property, get_queryset=_exclude_private)
    entry_type = _make_type("FsEntryType", Entry, primary=False)
    finalize_django_types()

    public_cat = Category.objects.create(name="c")
    public_item = Item.objects.create(name="pub_item", category=public_cat)
    hidden_item = Item.objects.create(name="hidden_item", category=public_cat, is_private=True)
    public_prop = Property.objects.create(name="pub_prop", category=public_cat)
    hidden_prop = Property.objects.create(name="hidden_prop", category=public_cat, is_private=True)

    keeps = Entry.objects.create(value="keeps", item=public_item, property=public_prop)
    drops_item = Entry.objects.create(value="drops_item", item=hidden_item, property=public_prop)
    # This entry's property is hidden but its item is public; with ``fields=["item"]``
    # the property edge is NOT cascaded, so the row survives.
    survives_prop = Entry.objects.create(
        value="survives_prop",
        item=public_item,
        property=hidden_prop,
    )

    result = apply_cascade_permissions(entry_type, Entry.objects.all(), _INFO, fields=["item"])
    names = set(result.values_list("value", flat=True))
    assert names == {"keeps", "survives_prop"}
    assert keeps in result
    assert survives_prop in result
    assert drops_item not in result


def test_fields_unknown_name_raises():
    """An unknown ``fields=`` name raises ConfigurationError naming field/model/set (Decision 9)."""
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
    """A known-but-non-cascadable ``fields=`` name (M2M / reverse / scalar) raises (Decision 9)."""
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
    """``fields="item"`` (a bare string) raises before any name lookup (Decision 9, Revision 3).

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
    """``fields=1`` (a non-iterable) raises ConfigurationError, not a raw TypeError (feedback M2).

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
    """``fields=[["item"]]`` (unhashable entry) raises ConfigurationError, not a raw TypeError (feedback M2).

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
    """``fields=[1]`` raises a clear "must be field-name strings" error, not a confusing name diff (feedback M2).

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
    Decision 10. The unawaited coroutine is closed by ``apply_type_visibility_sync``
    before the raise, so no "coroutine was never awaited" ``RuntimeWarning`` fires -
    the suite's ``filterwarnings = error`` policy (pytest.ini) would turn any such
    warning into a hard error, so a leaked coroutine fails this test by construction.

    The message carries the *cascade-specific* recourse (feedback M1): make the
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
    """``aapply_cascade_permissions`` runs the sync walk via ``sync_to_async`` (Decision 10).

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


class _SelfNode(models.Model):
    """Self-referential FK fixture shared by the fail-closed / fields= pins."""

    name = models.TextField()
    parent = models.ForeignKey(
        "self",
        null=True,
        on_delete=models.CASCADE,
        related_name="children",
    )

    class Meta:
        app_label = "products"
        managed = False


def test_self_referential_cascading_hook_fails_closed():
    """A ``parent = FK('self')`` edge whose own hook cascades is a genuine recursion.

    The walk invokes the target type's hook (the same type), which re-enters the
    cascade while active - the path-rich cycle error raises instead of the old
    silent depth-1 break (which skipped the parent's OWN parent-edge constraint:
    a chain whose grandparent was hidden stayed visible).
    """
    node_type = _make_type(
        "SelfNodeType",
        _SelfNode,
        get_queryset=lambda cls, qs, info: apply_cascade_permissions(
            cls,
            qs.exclude(name="hidden"),
            info,
        ),
    )
    finalize_django_types()

    with pytest.raises(ConfigurationError) as excinfo:
        apply_cascade_permissions(node_type, _SelfNode.objects.all(), _INFO)
    assert "SelfNodeType.parent -> SelfNodeType" in str(excinfo.value)
    assert _cascade_state.get() is None


@pytest.mark.django_db(transaction=True)
def test_self_referential_fields_scoping_breaks_recursion():
    """``fields=[]`` inside the self-hook is the documented cycle-breaking recourse.

    The hook narrows its own rows and cascades nothing further, so the root
    walk's single ``parent`` constraint applies the type's direct narrowing
    without re-entering - a row whose parent is hidden drops, and the walk
    terminates cleanly.
    """
    with _tables(_SelfNode):
        node_type = _make_type(
            "ScopedSelfNodeType",
            _SelfNode,
            get_queryset=lambda cls, qs, info: apply_cascade_permissions(
                cls,
                qs.exclude(name="hidden"),
                info,
                fields=[],
            ),
        )
        finalize_django_types()

        hidden_parent = _SelfNode.objects.create(name="hidden")
        visible_parent = _SelfNode.objects.create(name="visible_parent")
        keeps = _SelfNode.objects.create(name="keeps", parent=visible_parent)
        _SelfNode.objects.create(name="drops", parent=hidden_parent)

        # NOTE the root call walks the ``parent`` edge (its ``fields=None``); only
        # the NESTED application inside the hook is scoped to nothing.
        result = apply_cascade_permissions(node_type, _SelfNode.objects.all(), _INFO)
        names = set(result.values_list("name", flat=True))
        assert "drops" not in names
        assert keeps in result
        assert _cascade_state.get() is None


@pytest.mark.django_db(transaction=True)
def test_nullable_chain_preserves_null_links_and_drops_hidden_tails():
    """A nullable two-edge chain keeps NULL links and drops hidden-tail rows.

    ``ChTop -> ChMid (nullable) -> ChTail``: the tail type hides a row, both
    upstream hooks cascade. A top row whose mid is NULL survives (the
    ``__isnull`` disjunct), a top row whose mid points at a hidden tail drops
    transitively, and a top row whose mid's tail is NULL survives (the nested
    disjunct).
    """

    class ChTail(models.Model):
        name = models.TextField()

        class Meta:
            app_label = "products"
            managed = False

    class ChMid(models.Model):
        name = models.TextField()
        tail = models.ForeignKey(
            ChTail,
            null=True,
            on_delete=models.CASCADE,
            related_name="mids",
        )

        class Meta:
            app_label = "products"
            managed = False

    class ChTop(models.Model):
        name = models.TextField()
        mid = models.ForeignKey(ChMid, null=True, on_delete=models.CASCADE, related_name="tops")

        class Meta:
            app_label = "products"
            managed = False

    with _tables(ChTail, ChMid, ChTop):
        _make_type(
            "ChTailType",
            ChTail,
            get_queryset=lambda cls, qs, info: qs.exclude(name="hidden_tail"),
        )
        _make_type("ChMidType", ChMid, get_queryset=_cascade_only)
        top_type = _make_type("ChTopType", ChTop, primary=False)
        finalize_django_types()

        hidden_tail = ChTail.objects.create(name="hidden_tail")
        ok_tail = ChTail.objects.create(name="ok_tail")
        mid_hidden = ChMid.objects.create(name="mid_hidden", tail=hidden_tail)
        mid_ok = ChMid.objects.create(name="mid_ok", tail=ok_tail)
        mid_null = ChMid.objects.create(name="mid_null", tail=None)

        ChTop.objects.create(name="drops_hidden_tail", mid=mid_hidden)
        ChTop.objects.create(name="keeps_ok_tail", mid=mid_ok)
        ChTop.objects.create(name="keeps_null_tail", mid=mid_null)
        ChTop.objects.create(name="keeps_null_mid", mid=None)

        result = apply_cascade_permissions(top_type, ChTop.objects.all(), _INFO)
        assert sorted(result.values_list("name", flat=True)) == [
            "keeps_null_mid",
            "keeps_null_tail",
            "keeps_ok_tail",
        ]


@pytest.mark.django_db
def test_isnull_disjunct_only_on_nullable_edges():
    """The ``__isnull=True`` disjunct composes for nullable edges ONLY.

    ``Entry.item`` / ``Entry.property`` are non-nullable: the composed SQL
    carries the bare membership tests with no vacuous ``IS NULL`` branch. The
    nullable twins (``test_nullable_fk_rows_preserved`` and the chain test
    above) pin the disjunct's row-level effect; this pins its absence.
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
# Slice 2 - N+1 audit (permissions-owned pins; optimizer-plan pins live in
# tests/optimizer/test_extension.py). Per Decision 7.
# =============================================================================


@pytest.mark.django_db(transaction=True)
def test_cascaded_traversal_adds_zero_queries(django_assert_num_queries):
    """A cascaded 2-deep shape executes in the same query count as its uncascaded twin.

    The ``__in`` subqueries compile into the caller's single ``SELECT`` (Decision 7),
    so a cascaded ``Entry -> Item/Property -> Category`` list evaluation costs the
    SAME one query as its identity-hook twin - the cascade adds zero round-trips.

    The pin is the LOAD-BEARING property (BUILD.md "Query-shape tests"): an
    ABSOLUTE count derived from a real run (both shapes == 1 query), not a bare
    ``cascaded == uncascaded`` equality (which a fallback that scaled both shapes
    identically would also satisfy). The ``"IN (SELECT"`` presence guard on the
    cascaded query is the right-path assertion: a silently-empty walk would also
    report one query, so the count is only meaningful with the subqueries proven
    present.
    """

    def _exclude_private(cls, qs, info):
        return apply_cascade_permissions(cls, qs.filter(is_private=False), info)

    # Cascaded shape: every target carries the cascading hook (reuse the
    # ``test_transitive_cascade_two_deep`` definitions).
    _make_type("ZqCategoryType", Category, get_queryset=_exclude_private)
    _make_type("ZqItemType", Item, get_queryset=_exclude_private)
    _make_type("ZqPropertyType", Property, get_queryset=_exclude_private)
    entry_type = _make_type("ZqEntryType", Entry, get_queryset=_exclude_private)
    finalize_django_types()

    public_cat = Category.objects.create(name="public_cat", is_private=False)
    private_cat = Category.objects.create(name="private_cat", is_private=True)
    public_item = Item.objects.create(name="pub_item", category=public_cat)
    hidden_item = Item.objects.create(name="hidden_item", category=private_cat)
    public_prop = Property.objects.create(name="pub_prop", category=public_cat)
    other_prop = Property.objects.create(name="other_prop", category=public_cat)
    keeps = Entry.objects.create(value="keeps", item=public_item, property=public_prop)
    # This entry's item is under a private category two edges away -> drops.
    Entry.objects.create(value="drops_via_item", item=hidden_item, property=other_prop)

    cascaded_qs = apply_cascade_permissions(entry_type, Entry.objects.all(), _INFO)
    # Right-path guard: the cascade actually composed the nested subqueries (a
    # silently-empty walk would also evaluate in one query but carry no subquery).
    assert "IN (SELECT" in str(cascaded_qs.query)

    # Absolute count: the cascaded list evaluation executes in ONE query - the
    # ``__in`` subqueries are nested SELECTs inside the single outer SELECT.
    with django_assert_num_queries(1):
        cascaded_rows = list(cascaded_qs)
    # And the narrowing is real: the private-category entry dropped, the public one stayed.
    assert cascaded_rows == [keeps]

    # Uncascaded twin: the identical chain with identity-hook targets (no
    # ``get_queryset``), evaluated over the SAME seeded rows.
    registry.clear()
    _make_type("UqCategoryType", Category)
    _make_type("UqItemType", Item)
    _make_type("UqPropertyType", Property)
    _make_type("UqEntryType", Entry)
    finalize_django_types()

    with django_assert_num_queries(1):
        uncascaded_rows = list(Entry.objects.all())
    assert len(uncascaded_rows) == 2  # both entries are visible without the cascade

    # The cascaded shape costs the same one query as its uncascaded twin: zero
    # added round-trips (Decision 7), distinguishing subquery composition from a
    # would-be per-FK extra query.


@pytest.mark.django_db
def test_fk_id_elision_falls_back_for_cascading_target():
    """A cascading target never FK-id-elides - re-affirms the shipped safety rule.

    FK-id elision (``category { id }`` round-tripping the source FK column without
    a JOIN) is disabled whenever the target hook must run
    (``walker.py::_plan_select_relation`` gates on
    ``not _target_has_custom_get_queryset(target_type)``). A cascading hook is a
    custom hook, so the relation falls back to a ``Prefetch`` instead of eliding -
    the inverse of ``test_optimizer_elides_forward_fk_id_only_selection_plan_shape``.
    This re-affirms the shipped safety rule against the new cascade hook shape
    (Decision 12 / Edge case "FK-id elision interaction").
    """
    from django.db.models import Prefetch

    def _exclude_private(cls, qs, info):
        return apply_cascade_permissions(cls, qs.filter(is_private=False), info)

    category_type = _make_type(
        "ElCategoryType",
        Category,
        get_queryset=_exclude_private,
        fields=("id", "name"),
    )
    item_type = _make_type("ElItemType", Item, fields=("id", "name", "category"))

    @strawberry.type
    class Query:
        @strawberry.field
        def all_items(self) -> list[item_type]:  # type: ignore[valid-type]
            return Item.objects.all()

    finalize_django_types()
    ext = DjangoOptimizerExtension()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    ctx = SimpleNamespace(user=None)

    # ``category { id }`` is the id-only selection that WOULD elide for a plain FK.
    result = schema.execute_sync("{ allItems { name category { id } } }", context_value=ctx)
    assert result.errors is None
    plan = ctx.dst_optimizer_plan
    # No elision: the cascading target forces a ``Prefetch`` fallback instead.
    assert plan.fk_id_elisions == ()
    assert plan.select_related == ()
    assert len(plan.prefetch_related) == 1
    assert isinstance(plan.prefetch_related[0], Prefetch)
    assert plan.prefetch_related[0].prefetch_to == "category"
    assert category_type.has_custom_get_queryset() is True


@pytest.mark.django_db
def test_strictness_raise_silent_across_cascaded_shape():
    """The cascade composes SQL (never lazy-loads), so strictness ``"raise"`` stays silent.

    A cascaded 2-deep ``Entry -> Item -> Category`` traversal under
    ``DjangoOptimizerExtension(strictness="raise")`` plans fully (each cascading
    target downgrades to a ``Prefetch`` baked with the request ``info``) and never
    lazy-loads, so the N+1 sentinel never trips: ``result.errors is None`` (Edge
    case "Strictness interaction"). The query is kept minimal so it can only take
    the planned downgraded-Prefetch path it claims to test (BUILD.md right-path).
    """

    def _exclude_private(cls, qs, info):
        return apply_cascade_permissions(cls, qs.filter(is_private=False), info)

    _make_type("SrCategoryType", Category, get_queryset=_exclude_private, fields=("id", "name"))
    _make_type(
        "SrItemType",
        Item,
        get_queryset=_exclude_private,
        fields=("id", "name", "category"),
    )
    item_type = registry.get(Item)

    @strawberry.type
    class Query:
        @strawberry.field
        def all_items(self) -> list[item_type]:  # type: ignore[valid-type]
            return Item.objects.all()

    finalize_django_types()

    public_cat = Category.objects.create(name="public_cat", is_private=False)
    Item.objects.create(name="pub_item", category=public_cat)

    ext = DjangoOptimizerExtension(strictness="raise")
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    # A ``"raise"`` trip would surface a GraphQL error; the cascaded shape stays silent.
    result = schema.execute_sync(
        "{ allItems { name category { name } } }",
        context_value=SimpleNamespace(user=None),
    )
    assert result.errors is None


# =============================================================================
# Slice 3 - gate-composition pins (connection / node / list pins live in their
# own files). Per Decision 11 / 12.
# =============================================================================


def _exclude_private(cls, qs, info):
    """The recurring cascading hook: row-narrow ``is_private=False`` then cascade.

    Re-declared locally per the Slice-1/2 sibling pattern (a shared cross-file
    fixture is the integration pass's call, not this slice's - see the artifact's
    DRY analysis). The hook ignores ``info`` (it narrows unconditionally), so any
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
    ``Category`` whose direct cascade is a no-op (feedback2 M2).
    """

    class Meta:
        model = Item
        fields = {"name": ["exact"]}

    def check_name_permission(self, request):
        user = getattr(request, "user", None)
        if not user or not user.is_staff:
            raise GraphQLError("You must be a staff user to filter by Item name.")


@pytest.mark.django_db
def test_cascade_then_filter_gate_composition():
    """Cascade narrows rows first, ``FilterSet.check_<field>_permission`` judges input second.

    Pin BOTH shapes (card DoD): a gated-field input is denied regardless of cascade
    state; passing input operates only on cascade-narrowed rows. (Decision 11.)

    Composition is observed at its consequence (the plan's accepted lighter shape):
    the cascade lives in ``get_queryset`` (here ``_exclude_private``) and runs at the
    visibility step; the gate fires from ``FilterSet.apply_sync`` over the
    already-narrowed queryset. So a denial is independent of which rows the cascade
    left, and a passing filter can only ever match cascade-visible rows.
    """
    category_type = _make_type("FgCategoryType", Category, get_queryset=_exclude_private)
    finalize_django_types()

    public = Category.objects.create(name="public", is_private=False)
    Category.objects.create(name="hidden", is_private=True)

    # The cascade narrows first: the type's ``get_queryset`` hook runs at the
    # visibility step, so ``_exclude_private``'s ``is_private=False`` row-narrow
    # drops the private row before the gate judges input. (Calling
    # ``apply_cascade_permissions`` directly here would be a no-op - ``Category`` is
    # the chain top with no cascadable forward FK, and the cascade does not invoke
    # the type's own hook; the narrowing genuinely lives in ``get_queryset``.)
    narrowed = category_type.get_queryset(Category.objects.all(), _INFO)

    # Shape (a): a gated-field (``name``) input is DENIED on input shape alone -
    # regardless of cascade state. The gate raises before any row math.
    with pytest.raises(GraphQLError, match="staff user to filter by Category name"):
        _StaffOnlyCategoryFilter.apply_sync(
            {"name": "public"},
            narrowed,
            _gate_info(is_staff=False),
        )

    # Shape (b): with passing input (staff user), the filter operates only on the
    # cascade-narrowed rows - the hidden private row is unreachable through the
    # filter even though its name matches the lookup space.
    passed = _StaffOnlyCategoryFilter.apply_sync(
        {"name": "hidden"},
        narrowed,
        _gate_info(is_staff=True),
    )
    assert list(passed) == []  # the hidden row was already cascade-dropped
    kept = _StaffOnlyCategoryFilter.apply_sync(
        {"name": "public"},
        narrowed,
        _gate_info(is_staff=True),
    )
    assert list(kept) == [public]


@pytest.mark.django_db
def test_cascade_then_order_gate_composition():
    """Same composition matrix for ``OrderSet`` ``check_<field>_permission`` gates (Decision 11)."""
    category_type = _make_type("OgCategoryType", Category, get_queryset=_exclude_private)
    finalize_django_types()

    beta = Category.objects.create(name="beta", is_private=False)
    alpha = Category.objects.create(name="alpha", is_private=False)
    Category.objects.create(name="hidden", is_private=True)

    # Cascade narrows first via the type's ``get_queryset`` hook (drops the private
    # row); the gate then arranges only those cascade-visible rows.
    narrowed = category_type.get_queryset(Category.objects.all(), _INFO)

    # Shape (a): ``orderBy`` naming the gated field is DENIED on input shape alone.
    with pytest.raises(GraphQLError, match="staff user to order by Category name"):
        _StaffOnlyCategoryOrder.apply_sync(
            {"name": Ordering.ASC},
            narrowed,
            _gate_info(is_staff=False),
        )

    # Shape (b): with passing input (staff user), the order arranges only the
    # cascade-narrowed rows - the hidden private row never appears in the result.
    ordered = _StaffOnlyCategoryOrder.apply_sync(
        {"name": Ordering.ASC},
        narrowed,
        _gate_info(is_staff=True),
    )
    assert list(ordered) == [alpha, beta]


@pytest.mark.django_db
def test_gate_denial_no_existence_leak():
    """A gate denial fires on input shape alone - identical error with/without hidden rows.

    The no-existence-leak property (Decision 11): a field denial and the
    cascade-hidden-row result are produced by independent layers, so the denial
    cannot reveal whether a hidden row exists. Two fixtures differing only in
    whether a hidden-target row exists must yield a byte-identical ``GraphQLError``.

    The queryset under test is one the cascade GENUINELY narrows: ``ItemType``
    cascades through its non-null ``category`` edge to a ``CategoryType`` that hides
    private categories, so an ``Item`` under a private category is dropped by the
    cascade itself. (The earlier shape cascaded over ``Category`` - the chain top,
    whose direct cascade is a no-op - so the denial assertion passed without any
    narrowing ever happening; feedback2 M2.)
    """
    _make_type("LeakCategoryType", Category, get_queryset=_exclude_private)
    item_type = _make_type("LeakItemType", Item)
    finalize_django_types()

    public_cat = Category.objects.create(name="public_cat", is_private=False)
    private_cat = Category.objects.create(name="private_cat", is_private=True)

    # Fixture 1: an Item under the PRIVATE category exists -> the cascade drops it.
    Item.objects.create(name="pub", category=public_cat, is_private=False)
    Item.objects.create(name="under_hidden", category=private_cat, is_private=False)
    with_hidden = apply_cascade_permissions(item_type, Item.objects.all(), _INFO)
    # Sanity: the cascade actually narrowed (the under-hidden Item is gone), so this
    # fixture genuinely differs from fixture 2 in row content - not just in name.
    assert sorted(with_hidden.values_list("name", flat=True)) == ["pub"]
    with pytest.raises(GraphQLError) as with_hidden_exc:
        _StaffOnlyItemFilter.apply_sync(
            {"name": "pub"},
            with_hidden,
            _gate_info(is_staff=False),
        )

    # Fixture 2: NO Item under a hidden category - delete the private chain entirely.
    Item.objects.filter(category=private_cat).delete()
    private_cat.delete()
    without_hidden = apply_cascade_permissions(item_type, Item.objects.all(), _INFO)
    assert sorted(without_hidden.values_list("name", flat=True)) == ["pub"]
    with pytest.raises(GraphQLError) as without_hidden_exc:
        _StaffOnlyItemFilter.apply_sync(
            {"name": "pub"},
            without_hidden,
            _gate_info(is_staff=False),
        )

    # Byte-identical denial: same message AND same extensions, hidden-present or not.
    assert str(with_hidden_exc.value) == str(without_hidden_exc.value)
    assert with_hidden_exc.value.extensions == without_hidden_exc.value.extensions


@pytest.mark.django_db
def test_nested_relation_traversal_respects_target_cascade():
    """A nested relation's target hook cascades via the ``Prefetch`` downgrade (Decision 12).

    The connection-DoD's "every edge's nested relations" half at the traversal-result
    level. The transitivity is exercised over a **to-many** nested relation
    (``Category -> items``) whose target ``ItemType`` cascades (``_exclude_private``):
    the optimizer downgrades the relation to a ``Prefetch`` baked with the live
    ``info``, so each category's nested ``items`` LIST drops the target's hidden rows -
    a hidden item does not surface through the nested traversal. (A forward
    *non-nullable* FK to a hidden target is a different shape: there the PARENT row
    drops via its own cascade rather than the FK nulling - a non-null FK cannot
    resolve to ``null``. The to-many list is the clean traversal-narrowing shape and
    matches the DoD's "nested relations" wording.)

    Complementary to Slice 2's plan-level downgrade pin (plan shape + child SQL carries
    the request user); this asserts the narrowed nested ROWS. The query selects exactly
    the nested relation so it can only take the planned-Prefetch path (BUILD.md
    right-path).
    """
    _make_type("NtItemType", Item, get_queryset=_exclude_private, fields=("id", "name"))
    category_type = _make_type("NtCategoryType", Category, fields=("id", "name", "items"))

    @strawberry.type
    class Query:
        @strawberry.field
        def all_categories(self) -> list[category_type]:  # type: ignore[valid-type]
            return Category.objects.order_by("pk")

    finalize_django_types()

    public_cat = Category.objects.create(name="public_cat", is_private=False)
    Item.objects.create(name="visible_item", category=public_cat, is_private=False)
    Item.objects.create(name="hidden_item", category=public_cat, is_private=True)

    ext = DjangoOptimizerExtension()
    schema = strawberry.Schema(query=Query, extensions=[lambda: ext])
    result = schema.execute_sync(
        "{ allCategories { name items { name } } }",
        context_value=SimpleNamespace(user=None),
    )
    assert result.errors is None
    # The category's nested ``items`` list narrows to the target's visible rows; the
    # hidden item never surfaces through the traversal.
    assert result.data["allCategories"] == [
        {"name": "public_cat", "items": [{"name": "visible_item"}]},
    ]
