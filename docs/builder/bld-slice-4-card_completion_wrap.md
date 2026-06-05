# Build: Slice 4 — Card-completion wrap

Spec reference: `docs/spec-029-consumer_dx_cleanup-0_0_9.md` (Slice checklist "Card-completion wrap", lines 122-125; Decision 11 lines 498-514; Decision 12 lines 516-529; Doc updates "Card-completion wrap" bullet lines 638-639; DoD items 15-16 lines 700-703; Risks "stale spec filename" / "stale CHANGELOG heading" lines 646-647)
Status: planned

## Plan (Worker 1)

This is a **doc-only** slice — no source or test `.py` files are touched. It records the card as fully Done now that all three functional slices (1, 2, 3) are `final-accepted`. Decision 12's Slice-3 carve-off contingency does **not** apply (all three shipped), so the wrap records the card as fully Done with no carve-off.

### Headline finding — KANBAN.md is a GENERATED artifact, not the source of truth (escalation/discretion item E1)

The spec's "Card-completion wrap" sub-bullets, Doc-updates bullet, and DoD item 15 are written as if `KANBAN.md` is a hand-editable board: "move `WIP-ALPHA-029-0.0.9` to the Done column", "rewrite the card body's stale references". The repository's actual architecture contradicts this:

- **`KANBAN.md` AND `KANBAN.html` are both rendered outputs** of the fakeshop kanban app's database-backed GraphQL payload. `scripts/build_kanban_md.py` imports `configure_django` + `fetch_dashboard_data` from `scripts/build_kanban_html.py` and renders `KANBAN.md` from the same `allCards` GraphQL query that renders `KANBAN.html` (`scripts/build_kanban_html.py::fetch_dashboard_data` posts the query via Django's test `Client(HTTP_HOST="localhost")` against the in-process schema reading `examples/fakeshop/db.sqlite3`). This was shipped in `0.0.8` (CHANGELOG `[0.0.8]` "Kanban example app and dashboard publishing": "`KANBAN.md` and `KANBAN.html` are now generated from that database-backed GraphQL payload").
- **The card's own in-file TODO comment says exactly this.** `KANBAN.md` lines 148-154 (the `<!-- TODO(spec-029 wrap): -->` block inside the 029 card body):
  - "When all slices ship, update the kanban app source rows and regenerate this rendered board."
  - Pseudo: "move WIP-ALPHA-029-0.0.9 to DONE-NNN-0.0.9 / rewrite stale card-body spec and 0.0.8 changelog references **in the source data** / run `scripts/build_kanban_md.py` and `scripts/build_kanban_html.py`".
- **Git history confirms the workflow is edit-DB-then-regen**, not hand-edit: `15ce94c kanban: card-board edit (TODO-BETA renumbering) + KANBAN regen`, `0f224d0 ... + KANBAN regen`, `e516717 kanban: ... + flag edit-via-DB`.
- **The card source data is in `examples/fakeshop/db.sqlite3`** (committed, git-tracked). A card's column membership is its `status` field; the rendered id is computed by `scripts/build_kanban_md.py::card_key` as `{STATUS}{-MILESTONE?}-{NNN:03d}-{version}` — DONE cards drop the milestone (`if status != "DONE" and milestone: status_parts.append(milestone)`), so a card whose status flips `wip`→`done` renders automatically as the bare `DONE-029-0.0.9` with **no manual id string** anywhere.
- **`import_cards.py` is NOT the move tool**: it is an insert/create command ("status optional default `todo`; **not `done`**") that renumbers cards after an insertion point. Moving an existing card to Done is a status mutation on the existing row, not an import.

**The conflict:** The spec/DoD describe a direct `KANBAN.md` text edit; the repo says the canonical move is (a) mutate the card's status row in `examples/fakeshop/db.sqlite3` (`wip`→`done`), rewrite the stale `spec`/scope/DoD card-body strings in the same source data, then (b) regenerate both `KANBAN.md` and `KANBAN.html` via the two build scripts. The "Notes for Kanban maintenance" prose at `KANBAN.md` line 2838 ("Treat this file as a living operational board, not a spec") reads as hand-edit guidance but is itself **rendered static-column-doc text** (`COLUMN_DOC_KEYS` in the build script) and is contradicted by the same file's 029-card TODO comment and the git history.

