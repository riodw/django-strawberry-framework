# Build: Final test-run gate — `spec-037` residual-reconciliation cycle

Spec reference: `docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md` (whole file) and its rationale companion `docs/SPECS/appx/spec-037-upload_file_image_mapping-0_0_11-rationale.md` (whole file)
Status: final-accepted

Worker 1 only (`docs/builder/BUILD.md` `## Final test-run gate`; `docs/builder/worker-1.md` `## Final test-run gate` gives the whole gate to Worker 1 — there is no Worker 2 or Worker 3 phase). One combined Plan + Gate-report + Final-verification block; Worker 1 sets `Status:` itself.

`git stash` / `git checkout` / `git restore` / `git worktree` were **not used at any point**; every `HEAD` read went through `git show HEAD:<path>` into a scratch path outside the repository. **No `--cov*` flag was passed to any run** — every `pytest` invocation below carries `--no-cov` (`BUILD.md` `## Coverage is the maintainer's gate, not a worker's tool`). `ruff` was run in **read-only** mode only; `--fix` was never passed, in any scope. This pass wrote exactly two files: this artifact and `docs/builder/worker-memory/worker-1.md`.

Hot-path declaration: **none** (copied from the plan as written).
Floor-verification scope: Slice 1's re-declared scope, **confirmed** here rather than re-run — this pass is the backstop, not a second owner. Slices 0 and 2 and the integration pass declared `none`.

Raw `path:NN` references are used below under `AGENTS.md` rule 27's per-cycle-artifact carve-out.

---

## Plan (Worker 1)

### DRY analysis

- **Helper inventory checked.** Not applicable and deliberately not run, recorded rather than silently skipped: this pass proposes no helper, no constant, no validation branch and no test helper, and writes no `.py` file at all. The `### Package-wide helper inventory before helper planning` obligation is scoped to "before proposing any new helper-like logic"; there is none to propose.
- **Existing patterns reused.** `docs/builder/bld-003-final.md` — the immediately-preceding cycle's execution of this same gate — supplied the section shape (`### Working tree, re-derived`, `### Gate commands, in BUILD.md order`, `### Floor verification`, `### Deferred work catalog`, `### Every count in this artifact, with the command that produced it`). Not re-invented.
- **New helpers justified.** None.
- **Duplication risk avoided.** The duplication a final gate can introduce is **restating the prior artifacts' numbers as if it measured them**. Every number below was measured in this pass and carries its command; where a figure is compared against a recorded one, both are printed and the comparison is stated as a comparison.

### Implementation steps

1. Run the four gate command groups in `BUILD.md` `## Final test-run gate` order, recording each one's real exit code.
2. Re-measure the failing set independently and compare it as a **set** against Slice 1's record; run the deselect control at this pass's own scope rather than inheriting Slice 1's.
3. Attribute every lint/format/diff hit to this cycle's diff or to the concurrent session, by measurement.
4. Confirm the floor-verification record for every declared scope, by reading the venv rather than the artifact prose.
5. Walk every per-slice and integration artifact for deferred work and write the catalog.

### Test additions / updates

None. This pass writes no `.py` file and no test.

### Implementation discretion items

None. Every judgement — whether a lint hit blocks, whether a failing row is this cycle's, whether an item is a deferral or a closed ruling — was decided here and is recorded below.

### Dispatched findings checklist

This pass dispatches nothing to a builder: the gate found no failure this cycle owns. The build plan's own checklist row is the closure target.

- [x] Final test-run gate -> `docs/builder/bld-037-final.md`

---

## Gate report (Worker 1)

### Working tree, re-derived

The plan's `## Baseline-dirty out-of-scope files` records 103 dirty paths at cycle start. **Re-derived here, the population is 114**, and the delta is decomposed rather than assumed:

```shell
git status --short | wc -l          # 114
git status --short -- <this cycle's 8 paths>
```

