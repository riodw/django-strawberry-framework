# Build: R2 — finish the documentation (card 044, debug_extension / 0.0.14)

Spec reference: `docs/spec-044-debug_extension-0_0_14.md` (whole file audited; edits at `:3-5`, `:104-107`, `:274-279`)
Rationale reference: `docs/spec-044-debug_extension-0_0_14-rationale.md` (audited, deliberately unedited — see box 25)
Status: final-accepted

**`Status: planned` on return means "ready for review — dispatch Worker 3".** Per the build plan's
**Deviation 3**, `built` belongs to Worker 2, and every write this pass made is in a file only
Worker 1 may touch (the active spec, its rationale sibling, this artifact, Worker 1's memory). So
this item runs the Deviation-3 chain — Worker 1 (plan + perform, `planned`) → Worker 3 (audit) →
Worker 1 (final verification, `final-accepted`) — exactly as R1 did. A reader who finds a `planned`
artifact that has plainly been worked should read it as "review R2", not as "unplanned work".

---

## Plan (Worker 1)

R2's contract, from the build plan's checklist: *finish the documentation — spec opener realigned to
shipped tense, plus a full audit of the spec's `## Doc updates` and `## Definition of done` against
HEAD with any drift fixed, and the `TODO(spec-044` / `TODO-ALPHA-044` staged-anchor sweep.*

The pass performs the work as well as planning it, for the same structural reason R1 did: nearly
every fix the item needs is inside the active spec, and `worker-1.md` `## Spec custody` makes
Worker 1 its only permitted editor.

### DRY analysis

- **Helper inventory checked.** Not applicable in its usual form and stated rather than skipped: no
  package source, no test, and no helper-like logic is in this item's writable set (spec + rationale
  + this artifact + Worker 1 memory), so there is no shape for a `django_strawberry_framework/` AST
  inventory to prevent duplicating. The inventory step exists to stop a *build* writing a second
  copy of a validator; this pass writes prose. Recorded so the omission is a ruling.
- **Existing patterns reused.** Three, all doc-side. (1) The shipped-spec opener form, taken from
  `docs/SPECS/spec-042-debug_toolbar-0_0_14.md:3` and `docs/SPECS/spec-043-test_client-0_0_14.md:3`
  rather than invented. (2) R1's four-way mechanical spec-edit verification (glossary check, in-page
  anchors, ref/def symmetry, trailing-comma check) — the same scratch `link_check.py` shape R1 built,
  re-run rather than re-reasoned. (3) R1's three grep families for citations a rewrite can falsify,
  applied to each sentence this pass touched **before** cutting it.
- **New helpers justified.** None. The one scratch probe (`link_check.py`) lives outside the repo and
  is not a deliverable.
- **Duplication risk avoided.** One real risk, and it drove a ruling: the same fact — "spec-044
  shipped at `0.0.14`" — is told in the opener, the `Status:` line, the slice enumeration, the header
  GLOSSARY sentence, `## Current state`, `## Slice checklist`, `## Doc updates`, and
  `## Definition of done`. Rewriting *every* telling to shipped tense would have been the naive fix
  and is what the build plan's DRY rule warns against ("a fact told twice in two files goes stale in
  one of them"). The pass instead keeps **one** source of truth for release state — the `Status:`
  line — and rules per section whether a telling is a claim about *now* (corrected) or about *then*
  (kept). See `### The ruling that governs this pass`.

### The ruling that governs this pass

Every judgement below follows one test, applied mechanically:

> **A sentence stays as authored if its own frame marks it as pre-work or authoring-time. It is
> corrected if it reads as a claim about the repo as it stands now.**

Two supports, and they point the same way. First, `worker-1.md` `## Spec status-line
re-verification` scopes the per-spawn edit duty to the **status/header lines** — "title, target
release, status, owner, predecessors" — i.e. exactly the block that makes claims about now. Second,
the repo's own precedent for a shipped card's spec: realign the opener and `Status:` line, correct
factually-wrong Decision / test-plan / DoD prose, and leave the slice-checklist and DoD **boxes**
unticked because the `Status:` line is the source of truth for what shipped.

The precedent is not asserted — it is measured. All four archived `0.0.14`-era siblings ship with
`## Current state` preserved verbatim under the identical lead-in `A true description of the repo as
this spec is authored:`, and all four ship with **zero** ticked boxes:

| Archived sibling | `## Current state` lead-in | `- [x]` | `- [ ]` |
|---|---|---|---|
| `docs/SPECS/spec-038-form_mutations-0_0_12.md` | identical, verbatim | 0 | 5 |
| `docs/SPECS/spec-041-channels_router-0_0_14.md` | identical, verbatim | 0 | 22 |
| `docs/SPECS/spec-042-debug_toolbar-0_0_14.md` | identical, verbatim | 0 | 24 |
| `docs/SPECS/spec-043-test_client-0_0_14.md` | identical, verbatim | 0 | 24 |

So `## Current state` is a **dated snapshot preserved as history**, and the slice checklist is an
**obligation list** whose completion is recorded by the `Status:` line rather than by its boxes.
Neither is a claim about now. The header block is.

### Implementation steps

1. Re-verify the spec's header lines `:1-115` against HEAD (the per-spawn duty). Fix `:3-5`'s
   `Planned for` / `WIP-ALPHA-044-0.0.14` to the archived siblings' `Built for` / `DONE-…` shape;
   confirm `:74`'s `Status:` line.
2. Fix `:104-108`'s claim that `docs/GLOSSARY.md` carries the entry as `planned for 0.0.14`, which
   the release falsified. It sits inside the header block and is a claim about another file's
   current content.
3. Rule on `## Current state`'s four post-release-false bullets under the test above.
4. Run the staged-anchor sweep and rule on every surviving hit by owner.
5. Audit all five `## Doc updates` rows and all nine `## Definition of done` rows against HEAD.
6. Audit the rest of the spec for the same class of staleness the four named items do not cover.
7. Run the four mechanical gates; report byte counts; grep for positional citations of every
   sentence touched, before and after.

Line numbers are pin-at-write-time. Every pin below was re-measured against the file as it stands at
the end of this pass unless marked "before the edit".

### Test additions / updates

None, and this is a ruling rather than an omission. Nothing in the writable set is executable: the
diff is one markdown file. `pytest` here would report only whether the tree at large is green — a
property this item cannot affect and the final gate owns. The plan declares hot-path `none` and
floor-verification scope `none`, so no measurement and no floor run is owed. No `--cov*` flag was
used, as `BUILD.md` `## Coverage is the maintainer's gate, not a worker's tool` requires of every
pass. No `ruff` run: no `.py` file was touched.

### Implementation discretion items

None. Every choice this item presents is a ruling on whether a sentence is true, which is not
delegable.

### Dispatched findings checklist

One box per discrete obligation, including one per `## Doc updates` row and one per
`## Definition of done` row. Ticked only where the contract landed in this pass's diff or where the
audit's finding is recorded with its ruling; a box left `- [ ]` carries its deferral inline.

**The opener and the header block**

