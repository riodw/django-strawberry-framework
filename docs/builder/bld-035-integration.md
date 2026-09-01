# Build: Cross-slice integration pass — 035 optimizer_hardening / 0.0.10

Spec reference: `docs/SPECS/spec-035-optimizer_hardening-0_0_10.md` (whole document) and its companion
`docs/SPECS/appx/spec-035-optimizer_hardening-0_0_10-rationale.md`
Status: final-accepted

A `BUILD.md` `### Procedural-closure slices`-shaped pass: Worker 1 only, no Worker 2 build and no
Worker 3 review, because an integration pass writes only its own artifact. Plan and verification are
one combined block, following the shape Slices 1 and 3 of this cycle already used. Every number below
was measured this pass from the repository root; no Worker 2 or Worker 3 measurement is carried
unconfirmed. Scratch scripts live **outside** the repository, under
`/private/tmp/claude-501/-Users-riordenweber-projects-django-strawberry-framework/f4b7d889-6e73-477e-b5c0-30ac0e17a204/scratchpad/w1-035-int/`
(`sweep.py`, `anchors.py`, `links.py`, `pair.py`, `symcheck.py`). No `git stash`, `git checkout`,
`git restore`, or `git worktree` at any point. No `--cov*` flag on any invocation.

## Integration pass (Worker 1)

### Cycle framing — which ordinary integration signals do not apply, and why

`BUILD.md` `## Cross-slice integration pass` names eight things the pass checks: duplicated helpers
across slices; inconsistent naming or error handling between slices; repeated ORM/queryset patterns
that should be centralized; misplaced responsibilities between modules touched by different slices;
missing or too-broad exports; repeated string literals / dictionary keys / tuple shapes across
slices; and whether comments now tell one coherent story across the new code.

**Seven of those eight are vacuous this cycle, and the reason is measurable rather than asserted: no
runtime code was written.** Slice 1 and Slice 3 wrote only `.md`. Slice 2 wrote `.py`, but its diff
is comment and docstring text only — proved by docstring-blanked `ast.dump` identity against pristine
`HEAD` on all four cohort files, with equal docstring counts and a position-for-position enumeration
of the five changed docstrings, under four negative controls including one (a non-docstring string
literal) that establishes the blanking is not vacuous. Re-derived independently at that slice's final
verification; not re-run here, because the diff has not changed since (`git status --porcelain` on the
cohort is unchanged, and the focused suite still reports the same 399 passing node ids). A cohort with
zero new executable lines cannot introduce a duplicated helper, an ORM pattern, a misplaced
responsibility, an export, or an inconsistent error path.

Saying this explicitly rather than being silent: **no consolidation of code is owed, and none could
be.** The eighth signal — whether the comments now tell one coherent story — is the one that *does*
bind, together with the checks below that this cycle's actual content makes load-bearing: the
staged-anchor sweep, the shipped-`.py`-to-spec anchor bindings that two slices could have collided
over, and the internal consistency of the spec / rationale pair that Slices 1 and 3 both wrote to.

### Step 1 — every prior artifact read, in slice order

Required, not "as needed" (`BUILD.md` `## Cross-slice integration pass` step 1). All three read end to
end this pass, plus the build plan, `ARTIFACT.md`, `worker-1.md`, `AGENTS.md`, `START.md`, `GOAL.md`,
`CHANGELOG.md`, the `docs/GLOSSARY.md` entries the spec names, the active spec, and the rationale
companion:

| Artifact | Status on disk | Content |
|---|---|---|
| `docs/builder/bld-035-slice-1-rationale_extraction.md` | `final-accepted` | the rationale MOVE; spec 143,045 -> 117,931 bytes; companion created at 57,185 bytes |
| `docs/builder/bld-035-slice-2-carry_forward_anchors.md` | `final-accepted` | four anchor retargets + five rule-27 citation repairs; three build passes, three reviews |
| `docs/builder/bld-035-slice-3-spec_reconciliation.md` | `final-accepted` | ten verified divergences written into the spec across 28 edits; spec 117,931 -> 125,681 bytes |

### Spec status-line re-verification (this spawn)

`worker-1.md` `## Spec status-line re-verification`, run at the start of every Worker 1 spawn. Re-read
`docs/SPECS/spec-035-optimizer_hardening-0_0_10.md` lines 1-11. Title, `Status: **SHIPPED (0.0.10)**`,
`Owner:`, `Predecessors:`, and the closing rationale-companion pointer paragraph all describe the
build's current state. **The two claims that were falsified are gone**: no `0.0.9` on-disk-version
parenthetical survives in the header (grep: 0 occurrences of `0.0.9` in the first paragraph), and the
live-working-path claim is corrected at all four sites Slice 1 identified. No status-line edit is
owed, and none was made — this pass may not edit the spec.

### Step 2 — static inspection helper coverage

`BUILD.md` step 2 asks for a run, or an explicitly recorded skip, for every Python file with
review-worthy logic the build touched. The build touched exactly four `.py` files. Rather than record
a skip for the three test files, the helper was **run on all of them plus `selections.py`** this pass,
with the mandatory `--output-dir docs/shadow`:

```shell
uv run python scripts/review_inspect.py django_strawberry_framework/optimizer/walker.py --output-dir docs/shadow
uv run python scripts/review_inspect.py django_strawberry_framework/optimizer/selections.py --output-dir docs/shadow
uv run python scripts/review_inspect.py tests/optimizer/test_walker.py --output-dir docs/shadow
uv run python scripts/review_inspect.py tests/optimizer/test_extension.py --output-dir docs/shadow
uv run python scripts/review_inspect.py tests/types/test_resolvers.py --output-dir docs/shadow
```

All five wrote their `.overview.md` / `.stripped.py` pair. **The regeneration was not optional**: the
pre-existing `docs/shadow/django_strawberry_framework__optimizer__walker.overview.md` predated Slice
2's edits in one copy of the tree — `docs/shadow/current/…walker.overview.md`, the `bug_hunt.py`
commit-snapshot folder owned by a different generator, still lists `# TODO(spec-035)` at the two
walker sites. That is a **stale snapshot of a different commit, not live drift**; the flat
`docs/shadow/*.overview.md` files this process uses were regenerated here and now agree with the
working tree. `docs/shadow/` is gitignored (`git check-ignore -v` confirms `.gitignore:174`), so the
regeneration added no tree churn — `git status --porcelain docs/shadow` is empty.

