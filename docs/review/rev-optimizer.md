# Review: `django_strawberry_framework/optimizer/` (folder pass)

Status: verified

## DRY analysis

- **Forward to project pass (`rev-django_strawberry_framework.md`): act-now cross-folder shared builder `FieldMeta._from_field_shape(field, *, is_relation)` collapsing the eleven-line per-attribute mirror.** `optimizer/field_meta.py::FieldMeta.from_django_field` (`field_meta.py:130-172`) and `types/resolvers.py::_field_meta_for_resolver`'s `not hasattr(field, "is_relation")` branch (`types/resolvers.py:182-212`) carry a line-for-line identical body (same `is_m2m` / `is_o2m` reads, same `target_field` cache, same many-side `nullable` short-circuit, same `relation_kind(field) == "reverse_one_to_one"` clause, same nine-attribute `FieldMeta(...)` call). `rev-optimizer__field_meta.md`'s DRY bullet flagged this as act-now and explicitly noted the duplicate's own docstring at `types/resolvers.py:182-189` names the mirror as load-bearing — which is exactly the brittleness signal a DRY consolidation should resolve. The walker-side `_resolve_field_map`'s `else {f.name: f for f in model._meta.get_fields()}` fallback (`walker.py:117`) is the OTHER half of the same dual-contract surface but it materialises a `dict[str, raw_field]` rather than a `dict[str, FieldMeta]` and the divergence is intentional per the walker docstring at `walker.py:101-110`. **This is a cross-folder concern (optimizer ↔ types) and the per-file artifact correctly forwarded it; the folder pass cannot land the helper because its second site lives in `types/`.** Forwarded to the project pass for the act-now decision after `rev-types__resolvers.md` and `rev-types__finalizer.md` close, since the consolidation must observe both folders simultaneously. Suggested signature carried forward verbatim from `rev-optimizer__field_meta.md` DRY bullet 1: `FieldMeta._from_field_shape(field: Any, *, is_relation: bool) -> FieldMeta` with `from_django_field` becoming a 3-line guard-and-delegate, and `_field_meta_for_resolver`'s fallback collapsing to `return FieldMeta._from_field_shape(field, is_relation=True)`.

- **Defer-with-trigger: shared `_evict_oldest_quarter(cache, max_size)` helper for FIFO-like bounded `dict` cache eviction under `optimizer/`.** `optimizer/extension.py::DjangoOptimizerExtension._optimize` (`extension.py:650-658`) carries an inline FIFO eviction policy (`pop(next(iter(cache)))` with a `_MAX_PLAN_CACHE_SIZE // 4` batch) that is the only such eviction site in the subpackage today. `rev-optimizer__extension.md` DRY bullet 3 deferred this with the explicit trigger "a second `dict`-backed bounded cache under `optimizer/` with the same eviction shape." Restated at folder scope so a future second-cache cycle (e.g., the per-execution AST cache at `extension.py::_per_execution_ast_cache` if it ever gains an eviction policy, or a future field-meta cache) re-triggers the consolidation review. No act-now folding at folder scope — single in-subpackage site does not justify a helper.

- **Defer-with-trigger: shared higher-order selection-tree walker `_walk_ast(node, fragments, visited, on_node, on_fragment_def)`.** `optimizer/extension.py::_walk_directives` (`extension.py:92-128`) and `optimizer/extension.py::_walk_reachable_fragment_definitions` (`extension.py:199-227`) already share `_child_selections` and `_unvisited_fragment_definition`; the only divergent step is "collect this node's directives" vs. "append this fragment-def to the reachable list." Per `rev-optimizer__extension.md` DRY bullet 1 the consolidation is deferred until "a third selection-tree walker lands (the walker module is currently the next candidate via a future 'schema audit selection-aware mode')." Restated at folder scope because `walker.py::_walk_selections` is structurally similar — it walks selection sets recursively too, but with a different cycle-guard shape and different concerns; the three-walker trigger phrasing remains correct. Trigger: any third place under `optimizer/` (or a cross-folder cousin) that needs cycle-guarded recursive selection-set + fragment-spread descent.

