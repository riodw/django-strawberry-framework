# Build: Catalog cohort J — the `0.0.9` Relay cohort's four specs describe shipped cards as unshipped (027)

Spec reference: [`docs/SPECS/spec-027-filters-0_0_8.md`][spec-027] owns the catalog this cohort discharges, but no corrected surface points at spec-027. The four dispatched defects belong to the `0.0.9` cohort's own cards: [`spec-029-consumer_dx_cleanup-0_0_9.md`][spec-029], [`spec-030-connection_field-0_0_9.md`][spec-030], [`spec-031-globalid_encoding-0_0_9.md`][spec-031], and [`spec-032-full_relay-0_0_9.md`][spec-032]. The dispatch is the staleness class cohort H measured and left standing on five further specs ([`bld-slice-13-027-shipped_card_spec_staleness.md`][slice-13] `### Notes for Worker 1 / Worker 0 — findings left in place` item 2).
Status: final-accepted

## Plan (Worker 1)

### Planning lives in the build plan; this cohort's fence came from the dispatch

**Ownership partition (declared, disjoint):** `docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md`, `spec-030-connection_field-0_0_9.md`, `spec-031-globalid_encoding-0_0_9.md`, `spec-032-full_relay-0_0_9.md`, plus this artifact. All four specs were edited; **all four were clean at `HEAD` at task start**, so no hunk in this cohort shares a file with another party.

Cohort I is writing `.py` files concurrently; cohort K holds `spec-034` / `035` / `036` / `038` / `039`; a separate session holds `spec-028` and its companions; cohort D's `spec-055` landing sits in the tree. No `.py` file, no `spec-027` / `spec-028` / `spec-055` surface, and no cohort-H or cohort-K spec was read for edit, written, or reverted (`AGENTS.md` rule 34).

### Dispatched findings checklist

Authored by Worker 1 (this cohort has no separate planning spawn). Each tick is re-derivable from the sections below.

- [x] Re-derive Worker 0's four figures rather than transcribing them, and reconcile the units
- [x] Verify each of the four cards' real state **and current id** on `KANBAN.md`, by title as well as by number
- [x] Verify cohort H's measured convention (prose opener dominant, `Target release:` confined to the `001`-`027` era, the `spec-028` / `spec-040` realigned form, the unticked-checklist rule) rather than trusting it
- [x] Rewrite each opener and each `Status:` line to the shipped form; tick nothing
- [x] Retire every `WIP-ALPHA` id to its verified current board spelling, per id, and classify the historical non-edits
- [x] Sweep for claims falsified by shipping and delete rather than restate them
- [x] Fix the whole blast radius per spec, then show the retired-vocabulary sweep empty
- [x] Census every `#"` per line (not the first) for wrapped citations, precondition and postcondition, with a control
- [x] Check whether a live `.py` comment quotes a string being changed, and stop at the ordering dependency

---

## Build report (Worker 1, acting as the cohort's only pass)

### Files touched

