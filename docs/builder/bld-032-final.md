# Build: Final test-run gate — spec-032 residual reconciliation

Spec reference: `docs/SPECS/spec-032-full_relay-0_0_9.md` (shipped record, card `DONE-032-0.0.9`)
Companion: `docs/SPECS/appx/spec-032-full_relay-0_0_9-rationale.md`
Status: final-accepted

Worker-1-only pass per `BUILD.md` `## Final test-run gate`, run after Slices 0-3, review round 1, and
the cross-slice integration pass all closed `final-accepted`. **This pass changed zero bytes in any
file it audits.** The only file it wrote is this artifact and `worker-memory/worker-1.md`.

**Gate command 10 (`scripts/build_tree_md.py --check`) still fails, and the failure record below
stands unchanged.** It no longer blocks `final-accepted` because the plan's preamble now carries the
pre-flight baseline exception `BUILD.md` `## Final test-run gate` requires — *"Failures block
`final-accepted` unless a pre-flight baseline exception was recorded in the plan's preamble."* The
exception was recorded late, on 2026-08-27, after this gate hit the failure; that lateness is Worker
0's own recorded finding and does not change what the exception covers. This pass re-verified the
exception against the tree rather than accepting it — see `### Gate 10`. **No slice of this cycle owns
the failing behavior**: the staleness is committed at `HEAD`, caused by two maintainer commits from
2026-08-26, and re-looping any slice would change nothing. The maintainer still owes one
`build_tree_md.py` run committed alongside the `0.0.14` work; that obligation is escalated below and
carried as `### Deferred work catalog` entry 6. Every other gate command passes.

## Plan + Final verification (Worker 1)

### Spec status-line re-verification

Performed, per the mandatory per-spawn check. Read lines 1-9 of the spec and 1-9 of the companion.
The spec's header still describes the build's current state at `HEAD`: `Status:` reads
`**SHIPPED (0.0.9)** — card DONE-032-0.0.9`, the unticked-checklist convention is stated with its
reason, the `## Current state` scoping disclosure is intact (and load-bearing — three slices' case-(c)
gradings rest on it), and the final paragraph correctly names the companion as the home of the
deliberative layer, which is true only after this cycle's Slice 0. **No edit owed; none made.**

### Required reading

Read in full: `AGENTS.md`, `START.md`, `docs/builder/BUILD.md` (`## Final test-run gate`,
`## Floor verification`, `## Coverage is the maintainer's gate, not a worker's tool`,
`## Cross-slice integration pass`, `## Claims are proven mechanically, never accepted on prose`,
`## Required reading per worker`, `## Build artifact naming`, `## Severity definitions`),
`docs/builder/ARTIFACT.md`, `docs/builder/worker-1.md`, `GOAL.md`, `CHANGELOG.md`,
`docs/GLOSSARY.md` (the entries this pass measures), the spec, the companion,
`docs/builder/build-032-full_relay-0_0_9.md`, and **every** prior artifact:
`bld-032-slice-0-rationale_extraction.md`, `bld-032-slice-1-root_field_surface.md`,
`bld-032-slice-2-relation_shapes.md`, `bld-032-slice-3-cross_spec_residue.md`,
`bld-032-review-1-spec_diff.md`, `bld-032-integration.md`. Own memory file read first.
**No other worker's memory file was read**, and this pass's own measurement scripts were scoped to
exclude `docs/builder/worker-memory/` up front — the integration pass recorded a crossing on exactly
that, and the rule is about the file, not the reading method.

---

## The gate, command by command

Run from the repo root, in the order `BUILD.md` `## Final test-run gate` gives, then the six
cycle-specific additions. Exit codes are read off the shell, not inferred from output text.

| # | Command | Result | Exit |
| --- | --- | --- | --- |
| 1 | `uv run pytest --no-cov` | `6870 passed, 42 skipped in 70.13s (0:01:10)` | **0** |
| 2 | `uv run python examples/fakeshop/manage.py check` | `System check identified no issues (0 silenced).` | **0** |
| 3 | `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` | `No changes detected` | **0** |
| 4 | `uv run ruff format --check .` | `434 files already formatted` | **0** |
| 5 | `uv run ruff check .` | `All checks passed!` | **0** |
| 6 | `git diff --check` | no output | **0** |
| 7a | `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-032-full_relay-0_0_9.md` | `OK: 40 terms - all have glossary entries and at least one spec link.` | **0** |
| 7b | `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-033-connection_optimizer-0_0_9.md` | `OK: 38 terms - all have glossary entries and at least one spec link.` | **0** |
| 8 | `uv run python scripts/check_citations.py` | `OK: 815 citations resolve (731 in 431 .py files, 84 in KANBAN.md).` | **0** |
| 9 | `uv run python scripts/check_trailing_commas.py --check` | no output (whole-repo default) | **0** |
| 10 | `uv run python scripts/build_tree_md.py --check` | `docs/TREE.md is not up to date; run scripts/build_tree_md.py.` — **FAILS; recorded baseline exception, pre-existing at `HEAD`** | **1 (FAIL)** |
| 11 | `uv run pre-commit run --all-files` | **not run** — unavailable and write-mode; discharged by five read-only proxies, all passing | n/a |

### Gate 1 — the full sweep, verbatim

```
$ uv run pytest --no-cov
...
================= 6870 passed, 42 skipped in 70.13s (0:01:10) ==================
EXIT=0
```

**Zero failures, zero errors, zero xfails reported as failures.** All three test trees ran in the one
invocation (`tests/`, `examples/fakeshop/apps/<app>/tests/` + `examples/fakeshop/tests/`,
`examples/fakeshop/test_query/`) under the project's default parallel `-n` workers, which is the
configuration `BUILD.md` `### Example-project schema changes must sync every schema-module list`
requires — the order-dependent `DuplicatedTypeName` / `LazyType KeyError` class is invisible below a
full parallel run. No `--cov*` flag was used here or anywhere in this pass; `--no-cov` is the only
coverage-shaped flag used and it opts out. **No line coverage was inspected or asserted.**

