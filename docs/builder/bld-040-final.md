# Build: Final test-run gate — 040 (auth mutations, retrospective reconciliation)

Spec reference: `docs/SPECS/spec-040-auth_mutations-0_0_13.md` (archived; shipped in `0.0.13`)
Status: final-accepted

Build plan: [`docs/builder/build-040-auth_mutations-0_0_13.md`][build-040]. Gate definition:
[`BUILD.md`][build-md] `## Final test-run gate` + `## Floor verification`; role delta:
[`worker-1.md`][worker-1] `## Final test-run gate`. Run at `HEAD = d3b91c8d`.

**HEAD moved under this gate.** The plan's pre-flight recorded `d3b91c8d`; this session opened with
a context snapshot naming `301bf450`. `d3b91c8d` is now HEAD and it is the concurrent `spec-050`
session's commit. `git show --stat d3b91c8d` names sixteen files and **none of them is one of this
cycle's seven**, so every diff figure below is HEAD-relative and nothing of this cycle's was
swallowed by it.

---

## Concurrency statement, first, because it changes how every command below reads

A concurrent maintainer session is mid-flight on `spec-050` with uncommitted production code in this
same tree. Every gate command is repo-wide, so a failure is not this cycle's until it has been
attributed by **diff content** ([`START.md`][start]: attribute dirty files by diff content, not by
"files my task touched").

**No `git stash`, `git checkout`, `git restore` or `git worktree` ran in this pass**, for any reason
including verification ([`BUILD.md`][build-md] `## Claims are proven mechanically`). Every HEAD
reference was `git show HEAD:<path>` written to a scratch path **outside** the repository. **No ruff
command ran in write mode**: `--check` only, never `--fix`, never a bare `.` under a writing flag.
Nothing of the concurrent session's was fixed, reverted or tidied ([`AGENTS.md`][agents] rule 34).

---

## Gate commands

| # | Command | Result |
|---|---|---|
| 1 | `uv run pytest --no-cov` | **2 failed, 7675 passed, 40 skipped** (64.69s). Both failures attributed to the concurrent session below. **0 failures in this cycle's scope.** |
| 2 | `uv run python examples/fakeshop/manage.py check` | **Pass** — `System check identified no issues (0 silenced).` exit 0 |
| 3 | `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` | **Pass** — `No changes detected`, exit 0 |
| 4a | `uv run ruff format --check .` | **Pass** — `445 files already formatted`, exit 0 |
| 4b | `uv run ruff check .` | **Pass** — `All checks passed!`, exit 0 |
| 4c | `git diff --check` | **Pass** — no output, exit 0 |
| 5 | Floor verification | **`No floor-verification scope declared.`** Declaration re-confirmed against the final diff; see below. |

No `--cov*` flag was passed anywhere. `--no-cov` is required because `pytest.ini`'s `addopts`
auto-applies `--cov` ([`BUILD.md`][build-md] `## Coverage is the maintainer's gate, not a worker's
tool`). No line coverage was inspected or asserted at any point in this pass.

### 1. `uv run pytest --no-cov`

```text
============ 2 failed, 7675 passed, 40 skipped in 64.69s (0:01:04) =============

FAILED examples/fakeshop/test_query/test_list_field_api.py::test_branches_omitted_and_null_arguments_match_the_legacy_reference
FAILED examples/fakeshop/test_query/test_list_field_api.py::test_holder_branches_combined_legacy_branch_matches_the_legacy_reference
```

**Both are the concurrent `spec-050` session's, and the attribution is mechanical rather than
circumstantial.**

The decisive evidence is that **neither node id exists at HEAD**. `git show
HEAD:examples/fakeshop/test_query/test_list_field_api.py` into a scratch path outside the repo, then
grep: **0** occurrences of either name; the worktree copy has **2**. Both rows were added by the
concurrent session's uncommitted diff (`git diff --numstat` on that file: 610 added / 108 removed,
alongside `list_field.py` 138/…, `orders/sets.py` 152/…, `utils/querysets.py` 95/…). A row that does
not exist at HEAD cannot be a regression of committed code, and it is in a file on no cohort's
writable list this cycle.

What each one reports, read rather than assumed:

- `…::test_branches_omitted_and_null_arguments_match_the_legacy_reference` fails at its own
  `assert sql == legacy_sql` on the `shipped omitted` label: the `DjangoListField` path emits
  `SELECT "library_branch"."id", "library_branch"."name"` where the test-local legacy oracle emits
  the same with `"library_branch"."city"` appended. That is an `only()`-projection difference on the
  list-field path — `django_strawberry_framework/list_field.py`, dirty from that session.
- `…::test_holder_branches_combined_legacy_branch_matches_the_legacy_reference` fails with
  `django.urls.exceptions.NoReverseMatch: 'djdt' is not a registered namespace`, raised out of that
  test module's own `_post_sync` helper at `:90` — a debug-toolbar URLconf the test's local
  `urlconf = 'test_list_field_api'` does not carry.

**Neither is parallel-run pollution.** Re-run alone, `-n0`, both still fail identically:
`uv run pytest -n0 --no-cov -q -q <the two node ids>` → `2 failed in 2.41s`, same two assertions.
So the selection is not what produces them.

**This cycle's own scope is green inside the same sweep.** `PASSED` rows matching
`tests/auth/` or `examples/fakeshop/test_query/test_auth_api.py`: **216**; `FAILED`/`ERROR` rows
matching the same: **0**. 216 is the figure every pass since Slice 6 has recorded, unchanged.

**Escalated to the maintainer, not fixed and not routed.** Per [`BUILD.md`][build-md] `## Claims are
proven mechanically`, a runtime claim about a tree a concurrent session is writing is not
worker-verifiable in the direction of "was it already broken" — that needs a clean checkout only the
maintainer can produce. What *is* verifiable and is recorded above: the failing node ids, the two
assertions, the HEAD absence of both rows, and the fact that neither the failing test file nor the
production file its first assertion exercises appears in this cycle's diff. **Nothing was reverted
or repaired.**

### 2-3. Django's own consistency checks

```shell
$ uv run python examples/fakeshop/manage.py check
System check identified no issues (0 silenced).                              (exit 0)

$ uv run python examples/fakeshop/manage.py makemigrations --check --dry-run
No changes detected                                                          (exit 0)
```

`examples/fakeshop/db.sqlite3` and `docs/GLOSSARY.md` are dirty from the concurrent session, so a
model-drift signal here could have been theirs. **There is none** — no drift to attribute in either
direction.

### 4. Lint / format / whitespace, all read-only

```shell
$ uv run ruff format --check .
445 files already formatted                                                  (exit 0)

$ uv run ruff check .
All checks passed!                                                           (exit 0)

$ git diff --check
                                                                             (exit 0, no output)
```

`git diff --check` reads the **whole** tree, the concurrent session's twenty-odd dirty files
included, and reports **zero** whitespace errors and zero conflict markers anywhere. Nothing to
attribute; the plan's `## Pre-flight` baseline exceptions (step 3's deliberately-skipped artifact
reset, step 5's scoped scratch clear, and the mid-cycle-updated `Baseline-dirty out-of-scope files`
line) are **not needed** — no exception is being claimed for any of the three commands.

The one `ruff format` warning (`COM812` may conflict with the formatter) is standing repo
configuration, emitted on every invocation, not a finding of this gate.

### 5. Floor verification

**`No floor-verification scope declared.`** The reason, in one line: this cycle changed no
production behaviour — its only three package edits are comments and docstrings, proved executable-
token identical to HEAD — so there is no version-dependent Django / Strawberry / Channels seam for a
floor run to exercise.

The plan declares `Floor-verification scope: none by default`, conditioned on "a slice that lands a
code fix touching the Django session / auth / Channels seam re-declares its own focused floor
scope". Exactly one slice landed a package edit, and `### Slice 6 declarations` re-declares
**`none`** on the recorded ground that no production behaviour changes. **Confirmed still true
against the final diff, not accepted from the declaration**, with the inverse proof a comment-only
edit owes ([`START.md`][start] `## Instruments that lie`: a docstring token cannot move a
docstring-stripped digest, so the proof runs the other way):

```shell
$ uv run python docs/builder/temp-tests/040-final/ast_identity.py \
      django_strawberry_framework/auth/mutations.py \
      django_strawberry_framework/mutations/resolvers.py \
      django_strawberry_framework/mutations/sets.py
IDENTICAL  django_strawberry_framework/auth/mutations.py
IDENTICAL  django_strawberry_framework/mutations/resolvers.py
IDENTICAL  django_strawberry_framework/mutations/sets.py
control (x = 1 vs x = 2 must be False): False                                (exit 0)
```

