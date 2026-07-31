# Build: Final test-run gate (card 044, debug_extension / 0.0.14 — residual-completion cycle)

Spec reference: `docs/SPECS/spec-044-debug_extension-0_0_14.md` (archived by item R3 of this cycle; 185,710 bytes) with `-terms.csv` (4,940) and `-rationale.md` (43,868) beside it
Build plan: `docs/builder/build-044-debug_extension-0_0_14.md`
Date: 2026-07-31
Status: final-accepted

This is a **gate artifact**, not a slice artifact, so it takes the shape `BUILD.md` `## Final test-run gate` prescribes: the command-by-command record, the `### Deferred work catalog`, the cross-artifact read folded in from the un-run integration pass, `### Summary`, and `### Spec changes made (Worker 1 only)`.

**`HEAD` moved during this pass**, from `05a08e31` (R3's close) to **`43f1f9f7`** — the maintainer committed the concurrent spec-046 work at 13:40:42, mid-gate. Every gate command below ran at `05a08e31`; the four fast read-only ones were re-run at `43f1f9f7` and are unchanged. The move is attributed in `### The baseline moved mid-pass: the maintainer committed at 43f1f9f7`, and it does not change a single result — it *retires* the baseline exception rather than exercising it.

---

## Gate command record

Every command in `BUILD.md` `## Final test-run gate`, in the order that section gives, with its real
result. No `--cov*` flag ran in this pass or in any pass of this cycle; no `--fix`; no write-mode
regenerate; no `git stash` / `checkout` / `restore` / `worktree`.

| # | Command | Result | Evidence |
|---|---|---|---|
| 1 | `uv run pytest --no-cov` | **PASS** | `5276 passed, 40 skipped in 58.96s`, exit 0. Python 3.14.2, Django 6.0.5, pytest 9.0.3, 8 xdist workers, 5314 items collected across all four `testpaths` (`tests`, `examples/fakeshop/tests`, `examples/fakeshop/test_query`, `examples/fakeshop/apps`). Full log at `docs/builder/temp-tests/044-final/pytest-full.log`. |
| 2 | `uv run python examples/fakeshop/manage.py check` | **PASS** | `System check identified no issues (0 silenced).`, exit 0. |
| 3 | `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` | **PASS** | `No changes detected`, exit 0. |
| 4 | `uv run ruff format --check .` | **PASS** | `405 files already formatted`, exit 0. The `COM812`-conflicts-with-formatter warning is a standing configuration notice, not a finding, and is present at HEAD. |
| 5 | `uv run ruff check .` | **PASS** | `All checks passed!`, exit 0. |
| 6 | `git diff --check` | **PASS** | no output, exit 0 — no whitespace error and no conflict marker anywhere in the tree. |
| 7 | `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-044-debug_extension-0_0_14.md` | **PASS** | `OK: 42 terms - all have glossary entries and at least one spec link.`, exit 0 — **re-run at the new archived path**, which is the reading the cycle owed. `--terms` defaults to a sibling of `--spec`, so the CSV was picked up at `docs/SPECS/` without a flag. |

**Every gate command passes.** Nothing is failing, so the recorded baseline exception is invoked for
nothing; see `## The baseline exception is recorded and moot` below, which matters because a moot
exception and an exercised one are different facts about the tree.

All seven ran at `05a08e31`. Commands **2, 4, 5, and 6** were then re-run unchanged at `43f1f9f7` after
the maintainer's mid-pass commit; command 1 was not re-run because the commit changed no working-tree
byte, which is proved rather than assumed in the attribution section below.

### Supplementary read-only confirmations (not part of the narrow gate)

Cheap, read-only, and they confirm nothing drifted between R3's close and this pass — which is the
only thing that could have silently invalidated R3's recorded figures:

| Command | Result |
|---|---|
| `uv run python examples/fakeshop/manage.py import_spec_terms --check` | `OK: 46 done cards have glossary links.` |
| `uv run python scripts/build_kanban_md.py --check` | `KANBAN.md is up to date.` |
| `uv run python scripts/build_kanban_html.py --check` | `KANBAN.html is up to date.` |
| `uv run python scripts/build_glossary_md.py --check` | `docs/GLOSSARY.md is up to date.` |
| `uv run python docs/builder/temp-tests/044-r2/link_audit.py <both moved files>` | spec: 35 headings, 200 in-page uses / 26 distinct / **0 broken**, 102 defs, 0 unused, **0 cross-file failures**. Rationale: 20 headings, 2 uses / 2 distinct / 0 broken, 28 defs, 0 unused, **0 cross-file failures**. The `"sql"` undefined is the standing false positive (`res.extensions["debug"]["sql"]`). |

Byte counts re-measured at the archived path and identical to R3's record: **185,710** / **43,868** /
**4,940**. `SpecDoc` for card 44 reads `path` `docs/SPECS/spec-044-debug_extension-0_0_14.md` and the
derived `url` follows it.

### Floor verification

**No floor-verification scope declared.** The build plan's preamble declares
`Floor-verification scope: none.` — no residual item touches a Django / Strawberry / channels
integration seam. The cycle edited a spec, its rationale sibling, cross-references, and DB-rendered
docs, and ran management commands against the example project, which is not a version-dependent seam.
**No floor venv was built and none was owed**; the shared `.venv` was not mutated. Each item's artifact
carries the matching `Not applicable; plan declares floor-verification scope none.` and none deferred a
floor run to this gate, so there is no unrun floor claim for the backstop to catch.

### Hot-path budget and failability proofs

Both `none` by plan declaration and both discharged rather than skipped. The plan declares
`Hot-path declaration: none.` — no residual item changes package source, so no item runs per request,
per resolver, per row, per connection, or per outbound message. Failability: **this cycle wrote no
tracked `.py` file at all**, so its boundary count is 0 arithmetically rather than by judgement, and
the three item artifacts each carry `None; this pass introduced no new boundary.` Read the whole
tracked diff for the catalogued fail-open shapes anyway: the only expression-bearing tracked change
this cycle made is a one-line docstring path in `docs/dry/export_dry_review.py`, which contains no
clamp, `getattr` default, `or` fallback, bare `except`, or truthiness test. R3's throwaway classifier
took the *opposite* shape deliberately — it raises on an unclassifiable path rather than passing it
through — and that reasoning is recorded in its artifact.

---

## The baseline exception is recorded and moot

The build plan's preamble records the exception `BUILD.md` `## Final test-run gate` requires in that
position: a failure attributable to a file this cycle never wrote does not block `final-accepted` and
does not route back through a residual item's loop. **It is honoured and it is unexercised** — all
seven commands pass, so no result had to be excused. The exception's value here is negative evidence:
the concurrent session's mid-edit source happens to be green right now, which is luck rather than a
property, and a later maintainer run may not be.

### The baseline moved mid-pass: the maintainer committed at `43f1f9f7`

`git status --porcelain` re-counted at both ends of this pass: **18 entries at start, 15 at end.**
The figure has now moved five times across the cycle — 7 → 14 → 7 → 16 → 18 → **15** — so it was
re-counted here rather than inherited, at both ends.

**A dirty list that SHRANK is a maintainer commit or a stale snapshot, never a worker revert**, and it
is attributed positively rather than assumed. `git reflog --date=iso` shows a new commit at
**13:40:42**, `43f1f9f7` "perf(transport): hand back the actor lease instead of wrapping it", and
`git diff --name-status 05a08e31..HEAD` names **exactly four files**:
`django_strawberry_framework/utils/sessions.py`, `tests/test_routers.py`, `tests/test_views.py`, and
`docs/spec-046-transport_security-0_0_15.md`. That is 18 − 4 committed + 1 added (this artifact) = 15,
which reconciles the count exactly. No worker reverted anything; no `git stash` / `checkout` /
`restore` / `worktree` ran at any point in this pass.

**The commit does not invalidate a single gate result, and the proof is mechanical rather than
inferred.** All four files' mtimes (12:50:55 - 12:55:14) **predate** the gate run, and
`git status --porcelain -- <the four>` now returns **0 lines** — i.e. the working tree matches `HEAD`
for each. So the bytes `pytest`, `ruff`, and `git diff --check` read at `05a08e31` are byte-identical
to the bytes now committed at `43f1f9f7`: the maintainer committed the working tree as-is rather than
rewriting it. The four fast read-only commands were re-run at `43f1f9f7` regardless —
`ruff format --check` `405 files already formatted`, `ruff check` `All checks passed!`,
`git diff --check` silent, `manage.py check` clean, all exit 0. `pytest` was not re-run, because
re-running it would read the same bytes; that is a reasoned skip, not an assumption.

**The consequence for the exception is that it is now retired for four more files.** The plan's
baseline exception covered eight `.py` files; five were committed at `05a08e31` before this pass and
three of the remaining, plus the spec-046 doc, were committed at `43f1f9f7` during it. **Every file the
exception was written for is now at `HEAD`.** What remains dirty and not this cycle's is two entries,
not six.

### Attribution of the 15 entries, positively rather than by assumption

Attribution rests on three independent grounds, not on "not mine": the **writable sets** (no residual
item's writable list contains a tracked `.py` file — every item's is spec / rationale / CSV / artifact /
memory, plus R3's four named files), the **mtimes**, and `git status` itself.

**This cycle's files (13 of the 15 entries)** — mtimes 10:52:11 to 13:27:44 plus this artifact, all
inside the cycle's passes:

| Entry | mtime | Owner |
|---|---|---|
| `RM docs/spec-044-debug_extension-0_0_14.md -> docs/SPECS/…` | 13:11:35 | R3 (`git mv`) + R1/R2 content |
| `R  docs/spec-044-debug_extension-0_0_14-terms.csv -> docs/SPECS/…` | 23:25:31 (prior day; `git mv` preserves mtime on a clean file) | R3 (`git mv`) |
| `?? docs/SPECS/spec-044-debug_extension-0_0_14-rationale.md` | 13:11:21 | R1 (authored), R3 (plain `mv`) |
| `M  docs/spec-050-debug_extraction-0_0_19.md` | 12:35:03 | R3 Worker 2, Direction 1 (3/3) |
| `M  docs/dry/export_dry_review.py` | 12:35:12 | R3 Worker 2, Direction 1 (1/1 docstring line) |
| `M  examples/fakeshop/db.sqlite3` | 13:13:09 | R3 (`SpecDoc.path` + `import_spec_terms` sync) |
| `M  KANBAN.md` | 13:14:19 | R3 regenerate (2/2 — the spec-map row and card 044's `Spec:` line) |
| `M  KANBAN.html` | 13:14:22 | R3 regenerate (1/1, minified data block) |
| `?? docs/builder/build-044-debug_extension-0_0_14.md` | 13:27:44 | Worker 0 |
| `?? docs/builder/bld-044-r1-rationale_move.md` | 10:52:11 | R1 |
| `?? docs/builder/bld-044-r2-doc_completion.md` | 12:03:10 | R2 |
| `?? docs/builder/bld-044-r3-spec_archive.md` | 13:26:25 | R3 |
| `?? docs/builder/bld-044-final.md` | this pass | this gate |

**Not this cycle's — 2 entries**, never edited, never reverted (`AGENTS.md` rule 34):

| Entry | mtime | Evidence it is not this cycle's |
|---|---|---|
| `M docs/feedback.md` | 13:15:05 | First line reads "Adversarial review: spec-046 transport security" — a maintainer review of the *other* cycle. Its mtime is later than the last write any pass of this cycle made. Dirty through R1, R2, and R3; swept into `05a08e31`; dirty again since. |
| `D to-many-search-optimizer-reproduction.md` | — | The plan's declared baseline deletion, standing since pre-flight and never touched by any worker. |

**Every `.py` file the plan's exception was written for is now committed.** The plan named eight dirty
mid-cycle; the maintainer committed five at `05a08e31` and the last three — plus
`docs/spec-046-transport_security-0_0_15.md` — at `43f1f9f7` during this pass. **No `.py` file is dirty
in the tree at all right now**, which is why the exception ends the cycle retired rather than spent:
it was recorded as required, it licensed nothing, and there is no longer a file it could apply to.

---

## Cross-artifact integration read (folded in from the un-run integration pass)

`BUILD.md` `## Cross-slice integration pass` is not run as a separate artifact this cycle, and the
plan records why: an integration pass exists to find duplication across slices that landed source, and
this cycle landed none. Its live obligations were split — the staged-anchor sweep ran in R2 (and again
in R3), and the cross-artifact read runs here. All three item artifacts were read **in full** (701 /
2,114 / 2,562 lines), as `worker-1.md` `## Required reading` requires with no "as needed".

**Cross-item duplication: none.** No item wrote a repo helper, a package module, or a test. Each
authored throwaway probes only, in per-item scratch directories (`docs/builder/temp-tests/044-r1/`,
`044-r2/link_audit.py`, `044-r3/relativize.py`) plus scratch paths outside the repo. That is
deliberate re-implementation rather than duplication: R2's `link_audit.py` was written from scratch so
that R1's link claims were confirmed by a **second independent implementation**, which is the opposite
of a DRY defect, and R3 re-ran R2's tool unedited (it takes paths from `argv`, so it survived the
archive). Nothing ships; none is promoted; `git diff -- django_strawberry_framework/__init__.py`
produces 0 lines.

**Naming and method are consistent across the three items, and converged rather than drifted.** One
artifact-naming convention (`bld-044-<item>-<slug>.md`, Deviation 2). One deferred-catalog record,
handed forward by pointer: R1 contributed one item, R2 merged it into a seven-item list, R3 added
three without re-deriving any. One correction convention, applied three times: no prior entry's body
was ever edited — each pass published its corrections in its own section, with checklist boxes and
their figures as the single licensed exception (`ARTIFACT.md` `## Re-pass sections`). One isolation
principle in four availability-shaped forms: reconstruct-by-`patch` (R1), `git diff -U0` (R2),
`git show HEAD:` where HEAD *was* the prior state (R2 final), and a saved pre-move copy plus
`git diff --no-index -U0` (R3, the only route that works for a file that is both renamed and, for its
sibling, untracked).

**Every cross-item hand-off landed; none went unlanded.** Checked hand-off by hand-off rather than
accepted on the closing artifact's word:

- **R1 → R2** (five hand-offs): the stale opener at `:3`, the future-tense header narration at
  `:104-108`, the four shipping-falsified `## Current state` bullets, and the five spec-internal
  `TODO(spec-044` / `TODO-ALPHA-044` mentions. R2 ruled on **all five** — opener realigned to the
  archived siblings' shipped form, `:104-108` corrected, `## Current state` kept with a stated ground,
  the five anchors kept. Verified live: the five mentions stand at `:427`, `:430`, `:452`, `:576`,
  `:578` in the archived spec, line for line the pins R2 established including its correction of R1's
  `:453` mislabel.
- **R1 → R3** (three cautions): the anchor-*resolution* pass rather than file-exists (run — 0 broken,
  0 cross-file failures, re-confirmed in this gate); the three name-based citations at `:1562`,
  `:1613`, `:1924` not re-ordinalized (nothing in R3 touched prose other than two path strings); the
  rationale's own path bucket handled separately rather than assumed identical to the spec's (it was —
  9 of 28 re-relativized, 19 regrouped).
- **R2 → R3** (three cautions): both files' link paths left un-pre-adjusted (they were, deliberately,
  so R3 could re-relativize from a known state); the literal `DONE-044-0.0.14` in the opener left
  untouched while `SpecDoc` was repointed (verified — the opener still reads `DONE-044-0.0.14` and the
  DB reads `path`); `link_audit.py` reused with its slugifier hazard recorded (it was, and its
  `_`-keeping slugifier is why 0 anchors report broken).
- **A reversed deferral, correctly reversed.** R2 pass 1 deferred `TODO-BETA-045-0.1.0` and
  `TODO-BETA-053-0.1.5` together on one shared blast-radius argument; Worker 3 falsified half of it
  (045 occurs in spec-044 only, so the two ids share no blast radius); R2 pass 2 then *fixed* 045
  in-spec. Verified live: the archived spec carries `TODO-ALPHA-052-0.1.0` twice and
  `BETA-045-0.1.0` **zero** times. Only 053 remains in the catalog, correctly.
- **Checklist state.** 27 + 37 + 50 = **114 boxes, all `- [x]`, zero `- [ ]`** across the three
  artifacts, so no item owes a deferral reason for an un-ticked box. All three carry
  `Status: final-accepted`.

**One inconsistency worth naming rather than leaving for the maintainer to trip over.** R2's box 33
records the authoritative catalog as its **six**-item merged list; R2's final verification then
appended item 7 *after* that correction, so the box's count is now one short. The authoritative
reading is the `### Deferred work catalog — the six items, confirmed and located` section
(`bld-044-r2-doc_completion.md:1944-1982`), which is the only place all seven appear — and this
gate's catalog below, which supersedes all of them. Nothing was lost; the count in one box is stale.

---

## Deferred work catalog

The next spec author's reading list. Re-derived from the three item artifacts rather than inherited,
and **every item re-verified against the live tree in this pass** — several were mislocated or
miscounted once already and corrected, so each bullet below states the measurement that confirms it.
Items are ordered by consequence, not by the order they were found.

### 1. The nine-site `SpecDoc.url` defect in the canonical archive procedure — highest value in this catalog

- **Source:** `bld-044-r3-spec_archive.md` `### The escalated Medium — a maintainer hand-off, confirmed
  at nine sites plus one, with a refinement`, and its `### Deferred work catalog hand-off` item 3.
  Originated as Worker 2's `### Notes for Worker 1 (spec reconciliation)` escalation (4 sites), widened
  by Worker 3 (+3 prose sites), confirmed and refined at final verification.
- **Licensing spec line:** none. The licence is file ownership: neither `docs/SPECS/NEXT.md` nor
  `docs/builder/worker-0.md` is writable by any worker in this cycle, so **the record is the
  deliverable** — a `revision-needed` would route to a builder that cannot write either file.
- **Description:** `docs/SPECS/NEXT.md` Step 8's copy-paste archive worked example instructs a write to
  `SpecDoc.url`, which is a read-only `@property` (`examples/fakeshop/apps/kanban/models.py::SpecDoc`
  derives `f"{SPEC_URL_PREFIX}/{self.path}"`; the writable column is `path`, added by migration
  `0009_specdoc_path.py`). **The next spec author runs that example verbatim and it raises
  `AttributeError: property 'url' of 'SpecDoc' object has no setter`** — it does not merely mis-write.
- **Re-measured this pass** (`grep -n 'SpecDoc\|url' docs/SPECS/NEXT.md`, each hit read and classified
  write-versus-read): the population is **9** sites — `:51` (outcome description, weakest), `:246`
  (field-list callout, prose-accurate but now misleading), `:247` (actionable instruction), `:248`
  (constructor kwarg, raises in `Model.__init__`), `:272` (`update_or_create` defaults, raises on both
  branches), `:280` (assignment), `:334` (numbered action 5, actionable instruction), `:337`
  (`update_or_create` defaults), `:338` (actionable instruction). **`:335` and `:339` are reads of the
  derived property and are correct as written** — they are not part of the population.
- **Plus a sixth surface with a trap:** `docs/builder/worker-0.md:223` carries **two** such writes on
  one line — the `SpecDoc.objects.create(..., url="https://…")` call **and** the following prose "If a
  `SpecDoc` row already exists for the card, **update** its `url`/`name`". Confirmed by reading the line
  this pass. A fix targeting only the `create(...)` call leaves the same line still instructing a write
  to a property with no setter. (`worker-0.md:211`'s `SpecDoc` mention is an existence invariant, not a
  `url` write, and is correct.)
- **Do not partial-fix.** A four-site correction leaves numbered action 5 itself still instructing the
  raising operation, in the document whose entire purpose is to be copy-pasted. Per-site replacements
  in the documents' own voice are drafted in R3's `### The escalated Medium` section; the falsifiable
  check for the whole item is that `grep -n 'SpecDoc' docs/SPECS/NEXT.md docs/builder/worker-0.md`
  returns zero sites that assign, construct, or instruct assigning `url`. **Owner: maintainer.**
- **Why the escalation was short by five:** the supporting grep sampled the defect's *syntax* (an
  assignment or a `'url':` key) rather than its *vocabulary* (prose spelling the same instruction).
  That is this cycle's repeating failure in miniature and the reason every count in this catalog was
  re-measured rather than carried.