The 42 skips are the standing `FAKESHOP_SHARDED` and optional-dependency skips (`AGENTS.md`:
sharded-specific tests skip under the default invocation); none is new and none is a masked failure.

### Gate 9 — the layout gate was proved to be a measurement, not a no-op

`check_trailing_commas.py --check` with no path arguments defaults to the whole repo
(`parser.add_argument("paths", nargs="*", …, default: whole repo)`), and silence plus exit 0 is its
pass shape. A control that cannot fail reads exactly like a passing proof, so the instrument was
fired on a mutant outside the repo before the zero was believed:

```
$ uv run python scripts/check_trailing_commas.py --check <scratch>/ctl/bad.py
<scratch>/ctl/bad.py:7:6: non-ASCII U+00E9 'e-acute' not allowed in .py (ASCII + emoji only)
1 non-ASCII char(s) in .py; replace with ASCII (emoji allowed)
EXIT=1
```

The mutant lives outside the working tree; nothing in the repo was written.

### Gate 10 — FAILS, is pre-existing at `HEAD`, and is a recorded baseline exception

```
$ uv run python scripts/build_tree_md.py --check
/Users/riordenweber/projects/django-strawberry-framework/docs/TREE.md is not up to date; run scripts/build_tree_md.py.
EXIT=1
```

`docs/TREE.md` is on this cycle's do-not-touch list, so it was **not** regenerated. What was done
instead is a read-only reproduction that names the cause, performed by copying `docs/TREE.md` to a
scratch path **outside** the repo and pointing the generator's `--md` at the copy (no `git stash`, no
`git checkout`, no `git restore`, no `git worktree` — the maintainer runs concurrent sessions against
this tree):

```
$ cp docs/TREE.md <scratch>/TREE.current.md
$ uv run python scripts/build_tree_md.py --md <scratch>/TREE.current.md      # writes the COPY only
$ diff <(git show HEAD:docs/TREE.md) <scratch>/TREE.current.md
459a460
> |-- test_consumers.py             # Hostile-input containment for the WebSocket consumer (spec-046).
647a649
> |-- test_connection_pagination_api.py  # Live /graphql pagination error containment for connections.
688a691
> |-- test_consumers.py             # Hostile-input containment for the WebSocket consumer (spec-046).
```

**The entire delta is three missing rows for two test files that exist on disk and are tracked at
`HEAD`.** Nothing else differs — not one comment string, not one row belonging to any file this cycle
touched.

Attribution, measured rather than asserted:

| Fact | Command | Result |
| --- | --- | --- |
| `docs/TREE.md` is unmodified in this tree | `git status --short -- docs/TREE.md` | empty — the staleness is committed |
| the two files are tracked at `HEAD` | `git cat-file -e HEAD:<path>` | both present |
| when `tests/test_consumers.py` last changed | `git log -1 --date=short -- …` | `0e5044da 2026-08-26 fix(consumers): fail closed when revalidation itself fails` |
| when `…/test_connection_pagination_api.py` last changed | `git log -1 --date=short -- …` | `3c105cf9 2026-08-26 fix(connection): contain hostile pagination and directive input` |
| when `docs/TREE.md` was last rendered | `git log -1 --date=short -- docs/TREE.md` | `91989b60 2026-08-25 docs(tree,agents): record the single-sourced release and the run's new modules` |

Both files entered the tree in maintainer commits **one day after** the last `docs/TREE.md` render,
in the concurrent `0.0.14` bug-hunt / containment work, and neither commit regenerated the doc.

**This cycle contributes zero to the failure, and that is a proof rather than an inference.** The
render above consumed the working tree's *edited* docstrings — the three test modules Worker 0
predicted would be safe because their edits sit on lines 4-5 rather than the first summary line — and
still reproduced `HEAD`'s `docs/TREE.md` byte-for-byte except for the three unrelated rows. Had any
edit disturbed a rendered summary, the diff would carry a **changed** comment line; it carries none.
The prediction is therefore settled in the affirmative by the instrument, which is why the check was
run rather than reasoned about.

**Escalated to the maintainer.** Per `BUILD.md` `## Claims are proven mechanically, never accepted on
prose`, a runtime/tooling failure believed pre-existing at `HEAD` is not worker-verifiable —
reproducing it in isolation needs a clean `HEAD` tree and this tree is legitimately dirty with the
cycle's work plus the maintainer's untracked `0_0_14.md`. Recorded above is every piece of evidence
this pass can obtain read-only. The fix is one command the maintainer owns
(`uv run python scripts/build_tree_md.py`, then commit `docs/TREE.md` with the `0.0.14` work it
belongs to); it is **not** a re-loop of any slice in this cycle, and no `revision-needed` re-dispatch
would touch it. **That obligation is still open.** It is carried as `### Deferred work catalog`
entry 6 so it survives this cycle's close, and the failure record above is left intact rather than
softened: the exception licenses `final-accepted`, it does not discharge the run the maintainer owes.

#### The baseline exception, re-verified rather than accepted

When this gate first ran, the plan's preamble recorded no baseline exception, so under `BUILD.md`
`## Final test-run gate` — *"Failures block `final-accepted` unless a pre-flight baseline exception
was recorded in the plan's preamble."* — the failure blocked `final-accepted` regardless of ownership,
and this artifact was set `revision-needed` on that ground alone. Worker 0 has since recorded the
exception in `docs/builder/build-032-full_relay-0_0_9.md`'s pre-flight preamble, dated 2026-08-27 and
labelled late in its own text: the bullet opens **"Baseline exception, recorded LATE (2026-08-27)
rather than at pre-flight — `scripts/build_tree_md.py --check` fails at HEAD"** and names the lateness
as the finding — *pre-flight should run every gate command it expects the final gate to run, or a
pre-existing failure arrives at the end of the cycle looking like the cycle caused it.* The preamble
is the home `BUILD.md` names, so the rule's condition is met in the place the rule points at.