### Step 3 — Repeated string literals compared across every shadow overview

The cross-file comparison `BUILD.md` step 3 requires. Literals appearing in two or more of the five
overviews:

| Literal | Files | Verdict |
|---|---|---|
| `category`, `category_id`, `CategoryType`, `allItems`, `allCategories`, `products` | `test_walker`, `test_extension`, `test_resolvers` | fixture model / GraphQL field names from `apps.products`. One authoring home already (the example app's models); a test naming its own fixture is not duplication. |
| `dst_optimizer_planned`, `dst_optimizer_strictness`, `dst_optimizer_fk_id_elisions` | `test_extension`, `test_resolvers` (+ `tests/test_connection.py`, `tests/test_relay_connection.py`, `tests/test_list_field.py`, `examples/fakeshop/test_query/test_scalars_api.py`) | **existence-challenged below — live, and the shared source already exists.** |
| `selections`, `_optimizer_runtime_prefixes` | `walker.py`, `selections.py` (+ `test_walker`, `test_selections`, `test_extension`) | the selection-node shim's namespace field names; authored once in `selections.py::with_runtime_prefix`, read in `walker.py`. One-directional, no second home. |
| `django_strawberry_framework` | `test_extension`, `test_resolvers` | logger-name literal in `caplog` assertions. |

**None of these originates in this cycle.** A cohort with zero new executable lines cannot add an
executable literal, and the overviews' "Repeated string literals" section excludes docstrings by
construction — so every entry above is pre-existing and unchanged. Recorded because `BUILD.md` calls
this section "essential at the cross-slice integration pass"; confirming it is empty of this cycle's
contributions is the check, not skipping it.

### Step 4 — Imports compared across every shadow overview

Dependency direction confirmed one-way and unchanged:

- `optimizer/selections.py` imports **one** local module, `..utils.typing`. It does **not** import
  `walker.py`. `optimizer/walker.py` imports `.selections` (nine symbols) and `.nested_planner` (two,
  one aliased `plan_connection_relation as _plan_nested_connection_relation`). So the
  `walker -> selections` and `walker -> nested_planner` edges are acyclic and the reverse edges do not
  exist.
- One cross-folder import out of `optimizer/` into `types/`: `walker.py` line 1198,
  `from ..types.definition import origin_has_custom_id_resolver`, **function-local and deferred** — the
  standing cycle-avoidance shape, pre-existing, and unchanged by this cycle (it is inside the AST that
  was proved identical to `HEAD`).
- The three test overviews import first-party `django_strawberry_framework.*` symbols, which is the
  expected direction; no test module imports another test module.
- **No sibling imports from outside the documented boundary**, and no import changed this cycle — an
  import statement is an executable line, and the identity proof rules out any change to one.

### Step 5 — deferred follow-up walked from every accepted artifact

`BUILD.md` step 5. Walked the `What looks solid`, `DRY findings`, and every
`### Notes for Worker 1 (spec reconciliation)` section across all three artifacts and all three review
passes of Slice 2.

**The inventory is NINE items, not six, and the discrepancy is itself a finding.**
`bld-035-slice-3-spec_reconciliation.md` `### Notes for Worker 1` says "Items 1-4 are the four Slice 2
recorded; 5 and 6 are this slice's." That description is wrong in one place: Slice 3's item 4 (the
bare `(line NNN)` comments) is not Slice 2's item 3 — it is a **rider on** Slice 2's item 4, promoted
to top level — and **Slice 2's item 3 has no counterpart in Slice 3's list at all.** Two non-blocking
observations recorded across the Slice 2 passes are also absent. A final gate reading only the last
artifact's list would silently drop them. The corrected inventory:

| # | Item | Source | This pass or `bld-035-final.md`? |
|---|---|---|---|
| D1 | The fifth carry-forward anchor is unretargeted: `examples/fakeshop/test_query/test_library_api.py:3680` still reads `# TODO(spec-035): extend this live connection-fragment block …`. Baseline-dirty with a concurrent session's work; `AGENTS.md` 34 forbids editing or reverting it. Should take the `TODO(BACKLOG polymorphic_interface_connections - the abstract-return optimizer entry card)` head once that work lands. | Slice 2 plan pass + all three reviews + Slice 3 item 1 | **`bld-035-final.md`.** No worker in this cycle was permitted to touch the file. |
| D2 | The two package test-tree anchors (`tests/optimizer/test_walker.py`, `tests/optimizer/test_extension.py`) become deletable **if and only if** the spec's G3 deferred test plan ever records their file placement. Both legs still hold: the G3 test-plan heading names no file (unlike the Slice 1 and Slice 2 headings), and `real extension execution` appears nowhere in the spec or its rationale. | Slice 2 plan pass, re-verified at Slice 2 final verification and Slice 3 item 2 | **`bld-035-final.md`.** Writing the follow-up card's test-file layout is that card's spec's decision, not this cycle's. |
| D3 | `django_strawberry_framework/optimizer/selections.py`'s reference anchor is the least informative of the five — the only one whose body cites no `spec-035 Decision N`, so a reader landing there by `grep` finds the owning card but not the design contract. One clause closes it. **`selections.py` is deliberately outside this cycle's ownership partition.** | Slice 2 review pass 1 item 3, re-affirmed at review passes 2 and 3 and at Slice 2 final verification item 3 — **absent from Slice 3's list** | **`bld-035-final.md`.** Recovered here so it survives; it would otherwise be lost at the Slice 2 -> Slice 3 seam. |
| D4 | The out-of-scope rule-27 raw line-citation population is **NINE occurrences**, citing *other* cards' specs: `tests/mutations/test_sets.py` 4 (spec-036), `tests/optimizer/test_extension.py` 4 (spec-033), `examples/fakeshop/config/settings.py` 1 (spec-039). Record as an **occurrence list, never a total** — three successive totals on record (zero, six/seven, eight) were each produced by an instrument that could not see one wrap shape. Two instrument lessons belong in the entry: a `line`-without-`s?` pattern is blind to the plural, and a comment-continuation `#` between the token and the number defeats any `\s+`-only pattern. The sweep must flatten each file's whitespace, newlines included, **before** matching, and must print its scanned-file count. | Slice 2 review passes 1-3 + Slice 2 final verification item 4 + Slice 3 item 3 | **`bld-035-final.md`.** Different cards own the citing files. |
| D5 | Bare self-referencing `(line NNN)` comments citing a source file's own lines — `tests/types/test_resolvers.py` (nine sites) and `tests/test_exceptions.py`; plus the non-spec `cookbook line(s)` shape in `tests/orders/test_sets.py` and `tests/orders/test_factories.py`. Same rot class against a different document; wants `path::Symbol`. | Slice 2 review pass 2 + Slice 2 final verification (as a rider on item 4) + Slice 3 item 4 | **`bld-035-final.md`.** Pre-dates this cycle; nothing this cycle did falsified them. |
| D6 | The spec's `## Implementation plan` delta-table preamble still reads "Line deltas were planning estimates; G1 and G2 have since shipped (Slice 1's are the realized `d1dea2fd` deltas)". Chronology by the letter of `BUILD.md` `## Spec rationale extraction`. Slice 3 judged it and **deliberately left it**: it is not one of the ten dispatched divergences, it is not false, and it does real work (the table's last column mixes an estimate with a realized figure). Re-confirmed present this pass at `docs/SPECS/spec-035-optimizer_hardening-0_0_10.md:260`. | Slice 3 item 5 | **`bld-035-final.md`.** Flagged so a future custodian judges it rather than inheriting it; leaving it reads as decided, not missed. |
| D7 | The rationale companion's `## Post-ship divergences (spec vs. HEAD)` mixes two list forms — items 1-7 as numbered entries, 8-9 as `###` subheadings, because the two new entries carry rejected alternatives. The preamble says so, so it is navigable; a tenth entry should either follow the subheading form or normalise all of them. | Slice 3 item 6 | **`bld-035-final.md`.** A style decision for the next custodian, not a defect. |
| D8 | Of the five `#"…"` anchors, `#"defaults to enabled"` is the least distinctive (four common words, no `G2` / `info` token). It resolves uniquely today — **re-measured this pass: 1** — so there is no defect; a future pass touching that docstring should prefer something like `#"info.operation` defaults to enabled"`. | Slice 2 review passes 2 and 3, agreed at Slice 2 final verification — **absent from Slice 3's list** | **`bld-035-final.md`.** Recovered here for the same seam reason as D3. |
| D9 | **New, found by this pass.** The rationale companion's Decision 4 rejected alternative still cites `` [`_project_scalar_only_window`][walker] `` — the alias site, not the definition. See `### Notes for Worker 1 (spec reconciliation)`. | this pass | **This pass — it is the one item that blocks.** Sets `revision-needed`. |