The instrument parses each path's worktree text and its `git show HEAD:<path>` text, deletes every
module / class / function docstring from both, and compares `ast.dump`. A comment cannot appear in
an AST at all, so identity after docstring removal is identity of the executable tokens.

**Two controls, because a comparison that cannot fail is a passing proof that measured nothing.** An
inline positive control (`x = 1` vs `x = 2` must compare unequal) is printed with every run, and the
same instrument over the three files the *concurrent* session is editing returns
`DIVERGES / DIVERGES / DIVERGES` on `list_field.py`, `orders/sets.py`, `utils/querysets.py` — real
behaviour changes, correctly detected. The three `IDENTICAL` rows are therefore a measurement.

**No floor venv was built.** [`BUILD.md`][build-md] `## Floor verification` names the floor as Django
5.2.16 / Python 3.10 / strawberry-graphql 0.316.0, and building one for a diff with no executable
delta would produce a number about nothing. The declaration is not falsified, so nothing blocks
`final-accepted` on this item.

---

## Verification, before the status was set

```shell
$ uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-040-auth_mutations-0_0_13.md
OK: 30 terms - all have glossary entries and at least one spec link.         (exit 0)

$ uv run python scripts/check_citations.py --check
OK: 979 citations resolve (814 in 442 .py files, 165 in KANBAN.md).          (exit 0)
```

`check_citations.py` runs whole-tree and so reads the concurrent session's dirty `.py` files too. It
is green at the same **979** that Slice 6, both integration runs and this gate all record, so **no
citation moved and there is nothing of the other cycle's to attribute here**. Note what the gate can
and cannot see: it resolves `path::Symbol` only, so the `path #"substring"` and label-vocabulary
citations in deferred entries 3, 4 and 5 below are outside its corpus by construction — their green
is not evidence about those.

### In-page anchors and the markdown link convention

`docs/builder/temp-tests/040-final/link_audit.py`, with slugs taken from the **raw** heading line
(the GitHub rule drops backticks and keeps their contents, so slugging code-span-stripped text
invents anchors that do not exist) and the ten group headers matched only **inside** the bottom
`<!-- LINK DEFINITIONS -->` block (a file whose prose quotes a group header otherwise false-alarms):

| File | Unique heading slugs | In-page uses | Unresolved | Ref uses / defs | Undefined | Unused | Def paths missing | Ten headers, in order |
|---|---|---|---|---|---|---|---|---|
| `docs/SPECS/spec-040-auth_mutations-0_0_13.md` | 35 | 165 | **0** | 96 / 96 | 0 | 0 | 0 | yes |
| `docs/SPECS/appx/…-rationale.md` | 33 | 77 | **0** | 60 / 60 | 0 | 0 | 0 | yes |
| `docs/builder/bld-040-final.md` (this file) | 21 | 0 | **0** | 7 / 7 | 0 | 0 | 0 | yes |

Instrument controlled: a copy of the spec with one bogus in-page anchor and one bogus reference
label appended reports `unresolved: ['no-such-heading']` and `undefined: ['no-such-label']`, so the
zeros are measurements rather than a sweep that ran on nothing. This table's heading figures count
**unique slugs**, where the integration pass counted heading **lines** (34 / 66); different
instruments over the same files, and it is the zeros that both agree on. This file's own row is
measured **post-write**, because a live count of a population the pass is itself editing is the
self-falsifying-instrument shape.

### Pre-commit

`uvx pre-commit run --files` over every file this pass writes, each path typed literally rather than
through a shell variable ([`START.md`][start] `## Instruments that lie`: zsh word-splitting turns a
sweep into one iteration and prints nothing). Run twice, **no rewrite on the second run** — the
`source-layout` hook, which owns the `.md` link-definition scaffold, left both files byte-identical
across the two runs, `md5` compared rather than asserted.

---

## `### Deferred work catalog`

Worker 1 is this catalog's only author. Its input is
[`bld-040-integration.md`][bld-040-integration] `### 6`, **12 entries in two blocks**. Every figure
below was **re-measured at this gate with its population named**, not copied — two inherited figures
in this cycle were already corrected once by exactly that discipline, and one entry sits in a file
the concurrent session is editing right now.