**Why this is an escalation/discretion item, not a guess:** the regeneration path is non-obvious and carries real risk that a doc-only planner must not resolve unilaterally:
1. A direct hand-edit of `KANBAN.md` leaves **at least four rendered surfaces** mutually inconsistent and out of sync with the DB source: the `## Done` column (add the card body), the `## In progress` section (remove the 029 card body), the `## WIP / DONE spec map` table (line 101 → move the row), and the next regeneration would silently revert the hand-edit (the DB still says `wip`). It also leaves `KANBAN.html` stale.
2. The DB-edit + regen path requires mutating a committed SQLite DB and running two build scripts that POST GraphQL against the in-process fakeshop schema — which depends on the build's full test environment being healthy. Note the build plan's **recorded baseline exception** (build plan §"Baseline exception"): ~30 pre-existing `apps/kanban/` test failures rooted in a kanban `pre_save` glossary-link signal at `apps/kanban/signals.py`. A regen that drives the kanban GraphQL path could surface that same baseline condition; whether it blocks `build_kanban_md.py` must be verified, not assumed.
3. Worker scope: Worker 2 is the implementer and CAN edit `examples/fakeshop/db.sqlite3` + run scripts, but the spec never authorized a DB mutation or a regen for this slice — it only named `KANBAN.md`. Changing the implementation surface from "edit `KANBAN.md`" to "edit the DB + regenerate" is a contract change beyond a planner's discretion.

**Recommended resolution (for Worker 0 → maintainer):** escalate E1 to the maintainer before Worker 2 builds. The maintainer chooses one of:
- **Path A (canonical, preferred): edit-DB-then-regen.** Worker 2 (a) flips the 029 card row `status` `wip`→`done` in `examples/fakeshop/db.sqlite3` (the milestone drop is automatic in `card_key`), (b) rewrites the stale `spec-021-nullable_overrides-0_0_8.md` reference → `spec-029-consumer_dx_cleanup-0_0_9.md` and the three `## [0.0.8]` CHANGELOG-heading references → `[Unreleased]` in the card-body source data (Scope Slice-3 bullet + the three per-slice DoD bullets), then (c) runs `uv run python scripts/build_kanban_md.py` and `uv run python scripts/build_kanban_html.py`. This is what the card's own TODO comment prescribes and what `git log` shows for every prior board move. The regen also resolves the TODO comment itself (it is card-body source data and disappears on the next render once the wrap lands).
- **Path B (fallback): direct `KANBAN.md` (+ `KANBAN.html`) hand-edit.** Only if the maintainer judges the DB+regen path infeasible in this cycle (e.g. the kanban baseline failure blocks the build script). Then Worker 2 hand-edits `KANBAN.md` to move the card, rewrite the stale references, and update the spec-map table — AND the DB must be reconciled separately by the maintainer so the next regen does not revert the change. The `bld-final.md` Deferred-work catalog records the DB-source drift as maintainer follow-up.

**This plan documents both the move mechanics and the stale-ref rewrites at the logical/card level so the build is executable under whichever path the maintainer selects.** The verbatim spec sub-checks are about the *outcome* (card in Done, spec link correct, stale refs gone), which both paths satisfy; the path choice is the discretion/escalation item.

### DRY analysis

- **Existing patterns reused.** The card-move mechanic is the same one every prior Done card already went through (`DONE-001` … `DONE-028`); the rendered id convention (`DONE-NNN-version`, milestone dropped) is centralized in `scripts/build_kanban_md.py::card_key` — no new id-formatting logic is invented. The stale-ref rewrites reuse the already-correct `Spec:` line in the card header (`KANBAN.md` line 146 already points at `spec-029-consumer_dx_cleanup-0_0_9.md`); only the body's Slice-3 Scope/DoD prose carries the stale `spec-021` / `0.0.8` strings.
- **New helpers justified.** None. This slice writes no code and adds no helper; it mutates board data + regenerates (Path A) or hand-edits rendered markdown (Path B).
- **Duplication risk avoided.** The chief risk is the rendered/source split itself: a naive hand-edit duplicates the card-state in two places (the `KANBAN.md` text and the DB row) that then disagree. Path A avoids it by keeping the DB as the single source of truth and re-deriving `KANBAN.md`/`KANBAN.html` from it. The plan flags this explicitly rather than letting Worker 2 introduce a silent fork.

