# Build: Slice 2 — Spec reconciliation (`spec-033`)

Spec reference: `docs/SPECS/spec-033-connection_optimizer-0_0_9.md` (whole file) + `docs/SPECS/appx/spec-033-connection_optimizer-0_0_9-rationale.md` (whole file)
Status: final-accepted

**Shape.** Worker-1-owned slice of the `033` residual reconciliation cycle ([`build-033-connection_optimizer-0_0_9.md`][build-033] `## Cycle shape` item 3), with no Worker 2 build pass and no Worker 3 review pass, so it carries one combined Plan + Final-verification block ([`docs/builder/BUILD.md`][build-md] `### Procedural-closure slices`). The `## Build report (Worker 2)` and `## Review (Worker 3)` sections of [`ARTIFACT.md`][artifact-md] are deliberately absent, not omitted; the validation run, the failability position, and the hot-path / floor declarations are folded into `## Final verification (Worker 1)`.

Input: the three read-only conformance cohorts' `### Notes for Worker 1 (spec reconciliation)` sections ([R1a][bld-1a], [R1b][bld-1b], [R1c][bld-1c]) plus [Slice 0][bld-0]'s. Every finding in them was already verified against source by its cohort and **was not re-verified from scratch**; every *count* restated below was re-derived at the moment it was written.

Raw `path:NN` references appear only in this file, per [`AGENTS.md`][agents] #"Source refs in docs and code comments" (per-cycle scratchpad carve-out). Every citation this pass wrote **into the two spec files** is symbol-qualified.

---

## Plan (Worker 1)

### Spec status-line re-verification

Read the spec's header block (title, shipped-in line, `Status:`, Owner, Predecessors, the rationale-companion pointer) at the start of this spawn. The `Status:` line still describes the build's current state — the card is `DONE-033-0.0.9`, all seven slices final-accepted, the unticked-checklist convention still holds, and no predecessor doc it names has been deleted. **Two header edits were required by the reconciliation itself**, not by status drift, and both are recorded under `### Spec changes made (Worker 1 only)`: the `Status:` line's Slice-2 clause asserted the retired per-parent fallback for ambiguous empty windows, and its Slice-1 clause said the selection helpers consolidated "into the walker". The header's `pyproject.toml` clause in the version-boundary sentence was also corrected (see item 12 below).

### DRY analysis

- **Helper inventory checked.** Not applicable in the package sense: this pass edits two markdown files and no `.py` file, so the package-wide AST inventory ([`worker-1.md`][worker-1] `### Package-wide helper inventory before helper planning`) has nothing to prevent. The analogous risk for a reconciliation pass is **prose duplication between the spec and its companion**, and it is answered below.
- **Existing patterns reused.** The `**Post-ship:**` bullet under `### Changes this Decision underwent`, the build-time record in the same section, and the `## Non-Decision deliberation` catch-all are the companion's own shapes, established by Slice 0 from the `spec-032` companion. No new section kind was invented in either file. The corrected-contract voice was calibrated against `docs/GLOSSARY.md`'s `## Connection-aware optimizer planning` entry, which is **already current** on marker rows, the conditional count, `last: 0`, the strategy seam, and keyset cursors — it is the one standing doc that had already absorbed the post-ship shape, and reusing its framing keeps the two consistent.
- **New helpers justified.** None.
- **Duplication risk avoided.** The governing rule is that the spec states the corrected contract and carries **no** chronology, while the companion carries what changed, when, why, and what was rejected. Enforced as a postcondition: the spec contains zero occurrences of `Post-ship`, `Revision N`, `as of`, `originally`, or a commit hash, and every commit hash and "idea #N" label in this cycle lives only in the companion. The one deliberate overlap is that a Decision's corrected contract and its companion bullet describe the same behavior from two vantage points — which is the split the mechanism exists to produce.

### Dispatched findings checklist

This is a reconciliation slice, not a spec slice: `spec-033`'s `## Slice checklist` has no entry for it (all seven spec slices shipped in `0.0.9`). The tick-and-audit surface is the cohorts' divergence inventory, one box per finding, cohorted by owning artifact.

**R1a — Decisions 3 / 4 / 6 / 9 / 11**

- [x] D1 — Decision 9's consolidation target is `optimizer/selections.py`, the module the Decision rejects by name; two of its six named symbols never existed
- [x] D2 — Decision 11's module map is short by seven modules and six test files; `nested_planner.py` has no test twin
- [x] D3 — `_dst_total_count` is conditional; the spec's own named test pins the inverse
- [x] D4 — Decision 6 fallback shape 2 is inverted: divergent aliases are planned, one window per response key
- [x] D5 — the matrix has nine fully-unplanned shapes, not four; the DISTINCT guard moved pre-build and generalised; unsupported relation kinds no longer raise
- [x] D6 — `first: 0` / overshot `after:` are served from marker rows (Slice-1-side sites only; R1b owns the Decision 5 body)
- [x] D7 — the `relay_max_results` cap passes through a request-policy `max_page_size` ceiling
- [x] D8 — the fetch mechanism is a pluggable strategy seam with three backends
- [x] D9 — the products premise cites an implicit `"both"` default that is now `"connection"` (**partially landed — see the deliberate non-landings below**)
- [x] D10 — the Strawberry-floor Risks item is resolved at `HEAD`
- [x] N2 — the phrase "post-build DRY refactor" is wrong-sized and retired
- [x] N3 — the number **four** swept as a numeral across its four grammars, not as a phrase
- [x] Medium — the ten `spec-033 Decision 11` cursor-parity citations: **spec side confirmed correct, no edit**; the cursor-parity invariant stays sited on Decision 4

