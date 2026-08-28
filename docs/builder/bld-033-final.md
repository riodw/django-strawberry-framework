# Build: Final test-run gate (`spec-033` residual reconciliation cycle)

Spec reference: `docs/SPECS/spec-033-connection_optimizer-0_0_9.md` (whole file) + `docs/SPECS/appx/spec-033-connection_optimizer-0_0_9-rationale.md` (whole file)
Status: final-accepted

**Shape.** Worker-1-owned pass ([`docs/builder/BUILD.md`][build-md] `## Final test-run gate`, [`docs/builder/worker-1.md`][worker-1] `## Final test-run gate`), with no Worker 2 build pass and no Worker 3 review pass, so it carries one combined Plan + Final-verification block. The `## Build report (Worker 2)` and `## Review (Worker 3)` sections of [`ARTIFACT.md`][artifact-md] are deliberately absent, not omitted. Raw `path:NN` references appear only in this file, per [`AGENTS.md`][agents] #"Source refs in docs and code comments" (per-cycle scratchpad carve-out).

**Writable surface for this pass:** this file and `docs/builder/worker-memory/worker-1.md`. Nothing else was written. Both spec files are read-only here — the integration pass was the last opportunity to edit them and it closed `final-accepted`.

**Every number in this artifact was measured at the moment it was written**, with the instrument this cycle converged on: join wrapped comments (`re.sub(r"\n\s*#\s?", " ", src)`) **first**, then normalize whitespace, then fold hyphenation where the target admits it, then count **occurrences** rather than matching lines.

---

## Plan (Worker 1)

### Spec status-line re-verification

Performed, per [`worker-1.md`][worker-1] `## Spec status-line re-verification (every Worker 1 spawn)`. Both files' header blocks read against the state this gate measured:

- `docs/SPECS/spec-033-connection_optimizer-0_0_9.md` lines 1-9 — title, the shipped-record framing, `Status: **SHIPPED (0.0.9) …**`, `Owner:`, `Predecessors:`, and the rationale-companion pointer. Nothing in them is falsified by this pass, which changes no byte of source, spec or companion. The `Status:` line's "cross-slice integration pass + final test-run gate green" clause describes the **original `0.0.9` build's** gate, which is what a shipped-spec status line records; it is not a claim about this residual cycle.
- `docs/SPECS/appx/spec-033-connection_optimizer-0_0_9-rationale.md` lines 1-7 — companion framing, the read-this-when guidance, and the append protocol. Current.
- **Byte sizes confirm neither file moved since the integration pass closed:** spec `160,623`, companion `99,844` — exactly the figures `bld-033-integration.md` `### Spec changes made (Worker 1 only)` recorded. **No spec edit is made or needed by this pass.**

### DRY analysis

Not applicable in the helper sense: this pass writes no code, no test, and no shared shape. The one instrument it authored — the docstring-stripped AST digest below — is written fresh rather than imported from a cohort artifact **on purpose**, because a sixth independent implementation agreeing with five prior ones is evidence, where re-running a cohort's own script would be a tautology.

### Gate checklist

- [x] `uv run pytest --no-cov` — full sweep, all three test trees
- [x] `uv run python examples/fakeshop/manage.py check`
- [x] `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run`
- [x] `uv run ruff format --check .`
- [x] `uv run ruff check .`
- [x] `git diff --check`
- [x] Floor verification: the plan's `none` scope verified **against the actual diff**, not restated
- [x] Hot-path declaration: each cohort's demonstrated zero-delta record confirmed to exist
- [x] `### Deferred work catalog` written, inheriting the integration pass's fifteen items from disk

### Implementation discretion items

None. A gate has no discretion; every command is fixed by [`BUILD.md`][build-md] and every result below is the one the command actually printed.

---

## Final verification (Worker 1)

### 1. Full sweep — `uv run pytest --no-cov`

**PASS**, exit `0`.

```
====================== 6900 passed, 42 skipped in 58.22s =======================
```

No `--cov*` flag was used here or anywhere in this pass, per [`BUILD.md`][build-md] `## Coverage is the maintainer's gate, not a worker's tool`. No line-coverage figure was inspected or asserted.

**The sweep's decomposition was measured, not assumed**, because a full-sweep total cannot be compared directly against the cohorts' focused figures:

| scope | result |
|---|---|
| `uv run pytest tests/ --no-cov` | **5967 passed, 40 skipped** |
| `uv run pytest examples/ --no-cov` | **933 passed, 2 skipped** |
| sum | **6900 passed, 42 skipped** |
| full sweep as run | **6900 passed, 42 skipped** |

`5967 + 933 = 6900` and `40 + 2 = 42`: the sweep decomposes exactly into the package tree and the example project's two trees, with no third population and no residue.

**Divergence from the cohorts' recorded figures: none.** All three recorded scopes were re-run and each reproduces digit for digit, so there is no delta to attribute:

| recorded scope | cohort figure | this gate | exit |
|---|---|---|---|
| `tests/ --no-cov` | 5967 passed, 40 skipped | **5967 passed, 40 skipped** | 0 |
| `tests/optimizer/ tests/test_connection.py tests/test_relay_connection.py --no-cov` | 1005 passed | **1005 passed** | 0 |
| `examples/fakeshop/test_query/test_library_api.py tests/test_keyset_connection.py --no-cov` | 224 passed | **224 passed** | 0 |

This is worth stating positively rather than by silence: the concurrent session's `workstream` sweep landed inside eleven of this cycle's thirteen `.py` files **after** every cohort measured these numbers, and all three still reproduce — which is the mechanical form of the claim that the sweep changed no executable byte.

