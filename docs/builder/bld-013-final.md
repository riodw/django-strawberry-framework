# Build: Final test-run gate (013 / real_m2m_coverage / 0.0.4)

Spec reference: `docs/SPECS/spec-013-real_m2m_coverage-0_0_4.md` (whole file; 77 lines, 5,739 bytes at
gate entry, unchanged by this pass)
Status: final-accepted

The closing pass of a **residual-completion cycle** for card `DONE-013-0.0.4`, dispatched to Worker 1
alone (`docs/builder/build-013-real_m2m_coverage-0_0_4.md` `## Dispatch record`:
"`worker-1.md` `## Final test-run gate` gives the whole gate to Worker 1"). It writes no code, so
`docs/builder/BUILD.md` `### Isolation is non-waivable` does not bind it.

Writable set as dispatched, and nothing else was touched:

- `docs/builder/bld-013-final.md` (this file, created)
- `docs/builder/worker-memory/spec-013-worker-1.md`

This pass made **no database write and ran no generator**, per the plan's F12 disposition.
`examples/fakeshop/db.sqlite3` and `docs/GLOSSARY.md` are dirty with a concurrent session's
uncommitted work; neither was opened for writing. `docs/GLOSSARY.md` was read **at `HEAD`** via
`git show HEAD:docs/GLOSSARY.md` into a scratch path outside the repository, so this pass read the
landed glossary rather than a concurrent session's unlanded rows.

**No `bld-integration.md` exists for this cycle**, by the plan's `## Artifact list` disposition: the
cycle lands no source, so there is no cross-slice DRY surface. Two of the integration pass's
obligations are discharged here and recorded below — the staged-anchor sweep and the read of every
closed artifact.

## Plan (Worker 1)

### DRY analysis

- **Helper inventory checked.** Not applicable and deliberately skipped, for the reason R1 and R2
  both recorded: the package-wide AST inventory in `worker-1.md`
  `### Package-wide helper inventory before helper planning` exists to prevent duplicated *code*
  shapes before a builder writes them. This pass's writable set is one Markdown artifact plus a
  memory file, it plans no helper, constant, validation branch, or test helper, and no pass of this
  cycle touches `django_strawberry_framework/`.
- **Existing patterns reused.** The gate is `docs/builder/BUILD.md` `## Final test-run gate` run
  verbatim in its stated order; the artifact shape is `docs/builder/ARTIFACT.md`'s template as R1 and
  R2 applied it for a Worker-1-only item (a `## Build report (Worker 1, acting for this item)` block
  carrying the run, then `## Final verification (Worker 1)`).
- **New helpers justified.** None. No executable artifact of any kind.
- **Duplication risk avoided.** One. Copying R2's five-item deferred list forward unchecked — avoided
  by re-deriving the catalog from **both** artifacts and re-measuring every figure, which is what
  surfaced the sixth item and one count correction (`### Deferred work catalog`).

### Implementation steps

1. Read the standing docs marked `yes` in the Worker 1 column, the plan in full, and both closed
   artifacts in full (`docs/builder/BUILD.md` `## Cross-slice integration pass` step 1 allows no
   "as needed").
2. Re-verify the spec's status/header lines (`worker-1.md` `## Spec status-line re-verification`).
3. Run every gate command in the order `docs/builder/BUILD.md` `## Final test-run gate` gives them.
4. Attribute every failure by path against this cycle's diff; record evidence and escalate rather
   than fixing, for anything outside it.
5. Discharge the two folded-in integration obligations.
6. Author the `### Deferred work catalog` from both artifacts by re-derivation, not by copy.

Line numbers are pin-at-write-time navigational hints.

### Test additions / updates

None, and none is possible: this pass's writable set contains no test file. The gate's own full sweep
is the only `pytest` invocation, run with `--no-cov` (`docs/builder/BUILD.md`
`## Coverage is the maintainer's gate, not a worker's tool`: `--no-cov` is the only permitted
coverage-shaped flag, and plain `uv run pytest` is a coverage run in this repo). No `--cov*` flag was
used anywhere in this pass, and no line coverage was inspected or asserted.

### Implementation discretion items

None. The gate's command set and order are fixed by `docs/builder/BUILD.md`; the one judgement this
pass owns — failure attribution — is argued from measured evidence below rather than left to taste.

### Dispatched findings checklist

This item is the gate, not a findings cohort: it has no dispatched findings of its own. Its checklist
is the gate's own command set, and the two integration obligations the plan folded in. Every box is
ticked only where the command actually ran and its result is recorded verbatim below.

- [x] `uv run pytest --no-cov` — the full sweep across all three test trees
- [x] `uv run python examples/fakeshop/manage.py check`
- [x] `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run`
- [x] `uv run ruff format --check .` (read-only; never `--fix`)
- [x] `uv run ruff check .` (read-only; never `--fix`)
- [x] `git diff --check`
- [x] `uv run python scripts/check_trailing_commas.py --check` over this cycle's files (the
  `source-layout` pre-commit hook enforces the Markdown link scaffold `ruff` does not see)
