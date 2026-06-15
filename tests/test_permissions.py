"""Cascade-permission tests - ``apply_cascade_permissions`` / ``aapply_cascade_permissions``.

Mirrors the flat ``django_strawberry_framework/permissions.py`` module per the
one-to-one test rule (Decision 3). Slice 1 pins the cascade foundation: the four
dedicated upstream-invariant pins (cycle guard, single-column scope, multi-DB
alias pinning, nullable-FK preservation) plus the rest of the Slice-1 contract
(hidden-target exclusion, transitive cascade, identity-hook skip, registry /
secondary semantics, the cascade-target return contract, ``fields=`` scoping and
validation, the sync-misuse contract, the async variant, and the self-referential
FK edge).

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

from django_strawberry_framework import (
    DjangoOptimizerExtension,
    DjangoType,
    finalize_django_types,
)
from django_strawberry_framework.exceptions import ConfigurationError
from django_strawberry_framework.filters import FilterSet
from django_strawberry_framework.orders import Ordering, OrderSet
from django_strawberry_framework.permissions import (
    SyncMisuseError,
    _cascadable_edge_names,
    _cascade_seen,
    _is_cascadable_edge,
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
    """The cycle-guard var must be reset to ``None`` after every test.

    A test that leaves ``_cascade_seen`` set would leak a stale seen-set into the
    next test sharing the context - the same request-isolation property the root
    ``finally`` reset guarantees in production. Pinning it here makes a leak a hard
    failure rather than a spooky-action-at-a-distance flake.
    """
    yield
    assert _cascade_seen.get() is None


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
    default (an identity-hook target the cascade skips). The default ``fields=("id",)``
    keeps the *selected* surface scalar-only so finalization never has to resolve a
    relation field to a (possibly-unregistered) target type - the cascade walks the
    model's ``_meta.get_fields()`` edges regardless of what the type exposes (the
    "Meta.fields-excluded FK edges still cascade" edge case).
    """
    namespace = {"Meta": type("Meta", (), {"model": model, "fields": fields, "primary": primary})}
    if get_queryset is not None:
        namespace["get_queryset"] = classmethod(get_queryset)
    return type(name, (DjangoType,), namespace)


# =============================================================================
# Slice 1 - cascade foundation (per Decision 5 / 9 / 10)
# The four dedicated upstream-invariant pins first (card DoD item 3).
# =============================================================================


@pytest.mark.django_db(transaction=True)
def test_cycle_guard_contextvar_breaks_mutual_cascade():
    """A<->B mutual cascade terminates; both directions apply direct narrowing.

    Build ``AType``/``BType`` whose hooks each cascade into the other. Assert the
    result is finite (no recursion error), each applies the other's *direct*
    narrowing, and ``_cascade_seen.get() is None`` after the root call returns -
    AND after a root call that raises (the ``finally`` reset). (Decision 5 step 5.)
    """

    class CycleA(models.Model):
        name = models.TextField()
        b = models.ForeignKey("CycleB", null=True, on_delete=models.CASCADE, related_name="a_set")

        class Meta:
            app_label = "products"
            managed = False

    class CycleB(models.Model):
        name = models.TextField()
        a = models.ForeignKey(CycleA, null=True, on_delete=models.CASCADE, related_name="b_set")

        class Meta:
            app_label = "products"
            managed = False

    with _tables(CycleA, CycleB):
        a_type = _make_type(
            "CycleAType",
            CycleA,
            get_queryset=lambda cls, qs, info: apply_cascade_permissions(
                cls,
                qs.exclude(name="hidden_a"),
                info,
            ),
        )
        b_type = _make_type(
            "CycleBType",
            CycleB,
            get_queryset=lambda cls, qs, info: apply_cascade_permissions(
                cls,
                qs.exclude(name="hidden_b"),
                info,
            ),
        )
        finalize_django_types()

        visible_b = CycleB.objects.create(name="ok_b")
        hidden_b = CycleB.objects.create(name="hidden_b")
        # A row pointing at a visible B survives; one pointing at a hidden B drops.
        keeps = CycleA.objects.create(name="keeps", b=visible_b)
        CycleA.objects.create(name="drops", b=hidden_b)

        # The root call from A cascades into B (BType hides ``hidden_b``); BType's
        # hook cascades back into A, and the seen-set breaks the A->B->A loop
        # without recursing forever. The walk terminates and applies B's direct
        # narrowing to A's rows.
        result = apply_cascade_permissions(a_type, CycleA.objects.all(), _INFO)
        names = sorted(result.values_list("name", flat=True))
        assert names == ["keeps"]
        assert keeps in result

        # Re-entry guard: the var is reset to ``None`` after the root returns.
        assert _cascade_seen.get() is None

    # ...AND after a root call whose *walk body* raises - the ``finally`` reset
    # fires even on exception. A target hook (reached during the root's walk, so
    # it runs inside the ``try``) raises; the root's ``finally`` must still clear
    # the seen-set. Re-using the A<->B tables: BType's hook raises, AType roots.
    # Clear the registry so the fresh primary registrations below don't collide
    # with CycleAType / CycleBType from the first block.
    registry.clear()
    with _tables(CycleA, CycleB):
        raiser_a = _make_type("RaiserAType", CycleA)

        def _boom(cls, qs, info):
            raise RuntimeError("boom")

        _make_type("RaiserBType", CycleB, get_queryset=_boom)
        finalize_django_types()

        with pytest.raises(RuntimeError, match="boom"):
            apply_cascade_permissions(raiser_a, CycleA.objects.all(), _INFO)
        # The ``finally`` cleared the seen-set despite the exception.
        assert _cascade_seen.get() is None


