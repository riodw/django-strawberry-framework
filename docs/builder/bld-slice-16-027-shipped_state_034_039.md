# Build: Catalog cohort K — five shipped specs describing themselves as unshipped, in five different spellings, plus the last live `WIP-ALPHA-033` id in the package

Spec reference: [`docs/SPECS/spec-027-filters-0_0_8.md`][spec-027] owns the catalog this cohort discharges, but no corrected surface points at spec-027. The dispatched defects belong to five other cards — [`spec-034-permissions-0_0_10.md`][spec-034], [`spec-035-optimizer_hardening-0_0_10.md`][spec-035], [`spec-036-mutations-0_0_11.md`][spec-036], [`spec-038-form_mutations-0_0_12.md`][spec-038], [`spec-039-serializer_mutations-0_0_13.md`][spec-039] — plus one docstring site in [`types/finalizer.py::_synthesize_relation_connections`][types-finalizer]. The dispatch is [`build-027-filters-0_0_8.md`][plan] `### Four further in-fence spec defects, verified by Worker 0, not yet dispatched` as extended by cohort H's `### Notes for Worker 1 / Worker 0 — findings left in place` items 2 and 3 ([`bld-slice-13-027-shipped_card_spec_staleness.md`][slice-13]).
Status: final-accepted

## Plan (Worker 1)

### Planning lives in the build plan; this cohort's fence came from the dispatch

Cohort H measured the population and left it in place: its item 2 names `spec-034`, `spec-035`, `spec-036` as "Planned for" openers over `DONE-` ids, `spec-038` as `TODO-ALPHA-038-0.0.12` in a "Planned for" opener, and `spec-039` as "Implemented on main; release deferred". Its item 3 names the two live `WIP-ALPHA-033-0.0.9` `.py` sites. This cohort discharges both, minus the `spec-029` / `030` / `031` / `032` half of item 2 (cohort J) and the `connection.py` half of item 3 (cohort I).

**Ownership partition (declared, disjoint):** `docs/SPECS/spec-034-permissions-0_0_10.md`, `spec-035-optimizer_hardening-0_0_10.md`, `spec-036-mutations-0_0_11.md`, `spec-038-form_mutations-0_0_12.md`, `spec-039-serializer_mutations-0_0_13.md`, `django_strawberry_framework/types/finalizer.py` (one docstring site), plus this artifact. All seven were written.

Cohort I is writing `.py` files concurrently (`connection.py`, `tests/test_routers.py`, `tests/test_permissions.py`, `tests/optimizer/test_walker.py`); cohort J holds `spec-029` – `032`; a separate session holds `spec-028` and its companion. No file outside the partition was read for edit, written, or reverted (`AGENTS.md` rule 34). Two of this cohort's files were already `M` at task start and the hunks are separable (below).

### Dispatched findings checklist

Authored by Worker 1 (this cohort has no separate planning spawn). Each tick is re-derivable from the sections below.

- [x] Task 1: re-derive every figure in Worker 0's table rather than transcribing it — `Status:` opener and `WIP-ALPHA` occurrence count per spec
- [x] Task 1: confirm each card's real state and current id against `KANBAN.md`, per card, not by pattern
- [x] Task 1: verify cohort H's archive convention by measurement (prose-opener dominance, the realigned form, the checklist rule) rather than trusting it
- [x] Task 1: collapse the five divergent shipped-state spellings onto the one convention, opener and `Status:` both
- [x] Task 1: retire every `WIP-ALPHA` id per id, distinguishing live claims from historical records and stating the judgement
- [x] Task 1: delete rather than restate every claim shipping falsified, with its measurement
- [x] Task 1: fix the whole blast radius, then show the retired-vocabulary sweep empty per spec
- [x] Task 1: verify the `spec-035` `### Decision` heading count against cohort C's disproof
- [x] Task 1: check whether a rationale companion exists for each spec; do not create one
- [x] Task 2: grep `docs/SPECS/` for the exact string before editing it, and report a quotation dependency rather than editing blindly
- [x] Task 2: prove zero executable-token change **element-wise**, not by count
- [x] Task 2: scoped `ruff format` / `ruff check --fix`, `check_trailing_commas.py --check`, focused `pytest tests/types tests/filters --no-cov`, no `--cov*` flag anywhere
- [x] Postcondition measured, not assumed: 0 wrapped `#"` citations across all six edited files, with a control proving the instrument still finds known originals

---

## Build report (Worker 1, acting as the cohort's only pass)

### Files touched

- `docs/SPECS/spec-034-permissions-0_0_10.md` — opener, `Status:`, one `## Current state` bullet, `### Decision 13`, one `## Definition of done` item; three `WIP-ALPHA-033-0.0.9` and one `TODO-ALPHA-035-0.0.10` retired.
- `docs/SPECS/spec-035-optimizer_hardening-0_0_10.md` — opener, `Status:`, one `## Current state` bullet, `### Decision 1`, `### Decision 9`, one `## Definition of done` item; one `WIP-ALPHA-035-0.0.10` retired.
- `docs/SPECS/spec-036-mutations-0_0_11.md` — opener and `Status:` only; the rest of the spec carried no falsified claim (measured, below).
- `docs/SPECS/spec-038-form_mutations-0_0_12.md` — opener, `Status:`, two "`039` is not yet specced" claims.
- `docs/SPECS/spec-039-serializer_mutations-0_0_13.md` — opener, `Status:`, and the Revision-10 self-quotation of its own former header; two `WIP-ALPHA-040-0.0.13` sites resolved as a consequence.
- `django_strawberry_framework/types/finalizer.py` — one docstring card id.

### Tests added or updated

None. The diff adds no executable statement and changes no contract a test can pin; the `.py` edit is proved token-identical below.

---

## Task 1 — five shipped specs describing themselves as unshipped

### Worker 0's table, re-derived

Occurrence counts are `grep -oF WIP-ALPHA <spec> | wc -l`, so the number is occurrences and not matching lines.

| Spec | `Status:` line opened | `WIP-ALPHA` occ. (re-derived) | Worker 0's figure |
|---|---|---|---|
| `spec-034` | `Status: build complete — all five slices shipped …` | 4 | 4 ✓ |
| `spec-035` | ``Status: **COMPLETE** (card `DONE-035-0.0.10`) …`` | 3 | 3 ✓ |
| `spec-036` | ``Status: **COMPLETE** (card `DONE-036-0.0.11`; …)`` | 0 | 0 ✓ |
| `spec-038` | ``Status: **IN PROGRESS** — authored for [`TODO-ALPHA-038-0.0.12`][kanban] …`` | 0 | 0 ✓ |
| `spec-039` | `Status: **IMPLEMENTED ON MAIN** — all five slices …` | 2 | 2 ✓ |

