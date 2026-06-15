# Review: `django_strawberry_framework/permissions.py`

Status: verified

## DRY analysis

- None — the module already routes its one data-leak-sensitive operation (running a target's sync `get_queryset` and rejecting an async hook) through the single canonical helper `utils/querysets.py::apply_type_visibility_sync` (`permissions.py:225`), and the "cascadable edge" predicate is defined exactly once in `_is_cascadable_edge` and consumed by both `_cascadable_edge_names` (the `fields=` validator) and `_walk` (`permissions.py:111`, `permissions.py:215`), so scope cannot drift between the validator and the walk. The async twin is a `sync_to_async` wrap of the single sync walk (`permissions.py:249`), so there is no second walk implementation to keep in parity. The `Q(...__in=...) | Q(...__isnull=True)` composition appears once. No near-copy or repeated literal exists to hoist.

## High:

None.

## Medium:

None.

## Low:

### `field.remote_field` is a bare attribute access while the two preceding predicates use guarded `getattr`

In `_is_cascadable_edge` the first two predicates read `getattr(field, "related_model", None)` and `getattr(field, "column", None)`, but the third reads `field.remote_field.parent_link` via `getattr(field.remote_field, "parent_link", False)` — the outer `field.remote_field` is unguarded.

```django_strawberry_framework/permissions.py:102:106
    return (
        getattr(field, "related_model", None) is not None
        and getattr(field, "column", None) is not None
        and not getattr(field.remote_field, "parent_link", False)
    )
```

This is correct today and not a latent crash: Python's `and` short-circuits, so `field.remote_field` is only evaluated once a field has both a non-`None` `related_model` and a non-`None` single-column `column` — i.e. a concrete forward `ForeignKey`/`OneToOneField`, which always carries a `remote_field` (`ForeignObjectRel`). The asymmetry (two defensive `getattr`s then one bare attribute access) is purely stylistic and arguably *correct* asymmetry: by the third clause the field's shape is already pinned, so a defensive `getattr(field, "remote_field", None)` would add a guard for a state that the first two predicates have already excluded. Defer unless a future Django release ever attaches a `column` to a field type that lacks `remote_field` (none exists today); at that point the bare access would surface as the right loud failure rather than a silent mis-scope, so leaving it unguarded is defensible even then. No action recommended now; recorded only so the next reviewer does not re-flag the asymmetry as an oversight.

## What looks solid

### DRY recap

- **Existing patterns reused.** The per-edge target-hook probe delegates to `utils/querysets.py::apply_type_visibility_sync` (`permissions.py:225`), keeping the package's ONE sync-misuse site (the coroutine-close + `SyncMisuseError` raise) — a visibility-routing mistake is a data-leak class, so it is correctly not re-decided here. `SyncMisuseError` is re-exported in the established `types/relay.py` redundant-alias form (`permissions.py:57`) and adds no new public name (already in the root `__all__` via `types`). The target type is resolved through `registry.get` (`permissions.py:219`), reusing the registry's `Meta.primary` semantics rather than re-deriving primary selection. The async twin reuses the `filters/sets.py` `sync_to_async(thread_sensitive=True)` precedent (`permissions.py:249`).
- **New helpers considered.** A shared cross-test cascading-hook fixture was considered for the test file but is correctly deferred to the integration pass (the per-slice `_exclude_private` re-declaration mirrors the sibling test-file pattern; noted in the test module's own docstring). No new production helper is warranted: the cascadable-edge predicate is already a single named function.
- **Duplication risk in the current file.** The `Q(f"{field.name}__in")` / `Q(f"{field.name}__isnull")` pair (`permissions.py:227`) is a single composition site, not a near-copy. The two `model._meta.get_fields()` walks (`permissions.py:111` in `_cascadable_edge_names`, `permissions.py:214` in `_walk`) are intentionally distinct: one collects names for validation, the other composes constraints and applies the `names_to_walk` / `registry` / `has_custom_get_queryset` gates — folding them would couple validation to composition and is correctly left apart.

### Other positives

- **Cycle guard is correct and request-scoped.** `_cascade_seen` is a `ContextVar` (not a module global), so isolation holds under both WSGI and ASGI, and the asgiref `copy_context()` into the `sync_to_async` worker thread means the async path's install/reset never leaks back into the event-loop task. The root call installs a fresh set and resets it in a `finally` (`permissions.py:187-191`) so a handler exception cannot leak a stale seen-set into the next request sharing the context. Re-entry on a class already in flight returns the queryset unchanged (`permissions.py:192-193`) — partial-narrow, never raise. The seen-set keys on the `DjangoType` *class* object, so a secondary-rooted walk that re-reaches its model via the primary still terminates (primary ≠ secondary in the set). All four behaviors are pinned: `test_cycle_guard_contextvar_breaks_mutual_cascade` (including the exception-path `finally` reset), `test_self_referential_fk_cascades_once`, `test_secondary_type_as_root_reaches_primary_on_transitive_revisit`, plus an autouse `_assert_contextvar_clean` fixture that makes any leak a hard failure.
- **Edge scope is tight and empirically pinned.** The `getattr(field, "column", None) is not None` test (rather than a bare `hasattr`) correctly excludes M2M and `GenericRelation` (whose `column` attribute *exists* but is `None` under Django 6.0) — `test_single_column_scope_skips_m2m_reverse_and_generic` asserts the exact cascadable set `{"fk", "o2o", "content_type"}` and individually verifies each excluded kind. The explicit `parent_link` guard drops the MTI `<parent>_ptr` edge that otherwise passes the two-predicate test (`test_mti_parent_link_edge_excluded`), preventing a child row from being silently narrowed by its MTI-parent type's hook.
- **Data-isolation correctness.** Nullable-FK rows survive a fully-hiding target via the `| Q(<fk>__isnull=True)` disjunct (`test_nullable_fk_rows_preserved`); a hidden-target row and a missing-target row are indistinguishable in the result, so the cascade never leaks "you may not see this" (`test_hidden_and_missing_targets_indistinguishable`). The target subquery base is pinned to the caller's *resolved* alias via `queryset.db` (`permissions.py:224`), not the private `_db`, so sharded callers never compose a cross-database `__in` (`test_multi_db_subquery_pinned_to_caller_alias`, `FAKESHOP_SHARDED`-gated).
- **Pure `.filter` composition, zero added round-trips.** `_walk` never evaluates, reorders, or projects; the `__in` subqueries compile into the caller's single `SELECT` (`test_cascaded_traversal_adds_zero_queries` pins an absolute count of 1 with an `"IN (SELECT"` right-path guard, distinguishing real composition from a silently-empty walk). The identity-hook skip (`has_custom_get_queryset() is False`, `permissions.py:222`) avoids emitting a dead `__in (SELECT ...)` for default targets (`test_identity_hook_targets_skipped_no_sql`), and unregistered targets (`registry.get` → `None`) are skipped (`test_unregistered_target_model_skipped`).
- **`fields=` validation is loud and well-specified.** `None` (walk all) vs `[]` (defined no-op) vs unknown/non-cascadable name (`ConfigurationError` naming field/model/cascadable-set) vs bare string (rejected up front so `fields="item"` does not validate per-character) are all distinct and each pinned (`test_fields_*`). A cascadable-but-hookless name validates clean and is skipped by the per-edge gate (`test_fields_valid_but_hookless_name_accepted`).
- **Async/sync parity is a deliberate single-walk design, not a gap.** The async twin wraps the *entire* sync walk in `sync_to_async`, so an `async def` target hook still raises `SyncMisuseError` from `aapply_cascade_permissions` (no awaiting context inside the worker thread). This is documented in the module docstring and pinned by `test_aapply_async_target_hook_still_raises`; the off-loop execution + no-leak property is pinned by `test_aapply_runs_walk_off_event_loop`. Because there is no second async walk, there is no parity surface to drift.
- **Composition with the optimizer and gates is verified.** A cascading hook is a custom hook, so the optimizer falls back from FK-id elision / `select_related` to a `Prefetch` baked with the live `info` (`test_fk_id_elision_falls_back_for_cascading_target`, `test_nested_relation_traversal_respects_target_cascade`), and a `strictness="raise"` run stays silent because the cascade composes SQL rather than lazy-loading (`test_strictness_raise_silent_across_cascaded_shape`). The `check_<field>_permission` input gates run *after* the cascade narrows rows, and a gate denial is byte-identical whether or not a hidden row exists (`test_gate_denial_no_existence_leak`) — the no-existence-leak property.
- **Docstrings and GLOSSARY are accurate.** The module/function docstrings precisely describe the four ported upstream invariants and the three package adaptations (registry primary resolution, identity-hook skip, `parent_link` exclusion). `GLOSSARY.md:171-200` matches the implementation verbatim, including the `fields=` semantics, the sync/async pair, and the composition section — no drift. No TODOs, no stale spec references.

### Summary

`permissions.py` is genuinely new 0.0.10 code (the cascade-permissions surface, never previously reviewed) and it holds up to scrutiny as a data-isolation-critical module. The cycle guard is correctly a `ContextVar` with `finally`-reset request isolation across WSGI/ASGI and the asgiref-copied async-worker context; the edge scope is tight (single-column forward FK/OneToOne only, with the `column is not None` and `parent_link` subtleties handled and individually pinned); nullable-FK rows are preserved; subqueries are alias-pinned to `queryset.db`; the walk is pure `.filter` composition with zero added round-trips; and the sync-misuse routing is delegated to the package's single canonical helper. The async twin is a `sync_to_async` wrap of the one sync walk, so there is no parity gap — the documented `SyncMisuseError`-from-both-variants behavior is intentional and tested. The test suite is unusually thorough, pinning every invariant, edge case, and composition surface with right-path guards. No High or Medium findings; one stylistic Low (a bare `field.remote_field` access after two guarded `getattr`s) that is correct by short-circuit and recorded only to pre-empt re-flagging. The cycle diff against the baseline is empty (the file was not touched this cycle); this is a fresh first review of standing code.

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass; 267 files left unchanged.
- `uv run ruff check --fix .` — pass; all checks passed.

### Notes for Worker 3
- Zero High, zero Medium. One Low (`### `field.remote_field` is a bare attribute access while the two preceding predicates use guarded `getattr``) is explicitly no-action: it is correct by `and` short-circuit (the third clause is only reached for concrete forward FK/OneToOne fields, which always carry `remote_field`), and a defensive `getattr` would guard a state the first two predicates already exclude. Recorded only to pre-empt re-flagging; no edit warranted.
- No GLOSSARY-only fix in scope — `GLOSSARY.md:171-200` (`apply_cascade_permissions` entry) matches the implementation verbatim, no drift.
- Cycle diff against `CYCLE_BASELINE` is empty; the file was not modified this cycle.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern.

No comment/docstring edits in scope. The module-level docstring and per-function docstrings accurately describe the four ported upstream invariants and the three package adaptations; no stale comments, no TODOs, no obsolete spec references.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

Not warranted — no source edit was made this cycle (review-only). Per `AGENTS.md` ("Do not update CHANGELOG.md unless explicitly instructed") and the active plan `docs/review/review-0_0_10.md` (silent on changelog edits for review artifacts), no changelog entry applies.

---

## Verification (Worker 3)

### Logic verification outcome

No-source-edit (shape #5) + no-findings (shape #1) on genuinely new, data-isolation-critical 0.0.10 code (`permissions.py`, never reviewed before). Did NOT rubber-stamp — independently re-derived each of the six dispatch-named highest-risk invariants against the actual source and `tests/test_permissions.py`:

1. **ContextVar reset in `finally`.** `apply_cascade_permissions::apply_cascade_permissions` #"token = _cascade_seen.set(seen)" installs a fresh `{cls}` on the root call and resets in a `finally` (unconditional, fires on the walk-body exception path too). Non-root re-entry `if cls in seen: return queryset` partial-narrows without raising; non-root non-seen path uses `try/finally: seen.discard(cls)`. No cross-request guard leak. Pinned by `test_cycle_guard_contextvar_breaks_mutual_cascade` (asserts the `finally` reset after a `RuntimeError("boom")` walk body) + the autouse `_assert_contextvar_clean` fixture making any residual set a hard failure.
2. **Single-column forward FK / OneToOne only; MTI `parent_link` exclusion.** `_is_cascadable_edge` = `related_model is not None AND column is not None AND not remote_field.parent_link`. The `column is not None` (not `hasattr`) correctly excludes M2M / `GenericRelation` whose `column` attribute exists-but-is-`None` under Django 6.0. `test_single_column_scope_skips_m2m_reverse_and_generic` asserts the exact set `{"fk", "o2o", "content_type"}` and individually checks each excluded kind; `test_mti_parent_link_edge_excluded` confirms the parent-link passes both upstream predicates yet is dropped by the guard.
3. **Nullable-FK rows preserved.** `_walk` composes `Q(<field>__in=target_qs) | Q(<field>__isnull=True)`. `test_nullable_fk_rows_preserved` (hide-everything hook keeps the null-FK row) + `test_hidden_and_missing_targets_indistinguishable`.
4. **Alias pinning via `queryset.db`.** `_walk` #"field.related_model._default_manager.using(queryset.db).all()" uses the public router-resolved `queryset.db`, not private `_db`. `test_multi_db_subquery_pinned_to_caller_alias` (FAKESHOP_SHARDED-gated).
5. **Sync/async parity — no gap.** `aapply_cascade_permissions` is a pure `sync_to_async(apply_cascade_permissions, thread_sensitive=True)(...)` wrap of the one sync walk; no second walk exists. An `async def` hook raises `SyncMisuseError` from both variants via the single `apply_type_visibility_sync` probe (confirmed at `utils/querysets.py::apply_type_visibility_sync`, line 93). Pinned by `test_aapply_runs_walk_off_event_loop` + `test_aapply_async_target_hook_still_raises`.
6. **Composition with `check_<field>_permission` gates.** Cascade narrows rows in `get_queryset` first; gates judge input after, over narrowed rows. `test_cascade_then_filter_gate_composition`, `test_cascade_then_order_gate_composition`, and the load-bearing `test_gate_denial_no_existence_leak` (byte-identical message AND `.extensions` with/without a hidden row) pin the no-existence-leak property.

Also confirmed the delegated chokepoints exist as cited: `SyncMisuseError` (`utils/querysets.py:35`), `apply_type_visibility_sync` (`utils/querysets.py:93`), `has_custom_get_queryset` (`types/base.py:669`), `registry.get` (`registry.py:221`) — and the `has_custom_get_queryset() is False` identity-hook skip + unregistered-target skip in `_walk` (pinned by `test_identity_hook_targets_skipped_no_sql` / `test_unregistered_target_model_skipped`).

**Single Low — correctly no-action.** The bare `field.remote_field` access (third clause of `_is_cascadable_edge`) is correct by `and` short-circuit: the first two clauses (`related_model is not None`, `column is not None`) pin the field to a concrete forward FK/OneToOne, which always carries `remote_field`, so the third clause cannot fault. No source defect; recorded only to pre-empt re-flagging. Verbatim trigger phrasing present, not a GLOSSARY-only fix — not a disqualifier.

### DRY findings disposition

DRY = None, accepted. Re-derived: the one data-leak-sensitive op routes through the single `apply_type_visibility_sync`; the cascadable-edge predicate is defined once in `_is_cascadable_edge` and consumed by both `_cascadable_edge_names` (validator) and `_walk` (walk), so scope cannot drift; the async twin is a `sync_to_async` wrap of the one sync walk (no second implementation). No near-copy to hoist.

### Temp test verification

No temp test needed. The six invariants are each pinned by a named test in `tests/test_permissions.py` that grep-matches and reads as a genuine right-path assertion (absolute query counts with `"IN (SELECT"` presence guards, exact cascadable-set equality, byte-identical-error checks). The source was read directly; the short-circuit reasoning for the single Low is verifiable by inspection. No executable confirmation gap remained.

### Shape #5 additional checks
- `git diff --stat <CYCLE_BASELINE> -- django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md`: empty for owned paths (the file was not touched this cycle — first review of standing code). Dirty working-tree files (`__init__.py`, `pyproject.toml`, `uv.lock`, `dicta.md`) are all diff-empty vs the baseline SHA → pre-baseline, not this item's edits.
- Each Worker 2 section opens with `Filled by Worker 1 per no-source-edit cycle pattern.` ✓
- The single Low has verbatim trigger phrasing and is no-action (not a GLOSSARY-only fix) ✓
- Changelog `Not warranted` cites BOTH `AGENTS.md` and the active plan's silence; `git diff -- CHANGELOG.md` empty ✓
- `uv run ruff format --check` (1 file already formatted) + `uv run ruff check` (All checks passed) on `permissions.py` ✓
- GLOSSARY (`#apply_cascade_permissions`) matches the implementation — the four invariants, `fields=` semantics, sync/async pair, and composition section — and is diff-empty vs baseline (no GLOSSARY-only fix) ✓

### Verification outcome

`cycle accepted; verified` — sets top-level `Status: verified` AND marks the `permissions.py` checklist box in `docs/review/review-0_0_10.md`.
