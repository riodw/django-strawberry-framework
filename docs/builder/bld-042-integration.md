# Build: cross-cohort integration pass — spec-042 post-ship reconciliation

Spec reference: `docs/SPECS/spec-042-debug_toolbar-0_0_14.md` + its
`docs/SPECS/appx/` companions
Build plan: `docs/builder/build-042-debug_toolbar-0_0_14.md` (`## Checklist`, the
cross-cohort integration row)
Cohorts read: `docs/builder/bld-042-review-1-spec_reconciliation.md` (A,
`final-accepted`), `docs/builder/bld-042-review-2-code_verification.md` (B,
`revision-needed`), `docs/builder/bld-042-review-3-code_fix.md` (C,
`final-accepted`)
Status: final-accepted

This cycle has no spec slices, so `BUILD.md` `## Cross-slice integration pass` is
run over the three **cohort** artifacts in cohort order; every step's substance
applies unchanged and only the artifact naming differs (the dispatch's framing,
followed as written).

The pass runs as a single Worker 1 pass — the `### Procedural-closure slices`
shape Cohort A also used, since the integration pass has no Worker 2 build and no
Worker 3 review of its own. Files written by this pass, its complete and
exclusive write set:

- `docs/builder/bld-042-integration.md` (this file, new)
- `docs/SPECS/spec-042-debug_toolbar-0_0_14.md`
- `docs/SPECS/appx/spec-042-debug_toolbar-0_0_14-rationale.md`
- `docs/builder/worker-memory/042-worker-1.md`

`git status --short -- docs/SPECS/` shows exactly one modified file (the spec)
and one untracked file (the rationale). **No source, no tests**, no fenced
surface: `docs/GLOSSARY.md`, `docs/README.md`, `README.md`, `docs/TREE.md`,
`KANBAN.md` / `KANBAN.html`, `TODAY.md`, `CHANGELOG.md`,
`examples/fakeshop/db.sqlite3` and every agentflow doc are untouched, and the
three cohort artifacts and everything under `docs/builder/temp-tests/042/` were
read and not written. The concurrent session's paths were never edited or
reverted (`AGENTS.md` rule 34).

---

## The six prerequisites

### 1. All three cohort artifacts read, in cohort order

Read in full, A then B then C (4,424 lines in C alone, three builder passes and
three reviews). No "as needed". What each contributes to the cross-cohort scan is
cited throughout below rather than summarised here.

### 2. Static inspection helper — run, and one recorded skip

| File | Disposition |
| --- | --- |
| `tests/middleware/test_debug_toolbar.py` | **Run** this pass: `uv run python scripts/review_inspect.py tests/middleware/test_debug_toolbar.py --output-dir docs/shadow`, exit 0. Its **Repeated string literals** section is the input to step 3 and to `### DRY findings` below. |
| `django_strawberry_framework/middleware/debug_toolbar.py` | **Run** this pass (exit 0) so the literal and import sections are current, but the helper is **moot for review purposes and the skip is recorded with its reason**: this cycle changed only the module docstring and one comment block, so there is no new logic for an AST overview to surface. |
| `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html` | **Not applicable, recorded rather than left unstated:** the helper is an AST tool over Python and cannot parse the asset. This is also why no instrument in this repository can mechanically review the only executable change the cycle shipped. |

**The docstring-only claim is the warrant for that skip, so it was re-derived
here rather than read off Cohort C's record** (`BUILD.md` `## Claims are proven
mechanically`). `git show HEAD:django_strawberry_framework/middleware/debug_toolbar.py`
into the scratchpad, both files parsed, every `Module` / `FunctionDef` /
`AsyncFunctionDef` / `ClassDef` docstring node removed, `ast.dump()` compared:
**identical, 12387 == 12387 characters.** Comments never reach the AST, so the
M4 comment edit rides the same comparison. Control that the instrument can see a
difference: the asset, whose diff is executable, is `33` added / `7` removed
lines against HEAD in the same reading.

### 3. Repeated string literals compared across every shadow overview

The two overviews this cycle owns, read fresh:

| Literal | `…/middleware/debug_toolbar.py` | `tests/middleware/test_debug_toolbar.py` |
| --- | --- | --- |
| `Content-Length` | 4x | 6x |
| `debugToolbar` | 3x | 3x |
| `debug_toolbar` | 2x | 10x |

All three are cross-file and all three were considered and closed by Cohort B
with reasons this pass re-read and agrees with (upstream-verbatim refresh blocks;
a wire protocol constant a Python name could not reach; a module path). Nothing
new.

**The cross-file literal population this cycle actually created is not in either
table**, because its second copy is the `.html` asset the helper cannot parse:
the predicate table's needles. `delete data.debugToolbar` 5x, `delete
data.debugToolbar;` 5x, `const id = CSS.escape(panelId);` 4x, `if (!isRecord(toolbar)
|| !isRecord(toolbar.panels)) return data;` 3x, `Object.entries(toolbar.panels)`
3x, and more — every one of them a quotation of a line in the asset. Judged at
cross-cohort altitude in `### DRY findings` below; the short answer is that the
duplication is the instrument and hoisting it would disarm the instrument.

#### The floor literal, re-measured — and the sweep that is part of the finding

The dispatch names six live sites and says three are gated. Re-measured this pass
with both needles, by path-based exclusion only:

- **Gated trio** (the closed population `tests/middleware/test_debug_toolbar.py::test_install_hint_floor_matches_the_pyproject_dev_group_row`
  and the hint-matching rows compare): `pyproject.toml`,
  `_HINT_SUBSTRING` in the package test, `_DEBUG_TOOLBAR_INSTALL_HINT` in the
  module.
- **Ungated restatements, enumerated as a dated measurement rather than as a
  count:** `docs/GLOSSARY.md`, `docs/README.md`, `CHANGELOG.md`
  #"Soft-dependency feature floors" (the backtick-and-space spelling),
  `docs/SPECS/appx/spec-042-debug_toolbar-0_0_14-terms.csv`, **and the spec's own
  seven value-bearing restatements** — which the deferred-work catalog's item 1
  does not name.