The 42 skips were enumerated with `-rs` rather than assumed, and every one is environment-gated by the default invocation: the **Postgres tier** (`requires the Postgres tier (FAKESHOP_PG_DSN)`, in `tests/test_lateral_pg_parity.py` and `tests/test_predicate_pg_explain.py`), the **sharded layout** (`requires FAKESHOP_SHARDED=1`, in `examples/fakeshop/test_query/test_multi_db.py`, `examples/fakeshop/apps/library/tests/test_generic_connection_sharded.py` and `tests/test_permissions.py`), and **psycopg2 absent** (`could not import 'django.contrib.postgres.fields'`, in `tests/types/test_converters.py`). None is a suppressed failure and none is in this cycle's thirteen files.

### 2. Django consistency checks

Both **PASS**, exit `0`.

- `uv run python examples/fakeshop/manage.py check` -> `System check identified no issues (0 silenced).`
- `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` -> `No changes detected`

Neither command writes `examples/fakeshop/db.sqlite3`; `makemigrations --check --dry-run` is read-only by construction, so the concurrently-written DB was neither reset nor touched. Neither result depends on that DB's row state — `check` reads the app registry and `makemigrations --check` compares model state against migration files, so both readings are stable despite the concurrent writer.

### 3. Lint / format / diff gate — read-only, never `--fix`

All three **PASS**. Exit codes captured directly rather than through a pipeline, because a piped `$?` reports `tail`'s status and would have read `0` for a failing tool:

| command | result | exit |
|---|---|---|
| `uv run ruff format --check .` | `434 files already formatted` | **0** |
| `uv run ruff check .` | `All checks passed!` | **0** |
| `git diff --check` | no output | **0** |
| `git diff HEAD --check` (widened) | no output | **0** |

`git diff --check` compares the unstaged working tree against the index; with nothing staged in this tree that is the same population as `git diff HEAD --check`, but both were run so the reading does not depend on that being true. Whitespace errors and conflict markers: **zero, tree-wide**.

`ruff format --check` emits a standing configuration warning (`COM812` may conflict with the formatter). It is a pre-existing repository configuration property, not a finding of this cycle, it is deliberate — `AGENTS.md` explains that `scripts/check_trailing_commas.py` and not `ruff` owns single-line explosion — and it does not affect the exit code.

**Supplementary gates, not required by `## Final test-run gate` but cheap and run because this cycle's whole subject is citation and vocabulary rot:**

- `uv run python scripts/check_citations.py --check` -> `OK: 828 citations resolve (738 in 431 .py files, 90 in KANBAN.md).`, exit `0`. Identical to the integration pass's and R3's readings — the citation surface has not moved since.
- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-033-connection_optimizer-0_0_9.md` -> `OK: 38 terms - all have glossary entries and at least one spec link.`, exit `0`. Same 38 as after Slice 0, Slice 2 and the integration pass: no term added or lost across the whole cycle.

### 4. Floor verification — scope `none`, verified against the diff

The build plan declares floor-verification scope **`none` cycle-wide**, on the ground that every edit was comment-only except two test repairs, so no Django / Strawberry / channels integration seam moved. [`BUILD.md`][build-md] makes this gate the backstop that confirms a planned floor verification happened, and [`worker-1.md`][worker-1] makes **a `none` declaration the diff falsifies grounds for `revision-needed`**. So the declaration was tested rather than restated.

**The instrument.** `ast.parse` -> strip every module / class / function docstring (substituting `Pass()` where a body would empty) -> `ast.dump(include_attributes=False)` -> `sha256[:12]`, on Python `3.14.2`. Comments never enter an AST at all, so this digest is blind to exactly the two things the ground claims are the only changes — comments and docstrings — and sensitive to everything else. Written for this pass without reference to any cohort's script; it is the **sixth** independent implementation in this cycle.

**Must-see control.** Inserting `_final_gate_control_probe = 1` above `connection.py`'s first import moves its digest `ecc47449f5ec` -> `49a0364cdecc`. A reported identity below is therefore a measurement and not a null the instrument would report either way.

**Both columns were measured twice — against `db7ecb1a` at gate start and against `24125be6` after the concurrent session committed mid-pass (section 6) — and every digit below, the control included, is identical across the two `HEAD` vintages.**

| file | worktree | `HEAD` | executable-identical |
|---|---|---|---|
| `django_strawberry_framework/connection.py` | `ecc47449f5ec` | `ecc47449f5ec` | yes |
| `django_strawberry_framework/optimizer/plans.py` | `8fb1b399480f` | `8fb1b399480f` | yes |
| `django_strawberry_framework/optimizer/walker.py` | `615fe2fe2be2` | `615fe2fe2be2` | yes |
| `django_strawberry_framework/optimizer/nested_fetch.py` | `302fbecdcc8d` | `302fbecdcc8d` | yes |
| `django_strawberry_framework/optimizer/nested_planner.py` | `3e8f913d90ae` | `3e8f913d90ae` | yes |
| `django_strawberry_framework/optimizer/lateral_fetch.py` | `9abf1bbf2dc2` | `9abf1bbf2dc2` | yes |
| `tests/test_connection.py` | `e10df5d5f0a3` | `e10df5d5f0a3` | yes |
| `tests/test_relay_connection.py` | `e357f45d6f2a` | `e357f45d6f2a` | yes |
| `tests/optimizer/test_plans.py` | `809ebc71d3d8` | `809ebc71d3d8` | yes |
| `tests/optimizer/test_walker.py` | `1311b82c4ceb` | `5e9799a71eee` | **NO** |
| `tests/optimizer/test_extension.py` | `bd92ca53429b` | `349aa5422d06` | **NO** |
| `tests/optimizer/test_nested_fetch.py` | `b459bd8740f2` | `b459bd8740f2` | yes |
| `examples/fakeshop/test_query/test_library_api.py` | `b5918390baa8` | `b5918390baa8` | yes |
| `django_strawberry_framework/optimizer/selections.py` *(concurrent)* | `241975dddd94` | `241975dddd94` | yes |
| `tests/optimizer/test_selections.py` *(concurrent)* | `acc7026f2b52` | `acc7026f2b52` | yes |

**This table is wider than the integration pass's eleven rows in two deliberate ways**, and both extensions matter to the floor question specifically. It covers all **thirteen** declared `.py` files — adding `tests/test_connection.py` and `tests/optimizer/test_plans.py`, which the integration pass's table did not carry — and it measures the **two concurrent-session `.py` files** as well, so the claim "the concurrent sweep is comment-only" is a reading rather than an inference from its authorship. All thirteen worktree digests the integration pass recorded reproduce; the two new rows are identical to `HEAD`; the two concurrent files are identical to `HEAD`.

**The verdict against the diff.** All six production modules under `django_strawberry_framework/` are **executable-identical to `HEAD`**. Exactly two files differ, both under `tests/optimizer/`, and both are R2's failability-proved test repairs. Their diffs were read, not inferred from the digest:

- `tests/optimizer/test_extension.py` — isolates the module-level `_doc_key_cache` LRU with `monkeypatch.setattr` and adds a fourth `_build_cache_key` call after clearing it, so the per-execution memo tier is pinned on its own instead of through the cross-request document cache standing in for it. Two docstring citations also gain a `spec-030` prefix. It monkeypatches package state; it touches no Django, Strawberry or channels API.
- `tests/optimizer/test_walker.py` — restores the shared-child M2M partition test, parametrized over both relation directions, asserting each of two parents receives the shared child in its **own** `first: 1` page. It exercises Django's prefetch and window compilation, but it **adds** an assertion against unchanged shipped code rather than moving a seam. Three docstring citations are re-sited from `Decision 11` to `Decision 4`, and two `workstream B` spellings become `spec-033 Decision 4`.

**The declaration holds.** No production byte moved, so no Django / Strawberry / channels integration seam moved; `none` is the correct scope and the diff does not falsify it.

**Supplementary floor run, beyond the declared scope.** The restored `test_walker.py` case is a *new* assertion executing Django's window and prefetch compilation, and it has never been executed at the floor. A scope of `none` does not require running it, and a failure there would be a pre-existing floor property of shipped code rather than a regression this cycle introduced — but the question is cheap to close by execution, and [`BUILD.md`][build-md] `## Floor verification` is explicit that reading source or reasoning from a changelog is not verification. So it was executed:

- floor venv: `<scratchpad>/dsf-floor`, built **outside the repository**, with an explicit `--python` on every install.
- resolved versions, read with `uv pip list --python <venv>/bin/python` rather than stated from memory: **Django `5.2.16`**, **strawberry-graphql `0.316.0`**, **Python `3.10.19`**, channels `4.3.2`, graphql-core `3.2.12`, pytest `9.1.1`. These are the floor [`BUILD.md`][build-md] `## Floor verification` names.
- `<venv>/bin/python -m pytest tests/optimizer/test_walker.py tests/optimizer/test_extension.py --no-cov` -> **351 passed**, exit `0`.

**The shared `.venv` was not mutated.** Read before and after the floor build with `uv pip list`: `django 6.1`, `strawberry-graphql 0.324.0`, `channels 4.3.2`, `graphql-core 3.2.8`, Python `3.14.2` — unchanged across the pass, and **not** the floor, which is exactly why a `none` scope is a declaration about the diff and not a claim about the environment the sweep ran in.

### 5. Hot-path declaration — confirmed, not re-measured

The plan declares **`none`** for this pass, which touches no runtime code. The dispatch's standing obligation is to confirm each cohort's demonstrated zero-delta record **exists**, rather than re-deriving it. Each was located on disk:

| declared-hot file | record | before / after / delta |
|---|---|---|
| `django_strawberry_framework/connection.py` | `bld-033-review-2` `### Hot-path budget`; `bld-033-review-3` `### Hot-path budget` (pass 2) | `ecc47449f5ec` / `ecc47449f5ec` / **0** |
| `django_strawberry_framework/optimizer/plans.py` | `bld-033-review-2` `### Hot-path budget` | `8fb1b399480f` / `8fb1b399480f` / **0** |
| `django_strawberry_framework/optimizer/walker.py` | `bld-033-review-2` `### Hot-path budget` (passes 1 and 2) | `615fe2fe2be2` / `615fe2fe2be2` / **0** |
| `django_strawberry_framework/optimizer/nested_fetch.py` | `bld-033-review-2` `### Hot-path budget` (pass 2); `bld-033-review-3` `### Hot-path budget` | `302fbecdcc8d` / `302fbecdcc8d` / **0** |
| `django_strawberry_framework/optimizer/nested_planner.py` | `bld-033-review-3` `### Hot-path budget` | `3e8f913d90ae` / `3e8f913d90ae` / **0** |
| `django_strawberry_framework/optimizer/lateral_fetch.py` | `bld-033-review-3` `### Hot-path budget` | `9abf1bbf2dc2` / `9abf1bbf2dc2` / **0** |

