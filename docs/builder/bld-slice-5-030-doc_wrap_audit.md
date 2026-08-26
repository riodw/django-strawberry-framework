# Build: Slice 5 — doc updates + card-completion wrap (AUDIT-ONLY under the cycle's scope fence)

Spec reference: `docs/SPECS/spec-030-connection_field-0_0_9.md` (`## Slice checklist` Slice 5, lines 80-88; `## Doc updates`, lines 523-536; `## Definition of done` items 1 / 8 / 9 / 10)
Status: final-accepted

**Scope fence (maintainer-set, `build-030-connection_field-0_0_9.md` #"Scope fence").** Every file Slice 5 names — `docs/GLOSSARY.md`, `docs/README.md`, `docs/TREE.md`, `TODAY.md`, `README.md`, `CHANGELOG.md`, `KANBAN.md` / `KANBAN.html`, `examples/fakeshop/db.sqlite3` — is **read-only this cycle**. So this slice **verifies** each doc claim and **records** every divergence for the maintainer, and reconciles only the SPEC where its own Slice-5 / `## Doc updates` / `## Definition of done` text makes a claim that is now false.

## Working-tree baseline re-read (`git status --short`, start and end of pass)

The concurrent session's footprint grew again past the build plan's list: `tests/forms/test_converter.py`, `tests/forms/test_inputs.py`, `tests/forms/test_sets.py`, `tests/test_views.py` are dirty and were not in Slice 4's snapshot. All 18 dirty `.py` files plus `AGENTS.md`, `pyproject.toml`, `uv.lock`, `docs/review/**`, `docs/dry/**`, `docs/bug_hunt/**` are the concurrent session's (`AGENTS.md` rule 34) — **neither edited nor reverted**.

My own footprint at the end of the pass is exactly three paths:

```text
 M docs/SPECS/spec-030-connection_field-0_0_9.md
?? docs/SPECS/appx/spec-030-connection_field-0_0_9-rationale.md
?? docs/builder/bld-slice-5-030-doc_wrap_audit.md
```

`uv run` worked all pass (`check_spec_glossary` ran green through both `uv run` and `.venv/bin/python`), so the concurrent dynamic-version migration that broke it during the rationale pass has settled. No `--cov*` flag was used in any invocation.

---

## Plan (Worker 1)

### Spec status-line re-verification

Lines 1-11 re-read. `Status: **SHIPPED (0.0.9)**`, the `DONE-030-0.0.9` card id, the five-slice summary, the Predecessors paragraph, and the rationale-companion pointer at `:11` all describe the current state; Slices 1-4 already corrected the Predecessors tail and the `Connection-aware optimizer planning` status. Line 5's clause "released under the [`CHANGELOG.md`][changelog] `## [0.0.9]` heading" is **true at `HEAD`** and is the sentence the Decision-13 / DoD reconciliation below aligns the rest of the spec with. No status-line edit needed.

### DRY analysis

**Helper inventory checked.** Not applicable and stated rather than skipped: this slice lands no `.py` change, so no helper, shared constant, validation branch, coercion utility, or test helper is proposed. The package-wide inventory was therefore not refreshed — the condition that would require it (proposing helper-like logic) does not arise.

- **Existing patterns reused.** The audit reuses the three grading tests Slices 1-4 established (the `## Current state` licence with all three cases; the state-claim-vs-scope-statement test; the inverse audit for shipped behavior the contract never states) and the two-disjoint-instrument population rule. Nothing new was derived.
- **New helpers justified.** None.
- **Duplication risk avoided.** The one real risk in this slice is a **partial claim fix** across a matched pair — the `## Slice checklist` KANBAN bullet and its `## Doc updates` twin, and the CHANGELOG bullet and its twin. Both pairs moved in one change; see `### Spec changes made (Worker 1 only)`.

### Boundary count

Zero. No guard, cap, rejection path, or validation branch is added. No failability proof is owed.

### Hot-path declaration

**None.** Stated explicitly per the build plan's conditional declaration: this slice lands no change inside `connection.py::_pipeline_sync`, `::_resolve_from_window`, `::_finalize_queryset`, or `optimizer/extension.py::apply_connection_optimization` — it lands no `.py` change at all.

### Floor-verification scope

**None.** Stated explicitly per the build plan's conditional declaration: no `.py` change under `connection.py`, `types/base.py`, `types/definition.py`, or `optimizer/extension.py`, so no floor run is owed and none is claimed.

### Slice 5's contract, audited against `HEAD`

Sub-check by sub-check, with the file state that decides each.

**(1) `docs/GLOSSARY.md` — the three status flips and the body content. SATISFIED.**

- Index table: `DjangoConnection` (`:117`), `DjangoConnectionField` (`:118`), `Meta.connection` (`:160`) all read `shipped (`0.0.9`)`.
- Entry bodies: `## `DjangoConnection`` (`:543`), `## `DjangoConnectionField`` (`:551`), `## `Meta.connection`` (`:1121`) each carry `**Status:** shipped (`0.0.9`).`.
- `Meta.connection` body describes the `{"total_count": bool}` shape and the Relay-Node requirement (both `Meta.interfaces` and direct inheritance), with a worked `class GenreType` example.
- Browse-by-category rows: `Meta.connection` is present in **Type generation** (`:241`) and **Relay** (`:250`); `DjangoConnectionField` / `DjangoConnection` are in **Relay** (`:250`) and the alphabetical Index head (`:29`, `:30`).
- The `## Doc updates` twin (`:528`) asks for four body details plus the cooperation-point note. All five are in the `DjangoConnectionField` body: sidecar-derived arguments via a synthesized resolver signature, the composition order spelled out, the opt-in `totalCount` with its per-instance and selection-gated qualifiers, the per-target `<TypeName>Connection` class, and the cooperation-point paragraph attributing nested window planning to the sibling entry. **Audited against Slice 3's rewritten S16 instruction, not the pre-`033` flat-walker one**, as that slice's handoff required — the instruction now asks for the note the glossary actually carries, and the glossary carries it.
- "Do not touch the [Connection-aware optimizer planning] entry — its status is `DONE-033-0.0.9`'s to set" is a scope statement, and it holds: that entry reads `shipped (`0.0.9`)` because `033` set it.

**(2) `docs/README.md` — move to the shipped surface. SATISFIED.** `DjangoConnectionField` sits at `:116` under the **`Shipped today` (`0.0.14`)** list (the section opens at `:91`, the list header at `:97`), with the sidecar-derived `filter:` / `orderBy:` arguments and the opt-in `totalCount` both noted, plus the `DjangoConnection[T]` alias. Nothing about the connection field remains in the "coming next" / beta / `1.0.0` block below it.

**(3) `docs/TREE.md` — list `connection.py`, drop the `[alpha]` tag, list the mirrored test. SATISFIED, confirmed rather than assumed.** `connection.py` appears at `:201` under `## django_strawberry_framework (current on-disk layout)` (`:188`-`:307`) and again at `:323` under `## django_strawberry_framework (target package layout)`; `tests/test_connection.py` appears at `:457` under `## Test layout`. Three instruments on the `[alpha]` claim: `grep -ic alpha` = **0**, `grep -c '\[alpha\]'` = **0**, and the file's planned-tag vocabulary is now `# planned by TODO-<CARD>` (16 lines, none of them `connection.py`'s, whose row carries a real description). Slice 4's measurement re-derived and confirmed.

