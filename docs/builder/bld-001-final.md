# Build: Final test-run gate — spec-001 residual-completion cycle

Spec reference: `docs/SPECS/spec-001-django_types-0_0_1.md` (whole file), companion
`docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md`
Build plan: `docs/builder/build-001-django_types-0_0_1.md` (final checklist line)
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
artifact was read **in full and in order** before any gate command was interpreted:

| Artifact | Lines | Status as read | What it delivered |
|---|---|---|---|
| `docs/builder/build-001-django_types-0_0_1.md` | 211 | R1/R2/R3 `- [x]`, final gate `- [ ]` | the plan, its three deviations, the 15-row verified drift floor, the 21-anchor constraint, and the **baseline exception** this gate is governed by |
| `docs/builder/bld-001-r1-rationale_move.md` | 1,267 | `final-accepted` | the rationale extraction: 17 removed passages, all located in the companion; spec `52,341 -> 42,483` bytes |
| `docs/builder/bld-001-r2-spec_reconciliation.md` | 3,060 | `final-accepted` | 18 drift rows reconciled across 3 build passes + 3 reviews + an end-to-end read; 5 illustrative code blocks deleted; `## Current state` -> `## Prior art` |
| `docs/builder/bld-001-r3-doc_completion_archive.md` | 2,182 | `final-accepted` | the consumer-doc corrections (`TODAY.md`, `docs/README.md`), the 3-direction archive audit, the `spec-002` C1 pointer, and the consolidated deferral list this gate re-verifies |

Also read in full: `AGENTS.md`, `START.md`, `docs/builder/BUILD.md`, `docs/builder/ARTIFACT.md`,
`docs/builder/worker-1.md`, `docs/builder/worker-memory/worker-1.md`,
`docs/SPECS/spec-001-django_types-0_0_1.md` and its rationale companion (targeted reads against every
claim this gate re-derives), `GOAL.md`, `docs/GLOSSARY.md` and `CHANGELOG.md` (targeted reads on the
scalar-conversion surface).

**Cross-artifact findings: none that block.** The three items are sequential and non-overlapping by
construction (R1 moves deliberation, R2 reconciles contract, R3 finishes consumer docs and audits the
archive), each closed `final-accepted` by an independent Worker 1 spawn, and each later item's opening
pass re-measured the prior item's handoff rather than inheriting it. The two shared-shape risks a
concurrent-cohort build would have — a duplicated helper and a duplicated constant — cannot arise:
**this cycle writes no `.py` file at all.** The one live document-level duplication risk (a fact told
twice across the spec and its rationale) was measured three times by shingle scan across the cycle and
is recorded, with its one deliberate exception, in the catalog below.

**Staged-anchor sweep: confirmed run in R3, result recorded, and re-run here as corroboration.**
R3's build report box D1 records `2 occurrences / 1 matching line / 1 file`, correcting its own plan's
predicted `1`; Worker 3 and R3's final verification each re-derived `2` independently. Re-run at this
gate from the repository root:

```
$ grep -rEo 'TODO\(spec-001|TODO-(ALPHA|BETA|STABLE)-001' . \
    --exclude-dir=.git --exclude-dir=dist --exclude-dir=node_modules --exclude-dir=.venv \
    --exclude-dir=docs/shadow --exclude=KANBAN.md --exclude=KANBAN.html --exclude=BACKLOG.md | wc -l
2

$ grep -rEn 'TODO\(spec-001|TODO-(ALPHA|BETA|STABLE)-001' django_strawberry_framework/ tests/ examples/ | wc -l
0
```

Both occurrences are on `docs/builder/build-001-django_types-0_0_1.md:187` — the plan's own R3
checklist line, which names both patterns in one sentence. That is a per-cycle artifact, not shipped
source. **Zero staged anchors in package source, `tests/`, or `examples/`**, so the
`revision-needed` trigger does not fire.

---

## Working-tree state, measured at this gate's open and again at its close

`AGENTS.md` rule 34 and the plan's baseline exception both turn on this, so it is measured twice and
both readings are recorded. HEAD is `fdfb711f` at both.

**Open and close are identical — 16 paths, 11 modified and 5 untracked:**

