# Review: `django_strawberry_framework/permissions.py`

Status: verified

## DRY analysis

- None — the cascade-permissions subsystem is already single-sourced. `_is_cascadable_edge` is the one definition of "cascadable edge" that both the full walk (`_walk` via `_cascadable_edges`) and the `fields=` validator (`_validate_fields` via `_cascadable_edge_names`) key off, so scope cannot drift between the two entry paths. The per-edge sync `get_queryset` invocation is delegated to the canonical `utils/querysets.py::apply_type_visibility_sync` (the package's single sync-misuse site, Decision 10), and the async twin `aapply_cascade_permissions` wraps the one sync `_walk` through `sync_to_async` rather than carrying a second async walk implementation. There is no near-copy or repeated literal to consolidate (shadow overview reports 0 repeated string literals).

## High:

None.

## Medium:

None.

## Low:

None.

## What looks solid

### DRY recap

- **Existing patterns reused.** `permissions.py::_walk #"apply_type_visibility_sync("` routes every per-edge target-hook run through the canonical `utils/querysets.py::apply_type_visibility_sync` (def at `utils/querysets.py:100`), keeping ONE sync-misuse-rejection site package-wide (Decision 10). `SyncMisuseError` is re-exported via the established redundant-alias form (`permissions.py #"from .utils.querysets import SyncMisuseError as SyncMisuseError"`, the `types/relay.py` convention) and adds no new public name (already in package-root `__all__` via `types`). `has_custom_get_queryset` (`types/base.py:669`) is the canonical "target has a real hook" gate reused as the per-edge skip predicate.
- **New helpers considered.** Considered folding `_cascadable_edge_names` into `_cascadable_edges` callers directly; rejected — the tiny frozenset wrapper names the `fields=`-validation intent (Decision 5 step 1) and keeps `_validate_fields` reading at one abstraction level. Considered an async-native walk to mirror the sync one; correctly rejected by the existing design (the async twin wraps the single sync walk, so an `async def` target hook raises `SyncMisuseError` identically from both variants — no coroutine-color duplication).
- **Duplication risk in the current file.** The four `getattr(field, ..., default)` reflective probes in `_is_cascadable_edge` are not a duplication smell — each tests a distinct field attribute (`related_model`, `column`, `many_to_many`, `parent_link`) and the `and`-chain ordering is load-bearing (short-circuits before `field.remote_field` is dereferenced on non-forward-relation fields). The two `Q(**{...})` constructions in `_walk` (`__in` and `__isnull`) are the two halves of the single nullable-FK-preserving disjunct, not a near-copy.

### Other positives

- **Empty cycle diff confirmed.** `git diff 2e35ec278e585cb2a8a93b84ae641d1126ceb3d5 -- django_strawberry_framework/permissions.py` and `git diff HEAD -- …` are both empty — no source-logic, test, or comment change this cycle. Genuine shape #5 no-source-edit cycle.
- **GLOSSARY is current, no drift.** Grepped every public symbol (`apply_cascade_permissions`, `aapply_cascade_permissions`, `SyncMisuseError`) against `docs/GLOSSARY.md`. The dedicated `apply_cascade_permissions` entry (GLOSSARY.md:180-210) accurately documents the single-column forward FK/O2O scope, the MTI `<parent>_ptr` exclusion, the four invariants (ContextVar cycle guard, single-column forward scope, `__isnull=True` nullable-FK preservation, `queryset.db` alias pinning), the loud `fields=` validation (bare-string rejection, unknown/non-cascadable name → `ConfigurationError`), the sync/async pair with `SyncMisuseError`, and the zero-round-trip `__in`-subquery composition. `SyncMisuseError`'s entries (GLOSSARY.md:1115, 1331) correctly attribute the raise to the shared `apply_type_visibility_sync`. No GLOSSARY-only fix in scope.
- **ContextVar cycle guard is correct under both runtimes.** Root call installs `{cls}` and resets the var in a `finally` (frame-exit cleanup survives a handler exception); re-entry on an in-flight `cls` returns the partially-narrowed queryset without raising; non-root frames `seen.discard(cls)` in their own `finally`. `ContextVar` (not a plain global) so request isolation holds under WSGI/ASGI, and the async twin's `sync_to_async` install/reset runs on the asgiref-copied context (never leaking back to the event-loop task).
- **Scope-leak guards are defensively tight.** `_is_cascadable_edge` excludes M2M (the explicit `not many_to_many` guard handles the Django 5.2 case where `ManyToManyField.column` is non-`None`), reverse relations / `GenericForeignKey` / `GenericRelation` (via `related_model` / `column` presence tests, with `column` value-checked not `hasattr`-checked to exclude the Django 6.0 `column=None` attributes), composite-PK/FK targets, and the MTI `<parent>_ptr` parent link (explicit `parent_link` guard) — each documented with the exact Django-version rationale.
- **Loud, well-shaped validation.** `_validate_fields` distinguishes the `None` sentinel (walk all) from `[]` (defined no-op), rejects a bare string before it iterates into per-character noise, and converts a raw `TypeError` from a non-iterable into a contract-naming `ConfigurationError` (feedback M2). The `list(...)`-before-`set(...)` ordering is deliberate so unhashable entries are caught by the string check rather than escaping from `set(...)`.
- **Zero added round-trips.** `_walk` composes pure `.filter(...)` `__in` subqueries and never evaluates, reorders, or projects, so the subqueries compile into the caller's single `SELECT` (Decision 7). The `lru_cache(maxsize=1024)` on `_cascadable_edges` caches immutable post-app-loading model metadata with bounded, correctness-neutral eviction.

### Summary

`permissions.py` is the cascade-permissions subsystem (`apply_cascade_permissions` / `aapply_cascade_permissions`) and is unchanged this cycle (empty diff vs both the per-cycle baseline `2e35ec27` and HEAD). Every load-bearing invariant the spawn brief named holds: ContextVar cycle guard with `finally` reset, single-column forward FK/O2O scope (with explicit M2M / MTI-`<parent>_ptr` exclusions carrying Django-version rationale), nullable-FK preservation via the `__isnull=True` disjunct, caller-alias pinning via `queryset.db`, sync+`sync_to_async` pairing through ONE sync walk, and zero added round-trips via `__in` subqueries. DRY is fully resolved — the edge predicate is single-sourced and the sync-misuse routing is delegated to the canonical `apply_type_visibility_sync`. GLOSSARY prose is current with no drift. Zero findings; genuine shape #5 no-source-edit cycle.

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass (289 files left unchanged).
- `uv run ruff check --fix .` — pass (all checks passed).

### Notes for Worker 3
- Zero findings across High/Medium/Low. Diff empty vs both the per-cycle baseline `2e35ec278e585cb2a8a93b84ae641d1126ceb3d5` and HEAD (`git diff … -- django_strawberry_framework/permissions.py` empty for both).
- No GLOSSARY-only fix in scope — `docs/GLOSSARY.md` entries for `apply_cascade_permissions` (180-210) and `SyncMisuseError` (1115, 1331) are current vs the implementation (verified via grep of all public symbols).
- No deferred findings; no false-premise rejections.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

- **Not warranted.** Internal-only review with zero source/test/doc edits this cycle. AGENTS.md #21 ("Do not update CHANGELOG.md unless explicitly instructed") and the active plan `docs/review/review-0_0_11.md` (silent on changelog edits for review cycles) both apply.

---

## Verification (Worker 3)

### Zero-edit proof (shape #5)
- `git diff 2e35ec278e585cb2a8a93b84ae641d1126ceb3d5 -- django_strawberry_framework/permissions.py` and `git diff HEAD -- …` are BOTH empty. `permissions.py` is absent from `git diff --stat <baseline> -- django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md`.
- The sole owned-path dirty hunk in the stat is `tests/management/test_inspect_django_type.py` (a file/image output-converter test, `_scalar_row` / `convert_field_output` — wholly unrelated to the cascade subsystem). It is the standing `inspect_django_type` concurrent-maintainer work this release (AGENTS.md #33; recorded in my memory across the connection.py / list_field.py cycles). Its owning artifact `rev-management__commands__inspect_django_type.md` is `Status: verified` (plan box still `[ ]` at review-0_0_11.md:103, so attributed under #33 rather than the closed-sibling carve-out). Either way it is not owned by THIS permissions cycle and is not a rejection trigger. The cycle's "Files touched: None" claim holds.
- CHANGELOG `git diff -- CHANGELOG.md` empty. Each Worker 2 section opens "Filled by Worker 1 per no-source-edit cycle pattern."

### Logic verification outcome
- High / Medium / Low all `None.` — independently confirmed genuine (not lazy), every load-bearing invariant pinned by a named test in `tests/test_permissions.py`:
  - ContextVar cycle guard + `finally` reset: `test_cycle_guard_contextvar_breaks_mutual_cascade` (re-entry partial-narrows; root resets in `finally`; `ContextVar` not a global so WSGI/ASGI + asgiref-copied-context isolation).
  - Single-column forward FK/O2O scope with M2M / reverse / generic exclusions: `test_single_column_scope_skips_m2m_reverse_and_generic`; MTI `<parent>_ptr` exclusion via the explicit `parent_link` guard: `test_mti_parent_link_edge_excluded`.
  - Nullable-FK `__isnull=True` preservation: `test_nullable_fk_rows_preserved`.
  - Caller-alias pinning via `queryset.db`: `test_multi_db_subquery_pinned_to_caller_alias`.
  - Zero added round-trips via `__in` subqueries: `test_cascaded_traversal_adds_zero_queries`.
  - Sync + `sync_to_async` sharing ONE `_walk`: `test_sync_helper_raises_syncmisuseerror_on_async_target_hook` + `test_aapply_async_target_hook_still_raises` (async twin raises identically from inside the worker thread).
  - `fields=` loud validation: `test_fields_bare_string_raises`, `test_fields_non_iterable_raises_configuration_error`, `test_fields_unhashable_entry_raises_configuration_error`, `test_fields_non_string_entry_raises_configuration_error`, `test_fields_unknown_name_raises`, `test_fields_non_cascadable_name_raises`, `test_fields_empty_list_cascades_nothing`.
- Reused-symbol claims confirmed live: `apply_type_visibility_sync` (def `utils/querysets.py:100`, `async_recourse` param) and `SyncMisuseError` (`utils/querysets.py:35`, `(ConfigurationError, RuntimeError)`); `has_custom_get_queryset` exists at `types/base.py`. The redundant-alias re-export adds no new public name.

### Genuine #5, not a missed #4 (GLOSSARY accuracy)
- `docs/GLOSSARY.md` `## apply_cascade_permissions` (180-207) read against live source: single-column forward FK/O2O scope, registry-primary lookup, skip-no-custom-hook gate, `Q(<fk>__in) | Q(<fk>__isnull=True)`, `queryset.db` alias pinning, depth-1 transitive cascade, the four invariants (ContextVar `finally` reset / single-column forward / `__isnull=True` / alias pinning), sync/async pair via `sync_to_async(thread_sensitive=True)`, `SyncMisuseError`, zero-round-trip `__in` — all accurate. `SyncMisuseError` entry (1115) correctly attributes the raise to the shared `apply_type_visibility_sync`. No GLOSSARY-only fix owed.

### DRY findings disposition
- DRY `- None` accepted: `_is_cascadable_edge` is the single edge predicate keyed by both the full walk and the `fields=` validator; per-edge sync hook delegated to canonical `apply_type_visibility_sync`; async twin wraps the one sync `_walk`. No near-copy to consolidate.

### Temp test verification
- None created; the existing permanent suite pins every invariant.

### Verification outcome
- `cycle accepted; verified` — sets top-level `Status: verified` AND marks the `permissions.py` checklist box.

---