**R1b — Decisions 5 / 8**

- [x] D5-1 — ambiguous empty windows are served from marker rows, not fallen back (11 spec homes); `last: 0` needed a new statement and got one
- [x] D5-2 — the annotation probe reads `_dst_row_number` only
- [x] D5-3 — the wrapper carries no slice metadata (build-time)
- [x] D5-4 — `pageInfo` page flags are a four-way fork
- [x] D5-5 — there is one `resolve_connection`, not two
- [x] D5-6 — the resolver probes a per-response-key `to_attr` first
- [x] D5-7 — keyset cursors ship and fork Decision 5 at five sites; the Non-goal and Out-of-scope entries are spent
- [x] D5-8 — a third fetch strategy and a runtime single-parent fast path feed the same `to_attr`; the degradation list stopped being closed
- [x] D8-1 — condition 1 is `strictness != "off"` from a `ContextVar`; condition 2 reads two publish channels
- [x] D8-2 — `_build_relation_connection_resolver` gained two parameters, not one (build-time)
- [x] D8-3 — `### Error shapes`'s "No new error surface" is false
- [x] `## Current state` lines 104-105 — **deliberately not chased to `HEAD`**; the section was dated instead (see below)

**R1c — Decisions 7 / 10 / 12, the products conversion, the live pins, the census**