| Bucket | Count | Attribution |
| --- | --- | --- |
| This cycle's own files | **8** | 2 tracked-modified (`docs/SPECS/spec-037-…md`, `tests/types/test_base.py`) + 6 untracked (the rationale companion, the build plan, the four prior `bld-037-*` artifacts). This artifact makes a 9th once written. |
| Concurrent session, enumerated in the plan | ~103 | 55 modified + 1 untracked under `django_strawberry_framework/`; 43 modified test/example files (the plan said 42); 4 modified docs; `docs/bug_hunt/bug_hunt-0_0_15.md` untracked. |
| Concurrent session, **not** in the plan's enumeration | **3** | `GOAL.md`, `docs/feedback2.md`, and one further test/example file (the tests+examples bucket measures 44 total, of which 1 is this cycle's, against the plan's 42). |

**The plan's baseline-dirty list is stale by three paths, and none of the three is this cycle's.** Proved by mtime and by content, not asserted:

- `docs/feedback2.md` — tracked but **empty at `HEAD`** (`git cat-file -s HEAD:docs/feedback2.md` → `0`); the working copy carries 276 lines whose own header names its companion as `docs/bug_hunt/bug_hunt-0_0_15.md`, which **is** in the plan's enumerated untracked baseline. mtime `2026-09-01 19:48:07`.
- `GOAL.md` — a 140-line roadmap rewrite (89 insertions / 51 deletions), mtime `2026-09-01 20:09:43`.
- Both mtimes **precede this cycle's first write** (`docs/SPECS/spec-037-…md` mtime `21:40:24`, `docs/SPECS/appx/…-rationale.md` `21:40:19`, `tests/types/test_base.py` `20:45:16`; Slice 1 recorded the spec at `20:17:40` after Slice 0's edit). `README.md`, `docs/README.md`, `docs/GLOSSARY.md` and `docs/TREE.md` all share mtime `19:48:07` — one concurrent write batch.

No worker in this cycle edited or reverted any of them (`AGENTS.md` rule 34), and this pass did not either.

**Tracked binary / generated files (`BUILD.md` `### Tracked binary / generated files`).**

- `examples/fakeshop/db.sqlite3` — **clean**. `git status --short -- examples/fakeshop/db.sqlite3` returns nothing, so there is no churn to diff semantically and nothing to handle.
- `KANBAN.md` / `KANBAN.html` — **clean**.
- `docs/GLOSSARY.md` / `docs/TREE.md` — dirty, in the plan's enumerated baseline, mtime `19:48:07`, and out of scope by the maintainer's fence as well as by rule 34. **Not diffed against a regenerate, not reverted, not touched** — regenerating them while a concurrent session's feature work is mid-flight is what `START.md` forbids, and this cycle may not write them in any case.

**This cycle's whole tracked diff, measured:**

```text
git diff HEAD --numstat -- docs/SPECS/spec-037-…md tests/types/test_base.py
298   495   docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md
57    0     tests/types/test_base.py
```

Plus one new untracked file, `docs/SPECS/appx/spec-037-upload_file_image_mapping-0_0_11-rationale.md`. **Zero package `.py` files.** Byte counts — spec 1,666 lines / **104,947 bytes**, companion 971 lines / **61,019 bytes** — are byte-for-byte the integration pass's post-edit figures, so nothing has touched either file since.

### Gate commands, in `BUILD.md` order

| # | Command | Exit | Result |
| --- | --- | --- | --- |
| 1 | `uv run pytest --no-cov` (full sweep, all three test trees) | `1` | **4 failed, 7148 passed, 42 skipped in 62.67s** — see `### The four failing rows` |
| 1b | the same sweep with this cycle's three new rows deselected (control) | `1` | **4 failed, 7145 passed, 42 skipped in 60.19s** — identical failing set |
| 2 | `uv run python examples/fakeshop/manage.py check` | `0` | `System check identified no issues (0 silenced).` **PASS** |
| 2 | `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` | `0` | `No changes detected` **PASS** |
| 3 | `uv run ruff format --check .` | `0` | `438 files already formatted` **PASS** |
| 3 | `uv run ruff check .` | `0` | `All checks passed!` **PASS** |
| 3 | `git diff --check` | `2` | **4 whitespace hits, all in `docs/feedback2.md`** — see `### The lint/format/diff gate, attributed` |
| 4 | Floor verification | — | **Confirmed** — see `### Floor verification` |

