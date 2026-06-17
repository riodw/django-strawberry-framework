# Review: `django_strawberry_framework/orders/`

Status: verified

Folder pass over `django_strawberry_framework/orders/` (`base.py`, `factories.py`, `inputs.py`, `sets.py`, `__init__.py`). All four file siblings closed `verified`: `rev-orders__base.md`, `rev-orders__factories.md`, `rev-orders__inputs.md`, `rev-orders__sets.md`. Baseline HEAD; the only dirty-vs-HEAD orders/utils files (`orders/sets.py` +`utils/permissions.py`, +13/-13) are the just-closed `verbatim_path` consolidation cycle's reviewed output, not unrelated concurrent work. Shadows regenerated for all five `orders/*.py` (the `__init__.py` shadow `docs/shadow/django_strawberry_framework__orders____init__.overview.md` covered explicitly).

## DRY analysis

- **Cross-folder filter/order family-wrapper consolidation — forward to project pass, do not merge at folder scope.** Every sibling artifact independently surfaced the same observation, and the family-wrapper layer spans `filters/` + `orders/` + `utils/`, so it cannot be resolved inside the `orders/` folder. The duplicated *shape* (not logic — the logic is already single-sited) is: (a) the permission delegate set on `OrderSet` (`orders/sets.py::OrderSet._request_from_info` / `_extract_branch_value` / `_active_permission_field_paths` / `_active_permission_targets` / `_invoke_permission_method` / `_run_permission_checks`) vs the byte-symmetric `FilterSet` twins (`filters/sets.py`); (b) the input-namespace materialize/clear pair + domain-local aliases (`orders/inputs.py` vs `filters/inputs.py`); (c) the `OrderArgumentsFactory` vs `FilterArgumentsFactory` 7-attr parameterization over `utils/inputs.py::GeneratedInputArgumentsFactory`; (d) the `RelatedOrder` vs `RelatedFilter` parameterization over `sets_mixins.RelatedSetTargetMixin`; (e) the `order_input_type` vs `filter_input_type` consumer helper, both already one-line delegates to `utils/inputs.py::build_lazy_input_annotation`. The residual per-family residue is the family-label string (`"OrderSet"`/`"orderset"`/`"related_orders"` vs the filter tokens) and `logic_keys` (`frozenset()` vs the operator bag). Any wrapper-layer hoist (e.g. a shared `PermissionDelegateMixin` parameterized by a small config) must preserve each family's public method names (the documented consumer-facing surface), so it is a deliberate project-pass triage of the whole filter+order+utils set together. Forwarded to `rev-django_strawberry_framework.md`; the per-folder passes correctly left it cross-folder.

- **filter/order `normalize_input_value` — confirmed NOT a shared traversal at folder scope; forward as a recorded-not-acted note.** Re-confirmed during this folder pass from the order side: `orders/inputs.py::normalize_input_value` is a whole-input walker delegating its dataclass/list/None-skip/leaf-vs-related traversal to the single-sited `utils/input_values.py::iter_active_fields`, emitting `(field_path, Ordering | None)`; the filter twin `filters/inputs.py::normalize_input_value` is a per-leaf value coercion (`isinstance`-dispatch into scalar/list/dict form-data) doing no traversal and called from inside the filter walker. Same name, different abstraction level; the only common mechanics already live in `utils/input_values.py` and the order side already consumes them. Cross-folder; forwarded to the project pass, do not force-merge.