Every record carries the four fields [`BUILD.md`][build-md] `## Hot-path budget` requires — metric, command, iteration count, before/after with delta — and each names its mutant digest as the control that makes the zero a measurement. Six for six present; none missing, none asserted in prose without a number. Their six "after" digests are independently reproduced by this gate's own table above, which was not the obligation but costs nothing once the instrument exists.

### 6. Concurrent work — attribution by diff content, never by `git status` membership

**The concurrent session committed mid-pass, and the `HEAD` this gate measures against therefore moved.** Recorded first, because every `HEAD`-relative number below has two vintages:

- **At gate start**, `HEAD` was `db7ecb1a` and the tree carried **25 modified** / **11 untracked** paths, **15** of the modified being `.py`. This cycle declared **13**; the two extras were exactly `optimizer/selections.py` and `tests/optimizer/test_selections.py`, which the dispatch independently names as the concurrent session's. **That arithmetic is a trap and was recorded as one**: it read like a clean partition while the concurrent `workstream` sweep sat inside **eleven of this cycle's own thirteen**.
- **Mid-pass** the concurrent session committed `24125be6` *"docs: retire the workstream vocabulary and home seven deferred audit items"* — 20 files, 86 insertions, 75 deletions, comprising the `workstream` sweep plus `KANBAN.md` / `KANBAN.html` / `README.md` / `ARTIFACT.md` / `BUILD.md` / the three `worker-*.md` role files and `db.sqlite3`. Exactly the set the dispatch attributed to that session, now landed by its own author.
- **At gate close**, `HEAD` is `24125be6` and the tree carries **14 modified** / **12 untracked**, of which **13** modified are `.py` — and those thirteen are now **exactly this cycle's thirteen declared files**, with no extras and no omissions. The dirty-file partition, which was a trap at gate start, is clean at gate close because the concurrent writer took its own work.

**Nothing in that commit is this cycle's**, and this pass neither prompted it, participated in it, nor staged anything into it. `docs/builder/worker-memory/worker-1.md` is `.gitignore`d (`.gitignore:188`, `docs/builder/worker-memory/`), so this pass's memory append could not have been swept into it and was verified intact on disk afterwards.

**The `HEAD` move changed no measurement in this artifact**, and that is a result rather than a convenience: the whole AST table in section 4 was re-run against `24125be6` and **every digit in both columns is unchanged**, including the two deliberate `NO` rows and the control. A vocabulary sweep moving from "uncommitted" to "committed" alters no docstring-stripped AST, which is the mechanical restatement of "it changed no executable byte" — now demonstrated across a commit boundary rather than only across a working-tree diff.

**Nothing below was edited, reverted, tidied, stashed, checked out, restored, or worktree'd by this pass.** `git show HEAD:<path>` into memory was the only reference mechanism used.

Re-measured at gate time with the wrapped-comment-join instrument, so the catalog carries a current vintage rather than an inherited one:

- **The `workstream` sweep: `db7ecb1a` 38 occurrences -> worktree 3**, measured at gate start. Twelve `.py` files carried the token in either vintage; **eleven** were touched by the sweep, and `django_strawberry_framework/utils/connections.py` was unchanged at 1, which is why it is a survivor rather than a target. The three survivors are `optimizer/lateral_fetch.py`, `utils/connections.py`, and `tests/test_relay_connection.py` — precisely the three the integration pass named. The pre-sweep per-file distribution: `connection.py` 7, `test_relay_connection.py` 9, `test_library_api.py` 6, `lateral_fetch.py` 4, `test_walker.py` 3, `plans.py` 2, `test_plans.py` 2, and 1 each in `nested_planner.py`, `selections.py`, `walker.py`, `test_selections.py`, `utils/connections.py`. **Re-measured at gate close against `24125be6`: 3 in both columns** — the sweep is now committed, so it has left the diff entirely, and the three survivors are the concurrent session's own residue in its own commit, not this cycle's.
- **The four mis-sited marker-row citations are all still present**, one per file, verified individually rather than as a total: `connection.py` (9 marker-row passages, 1 citing Decision 4), `optimizer/lateral_fetch.py` (3, 1), `optimizer/plans.py` (2, 1), `tests/optimizer/test_plans.py` (1, 1).
- **`tests/test_relay_connection.py`**: worktree **24** `Decision N` references, **15** bare. Against `db7ecb1a` that was **20** / **16**, reproducing the integration pass's figures exactly; against `24125be6` it is **24** / **16**, because the concurrent commit carried its own four added references. The **worktree-vs-`HEAD` delta is now one bare reference qualified**, which is this cycle's own R2/R3 repair and nothing else — a cleaner statement of the same fact than the pre-commit reading could make, since that one mixed two authors' edits into a single pair of numbers.

**This is not the gate failing.** Every gate command above passed, so there is no red for a maintainer to misattribute. The concurrent work is recorded here because a maintainer reading a green gate over a tree containing another session's uncommitted vocabulary sweep needs to know the sweep is *in* the measurement and changed no executable byte of it — which the fifteen-row AST table proves in both directions.

**Staged-anchor sweep, re-run.** `grep -rn --include='*.py' --include='*.md' 'TODO(spec-033' .` returns **zero hits in shipped source**. The surviving hits are the spec's own description of the anchor convention (`spec-033` line 388), the companion's Revision-2 narrative (line 32), `docs/builder/DONE/build-032-full_relay-0_0_9.md`, and this cycle's own artifacts describing the anchor they discharged. The anchor R3 removed has not come back.

### 7. Declarations

