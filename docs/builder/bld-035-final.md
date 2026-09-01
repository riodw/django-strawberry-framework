# Build: Final test-run gate — spec-035 retrospective reconciliation cycle

Spec reference: `docs/SPECS/spec-035-optimizer_hardening-0_0_10.md` (whole file; the cycle's reconciled contract)
Rationale companion: `docs/SPECS/appx/spec-035-optimizer_hardening-0_0_10-rationale.md`
Build plan: `docs/builder/build-035-optimizer_hardening-0_0_10.md`
Status: final-accepted

**Shape note.** This is `docs/builder/BUILD.md` `## Final test-run gate`, the cycle's last pass. `worker-1.md` `## Final test-run gate` gives the whole gate to Worker 1, so the `## Build report (Worker 2)` and `## Review (Worker 3)` sections of `docs/builder/ARTIFACT.md` are not applicable and the gate record lives under `## Gate report (Worker 1)` below. The cycle's `bld-035-integration.md` closed `final-accepted` after a consolidation pass; this artifact is the gate that follows it.

**Cycle framing that changes how a failure is graded.** This cycle wrote **no runtime code**: Slices 1 and 3 are `.md` only, Slice 2 is comment and docstring text in four `.py` files. Re-proved at this gate rather than accepted (`### Zero-executable-change, re-proved at the gate`). The working tree is broadly dirty from concurrent maintainer sessions (`AGENTS.md` 34, `START.md` "Concurrent sessions"), and the build plan's `### Baseline-dirty out-of-scope files` names the exceptions. Every gate result below is attributed to a file and a cause before it is graded.

---

## Plan (Worker 1)

### DRY analysis

- **Helper inventory checked.** Not applicable, and for the cycle's standing reason rather than a skip: `worker-1.md` `### Package-wide helper inventory before helper planning` gates *proposing helper-like logic*, and this pass proposes none. It writes two Markdown files and no `.py`. The one measurement that would make an inventory meaningful was taken anyway and is recorded below: the cycle's whole `.py` diff is docstring-blanked AST-identical to `HEAD`, so nothing under `django_strawberry_framework/` has an executable line to duplicate.
- **Existing patterns reused.** The gate's command list is `BUILD.md` `## Final test-run gate` verbatim, in its declared order, extended by the four cycle-specific gate rows the dispatch adds (spec glossary, trailing commas, the five shipped-`.py` anchors, the wrap-aware staged-anchor sweep). The `### Deferred work catalog` shape is that same section's, including its no-deferrals literal. The artifact shape is `docs/builder/bld-003-final.md`'s, the immediately preceding execution of this pass.
- **New helpers justified.** None. Three throwaway scripts (`anchors.py`, `sweep.py`, `pop.py`) live **outside** the repository, under the session scratchpad, and write nothing into the tree.
- **Duplication risk avoided.** The live risk in this pass is the catalog: `bld-035-integration.md` `### Step 5` already carries a D1-D11 inventory, and copying it would reproduce whatever is wrong in it. That inventory was itself built to correct a **derived** roll-up (Slice 3's "items 1-4 are the four Slice 2 recorded", which dropped two items), and its own consolidation section then caught an **inherited-not-measured** figure inside it (seven vs six). So every item below was re-derived from the source artifacts and from the tree, with the command quoted; two of the eleven did not reproduce as written and are corrected in place.

### Implementation steps

1. Read the standing docs, the role file, the active spec and rationale, the build plan, and all four prior `bld-035-*` artifacts in full (`BUILD.md` `## Cross-slice integration pass` — no "as needed").
2. Re-verify the spec's status/header lines (`worker-1.md` `## Spec status-line re-verification`, owed by every Worker 1 spawn).
3. Run every gate command in `BUILD.md` `## Final test-run gate` order and record each one's real result, plus the four cycle-specific rows.
4. Attribute every failure to a file and a cause before grading it; record and escalate anything pre-existing at `HEAD` or concurrent rather than fixing it.
5. Record the floor-verification disposition for the plan's declared scope.
6. Author the `### Deferred work catalog` by walking every artifact's `### Notes for Worker 1 (spec reconciliation)`, `What looks solid`, `DRY findings`, and review sections — re-deriving, never inheriting.
7. Set `Status:` and append a memory entry.

### Test additions / updates

None. This pass lands no source and no test; the gate itself is the verification, and its full-sweep command is recorded below.

### Implementation discretion items

None reserved. The gate has no downstream worker, so nothing is delegable.

### Dispatched findings checklist

Spec-035's `## Slice checklist` covers the shipped `DONE-035-0.0.10` card and was audited at each slice's own final verification; this is not a review round. Per `worker-1.md` planning step 8 the boxes below are the gate's own obligations, drawn from `BUILD.md` `## Final test-run gate`, `worker-1.md` `## Final test-run gate`, and this cycle's dispatch. Worker 1 both performs and ticks; there is no later pass to audit them, so each box cites the evidence in this artifact that discharges it.

- [x] `uv run pytest --no-cov` run, full sweep across all three test trees, no `--cov*` flag in any form, result recorded (`### Gate commands, in BUILD.md order`, row 1).
- [x] Line coverage neither inspected nor asserted (`BUILD.md` `## Coverage is the maintainer's gate, not a worker's tool`).
- [x] `uv run python examples/fakeshop/manage.py check` run and recorded (row 2).
- [x] `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` run and recorded (row 3).
- [x] `uv run ruff format --check .` run read-only, never `--fix`, and recorded (row 4).
- [x] `uv run ruff check .` run read-only, never `--fix`, and recorded (row 5).
- [x] `git diff --check` run and recorded, its one failure attributed by file and cause (row 6, `### The one gate failure, attributed`).
- [x] Floor verification: the plan's declared scope is `none`, so `No floor-verification scope declared.` is written out rather than the section silently omitted, and the floor is cited without being run (`### Floor verification`).
- [x] `scripts/check_spec_glossary.py --spec docs/SPECS/spec-035-...md` run, exit 0 recorded (row 7).
- [x] `scripts/check_trailing_commas.py --check` run over both spec `.md` files and all four cohort `.py` files, exit 0 recorded (row 8).
- [x] The five shipped-`.py` `#"substring"` spec anchors **re-derived from the four cohort `.py` files**, not copied from a list, and each counted in the spec (row 9, `### The five shipped-.py spec anchors, re-derived`).
- [x] The two out-of-scope `tests/types/test_resolvers.py` anchors targeting `types/resolvers.py` checked against the source they cite, not against the spec — one resolves, one does not (`### The five shipped-.py spec anchors, re-derived`, and catalog **D12**).
- [x] Staged-anchor sweep run **wrap-aware** (whitespace flattened across newlines, plus a comment-continuation variant), population size printed (row 10, `### Staged-anchor sweep, re-measured at the gate`).
- [x] `### Deferred work catalog` authored from **every** artifact, re-derived rather than inherited, with the source artifact section named per bullet.
- [x] The out-of-scope raw-line-number citation population re-derived with an instrument that survives both a wrap and a `#` comment-continuation marker, and recorded as an **occurrence list** rather than a total (catalog **D4**).
- [x] Every stated count is command-produced and the command is quoted beside it (`### Every count in this artifact, with the command that produced it`).
- [x] `HEAD` read **read-only** via `git show HEAD:<path>` into a scratch path outside the repo; no `git stash` / `checkout` / `restore` / `worktree`, no commit, no branch.
- [x] No `.py` file written; no `.md` written other than this artifact and `docs/builder/worker-memory/worker-1.md`; no `scripts/build_*.py` generator run; no rendered doc regenerated.

---

## Gate report (Worker 1)

### Working tree, re-derived

`HEAD` re-derived rather than quoted from the plan:

```shell
git rev-parse --short HEAD          # 7542d45d
```

The cycle's own paths, `git status --short` over the cohort:

| Path | State | Owner |
|---|---|---|
| `django_strawberry_framework/optimizer/walker.py` | ` M` | Slice 2 |
| `tests/optimizer/test_walker.py` | ` M` | Slice 2 |
| `tests/optimizer/test_extension.py` | ` M` | Slice 2 |
| `tests/types/test_resolvers.py` | ` M` | Slice 2 (mid-flight partition correction) |
| `docs/SPECS/spec-035-optimizer_hardening-0_0_10.md` | ` M` | Slices 1 and 3 |
| `docs/SPECS/appx/spec-035-optimizer_hardening-0_0_10-rationale.md` | `??` (new) | Slices 1 and 3 + consolidation |
| `docs/builder/build-035-…md`, `bld-035-slice-{1,2,3}-*.md`, `bld-035-integration.md` | `??` (new) | Worker 0 / this cycle |

Everything else `git status` reports dirty is a concurrent session's, per the build plan's `### Baseline-dirty out-of-scope files`. Two of those matter to this gate and are named where they matter: `examples/fakeshop/test_query/test_library_api.py` (the surviving anchor, catalog **D1**) and `docs/feedback.md` (the one gate failure, below). Also dirty and untouched: `docs/builder/DONE/build-046-transport_security-0_0_15.md`, which is in this pass's do-not-touch list.

### Zero-executable-change, re-proved at the gate

`BUILD.md` `## Claims are proven mechanically, never accepted on prose` grades "carried over unchanged" as a claim to re-derive, not to accept. It is the load-bearing claim of the whole cycle — it is why a `pytest` failure in this tree would not be this cycle's — so I ran it myself against pristine `HEAD` obtained read-only:

```shell
git show HEAD:<path> > <scratchpad>/head/<flattened-name>      # four cohort files
# then, per file: ast.dump(blanked(HEAD)) == ast.dump(blanked(WORK))
```

| File | Docstrings at `HEAD` | Docstrings in tree | Plain AST identical | Docstring-blanked AST identical |
|---|---|---|---|---|
| `django_strawberry_framework/optimizer/walker.py` | 37 | 37 | no | **yes** |
| `tests/optimizer/test_walker.py` | 192 | 192 | no | **yes** |
| `tests/optimizer/test_extension.py` | 171 | 171 | **yes** | **yes** |
| `tests/types/test_resolvers.py` | 48 | 48 | no | **yes** |

Equal docstring counts per file are what make a *moved* docstring surface rather than slip through a name-keyed compare. **Negative control**, run in the same script so a vacuous instrument would be visible: perturbing one executable token in `walker.py` (`if db_field is not None and enable_only` -> `if db_field is None and enable_only`) makes the blanked comparison report **False**. The instrument can fail; it did not.

Read against the diff, the four files' entire change set is: two `TODO(spec-035…)` -> `TODO(BACKLOG polymorphic_interface_connections - the abstract-return optimizer entry card)` retargets in `walker.py`, two more in `test_walker.py` / `test_extension.py`, and five raw-line-number spec citations rewritten as `Edge cases #"substring"` anchors. No executable line, so no boundary could have been introduced and no fail-open shape could have landed.

### Gate commands, in `BUILD.md` order

| # | Command | Result |
|---|---|---|
| 1 | `uv run pytest --no-cov` | **PASS** — `7069 passed, 42 skipped in 69.40s`, exit **0**. Full sweep across all three test trees, `xdist` parallel. No `--cov*` flag in any form; no line-coverage figure was inspected or asserted. |
| 2 | `uv run python examples/fakeshop/manage.py check` | **PASS** — `System check identified no issues (0 silenced).`, exit **0**. |
| 3 | `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` | **PASS** — `No changes detected`, exit **0**. |
| 4 | `uv run ruff format --check .` | **PASS** — `435 files already formatted`, exit **0**. Read-only; never `--fix`. (The `COM812`-conflict warning is the repo's standing configuration notice, not a finding.) |
| 5 | `uv run ruff check .` | **PASS** — `All checks passed!`, exit **0**. Read-only; never `--fix`. |
| 6 | `git diff --check` | **FAIL**, exit **2** — four hits, all in `docs/feedback.md` (lines 3, 4, 5, 6), all trailing whitespace on **added** lines. Attributed below; not this cycle's, and not blocking. |
| 7 | `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-035-optimizer_hardening-0_0_10.md` | **PASS** — `OK: 23 terms - all have glossary entries and at least one spec link.`, exit **0**. This is also the exact invocation the spec's Definition-of-done item 1 now carries, which Slice 3 corrected from a pre-archive path that exited 2. |
| 8 | `uv run python scripts/check_trailing_commas.py --check <2 spec .md + 4 cohort .py>` | **PASS** — exit **0** over `spec-035-…md`, `…-rationale.md`, `optimizer/walker.py`, `tests/optimizer/test_walker.py`, `tests/optimizer/test_extension.py`, `tests/types/test_resolvers.py`. Covers ASCII-only source, line length, the trailing-comma layout, and the `.md` link-definition scaffold. |
| 9 | Five shipped-`.py` `#"substring"` spec anchors, re-derived and counted | **PASS** — all five resolve **exactly once**. Table below. |
| 10 | Wrap-aware staged-anchor sweep | **PASS with one expected survivor** — exactly one `TODO(spec-035` in shipped source across 571 `.py` files, the baseline-dirty `test_library_api.py` site whose work has not shipped. Catalogued as **D1**. |

### The one gate failure, attributed

`git diff --check` exits 2 on four added lines in `docs/feedback.md`:

```
docs/feedback.md:3: trailing whitespace.
docs/feedback.md:4: trailing whitespace.
docs/feedback.md:5: trailing whitespace.
docs/feedback.md:6: trailing whitespace.
```

Attribution, derived rather than assumed:

- **The file is not in this cycle's cohort.** It appears in no writable list in `docs/builder/build-035-optimizer_hardening-0_0_10.md`, and no `bld-035-*` artifact records an edit to it. The build plan's `### Baseline-dirty out-of-scope files` covers it under "everything else `git status` reports dirty outside this plan's writable lists" — the pre-flight baseline exception `BUILD.md` `## Final test-run gate` contemplates.
- **The content is not this cycle's subject.** The added lines are a concurrent session's `spec-050` architectural review, dated 2026-08-31, targeting card `WIP-ALPHA-050-0.0.15`.
- **`HEAD` was read read-only to confirm the whitespace is added, not pre-existing:** `git show HEAD:docs/feedback.md` into a scratch path outside the repo returns a **0-line** file with **0** trailing-whitespace lines. Every flagged line is therefore an uncommitted addition by a concurrent writer.
- **Disposition:** recorded and escalated to the maintainer, per the framing rule for a concurrent or pre-existing-at-`HEAD` condition. Not fixed (`AGENTS.md` 34 forbids editing or reverting a concurrent session's dirty file), not reverted, and **not blocking** `final-accepted`: no file this cycle wrote is implicated. The integration pass reached the same reading independently (`bld-035-integration.md:601`), which is why this is a second confirmation rather than a first sighting.

Scoped re-run, to show the cycle's own surfaces are clean: `git diff --check -- docs/SPECS/ django_strawberry_framework/ tests/ docs/builder/` is **clean**.

### The five shipped-`.py` spec anchors, re-derived

Re-derived **from the four cohort `.py` files** rather than copied from any artifact's list, with two flatten variants (plain whitespace flatten across newlines; and a flatten that first removes `\n\s*#\s*` comment-continuation markers), then counted in the post-Slice-3 spec with `str.count`. Instrument: `<scratchpad>/w1-final/anchors.py`. It found **7** `#"…"` anchors in the cohort — the five that target the spec, plus two that target a source file.

| Citing site | Anchor | Occurrences in spec |
|---|---|---|
| `django_strawberry_framework/optimizer/walker.py:854` (`_record_relation_access`) | `#"every projection writer checks the gate"` | **1** |
| `tests/optimizer/test_walker.py:4850` (`test_mutation_scalar_only_connection_window_no_only`) | `#"every projection writer checks the gate"` | **1** |
| `tests/optimizer/test_walker.py:4897` (`test_subscription_operation_gated`) | `#"subscription operations are gated identically"` | **1** |
| `tests/optimizer/test_walker.py:4913` (`test_enable_only_defaults_enabled_without_info`) | `#"defaults to enabled"` | **1** |
| `tests/types/test_resolvers.py:1036` (the consumer-`.only()` elision pin) | `#"can defer the FK column (both"` | **1** |

**All five resolve exactly once.** This is the cycle's one cross-slice collision hazard — Slice 2 wrote these anchors into `## Edge cases and constraints` and Slice 3 then rewrote parts of that same section — and it did not fire: Slice 3's edit re-homed the fourth projection writer's path *inside* the first bullet while leaving the bound phrase byte-identical.

**The two out-of-scope anchors, checked against the source they cite (not the spec).** Both pre-date this cycle and are byte-identical to `HEAD` (the cohort diff touches only `tests/types/test_resolvers.py:1035`).

| Citing site | Anchor | Resolves in `django_strawberry_framework/types/resolvers.py`? |
|---|---|---|
| `tests/types/test_resolvers.py:932` | `types/resolvers.py::_build_fk_id_stub #"if related_id is None"` | **yes**, exactly once |
| `tests/types/test_resolvers.py:892` | `types/resolvers.py::_build_fk_id_stub #"instance = root if hasattr(root, "_state") else None"` | **no — 0 occurrences** |

The second does not resolve: the live line at `django_strawberry_framework/types/resolvers.py:149` reads `instance = root if getattr(root, "_state", None) is not None else None`, and `hasattr(root` appears nowhere in that module. `types/resolvers.py` is **clean at `HEAD`** (`git status --short` reports it unmodified) and its `HEAD` content already carries the `getattr` form, so this is pre-existing at `HEAD` and not falsified by anything this cycle did. Recorded as catalog **D12** and escalated; not graded against the spec, and not fixed (this pass writes no `.py`).

### Staged-anchor sweep, re-measured at the gate

`BUILD.md` `## Cross-slice integration pass` step 6, run **wrap-aware**, because a line-oriented `grep` is fail-open on a wrapped citation and produced two false zero counts inside this cycle already. Instrument: `<scratchpad>/w1-final/sweep.py`. Pattern `TODO\(\s*spec-035|TODO-(ALPHA|BETA|STABLE)-035` matched against three variants of each file — raw text, whitespace flattened across newlines, and that flatten with `#` comment-continuation markers removed. Excluded per the step-6 rule: `KANBAN.md`, `KANBAN.html`, `BACKLOG.md`, `docs/review/`, `docs/builder/DONE/`; also excluded as non-repo: `.git`, `.venv`, `node_modules`, `__pycache__`, `dist`, tool caches.

**Population size printed, so a zero is distinguishable from an unrun instrument: 921 files scanned, 16 carrying a match.** Decomposition:

| Class | Files | Verdict |
|---|---|---|
| **Shipped source / tests** | `examples/fakeshop/test_query/test_library_api.py:3680` | **The one survivor.** Legitimate — see below. |
| This cycle's own artifacts | `build-035-…md`, `bld-035-slice-{1,2,3}-*.md`, `bld-035-integration.md` | Prose; per-cycle scratchpads. |
| Worker memory | `worker-memory/worker-{1,2,3}.md` | Scratch, `.gitignore`d. |
| Sibling specs / rationales narrating a card id | `spec-020-…-rationale.md`, `spec-033-…-rationale.md`, `spec-034-…-rationale.md`, `spec-034-…md`, `spec-037-…md` | Prose about `TODO-ALPHA-035` card ids, not anchors. |
| This spec's own companion | `spec-035-…-rationale.md:233` | Slice 1's flagged sentence, quoting the anchor form. |
| Regenerable snapshot | `docs/shadow/current/…walker.overview.md` | A concurrent session's `bug_hunt.py` output at a different commit. |

Narrowed to `.py` only, which is the population the rule is about:

```shell
# same three-variant matcher, restricted to *.py
py files scanned: 571   hits: ['examples/fakeshop/test_query/test_library_api.py']
```

**The survivor is legitimate.** `examples/fakeshop/test_query/test_library_api.py:3680` reads `# TODO(spec-035): extend this live connection-fragment block with the matching-type relation-planning acceptance test required by the test_query README.` — the P3a live matching-type test, which the spec's deferred G3 test plan carries as **carry-forward to the abstract-return optimizer entry card**. `BUILD.md`'s rule ("an anchor whose work this slice shipped must be removed") does not reach it: the work has **not** shipped. The file is baseline-dirty from a concurrent session and named in the build plan's `### Baseline-dirty out-of-scope files`, so no worker in this cycle was permitted to touch it (`AGENTS.md` 34). Catalogued as **D1**, not routed to a re-loop.

Converse measurement, to show the retarget converged: `TODO(BACKLOG` in `.py` returns **five**, all carrying the identical head token `TODO(BACKLOG polymorphic_interface_connections` — `optimizer/selections.py`, `optimizer/walker.py` (twice), `tests/optimizer/test_walker.py`, `tests/optimizer/test_extension.py`. A plain `grep -o 'TODO(BACKLOG[^)]*)'` finds **none** of them, because every one wraps with a `#` continuation inside the parenthesis; that is the fail-open shape the flatten exists to defeat.

### Floor verification

**No floor-verification scope declared.**

The build plan declares `**Floor-verification scope:** none. No slice touches a Django / Strawberry / channels integration seam; no runtime line changes.` Re-verified against the cycle's content rather than accepted: the whole `.py` diff is docstring-blanked AST-identical to `HEAD` (`### Zero-executable-change, re-proved at the gate`), so there is no runtime line whose behavior could differ at the floor. Per `worker-1.md` `## Final test-run gate`, **no floor venv was built and none was run.**

For the record, cited and not run — `BUILD.md` `## Floor verification` is the single canonical statement: the supported floor is Django **5.2.16** on Python **3.10** with strawberry-graphql **0.316.0**.

The shared `.venv` the gate above ran in is **not** the floor; its versions were read rather than recalled (`uv pip list`): Django **6.1**, strawberry-graphql **0.324.0**, channels **4.3.2**, on Python **3.14.2**.

### Hot-path budget

Not applicable; the plan declares no hot path, for the whole cycle. Re-verified the same way: no slice changes runtime behavior, so there is no operation whose cost could move.

### Failability proofs

`None; this cycle introduced no new boundary.` — and the inverse is proved rather than asserted. All three build passes of Slice 2 and both Worker 1 doc slices carry the same negative sentence, and the diff confirms it is true: with zero executable lines changed, no guard, cap, rejection path, or validation branch *could* have been introduced. No fail-open shape landed and none could. This is the present-and-negative form `worker-1.md` `### Failability and fail-open checks` requires; silence there would read identically to not having looked.

### Cross-artifact read

All five prior artifacts read in full, in order, per the strict-reading rule: `bld-035-slice-1-rationale_extraction.md` (161 lines), `bld-035-slice-2-carry_forward_anchors.md` (2,794 lines, three build passes and three reviews), `bld-035-slice-3-spec_reconciliation.md` (363), `bld-035-integration.md` (652, including its consolidation pass), and `build-035-optimizer_hardening-0_0_10.md` (211). Every `Status:` line is `final-accepted`; the build plan's checklist has Slices 1-3 and the integration pass ticked and this gate as the only open box.

### Spec status-line re-verification (owed by every Worker 1 spawn)

Re-read `docs/SPECS/spec-035-optimizer_hardening-0_0_10.md:1-11`. Title, the `Shipped in 0.0.10` lead, `Status:`, `Owner:`, `Predecessors:`, and the rationale-companion pointer all describe the build's current state. The two header-adjacent claims Slices 1 and 2 routed forward are **closed on disk**, confirmed by grep rather than by reading the Slice 3 report:

- The archived-path claim: `:137` now reads "The spec file lives at **`docs/SPECS/spec-035-optimizer_hardening-0_0_10.md`** (this document), archived there by the `docs/SPECS/NEXT.md` Step 8 sweep …"; `grep -n 'docs/spec-035'` returns no pre-archive path anywhere in the spec.
- The `0.0.9` on-disk-version parenthetical is gone from the header; `grep -n '0\.0\.9'` in the spec now returns only `spec-033` / `DONE-033-0.0.9` references, which are correct.

**No spec edit is owed by this pass and none was made.** The gate exposed no spec defect. Control, so that "the spec is clean" is a measurement rather than an absence of looking: the six `_project_scalar_only_window` reference citations in the spec all target `[nested-planner]` and **zero** target `[walker]`; the two in the companion likewise. The stale-symbol class the cycle was built around is closed in both halves of the pair.

### Every count in this artifact, with the command that produced it

| Count | Command / instrument |
|---|---|
| `7069 passed, 42 skipped` | `uv run pytest --no-cov` |
| `435 files already formatted` | `uv run ruff format --check .` |
| 4 `git diff --check` hits, all `docs/feedback.md` | `git diff --check` |
| 0 lines / 0 trailing-whitespace lines in `docs/feedback.md` at `HEAD` | `git show HEAD:docs/feedback.md > <scratchpad>/feedback-head.md; wc -l; grep -cE ' $'` |
| `OK: 23 terms` | `uv run python scripts/check_spec_glossary.py --spec …` |
| docstring counts 37 / 192 / 171 / 48, equal at `HEAD` and in tree | `<scratchpad>/w1-final` AST script over `git show HEAD:<path>` copies |
| 7 `#"…"` anchors in the cohort; 5 spec-targeting, each resolving **1** | `<scratchpad>/w1-final/anchors.py` |
| 0 occurrences of `instance = root if hasattr(root, "_state") else None` in `types/resolvers.py` | `str.count` over the module source |
| 921 files scanned, 16 with a `spec-035` staged anchor, **1** in shipped source | `<scratchpad>/w1-final/sweep.py` |
| 571 `.py` files scanned, **1** `TODO(spec-035` hit | same matcher, `*.py` only |
| **5** `TODO(BACKLOG polymorphic_interface_connections` sites in `.py` | same flatten; a plain `grep -o 'TODO(BACKLOG[^)]*)'` returns 0 |
| **9** out-of-scope raw-line-number spec citations (occurrence list, not a total) | `<scratchpad>/w1-final/pop.py`, 571 `.py` files |
| 12 bare `(line NNN)` self-citations + 2 `cookbook line(s)` sites | `grep -rnoE '\(lines? [0-9]+' --include='*.py'` |
| spec: 6 `_project_scalar_only_window` citations, all `[nested-planner]`, 0 `[walker]` | `grep -o '\[`[^`]*_project_scalar_only_window`\]\[[a-z-]*\]' \| sort \| uniq -c` |
| D10 population: spec 9 `::`-form + 6 `registry.` spans; companion 3 + 3 | per-shape `grep -o … \| wc -l` on both files, owners resolved by `ast` |

### Deferred work catalog

The next spec author's reading list. `bld-035-integration.md` `### Step 5` carries a D1-D11 inventory with D9 closed; per `BUILD.md` `## Claims are proven mechanically, never accepted on prose` I **re-derived** every item from the source artifacts and from the tree rather than copying it. Ten of eleven reproduce. **Two are corrected** (D5's count, D10's figures), **D9 is confirmed closed and is therefore not a deferral**, and **one new item (D12) was found at this gate**.

- **D1 — the fifth carry-forward anchor is unretargeted.** *Sources:* `bld-035-slice-2-…md` `### Notes for Worker 1` (plan pass, Worker 2 pass 1, Worker 3 passes 1-3, Worker 1 final verification item 1); `bld-035-slice-3-…md` `### Notes for Worker 1` item 1; `bld-035-integration.md` `### Step 5` D1 and `### Step 6`. *Licensing spec line:* none — the spec does not license it; `AGENTS.md` 34 and the build plan's `### Baseline-dirty out-of-scope files` do. *Description:* `examples/fakeshop/test_query/test_library_api.py:3680` still reads `# TODO(spec-035): extend this live connection-fragment block with the matching-type relation-planning acceptance test required by the test_query README.` — the **P3a live matching-type test**, which the spec's deferred G3 test plan carries as carry-forward to the abstract-return optimizer entry card. Re-measured at this gate: it is the **only** `TODO(spec-035` occurrence across 571 `.py` files. The file is baseline-dirty with a concurrent session's work, so no worker in this cycle could edit or revert it. It should take the same `TODO(BACKLOG polymorphic_interface_connections - the abstract-return optimizer entry card)` head once that session's work lands. **This is the one anchor that makes the step-6 sweep non-empty**, and it is a recorded deferral, not a finding.

- **D2 — the two package test-tree anchors become deletable if and only if the spec's G3 deferred test plan records their file placement.** *Sources:* `bld-035-slice-2-…md` `### Decision: the two package test-tree anchors are KEPT, retargeted — not deleted` and `### Notes for Worker 1` item 2 (all passes); `bld-035-slice-3-…md` item 2; integration D2. *Licensing spec line:* `docs/SPECS/spec-035-…md:334`, `### Slice 3 — G3 — DEFERRED (carry-forward requirements for the abstract-return optimizer entry card)`. *Description:* the anchors in `tests/optimizer/test_walker.py` and `tests/optimizer/test_extension.py` restate spec test names verbatim, which on DRY alone would make them deletable duplicates — except that each also carries a **file-placement judgement that exists nowhere else**. Both legs re-verified here: the G3 heading at `:334` names **no file**, unlike `:306` (`### Slice 1 — G1 (tests/optimizer/test_extension.py)`) and `:317` (`### Slice 2 — G2 (tests/optimizer/test_walker.py + tests/optimizer/test_extension.py, extend)`); and `real extension execution` occurs **0** times in the spec and **0** times in the companion. Slice 3 deliberately did not write that placement in, because inventing the follow-up card's test-file layout is that card's spec's decision. The condition is unchanged; the anchors stay.

- **D3 — `selections.py`'s reference anchor is the least informative of the five.** *Sources:* `bld-035-slice-2-…md` Worker 3 pass 1 `### Notes for Worker 1` item 3, re-affirmed at passes 2 and 3 and at Slice 2 final verification; integration D3 (**absent from Slice 3's list** — recovered at the integration pass). *Licensing spec line:* none; `selections.py` is outside this cycle's ownership partition by the build plan's `## Declarations` table. *Description:* `django_strawberry_framework/optimizer/selections.py`'s `TODO(BACKLOG …)` body cites the entry contract as `(R1)` **without naming the document that defines it**. Re-measured: `grep -c 'spec-035 Decision'` returns **0** for `selections.py` against **11** in `walker.py`, **8** in `tests/optimizer/test_walker.py`, **2** in `tests/optimizer/test_extension.py`. A reader landing there by `grep` finds the owning card but not the design contract. One clause closes it. **CLOSED 2026-09-01, in this cycle.** The anchor body at `django_strawberry_framework/optimizer/selections.py` #"add a tri-state fragment classifier" now names its defining document in both places the sibling anchors do: it gained `Design contract: spec-035 Decision 6 (the tri-state classifier and its accept set) and Decision 7 (narrow, do not multi-plan).`, and its bare `(R1)` precondition became `(spec-035 Decision 6 R1)`. `grep -c 'spec-035 Decision'` on that block returns **2** where it returned 0, so all five carry-forward anchors now satisfy the spec's own #"Each body cites this spec's" claim, which was false for this one seam. Comment text only: `ast.dump` over the module is byte-identical to `HEAD` and 0 docstrings changed.

- **D4 — nine out-of-scope raw-line-number spec citations, naming *other* specs.** *Sources:* build plan `#### Partition correction` ("seven"); `bld-035-slice-2-…md` Worker 2 pass 1 ("six"), Worker 3 pass 2 ("seven"), Worker 2 pass 3 ("eight"), Worker 3 pass 3 and Worker 1 final verification item 4 ("nine"); `bld-035-slice-3-…md` item 3; integration D4. *Licensing spec line:* none — same `AGENTS.md` 27 defect class as the five this cycle fixed, but owned by different cards. *Description:* re-derived at this gate with an instrument that survives **both** a wrap and a `#` comment-continuation marker between the token and the number — per-file `re.sub(r"\s+", " ", text)` flatten across newlines, then match — over **571** `.py` files. **Recorded as an occurrence list, never a total**, because three successive totals on record (zero, six/seven, eight) were each produced by an instrument that could not see one wrap shape: **HOMED 2026-09-01 on `TODO-ALPHA-056-0.0.17` scope order 57's sibling at order 60**, the card's #"Thirteen prose citations into shipped specs" item, which already carried 13 of this class and whose population this cycle reduced. That item's amendment records: the 4 spec-035-owned sites it named are discharged, the live subset is the 9 in the table above, and its own `\blines? [0-9]+` instrument was blind to this cycle's fifth fix (`#"spec-035 edge case 316"`, a raw numeral spelled without the word `line`) - so a census of the class must scan `edge case NNN` as well. It also records the sequencing consequence: `optimizer/walker.py` was the only one of the 13 in package source and is now clean, so that item no longer waits on a `TODO-ALPHA-053-0.0.15` WP batch and all 9 can land in one pass.

  | Site | Citation as flattened | Owning spec |
  |---|---|---|
  | `tests/mutations/test_sets.py:1034` | `spec-036 Decision 6 line 334` | spec-036 |
  | `tests/mutations/test_sets.py:1039` | `spec-036 Edge cases line 509` | spec-036 |
  | `tests/mutations/test_sets.py:1073` | `spec-036 Decision 6 line 334` | spec-036 |
  | `tests/mutations/test_sets.py:1073` | `Edge cases line 509` | spec-036 |
  | `tests/optimizer/test_extension.py:1718` | `Decision 7 line 346` | spec-033 |
  | `tests/optimizer/test_extension.py:1754` | `Decision 7 line 346` | spec-033 |
  | `tests/optimizer/test_extension.py:1817` | `Decision 7 line 347` | spec-033 |
  | `tests/optimizer/test_extension.py:2248` | `spec line 350` (names **no** spec, and wraps) | spec-033, by the file's header comment |
  | `examples/fakeshop/config/settings.py:74` | `Decision 13 / spec line # 969` (wraps, with a `#` between `line` and the number) | spec-039 |

  Note `tests/optimizer/test_extension.py` **is** in this cycle's writable cohort — these four are out of scope by *spec ownership*, not by file ownership, and Slice 2 deliberately left them. Two instrument lessons belong with the entry: a `line`-without-`s?` pattern is blind to the plural (`cookbook lines 124-130`), and a comment-continuation `#` between the token and the number defeats any `\s+`-only pattern. Print the scanned-file count so a zero is distinguishable from an unrun sweep.

- **D5 — bare self-referencing `(line NNN)` comments, same rot class against a different document. Count corrected.** *Sources:* `bld-035-slice-2-…md` Worker 3 pass 2 (`tests/types/test_resolvers.py`, nine sites), Slice 2 final verification (adds `tests/test_exceptions.py`); `bld-035-slice-3-…md` item 4; integration D5. *Licensing spec line:* none; pre-dates this cycle and nothing this cycle did falsified them. *Description:* comments citing a source file's own line numbers, which `AGENTS.md` 27 wants as `path::Symbol`. Integration D5 names `tests/test_exceptions.py` without a count; measured here — `grep -rnoE '\(lines? [0-9]+' --include='*.py'` returns **9** in `tests/types/test_resolvers.py` (`:1797, :1802, :1808, :1817, :1828, :1908, :1915, :1920, :1931`) and **3** in `tests/test_exceptions.py` (`:459, :464, :481`), twelve in total. The non-spec `cookbook line(s)` shape adds `tests/orders/test_sets.py:169` and `tests/orders/test_factories.py:250`. **HOMED 2026-09-01 as a new `TODO-ALPHA-056-0.0.17` scope item (order 80).** It had no owner: that card's order-60 item explicitly routes this population to "a live-code batch, not a documentation pass" and no batch names it. The new item carries the 12 sites plus the 2 `cookbook line(s)` sites, the routing rule (fold into whichever `TODO-ALPHA-053-0.0.15` WP batch opens the file; only the residue no batch opens belongs to 056), and **D12 as the precedent for the fix shape** - replace the line number with a `path::Symbol #"substring"` pair and prove the anchor resolves exactly once, never a mechanical `path:NN` rewrite, since at least three of these targets have moved.

- **D6 — the spec's `## Implementation plan` delta-table preamble carries chronology, judged and deliberately left.** *Sources:* `bld-035-slice-3-…md` item 5; integration D6. *Licensing spec line:* `docs/SPECS/spec-035-…md:260`, re-confirmed present verbatim at this gate: "Line deltas were planning estimates; G1 and G2 have since shipped (Slice 1's are the realized `d1dea2fd` deltas)." *Description:* chronology by the letter of `BUILD.md` `## Spec rationale extraction`, but not false, and it does real work — it tells a reader the table's last column mixes an estimate with a realized figure. Flagged so a future custodian judges it rather than inherits it; leaving it reads as decided, not missed.

- **D7 — the rationale companion's `## Post-ship divergences (spec vs. HEAD)` mixes two list forms.** *Sources:* `bld-035-slice-3-…md` item 6; integration D7. *Licensing spec line:* none; a style decision. *Description:* re-confirmed at this gate — items **1-7** are numbered list entries, **8** and **9** are `### Divergence 8` / `### Divergence 9` subheadings, because the two new entries carry rejected alternatives and needed the structure. The section preamble says so, so it is navigable; a tenth entry should either follow the subheading form or normalise all of them.

- **D8 — `#"defaults to enabled"` is the least distinctive of the five anchors.** *Sources:* `bld-035-slice-2-…md` Worker 3 passes 2 and 3, agreed at Slice 2 final verification; integration D8 (**absent from Slice 3's list** — recovered at the integration pass). *Licensing spec line:* none; not a defect. *Description:* four common words with no `G2` / `info` token, so it is the anchor most exposed if the spec ever grows a second sentence using that phrasing. Re-measured here: it resolves **exactly once**, which is all `AGENTS.md` 27 requires, so there is nothing to fix. A future pass touching `tests/optimizer/test_walker.py::test_enable_only_defaults_enabled_without_info`'s docstring should prefer something like `` #"info.operation` defaults to enabled" ``.

- **D9 — CLOSED, not deferred.** *Source:* integration `### Notes for Worker 1 (spec reconciliation)`, closed by that artifact's `## Consolidation (Worker 1)` pass. *Description:* the companion's Decision 4 rejected alternative cited `` [`_project_scalar_only_window`][walker] `` — the alias site — after Slice 1 moved that text out of the spec and out of Slice 3's sweep. Re-verified closed at this gate rather than accepted: `docs/SPECS/appx/spec-035-…-rationale.md:109` now reads `` [`_project_scalar_only_window`][nested-planner] ``, and by ref-id the spec carries **6** `_project_scalar_only_window` reference citations, **all** `[nested-planner]`, **0** `[walker]`; the companion carries **2**, both `[nested-planner]`. Recorded here only so a reader of the integration inventory does not carry it forward as open.

- **D10 — `path::Symbol` under-qualification is a repo-wide convention register, not `035` drift. Figures corrected.** *Source:* integration `## Consolidation` `### Notes for Worker 1`. *Licensing spec line:* none; a standing-convention question for the maintainer. *Description:* both `035` documents cite methods without their owning class. Owners re-derived by `ast` rather than by grep: `_optimize` and `_build_cache_key` are methods of `DjangoOptimizerExtension` in `optimizer/extension.py`; `forward_resolver` is a closure nested inside `types/resolvers.py::_make_relation_resolver`. `AGENTS.md` 27's `path::QualifiedName` would want the owning scope. **The integration's "17 sites in the spec, 5 in the companion" does not reproduce** under a per-shape re-derivation — measured, spec: `extension.py::_optimize` **4**, `extension.py::_build_cache_key` **4**, `types/resolvers.py::forward_resolver` **1** (nine in the `::` grammar), plus `registry.model_for_type` **5** and `registry.definition_for_graphql_name` **1** (six prose spans) = **15**; companion: `extension.py::_optimize` **3**, plus `registry.model_for_type` **2** and `registry.definition_for_graphql_name` **1** = **6**. Note the spec *also* carries the fully-qualified `DjangoOptimizerExtension._optimize` **5** times, so it is internally inconsistent in spelling — which is the strongest argument that this is a convention call rather than a per-document fix. The form is consistent across every `035` document and pre-dates this cycle. **HOMED 2026-09-01 as a new `TODO-ALPHA-056-0.0.17` scope item (order 81), and this entry's own figures are INCOMPLETE by one grammar.** Re-derived at that homing by `ast` classification of every package `def`: the 15 and 6 above **reproduce exactly** and are the sum of two grammars - the inline ``path.py::method`` form (spec 9, companion 3) plus the instance-qualified prose spans (spec 6, companion 3) - and the 5 is the raw count of the qualified `DjangoOptimizerExtension._optimize`, 4 of them carrying a ``path.py::`` prefix. What this entry missed is a **third grammar**: the markdown reference-link form ``[`method`][label]``, which carries the path in the link definition and the class nowhere, at **6** in the spec and **1** in the companion (all `_optimize`). Totals are therefore **21** and **7**. Two sub-populations need rulings of their own because a class name does not fix either: `types/resolvers.py::forward_resolver` is a nested closure inside `_make_relation_resolver`, and the `registry.*` spans are qualified by an object rather than unqualified.

- **D11 — derived counts drifted repeatedly in this cycle; re-derive every one you inherit, including your own.** *Source:* integration `## Consolidation` `### Notes for Worker 1`. *Licensing spec line:* none; a process lesson for the next cycle. *Description:* the integration pass wrote "the spec uses `[nested-planner]` at seven citations"; the consolidation measured **six** (seven was the pre-cycle `[walker]` population, one of which left the spec with the moved text). I re-derived **six** independently at this gate. This gate's own re-derivation adds a **fourth** instance of the same shape — D10's "17 / 5" measures **15 / 6** — after the six-vs-nine deferred-inventory drift and the zero/six-seven/eight/nine population drift. The pattern is stable enough to state as a rule: **a count in an artifact is a claim; re-measure it, quote the command, and prefer an occurrence list whose entries the next reader can re-derive.**

- **D12 — NEW, found at this gate: a `#"substring"` anchor in `tests/types/test_resolvers.py` that does not resolve.** *Source:* this artifact, `### The five shipped-.py spec anchors, re-derived`. *Licensing spec line:* none; pre-existing at `HEAD`. *Description:* `tests/types/test_resolvers.py:892` cites `django_strawberry_framework/types/resolvers.py::_build_fk_id_stub #"instance = root if hasattr(root, "_state") else None"`. That substring occurs **0** times in the cited module; the live line at `types/resolvers.py:149` reads `instance = root if getattr(root, "_state", None) is not None else None`, and `hasattr(root` appears nowhere in the file. Its sibling anchor at `:932` (`#"if related_id is None"`) resolves once, so this is one broken anchor rather than a broken convention. **Pre-existing at `HEAD`, proved read-only:** `django_strawberry_framework/types/resolvers.py` is unmodified in this tree and its `HEAD` content already carries the `getattr` form; the citing comment is byte-identical to `HEAD` (this cycle's only change to that file is at `:1035`). `git log -S'hasattr(root, "_state")' -- django_strawberry_framework/types/resolvers.py` names `ddd5dbb9` and `4b7d7703` as the commits that introduced and removed the cited form. Not this cycle's, not fixed here (this pass writes no `.py`), and **escalated to the maintainer** — it is the same rot class as D4 and D5 but strictly worse, because a `#"substring"` anchor is the form `AGENTS.md` 27 prescribes as the *fix*, and a non-resolving one reads as compliant. **CLOSED 2026-09-01, in this cycle.** Retargeted to the live line: the citation now reads `#"instance = root if getattr(root, "_state", None) is not None else None"` and the prose branch description above it was corrected from `hasattr(root, "_state") else None` to `getattr(root, "_state", None) is not None`. The substring resolves **exactly once** in `django_strawberry_framework/types/resolvers.py`. Comment text only, and proved against the pre-edit file rather than against `HEAD` (this cycle had already changed a docstring at `:1035`, so a `HEAD` comparison would have mis-attributed that change to this fix): reversing the replacement in memory and re-parsing gives an identical `ast.dump`. Homed for the class, not just the site: recorded on `TODO-ALPHA-056-0.0.17` scope order 57, whose dead-`#"substring"`-pinpoint seed list drops from 10 to 9 and keeps this site as the resolver's sharpest positive control - it is the only one of the ten whose rot came from a rename in package source rather than a reflow.

### DRY check across the cycle

No new duplication. This pass writes two `.md` files and no code; the cycle as a whole added zero executable lines, so there is no helper, literal, or ORM shape to consolidate. The integration pass already existence-challenged the one candidate it found (`DST_OPTIMIZER_*` literals — live, and `optimizer/_context.py` is already their single home, so no consolidation). The one DRY question the cycle actually carried — whether the two package test-tree anchors are deletable duplicates of the spec's deferred test plan — is answered in the negative for a measured reason and is catalogued as **D2** rather than left implicit.

---

## Final verification (Worker 1)

- **Gate commands:** all ten run in `BUILD.md` order, each result recorded above. Nine pass. The one failure (`git diff --check`) is four added lines of trailing whitespace in `docs/feedback.md`, a file in no cohort of this cycle, whose `HEAD` content is empty — a concurrent session's uncommitted work, recorded and escalated per the pre-existing/concurrent rule, and not blocking.
- **No `--cov*` flag** was passed to anything in this pass; `--no-cov` was used exactly once, on the full sweep, because `pytest.ini`'s `addopts` auto-applies `--cov`. No line-coverage figure was inspected or asserted.
- **Floor verification:** `No floor-verification scope declared.` No floor venv was built; the floor is cited from `BUILD.md` `## Floor verification` (Django 5.2.16 / Python 3.10 / strawberry-graphql 0.316.0) and the shared `.venv`'s versions were read rather than recalled.
- **Spec reconciliation:** none owed. The gate exposed no spec defect; the header claims routed forward by Slices 1 and 2 are closed on disk, and the stale-symbol class is closed in both halves of the spec/companion pair (measured, not read).
- **Checklist audit:** every prior artifact's checklist was audited at its own final verification and all are `final-accepted`; this artifact's own `### Dispatched findings checklist` is ticked box by box with the evidence cited in-line, and no box is left `- [ ]`.
- **Final status:** `final-accepted`.

## Deferred-item enactment pass (Worker 0, 2026-09-01, maintainer-authorized)

Scope granted: spec files and `.py` files, plus board-DB edits. No close-out agentflow edits.

- **D3 and D12 CLOSED on disk**, both comment text only. `django_strawberry_framework/optimizer/selections.py`
  is `ast.dump`-identical to `HEAD` with 0 changed docstrings; `tests/types/test_resolvers.py` is
  `ast.dump`-identical to its own pre-edit state (compared that way deliberately - a `HEAD` comparison
  would have mis-attributed this cycle's earlier `:1035` docstring fix to this one). Each entry above
  carries its own closure record.
- **D4, D5 and D10 HOMED on `TODO-ALPHA-056-0.0.17`** by ORM edit: two existing scope items amended
  (order 57, the dead-`#"substring"` seed list, 10 -> 9; order 60, the raw-line-number citation item,
  13 -> 9 with its instrument's `edge case NNN` blind spot and the retired package-source sequencing
  dependency recorded) and two new scope items appended (order 80 for D5, which had no owner at all
  because order 60 routes it to "a live-code batch" that names it nowhere; order 81 for D10). Card 056
  went 80 -> 82 scope items; no other card was touched. **`KANBAN.md` / `KANBAN.html` were deliberately
  NOT regenerated** - both carry a concurrent session's uncommitted edits (`KANBAN.md` +4/-3,
  `KANBAN.html` +1/-1 unstaged at this pass), so a regenerate would overwrite that session's in-flight
  board work in files it owns. The DB is the source of truth; the render is owed to whoever wraps the
  board next. (An earlier draft of this bullet called those changes *staged*, on an empty `git diff`
  that was empty only because the command ran from `examples/fakeshop/` where the pathspec matched
  nothing - re-measured from the repository root, the index is clean and the changes are unstaged.
  A pathspec that matches no file reports exactly like a clean file.)
- **D1 remains blocked and D2 remains the follow-up card's decision.** `examples/fakeshop/test_query/test_library_api.py`
  is still baseline-dirty. D10's own figures were found incomplete at this pass and are corrected in
  its entry above.
- **Four citations into this cycle's own artifacts were broken by this cycle's fixes**, found by a
  wrap-aware sweep over the two files this pass edited and all four repaired: `bld-035-slice-2`'s
  `#"contract (R1). Pseudocode:"` (broken by D3's close, retargeted and re-quoted on a single comment
  line, since the prose word `Design` preceding the new phrase sits on the line above and a pinpoint
  spanning that wrap resolves zero times), `bld-035-slice-2`'s `#"spec-035 edge case 316"` checklist
  row and the build plan's four-row pre-fix table (all relabelled as history and taken out of the
  `#"..."` grammar so no sweep reads them as live claims). **The generalizable defect: an artifact that
  pinpoints the exact phrase a catalogued fix will rewrite defeats its own anchor.** Cite the stable
  neighbourhood, or mark the quote pre-fix. All pinpoints into both edited files now resolve exactly
  once.
- **Gates:** `ruff check .` and `ruff format --check` clean; `scripts/check_trailing_commas.py --check`
  clean; `scripts/check_citations.py` -> `OK: 917 citations resolve (770 in 433 .py files, 147 in
  KANBAN.md)`; `pytest tests/types/` -> 533 passed, 2 skipped.
- **One test failure, attributed to a concurrent session and NOT fixed or reverted:**
  `tests/optimizer/test_walker.py::test_divergent_key_windows_shared_payload_uses_none_key` asserts
  `planned == [(None, (0, 2, False), None)]` and receives
  `ConnectionWindowBounds(offset=0, limit=2, reverse=False)` in place of the plain tuple - an in-flight
  window-object refactor. Attribution is decisive rather than inferred: five optimizer modules
  (`walker.py`, `nested_planner.py`, `join_taxonomy.py`, `field_meta.py`, `extension.py`) are
  AST-changed against `HEAD` in this tree and none is this cycle's, while this pass's only optimizer
  edit, `selections.py`, is AST-identical to `HEAD` and therefore behaviour-neutral by construction.
  Escalated, per `AGENTS.md` 34.

### Summary

The gate is green on everything this cycle owns. The full sweep passes at **7069 passed, 42 skipped** with no `--cov*` flag; `manage.py check` and `makemigrations --check --dry-run` are clean; `ruff format --check` and `ruff check` are clean read-only; `check_spec_glossary.py` returns `OK: 23 terms` on the exact invocation the spec's Definition-of-done item 1 now carries; `check_trailing_commas.py --check` is clean over both spec files and all four cohort `.py` files. The five shipped-`.py` `#"substring"` spec anchors, re-derived from the cohort source rather than copied, each resolve exactly once — so the cycle's one cross-slice collision hazard did not fire. The wrap-aware staged-anchor sweep over 921 files (571 of them `.py`) returns exactly one shipped-source survivor, and it is the expected one.

Two things are recorded rather than fixed, and neither is this cycle's. `git diff --check` fails on four added lines in `docs/feedback.md`, a concurrent session's work in a file that is **empty at `HEAD`** and appears in no writable list here. And `tests/types/test_resolvers.py:892` carries a `#"substring"` anchor into `types/resolvers.py` that no longer resolves, byte-identical to `HEAD` in a module that is clean at `HEAD`. Both are escalated to the maintainer, the only party who can run a clean tree; recording plus escalating discharges the obligation, and neither blocks the gate.

The deferred-work catalog is **D1-D8 and D10-D12 open, D9 closed**. It was re-derived rather than inherited, which was the right call twice: D5's `tests/test_exceptions.py` leg had no count and has three sites, and D10's "17 spec / 5 companion" measures 15 and 6. That is the fourth derived-count drift in this cycle, and the lesson is now stated as a catalog item of its own.

### Spec changes made (Worker 1 only)

**No spec or rationale edit this pass**, and none is owed. Slice 3 and the integration consolidation closed both files; this pass's writable list excludes them; and the control run recorded under `### Spec status-line re-verification` measures the pair clean rather than assuming it. No `.py` file was written, no `scripts/build_*.py` generator was run, no rendered doc was regenerated, no branch was created or switched, and nothing was committed.

**Deferral reasons.** Eleven items are deferred (D1-D8, D10-D12), each enumerated above with its source artifact section, the line that licenses it where one exists, and its target. Ten target a future card, a future spec, or the maintainer; D6 and D7 target the next spec custodian as judgement calls already made. D9 is not a deferral — it was raised and closed inside this cycle, and is listed only so the integration inventory's numbering is not misread.

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