- [x] Floor verification — the plan declares scope `none`; the literal is recorded and no floor venv
  was built
- [x] Folded-in integration obligation: the staged-anchor sweep, confirmed independently
- [x] Folded-in integration obligation: the read of every closed artifact, walking its deferrals and
  notes
- [x] `### Deferred work catalog` authored from both artifacts by re-derivation

---

## Build report (Worker 1, acting for this item)

### Files touched

- `docs/builder/bld-013-final.md` — this artifact, created.
- `docs/builder/worker-memory/spec-013-worker-1.md` — memory entry appended (gitignored).

Nothing else. `git status --porcelain` reports **131** paths at gate entry against R2's recorded 130;
the delta is a further concurrent-session change that arrived between the two passes. The baseline
moves, as the plan's `## Baseline-dirty out-of-scope files` warns, which is why it is re-derived here
rather than quoted. **Not one baseline-dirty path was edited, reverted, staged, stashed,
`git checkout`ed, or `git restore`d.**

`HEAD` = `973d00b2c4cae3d3474dcd819b1c9a012d18bfe1`, unchanged since the plan was written.

**This cycle's entire diff, enumerated** — the population every attribution judgement below rests on:

| Path | State | Written by |
|---|---|---|
| `docs/SPECS/spec-013-real_m2m_coverage-0_0_4.md` | `M` | R1 (reconciled), R2 (one bullet) |
| `docs/SPECS/appx/spec-013-real_m2m_coverage-0_0_4-rationale.md` | `??` | R1 (created), R2 (appended) |
| `docs/builder/bld-013-r1-rationale_and_spec_reconciliation.md` | `??` | R1 |
| `docs/builder/bld-013-r2-doc_completion_archive_audit.md` | `??` | R2 |
| `docs/builder/build-013-real_m2m_coverage-0_0_4.md` | `??` | Worker 0 (the plan) |

Measured by `git status --porcelain -- <the five paths>`. **Five Markdown files and nothing else: no
package source, no test, no database, no generated doc, no `.py` of any kind.** That is the fact the
whole attribution section turns on.

### Gate command 1 — full sweep

```shell
uv run pytest --no-cov
```

**FAIL (1 failed, 5831 passed, 40 skipped in 216.65s).** Verbatim summary line:

```
============ 1 failed, 5831 passed, 40 skipped in 216.65s (0:03:36) ============
```

Failing node id, listed rather than counted so the reader can re-derive:

- `tests/rest_framework/test_inputs.py::test_dedupe_serializer_input_shape_is_sole_cache_protocol`

Attributed and escalated in `### Attribution of the one gate failure` below. **Not this cycle's**, and
not fixed, masked, skipped, or routed back through an item.

### Gate command 2 — Django consistency checks against the example project

```shell
uv run python examples/fakeshop/manage.py check
```

**PASS** (exit 0). Output: `System check identified no issues (0 silenced).`

```shell
uv run python examples/fakeshop/manage.py makemigrations --check --dry-run
```

**PASS** (exit 0). Output: `No changes detected.`

Both are meaningful here despite the Markdown-only diff: they are the backstop that a concurrent
session's ~42 modified package sources and the example project's models/admin/urls have not drifted
apart in the tree the maintainer will commit from.

### Gate command 3 — the read-only lint / format / diff gate

Run read-only throughout. **`--fix` was never passed to any invocation**, and no file was rewritten by
this pass.

| Command | Exit | Result |
|---|---|---|
| `uv run ruff format --check .` | 0 | **PASS** — `420 files already formatted` |
| `uv run ruff check .` | 0 | **PASS** — `All checks passed!` |
| `git diff --check` | 0 | **PASS** — no output; no whitespace error and no conflict marker anywhere in the tree |

`ruff format --check` also emits a standing configuration warning, recorded because it is not a
failure and a later reader should not mistake it for one: `The following rule may cause conflicts when
used with the formatter: COM812`. It is a pre-existing repository configuration property (`AGENTS.md`
rule 17 makes `scripts/check_trailing_commas.py`, not `ruff`, the owner of single-line explosion, so
`COM812` is deliberately retained), it is emitted on `--check` and `--fix` alike, and the command's
exit code is 0.

**Attribution by path is not needed for this gate: it passed tree-wide.** The gate is tree-wide, so it
*could* have failed on a concurrent session's files; it did not, on any file, so no path-based
attribution judgement arises. Had it failed, the rule the plan and dispatch set is that a failure
inside `docs/SPECS/spec-013-*.md`, `docs/SPECS/appx/spec-013-*-rationale.md`, or
`docs/builder/*013*.md` is this cycle's and blocks `final-accepted`, and a failure anywhere else is
recorded and escalated.

### Gate command 3b — the `source-layout` scaffold check `ruff` cannot see