- **Defer-with-trigger: shared `freeze_sentinel(cls, name, **kwargs)` helper or `@with_sentinels` decorator for the `dataclass(frozen=True)` + `ClassVar` + post-class-body rebind pattern.** `optimizer/hints.py:71` + `hints.py:157` is the only site in `optimizer/` (the `OptimizerHint.SKIP` sentinel installation). Per `rev-optimizer__hints.md` DRY bullet 2 the consolidation is deferred until "the SKIP sentinel pattern reappears for a second `dataclass(frozen=True)` in the package." Restated at folder scope so a future second-frozen-dataclass cycle anywhere in the optimizer subpackage (e.g., an aggregates/orders typed-wrapper) re-triggers the helper extraction.

- **Defer-with-trigger: cross-folder `_strawberry_schema_of(obj, default=None)` helper consolidating the two `_strawberry_schema_from_*` shapes.** Per `rev-optimizer__extension.md` DRY bullet 2: `extension.py::_strawberry_schema_from_schema` (`extension.py:299-306`) and `extension.py::_strawberry_schema_from_info` (`extension.py:309-316`) read the same private attribute through two access shapes; the two helpers correctly avoid sharing today because the schema fallback differs (`return schema` vs. `return None`). Restated at folder scope so a third `_strawberry_schema` reach site under `optimizer/` (or any new consumer of the private attribute) re-triggers the consolidation review. Trigger: a third Strawberry-schema reach site under `optimizer/` or any new consumer of the `_strawberry_schema` private attribute.

## High:

None.

## Medium:

None.

## Low:

### Forward to project pass: cross-folder DRY act-now opportunity for `FieldMeta._from_field_shape`

Restated above in `## DRY analysis` as the first bullet. The folder pass cannot land the act-now extraction because the second call site (`types/resolvers.py::_field_meta_for_resolver`) lives outside `optimizer/`; the project pass owns the decision after `rev-types__resolvers.md` closes. Recording it here in `## Low:` because the folder-level audit otherwise reads as if no real DRY work is in flight, which would be inaccurate — the cross-folder mirror is the most substantive optimizer-touching DRY finding in the cycle to date, and the project pass needs to inherit the act-now framing rather than re-triage it. No in-cycle source edit at the folder layer.

### Forward to project pass: GLOSSARY coverage gap for the `DST_OPTIMIZER_*` key string LITERALS

`rev-optimizer___context.md` Low #2 forwarded a GLOSSARY drift on four of the five `DST_OPTIMIZER_*` key strings — `dst_optimizer_planned`, `dst_optimizer_lookup_paths`, `dst_optimizer_strictness` (plus the two already named in adjacent entries `FK-id elision` and the `Strictness mode` paragraph). The single source of truth lives at `_context.py:34-38` and is imported by name at both `optimizer/extension.py:48-52` (write side, five sites) and `types/resolvers.py:36-38` (read side, three sites); folder-wide grep for `"dst_optimizer*"` returns ONLY the five constant assignments at `_context.py:34-38` (audit confirmed clean — no raw-string regression anywhere in `optimizer/` or `types/`). The five literals ARE consumer-introspectable surface during a strictness incident (the use-case the `Strictness mode` entry advertises), but the names are not currently documented as consumer-facing API. Forwarded to project pass per the joint-cut deferral pattern recorded in `rev-optimizer___context.md`: deferred until either (a) the `_context` module loses its underscore prefix and the read helper becomes public consumer API, OR (b) a sixth `dst_optimizer_*` key lands. Folder pass adds nothing new — the per-file artifact's framing is correct.

### Forward to project pass: GLOSSARY coverage gap for `FieldMeta`

`rev-optimizer__field_meta.md` Low #2 forwarded a GLOSSARY entry gap for `FieldMeta` despite its cross-module public-import surface (`types/base.py:39`, `types/definition.py:10`, `types/converters.py:49`, `types/resolvers.py:43`, `types/finalizer.py:54`). The only GLOSSARY trace today is `docs/GLOSSARY.md:825` (Plan-cache tail bullet). Joint-cut deferral with the `DST_OPTIMIZER_*` literals above per `rev-optimizer___context.md`'s framing — internal-but-cross-module-visible optimizer symbols are best authored together at the project layer alongside their first cohort of consumer documentation. Folder pass adds nothing new.