**Block A is deferred work. Block B is closed with a recorded decision, or is a correction of
record: the gate carries these so nothing downstream re-opens them.**

### A. Deferred

1. **The subprocess-isolation idiom — `subprocess.run([sys.executable, …])` spelled inline in 8 test
   files, 8 call sites.** Source: Slice 6 plan `### Out-of-scope observations`; Slice 6 Worker 1
   pass-2 item 4; integration `### Ruling 3`. No licensing spec line — out-of-spec DRY.
   **Re-measured, and the first instrument was wrong:** a first-argument match on
   `subprocess.run(\s*\[\s*sys\.executable` returns **7** files, because `tests/base/test_init.py`
   builds the argv into a `cmd` local and calls `subprocess.run(cmd, …)` — precisely the AST/regex
   blind spot this cycle's own memory names. Re-run over the `sys.executable` token instead:
   **9 occurrences in 8 files**, of which one (`tests/test_scalars.py`) is a docstring mention, so
   **8 call sites in 8 files** — `tests/auth/test_mutations.py`, `tests/auth/test_sessions.py`,
   `tests/base/test_init.py`, `tests/filters/test_finalizer.py`, `tests/filters/test_sets.py`,
   `tests/orders/test_inputs.py`, `tests/rest_framework/test_soft_dependency.py`,
   `tests/test_scalars.py`. Control, files using `subprocess.run(` at all: **10**; the two extras
   (`tests/test_bug_hunt.py`, `tests/test_ci_governance.py`) invoke `git`, not an interpreter, and
   were read at source to confirm it. The integration pass's figure of 8 stands. Deferred because
   five directories are involved and the shared home is a repo-level `tests/` decision (which
   conftest; what the contract is for a soft-dependency probe versus an import-isolation probe
   versus a warnings probe) belonging to a DRY cycle over the whole test tree. This build already
   collapsed the two copies inside its own file into `::_auth_free_subprocess`.
2. **`docs/GLOSSARY.md`'s auth entry repeats the exact defect this cycle fixed in the spec.**
   Source: Slice 3 `### Notes for Worker 1` `F1`; Slice 4 `F4`; integration `D1`. Licensing line:
   the plan's `### Scope fence (maintainer-set)`, which puts `docs/GLOSSARY.md` out of scope.
   **Re-read at source this gate — still live**, at `docs/GLOSSARY.md:329`: "the privilege columns
   (`is_staff` / `is_superuser` / `groups` / `user_permissions`) are unreachable by construction" —
   the retired unqualified framing **and** the four-of-five enumeration with `is_active` absent. The
   fix is the two-part one spec edit 1 made, applied to the `GlossaryTerm` body via the ORM and then
   `scripts/build_glossary_md.py`. **Note for whoever takes it, re-verified at this gate:** the file
   is dirty right now from the concurrent session with **exactly one** hunk, and it is unrelated —
   the `apps.py` entry's three-appliers → four-appliers rewrite adding `_graphql_core_patches`
   (`git diff --stat`: 1 insertion, 1 deletion). The glossary edit lands **on top** of that, never
   by regenerating over it. **For the maintainer.**
3. **`spec-042 Revision N` citations in `tests/middleware/test_debug_toolbar.py` — 5 occurrences**,
   at `:21 :111 :475 :509 :523`. Source: Slice 6 plan `### Out-of-scope observations`. Re-measured
   as occurrences this gate: `grep -o 'spec-042 Revision'` = **5**, at exactly those five lines. Same
   defect class as `F2` (a label vocabulary a rationale extraction stranded), a different spec's
   population and a different owner. Invisible to `check_citations.py`, which is `path::Symbol` only.
   **For the maintainer.**
4. **Bug-hunt round provenance in `tests/auth/test_sessions.py` — 2 occurrences**, at `:465` and
   `:720`. Source: same. [`START.md`][start] `## Style Rio cares about` bans round provenance in
   code; the file was on no cohort's writable list and cites no spec, so both sit outside `F2`'s
   population. **Re-measured, and the first sweep returned zero:** the spelling is
   `(hunt 0_0_14)` and `(hunt 0_0_14 rev)`, which a `bug[- ]hunt|round [0-9]` vocabulary misses
   entirely — a sample read as a census, caught only by widening to the bare `hunt` token. The
   figure of 2 is confirmed; the file is clean in the tree. Pass 1 had already corrected this
   inherited figure from 1 to 2, the dominant-residual shape where a one-site figure closes a
   finding with half of it live. **For the maintainer.**
