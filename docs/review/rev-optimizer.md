# Review: `django_strawberry_framework/optimizer/`

Status: verified

Folder pass over the optimizer subpackage. All seven in-scope siblings are `verified`
(`rev-optimizer___context.md`, `rev-optimizer__extension.md`, `rev-optimizer__field_meta.md`,
`rev-optimizer__hints.md`, `rev-optimizer__plans.md`, `rev-optimizer__selections.md`,
`rev-optimizer__walker.md`). This pass covers `optimizer/__init__.py`
(shadow `docs/shadow/django_strawberry_framework__optimizer____init__.overview.md`) and the
folder-level structure: cross-sibling duplicated helpers, naming / error-handling drift,
repeated ORM/queryset patterns, misplaced responsibilities, `__init__.py` exports,
circular-import risk, and the repeated-literal + import-direction checks across sibling
shadows. The two siblings explicitly forwarded two cross-file DRY items to this pass; both
are re-derived with all siblings in view and dispositioned below. Baseline HEAD `58ca2def`.
No source edit warranted from this folder pass (shape #3 → #5).

## DRY analysis

- **FK-id-elision recompute twins (`field_meta.py` build-time stamper vs `walker.py`
  walk-time consumer) — deferred-with-trigger, genuinely intentional dual-path. Disposition
  CONFIRMED at folder scope.** `field_meta.py::FieldMeta._from_field_shape`
  (field_meta.py:211-220 elision boolean), `field_meta.py::_target_pk_name` (field_meta.py:227-241),
  and `field_meta.py::_has_composite_pk` (field_meta.py:244-247) are the build-time canonical
  producers; `walker.py::_can_elide_fk_id` (walker.py:854-889) and `walker.py::_target_pk_name`
  (walker.py:892-900) plus the inline composite-PK guard (walker.py:873-880) are the
  walk-time consumers. Both walker helpers are `getattr(field, "<slot>", None)`-first shims
  (walker.py:862-864, 894-896) that return the stamped value when present and only recompute
  from a raw Django descriptor on the unstamped / test-double fallback. The recompute tails
  are logically byte-equivalent to the producer (same seven `and` clauses, same composite-PK
  exclusion). **This is NOT an act-now consolidation** for three folder-confirmed reasons:
  (1) **input-contract divergence** — `field_meta._target_pk_name` takes a **model**
  (field_meta.py:227), `walker._target_pk_name` takes a **field/FieldMeta** (walker.py:892);
  a naive merge fuses two input shapes. (2) **deliberate decoupling** — `walker.py` does NOT
  import `field_meta.py` at all (confirmed: walker's intra-package imports are only `hints`,
  `plans`, `selections`); it consumes `FieldMeta` purely by stamped-slot duck-typing, so the
  recompute tail is the *decoupling mechanism*, not an accidental copy. Folding it into a
  shared free function would re-introduce a `walker → field_meta` edge that the current design
  avoids. (3) the consolidation spans two files, so it cannot land in any single-file cycle.
  **Defer with trigger (verbatim):** "walker's raw-descriptor recompute fallback is removed"
  — i.e. once a registry-coverage gate guarantees every field reaching the walker is
  `FieldMeta`-stamped, both walker shims collapse to a pure slot read, the recompute logic
  lives only in `field_meta.py`, and the cross-file edge question is moot. Trigger unmet today
  (`field_meta.py` has no `m2m_connector_attname` slot and the walker's fallback is still
  reachable from fabricated resolver-path shapes). This is the cross-file confirmation the
  `field_meta.py` and `walker.py` siblings forwarded.

- **Per-relation argument bundle re-passed through the walker dispatch tree
  (`(plan, prefix, info, runtime_paths, resolver_identities, enable_only)` alongside the
  relation tuple) — deferred-with-trigger, REFINED. Disposition: defer, but the trigger's
  threshold is folder-confirmed as not-yet-met and the future home is correctly the folder
  scope.** The shared context bundle threads through `_plan_select_relation` /
  `_plan_prefetch_relation` / `_record_relation_access` / both `_apply_hint` re-dispatches /
  `_plan_connection_relation` (the `enable_only=enable_only` token alone appears at 17 sites
  in walker.py, of which ~4-6 are distinct dispatch families; the rest are the single-decision
  recursive propagation of a flag derived once in `plan_optimizations` at walker.py:108). The
  proposed consolidation — a frozen `RelationWalkContext` dataclass threaded once — does **not
  yet exist anywhere in the package** (grep `RelationWalkContext` = NONE). Acting now is
  net-neutral: the bundle is still readable at each site and the dataclass earns its keep only
  when the call sites grow another member. spec-035 added exactly ONE member (`enable_only`)
  to a bundle the prior 0.0.9 cycles already flagged on `_plan_select_relation` /
  `_plan_prefetch_relation`; the trend is real but the threshold is one member short. **Defer
  with trigger (verbatim):** "the planner gains a further per-relation context member beyond
  `enable_only`" — at that point fold `(plan, prefix, info, runtime_paths,
  resolver_identities, enable_only)` into a frozen `RelationWalkContext` dataclass threaded
  once through the relation-walk dispatch family. **Refinement recorded for the next DRY
  cycle:** when the trigger fires, the dataclass should be a *folder-scoped* type (a new
  small module or a block in `walker.py`), because the bundle is internal to the walk and
  never crosses the `extension.py` seam (extension calls `plan_optimizations(...)` /
  `plan_relation(...)`, not the per-relation dispatchers) — so it is a walker-internal
  consolidation, not a cross-sibling one. Confirm/refine: **confirmed** as a real deferred
  candidate; **refined** to "walker-internal, folder-scoped dataclass" rather than a
  cross-module shared type.

- **No NEW folder-level DRY candidate surfaced by the cross-sibling checks.** The repeated
  string-literal compare across all eight sibling shadows shows the only 2+-file literal is
  `selections` (in `selections.py` and `walker.py`) plus per-file reflective-access attribute
  names (`queryset`, `target_field`, `related_model`, `arguments`, `prefetch`, `operation`) —
  all `getattr`-key strings for Django/Strawberry node shapes or parameter names, none of
  which are string-keyed dispatch constants that could hoist to a shared named constant. The
  genuine shared-vocabulary keys (the five `DST_OPTIMIZER_*` stash keys, the four pagination
  arg names) are already single-sourced (`_context.py`, `extension.py::_PAGINATION_ARG_NAMES`)
  and consequently do NOT appear as cross-file repeats — confirming the existing
  single-sourcing holds. No new helper to extract at folder scope.

## High:

None.

## Medium:

None.

## Low:

None. (The pre-existing M2M-connector raw-`_meta` Low and the two `selections.py`
intentional-asymmetry Lows are file-scoped and already dispositioned with verbatim triggers
in their `verified` sibling artifacts; a folder pass does not re-litigate `verified` file
internals. No folder-level Low surfaced.)

## What looks solid

### DRY recap

- **Existing patterns reused (folder-confirmed single-sourcing).** The subpackage routes
  every shared mechanism through exactly one owner and the siblings consume by re-alias, not
  re-implementation: request-scope stash dispatch + the five `DST_OPTIMIZER_*` keys are
  single-sourced in `_context.py` (consumed by `extension.py` write-side and
  `types/resolvers.py` read-side); the selection-traversal primitives (fragment /
  directive / response-key / `edges { node }`-unwrap) are single-sourced in `selections.py`
  (consumed by `walker.py:54-61` and `extension.py:67-75` under `_`-aliases, the 0.0.9 DRY
  pass); the hint-skip dispatch is single-sourced in `hints.py::hint_is_skip` (consumed by
  two `walker.py` sites + `extension.py`); relation classification is single-sourced in
  `utils/relations.py` (consumed by `field_meta.py` and `walker.py`); the cursor-parity
  `deterministic_order` / `ends_in_unique_column` live once in `plans.py` and are imported
  back by `connection.py`. The plan-build-and-apply tail is single-sited in
  `extension.py::apply_to`, shared by `_optimize` and `apply_connection_optimization`.
- **New helpers considered.** The two forwarded cross-file items (FK-id-elision twin,
  `RelationWalkContext` bundle) were both re-derived with all siblings in view and remain
  deferred-with-trigger (see `## DRY analysis`); neither trigger has fired. A folder-level
  hoist of the repeated reflective-access attribute-name literals was considered and rejected
  — they are `getattr` keys / parameter names, not dispatch constants.