An exception is a claim like any other, so this pass re-derived it instead of accepting it
(`BUILD.md` `## Claims are proven mechanically, never accepted on prose`). Three things had to hold —
that the entry exists in the preamble, that it describes *this* failure, and that the failure is
genuinely pre-existing and untouched by this cycle:

| Re-verification | Command | Result |
| --- | --- | --- |
| the exception is in the plan's preamble and names this gate | read `docs/builder/build-032-full_relay-0_0_9.md` pre-flight block | present, dated 2026-08-27, names `scripts/build_tree_md.py --check` and `docs/TREE.md` |
| the failure it describes is the failure hit here | `uv run python scripts/build_tree_md.py --check` | `docs/TREE.md is not up to date; run scripts/build_tree_md.py.` — EXIT 1, unchanged |
| `docs/TREE.md` on disk is `HEAD`'s, so the staleness is committed | `diff <copy of docs/TREE.md> <(git show HEAD:docs/TREE.md)` | identical; `git status --short -- docs/TREE.md` empty |
| the delta is exactly the three rows the exception claims | re-render into a scratch copy **outside** the repo, `diff` against `git show HEAD:docs/TREE.md` | `459a460`, `647a649`, `688a691` — three **added** rows, zero changed rows |
| the two modules post-date the last render | `git log -1 --date=short -- <each path>` | `0e5044da` 2026-08-26 and `3c105cf9` 2026-08-26 vs `docs/TREE.md` at `91989b60` 2026-08-25 |
| neither module is in this cycle's diff | `git diff --name-only` | nine paths, neither among them |

The re-render was performed the same read-only way as the original: `cp docs/TREE.md` to a scratch
path outside the repository, point `--md` at the **copy**, and diff the copy against
`git show HEAD:docs/TREE.md`. No `git stash`, `git checkout`, `git restore`, or `git worktree` was
used at any point, and `git status --short -- docs/TREE.md` was re-read afterwards and is still empty
— the repository's own `docs/TREE.md` was never written.

**Verdict: the exception covers the failure exactly, and covers nothing else.** Its three-row claim is
the whole delta, not a sample of it; its attribution to `0e5044da` / `3c105cf9` re-derives
independently; and the two files it names are absent from this cycle's nine-path diff. Gate 10 is
therefore a recorded baseline exception rather than an open failure, and it no longer blocks
`final-accepted`. Nothing about the exception weakens the escalation above.

### Gate 11 — `pre-commit`, skipped for two stated reasons, and discharged by proxies

`uv run pre-commit --version` fails with `Failed to spawn: pre-commit` — it is not in the project
environment (`.pre-commit-config.yaml`'s own header says it is invoked as `uvx pre-commit`, i.e. from
an ephemeral download). Second and independently sufficient: every hook in that config is
**write-mode** — `check_trailing_commas.py --fix`, `ruff format`, `ruff check --fix`, and
`build_kanban_tracked_path_constants.py`, which writes a constants file — so `--all-files` would
rewrite files across a tree carrying a concurrent session's work. `worker-1.md` forbids this pass from
editing source, and the brief says to skip rather than force it. **Skipped, said so.**

All five hooks have an exact read-only proxy, and all five were run:

| Hook | Read-only proxy run | Exit |
| --- | --- | --- |
| `kanban-tracked-path-constants` | `uv run python scripts/build_kanban_tracked_path_constants.py --check` | **0** |
| `source-layout` | gate 9 (`check_trailing_commas.py --check`, whole repo) | **0** |
| `ruff-format` | gate 4 (`ruff format --check .`) | **0** |
| `ruff-check` | gate 5 (`ruff check .`) | **0** |
| `check-citations` | gate 8 (`check_citations.py`) | **0** |

The hook set is therefore green on the evidence, without a single byte written.

### Floor verification

**No floor-verification scope declared.** The build plan's preamble reads
`Floor-verification scope: none. No slice touches a Django / Strawberry / channels integration seam.`
— true by construction, since no slice changed executable bytes. No floor venv was built and the
shared `.venv` was not mutated, installed into, or read for version numbers.

### Closing re-check: the tree has not drifted under a concurrent writer

This gate spans a maintainer edit to the plan's preamble, and the maintainer runs concurrent sessions
against this tree, so the cheap read-only gates were re-run before `final-accepted` was set. The full
`pytest` sweep was **not** re-run: it passed at `6870 passed, 42 skipped` and this cycle has changed
nothing since — re-running a 70-second sweep over an unchanged program would measure the same program
twice. No `--cov*` flag was used here or anywhere in this pass.

| Command | Result | Exit |
| --- | --- | --- |
| `uv run ruff format --check .` | `434 files already formatted` | **0** |
| `uv run ruff check .` | `All checks passed!` | **0** |
| `git diff --check` | no output | **0** |
| `uv run python scripts/check_citations.py` | `OK: 815 citations resolve (731 in 431 .py files, 84 in KANBAN.md).` | **0** |
| `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-032-full_relay-0_0_9.md` | `OK: 40 terms - all have glossary entries and at least one spec link.` | **0** |

Every result is identical to the first reading, including the citation gate's `815` and the glossary
gate's `40 terms`. Exit codes were read off the shell per command rather than through a pipeline —
under `zsh` a `${PIPESTATUS[0]}` reads empty, which is exactly the shape of a control that reports
nothing and looks like a pass.

**One thing did move, and it is the maintainer's, not this cycle's.** `HEAD` advanced from `0ff3cea5`
to **`b2392014`**, which committed the eleven `bld-031-*` deletions that were dirty at this cycle's
pre-flight and added `docs/builder/build-031-globalid_encoding-0_0_9.md`. Its `--stat` is thirteen
files, all under `docs/builder/`, none of them this cycle's and none of them `docs/TREE.md` or the
kanban DB. Slice 2 already recorded this commit landing mid-cycle. It changes no gate result: gate 10
was re-derived against the *current* `HEAD` above, and `git status --short` still lists exactly the
nine tracked modifications and eight untracked files in `## Files the maintainer reviews and commits`,
plus the maintainer's `0_0_14.md`. Nothing was reverted, tidied, or staged.