### 2. Two in-flight sibling specs assert `TODO(spec-044 Slice 3)` anchors that do not exist

- **Source:** `bld-044-r1-rationale_move.md` `### Step 6 — the staged-anchor sweep` class 3 and its
  `### For the ### Deferred work catalog` (R1's single contribution); carried as item 1 through every
  later version of the list.
- **Licensing spec line:** none; licensed by writability — both are live specs belonging to their own
  authors or a future cycle, outside every residual item's writable set.
- **Description:** `docs/spec-050-debug_extraction-0_0_19.md:390` and
  `docs/spec-051-boundary_dry_squeeze-0_0_20.md:556` both assert the version-quintet sites "currently
  carry `TODO(spec-044 Slice 3)` anchors owned by the in-flight `0.0.14` cut". The cut landed
  2026-07-20 and **zero** such anchors survive, so both sentences are false and each is load-bearing
  for a future author's anchor-staging decision.
- **Re-verified this pass:** both lines read as quoted;
  `grep -rEn 'TODO\(spec-044|TODO-(ALPHA|BETA|STABLE)-044' django_strawberry_framework tests examples scripts | wc -l`
  → **0**, the fifth independent reproduction across the cycle.
- **Why drift and not a dated snapshot:** both sentences sit under those specs' `## Architectural
  decisions` (`spec-050:258`, `spec-051:309`), which carries no dating frame. Contrast item 3.
  **Owner: each spec's author.**

### 3. The same two specs claim card `WIP-ALPHA-044-0.0.14` is mid-flight — probably drift, posed as a question

- **Source:** `bld-044-r2-doc_completion.md`, item 2 of every version of its list; **located
  correctly only at final verification** (`### Deferred work catalog — the six items, confirmed and
  located`).
- **Licensing spec line:** none; writability again.
- **Description:** `docs/spec-050-…:173` reads "Card `WIP-ALPHA-044-0.0.14` is mid-flight and owns the
  `0.0.14`…"; `docs/spec-051-…:235` reads "Card `WIP-ALPHA-044-0.0.14`…". Both are falsified — the card
  is `DONE-044-0.0.14` and the cut is applied.
- **The location correction, which is why this bullet states both halves:** pass 1 pinned `:173` /
  `:235` (right), Worker 3 relocated it to `:155` / `:215`, the merged list and the pass-2 re-review
  both carried `:155` / `:215`, and final verification corrected it back. **`:155` and `:215` are the
  `## Current state` heading lines**, 18-20 lines above the sentences. Re-measured this pass: the
  headings are at `docs/spec-050-…:155` and `docs/spec-051-…:215`, the sentences at `:173` and `:235`.
- **Keep both halves of the evidence.** These sentences sit in each spec's own `## Current state` —
  the section this cycle ruled *keeps* a shipping-falsified bullet when it self-dates — **but neither
  section carries the dating lead-in that licenses spec-044's equivalent keep**. Verified this pass:
  both go straight from `## Current state` to bullets, with no "A true description of the repo as this
  spec is authored:" line. Both specs are still in flight, so a refresh is the likely answer.
  **Record as *probably drift, owner = each spec's author*, not as an asserted defect** — it was
  checked and deliberately posed as a question.

### 4. Routing observation: two files, one job each — not four errands

- **Source:** `bld-044-r2-doc_completion.md`, item 7, appended at final verification.
- **Description:** items 2 and 3 together are the whole of those two files' spec-044 staleness — four
  sentences across two files whose authors are the same two people. **`spec-050` owes `:173` and
  `:390`; `spec-051` owes `:235` and `:556`.** No new drift claimed; this exists so the maintainer
  routes them as one job per file. It was written only because item 3's location correction landed in
  the same section.

### 5. `TODO-BETA-053-0.1.5` — a dead card id left uniformly wrong on purpose

- **Source:** `bld-044-r2-doc_completion.md`, item 3 of every version of its list; the blast radius
  was reproduced independently by Worker 3 pass 1, Worker 3 pass 2, and final verification.
- **Licensing spec line:** none — and notably it is not in the spec's `## Doc updates` or
  `## Definition of done` either. The drift was caused by the **2026-07-30 card renumber**, not by
  spec-044's shipping, and the licence is the standing rule that a spec-only correction which diverges
  from copies the worker cannot edit is worse than uniformly wrong. **One owner, one sweep, or not at
  all.**
- **Description:** the id names nothing. Card `053` now names `FieldSet` at `0.1.1`
  (`TODO-BETA-053-0.1.1`, `KANBAN.md:493`); the likely intended target is
  `TODO-BETA-060-0.1.5` — "Fakeshop GraphQL schema activation" (`KANBAN.md:939`), same version, same
  subject. Confidence is high on identity and **lower that it is still the natural host** for fakeshop
  opting into the debug extension, since card 060's planning note assigns per-subsystem activation to
  the respective Layer-3 cards' Slice 4.
- **Re-measured this pass with the distinctive token.** `BETA-053` is **not** distinctive — it matches
  the live `BETA-053-0.1.1` (18 occurrences in `KANBAN.md` alone) and inflates the census to 79.
  `grep -rno 'BETA-053-0\.1\.5'` returns **44** occurrences, of which **12** are in this cycle's own
  per-cycle scratchpad (`bld-044-r2-doc_completion.md`). The real drift population is **32 occurrences
  across 10 files**: `TODAY.md` (3), the archived `docs/SPECS/spec-044-debug_extension-0_0_14.md`
  (1, at `:2623`), six archived specs — `spec-030` (2), `spec-032` (7), `spec-033` (7), `spec-037` (3),
  `spec-041` (3), `spec-042` (4), summing to **26** exactly as R2 recorded — and **two source/test
  files**, `examples/fakeshop/apps/products/schema.py` (1) and
  `examples/fakeshop/test_query/test_products_api.py` (1). Repointing spec-044's single occurrence
  alone would leave one file disagreeing with nine.
- **Its sibling was fixed, and the asymmetry is the point.** `TODO-BETA-045-0.1.0` occurred in
  spec-044 only, so it had no shared blast radius and R2 pass 2 repointed it to
  `TODO-ALPHA-052-0.1.0` in-spec (verified: 2 occurrences of the new id, 0 of the old). Same class of
  defect, two different-sized jobs. **Owner: maintainer.**

### 6. `strawberry.Schema` vs the shipped `DjangoSchema(...)` — two surfaces, one pass

- **Source:** `bld-044-r2-doc_completion.md`, items 4 and 5 (item 5 was **new in Worker 3's pass-1
  verification** and pinned to a line in the merged list).
- **Licensing spec line:** none. Deferred because the divergence comes from the **mutation-atomicity
  card's** shipping rather than spec-044's, and because deciding whether the cookbook recipe should now
  name `DjangoSchema` changes the spec's central migration story — a maintainer call, not a
  doc-completion pass's. Note the spec *is* writable by this cycle, so the non-fix is an explicit
  ruling rather than an impossibility.
- **Description:** the archived spec's `:291-297` calls
  `strawberry.Schema(query=Query, config=strawberry_config(), extensions=[lambda: _optimizer])` "the
  canonical shape `config/schema.py` demonstrates today". Verified this pass:
  `examples/fakeshop/config/schema.py:77-81` builds `DjangoSchema(query=Query, mutation=Mutation,
  config=strawberry_config(), extensions=[lambda: _optimizer])`. `DjangoSchema` is a
  `strawberry.Schema` subclass (`django_strawberry_framework/schema.py:199`), so three of four cited
  elements are exact and the named class is a base of the class used — **inexact, not false**. The two
  nearby recipe snippets (`:326`, `:892`) are query-only consumer examples for which plain
  `strawberry.Schema` remains correct.
- **The second surface:** `examples/fakeshop/test_query/README.md:23` carries the same divergence,
  verified this pass — it states the project schema "constructs `strawberry.Schema(query=Query,
  mutation=Mutation, config=strawberry_config(), extensions=[lambda: _optimizer])`". That file is
  writable by no residual item. **Whoever answers this should answer both surfaces in one pass**, or
  the spec and the README will disagree with each other as well as with the code.
  **Owner: maintainer.**

### 7. The `065` / `046` card-id split between two standing docs

- **Source:** first recorded in `bld-044-r2-doc_completion.md`'s pass-1
  `### Notes for Worker 1 (spec reconciliation)` as "observed, outside every residual item's scope,
  recorded so it is not lost"; **promoted into the catalog as item 6 by Worker 3 pass 1** with the pins
  verified.