**(4) `TODAY.md` — the products "still waiting for" list. SATISFIED.** `## What products is still waiting for` (`:364`) states in its opening paragraph that "`DjangoConnectionField` (Relay connections) shipped in `0.0.9` and products' four root fields are now connections", the three remaining bullets are `Meta.fields_class` / `Meta.search_fields` / `Meta.aggregate_class` only, and the not-yet-wired surfaces are routed to the fakeshop-activation card `TODO-BETA-061-0.1.5` — which is the alternative the sub-check explicitly licenses. The file stays products-centric.

**(5) `README.md` — the status paragraph. SATISFIED.** `## Status` (`:60`) enumerates the connection field at `:78`: "`0.0.9` — the Relay release: `DjangoConnectionField` (cursor pagination + sidecar-derived `filter:` / `orderBy:` + opt-in `totalCount`)". The sub-check is conditional ("only if it enumerates the connection field"), and it does.

**(6) `CHANGELOG.md` — the `### Added` bullet. SATISFIED as to content; the `[Unreleased]` clause is SPEC DRIFT.** Two bullets at `:94` and `:95` cover all three symbols (`DjangoConnectionField` + `DjangoConnection[T]` in one, `Meta.connection` / `totalCount` in the other), under `### Added` inside `## [0.0.9] - 2026-06-13`. `[Unreleased]` does not exist in the file at all (`grep -c Unreleased CHANGELOG.md` = 0). The grading and repair are in `### The grading tests, applied explicitly` below.

**(7) `KANBAN.md` — the card and its spec reference. SATISFIED.** `### [DONE-030-0.0.9 - `DjangoConnectionField`]` at `:3380`, in the Done section, with `Spec: [spec-030-connection_field-0_0_9.md](docs/SPECS/spec-030-connection_field-0_0_9.md)` at `:3387` — the archived path, correct. The board index table carries the same at `:117`. The `## Doc updates` twin also asks that the card-body DoD's unnumbered `docs/spec-connection.md` reference be rewritten to the canonical name: `grep -c 'spec-connection' KANBAN.md` = **0**, so that is done. Two stale `docs/spec-030` paths survive elsewhere in the same card body — a DB finding, recorded below, not a failure of this sub-check.

**(8) No version-file edits. SATISFIED, and the instrument matters.** `HEAD` cannot answer this (the version has moved since), so the audit is over `030`'s own commits. `git show --stat` over `eaaf1385` (authoring), `10fd7f48` (terms), `8cac3495` (the build), and `e2b5b10b` (the review round):

- `pyproject.toml` — **0** touches across all four.
- `uv.lock` — **0** touches across all four.
- `__version__` — `8cac3495` touches `django_strawberry_framework/__init__.py` (+3), and the version literal is byte-identical `__version__ = "0.0.8"` before and after (`git show 8cac3495^:… | grep __version__` vs `git show 8cac3495:… | grep __version__`). The +3 lines are the `from .connection import …` line and the two `__all__` entries — Decision 14's Slice-4 export promotion.
- `tests/base/test_init.py::test_version` — `8cac3495` **does touch the file** (+2), and the two added lines are `"DjangoConnection",` / `"DjangoConnectionField",` inside `test_public_api_surface_is_pinned`'s `__all__` tuple. `test_version` is untouched.

The rule holds, and it holds **only because all four spec sites state the symbol** `tests/base/test_init.py::test_version` rather than the bare file. Verified from the other side too: the joint-cut commit `6aeebd8d` ("Bump version to 0.0.9 …") is where `pyproject.toml`, `__init__.py`, `tests/base/test_init.py`, `uv.lock`, and the `CHANGELOG.md` heading all move together — exactly the ownership Decision 13 assigns. The concurrent session's in-flight dynamic-version migration on `pyproject.toml` / `tests/base/test_init.py` is irrelevant to this claim, because the claim is about commits, not about the working tree; stated so no reader has to wonder which version it describes.

### The grading tests, applied explicitly

**The `## Current state` licence — case 1 only, and no new site.** No Slice-5 sub-check, `## Doc updates` bullet, or DoD item sits in `## Current state`, so the licence is not engaged by this slice's own surface. `:102` and `:111` were re-derived at `eaaf1385` by Slices 1 / 3 / 4 and are untouched here. Case 2 (a prediction the build falsified) is **absent**. Case 3 recurred — see below.

**Case 3 — a true prediction whose enduring implication later work falsified — recurred, and this is its second appearance outside `## Current state`.** Decision 13 said CHANGELOG bullets "land under `[Unreleased]`". At `8cac3495` they did: `git show 8cac3495:CHANGELOG.md` shows both new bullets under `## [Unreleased]` / `### Added`. The joint cut then promoted that heading to `## [0.0.9] - 2026-06-13` — which is the mechanism the *same Decision* assigns to the joint cut. So the prediction was true and its enduring implication was falsified by the boundary the Decision itself drew. Read in the present tense today it claims a heading `CHANGELOG.md` does not contain. Per Slice 3's rule the repair is to **state the scope boundary the sentence was really expressing**: this card contributes `### Added` bullets and promotes no release heading. The four sites moved together (`:86`, `:427`, `:534`, `:589`); `:591`'s "no `CHANGELOG.md` release heading is promoted" is a pure scope statement and is untouched.

**The state-claim-vs-scope-statement test, which does most of the work here.** Nearly every Slice-5 sentence is an instruction, so the test is applied per sentence rather than per section:

- **Scope statements — stay.** "No version-file edits in this card" (`:88`); "No version-heading promotion" (`:534`, `:591`); "Do not touch the [Connection-aware optimizer planning] entry — its status is `DONE-033-0.0.9`'s to set" (`:81`, `:528`); "the Slice 5 maintainer prompt must name this edit explicitly" (`:86`, `:525`); "keep the file products-centric" (`:84`, `:532`); "only if it enumerates the connection field" (`:85`, `:533`).
- **State claims that drifted — rewritten.** Decision 1's "The spec file lives at `docs/spec-030-…`" (`:285`); DoD item 1's three inline paths and its "`present in both docs/GLOSSARY.md and the CSV as planned for 0.0.9`" clause (`:567`); DoD item 8's "`[Unreleased]` carries the `### Added` bullet" (`:589`); DoD item 9's card-body-reference path (`:590`); the `## Slice checklist` / `## Doc updates` KANBAN path pair (`:87`, `:536`).
- **An instruction whose path claim drifted while the instruction stayed true** — the two KANBAN bullets. The instruction ("point the card body's spec reference at this document") is discharged; only the spelling of "this document" was stale. Fixing the path is not the same as unticking the box, and both were done in the right register.