### Implementation steps

Line numbers are pin-at-write-time hints; verify against current `KANBAN.md` / DB before editing (another pass or a regen may have shifted them).

1. **Determine the Done id (pinned).** Highest existing DONE id is `DONE-028-0.0.8` (`KANBAN.md` line 1494, top of `## Done`). The card to move is `WIP-ALPHA-029-0.0.9`. Per the convention that the rendered id keeps the card's NNN and version and only swaps the status prefix (`card_key`: DONE drops the milestone), the next id is **`DONE-029-0.0.9`** — NOT a fresh sequential allocation. NNN (`029`) and version (`0.0.9`) are unchanged from the WIP card; only `WIP-ALPHA` → `DONE`. **This is pinned, not a discretion item.** (Sanity: 029 is the lowest-NNN `0.0.9` card and the only one of the four `0.0.9` WIP cards that is shipping now; 030/031/032 stay `WIP-ALPHA`.)

2. **Move the card to Done exactly once.** The card body currently lives under `## In progress` (header `KANBAN.md` line 134; card body `### [WIP-ALPHA-029-0.0.9 …]` at line 139 through the end of its `#### Card references` block at line 195, immediately before the `<a id="djangoconnectionfield">` anchor for the 030 card at line 197). The move:
   - **Remove** the 029 card body from the `## In progress` section in its entirety (anchor `<a id="djangotype_consumer_dx_cleanup_pass">` at line 138 through line 195). After removal, `## In progress` contains the "No active WIP cards." line (136) followed directly by the 030 card — the 029 card must NOT remain in In-progress.
   - **Add** it once to the top of the `## Done` column (the section is in descending id order; `DONE-028-0.0.8` is currently topmost at line 1494), as `### [DONE-029-0.0.9 — \`DjangoType\` consumer-DX cleanup pass](KANBAN.html#djangotype_consumer_dx_cleanup_pass)`. It must appear in `## Done` **exactly once** and nowhere else.
   - Update the card header `Status:` (line 144) from `Planned` to whatever the renderer emits for done cards (a `done`/`shipped`-shaped status), consistent with sibling Done cards.
   - Under Path A this is achieved by the DB status flip + regen (positioning, anchor, ordering, and the `KANBAN.html#…` self-link are all produced by the renderer). Under Path B it is a manual cut-from-In-progress / paste-into-Done.