### Forward to project pass: GLOSSARY coverage confirmation for `OptimizationPlan` / `plan_optimizations` / `plan_relation` / `diff_plan_for_queryset` etc. is correctly absent

`rev-optimizer__plans.md` "Other positives" and `rev-optimizer__walker.md` Low #10 both confirmed that the optimizer's internal mechanics (`OptimizationPlan`, `diff_plan_for_queryset`, `resolver_key`, `runtime_path_from_info`, `runtime_path_from_path`, `lookup_paths`, the `append_*` helpers, the `_consumer_*` helpers, `plan_optimizations`, `plan_relation`) are CORRECTLY absent from GLOSSARY per `optimizer/__init__.py:14-17` ("internal implementation details consumed by `extension.py` and tests, not consumer-facing API"). The consumer-facing surface for the optimizer is exactly `DjangoOptimizerExtension`, `OptimizerHint` + factories, `Meta.optimizer_hints`, `Plan cache`, `FK-id elision`, `only() projection`, `Schema audit`, `Strictness mode`, `Queryset diffing` — all of which have current GLOSSARY entries (drift items already filed and closed under `rev-optimizer__extension.md`, `rev-optimizer__hints.md`, `rev-optimizer__plans.md`). Forwarded here as a positive audit-trail forward, NOT a finding — the project pass owes a one-bullet confirmation in its `## What looks solid` that the optimizer subpackage's `__all__` discipline and GLOSSARY-coverage alignment is correct rather than re-triaging the absences as gaps.

## What looks solid

### DRY recap

- **Existing patterns reused at folder scope.** The five `DST_OPTIMIZER_*` key string literals live at exactly one site (`_context.py:34-38`) and are consumed by name across `extension.py:48-52` (5 imports) and the cross-folder `types/resolvers.py:36-38` (3 imports); folder-wide grep `grep -rn '"dst_optimizer' django_strawberry_framework/optimizer/` returns ONLY the five constant assignments — zero raw-string regression. `hint_is_skip` (imported from `.hints`) is the single dispatch helper consumed by both `walker.py::_apply_hint` (`walker.py:433`) and `extension.py::check_schema` (`extension.py:721`) — no open-coded `hint is OptimizerHint.SKIP or hint.skip` regressions in the subpackage. `OptimizationPlan.finalize()` is invoked exactly once (`walker.py:58` in `plan_optimizations`) — the documented immutability handoff is single-site. The framework-wide `logger` is re-exported from `optimizer/__init__.py:26` and consumed via `from . import logger` at `extension.py:46` and `walker.py:16` — no `getLogger(__name__)` regressions inside the subpackage. `plans.py`'s `append_unique` / `append_unique_many` / `append_prefetch_unique` / `resolver_key` / `runtime_path_from_info` are the single source of truth for plan mutations; the walker routes every plan mutation through these helpers and never open-codes a dedupe (audit per `rev-optimizer__walker.md` carry-forward — confirmed clean). The optimizer subpackage's intra-folder imports form a strict DAG (`__init__.py` → `extension.py` → {`_context.py`, `hints.py`, `plans.py`, `walker.py`}; `walker.py` → {`hints.py`, `plans.py`}; `hints.py` → {}; `field_meta.py` → {}; `plans.py` → {}; `_context.py` → {}) with no circular-import risk and no two-way dependency.

- **New helpers considered at folder scope (and rejected/deferred).** A folder-level `_walk_selection_tree(on_node, on_fragment_def)` higher-order helper consolidating `extension.py::_walk_directives` + `extension.py::_walk_reachable_fragment_definitions` was evaluated and deferred per `rev-optimizer__extension.md` DRY bullet 1's third-walker trigger. A folder-level `_evict_oldest_quarter(cache, max_size)` helper was evaluated and deferred per `rev-optimizer__extension.md` DRY bullet 3's second-cache trigger. A folder-level `_dispatch_select_or_prefetch(force_kind=...)` consolidator collapsing the three near-identical 9-arg `_plan_*_relation(...)` call tuples in `walker.py::_apply_hint` was evaluated and deferred per `rev-optimizer__walker.md` DRY bullet 1's sixth-call-tuple trigger. A folder-level `hint_kind(hint) -> Literal[...]` classifier was evaluated and deferred per `rev-optimizer__hints.md` DRY bullet 1's third-call-site trigger. None act-now at folder scope because each per-file deferral cited the same load-bearing-distinction rationale (priority-order comment visibility at `walker.py:429-431`; read-vs-write symmetry at `_context.py:48-49`; per-conflict UX message text at `hints.py:86-104`). The folder pass has nothing to add to the per-file evaluation.