**The inverse audit — shipped behavior the contract never states.** Slices 2 and 4 each found one. This slice finds no *new* one in `030`'s own contract, and instead finds the mirror-image class three times over: shipped `030`-adjacent behavior that the **docs** never state, which the fence forbids fixing. All three are in `### Maintainer findings`.

### Populations swept, instruments used, and counts

Every count below is an **occurrence** count re-derivable from the command shown, never an asserted number, and every population carries two instruments on genuinely disjoint vocabulary.

**Population A — the spec's self-referential path claims.**

- I1 (literal token): `grep -o 'docs/spec-030' <spec> | wc -l` → **7** before, **0** after.
- I2 (disjoint — never matches the `docs/spec-030` token; reconstructs every path-shaped occurrence of the filename stem and classifies it by full prefix): `grep -oE '[A-Za-z0-9/_.-]*connection_field-0_0_9[A-Za-z0-9.-]*' <spec> | sort | uniq -c`. Before: `docs/spec-030-…​.md` ×6 + `docs/spec-030-…-terms.csv` ×1 = **7 stale**, alongside 16 correctly-relative `appx/…-rationale.md` defs, 1 `appx/…-terms.csv` def, 1 bare `spec-030-…​.md` def, 1 correct `docs/SPECS/appx/…-rationale.md` inline. After: `docs/SPECS/spec-030-…​.md` ×6 + `docs/SPECS/appx/…-terms.csv` ×1, **0 stale**.
- **Instrument-validation note:** I2 is what proved the reference-style **definitions** were never broken (the archival sweep re-relativized them) and that the rot was confined to inline link *text*. That is why no def path was rewritten and no new def was added — a fix aimed at the defs would have been the wrong repair entirely.
- Control: `grep -o 'docs/spec-connection' <spec> | wc -l` = **2**, unchanged — the deliberate contrast with the card body's pre-canonical name, in Decision 1 and the `## Doc updates` KANBAN bullet. `grep -o 'docs/SPECS/' <spec> | wc -l` = **2** before, **10** after.

**Population B — the `[Unreleased]` CHANGELOG-placement claim.**

