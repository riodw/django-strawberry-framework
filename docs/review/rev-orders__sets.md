# Review: `django_strawberry_framework/orders/sets.py`

Status: verified

## DRY analysis

- **Cross-folder filter/order permission-wrapper layer (forward to project pass; do NOT merge locally).** The thin permission delegates on `OrderSet` — `_request_from_info` (`orders/sets.py::OrderSet._request_from_info`), `_extract_branch_value` (`OrderSet._extract_branch_value`), `_active_permission_field_paths` (`OrderSet._active_permission_field_paths`), `_active_permission_targets` (`OrderSet._active_permission_targets`), `_invoke_permission_method` (`OrderSet._invoke_permission_method`), `_run_permission_checks` (`OrderSet._run_permission_checks`) — are the symmetric twins of `FilterSet`'s same-named methods, each already a one-line delegate into the single-sited `utils/permissions.py` mechanics. The only per-family residue is the family-label string (`"OrderSet"` vs `"FilterSet"`), the `related_attr`/`target_attr` tokens (`"related_orders"`/`"orderset"` vs `"related_filters"`/`"filterset"`), and `logic_keys` (`frozenset()` vs the filter operator bag). Consolidating the wrapper *layer itself* (e.g. a shared `PermissionDelegateMixin` parameterized by a small config object) spans two folders and would have to preserve each family's public method names (the documented consumer-facing surface). Defer until the project-level pass (`docs/review/rev-django_strawberry_framework.md`) triages the whole filter+order+utils family-wrapper set together; the per-folder passes correctly left this cross-folder.