- **Licensing spec line:** none — nothing to do with spec-044's shipping; both files are unwritable by
  every residual item.
- **Description:** verified this pass — `TODAY.md:384` attributes the router redesign to "the
  transport-security card `065`", while `docs/README.md:128` attributes it to `046`. The 2026-07-30
  renumber moved `065` → `046`, so `TODAY.md` carries the pre-renumber number.
  **Owner: the preserved spec-046 cycle's closeout, or the renumber's.**

### 8. `NEXT.md`'s "exactly one WIP spec at `docs/`" invariant is left unsatisfied by design

- **Source:** `bld-044-r3-spec_archive.md` `### Deferred work catalog hand-off` item 1 (box W1-48).
- **Licensing spec line:** none in a spec — licensed by **the maintainer's explicit scoping of this
  cycle to archiving spec-044 alone**, which is recorded in R3's `### Scope decision recorded first:
  only spec-044 is archived`.
- **Description:** after R3's move, **seven live spec stems** remain at `docs/` root — `045`, `046`,
  `050`, `051`, `052`, `053`, `054`. Recorded so a future `NEXT.md` Step 8 run does not read the
  residue as drift this cycle caused.
- **The counting trap, re-verified this pass:** `ls docs/spec-*.md` prints **eight** files, not seven,
  because `spec-046` carries its own `-rationale.md` alongside its `.md`. The file count and the stem
  count differ by one, and **eight is not evidence a stem was missed.**
  **Owner: maintainer / the next spec author's Step 8.**

### 9. The 14th `GlossarySpecMention` orphan pair, and its cause in the command

- **Source:** `bld-044-r3-spec_archive.md` `### Deferred work catalog hand-off` item 2, measured in
  `### The DB sync — prediction against measurement`.
