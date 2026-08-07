# Build: Final test-run gate — spec-002 residual-completion cycle

Spec reference: `docs/SPECS/spec-002-optimizer-0_0_2.md` (whole file), companion
`docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md`
Build plan: `docs/builder/build-002-optimizer-0_0_2.md` (final checklist line)
Status: final-accepted

This is the cycle's last pass before the maintainer handoff. It runs `BUILD.md` `## Final test-run
gate` in the order given there, records each command's real pass/fail with the output actually seen,
folds in the cross-slice integration obligations the build plan assigned here, and writes the
`### Deferred work catalog`.

**The plan's `## Artifact list` note governs the shape of this artifact.** There is no
`bld-integration.md`: this cycle lands no source, so a cross-slice DRY scan has no subject. Its two
live obligations were split — the staged-anchor sweep (`BUILD.md` `## Cross-slice integration pass`
step 6) ran in R3, and the cross-artifact read runs here. Both are discharged below.

---

## Cross-artifact read (integration-pass obligation, folded into this gate)

`BUILD.md` `## Cross-slice integration pass` step 1 allows no "as needed" reading. Every prior
artifact of this cycle was read before any gate result was interpreted and before the catalog was
written:

| Artifact | Lines / bytes | Status as read | What it delivered |
|---|---|---|---|
| `docs/builder/build-002-optimizer-0_0_2.md` | 245 | R1/R2/R3 `- [x]`, final gate `- [ ]` | the plan, its three deviations, the six already-shipped-slice evidence rows, the 15-row verified drift floor, the **3-anchor constraint**, and the **baseline exception** this gate is governed by |
| `docs/builder/bld-002-r1-rationale_move.md` | 1,364 / 97,416 | `final-accepted` | the rationale extraction: `## Open questions`, the `## O4 extraction` fold, the `## Problem statement` and `## Architecture decision` derivations, and the `## References` chronology clause, all relocated; spec `7,398 -> 7,006` bytes; companion created at 14,296 |
| `docs/builder/bld-002-r2-spec_reconciliation.md` | 1,472 / 107,645 | `final-accepted` | 15 drift rows reconciled; `## Current state` **removed** rather than retitled; a family-wide scope rule written into `## Purpose`; spec `7,006 -> 9,844` (+2,838, +40.5%); companion grown to 33,620 |
| `docs/builder/bld-002-r3-doc_completion_archive.md` | 2,202 / 169,364 | `final-accepted` | the durable-doc audit (zero edits owed), the three-direction archive verification, the `SpecDoc` / terms-CSV chain, the staged-anchor sweep, **one** `CardItem.text` mutation on card `TODO-ALPHA-052-0.1.0`, and the eight-item consolidated hand-off this gate re-verifies |

Also read in full for this pass: `AGENTS.md`, `START.md`, `docs/builder/BUILD.md`,
`docs/builder/ARTIFACT.md`, `docs/builder/worker-1.md`, `docs/builder/worker-memory/worker-1.md`,
`GOAL.md`, `docs/SPECS/spec-002-optimizer-0_0_2.md`, and `docs/builder/bld-001-final.md` as the
precedent for this gate. Targeted reads against every claim re-derived here:
`docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md`, `docs/GLOSSARY.md`, `CHANGELOG.md`,
`KANBAN.md`, `docs/SPECS/spec-003-optimizer_nested_prefetch_chains-0_0_2.md`, and
`docs/SPECS/spec-006-public_surface-0_0_3.md`. No other worker's memory file was opened.

**Cross-artifact findings: none that block.** The three items are sequential and non-overlapping by
construction (R1 moves deliberation out, R2 reconciles the surviving contract, R3 finishes the
consumer-facing documentation and audits the archive), each closed `final-accepted` by an independent
Worker 1 spawn, and each later item re-measured the prior item's hand-off rather than inheriting it —
visibly so: R2 corrected R1's anchor budget from 1/1/1 to 1/1/2, and R3 corrected R2's terms-CSV
premise as well as its count. The two shared-shape risks a concurrent-cohort build carries — a
duplicated helper and a duplicated constant — cannot arise: **this cycle writes no `.py` file at
all.** The one live document-level duplication (a fact told twice across the spec and its rationale)
was measured in R1 and again in R2 and stands at one labelled 12-word quotation; the two genuine
cross-round duplications (the hand-rolled link checker, the rationale preamble) are catalogued below
rather than consolidated, because both targets sit outside every residual item's write set.

**Staged-anchor sweep: confirmed run in R3, and re-run here as corroboration.**

```
$ grep -rEn 'TODO\(spec-002|TODO-(ALPHA|BETA|STABLE)-002' django_strawberry_framework/ tests/ examples/
exit=1        # no match
```

Zero staged anchors naming this build's spec or card in package source, in any of the three test
trees, or in the example project, so the `revision-needed` trigger does not fire. Every survivor
tree-wide is a per-cycle `docs/builder/` artifact whose prose describes the sweep — including this
paragraph, which is why the load-bearing run is scoped to the three shipped trees rather than to `.`.