The prior cycle's second DRY bullet (`_verbatim_attr` byte-identical twin of `utils/permissions.py::verbatim_path`) is **resolved in HEAD** and is the reason this cycle's diff is empty: `orders/sets.py` no longer defines a local fallback — it imports the now-public `verbatim_path` from `..utils.permissions` (in that module's `__all__`) at line 47 and passes it as `fallback_path` at line 362. Recap only, not a candidate; see `### DRY recap`.

## High:

None.

## Medium:

None.

## Low:

None.

## What looks solid

### DRY recap

- **Existing patterns reused.** Every behavior of substance is a thin delegate to a single-sited shared primitive: declaration collection via `..sets_mixins.collect_related_declarations` (`OrderSetMetaclass.__new__`); the expansion-cache + reentry-guard via `..sets_mixins.expanded_once` keyed off the `SetLifecycleAttrs` descriptor `OrderSet._lifecycle` (shared shape with `FilterSet.get_filters`); the full permission core via `..utils.permissions` (`request_from_info`, `extract_branch_value`, `active_permission_targets`, `invoke_permission_method`, `run_active_input_permission_checks`, `verbatim_path`); input normalization via `.inputs.normalize_input_value`; to-many detection via `..utils.relations.relation_kind` / `is_many_side_relation_kind`; `Ordering.resolve` for `OrderBy` construction. `_lifecycle` is the single source for the slot names both `get_fields` and `registry.clear()` reference.
- **New helpers considered.** The permission-wrapper-layer mixin (see `## DRY analysis`) — rejected at file/folder scope because it is cross-folder and must preserve per-family public method names; forwarded to the project pass. No file-local helper is warranted: every method body is already one delegating call. The `_verbatim_attr` local fallback was eliminated in the prior cycle by promoting `verbatim_path` into `utils/permissions.__all__`, so the orders→utils dedupe is already paid.
- **Duplication risk in the current file.** The only repeated literal is `"related_orders"` (overview: 4x — the metaclass `collection_attr`, the `_active_permission_targets` `related_attr`, and the `get_fields` `__dict__`/`getattr` reads). It is the family attribute-name token, passed/read against distinct objects (collector config, permission-targets config, the class itself); the intentional sibling-design counterpart of `FilterSet`'s `"related_filters"`. Hoisting it to a constant would not reduce drift because the two families must differ here by design. `apply_sync` / `apply_async` share a near-identical tail (`_normalize_input` → early return → `get_flat_orders` → `_resolve_order_expressions` → early return → conditional `annotate` → `order_by`); the sole divergence is the permission-check wrapping (direct call vs `sync_to_async(thread_sensitive=True)`), the canonical sync/async-split shape the filter side uses too — folding it would force a flag-threaded shared body and lose the clean two-entry-point surface.

### Other positives

- **Permission gate is fail-closed and pre-mutation, both paths.** `apply_sync` and `apply_async` resolve the request, then run `_run_permission_checks` BEFORE any `order_by`/`annotate` touches the queryset (spec-028 Decision 8 step 6). The async path wraps only the permission checks (potential blocking ORM reads in consumer `check_*` hooks) in `sync_to_async(thread_sensitive=True)`, correctly leaving the pure-Python parsing and the non-I/O `order_by` call unwrapped — identical step sequence to the sync path.
- **To-many ordering avoids the row-multiplication trap.** `_resolve_order_expressions` routes any path that traverses a to-many relation (`_path_traverses_to_many`, via `relation_kind`/`is_many_side_relation_kind`) through `.annotate(<alias>=Min/Max(path))` (`Min` for ASC, `Max` for DESC) rather than a raw fan-out `order_by("rel__col")`, so the parent GROUP-BY keeps one row per parent and the connection's positional cursors and `totalCount` stay correct (`docs/feedback.md` P1-B). NULLS positioning carries onto the aggregate alias through the same `Ordering.resolve`; scalar / to-one paths order directly.
- **`_path_traverses_to_many` caching is bounded and side-effect-free.** `@lru_cache(maxsize=2048)` over a pure `(model, field_path)` metadata walk; the bound caps dynamic-test-model / generated-path growth and eviction only recomputes identical metadata. The walk fails safe (`False`) at the first non-relation segment, an unresolvable segment (`FieldDoesNotExist`), or a `related_model` of `None`.
- **`get_fields` cache-write gate is MRO-safe.** Reads `cls.__dict__.get("_expanded_fields")` directly (not `getattr`) so a subclass never inherits a parent's completed cache, and writes only when `related_orders` is on this class's own `__dict__` AND no `_orderset` is still an unresolved string forward-reference — the exact two-condition gate `FilterSet.get_filters` uses.
- **`Meta.fields = "__all__"` raises a clear `ConfigurationError`** naming the class when `Meta.model` is absent, before the column walk. The `_get_concrete_field_names_for_order` import is local to dodge the `orders/sets.py` ↔ `orders/inputs.py` runtime cycle.
- **GLOSSARY contract accurate.** `#orderset` (GLOSSARY.md:965-973) mirrors the shipped surface verbatim — Meta.model/fields list+`"__all__"` (forward FK/O2O columns included, reverse + M2M excluded), `RelatedOrder`, active-input-only `check_*_permission` with active-branch double-dispatch deduped per `(OrderSet class, method name)`, list-shaped tie-breaker, six-member `Ordering`, the Layer-6 deferred non-goal, and the `apply_sync`/`apply_async` pair. `#ordering` (961), `#metaorderset_class` (849-859), `#relatedorder` (1057-1061) all consistent with the source. No drift. Private `_`-prefixed helpers carry no GLOSSARY entry (absence correct).

### Summary

Genuine no-source-edit (shape #5) cycle: both `git diff 964d6d5c -- orders/sets.py` and `git diff HEAD -- orders/sets.py` are empty (last touching commit `8d6ca99b`, cumulative-in-HEAD). The file is the order-side apply-pipeline + declaration/validation surface, and it is a model of delegation — every behavior of substance funnels into a single-sited shared primitive in `sets_mixins`, `utils/permissions`, `utils/relations`, or `.inputs`, with the to-many aggregate guard and the fail-closed pre-mutation permission gate (both correct, both sync/async-parity) as the only genuinely order-local logic. The prior cycle's `_verbatim_attr` DRY item is resolved in HEAD (`verbatim_path` promoted to `utils/permissions.__all__` and imported here), which is precisely why this cycle's diff is clean. The single remaining DRY opportunity — the cross-folder filter/order permission-wrapper layer — stays forwarded to the project pass. No High/Medium/Low findings; GLOSSARY contract accurate.

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
None — no-source-edit cycle.

### Tests added or updated
None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass; "289 files left unchanged".
- `uv run ruff check --fix .` — pass; "All checks passed!" (only the pre-existing COM812-vs-formatter config notice).

### Notes for Worker 3
- Both `git diff 964d6d5ca39691467275f86c52dd7e3b64bca49f -- orders/sets.py` and `git diff HEAD -- orders/sets.py` are empty; the file is unchanged this cycle (last touching commit `8d6ca99b`).
- Low: none. No High, no Medium.
- The single DRY-analysis bullet (cross-folder filter/order permission-wrapper layer) is forward-deferred to the project pass (`rev-django_strawberry_framework.md`), not a local edit.
- Prior-cycle `_verbatim_attr` DRY item is already resolved in HEAD: `verbatim_path` is public in `utils/permissions.__all__`, imported at `orders/sets.py` line 47, used as `fallback_path` at line 362. No action.
- No GLOSSARY-only fix in scope — `#orderset`/`#ordering`/`#metaorderset_class`/`#relatedorder` prose verified accurate against current source.

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern. No source edits; comments/docstrings are accurate — the cookbook-port lineage, spec-028 Decision references, and the to-many `docs/feedback.md` P1-B citation all verified (`docs/feedback.md` present on disk). No changes.

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern. Not warranted — no source change this cycle (review-only). Cites AGENTS.md ("Do not update CHANGELOG.md unless explicitly instructed") and the active plan (`docs/review/review-0_0_11.md`) being silent on changelog edits for review cycles.

---

## Verification (Worker 3)

### Logic verification outcome
No High / Medium / Low findings to dispatch — genuine shape-#5 no-source-edit cycle. Independently confirmed the artifact's substantive claims against live source:

- **Zero-edit proof.** `git diff 964d6d5ca39691467275f86c52dd7e3b64bca49f -- django_strawberry_framework/orders/sets.py` empty; `git diff HEAD -- …` empty; owned-paths `git diff --stat 964d6d5c -- django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md` empty (no sibling attribution needed); last touching commit `8d6ca99b` (cumulative-in-HEAD, not this cycle).
- **`verbatim_path` import + no local twin.** `grep -rn "_verbatim_attr" django_strawberry_framework/` returns zero — no local fallback twin remains. `verbatim_path` is public in `utils/permissions.py::__all__` (`#"verbatim_path"`), imported at `orders/sets.py` (`#"    verbatim_path,"` in the `..utils.permissions` block) and passed as `fallback_path=verbatim_path` inside `OrderSet._active_permission_targets`. DRY recap "orders→utils dedupe already paid" confirmed.
- **Metaclass collection.** `OrderSetMetaclass.__new__` delegates to `collect_related_declarations(..., declaration_type=RelatedOrder, collection_attr="related_orders", inherit_from_bases=True)` — single-sited shared collector; no per-family logic beyond the config tokens.
- **Meta validation.** `_expand_meta_fields` raises `ConfigurationError` naming `cls.__name__` for `fields="__all__"` without `Meta.model`, before the column walk; `_get_concrete_field_names_for_order` import is function-local to break the `orders/sets.py` ↔ `orders/inputs.py` runtime cycle.
- **Sync vs async parity.** `apply_sync` runs `_run_permission_checks` BEFORE `order_by`/`annotate`; `apply_async` wraps only `_run_permission_checks` in `sync_to_async(thread_sensitive=True)`, leaving pure-Python parse + `order_by` unwrapped. No `apply(...)` dispatcher (`grep "def apply"` → only `apply_sync` / `apply_async`), matching Spec DoD 4(c).
- **Per-field permission scope + active-branch dispatch.** `_active_permission_targets` config: `related_attr="related_orders"`, `logic_keys=frozenset()` (no operator bag), `handle_top_level_list=True`, `fallback_path=verbatim_path`; `_run_permission_checks` passes `target_attr="orderset"` (filter twin uses `"filterset"`). All six wrapper methods are byte-symmetric one-line delegates to `utils/permissions.py`, and the six same-named filter twins exist at `filters/sets.py` (`_request_from_info`/`_extract_branch_value`/`_active_permission_field_paths`/`_active_permission_targets`/`_invoke_permission_method`/`_run_permission_checks`) — sibling-design symmetry, not drift.
- **To-many aggregate guard.** `_resolve_order_expressions` routes `_path_traverses_to_many` paths through `.annotate(<alias>=Min/Max(path))` (`Min` for ASC, `Max` for DESC) — row-preserving; scalar / to-one paths order directly. `@lru_cache(maxsize=2048)` over pure `(model, field_path)` metadata, fail-safe `False` at non-relation / `FieldDoesNotExist` / `related_model is None`.

### DRY findings disposition
Single DRY-analysis bullet — the cross-folder filter/order permission-wrapper layer — correctly forwarded to the project pass (`rev-django_strawberry_framework.md`), NOT a local fix: consolidating spans two folders and must preserve each family's documented public method names. The prior cycle's second DRY bullet (`_verbatim_attr` byte-identical twin) is resolved in HEAD (promotion of `verbatim_path` to `utils/permissions.__all__`) — confirmed by the zero `_verbatim_attr` grep and the live import. No GLOSSARY-only fix in scope (would be disqualifying for a #5).

### GLOSSARY / #5-vs-#4 gate
`#orderset` (GLOSSARY.md `## OrderSet`), `#metaorderset_class` (`## Meta.orderset_class`), `#relatedorder` (`## RelatedOrder`), and `#ordering` (`## Ordering`) all accurate vs live source — Meta.model/fields list+`"__all__"` (forward FK/O2O included, reverse + M2M excluded), active-input-only `check_*_permission` with active-branch double-dispatch deduped per `(OrderSet class, method name)`, list-shaped tie-breaker, six-member `Ordering`, Layer-6 deferred non-goal. Private `_`-prefixed helpers correctly carry no entry. Genuine #5, not a missed #4.

### Temp test verification
None — no temp tests created. Existing suite `tests/orders/test_sets.py` (733 lines) present; not re-run preemptively (no source change, no test introduced this cycle, per worker-3.md).

### Changelog disposition
"Not warranted" — `git diff -- CHANGELOG.md` empty; cites BOTH AGENTS.md ("Do not update CHANGELOG.md unless explicitly instructed") AND the active plan's silence. Internal-only framing matches the (empty) diff scope. Accepted.

### Validation
`uv run ruff format --check django_strawberry_framework/orders/sets.py` → "1 file already formatted"; `uv run ruff check …` → "All checks passed!" (only the pre-existing COM812-vs-formatter notice).

### Verification outcome
cycle accepted; verified — sets top-level `Status: verified` AND marks the `orders/sets.py` checklist box in `docs/review/review-0_0_11.md`.