Both `ruff` invocations are repo-wide and read-only. `--fix` was never passed: it would rewrite ~55 package files a concurrent session has dirty.

### The four failing rows

Re-measured independently in this pass; nothing inherited.

```text
FAILED tests/optimizer/test_walker.py::test_divergent_key_windows_shared_payload_uses_none_key
FAILED tests/orders/test_inputs.py::test_ensure_field_specs_derives_the_unset_sentinel_from_the_family_declaration
FAILED tests/test_sets_mixins.py::test_permission_family_config_stays_on_each_set_class
FAILED tests/test_sets_mixins.py::test_filter_normalizer_honors_a_subclass_unset_sentinel_override
4 failed, 7148 passed, 42 skipped in 62.67s
```

**Set comparison against the record.** Slice 1's Worker 3 and Slice 1's Worker 1 each ran `uv run pytest tests/ --no-cov` — the **package tree only** — and recorded `4 failed, 6188 passed, 40 skipped`. This gate runs the **full sweep across all three trees**, so the passed / skipped totals differ by construction (`7148` vs `6188`, `42` vs `40`); the totals are not the comparison. **The failing node-id set is identical, member for member, to the recorded one.** No row was added, none dropped.

**The deselect control, run at this pass's own scope rather than inherited.** Slice 1's control ran at `tests/`; this one runs at the gate's scope, because a control at a narrower scope does not settle the wider one:

```shell
uv run pytest --no-cov -q \
  --deselect tests/types/test_base.py::test_meta_required_overrides_forces_non_null_file_output \
  --deselect tests/types/test_base.py::test_meta_required_overrides_forces_non_null_image_output \
  --deselect tests/types/test_base.py::test_meta_nullable_overrides_on_a_file_column_is_a_no_op
```

```text
<the identical four FAILED lines>
4 failed, 7145 passed, 42 skipped in 60.19s
```

`7148 - 3 = 7145`, and the failing set survives the removal of everything this cycle added. **This cycle's diff neither causes nor masks these four** — a measurement at the gate's own scope, not an argument.

**Evidence a worker can produce; the verdict is not one of them.**

- **Are the failing rows or their code in this cycle's diff?** No, on both counts. This cycle's whole source diff is `tests/types/test_base.py` (+57, −0); the four rows live in `tests/optimizer/`, `tests/orders/` and `tests/test_sets_mixins.py`, none of which imports anything this diff touches.
- **The tracebacks name a mid-refactor seam, not a file/image one.** Two distinct signatures, neither reachable from the file/image surface this cycle graded:
  - `assert [(None, ConnectionWindowBounds(offset=0, limit=2, reverse=False), None)] == [(None, (0, 2, False), None)]` — a tuple being converted to a structured object inside `optimizer/walker.py`, which is ` M`.
  - `TypeError: ActiveInputPermissionAttrs.__init__() got an unexpected keyword argument 'unset_sentinel'` (from `dataclasses.replace`) and `AttributeError: 'ActiveInputPermissionAttrs' object has no attribute 'related_attr'` — a dataclass losing fields while callers still pass them, in `sets_mixins.py`, which is ` M`.
- **What no worker can say:** whether these four are green at a clean `HEAD`. `BUILD.md` `## Claims are proven mechanically, never accepted on prose` is explicit that a failing test is **not worker-verifiable at all** — reproducing it needs the whole tree at `HEAD`, and this tree is legitimately dirty with a concurrent session's work. **Recording the claim plus this evidence and escalating to the maintainer discharges the obligation.** Not investigated, not edited, not reverted (`AGENTS.md` rule 34).