3. **Update the `## WIP / DONE spec map` table.** Row at `KANBAN.md` line 101 currently reads `| \`WIP-ALPHA-029-0.0.9\` — \`DjangoType\` consumer-DX cleanup pass | [spec-029-consumer_dx_cleanup-0_0_9.md](docs/spec-029-consumer_dx_cleanup-0_0_9.md) |`. After the move the card id in this row becomes `DONE-029-0.0.9`, and the row sorts with the Done cards (above `DONE-028-0.0.8` at line 105, below the remaining WIP rows). The **spec link stays `docs/spec-029-consumer_dx_cleanup-0_0_9.md`** — note this spec is NOT moved to `docs/SPECS/` by this card (per BUILD.md "Spec stays at its working location"; archival is a future spec's opt-in Step-8 sweep, not this wrap). Under Path A the renderer rebuilds this table from the DB; under Path B it is a manual table edit.

4. **Confirm the card-body `Spec:` reference points at the canonical spec.** The card-header `Spec:` line (`KANBAN.md` line 146) ALREADY reads `[spec-029-consumer_dx_cleanup-0_0_9.md](docs/spec-029-consumer_dx_cleanup-0_0_9.md)` — correct, no change needed; confirm it survives the move unchanged. (The stale `spec-021` reference is NOT in this header line — it is in the body, step 5.)

5. **Rewrite the stale `spec-021-nullable_overrides-0_0_8.md` reference (card-body cleanup).** It appears twice in the 029 card body:
   - Slice-3 **Scope** bullet (`KANBAN.md` line 168): "**Requires spec**: `docs/spec-021-nullable_overrides-0_0_8.md` — open design decisions include …" → rewrite the filename to `docs/spec-029-consumer_dx_cleanup-0_0_9.md` (the canonical spec per Decision 1). The "open design decisions" prose may be left or trimmed at discretion (D2); the load-bearing fix is the filename.
   - Slice-3 **Definition of done** bullet (`KANBAN.md` line 174): "`docs/spec-021-nullable_overrides-0_0_8.md` written and reviewed" → rewrite the filename to `docs/spec-029-consumer_dx_cleanup-0_0_9.md`.

6. **Rewrite the stale `## [0.0.8]` CHANGELOG-heading references (card-body cleanup ONLY — NOT a CHANGELOG edit).** Three occurrences in the per-slice DoD bullets:
   - Slice-1 DoD (`KANBAN.md` line 172): "CHANGELOG entry under `## [0.0.8]` `### Changed`." → `[Unreleased]` `### Changed`.
   - Slice-2 DoD (`KANBAN.md` line 173): "CHANGELOG entry under `## [0.0.8]` `### Added`." → `[Unreleased]` `### Added`.
   - Slice-3 DoD (`KANBAN.md` line 174): "CHANGELOG entry under `## [0.0.8]` `### Added`." → `[Unreleased]` `### Added`.
   These edits change only the **card-body text describing where the CHANGELOG entries went**; per the spec Doc-updates bullet and Decision 11 ("the latter only as part of the card-body cleanup, NOT as a CHANGELOG edit"), **this slice must NOT touch `CHANGELOG.md` itself.** `CHANGELOG.md`'s `[Unreleased]` block already correctly carries the Slice 1/2/3 bullets (verified: `[Unreleased]` `### Changed` extensions migration + `### Added` inspect command + `### Added` nullable/required overrides), and the `## [0.0.8] - 2026-06-03` heading is a real shipped release heading that stays exactly as is.

7. **Hard constraint — NO version-file edits (Decision 11, DoD 16).** This slice must leave untouched: `pyproject.toml`, `django_strawberry_framework/__init__.py` `__version__`, `tests/base/test_init.py::test_version`, `uv.lock`. **No CHANGELOG release-heading promotion** — `[Unreleased]` stays `[Unreleased]`; the joint `0.0.9` cut (shared with `WIP-ALPHA-030/031/032-0.0.9`) owns the bump. The wrap moving the card to Done does NOT imply a version bump.

8. **Out-of-scope card-body strings (discretion D3).** The card body also carries incidental "0.0.8"-era wording NOT named by the spec's stale-reference items — e.g. line 188 "Smallest of the three `0.0.8` cards" and line 189 "landing the migration in 0.0.8". The spec scopes the rewrite to the `spec-021` filename and the `## [0.0.8]` CHANGELOG-heading references only. Leaving the incidental sizing/context prose as-is is acceptable; tidying it to `0.0.9` is at implementation discretion and is NOT required for the verbatim sub-checks or DoD. Worker 3's "no obsolete old-version wording" doc-sanity check applies to surfaces the slice *deliberately updated* — flag, don't fail, on incidental prose the slice chose not to rewrite.

### Test additions / updates

None. This is a doc-only slice with no `.py` files touched and no test surface. `scripts/review_inspect.py` is **not applicable** (no `.py` files touched) — recorded skip + reason below.

Behavioral guard for Worker 3 / final verification: the verbatim sub-checks are confirmable by `diff` against the spec source and by `grep` against the rendered `KANBAN.md` (card present once in Done, absent from In-progress, no surviving `spec-021-nullable_overrides-0_0_8.md` string, no `## [0.0.8]` CHANGELOG-heading reference in the 029 card body, `Spec:` link resolves to the existing `docs/spec-029-consumer_dx_cleanup-0_0_9.md`).

### Implementation discretion items

- **D1 (escalation, NOT pure discretion) — KANBAN.md edit path (Path A DB+regen vs Path B hand-edit).** See finding E1 above. This exceeds planner discretion because it changes the implementation surface the spec named; Worker 0 must escalate to the maintainer for the path choice before Worker 2 builds. Worker 1 records it here so the build is executable under either path and so the decision is explicit, not silently made by whichever worker touches the file.
- **D2 — Slice-3 Scope "open design decisions" prose.** When rewriting the `spec-021` filename in the Scope bullet (step 5), whether to also trim the now-resolved "open design decisions include dict-of-name vs tuple-set …" list (those decisions ARE resolved by spec Decisions 5/8/9/10) is at Worker 2's discretion. The load-bearing change is the filename; trimming the prose is optional tidy.
- **D3 — incidental `0.0.8` sizing/context prose.** See step 8. Leaving it or tidying it to `0.0.9` is at Worker 2's discretion; neither is required by the verbatim checks.

### review_inspect.py skip

`scripts/review_inspect.py` is **skipped — not applicable**: Slice 4 touches no `.py` files (it moves a KANBAN card and rewrites card-body doc text; under Path A it mutates a committed SQLite DB row + runs existing build scripts, neither of which is a reviewable `.py` source change introduced by this slice). The helper parses Python source as text/AST; there is no slice-authored Python to inspect. BUILD.md requires the helper only for `.py` files with review-worthy logic — none exist here. Worker 3's review for this slice runs the **"Documentation / release sanity"** check (the slice modifies KANBAN, a release/doc surface), NOT `review_inspect.py`.

### Documentation / release sanity readiness (so Worker 3's check passes)

This slice modifies KANBAN (a release/doc surface), so Worker 3 will run BUILD.md's "Documentation / release sanity" check. The plan is shaped so each bullet passes:
- **Card removed from old section + appears once in Done.** Steps 2-3: the 029 card body is deleted from `## In progress` and added exactly once to `## Done` (and the spec-map row moves with it). Confirmable by `grep -c "WIP-ALPHA-029"` → 0 in active board (only historical/cross-ref mentions in OTHER cards' prose may remain, e.g. dependency back-refs — those are legitimate references to the now-Done card and rewrite to `DONE-029-0.0.9` under Path A regen; under Path B confirm they are consistent) and `grep -c "DONE-029-0.0.9 — \`DjangoType\` consumer-DX cleanup pass"` heading → exactly 1 in `## Done`.
- **Spec link points at an existing file.** Step 4: card `Spec:` line resolves to `docs/spec-029-consumer_dx_cleanup-0_0_9.md`, which exists on disk (verified). The spec is NOT archived by this card.
- **Verbatim copies confirmable by `diff`.** The verbatim sub-checks below are copied character-for-character from spec lines 122-125.
- **No obsolete version wording in surfaces the slice updated.** Steps 5-6: stale `spec-021-nullable_overrides-0_0_8.md` and `## [0.0.8]` CHANGELOG-heading references are removed from the 029 card body. Incidental sizing prose (step 8) is out of the spec's named scope — flag, don't fail.
- **No CHANGELOG edit / no version-file edit.** Steps 6-7: `CHANGELOG.md` and all version files are untouched; `[Unreleased]` stays `[Unreleased]`. A CHANGELOG-sanity check keyed on "version line matches `pyproject.toml`" treats the unchanged version + `[Unreleased]` as expected, not drift (build-plan §"Version-bump owner").

### Spec slice checklist (verbatim)

Copied verbatim from `docs/spec-029-consumer_dx_cleanup-0_0_9.md` Slice checklist "Card-completion wrap" (lines 122-125):

- [ ] Card-completion wrap (lands when all three slices ship; NOT a code slice)
  - [ ] [`KANBAN.md`][kanban]: move [`WIP-ALPHA-029-0.0.9`][kanban] to the Done column with the next available `DONE-NNN-0.0.9` id; add / confirm the card body's `Spec:` reference points at [`docs/spec-029-consumer_dx_cleanup-0_0_9.md`][spec-029] (this document).
  - [ ] **No version-file edits in this card.** Leave `pyproject.toml`, [`__version__`][package-init], [`tests/base/test_init.py::test_version`][test-base-init], and `uv.lock` to the joint `0.0.9` cut per [Decision 11](#decision-11--version-bumps-are-owned-by-the-joint-009-cut).
  - [ ] If the schedule forces Slice 3 to defer, carve it off as its own follow-up card (`docs/spec-029b-nullable_overrides-0_0_9.md` or a renumbered successor) without disrupting Slices 1 + 2 per [Decision 12](#decision-12--slice-independence-and-the-slice-3-carve-off-contingency).

Note on the third sub-check: Slice 3 shipped and is `final-accepted`, so the carve-off contingency did NOT fire. At final verification this box is satisfied as "not triggered" (the schedule did not force a Slice-3 defer; all three slices shipped) and is ticked on that basis with a one-line note, NOT left silently unticked.

---

## Build report (Worker 2)

(to be filled by Worker 2)

---

## Review (Worker 3)

(to be filled by Worker 3)

---

## Final verification (Worker 1)

(to be filled by Worker 1 at final verification)