- [x] M1 — Decision 6 item 2 inverted, 8 spec homes (re-derived; landed with R1a's D4)
- [x] M2 — `_dst_total_count` conditional, 3 spec homes (landed with R1a's D3)
- [x] M3 — the `first: 0` / overshot-`after:` contract inverted; `last: 0` is the only survivor
- [x] M4 — Decision 6 item 3's "neither suppress nor shape the window" is false of this card's own seam; the `## User-facing API` no-new-surface sentence is **left as-is**, correctly
- [x] M5 — card-id rot, 9 occurrences plus three further populations
- [x] M6 — Decision 12 / DoD item 12 false as present tense; dated instead
- [x] L2 — `test_m2m_shared_child_partitions_per_parent` no longer exercises a shared-child scenario
- [x] L3 — the products `relay_max_results` Slice-6 instruction rests on a spent premise
- [x] L4 — the `ValueError` half of the same sentence is wrapped before it reaches a consumer
- [x] L5 — `TestDeterministicOrderHoistParity`'s parity premise is structurally unprovable; restated as the single-source contract
- [x] L9 — five pre-archive path occurrences across four sites
- [x] Job 1 precision note — the Slice-3 cache test pins two **keys**, not two windows
- [x] The unnamed-but-promised Slice-6 pin is named
- [x] L1, L6, L7, L8 — **not spec defects**; recorded as deferred / no-action (below)

**Escalations — recorded, not resolved**

- [x] R1b M1 — the `connection_to_attr` strictness probe answers "attribute present", not "window consumed"
- [x] R1a DRY-1 — `window_partition_for_prefetch` has zero production callers
- [x] R1a Medium — ten dead back-compat aliases in `walker.py`
- [x] R1c note 9 — the strategy seam has no owning spec

### Implementation steps

1. Read all three cohort artifacts and Slice 0's in full; read both spec files end to end.
2. Re-derive every inherited count before restating it (results under `### Re-derived counts`).
3. Rewrite each stale spec passage to state the corrected contract directly, working from the cohorts' per-site lists and verifying each site still said what the list said (two passes had edited the spec since some line numbers were taken, so every edit matched on text, never on line number).
4. Sweep parallel sites by the shortest distinctive token, not the phrase — the numeral `four`, the bare `051`, the path spelling, the `_dst_total_count` pairing.
5. Land each correction's `**Post-ship:**` or build-time record in the companion under the owning Decision, or under `## Non-Decision deliberation`.
6. Verify: link definitions, in-page anchors, cross-file anchors, every source citation the pass wrote, both gate scripts, `git diff --check`, and a foreign-citation census as a postcondition.

### Test additions / updates

None, and none possible: this pass edits two markdown files and no `.py` file. `pytest` was **not** run — not needed and not permitted for this pass, and never with a `--cov*` flag anywhere in this cycle ([`docs/builder/BUILD.md`][build-md] `## Coverage is the maintainer's gate, not a worker's tool`).

### Implementation discretion items

None delegated — single-worker pass, no builder. Four choices were **assessed and decided here** because each could otherwise have been resolved silently and wrongly:

- **`## Current state` is not chased to `HEAD`.** R1b flagged that lines 104-105 are cited *as inputs* by Decisions 5 and 8, so a reader follows them expecting current fact. The section's own opener frames it as the repo before the build, and rewriting a dated snapshot to today's shape would destroy the only record of what the card was written against. Decided: keep the section dated and make the dating unmissable by strengthening its opener ("**as of this spec's authoring, before the build** … It is a dated snapshot on purpose and is not maintained against `HEAD`; where a Decision below cites it as an input, the Decision itself states the current contract"). Every Decision that cites it now states the current contract itself, so the pointer no longer misleads.
- **Two Decision headings were renamed; ten were not.** Decision 9's heading asserted a module location that is flatly false, and Decision 6's opened a colon-list that grouped divergent aliases under "Fallback shapes" when they are planned. Both were renamed and their anchors swept (8 and 26 occurrences respectively, all inside the two files this slice owns; zero references anywhere else in the tree). **No Decision was renumbered.**
- **`## User-facing API`'s "this card adds no public symbol" is left exactly as written**, per the boundary R1c drew: it is true *of this card*, `git diff -- django_strawberry_framework/__init__.py` is empty, and none of the four later seam surfaces is a package-root export. The seam's shape is stated in Decision 4 and Decision 6, where a later commit changed what *this card's* seam does; the companion carries a `**Post-ship:**` note so a reader of the final record is not misled either way.
- **The cursor-parity invariant stays sited on Decision 4.** Worker 0 pinned this before dispatch and R1a's evidence agrees: Revision 2's finding 7 deliberately promoted it *out of* Decision 11. The spec side needed no edit; the ten `spec-033 Decision 11` citations in source and tests are the side that moves, and the concurrent R2 cohort owns them.

---

## Final verification (Worker 1)

### Re-derived counts

Every count below was measured at the moment it was written, never inherited.

| Claim | Re-derived | Source's figure |
|---|---|---|
| R1c census: present-and-pinning | **66** | The census **table** says 66 and the build plan's Slice summary says **68**. 76 − 3 (present, no longer pinning) − 4 (renamed) − 3 (absent, contract dropped) = **66**, and counting the table's 76 rows by bucket gives the same. **66 is correct; the 68 is not propagated anywhere in this pass.** |
| `051` card-id rot | **9 occurrences** — 1 in the spec (DoD item 11), 8 in the companion (7 bare `` `051` ``, 1 `TODO-BETA-051-0.1.5`) | R1c: 9 ✓ (Slice 0: 7, measured with a bare-numeral grep that cannot see a full id) |
| `TODO-BETA-062-0.1.5` already correct — do not touch | **8** (5 spec + 3 companion), now 13 spec + 11 companion after the sweep | R1c ✓ |
| `TODO-BETA-047-0.1.2` → `TODO-BETA-056-0.1.2` | **2**, both in the spec | R1c ✓ |
| `TODO-ALPHA-034/035-0.0.10` → `DONE-` | **6** — `035` ×3 spec + ×2 companion, `034` ×1 spec | R1c ✓ |
| Pre-archive path spelling | **5 occurrences across 4 sites** — spec ×4 (DoD item 1 carries two) + companion ×1 | R1c's L9: 5/4 ✓ (Slice 0: 3) |
| Fully-unplanned shapes at `HEAD` | **9** | R1a's D5 ✓ |
| `unwindowable_child_queryset_reason` reasons | **5** (`sliced`, `select_for_update`, `combined`, `distinct`, `values`) | R1a ✓ |
| Modules Decision 11's map was short by | **7** (`selections`, `nested_fetch`, `nested_planner`, `lateral_fetch`, `single_parent_fetch`, `join_taxonomy`, `keyset`), or **8** counting `utils/connections.py`, which the map *does* name | Both figures are true under different subjects; the spec states seven-unnamed and the companion states eight-landed, each with its subject spelled out |
| Test files Decision 11's map was short by | **6** | R1a ✓ |
| `optimizer/nested_planner.py` size | **1,436 lines**, and no `tests/optimizer/test_nested_planner.py` exists | R1a ✓ |
| `optimizer/` modules on disk | **13** excluding `__init__.py` | R1a ✓ |
| Decision 9 anchor occurrences swept | **8** (6 spec + 2 companion), zero elsewhere in the tree | new measurement |
| Decision 6 anchor occurrences swept | **26**, zero elsewhere in the tree | new measurement |
| Foreign `spec-033` citations, tracked files, excluding the pair and this cycle's plan + artifacts | **277 occurrences across 43 files** | Slice 0 measured 278/43 before this cycle's artifacts existed and while the concurrent R2 cohort was not yet writing `.py` files; the scope is the same and the one-occurrence delta is R2's live edits, not a break |

### Verification commands and their real results

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-033-connection_optimizer-0_0_9.md` → `OK: 38 terms - all have glossary entries and at least one spec link.`, exit 0. Same 38 as after Slice 0; **no term was added or lost**, and `docs/SPECS/appx/spec-033-connection_optimizer-0_0_9-terms.csv` was not touched.
- `uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-033-connection_optimizer-0_0_9.md docs/SPECS/appx/spec-033-connection_optimizer-0_0_9-rationale.md` → exit 0. Both files keep the single `<!-- LINK DEFINITIONS -->` delimiter and all 10 canonical group headers in order; the twelve definitions this pass added (nine in the spec, three in the companion) are alphabetical within their groups.
- `git diff --check` → exit 0.
- **Link-definition and anchor proof, both files.** Zero undefined `[text][ref-id]` uses, zero unreferenced definitions, zero definition targets missing on disk, zero dangling in-page `](#…)` anchors, and zero dangling **cross-file** anchors (each `path#anchor` definition resolved against the target file's real headings). Run after every edit batch and again at the end.
- **Source-citation proof.** Every `path #"substring"` and `path::Symbol #"substring"` citation this pass wrote into the spec was matched against the file it names: each substring occurs **exactly once**. One citation was rewritten because a markdown code span cannot carry the escaped quotes its literal needed (`fallbacks.append((resp_key, "last: 0"))` → `optimizer/nested_planner.py::_divergent_key_windows #"if reverse and limit == 0:"`, re-verified as a single occurrence).
- **Renamed-heading sweep.** `grep -r` over every `.md` / `.py` / `.html` in the tree for the two old anchor slugs and the two old heading phrases: zero hits outside the two files this slice owns and the cohort artifacts that reported them.
- No `ruff` invocation: this pass touched no `.py` file.
- **No `pytest`.** Not needed and not permitted for this pass; no `--cov*` flag was used anywhere.

### Declarations

- **Hot-path declaration:** `none`. This pass touches no runtime code.
- **Floor-verification scope:** `none`. No Django / Strawberry / channels integration seam is touched, so no floor venv was built. Where a floor fact was needed it was taken from the cohorts' cited readings, never from memory: the supported floor is Django 5.2.16 / Python 3.10 / strawberry-graphql 0.316.0 ([`BUILD.md`][build-md] `## Floor verification`); `pyproject.toml` now declares `strawberry-graphql>=0.316.0` and `Django>=5.2.16` (R1a's D10); the shared `.venv` read as Django 6.1 / strawberry-graphql 0.324.0 / Python 3.14.2 (R1b's cited `uv pip list`) and is **not** the floor.
- **Ownership partition:** the four files this cohort owns per the build plan — `docs/SPECS/spec-033-connection_optimizer-0_0_9.md`, `docs/SPECS/appx/spec-033-connection_optimizer-0_0_9-rationale.md`, this artifact, and `docs/builder/worker-memory/worker-1.md`. `git status --short` after the pass shows those plus the ten `.py` files the concurrent R2 cohort owns, the untracked `0_0_14.md`, Worker 0's plan, and the three R1 artifacts. **Nothing outside the partition was written**; R2's `.py` edits were neither reviewed nor reverted ([`AGENTS.md`][agents] rule 34), and `0_0_14.md` / `docs/builder/bld-003-final.md` were neither read as this cycle's nor touched.
- **Failability position:** `None; this pass introduces no boundary.` It ships no executable byte. The analogous proof for a text pass is the citation-and-anchor verification above, which fails loudly when a reference stops resolving.

### Measurements

| File | Before | After | Delta |
|---|---|---|---|
| `docs/SPECS/spec-033-connection_optimizer-0_0_9.md` | 137,803 bytes / 643 lines | 160,376 / 686 | +22,573 / +43 |
| `docs/SPECS/appx/…-rationale.md` | 70,960 / 367 | 99,844 / 410 | +28,884 / +43 |

The pair grew by 51,457 bytes. That is expected and is the shape the cycle's plan predicts: Slice 0 removed 40,594 bytes of deliberation from the spec, and Slice 2 replaces four-shape summaries with nine-arm matrices, adds the strategy seam and the `last: 0` contract the spec had no home for, and lands 29 post-ship / build-time records the companion did not carry. The corpus ratchet in [`BUILD.md`][build-md] `## The corpus ratchet` governs the six workflow docs, none of which this pass touches.

### Checklist audit

Every box in `### Dispatched findings checklist` is `- [x]` and each contract landed on disk, except the five recorded below as deliberate non-landings, each of which is ticked because the *decision* landed rather than an edit. No box is ticked without a landed contract and none is left silently un-ticked.

### Divergences deliberately NOT landed, and why

1. **`## Current state` was dated, not updated** (R1b's D5-5 / D8-1 note; R1a's D9 site `:107`). The section is a self-declared snapshot of the repo before the build, and rewriting it would erase the record the Decisions were written against. Its opener now says so explicitly. The Slice-6 checklist's `"both"` sentence (`:81`) is likewise a true statement about `DONE-032-0.0.9`'s default at the time and was left; Decision 4's `to_attr`-isolation bullet, which is present-tense normative, **was** corrected to say `"both"` is an explicit opt-in.
2. **`## User-facing API`'s "This card adds no public symbol, no `Meta` key, and no constructor argument"** — left verbatim. True of this card; the four later seam surfaces reach consumers through `optimizer/hints.py`, the extension constructor, and `conf.py`, never the package root.
3. **The cursor-parity invariant's siting** — no spec edit. It stays on Decision 4 where Revision 2's finding 7 put it; the ten `spec-033 Decision 11` citations in `.py` files are the side that moves, and the concurrent R2 cohort owns exactly those files.
4. **`## Non-goals`' sidecar-filtered-nested-connections entry** — R1a verified it is still accurate at `HEAD`, so it was left unchanged rather than "fixed" alongside its neighbours. Recorded because a sweep of that section would otherwise look incomplete.
5. **`## Edge cases`' "Parents with no related rows" bullet** — R1b explicitly marked it still true and said not to change it. Its *reason* did change (an empty list now proves childlessness rather than an `offset == 0` / `limit > 0` precondition proving it), so the bullet was restated to give the current reason while keeping the same outcome. This is the one item on this list where a small edit landed against a "do not change" note, and it is called out for that reason.
6. **The three escalations and the strategy-seam ownership question** — recorded in the companion under `## Non-Decision deliberation` with each cohort's resolution paths, and surfaced under `### Deferred work` below. **No spec contract was changed to pre-empt the maintainer's answer, and no `.py` file was touched.**
7. **`docs/SPECS/appx/spec-033-connection_optimizer-0_0_9-terms.csv`** — not touched. No correction introduced a net-new glossary term; the gate still reports the same 38.

### Summary

`spec-033` now reads as a clean current contract: nine refusal arms instead of four fallback shapes, divergent aliases planned one window per response key, marker rows serving `first: 0` and overshot `after:`, `last: 0` as the one always-fallback shape, a conditional `_dst_total_count` and a four-way `pageInfo` fork, one `resolve_connection`, a three-backend strategy seam feeding the `to_attr` this card created, keyset cursors stated as a spent Non-goal, the selection helpers in `optimizer/selections.py`, and a module map that names all of it plus the one module with no test twin. No chronology survives in the spec; **29** records now sit in the companion under their owning Decisions — 24 `**Post-ship:**` bullets, 3 build-time records, and 2 inline post-ship resolutions on `## Risks and open questions` items — each naming the shipped behavior and the commit that changed it. Card-id and path rot are swept across both files. Both gate scripts pass, every anchor and link definition in both files resolves in both directions, and every source citation the pass wrote matches exactly one line of the file it names.

### Spec changes made (Worker 1 only)

Sites are cited by section and by the text they carry, not by line number, since two passes had already shifted the file and a third is running concurrently. Each entry names the cohort finding that drove it.

**Header, `## Key glossary references`, conventions**

1. **`Status:` line, Slice-2 clause** — "with a per-parent fallback for ambiguous empty windows" → "falling back per parent whenever the window is absent or unsafe to consume". *R1b D5-1.*
2. **`Status:` line, Slice-1 clause** — "selection-helper consolidation into the walker" → "selection-helper consolidation". *R1a D1.*
3. **Header version-boundary sentence** — dropped `pyproject.toml` from the bump-artifact list. *R1c M6.*
4. **`Meta.connection` glossary bullet** — the ambiguous-empty per-parent fallback replaced by the marker row and the observability-conditional count. *R1b D5-1, R1a D3.*
5. **`OptimizerHint` glossary bullet** — "the other hint shapes do not affect it in `0.0.9`" → `strategy(...)` selects the backend and a `to_attr`-bearing `prefetch(...)` is refused. *R1c M4, R1b D8-3.*
6. **`Meta.search_fields` glossary bullet** — `TODO-BETA-047-0.1.2` → `TODO-BETA-056-0.1.2`. *R1c M5.*
7. **`docs/TREE.md` conventions bullet** — the "build proper adds no new source module" framing and the "post-build DRY refactor adds exactly one" parenthetical replaced by a pointer at Decision 11's enumeration and the one open mirror exception. *R1a D2, N2.*

**`## Slice checklist`**

8. **Slice-1 helper sub-bullet** — the six-symbol move into `walker.py` replaced by the public names in `optimizer/selections.py` that both consumers import. *R1a D1.*
9. **Slice-1 step (b)** — the `query.distinct` check replaced by the five-reason base-queryset classifier. *R1a D5.*
10. **Slice-1 `plans.py` sub-bullet** — `_dst_total_count` made conditional. *R1a D3, R1c M2.*
11. **Slice-1 fallback sub-bullet** — the four-shape list replaced by the nine refusal arms, with divergent aliases moved to the planned side. *R1a D4/D5, R1c M1.*
12. **Slice-2 resolver sub-bullet** — one parameter → two (`relation_field_name` and `declaring_type`); probe reads the row number only; per-key `to_attr` named. *R1b D8-2, D5-2, D5-6.*
13. **Slice-2 `resolve_connection` sub-bullet** — two paths → one override; ambiguous-empty fallback → marker rows; the wrapper's `fallback` callable named. *R1b D5-5, D5-1, D5-3.*
14. **Slice-4 strictness sub-bullet** — condition 1 restated as `strictness != "off"` from the `ContextVar`, condition 2 as two publish channels. *R1b D8-1.*
15. **Slice-5 mirror sub-bullet** — "divergent-alias fallback" → "per-response-key divergent-alias windows". *R1b D5-6.*

**`## Current state`, `## Goals`, `## Non-goals`**

16. **`## Current state` opener** — strengthened to declare itself a dated, deliberately un-maintained snapshot. *R1b's "Also for Slice 2" note; see discretion item 1.*
17. **Goal 2** — ambiguous-empty per-parent fallback → marker rows; `totalCount` gated on observability. *R1b D5-1, R1a D3.*
18. **Goal 7** — `pyproject.toml` dropped from the version-artifact list. *R1c M6.*
19. **Non-goal: keyset cursors** — rewritten from "stay in `BACKLOG.md` item 39" to a statement of the current relationship, naming all five fork sites and the cursor-field precedence. *R1b D5-7.*
20. **Non-goals: G1-G3 guards and the permissions subsystem** — `TODO-ALPHA-035-0.0.10` → `DONE-035-0.0.10`, `TODO-ALPHA-034-0.0.10` → `DONE-034-0.0.10`, with the surrounding "lands after this card" / "when it lands" tenses corrected. *R1c M5.*

**`### Error shapes`**

21. **"No new error surface"** — replaced by the inherited-guards sentence plus the five raising surfaces the window machinery actually added, each fail-closed. *R1b D8-3.*

**`## Architectural decisions`**

22. **Decision 1** — the spec's location restated as its archived path, with the authoring path named as history, on the `spec-032` post-move model. *R1c L9.*
23. **Decision 4, new opening paragraph** — the strategy seam: three backends, the runtime single-parent fast path, the three selection surfaces, and the statement that everything below it is strategy-independent. *R1a D8, R1c M4.*
24. **Decision 4 `**Partition key**`** — "Unsupported relation kinds raise" → `classify_relation_join` never raises and returns `windowable=False`; `GenericRelation` added; the raising helper's surviving contract named. *R1a D5.*
25. **Decision 4 `**Window**`** — `_dst_total_count` made conditional, with the `FetchMode` derivation and the n+1 sentinel named. *R1a D3, R1c M2.*
26. **Decision 4 `**DISTINCT-target guard**`** → **`**Unwindowable child querysets are classified before the window is built**`** — five reasons, base queryset, one strategy-independent gate. *R1a D5.*
27. **Decision 4 `**Slice arithmetic**`** — the request-policy `max_page_size` ceiling added; the trailing fallback list repointed at Decision 6's refusal arms. *R1a D7, D4.*
28. **Decision 4 `**`to_attr` isolation**`** — the per-key `_dst_<field>$<key>_connection` grammar and its `LOOKUP_SEP` reason added; `"both"` restated as an explicit opt-in. *R1a D4, D9.*
29. **Decision 5, resolver bullets** — per-key probe order added; the wrapper's real two fields and the reason it can carry no slice metadata; the probe reads the row number only. *R1b D5-6, D5-3, D5-2.*
30. **Decision 5, `resolve_connection` paragraph** — two paths → the single override plus the `ClassVar` count opt-in. *R1b D5-5.*
31. **Decision 5, `pageInfo` bullet** — the four-way `has_next_page` fork and the keyset `has_previous_page` clause. *R1b D5-4.*
32. **Decision 5, `totalCount` bullet** — the count-free recovery path added. *R1b D5-4, R1a D3.*
33. **Decision 5, empty-wrapper bullet** — rewritten as the marker-row contract, with "an empty list now proves childlessness". *R1b D5-1, R1a D6, R1c M3.*
34. **Decision 5, wrapper-absent paragraph** — the closed cause list opened; a new `last: 0` paragraph added, the contract having had no home in the spec at all. *R1b D5-8, D5-1.*
35. **Decision 6, whole body and heading** — heading `Fallback shapes: sidecar input, divergent aliases, hints, and scalar-only connections` → `Refusal arms, divergent aliases, hints, and scalar-only connections`, anchor swept in both files (26 occurrences); four shapes → nine arms with per-key / whole-relation granularity and a decision site each; divergent aliases and scalar-only selections moved to an explicit not-a-fallback section; the hints item rewritten around `strategy(...)` and the refused `to_attr` hint. *R1a D4/D5, R1b D8-3, R1c M1/M4.*
36. **Decision 8, three-condition guard** — restated as a numbered list with the `ContextVar`, the two planned-set channels, and the fail-open the stash-only reading would reintroduce. *R1b D8-1.*
37. **Decision 9, heading and body** — heading `… consolidate into the walker` → `… consolidate into one module both consumers import`, anchor swept in both files (8 occurrences); body restated around the public `optimizer/selections.py` names, both consumers importing, and no forced import direction. *R1a D1.*
38. **Decision 11, whole body** — the "no new module" map replaced by the modules the contract actually touches, the seven unnamed ones, the enlarged `utils/connections.py` inventory, the "no public surface" line, the six unnamed test files, and the `nested_planner.py` mirror exception. *R1a D2, N2.*
39. **Decision 12 body** — `pyproject.toml` dropped, with the single-source rule stated. *R1c M6.*

**`## Implementation plan`, `## Edge cases`, `## Test plan`, `## Doc updates`, `## Out of scope`, `## Definition of done`**

40. **Slice-1 and Slice-2 table rows** — `selections.py` added to the files column; "fallback non-planning ×4" → the unwindowable-child-queryset and per-response-key phrasing; the ambiguous-empty fallback pin → the marker-row and `last: 0` pins; the resolver's second parameter. *R1a D1/D4/D5, R1b D5-1/D8-2.*
41. **Edge case: identical / divergent aliases** — rewritten to the per-key windows. *R1a D4.*
42. **Edge case: M2M shared children** — narrowed to what the named test pins, with the live test that earns the consumer-visible half. *R1c L2.*
43. **Edge cases: `first: 0` / overshot `after:` and parents with no related rows** — marker rows; the empty-list proof; a new `last: 0` bullet. *R1b D5-1, R1c M3.*
44. **Edge case: `last`-only** — the four-way flag fork; `before`+`last` restated as `UnwindowableConnection`. *R1b D5-4, R1a D5.*
45. **Edge case: `relay_max_results` agreement** — the request-policy ceiling. *R1a D7.*
46. **Edge case: `.distinct()`** — one of five reasons. *R1a D5.*
47. **Edge case: Backend floor** — the caveat scoped to the windowed strategy; `"auto"` and the lateral backend named. *R1a D8.*
48. **Test-plan intro, package-only rationale** — the fallback matrix restated as refusal arms plus per-key divergent-alias windows. *R1b D5-6, R1a D4.*
49. **Test plan Slice 1** — `test_nested_connection_planned_as_windowed_prefetch` restated to the contract it now pins, with the observability test named; the partition-helper and window-helper and hoist-parity entries repointed at their real class homes; `test_m2m_shared_child_partitions_per_parent` narrowed; the fallback-test list rewritten with the divergent-alias inversion. *R1a D3/D4, R1c M2/L2/L5, census renames.*
50. **Test plan Slice 2** — the two `..._falls_back_for_total_count_and_pageinfo` names replaced by the marker-row and `last: 0` pins that exist. *R1b D5-1, R1c M3.*
51. **Test plan Slice 3** — the cache test's claim narrowed from "two plans, two windows" to two keys, with the live test that earns the window half. *R1c Job-1 precision note.*
52. **Test plan Slice 5** — `test_nested_connection_first_zero_empty_page_live`'s "fast-path → per-parent fallback" parenthetical corrected to the marker row. *R1c M3.*
53. **Test plan Slice 6** — the cap sentence rewritten (the `ValueError` is wrapped as a `GraphQLError` before the wire; no products collection is over the cap today; the package-tree home for the capped-page pin is licensed by the intro); the promised nested-connection pin named as `test_products_categories_items_connection_fixed_query_count`, with its cardinality axis stated. *R1c L3, L4, L8, and the unnamed-pin note.*
54. **Doc updates: `docs/TREE.md` bullet** — four modules → every module Decision 11 enumerates. *R1a D2.*
55. **Doc updates: GLOSSARY bullet** — the fallback-matrix list corrected to the refusal arms. *R1c M1, R1a D5.*
56. **Doc updates: KANBAN bullet** — the pre-archive path removed, `WIP-ALPHA-033-0.0.9` → the completed move, `TODO-BETA-062-0.1.5` reconciliation stated as done. *R1c M5, L9.*
57. **Out of scope: per-alias windows** — split from the sidecar entry and recorded as shipped. *R1c M1.*
58. **Out of scope: keyset cursors** — split from the "Relay magic" entry and recorded as shipped. *R1b D5-7.*
59. **Out of scope: G1-G3, permissions, search** — card ids swept. *R1c M5.*
60. **DoD item 1** — archived path ×2 including the `--spec` argument; `OK: <N> terms` made concrete as `OK: 38 terms`. *R1c L9.*
61. **DoD item 2** — helpers relocated to `optimizer/selections.py` with both importers. *R1a D1.*
62. **DoD item 4** — conditional count; per-key divergent-alias windows; "the four fallback shapes" → the refusal arms. *R1a D3/D4, R1c M2.*
63. **DoD item 5** — ambiguous-empty fallback → marker rows plus the `last: 0` clause. *R1b D5-1, R1c M3.*
64. **DoD item 11** — `` `051` `` → `TODO-BETA-062-0.1.5`; `DONE-NNN-0.0.9` → `DONE-033-0.0.9`. *R1c M5.*
65. **DoD item 12** — dated ("No version bump **landed** in this card"), `pyproject.toml` clause replaced by the single-source rule, and the later cuts' movement stated as expected. *R1c M6.*

**Link definitions**

66. **Nine added** to the spec (`next` in the `docs/SPECS/` group; `join-taxonomy`, `keyset`, `lateral-fetch`, `nested-fetch`, `nested-planner`, `selections`, `single-parent-fetch`, `utils-connections` in the `django_strawberry_framework/` group, alphabetical within it); **three added and one pruned** in the companion (`changelog`, `docs-readme`, `glossary-configurationerror` added; `test-opt-walker` pruned when its only use went away). Zero undefined uses and zero unreferenced definitions remain in either file.

### Companion changes made (Worker 1 only)

- **Header `**Not corrected here.**` paragraph** → `**Reconciled after the move.**`, stating where each correction's record lives and carrying the census headline (zero genuine lost coverage across 76 named tests).
- **`### Changes this Decision underwent`, Decision 4** — six `**Post-ship:**` bullets: the conditional count, the relocated and generalised DISTINCT guard, the never-raising join classifier, the adopted per-alias-windows alternative, the request-policy ceiling, and the strategy seam.
- **Decision 5** — one build-time record (the wrapper's slice metadata was never implementable, with the reason) and seven `**Post-ship:**` bullets: marker rows, the four-way flag fork, the row-number-only probe, the single `resolve_connection`, the per-key probe order, keyset cursors, and the opened degradation list.
- **Decision 6** — four `**Post-ship:**` bullets, opening with the one that matters: the justification's own monotonicity claim is what an inversion falsifies, and the count went four → nine across four grammars.
- **Decision 8** — two `**Post-ship:**` bullets (the `ContextVar` fail-open closure, `force_unplanned`) and one build-time record (`declaring_type` is Decision 8's parameter, not Decision 5's).
- **Decision 9** — "Nothing later reopened it" retired; one build-time record (two of six symbols never existed) and one `**Post-ship:**` bullet recording that the rejected `optimizer/selections.py` is the shipped shape and that the rejection's entire argument, not one clause, is retired.
- **Decision 11** — three `**Post-ship:**` bullets: the eight modules with per-commit attribution, the six unnamed test files plus the `nested_planner.py` mirror exception, and the no-public-surface confirmation.
- **Decision 12** — one `**Post-ship:**` bullet explaining why the sentence is true of this card's slices and false as present-tense prose.
- **`## Risks and open questions`** — two items marked resolved with `**Post-ship:**` notes: the Strawberry floor (raised to `>=0.316.0`, with all three source-verified internals re-checked at the newer installed version) and window-function backend support (the `"auto"` strategy is the deferred capability probe in a different shape).
- **`## Non-Decision deliberation`** — the two rot bullets rewritten as resolved records with their re-derived counts and the lesson each carries; plus four new entries: the false "No new error surface" sentence with its four raising surfaces, the strategy seam's missing owner with the three resolution paths, and the three escalations with the cohorts' proposed paths.
- **Card-id sweep** — eight `051` occurrences → `TODO-BETA-062-0.1.5`; two `TODO-ALPHA-035-0.0.10` → `DONE-035-0.0.10`. Revision 1's `WIP-ALPHA-033-0.0.9` provenance mention was **not** touched, per [`KANBAN.md`][kanban]'s own rule that a sentence describing a past state is true only in the numbering of its own time.

### Dependencies on the concurrent R2 cohort

R2 writes only `.py` files; this slice wrote only spec files. Two spec sentences name tests whose bodies R2 is changing, and in both the spec now states the **contract**, not the assertion's current wording:

- `test_nested_connection_planned_as_windowed_prefetch` — the spec states that the plan carries the row-number annotation and slice filters and that the count is absent for an edges-only page, which is what the shipped body asserts and what R2's docstring repair will describe. If R2's repair changes the body's assertions rather than its prose, the spec sentence still holds.
- `test_m2m_shared_child_partitions_per_parent` — the spec now describes what the body pins (two partition-expression equalities) and names the live test that earns the shared-child half, so R2 restoring a shared-child scenario would make the spec sentence *narrower* than the test rather than wrong. Flagged for the integration pass.

One further R2-adjacent note: `django_strawberry_framework/optimizer/nested_fetch.py` carries `#"the historical spec-033 Decision 6 shape 4 guard"`. Decision 6's items were renumbered by this pass (the DISTINCT guard is now arm 6 of nine). The comment is explicitly framed as historical so it is not false, but it is the only ordinal citation into Decision 6's item list anywhere in the tree, and `nested_fetch.py` is **outside** R2's declared ownership. Routed to the integration pass, not fixed here.

### Deferred work

Doc surfaces this cycle's fence excludes ([`build-033-connection_optimizer-0_0_9.md`][build-033] `## Scope fence`), each with its evidence, **none fixed**:

- **`docs/TREE.md`** — its optimizer module entries cannot describe the seven post-ship modules Decision 11 now names. Script-rendered from module docstrings by `scripts/build_tree_md.py`, so the fix is a docstring-plus-regenerate change, not a doc edit. *R1a D2.*
- **`docs/GLOSSARY.md`, `## Strictness mode`** — its `0.0.9` paragraph still lists "divergent aliases" among the shapes that fall back per parent, which the idea-#2 inversion retired. **Note the correction to the dispatch's premise: `docs/GLOSSARY.md`'s `## Connection-aware optimizer planning` entry is *not* stale** — it already describes marker rows, the conditional count and n+1 probe, `last: 0`, the argument-conflict fallback, the strategy seam, and keyset `Meta.cursor_field`. It is the one standing doc that had absorbed the post-ship shape, and it was used as the voice reference for this pass. Only the Strictness-mode entry's one clause is stale. DB-generated: edit the glossary app's DB and re-render.
- **`KANBAN.md`** — `DONE-033-0.0.9`'s card body was not read against the corrected spec. Read-only this cycle (used to adjudicate card ids).
- **`docs/README.md`** — no correction needed and none made; R1b established it is *right* where the spec was wrong about keyset ordering. Recorded so a later reader does not "fix" it toward the retired Non-goal.
- **`CHANGELOG.md` / `TODAY.md` / `README.md`** — untouched; the `0.0.14` entry's "Pluggable nested-connection fetch-strategy seam" bullet is the only standing-doc record the seam has, and it is accurate.
- **`tests/test_connection.py`'s `TODO(spec-033 Slice 1-2)` anchor** — the only `TODO(spec-033` anchor in the tree; the work shipped, so `BUILD.md` `## Cross-slice integration pass` step 6 requires it re-classified (drop `TODO(`, keep the provenance). A `.py` edit; owner is R2 or the integration pass. *R1a Low, R1b.*
- **`nested_fetch.py`'s "Decision 6 shape 4" ordinal** — see the R2 dependency note above.

Test-side items that are not spec defects and were not fixed:

- **R1c L1** — `test_cache_key_variable_name_collection_memoized_for_nested_fallbacks` is order-dependent on the module-level `_doc_key_cache` LRU; it fails loudly rather than silently, and the fix is one `monkeypatch.setattr` line. `tests/optimizer/test_extension.py` is in R2's partition.
- **R1c L6** — `optimizer/extension.py` imports an underscore-private name from `nested_fetch`.
- **R1c L7 / L8** — four spec-named single-cardinality pins whose docstrings claim parent-count independence, and the products pin's children-per-parent axis. Each carries an absolute count derived from a real run, so each is distinguishing; the spec text was corrected where it over-claimed and no test change is owed.

**Three escalations — maintainer decisions, recorded in the companion under `## Non-Decision deliberation`, not resolved here.** In all three the shipped code implements the spec's own words, so each is a contract question rather than a defect ([`BUILD.md`][build-md] `### Contract-level findings are escalated as maintainer decisions before dispatch`):

1. **The `connection_to_attr` strictness probe answers "attribute present", not "the window was consumed"** (R1b M1, demonstrated with a three-row temp test). Three refusal shapes read as "served" and `"raise"` stays silent on a real per-parent access; no data is wrong, only the diagnostic is silent. Paths: thread the resolver's already-computed boolean and restate Decision 8's third condition (recommended); accept and record that a `_dst_`-namespace write can silence strictness; or narrow to the sidecar half only.
2. **`optimizer/plans.py::window_partition_for_prefetch` has zero production callers behind six tests** (R1a DRY-1), two of which pin an `OptimizerError` no production path can emit while `exceptions.py` documents that raise as live. Paths: delete the shim and move its pins onto `classify_relation_join`; give it the production caller it implies; or declare it a supported introspection helper in Decision 4.
3. **Ten of `optimizer/walker.py`'s seventeen back-compat aliases are dead, under a comment asserting live test readers** (R1a Medium). Deleting them is an existence question; correcting the false comment is not, and that half is in R2's scope.

**A fourth, larger question the cohorts raise together:** the nested-connection strategy seam has no owning spec. Three of this card's contracts were inverted by commits labelled "idea #N" belonging to no card, and the seam itself shipped in the `0.0.14` cut with a `CHANGELOG.md` entry and no spec. This cycle took the only option a worker may take — record each divergence under the owning Decision here — but the durable fix is either a card for the seam with the inverted contracts moved onto its spec, or a standing post-ship divergence section in a spec declared frozen. **Maintainer decision.**

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md
[kanban]: ../../KANBAN.md

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->
[artifact-md]: ARTIFACT.md
[bld-0]: bld-033-slice-0-rationale_extraction.md
[bld-1a]: bld-033-review-1a-plan_side_foundation.md
[bld-1b]: bld-033-review-1b-fast_path_strictness.md
[bld-1c]: bld-033-review-1c-cache_examples_census.md
[build-033]: build-033-connection_optimizer-0_0_9.md
[build-md]: BUILD.md
[worker-1]: worker-1.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