**Grading.** The suite is not green, and **that is not this cycle's failure.** Escalated to the maintainer as catalog item 1. It does not block `final-accepted`.

### The lint/format/diff gate, attributed

`ruff format --check .` and `ruff check .` both pass **repo-wide**, exit `0` — so the concurrent session's ~55 dirty package files carry no format or lint failure to separate out. Nothing to attribute on those two.

`git diff --check` exits `2` with **4 hits**, and every one is in a single file:

```text
docs/feedback2.md:3: trailing whitespace.
docs/feedback2.md:4: trailing whitespace.
docs/feedback2.md:5: trailing whitespace.
docs/feedback2.md:6: trailing whitespace.
```

```shell
git diff --check | grep -oE '^[^:]+' | sort -u   # -> docs/feedback2.md (only)
```

**Attributed to the concurrent session, by measurement:**

- The file is **empty at `HEAD`** and carries **0** trailing-whitespace lines there; the working copy carries **4**. The whitespace arrived with the concurrent session's 276-line write.
- Its own header names `docs/bug_hunt/bug_hunt-0_0_15.md` as its companion — a file in the plan's enumerated untracked baseline population.
- Its mtime `19:48:07` precedes this cycle's first write.
- **This cycle never touched it.** It appears in no worker's written-files list in any of the four prior artifacts, and it is not in this cycle's writable surface.

**The same gate restricted to this cycle's own tracked diff passes:**

```shell
git diff --check -- tests/types/test_base.py docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md
# exit 0, no output
```

**Grading.** A whitespace failure in a file this cycle never touched, dirty from a concurrent session, is a **pre-existing-at-baseline** hit and does not block `final-accepted` (`worker-1.md` `## Final test-run gate`). A hit in `tests/types/test_base.py`, the spec, or the rationale companion **would** block; there is none. Recorded for the maintainer, who owns the commit and can decide whether to have that session strip it.

### Floor verification

**Slice 1's declared scope — confirmed, and confirmed by reading the venv rather than the artifact's prose.**

- **Declared by:** `bld-037-slice-1-code_conformance.md` `### Floor-verification scope (re-declared)` — the plan's `none by default` was re-declared because the new tests construct a `DjangoType` through `__init_subclass__` and read the annotations Strawberry consumes, which `BUILD.md` `### When it is required` lists as "schema and type construction against Strawberry internals".
- **Owning pass:** Slice 1's **Worker 2 build pass**. Slice 1's Worker 3 independently re-ran the three new node ids in the same venv (`3 passed in 1.16s`), and Slice 1's Worker 1 confirmed the record at final verification.
- **Venv:** `/tmp/dsf-floor-037`, outside the working tree. **Still present at this gate.**
- **Resolved versions, read in this pass** (`uv pip list --python /tmp/dsf-floor-037/bin/python`, plus `/tmp/dsf-floor-037/bin/python -V`):

```text
Python 3.10.19
django                      5.2.16
strawberry-graphql          0.316.0
channels                    4.3.2
django-filter               26.1
djangorestframework         3.18.0
pytest                      9.1.1
pytest-django               4.14.0
```

These are exactly the floor point `BUILD.md` `## Floor verification` states — **read from that section in this pass**, never from memory or from a number restated in a role file or a prior artifact.

- **Focused scope as run:** the three new node ids plus the existing `spec-037` file-override block in `tests/types/test_base.py`, six node ids given in full on the command line, `--no-cov`, no `--cov*` flag.
- **Result: PASS — `6 passed in 1.30s`**, session header confirming `Python 3.10.19` / `django: version: 5.2.16`.
- **The shared `.venv` was not mutated, verified rather than asserted.** Read in this pass: `django 6.1`, `strawberry-graphql 0.324.0`, `Python 3.14.2`. A leaked `--python` would have pulled it to `5.2.16` / `3.10`; it did not. (Slice 1 recorded the shared venv's Django and Python but never its `strawberry-graphql`, so `0.324.0` is a **first reading**, not a delta — stated so no later pass reads it as drift. This is why `BUILD.md` forbids stating `.venv`'s versions from memory.)

