# Build: Slice 5 — doc updates + card-completion wrap (AUDIT ONLY; the external doc surfaces are out of fence)

Spec reference: `docs/SPECS/spec-031-globalid_encoding-0_0_9.md` `## Slice checklist` Slice 5 (line 77 ff.),
`## Doc updates` (line 534 ff.), `## Definition of done` items 1 and 7-10.
Rationale companion: `docs/SPECS/appx/spec-031-globalid_encoding-0_0_9-rationale.md`.
Build plan: `docs/builder/build-031-globalid_encoding-0_0_9.md` (`## Cycle shape`, `### Scope fence`).
Status: final-accepted

Closed by **procedural closure** (`docs/builder/BUILD.md` `### Procedural-closure slices`): the CODE GAP
list is empty and no source or test edit is warranted, so this is one combined Plan + Final-verification
block with `Status: final-accepted` set directly. No Worker 2, no Worker 3.

---

## Plan (Worker 1) + Final verification (Worker 1)

### Working-tree baseline (re-read at the start of this pass)

`git status --short` at pass start:

```
 M docs/SPECS/spec-031-globalid_encoding-0_0_9.md
?? docs/SPECS/appx/spec-031-globalid_encoding-0_0_9-rationale.md
?? docs/builder/bld-031-slice-{0,1,2,3,4}-*.md
?? docs/builder/build-031-globalid_encoding-0_0_9.md
```

All six are this cycle's own work. **The build plan's four baseline-dirty concurrent paths are gone**:
the concurrent session committed them mid-cycle (HEAD `bc4ed00a` → `5ebcfe9c`, via `0e5044da
fix(consumers): fail closed when revalidation itself fails` and `5ebcfe9c chore(kanban): carry the board
and glossary source for the rendered docs`). `django_strawberry_framework/consumers.py`,
`utils/sessions.py`, `tests/test_consumers.py`, and `examples/fakeshop/db.sqlite3` are therefore clean at
HEAD and nothing in this pass touches them. Note that `5ebcfe9c` committed the **DB and the rendered
board/glossary** — which is the source this slice audits — so the surfaces below are read at their
committed state, not at a mid-write one.

### This slice is split down the middle

Slice 5's spec contract is "doc updates + card-completion wrap". The maintainer's fence covers spec files
and `.py` files only, so:

- **the external doc surfaces are AUDIT-ONLY** — `docs/GLOSSARY.md`, `docs/README.md`, `docs/TREE.md`,
  `TODAY.md`, `README.md`, `CHANGELOG.md`, `KANBAN.md`, `KANBAN.html`, `examples/fakeshop/db.sqlite3`, and
  the spec's `-terms.csv`. Verified, never edited; a divergence would be a `### Deferred work catalog`
  item for `bld-031-final.md`, not a fix;
- **the spec file and the rationale companion are fully in fence and fully mine**, so any Slice-5 finding
  whose fix lives inside the spec is fixed in this pass. That half is what discharges the two findings
  routed forward unclaimed for four slices.

`docs/GLOSSARY.md`, `KANBAN.md`, and `KANBAN.html` are additionally **generated from
`examples/fakeshop/db.sqlite3`** (`docs/builder/BUILD.md` `### Generated docs are DB-backed`), so they are
doubly out of fence: never hand-edited, and no generator was run in this pass.

### DRY analysis

- **Helper inventory checked.** Not applicable in the code sense — this slice writes no code and plans
  none. The DRY question it does own is **claim duplication across the spec's regions**, which is this
  cycle's dominant defect: Slice 2 found one contract stated wrong in five homes at once. Every claim this
  pass touched was swept for its full population before being edited (see
  `### Spec changes made (Worker 1 only)`), and the two claims it corrected were re-stated in **five** and
  **four** homes respectively, not one.
- **Existing patterns reused.** The `**Post-ship:**` bullet convention Slices 1-4 established in the
  rationale companion, keyed to the spec Decision by heading and anchor. Four bullets appended, no new
  section, no new shape.
- **New helpers justified.** None.
- **Duplication risk avoided.** The naive fix for the pre-archival-path finding is a global
  `docs/spec-031-…` → `docs/SPECS/spec-031-…` string replace across five sites. That would have written
  the *same* fragile claim five more times, one archival move from breaking again. The fix instead
  **removes the path from the prose entirely** at four of the five sites and lets the reference-style
  `[spec-031]` definition carry it — one source, and the convention `START.md` documents for exactly this.

### Spec slice checklist (verbatim)

Copied verbatim from the spec's `## Slice checklist` Slice 5. Boxes are ticked where the contract
**landed in the shipped repository**, which is what a residual cycle audits.

