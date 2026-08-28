# Build: R2 — spec reconciliation (the spec states the current contract; the rationale takes the history)

Spec reference: `docs/SPECS/spec-034-permissions-0_0_10.md` (whole file)
Rationale companion: `docs/SPECS/appx/spec-034-permissions-0_0_10-rationale.md` (whole file)
Build plan: `docs/builder/build-034-permissions-0_0_10.md` (`## Cycle shape` obligation 3; `## R1 outcome`; `## Maintainer-set scope for this cycle`)
Inputs: `docs/builder/bld-034-review-1a-cascade_module.md`, `docs/builder/bld-034-review-1b-composition_pins.md`, `docs/builder/bld-034-review-1c-fakeshop_and_surface.md` (read in full)
Status: final-accepted

**Round shape.** This round lands **no source and no test**. Its whole deliverable is two Markdown files — the spec, rewritten to state the contract that is true at `HEAD` directly and without chronology, and the rationale companion, which takes the history as `**Post-ship:**` bullets. Per `docs/builder/BUILD.md` `### Procedural-closure slices` it therefore carries a combined `## Plan (Worker 1)` + `## Final verification (Worker 1)` block; the Worker 2 build pass and Worker 3 review pass are marked not-applicable with that reason.

---

## Plan (Worker 1)

### The split question, answered

**Not split.** One coherent pass.

`docs/builder/BUILD.md` `### Slice splitting` names two triggers and obliges an answer to both, not a split.

- **Diff shape.** The rewrite touches on the order of fifty sentences across two files. That is large by sentence count and small by review cost: there is no executable surface, no fixture, and no interaction between the two files beyond a set of reference links whose resolution is checked mechanically (`### Verification run` below). The failure mode a split protects against — a reviewer losing the thread of a large code diff — does not apply to prose whose every edit is independently checkable against a cohort finding.
- **Estimated new boundary count: zero.** The round introduces no guard, gate, cap, or rejection path, so it owes no failability proof and carries none of the per-boundary load that makes a large builder cohort unaffordable. The trigger that most often forces a split is absent here.
- **The decisive argument runs the other way.** `docs/builder/worker-1.md` `## Review-round custody`: *a half-reconciled spec is worse than an un-updated one, because the reader cannot tell which half is current.* The headline divergence is a **single contract** — the cascade's post-`0.0.10` hardening — restated at eight sites in three grammars across `## Slice checklist`, `## Goals`, `### Error shapes`, Decision 5, and four `## Edge cases and constraints` bullets. Any split by section cuts that one sentence's homes across two passes and guarantees the half-reconciled state the rule forbids. The same holds for the `cacheable = False` wording (Goal 3 vs the plan-cache edge case) and for the sync-misuse recourse (Decision 10 bullet 1 vs bullet 3 vs `### Error shapes`): in each case the defect *is* that two homes of one contract disagree, so the fix is only a fix if both move together.

Recorded here rather than acted on: had this round been split, the carve would have gone back to Worker 0 rather than being improvised into a second artifact.

### Dispatched findings checklist

One box per finding the three cohorts routed to R2, quoting the finding as the cohort stated it and citing the symbol-qualified path the cohort recorded. Worker 1 both performs and audits these; every tick below is audited in `## Final verification (Worker 1)`.

**From R1a — cascade module, public surface, package tests**

- [x] **A2 / B5 / D5-step-1 — the three-predicate edge scope.** "Edge scope is `_meta.get_fields()` entries with `related_model` present AND `getattr(field, "column", None) is not None` AND NOT `getattr(field.remote_field, "parent_link", False)`" — SUPERSEDED (`c68aecab`). True at `HEAD`: `django_strawberry_framework/permissions.py::_is_cascadable_edge` is `isinstance(field, models.ForeignKey) and getattr(field, "column", None) is not None`.
- [x] **A4 / F13 — `GenericForeignKey` "excluded precisely".** SUPERSEDED (`c68aecab`): `permissions.py::_is_unsupported_forward_edge` + the full-walk preflight at `permissions.py::apply_cascade_permissions #"cannot walk every edge of"`. `GenericRelation` stays skipped.
- [x] **A5 / F14 / D5-step-1 — the MTI `<parent>_ptr` exclusion, with its *Deferred extension* paragraph.** SUPERSEDED (`c68aecab`): parent links cascade; `permissions.py::_is_cascadable_edge` docstring #"MTI ``<parent>_ptr`` parent links included".
- [x] **A7 / B7 / B17 / F16 / F20 — the `has_custom_get_queryset()` hook gate.** SUPERSEDED (`c68aecab`): `grep -c has_custom_get_queryset django_strawberry_framework/permissions.py` = 0; every registered target composes. R1a's instruction to record it as *a recorded rejected alternative re-adopted for a reason the original deliberation did not weigh* is discharged in the rationale.
- [x] **A8b — the unconditional `__isnull` disjunct.** SUPERSEDED (`c68aecab`): `permissions.py::_walk #"if field.null:"`.
- [x] **A10 / A11 / C3 / C9 / D1 / F3 / F4 / F9 — the `ContextVar` seen-set and the never-raise cycle contract.** SUPERSEDED (`c68aecab`): `permissions.py::_cycle_error` + `permissions.py::apply_cascade_permissions #"raise _cycle_error(state, cls)"`, with `fields=[]` the one permitted re-entrant shape. R1a's eight-site, three-grammar flag is the reason this is one box and not eight.
- [x] **A15 / B19 / C8 / D10-bullet-1 — the sync-misuse probe shape and the named recourses.** CONFORMS-in-behaviour / SUPERSEDED-in-description: the cascade *delegates* the whole invocation to `utils/querysets.py::apply_type_visibility_sync`, the guard tests `inspect.isawaitable`, and `permissions.py #"_ASYNC_RECOURSE"` names a sync hook rewrite or `fields=` scoping — not `aapply_cascade_permissions`. Decision 10 bullet 3 already said so, so the spec contradicted itself.
- [x] **A16 / B20 / D10-bullet-2 — `sync_to_async(thread_sensitive=True)` "(the `filters/sets.py` precedent)".** STALE-DESCRIPTION: `permissions.py::aapply_cascade_permissions #"await run_in_one_sync_boundary("` — the shared one-boundary primitive (`spec-040` D17).
- [x] **B2 — Decision 3's module-contents inventory omits the `SyncMisuseError` re-export.** STALE-DESCRIPTION: `permissions.py #"from .utils.querysets import SyncMisuseError as SyncMisuseError"`.
- [x] **B8 / F15 — "the cascade does not defensively rewrite the hook's return (a hook returning a non-row queryset is a consumer bug … not silently absorbed)".** SUPERSEDED (`c68aecab`, `90d1cf14`, `60998b17`): `permissions.py::_validated_target_subquery` rejects sliced / combined / field-`distinct` / grouped / alias-shadowing returns and re-projects the rest to `.values(field.target_field.attname)`. Both of the bullet's worked examples are now wrong in opposite directions.
- [x] **B12 / L1 — Decision 6's Consumer-recipe divergence cites a substring matching zero occurrences, on a premise that has itself inverted.** STALE-DESCRIPTION: `types/resolvers.py::_make_relation_resolver #"return getattr(root, field_name)"` matches 0; the forward-FK branch routes through `types/resolvers.py::_visible_related_object`. Attributed to `841e56d6` by `git log -S`.
- [x] **B14 / F18 / Decision 8 — the nested-alias and hook-return alias rejections are unstated, and the Sharded-callers citation carries a raw `walker.py:212`.** The nested check is `permissions.py::apply_cascade_permissions #"nested walk for"`; the citation is a rule-27 violation in a standing doc and numerically stale.
- [x] **C11 / M2 — `## Error shapes` lists 2 of the 12 error surfaces the helper actually has, and one of the 2 now states the opposite of the truth.** STALE-DESCRIPTION; the ten further shapes are enumerated in R1a census row C11.
- [x] **F12 — composite-PK / composite-FK targets "skipped by the scope test exactly as M2M is".** SUPERSEDED (`c68aecab`): unsupported, preflights closed.
- [x] **F17 / M3 — the queryset-polymorphism bullet is false in the consumer-breaking direction.** SUPERSEDED (`60998b17` for the seal, `c68aecab` for the sliced/combined rejections): the root is sealed and rebuilt, so a consumer `QuerySet` subclass is silently replaced and sliced / combined roots raise. R1a measured all three.
- [x] **F21 — `fields=[]`'s unstated new role** as the one permitted re-entrant shape and the documented cycle-breaking recourse.
- [x] **G1 / L2 — Decision 1 and DoD item 1 carry the pre-archive `docs/spec-034-…` path, and DoD item 1's command exits 2 as written.** STALE-DESCRIPTION; the only executably-false claim in the R1a territory.
- [x] **Test-name census — 7 of 23 spec-named Slice-1 tests absent, each replaced by a pin of the inverted contract.** RENAMED / SUPERSEDED; live names recorded per row in R1a's table.
- [x] **"Neither `## Current state` nor any Decision mentions the sealed visibility boundary at all."** R1a asked for a home for the source-side statement (root sealing, `require_model_rows=False`, the two `render_error` seams).