- **Hot-path declaration:** `none` for this pass — it touches no runtime code. Every cohort's demonstrated zero delta confirmed present in section 5.
- **Floor-verification scope:** `none` cycle-wide, **verified against the diff** in section 4 and not restated. One supplementary floor run was performed beyond the scope; its venv, resolved versions and result are recorded there. The shared `.venv` was not mutated and no `uv pip install` targeted it.
- **Ownership partition:** `docs/builder/bld-033-final.md` and `docs/builder/worker-memory/worker-1.md`. Nothing outside it was written. No `.py` file, no spec file, no standing doc, no kanban DB.
- **Failability position:** `None; this pass introduces no boundary.` It ships no executable byte. Its analogue is the must-see control on the AST instrument and the exit-code capture discipline in section 3, both of which fail loudly.
- **Commit position:** nothing committed, branched, stashed, or staged. The gate hands off to the maintainer.

### Deferred work catalog

The next spec author's reading list, per [`BUILD.md`][build-md] `## Final test-run gate`. **The no-deferrals literal does not apply** — this cycle deferred a great deal, deliberately, under a maintainer-set scope fence.

Items 1-15 are inherited **from disk** from `bld-033-integration.md` `### Notes for Worker 1 (spec reconciliation)`, which consolidated every cohort's `What looks solid` / `Notes for Worker 1` / `### Deferred work` section. Items 16-18 are added by this gate: 16 from `bld-033-slice-2` `### Deferred work`, 17 from `bld-033-slice-0` `### Notes for Worker 1 (spec reconciliation)` where it was raised and never resolved, and 18 from this cycle's own process record.

**Group counts: A = 4, B = 1, C = 4, D = 2, E = 5, F = 2. Eighteen items in six groups.** No group is empty.

#### A. Escalations — maintainer-owned, unresolvable by a worker (4)

In all four the shipped code implements the spec's own words, so none is a deviation this cycle could repair. None is licensed by a spec line to be deferred; each is deferred because it is a **contract question**, which [`BUILD.md`][build-md] `### Contract-level findings are escalated as maintainer decisions before dispatch` puts outside a worker's call.

1. **The `connection_to_attr` strictness probe answers "attribute present", not "the window was consumed".** *(`bld-033-review-1b` M1; re-recorded in `bld-033-integration.md` A1.)* `django_strawberry_framework/types/resolvers.py::_check_n1` re-derives from the attribute an answer `django_strawberry_framework/connection.py::_build_relation_connection_resolver` computed one branch earlier and discarded, so three refusal shapes read as "served" and `"raise"` stays silent on a real per-parent query. Demonstrated with a 3-row temp test, not argued. **Licensing spec line:** Decision 8 states the condition as "the fast-path `to_attr` is absent on `root`", so the shipped code is correct against the spec and changing it is a contract change. No data-correctness impact — only the diagnostic is silent. R1b's three resolution paths stand; it recommends threading the resolver's already-computed boolean.
2. **`django_strawberry_framework/optimizer/plans.py::window_partition_for_prefetch` has zero production callers behind six tests.** *(`bld-033-review-1a` DRY-1, the existence challenge; `bld-033-integration.md` A2.)* Production derives the partition from the join descriptor instead, and two of the six pin an `OptimizerError` no production path can emit while `exceptions.py` documents that raise as a live error mode. **Read it with R2's failability work, which is decisive here:** mutating `optimizer/join_taxonomy.py::_partition_expr` (read by the shim *and* by production) and mutating `optimizer/nested_fetch.py::attach_windowed_prefetch`'s `partition_by=` (read only by production) fail the **same two rows** — the restored shared-child test's, both times — and **neither fails any row of the shim's own six-row family**. Three resolution paths in R1a; the maintainer picks.
3. **Ten of `django_strawberry_framework/optimizer/walker.py`'s seventeen back-compat aliases are dead.** *(`bld-033-review-1a` Medium; `bld-033-integration.md` A3.)* Independently re-derived by Worker 3 from an AST pass over all 17. The false half of the comment was repaired by R2 — a comment correction is not an existence question — and the deletion is executable and remains escalated. **Pair it with item 6:** deleting the aliases removes the only non-`connection.py` readers of the two `to_attr` delegates, after which that relocation is mechanical.
4. **The nested-connection strategy seam has no owning spec, and it is the root cause of items 1-3 rather than a fourth item.** *(`bld-033-review-1c`; `bld-033-integration.md` A4.)* No file under `docs/SPECS/` takes it as its subject. This is why three of this card's contracts silently inverted post-ship and why every attribution in this cycle had to be **by commit rather than by card**: `57cbd32a`, `9580e84e`, `51421e54`, `6912ca92`, `991d5120`, `deeb53b4`, `de2601e9`, `841e56d6`, `567cc6d0`. R1c argues for opening a card for the seam and moving the inverted contracts onto its spec, which is what the package's "every shipped surface has an owning spec" posture implies.

#### B. Found by the integration pass, unroutable inside this cycle (1)

