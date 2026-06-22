# Review: `django_strawberry_framework/utils/querysets.py`

Status: verified

## DRY analysis

- None — this module **is** the consolidation point for the query-source + `get_queryset` visibility contract (the 0.0.9 DRY pass, `docs/feedback.md` Major 1). Every helper is single-sited and reused package-wide rather than duplicated: `model_for` is the one home for `type_cls.__django_strawberry_definition__.model` (consumed by `permissions.py`, `relay.py`, `connection.py`, `types/relay.py`, `mutations/resolvers.py`); `initial_queryset` seeds from `model_for` so the model lookup never re-spells; `reject_async_in_sync_context` single-sources the coroutine-rejection message template for all three sync hook seams (`apply_type_visibility_sync` + the two write-auth hooks via `mutations/resolvers.py` and `mutations/sets.py`); `apply_type_visibility_sync`/`apply_type_visibility_async` are the sole sync/async visibility routers; `normalize_query_source` is the one Manager→QuerySet coercion; `post_process_queryset_result_sync`/`async` compose the list-field consumer-resolver shape. No internal near-copy or repeated dispatch literal remains to fold.

## High:

None.

## Medium:

None.

## Low:

None.

## What looks solid

### DRY recap

- **Existing patterns reused.** `apply_type_visibility_sync` (`utils/querysets.py::apply_type_visibility_sync`) reuses `reject_async_in_sync_context` for its coroutine guard rather than re-spelling the `inspect.iscoroutine` + `close()` + raise sequence; `initial_queryset` (`utils/querysets.py::initial_queryset`) reuses `model_for` for the model handle; `post_process_queryset_result_sync`/`async` reuse `normalize_query_source` + the `apply_type_visibility_*` pair. The module composes its own primitives top-down.
- **New helpers considered.** None needed at this granularity — the six public helpers plus the `SyncMisuseError` marker are already split by abstraction level (raw model handle → seeded queryset → coercion → colored visibility call → consumer-resolver composition). Folding any pair would re-merge a deliberately distinct seam (e.g. sync vs async visibility, or model-only `model_for` vs queryset-seeding `initial_queryset`).
- **Duplication risk in the current file.** The two `recourse`-bearing async-misuse strings (`_RELAY_ASYNC_RECOURSE` at module scope and the surface-specific recourse passed by callers) read as near-copies but are the **distinct** surface-guidance tails of the same contract — the message *template* lives once in `reject_async_in_sync_context`; only the trailing `recourse` clause varies per caller (Relay default vs cascade vs connection). Correct sibling design, not duplication.

### Other positives

- **Visibility seam is single-sited and not bypassed.** A package-wide grep for `.get_queryset(` outside this module returns only two hits, neither a bypass: `filters/base.py::DjangoTypeFilter.get_queryset #"super().get_queryset(request)"` is the Django-admin/cookbook `get_queryset(request)` auto-derivation method (a different signature and purpose entirely), and `optimizer/plans.py #"DjangoType.get_queryset(queryset, info)"` is a docstring reference. Every real `DjangoType.get_queryset(queryset, info)` invocation routes through `apply_type_visibility_sync`/`apply_type_visibility_async` (walker, connection, list_field, filters/sets, types/relay, mutations/resolvers, permissions). The "a visibility-hook mistake is a data-leak bug" routing invariant the module docstring asserts holds.
- **`model_for` is correct and orphan-free.** It returns `type_cls.__django_strawberry_definition__.model` verbatim, so the 7a17ba75 promotion that replaced the private `types/relay.py::_model_for` and three inline reads is semantics-identical. `grep -rn _model_for` returns zero — the private twin is fully removed, no orphan. The handle is used only for model-identity / `_meta` / `DoesNotExist` reads at every call site, never substituted for the visibility queryset seed, so no existence-leak regression. Note `registry.model_for_type` is a **distinct** registry-keyed method (returns `type[Model] | None`), not a duplicate of `model_for`.
- **`reject_async_in_sync_context` is fail-loud and warning-safe.** A coroutine result is `close()`d before the raise (silencing the `coroutine was never awaited` warning that `filterwarnings = error` would turn into a test failure — consistent with the `tests/conftest.py` async-leak discipline), then a `SyncMisuseError` naming `owner.method` / `context` / `recourse` is raised. Treating a truthy coroutine as success would be a silent authorization bypass for the permission seams; rejecting loudly is the correct fail-closed shape.
- **`SyncMisuseError` dual-inheritance contract intact.** It multiple-inherits `ConfigurationError` AND `RuntimeError` so `except ConfigurationError` and `except RuntimeError` both match; it is exported through the package root (`__init__.py` `__all__`) and re-exported from `types/relay.py` for back-compat (`from ..utils.querysets import SyncMisuseError as SyncMisuseError`).
- **`apply_type_visibility_async` honors the Decision 9 await contract.** It awaits the coroutine before returning, fixing the earlier-implementation bug (calling `.filter` on a coroutine) called out in its docstring.
- **Cycle-safe by construction.** The module imports only `inspect`, `typing`, `django.db.models`, and `..exceptions.ConfigurationError`; it never imports back into the package, so `types/relay.py` (imported at module top by `types/base.py`) can import from here without closing a load cycle.

