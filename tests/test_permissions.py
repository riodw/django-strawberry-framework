"""Cascade-permission tests — ``apply_cascade_permissions`` / ``aapply_cascade_permissions``.

STAGED SEAM (spec-034). Mirrors the flat ``django_strawberry_framework/permissions.py``
module per the one-to-one test rule (Decision 3). Every test below is a
``@pytest.mark.skip`` stub naming the slice and the contract it will pin — the
file collects cleanly and shows the whole permissions test plan as pending. Fill
each in and drop its skip in the owning slice.

Test-plan homes (spec-034 Test plan):
  * Slice 1 — the cascade foundation + its four upstream-invariant pins (THIS file).
  * Slice 2 — N+1 / cacheability pins owned here; optimizer-plan pins extend
    ``tests/optimizer/test_extension.py``.
  * Slice 3 — gate-composition pins owned here; connection / node / list pins
    extend ``tests/test_connection.py`` / ``test_relay_node_field.py`` /
    ``test_list_field.py``.
  * Slice 4 — live HTTP coverage extends ``examples/fakeshop/test_query/test_products_api.py``.
"""

import pytest

# The symbols exist (permissions.py is shipped as a NotImplementedError seam); the
# package-root re-export lands in Slice 1 (Decision 4). Import from the module path
# so this file collects today and the import itself proves permissions.py is clean.
from django_strawberry_framework.permissions import (  # noqa: F401
    SyncMisuseError,
    aapply_cascade_permissions,
    apply_cascade_permissions,
)

# =============================================================================
# Slice 1 — cascade foundation (per Decision 5 / 9 / 10)
# The four dedicated upstream-invariant pins first (card DoD item 3).
# =============================================================================


@pytest.mark.skip(reason="TODO(spec-034 Slice 1): cycle-guard invariant pin")
def test_cycle_guard_contextvar_breaks_mutual_cascade():
    """A↔B mutual cascade terminates; both directions apply direct narrowing.

    Build ``AType``/``BType`` whose hooks each cascade into the other. Assert the
    result is finite (no recursion error), each applies the other's *direct*
    narrowing, and ``_cascade_seen.get() is None`` after the root call returns —
    AND after a root call that raises (the ``finally`` reset). (Decision 5 step 5.)
    """


@pytest.mark.skip(reason="TODO(spec-034 Slice 1): single-column scope invariant pin")
def test_single_column_scope_skips_m2m_reverse_and_generic():
    """Only single-column forward FK / OneToOne edges cascade (Decision 5 step 1).

    A model carrying an M2M, a reverse FK, a reverse O2O, a ``GenericForeignKey``,
    a ``GenericRelation``, and a forward FK + forward O2O: assert ``_cascade_edges``
    returns exactly the two forward single-column relations (the others lack a
    ``column`` / ``related_model`` and are excluded by construction).
    """


@pytest.mark.skip(reason="TODO(spec-034 Slice 1): multi-DB alias-pinning invariant pin")
def test_multi_db_subquery_pinned_to_caller_alias():
    """A ``.using("other")`` caller pins every cascade subquery to ``"other"`` (Decision 8).

    Assert (via captured SQL / ``queryset.db``) that the composed ``__in`` subquery
    binds to the caller's resolved alias, not a router-independent route; a
    router-divergent model pair stays single-DB.
    """


@pytest.mark.skip(reason="TODO(spec-034 Slice 1): nullable-FK preservation invariant pin")
def test_nullable_fk_rows_preserved():
    """``NULL``-FK rows survive a cascade that hides every target row.

    The ``| Q(fk__isnull=True)`` disjunct: a target hook that hides everything
    drops every non-null-FK row but keeps the null-FK rows. No error, no leak.
    """


# --- the rest of the Slice 1 contract -----------------------------------------


@pytest.mark.skip(reason="TODO(spec-034 Slice 1): hidden-target row exclusion")
def test_cascade_excludes_rows_with_hidden_targets():
    """A parent row whose FK targets a hook-hidden row is excluded (Decision 6)."""


@pytest.mark.skip(reason="TODO(spec-034 Slice 1): no existence leak")
def test_hidden_and_missing_targets_indistinguishable():
    """A hidden-target row and a missing-target row are equally absent (Decision 6)."""


@pytest.mark.skip(reason="TODO(spec-034 Slice 1): transitive cascade")
def test_transitive_cascade_two_deep():
    """``Entry → Item → Category`` narrows transitively when each hook cascades."""


@pytest.mark.skip(reason="TODO(spec-034 Slice 1): identity-hook gate emits no SQL")
def test_identity_hook_targets_skipped_no_sql():
    """A target with no custom hook contributes no ``__in`` subquery (SQL assertion).

    The ``has_custom_get_queryset() is False`` gate (Decision 5 step 3) — the
    deviation from upstream's unconditional call that avoids dead ``__in`` SQL.
    """


@pytest.mark.skip(reason="TODO(spec-034 Slice 1): unregistered target skipped")
def test_unregistered_target_model_skipped():
    """An edge whose target model has no registered ``DjangoType`` is skipped."""


@pytest.mark.skip(reason="TODO(spec-034 Slice 1): secondary types never cascade targets")
def test_secondary_type_never_cascade_target():
    """``registry.get`` returns the primary; a stricter secondary hook never cascades."""