---

## Working-tree state, measured at this gate's open and again at its close

`AGENTS.md` rule 34 and the plan's baseline exception both turn on this, so it is measured twice and
both readings are recorded. HEAD is `faebd949` at both.

**Open: 15 paths. Close: 16 — this artifact is the sixteenth and appears only after it is written.**

```
 M KANBAN.html                                        <- MIXED: R3's one CardItem + concurrent session
 M KANBAN.md                                          <- MIXED: R3's one CardItem + concurrent session
 M docs/SPECS/spec-002-optimizer-0_0_2.md             <- THIS CYCLE (R1 + R2)
 M docs/SPECS/spec-042-debug_toolbar-0_0_14.md        <- concurrent
 M docs/SPECS/spec-043-test_client-0_0_14.md          <- concurrent
 M docs/SPECS/spec-044-debug_extension-0_0_14.md      <- concurrent
 M docs/SPECS/spec-050-debug_extraction-0_0_19.md     <- concurrent
 M docs/SPECS/spec-051-boundary_dry_squeeze-0_0_20.md <- concurrent
 M examples/fakeshop/db.sqlite3                       <- MIXED: R3's one CardItem + concurrent session
 M examples/fakeshop/test_query/README.md             <- concurrent
?? docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md   <- THIS CYCLE (R1 + R2)
?? docs/builder/build-002-optimizer-0_0_2.md               <- THIS CYCLE
?? docs/builder/bld-002-r1-rationale_move.md               <- THIS CYCLE
?? docs/builder/bld-002-r2-spec_reconciliation.md          <- THIS CYCLE
?? docs/builder/bld-002-r3-doc_completion_archive.md       <- THIS CYCLE
?? docs/builder/bld-002-final.md                           <- THIS CYCLE (this file, at close only)
```

The set is identical to the one R3 recorded at its open and its close, and the eight concurrent-session
paths are exactly the eight the plan's `## Baseline-dirty out-of-scope files` names (the ninth entry
there, `examples/fakeshop/db.sqlite3`, is one of the three now-mixed generated paths rather than a
purely concurrent one). **Nothing was reverted, checked out, restored, or stashed by this pass**; no
`git worktree` was created. This pass wrote exactly two files: this artifact and
`docs/builder/worker-memory/worker-1.md` (gitignored).

---

## Environment, read rather than asserted

`BUILD.md` `## Floor verification`: *"Never state `.venv`'s own versions from memory or from a number
written down in a document."* Read at this gate:

```
$ uv pip list | grep -iE '^(django|strawberry-graphql|channels|django-filter|djangorestframework) '
channels                    4.3.2
django                      6.1
django-filter               25.2
djangorestframework         3.17.1
strawberry-graphql          0.323.2

$ uv run python -c "import sys; print(sys.version)"
3.14.2 (main, Jan 27 2026, 23:32:07) [Clang 21.1.4]
```

The shared `.venv` carries Django **6.1** against an open-ended `Django>=5.2.16` in `pyproject.toml`.
Every gate command below nonetheless completed green, `manage.py check` included — the command where
a fail-closed `AppConfig.ready()` guard would surface. Recorded as checked-and-clear from the reading,
not invoked from a note.

---

## Gate commands (`BUILD.md` `## Final test-run gate`, in order)

| # | Command | Result | Evidence |
|---|---|---|---|
| 1 | `uv run pytest --no-cov` | **PASS** (exit 0) | `5635 passed, 40 skipped in 62.65s (0:01:02)` |
| 2 | `uv run python examples/fakeshop/manage.py check` | **PASS** (exit 0) | `System check identified no issues (0 silenced).` |
| 3 | `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` | **PASS** (exit 0) | `No changes detected` |
| 4 | `uv run ruff format --check .` | **PASS** (exit 0) | `418 files already formatted` |
| 5 | `uv run ruff check .` | **PASS** (exit 0) | `All checks passed!` |
| 6 | `git diff --check` | **PASS** (exit 0) | no output |

Notes on the readings, so a later reader can re-derive rather than trust them:

- **`--no-cov` is the only coverage-shaped flag used anywhere in this pass.** `pytest.ini`'s `addopts`
  auto-applies `--cov`, so plain `uv run pytest` would have been a coverage run and is forbidden
  (`BUILD.md` `## Coverage is the maintainer's gate, not a worker's tool`). **No line coverage was
  inspected or asserted**, and the only requirement taken from the sweep is that it passes.
- The sweep is the **full** three-tree run — package `tests/`, per-app `examples/fakeshop/apps/*/tests/`,
  and live `examples/fakeshop/test_query/` — under `xdist` (`gw0`-`gw7` in the transcript), which is the
  configuration `BUILD.md` `### Example-project schema changes must sync every schema-module list` names
  as the only one that can expose an order-dependent registry collision. The 40 skips are the standing
  `FAKESHOP_SHARDED`-gated set plus soft-dependency guards; no skip is new to this cycle, which writes
  no test.