### Summary

A genuine no-source-edit (shape #5) cycle: `git diff 7f56013994cd57ce6d819f765918520b55139098 -- utils/querysets.py`, `git diff HEAD -- utils/querysets.py`, and `git log baseline..HEAD -- utils/querysets.py` are all empty; the last touch (7a17ba75, the `model_for` promotion) is cumulative-in-HEAD, not a pending edit. The DRY-cycle-added helpers (`model_for`, `reject_async_in_sync_context`, the `apply_type_visibility_*` pair) are correct and verbatim/semantics-preserving, and the `get_queryset` visibility seam is single-sited with no bypass. The only GLOSSARY-documented symbol from this file is `SyncMisuseError` (public, root `__all__`); its entry (#syncmisuseerror, GLOSSARY:1325-1337, plus the #relay-node-integration:1115 and overview:41/143/163/201 references) is accurate — ConfigurationError+RuntimeError multi-inherit, closed coroutine, single-sited `apply_type_visibility_sync`, package-root export with types.relay back-compat re-export, no drift. The remaining helpers are private/dotted-path (not in `utils/__init__.__all__`, which is `RelationKind`/`is_many_side_relation_kind`/`pascal_case`/`relation_kind`/`snake_case`/`unwrap_*`) → no GLOSSARY entry → absence correct. No High, no Medium, no Low.

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass; `289 files left unchanged`.
- `uv run ruff check --fix .` — pass; `All checks passed!`.

### Notes for Worker 3
- All severities `None.`; the file's diff is empty against baseline (`7f56013994cd57ce6d819f765918520b55139098`), against HEAD, and `git log baseline..HEAD -- utils/querysets.py` returns nothing. Last touch 7a17ba75 (`model_for` promotion) is cumulative-in-HEAD, not a pending edit.
- No GLOSSARY-only fix in scope: the one GLOSSARY-documented symbol (`SyncMisuseError`, #syncmisuseerror) is accurate as-is; all other helpers are private/dotted-path (not in `utils/__init__.__all__`) → no entry → absence correct.
- Visibility-seam single-siting verified by package-wide grep: the only two `.get_queryset(` hits outside this module are `filters/base.py::DjangoTypeFilter.get_queryset` (the unrelated `get_queryset(request)` admin/cookbook signature) and an `optimizer/plans.py` docstring reference — neither bypasses `apply_type_visibility_*`.
- `_model_for` orphan check: `grep -rn _model_for` returns zero.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern.

No comment or docstring edits in scope. The module docstring (the query-source + visibility contract description), the `SyncMisuseError` docstring (dual-inheritance rationale + filters/sets dispatcher note), and each helper docstring were re-read against current behavior and remain accurate — including the `reject_async_in_sync_context` authorization-bypass rationale and the `apply_type_visibility_async` Decision 9 await-contract note. No stale cross-module claims found.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

Not warranted. No source change this cycle (empty diff). Per `AGENTS.md` ("Do not update CHANGELOG.md unless explicitly instructed") and the active plan `docs/review/review-0_0_11.md` (silent on changelog edits for review cycles), no changelog entry is warranted.

---

## Verification (Worker 3)

### Logic verification outcome
All severities `None.` — genuine no-source-edit (shape #5) cycle. Each Worker 2 section opens with the `Filled by Worker 1 per no-source-edit cycle pattern.` gate line. The DRY-cycle-added helpers (`model_for`, `reject_async_in_sync_context`, `apply_type_visibility_*`) are cumulative-in-HEAD and independently confirmed correct:

- **Zero-edit proof clean all four axes:** `git diff 7f56013994cd57ce6d819f765918520b55139098 -- django_strawberry_framework/utils/querysets.py` empty; `git diff HEAD -- …` empty; `git log baseline..HEAD -- …` empty; owned-paths `--stat` (`django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md`) empty → no sibling attribution needed. Dirty tree is `docs/dry/` only.
- **`model_for` correct + orphan-free:** returns `type_cls.__django_strawberry_definition__.model` verbatim (querysets.py::model_for); `grep -rn _model_for` exit 1 (private twin fully removed, no orphan). `grep -rn "model_for(" ` confirms the def is single-sited in querysets.py; consumers (connection.py:827, permissions.py:225, relay.py:139/220, types/relay.py:111/173/762, mutations/resolvers.py:575/811/1094) all read the handle for model-identity / `_meta` / `DoesNotExist`, never as a visibility-queryset seed (the seed path is `apply_type_visibility_*(cls, initial_queryset(cls), info)`, and `initial_queryset` does its own handle-independent lookup) → no existence-leak regression. `registry.model_for_type` is a distinct registry-keyed method, not conflated.
- **`reject_async_in_sync_context` fail-closed:** querysets.py:86-91 — when `inspect.iscoroutine(value)` it `value.close()`s THEN raises `SyncMisuseError` (naming `owner.method` / `context` / `recourse`); there is no path returning a truthy coroutine. `apply_type_visibility_sync` (174-181) passes the hook result as the FIRST positional arg to the guard, so close+raise fires before any caller can treat it as success — the silent-authorization-bypass hazard is closed. Used by all three sync hook seams (this visibility seam + the two write-auth hooks via mutations/resolvers + mutations/sets per the docstring).
- **`apply_type_visibility_async` honors Decision 9:** awaits awaitables (198-199) before returning, fixing the prior `.filter`-on-coroutine bug; sync `get_queryset` passes through.
- **Visibility seam single-sited, not bypassed:** `grep -rn "\.get_queryset(" ` outside querysets.py returns exactly two non-bypass hits — `filters/base.py::DjangoTypeFilter.get_queryset` (the `get_queryset(self, request)` admin/cookbook auto-derivation method, a different signature confirmed at line 472) and an `optimizer/plans.py:176` docstring reference. No real `DjangoType.get_queryset(queryset, info)` invocation routes around `apply_type_visibility_sync/async`.

### DRY findings disposition
DRY-None genuine: this module IS the 0.0.9 consolidation point. The `_RELAY_ASYNC_RECOURSE` module constant vs caller-passed recourse are the distinct surface-guidance tails of one template (the template lives once in `reject_async_in_sync_context`); the six public helpers are split by abstraction level (raw handle → seeded queryset → coercion → colored visibility call → consumer-resolver composition) — folding any pair re-merges a deliberately distinct seam. Nothing forwarded.

### Temp test verification
None used — no-source-edit cycle; verification by grep + source read + ruff was sufficient.

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the `utils/querysets.py` checklist box. GLOSSARY `SyncMisuseError` entry (#syncmisuseerror, GLOSSARY:1325-1335) spot-checked accurate vs live source (ConfigurationError+RuntimeError multi-inherit, closed coroutine before raise, single-sited `apply_type_visibility_sync` routing, package-root export with types.relay back-compat re-export `from ..utils.querysets import SyncMisuseError as SyncMisuseError`). All other helpers are private/dotted-path (absent from `utils/__init__.__all__` = RelationKind/is_many_side_relation_kind/pascal_case/relation_kind/snake_case/unwrap_graphql_type/unwrap_return_type) → no GLOSSARY entry → absence correct, genuine #5 not missed #4. No GLOSSARY-only fix in scope. Ruff format-check (`1 file already formatted`) + check (`All checks passed!`) pass.