**From R1b — optimizer cooperation and composition pins**

- [x] **S2-3 — Slice 2's checklist cites `optimizer/walker.py::_target_has_custom_get_queryset` as though it were the `cacheable` rule.** STALE-DESCRIPTION: the rule is `optimizer/walker.py::_plan_prefetch_relation #"plan.cacheable = False"`; the predicate never touches `plan.cacheable`.
- [x] **G3 — `## Goals` item 3 says "the `cacheable = False` **request-scope** rule" while the spec's own plan-cache edge case correctly calls the shipped rule coarser.** STALE-DESCRIPTION, and a live self-contradiction; the rationale records the Revision-2 reword that never reached Goal 3.
- [x] **D11-5 — Decision 11's three-layer table writes `get_queryset` as `(cls, queryset, info)` against a shipped `(cls, queryset, info, **kwargs)`.** STALE-DESCRIPTION: `django_strawberry_framework/types/base.py::DjangoType.get_queryset`.
- [x] **D12-5 — Decision 12's `_build_child_queryset` citation is a rule-27 violation, stale by ~173 lines, and omits `allow_sliced=True`.** STALE-DESCRIPTION: `optimizer/walker.py::_build_child_queryset #"queryset = apply_type_visibility_sync(target_type, queryset, info, allow_sliced=True)"`, added by `spec-045` Decision 5.
- [x] **E4 — the Sharded-callers edge case carries the same raw `walker.py:212`.** STALE-DESCRIPTION; R1b's note that fixing one without the other leaves the class alive is why both moved in this pass, along with a third site.
- [x] **E3 / L3 — the strictness bullet and Slice 2's fourth pin imply `test_strictness_raise_silent_across_cascaded_shape` measures the cascade's lazy-load property; it measures optimizer planning.** Established by R1b's four recorded mutations, not by reading.

**From R1c — fakeshop activation, live coverage, deferred surface**

