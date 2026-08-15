# Build: Final test-run gate — spec-008 residual-completion cycle

Spec reference: `docs/SPECS/spec-008-definition_order_independence-0_0_4.md` (post-R2, whole file)
Status: final-accepted

Plan source: `docs/builder/build-008-definition_order_independence-0_0_4.md` `## Checklist` (final row)
and `## Baseline-dirty out-of-scope files` (the baseline exception at `:285`).
Handoff consumed: `docs/builder/bld-008-r3-doc_completion_archive.md` `### Notes for Worker 1`,
sections A-E (`:1551`-`:1630`).
Prior artifacts read before this pass, in cycle order (`BUILD.md` `## Cross-slice integration pass`,
"every artifact is required context" — no "as needed"): `bld-008-r1-rationale_move.md`,
`bld-008-r2-spec_reconciliation.md`, `bld-008-r2b-source_attribution.md`,
`bld-008-r3-doc_completion_archive.md`. All four carry header `Status: final-accepted`, verified by
reading each header block rather than by trusting the plan's checklist.

Gate environment, re-derived at this pass rather than quoted: `HEAD` =
`947f74948c16b20b0c15ff359bb53fbe462d4b8c` (`git rev-parse HEAD`) — unmoved through every pass of this
cycle. Working tree = **52** entries (`git status --short | wc -l`; unit: status lines), the same
figure R3 recorded, so the baseline did not move under this gate.

## Plan (Worker 1)

### Dispatched findings checklist

This is the gate, not a slice; the checklist is the six gate commands `BUILD.md` `## Final test-run
gate` prescribes, plus the floor determination it requires as a backstop.

- [x] `uv run pytest --no-cov` — full sweep across all three test trees
- [x] `uv run python examples/fakeshop/manage.py check`
- [x] `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run`
- [x] `uv run ruff format --check .` (read-only; never `--fix`)
- [x] `uv run ruff check .` (read-only)
- [x] `git diff --check`
- [x] Floor verification — plan declares scope `none`; the determination is **confirmed**, not re-run

---

## Build report (Worker 1)

### The six gate commands, each with its real result

Every command was run from the repository root in the shared `.venv` and its result recorded as it
completed. **No coverage-shaped flag other than `--no-cov` was used**, and no coverage figure was
inspected or asserted anywhere in this pass (`BUILD.md` `## Coverage is the maintainer's gate, not a
worker's tool`).

| # | Command | Exit | Result |
|---|---|---|---|
| 1 | `uv run pytest --no-cov` | 0 | **PASS** — `5651 passed, 40 skipped in 90.11s` |
| 2 | `uv run python examples/fakeshop/manage.py check` | 0 | **PASS** — `System check identified no issues (0 silenced).` |
| 3 | `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` | 0 | **PASS** — `No changes detected` |
| 4 | `uv run ruff format --check .` | 0 | **PASS** — `418 files already formatted` |
| 5 | `uv run ruff check .` | 0 | **PASS** — `All checks passed!` |
| 6 | `git diff --check` | 0 | **PASS** — no output (no whitespace error, no conflict marker) |

**Derivations for the two counts stated above**, so neither reads as measured-by-assertion:

- `5651 passed, 40 skipped` is pytest's own summary line, quoted verbatim from the run log, not
  recomposed from a node-id count. **Failures and errors independently counted at zero**:
  `grep -cE '^(FAILED|ERROR)' <run log>` -> **0** (unit: summary lines emitted by pytest for failing
  or erroring nodes). The two numbers agree, which is the check a bare summary quote skips.
- `418 files already formatted` is ruff's own output line (unit: files), quoted verbatim. Command 4
  also emits a standing `COM812`-vs-formatter advisory warning on **every** invocation in this repo;
  it is configuration advice, not a finding, and does not affect the exit status.

### Failures, and the attribution work the baseline exception requires

**There were none.** Zero failing test node ids, zero collection or setup errors, zero lint findings,
zero format diffs, zero whitespace/conflict-marker hits across all six commands.

This is worth stating precisely rather than as a bare "green", because the plan's baseline exception
(`build-008-definition_order_independence-0_0_4.md:285`) is the gate's central judgement and it was
**never exercised**. Every one of the six commands reads the **whole tree**, and the tree is not this
cycle's:

- **6 concurrent package sources** — `git status --short django_strawberry_framework/` -> 9 ` M`,
  minus R2b's three (`testing/relay.py`, `types/base.py`, `types/relations.py`) = **6**: five
  transport-surface (`_boundary_ordering.py`, `_cross_web_patches.py`, `_request_body.py`,
  `connection.py`, `middleware/request_body.py`) plus `conf.py`.