- **Duplication risk in the current folder.** The FK-id-elision recompute logic is the one
  genuinely-near-duplicate pair, and it is intentional sibling design: the producer stamps,
  the consumer reads-stamped-or-recomputes, and the recompute tail is the deliberate
  decoupling that keeps `walker.py` from importing `field_meta.py`. Divergence risk is
  mitigated by both being test-pinned (eight relation shapes in
  `tests/optimizer/test_field_meta.py`; the gate arms + elision-under-mutation in
  `tests/optimizer/test_walker.py`).

### Other positives

- **`__init__.py` exports are minimal and correct.** Re-exports exactly
  `DjangoOptimizerExtension` (the sole consumer-facing public symbol) and `logger`
  (the canonical intra-subpackage logger handle that `extension.py` and `walker.py` consume
  via `from . import logger`, so the `"django_strawberry_framework"` literal lives in one
  place). `__all__ = ("DjangoOptimizerExtension", "logger")`. `OptimizationPlan` /
  `plan_optimizations` are deliberately NOT re-exported (internal, consumed at their dotted
  paths) — the docstring documents this and the rationale. Shadow overview: imports 2,
  symbols 0, no executable code, no ORM markers, no repeated literals — clean namespace module.
- **Import-direction graph is one-way and acyclic.** Intra-package edges form a clean DAG:
  `_context.py` and `selections.py` are pure leaves (no intra-optimizer, no first-party
  imports); `field_meta.py` / `hints.py` / `plans.py` import only outward to `..exceptions` /
  `..utils`; `walker.py` imports `hints` / `plans` / `selections`; `extension.py` (the
  orchestrator) imports all of `_context` / `hints` / `plans` / `selections` / `walker`;
  `__init__.py` imports `.extension`. No sibling-to-sibling cycle. The single optimizer→types
  edge (`walker.py:919 from ..types.definition import origin_has_custom_id_resolver`) is
  correctly deferred to function scope to break the optimizer↔types cycle. `selections.py`'s
  one strawberry import is likewise function-local.