**Five spellings of one state, and not one of them is the archive's.** `build complete` (034) and `**COMPLETE**` (035, 036) assert completion without asserting release; `**IMPLEMENTED ON MAIN**` (039) asserts the opposite of release outright ("release deferred"); `**IN PROGRESS**` (038) is flatly false on a Done card. The openers diverge a sixth way: 034 / 035 / 036 read "Planned for", 038 reads "Planned for" over a `TODO-ALPHA-` id, and 039 reads "Implemented on main; release deferred to the joint `0.0.13` cut".

### Card state and current id, verified per card

`grep -oE '(DONE|WIP-ALPHA|TODO-ALPHA|BLOCKED-ALPHA|TODO-BETA)-<NNN>-[0-9.]+' KANBAN.md | sort | uniq -c`:

| Card | Board ids present | Other spelling on the board | Release heading in `CHANGELOG.md` |
|---|---|---|---|
| 034 | `DONE-034-0.0.10` ×21 | none | `## [0.0.10] - 2026-06-16` |
| 035 | `DONE-035-0.0.10` ×2 | none | `## [0.0.10] - 2026-06-16` |
| 036 | `DONE-036-0.0.11` ×32 (+2 sentence-final) | none | `## [0.0.11] - 2026-06-19` |
| 038 | `DONE-038-0.0.12` ×9 | none | `## [0.0.12] - 2026-06-23` |
| 039 | `DONE-039-0.0.13` ×9 | none | `## [0.0.13] - 2026-07-06` |
| 033 (cited by 034) | `DONE-033-0.0.9` ×15 | none | — |
| 040 (cited by 039) | `DONE-040-0.0.13` ×7 (+2 sentence-final) | none | — |

All five releases shipped and `pyproject.toml` `[project].version` reads `0.0.14`, so **every** "the on-disk version reads / stays at `0.0.X`" and "the only pending release act" claim below is falsified by measurement rather than by inference. The `## In progress` KANBAN column renders "No cards in progress."

### The convention, verified rather than trusted

Cohort H's three measurements re-derived independently over the 56 files in `docs/SPECS/`:

- **The prose opener is dominant.** 17 of 56 carry a `Target release:` header line; **39 do not** and open with prose on line 3. All 17 fall in the `007`–`027` range and none above `027`, so importing that header into an `034`+ record would be adopting a superseded era's shape. All five of this cohort's specs are prose-opener records, so every opener was **corrected in place, never removed**.
- **The realigned form.** The era's already-corrected shipped records are `spec-028` ("Shipped in `0.0.8` (card [`DONE-028-0.0.8`][kanban], moved from `WIP-ALPHA-028-0.0.8` at Slice 5). **This spec is the final implementation record, not an open build plan.**"), and cohort H's `spec-033` / `spec-037`. `Shipped in` is the verb in all three; `Status: **SHIPPED (\`0.0.X\`)**` is the `Status:` form in cohort H's two, which are the most recent realignment and therefore the form matched here. `spec-028`'s own `Status:` reads the lowercase `shipped in \`0.0.8\`.`; the divergence is noted and cohort H's spelling was preferred as the later one.
- **The checklist rule.** [`spec-045`][spec-045]'s `Status:` states it — the boxes stay unticked because the `Status:` line is the completion source of truth — and `spec-047` / `048` / `049` repeat the sentence. **No box was ticked or unticked in any file this cohort touched**, verified by count: `034` 21 unticked / 0 ticked, `035` 0 / 10, `036` 19 / 0, `038` 19 / 0, `039` 28 / 0, before and after.

**One convention delta this cohort had to derive itself.** `spec-035` is the one spec in the set whose checklist boxes **are** ticked (10 of 10), because its own opener declares "The [Slice checklist](#slice-checklist) below ticks Slices 1, 2, and 4 (all shipped) and marks Slice 3 (G3) **deferred**". Pasting the stays-unticked clause into its `Status:` would have written a false sentence in the act of fixing a false sentence. `spec-028` supplies the correct clause for a ticked record — "the [Slice checklist](#slice-checklist) is ticked to reflect the executed plan" — so `035` carries that instead. Archive-sourced, not invented.

### Per-spec before / after

#### `spec-034-permissions-0_0_10.md`

**Opener.** Before: "Planned for `0.0.10` (card [`DONE-034-0.0.10`][kanban]). **This spec is an open build plan, not a shipped record.** The card was directed to spec by the maintainer while [`WIP-ALPHA-033-0.0.9`][kanban] (connection-aware optimizer planning) remains in progress; the two cards are independent …". After: "Shipped in `0.0.10` (card [`DONE-034-0.0.10`][kanban]). **This spec is the final implementation record, not an open build plan.** The card was directed to spec by the maintainer alongside [`DONE-033-0.0.9`][kanban] (connection-aware optimizer planning); the two cards are independent …". This is the one opener in the set carrying the "open build plan, not a shipped record" sentence, so it is the one that takes `spec-028`'s verbatim replacement clause.

**Opener, checklist clause.** Before: "stays unticked as the contract record". After: "stays unticked because the `Status:` line is the completion source of truth (the shipped-spec convention)".

**Opener, sibling card + version tail.** `TODO-ALPHA-035-0.0.10` → `DONE-035-0.0.10`. The parenthetical lost its falsified half: before "(the on-disk version reads `0.0.9` as of this writing — the `0.0.9` cut has landed; the `0.0.10` bump itself remains the joint cut's job)", after "(the on-disk version reads `0.0.9` as of this writing — the `0.0.9` cut has landed)". The surviving clause is explicitly tense-marked and the sentence before it already says the joint cut owns the bump, so the deleted tail was falsified **and** redundant.

**`Status:`.** Before: "Status: build complete — all five slices shipped (…); pending the cross-slice integration pass and the joint-`0.0.10` final gate. Five slices: …". After: "Status: **SHIPPED (`0.0.10`) — all five slices (…) final-accepted.** Card [`DONE-034-0.0.10`][kanban], released under the [`CHANGELOG.md`][changelog] `## [0.0.10]` heading. The `0.0.10` version bump and the `CHANGELOG.md` release-heading promotion belong to the joint cut, not to this card, per [Decision 13](#decision-13--version-bumps-are-owned-by-the-joint-0010-cut). The [Slice checklist](#slice-checklist) below stays unticked because the `Status:` line is the completion source of truth (the shipped-spec convention). Five slices: …". The five-slice enumeration that follows was not touched.

**Blast radius, three further sites.**

| Site | Before | After |
|---|---|---|
| `## Current state`, hard-dependency bullet | "[`WIP-ALPHA-033-0.0.9`][kanban] remains open but is independent — the cascade composes with *whatever* the connection pipeline does" | "[`DONE-033-0.0.9`][kanban] is independent — the cascade composes with *whatever* the connection pipeline does" |
| `### Decision 13` | "the version bump belongs to the **joint cut** that releases both cards — and lands only after the still-pending `0.0.9` cut (gated on [`WIP-ALPHA-033-0.0.9`][kanban]) is taken." | "the version bump belongs to the **joint cut** that releases both cards." |
| `## Definition of done`, item 13 | "(the joint `0.0.10` cut owns the bump, after the pending `0.0.9` cut)." | "(the joint `0.0.10` cut owns the bump)." |