- **Duplication risk at folder scope.** Folder-pass repeated-string-literal check across all seven sibling shadow overviews (regenerated `_context.py` + `__init__.py` overviews at folder-pass time so the seven-file sweep is current): per-file repeated literals are intra-file only — `extension.py` has `2x "_strawberry_schema"` (both inside `_strawberry_schema_from_schema` / `_strawberry_schema_from_info`, already evaluated by `rev-optimizer__extension.md` DRY bullet 2), `plans.py` has `2x "prefetch_to"` and `2x "queryset"` (both inside the `_lookup_path` / `_diff_prefetch_related` consolidation point that `rev-optimizer__plans.md` evaluated), `walker.py` has `3x "prefetch"`, `3x "selections"`, `2x "related_model"`, `2x "target_field"`, `2x "directives"`, `2x "arguments"` (intra-file dispatch literals reused inside the walker hotspots). Cross-file grep confirms only THREE candidate strings appear in more than one optimizer file: `"target_field"` and `"related_model"` (both in `field_meta.py` and `walker.py`) and `"is_relation"` (in `field_meta.py` only, where the walker reads it through `FieldMeta.is_relation` rather than the raw attribute). The two genuine two-file duplications (`"target_field"`, `"related_model"`) ARE the same `FieldMeta._from_field_shape` cross-folder DRY footprint already forwarded to the project pass via DRY bullet 1 and Low #1 above — the act-now extraction subsumes both literals. No additional folder-level duplication finding.

### Other positives

- **Public-API discipline.** `optimizer/__init__.py:29` exports exactly two symbols (`DjangoOptimizerExtension`, `logger`); both are intentional consumer-facing surfaces and the docstring at `optimizer/__init__.py:14-17` records the explicit decision to NOT re-export `OptimizationPlan` / `plan_optimizations` / `plan_relation` ("internal implementation details consumed by `extension.py` and tests, not consumer-facing API"). This single sentence is the load-bearing audit trail that gates every "should this internal symbol get a GLOSSARY entry?" question in the per-file artifacts (cited verbatim in `rev-optimizer__plans.md`, `rev-optimizer__walker.md`, and forwarded again above as a project-pass confirmation). The re-export contract for `logger` is itself a documented compatibility shim (the docstring spans 24 lines explaining why both production siblings and the pass-through tests reach through `optimizer/__init__.py`) — same calibration as the `optimizer/extension.py:63-67` `_stash_on_context` underscore-prefixed re-export shim recorded in `rev-optimizer___context.md`.

- **Error-class discipline.** `optimizer/` raises exactly two typed errors and the split is consistent: `ConfigurationError` (consumer-facing misconfiguration: `hints.py` rejects out-of-shape `OptimizerHint(...)` constructions; `walker.py::_apply_hint` rejects `force_select` on many-side relations and `prefetch(obj)` lookup mismatches) and `OptimizerError` (defensive descriptor guard: `field_meta.py::FieldMeta.from_django_field` rejects inputs missing `name` + `is_relation`). The two exception classes have non-overlapping use sites and the consumer-vs-defensive split is load-bearing. No `ValueError` / `TypeError` regressions inside the subpackage (only narrow `(TypeError, ValueError)` catches inside `plans.py::_consumer_only_fields` for the documented Django-private 2-tuple shape). Error-message phrasing inside `walker.py` consistently prefixes with `OptimizerHint.<factory>... on <TypeName>.<field_name>: ...` (three sites: `walker.py:481-484`, `walker.py:538`, `walker.py:549`); `hints.py` raises at construction time without resolver context (no `type_name.field_name` prefix available); the layer-appropriate divergence is correct.