5. **`Revision N P<n>` citations in `examples/fakeshop/test_query/test_library_api.py` — 5
   occurrences**, at `:2749 :3830 :3885 :4026 :4041`. Source: Slice 6 plan `### Out-of-scope
   observations`. Re-measured as occurrences this gate: **5**, at exactly those lines. That file
   belongs to the concurrently active `spec-050` cycle and must not be touched by this one
   ([`AGENTS.md`][agents] rule 34). **For the maintainer / that cycle.**
6. **`## Definition of done` item 6's coverage clause is structurally unverifiable by any worker.**
   Source: Slice 4 `### Spec changes made`, the one un-ticked box of that slice. Licensing line:
   [`BUILD.md`][build-md] `## Coverage is the maintainer's gate, not a worker's tool`. Re-read at
   source this gate: item 6 opens "The full suite is green at the 100% coverage gate
   (`fail_under = 100`)" — no worker may measure that. **Its other half is discharged**, and that was
   verified rather than inherited: the clause "the three deliberate non-reuse points carry their
   source comment" now holds — `django_strawberry_framework/auth/mutations.py` carries `D-N1` at
   `:616`, `D-N2` at `:1109` and Slice 6's `D-N3` at `:1197`, where the pre-cycle count was two of
   three. The coverage half is the maintainer's gate by construction.
7. **Cosmetic, unfixable in place: `docs/builder/bld-040-slice-6-code_remediation.md:888` carries
   `scripts/prove_failability.py`'s own `<fill in …>` explanatory line** inside a prior
   `### Failability proofs` block. Source: Slice 6 Worker 1 passes 1 and 2. Re-read this gate — line
   888 is the tool's instruction sentence ("Every `<fill in ...>` above is a judgement no tool can
   make…"), and the file carries **0** unfilled placeholders: `grep -c 'why 0: <fill in'` = **0**,
   because no entry is zero-row. [`ARTIFACT.md`][artifact-md] forbids editing a prior entry, so it
   stays. **For the maintainer's awareness only.**

### B. Closed with a recorded decision, or a correction of record — do not re-open

8. **The `_declare_group_type` / `_declare_user_type` per-file pairs are accepted duplication, not
   deferred.** Source: integration `### Ruling 1`, four recorded grounds. The condition that would
   change the answer is recorded with it: a third caller, or a decision to widen
   `tests/auth/_helpers.py`'s stated "plain (non-fixture) helpers" contract to registry-mutating
   declarations. Re-verified this gate: `_declare_group_type` is defined at exactly **2** sites
   (`tests/auth/test_mutations.py:160`, `tests/auth/test_queries.py:86`), one per file, and neither
   `tests/auth/_helpers.py` nor `tests/auth/conftest.py` is dirty.
9. **The `_LOGOUT_Q` tally: two prior entries in the integration artifact carry `11` → `14`; the
   correct figure is `12` → `15`.** Sources: integration `### Ruling 2`, its `## Build report
   (Worker 2)` before/after table, Worker 3 `L1`, and pass 1's `### 1. Disposition …`. Licensing
   line: [`ARTIFACT.md`][artifact-md] "never edit prior entries". `11` is the reader count at HEAD;
   Slice 6 added one reader before the consolidation loop ran. **Re-measured this gate, occurrences
   not lines, both trees named:** `git show HEAD:tests/auth/test_mutations.py` → **12** occurrences
   = 11 readers + 1 store, 0 prose; the worktree → **17** occurrences = **15 readers + 1 store + 1
   prose mention** (the `:2513` comment naming the document, which does not exist at HEAD). 12 → 15
   readers confirmed.
10. **The line tally: integration `## Build report (Worker 2, pass 2)` `### Notes for Worker 3`
    carries "three added lines and two removed"; the correct figure is 4 added and 2 removed.**
    Sources: that section, Worker 3 `L5`, integration `#### L5`. Same licensing line as entry 9.
    Nothing downstream reads the figure.
