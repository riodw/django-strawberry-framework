# Review: `django_strawberry_framework/permissions.py`

Status: verified

## DRY analysis

- None — the module is already the single home of the cascade-visibility contract. `permissions.py::_is_cascadable_edge` is the ONE definition of "cascadable edge" (both the `fields=None` full walk via `_walk`/`_cascadable_edges` and the `fields=` validator via `_validate_fields`/`_cascadable_edge_names` key off it, so scope cannot drift between the two entry paths), the per-edge sync `get_queryset` invocation is delegated to the canonical `utils/querysets.py::apply_type_visibility_sync` (the package's ONE sync-misuse site, Decision 10), and the async twin `aapply_cascade_permissions` wraps the one sync `_walk` through `sync_to_async` rather than carrying a second async walk. The this-cycle `model_for` promotion (commit `7a17ba75`) is itself a completed DRY consolidation — the prior inline `cls.__django_strawberry_definition__.model` read is now the shared `utils/querysets.py::model_for` source — so there is nothing left to consolidate (shadow overview reports 0 repeated string literals).

## High:

None.

## Medium:

None.

## Low:

None.

## What looks solid

### DRY recap

- **Existing patterns reused.** The model-handle read at `permissions.py::apply_cascade_permissions #"model = model_for(cls)"` now routes through `utils/querysets.py::model_for` (def `utils/querysets.py:94`, `return type_cls.__django_strawberry_definition__.model` at `:105`) — the same single-source promotion (commit `7a17ba75`) that hit `connection.py`, `relay.py`, `mutations/resolvers.py`, and `types/relay.py`. The per-edge target-hook run routes through the canonical `utils/querysets.py::apply_type_visibility_sync` (`permissions.py::_walk #"apply_type_visibility_sync("`), keeping ONE sync-misuse-rejection site package-wide (Decision 10). `SyncMisuseError` is re-exported via the redundant-alias form (`permissions.py #"from .utils.querysets import SyncMisuseError as SyncMisuseError"`, the `types/relay.py` convention) and adds no new public name (already in package-root `__all__` via `types`). `has_custom_get_queryset` (`types/base.py`) is the canonical "target has a real hook" gate reused as the per-edge skip predicate.
- **New helpers considered.** None needed at this granularity. Folding `_cascadable_edge_names` into `_cascadable_edges` callers was considered and rejected — the frozenset wrapper names the `fields=`-validation intent (Decision 5 step 1) and keeps `_validate_fields` at one abstraction level. An async-native walk to mirror the sync one is correctly rejected by the existing design (the async twin wraps the single sync walk, so an `async def` target hook raises `SyncMisuseError` identically from both variants — no coroutine-color duplication).
- **Duplication risk in the current file.** The four `getattr(field, ..., default)` reflective probes in `_is_cascadable_edge` are not a smell — each tests a distinct attribute (`related_model`, `column`, `many_to_many`, `parent_link`) and the `and`-chain order is load-bearing (short-circuits before `field.remote_field` is dereferenced on non-forward-relation fields). The two `Q(**{...})` constructions in `_walk` (`__in` / `__isnull`) are the two halves of the single nullable-FK-preserving disjunct, not a near-copy. The async-recourse string at `permissions.py::_walk` (`:271-276`) is a deliberate per-call message distinct from the get_queryset-seam recourse strings in `utils/querysets.py` / `mutations/resolvers.py`, not a hoistable literal.

### Other positives

- **The `model_for` promotion preserves the cascade visibility/scope invariants.** Verified at source: `model_for(cls)` (`permissions.py:225`) returns `cls.__django_strawberry_definition__.model` byte-for-byte verbatim (`utils/querysets.py:105`) — semantics-identical to the pre-commit inline read (`git show 7a17ba75 -- permissions.py`: a one-line read-site swap plus one import). The resulting `model` handle is used ONLY for (a) `_validate_fields(model, fields)` → edge-name validation off `model._meta.get_fields()`, and (b) `_walk(model, …)` → edge enumeration via `_cascadable_edges(model)`. It is NEVER substituted for the visibility queryset seed: each edge's target rows are seeded from `field.related_model._default_manager.using(queryset.db).all()` (`permissions.py:266`) and narrowed through the target type's own `get_queryset` via `apply_type_visibility_sync`. No existence-leak, no visibility weakening, no DB-alias change.
- **Empty cycle diff confirmed (genuine shape #5).** `git diff 7a174e8a3f6f9beab67e590c980c2074ee34a3c5 -- django_strawberry_framework/permissions.py` and `git diff HEAD -- …` are both empty — the `7a17ba75` change (+2/-2) is cumulative-in-HEAD, not a pending edit. No source-logic, test, or comment change this cycle.
- **ContextVar cycle guard correct under both runtimes.** Root call installs `{cls}` and resets the var in a `finally` (frame-exit cleanup survives a handler exception); re-entry on an in-flight `cls` returns the partially-narrowed queryset without raising; non-root frames `seen.discard(cls)` in their own `finally`. `ContextVar` (not a plain global) so request isolation holds under WSGI/ASGI, and the async twin's `sync_to_async` install/reset runs on the asgiref-copied context (never leaking back to the event-loop task). Untouched by the promotion.
- **Scope-leak guards defensively tight.** `_is_cascadable_edge` excludes M2M (the explicit `not many_to_many` guard handles the Django 5.2 case where `ManyToManyField.column` is non-`None`), reverse relations / `GenericForeignKey` / `GenericRelation` (via `related_model` / `column` presence tests, `column` value-checked not `hasattr`-checked to exclude the Django 6.0 `column=None` attributes), composite-PK/FK targets, and the MTI `<parent>_ptr` parent link (explicit `parent_link` guard) — each documented with the exact Django-version rationale.
- **Loud, well-shaped `fields=` validation.** `_validate_fields` distinguishes the `None` sentinel (walk all) from `[]` (defined no-op), rejects a bare string before it iterates into per-character noise, and converts a raw `TypeError` from a non-iterable into a contract-naming `ConfigurationError` (feedback M2). The `list(...)`-before-`set(...)` ordering is deliberate so unhashable entries are caught by the string check rather than escaping from `set(...)`.
- **Zero added round-trips + no orphan.** `_walk` composes pure `.filter(...)` `__in` subqueries and never evaluates, reorders, or projects, so the subqueries compile into the caller's single `SELECT` (Decision 7); `lru_cache(maxsize=1024)` on `_cascadable_edges` caches immutable post-app-loading model metadata with bounded, correctness-neutral eviction. `grep -rn _model_for django_strawberry_framework/` returns zero — the private twin was fully removed in the same commit; no dangling symbol.

### Summary

Drift re-review of the package-root cascade-permissions module after commit `7a17ba75` ("Promote model_for(type_cls) to utils") changed it +2/-2. Both `git diff 7a174e8a -- permissions.py` and `git diff HEAD -- permissions.py` are empty — the change is cumulative-in-HEAD. The only change this cycle is the `model_for` promotion: one import (`from .utils.querysets import apply_type_visibility_sync, model_for`) and one read-site swap (`model = model_for(cls)`). `model_for` returns `__django_strawberry_definition__.model` verbatim, so the read is semantics-identical; the model handle feeds only edge validation and enumeration, never the per-edge visibility seed (`field.related_model._default_manager.using(queryset.db).all()`), so the cascade visibility and single-column-forward scope invariants are unchanged — no existence-leak and no visibility weakening. Every other load-bearing invariant holds: ContextVar cycle guard with `finally` reset, M2M / MTI-`<parent>_ptr` exclusions, nullable-FK `__isnull=True` preservation, caller-alias pinning, sync+`sync_to_async` through ONE walk, zero round-trips. GLOSSARY `#apply_cascade_permissions` (180-209) is contract-level prose that abstracts over the internal lookup (no `model_for` mention; `model_for` is a private utils helper with no `__all__`, so its absence is correct) — no drift. Zero findings; genuine shape #5 no-source-edit cycle.

---

## Verification (Worker 3)

### Logic verification outcome
Zero High / Medium / Low findings to disposition (all `None.`); nothing to address or reject. Drift re-verification of the `model_for` promotion (commit `7a17ba75`) over the package-root cascade module.

- **Stability / zero-edit proof (genuine shape #5).** `git diff HEAD -- django_strawberry_framework/permissions.py` empty; `git diff 7a174e8a3f6f9beab67e590c980c2074ee34a3c5 -- django_strawberry_framework/permissions.py` empty; owned-paths `--stat` (`django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md`) vs baseline empty. The `7a17ba75` change is cumulative-in-HEAD: `git show` confirms it is exactly +1/-1 (import line `apply_type_visibility_sync` → `apply_type_visibility_sync, model_for`) plus +1/-1 (`model = cls.__django_strawberry_definition__.model` → `model = model_for(cls)`). All three Worker 2 sections carry the `Filled by Worker 1 per no-source-edit cycle pattern.` gate line.
- **`model_for` semantics-identical.** `model_for(type_cls)` returns `type_cls.__django_strawberry_definition__.model` verbatim (`utils/querysets.py:105`), so the read-site swap is byte-for-byte semantics-preserving vs the pre-commit inline read.
- **No existence-leak / no visibility weakening (independently confirmed at source).** The `model` handle from `model_for(cls)` (`permissions.py:225`) flows ONLY to (a) `_validate_fields(model, fields)` (`:226`, edge-name validation off `model._meta`) and (b) `_walk(model, …)` (`:233`/`:240`, edge enumeration via `_cascadable_edges(model)`). It is NEVER substituted for the per-edge visibility seed, which stays independently `field.related_model._default_manager.using(queryset.db).all()` (`:266`) narrowed through the target type's own hook via `apply_type_visibility_sync` (`:267`). The seed is handle-independent — a handle→seed swap would have to rewrite line 266, which is unchanged. Pinned by `test_cascade_excludes_rows_with_hidden_targets`, `test_hidden_and_missing_targets_indistinguishable`, `test_gate_denial_no_existence_leak` (tests/test_permissions.py).
- **Four invariants untouched and test-pinned.** ContextVar cycle guard + `finally` reset (`apply_cascade_permissions:228-242`; `test_cycle_guard_contextvar_breaks_mutual_cascade`, `test_self_referential_fk_cascades_once`); single-column forward FK/O2O scope with M2M / reverse / generic exclusions (`_is_cascadable_edge:107-112`; `test_single_column_scope_skips_m2m_reverse_and_generic`); MTI `<parent>_ptr` `parent_link` exclusion (`test_mti_parent_link_edge_excluded`); nullable-FK `__isnull=True` preservation (`_walk:279`; `test_nullable_fk_rows_preserved`); caller-alias `queryset.db` pinning (`:266`; `test_multi_db_subquery_pinned_to_caller_alias`); zero round-trips (`test_cascaded_traversal_adds_zero_queries`); sync + `sync_to_async`-through-one-walk async twin (`test_sync_helper_raises_syncmisuseerror_on_async_target_hook`, `test_aapply_runs_walk_off_event_loop`, `test_aapply_async_target_hook_still_raises`).
- **`_model_for` orphan grep zero.** `grep -rn "_model_for" django_strawberry_framework/` → exit 1 (no hits); the private twin was fully removed in the same commit, no dangling symbol. `grep model_for permissions.py` → exactly the import (`:64`) + one call site (`:225`).
- **GLOSSARY accurate (genuine #5, no GLOSSARY-only fix).** `#apply_cascade_permissions` (`docs/GLOSSARY.md:180-209`) is contract-level prose, accurate vs live source, and byte-unchanged vs baseline (`git diff … -- docs/GLOSSARY.md` empty). The lone `model_for` token in GLOSSARY (`:865`) is `registry.model_for_type` — a different registry method, not the `utils/querysets.py::model_for` helper, which (private, no `__all__`) correctly carries no entry.

### DRY findings disposition
DRY is a single `None —`. Confirmed: the cascade is the one home of the cascade-visibility contract; the `model_for` promotion is itself a completed DRY consolidation (the old inline `__django_strawberry_definition__.model` read now routes through the shared `utils/querysets.py::model_for`, single-sited). Nothing to carry forward.

### Temp test verification
- None created — no-source-edit cycle; existing named tests in `tests/test_permissions.py` provide the invariant pins cited above.
- Disposition: n/a.

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the `permissions.py` checklist box in `docs/review/review-0_0_11.md`.

### Changelog disposition (verified)
`Not warranted` accepted: `git diff -- CHANGELOG.md` empty; disposition cites BOTH AGENTS.md #21 and the active plan's silence. Internal-only framing matches the actual diff scope (zero source/test/doc edits this cycle; the `model_for` promotion was changelog-dispositioned at its own landing).

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass (`289 files left unchanged`; the COM812-with-formatter warning is the standing config note, not a failure).
- `uv run ruff check --fix .` — pass (`All checks passed!`).

### Notes for Worker 3
- No source/test/GLOSSARY/CHANGELOG edits. The `model_for` promotion (commit `7a17ba75`) is cumulative-in-HEAD; both `git diff 7a174e8a -- permissions.py` and `git diff HEAD -- permissions.py` are empty.
- No High/Medium/Low findings to disposition; DRY is a single `None —`.
- No GLOSSARY-only fix in scope — the `#apply_cascade_permissions` entry (`docs/GLOSSARY.md:180-209`) is contract-level prose, accurate vs source, and never names `model_for` (a private utils helper with no `__all__`).
- Invariant-check anchor for re-verification: `model_for(cls)` returns `cls.__django_strawberry_definition__.model` verbatim (`utils/querysets.py:105`); handle used only for `_validate_fields` + `_walk` edge enumeration, never the per-edge visibility seed (`field.related_model._default_manager.using(queryset.db).all()`, `permissions.py:266`). No existence-leak / no visibility weakening.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern. No comment or docstring edits — the module docstring, the `model_for`/`apply_type_visibility_sync` import comment block (`permissions.py:60-63`), and the `_cascade_seen` ContextVar comment all remain accurate after the promotion. No stale references introduced.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

- **Not warranted.** Internal-only review with zero source/test/doc edits this cycle (the `model_for` promotion is cumulative-in-HEAD and was changelog-dispositioned at its own landing). AGENTS.md #21 ("Do not update CHANGELOG.md unless explicitly instructed") and the active plan `docs/review/review-0_0_11.md` (silent on changelog edits for review cycles) both apply.