#### `spec-035-optimizer_hardening-0_0_10.md`

**Opener.** Verb only: "Planned for `0.0.10`" → "Shipped in `0.0.10`". Its next sentence — "**This card ships two of the three audited guards; the third is deferred.**" — is a true present-tense contract statement, not the "open build plan" clause, so no replacement clause applies (cohort H's `spec-037` treatment). Two further opener edits: "(the permissions subsystem, now build-complete)" → "(the permissions subsystem, shipped)", and the version tail lost "; the only pending release act is the joint `0.0.10` cut, which owns the bump".

**`Status:`.** Before: "Status: **COMPLETE** (card `DONE-035-0.0.10`) — G1 shipped (commit `d1dea2fd`), G2 shipped (this card's build), Slice 4 doc wrap landed; G3 deferred." After: "Status: **SHIPPED (`0.0.10`)** — card [`DONE-035-0.0.10`][kanban], released under the [`CHANGELOG.md`][changelog] `## [0.0.10]` heading; G1 shipped (commit `d1dea2fd`), G2 shipped in this card's build, Slice 4 doc wrap landed; G3 deferred. The [Slice checklist](#slice-checklist) is ticked to reflect the executed plan." The bare `` `DONE-035-0.0.10` `` code span became the `[kanban]`-linked form the archive uses. The commit sha is pre-existing content naming where G1 landed, not provenance this cohort added.

**Blast radius, three further sites.**

| Site | Before | After |
|---|---|---|
| `## Current state` | "- **The joint-cut sibling is build-complete.** … The `0.0.10` joint cut releases both cards and owns the version bump; the on-disk version reads `0.0.9`." | "- **The joint-cut sibling has shipped.** … The `0.0.10` joint cut releases both cards and owns the version bump." |
| `### Decision 1` (filename derivation) | "The card is `WIP-ALPHA-035-0.0.10`, so `<NNN>` is `035` and `<0_0_X>` is `0_0_10`." | "The card is `DONE-035-0.0.10`, so …" (derivation unchanged and still correct) |
| `### Decision 9` | "(the permissions subsystem, build-complete); … (the `0.0.9` cut has already landed — on-disk `__version__ == \"0.0.9\"` — so the joint `0.0.10` cut is the only pending release act)." | "(the permissions subsystem); … that releases both cards." |
| `## Definition of done`, item 11 | "(the joint `0.0.10` cut owns the bump; the `0.0.9` cut has already landed, so that joint cut is the only pending release act)." | "(the joint `0.0.10` cut owns the bump)." |

**The `### Decision` heading count, verified.** `grep -c '^### Decision ' docs/SPECS/spec-035-optimizer_hardening-0_0_10.md` returns **9**, headings `Decision 1` through `Decision 9` with no gaps. Cohort C's disproof is confirmed: any citation naming a `spec-035` Decision above 9 is false. **This cohort met none** — the only `spec-035` Decision references inside its own writable set are `Decision 9` (twice, in the version-boundary sites above) and `Decision 3` / `4` / `5` / `6` / `7` in the untouched opener, all in range.

#### `spec-036-mutations-0_0_11.md`

**Opener.** "Planned for `0.0.11` (card [`DONE-036-0.0.11`][kanban]). This card opens" → "Shipped in `0.0.11` (card [`DONE-036-0.0.11`][kanban]). This card opens". Nothing else in the paragraph changed; it carries no "open build plan" clause and no falsified version claim.

**`Status:`.** Before: "Status: **COMPLETE** (card `DONE-036-0.0.11`; all five slices shipped — build complete). Authored from the card body via the [`docs/SPECS/NEXT.md`][next] flow." After: "Status: **SHIPPED (`0.0.11`)** — card [`DONE-036-0.0.11`][kanban], released under the [`CHANGELOG.md`][changelog] `## [0.0.11]` heading; all five slices final-accepted. Authored from the card body via the [`docs/SPECS/NEXT.md`][next] flow. The [Slice checklist](#slice-checklist) below stays unticked because the `Status:` line is the completion source of truth (the shipped-spec convention)."

**Blast radius: empty, and that is a measurement rather than an absence of effort.** `spec-036` is the cleanest record in the set. Its `## Current state` opens "A true description of the repo as this spec is authored", every version sentence in `### Decision 13` and DoD item 8 is a card-scope statement ("no slice in this card edits …", "the joint `0.0.11` cut … owns the bump") that shipping does not falsify, and the negative-vocabulary sweep over the whole file returns three hits, all unrelated (a `## Doc updates` instruction, an input-field default rule, a predecessor note).

#### `spec-038-form_mutations-0_0_12.md`

**Opener.** "Planned for `0.0.12` (card [`TODO-ALPHA-038-0.0.12`][kanban]). This card adds the" → "Shipped in `0.0.12` (card [`DONE-038-0.0.12`][kanban]). This card adds the". This spec is the outright false one: a `TODO-ALPHA-` id **and** a "Planned for" verb **and** an `IN PROGRESS` `Status:` on a card the board carries as `DONE-038-0.0.12` under a released `## [0.0.12]` heading.

**`Status:`.** Before (five hard-wrapped lines): "Status: **IN PROGRESS** — authored for [`TODO-ALPHA-038-0.0.12`][kanban] via the [`docs/SPECS/NEXT.md`][next] flow; Slices 1–4 built and accepted (…), only Slice 5 remains. Slice 5 flips this line to shipped at the `0.0.12` cut." After: "Status: **SHIPPED (`0.0.12`)** — card [`DONE-038-0.0.12`][kanban], released under the [`CHANGELOG.md`][changelog] `## [0.0.12]` heading; authored via the [`docs/SPECS/NEXT.md`][next] flow, **all five slices final-accepted** (the form converter + form-derived inputs; the two bases + `Meta` validation + the phase-2.5 bind; the resolver pipeline + `DjangoMutationField` exposure; the products live form surface; docs + the `0.0.12` version cut + card wrap). The [Slice checklist](#slice-checklist) below stays unticked because the `Status:` line is the completion source of truth (the shipped-spec convention)." Three things went rather than being restated: the stale card id, "only Slice 5 remains", and "Slice 5 flips this line to shipped at the `0.0.12` cut" — a self-referential instruction about this very line, which `0.0.12` shipping discharged. Slice 5's own subject was folded into the five-slice list so nothing was lost.

**Blast radius, two sites, both the same falsified claim.** `spec-038` twice justifies the `036`-surface generalization by saying the serializer flavor's reuse is only an intent because "`039` is not yet specced". `spec-039` exists, shipped as `DONE-039-0.0.13` under a released `## [0.0.13]`.

| Site | Before | After |
|---|---|---|
| `## Cross-flavor reuse` preamble | "and the future `0.0.13` [`SerializerMutation`][glossary-serializermutation] flavor is designed to reuse every one of them — though `039` is not yet specced, so that reuse is a forward intent, not a commitment this card can bind):" | "and the `0.0.13` [`SerializerMutation`][glossary-serializermutation] flavor is designed to reuse every one of them):" |
| diff-budget paragraph | "flavor is designed to reuse (a forward intent — `039` is not yet specced)." | "flavor is designed to reuse." |

The falsified premise was deleted rather than inverted: "is designed to reuse" is a true statement about why the seams have the shape they have, and upgrading it to "does reuse" would be a claim about `039`'s implementation this cohort has not measured per-axis.

`spec-038`'s `## Current state` bullets ("**No `forms/` module exists.**", "**The version line reads `0.0.11`.**") sit under "A true description of the repo as this spec is authored" and were left: an explicitly tense-marked authoring snapshot is the class cohort H preserved in `spec-033`.

#### `spec-039-serializer_mutations-0_0_13.md`

**Opener.** Before (two hard-wrapped lines): "Implemented on main; release deferred to the joint `0.0.13` cut (card [`DONE-039-0.0.13`][kanban]). This card adds the". After: "Shipped in `0.0.13` (card [`DONE-039-0.0.13`][kanban]). This card adds the". A near-miss spelling: it names the card correctly and still asserts the release has not happened.

**`Status:`.** Before: "Status: **IMPLEMENTED ON MAIN** — all five slices (Slice 0 + Slices 1-4) are final-accepted and on main; the implemented-on-main docs + the card wrap landed in Slice 4 ([`DONE-039-0.0.13`][kanban]). **Release deferred to the joint `0.0.13` cut** shared with [`WIP-ALPHA-040-0.0.13`][kanban], which still owns the version bump (`0.0.12` → `0.0.13`) and the public release-status flip (…) — **F8** / [Decision 14](…). The card was authored for `TODO-ALPHA-039-0.0.13` via the [`docs/SPECS/NEXT.md`][next] flow." After: "Status: **SHIPPED (`0.0.13`)** — card [`DONE-039-0.0.13`][kanban], released under the [`CHANGELOG.md`][changelog] `## [0.0.13]` heading; all five slices (Slice 0 + Slices 1-4) final-accepted, the docs + card wrap landed in Slice 4. The `0.0.13` version bump and the public release-status flip (the GLOSSARY `shipped (0.0.13)` status, the `README.md` / [`docs/README.md`][docs-readme] \"Shipped today\" move, the `CHANGELOG.md` bullets) belong to the joint cut shared with [`DONE-040-0.0.13`][kanban], not to this card — **F8** / [Decision 14](…). The [Slice checklist](#slice-checklist) below stays unticked because the `Status:` line is the completion source of truth (the shipped-spec convention). The card was authored via the [`docs/SPECS/NEXT.md`][next] flow."

The version-bump / release-flip sentence was **kept and re-tensed rather than deleted**: which card owned the bump is a live scope contract (`### Decision 14`), and only "Release deferred" / "still owns" were the falsehoods. The stale `TODO-ALPHA-039-0.0.13` went with the sentence that carried it, exactly as cohort H handled `spec-037`'s `Status:`.

**One blast-radius site: the Revision-10 entry quoting its own former header.** The entry read "Reconciled the stale header to reality: the body line 3 \"Planned for `0.0.13`\" and the Status block \"**IN PROGRESS** … no slice built yet\" now read **IMPLEMENTED ON MAIN; release deferred to the joint `0.0.13` cut** shared with [`WIP-ALPHA-040-0.0.13`][kanban], which still owns the version bump and the public release-status flip (…)." Deleted, keeping the rest of the entry (five slices final-accepted, which docs and card wrap landed in Slice 4, no version bump, joint-cut deferrals confirmed absent from the diff).

This one is **not** the historical-record class, on three independent grounds: its verb is "now read", a present-tense assertion about the header this cohort just rewrote, so leaving it would have left the spec asserting `SHIPPED` in one place and `IMPLEMENTED ON MAIN` in another — the half-reconciled state that is worse than no fix; it quotes the superseded text rather than recording a fact about the build; and it cites "body line 3", a raw `line NN` reference `AGENTS.md` rule 27 permits only in per-cycle artifacts. Deleting it is also what resolved the file's last two `WIP-ALPHA` occurrences.

`spec-039`'s two `## In progress`-column sentences (`## Current state` and `## Risks and open questions`) were left: both are spelled "as this spec is authored", and the column was in fact empty then — `KANBAN.md` renders "No cards in progress." now as well, so neither is even counterfactual.

### The `WIP-ALPHA` retirement table

| Spec | Site | Id | Verified board spelling | Disposition |
|---|---|---|---|---|
| 034 | opener | `WIP-ALPHA-033-0.0.9` | `DONE-033-0.0.9` (×15) | **retired** — live claim ("remains in progress") |
| 034 | `## Current state` | `WIP-ALPHA-033-0.0.9` | `DONE-033-0.0.9` | **retired** — live claim ("remains open") |
| 034 | `### Decision 13` | `WIP-ALPHA-033-0.0.9` | `DONE-033-0.0.9` | **retired** with the falsified clause that carried it |
| 034 | `## Revision history`, Revision 8 | `WIP-ALPHA-035-0.0.10` | `DONE-035-0.0.10` (×2) | **left — historical.** A revision-log record of a review pass that reverted the package version to `0.0.9`; its parenthetical ("the joint cut is still pending, `WIP-ALPHA-035-0.0.10` open") was the reason that revision acted as it did, and is a real record |
| 035 | `## Revision history`, Revision 1 | `WIP-ALPHA-035-0.0.10` | `DONE-035-0.0.10` | **left — historical.** "initial draft authored from the … card body"; that was the card's id when the draft was authored |
| 035 | `### Decision 1` | `WIP-ALPHA-035-0.0.10` | `DONE-035-0.0.10` | **retired** — a bare present-tense claim about the card's identity, the same site class cohort H corrected in `spec-033`'s Decision 11 |
| 035 | `## Doc updates`, Slice 4 | `WIP-ALPHA-035-0.0.10` | `DONE-035-0.0.10` | **left — imperative slice step.** "move [`WIP-ALPHA-035-0.0.10`][kanban] to Done with the next `DONE-NNN-0.0.10` id" — the subject is legitimately the pre-move id; cohort H left the identical site in `spec-033` |
| 039 | `Status:` | `WIP-ALPHA-040-0.0.13` | `DONE-040-0.0.13` (×7) | **retired** — live claim ("still owns the version bump") |
| 039 | `## Revision history`, Revision 10 | `WIP-ALPHA-040-0.0.13` | `DONE-040-0.0.13` | **removed with the falsified sentence**, per the determination above; not a retirement in place |

Occurrences: **9 → 3** (034 ×1, 035 ×2, all four judged non-edits above; the fifth non-edit candidate, 039's Revision 10, went with its sentence). No id was pattern-substituted; each was checked against the board separately, which is what surfaced that `WIP-ALPHA-035-0.0.10` and `TODO-ALPHA-035-0.0.10` are two stale spellings of the same card **living in the same spec** (034), one in a revision log and one in the opener, only the second of which is a live claim.

### Every claim deleted, with its measurement

| # | Spec / site | Deleted claim | Measurement that falsifies it |
|---|---|---|---|
| 1 | 034 opener | "**This spec is an open build plan, not a shipped record.**" | `DONE-034-0.0.10` ×21 on the board; `## [0.0.10] - 2026-06-16` in `CHANGELOG.md` |
| 2 | 034 opener | "[`WIP-ALPHA-033-0.0.9`][kanban] … remains in progress" | `DONE-033-0.0.9` ×15; no `WIP-` spelling on the board |
| 3 | 034 opener | "the `0.0.10` bump itself remains the joint cut's job" | `pyproject.toml` `[project].version = "0.0.14"`; `__version__ = "0.0.14"` |
| 4 | 034 `Status:` | "pending the cross-slice integration pass and the joint-`0.0.10` final gate" | `## [0.0.10]` released; the card is Done |
| 5 | 034 `## Current state` | "remains open but is independent" | as #2 |
| 6 | 034 `### Decision 13` | "lands only after the still-pending `0.0.9` cut (gated on …) is taken" | `## [0.0.10]`, `## [0.0.11]`, `## [0.0.12]`, `## [0.0.13]`, `## [0.0.14]` all present |
| 7 | 034 DoD item 13 | "after the pending `0.0.9` cut" | as #6 |
| 8 | 035 opener | "the only pending release act is the joint `0.0.10` cut, which owns the bump" | as #3 |
| 9 | 035 opener / Decision 9 | "now build-complete" / "build-complete" describing card 034 | `DONE-034-0.0.10` ×21 |
| 10 | 035 `## Current state` | "the on-disk version reads `0.0.9`" | as #3 |
| 11 | 035 `### Decision 9` | "(the `0.0.9` cut has already landed — on-disk `__version__ == \"0.0.9\"` — so the joint `0.0.10` cut is the only pending release act)" | as #3 |
| 12 | 035 DoD item 11 | "the `0.0.9` cut has already landed, so that joint cut is the only pending release act" | as #3 |
| 13 | 038 `Status:` | "only Slice 5 remains" | five slices; `DONE-038-0.0.12` ×9; `## [0.0.12] - 2026-06-23` |
| 14 | 038 `Status:` | "Slice 5 flips this line to shipped at the `0.0.12` cut" | `## [0.0.12]` released |
| 15 | 038 ×2 | "`039` is not yet specced" | `docs/SPECS/spec-039-serializer_mutations-0_0_13.md` exists; `DONE-039-0.0.13` ×9; `## [0.0.13] - 2026-07-06` |
| 16 | 039 opener | "release deferred to the joint `0.0.13` cut" | `## [0.0.13] - 2026-07-06` |
| 17 | 039 `Status:` | "**Release deferred** … which still owns the version bump" | as #16; `DONE-040-0.0.13` ×7 |
| 18 | 039 Revision 10 | the self-quotation of the former opener and `Status:` | the header it describes no longer exists |

No `bld-*` build-artifact reference and no `## In progress`-column *claim* (as opposed to a tense-marked snapshot) existed in this cohort's five files: `grep -nE 'bld-'` returns 0 in all five, before and after.

### Blast-radius sweep, shown empty per spec

`grep -nE "open build plan, not a shipped record|\*\*IN PROGRESS\*\*|\*\*IMPLEMENTED ON MAIN\*\*|IMPLEMENTED ON MAIN|\*\*COMPLETE\*\* \(card|Status: build complete|not yet specced|still owns the version bump|remains open but|only pending release act|pending release act|remains the joint cut's job|after the pending \`0\.0\.9\` cut|still-pending|only Slice 5 remains|pending the cross-slice|now build-complete|is build-complete|release deferred"` over each file:

| Spec | Hits before | Hits after |
|---|---|---|
| `spec-034` | 5 | **0** |
| `spec-035` | 6 | **0** |
| `spec-036` | 1 | **0** |
| `spec-038` | 4 | **0** |
| `spec-039` | 5 | **0** |

Plus per-spec `grep -noE 'WIP-ALPHA-[0-9]+-[0-9.]+'`: 034 → 1 row (Revision 8), 035 → 2 rows (Revision 1, Slice 4 board move), 036 → 0, 038 → 0, 039 → **0**. Each survivor is a row in the retirement table with its recorded reason.

### The rationale companions do not exist, and none was created

`ls docs/SPECS/appx/` carries `spec-034-…-terms.csv`, `spec-035-…-terms.csv`, `spec-036-…-terms.csv`, `spec-038-…-terms.csv` and `spec-039-…-terms.csv` and **no `-rationale.md` for any of the five**. All five therefore keep their deliberative layer inline — an inline `## Revision history` chronology plus a `Justification:` / `Alternatives considered (and rejected):` pair under each Decision — the same condition cohort H reported for `spec-040`. Creating a companion is a structural decision outside this cohort's fence, so the corrections are recorded here. The direct consequence for this pass: `spec-039`'s Revision-10 falsehood existed **because** the spec narrates its own history in-file, and the four historical non-edits in the retirement table are all revision-log rows that would not be in the spec at all had the move been done.

### Link definitions, anchors, and checklist boxes

No definition added and none removed. `[kanban]`, `[changelog]`, `[next]`, `[docs-readme]` and the `#slice-checklist` / `#decision-13-…` / `#decision-14-…` anchors were each confirmed present in the target file before use. Verified mechanically rather than by eye, by running one probe over `git show HEAD:<path>` copies and over the working tree and differencing the failure sets:

| Spec | New used-but-undefined refs | New orphan definitions | New unresolved in-page anchors |
|---|---|---|---|
| `spec-034` | none | none | none |
| `spec-035` | none | none | none |
| `spec-036` | none | none | none |
| `spec-038` | none | none | none |
| `spec-039` | none | none | none |

(The probe reports a small pre-existing baseline in four files — one orphan `[backlog]` definition in `036` and one anchor per file whose heading contains `()` — identical at `HEAD` and in the tree, so unchanged by this cohort. Differencing against `HEAD` rather than reading absolute numbers is what makes that distinguishable.)

---

## Task 2 — `types/finalizer.py`'s docstring card id

### The ordering constraint, checked first

Cohort H's item 3 warned that `spec-033` quotes `connection.py`'s sibling comment verbatim, so a `.py` string can have a spec-side dependency. Checked before editing:

- `grep -rn "connection pipeline is" docs/SPECS/` returns **nothing**. No spec quotes this string.
- `grep -rn "WIP-ALPHA-033" docs/SPECS/` returned spec-side occurrences in `spec-030`, `spec-031`, `spec-032`, `spec-033` and three `appx/*-terms.csv` rows. None of them is a quotation of this docstring; the nearest, `spec-032` `#### Edge cases`, states the same fact in its own words ("Wiring strictness into the connection pipeline is `033`'s scope") and names the card as bare `033`. **No dependency, so the edit is unblocked.** (The `029`–`032` half of that population shrank while this pass ran; see `### Notes for Worker 1 / Worker 0` finding 4.)
- The seam cohort H flagged is already discharged by another cohort: `django_strawberry_framework/connection.py` now reads ``reachable as the cooperation seam ``DONE-033-0.0.9``'s``, and `spec-033` carries no `WIP-ALPHA-033` id at the site that quoted it. Reported rather than acted on — `connection.py` is not in this cohort's partition.

### Before / after

Board state re-verified: `DONE-033-0.0.9` ×15 in `KANBAN.md`, no `WIP-`/`TODO-` spelling for card 033.

Before (`types/finalizer.py::_synthesize_relation_connections` docstring):

```
    connection pipeline is ``WIP-ALPHA-033-0.0.9``'s scope.
```

After:

```
    connection pipeline is ``DONE-033-0.0.9``'s scope.
```

`grep -rn "WIP-ALPHA-033" --include='*.py' .` (excluding `.venv`) now returns **0** — the class is closed across the whole Python surface, not only this file.

### Token-identity proof, element-wise

Instrument: `tokenize.generate_tokens`, dropping `COMMENT` / `NL` / `ENCODING` and every **statement-position** `STRING` (a `STRING` whose preceding kept token is `NEWLINE` / `INDENT` / `DEDENT` / `ENCODING` or start-of-file — i.e. a docstring or bare string statement). The remaining `(type, string)` pairs are compared **pair by pair with `zip(..., strict=True)`**, and the count comparison is only a precondition on the element-wise walk, never the proof itself.

| Measure | Result |
|---|---|
| filtered executable tokens, before | 6436 |
| filtered executable tokens, after | 6436 |
| **element-wise mismatches** | **0** |
| pre-edit snapshot | written outside the repository, under this session's private `cohortK-027/` scratchpad |
| file bytes | 99766 → 99761 (−5, the length delta of `WIP-ALPHA` → `DONE`) |

Count-only checking is exactly what would have passed the two prior cohorts' equal-count mutations, which is why the mismatch list rather than the length is the recorded evidence.

### Wrapped-citation postcondition

Instrument walks **every** `#"` on each line with `str.find` in a loop, classifying test-closure first and only then the predecessor character (non-whitespace other than `(` / `[` marks a `"#"` / `###"` string-literal false positive). Run over all six edited files:

| File | `#"` citation occurrences | Wrapped |
|---|---|---|
| `spec-034` | 9 | **0** |
| `spec-035` | 3 | **0** |
| `spec-036` | 3 | **0** |
| `spec-038` | 3 | **0** |
| `spec-039` | 21 | **0** |
| `types/finalizer.py` | 7 | **0** |
| **total** | **46** | **0** |

**Control, so the 0 is the tree and not a broken instrument:** the same script over `git archive HEAD` copies of `spec-037` and `spec-040` reports 10 wrapped across 29 occurrences (`spec-037` 4 at lines 15 / 486 / 1122 / 1655, `spec-040` 6 at 734 / 782 / 884 / 1795 / 1898 / 1951) — the known originals, found. Also censused every `#"` per line, not the first, which is the defect that hid cohort G's site.

Run over this artifact as well, the same instrument reads **6** citation occurrences and **0** wrapped, so the seven-file total is 52 occurrences and 0 wraps. Nothing here reproduces the defect as its own evidence, so a future sweep needs no exception for this file.

Two of this cohort's edits reflowed hard-wrapped paragraphs (`spec-038`'s `Status:` and `spec-039`'s `Status:` and opener). Neither paragraph contains a citation, and the postcondition above is a full-file census rather than a spot check of the edited lines, so no reflow could have created a wrap unseen.

---

## Validation run

| Command | Result |
|---|---|
| `uv run python scripts/check_citations.py` | `OK: 782 citations resolve (705 in 422 .py files, 77 in KANBAN.md).` |
| `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-034-permissions-0_0_10.md` | `OK: 42 terms - all have glossary entries and at least one spec link.` |
| `… --spec docs/SPECS/spec-035-optimizer_hardening-0_0_10.md` | `OK: 23 terms …` |
| `… --spec docs/SPECS/spec-036-mutations-0_0_11.md` | `OK: 38 terms …` |
| `… --spec docs/SPECS/spec-038-form_mutations-0_0_12.md` | `OK: 31 terms …` |
| `… --spec docs/SPECS/spec-039-serializer_mutations-0_0_13.md` | `OK: 38 terms …` |
| `uv run python scripts/check_trailing_commas.py --check <all six files>` | exit 0, no output |
| `uv run ruff format django_strawberry_framework/types/finalizer.py` | `1 file left unchanged` (dry `--diff` first: `1 file already formatted`) |
| `uv run ruff check --fix django_strawberry_framework/types/finalizer.py` | `All checks passed!` |
| `uvx pre-commit run --files django_strawberry_framework/types/finalizer.py` | all five hooks **Passed** on the second run, byte-identical file (see below) |
| `uv run pytest tests/types tests/filters --no-cov -q` | `1034 passed in 6.45s`, 8 workers |
| wrapped-citation census, six files + control | **0** wrapped / 46 occurrences; control 10 wrapped / 29 (table above) |

No `--cov*` flag was passed in any invocation; `--no-cov` is the only coverage-shaped flag used, as `pytest.ini`'s `addopts` requires.

**The citation count is `782`, identical to cohort G's and cohort H's, and this cohort cannot have moved it.** The gate holds `docs/` out of scope, and the one `.py` line touched changes a card id inside a docstring, not a `path::Symbol` citation. The number matching across a window in which cohorts I and J are writing `.py` files is a measured coincidence; the point is that the gate is green and no delta is ours.

**One `pre-commit` result needs stating precisely rather than as a pass.** The **first** run reported `citations resolve … Failed — files were modified by this hook`, while printing `OK: 782 citations resolve`. A copy of `finalizer.py` was taken and the hook re-run: every hook **Passed** and `cmp` against that copy exited 0 — the file was byte-identical. `scripts/check_citations.py` has no write path (`grep -nE 'write_text|--fix'` returns only its `def main`), so the first result is `pre-commit`'s own stash/restore mtime artifact against a tree three other cohorts are writing, not a modification. It is recorded here because "Failed" in a gate log is exactly the thing a later reader would take at face value.

---

## `git status --porcelain` classification

Captured at task start, after the last spec edit, and again after this artifact was written; each pair **differenced rather than eyeballed**: 84 paths → 89 → 94.

First difference (84 → 89), four lines this cohort's and one not:

```
> M docs/SPECS/spec-034-permissions-0_0_10.md
> M docs/SPECS/spec-035-optimizer_hardening-0_0_10.md
> M docs/SPECS/spec-036-mutations-0_0_11.md
> M docs/SPECS/spec-038-form_mutations-0_0_12.md
> ?? docs/builder/bld-slice-3-028-spec_reconciliation.md
```

Second difference (89 → 94), one line this cohort's and four not:

```
> M docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md
> M docs/SPECS/spec-030-connection_field-0_0_9.md
> M docs/SPECS/spec-031-globalid_encoding-0_0_9.md
> M docs/SPECS/spec-032-full_relay-0_0_9.md
> ?? docs/builder/bld-slice-16-027-shipped_state_034_039.md
```

No line was removed in either difference. Every path classifies as:

- **This cohort (7):** `spec-034`, `spec-035`, `spec-036`, `spec-038` (four newly dirty, this cohort alone); `spec-039` and `django_strawberry_framework/types/finalizer.py` (both already `M` at task start, shared — see below); and this artifact (`??`).
- **Cohort I (`.py`, concurrent):** `connection.py`, `tests/test_routers.py`, `tests/test_permissions.py`, `tests/optimizer/test_walker.py` and the wider `.py` set. Untouched.
- **Cohort J, landed mid-pass:** `spec-029`, `spec-030`, `spec-031`, `spec-032` went from clean to `M` between this cohort's second and third status captures. Never read for edit, never written, never reverted; the only effect on this artifact is the `WIP-ALPHA-033` population shrinking between two of its own readings (finding 4).
- **Cohorts G / H, shared or landed spec surface:** `spec-033`, `spec-037`, `spec-040`, `spec-041`, `spec-045`, `spec-046`, `appx/spec-001-…-rationale`, `appx/spec-004-…-rationale`, `appx/spec-009-…-rationale`, `appx/spec-015-…-rationale`. Read for the convention only; never written.
- **The concurrent `spec-028` session:** `docs/SPECS/spec-028-orders-0_0_8.md` (M), `appx/spec-028-orders-0_0_8-rationale.md`, `docs/builder/bld-slice-{1,2,3}-028-*.md`, `docs/builder/build-028-orders-0_0_8.md`. `spec-028` was read for the opener and ticked-checklist conventions; never written, never reverted (`AGENTS.md` rule 34).
- **Cohort D, landed:** `docs/SPECS/spec-055-search_fields-0_1_2.md`. Untouched.
- **Worker 0 and earlier cohorts:** `docs/builder/build-027-filters-0_0_8.md` (M) plus `bld-slice-{6,7,8,9,10,11,12,13,14}-027-*.md` (`??`).

**The two shared files, and why the hunks are separable.**

- `docs/SPECS/spec-039-serializer_mutations-0_0_13.md` was `M` at task start from a concurrent citation repair — two hunks near lines 354 and 2344, retargeting a `forms/resolvers.py` `#"…"` anchor from `#"Authorize BEFORE decoding relations"` to `#"Authorize runs BEFORE the relation decode"`. This cohort's hunks are the opener (lines 3-4), the `Status:` block (lines ~234-244) and the Revision-10 entry (~line 615). Disjoint; both sessions' work coexists. Byte count `HEAD` → tree: 343,952 → 343,558.
- `django_strawberry_framework/types/finalizer.py` was `M` at task start from a concurrent docstring reflow in `_format_owner_target_mismatch_error` (around line 1380), six lines re-wrapped around a `spec-027 #"owning \`FilterSet\`'s target \`DjangoType\`"` citation. This cohort's edit is one line at ~660, inside a different function. Byte count `HEAD` → tree: 99,762 → 99,761 (this cohort −5, the concurrent reflow +4). Confirmed the file's current state before assuming a baseline, as the brief required: `HEAD` is **not** this cohort's baseline for it.

Byte counts, `HEAD` → working tree, for the five specs: `spec-034` 145,408 → 145,643 (+235); `spec-035` 143,253 → 143,045 (−208); `spec-036` 164,266 → 164,498 (+232); `spec-038` 185,789 → 185,815 (+26); `spec-039` 343,952 → 343,558 (−394, of which the concurrent citation repair is part).

### Implementation notes

- **The convention was taken from the archive and the archive had two answers, not one.** `spec-028` and cohort H's `spec-033` / `spec-037` agree on the opener verb (`Shipped in`) but not on the `Status:` spelling (`shipped in \`0.0.8\`.` versus `**SHIPPED (\`0.0.X\`)**`). Matching the later pair keeps this era's realigned records identical to each other; recording the divergence keeps the next pass from "fixing" `spec-028` into a third form.
- **The checklist clause is per-record, not per-convention.** Four of five specs take the stays-unticked clause; `spec-035` takes `spec-028`'s ticked-record clause because its boxes are genuinely ticked. Applying one clause uniformly would have written a false sentence into a `Status:` line whose whole purpose is to be the true one.
- **A card-scope statement is not a falsified claim, and the two look alike.** "No slice in this card edits `pyproject.toml`; the joint cut owns the bump" survives shipping untouched; "the joint cut is the only pending release act" does not. Every version sentence in the five specs was sorted on that test rather than on whether it mentioned a version, which is why `spec-036` needed two edits and `spec-035` needed six.
- **Deleting a falsified premise beats inverting it.** `spec-038`'s "`039` is not yet specced" could have become "`039` reuses every one of them", but that is a claim about `039`'s implementation this cohort has not measured per-axis. The premise went; the design statement it was hedging stayed.
- **Every measurement was taken against the working tree**, and the two shared files were re-read at the start rather than assumed to match `HEAD`, because three other cohorts are writing this tree. The `HEAD` snapshots used for the link-integrity difference and the wrapped-citation control were taken read-only via `git archive` / `git show` into a scratch path outside the repository; no `git stash`, `checkout`, `restore` or `worktree` was used.

### Notes for Worker 3

No Worker 2 / Worker 3 cycle: the diff adds no executable statement and the one `.py` change is proved token-identical. If one runs anyway, the four claims worth re-deriving mechanically are the `WIP-ALPHA` occurrence counts (five `grep -oF … | wc -l`), the board-id table (seven `grep -oE … | sort | uniq -c`), the `spec-035` `### Decision` count (`grep -c '^### Decision '` → 9), and the token-identity walk (the script is in this session's private `cohortK-027/` scratchpad and takes no arguments).

### Notes for Worker 1 / Worker 0 — findings left in place

Each is measured; each is outside this cohort's fence or its dispatch; none was repaired.

1. **None of the five specs has a rationale companion, and all five keep their deliberative layer inline.** `docs/SPECS/appx/` carries a `-terms.csv` for each and no `-rationale.md` for any. This is the same condition cohort H reported for `spec-040`, now measured across `034` / `035` / `036` / `038` / `039` as well — seven consecutive cards in the `029`–`043` band, which is exactly the band cohort F identified as never having had a companion. `spec-039`'s Revision-10 falsehood is a direct consequence: a spec that narrates its own history acquires a claim about its own header that its next correction falsifies. Carding the companion creation is Worker 0's.
2. **A large stale `TODO-ALPHA-` population survives in this cohort's five files, deliberately untouched.** Occurrences after the pass, `grep -oE '(TODO-ALPHA|TODO-BETA|BLOCKED-ALPHA)-[0-9]{3}-[0-9.]+' | wc -l`: `spec-034` **19** (own id `TODO-ALPHA-034-0.0.10` ×9, `TODO-ALPHA-033-0.0.10` ×3, `TODO-ALPHA-027-0.0.10` ×1, `TODO-ALPHA-035-0.0.10` ×2, `TODO-BETA-046-0.1.1` ×4 — note the `033-0.0.10` and `027-0.0.10` spellings are pre-renumber ids for *this* card, flagged as such by the spec's own `## Risks and open questions`), `spec-035` **0**, `spec-036` **10**, `spec-038` **10**, `spec-039` **13** — **52** across the five. Almost all name the literal marker text of a source comment or a `docs/TREE.md` reservation ("planned by `TODO-ALPHA-038-0.0.12`"), or are revision-log rows, or are imperative Slice-5 board-move steps — the same population class cohort H left in `spec-037` with the same reasoning: they are internally consistent, so the spec is not half-reconciled, and a card-`NNN` pass would need to decide the whole population at once. **The dispatch named `WIP-ALPHA` only**, and this population is over five times larger than the nine `WIP-ALPHA` occurrences it did name.
3. **`connection.py`'s half of cohort H's item 3 is already discharged by another cohort, and the ordering hazard it warned about no longer exists.** `connection.py` reads ``DONE-033-0.0.9`` and `spec-033` carries no `WIP-ALPHA-033` id at the site that quoted it. With `types/finalizer.py` closed here, `grep -rn "WIP-ALPHA-033" --include='*.py' .` returns **0** repo-wide. Worth recording because the dispatch still described the `.py`-first ordering as an open constraint.
4. **Seven spec-side `WIP-ALPHA-033` occurrences remain over six lines, all outside this cohort's partition — and the population moved while this pass ran.** Final measurement, `grep -roF "WIP-ALPHA-033" docs/SPECS/ | wc -l` → **7**, on 6 lines: `docs/SPECS/spec-032-full_relay-0_0_9.md` (1 line), `docs/SPECS/spec-033-connection_optimizer-0_0_9.md` (2 lines — Revision 1 and the Slice 7 board move, both of which cohort H decided deliberately), and one description-column row each in `appx/spec-031-globalid_encoding-0_0_9-terms.csv`, `appx/spec-032-full_relay-0_0_9-terms.csv` and `appx/spec-034-permissions-0_0_10-terms.csv`. **The first measurement of this population, taken at the start of Task 2, was larger** — it also carried hits in `spec-030` and `spec-031` and several more lines in `spec-032`; cohort J landed its `spec-029` / `030` / `031` / `032` edits between the two readings (all four went from clean to `M` mid-pass), which is what removed them. Recorded because the shrinkage is a concurrent cohort's work, not a correction to the earlier reading, and because it is why the two numbers in this artifact differ. The three `-terms.csv` rows are a surface no cohort in this cycle has been given, and `spec-034`'s row belongs to this cohort's *card* but not to its writable set.
5. **`spec-035` narrates its own history in its opener.** Line 3 reads "the [Current state](#current-state) section, as reconciled in Revision 4, describes the shipped repo" — a spec pointing at its own revision round, which `BUILD.md` `## Spec rationale extraction` forbids outright. Not dispatched, and repairing it properly means the rationale move (finding 1), so it is reported rather than patched.
6. **`spec-039` carries orphaned review-round ids in normative prose: `F8` ×11 and `F11` ×13** (`grep -oE '\bF(8|11)\b' | sort | uniq -c`), including in the `Status:` line this cohort rewrote, where `F8` was preserved rather than invented. The spec has no companion for them to resolve into — the same never-extractable class cohort F measured at 26 occurrences in `.py`. Retiring them is a spec-wide vocabulary decision, not a `Status:`-line one.
7. **`spec-036` twice calls `DjangoMutationField` a symbol "the glossary does not yet name"** (`grep -c 'does not yet name'` → **2**, in the opener's Predecessors paragraph and in `## Doc updates`). Slice 5 shipped that glossary entry, so both are stale — but the `## Doc updates` one is an imperative slice instruction describing the pre-slice state, the class cohort H left in `spec-033`'s Slice 7 step, and the opener one is inside the sentence that names what Slice 5 did. Left as one population for a card-`036` pass to decide together, rather than half-fixed here.

---

## Final verification (Worker 1)

Deferred to Worker 1's final pass per the dispatch: this artifact stays `Status: built`.

<!-- LINK DEFINITIONS -->

<!-- Root -->

[changelog]: ../../CHANGELOG.md
[kanban]: ../../KANBAN.md

<!-- docs/ -->

[docs-readme]: ../README.md
[glossary-serializermutation]: ../GLOSSARY.md#serializermutation

<!-- docs/SPECS/ -->

[next]: ../SPECS/NEXT.md
[spec-027]: ../SPECS/spec-027-filters-0_0_8.md
[spec-034]: ../SPECS/spec-034-permissions-0_0_10.md
[spec-035]: ../SPECS/spec-035-optimizer_hardening-0_0_10.md
[spec-036]: ../SPECS/spec-036-mutations-0_0_11.md
[spec-038]: ../SPECS/spec-038-form_mutations-0_0_12.md
[spec-039]: ../SPECS/spec-039-serializer_mutations-0_0_13.md
[spec-045]: ../SPECS/spec-045-visibility_boundary-0_0_14.md

<!-- docs/builder/ -->

[plan]: build-027-filters-0_0_8.md
[slice-13]: bld-slice-13-027-shipped_card_spec_staleness.md

<!-- django_strawberry_framework/ -->

[types-finalizer]: ../../django_strawberry_framework/types/finalizer.py

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