### Step 6 — staged-anchor sweep (the load-bearing check)

`BUILD.md` step 6, run with **two instruments** because a line-oriented `grep` is fail-open on a
citation that wraps across two source lines, and that exact fail-open produced two false zero counts
inside this cycle already (the build plan's `#### Partition correction` and its own correction).

Instrument (`sweep.py`): for every readable file in the tree, match
`TODO\(\s*spec-035|TODO-(ALPHA|BETA|STABLE)-035` against (a) each raw line, (b) the file's whitespace
flattened to single spaces including newlines, and (c) that flatten with comment-continuation `#`
markers removed. **5,652 files scanned**; the population size is printed, so a zero would be
distinguishable from an unrun instrument. Excluded per the step-6 rule: `KANBAN.md`, `KANBAN.html`,
`BACKLOG.md`, `docs/review/`, `docs/builder/DONE/`.

**Result: exactly one shipped source/test survivor, and it is the expected one.**

- `examples/fakeshop/test_query/test_library_api.py:3680` — `# TODO(spec-035): extend this live
  connection-fragment block with the …`. **Legitimate survivor.** The anchor names work that has
  **not** shipped (the P3a live matching-type test), so `BUILD.md`'s rule — "an anchor whose work this
  slice shipped must be removed" — does not apply to it. The file is baseline-dirty from a concurrent
  session and named in the build plan's `### Baseline-dirty out-of-scope files`, so no worker in this
  cycle was permitted to touch it (`AGENTS.md` 34). **Recorded as deferral D1, not routed to a
  re-loop.**

Every other hit is prose, and none is a code site: this cycle's own three artifacts and the build
plan; `docs/builder/worker-memory/worker-{1,2,3}.md` (scratch); Slice 1's flagged sentence in the
rationale companion; four sibling specs / rationales mentioning `TODO-ALPHA-*` card ids in narrative
(`spec-020`, `spec-033`, `spec-034` rationales, `spec-037` describing a `TODO-ALPHA-035-0.0.11`
reference it already corrected); the stale `docs/shadow/current/` snapshot (regenerable, different
generator, different commit); and the two excluded `KANBAN` files.

**Confirmed: no other `spec-035` anchor survives whose work this cycle shipped.** The card-id form
`TODO-(ALPHA|BETA|STABLE)-035` returns **zero** `.py` hits tree-wide — the `spec-037` sentences
describe a `scalars.py` docstring reference that card already fixed.

Converse measurement: `TODO(BACKLOG` in `.py` returns **five**, all carrying the identical head token
`TODO(BACKLOG polymorphic_interface_connections` — `optimizer/selections.py`, `optimizer/walker.py`
(twice), `tests/optimizer/test_walker.py`, `tests/optimizer/test_extension.py`. Note that a plain
`grep -o 'TODO(BACKLOG[^)]*)'` finds **none** of them, because every one wraps with a `#` continuation
inside the parenthesis; that is the fail-open shape this pass's flatten exists to defeat.

### The shipped-`.py`-to-spec anchor bindings survive the cycle as a whole

**This is the one place two slices could have collided, and neither slice's own verification covers
the pair.** Slice 2 wrote five `#"substring"` anchors into shipped `.py` files pointing into the
spec's `## Edge cases and constraints`; Slice 3 then rewrote parts of that same section (its edits 15
and 16 land inside it). Re-derived here from the `.py` files rather than retyped from either artifact:
every `#"…"` occurrence across **581** `.py` files was extracted under both a plain whitespace flatten
and a comment-continuation-stripping flatten (154 distinct anchors tree-wide), then each spec-035 one
counted in the post-Slice-3 spec with `str.count`.