**Slice 0, Slice 2 and the integration pass declared `none` — confirmed, with the reason each recorded.** All three are procedural / documentation passes writing no `.py` file and touching no Django / Strawberry / channels integration seam:

| Pass | Declaration on disk | Confirmed |
| --- | --- | --- |
| Slice 0 (`bld-037-slice-0-…`) | `Not applicable; plan declares floor-verification scope none.` | yes — no source, no framework seam; its whole diff is spec + companion Markdown |
| Slice 2 (`bld-037-slice-2-…`) | `Not applicable; this slice writes no .py file and declares floor-verification scope none.` | yes — same |
| Integration (`bld-037-integration.md`) | `Not applicable; this pass writes no .py file.` | yes — same |

**No declared floor scope went unrun**, so there is no `revision-needed` on this clause.

### Staged-anchor sweep — re-measured at the gate

`BUILD.md` `## Cross-slice integration pass` step 6 owns this sweep and the integration pass ran it; re-derived here because the gate is the last pass that can see a late anchor, and because a zero must be distinguishable from an unrun sweep. zsh does **not** word-split, so arrays are used and the population is printed first.

```text
tracked source/test/example/script files: 440
untracked in those trees: 1
037 anchors (TODO(spec-037 | TODO-{ALPHA,BETA,STABLE}-037): 0
```

**Negative controls, same shell, same population:** the card-id grammar hits **30** times and the `TODO(spec-NNN` grammar **25** times for *other* cards. Both instruments are demonstrably live in this tree; they hit `037` zero times.

**One inherited count corrected.** The integration pass's prose reports the second control as "22", but the counts in its own printed `uniq -c` table sum to **25**, which is what this pass measures. The control's conclusion is unaffected (both are far above zero); the number is corrected here rather than propagated.

### Cross-artifact read

All four prior artifacts were read **in full, in order**, before anything above was written: `bld-037-slice-0-rationale_extraction.md` (278 lines), `bld-037-slice-1-code_conformance.md` (846), `bld-037-slice-2-spec_reconciliation.md` (399), `bld-037-integration.md` (372). All four carry `Status: final-accepted`. Plus `AGENTS.md`, `START.md`, `docs/builder/BUILD.md`, `docs/builder/ARTIFACT.md`, `docs/builder/worker-1.md`, `docs/builder/bld-003-final.md`, the build plan, the active spec and its companion, and `docs/builder/worker-memory/worker-1.md` (read first). No other worker's memory file was opened.

**The build plan's `spec-048` version, verified corrected.** The integration pass's `### Routed to the maintainer` item 4 recorded that the plan's `## Worker-0 verification pass` D1 named `spec-048` as `0.0.17`, a version the card never shipped at, and that the plan was not writable by that pass. Re-measured here:

```shell
grep -n '0\.0\.17' docs/builder/build-037-upload_file_image_mapping-0_0_11.md \
  docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md \
  docs/SPECS/appx/spec-037-upload_file_image_mapping-0_0_11-rationale.md
# -> no match in any of the three
```

The plan's D1 now reads `` `spec-048` (commit `567cc6d0`) ``, with no version at all. **Worker 0 corrected it; the corpus carries zero `0.0.17` occurrences outside the integration artifact's own record of the finding** (2 lines, which are the historical record and correctly retain the wrong value they describe). Catalog item 4 is closed on this measurement.

### Deferred work catalog

The next spec author's reading list. Every per-slice and integration artifact's `### Notes for Worker 1 (spec reconciliation)`, `### What looks solid`, `### DRY findings`, `### Routed to the maintainer` and `### Not a finding` sections were walked. **Five items.**