- [x] Slice 5: doc updates + card-completion wrap (grants the per-card [`CHANGELOG.md`][changelog] edit permission)
  - [x] [`docs/GLOSSARY.md`][glossary]: add a `## Meta.globalid_strategy` entry and a `## RELAY_GLOBALID_STRATEGY` (or a single "Django-model-based GlobalID encoding") entry as `shipped (0.0.9)`, add their Index rows, and add them to the "Relay" / "Type generation" [Browse by category][glossary] rows; extend the [Relay Node integration][glossary] body to describe the model-anchored default and the strategy override.
  - [x] [`docs/README.md`][docs-readme]: note the model-anchored `GlobalID` default and the `Meta.globalid_strategy` / `RELAY_GLOBALID_STRATEGY` opt-out in the shipped-surface list.
  - [x] [`docs/TREE.md`][tree]: no new module (encode / decode live in the existing `types/relay.py`); add the `conf.py` `RELAY_GLOBALID_STRATEGY` settings note if the layout reference enumerates settings keys.
  - [x] [`TODAY.md`][today]: update the products `GlobalID`-filtering examples to the model-label payload and add the breaking-wire-format-change note **including the `type+model`-first upgrade sequence**; keep the file products-centric.
  - [x] [`README.md`][readme]: update the status paragraph's newest-shipped-surface line if it enumerates the GlobalID encoding.
  - [x] [`CHANGELOG.md`][changelog]: a `### Changed` (breaking) bullet for the model-anchored `GlobalID` default — which **must prescribe the `type+model`-first upgrade sequence** — plus an `### Added` bullet for `Meta.globalid_strategy` / `RELAY_GLOBALID_STRATEGY`, both under `[Unreleased]`. No version-heading promotion.
  - [x] [`KANBAN.md`][kanban]: move this card to the Done column, where it is `DONE-031-0.0.9`; add / confirm the card body's spec reference points at this document.
  - [x] **No version-file edits in this card.** Leave `pyproject.toml`, `__version__`, `tests/base/test_init.py::test_version`, and `uv.lock` to the joint `0.0.9` cut.

---

## CODE GAP audit

Slice 5 contracts no production code, so the question is the one the build plan's `## Cycle shape` item 2
states: **did the wrap skip, drop, or forget anything the spec planned?** Every contracted item is walked
below with its verdict and the evidence, against `## Slice checklist` Slice 5, `## Doc updates`, and
`## Definition of done` items 1 and 7-10.

**Verdict: the CODE GAP list is EMPTY.** Every contracted doc surface landed. Nothing was skipped,
dropped, or forgotten.

### Contracted surfaces (`docs/GLOSSARY.md` — DoD item 7 first clause)

| # | Contracted | Verdict | Evidence |
|---|---|---|---|
| G1 | `## Meta.globalid_strategy` entry, `shipped (0.0.9)` | **landed** | `docs/GLOSSARY.md:1198` heading, `:1200` `**Status:** shipped (`0.0.9`)`, full four-strategy table + precedence + the `0.0.14` fail-closed paragraph |
| G2 | `## RELAY_GLOBALID_STRATEGY` entry, `shipped (0.0.9)` | **landed** | `docs/GLOSSARY.md:1663` heading, `:1665` status line, body covering the thin-reader read, the once-per-lifecycle unconditional validation, the snapshot, and the `registry.clear()` requirement |
| G3 | Index rows for both | **landed** | `:167` — the `Meta.globalid_strategy` Index row, anchored `#metaglobalid_strategy`, status `shipped (0.0.9)`; `:199` — the `RELAY_GLOBALID_STRATEGY` Index row, same status |
| G4 | "Relay" / "Type generation" Browse-by-category rows | **landed** | `:241` Type-generation row carries `Meta.globalid_strategy`; `:250` Relay row carries `RELAY_GLOBALID_STRATEGY`. See the note below — the slash is read as an assignment, not a doubling |
| G5 | `Relay Node integration` body extended with the model-anchored default | **landed** | `:1659` — the `0.0.9` model-label default, all four strategies, the precedence chain, the unchanged `node_id` / FK-`id` / composite-pk facts, and the `DONE-032` refetch surface; `:1661` See-also carries both new anchors |

**Note on G4, recorded as an ambiguity and not a divergence.** The spec says "add them to the
`"Relay"` / `"Type generation"` [Browse by category] rows". Neither symbol appears in *both* rows: the
per-type `Meta` key sits under Type generation, the setting under Relay. Read as a distributive
assignment (each symbol to the row it belongs in) the contract is satisfied; read as "both symbols in both
rows" it is half-satisfied. The shipped arrangement is the one a reader is better served by, and the
glossary is out of fence in any case, so this is noted rather than raised.

### Contracted surfaces (`docs/README.md` / `docs/TREE.md` / `TODAY.md` / `README.md` — DoD item 7 second clause)