| Citing symbol | Anchor | Occurrences in spec | Lands on |
|---|---|---|---|
| `django_strawberry_framework/optimizer/walker.py::_record_relation_access` | `every projection writer checks the gate` | **1** | the G2 every-projection-writer Edge-cases bullet, which names `_record_relation_access` by symbol |
| `tests/optimizer/test_walker.py::test_mutation_scalar_only_connection_window_no_only` | `every projection writer checks the gate` | **1** | same bullet, which names the scalar-only window writer the test gates |
| `tests/optimizer/test_walker.py::test_subscription_operation_gated` | `subscription operations are gated identically` | **1** | the SUBSCRIPTION arm bullet |
| `tests/optimizer/test_walker.py::test_enable_only_defaults_enabled_without_info` | `defaults to enabled` | **1** | the missing-`info` / missing-`info.operation` bullet |
| `tests/types/test_resolvers.py::test_fk_id_elision_falls_back_when_consumer_only_defers_fk` | `can defer the FK column (both` | **1** | the consumer-`.only()` bullet, which names that test by name in its closing sentence |

**All five resolve exactly once and land on the right bullet.** Slice 3's edit 16 re-homed the fourth
writer's path *inside* the first bullet — it now reads
`` [`nested_planner.py::_project_scalar_only_window`][nested-planner] `` — while leaving the bound
phrase byte-identical, which is precisely the constraint Worker 3 escalated at Slice 2's third review.
The collision did not occur.