- **`ruff format --check` and `ruff check` were run read-only over `.`** — never `--fix`. Running them
  repo-wide is what the gate requires and is safe *because* they are read-only; a write-mode run would
  have swept the concurrent session's eight paths.
- `git diff --check` covers the whole tree, this cycle's two tracked edits and the concurrent
  session's alike, and reports no whitespace error and no conflict marker anywhere.

### Documentation constraint commands (re-run because this cycle's whole deliverable is documentation)

| Command | Result | Output |
|---|---|---|
| `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-002-optimizer-0_0_2.md` | **PASS** (exit 0) | `OK: 3 terms - all have glossary entries and at least one spec link.` |
| `uv run python examples/fakeshop/manage.py import_spec_terms --check` | **PASS** (exit 0) | `OK: 49 done cards have glossary links.` |
| `uv run python scripts/check_trailing_commas.py --check` on the spec | **PASS** (exit 0) | no output |
| `uv run python scripts/check_trailing_commas.py --check` on the rationale | **PASS** (exit 0) | no output |
| `uv run python scripts/check_trailing_commas.py --check` on `bld-002-r1-rationale_move.md` | **PASS** (exit 0) | no output |
| `uv run python scripts/check_trailing_commas.py --check` on `bld-002-r2-spec_reconciliation.md` | **PASS** (exit 0) | no output |
| `uv run python scripts/check_trailing_commas.py --check` on `bld-002-r3-doc_completion_archive.md` | **PASS** (exit 0) | no output |
| `uv run python scripts/check_trailing_commas.py --check` on `bld-002-final.md` (this file) | **PASS** (exit 0) | no output; run after the file was written |
| `uv run python scripts/build_tree_md.py --check` | **PASS** (exit 0) | `docs/TREE.md is up to date.` |

**The 3-anchor constraint held end to end, and it held with a spare.** The plan's
`### The 3-anchor constraint` is the trap this cycle was built around: three anchors in a 7.4KB spec,
each carried at plan time by a *single* link, two of them in sections R1 and R2 were most likely to
rewrite. Both sections were in fact rewritten (`## Current state` was removed outright), and the
anchor map is now **1 / 1 / 2**:

```
$ grep -o '\]\[glossary-[a-z0-9_-]*\]' docs/SPECS/spec-002-optimizer-0_0_2.md | sort | uniq -c
   2 ][glossary-djangooptimizerextension]
   1 ][glossary-djangotype]
   1 ][glossary-only-projection]
```

`exit 0` is the gate; `49` is not — the done-card count is the whole board's, not card 2's, and it
moved 48 -> 49 during the prior cycle. The property the command asserts is that every done card,
`DONE-002-0.0.2` included, still has its glossary links, and the terms CSV was never edited to buy
one (323 bytes, 3 data rows, 3 distinct anchors, absent from `git status`).

**Three further generator `--check` runs**, because the mixed generated trio goes to the maintainer
and `--check` is the assertion that nothing was hand-edited into a rendered file:

```
$ uv run python scripts/build_kanban_md.py --check      -> KANBAN.md is up to date.        exit=0
$ uv run python scripts/build_kanban_html.py --check    -> KANBAN.html is up to date.      exit=0
$ uv run python scripts/build_glossary_md.py --check    -> docs/GLOSSARY.md is up to date. exit=0
```

**An independent link-and-anchor audit of the pair**, written at this gate rather than inherited (the
sixth hand-roll in this cycle family, and the reason catalog item 5 exists). It masks code-span
content to same-length filler, preserves whitespace runs, preserves `_`, and renders reference-link
markup out of a heading before slugging — the four measured slugger defects:

```
docs/SPECS/spec-002-optimizer-0_0_2.md:                    defs=4  uses=4  undefined=[] orphaned=[] broken=[]
docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md:     defs=19 uses=19 undefined=[] orphaned=[] broken=[]
```

4/4 and 19/19 with every count zero, reproducing R3's C2 reading from a fifth independent
implementation. Every definition target resolves on disk and every `#fragment` resolves against the
target file's headings, `#visibility-status` included.

## Floor verification

**No floor-verification scope declared.**

The build plan's preamble declares `Floor-verification scope: none`, and the declaration is correct
rather than merely present: no residual item touches a Django / Strawberry / channels integration
seam — request/response handling, view or ASGI plumbing, upload or body parsing, session/auth,
queryset or expression compilation, schema and type construction against Strawberry internals, or
consumer middleware wiring. The cycle edited a spec, its rationale companion, cross-references, and
one kanban `CardItem`. **No `.py` file was written in this cycle at all.** R1, R2, and R3 each
recorded the `none` declaration in their `### Floor verification` sections, so there is no floor run
a pass owed and skipped, and **the gate owes none of its own**.