5. **A concurrent session's `workstream` sweep left one contract named three ways, four citations mis-sited, and three sites un-swept.** *(`bld-033-integration.md` B5; re-measured by this gate in section 6 and unchanged.)* The marker-row contract is cited 7 times on Decision 5 (correct), 4 times on Decision 4 (which states no marker-row contract), and 3 sites still name a retired `Workstream C`. The four mis-sited: `django_strawberry_framework/connection.py` #"With marker rows planned for the ambiguous shapes", `django_strawberry_framework/optimizer/lateral_fetch.py` #"the ambiguous-shape marker rows", `django_strawberry_framework/optimizer/plans.py` #"Marker rows (spec-033 Decision 4", `tests/optimizer/test_plans.py` #"The marker-row disambiguation". The three `Workstream C` survivors: `optimizer/lateral_fetch.py`, `utils/connections.py`, `tests/test_relay_connection.py`.

   **Two repairs are possible and they are not equivalent.** (a) Re-site the four citations on Decision 5 and retire the three survivors — smallest surface, makes all eleven passages agree. (b) Add a marker-row cross-pointer to Decision 4 — one edit instead of seven, but it changes the contract document to accommodate prose, and Decision 5 already states the plan side as well as the resolve side. **Recommend (a)**, in a follow-on `.py` cohort with its own declared partition. The integration pass added the condition "dispatched only once the concurrent session's work has landed", since a cohort cannot own files a live writer holds ([`AGENTS.md`][agents] rule 34). **That condition is now satisfied: the sweep was committed mid-gate as `24125be6`** (section 6), the `workstream` count is 3 in both the worktree and `HEAD`, and all four mis-sited citations plus all three survivors are present in committed source. The blocker on this item is discharged; the work itself is not.

   **The transferable half:** a vocabulary retirement has no gate, and this cycle now has *two* independent data points that it rots within one pass — Slice 2's Decision 6 heading rename stranded 13 source sites, and this sweep stranded 3 while creating 4 mis-sited citations. A slice that renames a Decision heading owes a tree-wide sweep of the retired heading's **nouns**, run with the wrapped-comment-join instrument. That belongs in [`BUILD.md`][build-md].

#### C. Source changes recorded, not implemented — outside this cycle's fence (4)

**Licensing:** the build plan's `## Scope fence for this cycle (maintainer-set)` restricts this cycle to spec files and the `.py` repairs the standing rules require. None of these four is such a repair; each is an improvement.

6. **Relocate the `to_attr` grammar to `django_strawberry_framework/utils/connections.py`.** *(`bld-033-review-1a` DRY-2; `bld-033-integration.md` C6.)* `connection.py` imports `_extend_only_projection`, `_relation_connection_to_attr` and `_relation_connection_to_attr_for_key` from `optimizer.nested_planner` and uses the latter two at the resolver's per-key probe. Decision 11 created `utils/connections.py` as "a neutral, cycle-safe home" precisely so the plan side and the resolve side share one source, and the `to_attr` grammar is as much a cursor-parity contract as the bounds are. **Note the corrected grounds:** the privacy of the imported names is *not* the argument — a cross-module `_`-private import is an established house convention here, **76 statements across 45 modules**, measured tree-wide — and on that basis `bld-033-review-1c`'s **L6** (`optimizer/extension.py` importing `_active_strategy`) is **closed as not-a-defect and should not be re-flagged**. The argument is placement. No behavior change; pairs with item 3.
7. **One shared `_COERCION_ERRORS` constant under `utils/`.** *(`bld-033-review-1b`, re-measured by `bld-033-integration.md` C7.)* `except (ValueError, TypeError, AttributeError, KeyError, IndexError)` — **16 occurrences across 3 files**: `connection.py` 11, `auth/mutations.py` 4, `utils/sessions.py` 1. R1b reported 15 across 2; its exact-shape regex could not see the third site, written in the **exploded multi-line** trailing-comma layout this repo enforces. `except` accepts a tuple name, so the consolidation is mechanical. **`utils/sessions.py` carries a six-member superset (it adds `ImportError`) and must not be folded in.** No cohort owns `utils/` or `auth/`; needs its own partition.
8. **Name `_optimizer_runtime_prefixes`.** *(`bld-033-review-1a` Low; corrected in description by `bld-033-integration.md` C8.)* The **string literal** occurs twice, in one module (`optimizer/walker.py`, both inside `getattr`); `optimizer/selections.py` carries the name as a keyword argument. R1a's Low heading says "a bare literal in two modules", which its own body does not claim. Still a real cross-seam attribute-name grammar with no named constant, and still cheap; Low on its merits, not on its heading.
9. **`django_strawberry_framework/connection.py::_resolve_from_window`'s keyset legs are separable.** *(`bld-033-review-1b` L3; `bld-033-integration.md` C9.)* 323 lines / 26 branch nodes, more than twice the file's next entry; the branch fan-out is the cross-product of four `FetchMode` shapes, the marker/probe split, and the keyset fork, and separating the keyset legs would roughly halve each half. A repair-cohort suggestion, **explicitly not a defect** — the shape predicates already delegate to `utils/connections.py` rather than being re-spelled.

#### D. Prose-citation exposure with no gate (2)

