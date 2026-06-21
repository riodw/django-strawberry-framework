# Review: `django_strawberry_framework/optimizer/` (folder pass)

Status: verified

Folder pass over the 7 in-scope files (`_context.py`, `extension.py`, `field_meta.py`, `hints.py`, `plans.py`, `selections.py`, `walker.py`) plus the subpackage `__init__.py`. All 7 per-file artifacts are `verified` this cycle. Per-cycle baseline `252672d1b7c694e857bfe4fa71f1280137d83030`; `git diff 252672d1… -- django_strawberry_framework/optimizer/` is EMPTY and `git diff HEAD -- …/optimizer/` is EMPTY. No optimizer source file is dirty in `git status` (the dirty paths are `docs/review/*` scratchpads + sibling specs — AGENTS.md #34 concurrent maintainer work, out of scope). Static helper confirmed run on every `.py` including `__init__.py` (8 overviews under `docs/shadow/`). Genuine **shape #5 no-source-edit cycle**: no High, no behavior-changing Medium, every cross-file DRY item defer-with-trigger, zero tracked edits.

## DRY analysis

- **`_target_pk_name` recompute twin between `walker.py` and `field_meta.py` (forwarded from `rev-optimizer__walker.md`).** `optimizer/walker.py::_target_pk_name` (walker.py:873-881) and `optimizer/field_meta.py::_target_pk_name` (field_meta.py:232-246) both bottom out in a `related_model._meta.pk.name` read, but their input contracts diverge: the walker's takes a **field/FieldMeta** and dereferences `.related_model` (with a `getattr(field, "target_pk_name", None)` stamped fast-path first, walker.py:875-877), while `field_meta.py`'s takes a **model directly**. Consolidation requires a shared free function spanning both files plus a decision on where the stamped-slot short-circuit lives. **Defer with trigger:** "walker's raw-descriptor recompute fallback is removed" — once a registry-coverage gate guarantees every field reaching the walker is `FieldMeta`-stamped, the walker's recompute tail (walker.py:878-881) deletes and the only remaining `_target_pk_name` lives in `field_meta.py`; the twin collapses for free. Acting now is net-negative (a cross-file helper to bridge two genuinely different input contracts adds an indirection layer the trigger will obsolete). Folder-level disposition: **kept folder-level, deferred** — both sites are `optimizer/`-internal, so this is not a project-pass forward.

- **Wide relation-context argument bundle threaded through walker's four projection writers (forwarded from `rev-optimizer__walker.md`).** `_plan_select_relation` / `_plan_prefetch_relation` / `_record_relation_access` / `_apply_hint`'s re-dispatches all thread the same `(plan, prefix, info, runtime_paths, resolver_identities, enable_only)` bundle alongside the relation tuple (walker.py:449-473, 716-722, 739-763, 765-776). **Defer with trigger:** "the planner gains a further per-relation context member beyond `enable_only`" — at that point fold the bundle into a frozen `RelationWalkContext` dataclass threaded once. Acting now is net-neutral (the bundle is still readable at four sites; the dataclass earns its keep on the next added member). All four sites are within `walker.py`, so this is a single-file deferral surfaced at folder level only because the relation-context shape is the spine of the walker's dispatch tree. Folder-level disposition: **kept folder-level (single-file), deferred.**

- **`_can_elide_fk_id` eligibility-predicate twin — RESOLVED, not a candidate.** Recorded here for the audit trail because prior cycles forwarded it as a folder-level item: commit `3b4f90c0` routed `walker.py::_can_elide_fk_id`'s raw-field fallback through `FieldMeta._from_field_shape(field, is_relation=True).fk_id_elision_eligible` (walker.py:870), so the 8-conjunct eligibility predicate is now single-sourced in `field_meta.py::FieldMeta._from_field_shape` and shared by the walker, the resolver test-double path (`types/resolvers.py::_field_meta_for_resolver`, :292), and the canonical `from_django_field` entry. No remaining predicate duplication. Only the `_target_pk_name` model-pk *lookup* (first bullet) still hand-recomputes.

## High:

None.

## Medium:

None.

## Low:

None — the one pre-existing Low in scope (`walker.py::_connector_only_field` M2M branch reads `related_model._meta.pk.attname` raw, walker.py:928) is a single-file finding already recorded and deferred-with-trigger in `rev-optimizer__walker.md` ("a stamped `m2m_connector_attname` slot is added to `FieldMeta`"); it is not a cross-file folder concern and is not re-raised here.

## What looks solid

### DRY recap

- **Shared discriminators are aliased, never re-implemented (forwarded item c — confirmed).** `is_fragment` and `should_include` are each defined exactly once in `optimizer/selections.py` (selections.py:273, :287). `walker.py` imports both and binds underscore aliases (`_is_fragment = is_fragment`, `_should_include = should_include`, walker.py:40,45,55-56; used at walker.py:1046). `extension.py` consumes them **transitively** through the higher-level `selections` helpers it imports (`named_children`, `node_children_with_runtime_prefix`, `directive_variable_names`, `ast_child_selections`, `resolve_unvisited_fragment`, `response_key` — extension.py:67-75, re-aliased under `_`-names at extension.py:85-89) — it does NOT re-spell the `type_condition`/`@skip`/`@include` logic. Grep confirms the `("skip", "include")` membership + `VariableNode` directive gate lives once (selections.py:251,258,290,295); the only other `"skip"` literal is `hints.py::hint_is_skip`'s `getattr(hint, "skip", False)` (hints.py:150), the distinct OptimizerHint-skip contract, not the directive gate. No discriminator drift possible across the three consumers.

- **Every cross-module substrate is single-owned with a one-way DAG.** `_context.py` owns the 5 `DST_OPTIMIZER_*` keys + stash dispatch; `selections.py` owns selection traversal; `hints.py` owns the skip-shape primitive (`hint_is_skip`, consumed by walker.py:687,1331 + extension.py:1045); `plans.py` owns the `append_unique*` merge discipline + `prefetch_to` private-attr contract + the hoisted `ends_in_unique_column`/`deterministic_order` that `connection.py` imports back (spec-033 Decision 11); `field_meta.py` owns the `fk_id_elision_eligible` predicate + `_from_field_shape` shape source. No literal or near-copy is re-spelled across siblings beyond the deferred `_target_pk_name` lookup.

- **Cross-sibling repeated-literal sweep clean.** Comparing the `Repeated string literals` sections of all 8 shadow overviews: the only literals appearing in 2+ files are `selections` (selections.py 10x + walker.py 2x) and `related_model` (walker.py 2x; read defensively in field_meta.py but not flagged repeated there). Both are graphql-core / Django protocol attribute names read via reflective `getattr` off heterogeneous duck-typed objects (AST nodes, Strawberry dataclasses, `FieldMeta`, raw Django fields) — protocol field names, not a string-keyed dispatch that could hoist to a shared constant. The string-key constants that DO warrant single-sourcing (`DST_OPTIMIZER_*`, `("skip","include")`, `_PAGINATION_ARG_NAMES`) are already centralized. No new folder-level literal-DRY candidate.

### Other positives

- **`__init__.py` export surface is correct and minimal.** `__all__ = ("DjangoOptimizerExtension", "logger")` (sorted, no private leak). `DjangoOptimizerExtension` is re-exported from `.extension` and consumed by the package root (`django_strawberry_framework/__init__.py:25`) — the single consumer-facing optimizer surface. `logger` is re-exported from `..` (the top-level package, the one home of the `"django_strawberry_framework"` logger-name literal) and is load-bearing: `walker.py:24` and `extension.py:51` consume it via `from . import logger`, and the re-export contract is pinned by `tests/optimizer/test_extension.py:52` + `tests/base/test_init.py:13`. The docstring's claim that removing the re-export "would silently break both production siblings, not just the tests" is accurate — grep confirms exactly those two production consumers and two test pins. `OptimizationPlan` / `plan_optimizations` are correctly NOT re-exported here (consumed at their dotted module paths; internal implementation detail, per the docstring).

- **Import DAG is one-way acyclic, no circular-import risk.** Leaves with zero sibling imports: `_context.py`, `field_meta.py`, `hints.py`, `plans.py`, `selections.py`. Mid-level: `walker.py` → `{field_meta, hints, plans, selections}`. Apex: `extension.py` → `{_context, hints, plans, selections, walker}`. Subpackage init: `__init__.py` → `extension` + `..logger`. `extension → walker` is a forward edge (apex over mid-level); `selections` is imported by both `walker` and `extension` but imports no sibling back (the 0.0.9 substrate that removed the prior `extension ↔ walker` round-trip, docs/feedback.md Major 2). No back-edge anywhere; verified at source.

- **Naming and error-handling are consistent across the folder.** Typed optimizer exceptions are sourced from one place (`..exceptions`: `OptimizerError` in field_meta/plans/walker, `ConfigurationError` in hints/walker). Reflective `getattr` reads carry `or`-defaults or upstream presence guards uniformly across every file (each per-file artifact's reflective-access audit came back clean). The `_`-prefixed-private vs `__all__`-public axis is applied consistently: no private symbol is re-exported, and every public-contract symbol that has GLOSSARY prose (`DjangoOptimizerExtension`, `OptimizerHint`, `OptimizationPlan.apply`, the `dst_optimizer_plan` stash, strictness, FK-id elision, plan cache) was verified drift-free in its per-file artifact, while the internal optimizer symbols (no `__all__`: `FieldMeta`, `hint_is_skip`, walker/plans/selections helpers) correctly carry no GLOSSARY entry — absence is correct, not drift.

- **Comment consistency.** The cross-module-claim comments are grep-verified accurate: the `__init__.py` logger-consumer claim, the `extension.py:80-89` underscore-alias provenance note (tests import `_named_children`/`_node_children_with_runtime_prefix` from extension — confirmed at test_extension.py:54-55), the `plans.py` "connection.py imports this back" notes, and the spec-033/spec-035 Decision cross-references. No stale TODO across the folder (`selections.py:315` and the two `walker.py` spec-035 anchors are validly BACKLOG/spec-anchored and AGENTS.md-exempt).

### Summary

The `optimizer/` subpackage is a mature, tightly-factored subsystem with a clean one-way acyclic import DAG (`selections`/`_context`/`field_meta`/`hints`/`plans` leaves → `walker` → `extension` → `__init__`), single-owned cross-module substrates, and a minimal correct export surface (`DjangoOptimizerExtension` + the load-bearing `logger` re-export, both with verified live consumers). All 7 per-file artifacts are `verified`; the cycle diff is empty against both the per-cycle baseline (`252672d1…`) and HEAD; no optimizer source is dirty. The folder-pass cross-file sweep surfaces no new finding: the three forwarded DRY items resolve to one RESOLVED predicate-twin (commit `3b4f90c0`), one folder-level defer-with-trigger (`_target_pk_name` lookup twin, kept folder-level), and one single-file defer-with-trigger (the relation-context argument bundle); the shared `is_fragment`/`should_include` discriminators are confirmed aliased (walker) / transitively consumed (extension), never re-implemented; the cross-sibling repeated-literal sweep is clean. Zero High/Medium/Low at folder level. Genuine no-source-edit (shape #5) cycle.

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass; `289 files left unchanged`.
- `uv run ruff check --fix .` — pass; `All checks passed!` (only the pre-existing COM812-vs-formatter config notice).

### Notes for Worker 3
- Folder pass over `optimizer/`; all 7 per-file artifacts `verified`. Cycle diff EMPTY vs both baseline `252672d1b7c694e857bfe4fa71f1280137d83030` and HEAD (`33466db5`); no optimizer source dirty (dirty paths are `docs/review/*` + sibling specs, AGENTS.md #34 concurrent work). Static helper confirmed run on every `.py` including `__init__.py` (8 `docs/shadow/` overviews present).
- No High / no behavior-changing Medium / no folder-level Low. Three forwarded DRY items dispositioned: (a) `_target_pk_name` lookup twin → KEPT FOLDER-LEVEL, defer-with-trigger "walker's raw-descriptor recompute fallback is removed" (both sites `optimizer/`-internal, NOT a project-pass forward); (b) relation-context argument bundle → single-file (`walker.py`) defer-with-trigger "the planner gains a further per-relation context member beyond `enable_only`"; (c) the prior `_can_elide_fk_id` predicate twin is RESOLVED by commit `3b4f90c0` (single-sourced through `FieldMeta._from_field_shape`), recorded in the DRY recap, not a candidate.
- Forwarded item (c shared discriminators) confirmed: `is_fragment`/`should_include` defined once in `selections.py:273,287`, ALIASED by `walker.py:40,45,55-56`, consumed TRANSITIVELY by `extension.py` via the `selections` helper imports (extension.py:67-75) — neither consumer re-implements the directive/fragment logic (grep: `("skip","include")` gate lives once in `selections.py`).
- Export surface: `__all__ = ("DjangoOptimizerExtension", "logger")` sorted/no-leak; `logger` re-export consumed by `walker.py:24` + `extension.py:51` + tests (`test_extension.py:52`, `test_init.py:13`); `DjangoOptimizerExtension` by package root `__init__.py:25`. Import DAG one-way acyclic (verified at source). No GLOSSARY-only fix in scope — all public-contract optimizer symbols verified drift-free in their per-file artifacts; internal symbols correctly carry no entry.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern.

No comment/docstring edits warranted at folder level. The cross-module-claim comments were grep-verified accurate across the folder: the `__init__.py` logger-consumer docstring (two production siblings + two test pins, all confirmed), the `extension.py:80-89` underscore-alias provenance note, the `plans.py` "connection.py imports this back" notes, and the spec-033/spec-035 Decision references. No stale TODO across the folder (per-file artifacts confirmed `selections.py:315` BACKLOG-anchored and the two `walker.py` spec-035 anchors validly scoped, all AGENTS.md-exempt). Each per-file artifact's comment pass is already `verified`.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

Not warranted — no source, test, GLOSSARY, or CHANGELOG edit this cycle (review-only folder pass, zero findings, empty cycle diff). AGENTS.md #21 forbids unsolicited CHANGELOG edits, and the active plan `docs/review/review-0_0_11.md` records no changelog obligation for the `optimizer/` folder-pass item. `git diff -- CHANGELOG.md` empty.

---

## Verification (Worker 3)

Shape #5 no-source-edit folder pass. Every gate verified at HEAD `33466db5`.

### Zero-edit proof
- `git diff 252672d1b7c694e857bfe4fa71f1280137d83030 -- django_strawberry_framework/optimizer/` EMPTY.
- `git diff HEAD -- django_strawberry_framework/optimizer/` EMPTY.
- Owned-paths stat `git diff --stat 252672d1… -- django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md` EMPTY — no optimizer source, no test, no GLOSSARY, no CHANGELOG hunk.
- `git status` dirt is entirely `docs/dry/`, `docs/feedback2.md`, `docs/review/*` scratchpads, and `docs/spec-038…` — AGENTS.md #34 concurrent-maintainer / scratchpad work, no tracked optimizer file dirty. No sibling-cycle attribution needed (no dirty path touches the optimizer target).
- `git diff -- CHANGELOG.md` EMPTY.

### Shape-#5 section gates
- All four Worker 2 sections open `Filled by Worker 1 per no-source-edit cycle pattern.` — confirmed.
- Zero High / zero Medium / zero folder-level Low. The one in-scope Low (`walker.py::_connector_only_field` M2M raw `_meta.pk.attname`) is correctly held single-file in `rev-optimizer__walker.md` with verbatim trigger, not re-raised here.
- No GLOSSARY-only fix (none present; would be disqualifying).
- Changelog `Not warranted` cites BOTH AGENTS.md #21 AND active-plan silence; diff empty — accepted.

### Folder reasoning verified at source
- **Export surface.** `__init__.py` `__all__ = ("DjangoOptimizerExtension", "logger")` (sorted, no private leak). `logger` re-exported `from ..` (canonical top-level home of the `"django_strawberry_framework"` literal); consumed by `walker.py:24` + `extension.py:51` via `from . import logger` — both grep-confirmed. `DjangoOptimizerExtension` re-exported from `.extension`, consumed by package root `../__init__.py:25`. `OptimizationPlan`/`plan_optimizations` correctly not re-exported.
- **Import DAG one-way acyclic.** Sibling-import grep per file: leaves with NO `from .` sibling edge = `_context.py`, `field_meta.py`, `hints.py`, `plans.py`, `selections.py` (their imports are `..exceptions`/`..utils`/`..registry`, not siblings). Mid: `walker.py` → `{field_meta, hints, plans, selections}` (+ `from . import logger`). Apex: `extension.py` → `{_context, hints, plans, selections, walker}`. `__init__.py` → `extension` + `..logger`. `selections.py` imported by both walker and extension but imports no sibling back. No back-edge.
- **Shared discriminators ALIASED, not re-implemented.** `is_fragment`/`should_include` defined exactly once (selections.py:273,287). Walker imports both and binds underscore aliases (walker.py:40,45,55-56; `_is_fragment` used at walker.py:1046). Extension does NOT define or re-spell either (grep: no `def is_fragment`/`def should_include`; its `type_condition` mentions at extension.py:879-882 are the converted-selection adapter docstring, not the discriminator) — consumes them transitively via the `selections` helper imports (extension.py:67-76). No drift possible.
- **`_can_elide_fk_id` twin genuinely RESOLVED by `3b4f90c0`.** Commit message + live source confirm: walker.py:867-870 returns the stamped slot if present, else delegates the raw-field fallback to `FieldMeta._from_field_shape(field, is_relation=True).fk_id_elision_eligible` — the same delegation `types/resolvers.py` uses. Predicate now single-sourced in `field_meta.py`. `related_model is None` short-circuit intact before any pk deref. Not a remaining candidate. The `model_for` grep hits in optimizer (`registry.model_for_type`, extension.py:655,1201) are a DIFFERENT method, unrelated to the sibling-cycle `utils/querysets.py::model_for` delegation — no optimizer involvement there.
- **`_target_pk_name` twin correctly KEPT folder-level, NOT forwarded.** Divergent input contracts confirmed at source: `walker.py:873-881::_target_pk_name(field)` takes a field, stamped `target_pk_name` fast-path, then `.related_model` → `._meta.pk.name`; `field_meta.py:232-246::_target_pk_name(model)` takes a model directly with defensive `_meta` read. Both sites `optimizer/`-internal → correctly NOT a project-pass forward. Defer-with-trigger ("walker's raw-descriptor recompute fallback removed") is sound — the field_meta canonical lookup is the early-warning canary.
- **Relation-context argument bundle** is single-file (`walker.py`), correctly deferred at folder level only because it is the dispatch spine; trigger ("planner gains a further per-relation context member beyond `enable_only`") sound. Not forwarded.
- **Nothing forwarded to the project pass from this folder** — both live DRY items are `optimizer/`-internal. Confirmed.

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the optimizer/ folder-pass checkbox in `docs/review/review-0_0_11.md`.