- [x] **1 — Opener at `:3-5` realigned to shipped tense.** Was ``Planned for `0.0.14` (card
      [`WIP-ALPHA-044-0.0.14`][kanban]); **this card completes the joint `0.0.14` cut and owns the
      version bump**``. Now ``Built for `0.0.14` (card [`DONE-044-0.0.14`][kanban]); **this card
      completed the joint `0.0.14` cut and owned the version bump** (see `Status:` below and
      [Decision 12](#…))``. The `Built for … (card `DONE-…`)` form and the `(see `Status:` below)`
      hand-off are both taken from the archived siblings' `:3-4`, not invented. Two deliberate
      differences from them, each with a reason: (a) 044 **owned** the cut where 042/043 rode it, so
      the follow-on clause states ownership rather than ridership; (b) the clause is past tense
      (`completed` / `owned`) because the cut is applied, where 042/043's present-tense "rides the
      joint cut" is the very sentence that went stale in those files. **Decision 12's heading was
      not touched** — 26 distinct in-page anchor targets are used 200 times in this spec and the
      Decision-12 slug is one of them, so the opener's bold clause and the heading now differ in
      tense by design.
- [x] **2 — `Status:` line at `:74` re-verified, unchanged.** It reads `**COMPLETE (card
      `DONE-044-0.0.14`) — all three slices built and the card-wrap landed; this card owned and
      applied the joint `0.0.14` version cut (the version quintet, the GLOSSARY `shipped (0.0.14)`
      status flips for `041` / `042` / `043` / `044`, and the release-status doc moves).**` Every
      clause is true at HEAD (the evidence is boxes 14-22). No edit owed; the per-spawn duty is
      discharged by verifying and recording.
- [x] **3 — Header narration at `:104-108` realigned; now `:104-107`.** Was ``[`docs/GLOSSARY.md`]
      carries [Response-extensions debug middleware] as `planned for 0.0.14`; Slice 2 updates the
      entry body to the implemented contract and Slice 3 flips the status to `shipped (0.0.14)`
      alongside the other three `0.0.14` entries.`` **Two independent falsehoods**, not one tense
      slip: `docs/GLOSSARY.md:179` reads `shipped (`0.0.14`)`, so the *quoted status is wrong*; and
      the two future-tense clauses describe work released on 2026-07-20. Now: "carries … as `shipped
      (0.0.14)`: Slice 2 rewrote the entry body to the implemented contract and Slice 3 flipped the
      status alongside the other three `0.0.14` entries." This is the item Worker 3 surfaced on R1
      and Worker 1's own R1 hand-off had not named. It is in scope because it sits **inside the
      header block** (it is the tail of the `Predecessors:` paragraph, above `## Key glossary
      references`) and is a claim about another file's current content — both halves of the governing
      test.
- [x] **4 — Post-`Status:` slice enumeration at `:75-90` ruled on: KEPT.** It narrates the three
      slices in the declarative present ("Slice 1 (**the `extensions/` subpackage …**)"). All four
      archived siblings ship the identical shape in the identical position (e.g.
      `docs/SPECS/spec-043-test_client-0_0_14.md:73-88`), and the paragraph's grammatical subject is
      the *slice's contract*, not the repo's state. Not a claim about now. Unedited.

**`## Current state`**

- [x] **5 — The four shipping-falsified `## Current state` bullets ruled on: KEPT, verbatim.** They
      are `:574` ("No `extensions/` subpackage exists"), `:576-578` (the `docs/TREE.md` `planned by
      TODO-ALPHA-044-0.0.14` reservation), `:581-585` (the `config/schema.py` "no direct Strawberry
      analogue" docstring quote), and `:663-668` ("The version line reads `0.0.13`"). Each is false
      as a present-tense claim and each is **correct as the dated snapshot the section declares
      itself to be** — the lead-in at `:565` reads `A true description of the repo as this spec is
      authored:`. Four reasons, in order of weight: (a) the four-sibling precedent table above —
      every archived `0.0.14`-era spec preserves this section verbatim, and inventing a different
      treatment for 044 alone would make the archive inconsistent exactly where a reader compares the
      four cards of one release; (b) the bullets are the **premises the Decisions argue from** —
      Decision 2's obligation to rewrite the `config/schema.py` sentence is unreadable once the
      sentence it quotes is gone, and Decision 12's ownership argument rests on the version line
      reading `0.0.13`; (c) `BUILD.md`'s rationale-move rule 2 deletes prose *a decision* falsified,
      and shipping is not a decision (R1's judgement call 5, which routed the question here rather
      than settling it); (d) the governing test — the section frames itself as "then". **No framing
      sentence was added either**, and that is the harder half of the ruling: a stronger caveat than
      the siblings' would read, to anyone comparing the four specs, as meaning something the others
      do not, which is the same inconsistency by another route.
- [x] **6 — `## Current state`'s `## Doc updates`-adjacent siblings ruled on with it: KEPT.** The
      same class appears inside obligation prose at `:492-493` ("the section currently lists only the
      `0.0.14` router"), `:457` ("that sentence is now false; reword it"), `:2508-2509` ("only the
      router is listed today, in shipped tense already"), and `:534` ("today the package has no
      in-response answer", in `## Problem statement`). Each describes the **starting condition the
      obligation acts on**, which is what makes the obligation legible; and a `## Problem statement`
      is by construction the pre-card motivation. All four kept.

**The staged-anchor sweep** (`BUILD.md` `## Cross-slice integration pass` step 6)

- [x] **7 — Sweep run, independently.** `grep -rEn 'TODO\(spec-044|TODO-(ALPHA|BETA|STABLE)-044' .`
      with `KANBAN.md` / `KANBAN.html` / `BACKLOG.md` excluded (there `TODO-<MILESTONE>-<NNN>`
      legitimately names a board card).
- [x] **8 — Zero anchors survive in package source or tests: CONFIRMED, not inherited.**
      `grep -rEn … django_strawberry_framework tests examples scripts | wc -l` → **0**. Card 044
      shipped, so that is the required result and this cycle owes no anchor removal. Additionally
      verified at the one site the spec names explicitly: `tests/extensions/__init__.py` was
      specified at `:426-428` to carry a `TODO(spec-044 Slice 1)` placement anchor, and the shipped
      file carries none — the anchor was correctly removed by the change that shipped the slice.
- [x] **9 — The five spec-internal sites ruled on: KEPT, all five.** `:427`, `:430` (`## Slice
      checklist`, Slice 1 — the sub-checks that *created* the anchors), `:452` (`## Slice checklist`,
      Slice 2 — "the rows move from `planned by TODO-ALPHA-044-0.0.14` to the real docstring-derived
      rows"), `:576`, `:578` (`## Current state`). None is a live anchor: each is prose *naming* an
      anchor, inside an obligation list or the dated snapshot, and `docs/TREE.md` at HEAD contains
      zero `TODO-ALPHA-044` occurrences, so the obligation the prose describes demonstrably
      completed. **One correction to R1's hand-off, made here rather than in its artifact**
      (`ARTIFACT.md` `## Re-pass sections` forbids editing a prior entry): R1 recorded `:453` as
      being in `## Doc updates`. It is in `## Slice checklist` — `## Doc updates` begins at `:2449`,
      and its `docs/TREE.md` row (`:2484-2489`) contains no anchor text at all. The count of five is
      right; one location label was not.
- [x] **10 — Every hit outside spec-044 classified by owner.** (a) **Historical, correct** —
      `docs/SPECS/spec-041/042/043-…md` and two archived `-terms.csv` files name
      `TODO-ALPHA-044-0.0.14` as the sibling card's id at their authoring time. Archived specs are
      the historical record; nothing owed. (b) **`docs/builder/` artifacts** — R1's and Worker 0's
      own prose about this sweep; per-cycle scratchpads. (c) **Live sibling specs, unowned** —
      `docs/spec-050-…:390` and `docs/spec-051-…:556`, already in R1's deferred catalog and
      re-confirmed here; see box 33 for two further sites in the same two files that R1's catalog
      entry does not name.

**`## Doc updates` audit — one box per row, all five against HEAD**

- [x] **11 — Row 1, `docs/GLOSSARY.md` entry body (Slice 2): LANDED.** `docs/GLOSSARY.md:1514-1526`
      carries the implemented contract, and the row's long enumeration landed **distributed across
      the focused entries the row's own vocabulary names** rather than inlined into one paragraph:
      `#per-operation-extension-isolation` carries the `strawberry-graphql>=0.316.0` floor *with its
      migration note* (the row's "release-wide migration notes"), `#graphene-debug-migration` carries
      the concrete `_debug` + `DjangoDebugMiddleware` → extension + `response.extensions.debug`
      cookbook migration, and `#djangodebugextension` (`:502`) carries the import path, class-form
      opt-in, per-operation instance, and the developer-only posture. The row's last clause — "the
      'distinct from the Debug-toolbar middleware' paragraph updated to shipped tense in **both**
      entries' cross-references" — is satisfied in both directions: `:424` (toolbar entry → this one)
      and `:1522` (this entry → toolbar). No drift; no edit.
- [x] **12 — Row 2, `docs/TREE.md` regenerated (Slice 2): LANDED.** Real docstring-derived rows at
      `docs/TREE.md:218`, `:332` (`extensions/ # Strawberry schema extensions supplied by
      django-strawberry-framework.`) and `:467`, `:679` (`extensions/ # Tests for package Strawberry
      schema extensions.`), and **zero** `TODO-ALPHA-044` occurrences anywhere in the file — so the
      `TrackedPath.is_current` flip and the re-render both happened. No drift; no edit.
- [x] **13 — Row 3, `examples/fakeshop/config/schema.py` docstring (Slice 2): LANDED.** The module
      docstring now reads "The response-side ``DjangoDebugExtension`` is opt-in and deliberately
      omitted from this aggregate schema; live coverage mounts it through a probe URLconf." The
      falsified "no direct Strawberry analogue and is left out for now" sentence is gone, and the
      replacement names both halves Decision 2 requires (the shipped symbol, fakeshop's deliberate
      opt-out). No drift; no edit.
- [x] **14 — Row 4, `GOAL.md` success criterion 7 (Slice 2): LANDED.** `GOAL.md:513` carries the
      scoping clarification, including the worked debug example ("removing `_debug` and
      `DjangoDebugMiddleware`, adding `DjangoDebugExtension` … and reading
      `response.extensions.debug`"). No drift in the row — but the *spec's own argument* for this row
      had gone stale, which is box 23.
- [x] **15 — Row 5, the Slice 3 cut: LANDED, all nine parts.** Checked one by one, not as a block.
      (1) GLOSSARY `shipped (0.0.14)` for all four surfaces + companions — `:179` (this card), and
      the companions `#channels-request-adapter` / `#require_optional_module` at `:88` / `:177`.
      (2) The GLOSSARY package-version line — `:20` `Current package version: `0.0.14``.
      (3) The `#joint-version-cut` entry's wording records the **applied** cut — `:907` "most
      recently applied at the joint `0.0.14` cut, where four cards shared the line", naming all four.
      (4) `README.md:62` — the Status section reads `**`0.0.14`, single-maintainer, alpha-quality.**`
      with `DjangoDebugExtension` (`DONE-044`) in the newest-shipped-surface paragraph.
      (5) `docs/README.md:97` — `**Shipped today** (`0.0.14`)`, and `:132` the `DjangoDebugExtension`
      bullet; **no "Coming next — remaining alpha (`0.0.14`)" block survives** (the only "coming
      next" left is the section *heading* `## Today and coming next`, which is not release wording).
      (6) `TODAY.md:387` — the `DjangoDebugExtension` bullet in shipped tense, alongside the toolbar
      and test-client additions the row required.
      (7) `CHANGELOG.md:19` — `## [0.0.14] - 2026-07-20`.
      (8) The version quintet — `pyproject.toml:4`, `django_strawberry_framework/__init__.py:41`,
      `tests/base/test_init.py:21`, the GLOSSARY line above, `uv.lock`'s package entry.
      (9) The DB-first card wrap — card `DONE-044-0.0.14` with a `SpecDoc` and 42
      `CardGlossaryTerm` rows (Worker 0's pre-flight, and `check_spec_glossary.py` independently
      reports `OK: 42 terms`). No drift; no edit.

**`## Definition of done` audit — one box per row, all nine against HEAD**

- [x] **16 — DoD row 1 (`extensions/debug.py` exists, docstrings, `on_operation` + `get_results`):
      LANDED.** `django_strawberry_framework/extensions/debug.py` (21,809 bytes) declares
      `class DjangoDebugExtension(SchemaExtension)` at `:371`, `on_operation` at `:419`,
      `get_results` at `:460`; module and class docstrings present.
- [x] **17 — DoD row 2 (the six SQL fields / exception triple wire names): LANDED.** Named in the
      GLOSSARY `#debug-sql-row` / `#debug-exception-row` entries and in the module docstring, with
      the `callproc()` omission and the nested-sync attribution boundary both recorded, as the row
      requires.
- [x] **18 — DoD row 3 (off by default; class-form opt-in): LANDED.** The extension is not wired
      into any shipped schema; `examples/fakeshop/config/schema.py`'s `DjangoSchema(...)` carries
      only `extensions=[lambda: _optimizer]`, i.e. fakeshop's documented opt-out is the DoD's
      "with the extension absent, no debug instrumentation runs" case exercised in the live tree.
- [x] **19 — DoD row 4 (subpackage import resolves; nothing added to the package root): LANDED, and
      the negative half is pinned in source.** `django_strawberry_framework/extensions/__init__.py`
      eagerly re-exports `DjangoDebugExtension` in `__all__`;
      `django_strawberry_framework/__init__.py:38` carries the standing instruction `# Do not import
      or root-export DjangoDebugExtension here: …` and the symbol appears nowhere else in that file.
- [x] **20 — DoD row 5 (no new dependency; floor raised to `strawberry-graphql>=0.316.0`; durably
      exercised): LANDED.** `pyproject.toml:35` `"strawberry-graphql>=0.316.0"`; `uv.lock:577`
      `specifier = ">=0.316.0"`; `.github/workflows/django.yml:51-73` force-installs exactly
      `0.316.0` on three matrix nodes with the comment naming the per-operation isolation reason.
      The one-time isolated-venv floor run this row also requires belongs to the shipped Slice 1's
      record, not to a residual pass; the plan declares this cycle's floor scope `none`.
- [x] **21 — DoD row 6 (split tests cover the Test plan): LANDED.**
      `examples/fakeshop/test_query/test_debug_extension_api.py` (15,876 bytes) owns the live
      probe-URLconf HTTP tier; `tests/extensions/test_debug.py` (38,962 bytes) owns
      request-impossible mechanics; `tests/extensions/__init__.py`'s docstring states the split rule
      and points at the live file by path, matching Decision 11.
- [x] **22 — DoD rows 7, 8, 9: LANDED.** Row 7 (the Slice 2 doc updates) is boxes 11-14. Row 8 (the
      joint cut) is box 15. Row 9 (`ruff` clean / no `pytest`) is a process row the shipped cycle's
      commits discharged and no residual item can re-prove; recorded as such rather than ticked on a
      re-run this pass is forbidden from doing (`AGENTS.md` rule 15 / `START.md`).
- [x] **23 — The spec's checkboxes left `- [ ]`: deliberate, and the reason is recorded.**
      *(Population corrected in pass 2 — Worker 3's Low 2. The original assertion "all nine DoD boxes
      and all 24 `## Slice checklist` boxes" was wrong twice: it mis-counted the slice checklist and
      omitted a whole section.)* Re-measured with `^\s*- \[[ x]\]`: **43 boxes, 0 ticked** — **20** in
      `## Slice checklist`, **14** in `## Helper-reuse obligations (DRY)` (D1-D6 / D-N1-D-N8), **9**
      in `## Definition of done`. **26** of the 43 are top-level, which is the figure comparable to
      the sibling table's `- [ ]` column (5 / 22 / 24 / 24) — that column is top-level-only, and
      mixing the two scopes is how the original miscount happened. The ruling is unchanged and its
      measurement held: 0 ticked boxes here and in all four archived siblings. Ticking them would put
      a second, independently-rottable record of release state in the spec — the exact duplication
      the plan's DRY rule names, and the one that did rot at `:56-73` (pass 2's Medium).

**What the four named items missed — the systematic read**

- [x] **24 — `## Goal and cookbook cross-reference` `:274-279` corrected.** Was "Because criterion 7
      **as written carves out no such case**, Slice 2 **carries** the corresponding `GOAL.md`
      clarification: …". `GOAL.md:513` now carries exactly that carve-out, so the premise is false as
      a present-tense claim. Now: "Criterion 7 carved out no such case as this spec was authored, so
      Slice 2 added the corresponding `GOAL.md` clarification **that it now carries**: …" — the
      argument survives intact, the premise is dated, and the outcome is stated. **Why this falls on
      the corrected side of the governing test while `## Current state` does not:** the phrase "as
      written" reads most naturally as *as it is currently written*, the sentence sits in a standing
      argument that the design honours `GOAL.md` (not in an obligation list and not in a dated
      section), and its section carries no dating frame anywhere. A reader who checks `GOAL.md`
      finds the spec wrong. That is the distinction, stated so the inconsistency charge can be
      answered rather than dodged.
- [x] **25 — `docs/spec-044-debug_extension-0_0_14-rationale.md`: audited, deliberately NOT
      edited.** It is in this pass's writable set, so the non-edit is a ruling. Two things were
      checked. (a) `:82` — Revision 1 reads "initial draft authored from the
      [`WIP-ALPHA-044-0.0.14`][kanban] card body". **Correct as history and kept**: the card *was*
      WIP when the draft was authored, and the rationale file's whole job is to hold the chronology.
      This is the one surviving `WIP-ALPHA-044` in either file and it is the one that should survive.
      (b) The file's only citation of the spec's header (`:78`, "Moved in full from the spec's
      header, where it stood under the line 'Revision history …'") names a line this pass did not
      touch. No edit owed; the rationale is byte-identical at **43,859**.
- [x] **26 — Positional-citation sweep over both files, before and after each edit.** R1's lesson
      applied: three grep families, all **whitespace-flattened** rather than line-oriented, since a
      citation broken across a line wrap is invisible to `grep -n`. (a) `WIP-ALPHA-044` /
      `Planned for` → the two spec sites this pass fixed plus rationale `:82` (box 25) plus
      `docs/spec-050-…:173` / `docs/spec-051-…:235` (box 33). (b) The vocabulary of each edited
      sentence — `planned for 0.0.14` (four flattened hits: the one fixed, three obligation-prose
      keeps), `criterion 7` (nine hits, each resolved to its own independent claim; none cites
      `:274` positionally). (c) `opener` / `header block` / `the first paragraph` / `the `Status:`
      line` across both files → one hit, rationale `:78`, resolved above. Nothing cites a sentence
      this pass rewrote.

**Verification**

- [x] **27 — `check_spec_glossary.py` exits 0, before and after.** `uv run python
      scripts/check_spec_glossary.py --spec docs/spec-044-debug_extension-0_0_14.md` →
      `OK: 42 terms - all have glossary entries and at least one spec link.`, exit **0**. Anchor
      exposure was checked **before** cutting text, per R1's `django-trac-37064-hardening` hazard: no
      edit removes a `](…GLOSSARY.md#…)` link or a `][glossary-…]` use, so no term could lose its
      only spec link. The `[glossary-response-extensions-debug-middleware]` use inside the rewritten
      `:104-107` sentence was deliberately preserved for exactly this reason.
- [x] **28 — In-page anchors and ref/def symmetry, both files.** Spec: 35 headings, **200 anchor
      occurrences across 26 distinct targets, 0 broken**; **102 definitions, 0 unused**, one
      "undefined" hit `"sql"` — the `res.extensions["debug"]["sql"]` code span, the standing false
      positive of the `][…]` probe every prior pass recorded. Rationale: 20 headings, 2 anchor
      occurrences, 0 broken; 28 definitions, 0 undefined, 0 unused. Every non-URL definition in both
      files resolves to a file that exists **and** to a real heading in it. All figures identical to
      R1's, which is the expected result for a prose-only pass.
- [x] **29 — `check_trailing_commas.py --check` exits 0 on explicit paths.** Explicit paths only —
      run pathless it rewrites unrelated `docs/` scratch files.
- [x] **30 — Byte counts reported.** *(Extended in pass 2 and again at final verification; each
      pass's figures are correct as of that pass and are kept.)* Spec **185,518 (R1 end) → 185,542
      (pass 1, +24) → 185,496 (pass 2, −46) → 185,485 (final verification, −11: the escalated Low's
      two-word fix)**, each re-measured with `wc -c` rather than carried. Rationale **43,859**
      throughout, byte-identical. For the cycle's arc: HEAD was 205,905 before R1.
- [x] **31 — Scope confirmed by `git status --short`.** Exactly one tracked modification
      (`docs/spec-044-debug_extension-0_0_14.md`) plus this artifact and the memory file. No package
      source, no test, no `examples/`, no `scripts/`, no `pyproject.toml` / `uv.lock` /
      `CHANGELOG.md` / `docs/GLOSSARY.md` / `docs/TREE.md` / `KANBAN.*`, no other `docs/spec-*.md`,
      no archived spec, no `bld-*.md` from the preserved spec-046 cycle. No commit, no branch, no
      `git stash` / `checkout` / `restore` / `worktree` at any point. The two baseline-dirty entries
      are the plan's declared ones and were neither edited nor reverted (`AGENTS.md` rule 34).

**Routed out, not dropped**

- [x] **32 — Non-spec drift needing Worker 2: NONE FOUND, and that is a finding.** Every one of the
      spec's five `## Doc updates` rows and nine `## Definition of done` rows landed at HEAD in
      shipped tense, so no docstring or standing-doc sentence spec-044's shipping falsified survives.
      Worker 0 does not need to dispatch Worker 2 before the review. The prose the audit *did* find
      false was all inside the active spec, i.e. inside this pass's own writable set.
- [x] **33 — Four unowned-file items recorded for the `### Deferred work catalog`.** Named, located,
      and directionally resolved so the maintainer's sweep is cheap. Details in
      `### For the ### Deferred work catalog in bld-044-final.md` below. *(Population corrected at
      final verification: the authoritative list is the **six**-item merged one under
      `### For the ### Deferred work catalog in bld-044-final.md — merged, six items` in pass 2's
      section — Worker 3 added two. The four-item list below and R1's single-item entry are both
      subsumed by it; the final gate must read the merged list, not this box's count.)*

---

## Build report (Worker 1, performing R2)

### Files touched

- `docs/spec-044-debug_extension-0_0_14.md` — three edits, all prose: the opener's tense and card id
  (`:3-5`), the header block's GLOSSARY-status claim (`:104-108` → `:104-107`), and the criterion-7
  premise in `## Goal and cookbook cross-reference` (`:274-279`). Enumerated with reasons under
  `### Spec changes made (Worker 1 only)`.
- `docs/builder/bld-044-r2-doc_completion.md` — this artifact (created).
- `docs/builder/worker-memory/worker-1.md` — memory entry appended under `## spec-044 residual
  cycle`.

`docs/spec-044-debug_extension-0_0_14-rationale.md` is in the writable set and was **deliberately not
edited** (box 25).

### Validation run

- `uv run python scripts/check_spec_glossary.py --spec docs/spec-044-debug_extension-0_0_14.md` →
  `OK: 42 terms - all have glossary entries and at least one spec link.` **exit 0**.
- `uv run python scripts/check_trailing_commas.py --check docs/spec-044-debug_extension-0_0_14.md
  docs/builder/bld-044-r2-doc_completion.md` → **exit 0**.
- In-page anchors + ref/def symmetry + cross-file anchor resolution, both files → box 28.
- `git status --short` → box 31.
- **This pass's diff isolated arithmetically from R1's**, since R1's work is uncommitted and a plain
  `git diff` against HEAD shows both. `git diff --numstat` now reads **76 insertions / 410 deletions**
  against R1's recorded **63 / 396** — a delta of **+13 / +14**, which is exactly the sum of this
  pass's three edits (3-for-3 at the opener, 4-for-5 at the header narration, 6-for-6 at
  criterion 7). No fourth hunk exists, so nothing was changed that this artifact does not record.
- No `ruff` run (no `.py` file touched); no `pytest` (nothing executable in the diff, and
  `AGENTS.md` rule 15 forbids an unrequested run).

### Failability proofs

None; this pass introduced no new boundary. The diff contains no `.py` file, no executable line, and
no guard, gate, or rejection path — `BUILD.md` `### What needs a proof, and what does not` scopes the
obligation to boundaries, so the re-run floor is arithmetically zero rather than a chosen subset.
Read for the catalogued fail-open shapes as well (clamp, `getattr` default, `or` fallback, bare
`except`, truthiness on an absent value): none can exist, there being no expression in the diff.

### Hot-path budget

Not applicable; plan declares no hot path. The build plan's declaration is `none` for the whole
cycle, on the ground that no residual item changes package source — which this pass's diff confirms.

### Floor verification

Not applicable; plan declares floor-verification scope `none`. No residual item touches a Django /
Strawberry / channels integration seam, so this pass owes no floor run and no version-dependent
reasoning.

### Implementation notes

- **Why the opener's bold clause moved to past tense while Decision 12's heading did not.** The
  heading is an anchor target used by 200 in-page references across the spec; rewording it would
  break the anchor and force a sweep of every citation, for a tense nicety. The opener is prose. So
  the two now differ in tense on purpose, and box 1 records it so a later reader does not "fix" the
  divergence by renaming the heading.
- **Why `(see `Status:` below and …)` was added rather than restating the release facts inline.** The
  `Status:` line is this pass's single source of truth for release state; the opener points at it
  instead of copying it. That is the same hand-off both archived siblings use, and it is what keeps
  the opener from becoming the second place release state can rot.
- **Why `:104-107` says "rewrote"/"flipped" rather than deleting the Slice attributions.** Naming
  which slice did which half is the spec's own record of how the GLOSSARY entry reached its current
  state, and it is checkable against the entry today. Only the tense and the quoted status were
  wrong.

### Notes for Worker 3

- **The whole pass is one ruling plus three one-sentence edits.** The review's substance is whether
  the governing test in `### The ruling that governs this pass` is the right test and whether it was
  applied consistently — particularly the `## Current state` keep (box 5) against the criterion-7
  correction (box 24), which are the two sides of the same line. Box 24 states the distinguishing
  argument explicitly so it can be attacked.
- **Two figures worth re-deriving rather than accepting.** The four-sibling precedent table (lead-in
  text identical, 0 ticked boxes in each) and the "zero anchors in source or tests" count. Both are
  one command each.
- **The scratch probe is reusable.** `link_check.py` (in-page anchors + ref/def symmetry + cross-file
  anchor resolution in one pass) lives at
  `/private/tmp/claude-501/-Users-riordenweber-projects-django-strawberry-framework/dd84b4f2-b2f3-496f-b611-703a26fa0822/scratchpad/link_check.py`,
  outside the repo. It is the same shape R1 built and R3 will need after the archive re-relativizes
  every definition path. Its slugifier maps **each** space to one hyphen and keeps `_` — a `\s+`
  collapse falsely reports every `decision-N--…` anchor missing.
- **Do not read the byte delta as a content change.** +24 bytes over three prose edits.

### Notes for Worker 1 (spec reconciliation)

Nothing carried forward for a later pass in the active spec: every falsehood this audit found inside
spec-044 was fixed in this pass. What follows is for **other files** and is deliberately not acted
on.

- **No Worker 2 dispatch is needed for R2** (box 32). Every `## Doc updates` and
  `## Definition of done` obligation landed at HEAD in shipped tense, so there is no false docstring
  or standing-doc sentence for Worker 2 to correct.
- **For R3, unchanged from R1's hand-off and re-confirmed:** both files' link blocks resolve from
  `docs/` today and must not be pre-adjusted. This pass added and removed **no** link definition, so
  R3's inventory is exactly what R1 recorded — the spec's 102 definitions (15 of them `rationale*`)
  and the rationale's 28, plus 33 cross-file `#anchor` targets between the two files, and
  `[glossary-django-trac-37064]` in both, which is what keeps `check_spec_glossary.py`'s 42nd term
  reachable.
- **For R3, one new caution.** The opener now contains the literal `DONE-044-0.0.14`. R3 repoints
  `SpecDoc.url` for card 44; it must not also "helpfully" touch the card id in the spec's opener,
  which is correct as written.
- **Observed, outside every residual item's scope, recorded so it is not lost:** `TODAY.md:384`
  attributes the router redesign to "the transport-security card `065`" while `docs/README.md:128`
  attributes it to `046`. The 2026-07-30 renumber moved that card 065 → 046, so `TODAY.md` carries
  the pre-renumber number. Nothing to do with spec-044's shipping; it belongs to the preserved
  spec-046 cycle or the renumber's own closeout.

### For the `### Deferred work catalog` in `bld-044-final.md`

Four items, all in files outside every residual item's writable set. The first re-states R1's entry;
the other three are new to this pass's systematic read.

1. **`docs/spec-050-debug_extraction-0_0_19.md:390` and `docs/spec-051-boundary_dry_squeeze-0_0_20.md:556`**
   each assert that the version-quintet sites "currently carry `TODO(spec-044 Slice 3)` anchors owned
   by the in-flight `0.0.14` cut". Re-confirmed false this pass: zero such anchors survive in source
   or tests. Both sit under `## Architectural decisions` — normative decision prose, not a dated
   snapshot — which is why they are drift rather than preserved history. R1's catalog entry stands.
2. **`docs/spec-050-…:173` and `docs/spec-051-…:235`** each read `Card `WIP-ALPHA-044-0.0.14` is
   mid-flight and owns the `0.0.14` joint cut`. Card 044 is `DONE-044-0.0.14` and the cut is applied.
   **Both sit in those specs' own `## Current state` sections**, so by this pass's governing test
   they are *legitimately* authoring-time snapshots and **not** defects — with one caveat worth the
   maintainer's eye: unlike spec-044's, neither of those sections carries the `A true description of
   the repo as this spec is authored:` lead-in, and both specs are still **in flight**, so their
   authors may want them refreshed rather than frozen. Recorded as a question, not as drift; noted
   here because a sweep that fixed item 1 while ignoring these would look arbitrary.
3. **A tree-wide card-id renumber reconciliation, not spec-044's to make.** Three dead card-id
   pointers survive in spec-044 itself — `TODO-BETA-045-0.1.0` at `:1686` and `:2641`, and
   `TODO-BETA-053-0.1.5` at `:2623` — and this pass **deliberately did not repoint them**, even
   though the spec is writable. Targets identified from the live board, with confidence stated:
   `TODO-BETA-045-0.1.0` (the alpha → beta milestone chores) is now
   **`TODO-ALPHA-052-0.1.0` — "Beta release (cleanup, verification, alpha → beta)"**, `KANBAN.md:436`
   — high confidence on subject (its DoD carries the `0.1.0` bump, the README/GLOSSARY status
   cross-check, and the parity audit), and note the **milestone prefix changed too** (BETA → ALPHA),
   so this was a re-milestoning, not only a renumber. `TODO-BETA-053-0.1.5` (the fakeshop-activation
   card) is now **`TODO-BETA-060-0.1.5` — "Fakeshop GraphQL schema activation"**, `KANBAN.md:939` —
   high confidence on identity (same version, same subject, and `053` now names `FieldSet` at
   `0.1.1`), **lower confidence that it is still the natural host** for fakeshop opting into the
   debug extension, because its planning note says per-subsystem activation belongs to the
   respective Layer-3 cards' Slice 4. Why this is not fixed here: the drift was caused by the
   2026-07-30 renumber rather than by spec-044's shipping, it is **not** in `## Doc updates` or
   `## Definition of done`, and it is tree-wide rather than local —
   `grep -rln 'TODO-BETA-053-0\.1\.5'` hits **ten files**: `TODAY.md`, spec-044, six archived specs
   (`spec-030`, `spec-032`, `spec-033`, `spec-037`, `spec-041`, `spec-042` — 26 occurrences between
   them), and **two source/test files**, `examples/fakeshop/apps/products/schema.py:228` and
   `examples/fakeshop/test_query/test_products_api.py`. Repointing spec-044's three alone would
   leave one file disagreeing with nine, which is strictly worse than an obviously-dead pointer.
   One owner, one sweep, or not at all.
4. **`docs/spec-044-…:291-297` is inexact rather than false, and was left alone on purpose.** It
   calls `strawberry.Schema(query=Query, config=strawberry_config(), extensions=[lambda:
   _optimizer])` "the canonical shape `config/schema.py` demonstrates today". At HEAD that file
   builds `DjangoSchema(query=Query, mutation=Mutation, config=strawberry_config(),
   extensions=[lambda: _optimizer])` — `DjangoSchema` being the mutation-atomicity card's shipped
   `strawberry.Schema` subclass. Three of the four cited elements are exact and the class named is a
   base of the class used, so the illustration is not wrong in substance; the two nearby recipe
   snippets (`:326`, `:892`) are **query-only consumer/cookbook examples**, for which plain
   `strawberry.Schema` remains correct. Not fixed because the divergence comes from a different
   card's shipping, and because deciding whether the cookbook recipe should now name `DjangoSchema`
   changes the spec's central migration story — a maintainer call, not a doc-completion pass's.

### Baseline / concurrent-work note

`git status --short` at the end of this pass, six entries: `M docs/feedback.md`,
`M docs/spec-044-debug_extension-0_0_14.md`, `D to-many-search-optimizer-reproduction.md`,
`?? docs/builder/bld-044-r1-rationale_move.md`, `?? docs/builder/build-044-debug_extension-0_0_14.md`,
`?? docs/spec-044-debug_extension-0_0_14-rationale.md` (this artifact is untracked scratch under
`docs/builder/` and appears once created). Unchanged in shape from the end of R1.

Two entries are not this pass's and were neither edited nor reverted (`AGENTS.md` rule 34):
`to-many-search-optimizer-reproduction.md` (the plan's declared baseline-dirty deletion) and
`docs/feedback.md` (a maintainer adversarial review of **spec-046**, the preserved cycle's
concurrent work, out of scope for every residual item).

### Spec changes made (Worker 1 only)

Three edits, each with the line range as numbered **before** the edit and a one-line reason.

- `docs/spec-044-debug_extension-0_0_14.md:3-5` — the opener realigned to shipped tense and to the
  Done card id, on the archived `0.0.14` siblings' form. Reason: the card is `DONE-044-0.0.14` and
  the version shipped 2026-07-20, so `Planned for` / `WIP-ALPHA-044-0.0.14` was false in the spec's
  most-read line. (Box 1.)
- `:104-108` — the header block's claim that `docs/GLOSSARY.md` carries the entry as `planned for
  0.0.14`, with two future-tense slice clauses, replaced by the shipped fact. Reason: two
  independent falsehoods — `docs/GLOSSARY.md:179` reads `shipped (0.0.14)`, and both clauses
  describe released work. (Box 3.)
- `:274-279` — `## Goal and cookbook cross-reference`'s premise "criterion 7 as written carves out no
  such case" dated to authoring time, and the outcome stated. Reason: `GOAL.md:513` now carries
  exactly that carve-out, so the present-tense premise was false; the argument is unchanged. (Box
  24.)

Deliberately **not** changed, each with the reason so the omission is a ruling and not a silence:
the `## Current state` bullets and their obligation-prose siblings (boxes 5, 6); all 33 spec
checkboxes (box 23); the five spec-internal `TODO(spec-044` / `TODO-ALPHA-044` mentions (box 9); the
post-`Status:` slice enumeration (box 4); the rationale file in full (box 25); the three dead
card-id pointers and the `config/schema.py` shape parenthetical (catalog items 3 and 4); and both
files' relative link paths, which resolve from `docs/` today and are R3's to re-relativize.

**Status-line re-verification (`worker-1.md` `## Spec status-line re-verification`).** Read `:1-115`
at the start of the pass. `:74`'s `Status:` line is accurate against HEAD in every clause and needed
no edit (box 2). The opener at `:3` and the header narration at `:104-108` were this item's declared
contract and are now fixed. No reference to a predecessor doc this build deleted survives: all four
`[spec-038]` / `[spec-041]` / `[spec-042]` / `[spec-043]` definitions resolve, as does `[rationale]`.

---

## Review (Worker 3)

Reviewed against the working tree with no memory of R2's reasoning. **R2's own contribution was
isolated by reconstruction, not by arithmetic:** `git show HEAD:docs/spec-044-debug_extension-0_0_14.md`
into a scratch path outside the repo, then `patch` with the diff captured at the end of R1 — the
reconstruction reproduces R1's recorded `63 / 396` numstat exactly, which is what makes it
trustworthy — then `diff -u <r1-end> <current>`. Result: **three hunks and nothing else**, at `:3-5`,
`:104-107`, and `:271-279`. No fourth hunk exists; nothing was changed that this artifact does not
record. No `git stash` / `checkout` / `restore` / `worktree` at any point.

### High:

None.

### Medium:

#### The header block's `**Version boundary**` paragraph is the same falsified-claim class the pass corrected, left neither corrected nor ruled on

`:56-73` sits **inside the header block** — the region step 1 of the plan declares in scope ("Re-verify
the spec's header lines `:1-115` against HEAD"), the region R1's hand-off explicitly handed to R2 ("R2
is the pass with the … context to rule on **the whole header region at once**"), and the region this
pass's own governing test puts on the corrected side ("Neither is a claim about now. **The header
block is.**"). It carries two claims the release falsified, in the same tenses the pass fixed two
paragraphs above and nineteen lines below:

```docs/spec-044-debug_extension-0_0_14.md:56
**Version boundary** (see [Decision 12](...)):
this card is the **last non-Done card at `0.0.14`**. Its three landed
predecessors — ... So unlike ... this spec's Slice 3
carries the version quintet, the GLOSSARY `shipped (0.0.14)` status flips for
all four `0.0.14` cards, and the release-status doc moves — mirroring the
lone-card ownership shape of [`spec-038`][spec-038] Decision 14.
```

`044` is `DONE-044-0.0.14`, so there is no non-Done card at `0.0.14` and nothing for Slice 3 to
carry — it carried it on 2026-07-20. The block now contradicts itself end to end: `:3-5` reads
"**completed** the joint `0.0.14` cut and **owned** the version bump", `:74`'s `Status:` reads "owned
and applied", and `:56-73` between them reads "is the last non-Done card" / "Slice 3 **carries**".
This is the second telling of release state the pass's own DRY ruling set out to eliminate, and it is
the one that rotted while the canonical telling was updated (see `### DRY findings`).

Not a judgement I am substituting for the pass's: the artifact contains **no ruling on this
paragraph at all** — it is absent from boxes 1-4, from `### Spec changes made (Worker 1 only)`, and
from the deliberate-non-edit list. Under `worker-3.md` review-job step 2 and `BUILD.md`
`## Severity definitions`, a contract item the diff does not address with no recorded deferral is
Medium.

**Recommended change** (Worker 1's file; a builder may not touch it): realign the paragraph's tense
to `:3-5` / `:74` — e.g. "this card **was** the last non-Done card at `0.0.14`" and "this spec's
Slice 3 **carried** the version quintet, the GLOSSARY `shipped (0.0.14)` status flips …" — leaving
the argument, the four card ids, and every anchor untouched. The alternative that also closes the
finding is a recorded ruling that the paragraph is authoring-frame; what cannot stand is silence,
because the governing test as written decides the opposite way for this region. No test expectation:
nothing here is executable.

### Low:

#### Decision 12's body repeats the same sentence, so the correction is one instance of a class

`:1656-1658` reads "**`044` is the last non-Done card at `0.0.14`** — the board shows no other WIP /
To-Do card at this patch version". Same present-tense claim about the board, same falsification. Its
frame is weaker than `:56`'s — a `### Decision N` justification is arguably authoring-time by
construction, and box 5's `## Current state` keep leans on exactly that reading ("Decision 12's
ownership argument rests on the version line reading `0.0.13`") — so I am **not** asking for it to be
rewritten. I am asking that whichever way `:56-73` is resolved, the resolution names this site, so the
spec does not end up with one instance corrected and its twin left standing for no stated reason.
(`:667`, the third instance, is inside `## Current state` and is already covered by box 5's ruling.)

#### Box 23's checkbox population is wrong: 43 boxes across three sections, not "nine DoD + 24 slice-checklist"

The **ruling** is right and I confirmed its measurement independently (0 ticked boxes in this spec and
in all four archived siblings). The **enumeration** is not. `grep -n '^\s*- \[[ x]\]'` gives 43
checkboxes: **20** in `## Slice checklist` (`:350`-`:505`), **14** in `## Helper-reuse obligations
(DRY)` (`:1736`-`:1940`, D1-D6 / D-N1-D-N8 — a section box 23 does not mention at all), and **9** in
`## Definition of done`. The sibling table's `- [ ]` figures (5 / 22 / 24 / 24) are **top-level-only**
counts and are internally consistent with each other; spec-044's comparable top-level figure is
**26**. Recommended change: state the population as 43 (20 / 14 / 9) or say the counts are top-level
only. Low because no box is mis-ticked either way.

#### The diff-isolation arithmetic is off by one line in each direction

`### Validation run` reads "a delta of **+13 / +14**, which is exactly the sum of this pass's three
edits (3-for-3 at the opener, **4-for-5** at the header narration, 6-for-6 at criterion 7)". Measured
against the reconstructed R1 end state, this pass's contribution is **12 insertions / 13 deletions** —
3-for-3, **3-for-4**, 6-for-6 — and the file goes 2840 → 2839 lines, consistent with 12/13 and not
with 13/14. The `+1 / +1` in the numstat delta is a diff-accounting artifact: the header-narration
edit abuts R1's large deletion hunk, so the combined-diff attribution shifts by one line each way.
The **conclusion** ("no fourth hunk exists") is correct — I proved it directly — but the arithmetic
does not prove it, and a later pass reusing delta-arithmetic as its isolation method would go hunting
a phantom line. Recommended change: keep the numstat figures, drop "exactly the sum", and cite the
reconstruction (or `diff -u` against a saved pass-1 copy) as the isolation proof.

### DRY findings

- **One live duplication, and it is the Medium.** The pass's DRY ruling is the right one — keep one
  source of truth for release state (`:74`'s `Status:` line) and have the opener point at it rather
  than copy it. `:56-73` is the counter-example that proves the ruling: a second, independently
  rottable telling of the same release facts, which rotted. Closing the Medium by pointing that
  paragraph at `Status:` (as `:3-5` now does) is the DRY-consistent fix; re-stating the quintet and
  the flips there in past tense would keep the duplication and merely refresh it.
- **No new duplication introduced.** The three edits add no fact not already stated elsewhere; the
  opener's `(see `Status:` below and [Decision 12])` hand-off is a pointer, not a copy. No helper, no
  literal, no near-copy: the diff is one markdown file.
- **Existence challenge:** none to raise. The pass introduces no abstraction, registry, helper, or
  indirection layer. The one scratch probe lives outside the repo and ships nothing.

### Public-surface check

Confirmed **mechanically**, not asserted: `git diff -- django_strawberry_framework/__init__.py`
produces no output (exit 0), so `__all__` and the re-export list are untouched. Independently,
`DjangoDebugExtension` appears exactly **once** in that file — inside the standing prohibition comment
at `:38-39` ("Do not import or root-export DjangoDebugExtension here: its public opt-in remains
django_strawberry_framework.extensions"), which is DoD row 4's negative half and box 19's claim.
Verified.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md (`git status --short` carries no entry for it, and
`CHANGELOG.md:19` still reads `## [0.0.14] - 2026-07-20` as box 15 part 7 records).

### Documentation / release sanity

Every check worked through explicitly; this is the pass the subsection was written for.

- **Version strings, shipped/planned statuses, card IDs.** Verified against HEAD, not against the
  artifact: the opener's `DONE-044-0.0.14` matches the live card; `docs/GLOSSARY.md:179` reads
  `shipped (`0.0.14`)` (edit 2's premise) and `:20` reads `Current package version: `0.0.14``; the
  other three `0.0.14` surfaces are flipped too (`:97` toolbar, `:107` router, `:197` `TestClient`,
  plus `:88` / `:177` companions); the quintet reads `0.0.14` at `pyproject.toml:4`,
  `django_strawberry_framework/__init__.py:41`, `tests/base/test_init.py::test_version`, `uv.lock:544`,
  GLOSSARY `:20`. `GOAL.md:513` carries the criterion-7 carve-out verbatim, so edit 3's falsification
  premise holds and its rewrite is accurate rather than merely different — it restates GOAL.md's own
  wording ("the import-only promise covers `Meta`-driven domain declarations; project-level engine
  configuration … migrates by documented recipe") and adds the outcome clause.
- **KANBAN movement.** Not applicable; R2 moved no card and touched no board file.
- **Markdown links.** Re-derived with my own auditor, both files. Spec: 35 headings, **200 in-page
  anchor occurrences across 26 distinct targets, 0 broken**; **102 definitions, 0 unused**, one
  "undefined" hit `"sql"` (the `res.extensions["debug"]["sql"]` code span — the standing false
  positive). Rationale: 20 headings, 2 anchor occurrences, 0 broken; 28 definitions, 0 undefined, 0
  unused. Every non-URL definition in both files resolves to an existing file **and** to a real
  heading in it. Figures identical to box 28's. Specifically confirmed: the opener's **new** in-page
  link resolves, and **Decision 12's heading is intact** at `:1654` with its slug unchanged, so all
  eleven citations of it still resolve — the deliberate opener/heading tense divergence costs nothing.
- **Archival.** R3 has not run; both files' relative paths resolve from `docs/` today. Not flagged,
  per the scope boundary.
- **Verbatim copies.** No verbatim spec-to-doc drop-in in this diff, so the character-for-character
  rule does not bind. The one quoted foreign string is the GLOSSARY status, and it matches `:179`.
- **No obsolete "planned" / old-version wording in files the slice deliberately updated.** This is
  where the `## Current state` ruling had to survive contact, and it **does**, on legs I re-derived
  rather than accepted: (1) the four-sibling measurement is real — `A true description of the repo as
  this spec is authored:` is byte-identical in `spec-038:529`, `spec-041:699`, `spec-042:643`,
  `spec-043:516` and `spec-044:565`, and each of the four ships **0** `- [x]`; (2) the "premises the
  Decisions argue from" claim is real, not decorative — `### Decision 12` argues from the version line
  ("Leaving the version at `0.0.13` after `044` ships would strand four cards' worth of shipped
  surface"), and `## Doc updates` `:2490-2492` plus Decision 2 both act on the `config/schema.py` "has
  no direct Strawberry analogue" sentence the bullet quotes, so deleting the quotes would orphan two
  obligations; (3) the section's own lead-in is the nearer frame, and no framing caveat was added,
  which keeps the four archived siblings comparable. **One counterweight the artifact does not record,
  and it should:** `:113-115` now reads "This document is the contract and states only what is
  currently true; it never narrates its own history" — a sentence **R1 added** (absent from
  `git show HEAD:` and from all four archived siblings; present only in the two specs that have
  rationale companions). So leg (1)'s comparability is weaker than stated: 044 uniquely asserts of
  itself what `## Current state` then contradicts. I do not think that overturns the keep — the local
  dating lead-in is the nearer and more specific frame — but it is exactly why the **header block**
  cannot also carry unruled stale claims, which is the Medium above.
- **Script-rendered docs.** None regenerated this pass; no feeding docstring changed. `docs/TREE.md`
  carries real docstring-derived `extensions/` rows (`:218`, `:332`, `:467`, `:679`) and **zero**
  `TODO-ALPHA-044` occurrences, so box 12's claim holds and no staging language is being rendered.

### Checklist walk (boxes 1-33)

Every box is either landed in the diff or an audit obligation discharged by verification. Sampled and
re-derived as follows; nothing is ticked without a matching change or a recorded finding.

- **1, 3, 24 (the three edits)** — all three land in the isolated diff, at the claimed lines, with the
  claimed text. Box 1's sibling-derived form checked against `docs/SPECS/spec-042-…:3` and
  `spec-043-…:3` ("Built for `0.0.14` (card [`DONE-04N-0.0.14`][kanban]); … (see `Status:` below)") —
  the form is taken, not invented, and the two documented departures (ownership vs ridership, past
  tense) are visible in the diff. Box 3's **two** falsehoods both verified: the quoted status against
  `docs/GLOSSARY.md:179`, and the future-tense clauses against a release dated 2026-07-20. Box 24's
  falsification verified against `GOAL.md:513`.
- **2 (`Status:` at `:74`)** — read clause by clause; every clause true at HEAD (quintet, four
  GLOSSARY flips, release-status moves). No edit owed. ✔
- **4, 5, 6, 9, 23, 25 (the deliberate keeps)** — each carries a recorded ruling, which is what the
  boxes claim. Box 5's evidence re-derived above. Box 25 re-derived: the rationale is **byte-identical
  at 43,859**, matching R1's recorded figure (`bld-044-r1…:390`), and its two checked sites are as
  described — `WIP-ALPHA-044` survives only in the Revision-1 chronology line, and its one citation of
  the spec's header names the moved "Revision history" line, not a sentence this pass touched. Box 23's
  count is the Low above.
- **7, 8, 10 (the staged-anchor sweep)** — reproduced independently, not inherited:
  `grep -rEn 'TODO\(spec-044|TODO-(ALPHA|BETA|STABLE)-044' django_strawberry_framework tests examples scripts | wc -l`
  → **0**. Tree-wide with `KANBAN.md` / `KANBAN.html` / `BACKLOG.md` excluded, the surviving hits are
  exactly the classes box 10 names: five spec-044-internal (`:427`, `:430`, `:452`, `:576`, `:578`),
  archived siblings + two archived `-terms.csv`, `docs/builder/` scratchpads, and the two live sibling
  specs. `tests/extensions/__init__.py` carries no anchor and its docstring instead states the
  Decision-11 split rule. **Box 9's correction to R1's hand-off is right:** `:452` is inside
  `## Slice checklist` (`:340`-`:528`), `## Doc updates` begins at `:2449`, and its `docs/TREE.md`
  row (`:2484-2489`) contains no anchor text. The one-line offset from R1's `:453` is explained by
  this pass's net −1 line above it, so the count of five is stable and only the label moved.
- **11-15 (`## Doc updates`, five rows)** — sampled where failure would matter most and where the
  claim is cheapest to assert without checking. Row 3 verified in the file:
  `examples/fakeshop/config/schema.py`'s docstring now reads "The response-side ``DjangoDebugExtension``
  is opt-in and deliberately omitted from this aggregate schema; live coverage mounts it through a
  probe URLconf" — the falsified sentence is gone. Row 4 verified at `GOAL.md:513`. Row 2 verified in
  `docs/TREE.md` (above). Row 1 spot-checked in both directions (`docs/GLOSSARY.md:1514` entry with
  `**Status:** shipped (`0.0.14`)` and the toolbar cross-reference at `:424`, plus `:502`'s import-path
  / class-form / per-operation posture). Row 5 sampled at its five most falsifiable parts:
  `CHANGELOG.md:19`, `README.md:62`, `docs/README.md`'s `**Shipped today** (`0.0.14`)` block with the
  `DONE-044` bullet **and** no surviving "coming next" release wording (the only hit is the section
  heading `## Today and coming next`), `TODAY.md`'s shipped-tense `DjangoDebugExtension` bullet, and
  the quintet. No drift found in any sampled row.
- **16-22 (`## Definition of done`, nine rows)** — sampled likewise. Row 5's floor is the one whose
  failure would matter most and it holds at all five sites: `pyproject.toml:35`
  `"strawberry-graphql>=0.316.0"`, `uv.lock:577` `specifier = ">=0.316.0"`, and
  `.github/workflows/django.yml:56`, `:57`, `:73` — **three** matrix nodes pinning exactly `0.316.0`,
  with `:51`'s comment naming the per-operation isolation reason. Row 4's negative half is pinned in
  source (see `### Public-surface check`). Row 1 verified by symbol
  (`extensions/debug.py::DjangoDebugExtension` at `:371`, `on_operation` `:419`, `get_results` `:460`).
  Row 3 verified from `config/schema.py:77-81`: `DjangoSchema(…, extensions=[lambda: _optimizer])`, so
  fakeshop's documented opt-out is genuinely the extension-absent case. Row 6's two files exist at the
  recorded sizes. Row 9's "process row the shipped cycle discharged" is the right disposition —
  `AGENTS.md` rule 15 forbids the re-run that would re-prove it.
- **26 (positional citations)** — **re-derived rather than accepted**, whitespace-flattened over both
  files with a 3-line sliding window, because a citation broken across a line wrap is invisible to
  `grep -n` (R1's lesson). After the edits: `planned for 0.0.14` → 3 flattened hits, all
  obligation-prose keeps; `completes the joint` / `owns the version bump` → 1 spec hit each, both the
  untouched Decision-12 heading, plus 1 rationale hit which is the mirrored heading; `WIP-ALPHA-044` →
  1 rationale hit (the Revision-1 line); "the spec's header" → 1 rationale hit, naming the moved
  Revision-history line. `criterion 7` resolved site by site: none cites `:274` positionally.
  **Nothing cites a sentence this pass rewrote.** Confirmed.
- **27, 28, 29 (mechanical gates)** — all re-run in this review.
  `check_spec_glossary.py --spec docs/spec-044-…md` → `OK: 42 terms …`, exit **0**;
  `check_trailing_commas.py --check` on the three explicit paths → exit **0**; the link audit above
  reproduces box 28 figure for figure. Box 27's ordering claim is sound: no edit removed a
  `GLOSSARY.md#…` link or a `][glossary-…]` use, and the rewritten `:104-107` deliberately keeps
  `[glossary-response-extensions-debug-middleware]`, which is what keeps that term's only spec link
  alive.
- **30, 31 (byte counts, scope)** — spec **185,518 → 185,542 (+24)** and rationale **43,859 →
  43,859** independently confirmed (`wc -c`; the R1 end state measured from the reconstruction).
  `git status --short` matches the recorded six entries exactly; no package source, test, `examples/`,
  `scripts/`, release-metadata, generated-doc, other-spec, or preserved-cycle artifact is touched.
- **32 (no Worker 2 dispatch needed)** — tested rather than accepted, since "nothing for the builder
  to do" is the convenient conclusion. All five `## Doc updates` rows and the sampled DoD rows land at
  HEAD in shipped tense (above), and an independent sweep of `django_strawberry_framework/` +
  `examples/fakeshop/config/schema.py` for staging language (`planned`, `not yet`, `future work`, "no
  direct Strawberry analogue") returns **zero**. The claim holds **as scoped** — no sentence *spec-044's
  shipping* falsified survives in a builder-writable file. One caveat: it is not a claim that every
  illustrative snippet in the tree is exact; see catalog addition 5 below, which is a *different*
  card's drift and correctly outside R2.
- **33 (deferred-work items)** — verified individually under `### Notes for Worker 1` below.

### What looks solid

- **The isolation of a three-edit prose pass is auditable and was audited.** Three hunks, each with a
  recorded reason, each premise verified against the file it cites. Nothing crept in.
- **The governing test is the right test and is stated in a form that can be attacked** — box 24 puts
  the distinguishing argument on the page instead of asserting consistency, which is why this review
  could test it at all. The `## Current state` keep survives the test; the header block is where the
  test's own answer was not followed through.
- **The `## Current state` ruling refused the easy over-correction.** Adding a framing caveat would
  have looked like diligence and would have made 044 read differently from its three release siblings
  at exactly the point a reader compares them. Not adding one is the harder and better call.
- **Decision 12's heading and its 200-occurrence anchor graph were left alone on purpose**, with the
  tense divergence recorded so a later reader does not "fix" it. That is the correct trade.
- **The dead-card-id cluster was refused for the right reason**, with the ten-file blast radius
  measured (I reproduced it) rather than asserted, and with per-target confidence stated.

### Temp test verification

- `docs/builder/temp-tests/044-r2/link_audit.py` — my own in-page-anchor / ref-def-symmetry /
  cross-file-anchor auditor, written independently rather than reusing the pass's scratch probe, so
  box 28 is confirmed by a second implementation. Disposition: **kept as gitignored scratch, not
  promoted** — it audits a document, pins no package behavior, and `AGENTS.md`'s test trees are for
  package coverage. Worth noting for R3: the slugifier hazard the pass flagged is real and I hit it —
  stripping `_` from headings falsely reports every `_debug` / `finalize_django_types` /
  `require_optional_module` anchor broken (9 phantom failures before the fix).
- No other temp test. Nothing in the diff is executable, so no `pytest` run was performed — stating
  that rather than running one for form. No `--cov*` flag was used anywhere in this pass.

### Failability proofs

Not applicable, and this is arithmetic rather than a chosen subset: the diff introduces no boundary,
guard, gate, or rejection path — it contains no `.py` file and no executable line — so `BUILD.md`
`### What needs a proof, and what does not` scopes the obligation to zero and the mandatory re-run
floor is empty by that scope. The build report's own `None; this pass introduced no new boundary.`
is accurate. No fail-open shape can exist where there is no expression.

### Hot-path budget

Not applicable; the plan declares hot-path `none` for the whole cycle and this pass changes no package
source, which the isolated diff confirms. No number is owed. Floor verification likewise: the plan's
floor-verification scope is `none`, no Django / Strawberry / channels seam is touched, and no
version-dependent reasoning was needed or performed.

### Notes for Worker 1 (spec reconciliation)

- **Escalated (Medium):** the `**Version boundary**` paragraph at `:56-73`. Two resolution paths, in
  the order I would take them: (a) realign its tense to `:3-5` / `:74`, which is the DRY-consistent
  and cheapest fix and touches no anchor; (b) record a ruling that a `**Version boundary**` paragraph
  is authoring-frame — but then say why the same reasoning does not return the `:3-5` opener and the
  `:104-107` GLOSSARY sentence to their original tense, since all three sit in the same block. Either
  path should also name `:1656-1658` (the Low above) so the class is closed rather than one instance.
- **Not a finding, but record it in the ruling if `## Current state` is revisited:** `:113-115`'s "This
  document … states only what is currently true; it never narrates its own history" is **new to this
  cycle** (R1 added it; absent at HEAD and from all four archived siblings). It weakens leg (a) of
  box 5's argument, which rests on 044 being comparable to those siblings. My read is that the keep
  still stands on legs (b) and (d); the maintainer may prefer the reverse. Worth one sentence in the
  spec's own ruling record either way.
- **The dead-card-id cluster (catalog item 3): confirmed recorded well enough to act on, and not filed
  as a finding**, per the standing rule that a spec-only correction diverging from un-editable copies
  is worse than uniformly wrong. I reproduced the blast radius: `TODO-BETA-053-0.1.5` hits **ten
  files** — `TODAY.md`, `docs/spec-044-…`, six archived specs (`spec-030`, `032`, `033`, `037`, `041`,
  `042`), and `examples/fakeshop/apps/products/schema.py` + `examples/fakeshop/test_query/test_products_api.py`
  — exactly as recorded. **One refinement the catalog should carry:** `TODO-BETA-045-0.1.0` occurs in
  **spec-044 only** (plus this cycle's artifacts), so the two ids do **not** share a blast radius —
  the "worse than uniformly wrong" argument covers `053` and not `045`, which a maintainer could
  repoint locally at zero divergence cost. Same owner, but two different-sized jobs.

### For the `### Deferred work catalog` in `bld-044-final.md` (Worker 3's verification and additions)

All four recorded items are real, and each is located precisely enough for the maintainer to act.
Verified individually:

1. **Confirmed.** `docs/spec-050-…:390` and `docs/spec-051-…:556` do assert live `TODO(spec-044 Slice 3)`
   anchors; zero such anchors exist in source or tests; and both sentences sit under those specs'
   `## Architectural decisions` (`spec-050:258`, `spec-051:309`), so "normative prose, not a dated
   snapshot" is right.
2. **Confirmed, and the question is posed fairly** — with one sharpening. Both sentences do sit in
   those specs' own `## Current state` (`spec-050:155`, `spec-051:215`), and I verified the caveat the
   item rests on: **neither section carries the `A true description of the repo as this spec is
   authored:` lead-in** — both go straight to bullets. So under this pass's own governing test those
   two sections do **not** self-date and therefore read as claims about now, which makes them drift
   rather than preserved history; the in-flight status of both specs makes a refresh the likely
   answer. Recording them as a question rather than a defect is defensible for a pass that cannot edit
   them, but the maintainer should read item 2 as "probably drift, owner = each spec's author", not as
   a coin flip.
3. **Confirmed.** See `### Notes for Worker 1` above, including the `045` / `053` blast-radius
   refinement.
4. **Confirmed exactly as characterised.** `:291-297` names `strawberry.Schema(query=Query,
   config=strawberry_config(), extensions=[lambda: _optimizer])` as "the canonical shape
   `config/schema.py` demonstrates today"; `examples/fakeshop/config/schema.py:77-81` builds
   `DjangoSchema(query=Query, mutation=Mutation, …)`; and `DjangoSchema` **is** a `strawberry.Schema`
   subclass (`django_strawberry_framework/schema.py:199`), so "inexact rather than false" is the right
   grade and the maintainer call it defers to (whether the cookbook recipe should now name
   `DjangoSchema`) is genuinely a spec-central one.
5. **New, found this pass — item 4 has a second surface, and it is a standing doc rather than a spec
   parenthetical.** `examples/fakeshop/test_query/README.md` (final paragraph before the isolation
   contract) states that the project schema "constructs `strawberry.Schema(query=Query,
   mutation=Mutation, config=strawberry_config(), extensions=[lambda: _optimizer])`" — the same
   divergence from `config/schema.py:77`'s `DjangoSchema(...)`, in a file R2 could not write and whose
   audience is every worker who reads the live-tier README as required reading. Caused by the
   mutation-atomicity card, not by spec-044's shipping, so it is correctly outside every residual
   item; but whoever answers item 4 should answer both surfaces in one pass, or the spec and the
   README will disagree with each other as well as with the code.
6. **The `065` / `046` card-id split the artifact observed is real and precisely located:**
   `TODAY.md:384` attributes the router redesign to "the transport-security card `065`" while
   `docs/README.md:128` attributes it to `046`; the 2026-07-30 renumber moved 065 → 046, so `TODAY.md`
   carries the pre-renumber number. Belongs to the preserved spec-046 cycle or the renumber's closeout,
   as recorded.

### Review outcome

**`revision-needed`** — one Medium, three Low, no High.

The Medium is a falsehood in the spec's header block, inside the region this item declared in scope
and R1 explicitly handed it, decided the other way by the pass's own governing test, and neither
corrected nor ruled on. `worker-3.md`'s acceptance gate does not let me accept an unresolved Medium
without a recorded rejection reason, and there is no reason recorded because the paragraph was not
seen. Under **Deviation 3** this routes to **Worker 1**, not Worker 2 — the fix is in the active spec,
which only Worker 1 may edit; no part of any finding lies in a Worker-2-writable file, so no builder
dispatch is needed to close them.

The three Lows are cheap and can land in the same pass: the Decision-12 twin named alongside the
Medium's resolution, box 23's checkbox population corrected (43 = 20 / 14 / 9, or the counts labelled
top-level-only), and the `+13 / +14` "exactly the sum" arithmetic replaced by the reconstruction proof.
Everything else in R2 — the ruling, the three edits, the fourteen-row audit, the anchor sweep, and the
four-item catalog — I verified and would accept unchanged; the pass is one paragraph short of complete,
not misdirected.

---

## Build report (Worker 1, pass 2 — custodian apply)

Worker 3 set `revision-needed` on R2. Under the plan's **Deviation 3** this item has no Worker 2 —
and independently, no finding lies in a Worker-2-writable file — so the apply pass is Worker 1's in
the builder's seat. The section therefore carries the `## Build report` shape from
`docs/builder/ARTIFACT.md` with Worker 1 named, appended at the end at the **same top level** so the
artifact still reads as a linear plan / apply / review / apply sequence, and **no prior entry is
edited**: not the plan, not Worker 3's review, not pass 1's build report. The two exceptions are the
`### Dispatched findings checklist` boxes whose *assertions* the review falsified — boxes **23** and
**30** — which the audit discipline in `BUILD.md` `### Dispatched findings checklist` assigns to
Worker 1, and each is marked inline as pass 2's.

**`Status:` on return is `planned`, not `built`.** Deviation 3 makes `planned` this item's
"ready for review" value, routing Worker 0 to dispatch Worker 3 for a re-review.

### Files touched

- `docs/spec-044-debug_extension-0_0_14.md` — three edits: the `**Version boundary**` paragraph's
  tense **and** its duplicated enumeration of the cut's contents (`:58`, `:67-72`), plus the two dead
  `TODO-BETA-045-0.1.0` card-id pointers (`:1686`, `:2641`). Enumerated under
  `### Spec changes made (Worker 1 only), pass 2`.
- `docs/builder/bld-044-r2-doc_completion.md` — this section, the two falsified box assertions,
  `Status:`.
- `docs/builder/worker-memory/worker-1.md` — memory entry.

No package source, no test, no `examples/` (including `examples/fakeshop/test_query/README.md`, which
Worker 3's new catalog item 5 names), no `scripts/`, no `pyproject.toml` / `uv.lock` / `CHANGELOG.md` /
`docs/GLOSSARY.md` / `docs/TREE.md` / `KANBAN.*`, no `README.md` / `GOAL.md` / `TODAY.md` /
`docs/README.md`, no other `docs/spec-*.md`, no archived spec, no preserved spec-046 `bld-*.md`. The
rationale file was again audited and again needed nothing (below). No commit, no branch, no
`stash` / `checkout` / `restore` / `worktree`. R3 not performed.

### Worker 3's findings, one by one

**Medium — the `**Version boundary**` paragraph at `:56-73` was neither corrected nor ruled on. AGREED, FIXED, and the fix is the DRY one rather than the cheap one.**

The finding is exact and I verified it rather than accepting it: `:58` read "this card **is** the
**last non-Done card at `0.0.14`**" and `:69-71` read "this spec's Slice 3 **carries** the version
quintet, the GLOSSARY `shipped (0.0.14)` status flips for all four `0.0.14` cards, and the
release-status doc moves". Card 044 is `DONE-044-0.0.14`, so there is no non-Done card at `0.0.14`
and nothing left for Slice 3 to carry. **The self-contradiction spanned eighteen lines**: `:3-5`
completed/owned, `:56-73` is/carries, `:74` owned and applied.

Worker 3 is also right that my own artifact carried **no ruling on it at all** — not in boxes 1-4, not
in `### Spec changes made (Worker 1 only)`, not in the deliberate-non-edit list. That is the failure
worth naming plainly: **my step 1 declared `:1-115` in scope, my governing test decides this region
on the corrected side, and I audited the two paragraphs on either side of it and not the one between
them.** A declared range is not an audited range unless every paragraph in it is named.

**Two resolution paths were offered; I took (a), and Worker 3's own `### DRY findings` is why it is
more than a tense fix.** Path (b) — ruling the paragraph authoring-frame — is not available without
also returning `:3-5` and `:104-107` to their original tense, since all three sit in one block; that
is the test's answer and it cannot be applied selectively. So the paragraph is realigned. But a
straight past-tensing would have **kept the duplication and merely refreshed it**: `:69-71`'s
enumeration ("the version quintet, the GLOSSARY `shipped (0.0.14)` status flips …, and the
release-status doc moves") is a substantive restatement of `:74`'s own parenthetical. Applied:

- `:58` — `is the **last non-Done card at `0.0.14`**` -> `was the …`.
- `:67` — `That card is this one.` -> `That card was this one.`
- `:69-72` — `this spec's Slice 3 carries the version quintet, the GLOSSARY `shipped (0.0.14)` status
  flips for all four `0.0.14` cards, and the release-status doc moves — mirroring the lone-card
  ownership shape of [`spec-038`] Decision 14.` -> `this spec's Slice 3 **carried the cut** — mirroring
  the lone-card ownership shape of [`spec-038`] Decision 14. **What the cut contained is recorded
  once, in the `Status:` line below.**`

So the paragraph now keeps everything that is argument — the three predecessors and their deferrals,
the last-card-owns rule, the contrast with the three siblings' Decision 10/10/12, the `spec-038`
lone-card mirror, all four card ids, and every link — and **stops being a second telling of release
state**. The paragraph is 17 lines before and after; no anchor, no link definition, and no glossary
link was touched, which is why `check_spec_glossary.py` still reports 42 terms.

**Low 1 — Decision 12's body at `:1656-1658` repeats the sentence. NAMED AND DELIBERATELY KEPT, and the class was swept rather than the two known instances patched.**

Worker 3 asked for the resolution to name this site rather than for a rewrite, and I agree with its
reasoning and adopt it: a `### Decision N` block records **the ground on which the decision was
taken**, so its frame is the decision's own moment. That is not a convenience — box 5's
`## Current state` keep *depends* on the same reading, since Decision 12 argues from the version line
reading `0.0.13`. Correcting the Decision body to past tense while `## Current state` still says "The
version line reads `0.0.13`" would be the inconsistency, not the fix. **KEPT, with the reason on the
record.**

**The class sweep found a fourth instance Worker 3 did not name, and a fifth site that is the same
sentence in a third frame.** Per R1's rule the grep is the **vocabulary of the changed text,
whitespace-flattened**, not a line-oriented search for the sentence already known
(`last non-?Done`, `non-?Done card`, `only non-Done`, `carries the version quintet`, `owns the cut`,
`last card of the patch line`, `joint cut.s last leg`, `release-status doc moves`,
`all four .0\.0\.14. cards`, `That card (is|was) this one`). Every hit, resolved with its frame and
its owner:

| Site | Text | Frame | Ruling |
|---|---|---|---|
| `:58`, `:67`, `:69-72` | "is the last non-Done card" / "Slice 3 carries …" | **header block** — describes the spec's current status | **CORRECTED** (the Medium) |
| `:1657` | "**`044` is the last non-Done card at `0.0.14`**" | `### Decision 12` justification — the decision's own moment | **KEPT** (Low 1, named) |
| `:663-668` | "The version line reads `0.0.13`, and this card is the joint cut's last leg … `044` is the only non-Done card at `0.0.14`" | `## Current state` — self-dated snapshot | **KEPT** (box 5) |
| `:726-729` | "**The `0.0.14` release becomes real.** Slice 3 aligns the version quintet and flips the release-status wording for all four `0.0.14` cards" | `## Goals` — an aspiration list, obligation-framed by construction | **KEPT — new this pass** |

The fourth row is the one neither the review nor pass 1 named. It is kept under the same test, and the
frame was verified against the siblings rather than assumed: `docs/SPECS/spec-042-…` and
`spec-043-…`'s `## Goals` ship in the identical "With X wired, a developer …" aspiration tense. Zero
hits of any pattern in the rationale file, so the class is closed at four sites with a stated owner
each — **one corrected, three kept for three different stated reasons.**

**Low 2 — box 23's checkbox population was wrong. FIXED IN PLACE, and the miscount's mechanism is recorded.**

Re-measured rather than copied from the review: **43** boxes, **20** `## Slice checklist` / **14**
`## Helper-reuse obligations (DRY)` / **9** `## Definition of done`, **0** ticked. My "nine + 24" was
wrong twice — a mis-counted slice checklist and an omitted section. **The mechanism matters more than
the number:** 24 was a half-remembered blend of the slice checklist's 20 and the sibling table's
top-level-only 22/24 column, i.e. I compared a total against top-level counts. The corrected box now
states both scopes (43 total, 26 top-level) so the comparison is checkable. The **ruling** is
untouched; Worker 3 re-derived its measurement independently and it held.

**Low 3 — the `+13 / +14` "exactly the sum" isolation arithmetic was wrong. CORRECTED HERE, NOT IN PLACE, and the placement is deliberate.**

The stale claim sits in `## Build report (Worker 1, performing R2)` `### Validation run`.
`ARTIFACT.md` `## Re-pass sections` forbids editing a prior entry's body — the licensed exceptions are
the checklist boxes and their figures — so the correction is **published here**, exactly as R1's
final verification handled the same shape. Worker 3's measurement is right and its diagnosis of mine
is right:

- Pass 1's real contribution was **12 insertions / 13 deletions** — 3-for-3 at the opener,
  **3-for-4** (not 4-for-5) at the header narration, 6-for-6 at criterion 7 — and the file went
  **2,840 -> 2,839** lines, which is consistent with 12/13 and not with 13/14.
- The `+1 / +1` I reported came from **hunk adjacency**: the header-narration edit abuts R1's large
  deletion hunk, so the combined diff's attribution shifts one line each way.
- **The corrected sentence pass 1 should have carried:** *`git diff --numstat` reads 76 / 410 against
  R1's 63 / 396, a delta of +13 / +14; the delta is one line inflated in each direction by hunk
  adjacency with R1's deletion, so it corroborates rather than proves the isolation. The proof is a
  reconstruction — `git show HEAD:<spec>` into a scratch path outside the repo, `patch` with R1's
  captured diff (which reproduces 63 / 396 exactly), then `diff -u` against the working tree.*
- **The lesson, which is the part worth keeping:** delta-arithmetic over a combined diff is not an
  isolation method. A later pass reusing it would go hunting a phantom line. **And the cheap route
  Worker 3's reconstruction makes unnecessary is `git diff -U0`** — zero context puts every changed
  line in its own hunk, so adjacency cannot merge or shift anything and no scratch reconstruction is
  needed to enumerate a pass's own regions. That is how this pass isolates itself, below.

**The counterweight Worker 3 asked to be recorded rather than acted on — RECORDED, and it does sharpen the ruling.**

`:113-115` ("This document is the contract and states only what is currently true; it never narrates
its own history") is **R1's sentence** — absent from `git show HEAD:` and from all four archived
siblings, present only in the two specs that have rationale companions. I verified that
independently. So leg (a) of box 5's argument — four-sibling comparability — **is weaker than pass 1
stated**: spec-044 uniquely asserts of itself a property that `## Current state` then appears to
contradict. Three things follow, and I state all three rather than only the convenient one:

1. **The keep still stands**, on the legs Worker 3 re-derived: the section's own dating lead-in is the
   nearer and more specific frame than a general header sentence, and the bullets are load-bearing
   premises (Decision 12 argues from the `0.0.13` version line; Decision 2 and the `## Doc updates`
   row at `:2490` both act on the `config/schema.py` sentence the bullet quotes, so deleting the
   quotes would orphan two obligations).
2. **`:113-115` is not itself false**, because "the contract" is what it claims to state currently
   true, and `## Current state` is explicitly a dated snapshot rather than contract. But the tension
   is real enough that a reader can feel it, which is the honest characterisation.
3. **It is precisely why the header block cannot carry unruled stale claims** — the sentence promising
   that the document states only what is currently true sits eight lines below a paragraph that did
   not. That is this pass's Medium, and R1's sentence is what made it worse rather than merely
   untidy. Recorded here rather than by editing `:113-115`: the sentence is a correct statement of
   the spec's *contract* posture, and weakening it to accommodate the snapshot section would trade a
   true general claim for a hedge.

### Validation run

- `uv run python scripts/check_spec_glossary.py --spec docs/spec-044-debug_extension-0_0_14.md` ->
  `OK: 42 terms - all have glossary entries and at least one spec link.` **exit 0**. Checked in the
  right order again: the removed clause at `:69-71` carries **no** `][glossary-…]` use and no
  `](…GLOSSARY.md#…)` link, verified before the cut, so no term could lose its only spec link.
- `uv run python scripts/check_trailing_commas.py --check docs/spec-044-debug_extension-0_0_14.md
  docs/spec-044-debug_extension-0_0_14-rationale.md docs/builder/bld-044-r2-doc_completion.md` ->
  **exit 0**. Explicit paths only; run pathless it rewrites unrelated `docs/` scratch files.
- **In-page anchors and ref/def symmetry, both files, re-run:** spec 35 headings, **200 anchor
  occurrences / 26 distinct targets / 0 broken**; **102 definitions, 0 unused**, one "undefined" hit
  `"sql"` (the standing `][…]`-probe false positive). Rationale 20 headings, 2 occurrences, 0 broken,
  28 definitions, 0 undefined, 0 unused. Every non-URL definition in both files resolves to a file
  that exists **and** to a real heading in it. Figures identical to pass 1's and to Worker 3's, which
  is the expected result: this pass added and removed no link and no heading. The two card-id rewrites
  reuse the already-defined `[kanban]`, so no definition was added and none went unused.
- **Positional-citation sweep, whitespace-flattened, before and after each edit.** Before: the ten
  patterns above, resolved into the four-row table. After: `carries the version quintet` -> **0**;
  `carried the cut` -> 1 (the new text); `last non-Done` -> 2 (the corrected header site and the
  deliberately-kept Decision 12 site); `release-status doc moves` -> 1 (`:74`'s `Status:` line, now
  the **single** telling); `TODO-BETA-045` -> **0**; `TODO-ALPHA-052` -> 2 (both rewritten sites).
  Zero hits of any pattern in the rationale file. Nothing anywhere cites a sentence this pass rewrote,
  and no sibling spec or standing doc cites spec-044's `**Version boundary**` paragraph — five sibling
  specs carry a paragraph under that same label, which confirms the label is a convention this edit
  preserved rather than a target.
- **Hunk count matches edit count, enumerated directly rather than inferred from a delta** (Low 3's
  lesson applied in the same pass that recorded it — and it caught a draft of this very bullet, which
  had asserted "three hunks" before the enumeration was run). `git diff -U0` over the spec isolates
  every changed line into its own hunk, which sidesteps the adjacency artifact entirely. Of the **34**
  zero-context hunks against HEAD, **five are pass 2's** and every one is accounted for:
  `@@ -58 +58 @@` (`is` -> `was`), `@@ -67 +67 @@` (`That card is` -> `was`), `@@ -70,3 +70,3 @@` (the
  enumeration replaced by the `Status:` pointer), `@@ -2015 +1686 @@` and `@@ -2990 +2641 @@` (the two
  card-id rewrites, 975 lines apart and therefore never coalescing). Three `Edit` operations produced
  those five regions because one edit spanned a six-line block containing two non-adjacent changed
  lines and one replaced both card-id occurrences at once — so **3 edits, 5 zero-context hunks, 7
  insertions / 7 deletions**, and no sixth region exists.
- **This time the delta arithmetic agrees, and the reason it does is the point.** `git diff --numstat`
  reads **83 / 417** against pass 1's **76 / 410** — a delta of **+7 / +7**, exactly the five hunks'
  line counts (1 + 1 + 3 + 1 + 1). Pass 1's arithmetic was off by one each way because its
  header-narration edit **abutted R1's large deletion hunk**; none of pass 2's five regions touches
  another hunk's context, so no attribution shifts. Delta arithmetic corroborating a direct
  enumeration is worth reporting; delta arithmetic **as** the isolation method is what Low 3 retired.
- No `git stash` / `checkout` / `restore` / `worktree` at any point.
- **Byte and line counts.** Spec **185,542 -> 185,496** (**-46**), lines **2,839 -> 2,839** — the
  paragraph is 17 lines before and after and both card-id rewrites are in-line, so an unchanged line
  count with a negative byte delta is exactly what the edits predict. Rationale **43,859**,
  byte-identical for the third consecutive pass.
- `git status --short` -> six entries, unchanged in shape from pass 1 and from R1: `M docs/feedback.md`,
  `M docs/spec-044-debug_extension-0_0_14.md`, `D to-many-search-optimizer-reproduction.md`,
  `?? docs/builder/bld-044-r1-rationale_move.md`, `?? docs/builder/bld-044-r2-doc_completion.md`,
  `?? docs/builder/build-044-debug_extension-0_0_14.md`,
  `?? docs/spec-044-debug_extension-0_0_14-rationale.md`.
- No `ruff` run (no `.py` file touched); no `pytest` (nothing in the diff is executable, and
  `AGENTS.md` rule 15 forbids an unrequested run). No `--cov*` flag in this or any pass.

### Failability proofs

None; this pass introduced no new boundary. The diff is one markdown file with no executable line, so
`BUILD.md` `### What needs a proof, and what does not` scopes the obligation to zero. Read for the
catalogued fail-open shapes as well: none can exist where there is no expression.

### Hot-path budget

Not applicable; plan declares no hot path, and the isolated diff confirms no package source changed.

### Floor verification

Not applicable; plan declares floor-verification scope `none`. No Django / Strawberry / channels seam
is touched and no version-dependent reasoning was needed.

### Dispatched findings checklist — audit of this pass

The plan's 33-box checklist is pass 1's and stands, with boxes 23 and 30 corrected in place as marked.
These four boxes cover pass 2's own dispatch:

- [x] **P2-1 — Medium: the `**Version boundary**` paragraph.** Fixed at `:58`, `:67`, `:69-72`; tense
      realigned to `:3-5` / `:74` **and** the duplicated enumeration replaced by a pointer at
      `Status:`, which is the DRY-consistent of the two available fixes. Ruled on explicitly, above.
- [x] **P2-2 — Low 1: Decision 12's twin at `:1657`.** Named and deliberately kept, with the reason
      (a `### Decision N` block's frame is the decision's own moment, and box 5's keep depends on that
      same reading). The class was swept, not the instance patched: **four** sites, one corrected and
      three kept, tabulated above — including a fourth in `## Goals` that the review did not name.
- [x] **P2-3 — Low 2: box 23's checkbox population.** Corrected in place to 43 (20 / 14 / 9), 26
      top-level, with the total-vs-top-level confusion that caused the miscount recorded.
- [x] **P2-4 — Low 3: the isolation arithmetic.** Corrected here rather than in the prior entry's
      body (`ARTIFACT.md` `## Re-pass sections`), with pass 1's sentence rewritten as it should have
      read. This pass isolates itself by **direct `git diff -U0` hunk enumeration** instead — and the
      new method immediately earned itself: a draft of that bullet asserted "three hunks" from the same
      kind of guess, and the enumeration measured **five** (3 edits, 5 zero-context hunks, 7/7 lines).

### Spec changes made (Worker 1 only), pass 2

Three edits, each with the line range as numbered **before** the edit and a one-line reason.

- `docs/spec-044-debug_extension-0_0_14.md:58` and `:67` — "this card **is** the last non-Done card"
  and "That card **is** this one" past-tensed. Reason: card 044 is `DONE-044-0.0.14`, so both were
  false present-tense claims inside the header block. (Worker 3's Medium.)
- `:69-72` — Slice 3's "**carries** the version quintet, the GLOSSARY `shipped (0.0.14)` status flips
  …, and the release-status doc moves" replaced by "**carried the cut** … What the cut contained is
  recorded once, in the `Status:` line below." Reason: false in tense **and** a second, independently
  rottable telling of the release facts `:74` owns — the duplication this pass's own DRY ruling set
  out to eliminate, and the telling that rotted. (Worker 3's Medium + `### DRY findings`.)
- `:1686` and `:2641` — `[`TODO-BETA-045-0.1.0`][kanban]` -> `[`TODO-ALPHA-052-0.1.0`][kanban]`, both
  occurrences. Reason and the re-ruling that licenses it: pass 1 deferred this to the catalog on a
  blast-radius argument Worker 3 **falsified** — `TODO-BETA-045-0.1.0` occurs in **spec-044 only**, so
  there are no un-editable copies to diverge from and the local fix costs zero divergence. On the
  corrected basis the target is established **mechanically, not by title match**: card number 045 is
  now occupied by `DONE-045-0.0.14` ("Sealed `get_queryset` visibility-boundary policy artifacts",
  cited in card 052's own DoD), so `TODO-BETA-045-0.1.0` names a card that cannot exist; and
  `TODO-ALPHA-052-0.1.0` is the **only** card at `0.1.0` on the board, is titled "Beta release
  (cleanup, verification, alpha -> beta)", and its "Files likely touched" (`README.md`,
  `docs/README.md`, `docs/GLOSSARY.md`, `docs/TREE.md`) plus its "doc status cross-check" note cover
  the chores spec-044 defers to it. **Residual uncertainty, stated rather than buried:** spec-044's
  phrase "the board's progress section" is not literally in card 052's definition of done, so the
  match is on subject and version rather than on every enumerated chore. `TODO-BETA-053-0.1.5` was
  **not** repointed — its blast radius is ten files including two source files, and Worker 3
  reproduced that measurement (catalog item 3).

Deliberately **not** changed in pass 2, each with its reason so the omission is a ruling: Decision 12's
body at `:1657` (P2-2); `## Current state` at `:663-668` (box 5); `## Goals` item 6 at `:726-729`
(new this pass, obligation-framed); `:113-115`'s R1-added contract sentence (recorded, above, with the
argument for leaving it); Decision 12's **heading**, whose slug carries eleven of the spec's 200 anchor
citations; the `TODO-BETA-053-0.1.5` cluster and the `strawberry.Schema` / `DjangoSchema` inexactness
(catalog items 3-5); and both files' relative link paths, which resolve from `docs/` today and are
R3's to re-relativize. The **rationale file** was audited a third time and again needs nothing: zero
hits of any of this pass's ten sweep patterns, its `WIP-ALPHA-044` at `:82` is correct as the
Revision-1 chronology, and its one citation of the spec's header names the moved "Revision history"
line rather than anything this pass touched.

**Status-line re-verification (`worker-1.md` `## Spec status-line re-verification`).** Read `:1-115`
again at the start of this pass — **paragraph by paragraph this time, which is the correction the
Medium buys.** The block now reads consistently end to end: `:3-5` "completed / owned", `:56-73`
"was / carried", `:74` "owned and applied", `:104-107` "carries … as `shipped (0.0.14)`", and
`:110-115`'s deliberative-layer pointer, which R3 will re-relativize. `:74` needed no edit in either
pass. Every `[spec-038]` / `[spec-041]` / `[spec-042]` / `[spec-043]` / `[rationale]` definition
resolves.

### For the `### Deferred work catalog` in `bld-044-final.md` — merged, six items

Pass 1 recorded four; Worker 3 verified all four, refined two, and added two. This is the merged
list, so the final gate reads **one** record rather than three. Item 3 has shrunk because half of it
was fixed in this pass.

1. **`docs/spec-050-…:390` and `docs/spec-051-…:556`** assert live `TODO(spec-044 Slice 3)` anchors
   "owned by the in-flight `0.0.14` cut". Zero such anchors exist in source or tests. Both sit under
   those specs' `## Architectural decisions` (`spec-050:258`, `spec-051:309`) — normative prose, not a
   dated snapshot — which is why they are drift. **Owner: each spec's author or a future cycle.**
   (R1's entry; Worker 3 confirmed the section attribution.)
2. **`docs/spec-050-…:155` and `docs/spec-051-…:215`** read "Card `WIP-ALPHA-044-0.0.14` is
   mid-flight and owns the `0.0.14` joint cut". **Read this as "probably drift", not as a coin flip** —
   Worker 3 verified the sharpening pass 1 could only pose as a question: both sentences sit in those
   specs' own `## Current state`, but **neither section carries the `A true description of the repo as
   this spec is authored:` lead-in** (both go straight to bullets), so under this cycle's governing
   test they do not self-date and therefore read as claims about now. Both specs are still in flight,
   which makes a refresh the likely answer. **Owner: each spec's author.**
3. **`TODO-BETA-053-0.1.5` — a tree-wide card-id reconciliation, deliberately not made locally.** The
   renumber moved that card to **`TODO-BETA-060-0.1.5` — "Fakeshop GraphQL schema activation"**
   (`KANBAN.md:939`; same version, same subject, and `053` now names `FieldSet` at `0.1.1`), with
   **lower confidence that it is still the natural host** for fakeshop opting into the debug extension,
   because its planning note assigns per-subsystem activation to the respective Layer-3 cards' Slice 4.
   Blast radius, measured by pass 1 and reproduced by Worker 3: **ten files** — `TODAY.md`, spec-044
   (`:2623`), six archived specs (`spec-030`, `032`, `033`, `037`, `041`, `042`), and two source/test
   files, `examples/fakeshop/apps/products/schema.py:228` and
   `examples/fakeshop/test_query/test_products_api.py`. Repointing spec-044's one occurrence alone
   would leave one file disagreeing with nine. **One owner, one sweep, or not at all.**
   **`TODO-BETA-045-0.1.0` has left this catalog** — Worker 3 showed it occurs in spec-044 only, so it
   carried no divergence cost, and pass 2 repointed it to `TODO-ALPHA-052-0.1.0` (see
   `### Spec changes made (Worker 1 only), pass 2`).
4. **`docs/spec-044-…:291-297` is inexact rather than false.** It names
   `strawberry.Schema(query=Query, config=strawberry_config(), extensions=[lambda: _optimizer])` as
   "the canonical shape `config/schema.py` demonstrates today"; that file (`:77-81`) builds
   `DjangoSchema(query=Query, mutation=Mutation, …)`, and `DjangoSchema` **is** a `strawberry.Schema`
   subclass (`django_strawberry_framework/schema.py:199`), so three of the four cited elements are
   exact and the class named is a base of the class used. The two nearby recipe snippets (`:326`,
   `:892`) are query-only consumer/cookbook examples, for which plain `strawberry.Schema` remains
   correct. Not fixed because the divergence comes from the mutation-atomicity card's shipping rather
   than spec-044's, and because deciding whether the cookbook recipe should now name `DjangoSchema`
   changes the spec's central migration story. **Owner: maintainer.**
5. **Item 4 has a second surface, and it is a standing doc rather than a spec parenthetical**
   (Worker 3's find, confirmed by me at the file): `examples/fakeshop/test_query/README.md:23` states
   that the project schema "constructs `strawberry.Schema(query=Query, mutation=Mutation,
   config=strawberry_config(), extensions=[lambda: _optimizer])`" — the same divergence from
   `config/schema.py:77`'s `DjangoSchema(...)`, in a file no residual item may write and whose
   audience is every worker who reads the live-tier README as required reading. **Whoever answers item
   4 should answer both surfaces in one pass**, or the spec and the README will disagree with each
   other as well as with the code. **Owner: maintainer.**
6. **`TODAY.md:384` attributes the router redesign to "the transport-security card `065`" while
   `docs/README.md:128` attributes it to `046`.** The 2026-07-30 renumber moved 065 -> 046, so
   `TODAY.md` carries the pre-renumber number. Nothing to do with spec-044's shipping. **Owner: the
   preserved spec-046 cycle's closeout or the renumber's.**

### Notes for Worker 3 (re-review)

- **The Medium's fix is two changes, not one**, and the second is the one worth checking: the
  duplicated enumeration is **gone**, not past-tensed, so `:74` is now the only place the cut's
  contents are listed. `grep` for `release-status doc moves` should return exactly one hit.
- **The class table is the pass's substantive addition.** Four sites, four frames, one corrected. The
  fourth row (`## Goals` item 6) is new and is the one most worth attacking, since a goals list could
  be argued either way; the frame check against the two archived siblings' `## Goals` is the evidence
  offered.
- **The `045` repoint reverses a pass-1 deferral on a basis your review supplied.** The mechanical leg
  is that number 045 is now `DONE-045-0.0.14`, cited in card 052's own DoD, so the old id cannot
  resolve. The soft leg — "the board's progress section" not appearing verbatim in card 052's DoD — is
  stated in the change record rather than smoothed over.
- **Two figures worth re-deriving rather than accepting:** the 43 = 20 / 14 / 9 population, and the
  **five** zero-context hunks (`git diff -U0`, not the delta route Low 3 retired — and note the count
  is five, not the three a draft of this artifact guessed before enumerating).

### Notes for Worker 1 (spec reconciliation)

Nothing carried forward inside the active spec: every falsehood either review found is now fixed or
carries a stated keep. The six catalog items above are for other files and are R3's and the
maintainer's, not a later R2 pass's.

### Baseline / concurrent-work note

`git status --short` is unchanged in shape across this pass, at seven entries (the six from pass 1
plus this artifact, which was already untracked). `docs/feedback.md` — a maintainer adversarial review
of **spec-046**, the preserved cycle's concurrent work — and the `to-many-search-optimizer-reproduction.md`
deletion were neither edited nor reverted, and no `git checkout` / `restore` / `stash` / `worktree`
ran at any point (`AGENTS.md` rule 34).

---

## Review (Worker 3, pass 2)

**Pass 2 isolated independently, and the isolation validated before it was used.** I rebuilt the
pass-1 spec from my own R1-end reconstruction plus the three pass-1 hunks I recorded last review; the
rebuild measures **185,542 bytes / 2,839 lines**, exactly pass 1's figure, which is what licenses the
comparison. `git diff --no-index -U0 <pass1> <current>` then yields **7 insertions / 7 deletions in
five zero-context hunks** — `@@ -58 +58 @@`, `@@ -67 +67 @@`, `@@ -70,3 +70,3 @@`, `@@ -1686 +1686 @@`,
`@@ -2641 +2641 @@` — and **no sixth region**. Pass 2's own `git diff -U0` enumeration is confirmed
figure for figure, including the corrected count of five rather than the three a draft guessed. No
`git stash` / `checkout` / `restore` / `worktree`; the spec and rationale were read-only to me.

### High:

None.

### Medium:

None. Pass 1's Medium is closed, and both halves of the fix verified below.

### Low:

#### The new sentence's "recorded **once**" is falsified by the paragraph twelve lines below it — and the grep used to support the claim was too narrow to see it

`:71-72` now reads "What the cut contained is recorded **once**, in the `Status:` line below." The
`Status:` line at `:74` does carry the enumeration — and so does the post-`Status:` slice enumeration
at `:85-90`, which **this pass deliberately kept** (box 4):

```docs/spec-044-debug_extension-0_0_14.md:85
and Slice 3 (**the joint `0.0.14` cut +
final card wrap** — the version quintet, the
GLOSSARY status flips for `041` / `042` / `043` / `044`, the
[`README.md`][readme] / [`docs/README.md`][docs-readme] / [`TODAY.md`][today]
release-status moves, and the `CHANGELOG.md` `0.0.14` section, …
```

So the cut's contents are recorded at least twice inside the same header block, and the second telling
is more complete than the `Status:` line's. The **edit is still right** — three tellings became two,
nothing load-bearing was lost, and the removed one was the tense-falsified one — but the new sentence
overstates what the removal achieved, in the spec rather than in the artifact, which is the durable
surface.

Why it survived the pass's own check: `### Validation run` tests the claim with
`release-status doc moves` → 1 hit. The surviving telling spells it **`release-status moves`**, without
"doc", so the pattern could not see it. That is the one recurring lesson in my memory file — grep the
**vocabulary**, not one spelling — applied here to a claim about counts (`the version quintet`
flattens to **five** sites: `:74`, `:83-90`, `:724`, `:1666`, `:2700`, four of them ruled keeps).

**Recommended change** (Worker 1's file): delete the word "once" — "What the cut contained is recorded
in the `Status:` line below" — or "…is recorded below rather than here". Two words, no anchor, no link,
no argument touched. **Equal-cost alternative:** record a rejection reason (e.g. that "once" is scoped
to the `**Version boundary**` paragraph's own neighbourhood), which closes the finding under the
acceptance gate just as well. No test expectation; nothing here is executable.

### DRY findings

- **Pass 1's DRY finding is discharged, and by the better of the two available fixes.** The duplicate
  telling was **deleted**, not past-tensed, so the header block no longer carries a second
  independently-rottable copy of the release facts. Verified mechanically rather than read: the
  paragraph is 17 lines before and after; it lost **no** reference-style link, **no** in-page anchor,
  and **no** card id (`[kanban]` ×3, `[glossary-djangographqlprotocolrouter]`,
  `[glossary-debug-toolbar-middleware]`, `[glossary-testclient]`, `[glossary-graphqltestcase]`,
  `[glossary-joint-version-cut]`, `[spec-041]`, `[spec-042]`, `[spec-043]`, `[spec-038]`, the
  Decision-12 in-page link, and `DONE-041/042/043-0.0.14` all still present); the only code span it
  lost is `` `shipped (0.0.14)` ``, which is the duplicated content itself. Every argument element
  survives — the three predecessors and their deferrals, the last-card-owns rule, the contrast with
  the siblings' Decision 10 / 10 / 12, and the `spec-038` lone-card mirror. A deletion is the easy fix
  to overreach with; this one did not overreach.
- **No new duplication.** Pass 2 adds one pointer sentence and rewrites two card ids; no fact is
  copied. The remaining multi-site telling of release state is the set of previously-ruled keeps, not
  new growth — which is exactly why the Low above is about a word and not about the edit.
- No abstraction, helper, or literal is introduced; nothing to challenge on existence grounds.

### Public-surface check

Confirmed mechanically again: `git diff -- django_strawberry_framework/__init__.py` produces no
output. `git status --short` carries the same seven entries pass 2 records, so no package source,
test, `examples/` file (including `test_query/README.md`, which the catalog names but must not be
edited by this item), `scripts/`, release-metadata, generated doc, other `docs/spec-*.md`, archived
spec, or preserved spec-046 artifact was touched.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Re-run, not carried over from pass 1.

- **Gates.** `check_spec_glossary.py --spec docs/spec-044-debug_extension-0_0_14.md` →
  `OK: 42 terms - all have glossary entries and at least one spec link.`, exit **0**.
  `check_trailing_commas.py --check` over the spec, the rationale, and this artifact → exit **0**.
- **The collapse did not orphan a link definition**, which is the specific failure shape a deletion of
  this kind causes. My own auditor, re-run on both files: spec 35 headings, **200 in-page anchor
  occurrences / 26 distinct targets / 0 broken**, **102 definitions / 0 unused / 0 undefined** except
  the standing `"sql"` code-span false positive; rationale 20 headings, 2 occurrences, 0 broken, 28
  definitions, 0 unused. Every non-URL definition in both files resolves to an existing file **and**
  to a real heading in it. Identical to pass 1's figures, which is the correct result for a pass that
  added and removed no definition — and the two card-id rewrites reuse the already-defined `[kanban]`,
  so neither orphaned nor added one.
- **Positional-citation sweep, whitespace-flattened over both files.** Reproduced exactly:
  `carries the version quintet` → **0**; `carried the cut` → 1 (the new text); `last non-Done` → 2 (the
  corrected header site and the deliberately-kept Decision 12 site); `TODO-BETA-045` → **0**;
  `TODO-ALPHA-052` → 2; `release-status doc moves` → 1. Zero hits of every pattern in the rationale
  file. Nothing cites a sentence pass 2 rewrote. The one gap this sweep has is the Low above:
  `release-status moves` (no "doc") also exists, at `:87`.
- **Version strings, statuses, card ids.** The header block now reads consistently end to end, which
  was the point: `:3-5` "completed / owned", `:56-72` "was … carried the cut", `:74` "owned and
  applied", `:104-107` "carries … as `shipped (0.0.14)`". The paragraph no longer asserts "is the last
  non-Done card" or "Slice 3 carries" — verified in the isolated diff, not inferred.
- **No obsolete "planned" / old-version wording in what the slice updated.** The four `## Current
  state` bullets remain, on the ruling pass 1 recorded and I re-derived last review; nothing new was
  added to that section. The `**Version boundary**` label is a house convention rather than something
  this edit invented — **18** spec files carry it (the artifact says "five"; the miscount runs in the
  conservative direction, since more siblings make the label more clearly a convention, so I am
  correcting the record here rather than filing it).
- **Rationale file untouched:** 43,859 bytes, byte-identical for the third consecutive pass (`wc -c`),
  and zero hits of any sweep pattern in it. R3's relative-path obligation is unchanged and not flagged.
- Script-rendered docs: none regenerated; no feeding docstring changed.

### The class sweep: each keep tested on its own stated ground

Three keeps and one correction from one claim is either careful or convenient, and only the grounds
distinguish them. I tested all four rows independently.

- **`:58` / `:67` / `:69-72` — header block, CORRECTED.** Right, and it is the row the governing test
  compels; verified in the diff.
- **`:1657` — `### Decision 12`, KEPT.** The stated ground is that a decision block records the ground
  on which the decision was taken. It holds, and it holds for a reason stronger than framing: the body
  argues *from* the `0.0.13` version line ("Leaving the version at `0.0.13` after `044` ships would
  strand four cards' worth of shipped surface"), so past-tensing the premise while `## Current state`
  still says "The version line reads `0.0.13`" would split one argument across two tenses. Kept
  correctly.
- **`:663-668` — `## Current state`, KEPT.** Box 5's ruling, re-derived last review (four-sibling
  lead-in byte-identical, 0 ticked boxes in each, bullets load-bearing as premises). Unchanged this
  pass.
- **`:726-729` — `## Goals` item 6, KEPT, and the fourth site is real.** Confirmed present and
  present-tense: "**The `0.0.14` release becomes real.** Slice 3 aligns the version quintet and flips
  the release-status wording for all four `0.0.14` cards". The offered ground — sibling `## Goals`
  ship in the same aspiration tense — checks out (`spec-042` "With the middleware wired, a developer
  … sees"; `spec-043` "A consumer … posts … gets back"), but those are *consumer-outcome* goals, not
  *process* goals about a slice, so on the offered evidence alone the analogy is inexact. **The ground
  holds on better evidence than was offered:** `docs/SPECS/spec-038-form_mutations-0_0_12.md`'s
  `## Goals` item 7 is the exact analogue — "**Complete the `0.0.12` cut.** This card is the lone
  `0.0.12` card, so Slice 5 …" — an archived, shipped spec preserving a lone-card version-cut goal in
  precisely this tense, and it is the spec `spec-044`'s Decision 12 explicitly mirrors. The keep is
  correct; it is now also precedented rather than argued.
- Sweep completeness: I ran my own flattened patterns over both files (`non-Done`, `That card`,
  `the version quintet`, `status flips for`, `all four `0.0.14` cards`, `the cut contained`) and found
  no fifth site of the claim. Four is the population.

### The `045` → `052` repoint (an edit beyond my findings)

Legitimate — my review supplied the basis by falsifying the blast-radius argument — but it is an edit
I had not reviewed, so I verified the target mechanically rather than by title match, as the pass
claims to have done:

- **The old id cannot resolve.** Card number 045 is `DONE-045-0.0.14` — "Sealed get_queryset
  visibility-boundary policy artifacts" (`KANBAN.md:99`) — and it is cited *inside card 052's own
  Definition of done* (`KANBAN.md:450`), so `TODO-BETA-045-0.1.0` names a card that cannot exist.
- **The new id is unique and correct.** A sweep of every card heading for a `0.1.0` version tag returns
  exactly **one** match: `### [TODO-ALPHA-052-0.1.0 - Beta release (cleanup, verification, alpha →
  beta)]` at `KANBAN.md:436`. Its DoD covers the chores spec-044 defers — the `0.1.0` version bump
  across the quintet, and "`README.md`, `docs/README.md`, `docs/GLOSSARY.md`, and `docs/TREE.md`
  cross-checked … 'shipped' / 'planned' status markers updated" — plus the parity audit.
- **The `BETA` → `ALPHA` prefix flip is documented, not inferred.** `KANBAN.md:14` states the rule and
  names this very card: "The two release cards themselves are tagged with the phase they usher in:
  `TODO-ALPHA-052-0.1.0` is the alpha → beta cut-over". Independent confirmation stronger than the
  subject match the artifact rested on.
- **The stated residual uncertainty is real and correctly disclosed:** card 052's DoD carries no
  "board's progress section" item, so that one deferred chore matches on subject and version rather
  than verbatim. Disclosed rather than smoothed.
- **`TODO-BETA-053-0.1.5` correctly left alone** at `:2623`, still reading "the fakeshop-activation
  beta card ([`TODO-BETA-053-0.1.5`][kanban]) is the natural host". I re-reproduced the asymmetry that
  licenses the split treatment: `TODO-BETA-045-0.1.0` now occurs **0** times tree-wide, while
  `TODO-BETA-053-0.1.5` still spans **ten** files including two source/test files. Both sites read
  coherently in context (`:1686` inside Decision 12's non-milestone-cut clause, `:2641` in the
  out-of-scope table).

### The two arithmetic corrections

- **Box 23, corrected in place and re-measured against my own count:** 43 boxes, 0 ticked, **20**
  `## Slice checklist` / **14** `## Helper-reuse obligations (DRY)` / **9** `## Definition of done`,
  **26** top-level — and it now says which scope the sibling table's `5 / 22 / 24 / 24` column uses,
  which is the mechanism that caused the miscount. Matches my measurement exactly.
- **Box 30 and the delta claim.** Box 30 now reads `185,518 → 185,542 → 185,496`; I re-measured all
  three (the first two from the reconstructions, the third with `wc -c`) and they hold, as does
  rationale `43,859`. Pass 1's "exactly the sum" sentence is corrected in this entry rather than in the
  prior entry's body, which is the right placement under `ARTIFACT.md` `## Re-pass sections`, and the
  rewritten sentence states the delta as corroboration rather than proof. Pass 2's own claim — `+7 / +7`
  agreeing with the five enumerated hunks — I reproduced: `git diff --numstat` reads 83 / 417 against
  76 / 410, and 1+1+3+1+1 = 7. The adopted method (`git diff -U0`) is sound and cheaper than my
  reconstruction; that it caught a wrong guess in its own draft bullet is the strongest evidence for it.

### The counterweight, recorded honestly

`:113-115`'s R1-added "states only what is currently true" is recorded with its provenance verified
independently, and the entry states the *unfavourable* consequence first — leg (a) of box 5's argument
"**is weaker than pass 1 stated**" — before arguing the keep survives on the other legs. It does not
soften it into a non-issue, and it draws the right conclusion from it (that the sentence is what made
the unruled header paragraph worse than untidy rather than merely stale). The decision to leave
`:113-115` alone is reasoned rather than defaulted. Nothing further owed.

### Deferred work catalog — six items, re-verified

- **Item 1** — `spec-050:390` / `spec-051:556` under `## Architectural decisions`, zero matching
  anchors in source. Still real; unchanged.
- **Item 2 — not blurred.** It keeps both halves of the evidence (the sentences sit in those specs' own
  `## Current state`; **neither section carries the dating lead-in**, which I verified again at
  `spec-050:155` and `spec-051:215`) and renders the verdict as "probably drift", with the in-flight
  status as the reason a refresh is likely and the owner named as each spec's author. That is my
  sharpening, not an escalation of it into an asserted defect. Correct.
- **Item 3** — correctly shrunk: `045` removed with the reason (my falsification of its blast radius,
  now fixed in-spec), `053` retained with the ten-file measurement, the `060` target, and the stated
  lower confidence about it still being the natural host. Re-reproduced this pass.
- **Items 4 and 5** — both still exact. Item 5's line reference checks out: the sentence is at
  `examples/fakeshop/test_query/README.md:23`, and it does name `strawberry.Schema(...)` where
  `config/schema.py:77` builds `DjangoSchema(...)`. The instruction to answer both surfaces in one pass
  survived the merge.
- **Item 6** — `TODAY.md:384` (`065`) vs `docs/README.md:128` (`046`), owner named. Unchanged.

### What looks solid

- **The fix chose deletion over past-tensing and lost nothing** — the strongest thing in this pass, and
  the thing most likely to have gone wrong. Link, anchor, card-id, and argument inventories are
  identical before and after.
- **The class sweep is the right response to a "name this site too" finding.** It converted one
  reviewer request into a four-site population with a stated frame and owner per site, and it found a
  site neither the review nor pass 1 had named. Three of four keeps rest on grounds that survive
  independent testing; the fourth (`## Goals`) survives on better evidence than it offered.
- **The failure was named plainly rather than minimised** — "a declared range is not an audited range
  unless every paragraph in it is named" is the correct diagnosis of pass 1's Medium, and it is the
  sentence a future pass should carry.
- **Low 3's lesson was applied inside the same pass that recorded it**, and caught a wrong count in its
  own draft. A lesson that pays for itself immediately is worth more than one filed for later.
- The `045` repoint reverses a prior deferral on evidence, verifies the target mechanically, and states
  its residual uncertainty. That is the right shape for an edit outside the review's findings.

### Temp test verification

- `docs/builder/temp-tests/044-r2/link_audit.py` — my own auditor from pass 1, re-run unchanged on
  both files. Disposition: kept as gitignored scratch, not promoted (it audits a document and pins no
  package behavior). The pass-1 reconstruction inputs live outside the repo in the session scratchpad.
- No `pytest` run: nothing in the diff is executable, so a run would report only the tree at large —
  stated rather than performed. No `--cov*` flag in any pass of this item.

### Failability proofs

Not applicable, arithmetically: the pass-2 diff is five one-to-three-line markdown regions with no
executable line, so `BUILD.md` `### What needs a proof, and what does not` scopes the obligation to
zero and the mandatory re-run floor is empty by that scope. No fail-open shape can exist where there
is no expression. The build report's `None; this pass introduced no new boundary.` is accurate.

### Hot-path budget

Not applicable; the plan declares hot-path `none` for the cycle and no package source changed —
confirmed by the isolated diff. Floor verification likewise not applicable: the plan's scope is
`none`, no Django / Strawberry / channels seam is touched, and no version-dependent reasoning was
needed or performed.

### Notes for Worker 1 (spec reconciliation)

- **Escalated (Low):** `:71-72`'s "recorded **once**". The remedy is deleting one word, and Worker 1's
  final verification is the pass that owns spec edits, so this needs no builder loop and no third
  review pass. Two resolution paths, either of which closes it: (a) drop "once" (or "…is recorded below
  rather than here"), recording it under `### Spec changes made (Worker 1 only)`; (b) record a rejection
  reason — that "once" is scoped to the `**Version boundary**` paragraph rather than to the whole
  header block. I would take (a): the sentence's whole purpose is to be the DRY pointer, and a pointer
  that overstates is the one sentence in the block a reader will check.
- **Method note worth carrying into R3, not a finding:** the `release-status doc moves` grep returning
  1 while `release-status moves` at `:87` survives is the same near-spelling trap in miniature. R3
  rewrites ~130 link definitions across three files; a sweep pattern that matches the *long* form of a
  path or label will miss its short form. Prefer the shortest distinctive token.
- No other spec reconciliation is owed. Everything pass 1's review raised is either fixed and verified
  or kept with a ground I tested.

### Review outcome

**`review-accepted`** — no High, no Medium, one Low, escalated above with its remedy and its
equal-cost alternative.

Pass 1's Medium is closed by the better of the two fixes I offered, verified in both halves: the
paragraph no longer claims "is the last non-Done card" or "Slice 3 carries", and the collapse cost no
link, anchor, card id, or argument. Low 1 is closed by a class sweep that outgrew the finding — four
sites, one corrected, three kept on three distinct grounds, each of which I tested and one of which I
could strengthen. Lows 2 and 3 are corrected to the figures I measured. The `045` → `052` repoint,
though outside my findings, verifies mechanically against the live board including the documented
`BETA` → `ALPHA` re-milestoning, and the `053` cluster is correctly still deferred. All three gates
re-run green with figures identical to the recorded ones, and pass 2's five-hunk / 7-for-7 isolation
reproduces exactly against an independently rebuilt pass-1 state.

Under Deviation 3 this hands to **Worker 1 for final verification**, which is also the pass that closes
the escalated Low. `review-accepted` rather than `revision-needed` because the finding is one word in
a sentence whose substance is correct, the fixer is the next worker in the chain either way, and a
full re-loop would buy no correctness.

## Final verification (Worker 1)

The accepting pass, and the pass that closes Worker 3's escalated Low. Two Worker 1 passes and two
Worker 3 passes have run; this pass has no in-context memory of any of them, so the artifact and the
working-tree diff are the contract. **Nothing here was accepted on prose.** `worker-1.md`
`### Verifying relocation / promotion claims` gives this pass an explicit delta — run the proof
yourself rather than reading Worker 3's acceptance as discharge — and R2's central pass-2 edit *is* a
deletion-with-preservation claim, so its no-loss inventory was re-derived from the tree below. Where
a re-derivation disagrees with a recorded figure the disagreement is stated rather than reconciled
silently.

### The escalated Low — resolved, and the reason it survived R2's own check

`:71-72` read "What the cut contained is recorded **once**, in the `Status:` line below." False as
written: the post-`Status:` slice enumeration at `:85-90` — which box 4 deliberately kept — records
the cut's contents again and **more fully** than `:74` does. Worker 3 offered deleting the word or
recording a scoping rejection. **Decided: fixed, and by rewording rather than by deleting one word.**
The sentence now reads "What the cut contained is recorded **below rather than here**."

Why that form and not "recorded in the `Status:` line below" (the literal one-word deletion): the
cut's contents are recorded in **two** places below, and the fuller of the two is the slice
enumeration, not the `Status:` line — so a pointer naming only `Status:` names the less complete
telling as if it were the record. "Below rather than here" carries **zero** positional claim that can
rot while stating exactly what the paragraph is doing (delegating rather than restating), which is
the sentence's whole purpose. The scoping-rejection path was refused for the reason Worker 3 gave and
I agree with: the one sentence in that block a reader will check is the pointer, and a pointer that
overstates is worse than no pointer.

**Why it survived R2's check, stated because the lesson generalizes** (Worker 3 flagged it forward
for R3 and it is worth more than the fix): pass 2's validation run tested the claim with
`release-status doc moves` -> 1 hit, while the surviving telling at `:88` spells it
**`release-status moves`**, without "doc". The pattern could not see it. **A verification grep that
picks a long phrase proves less than one that picks the shortest distinctive token** — the long form
is a *sample* of the claim's vocabulary, and a sample cannot establish a count. Re-run here with the
shortest tokens, the release-state class is **7** flattened sites in the spec, not the five Worker 3's
Low estimated: `version quintet` at `:74` (the canonical `Status:` telling), `:85` (box 4's kept slice
enumeration), `:468` (`## Slice checklist`), `:726` (`## Goals` item 6), `:1668` (`### Decision 12`),
`:1712` (`## Implementation plan`'s doc table), `:2702` (`## Definition of done`). Every one of the six
non-canonical sites is an obligation list, a decision block, a self-dated snapshot, or the kept
enumeration — i.e. already covered by a recorded class ruling (boxes 4, 5, 6, 22, and pass 2's
four-row table). **No unruled site of the class remains**, and none is a claim about now inside the
header block. Zero hits of any pattern in the rationale file.

### One further site of the *other* class, previously unnamed — ruled KEEP

The same too-long-pattern flaw hid a site of the `planned`-status class as well, and this is the
third instance of the lesson in one cycle. Box 26's sweep pattern was `planned for 0.0.14`; the site
spells it **`planned contract`**, so no box names it:

```docs/spec-044-debug_extension-0_0_14.md:121
- [Response-extensions debug middleware][glossary-response-extensions-debug-middleware]
  - the subject. The glossary already pins the planned contract: ... Slice 2
  updates the entry body to the implemented contract; Slice 3 flips the
  status to `shipped (0.0.14)`.
```

`:122-127`, in `## Key glossary references` — the section immediately below the header block, and
therefore **outside** the `:1-115` range pass 1 declared, so this is not a second scope breach.
Ruled **KEEP**, on box 6's stated class ground rather than a new one: the clause is the *starting
condition the obligation acts on*, which is what makes the obligation legible, and it reads that way
on the plainest reading — "planned **contract**" modifies the contract, not the entry's status
marker, and the very next clause draws the planned-contract / implemented-contract contrast that is
the obligation's point. The corrected near-twin at `:104-107` is distinguished exactly as box 3
distinguished it: **it sits inside the header block**, which the governing test puts on the corrected
side. Correcting this one while keeping the eight structurally identical future-tense clauses in
`## Slice checklist` (`:447`, `:451`, `:496`, `:511`), `## Implementation plan` (`:1708`), and
`## Doc updates` (`:2487`, `:2520`) is the inconsistency, not the fix; and `BUILD.md`'s tie-break for
an unclear carve-out is that it stays. Population of the `planned` class, measured with the short
token: 12 hits, of which 3 are unrelated technical uses (`unplanned lazy loads` `:216`, the
optimizer's `planned` shapes `:717` / `:2230`), 2 are box 5's `## Current state` bullets, 6 are
obligation-list keeps, and this one. **Class closed at 12 sites with a ruling on each.**

### The relocation proof — the no-loss inventory, re-derived

R2's pass-2 edit replaced a three-line enumeration with a pointer. That is a deletion-with-preservation
claim and it is the one claim an author and a reviewer can both talk themselves into, so it was
re-derived rather than read. `git show HEAD:docs/spec-044-debug_extension-0_0_14.md` into a scratch
path **outside** the repo (never `git stash` / `checkout` / `restore` / `worktree` — the maintainer
runs concurrent sessions against this tree); HEAD measures **205,905** bytes / 3,173 lines. R1 did not
touch this paragraph, so HEAD `:56-72` **is** the pre-pass-2 state and needs no reconstruction to
compare against — a cheaper route to the same isolation than either prior pass used.

`diff -u` over the 17-line paragraph, before against after: **three changed lines and nothing else**
(`is` -> `was`, `That card is` -> `was`, and the enumeration-for-pointer replacement). Inventory of
every citable element, extracted mechanically and compared as multisets:

| Element | Before | After | Verdict |
|---|---|---|---|
| Reference-style `][ref]` uses | 13 across 10 distinct (`[kanban]` x3) | identical | no loss |
| In-page anchors | 1 (Decision 12's slug) | identical | no loss |
| Card ids | `DONE-041/042/043-0.0.14` | identical | no loss |
| Code spans | 13 | 12 | see below |
| Paragraph length | 17 lines | 17 lines | unchanged |

**One refinement to Worker 3's inventory, in the direction of precision rather than of a defect.**
Its `### DRY findings` records "the only code span it lost is `` `shipped (0.0.14)` ``". Two spans
left: `` `shipped (0.0.14)` `` **and** one of the paragraph's three `` `0.0.14` `` spans (the one in
"all four `0.0.14` cards"), with `` `Status:` `` gained. Both losses sit inside the removed
enumeration clause and neither is load-bearing — `` `0.0.14` `` still appears twice in the paragraph
and **56** times in the spec — so the verdict is unchanged and the claim's substance holds. Every argument
element survives, checked one by one against the before-text: the three predecessors and their
deferrals, the last-card-owns rule, "that card was this one", the contrast with the three siblings'
Decision 10 / 10 / 12, and the `spec-038` lone-card mirror. **No link definition was orphaned** —
the specific failure shape such a deletion causes — confirmed by the ref/def gate below, which
reports 102 definitions and **0 unused**, unchanged across all four passes.

### Step 3 — the checklist audit (the central duty)

**No box is over-ticked and none is silently un-ticked.** All 33 plan boxes plus the four pass-2
boxes read `- [x]`, none is deferred, so nothing needed ticking or un-ticking and no `- [ ]` deferral
reason is owed for the artifact's own checklist. Each box was judged against **what its own text
claims**, since most are audit obligations discharged by verification rather than by a diff hunk.
Two boxes' figures were extended in place under the audit discipline `BUILD.md`
`### Dispatched findings checklist` assigns to Worker 1, each marked inline:

- **Box 30** — the byte chain now carries this pass's measurement: **185,518 -> 185,542 -> 185,496 ->
  185,485**. All four re-measured with `wc -c` in this pass (the first two from the HEAD scratch copy
  plus the recorded pass deltas, the last two directly). Rationale **43,859** at every point.
- **Box 33** — its "Four" is superseded. The authoritative catalog is pass 2's **six**-item merged
  list; the box now says so, because a final gate reading the box's count would drop two items.

The corrected figures rather than the narrative about them, re-measured independently:

- **Box 23's population.** `grep -cE '^\s*- \[[ x]\]'` -> **43**; `- [x]` -> **0**; top-level
  `^- \[[ x]\]` -> **26**; per section, `## Slice checklist` (`:340`-`:528`) **20**,
  `## Helper-reuse obligations (DRY)` (`:1721`-`:1965`) **14**, `## Definition of done` (`:2645`-end)
  **9**. Matches the corrected box exactly. The sibling table's `5 / 22 / 24 / 24` column is
  top-level-only, and all four siblings measure **0** ticked — re-verified in this pass, as was the
  byte-identical `A true description of the repo as this spec is authored:` lead-in in all five files.
- **The delta arithmetic.** Confirmed retired rather than repaired: `git diff --numstat` still reads
  **83 / 417** after this pass's edit, because the edited line was already inside a pass-2 insertion.
  A third demonstration that delta arithmetic is not an isolation method. `git diff -U0` reports **34**
  zero-context hunks against HEAD before and after, and this pass's change is confined to the
  existing `@@ -70,3 +70,3 @@` region — verified by reading the hunk, not inferred from the count.
- **Boxes 8, 9, 10 (the sweep).** 0 hits under `django_strawberry_framework` / `tests` / `examples` /
  `scripts`; five spec-044-internal sites at **`:427`, `:430`, `:452`, `:576`, `:578`**, matching box
  9's labels line for line, including its correction of R1's `:453` mislabel.
- **Boxes 11-15, 16-22 (the fourteen rows).** Re-checked at the sites whose failure would matter most
  and whose assertion is cheapest to make without looking: `docs/GLOSSARY.md` `:20` package version,
  `:179` this card's `shipped (0.0.14)` plus `:97` / `:107` / `:197` for the other three and
  `:88` / `:177` for the companions, `:424` / `:1522` the both-directions cross-references, `:907`'s
  applied-cut wording; `docs/TREE.md` `:218` / `:332` / `:467` / `:679` real docstring-derived rows and
  **0** `TODO-ALPHA-044`; `examples/fakeshop/config/schema.py:77-81` building `DjangoSchema(...,
  extensions=[lambda: _optimizer])` with no falsified analogue sentence; `GOAL.md:513`;
  `README.md:62`; `docs/README.md:97` / `:132`; `TODAY.md:387`; `CHANGELOG.md:19`; the quintet at
  `pyproject.toml:4`, `__init__.py:41`, `tests/base/test_init.py`, GLOSSARY `:20`, `uv.lock`;
  `extensions/debug.py::DjangoDebugExtension` at `:371` with `on_operation` `:419` /
  `get_results` `:460`; `pyproject.toml:35` and `uv.lock:577` at `>=0.316.0` with three workflow
  matrix nodes pinning `0.316.0` (`:56`, `:57`, `:73`, reason comment at `:51`). **No drift in any
  row.** Box 22's disposition of DoD row 9 (a process row the shipped cycle discharged, which
  `AGENTS.md` rule 15 forbids re-proving) is right.
- **Box 32 re-tested rather than accepted**, since "nothing for the builder to do" is the convenient
  conclusion: a staging-language sweep (`planned`, `not yet`, `future work`, `no direct Strawberry
  analogue`, `coming soon`) over `django_strawberry_framework/extensions/` and
  `examples/fakeshop/config/schema.py` returns **zero**. The finding stands: no Worker 2 dispatch was
  owed, and this audit does not overturn it.
- **Box 25.** The rationale is **43,859** bytes, byte-identical for the fourth consecutive pass, its
  one `WIP-ALPHA-044` still the Revision-1 chronology line at `:82`, and zero hits of any of this
  pass's sweep patterns in it. Untouched, confirmed.

**The spec's own 43 checkboxes stay `- [ ]`**, which is a ruling and not a silence; the deferral
reason is recorded under `### Spec changes made (Worker 1 only)` below.

### The class rulings, confirmed on the ground each actually rests on

Not re-litigated — checked that each is recorded with the ground that holds:

- **`:58` / `:67` / `:69-72` header block — CORRECTED.** The row the governing test compels. Verified
  in the isolated diff.
- **`:1657` `### Decision 12` — KEPT.** The artifact records Worker 3's stronger ground and not merely
  the framing one: the body argues *from* the `0.0.13` version line, so past-tensing the premise while
  `## Current state` still says "The version line reads `0.0.13`" would split one argument across two
  tenses. Confirmed at `:1656-1658` and `:663-668`.
- **`:663-668` `## Current state` — KEPT.** Self-dated snapshot; the lead-in at `:565` is byte-identical
  to all four archived siblings' and each ships 0 ticked boxes. Both legs re-measured this pass.
- **`:726-729` `## Goals` item 6 — KEPT, on the replaced ground.** Confirmed that the artifact now
  rests it on `docs/SPECS/spec-038-form_mutations-0_0_12.md`'s `## Goals` item 7 — verified at
  **`:608`**: "**Complete the `0.0.12` cut.** This card is the lone `0.0.12` card, so Slice 5 owns the
  version-file alignment" — the archived lone-card-cut shape `### Decision 12` explicitly mirrors, and
  not on spec-042/043's consumer-outcome goals, which were the wrong comparator. The ground that holds
  is the one on the page.
- **The `045` -> `052` repoint.** Re-verified mechanically, not by title: `TODO-BETA-045-0.1.0` now
  occurs **0** times tree-wide outside this cycle's artifacts; number 045 is `DONE-045-0.0.14` and is
  cited inside card 052's own DoD, so the old id cannot resolve; `TODO-ALPHA-052-0.1.0` is the unique
  `0.1.0` card and the `BETA` -> `ALPHA` flip is documented at `KANBAN.md:14`. Both rewritten sites
  read coherently (`:1686`, `:2641`). Its **residual uncertainty is real and correctly still
  disclosed** — "the board's progress section" is not a verbatim item of card 052's DoD — and stays
  disclosed. `TODO-BETA-053-0.1.5` correctly still refused at `:2623`: blast radius re-reproduced at
  **ten files**, two of them source/test (`examples/fakeshop/apps/products/schema.py`,
  `examples/fakeshop/test_query/test_products_api.py`).
- **The `:113-115` counterweight** is recorded with the unfavourable clause first ("**is weaker than
  pass 1 stated**") before the keep is argued. Left exactly that way.
- **The `**Version boundary**` label count.** Worker 3's correction confirmed: **18** spec files carry
  it, not five. Precisely: 18 files including spec-044 itself, so **17** siblings. Pass 2's "five" sits
  in a prior build report's body, which `ARTIFACT.md` `## Re-pass sections` forbids me to edit; the
  correction stands here and in Worker 3's section.

### Step 4 — R2 against R1

Read `docs/builder/bld-044-r1-rationale_move.md` in full (`final-accepted`, 701 lines). No new
duplication and no inconsistent shape:

- **Section shape is identical**, deliberately: both items ran the Deviation-3 chain and both carry
  `## Build report (Worker 1, pass 2 — custodian apply)` at top level, a findings-one-by-one block,
  `### Spec changes made (Worker 1 only), pass 2`, and `### Dispatched findings checklist — audit of
  this pass`. Neither edits a prior entry's body; both publish a prior-entry correction in the later
  section instead. Same convention, applied twice.
- **The deferred catalog is one record, not three.** R1's artifact carries one item and R2's merged
  list carries it as item 1 with attribution, plus five more. Box 33 now says the merged six-item list
  is authoritative, so the final gate cannot double-count or drop.
- **Method evolved rather than diverged.** R1 isolated by reconstruction; R2 pass 2 adopted
  `git diff -U0` and recorded *why* (adjacency cannot shift a zero-context hunk). This pass used a
  third and cheaper route where it was available — HEAD is itself the pre-pass-2 state for that
  paragraph — and all three agree.
- **The escalated Low is itself a duplication finding**, so step 4 is live rather than formal here:
  three tellings of the cut's contents became two, and the fix removed the tense-falsified one. My
  edit adds no fact and removes a positional claim, so it introduces nothing new to rot. The two
  remaining tellings are `:74` (canonical) and `:85-90` (box 4's ruled keep).
- One inherited-lesson consistency check: R1's final verification recorded that a **line-oriented**
  citation sweep is blind to a citation broken across a line wrap. R2 applied it (whitespace-flattened
  sweeps in both passes). The failure this pass closed is the *sibling* gap — flattened but
  over-specific — which is worth carrying as a pair.

### Step 5 — focused tests: the reasoning, not a run

**Nothing R2 touched is executable**, so there is no focused scope to run. The whole diff is one
markdown file; a `pytest` invocation would report only whether the tree at large is green, a property
this item cannot affect and the final gate owns. Recording the reasoning is the honest discharge, and
running `pytest` for form would be worse than not running it. No `--cov*` flag in this or any pass of
this item (`BUILD.md` `## Coverage is the maintainer's gate, not a worker's tool`). No `ruff` run: no
`.py` file was touched, in any pass.

### Step 6 — the staged-anchor sweep

`grep -rEn 'TODO\(spec-044|TODO-(ALPHA|BETA|STABLE)-044' .`, with `KANBAN.md` / `KANBAN.html` /
`BACKLOG.md` excluded (there `TODO-<MILESTONE>-<NNN>` legitimately names a board card).

**Zero anchors in package source or tests: reproduced a third time, independently.** Card 044 shipped,
so that is the required result and this cycle owes no anchor removal. Not re-litigated. The tree-wide
survivors are exactly the classes box 10 names, by file: spec-044 itself **5** (the ruled keeps),
`docs/SPECS/spec-041/042/043` **17** plus two archived `-terms.csv` **2** (historical record),
`docs/spec-050` **1** / `docs/spec-051` **1** (catalog item 1), and this cycle's own
`docs/builder/` artifacts **20** (per-cycle scratchpads). Nothing owed.

### Failability and fail-open checks

**Confirmed from the diff rather than assumed.** R2 introduced no boundary, guard, gate, or rejection
path: **this item's** diff is one tracked markdown file (`docs/spec-044-…md`) plus untracked cycle
artifacts, and it contains no `.py` file and no executable line — all 34 zero-context hunks are prose,
a pointer line, and two card-id spans. (The seven package-source / test files that went dirty mid-pass
are a concurrent session's and are excluded on the evidence in
`### Baseline / concurrent-work note`, not on assumption.) `BUILD.md`
`### What needs a proof, and what does not` scopes the obligation to boundaries, so **no failability
proof is owed** and the mandatory re-run floor is arithmetically zero rather than a chosen subset.
Read for the catalogued **fail-open shapes** as well (clamp, `getattr` default, `or` fallback, bare
`except`, truthiness on a value that can be absent, any default reached because the input was
incoherent): none can exist, there being no expression in the diff to carry one. Both build reports'
`None; this pass introduced no new boundary.` is accurate.

### The verification gates, re-run in this pass — before and after my edit

- `uv run python scripts/check_spec_glossary.py --spec docs/spec-044-debug_extension-0_0_14.md` ->
  `OK: 42 terms - all have glossary entries and at least one spec link.`, **exit 0**, both times.
  Checked in the right order: the reworded clause carries no `][glossary-…]` use and no
  `](…GLOSSARY.md#…)` link, so no term could lose its only spec link.
- **In-page anchors and ref/def symmetry, both files, my own auditor** (fences stripped line by line;
  GitHub slugs — backticks stripped, punctuation dropped, `_` **kept**, **each** space to one hyphen,
  duplicates suffixed). Spec: 35 headings, **200 anchor occurrences across 26 distinct targets, 0
  broken**; **305 `][ref]` occurrences across 103 distinct ref-ids against 102 definitions, 0
  unused**, one "undefined" hit `"sql"` — the `res.extensions["debug"]["sql"]` code span, the standing
  false positive of the `][…]` probe every prior pass recorded. That reconciles the prior passes'
  recorded "103 uses" exactly as 200-vs-26 reconciles for anchors: **103 is distinct ref-ids** (102
  defined plus the false positive), 305 is occurrences. Rationale: 20 headings, 2 occurrences, 0
  broken; 76 occurrences across 28 distinct ref-ids / 28 definitions, 0 undefined, 0 unused. **Every non-URL definition in both files resolves to a file that exists and to
  a real heading in it.** Figures identical before and after my edit and identical to all three prior
  passes' — the correct result for a pass that added and removed no link, anchor, or heading.
- `uv run python scripts/check_trailing_commas.py --check docs/spec-044-debug_extension-0_0_14.md
  docs/spec-044-debug_extension-0_0_14-rationale.md docs/builder/bld-044-r2-doc_completion.md` ->
  **exit 0**. Explicit paths only; run pathless it rewrites unrelated `docs/` scratch files.
- **Byte and line counts.** Spec **185,496 -> 185,485** (**-11**), lines **2,839 -> 2,839** — the
  reworded sentence occupies the same two wrapped lines. Rationale **43,859**, untouched. HEAD is
  **205,905**, so the spec is **20,420 bytes** below it and the R1 move's purpose is intact.
- `git status --short` -> the seven entries pass 2 records at the **start** of this pass, and
  **fourteen** at the end: seven package-source / test files went dirty mid-pass under a concurrent
  session. This pass wrote no `.py` file; see `### Baseline / concurrent-work note` for the
  attribution evidence and the handling.

### Deferred work catalog — the six items, confirmed and located

Each verified at the file, not accepted from the record. All six are real and belong to
`bld-044-final.md`'s `### Deferred work catalog`, which this pass does not author. Two location
corrections, so the maintainer's sweep lands on the sentence rather than near it:

1. **Confirmed.** `docs/spec-050-…:390` ("the version-quintet sites currently carry `TODO(spec-044
   Slice 3)`") and `docs/spec-051-…:556`, both under those specs' `## Architectural decisions`; zero
   such anchors survive in source or tests. Drift. Owner: each spec's author.
2. **Confirmed, and its two-sided evidence is intact and must stay so — it is a question, not an
   asserted defect.** Both sentences do sit in those specs' own `## Current state`, and **neither
   section carries a dating lead-in** — verified this pass: `docs/spec-050-…:155` and
   `docs/spec-051-…:215` are the section *headings* and both go straight to bullets. **Location
   correction:** the sentences themselves are at **`docs/spec-050-…:173`** and
   **`docs/spec-051-…:235`**; the merged item's `:155` / `:215` are the heading lines, 18-20 lines
   above. Both specs are in flight, so "probably drift, owner = each spec's author" is the right
   rendering.
3. **Confirmed**, correctly shrunk to `TODO-BETA-053-0.1.5` alone, ten-file blast radius reproduced
   above, `060` target and the stated lower confidence about it still being the natural host intact.
4. **Confirmed exactly as characterised.** `:291-297` names `strawberry.Schema(query=Query,
   config=strawberry_config(), extensions=[lambda: _optimizer])` as the shape `config/schema.py`
   "demonstrates today"; that file (`:77-81`) builds `DjangoSchema(query=Query, mutation=Mutation,
   …)`, and `DjangoSchema` **is** a `strawberry.Schema` subclass
   (`django_strawberry_framework/schema.py:199`). Inexact, not false. Owner: maintainer.
5. **Confirmed at the file.** `examples/fakeshop/test_query/README.md:23` states the project schema
   "constructs `strawberry.Schema(query=Query, mutation=Mutation, config=strawberry_config(),
   extensions=[lambda: _optimizer])`" — the same divergence, in a standing doc no residual item may
   write and which every Worker 3 reads as required reading. Answer both surfaces in one pass.
6. **Confirmed.** `TODAY.md:384` says "the transport-security card `065`"; `docs/README.md:128` says
   `046`. The 2026-07-30 renumber moved 065 -> 046, so `TODAY.md` carries the pre-renumber number.
   Owner: the preserved spec-046 cycle's closeout or the renumber's.

**One addition from this pass's own audit**, for the same catalog:

7. **`docs/spec-050-…:390` and `docs/spec-051-…:556` are not the whole of those two files' spec-044
   staleness** — item 1 and item 2 together are, and they are **four** sentences across two files
   whose *authors are the same two people*. Recorded so the maintainer routes them as one job per
   file rather than four errands: `spec-050` owes `:173` and `:390`; `spec-051` owes `:235` and
   `:556`. No new drift claimed; this is a routing observation about items 1 and 2.

### Summary

R2 finished spec-044's documentation and this pass accepted it after closing the one escalated Low.
What the item delivered: the opener realigned to shipped tense on the archived siblings' form
(`Built for `0.0.14` (card `DONE-044-0.0.14`)`), the header block's GLOSSARY-status claim and the
`**Version boundary**` paragraph corrected, the criterion-7 premise dated, the two dead
`TODO-BETA-045-0.1.0` pointers repointed to `TODO-ALPHA-052-0.1.0`, and — the substantive product —
a **ruled** answer for every stale-reading sentence the release created, one corrected class and
three keep classes, each with a stated ground rather than a silence. The fourteen `## Doc updates` /
`## Definition of done` rows all landed in shipped tense, so no Worker 2 dispatch was owed; that
finding survives this audit. The spec is **185,485** bytes against **205,905** at HEAD; the rationale
is untouched at **43,859**; all four mechanical gates pass in this pass's own run with figures
identical to every prior pass's.

Three things this pass adds to the record rather than inherits. **First**, the escalated Low's lesson
generalizes past its own fix: the release-state class is **7** sites by shortest-token measure (not
five), and a *fifth* site of the `planned` class exists at `:122-127` that no box named, because both
sweeps chose a long phrase. Both are now ruled, and the pair — R1's "line-oriented sweeps are blind
to a line wrap" plus R2's "flattened but over-specific" — is the transferable lesson. **Second**, the
no-loss inventory is confirmed with one refinement: **two** code spans left the collapsed paragraph,
not one, both inside the removed enumeration and neither load-bearing. **Third**, delta arithmetic
failed a third time — `git diff --numstat` is unchanged at 83 / 417 after an edit that changed two
lines — which is the strongest available argument for the `git diff -U0` method pass 2 adopted.

### Spec changes made (Worker 1 only)

One edit, with the line range as numbered **before** the edit and a one-line reason.

- `docs/spec-044-debug_extension-0_0_14.md:71-72` — "What the cut contained is recorded **once**, in
  the `Status:` line below." -> "What the cut contained is recorded **below rather than here**."
  Reason: "once" was false — the post-`Status:` slice enumeration at `:85-90`, deliberately kept by
  box 4, records the cut's contents again and more fully. Closes Worker 3's escalated Low. No anchor,
  no link definition, no glossary link, and no argument touched; -11 bytes, line count unchanged.

Deliberately **not** changed, each with its reason so the omission is a ruling and not a silence:

- **All 43 of the spec's checkboxes stay `- [ ]`** (20 `## Slice checklist` / 14 `## Helper-reuse
  obligations (DRY)` / 9 `## Definition of done`, 26 of them top-level). Deferral reason, per
  `## Final verification job` step 3: they are an **obligation list**, and `:74`'s `Status:` line is
  the single source of truth for release state — ticking them would put a second independently
  rottable record of it in the spec, which is the duplication that already rotted once at `:56-73`.
  Measured, not asserted: all four archived `0.0.14`-era siblings ship **0** ticked boxes. Not
  deferred to a future pass; this is the settled handling for a shipped card's spec, upheld by both
  reviews.
- **`## Key glossary references` `:122-127`** — ruled KEEP above, on box 6's class ground.
- **`### Decision 12`'s body `:1657`, `## Current state` `:663-668`, `## Goals` item 6 `:726-729`** —
  the three recorded keeps, each confirmed on the ground it rests on above.
- **`:113-115`'s R1-added contract sentence** — recorded with the unfavourable clause first, as
  pass 2 left it; weakening it would trade a true general claim for a hedge.
- **`### Decision 12`'s heading**, whose slug carries eleven of the spec's 200 anchor citations.
- **The `TODO-BETA-053-0.1.5` pointer at `:2623`** and the `strawberry.Schema` / `DjangoSchema`
  inexactness at `:291-297` — catalog items 3 and 4, both wider than this item.
- **Both files' relative link paths**, which resolve from `docs/` today and are **R3's** to
  re-relativize. Not pre-adjusted.
- **The rationale file in full** — audited a fourth time and again needs nothing (box 25).

**Status-line re-verification (`worker-1.md` `## Spec status-line re-verification`).** Read `:1-115`
paragraph by paragraph, plus `## Key glossary references` on the ground that the last pass's Medium
came from trusting a declared range. The block now reads consistently end to end: `:3-5`
"completed / owned", `:56-72` "was … carried the cut … recorded below rather than here", `:74` "owned
and applied", `:104-107` "carries … as `shipped (0.0.14)`", `:110-115` the deliberative-layer pointer
R3 will re-relativize. `:74` needed no edit in any of the three passes. Every `[spec-038]` /
`[spec-041]` / `[spec-042]` / `[spec-043]` / `[rationale]` definition resolves, and no reference to a
predecessor doc this cycle deleted survives.

### Baseline / concurrent-work note

**The dirty list GREW mid-pass, and it is not this pass's growth.** It opened at the seven entries
pass 2 records — `M docs/feedback.md`, `M docs/spec-044-debug_extension-0_0_14.md`,
`D to-many-search-optimizer-reproduction.md`, and the four untracked cycle files
(`bld-044-r1-rationale_move.md`, `bld-044-r2-doc_completion.md`,
`build-044-debug_extension-0_0_14.md`, `spec-044-debug_extension-0_0_14-rationale.md`) — measured at
the start. It closed at **fourteen**: seven **package source and test** files appeared while this pass
was running.

- `django_strawberry_framework/_request_body.py` (+92/-16), `auth/mutations.py` (+25/-11),
  `consumers.py` (+76/-76), `utils/sessions.py` (+118/-85), `views.py` (+6/-1),
  `tests/auth/test_mutations.py` (+68/-39), `tests/test_routers.py` (+67/-61).

**None is this pass's, and none was edited or reverted** (`AGENTS.md` rule 34). Attributed rather than
assumed: this pass issued no write to any `.py` file at all — its only writes were one spec edit and
this artifact — and the mtimes place the churn outside its writes (`consumers.py` 11:57,
`views.py` 11:59, `tests/test_routers.py` **12:02:25**, i.e. *after* this section was first written at
12:02:03, while the spec edit landed at 11:55:11). The file set is the transport / session / auth
surface of the **preserved spec-046 cycle** — the same cycle whose `docs/feedback.md` adversarial
review has been dirty since R1 — so this is a concurrent session's in-flight work on that cycle, not
build output and not a maintainer rewrite of anything spec-044 owns. The build plan's context flag
holds regardless: **no residual item changes package source**, so nothing in that list can be this
item's, and box 31's scope claim remains true of this item's own writes.

Two consequences worth stating rather than leaving for the final gate to trip over. First, the
`### Deferred work catalog` and any full-tree `pytest` the gate runs will see this churn; it is
concurrent work to be reported, never reverted, and `git diff --check` / `ruff --check` failures inside
those seven files are not this cycle's to fix. Second, `docs/feedback.md` and the
`to-many-search-optimizer-reproduction.md` deletion remain the plan's declared baseline-dirty pair and
are likewise untouched.

No `git checkout` / `restore` / `stash` / `worktree` ran at any point. No commit, no branch. R3 not
performed, and no path was pre-adjusted for it.

### Final status

**`final-accepted`.**

No box is over-ticked, none is silently un-ticked, the escalated Low is closed in the spec, the
deletion-with-preservation claim is re-proven from the tree in both directions, all four gates pass in
this pass's own run, and the two unruled sites this audit found are ruled — one on the ground the
recorded class rulings already establish, and neither requiring a re-loop. Under Deviation 3 a
`revision-needed` here would route back to Worker 1; nothing requires it.

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