1. **Four rows fail the full package sweep; only the maintainer can confirm they are pre-existing.** Source: `bld-037-slice-1-code_conformance.md` `### Escalation to the maintainer: four failing rows in the full package sweep` and `### Notes for Worker 1`; `bld-037-slice-2` `### Routed to the maintainer` item 3; `bld-037-integration.md` `### Routed to the maintainer` item 3. Licensing rule, not a spec line: `BUILD.md` `## Claims are proven mechanically, never accepted on prose` — a failing test at `HEAD` is not worker-verifiable at all. The rows are `tests/optimizer/test_walker.py::test_divergent_key_windows_shared_payload_uses_none_key`, `tests/orders/test_inputs.py::test_ensure_field_specs_derives_the_unset_sentinel_from_the_family_declaration`, `tests/test_sets_mixins.py::test_permission_family_config_stays_on_each_set_class`, `tests/test_sets_mixins.py::test_filter_normalizer_honors_a_subclass_unset_sentinel_override`; all four sit in the concurrent session's dirty surface, and the gate's own deselect control proves this cycle's diff neither causes nor masks them. **Needs a clean `HEAD` tree.**

2. **`docs/GLOSSARY.md`'s `DjangoFileType` / `DjangoImageType` / `Meta.required_overrides` entries publish contracts this cycle corrected in the spec, and nobody has checked them against the post-`spec-048` shape.** Source: `bld-037-slice-2-spec_reconciliation.md` `### Routed to the maintainer` item 1; `bld-037-integration.md` `### Routed to the maintainer` item 1. Licensed by the build plan's `## Cycle shape` scope fence, which puts `docs/GLOSSARY.md` out of scope for this cycle. The spec now states `name` / `size` / `url` (+ `width` / `height`) as the default subfields with `path` behind `Meta.filesystem_path_fields`; whether the glossary still says the old four-field shape is unmeasured.

3. **`DjangoFilePathType` / `DjangoImagePathType` are root-exported, and their `docs/GLOSSARY.md` / `docs/TREE.md` presence was unverifiable inside the fence.** Source: `bld-037-slice-2` `### Routed to the maintainer` item 2; `bld-037-integration.md` item 2. Same fence licenses the deferral. They are `spec-048`'s to own; flagged because this cycle introduced them into `spec-037`'s vocabulary, where they previously had **zero** occurrences (the finished spec now carries 8 and 7).

4. **CLOSED — the build plan's wrong `spec-048` release version.** Source: `bld-037-integration.md` `### Routed to the maintainer` item 4 and `### Spec changes made (Worker 1 only)` row 1. The companion was fixed in the integration pass; the plan was not writable by it and was routed to the maintainer. **Worker 0 has since corrected the plan**, verified at this gate: zero `0.0.17` occurrences in the plan, the spec, or the companion. Listed so the next author does not re-chase it from the integration artifact.

5. **No file-column-specific read-side `Meta.exclude` test, graded Low and deliberately not planned.** Source: `bld-037-slice-1-code_conformance.md` `### Notes for Worker 1 (spec reconciliation)`, `Not a finding, do not re-raise` item (b). No spec line licenses it; the reason recorded is that `Meta.exclude` is name-keyed with **no** file branch in `types/base.py::_select_fields` and the write side is already pinned, so the gap is a coverage nicety rather than an unpinned contract. A future spec touching the read-side `Meta` surface should decide whether to add it.

**Closed in-cycle, explicitly not deferred — do not re-open.** Recorded here so the next author can tell a settled ruling from an open item: Slice 1's single Low (the third test's annotation assertion overlapping `::test_filesystem_path_fields_absent_leaves_every_column_pathless`) was **ruled `keep as-is`** at Slice 1's final verification, with one clause of the finding refuted at source; `__version__` being `0.0.15` against this card's `0.0.11` cut is **not** stale (Decision 10 and DoD item 7 describe a cut that happened); Decision 7's "three net-new root exports" and Decision 8's opening sentence are **card-scoped completion claims** kept deliberately; the one moved Risks sentence whose Pillow premise is false at `HEAD` is corrected in the companion's `## Provenance of this record` rather than inside moved text; and `## Implementation plan`'s closing `scalars.py` paragraph was inspected and left because removal *is* the correction it names.