- [x] **H3 — `## Current state`: "The four products-schema hooks that call it remain comments (Slice 4's uncomment)."** FALSIFIED PREDICTION, must be rewritten: all four are live classmethods (`examples/fakeshop/apps/products/schema.py::CategoryType.get_queryset` and siblings).
- [x] **H4 — `## Current state`: "**The fakeshop activation site is staged.** … carries a commented `apply_cascade_permissions` import and four commented `get_queryset` cascade hooks — one per type, each behind a `TODO-ALPHA-034-0.0.10` marker".** FALSIFIED PREDICTION; H5's parenthetical about the user-read correction stands and was kept.
- [x] **H1–H2, H5–H9 — seven `## Current state` clauses graded dated observations that stand.** Left untouched, deliberately.
- [x] **B10 — "seeded the deterministic private/public chains … through a **module-local helper**".** STALE-DESCRIPTION: the helper is `examples/fakeshop/apps/products/services.py::seed_cascade_split`.
- [x] **A11 — "`Item` / `Entry` `is_private` a per-row `random.choice([True, False])`".** SUPERSEDED: `services.py::seed_data` draws from `random.Random(PRIVACY_STREAM_SEED)`; the superseding change names itself in the source comment.
- [x] **B11 — the Slice 4 re-pin bullet's "(expected small — the suite seeds public fixtures by default)".** STALE-DESCRIPTION, falsified by the rationale's own resolution text.
- [x] **E3-adjacent — "12 across `test_products_api.py` and the in-process `test_schema.py`" is right in its digits and wrong in its subject.** Fixed by stating the population, not by changing 12 to 14 (see `### Population claims measured in this pass`).
- [x] **F1 / F2 / F3 — Decision 1, DoD item 1 (×2 spellings, one inside a load-bearing `--spec` argument), and the `## Doc updates` card-wrap instruction carry the pre-archive path.** STALE-DESCRIPTION; DoD item 1 was the only executably-false claim in the territory.
- [x] **D6 — the opener's "the on-disk version reads `0.0.9` as of this writing".** R1c flagged it as a judgement call rather than a finding: a self-dating clause sitting in the identity paragraph rather than in the vintage-framed `## Current state`. Judged and removed — see `### Spec changes made (Worker 1 only)`.
- [ ] **C5 — Decision 2's `_bind_fieldsets` lands with `TODO-BETA-046-0.1.1`; live name `TODO-BETA-055-0.1.1`.** RENAMED (card-id rot). **Deferred, not performed:** the maintainer escalation in `build-034-permissions-0_0_10.md` `## R1 outcome` rules every card-id spelling out of this cycle's scope, and `KANBAN.md`:398 already homes this site while ruling four spec sites "leave verbatim" *because the source still reads the old id*. Catalogued below.
- [ ] **D3 — Decision 13's `TODO-ALPHA-035-0.0.10` against the opener's `DONE-035-0.0.10`.** RENAMED (card-id rot). **Deferred** for the same reason; `KANBAN.md`:398 names this exact site as `spec-034`'s single clean prefix flip. Catalogued below.
- [ ] **G-i — `TODO-ALPHA-034-0.0.10` ×6 in the spec, per-site graded on the board into three classes.** **Deferred** for the same reason. All six survive this pass byte-identical, verified in `### Verification run`.
- [ ] **B4a — the live staff matrix covers two of four root fields.** SKIPPED, and **not R2's**: it routes to R3, which is running concurrently. No spec edit is owed — R1c established that the spec already states the four-root matrix correctly in `## Slice checklist` Slice 4 box 2 and `## Definition of done` item 10, so R3 makes the code match the spec rather than the other way round.
- [ ] **M1 — the dead `view_<model>` branch (escalated, contract-level).** Not a spec edit: R1c escalated it to the maintainer with three resolution paths, and the shipped behaviour is spec-conformant either way. Catalogued below.
- [ ] **M2 — 18 rotted card-id occurrences in `examples/fakeshop/apps/products/schema.py`.** Not R2's: source, and the maintainer escalation. Catalogued below.
- [ ] **E15 — the `KANBAN.md` M2M/reverse follow-up surfacing.** Not graded by R1c and not reachable from this cycle (board edits are out of scope). Catalogued below.

**Escalations R1a raised rather than decided** (recorded, not performed — both are maintainer calls on source this round may not touch):

- [ ] **R1a M1 — `permissions.py::_is_unsupported_forward_edge #"getattr(field, \"is_relation\", False)"` is the catalogued `getattr`-default fail-open shape.** No live exploit path (the only input population is `model._meta.get_fields()`, every member of which defines `is_relation`). Catalogued below.
- [ ] **R1a DRY D1 — `permissions.py::_cascadable_edges` has one reader and `::_cascadable_edge_names` has zero production readers.** Catalogued below.

---

## Build report (Worker 2)

**Not applicable.** This round lands no source and no test, so there is no Worker 2 build pass, no diff over `.py` files, no `### Files touched` beyond the two spec-family Markdown files Worker 1 owns, no failability proof (the round introduces no boundary), no hot-path number (`build-034-permissions-0_0_10.md`: "R1 and R2 land no source and declare none"), and no floor-verification scope (the same plan declares `none` for R2; the floor itself is stated canonically in `docs/builder/BUILD.md` `## Floor verification` and is not restated here). No `ruff` run was owed and none was made.

---

## Review (Worker 3)

**Not applicable, same reason.** `docs/builder/BUILD.md` `### Isolation is non-waivable` binds the builder/reviewer pair over a *source diff*; there is none. `docs/builder/BUILD.md` `### Procedural-closure slices` licenses the single Worker 1 pass, and Worker 1's audit of its own `### Dispatched findings checklist` — performed in `## Final verification (Worker 1)` against the shipped source each box cites — is the check that stands in its place. Worker 0 reads that checklist.

---

## Final verification (Worker 1)

### Spec changes made (Worker 1 only)

Every edit, with the spec section, the cohort finding that triggered it, and a one-line reason. All are in `docs/SPECS/spec-034-permissions-0_0_10.md` unless marked otherwise.

**Header and status lines** (`docs/builder/worker-1.md` `## Spec status-line re-verification`, run at the start of this spawn)

| # | Section | Trigger | Change and reason |
|---|---|---|---|
| 1 | Opening paragraph | R1c D6 | Dropped "(the on-disk version reads `0.0.9` as of this writing — the `0.0.9` cut has landed)". The version boundary it supported — "This card's slices land within the `0.0.10` line and never bump the version themselves" — is a complete statement without it, and the parenthetical was the only clause in the identity paragraph that a reader had to date before trusting. |
| 2 | `Status:` line | re-verification | Read end-to-end and left unchanged: it correctly reads SHIPPED (`0.0.10`), names the released `CHANGELOG.md` heading, and already gives the shipped-spec unticked-boxes convention. |
| 3 | `## Slice checklist` preamble | R1c H3/H4 class | "Boxes are unticked because the work has not started." → the shipped-spec convention the header already states. A false completion claim in a checklist preamble gets none of `## Current state`'s vintage licence. |

**The cascade-hardening divergence class** (R1a; attributions `c68aecab`, `90d1cf14`, `1dd9273a` / `60998b17`, `dc00f4a6`)