```
 M KANBAN.html                                        <- concurrent (spec-049 card wrap)
 M KANBAN.md                                          <- concurrent (spec-049 card wrap)
 M SECURITY.md                                        <- concurrent (spec-049)
 M TODAY.md                                           <- THIS CYCLE (R3 F1) + one concurrent hunk at :381
 M docs/GLOSSARY.md                                   <- concurrent (spec-049 card wrap)
 M docs/README.md                                     <- THIS CYCLE (R3 F2)
 M docs/SPECS/spec-001-django_types-0_0_1.md          <- THIS CYCLE (R1 + R2)
 M docs/SPECS/spec-002-optimizer-0_0_2.md             <- THIS CYCLE (R3 C1)
 M docs/spec-049-dependency_ci_hardening-0_0_14.md    <- concurrent
 M examples/fakeshop/db.sqlite3                       <- concurrent
 M uv.lock                                            <- concurrent (spec-049 dependency work)
?? docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md   <- THIS CYCLE (R1 + R2)
?? docs/builder/build-001-django_types-0_0_1.md               <- THIS CYCLE
?? docs/builder/bld-001-r1-rationale_move.md                  <- THIS CYCLE
?? docs/builder/bld-001-r2-spec_reconciliation.md             <- THIS CYCLE
?? docs/builder/bld-001-r3-doc_completion_archive.md          <- THIS CYCLE
```

`docs/builder/bld-001-final.md` (this file) is this gate's sixth cycle path and appears only after it
is written. **Nothing was reverted, checked out, restored, or stashed by this pass**, and this pass
wrote exactly two files: this artifact and `docs/builder/worker-memory/worker-1.md` (gitignored).

The membership matches the seven concurrent paths named in this gate's dispatch exactly
(`examples/fakeshop/db.sqlite3`, `KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md`,
`docs/spec-049-dependency_ci_hardening-0_0_14.md`, `SECURITY.md`, `uv.lock`) plus the one concurrent
line in `TODAY.md`.

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

**The known Django-6.1 hazard did not materialise, and that is a reading, not an assumption.** The
shared `.venv` carries Django **6.1** against an open-ended `Django>=5.2.16` in `pyproject.toml`; the
concurrent session's spec-049 work is dependency/CI hardening and `uv.lock` is dirty, so the resolved
set is theirs, not this cycle's. Every gate command below nonetheless completed green, including
`manage.py check`, which is where a fail-closed `AppConfig.ready()` guard would have surfaced. No
failure is attributable to the environment, so the hazard is recorded as checked-and-clear rather than
invoked.

---

## Gate commands (`BUILD.md` `## Final test-run gate`, in order)

| # | Command | Result | Evidence |
|---|---|---|---|
| 1 | `uv run pytest --no-cov` | **PASS** (exit 0) | `5635 passed, 40 skipped in 288.03s (0:04:48)` |
| 2 | `uv run python examples/fakeshop/manage.py check` | **PASS** (exit 0) | `System check identified no issues (0 silenced).` |
| 3 | `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` | **PASS** (exit 0) | `No changes detected` |
| 4 | `uv run ruff format --check .` | **PASS** (exit 0) | `418 files already formatted` |
| 5 | `uv run ruff check .` | **PASS** (exit 0) | `All checks passed!` |
| 6 | `git diff --check` | **PASS** (exit 0) | no output; re-run at gate close, still exit 0 |

Notes on the readings, so a later reader can re-derive rather than trust them:

- **`--no-cov` is the only coverage-shaped flag used anywhere in this pass.** `pytest.ini`'s `addopts`
  auto-applies `--cov`, so plain `uv run pytest` would have been a coverage run and is forbidden
  (`BUILD.md` `## Coverage is the maintainer's gate, not a worker's tool`). **No line coverage was
  inspected or asserted**, and the only requirement taken from the sweep is that it passes.
- The sweep is the **full** three-tree run — package `tests/`, per-app `examples/fakeshop/apps/*/tests/`,
  and live `examples/fakeshop/test_query/` — under `xdist` (`gw0`-`gw7` in the transcript), which is the
  configuration `BUILD.md` `### Example-project schema changes must sync every schema-module list` names
  as the only one that can expose an order-dependent registry collision. The 40 skips are the standing
  `FAKESHOP_SHARDED`-gated set plus soft-dependency guards (`AGENTS.md` 30); no skip is new to this cycle,
  which writes no test.