| # | Contracted | Verdict | Evidence |
|---|---|---|---|
| D1 | `docs/README.md` shipped-surface note | **landed** | `:80` — the model-anchored default, the per-type / schema-wide opt-out, the four strategies, and a cross-link to the glossary subsection. `:82` adds an un-contracted block quote on the multi-`DjangoType`-per-model collapse, which is the `_warn_model_label_secondary_collapse` behavior; **shipped doc surface beyond the contract, in the reader's favor** |
| D2 | `docs/TREE.md`: no new module | **landed** | `:288` / `:415` — `relay.py # Internal Relay helpers - interface injection, node resolver defaults, and GlobalID strategies.` No `types/globalid.py` exists, matching Decision 11 |
| D3 | `docs/TREE.md`: the `conf.py` settings note **if the layout reference enumerates settings keys** | **landed as a no-op; the conditional did not fire** | `:200` / `:323` read `conf.py # Package settings, read from the host project's ``DJANGO_STRAWBERRY_FRAMEWORK`` dict.` — the reference names the dict, never an individual key. `grep -n 'RELAY_GLOBALID' docs/TREE.md` → no matches, and no other settings key is enumerated either, so the obligation was correctly discharged by doing nothing |
| D4 | `TODAY.md` products `GlobalID`-filtering examples on the model label | **landed** | `:266` `exact: "<GlobalID: base64 of products.category:<pk>>"`; `:335` `categoryId: "<GlobalID: products.category:<pk>>"`. No `CategoryType:<pk>` filter example survives |
| D5 | `TODAY.md` breaking-wire-format note **including the `type+model`-first upgrade sequence** | **landed** | `:290` the breaking-change block quote (naming the `0.0.6` `BigInt` precedent); `:292`-`:294` the numbered 1-2-3 sequence; `:296` the load-bearing step-3 rename caveat, stating explicitly that `type+model` is **not** a rename-history alias map (`BACKLOG.md` item 39); `:298` the multi-type collapse hazard. `:14` carries the capability line. File stays products-centric |
| D6 | `README.md` status paragraph newest-shipped-surface line | **landed** | `:78` — the `0.0.9` release line names "model-anchored `GlobalID`s (`app_label.modelname:<pk>`, so type renames keep cached IDs valid)" |