- **Licensing spec line:** none. Deferred on the same measured ground as item 5: a spec-044-only
  cleanup makes one card diverge from 13 siblings. **One owner, one sweep, or not at all.**
- **Description:**
  `examples/fakeshop/apps/glossary/management/commands/import_spec_terms.py::_sync_spec_mentions`
  **orphans rather than repoints** — it deletes only rows at the **new** `spec_path`, never the old
  one, so every spec archive leaves the old path's rows behind forever.
- **Re-measured this pass, live against the DB:** total rows **1450** (up from 1408, the predicted
  delta hit exactly), **42 live** at `docs/SPECS/spec-044-debug_extension-0_0_14.md` beside **42
  orphaned** at `docs/spec-044-debug_extension-0_0_14.md`, **60 distinct `spec_path` values** for 46
  live specs, and **14 `spec_path` values with no file on disk** — i.e. 14 orphan pairs, of which 13
  predate this cycle (e.g. spec-028 43 orphans beside 44 live; spec-043 22 beside 22).
  **Owner: maintainer.**

### 10. `docs/spec-050-…:553`'s `[spec-038]` definition names a file that does not exist

- **Source:** `bld-044-r3-spec_archive.md` Worker 2's `### Notes for Worker 1 (spec reconciliation)`
  (box W2-5), confirmed by Worker 3 and again at final verification.