**No floor venv was built by this gate**, per the dispatch, and the shared `.venv` was not mutated by
any command above — every one is read-only or test-only.

## Failability proofs

`None; this cycle introduced no new boundary.` Pre-declared in the plan and audited across all three
items: the entire cycle diff is Markdown plus one DB text column. There is no guard, cap, gate,
rejection path, or validation branch whose removal a test could fail on, so the mandatory re-run floor
is arithmetic over an empty set rather than a waived obligation. Equally there is no fail-open
**shape** to read for — a fail-open expression needs executable code, and the diff has none. Their
absence is not a finding.

## Hot-path budget

`Not applicable; plan declares no hot path.` The build plan declares `Hot-path declaration: none`
cycle-wide, and nothing this cycle wrote runs per request, per resolver, per row, per connection, or
per outbound message.

---

## The baseline exception, and what it had to govern

The plan's preamble carries it, which is what `BUILD.md` `## Final test-run gate` requires for it to
be honoured:

> A failure attributable to a file this cycle never wrote does **not** block `final-accepted` and does
> **not** route back through a residual item's loop; it is reported to the maintainer. The gate still
> reports each command's real result — the exception governs what a result *blocks*, never whether it
> is recorded honestly.

**It was not needed. All fifteen commands above passed**, so there is no failure to attribute in
either direction — none against a concurrent-session file, and none against this cycle's own writes.
Recorded rather than omitted, because "the exception was available and unused" and "the exception was
quietly relied on" are different states and only the first is provable by a green board.

Had a failure occurred, this cycle's own writes — the only set that could have routed back through an
item loop — are exactly: `docs/SPECS/spec-002-optimizer-0_0_2.md`,
`docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md`, one `CardItem.text` row in
`examples/fakeshop/db.sqlite3` (plus the `KANBAN.md` / `KANBAN.html` regenerate of it), and the
`docs/builder/build-002-*` / `bld-002-*` artifacts. Anything else is the concurrent session's or
pre-existing at HEAD.

**No "pre-existing at HEAD" claim had to be made**, and that is the honest reading rather than a
convenience: `BUILD.md` `## Claims are proven mechanically, never accepted on prose` makes a failing
test **not worker-verifiable at all** in a dirty tree, so such a claim would have been recorded and
escalated rather than resolved here. Nothing failed, so nothing was escalated on that ground.

---

## Item statuses and checklist audit

| Item | Artifact | Status | Boxes |
|---|---|---|---|
| R1 — spec rationale extraction | `bld-002-r1-rationale_move.md` | `final-accepted` | dispatched-findings checklist audited at R1's final verification; none left `- [ ]` |
| R2 — spec reconciliation | `bld-002-r2-spec_reconciliation.md` | `final-accepted` | dispatched-findings checklist audited at R2's final verification; none left `- [ ]` |
| R3 — documentation completion + archive audit | `bld-002-r3-doc_completion_archive.md` | `final-accepted` | 18 boxes, all `- [x]`, each **re-tested by re-running its check** at R3's final verification; none un-ticked, none left `- [ ]` |

Re-read at this gate: all three `Status:` lines are `final-accepted`, and no artifact carries an
un-deferred `- [ ]`. The plan's checklist accordingly has R1, R2, and R3 `- [x]`, with only the final
gate line open — Worker 0 marks it after this artifact reaches `final-accepted`.

**Spec status-line re-verification (`worker-1.md`, every Worker 1 spawn).**
`docs/SPECS/spec-002-optimizer-0_0_2.md:1` is `# Spec: Optimizer & Reverse-Relation Resolution`, `:2`
blank, `:3` `## Purpose`. **There is no status / target-release / owner / predecessor block**, so this
obligation has nothing to falsify and no edit is owed. Re-derived here, not inherited from R3.

---

## Deferred work catalog

`BUILD.md` `## Final test-run gate`: this is the next spec author's reading list. R3's final
verification consolidated eight items; each was **re-verified by execution at this gate** rather than
carried on trust, because a catalogued deferral carried unchecked is how a closed item gets reported
as open. Every item names its source artifact section, the spec line that licenses the deferral (or
`none`, and why), a one-line description, and an owner.

1. **The `KANBAN.md:310` card bullet — CLOSED, not deferred.** *Source:* R1 `### Notes for Worker 1`
   item 1 -> R2 item 1 -> R3 `#### A` / box A1. *Licensing spec line:* none; the build plan
   pre-authorized a DB write when the audit found real drift, and this cycle itself created the drift.
   **Owner: none — discharged.** Re-verified here: `KANBAN.md:310` carries the replacement text, and
   `build_kanban_md.py --check` / `build_kanban_html.py --check` both exit 0, so the render matches the
   DB. Listed so the next author does not re-open a closed key.
