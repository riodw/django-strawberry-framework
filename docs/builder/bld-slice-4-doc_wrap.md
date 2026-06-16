# Build: Slice 4 — doc updates + card-completion wrap

Spec reference: `docs/spec-035-optimizer_hardening-0_0_10.md` (Slice-4 checklist lines 57-58; Doc updates lines 383-398; DoD items 10-11 lines 455-458)
Status: final-accepted

> **CHANGELOG.md edit AUTHORIZED for this slice.** The maintainer explicitly authorized the `CHANGELOG.md` edit at build kickoff (2026-06-16; recorded in `build-035-optimizer_hardening-0_0_10.md` build-wide context flags). Slice 4 adds the **G1 + G2** bullets under `[Unreleased]` (`### Changed` / `### Fixed`), **no version-heading promotion**, **no G3 bullet** (G3 ships nothing). Per `AGENTS.md` #"Do not update CHANGELOG.md unless explicitly instructed", the spec alone cannot grant this; the maintainer's explicit kickoff instruction does.

## Plan (Worker 1)

### DB-verification findings (run before planning, per worker-0.md "Verify card/glossary references against the DB before editing")

Verified live against `examples/fakeshop/db.sqlite3` at HEAD `3c2b0427` (read-only; NO DB mutation performed):

- **Card 35 exists and matches the spec/plan.** `Card.objects.get(number=35)` → `status.key = "wip"`, rendered `card_id = "WIP-ALPHA-035-0.0.10"`, `milestone_id = 1` (Alpha), `title = "Optimizer robustness hardening (upstream-comparison guards)"`, `slug = optimizer_robustness_hardening_upstream_comparison_guards`. The `WIP-ALPHA-035-0.0.10` id is accurate. `glossary_links.count() = 0` (no `CardGlossaryTerm` rows yet — expected; `import_spec_terms` syncs them once the card is `done`).
- **A `SpecDoc` ALREADY EXISTS for card 35.** `SpecDoc.objects.get(card=card35)` → `name="spec-035-optimizer_hardening-0_0_10"`, `url="https://github.com/riodw/django-strawberry-framework/blob/main/docs/spec-035-optimizer_hardening-0_0_10.md"` (the **non-archive** `docs/` path). The spec/plan want the reference set to the `docs/SPECS/` archive path. **So Slice 4 UPDATES the existing `SpecDoc.url` — it does NOT create a new `SpecDoc`** (worker-0.md step 2's `.create(...)` would collide on the unique `name`). Set `sd.url = "https://github.com/riodw/django-strawberry-framework/blob/main/docs/SPECS/spec-035-optimizer_hardening-0_0_10.md"; sd.save()`.
- **The four GLOSSARY anchors the body edits touch all exist as `shipped` `GlossaryTerm` rows:** `djangooptimizerextension`, `only-projection`, `fk-id-elision`, `strictness-mode`. (Spec's body-edit targets confirmed present; no net-new heading needed — DoD item 1 / "no net-new public symbol".)
- **Terms-CSV present.** `docs/spec-035-optimizer_hardening-0_0_10-terms.csv` exists (23 rows). Every anchor in it already exists as a `GlossaryTerm` row (verified by iterating the CSV against `GlossaryTerm.objects.filter(anchor=...)`) — so card 35's own `import_spec_terms` sync will not fail on a missing-anchor precondition.
- **`import_spec_terms --check` is CURRENTLY FAILING — but the failure is CARD 34, NOT card 35.** Error: `GlossarySpecMention rows for docs/SPECS/spec-034-permissions-0_0_10.md do not match …-terms.csv: [] != [42 anchors]`. Root cause (verified): `DONE-034`'s `SpecDoc.url` resolves to the archive path `docs/SPECS/spec-034-permissions-0_0_10.md` (that file exists, so `import_spec_terms::_resolve_spec_path` returns it directly), but card 34's existing `GlossarySpecMention` rows are stored under the OLD `spec_path = docs/spec-034-permissions-0_0_10.md` — so `--check` finds zero mentions at the archive path. Card 34 has 42 `CardGlossaryTerm` rows already; only its `GlossarySpecMention` rows are mis-pathed. **This is a pre-existing DONE-034 data drift at HEAD, independent of card 35.** It is REPAIRED by the WRITE-mode `import_spec_terms` (step 5 below): `_sync_spec_mentions` keys on `plan.spec_path` (the archive path) and `update_or_create`s the mentions there for EVERY done card, so after step 5 card 34's archive-path mentions exist and step 8's `--check` passes. (The stale `docs/`-path mention rows are orphaned but harmless — `--check` only queries the archive path.) **Do NOT partial-fix card 34 by hand; the standard write pass reconciles it.** Recorded here so Worker 3 does not flag the current `--check` failure as a card-35 regression and so the final gate expects step 5 to clear it.
- **Card 35's archive-path `SpecDoc.url` resolves correctly even though the spec file STAYS at `docs/`.** Simulated `_resolve_spec_path("docs/SPECS/spec-035-optimizer_hardening-0_0_10.md")`: the archive path does not exist on disk → basename-glob fallback `docs/**/spec-035-optimizer_hardening-0_0_10.md` → single match `docs/spec-035-optimizer_hardening-0_0_10.md` → terms CSV resolved at `docs/spec-035-optimizer_hardening-0_0_10-terms.csv` (exists). So setting the `SpecDoc.url` to the archive path is safe; `import_spec_terms` finds the live terms CSV via the glob. **The spec file itself STAYS at `docs/spec-035-...md` this card** (AGENTS.md #26 / BUILD.md "Spec stays at its working location" — the `docs/SPECS/` move is the next spec author's Step-8 sweep, NOT this card; only the DB `SpecDoc.url` field points forward).
- **`docs/GLOSSARY.md` is ALREADY DRIFTED from the DB at HEAD (4 stale TODO-anchor comment blocks).** Read-only render to a temp file (`build_glossary_md.py --md /tmp/…`) then `diff` vs the committed file: the committed `docs/GLOSSARY.md` carries exactly 4 `<!-- TODO(spec-035 Slice 4): … -->` comment blocks (on the `DjangoOptimizerExtension`, `FK-id elision`, `only() projection`, `Strictness mode` entries) that do NOT exist in the DB `GlossaryTerm.body` rows. The diff is 22 lines, ALL deletions of those 4 TODO blocks, ZERO additions. So a fresh regenerate from the unchanged DB would *remove* the 4 TODO blocks. **Consequence for the byte-clean check:** the TODO blocks are this slice's own staged anchors (AGENTS.md #26 "removed in the same change that ships the slice"); they live only in the committed file, not the DB, so Worker 2 need NOT remove them from the DB (they aren't there) — they vanish naturally on the step-7 regenerate. Worker 2's only GLOSSARY DB work is to APPEND the real notes to the 4 `GlossaryTerm.body` rows. After step 7's regenerate, `docs/GLOSSARY.md` = TODO blocks gone + new notes added; step 8's byte-clean check (re-run regenerate, expect zero *further* diff) then holds because the DB and the freshly-written file agree. **No other GLOSSARY drift exists** (the only `>` additions in the regen diff were zero).

### Spec status-line re-verification (per worker-1.md, every spawn)

Read spec lines 1-9 (title / `Planned for 0.0.10` / Status / Owner / Predecessors). The Status line (line 5) reads "G1 shipped (commit `d1dea2fd`); G2 + the doc wrap remain; G3 deferred" — accurate for the start of Slice 4 (Slices 1-3 are `final-accepted`; the doc wrap is exactly what remains). No status-line edit needed this pass.