- **Error-handling is consistent across siblings.** `OptimizerError` (typed-input guards in
  `field_meta.py`, `plans.py`, `walker.py`) and `ConfigurationError` (hint conflicts in
  `hints.py`, hint application in `walker.py`) are the two consistent first-party exception
  families; no sibling raises a bare `AttributeError`/`ValueError` where a typed error
  belongs. Defensive reflective access uniformly uses the `getattr(..., default) or default`
  idiom across `selections.py` (25 sites), `plans.py`, `walker.py`, and `field_meta.py`, with
  the deliberate "fail-loud on malformed test double" exceptions (the M2M-connector raw
  `_meta` read) documented in the owning sibling.
- **Responsibility boundaries are clean (Two Scoops layering).** `field_meta.py` =
  metadata PRODUCER; `plans.py` = passive plan CARRIER (stores `fk_id_elisions` as opaque
  resolver keys, computes nothing about eligibility); `walker.py` = selection-tree planner /
  metadata CONSUMER; `selections.py` = traversal substrate; `_context.py` = request-scope
  hand-off dispatch; `hints.py` = the `OptimizerHint` value type; `extension.py` = the
  Strawberry-extension orchestrator and the only consumer-facing entry. No misplaced
  responsibility surfaced — the forwarded "where does FK-id-elision live" question resolves
  cleanly (producer in `field_meta`, carrier in `plans`, consumer in `walker`), and each
  sibling's artifact independently arrived at the same partition.