- I1: `grep -o 'Unreleased' <spec> | wc -l` → **4** before (`:86`, `:427`, `:534`, `:589`), **0** after.
- I2 (disjoint — no `Unreleased` token): `grep -n 'release heading\|version-heading\|release-heading\|CHANGELOG' <spec>` → 11 lines before. It recovers the same 4 and adds 7 that carry **no placement claim**: `:5` (states the shipped `## [0.0.9]` heading — already true), `:51` / `:80` / `:525` (the permission grant), `:451` (the estimate table's file list), `:591` (the scope statement), `:598` (the link def). Post-edit the placement vocabulary count is 5 and every one is a scope statement.
- Corroborating file-side measurement: `grep -c 'Unreleased' CHANGELOG.md` = **0**; the bullets sit under `## [0.0.9] - 2026-06-13` / `### Added` at `:94`-`:95`.

**Population C — the directive-resolved selection gate in `docs/GLOSSARY.md`** (Slice 4's handoff, re-derived rather than inherited).

- I1: `grep -oiE '@skip|@include|directive[a-z-]*' docs/GLOSSARY.md | sort | uniq -c` → `@include` 1, `@skip` 1, `Directives` 1, `directive` 1, `directives` 2 — **6 occurrences over 5 lines** (`:657`, `:764`, `:1498`, `:1501`, `:1687`). Nearest-heading classification: `DjangoListField` (the `directives` pass-through kwarg), the resource-policy walk (a generic directive sentence), **Plan cache** ×2 (`@skip` / `@include` in the cache key), and the body-size cap (reverse-proxy directives). **None is a `030` entry.**
- I2 (disjoint — the property's own vocabulary, not the directive vocabulary): `grep -n 'selection-gat' docs/GLOSSARY.md` → **1** line, `:555`, the `DjangoConnectionField` body, which says "selection-gated" and stops there. So the property is stated in the docs at exactly one site and that site does not say what resolves the selection.
- Spec-side control: the spec now states the directive-resolved property at four sites (Slice 4's edit). Confirmed.

**Population D — keyset cursors / `Meta.cursor_field` in the standing docs.**

- I1: `grep -c 'cursor_field' docs/GLOSSARY.md` = **2** (`:391`, `:547`), and `grep -n '^#\{1,3\} .*[Cc]ursor' docs/GLOSSARY.md` returns two headings, **neither** of them `Meta.cursor_field` (`## Django debug-cursor capture`, `## Reference-counted cursor coordinator`).
- I2 (disjoint token): `grep -ic keyset docs/GLOSSARY.md` = **6**, over 4 entries by nearest-heading classification (`Connection-aware optimizer planning` ×2, `DjangoConnection`, `finalize_django_types` ×2, `Production error policy`). So keyset cursors are described in four other entries' prose and have no entry of their own.
- `CHANGELOG.md`: `grep -ci keyset` = **0** and `grep -c cursor_field` = **0**. Second instrument on the same file: `grep -on 'cursor[a-z_]*' CHANGELOG.md` → 8 occurrences over 6 lines, every one about *offset* cursors or cursor stability, none about the keyset opt-in.
- **The spec's own reference is legitimate as written.** `Meta.cursor_field` occurs 7 times in the spec and is **never** rendered as a glossary link (`grep -o 'cursor_field`\]\[…' <spec>` = 0), and it is **absent from the terms CSV** (`grep -c cursor_field <terms.csv>` = 0). So `check_spec_glossary` cannot and does not complain, and Decision 9 citing `django_strawberry_framework/keyset.py` rather than a glossary anchor is the correct choice given no anchor exists. The glossary gap is a documentation finding, not a spec defect.

**Population E — the already-sliced-`QuerySet` `GraphQLError`** (Slice 2's handoff, re-derived).

- I1 (three spellings): `pre-sliced` / `already-sliced` / `already sliced`, case-insensitive → **0** in `CHANGELOG.md` and **0** in `docs/GLOSSARY.md`.
- I2 (disjoint — the bare stem): `grep -oni 'slic[a-z]*'` → `CHANGELOG.md` 5 occurrences (3 `slice`, 2 `slicing`), all on `:87` / `:94` / `:102` / `:104` about the optimizer's pre-slice queryset and window planning; `docs/GLOSSARY.md` 18 occurrences, and the 4 `sliced` ones are at `:294` (hook-return normalization), `:663` (`DjangoListField` row bound), `:1513` (the multi-db `Prefetch` seal) — none about rejecting a resolver-supplied sliced queryset. The guard's own docstring (`connection.py::_guard_source_not_pre_sliced`) confirms it is a consumer-visible `GraphQLError` converted from a raw `TypeError`.

**Population F — the terms-CSV companion's stale status vocabulary.**

- I1: `grep -c 'WIP-03' <terms.csv>` = **5** (`:5`, `:24`, `:25`, `:29`, `:40`) — `WIP-032` / `WIP-033` card ids for cards that are now `DONE-032-0.0.9` / `DONE-033-0.0.9`.
- I2 (disjoint — status vocabulary, no `WIP` token): `grep -n 'stays planned\|status flips\|flat-selection' <terms.csv>` → 4 lines (`:2`, `:3`, `:19`, `:25`).

**Population G — stale spec paths in the generated board.**

- I1: `grep -c 'docs/spec-030' KANBAN.md` = **2**; `grep -c 'docs/SPECS/spec-030' KANBAN.md` = **2**.
- I2 (disjoint surface — the rendered HTML's JSON data block, read with a Python regex because the shell grep hits a complexity limit on the single-line payload): 2 occurrences on `KANBAN.html:97`, the same two strings. Nearest-card classification puts all of them inside `### [DONE-030-0.0.9 - `DjangoConnectionField`]` (`KANBAN.md:3380`): a DoD checkbox (`- [x] Add `docs/spec-030-connection_field-0_0_9.md`.`) and the card's description bullet. The card's `Spec:` field is correct, so this is residue in the card *body*, not in the reference the sub-check governs.

### Spec slice checklist (verbatim)

Quoted from the spec **as it stood at the start of this pass** — deliberately, because this pass reconciled two of these sub-bullets, and the audit's job is to record the contract it audited. Each box is ticked because the **shipped doc state** satisfies it.

- [x] [`docs/GLOSSARY.md`][glossary]: flip [`DjangoConnectionField`][glossary-djangoconnectionfield], [`DjangoConnection`][glossary-djangoconnection], and [`Meta.connection`][glossary-metaconnection] from `planned for 0.0.9` to `shipped (0.0.9)` in the [Index][glossary-index] table and entry bodies; confirm `Meta.connection` describes the `{"total_count": bool}` shape and the Relay-Node requirement and remains present in the Index plus the "Relay" / "Type generation" [Browse by category][glossary] rows. Do not touch the [Connection-aware optimizer planning][glossary-connection-aware-optimizer-planning] entry — its status is [`DONE-033-0.0.9`][kanban]'s to set.
- [x] [`docs/README.md`][docs-readme]: move `DjangoConnectionField` from the "coming next" `0.0.9` line to the shipped surface list; note the sidecar-derived `filter:` / `orderBy:` arguments and opt-in `totalCount`.
- [x] [`docs/TREE.md`][tree]: list [`connection.py`][connection] under the current on-disk package layout (drop its `[alpha]` planned tag) and the mirrored [`tests/test_connection.py`][test-connection].
- [x] [`TODAY.md`][today]: update the products "still waiting for" list — `DjangoConnectionField` moves from waiting to shipped (or note products' Relay-connection activation tracking, lit up at fakeshop activation per `TODO-BETA-061-0.1.5`); keep the file products-centric.
- [x] [`README.md`][readme]: update the status paragraph's newest-shipped-surface line if it enumerates the connection field (include only if reflected there).
- [x] [`CHANGELOG.md`][changelog]: `### Added` bullet under `[Unreleased]` for `DjangoConnectionField` / `DjangoConnection` / `Meta.connection`. **This is the per-card CHANGELOG-edit permission grant** ([`AGENTS.md`][agents] withholds it by default); the Slice 5 maintainer prompt must name this edit explicitly. No version-heading promotion (per Decision 13).
  - Ticked on the **content** contract, which is satisfied in full: two `### Added` bullets covering all three symbols, and no release heading written by this card. The `[Unreleased]` clause is not a doc gap — it is the case-3 spec drift reconciled as S6 / S7 / S8 / S9 below. Recorded rather than silently ticked, because the sentence as quoted is literally false against `HEAD` and only the reconciled sentence is satisfiable.
- [x] [`KANBAN.md`][kanban]: move this card to the Done column, where it is `DONE-030-0.0.9` (the column-move pass assigns the next available id); add / confirm the card body's spec reference points at `docs/spec-030-connection_field-0_0_9.md` (this document).
  - Ticked: the card is in Done with `Spec:` pointing at the archived path, and the `## Doc updates` twin's "rewrite the unnumbered `docs/spec-connection.md` reference" is discharged (0 occurrences board-wide). The two stale `docs/spec-030` paths elsewhere in the card body are MF-6, a DB finding outside this sub-check's subject.
- [x] **No version-file edits in this card.** Leave `pyproject.toml`, [`__version__`][package-init], [`tests/base/test_init.py::test_version`][test-base-init], and `uv.lock` to the joint `0.0.9` cut per Decision 13.

**Tally: 8 ticked, 0 unticked, 0 deferred.** Worth stating plainly, because the fence made an unticked box the expected outcome: **Slice 5's doc work was actually done at ship time.** `8cac3495` touched all seven of its files (`CHANGELOG.md`, `KANBAN.md`, `KANBAN.html`, `README.md`, `TODAY.md`, `docs/GLOSSARY.md`, `docs/README.md`, `docs/TREE.md`), so the fence blocked nothing a sub-check asked for. Every maintainer finding below is either an **inverse-audit** gap (shipped behavior no doc states) or post-ship drift in text no `030` sub-check governs.

### Implementation steps

None. No `.py` file, test, or fenced-out doc is written by this pass; the only writes are the spec, its rationale companion, this artifact, and the Worker-1 memory file.

### Test additions / updates

None. `tests/test_connection.py` was re-run unchanged as the focused regression scope (see `### Postcondition proofs`).

### Implementation discretion items

None. No implementation.

### CODE GAP list

**Empty.** No `.py` divergence surfaced; this slice's entire surface is documentation and spec text. `Status: final-accepted` rather than `planned` follows directly.

---

## Final verification (Worker 1)

### Spec changes made (Worker 1 only)

Nine edits across two populations, both closed. Line numbers are post-edit.

**S1 — Decision 1 (`:285`): the subject corrected, not the sentence deleted.** It read "The spec file lives at **`docs/spec-030-connection_field-0_0_9.md`** (this document), NOT `docs/spec-connection.md` …". The Decision's subject is the **naming convention**; the sentence carrying it asserted a **location** that `AGENTS.md` rule 26's archival move falsified. It now pins the canonical structured filename `spec-030-connection_field-0_0_9.md` against the card body's unnumbered `docs/spec-connection.md`, then states the archived location as the answer — `docs/SPECS/`, companions under `docs/SPECS/appx/`, cited to `AGENTS.md` — so the reader is never asked to reconstruct where the file is. Reads as though the archived location were always the answer, with no chronology. The `docs/spec-connection.md` contrast is untouched: overruling the card body's wording is why the Decision exists.

**S2 — the `## Slice checklist` KANBAN bullet (`:87`) and S3 — its `## Doc updates` twin (`:536`): the matched pair, moved together.** Inline `docs/spec-030-connection_field-0_0_9.md` → `docs/SPECS/spec-030-connection_field-0_0_9.md` in both. Moving one without the other is precisely the partial-claim-fix defect this cycle keeps finding; naming that as the reason rather than leaving it implicit.

**S4 — DoD item 1 (`:567`): three stale paths, one of them inside a runnable command.** The spec path, the companion-CSV path (`docs/spec-030-…-terms.csv` → `docs/SPECS/appx/spec-030-…-terms.csv`), and `check_spec_glossary.py --spec docs/spec-030-…` — which would fail today on a missing file, so the completion condition was not re-verifiable as written. All three now spell the real location; the command as written now runs and reports `OK: 50 terms`.

**S5 — DoD item 1's status clause (`:567`, same sentence): a pre-flip state described as current.** It said `Meta.connection` "is present in both `docs/GLOSSARY.md` and the CSV as `planned for 0.0.9`; Slice 5 flips it to `shipped (0.0.9)`" — a state claim the flip falsified, paired with an instruction the flip discharged. Half of it was never true at all: the CSV carries no status word for `Meta.connection` (its notes column describes the shape). Item 1 now states the standing condition — a glossary heading exists and a CSV row anchors the term to it — and leaves the status flip to item 8, where a completion condition about status belongs.

**S6 — the `## Slice checklist` CHANGELOG bullet (`:86`).** "`### Added` bullet under `[Unreleased]`" → "`### Added` bullets", with the placement replaced by the scope boundary it was expressing: this card contributes bullets only, and the heading they ship under belongs to the joint `0.0.9` cut. The permission-grant sentence and the maintainer-prompt requirement are untouched — both are scope statements and both still hold.

**S7 — Decision 13 (`:427`).** "CHANGELOG bullets land under `[Unreleased]`." → "The card contributes `### Added` bullets only; the release heading they ship under is not this card's to write." Same case-3 repair. The Decision's other three clauses (the four version files by symbol, no release-heading promotion, the joint cut owning the `0.0.8` → `0.0.9` bump) are unchanged and were all verified true.

**S8 — the `## Doc updates` CHANGELOG bullet (`:534`): S6's twin, moved in the same change.** Also tightened "No version-heading promotion" to "No release-heading promotion — the heading they ship under belongs to the joint `0.0.9` cut", so the twin says the same thing as its checklist partner rather than a near-miss of it.

**S9 — DoD item 8 (`:589`).** "`CHANGELOG.md` `[Unreleased]` carries the `### Added` bullet" → "`CHANGELOG.md` carries the `### Added` bullets under the `0.0.9` release heading the joint cut owns". A completion condition may name where the bullets are; it may not name a heading the file no longer has. This is the site that makes the whole population coherent, because line 5's opener already said the card was "released under the `CHANGELOG.md` `## [0.0.9]` heading" — the spec previously disagreed with itself two hundred lines apart.

**S10 — DoD item 9 (`:590`).** Card-body-reference path corrected to `docs/SPECS/spec-030-connection_field-0_0_9.md`. The item asserts what `KANBAN.md` records, and the board records the archived path — so the spec was the wrong half of the pair.

**Not changed, deliberately.**

- `:88` (no version-file edits), `:591` (DoD item 10) — scope statements, both verified true against `030`'s own commits, both stating the symbol `::test_version` rather than the file, which is what makes them true. Touching either would have broken a correct claim.
- `:81` / `:528` (the glossary bullets) — Slice 3's S8 / S16 already rewrote both; audited against the current instruction and satisfied.
- `:82`-`:85` and `:530`-`:533` (`docs/README.md`, `docs/TREE.md`, `TODAY.md`, `README.md`) — instructions describing landed work, each verified satisfied. The two surviving `[alpha]` mentions inside them are instructions about landed work, not state claims (Slice 4's grading, re-derived here).
- `:5` — its `## [0.0.9]` clause is true and is what the S9 reconciliation aligns the DoD with.
- No reference-style link **definition** was rewritten and none was added. Population A's I2 proved the defs were re-relativized by the archival sweep and all resolve; the rot was confined to inline link text. `docs/SPECS/appx/` continues to share its parent's `<!-- docs/SPECS/ -->` group header, and the ten headers remain a closed list — no eleventh was earned or attempted.
- The unused `[goal]` link definition — pre-existing, named again so no sweep attributes it here.

### Rationale companion appends (Worker 1 only)

Append-only, per `worker-1.md` `### Performing the rationale move` rule 4. Three appends, each keyed to the spec text it explains.

- **Decision 1 → `### Changes this Decision underwent`**, one `**Post-ship:**` bullet: why the subject/location split matters, why the convention half survives, and why the repair is a subject correction rather than a deletion.
- **Decision 13 → `### Changes this Decision underwent`**, two `**Post-ship:**` bullets: (a) the no-version-bump audit in full, including the `tests/base/test_init.py` file-vs-symbol subtlety and the both-sides confirmation via `6aeebd8d`, with the standing lesson that a claim can be right in every path and wrong in its subject; (b) the `[Unreleased]` case-3 grading, with the evidence at `8cac3495` and the note that the bullet text itself was later rewritten — a second reason no spec sentence should pin a CHANGELOG bullet's surroundings.
- **`## Non-Decision deliberation` → new `### Post-ship: the self-referential path claims the spec's own archival invalidated`**: the measured 7-site population with both instruments, the per-site grading (the runnable command, the matched pair, the DoD-item-9 wrong-half-of-the-pair, and Decision 1 as the odd one out), and the DoD-item-1 status clause that rode in the same sentence without being a path claim at all.

### Postcondition proofs

- **Glossary gate:** `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-030-connection_field-0_0_9.md` → `OK: 50 terms - all have glossary entries and at least one spec link.` Run before the edits, after the spec edits, and after the companion appends; identical every time. Also run through `.venv/bin/python` as the fallback path, same result.
- **Trailing-comma / link-scaffold gate:** `uv run python scripts/check_trailing_commas.py --check docs/SPECS/spec-030-connection_field-0_0_9.md docs/SPECS/appx/spec-030-connection_field-0_0_9-rationale.md` → exit 0.
- **Link / anchor integrity, instrument validated on a known-good file first.** `START.md` yields exactly three explainable hits, all of them the file's own literal syntax examples in prose (`[text][ref-id]`, `](#decision-N)`, `](#some-heading)`) — one class, not three defects. Against that baseline: spec **110 defs, 109 used, unused=['goal']** (the pre-existing orphan), and **no dangling in-page anchor, no undefined ref-id, no missing def target, no dangling def anchor**; companion **58 defs, 58 used, zero unused, zero problems**. Identical to Slice 4's postcondition, so no edit here disturbed either scaffold. (Run against **this artifact** the checker reports the same three hits, for the same reason — this sentence quotes those literal examples. A checker that flags its own documentation is behaving correctly; noted so the next reader does not read it as three defects here either.)
- **Disk-exists check on every path this pass wrote into the spec.** `docs/SPECS/spec-030-connection_field-0_0_9.md` and `docs/SPECS/appx/spec-030-connection_field-0_0_9-terms.csv` both exist; the `check_spec_glossary` invocation now quoted in DoD item 1 was executed verbatim and reports `OK: 50 terms`, which is the strongest form of the check for that site.
- **Staged-anchor sweep** (`worker-1.md` `## Final verification job` step 6, mandatory for a doc-wrap slice): `grep -rEn 'TODO\(spec-030|TODO-(ALPHA|BETA|STABLE)-030' .` over `*.py` / `*.md` / `*.csv`, excluding the board files where `TODO-<MILESTONE>-<NNN>` legitimately names unshipped cards → **zero hits**. No anchor of this build's spec or card survives anywhere in shipped source, tests, or standing docs.
- **`.py` surface byte-unchanged by this pass.** `git status --short` attributes exactly one modified file to me (`docs/SPECS/spec-030-connection_field-0_0_9.md`) plus two untracked (the companion, this artifact). All 18 dirty `.py` files are in the concurrent session's set, which grew by four `tests/forms/` + `tests/test_views.py` files during the pass; none was edited or reverted.
- **Focused tests:** `uv run pytest tests/test_connection.py --no-cov -q` → **71 passed** (8 workers, 71 items). No `--cov*` flag in any invocation this pass.
- **Sizes:** spec 136,865 B → **137,372 B** (+507); companion 86,773 B → **93,103 B** (+6,330). The spec shrank in claims and grew by 507 bytes of path and boundary text; the whole explanation is in the companion, which is where the maintainer's split puts it.

### Public-surface check

In scope for this slice and filled rather than deleted, because Slice 5's DoD item 10 makes a claim about `django_strawberry_framework/__init__.py`.

`git diff -- django_strawberry_framework/__init__.py` **does** change the file, and the change is not this cycle's: Slice 4 byte-diffed it against `git show HEAD:` and found three added comment lines about single-sourcing the release literal, with `__all__` and the re-export list identical. Re-confirmed unchanged in that respect this pass. This slice added no public export and removed none — it wrote no `.py` byte at all.

The historical half of the claim is the one this slice owns, and it is verified: at `8cac3495` the file gained `from .connection import DjangoConnection, DjangoConnectionField` plus the two `__all__` entries, authorized by Decision 14 and DoD item 7, with `__version__` byte-identical `"0.0.8"` across the commit.

### CHANGELOG sanity

In scope and filled rather than deleted. This slice **did not modify** `CHANGELOG.md` — it is fenced out — so the check is run as an audit of the shipped entry against the spec's contract:

- **Version line.** The two `030` bullets sit under `## [0.0.9] - 2026-06-13`. That heading matches the release the spec's `Status:` line names, and the card did not write it (`6aeebd8d` did). Consistent with Decision 13 as reconciled.
- **Headings used.** `### Added` — exactly what Slice 5 and `## Doc updates` authorize. No `### Changed` / `### Fixed` / `### Removed` entry is attributable to this card.
- **Wording against behavior shipped.** Both bullets read coherently against `HEAD`: the field bullet names the Relay-Node target, the `edges` / `node` / `pageInfo` envelope on Strawberry's native `relay.connection()`, the sidecar-derived arguments via a synthesized resolver signature, the full six-step composition pipeline in the contracted order, the field-owned optimizer cooperation point with the correct reason (connection slicing hides the pre-slice queryset from the middleware), the `first` + `last` guard, and the `connection.py` module plus the `DjangoConnection[T]` alias. The `Meta.connection` bullet names the `{"total_count": True}` shape, type-creation validation, the generated per-target `<TypeName>Connection`, the selection gate, the post-filter pre-slice count, and the per-instance independence of two aliases' counts.
- **Nothing overstates or understates.** One measured qualification: the bullet text at `HEAD` is **not** the text that landed at `8cac3495` — a later editorial pass shortened and reordered both bullets. Same three symbols, same substance, no claim added or dropped. Noted because a `diff` against the commit is the only way to see it, and because it is a second reason the spec should not pin a bullet's surroundings.
- **Understated by omission, and this is a finding rather than a nit:** the file documents `030`'s surface and not two later consumer-visible additions to the same field. See MF-3 and MF-4.

### Documentation / release sanity

In scope — this slice's whole subject is documentation — and filled rather than deleted. This pass modified only the spec and its rationale companion.

- **Version strings, shipped/planned statuses, card IDs.** The spec's `Status: **SHIPPED (0.0.9)**`, the `DONE-030-0.0.9` id, and the sibling ids match the board and the changelog. Every status word in the seven audited docs that concerns `030`'s three symbols reads `shipped (0.0.9)`; none reads `planned`. `grep -c 'planned for `0.0.9`'` over the spec is unchanged from Slice 3's measurement and every occurrence is about `030`'s own glossary entries or the licensed `:102` observation.
- **KANBAN movement.** None by this pass. The card is already in Done, once, with no residue in any other column (`grep -n 'DONE-030-0.0.9'` returns dependency and cross-reference rows in other cards' bodies, which is the board's normal shape, plus exactly one `### [DONE-030-0.0.9 …]` card heading).
- **Spec archival.** Already complete: the spec sits at `docs/SPECS/` with both companions at `docs/SPECS/appx/`. This pass made the spec's own text agree with that, which is the half the archival sweep missed.
- **Links introduced or moved.** No definition was added or re-pointed. The five inline paths this pass rewrote are link *text* over existing, resolving definitions; all disk-exists-checked, and the anchor checker reports zero problems on both files.
- **Verbatim spec text copied elsewhere.** None by this pass. The `### Spec slice checklist (verbatim)` quotations above are the pre-edit spec text, deliberately, and are labeled as such.
- **No obsolete "coming soon" / "planned" / old-version wording** remains in anything this pass touched, and none was found in the seven audited docs concerning `030`'s surface.
- **No script-rendered doc was regenerated** and no module docstring was touched, so the staging-language clause does not apply. Recorded rather than skipped, because a non-fenced cycle would owe a `docs/TREE.md` regenerate here and this one is forbidden it — and the regenerate is, in any case, already unnecessary: `docs/TREE.md` carries `connection.py` and `tests/test_connection.py` with no `[alpha]` tag anywhere.

### Maintainer findings

**The cycle's Slice-5 deliverable.** Every divergence the scope fence stopped this slice from fixing, with the file, the claim, the actual state, and whether the repair is a text edit or a DB-backed regenerate. `docs/GLOSSARY.md`, `KANBAN.md`, and `KANBAN.html` are **generated** from `examples/fakeshop/db.sqlite3` (`BUILD.md` `### Generated docs are DB-backed`), so a divergence in any of them is a **DB finding** — edit the DB via the Django ORM and re-render, never hand-edit the rendered markdown — and is doubly out of scope for editing here.

**MF-1 — `docs/GLOSSARY.md`: the three `030` entries never state that `totalCount` selection-gating is directive-resolved.** *(DB-backed regenerate.)*
The claim as the docs make it: `DjangoConnectionField` (`:555`) says the count is "selection-gated" and stops there; `DjangoConnection` (`:547`) and `Meta.connection` (`:1121`-`:1127`) do not raise the subject. Actual shipped behavior: the gate resolves `@skip` / `@include` through `optimizer/selections.py::should_include`, so a directive-excluded `totalCount` issues no count query — live-pinned by `examples/fakeshop/test_query/test_library_api.py::test_genre_connection_total_count_skip_include_no_count`, and now contracted in the spec at four sites (Slice 4's edit). The glossary has **zero** directive-vocabulary occurrences in any `030` entry (Population C, two instruments). A consumer reading only the glossary cannot tell whether a `@skip`-ed `totalCount` still costs a query.

**MF-2 — `docs/GLOSSARY.md`: `Meta.cursor_field` is shipped public surface with no glossary heading.** *(DB-backed regenerate.)*
The claim: `docs/GLOSSARY.md` is the package's capability catalog and carries a heading per `Meta` key — `Meta.connection`, `Meta.relation_shapes`, `Meta.globalid_strategy`, `Meta.optimizer_hints`, and the rest all have one. Actual state: `Meta.cursor_field` has **none**, while two entry bodies reference the key as though a reader could look it up (`Connection-aware optimizer planning` `:391`, `DjangoConnection` `:547`), and keyset cursors are described in four other entries' prose with no entry of their own (Population D, two instruments). The key is validated at finalization (`finalize_django_types` `:928` names the validation step), so it is a public, type-level, `ConfigurationError`-guarded surface. **This slice also settles the question Slice 1 raised about the spec's side of it: the spec's own reference is legitimate as written** — `Meta.cursor_field` is never rendered as a glossary link and is absent from the terms CSV, so `check_spec_glossary` is satisfied and Decision 9's citation of `django_strawberry_framework/keyset.py` is the correct choice while no anchor exists. Nothing in the spec needs changing; the glossary needs an entry.

**MF-3 — `CHANGELOG.md`: no entry for the keyset-cursor feature or `Meta.cursor_field`.** *(Text edit.)*
The claim: `CHANGELOG.md`'s own header says "All notable changes to this project will be documented in this file", and every other consumer-facing `Meta` key has an entry. Actual state: `grep -ci keyset` = **0** and `grep -c cursor_field` = **0**; the eight `cursor`-stem occurrences are all about offset cursors or cursor stability (Population D). The keyset codec, its `Meta.cursor_field` opt-in, and the AES-SIV soft dependency shipped on the `0.0.14` line as public surface. Not `030`'s work — `connection.py` merely dispatches to it — which is likely how it fell between two cards' changelog obligations.

**MF-4 — `CHANGELOG.md` and `docs/GLOSSARY.md`: the already-sliced-`QuerySet` `GraphQLError` is undocumented.** *(Text edit for `CHANGELOG.md`; DB-backed regenerate for `docs/GLOSSARY.md`.)*
The claim: consumer-visible error contracts on a shipped field are documented — the `first` + `last` `GraphQLError` is in both files. Actual state: the guard `connection.py::_guard_source_not_pre_sliced` converts what was a raw `TypeError` at the GraphQL boundary into a clear `GraphQLError` when a consumer `resolver=` returns an already-sliced queryset (`Category.objects.all()[:5]`), and **neither** file mentions it under any of five spellings tested (Population E, two instruments per file). Slice 2 established that this guard reached the package through a commit with no card and no spec, which is why no card's doc obligation ever covered it — the same card-less-provenance pattern the integration pass is carrying forward.

**MF-5 — `docs/SPECS/appx/spec-030-connection_field-0_0_9-terms.csv`: the notes column still narrates pending work and uses retired card ids.** *(Text edit; the file is on this slice's do-not-touch list.)*
Four distinct claims, all stale (Population F, two instruments): rows 2 and 3 say the `DjangoConnectionField` / `DjangoConnection` "status flips planned for 0.0.9 -> shipped (0.0.9)" as pending work; row 25 says `Connection-aware optimizer planning` "stays planned for 0.0.9", which the glossary now contradicts outright (`shipped (0.0.9)`); row 19 says the optimizer "in 0.0.9 rides the existing root-gated flat-selection walker", the exact claim `DONE-033-0.0.9` retired and Slice 3 removed from the spec; and rows 5 / 24 / 25 / 29 / 40 use `WIP-032` / `WIP-033` for cards now `DONE-032-0.0.9` / `DONE-033-0.0.9`. None of this is gated: `check_spec_glossary` validates the `term,anchor` pair against real glossary headings and never reads the notes column, so this text can drift indefinitely without any instrument objecting. Recorded as a **gate gap** as much as a content gap.

**MF-6 — the kanban DB: the `DONE-030-0.0.9` card body carries two stale `docs/spec-030` paths.** *(DB-backed regenerate — the fix is two ORM row edits plus `build_kanban_md.py` / `build_kanban_html.py`; note that `KANBAN.html`'s Vue shell is hand-edited and only its data block regenerates.)*
The claim: `AGENTS.md` rule 26 says the archival step "rewrites every cross-reference in one sweep". Actual state: the sweep updated the card's `Spec:` field (`KANBAN.md:3387`, correct `docs/SPECS/…`) and the board index table (`:117`, correct) but missed two rows inside the same card body — the DoD checkbox `- [x] Add `docs/spec-030-connection_field-0_0_9.md`.` (`:3479`) and the card's description bullet naming "New `connection.py` + `docs/spec-030-connection_field-0_0_9.md` + tests" (`:3514`). Both render into `KANBAN.html:97`'s JSON payload as well (Population G, two instruments and two surfaces). Two occurrences of the stale path against two of the correct one, inside one card — which is why a whole-file count could not have distinguished "archived" from "half-archived".

**Not a finding, recorded so no later sweep re-opens it.** The two surviving `[alpha]` mentions in the spec (`:83` checklist, `:530` `## Doc updates`) instruct Slice 5 to drop `connection.py`'s `[alpha]` tag from `docs/TREE.md`. That work is done — three instruments return zero — so the instructions correctly describe landed work and are not drift. Slice 4's measurement re-derived rather than inherited.

### Summary

Slice 5's contract is satisfied at `HEAD` in full, on all eight sub-checks, and the fence blocked nothing any sub-check asked for: `030`'s own build commit `8cac3495` touched every one of Slice 5's seven doc files, so the doc wrap genuinely happened at ship time. `docs/GLOSSARY.md` carries all three status flips in both the Index and the entry bodies, with the `DjangoConnectionField` body matching Slice 3's rewritten instruction rather than the pre-`033` one; `docs/README.md` lists the field on the shipped surface with both required notes; `docs/TREE.md` carries `connection.py` and its mirrored test with no `[alpha]` tag anywhere; `TODAY.md` states the field shipped and routes the unwired surfaces to `TODO-BETA-061-0.1.5` while staying products-centric; `README.md`'s `## Status` enumerates it; `CHANGELOG.md` carries both `### Added` bullets covering all three symbols; and `KANBAN.md` records the card in Done with its `Spec:` field on the archived path and no `docs/spec-connection.md` residue board-wide.

**Decision 13's no-version-bump rule holds, verified from both sides.** Across `030`'s four commits, `pyproject.toml` and `uv.lock` are untouched and `__version__` is byte-identical `"0.0.8"`; the joint-cut commit `6aeebd8d` is where all four version files and the release heading move together. The one subtlety is the finding worth carrying: `8cac3495` **does** touch `tests/base/test_init.py`, for Decision 14's `__all__` pin, and the rule survives it only because every one of the four spec sites states the symbol `::test_version` rather than the bare file.

**CODE GAP list: empty.** Ten reconciliation edits (S1-S10) landed in the spec, closing two populations. Population A, **7 occurrences over 5 lines**, took 5 edits: Decision 1's subject/location split (S1), the KANBAN matched pair (S2 / S3), DoD item 1's three paths including a runnable command (S4), and DoD item 9 (S10) — plus S5, a pre-flip status clause riding in item 1's sentence without being a path claim. Population B, **4 occurrences over 4 lines**, took 4 edits, one per site: the checklist bullet (S6), Decision 13 (S7), the `## Doc updates` twin (S8), and DoD item 8 (S9). Both populations measure **0** post-edit on both instruments. Each edit's "what changed and why" is in the rationale companion and none of it in the spec. `check_spec_glossary` holds at `OK: 50 terms`, both link scaffolds validate against an instrument verified on a known-good file first, every anchor resolves, the `.py` surface is byte-unchanged, the staged-anchor sweep returns zero, and the 71-row focused scope passes.

**Six maintainer findings**, and their shape is the slice's real result: **not one is a Slice-5 sub-check the fence left open.** Four are inverse-audit gaps — shipped, live-pinned behavior that no standing doc states (the directive-resolved gate, `Meta.cursor_field`, keyset cursors, the pre-sliced-queryset error) — and two are post-ship drift in text no `030` sub-check governs (the terms CSV's notes column, the kanban card body's two stale paths). Three of the six are DB-backed and cannot be fixed by editing text at all.

### Spec changes made (Worker 1 only) — deferral reasons for unticked boxes

None. All eight boxes in `### Spec slice checklist (verbatim)` are ticked because the shipped doc state satisfies them; nothing is deferred and nothing is silently un-ticked. Two boxes carry an explicit qualification rather than a bare tick — the CHANGELOG box (ticked on its content contract, with the `[Unreleased]` clause reconciled as spec drift rather than recorded as a doc gap) and the KANBAN box (ticked on the spec-reference contract, with the card body's two stale paths routed to MF-6) — because a tick that hides a qualification is the over-tick this discipline exists to prevent.

### Handed forward to the integration pass

- **The six maintainer findings above are the cycle's Slice-5 deliverable** and must reach `bld-final-030.md`'s `### Deferred work catalog` intact, each with its text-edit-vs-DB-regenerate disposition. Three are DB-backed (`docs/GLOSSARY.md` ×2, the kanban DB ×1); two are `CHANGELOG.md` text edits; one is the terms-CSV text. None is fixable inside this cycle's fence.
- **MF-5 is also a gate gap, not only a content gap.** `check_spec_glossary.py` validates a terms CSV's `term,anchor` pair and never reads its notes column, so every archived spec's CSV can carry arbitrarily stale prose with no instrument objecting. Worth a decision: either the notes column is contract text and needs a gate, or it is scratch and should stop asserting statuses. Four `030` rows currently assert statuses that contradict `docs/GLOSSARY.md`.
- **A fourth instance of the card-less / spec-less provenance pattern**, and the first one visible from the *documentation* side rather than the code side. Slices 2, 3, and 4 found three surfaces reaching the shipped package through commits naming no card. MF-3 and MF-4 are the doc-shaped consequence: a feature that belongs to no card's doc obligation gets no changelog entry and no glossary heading, and no gate notices. The `git log -S` sweep Slices 2-4 recommended should therefore also ask, per hit, whether the surface it finds is documented — a card-less commit's *doc* debt is invisible to every instrument this cycle has used.
- **Both prior open items are still open and now have a third reason to look.** The `DONE-032-0.0.9` parity-table row (`:150`) still reads `planned` for a shipped card; Slice 4 confirmed `relay.py` is real and shipped, and this slice adds that `docs/README.md:117` and `TODAY.md:380` both describe `DjangoNodeField` / `DjangoNodesField` as shipped in `0.0.9` — three independent documents agreeing against that one cell. Fixing it still needs someone who has audited `032`. And `:557`'s "Auto-trigger of `finalize_django_types()` — deferred to `032`" is carried from Slices 1-4 and remains unaudited.
- The unused `[goal]` link definition in the spec — pre-existing, harmless, named once more so no sweep attributes it to this pass.
- **A method note for the integration pass's own reconciliation.** Population A is the first population this cycle where the **reference-style definitions were correct and the inline link text was wrong**. Any sweep that checks link resolution — including the anchor checker used in every slice of this cycle — reports a clean file in exactly that case. The instrument that found it reconstructs the visible path and classifies it by prefix; a resolution check never could. Worth applying to the other archived specs, since the same archival sweep produced all of them.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md
[changelog]: ../../CHANGELOG.md
[kanban]: ../../KANBAN.md
[readme]: ../../README.md
[today]: ../../TODAY.md

<!-- docs/ -->
[docs-readme]: ../README.md
[glossary]: ../GLOSSARY.md
[glossary-connection-aware-optimizer-planning]: ../GLOSSARY.md#connection-aware-optimizer-planning
[glossary-djangoconnection]: ../GLOSSARY.md#djangoconnection
[glossary-djangoconnectionfield]: ../GLOSSARY.md#djangoconnectionfield
[glossary-index]: ../GLOSSARY.md#index
[glossary-metaconnection]: ../GLOSSARY.md#metaconnection
[tree]: ../TREE.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->
[connection]: ../../django_strawberry_framework/connection.py
[package-init]: ../../django_strawberry_framework/__init__.py

<!-- tests/ -->
[test-base-init]: ../../tests/base/test_init.py
[test-connection]: ../../tests/test_connection.py

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