### DRY analysis

- **Existing patterns reused — the DB-backed generated-doc procedure.** No code helper; the reuse is the canonical DONE-card move procedure in `docs/builder/worker-0.md` "Closing out a kanban card" (DONE-card invariants; `import_spec_terms`; the byte-clean-regenerate verification) and the existing DONE-card render shape (DONE-034 in `KANBAN.md` shows `Spec:` at the `docs/SPECS/` archive path, `#### Definition of done` items rendered `- [x]` from `CardItem.is_complete`). Worker 2 mirrors that shape, NOT a hand-edit.
- **Single canonical wording, fanned out — drift avoidance across README / docs/README / GLOSSARY / CHANGELOG.** The one load-bearing phrase is the optimizer's **"what it will not touch"** note for G1 (consumer-evaluated querysets) and G2 (non-`QUERY` operations). To avoid four divergent paraphrases, anchor every surface to the spec's canonical wording (Decision 3 line 168 for G1; Decision 4 lines 187/196 for G2; Decision 5 lines 213-217 for the elision loaded-check). The GLOSSARY bodies carry the full sentence; README / docs/README carry a one-line compression of the SAME sentence; the CHANGELOG bullets restate the SAME behavior in past-tense release-note voice. Do not invent a second framing of "non-query operations keep select/prefetch but no column deferral" — reuse it verbatim-in-substance everywhere.
- **New helpers justified: none.** Doc-only slice; zero source/test code, zero new module, zero new GLOSSARY heading (refinements of shipped bodies only — DoD item 1).
- **Duplication risk avoided — the G3 wording trap.** The 4 stale GLOSSARY TODO anchors and the README / docs/README / KANBAN TODO anchors were authored BEFORE Revision 3 deferred G3, so they all mention "G3 fragment-narrowing behavior" / "narrows fragment planning by type condition". The naive implementation would carry that G3 prose into the shipped notes. **G3 ships NOTHING this card.** The GLOSSARY `Strictness mode` entry gets only a one-line *deferral pointer* (to the abstract-return optimizer entry card / `BACKLOG.md` `polymorphic_interface_connections`); README / docs/README mention ONLY G1 + G2 ("evaluated querysets, non-query operations"), NOT narrowing. The CHANGELOG gets NO G3 bullet. This is the single biggest correctness pin of the slice.

### Implementation steps (Worker 2)

> Ordered. DB-first-then-regenerate for GLOSSARY + KANBAN; hand-edits for README / docs/README / CHANGELOG. Run DB edits via `uv run python examples/fakeshop/manage.py shell`; regenerate from the repo root. Line numbers are pin-at-write-time hints — re-verify against current source before editing.

**A. GLOSSARY (DB-backed — edit `GlossaryTerm.body` via ORM, then regenerate)**