- **spec-035 hardening kept the folder coherent.** spec-035 touched three siblings —
  `extension.py` (G1 evaluated-queryset guard), `walker.py` (G2 `enable_only` projection
  gate, +172 lines), and `selections.py` (the G3 TODO, re-anchored this review run to the
  active BACKLOG card). All three changes routed through the existing single-owner seams
  (G1 sits between `normalize_query_source` and the shared `apply_to` tail; G2 threads one
  flag derived once and consumed at every projection writer; the G3 TODO ships no runtime
  code). No new cross-sibling duplication, no responsibility migration, no new import edge.
  The folder's internal structure is unchanged in shape — the hardening added behavior inside
  the existing boundaries, exactly the desired outcome.
- **Comment consistency across siblings.** The TODO anchors are now uniformly active: the
  `selections.py` G3 anchor was re-anchored (verified prior-cycle edit, dirty vs HEAD) to
  `TODO(BACKLOG polymorphic_interface_connections …)` and the two `walker.py` G3 anchors
  carry the same deferral rationale; no sibling carries a stale spec reference. The
  cross-sibling docstrings agree on the shared contracts (e.g. `hints.py::__post_init__` and
  `walker.py::_apply_hint` both document construction-time conflict rejection vs dispatch
  ordering).

### Summary