`ruff` does not see the Markdown link scaffold; the `source-layout` pre-commit hook does, and this
cycle's whole output is Markdown, so a scaffold defect would be invisible to the gate above and would
surface only at the maintainer's commit (the standing trap in `START.md`
`## Markdown link convention`).

```shell
uv run python scripts/check_trailing_commas.py --check \
  docs/SPECS/spec-013-real_m2m_coverage-0_0_4.md \
  docs/SPECS/appx/spec-013-real_m2m_coverage-0_0_4-rationale.md \
  docs/builder/bld-013-r1-rationale_and_spec_reconciliation.md \
  docs/builder/bld-013-r2-doc_completion_archive_audit.md \
  docs/builder/build-013-real_m2m_coverage-0_0_4.md
```

**PASS** (exit 0). Run in `--check` mode only, so no file was auto-rewritten. All five of this cycle's
files are covered, the plan included — the tree-wide `ruff` gate above would not have caught a
scaffold defect in any of them.

The spec-specific checker was re-run at the gate as well, since this cycle rewrote the spec:

```shell
uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-013-real_m2m_coverage-0_0_4.md
```

**PASS** (exit 0). Output: `OK: 1 terms - all have glossary entries and at least one spec link.`

### Gate command 4 — floor verification

**No floor-verification scope declared.**

The plan's preamble declares it explicitly: "Floor-verification scope: **none.** No item touches a
Django / Strawberry / channels integration seam — no item touches executable code at all." Both closed
artifacts carry the matching `### Floor verification` literal. `docs/builder/BUILD.md`
`### When it is required` scopes the obligation to slices touching a framework integration seam; a
Markdown-only cycle touches none, so the declaration is correct and **no floor venv was built**. The
shared `.venv` was not mutated, downgraded, or installed into by any command in this pass
(`worker-1.md` `## Scope`).

### Folded-in integration obligation 1 — the staged-anchor sweep

`docs/builder/BUILD.md` `## Cross-slice integration pass` step 6, confirmed **independently** rather
than accepted from R2's record:

```shell
grep -rEn 'TODO\(spec-013|TODO-(ALPHA|BETA|STABLE)-013' . \
  --exclude-dir=.git --exclude-dir=.venv --exclude-dir=__pycache__ \
  --exclude=KANBAN.md --exclude=KANBAN.html --exclude=BACKLOG.md --exclude='*.sqlite3'
```

**Exactly one hit**, and it is not a staged anchor:

```
docs/builder/bld-013-r1-rationale_and_spec_reconciliation.md:279
```

That is R1's own quotation of the sweep command, inside a per-cycle scratchpad (`START.md`
`## Temp artifact conventions`). R2's quotation at its line 317 escapes the parenthesis
(`TODO\(spec-013`) and so does not match at all, which is why this sweep returns one hit where R2's
returned one hit for a different line — both reduce to the same finding.

**Zero staged anchors exist in shipped source, tests, or any standing doc.** Nothing to discharge, no
anchor to remove, no finding, and nothing to route back to an owning item. The `KANBAN.md` /
`KANBAN.html` / `BACKLOG.md` exclusions are the ones step 6 prescribes, where `TODO-<MILESTONE>-<NNN>`
legitimately names unshipped board cards.

### Folded-in integration obligation 2 — the read of every closed artifact

Both were read **in full**, and their deferrals and notes walked, not skimmed
(`docs/builder/BUILD.md` `## Cross-slice integration pass` step 1 allows no "as needed"):

- `docs/builder/bld-013-r1-rationale_and_spec_reconciliation.md` — 334 lines,
  `Status: final-accepted`. Dispatched findings F1-F7 `- [x]`, F8 `- [ ]` with its deferral recorded.
  Its `### Notes for Worker 1 (spec reconciliation)` routes two items forward; its
  `### Inbound spec-013 references` routes a third that R2's list did not carry forward
  (`### Deferred work catalog` item 6).
- `docs/builder/bld-013-r2-doc_completion_archive_audit.md` — 493 lines,
  `Status: final-accepted`. F9-F11 `- [x]`, F12 `- [ ]` with its deferral reason, reversal recipe, and
  a measured mechanism correction. Its `### Deferred work list` carries five bullets; its
  `### Notes for Worker 1` points at that list.

The plan's remaining cross-slice checks (duplicated helpers, repeated ORM patterns, misplaced
responsibilities, exports, shadow-overview literal and import comparisons) are **structurally
inapplicable**: they scan landed Python for cross-slice duplication and this cycle lands none. That is
the plan's own recorded reason for producing no `bld-integration.md`, and the same disposition the
spec-011 and spec-012 cycles took.

### Attribution of the one gate failure

`docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on prose` is explicit that
**"Pre-existing at HEAD" for a failing test is not worker-verifiable at all** — reproducing it needs
the whole tree at `HEAD`, and this tree is legitimately dirty with a concurrent session's work across
~42 package sources and ~25 tests. So this pass records the evidence it can get and escalates. It does
**not** assert the failure is pre-existing, and it does not fix, mask, skip, or route it back through
an item.