**Cross-check run against D4/D6, since a wire-format claim's population is never the files a section
names** (Slice 4's lesson, applied to the doc tier): `grep -rn 'type_cls, model, root, info'` across
`docs/GLOSSARY.md`, `docs/README.md`, `TODAY.md`, `README.md`, `docs/TREE.md` → **no matches**. Every
external doc states the current three-arg callable contract; the only four-arg spelling in the tree is
`CHANGELOG.md`'s `## [0.0.9]` entry, which is historically correct (see C2). Likewise
`grep -rn 'docs/spec-031'` across the same five files plus `KANBAN.md` and `CHANGELOG.md` → **no
matches**: the pre-archival path survived only inside the spec, which is why no external gate ever saw it.

### Contracted surfaces (`CHANGELOG.md` — DoD item 7 third clause)

| # | Contracted | Verdict | Evidence |
|---|---|---|---|
| C1 | `### Changed` (breaking) bullet **prescribing the `type+model`-first upgrade sequence** | **landed** | `CHANGELOG.md:108`. Carries the model-label default, the `0.0.6` `BigInt` parallel, the per-type and schema-wide opt-outs, the ordered `"type+model"` → age-out → rename/flip sequence, the pointer to `TODAY.md` for the full sequence, and the multi-type collapse paragraph |
| C2 | `### Added` bullet for `Meta.globalid_strategy` / `RELAY_GLOBALID_STRATEGY` | **landed** | `CHANGELOG.md:98`, under `## [0.0.9]` `### Added` |
| C3 | Both under `[Unreleased]`, **no version-heading promotion** (Decision 12) | **landed as contracted; the heading moved later, and that is the joint cut's doing** | Graded with the stale-sentence test rather than called drift. `git show 7d892d6f -- CHANGELOG.md` shows both bullets written **under `[Unreleased]`**, replacing the staged `TODO(spec-031-globalid_encoding-0_0_9 Slice 5)` HTML-comment block, and promoting no release heading. They sit under `## [0.0.9]` today because the joint `0.0.9` cut promoted them — precisely what Decision 12 assigns to the cut. Case (c): the prediction held; only DoD item 7's present tense rotted. Reconciled in the spec, not deleted |

C2 states the callable as `(type_cls, model, root, info) -> str`. That is **correct for `0.0.9`** and not a
divergence: `CHANGELOG.md:33`, under `## [0.0.14]` `### Changed`, records dropping `info` as its own
breaking change. The two entries are consistent, and together they falsify a sentence *this cycle* wrote
into the spec — see finding S5-3.

### Contracted surfaces (`KANBAN.md` — DoD item 8)

| # | Contracted | Verdict | Evidence |
|---|---|---|---|
| K1 | The card is recorded as `DONE-031-0.0.9` | **landed** | `KANBAN.md:116` (the Done index row), `:3327` (the card heading, anchored into `KANBAN.html`), `:3334` (the card body). `:64` narrates the whole Relay cohort as shipped |
| K2 | The card body's spec reference points at this document | **landed, at the archived path** | `:3334` `- Spec: [spec-031-globalid_encoding-0_0_9.md](docs/SPECS/spec-031-globalid_encoding-0_0_9.md)`, and `:116` the same. `KANBAN.html` carries exactly one `spec-031` reference and it is the same archived path. The contract text named the pre-archival `docs/spec-031-…`; the archival sweep moved both the file and this pointer together, so K2 is satisfied against the file's real location. This is the KANBAN half of finding S5-1 |

### DoD item 9 — no version-file edits in this card

**Confirmed mechanically.** `git show --stat 7d892d6f` (the card's shipping commit, `Finish
build-031-globalid_encoding-0_0_9.md`) lists 35 files and **none** of `pyproject.toml`,
`django_strawberry_framework/__init__.py`, `tests/base/test_init.py`, or `uv.lock`. No `CHANGELOG.md`
release heading is promoted in that diff either (C3). The joint cut owns both, as Decision 12 says.

### DoD item 10 — the coverage posture claim

**Partially verifiable read-only; the rest is recorded as not-worker-verifiable rather than asserted.**

- `fail_under = 100` is present at `pyproject.toml:228`. Verified.
- Whether package coverage *is* at 100% cannot be established in this pass. Establishing it means running
  `pytest` with `--cov*`, which `docs/builder/BUILD.md` `## Coverage is the maintainer's gate, not a
  worker's tool` forbids in **every** worker pass. It is CI's gate and the maintainer's.
- The item's second half — "routine per-slice work does not run pytest locally; worker-local validation is
  `ruff format` / `ruff check --fix`" — is a process statement, not a repository fact, and matches
  `AGENTS.md` #"No pytest after edits". No divergence.

Saying so is the point: an unverified claim asserted as verified is a Medium finding under `## Claims are
proven mechanically, never accepted on prose`, and "coverage is at 100%" is exactly the shape that reads
as measured when nobody measured it.

### DoD item 1 — the spec + companion CSV

**Landed, and the spec sentence describing it was false.** Both `Meta.globalid_strategy` and
`RELAY_GLOBALID_STRATEGY` carry `docs/GLOSSARY.md` headings (G1/G2) **and** rows in
`docs/SPECS/appx/spec-031-globalid_encoding-0_0_9-terms.csv`, which is why
`uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-031-globalid_encoding-0_0_9.md`
reports `OK: 31 terms` rather than 29. The doc surface is correct; the *spec sentence* was not, and that
half is in fence — finding S5-2.

---

## Divergences found (the shipped state is the truth; the spec was rewritten)

Three findings, all spec-internal. **No external doc surface diverged**, so this slice contributes no
doc-surface item to the deferred catalog.

### S5-1 — the pre-archival spec path, asserted at five sites in three grammars

Routed forward by Slice 0 and unclaimed through Slices 1-4. The population was **re-derived, not
inherited**: Slice 0 named spec lines 250 / 567 / 84 / 542 / 589 pre-edit, and four slices of editing had
moved every one of them. `grep -n 'docs/spec-031'` over the current file returns **five lines carrying
seven occurrences** (line 572 carries three: the DoD item's link text, the companion-CSV filename, and the
quoted `check_spec_glossary.py` invocation).

The reference-style `[spec-031]` definition was correct at every site. That is why nothing broke and why
no gate flagged it: **a stale path inside link *text* is invisible to every link checker in the repo,
because a checker follows the definition.** My own anchor/fragment validators confirm it — they reported
zero dangling links both before and after this pass.

Graded with the stale-sentence test rather than string-replaced, because Decision 1 is not the same
sentence as a cross-reference:

- **Decision 1's body — case (c).** A true prediction (the file did live at `docs/` when written) whose
  enduring implication the `docs/SPECS/NEXT.md` Step-8 archival sweep falsified. Decision 1's *subject* is
  the canonical structured **filename**; the directory was never its decision. Reconciled to that scope
  boundary: the Decision now pins the filename and its two same-stem companions, and names the
  `AGENTS.md` archival convention as the owner of the directory, stating the current locations as fact.
  Neither deleted nor left verbatim.
- **The four contract sentences — case (b).** The Slice-5 `KANBAN.md` checklist bullet, the `## Doc
  updates` card-completion bullet, DoD item 1, and DoD item 8 are cross-references telling a reader where
  to look. Each now refers to "this document" and lets the `[spec-031]` definition carry the path, so a
  future archival move breaks none of them.

### S5-2 — DoD item 1's false terms-CSV claim, and the same claim in three more homes

DoD item 1 said the two net-new symbols "have **no** glossary heading yet … so they are intentionally
absent from the CSV and tracked as the first [Risks and open questions] item". Every clause is now false:
both headings exist, both CSV rows exist, and the spec's `## Risks and open questions` no longer carries
items at all (Slice 0 moved them to the companion), so the ordinal pointer resolves to a section that does
not contain what it promises.

**The falsifier was the card itself, not a later card.** `git show 7d892d6f --
docs/spec-031-globalid_encoding-0_0_9-terms.csv` shows the card's own shipping commit adding both rows,
alongside its 59-line `docs/GLOSSARY.md` edit. So a *closure* contract was falsified by the very slice
contracted to satisfy it, and survived the card's own wrap plus five releases. Case (b), reconciled.

The population is **four homes, not one**: DoD item 1, the Slice-5 GLOSSARY checklist bullet (line 78),
the `## Doc updates` GLOSSARY bullet (line 539), and the `## Implementation plan` table's row 5. The first
carried the false claim; the other three carried the *incomplete* version of the same contract — they name
the glossary entries as Slice 5's deliverable and omit the CSV rows, which the checker's own rule makes
inseparable from them. All four now state the coupling: the headings and the rows land in the **same**
change, because `check_spec_glossary.py` rejects a CSV term whose heading does not yet exist. That
constraint is what made the original wording correct while it was written, and stating it is what stops a
future reader re-deriving the "absent" conclusion.

### S5-3 — a dated claim this cycle wrote, wrong on its own date (case (d))

Not routed to me; found by the end-to-end consistency re-read this slice owes.

Decision 6 read: "a wrong-arity callable (e.g. `(type_cls, model)`, or **the pre-`0.0.9` four-arg**
`(type_cls, model, root, info)` shape [Decision 4] dropped `info` from)". The four-arg shape is not
pre-`0.0.9` — it is what `0.0.9` **published**. `CHANGELOG.md:98` (`## [0.0.9]` `### Added`) ships the
callable as `(type_cls, model, root, info) -> str`, and `CHANGELOG.md:33` (`## [0.0.14]` `### Changed`)
records dropping `info` as a breaking change. The rationale companion's own `## Revision history` agrees:
Revision 7's three deltas are the post-ship `0.0.14` hardening, and delta (b) is the `info` drop. So the
four-arg shape is the `0.0.9`-through-`0.0.13` contract.

`git show HEAD:docs/SPECS/spec-031-globalid_encoding-0_0_9.md` carries no "four-arg" phrase in Decision 6
at all, so **this sentence was authored by this cycle** (Slice 1, and echoed into its rationale bullet).
Reconciled to "the **superseded** four-arg shape", asserting no date; the dating lives in the companion.

The generalizable half, recorded in the companion: **a dated claim written during reconciliation is not
protected by the reconciliation.** Slice 4 extended the stale-sentence test with case (d) for a sentence
the *spec author* got wrong on its date. This is case (d) one level in — a sentence a *reconciling slice*
got wrong on its date — and it is structurally harder to catch, because each slice grades the sentences it
inherits and nobody grades the ones it writes. The final functional slice is the only pass positioned to.

---

## Spec changes made (Worker 1 only)

Eight edits to `docs/SPECS/spec-031-globalid_encoding-0_0_9.md`, all Slice 5. Line numbers are
pre-edit anchors.

| # | Spec site | Change | Reason | Finding |
|---|---|---|---|---|
| 1 | line 9 (`Predecessors`, tail clause) | "it does **not** yet carry `Meta.globalid_strategy` or `RELAY_GLOBALID_STRATEGY` entries … see Risks and open questions" → "it also carries [both] as `shipped (0.0.9)` … whose entries and companion-CSV rows Slice 5 authors" | The clause carried no date marker (unlike lines 78 / 539, which say "at spec-authoring time" and are licensed case-(a) observations) and pointed at a `## Risks and open questions` section that no longer holds the item. Now states the shipped fact and links both glossary anchors | S5-2 |
| 2 | line 250 (`Decision 1` body) | "The spec file lives at **`docs/spec-031-globalid_encoding-0_0_9.md`**" → the canonical **filename** plus both same-stem companions, with the directory attributed to the `AGENTS.md` archival convention and the current `docs/SPECS/` + `docs/SPECS/appx/` locations stated | Case (c): the Decision's subject is the naming convention; only the location claim rotted. Reconciled to the scope boundary rather than deleted or left verbatim | S5-1 |
| 3 | line 84 (Slice-5 `KANBAN.md` checklist bullet) | Bare `docs/spec-031-…` path → "this document ([`spec-031-globalid_encoding-0_0_9.md`][spec-031], at whatever path the `AGENTS.md` archival convention has it under)" | Case (b): a cross-reference telling a reader where to look. The `[spec-031]` def now carries the path alone | S5-1 |
| 4 | line 547 (`## Doc updates` card-completion bullet) | Same substitution | Same claim, second home | S5-1 |
| 5 | line 572 (`## Definition of done` item 1) | Whole item rewritten: path removed from link text and from the quoted invocation; `OK: <N> terms` → `OK: 31 terms`; the "no glossary heading yet / intentionally absent from the CSV / the first Risks item" clauses replaced by the current contract and the checker constraint that couples headings to rows | Case (b) on the CSV claim + S5-1's two path occurrences + a dangling ordinal pointer into a section Slice 0 emptied | S5-1, S5-2 |
| 6 | line 593 (`## Definition of done` item 7, CHANGELOG clause) | "`[Unreleased]` carries the … bullets" → "gains the … bullets, written under `[Unreleased]` …; the joint `0.0.9` cut, not this card, later promotes them under the release heading (Decision 12)" | Case (c): the prediction held (`7d892d6f` wrote them under `[Unreleased]` and promoted nothing); only the present tense rotted against a CHANGELOG a reader can open. DoD item 9's "no release heading is promoted" is a claim about the card and needed no change | C3 |
| 7 | line 594 (`## Definition of done` item 8) | Bare `docs/spec-031-…` path → "this document ([`spec-031-…`][spec-031]) at its current path" | Case (b), fifth and last path home | S5-1 |
| 8 | line 302 (`Decision 6`, callable bullet) | "the **pre-`0.0.9`** four-arg `(type_cls, model, root, info)` shape" → "the **superseded** four-arg … shape" | Case (d): false on its own date, and authored by this cycle. The Decision now asserts no date; the dating is recorded in the companion | S5-3 |

Three further edits keep the S5-2 contract consistent across the homes that restate it — the population
sweep this slice owes rather than fixing only the site it was handed:

| # | Spec site | Change | Reason |
|---|---|---|---|
| 9 | line 78 (Slice-5 GLOSSARY checklist bullet) | Appended ", together with their [companion-CSV] rows in the **same** change, since `check_spec_glossary.py` rejects a CSV term whose heading does not yet exist" | The bullet named only the glossary entries. The dated "do not exist at spec-authoring time" clause is a verified case-(a) observation (`git show b1f82f0e:docs/GLOSSARY.md` has no such heading) and was left standing |
| 10 | line 539 (`## Doc updates` GLOSSARY bullet) | Same coupling appended | Second home of the same incomplete contract |
| 11 | line 420 (`## Implementation plan` table, row 5 "Files touched") | Added the companion terms CSV to Slice 5's file list, with the coupling noted parenthetically | Row 5 listed seven doc files and omitted the CSV the card's own commit touched — the third home, and the one a planner reads |

### Rationale companion entries appended

Four `**Post-ship:**` bullets in
`docs/SPECS/appx/spec-031-globalid_encoding-0_0_9-rationale.md`, append-only, each keyed to the spec
Decision or section it belongs to by heading and anchor, in the convention Slices 1-4 established:

1. **`## Decision 1` → `### Changes this Decision underwent`** — the location claim reconciled; the
   population was five lines in three grammars, not the one site the Slice-0 bullet named; and the
   invisibility rule: a stale path inside link *text* is invisible to every link checker in the repo,
   because a checker follows the definition. Records why the fix removes the path rather than replacing
   it.
2. **`## Decision 6` → `### Changes this Decision underwent`** — the four-arg dating corrected against
   both CHANGELOG entries, with the case-(d)-in-the-small lesson: a dated claim written *during*
   reconciliation is graded by nobody, because a slice checks the sentences it inherits, not the ones it
   writes.
3. **`## Decision 12` → `### Changes this Decision underwent`** — the `[Unreleased]` clause as a
   third-case sentence: the prediction held, the joint cut moved the heading, and the DoD item now states
   the boundary it was really expressing. Carries the `git show --stat 7d892d6f` evidence for DoD item 9.
4. **`## Risks and open questions`** — item 1 closed, naming the card's own commit as the falsifier and
   the checker constraint that made the original wording correct; plus the generalization that a
   definition-of-done item describing the pre-build repo is self-defeating by construction, and the wrap
   slice is the one pass positioned to notice.

Two link definitions were added to the companion to support these bullets, in their canonical groups and
alphabetical position: `[package-init]` under `<!-- django_strawberry_framework/ -->` and
`[check-spec-glossary]` under the previously-empty `<!-- scripts/ -->`.

---

## Staged-anchor sweep (`worker-1.md` final-verification step 6)

This is the doc-wrap slice, so it owns the standing-authority sweep
(`docs/builder/BUILD.md` `## Cross-slice integration pass` step 6).

```shell
grep -rEn 'TODO\(spec-031|TODO-(ALPHA|BETA|STABLE)-031' . \
  | grep -v '^\./\.git/' | grep -v 'KANBAN.md\|KANBAN.html\|BACKLOG.md'
```

**Result: no surviving anchor in any shipped source, test, or comment.** Six hits, every one prose
*describing* an anchor rather than being one:

- `docs/SPECS/spec-031-…md:76` and `:419` — the spec's own Slice-4 text recording that the anchor "is
  removed by this slice";
- `docs/SPECS/appx/spec-031-…-rationale.md:408` — Slice 4's post-ship bullet recording the same deletion;
- `docs/builder/bld-031-slice-0-…md:233` and `bld-031-slice-4-…md:80` — prior artifacts' own sweeps;
- `docs/SPECS/appx/spec-022-export_schema-0_0_7-rationale.md:350` — a **card-renumber history row**
  (`| Debug-toolbar middleware | TODO-ALPHA-031 for 0.0.12 | DONE-042-0.0.14 |`). It names a *different*
  card that once held the number 031, in a table whose purpose is to record the renumber. Not a staged
  anchor, and out of fence.

The board files excluded by the rule carry no `031` anchor either. This confirms Slice 4's finding that
`examples/fakeshop/apps/products/schema.py`'s anchor was deleted by the shipping commit `7d892d6f`
(`-7` lines on that file), discharging `AGENTS.md` rule 26.

---

## Internal-consistency re-read (this is the last slice)

Four slices each rewrote their own region, and this cycle has already found one contract wrong in five
homes at once. The whole spec was re-read end to end for contradictions the cycle itself introduced, with
these mechanical cross-checks on the claims that live in more than one home:

| Check | Command / method | Result |
|---|---|---|
| Signature spellings agree across every home | `grep -on 'install_globalid_typename_resolver([^)]*)' \| sort -u` and the same for `_validate_globalid_strategy` / `_resolve_globalid_strategy` | One spelling each. `install_…(type_cls, definition, globalid_setting)` at 2 sites; `_validate_globalid_strategy` in its two licensed forms (the `meta` definition and the `source="setting"` call) at 4 sites; `_resolve_globalid_strategy(definition, globalid_setting)` at 6. Slice 0's arity contradiction stays closed |
| The fail-closed filter contract, the five-homes case | grep each of `GLOBALID_UNVALIDATABLE`, "known `None`", `_audit_globalid_filter_strategies`, "unbound-owner" and compare the line sets | Consistent across the Slice-2 checklist, both Error-shapes bullets, Decision 13, the plan table, Edge cases, the filter/finalizer test lists, and DoD item 4. Every home carries the same split: the build-time audit keys on the two encode-only names, the runtime backstop additionally rejects a known `None`, and only the unbound-owner case keeps node-id-only |
| Census claims (`the only` / `the one` / bare singulars) | grep the quantifiers **and** the subject | The one survivor, Decision 10's shadow-install sentence, is correctly scoped to "during `id` resolution" and states the `testing/relay.py::global_id_for` carve-out in the same sentence — Slice 2's fix holding |
| Chronology residue after the Slice-0 move | `grep -nE 'Revision [0-9]\|review finding\|Rev [0-9]\|\(P[0-9]'` | Zero. The spec narrates none of its own history |
| Pre-archival paths | `grep -n 'docs/spec-031'` | Zero after edit 7 |
| Four-arg callable dating | cross-read against `CHANGELOG.md` `## [0.0.9]` and `## [0.0.14]` | The one inconsistency in the cycle's own output; fixed as S5-3 |
| `31 terms` | asserted in exactly one home (DoD item 1) after edit 5 | Measured, not carried forward |

No other cross-region contradiction survives.

---

## Plan declarations

- **Hot-path declaration:** `none`. This slice writes no code and plans none. Deliberate, not silence.
- **Floor-verification scope:** `none`. It touches no Django / Strawberry / channels seam.
- **Ownership partition:** `none; sequential slices`.
- **Boundary count:** 0. No guard, cap, rejection path, or validation branch is added, so no failability
  proof is owed and no split question arises.
- **`scripts/review_inspect.py`:** not run, and the skip is recorded with its reason — the helper's
  triggers are all `.py`-file triggers (`docs/builder/BUILD.md` `### When to run the helper during
  build`), and this slice plans no change to any `.py` file.

---

## Final verification checks run

| Check | Command | Result |
|---|---|---|
| Spec/glossary gate | `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-031-globalid_encoding-0_0_9.md` | `OK: 31 terms` — before **and** after the edits. Edits 1 and 5 add glossary links rather than removing any, so no CSV term was orphaned |
| In-page anchors, both files | AST-free slugger over every non-fenced heading vs every `](#…)` use | 0 dangling, before and after |
| Reference-style link defs, both files | undefined ref-ids / unused defs / defs whose file is missing | 0 / 0 / 0, before and after. The two defs added to the companion are both used |
| Cross-file link **fragments** | every `path#fragment` def resolved against the target file's real headings | 0 dangling, before and after — including all 13 `[rationale-dN]` spec→companion pairs and the companion's `[spec-031-*]` pairs back |
| Markdown scaffold / layout | `uv run python scripts/check_trailing_commas.py --check <both files>` | exit 0 |
| Working tree | `git status --short` | Only this cycle's six paths. Nothing outside the fence touched; nothing reverted |

No `pytest` run: this slice changes no code and no test, so there is no focused scope to run
(`worker-1.md` final-verification step 5). No `--cov*` flag was used anywhere in this pass.

---

## Worker 2 dispatch

**None.** The CODE GAP list is empty and no source or test edit is judged necessary by this slice. Per the
build plan's `## Dispatch rule for this cycle` the slice closes by procedural closure. The three findings
were all spec-internal and therefore mine to fix in this pass; the doc-surface audit produced no
divergence at all, and a doc-surface divergence would in any case be a deferred-catalog item rather than a
Worker 2 dispatch, the external doc surfaces being outside the maintainer's fence entirely.

---

## Deferred to `### Deferred work catalog` (for `bld-031-final.md`)

Slice 5 contributes **no new item**. Every contracted doc surface landed, so there is no doc-surface
divergence to record, and the two findings routed forward since Slice 0 are discharged here rather than
handed on — this was their last functional-slice chance and they were taken.

Two observations are recorded for the final gate's catalog author without being defects:

- **The G4 Browse-by-category ambiguity** (above) — the spec's `"Relay" / "Type generation"` slash admits
  two readings and the glossary satisfies the better one. Worth a sentence in the catalog only if the
  maintainer wants the slash disambiguated in a future spec's template; nothing to fix here.
- **`TODAY.md:14` needs no change.** Slice 4 flagged it for this audit: its "own-PK GlobalID filtering,
  `node(id:)` refetch shape" phrasing is what the spec's `## Current state` mis-borrowed and
  re-attributed to the live tier's assertion set. Read on its own terms it describes the Relay
  *capability*, and both halves of that capability have shipped, so it is accurate. Recorded so the
  catalog does not inherit S2 as a phantom doc obligation.

The catalog items still open from earlier slices are unchanged by this pass and are listed here only so
the final gate can walk one list:

- **Four stale `.py` docstring/comment clauses, batched** (Slices 2 and 3) —
  `types/definition.py::DjangoTypeDefinition` #"the filter falls back to node-id-only validation";
  `types/relay.py::encode_typename` and `::_install_typename_closure`, both carrying the falsified
  `type`-branch exclusivity claim; and `types/relay.py::decode_global_id` #"WIP-ALPHA-032-0.0.9".
  Comment-only, nothing behavioral rests on them, and the spec now states the correct contract in every
  home. Batched because `### Isolation is non-waivable` makes even a one-line comment fix a two-spawn
  cycle.
- **`_first_model_label_emitter` / `_audit_model_label_routing` no-definition raises** (Slice 2) —
  shipped internal-consistency guards with no spec sentence, deliberately left uncontracted.
- **Two `spec-032` cross-references into text this cycle moved** (Slice 0) —
  `docs/SPECS/spec-032-full_relay-0_0_9.md` lines 13 / 281 / 452 cite a `spec-031` Revision 7 and two
  Decision-level rejected alternatives that now live in the companion. `spec-032` is out of this cycle's
  fence entirely; owner is the maintainer or a future `032` cycle.

---

## Summary

Slice 5's contracted wrap **landed in full**: both net-new glossary entries as `shipped (0.0.9)` with
Index and category rows and an extended `Relay Node integration` body; the `docs/README.md`,
`docs/TREE.md`, `TODAY.md`, and `README.md` shipped-surface and breaking-format notes; the `CHANGELOG.md`
`### Changed` bullet prescribing the `type+model`-first upgrade sequence plus its `### Added` sibling; the
`DONE-031-0.0.9` card with a working spec reference; no version-file edits; and both companion-CSV rows.
CODE GAP list **empty**.

The audit-only half produced no divergence. The in-fence half discharged the two findings routed forward
unclaimed since Slice 0 — the pre-archival spec path (five sites, seven occurrences, re-derived rather
than inherited) and DoD item 1's false terms-CSV claim (four homes, and falsified by the card's own
shipping commit) — and found a third the end-to-end re-read owed: a "pre-`0.0.9`" dating **this cycle**
wrote into Decision 6, which both CHANGELOG entries falsify. Eleven spec edits, four rationale bullets,
two companion link definitions. Staged-anchor sweep clean. `check_spec_glossary` `OK: 31 terms`; zero
dangling anchors, fragments, or link defs in either file.

### Final status

`final-accepted`. Procedural closure; no Worker 2, no Worker 3.

<!-- LINK DEFINITIONS -->

<!-- Root -->

[changelog]: ../../CHANGELOG.md
[kanban]: ../../KANBAN.md
[readme]: ../../README.md
[today]: ../../TODAY.md

<!-- docs/ -->

[docs-readme]: ../README.md
[glossary]: ../GLOSSARY.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->

[spec-031]: ../SPECS/spec-031-globalid_encoding-0_0_9.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