The optimizer subpackage is in excellent folder-level shape. All seven in-scope siblings are
`verified`; the `__init__.py` is a clean two-export namespace module with minimal,
correctly-scoped public surface (`DjangoOptimizerExtension` + `logger`). The intra-package
import graph is a one-way DAG with the single optimizer→types edge correctly function-scoped,
so there is no circular-import risk. Responsibility boundaries are clean (producer / carrier /
consumer / substrate / dispatch / value-type / orchestrator), error handling and defensive
reflective-access idioms are consistent across siblings, and the spec-035 hardening
(extension / walker / selections) added behavior strictly inside the existing single-owner
seams without introducing new cross-sibling duplication or import edges. The cross-sibling
repeated-literal compare surfaced no new DRY candidate — the only shared literals are
reflective-access attribute names, while the genuine shared-vocabulary keys are already
single-sourced. The two forwarded cross-file DRY items are both confirmed genuinely
intentional dual-path / deferred-with-trigger: (1) the FK-id-elision recompute twins are the
deliberate decoupling that keeps `walker.py` from importing `field_meta.py` (trigger:
"walker's raw-descriptor recompute fallback is removed"); (2) the per-relation argument bundle
is a confirmed-but-not-yet-triggered `RelationWalkContext` candidate, refined to
walker-internal / folder-scoped (trigger: "the planner gains a further per-relation context
member beyond `enable_only`"). No High / Medium / Low folder-level findings; no act-now
consolidation warranted. No-source-edit folder pass (shape #3 → #5).

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — 270 files left unchanged.
- `uv run ruff check --fix .` — All checks passed (only the pre-existing COM812-vs-formatter config notice).

### Notes for Worker 3
- Folder pass over `optimizer/`; all seven siblings `verified`. Covered `optimizer/__init__.py`
  (clean two-export namespace module) + folder structure. No High/Medium/Low folder finding.
- Both forwarded cross-file DRY items are deferred-with-trigger (triggers unmet) and recorded
  in `## DRY analysis`: FK-id-elision recompute twins (confirmed intentional dual-path —
  `walker.py` does not import `field_meta.py`; the recompute tail is the decoupling) and the
  per-relation argument bundle (confirmed candidate, refined to walker-internal /
  folder-scoped; `RelationWalkContext` does not exist yet). Neither is act-now.
- No GLOSSARY-only fix in scope. GLOSSARY/TREE folder-level optimizer references
  (`DjangoOptimizerExtension`, subpackage descriptions) are accurate; per-symbol GLOSSARY
  checks already cleared in the `verified` sibling artifacts.
- `selections.py` is dirty vs HEAD — this is the VERIFIED TODO re-anchor from the closed
  `rev-optimizer__selections.md` cycle (the maintainer has not yet committed it), i.e. the
  folder's reviewed state, not an unrelated concurrent edit. Diff is exactly the -6/+12
  comment block. No optimizer source edited THIS cycle (`git diff HEAD --
  django_strawberry_framework/optimizer/` shows only that prior-cycle comment hunk).

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern.

No comment/docstring edits warranted at folder scope. The `__init__.py` docstring accurately
documents the two-export contract and the deliberate non-export of `OptimizationPlan` /
`plan_optimizations`. Cross-sibling comment consistency confirmed: TODO anchors are uniformly
active (no stale spec references), and the shared-contract docstrings agree across siblings
(`hints.py`/`walker.py` hint dispatch; `_context.py`/`extension.py` stash hand-off;
`selections.py` traversal substrate consumed by `walker.py`/`extension.py`). Shadow overview
for `__init__.py` reports 0 TODO comments.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

Not warranted — no source change this cycle (folder review only; empty optimizer-source diff
for this cycle). Per AGENTS.md #21 ("Do not update CHANGELOG.md unless explicitly instructed")
and the active plan `docs/review/review-0_0_10.md` (silent on changelog edits for review
cycles). The spec-035 hardening ships its own CHANGELOG entry under its Slice 4 maintainer
prompt, out of scope for this review.

---

## Verification (Worker 3)

Terminal folder-pass verification of the no-source-edit (shape #5) cycle over
`django_strawberry_framework/optimizer/`. Baseline `58ca2def` == current HEAD. The four
load-bearing folder claims were independently confirmed against current source.

### Logic verification outcome

No High / Medium / Low findings to address — all `None`, confirmed at folder scope.
Independent confirmation of the four load-bearing structural claims:

- **(a) `walker.py` does NOT import `field_meta.py` — CONFIRMED.** walker's intra-package
  imports are exactly `logger` (`. `), `hints`, `plans`, `selections` (walker.py:24-37);
  there is no `from .field_meta` edge at module or function scope. The only two `field_meta`
  tokens in walker.py are a docstring (walker.py:181) and a comment (walker.py:916), not
  imports. This validates the FK-id-elision dual-path rationale: walker's
  `_can_elide_fk_id` / `_target_pk_name` (walker.py:854-900) are `getattr(stamped, None)`-first
  shims whose raw-`_meta` recompute tails (e.g. `related_model._meta.pk.name` at walker.py:900,
  the `field.attname … and not field.many_to_many …` chain at walker.py:881-889) ARE the
  decoupling mechanism. Folding them into a shared free function would re-introduce the
  `walker → field_meta` edge the design provably avoids.

- **(b) Import graph acyclic, optimizer→types edge function-scoped — CONFIRMED.** Per-sibling
  module-level intra-optimizer import scan: `_context.py` / `field_meta.py` / `hints.py` /
  `plans.py` / `selections.py` are leaves (no sibling-to-sibling module imports); `walker.py`
  imports `logger`/`hints`/`plans`/`selections`; `extension.py` imports
  `logger`/`_context`/`hints`/`plans`/`selections`/`walker`; `__init__.py` imports `.extension`.
  No back-edge, no cycle — clean one-way DAG. The single optimizer→types edge
  (`from ..types.definition import origin_has_custom_id_resolver`) appears at exactly ONE site,
  walker.py:919, function-local inside `_origin_has_custom_id_resolver` (the comment at
  walker.py:916-918 names the cycle it breaks: `types.definition` pulls in
  `optimizer.field_meta` at module load). No module-level `..types` import exists in any sibling.

- **(c) `__init__.py` exports exactly the intended surface — CONFIRMED.** Module body is
  `from .. import logger` + `from .extension import DjangoOptimizerExtension` and
  `__all__ = ("DjangoOptimizerExtension", "logger")` — the minimal two-export namespace.
  `OptimizationPlan` / `plan_optimizations` are deliberately NOT re-exported; the docstring
  documents both the re-export contract (consumed by `extension.py`/`walker.py` via
  `from . import logger`) and the non-export rationale.

- **(d) Both DRY forwards genuinely deferred-with-valid-trigger, NOT dodged act-now
  consolidations — CONFIRMED.**
  - *FK-id-elision recompute twins*: the consolidation's own trigger ("walker's raw-descriptor
    recompute fallback is removed") is unmet — `field_meta.py` has slots
    `reverse_connector_attname` (field_meta.py:124) and `target_field_attname` but NO
    `m2m_connector_attname` slot, so the walker recompute fallback is still reachable. Acting
    now is impossible without re-introducing the avoided `walker→field_meta` edge (claim a),
    making this a sound deferral, not a dodge.
  - *`RelationWalkContext` bundle*: grep `RelationWalkContext` across the whole package =
    NONE — the candidate type does not exist yet, and spec-035 added exactly one member
    (`enable_only`), one short of the "further per-relation context member beyond
    `enable_only`" trigger. Net-neutral to act now; correctly deferred (refined to
    walker-internal/folder-scoped). Confirms Worker 1 shape #5 context.

### DRY findings disposition

No new folder-level DRY candidate (confirmed: cross-sibling repeated literals are
`getattr`-key/parameter-name strings, not dispatch constants; genuine shared-vocabulary keys
already single-sourced in `_context.py` / `extension.py`). The two forwarded cross-file items
remain deferred-with-trigger per the independent checks above; neither trigger has fired.
Both forwards from the `field_meta.py` and `walker.py` sibling cycles are now closed at folder
scope. DRY soundness verified.

### Sibling-cycle attribution (shape #5)

`git diff --stat 58ca2def -- django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md`
shows dirty hunks at `management/commands/_imports.py|export_schema.py|inspect_django_type.py`
+ `tests/management/test_imports.py` (closed `rev-management__commands.md`, verified, [x] at
review-0_0_10.md) and `optimizer/selections.py`. The `selections.py` hunk is exactly the
-6/+12 TODO re-anchor block (`TODO(spec-035 Slice 3)` → `TODO(BACKLOG
polymorphic_interface_connections …)`), attributing to the closed sibling cycle
`rev-optimizer__selections.md` (`Status: verified`, [x] at review-0_0_10.md:98) — the folder's
reviewed state, not concurrent maintainer work. `git diff HEAD -- optimizer/` shows only that
single prior-cycle comment hunk. The folder pass's own "Files touched: None" claim holds.

### Temp test verification

None used — no behavioral claim required runtime proof; all four claims are structural
(import graph, export surface, candidate-existence) and confirmed by grep/read against source.

### Shape #5 mechanics

- Each Worker 2 section opens with `Filled by Worker 1 per no-source-edit cycle pattern.`
  (Fix report, Comment/docstring pass, Changelog disposition). ✓
- Changelog `Not warranted`: `git diff -- CHANGELOG.md` empty (0 lines); disposition cites
  BOTH AGENTS.md #21 and the active plan `review-0_0_10.md`'s silence on changelog
  authorization for review cycles. Internal-only framing matches the empty cycle diff. ✓
- No GLOSSARY-only fix; no Low without verbatim trigger (all Lows are `None`). ✓
- `uv run ruff format --check` — 8 files already formatted; `uv run ruff check` — all checks
  passed (only the pre-existing COM812-vs-formatter notice). ✓

### Verification outcome

`cycle accepted; verified` — sets top-level `Status: verified` AND marks the `optimizer/`
folder-pass checklist box at `docs/review/review-0_0_10.md`.