**The failure.** `tests/rest_framework/test_inputs.py::test_dedupe_serializer_input_shape_is_sole_cache_protocol`

```
    cre_a, shape_a = build_serializer_input_class(_item_serializer(), operation_kind="create")
    cre_b, shape_b = build_serializer_input_class(_item_serializer(), operation_kind="create")
>   assert shape_a == shape_b
E   AssertionError: assert SerializerInp...ItemSerInput') == SerializerInp...ItemSerInput')
E     Omitting 7 identical items, use -vv to show
E     Differing attributes:
E     ['serializer_class']
E     Drill down into differing attribute serializer_class:
E       serializer_class: <class 'tests.rest_framework.test_inputs._item_serializer.<locals>.ItemSer'>
E                      != <class 'tests.rest_framework.test_inputs._item_serializer.<locals>.ItemSer'>

tests/rest_framework/test_inputs.py:658: AssertionError
```

**Evidence gathered, each with the command it came from.**

| # | Question | Answer | How |
|---|---|---|---|
| E1 | Is the failing test in this cycle's diff? | **No** | The five-path diff table above. This cycle wrote zero `.py` files |
| E2 | Is the code under it in this cycle's diff? | **No** | Same table. `django_strawberry_framework/rest_framework/inputs.py` is not this cycle's |
| E3 | Is the failing test file dirty with a concurrent session's work? | **No** | `git status --porcelain -- tests/rest_framework/` reports only `test_sets.py` |
| E4 | Is the module under test dirty? | **No** | `git status --porcelain -- django_strawberry_framework/rest_framework/` reports only `sets.py` |
| E5 | Are either byte-identical to `HEAD`? | **Yes, both** | `git show HEAD:<path>` into a scratch path **outside** the repo, then `diff -q`: both report identical. No `git stash` / `checkout` / `restore` / `worktree` was used |
| E6 | Is it order- or parallelism-dependent? | **No** | Re-run isolated: `uv run pytest "tests/rest_framework/test_inputs.py::test_dedupe_serializer_input_shape_is_sole_cache_protocol" --no-cov -p no:randomly` -> `1 failed in 3.06s`, same assertion |
| E7 | When were the two files last changed? | `5851bb59` (2026-08-15), and it **is an ancestor of `HEAD`** | `git log -1 --format='%h %ad %s' -- <each path>`; `git merge-base --is-ancestor 5851bb59 HEAD` -> exit 0 |
| E8 | Did a concurrent session change the cache helper the test names? | **No** | `_serializer_shape_build_cache` is built by `make_shape_build_cache` in `django_strawberry_framework/utils/inputs.py`, which **is** dirty (+200 lines) — but `git diff -U0 -- <that file> \| grep make_shape_build_cache` returns no hunk. The concurrent work adds a separate dynamic-set cache family, not this one |

**The mechanism, read out of the two files at `HEAD` so the escalation is actionable rather than a bare
node id.** `tests/rest_framework/test_inputs.py::_item_serializer` is a factory that declares a
**fresh** local `class ItemSer` on every call, and the test calls it twice.
`django_strawberry_framework/rest_framework/inputs.py::SerializerInputShape` is a
`@dataclass(frozen=True)` whose **first field is `serializer_class`**, so the generated `__eq__`
compares it — and two distinct classes are unequal. The test's docstring premise, "a second build of
an identical descriptor", is therefore not what the body constructs: the two descriptors differ in
exactly the one attribute pytest names. The other seven fields are identical, which is why the
diff reads `Omitting 7 identical items`.

**The candidate fix is named and deliberately NOT applied.** Building both from one shared serializer
class (`ser = _item_serializer()` hoisted, passed to both `build_serializer_input_class` calls) would
restore the test's stated intent — that `dedupe_serializer_input_shape` is the sole writer of the
cache — without weakening `SerializerInputShape`'s identity contract, which is load-bearing (its
docstring records why a name-only key is insufficient). **Whether that is the right fix, or whether
the shape's equality contract is what should change, is a maintainer decision**, and either way the
edit lands in a test or source file this dispatch forbids this pass to touch, in committed code this
cycle did not produce.

**Conclusion.** The failure cannot have been caused by this cycle: the cycle's complete output is five
Markdown files, and both the failing test and the module it exercises are byte-identical to `HEAD` and
were last modified by a commit that is an ancestor of `HEAD`. Recording the evidence above and
escalating to the maintainer — the only party who can run a clean `HEAD` tree — **discharges the
obligation** (`docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on prose`,
"Pre-existing at HEAD"). It does **not** block `final-accepted` for this cycle.

### Failability proofs

