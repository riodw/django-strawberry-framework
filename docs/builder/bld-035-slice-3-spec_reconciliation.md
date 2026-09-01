# Build: Slice 3 — Spec reconciliation against the shipped repo

Spec reference: `docs/SPECS/spec-035-optimizer_hardening-0_0_10.md` (whole document)
Status: final-accepted

A `BUILD.md` `### Procedural-closure slices`-shaped pass: Worker 1 only, no Worker 2 build and no
Worker 3 review, because the slice's whole content is spec `.md` custody and it changes no `.py`
file. Plan and final verification are one combined block below, per that section's artifact shape.

## Plan + Final verification (Worker 1)

### DRY analysis

- **Helper inventory checked.** Not applicable in its usual form: this slice proposes no helper,
  constant, validation branch, or test helper, and writes no `.py` file. The package-wide AST
  inventory exists to prevent duplicated *code* shapes at plan time, and a slice whose entire diff
  is two `.md` files cannot introduce one. Recorded rather than skipped so the omission reads as
  assessed. The prose analogue was run instead and is the next bullet.
- **Existing patterns reused.** The archived-path wording follows the two sibling specs already
  through the `docs/SPECS/NEXT.md` Step 8 sweep: `docs/SPECS/spec-034-permissions-0_0_10.md`
  `### Decision 1 — Spec filename and canonical naming` and
  `docs/SPECS/spec-033-connection_optimizer-0_0_9.md`'s equivalent. `spec-033`'s form is the closer
  fit here because it also names the authoring location the file was archived *from*, which this
  spec's Decision 1 needs so the four corrected sites stay mutually consistent. The corrected
  `## Doc updates` KANBAN bullet follows `spec-034`'s "confirm the spec reference points at this
  spec file" phrasing, and Definition-of-done item 1 follows `spec-033`'s, which already spells the
  `--spec` argument with the archived path.
- **New helpers justified.** None. Five new reference-style link definitions were added to the spec
  (`nested-planner`, `drf-resolvers`, `forms-resolvers`, `mutations-resolvers`, `spec-045`) and three
  to the rationale (`docs-readme`, `glossary-get-queryset-visibility-hook`, `spec-035-goals`), each
  because a corrected sentence now names a file the document did not previously link. Every one is
  used at least once; verified below.
- **Duplication risk avoided.** The naive shape of this reconciliation is to write each correction
  into the spec *and* narrate the correction beside it. That is exactly the chronology `BUILD.md`
  `## Spec rationale extraction` forbids, and it also duplicates the rationale companion, whose
  `## Post-ship divergences (spec vs. HEAD)` section already holds the explanation for divergences
  1-7. The plan therefore fixed each spec sentence to state the current contract flat, appended only
  the two divergences the companion did not yet carry (8 and 9), and added a `### Changes this
  Decision underwent` line under Decisions 3 and 5 pointing at them. No explanation is written twice.

### Implementation steps

Each step is one divergence from the dispatch, re-verified from source before editing (evidence
under `### Claim re-derivation`, below). Section names, not line numbers — the file moved under this
slice's own edits.

1. `_project_scalar_only_window` relocated: correct every path-bearing citation to the live home.
2. Decision 5: state the three-part shipped mechanism the Decision understated.
3. Decision 3 and the G1 statements: state the `spec-045` visibility-boundary narrowing.
4. Slice 1 test plan: replace the reversed live-coverage waiver with the shipped live coverage.
5. Slice 2 test plan and `## Out of scope`: record the G2 live-test handoff as discharged.
6. `## Implementation plan`: rewrite the staged-anchor paragraph, both sentences.
7. Four archived-path sites: state that the spec is at `docs/SPECS/`.
8. Header: delete the stale `0.0.9` on-disk-version parenthetical.
9. `## Current state`: correct the `apply_connection_optimization` attribution.
10. Definition of done: name the rationale companion alongside the terms CSV.

### Test additions / updates

None, and none possible: Worker 1 never writes tests, and this slice changes no runtime behavior
that a test could pin. The verification this slice owes is the mechanical gate list under
`### Verification obligations`, which is run below rather than deferred.

### Implementation discretion items

None. Every wording choice was resolved from the spec, the sibling specs, and the source; nothing was
left to a later pass.