- **Licensing spec line:** none; a pre-existing inaccuracy in another live spec, unrelated to
  spec-044's move.
- **Description:** verified this pass —
  `docs/spec-050-debug_extraction-0_0_19.md:553` reads
  `[spec-038]: SPECS/spec-038-auth_mutations-0_0_13.md`. No such file exists: spec-038 is
  `docs/SPECS/spec-038-form_mutations-0_0_12.md` and `auth_mutations` is
  `docs/SPECS/spec-040-auth_mutations-0_0_13.md`. It sits **one line above** the `[spec-044]`
  definition R3 rewrote (`:554`, now correctly resolving), so it appears in the same hunk and a
  reviewer will see it. Correctly left unfixed. **Owner: `spec-050`'s author.**

### 11. `scripts/archive_spec.py` — a real future card, not an annoyance

- **Source:** raised in the R3 plan's `### DRY analysis` and re-affirmed in its
  `### Deferred work catalog hand-off`.
- **Description:** `docs/SPECS/NEXT.md` Step 8's archive procedure is ~120 lines of hand-run steps that
  has now produced **two standing-doc defects** (item 1) and **14 orphan-row pairs** (item 9). Three
  directions of cross-reference rewriting, a group-relocation obligation invisible to every checker,
  and a DB sync inseparable from the physical move are all mechanizable. **Owner: maintainer, as a
  board card.**