Out of scope and correctly not graded against the spec: `tests/types/test_resolvers.py` carries two
`#"…"` anchors targeting `django_strawberry_framework/types/resolvers.py` (`#"if related_id is None"`,
`` #"instance = root if hasattr(root, `_state`" `` ). Both pre-date this cycle and name a source file,
not the spec.

### Cross-artifact consistency: the spec and its rationale companion are now a pair

Slices 1 and 3 both wrote to both files, so the pair's internal consistency is a cross-slice property
neither slice could check alone. Four instruments, all run this pass.

**1. Link integrity, both directions** (`links.py`, `pair.py`). Spec: 32 headings, 74 link
definitions, 16 in-page anchors used, **0 dangling**, **0 used-but-undefined ref ids**, **0
defined-but-unused**. Rationale: 20 headings, 51 definitions, 12 in-page anchors used, **0 dangling**,
**0 / 0**. Of those definitions, 11 in the spec and 21 in the rationale point into the other half of
the pair; **0 dangling** in either direction. The slugifier strips only `**` / `*`, never bare `_` —
the bug that produced 24 false positives at Slice 3.

**2. Cross-file references from the rest of the repo into either file's anchors.** Swept the whole
tree for `spec-035-optimizer_hardening-0_0_10(-rationale)?\.md#<anchor>`. Exactly one hit, and it is
not a link: `bld-035-slice-1-rationale_extraction.md` quoting the pattern `#decision-N--…` in prose.
**Nothing outside the pair links into a heading that Slice 1's move removed or Slice 3's edit 20
truncated** — the zero-churn truncation held for external readers too, not just the three in-page
uses.

**3. Every rationale entry names a spec decision that exists by heading and anchor**
(`BUILD.md` `## Spec rationale extraction`: "an entry naming no decision cannot be looked up"). All
**nine** `## Decision N` sections in the rationale open with a `Spec: [<title>][spec-035-dN].` pointer,
and all nine ref ids resolve to a slug that exists in the spec's heading set — machine-checked, one
row per Decision, zero failures. `## Risks and open questions` and all nine
`## Post-ship divergences` entries likewise key to an owning Decision or spec section by
reference-style link.

**4. No divergence is described one way in the spec's normative text and another way in the
rationale's account of it.** Walked all nine divergences against the current spec prose:

- Div 1 (`_project_scalar_only_window` relocation) — **one contradiction found; see
  `### Notes for Worker 1`.** The spec side is fully corrected: all seven surviving path-bearing
  citations now use `[nested-planner]`, zero use `[walker]`.
- Div 2 (Decision 5's three-part mechanism) — spec Decision 5 and the Implementation-plan source list
  now name `_fk_attname_is_deferred`, `_FK_ELISION_UNSAFE`, and `_check_n1`'s `force_unplanned`; the
  rationale's account matches.
- Div 3 (G1 waiver reversed) — the spec's waiver is replaced by the shipped live coverage; the
  rationale holds the declined-alternative reasoning and says so.
- Div 4 (G2 handoff discharged) — spec `## Out of scope` and both test-plan bullets say discharged;
  rationale agrees.
- Div 5 (staged anchors) — spec `## Implementation plan` now names five sites and the
  `TODO(BACKLOG …)` form; rationale records the three-site claim as what the spec *said*.
- Div 6 / 9 (`apply_connection_optimization`, DoD grouping) — spec `## Current state` now attributes
  the function to `extension.py` as module-level, called from `connection.py`; DoD names both
  companions. Rationale agrees on both.
- Div 7 (archived path) — corrected at all four sites; `check_spec_glossary.py` with the corrected
  `--spec` argument exits 0.
- Div 8 (G1 narrowed by `spec-045`) — spec `## Goals` item 1, Decision 3, and the new G1 Edge-cases
  bullet all scope the pass-through to the `_optimize` path; the rationale carries the why and two
  rejected alternatives. Consistent.

One tense observation, recorded and **not** raised as a defect: divergence entries 1-7 were written by
the Slice 1 pass and describe the spec in the present tense ("The spec names … in eight places", "The
spec declines a live G1 test"), which Slice 3's corrections have since made false about the spec's
current text. The section's preamble covers this explicitly — it states that items 1-6 are the build
plan's enumeration re-derived by the Slice 1 pass, that item 7 is that pass's status-line finding, and
that **"Slice 3 of this cycle wrote every correction into the spec body"** — so a reader cannot mistake
the entries for current descriptions. The framing is what makes it navigable; without it this would be
the stale-on-its-own-date shape.

**5. Gates re-run by me, not read.**
`uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-035-optimizer_hardening-0_0_10.md`
-> `OK: 23 terms - all have glossary entries and at least one spec link.`, **exit 0**.
`uv run python scripts/check_trailing_commas.py --check` on both files -> **exit 0** (the
`<!-- LINK DEFINITIONS -->` scaffold, all 10 canonical group headers in `START.md` order, alphabetical
defs within each group).

### DRY analysis

- **Helper inventory checked.** Refreshed for the **whole package** at Slice 2's plan pass into
  `docs/shadow/helper-inventory.md` (1,964 lines, `django_strawberry_framework/` recursive). It is
  current for this pass: `django_strawberry_framework/` carries no executable-line change since it was
  generated — the docstring-blanked AST identity against `HEAD` is the proof, and `walker.py` is the
  only package file in any cohort. Shapes grepped for this pass: `project_scalar`, `only_window`,
  `enable_only`, `fragment`, `type_condition`. **No helper is warranted and none could be**: this cycle
  writes no executable line, so there is no call site for one to serve.
- **Existing patterns reused.** None applicable — the pass writes one `.md` artifact. Its section shape
  is copied from `ARTIFACT.md` and from the two Worker-1-only combined-block artifacts this cycle
  already produced (`bld-035-slice-1-rationale_extraction.md`,
  `bld-035-slice-3-spec_reconciliation.md`).
- **New helpers justified.** None, and none is possible.
- **Duplication risk avoided.** The characteristic duplication of an integration artifact is restating
  the per-slice artifacts' findings as if newly measured. Every number above was re-derived with this
  pass's own instruments; where a figure reproduces a prior pass's, that is said as a confirmation
  (five anchors at 1 each, 399 tests, five `TODO(BACKLOG` sites) rather than presented as new.
- **Existence challenge before any consolidation** (`worker-1.md` `## Integration pass` delta). The
  only cross-file repeated literals with a plausible shared-source argument are
  `dst_optimizer_planned` / `dst_optimizer_strictness` / `dst_optimizer_fk_id_elisions`. Readers
  grepped across `django_strawberry_framework/`, `tests/`, and `examples/`: 34 / 17 / 17 occurrences
  respectively, spread over six test modules and **exactly one production module**. They are **not**
  dead code, and **the shared source already exists** —
  `django_strawberry_framework/optimizer/_context.py` defines `DST_OPTIMIZER_FK_ID_ELISIONS`,
  `DST_OPTIMIZER_PLANNED`, and `DST_OPTIMIZER_STRICTNESS` as the single home for each wire name. The
  test-side string literals are deliberate: a test that imported the constant from the code under test
  would keep passing through a rename of the attribute it exists to pin. **No consolidation is
  recommended; the duplication is not live and the shared shape is already centralized.**
- **Comments tell one coherent story across the five anchor sites.** All five carry the identical
  `TODO(BACKLOG polymorphic_interface_connections - the abstract-return optimizer entry card)` head, so
  one grep returns `BACKLOG.md`'s card plus every production and test seam in one listing. The
  reachability *mechanism* is stated **once**, at `selections.py`, with the other four carrying only a
  one-clause R1 precondition — the correct split, since four copies of a mechanism drift and four
  copies of a precondition do not. The one asymmetry is D3: `selections.py` alone carries no
  `spec-035 Decision N` design pointer, so the uniformity is currently one-directional. Cataloged, not
  fixed — that file is deliberately outside this cycle's ownership partition.

### Failability proofs

`None; this pass introduced no new boundary.` — and the inverse is provable rather than asserted: this
pass's entire diff is one new `.md` file, so there is no executable line in it and therefore no guard,
cap, gate, rejection path, or validation branch that *could* have been introduced. **No fail-open
shape landed and none could.** The same holds cumulatively for the cycle: the docstring-blanked AST
identity across all four Slice 2 cohort files proves no executable line exists anywhere in the cycle's
diff, so the `None; …` records at all three Slice 2 passes are true rather than merely present.

### Hot-path budget

Not applicable; plan declares no hot path. No slice in this cycle changes runtime behavior.

### Floor verification

Not applicable; plan declares floor-verification scope none. No slice touches a Django / Strawberry /
channels integration seam, and no runtime line changed. The floor named in `BUILD.md`
`## Floor verification` — Django 5.2.16 on Python 3.10 with strawberry-graphql 0.316.0 — is not
exercised by anything in this cycle. `bld-035-final.md` records `No floor-verification scope
declared.`

### Focused test run

```
uv run pytest tests/optimizer/test_walker.py tests/optimizer/test_extension.py tests/types/test_resolvers.py --no-cov -q
399 passed in 9.09s
```

They run, at the same count Slice 2's final verification recorded, so nothing rotted between Slice 2's
close and this pass. No `--cov*` flag. The **full** sweep belongs to the final gate, not here.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` is not empty and the change is **not this
cycle's**: a concurrent session's `__version__ = "0.0.14"` -> `"0.0.15"` bump. `__all__` and the
re-export list are unchanged. That file is in no cohort of the build plan's ownership table and is
baseline-dirty under `AGENTS.md` 34 — never edit, never revert. The cycle adds no public export,
consistent with spec Decision 9's "this card adds no public symbol".

### Documentation / release sanity

- No version string, shipped/planned status, or card id changed this pass. The spec's `Status:` line,
  the `DONE-035-0.0.10` card id, and the `## [0.0.10]` `CHANGELOG.md` reference were re-read and are
  accurate.
- Every markdown link this pass introduces is a backticked path, not a link; the artifact's
  `<!-- LINK DEFINITIONS -->` block carries all ten canonical group headers, empty.
- No script-rendered doc was regenerated and none was touched. The maintainer's scope excludes
  `KANBAN.md` / `KANBAN.html` / `docs/GLOSSARY.md` / `docs/TREE.md` / `CHANGELOG.md` / `README.md` /
  `docs/README.md` / `BACKLOG.md` / `examples/fakeshop/db.sqlite3`; this pass wrote none of them.
- `docs/shadow/` was regenerated. It is gitignored regenerable scratch with one owner per folder, and
  only the flat `review_inspect.py`-owned files were rewritten; `docs/shadow/current/` (a concurrent
  session's `bug_hunt.py` snapshot) was left untouched.

### Notes for Worker 1 (spec reconciliation)

**One finding, and it blocks.** The spec and its rationale companion contradict each other about the
home of `_project_scalar_only_window` — the exact symbol this cycle's flagship divergence is about.

- **Where it lives.** `docs/SPECS/appx/spec-035-optimizer_hardening-0_0_10-rationale.md`,
  `## Decision 4` -> `### Alternatives considered (and rejected)`, the rejected alternative "Block
  scalar appends only, relying on `_ensure_connector_only_fields`'s empty-`only_fields` no-op to
  suppress the rest" (`:109`).
- **Current wording, quoted:** "And [`` `_project_scalar_only_window` ``][walker] applies `.only(...)`
  directly without populating `only_fields` …" — the ref id is `[walker]`, whose definition in that
  same file is `../../../django_strawberry_framework/optimizer/walker.py`.
- **Why it is wrong.** Re-derived by AST rather than by grep: `_project_scalar_only_window` is
  **defined** at `django_strawberry_framework/optimizer/nested_planner.py:652` (`def
  _project_scalar_only_window(`), and `django_strawberry_framework/optimizer/walker.py:81` holds only
  `_project_scalar_only_window = _nested_planner._project_scalar_only_window`, a module-level alias.
  The citation resolves while the symbol claim is false — the same shape this cycle corrected in the
  spec.
- **Why it is a cross-slice defect rather than a Slice 3 miss.** The rationale's own divergence item 1
  enumerates the eight stale sites and names "Decision 4's enumeration **and its rejected
  alternative**" among them. Slice 1 *moved* that rejected alternative out of the spec; Slice 3's
  implementation step 1 ("correct every path-bearing citation to the live home") then swept the spec
  and fixed seven, and could not see the eighth because it no longer lived there. **The pair now
  documents a stale site and leaves it stale.** Measured: the spec uses `[nested-planner]` at seven
  citations and `[walker]` at zero; the rationale uses `[walker]` at one and `[nested-planner]` at one.
- **Recommended replacement.** Change the ref id from `[walker]` to `[nested-planner]` at that one
  site. `[nested-planner]:
  ../../../django_strawberry_framework/optimizer/nested_planner.py` is **already defined and already
  used** in the rationale (divergence item 1), so no new link definition is needed and no link rot is
  created. The surrounding claim — that the writer applies `.only(...)` directly without populating
  `only_fields` — stays true verbatim and needs no rewording.
- **Secondary, same edit.** Divergence item 1's own sentence "The spec names
  `walker.py::_project_scalar_only_window` … in eight places" should be re-read in the same pass: seven
  of those eight are now corrected and the eighth is the site above, so once it is fixed the sentence
  describes a population that no longer exists in either file. It is covered by the section preamble's
  what-the-spec-said framing, so this is a judgement to make deliberately, not an automatic rewrite.
- **Owner.** Worker 1, spec custody. `worker-1.md` `### Performing the rationale move` rule 4 makes the
  companion append-only *during the build*, which is about where new decisions land; correcting a
  citation the file itself flags as stale is custody, not a new decision — and Slice 3 already amended
  counts and Decision sections in the same file under the same rule.
- **Scope of the re-loop.** One `.md` file, one ref id, plus the judgement call above. No `.py` change,
  so no Worker 2 / Worker 3 dispatch is needed on code grounds; the maintainer's cycle rule dispatches
  Workers 2 and 3 only where the **code** needs a change.

**Nothing else is owed.** No other divergence is described inconsistently across the pair, no in-page
or cross-file anchor dangles, all five shipped-`.py` anchors resolve exactly once and land correctly,
and the spec's status lines describe the build's current state.

### Summary

The cross-slice integration pass for `035` is clean on every check the cycle's content makes
applicable, and blocked on one.

**Clean.** The staged-anchor sweep over 5,652 files under three matching instruments returns exactly
one shipped-source survivor, `examples/fakeshop/test_query/test_library_api.py:3680`, which names work
that has **not** shipped and sits in a baseline-dirty file no worker in this cycle was permitted to
touch — a recorded deferral, not a finding. No other `spec-035` anchor and no `TODO-*-035` card-id
anchor survives anywhere in shipped source or tests. The five `#"substring"` bindings Slice 2 wrote
into shipped `.py` all still resolve exactly once against the post-Slice-3 spec and land on the bullet
their citing symbol is about, so the one place two slices could have collided did not. The spec /
rationale pair has zero dangling in-page anchors, zero orphan or undefined ref ids in either file, zero
dangling cross-references from the rest of the tree, and all nine rationale Decision sections key to a
spec heading that exists. Both gates are green, and the focused suite still reports 399 passing. Seven
of `BUILD.md`'s eight integration signals are vacuous here for a measurable reason — the cycle wrote
zero executable lines — and the eighth, comment coherence, holds: five sites, one grep token, the
reachability mechanism stated once.

**Blocked.** The rationale companion's Decision 4 rejected alternative still cites
`` [`_project_scalar_only_window`][walker] `` while the spec, corrected by Slice 3, cites
`[nested-planner]` at all seven of its surviving sites — and the companion's own divergence item 1
names that rejected alternative as one of the eight stale sites. Slice 1 moved the text out of the
spec, so Slice 3's sweep could not reach it. One ref-id change closes it.

**Deferred-work inventory corrected from six items to nine.** Slice 3's `### Notes for Worker 1`
describes its list as "the four Slice 2 recorded" plus two of its own; that description drops Slice 2's
item 3 (the `selections.py` reference anchor cites no `spec-035 Decision N`) and both non-blocking
observations. Recovered above as D3 and D8 so `bld-035-final.md` `### Deferred work catalog` can carry
the full set.

### Spec changes made (Worker 1 only)

**No spec or rationale edit this pass.** Slice 3 closed both files and this pass's writable list
excludes them; the one defect found is recorded above with its owner and its exact replacement, and
routes to a consolidation loop.

**Deferral reasons.** Nine items are deferred, enumerated with their sources and targets under
`### Step 5`. Eight of the nine (D1-D8) route to `docs/builder/bld-035-final.md`
`### Deferred work catalog`; the ninth (D9) is this pass's blocking finding and routes to a Worker 1
consolidation loop rather than the catalog. The one survivor of the step-6 anchor sweep is D1, whose
deferral reason is that `AGENTS.md` 34 forbids editing or reverting a baseline-dirty file.

### Final status

`revision-needed`.

---

## Consolidation (Worker 1)

Dispatched off this artifact's `revision-needed`. Spec-custody work in `.md` only; no `.py` file
changed, so no Worker 2 / Worker 3 loop was needed. One file was written:
`docs/SPECS/appx/spec-035-optimizer_hardening-0_0_10-rationale.md`.

### What the finding actually was, re-derived

Each claim was verified against source before any edit; none was accepted on the dispatch prose.

- **`_project_scalar_only_window` is DEFINED at `django_strawberry_framework/optimizer/nested_planner.py::_project_scalar_only_window`** (AST: `FunctionDef`, `:652`).
  `django_strawberry_framework/optimizer/walker.py:81` holds `_project_scalar_only_window = _nested_planner._project_scalar_only_window` — a module-level `Assign`, i.e. an alias. Confirmed by AST
  rather than grep, so "present in the file" cannot masquerade as "defined in the file".
- **`_record_relation_access` genuinely IS `walker.py`'s** (AST: `FunctionDef`, `walker.py:831`). Its
  `[walker]` citation in the same bullet is correct and was left untouched, as instructed.
- **The forwarding chain holds.** `walker.py::_plan_connection_relation` (`:1428`) calls
  `_plan_nested_connection_relation(..., enable_only=enable_only)` (`:1443`), which is walker's own
  import alias for `nested_planner.py::plan_connection_relation` (`:1053`, `enable_only: bool = True`),
  which forwards to the writer, whose body opens `if not enable_only: return child_queryset`.
- **The spec is clean and stays unedited.** `md5` of `docs/SPECS/spec-035-optimizer_hardening-0_0_10.md`
  is `32b8befe880eb6035651d30160d66734` before and after this pass.

### Defect 1 — the stale symbol link the spec-only sweep could not reach

`spec-035-optimizer_hardening-0_0_10-rationale.md` `## Decision 4` ->
`### Alternatives considered (and rejected)`, the "Block scalar appends only …" bullet, changed
``[`_project_scalar_only_window`][walker]`` -> ``[`_project_scalar_only_window`][nested-planner]``.
`[nested-planner]` was already defined and already used in that file, so no link definition was added
and no ref-id became an orphan. No prose in the bullet changed.

### Defect 2 — divergence item 1's falsified present tense, re-measured

The old sentence claimed the spec "names `walker.py::_project_scalar_only_window` … in **eight
places**" and enumerated them. Re-derived rather than inherited, using `git show HEAD:` into a scratch
path outside the repo:

| population | pre-cycle spec (`HEAD`) | spec now | companion now |
| --- | --- | --- | --- |
| reference-style citations of the symbol | **7**, every one targeting `[walker]` | **6**, every one targeting `[nested-planner]` | **1** (the moved rejected alternative), now `[nested-planner]` |
| path-free code-span mentions | 4 | 4 | 3 |
| citations targeting `[walker]` | 7 | **0** | **0** |

So the old enumeration was doubly wrong once Slice 3 ran: wrong on the count (the pre-cycle population
was seven reference citations across ten token sites, not eight places) and wrong on the tense (all
seven are now corrected — six in place, the seventh here). Item 1 was rewritten to state what the spec
used to say in the past tense and what it says now as a measurement, and to correct one further error
of the same class it carried: it named the forwarder as `nested_planner._plan_nested_connection_relation`, which does not exist in that
namespace — `_plan_nested_connection_relation` is `walker.py`'s local import alias for
`nested_planner.py::plan_connection_relation`. Slice 3 caught this for the spec
(`bld-035-slice-3-spec_reconciliation.md` row 1) and wrote the definition name there; the companion
kept the alias name, invisible to the same spec-only sweep.

### Defect 3 — the sweep for the class, with its population

The class is: **a citation that left the spec during the rationale MOVE is invisible to any later
spec-only sweep.** Six instruments, each with its measured population.

1. **Reference-style code-span citations resolved through their ref-id's `.py` target, checked by AST**
   (module-level `def` / `class` vs `Assign` / import alias): **47 checked** in the companion (74
   reference-style citations total, 47 of them `.py`-targeted). One alias defect — defect 1. Four
   residual flags are the `extension.py::_optimize` register (a method cited without its class); the
   spec uses the identical form at four sites, so it is a convention, not drift. Cataloged below, not
   edited.
2. **Bare `path::Symbol` code spans that carry no link** — the blind spot that hid the forwarder error,
   since a `::` span fails an identifier-shaped regex: **52 dotted-or-`::` spans** re-swept. One defect
   (`nested_planner._plan_nested_connection_relation`), folded into the item-1 rewrite. The rest resolve
   (`info.operation`, `definition.interfaces`, `origin.__mro__`, `relay.Node`, bare filenames).
3. **Unlinked identifier-shaped code spans, existence-checked against every `.py` in
   `django_strawberry_framework/` + `tests/` + `examples/`**: **59 distinct** candidates, **0** missing.
   The only non-hits are commit SHAs (`d1dea2fd`, `dd8dc0b3`), the upstream symbol
   `get_possible_concrete_types`, and the three topic slugs from Decision 1.
4. **Decision 5's shipped mechanism** — `_build_fk_id_stub` (`resolvers.py:120`), `_check_n1` (`:218`),
   `_fk_attname_is_deferred` (`:91`), `_FK_ELISION_UNSAFE` (`:88`, module-level `AnnAssign`): all four
   defined at the cited `types/resolvers.py`. **0 defects.**
5. **`apply_connection_optimization`**: AST-confirmed a module-level `FunctionDef` in
   `django_strawberry_framework/optimizer/extension.py`, in that module's `__all__`, imported by
   `connection.py:74`. **Not** a `DjangoConnectionField` method. Divergence item 6's description is
   correct; only its tense needed fixing.
6. **Archived paths and the G1 unconditional claim**: the spec is on disk at `docs/SPECS/`, both
   companions at `docs/SPECS/appx/`; the companion's own link defs resolve there. Swept the companion
   for a surviving unqualified G1 pass-through guarantee — the only candidate is Decision 3's moved
   justification ("consumer-evaluated queryset is left alone"), which is the historical argument, and
   the same Decision's `### Changes this Decision underwent` already names the `spec-045` narrowing and
   links divergence 8 twelve lines below it. **Not a defect**; recorded so the judgement is visible.
   Both `#"substring"` anchors the companion binds into
   `django_strawberry_framework/utils/querysets.py` resolve **exactly once** each.

**Same-class sweep of the divergence list itself.** Defect 2 is not one sentence: items **1-7** were
all written before Slice 3 ran and all carried present-tense claims about the spec that Slice 3
falsified (items 8 and 9 were written by Slice 3 itself and were already correct). Verified one by one
against the current spec — Decision 5's three-part implementation rule (`:186-202`), the Slice 1 live
G1 pin (`:306-316`), the Slice 2 live-test-handoff paragraph, the staged-anchor paragraph naming five
sites (`:271`), the Current-state `apply_connection_optimization` bullet (`:75`), and the four archived
-path sites — then re-tensed each so the past-tense account describes what the spec used to say and
every surviving present-tense claim is true. Fixing item 1 alone would have been the partial claim fix.

### Verification obligations

1. `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-035-optimizer_hardening-0_0_10.md`
   -> `OK: 23 terms - all have glossary entries and at least one spec link.`, **exit 0**.
2. `uv run python scripts/check_trailing_commas.py --check docs/SPECS/appx/spec-035-optimizer_hardening-0_0_10-rationale.md`
   -> **exit 0** (the only `.md` file this pass edited besides this artifact).
3. Companion link integrity: **51 defs / 51 ref-ids used**, 0 undefined, 0 orphan; **30 in-page
   anchors**, 0 dangling; every non-URL link-def path resolves on disk and every `#anchor`-carrying def
   resolves to a real heading in its target.
4. The five shipped-`.py` `#"substring"` spec anchors, re-derived over **579 `.py` files** under two
   flatten variants (whitespace-only and comment-continuation-aware, since a `#` continuation defeats a
   `\s+`-only pattern): `walker.py` and `tests/optimizer/test_walker.py` -> "every projection writer
   checks the gate"; `tests/optimizer/test_walker.py` -> "defaults to enabled" and "subscription
   operations are gated identically"; `tests/types/test_resolvers.py` -> "can defer the FK column
   (both". **All five resolve exactly once**, all inside `## Edge cases and constraints`
   (spec `:280`, `:286`, `:282`, `:281`; section spans `:273-298`).
5. Byte / line counts:

   | file | before | after |
   | --- | --- | --- |
   | `docs/SPECS/appx/spec-035-optimizer_hardening-0_0_10-rationale.md` | 62,423 bytes / 334 lines | 63,468 bytes / 334 lines |
   | `docs/SPECS/spec-035-optimizer_hardening-0_0_10.md` | 125,681 bytes / 514 lines | **unchanged** (`md5` identical) |

**Control run over the spec itself.** The same AST citation instrument was run against
`docs/SPECS/spec-035-optimizer_hardening-0_0_10.md`: **176 `.py`-targeted reference citations checked,
zero stale-path and zero alias defects.** That is what licenses leaving the spec untouched — a
measurement, not an assumption that Slice 3 finished the job.

`uv run ruff format --check .` -> `435 files already formatted`. `git diff --check` over `docs/SPECS/`
-> clean (the tree-wide run flags only `docs/feedback.md`, baseline-dirty and out of scope).

### Notes for Worker 1 (spec reconciliation)

**No `.py` change is owed and nothing routes to Worker 2.** Two observations for the deferred catalog,
neither a defect of this cycle:

- **D10 — `path::Symbol` under-qualification is a repo-wide register, not `035` drift.** Both files
  cite `extension.py::_optimize` and `extension.py::_build_cache_key` (methods of
  `DjangoOptimizerExtension`), `types/resolvers.py::forward_resolver` (a nested closure), and
  `registry.model_for_type` / `registry.definition_for_graphql_name` (methods on `TypeRegistry` reached
  through the module-level `registry` instance). `AGENTS.md` 27's `path::QualifiedName` would want the
  owning class. 17 sites in the spec, 5 in the companion, and the form is consistent across every
  `035` document and predates this cycle. Changing it is a standing-convention question for the
  maintainer, not a `035` reconciliation.
- **D11 — this artifact's own pre-consolidation count was inherited, not measured.** The
  `### Notes for Worker 1` section above says the spec "uses `[nested-planner]` at seven citations"; the
  measured figure is **six** (seven was the pre-cycle `[walker]` population, one of which left the spec
  with the moved text). Left in place as prior-pass content per `ARTIFACT.md`; recorded here so
  `bld-035-final.md` carries the corrected number. This is the third occurrence in the cycle of a
  derived count drifting from its source — the same shape as the six-vs-nine deferred inventory.

The deferred-work inventory this artifact carries is unchanged: **nine** items (D1-D9), with D9 now
**closed** by this consolidation rather than deferred, plus D10 and D11 above. `bld-035-final.md`
should read the catalog as D1-D8 open, D9 closed, D10-D11 new.

### Final status

`final-accepted`. The `revision-needed` finding is closed, the same-class sweep is clean across six
instruments, and the spec needed no edit.

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