- `docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md` — opener, `Status:`, checklist preamble, two parity-table rows, the filename derivation, Decision 11's sibling-card list, and three board-move / definition-of-done sites.
- `docs/SPECS/spec-030-connection_field-0_0_9.md` — opener, `Status:`, checklist preamble, Decision 2's card-scope boundary list, Decision 13's body and justification, four dependency-direction clauses, and three board-move / definition-of-done sites.
- `docs/SPECS/spec-031-globalid_encoding-0_0_9.md` — opener, `Status:` (the archive's worst instance), checklist preamble, Decision 2's intro, Decision 12's body and justification, one `## Current state` pointer, and three board-move / definition-of-done sites.
- `docs/SPECS/spec-032-full_relay-0_0_9.md` — opener, `Status:`, checklist preamble, two `## Key glossary references` bullets, two `## Current state` pointers, three `## Non-goals` bullets, Decision 2's boundary list, one Decision-6 justification bullet, Decision 13's body and justification, one `## Edge cases` bullet, one `## Risks` bullet, three `## Out of scope` bullets, and three board-move / definition-of-done sites.

Edits were applied by two scratchpad scripts (outside the repo, `027` in every filename) that assert each replacement's **expected occurrence count before writing** and abort without writing any file if a single count is off, plus one three-line follow-up. Every count matched on the first run, so no site was located by guesswork.

### Tests added or updated

None. The diff adds no executable statement and changes no contract a test can pin.

---

## The four figures, re-derived — and Worker 0's unit is lines, not occurrences

Worker 0's table reads 7 / 10 / 7 / 17 `WIP-ALPHA` "occurrences". Those are **matching lines**; the occurrence counts are higher because several lines carry two, three, or four ids. Both instruments are reported so the artifact cannot be read as contradicting the dispatch.

| Spec | `Status:` line opened | Lines with `WIP-ALPHA` (Worker 0's figure) | `WIP-ALPHA` occurrences |
| --- | --- | --- | --- |
| spec-029 | `in build — Slices 1-3 implemented and accepted; Slice 4 (KANBAN move) + joint 0.0.9 cut pending.` | 7 | **12** |
| spec-030 | `in build — Slices 1-5 accepted; integration + final-gate pending.` | 10 | **12** |
| spec-031 | **`planned — not started.`** | 7 | **9** |
| spec-032 | `in build — all seven slices implemented (final-accepted in the build cycle, uncommitted; …)` | 17 | **20** |

`spec-031` is confirmed as the archive's worst instance: a `Status:` line asserting the work had not begun on a card whose contract is on disk at `HEAD` — `types/relay.py::encode_typename` (473), `::install_globalid_typename_resolver` (582), `::decode_global_id` (675), and 26 `globalid_strategy` occurrences in that one module.

## Card state and current id, verified per card by title as well as by number

`KANBAN.md` is the authority. `grep -o 'WIP-ALPHA-[0-9]*-[0-9.]*' KANBAN.md` returns **nothing at all** — no `WIP-ALPHA` id survives anywhere on the board — so every one of these ids is dangling, not merely stale. Each number was then confirmed against the board's own card title and `SpecDoc` link, because the 2026-07-30 renumber moves numbers with completion order and `DONE-` plus the same number is exactly what must not be assumed.

| Spec | Board id | Board hits | Board title (and `SpecDoc` row) |
| --- | --- | --- | --- |
| spec-029 | `DONE-029-0.0.9` | 7 | "`DjangoType` consumer-DX cleanup pass" → `docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md` |
| spec-030 | `DONE-030-0.0.9` | 28 | "`DjangoConnectionField`" → `docs/SPECS/spec-030-connection_field-0_0_9.md` |
| spec-031 | `DONE-031-0.0.9` | 3 | "Django-model-based GlobalID encoding" → `docs/SPECS/spec-031-globalid_encoding-0_0_9.md` |
| spec-032 | `DONE-032-0.0.9` | 12 | "Full Relay story (Node + Connection + Root + validation)" → `docs/SPECS/spec-032-full_relay-0_0_9.md` |

The release itself shipped, not merely the four cards: [`CHANGELOG.md`][changelog] carries `## [0.0.9] - 2026-06-13`, and `pyproject.toml` is at `0.0.14`.

## The convention, confirmed rather than trusted

Three separate measurements, each re-derived here.

**The prose opener is dominant and stays.** 17 of the 56 archived specs carry a `Target release:` header line and 39 do not; the `Target release:` family is the `001`-`027` era. None of these four specs has one, so importing that shape would adopt a superseded era's header block. **Corrected in place, never removed.**

**The realigned form.** [`spec-028`][spec-028] opens "Shipped in `0.0.8` (card [`DONE-028-0.0.8`][kanban], moved from `WIP-ALPHA-028-0.0.8` at Slice 5). **This spec is the final implementation record, not an open build plan.**" and `spec-040` "Shipped in `0.0.13` (card [`DONE-040-0.0.13`][kanban])." Both confirmed on disk. The simple form (`Shipped in X (card [DONE-NNN-X][kanban])`) is what these four take, and `spec-028` supplies the replacement clause verbatim.

**The unticked-checklist rule, and where this cohort does NOT follow spec-028.** [`spec-045`][spec-045]'s `Status:` line states the rule — "The Slice checklist boxes below stay unticked because the `Status:` line is the completion source of truth (the shipped-spec convention)" — and `047` / `048` / `049` repeat it. `spec-028` is the one realigned record that says the opposite ("the [Slice checklist](#slice-checklist) is ticked to reflect the executed plan"). This cohort takes `spec-028`'s **opener clause** and `spec-045`'s **checklist rule**, per the dispatch. Proof that nothing was ticked: `- [x]` count is **0** at `HEAD` and **0** in the working tree for all four specs, and the `- [ ]` counts are unchanged at 25 / 29 / 30 / 37.

**The board-move bullet: measured, and the archive's reconciled records resolve it.** Cohort H left `spec-033:564`'s "move [`WIP-ALPHA-033-0.0.9`][kanban] to Done" in place and flagged it as possibly owed (its finding 5). A census of the archive's *reconciled* shipped records answers the question: `spec-020` ("Move `DONE-020-0.0.7` to the Done column"), `spec-021`, `spec-025` ("keeping its `DONE-025-0.0.7` id"), `spec-022` ("moves the card to Done") and this cycle's own `spec-027` Slice 3 ("move **this card** to the Done column, where it is `DONE-027-0.0.8` (the column-move pass assigns the next available id)") carry the **resolved id or no id at all** — **zero of five** carry a pre-move id. The pre-move spelling survives only in specs nobody has reconciled. So these four follow `spec-027`'s reconciled wording, which is this cycle's own precedent, and the same treatment closes the `DONE-NNN-0.0.9` placeholder in each definition-of-done item (`spec-027` DoD 22 was corrected the same way).

## Per-spec before / after: opener and `Status:`

Only the changed clauses are quoted; the slice enumerations that follow each `Status:` head were not touched.

### spec-029

**Opener.** Before: "Planned for `0.0.9` (card [`WIP-ALPHA-029-0.0.9`][kanban]). **This spec is an open build plan, not a shipped record.** The three functional slices (1-3) have now been implemented and accepted during the build; the card is not yet formally Done (Slice 4's KANBAN move and the joint `0.0.9` cut remain). The [Slice checklist] below stays unticked as the original contract record (build progress is tracked in the build plan, not here);" — After: "Shipped in `0.0.9` (card [`DONE-029-0.0.9`][kanban]). **This spec is the final implementation record, not an open build plan.** The [Slice checklist] below stays unticked because the `Status:` line is the completion source of truth (the shipped-spec convention; build progress is tracked in the build plan, not here);". The sibling-card clause moved from "three sibling WIP cards (`WIP-ALPHA-030/031/032-0.0.9`)" to "three sibling cards (`DONE-030/031/032-0.0.9`)".

**`Status:`.** Before: "Status: in build — Slices 1-3 implemented and accepted; Slice 4 (KANBAN move) + joint `0.0.9` cut pending." — After: "Status: **SHIPPED (`0.0.9`)** — card [`DONE-029-0.0.9`][kanban], released under the [`CHANGELOG.md`][changelog] `## [0.0.9]` heading." Its tail moved from "The card body counts as complete when all three slices land; if the schedule forces Slice 3 to defer, the slice carves off as its own follow-up card …" to "All three slices landed, so the Slice-3 carve-off contingency in [Decision 12] does not apply." plus the unticked-checklist sentence.

### spec-030

**Opener.** "Planned for `0.0.9` (card …). **This spec is an open build plan, not a shipped record.** The card is the lowest-NNN WIP card in the `0.0.9` cohort and the **central read-side primitive** …, and the [Full Relay story] ([`DONE-032-0.0.9`][kanban]) is hard-blocked on it landing." → "Shipped in `0.0.9` (card …). **This spec is the final implementation record, not an open build plan.** The card is the **central read-side primitive** …, and the [Full Relay story] ([`DONE-032-0.0.9`][kanban]) builds directly on it." Same unticked-clause rewrite; siblings retired.

**`Status:`.** "Status: in build — Slices 1-5 accepted; integration + final-gate pending." → "Status: **SHIPPED (`0.0.9`)** — card [`DONE-030-0.0.9`][kanban], released under the [`CHANGELOG.md`][changelog] `## [0.0.9]` heading." The unticked sentence was appended to the line's end.

### spec-031

**Opener.** "Planned for `0.0.9` … **This spec is an open build plan, not a shipped record.** The card is the lowest-NNN WIP card in the `0.0.9` cohort and the **Relay identity-format decision** …" → "Shipped in `0.0.9` … **This spec is the final implementation record, not an open build plan.** The card is the **Relay identity-format decision** …". Siblings retired; the unticked clause rewritten.

**`Status:`.** "Status: planned — not started." → "Status: **SHIPPED (`0.0.9`)** — card [`DONE-031-0.0.9`][kanban], released under the [`CHANGELOG.md`][changelog] `## [0.0.9]` heading." Unticked sentence appended.

### spec-032

**Opener.** "Planned for `0.0.9` (card [`WIP-ALPHA-032-0.0.9`][kanban]). **This spec is an open build plan, not a shipped record.** The card is the lowest-NNN WIP card in the `0.0.9` cohort and the **connective tissue of the Relay surface** …" → "Shipped in `0.0.9` (card [`DONE-032-0.0.9`][kanban]). **This spec is the final implementation record, not an open build plan.** The card is the **connective tissue of the Relay surface** …". The sibling clause moved from "the sibling WIP card [`WIP-ALPHA-033-0.0.9`][kanban] and the already-shipped …" to "the sibling card [`DONE-033-0.0.9`][kanban] and …".

**`Status:`.** The whole head — "in build — all seven slices implemented (final-accepted in the build cycle, uncommitted; Slice 4 includes the always-concrete `_connection_type_for` guard fix shipped via plan amendment …); the cross-slice integration pass is closed (final-accepted) and the final test-run gate passed clean (full `--no-cov` sweep 1629 passed / 3 skipped, Django `manage.py check` + `makemigrations --check`, and the `ruff format --check` / `ruff check` / `git diff --check` lint-format-diff gate all green); the build is complete and uncommitted, pending the maintainer's commit and the joint-`0.0.9`-cut version bump" — was replaced by "Status: **SHIPPED (`0.0.9`)** — card [`DONE-032-0.0.9`][kanban], released under the [`CHANGELOG.md`][changelog] `## [0.0.9]` heading." **No gate colour is asserted for any of the four cards**, because no `029`-`032` build artifact survives to measure against: `docs/builder/DONE/` carries `build-001` … `build-026` and then `build-044` onward.

## The `WIP-ALPHA` retirement table

53 occurrences before, **7** after — 46 retired. Every target spelling is the one verified on the board above.

| Spec | Site | Retired to | Class |
| --- | --- | --- | --- |
| 029 | opener (line 3), card id | `DONE-029-0.0.9` | live claim |
| 029 | opener, three sibling ids | `DONE-030/031/032-0.0.9` | live claim |
| 029 | parity table (184), `WIP-ALPHA-030/031/032-0.0.9` | id dropped, row now `shipped (0.0.9)` | live claim |
| 029 | filename derivation (304) | `DONE-029-0.0.9` | live claim |
| 029 | Decision 11 body (500), three ids | `DONE-030/031/032-0.0.9` | live claim |
| 029 | slice-checklist board move (123) | "this card … where it is `DONE-029-0.0.9`" | instruction |
| 029 | doc-updates board move (639) | same | instruction |
| 029 | definition of done 15 (702) | `DONE-029-0.0.9` | placeholder |
| 030 | opener, card id + three siblings | `DONE-030/031/032/033-0.0.9` | live claim |
| 030 | Decision 2 boundary list (314-317), four ids | `DONE-030/031/032/033-0.0.9` | live claim |
| 030 | filename derivation (302) | `DONE-030-0.0.9` | live claim |
| 030 | Decision 13 body (509) | "the four Relay cards" | live claim |
| 030 | board moves (102, 619) + definition of done 9 (676) | `DONE-030-0.0.9` | instruction / placeholder |
| 030 | **Revision 1 (13)** | **not edited** | historical |
| 031 | opener, card id + two siblings | `DONE-031/032/033-0.0.9` | live claim |
| 031 | `## Current state` (150) | `DONE-032-0.0.9` | pointer in a tense-fenced section |
| 031 | filename derivation (293) | `DONE-031-0.0.9` | live claim |
| 031 | Decision 2 intro (304) | "four Relay cards beside `DONE-029-0.0.9`" | live claim |
| 031 | Decision 12 body (520) | "the Relay cards" | live claim |
| 031 | board moves (125, 661) + definition of done 8 (711) | `DONE-031-0.0.9` | instruction / placeholder |
| 031 | **Revision 1 (52), two ids** | **not edited** | historical |
| 032 | opener, card id + sibling | `DONE-032-0.0.9`, `DONE-033-0.0.9` | live claim |
| 032 | key glossary (62, 63) | `DONE-033-0.0.9` | live claim |
| 032 | `## Current state` (137, 144) | `DONE-033-0.0.9` | pointer in a tense-fenced section |
| 032 | `## Non-goals` (159) | `DONE-033-0.0.9` | live claim |
| 032 | filename derivation (276) | `DONE-032-0.0.9` | live claim |
| 032 | Decision 2 boundary list (291) | `DONE-033-0.0.9`, "(shipped)" | live claim |
| 032 | Decision 6 justification (374) | `DONE-033-0.0.9` | live claim |
| 032 | Decision 13 body (491) | `DONE-033-0.0.9` | live claim |
| 032 | `## Edge cases` (478) | `DONE-033-0.0.9` | live claim |
| 032 | `## Risks` (633) | `DONE-033-0.0.9` | live claim |
| 032 | board moves (120, 623) + definition of done 11 (686) | `DONE-032-0.0.9` | instruction / placeholder |
| 032 | **Revision 1 (43), three ids** | **not edited** | historical |
| 032 | **`## Current state` (135), quoted `.py` docstring** | **not edited** | `.py`-first ordering |

### The seven survivors, each a decided non-edit

**Six are `**Revision 1**` bullets** — `spec-030:13`, `spec-031:52` (two ids), `spec-032:43` (three ids). The rule applied: an id inside a revision-log bullet is part of the recorded event ("initial draft authored from the [`WIP-ALPHA-031-0.0.9`][kanban] card body via the `docs/SPECS/NEXT.md` flow"), so rewriting it falsifies a true record of the drafting. Everywhere else the id is a **pointer** to a board row, and a pointer's job is to resolve today. That is the line this cohort drew, and it is the same distinction cohort H recorded for `spec-037`'s revision-history entries.

**The seventh is `spec-032:135`, and it is a `.py`-first ordering dependency.** That line quotes `types/relay.py::decode_global_id`'s docstring verbatim, including the card id: the spec says the dispatch is "documented in-source as \"the forward-looking piece root `node(id:)` / `nodes(ids:)` (`WIP-ALPHA-032-0.0.9`) will consume\"", and `types/relay.py:680` at `HEAD` reads exactly that. **The spec text is correct; the `.py` site is the finding.** Changing the spec first would make the spec misquote live source. `grep -rn 'WIP-ALPHA' --include='*.py' .` returns three sites repo-wide: `types/relay.py:680` (this one), `types/finalizer.py:660` (`WIP-ALPHA-033-0.0.9`, the site cohort H already reported), and `examples/fakeshop/apps/kanban/models.py:512`, where `WIP-ALPHA-030-0.0.9` is a **format example** in a docstring describing the card-id shape and is correct as an illustration. `.py` is cohort I's surface.

### Two further stale card ids, same class, retired after checking each rather than pattern-substituting

- **`TODO-ALPHA-034-0.0.10` → `DONE-034-0.0.10`** (4 sites in `spec-032`: 68, 161, 292, 643). The board carries `DONE-034-0.0.10` "Permissions subsystem"; `permissions.py::apply_cascade_permissions` is on disk and `CHANGELOG.md` carries `## [0.0.10] - 2026-06-16`. Same defect as the dispatch's: a shipped card named by an unshipped id.
- **`TODO-BETA-047-0.1.2` → `TODO-BETA-055-0.1.2`** (3 sites in `spec-032`: 69, 163, 645). This one is the renumber trap the dispatch warns about. `grep -c 'TODO-BETA-047-0.1.2' KANBAN.md` returns **0**, and `047` today names `DONE-047-0.0.14` — a real, shipped, unrelated card, which is strictly worse than a dangling id. The `0.1.2` `Meta.search_fields` card is `TODO-BETA-055-0.1.2`, confirmed twice: the board's `0.1.x` id list carries it, and [`spec-055-search_fields-0_1_2.md`][spec-055]'s own opener reads "Planned for `0.1.2` (card `TODO-BETA-055-0.1.2`)". It is still `TODO`, so the surrounding "stays absent until `0.1.2`" prose is true and was left.
- **`TODO-BETA-061-0.1.5` (7 sites in `spec-032`) — verified current and NOT changed.** `grep -c` returns 10 on the board. Pattern-substituting every `TODO-BETA-` id would have broken these.

## Falsified claims deleted, with the measurement for each

Deleted rather than restated, per the dispatch and `BUILD.md`'s rule that prose the current state has falsified belongs in neither file.

| # | Spec | Claim deleted | Measurement that falsifies it |
| --- | --- | --- | --- |
| 1 | 029 | "the card is not yet formally Done (Slice 4's KANBAN move and the joint `0.0.9` cut remain)" | board carries `DONE-029-0.0.9` at 7 sites; `CHANGELOG.md` `## [0.0.9] - 2026-06-13` |
| 2 | 029 | "Slice 4 (KANBAN move) + joint `0.0.9` cut pending" | as above |
| 3 | 029 | the open Slice-3 carve-off contingency ("if the schedule forces Slice 3 to defer …") | Slice 3 landed: `types/base.py:82` carries `nullable_overrides` in `ALLOWED_META_KEYS`; `examples/fakeshop/apps/library/schema.py:166` declares `NullabilityOverrideBookType` |
| 4 | 029 | parity row "planned (`0.0.9` — `WIP-ALPHA-030/031/032-0.0.9`)" | all three cards `DONE`; row is now `shipped (0.0.9)`, matching the two `shipped (0.0.8)` rows above it |
| 5 | 029 | parity row "planned (`0.0.10`)" for `apply_cascade_permissions` | `permissions.py::apply_cascade_permissions` on disk; `CHANGELOG.md` `## [0.0.10] - 2026-06-16` |
| 6 | 029 | Decision 11's sibling labels — `WIP-ALPHA-031` called "the full Relay story", `WIP-ALPHA-032` called "Connection-aware optimizer planning" | board titles: `031` = GlobalID encoding, `032` = Full Relay story, `033` = connection-aware optimizer planning. Two of three labels were **wrong**, not merely stale; corrected while retiring the ids |
| 7 | 030 | "integration + final-gate pending" | card `DONE`; release cut |
| 8 | 030, 031, 032 | "The on-disk version is still `0.0.8`; several `0.0.9`-tagged surfaces already ship under `[Unreleased]` against the unchanged version." (three sites, identical text) | `pyproject.toml` is at `0.0.14`; `CHANGELOG.md` carries a `## [0.0.9]` release heading. The tense-marked twin in each opener — "(the on-disk version is still `0.0.8` at spec-authoring time)" — **stays**, per cohort H's ruling on the same sentence in `spec-033` |
| 9 | 030, 031, 032 | "when multiple **WIP** cards share the target patch version" (three sites) | no `WIP-ALPHA` id exists on the board at all |
| 10 | 031 | "planned — not started" | `types/relay.py` ships `encode_typename` / `install_globalid_typename_resolver` / `decode_global_id` at `HEAD` |
| 11 | 031 | "`0.0.9` carries three WIP Relay cards plus two shipped ones" | half-reconciled: the boundary list **immediately below it** already used `DONE-030/031/032/033` ids |
| 12 | 032 | the whole `Status:` build narration — "final-accepted in the build cycle, uncommitted", the integration-pass and final-gate colours, "full `--no-cov` sweep 1629 passed / 3 skipped", "pending the maintainer's commit" | the card is `DONE`, `0.0.9` is released, and a spec never narrates its own build cycle |
| 13 | 032 | "every connection (root or nested) derives an **empty** optimizer plan, so nested `edges { node }` selections lazy-load" (key glossary, edge cases, risks) | `optimizer/extension.py:1490` `apply_connection_optimization` resolves the target model from the registered definition and delegates to `DjangoOptimizerExtension.apply_to`; `connection.py` calls it at 1562 and 1571. Measured on a `git show HEAD:` copy because cohort I is rewriting both modules |
| 14 | 032 | "[`connection.py`][connection] never consults the `DST_OPTIMIZER_STRICTNESS` / `DST_OPTIMIZER_PLANNED` sentinels" (key glossary, edge cases, risks) | `connection.py:95` imports `_check_n1` from `types/resolvers.py` and calls it at 1990 with `kind="connection_to_attr"`; its docstring at 1923 names the probe |
| 15 | 032 | "the Node entry points … integrate with declared permissions when it lands" / "when that card lands" (two sites) | `DONE-034-0.0.10` shipped |
| 16 | 032 | "nested-connection selections lazy-load until the walker lands" in the Decision 2 boundary list, and the Risks bullet's "Preferred answer / Fallback" pair predicting `033` might slip the cut | `033` shipped in the same `0.0.9` cut; the risk is settled, so the spec now states which way |
| 17 | 030 | "hard-blocked on this card landing" / "hard-blocked on this card" (three sites: problem statement, non-goals, out of scope) | `DONE-032-0.0.9` shipped; the sentences now read "depends on this card" |
| 18 | 029, 030, 031, 032 | "Boxes are unticked because the work has not started." (four sites) | all four cards shipped; replaced by the `spec-045` convention sentence. **No box was ticked** |
| 19 | 029, 030, 031, 032 | twelve `DONE-NNN-0.0.9` placeholders across the slice checklists, doc-updates blocks, and definition-of-done items | the ids are known; `spec-027` DoD 22's identical placeholder was resolved the same way this cycle |

No `## In progress` column claim and no `bld-*` build-artifact reference existed in any of the four specs; the sweep below shows both empty.

## Blast-radius sweep, per spec, shown empty

One instrument over all four files, after the edits:

```shell
grep -nE 'open build plan|not a shipped record|Status: in build|Status: planned|Status: in progress|lowest-NNN WIP|sibling WIP card|WIP Relay card|multiple WIP cards|DONE-NNN|work has not started|on-disk version is still|hard-blocked|awaits maintainer|## In progress|bld-slice|bld-final|bld-integration|when it lands|when that card lands|until it lands|until the walker lands' \
  docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md docs/SPECS/spec-030-connection_field-0_0_9.md \
  docs/SPECS/spec-031-globalid_encoding-0_0_9.md docs/SPECS/spec-032-full_relay-0_0_9.md
```

Returns **four lines, all of them the new correct clause** "**This spec is the final implementation record, not an open build plan.**" — one per spec, matching on `open build plan`. Every other alternative returns nothing in every file. A second sweep for the stale non-`WIP` ids (`TODO-ALPHA-034`, `TODO-BETA-047`) returns **0** in all four files.

Two negative controls on the sweep itself: `TODO-BETA-061-0.1.5` still returns 7 hits in `spec-032` (a *correct* id the sweep must not have touched), and the `- [x]` census returns 0 in all four files (a tick the sweep must not have introduced).

## Structural postconditions

| Check | Result |
| --- | --- |
| `- [x]` boxes, `HEAD` → tree, all four specs | 0 → 0 |
| `- [ ]` boxes, `HEAD` → tree | 25 → 25, 29 → 29, 30 → 30, 37 → 37 |
| every `^#` heading line, `HEAD` vs tree (md5 per file) | **identical** in all four — no `### Decision N` heading moved, so every in-page anchor target survives |
| in-page anchors used vs headings present | 18 / 19 / 14 / 19 used, **0 unresolved** |
| reference-style link definitions | **0 undefined refs** and 0 newly-orphaned defs in all four. `spec-030`'s `[goal]` definition is orphaned, but it is orphaned at `HEAD` too (`git show HEAD:… \| grep -c '\]\[goal\]'` → 0), so it is pre-existing and was left |
| new ref-ids added | none — every id used (`kanban`, `changelog`, `glossary-get_queryset-visibility-hook`) was already defined and already in use |

## Wrapped-citation census: precondition, postcondition, control

The instrument walks **every** `#"` occurrence per line with `str.find` in a loop, classifying test-closure first and only then the predecessor character, so it does not inherit the first-occurrence bug that hid `spec-004`'s wrap from Worker 0 and that the dispatch names explicitly.

| Run | Scope | `#"` occurrences | Wrapped |
| --- | --- | --- | --- |
| Precondition | the four specs, working tree = `HEAD` | 21 | **0** |
| Postcondition | the four specs, after all edits | 21 | **0** |
| Control | `git show HEAD:docs/SPECS/spec-037-…` snapshot outside the repo | 8 | **4** — the instrument still finds known originals, so the 0 is the files, not a broken instrument |

Occurrence count identical before and after, so **no reflow disturbed a citation**: every replacement was contained within one line, and the one multi-line construct rewritten (`spec-032`'s Edge-cases bullet) carried no `#"` anchor. Run against this artifact the same instrument reads 5 `#"` occurrences and **0** wrapped — all five sit inside code spans naming the class, none is a citation.

## Validation run

| Command | Result |
| --- | --- |
| `uv run python scripts/check_citations.py` | `OK: 782 citations resolve (705 in 422 .py files, 77 in KANBAN.md).` |
| `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md` | `OK: 44 terms - all have glossary entries and at least one spec link.` |
| `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-030-connection_field-0_0_9.md` | `OK: 50 terms …` |
| `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-031-globalid_encoding-0_0_9.md` | `OK: 31 terms …` |
| `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-032-full_relay-0_0_9.md` | `OK: 40 terms …` |
| `uv run python scripts/check_trailing_commas.py --check <all four specs>` | exit 0, no output |
| wrapped-citation census | 21 → 21 occurrences, **0** wrapped, control 4 (table above) |

**The citation count is `782`, identical to cohort G's and cohort H's, and this cohort cannot have moved it.** The gate holds `docs/` out of scope by design and every file this cohort touched is under `docs/`. Any future delta belongs to another cohort's `.py` surface.

No `pytest` was run: the diff adds no executable statement.

## `git status --porcelain` classification

Captured before the first edit, after the last spec edit, and again after this artifact was written; each pair diffed rather than eyeballed. Before: **84** paths. After the spec edits: **93**. After this artifact: **95**. The eleven new lines:

- **This cohort (5):** `M docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md`, `spec-030-connection_field-0_0_9.md`, `spec-031-globalid_encoding-0_0_9.md`, `spec-032-full_relay-0_0_9.md`, and `?? docs/builder/bld-slice-15-027-shipped_state_029_032.md` (this file). All four specs were **clean at task start**, so this cohort is the only party in any of them.
- **Cohort K, landed mid-pass (5):** `M docs/SPECS/spec-034-permissions-0_0_10.md`, `spec-035-optimizer_hardening-0_0_10.md`, `spec-036-mutations-0_0_11.md`, `spec-038-form_mutations-0_0_12.md`, and `?? docs/builder/bld-slice-16-027-shipped_state_034_039.md` (its artifact, which appeared while this one was being written). Read for nothing, written never — and note that cohort K is discharging the same staleness class on the specs cohort H's finding 2 listed beside these four.
- **The concurrent `spec-028` session (1):** `?? docs/builder/bld-slice-3-028-spec_reconciliation.md`.

Everything already dirty at task start classifies as: **cohort I (`.py`, concurrent)** 32 paths under `django_strawberry_framework/`, 4 under `examples/fakeshop/apps/`, 2 under `examples/fakeshop/test_query/`, 19 under `tests/`; **cohort H's landed spec surface** `spec-033`, `spec-037`, `spec-040`, `appx/spec-001-…-rationale`, `appx/spec-004-…-rationale`, `appx/spec-009-…-rationale`, `appx/spec-015-…-rationale`; **cohort G / earlier** `spec-039`, `spec-041`, `spec-045`, `spec-046` and `docs/builder/bld-slice-{6…14}-027-*.md`; **the `spec-028` session** `spec-028-orders-0_0_8.md`, `appx/spec-028-orders-0_0_8-rationale.md`, `build-028-orders-0_0_8.md`, `bld-slice-{1,2}-028-*.md`; **cohort D** `spec-055-search_fields-0_1_2.md`; **Worker 0** `build-027-filters-0_0_8.md`. None was touched.

Byte counts, `HEAD` → working tree: `spec-029` 170,135 → 170,042 (−93); `spec-030` 137,934 → 138,023 (+89); `spec-031` 190,762 → 190,961 (+199); `spec-032` 190,040 → 187,312 (−2,728, almost all of it the deleted `Status:` build narration and the two falsified-mechanism bullets).

### Implementation notes

- **Every replacement asserted its occurrence count before any file was written.** The scripts run a dry pass over all four specs, collect every mismatch, and abort with nothing written if even one count is off. Every count matched on the first run — including the twelve board-move / definition-of-done sites, where two shapes ("to the Done column with the next available …" and "to Done with the next …") differ by three words and would otherwise be easy to conflate.
- **The corrected vocabulary was taken from the archive, not invented.** "Shipped in `0.0.X` (card …)" and "This spec is the final implementation record, not an open build plan" are `spec-028`'s; "stays unticked because the `Status:` line is the completion source of truth (the shipped-spec convention)" is `spec-045`'s; "move this card to the Done column, where it is `DONE-NNN-0.0.X` (the column-move pass assigns the next available id)" is `spec-027`'s. Three source records, zero coinages.
- **`## Current state` sections were treated as tense-fenced, and only their pointer ids retired.** Each of these specs' openers states that `## Current state` "describes the repo as of this spec's authoring, before the build", and `spec-031` / `spec-032` repeat it in the section's own first line ("A true description of the repo as of this writing"). The fence licenses the snapshot's tense; it does not license a card id that resolves to nothing. So the substance was left and the ids retired. The same reasoning kept the tense-marked "(the on-disk version is still `0.0.8` at spec-authoring time)" in three openers while deleting its untensed twin from three Decision justifications.
- **Two falsified mechanisms were measured against a `git show HEAD:` copy outside the repo, never the working tree**, because cohort I is rewriting `connection.py` and `types/finalizer.py` right now. Both `optimizer/extension.py::apply_connection_optimization` and `connection.py`'s `_check_n1` call were read from that snapshot.
- **Where a falsified mechanism carried live contract alongside it, the contract was kept and only the mechanism deleted.** `spec-032`'s Edge-cases bullet lost its "empty plan / never consults the sentinels" premise but kept all three lettered consequences (behaviour-only live assertions, no optimizer-dogfooding example converted, the relation-manager seeding that gives `033` a cooperation seam), because those are `032`'s own contracts and nothing measured falsifies them.
- **Line numbers in this artifact are pre-edit**, and are navigational only; every site is also identified by section and by the text quoted.

### Notes for Worker 3

No Worker 2 / Worker 3 cycle: the diff touches no `.py` file and changes no contract a test can pin. If one runs anyway, the four claims worth re-deriving mechanically are the board-id table (five `grep -c` invocations plus the card-title rows), the two falsified-mechanism measurements against a `git show HEAD:` snapshot, the census postcondition with its control, and the heading-md5 equality that proves no `### Decision N` anchor moved.

### Notes for Worker 1 / Worker 0 — findings left in place

Each is measured; each is outside this cohort's fence; none was repaired.

1. **`types/relay.py:680` carries the pre-ship card id `WIP-ALPHA-032-0.0.9`**, and `spec-032:135` quotes that docstring verbatim. The `.py` fix must land first or the spec's quotation breaks. This is the third `.py` site in this class, beside `types/finalizer.py:660` (`WIP-ALPHA-033-0.0.9`) which cohort H already reported; `examples/fakeshop/apps/kanban/models.py:512` is **not** a member (the id there is a format example illustrating the card-id shape). `.py` is cohort I's surface.
2. **None of these four specs has a rationale companion, and their deliberative layer is still inline.** `docs/SPECS/appx/` carries `spec-029-…-terms.csv`, `spec-030-…-terms.csv`, `spec-031-…-terms.csv` and `spec-032-…-terms.csv` and **no** `-rationale.md` for any of the four. All four carry a `Revision history (kept inline so the spec is self-contained)` block plus a `Justification:` / `Alternatives considered (and rejected):` pair under each Decision — the same condition `spec-027` was in before this cycle's Slice 1, and the same finding cohort H recorded for `spec-040`. Creating a companion is a structural decision outside this dispatch, so it was not created; carding it is Worker 0's. This is now a **five-spec** population with `spec-040`.
3. **`spec-032:43`'s Revision-1 bullet names the fakeshop products-activation card `TODO-BETA-051-0.1.5`, while seven other sites in the same spec name it `TODO-BETA-061-0.1.5`** — the board's spelling, at 10 hits. Left as a historical non-edit under the rule above, but it is a genuine two-spellings-of-one-card condition, and `051` today names a live different card (`TODO-ALPHA-051-0.0.15`). A card-`032` closeout that decides to rewrite revision-history pointers should take this site.
4. **`spec-032`'s `## Doc updates` block narrates its own build.** Beyond the sentences this cohort rewrote it still contains "The build extended the same additions to the **target** trees … recorded at final verification", "The wrap also re-sectioned the card's 11 Definition-of-done items … (recorded at final verification)", "update the 'Coming next' `0.0.9` line (the in-progress remainder shrinks to `033`)", and "(the latent break is now live)". That is the "a spec never narrates its own history" class rather than the shipped-state class, and repairing it is the rationale-extraction job finding 2 describes. Not touched, to keep this diff auditable.
5. **All four specs still spell their own path pre-archive** — `docs/spec-029-consumer_dx_cleanup-0_0_9.md` and siblings appear as **display text** in the board-move bullets, the doc-updates blocks and the definition-of-done items, while the files live at `docs/SPECS/`. The reference-style link definitions all resolve correctly, so nothing is broken; the visible text is stale. `spec-027`'s D11 flagged the identical class on its own card and this cycle's Slice 3 fixed it there. Out of this dispatch's scope (a path, not a shipping claim); a card-level closeout for these four should take it.
6. **`spec-030`'s `[goal]` link definition is orphaned at `HEAD`** (0 body uses in either tree). Pre-existing, and deleting a definition is outside this dispatch.
7. **`spec-029`'s parity table still lists `FieldSet` (`0.1.1`), `AggregateSet` (`0.1.3`) and the Postgres search filters (`0.1.2`) as planned**, which is correct — those releases are ahead of `0.0.14` — so the table's two falsified rows are the only two, and the sweep is complete for that table.

---

## Final verification (Worker 1)

Deferred to Worker 1's final pass per the dispatch: this artifact stays `Status: built`.

<!-- LINK DEFINITIONS -->

<!-- Root -->

[changelog]: ../../CHANGELOG.md
[kanban]: ../../KANBAN.md

<!-- docs/ -->

<!-- docs/SPECS/ -->

[spec-027]: ../SPECS/spec-027-filters-0_0_8.md
[spec-028]: ../SPECS/spec-028-orders-0_0_8.md
[spec-029]: ../SPECS/spec-029-consumer_dx_cleanup-0_0_9.md
[spec-030]: ../SPECS/spec-030-connection_field-0_0_9.md
[spec-031]: ../SPECS/spec-031-globalid_encoding-0_0_9.md
[spec-032]: ../SPECS/spec-032-full_relay-0_0_9.md
[spec-045]: ../SPECS/spec-045-visibility_boundary-0_0_14.md
[spec-055]: ../SPECS/spec-055-search_fields-0_1_2.md

<!-- docs/builder/ -->

[slice-13]: bld-slice-13-027-shipped_card_spec_staleness.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