### 12. Two archived `0.0.14` siblings still carry a `Status:` line saying 044 is pending

- **Source:** **this gate's own audit**, stated plainly rather than dressed as an item-artifact
  hand-off. No per-item artifact records it: R2 read `docs/SPECS/spec-042-…:3` and `spec-043-…:3` as
  the *opener* precedent for its own realignment and had no reason to read their `Status:` lines, and
  they are outside every residual item's writable set either way. Recorded here because the cycle's own
  ruling is what makes it consequential.
- **Description, measured this pass:**
  `docs/SPECS/spec-042-debug_toolbar-0_0_14.md:55` — "the `0.0.14` version release **rides the joint
  cut (043 / 044 pending)**"; `docs/SPECS/spec-043-test_client-0_0_14.md:72` — "**rides the joint cut
  (044 pending)**". Card 044 shipped 2026-07-20; nothing is pending.
  (`docs/SPECS/spec-041-channels_router-0_0_14.md:90` is clean.)
- **Why it is worth a bullet rather than filing under archived history:** this cycle ruled, and three
  reviews upheld, that a spec's **`Status:` line is the single source of truth for release state** —
  which is exactly the line that is stale in both siblings. That is a narrower claim than "archived
  specs may keep shipping-falsified prose", which remains true for their `## Current state` sections and
  their dated obligation lists. The tension is real and is the maintainer's to settle.
  **Owner: maintainer.** Note spec-043 carries eleven further "joint cut" mentions in body prose
  (`:4`, `:68`, `:90`, `:109`, `:186`, `:239`, `:251`, `:303`, `:454`, `:585`, `:649`) which are
  dated authoring-time obligation prose and, on this cycle's own test, **keep**.

### Explicitly owed by nobody, recorded so it is not re-opened

- **The isolated-venv floor run** the spec's `## Definition of done` row 5 requires belongs to the
  shipped Slice 1's record, not to a residual pass; this cycle's floor scope is `none`.
- **`## Definition of done` row 9**'s process re-proof was discharged by the shipped cycle's commits
  and no residual item can re-prove it (`AGENTS.md` rule 15 forbids the re-run).
- **The spec's 43 checkboxes stay `- [ ]`** (20 `## Slice checklist` / 14 DRY / 9 DoD, 26 top-level).
  Not deferred: `Status:` is the single source of truth for release state and all four archived
  `0.0.14`-era siblings ship 0 ticked. Settled handling, upheld by three reviews.
- **The rationale file's `WIP-ALPHA-044` mentions** (`:82`, `:78`) are correct as Revision-1
  chronology; the rationale is the one file licensed to narrate history.
- **`## Current state`, `## Goals` item 6, `### Decision 12`'s body, `## Key glossary references`, and
  `:113-115`** in the archived spec were each ruled a deliberate KEEP with a stated ground (the
  `planned` class was closed at 12 sites with a ruling on each). Do not re-flag; R2's
  `### The class sweep` carries the grounds.
- **The nine same-shape link hits R1 verified and rejected** as already-resolving (`:273`, `:741`,
  `:856`, `:1217`, `:1574`, `:1884`, `:2410`, `:2543`, `:2083`/`:2087`) — recorded so a later pass does
  not re-flag them.

---

## What the cycle delivered, against the maintainer's three-part instruction

1. **The missing `-rationale.md` (R1).** `docs/SPECS/spec-044-debug_extension-0_0_14-rationale.md`,
   43,868 bytes / 672 lines, keyed decision by decision so it works as a review instrument rather than
   an archive. It is a **move**, not a copy: the spec went 205,905 → 185,518 bytes in that pass, a 10%
   cut off every future spawn's read of it, and every one of the 396 removed lines was proven to have
   exactly one home. The deliberative layer that the shipped `0.0.14` cycle never extracted now exists.
