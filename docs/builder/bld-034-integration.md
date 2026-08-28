# Build: cross-slice integration pass — `034` residual-reconciliation cycle

Spec reference: `docs/SPECS/spec-034-permissions-0_0_10.md` (whole file)
Rationale companion: `docs/SPECS/appx/spec-034-permissions-0_0_10-rationale.md` (whole file)
Build plan: `docs/builder/build-034-permissions-0_0_10.md`
Inputs: `docs/builder/bld-034-slice-0-rationale_extraction.md`, `bld-034-review-1a-cascade_module.md`, `bld-034-review-1b-composition_pins.md`, `bld-034-review-1c-fakeshop_and_surface.md`, `bld-034-review-2-spec_reconciliation.md`, `bld-034-review-3-code_repair.md` (all read in full, in cycle order)
Status: final-accepted

**Pass shape.** This pass lands **no source and no test**. Per `docs/builder/BUILD.md` `### Procedural-closure slices` it carries a combined `## Plan (Worker 1)` + `## Final verification (Worker 1)` block; `## Build report (Worker 2)` and `## Review (Worker 3)` are marked not-applicable with that reason.

**What the cycle's shape does to this pass, said once.** Only **one** round landed executable bytes — R3, `examples/fakeshop/test_query/test_products_api.py`, `+95 / -12`, no production source. The classic cross-slice scan (duplicated helpers across slices, inconsistent error handling between slices, misplaced responsibilities between modules touched by different slices) therefore has a **single-round surface**, and several of its questions are structurally unanswerable rather than answered clean. Each such check below says so and says why, rather than reporting a vacuous check as a passing one — `BUILD.md` `### Fail-open shapes`: a control that cannot fail reads exactly like a passing proof.

---

## Plan (Worker 1) + Final verification (Worker 1)

### Spec status-line re-verification (this spawn)

Read the spec's title, the `Shipped in 0.0.10` identity paragraph, the `Status:` line, `Owner:`, and `Predecessors:` end to end. **Nothing this cycle did falsifies any of them; no header edit is owed and none was made.** The `Status:` line reads SHIPPED (`0.0.10`) with all five slices final-accepted, names the released `CHANGELOG.md` heading, and states the shipped-spec unticked-boxes convention. R2 already removed the two stale clauses (the self-dating `0.0.9` parenthetical and the Slice-checklist preamble's "the work has not started"), and R3's two spawns re-verified after that.

R2's zero-narration baseline re-derived here rather than inherited, counting **occurrences** per token in the spec:

```text
Post-ship        0
Revision         0
as of            2      <- both the deliberate `## Current state` vintage framing (spec:3 identity paragraph, spec:81 section preamble)
later changed    0
amendment        0
post-ship        0
```

### Pre-condition 1 — every prior artifact read in cycle order

**Done, all six, in full**, in the order the cycle produced them: Slice 0 (rationale extraction) → R1a → R1b → R1c → R2 → R3. No "as needed" reading. The build plan (including `## R1 outcome`, `## R2 outcome`, `## R3 outcome`, `## Maintainer-set scope for this cycle` and the pre-flight deviation table), `AGENTS.md`, `START.md`, `GOAL.md`, `docs/builder/BUILD.md`, `docs/builder/ARTIFACT.md`, `docs/builder/worker-1.md`, `docs/GLOSSARY.md` and `CHANGELOG.md` were read alongside them.

### Pre-condition 2 — static inspection helper coverage

Every claim checked against `docs/shadow/` on disk, not against the artifacts' prose. The build **touched one** `.py` file; the R1 cohorts ran the helper over their read-only audit targets as well.

| File | Claiming pass | Shadow file present | mtime | Verdict |
|---|---|---|---|---|
| `django_strawberry_framework/permissions.py` | R1a | `django_strawberry_framework__permissions.overview.md` | 2026-08-28 01:41 | ran, in-cycle |
| `django_strawberry_framework/optimizer/walker.py` | R1b | `django_strawberry_framework__optimizer__walker.overview.md` | 01:44 | ran, in-cycle |
| `django_strawberry_framework/connection.py` | R1b | `django_strawberry_framework__connection.overview.md` | 01:44 | ran, in-cycle |
| `django_strawberry_framework/types/definition.py` | R1c | `django_strawberry_framework__types__definition.overview.md` | 01:45 | ran, in-cycle |
| `examples/fakeshop/apps/products/schema.py` | R1c | `examples__fakeshop__apps__products__schema.overview.md` | 01:45 | ran, in-cycle |
| `examples/fakeshop/test_query/test_products_api.py` | R3 (plan, W3 pass 1, W3 pass 2) | `examples__fakeshop__test_query__test_products_api.overview.md` | 03:01 | ran, in-cycle, and it is the only file the build **edited** |

**No file with review-worthy logic that the build touched lacks a run or a recorded skip.** The set of edited files is exactly `{examples/fakeshop/test_query/test_products_api.py}`, and it carries three runs. Every other file in the table is read-only audit territory, so the helper's trigger conditions were met voluntarily rather than compulsorily — recorded as such.