1. **Append the G1 + G2 notes to the 4 `GlossaryTerm.body` rows via the ORM** (`manage.py shell`; `t = GlossaryTerm.objects.get(anchor=…); t.body = t.body + "\n\n" + <new text>; t.save()`). The committed-file TODO blocks are NOT in the DB body (verified) — do NOT try to strip them from the DB; they disappear on the step-7 regenerate. Append (preserving each body's existing trailing structure; the `**See also:**` line is part of the rendered entry, NOT the `body` field — confirm whether `See also` is in `body` or rendered separately before appending, and append BEFORE any in-body See-also if present):
   - **`djangooptimizerextension`** — add G1 + G2 to the shipped-behavior list and a one-line "what the optimizer will not touch" note (spec Doc-updates line 388; ground in Decision 3 line 168 + Decision 4 lines 187/196):
     - G1: the optimizer passes a consumer-evaluated root queryset through unchanged — if the resolver already evaluated it (`len(qs)`, `bool(qs)`, slicing), the `_optimize` middleware returns it as-is rather than re-executing it with an `.only()` / `select_related` clone (shipped `0.0.10`).
     - G2: for non-`QUERY` operations (mutation / subscription) the optimizer suppresses all column projection at plan-build time — `select_related` / `prefetch_related` still apply, but no `.only(...)` column deferral is baked into the returned queryset (shipped `0.0.10`).
     - "What the optimizer will not touch": a queryset the consumer already evaluated, and column projection on non-`QUERY` operations.
   - **`only-projection`** — note the G2 operation-type gate (spec Doc-updates line 389; Decision 4 lines 187/196/200): `.only(...)` is applied for `QUERY` operations only; mutation / subscription querysets keep `select_related` / `prefetch_related` but carry no column deferral (so a mutation-returned queryset never carries a selection-shaped deferred-field set; shipped `0.0.10`).
   - **`fk-id-elision`** — one-line note (spec Doc-updates line 391; Decision 5 lines 213-219): FK-id elision stays enabled under non-`QUERY` operations, **with a consumer-`.only()` loaded-check** — the elision stub verifies the FK column is loaded on the parent row and falls back loudly (strictness-visible) when a consumer projection deferred it, rather than a silent per-row lazy load (shipped `0.0.10`).
   - **`strictness-mode`** — a one-line **G3 deferral pointer ONLY, no behavior note** (spec Doc-updates line 390; DoD item 10): interface / union sibling-concrete-type fragment narrowing (the would-be G3 strictness interaction) is **deferred** to the abstract-return optimizer entry card (the `BACKLOG.md` `polymorphic_interface_connections` work); strictness behavior is unchanged by this card. Do NOT state any narrowing behavior as shipped.
2. **Reconcile any existing GLOSSARY drift before regenerating** (worker-0.md step 1 sub-bullet): none beyond the 4 TODO blocks, which are file-only (not in the DB) and intentionally removed by the regenerate. No other `GlossaryTerm.body` is hand-edited in the committed file vs the DB (verified: the only regen diff was the 4 TODO deletions). No net-new glossary term to seed (all 23 CSV anchors already exist).

**B. KANBAN card-completion wrap (DB-backed — move WIP → Done, then regenerate)**

3. **Update the existing `SpecDoc.url` to the archive path** (do NOT `.create()` — a `SpecDoc` already exists; see findings): `sd = SpecDoc.objects.get(card=card35); sd.url = "https://github.com/riodw/django-strawberry-framework/blob/main/docs/SPECS/spec-035-optimizer_hardening-0_0_10.md"; sd.save()`. The `name` stays `spec-035-optimizer_hardening-0_0_10`. (worker-0.md step 2, adapted: the SpecDoc exists, so this is an update not a create.)
4. **Bootstrap ≥1 glossary link** so the done-save invariant passes (worker-0.md step 3): create one `CardGlossaryTerm` for card 35 against a term in the CSV (e.g. `djangooptimizerextension`) — `import_spec_terms` (step 6) reconciles the full set. (Required because the `done`-status pre_save validation in `apps/kanban/signals.py` demands both a linked `SpecDoc` AND ≥1 `glossary_links`.)
5. **Flip status to done via ORM `.save()`** (worker-0.md step 4): `card35.status = Status.objects.get(key="done"); card35.save()`. `.save()` fires the pre_save validation (SpecDoc + glossary link present) and sets `milestone_id`; the rendered id auto-becomes `DONE-035-0.0.10` (done cards drop the `ALPHA` prefix). `milestone_id` stays `1` (Alpha) — same as DONE-034. **Do NOT touch `planning_state`** (the "Status: …" header line): the spec's Slice-4 scope does not name it, the worker-0 procedure does not change it, and DONE-034 itself left `planning_state = "In progress"` — leave card 35's `planning_state = "Needs spec"` as-is (out of slice scope; changing it would be unrequested drift). If Worker 2 judges it visually wrong, flag for Worker 1, do not change unilaterally.
6. **Sync the full glossary-link set across ALL done cards** (worker-0.md step 5): `uv run python examples/fakeshop/manage.py import_spec_terms`. This (a) creates card 35's `CardGlossaryTerm` + `GlossarySpecMention` rows from its terms CSV, AND (b) **repairs the pre-existing DONE-034 mention drift** by re-creating card 34's `GlossarySpecMention` rows under the archive `spec_path` (see findings). Expect the success line `Imported glossary terms for N done card(s).`
7. **Fix card-body content the spec wrap names, and tick the SHIPPED DoD items only** (worker-0.md step 6) — edit `CardItem.text` / `CardItem.is_complete` via ORM:
   - **DoD `CardItem.is_complete` (section "Definition of done", 8 items, orders 0-7 — all currently `False`):** tick `is_complete = True` for the **shipped** items ONLY — order 0 (spec file), order 1 (G1), order 2 (G2 plan shape), order 3 (G2 elision decision), order 6 (no B1-B8 regression), order 7 (optimizer docs note). **Leave orders 4 and 5 `is_complete = False`** — these are the **G3** DoD items ("union and interface fragment tests …", "Strictness `warn` no longer fires … narrowed sibling fragments"), which spec DoD items 6-8 (lines 443-449) explicitly DEFER and state are "NOT part of this card's completion". Ticking them would falsely claim G3 shipped. This is the deliberate departure from the generic worker-0 "mark every DoD complete" line: the spec's deferral is authoritative for this slice. Record the two un-ticked items as the G3 deferral (see step 8).
   - **G3-deferral follow-up reference (spec Slice-4 line 58 / DoD item 10 "records the G3 deferral as a follow-up card reference"):** add the deferral to the card so the rendered Done card records it — preferred site: edit the two un-ticked G3 DoD `CardItem.text` (orders 4, 5) to prefix `**[DEFERRED to the abstract-return optimizer entry card — BACKLOG `polymorphic_interface_connections`; see spec-035 Decision 6/7 / Revision 3]** ` before the existing text, OR add a single `CardItem` in an appropriate section recording the G3 deferral and the follow-up card. Worker 2 picks one shape (see Implementation discretion items); keep it faithful to the spec's deferral wording (Revision 3, lines 56 / 416).
   - **Stale card-body refs:** there is an embedded `<!-- TODO(spec-035 Slice 4): completion wrap is DB/re-render owned … -->` comment rendered inside the WIP card body in `KANBAN.md` (it mentions "after G2/G3/docs ship"). Locate its backing `CardItem` (a body/`Other`-section item) and remove/clear it — it is this slice's own staged anchor (AGENTS.md #26 "removed in the same change that ships the slice"). Do not carry its G3 framing forward.
   - Keep edits to what the spec authorizes; leave unrelated card-body prose alone.
8. **Regenerate all three generated docs** from the repo root (worker-0.md step 7): `uv run python scripts/build_kanban_md.py`, `uv run python scripts/build_kanban_html.py`, `uv run python scripts/build_glossary_md.py`.

**C. Hand-edited docs (NOT DB-backed)**

9. **`README.md`** — replace the staged TODO anchor (`<!-- TODO(spec-035 Slice 4): add the optimizer robustness status note here … -->`, currently around lines 52-55) with a short robustness note in the Status section: the package's optimizer now guards consumer-evaluated querysets (G1) and non-query operations (G2) — NO mention of fragment narrowing / G3 (spec Doc-updates line 394; DoD item 10). G1 + G2 only. Follow the reference-style markdown link convention (any cross-file link added goes in the bottom block under the correct group header; existing `[glossary]` / `[changelog]` defs already present). No new cross-file link is strictly required.
10. **`docs/README.md`** — two edits (spec Doc-updates line 393; DoD item 10):
    - Replace the staged TODO anchor (`<!-- TODO(spec-035 Slice 4): update the optimizer overview when G2/G3 ship … -->`, currently around lines 124-127) by adding the "what the optimizer will not touch" sentence (evaluated querysets, non-query operations — G1 + G2 ONLY, no narrowing) to the optimizer paragraph (the `DjangoOptimizerExtension` bullet around line 106 / the optimizer overview).
    - Shrink the "Coming next" `0.0.10` line (currently line 130: `- `0.0.10` — optimizer robustness hardening (upstream-comparison guards; the `035` joint-cut sibling)`) to reflect the joint cut completing — drop the `035` remainder framing per the spec ("the 'Coming next' `0.0.10` line drops the `035` remainder as the joint cut completes"). Keep the line coherent; the `0.0.10` cut now contains both DONE-034 (permissions) and DONE-035 (this card).
    - Reference-style links preserved; defs in the bottom block under the right group header.
11. **`CHANGELOG.md` (AUTHORIZED — see banner)** — add the **G1 + G2** bullets under the existing `## [Unreleased]` heading (spec Doc-updates line 395; build-plan flag; DoD items 10-11):
    - The `[Unreleased]` block currently has only `### Added` (the DONE-034 cascade-permissions bullets). Add a `### Changed` and a `### Fixed` subsection under `[Unreleased]` (Keep-a-Changelog order: Added / Changed / Fixed). G2 (operation-type gating of `.only()` — a behavior change to what the optimizer projects) → `### Changed`. G1 (evaluated-queryset re-execution prevented — a defect-class fix) → `### Fixed`. (If Worker 2 judges G1 better as `### Changed` too, see discretion items — but `### Fixed` matches the spec's "evaluated-queryset *guard*" framing and the audit's "doubled query invisible to the consumer" defect description.)
    - **NO version-heading promotion** — leave `## [Unreleased]`; do NOT add a `## [0.0.10]` heading (the joint `0.0.10` cut owns the bump — Decision 9 / DoD item 11). **NO G3 bullet** (G3 ships nothing — DoD item 10).
    - Wording: past-tense release voice restating the SAME behavior as the GLOSSARY notes (DRY — do not invent a new framing). Use the existing CHANGELOG link-reference style (`[glossary-…]` defs already present at the bottom; reuse `[glossary-djangooptimizerextension]`, `[glossary-only-projection]`, `[glossary-fk-id-elision]`, `[glossary-strictness-mode]` if linking; add any missing def to the bottom block under the correct group).
12. **`TODAY.md` — NO EDIT** (spec Doc-updates line 396, deliberate omission): `TODAY.md` is products-capability-centric; G1/G2 are internal optimizer robustness with no products-visible surface change. Recorded here so Worker 3's "Documentation / release sanity" check does NOT flag the missing `TODAY.md` edit as an oversight — the omission is per spec.

**D. Explicit no-edit guards (Decision 9 / DoD item 11)**

13. **No version-file edits:** `pyproject.toml`, `django_strawberry_framework/__init__.py` (`__version__`), `tests/base/test_init.py` (`test_version`), `uv.lock` — all UNCHANGED. The on-disk `__version__` stays `0.0.9`; the joint `0.0.10` cut owns the bump. **No `__all__` / public-symbol change** (no new public symbol this card). **No source/test code edits** (Slices 1-3 already shipped all code; Slice 4 is doc + DB only).

### Test additions / updates

Doc-only slice — **no code tests** (no source change). Instead, pin the **verification gates** Worker 3 / Worker 1 run (these are the slice's acceptance proof; they are also the spec/DoD checks):

- **`uv run python examples/fakeshop/manage.py import_spec_terms --check` reports OK** for all done cards (after step 6's write pass — this both syncs card 35 AND clears the pre-existing DONE-034 drift). NOTE for Worker 3: this currently FAILS at HEAD on card 34 (pre-existing, see findings); step 6 must clear it; a still-failing `--check` after step 6 is a real blocker, but a failure attributable to card 34's pre-step-6 state is expected.
- **`git diff docs/GLOSSARY.md` is byte-clean after the DB edit + step-8 regenerate** (worker-0.md step 8): re-run `scripts/build_glossary_md.py` and confirm ZERO further diff — proves the DB body rows regenerate the committed glossary identically (the 4 stale TODO blocks are gone, the new G1/G2/Decision-5/G3-deferral notes are present, and nothing else drifts). A non-empty diff means a DB body still differs from the file.
- **`KANBAN.md` shows `DONE-035-0.0.10` in the Done section** (removed from "In progress"), `Spec:` pointing at `docs/SPECS/spec-035-optimizer_hardening-0_0_10.md`, the 6 shipped DoD items rendered `- [x]`, the 2 G3 DoD items rendered `- [ ]` with the deferral text, and the G3 follow-up reference recorded. `KANBAN.html` regenerated to match.
- **`uv run python examples/fakeshop/manage.py check` passes** (Django system checks; worker-0.md step 8).
- **Reference-style markdown link disk-exists checks** (START.md "run a disk-exists check on each rewritten path"; Worker 3 "Documentation / release sanity"): every cross-file link added/moved in `README.md` / `docs/README.md` / `CHANGELOG.md` / the KANBAN `Spec:` reference points at an existing file or a documented future file. The KANBAN `Spec:` archive path `docs/SPECS/spec-035-optimizer_hardening-0_0_10.md` is the EVENTUAL home (the file still lives at `docs/spec-035-…md` this card) — this is the documented-future-file case (the next spec author's Step-8 sweep moves it); Worker 3 should treat the archive path as a documented forward reference, NOT a broken link.
- **CHANGELOG sanity** (Worker 3 "CHANGELOG sanity"): the `[Unreleased]` G1 + G2 bullets sit under `### Fixed` / `### Changed`; NO `## [0.0.10]` heading promoted; NO G3 bullet; wording matches the GLOSSARY notes' behavior; version unchanged (on-disk `0.0.9`).
- **Whole working tree:** `git status --short` after the slice shows ONLY the intended surfaces dirty — `docs/GLOSSARY.md`, `KANBAN.md`, `KANBAN.html`, `examples/fakeshop/db.sqlite3`, `README.md`, `docs/README.md`, `CHANGELOG.md` (plus this `bld-*.md` artifact). No source/test/version files.

### Implementation discretion items

Worker 1 has assessed these and they are genuinely at Worker 2's discretion:

- **CHANGELOG G1 subsection placement (`### Fixed` vs `### Changed`).** Plan prefers G1 → `### Fixed` (it closes a doubled-query defect) and G2 → `### Changed` (it changes what the optimizer projects). If Worker 2 reads G1 as a behavior change rather than a bug fix, `### Changed` for both is acceptable — but keep G2 in `### Changed` regardless, and do not split a single guard across two headings.
- **G3-deferral recording shape on the card.** Either (a) prefix the two un-ticked G3 DoD `CardItem.text` (orders 4, 5) with a `**[DEFERRED …]**` marker, or (b) add one dedicated `CardItem` recording the G3 deferral + follow-up card. Both satisfy "records the G3 deferral as a follow-up card reference"; pick the one that renders cleanest in `KANBAN.md`.
- **Exact prose of the GLOSSARY appends / README notes**, within the substance pinned in step 1 / steps 9-11 and grounded in the cited Decisions. Match the surrounding entry's voice; keep G1+G2-only (never G3-as-shipped).
- **Whether each GLOSSARY G1/G2 note is a new list bullet vs a trailing sentence** in the body — match the existing body structure of each entry.

### Spec slice checklist (verbatim)

From the spec's `## Slice checklist`, Slice 4 (lines 57-58), copied verbatim:

- [x] Slice 4: doc updates + card-completion wrap (per [Doc updates](#doc-updates))
  - [x] [`docs/GLOSSARY.md`][glossary] (append the **shipped** guards G1 + G2 to [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] / [`only()` projection][glossary-only-projection] bodies — no new heading; **no G3 note**, since G3 ships no behavior here — the [Strictness mode][glossary-strictness-mode] body instead gets the G3-deferral pointer to the follow-up card), [`docs/README.md`][docs-readme] (the optimizer surface line + the "Coming next" `0.0.10` line shrinks as the joint cut completes), [`README.md`][readme] (the optimizer "what it will not touch" note, G1 + G2 only), [`CHANGELOG.md`][changelog] (only if the Slice 4 maintainer prompt explicitly requests it — the spec does not grant the permission), [`KANBAN.md`][kanban] (card → Done via the kanban DB + re-render; the G3 deferral recorded as a follow-up card reference). No version-file edits ([Decision 9](#decision-9--version-bumps-are-owned-by-the-joint-0010-cut)).

> Worker 2 ticks each box as the contract lands; Worker 1 audits at final verification. NOTE: the verbatim sub-bullet's "[`CHANGELOG.md`][changelog] (only if the Slice 4 maintainer prompt explicitly requests it)" condition IS satisfied — the maintainer authorized the CHANGELOG edit at kickoff (banner above), so the CHANGELOG edit is in-scope for this slice.

Both boxes ticked: every named surface landed (GLOSSARY G1+G2 appends + Strictness G3-deferral pointer; docs/README optimizer-line note + shrunk Coming-next `0.0.10` line; README G1+G2-only robustness note; CHANGELOG G1+G2 bullets under `[Unreleased]`; KANBAN card → `DONE-035-0.0.10` via DB + re-render with the G3 deferral recorded). No version-file edits.

---

## Build report (Worker 2)

### Files touched

Slice-intended (all confirmed via `git status --short`):

- `examples/fakeshop/db.sqlite3` — all DB-backed edits (the generated docs are rendered from this; never hand-edited):
  - `apps.glossary.GlossaryTerm.body` appended (4 rows, ORM `.save()`): `djangooptimizerextension` (G1 + G2 shipped-behavior bullets + "what the optimizer will not touch" note), `only-projection` (G2 operation-type gate sentence), `fk-id-elision` (Decision-5 loaded-check sentence), `strictness-mode` (G3-deferral pointer only, no behavior). Each appended BEFORE the in-body `**See also:**` line (the See-also is part of `body`, confirmed against the renderer `scripts/build_glossary_md.py::render_term`).
  - `apps.kanban.SpecDoc.url` UPDATED (not created — a row already existed; name is unique) to the `docs/SPECS/` archive path.
  - One `CardGlossaryTerm` bootstrapped (card 35 → `djangooptimizerextension`) to satisfy the done-save invariant; `import_spec_terms` then synced the full 23-term set.
  - `Card(number=35).status` → `done` via ORM `.save()` (rendered id auto-becomes `DONE-035-0.0.10`; `milestone_id=1` Alpha; `planning_state` left `needs_spec` untouched per plan).
  - DoD `CardItem`s: orders 0,1,2,3,6,7 `is_complete=True` (shipped); orders 4,5 left `is_complete=False` and prefixed with a `**[DEFERRED …]**` marker recording the G3 follow-up reference.
  - `import_spec_terms` (write) created card-35 `CardGlossaryTerm` + `GlossarySpecMention` rows AND repaired the pre-existing DONE-034 mention drift (re-created card-34 mentions under the archive `spec_path`).
- `docs/GLOSSARY.md` — regenerated from the DB (`scripts/build_glossary_md.py`). Diff = 4 stale TODO-block removals + the 4 body appends; byte-clean on re-regenerate.
- `KANBAN.md` — regenerated (`scripts/build_kanban_md.py`): `DONE-035-0.0.10` now in the Done summary table + as a full Done card (Spec at archive path; 6 DoD `- [x]`, 2 G3 DoD `- [ ]` with the deferral text); WIP entry + the file-only TODO comment gone; byte-clean on re-regenerate.
- `KANBAN.html` — regenerated (`scripts/build_kanban_html.py`) to match.
- `README.md` — Status section: replaced the staged G3-mentioning TODO anchor with a G1+G2-only "two robustness guards" note ("No public API change").
- `docs/README.md` — two edits: (1) appended the G1+G2 "what the optimizer will not touch" sentence to the `DjangoOptimizerExtension` bullet; (2) removed the staged TODO anchor and shrank the "Coming next" `0.0.10` line (dropped the `035` remainder framing, now reads "cascade-permissions subsystem and optimizer robustness hardening").
- `CHANGELOG.md` — added `### Changed` (G2 operation-type gating + Decision-5 elision loaded-check) and `### Fixed` (G1 evaluated-queryset guard) under `[Unreleased]`; no `## [0.0.10]` heading promoted; no G3 bullet; added 3 missing `[glossary-*]` defs alphabetically in the `docs/` link-def group.
- `docs/builder/bld-slice-4-doc_wrap.md` — this report; both verbatim checklist boxes ticked.

Prior-slice / expected dirty (NOT touched this pass, per the dispatch): `django_strawberry_framework/optimizer/walker.py`, `django_strawberry_framework/types/resolvers.py`, `tests/optimizer/test_extension.py`, `tests/optimizer/test_walker.py`, `tests/types/test_resolvers.py` (Slice 2), `docs/spec-035-optimizer_hardening-0_0_10.md` (spec edit), and the prior `bld-slice-1/2/3-*.md` + `build-035-*.md` artifacts.

### Tests added or updated

None — doc-only slice, no source change. Acceptance is the verification-gate suite below (the spec/DoD checks), not new code tests.

### Validation run

- `uv run python scripts/build_glossary_md.py` / `scripts/build_kanban_md.py` / `scripts/build_kanban_html.py` — all ran clean (84 terms / 58 cards + 15 board docs / 59 cards regenerated).
- `uv run python examples/fakeshop/manage.py import_spec_terms` (write) — `Imported glossary terms for 35 done card(s).`
- `uv run python examples/fakeshop/manage.py import_spec_terms --check` — `OK: 35 done cards have glossary links.` (FAILED at HEAD on card 34 pre-edit, as the plan predicted; the write pass repaired it.)
- `git diff docs/GLOSSARY.md` — reflects ONLY the 4 TODO-block removals + the 4 intended body appends (G1/G2/Decision-5/G3-deferral). **Byte-clean confirmed:** a second regenerate produced 0 further diff (DB regenerates the committed glossary identically). KANBAN.md likewise byte-clean (0 diff on re-regenerate).
- `uv run python examples/fakeshop/manage.py check` — `System check identified no issues (0 silenced).`
- `uv run ruff format .` — `267 files left unchanged` (no `.py` edits; the COM812-vs-formatter warning is the repo's standing config note, not an error).
- `uv run ruff check --fix .` — `All checks passed!`
- `git status --short` — modified: `CHANGELOG.md`, `KANBAN.html`, `KANBAN.md`, `README.md`, `docs/GLOSSARY.md`, `docs/README.md`, `examples/fakeshop/db.sqlite3` (slice-intended) + the prior-slice source/tests/spec and `bld-*`/`build-*` artifacts (expected, not touched this pass). **No unrelated tool churn to revert** (ruff changed nothing).
- Version-file guard: `pyproject.toml`, `django_strawberry_framework/__init__.py`, `tests/base/test_init.py`, `uv.lock` all clean; on-disk `__version__` still `0.0.9`.

### Implementation notes

- **G3 ships nothing on every surface.** The 4 stale GLOSSARY TODO blocks, the README/docs-README TODO anchors, and the KANBAN TODO comment were all authored pre-Revision-3 and mention G3 fragment narrowing; every replacement carries G1+G2 only. The `strictness-mode` body gets a pure deferral pointer (no behavior). The 2 G3 DoD items (orders 4,5) stay unticked.
- **The KANBAN TODO comment (KANBAN.md old lines 151-155) is a file-only hand-edit anchor, NOT a DB row.** Confirmed by a baseline regenerate-to-temp diff: it vanishes on re-render exactly like the 4 GLOSSARY TODO blocks. No DB edit was needed to clear it; the step-8 regenerate dropped it.
- **G3-deferral recording shape (discretion item):** chose shape (a) — prefixed the two un-ticked G3 DoD `CardItem.text` (orders 4,5) with `**[DEFERRED to the abstract-return optimizer entry card — BACKLOG `polymorphic_interface_connections`; see spec-035 Decision 6/7 / Revision 3]** `. Renders cleanly as the `- [ ]` items in the Done card and keeps the follow-up reference adjacent to the deferred contract.
- **CHANGELOG G1 placement (discretion item):** G1 → `### Fixed` (closes a doubled-query defect invisible to the consumer), G2 → `### Changed` (changes what the optimizer projects). Matched the spec's "evaluated-queryset *guard*" + audit "doubled query invisible" framing.
- **`SpecDoc` UPDATE not create:** a row already existed (non-archive `docs/` url); `.create()` would have collided on the unique `name`. Set `sd.url` to the archive path + `.save()`, leaving `name` unchanged.
- **`planning_state` left as `needs_spec`** (rendered "Status: Needs spec" header) — out of slice scope per plan; DONE-034 itself renders a stale "Status: In progress", so this matches existing DONE-card precedent (see Notes for Worker 1).
- **`import_spec_terms` side effect — DONE-034 drift repair.** The write pass re-created card-34's `GlossarySpecMention` rows under the archive `spec_path`, clearing the pre-existing `--check` failure that was unrelated to card 35. The GLOSSARY spec-mention total rose 851→916 (card-35 + card-34-repair mention rows); these feed the cross-reference tables, not the term bodies, and the byte-clean re-regenerate confirms zero term-body drift.

### Notes for Worker 3

- **Byte-clean proof:** `git diff docs/GLOSSARY.md` shows only the intended changes; running `scripts/build_glossary_md.py` a second time yields 0 further diff (the committed file is DB-faithful). Same for `KANBAN.md`. This is the worker-0.md step-8 verification — the DB and the rendered files agree.
- **DoD-tick rationale:** 6 ticked (orders 0,1,2,3,6,7 — the shipped G1+G2+wrap+no-regression items); 2 left unticked (orders 4,5 — the G3 items spec DoD items 6-8 / lines 443-449 explicitly defer and state are "NOT part of this card's completion"). Ticking them would falsely claim G3 shipped. This is the deliberate departure from the generic worker-0 "mark every DoD complete" line.
- The current `import_spec_terms --check` PASS is post-write-pass. At HEAD it failed on card 34 (pre-existing drift, recorded in the plan's DB-verification findings); the standard write pass cleared it — not a card-35 regression.
- The KANBAN `Spec:` archive path `docs/SPECS/spec-035-…md` is a documented FORWARD reference (the spec file still lives at `docs/spec-035-…md` this card; the `docs/SPECS/` move is the next spec author's NEXT.md Step-8 sweep). Treat it as a documented future file, not a broken link, per the plan + AGENTS.md #26.
- `TODAY.md` deliberately NOT edited (spec Doc-updates line 396) — G1/G2 are internal optimizer robustness with no products-visible surface change. Do not flag the missing `TODAY.md` edit.

### Notes for Worker 1 (spec reconciliation)

- **No spec gap surfaced.** The slice landed exactly per the plan and spec Doc-updates / DoD items 10-11. No spec edit needed.
- **Non-blocking observation (NOT a change request):** the rendered `DONE-035-0.0.10` card header still reads `- Status: Needs spec` because `planning_state` was left untouched (plan step 5 directed leaving it; out of slice scope). DONE-034 likewise renders `- Status: In progress`, so the stale `planning_state` on done cards is a pre-existing repo-wide pattern, not introduced by this slice. If the maintainer wants done cards to render a terminal `planning_state`, that is a separate cross-card cleanup (many DONE cards carry stale planning_state values) — recorded here as a possible follow-up, not actioned.

---

## Review (Worker 3)

Cumulative-diff filter applied: the Slice-4 surfaces under review are `CHANGELOG.md`, `KANBAN.md`, `KANBAN.html`, `README.md`, `docs/GLOSSARY.md`, `docs/README.md`, and `examples/fakeshop/db.sqlite3` (per `### Files touched`). The Slice-2 `walker.py` / `resolvers.py` / `tests/*` changes and the `docs/spec-035-…md` edit are prior-slice and out of Slice-4 scope (confirmed only for cross-doc consistency).

### High

None.

### Medium

None.

### Low

None.

### DRY findings

- **Single canonical wording, fanned out cleanly — no divergent paraphrase.** The G1 / G2 / Decision-5 / G3-deferral behavior statements are anchored to one substance and restated per surface at the right altitude: GLOSSARY bodies carry the full sentence (`djangooptimizerextension` G1+G2 bullets + the "what the optimizer will not touch" note; `only-projection` G2 gate; `fk-id-elision` Decision-5 loaded-check; `strictness-mode` G3-deferral pointer), `README.md` / `docs/README.md` carry a one-line compression of the SAME sentence, and the `CHANGELOG.md` `### Changed` / `### Fixed` bullets restate it in past-tense release voice. No second framing of "non-query operations keep select/prefetch but no column deferral" was invented anywhere — the four surfaces agree in substance, satisfying the plan's DRY-fan-out contract. No duplicated logic, repeated literal, or near-copy worth consolidating (doc-only slice).

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` is **empty** — `__all__` and the re-export list are unchanged. Matches DoD item 11 / Decision 9 ("adds no public symbol, so `__all__` is untouched"). No public-surface drift.

### CHANGELOG sanity

Read the `[Unreleased]` block end-to-end. Verdict: **PASS.**

- **G2 → `### Changed`** ("Operation-type gating of `.only()` (optimizer guard G2)") — correctly framed as a behavior change to what the optimizer projects; carries the Decision-5 elision loaded-check in the same bullet (a consumer-`.only()` loaded-check, loud strictness-visible fallback). Matches Decision 4 (lines 187/196/200) + Decision 5 (lines 213-217).
- **G1 → `### Fixed`** ("Evaluated-queryset guard (optimizer guard G1)") — correctly framed as a defect-class fix (doubled query invisible to the consumer); manager-coercion path still optimizes. Matches Decision 3 (line 168). The discretion-item choice (G1→Fixed, G2→Changed) is consistent with the spec's "evaluated-queryset *guard*" framing.
- **No version-heading promotion** — block stays `## [Unreleased]`; next heading is `## [0.0.9] - 2026-06-13`. No `## [0.0.10]`. The joint cut owns the bump (DoD item 11). PASS.
- **No G3 bullet** — confirmed by grep across the diff's added lines: zero G3/narrowing/fragment prose in CHANGELOG. PASS.
- **Version-line consistency** — on-disk `__version__ = "0.0.9"` (`__init__.py` line 29) and `version = "0.0.9"` (`pyproject.toml` line 4), both unchanged. No CHANGELOG version line claims `0.0.10`. PASS.
- **Keep-a-Changelog order** preserved (Added / Changed / Fixed). The 3 new `[glossary-*]` defs (`djangooptimizerextension`, `fk-id-elision`, `only-projection`) sit alphabetically in the `docs/` link-def group and resolve to real GLOSSARY headings; all 4 refs used in the new bullets (incl. `glossary-strictness-mode`) have defs present.

### Documentation / release sanity

Read every changed doc surface end-to-end. Verdict: **PASS.**

- **Version strings / shipped-planned statuses / card IDs.** `__version__` / `pyproject` both stay `0.0.9` (no bump this card — correct). The rendered Done card and the new GLOSSARY/README notes consistently attribute G1/G2 to `0.0.10`. The `apply_cascade_permissions` glossary row renders `shipped (0.0.10)`, consistent with the joint cut.
- **KANBAN card move.** `WIP-ALPHA-035` references: **zero** remaining. `DONE-035-0.0.10` appears **exactly twice** (Done summary table line 100; Done card heading line 1399) — removed from In-progress (the "In progress" section now reads "No active WIP cards") and present in Done exactly once as a card. Rendered `Spec:` points at `docs/SPECS/spec-035-optimizer_hardening-0_0_10.md`.
- **Markdown links — disk-exists checks.** The KANBAN `Spec:` archive path `docs/SPECS/spec-035-…md` does **not** exist on disk (the file correctly still lives at `docs/spec-035-…md`); this is the **documented-future-file** case (the next spec author's NEXT.md Step-8 sweep moves it) — treated as a documented forward reference, NOT a broken link, per AGENTS.md #26 + BUILD.md "Spec stays at its working location." The 3 new CHANGELOG glossary defs resolve to real GLOSSARY headings. README / docs-README added no net-new cross-file link.
- **Spec archival NOT performed (correct).** `docs/SPECS/spec-035-…md` is absent; only the `SpecDoc.url` DB field points forward to the archive home. The live spec file stays at `docs/spec-035-…md`.
- **No obsolete wording.** All four `<!-- TODO(spec-035 Slice 4) -->` GLOSSARY/README/docs-README anchors and the WIP-card-body TODO comment are gone (grep returns no matches). The `docs/README.md` "Coming next" `0.0.10` line was shrunk to drop the `035` remainder framing ("cascade-permissions subsystem and optimizer robustness hardening (upstream-comparison guards)") — coherent and reflects the joint cut completing. No "coming soon"/"planned"/old-version wording remains on the updated lines.
- **TODAY.md NOT edited** — per spec Doc-updates line 396 (deliberate omission; G1/G2 are internal optimizer robustness, no products-visible surface). Not flagged.

#### DB-backed byte-clean verification (independently re-run)

- Re-ran `scripts/build_glossary_md.py && build_kanban_md.py && build_kanban_html.py` from repo root, then a **second** time, hashing between runs. The three files are **byte-identical across the two regenerates** (md5 stable: `54bd485…` GLOSSARY, `c3bb14b…` KANBAN.md, `34869cf…` KANBAN.html) — proves the committed files are DB-faithful with zero drift (the worker-0 step-8 byte-clean pin holds). My no-op regenerate is not a change to revert.
- `uv run python examples/fakeshop/manage.py import_spec_terms --check` → `OK: 35 done cards have glossary links.` (exit 0). The pre-existing DONE-034 mention drift the plan flagged is cleared by Worker 2's write pass; no card-35 regression.
- `uv run python examples/fakeshop/manage.py check` → `System check identified no issues (0 silenced).` (exit 0).

#### No-G3-leakage check (the slice's biggest correctness pin)

Grepped the added lines across GLOSSARY / README / docs-README / CHANGELOG for `narrow|sibling|fragment|type.condition|polymorphic|interface…union`. **Exactly one** match: the `strictness-mode` GLOSSARY **deferral pointer** ("Interface / union sibling-concrete-type fragment narrowing (the would-be G3 strictness interaction) is **deferred** to the abstract-return optimizer entry card … strictness behavior is unchanged by that deferred work."). This is the single allowed G3 mention (spec Doc-updates line 390) and explicitly states G3 is deferred / unchanged — no G3 behavior claimed as shipped. No G3 prose leaked into any other surface; CHANGELOG carries no G3 bullet. PASS.

#### DoD-tick verdict

Read the rendered Done card's `#### Definition of done` (8 items). **6 ticked `- [x]`**: spec file added, G1 early-return + tests, G2 query/mutation plan coexistence, G2 FK-id-elision decision pinned, no-B1-B8-regression, optimizer-docs "what it will not touch" note. **2 unticked `- [ ]`** — the two G3 items (union/interface fragment tests; strictness-`warn`-no-longer-fires-for-narrowed-sibling), each prefixed `**[DEFERRED to the abstract-return optimizer entry card — BACKLOG polymorphic_interface_connections; see spec-035 Decision 6/7 / Revision 3]**`. This matches the spec's deferral exactly (DoD items 6-8 / lines 443-449: "NOT part of this card's completion") and records the G3 deferral as a follow-up card reference (Slice-4 line 58 / DoD item 10). Ticking them would falsely claim G3 shipped; leaving them unticked-with-marker is correct. PASS.

### What looks solid

- The DB-backed move is clean and reversible: `SpecDoc.url` UPDATE (not a colliding `.create()`), one bootstrap `CardGlossaryTerm` then full `import_spec_terms` sync, status flip via ORM `.save()` (rendered id auto-becomes `DONE-035-0.0.10`, drops the `ALPHA` prefix), all regenerated. Byte-stable on independent re-regenerate.
- The G3-deferral discipline is airtight across all five surfaces (4 docs + the card body): G3 ships nothing, every staged pre-Revision-3 TODO anchor that mentioned fragment narrowing was replaced with G1+G2-only prose, and the only G3 mention anywhere is the one allowed deferral pointer.
- CHANGELOG `### Changed`/`### Fixed` split is correct, version-promotion-free, G3-free, and DRY-consistent with the GLOSSARY bodies.
- Working tree shows only the intended Slice-4 surfaces dirty plus expected prior-slice/artifact files; no source/test/version-file drift introduced by Slice 4.

### Temp test verification

No temp tests created. **Static inspection helper (`scripts/review_inspect.py`) SKIPPED** — reason: Slice 4 is doc + DB only and adds **zero** `.py` logic (the only `.py` files in the working tree, `walker.py` / `resolvers.py` / `tests/*`, are prior-slice Slice-2 changes outside this review's scope; `git diff -- django_strawberry_framework/__init__.py` is empty). None of the BUILD.md "when to run the helper" triggers (new `.py` file, `optimizer/`/`types/` touch this slice, ≥30/≥50 new logic lines) fire for Slice 4. Per BUILD.md "Static inspection helper" rules the helper is correctly skipped for a no-`.py`-logic slice.

### Notes for Worker 1 (spec reconciliation)

- **No spec edit needed for Slice 4.** The slice landed exactly per the plan and spec Doc-updates / DoD items 10-11; the spec's own diff (5 ins / 4 del) is prior-slice/Worker-1 reconciliation work, out of Slice-4 scope.
- **Accepted cross-card pre-existing condition (NOT a Slice-4 finding) — flag for Worker 1 only:** the rendered `DONE-035-0.0.10` card header reads `- Status: Needs spec` because `planning_state` was deliberately left untouched (plan step 5; out of slice scope, changing it would be unrequested drift). This matches existing done-card precedent — DONE-034 renders `- Status: In progress`, and many DONE cards render `- Status: Planned` / `Needs spec` (verified repo-wide). Slice 4 did not introduce it. **No fix required this card** per the dispatch's "do NOT require a fix if it matches existing done-card precedent." If the maintainer ever wants done cards to render a terminal `planning_state`, that is a separate cross-card cleanup spanning many DONE cards — a possible future follow-up, not actioned here.

### Review outcome

`review-accepted` — zero High/Medium/Low findings. CHANGELOG sanity, documentation/release sanity, the byte-clean double-regenerate, `import_spec_terms --check` (OK, 35 cards), `manage.py check` (clean), the no-G3-leakage grep (one allowed deferral pointer only), and the 6-ticked/2-deferred DoD verdict all pass. Public surface unchanged. The `planning_state = "Needs spec"` rendering is an accepted cross-card pre-existing condition matching done-card precedent, flagged for Worker 1, not a finding.

---

## Final verification (Worker 1)

Read the full artifact (Plan / Build report / Review) and independently re-ran every acceptance gate. Diff scope confirmed: the Slice-4 surfaces (`docs/GLOSSARY.md`, `KANBAN.md`, `KANBAN.html`, `README.md`, `docs/README.md`, `CHANGELOG.md`, `examples/fakeshop/db.sqlite3`) plus the prior-slice Slice-2 source/tests (`optimizer/walker.py`, `types/resolvers.py`, `tests/optimizer/test_*.py`, `tests/types/test_resolvers.py`) and the prior Worker-1 spec edit (`docs/spec-035-…md`, 5 ins / 4 del) — the latter group confirmed out-of-Slice-4-scope only.

### Spec slice checklist box audit (Worker 1 is no longer the original ticker)

Both verbatim boxes were ticked `- [x]` by Worker 2. Audited each against the actual rendered files / working-tree diff — both genuinely landed; no box un-ticked:

- **Box 1 — `Slice 4: doc updates + card-completion wrap`.** LANDED. Every named surface edited and verified below.
- **Box 2 — the nested sub-bullet (GLOSSARY / docs/README / README / CHANGELOG / KANBAN, no version-file edits).** LANDED, each contract independently confirmed:
  - `docs/GLOSSARY.md`: `DjangoOptimizerExtension` body carries the G1 pass-through bullet (line 419), the G2 non-`QUERY` column-projection-suppression bullet (line 420), and the "What the optimizer will not touch" note (line 422); `only() projection` body carries the G2 operation-type-gate sentence (line 902); `FK-id elision` body carries the Decision-5 consumer-`.only()` loaded-check sentence (line 565); `Strictness mode` body carries ONLY the G3-deferral pointer (line 1295: "deferred … strictness behavior is unchanged") — no behavior note. No net-new heading.
  - `docs/README.md`: the `DjangoOptimizerExtension` overview bullet gained the "what the optimizer will not touch" sentence (G1 + G2 only, no narrowing); the "Coming next" `0.0.10` line shrank to drop the `035` remainder ("cascade-permissions subsystem and optimizer robustness hardening").
  - `README.md`: the Status section's staged G3-mentioning TODO anchor was replaced with a G1+G2-only "two robustness guards … No public API change" note.
  - `CHANGELOG.md`: `### Changed` (G2 operation-type gating + Decision-5 elision loaded-check) and `### Fixed` (G1 evaluated-queryset guard) under `[Unreleased]`; NO `## [0.0.10]` heading promoted; NO G3 bullet; 3 new `[glossary-*]` defs added alphabetically in the `docs/` group.
  - `KANBAN.md`: `DONE-035-0.0.10` in the Done summary table (line 100) + as a full Done card (line 1399); zero `WIP-ALPHA-035` references remaining; `Spec:` points at `docs/SPECS/spec-035-optimizer_hardening-0_0_10.md` (documented forward reference); 6 shipped DoD items `- [x]`, 2 G3 DoD items `- [ ]` with the `**[DEFERRED …]**` follow-up-card marker. `KANBAN.html` regenerated to match.
  - No version-file edits: `pyproject.toml`, `__init__.py`, `tests/base/test_init.py`, `uv.lock` all clean; `git diff -- django_strawberry_framework/__init__.py` empty (`__all__` untouched).

No `- [ ]` boxes remain in the Plan's verbatim checklist; no deferral to record there.

### DoD items 10-11 verdict — DELIVERED

- **Item 10 (docs):** GLOSSARY appends G1 + G2 to the `DjangoOptimizerExtension` / `only() projection` / `FK-id elision` bodies (no new heading) + the `Strictness mode` G3-deferral pointer; docs/README + README carry the "what the optimizer will not touch" note (G1 + G2 only); CHANGELOG `[Unreleased]` carries the G1 + G2 bullets (maintainer-authorized at kickoff), NO version-heading promotion, NO G3 bullet; KANBAN records `DONE-035-0.0.10` with the spec reference at the `docs/SPECS/` archive path and the G3 deferral as a follow-up card reference. All present and correct.
- **Item 11 (no version bump):** `pyproject.toml` / `__version__` (`__init__.py`) / `tests/base/test_init.py` / `uv.lock` unchanged; on-disk `__version__ = "0.0.9"` and `pyproject version = "0.0.9"`; no `CHANGELOG.md` release heading promoted; `__all__` untouched. Confirmed.

### DB-backed byte-clean invariant — independently confirmed

- Hashed the three committed files, re-ran `uv run python scripts/build_glossary_md.py && build_kanban_md.py && build_kanban_html.py` from the repo root, re-hashed. **All three byte-identical across the regenerate** (`docs/GLOSSARY.md` md5 `54bd4857…`, `KANBAN.md` `c3bb14bf…`, `KANBAN.html` `34869cf8…` — stable before and after). This proves the committed files are DB-faithful (the DB regenerates them identically); the no-op verification regenerate is NOT a change to revert. (`git diff --stat` against HEAD shows the cumulative Slice-4 change set, not a post-regenerate drift — the hashes are the load-bearing proof.)
- `uv run python examples/fakeshop/manage.py import_spec_terms --check` → `OK: 35 done cards have glossary links.` The pre-existing DONE-034 mention drift the plan flagged is cleared by Worker 2's write pass; not a card-35 regression.
- `uv run python examples/fakeshop/manage.py check` → `System check identified no issues (0 silenced).`

### Spec reconciliation — NO spec edit made

No spec edit was made for this slice. The spec FILE correctly stays at its working location `docs/spec-035-optimizer_hardening-0_0_10.md` (AGENTS.md #26 / BUILD.md "Spec stays at its working location") — no archival happens at the completing card; only the `SpecDoc.url` DB field points forward at the future `docs/SPECS/` home, re-rendered into the KANBAN `Spec:` reference. The spec status line (line 5: "G1 shipped; G2 + the doc wrap remain; G3 deferred") describes the card's slice structure / sequencing accurately and makes no false "already-shipped-work remains unshipped" claim requiring correction; G1's shipped status is explicitly recorded, and "G2 + the doc wrap remain" is the scope statement the build executed. Worker 2 and Worker 3 both reported no spec gap. No edit warranted.

### `planning_state` note — ACCEPTED cross-card pre-existing condition (no fix this card)

The rendered `DONE-035-0.0.10` card header reads `- Status: Needs spec` because `planning_state` was deliberately left untouched (plan step 5: out of Slice-4 scope; the spec's Slice-4 scope does not name it and the worker-0 close-out procedure does not change it). Verified repo-wide this matches existing done-card precedent: across DONE cards the rendered `Status:` line is `Shipped` ×28, `Planned` ×4, `Needs spec` ×2, `In progress` ×1 — and the direct joint-`0.0.10`-cut sibling `DONE-034-0.0.10` itself renders `- Status: In progress`. Slice 4 did not introduce the stale-`planning_state` pattern. Per the dispatch ("do NOT require a fix if it matches existing done-card precedent"), this is an **accepted cross-card pre-existing condition**, flagged for the maintainer / next-spec follow-up (a separate cross-card cleanup spanning many DONE cards), NOT a Slice-4 defect.

### DRY check across slices — clean

- G1 (`optimizer/extension.py`, procedural/shipped pre-spec), G2 (`optimizer/walker.py` single derived `enable_only` bool threaded through the four projection writers — NOT four independent `info.operation` checks — plus the `types/resolvers.py` Decision-5 loaded-check), and G4 (docs) do not overlap; no duplicated logic introduced.
- Cross-doc wording is one canonical substance fanned out at the right altitude: GLOSSARY bodies carry the full sentence, README / docs/README a one-line compression, CHANGELOG the past-tense release voice. The G2 "keep `select_related` / `prefetch_related`, no `.only()` column deferral" statement and the G1 "evaluated-queryset pass-through" statement are consistent across all four surfaces with no divergent second framing. No repeated literal / near-copy worth consolidating (doc-only slice).

### Final status: `final-accepted`

Every Plan box truly landed; DoD items 10-11 delivered; byte-clean DB-faithful regenerate, `import_spec_terms --check` (OK, 35 cards), and `manage.py check` (clean) all pass; no version-file or public-surface drift; no spec edit needed; the `planning_state` rendering is an accepted cross-card pre-existing condition; DRY clean across slices.

### Summary

Slice 4 closed out card 35 as a doc + DB-backed wrap with zero source/test/version change. It appended the shipped G1 (evaluated-queryset pass-through) and G2 (non-`QUERY` `.only()` suppression) behaviors to the `docs/GLOSSARY.md` `DjangoOptimizerExtension` / `only() projection` / `FK-id elision` bodies (plus a "what the optimizer will not touch" note), added a G3-deferral pointer to the `Strictness mode` body (G3 ships nothing here), carried the same substance into `README.md` / `docs/README.md` and a `### Changed` / `### Fixed` `[Unreleased]` CHANGELOG pair (maintainer-authorized), and moved `WIP-ALPHA-035` → `DONE-035-0.0.10` via the kanban DB + re-render (SpecDoc url → archive path, 6 shipped DoD items ticked, 2 G3 DoD items left deferred with the follow-up-card marker). No version bump (the joint `0.0.10` cut owns it); on-disk `__version__` stays `0.0.9`. The DB regenerates the three committed generated docs byte-identically.

### Spec changes made (Worker 1 only)

None. No spec edit was made for this slice — see "Spec reconciliation" above. The spec file stays at `docs/spec-035-optimizer_hardening-0_0_10.md` (working location; no archival at the completing card per AGENTS.md #26 / BUILD.md "Spec stays at its working location").