While re-reading that inventory this pass corrected a count of its own: the section's lead line said
*"nine tracked modifications plus seven untracked files"* while enumerating **nine** untracked files
beneath it. Re-measured — `git status --short` gives 9 `M` rows and 10 `??` rows, one of which is the
maintainer's `0_0_14.md` — the number is **nine and nine**, and the enumeration was right all along.
Counted rather than carried, per the standing rule that a stated count reads as measured to every
later pass.

### The cycle's central claim, re-proved by a third independent instrument

"Zero executable bytes" is the premise every scope decision in this cycle rests on, and it is the
`### Claims are proven mechanically` "relocated / carried over unchanged" shape. Slice 3 proved it and
Worker 0 re-proved it; this gate proves it a third time rather than inheriting either.

Instrument: parse each file and its `git show HEAD:<path>` content with `ast`, blank every module /
class / function docstring to a sentinel, flatten every node's `lineno` / `col_offset` /
`end_lineno` / `end_col_offset` to 0, then compare `ast.dump`. Comments never reach the AST, so a
match means the executable program is identical.

**Proved failable in both directions before any result was believed** — three negatives that must
compare equal and three mutations that must not:

```
comment-only change:             identical=True
docstring-only change:           identical=True
line-shift only:                 identical=True
EXECUTABLE change (operator):    identical=False
EXECUTABLE change (default arg): identical=False
EXECUTABLE change (arg rename):  identical=False
```

Result over all seven files:

```
examples/fakeshop/apps/library/schema.py:            raw_identical=False  ast_normalized_identical=True
examples/fakeshop/test_query/test_library_api.py:    raw_identical=False  ast_normalized_identical=True
examples/fakeshop/test_query/test_products_api.py:   raw_identical=False  ast_normalized_identical=True
tests/test_relay_connection.py:                      raw_identical=False  ast_normalized_identical=True
tests/test_relay_node_field.py:                      raw_identical=False  ast_normalized_identical=True
tests/testing/test_relay.py:                         raw_identical=False  ast_normalized_identical=True
tests/types/test_base.py:                            raw_identical=False  ast_normalized_identical=True
MISMATCHES= 0
```

`raw_identical=False` everywhere confirms the files really did change (a checker fed identical inputs
would report the same `True` and prove nothing); `MISMATCHES=0` confirms none of those changes is
executable. **The suite's 6870 passes are therefore a re-run of `HEAD`'s program, not a re-run of a
modified one** — which is the only reading under which a green sweep says anything about a
documentation cycle.

---

## Deferred work catalog

The next spec author's reading list. Re-derived from the artifacts in this pass rather than copied:
every `### Notes for Worker 1 (spec reconciliation)`, `What looks solid`, `### Low:` / `### Medium:`,
and deferral section of `bld-032-slice-0` … `bld-032-slice-3`, `bld-032-review-1-spec_diff.md`, and
`bld-032-integration.md` was walked, and every fact below was re-measured against the tree today.

**Measured count: seven items routed forward, filed as six entries — six items in five entries from
the artifact walk, plus one entry this gate itself raises.** Entry 6 (`docs/TREE.md` regeneration) has
no source artifact by construction: no slice could have found it, because it is a gate command's
failure and the gate is the first pass that runs one. The five-entry number below therefore describes
the artifact walk, which is its subject; the catalog's own total is six.

Within the artifact walk, the integration pass numbered
six entries; the difference is a filing convention and not a discrepancy — its entries 1 and 2 are the
two `docs/GLOSSARY.md` siblings, which it itself declared inseparable, and they are filed here as the
single entry that discharge actually is. Fourteen further items appear in the artifacts as deferrals
and are **not** in this catalog because they were discharged inside the cycle (Slice 0 notes 1-4,
Slice 1 note 2, Slice 2 notes 1-2, review M-2); four more were deliberately not routed and are
recorded below with their reasons so the next audit does not re-raise them.

### 1. `docs/GLOSSARY.md` — two falsified claims from this card, in one DB-generated file, one discharge

**Owner: maintainer follow-up** (glossary-app DB edit in `examples/fakeshop/db.sqlite3`, then
`uv run python scripts/build_glossary_md.py`). Sources: `bld-032-slice-1-root_field_surface.md`
`### Notes for Worker 1` item 1, and `bld-032-review-1-spec_diff.md` M-1. Licensed as a deferral by
the build plan's `## Scope of this cycle (maintainer-set)`: `docs/GLOSSARY.md` is out of scope for
every slice, and it is DB-generated, so a hand edit would be reverted by the next render.

**(a) `## DjangoNodesField` — the batch is not uncapped.** Re-measured today at `docs/GLOSSARY.md`
line 717, one occurrence of `deliberately uncapped` in the file. Present text:

> The batch is deliberately uncapped in `0.0.9` (parity with both upstreams; request-size limiting
> belongs to the consumer's transport layer).

Falsified by `django_strawberry_framework/resource_policy.py::ResourcePolicy.max_node_ids` (default
`200`), charged pre-execution against the `ids` argument by
`django_strawberry_framework/extensions/resource_policy.py`. Replacement: state that the batch is
bounded by `ResourcePolicy.max_node_ids` (default `200`), charged pre-decode against the `ids`
argument, and that the bound is deliberately independent of `max_page_size` so raising a page size
never raises a batch size. The spec's own Edge case and Risks item were corrected by Slice 1; this
entry is the same sentence's other home.

**(b) `` ## `Meta.relation_shapes` `` — `"both"` is no longer the default.** Re-measured today at
`docs/GLOSSARY.md` line 1350; the present text reads
`` values `"list"` / `"connection"` / `"both"` (`"both"` is the implicit default) ``. Falsified by
`django_strawberry_framework/types/base.py::DEFAULT_RELATION_SHAPE = "connection"` (spec-047, shipped
in `0.0.14`). Worker 3's corrected sentence, to be used verbatim:

> `Meta.relation_shapes` is a `dict[str, str]` with values `"list"` / `"connection"` / `"both"`
> (`"connection"` is the implicit default since `0.0.14`): the default emits the connection alone
> and suppresses the `list[T]` field, `"both"` is the explicit opt-in that keeps that list beside
> it, and `"list"` suppresses the connection.

**Why (a) and (b) are one entry and must be one discharge.** Same card's falsified claims, same
DB-generated file, one edit plus one re-render closes both; filed separately, the cheaper one gets
skipped. The urgency is that **the file already contradicts itself** — line 1637's
`## Relay Node integration` entry states the `0.0.14` many-side flip correctly
(*"a selected many-side relation renders as the synthesized `<field>Connection` ALONE"*), so a reader
comparing the two entries cannot tell which half is current. That is worse than either stale claim
alone.

### 2. `docs/SPECS/spec-033-connection_optimizer-0_0_9.md` — the `### Decision 9` in-page anchor is dead at five sites

**Owner: `spec-033`'s own residual cycle** (maintainer to schedule). Source:
`bld-032-slice-3-cross_spec_residue.md` `### Notes for Worker 1` item 1, confirmed independently by
review round 1 `### Verdict on the three deferred-work routings` item 1 and by the integration pass.
Licensed as a deferral by the build plan's scope line, which grants this cycle sibling-spec edits only
for *"sibling spec files whose citations the rationale move breaks"* — this is `spec-033`-internal
authoring rot the move did not cause.

Re-measured today, and **pre-existing at `HEAD` proved read-only**:
`git show HEAD:docs/SPECS/spec-033-connection_optimizer-0_0_9.md | grep -c` returns **5**, identical
to the working tree's 5, and this cycle's whole `spec-033` diff is `2 insertions(+), 1 deletion(-)`
(one citation sentence plus one link definition) touching neither the heading nor any use site.

Replacement text: replace every
`#decision-9--the-edgesnode-selection-helpers-consolidate-into-the-walker` with
`#decision-9--the-edges--node--selection-helpers-consolidate-into-the-walker`. **The heading at line
382 is correct and must not be changed** — GitHub drops the code span's braces and hyphenates each
remaining space, so the doubled hyphens are the resolving form. Sites: the `Status:` line, the
`## Slice checklist` Slice-1 entry, the `## Current state` selection-unwrap bullet, `### Decision 11`'s
build-proper source bullet, and `## Definition of done` item 2. It is the only anchor of this shape
under `docs/`.

### 3. Stale pre-archive `docs/spec-<NNN>` prose paths naming archived specs — 22 occurrences, two homes

**Owner: maintainer follow-up**, split by home — the `.py` half belongs to each named spec's own
residual cycle; the `KANBAN.md` half is one card-body DB edit. Sources:
`bld-032-slice-3-cross_spec_residue.md` `### Notes for Worker 1` item 2 (the `.py` half, confirmed by
review round 1's verdict item 2) and `bld-032-integration.md` `## New finding this pass` (the
`KANBAN.md` half). Licensed as a deferral because the `.py` half would change executable bytes on
other cards' surfaces and the `KANBAN.md` / `KANBAN.html` half is DB-generated and on the plan's
do-not-touch list.

**(a) Nine occurrences in `.py` docstrings**, re-enumerated today, none of them spec-032's:
`scripts/check_spec_glossary.py` x4 (`018`), `tests/test_list_field.py` (`020`),
`tests/optimizer/test_multi_db.py` (`023`), `examples/fakeshop/test_query/test_glossary_api.py` x2
(`028`), `tests/test_connection.py` (`030`). Repair is mechanical — insert `SPECS/` after `docs/` —
but read the site first: the two `test_glossary_api.py` hits are asserted **data values** matched
against the glossary DB (a code-only fix would break the test), and the four
`check_spec_glossary.py` hits are illustrative usage examples in a docstring.

**(b) Thirteen occurrences in `KANBAN.md`**, plus the two `spec-032` ones mirrored in `KANBAN.html`
(same card body, same render). By spec: `028` x3, `029` x2, `030` x2, **`032` x2**, `033`, `034`,
`035`, `045`. Every distinct path was disk-checked today: all eight resolve to `MISSING` at
`docs/spec-…` and `EXISTS` at `docs/SPECS/spec-…`. The file's other four `docs/spec-<NNN>` spellings
(`057`, `058` x2, `060`) are **correct as written** — those specs are in flight and unwritten, and
`docs/` is a working spec's proper location; they must not be swept.

Measured before calling it rot, per the standing rule: `.py` carries **30** correct
`docs/SPECS/spec-<NNN>` spellings against these **9** stale (29 vs 26 within the four code roots the
slices walked, plus one in `docs/dry/`, which reconciles the integration pass's 26-plus-3-repaired
exactly); `KANBAN.md` carries **160** correct against **17** stale, of which 4 are the legitimate
in-flight paths. The correct form is overwhelmingly the convention, which is what makes the minority
a defect rather than a style preference.

**Two of the thirteen are this card's own residue** (`docs/spec-032-full_relay-0_0_9.md` x2 in
`KANBAN.md`, x2 in `KANBAN.html`) and should be discharged with this cycle's commit; the rest belong
to their own specs' cycles. The fix is a card-body DB edit plus
`scripts/build_kanban_md.py` **and** `scripts/build_kanban_html.py` (the `KANBAN.html` Vue shell is
hand-edited; only its data block regenerates), never a hand edit of either rendered file.

### 4. `tests/test_relay_connection.py` — two comment-layer items, one file, one touch

**Owner: maintainer follow-up.** Sources: `bld-032-slice-3-cross_spec_residue.md`
`### Notes for Worker 1` item 3, and review round 1 findings L-1 and L-2, both rejected-for-this-pass
in writing under `## Final verification (Worker 1)`. Licensed as a deferral by the build plan's scope
line: a `.py` edit is authorized **only** on a finding that the code skipped or dropped a spec
contract, and across four slices and one review round no code gap was found. A parametrize id is an
executable byte.