### Every count in this artifact, with the command that produced it

| Count | Command | Result |
| --- | --- | --- |
| dirty paths in the tree | `git status --short \| wc -l` | 114 |
| this cycle's dirty paths | `git status --short -- <8 paths>` | 8 (2 ` M`, 6 `??`) |
| this cycle's tracked diff | `git diff HEAD --numstat -- <2 paths>` | spec `298 495`, test `57 0` |
| spec / companion size | `wc -l -c <both>` | 1,666 / 104,947 and 971 / 61,019 |
| full sweep | `uv run pytest --no-cov -q` | 4 failed, 7148 passed, 42 skipped |
| deselect control | same + 3 `--deselect` | 4 failed, 7145 passed, 42 skipped |
| `git diff --check` hits | `git diff --check \| wc -l` | 8 lines = 4 hits, 1 file |
| `docs/feedback2.md` trailing-ws, `HEAD` vs working | `grep -c ' $'` on the `HEAD` blob and the working copy | 0 vs 4 |
| ruff format scope | `uv run ruff format --check .` | 438 files already formatted |
| staged-anchor population | zsh array over `git ls-files` | 440 tracked + 1 untracked |
| `037` anchors | `grep -rEo 'TODO\(spec-037\|TODO-(ALPHA\|BETA\|STABLE)-037' …` | 0 |
| negative controls | the two other-card grammars, same population | 30 and 25 |
| new node ids present | `grep -c` over the three `def test_` names | 3 |
| `0.0.17` in plan / spec / companion | `grep -n '0\.0\.17' <three files>` | 0 |

### DRY check across the cycle

No new duplication, and none possible: this pass writes no `.py` file, no helper, no constant and no test. Against the three slices and the integration pass there is no shared shape to collide with — the cycle's entire source diff remains three test functions in one pre-existing test file, and `git diff -- django_strawberry_framework/__init__.py` is empty, so no public export changed. The cross-slice DRY question was answered mechanically at the integration pass (added top-level `def _make_` = 0, total unchanged at 6) and is not re-fought here.

### Failability proofs

`None; this pass introduced no new boundary.` This pass lands no runtime code. The proof obligations it *does* carry are the measurements above, and **each carries its own negative control**, which is what makes a zero mean something:

- the failing-set comparison is paired with the **deselect control at this pass's own scope**, so "not reachable from this cycle's diff" is a measurement rather than an argument;
- the `git diff --check` attribution is paired with the same command **restricted to this cycle's two tracked files** (exit 0), so a clean cycle-scope result is distinguishable from an unrun check;
- the staged-anchor sweep is paired with the two grammars run against the same printed population for **other** cards (30 and 25 hits), so a zero from a mis-typed pattern would show as a zero there too;
- the floor confirmation reads the venv's resolved versions **and** the shared `.venv`'s, so a leaked `--python` would be visible as movement in the second reading.

`BUILD.md`'s Worker-1 delta was also discharged: Slice 1's single failability record was audited field by field at that slice's final verification and re-run independently by Worker 3 at the recorded scope with an identical node-id set and a byte-proved revert. **No fail-open shape landed** — the cycle's diff is three test functions and five assertions over an unchanged code path, with no expression, guard, or default that could silently substitute a permissive answer.

### Hot-path budget

`Not applicable; plan declares no hot path.`

### Spec status-line re-verification (owed by every Worker 1 spawn)