- **Comment / docstring discipline at folder scope.** Per the worker-1 carry-forwards from `rev-optimizer__extension.md` and `rev-optimizer__walker.md`, the `spec-014 → spec-018` citation drift sweep across `optimizer/` (three sites total: `extension.py:701`, `walker.py:98`, `walker.py:581`) is closed — `grep -rn "spec-014" django_strawberry_framework/optimizer/` returns zero hits at folder-pass time, and `spec-018` appears at exactly the three audited sites. No other archived-spec / TODO-anchor / WIP-ALPHA citation rot found across the seven files at folder-pass time. Inline-comment style (RST-quote convention, audit-trail anchors, defensive-guard rationale) is uniform across siblings.

- **Test-tree discipline.** Per-file artifacts confirm `tests/optimizer/test_*.py` carries focused per-symbol pins for every documented contract (single-file granularity: `test_context.py`-style tests live inside `test_extension.py` because the context helpers are imported under aliases there; `test_field_meta.py`, `test_hints.py`, `test_plans.py`, `test_walker.py`, `test_extension.py` carry their own focused test classes). The "real-usage via fakeshop" gate is exercised by `examples/fakeshop/test_query/test_scalars_api.py::test_scalars_optimizer_coerces_manager_to_queryset_in_http_query` and the broader fakeshop GraphQL pings; the package-internal tree carries the symbol-level defensive coverage. Test placement is consistent with AGENTS.md rule 9.

- **Static helper sweep.** `python scripts/review_inspect.py --output-dir docs/shadow` was re-run at folder-pass time for `_context.py` and `__init__.py` (the two siblings whose overviews were absent under `docs/shadow/`); the other five (`extension.py`, `field_meta.py`, `hints.py`, `plans.py`, `walker.py`) already had current overviews from per-file cycles. Hotspot-density summary across the seven files: only `extension.py::_collect_schema_reachable_types._walk_gql_type` (45/14) and `extension.py::_optimize` (62/5) and `extension.py::_get_or_build_plan` (40/5) and `extension.py::check_schema` (48/10) and `extension.py::_build_cache_key` (63/4) and `extension.py::_walk_directives` (37/10) and `walker.py::_walk_selections` (140/13) clear the 40-line / 8-branch Medium threshold; all are explicitly addressed in the per-file artifacts with branch-coverage justifications and decomposition deferrals tied to explicit triggers.

- **Ruff gates clean at folder scope.** `uv run ruff format --check django_strawberry_framework/optimizer/` reports "7 files already formatted"; `uv run ruff check django_strawberry_framework/optimizer/` reports "All checks passed!" at folder-pass time.

### Summary

The `optimizer/` subpackage is a clean six-module + `__init__.py` cohesive subsystem with strict one-way intra-folder imports (`_context.py` / `hints.py` / `field_meta.py` / `plans.py` → `walker.py` → `extension.py` → `__init__.py`), a single source of truth for context-stash keys (`_context.py`'s five `DST_OPTIMIZER_*` constants), a single source of truth for skip-shape hint dispatch (`hints.py::hint_is_skip`), a single source of truth for plan mutations (`plans.py`'s `append_unique` / `append_unique_many` / `append_prefetch_unique`), and a documented internal-vs-consumer-API split codified in `__init__.py:14-17`. Zero High, zero Medium, four Lows — all of which are forwards-with-no-folder-level-edit: (a) cross-folder DRY act-now `FieldMeta._from_field_shape` forwarded to project pass (the optimizer side is one of two call sites; the second lives in `types/resolvers.py`), (b)/(c) GLOSSARY coverage forwards for the `DST_OPTIMIZER_*` literals and `FieldMeta` forwarded to project pass per the joint-cut deferral pattern, (d) a positive audit-trail forward confirming the `OptimizationPlan` / `plan_optimizations` / `plan_relation` GLOSSARY absences are correct under the `optimizer/__init__.py:14-17` internal-implementation framing. Five DRY items at folder scope, all defer-with-explicit-trigger or forwarded — no act-now folder-level consolidation candidate. Shape #5 qualifier (no source edits at folder scope; every Low is a forward; ruff format + check both green) — Worker 2 is skipped; Worker 1 fills the Worker 2 sections inline per the no-source-edit cycle pattern.

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle. All four Lows are forwards to the project pass with no in-cycle source/test/GLOSSARY/CHANGELOG edit; the four DRY bullets in `## DRY analysis` are either (a) forwarded to project pass for the cross-folder act-now decision, or (b) deferred-with-explicit-trigger at folder scope per the per-file artifact framing. No folder-level helper extraction was justified; no per-file finding was re-filed at folder scope.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format --check django_strawberry_framework/optimizer/` — pass (7 files already formatted; repo-wide COM812 formatter-conflict warning is pre-existing per per-file artifacts, not introduced by this cycle).
- `uv run ruff check django_strawberry_framework/optimizer/` — pass (All checks passed!).

### Notes for Worker 3
- Per-Low dispositions:
  - Low #1 (`FieldMeta._from_field_shape` cross-folder act-now extraction) — forwarded to `rev-django_strawberry_framework.md` project pass; folder pass cannot land the helper because the second call site lives in `types/resolvers.py`. Project pass should observe both folders simultaneously after `rev-types__resolvers.md` closes.
  - Low #2 (GLOSSARY drift on `DST_OPTIMIZER_*` literals) — forwarded to project pass per the joint-cut deferral pattern recorded in `rev-optimizer___context.md`.
  - Low #3 (GLOSSARY drift on `FieldMeta`) — forwarded to project pass per the joint-cut deferral pattern recorded in `rev-optimizer__field_meta.md`.
  - Low #4 (positive audit-trail confirmation that `OptimizationPlan` / `plan_optimizations` / `plan_relation` GLOSSARY absences are correct) — recorded for project-pass `## What looks solid` carry-forward; no edit required.