def test_single_column_scope_skips_m2m_reverse_and_generic():
    """Only single-column forward FK / OneToOne edges cascade (Decision 5 step 1).

    A model carrying an M2M, a reverse FK, a reverse O2O, a ``GenericForeignKey``,
    a ``GenericRelation``, and a forward FK + forward O2O: assert
    ``_cascadable_edge_names`` returns exactly the two forward single-column
    relations (these others lack a ``column`` / ``related_model`` or are marked
    many-to-many and excluded *by construction*). The one edge that passes the
    relation / single-column predicates yet must still be excluded - the MTI
    ``<parent>_ptr`` parent-link, dropped by the explicit ``parent_link`` guard,
    *not* by construction - is pinned separately by
    ``test_mti_parent_link_edge_excluded``.
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

    # The cascadable set is exactly the forward single-column relations: the
    # explicit ``fk`` / ``o2o`` plus ``content_type`` (the GFK's *backing* FK is
    # itself an ordinary single-column forward FK and legitimately cascadable - it
    # is the virtual ``content_object`` GFK and the ``generics`` reverse relation
    # that are excluded). The M2M, reverse FK, reverse O2O, GFK, and GenericRelation
    # all drop out.
    names = _cascadable_edge_names(ScopeModel)
    assert names == {"fk", "o2o", "content_type"}

    # Each edge passes / fails the single predicate for the documented reason.
    by_name = {f.name: f for f in ScopeModel._meta.get_fields()}
    assert _is_cascadable_edge(by_name["fk"]) is True
    assert _is_cascadable_edge(by_name["o2o"]) is True
    assert _is_cascadable_edge(by_name["content_type"]) is True  # backing FK, single column
    assert getattr(by_name["m2m"], "many_to_many", False) is True
    assert _is_cascadable_edge(by_name["m2m"]) is False  # M2M, join table
    assert _is_cascadable_edge(by_name["content_object"]) is False  # GFK, ``related_model`` absent
    assert _is_cascadable_edge(by_name["generics"]) is False  # GenericRelation, virtual
    assert _is_cascadable_edge(by_name["children"]) is False  # reverse FK, no ``column``
    assert _is_cascadable_edge(by_name["profile"]) is False  # reverse O2O, no ``column``


def test_mti_parent_link_edge_excluded():
    """An MTI child's ``<parent>_ptr`` parent-link is not walked (Decision 5 step 1).

    A multi-table-inheritance child's auto-generated ``<parent>_ptr``
    ``OneToOneField(parent_link=True)`` carries both a ``related_model`` and a
    ``column``, so it passes the two-predicate scope test - but the
    ``not getattr(field.remote_field, "parent_link", False)`` guard drops it, so a
    child row is *not* silently narrowed by its MTI-parent type's hook. Synthetic
    MTI graph (no fakeshop model uses MTI); pins H1 against the scope pseudo-code.
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
    # The parent link DOES carry both predicates the upstream test keys on...
    assert ptr.related_model is MtiParent
    assert hasattr(ptr, "column")
    assert getattr(ptr.remote_field, "parent_link", False) is True
    # ...yet the ``parent_link`` guard excludes it.
    assert _is_cascadable_edge(ptr) is False
    assert "mtiparent_ptr" not in _cascadable_edge_names(MtiChild)


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
    # The cascade composed a constraint (an ``__in`` subquery)...
    assert "IN (SELECT" in str(result.query)
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