- **4 concurrent test files** — `tests/base/test_conf.py`, `tests/test_connection.py`,
  `tests/test_views.py`, `examples/fakeshop/test_query/test_transport_api.py`.
  (`tests/testing/test_relay.py` is R2b's and is **in-cycle**, not baseline.)
- **`docs/GLOSSARY.md`** ` M` from the concurrent re-export-index change, hunks inside lines 27-63.
- **`docs/review/`** — re-derived at this gate: **5 ` M`, 4 `??`, 0 ` D`**
  (`git status --short docs/review/ | awk '{print $1}' | sort | uniq -c`; unit: status lines).
- Plus `KANBAN.md`, `KANBAN.html`, `examples/fakeshop/db.sqlite3`, and the spec-006 / spec-007
  residual cycles' uncommitted output.

Those files ran, were parsed, were linted, and were format-checked by this gate, and **none of them
produced a failure**. So there is no result to attribute, nothing to route to the maintainer under the
exception, and nothing to route back through an item's loop. Had a failure appeared, the rule the gate
would have applied is the plan's, unchanged: **a failure attributable to a file this cycle never wrote
does not block `final-accepted` and does not re-loop an item — it is reported to the maintainer; the
exception governs what a result *blocks*, never whether it is recorded honestly.**

**The exception's scope is a property, not a list.** R3 recorded that the plan's preamble still says
"five concurrently-edited source files" while the true figure is six; `conf.py`, `_request_body.py`,
and `connection.py` appeared after the preamble was written. The scope is "a file this cycle never
wrote", so the count moving does not move the exception. This gate re-derived the count rather than
inheriting either figure.

### This cycle's diff, stated positively so attribution is possible at all

The gate's attribution rule needs a positive statement of what this cycle wrote. Verified by
`git status --short` against each path:

| Path | State | Item |
|---|---|---|
| `docs/SPECS/spec-008-definition_order_independence-0_0_4.md` | ` M` | R1 + R2 |
| `docs/SPECS/appx/spec-008-definition_order_independence-0_0_4-rationale.md` | `??` | R1 |
| `docs/SPECS/spec-001-django_types-0_0_1.md` | ` M` | R2 (partition Edit 1) |
| `docs/SPECS/spec-010-foundation-0_0_4.md` | ` M` | R2 (Edits 2-3, decisions 3, 5, 7) |
| `django_strawberry_framework/types/relations.py` | ` M` | R2b |
| `django_strawberry_framework/types/base.py` | ` M` | R2b |
| `django_strawberry_framework/testing/relay.py` | ` M` | R2b (decision 8) |
| `tests/testing/test_relay.py` | ` M` | R2b (M1 addendum) |
| `docs/builder/build-008-definition_order_independence-0_0_4.md` | `??` | plan |
| `docs/builder/bld-008-r1` / `r2` / `r2b` / `r3` / this file | `??` | artifacts |

**4 `.py` files** in this cycle's diff (unit: files; `git status --short` over the four paths above),
all four R2b's, and no other source, test, or example file anywhere in the cycle.

### Floor verification — the plan's `none` CONFIRMED, not re-run

The plan declares floor-verification scope **`none`**, on a stated condition rather than a bare
assertion: R2b's diff is comment-and-message-only, so it changes no executable line and a floor run
could not distinguish pass from fail. `BUILD.md` `## Final test-run gate` makes this gate the
**backstop that confirms it happened**, not a second owner, so what is owed here is confirmation of the
condition — which is exactly what the plan's own wording makes checkable.

**Confirmed by reading the diff, not by inheriting the claim.**
`git diff -- django_strawberry_framework/types/relations.py django_strawberry_framework/types/base.py
django_strawberry_framework/testing/relay.py` contains, in full:

- `types/relations.py` — module-docstring prose only (the `spec-014` -> spec-010/spec-018 attribution
  rewrite). Docstring text.
- `types/base.py::_build_annotations` — one `#` comment line, `spec-014` -> `spec-018`.
- `testing/relay.py` — the decision-8 remedy string, re-split across adjacent literals. A message
  **argument** changed; no operator, no branch, no call, no signature.

**No changed line is an executable statement**, and the one changed string is the case the plan named
explicitly when it declared the scope ("decision 8's error string included: a changed string is still
no changed control flow"). The `.py` file R2b also touched, `tests/testing/test_relay.py`, adds exactly
one assertion line pinning that message — a test, and a test cannot be the seam a floor run would
probe.

R3's half of the determination re-derived independently: **R3's diff contains zero `.py` files**
(`git status --short` over R3's writable set returns the artifact alone). So the floor `none` was
never merely satisfied — for R3 the condition never came into play at all.

**No floor venv was built and none is owed.** `/tmp/dsf-floor` was not created; the shared `.venv` was
not mutated by any command in this gate (all six are read-only or test-only, and none is a
`uv pip install`).

### Deferred work catalog

The next spec author's reading list. Source of truth is
`docs/builder/bld-008-r2-spec_reconciliation.md:2409` (the block headed ``**For R3's `### Deferred work
catalog`:**``), with dispositions from `bld-008-r3-doc_completion_archive.md` `## Deferred work catalog`
as corrected by its pass-2 block. Structure re-derived at this gate by reading the source block
end-to-end — **fifth independent derivation**, and it holds:

**Ten numbers, eight items: 2 CLOSED with their reasons (4, 5), 6 OPEN (1, 2, 3, 6, 7, 8), 2 standing
process carry-forward (9, 10).** Stated in that shape deliberately. A catalog that arrives as a bare
list of six open items has lost nothing visible and everything explanatory — the two closures are the
part a summariser drops, and they are what stop items 4 and 5 being re-opened by the next reader.

| # | Item | Disposition | Source |
|---|---|---|---|
| 1 | `spec-010 #"exactly as required by"`'s `spec-009 (1076-1077)` citation is stale — it resolves to the multiple-`DjangoType`s question, while the error requirement it is cited for sits at spec-009 `### Decision 6: fail loudly`, 8 lines earlier | **OPEN** — stale **at HEAD and independent of this cycle**; belongs to a future spec-009 residual cycle | R2 `:2409` item 1; R3 verified present at `spec-010:408` |
| 2 | spec-009 `### Layer 3: Finalization trigger` carries **two** inbound citations to reconcile — `(670-687)` at `spec-010:65` (restored by Edit 3) and `(1076-1077)` at `spec-010:408` | **OPEN** — both to the same future spec-009 cycle; both verified present at HEAD | R2 item 2; R3 re-verified |
| 3 | **spec-010's rule-27 debt** — raw `path:NN` citations throughout. Carry the framing, not the number: **`spec-010 #"## Note on source line references"` institutionalizes the practice**, so closing it is a conversion **plus a section retirement**, and it needs a maintainer decision authorizing spec-010 edits outside the sites decisions 1-8 name. **Not a find-and-replace.** Figures, quoted from R3's section D.1: **42 occurrences on 30 lines; 20 on 15 in-repo violations; 22 on 15 pinned third-party prior art**; two in-repo refs (`spec-010:299`, `:383`) sit inside pseudocode comments | **OPEN** — the largest item, and a maintainer decision, not a task | R2 item 3; R3 `### Item 3 in full` + D.1 |
| 4 | `testing/relay.py`'s `(or build the schema)` string | **CLOSED by R2b.** Dispatched under maintainer decision 8, delivered, and pinned at `tests/testing/test_relay.py:186`. **Not deferred work** — listing it as deferred would double-count it | R2 item 4 (as DISPATCHED); R3 advanced to CLOSED |
| 5 | `spec-010:513`'s phase-2/3 partial-mutation contract | **CLOSED as not-a-defect**, recorded so it is not re-flagged. Partial mutation is still real; only the *recovery* claim was stale, and R2 fixed that | R2 item 5 |
| 6 | Card 8's two incomplete `Verified in upstream` `CardItem`s | **OPEN as a maintainer observation** — re-verified by read-only ORM query at R3 (Audit 3); no DB write by any pass | R2 item 6; R3 Audit 3 |
| 7 | `KANBAN.md:248` names one spec too many | **OPEN as a maintainer observation** — see escalation 3 below. DB-generated; not hand-editable | R2 item 7; R3 Audit 2 |
| 8 | `docs/review/` holds an open maintainer escalation | **OPEN and unresolved** — see escalation 4 below | R2 item 8; R3 `### Item 8 in full` |
| 9 | *(Standing)* the recurring failure mode: **a pointer names the right target and the anchor lands on prose that does not carry the claim.** A resolving link is evidence about the document graph, never about the claim. The two separating tests are **subject match** and **explicit forwarding by name** | Process carry-forward, not deferred work | R2 item 9 |
| 10 | *(Standing)* the baseline-dirty count | Process carry-forward; **re-derived at this gate: 52 status lines** (R2 recorded 43, R3 49, R3 pass 2 52). The figure is re-derived every pass by contract, never carried | R2 item 10 |

**Two entries that are explicitly NOT deferrals, recorded so a future reader does not hunt for them in
the catalog:**

- **R2b's M1** — authorized and implemented *inside* this cycle; it lives at
  `tests/testing/test_relay.py:186`. Catalogue it as *where it landed*, never as open.
- **The `_PendingRelationAnnotation` / `PendingRelationAnnotation` spelling difference** between
  spec-010's pseudocode and the shipped symbol — examined at both R2b reviews and both final
  verifications and closed, so it is not re-opened.

**One durable rule the catalog carries forward**, from R2b: `testing/relay.py::global_id_for`'s message
is split across adjacent string literals, so **a source grep returns 0 occurrences for text that is
present in the raised string**. Any future audit or assertion about that message runs against the
runtime (assembled) value, never the source text.

### Four maintainer escalations, surfaced by this gate

None is fixable inside this cycle; all four are carried, not closed. None blocks `final-accepted`.

1. **Spec-010's rule-27 debt needs a maintainer DECISION** (catalog item 3). It is not a defect to
   assign — closing it is a citation conversion **plus** retiring `spec-010 #"## Note on source line
   references"`, the section that **institutionalizes** the practice, and it requires authorization for
   spec-010 edits outside the sites maintainer decisions 1-8 name. Figures as in item 3 above.
2. **The stale `spec-009 (1076-1077)` citation at `spec-010:408`** (catalog item 1). **Stale at HEAD,
   not this cycle's damage** — it was already wrong before R2 opened the file, and this cycle's spec-010
   writable surface never covered it. It belongs with catalog item 2 to one future spec-009 residual
   cycle.
3. **`KANBAN.md:248` names one spec too many** (catalog item 7) — it lists spec-008 among the specs
   still naming `convert_relation`, and spec-008 no longer does. **Record only**: the file is
   DB-generated and corrects itself when that board item's card is next regenerated. **Do not add
   spec-018 to the list** — its two occurrences are explicitly marked historical, which is why its
   absence is correct.
4. **The `docs/review/` escalation** (catalog item 8) — **open and unresolved**, first raised during the
   spec-007 cycle. State re-derived at this gate: **five ` M`, zero ` D`** (plus four `??`). All five
   previously-deleted `rev-*.md` have returned modified, which **strengthens** the reading that a REVIEW
   cycle regenerated its own artifacts rather than an `AGENTS.md` rule 22 violation. **That remains
   evidence, not a conclusion — only the maintainer can confirm the intent.** No pass in this cycle,
   this gate included, touched, read for content, restored, or reverted anything under that directory;
   the state was observed through `git status` alone.

### One process note

**"Procedural closure" now means two things in this repo**, and the next cycle should inherit the
distinction rather than the word. `BUILD.md` `### Procedural-closure slices` = a single Worker 1 pass,
**no Worker 2 and no Worker 3**. This cycle's plan `### Deviation 2` = **no Worker 2 only**, with the
Worker 3 audit explicitly non-skippable. R1, R2, and R3 each ran the full Worker 3 audit — R3 ran it
twice. Nothing on disk is ambiguous; this is a precision, not a defect.

### Figures lifted from R3, and where each was taken from

`bld-008-r3-doc_completion_archive.md` carries superseded figures above `:861`. Per the binding rule
R3 established (its section B), every figure quoted here is taken from the superseding counts table at
`:879` or the keyed correction sections below it — **never from any row above `:861`, and specifically
never `:391`**, which R3 named because its tidy two-integer form makes it the most quotable-looking
stale site in the file. Item 3's figures above come from section **D.1** (`:1605`), which is below
`:861`; its `### Item 3 in full` twin at `:300` was deliberately not used as the source.

**Re-derived at this gate rather than quoted**, per the standing rule that every count carries its unit
and derivation command — all three agree with R3's corrected values:

| Figure | Unit | Derivation command | Result |
|---|---|---|---|
| `cardinalit` in the package | matching lines | `grep -rniE 'cardinalit' django_strawberry_framework/ \| wc -l` | **42** |
| same | files | `grep -rliE 'cardinalit' django_strawberry_framework/ \| wc -l` | **12** |
| `finalize_django_types()` in the package | matching lines | `grep -rn 'finalize_django_types()' django_strawberry_framework/ \| wc -l` | **45** |
| same | call sites | `grep -rnE '^\s*(await )?(\w+\.)?finalize_django_types\(\)' django_strawberry_framework/ \| wc -l` | **0** |
| staged anchors outside `docs/builder/` | matching lines | `grep -rEn 'TODO\(spec-008\|TODO-(ALPHA\|BETA\|STABLE)-008' . \| grep -cv '^docs/builder/'` | **0** (raw total 12) |

**The `./`-prefix trap was checked on this gate's own run, not assumed away.** The prompt records it
firing fifteen-plus times this cycle, including a case where an assumed `./` prefix turned a 0 into a
false 11. Verified here by printing the raw hits: this environment's recursive grep emits
`docs/builder/bld-008-…`, **without** a `./` prefix, so `grep -v '^docs/builder/'` genuinely filters
rather than passing every line through. Raw 12, complement 0 — and the raw figure is the one that moves
when a pass writes prose containing the anchor text, which is why **0 outside `docs/builder/` is the
reportable form and the raw total never is**.

### Failability proofs / hot-path budget

`None; this pass introduced no new boundary.` This gate wrote no source, no test, and no production
line; there is nothing to mutate. `Not applicable; plan declares no hot path.` — and independently
true of this pass, which changed no executable code.

### Validation run

No write-mode command was run by this pass. `ruff format --check .` and `ruff check .` are the gate's
own read-only commands, recorded above; neither `--fix` nor `ruff format .` was invoked anywhere.
`git status --short` after the gate -> **53** entries, up from 52 by exactly this artifact
(`docs/builder/bld-008-final.md`, `??`) and nothing else. No unexpected churn, nothing reverted, no
file outside the two writable paths touched.

### Notes for Worker 0

The cycle is closed and hands off to the maintainer. All four items (R1, R2, R2b, R3) are
`final-accepted` with their boxes ticked; this gate's box is the last one and is now earned. The
maintainer commits the source changes, the four spec/rationale files, the five `bld-008-*` artifacts,
and the plan, at their discretion.

---

## Final verification (Worker 1)

- **Every gate command run and recorded honestly.** Six commands, six real exit codes, six pass
  results, all quoted from the actual output. No count in this artifact was asserted without its unit
  and derivation.
- **No failure of any kind occurred**, so the baseline exception was recorded but never exercised, and
  no attribution verdict — blocking or reported — was owed for any file.
- **No cycle-attributable failure**, so no item re-loops. R1, R2, R2b, and R3 all stay
  `final-accepted`.
- **Floor determination confirmed rather than re-run**, on the plan's declared condition, verified by
  reading R2b's diff line by line.
- **The deferred-work catalog is carried forward at full width** — ten numbers, eight items, both
  closures intact, item 3's institutionalizing framing intact.
- **Four maintainer escalations surfaced**, none blocking.
- Nothing was fixed, reverted, restored, or edited by this pass. Nothing under `docs/review/` was
  touched. No commit, no branch.

### Summary

The spec-008 residual-completion cycle passes its final test-run gate on a fully green board: the
whole-tree suite (`5651 passed, 40 skipped`, zero failures, zero errors), Django's two example-project
consistency checks, both read-only ruff gates, and `git diff --check` all pass, in a working tree
carrying 52 entries from five concurrent sessions. The cycle's own diff is four Markdown documents plus
four `.py` files whose combined change is one docstring, one comment, one error-message string, and one
test assertion — no executable production line, which is what makes the plan's floor-verification
`none` a confirmed determination rather than an unrun obligation.

What the cycle delivered: spec-008's deliberative layer moved to a rationale sibling (the largest such
move in the residual series), the spec reconciled from an open design exploration into a settled design
record, five authorized sibling-spec edits under the 001-010 ownership partition, two `spec-014` source
misattributions corrected, and one consumer-visible error string that named a non-remedy replaced with
one that works.

### Spec changes made (Worker 1 only)

**None.** This gate made no spec edit. The cycle's spec edits are recorded in
`bld-008-r1-rationale_move.md` and `bld-008-r2-spec_reconciliation.md` under their own
`### Spec changes made (Worker 1 only)` sections; this pass verified they are on disk and did not
re-open them.

### Final status

**`final-accepted`.** The gate closes the spec-008 residual-completion cycle. Header `Status:` (line 4)
set in the same action as this block, per the standing fix for the R2 five-pass header drift; **no
`## Status` section appended** — the canonical `Status:` is the header line, the only line Worker 0
reads (`ARTIFACT.md:3`, `:181`). Worker 0 marks the plan's final checklist box and hands off to the
maintainer.