- **No NEW orders-side `verbatim_path` duplicate remains.** Verified per the dispatch forward (#2): `grep -rnE '_verbatim_attr|_verbatim_path|verbatim_path' django_strawberry_framework/ tests/` returns exactly 5 hits, all the consolidated public `utils/permissions.py::verbatim_path` — the def (`permissions.py:149`), `__all__` entry (`permissions.py:70`), the internal call site (`permissions.py:249`), and the order side's import + use (`orders/sets.py:47`, `orders/sets.py:362`). The former `orders/sets.py::_verbatim_attr` byte-identical copy is gone; zero orphans, zero stale `_verbatim_*` references anywhere in source or tests. The prior cycle's act-now DRY consolidation is folder-clean.

## High:

None.

## Medium:

None.

## Low:

### Stale "dynamic OrderSet caching" coverage claim in the order test docstring + TREE.md (act-now folder finding)

`tests/orders/test_factories.py:1` (module docstring) and `docs/TREE.md:376` + `docs/TREE.md:515` (two identical tree-entry comments) all describe the order test file as covering *"BFS input generation **and dynamic OrderSet caching**."* The order side ships **no** dynamic cache: Layer 6 (`_dynamic_orderset_cache` / `get_orderset_class`) is a standing deferred non-goal — both the `orders/factories.py` module docstring and its TODO anchor (`factories.py::OrderArgumentsFactory` region #"standing deferred non-goal") state this, and the forward-reserved symbols are absent from the shipped module. The test file confirms it: all ten test functions are BFS / cycle / leaf-annotation / related-branch / collision / idempotency / shared-input / subclass-rejection / none-target-skip / double-enqueue-dedupe cases (`test_factory_visits_every_reachable_relatedorder_target_via_bfs` … `test_factory_dedupes_double_enqueued_target_via_seen_check`); there is exactly **zero** dynamic-cache coverage (grep for `dynamic` / `_make_cache` / `get_orderset_class` / `_dynamic_orderset_cache` in the test file returns only the line-1 docstring phrase itself). The claim is a copy-from-filter-side artifact — the filter twin `tests/filters/test_factories.py` / `filters/factories.py` genuinely ships and tests Layer 6, the order twin does not. A reader (or a future maintainer reviving Layer 6) is told coverage exists that does not.

This is the dispatch's ACT-NOW candidate (#1), and at folder scope it is a real, warranted edit: sibling-test consistency is the folder pass's explicit domain (the per-file `rev-orders__factories.md` Low was correctly forwarded here precisely because it touches files outside that cycle's single-file target). The fix is a verbatim phrase trim in three identical-wording locations — drop "` and dynamic OrderSet caching`" so each reads "BFS input generation.":

```tests/orders/test_factories.py:1
"""OrderArgumentsFactory tests for BFS input generation and dynamic OrderSet caching.
```

```docs/TREE.md:376
│   ├── test_factories.py         # OrderArgumentsFactory tests for BFS input generation and dynamic OrderSet caching.
```

```docs/TREE.md:515
│   ├── test_factories.py         # OrderArgumentsFactory tests for BFS input generation and dynamic OrderSet caching.
```

Recommended replacement text (Worker 2 lifts verbatim):

- `tests/orders/test_factories.py:1` → `"""OrderArgumentsFactory tests for BFS input generation.`
- `docs/TREE.md:376` and `docs/TREE.md:515` (both identical) → `│   ├── test_factories.py         # OrderArgumentsFactory tests for BFS input generation.`

Both `docs/TREE.md` lines are byte-identical, so a `replace_all` is safe. No source-logic change; the body of `tests/orders/test_factories.py` (the second docstring sentence already accurately enumerates BFS walk / collision / idempotency / subclass rejection / leaf+related annotation shape — no dynamic-cache mention) needs no edit. This Low drives `Status: under-review` so Worker 2 makes the edit.

## What looks solid

### DRY recap

- **Existing patterns reused.** The folder is a uniform thin-delegation family over single-sited shared cores: `RelatedOrder` over `sets_mixins.RelatedSetTargetMixin` (`orders/base.py`); `OrderArgumentsFactory` over `utils/inputs.py::GeneratedInputArgumentsFactory` (`orders/factories.py`); the input namespace over `utils/input_values.py::iter_active_fields` + `utils/inputs.py` generated-input mechanics (`orders/inputs.py`); the permission pipeline over `utils/permissions.py` (`orders/sets.py`, now including the consolidated `verbatim_path`); the consumer helper `order_input_type` over `utils/inputs.py::build_lazy_input_annotation` (`orders/__init__.py`). No machinery is re-implemented inside the folder.
- **Duplication risk in the current folder.** The cross-sibling repeated-literal compare (regenerated shadows) shows the only 2+-file literals are the family-parameterization tokens — `"OrderSet"` (as `family_label` vs `set_class_name` keyword roles into distinct `utils/inputs.py` helpers), `"orderset"` (`_rename_noun` collision wording vs `_related_target_attr` resolution slot), `"related_orders"` (the family-collection attr passed to `collect_related_declarations` / `active_permission_targets`), and `order_input_type` (the helper name appearing twice in its own `__init__.py`). Each is a deliberate per-family token spelled per-call (the filter twin spells the symmetric `"FilterSet"` / `"filterset"` / `"related_filters"` set); hoisting to module constants would not reduce drift risk because the two families must differ here by design. Genuine shared keys (the `DST_OPTIMIZER_*` family, pagination args) do not appear because they are already single-sourced outside this folder — confirming the single-sourcing holds. Import-based consolidation (the `verbatim_path` move) added no cross-file string literal, as expected.

(The "New helpers considered." bullet is dropped at folder scope: every candidate — the family-wrapper layer, the `normalize_input_value` pair, the deferred Layer-6 cache hoist — is cross-folder and owned by the project pass or a future revival card, not a folder-local extraction.)

### Other positives

- **`__init__.py` export surface is correct and filter-symmetric.** `__all__` is the 5-name tuple (`OrderSet`, `OrderSetMetaclass`, `Ordering`, `RelatedOrder`, `order_input_type`). `OrderArgumentsFactory` is deliberately NOT re-exported (advanced consumers import from `orders.factories` directly, matching the filter side keeping `FilterArgumentsFactory` out of `filters/__init__.py`, spec-028 Decision 2); `INPUTS_MODULE_PATH` / `_input_type_name_for` are re-exported at module scope but kept out of `__all__` (leading `_` flags them consumer-private), mirroring the filter convention. `OrderSetMetaclass` IS exported for one-for-one parity with the filter `FilterSetMetaclass` surface. The `_helper_referenced_ordersets` ledger is co-located with its only writer (`order_input_type`) per spec-028 Decision 2; the docstring honestly notes Slice 3 will wire `registry.clear()` to clear it via the two-step local-import dance — a forward-looking note, not a stale claim (no TODO anchor needed; it documents a future slice, not a deferred call path that must fail loudly).
- **Import-direction is a clean one-way DAG, no cycle.** Intra-folder: `base.py` (leaf — only `..sets_mixins`) ← `inputs.py` ← `sets.py` / `factories.py` ← `__init__.py`. `inputs.py`'s `from .sets import OrderSet` is `TYPE_CHECKING`-only (so no real `inputs↔sets` cycle); `sets.py`'s `from .inputs import _get_concrete_field_names_for_order` is function-scoped; the one `optimizer`/`types` references are `TYPE_CHECKING` or function-scoped. Every cross-folder edge fans strictly OUTWARD to the shared core (`utils/`, `sets_mixins`, `exceptions`, `types`); none of those import back into `orders/` (the `verbatim_path` consolidation rode the pre-existing `orders → utils.permissions` edge, adding no new coupling, re-verified). No circular-import risk.
- **Naming + error-handling are consistent across siblings and with the filter family.** Every public symbol carries the family noun (`OrderSet` / `Ordering` / `RelatedOrder` / `order_input_type` / `orderset_class`); permission denials raise pre-mutation in both `apply_sync` and `apply_async`; lazy related-class resolution propagates raw `ImportError` at the `base.py` layer without `ConfigurationError` rewrap (documented divergence). No naming or error-handling drift between the four files or against the filter twin.
- **Security-critical gate-before-mutation holds folder-wide.** The permission pipeline (`orders/sets.py`) fires `_run_permission_checks` BEFORE any queryset mutation in both sync and async apply paths; the duck-typed `_active_permission_targets` contract the shared `utils/permissions.py::run_active_input_permission_checks` calls is defined on `OrderSet` (and symmetrically on `FilterSet`), so the shared core never `AttributeError`s regardless of which family drives it. The `79b74b46` perm consolidation + the `verbatim_path` follow-up are both verified behavior-preserving by the file-level cycles.
- **GLOSSARY accurate across the folder.** `OrderSet`, `Ordering`, `RelatedOrder`, `Meta.orderset_class` entries all match the implementation (six-member enum with True-or-None NULLS sentinels; three RelatedOrder target shapes; active-input-only + active-branch double-dispatch). No internal helper names are documented, so the prior-cycle renames (`_iter_active_related_branches` → `_active_permission_targets`, `_verbatim_attr` → `verbatim_path`) create no GLOSSARY drift. The only standing-doc inaccuracy in scope is the TREE/test-docstring stale-coverage claim flagged as the act-now Low.

### Summary

The `orders/` folder is in good shape: a uniform, well-factored thin-delegation family (`base` over the related mixin, `factories` over the generated-input factory, `inputs` over the input-values traversal substrate, `sets` over the permissions core, `__init__` over the lazy-input-annotation helper), every cross-folder edge fanning one-way outward to the shared core with no cycle, and a 5-name `__all__` that is correctly symmetric with the filter package's export decisions. All four file siblings are `verified`; the `verbatim_path` consolidation is folder-clean (the orders-side duplicate is gone, grep-verified). No High, no Medium. One act-now Low: the stale "dynamic OrderSet caching" coverage claim copied from the filter side into `tests/orders/test_factories.py:1` and `docs/TREE.md:376` + `:515` promises Layer-6 test coverage the order side does not ship (zero dynamic-cache tests, no shipped cache) — a verbatim three-location phrase trim warranted now at folder scope, driving `Status: under-review`. The two cross-folder DRY observations (family-wrapper layer, `normalize_input_value` same-name-different-abstraction pair) are forwarded to the project pass, not merged.

---

## Fix report (Worker 2)

Consolidated single-spawn (doc-only fix, shape #4 — test docstring + standing-doc TREE.md, analogous to a GLOSSARY-only fix). Logic + comment + changelog disposition recorded together; bare `Status: fix-implemented`.

### Files touched
- `tests/orders/test_factories.py:1` — module-docstring first line: dropped the stale `" and dynamic OrderSet caching"` clause. The order side ships no Layer-6 dynamic OrderSet cache (`_dynamic_orderset_cache` / `get_orderset_class` are a standing deferred non-goal) and the file has zero dynamic-cache tests, so the claim is a copy-from-filter-side artifact.
- `docs/TREE.md:376` and `docs/TREE.md:515` — two byte-identical tree-entry comments for `test_factories.py`: dropped the same `" and dynamic OrderSet caching"` clause via `replace_all` (grep confirmed exactly the two intended occurrences, no other legitimate occurrence in TREE.md).

### Tests added or updated
- None. Doc-accuracy fix only — no source logic, no behavior change, no new contract. Test body's second docstring sentence already enumerates the real coverage (BFS walk / collision / idempotency / subclass rejection / leaf+related annotation) and needed no edit.

### Validation run
- `uv run ruff format .` — pass (270 files left unchanged).
- `uv run ruff check --fix .` — pass (All checks passed!; pre-existing COM812/formatter advisory only).
- No pytest (doc-only; per AGENTS.md #14 and dispatch).

### Notes for Worker 3
- No shadow file used (pure prose trim).
- Repo-wide grep `grep -rn "dynamic OrderSet caching" .` excluding `docs/review` + `docs/shadow` returns **zero** hits after the edit — no other stale claim of this kind remains in any standing doc or source.
- Cycle diff is exactly the three trims: `git diff HEAD -- tests/orders/test_factories.py docs/TREE.md` shows one line in the test docstring and the two byte-identical TREE.md lines.
- `uv.lock` not modified by the `uv run` invocations (clean in `git status`). Other dirty/untracked files in the tree are prior-cycle and concurrent review work, out of scope for this cycle.

---

## Comment/docstring pass

Doc trims (consolidated). Old → new for each location:

### Files touched
- `tests/orders/test_factories.py:1`
  - old: `"""OrderArgumentsFactory tests for BFS input generation and dynamic OrderSet caching.`
  - new: `"""OrderArgumentsFactory tests for BFS input generation.`
- `docs/TREE.md:376` (identical to `:515`)
  - old: `│   ├── test_factories.py         # OrderArgumentsFactory tests for BFS input generation and dynamic OrderSet caching.`
  - new: `│   ├── test_factories.py         # OrderArgumentsFactory tests for BFS input generation.`
- `docs/TREE.md:515` — same old → new as `:376` (byte-identical line; `replace_all` covered both).

### Per-finding dispositions
- Low (stale "dynamic OrderSet caching" coverage claim): **edited** — trimmed at all three locations per the artifact's verbatim recommendation. No source-logic change.

### Validation run
- `uv run ruff format .` — pass.
- `uv run ruff check --fix .` — pass.

### Notes for Worker 3
TREE.md uses plain-prose tree comments here (not inline cross-file links); the trims touch no reference-style link defs and introduce no inline links. Convention intact.

---

## Changelog disposition

### State
`Not warranted`.

### Reason
Internal doc-accuracy fix (test docstring + standing-doc TREE.md), no consumer-visible behavior, no public-API or typed-error change. Cites BOTH: AGENTS.md #21 ("Do not update CHANGELOG.md unless explicitly instructed") AND the active plan's silence on changelog authorization for this cycle (folder pass is never the authorising scope; CHANGELOG drift, if any, forwards to the project pass).

### What was done
No `CHANGELOG.md` edit. `git diff HEAD -- CHANGELOG.md` empty.

### Validation run
- `uv run ruff format .` — pass.
- `uv run ruff check --fix .` — pass.

---

## Verification (Worker 3)

Consolidated single-spawn doc-only fix (shape #4): single terminal verify, bare `Status: fix-implemented` incoming.

### Logic verification outcome
No source-logic or test-logic findings — this cycle's only finding was the act-now Low (stale "dynamic OrderSet caching" coverage claim). Verified addressed:

- **Diff is exactly the three prose trims, no logic change.** `git diff HEAD -- tests/orders/test_factories.py docs/TREE.md` shows: (a) the `test_factories.py` module-docstring first line only (`-"""…BFS input generation and dynamic OrderSet caching."` → `+"""…BFS input generation."`), and (b) the two byte-identical TREE.md tree-entry comments (`:376`, `:515`). The test file change is its module docstring only — the test body (imports, all 10 `def test_*`, fixtures) is untouched. `git diff HEAD -- CHANGELOG.md` empty.
- **Trimmed text now ACCURATELY describes the file.** The order test file genuinely has no dynamic-cache coverage: all 10 test functions are BFS / cycle-via-seen-set / leaf-ordering-annotation / related-branch lazy-forward-ref / classname-collision / idempotency / shared-input-across-instances / subclass-rejection / none-target-skip / double-enqueue-dedupe (`test_factory_visits_every_reachable_relatedorder_target_via_bfs` … `test_factory_dedupes_double_enqueued_target_via_seen_check`). `grep -nE "dynamic|_make_cache|get_orderset_class|_dynamic_orderset_cache"` in the test file returns zero hits after the trim. The retained second docstring sentence already enumerates the real coverage and needed no edit.
- **Removing the claim is correct, NOT hiding a real feature.** The order side ships no Layer-6 dynamic OrderSet cache. `grep -rnE "_dynamic_orderset_cache|def get_orderset_class|_make_cache" django_strawberry_framework/orders/` returns only two hits, both in `factories.py`: the module docstring (`factories.py #"are NOT shipped"`, spec-028 Decision 12) and the bottom `# TODO(spec-028-orders-0_0_8 Decision 12; standing deferred non-goal)` comment block listing `_dynamic_orderset_cache` / `get_orderset_class` as forward-reserved symbols with no shipped consumer. No live definition exists. The claim was a copy-from-filter-side artifact (the filter twin genuinely ships Layer 6); trimming restores doc-source truth.
- **Repo-wide grep clean.** `grep -rn "dynamic OrderSet caching" .` excluding `docs/review` + `docs/shadow` returns ZERO hits — no other stale claim of this kind remains in any standing doc or source.

### Folder-pass findings soundness
- **`verbatim_path` no-duplicate.** Re-ran `grep -rnE '_verbatim_attr|_verbatim_path|verbatim_path' django_strawberry_framework/ tests/` = exactly 5 hits, all the consolidated public `utils/permissions.py::verbatim_path` (def `:149`, `__all__` `:70`, internal call site `:249`) plus the order side's import (`orders/sets.py:47`) and use (`orders/sets.py:362`). Zero `_verbatim_attr` orphans. Folder-clean, matching the prior-cycle (`rev-orders__sets.md`) consolidation I accepted.
- **Import DAG, `__init__` surface, cross-folder DRY forwards.** Independently verified in my four accepted file-sibling cycles (`rev-orders__base.md` / `__factories.md` / `__inputs.md` / `__sets.md`, all `Status: verified`, all `[x]` at review-0_0_10.md:102-105): one-way intra-folder DAG (`base ← inputs ← sets/factories ← __init__`, the `inputs↔sets` edge `TYPE_CHECKING`-only, every cross-folder edge fanning outward to the shared core with no back-edge), the 5-name `__all__`, and the two cross-folder DRY observations (family-wrapper layer; `normalize_input_value` same-name-different-abstraction pair) correctly forwarded to the project pass rather than force-merged. No new evidence contradicts any of these at folder scope.

### DRY findings disposition
Two cross-folder observations forwarded to `rev-django_strawberry_framework.md` (project pass) — sound: both span filters+orders+utils and cannot be resolved at folder scope. The "no NEW orders-side `verbatim_path` duplicate" item is grep-confirmed above. No folder-local DRY action warranted.

### Temp test verification
None used — pure prose trim, no behavior to pin. No pytest run (doc-only; AGENTS.md #14 and dispatch).

### Changelog verification
State `Not warranted`. `git diff HEAD -- CHANGELOG.md` empty (confirmed). Cites BOTH AGENTS.md #21 ("Do not update CHANGELOG.md unless explicitly instructed") AND the active plan's silence on changelog authorization for this folder-pass cycle. Internal-only framing honest: the cycle changed only a test docstring + standing-doc TREE.md, no public-API surface — "Not warranted" is the correct state (not "deferred to maintainer"). Justified.

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the `orders/` folder-pass checklist box at `docs/review/review-0_0_10.md:106`.

---

## Iteration log

(none)