The remaining 11 overview pairs under `docs/shadow/` carry 2026-08-27 18:24–20:48 timestamps, predate this cycle's first pass, and belong to a prior or concurrent session. Pre-flight step 5's recorded deviation left them in place; they are **not** this cycle's evidence and are excluded from the comparisons below, with that exclusion stated rather than silently applied.

### Pre-condition 3 — Repeated string literals compared **across files**

R3's own measurement (`allItems` 17, `allCategories` 12, `view_category_1` 6, `products.category` 40) is a **within-one-file** delta and does not discharge this step. The cross-**file** comparison is the one BUILD.md asks for, and the overview's own list is **truncated at 25 entries** for the test file ("86 more not shown") — a truncated instrument is not a population, so the full per-file sets were re-derived with an AST pass replicating the helper's own rule (`ast.Constant` string values, `len(stripped) >= 8`, count > 1).

```text
permissions.py          5 repeated literals
optimizer/walker.py     7
connection.py           3
types/definition.py     3
products/schema.py      5
test_products_api.py  111        <- the overview shows 25 of these

=== repeated-in-file literals appearing in 2+ FILES ===
  22 total  {'products/schema.py': 2, 'test_products_api.py': 20}   'category'
  12 total  {'products/schema.py': 4, 'test_products_api.py': 8}    'description'
2 cross-file candidates
```

**Neither is a DRY candidate, and neither is this cycle's.** Both are model field names wearing two different hats: in `products/schema.py` they are entries in four declarative `Meta.fields` tuples (each type must name its own set; a shared constant would make the four schemas indistinguishable in the SDL — R1c's reasoning, re-derived), and in `test_products_api.py` they are GraphQL selection text inside query strings. A package module's Meta declaration and an example test's query string cannot share a source. **No cross-file DRY finding.**

Cross-checked specifically for literals R3 *added*: `allCategories` / `allItems` / `allProperties` / `allEntries` and the four `view_<model>_1` usernames appear in **one** file each. The root-field names are camelCase wire names synthesized from the schema, so `products/schema.py` cannot carry them, and does not.

### Pre-condition 4 — Imports compared across shadow overviews

One-way direction confirmed; one import is worth a judgement and gets one.

- **`permissions.py` → `.utils.querysets`, one private name.** `from .utils.querysets import (_prepared_visibility_source, apply_type_visibility_sync, model_for, run_in_one_sync_boundary)` — a root module importing four names from a subpackage, one of them private. **Verdict: the direction is right and the private name is a naming wart, not a boundary violation.** Verified rather than accepted: `utils/querysets.py` imports nothing from `permissions.py` (`grep` for `permission` over its import lines returns nothing), so there is no cycle; and `_prepared_visibility_source` is the source-side twin of the public `apply_type_visibility_sync`, with **no public alias**. Its readers, measured: two internal uses inside `utils/querysets.py` (`:3030`, `:3273`), one cross-module use in `permissions.py::apply_cascade_permissions` (`:621`), and one test import. The alternative — `permissions.py` duplicating the sealed source boundary locally — is the DRY violation the shared seam replaced. Recorded, not filed as a finding; it is a `utils/querysets.py` naming question and this pass writes no source.
- **`products/schema.py` → package root only** (`from django_strawberry_framework import ... apply_cascade_permissions`), which is the documented consumer surface. One-way, no reach into a private module.
- **`types/definition.py`** imports up into `..exceptions` / `..optimizer.*` / `..registry` and sideways into `.relay`; no import touches the Decision 2 `fields_class` slot.
- **`optimizer/walker.py`** imports `from ..utils.querysets import apply_type_visibility_sync` — the shared visibility seam imported rather than reimplemented, which is what makes Decision 12's "no optimizer change" true.
- **`test_products_api.py` repeats `from django.contrib.auth.models import Permission` at four in-function sites** (`:90`, `:522`, `:3330`, `:3975`). All four predate this cycle — R3 added no import — so it is not a cross-round finding. Recorded so a later reader does not attribute it here.

**No sibling imports from outside its documented boundary.**

### Pre-condition 5 — deferred follow-up in every accepted artifact's `What looks solid` / `DRY findings`

Walked bullet by bullet across all six artifacts. Exactly one deferred DRY item could in principle land in this pass, and it may not:

- **R1a DRY D1 — `_cascadable_edges` / `_cascadable_edge_names`.** Handled under `### Consolidation candidates` below with reader counts re-derived. **Out of scope: production source this cycle has not authorized changing.**
- **R1a D2** (five repeated message fragments in `permissions.py`) — re-derived here; each sits in a distinct f-string whose sentence differs and the two `cross-database subqueries` sites are two genuinely different errors. No finding, confirmed.
- **R1b DRY** — four near-copy cascading fixtures across `tests/test_connection.py`, `tests/test_relay_node_field.py`, `tests/test_list_field.py`, `tests/optimizer/test_extension.py`, with a recorded recommendation **against** consolidation (four independently-runnable modules with different registry/reload harnesses; `BUILD.md` `### Example-project schema changes must sync every schema-module list` names the order-dependence). Sustained: consolidating would couple four schema-module harnesses to buy one fixture, and it is test source this pass may not touch in any case.
- **R1b** — `plan.cacheable = False` at three `optimizer/walker.py` sites encoding three different reasons. Not a DRY defect; sustained.
- **R1c DRY** — four near-identical hook bodies in `products/schema.py`, deliberately not consolidated because Goal 7 ("reading a type's class body shows its entire row-visibility story") is the property the fakeshop schema exists to demonstrate. Sustained. The `DjangoTypeDefinition.fields_class` existence challenge was raised and answered on the record (`KANBAN.md`:643 names `TODO-BETA-055-0.1.1`'s `_bind_fieldsets` as the scheduled populator); not re-raised — re-opening an answered existence challenge is the rubber stamp `worker-3.md` warns against.
- **R3 DRY D1** — the two-site ORM page-expectation comprehension, **resolved inside R3** behind `_cascade_page_gids(model)`. Re-verified below.

### Pre-condition 6 — staged-anchor sweep, populations re-derived rather than inherited

Three grammars over the whole tree (`.git/` and `.venv/` excluded), `KANBAN.md` / `KANBAN.html` / `BACKLOG.md` excluded where BUILD.md excludes them.

```shell
$ grep -rEn 'TODO\(spec-034|TODO-(ALPHA|BETA|STABLE)-034' --include='*.py' .
0 occurrences

$ grep -rEn 'TODO.{0,40}034|034.{0,40}TODO' --include='*.py' .
examples/fakeshop/apps/products/schema.py:22:`DONE-034-0.0.10` permissions, `TODO-BETA-046-0.1.1` fieldsets,

$ grep -rn '034' --include='*.py' .
# 47 lines, every one a `spec-034` / `DONE-034-0.0.10` provenance reference in a
# docstring or comment; zero TODO anchors naming card 034
```

- **`TODO(spec-034` in shipped source or tests: 0 occurrences**, in every grammar. The tree-wide population is the spec's `## Implementation plan` sentence *describing* the anchor discipline (`docs/SPECS/spec-034-permissions-0_0_10.md:379`), plus quotations inside this cycle's own artifacts (`bld-034-review-3-code_repair.md`, and now this file). Matches what R3's two sweeps recorded, re-derived independently.
- **`TODO-<MILESTONE>-034` in shipped source or tests: 0 occurrences.** The one loose-grammar hit is `DONE-034-0.0.10` at `products/schema.py:22` — a **DONE** provenance reference, which is exactly the "replace with non-TODO provenance such as `DONE-<NNN>`" form BUILD.md step 6 licenses.
- **R1c's separate claim re-derived:** `examples/fakeshop/apps/products/schema.py`'s `TODO-ALPHA-034-0.0.10` markers are **fully discharged — 0 occurrences**, confirmed. The same file's card-id census re-derives exactly as R1c and R2 recorded it, which also confirms nothing in this cycle moved a spelling:

```text
   7 TODO-BETA-046-0.1.1
   5 TODO-BETA-047-0.1.2
   6 TODO-BETA-049-0.1.3      <- 18 rotted, maintainer-escalated
   1 TODO-BETA-062-0.1.5      <- correct, must not be swept
```

- **Spec-side card ids, after R2 and R3:** `TODO-ALPHA-033-0.0.10` 1, `TODO-ALPHA-034-0.0.10` 6, `TODO-ALPHA-035-0.0.10` 1, `TODO-BETA-046-0.1.1` 2 — identical to R1c's pre-round census, so every escalated spelling survived the cycle byte-identical, as R2 and R3 both claim.

**One population no pass enumerated, surfaced here.** The **rationale companion's** card-id spellings were never fully censused: R1c's census G-ii enumerated only its three `TODO-BETA-046-0.1.1` sites, and R2's post-round measurement was explicitly "card-id spellings **in the spec**". Measured now:

```text
   2 TODO-ALPHA-027
   2 TODO-ALPHA-027-0.0.10
   2 TODO-ALPHA-033-0.0.10
   5 TODO-ALPHA-034-0.0.10
   1 TODO-ALPHA-035-0.0.10
   3 TODO-BETA-046-0.1.1
```

All 15 were read at their sites: every one sits inside a `- **Revision N**` history bullet, a `### Changes this Decision underwent` entry, or the Risks body's own record of a stale-id finding — i.e. the decided-non-edit class (true as history at the date each records). The `TODO-ALPHA-027-0.0.10` pair is the sharpest case and is *deliberately* preserved: it is a Revision-2 record of an incoming review that **claimed** the fakeshop hooks carried that marker, and of the verification that found they already read `034`. Nothing to fix; recorded so the class is enumerated rather than assumed empty.

### Spec ⇄ rationale coherence

The pair was checked for the four failure modes a single-file read cannot see.

**(d) Dangling pointers, both directions — 0.** Mechanical, both files, all three link classes (in-page `](#anchor)`, reference definitions into the other file with a `#fragment`, reference definitions into a third file with a `#fragment`), with GitHub's actual slug rule (lowercase, punctuation dropped, **each** space becomes one hyphen — an em dash therefore yields the `--` that a naive collapsing slugger gets wrong):

```text
--- SPEC: 0 unresolved anchors
--- RATIONALE: 0 unresolved anchors
```

Every one of the 13 `[rationale-dN]` definitions resolves to a real rationale heading and every one of the 13 `[spec-034-dN]` definitions resolves to a real spec heading — including the Decision 5 slug R2 renamed, which is the one most likely to have been left half-swept.

**(c) A rejected alternative the reconciled spec has since adopted — one, and it is correctly recorded.** All 29 rejected alternatives were read against the reconciled spec. Exactly one is now the shipped contract: Decision 5's *"Calling every target's `get_queryset` unconditionally (upstream behavior)"*. The rationale records the re-adoption explicitly (`## Decision 5` → `**Post-ship — the recorded rejected alternative was re-adopted, for a reason the original deliberation did not weigh.**`), and the reconciled spec's Decision 5 step 3 states the counter-argument in place rather than leaving the reader to find it: *"A hook gate keyed on `has_custom_get_queryset()` would look like a free optimization … and is not one."* R1a asked for exactly this shape and it landed. The other 28 alternatives are still rejected at `HEAD`, checked one by one — including D10's async-native walk (still deferred), D10's per-hook wrapping (`run_in_one_sync_boundary` is one boundary), D3's `permissions/` package (still flat), D8's no-pinning, D9's warn-instead-of-raise, D12's `cascade=True` option.

**(a) A rationale entry describing a contract the spec no longer states — one substantive case, and it is a genuine miss.** See `### Finding I1` below.

**(b) A `**Post-ship:**` bullet contradicting the spec sentence above it — 0.** All 25 bullets were read against the spec section each names. Two shapes were checked hardest because they are the ones that go wrong: the four Decision 5 bullets against the rewritten five-step Decision (consistent, including the `fields=[]` re-entrant shape appearing in both), and the Decision 10 bullets against `### Error shapes` (consistent, see the seam section).

**One count in the pair's own record is wrong.** `bld-034-review-2-spec_reconciliation.md`'s summary and the build plan's `## R2 outcome` both state **"14 `**Post-ship:**` bullets under 11 Decisions plus 6 under `## Non-Decision deliberation`"**. Re-derived by enumerating every top-level (indent 0) `- **Post-ship…` bullet and attributing each to its enclosing section:

```text
  1  Decision 1        1  Decision 6        2  Decision 9        2  Decision 12
  1  Decision 3        2  Decision 7        3  Decision 10       6  Non-Decision deliberation
  4  Decision 5        2  Decision 8        1  Decision 11
total 25 bullets, 11 sections
```

**19 under 10 Decisions, plus 6 = 25**, not 14 + 6 = 20. Decisions 2, 4 and 13 carry none. The `11` is right in its digits and wrong in its subject — it counts *sections carrying bullets* (10 Decisions + the non-Decision section), not Decisions. The file itself is correct; only the number describing it is wrong. **Neither file is editable by this pass** (`ARTIFACT.md` forbids editing a prior entry; the build plan is Worker 0's), so this is a recorded correction for the final gate rather than open work. R2's other stated counts re-derive correctly: its checklist is **34** `- [x]` and **9** `- [ ]`, so "34 of 43 dispatched" is right.

### Finding I1 (SUPERSEDED, Low) — the per-model edge memo shipped, and three deliberation sites still call it unshipped

The one substantive divergence this pass found that no cohort routed. It sits precisely where a cross-cohort pass can see it and a single-territory audit cannot: R1a saw the memo and graded the *narrow* claim it was checking, while the sentences the memo falsifies had already been moved into the rationale companion by Slice 0 and were outside R1a's spec territory by the time R2 ran.

**At `HEAD`,** `django_strawberry_framework/permissions.py::_edge_plan` is `@lru_cache(maxsize=1024)` over `model._meta.get_fields()`, shared by `fields=` validation, the unsupported-edge preflight, and the walk. Its docstring answers the invalidation question directly: *"Django model metadata is immutable after app loading … eviction is correctness-neutral because the plan can always be recomputed."*

**Three sites still describe that as not shipped:**

1. `docs/SPECS/appx/…-rationale.md` `## Risks and open questions` → **Cascade-call overhead on hot paths**: *"The work is one `get_fields()` loop plus set ops"* — **false at `HEAD`**: the loop runs once per model, not once per `get_queryset` invocation.
2. The same item's *"Fallback: a per-`(model, fields)` walk-result memo (the edges, not the querysets) — cheap to add …; **deferred** per the measure-first discipline"* — the edges half has shipped (keyed per model rather than per `(model, fields)`), so the fallback is half-taken and is still recorded as deferred.
3. `## Decision 5` → `### Alternatives considered (and rejected)` alternative 4, *"A finalize-time precomputed cascade plan per type … precomputing buys one loop over `get_fields()` per call at the cost of a cache layer with invalidation semantics. Measure first."* — `HEAD` shipped exactly that cache layer (lazily rather than at finalize time), with the invalidation objection answered in the helper's own docstring. Decision 5's *other* re-adopted alternative gets a `**Post-ship:**` retraction; this one does not.

**The spec itself is clean.** Decision 9's held-back closing paragraph says *"The check is a set comparison per call"* and *"the model's cascadable set is stable post-finalize"* — both still true, because the per-call set diff genuinely still runs. The spec nowhere asserts a per-call `get_fields()` loop (`grep -nE 'get_fields|per call|per-call'` over the spec returns three lines, all accurate). **So no spec edit is owed; the correction belongs wholly to the rationale companion** — a `**Post-ship:**` bullet under Decision 5 naming `_edge_plan`, plus an in-place correction of the Risks item's cost premise, in the shape R2 already used three times (its rows 66).

**Not fixed here, deliberately.** This pass's writable scope permits a spec edit only where integration reveals an inconsistency **this cycle created**, and permits a rationale bullet only as the companion to such a spec edit. This inconsistency was inherited: the two sentences said the same thing before and after Slice 0's move, and both were already stale against `HEAD` when the cycle opened. Recorded, with the exact fix named so no design question is left, and handed to Worker 0 — see `### What Worker 0 must decide`.

Severity **Low** under `BUILD.md` `## Severity definitions` (a stale deliberative record, not a load-bearing contract). Grade **SUPERSEDED** under the build plan's own rule, which routes it to an R2-shaped pass.

### Cross-cohort seam

The three R1 cohorts partitioned the spec's territory and each was internally consistent by construction. Four contracts straddle two or three territories; each was re-read across all of them in the reconciled spec.

**Seam 1 — the `has_custom_get_queryset()` gate, graded SUPERSEDED by R1a and CONFORMS by R1b.** The two grades are about **different surfaces** and the reconciled spec now says so at every site. Phrase-swept rather than line-checked (`custom get_queryset|custom hook|hook gate|identity hook`, case-insensitive), which is the grammar R1a's own eight-site lesson demands: **six** sites, all consistent — `:58` and `:400` and `:97` are the **optimizer's** use (downgrade rule, `cacheable = False` presence-not-content rule), `:84` is a `## Current state` observation about the shipped sentinel that remains true, `:256` is Decision 5 step 3 stating that the **cascade** gates on registration and not on the hook, with the security reason, and `:283`/`:353` are relation-resolver and nested-prefetch statements about targets with custom hooks. **No site still implies the cascade gates on the hook.** `grep -c has_custom_get_queryset django_strawberry_framework/permissions.py` = 0, so the source half holds too.

**Seam 2 — the cascade's `get_queryset` contract, as specified (R1a), consumed (R1b) and instantiated (R1c).** The straddling question neither cohort could ask: *the cascade rejects a sliced root — can any shipped surface hand a sliced queryset into a cascading `get_queryset`?* Answered by enumerating **every** call site of `apply_type_visibility_sync` / `_async` in the package (18 sites across `permissions.py`, `connection.py`, `list_field.py`, `filters/sets.py`, `types/resolvers.py`, `types/relay.py`, `optimizer/walker.py`, `mutations/resolvers.py`, `utils/querysets.py`) and reading what each passes:

- Exactly **one** site passes `allow_sliced=True`: `optimizer/walker.py::_build_child_queryset`. Its source is `field.related_model._default_manager.all()` — **unsliced when the hook runs**; the flag exists so the seal accepts a *sliced return* from a nested-connection child, which the in-body comment states and `nested_fetch.py::unwindowable_child_queryset_reason` consumes.
- Every other site takes the default `allow_sliced=False`, so a sliced **source** is rejected by the shared boundary before a consumer hook is ever invoked.
- The connection pipelines apply visibility as the first post-normalization step, upstream of `filter:` / `orderBy:` / slicing; the Relay node/nodes defaults seed from `initial_queryset(cls)`.

**Verdict: no shipped surface can hand a sliced root to a cascading hook.** The cascade's own root-slice rejection (`permissions.py::_validate_root_queryset`, not the seal — the cascade passes `require_model_rows=False`, which switches the seal's own slice branch off) therefore guards a *consumer* slicing inside its own hook, and the spec's `### Error shapes` recourse — *"cascade first and slice after"* — is exactly right for that reader. Consistent across all three territories.

**Seam 3 — the sync-misuse recourse text, spanning Decision 10 and `### Error shapes`.** This is the seam that was internally contradictory before R2 (bullet 1 named `aapply_cascade_permissions` as a recourse; bullet 3 named `fields=`). Re-read against the source string rather than against R2's record: `permissions.py #"_ASYNC_RECOURSE"` says *"neither can await an async target hook; make this target type's `get_queryset` sync, or pass `fields=` to skip the async-hooked edge."* Decision 10 bullet 1 now names those two recourses **and** states explicitly that the message does **not** point at `aapply_cascade_permissions`; bullet 3 names the same two; `### Error shapes` line 206 names the same two. **Three homes, one contract.**

**Seam 4 — `### Error shapes` as an inventory, spanning R1a's census C11 and R2's rewrite.** R1a counted twelve error surfaces where the section listed two; R2 rewrote it into five groups. Verified against the source rather than against either record: `permissions.py` carries **15** direct `raise ConfigurationError(` sites (5 in `_validate_fields`, 2 in `_validate_root_queryset`, 5 in `_validated_target_subquery`, 3 in `apply_cascade_permissions`) plus `_cycle_error`'s constructed error, plus 3 root-renderer and 4 edge-renderer defect codes routed through the shared boundary. Every one maps onto a bullet in the rewritten section: `fields=` validation (4 bullets), walk preconditions (5), target-hook return contract (2), sync/async (1), what never raises (2). **No raise site is unrepresented and no bullet is unbacked.**

### Consolidation candidates

**None requiring dispatch.** One candidate was flagged by a cohort and is confirmed as **dead code rather than live duplication**, which is why the higher-quality fix is delete-and-trim — and why this pass may not perform it.

**R1a DRY D1 — `_cascadable_edges` / `_cascadable_edge_names`.** Reader counts re-derived by me, not read off R1a's record:

```shell
$ grep -rn '_cascadable_edges' --include='*.py' .
django_strawberry_framework/permissions.py:248:def _cascadable_edges(model: type[models.Model]) -> tuple[Any, ...]:
django_strawberry_framework/permissions.py:255:    return frozenset(field.name for field in _cascadable_edges(model))

$ grep -rn '_cascadable_edge_names' --include='*.py' .
tests/test_permissions.py:74      (import)
tests/test_permissions.py:527, :681, :798   (three call sites)
django_strawberry_framework/permissions.py:253:def _cascadable_edge_names(...)
```

**Confirmed: `_cascadable_edges` has exactly one reader (`_cascadable_edge_names`), and `_cascadable_edge_names` has zero production readers.** Every production path — `_validate_fields`, `apply_cascade_permissions`'s preflight, `_walk` — reaches `_edge_plan(model)` directly. **Verdict: R1a graded it correctly; it is a test-facing seam, not live duplication, and the fix is a deletion, not an extraction.** **Not acted on:** it touches production source this cycle has not authorized changing (build plan `## Maintainer-set scope`), it is a maintainer call R1a escalated rather than decided, and it is Low-value work that should gate nothing. It stays in the deferred catalog with the reader counts now verified twice.

**R3's own consolidation, re-verified as removed rather than relocated.** `grep -rn '_RELAY_MAX_RESULTS\]' tests/ examples/` returns **one** line — `examples/fakeshop/test_query/test_products_api.py:2298`, inside `_cascade_page_gids` — and the helper has exactly the two readers the plan named (`:2333` T1's `expected`, `:2360` T2's inline precondition). `_CASCADE_ROOT_FIELDS` has exactly the two parametrize readers. `git diff --stat HEAD` on the file reports `95 insertions(+), 12 deletions(-)`, matching the round's record.