**(a) The `["both", "connection"]` parametrization is degenerate.** Seven decorator sites (lines 832,
854, 870, 901, 915, 941, 960) feed
`tests/test_relay_connection.py::_shelf_books_connection_schema`, whose body passes
`meta_extra={"relation_shapes": {"books": shape}} if shape == "connection" else None` — so the
`"both"` arm supplies **no** `relation_shapes` key and exercises the package default, which has been
`"connection"` since `567cc6d0`. Both arms resolve to the same shape.

**A count correction, measured rather than carried:** the prior artifacts state *"Fourteen test ids
read `[both]`"*. Collected today
(`uv run pytest tests/test_relay_connection.py --no-cov --collect-only -q -p no:randomly`), the file
yields **8** `[both]` ids and 8 `[connection]` ids. **Seven** of the `[both]` ids are the degenerate
ones; the eighth, `test_non_node_target_explicit_raises[both]`, comes from a *different*
parametrization (`["connection", "both"]` at line 323) that passes the shape explicitly to a
non-Node target and asserts the raise — **genuine, and it must not be swept with the others.**
Fourteen is the total id count across the seven sites (both arms), not the count of misleading ids.
The defect is seven ids, and the population contains one look-alike that is correct.

Not a code defect: no assertion is false, and the pair still separates default resolution from
explicit lookup — which is exactly what the docstring says at `HEAD` today, because Slice 3 corrected
it. Suggested repair: rename the arm `"default"` and invert the builder's condition, or add a third
arm passing an explicit `{"books": "both"}` so the matrix regains a genuine `"both"` run.

**(b) A comment reflow left a 13-character orphan line.** `tests/test_relay_connection.py:790` is the
bare line `# WITHOUT the`, mid-sentence in the rewritten section banner. Cosmetic — `ruff format
--check` and `check_trailing_commas.py --check` both pass over it (gates 4 and 9 above).

**Deliberately filed as one entry**: both live in the same file and one edit discharges both. A
separate entry is how the cheaper of two same-file items gets skipped.

### 5. `TODAY.md` — the relation-as-Connection paragraph leads with the retired default

**Owner: maintainer follow-up.** Source: review round 1 finding L-5, rejected-for-this-pass in
writing. Licensed as a deferral by the build plan's out-of-scope list, which names `TODAY.md`
explicitly.

Re-measured today: `TODAY.md` line 180 opens *"As of `0.0.9`, every to-many relation between two
Relay-Node-shaped types gains a paginated `<field>Connection` sibling alongside the plain `list[T]`
field"* and self-corrects four sentences later with *"Since `0.0.14` the default is the connection
**alone** — `CategoryType.properties` is reachable only through `propertiesConnection`"*. Weaker than
entry 1 because the paragraph is self-consistent by its end and its later half is correct; still a
defect, because a reader who stops at the first sentence gets the retired contract. The repair is to
lead the paragraph with the current default and keep the `0.0.9` shape as the history it is.

### 6. `docs/TREE.md` — one `build_tree_md.py` run, owed alongside the `0.0.14` commits

**Owner: maintainer follow-up**, to be committed with the `0.0.14` work that caused it — one command,
`uv run python scripts/build_tree_md.py`, then commit `docs/TREE.md`. Source: this artifact's
`### Gate 10`; licensed as a deferral by the build plan's `## Scope of this cycle (maintainer-set)`,
which names `docs/TREE.md` in the out-of-scope list, and by the pre-flight baseline exception recorded
in that plan's preamble on 2026-08-27. `START.md` gives the second, independent reason not to take it
here: never regenerate a rendered doc while another session's feature work is mid-flight — the
`0.0.14` containment work is exactly that.

`scripts/build_tree_md.py --check` exits 1 at `HEAD`. Re-measured in this pass against the current
`HEAD` (`b2392014`), the whole delta is **three added rows** and zero changed rows:

- `tests/test_consumers.py` — two rows (current tree and target tree), from `0e5044da` (2026-08-26).
- `examples/fakeshop/test_query/test_connection_pagination_api.py` — one row, from `3c105cf9`
  (2026-08-26).

Both commits post-date `docs/TREE.md`'s last render (`91989b60`, 2026-08-25) by a day, `docs/TREE.md`
is clean in `git status`, and neither file appears in this cycle's nine-path diff — so the staleness
is committed at `HEAD` and this cycle contributes nothing to it. **The exception licenses
`final-accepted`; it does not discharge the run.** This entry exists so the obligation outlives the
cycle: the next reader of the tooling gate should find `docs/TREE.md` current, and if it is not, this
is the entry that says why and whose it is.

The second half of the item is Worker 0's own finding and belongs to the agentflow rather than to any
file: **pre-flight should run every command the final gate runs.** This exception was recorded on the
last day of the cycle because pre-flight never ran `build_tree_md.py --check`, which is how a failure
already committed at `HEAD` arrived at the gate looking like the cycle had caused it and cost a
`revision-needed` round-trip to attribute.

### Deliberately NOT routed — settled questions, recorded so the next audit does not re-open them

- **`BACKLOG.md`'s `stable_cursor_field` entry describing a shipped feature in the future tense, and
  the missing `` ## `Meta.cursor_field` `` glossary heading.** Source: `bld-032-slice-3` notes 4 and 5.
  **Already carded**: `KANBAN.md` carries both by name inside one undecided "where is the shipped
  keyset feature documented" bullet, alongside the absent CHANGELOG entry. Re-derived by Slice 3
  rather than inherited. Routing them again would create a duplicate of a live card.
- **Review round 1 L-3 — six companion `### Justification (moved from the spec)` bodies opening with
  a lowercase fragment.** **Rejected with reason, and deliberately not routed.** Two independent
  grounds: `worker-1.md` `### Performing the rationale move` makes the rationale file append-only
  during the build, and byte-verbatim is the property that makes the move auditable — a future reader
  can diff any moved body against the spec's git history and confirm nothing was reworded.
  Capitalising six openers destroys that for a cosmetic gain, and doing it later costs the same, so
  leaving the item open would invite a future pass to "fix" a load-bearing property.