None; this pass introduced no new boundary. Its writable set is one Markdown artifact plus a memory
file, and it added no guard, gate, or rejection path. Consistent with R1's and R2's identical records,
so no boundary anywhere in this cycle owes a proof.

### Hot-path budget

Not applicable; plan declares no hot path (`docs/builder/build-013-real_m2m_coverage-0_0_4.md`
preamble: "Hot-path declaration: none. Both items write Markdown only"). Nothing in this cycle runs
per request, per resolver, per row, per connection, or per outbound message.

### Floor verification

**No floor-verification scope declared.** Full record in `### Gate command 4 — floor verification`
above; the plan's declaration is `none` and no pass of this cycle owed a floor run, so there is no
unrun floor claim for the gate to backstop.

### Implementation notes

- **The glossary was read at `HEAD`, not from the working tree.** `docs/GLOSSARY.md` is required
  Worker 1 reading and is dirty with a concurrent session's uncommitted work; reading the working copy
  would have meant reading unlanded rows and possibly checking the spec against a claim that has not
  shipped. `git show HEAD:docs/GLOSSARY.md` into a scratch path outside the repository is the
  read-only form `docs/builder/BUILD.md` prescribes, and it is what confirmed that the spec's
  corrected forward-FK bullet (R2's DEFECT-1) agrees with the landed `## Relation handling` entry.
- **The failure was re-run in isolation before being attributed.** A tree-wide sweep cannot
  distinguish an order-dependent cross-test-pollution flake from a deterministic failure, and the two
  attribute differently. The isolated re-run is what makes E6 a measurement rather than an assumption.
- **The deferred catalog was re-derived, not copied.** R2 catalogued five items; re-deriving from both
  artifacts found a sixth that R2's list did not carry forward, and re-measuring found one figure both
  artifacts state that does not reproduce. Copying would have propagated both silently — the exact
  failure mode `docs/builder/BUILD.md` `## Claims are proven mechanically` describes for a stated
  count.
- **The plan's final checkbox is deliberately left `- [ ]`.** `worker-1.md` `## Scope` forbids Worker 1
  from marking build-plan checkboxes; Worker 0 marks it after reading this artifact's
  `Status: final-accepted`.

### Notes for Worker 3

No Worker 3 pass is dispatched for this item (`## Dispatch record`: "Worker 1 only"; the cycle writes
no code, so `### Isolation is non-waivable` does not bind). Every verification a reviewer would run is
above, each with the command and its exit code.

### Notes for Worker 1 (spec reconciliation)

None owed forward — this is the closing pass. The spec needed no edit at this gate
(`### Spec changes made (Worker 1 only)`), and everything the cycle could not perform is in
`### Deferred work catalog`, which is this artifact's own section and the next spec author's reading
list.

---

## Final verification (Worker 1)

- **Gate checklist:** every box in `### Dispatched findings checklist` is `- [x]`, and each was ticked
  only against a command that actually ran with its result recorded verbatim above. No box is ticked
  without a matching run.
- **Every planned step implemented.** Steps 1-6 all ran; none was rejected.
- **Spec status-line re-verification** (`worker-1.md` `## Spec status-line re-verification`, required
  of **every** Worker 1 spawn including this one): spec lines 1-5 read title `Spec: Real M2M
  coverage`, `Target release: 0.0.4`, `Status: shipped`, `Owner: package maintainer`, plus the line-7
  pointer sentence naming the rationale companion. Re-read at this gate and **all still accurate** —
  nothing this gate ran falsified any of them, no predecessor reference needs updating, and the
  rationale companion the pointer names exists at the path it gives. No edit made. This is the third
  independent re-verification of the same block (R1, R2, and this pass).
- **Gate results:** `pytest --no-cov` **FAIL** on one node, attributed and escalated as not this
  cycle's; `manage.py check` **PASS**; `makemigrations --check --dry-run` **PASS**;
  `ruff format --check .` **PASS**; `ruff check .` **PASS**; `git diff --check` **PASS**;
  `check_trailing_commas --check` over all five of this cycle's files **PASS**;
  `check_spec_glossary` **PASS**; floor verification: `No floor-verification scope declared.`
- **Attribution judgement, stated once for the record:** this cycle's complete output is five Markdown
  files and no `.py` of any kind, so no `pytest`, `check`, `ruff`, or `git diff --check` result can be
  its doing. The lint/format/diff gate passed tree-wide, so no path-based attribution arose there. The
  single `pytest` failure is in a test and a module both byte-identical to `HEAD`, both last modified
  by an ancestor commit of `HEAD`, reproducible in isolation, and neither in this cycle's diff —
  recorded with its evidence and **escalated to the maintainer**, which discharges the obligation.
- **DRY check across this cycle's accepted items:** no new duplication. This artifact cites R1's and
  R2's records rather than restating them, and the deferred catalog carries each item's evidence once.
- **Claims proven mechanically:** every count and figure in this artifact was measured as it was
  written, or is a listed set the reader can re-derive (the five diff paths, the one failing node id,
  the six catalog items, the eight evidence rows). Two figures inherited from the closed artifacts did
  **not** reproduce and are corrected in the catalog rather than propagated.
- **Existing tests:** the gate's own full sweep is the run; no focused re-run was owed, since this
  pass's writable set contains no test and no source. No `--cov*` flag was used anywhere in this pass,
  and no line coverage was inspected or asserted.
- **Staged-anchor sweep:** performed independently; zero anchors in shipped surfaces.
- **No fail-open shape landed.** Not applicable to a Markdown-only cycle, confirmed by reading the
  diff — there is no expression, guard, or decision path in it.
- **Final status:** `final-accepted`. Every gate command either passed or, in the single failing case,
  was attributed with measured evidence and escalated as not this cycle's, which is the acceptance
  condition this gate's dispatch sets.

### Summary

Ran the full final test-run gate for the `DONE-013-0.0.4` residual-completion cycle. **Eight of the
nine commands pass**: Django's `check` and `makemigrations --check --dry-run` against the example
project, the whole read-only lint/format/diff gate (`ruff format --check .`, `ruff check .`,
`git diff --check`), the `source-layout` scaffold check over all five of this cycle's Markdown files,
and `check_spec_glossary` re-run after the cycle's spec edits. Floor verification is the declared
literal `No floor-verification scope declared.` — the plan scopes it `none` because no item of this
cycle touches executable code, so no floor venv was built and the shared `.venv` was untouched.

The full sweep is **1 failed, 5831 passed, 40 skipped**. The one failure,
`tests/rest_framework/test_inputs.py::test_dedupe_serializer_input_shape_is_sole_cache_protocol`,
**cannot be this cycle's**: the cycle's entire output is five Markdown files, and both the failing
test and the `rest_framework/inputs.py` module it exercises are byte-identical to `HEAD` (verified
read-only via `git show HEAD:<path>` into a scratch path outside the repository), were last modified
by commit `5851bb59` which is an ancestor of `HEAD`, and reproduce the same assertion when run in
isolation. The mechanism was diagnosed so the escalation is actionable — the test's `_item_serializer`
factory builds a fresh class per call while `SerializerInputShape` is a frozen dataclass comparing
`serializer_class`, so the two descriptors the test calls "identical" differ in exactly that one
attribute — and the candidate fix is named but deliberately not applied, since it lands in a test file
this dispatch forbids and turns on a maintainer contract decision. Recorded and escalated.

Both integration-pass obligations the plan folded in are discharged: the staged-anchor sweep returns
exactly one hit, R1's own quotation of the command inside a per-cycle scratchpad, so zero anchors
survive in shipped source, tests, or standing docs; and both closed artifacts were read in full with
their deferrals walked. That read is what produced the catalog below — **six items, not R2's five**,
plus one inherited figure corrected by measurement.

### Spec changes made (Worker 1 only)

**None.** This gate falsified nothing in `docs/SPECS/spec-013-real_m2m_coverage-0_0_4.md`, so
`worker-1.md` `## Spec custody` licenses no edit — it permits one only where the build proves the spec
inaccurate. The header block was re-verified and left unchanged (above). The spec is **5,739 bytes /
77 lines** at gate exit, exactly as R2 left it, and its rationale companion **41,636 bytes / 595
lines** (`wc -c -l`).

Two items surfaced by this pass are **not** spec edits and are deliberately not made here, in line
with this dispatch: the `pytest` failure (committed code, outside the writable set, escalated) and the
sixth catalog item plus its count correction (a cross-surface cluster, catalogued).

### Deferred work catalog

Authored by Worker 1, its only author (`docs/builder/BUILD.md` `## Final test-run gate`). Walked from
**both** closed artifacts' spec-reconciliation notes, `Notes for Worker 1` sections, dispatched-findings
deferrals, and build-report sweeps, plus the rationale's own
`### What this cycle deliberately did not fix`. **Every figure below was re-measured at this gate**;
R2's list of five was verified rather than copied, which surfaced a sixth item R2's list did not carry
forward and one count both artifacts state that does not reproduce.

**Item 1 is given its own prominence below the list: it is the one piece of work this cycle
identified, could not perform, and hands to the maintainer as a ready-to-apply step.**

- **1. F12 — the `DONE-013-0.0.4` card body carries a duplicate `#### Scope` row.** *Source:* the
  plan's `### R2 findings` F12; R2's `### Deferred work list` first bullet; R2's dispatched-findings
  box `- [ ]`. *Spec line licensing it:* none — this is a Kanban-database defect, not a spec claim.
  *Description:* bullet 3 of the card's `#### Scope` section restates bullets 1 and 2 verbatim; the
  fix is one ORM delete plus a regenerate, blocked only by a dirty `db.sqlite3`. **Full evidence,
  reversal recipe, and mechanism correction below.**
- **2. `KANBAN.md` line 341 — the archived-stub preamble count is now stale.** *Source:* R1's
  `### Inbound spec-013 references` and `### Notes for Worker 1`; R2's `### D` table and
  `### Deferred work list`. *Spec line licensing it:* none; it is a board claim this cycle's own spec
  edit falsified. *Description:* the line reads "Four archived stubs still carry the boilerplate
  'expand it into the full builder-format spec' preamble: `spec-013`, `spec-016`, `spec-024`,
  `spec-026`". **Re-measured at this gate** by `grep -c 'expand it into the full builder-format spec'`
  per file: `spec-016` **1**, `spec-024` **1**, `spec-026` **1**, `spec-013` **0** — R1 moved
  spec-013's preamble into the rationale. **The correct figure is three.** *Why not fixed:* `KANBAN.md`
  is generated from `examples/fakeshop/db.sqlite3`, which is dirty with a concurrent session's
  uncommitted work, so a regenerate would publish rows that have not landed (`START.md`
  `## Concurrent sessions`), and a hand-edit of a generated file is reverted by the next render.
  *Reversal recipe:* once the DB is clean at `HEAD`, edit the card item's text through the ORM to read
  three and name `spec-016` / `spec-024` / `spec-026`, then regenerate `KANBAN.md` and `KANBAN.html`.
  The line already anticipates this shape — it instructs a later sweep to "measure four and not
  re-derive five" after the spec-012 cycle; the same sentence now needs three.
- **3. `docs/SPECS/appx/spec-011-stale_placeholder_cleanup-0_0_4-rationale.md` line 28 — the same
  count, in a prior cycle's committed rationale.** *Source:* R1's `### Inbound spec-013 references`
  and `### Notes for Worker 1`; R2's `### D` table and `### Deferred work list`. *Spec line licensing
  it:* none. *Description:* it says five specs still carry the preamble (`spec-012`, `spec-013`,
  `spec-016`, `spec-024`, `spec-026`); **re-measured three** at this gate by the same grep. It was
  already stale by one before this cycle, from the spec-012 residual cycle. *Why not fixed:* a prior
  cycle's committed rationale is outside this cycle's writable set and on this dispatch's do-not-touch
  list; and fixing this site while the DB-backed co-stale site (item 2) stays wrong is the partial fix
  `worker-0.md` `## Closing out a kanban card` forbids — it leaves the surface divergently rather than
  uniformly wrong. *Reversal recipe:* fix items 2 and 3 in **one** sweep, not separately.
- **4. `docs/builder/DONE/build-007-onboarding_docs_spec_consolidation-0_0_4.md` line 254 — a
  smallest-specs byte ranking naming "spec-013 (1,669 bytes)".** *Source:* R2's `### D` table
  (new to R2's sweep, not in R1's record) and its `### Deferred work list`; also recorded in the
  rationale's `## Audit record`. *Spec line licensing it:* none. *Description:* the ranking lists
  spec-013 at 1,669 bytes among the five smallest tracked specs; the file is **5,739 bytes** at this
  gate (`wc -c`, re-measured), so both the figure and the ordering are stale. *Why not fixed:* it is a
  closed cycle's committed record of a measurement taken at its own date, not a live claim restated
  anywhere, and prior cycles' `build-*.md` files are on this dispatch's do-not-touch list. The
  spec-012 residual cycle left the equivalent spec-012 figure standing for exactly this reason.
  *Reversal recipe:* none needed unless the maintainer decides such rankings should carry an
  as-measured date rather than be maintained — which is the real question this item raises for the
  next spec author.
- **5. F8 — the unused `[backlog]` link definition in the spec.** *Source:* the plan's
  `### R1 findings` F8; R1's dispatched-findings box `- [ ]` and its rationale entry "The `[backlog]`
  link definition — recorded, not fixed"; R2's ref-id audit and `### Deferred work list`. *Spec line
  licensing it:* the spec's link-definitions block, `<!-- Root -->` group (spec line 51). *Description:*
  `[backlog]: ../../BACKLOG.md` is defined and never used — **re-measured at this gate**,
  `grep -c '\[backlog\]'` over the spec returns **1**, the definition itself, and it remains the file's
  only unused definition. *Why not fixed:* it is one file of a 71-definition / 23-file cross-surface
  cluster owned by `TODO-ALPHA-052-0.1.0`, which `KANBAN.md` line 340 already catalogues by name,
  listing `spec-013` among the eight archived specs carrying an unused `[backlog]`. A spec-only
  correction diverging from un-editable copies is worse than uniformly wrong. *Reversal recipe:* the
  card retires all 71 in one sweep; nothing spec-013-specific is needed.
- **6. The misleading `[spec-013]` ref-id in `docs/SPECS/spec-025-scalar_map_helper-0_0_7.md`, and the
  pre-renumber `spec-013-deferred_scalars` names in `spec-018` / `spec-019`.** *Source:* **R1's**
  `### Inbound spec-013 references` ("none is fixable without opening a cross-surface renumber
  cluster") and the rationale's `### What this cycle deliberately did not fix`, third bullet. R2
  confirmed them in its `### D` table as false positives but **did not carry them into its
  `### Deferred work list`** — which is why re-deriving the catalog rather than copying R2's five was
  load-bearing. *Spec line licensing it:* none; it is a cross-spec ref-id defect. *Description:*
  `spec-025` defines `[spec-013]: spec-017-deferred_scalars-0_0_6.md` — a ref-id whose **name** says
  card 13 while its **target** is spec-017 — so every future `grep -rn "spec-013"` reads those uses as
  inbound references to this card; and `spec-018` line 175 / `spec-019` line 133 name a
  "`spec-013-deferred_scalars`" that pre-dates the board renumber. **None names card 13 and none is
  broken by this cycle's rewrite**, so nothing is currently *wrong* — the cost is a recurring
  false-positive trap for exactly the kind of inbound sweep this cycle ran twice. *Why not fixed:*
  renaming a ref-id across a sibling spec is outside this cycle's writable set, and the pre-renumber
  names belong to the same board-renumber cluster `KANBAN.md` line 340 records for `[spec-011]` —
  partial-fixing one spec of it is the divergent-fix trap again. *Reversal recipe:* fold into the
  board-renumber sweep that owns the `[spec-011]` artifact cluster; rename `spec-025`'s ref-id to
  `[spec-017]` (definition plus its body uses) in that one pass.

**One inherited figure corrected by measurement, recorded rather than propagated.** R1's
`### Inbound spec-013 references` and R2's `### D` table both state that `spec-025` carries
"3 body uses + 1 def" of `[spec-013]`. Re-measured at this gate: `grep -o '\[spec-013\]' | wc -l`
returns **6** total, of which **1** is the definition line (`spec-025` line 706) and **5** are body
uses (lines 6, 64 twice, 319, 335). The disposition is unaffected — item 6 stays deferred for the same
reason — but the count is corrected here so it is not carried into a third artifact
(`docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on prose`: a stated count
reads as measured and propagates silently, invisible to re-reading).

#### The maintainer's ready-to-apply step: F12

Given its own subsection because it is the single piece of work this cycle **identified, could not
perform, and hands over ready to run** — every other catalog item is either owned by an existing card
or is a question rather than a task.

**The defect.** The rendered `DONE-013-0.0.4` card body carries a duplicate `#### Scope` row:
bullet 3 ("replace test-only M2M / cardinality fixtures with real `library` models; add package +
HTTP coverage.") restates bullets 1 and 2. Confirmed at `KANBAN.md` line 4519 under
`### [DONE-013-0.0.4 ...]` `#### Scope`. It is the identical defect card `DONE-011-0.0.4` carried.

**Why this cycle could not do it.** `KANBAN.md` and `KANBAN.html` are **generated** from
`examples/fakeshop/db.sqlite3` (`docs/builder/BUILD.md` `### Generated docs are DB-backed`), so the
fix is an ORM edit plus a regenerate — never a hand-edit, which the next render silently reverts. The
DB is **dirty with a concurrent session's uncommitted work**, so a regenerate now would publish rows
that have not landed (`START.md` `## Concurrent sessions`). The card-011 cycle dispatched its
equivalent item only after verifying the DB was clean at `HEAD`; that precondition fails here. This
cycle therefore made no database write and ran no generator.

**Reversal recipe — one step, once `examples/fakeshop/db.sqlite3` is clean at `HEAD`.** Through the
Django ORM, delete the third `#### Scope` row of card 13, identified **by its text** rather than by an
assumed index (`CardItem.order` is not re-derivable without opening the DB this cycle may not touch):

```python
CardItem.objects.get(
    card__number=13,
    section__key="scope",
    text__startswith="replace test-only M2M",
).delete()
```

`CardItem.card` -> `Card.number` (`PositiveIntegerField`); `CardItem.section` -> `Section.key`
(`SlugField`) — both read from `examples/fakeshop/apps/kanban/models.py` at `HEAD`. Then regenerate
`KANBAN.md` and `KANBAN.html`. Nothing else changes: the reconciled spec and its rationale already
carry the non-duplicated form.

**Mechanism correction, measured and load-bearing for the recipe.** The plan's F12 says the duplicate
"is the card's `description` column rendered into the scope section". **It is not.**
`scripts/build_kanban_md.py::render_card` builds every `#### <section>` block from `card["items"]`
grouped by section, and the renderer's only use of a `description` key is the relative-size legend.
The duplicate is a third `CardItem` **row** on the `scope` section whose text happens to equal the
card's description — an importer artifact, not a render path. **The fix target is a row, not a
column**, which is why the recipe above deletes one. Measured by R2 and carried here unchanged; had
the plan's characterization been followed, the fix would have targeted a column that the renderer
never reads and the duplicate would have survived the regenerate.

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