### The classic cross-slice checks, with their real surface

Stated one by one so a vacuous check is never reported as a passing one.

| Check | Surface | Result |
|---|---|---|
| Duplicated helpers across rounds | **Single-round.** Only R3 landed code; R1a/R1b/R1c/R2 landed none. Cross-round helper duplication is structurally impossible. | Vacuous, and said so. The **within-round** duplication R3 introduced was caught by its own Worker 3, escalated, decided by Worker 1, and consolidated — verified above. |
| Inconsistent naming / error handling between rounds | **Single-round** for code. For *prose*, the surface is real: two rounds wrote the spec-family pair. | Live; covered by `### Spec ⇄ rationale coherence` and `### Cross-cohort seam`. One naming inconsistency found, see below. |
| Repeated ORM / queryset patterns to centralize | Live in one file. | The one such pattern (the pk-order + page-cap window) is centralized at `_cascade_page_gids`; `grep` proves one occurrence tree-wide. |
| Misplaced responsibilities between modules touched by different rounds | **Vacuous:** one module was touched, by one round. | Said plainly. The module-boundary question that *is* live — `permissions.py` importing a private `utils/querysets.py` name — is judged under pre-condition 4. |
| Missing or too-broad exports | Live and checked: `git diff -- django_strawberry_framework/__init__.py` is **empty**; `git diff --name-only HEAD -- django_strawberry_framework/` is empty. No production byte moved in the whole cycle. | Clean. |
| Repeated literals / dict keys / tuple shapes across rounds | Live across files, vacuous across rounds. | Pre-condition 3; two cross-file literals, neither a candidate. |
| Comments telling one coherent story across the new code | Live but small: one file, three sites. | Read in full. `_CASCADE_ROOT_FIELDS`'s `#:` comment matches the file's constant style and states *why* the tuple carries the `view_<model>` username; `_cascade_page_gids`'s docstring states the invariant (the ordering and cap are the **connection's**, coupled so the two staff rows cannot drift) and the negative that makes it an expectation rather than a second read of the response. **No process provenance** in either — grepped for round ids, pass numbers, `Revision N`, finding ids, worker names: zero. The only external pointer is `spec-034`, which `AGENTS.md` permits. One thing checked and cleared: the constant's comment says the `view_<model>` holder "takes the hook's `elif user.has_perm(...)` branch instead of the anonymous fall-through", which is true of control flow while R1c's M1 establishes the branch's *result* is identical — the comment does not claim otherwise, and T2 asserting that actor explicitly is what makes a future divergence observable at all. No finding. |