- No GLOSSARY-only fix in scope at folder layer.
- Shape #5 qualifier honoured: zero edits to any tracked file (source, tests, GLOSSARY, CHANGELOG), all Lows are forwards or deferrals.
- Ruff outcomes recorded above; folder-scope invocations only (per-file artifacts already ran the full `.` sweep).

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern.

No comment/docstring edits in scope at folder layer — every per-file artifact closed its own comment-pass / docstring-pass work in its own cycle. Folder pass adds no new comment-pass surface.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

### State
`Not warranted`.

### Reason
Cited per `worker-2.md`'s three-state-disposition gate, both halves required:

- `AGENTS.md` rule 21 — "Do not update CHANGELOG.md unless explicitly instructed."
- The active review plan `docs/review/review-0_0_7.md` is silent on changelog authorization for this cycle item — the folder pass for `optimizer/` is a no-source-edit cycle with all Lows forwarded; no consumer-visible behaviour change, no public symbol added/removed, no typed-error contract change, no GLOSSARY entry edit.

### What was done
No `CHANGELOG.md` edit.

### Validation run
- `uv run ruff format --check django_strawberry_framework/optimizer/` — pass (7 files already formatted).
- `uv run ruff check django_strawberry_framework/optimizer/` — pass (All checks passed!).

---

## Verification (Worker 3)

### Logic verification outcome
Shape #5 no-source-edit folder pass; all four Lows are forwards to the project pass (cross-folder `FieldMeta._from_field_shape` act-now extraction at Low #1 because the second call site lives in `types/resolvers.py`; `DST_OPTIMIZER_*` literal GLOSSARY drift at Low #2 per the joint-cut deferral pattern from `rev-optimizer___context.md`; `FieldMeta` GLOSSARY gap at Low #3 per the joint-cut pattern from `rev-optimizer__field_meta.md`; positive audit-trail confirmation at Low #4 that `OptimizationPlan` / `plan_optimizations` / `plan_relation` GLOSSARY absences are correct under `optimizer/__init__.py:14-17`'s internal-implementation framing). Zero High / Medium / Low source edits at folder scope; no GLOSSARY-only fix in scope. Spot-verified the load-bearing claims: `__init__.py:14-17` carries the internal-vs-consumer-API audit trail verbatim; `_context.py:34-38` is the single source of truth for the five `DST_OPTIMIZER_*` constants (`grep -rn '"dst_optimizer' optimizer/ types/` returns only those five assignments, zero raw-string regressions); `grep -rn "spec-014" optimizer/` returns zero hits so the citation-drift sweep stays closed; `__init__.py:29` exports exactly `("DjangoOptimizerExtension", "logger")` per the recorded discipline.