@pytest.mark.django_db
def test_identity_hook_targets_skipped_no_sql():
    """A target with no custom hook contributes no ``__in`` subquery (SQL assertion).

    The ``has_custom_get_queryset() is False`` gate (Decision 5 step 3) - the
    deviation from upstream's unconditional call that avoids dead ``__in`` SQL.
    """
    # ItemType has the IDENTITY default hook; EntryType cascades. The Entry->Item
    # edge resolves to an identity target, so no ``IN (SELECT ...)`` clause for it.
    _make_type("IdentItemType", Item)  # identity default - no get_queryset override
    _make_type("IdentPropertyType", Property)
    entry_type = _make_type("IdentEntryType", Entry, primary=False)
    finalize_django_types()

    assert registry.get(Item).has_custom_get_queryset() is False

    result = apply_cascade_permissions(entry_type, Entry.objects.all(), _INFO)
    # No edge had a custom hook, so the queryset is composed with zero subqueries.
    assert "IN (SELECT" not in str(result.query)
    assert str(result.query) == str(Entry.objects.all().query)


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
    # PRIMARY, so the stricter secondary hook does NOT narrow.
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
    # Resolved through the permissive primary (identity) -> no narrowing, no subquery.
    assert "IN (SELECT" not in str(result.query)
    assert result.count() == 1


