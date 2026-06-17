# Review: `django_strawberry_framework/orders/sets.py`

Status: verified

## DRY analysis

- **Cross-folder filter/order family-wrapper consolidation (forward to project pass, do not merge locally).** The thin permission delegates on `OrderSet` — `_request_from_info` (sets.py:302-313), `_extract_branch_value` (sets.py:316-330), `_active_permission_field_paths` (sets.py:333-347), `_active_permission_targets` (sets.py:350-372), `_invoke_permission_method` (sets.py:375-390), `_run_permission_checks` (sets.py:393-455) — are the symmetric twins of `FilterSet`'s same-named methods (filters/sets.py:1285-1289/1292 etc.), each already a one-line delegate to the single-sited `utils/permissions.py` mechanics. The remaining per-family residue is the family-label string (`"OrderSet"` vs `"FilterSet"`), the `related_attr`/`target_attr` token (`"related_orders"`/`"orderset"` vs `"related_filters"`/`"filterset"`), and `logic_keys` (`frozenset()` vs the filter operator bag). Consolidating the wrapper *layer itself* (e.g. a shared `PermissionDelegateMixin` parameterized by a small config object) spans two folders and would have to preserve each family's public method names (the documented consumer-facing surface). Defer until the project-level pass (`docs/review/rev-django_strawberry_framework.md`) triages the whole filter+order+utils family-wrapper set together; the per-folder passes correctly left this cross-folder.
- **`_verbatim_attr` (sets.py:56-62) vs `utils/permissions.py::_verbatim_path` (permissions.py:148-150).** Two byte-identical `def f(python_attr): return python_attr` fallbacks now exist — one module-private in `orders/sets.py`, one module-private in `utils/permissions.py`. They serve the same "attr is its own source path" role. The order-side copy exists only to avoid allocating a fresh lambda per traversal (its docstring says so). Act-now candidate: export `utils.permissions._verbatim_path` (drop the leading underscore, add to `__all__`) and have `orders/sets.py::_active_permission_targets` pass it as `fallback_path`, deleting `_verbatim_attr`. This is a genuine same-shape duplicate across the orders→utils edge the refactor already established. Small win; defer-or-act is a judgment call for Worker 2 — flagged here so the DRY-cycle export picks it up. (Forward to project pass if Worker 2 declines, since the cleanest home is the already-shared util.)

## High:

None.

## Medium:

None.

## Low:

### `_path_traverses_to_many` process-lifetime cache keyed by model `type` (forward-looking)

`_path_traverses_to_many` (sets.py:66-97) gained `@lru_cache(maxsize=2048)` in commit `880f8a52` (a separate change from the permission consolidation under review). The cache key is `(model, field_path)` where `model` is a Django model **class**. For shipped consumer models this is correct and the bounded size + pure-metadata answer are sound (the docstring justifies both). The only latent hazard is dynamically-generated model classes in tests / migrations that are created and discarded under the same qualified name across runs: the cache holds a strong reference to every distinct `type` object passed, so a long-lived process that churns dynamic model classes accumulates entries (up to the 2048 cap, then evicts LRU). This is benign today — the example/test suite's dynamic models are few and the cap is generous — and the same `lru_cache(maxsize=2048)` pattern is used in `utils/permissions.py::_check_method_name` (permissions.py:45). No action. Defer until a test fixture is observed generating >2048 distinct model classes in one process, OR until the package adopts a `WeakKeyDictionary`-style cache convention for model-keyed memoization; at that point fold both this and `_check_method_name` through the shared convention.

### `_resolve_order_expressions` aggregate-alias direction parse via `"ASC" in direction.name` (forward-looking)