| # | Section | Trigger | Change and reason |
|---|---|---|---|
| 4 | `## Slice checklist` Slice 1 box 1 | A2, A4, A5, A7, A8b | Rewrote the scope test to the shipped `isinstance(field, models.ForeignKey)` predicate, MTI parent links **in** scope, GFK / composite **unsupported** with a preflight, every registered target composing, and the `__isnull` disjunct conditional on `field.null`. One box carried five superseded clauses. |
| 5 | `## Slice checklist` Slice 1 box 2 | A10, A11 | Rewrote the cycle box: frozen `_TraversalState`, path-rich fail-closed raise, `fields=[]` the one permitted re-entrant shape, per-frame token reset. |
| 6 | `## Slice checklist` Slice 1 boxes 3–5 | R1a C11, A15, A16 | Added the non-iterable / non-string-entry and unsupported-forward-relation `fields=` rejections; replaced the "probe shape" wording with the delegation to `apply_type_visibility_sync`; replaced the `filters/sets.py` precedent with `run_in_one_sync_boundary`. |
| 7 | `## Goals` item 1 | D1 | "partial-narrow on cycle break, never a raise" → the fail-closed, path-rich contract; "single-column forward scope" → "single-column concrete forward scope". |
| 8 | `### From django-graphene-filters` | A2, A8b, A10 | The "same four invariants" sentence described three mechanisms the package has since tightened. Now names the four invariant *axes* and states each tightening in a following paragraph. |
| 9 | `### Explicitly do not borrow` | A7 | Replaced "**The unconditional target call**" — which the package now performs — with the divergence that is real at `HEAD`: upstream's silent skip of an uncomposable forward relation. |
| 10 | `## User-facing API` | A10 | "with the `ContextVar` seen-set breaking cycles" → "with the `ContextVar` traversal state failing a cycle closed". |
| 11 | `### Error shapes` | C11 / M2 | Rewrote the section as the helper's complete inventory, grouped by when in the call each rejection fires: `fields=` validation (4), walk preconditions (5 incl. the cycle), the hook-return contract (2), sync/async (1), and what never raises (2). "Cycles never raise" stated the opposite of the shipped contract. |
| 12 | `### Decision 3` | B2 | Added the `SyncMisuseError` re-export to the module-contents inventory, with the reason it adds no package-root name. |
| 13 | `### Decision 5` heading | A7 | `has_custom_get_queryset()` gate → **every registered target composes**. The heading asserted an inverted contract. Its slug moved with it, swept across 13 spec anchors and 4 rationale anchors plus both files' `## Decision 5` headings (see `### Verification run`). |
| 14 | `### Decision 5` lead-in | F17, R1a's "no Decision mentions the sealed boundary" | Added a **Root sealing** paragraph *before* the numbered steps rather than as a step 0, so every existing "step 1" / "step 4" / "step 5" cross-reference in both files keeps its referent. |
| 15 | `### Decision 5` step 1 | A2, A4, A5, F12, F13, F14 | Rewrote to the shipped predicate, with the unsupported-forward-relation classification as a second paragraph. |
| 16 | `### Decision 5` step 3 | A7, B7 | "Hook gate" → "Every registered target composes", carrying the security reason (a registered proxy type's filtered `_default_manager` *is* its visibility policy). |
| 17 | `### Decision 5` step 4 | B8, F15, A15 | Added the delegation to the shared boundary, the hook-return validation, the `.values(target_field.attname)` re-projection, and the conditional `__isnull`. |
| 18 | `### Decision 5` step 5 | A11, F21 | Rewrote to the frozen state, the fail-closed raise with its reason, the `fields=[]` recourse, and ancestry-not-visit-count framing. |
| 19 | `### Decision 6` divergence block | B12 / L1 | Replaced the zero-match citation and its inverted premise with the live mechanism (`types/resolvers.py::_visible_related_object` via `::_custom_visibility_type`) and the stronger reason the conclusion now rests on: a non-null FK field cannot return `None`. |
| 20 | `### Decision 8` | B14 | Added the two alias **enforcement** rejections (nested application off the root alias; hook return explicitly routed off it, with an unrouted return repinned) as a new sub-list. |
| 21 | `### Decision 9` | B17, C11, F20 | Added the non-iterable / non-string-entry rejections and the dedicated unsupported-forward-relation error; narrowed "no registered type **or no custom hook**" to the surviving half. |
| 22 | `### Decision 10` bullets 1–2 | B19, A15, A16, C8 | Bullet 1 now states the delegation, `inspect.isawaitable`, and the two recourses that work — reconciled to bullet 3, which the spec had been contradicting. Bullet 2 names `run_in_one_sync_boundary`. |
| 23 | `### Decision 10` bullet 2 tail | A10 | "seen-set" → "traversal state" in the asgiref context-copy sentence. |
| 24 | `## Edge cases` self-referential FK | F3 | Fails closed; `fields=[]` recourse named. |
| 25 | `## Edge cases` mutual cascade A↔B | F4 | Fails closed with the full path; the reason the partial narrow was unsafe stated. |
| 26 | `## Edge cases` frame-exit discard | A10 | Mechanism reworded from set-membership to ancestry; the sibling-edge conclusion is unchanged and correct. |
| 27 | `## Edge cases` `ContextVar` isolation | A10 | Same mechanism reword; the asgiref guarantee and its pin are unchanged. |
| 28 | `## Edge cases` secondary-type-as-root | F9 | Termination is now by fail-closed raise naming both types, not by silent un-narrowing. |
| 29 | `## Edge cases` composite-PK/FK | F12 | Skipped → unsupported, preflights closed, with the reason it differs from M2M. |
| 30 | `## Edge cases` GFK / `GenericRelation` | A4, F13 | Split the bullet by whether skipping can hide a leak; the backing `content_type` FK's status stated. |
| 31 | `## Edge cases` MTI parent link | A5, F14 | "excluded by design" → cascades, with the leak that motivated the flip; the *Deferred extension* paragraph deleted (the extension shipped as the default, so the paragraph is prose a later decision falsified). |
| 32 | `## Edge cases` hook-return contract | F15 | Rewritten to validated-and-normalized, with the rejected shapes, the re-projection, and the alias-shadow security argument. All four worked examples were wrong. |
| 33 | `## Edge cases` abstract-base hooks | F16 | Conclusion kept, mechanism replaced: participation is by registration, not by hook detection through abstract bases. |
| 34 | `## Edge cases` queryset-polymorphism | F17 / M3 | Rewritten around the seal: framework-owned plain `QuerySet` returned, sliced and combined roots rejected, `.values()` root supported; `only()` and ordering survival kept. |
| 35 | `## Test plan` Slice 1 | Test-name census | Repointed all seven absent names to their live pins and added rows for the boundaries the census surfaced (root seal, hook-return battery, alias-shadow, nested-alias). |

**The composition-pin description defects** (R1b)

| # | Section | Trigger | Change and reason |
|---|---|---|---|
| 36 | `## Slice checklist` Slice 2 box 1 | S2-3, E3/L3 | Repointed the `cacheable` citation to `_plan_prefetch_relation`; said what the strictness pin actually detects. |
| 37 | `## Goals` item 3 | G3 | "request-scope rule" → the custom-hook rule, with the presence-not-content clause the edge case already carried; the zero-round-trip clause now names its absolute-count proof. |
| 38 | `## Key glossary references`, `## Current state` bullet 2 | G3 class | Two further homes of the same "request-scope" phrasing, found by sweeping the phrase rather than the finding's line. |
| 39 | `### Decision 11` table row 1 | D11-5 | `(cls, queryset, info)` → `(cls, queryset, info, **kwargs)`. |
| 40 | `### Decision 12` bullet 2 | D12-5 | Raw `(walker.py:212-214)` → a rule-27 `path::Symbol #"substring"` citation; `allow_sliced=True` added with its `spec-045` attribution. |
| 41 | `## Edge cases` sharded callers | E4 | Raw `walker.py:212` dropped; the symbol citation stands alone. |
| 42 | `## Edge cases` strictness | E3 / L3 | Says which pin carries which property, and that the two are complementary. |
| 43 | `## Test plan` Slice 1 harness note | R1b out-of-territory note | The raw `examples/fakeshop/config/settings.py` "line ~116" became a reference-style link; "Build it on the … harness" reworded to "borrow the in-test alias / router pattern", with the pin's real home named. |

**The fakeshop / surface defects** (R1c)

| # | Section | Trigger | Change and reason |
|---|---|---|---|
| 44 | `## Current state` bullet 1 | H3 | The falsified prediction rewritten to the live shape. |
| 45 | `## Current state` fakeshop bullet | H4 | Rewritten to the live shape, **keeping** H5's user-read parenthetical and the `TODO-ALPHA-034-0.0.10` spelling — the marker is now named as one the file does *not* carry, which is a present-tense observation and leaves the escalated card-id spelling byte-identical. |
| 46 | `### Decision 1` | F1 | Pre-archive path → `docs/SPECS/…`, with the companions' `appx/` home stated. |
| 47 | `## Doc updates` card-wrap bullet | F3 | "confirm the spec reference points at `docs/spec-034-permissions-0_0_10.md`" → "at this spec file". The cited substring `to Done with the next` and every card id in the bullet are untouched. |
| 48 | `## Definition of done` item 1 | F2 | Both path spellings corrected, including the one inside the `--spec` argument. The command now exits 0 (`### Verification run`). |
| 49 | `## Definition of done` items 2–3 | A7, A11, G2, G3 | Item 2's walk enumeration now matches the shipped walk; item 3's "partial-narrow cycle break" is the fail-closed contract. |
| 50 | `## Test plan` Slice 4 last bullet | B11 | The "(expected small …)" parenthetical replaced by what the re-pin actually was, with the seeder facts that made it load-bearing. |

**Rationale companion** (`docs/SPECS/appx/spec-034-permissions-0_0_10-rationale.md`) — appended `**Post-ship:**` bullets, plus three in-place corrections

| # | Location | Change |
|---|---|---|
| 51 | Decision 1 `### Changes this Decision underwent` | The archive sweep, why link definitions moved and prose spellings did not, and DoD item 1's exit-2 command. |
| 52 | Decision 3 | The `SyncMisuseError` re-export (`c68aecab`). |
| 53 | Decision 5 | The five-point hardening as one bullet with six sub-bullets (scope predicate, MTI, GFK/composite, `__isnull`, cycles, the mechanism name), the eight-site three-grammar note, and the measured five-row revert. |
| 54 | Decision 5 | The re-adopted rejected alternative, recorded as R1a asked: re-adopted for a security reason the dead-SQL deliberation never reached, **not** as a rejection that was wrong on its own terms. |
| 55 | Decision 5 | The sealed visibility boundary (`1dd9273a` / `60998b17`, documented after the fact by `spec-045`): root rebuild and the hook-invocation move. |
| 56 | Decision 5 | The inverted hook-return contract (`c68aecab`, `90d1cf14`, `60998b17`), with `90d1cf14`'s own security argument preserved. |
| 57 | Decision 6 | The zero-match citation and its inverted premise (`841e56d6`), plus why no gate can see the defect. |
| 58 | Decision 7 | Goal 3's un-propagated Revision-2 reword, and the strictness-pin attribution with R1b's four-mutation measurement. |
| 59 | Decision 8 | The two alias-enforcement rejections; the three raw-line citations. |
| 60 | Decision 9 | The `## Error shapes` pre-ship gap (a Revision-8 change that never reached the section), the dedicated unsupported-relation error, and the hookless-target half. |
| 61 | Decision 10 | The recourse text reaching bullet 3 but not bullet 1 or `## Error shapes`; probe → delegation; `run_in_one_sync_boundary`. |
| 62 | Decision 11 | The one-term-short signature in the table. |
| 63 | Decision 12 | The dependency surviving the refactor its citation did not; the Slice 2 `cacheable` symbol. |
| 64 | `## Non-Decision deliberation` | Six appended bullets: the `## Current state` clause-by-clause judgement (Slice 0 explicitly left this one for the reconciliation pass); the `### Error shapes` inventory; the borrowing-posture rewrite; and the three Risks-body corrections. |
| 65 | `## Risks and open questions` preamble | Amended "verbatim" to say the body moved verbatim and was corrected once afterwards, naming where the corrections are recorded — otherwise the preamble's own claim would be false. |
| 66 | `## Risks` Live-suite-sensitivity item | Three in-place corrections: `random.choice` → the fixed-seed stream; "module-local helper" → `services.seed_cascade_split` (which contradicted the same file's Revision 8); the "12" count replaced by its population. |

**Deliberately not changed**

- Every `TODO-ALPHA-*` / `TODO-BETA-*` spelling in both files, in every grammar. Verified byte-identical in `### Verification run`.
- The seven `## Current state` clauses R1c graded dated observations (H1–H2, H5–H9). `docs/builder/BUILD.md` `### `## Current state`: observations stand, predictions do not` — a falsified observation stays because the header dates it.
- `## Edge cases`' plan-cache, FK-id-elision, `Meta.fields`-excluded-edges, empty-visible-set, nullable-FK, non-nullable-forward-FK-drop, and re-entrancy/idempotence bullets: all CONFORMS across R1a and R1b, and R1a verified the re-entrancy bullet against the sealed root by temp test rather than assuming it. Correct text is not churned.
- `## User-facing API`'s `request_from_info` sentence (R1c L2: the hooks take the same *path*, not the same *call*, and a consumer example must not import a private helper — verified and rejected, no change recommended).

### Verification run

Every command below was run in this pass; the output is quoted as produced.

**Glossary gate** — unchanged count, which is the expected result: this round moved no term's only link.

```shell
$ uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-034-permissions-0_0_10.md
OK: 42 terms - all have glossary entries and at least one spec link.
# exit 0
```

**Citation gate** — unchanged, expected: `scripts/check_citations.py` scopes to `path::Symbol` citations in `.py` files and `KANBAN.md`, and this round wrote neither.

```shell
$ uv run python scripts/check_citations.py --check
OK: 857 citations resolve (738 in 431 .py files, 119 in KANBAN.md).
# exit 0
```

**Link-def scaffold check**, both files:

```shell
$ uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-034-permissions-0_0_10.md docs/SPECS/appx/spec-034-permissions-0_0_10-rationale.md
# no output, exit 0
```

**Anchors, ref/def parity, canonical headers, disk-exists** — one script over both files, run before and after the round; the "after" output:

```text
=== docs/SPECS/spec-034-permissions-0_0_10.md ===
in-page anchors used: 24  unresolved: []
ref uses: 284 occurrences / 96 distinct; defs: 96
  used-without-def: []
  def-without-use : []
  canonical headers present in order: True
  def paths missing on disk: []
  cross-file anchors unresolved: []
=== docs/SPECS/appx/spec-034-permissions-0_0_10-rationale.md ===
in-page anchors used: 13  unresolved: []
ref uses: 104 occurrences / 51 distinct; defs: 51
  used-without-def: []
  def-without-use : []
  canonical headers present in order: True
  def paths missing on disk: []
  cross-file anchors unresolved: []
```

Five reference definitions were added to keep parity: `[resolvers]`, `[spec-045]`, `[fakeshop-settings]` in the spec; `[spec-034-dod]`, `[spec-034-goals]`, `[spec-045]`, `[filters-sets]` in the rationale. Each sits in the canonical group for the **target's** location and is alphabetical within it.

**The Decision 5 heading rename, verified as a sweep rather than an edit.** Renaming the heading moves its slug, and 16 anchors pointed at it across the two files with no foreign readers (`grep -rln 'decision-5--the-cascade-walk' --include='*.md' .` outside the pair returned nothing):

```text
old slug remaining: spec 0, rationale 0
new slug: spec 13, rationale 4
headings: both files now read "…registry primary lookup, every registered target composes, subquery intersection"
old heading text remaining: 1 occurrence, in the rationale's Revision 1 bullet — correct as history, kept
```

**DoD item 1's command, the round's one executably-false claim**, before and after:

```shell
# as the spec wrote it, before this round
$ uv run python scripts/check_spec_glossary.py --spec docs/spec-034-permissions-0_0_10.md
error: missing file: docs/spec-034-permissions-0_0_10.md
# exit 2
# as the spec writes it now
$ uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-034-permissions-0_0_10.md
OK: 42 terms - all have glossary entries and at least one spec link.
# exit 0
```

**Byte and line counts**

| File | Before | After | Delta |
|---|---|---|---|
| `docs/SPECS/spec-034-permissions-0_0_10.md` | 112,241 bytes / 607 lines | 128,905 bytes / 655 lines | +16,664 / +48 |
| `docs/SPECS/appx/spec-034-permissions-0_0_10-rationale.md` | 69,448 bytes / 396 lines | 93,722 bytes / 434 lines | +24,274 / +38 |

The corpus ratchet in `docs/builder/BUILD.md` binds `BUILD.md`, `ARTIFACT.md` and the four role files; this round edits none of them. Spec growth is expected here and is where it should be: `### Error shapes` went from 5 bullets to 14 because it was listing two of the helper's error surfaces.

### Line-conservation audit

`docs/builder/bld-034-slice-0-rationale_extraction.md` caught a duplicated bullet that every byte count was blind to, and a rewrite pass of this size is exactly where that recurs. Four independent checks, all clean:

- **No duplicated content line.** `awk 'length($0)>60' <file> | sort | uniq -d` — empty for both files.
- **No duplicated link definition and no duplicated heading.** Empty for both, except the rationale's three per-Decision structural headings (`### Justification (moved from the spec)`, `### Alternatives considered (and rejected)`, `### Changes this Decision underwent`), which are one per Decision by design.
- **Section conservation against pristine `HEAD`.** All 16 `##` sections and all 13 `### Decision N` headings present, same names, same order.
- **Bullet conservation per section**, current vs `git show HEAD:…` (read-only, no `checkout` / `stash`):

| Section | HEAD | Now | Expected |
|---|---|---|---|
| `## Edge cases and constraints` | 24 | 24 | every rewrite was 1:1 |
| `### Error shapes` | 5 | 14 | the deliberate expansion |
| `## Definition of done` numbered items | 14 | 14 | items corrected in place |
| `## Test plan` bullets | 38 | 41 | +3 rows for boundaries the census surfaced |
| `## Slice checklist` `- [ ]` boxes | 21 | 21 | boxes rewritten, none added or dropped |

### Population claims measured in this pass

`docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on prose`, and R1a's warning that one contract can wear three grammars. Every number below was produced by the command beside it, at the moment it was written.

- **The cycle contract's spellings in the spec, before the rewrite** — `grep -o -F` per spelling, counting occurrences: `never a raise` 2, `partially-narrowed` 3, `partial narrow` 1, `un-narrowed` 1, `Cycles never raise` 1, `seen-set` 16. A grep for any one misses the others; R1a's eight *sites* and these spellings are different populations of the same defect, which is why the checklist carries them as one box rather than eight.
- **Card-id spellings in the spec, after the rewrite** — `grep -ohE 'TODO-(ALPHA|BETA|STABLE)-[0-9]{3}[A-Za-z0-9._-]*' | sort | uniq -c`: `TODO-ALPHA-033-0.0.10` 1, `TODO-ALPHA-034-0.0.10` 6, `TODO-ALPHA-035-0.0.10` 1, `TODO-BETA-046-0.1.1` 2. Identical to R1c's pre-round census (`034` ×6 at the six sites it enumerated; `035` ×1; `046` ×2), so no spelling moved.
- **The re-pin population, re-derived.** Sweeping three tokens (`activated cascade`, `post-cascade`, `spec-034`) and attributing each hit to its enclosing `def test_`, excluding the six new cascade tests: **13** in `examples/fakeshop/test_query/test_products_api.py` and **2** in `examples/fakeshop/apps/products/tests/test_schema.py`. R1c's grammar found 12 in the first file. Both readings are defensible and neither is the rationale sentence's original subject, which was at-risk *assertions*. Three numbers for one population is the argument for stating the population instead, which is what the rationale now does — R1c's own recommendation, and the reason the fix is not `12` → `14`.

### Foreign-citation enumeration and disposition

`AGENTS.md` rule 27's `path #"unique substring"` form breaks silently on a reword **and on a reflow**, and no gate sees it — `scripts/check_citations.py` is `path::Symbol`-only with `docs/` out of scope. Swept before and after the round with `grep -rn 'spec-034-permissions-0_0_10\.md[^)]*#"' --include='*.md' --include='*.py' .` (excluding `docs/shadow/`), then each cited substring checked with `grep -c -F` against both files.

| Citing site | Cited substring | Lives in | Touched by this round? | Disposition |
|---|---|---|---|---|
| `KANBAN.md`:398 | `#"The `0.0.10` patch line is shared with"` | spec, Decision 13 | **No** — verified `grep -c -F` = 1 after the round | Resolves. Decision 13 was not edited; the escalated `TODO-ALPHA-035-0.0.10` spelling in the same sentence is untouched. |
| `KANBAN.md`:398 | `#"but the live kanban card is"` | rationale, Decision 2 justification | No | **Already dangling before this round** — Slice 0's move carried the sentence into the companion. R1c flagged it; this round cannot repair it (`KANBAN.md` is out of scope). Catalogued. |
| `KANBAN.md`:398 | `#"Stale card-id reference in `TODAY.md`"` | rationale, Risks body | No | Same class: moved by Slice 0, cited against the spec. Catalogued. |
| `KANBAN.md`:398 | `#"so `<NNN>` is"` | rationale, Decision 1 justification | No | Same class. Catalogued. |
| `KANBAN.md`:398 | `#"to Done with the next"` | spec, `## Doc updates` card-wrap bullet | **Edit in the same bullet, not in the substring** | Resolves. The path spelling changed four clauses away; `grep -c -F 'to Done with the next'` = 1 after the round, on one line, unreflowed. |
| `docs/builder/DONE/build-029-consumer_dx_cleanup-0_0_9.md`:324 | `#"is scalar-only (spec-029 Decision 10)"` | spec, `## Edge cases` non-nullable-forward-FK bullet | **No** — that bullet is CONFORMS across R1a F11 and R1b E5 and was deliberately not churned | Resolves, `grep -c -F` = 1. |

**One board claim this sweep falsified, which cannot be repaired here.** `KANBAN.md`:402 states "`docs/SPECS/spec-034-permissions-0_0_10.md` no longer carries `scalar-only` anywhere and is DISCHARGED". It does: one occurrence, in the non-nullable-forward-FK edge case, which is the very substring `build-029` cites. The claim was false before this round and is false after it. Catalogued.

**Nothing this round rewrote sits under a foreign `#"substring"` citation.** Five of the six citation sites are untouched text; the sixth is a bullet edited outside its cited substring, on the same line.

### Dispatched findings checklist — audit

Every `- [x]` above was re-checked against the shipped source it cites, not against my own edit. The audit is the reason for the box-per-contract shape: a box that quotes the cohort's finding and cites the symbol can be re-derived without re-reading the diff.

- **Ticked and landed: 34 boxes** (`grep -c '^- \[x\]'` over this section — measured as this line was written, not carried from the plan). Each names a spec section that now states the shipped contract; the section-by-section record is `### Spec changes made (Worker 1 only)` rows 1–50, and the matching `**Post-ship:**` bullet is rows 51–66.
- **Left `- [ ]` with a recorded reason: 9 boxes** (`grep -c '^- \[ \]'`, same scope; 34 + 9 = 43 dispatched), all of them out of this round's authority rather than unfinished work — 3 card-id sites the maintainer escalation freezes, 1 SKIPPED contract owned by R3, 2 R1c escalations (M1 dead branch, M2 source card-id rot), 1 board-surfacing claim (`E15`), and 2 R1a escalations (the fail-open `getattr` shape, the DRY existence challenge). Each is a catalog bullet below.
- **No box was ticked whose contract did not land**, and no landed contract was left un-ticked. The three cohorts recorded no on-disk required-amendment list beyond their `### Notes for Worker 1 (spec reconciliation)` sections, which were walked bullet by bullet; `docs/builder/worker-1.md` `## Review-round custody`'s "confirm each builder's on-disk required-amendment list was discharged" is satisfied by that walk, there being no builder pass in R1.

### Deferred work catalog

Everything this round found that its scope forbids fixing. The final gate assembles the full catalog; this is R2's contribution.

**Card-id rot — one coupled class, escalated to the maintainer**

- **`examples/fakeshop/apps/products/schema.py` carries 18 rotted card-id occurrences** — `TODO-BETA-046-0.1.1` ×7, `TODO-BETA-047-0.1.2` ×5, `TODO-BETA-049-0.1.3` ×6 — beside one **correct** `TODO-BETA-062-0.1.5` that must not be swept. Live referents: `TODO-BETA-055-0.1.1` / `-056-0.1.2` / `-058-0.1.3`. Source: `bld-034-review-1c-fakeshop_and_surface.md` census G-iii, finding M2. Deferred because `build-034-permissions-0_0_10.md` `## R1 outcome` escalates it: `KANBAN.md`:398 rules four *spec* sites "leave verbatim" **because the source still reads the old id**, so the spec-side and source-side halves must move together, and `KANBAN.md` is outside this cycle's maintainer-set scope. Home it on whichever card next legitimately opens that file, alongside the already-homed `django_strawberry_framework/types/definition.py`:69 site (`KANBAN.md`:250).
- **The spec's own card-id sites survive this round byte-identical** — `TODO-ALPHA-034-0.0.10` ×6, `TODO-BETA-046-0.1.1` ×2, `TODO-ALPHA-035-0.0.10` ×1, `TODO-ALPHA-033-0.0.10` ×1 — under the same escalation. `KANBAN.md`:398's per-site grading (class (a) de-tense, class (b) leave verbatim, class (c) clean prefix flip) is the ruling to apply, and applying it needs the source half to move in the same pass. Source: R1a's out-of-territory note, R1c census G-i.

**Citations this cycle broke or found broken, none repairable here** (`KANBAN.md` is out of scope)

- **`KANBAN.md`:398 cites three substrings that Slice 0's rationale move carried out of the spec**: `#"but the live kanban card is"`, `#"Stale card-id reference in `TODAY.md`"`, and `#"so `<NNN>` is"`. All three now live in `docs/SPECS/appx/spec-034-permissions-0_0_10-rationale.md`; the board's citations dangle. Source: `bld-034-review-1c` (which found the first) plus this round's before/after sweep (which found the other two). The repair is a path swap in the board item, not a reword.
- **`KANBAN.md`:402's "spec-034 … no longer carries `scalar-only` anywhere and is DISCHARGED" is false.** One occurrence survives, in the `## Edge cases` non-nullable-forward-FK bullet, and it is exactly the substring `docs/builder/DONE/build-029-consumer_dx_cleanup-0_0_9.md`:324 cites. Source: this round's foreign-citation sweep. The board item should be reopened or its discharge re-scoped.

**Source-side items the cohorts escalated rather than dispatched**

- **`django_strawberry_framework/permissions.py::_is_unsupported_forward_edge #"getattr(field, \"is_relation\", False)"`** is the catalogued `getattr`-default fail-open shape on the walk's fail-closed-vs-skip decision, filed Medium by `bld-034-review-1a` finding M1. No live exploit path: the only caller is `permissions.py::_edge_plan`, whose sole input is `model._meta.get_fields()`, every member of which defines `is_relation` as a class attribute — and the two predicates beside it on the same line use plain attribute access, so the one `getattr` is inconsistent with its own line. Resolution paths R1a offered: read `field.is_relation` directly, or leave it and record the closed-population argument in the docstring so a later reader does not "fix" it into a real fallback.
- **`permissions.py::_cascadable_edges` and `::_cascadable_edge_names` are a two-level indirection with zero production readers** (`bld-034-review-1a` DRY finding D1, raised as an existence challenge, not decided). Every production path calls `_edge_plan(model)` directly; the only call sites of `_cascadable_edge_names` are three in `tests/test_permissions.py`. Low value; should gate nothing.
- **The `view_<model>` branch is dead in all four fakeshop hooks** — identical to the fall-through it precedes, so it cannot change the result, and it costs a permission-table read per request per type (`bld-034-review-1c` finding M1, escalated as contract-level). It is spec-conformant behaviour, and R1c's ordering constraint matters: **R3's staff rows should land before any collapse**, so the collapse is performed against a suite that can detect a mistake in it. Three resolution paths recorded in R1c.

**Coverage and doc obligations outside this cycle's reach**

- **The prefetch-child alias behaviour is described in a standing doc and asserted by nothing** (`bld-034-review-1b` finding L2). `tests/optimizer/test_multi_db.py` has zero `cascad` occurrences and no `FAKESHOP_SHARDED`-gated file exercises the cascade inside a prefetch child. Not a SKIPPED contract — the spec claims no pin for that bullet — but a future `FAKESHOP_SHARDED`-gated row asserting the prefetch child's `.db` would close it.
- **`examples/fakeshop/apps/products/services.py::seed_cascade_split` has no per-app test** (`bld-034-review-1c` finding L1). Every other public helper in the module is covered; example apps sit outside the `fail_under` gate, so this is a test-surface asymmetry rather than a coverage gap.
- **`utils/querysets.py::_seal_or_defect`'s docstring says "The cascade (`require_model_rows=False`) keeps its own slice rejection in `permissions.py::_validated_target_subquery`."** True for the *hook return*; the **root** slice rejection lives in `permissions.py::_validate_root_queryset`. A one-clause docstring imprecision in a source file this round may not touch (R1a, out-of-territory note).
- **`docs/README.md`'s "Coming next `0.0.10`" line is not re-derivable at `HEAD`** and was graded SUPERSEDED by four later cuts rather than a `034` gap (`bld-034-review-1c` census E7). Recorded so a later reader does not re-open it as a missed doc obligation.
- **The `KANBAN.md` M2M / reverse-relation cascade follow-up surfacing** (`## Doc updates` Slice 5, census E15) could not be established by R1c and cannot be checked or performed here — board edits are outside the cycle's maintainer-set scope. The spec's `## Non-goals` and `## Out of scope` both still say no follow-up card exists.
- **`docs/GLOSSARY.md`'s `apply_cascade_permissions` entry already carries the hardened contract** (R1c's out-of-territory note; corroborated by R1a against `docs/README.md`). No obligation follows for this cycle — recorded as the evidence that the standing docs were updated with the hardening and only the archived spec was left behind, which is this round's whole subject.

### Summary

`spec-034` now states the contract that is true at `HEAD` — directly, with no `**Post-ship:**` marker, no "as of", no revision tag, and no amendment block anywhere in it. A reader of the spec alone comes away with the shipped cascade contract and no sense that it ever said otherwise. The rationale companion took the history: fourteen `**Post-ship:**` entries under eleven Decisions plus six under `## Non-Decision deliberation`, each naming the shipped behaviour, what the spec used to say, and the commit / card / spec the cohorts attributed it to.

Thirty-four of the forty-three dispatched findings landed in the spec, counted by `grep -c` over the checklist rather than carried forward from the plan. The nine left open are all out of this round's authority — three card-id sites frozen by a maintainer escalation whose two halves are coupled across a file this cycle may not touch, one SKIPPED contract owned by the concurrent R3 cycle, and five escalations or board items — each with a one-line reason above and a catalog bullet.

Every gate that could see this round is green and unchanged (`OK: 42 terms`, `OK: 857 citations resolve`, scaffold exit 0), every anchor and reference in both files resolves with exact ref/def parity, the one executably-false claim in the spec now exits 0, and the line-conservation audit found no duplication across four independent checks.

Final status: `final-accepted`.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