### DRY findings disposition
Five DRY items at folder scope, all forwards or defer-with-trigger:
- DRY #1 `FieldMeta._from_field_shape` cross-folder act-now extraction — forwarded to project pass (mirror lives at `types/resolvers.py::_field_meta_for_resolver` `not hasattr(...)` branch); the project pass owns the act-now decision after `rev-types__resolvers.md` and `rev-types__finalizer.md` close.
- DRY #2 `_evict_oldest_quarter(cache, max_size)` — deferred until a second `dict`-backed bounded cache lands under `optimizer/` (trigger from `rev-optimizer__extension.md` DRY #3).
- DRY #3 higher-order `_walk_ast(node, fragments, visited, on_node, on_fragment_def)` — deferred until a third selection-tree walker under `optimizer/` (trigger from `rev-optimizer__extension.md` DRY #1).
- DRY #4 `freeze_sentinel` / `@with_sentinels` helper for the `dataclass(frozen=True)` + `ClassVar` + post-class-body rebind pattern — deferred until a second `dataclass(frozen=True)` SKIP sentinel reappears under the package (trigger from `rev-optimizer__hints.md` DRY #2).
- DRY #5 cross-folder `_strawberry_schema_of(obj, default=None)` — deferred until a third Strawberry-schema reach site under `optimizer/` or any new consumer of the private attribute (trigger from `rev-optimizer__extension.md` DRY #2).
All five deferrals carry grep-resolvable triggers; the folder pass adds nothing new to the per-file evaluation.

### Temp test verification
- No temp tests used; shape #5 no-source-edit cycle.

### Verification outcome
`cycle accepted; verified`.

Five-check rundown:
1. `git diff --stat HEAD -- django_strawberry_framework/optimizer/ tests/optimizer/ docs/GLOSSARY.md CHANGELOG.md` shows dirty hunks across `optimizer/_context.py`, `optimizer/extension.py`, `optimizer/field_meta.py`, `optimizer/hints.py`, `optimizer/plans.py`, `optimizer/walker.py`, `docs/GLOSSARY.md`, `tests/optimizer/test_walker.py` AND a clean `CHANGELOG.md` diff. Per dispatch prompt ("sibling-cycle attributable hunks acceptable") and the artifact's "Files touched: None" claim, all eight dirty hunks attribute to the six closed sibling per-file cycles: `rev-optimizer___context.md`, `rev-optimizer__extension.md`, `rev-optimizer__field_meta.md`, `rev-optimizer__hints.md`, `rev-optimizer__plans.md`, `rev-optimizer__walker.md` — every one `Status: verified` on disk with checkboxes `[x]` at `review-0_0_7.md:73-78`. The folder-pass artifact itself contributed zero edits per its own "Files touched: None" record. Attribution chain holds (same pattern as `management/commands/` and `management/` folder cycles in worker memory).
2. All three Worker 2 sections (`## Fix report (Worker 2)`, `## Comment/docstring pass`, `## Changelog disposition`) open with `Filled by Worker 1 per no-source-edit cycle pattern.` verbatim.
3. All four Lows are "Forward to project pass" forwards; no Low landed an in-cycle GLOSSARY-only or source edit. The GLOSSARY-coverage forwards (Lows #2/#3) explicitly cite the joint-cut deferral pattern from the per-file artifacts.
4. Changelog `Not warranted` cites both `AGENTS.md` rule 21 ("Do not update CHANGELOG.md unless explicitly instructed") AND active-plan silence (`docs/review/review-0_0_7.md` is silent on changelog authorization for this cycle item). `git diff -- CHANGELOG.md` is empty, consistent with the disposition. The internal-only framing is honest because the cycle's edits at folder layer are zero (no source, no tests, no GLOSSARY, no CHANGELOG); no public-API surface was touched at folder scope.
5. Ruff gates clean on spot-verify: `uv run ruff format --check django_strawberry_framework/optimizer/` → "7 files already formatted" (repo-wide COM812 formatter-conflict warning pre-existing per per-file artifacts); `uv run ruff check django_strawberry_framework/optimizer/` → "All checks passed!".

---

## Iteration log

(Append-only; Worker 3 adds `## Verification (Worker 3)` block.)