2. **The finished documentation (R2).** The opener realigned from ``Planned for `0.0.14` (card
   `WIP-ALPHA-044-0.0.14`)`` to the archived siblings' shipped form; the header block's GLOSSARY-status
   claim and its `**Version boundary**` paragraph corrected; the criterion-7 premise dated; the two
   dead `TODO-BETA-045-0.1.0` pointers repointed. All fourteen `## Doc updates` / `## Definition of
   done` rows audited against HEAD and found already landed in shipped tense — **so no Worker 2
   dispatch was owed**, a finding of absence that survived two reviews and a final audit. The
   substantive product is a *ruled* answer for every stale-reading sentence the release created: one
   corrected class and three keep classes, each with a stated ground rather than a silence.
3. **The archived spec (R3).** Three files moved to `docs/SPECS/` — the tracked spec (dirty with
   R1+R2's uncommitted edits, `git mv`), the tracked clean `-terms.csv` (`git mv`), and the untracked
   `-rationale.md` (plain `mv`) — with all three destination digests byte-identical to their pre-move
   digests, so the dirty content is *proven* to have survived. 95 of 130 link definitions
   re-relativized by a classifier that raises rather than passing through, and **34 more changed group**
   under `START.md`'s group-by-target rule — the obligation R3's own plan table omitted, and the one a
   path-only diff hides because every link still resolves. `SpecDoc.path` repointed in the DB,
   `KANBAN.md` / `KANBAN.html` regenerated.

---

## Files the maintainer should commit for this cycle

`START.md` requires staging explicitly (`git add <path>`, never `git add -A`) precisely because a
concurrent session's WIP would otherwise be swept in. **The renames must be staged as renames** — the
two `git mv`-moved files are already staged as `R` / `RM`, so `git add` on the destination path
preserves that; do not `git rm` + `git add` them.

**This cycle's thirteen paths — commit these** (the twelve its work left in `git status`, plus this
artifact):

```shell
# The archived spec and its two siblings (renames already staged by git mv;
# the rationale is untracked and new).
git add docs/SPECS/spec-044-debug_extension-0_0_14.md
git add docs/SPECS/spec-044-debug_extension-0_0_14-terms.csv
git add docs/SPECS/spec-044-debug_extension-0_0_14-rationale.md

# Inbound cross-reference rewrites (R3 Direction 1).
git add docs/spec-050-debug_extraction-0_0_19.md
git add docs/dry/export_dry_review.py

# The DB row and its two regenerated exports (R3).
git add examples/fakeshop/db.sqlite3
git add KANBAN.md
git add KANBAN.html

# The build plan and the four cycle artifacts.
git add docs/builder/build-044-debug_extension-0_0_14.md
git add docs/builder/bld-044-r1-rationale_move.md
git add docs/builder/bld-044-r2-doc_completion.md
git add docs/builder/bld-044-r3-spec_archive.md
git add docs/builder/bld-044-final.md
```

Thirteen paths in total — **seven** already-tracked (the spec and CSV as staged renames, plus
`docs/spec-050-…`, `docs/dry/export_dry_review.py`, `examples/fakeshop/db.sqlite3`, `KANBAN.md`,
`KANBAN.html`) and **six** new and untracked (the `-rationale.md`, the build plan, and the four
`bld-044-*` artifacts).

Both generated exports carry a real change and both must be staged: `git diff --numstat` reads
`KANBAN.md` **2/2** — the `## WIP / DONE spec map` row and card 044's body `Spec:` line, each repointed
from `docs/spec-044-…` to `docs/SPECS/spec-044-…` — and `KANBAN.html` **1/1** on its minified data
block. Neither is a no-op, and `--check` reporting both "up to date" means only that the file matches
what the DB now renders, which is the point of staging the DB row alongside them.

**The two paths that are not this cycle's — do NOT stage these:**

- `docs/feedback.md` — a maintainer adversarial review of spec-046, not of spec-044.
- `to-many-search-optimizer-reproduction.md` (a deletion) — the plan's declared baseline entry.

Neither was edited or reverted by any worker (`AGENTS.md` rule 34); their attribution is in
`### Attribution of the 15 entries, positively rather than by assumption` above. **The four other
spec-046 paths that were dirty when this gate opened are no longer in the list** — the maintainer
committed them at `43f1f9f7` mid-pass, so `django_strawberry_framework/utils/sessions.py`,
`tests/test_routers.py`, `tests/test_views.py`, and `docs/spec-046-transport_security-0_0_15.md` need
no staging decision at all. A commit list inherited from R3's close would have named them; this one was
re-derived after the move.

**Also un-stageable, and deliberately preserved rather than deleted:** the 25 committed `bld-*.md` /
`build-046-*.md` artifacts of the spec-046 cycle (already at HEAD), the gitignored
`docs/builder/worker-memory/` files, and the gitignored `docs/builder/temp-tests/` directories
including this pass's `044-final/`. See Deviation 1 below.

---

## The three declared deviations — honoured

- **Deviation 1 — the prior cycle's artifacts, memory, shadow, and temp-tests are PRESERVED.**
  Honoured throughout: pre-flight steps 3 and 5 were deliberately not performed, and **nothing was
  deleted at any point in this cycle**. The spec-046 cycle's 25 committed artifacts, the four
  gitignored `worker-memory/` files, and the ten gitignored `temp-tests/` cycle directories all
  survive. **Do not delete any of it now** — that cycle's closeout retrospective has not run, and
  `worker-0.md` `## Closeout job` step 5 owns the cleanup, **after** the maintainer commits. Deleting
  the gitignored files is unrecoverable and would destroy the input to a retrospective that has not
  happened. Collision was avoided by naming, exactly as the deviation planned: every artifact this
  cycle created is `bld-044-`- or `build-044-`-prefixed and none of those paths pre-existed.
- **Deviation 2 — artifact filenames carry the `044` card number.** Honoured: `bld-044-r1-…`,
  `bld-044-r2-…`, `bld-044-r3-…`, and this `bld-044-final.md`. All four are `docs/builder/bld-`-prefixed
  as `## Build artifact naming` requires, and none collides with the surviving spec-046
  `bld-slice-1..5-*` / `bld-integration.md` / `bld-final.md` set.
