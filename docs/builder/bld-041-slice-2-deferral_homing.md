# Build: spec-041 slice 2 — deferral homing and the cross-surface range claim

Spec reference: `docs/SPECS/spec-041-channels_router-0_0_14.md`
Status: final-accepted

Cycle type: continuation of the **post-ship reconciliation round** recorded in
`docs/builder/build-041-channels_router-0_0_14.md`. Slice 1 closed the spec / companion
reconciliation; this slice discharges the deferral catalog that slice's final gate produced
(`docs/builder/bld-041-final.md` `## Deferred work catalog`), under a writable set the maintainer
widened at dispatch to include the fakeshop board and glossary databases.

---

## Scope, and how it differs from slice 1

Slice 1 could not write four of the surfaces its own findings named: the glossary is rendered from
a database, `spec-042` belongs to another card, `pyproject.toml` is packaging metadata, and the
board is a database. Three of those four are now in scope. The fourth, `pyproject.toml`, is not,
and its one site is homed rather than edited.

Writable in this slice: `docs/SPECS/*.md`, `django_strawberry_framework/**/*.py`, the fakeshop
`kanban` and `glossary` databases plus the documents rendered from them. Out of scope and
untouched: `pyproject.toml`, `uv.lock`, `TODAY.md`, `BACKLOG.md`, `CHANGELOG.md`, every file under
`docs/builder/DONE/`, and the process documents (`BUILD.md`, `ARTIFACT.md`, `worker-*.md`).

No Worker 2 pass again, for the reason slice 1 recorded: no `.py` file needed to change, and a
spec is Worker-1 property. Worker 0 measured, Worker 1 executed, Worker 3's grading rules were
applied to Worker 0's own counts — see `## The count error this slice made, and caught`.

---

## What the catalog asked for, and what each item got

| Catalog item | Disposition |
|---|---|
| 1 — the Channels-floor vs `Framework :: Django :: 6.1` dependency decision | Homed on the boundary-hardening / DRY-squeeze card, `scope`, as a decision covering **all three** soft-dependency floors rather than the channels one alone |
| 2 — three parallel sites riding that answer | Two corrected here (`docs/GLOSSARY.md` via the DB, `spec-042` in place); the `pyproject.toml` comment folded into item 1's row. The catalog's count of these sites was wrong and is corrected in `bld-041-final.md` |
| 3 — the board-owned card-id renumber | Census amended with a dated re-measurement; the second, never-enumerated population given a row of its own |
| 4 — the ungated `-terms.csv` `notes` column | Already homed on the alpha documentation-debt card. No action; re-verified present |

---

## Finding: the range claim was a five-site population, not a three-site one

`bld-041-final.md` item 2 measured the phrase `whole advertised Django range` and reported the
result as the claim population. Those are different sets. Re-measured 2026-09-11:

| Site | Spelling | Verdict |
|---|---|---|
| `docs/GLOSSARY.md` router entry | *one floor covering the package's whole advertised Django range through 6.0* | false |
| `spec-042` `## Slice checklist` | *one floor for the whole advertised Django range* + *advertises `Framework :: Django :: 6.0`* | false, twice |
| `spec-042` `### Error shapes` | *covers the package's whole advertised Django range (through 6.0)* | false |
| `spec-042` Decision 5 body | *covers the package's advertised Django 6.0 range* + *classifiers 5.2 + 6.0* | false, twice |
| `spec-042` `## Definition of done` | *covering the advertised Django range through 6.0* | false |

Five sites, of which the phrase reaches three. Two of the five sit in homes the *five homes* rule
requires to agree with the Decision, so a phrase-scoped sweep would have left the Decision body
and the definition of done contradicting the checklist it governs.

### Why the claim is false, and why the two soft dependencies differ

Measured against installed metadata and PyPI on 2026-09-11:

- `pyproject.toml` advertises `Framework :: Django :: 5.2`, `6.0` **and** `6.1`.
- `channels` at the floor `django_strawberry_framework/utils/imports.py` #"CHANNELS_FLOOR = "
  carries classifies Django 4.2 / 5.1 / 5.2 / 6.0. That release is also the latest published, so
  **no released Channels version classifies 6.1 at all** — the gap cannot be closed by a bump, and
  prose is the only lever.
- `django-debug-toolbar` `7.0.0` classifies 5.2 + 6.0; `7.1.1`, already what the dev group
  resolves to, classifies 5.2 / 6.0 / 6.1. Here a bump **would** close the gap.

The two cases look identical in the specs and are not, which is why the decision is homed as one
row naming both rather than two rows. The corrections state only the verified reach — *the floor's
Django coverage reaches 6.0 and stops short of the `6.1` the package also advertises* — and stay
true whichever way the packaging call goes.

---

## Finding: the second stale card-id population had no board home

The board's census row owns the fakeshop-activation id and has been re-measured four times. Its
sibling — the migration-and-adoption-guides id — was never enumerated anywhere on the board,
despite sitting in three of the same files and originating in the same 2026-08-29 inserts. Both
ids are wrong in **both** halves: the numeral names a different card, and the version suffix names
a different release line, so no uniform shift repairs either.

Measured 2026-09-11 over every tracked file, by byte occurrence, before the new row existed:

| Population | Text-file occurrences | Board renders | Sweepable |
|---|---|---|---|
| fakeshop-activation id | 45 across 13 files | 4 | 41 |
| migration-guides id | 11 across 5 files | 0 | 11 |