- **Review round 1 L-4 — `## Current state`'s "as of this writing".** **Rejected with reason.** It
  scopes a section rather than timestamping an edit, and three slices' case-(c) gradings (Slice 1's
  five struck-through foundation items, Slice 2's `GenreType` description, Slice 3's products
  sentence) rest on the section declaring its own date. Line 3's disclosure and line 101's are
  designed redundancy, not rot.
- **The build plan's own two factual slips** — B7 naming `IssueType` where the `{"issues":
  "connection"}` key is on `PeriodicalType`, and the A3 bucket (Bucket B, not A: `git log -S` returns
  exactly one commit, `dc00f4a6`, post-ship). Corrected in the slice artifacts' evidence tables.
  Informational: the plan is Worker 0's file and closes with the cycle, and no spec sentence depends
  on either.

---

## What this cycle proved about the code

**Nothing in `spec-032` was ever skipped, dropped, or forgotten.** Every functional deliverable and
every spec-named test the card promised exists at `HEAD` and passes: the six named-helper rejections
and their two re-affirmation pins; both root fields with `strawberry.ID` arguments, the narrow decode
catch, id-slot pk pre-coercion, the typed-match check, per-type batching, `_interleave`, the
`_node_fields_declared` ledger and the finalization no-Node-types check; `Meta.relation_shapes` with
its validation, the Phase-2.5 synthesis and its two-surface collision guard; the always-concrete
`_connection_type_for` with the `relay_max_results` cap and the live conformance matrix; the public
`testing/relay.py` helpers with cause-discriminated remediations; and the fakeshop library activation
with all eleven live tests. Worker 0 verified this against source before any dispatch, four
reconciliation slices re-verified every finding independently at `HEAD`, and a Worker 3 pass over the
whole diff sampled the contract sentences afresh. **Every one of the twelve divergences the cycle
found was a stale sentence in the spec, never a missing behavior in the package** — either surface
this card's own build shipped and never wrote down, or a contract a later card (spec-047, spec-033,
the `0.0.14` security work) deliberately changed underneath a shipped spec. No builder was dispatched
because none was owed, and gate 1's 6870 passes over a program proved byte-identical to `HEAD`
confirm the cycle left that true.

---

## Byte counts and the closing chain against `HEAD`

Measured in this pass with `git show HEAD:<path> | wc -c` against `wc -c <path>`, not carried from
any prior artifact.

| File | `HEAD` | Now | Delta |
| --- | --- | --- | --- |
| `docs/SPECS/spec-032-full_relay-0_0_9.md` | 188,525 | **170,378** | **-18,147 (-9.6%)** |
| `docs/SPECS/appx/spec-032-full_relay-0_0_9-rationale.md` | did not exist | **108,497** | **net-new** |
| `docs/SPECS/spec-033-connection_optimizer-0_0_9.md` | 173,810 | **174,040** | **+230** |
| `examples/fakeshop/apps/library/schema.py` | 64,505 | 64,509 | +4 |
| `examples/fakeshop/test_query/test_library_api.py` | 358,521 | 358,510 | -11 |
| `examples/fakeshop/test_query/test_products_api.py` | 182,197 | 182,332 | +135 |
| `tests/test_relay_connection.py` | 122,916 | 123,238 | +322 |
| `tests/test_relay_node_field.py` | 54,637 | 54,637 | **0** |
| `tests/testing/test_relay.py` | 12,780 | 12,786 | +6 |
| `tests/types/test_base.py` | 91,949 | 91,972 | +23 |

Spec lines 794 -> **710**; companion **471** lines. The seven `.py` files total **+479 bytes** of
comment and docstring text and **zero** executable bytes (proved above). `tests/test_relay_node_field.py`
is worth naming: its delta is 0 while `raw_identical=False` — a byte-neutral comment rewrite, and
exactly the case a size-only check would have called untouched.

The chain closes to the byte at every recorded handoff: `188,525` (Slice 0 in) -> `145,056` ->
`157,923` -> `165,828` -> `170,612` -> `170,378` (review round M-2's seven cuts, `-234`) = the file on
disk today. `174,040 - 173,810 = 230`, exactly `spec-033`'s claimed delta, and that diff is
`2 insertions(+), 1 deletion(-)` — one citation sentence and one link definition, nothing else. The
shape inverts mid-cycle and that is the signature to remember: the rationale move took 43,469 bytes
out, then three reconciliation slices put 25,322 back.

---

## Files the maintainer reviews and commits

**This cycle's output — nine tracked modifications plus nine untracked files.**

Modified, tracked:

1. `docs/SPECS/spec-032-full_relay-0_0_9.md` — the reconciled spec.
2. `docs/SPECS/spec-033-connection_optimizer-0_0_9.md` — one citation repair + one link def (+230).
3. `examples/fakeshop/apps/library/schema.py` — comment only.
4. `examples/fakeshop/test_query/test_library_api.py` — docstring only.
5. `examples/fakeshop/test_query/test_products_api.py` — comment/docstring only.
6. `tests/test_relay_connection.py` — comment/docstring only.
7. `tests/test_relay_node_field.py` — comment only.
8. `tests/testing/test_relay.py` — comment only.
9. `tests/types/test_base.py` — docstring only.

Untracked, new:

10. `docs/SPECS/appx/spec-032-full_relay-0_0_9-rationale.md` — the net-new companion (the cycle's
    primary deliverable).
11. `docs/builder/build-032-full_relay-0_0_9.md` — the build plan.
12. `docs/builder/bld-032-slice-0-rationale_extraction.md`
13. `docs/builder/bld-032-slice-1-root_field_surface.md`
14. `docs/builder/bld-032-slice-2-relation_shapes.md`
15. `docs/builder/bld-032-slice-3-cross_spec_residue.md`
16. `docs/builder/bld-032-review-1-spec_diff.md`
17. `docs/builder/bld-032-integration.md`
18. `docs/builder/bld-032-final.md` — this file.

**Stage these as an explicit path list.** `git add -A` would sweep the concurrent work below.

**Concurrent work — leave alone, do not stage with this cycle, never revert.**

- `0_0_14.md` at the repo root (untracked). The maintainer's in-flight `0.0.14` notes. Not read as
  instruction, not touched, not staged.
- `docs/TREE.md` is **not** dirty, but it is stale at `HEAD` for the reason in `### Gate 10` — a
  regenerate belongs with the `0.0.14` commits that introduced `tests/test_consumers.py` and
  `examples/fakeshop/test_query/test_connection_pagination_api.py`, not with this cycle. It is
  `### Deferred work catalog` entry 6, and the pre-flight baseline exception that unblocks the gate
  does not discharge it.