- **Deviation 3 — the `built` state is skipped where the deliverable is Worker-1-exclusive.** Honoured
  for R1 only, as declared: its chain ran Worker 1 (plan + perform, `planned`) → Worker 3 (audit) →
  Worker 1 (final verification, `final-accepted`), with no Worker 2 pass — because `BUILD.md`
  `## Spec rationale extraction` makes Worker 1 the only role that performs the move and states that
  Worker 2 never reads the rationale file. The Worker 3 audit was **not** skipped alongside the Worker 2
  build, which was the deviation's own condition. R2 and R3 both ran the full unmodified chain,
  including two Worker 2/Worker 3 loops each.

---

## Summary

**The gate is green and the cycle is closed.** All seven gate commands pass — the full sweep at
**5276 passed / 40 skipped**, both Django consistency checks clean, `ruff format --check` and
`ruff check` clean over 405 files, `git diff --check` silent, and `check_spec_glossary.py` re-run at the
new archived path reporting `OK: 42 terms`. Floor-verification scope is `none` and is stated as such
rather than left implied; no floor venv was built and none was owed. Hot-path and failability
obligations are both arithmetically zero, because this cycle wrote no tracked `.py` file at all — which
was also the strongest attribution available for every `.py` file that went dirty around it.

**The recorded baseline exception is honoured, unexercised, and now retired.** Nothing failed, so
nothing had to be excused. **The baseline moved during the gate:** the dirty list read **18 entries at
pass start and 15 at pass end**, and `HEAD` moved from `05a08e31` to **`43f1f9f7`** because the
maintainer committed the concurrent spec-046 work at 13:40:42, mid-pass. A shrinking dirty list is a
commit or a stale snapshot, never a worker revert, and this one reconciles exactly: 18 − 4 committed
+ 1 added (this artifact) = 15, with `git reflog` and `git diff --name-status 05a08e31..HEAD` naming
the four. It invalidates no result — all four files' mtimes predate the gate run and
`git status -- <the four>` now returns 0 lines, so the bytes `pytest` and `ruff` read are byte-identical
to the bytes now at `HEAD` — and the four fast commands were re-run at `43f1f9f7` anyway, all still
green. Consequence: **no `.py` file is dirty in the tree at all now**, so every file the exception was
written for is committed and the exception licensed nothing. Of the 15 remaining entries, 13 are this
cycle's and **2** are not, each attributed by writable set, mtime, and `git status` rather than by
assumption.

**The cycle delivered the maintainer's three-part instruction in full:** the `-rationale.md` the
shipped `0.0.14` cycle skipped (43,868 bytes, and a 20,195-byte net reduction in the spec every future
spawn reads), the finished documentation (a ruled answer for every sentence the release made
stale — one corrected class, three keep classes, each with a ground), and the archived spec at
`docs/SPECS/` with all three cross-reference directions swept, the DB repointed, and the exports
regenerated. The cross-artifact read found no cross-item duplication, no inconsistent naming, and no
unlanded hand-off: all fourteen hand-offs between R1, R2, and R3 were checked individually and landed,
114 checklist boxes across the three artifacts are ticked with none silently un-ticked, and one stale
count in R2's box 33 is named here rather than left to surprise a reader.

**The catalog is the cycle's most valuable output**, and its highest-consequence entry is not the
archive: `docs/SPECS/NEXT.md` Step 8's copy-paste archive example instructs a write to a read-only
`@property` at nine sites, plus two more on one line of `docs/builder/worker-0.md:223`. The next spec
author runs that example verbatim and it raises. Neither file is writable by any worker, which is why
the record — nine sites classified write-versus-read, with per-site replacements — is the deliverable.
Twelve items are catalogued, each re-verified against the live tree in this pass rather than inherited;
two counts and one location that earlier passes got wrong are corrected here with the measurement that
falsified them, and one item (12) is sourced from this gate's own audit rather than from an item
artifact, which is said plainly.

`Status: final-accepted`. Remaining for Worker 0: tick the plan's final checkbox. Remaining for the
maintainer: commit the **thirteen** paths named above — staged individually, never `git add -A`, with
the two renames staged as renames — then the spec-046 closeout retrospective, which owns the scratch
cleanup this cycle deliberately did not perform. Do not delete the preserved spec-046 artifacts, the
gitignored worker memory, or `temp-tests/` before that retrospective runs.

### Spec changes made (Worker 1 only)

**None in this pass.** The gate revealed no inaccuracy in either
`docs/SPECS/spec-044-debug_extension-0_0_14.md` or its `-rationale.md` that custody required me to
reconcile, so neither file was edited and both are byte-identical to R3's recorded end state
(**185,710** and **43,868**, re-measured with `wc -c` this pass).

`worker-1.md` `## Spec status-line re-verification` obliges every Worker 1 spawn to re-read the spec's
status/header lines and edit any the build has falsified. Read this pass and **all accurate**:

- `:1` the title; `:3-5` ``Built for `0.0.14` (card [`DONE-044-0.0.14`][kanban]); **this card completed
  the joint `0.0.14` cut and owned the version bump**`` — shipped tense, Done card id, correct.
- `:74` `Status: **COMPLETE (card `DONE-044-0.0.14`) — all three slices built and the card-wrap landed;
  this card owned and applied the joint `0.0.14` version cut …**` — accurate, and the single source of
  truth for release state.
- The rationale file's own header correctly frames it as the deliberative companion and names the spec
  by its `[spec-044]` definition, which now resolves as a `docs/SPECS/` sibling.
- Every `[spec-038]` / `[spec-041]` / `[spec-042]` / `[spec-043]` / `[rationale]` definition resolves
  from the new location: `link_audit.py` reports **0 broken in-page anchors and 0 cross-file
  failures** for both files, and `check_spec_glossary.py` exits 0 at the new path.

The archive falsified nothing in the header block — R3's final verification read `:1-130` paragraph by
paragraph and fixed the one sentence the move did falsify (`:1103`'s self-reference), and this pass
re-confirmed the result rather than re-deriving it. **No box in any item artifact is `- [ ]`, so no
deferral reason is owed under `## Final verification job` step 3.**

Temp files created by this pass, all under the writable scratch path and gitignored:
`docs/builder/temp-tests/044-final/pytest-full.log`.

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