- **`ruff format --check` and `ruff check` were run read-only over `.`** — never `--fix`. Running them
  repo-wide is what the gate requires and is safe *because* they are read-only; a write-mode run would
  have swept the concurrent session's eight paths.
- `git diff --check` covers the whole tree, this cycle's five tracked edits and the concurrent
  session's seven alike, and reports no whitespace error and no conflict marker anywhere.

### Documentation constraint commands (re-run because this cycle's whole deliverable is documentation)

| Command | Result | Output |
|---|---|---|
| `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-001-django_types-0_0_1.md` | **PASS** (exit 0) | `OK: 21 terms - all have glossary entries and at least one spec link.` |
| `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-002-optimizer-0_0_2.md` | **PASS** (exit 0) | `OK: 3 terms - all have glossary entries and at least one spec link.` |
| `uv run python examples/fakeshop/manage.py import_spec_terms --check` | **PASS** (exit 0) | `OK: 49 done cards have glossary links.` |

**Exit 0 is the gate; `49` is not.** The done-card number read `48` when the build plan was written and
`49` from R2 onward, moved by the concurrent session's `DONE-049-0.0.14` card wrap. The property the
command actually asserts — that every done card, `DONE-001-0.0.1` included, still has its glossary
links — holds on both sides of that change. The number is recorded so a later pass quoting the plan's
`48` does not waste time deciding whether something broke.

The 21-term reading is the constraint the whole cycle was run against: all 21 anchors in
`docs/SPECS/appx/spec-001-django_types-0_0_1-terms.csv` still resolve, and the terms CSV was never
edited to buy one.

## Floor verification

**No floor-verification scope declared.**

The build plan's preamble declares `Floor-verification scope: none`, and the declaration is correct
rather than merely present: no residual item touches a Django / Strawberry / channels integration seam
— request/response handling, view or ASGI plumbing, upload or body parsing, session/auth, queryset or
expression compilation, schema and type construction against Strawberry internals, or consumer
middleware wiring. **No `.py` file was written in this cycle at all**; the complete write set is five
Markdown files plus five `docs/builder/` artifacts. R1, R2 (all three passes), and R3 each recorded
`Not applicable; plan declares floor-verification scope none.` in their `### Floor verification`
sections, so there is no floor run that a pass owed and skipped.

**No floor venv was built by this gate**, per the dispatch, and the shared `.venv` was not mutated by
any command above (all six are read-only or test-only; `uv run` resolved the existing environment).

## Failability proofs

`None; this cycle introduced no new boundary.` Audited across all three items: the entire cycle diff is
Markdown. There is no guard, cap, gate, rejection path, or validation branch whose removal a test could
fail on, so the mandatory re-run floor is arithmetic on an empty set rather than a waived obligation.
Equally, there is no fail-open **shape** to read for — a fail-open expression needs executable code, and
the diff has none.

## Hot-path budget

`Not applicable; plan declares no hot path.` The build plan declares `Hot-path declaration: none`
cycle-wide, and nothing this cycle wrote runs per request, per resolver, per row, per connection, or
per outbound message.

---

## The baseline exception, and what it had to govern

The plan's preamble carries it, which is what `BUILD.md` `## Final test-run gate` requires for it to be
honoured:

> A failure attributable to a file this cycle never wrote does **not** block `final-accepted` and does
> **not** route back through a residual item's loop; it is reported to the maintainer. The gate still
> reports each command's real result — the exception governs what a result *blocks*, never whether it is
> recorded honestly.

**It was not needed. Every one of the nine commands above passed, so there is no failure to attribute
in either direction** — none against a concurrent-session file, and none against this cycle's own
writes. Recorded rather than omitted, because "the exception was available and unused" and "the
exception was quietly relied on" are different states and only the first is provable by a green board.

Had a failure occurred, this cycle's own writes — the only set that could have routed back through an
item loop — are exactly:

`docs/SPECS/spec-001-django_types-0_0_1.md`, `docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md`,
`docs/SPECS/spec-002-optimizer-0_0_2.md`, `TODAY.md` (the `## Package scalar conversions` region only),
`docs/README.md` (line 99 only), and the `docs/builder/` artifacts.