### Finding I2 (Low, contained) — R1b names a symbol that does not exist

`bld-034-review-1b-composition_pins.md` census rows **S2-4** and **S2-5** cite `django_strawberry_framework/permissions.py::_cascade_edges`. **No such symbol exists at `HEAD`**; the walk is `permissions.py::_walk` (`:671`), which is what R1a cites correctly throughout. The cited *substring* is real and lives in `_walk` (`permissions.py:713`, `condition = Q(**{f"{field.name}__in": subquery})`), so the evidence stands and the CONFORMS grades are sound — only the symbol name is wrong.

**Contained: it did not propagate.** `grep -rn '_cascade_edges' --include='*.md' .` returns exactly the two R1b lines and nothing else; the spec, the rationale companion, and R2's discharge record all name the live symbols. Two cohorts naming one function differently is the seam shape worth recording even when it costs nothing — a per-cycle scratchpad closes with the cycle, and `ARTIFACT.md` forbids me editing a prior entry, so this is a recorded correction rather than open work.

### Verification commands and their real output

Every command below was run in this pass; output is quoted as produced. No `pytest` was run (this pass changes no executable byte and the focused runs belong to R3 and to the final gate); no `--cov*` flag was used anywhere.

```shell
$ git status --short
 M BACKLOG.md
 M KANBAN.html
 M KANBAN.md
 M README.md
 M docs/SPECS/spec-034-permissions-0_0_10.md
 M examples/fakeshop/db.sqlite3
 M examples/fakeshop/test_query/test_products_api.py
 M scripts/_kanban_lib.py
 M scripts/build_kanban_html.py
 M scripts/build_kanban_md.py
 M tests/test_build_kanban_html.py
?? 0_0_14.md
?? docs/DIVERGENCE.md
?? docs/SPECS/appx/spec-034-permissions-0_0_10-rationale.md
?? docs/builder/bld-034-*.md
?? docs/builder/build-034-permissions-0_0_10.md
# the cycle's own two spec-family files and one test file, plus the plan's
# baseline-dirty concurrent set. Nothing was edited or reverted by this pass.

$ git diff --stat HEAD -- examples/fakeshop/test_query/test_products_api.py
 1 file changed, 95 insertions(+), 12 deletions(-)

$ git diff -- django_strawberry_framework/__init__.py
# empty
$ git diff --name-only HEAD -- django_strawberry_framework/
# empty

$ grep -rEn 'TODO\(spec-034|TODO-(ALPHA|BETA|STABLE)-034' --include='*.py' .
# 0 occurrences

$ grep -ohE 'TODO-(ALPHA|BETA|STABLE)-[0-9]{3}[A-Za-z0-9._-]*' \
    examples/fakeshop/apps/products/schema.py | sort | uniq -c
   7 TODO-BETA-046-0.1.1
   5 TODO-BETA-047-0.1.2
   6 TODO-BETA-049-0.1.3
   1 TODO-BETA-062-0.1.5

$ grep -rn '_RELAY_MAX_RESULTS\]' tests/ examples/
examples/fakeshop/test_query/test_products_api.py:2298:        for pk in model.objects.order_by("pk").values_list("pk", flat=True)[:_RELAY_MAX_RESULTS]

$ grep -rn '_cascade_edges' --include='*.md' .
docs/builder/bld-034-review-1b-composition_pins.md:49
docs/builder/bld-034-review-1b-composition_pins.md:50
# contained in one per-cycle artifact; zero occurrences in either spec-family file

$ grep -n 'def _cascade_edges\|def _walk' django_strawberry_framework/permissions.py
671:def _walk(

$ grep -rn '_cascadable_edge_names' --include='*.py' . | wc -l
5     # 1 def + 1 test import + 3 test call sites; zero production readers
```