### Spec slice checklist (verbatim)

`BUILD.md` `## Build scope`: this slice is not a spec `## Slice checklist` slice — the spec's four
slices all closed at `0.0.10`, and this cycle is a retrospective reconciliation the spec does not
enumerate. It is also not a review round, so there is no `### Dispatched findings checklist` either.
The dispatch's ten verified divergences are the closest analogue and are tracked as the ten
implementation steps above, each discharged under `### Spec changes made (Worker 1 only)`.

---

### Claim re-derivation

`BUILD.md` `## Claims are proven mechanically, never accepted on prose`. Every divergence was
re-derived from source this pass rather than accepted from the dispatch or from the prior artifacts.

| # | Claim | Instrument | Result |
|---|---|---|---|
| 1 | `_project_scalar_only_window` is defined in `nested_planner.py`, `walker.py` keeps an alias | `grep -rn '_project_scalar_only_window' --include='*.py'` then read both sites | Definition at `optimizer/nested_planner.py::_project_scalar_only_window`; `optimizer/walker.py #"_project_scalar_only_window = _nested_planner._project_scalar_only_window"` is a bare module-level alias. **Confirmed** |
| 1 | The G2 gate travelled with it | Read the relocated function and the forwarding chain | The writer opens `if not enable_only: return child_queryset`; `walker.py::_plan_connection_relation` passes `enable_only=enable_only` to `nested_planner.py::plan_connection_relation`, which passes it to the writer. **Confirmed** — and note the public name in `nested_planner.py` is `plan_connection_relation`; `_plan_nested_connection_relation` is only walker's local import alias, so the spec cites the definition name |
| 2 | Three unnamed mechanisms carry Decision 5's loud fallback | `grep -n '_FK_ELISION_UNSAFE\|_fk_attname_is_deferred\|force_unplanned' types/resolvers.py` then read each | Sentinel, probe (with the `__dict__` + `get_deferred_fields()` test-double carve-out), and the keyword-only `force_unplanned` on `_check_n1` whose `if not force_unplanned and _relation_is_planned(...)` is the bypassed short-circuit; `forward_resolver` sets it exactly on the sentinel path. **Confirmed** |
| 3 | `spec-045` narrows G1 across a visibility hook | Read both cited `utils/querysets.py` anchors and the sync/async runners around them | The seal rebuilds the source and never copies `_result_cache`; the hook result is ALWAYS re-sealed with no identity fast path, "because object identity is not immutability". **Confirmed**, and `docs/README.md` already states the unified contract |
| 4 | The G1 waiver was reversed | `grep -n` both names, then read the resolver and the test | `apps/library/schema.py::Query.all_library_branches_eager_eval` evaluates via `if not queryset:`; `test_query/test_library_api.py::test_library_evaluated_queryset_not_re_executed_over_http` asserts `len(captured) == 1` over `/graphql/`. **Confirmed** |
| 5 | The G2 handoff was discharged | `grep -n 'G2 behavioral tier' test_products_api.py`; `grep -n` the three resolver modules; `grep -n` CHANGELOG | Two pins — `test_g2_mutation_response_keeps_relation_with_bounded_query_count` and `test_g2_serializer_mutation_response_keeps_relation_with_bounded_query_count`; `mutations/resolvers.py`, `forms/resolvers.py`, `rest_framework/resolvers.py` each cite the gate. **Confirmed** |
| 6 | Five `TODO(BACKLOG …)` anchors, one out-of-scope `TODO(spec-035)` | Wrap-aware sweep: per-file `re.sub(r"\s+"," ",text)` flatten, then match, over **576** `.py` files | `TODO(BACKLOG` = **5** (`optimizer/selections.py` above `included_field_selections`; `optimizer/walker.py` inside `_walk_selections` and inside `_selected_scalar_names`; `tests/optimizer/test_walker.py`; `tests/optimizer/test_extension.py`), `TODO(spec-035` = **1**, at `examples/fakeshop/test_query/test_library_api.py` (baseline-dirty, out of scope). **Confirmed** |
| 7 | The spec is archived and DoD item 1's command is broken | `ls` both paths; run the command as written | `docs/spec-035-…md` does not exist; `docs/SPECS/spec-035-…md` and both `appx/` companions do. `check_spec_glossary.py --spec docs/spec-035-…md` → `error: missing file`, **exit 2**. **Confirmed** |
| 8 | `__version__` is far past `0.0.9` | Read the file; `git show HEAD:` for the concurrent bump | Working tree `0.0.15`, HEAD `0.0.14` — a concurrent session's bump in flight, as the dispatch warned. Either way the `0.0.9` parenthetical is false. **Confirmed** |
| 9 | `apply_connection_optimization` is module-level | `grep -rn` across the package | `def apply_connection_optimization` in `optimizer/extension.py`, in that module's `__all__`, imported and called by `connection.py`. Never a `DjangoConnectionField` attribute. **Confirmed** |
| 10 | The rationale companion exists | `ls docs/SPECS/appx/` | Present, 57,185 bytes at slice start. **Confirmed** |