One attribution worth stating positively while the tree is still mixed: **`TODAY.md` carries hunks from
both sessions.** R3's edits are at `:157`, `:162`, and the `<!-- docs/ -->` link-definition group; the
concurrent session's is the single line at `:381` (a `065` -> `DONE-046` card renumber). R3 proved the
two regions disjoint by `git show HEAD:TODAY.md`, and this gate re-confirms the file is dirty in both
directions. The maintainer receives one mixed diff there and nowhere else.

---

## Item statuses and checklist audit

| Plan checklist line | Artifact | Status | Boxes |
|---|---|---|---|
| R1 — rationale extraction | `bld-001-r1-rationale_move.md` | `final-accepted` | 11 of 11 `- [x]`, audited at R1's final verification |
| R2 — spec-versus-HEAD reconciliation | `bld-001-r2-spec_reconciliation.md` | `final-accepted` | 20 of 21 `- [x]`; **D13 `- [ ]`** with a durable deferral reason (catalog item 6) |
| R3 — documentation completion and archive audit | `bld-001-r3-doc_completion_archive.md` | `final-accepted` | 16 of 16 `- [x]`, audited twice (Worker 3, then R3's final verification) |
| Final test-run gate | this file | `final-accepted` | — |

The one open box is D13, and **no work is owed by it**: its contract — that the spec no longer claims
fakeshop declares no M2M field — was discharged by R1's rationale move rather than by R2's diff, and
`BUILD.md` `### Dispatched findings checklist` reserves the tick for a box whose fix landed in *its own*
diff. The durable reason lives in a tracked file that ships with the spec
(`docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md` `### Drift rows that changed nothing, and
why`, confirmed present at `:852` this pass), not only in the per-cycle artifact.

Each item's status was set by an independent Worker 1 spawn after an independent Worker 3 review. No
box audit was re-opened by this gate; `BUILD.md` gives the gate the commands and the catalog, not a
fourth review of settled items.

---

## Deferred work catalog

The next spec author's reading list. R3's final verification consolidated nine items; **each was
re-verified as still true at this gate by the command quoted, not lifted on trust** — a catalogued
deferral carried forward without re-checking is how a closed item gets reported as open. Two further
items that earlier artifacts recorded and R3's consolidation did not carry are added as 10 and 11.

1. **Live bug: `scripts/check_spec_glossary.py::github_anchor` slugs heading text without rendering
   link markup first.** *Source: `bld-001-r2` `### Notes for Worker 1` item 8; `bld-001-r3` plan
   `### Implementation discretion items` and review `### Notes for Worker 1` item 2. No spec line
   licenses the deferral; `scripts/` is outside this cycle's write set.* **Re-verified by execution at
   this gate**, not by reading:
   `github_anchor("[Scalar field conversion][glossary-scalar-field-conversion]")` returns
   `scalar-field-conversionglossary-scalar-field-conversion` — brackets stripped as non-word characters
   instead of the link being rendered — where the correct slug is `scalar-field-conversion`. **Blast
   radius re-measured, so the priority is neither overstated nor waved away: `docs/GLOSSARY.md` carries
   `0` headings with link markup, so the shipped `check_spec_glossary` run is unaffected today; `7`
   headings under `docs/SPECS/` carry it**, `docs/SPECS/spec-001-django_types-0_0_1.md:142` among them,
   so any tool reusing the function on a spec heading gets a false negative. Fix is two lines (render
   `[text][ref]` and `[text](url)` to `text` before slugging). **Owner: maintainer.**
2. **Promote one corrected link / anchor / overlap checker into `scripts/`.** *Source: `bld-001-r1`
   `### Notes for Worker 1` item 11; `bld-001-r2` `### Notes for Worker 1` item 4; `bld-001-r3` review
   `### Temp test verification`. Out of the cycle's write set for the same reason as item 1.*
   **Re-verified: `ls scripts/` matches nothing on `link|anchor|overlap|shingle`** — no such helper
   exists, and every pass in this cycle hand-wrote its own private implementation under
   `docs/builder/temp-tests/` (gitignored). Item 1 is the concrete defect that repetition keeps routing
   around, so the two are one piece of work. The checks every spec-plus-rationale pair now owes: link
   scaffold (defs / uses / undefined / orphan), the 10 canonical group headers in **positional** order,
   alphabetical order within group, on-disk resolution of every def target with the fragment stripped
   **and URLs excluded**, in-page anchors on a slugger that renders link markup before slugging, an
   inline-cross-file-link sweep, a rule-27 raw-`path:NN` sweep, and a maximal-shared-shingle scan — the
   only thing that turns *"it was a move, not a copy"* into a measurement. **Owner: maintainer** (new
   scope).
3. **Pre-existing `AGENTS.md` rule-27 violation: raw `path:NN` at
   `docs/SPECS/spec-002-optimizer-0_0_2.md:72`.** *Source: `bld-001-r3` spec-002 pass
   `### Notes for Worker 1` item 1; review item 2.* The `## References` bullet reads
   ``graphene-django relation resolver wrap: `…/site-packages/graphene_django/converter.py:308-471`.``
   **Re-verified byte-identical at HEAD this gate** (`git show HEAD:… | sed -n '72p'` matches the
   worktree line exactly), so it is **not this cycle's regression**. Not fixed because the
   symbol-qualified replacement names a symbol in an upstream package outside this repo — real work with
   a real chance of naming the wrong symbol, this cycle's catalogued failure mode. **Owner: a future
   spec-002 cycle's Worker 1, or the maintainer.**
4. **Test-surface gap: nothing pins `OptimizerHint.prefetch(obj)`'s interaction with a custom
   `get_queryset`.** *Source: `bld-001-r2` `### Notes for Worker 1` item 3. Licensed by the build plan's
   build-wide context flag "No source or test file changes in this cycle".* **Re-verified at this gate:
   `tests/optimizer/test_hints.py` contains `0` occurrences of `get_queryset`**, and
   `django_strawberry_framework/optimizer/hints.py:198` defines `prefetch(cls, obj: Prefetch)`. The
   behaviour is **deliberate** — a consumer-supplied `Prefetch` is used verbatim, so the hinted child
   queryset bypasses `utils/querysets.py::apply_type_visibility_sync`
   (`optimizer/walker.py::_apply_hint` #"Consumer-supplied Prefetch objects commonly close over") — and
   it is unpinned in **either** direction. An unpinned deliberate divergence on a data-isolation path is
   indistinguishable from a bug to the next reader, which is exactly why a row asserting it is cheap
   insurance against a future refactor "fixing" it silently. Worker 3's evidence is
   `docs/builder/temp-tests/r2b2-spec001/test_hint_visibility.py` (gitignored; two rows, one a positive
   control). **Owner: the next optimizer cycle, or a maintainer call — never a spec-001 item.**
5. **Binding constraint on any later cycle that re-homes the two lifted optimizer rules into
   `spec-002`.** *Source: `bld-001-r1` item 4; `bld-001-r2` `### Notes for Worker 1` item 1, last
   bullet; `bld-001-r3` spec-002 pass.* The O5 `only()` reason
   (`docs/SPECS/spec-001-django_types-0_0_1.md:349`) and the O6 every-`Prefetch` visibility clause
   (`:357`) sit beside the PR #583 carve-out (`:351`) that is their reason. **Those three are one
   decision:** a cycle moving them must re-home the carve-out with them and delete all three from
   spec-001 **in the same change**, or the duplication R2 exists to remove comes straight back.
   **Re-verified present at this gate**, in bold, at
   `docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md:710-711` (*"it must re-home the PR #583
   carve-out with them and delete all three from spec-001 in the same change"*), and all three spec
   lines re-read on disk. **Owner: whoever opens the next spec-002 cycle.**
6. **Drift row D13 — the cycle's one checklist box that closed `- [ ]`, and no work is owed.**
   *Source: `bld-001-r2` `### Spec changes made (Worker 1 only)` and its checklist audit.* **Re-verified:
   the box reads `- [ ] **D13**` at `bld-001-r2-spec_reconciliation.md:248`, and the durable reason is
   present at `docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md:852`**
   (`### Drift rows that changed nothing, and why`), carrying the HEAD evidence. The row's contract was
   discharged by R1's rationale move, so the box records what actually happened rather than claiming a
   diff it did not have. Listed so a later reader does not mistake an open box for open work.
   **No owner; closed.**
7. **`TODAY.md`'s scalar list is a documented subset, deliberately.** *Source: `bld-001-r3` build report
   `### Notes for Worker 1` item 2; review item 4.* **Re-verified at this gate**: the lead-in at
   `TODAY.md:152` reads *"`DjangoType` converts these model fields to Strawberry scalars"* — not
   *"only these"* — and the list names a subset of `SCALAR_MAP`'s 26 keys while generalizing the rest.
   **Not drift and not an omission.** Expanding it into a 26-row table would recreate exactly the
   doc-to-doc duplication that put `TODAY.md` out of step with the package in the first place. If a
   later cycle wants it settled either way, the site is that lead-in sentence, never the spec.
   **Recorded so it is not "fixed".**
8. **Examined and explicitly not a defect: `django_strawberry_framework/filters/sets.py:330` maps
   `models.DurationField -> DurationFilter`.** *Source: `bld-001-r3` review `### Sibling sweep`.*
   **Re-verified present at that line this gate.** It reads as contradicting the corrected consumer docs
   and does not: the row is a deliberate mirror of django-filter's own table and becomes reachable
   exactly when a consumer registers the `SCALAR_MAP[DurationField]` entry the corrected docs tell them
   to register. **Recorded so a later sweep does not re-flag it.**
9. **Process lesson for whoever reconciles the next spec.** *Source: `bld-001-r2`
   `### Notes for Worker 1` item 9.* A reconciliation organized by **claim** cannot see a contradiction
   between two **sections** — it belongs to no drift row, no finding, and no diff hunk — and neither can
   a review auditing the same fragments. **Read the whole document once, in order, at the end.** R2's
   gate did, in one pass, and found a defect three builds and three reviews had each looked straight
   past, in text they had themselves written. Belongs to closeout rather than to a future card, and is
   recorded here because closeout reads this file.
10. **`docs/SPECS/spec-002-optimizer-0_0_2.md` carries two status-shaped sections of the shape R2
    retired from spec-001.** *Source: `bld-001-r3` final verification `### Spec status-line
    re-verification — both specs` — recorded there, not carried into R3's own consolidation, which is
    why it is added here.* **Re-verified at this gate**: `grep '^## '` over spec-002 returns
    `## Current state` (`:16`) and `## Visibility status` (`:63`). **Both are accurate at HEAD today** —
    R3 checked them against `django_strawberry_framework/__init__.py`'s `DjangoOptimizerExtension`
    re-export, the existence of `optimizer/walker.py`, and spec-002's own six `- [x]` implementation
    boxes — so **nothing is wrong now**. The deferral is the standing-promise shape itself: R2 retitled
    spec-001's `## Current state` to `## Prior art` on the reasoning that *a section named for the
    present is a promise no shipped spec can keep*, and spec-002 has not had that treatment. Out of this
    cycle's write set (spec-002 was opened only for the C1 pointer). **Owner: the next spec-002 cycle's
    Worker 1.** Note the same trap R2 hit: an in-page anchor rename is a breaking change if a sibling
    file cites it.
11. **Measured spec-versus-rationale overlap residue, accepted rather than resolved.** *Source:
    `bld-001-r2` Worker 3 pass 1 `### DRY findings` and R2's final verification
    `### Division of labour between the two documents`.* Three shingle scans across the cycle put the
    shared text at ~4.5% of the spec body, and two classes were recorded as **deliberately kept**: the
    `typing.Any` reason clause, which `BUILD.md`'s reader rule (the rationale must say why an
    alternative lost) and `worker-1.md`'s implementation-relevant-why carve-out (a builder never reads
    the rationale) both claim — **re-verified this gate at rationale `:105-110`**, where the entry states
    the disposition explicitly — and four *pure-restatement* runs (cache-check ordering, `Meta.primary`
    many-to-one, the plan-cache clause, the `ChoiceFixture` mechanism) that two review passes and R2's
    gate each read and recorded as *the minimal contrast a "claims the spec no longer makes" entry
    cannot avoid*. **This is a recorded acceptance, not an open defect**, and it is carried here only so
    the next rationale extraction has a baseline number and does not re-litigate a settled disposition.
    **No owner; accepted.**

*(Two facts earlier artifacts flagged are deliberately **not** carried: the 21-anchor budget and the
`import_spec_terms` done-card number. Both are standing invariants re-measured every pass — and both are
re-measured above — not deferred work.)*

---

## Handoff to the maintainer

### What this cycle delivered

`spec-001-django_types-0_0_1` shipped at `0.0.1` and the package is at `0.0.14`. This cycle produced the
deliverable set that shipped cycle never made, plus the reconciliation fifty-odd later specs had made
necessary. Three sequential items, each planned, performed, independently reviewed, and independently
final-verified:

- **R1 — the missing rationale companion.** `docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md`
  did not exist; `BUILD.md` `## Spec rationale extraction` makes the move pre-flight step 7 and the
  shipped cycle predates the rule. Eight whole sections' worth of deliberation — the scope-creep
  argument, four "deviation from earlier draft" chronologies, every slice `Status:` annotation,
  `## Post-slice-7 future work`, `## Open questions` — was **cut**, not copied, into a keyed companion,
  and the spec dropped from `52,341` to `42,483` bytes. The implementation-relevant carve-out
  (`worker-1.md`'s one named way this move can itself cause a defect) held: the PR #583 paragraph —
  *otherwise FK joins bypass per-type visibility filtering and leak rows* — stayed in the spec.
- **R2 — the spec now describes the package that exists.** Eighteen drift rows discharged: fifteen from
  the plan's verified floor and **three the pass found itself** by reading the spec end to end rather
  than working the table. The most consumer-visible is D17: the spec promised GraphQL mappings for
  `DurationField` and `BinaryField`, both of which in fact fail closed at schema build. Five illustrative
  code blocks — each a stale second copy of a module, two of them naming a `registry.lazy_ref` the
  registry has never had — were deleted behind symbol-qualified pointers. `## Current state`, a heading
  no shipped spec can keep, became `## Prior art`, and its six glossary anchors were re-sited into
  contract prose without the anchor budget ever dropping below one link. Two optimizer rules that the
  lift to `spec-002` would have left stated in **no** document were restored as contract, re-derived
  against `optimizer/walker.py` rather than restored verbatim — which caught a sentence that was false
  at HEAD.
- **R3 — the consumer-facing documentation, and the archive audit.** The archive had already landed, and
  every leg of it verified green in all three cross-reference directions, in the kanban DB, and in the
  terms-CSV chain. The real finding was elsewhere: `TODAY.md` promised `DurationField -> Python-native
  time types` and `BinaryField -> bytes`, and `docs/README.md` listed `binary` among shipped scalar
  conversions — the same falsehood R2 had just corrected in the spec, still live in the two files a
  consumer actually reads, and files no earlier pass in this cycle had opened. Both corrected, with the
  raise proved at **type creation** by building real `DjangoType` subclasses rather than by a missing
  dict key. One genuine dangling reference in `spec-002` (a prediction R1 had moved) was fixed with a
  pointer in that file's own register; a second alleged dangle was **verified to resolve** and correctly
  left alone.

The cycle's own quality signal: three build passes and three reviews on R2 closed nine, three, and zero
findings; R3's review closed zero High/Medium/Low with one DRY finding escalated and then applied. Every
mechanical claim in every artifact was re-derived by the next pass rather than inherited — a discipline
that cost the cycle roughly a dozen asserted counts and is the reason the numbers in these artifacts can
be trusted.

### What this cycle deliberately did **not** do

- **It changed no package source, no test, and nothing under `examples/`.** The plan's build-wide context
  flags forbid it; the complete write set is Markdown. The one conditional source touch R3 was authorized
  to make (a factually false module docstring) was not owed — `build_tree_md.py --check` is clean — and
  was not made.
- **It did not touch `CHANGELOG.md`** (`AGENTS.md` rule 21), `pyproject.toml`, `__init__.py`, or the
  version quintet. `0.0.1` shipped long ago; nothing here is a release.
- **It wrote no DB row and regenerated no generated doc.** `docs/GLOSSARY.md`, `KANBAN.md`,
  `KANBAN.html`, and `docs/TREE.md` were **read** and found already correct on the spec-001 surface, so
  no ORM edit or regenerate was owed. All four are dirty in the tree from the concurrent session, not
  from this cycle.
- **It did not archive the spec.** There was nothing to archive: the spec, its `-terms.csv`, the
  `SpecDoc.path` row, and every inbound reference were already at their post-archive locations before
  the cycle opened. What the cycle **did** owe the archive is the companion `AGENTS.md` rule 26 also
  names — the `-rationale.md` beside the `-terms.csv` in `appx/` — and R1 wrote it directly at the
  archived location. The archive is complete *because* R1 produced the missing companion, not merely
  because the earlier move happened to be right.
- **It resolved none of the eleven catalogued deferrals**, each of which is out of the cycle's write set
  by construction (`scripts/`, `tests/`, `spec-002`'s prose beyond one pointer) and owned by a maintainer
  or a named future cycle.

### The boundary R3 drew, restated verbatim because it is the sentence most easily over-read

> **"finished" means the spec-001 surface as enumerated by R2's drift rows plus the scalar /
> file-output / relation claims in the four consumer docs. This item did not re-audit documentation
> unrelated to spec-001, and does not assert it is correct.**

So: the maintainer's brief — *"the documentation needs to be finished and then the spec needs to be
archived"* — is answered **for the spec-001 surface**. `README.md` and `GOAL.md` were swept for that
surface and are genuinely zero on every token (measured, not assumed), and were therefore correctly left
unedited; that is not a claim that the rest of their content was audited. It was not.

### Files the maintainer will be committing

This cycle's writes, and nothing else. `docs/builder/worker-memory/` and `docs/builder/temp-tests/` are
gitignored and are not part of the diff.

| File | State | Owner item |
|---|---|---|
| `docs/SPECS/spec-001-django_types-0_0_1.md` | modified | R1 + R2 |
| `docs/SPECS/appx/spec-001-django_types-0_0_1-rationale.md` | **new** (untracked) | R1 + R2 |
| `docs/SPECS/spec-002-optimizer-0_0_2.md` | modified (one inserted sentence) | R3 (C1) |
| `TODAY.md` | modified — **`## Package scalar conversions` region only; the file also carries one concurrent hunk at `:381`** | R3 (F1) |
| `docs/README.md` | modified (line 99) | R3 (F2) |
| `docs/builder/build-001-django_types-0_0_1.md` | **new** (untracked) | Worker 0 |
| `docs/builder/bld-001-r1-rationale_move.md` | **new** (untracked) | R1 |
| `docs/builder/bld-001-r2-spec_reconciliation.md` | **new** (untracked) | R2 |
| `docs/builder/bld-001-r3-doc_completion_archive.md` | **new** (untracked) | R3 |
| `docs/builder/bld-001-final.md` | **new** (untracked) | this gate |

**Not this cycle's — do not attribute these to the build** (`AGENTS.md` rule 34; none was edited or
reverted by any pass): `KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md`, `SECURITY.md`, `uv.lock`,
`docs/spec-049-dependency_ci_hardening-0_0_14.md`, `examples/fakeshop/db.sqlite3`, and the single
`TODAY.md` line at `:381`. They are the concurrent session's in-flight spec-049 dependency/CI-hardening
cycle. **`git add <path>` explicitly; never `git add -A`** (`START.md` "Concurrent sessions").

One consequence of that mix, stated so it is not discovered at commit time: **`TODAY.md` is the one file
whose diff belongs to both sessions.** Everything else separates cleanly along the table above.

---

## Final status

`final-accepted`.

All six gate commands and all three documentation constraint commands pass with exit 0, on a tree that
carries a concurrent session's uncommitted work throughout. The baseline exception was available and
**unused** — nothing failed, so nothing had to be excused. The floor declaration is `none` and is
correct: no `.py` file was written and no framework seam was touched, so no floor run was owed and none
was skipped. The staged-anchor sweep ran in R3 with its result recorded and re-derives identically here:
two occurrences, both in this cycle's own plan text, zero in shipped source. Every prior artifact was
read in full and in order; the cross-artifact scan finds no duplication to consolidate, because a cycle
that writes no code cannot create any. Eleven deferrals are catalogued, each re-verified by execution at
this gate rather than lifted on trust, each with a named owner or an explicit "closed / accepted".

The cycle is complete and ready for the maintainer's review and commit.