Anchor resolution, both files, all three link classes (script in this pass's scratchpad, re-derivable — GitHub slug rule, each space one hyphen):

```text
--- SPEC: 0 unresolved anchors
--- RATIONALE: 0 unresolved anchors
```

Cross-file repeated-literal comparison (AST re-derivation of the helper's own rule, because the overview truncates the test file's list at 25 of 111):

```text
=== repeated-in-file literals appearing in 2+ FILES ===
  22 total  {'products/schema.py': 2, 'test_products_api.py': 20}   'category'
  12 total  {'products/schema.py': 4, 'test_products_api.py': 8}    'description'
2 cross-file candidates
```

**Gate re-runs: not owed and not made.** `check_spec_glossary.py`, `check_citations.py` and `check_trailing_commas.py` are conditional on a spec-family edit, and this pass made none. Their last measured readings stand, from R3's final verification on files this pass did not touch: `OK: 42 terms` (exit 0), `OK: 857 citations resolve (738 in 431 .py files, 119 in KANBAN.md)` (exit 0), scaffold exit 0.

### Deferred work catalog — this pass's contribution

R2's catalog was **read out of `bld-034-review-2-spec_reconciliation.md` `### Deferred work catalog`**, not reconstructed from memory, and is not restated here; the final gate assembles one catalog from that section plus the four items below, so nothing duplicates. R2's twelve items stand unchanged and are re-confirmed as still open by this pass: the 18 source-side card ids coupled to four spec sites; the spec's frozen card-id population; the three dangling `KANBAN.md` citations Slice 0's move created; `KANBAN.md`:402's false `scalar-only` discharge claim; the `is_relation` fail-open shape; the `_cascadable_edges` existence challenge; the dead `view_<model>` branch; the unasserted prefetch-child alias behaviour; `seed_cascade_split`'s missing per-app test; the `_seal_or_defect` docstring imprecision; `docs/README.md`'s superseded "Coming next" line; and the unverifiable board M2M follow-up surfacing.

**New, found by this pass:**

- **The per-model edge memo shipped and three deliberation sites still call it unshipped** (`### Finding I1`). Sites: the rationale's `## Risks and open questions` → *Cascade-call overhead on hot paths* (both its cost premise and its "deferred" fallback) and its `## Decision 5` rejected alternative 4. `django_strawberry_framework/permissions.py::_edge_plan` is `@lru_cache`d per model. **The spec needs no edit; the correction is a rationale `**Post-ship:**` bullet under Decision 5 plus an in-place fix to the Risks item's cost premise.** Graded SUPERSEDED by the build plan's own rule, which routes it to an R2-shaped pass. Not performed here: this pass's licence covers only an inconsistency the cycle created, and this one was inherited.
- **Two stated counts in the cycle's own accepted record are wrong and are not editable by this pass.** (i) `bld-034-review-2-spec_reconciliation.md`'s summary and the build plan's `## R2 outcome` say "14 `**Post-ship:**` bullets under 11 Decisions plus 6"; measured, it is **19 under 10 Decisions plus 6 = 25**, and the `11` counts sections rather than Decisions. (ii) `bld-034-review-1b-composition_pins.md` rows S2-4 / S2-5 cite `permissions.py::_cascade_edges`, a symbol that does not exist; the live symbol is `::_walk` (`### Finding I2`). Both are recorded corrections for the final gate, not open work — `ARTIFACT.md` forbids editing a prior entry and the build plan is Worker 0's file.
- **The rationale companion's card-id population is now enumerated** (15 occurrences in six spellings, listed under pre-condition 6) and every one is the decided-non-edit history class. No pass had censused it: R1c enumerated three of the fifteen and R2's post-round measurement was spec-only. Nothing to fix; recorded so the class is closed by measurement rather than by assumption.
- **Three prose-only corrections R3 recorded rather than fixed, carried forward as corrections and not as defects** (`bld-034-review-3-code_repair.md` `### Notes for Worker 1`): **L1** the pass-1 build report's reason for dropping the shipped trailing assertion is wrong (the correct reason is "not generalizable to the parametrized `model`"); **L2** the plan's repeated-literal prediction was falsified at `+1` per root field; **L3** the pass-2 report's stated obstacle to annotating the helper's parameter does not hold (`from django.db.models import Model` binds `Model`, no collision), though the choice it defends is right on the per-file-`ANN`-ignore ground. All three live in Worker 1 sections because `ARTIFACT.md` forbids editing the prior entry, which is exactly why the final gate should carry them where a reader will find them.

### What Worker 0 must decide

**No consolidation pass is needed and none is requested.** This pass found no duplicated helper, no repeated ORM pattern outside its single home, no misplaced responsibility, and no cross-file literal worth a shared source, so **Worker 2 and Worker 3 need no dispatch on DRY grounds.**

One decision is owed, and it is the maintainer's through Worker 0: **`### Finding I1`.** Either (a) route it to the final gate's `### Deferred work catalog` as an inherited post-ship divergence for a future pass, or (b) dispatch one Worker-1 spec-reconciliation micro-pass in R2's shape to append the `**Post-ship:**` bullet under Decision 5 and correct the Risks item's cost premise — two edits, both in the rationale companion, no spec edit, no source, no gate re-run beyond the scaffold check. The fix shape is fully named above so the pass would carry no design question. **I did not take (b) unilaterally** because the divergence predates this cycle and my licence is scoped to inconsistencies the cycle created.

### Final status

`final-accepted`. The integration pass is clean in the sense that matters: nothing it found requires a builder or reviewer dispatch. Two of its findings are recorded corrections to the cycle's own record (`I2`, and the Post-ship count), one is an inherited post-ship divergence with a named fix and a decision routed to Worker 0 (`I1`), and the six pre-conditions are discharged with their real results — including the three checks whose surface this cycle's shape makes vacuous, each said plainly rather than reported as a pass.

### Spec changes made (Worker 1 only)

**None.** No spec edit and no rationale edit was made by this pass. The one divergence that would warrant a rationale bullet (`### Finding I1`) is inherited rather than cycle-created, so it is recorded and routed rather than fixed, per this pass's scope. The spec's status/header lines were re-verified this spawn and need no edit.

---

## Build report (Worker 2)

Not applicable. `docs/builder/BUILD.md` `### Procedural-closure slices`: this pass lands no source and no tests, so there is no build pass to dispatch, no `### Files touched` beyond this artifact, no failability proof (it introduces no boundary), no hot-path number (the build plan declares `none` for every pass after R1, and this pass changes no executable byte), and no floor-verification scope (R3's builder pass owns the cycle's one floor run and re-ran it at pass 2; the final gate is its backstop). No `ruff` run was owed and none was made.

---

## Review (Worker 3)

Not applicable, same reason. `docs/builder/BUILD.md` `### Isolation is non-waivable` binds the builder/reviewer pair over a **source diff**; there is none. The cross-artifact comparisons, the anchor and literal re-derivations, and the seam walk above are mechanical and re-runnable from the commands quoted, which is what stands in place of a second reader here.

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