@pytest.mark.django_db(transaction=True)
def test_secondary_type_as_root_reaches_primary_on_transitive_revisit():
    """A cascade rooted on a *secondary* type re-reaches its model via the primary.

    Declare ``get_queryset`` (and the cascade) on a *secondary* type so it is the
    walk root; when the transitive walk re-reaches that same model through another
    edge it resolves via ``registry.get`` -> the **primary**, so the re-reach narrows
    by the primary's hook, not the rooting secondary's. The seen-set keys on the
    class object (``secondary != primary``), so the walk still terminates (Edge cases).
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

    with _tables(SelfRef):
        # PRIMARY hides ``primary_hidden``; SECONDARY (the root) hides ``secondary_hidden``.
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

        root = SelfRef.objects.create(name="root")
        primary_hidden = SelfRef.objects.create(name="primary_hidden")
        # ``root`` points at a parent the PRIMARY hides -> ``root`` drops on the
        # transitive re-visit (resolved via the primary, not the rooting secondary).
        root.parent = primary_hidden
        root.save()

        # Rooting on the SECONDARY: the ``parent`` edge re-reaches SelfRef and
        # resolves via ``registry.get`` -> the PRIMARY. The walk terminates
        # (secondary != primary in the seen-set) and narrows by the primary hook.
        result = apply_cascade_permissions(secondary, SelfRef.objects.all(), _INFO)
        names = set(result.values_list("name", flat=True))
        # ``root`` is excluded (its parent is primary-hidden); ``primary_hidden``
        # itself has no parent, so it survives the secondary root's own narrowing
        # (the secondary only hides ``secondary_hidden``, of which there are none).
        assert "root" not in names
        assert _cascade_seen.get() is None


@pytest.mark.django_db(transaction=True)
def test_cascade_target_sliced_or_values_queryset_is_consumer_bug():
    """A cascade target must return an unsliced, non-``.values()`` model-row queryset.

    The helper composes each target hook's return as the RHS of ``Q(<fk>__in=...)``,
    so a ``.values("col")`` return mis-narrows (compares the FK against the wrong
    column, no error) and a multi-column ``.values()`` raises ``ValueError`` ("the
    'in' lookup must have 1 selected field"); a sliced return is a MySQL-only hard
    error and a silent mis-narrowing elsewhere. The cascade does not defensively
    rewrite the hook's return - a non-row queryset is a consumer bug (Edge cases).
    """

    class CtTarget(models.Model):
        name = models.TextField()

        class Meta:
            app_label = "products"
            managed = False

    class CtParent(models.Model):
        target = models.ForeignKey(CtTarget, on_delete=models.CASCADE, related_name="parents")

        class Meta:
            app_label = "products"
            managed = False

    with _tables(CtTarget, CtParent):
        # A multi-column ``.values()`` return is the load-bearing pin: the ``__in``
        # subquery must have exactly one selected column, so Django raises when the
        # caller's queryset is evaluated.
        _make_type(
            "CtTargetType",
            CtTarget,
            get_queryset=lambda cls, qs, info: qs.values("id", "name"),
        )
        parent_type = _make_type("CtParentType", CtParent, primary=False)
        finalize_django_types()

        target = CtTarget.objects.create(name="t")
        CtParent.objects.create(target=target)

        # The cascade composes the multi-column ``.values()`` return straight into
        # ``Q(<fk>__in=...)`` with no defensive rewrite, so Django's ``In`` lookup
        # rejects it - the message is
        # "The QuerySet value for the 'in' lookup must have 1 selected fields
        # (received 2)". The raise fires while the ``.filter(Q(...))`` lookup is
        # built (or at evaluation, depending on Django internals), so wrap both the
        # composition and the materialization to be agnostic about which.
        with pytest.raises(ValueError, match=r"'in' lookup must have 1 selected fields"):
            result = apply_cascade_permissions(parent_type, CtParent.objects.all(), _INFO)
            list(result)


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
def test_fields_valid_but_hookless_name_accepted():
    """A cascadable edge whose target lacks a registered type / custom hook is accepted+skipped."""
    # ``item`` is cascadable, but ItemType has the identity hook -> validates clean,
    # contributes nothing (no raise, no subquery). Consistent with ``fields=None``.
    _make_type("HooklessItemType", Item)  # identity default
    entry_type = _make_type("HooklessEntryType", Entry, primary=False)
    finalize_django_types()

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
    ``_cascade_seen.get()`` stays ``None`` in the async caller after the await.
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
    assert _cascade_seen.get() is None
    result = await aapply_cascade_permissions(entry_type, Entry.objects.all(), _INFO)
    # The walk composed a constraint (the cascade ran off the loop)...
    assert "IN (SELECT" in str(result.query)
    # ...and the worker-thread seen-set did NOT leak back into the awaiting task.
    assert _cascade_seen.get() is None


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
    assert _cascade_seen.get() is None


@pytest.mark.django_db(transaction=True)
def test_self_referential_fk_cascades_once():
    """A ``parent = FK('self')`` edge applies the target's direct narrowing once.

    The seen-set breaks the self-recursion at depth 1: the constraint still applies
    (parent must be visible by the type's own narrowing) but the nested cascade
    call returns un-narrowed rather than recursing forever (Edge cases).
    """

    class Node(models.Model):
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

    with _tables(Node):
        node_type = _make_type(
            "SelfNodeType",
            Node,
            get_queryset=lambda cls, qs, info: apply_cascade_permissions(
                cls,
                qs.exclude(name="hidden"),
                info,
            ),
        )
        finalize_django_types()

        hidden_parent = Node.objects.create(name="hidden")
        visible_parent = Node.objects.create(name="visible_parent")
        keeps = Node.objects.create(name="keeps", parent=visible_parent)
        Node.objects.create(name="drops", parent=hidden_parent)

        # The walk terminates (seen-set breaks the self-edge at depth 1) and applies
        # the type's own direct narrowing to the ``parent`` edge: a row whose parent
        # is hidden drops; a row whose parent is visible survives.
        result = apply_cascade_permissions(node_type, Node.objects.all(), _INFO)
        names = set(result.values_list("name", flat=True))
        assert "drops" not in names
        assert keeps in result
        assert _cascade_seen.get() is None


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