**Wrap-aware instrument, and why a plain grep was not used.** Divergence 6's count is the one number
in this slice that a line-oriented `grep` gets wrong, and it got it wrong twice earlier in this cycle
(`worker-1.md` memory; the build plan's own `#### Partition correction`). Every `TODO(BACKLOG …)`
anchor in the package wraps across two source lines with a `#` continuation marker inside the
parenthesis, so `grep -o 'TODO(BACKLOG[^)]*)'` matches none of them. The sweep run here flattens
whitespace **per file including newlines** before matching and prints its scanned-file population
(576), so a zero would be distinguishable from an unrun instrument.

### Spec changes made (Worker 1 only)

Twenty-eight edits to `docs/SPECS/spec-035-optimizer_hardening-0_0_10.md`, by section. The
**Div** column is the dispatch's divergence number.

| # | Section / heading | Div | Change and reason |
|---|---|---|---|
| 1 | Header, first paragraph | 8 | Deleted the `(the on-disk version reads 0.0.9 as of this writing — the 0.0.9 cut has landed)` parenthetical. It dates a shipped card to a pre-release moment, which is chronology; `worker-1.md` rule 2 deletes such prose rather than updating it |
| 2 | `## Key glossary references`, `AGENTS.md` conventions bullet | 4, 5 | Recast the live-HTTP-priority clause from "nothing shipping in this card is live-reachable yet" to the standing two-tier placement rule. Both guards now carry live pins, so the old clause was false about the repo |
| 3 | `## Slice checklist`, Slice 2 first sub-bullet | 1 | Fourth projection writer re-homed to `nested_planner.py`, naming the `_plan_connection_relation` → `plan_connection_relation` forwarding that carries `enable_only` to it |
| 4 | `## Current state`, walker-entry bullet | 1 | Same re-home; notes `walker.py` keeps only the alias, so a reader opening `walker.py` is not misled |
| 5 | `## Current state`, connection-field bullet | 9 | `apply_connection_optimization` re-attributed to `extension.py` as a module-level function called from `connection.py`, not a `DjangoConnectionField` method |
| 6 | `## Goals`, item 1 | 3 | G1's pass-through scoped to the `_optimize` path, naming the `spec-045` visibility-hook carve-out. The unqualified wording promised a guarantee the package does not offer |
| 7 | `### Decision 1` | 7 | Spec's own location corrected to `docs/SPECS/`, naming the authoring location it was archived from and both `appx/` companions (`spec-033` wording precedent) |
| 8 | `### Decision 3`, after the scope paragraph | 3 | New paragraph stating the visibility-boundary narrowing, with both `utils/querysets.py` `#"substring"` anchors and why the seal wins over the guard |
| 9 | `### Decision 4`, fourth-writer bullet | 1 | Re-homed to `nested_planner.py`; added that it is the one gated writer outside `walker.py`, which is why the gate travels with the function |
| 10 | `### Decision 5`, implementation rule | 2 | Replaced the single "falls back loudly" sentence with the shipped three-part contract: `_fk_attname_is_deferred` probe, `_FK_ELISION_UNSAFE` signal-never-read, `_check_n1(force_unplanned=…)` bypass. The stated outcome is unreachable without the third |
| 11 | `### Decision 8`, source list | 1, 2 | Added `optimizer/nested_planner.py` as a source file of the G2 gate and named the three `types/resolvers.py` symbols Decision 5 depends on |
| 12 | `### Decision 8`, tests bullet | 4, 5 | Restated as the standing two-tier split (plan state package-internal, behavior live) instead of "neither is live-reachable in this card" |
| 13 | `## Implementation plan`, table row 2 | 1 | Files-touched cell splits `walker.py` (three writers + the forward) from `nested_planner.py` (the fourth writer) |
| 14 | `## Implementation plan`, staged-anchor paragraph, **both** sentences | 6 | Opening sentence generalised from the `TODO(spec-035 Slice N)` spelling to the discipline (name the document and the unit that will ship the work); replaced sentence now names five sites, the `TODO(BACKLOG polymorphic_interface_connections …)` form, and the Decision 6 / 7 / R1 bodies. Was false on count (three), form, and owner |
| 15 | `## Edge cases and constraints`, new G1 bullet | 3 | States that a `get_queryset` hook refreshes the queryset before the guard sees it, and that this is deliberate |
| 16 | `## Edge cases and constraints`, G2 every-projection-writer bullet | 1 | Path corrected inside the bullet. **The bound phrase `every projection writer checks the gate` is untouched** — two shipped docstrings anchor to it |
| 17 | `## Test plan`, live bullet | 4, 5 | "none new in this card" replaced by the two live pins that now exist |
| 18 | `## Test plan`, package-internal bullet | 4, 5 | Reason restated as tier complementarity rather than unreachability |
| 19 | `### Slice 1 — G1`, live-coverage waiver | 4 | Waiver replaced by the shipped live coverage (resolver + one-query pin). The declined-alternative reasoning moved to the rationale, which already held it |
| 20 | `### Slice 2 — G2` heading | — | Shortened to end at `extend)`; the Decision 5 test-location clause moved into the section body verbatim in substance. Fixes a **pre-existing** dangling in-page anchor (see below) |
| 21 | `### Slice 2 — G2`, scalar-window test bullet | 1 | Writer citation re-homed |
| 22 | `### Slice 2 — G2`, live-test handoff | 5 | Recorded as discharged, naming both live pins and the three resolver modules that cite the gate |
| 23 | `## Doc updates`, KANBAN card-wrap bullet | 7 | "set the card's spec reference to the **live** working path `docs/spec-035-…`" replaced by `spec-034`'s "confirm the reference points at this spec file", keeping the never-a-per-card-move policy that is still true |
| 24 | `## Out of scope`, `0.0.11` cohort bullet | 5 | Handoff marked discharged; "no obligation is outstanding" |
| 25 | `## Definition of done`, group heading | 10 | `**Spec + companion CSV**` → `**Spec + companion CSV + rationale companion**` |
| 26 | `## Definition of done`, item 1 | 7, 10 | Path corrected in prose **and inside the `--spec` argument**; both `appx/` siblings named, the rationale one linked |
| 27 | `## Definition of done`, item 3 | 1 | Fourth-writer citation re-homed |
| 28 | `## Definition of done`, item 10 | 7 | `SpecDoc` claim corrected the same way as edit 23 |

Plus five link definitions added under `<!-- django_strawberry_framework/ -->` and
`<!-- docs/SPECS/ -->`, alphabetical within their groups: `drf-resolvers`, `forms-resolvers`,
`mutations-resolvers`, `nested-planner`, `spec-045`. Each is used at least once.

**Edit 20 is a defect fix, not a reconciliation item.** `bld-035-slice-1-rationale_extraction.md`
`### Notes for Worker 1` flagged a pre-existing dangling anchor,
`#slice-2--g2-testsoptimizertest_walkerpy--testsoptimizertest_extensionpy-extend`, used twice: the
`### Slice 2 — G2 (...)` heading contained two reference-style links, so its rendered slug is longer
than the anchor written for it. It was verified present in the pre-move copy, so this cycle did not
cause it — but this slice's own edit 22 added a **third** use of it, and verification obligation 3
requires every in-page anchor to resolve. The heading was therefore truncated at `extend)`, which
makes its slug **exactly** the existing anchor string, so all three uses were fixed without editing
any of them. The clause removed from the heading was not deleted: it is the first sentence of the
section body now. Slice 1's warning that renaming the heading breaks its uses is what made the
zero-churn form worth deriving rather than renaming and re-pointing.

### Rationale companion changes made (Worker 1 only)

`docs/SPECS/appx/spec-035-optimizer_hardening-0_0_10-rationale.md`. Append-only during the build
(`worker-1.md` `### Performing the rationale move` rule 4); nothing existing was rewritten except the
two counts and two `### Changes this Decision underwent` lists, all of which are additive in
substance.

- `## Post-ship divergences (spec vs. HEAD)` preamble — "Seven places" → "**Nine**", and a sentence
  attributing items 1-7 to the Slice 1 pass and 8-9 to this one, so a reader can tell which pass
  measured what.
- **New `### Divergence 8 — Decision 3: G1's contract was NARROWED at the visibility boundary by
  `spec-045`.`** Carries what the spec said, what the repo does with both `utils/querysets.py`
  anchors, and — the part that belongs only here — *why the narrowing wins over G1's guarantee*: the
  two contracts point opposite ways at exactly one place, and authority over rows breaks the tie,
  because G1's own justification is "respect what the consumer already did" and the visibility hook
  exists precisely because that is not the last word. Two rejected alternatives recorded with the
  reason each lost (leave the unconditional wording and treat the carve-out as an implementation
  detail; state the boundary only in `## Edge cases`).
- **New `### Divergence 9 — Definition of done item 1: the "Spec + companion CSV" grouping predates
  this file.`** Short; records that the grouping named one sibling because one existed.
- `## Decision 3` → `### Changes this Decision underwent` — one entry for this cycle, pointing at
  divergence 8 and at the waiver replacement (item 3).
- `## Decision 5` → `### Changes this Decision underwent` — one entry naming the three mechanisms the
  Decision understated, pointing at divergence 2.
- Three link definitions added: `docs-readme`, `glossary-get-queryset-visibility-hook`,
  `spec-035-goals`. Each used.

**Nothing was appended for divergences 1-7.** Their explanations already sit in this section, written
by the Slice 1 pass, and `worker-1.md`'s move rules make the companion the single home for an
explanation. Writing them a second time would be exactly the duplication `### DRY analysis` names.

### Verification obligations

All six discharged this pass. Each command was run in this slice, not carried from an earlier one.

1. **`check_spec_glossary.py`** — `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-035-optimizer_hardening-0_0_10.md`
   → `OK: 23 terms - all have glossary entries and at least one spec link.`, **exit 0**.
   The corrected DoD item 1 command is this exact invocation, and its predecessor was proved broken
   first: the pre-edit path returned `error: missing file: docs/spec-035-optimizer_hardening-0_0_10.md`,
   **exit 2**. Running both is what makes "the corrected command works" a measurement rather than an
   assumption — a control the correction would otherwise not have.
2. **`check_trailing_commas.py --check`** on both edited `.md` files → **exit 0**. The `source-layout`
   scaffold (the `<!-- LINK DEFINITIONS -->` delimiter, all 10 canonical group headers in `START.md`
   order, alphabetical defs within each group, paths resolved from the source file's directory) holds
   after the eight added definitions.
3. **In-page anchors, ref-ids, link-def paths** — scripted check over both files, fenced code stripped:
   dangling in-page anchors **none**; used-but-undefined ref-ids **none**; defined-but-unused ref-ids
   **none**; link-def paths missing on disk **none**. The spec's one long-standing dangling anchor is
   resolved by edit 20. *Instrument note:* the first run of this check reported 24 false dangling
   anchors because the slugifier stripped `_` as an emphasis marker, killing `_result_cache` and
   `only_fields` in two Decision headings. Corrected to strip only `**`/`*` and re-run; the corrected
   run is the one reported. A slugifier bug and real link rot are indistinguishable from the output
   alone, which is why the 24 were opened rather than fixed.
4. **The five shipped-`.py` `#"substring"` anchors** — extracted **from the four cohort `.py` files**
   with a wrap-aware flatten rather than retyped from the dispatch, then each counted in the spec:

   | Site | Anchor | Occurrences in spec |
   |---|---|---|
   | `django_strawberry_framework/optimizer/walker.py::_record_relation_access` | `#"every projection writer checks the gate"` | 1 |
   | `tests/optimizer/test_walker.py::test_mutation_scalar_only_connection_window_no_only` | `#"every projection writer checks the gate"` | 1 |
   | `tests/optimizer/test_walker.py::test_subscription_operation_gated` | `#"subscription operations are gated identically"` | 1 |
   | `tests/optimizer/test_walker.py::test_enable_only_defaults_enabled_without_info` | `#"defaults to enabled"` | 1 |
   | `tests/types/test_resolvers.py` (the consumer-`.only()` elision pin) | `#"can defer the FK column (both"` | 1 |

   All five resolve **exactly once**, before and after the edits. Edit 16 changed the interior of the
   bullet two of them bind to and left the bound phrase byte-identical.
5. **Byte / line count.** Spec **117,931 bytes / 498 lines → 125,681 bytes / 514 lines** (+7,750 /
   +16). Rationale **57,185 / 311 → 62,423 / 334** (+5,238 / +23). Both grow, correctly: a
   reconciliation replaces short false statements with longer true ones, and the companion is
   append-only. `BUILD.md` `## The corpus ratchet` binds edits to `BUILD.md`, `ARTIFACT.md`, and the
   four `worker-*.md` role files — none of which this slice touches — so no retirement is owed.
6. **`AGENTS.md` rule 27.** `grep -nE '\.(py|md):[0-9]+'` over both edited files → **no matches**.
   Every source reference written this pass is a `path::QualifiedName` symbol path or a
   `path #"unique substring"` anchor.

### Focused test run

None run, and none owed. `worker-1.md` `## Final verification job` step 5 calls for the focused tests
*the plan calls for*; this slice's plan calls for none, because it writes no `.py` file and changes no
runtime behavior. The build plan's `**Hot-path declaration:** none` and `**Floor-verification scope:**
none` cover the whole cycle and are unchanged by this slice. No `--cov*` flag was used anywhere in
this pass.

### Failability proofs

`None; this pass introduced no new boundary.` — and the inverse is provable rather than merely
asserted: the slice's entire diff is two `.md` files (`git status --short` shows no `.py` file
modified by this pass), so there is no executable line in it and therefore no guard, cap, rejection
path, or validation branch that *could* have been introduced. No fail-open shape landed and none
could.

### Hot-path budget

Not applicable; plan declares no hot path. No slice in this cycle changes runtime behavior.

### Floor verification

Not applicable; plan declares floor-verification scope none. No slice touches a Django / Strawberry /
channels integration seam.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` carries a concurrent session's `__version__`
bump (`0.0.14` → `0.0.15`) and is **baseline-dirty and out of scope** per the build plan; this slice
wrote nothing to it. No `__all__` or re-export change originates in this slice, which is the pin the
spec's Definition-of-done item 11 makes.

### Documentation / release sanity

This slice's diff is documentation, so the checks apply.

- Version strings, shipped statuses, and card IDs: unchanged except the deleted `0.0.9` parenthetical.
  The `Status:` line, the `DONE-035-0.0.10` card id, and the `## [0.0.10]` CHANGELOG reference were
  re-read and are accurate.
- Markdown links introduced by this slice all point at files that exist on disk (obligation 3).
- Spec archival: the spec is at `docs/SPECS/` with both companions at `docs/SPECS/appx/`, and the four
  sites claiming otherwise now say so. The historical record is preserved — the per-card policy that
  the sites were expressing ("never a per-card move; the Step 8 sweep owns it") is still true and is
  kept in the corrected wording.
- No obsolete "coming soon" / "planned" / old-version wording remains in the passages this slice
  deliberately updated: the reversed waiver, the outstanding handoff, and the pre-archive path are the
  three such statements the cycle identified, and all three are gone.
- No script-rendered doc was regenerated (none was touched). The maintainer's scope excludes
  `KANBAN.md` / `docs/GLOSSARY.md` / `docs/TREE.md` / `CHANGELOG.md` / `README.md` / `docs/README.md`,
  and this slice wrote none of them.

### Notes for Worker 1 (spec reconciliation)

Carried to `docs/builder/bld-035-final.md` `### Deferred work catalog`, which Worker 1 authors. Items
1-4 are the four Slice 2 recorded; 5 and 6 are this slice's.

1. **The fifth carry-forward anchor is unretargeted**, at `examples/fakeshop/test_query/test_library_api.py`
   (`# TODO(spec-035): extend this live connection-fragment block ...`) — baseline-dirty, never edited
   and never reverted. Re-measured this pass with the wrap-aware sweep over 576 `.py` files: it is the
   **only** `TODO(spec-035` occurrence in the tree. It should take the
   `TODO(BACKLOG polymorphic_interface_connections - the abstract-return optimizer entry card)` head
   once the concurrent session's work lands. **This is the one anchor that makes `BUILD.md`
   `## Cross-slice integration pass` step 6's sweep non-empty** — a recorded deferral, not a finding.
2. **The two package test-tree anchors are now deletable on the spec's side of the argument, but not
   yet on the code's.** Slice 2 kept them because the spec's G3 deferred test-plan heading names no
   file, unlike its Slice 1 and Slice 2 headings, so each anchor held a file-placement judgement
   existing nowhere else. This slice did **not** write that placement into the deferred test plan: the
   dispatch's ten divergences do not include it, and inventing the follow-up card's test-file layout
   is that card's spec's decision, not this reconciliation's. The condition is unchanged and the
   anchors stay.
3. **Nine out-of-scope rule-27 raw line citations** naming *other* specs — `tests/mutations/test_sets.py`
   (4, spec-036), `tests/optimizer/test_extension.py` (4, spec-033), `examples/fakeshop/config/settings.py`
   (1, spec-039). Belongs to those cards. Record it as an occurrence **list**, not a total, and specify
   a whitespace-flattening instrument: a comment-continuation `#` between `line` and the number defeats
   any `\s+`-only pattern, and a `line`-without-`s?` pattern is blind to `lines 124-130`.
4. **`tests/types/test_resolvers.py`-style bare `(line NNN)` comments** citing a source file's own
   lines — same rot shape against a different document; wants `path::Symbol`.
5. **The `## Implementation plan` delta-table preamble still says "Line deltas were planning estimates;
   G1 and G2 have since shipped".** That is chronology by the letter of `BUILD.md` `## Spec rationale
   extraction`, and this slice left it: it is not one of the dispatch's ten divergences, it is not
   false, and it is doing real work (it tells a reader the table's last column mixes an estimate with a
   realized figure). Flagged so a future custodian judges it rather than inheriting it, and so that
   leaving it reads as decided.
6. **The rationale companion's `## Post-ship divergences` section now mixes two list forms** — items
   1-7 as numbered list entries, 8-9 as `###` subheadings, because the two new entries carry rejected
   alternatives and needed the structure. The preamble says so explicitly, so it is navigable, but if a
   later pass adds a tenth it should either follow the subheading form or normalise all of them.

### Summary

The spec now describes the repo. Ten verified divergences were re-derived from source and written into
`docs/SPECS/spec-035-optimizer_hardening-0_0_10.md` across 28 edits as flat present-tense contract —
no amendment block, no "as of Revision N", no chronology — and the explanation for each lives in the
rationale companion, which gained two new divergence entries and two `### Changes this Decision
underwent` pointers. The relocated fourth projection writer, Decision 5's three-part strictness-visible
fallback, G1's `spec-045` visibility-boundary narrowing, the reversed live-coverage waiver, the
discharged G2 handoff, the staged-anchor inventory, the archived path at four sites, the stale version
parenthetical, and the `apply_connection_optimization` misattribution are all corrected; the rationale
companion is acknowledged in the Definition of done. One pre-existing dangling in-page anchor was fixed
as a side effect, by a heading truncation whose slug equals the anchor already in use, so none of its
three uses needed editing.

Nothing normative changed. G1 / G2 / Decision 5's contracts, the G3 deferral with R1-R3, the Slice 3
deferred test plan, the non-goals, and the borrowing posture are all still accurate and were left
alone. Slice 3 / G3 remains `[deferred]` and still ships no runtime code. The five shipped-`.py`
`#"substring"` anchors all still resolve exactly once, the bound phrase `every projection writer checks
the gate` byte-identical. No `.py` file and no out-of-scope doc was touched.

Final status: **`final-accepted`**.

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