`_resolve_order_expressions` (sets.py:525) selects `models.Min` vs `models.Max` with `aggregate = models.Min if "ASC" in direction.name else models.Max`. This is correct for all six `Ordering` members (every ascending member name contains `ASC`, every descending contains `DESC`, and the substring `"ASC"` cannot appear in a `DESC*` name). It is a string-substring read of an enum that already exposes the semantic via `direction.resolve(...)`. Brittle only if a future `Ordering` member is added whose name contains neither token or both — none is planned. No action. Defer until `Ordering` gains a member outside the `ASC*`/`DESC*` naming scheme; at that point replace the substring test with an explicit ascending/descending predicate on the enum (e.g. an `Ordering.is_ascending` property single-sourced in `orders/inputs.py`).

## What looks solid

### DRY recap

- **Existing patterns reused.** The permission pipeline is a thin delegation layer over the single-sited shared core: `_active_permission_targets` → `utils/permissions.py::active_permission_targets` (permissions.py:153-200); `_run_permission_checks` → `run_active_input_permission_checks` (permissions.py:295-338); `_request_from_info`/`_extract_branch_value`/`_invoke_permission_method` → their `utils/permissions.py` namesakes. The class-expansion cache + reentry guard reuse `sets_mixins.expanded_once` (sets.py:235-240); `related_orders` collection reuses `collect_related_declarations` (sets.py:126-133); the lifecycle slot names are single-sourced in `_lifecycle: SetLifecycleAttrs` (sets.py:186-190). The traversal mechanics live in `utils/input_values.py::iter_active_fields`.
- **New helpers considered.** A shared `_verbatim_path`/`_verbatim_attr` factoring across the orders→utils edge — recorded as an act-now DRY candidate above rather than as a recap dismissal, since it is a real same-shape duplicate. No other new local helper is warranted: the apply pipeline's sync/async pair deliberately repeats its five-step body (only the `sync_to_async` wrap differs) and folding it would obscure the async-only wrapping decision.
- **Duplication risk in the current file.** The 4× `"related_orders"` literal (overview "Repeated string literals") is the family-collection attr name passed to `collect_related_declarations`, `active_permission_targets`, and read in docstrings — it is the order-family parameterization token, intentionally spelled per-call (the filter twin spells `"related_filters"`); hoisting to a module constant would not reduce drift risk because the two families must differ here by design. The `apply_sync`/`apply_async` near-duplicate bodies are intentional sibling design (the async one wraps only `_run_permission_checks` in `sync_to_async`; `order_by`/`annotate` are pure-Python + non-I/O queryset-method calls per spec-028 Decision 8 step 7).

### Other positives