10. **`tests/test_relay_connection.py` has no safe default for a bare `Decision N`, and the exposure is growing.** *(`bld-033-review-3` `### Notes for Worker 1` item 2; `bld-033-integration.md` D10.)* Re-measured by this gate: worktree **24 references / 15 bare**; against `db7ecb1a` `HEAD` was **20 / 16**, reproducing the integration pass's figures exactly, and against `24125be6` it is **24 / 16** (section 6). The exposure grew from 20 to 24 references through the concurrent commit and is now committed rather than pending, so the file a later cohort must qualify is larger than when R3 first flagged it. Its module docstring cites `spec-032` while its body carries live references belonging to `spec-030`, `spec-032`, `spec-033` and `spec-047`. **Every reference R3's reviewer read is correct**, so there is no live defect — and it is nevertheless **deferred work rather than a non-issue**, on three grounds: the file has no single default a reader can fall back on; the concurrent sweep just increased the density of mixed qualified/bare references in it; and the failure mode is silent, a wrong resolution that *reads* as correct, which R3 found and closed once already in `connection.py`, where the module's declared `Spec:` line points at `spec-030`'s topically-adjacent Decision 6. Remedy: qualify every bare reference in that file with its `spec-0NN` prefix, in a cohort with its own partition. **Not a spec edit.**
11. **The "Decision 6 shape 4" class, generalised — the cycle's most transferable finding.** *(`bld-033-integration.md` D11.)* The instance is closed (R2 repaired it; R3 swept its vocabulary siblings 13 -> 0). The class is: **a prose reference from source into a spec Decision is invisible to every gate this repository has.** `scripts/check_citations.py` resolves `path::Symbol` references and deliberately excludes `docs/`, so it can see neither an ordinal *inside* a Decision's item list, nor a citation by a Decision's heading text, nor a citation to a Decision that exists but does not state the claim.

    **Recommendation, in two parts, because a gate can only reach the first.** (a) A mechanical extension of `check_citations.py` — resolve every `spec-<NNN> Decision <N>` occurring in first-party `.py` against the `### Decision <N>` headings of `docs/SPECS/spec-<NNN>-*.md` — would catch a citation to a **non-existent** Decision. Worth having, and cheap. (b) **It would have caught none of this cycle's four instances**: "shape 4" was an ordinal *inside* an existing Decision, and all four marker-row mis-sitings name a Decision that exists and simply does not state the claim. Only reading catches those, which is why the durable instrument is the spec-side convention the integration pass landed in Decision 6's introduction — a citation naming the arm by content carries its own claim, so target and claim are checkable in one read. **Record both, and do not let (a) create the impression the class is gated.**

#### E. Fenced doc surfaces — evidence recorded, none fixed (5)

**Licensing:** the build plan's `## Scope fence for this cycle (maintainer-set)` — "No `KANBAN.md` / `KANBAN.html` / `docs/GLOSSARY.md` / `docs/TREE.md` / `CHANGELOG.md` / `TODAY.md` / `README.md` edit, no kanban-DB write, no card-wrap or closeout agentflow edit. Doc-surface divergences a cohort finds are **recorded in the deferred-work catalog**, never fixed here." This cycle is spec-and-`.py` only and adds no closeout agentflow edit, so all five stay for a later cycle.

12. **`docs/TREE.md`** — script-rendered by `scripts/build_tree_md.py` from module docstrings **this cycle edited**, and its optimizer entries cannot describe the seven post-ship modules Decision 11 now names. The fix is a docstring-plus-regenerate change, not a doc edit, and the docstring fix and the regenerate must land in the **same** change (a hand-edit of the generated tail is reverted by the next render). *(`bld-033-review-1a` D2, `bld-033-slice-2` `### Deferred work`.)*
13. **`docs/GLOSSARY.md` `## Strictness mode`** — its `0.0.9` paragraph still lists "divergent aliases" among the shapes that fall back per parent, which the idea-#2 inversion (`57cbd32a` / `9580e84e`) retired. DB-generated: edit the fakeshop glossary app's DB and re-render, never hand-edit. **The dispatch's original premise is corrected and this is the only stale entry:** `docs/GLOSSARY.md`'s `## Connection-aware optimizer planning` entry is **not** stale — it already describes marker rows, the conditional count and n+1 probe, `last: 0`, the argument-conflict fallback, the strategy seam and keyset `Meta.cursor_field`, and Slice 2 used it as its voice reference. *(`bld-033-slice-2` `### Deferred work`.)*
14. **`KANBAN.md`** — `DONE-033-0.0.9`'s card body was never read against the corrected spec. Read-only this cycle, used only to adjudicate card ids. *(`bld-033-slice-2` `### Deferred work`.)*
15. **`docs/README.md` — no change needed, recorded so a later reader does not "fix" it.** `bld-033-review-1b` established it is *right* where the spec was wrong about keyset ordering; the spec is now corrected toward it. Any future pass that "aligns" it toward the retired Non-goal would be reintroducing the defect. *(`bld-033-review-1b`, `bld-033-slice-2` `### Deferred work`.)*
16. **`CHANGELOG.md` / `TODAY.md` / `README.md` — untouched and, as of this cycle's reading, accurate.** *(`bld-033-slice-2` `### Deferred work`; added to the catalog by this gate, as the integration pass's group E carried only 12-15.)* The `0.0.14` entry's "Pluggable nested-connection fetch-strategy seam" bullet is the **only** standing-doc record the strategy seam has anywhere, which is a second reading of item 4's root cause: a seam whose sole documentation is one changelog bullet has no owning spec by construction. A later cycle that opens the seam's card should verify this bullet against whatever contract that card states.

#### F. Recorded by this gate (2)