`worker-1.md` `## Spec status-line re-verification (every Worker 1 spawn)`. Read spec:1-40 in this spawn. The header states `Shipped in 0.0.11 (card DONE-037-0.0.11)`, `Status: **SHIPPED (0.0.11)** … all four slices final-accepted`, and predecessors `spec-036` / `spec-001`, both of which exist on disk. It carries no "not yet shipped" / "remains to be" claim, references no predecessor doc this build deleted, and this pass falsified nothing in it. Its opener's `mutations/inputs.py::model_column_write_annotation` citation — Slice 2's N12 replacement for the dead seam substring — resolves. **No status-line edit owed, and none made:** the maintainer's dispatch also fences this pass out of the spec entirely, and the spec's byte count is unchanged from the integration pass's post-edit figure, which proves the non-edit rather than asserting it.

---

## Final verification (Worker 1)

### Summary

The gate ran in full. **Django's consistency checks, `ruff format --check .` and `ruff check .` all pass repo-wide.** Two commands do not exit `0`, and both were attributed by measurement rather than argued:

- **The full sweep is `4 failed, 7148 passed, 42 skipped`.** The failing node-id **set is identical** to the one Slice 1's Worker 3 and Worker 1 each recorded; only the passed / skipped totals differ, because this gate sweeps all three trees where their runs swept `tests/` alone. The deselect control, re-run here at the gate's own scope, returns `7148 - 3 = 7145` with a byte-identical failing set — **this cycle's diff neither causes nor masks any of the four.** All four are in the concurrent session's dirty modules (`optimizer/walker.py`, `orders/*`, `sets_mixins.py`), and their tracebacks name a dataclass and a tuple-to-object conversion mid-refactor. A failing test at `HEAD` is not worker-verifiable at all; recorded, evidenced, and escalated to the maintainer as catalog item 1.
- **`git diff --check` exits `2` on 4 trailing-whitespace hits, all in `docs/feedback2.md`** — a file empty at `HEAD`, filled with 276 lines by the concurrent session at mtime `19:48:07`, before this cycle's first write, and never touched by any worker in this cycle. The same command restricted to this cycle's two tracked files exits `0`.

**Neither failure is this cycle's**, so neither routes back through a slice loop. The cycle's own diff — `tests/types/test_base.py` (+57, −0), the reconciled spec, and the new rationale companion — passes every clause of the gate that applies to it. Floor verification is confirmed for the one declared scope by reading `/tmp/dsf-floor-037` in this pass (Python 3.10.19 / django 5.2.16 / strawberry-graphql 0.316.0, `6 passed`), with the shared `.venv` unmutated; Slices 0 and 2 and the integration pass declared `none` and each is confirmed with its recorded reason. The staged-anchor sweep is clean against a printed 440-file population with two live negative controls. The deferred-work catalog carries **five items**, one of them already closed by Worker 0's correction of the build plan.

One inherited number was corrected rather than propagated: the integration pass's second negative control is **25**, not the 22 its prose states — its own printed table sums to 25.

### Spec changes made (Worker 1 only)

**None.** The maintainer's dispatch fences this pass to `docs/builder/bld-037-final.md` and `docs/builder/worker-memory/worker-1.md`, and nothing found here needed a spec edit. **Proved by non-edit rather than asserted:** `docs/SPECS/spec-037-upload_file_image_mapping-0_0_11.md` is 1,666 lines / 104,947 bytes and `docs/SPECS/appx/spec-037-upload_file_image_mapping-0_0_11-rationale.md` is 971 lines / 61,019 bytes — byte-for-byte the integration pass's recorded post-edit figures, so neither file has been written since that pass closed.

**No deferral reasons are owed** on a checklist box: this pass's `### Dispatched findings checklist` carries one box, ticked, with the gate run.

### Final status

`final-accepted`. Every command in `BUILD.md` `## Final test-run gate` ran, in order, with its real exit code recorded. The two non-zero exits are both attributed by measurement to a concurrent session's work in files this cycle never touched, escalated to the maintainer as the only party who can run a clean `HEAD` tree, and do not block acceptance. The floor-verification backstop has a complete record to confirm for the one declared scope and a recorded `none` for the other three passes. The deferred-work catalog is written. Worker 0 may mark the build plan's final checkbox.

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