Not swept here. The census's own standing rule is that one owner takes all of it in a single pass,
and 11 of the fakeshop-activation population's sweepable sites sit in files this slice may not
write (`TODAY.md` 3, `docs/builder/DONE/` 5) or that need a per-site read against a live referent
(`BACKLOG.md` 1, `docs/builder/DONE/` 2 on the guides side). A spec-only share would leave each
spec disagreeing with the standing docs quoting it — the partial claim fix the final artifact
already names as the dominant residual defect.

---

## The count error this slice made, and caught

The first draft of the census amendment was written from a shell pipeline that reported **46**
occurrences while its own per-file listing summed to **45**, and the draft closed the gap with an
invented `build-027` clause rather than resolving it. Caught on read-back, before the render.

The gap was the instrument, not the data: `grep` stops counting a binary file after the first
match, so `examples/fakeshop/db.sqlite3` contributed 1 to the total line and 0 to the per-file
listing. Re-measured in Python by byte count, the board database holds **3** occurrences where the
ORM returns **2** — one dead freelist page, exactly the residue the census row already warns
about. Every figure written to the board was re-derived with that instrument and re-verified after
the render.

Standing form of the lesson, already in the census row and now demonstrated against it: a total
and a breakdown produced by different instruments must be reconciled before either is published,
and a discrepancy of one is never rounding.

---

## Changes

**`docs/SPECS/spec-042-debug_toolbar-0_0_14.md`** — four edits, one per home. The slice checklist
now names all three advertised classifiers; the error-shapes paragraph, the Decision 5 body and
the definition of done each state the floor's reach instead of a whole-range promise. The
`7.0.0`-is-first-with-the-6.0-classifier fact is true and untouched everywhere it appears.

**`docs/GLOSSARY.md`** — one `GlossaryTerm` body edit against the fakeshop glossary database,
re-rendered with `scripts/build_glossary_md.py`. Never hand-edited.

**Board database**, four writes, re-rendered with `scripts/build_kanban_md.py` and
`scripts/build_kanban_html.py`:

- boundary-hardening / DRY-squeeze card, new `scope` row: the three-floor decision, both cases
  stated with their metadata, the `pyproject.toml` comment folded in, and the reason this card
  rather than the release card (which excludes version floors by name).
- alpha documentation-debt card, census row amended: dated re-measurement, corrected `docs/SPECS/`
  and `spec-041` shares, the freelist figure, five newly graded decided non-edits, and the 36
  sites still owing a per-site read.
- alpha documentation-debt card, new `scope` row: the migration-guides population, per-file, with
  its own board-side occurrence declared and excluded from its own total.
- migration-and-adoption-guides card, new `scope` row: the router migration row's content — the
  three constructor divergences and the separate URLconf entry — which previously existed only as
  a symbol-mapping reference edge.

**`docs/builder/bld-041-final.md`** — the deferral catalog's item 2 corrected (phrase count read
as claim count; inverted "row above it"), items 2 and 3 marked discharged, and a disposition
paragraph added naming where each of the four now lives.

---

## Verification

Re-measured after the render, in Python by byte count over every tracked file:

- fakeshop-activation id: 45 text-file occurrences across 13 files, unchanged — the new rows
  spell that id only as a bare backticked numeral. Board database 3 bytes against 2 ORM rows.
- migration-guides id: 13 text-file occurrences across 7 files, up from 11 by exactly the two
  renders of the one new row; 14 including the database byte, which is the figure that row
  predicts of itself in advance.
- `whole advertised Django range`: **0** outside this cycle's own artifacts.
- `advertised Django range` in `spec-042`: 0. In `spec-041`: 2, both re-read and both stating the
  verified reach.

Gates, all green: `scripts/check_trailing_commas.py --check` over the touched paths;
`scripts/check_citations.py` (983 citations resolve, 169 in `KANBAN.md`);
`scripts/check_kanban_anchors.py`; `--check` on all four generators;
`scripts/check_spec_glossary.py` on both touched specs.

No `pytest`, for slice 1's recorded reasons, both still true: no `.py` file changed in this slice,
and the tree carries a concurrent cycle's in-flight source edits.

---

## Working-tree disposition

Added by this slice: this file. Modified by this slice:
`docs/SPECS/spec-042-debug_toolbar-0_0_14.md`, `docs/GLOSSARY.md`, `KANBAN.md`, `KANBAN.html`,
`examples/fakeshop/db.sqlite3`, `docs/builder/bld-041-final.md`.

One disclosure about the rendered glossary. `docs/GLOSSARY.md` and the database were both already
modified by the concurrent `spec-050` session when this slice began. The generator is
deterministic — rendering from `git show HEAD:examples/fakeshop/db.sqlite3` reproduces `HEAD`'s
`docs/GLOSSARY.md` byte for byte, verified — and the rendered file now differs from `HEAD` at
exactly three lines: this slice's router entry, plus two entries belonging to that session. Those
two were already in the working database before this slice touched anything, so the render carried
them rather than creating them; whether that session had already rendered them cannot be
recovered, so if it had not, this render published them early. Nothing else rode along.
`KANBAN.md` and `KANBAN.html` carry four hunks, all this slice's.

Nothing is committed. Only the maintainer commits.

## Final status

`final-accepted`.