11. **The working-tree attribution in integration `## Review (Worker 3, pass 2)` `### Confirming the
    fence held` is wrong for two files.** `django_strawberry_framework/mutations/sets.py` and
    `django_strawberry_framework/mutations/resolvers.py` are attributed there to the concurrent
    `spec-050` session; they are **this cycle's** Slice 6 `F3` docstring fixes. Same licensing line
    as entry 9. **Re-proved at this gate from diff content, not inherited:** every hunk in both files
    is `F2` (the `spec-040 Revision-7 marker fix` attribution removed) or `F3` (`_bind_mutation` /
    `_bind_form_mutation` → the live `bind_mutations` / `bind_form_mutations` /
    `bind_write_declarations`) — there is no `spec-050`-shaped hunk in either. **This is the one
    correction with a consequence for the commit:** a stager working from that superseded paragraph
    would drop two landed fixes. The staging list is `## The exact file list to commit` below.
12. **`tests/auth/test_mutations.py:1253` binds `model` where the file's other three user-model
    locals and the production parameter spell it `user_model` (`L4`).** Accepted by integration
    `#### L4`, with its origin — the integration artifact's **own pinned text**, so the divergence is
    Worker 1's and not the builder's — and its condition recorded: **if any later pass opens this
    file for another reason, rename it to `user_model`.** Re-verified this gate: `:1253` reads
    `model = _privilege_required_user()`; the three siblings at `:881`, `:950` and `:1269` read
    `user_model = …`. Not deferred work in its own right; no loop is owed for it.

---

## What the cycle delivered, against what it was commissioned to do

The maintainer commissioned three things. All three landed.

1. **The rationale extraction that never ran.** `spec-040` was the one archived spec of its
   generation with a `-terms.csv` companion and no `-rationale.md`. It has one now:
   `docs/SPECS/appx/spec-040-auth_mutations-0_0_13-rationale.md`, 1,949 lines, keyed decision by
   decision, carrying 16 `**No longer claims:**` retractions. Those retractions turned out to be the
   cycle's most productive instrument: sweeping the spec against them is what found the largest
   residual in the integration pass.
2. **A conformance audit of the shipped code against every normative claim in the spec** — the
   maintainer's stated goal was to make sure the code did not deviate or drop, or that a planned
   feature was not simply forgotten. **327 graded rows across five audit slices produced exactly one
   code gap**, and it was a missing source comment. 327 re-derived here from the four matrices at
   source rather than carried: Slice 2's **63** + Slice 3's **91** + Slice 4's **122** + Slice 5's
   **51** = **327**; the single `CODE-GAP` is Slice 4's `CG-1`. **The `0.0.13` build dropped nothing
   it planned.** Decision 6's registration pipeline was graded step by step at the release commit and
   every step it specifies is present, down to the narrowest — the four-tuple decode hand-off, the
   provided-marker exclusion seam, `set_password` before `full_clean`, and the
   plaintext-never-persisted assertion on both paths.
3. **The spec reconciled to the current contract**, with every explanation in the companion and none
   in the spec. Divergence ran one direction almost everywhere: the code moved forward after release
   and the spec did not. Two exceptions are worth the maintainer's attention because they were not
   drift at all — five divergences were **false on their own date**, verified identical at
   `3a294082 Release 0.0.13` (Decision 6's three-way kwarg-partition claim and Decision 7's
   single-sited-dispatcher claim among them). Decision 11 was the largest: it made nine claims and
   **eight were false**, two of them in the heading, so the heading was renamed and all 16 in-page
   anchor uses, both reference labels and the companion's mirrored heading were swept with it.