**The load-bearing reading is the delta, not the total, and the total is stated
as a function of its instrument** rather than as a number. Tight needle
`django-debug-toolbar>=` against loose `` django-debug-toolbar`?[^A-Za-z0-9]{0,3}>= ``,
over every file in the tree except `.git/`, `uv.lock`, `docs/shadow/` and this
cycle's own `042` artifacts: **the loose needle finds exactly one restatement the
tight one does not, `CHANGELOG.md:61`**, which is Cohort C's finding reproduced.
The absolute occurrence count is **not** reproducible across instruments and no
figure for it is published here: whether `__pycache__/*.pyc`, the tracked
`examples/fakeshop/db.sqlite3`, and `docs/builder/temp-tests/042/`'s own proof
reports are read moves it by more than twenty, and the catalog's own "24 / 25"
was measured against an unstated corpus. State the corpus or state no number.

**One site is a pair, which the catalog does not say.** The terms.csv
soft-dependency row has a DB twin: `import_spec_terms` loaded the same `notes`
cell into `glossary_glossaryspecmention.notes` in `examples/fakeshop/db.sqlite3`
(read from a scratchpad copy, never the tracked file; the DB's only other hit is
`glossary_glossaryterm.body`, which is the source `docs/GLOSSARY.md:496` renders
from, already catalogued). So a bump correcting the CSV alone leaves the DB copy
live, and the DB copy is an ORM edit plus a regenerate rather than a text fix.

**One instrument lie, recorded because it is the kind that reads like a clean
sweep.** My first census excluded `uv.lock` and `docs/shadow/` with
`grep -v` over the *output lines* rather than over paths, and
`docs/SPECS/appx/spec-042-debug_toolbar-0_0_14-terms.csv`'s matching line
contains the words `uv.lock regeneration` — so the terms.csv silently dropped out
of a sweep that otherwise looked complete, and the file the catalog names as an
ungated site was the one the census could not see. Re-run with path-based
exclusion only. `START.md` `## Instruments that lie` is the standing rule; this
is a new entry in its class: **a content filter used as a path filter deletes
exactly the rows whose content discusses the thing being filtered out.**

Dispositions: every ungated doc site is fenced out of this cycle
(**record, never fix**) and stays in the catalog; the terms.csv is outside this
pass's write set; the spec's own seven are **checked and decided, not work** —
they record what the card shipped, the DoD item already hedges "or the floor the
Slice-1 gate proves", and the sweep instruction the spec carries reaches them.
Carried forward as a correction to catalog item 1 in `### Carried forward` below.

### 4. Imports compared across the shadow overviews

One-way, and unchanged by this cycle:

- The module's only first-party import is
  `django_strawberry_framework.utils.imports.require_optional_module` — the
  documented D1 direction (leaf → shared primitive), not a boundary crossing. Its
  `debug_toolbar` / `strawberry` / `django` statement imports sit deliberately
  below the guard under `# noqa: E402`, which is Decision 5's shape.
- The test file imports the package only at its root (`import
  django_strawberry_framework`) and reaches the asset through
  `django_strawberry_framework.__file__`, never a repo-relative path; its one new
  import this cycle is stdlib `re`. Its reach out of `tests/` to read
  `pyproject.toml` copies `tests/test_ci_governance.py`'s established idiom.
- No package module imports a test; the asset imports nothing and patches two
  globals.
- **Django / ORM markers: `None`** in the module overview, so there is no
  ORM/queryset pattern to centralise and no entry owing a justification.

No sibling imports outside its documented boundary.

### 5. Every cohort's `What looks solid` / `DRY findings` / `Notes for Worker 1`, walked

Walked in all three artifacts across all passes. Cohort C's final verification
already assembled an 11-item `### Deferred work catalog`; each item was graded
here against the question the dispatch asks — does it belong *here, now*?

| Catalog item | Belongs here, now? |
| --- | --- |
| 1 floor's ungated restatements | **No** — three of the sites are maintainer-fenced and one is outside this pass's write set. But its **enumeration is incomplete** and its instruction is the half that matters; corrected below. |
| 2 `docs/GLOSSARY.md` stale entry | No — fenced out and DB-backed (ORM edit plus regenerate). |
| 3 DRF twin false-population comment | No — different spec, different write set. |
| 4 `DEBUG_TOOLBAR_FLOOR` refinement | No — `utils/imports.py` and `tests/test_ci_governance.py` are out of scope; trigger fired, correctly catalogued as a refinement. |
| 5 re-needle `no-upstream-value-returning-panel-map` | **Its warrant changes** — see `### I4`. Still not mine (Worker 1 writes no tests), so it becomes a builder dispatch rather than a catalog item. |
| 6 JS-runtime question | No — maintainer decision, homed at close-out by name. |
| 7 Decision 1 template sentence across archived specs | No — other specs' write set. |
| 8 two package-relative citations in the spec | **No, and the reason is stronger than the catalog's** — see `### I6`. |
| 9 `## Implementation plan` opener | No — recorded as decided, not work. |
| 10 concurrent session's queued work in the test file | No — a handover note. |
| 11 Worker 2's routed Test 16 rewording | No — discharged in Cohort C, correctly recorded as closed. |

Nothing the catalog holds was found to belong here. What the catalog **missed**
is below.

### 6. Staged-anchor sweep

```
grep -rEn 'TODO\(spec-042|TODO-(ALPHA|BETA|STABLE)-042' .
```

**One hit tree-wide, and it is not an anchor.**
`docs/SPECS/spec-042-debug_toolbar-0_0_14.md` #"seam carries a `TODO(spec-042
Slice N)` source anchor per" is the Slice-1 checklist box *stating the
obligation*, quoting the anchor form inside backticks. Excluding `KANBAN.md` /
`KANBAN.html` / `BACKLOG.md` changes nothing — none of the three carries one.

Zero staged anchors survive in shipped source, tests or comments. Nothing to
discharge, nothing to route. Worth naming the shape: a sweep for an anchor form
matches every document that *defines* the form, so the hit count is not the
finding until each hit is read.

---

## Findings

### I1 — a rationale entry Cohort A wrote in the present tense, falsified by Cohort C's code (closed here)

**This is the seam the pass exists for.** Cohort A authored
`docs/SPECS/appx/spec-042-debug_toolbar-0_0_14-rationale.md` before any of
Cohort C's work existed. Its `## Post-ship corrections` F7 entry closed with
*"the module docstring enumerates (1) and (2) and closes 'No other Python
behavior differs', which now understates (3) … outside this cohort's write
set"* — a present-tense claim about a source file, and the exact sentence Cohort
C's dispatched "stale docstring line" item then retired. Measured: the closer
occurs **0** times in the module today, and the docstring names all three
divergences.

Cohort C's Worker 1 **did** sweep the parallel site — the Decision 6 change
record already reads "it now enumerates the three Python divergences by name …
and the closer is gone rather than renumbered". It did not sweep the
post-ship-correction entry. `START.md` #"Partial claim fix = dominant residual
defect": one spelling fixed, the parallel site in the same file still live.

No single cohort could see it: A owns the sentence and closed before C existed; B
writes no spec text; C's two five-homes re-audits walked the contract homes and
the Borrowing-posture entry, which is where its own edits landed. The
cross-cohort read is the only instrument that opens A's text after C's code.

**Closed in this pass** — rationale edit 1 below.

### I2 — the spec's rationale pointer strands five inbound `spec-042 Revision N` citations (closed here)

Cohort A cut the nine-entry `Revision history` block out of the spec and
preserved the revision names in the rationale's `## Round vocabulary`
deliberately, recording that it did so because sibling specs cite them. Measured
**before this pass**: `grep -i revision` over the spec returned **0**
occurrences — including in the pointer that replaced the block, which names
"every change it has undergone" and never the word. So a reader arriving from a
`spec-042 Revision N` citation opened the spec, found the word nowhere, and had
no path to the companion. (After spec edit 1 the reading is **2**, both inside
the new signpost; `Revision [0-9]` stays at **0**, since the signpost names the
citation form and restates no revision.)

The inbound population, measured tree-wide rather than enumerated: **five**, in
two groups — three in `docs/SPECS/spec-043-test_client-0_0_14.md` ("spec-042
Revision 8", the shipped-spec closeout convention), which the rationale already
names, and **two in first-party test source**,
`tests/middleware/test_debug_toolbar.py` lines 21 and 121, both "spec-042
Revision 5", which no cohort's sweep population contained: A swept the
spec/rationale pair, B graded code against contract, C swept asset needles and
floor literals.

**Not a defect in the citers, and the grading matters.** `START.md` #"Bare
`Decision N` / `DoD N` = repo-wide convention, not defect" and `KANBAN.md`'s own
numbered-item-citation item grade this vocabulary **by anchor**, and all five are
anchored to the spec by name. Both test-file sites additionally state the reason
they cite in the adjacent clause, so the label carries no orphaned WHY. What the
move owed was a **destination**, and the destination's signpost was missing.

A prior cycle had already looked at this and deferred it on a warrant this cycle
falsified: `docs/builder/DONE/build-040-auth_mutations-0_0_13.md` #"Deferred
entries 3 and 5 were correctly NOT homed" reasons that the five citations resolve
"today" because the spec *still carries* `Revision 5` ×9, `Revision 7` ×2 and
`Revision 8` ×1 "with no rationale companion". Both halves of that ground are now
false. That artifact is closed — **recorded, not edited**.

**Closed in this pass** — spec edit 1 and rationale edit 2 below, both halves of
the pair swept together.

### I3 — the M4 fix published a sweep instruction whose needle cannot see the population it points at (half closed here; half needs a builder)

**Medium.** Graded Medium for the reason Cohort B graded M4 Medium rather than
Low: this comment is not decoration, it is *the instruction a floor bump
follows*.

M4's root-cause fix replaced a false count with an instruction — name the gated
trio by mechanism, and tell a bump to *sweep the tree* rather than trust an
enumeration. The sweep is therefore the load-bearing instrument, and the needle
it names, `django-debug-toolbar>=`, provably **misses a live restatement**:
`CHANGELOG.md:61` writes the name and the constraint with a backtick and a space
between them. Measured both ways this pass over a stated corpus: the loose needle
finds exactly one restatement the tight needle does not, and it is that line.

The cycle knows. `docs/SPECS/appx/…-rationale.md` #"accepting that the sweep
itself owes more than one spelling" records the lesson, and the deferred-work
catalog's item 1 carries it for a future card. But the instruction itself is
published at **six** sites and only the rationale's carried the caveat — the
other five all named the bare specifier. That is `START.md` #"Partial claim fix =
dominant residual defect" one level down from M4: the count was corrected and the
instrument that replaced it was left bounded by one spelling. Shipping it that way
means a bump follows the corrected instruction and still misses a site, which is
M4's own defect class reproduced inside M4's fix.

Split by write set:

- **Mine, closed in this pass** — the three spec sites: the Slice-1 dependency
  box, Decision 5, and the `## Risks and open questions` bullet (spec edits 2-4),
  plus the rationale's change record (rationale edit 3).
- **A builder's** — the three code sites:
  `django_strawberry_framework/middleware/debug_toolbar.py` #"included, is gated
  by nothing, so a floor bump sweeps the tree for the", and
  `tests/middleware/test_debug_toolbar.py` at both the `_HINT_SUBSTRING` comment
  and `::test_install_hint_floor_matches_the_pyproject_dev_group_row`'s
  docstring. One clause each; the contract is *state the sweep's instrument
  honestly* — sweep the package **name** and read each hit, never the `>=`
  specifier alone — not any particular wording.

Note that the fix is **not** "use a looser regex": the bare name occurs 134 times
tree-wide, so the honest instruction is a name sweep whose hits are read, and
saying so is the whole point. `tests/middleware/test_debug_toolbar.py` #"assert
its `django-debug-toolbar>=` dev-group row is exactly the re-typed" and the
governance row's own `re.findall` are **not** in scope: there the specifier
spelling is fixed by TOML and the regex is the gate, not the sweep.

### I4 — existence challenge on the predicate table: one row can never fail alone (needs a builder)

**Medium.** The dispatch asks the existence question of the eight predicate
constructors and the 57 rows. Answered by measurement, not by argument.

**The table should exist.** Cohort B measured its monolithic predecessor at
**1** failing row for the removal of *any* template guard and **1** for the
removal of *all* of them; the table measures each family separately. Deleting it
returns the asset to a state where the suite cannot distinguish one dropped guard
from seven. It is not an abstraction over duplication — it is the only instrument
in the file whose output tracks what it measures.

**The eight constructors should all exist**, and the evidence is that their
failing sets are disjoint rather than that they read differently. `_adjacent`
fires for both spellings of a conditional scrub; `_own_statement_line` only for
the inline one; `_unnested_within` only for the braced one — so adjacency alone
would hold each spelling at a single row, which `### Acceptance rule: weakly
pinned is revision-needed` does not permit, and the two siblings are what lift
each to two. `_return_count_between` answers a question none of the other seven
asks (count a token across a span) and its rows fail for weakenings that fail
none of the adjacency family's, measured in both directions by Cohort C. No two
constructors are near-copies.

**One row should not exist as needled.** Checked mechanically, pairwise across
every needle in the landed table rather than by reading:
`no-upstream-value-returning-panel-map` is `_absent("`.map(([id, panel])`")` and
`no-upstream-raw-panel-key-binding` is `_absent("`([id, panel])`")`. The first
needle **contains** the second, so any text failing the longer row fails the
shorter one too: the row cannot produce a failing node id the table does not
already have. Exactly one such pair exists in the table (57 rows, 57 unique ids,
one containment pair).

This is sharper than the L5-2 that Cohort C recorded and catalogued. L5-2 found
the row's *reach over a partial hand-revert* had narrowed and correctly graded it
an improvement, because the row is not inert by the falsifier `## Test plan` Test
16 states — its needle does occur once in upstream's asset. Subsumption is a
second defect with the same symptom and a different instrument: **inertness is
found by counting the needle in the borrow; subsumption is found by comparing the
table's needles to each other**, and nothing in this cycle ran the second check.

The fix is the one the catalog already derived and measured, which is why this
raises its warrant rather than changing it: re-needle to `` `.panels).map(` ``
(1 occurrence upstream, 0 in the port, binding-agnostic, and not a superstring of
any sibling). **Do not** use `Object.entries(toolbar.panels).map(` — 0
occurrences upstream, therefore inert, the trap this cycle has now met three
times. One argument, one file, `tests/middleware/test_debug_toolbar.py`.

`AGENTS.md` rule 5 is why this is a dispatch and not a catalog item: the derived
fix exists, it is one argument, and deferring it leaves a row in the tree that
reads green forever.

### I5 — the absence rows, independently checked (no defect)

The check that would have surfaced a problem had one existed. `## Test plan` Test
16 names a falsifier — "an absence row whose needle upstream does not actually
carry — a needle the borrow never spells can never fail, and reads exactly like a
working row". Run against the borrow itself
(`~/projects/strawberry-django-main/strawberry_django/templates/strawberry_django/debug_toolbar.html`),
occurrences in both assets:

| Row | upstream | port |
| --- | --- | --- |
| `no-upstream-single-argument-parse` | 1 | 0 |
| `no-upstream-own-hasownproperty-call` | 1 | 0 |
| `no-upstream-value-returning-panel-map` | 1 | 0 |
| `no-upstream-raw-panel-key-binding` | 1 | 0 |
| `no-document-level-nav-lookup` | 1 | 0 |
| `no-upstream-chained-panel-title-write` | 1 | 0 |
| `no-post-scrub-read-of-panels` | 1 | 0 |
| `no-post-scrub-read-of-request-id` | 1 | 0 |

Eight of eight fire on a verbatim paste and none is inert. Test 16's stated
falsifier does not fire. (What it does not cover is I4's containment, which is
why I4 is a finding and this is not.)

### I6 — the package-relative citations: correctly deferred, and the catalog's population is short by one

Catalog item 8 names "two package-relative citations in the spec"
(`utils/imports.py::require_optional_module`) and defers them. Re-derived by
parsing both files for every `*.py::Symbol` form and testing each path against
disk: **2 in the spec, 0 in the rationale** — the figure holds.

But the population is **three**: `docs/SPECS/spec-041-channels_router-0_0_14.md`
carries the identical spelling once, and it is outside this pass's write set.
Fixing only the two I own would be `START.md`'s partial-claim-fix shape exactly —
the sibling stays live while the population reads as retired. So the deferral is
right for a stronger reason than the catalog gives, and the catalog item needs
its third site. Carried forward, not fixed.

### I7 — comments tell one coherent story (no defect)

Checked across the module docstring, the module's `_DEBUG_TOOLBAR_INSTALL_HINT`
comment block, the test file's module docstring and `_HINT_SUBSTRING` comment, the
predicate table's block comment, and the asset's own comments:

- The gated-population framing is **the same claim in the same words** at the
  module comment and the test comment — a deliberate mirror, not drift — and both
  say "GATED sites, not a census". Neither publishes a numeral for the whole
  population. (Their sweep instrument is I3; the framing itself is coherent.)
- The divergence framing agrees in all three homes: the docstring names the
  Python divergences and declines to count the template's; the table's block
  comment states the both-halves rule per kind; `## Borrowing posture` enumerates
  seven bullets and `seven` occurs at exactly its three sites.
- **No banned process provenance** in the three files: swept for cohort/worker
  attribution, round numbering, severity labels, "as of 0.0.N" and "previously" —
  the only hits are the two anchored `spec-042 Revision 5` citations of I2, which
  the repo's own anchor grading does not treat as defects.
- The asset's comments state invariants ("The one question every read below
  depends on…") rather than history.

### I8 — exports, responsibilities, ORM patterns (no defect)

`git diff HEAD -- django_strawberry_framework/__init__.py` is **0 lines**;
`__all__` and the re-export list are unchanged and the cycle added no public
name — `isRecord` is IIFE-local, and the table and its eight predicates are
module-private in the test file. Responsibilities did not move between modules:
the middleware still owns detection and rewriting, the asset the browser-side
bridge, the test file the text contract. Django/ORM markers are `None`, so there
is no repeated queryset pattern to centralise.

---

## DRY findings

- **The table's needles duplicate the asset's text, and that is the instrument
  rather than a duplication to remove.** ~35 substring needles quote lines of an
  89-line asset, several of them more than once. Both prior passes recorded the
  reason and it survives at cross-cohort altitude: the duplication is
  *self-detecting* — reword the asset's scrub line and eight rows fail loudly in
  one run — and hoisting a needle into a shared constant would let **one** edit
  silently re-needle several rows at once, which is precisely the drift this
  cycle's evidence chain is built to detect. Not a finding.
- **The standing recommendation both prior passes left open stays open, and it is
  not mine.** `delete data.debugToolbar` (5x) and `delete data.debugToolbar;`
  (5x) are two spellings of one asset statement, differing only by a semicolon
  and not load-bearingly different. Collapse them to one module constant *if the
  file is reopened for another reason* — which I3 and I4 now reopen it for.
  Recorded as a should, not a must, in the dispatch below.
- **The regex-over-`pyproject.toml` governance idiom remains at three sites in
  two files**, with the extraction correctly declined inside the fence and
  carried as catalog item 4. Re-read; nothing changes it.
- **Existence challenges** — the table, the eight predicates, `isRecord`: all
  answered above under I4. One row fails the challenge as needled.
- **No duplicated helper across cohorts.** Cohort A wrote prose, Cohort B wrote
  no source, Cohort C's only new package-side shape is `isRecord`, which has four
  real call sites and replaces four spellings of one predicate.

---

## Spec changes made (Worker 1 only)

Each edit states the corrected contract directly — no amendment block, no
chronology, no cohort provenance. Census before writing **and re-measured after**,
occurrences rather than matching lines, because the pass that publishes a figure
about a file it is editing is the pass most likely to publish a stale one:
`Revision [0-9]` in the spec **0** before, **0** after — the new signpost names
the citation *form* and restates no revision; the bare word `revision` goes
**0 → 2**, both inside that signpost, which is the edit's whole purpose; `seven`
**3 → 3**, the same three sites; value-bearing `django-debug-toolbar>=7.0.0`
**7 → 7** — no floor value was added, moved or removed by this pass.

Spec (`docs/SPECS/spec-042-debug_toolbar-0_0_14.md`):

1. **The rationale pointer** (the paragraph opening "Deliberation for every
   decision below") gains a sentence naming the revision vocabulary as living in
   the companion's `## Round vocabulary` and nowhere in the spec, and saying that
   a `spec-042 Revision N` citation — first-party source and sibling specs both
   carry some — resolves there. *Reason:* the spec carried **0** occurrences of
   the word, so five inbound citations had no path at the file they name. *I2.*
2. **`## Slice checklist`, the dependency box** — the sweep instruction now says
   to sweep for the package **name** and read each hit, and names the `>=`
   specifier as the narrower instrument a restatement separating the name from
   the constraint does not match. *Reason:* the instruction a floor bump follows
   named an instrument that provably misses a live site. *I3.*
3. **Decision 5** — same correction, stated as why the specifier is the narrower
   instrument. *I3.*
4. **`## Risks and open questions`, the three-places bullet** — same correction.
   *I3.* All three say the same thing because all three are the same instruction;
   the three code sites that also carry it are the builder's half.

Rationale (`docs/SPECS/appx/spec-042-debug_toolbar-0_0_14-rationale.md`):

1. **`## Post-ship corrections`, F7's closing note** — the present-tense
   understatement claim becomes the discharged record it now is, naming what the
   docstring says today and cross-linking the Decision 6 change record that
   already said so. *Reason:* the sentence was false against the tree. *I1.*
2. **`## How to read this file`, the "No timeline" bullet** — the warrant for
   keeping the revision names widens from "three sentences in spec-043" to the
   measured population of five across two groups, names the two first-party
   test-source citers, and states the anchor grading under which none of them is
   a defect. *Reason:* an enumeration presented as the population, in the file
   whose cycle retired that shape. *I2.*
3. **Decision 5's change record** — the rule now names the sweep's own
   instrument (the package name, each hit read) rather than accepting in passing
   that "the sweep owes more than one spelling", with the reason a correction
   that fixes the count and leaves the needle reproduces the defect one level
   down. *I3.*
4. **`### Borrowing posture — the template port`, the table's self-claim change
   record** — a further measured lesson: an absence needle containing another
   absence needle in the same table can never fail alone; inertness and
   subsumption are different defects with the same symptom and are caught by
   different instruments (occurrence counts in both assets; pairwise containment
   across the table's own needles). The bullet list's leading numeral was
   **removed** in the same edit rather than incremented — a count of a list later
   work extends is the shape this cycle spent three passes retiring. *I4.*

Byte counts: spec 161,287 → 162,175; rationale 67,234 → 69,443. This pass wrote
no source and no tests.

---

## Gates

| Gate | Command | Result |
| --- | --- | --- |
| Spec glossary | `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-042-debug_toolbar-0_0_14.md` | `OK: 24 terms - all have glossary entries and at least one spec link.` |
| Citations | `uv run python scripts/check_citations.py --check` | `OK: 992 citations resolve (823 in 441 .py files, 169 in KANBAN.md).` — reads `.py` + `KANBAN.md` only, so it says nothing about either file this pass wrote |
| Whitespace | `git diff --check` (whole tree) | exit 0 |
| Format | `uv run ruff format --check .` | `444 files already formatted` |
| Lint | `uv run ruff check .` | `All checks passed!` (never `--fix`) |
| Source layout | `uv run python scripts/check_trailing_commas.py --check <the spec and the rationale>` | exit 0 — explicit paths only, since its default is a repo-wide auto-fix over the concurrent session's files |
| Focused suite | `uv run pytest tests/middleware/test_debug_toolbar.py examples/fakeshop/test_query/test_debug_toolbar_api.py -n0 --no-cov` | **86 passed**, exit 0, 0 collection errors. No `--cov*` flag in this pass; no full sweep (`AGENTS.md` #"No pytest after edits" — the maintainer did not ask, and the tree carries another cycle's work) |
| Link convention + rule-27 forms | own verifier over both files | spec 73 defs / 73 used, rationale 26 / 26; 0 undefined refs, 0 orphan defs, 0 broken in-page anchors (104 + 22 checked), 0 missing def targets, 0 broken cross-file anchors, 0 `path:NN` |

**The verifier was positive-controlled before its green was believed** — an
invented `[no-such-ref]` and an invented `#no-such-heading` appended to a scratch
copy, both reported, the copy removed. My own verifier has now been wrong twice in
this cycle and the file right both times, which is why the control runs every
time.

---

## Final status

`revision-needed`.

Two findings need a change to files this pass may not write, and `BUILD.md`
`## Cross-slice integration pass` is explicit that this is what the integration
pass does with them: *"If DRY opportunities are found, Worker 1 records them in
`bld-integration.md` and asks Worker 0 to dispatch Worker 2 for a consolidation
pass and Worker 3 for a review pass. Repeat until clean."*
`### Isolation is non-waivable` holds — the planner writes no source.

**Worker 0 must dispatch a builder.** One pass, two files, both already in Cohort
C's declared ownership, so the partition needs no change:

| # | File | Contract |
| --- | --- | --- |
| I3 | `django_strawberry_framework/middleware/debug_toolbar.py` (the `_DEBUG_TOOLBAR_INSTALL_HINT` comment block) and `tests/middleware/test_debug_toolbar.py` (the `_HINT_SUBSTRING` comment **and** `::test_install_hint_floor_matches_the_pyproject_dev_group_row`'s docstring — all three sites, or it is the partial fix again) | The published sweep instruction states an instrument that can see the population it points at: sweep the package **name**, read each hit; the `>=` specifier is the narrower form and misses a restatement that separates the name from the constraint. No numeral for any population. The spec and the rationale already say this; the code sites are what a bump reads. |
| I4 | `tests/middleware/test_debug_toolbar.py` (`_TEMPLATE_CONTRACT`, the `no-upstream-value-returning-panel-map` row) | No absence row's needle contains another absence row's needle, so every row can fail on its own. The derived and measured fix is the needle `` `.panels).map(` `` (1 occurrence upstream, 0 in the port); **not** `Object.entries(toolbar.panels).map(`, which is 0 upstream and therefore inert. Re-measure the row-set delta on the `forEach` → `.map` revert in both its spellings (whole-form and binding-preserving) and record both. |

Neither is a new production boundary, so neither owes a new failability entry —
but the builder's proof obligation is the row-set measurement above, and Worker 3
should re-run the pairwise-containment check over the landed table rather than
accept that the one pair is gone.

While that file is open, the DRY recommendation both prior reviews left standing
becomes cheap: collapse `delete data.debugToolbar` / `delete data.debugToolbar;`
to one module constant used by all ten rows. Recommended, not required, and
explicitly not a gate on acceptance.

**The integration pass then re-runs** (`BUILD.md`: "Repeat until clean") before
`docs/builder/bld-042-final.md`.

What is clean, with the evidence that would have shown otherwise: the
staged-anchor sweep is empty and its one hit was read rather than counted; all
eight absence needles occur in the borrow and none in the port, so Test 16's own
stated falsifier does not fire; the module's AST is identical to HEAD with
docstrings stripped, independently re-derived, so no Python behavior moved; the
public surface diff is zero lines; the five contract homes agree with each other
and with the tree on the seven diverged forms; both retired Cohort A claims
(`debug_toolbar_urls.py`, `0.262.0`) still measure 0 in the spec; and the focused
suite is 86 green.

---

## Carried forward — corrections the final gate's `### Deferred work catalog` must hold

`docs/builder/bld-042-final.md` copies Cohort C's 11-item catalog. Four items
need amending before it does, and one is new. Each keeps a named owner.

1. **Item 1's enumeration is short, one of its sites is a pair, and its
   instruction is the half that matters.** Add the spec's own seven value-bearing
   restatements; record that the `-terms.csv` soft-dependency row has a DB twin
   at `glossary_glossaryspecmention.notes` in `examples/fakeshop/db.sqlite3`, so
   that site is a CSV edit **and** an ORM edit plus regenerate; replace the
   item's "24 / 25" with the reproducible half — the loose needle finds exactly
   one restatement the tight one misses — since the absolute count is a function
   of an unstated corpus; and say plainly that the sweep a bump owes is over the
   package **name** with each hit read. Record the census instrument failure with
   it: a `grep -v` content filter used as a path filter deletes exactly the rows
   whose text mentions the excluded path.
   *Owner:* unchanged — the card that next raises the `[dependency-groups].dev`
   specifier.
2. **Item 5 is superseded by finding I4** and should be carried as a dispatched
   builder item rather than deferred work, unless the maintainer declines the
   dispatch — in which case it is carried forward with the subsumption
   measurement attached, not with L5-2's "narrowed reach" framing alone.
   *Owner:* this cycle's builder pass; failing that, whoever next opens
   `tests/middleware/test_debug_toolbar.py`.
3. **Item 8's population is three, not two.** The third is
   `docs/SPECS/spec-041-channels_router-0_0_14.md`, same spelling, once. A
   sweeper fixing the two named would leave the sibling live and read the
   population as closed. *Owner:* unchanged — the next `docs/SPECS/NEXT.md`
   Step 8 archival sweep, which is also item 7's owner.
4. **New: a prior cycle's closed artifact carries a warrant this cycle
   falsified.** `docs/builder/DONE/build-040-auth_mutations-0_0_13.md`
   #"Deferred entries 3 and 5 were correctly NOT homed" defers the five
   `spec-042 Revision N` citations on the ground that the spec still carries the
   revision names and has no rationale companion. Both halves are now false —
   the block moved and the companion exists — while the **conclusion** stays
   correct, because Cohort A preserved the names and this pass added the spec's
   signpost (I2). Catalogued so a later reader does not re-derive the wrong
   conclusion from a warrant that no longer holds; that artifact is closed and
   was not edited. *Owner:* nobody — recorded as decided.
5. **Item 6 (the JS-runtime question) gains one sentence of evidence from this
   pass**, not a change of framing: the absence rows were independently confirmed
   to fire on a verbatim paste and only on one, so "the rows detect an upstream
   paste and nothing else" is now measured in both assets rather than reasoned.
   *Owner:* unchanged — the maintainer, at close-out.

Items 2, 3, 4, 7, 9, 10 and 11 carry forward unchanged.

---

## Concurrent-session baseline

A reading, not a constant — and a reading of a population this pass is itself
editing, which is the failure mode to name rather than to round off.
`git status --short` returned **76** paths before this artifact existed,
reproducing Cohort C's final reading exactly, and returns **77** after it, the
delta being this file. This cycle's paths are the three code/test files, the
modified spec, and six untracked `042` files (the rationale, the three cohort
artifacts, the build plan, and this artifact); every other path is the concurrent
session's and was neither read as build output nor edited nor reverted
(`AGENTS.md` rule 34). Take a fresh reading at the final gate; never compare
against either number here.

---

## Build report (Worker 2)

The consolidation pass the integration pass dispatched: findings **I3** (the
three code sites of the sweep instruction) and **I4** (the subsumed absence
needle). Two files written, plus this artifact, a new manifest and its report.
No existing manifest, report or probe script under `docs/builder/temp-tests/042/`
was overwritten, no table row was renamed or removed, and the spec, the
rationale, the three closed cohort artifacts, the build plan and every fenced
surface (`CHANGELOG.md` included) were read-only or untouched.

### Files touched

Grounded in `git status --short`, not memory.

- `django_strawberry_framework/middleware/debug_toolbar.py` - I3 site 1: the
  `_DEBUG_TOOLBAR_INSTALL_HINT` comment block now states the sweep's instrument
  as the package **name** with each hit read, and names the `>=` specifier as
  the narrower form a restatement separating name from constraint does not
  match. Comment bytes only; no executable token moved (inverse proof below).
- `tests/middleware/test_debug_toolbar.py` - I3 sites 2 and 3 (the
  `_HINT_SUBSTRING` comment and
  `::test_install_hint_floor_matches_the_pyproject_dev_group_row`'s docstring),
  the same instruction in the same words; I4's re-needle on the
  `no-upstream-value-returning-panel-map` row; one clause added to the table's
  own falsifier list so the rule that forbids a subsumed needle sits where the
  next editor writes a row; and the mandatory-scrub needle named once as
  `_SCRUB` / `_SCRUB_STATEMENT` (the DRY item both prior reviews left standing).
- `docs/builder/temp-tests/042/proofs-042-integration-i4.json` and
  `docs/builder/temp-tests/042/proofs-report-042-integration-i4.md` - new,
  distinctly named, `042` kept.
- `docs/builder/bld-042-integration.md` - this report; `Status: built`.

`django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html`
was **not** written by this pass. It carries the cycle's earlier work and shows
`M` for that reason; the proofs below mutate it transiently and restore it, and
its SHA-256 after this pass -
`92cd040294ad2dba26158c652f92b9760cd35b64b91f848822a1fa093e17fa00` - is the same
value the prior pass's restore proof recorded.

### Tests added or updated

- `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence[no-upstream-value-returning-panel-map]`
  - needle `.map(([id, panel])` becomes `.panels).map(`. **The id is unchanged**,
  so the 32 node ids the three prior proof records cite all still resolve; the
  table is still 57 rows with 57 unique ids.
- No row added, renamed or removed. Every other row's resolved needle is
  byte-identical across this pass (evidence under `### Implementation notes`).

### Validation run

- `uv run ruff format django_strawberry_framework/middleware/debug_toolbar.py tests/middleware/test_debug_toolbar.py` - pass (scoped to this pass's files, never `.`).
- `uv run ruff check --fix <the same two files>` - `All checks passed!`.
- `uv run python scripts/check_trailing_commas.py <the same two files>` - rewrote one file: naming the scrub needle shortened three table rows below the explode threshold, so it collapsed them. Re-ran `ruff format` on the test file, then `--check` on both: exit 0, `2 files already formatted`.
- `uv run python scripts/check_citations.py --check` - `OK: 992 citations resolve (823 in 441 .py files, 169 in KANBAN.md).`
- `git diff --check` (whole tree) - exit 0.
- `git status --short | wc -l` - **77**, the same reading the integration pass recorded after its own artifact existed; this pass adds no path (the two new files sit under the gitignored `temp-tests/`). Every modified file is accounted for above; the concurrent session's paths were neither edited nor reverted (`AGENTS.md` rule 34), and nothing was stashed, checked out or restored.
- `uv run pytest tests/middleware/test_debug_toolbar.py examples/fakeshop/test_query/test_debug_toolbar_api.py -n0 --no-cov` - **86 passed**, exit 0, 0 collection errors, after every edit and after the last revert. No `--cov*` flag; no full sweep.

### Failability proofs

Manifest `docs/builder/temp-tests/042/proofs-042-integration-i4.json`, report
`docs/builder/temp-tests/042/proofs-report-042-integration-i4.md`, run by
`uv run python scripts/prove_failability.py <manifest> --output <report>`, exit
**0**. Anchors checked first (`--check-anchors-only`; all three matched exactly
once) before any mutation; scratch root outside the repo
(`<scratchpad>/failability-042-integration-i4`); a pre-mutation baseline run for
every entry; one mutation live at a time, reverted before the next; no
`ACTIVE-MUTATION.json` marker remains.

This pass introduces **no new production boundary**, so none of the three is a
new-boundary entry. They are the measurement I4 owes: the re-needled row must
now produce a failing node id the table does not otherwise produce.

- `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html #"Object.entries(toolbar.panels).forEach"` - **the binding-preserving revert**, the spelling under which the subsumed needle could not fire. Mutation applied: `Object.entries(toolbar.panels).forEach(([panelId, panel]) => {` -> `Object.entries(toolbar.panels).map(([panelId, panel]) => {`. Scope as run: `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE -n0 tests/middleware/test_debug_toolbar.py examples/fakeshop/test_query/test_debug_toolbar_api.py`. Pre-mutation state of that scope: `86 passed`, exit 0, 0 pre-existing failing rows. Collection/setup errors: 0. Failing node ids:
  - `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence[panel-loop-is-foreach]`
  - `tests/middleware/test_debug_toolbar.py::test_template_port_invariants_and_robustness_divergence[no-upstream-value-returning-panel-map]`

  Revert proved by byte comparison: `filecmp.cmp(shallow=False) True; sha256 92cd040294ad2dba... == 92cd040294ad2dba...` against the pre-mutation copy.

  **This is the I4 proof.** The same mutation at the same scope was measured by the prior pass's supplementary run (`docs/builder/temp-tests/042/proofs-report-worker3-pass3-supplementary.md`, entry 2) at **one** row - `[panel-loop-is-foreach]` alone, the subsumed row silent. The set difference is exactly `[no-upstream-value-returning-panel-map]`: a failing node id the table did not otherwise produce, which is what "the row can fail alone" means. Two rows clears the weakly-pinned threshold and sits inside Worker 3's mandatory re-run floor.

- `.../debug_toolbar.html #"Object.entries(toolbar.panels).forEach"` - **the whole-form revert**, upstream's own line pasted verbatim (`Object.entries(data.debugToolbar.panels).map(([id, panel]) => {`), the failure the row was written to catch. Same scope, same pre-mutation state (`86 passed`, exit 0, 0 pre-existing rows). Collection/setup errors: 0. Failing node ids:
  - `...[scrub-before-panel-loop]`
  - `...[panel-loop-is-foreach]`
  - `...[no-upstream-value-returning-panel-map]`
  - `...[no-upstream-raw-panel-key-binding]`
  - `...[payload-shape-guard-before-panel-loop]`
  - `...[panel-record-guard-first-in-loop]`
  - `...[no-post-scrub-read-of-panels]`

  Revert proved: `filecmp.cmp(shallow=False) True; sha256 92cd040294ad2dba... == 92cd040294ad2dba...`. Both absence rows fire here, so the narrower needle keeps the verbatim-paste reach the wider one had and gains the partial-revert reach it lacked.

- `.../debug_toolbar.html #"delete data.debugToolbar;"` - **the scrub deleted**, re-measured because this pass replaced ten typed copies of that needle with one constant. Same scope, same pre-mutation state. Collection/setup errors: 0. Failing node ids: `[scrub-key-deleted]`, `[scrub-immediately-follows-capture]`, `[scrub-is-its-own-statement]`, `[scrub-not-nested-inside-update]`, `[no-return-between-entry-guard-and-scrub]`, `[entry-guard-return-is-the-only-one-before-the-scrub]`, `[scrub-before-null-handle-bail]`, `[scrub-before-payload-shape-guard]`, `[scrub-before-panel-loop]`, `[scrub-before-request-id-write]` - **the same ten ids** the prior pass measured for the same mutation at the same scope, set-identical. Revert proved: `filecmp.cmp(shallow=False) True; sha256 92cd040294ad2dba... == 92cd040294ad2dba...`. That set identity is the evidence the DRY collapse changed no needle.

No zero-row entry, so no `why 0` judgement is owed.

**Inverse proof for the comment-only production edit.** The middleware change is
comment bytes, so `BUILD.md` owes AST identity rather than a failability entry:
`ast.dump()` of the module with every docstring stripped, HEAD obtained
read-only via `git show HEAD:` into a scratch path outside the repo (never
`git checkout`, never a stash). **`12387 == 12387`, identical: True** - the same
digest length the earlier passes in this cycle recorded, measured against HEAD
and against the pre-edit working tree both.

### Hot-path budget

Not applicable; the dispatch declares hot-path `none`. The changes are comment
and docstring bytes plus one test needle and one test-local constant; no
production expression, branch or call was added or moved.

### Floor verification

Not applicable; the dispatch declares floor-verification scope `none`. No
Django / Strawberry / channels seam is touched. Floor facts, copied from
`docs/builder/BUILD.md` `## Floor verification` rather than from memory: Django
**5.2.16** on Python **3.10** with strawberry-graphql **0.316.0**. No venv was
built and the shared `.venv` was not mutated.

### Implementation notes

- **One phrasing, taken from the spec, not a third one.** All three code sites
  now say what the spec's Slice-1 dependency box, Decision 5 and
  `## Risks and open questions` say: sweep the package name and read each hit;
  the `>=` specifier is the narrower instrument, and a restatement separating
  the name from the constraint with a backtick or a space does not match it.
  No site publishes a count of anything - not of gated sites, not of
  restatements, not of hits. The gated trio is still named by mechanism (the
  test compares hint to literal and literal to the dependency row), which is a
  statement a reader can check rather than a number that rots.
- **The governance row's own `re.findall` is untouched.** There the specifier
  spelling is fixed by TOML and the regex is the gate, not the sweep; only the
  docstring's closing paragraph, which describes the sweep, changed.
- **The I4 needle is `.panels).map(`, measured rather than argued.** Occurrences
  counted in both assets this pass: `.panels).map(` - **1** upstream, **0** in
  the port; the old needle `.map(([id, panel])` - 1 and 0; the sibling needle
  `([id, panel])` - 1 and 0; and `Object.entries(toolbar.panels).map(` - **0**
  upstream, therefore inert, which is why it was not used. Upstream's line is
  `Object.entries(data.debugToolbar.panels).map(([id, panel]) => {`, so the
  fragment names the divergence (a value-returning call on the panels map) and
  nothing of the binding, which is the sibling row's subject.
- **Pairwise containment re-derived over the landed table, not assumed.** A
  scratch probe resolves every row's predicate arguments through the module's
  constants and compares the two versions of the file: 57 rows before and after,
  0 ids added or removed, **exactly one row changed** (the I4 needle), 8 absence
  needles, and **0 containment pairs** among them. The probe lives in the
  session scratchpad, outside the repo, so nothing under `temp-tests/042/` was
  touched; its resolution step is what lets the `_SCRUB` constants be compared
  against the literals they replaced.
- **The rule went into the table's own comment, stated by mechanism.** An
  absence needle must occur in the borrow and in no sibling absence needle -
  inertness and subsumption side by side, since they share a symptom and are
  caught by different instruments. No numeral: the next editor extends this
  table, and a count above a list the reader is editing is the self-falsifying
  instrument this cycle has already retired twice.
- **The DRY item landed.** `_SCRUB` / `_SCRUB_STATEMENT` replaces five plus five
  typed copies of the scrub needle, and `_SCRUB_STATEMENT` is `f"{_SCRUB};"`
  rather than a second literal, so the two spellings cannot drift apart either.
  It was recommended and not required; it is cheap here because the row set and
  the node ids are provably unchanged (the needle diff above and the ten-id set
  identity in the third proof). It is the only change in this pass that is
  neither I3 nor I4, and it is confined to the file I4 already opens.

### Notes for Worker 3

- The before-measurement for I4 is entry 2 of
  `docs/builder/temp-tests/042/proofs-report-worker3-pass3-supplementary.md` -
  same mutation, same scope, **1** row. This pass's entry 1 is the after: **2**
  rows. Differencing the two sets is the cheapest way to audit the claim.
- The pairwise-containment check the integration pass asked you to re-run is
  scripted in the session scratchpad (`needle_diff_042_i4.py`); it takes two
  copies of the test file and prints row count, id delta, changed rows, and the
  containment pairs among absence needles. Re-derive it your own way if you
  prefer - the claim is 0 pairs over 8 absence needles in a 57-row table, with
  every other needle byte-identical to the pre-pass file.
- The template asset was mutated three times during the proofs and restored each
  time; its SHA-256 is unchanged from the value the prior pass's restore proof
  recorded, and no `ACTIVE-MUTATION.json` marker remains in the scratch root.
- The middleware edit is comment bytes only, so the diff is best read against
  the inverse proof rather than for behavior: nothing executable moved.

### Notes for Worker 1 (spec reconciliation)

Both items are in the rationale companion, which only Worker 1 may write. The
spec itself needs nothing from this pass - its three corrected sites are what
the code now repeats, and it states no needle.

1. **`docs/SPECS/appx/spec-042-debug_toolbar-0_0_14-rationale.md`,
   `### Borrowing posture - the template port`, the bullet opening "A rename in
   the guarded file can narrow an absence needle's reach without making it
   inert, and the row still reads green."**
   - *Current wording:* "The row asserting upstream's value-returning panel loop
     is absent is needled on that loop's whole head, binding included. When the
     port renamed the loop's key variable, the needle stopped matching a revert
     that restores upstream's `.map` while keeping the port's binding ..."
   - *Recommended replacement:* keep the generalized lesson verbatim (its
     closing clause, that the narrower needle is the one that survives, is now
     the landed rule) and put the row's own history in the past tense: "...was
     needled on that loop's whole head, binding included, and a rename of the
     port's key variable narrowed it to the verbatim paste alone; it now carries
     the fragment that names only the divergence." Present tense there is false
     against the tree as of this pass.
2. **Same section, the bullet opening "An absence needle that contains another
   absence needle in the same table can never fail alone, whatever it is counted
   in."**
   - *Current wording:* "The same value-returning-panel-loop row **is** needled
     on `` `.map(([id, panel])` ``, which contains the sibling row's
     `` `([id, panel])` `` outright, so any text that fails the longer needle
     fails the shorter one too and the row adds no failing node id the table did
     not already have. ... Measured over the landed table, exactly one pair is
     subsumed, and the narrower fragment that fixes the reach above fixes the
     subsumption with it."
   - *Recommended replacement:* the rule stays; the instance becomes discharged
     and carries its measurement: "The value-returning-panel-loop row **was**
     needled on `` `.map(([id, panel])` ``, which contained the sibling row's
     `` `([id, panel])` `` outright ... It now carries `` `.panels).map(` ``
     (one occurrence upstream, none in the port), no absence needle in the table
     contains another, and the binding-preserving revert that failed one row
     under the old needle fails two under this one."
   - Left as written, it reproduces I1's shape exactly: a rationale entry in the
     present tense that the code has since falsified.

### Disposition

- **I3 - closed.** All three code sites carry the corrected instruction, in the
  spec's own words, with no published count. The partial-fix failure mode the
  finding names does not recur: the three sites were enumerated before any was
  edited, and all three landed in this diff.
- **I4 - closed, with the row-set delta measured in both revert spellings.** The
  row's id, and therefore every proof record citing it, is untouched.
- **The optional DRY recommendation - landed**, with evidence that it changed no
  needle and no node id.
- Nothing here changes a plan-level architectural call, so no structural-drift
  pause. `Status: built`.

---

## Review (Worker 3)

Reviewing the consolidation pass the cross-cohort integration pass dispatched:
**I3** (three code sites carry one sweep instruction), **I4** (the subsumed
absence needle re-needled), and the **unasked DRY item** (`_SCRUB` /
`_SCRUB_STATEMENT`). Diff read: `git diff HEAD -- django_strawberry_framework/middleware/debug_toolbar.py tests/middleware/test_debug_toolbar.py`,
scoped to this pass's contribution via `### Files touched` (`worker-3.md`
"Cumulative-diff trap": the middleware's module-docstring rewrite and the test
file's table-construction are prior cohorts' accepted work, not this pass's).

### Mutations recorded BEFORE they are made

`worker-3.md` "Scope" requires the source carve-out's mutations to appear here
before the tree is touched. Three are replays of the builder's manifest at the
recorded scope; the fourth is a mutation **no manifest in this cycle carries**,
which is where this pass's central claim can actually be falsified. All four
target `django_strawberry_framework/templates/django_strawberry_framework/debug_toolbar.html`,
one at a time, reverted before the next, scratch root outside the repository.
Live-mutation check run first: the asset's SHA-256 before any of this is
`92cd040294ad2dba26158c652f92b9760cd35b64b91f848822a1fa093e17fa00`, the value
the prior pass's restore proof recorded, so no prior agent left a mutation live.

1. **W3-R1, binding-preserving revert** (replay of builder entry 1) -
   `Object.entries(toolbar.panels).forEach(([panelId, panel]) => {` ->
   `Object.entries(toolbar.panels).map(([panelId, panel]) => {`.
2. **W3-R2, whole-form revert** (replay of builder entry 2) - the same anchor ->
   `Object.entries(data.debugToolbar.panels).map(([id, panel]) => {`.
3. **W3-R3, scrub deleted** (replay of builder entry 3) - `      delete data.debugToolbar;\n` -> nothing. This is the DRY item's measurement.
4. **W3-R4, NEW - the re-needled row's strict independence.** A value-returning
   `.panels).map(` inserted **above** the loop while the port's `forEach` and
   binding both stay: `const _x = Object.values(toolbar.panels).map(function (p) { return p; });`
   prepended to the anchor line. The builder proved "2 rows where 1 fell
   before". This proves the stronger thing the dispatch actually asks for - that
   `no-upstream-value-returning-panel-map` produces a failing node id **no other
   row in the table produces**, which is what "can fail alone" means. Nothing in
   this cycle has run it.

Scope for all four, as the builder recorded it:
`tests/middleware/test_debug_toolbar.py examples/fakeshop/test_query/test_debug_toolbar_api.py -n0`.
Pre-mutation baseline, run by me before any mutation: **86 passed**, exit 0, 0
collection errors.

### The four proofs, run

Manifest `docs/builder/temp-tests/042/proofs-042-worker3-review-i3-i4.json`,
report `docs/builder/temp-tests/042/proofs-report-042-worker3-review-i3-i4.md`
(both new, distinctly named, `042` kept; no existing manifest, report or probe
script was overwritten). Anchors validated first with `--check-anchors-only`
(4/4 matched exactly once), scratch root outside the repository, one mutation
live at a time, a pre-mutation baseline for every entry, every restore proved by
`filecmp.cmp(shallow=False)` plus SHA-256. The asset's digest after all four is
`92cd040294ad2dba26158c652f92b9760cd35b64b91f848822a1fa093e17fa00`, the value it
carried before I started; no `ACTIVE-MUTATION.json` remains (`pristine/` is the
only thing in the scratch root). Re-run of the scope after the last restore:
**86 passed**, exit 0, 0 collection errors.

| Entry | Rows | Node ids | Builder's record | Verdict |
| --- | --- | --- | --- | --- |
| W3-R1 binding-preserving revert | **2** | `[panel-loop-is-foreach]`, `[no-upstream-value-returning-panel-map]` | entry 1, same two | **set-identical** |
| W3-R2 whole-form revert | **7** | `[scrub-before-panel-loop]`, `[panel-loop-is-foreach]`, `[no-upstream-value-returning-panel-map]`, `[no-upstream-raw-panel-key-binding]`, `[payload-shape-guard-before-panel-loop]`, `[panel-record-guard-first-in-loop]`, `[no-post-scrub-read-of-panels]` | entry 2, same seven | **set-identical** |
| W3-R3 scrub deleted | **10** | the ten `scrub-*` / `*-scrub` / `entry-guard-*` ids | entry 3, and the prior pass's record, same ten | **set-identical across three independent runs** |
| W3-R4 **new** | **1** | `[no-upstream-value-returning-panel-map]` | not run by any pass | see below |

**The 1 -> 2 transition is real and the set difference is exactly the re-needled
row.** The prior pass's supplementary record
(`proofs-report-worker3-pass3-supplementary.md`, entry 2) measured this same
mutation at this same scope at **one** row, `[panel-loop-is-foreach]`. W3-R1
measures two. `{panel-loop-is-foreach, no-upstream-value-returning-panel-map} \
{panel-loop-is-foreach} = {no-upstream-value-returning-panel-map}`. Nothing else
moved.

**W3-R4 is the measurement this cycle had not taken, and it is the one that
actually settles I4.** "Two rows where one fell before" shows the row now fires
on *that* mutation; it does not show the row can produce a failing node id **no
other row produces**, which is what the existence challenge asked. So I
constructed the mutation only this row can see — a value-returning
`Object.values(toolbar.panels).map(...)` inserted **above** the loop while the
port's `forEach` and its `panelId` binding both stay — and it fails
`[no-upstream-value-returning-panel-map]` **alone**. The row is independent
outright, not merely less subsumed.

`prove_failability.py` labels W3-R4 "WEAKLY PINNED - revision-needed" because
its arithmetic is written for boundary proofs, where one row means one
assertion holds a guard. W3-R4 is not a boundary proof: it is a **row-isolation**
proof, where exactly one failing row is the result being sought and any second
row would have falsified it. Recorded explicitly so the tool's verdict line is
not read as a finding — `BUILD.md` `### Acceptance rule` governs boundaries, and
this pass introduces none.

### Independent re-derivation of the two probe claims

Both re-derived from the source with my own `ast` probe
(`w3_probe_042_needles.py` / `_eval.py` / `_subsume.py` / `_mutations.py`, in the
session scratchpad outside the repository), resolving each row's predicate
arguments through the module's constants — never by reading the builder's
probe or its output.

- **57 rows, 57 unique ids, 0 duplicate ids.** Predicate census: 33 `_present`,
  9 `_ordered`, 8 `_absent`, 2 `_return_count_between`, 2 `_defined_once`, 1
  each of `_adjacent`, `_own_statement_line`, `_unnested_within`.
- **All 57 evaluate True against the live asset**, which is the check that
  closes the dispatch's "a constant that renders one character differently"
  hazard completely: **every one of the ten rows the DRY item touched is a
  positive-direction predicate**, so any mis-rendering of `_SCRUB` —
  shorter, longer, or a character out — makes that row evaluate **False** and
  the suite red. There is no spelling of the constant that weakens a row
  silently. Resolved values, printed rather than assumed:
  `_SCRUB = 'delete data.debugToolbar'`, `_SCRUB_STATEMENT =
  'delete data.debugToolbar;'`, the 5 + 5 split the report claims.
- **Inertness, occurrences in both files, all eight absence needles:** each is
  **1** upstream and **0** in the port, the new `` `.panels).map(` `` included.
  None is inert. (`Object.entries(toolbar.panels).map(` measured **0** upstream
  here too, so rejecting it was right.)
- **Pairwise containment across all 57 rows and all 74 needle arguments**, not
  the 8 absence needles: **38** containment relations exist, of which
  **0 are absence-over-absence**. The one pair I4 named is gone and no new one
  was introduced.
- **Replay of every prior-recorded mutation against the current table.** All six
  entries of `proofs-worker3-pass3.json` re-evaluated in memory against the
  landed table and compared with the node-id sets
  `proofs-report-worker3-pass3.md` recorded: **6/6 set-identical** (2, 2, 2, 2,
  7, 2 rows). This is the broad instrument for "did any row's effective needle
  move": it reaches the scrub family, the `CSS.escape` family and the panel-loop
  family at once, and a needle that had shifted would surface as a set
  difference in one of them. None did.

**Conclusion on the unasked DRY change: it moved no row's effective needle.**
Three independent instruments agree — the 57/57 True evaluation, the ten-id set
identity across three runs, and the six-way replay.

### The DRY item was not unasked

The dispatch frames `_SCRUB` / `_SCRUB_STATEMENT` as an optional item the
builder took on its own initiative. Read against the cohort artifact, it is the
discharge of a **standing recommendation with a trigger condition this pass
met**: `bld-042-review-3-code_fix.md` `### DRY findings` #"Pass 2's standing
recommendation" records "collapse the two `delete data.debugToolbar` spellings
to one constant **if the file is reopened for other reasons**". I3 and I4
reopened the file. The builder's own description — "the DRY item both prior
reviews left standing" — is accurate, and the grading follows from that rather
than from tolerance for scope creep.

The same section records the reason the *other* candidate was declined:
"hoisting a needle into a shared constant would let **one** edit silently
re-needle four rows at once". That reason does not transfer to this hoist, and
the difference is mechanical rather than a matter of judgement: the four
`CSS.escape` rows had landed in that same pass with no drift history, whereas
the scrub's **two spellings of one fact** could drift apart from each other, and
`_SCRUB_STATEMENT = f"{_SCRUB};"` is what structurally stops them. "Silently" is
also false here, per the positive-direction argument above.

### High:

None.

### Medium:

None.

### Low:

#### L1 - seven presence rows can never fail alone; rejected, with the measurement that says why

I4 retired one absence-over-absence pair. Applying the same instrument to the
whole table rather than to the 8 absence needles, **seven `_present` rows are
implied by a sibling row that pins the identical needle**, so none of them can
produce a failing node id the table does not already produce:
`scrub-key-deleted`, `null-handle-bail-present`, `panel-key-escaped-for-selector`,
`unusable-panel-key-skips-panel`, `nav-lookup-scoped-to-handle`,
`payload-shape-guard-present`, `panel-record-guard-present` — each subsumed by an
`_ordered` / `_adjacent` / `_own_statement_line` / `_unnested_within` /
`_return_count_between` row carrying the same string.

**Rejected as a finding, and the reason is not symmetry with I4 but its
absence.** I4's pair coupled rows pinning **two different divergences** — a
value-returning loop and a raw key binding — so the table advertised two
independent guards and held one, and the fix (a narrower needle) restored the
second guard. These seven are each subsumed by a row pinning **the same needle,
more strictly**: the anchor row states the invariant, the positional row states
the invariant plus its position. Nothing is advertised that is not held, the
table's detection power is identical with or without them, and the only
available "fix" is deleting the plain statement of each invariant — which trades
readability for zero measured detection. `worker-3.md` `### The existence
challenge` asks what would break if the abstraction were deleted; here the
honest answer is "nothing measurable, and the table reads worse", so the
challenge is raised and answered against acting on it.

Recorded rather than dropped because the landed comment states the rule for
absence needles only, and a future reader who runs the containment check
table-wide will meet these seven and need to know they were measured and
dispositioned, not missed.

#### L2 - nothing stops a future absence needle being derived from `_SCRUB`, where a mis-rendering WOULD be silent

The safety argument above holds because all ten rows reading `_SCRUB` /
`_SCRUB_STATEMENT` are positive-direction. Verified: **no absence needle derives
from the constant**, and the two absence rows naming the same object —
`no-post-scrub-read-of-panels` (`data.debugToolbar.panels`) and
`no-post-scrub-read-of-request-id` (`data.debugToolbar.requestId`) — are typed
literals, correctly. But that is a property of the current table, not a rule the
file states. A future editor writing `_absent(f"{_SCRUB}.panels")` would get a
row that goes inert on any drift in the constant, with nothing red — this
cycle's own defect class, one derivation step out, and exactly the hazard the
declined `CSS.escape` hoist was declined over.

**Accepted with a recorded reason rather than re-looped:** the table's falsifier
comment already forbids the *outcome* ("a needle the borrow never spells can
never fail"), the current table contains no instance, and `BUILD.md`
`### Spawn-per-cycle dispatch` step 4 closes on a Low dispositioned with its
reason. Routed to the deferred-work catalog below as a one-clause addition
rather than a re-dispatch.

#### L3 - a symbol name wrapped across two backtick spans, unsearchable and ungated

`tests/middleware/test_debug_toolbar.py` #"rows below against the literal,
``test_install_hint_floor_matches_the_``" writes the governance test's name
across two code spans to fit the line:

```tests/middleware/test_debug_toolbar.py
# rows below against the literal, ``test_install_hint_floor_matches_the_``
# ``pyproject_dev_group_row`` against the dependency row), which is what makes
```

`grep test_install_hint_floor_matches_the_pyproject_dev_group_row` does not find
this reference, so a rename of that test strands it with nothing to catch it:
`check_citations.py` is `path::Symbol`-only and this is neither form.
`START.md` #"never wrap a `path::Symbol` across lines (shorten prose, not path)"
names the hazard; the same hazard applies to a bare symbol name, with less
gating rather than more. My own I3 sweep hit it — a line-anchored grep for the
shared clause returned 2 of the 3 sites because the middleware's copy wraps too,
and only a whitespace-normalizing sweep found all three.

**Accepted with a recorded reason:** the fix is to shorten the surrounding prose
so the name fits one line, it changes no behavior and no row, and holding the
cycle open for it is the polish-hold `BUILD.md` step 4 exists to prevent. Routed
below.

### DRY findings

- **`_SCRUB` / `_SCRUB_STATEMENT` - correct, and the existence challenge answers
  for it.** Ten readers, not one, so this is not the one-real-caller indirection
  the challenge hunts; and deleting it would not restore ten independent
  literals but re-create a pair of spellings of one fact that can drift apart,
  which is the thing pass 2 asked to be closed. `f"{_SCRUB};"` rather than a
  second literal is the shape that makes the coupling structural. `_SCRUB` is
  module-private to the test file (12 source lines mention it, all in it); no
  reader outside.
- **Needle literals still repeat elsewhere, still correctly.** `const id =
  CSS.escape(panelId);` 4x and `if (id === "") return;` 2x are untouched by this
  pass and the prior pass's reason for leaving them stands; not re-raised.
- **The three I3 sites are one phrasing, not three near-copies** — which is the
  DRY-correct outcome for a rule that must be found from any of them. Measured
  with a whitespace-normalizing sweep over every tracked file (a line-anchored
  grep undercounts, since two of the three wrap): the sweep-the-NAME clause
  occurs **3** times and only at the three dispatched sites, the `>=`-specifier
  clause **3** times at the same three, and the backtick-or-space clause 3 times
  — middleware, test file, and `docs/SPECS/spec-042-debug_toolbar-0_0_14.md`,
  which is the spec wording the code was asked to repeat.
- **No new duplication across the two files.** The middleware comment and the
  test comment are the deliberate mirror `### I7` already graded coherent; the
  docstring says the same thing in its own grammar, which is right for a
  docstring.

### Claim verification

Every claim the pass makes that a later reader would otherwise take on trust,
re-derived:

- **AST identity of the middleware, docstrings stripped: 12387 == 12387,
  identical True.** Derived myself from `git show HEAD:` into a scratch path
  outside the repo (never `git checkout`, never a stash), with the control that
  the raw sources do differ. Third independent derivation of that figure.
- **No production boundary introduced**, so no new-boundary failability entry is
  owed: the middleware diff is comment bytes (AST-identical), and the rest is a
  test file and its constants.
- **`re.findall` governance row behaves as claimed.** Ran it: `rows ==
  ['django-debug-toolbar>=7.0.0'] == [_HINT_SUBSTRING]`, and `pyproject.toml`
  carries exactly one such row under `[dependency-groups]` `dev = [`. The
  comment now describes a sweep the test does **not** perform — and both the
  comment and the docstring say so in terms ("Those are the GATED sites, not a
  census"; "this row says nothing about it"), so the gap is stated, not implied.
- **"the same regex-over-`pyproject.toml` idiom the suite's Channels and
  Strawberry governance rows use"** - verified, not accepted:
  `tests/test_ci_governance.py` #"channels\[daphne\]>=" and #"strawberry-graphql>=" are
  the two sibling rows and use the same `re.findall` over the same file.
- **The sweep instruction is the honest instrument.** Re-measured over every
  tracked file: the bare name occurs **137** times against **21** for
  `django-debug-toolbar>=`, and **34 files carry the name more often than the
  specifier** — so "sweep the name and read each hit" is not rhetoric, and no
  site publishes a count of that population. The numerals that remain
  ("three places", "three gated sites") count the **gated** trio, which
  `test_install_hint_floor_matches_the_pyproject_dev_group_row` gates by list
  equality — a checkable claim, not a census that rots.
- **Template asset untouched, as claimed.** SHA-256 read before my first
  mutation and after my last: unchanged, and equal to the value the prior pass's
  restore proof recorded.

### Fail-open shape hunting

No production expression, branch or call was added or moved (AST identity), so
the package side has no new shape. On the test side the predicate constructors
are the place a fail-open shape would hide, and all of them fail **closed**: a
missing needle makes `_ordered`, `_adjacent`, `_unnested_within` and
`_return_count_between` return `False` rather than raise, so a row a dropped
guard makes unanswerable fails under its own id instead of erroring out of the
parametrized body. Confirmed by reading each body and by W3-R3, where the scrub
is gone and all ten rows fail under their own ids with 0 collection/setup errors.

### Test staleness - swept independently, not from the diff's file list

Derived rather than read off `### Files touched`. The pass renames one thing
that anything could cite: the I4 needle. Swept tree-wide for
`` `.map(([id, panel])` ``: **1** occurrence in a standing doc
(`docs/SPECS/appx/spec-042-debug_toolbar-0_0_14-rationale.md`, the bullet the
builder routed) and the rest only in this cycle's own `bld-042-*` artifacts,
which record history and are exempt per `START.md` #"Per-cycle scratch closes
w/ cycle". `_SCRUB` / `_SCRUB_STATEMENT` are new module-private names with no
possible outside citer. `check_citations.py --check` - `OK: 992 citations
resolve`. No model field, column, `fields=` list or wire shape moved, so neither
shape `BUILD.md` `### Test staleness a focused run cannot see` names is in play.

### Static helper use

**Skipped, with reason.** `BUILD.md` `### When to run the helper during build`
fires for Worker 3 on a new `.py` file (none), a file under `optimizer/` or
`types/` (none), 30+ new logic lines under `django_strawberry_framework/` (this
pass adds **zero** — the middleware is AST-identical), or 50+ outside it (this
pass's test-file contribution is comment blocks, one needle argument, two module
constants and one comment clause, well under). Separately, `docs/shadow/` is not
in my exclusive writable list, so running it would write outside my carve-out.
The integration pass ran it on both files this cycle (`### 2.` above) and its
repeated-string-literal output is the evidence under `### DRY findings`.

### Public-surface check

`git diff HEAD -- django_strawberry_framework/__init__.py` is **0 lines**;
`__all__` and the re-export list are unchanged. The cycle added no public name:
`_SCRUB`, `_SCRUB_STATEMENT`, `_TEMPLATE_CONTRACT` and the eight predicate
constructors are module-private to the test file, and `isRecord` is IIFE-local
in the asset.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. The
spec and rationale edits in this artifact belong to the integration pass above,
not to the consolidation pass under review, and this pass wrote neither.

### Hot-path budget

Dispatch declares hot-path `none`, and the declaration holds on inspection
rather than on the report's say-so: AST identity proves no production
expression, branch or call was added or moved. Nothing to verify the existence
of.

### Floor verification

Dispatch declares floor-verification scope `none`; no Django / Strawberry /
channels seam is touched. Floor facts as the report copies them from
`docs/builder/BUILD.md` `## Floor verification` — Django **5.2.16**, Python
**3.10**, strawberry-graphql **0.316.0** — check out against that section. No
venv was built; the shared `.venv` was not mutated.

### The routing to Worker 1: complete, measured rather than assumed

The dispatch asks whether the builder's routing is complete, on the ground that
I1 found the identical shape and one named site is a sample. Measured, not
argued: swept every tracked file plus the untracked rationale and the cycle's
artifacts for the falsified spellings.

- `` `.map(([id, panel])` `` — **1** standing-doc occurrence, the rationale
  bullet the builder routed as item 2. Everything else is in `bld-042-*`
  per-cycle artifacts, which correctly record history. The spec carries **0**.
- "exactly one pair is subsumed" — **1** standing-doc occurrence, the same
  bullet. Same disposition.
- The other routed bullet's falsified half is its count ("a partial revert that
  now fails one presence row"), now two, and the builder's replacement text
  drops that clause.
- Swept the rationale and spec independently for every other present-tense
  description this pass could falsify — the three-places comment's old
  "place 1 / place 2 / place 3" wording, "No other Python behavior differs",
  "two narrow", the ten typed scrub copies, the table's falsifier list. Every
  hit is already in a past-tense change record (rationale `### F7`,
  `**Change record — the three-places rule names the gated trio**`) or describes
  something this pass did not touch.

**The routing population is two sites and both are routed.** The recommended
replacement texts are answer-shaped and correct against the tree as of this
pass, including the "fails two under this one" figure, which W3-R1 independently
measures.

### What looks solid

- **I4 is closed at a higher standard than it was dispatched at.** The
  re-needled row is not merely less subsumed, it fails strictly alone (W3-R4),
  and its sibling `no-upstream-raw-panel-key-binding` also fails alone (the
  pass-3 `CSS.escape` entry, replayed set-identically). Both halves of the
  divergence pair are now independently failable, which is what the absence-row
  contract promised all along.
- **The needle was chosen by measurement.** `` `.panels).map(` `` at 1 upstream
  and 0 in the port; the rejected alternative at 0 upstream and therefore inert.
  Re-measured here, both figures hold.
- **The rule went into the table's own comment**, next to where the next editor
  writes a row, stated by mechanism and with no numeral over a list the reader
  is editing. That is the correct home, and the no-numeral choice is the lesson
  this cycle paid for twice.
- **The row id is unchanged**, so all 32 node ids the three prior proof records
  cite still resolve — which my six-way replay depends on and confirms.
- **The I3 fix enumerated its three sites before editing any**, and all three
  landed. The partial-claim-fix shape the finding names does not recur.
- **The comment/test divergence is stated rather than hidden.** The comment
  describes a sweep the governance row does not perform, and says so in both
  the comment and the docstring.

### Temp test verification

No temp test files written. Verification was five `ast`-based probes in the
session scratchpad **outside** the repository
(`w3_probe_042_needles.py`, `_eval.py`, `_subsume.py`, `_mutations.py`, plus the
prior-mutation replay) and the four-entry failability manifest and report under
`docs/builder/temp-tests/042/`, both new and distinctly named. Disposition: the
probes stay in the scratchpad and close with the cycle; the manifest and report
are the durable record of the re-run. Nothing existing under `temp-tests/042/`
was overwritten (`ls` before and after: the 20 prior files are intact, my 2 are
additions).

### Notes for Worker 1 (spec reconciliation)

The builder's two rationale items stand as written; I verified both are
falsified by the tree and that their replacement texts are correct, and I add
nothing to them. Three items for the final gate's `### Deferred work catalog`,
none of them blocking:

1. **L3, one line of prose.** `tests/middleware/test_debug_toolbar.py`
   #"``test_install_hint_floor_matches_the_``" splits a symbol name across two
   backtick spans, making it ungreppable and ungated. Fix is to shorten the
   surrounding clause so the name sits on one line.
2. **L2, one clause.** The table's falsifier comment forbids an inert absence
   needle but does not say that an absence needle must be a **typed literal**,
   never derived from `_SCRUB` / `_SCRUB_STATEMENT` — the one derivation under
   which a drifting constant would be silent instead of red.
3. **L1, recorded not actioned.** Seven `_present` rows cannot fail alone; the
   measurement and the reason for leaving them are in `### Low:` above, so a
   later pass running the containment check table-wide does not re-open a
   question this pass already answered.

`### I6`'s catalog correction (the third `utils/imports.py::require_optional_module`
citation in `docs/SPECS/spec-041-channels_router-0_0_14.md`) is unaffected by
this pass and still owed to the catalog.

### Review outcome

`review-accepted`.

**The evidence that would have caught a defect had one been there**, stated so
the acceptance is auditable rather than asserted:

- If the `_SCRUB` constant had rendered even one character differently from the
  ten literals it replaced, the 57/57-True evaluation would have shown it, since
  every row reading the constant is positive-direction; the ten-id set identity
  across three independent runs would have shown it; and the six-way replay of
  the prior pass's mutations would have shown it as a set difference. Three
  instruments, each able to fail independently.
- If the re-needle had traded one subsumption for another, the all-57 pairwise
  containment check would have found it. It found 38 containment relations and
  **0** absence-over-absence — and, running the same instrument past the
  dispatch's brief, it found the seven presence rows the absence-only check
  cannot see, which is the check actually being complete rather than passing.
- If the new needle had been inert, the occurrence count in **both** files would
  have shown 0 upstream. It shows 1 and 0.
- If the re-needled row were still unable to fail alone, W3-R4 would have failed
  2 rows or 0. It failed exactly 1, and that 1 was the row.
- If a mutation had been left live, the anchor check would have aborted the
  entry, and the digest read before my first mutation would not have matched the
  prior pass's recorded value. Both passed.
- If the builder's routing had been a sample rather than a population, the
  tree-wide sweep for the falsified spellings would have returned a standing-doc
  site it did not route. It returned exactly the sites it routed.

The one Medium-shaped risk the dispatch flagged — a consolidation pass quietly
changing what the table measures — is measured and did not happen. The three
Lows are dispositioned with reasons, per `BUILD.md` `### Spawn-per-cycle
dispatch` step 4.

---

## Final verification (Worker 1)

The integration pass's own close, after the consolidation loop
`BUILD.md` `## Cross-slice integration pass` prescribes ("Repeat until clean")
and `worker-0.md` `## Integration and final gate dispatch` step 2 routes back
here. Everything below is graded against the **diff and the tree**, never
against the build report or the review that describes them.

Files written by this pass, its complete and exclusive write set:

- `docs/builder/bld-042-integration.md` (this section; the `Status:` line)
- `docs/SPECS/spec-042-debug_toolbar-0_0_14.md`
- `docs/SPECS/appx/spec-042-debug_toolbar-0_0_14-rationale.md`
- `docs/builder/worker-memory/042-worker-1.md`

No source, no tests. `docs/GLOSSARY.md`, `docs/README.md`, `README.md`,
`docs/TREE.md`, `KANBAN.md` / `KANBAN.html`, `TODAY.md`, `CHANGELOG.md`,
`examples/fakeshop/db.sqlite3`, every agentflow doc, the build plan, the three
closed cohort artifacts and everything under `docs/builder/temp-tests/042/` were
read and not written. The concurrent session's paths were never edited or
reverted, and nothing was stashed, checked out or restored (`AGENTS.md` rule 34).

Declarations as dispatched: **hot-path `none`** — confirmed on inspection rather
than on the report's say-so, the middleware being AST-identical to HEAD with
docstrings stripped. **Floor-verification scope `none`** — no Django /
Strawberry / channels seam is touched. Floor facts, copied from
`docs/builder/BUILD.md` `## Floor verification` and not from memory: Django
**5.2.16** on Python **3.10** with strawberry-graphql **0.316.0**. No venv was
built; the shared `.venv` was not mutated.

### I3 and I4, audited against the diff

**I3 — closed.** All three code sites carry the instruction, read out of
`git diff HEAD` rather than out of `### Files touched`:

| Site | In the diff |
| --- | --- |
| `django_strawberry_framework/middleware/debug_toolbar.py` #"a floor bump sweeps the tree for the package" | yes — the `_DEBUG_TOOLBAR_INSTALL_HINT` comment block, replacing the "place 1 / place 2 / place 3" enumeration |
| `tests/middleware/test_debug_toolbar.py` #"sweeps the tree for the package NAME and reads each hit" | yes — the `_HINT_SUBSTRING` comment block |
| `tests/middleware/test_debug_toolbar.py::test_install_hint_floor_matches_the_pyproject_dev_group_row` | yes — its docstring's closing paragraph |

The contract the finding stated was *state the sweep's instrument honestly*, and
all three say the same thing: sweep the package **name** and read each hit; the
`>=` specifier is the narrower form, and a restatement separating the name from
the constraint with a backtick or a space does not match it. **No site publishes
a count of any population**, which was the half of M4's defect the fix had
reproduced. The numerals that survive count the **gated** trio, which
`::test_install_hint_floor_matches_the_pyproject_dev_group_row` gates by list
equality — a claim a reader can check, not a census that rots. The governance
row's own `re.findall` is untouched, correctly: there the specifier spelling is
fixed by TOML and the regex is the gate rather than the sweep.

The partial-fix shape the finding names does not recur, and that is measured
rather than asserted. Swept over a stated corpus — every tracked file, every
untracked non-ignored file, plus the untracked rationale, **744 files** — with
whitespace normalized before matching, because two of the three sites wrap the
shared clause across a line and a line-anchored grep finds two of three (the
failure Worker 3 recorded, reproduced here before being relied on): the
sweep-the-NAME clause occurs at exactly the three code sites plus the spec
wording they repeat, and nowhere else.

**I4 — closed, and re-derived rather than read.** My own `ast` probe resolves
every row's predicate arguments through the module's constants and evaluates
them against the live asset; it was written without reading the builder's probe
or Worker 3's:

- **57 rows, 57 unique ids, 0 duplicates.** Predicate census: 33 `_present`,
  9 `_ordered`, 8 `_absent`, 2 `_return_count_between`, 2 `_defined_once`, and
  one each of `_adjacent`, `_own_statement_line`, `_unnested_within`.
- **All 57 evaluate True against the shipped asset**, which is what makes the
  `_SCRUB` collapse safe to accept: every row reading the constant is
  positive-direction, so no spelling of it can weaken a row silently. Resolved
  values printed rather than assumed — `_SCRUB = 'delete data.debugToolbar'`,
  `_SCRUB_STATEMENT = 'delete data.debugToolbar;'`.
- **Inertness, both assets, all eight absence needles: 1 upstream and 0 in the
  port, the new `` `.panels).map(` `` included.** None is inert.
- **Pairwise containment across all 57 rows and all 72 string needles: 38
  containment relations, 0 of them absence-over-absence.** The pair I4 named is
  gone and none was introduced. (Worker 3 states 74 needle *arguments*; the two
  extra are `_return_count_between`'s integer counts, not needles. Not a defect
  — recorded because a published figure whose subject is unstated is how this
  cycle has been wrong before.)

Worker 3's W3-R4 is the measurement that actually settles the existence
challenge, and I accept it as run: a value-returning `.panels).map(` inserted
above an otherwise intact port loop fails
`[no-upstream-value-returning-panel-map]` **alone**, which is independent reach
proved outright rather than by set arithmetic. `prove_failability.py` labels that
entry `WEAKLY PINNED - revision-needed`; that verdict line is **not** a finding
and does not block acceptance. `BUILD.md` `### Acceptance rule: weakly pinned is
revision-needed` governs **new boundaries**, and this pass introduced none — the
middleware is AST-identical, the rest is a test file. W3-R4 is a row-isolation
proof, where exactly one failing row is the result being sought and a second row
would have falsified it. Saying so here is deliberate: the tool's own line is the
thing a later reader is most likely to mistake for an open rejection.

Restore evidence audited rather than accepted: the asset's SHA-256 read now is
`92cd040294ad2dba26158c652f92b9760cd35b64b91f848822a1fa093e17fa00`, the value
both proof records cite; no `ACTIVE-MUTATION.json` exists anywhere in the tree;
`docs/builder/temp-tests/042/` holds the 20 prior files plus the two new,
distinctly-named `042` additions, nothing overwritten.

### I1 and I2, re-verified after the consolidation touched the same files

Both findings I closed in the integration pass live in files the consolidation
then wrote, so neither was taken on trust.

- **I1 holds.** `No other Python behavior differs` occurs **0** times in
  `django_strawberry_framework/middleware/debug_toolbar.py`; its docstring names
  `process_view`, `_get_payload` and `_postprocess`. The rationale's F7 entry no
  longer asserts the understatement in the present tense. The consolidation's
  middleware edit was the hint comment block, below the docstring, and did not
  disturb it.
- **I2 holds.** `Revision [0-9]` in the spec: **0**; the bare word `revision`:
  **2**, both inside the signpost the pass added, which names the
  `spec-042 Revision N` citation form. `## Round vocabulary` still carries the
  names in the companion. All five inbound citers survive the consolidation's
  512-line rewrite of the test file and both source-side ones keep their adjacent
  WHY clause: `tests/middleware/test_debug_toolbar.py` ×2 (`spec-042 Revision 5`)
  and `docs/SPECS/spec-043-test_client-0_0_14.md` ×3 (`spec-042 Revision 8`).

Also re-run at this pass rather than carried: the staged-anchor sweep
(`grep -rEn 'TODO\(spec-042|TODO-(ALPHA|BETA|STABLE)-042' .`) still returns one
hit tree-wide and it is the Slice-1 checklist box *stating the obligation*, not
an anchor; and a banned-process-provenance sweep of the three cycle files
(worker/cohort attribution, round numbering, severity labels, `as of 0.0.N`,
`previously`) returns nothing but the two anchored `spec-042 Revision 5`
citations the repo's own anchor grading does not treat as defects.

### The routed population, re-derived — and the dispatch's own count corrected

`BUILD.md` `## Claims are proven mechanically` puts this on me, and it paid
again. The dispatch states the falsified `` `.map(([id, panel])` `` spelling
"occurs at exactly two standing-doc sites, both routed". **The spelling occurs
at one.** Measured over the 744-file corpus above, whitespace normalized:

| Spelling | Standing docs | Per-cycle artifacts |
| --- | --- | --- |
| `.map(([id, panel])` | **1** — the rationale's subsumption bullet | 27 |
| `exactly one pair is subsumed` | **1** — the same bullet | 2 |
| `now fails one presence row` | **1** — the *other* bullet | 1 |

Two **bullets** were routed, in one file, and their falsified content is not the
same spelling: one carries the needle literal and the subsumption claim, the
other carries a present-tense description and a now-wrong row count. Both were
routed correctly and both are corrected below, so the work is unchanged — but
"two sites of that spelling" is the fifth named citation in this cycle to name
the wrong site, and a sweeper who trusted it would have looked for a second
occurrence that does not exist, then either invented one or concluded the
population had already been fixed. The count of corrections was right; the
characterisation of the population was not.

After the corrections: the literal survives **once** in a standing doc, inside a
past-tense change record that names what left — which is what a change record is
for — and `exactly one pair is subsumed` and `now fails one presence row` are
**0** in standing docs. The remaining hits are `bld-042-*` per-cycle artifacts,
which record history and close with the cycle (`START.md` #"Per-cycle scratch
closes w/ cycle").

### The three Lows, decided

**L6-1 / `### Low:` L1 — seven `_present` rows can never fail alone. Closed,
finding rejected, and I agree with the reason.** Re-derived independently before
agreeing: exactly **seven** presence rows carry a needle that is also an
argument of a stricter sibling — `scrub-key-deleted`,
`null-handle-bail-present`, `panel-key-escaped-for-selector`,
`unusable-panel-key-skips-panel`, `nav-lookup-scoped-to-handle`,
`payload-shape-guard-present`, `panel-record-guard-present` — each implied by an
`_ordered` / `_adjacent` / `_own_statement_line` / `_unnested_within` /
`_return_count_between` row over the same string, and the implication is strict
(those predicates return `False` on a missing needle rather than raising, so the
presence row cannot fail without its sibling failing too).

The distinction from I4 is the one that decides it, and it is mechanical rather
than aesthetic. I4's pair coupled rows pinning **two different divergences** — a
value-returning loop and a raw key binding — so the table advertised two
independent guards and held one; the fix restored the second guard. These seven
are each subsumed by a row pinning **the same needle, more strictly**: the plain
row states the invariant, the positional row states the invariant *and* its
position. Nothing is advertised that is not held, detection power is identical
with or without them, and the only available "fix" is deleting the plain
statement of each invariant — readability traded for zero measured detection.
Closed with that reason recorded, per `BUILD.md` `### Spawn-per-cycle dispatch`
step 4.

**L6-2 / `### Low:` L2 — a future absence needle derived from `_SCRUB`. Closed
here, by writing the clause into the spec.** The hazard is real and is the one
shape where the new constants could drift silently: every row reading `_SCRUB`
today is positive-direction, so a drifted constant turns those rows red, but
`_absent(f"{_SCRUB}.panels")` would go **inert** on the same drift with nothing
to show for it — this cycle's own defect class, one derivation step out.

Where the clause belongs is a contract question, so it is mine and it went into
`## Test plan` Test 16 (spec edit 1 below). Two reasons beyond ownership. First,
the spec was **behind the code**: the table's own comment already forbids a
subsumed needle, and Test 16's falsifier list named only inertness — a
five-homes divergence in which the code states a rule the contract does not, and
the contract is the half a future table is written against. Second, the three
unfailable-absence-row shapes are one family with one falsifier each, and
splitting them across two homes is what let the second one be missed. The code
comment's mirror is the *second* copy of this rule, not its home; re-opening a
source file for one clause would cost a builder pass, a review pass and the
whole proof chain that a comment-and-needle edit moved no row — which this cycle
has now paid twice — to restate what the contract will already say. Routed to
the catalog as a mirror-sync for the next pass that opens the file, with a named
owner. **Not `revision-needed`.**

**L6-3 / `### Low:` L3 — a symbol name wrapped across two backtick spans. Closed
as a recorded Low with a named owner; no builder re-loop.** Weighed honestly
rather than waved through:

- The hazard is real and ungated. `check_citations.py` reads `path::Symbol`
  only, so nothing catches it, and `START.md` names the wrapped-citation shape
  directly.
- It is also the **weakest instance of that shape available**: the stranded
  citer and the symbol it names are in the **same file**, 176 lines apart.
  Measured tree-wide, the full name is cited nowhere else outside this cycle's
  own artifacts. A rename of that test is an edit to this file, by someone with
  the stale comment in the same buffer — the cost of the miss is one stale
  comment inside the file being renamed, not a broken cross-file citation.
- The cost of the fix is not one line of prose. `### Isolation is non-waivable`
  means a builder pass, then a review pass, on a file whose last two passes each
  owed a full failability chain to prove a comment edit moved no row; this cycle
  has already run three builder passes plus a consolidation.
- `BUILD.md` `### Spawn-per-cycle dispatch` step 4 licenses closing a finding
  intentionally rejected with a recorded reason, and this is that.

The owner is not a placeholder: the wrapped name sits **inside the
`_HINT_SUBSTRING` comment block**, which is exactly the comment a floor bump
rewrites — so catalog item 1's owner already has this text open. Recorded there
rather than left to "whoever next opens the file".

### Spec changes made (Worker 1 only)

Census before writing and re-measured after, occurrences rather than matching
lines, fixed-string rather than regex — one regex in this pass returned `0` on a
mismatched-paren error that reads exactly like a clean result, which is the
instrument class this cycle keeps meeting. Value-bearing
`django-debug-toolbar>=7.0.0` in the spec **7 → 7** (no floor value added, moved
or removed); `seven` **3 → 3**, the same three sites; `Revision [0-9]` in the
spec **0 → 0**. Byte counts across this pass: spec 162,175 → 162,777; rationale
69,443 → 69,959. No source, no tests.

Spec (`docs/SPECS/spec-042-debug_toolbar-0_0_14.md`):

1. **`## Test plan` Test 16, the falsifier sentence.** The clause
   #"or an absence row whose needle upstream does not actually carry" is
   replaced by #"or an absence row that cannot fail on its own", followed by the
   three shapes that make one unfailable and the instrument that catches each:
   a needle the borrow never spells (counted in both assets, occurrences rather
   than matching lines); a needle **containing another absence row's needle**
   (pairwise containment across the table's own needles); and a needle **derived
   from a shared constant** rather than typed literally, which goes silently
   inert on a drift where a presence row over the same constant goes red.
   *Reason:* the contract named one of the three. The second was measured by
   this cycle and landed only in the test file's own comment, leaving the code
   stating a rule the contract did not; the third has no instance today and no
   rule against it, and is the one shape in which the `_SCRUB` collapse could be
   undone silently. Stated as answers, with no count of anything.
   *Triggers:* I4, and Worker 3's `### Low:` L2 (**L6-2**), decided above.

Rationale (`docs/SPECS/appx/spec-042-debug_toolbar-0_0_14-rationale.md`), both
edits routed by the builder under `### Notes for Worker 1 (spec reconciliation)`
and both verified falsified against the tree before being applied:

1. **`### Borrowing posture — the template port`, the bullet opening "A rename
   in the guarded file can narrow an absence needle's reach without making it
   inert".** The generalized lesson is kept verbatim — it is the landed rule —
   and the instance goes to the past tense: the row #"was needled on that loop's
   whole head, binding included", a rename of the port's key variable narrowed
   it to the verbatim paste alone, and #"It now carries the fragment that names
   only the divergence, and that same partial revert fails it again".
   *Reason:* the bullet described the row in the present tense and carried the
   count "now fails one presence row", both false against the tree after the
   consolidation. *Trigger:* the builder's routed item 1; the count re-measured
   by Worker 3's W3-R1 at two rows.
2. **Same section, the bullet opening "An absence needle that contains another
   absence needle in the same table can never fail alone".** The rule stays; the
   instance becomes a discharged record naming what left (#"was needled on
   `` `.map(([id, panel])` ``"), and the measurement replaces the claim
   #"exactly one pair is subsumed": the row now carries `` `.panels).map(` `` —
   one occurrence upstream, none in the port — no absence needle in the table
   contains another, the partial revert that failed one row under the old needle
   fails two under this one, and a value-returning call on the panels map above
   an otherwise intact port loop fails that row alone. It closes by naming the
   table's own comment as where the rule is stated for the next editor.
   *Reason:* an entry in the present tense that the consolidation falsified —
   I1's exact shape, in the file I1 was found in, which is why it was routed
   rather than left. *Trigger:* the builder's routed item 2; the figures from
   W3-R1 and W3-R4 and from my own containment re-derivation.

The spec needed nothing from the consolidation beyond edit 1: its three I3 sites
are what the code now repeats, and it states no needle.

### Gates

Every command re-run at this pass; nothing carried from the pass above.

| Gate | Command | Result |
| --- | --- | --- |
| Spec glossary | `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-042-debug_toolbar-0_0_14.md` | `OK: 24 terms - all have glossary entries and at least one spec link.` exit 0 |
| Citations | `uv run python scripts/check_citations.py --check` | `OK: 992 citations resolve (823 in 441 .py files, 169 in KANBAN.md).` exit 0 — reads `.py` + `KANBAN.md` only, so it says nothing about either file this pass wrote |
| Whitespace | `git diff --check` (whole tree) | exit 0 |
| Format | `uv run ruff format --check .` | `444 files already formatted` |
| Lint | `uv run ruff check .` | `All checks passed!` (never `--fix`) |
| Source layout | `uv run python scripts/check_trailing_commas.py --check <the spec, the rationale, this artifact>` | exit 0 — explicit paths only, its default being a repo-wide auto-fix over the concurrent session's files |
| Focused suite | `uv run pytest tests/middleware/test_debug_toolbar.py examples/fakeshop/test_query/test_debug_toolbar_api.py -n0 --no-cov` | **86 passed**, exit 0, 0 collection errors. No `--cov*` flag; no full sweep — that is the final gate's, and the maintainer did not ask for one here |
| Link convention + rule-27 forms | own verifier over both files | spec 73 defs / 73 used, rationale 26 / 26; 0 undefined refs, 0 orphan defs, 0 broken in-page anchors (104 + 22 checked), 0 missing def targets, 0 `path:NN` |

**The verifier's positive control failed as a control first, and that is recorded
rather than tidied.** Appending an invented `[no-such-ref]` and
`#no-such-heading` to a scratch copy reported neither, because the append landed
*after* the `<!-- LINK DEFINITIONS -->` marker the verifier partitions on — so
the injected text was never in the body the verifier reads. A control that
cannot fail is a passing proof (`START.md` `## Instruments that lie`). Re-run
with the injection placed **before** the marker: both were reported, and the
real files' green is believed on that basis. Third time in this cycle my own
verifier has been the thing at fault and the file right.

### Final status

`final-accepted`.

Both dispatched findings are closed against the diff. I3's three code sites carry
one instruction whose instrument can see the population it names, verified by a
whitespace-normalizing sweep over a stated corpus rather than by a line-anchored
grep. I4's row is re-needled to a fragment that is neither inert nor subsumed,
verified by my own re-derivation of all 57 rows — 0 absence-over-absence
containment pairs, 8 of 8 absence needles occurring once upstream and never in
the port, all 57 predicates True against the shipped asset — and by Worker 3's
W3-R4, which proves independent reach outright. The unasked DRY collapse moved no
needle and no node id, by three instruments that could each have failed alone.
I1 and I2 still hold after the consolidation rewrote 512 lines of the file they
live beside. The two routed rationale corrections are applied, over a
re-derived population that corrected the dispatch's own description of it. The
three Lows are decided: one rejected with its measurement, one discharged into
the spec's contract, one closed as a recorded Low with an owner who already has
that text open. No source and no tests were written by this pass; every gate is
green.

**Worker 0 may mark the integration checkbox and dispatch the final gate.** No
builder re-loop is required and none is recommended.

### Deferred work catalog — the merged set, ready for the final gate

`docs/builder/bld-042-final.md` consumes **this** list, not Cohort C's, which it
supersedes: the 11 items assembled in `bld-042-review-3-code_fix.md`
`### Deferred work catalog` with four corrected and one discharged, plus four
added by the integration pass and the consolidation's review. Enumerated over the
source's own numbering (`START.md` #"Harvesting items from a doc about to be
deleted") so the final gate copies one file, and 1-11 keep their source numbers
so a reader arriving from Cohort C's artifact lands on the same item. Each bullet
carries **the source artifact section**, **the spec line licensing the deferral
or `none`**, **a one-line description**, and **a named owner**
(`START.md` #"Item routed forward w/o NAMED owner dies" — `AGENTS.md` carries no such
phrase, and both the dispatch and Cohort C's catalog name the wrong file for it).

Items needing a **KANBAN card the maintainer must place** — the board write set
is fenced out of this cycle, so no worker can home them: **2, 3, 4** (3 and 4
share one card), and **1 / 12 / 14 / 15** jointly, which name "the card that next
raises the `[dependency-groups].dev` specifier" and no such card exists yet.
Items 6, 7, 8, 10 have live owners already. Items 9, 11, 13, 16 need no card —
they are recorded as decided or discharged.

1. **The floor's ungated restatements, and an instrument that can see them.**
   *Source:* Cohort C `### Deferred work catalog` item 1, **corrected** by
   `### 3.` and `### Carried forward` item 1 above. *Spec licence:*
   `## Risks and open questions`, the "single-valued across its three gated
   sites, and restated elsewhere ungated" bullet. *Description:*
   `django-debug-toolbar>=7.0.0` is restated, correct today and gated by nothing,
   at `docs/GLOSSARY.md` (DB-backed — an ORM edit plus a regenerate, never a
   hand-edit), `docs/README.md`, `CHANGELOG.md` #"Soft-dependency feature
   floors", the `…-terms.csv` soft-dependency row, **and the spec's own seven
   value-bearing restatements**, which Cohort C's enumeration omitted. The
   terms.csv site is a **pair**: `import_spec_terms` loaded the same `notes` cell
   into `glossary_glossaryspecmention.notes` in `examples/fakeshop/db.sqlite3`,
   so fixing the CSV alone leaves the DB copy live. Cohort C's "24 / 25" is
   **withdrawn** — the absolute count is a function of an unstated corpus and
   moves by more than twenty depending on whether `__pycache__`, the tracked DB
   and `temp-tests/` are read; the reproducible half is the delta, that the loose
   needle finds exactly one restatement the tight one misses (`CHANGELOG.md:61`).
   The sweep a bump owes is over the package **NAME** with each hit read. Carry
   the census failure with the item: a `grep -v` content filter used as a path
   filter deletes exactly the rows whose text mentions the excluded path, which
   is how the terms.csv dropped silently out of a sweep that looked complete.
   *Owner:* the card that next raises the `[dependency-groups].dev` specifier —
   **needs a KANBAN card; the maintainer places it.**
2. **`docs/GLOSSARY.md`'s Debug-toolbar middleware entry is a measured stale
   carrier.** *Source:* Cohort C item 2; unchanged. *Spec licence:* none — the
   entry is outside the spec's contract surface. *Description:* its body says
   "Two deliberate robustness divergences" and enumerates two where the module
   now names three, and it restates the floor besides. DB-backed and fenced out
   of this cycle: an ORM edit plus a regenerate. *Owner:* **needs a KANBAN
   card**; recommended carrier is the Slice-2 glossary status flip the spec
   already defers to the joint cut.
3. **The DRF twin is the package's last false-population comment.** *Source:*
   Cohort C item 3; unchanged. *Spec licence:* none — different spec (spec-039).
   *Description:* `django_strawberry_framework/rest_framework/__init__.py`
   #"three-places-that-must-agree" and `tests/rest_framework/test_soft_dependency.py`
   #"three-places-that-must-agree" name three places for
   `djangorestframework>=3.17.0`, and no `tests/test_ci_governance.py` row gates
   the `pyproject.toml` side. Same defect class as M4. *Owner:* **needs a KANBAN
   card** with that write set.
4. **The `DEBUG_TOOLBAR_FLOOR` refinement, trigger fired.** *Source:* Cohort C
   item 4; unchanged. *Spec licence:* none — a refinement, not a deferred fix.
   *Description:* hoist the toolbar floor beside `CHANNELS_FLOOR` /
   `STRAWBERRY_FLOOR` in `django_strawberry_framework/utils/imports.py`,
   interpolate it into the hint, and gate it beside the two existing rows in
   `tests/test_ci_governance.py`; its stated trigger — a third
   regex-over-`pyproject.toml` governance row — fired in this cycle.
   *Owner:* **the same card as item 3** (both need `utils/imports.py` +
   `tests/test_ci_governance.py`).
5. **~~Re-needle `no-upstream-value-returning-panel-map`~~ — DISCHARGED, not
   deferred.** *Source:* Cohort C item 5, superseded by `### I4` and closed by
   the consolidation pass. *Spec licence:* n/a. *Description:* the row now
   carries `` `.panels).map(` ``; 0 absence-over-absence containment pairs
   survive, and W3-R4 shows the row failing alone. Recorded here **so the final
   gate does not carry it forward as open**, which a straight copy of Cohort C's
   list would do. *Owner:* none; closed in this cycle.
6. **The JS-runtime question**, parked for the maintainer. *Source:* Cohort C
   item 6, **with one sentence of evidence added** by `### I5`. *Spec licence:*
   `## Risks and open questions`, the "pinned by text, never by execution"
   bullet. *Description:* the asset's guards are established by reasoning against
   the language and the CSSOM rules and by no test; the absence rows detect a
   paste of upstream's text and nothing else. That last clause is now **measured
   in both assets** rather than reasoned — all eight needles occur once upstream
   and never in the port — so the risk is bounded rather than suspected.
   *Owner:* the maintainer, at close-out.
7. **Decision 1's "This spec lives at `docs/spec-…`" template sentence** in the
   archived specs. *Source:* Cohort C item 7; unchanged. *Spec licence:* none.
   *Description:* the custody cohort corrected spec-042's copy and could not
   sweep the rest; the population is a grep away and the fix is mechanical.
   *Owner:* the next `docs/SPECS/NEXT.md` Step 8 archival sweep.
8. **Package-relative citations of `utils/imports.py::require_optional_module`
   — the population is THREE, not two.** *Source:* Cohort C item 8, **corrected**
   by `### I6`. *Spec licence:* none. *Description:* two in
   `docs/SPECS/spec-042-debug_toolbar-0_0_14.md` and **one in
   `docs/SPECS/spec-041-channels_router-0_0_14.md`**, same spelling; `AGENTS.md`
   rule 27 wants the repo-relative form, and no gate reads either
   (`check_citations.py` does not read `docs/`). Fixing only the two named would
   leave the sibling live while the population read as closed. *Owner:* the same
   archival sweep as item 7.
9. **`## Implementation plan`'s "for the Worker 0 build handoff" opener.**
   *Source:* Cohort C item 9; unchanged. *Spec licence:* none. *Description:*
   pre-existing at HEAD; it names an audience rather than attributing a change,
   so it is not the process provenance `AGENTS.md` rule 27 bans. Catalogued so
   the next reader does not re-decide it. *Owner:* nobody — recorded as decided.
10. **The concurrent session has queued work in this cycle's test file.**
    *Source:* Cohort C item 10; unchanged in substance, one fact added.
    *Spec licence:* none. *Description:* its dirty
    `examples/fakeshop/test_query/README.md` backlog names
    `tests/middleware/test_debug_toolbar.py::test_get_payload_panel_title_only_when_has_content`
    for live promotion and two `Content-Length` refresh rows for deletion
    afterwards. Nothing collides today; whoever executes it now meets a file
    carrying a 57-row table, eight predicate constructors and the `_SCRUB`
    constants. *Owner:* the concurrent session's own live-promotion card.
11. **Worker 2's routed Test 16 rewording is discharged, not deferred.**
    *Source:* Cohort C item 11; unchanged. *Owner:* none; closed in Cohort C.
12. **A prior cycle's closed artifact carries a warrant this cycle falsified.**
    *Source:* `### I2` and `### Carried forward` item 4 above. *Spec licence:*
    none. *Description:* `docs/builder/DONE/build-040-auth_mutations-0_0_13.md`
    #"Deferred entries 3 and 5 were correctly NOT homed" defers the five
    `spec-042 Revision N` citations on the ground that the spec still carries the
    revision names and has no rationale companion. Both halves are now false —
    the block moved, the companion exists — while the **conclusion** stays
    correct, because Cohort A preserved the names and the spec now carries the
    signpost. Catalogued so a later reader does not re-derive the wrong
    conclusion from a dead warrant; that artifact is closed and was not edited.
    *Owner:* nobody — recorded as decided.
13. **Seven `_present` rows cannot fail alone; measured, and deliberately left.**
    *Source:* `## Review (Worker 3)` `### Low:` L1, and the independent
    re-derivation in `### The three Lows, decided` above. *Spec licence:*
    `## Test plan` Test 16, whose falsifier list is about **absence** rows — the
    clause added by this pass's spec edit 1 deliberately does not reach these.
    *Description:* each is subsumed by a sibling pinning the **same** needle more
    strictly, so nothing is advertised that is not held and the table's detection
    power is identical with or without them; the only available fix is deleting
    the plain statement of each invariant. Recorded because a later reader
    running the containment check table-wide will meet all seven and needs to
    know they were measured and dispositioned rather than missed.
    *Owner:* nobody — recorded as decided.
14. **A symbol name wrapped across two backtick spans, ungreppable and
    ungated.** *Source:* `## Review (Worker 3)` `### Low:` L3; decided above.
    *Spec licence:* none. *Description:*
    `tests/middleware/test_debug_toolbar.py` #"rows below against the literal,
    ``test_install_hint_floor_matches_the_``" splits the governance test's name
    across two code spans to fit the line, so a rename of that test strands the
    reference with nothing to catch it (`check_citations.py` is
    `path::Symbol`-only and this is neither form). The fix is to shorten the
    surrounding clause so the name sits on one line; it changes no behavior, no
    row and no node id. *Owner:* **item 1's owner — the card that next raises the
    `[dependency-groups].dev` specifier**, because the wrapped name sits inside
    the `_HINT_SUBSTRING` comment block that card rewrites. Needs the same KANBAN
    card as item 1.
15. **The table comment's falsifier list mirrors two of the contract's three
    absence-row shapes; sync it when the file is next opened.** *Source:*
    `## Review (Worker 3)` `### Low:` L2, discharged into the spec by this pass's
    spec edit 1. *Spec licence:* `## Test plan` Test 16 as amended, which now
    names all three. *Description:* `tests/middleware/test_debug_toolbar.py`
    #"An absence needle must occur in the borrow" states inertness and
    subsumption; the third shape — an absence needle
    **derived from `_SCRUB` / `_SCRUB_STATEMENT`** rather than typed literally,
    the one derivation under which a drifting constant is silent instead of red —
    is now in the contract and not yet in the mirror. No instance exists in the
    table today; this is a one-clause addition to a comment, not a fix.
    *Owner:* **item 1's / item 14's card**, whichever pass next opens
    `tests/middleware/test_debug_toolbar.py`; item 10's live-promotion card is an
    equally valid carrier and would meet the comment anyway.
16. **`prove_failability.py`'s verdict arithmetic has no row-isolation case.**
    *Source:* `## Review (Worker 3)` `### The four proofs, run`, and this pass's
    audit of it. *Spec licence:* none — a tooling observation, not spec work.
    *Description:* the tool labels a one-row result `WEAKLY PINNED -
    revision-needed` because its arithmetic is written for boundary proofs, where
    one row means one assertion holds a guard. A **row-isolation** proof — "does
    this row produce a failing id no other row produces" — seeks exactly one row,
    and a second would falsify it, so the tool's line reads as a finding against
    a proof that succeeded. Twice now a pass has had to write a paragraph
    explaining that the verdict does not apply. Catalogued as a decided
    observation, not as work: `scripts/` is outside this cycle's write set and
    the judgement may be better left to the reader than encoded.
    *Owner:* nobody — recorded as decided; raise it at close-out if the shape
    recurs.

### Concurrent-session baseline

A fresh reading, per the instruction in `## Concurrent-session baseline` above
never to compare against a number written there. `git status --short` returns
**77** paths at the close of this pass. This cycle's paths are the three
code/test files, the modified spec, and six untracked `042` files (the rationale,
the three cohort artifacts, the build plan, and this artifact); every other path
is the concurrent session's and was neither read as build output nor edited nor
reverted (`AGENTS.md` rule 34). The final gate takes its own reading.

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