- `examples/fakeshop/db.sqlite3` is clean in this tree and was never written. The catalog's entries 1
  and 3 both call for DB edits; those are the maintainer's, after this cycle's commit.

Untouched and verified absent from `git status --short`: `KANBAN.md`, `KANBAN.html`,
`docs/GLOSSARY.md`, `CHANGELOG.md`, `TODAY.md`, `README.md`, `GOAL.md`, `docs/TREE.md`,
`docs/README.md`, `BACKLOG.md`, `examples/fakeshop/db.sqlite3`, and every file under
`django_strawberry_framework/`.

---

### DRY analysis

Not applicable to source: this pass writes no Python, proposes no helper, and the cycle changed zero
executable bytes (re-proved above). Recorded rather than skipped so a later pass can see the question
was asked. The prose form of the question — one contract, one vocabulary, one home — was answered by
the integration pass and is not re-litigated here; the one live duplication candidate it identified
(the `docs/GLOSSARY.md` pair) is catalog entry 1, filed as a single discharge for exactly the DRY
reason.

### Test additions / updates

None. This pass adds no source and no test. The only `pytest` invocations were gate 1
(`--no-cov`, the required full sweep) and one `--collect-only -q` run used to measure the `[both]` id
population in catalog entry 4. **No `--cov*` flag was used anywhere in this pass**, and no line
coverage was inspected or asserted.

### Spec slice checklist (verbatim)

Not applicable. The final test-run gate is defined by `BUILD.md`, not by an entry in the spec's own
`## Slice checklist` (which carries the seven shipped build slices 1-7). There are no verbatim
sub-checks to copy, tick, or audit. Every reconciliation slice's artifact records the same, so no box
anywhere in this cycle is silently un-ticked. Recorded explicitly rather than omitted, so the absence
reads as a decision.

### Implementation discretion items

None. Every choice in a gate pass is the custodian's; nothing was delegated.

### Summary

Ten of eleven gate commands pass. The full sweep is **6870 passed, 42 skipped**, with zero failures
and zero errors, run with `--no-cov` and no coverage inspected; Django's `check` and
`makemigrations --check` are clean; `ruff format --check`, `ruff check` and `git diff --check` are
clean tree-wide; both glossary gates, the citation gate and the source-layout gate exit 0, the last of
them on an instrument fired against a mutant first. `pre-commit` is unavailable in the project
environment and every hook in it is write-mode, so it was skipped and discharged instead by all five
hooks' read-only proxies, each passing. No floor-verification scope was declared and none was owed.

**`scripts/build_tree_md.py --check` fails, and this cycle did not cause it.** The generator's output
reproduces `HEAD`'s `docs/TREE.md` exactly except for three rows naming two test files the maintainer
added on 2026-08-26, one day after the doc's last render, in commits `0e5044da` and `3c105cf9`. The
render consumed this cycle's *edited* docstrings and produced no changed comment line, which settles
Worker 0's prediction affirmatively by measurement rather than by argument. `docs/TREE.md` is on the
do-not-touch list and was not regenerated; the failure is escalated to the maintainer with the
read-only evidence. The plan's preamble now carries the pre-flight baseline exception `BUILD.md`
requires, recorded late (2026-08-27) and labelled late in its own text, so under
*"Failures block `final-accepted` unless a pre-flight baseline exception was recorded in the plan's
preamble"* gate 10 no longer blocks. This pass re-verified the exception rather than accepting it —
the three-row delta, the two commit attributions, `docs/TREE.md`'s clean status, and the two files'
absence from this cycle's diff all re-derive, all read-only, no `git stash` / `checkout` / `restore` /
`worktree` anywhere. **The failure record is left intact and the maintainer still owes one
`build_tree_md.py` run committed with the `0.0.14` work**; it is catalog entry 6.

The deferred-work catalog carries **seven routed items filed as six entries**, each with a named owner
and each re-measured today: the two `docs/GLOSSARY.md` siblings as one inseparable discharge (the file
currently contradicts itself), `spec-033`'s five-site dangling `### Decision 9` anchor (proved
pre-existing at `HEAD`), the twenty-two stale pre-archive `docs/spec-<NNN>` paths across `.py` and
`KANBAN.md` (two of them this card's own), `tests/test_relay_connection.py`'s parametrize-id pair as
one file and one touch, `TODAY.md`'s paragraph opener, and the `docs/TREE.md` regeneration the
maintainer owes alongside the `0.0.14` commits. One carried number was corrected in the
re-derivation: the degenerate `[both]` ids are **seven**, not fourteen, and the population contains an
eighth `[both]` id that is genuine and must not be swept with them. Four items are deliberately not
routed, each with its reason on record.

The byte chain closes to the byte at every handoff (spec `188,525 -> 170,378`, `-9.6%`; companion
`108,497` net-new; `spec-033` `+230`; seven `.py` files `+479` bytes of comment text), and the cycle's
premise is re-proved by a third independent instrument: **zero executable bytes changed**, on an
AST-normalized comparison against `HEAD` that was shown to fire on three kinds of executable mutation
and to stay silent on three kinds of cosmetic one. What the cycle proved about the code is that
`spec-032`'s contracts were never skipped, dropped, or forgotten — every divergence it found was a
stale sentence in the spec.

### Spec changes made (Worker 1 only)

**None.** The spec's status/header lines were re-verified this spawn and no edit was owed; the gate
exposed no spec defect. No source or test file was edited, no sibling spec was edited, the companion
was not edited, and no closeout or agentflow doc was edited. Nothing was committed and no branch was
created.

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