@pytest.mark.skip(reason="TODO(spec-034 Slice 1): fields= scopes the walk")
def test_fields_scopes_walk():
    """``fields=["item"]`` cascades only ``item`` and leaves ``property`` alone."""


@pytest.mark.skip(reason="TODO(spec-034 Slice 1): fields= unknown name raises")
def test_fields_unknown_name_raises():
    """An unknown ``fields=`` name raises ConfigurationError naming field/model/set (Decision 9)."""


@pytest.mark.skip(reason="TODO(spec-034 Slice 1): fields= non-cascadable name raises")
def test_fields_non_cascadable_name_raises():
    """A known-but-non-cascadable ``fields=`` name (M2M / reverse / scalar) raises (Decision 9)."""


@pytest.mark.skip(reason="TODO(spec-034 Slice 1): fields= valid-but-hookless name accepted")
def test_fields_valid_but_hookless_name_accepted():
    """A cascadable edge whose target lacks a registered type / custom hook is accepted+skipped."""


@pytest.mark.skip(reason="TODO(spec-034 Slice 1): fields= bare string rejected up front")
def test_fields_bare_string_raises():
    """``fields="item"`` (a bare string) raises before any name lookup (Decision 9, Revision 3).

    Without the ``isinstance(fields, str)`` guard the walk would validate ``'i'``,
    ``'t'``, ``'e'``, ``'m'`` as field names and surface a misleading "'i' is not
    cascadable" — the guard names the non-string-iterable requirement instead.
    """


@pytest.mark.skip(reason="TODO(spec-034 Slice 1): sync helper rejects async target hook")
def test_sync_helper_raises_syncmisuseerror_on_async_target_hook():
    """A target ``async def get_queryset`` reached from the sync walk raises SyncMisuseError.

    Coroutine closed first (no ``RuntimeWarning``); message names the target type
    and the two recourses (``aapply_cascade_permissions`` / sync rewrite). Decision 10.
    """


@pytest.mark.skip(reason="TODO(spec-034 Slice 1): async variant runs off the event loop")
def test_aapply_runs_walk_off_event_loop():
    """``aapply_cascade_permissions`` runs the sync walk via ``sync_to_async`` (Decision 10).

    Assert the walk executes off the event-loop thread and the ``ContextVar``
    seen-set is clean inside the worker (asgiref copy_context) and does not leak
    back into the awaiting task.
    """


@pytest.mark.skip(reason="TODO(spec-034 Slice 1): async variant still raises on async hook")
def test_aapply_async_target_hook_still_raises():
    """An ``async def`` target hook raises SyncMisuseError from the async variant too (Decision 10)."""


@pytest.mark.skip(reason="TODO(spec-034 Slice 1): self-referential FK cascades once")
def test_self_referential_fk_cascades_once():
    """A ``parent = FK('self')`` edge applies the target's direct narrowing once.

    The seen-set breaks the self-recursion at depth 1: the constraint still applies
    (parent must be visible by the type's own narrowing) but the nested cascade
    call returns un-narrowed rather than recursing forever (Edge cases).
    """


# =============================================================================
# Slice 2 — N+1 audit (permissions-owned pins; optimizer-plan pins live in
# tests/optimizer/test_extension.py). Per Decision 7.
# =============================================================================


@pytest.mark.skip(reason="TODO(spec-034 Slice 2): cascade adds zero round-trips")
def test_cascaded_traversal_adds_zero_queries():
    """A cascaded 2-deep shape executes in the same query count as its uncascaded twin.

    The ``__in`` subqueries compile into the caller's single ``SELECT`` (Decision 7);
    use ``django_assert_num_queries`` to pin the count equal across the two shapes.
    """


@pytest.mark.skip(reason="TODO(spec-034 Slice 2): FK-id elision falls back for cascading target")
def test_fk_id_elision_falls_back_for_cascading_target():
    """A cascading target never FK-id-elides — re-affirms the shipped safety rule."""


@pytest.mark.skip(reason="TODO(spec-034 Slice 2): strictness raise stays silent across cascade")
def test_strictness_raise_silent_across_cascaded_shape():
    """The cascade composes SQL (never lazy-loads), so strictness ``"raise"`` stays silent."""


# =============================================================================
# Slice 3 — gate-composition pins (connection / node / list pins live in their
# own files). Per Decision 11 / 12.
# =============================================================================


@pytest.mark.skip(reason="TODO(spec-034 Slice 3): cascade-then-filter-gate composition")
def test_cascade_then_filter_gate_composition():
    """Cascade narrows rows first, ``FilterSet.check_<field>_permission`` judges input second.

    Pin BOTH shapes (card DoD): a gated-field input is denied regardless of cascade
    state; passing input operates only on cascade-narrowed rows. (Decision 11.)
    """


@pytest.mark.skip(reason="TODO(spec-034 Slice 3): cascade-then-order-gate composition")
def test_cascade_then_order_gate_composition():
    """Same composition matrix for ``OrderSet`` ``check_<field>_permission`` gates (Decision 11)."""


@pytest.mark.skip(reason="TODO(spec-034 Slice 3): gate denial leaks no existence")
def test_gate_denial_no_existence_leak():
    """A gate denial fires on input shape alone — identical error with/without hidden rows."""


@pytest.mark.skip(
    reason="TODO(spec-034 Slice 3): nested relation traversal respects target cascade",
)
def test_nested_relation_traversal_respects_target_cascade():
    """A nested relation's target hook cascades via the ``Prefetch`` downgrade (Decision 12)."""