And **seven findings remediated in `.py`** by Slice 6 and the integration consolidation: `CG-1`'s
scoped `D-N3` comment, four `TEST-GAP` closures, and the two stranded-citation findings (`F2`'s
`spec-040 Revision N` citations, `F3`'s `_bind_mutation` / `_bind_form_mutation` docstring names).

### Zero production behaviour changed

Every package edit this cycle made is a comment or a docstring, and all three files are
**executable-token identical to HEAD** — proved above with a positive control and a negative control,
not asserted. The behavioural change is entirely on the test side: **seven new collected node ids
against one retired**, closing the four test gaps the audit found.

That figure, re-measured at this gate by AST over module-level `test_*` functions in
`git show HEAD:<path>` against the worktree: `tests/auth/test_mutations.py` **97 → 101**
(`test_sessionless_login_…` / `test_sessionless_logout_raises_the_configuration_error_naming_both_middlewares`,
`test_register_mutation_rejects_a_protected_required_field_at_the_factory_call`,
`test_an_unplanned_relation_under_login_node_is_strictness_visible`,
`test_finalize_in_an_auth_free_process_never_imports_the_auth_subsystem` added;
`test_sessionless_request_surfaces_djangos_own_error` retired) and `tests/auth/test_queries.py`
**21 → 22** (`test_an_unplanned_relation_under_me_is_strictness_visible`). **Six new functions and
one retired**, which is **seven** node ids once the finalize row's `[finalize]` / `[schema]`
parametrization is counted.

---

## The exact file list to commit

Attribution is by **diff content** throughout, and it uses the **corrected** attribution from
[`bld-040-integration.md`][bld-040-integration] `### 7` — **not** the superseded
`### Confirming the fence held` paragraph, which misfiled two of these files (deferred entry 11).

### This cycle's — tracked, modified: 7 files

`git diff --numstat`, measured at this gate against `HEAD = d3b91c8d`:

| File | Ins / Del | The change, in one line |
|---|---|---|
| `docs/SPECS/spec-040-auth_mutations-0_0_13.md` | 693 / 876 | The reconciliation: the deliberative layer cut to the companion, all 12 Decisions re-graded against shipped code, the five cross-home divergences closed |
| `django_strawberry_framework/auth/mutations.py` | 11 / 4 | **Comment and docstring only** — `CG-1`'s scoped `D-N3` comment plus the `F2` citation restatements |
| `django_strawberry_framework/mutations/resolvers.py` | 6 / 6 | **Docstring only** — `F2` and `F3`. **This cycle's, not the concurrent session's** |
| `django_strawberry_framework/mutations/sets.py` | 7 / 7 | **Docstring only** — the `F3` rename sweep plus `build_input`'s real caller. **This cycle's, not the concurrent session's** |
| `tests/auth/test_mutations.py` | 275 / 64 | The four `TEST-GAP` closures, the three DRY consolidations, the two pinned Low edits |
| `tests/auth/test_queries.py` | 86 / 7 | `TG-3`'s `me` twin: a `groups`-exposing `_declare_user_type` seam, a `Group` type, the strictness-visible row |
| `examples/fakeshop/test_query/test_auth_api.py` | 6 / 6 | **Docstring only** — two `F2` citation restatements |

**Totals, measured: 7 files, 1,084 insertions / 970 deletions.**

> **A fifth unmeasured stated count, found by this gate.**
> [`bld-040-integration.md`][bld-040-integration] `### 7` heads that same table
> "**Tracked, modified — 7 files, 391 insertions / 94 deletions**". The per-file rows below it are
> correct and sum to **1,084 / 970**; `391 / 94` is the sum of the **six non-spec rows**
> (11+6+7+275+86+6 and 4+6+7+64+7+6), with the 693 / 876 spec row omitted while the sentence still
> says "7 files". Right in every digit, wrong in its subject — [`START.md`][start]'s shape exactly,
> and the fourth time this cycle a supporting tally attached to a conclusion that holds at any value
> reached a later pass unchallenged. **Nothing downstream depends on it**; the per-file table, which
> is what a stager reads, was right all along.

### This cycle's — untracked, new

- `docs/SPECS/appx/spec-040-auth_mutations-0_0_13-rationale.md` — 1,949 lines. **Tracked-and-committed
  material, not scratch** ([`worker-1.md`][worker-1] `### Performing the rationale move`, rule 5).
- `docs/builder/build-040-auth_mutations-0_0_13.md` — the plan, **543** lines. (The integration
  artifact recorded 514; Worker 0 appended slice-log entries after that reading, so the figure is
  a live count of a file still being written, not a discrepancy.)
- `docs/builder/bld-040-slice-1-rationale_extraction.md` (387),
  `bld-040-slice-2-audit_substrate_login_logout.md` (577),
  `bld-040-slice-3-audit_register_current_user.md` (849),
  `bld-040-slice-4-audit_obligations_edges_tests.md` (1,086),
  `bld-040-slice-5-later_spec_reconciliation.md` (539),
  `bld-040-slice-6-code_remediation.md` (2,980), `bld-040-integration.md` (3,356), and
  **this file**.

Not in any of the above and never to be staged: `docs/builder/worker-memory/` and
`docs/builder/temp-tests/` are gitignored cycle scratch.

### NOT this cycle's — the concurrent `spec-050` session's, untouched

Measured at the close of this pass; **this set has moved four times across the cycle's passes**, so
it is a snapshot and not an invariant.

`django_strawberry_framework/list_field.py`, `django_strawberry_framework/orders/sets.py`,
`django_strawberry_framework/utils/querysets.py`, `docs/GLOSSARY.md`, `docs/feedback.md`,
`docs/spec-050-list_field_arguments-0_0_15.md`, `docs/builder/bld-final.md`,
`docs/builder/bld-slice-3-sql_and_unit_contracts.md`, `examples/fakeshop/db.sqlite3`,
`examples/fakeshop/test_query/test_list_field_api.py`,
`examples/fakeshop/test_query/test_list_field_async_api.py`,
`examples/fakeshop/test_query/test_multi_db.py`, `tests/orders/test_sets.py`,
`tests/test_list_field.py`, `tests/utils/test_querysets.py`.

**Nothing of theirs was reverted, checked out, stashed, tidied or staged.** Note that
`docs/builder/bld-final.md` — theirs — and `docs/builder/bld-040-final.md` — this one — are
different files; the `040` infix is what separates every path this cycle created from theirs.

---

## What is deliberately NOT in the diff

The maintainer's scope fence was **spec files and `.py` files only**. These were not written, and
that is a fence, not an oversight:

`KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md`, `docs/TREE.md`, `docs/README.md`, `README.md`,
`TODAY.md`, `GOAL.md`, `CHANGELOG.md`, the kanban DB (`examples/fakeshop/db.sqlite3`), and the
closeout agentflow ([`BUILD.md`][build-md] `## Closeout`).

**The one known consequence, stated as a maintainer item rather than left implicit:**
`docs/GLOSSARY.md`'s auth entry (line 329) still carries the framing the spec retired this cycle —
the unqualified "unreachable by construction" — and still omits `is_active` from the refused
auto-expose list, naming four of the five protected columns. It is deferred entry 2 above, with its
fix procedure and its dirty-file hazard recorded. The glossary is DB-backed, so the fix is an ORM
edit to the `GlossaryTerm` body followed by `scripts/build_glossary_md.py` — never a hand-edit of
the rendered file, and never a regenerate over the concurrent session's live hunk.

The same defect was found **inside the spec** by the integration pass, at `## Goals`, `### Decision
8` and `## Definition of done` item 4, where no slice's partition covered it. Those three are fixed
and in the diff. The glossary copy is the one that is out of fence.

---

## Final status

`final-accepted`.

Every gate command passes except `pytest`, whose two failures are attributed with mechanical
evidence to the concurrent `spec-050` session — **neither failing node id exists at HEAD**, both live
in that session's uncommitted file, both reproduce in isolation under `-n0`, and neither the test
file nor the production file the first one exercises is in this cycle's diff. This cycle owns no
failure: **216 auth rows passed and 0 failed** inside the same sweep. `manage.py check`,
`makemigrations --check`, `ruff format --check`, `ruff check` and `git diff --check` are all clean
repo-wide, so no pre-flight baseline exception is being claimed. Floor verification is `none`, its
declaration re-confirmed against the final diff by a controlled AST-identity proof rather than
accepted from the plan. `check_spec_glossary.py` exits 0 at 30 terms; `check_citations.py` exits 0
at the unchanged 979; anchors and the link convention hold at zero unresolved and zero undefined
across the spec, the companion and this artifact; pre-commit passes with no rewrite on a second run.

The failing `spec-050` rows are **escalated to the maintainer**, not routed and not repaired.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../AGENTS.md
[start]: ../../START.md

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->
[artifact-md]: ARTIFACT.md
[bld-040-integration]: bld-040-integration.md
[build-040]: build-040-auth_mutations-0_0_13.md
[build-md]: BUILD.md
[worker-1]: worker-1.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