17. **Three absolute developer paths survive in the spec's own prose, raised in Slice 0 and never resolved.** *(`bld-033-slice-0` `### Notes for Worker 1 (spec reconciliation)`; not carried by `bld-033-integration.md`.)* Measured by this gate: `docs/SPECS/spec-033-connection_optimizer-0_0_9.md` lines **59**, **91**, **148** each cite `/Users/riordenweber/projects/strawberry-django-main/strawberry_django/...` — the Slice-1 checklist's `plans.py` sub-bullet, the `## Problem statement` upstream-proof paragraph, and the `## Borrowing posture` paragraph. The rationale companion carries **zero**. The line numbers are unchanged from Slice 0's measurement, so nothing moved them and no pass acted on them. **This is a genuine open question, not an oversight to fix silently:** [`AGENTS.md`][agents] names that checkout as the upstream reference by absolute path, so it may be house convention — but a machine-specific absolute path in a shipped spec is not reproducible for another reader. It needs a decision either way, and it belongs to whichever cycle next opens the spec, because **both spec files were read-only to this gate**.
18. **Workflow recommendation: `BUILD.md`'s dispatch loop keys off a `Status:` line a worker writes before it finishes appending.** *(This cycle's own process record — `build-033-connection_optimizer-0_0_9.md` R2 checklist, "Worker-0 dispatch error", and `docs/builder/ARTIFACT.md` `## Status field ownership`.)* It cost this cycle a real defect: R2's pass-2 re-review was dispatched off `Status: built` while Worker 2 was still writing, so a reviewer graded a **424-line** file that had already reached **897** lines by the time Worker 0 checked (and stands at **1,319** as this gate reads it) and raised a confident `Medium 1` that was **false against the finished artifact** — "pass 2 recorded no build report" — when `## Build report (Worker 2, pass 2)` was already on disk carrying its files-touched, inverse proof, hot-path zero-delta figures, validation run and floor declaration. Worker 0's independent verification and the reviewer's own re-read reached the same correction separately, which is the outcome the verify-before-dispatch rule exists for; **the cost was a full review round, not a wrong merge.** The durable fix is a dispatch rule, not a worker fault: **wait for the agent's own completion signal, not for the file to change.** [`ARTIFACT.md`][artifact-md] `## Status field ownership` defines who sets the line but not when it may be *read*, and that gap is where this defect lives. This gate wrote its entire artifact before setting `Status:` for exactly that reason.

### Checklist audit

Every box in `### Gate checklist` is `- [x]` and each contract landed as a recorded measurement above: the three test-run commands in section 1, the two Django checks in section 2, the three lint/format/diff commands in section 3, the floor-scope verification against the diff in section 4, the six hot-path record confirmations in section 5, and the catalog in `### Deferred work catalog`. No box is ticked without a landed result and none is left silently un-ticked.

The build plan's own checklist carries `- [x]` on all eight prior rows and `- [ ]` on `Final test-run gate -> docs/builder/bld-033-final.md`. **Worker 0 owns that box**; [`worker-1.md`][worker-1] forbids Worker 1 marking build-plan checkboxes, so it is deliberately left unticked here.

### Summary

**Every gate command passes. No failure to attribute, to this cycle or to the concurrent session.**

The full sweep is **6900 passed, 42 skipped**, and it decomposes exactly into `tests/` (5967/40) and `examples/` (933/2). All three of the cohorts' recorded focused figures — 5967/40, 1005, and 224 — reproduce digit for digit, which is worth reading as a positive result rather than an absence: the concurrent `workstream` sweep landed inside eleven of this cycle's thirteen `.py` files *after* those numbers were taken, and they did not move. Django's `check` and `makemigrations --check --dry-run` are clean, `ruff format --check` and `ruff check` are clean across 434 files, and `git diff --check` finds no whitespace error or conflict marker anywhere in the tree.

The plan's `none` floor scope was **tested against the diff rather than restated**, under a sixth independently written docstring-stripped AST instrument carrying a must-see control. All six production modules are executable-identical to `HEAD`; the two concurrent-session `.py` files are executable-identical to `HEAD`; exactly two files differ, both `tests/optimizer/` files, and both are R2's failability-proved test repairs, whose diffs were read rather than inferred. No Django / Strawberry / channels integration seam moved, so `none` is correct. Beyond the declared scope, the two differing files were additionally executed at the floor — Django 5.2.16 / Python 3.10.19 / strawberry-graphql 0.316.0, in a venv outside the repository, with the shared `.venv` read before and after and unmutated — and returned **351 passed**.

**The concurrent session committed its own work mid-gate** as `24125be6`, moving the `HEAD` every measurement here is relative to. Recorded in full in section 6, with two consequences worth carrying: the whole AST table was re-run against the new `HEAD` and **every digit in both columns is unchanged**, so "the sweep changed no executable byte" is now demonstrated across a commit boundary and not merely across a working-tree diff; and the dirty-`.py` partition, a trap at gate start (15 dirty against 13 declared, with a foreign edit inside eleven of the thirteen), is **exactly this cycle's thirteen files** at gate close. This pass committed nothing, staged nothing, and was not party to that commit.

This cycle's headline result stands unchanged and belongs at the top of the next author's reading: **nothing planned in the spec was ever skipped.** R1c's 76-row named-test census found 66 present and pinning, 3 present but no longer pinning, 4 renamed to live pins, 3 absent because the contract itself changed, and **0 absent while the contract still stood**.

The catalog carries **18 items in six groups**, none empty. The four escalations are the substantive half, and item 4 is the one to read first: three of them are symptoms of a seam that has no owning spec, which is also why every post-ship attribution in this cycle had to be by commit hash rather than by card.

### Spec changes made (Worker 1 only)

**None.** Both spec files are read-only to this pass — the integration pass was the last opportunity to edit them and it closed `final-accepted`. Their byte sizes are unchanged at `160,623` and `99,844`, confirming that in fact and not only in intent. Item 17 above is the one spec-surface question this gate found open; it is recorded for a later cycle rather than fixed, because fixing it here would have been an out-of-partition write.

<!-- LINK DEFINITIONS -->

<!-- Root -->

[agents]: ../../AGENTS.md

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

[artifact-md]: ARTIFACT.md
[build-md]: BUILD.md
[worker-1]: worker-1.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