2. **The `0.0.2`-versus-`0.0.3` release-dating disagreement.** *Source:* R2 hand-off item 10 -> R3
   `#### B` / box B5 -> R3's escalation 1. *Licensing spec line:* none — `AGENTS.md` rule 21 closes
   `CHANGELOG.md` to every worker, which is what makes it undecidable inside a build.
   `docs/GLOSSARY.md` dates `DjangoOptimizerExtension` and `only()` projection to `0.0.2`, matching
   card `DONE-002-0.0.2`'s `target_version`; `CHANGELOG.md` `[0.0.2]` calls the extension *"early …
   depth-1"* while `[0.0.3]` dates the end-to-end surface to `0.0.3`. Whether a
   `**Status:** shipped (X)` line names **first shipped** or **complete** is an editorial call about
   the glossary's dating convention for a subsystem that shipped across two releases, and it is not
   unilaterally correctable — `GlossaryTerm.body`, the card's `target_version`, the card id, and the
   spec filename `…-0_0_2.md` must move together. **Owner: maintainer.**
3. **Card 2's terms-CSV set — DECIDED at three, with reopening conditions written down.** *Source:*
   R2 hand-off item 11 -> R3 `#### D` / box D3 -> R3's `### The terms-CSV ruling`. *Licensing spec
   line:* none; `AGENTS.md` rule 26 (fold-in belongs to the completing spec's Slice 5) is what closes
   it. Four glossary-backed terms are named in the spec body without a link — `DjangoConnectionField`
   (`:25`), `finalize_django_types` (`:31`), `FK-id elision` (`:33`), `Visibility boundary` (`:48`) —
   and that gap is deliberate. **Owner: closed.** Re-verified here: the CSV is 323 bytes / 3 data rows
   / 3 distinct anchors and absent from `git status`, and `check_spec_glossary` exits 0 at three.
   Reopening requires a cycle that already owns both spec-002's body and card 2's board record; the
   mechanical sequence (spec-body link first, then the CSV row, then both commands, then re-render
   `KANBAN.md`) is in R3's ruling. For the record: R2's premise was wrong as well as its count —
   `Plan cache` and `Meta.optimizer_hints` occur **0** times in the spec.
4. **`spec-003-optimizer_nested_prefetch_chains-0_0_2.md` is stale at four sites.** *Source:* R2
   hand-off item 4 (which named one) -> R3 `#### C` / box C4 (which found four). *Licensing spec
   line:* none; the file is a read-only sibling owned by another card, per the build plan's
   `## Build-wide context flags`. Re-read at this gate: `:4` still says *"The remaining O-slice is
   O4"* (O4 shipped); `:27` still publishes `plan_optimizations(selected_fields, model, info=None)` at
   the pre-D4 arity and still names `_collect_scalar_only_fields` in the present tense (**0**
   occurrences in `django_strawberry_framework/`); `:333` is a discharged when-O4-ships instruction
   naming `## Current state`, a section that no longer exists; `:335`'s trailing clause is *"Also
   update the older parent-spec O4 references in `docs/SPECS/spec-002-optimizer-0_0_2.md`."* R3
   supplies recommended replacement wording for `:4` and `:333`. **Owner: maintainer / whoever next
   opens `spec-003`.** **Do not sweep up `spec-006-public_surface-0_0_3.md:136` and `:147`** — both
   re-read here, both name `## Visibility status`, both **live and correct**; that heading survives in
   spec-002 precisely because of them.
5. **Promote one spec/rationale link-and-anchor checker into `scripts/`, with the four measured
   slugger defects encoded as regression tests.** *Source:* R1 hand-off item 8 -> R2 item 8 -> R3
   Notes item 5 and its Worker 3's `### DRY findings` -> R3's `#### DRY escalation`. *Licensing spec
   line:* none; `scripts/` is outside every write set in this cycle. Already tracked as a board card
   at `KANBAN.md:309` (re-read here, still present and still un-owned) — this is a **sixth measured
   argument for an existing item, not a new one**, the sixth hand-roll being this gate's own audit
   above. The four defects to encode:
   - **(a) A heading that is itself a reference link, slugged without rendering the markup out
     first.** `check_spec_glossary.py::github_anchor` turns `## [Scalar field conversion][glossary-…]`
     into `…conversionglossary-scalar-field-…`. **False dangling.**
   - **(b) Whitespace runs collapsed.** GitHub replaces spaces **one at a time**, so a heading with a
     double space slugs to a double hyphen; a checker that collapses runs reports a **false PASS** —
     the only **silent** defect of the four, and therefore the most dangerous to leave unencoded.
   - **(c) Code spans deleted rather than masked before matching reference links.** A reference link
     here is routinely spelled ``[`only()`][ref]``; deleting the span leaves `[][ref]`, which
     `\[([^\]]+)\]` cannot match. One run reported 3 spec + 12 rationale **false orphans** from this
     alone. The fix is to mask the span's content to **same-length filler**, preserving the brackets.
   - **(d) `_` stripped as an emphasis marker before slugging.** It destroys `django_types`, so
     `#coordination-with-spec-001-django_types-0_0_1md` reports unresolved **against a correct link
     definition** — a false positive whose natural "fix" is to corrupt a good link. **This one is a
     recurrence:** R1 measured it and wrote it into its hand-off, and R3's reviewer re-introduced it
     from scratch two rounds later. A trap recorded in prose demonstrably did not prevent its own
     repetition; only a test can. That, not the hand-roll count, is the argument for the tool.

   **What a real checker must do**, so the requirement list is not re-derived either: render
   reference-link markup out of a heading before slugging; keep alphanumerics, `-` and `_` and drop
   the rest; replace each space with one hyphen without collapsing runs; mask code-span content to
   same-length filler; resolve every definition target from the **source file's own directory** with
   the fragment stripped; resolve every `#frag` against the **target** file's headings; and report
   defs, uses, undefined, orphaned, duplicate-defs, broken-on-disk, and inline cross-file links as
   separate counts. **Owner: maintainer**, via `KANBAN.md:309`.
6. **The rationale-file preamble is a de-facto template with no single source.** *Source:* R1's
   `### Disposition of the escalated DRY observation` and its Worker 3's escalation there -> R3's
   `### DRY check across R1, R2, and R3`. *Licensing spec line:* none. 266 words / 13.0% of the body
   are shared with `docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md`, entirely in the preamble
   and framing — **zero shared words in the entries section**, which is where review value lives. R1
   trimmed the one run with a canonical home elsewhere (the `**Who reads it.**` bullet, now a pointer
   at `BUILD.md`) and kept the rest, because unilaterally trimming a shared template would make the
   two siblings diverge and `spec-001`'s rationale belongs to a closed cycle. The natural fix is to
   **emit** the preamble, which folds into item 5's tool rather than standing alone. **Owner:
   maintainer.**
7. **The `_optimizer_field_map` rename-sweep residue — four live-code sites on a deleted symbol.**
   *Source:* R2 hand-off item 9 (scope-corrected at its final verification from three to four) -> R3
   Notes item 6. *Licensing spec line:* none; `tests/` and `scripts/` are outside every residual
   item's write set. Re-measured at this gate — the symbol has **0** occurrences in
   `django_strawberry_framework/`, and four in live code:
   `tests/optimizer/test_field_meta.py:322` `::test_optimizer_field_map_populated`, `:339`
   `::test_optimizer_field_map_contains_relations`, `:362`
   `::test_optimizer_field_map_respects_fields_filter`, and the token in `scripts/review_inspect.py:42`.
   The prose survivals in `CHANGELOG.md` / `KANBAN.md` / `spec-010` / `spec-016` are **correct as
   history and are not in the sweep** — widening it into a documentation sweep is the error to avoid.
   R3 corroborated the shape with a second instance: `_collect_scalar_only_fields` is likewise absent
   from the package while `spec-003:27` still names it in the present tense (item 4). **Owner:
   maintainer / a future test-hygiene card.**
8. **Two `TODO(spec-035)` anchors in `django_strawberry_framework/optimizer/walker.py` (`:464`,
   `:1131`) — recorded, with no action owed.** *Source:* R3 `#### B` / box B2 and Notes item 8.
   *Licensing spec line:* `BUILD.md` `## Cross-slice integration pass` step 6, which scopes the
   staged-anchor sweep to anchors naming **this** build's spec or card. Re-read here: `:464`
   *"supply a registry-only type-condition classifier"*, `:1131` *"audit this FK-id-elision helper as
   the walker's …"*. Both name spec-035, both are indented `#` comments inside function bodies so
   neither reaches `docs/TREE.md`'s docstring render, and package source is read-only this cycle.
   **Owner: whoever closes spec-035.** Recorded so a future sweep reads them as that spec's debt
   rather than as this cycle's, and does not spend a pass re-deriving why they were left.

### Closed this cycle — do not re-raise

Every one was re-verified as closed rather than assumed:

- **R1's `## References` chronology clause** — moved to the rationale entry that already owns the
  bundling argument; a chronology regex over the spec returns zero hits.
- **D15's four upstream locators** — verified present in the checkouts `AGENTS.md` line 2 names, with
  the two URLs honestly recorded as unfetched rather than claimed verified.
- **Drift rows D3 and D13** — routed on *"whose contract is the answer"* rather than *"did it ship"*;
  D3 became O1 contract, D13 stayed `spec-004`'s.
- **The retitle question** — `## Current state` removed rather than retitled; `## Visibility status`
  held by `spec-006`'s two citations and the companion's `#visibility-status` link definition;
  `## Shipped slices` and `## Implementation checklist` survive the standing-promise argument on their
  merits, since a past-tense fact about what shipped is not a promise about the present.
- **The missing blank line before `### O4`** and **the `## Coordination` framing tension** — both
  fixed / resolved in R2.
- **Three wordings deliberately left as they are, each recorded so a later pass does not "fix" them
  back.** These are not deferrals; they are the reverse, and they are gathered here because a
  do-not-touch note that lives only in a closed artifact is the one a future sweep steps on.
  (a) `## Architecture decision`'s *"must return correct results **when** the optimizer is disabled
  **and when** a relation is not already loaded"* — the repeated `when` distributes the two
  obligations and is the disambiguator; re-checked here, present exactly once.
  (b) `## Purpose`'s *"Where one of them changed how one of the slices below behaves"* — the only
  "before"-implying verb in the reconciled spec, and it is about sibling specs changing package
  behavior, not about this document's own revisions, so it is not the chronology the rule forbids;
  present exactly once.
  (c) The rationale pointer appears at **three** sites, not the five a literal reading of the
  per-decision pointer rule yields; on a spec this short, five would make the pointer the loudest
  thing in three sections. Re-counted here: `[spec-002-rationale]` is used at `:8`, `:18`, `:27` plus
  its one definition at `:89`.
- **One provenance note (R3's Worker 3, Notes item 4), which the eight-item consolidation does not
  carry and which belongs here.** `docs/builder/build-002-optimizer-0_0_2.md:149` and
  `docs/builder/bld-002-r3-doc_completion_archive.md:132` still quote the **retired**
  `KANBAN.md:310` bullet verbatim. Confirmed at this gate: both lines still open with
  *"`docs/SPECS/spec-002-optimizer-0_0_2.md` carries four status-shaped sections: `## Current
  state`, …"*. They are per-cycle artifacts recording what the bullet said at plan time, they are
  **correct as provenance**, and they must not be updated to the new text.

---

## Handoff to the maintainer

### Summary — what the whole cycle shipped

Three deliverables, one per residual item.

- **The new rationale companion.** `docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md` did not
  exist at this cycle's open; it is now **33,620 bytes** and carries eight entries, each keyed to a
  spec decision by heading text **and** by resolving reference-style anchor, each with at least one
  rejected alternative and the reason it lost, and each with a `**Claims the spec no longer makes.**`
  line. R1 created it at 14,296 bytes by *moving* the deliberative layer out — `## Open questions`,
  the `## O4 extraction` fold, the `## Problem statement` and `## Architecture decision` derivations,
  and the `## References` chronology clause — and R2 grew it to its current size with the change
  record for every drift row it reconciled. Three entries are keyed to headings the cycle removed and
  say so in their own lead, pointing at the surviving section their argument bears on.
- **The reconciled spec.** `docs/SPECS/spec-002-optimizer-0_0_2.md` went **7,398 bytes at HEAD ->
  7,006 after R1's move (-392, -5.3%) -> 9,844 after R2's reconciliation (+2,838, +40.5%)**. Growth is
  the correct sign for a reconciliation: a corrected contract costs more words than a wrong one.
  Fifteen drift rows were resolved; three claims were flatly false at HEAD (relation resolvers said to
  attach at `DjangoType.__init_subclass__`, the walker said to route through `_optimizer_field_map` —
  **no such symbol exists** — and `plan_optimizations` published at the wrong arity) and each now
  states the contract that holds, with no chronology and no amendment block. Two structural outputs
  outweigh the fifteen corrections: `## Current state` was **removed** rather than retitled, its two
  unique facts re-sited into the contract prose that already owned their subjects; and `## Purpose`
  gained a **scope rule for the whole optimizer family** — state the behavior that holds, name the
  owning spec in one clause, restate none of its rules — the only artifact of the cycle that
  constrains a future author.
- **The board correction.** One `CardItem.text` on card `TODO-ALPHA-052-0.1.0`, the `KANBAN.md:310`
  deferral bullet that this cycle itself falsified three ways: R1 removed `## Open questions`, R2
  removed `## Current state`, and R2 added the very `#anchor` citation the old bullet swore did not
  exist. The replacement was applied through the ORM with `.save()`, proved byte-identical to R2's
  decided text by four independent derivations, and carried onto the board by regenerating
  `KANBAN.md`, `KANBAN.html`, and `docs/GLOSSARY.md`. It states the surviving constraint and
  deliberately carries **no count**, so the next entry the companion gains cannot falsify it the way
  the old bullet was falsified.

### Archive status — verified, not performed

The maintainer's instruction named archival as an outcome, and the honest report is that it was
**already done before this cycle opened and is now confirmed complete**. `docs/SPECS/spec-002-optimizer-0_0_2.md`
and `docs/SPECS/appx/spec-002-optimizer-0_0_2-terms.csv` were already at their archived paths;
`SpecDoc.path` for card 2 already read `docs/SPECS/spec-002-optimizer-0_0_2.md`; and both `KANBAN.md`
references already pointed there. **No move was performed by this cycle, and none was owed** — the
build plan declared this at pre-flight (`## Build-wide context flags`), which is why R1's new
rationale file was written directly to `docs/SPECS/appx/` rather than to `docs/` and moved after.

What R3 did instead was verify the archive in all three cross-reference directions, and every leg came
back clean: outbound (the spec's own link definitions and its seven code-span sibling-spec paths, all
resolving), inbound (nine `KANBAN.md` / eight `KANBAN.html` / `spec-003` / `spec-006` / `spec-033` /
`spec-035` / `spec-001` references, all correct; **ten** standing docs carrying zero `spec-002`
references; no surviving pre-archive `docs/spec-002…` path anywhere), and the chain
(`SpecDoc.path` -> file exists; card 2 -> 3 glossary links; terms CSV -> 3 rows, 3 distinct anchors;
`import_spec_terms --check` exit 0). Re-confirmed at this gate by the link audit and the constraint
commands above.

### What the maintainer must reconcile at commit

- **The mixed generated trio.** `KANBAN.md`, `KANBAN.html`, and `examples/fakeshop/db.sqlite3` carry
  **R3's one `CardItem.text` edit plus a concurrent session's work** on card 52 (three new items) and
  card 21 (one), all timestamped `2026-08-07T04:13:51`. **No worker attempted to separate it**, per
  `BUILD.md` `### Tracked binary / generated files: churn and concurrent-writer handling`, and none
  should. The evidence that this cycle's contribution is exactly one row is R3's whole-database
  HEAD-versus-now content comparison, plus `--check` exit 0 on all three generators re-run at this
  gate — which asserts that every byte on disk is what the DB renders, i.e. that nothing was
  hand-edited into a generated file.
- **Eight concurrent-session paths that are not this cycle's work**, listed in the plan's
  `## Baseline-dirty out-of-scope files` and re-measured unchanged here:
  `docs/SPECS/spec-042-debug_toolbar-0_0_14.md`, `docs/SPECS/spec-043-test_client-0_0_14.md`,
  `docs/SPECS/spec-044-debug_extension-0_0_14.md`, `docs/SPECS/spec-050-debug_extraction-0_0_19.md`,
  `docs/SPECS/spec-051-boundary_dry_squeeze-0_0_20.md`, `examples/fakeshop/test_query/README.md`, and
  the `KANBAN.md` / `KANBAN.html` / `db.sqlite3` share of the mixed diff above. **No worker edited,
  reverted, or checked out any of them.**
- **Nothing else.** No package source, no test, no `examples/` code, no `CHANGELOG.md`, no sibling
  spec, no terms CSV, and no `scripts/` entry was touched by this cycle.

### Files this cycle produces for the commit

- `docs/SPECS/spec-002-optimizer-0_0_2.md` (modified, 7,398 -> 9,844)
- `docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md` (new, 33,620)
- `docs/builder/build-002-optimizer-0_0_2.md` (new)
- `docs/builder/bld-002-r1-rationale_move.md` (new)
- `docs/builder/bld-002-r2-spec_reconciliation.md` (new)
- `docs/builder/bld-002-r3-doc_completion_archive.md` (new)
- `docs/builder/bld-002-final.md` (new, this file)
- the one-row `CardItem.text` share of `examples/fakeshop/db.sqlite3` / `KANBAN.md` / `KANBAN.html`

---

## Spec changes made (Worker 1 only)

**`docs/SPECS/spec-002-optimizer-0_0_2.md` — no change at this gate.** 9,844 bytes / 103 lines,
byte-identical to R2's close and to what R3 verified. The gate exposed no defect in it: all fifteen
commands passed, the anchor map is 1/1/2, the link audit is 4/4 with every count zero, the status-line
obligation has nothing to falsify, and no raw `path:NN` reference exists in the file.

**`docs/SPECS/appx/spec-002-optimizer-0_0_2-rationale.md` — no change at this gate.** 33,620 bytes,
byte-identical to R2's close. The link audit is 19/19 with every count zero and every fragment
resolving.

**No deferral reason is owed under this heading.** No checklist box in any of the three item artifacts
is `- [ ]`, and none was un-ticked. The deferrals this cycle carries are not checklist boxes — they
are the eight catalog items above, every one with a named owner.

## Final status

`final-accepted`.

Fifteen gate commands, fifteen passes: the full three-tree sweep (`5635 passed, 40 skipped`), both
Django consistency checks, the three read-only lint/format/diff gates, and the nine documentation
constraint commands, plus three generator `--check` runs and an independently written link audit.
Floor-verification scope is `none` and correctly so, so the gate owes no floor run and built no floor
venv. Hot path: none. Failability proofs: none owed — the cycle introduced no boundary. The plan's
baseline exception was available and **unused**: no command failed, in this cycle's files or in the
concurrent session's.

The cycle delivered the missing rationale companion, a spec reconciled against the shipped package,
and one board correction — and it found the archive already sound, so it confirmed the archive rather
than performing it. Eight deferrals are catalogued, each re-verified by execution at this gate and each
with a named owner or an explicit "closed". The cycle is complete and ready for the maintainer's review
and commit.