- **Refactor preserves behavior (the central review charge).** The `79b74b46` consolidation is verified behavior-preserving: (a) LEAF half — `_active_permission_field_paths` now returns `_active_permission_targets(input)[0]`, same `field_specs=_field_specs`, same `related_attr="related_orders"`, same `logic_keys=frozenset()`, and `fallback_path` moved from an inline `lambda python_attr: python_attr` to the byte-identical module-level `_verbatim_attr`; (b) RELATED half — the deleted `_iter_active_related_branches` is replaced by the shared `run_active_input_permission_checks` reading `cls._active_permission_targets(input)[1]`; RELATED classification in `iter_active_fields` (input_values.py:179-180) keys ONLY off `related_attr` membership and the branch tuple reads `related_obj`/`raw_value` (never `spec`), so the superset config (now carrying `_field_specs` + empty `logic_keys`) yields byte-identical branch tuples to the old field-spec-less call; (c) `logic_keys=frozenset()` keeps the order side LOGIC-free, matching the no-operator-bag contract.
- **Permission gate fires before queryset mutation (security-critical, both paths).** `apply_sync` (sets.py:560-571) calls `_request_from_info` → `_run_permission_checks` BEFORE `_normalize_input`/`get_flat_orders`/`_resolve_order_expressions`/`annotate`/`order_by`. `apply_async` (sets.py:599-613) does the same with `_run_permission_checks` wrapped in `sync_to_async(thread_sensitive=True)`. A denial raises pre-mutation; no ordering is applied on the denied path. Sync/async parity confirmed (identical step sequence, async wraps only the permission call).
- **Duck-typed contract satisfied on both families.** `run_active_input_permission_checks` calls `cls._active_permission_targets(input_value)` (permissions.py:325); grep confirms BOTH `OrderSet` (sets.py:350) and `FilterSet` (filters/sets.py:1292) define it, so the shared core never hits an `AttributeError` regardless of which family drives it. The deleted `_iter_active_related_branches` has zero dangling references on the order side (the filter side's same-named method is a separate, still-used method).
- **RelatedOrder cross-relation traversal correct.** `_run_permission_checks` recurses into each active `RelatedOrder` branch via the shared core (recurse into child orderset's own `_run_permission_checks`, then fire the parent's per-branch gate) — the documented parent-vs-child double-dispatch, deduped per `(class, method)` through the shared `_fired` map. The position-side-channel defense (parent `check_<branch>_permission` on an active branch) matches GLOSSARY `RelatedOrder`:1034.
- **To-many fan-out guard in ordering.** `_resolve_order_expressions` (sets.py:520-530) routes a to-many path through a `Min`/`Max` aggregate annotation + GROUP-BY-forcing `.annotate` instead of a raw fan-out `order_by("rel__col")` — preventing row multiplication that would corrupt connection cursors and `totalCount` (docs/feedback.md P1-B). `_path_traverses_to_many` stops correctly at the first non-relation or unresolvable segment.
- **GLOSSARY accurate, no drift.** `OrderSet` (940-946), `Ordering` (936), `RelatedOrder` (1032-1036), `Meta.orderset_class` (828-834) all match the implementation; the active-input-only + active-branch double-dispatch prose is exactly the shipped contract. No internal helper names are documented, so the `_iter_active_related_branches`→`_active_permission_targets` rename creates no GLOSSARY drift.

### Summary

`orders/sets.py` is in good shape. The `79b74b46` permission consolidation is a clean, behavior-preserving delegation: the order side gained the duck-typed `_active_permission_targets` contract that the shared `run_active_input_permission_checks` calls, fused the former two-walk LEAF/RELATED traversal into one `iter_active_fields` pass, and the inline `lambda` fallback became the module-level `_verbatim_attr`. LEAF and RELATED partitions are byte-identical to the prior logic (RELATED classification is independent of the now-populated `field_specs`/`logic_keys`), the security-critical gate-before-mutation invariant holds in both sync and async apply paths, and RelatedOrder cross-relation traversal + the to-many aggregate guard are intact. This-cycle diff is empty (the refactor landed under HEAD); no High/Medium findings; two forward-looking Lows (model-`type`-keyed `lru_cache` lifetime, enum-name substring direction parse) and two DRY candidates (the cross-folder family-wrapper consolidation forwarded to the project pass, and an act-now `_verbatim_path` dedupe across the orders→utils edge). No High → no source edit required → shape #5 (no-source-edit cycle).

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
None — no-source-edit cycle.

### Tests added or updated
None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — 270 files unchanged.
- `uv run ruff check --fix .` — all checks passed (only the pre-existing COM812-vs-formatter config notice).

### Notes for Worker 3
- This-cycle diff against HEAD is empty; the `79b74b46` permission consolidation (and the `880f8a52` `lru_cache` add) already landed under HEAD. Reviewed against current source.
- Low #1 (`_path_traverses_to_many` model-`type`-keyed `lru_cache` lifetime): forward-looking, deferred with trigger ">2048 distinct model classes in one process OR adoption of a WeakKeyDictionary model-keyed cache convention" — fold with `utils/permissions.py::_check_method_name` then. No source edit.
- Low #2 (`"ASC" in direction.name` substring direction parse): forward-looking, deferred with trigger "`Ordering` gains a member outside the `ASC*`/`DESC*` naming scheme". Correct for all six current members. No source edit.
- DRY act-now candidate (`_verbatim_attr` vs `utils/permissions.py::_verbatim_path`): flagged for the DRY cycle; if Worker 2/DRY acts, the home is the shared util (export `_verbatim_path`). Not actioned this cycle (Worker 1 may not edit source).
- DRY cross-folder family-wrapper consolidation: forwarded to `docs/review/rev-django_strawberry_framework.md` project pass.
- No GLOSSARY-only fix in scope — GLOSSARY verified accurate.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern. No comment/docstring defects found: every delegate's docstring accurately names its `utils/permissions.py` target and the family-specific config it passes; the module docstring's helper list was updated by `79b74b46` to name `_active_permission_targets` (no stale `_iter_active_related_branches` reference remains). No source edit.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern. Not warranted — no source edit this cycle (review-only). Per AGENTS.md #21 ("Do not update CHANGELOG.md unless explicitly instructed") and the active plan (`docs/review/review-0_0_10.md`) being silent on changelog edits for review cycles.

---

## Verification (Worker 3)

### DRY adjudication — the flagged `_verbatim_attr` / `_verbatim_path` inconsistency

**Verdict: Path (A) — genuinely act-now.** The artifact's shape #5 (no-source-edit) disposition is therefore WRONG; this cycle needs a real source edit.

**Evidence (independently re-derived, not taken from the artifact):**

- Byte-identical bodies and signatures. `orders/sets.py::_verbatim_attr` is `def _verbatim_attr(python_attr: str) -> str: return python_attr`; `utils/permissions.py::_verbatim_path` is `def _verbatim_path(python_attr: str) -> str: return python_attr`. Only the name and docstring differ — the signature line and the single `return python_attr` body match character-for-character.
- No new import edge. `orders/sets.py` already imports five names from `..utils.permissions` (lines 41-47: `active_permission_targets`, `extract_branch_value`, `invoke_permission_method`, `request_from_info`, `run_active_input_permission_checks`). Adding one more (the promoted verbatim helper) rides the existing edge — zero new coupling. The cross-folder DAG direction (orders → utils, one-way) is unchanged.
- The shared util is the cleanest home. `grep -rn` over the package shows exactly two defs and exactly three `fallback_path=` call sites: `filters/sets.py:1311` passes a *real* transform (`cls._form_key_for_python_attr`), so it is not a duplicate; the order side (`orders/sets.py:370`) and the permissions-internal `active_related_branches` (`permissions.py:241`) both pass the verbatim identity. The util already owns the parameter contract (`fallback_path: Callable[[str], str]`, called at `permissions.py:196`), so the verbatim default belongs there.

**Why the (B) "intentional sibling design" defenses do not hold:**

- The order-side docstring's rationale ("module-level, not a per-call lambda, so `_active_permission_targets` does not allocate a fresh closure each traversal") justifies *not inlining a lambda*. It does NOT justify a *second* module-level copy: a module-level function living in the shared util satisfies the no-fresh-closure goal identically. The rationale argues against lambdas, not against reuse.
- "Too trivial to share" fails the AGENTS.md DRY-first mandate explicitly ("always recommend the root-cause fix over the surface patch; pragmatic shortcuts are NEVER a viable answer"). A one-line pure helper duplicated across an already-established import edge is exactly the drift surface the mandate targets: if the meaning of "verbatim" ever changes, two copies must change in lockstep.
- The "different role" nuance is real but non-controlling. The permissions-side `_verbatim_path` is a discard-path placeholder (its sole caller `active_related_branches` does `_leaf_paths, branches = active_permission_targets(...); return branches` — the leaf output it feeds is thrown away), whereas the order-side `_verbatim_attr` is load-bearing (its output flows through `_active_permission_field_paths` → `check_<field>_permission` gate dispatch in the pre-bind no-field-spec case). But identical body + shared home + no new edge means DRY consolidation still wins; the role difference is a comment-clarity matter, addressed by the work order's docstring instruction, not a reason to keep two copies.

Worker 1's own DRY bullet labeled this "a genuine same-shape duplicate across the orders→utils edge" and an "act-now candidate." Marking that AND shape #5 is the self-contradiction the dispatch flagged; under the DRY-first mandate the act-now finding controls.

### Work order for Worker 2 (the consolidation)

1. In `utils/permissions.py`: promote `_verbatim_path` to a module-public name `verbatim_path` (drop the leading underscore) and add `"verbatim_path"` to `__all__` (the sorted 8-name list at lines 61-70 — insert keeping alphabetical order; it lands between `run_active_input_permission_checks` and the rest as appropriate, re-sort the list). Update the internal call site at `permissions.py:241` (`fallback_path=_verbatim_path` → `fallback_path=verbatim_path`). Broaden its docstring one line so it reads as the shared verbatim fallback for both the related-only discard caller and the order side (it is no longer "the related-only callers" exclusively).
2. In `orders/sets.py`: add `verbatim_path` to the existing `from ..utils.permissions import (...)` block (lines 41-47), delete the local `_verbatim_attr` def (lines 56-62), and change `_active_permission_targets`'s `fallback_path=_verbatim_attr` (line 370) to `fallback_path=verbatim_path`. The order-side rationale (module-level, not a per-call lambda) is preserved — `verbatim_path` is module-level in the util.
3. Sweep for orphan references: `grep -rn "_verbatim_attr\|_verbatim_path" django_strawberry_framework/ tests/` must return only the new `verbatim_path` after the change (AGENTS.md "grep-sweeping for `::OldName` references in the same change"). No symbol-qualified `::_verbatim_path` / `::_verbatim_attr` references exist in docs or comments (grep clean today).
4. Run `uv run ruff format .` and `uv run ruff check --fix .` per AGENTS.md #15.
5. No new test required: the consolidation is behavior-preserving (identical pure body), and both call paths are already exercised by the existing permission suite (the order side's leaf-path fallback and the related-branch discard path). The comment pass must confirm the promoted docstring describes the now-shared contract.
6. Changelog: internal-only refactor (no public-API surface change — the helper is package-internal mechanics), so "Not warranted" with both citations (AGENTS.md #21 + active-plan silence) remains correct.

### Behavior-preservation re-confirmation (independent of the DRY verdict)

The `79b74b46` refactor is verified behavior-preserving and security-correct; the only defect is the *disposition*, not the source logic:

- **Gate-before-mutation (sync).** `apply_sync` (lines 560-571): `_request_from_info` → `_run_permission_checks` fire (560-561) BEFORE `_normalize_input` / `get_flat_orders` / `_resolve_order_expressions` / `annotate` / `order_by` (562-571). A denial raises pre-mutation; no ordering is applied on the denied path.
- **Gate-before-mutation (async).** `apply_async` (599-613): `_request_from_info` (599) then `await sync_to_async(cls._run_permission_checks, thread_sensitive=True)(...)` (600-603) before any queryset call. Only the permission call is wrapped; step sequence identical to sync.
- **Partition equivalence (the fusion).** `_active_permission_targets` passes the superset config to the shared `active_permission_targets`; the classifier appends LEAF as `spec.django_source_path` or `fallback_path(python_attr)` and RELATED as `(python_attr, related_obj, raw_value)` — RELATED never reads `spec`, so it is independent of the now-populated `field_specs` and of `logic_keys=frozenset()`. The LEAF half reproduces the prior `_active_permission_field_paths`; the RELATED half reproduces the prior field-spec-less related walk. The two-walk result is reproduced byte-identically. (Same fused-partition equivalence pattern I verified on `filters/sets.py` this release: kept-kind classification independent of the zeroed config dimension + disjoint LEAF/RELATED/LOGIC name families.)
- **Duck-typed contract.** Shared `run_active_input_permission_checks` (permissions.py:325) calls `cls._active_permission_targets(input_value)`; `OrderSet` defines it (sets.py:350), so no AttributeError regardless of which family drives the shared core.
- **RelatedOrder double-dispatch.** `_run_permission_checks` → `run_active_input_permission_checks(..., target_attr="orderset")` recurses into the child orderset's `_run_permission_checks` then fires the parent's per-branch gate, deduped per `(class, method)` via the shared `_fired` map. Intact.

Behavior preservation is NOT the reason for rejection — it holds. The rejection is solely the act-now DRY consolidation the shape #5 disposition skipped.

### Verification outcome

`revision-needed` — sets top-level `Status: revision-needed`. The `_verbatim_attr` / `_verbatim_path` duplication is an act-now DRY consolidation (Path A); the no-source-edit disposition is wrong. Work order recorded above for Worker 2. The `orders/sets.py` checklist box in `docs/review/review-0_0_10.md` is NOT marked. Re-spawns Worker 1 (no-source-edit cycle) → Worker 2 (the consolidation edit).

---

## Fix report (Worker 2, pass 2)

DRY consolidation per Worker 3's Path-A work order. Consolidated single-spawn shape (exclusively a DRY delegation to a canonical helper — semantics preserved by construction), so logic + comment + changelog are handled in one pass.

### Files touched
- `django_strawberry_framework/utils/permissions.py` — promoted `_verbatim_path` → public `verbatim_path` (dropped the leading underscore); broadened its docstring to read as the shared identity `fallback_path` for BOTH the related-only discard caller (`active_related_branches`) AND the order side (it now folds in the order-side "module-level, not a per-call lambda" rationale that previously justified the second copy); added `"verbatim_path"` to `__all__` (kept alphabetical); repointed the internal call site in `active_related_branches` (`fallback_path=_verbatim_path` → `verbatim_path`).
- `django_strawberry_framework/orders/sets.py` — added `verbatim_path` to the existing `from ..utils.permissions import (...)` group; deleted the local `_verbatim_attr` def (the former lines 56-62); repointed `OrderSet._active_permission_targets`'s `fallback_path=_verbatim_attr` → `verbatim_path`. No other change; the order-side no-fresh-closure guarantee is preserved (`verbatim_path` is module-level in the util).

### Tests added or updated
None — existing coverage suffices. The helper is a pure identity function; both call paths are already exercised through the permission-target traversal suite: the order-side LEAF fallback flows through `OrderSet._active_permission_field_paths` → `check_<field>_permission` gate dispatch (order permission tests), and the related-only discard path runs through `active_related_branches` (filter/order related-branch permission tests). No behavior changed (identical body, identical fallback semantics at both sites), so no new pin is warranted per AGENTS.md test-placement / logic-fix dicta.

### Validation run
- `uv run ruff format .` — pass (270 files left unchanged).
- `uv run ruff check --fix .` — pass (All checks passed; only the pre-existing COM812-vs-formatter config notice).
- `grep -rn "_verbatim_attr\|_verbatim_path\|verbatim_path" django_strawberry_framework/ tests/` — only the new `verbatim_path` (5 hits: def + `__all__` + 1 import + 2 call sites); zero orphans, zero `::_verbatim*` symbol-qualified refs in docs/comments.
- `git diff HEAD --stat` on the two files — +13/-13, scoped to the promotion + reuse only; `uv.lock` untouched.

### Comment/docstring disposition (inline — the broadened docstring IS the comment work)
The promoted `verbatim_path` docstring now describes the now-shared contract (identity fallback for any caller with no lookup-to-source remap; names both the related-only discard caller and the order side; retains the module-level no-fresh-closure note). The order-side `_verbatim_attr` docstring is gone with its def. No stale comment remains: `OrderSet._active_permission_targets`'s docstring already describes the delegation without naming the old helper. No other comment edits in scope.

### Changelog disposition (inline)
`Not warranted`. Internal-only refactor — `verbatim_path` is package-internal mechanics with no consumer-visible / public-API surface change. Cites BOTH AGENTS.md #21 ("Do not update CHANGELOG.md unless explicitly instructed") AND the active plan (`docs/review/review-0_0_10.md`) being silent on changelog authorization for this cycle. No `CHANGELOG.md` edit; `git diff HEAD -- CHANGELOG.md` empty.

### Notes for Worker 3
- No shadow file used (trivial identity-helper move; source read directly).
- Promotion is byte-identical in body to both prior defs; only name + docstring changed. The util now exports 9 names (was 8), `__all__` re-sorted to keep alphabetical with `verbatim_path` last.
- Both prior defs were module-private; no external import path broke (no consumer imported `_verbatim_attr` / `_verbatim_path`).
- Status set to bare `fix-implemented` (routes to Worker 3 terminal-verify).

---

## Verification (Worker 3, pass 2)

**Terminal verify of the Path-A DRY consolidation. Outcome: `verified`.** All work-order items independently confirmed against the working tree; behavior preservation (re-confirmed in pass 1) still holds because the refactor only swapped a helper reference for a byte-identical promoted twin.

### Diff matches the work order exactly
`git diff HEAD -- utils/permissions.py orders/sets.py` is +13/-13, scoped to the promotion + reuse only:
- **`utils/permissions.py`** — `_verbatim_path` → public `verbatim_path` (signature + single `return python_attr` body unchanged); docstring broadened to name BOTH callers (the related-only `active_related_branches` discard caller AND the order side) and retains the module-level no-fresh-closure rationale; `"verbatim_path"` added to `__all__`; the internal call site in `active_related_branches` (`permissions.py:249`) repointed `fallback_path=verbatim_path`.
- **`orders/sets.py`** — `verbatim_path` added to the existing `from ..utils.permissions import (...)` group (line 47, inside the already-established import edge — no new edge); local `_verbatim_attr` def deleted; `OrderSet._active_permission_targets`'s `fallback_path` repointed to `verbatim_path` (line 362). Still an identity fallback — no behavioral change.

### `verbatim_path` public + in `__all__`, docstring covers both callers
Confirmed: `def verbatim_path` at `permissions.py:149` (public, underscore dropped); `"verbatim_path"` present in `__all__` (line 70) and the list is correctly alphabetical (it sorts last). Docstring names the related-only discard caller and `OrderSet._active_permission_targets`, and notes the filter side passes its own real remap — accurate three-way contract. The internal `permissions.py` call site uses the new name.

### grep-sweep genuinely clean
`grep -rn "_verbatim_attr\|_verbatim_path\|verbatim_path" django_strawberry_framework/ tests/` returns exactly 5 hits, ALL the new `verbatim_path` (def + `__all__` + 1 import + 2 call sites: `permissions.py:70/149/249`, `sets.py:47/362`). Zero `_verbatim_attr` / `_verbatim_path` orphans; zero stale `_verbatim_*` refs. A broader sweep over docs/comments for the English word "verbatim" surfaced only unrelated prose (port descriptions, pass-through docs) — no symbol-qualified `::_verbatim_*` references in any standing doc or comment.

### No new import cycle
The `orders → utils.permissions` edge already existed (five names imported pre-cycle); adding `verbatim_path` rides it. `permissions.py`'s import block (lines 26-42) pulls only `__future__`/stdlib/`django.http`/`..exceptions`/`.input_values` — no back-edge to `orders`. The module docstring's own claim ("depends on neither family package... both can import it without a cycle") holds. One-way DAG unchanged.

### No new test — sound call
The helper is a pure identity function; the promotion is byte-identical in body to both prior defs, so the consolidation is behavior-preserving by construction. Both call paths are already exercised by the existing permission-target traversal suite (order-side LEAF fallback via `_active_permission_field_paths` → gate dispatch; related-branch discard path via `active_related_branches`). No new pin warranted per AGENTS.md test dicta. Accepted.

### Ruff + changelog
`uv run ruff format --check` — 2 files already formatted. `uv run ruff check` — All checks passed (only the pre-existing COM812-vs-formatter config notice). `git diff HEAD -- CHANGELOG.md` empty; `Not warranted` cites BOTH AGENTS.md #21 AND the active plan's silence — and the "internal-only" framing is honest: `verbatim_path` is package-internal mechanics (a module-public name within `utils/permissions.__all__`, not a consumer-facing public surface — consumers use Meta classes, never these helpers). Correct state.

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the `orders/sets.py` checklist box in `docs/review/review-0_0_10.md`.
