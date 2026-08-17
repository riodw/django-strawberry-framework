# Build: Round 2 — the `_resolve_field_map` dual-contract cross-reference (F8)

Spec reference: `docs/SPECS/spec-016-fieldmeta_consolidation-0_0_6.md` (`### Bounded exceptions to the single-source rule`, the walker's-dual-contract bullet)
Build plan: `docs/builder/build-016-fieldmeta_consolidation-0_0_6.md` (`### R2 finding — the one source-level defect`)
Status: final-accepted

**Full-cycle round** per the build plan's `## Artifact list`: Worker 1 plan -> Worker 2 build -> Worker 3 review -> Worker 1 final verification. This is the only round in the cycle that dispatches Worker 2, and its entire scope is one docstring line in one clean file.

## Plan (Worker 1)

### Spec status-line re-verification

Performed at spawn per `docs/builder/worker-1.md` `## Spec status-line re-verification (every Worker 1 spawn)`. Spec lines 1-7 read: title, `Target release: 0.0.6 (per KANBAN.md card DONE-016-0.0.6)`, `Status: shipped.`, `Owner: package maintainer.`, and the one-line rationale-companion pointer. **All five still describe the build's current state**; R1 rewrote them this cycle and R2 changes no contract, so no edit is owed and none was made. No predecessor doc this build deleted is referenced.

One spec-body imprecision was found while reading the contract this round's docstring must match. It does not block R2 and is **not** edited in this pass — see `### Notes for Worker 1 (spec reconciliation)`.

### Baseline, HEAD, and drift — measured this pass

| Fact | R1's reading | This pass | Note |
|---|---|---|---|
| `HEAD` | `ded4b00c364c5938035d80dd6d38b1bef40a441c` | `ab821ae07e5c9b581c2a644a81e94c890c8790cd` | **Drift again, and again not new content** |
| tree object | `7debb73f3b03e58ca197904756bed5d59753e549` | `7debb73f3b03e58ca197904756bed5d59753e549` | **identical** — every R1 and plan-time file reading stays valid |
| parent | `d28fbc0a63613ed0ca0da4c784a670c499067b6a` | `1dafe4191eb819a286f6c46b69f718ae05193586` | changed: a concurrent session rebased the branch under us |
| subject | `refactor: single-site the duplicated class-label, bind, and fetch seams` | same | same |
| committer date | `2026-08-17 15:25:18 -0400` | `2026-08-17 15:25:18 -0400` | same |
| `git status --short \| wc -l` | 56 at R1's pass end | 56 | see below |

Commands: `git rev-parse HEAD`; `git log -1 --format='%H %T %P %ci %s'`; `git log -3 --format='%h %T %s'`; `git merge-base --is-ancestor d28fbc0a HEAD` -> **NO**; `git merge-base --is-ancestor ded4b00c HEAD` -> **NO**.

**Read the tree object, never the hash.** Both of R1's recorded hashes are now un-reachable — this time the *parent* moved, not only the committer date, so the rewrite is a rebase rather than an amend. The top commit's tree is nonetheless byte-identical to R1's (`7debb73f`), which is the fact that matters: **no file this round reads has changed since the plan was written.** `git log A..B` and `merge-base --is-ancestor` both mis-report this as new work; only `%T` acquits it. Worker 2 re-derives `HEAD` at its own spawn and applies the same test: if `%T` is still `7debb73f` the readings below hold; if `%T` differs, re-measure `### Step 1` before editing.

**Working tree at this pass: 56 paths, of which 5 are this cycle's** — `?? docs/builder/build-016-…` (Worker 0's plan), `M docs/SPECS/spec-016-…md` and `?? docs/SPECS/appx/spec-016-…-rationale.md` (R1's, uncommitted), `?? docs/builder/bld-016-r1-…md` (R1's), and this artifact. The remaining **51** are the concurrent sessions' baseline-dirty population the build plan enumerates (R1 measured 52; the untracked `docs/review/rev-*.md` bucket moves while a concurrent review cycle emits into it, so the number drifting is expected and is not evidence of build output). Every one of them falls inside a bucket the plan declared out of scope.

`git stash`, `git checkout`, `git restore`, and `git worktree` were used **nowhere** in this pass. Every source reading was taken read-only through `git show HEAD:<path>` into a scratch path outside the repository, or through `git grep … HEAD`, or read from a file verified byte-identical to `HEAD`.

**`optimizer/walker.py` is clean at baseline — verified two ways, and Worker 2 must verify it again:**

```shell
git status --short -- django_strawberry_framework/optimizer/walker.py   # prints nothing
git show HEAD:django_strawberry_framework/optimizer/walker.py > <scratch outside repo>/walker.py
cmp <scratch outside repo>/walker.py django_strawberry_framework/optimizer/walker.py   # exit 0
```

Both passed this pass (`cmp` exit 0). If either fails at Worker 2's spawn, a concurrent session has taken the file: **stop and report**, do not edit and do not revert.

### DRY analysis

**Helper inventory checked.** No package-wide AST inventory was regenerated, and deliberately so: `docs/shadow/helper-inventory.md` already exists on disk (213,854 bytes, mtime 2026-08-16 04:35) as a **concurrent session's** output, and this cycle does not overwrite another session's shadow files (build plan, pre-flight step 5 deviation). It was read read-only and grepped for this round's shapes — `_resolve_field_map`, `_field_meta_for_resolver`, `finalize_django_types`, `_resolve_optimizer_hints` — which appear at `:956`, `:1520`, `:1448`, `:958`, each under its own module heading, confirming the two cross-referenced symbols live in different packages. It is a day stale against a tree several concurrent sessions have edited, so it is **not** treated as current for any claim; every load-bearing fact below was measured directly against `HEAD`. The staleness is harmless here because **this round proposes no helper, constant, validation branch, coercion utility, or test helper, and adds no executable statement at all** — `docs/builder/worker-1.md` `### Package-wide helper inventory before helper planning` gates helper planning, and there is none to gate.

`scripts/review_inspect.py` was run for the target file, as `docs/builder/BUILD.md` `### When to run the helper during build` requires for any file under `optimizer/`:

```shell
uv run python scripts/review_inspect.py django_strawberry_framework/optimizer/walker.py --output-dir docs/shadow
```

It wrote `docs/shadow/django_strawberry_framework__optimizer__walker.overview.md` and `…stripped.py` (both this pass's own creations, so no concurrent output was clobbered). **Recorded limitation, because it matters for Worker 3:** the stripped file removes every `#` comment and replaces every string-literal token *including docstrings* with `...`, so the helper's output is structurally blind to this round's entire change surface. The overview is useful here for exactly one thing — it reports walker.py's two `TODO(spec-035)` anchors at `:462` and `:1129`, which belong to another card and **must not be disturbed** (the tree-wide sweep `grep -rEn 'TODO\(spec-016|TODO-(ALPHA|BETA|STABLE)-016'` returns nothing outside the build plan's own prose about the sweep, so this build stages no anchor of its own).

- **Existing patterns reused.** The replacement text is not invented: `django_strawberry_framework/optimizer/field_meta.py::FieldMeta._from_field_shape` (docstring, `field_meta.py:204`) already spells this exact symbol `types/resolvers.py::_field_meta_for_resolver`, and the reconciled spec's `### Bounded exceptions to the single-source rule` bullet uses the same spelling. R2 makes walker.py agree with the two places that were already right rather than choosing a third form. Measured: `grep -rn -o "types/resolvers.py::_field_meta_for_resolver" --include='*.py' django_strawberry_framework/` -> exactly one hit, `optimizer/field_meta.py:204`; `grep -rn -o "optimizer/resolvers.py::_field_meta_for_resolver"` -> exactly one hit, `optimizer/walker.py:313`.
- **New shared shape justified.** None. Nothing this round produces is reusable by another round.
- **Duplication risk avoided.** The live risk is a *third* spelling of one symbol reference entering the package. Prevented by fixing the replacement text verbatim in `### Step 2` below, leaving Worker 2 no wording discretion, and by pinning it to the measured precedent rather than to a style preference.

#### The existence challenge: is a prose "keep the two in sync" note the right shape at all?

`docs/builder/BUILD.md` DRY-FIRST requires this question be answered, not skipped. **Answer: yes, the note is the correct shape, and the two sites are not a duplication.** The reasoning, from the source read this pass:

- `optimizer/walker.py::_resolve_field_map` returns `tuple[type | None, Any | None, dict[str, Any]]`. On the fallback path the dict's values are **raw Django field objects** from `model._meta.get_fields()` — a different *type* from `FieldMeta` — and the docstring states that downstream `getattr(..., default)` reads are the ONLY reason the two shapes coexist safely.
- `types/resolvers.py::_field_meta_for_resolver` returns `FieldMeta`, unconditionally. Its fallbacks (`FieldMeta._from_field_shape(field, is_relation=True)` when the descriptor lacks `is_relation`, else `FieldMeta.from_django_field(field)`) produce a genuine `FieldMeta` observably identical to the canonical builder's on the same descriptor.

So what the two sites share is **one sentence of policy** — "the canonical definition may be unreachable, so a non-canonical path exists here" — and not a shape, a type, a branch ladder, or a body. There is nothing to extract: a helper factoring their commonality would factor a *statement*, which is what a cross-reference already is. The DRY-correct form for shared policy across two deliberately-different implementations is precisely a pointer at the other site, which is what the line does. The defect is that the pointer's address is wrong, not that the pointer exists.

**Could the duplication be closed instead of documented?** Only by making walker's fallback build `FieldMeta` objects and deleting the resolver fallbacks — and that is already a **recorded rejected alternative** in `docs/SPECS/appx/spec-016-fieldmeta_consolidation-0_0_6-rationale.md` `### ## Scope — "single source of truth" stated without its two bounded exceptions`, rejected on two grounds this round does not get to re-open: the walker's own docstring defers closure to a named future gate ("until the registry-coverage gate lands"), so closing it here pre-empts a scoped decision with a drive-by change; and it is production-code work in a cycle whose one authorized source edit is a docstring cross-reference. **Worker 2 is not authorized to touch either site's logic**, and Worker 3 must reject any diff that does.

If the answer ever changes, the condition that would change it is named: the registry-coverage gate landing, at which point walker's fallback disappears, the dual contract ends, and the cross-reference should be deleted rather than re-pointed.

### Boundary count, and the failability-proof answer

**Boundary count: zero.** Enumerated explicitly, because `docs/builder/worker-1.md` `### Boundary count is a split trigger` requires the count in writing even when the diff is one line: this round adds no guard, no cap, no rejection path, no validation branch, no gate, and no error message. No split trigger fires.

**Failability proof owed: none, and here is the reasoning against the rule rather than an assertion.** `docs/builder/BUILD.md` `### What needs a proof, and what does not` scopes the obligation to a **new boundary, guard, gate, or rejection path** — "anything whose job is to say 'no', hold an invariant, or fail closed" — and explicitly exempts "doc edits" and changes that move existing behavior. R2's diff changes ten characters inside a function docstring: `_resolve_field_map`'s executable body (`type_cls = …` / `definition = …` / `field_map = …` / `return …`, four statements) is untouched, so there is no boundary whose removal a mutation could measure. There is nothing to mutate that a test could observe, which is the definition of a change that owes no proof rather than one whose proof is inconvenient. Worker 2 writes `None; this pass introduced no new boundary.` under `### Failability proofs` and keeps the heading.

The adjacent proof rule that *would* apply — `docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on prose` — is discharged not by a failability loop but by the greps in `### Step 3`, which is why they are mandatory and their proof condition is stated exactly.

**Fail-open shapes: none introduced.** Recorded because `## Failability proofs` makes reading for the shape a plan-time duty. No clamp, `getattr` default, `or` fallback, bare `except`, or truthiness test enters the diff — the diff contains no expression at all.

### Hot-path declaration

**None**, copied from the build plan as written: `Hot-path declaration: **none.** … R2's single change is a docstring line — no executable statement changes, so no path gets slower or faster.` Worker 2 writes `Not applicable; plan declares no hot path.` under `### Hot-path budget`.

### Floor-verification scope

**None**, copied from the build plan as written: `Floor-verification scope: **none.** No round touches a Django / Strawberry / channels integration seam.` Floor facts quoted from `docs/builder/BUILD.md` `## Floor verification` so no pass restates them from memory: Django **5.2.16** on Python **3.10** with strawberry-graphql **0.316.0**; **the shared `.venv` is not the floor**. Worker 2 writes `Not applicable; plan declares floor-verification scope none.` under `### Floor verification`, and installs nothing into the shared `.venv`.

### Ownership partition

**None; sequential rounds**, copied from the build plan as written. R2 is the cycle's only round with a source file in its writable set and still runs in sequence after R1, because R1's reconciliation is what established the symbol vocabulary this fix must match.

### Writable files for Worker 2 — the complete list

Nothing outside this list may be created, edited, moved, staged, or reverted.

1. `django_strawberry_framework/optimizer/walker.py` — clean at baseline; **verify that is still true** with the two commands in `### Baseline, HEAD, and drift` before the first edit, and stop-and-report rather than editing if either fails.
2. `docs/builder/bld-016-r2-walker_source_reference_fix.md` — this artifact; append the build report at the same top level, never edit the plan section.
3. `docs/builder/worker-memory/spec-016-worker-2.md` — Worker 2's own memory file (it exists and is empty; gitignored). Worker 2 reads and writes only this one, never another worker's.

Worker 2 may create its own new output under `docs/shadow/` if it re-runs `scripts/review_inspect.py`, and must not overwrite `docs/shadow/helper-inventory.md`, `docs/shadow/current/`, or any other pre-existing shadow file — those are a concurrent session's.

### Do not touch

- `CHANGELOG.md` (`AGENTS.md` rule 21 — no CHANGELOG updates unless told; the stale-id and stale-site-name residue there is catalogued, not fixed), `KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md`, `examples/fakeshop/db.sqlite3` — generated / DB-backed, none in any round's writable set. If one turns dirty during this round it is a concurrent writer's, **not** this build's output, and no worker reverts it.
- Anything under `docs/review/` (`AGENTS.md` rule 22 — never bulk-delete or bulk-overwrite; `rev-*.md` / `review-*.md` are committed source of truth).
- `docs/SPECS/spec-016-fieldmeta_consolidation-0_0_6.md` and its `appx/` companions (`-rationale.md`, `-terms.csv`) — custodian-only; Worker 1 is the only role that may edit them. Surface any needed change under `### Notes for Worker 1 (spec reconciliation)`.
- `tests/test_registry.py` — its `:504` comment names the deleted `_record_pending_relation` and is deliberately **out of scope** this cycle (see `### Notes for Worker 1`). Do not fix it, do not open it to edit.
- `docs/shadow/` and `docs/builder/temp-tests/` **existing** contents — another session's live output.
- **The baseline-dirty out-of-scope paths listed in the build plan's `## Baseline-dirty out-of-scope files`** — never edit, never revert, never stage, never `git checkout`. Two concurrent sessions' in-flight work; the count drifts upward during the cycle (50 at plan time, 52 at R1, 51 at this pass, still moving), so treat the *buckets* as the definition, not the number. **`django_strawberry_framework/optimizer/extension.py` is among them**: read it only via `git show HEAD:<path>`, never open it for editing, even though it is one of the files this card's spec names.
- `git stash`, `git checkout`, `git restore`, `git worktree` — banned in this round, no exceptions. The maintainer runs concurrent sessions against this tree.
- `scripts/build_tree_md.py`, `scripts/build_kanban_md.py`, `scripts/build_glossary_md.py` — do not run them. They read the fakeshop DB and rewrite generated docs that are out of every round's writable set. No regeneration is owed: `docs/TREE.md` renders **module** docstrings, and this round edits a **function** docstring (`_resolve_field_map`, at `walker.py:313`; the module docstring is at the top of the file and is untouched).

### Implementation steps

Line numbers are pin-at-write-time navigational hints; verify against the current source before editing.

#### Step 1 — confirm the target is unchanged and the old text is unique

```shell
git rev-parse HEAD
git log -1 --format='%T'      # expect 7debb73f3b03e58ca197904756bed5d59753e549; if different, re-measure Step 2's text
git status --short -- django_strawberry_framework/optimizer/walker.py                       # expect no output
grep -cF 'optimizer/resolvers.py::_field_meta_for_resolver' django_strawberry_framework/optimizer/walker.py
```

The `grep -cF` **must print exactly `1`.** A count of 0 means someone already fixed it (stop and report); a count above 1 means the single-line edit below is not unique and the plan needs revising (stop and report). This check runs **before** the edit, for the same reason `docs/builder/BUILD.md`'s proof loop puts its anchor check first: nothing later in the sequence can tell that its own reference was already mutated.

#### Step 2 — the edit: one line, exact text on both sides

The line is `django_strawberry_framework/optimizer/walker.py:313`, inside `::_resolve_field_map`'s docstring, in its `DUAL CONTRACT` paragraph. The surrounding three lines at `HEAD` read (312-314, four-space indent, lengths 69 / 73 / 9):

```
    divergence (and the same ``getattr``-defensive fallback) lives in
    ``optimizer/resolvers.py::_field_meta_for_resolver``; keep the two in
    sync.
```

**Replace exactly this one line** (line 313, including its leading four spaces):

```
    ``optimizer/resolvers.py::_field_meta_for_resolver``; keep the two in
```

**with exactly this one line:**

```
    ``types/resolvers.py::_field_meta_for_resolver``; keep the two in
```

That is the whole change: `optimizer/` -> `types/`, ten characters, one line. Lines 312 and 314 are **not** touched.

**Do not reflow the paragraph.** The replacement is 69 characters (measured), so it would fit `sync.` on the same line and the temptation is real. Two reasons it is refused, both decided here rather than delegated: a reflow enlarges a one-line diff into a three-line one for zero contract gain, and a `#"unique substring"` citation anywhere in the repo's specs or docs breaks on reflow exactly as it breaks on reword (standing lesson). Nothing currently cites into these three lines — the spec cites `optimizer/walker.py::_resolve_field_map` with no substring, and the rationale cites `#"DUAL CONTRACT (read before consuming the returned map)"`, which is `walker.py:304` and unaffected — but the discipline is what keeps that true.

**Why `types/resolvers.py` and not a bare `resolvers.py`, measured rather than asserted.** The package's house style permits a bare-basename shorthand for a cross-folder target where the basename is unique (`plans.py::`, `nested_planner.py::`, `nested_fetch.py::`, `finalizer.py::` all appear that way, and `find . -name plans.py` / `nested_planner.py` / `finalizer.py` each return exactly one path). `resolvers.py` is the opposite case: `find django_strawberry_framework -name resolvers.py` returns **four** paths — `types/`, `forms/`, `mutations/`, `rest_framework/`. So the folder segment is load-bearing for this symbol specifically, and `optimizer/` is not merely under-qualified but names one of the folders that does **not** contain it. The chosen spelling matches the two places already correct (`optimizer/field_meta.py:204` and the reconciled spec).

ASCII-only (`AGENTS.md` rule 17): the replacement contains no non-ASCII byte. Line length: 69, well inside the 100 limit (E501 graced to 110).

#### Step 3 — the grep sweep, with its proof condition stated

`AGENTS.md` rule 27's "renaming a symbol means grep-sweep `::OldName` in the same change" is the standing authority. Run all four and paste each command with its output into the build report.

```shell
# 3a. THE PROOF OF THE FIX: zero occurrences of the never-existent module in package source.
grep -rn "optimizer/resolvers" django_strawberry_framework/
#   PROOF: prints nothing, exit 1. Any line under django_strawberry_framework/ is a failure.

# 3b. Repo-wide, to show the only survivors are per-cycle artifacts that QUOTE the defect.
git grep -n -I "optimizer/resolvers" -- . ':!*.sqlite3'
#   PROOF: the only hits are docs/builder/build-016-…md (the F8 row) and
#   docs/SPECS/appx/spec-016-…-rationale.md (the deferred-work bullet), both of which
#   quote the wrong spelling as evidence and MUST NOT be edited. Zero hits in .py files.

# 3c. Every ``path.py::Symbol`` reference in the edited file resolves to a real file.
grep -n -oE '``[a-zA-Z_]+(/[a-zA-Z_]+)*\.py::[A-Za-z_.]+``' \
    django_strawberry_framework/optimizer/walker.py \
  | while IFS=: read -r ln ref; do
      p=$(echo "$ref" | sed 's/^``//; s/::.*//')
      if [ -f "django_strawberry_framework/$p" ]; then r="root-relative OK"
      elif [ -f "django_strawberry_framework/optimizer/$p" ]; then r="optimizer-sibling OK"
      else r="*** UNRESOLVED ***"; fi
      echo "$ln  $ref  -> $r"
    done
#   PROOF: six rows, zero of them "*** UNRESOLVED ***".
#   Before the fix this loop reports two unresolved rows (:313 and :579); after the fix it
#   reports one (:579). See the F8-sweep box for why :579 is CORRECT and must not be changed.

# 3d. The deleted symbol and the unqualified audit-method spelling are absent from package source.
grep -rn "_record_pending_relation" django_strawberry_framework/
grep -rnE "extension\.check_schema" django_strawberry_framework/ tests/
#   PROOF: both print nothing, exit 1. (Measured at plan time: both already clean. These two
#   run as regression guards, not as fixes — the surviving occurrences are all in files this
#   round may not touch, catalogued under ### Notes for Worker 1.)
```

**What the sweep found, and the decided disposition of each near-miss.** All of this was measured at plan time; Worker 2 re-proves it with 3a-3d and fixes nothing beyond `:313`.

| Site | Spelling | Decision | Reason |
|---|---|---|---|
| `optimizer/walker.py:313` | `optimizer/resolvers.py::_field_meta_for_resolver` | **FIX (F8)** | names a module that has never existed, and `resolvers.py` is 4-way ambiguous so the wrong folder actively misdirects |
| `optimizer/walker.py:579` | `finalizer.py::finalize_django_types` | **do not change** | under-qualified but resolves: `finalizer.py` is a **unique** basename package-wide, and the same shorthand is house style at ~12 cross-folder sites (`connection.py:401`, `keyset.py:185`, `utils/connections.py:184,445,446,447`, `utils/querysets.py:2790,2981`, `filters/inputs.py:738`, `rest_framework/resolvers.py:1860`, `optimizer/walker.py:121,377,740`). Fixing one instance in one file would create a local inconsistency and is a house-style change, not a defect fix. **Not** the same class as F8 |
| `optimizer/walker.py:770` | `utils.relations.instance_accessor` (dotted) | **do not change** | `instance_accessor` is not one of this card's symbols (`utils/relations.py:550`, unrelated to the seven reader sites), so it is outside spec-016's scope. Recorded, not dispatched |
| `optimizer/extension.py:679` | bare `` `check_schema` `` in prose | **do not change**, and out of writable set anyway | a same-module mention inside `extension.py` itself, not a cross-module path reference; rule 27 governs source *refs*, not a local name. The file is also baseline-dirty |
| `registry.py:6` | `types.converters.resolved_relation_annotation` (dotted) | **defer** | a non-conforming spelling of one of this card's symbols (V2), but `registry.py` is outside the writable set this round was given. Catalogued under `### Notes for Worker 1` |
| `types/converters.py:409` | `types/base._build_annotations` (mixed) | **defer** | same class, same reason (V1's canonical read site); `types/converters.py` is outside the writable set. Catalogued |
| `tests/test_registry.py:504` | `_record_pending_relation` | **defer** | names a symbol deleted at `f83bb71b`; explicitly out of scope per the do-not-touch list |
| `CHANGELOG.md:221` | stale card id + 3 stale site names + bare `extension.check_schema` | **defer** | `AGENTS.md` rule 21 forbids the edit |

#### Step 4 — validation, scoped so it cannot reformat a concurrent session's files

`AGENTS.md` rule 16 requires `uv run ruff format .` and `uv run ruff check --fix .` after every edit, and `docs/builder/ARTIFACT.md`'s `### Validation run` requires the write-mode runs be **scoped to this pass's own files, never `.`**. The two reconcile the only way they can: run the same tools in the same order, with the one file this round touched as the explicit target. Nine package source files and ten test files are dirty with two concurrent sessions' work; a bare `.` would reformat all of them and put someone else's churn in this round's diff.

```shell
uv run ruff format django_strawberry_framework/optimizer/walker.py
uv run ruff check --fix django_strawberry_framework/optimizer/walker.py
uv run python scripts/check_trailing_commas.py --check django_strawberry_framework/optimizer/walker.py
git status --short
```

- The third command is the ASCII-only / source-layout gate the pre-commit `source-layout` hook runs; `ruff format` passing is not that hook passing, and a build pass that skips it defers the failure to commit time. `--check` is read-only.
- `git status --short` after both ruff invocations: **`django_strawberry_framework/optimizer/walker.py` plus this artifact must be the only additions to the baseline-dirty set.** Anything else is a **stop-and-report**, never a revert — `git checkout -- <path>` here destroys a concurrent session's uncommitted change. Report it in the build report rather than tidying it.
- **No `pytest` in this pass.** There is no test whose behavior this change could alter: the diff contains no executable statement, and nothing in `tests/` or `examples/` asserts on this docstring (measured: `grep -rn "__doc__\|DUAL CONTRACT\|_resolve_field_map" tests/ examples/` returns one hit, `tests/optimizer/test_walker.py:2105`, which mentions `_resolve_field_map(Item)` in a *test's own* explanatory comment and asserts nothing about the docstring). `docs/builder/BUILD.md` `## Coverage is the maintainer's gate, not a worker's tool` forbids coverage flags in every pass; `--no-cov` is the only coverage-shaped flag permitted anywhere, and this pass needs none of them.

#### Step 5 — write the build report and set `Status: built`

Append `## Build report (Worker 2)` at the top level of this artifact with every subsection `docs/builder/ARTIFACT.md` names, including the three that are written as explicit negatives here (`### Failability proofs` -> `None; this pass introduced no new boundary.`; `### Hot-path budget` -> `Not applicable; plan declares no hot path.`; `### Floor verification` -> `Not applicable; plan declares floor-verification scope none.`). Keep every heading. Tick the checklist boxes whose contract actually landed. Append 3-5 lines to `docs/builder/worker-memory/spec-016-worker-2.md`. Set the artifact's `Status:` line to `built`. **Never commit** — only the maintainer commits, even if asked.

### Test additions / updates

**None owed, and this is a decided answer rather than an empty section.** A comment-only change ordinarily owes no test, and this one specifically cannot owe one:

- The diff changes ten characters inside a function docstring. `_resolve_field_map`'s four executable statements, its signature, and its return shape are unchanged, so there is no behavior a new assertion could pin and no existing assertion that can go stale.
- Nothing in any of the three test trees asserts on this docstring. Measured: `grep -rn "__doc__\|DUAL CONTRACT\|_resolve_field_map" tests/ examples/` -> a single hit, `tests/optimizer/test_walker.py:2105`, and it is prose inside a test's own comment.
- The docstring is **function-level**, not module-level, so `scripts/build_tree_md.py` (which renders `docs/TREE.md` from module docstrings) reads nothing that changed. No generated-doc regeneration is owed, and running the renderer is forbidden by the do-not-touch list.
- Neither of `docs/builder/BUILD.md`'s two test-staleness shapes applies: no example-model field set changed, and no wire shape changed.

**Temp tests: none appropriate.** `docs/builder/temp-tests/` holds a concurrent session's live output (`r1`, `r1c`, `r2`, `r4`); this round creates nothing there. Worker 3 needs no temp test to review a one-line docstring change — the greps in Step 3 are the verification, and Worker 3 should re-run 3a and 3c independently rather than accepting the recorded output.

### Implementation discretion items

Assessed and decided as Worker 2's, per `docs/builder/ARTIFACT.md` — neither is architectural:

- **The mechanism of the edit** (an `Edit` on the single line versus rewriting the docstring block with identical bytes elsewhere). Any mechanism is fine provided the resulting file differs from `HEAD` by exactly line 313 and nothing else; `git diff -- django_strawberry_framework/optimizer/walker.py` showing a one-line change is the acceptance condition.
- **The order of Step 3's four greps and Step 4's three commands** within their own steps, and whether the Step 3 loop is pasted as a one-liner or a multi-line block in the build report. Step 1's `grep -cF` must still run **before** the edit, and Step 4's two ruff runs must run in the order given.

Everything about the replacement *text* is fixed in Step 2 and is not discretionary.

### Dispatched findings checklist

One `- [ ]` box per item dispatched to this round. F1-F7 belong to R1 (closed) and F9-F13 to R3; neither appears here. Boxes stay `- [ ]` at planning; Worker 2 ticks only a box whose contract landed in its diff; Worker 1 audits every tick at final verification.

- [x] **F8** — "**`optimizer/walker.py::_resolve_field_map`'s docstring points its dual-contract cross-reference at a module that does not exist.** It reads 'The same divergence (and the same `getattr`-defensive fallback) lives in `optimizer/resolvers.py::_field_meta_for_resolver`; keep the two in sync.' There is no `django_strawberry_framework/optimizer/resolvers.py`; the symbol is `django_strawberry_framework/types/resolvers.py::_field_meta_for_resolver` (V3). This is the *one* cross-reference tying the two halves of this card's SSoT surface together, and it sends a reader looking for a file that was never there." Symbol-qualified path, from Worker 0's verification pass: `django_strawberry_framework/optimizer/walker.py::_resolve_field_map` #"keep the two in", target `django_strawberry_framework/types/resolvers.py::_field_meta_for_resolver`. Landed when the Step 2 replacement is in the file and Step 3a prints nothing.
- [x] **F8-sweep** — `AGENTS.md` rule 27's same-change grep-sweep obligation for this card's own symbols, dispatched as its own box because it is separately auditable work rather than a side effect of the F8 edit. Landed when all four Step 3 commands have been run and their exact output pasted into the build report, each meeting the stated proof condition: 3a and 3d print nothing; 3b's only hits are per-cycle artifacts that quote the defect and **zero `.py` files** (the plan's "two artifacts" prediction was wrong — `git grep` cannot see this cycle's untracked artifacts, so the population must be established with a plain recursive grep, and its total is a moving figure about the artifacts that no pass may quote forward); 3c prints **every `` `path.py::Symbol` `` reference in the edited file with zero unresolved once the loop's candidate roots include `types/`** — corrected by Worker 1 at final verification, because the condition as first written ("six rows with zero `*** UNRESOLVED ***`") was unachievable on the day it was written and is now two rows off besides. The provable form, re-measured at final verification: **seven rows**, and with `types/`-sibling added as a third candidate root all seven resolve (`:121` `extension.py::_build_cache_key`, `:308` `field_meta.py::_DjangoFieldLike`, `:315` `types/resolvers.py::_field_meta_for_resolver`, `:368` `utils/querysets.py::apply_type_visibility_sync`, `:382` `nested_fetch.py::unwindowable_child_queryset_reason`, `:584` `finalizer.py::finalize_django_types`, `:745` `plans.py::prune_unsupportable_select_related`). Run with the plan's two-root loop verbatim the equivalent condition is **seven rows, exactly one `*** UNRESOLVED ***`, and it is `:584` `finalizer.py::finalize_django_types`** — the acquitted house-style shorthand, not a defect. Ticking this box also asserts that **no near-miss site in the Step 3 disposition table was changed** — `walker.py:579`, `walker.py:770`, `registry.py:6`, `types/converters.py:409`, `tests/test_registry.py:504`, `CHANGELOG.md:221` are all untouched.

### Notes for Worker 1 (spec reconciliation)

Recorded at plan time for the final gate's `### Deferred work catalog` (Worker 1 is its only author) and for R3's audit. **None of these is a defect in shipped behavior, and none is R2's to fix.**

1. **The spec's `### Bounded exceptions` bullet over-claims the symmetry between the two sites, as does the docstring it describes.** Both say "the same divergence" is present in `types/resolvers.py::_field_meta_for_resolver`. Measured this pass: `_resolve_field_map` returns a `dict[str, Any]` whose values are `FieldMeta` **or raw Django field objects** — a genuine dual *shape*, safe only via `getattr(..., default)` — while `_field_meta_for_resolver` returns `FieldMeta` unconditionally, its fallbacks producing a real `FieldMeta` via `FieldMeta._from_field_shape` / `from_django_field`. What the two actually share is one policy ("the canonical definition may be unreachable"), not a shape and not the `getattr`-defensive read. The claim is defensible at a coarse reading and misdirects no builder, so **the spec is NOT edited in this pass** and the round stays `planned` rather than `revision-needed`: R2's brief is the reference's *address*, and rewording the claim in the docstring would exceed the one authorized source edit while rewording it in the spec would change a contract sentence mid-round. Candidate for a future spec-custodian pass or the next residual cycle; if taken, the docstring and the spec bullet must be corrected in the same change, since one describes the other.
2. **`django_strawberry_framework/registry.py:6`** spells one of this card's symbols as `` ``types.converters.resolved_relation_annotation`` `` — a dotted module path where `AGENTS.md` rule 27 requires `types/converters.py::resolved_relation_annotation`. The file is clean at baseline but outside this round's writable set. Measured by `git grep -n -I -E "converters\.resolved_relation_annotation" HEAD`.
3. **`django_strawberry_framework/types/converters.py:409`** spells another of this card's symbols as `` ``types/base._build_annotations`` `` — a mixed slash-and-dot form where rule 27 requires `types/base.py::_build_annotations`. Clean at baseline, outside this round's writable set. Same grep.
4. **`django_strawberry_framework/optimizer/walker.py:770`** carries `` (``utils.relations.instance_accessor``) `` — a dotted form in the file this round *does* own, deliberately left alone because `instance_accessor` (`utils/relations.py:550`) is not one of spec-016's symbols and fixing it would be scope creep into another card's surface.
5. **The bare-basename cross-folder shorthand is house style, not a defect class** — ~12 sites measured (listed in the Step 3 disposition table), each resolving because the basename is unique package-wide. Recorded so a later sweep does not "fix" one instance and fracture the convention, and so the next reader understands why `walker.py:579` was seen and passed while `:313` was fixed: `resolvers.py` is four-way ambiguous and `finalizer.py` is not.
6. **R1's two carried-forward residues stand unchanged**, both re-measured this pass: `tests/test_registry.py:504` names the deleted `_record_pending_relation` (tests are outside every round's writable set this cycle), and `CHANGELOG.md:221` carries the pre-renumber card id **plus** the three stale site names **plus** the bare `extension.check_schema` — wider than F12 recorded it, and barred by `AGENTS.md` rule 21.
7. **`HEAD`'s hash has now rotted twice in one cycle, the second time by a rebase rather than an amend** (`d94db992` -> `ded4b00c` -> `ab821ae0`, parent moving from `d28fbc0a` to `1dafe419`), while the tree object stayed `7debb73f` throughout. The final gate should quote the tree object rather than any commit hash when it certifies what was verified.
8. **`scripts/review_inspect.py`'s output is structurally blind to this round's change surface** (it strips comments and replaces every string-literal token including docstrings with `...`). Recorded so the final gate does not read a clean shadow overview as evidence about a docstring edit.

---

## Build report (Worker 2)

### Files touched

Grounded in `git status --short`, not memory. **58 paths dirty at this pass's end; 57 at its start.** The one addition is `walker.py`; everything else in that listing was already dirty at spawn and belongs to the concurrent sessions (the plan's `## Baseline-dirty out-of-scope files` buckets). None was edited, reverted, staged, or `git checkout`ed.

- `django_strawberry_framework/optimizer/walker.py` — `::_resolve_field_map`'s docstring, the closing sentences of its `DUAL CONTRACT` paragraph. Two changes in one edit: F8's cross-reference address (`optimizer/resolvers.py` -> `types/resolvers.py`), and Worker 0's mid-flight correction of the same sentence's over-claim (below). `-4 / +7` lines; no executable statement, signature, or return shape touched.
- `docs/builder/bld-016-r2-walker_source_reference_fix.md` — this build report, the two `### Dispatched findings checklist` ticks, `Status: built`. The `## Plan (Worker 1)` section was not edited.
- `docs/builder/worker-memory/spec-016-worker-2.md` — one appended entry (gitignored, so it does not appear in `git status`).

**Baseline re-verified before the first edit, exactly as `### Baseline, HEAD, and drift` requires:**

```shell
git rev-parse HEAD                      # ab821ae07e5c9b581c2a644a81e94c890c8790cd
git log -1 --format='%H %T %P %ci %s'   # tree 7debb73f3b03e58ca197904756bed5d59753e549
git status --short -- django_strawberry_framework/optimizer/walker.py   # no output
git show HEAD:django_strawberry_framework/optimizer/walker.py > <scratch outside repo>/walker.head.py
cmp <scratch outside repo>/walker.head.py django_strawberry_framework/optimizer/walker.py   # exit 0
grep -cF 'optimizer/resolvers.py::_field_meta_for_resolver' django_strawberry_framework/optimizer/walker.py   # 1
```

`HEAD`'s commit hash is unchanged from R1's second measurement (`ab821ae0`) and the **tree object is still `7debb73f`**, so every plan-time reading held and no re-measurement of Step 2's text was owed. `grep -cF` printed exactly `1` before the edit — neither the already-fixed nor the non-unique stop-and-report case. `git stash`, `git checkout`, `git restore`, and `git worktree` were used **nowhere** in this pass; the only HEAD reference was `git show HEAD:<path>` into a scratch path outside the repository.

### Tests added or updated

**None, per the plan's `### Test additions / updates`**, which decided the answer rather than leaving it blank: the diff changes only docstring prose, no executable statement or wire shape, and nothing in any of the three test trees asserts on this docstring. Re-measured this pass rather than accepted from the plan: `grep -rn "__doc__\|DUAL CONTRACT\|_resolve_field_map" tests/ examples/` returns one hit, `tests/optimizer/test_walker.py:2105`, which names `_resolve_field_map(Item)` inside a test's own explanatory comment and asserts nothing about the docstring. Neither test-staleness shape (`BUILD.md` `### Test staleness a focused run cannot see`) applies — no example-model field set and no wire shape changed — so no full sweep was owed before `Status: built`. No temp test created; `docs/builder/temp-tests/` was not touched.

### Validation run

Scoped to the one file this pass touched, never `.`, in the plan's order.

- `uv run ruff format django_strawberry_framework/optimizer/walker.py` — **pass**, `1 file left unchanged` (the replacement was already formatter-clean). The `COM812`-vs-formatter conflict warning is pre-existing repo configuration, not this diff's.
- `uv run ruff check --fix django_strawberry_framework/optimizer/walker.py` — **pass**, `All checks passed!`, no fix applied.
- `uv run python scripts/check_trailing_commas.py --check django_strawberry_framework/optimizer/walker.py` — **pass**, exit 0 (the ASCII-only / source-layout gate the pre-commit `source-layout` hook runs; read-only).
- `git status --short` after both ruff invocations — **58 paths**, of which `django_strawberry_framework/optimizer/walker.py` is this pass's only source addition to the baseline-dirty set and `docs/builder/bld-016-r2-…md` this pass's only artifact write. No unexpected churn appeared, so no stop-and-report was owed and nothing was reverted.
- **No `pytest` run**, per the plan and `BUILD.md` `## Coverage is the maintainer's gate, not a worker's tool`. No coverage-shaped flag was used anywhere in this pass.

**The Step 3 sweep, verbatim commands and exact output.** Each proof condition is stated with its result; two deviated from the plan's predicted output and both deviations are the plan's own prediction being wrong, not the fix being wrong.

```shell
# 3a. THE PROOF OF THE FIX
$ grep -rn "optimizer/resolvers" django_strawberry_framework/
$ echo "exit=$?"
exit=1
```

**PROOF MET** — zero occurrences of the never-existent module anywhere under package source.

```shell
# 3b. Repo-wide
$ git grep -n -I "optimizer/resolvers" -- . ':!*.sqlite3'
$ echo "exit=$?"
exit=1
```

**PROOF MET, but by a stronger result than the plan predicted, for a mechanical reason worth recording.** The plan expected two surviving hits (the build plan's F8 row and the rationale companion's deferred-work bullet). `git grep` without `--no-index` searches **tracked** files only, and both of those files are untracked (`?? docs/builder/build-016-…`, `?? docs/SPECS/appx/spec-016-…-rationale.md`), so it reports none. Re-run with a plain recursive grep so the population is actually established rather than sampled:

```shell
$ grep -rn -I "optimizer/resolvers" --exclude='*.sqlite3' .
docs/SPECS/appx/spec-016-fieldmeta_consolidation-0_0_6-rationale.md:470
docs/builder/bld-016-r2-walker_source_reference_fix.md:58, :128, :139, :146, :169, :173, :204, :256
docs/builder/build-016-fieldmeta_consolidation-0_0_6.md:82
```

**Eleven occurrences across three files, every one a per-cycle artifact quoting the defect as evidence** (nine of them in this artifact's own plan section), and **zero in any `.py` file**. None was edited. This is the plan's stated proof condition met on content; only its predicted command output was wrong.

```shell
# 3c. Every ``path.py::Symbol`` reference in the edited file resolves
121  ``extension.py::_build_cache_key``                      -> optimizer-sibling OK
312  ``types/resolvers.py::_field_meta_for_resolver``         -> root-relative OK
366  ``utils/querysets.py::apply_type_visibility_sync``      -> root-relative OK
380  ``nested_fetch.py::unwindowable_child_queryset_reason``  -> optimizer-sibling OK
582  ``finalizer.py::finalize_django_types``                 -> *** UNRESOLVED ***
743  ``plans.py::prune_unsupportable_select_related``        -> optimizer-sibling OK
```

**Six rows, and the one `*** UNRESOLVED ***` row is the acquitted site, not a defect.** The plan's Step 3c states its proof condition two contradictory ways in the same box — "six rows, zero of them `*** UNRESOLVED ***`" and, three lines later, "after the fix it reports one (`:579`)". The measured answer is the **second**: the loop resolves only package-root-relative and optimizer-sibling paths, and `finalizer.py` is neither — it is `types/finalizer.py`, so the loop's two candidate paths both miss. That is a limitation of the loop, not an unresolved reference: `find django_strawberry_framework -name finalizer.py` returns exactly one path, so the bare-basename shorthand resolves for a human reader, which is precisely the acquittal the disposition table records. The row moved `:579` -> `:582` because this pass's edit added three net lines above it. **F8's own row is line 312 and reads `root-relative OK`** — the fix, proved by the same loop that flagged it before.

```shell
# 3d. Regression guards
$ grep -rn "_record_pending_relation" django_strawberry_framework/     ; echo exit=$?   # exit=1
$ grep -rnE "extension\.check_schema" django_strawberry_framework/ tests/ ; echo exit=$?   # exit=1
```

**PROOF MET** — both print nothing. Regression guards only; nothing was fixed by them.

**No near-miss site in the disposition table was changed.** `walker.py:582` (was `:579`), `walker.py:773` (was `:770`, the `utils.relations.instance_accessor` dotted form), `registry.py:6`, `types/converters.py:409`, `tests/test_registry.py:504`, and `CHANGELOG.md:221` are all untouched — `git diff` over the whole tree shows this pass's only source hunk is the one in `walker.py`'s docstring.

### Failability proofs

**None; this pass introduced no new boundary.**

Recorded with the plan's reasoning rather than as a bare assertion, per its `### Boundary count, and the failability-proof answer`: boundary count is **zero** — no guard, cap, rejection path, validation branch, gate, or error message enters the diff. `BUILD.md` `### What needs a proof, and what does not` scopes the obligation to a new boundary and explicitly exempts doc edits. `_resolve_field_map`'s four executable statements, its signature, and its return shape are byte-identical to `HEAD`, so there is nothing a mutation could remove and no test row that could observe its removal. No mutation was applied anywhere in this pass and no `ACTIVE-MUTATION.json` exists; the tree handed to Worker 3 carries none. **Fail-open shapes: none introduced** — the diff contains no expression at all.

### Hot-path budget

**Not applicable; plan declares no hot path.** No executable statement changed, so no path got slower or faster.

### Floor verification

**Not applicable; plan declares floor-verification scope none.** Nothing was installed into the shared `.venv`, and no floor venv was built. Floor facts, quoted from `BUILD.md` `## Floor verification` rather than restated from memory: Django **5.2.16** on Python **3.10** with strawberry-graphql **0.316.0**; the shared `.venv` is not the floor.

### Implementation notes

- **The edit was applied as one `Edit` over the four-line sentence** rather than the plan's single-line replacement, because the mid-flight addition below rewrites that sentence's content. The plan's Step 2 no-reflow rule was written for the address-only fix — where a reflow would enlarge a one-line diff for zero contract gain — and it stops governing once the sentence's substance is what changes. The `DUAL CONTRACT` paragraph's first six lines, everything above them, and everything below the docstring are untouched; the diff is `-4 / +7` inside one docstring.
- **`types/resolvers.py::` and not a bare `resolvers.py::`**, as the plan fixed: `find django_strawberry_framework -name resolvers.py` returns **four** paths (`types/`, `forms/`, `mutations/`, `rest_framework/`) measured again this pass, so the folder segment is load-bearing for this symbol. The spelling matches the two sites that were already right (`optimizer/field_meta.py::FieldMeta._from_field_shape`'s docstring and the reconciled spec's `### Bounded exceptions` bullet), so no third spelling of one symbol entered the package.
- **`--` for the parenthetical dashes, not an en/em dash** — ASCII-only in `.py` (`AGENTS.md` rule 17), and it matches the surrounding paragraph's existing `-- that defensive access is the ONLY reason` style. Longest new line is 74 characters, inside the 100 limit.
- **"Keep the policy in sync" replaced "keep the two in sync"** rather than dropping the sync instruction. The instruction still holds — what must not drift is the shared policy — and the qualifier is what stops the next reader inferring the shapes must converge too.
- `scripts/review_inspect.py` was **not** re-run this pass. The plan already ran it for this file and recorded the finding that matters (walker.py's two `TODO(spec-035)` anchors, another card's, both untouched by this diff), and its output is structurally blind to a docstring edit — it replaces every string-literal token including docstrings with `...`. Re-running it would have produced a file identical in every respect this round can change. No new `docs/shadow/` file was created and no existing one was overwritten.

### Notes for Worker 3

- **The mid-flight instruction from Worker 0, recorded here so this artifact carries it rather than the dispatch transcript.** Worker 1's planning pass measured, and escalated as note 1 under `### Notes for Worker 1 (spec reconciliation)`, that the same docstring sentence F8 fixes also **over-claims**: it said "the same divergence (and the same `getattr`-defensive fallback)" lives at the twin site. Worker 1 deferred the correction because the spec's `### Bounded exceptions to the single-source rule` bullet carries the same over-claim and the pair should move together. **Worker 0 authorized the source half in this pass**, in the same edit as F8, on the ground that it is the same sentence and splitting one sentence across two rounds is what would strand it. The spec half is dispatched to R3 (Worker 1, custodian) citing the wording landed here, so the pair lands in one maintainer commit. Worker 3 should review the diff against **both** obligations, not F8 alone.
- **I verified the over-claim myself before rewriting it, as instructed, and my reading agrees with Worker 1's.** Read read-only via `git show HEAD:django_strawberry_framework/types/resolvers.py` into a scratch path outside the repo. In my own words: `::_field_meta_for_resolver` is annotated `-> FieldMeta` and **every one of its three return paths yields a `FieldMeta`** — the canonical `definition.field_map.get(field.name)` hit, `FieldMeta._from_field_shape(field, is_relation=True)` for a descriptor lacking `is_relation`, and `FieldMeta.from_django_field(field)` otherwise. There is no branch on which it returns a raw Django field, so it has no dual return shape. Its consumer reads the result by **plain attribute access** — `types/resolvers.py::_make_relation_resolver` #"field_meta = _field_meta_for_resolver(field, parent_type)" then `field_meta.relation_kind` and `field_meta.is_many_side` — with no `getattr` default anywhere, which is only safe *because* the return type is unconditional. By contrast `::_resolve_field_map` returns `dict[str, Any]` whose values are `definition.field_map`'s `FieldMeta` on the registered path and raw `model._meta.get_fields()` objects on the fallback, which is what forces the `getattr(..., default)` discipline the paragraph's earlier lines state. **So the two sites share the policy — prefer the canonical definition-backed metadata, fall back when it is unreachable — and share neither the dual return shape nor the `getattr`-defensive read.** That is what the new wording says, and it is the narrowest correction that makes the sentence true.
- **`unreachable` was chosen over `unavailable`** for the fallback condition, to match the spec's own vocabulary in the same bullet (#"the canonical definition may be unreachable") and `_field_meta_for_resolver`'s actual condition — the definition or the entry not being resolvable, rather than absent in some other sense.
- The `finalizer.py::finalize_django_types` row that the Step 3c loop prints as `*** UNRESOLVED ***` is the disposition table's acquitted `:579` site at its new line `:582`, not a regression this pass introduced. The loop cannot resolve `types/`-relative shorthand; see `### Validation run` for the measurement.
- Nothing was mutated, so the tree Worker 3 receives holds no transient production change. `walker.py` differs from `HEAD` by exactly one docstring hunk.

### Notes for Worker 1 (spec reconciliation)

The plan's eight notes stand as written; these are this pass's additions. **The first is the live one and R3 owns it.**

1. **The spec half of the over-claim is now owed, and its wording is fixed by what landed.** The source half is corrected in this pass under Worker 0's mid-flight authorization, so the spec and the code now disagree until R3 closes it.
   - **Where it lives:** `docs/SPECS/spec-016-fieldmeta_consolidation-0_0_6.md`, `### Bounded exceptions to the single-source rule`, first bullet (**The walker's dual contract**), its closing sentence. Secondary, and stale the moment the custodian edits the file: `spec-016-fieldmeta_consolidation-0_0_6.md:34`.
   - **Current wording, quoted:** "The site's docstring is the standing statement of this contract, and the same divergence is present in `types/resolvers.py::_field_meta_for_resolver`."
   - **Recommended replacement:** "The site's docstring is the standing statement of this contract. `types/resolvers.py::_field_meta_for_resolver` shares the policy — prefer the canonical definition-backed metadata, fall back when it is unreachable — but not this dual return shape: it returns a `FieldMeta` unconditionally, so its callers read attributes directly and need no `getattr` default."
   - **Why this wording:** it is the spec-side paraphrase of the sentence now in `walker.py::_resolve_field_map`'s docstring, so the two describe each other without either over-claiming. Note the second bullet of that same spec section (**Test-double fallbacks**) is already correct and needs no edit — it states the fallbacks "produce a `FieldMeta` observably identical to the canonical builder's", which is the very fact that falsifies the first bullet's "same divergence" claim. The spec already contained its own refutation two bullets apart.
2. **The plan's Step 3c proof condition is self-contradictory and should not be copied forward into R3 or the final gate.** It states both "six rows, zero of them `*** UNRESOLVED ***`" and "after the fix it reports one (`:579`)"; the measured answer is one row, and that row is the acquitted `finalizer.py` shorthand the loop structurally cannot resolve. Any future sweep reusing this loop should either resolve `types/`-relative paths too or record the expected row explicitly, or it will read a correct file as defective every time.
3. **The plan's Step 3b predicted output is wrong in a way that would hide a regression.** `git grep` without `--no-index` skips untracked files, and both files the plan expected to see are untracked this cycle, so the command returns nothing whether or not the defect survives elsewhere in them. A repo-wide sweep whose purpose is to establish a population must not be `git grep` while this cycle's own artifacts are untracked; the plain recursive grep recorded in `### Validation run` is the one that measures it (eleven occurrences, three files, all per-cycle artifacts, zero `.py`).
4. **No refactor of the two dual-contract sites is proposed**, which the plan explicitly invited a proposal on. Having read both bodies this pass I agree with the plan's `#### The existence challenge` and its rejected-alternative record: the sites share a policy, not a shape, and the condition that would end the duplication is already named in the docstring itself ("until the registry-coverage gate lands"), at which point the walker's fallback disappears and the cross-reference should be **deleted** rather than re-pointed. Recorded so a later reader does not mistake silence here for the question going unasked.

---

## Review (Worker 3)

Reviewed the working-tree diff of `django_strawberry_framework/optimizer/walker.py` against `HEAD`, read-only. **`HEAD` tree object certified `7debb73f3b03e58ca197904756bed5d59753e549`** (`git rev-parse HEAD^{tree}`), matching what the plan and the build report both recorded, so every reading either pass took still stands and no commit hash was trusted. `git stash`, `git checkout`, `git restore`, `git worktree` were used **nowhere** in this pass; the only `HEAD` reference was `git show HEAD:<path>` / `git diff`.

The diff is one hunk inside `::_resolve_field_map`'s docstring, `-4 / +7`. Re-derived independently: `git diff -- django_strawberry_framework/optimizer/walker.py` shows no change to the four executable statements (`type_cls = …`, `definition = …`, `field_map = …`, `return …`), the signature, or the return annotation. No other file carries a hunk attributable to this pass.

### High:

None.

### Medium:

None.

### Low:

#### The paragraph's untouched first half still states an absolute that the walker's own consumers falsify, and the new contrast sentence leans on it

`django_strawberry_framework/optimizer/walker.py::_resolve_field_map` #"Both shapes are read via" (walker.py:308-310, **not** in this diff) reads "Both shapes are read via ``getattr(..., default)`` downstream -- that defensive access is the ONLY reason the two coexist safely". Measured against the actual consumers, that is false as an absolute. Plain, non-`getattr` attribute reads of field-map-derived values, **8 occurrences** across the walker:

- `field.name` — walker.py:181 (`_relation_strategy`'s debug log)
- `f.name` — walker.py:547 (the custom-pk scan; its sibling `attname` read *is* `getattr`-defensive, the `name` read is not)
- `django_field.is_relation` — walker.py:566, walker.py:1168
- `django_field.related_model` — walker.py:735, :746, :798, :913

Every one is safe, and safe for a reason the sentence does not state: those four attributes exist on **both** shapes (`FieldMeta.name` / `.is_relation` / `.related_model` are declared fields on `optimizer/field_meta.py::FieldMeta`, and a raw Django field carries all three). The load-bearing invariant is the sentence's own *next* clause — "never read a ``FieldMeta``-only attribute without a ``getattr`` default" — which is correct and is what a reader must obey. The absolute preceding it is a false description of the same rule.

Why it matters here rather than as generic pre-existing drift: R2's new sentence ends "**so its callers read attributes directly and need no ``getattr`` default**", which by contrast asserts that the walker's callers *do* need one at every read. They do not, and the wording therefore extends the imprecision instead of narrowing it. The narrow correction is to say what is actually true of both sites: attributes common to both shapes are read directly at either site; a `FieldMeta`-only attribute needs a default only on the walker's map.

**The same false absolute is in the spec bullet dispatched to R3** — `docs/SPECS/spec-016-fieldmeta_consolidation-0_0_6.md` `### Bounded exceptions to the single-source rule`, first bullet: "The two shapes coexist safely only because every downstream read is `getattr(..., default)`" — and Worker 2's recommended R3 replacement rewrites only that bullet's **closing** sentence, leaving this clause intact. So R3 would land a corrected closing sentence on top of an uncorrected premise.

**Disposition: not held against this round; escalated to Worker 1 (see `### Notes for Worker 1`).** The text is outside the one sentence Worker 0 authorized R2 to touch, and the docstring/spec pair must move together for exactly the reason the plan gave for the over-claim itself. No behavior is affected and no test expectation changes.

### The two things this round was told to verify hardest

**1. The over-claim correction is TRUE. Verified independently, not accepted from the build report.**

`django_strawberry_framework/types/resolvers.py::_field_meta_for_resolver` is annotated `-> FieldMeta` and has exactly three exits, all of which yield a `FieldMeta`:

- the canonical hit — `registry.get_definition(parent_type)` then `definition.field_map.get(field.name)`, returned only when not `None`;
- `FieldMeta._from_field_shape(field, is_relation=True)` when `not hasattr(field, "is_relation")`;
- `FieldMeta.from_django_field(field)` otherwise.

There is no branch on which a raw Django field escapes, so **no dual return shape** — the diff's central claim holds. Its consumer `types/resolvers.py::_make_relation_resolver` reads the result by plain attribute access — `field_meta.relation_kind`, `field_meta.is_many_side`, `field_meta.related_model.DoesNotExist`, `field_meta.attname` — with **zero** `getattr` defaults on `field_meta` anywhere in the function, which is only sound because the return type is unconditional. So "its callers read attributes directly and need no `getattr` default" is true as stated about the twin site.

The shared-policy half also holds: both sites prefer definition-backed metadata (`registry.get_definition(...)` -> `field_map`) and fall back when it is unreachable. `unreachable` is the right word for both — the walker's fallback fires when `registry.get(model)` / `get_definition` yields nothing, the resolver's when the definition or the entry does not resolve.

What the sentence asserts that I could **not** confirm as written is only the contrast implied about the walker side, filed as the Low above. Everything the sentence says about `_field_meta_for_resolver` is verified.

**2. No third spelling entered the package. Re-measured, occurrences not lines.**

Shortest distinctive token `_field_meta_for_resolver`, whole repo, `*.sqlite3` excluded:

| Spelling | Occurrences | Where |
|---|---|---|
| `types/resolvers.py::_field_meta_for_resolver` | 22 | 2 in package `.py` (`optimizer/field_meta.py`, `optimizer/walker.py`), 20 in specs / per-cycle artifacts / `docs/dry/` |
| `optimizer/resolvers.py::_field_meta_for_resolver` | 8 | 0 in any `.py`; all in per-cycle artifacts quoting the defect (rationale 1, build plan 3, this artifact 4) |
| `resolvers.py::_field_meta_for_resolver` (any prefix) | 30 | = 22 + 8, so **no bare-basename or third variant exists** |
| `types/resolvers::…`, `types.resolvers.…` | 0 each | — |

Package source therefore carries exactly **two** occurrences of this symbol reference and **one** spelling. `grep -rn "optimizer/resolvers" django_strawberry_framework/` -> nothing, exit 1 (3a reproduced). The chosen form is also the one `optimizer/field_meta.py::FieldMeta._from_field_shape`'s docstring already used, so the fix converged on the existing voice rather than adding a third. Rule 27 satisfied: the folder segment is load-bearing — `find django_strawberry_framework -name resolvers.py` returns **four** paths (`types/`, `forms/`, `mutations/`, `rest_framework/`), re-measured this pass.

### Dispatched findings checklist walk

- **F8 `- [x]` — tick confirmed.** The Step 2 contract landed (the reference now reads `types/resolvers.py::_field_meta_for_resolver` at walker.py:312) and 3a prints nothing. No box is unaddressed.
- **F8-sweep `- [x]` — tick confirmed, with both of its stated proof conditions re-measured and one substituted.** All four sweep commands ran and their output is in the build report. 3a and 3d reproduced exactly (both exit 1). 3b and 3c did not meet the proof conditions **as the plan wrote them**, and in both cases I re-measured and the plan is what was wrong (see below). The tick's second assertion — that no near-miss site in the disposition table was changed — is confirmed mechanically: `git status --short` reports `registry.py`, `types/converters.py`, `tests/test_registry.py`, `CHANGELOG.md`, `types/resolvers.py`, and `optimizer/field_meta.py` all **clean**, and `walker.py`'s whole diff is the one docstring hunk, so `:582` (`finalizer.py` shorthand) and `:773` (`utils.relations.instance_accessor`) are untouched.

No box is ticked without a matching fix, and no dispatched box is unaddressed.

### Worker 2's two corrections to Worker 1's plan — both re-measured, both hold

- **`git grep` cannot observe untracked files: HOLDS.** `git grep -n -I "optimizer/resolvers" -- . ':!*.sqlite3'` returns nothing, exit 1, while `git status --short` shows `?? docs/SPECS/appx/spec-016-…-rationale.md` and `?? docs/builder/build-016-…md` — the two files the plan predicted as hits — plus the artifact itself, all untracked. The plan's 3b would have returned empty **whether or not the defect survived in those files**, so as a population check it was non-distinguishing. The recursive grep is the correct instrument, exactly as the build report says.
  - One recording nit while re-measuring: the build report's "**eleven** occurrences across three files" is a line-ish count, not an occurrence count — `grep -o` gives 3 occurrences on the build plan's single line 82. Current true figures: **18 occurrences / 15 lines / 3 files** (rationale 1/1, build plan 3/1, this artifact 14/13), the artifact's share having grown because the build report itself quotes the string. The load-bearing half of the claim — **zero in any `.py`, every survivor a per-cycle artifact quoting the defect** — is correct and re-verified. Recorded as a method note, not a finding.
- **Step 3c's proof condition is stated two contradictory ways: HOLDS.** The plan's box says "PROOF: six rows, zero of them `*** UNRESOLVED ***`" and three lines later "after the fix it reports one (`:579`)". I ran the loop verbatim and got the build report's six rows byte-for-byte, including `582  ``finalizer.py::finalize_django_types``  -> *** UNRESOLVED ***`. The measured answer is **one** unresolved row, and it is a limitation of the loop (it tries only package-root-relative and `optimizer/`-sibling candidates; `find django_strawberry_framework -name finalizer.py` returns the single path `types/finalizer.py`), not a defect in the file. F8's own row prints `312  ``types/resolvers.py::_field_meta_for_resolver``  -> root-relative OK` — the fix proved by the same loop that flagged it. Worker 2's reading is right; the plan's first phrasing is unachievable.

### Recorded proofs audit

- **Failability proof: none owed, and the plan's reasoning holds.** Audited against `docs/builder/BUILD.md` `### What needs a proof, and what does not`, which scopes the obligation to a new boundary / guard / gate / rejection path and explicitly exempts doc edits. I confirmed rather than assumed that no boundary crept in: the diff adds no `if`, no comparison, no `raise`, no error message, no default argument — it contains **no expression at all**, only docstring prose, and `_resolve_field_map`'s body is byte-identical to `HEAD`. Boundary count zero, so nothing could be mutated whose removal a row could observe. Demanding a proof here would be theatre. **Empty re-run set is legal**: the mandatory floor (`worker-3.md`, every boundary with a recorded count <= 3, plus every security / data-isolation boundary) is vacuous because the diff introduces no boundary at all. Nothing was mutated by me either; no `ACTIVE-MUTATION.json` exists and my source carve-out was not exercised.
- **Fail-open shapes: none, confirmed rather than assumed.** Hunted per `BUILD.md` `### Fail-open shapes` over the diff: no clamp, no `getattr` default, no `or` fallback, no bare `except`, no truthiness test on an absent-capable value — there is no executable token in the hunk to carry one. (The `getattr`-discipline *prose* the docstring discusses is unchanged behavior, not a new shape.)
- **Hot-path budget: not owed.** Plan declares `none`; no executable statement changed, so nothing to measure. No missing-number finding.
- **Floor verification: not owed.** Plan declares scope `none`. Nothing was installed into the shared `.venv` by this pass or by mine; no floor venv was built. Floor facts as quoted from `BUILD.md` `## Floor verification`: Django **5.2.16** on Python **3.10** with strawberry-graphql **0.316.0**, and the shared `.venv` is not the floor.

### DRY findings

None. The diff adds no helper, constant, literal, branch, or parallel data flow — there is nothing to consolidate and nothing new to duplicate.

**The existence challenge — I agree with Worker 1's conclusion as it now reads in the source, having re-derived it rather than deferred to the plan.** The two sites share one *policy* (prefer definition-backed metadata; fall back when it is unreachable) and share neither a return shape nor a read discipline, which the landed wording now says explicitly. A prose pointer is the DRY-correct form for policy shared across two deliberately different implementations: a helper factoring their commonality would factor a statement, and a statement is what a cross-reference already is. The defect was the pointer's address, not its existence. The rationale companion's `*Rejected alternative.*` under the bounded-exceptions entry records closing the exceptions (make the walker's fallback build `FieldMeta`, delete the resolver fallbacks) with its two reasons, and I am not re-opening it — the walker's own docstring names the exit condition ("until the registry-coverage gate lands"), at which point the fallback disappears, the dual contract ends, and the cross-reference should be **deleted** rather than re-pointed. **No refactor is proposed, and a refactor would have been out of scope for this round regardless.**

The one shape worth watching is the sentence-level duplication this round has now created between the docstring and the spec bullet: two prose statements of one contract that must be corrected together. That is not a code DRY defect, but it is why the Low above must land in R3 as a pair.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` produces **no output**: `__all__` and the re-export list are unchanged. No new public export; nothing needing spec authorization.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md. Confirmed clean at `git status --short -- CHANGELOG.md`. Its known-stale text about this card (pre-renumber id, three stale site names, bare `extension.check_schema`) is barred by `AGENTS.md` rule 21 and is catalogued for the maintainer, not a finding against this round.

### Documentation / release sanity (only when the slice touches docs, release metadata, KANBAN, or archived specs)

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. The diff's only file is package source. Two checks made anyway because the change is a docstring: `docs/TREE.md` renders **module** docstrings and this is a **function** docstring, so no regenerate is owed; and no `#"unique substring"` citation anywhere in the repo points into the four lines the hunk replaced (the spec cites `optimizer/walker.py::_resolve_field_map` with no substring, the rationale cites #"DUAL CONTRACT (read before consuming the returned map)" at walker.py:304, above the hunk and unchanged), so the reflow the build report performed broke no citation. `KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md`, `examples/fakeshop/db.sqlite3` untouched.

### Static helper use

**Run, not skipped** — `BUILD.md` `### When to run the helper during build` requires it for a slice touching an existing `.py` under `optimizer/`:

```shell
uv run python scripts/review_inspect.py django_strawberry_framework/optimizer/walker.py --output-dir docs/shadow
```

It rewrote `docs/shadow/django_strawberry_framework__optimizer__walker.overview.md` and `….stripped.py` — this cycle's own two files (Worker 1 created them at plan time), so no concurrent session's shadow output was clobbered; `docs/shadow/helper-inventory.md` and `docs/shadow/current/` were not touched. **The build report's warning is correct and I confirm it: the helper's output is structurally blind to this diff**, because the stripper replaces every string-literal token including docstrings with `...`. Its one useful reading here is the pair of `TODO(spec-035)` anchors in walker.py, which belong to another card and are untouched by this diff. No shadow line numbers are cited anywhere in this review.

Independent staleness sweep, run against the tree rather than the artifact's file list: no example-model field set and no wire shape changed, so neither `BUILD.md` `### Test staleness a focused run cannot see` shape applies. `grep -rn "_resolve_field_map\|DUAL CONTRACT\|__doc__" tests/ examples/` finds one hit, a test's own explanatory comment at `tests/optimizer/test_walker.py:2105`, asserting nothing about this docstring.

### No `pytest` run, and what that decision rests on

No focused run, and I can name why rather than leaving it implicit: there is no assertion anywhere in the three test trees whose pass/fail this diff can change, because the diff contains no executable token. A focused run would prove only that an unrelated suite is green, which is not a claim this review needs. No coverage-shaped flag was used in this pass.

### What looks solid

- The fix converged on the spelling two already-correct sites use instead of inventing a third, and that is now measurable: one spelling, two `.py` occurrences, zero of the wrong form in any `.py`.
- Worker 2 verified the over-claim in its own words before rewriting it and reached the same reading I did from an independent read of `types/resolvers.py` — the three-exit enumeration and the no-`getattr`-defaults consumer are both accurate.
- Both plan errors were caught by the builder rather than propagated, and both are stated in a form the next reader can re-measure. That is the failure mode `BUILD.md` warns about (a prescribed step is a hypothesis) being handled correctly.
- The reflow decision is defensible against the plan's no-reflow rule: the rule was written for an address-only fix, the sentence's substance is what changed, and the reflow broke no `#"substring"` citation (checked independently).
- ASCII-only holds (`--` not an em dash, matching the paragraph's existing style); longest new line 74 characters, inside the limit.
- No near-miss site was "helpfully" fixed. `walker.py:582` and `:773`, `registry.py:6`, `types/converters.py:409`, `tests/test_registry.py:504`, `CHANGELOG.md:221` are all as they were, each with a recorded reason.

### Temp test verification

None created. `docs/builder/temp-tests/` holds a concurrent session's live output and was not read into or written. A temp test could not demonstrate anything about a docstring, and manufacturing one would be activity rather than verification.

### Notes for Worker 1 (spec reconciliation)

1. **Escalated: the R3 spec edit needs a second clause corrected, not only the closing sentence — and the docstring's untouched half with it.** See `### Low:` for the measurement (8 plain non-`getattr` reads of field-map values in the walker). The premise clause in `docs/SPECS/spec-016-fieldmeta_consolidation-0_0_6.md` `### Bounded exceptions to the single-source rule`, first bullet — "The two shapes coexist safely only because every downstream read is `getattr(..., default)`" — is false as an absolute in the same way the closing sentence was, and Worker 2's recommended replacement leaves it standing. Resolution paths for the custodian to pick between:
   - **(a) Correct both clauses in R3, in both files.** The bullet's premise becomes the true invariant — attributes common to both shapes are read directly; a `FieldMeta`-only attribute must never be read off the map without a default — and `walker.py::_resolve_field_map` #"Both shapes are read via" is corrected to match in the same change. This needs a second authorized source edit in R3, which R2 did not have.
   - **(b) Correct the spec in R3 and carry the docstring half to the next residual cycle.** Cheaper, but it re-creates exactly the split-across-rounds condition Worker 0's mid-flight instruction rejected for this same sentence, and leaves code and spec disagreeing again.
   - **(c) Accept both as coarse-but-directionally-right prose.** Defensible for the docstring alone, weaker now that R3 is already editing the neighbouring sentence for precision: correcting one half of one bullet while leaving its premise false is the outcome hardest to justify to the next auditor.
   My recommendation is **(a)**. Either way, Worker 2's landed wording and its recommended spec replacement **are consistent with each other and with what I verified** — the inconsistency is between the recommendation and the clause it does not touch, not between the two documents' new sentences.
2. **The plan's Step 3b and Step 3c defects both hold** (build-report notes 2 and 3 confirmed by independent re-measurement, above). Neither should be copied into R3 or the final gate. The 3c loop resolves only root-relative and `optimizer/`-sibling paths, so it reports `types/finalizer.py` shorthand as unresolved forever; any reuse must either resolve `types/`-relative paths or name the expected row. A population sweep must not be `git grep` while this cycle's own artifacts are untracked.
3. **`grep -o` counts occurrences; `grep -c` counts lines.** The build report's "eleven occurrences" is the latter shape wearing the former's name (true current figures 18 / 15 / 3, and the artifact's own share keeps growing as passes quote the string). No conclusion changes — zero in `.py` is the load-bearing half and it is verified — but the final gate should not quote the number forward.
4. **The final gate should certify by tree object.** `HEAD` rotted twice this cycle (`d94db992` -> `ded4b00c` -> `ab821ae0`, the second time by rebase) while the tree stayed `7debb73f`. I certified against `git rev-parse HEAD^{tree}` and recommend the gate do the same; `merge-base --is-ancestor` mis-reports this tree as new work.
5. **No refactor of the two dual-contract sites is proposed** — the existence challenge is answered above, in agreement with the plan and the rationale's recorded rejected alternative. Recorded so silence is not mistaken for the question going unasked, and so the deferred catalog carries the exit condition: when the registry-coverage gate lands, the walker's fallback disappears and this cross-reference should be **deleted**, not re-pointed.

### Review outcome

`review-accepted`. No High and no Medium findings. The one Low is escalated to Worker 1 with resolution paths (it is text outside the sentence R2 was authorized to touch, and it must move as a docstring/spec pair for the same reason the over-claim itself did), so nothing is held open against this round. Both dispatched boxes are ticked with matching landed work, both of the builder's corrections to the plan hold, no failability proof is owed and none was needed, the public surface is unchanged, and the package now speaks with one measured voice about `types/resolvers.py::_field_meta_for_resolver`.

---

## Final verification (Worker 1)

`Status: revision-needed`. The round's own work is correct and every dispatched tick is honest; the round is re-opened for **one wording change in the same paragraph R2 already edited**, whose exact replacement text is fixed below. Reason in one line: **Worker 3's escalated Low is upheld on my own re-measurement, and R2's newly landed sentence depends on the false premise for its meaning**, which converts pre-existing drift into drift this round extended.

### Spec status-line re-verification

Performed at spawn per `docs/builder/worker-1.md` `## Spec status-line re-verification (every Worker 1 spawn)`. `docs/SPECS/spec-016-fieldmeta_consolidation-0_0_6.md` lines 1-7 (title, `Target release: 0.0.6 (per KANBAN.md card DONE-016-0.0.6)`, `Status: shipped.`, `Owner: package maintainer.`, the rationale-companion pointer) **still describe the build's current state**; R1 rewrote them this cycle and nothing since has falsified one. No edit owed, none made. No reference to a predecessor doc this build deleted survives. The spec is **not** edited in this pass — the spec half of the ruling belongs to R3, by the same pair-in-one-commit logic that produced R2's mid-flight instruction.

### HEAD certified by BLOB, not by tree — the method note is upheld and then superseded

Worker 3's note 4 (certify by tree object, not commit hash) is **confirmed correct in direction and proven insufficient in granularity, by three tree moves inside this single pass.**

| Commit | Tree | `walker.py` blob | Certified by |
|---|---|---|---|
| `ab821ae0` (plan / build / review) | `7debb73f` | `1030b037` | plan, build report, review |
| `6b42c8d2` `fix(optimizer): reverse expression order terms …` | `6de32219` | `1030b037` | landed mid-pass |
| `76fdeac3` `docs(review): optimizer review artifacts, all 14 files cleared` | `4c207c7a` | `1030b037` | landed mid-pass |
| `fa248bdf` `move files;` (**HEAD at this pass's end**) | `b00e7846` | `1030b037` | this pass |

Three concurrent commits landed **during this verification pass**. The commit hash rotted a third time, and this time **the tree object rotted too** — so the tree test Worker 3 recommended would have reported drift and been wrong about content for the third time in one cycle. The invariant that actually held is the **blob object of the file under review**: `git rev-parse <commit>:django_strawberry_framework/optimizer/walker.py` is `1030b037b2db85290eeb45bde92c55b865cf6f42` at all four commits, so every reading the plan, the build report, and the review took is still valid.

**Carried to the final gate as the corrected method rule:** certify a pass's readings by `git rev-parse HEAD:<path>` for each file the pass reads, and record the blob. A tree object is the right instrument only for a claim about the whole tree; for a claim about one file it is strictly noisier than the blob and generates false drift alarms in a concurrently-committed repo. Quote no commit hash as a content certificate.

`git stash`, `git checkout`, `git restore`, `git worktree` used **nowhere** in this pass. Every `HEAD` reading went through `git show HEAD:<path>` into a scratch path outside the repository, `git rev-parse`, or `git diff`.

### A concurrent session has STAGED this round's hunk — read the diff with `git diff HEAD`, not `git diff`

**Recorded first because it silently breaks the audit instrument the pass is required to use.** The dispatch (and `## Final verification job` step 3) names `git diff -- django_strawberry_framework/optimizer/walker.py`. That command **returns empty output** at this pass's end. The file is not clean and the fix is not lost: `git status --short` reports `M ` — **staged**, index equal to worktree — so `git diff` (worktree vs index) has nothing to show while `git diff --cached` and `git diff HEAD` both show the hunk. Nobody in this build staged it; `git add` is in no round's writable procedure and Worker 2 recorded none.

**And it is not only `walker.py`.** `git diff --cached --name-status` reports **32 staged paths** — a blanket `git add -A`-shaped sweep, not a targeted stage. It has swept **this cycle's entire output** (`M docs/SPECS/spec-016-…md`, `A docs/SPECS/appx/spec-016-…-rationale.md`, `A docs/builder/build-016-…md`, `A docs/builder/bld-016-r1-…md`, `A docs/builder/bld-016-r2-…md`, `M …/optimizer/walker.py`) **together with both concurrent sessions' WIP** (`mutations/resolvers.py`, `orders/inputs.py`, `orders/sets.py`, `relay.py`, `debug_toolbar.html`, 14 `A docs/review/rev-*.md`, `review-0_0_14.md`, and six test files). This is exactly the hazard the standing rules name in both directions at once — START.md's *stage explicitly, never `git add -A`* and *your uncommitted edits may land in their commit*.

Three consequences, none of them remediable by this pass:

1. **This round's hunk — and every artifact of this cycle — is one `git commit` away from landing inside a concurrent session's commit, while the round is `revision-needed`.** Nothing is done about it here: unstaging is `git restore --staged` / `git reset`, which is not in this pass's writable set, is a mutation of another session's index state, and is barred by the method rules. **Flagged to the maintainer** as the one thing about this round that wants a human decision rather than a worker action. A `git commit` on this index right now would ship an un-reviewed docstring the pass has just ruled `revision-needed`, in a commit whose message describes someone else's work.
2. **`git diff -- <path>` is not a sound audit instrument in this tree.** Every remaining pass in this cycle must use `git diff HEAD -- <path>`. A pass that used the bare form would have concluded the file was clean and the fix absent.
3. The near-miss-site cleanliness check has the same trap; it was run as `git diff HEAD --name-only` below rather than on `git status` alone.

### The ruling on Worker 3's escalated Low: the wording MUST change

**Re-measured from source, not accepted from the review.** Worker 3's count is a claim like any other, and it is **low by two occurrences**.

Population: plain, non-`getattr` attribute reads of a value taken out of `_resolve_field_map`'s returned `field_map`. Established by grepping every identifier that holds one (`django_field.`, bare `field.` inside the dual-contract helpers, `f.` / `db_field.` over `field_map.values()`), then reading each hit's provenance rather than pattern-matching it.

| Site | Read | Holder's provenance |
|---|---|---|
| `walker.py:181` | `field.name` | `plan_relation`, called at `:631` as `plan_relation(django_field, …)` |
| `walker.py:376` | `field.related_model._default_manager` | `_build_child_queryset`, called at `:875` as `_build_child_queryset(django_field, …)` — **missed by Worker 3** |
| `walker.py:547` | `f.name == id_attr` | comprehension over `field_map.values()`; its sibling `getattr(f, "attname", None)` on the same line *is* defensive |
| `walker.py:566` | `django_field.is_relation` | `field_map.get(django_name)` |
| `walker.py:735` | `django_field.related_model` | same |
| `walker.py:746` | `django_field.related_model` | same |
| `walker.py:749` | `django_field.related_model` | same — **missed by Worker 3** (its `:746` entry counts the line, not the two occurrences on `:746`/`:749`) |
| `walker.py:798` | `django_field.related_model` | same |
| `walker.py:913` | `django_field.related_model` | same |
| `walker.py:1168` | `django_field.is_relation` | same |

**10 occurrences across 10 lines, over 3 distinct attributes** (`related_model` x6, `is_relation` x2, `name` x2). Worker 3 recorded **8**, and also wrote "those **four** attributes" while enumerating three — a slip in the same direction as the round's earlier line-vs-occurrence slip. The two additional occurrences are found only by resolving `field`-named parameters back to their call sites (`:376`) and by counting occurrences rather than lines (`:749`), which are precisely the two disciplines this cycle has already had to correct twice. **The finding is strengthened, not weakened, by re-measurement.**

Against that, the defensive population: `getattr(django_field, "related_model", None)` at `:340`, `getattr(django_field, "attname", None)` at `:851`, `getattr(db_field, "attname", None)` at `:563`, `getattr(f, "attname", None)` at `:547`, and `getattr(field, "python_name"/"graphql_name"/"name", …)` at `:205`/`:211`/`:236`.

**So the premise is false as stated, and Worker 3's identification of the true invariant is correct.** `walker.py:307-309` reads "Both shapes are read via ``getattr(..., default)`` downstream -- that defensive access is the ONLY reason the two coexist safely". Both halves fail: the reads are *not* all `getattr`-defaulted (10 are not), and defensive access is therefore *not* the only reason the shapes coexist safely — the other reason is that the attributes read directly are present on both shapes. The load-bearing invariant is the sentence's own next clause, "never read a ``FieldMeta``-only attribute without a ``getattr`` default", which is correct and is what a consumer must actually obey.

One refinement on Worker 3's phrasing, which I do not adopt verbatim: it justifies the plain reads by asserting the attributes "exist on **both** shapes". That is proven for `name` and `is_relation` — `optimizer/field_meta.py::_DjangoFieldLike`'s docstring is the standing guarantee ("Every Django ``Field`` and reverse-relation descriptor surfaced by ``Model._meta.get_field`` / ``Model._meta.get_fields`` guarantees ``name`` and ``is_relation``"), and `FieldMeta` declares both. For `related_model` it is *assumed rather than guaranteed*: `FieldMeta` declares it, but the module itself hedges the raw shape at `:340` with `getattr(django_field, "related_model", None)`, and `_DjangoFieldLike` deliberately does not promise it. The replacement text below therefore states the **rule** and names only the two guaranteed attributes, rather than publishing a three-item safe-list the module's own code contradicts. Writing a closed list here would recreate the exact defect being fixed.

#### Why this outweighs the cost of re-opening a reviewed file

Weighed as the maintainer would, both directions stated:

- **Against re-opening.** Two concurrent sessions are working near `optimizer/`, and one of them committed `fix(optimizer): …` *during this pass*; a wording churn costs an apply pass and a re-review; the false premise predates this cycle and misdirects no builder into a defect.
- **For re-opening, and decisive.** (1) **R2's own new sentence leans on the false contrast.** "so its callers read attributes directly and need no ``getattr`` default" is meaningful only against a premise that the walker's callers *do* need one at every read — which 10 occurrences falsify. This round therefore did not merely fail to fix pre-existing drift, it **extended** it, and that is the one case where "pre-existing" stops being a defence. (2) The paragraph is labelled `DUAL CONTRACT (read before consuming the returned map)` — an instruction to a consumer to obey it. This repo's standing rule is that a comment states the invariant; a false invariant in the one place a reader is told to obey is the highest-cost location for this class of error, not a cosmetic one. (3) **The cost is bounded and small.** The correction is contiguous with the hunk R2 already landed, in the same paragraph of the same docstring, so it is one hunk and not two; the file's baseline blob is provably unchanged across four commits (`1030b037`), so the concurrency risk here is measured rather than feared; and the round adds no executable statement either before or after.
- **Rejected: Worker 3's option (c)** (accept both as coarse-but-directionally-right). Correcting one sentence of a bullet for precision while leaving its premise false is the outcome hardest to defend to the next auditor, and Worker 3 says so. **Rejected: option (b)** (spec now, docstring later) — it re-creates the split-across-rounds condition Worker 0's mid-flight instruction already rejected for this same sentence. **Adopted: option (a)**, both clauses, both files, the source half in a re-dispatched R2 and the spec half in R3.

#### Exact replacement text — the walker docstring (for Worker 2; no wording discretion)

Target: `django_strawberry_framework/optimizer/walker.py::_resolve_field_map`, its `DUAL CONTRACT` paragraph. **Lines 304-306 are NOT touched** (`DUAL CONTRACT (read before consuming the returned map): the values` / `are ``FieldMeta`` when the model has a registered ``DjangoType``, but` / `raw Django field objects (from ``model._meta.get_fields()``) on the`). Replace **exactly lines 307-317** — the block that currently begins `fallback path when it does not. Both shapes are read via` and ends `differ by design.` — with exactly this, four-space indent preserved:

```
    fallback path when it does not. ``name`` and ``is_relation`` are
    guaranteed on both shapes (``field_meta.py::_DjangoFieldLike``) and are
    read directly; any other attribute is read directly only where both
    shapes carry it, and a ``FieldMeta``-only attribute must never be read
    off this map without a ``getattr(..., default)``. That rule, not a
    blanket ``getattr`` discipline, is what lets the two shapes coexist
    safely. Treat the values as ``FieldMeta | Any`` until the
    registry-coverage gate lands.
    ``types/resolvers.py::_field_meta_for_resolver`` shares the policy --
    prefer the canonical definition-backed metadata, fall back when it is
    unreachable -- but not this dual return shape: it returns a
    ``FieldMeta`` unconditionally, so its callers read every attribute
    directly. Keep the policy in sync; the shapes differ by design.
```

Every property that governed the text was measured, not assumed:

- **ASCII-only** (`AGENTS.md` rule 17): verified byte-wise, no character outside `0x20-0x7E`; `--` for the parenthetical dashes, matching the paragraph's existing style.
- **Line lengths** 33-75, longest 75, inside the 100 limit with no reliance on the 110 grace.
- **`field_meta.py::_DjangoFieldLike` is the correct citation and the correct spelling.** The symbol exists at `optimizer/field_meta.py:39` and its docstring is the guarantee being cited. `find django_strawberry_framework -name field_meta.py` returns **exactly one** path, and it is an `optimizer/` sibling of `walker.py`, so the bare-basename form matches walker.py's four existing sibling refs (`extension.py::`, `nested_fetch.py::`, `finalizer.py::`, `plans.py::`) and rule 27's `path::QualifiedName` shape. This is the round's acquitted house-style convention being *used*, not a new spelling.
- **No third spelling of `_field_meta_for_resolver`**: the reference `types/resolvers.py::_field_meta_for_resolver` is carried through verbatim from what R2 landed.
- **`getattr(..., default)`** is written with its argument ellipsis, matching the form the paragraph already uses at `:308`, rather than the bare `getattr` R2's sentence used.
- The sentence R2 landed keeps its substance; only "read attributes directly and need no ``getattr`` default" becomes "read every attribute directly", which drops the false implied contrast while keeping the true statement about the twin site (verified independently below).

**Reflow is required here, unlike in R2.** The plan's no-reflow rule was written for an address-only fix and Worker 2 correctly judged it to stop governing once a sentence's substance changes; the same judgment applies again and is now the plan's, not Worker 2's discretion.

#### The `#"substring"` citation this reword breaks — and its required disposition

Standing rule (this cycle's own carried lesson): **a `spec-NNN #"substring"` citation breaks on reword AND on reflow; grep-sweep as pre- and postcondition.** Swept before fixing the text, which is what caught it:

- **`docs/builder/DONE/build-004-optimizer_beyond-0_0_3.md:257`** cites `walker.py` **#"ONLY reason the two coexist safely"** — the exact clause being deleted. The file is **tracked and clean**, under `docs/builder/DONE/`, i.e. a retained archived record and *not* a per-cycle `bld-*.md` scratchpad, so START.md's scratchpad exemption does not cover it. The citation cannot be preserved by choosing gentler wording: the cited substring **is** the false clause.
  - **Required disposition:** re-point it to **#"lets the two shapes coexist"** — corrected by Worker 1 at final verification of pass 2, on Worker 3's escalated Low. The longer form first written here, **#"lets the two shapes coexist safely"**, contains the words the replacement text carries but **spans the line break** the replacement's own wrapping introduced (`walker.py:312`/`:313`), so it greps to zero: `grep -c 'lets the two shapes coexist safely' django_strawberry_framework/optimizer/walker.py` -> `0`, exit 1, while `grep -c 'lets the two shapes coexist'` -> `1` at `walker.py:312`. A citation that greps to zero is broken whether the break came from a reword or a reflow, and recording an unexecutable re-point target inside a *decided* deferral would have reproduced the class of defect F8 fixed. The corrected form is unique and single-line. The same D23 row is making the same point with it. This is a one-substring edit on one line and it must land in the **same change** as the docstring reword, or the archived record is left dangling.
  - **`docs/builder/DONE/build-004-optimizer_beyond-0_0_3.md` is in no round's writable set.** Worker 0 must add it to the re-dispatched R2's writable set (it is the round whose edit breaks the citation), or record the deferral explicitly. Recorded here so the choice is made rather than defaulted.
- Everything else surviving a sweep for `Both shapes are read via` / `ONLY reason the two coexist` / `registry-coverage gate` / `Keep the policy in sync` is either this cycle's own per-cycle artifact (exempt), `docs/dry/dry-0_0_11.md` (exempt per-cycle, and its two hits paraphrase the gate rather than cite a substring), or the rationale companion at `:263`, which quotes only **#"until the registry-coverage gate lands"** — ~~a phrase the replacement **preserves verbatim**, so it does not break.~~ **Corrected by Worker 1 at final verification of pass 2, on Worker 3's escalated Low: the clearance was measured phrase-wise, not line-wise, and it does not hold.** The words survive but the replacement's wrapping moved them across a line boundary (`walker.py:313`/`:314`), so `grep -c 'until the registry-coverage gate lands'` -> `0`, exit 1; the greppable form is **#"registry-coverage gate lands"** (`grep -c` -> `1`, `walker.py:314`). The rationale's use is narrative prose quotation rather than a rule-27 citation, so nothing normative broke — but the clearance's stated basis was wrong, and the companion's quotation is re-pointed to the greppable form in R3. `docs/SPECS/appx/…-rationale.md`'s other citation, #"DUAL CONTRACT (read before consuming the returned map)", is `walker.py:304` and outside the replaced block.

#### Exact replacement text — the spec bullet (Worker 1 lands this in R3; NOT edited in this pass)

Target: `docs/SPECS/spec-016-fieldmeta_consolidation-0_0_6.md` `### Bounded exceptions to the single-source rule`, **first** bullet (**The walker's dual contract**), currently the whole of line 34. Both defective clauses are on that one line — the premise Worker 3 escalated *and* the closing sentence Worker 2 recommended replacing — so it is replaced whole rather than sentence-wise. Replace the entire bullet with exactly:

```
- **The walker's dual contract.** `optimizer/walker.py::_resolve_field_map` returns `FieldMeta` values for a model with a registered `DjangoType` and **raw Django field objects** from a `model._meta.get_fields()` walk for a model without one. `name` and `is_relation` are guaranteed on both shapes (`optimizer/field_meta.py::_DjangoFieldLike`) and are read directly; any other attribute is read directly only where both shapes carry it, and a `FieldMeta`-only attribute must never be read off that map without a `getattr(..., default)`. That rule, not a blanket `getattr` discipline, is what makes the two shapes safe to coexist. The site's docstring is the standing statement of this contract. `types/resolvers.py::_field_meta_for_resolver` shares the policy (prefer the canonical definition-backed metadata, fall back when it is unreachable) but not this dual return shape: it returns a `FieldMeta` unconditionally, so its callers read every attribute directly.
```

- **Root-relative refs** (`optimizer/field_meta.py::_DjangoFieldLike`), matching the section's existing `optimizer/walker.py::` / `types/resolvers.py::` form, not walker.py's sibling shorthand.
- **The second bullet (Test-double fallbacks) still needs no edit.** Worker 2's reading is right and worth preserving in the record: it already states the fallbacks "produce a `FieldMeta` observably identical to the canonical builder's on the same descriptor", which is the fact that falsified the first bullet's original claim. The spec contained its own refutation two bullets apart.
- **R3's own obligations on landing it:** `scripts/check_spec_glossary.py` still exits 0; every in-page anchor still resolves; the `### Bounded exceptions` heading is cited from `spec-016-…-rationale.md` and from this artifact by heading name, which the replacement does not change. Re-run the substring sweep as the **post**condition too.

### Audit of every `- [x]` tick against the diff

Run against `git diff HEAD -- django_strawberry_framework/optimizer/walker.py` (see the staging note above for why the bare form is unsound here). **Both ticks stand; neither is an over-tick; no open box needed ticking.**

- **`- [x]` F8 — tick CONFIRMED, re-derived.** The diff is exactly one hunk, `-4 / +7`, entirely inside `::_resolve_field_map`'s docstring. `grep -rn "optimizer/resolvers" django_strawberry_framework/` prints nothing, **exit 1** (3a reproduced independently). `grep -rIn --include='*.py' -o '[a-zA-Z_/.]*resolvers\.py::_field_meta_for_resolver' .` returns **exactly two occurrences, both the one correct spelling** — `optimizer/walker.py:312` and `optimizer/field_meta.py:204`. Contract landed.
- **`- [x]` F8-sweep — tick CONFIRMED, including its second assertion.** All four sweep commands ran with output pasted; 3a and 3d reproduced (both exit 1). The "no near-miss site was changed" assertion is confirmed **mechanically and by content**: `git diff HEAD --name-only -- django_strawberry_framework/` lists `mutations/resolvers.py`, `optimizer/walker.py`, `orders/inputs.py`, `orders/sets.py`, `relay.py`, `templates/…/debug_toolbar.html` — every entry but `walker.py` a plan-declared baseline-dirty path, and `registry.py`, `types/converters.py`, `types/resolvers.py`, `optimizer/field_meta.py`, `tests/test_registry.py`, `CHANGELOG.md` all absent from it. By content: `registry.py:6` still carries `types.converters.resolved_relation_annotation`, `types/converters.py:409` still `types/base._build_annotations`, `tests/test_registry.py:504` still `_record_pending_relation`, `walker.py:582` still the `finalizer.py::` shorthand, `walker.py:773` still `utils.relations.instance_accessor`. Nothing was helpfully fixed.

**No box remains `- [ ]`**, so no deferral reason is owed under step 3. The two boxes are the round's whole dispatched scope; the wording ruling above is a *new* obligation created by this pass, not an un-ticked box, and is dispatched as such.

**Required-amendment lists discharged** (`## Review-round custody`): Worker 0's one mid-flight amendment — correct the same sentence's over-claim in the same edit as F8 — is on disk in the diff, not merely recorded. Confirmed present.

### Re-derivation of the round's own claims

Each re-derived rather than accepted:

- **No executable statement changed.** `git diff HEAD -U0 -- …walker.py` filtered to `^[+-]` lines yields **only docstring prose**; `_resolve_field_map`'s four statements (`type_cls = …`, `definition = …`, `field_map = …`, `return …`), its signature, and its return annotation are byte-identical to `HEAD`. The hunk contains no expression, no `if`, no `raise`, no default argument. **Boundary count zero confirmed**, so no failability proof is owed and none is missing; **no fail-open shape** could be introduced by a hunk with no executable token. Both of `## Failability and fail-open checks`' confirmations discharged.
- **Chosen spelling matches the already-correct sites; no third spelling exists.** Whole-repo occurrence census (occurrences, not lines, `*.sqlite3` excluded): `types/resolvers.py::_field_meta_for_resolver` **22**; `django_strawberry_framework/types/resolvers.py::…` **5** (the same spelling under a repo-root prefix, docs only, not a variant of the package-relative ref); `optimizer/resolvers.py::…` **9**, every one in a per-cycle artifact quoting the defect and **zero in any `.py`**; apparent bare `resolvers.py::…` **1**, which resolves on reading to Worker 3's own table cell *describing* the pattern rather than a reference; dotted `types.resolvers._field_meta_for_resolver` and `types/resolvers::…` **0 each**. Package source carries **2 occurrences and 1 spelling**. Rule 27's folder segment is load-bearing here: `find django_strawberry_framework -name resolvers.py` returns **four** paths (`types/`, `forms/`, `mutations/`, `rest_framework/`), re-measured.
- **No baseline-dirty path was edited or reverted.** The six package paths differing from `HEAD` are enumerated above; five are plan-declared baseline-dirty and none carries a hunk attributable to this build. Note for the record that `optimizer/extension.py`, `optimizer/nested_planner.py`, `optimizer/plans.py`, and `optimizer/selections.py` **left** the dirty set during this pass — they were **committed** by `6b42c8d2`, not reverted by anyone; the dirty count fell 58 -> 36 for that reason. A falling dirty count in this tree is not evidence of a revert, and this pass performed none.
- **Public surface untouched.** `git diff HEAD --stat -- django_strawberry_framework/__init__.py` produces no output. `__all__` and the re-export list are unchanged; no new public export needs spec authorization.
- **The over-claim correction R2 landed is TRUE about the twin site**, re-derived from `types/resolvers.py`: `::_field_meta_for_resolver` is annotated `-> FieldMeta` with three exits (canonical `definition.field_map.get(field.name)` when not `None`; `FieldMeta._from_field_shape(field, is_relation=True)` when the descriptor lacks `is_relation`; `FieldMeta.from_django_field(field)` otherwise), none of which lets a raw Django field escape. `FieldMeta` is a `@dataclass(frozen=True, slots=True)` declaring `name`, `is_relation`, `related_model`, `attname`, and the rest, so its consumers' plain reads are sound by the type, not by luck. **No dual return shape at the twin site: confirmed.** Only the *implied contrast about the walker* was wrong, which is the ruling above.
- **No spec-016 staged anchor survives anywhere.** `grep -rIn -E 'TODO\(spec-016|TODO-(ALPHA|BETA|STABLE)-016' .` outside this cycle's own artifacts returns nothing, exit 1. Walker.py's two `TODO(spec-035)` anchors belong to another card and are both still present and untouched.
- **The plan's two defects both hold**, as Worker 2 found and Worker 3 confirmed, and neither is copied forward: Step 3b's `git grep` cannot see untracked files and is therefore non-distinguishing as a population check while this cycle's artifacts are untracked; Step 3c states its proof condition two contradictory ways, and the measured answer is one `*** UNRESOLVED ***` row, which is the loop's inability to resolve `types/`-relative shorthand rather than a defect in the file.

### Method notes confirmed and carried to the final gate

Both of Worker 3's notes are upheld, one of them with a correction:

1. **"Eleven occurrences" was a line-ish count, not an occurrence count. CONFIRMED.** Current census of `optimizer/resolvers`: **21 occurrences / 18 lines / 3 files** (this artifact 17/16, the build plan 3/1, the rationale companion 1/1). Worker 3 measured 18/15/3 at its pass and was right then; the artifact's share grows every time a pass quotes the string, which is why **no pass may quote this number forward** — it is a moving figure about the artifacts, not about the code. The load-bearing half is stable and re-verified: **zero occurrences in any `.py`**, `grep` exit 1. `grep -o` counts occurrences; `grep -c` counts lines; a stated count is an occurrence count.
2. **Certify HEAD content by tree object rather than commit hash. CONFIRMED IN DIRECTION, CORRECTED IN GRANULARITY.** The commit hash moved a third time (`d94db992` -> `ded4b00c` -> `ab821ae0` -> `6b42c8d2` -> `76fdeac3` -> `fa248bdf`) and **the tree moved with it** this time (`7debb73f` -> `6de32219` -> `4c207c7a` -> `b00e7846`), so a tree-object certificate would have raised a false drift alarm. The **blob object of the file under review** is the instrument that held: `1030b037` for `walker.py` at all four commits. The final gate certifies per-file blobs. See the table above.

A third note is added by this pass and matters as much as either: **`git diff -- <path>` silently reports a staged file as clean.** Use `git diff HEAD -- <path>`. This pass would have concluded the fix was absent otherwise.

### Deferred work — the complete catalog input from this round

Recorded so the final gate's `### Deferred work catalog` can be assembled from artifacts alone. Nothing here is a defect in shipped behavior.

1. **`tests/test_registry.py:504`** names the deleted `_record_pending_relation` (deleted at `f83bb71b`) in a comment. Tests are outside every round's writable set this cycle. Verified still present and the file still clean.
2. **`CHANGELOG.md:221`** carries the pre-renumber card id **plus** three stale site names **plus** a bare `extension.check_schema` (the symbol is `optimizer/extension.py::DjangoOptimizerExtension.check_schema`). Wider than F12 recorded. `AGENTS.md` rule 21 bars the edit; maintainer decision. File verified clean.
3. **`django_strawberry_framework/registry.py:6`** spells `` `types.converters.resolved_relation_annotation` `` where rule 27 requires `types/converters.py::resolved_relation_annotation`. Clean, outside every round's writable set.
4. **`django_strawberry_framework/types/converters.py:409`** spells `` `types/base._build_annotations` `` where rule 27 requires `types/base.py::_build_annotations`. Same class, same reason.
5. **`django_strawberry_framework/optimizer/walker.py:773`** carries `` `utils.relations.instance_accessor` `` (dotted). In the file this round owns, but `instance_accessor` (`utils/relations.py:550`) is not a spec-016 symbol; fixing it is scope creep into another card.
6. **The bare-basename cross-folder shorthand is house style, ACQUITTED, ~12 sites** — each resolving because the basename is unique package-wide (`connection.py:401`, `keyset.py:185`, `utils/connections.py:184,445,446,447`, `utils/querysets.py:2790,2981`, `filters/inputs.py:738`, `rest_framework/resolvers.py:1860`, `optimizer/walker.py:121,377,740`, plus `walker.py:582`). Recorded so a later sweep does not "fix" one instance and fracture the convention. `walker.py:582`'s `finalizer.py::` was seen and deliberately passed while `:313` was fixed, because `resolvers.py` is four-way ambiguous and `finalizer.py` is not. **This pass's replacement text uses the same convention** for `field_meta.py::_DjangoFieldLike`, which is the convention being applied, not breached.
7. **The Step 3c reference-resolution loop resolves only package-root-relative and `optimizer/`-sibling paths**, so it reports `types/`-relative shorthand (`finalizer.py`) as unresolved forever. Any reuse must resolve `types/`-relative paths too or name the expected row explicitly, or it will read a correct file as defective.
8. **`scripts/review_inspect.py`'s output is structurally blind to a docstring change** — it strips comments and replaces every string-literal token including docstrings with `...`. A clean shadow overview is not evidence about this diff.
9. **The dual contract's exit condition, for the catalog:** when the registry-coverage gate lands, the walker's fallback disappears, the dual contract ends, and this cross-reference should be **deleted** rather than re-pointed — along with the whole `DUAL CONTRACT` paragraph and the spec's first bounded exception. The rationale companion's recorded rejected alternative (make the walker's fallback build `FieldMeta`, delete the resolver fallbacks) stays rejected; I re-derived the existence challenge and agree with the plan and Worker 3: the two sites share a policy, not a shape, and a prose pointer is the DRY-correct form for that. No refactor is proposed.
10. **`docs/builder/DONE/build-004-optimizer_beyond-0_0_3.md:257`'s `#"ONLY reason the two coexist safely"` citation** must be re-pointed in the same change as the docstring reword (see the disposition above). If Worker 0 declines to add the file to R2's writable set, this becomes a deferred item and the archived record is knowingly left dangling — record which.
11. **A concurrent session has staged `walker.py`.** Maintainer-facing; no worker may unstage it. See the staging note.

### DRY re-check against prior accepted rounds

None owed and none found. R1 edited only the spec and its companion; R2 adds no helper, constant, literal, branch, or parallel data flow, and the replacement text above adds none either. The one shape shared across rounds is the *sentence pair* — the docstring paragraph and the spec bullet, two prose statements of one contract that must be corrected together — which is precisely why the ruling dispatches both halves with fixed text rather than leaving either to a writer's discretion.

### Focused test run

**None run, and the reason is structural rather than a skip.** No assertion in any of the three test trees can change pass/fail on a hunk containing no executable token; `grep -rn "_resolve_field_map\|DUAL CONTRACT\|__doc__" tests/ examples/` finds one hit, `tests/optimizer/test_walker.py:2105`, which names `_resolve_field_map(Item)` inside a test's own explanatory comment and asserts nothing about the docstring. `docs/builder/BUILD.md` `## Coverage is the maintainer's gate, not a worker's tool`: no coverage-shaped flag was used anywhere in this pass. Hot-path budget not owed (plan declares none; nothing executable changed). Floor verification not owed — **no floor-verification scope was declared for any round in this cycle**; floor facts quoted from `docs/builder/BUILD.md` `## Floor verification`: Django **5.2.16** on Python **3.10** with strawberry-graphql **0.316.0**, and the shared `.venv` is not the floor. Nothing was installed into the shared `.venv` by this pass.

### Spec changes made (Worker 1 only)

**None in this pass, deliberately.** The spec's status lines are accurate and needed no edit. The one spec change this pass *decides* — the `### Bounded exceptions to the single-source rule` first-bullet replacement, text fixed verbatim above — belongs to **R3**, so the docstring and the spec reach the maintainer in one commit, which is the same reason Worker 0 gave for landing R2's over-claim correction in R2. Editing it here would strand the source half in a re-dispatched R2 and re-create the split the cycle has already rejected once.

Recorded for R3's own pass: the spec file is currently **`M ` — staged** by a concurrent session, exactly like `walker.py`. R1's spec edits are therefore already in someone else's index. R3 must read the spec with `git diff HEAD --` semantics too, and must not stage or unstage anything.

### What returns to Worker 0

1. **Re-dispatch Worker 2 (apply-changes)** with the docstring replacement text above, verbatim, no wording discretion. Its writable set is `django_strawberry_framework/optimizer/walker.py`, this artifact, its own memory file, and — Worker 0's decision — `docs/builder/DONE/build-004-optimizer_beyond-0_0_3.md` for the one-substring citation re-point. Baseline re-verify by **blob** (`git rev-parse HEAD:django_strawberry_framework/optimizer/walker.py`, expect `1030b037b2db85290eeb45bde92c55b865cf6f42`), read the diff with `git diff HEAD --`, and stop-and-report rather than unstage.
2. **Re-dispatch Worker 3 (re-review)** against both the F8 contract and the corrected premise, with the 10-occurrence measurement above to re-derive rather than accept.
3. **Then R3 (Worker 1, custodian)** lands the spec bullet replacement, re-runs `check_spec_glossary.py`, and re-runs the `#"substring"` sweep as a postcondition.

---

## Build report (Worker 2, pass 2)

Apply-changes pass for Worker 1's `revision-needed` ruling. **Worker 1's replacement text was applied verbatim, as one hunk in the same paragraph pass 1 edited.** No wording discretion was taken and none was available: the block replaced is lines 307-317 as the ruling names them, and the 13 replacement lines are byte-for-byte the ruling's fenced text.

### Files touched

Grounded in `git status --short`, not memory. **33 paths dirty at this pass's end, 32 at its start** — this pass added **no** path (`walker.py` and the artifact were both already dirty from pass 1); the one arrival is a concurrent session's ` M django_strawberry_framework/connection.py`, recorded under `### Validation run`. The falling count since pass 1's 58 is `6b42c8d2` / `76fdeac3` / `fa248bdf` having committed other sessions' work, not a revert by anyone.

- `django_strawberry_framework/optimizer/walker.py` — `::_resolve_field_map`'s docstring, the `DUAL CONTRACT` paragraph. One hunk versus `HEAD`, `-8 / +13`. No executable statement, signature, or return annotation touched.
- `docs/builder/bld-016-r2-walker_source_reference_fix.md` — this build report and `Status: built`. Neither `## Plan (Worker 1)`, `## Review (Worker 3)`, nor `## Final verification (Worker 1)` was edited; the `### Dispatched findings checklist` markers were not changed (see below).
- `docs/builder/worker-memory/spec-016-worker-2.md` — one appended entry (gitignored).

**Baseline certified by BLOB, per the ruling's corrected method rule — never by commit hash, never by tree object:**

```shell
git rev-parse HEAD                                                    # fa248bdf064b3dca52c1e591b6c6444b041bb65f
git rev-parse HEAD:django_strawberry_framework/optimizer/walker.py    # 1030b037b2db85290eeb45bde92c55b865cf6f42
```

`1030b037` is the blob Worker 1 measured across four commits, so the baseline this pass edited against is provably the one the ruling was written against, even though `HEAD` has moved again.

**The one working-tree difference in `walker.py` versus `HEAD` before editing was R2 pass 1's own docstring hunk, and nothing else** — confirmed with `git diff HEAD -- django_strawberry_framework/optimizer/walker.py` (the bare `git diff` form is unsound here; see below), which printed exactly the pass-1 hunk `@@ -308,10 +308,13 @@`, four lines removed and seven added, all docstring prose. No concurrent session had opened the file, so no stop-and-report was owed.

**The staged-tree condition was worked around, not fought.** `git status --short -- …/walker.py` reports `MM` — staged *and* further modified — so `git diff -- <path>` is not a sound instrument. Every diff taken or reported in this pass used `git diff HEAD -- <path>`. Nothing was unstaged, `git reset` and `git add` were not run, and the index was not touched. `git stash`, `git checkout`, `git restore`, `git worktree`: used **nowhere**.

### The measurement, re-derived before writing — Worker 1's 10 CONFIRMED

Required by the dispatch, and re-derived rather than encoded from the ruling. Population: plain, non-`getattr` attribute reads of a value taken out of `_resolve_field_map`'s returned `field_map`, counted as **occurrences**, not matching lines.

```shell
grep -n -o -E '(django_field|db_field|field|f)\.(name|is_relation|related_model|attname)' \
    django_strawberry_framework/optimizer/walker.py
```

14 raw hits. Four are **not** reads of the map's values and are excluded by reading each hit rather than pattern-matching it:

| Excluded hit | Why |
|---|---|
| `:324` `f.name` | the map's *construction* (`{f.name: f for f in model._meta.get_fields()}`), not a read of its values |
| `:374` `field.related_model` | inside `_build_child_queryset`'s own docstring prose, not code |
| `:773` `field.name` | inside `_plan_relation_traversal`'s docstring prose, not code |
| `:1125` `django_field.related_model` | inside a `#` comment, not code |

The surviving **10 occurrences across 10 lines and 3 attributes** — identical to Worker 1's table, line for line:

| Line | Read | Holder's provenance (verified, not assumed) |
|---|---|---|
| `:181` | `field.name` | `plan_relation(field, …)`, called at `:631` as `plan_relation(django_field, …)` |
| `:376` | `field.related_model._default_manager` | `_build_child_queryset(field, …)`, called at `:875` as `_build_child_queryset(django_field, …)` |
| `:547` | `f.name == id_attr` | comprehension `for f in field_map.values()` at `:546`; the sibling `getattr(f, "attname", None)` on the same line *is* defensive |
| `:566` | `django_field.is_relation` | `django_field` from the selection walk over `field_map` |
| `:735` | `django_field.related_model` | same |
| `:746` | `django_field.related_model` | same |
| `:749` | `django_field.related_model` | same (a second occurrence two lines below `:746`, not the same one) |
| `:798` | `django_field.related_model` | same |
| `:913` | `django_field.related_model` | same |
| `:1168` | `django_field.is_relation` | `field_map.get(django_name)` at `:1148` / `:1167` |

**`related_model` x6, `is_relation` x2, `name` x2 = 10.** My reading does **not** disagree with Worker 1's at any row, so nothing is encoded here that I could not confirm. Worker 3's 8 is superseded for the two reasons Worker 1 named and I reproduced: `:376` is found only by resolving a `field`-named parameter back to its call site, and `:749` is found only by counting occurrences rather than lines.

The defensive population is unchanged and was re-checked so the contrast is measured rather than asserted: `getattr(django_field, "related_model", None)` at `:340`, `getattr(db_field, "attname", None)` at `:563`, `getattr(f, "attname", None)` at `:547`, `getattr(django_field, "attname", None)` at `:851`.

### The landed paragraph asserts nothing false — checked clause by clause

The dispatch requires this confirmation explicitly, including for the surviving pass-1 clause.

- **The false absolute is gone.** `Both shapes are read via ``getattr(..., default)`` downstream -- that defensive access is the ONLY reason the two coexist safely` no longer exists in the file. `grep -c 'ONLY reason the two coexist safely' django_strawberry_framework/optimizer/walker.py` -> `0`, exit 1.
- **The surviving pass-1 clause did NOT survive unchanged.** `so its callers read attributes directly and need no ``getattr`` default` — the clause Worker 1 ruled leans on the false contrast — is **removed**; `grep -c 'need no ``getattr`` default' …walker.py` -> `0`, exit 1. It is replaced by `so its callers read every attribute directly`, which states the true fact about the twin site without implying anything about the walker's own reads.
- **What the paragraph now claims, and why each claim is true.** `name` and `is_relation` guaranteed on both shapes: `optimizer/field_meta.py::_DjangoFieldLike` (`field_meta.py:39`) is the standing guarantee for the raw shape and `FieldMeta` declares both. "any other attribute is read directly only where both shapes carry it" is a **rule**, not a safe-list, so the 6 direct `related_model` reads are governed without publishing a closed list the module's own `getattr(django_field, "related_model", None)` at `:340` would contradict — which is the trap Worker 1 rejected and I did not reintroduce. `related_model` appears in the text **nowhere**.
- **No new false absolute was introduced.** "That rule, not a blanket `getattr` discipline, is what lets the two shapes coexist safely" is consistent with all 10 plain reads and all 4 defensive ones; it is the sentence the 10 occurrences prove rather than falsify.

### `docs/builder/DONE/build-004-optimizer_beyond-0_0_3.md` — Worker 0's disposition, recorded for the deferred catalog

**NOT edited. Verified untouched and still clean:** `git status --short -- docs/builder/DONE/build-004-optimizer_beyond-0_0_3.md` prints nothing.

Its `:257` D23 row cites `walker.py` **#"ONLY reason the two coexist safely"**, and this pass deletes that clause, so the citation is now **stale by design**. Worker 0's disposition, which supersedes Worker 1's "re-point it in the same change" requirement and is recorded here so the final gate carries it into `### Deferred work catalog` rather than re-litigating it: the file is an **archived per-cycle artifact whose quotation was accurate for the source as it stood at that cycle**, and rewriting a closed historical record to track a later reword is worse than the stale quote. Worker 1's suggested re-point target (**#"lets the two shapes coexist safely"**) does exist verbatim in the landed text, so a future maintainer who disagrees with the disposition can execute the one-substring edit without re-deriving it. The file was not opened for editing.

### Tests added or updated

**None, and it is a decided answer.** The diff changes docstring prose only: `_resolve_field_map`'s four executable statements, its signature, and its return annotation are byte-identical to `HEAD` at blob `1030b037`. Re-measured this pass rather than carried from pass 1: `grep -rn "__doc__\|DUAL CONTRACT\|_resolve_field_map" tests/ examples/` returns one hit, `tests/optimizer/test_walker.py:2105`, which names `_resolve_field_map(Item)` inside a test's own explanatory comment and asserts nothing about the docstring. Neither `BUILD.md` `### Test staleness a focused run cannot see` shape applies — no model field set and no wire shape changed — so no full staleness sweep was owed before `Status: built`. No temp test created; `docs/builder/temp-tests/` untouched.

### Validation run

Scoped to the one file this pass touched, never `.`, in the plan's order.

- `uv run ruff format django_strawberry_framework/optimizer/walker.py` — **pass**, `1 file left unchanged`. (The `COM812`-vs-formatter warning is pre-existing repo configuration.)
- `uv run ruff check --fix django_strawberry_framework/optimizer/walker.py` — **pass**, `All checks passed!`, no fix applied.
- `uv run python scripts/check_trailing_commas.py --check django_strawberry_framework/optimizer/walker.py` — **pass**, exit 0 (the ASCII-only / source-layout gate the pre-commit `source-layout` hook runs; read-only).
- `git status --short` after both ruff invocations — **32 paths, zero additions by this pass.** `git diff HEAD --name-only -- django_strawberry_framework/` lists `mutations/resolvers.py`, `optimizer/walker.py`, `orders/inputs.py`, `orders/sets.py`, `relay.py`, `templates/…/debug_toolbar.html` — every entry but `walker.py` a plan-declared baseline-dirty path. No unexpected churn, so no stop-and-report was owed and nothing was reverted, staged, or unstaged.
- **One path appeared mid-pass and is a concurrent session's, not this build's output: `django_strawberry_framework/connection.py`, status ` M` (unstaged),** taking the final count to **33**. It is absent from every command this pass ran — the only file this pass opened for editing is `walker.py` — and it lands squarely in the plan's baseline-dirty buckets (a concurrent session is committing `fix(optimizer): …`-shaped work into this area, and `optimizer/extension.py` / `nested_planner.py` / `plans.py` / `selections.py` left the dirty set the same way during the previous pass). Per `AGENTS.md` rule 34 it is treated as out-of-scope concurrent work: **not edited, not reverted, not staged, not `git checkout`ed** — recorded here rather than tidied, which is the required disposition.
- **No `pytest`.** No coverage-shaped flag anywhere in this pass.
- **ASCII-only, measured byte-wise:** `LC_ALL=C grep -c '[^ -~]' …walker.py` -> `0`. `--` for the parenthetical dashes, matching the paragraph's existing style.
- **Line lengths in the replaced block:** 33-75, longest **75**, inside the 100 limit with no reliance on the 110 grace.

**The sweep, re-run rather than carried forward.**

```shell
# 3a. THE PROOF OF THE FIX
$ grep -rn "optimizer/resolvers" django_strawberry_framework/   ; echo exit=$?     # exit=1
```

**PROOF MET** — zero occurrences of the never-existent module under package source. The reference the ruling carries through verbatim is intact.

```shell
# census of the symbol reference in .py, occurrences not lines
$ grep -rIn --include='*.py' -o '[a-zA-Z_/.]*resolvers\.py::_field_meta_for_resolver' .
django_strawberry_framework/optimizer/walker.py:315:types/resolvers.py::_field_meta_for_resolver
django_strawberry_framework/optimizer/field_meta.py:204:types/resolvers.py::_field_meta_for_resolver
```

**Two occurrences, one spelling** — unchanged from what Worker 1 certified; the reword moved walker.py's occurrence `:312` -> `:315` and introduced no third spelling.

```shell
# 3b. population sweep, plain recursive grep (git grep cannot see this cycle's untracked artifacts)
$ grep -rn -I -o "optimizer/resolvers" --exclude='*.sqlite3' . | awk -F: '{print $1}' | sort | uniq -c
   1 docs/SPECS/appx/spec-016-…-rationale.md
  20 docs/builder/bld-016-r2-walker_source_reference_fix.md
   3 docs/builder/build-016-fieldmeta_consolidation-0_0_6.md
```

**24 occurrences / 3 files, every one a per-cycle artifact quoting the defect, and zero in any `.py`.** The number is quoted here **only as this pass's own measurement and must not be carried forward** — it grows every time a pass quotes the string (18 at Worker 3, 21 at Worker 1, 24 now), which is the moving-figure hazard Worker 1 recorded. The load-bearing half is stable: zero in `.py`.

```shell
# 3c. reference-resolution loop
121  ``extension.py::_build_cache_key``                      -> optimizer-sibling OK
308  ``field_meta.py::_DjangoFieldLike``                     -> optimizer-sibling OK
315  ``types/resolvers.py::_field_meta_for_resolver``        -> root-relative OK
368  ``utils/querysets.py::apply_type_visibility_sync``      -> root-relative OK
382  ``nested_fetch.py::unwindowable_child_queryset_reason`` -> optimizer-sibling OK
584  ``finalizer.py::finalize_django_types``                 -> *** UNRESOLVED ***
745  ``plans.py::prune_unsupportable_select_related``        -> optimizer-sibling OK
```

**Seven rows now, not six** — the ruling's new `field_meta.py::_DjangoFieldLike` citation is the seventh, and it resolves `optimizer-sibling OK`, confirming the sibling-shorthand spelling is correct (`find django_strawberry_framework -name field_meta.py` returns exactly one path, an `optimizer/` sibling). The single `*** UNRESOLVED ***` row is the acquitted `types/finalizer.py` shorthand at its new line `:584` (was `:582`, moved by this pass's +5 net lines) — the loop's known inability to resolve `types/`-relative paths, not a defect and not a regression.

```shell
# 3d. regression guards
$ grep -rn "_record_pending_relation" django_strawberry_framework/       ; echo exit=$?   # exit=1
$ grep -rnE "extension\.check_schema" django_strawberry_framework/ tests/ ; echo exit=$?   # exit=1
```

**PROOF MET** — both print nothing.

**No near-miss site was changed.** `walker.py:584` (`finalizer.py::` shorthand) and `walker.py:776` (was `:773`, the `utils.relations.instance_accessor` dotted form) are untouched; `registry.py`, `types/converters.py`, `types/resolvers.py`, `optimizer/field_meta.py`, `tests/test_registry.py`, `CHANGELOG.md`, and `docs/builder/DONE/build-004-…md` are all absent from `git diff HEAD --name-only` and clean in `git status --short`.

### Failability proofs

**None; this pass introduced no new boundary.** Boundary count **zero**, re-derived for this pass rather than carried: `git diff HEAD -U0 -- …walker.py` filtered to `^[+-]` yields only docstring prose — no `if`, no comparison, no `raise`, no error message, no default argument, **no expression at all**. `BUILD.md` `### What needs a proof, and what does not` scopes the obligation to a new boundary / guard / gate / rejection path and exempts doc edits, so there is nothing a mutation could remove and no row that could observe its removal. No mutation was applied anywhere in this pass; no `ACTIVE-MUTATION.json` exists. **Fail-open shapes: none introduced** — a hunk with no executable token cannot carry a clamp, `getattr` default, `or` fallback, bare `except`, or truthiness test. (The `getattr` *discipline the prose describes* is unchanged behavior, not a new shape.)

### Hot-path budget

**Not applicable; plan declares no hot path.** No executable statement changed, so no path got slower or faster.

### Floor verification

**Not applicable; no floor-verification scope was declared for any round in this cycle.** Nothing was installed into the shared `.venv` and no floor venv was built. Floor facts quoted from `docs/builder/BUILD.md` `## Floor verification` rather than restated from memory: Django **5.2.16** on Python **3.10** with strawberry-graphql **0.316.0**; the shared `.venv` is not the floor.

### Dispatched findings checklist — no marker changed, and why that is correct

**Neither box's marker was touched.** Both `- [x]` **F8** and `- [x]` **F8-sweep** were ticked in pass 1 and Worker 1's final verification audited both as honest, non-over-ticks. This pass lands no *new* dispatched box: the ruling created a **new obligation on an already-ticked round**, not a new checklist item, and the dispatch's instruction to tick "the boxes that this pass lands, and only those" therefore resolves to none. Both contracts still hold under the reword and were re-proved above — F8's reference reads `types/resolvers.py::_field_meta_for_resolver` at `:315` with 3a printing nothing, and the F8-sweep's four commands were all re-run with their output pasted and no near-miss site changed. Ticking a box twice, or adding a box for the ruling, would both be marker edits Worker 2 is not authorized to make.

### Implementation notes

- **One `Edit` over the whole 11-line block**, replaced by the ruling's 13 lines, so the hunk is one contiguous change in the paragraph pass 1 already edited rather than two. That is the dispatch's explicit shape requirement and it is also what the ruling's own reflow permission provides for.
- **Applied verbatim.** I compared the landed lines against the ruling's fenced block character by character, including the four-space indent, `getattr(..., default)` with its argument ellipsis, `--` for the dashes, and the line breaks. No word was changed, added, or dropped, and no paragraph was re-wrapped beyond the ruling's own wrapping.
- **`field_meta.py::_DjangoFieldLike` verified to exist before the text landed**, not after: `grep -n "_DjangoFieldLike" django_strawberry_framework/optimizer/field_meta.py` -> `39` (the `Protocol` class) and `163` (its use in `from_django_field`'s annotation). The citation is a real symbol in the sibling module, so rule 27 is satisfied and the 3c loop confirms it resolves.
- **The rule-not-a-list shape was preserved deliberately.** It would have been easy to "improve" the text by naming `related_model` alongside the two guaranteed attributes, since 6 of the 10 measured reads are `related_model`. That is exactly the closed safe-list Worker 1 rejected — `walker.py:340` hedges that very attribute with a `getattr` default and `_DjangoFieldLike` does not promise it — so publishing it would recreate the class of defect being fixed. Recorded because the temptation is real and the next reader should know it was seen and refused.
- `scripts/review_inspect.py` was **not** re-run. Its output is structurally blind to this change surface (it replaces every string-literal token including docstrings with `...`), so a re-run would have produced a file identical in every respect this pass can change. No new `docs/shadow/` file was created and no existing one was read into or overwritten.

### Notes for Worker 3

- **Review target: the paragraph, not the diff's novelty.** The whole of this pass is Worker 1's fixed text landing in one hunk. The two things worth re-deriving independently are (1) the 10-occurrence measurement — my table above gives each hit's holder provenance and each exclusion's reason, so disagreement should name a row rather than a total, and remember `grep -o` counts occurrences while `grep -c` counts lines; and (2) that no clause in the landed paragraph is false, including that the pass-1 clause `need no ``getattr`` default` is **gone** rather than merely reworded around.
- **Use `git diff HEAD -- <path>`.** `walker.py` is `MM` (staged by a concurrent session, then modified by this pass), so the bare `git diff` form shows only the pass-2 delta against the staged pass-1 state and the bare `git diff --cached` shows only pass 1. Only `git diff HEAD --` shows the round's whole hunk.
- **Certify by blob, not tree or commit.** `git rev-parse HEAD:django_strawberry_framework/optimizer/walker.py` was `1030b037b2db85290eeb45bde92c55b865cf6f42` for this pass, as it was for the plan, the build, the review, and the ruling — five passes across six commits and four tree objects.
- **`docs/builder/DONE/build-004-…md:257`'s citation is now stale and that is deliberate**, per Worker 0's recorded disposition above. It is not an omission by this pass and not a finding against the round; it belongs in the final gate's deferred catalog. Do not "fix" it.
- The 3c loop prints **seven** rows now (the ruling added a citation) with the same single acquitted `*** UNRESOLVED ***` row, moved `:582` -> `:584`.
- Nothing was mutated, so the tree carries no transient production change. `walker.py` differs from `HEAD` by exactly one docstring hunk, `-8 / +13`.

### Notes for Worker 1 (spec reconciliation)

The plan's eight notes and pass 1's four stand as written. This pass's additions:

1. **The spec half is now the only open half of the pair, and its recommended replacement needs one change from what pass 1 proposed.** R3's target text is the ruling's own `#### Exact replacement text — the spec bullet`, not pass 1's earlier recommendation — pass 1's version corrected only the bullet's closing sentence and left the false premise clause standing, which is the defect Worker 3 escalated and the ruling upheld. Recorded because two candidate replacements for one bullet now exist in this artifact and R3 must land the later one.
   - **Where it lives:** `docs/SPECS/spec-016-fieldmeta_consolidation-0_0_6.md`, `### Bounded exceptions to the single-source rule`, first bullet (**The walker's dual contract**).
   - **Current wording, quoted:** "The two shapes coexist safely only because every downstream read is `getattr(..., default)`" (the premise) together with "the same divergence is present in `types/resolvers.py::_field_meta_for_resolver`" (the closing sentence).
   - **Recommended replacement:** exactly the fenced bullet in `#### Exact replacement text — the spec bullet` above, which is the spec-side paraphrase of what this pass landed. The two now describe each other with no over-claim on either side.
2. **The measurement is stable across three independent derivations at two different values, and the disagreement is instructive.** Worker 3 measured 8, Worker 1 measured 10, I measured 10 with identical rows. Both of the two occurrences Worker 3 missed are of the shapes this cycle has now had to correct three times: a holder reached through a differently-named parameter (`:376`), and a second occurrence on a line already counted (`:749`). The standing form of the lesson, for the catalog: **a stated count is an occurrence count over a population whose membership is established by reading each candidate's provenance, not by the identifier it happens to be spelled with.**
3. **The `DONE/` citation disposition is a decision, not a deferral by omission** — Worker 0 ruled the archived record keeps its accurate-at-the-time quote rather than being rewritten to track a later reword. It supersedes the ruling's "must land in the same change" requirement for that one file. The catalog should carry it as **decided**, with the re-point target (**#"lets the two shapes coexist safely"**, present verbatim in the landed text) recorded so a maintainer who reverses the call has no work to re-derive. This is the answer to the ruling's own "record which".
4. **`git diff -- <path>` reported this pass's file as showing only half its hunk**, because a concurrent session's stage split the round's work across index and worktree (`MM`). The ruling's rule ("use `git diff HEAD --`") is not merely about clean-looking files: on a re-pass it silently hides the earlier pass's half. The final gate should state it in that stronger form.

---

## Review (Worker 3, pass 2)

Re-review of the apply pass against Worker 1's `revision-needed` ruling. Read-only throughout: `git stash`, `git checkout`, `git restore`, `git worktree` used **nowhere**; the index was not touched (no `git add`, no `git reset`, no unstage). Every `HEAD` reading went through `git show HEAD:<path>` into a scratch path outside the repository, `git rev-parse`, `git diff HEAD`, or `git grep`.

**Certified by blob, per the ruling's corrected method rule.** `git rev-parse HEAD` -> `fa248bdf064b3dca52c1e591b6c6444b041bb65f`; `git rev-parse HEAD:django_strawberry_framework/optimizer/walker.py` -> `1030b037b2db85290eeb45bde92c55b865cf6f42` — the same blob the plan, both build passes, the pass-1 review, and the ruling all measured, so every reading in this artifact is still valid against the file I read. No commit hash or tree object is quoted here as a content certificate.

**The whole round's change read with `git diff HEAD -- <path>`**, as the dispatch requires. `git status --short` reports `MM` for `walker.py`; I confirmed the trap rather than accepting it — the bare `git diff` form shows only pass 2 and `git diff --cached` only pass 1. `git diff HEAD --numstat` -> `13 8`, i.e. `-8 / +13`, **one hunk** (`@@ -304,14 +304,19 @@`), entirely inside `::_resolve_field_map`'s docstring.

### High:

None.

### Medium:

None.

### Low:

#### The re-point substring recorded for the archived `DONE/` citation is not greppable as written — it spans a line break

`docs/builder/bld-016-r2-walker_source_reference_fix.md:825` (Worker 2, quoting Worker 1's `:664`) records that the suggested re-point target for `docs/builder/DONE/build-004-optimizer_beyond-0_0_3.md:257` — **#"lets the two shapes coexist safely"** — "does exist verbatim in the landed text". Measured: it does not exist as a single-line substring. The landed text wraps it:

```django_strawberry_framework/optimizer/walker.py:312:313
    blanket ``getattr`` discipline, is what lets the two shapes coexist
    safely. Treat the values as ``FieldMeta | Any`` until the
```

`grep -c 'lets the two shapes coexist safely' django_strawberry_framework/optimizer/walker.py` -> `0`, exit 1. The greppable form is **#"lets the two shapes coexist"** (unique, one hit, `walker.py:312`).

Why it matters rather than being pedantry: this cycle's whole standing lesson is that a `#"substring"` citation breaks on reflow as well as on reword, and the point of recording a re-point target inside a *decided* deferral is that a maintainer who reverses Worker 0's disposition "has no work to re-derive". As recorded, that maintainer would paste a citation that greps to nothing — reproducing the class of defect F8 fixed, in the file the disposition deliberately left dangling.

**The same wrap affects the one citation the ruling asserted was safe.** `docs/SPECS/appx/spec-016-fieldmeta_consolidation-0_0_6-rationale.md:263` quotes "until the registry-coverage gate lands", and the ruling (`:666`) cleared it because "the replacement **preserves verbatim**". The words are preserved, but at `HEAD` the phrase sat on one line (`` ``FieldMeta | Any`` until the registry-coverage gate lands. The same``) and it now spans `walker.py:313`/`:314`. That particular use is prose quotation inside a rationale narrative rather than a rule-27 `#"substring"` citation, so no formal citation is broken — but the ruling's stated *basis* for clearing it does not hold at grep granularity, and the postcondition sweep the ruling itself demands would have caught both.

**Disposition: not held against this round.** Worker 2 applied fixed text verbatim, exactly as instructed, and had no wording discretion; the inaccuracy is in the ruling's and the build report's *prose about* the text, not in the landed source. No behavior, no test expectation, and no shipped contract is affected. Escalated to Worker 1 under `### Notes for Worker 1 (spec reconciliation)` so the deferred catalog carries the greppable form and so R3 runs its postcondition sweep as a **line-wise** grep.

### The four things this pass was told to review hardest

**1. Does the landed paragraph assert anything false? No — re-derived clause by clause, and the measurement re-derived from source first.**

I re-derived the count independently before reading either the ruling's table or Worker 2's, then compared. Population: plain, non-`getattr` attribute reads of a value taken out of `_resolve_field_map`'s returned `field_map`, counted as **occurrences**. Candidate sweep `grep -n -o -E '(django_field|db_field|field|f)\.(name|is_relation|related_model|attname)'` -> 14 raw occurrences; I then read each hit's provenance rather than pattern-matching it, and separately swept `grep -n -o -E '(django_field|db_field)\.[a-zA-Z_]+'` and every other attribute on the candidate holders to confirm the attribute set is closed (nothing outside `name` / `is_relation` / `related_model` / `attname` is read off a map value anywhere in the file).

Excluded, with reasons (current line numbers — the file is `+2` on the numbers both the ruling and the build report used, because pass 2 added two lines above them):

| Excluded | Why |
|---|---|
| `:326` `f.name` | the map's **construction** key (`{f.name: f for f in model._meta.get_fields()}`), not a read of its values |
| `:376` `field.related_model` | `_build_child_queryset`'s own docstring prose |
| `:775` `field.name` | `_plan_relation_traversal`'s docstring prose |
| `:1127` `django_field.related_model` | inside a `#` comment |

Surviving, **10 occurrences on 10 lines over 3 attributes**, each holder's provenance resolved to a call site or a `field_map` read rather than assumed:

| Line (now) | Read | Holder |
|---|---|---|
| `:181` | `field.name` | `plan_relation(field, …)`, called at `:633` as `plan_relation(django_field, …)` |
| `:378` | `field.related_model._default_manager` | `_build_child_queryset(field, …)`, called at `:877` as `_build_child_queryset(django_field, …)` |
| `:549` | `f.name == id_attr` | comprehension `for f in field_map.values()` at `:548`; the sibling `getattr(f, "attname", None)` on the same line *is* defensive |
| `:568` | `django_field.is_relation` | selection walk over `field_map` |
| `:737` | `django_field.related_model` | same |
| `:748` | `django_field.related_model` | same |
| `:751` | `django_field.related_model` | same — a **second occurrence** two lines below `:748`, not the same one |
| `:800` | `django_field.related_model` | same |
| `:915` | `django_field.related_model` | same |
| `:1170` | `django_field.is_relation` | `field_map.get(django_name)` at `:1150`, or the forward-resolve rebind at `:1169` |

**`related_model` x6, `is_relation` x2, `name` x2 = 10.** This **confirms Worker 1's and Worker 2's 10 row-for-row** and supersedes my own pass-1 count of 8. Both misses were mine, and both are the shapes this cycle keeps having to correct: `:378` is reachable only by resolving a `field`-named parameter back to its call site, and `:751` only by counting occurrences instead of matching lines. My pass-1 section also wrote "those **four** attributes" while enumerating three; that is corrected here to three.

Defensive population re-checked so the contrast is measured: `getattr(django_field, "related_model", None)` at `:342`, `getattr(f, "attname", None)` at `:549`, `getattr(db_field, "attname", None)` at `:565`, `getattr(django_field, "attname", None)` at `:853`.

Now every clause of the landed paragraph against that:

- "``name`` and ``is_relation`` are guaranteed on both shapes (``field_meta.py::_DjangoFieldLike``)" — **true, and the citation is accurate.** I read the Protocol: `optimizer/field_meta.py::_DjangoFieldLike` (`field_meta.py:39`) declares exactly `name: str` and `is_relation: bool`, and its docstring is the standing guarantee ("Every Django ``Field`` and reverse-relation descriptor surfaced by ``Model._meta.get_field`` / ``Model._meta.get_fields`` guarantees ``name`` and ``is_relation``"), explicitly adding that the remaining attributes "are read defensively with ``getattr`` defaults". `FieldMeta` declares both at `field_meta.py:133`/`:134`. So the guarantee is real on the raw shape and declared on the `FieldMeta` shape — the docstring claims neither more nor less than the Protocol delivers.
- "any other attribute is read directly only where both shapes carry it, and a ``FieldMeta``-only attribute must never be read off this map without a ``getattr(..., default)``" — **true, and it is a rule, not a list** (see point 2).
- "That rule, not a blanket ``getattr`` discipline, is what lets the two shapes coexist safely" — **true**, and it is the sentence my 10 occurrences *prove* rather than falsify. The false absolute it replaces is gone: `grep -c 'ONLY reason the two coexist safely'` -> `0`, exit 1.
- "Treat the values as ``FieldMeta | Any`` until the registry-coverage gate lands" — unchanged in substance from `HEAD`, still true.
- "``types/resolvers.py::_field_meta_for_resolver`` shares the policy -- prefer the canonical definition-backed metadata, fall back when it is unreachable" — **true**, re-derived from `types/resolvers.py`: the canonical arm is `registry.get_definition(parent_type)` then `definition.field_map.get(field.name)`, returned only when not `None`.
- "but not this dual return shape: it returns a ``FieldMeta`` unconditionally" — **true**: annotated `-> FieldMeta`, three exits (canonical hit; `FieldMeta._from_field_shape(field, is_relation=True)` when `not hasattr(field, "is_relation")`; `FieldMeta.from_django_field(field)` otherwise), no branch on which a raw Django field escapes.
- "so its callers read every attribute directly" — **true, and this is the clause the ruling rewrote, so I measured it rather than inheriting it.** `grep -n -o -E 'field_meta\.[a-zA-Z_]+'` over `types/resolvers.py` returns 11 plain reads (`attname` x5, `related_model` x4, `relation_kind`, `is_many_side`), and `grep -rn "getattr(field_meta"` over the whole package returns **nothing, exit 1**. Zero defensive reads of a `_field_meta_for_resolver` result exist anywhere.
- **The pass-1 clause the ruling condemned is gone, not reworded around.** `grep -c 'need no ``getattr`` default'` -> `0`, exit 1. It is replaced by "read every attribute directly", which states the twin site's fact without implying anything about the walker's own reads — which was the whole basis of the ruling.

**Verdict: no clause in the landed paragraph is false, including every clause that survived pass 1.**

**2. Is the rule stated as a rule rather than as a closed safe-list? Yes, and the trap was avoided.**

`related_model` appears **nowhere** in the landed text (`grep -c 'related_model' <the hunk>` -> 0), even though 6 of the 10 measured direct reads are `related_model`. That is the right call and I re-derived why rather than taking it from the ruling: `walker.py:342` hedges that very attribute with `getattr(django_field, "related_model", None)`, and `_DjangoFieldLike` deliberately does not promise it. A three-item safe-list would therefore have been contradicted by the module's own code four lines below the docstring — exactly the class of defect F8 and the ruling were fixing. The landed form ("any other attribute is read directly only where both shapes carry it") governs all six `related_model` reads without publishing a list, and it names only the two attributes the Protocol actually guarantees.

**3. One coherent paragraph, and the F8 fix intact.**

- **One hunk, in the paragraph pass 1 edited.** `git diff HEAD` shows a single `@@` block; lines 304-306 (`DUAL CONTRACT (read before consuming the returned map): the values` / `are ``FieldMeta`` when …` / `raw Django field objects …`) are untouched context, and the `"""` terminator and everything below it are context. There is no second hunk anywhere in the file and no second file with a hunk attributable to this pass.
- **Applied verbatim.** I compared the 13 added lines character-for-character against the ruling's fenced block at `:632-646`, including the four-space indent, `getattr(..., default)` with its argument ellipsis, `--` for the dashes, and every line break. Identical. No wording discretion was taken.
- **F8 survives.** `grep -rIn --include='*.py' -o '[a-zA-Z_/.]*resolvers[./]py::_field_meta_for_resolver' .` returns **exactly two occurrences, one spelling** — `optimizer/walker.py:315` and `optimizer/field_meta.py:204`, both `types/resolvers.py::_field_meta_for_resolver`. **No third spelling of the symbol exists in any `.py`.** `grep -rn "optimizer/resolvers" django_strawberry_framework/` -> nothing, exit 1 (3a reproduced independently). The folder segment stays load-bearing: `find django_strawberry_framework -name resolvers.py` -> **four** paths (`types/`, `forms/`, `mutations/`, `rest_framework/`), re-measured.
- **The new citation's spelling is the acquitted house convention being used, not breached.** `find django_strawberry_framework -name field_meta.py` -> exactly one path, an `optimizer/` sibling of `walker.py`, so the bare-basename form matches walker.py's four existing sibling refs and rule 27's `path::QualifiedName` shape.

**4. No executable change, and no fail-open shape.**

`git diff HEAD -U0` filtered to `^[+-]` yields **only docstring prose**. `_resolve_field_map`'s four executable statements (`type_cls = …`, `definition = …`, `field_map = …`, `return type_cls, definition, field_map`), its signature, and its return annotation `tuple[type | None, Any | None, dict[str, Any]]` are byte-identical to `HEAD` at blob `1030b037` — verified by reading them as diff context and against `git show HEAD:<path>`. The hunk contains no `if`, no comparison, no `raise`, no error message, no default argument, **no expression at all**. Consequently: **boundary count zero**, and no clamp, `getattr` default, `or` fallback, bare `except`, or truthiness test could enter (`BUILD.md` `### Fail-open shapes`). The `getattr` *discipline the prose describes* is unchanged behavior, not a new shape.

Also confirmed: ASCII-only, measured byte-wise — `LC_ALL=C grep -c '[^ -~]'` -> `0`, exit 1. New block line lengths 33-75 (longest 75), inside the 100 limit with no reliance on the 110 grace; the file's pre-existing 109-character maximum line is untouched by this hunk.

### Dispatched findings checklist audit — I agree with Worker 2's no-marker-change

**Agreed, and for the reason Worker 2 gives.** The ruling created a **new obligation on an already-ticked round**, not a new dispatched box. There are exactly two boxes, both `- [x]` from pass 1, both audited as honest by Worker 1's final verification, and both contracts **still hold under the reword** — which is the part that matters, because a reword could have un-landed a ticked contract and did not:

- **`- [x]` F8 — still landed.** The reference reads `types/resolvers.py::_field_meta_for_resolver` at `walker.py:315`; 3a prints nothing, exit 1; the census shows one spelling, two `.py` occurrences.
- **`- [x]` F8-sweep — still landed.** All four sweep commands re-run by me, output below. Its "no near-miss site was changed" assertion re-confirmed mechanically and by content: `git diff HEAD --name-only` over `django_strawberry_framework/`, `tests/`, `docs/builder/DONE/`, `docs/SPECS/` lists no `registry.py`, no `types/converters.py`, no `types/resolvers.py`, no `optimizer/field_meta.py`, no `tests/test_registry.py`, no `CHANGELOG.md`, no `DONE/**`; and by content `walker.py:584` still carries the `finalizer.py::` shorthand and `walker.py:776` still `utils.relations.instance_accessor`.

No tick lacks a matching landed fix, and no box is unaddressed. Adding a box for the ruling, or re-ticking, would both be marker edits Worker 2 is not authorized to make — and would also have been the *wrong* record, since the ruling's obligation is not a dispatched finding.

One note that is not a finding against Worker 2: the F8-sweep box's own text still states its proof condition as "3c prints six rows with zero `*** UNRESOLVED ***`", which is unachievable and was unachievable at pass 1 (the loop cannot resolve `types/`-relative shorthand) and is now two rows off (seven rows, one acquitted). The box text is the plan's and is not editable by Worker 2 or by me; the substitution is recorded in the build report and in the ruling. Carried to the final gate so the box is not read literally.

### Recorded proofs audit

- **Failability proof: none owed, and the reasoning holds against `BUILD.md` `### What needs a proof, and what does not`.** That section scopes the obligation to a **new boundary, guard, gate, or rejection path** — "anything whose job is to say 'no', hold an invariant, or fail closed" — and exempts doc edits. I confirmed rather than assumed that pass 2 introduced no boundary: see point 4, the hunk contains no executable token, so there is nothing a mutation could remove and no row that could observe its removal. **The mandatory re-run floor (`worker-3.md`: every boundary with a recorded count <= 3, plus every security / data-isolation boundary) is vacuous, so an empty re-run set is legal.** I re-ran no boundary because none exists; I accepted none on Worker 2's record because there is no record to accept. Nothing was mutated by me — my source carve-out was not exercised — and no `ACTIVE-MUTATION.json` exists, so the tree carries no transient production change from any pass.
- **Fail-open shapes: none, hunted rather than assumed.** Per point 4.
- **Hot-path budget: not owed.** Plan declares `none`; no executable statement changed. No missing-number finding.
- **Floor verification: not owed.** No round in this cycle declares a floor scope. Nothing was installed into the shared `.venv` by this pass. Floor facts quoted from `BUILD.md` `## Floor verification`: Django **5.2.16** on Python **3.10** with strawberry-graphql **0.316.0**; the shared `.venv` is not the floor.

### The two dispositions I was told to check rather than accept — both are as described

**(a) `docs/builder/DONE/build-004-optimizer_beyond-0_0_3.md` — NOT edited, and correctly so.** Verified untouched two ways: `git status --short -- docs/builder/DONE/` prints nothing, and the path is absent from `git diff HEAD --name-only`. Its `:257` D23 row does cite `walker.py` **#"ONLY reason the two coexist safely"**, and that clause is now gone from the file (`grep -c` -> 0, exit 1), so the citation **is** stale by design. Worker 0's disposition is exactly as Worker 2 records it, and I agree with it on the merits: the row is a closed cycle's record of what the source said *at that cycle*, and rewriting a historical quotation to track a later reword falsifies the record it exists to preserve. The one thing the disposition gets wrong is the re-point target's greppability, filed as the Low above.

**(b) The 3c sweep prints seven rows with one acquitted `types/finalizer.py` bare-basename row — reproduced verbatim.** Ran the plan's loop myself:

```shell
121  ``extension.py::_build_cache_key``                      -> optimizer-sibling OK
308  ``field_meta.py::_DjangoFieldLike``                     -> optimizer-sibling OK
315  ``types/resolvers.py::_field_meta_for_resolver``        -> root-relative OK
368  ``utils/querysets.py::apply_type_visibility_sync``      -> root-relative OK
382  ``nested_fetch.py::unwindowable_child_queryset_reason`` -> optimizer-sibling OK
584  ``finalizer.py::finalize_django_types``                 -> *** UNRESOLVED ***
745  ``plans.py::prune_unsupportable_select_related``        -> optimizer-sibling OK
```

Seven rows because the ruling's `field_meta.py::_DjangoFieldLike` citation is the seventh, and it resolves `optimizer-sibling OK` — independent confirmation that the new citation's spelling is right. The single `*** UNRESOLVED ***` row is the acquitted site at `:584`: `find django_strawberry_framework -name finalizer.py` returns exactly one path, `django_strawberry_framework/types/finalizer.py`, so the shorthand resolves for a human reader and the loop's two candidate roots (package-root-relative, `optimizer/`-sibling) both structurally miss it. Loop limitation, not a defect, not a regression.

The rest of the sweep, re-run rather than accepted:

```shell
$ grep -rn "optimizer/resolvers" django_strawberry_framework/            # nothing, exit 1
$ grep -rn "_record_pending_relation" django_strawberry_framework/       # nothing, exit 1
$ grep -rnE "extension\.check_schema" django_strawberry_framework/ tests/ # nothing, exit 1
```

I deliberately do **not** restate the repo-wide `optimizer/resolvers` occurrence total. It is a figure about the artifacts, not the code, and it grows every time a pass quotes the string (8 -> 18 -> 21 -> 24 across this cycle); the load-bearing half is stable and re-verified: **zero occurrences in any `.py`**.

### DRY findings

None. The diff adds no helper, constant, literal, branch, or parallel data flow. Nothing to consolidate; nothing new duplicated.

**Existence challenge — asked again against the landed wording, and the answer is still that the prose note is the right shape, but it now carries its weight in a way pass 1's wording did not.** Grounds for asking: a cross-reference is an indirection with exactly one reader, which is the shape `worker-3.md` says to challenge. Re-derived from both bodies:

- The two sites share **one policy** (prefer the canonical definition-backed metadata; fall back when it is unreachable) and share neither a return shape (`dict[str, Any]` with two value types vs unconditional `FieldMeta`) nor a read discipline (mixed plain/defensive vs 11 plain reads and zero `getattr`). A helper factoring their commonality would factor a *statement*, and a statement is what a cross-reference already is.
- **Does the landed wording make the note carry its weight? Yes, and this is a real improvement over both `HEAD` and pass 1.** At `HEAD` the note asserted "the same divergence (and the same ``getattr``-defensive fallback)" — a claim that is false, and a false pointer is worse than no pointer because it tells the reader the twin site needs the same defensive care it does not need. Pass 1 narrowed it but left the walker-side premise false, so the contrast still misdirected. The landed sentence states the shared half and **names the asymmetry explicitly**, so a reader arriving at either site learns the one thing a pointer can usefully carry: what must not drift (the policy) and what must not be assumed to match (the shape). That is the pointer earning its existence rather than merely existing.
- The exit condition is named in the docstring itself ("until the registry-coverage gate lands"), at which point the walker's fallback disappears, the dual contract ends, and the cross-reference should be **deleted** rather than re-pointed. The rationale companion's recorded `*Rejected alternative.*` (make the walker's fallback build `FieldMeta`, delete the resolver fallbacks) stays rejected and I am not re-opening it.

**No refactor is proposed**, and one would have been out of scope for this round regardless. Recorded under `### Notes for Worker 1` so silence is not read as the question going unasked.

### Public-surface check

`git diff HEAD -- django_strawberry_framework/__init__.py` produces **no output** (0 bytes). `__all__` and the re-export list are unchanged; no new public export, nothing needing spec authorization.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md. Confirmed absent from `git diff HEAD --name-only` and clean in `git status --short`. Its known-stale text about this card is barred by `AGENTS.md` rule 21 and is catalogued, not a finding.

### Documentation / release sanity (only when the slice touches docs, release metadata, KANBAN, or archived specs)

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. The diff's only file is package source. Three checks made anyway because the change is a docstring reflow:

- `docs/TREE.md` renders **module** docstrings; this is a **function** docstring, so no regenerate is owed and none was run.
- **Substring-citation sweep run as a postcondition** over `Both shapes are read via`, `ONLY reason the two coexist`, `registry-coverage gate`, `Keep the policy in sync`, `keep the two in`, `Treat the values as`. Survivors outside this cycle's own per-cycle artifacts: `docs/builder/DONE/build-004-…md:257` (the by-design stale citation, disposition (a) above), `docs/dry/dry-0_0_11.md:387,506` (per-cycle, paraphrase not citation), and `docs/SPECS/appx/…-rationale.md:263` (prose quotation, now line-wrapped in the source — see the Low). Nothing else points into the replaced block.
- `KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md`, `examples/fakeshop/db.sqlite3`, `docs/SPECS/**` and `docs/builder/DONE/**` all absent from `git diff HEAD --name-only` except R1's already-recorded spec edits, which are not this pass's.

### Static helper use

**Skipped, with the reason stated and mechanically proved.** `scripts/review_inspect.py` was not re-run this pass. Its stripper replaces every string-literal token **including docstrings** with `...`, so its output is structurally incapable of showing this diff — proved rather than asserted: `grep -c 'DUAL CONTRACT' docs/shadow/django_strawberry_framework__optimizer__walker.stripped.py` -> `0`, exit 1, i.e. the paragraph under review does not appear in the helper's output at all. Re-running it would have produced a file identical in every respect this pass can change, while writing into `docs/shadow/` for no evidentiary gain. The plan-time run's one useful reading still stands and I confirmed it holds: walker.py's two `TODO(spec-035)` anchors belong to another card and are untouched (`grep -rIn -E 'TODO\(spec-016|TODO-(ALPHA|BETA|STABLE)-016'` finds nothing outside this cycle's own artifacts). No new `docs/shadow/` file was created, and `docs/shadow/helper-inventory.md` / `docs/shadow/current/` were not touched. No shadow line number is cited anywhere in this review.

Independent staleness sweep, run against the tree rather than the artifact's file list: neither `BUILD.md` `### Test staleness a focused run cannot see` shape applies — no example-model field set and no wire shape changed. `grep -rn "_resolve_field_map\|DUAL CONTRACT\|__doc__" tests/ examples/` finds one hit, `tests/optimizer/test_walker.py:2105`, a test's own explanatory comment asserting nothing about this docstring.

### No `pytest` run, and what that rests on

No focused run, and the reason is structural rather than a skip: no assertion in any of the three test trees can change pass/fail on a hunk with no executable token, so a run would prove only that an unrelated suite is green — not a claim this review needs. No coverage-shaped flag was used anywhere in this pass.

### What looks solid

- **The ruling's text landed verbatim and the pass-1 clause the ruling condemned is genuinely gone**, not reworded around it — the distinction the dispatch asked me to check, and it holds by grep in both directions.
- **The rule-not-a-list discipline survived contact with temptation.** 6 of 10 direct reads are `related_model` and the text names it nowhere; `walker.py:342`'s own `getattr` hedge on that attribute is why a list would have been self-contradicting. Worker 2 recorded that it saw the temptation and refused it, which is the right shape of implementation note.
- **The measurement converged across four independent derivations** (mine at 8, then Worker 1, Worker 2, and mine again at 10 with identical rows). My pass-1 undercount is corrected here, and both misses were the two disciplines this cycle has now had to fix repeatedly.
- **The staging trap was handled, not fought.** Worker 2 read the round through `git diff HEAD --`, recorded `MM`, and touched neither index nor another session's file; the mid-pass arrival of ` M connection.py` was recorded rather than tidied, which is the required disposition under `AGENTS.md` rule 34.
- **The new citation is the acquitted house convention being applied**, and the 3c loop independently confirms it resolves as an `optimizer/` sibling.
- One hunk, one paragraph, `-8 / +13`, no executable token, ASCII-only, longest new line 75.

### Temp test verification

None created; none appropriate. `docs/builder/temp-tests/` holds a concurrent session's live output and was neither read into nor written. No temp test can demonstrate anything about docstring prose, so manufacturing one would be activity rather than verification. No temp test from any pass is the sole proof of any shipped behavior here.

### Notes for Worker 1 (spec reconciliation)

1. **Escalated: the recorded re-point substring for `DONE/build-004-…md:257` is not greppable, and the ruling's clearance of the rationale's `registry-coverage gate` quotation rests on the same oversight.** See `### Low:` for the measurement. Resolution paths:
   - **(a) Amend the catalog entry only** — record the re-point target as **#"lets the two shapes coexist"** (unique, `walker.py:312`, single line) instead of **#"lets the two shapes coexist safely"**, and note that the rationale's `:263` quotation now spans `walker.py:313`/`:314`. No source edit, no round re-opened. **My recommendation** — the disposition to leave the archived record alone is right, and this only makes its escape hatch actually executable.
   - **(b) Also re-point `DONE/build-004-…md:257` in R3**, reversing Worker 0's disposition. I do not recommend it: the archived quotation was accurate for its own cycle, and rewriting closed records to track later rewords is the worse precedent.
   - **(c) Reflow the docstring so both phrases sit on one line each.** Rejected on my side — it re-opens a reviewed file to satisfy a citation convention, and the wrapping is the ruling's own fixed text.
   In every path, **R3 must run its substring sweep line-wise**, not phrase-wise: this pass is the second time in the cycle a phrase was cleared as "preserved verbatim" while a wrap moved it across a line boundary.
2. **The landed wording and the R3 recommendation are mutually consistent and consistent with what I measured — confirmed, since the pair must read as one contract.** The spec's `### Bounded exceptions to the single-source rule` first bullet still carries **both** false clauses at `spec-016-…md:34` ("The two shapes coexist safely only because every downstream read is `getattr(..., default)`" and "the same divergence is present in `types/resolvers.py::_field_meta_for_resolver`") — deliberately R3's to fix and **not a finding against R2**. The ruling's `#### Exact replacement text — the spec bullet` is the spec-side paraphrase of exactly what landed: same two guaranteed attributes, same rule-not-a-list shape, same `unconditionally` / `read every attribute directly` statement about the twin site, root-relative `optimizer/field_meta.py::_DjangoFieldLike` where the docstring uses the sibling shorthand (correct for each file's convention). Every clause of it is true against my own measurements. **R3 must land that later text, not pass 1's earlier recommendation** — two candidate replacements for one bullet now exist in this artifact, and pass 1's corrects only the closing sentence.
3. **The F8-sweep checklist box's stated proof condition is literally unmet and cannot be met.** "3c prints six rows with zero `*** UNRESOLVED ***`" was unachievable at pass 1 and is now two rows off. The box text belongs to the plan and neither Worker 2 nor I may edit it; the substitution is recorded in three places. The final gate should not read it literally, and no future sweep should reuse the loop without either resolving `types/`-relative paths or naming the expected row.
4. **My pass-1 count of 8 was wrong and is corrected to 10 here** (`:378` reachable only through a differently-named parameter's call site; `:751` only by counting occurrences instead of lines). My pass-1 phrase "those **four** attributes" while enumerating three is also corrected: three attributes, ten occurrences. Recorded because the pass-1 review section stays on disk unedited and the final gate reads both.
5. **No refactor of the two dual-contract sites is proposed.** The existence challenge is answered above, in agreement with the plan, the rationale's recorded rejected alternative, and my pass-1 answer — but on stronger grounds now, because the landed wording is what makes the pointer carry its weight rather than merely exist. Catalog the exit condition: when the registry-coverage gate lands, the walker's fallback disappears, the dual contract ends, and the cross-reference plus the whole `DUAL CONTRACT` paragraph plus the spec's first bounded exception should be **deleted**, not re-pointed.
6. **`walker.py` is still `MM`** — staged by a concurrent session, then modified by this round. I did not touch the index. The maintainer-facing hazard the ruling recorded is unchanged: a `git commit` on this index would ship this round's docstring inside a commit describing someone else's work. Flagged, not acted on.

### Review outcome

`review-accepted`. No High and no Medium. The single Low is an inaccuracy in the artifact's own prose about the landed text — not in the landed text, and not in anything Worker 2 had discretion over — and it is escalated to Worker 1 with resolution paths, so nothing is held open against this round. The ruling's replacement text landed verbatim as one hunk in the paragraph pass 1 edited; every clause of the resulting paragraph is true, including all four that survived pass 1; the rule is stated as a rule and `related_model` appears nowhere; F8's cross-reference is intact with one spelling and two `.py` occurrences; the four executable statements, the signature, and the return annotation are byte-identical to blob `1030b037`; boundary count is zero so the failability floor is legally empty and the re-run set legally empty with it; both dispositions I was told to check are as described; and the public surface is unchanged.

---

## Final verification (Worker 1, pass 2)

`Status: final-accepted`. The round is closed. This is an audit, not a re-litigation of the ruling: Worker 2 applied the fixed text verbatim as one hunk, Worker 3 re-reviewed with no High and no Medium and corrected its own pass-1 count from 8 to 10, and everything load-bearing below was **re-measured from source at this pass** rather than read out of either report.

### Spec status-line re-verification

Performed at spawn per `docs/builder/worker-1.md` `## Spec status-line re-verification (every Worker 1 spawn)`. `docs/SPECS/spec-016-fieldmeta_consolidation-0_0_6.md` lines 1-7 (title; `Target release: 0.0.6 (per KANBAN.md card DONE-016-0.0.6)`; `Status: shipped.`; `Owner: package maintainer.`; the rationale-companion pointer) **still describe the build's current state.** No edit owed, none made in this pass. No reference to a predecessor doc this build deleted survives. The spec body edit this round decided is R3's, as ruled.

### Certification: blob, not commit, not tree

| Fact | Value |
|---|---|
| `git rev-parse HEAD` | `fa248bdf064b3dca52c1e591b6c6444b041bb65f` |
| `git rev-parse HEAD:django_strawberry_framework/optimizer/walker.py` | `1030b037b2db85290eeb45bde92c55b865cf6f42` |
| `git status --short -- …/walker.py` | `MM` (staged by a concurrent session, then modified by pass 2) |
| `git diff HEAD --numstat -- …/walker.py` | `13  8` -> `-8 / +13`, one hunk `@@ -304,14 +304,19 @@` |
| `git status --short \| wc -l` | 33 |

`1030b037` is the same blob the plan, both build passes, both reviews, and the pass-1 ruling measured — six commits and four tree objects deep. Every reading in this artifact is still valid against the file I read. `git stash`, `git checkout`, `git restore`, `git worktree` used **nowhere**; the index was not touched (no `git add`, no `git reset`, no unstage). All diffs taken as `git diff HEAD -- <path>`, never the bare form, which reports an `MM` file's staged half as clean.

### 1. No executable statement changed — proved by AST, not by reading the diff

Stronger than a diff inspection, because a diff inspection is what a reflow can fool. Both the `HEAD` blob (extracted read-only via `git show HEAD:<path>` into a scratch path outside the repository) and the working tree were parsed and `_resolve_field_map` unparsed:

| Property | `HEAD` | working tree |
|---|---|---|
| non-docstring statements | 4 | 4 |
| signature | `model: type[models.Model], *, source_type: type \| None = None` | identical |
| return annotation | `tuple[type \| None, Any \| None, dict[str, Any]]` | identical |
| statement 1 | `type_cls = source_type if source_type is not None else registry.get(model)` | identical |
| statement 2 | `definition = registry.get_definition(type_cls) if type_cls is not None else None` | identical |
| statement 3 | `field_map = definition.field_map if definition is not None else {f.name: f for f in model._meta.get_fields()}` | identical |
| statement 4 | `return (type_cls, definition, field_map)` | identical |

Byte-identical on every row. **Boundary count zero confirmed**, so no failability proof is owed and none is missing; **no fail-open shape** can be introduced by a hunk carrying no executable token. Both confirmations of `docs/builder/worker-1.md` `### Failability and fail-open checks` are discharged. The diff is a single hunk in one file; no second hunk anywhere and no other file carries one attributable to this round.

### 2. The landed docstring asserts nothing false — re-derived clause by clause

- **"``name`` and ``is_relation`` are guaranteed on both shapes (``field_meta.py::_DjangoFieldLike``)".** True and the citation is exact. `optimizer/field_meta.py::_DjangoFieldLike` is a `Protocol` declaring **exactly** `name: str` and `is_relation: bool`, and its docstring is the standing guarantee for the raw shape; it adds that the remaining attributes "are read defensively with ``getattr`` defaults". `FieldMeta`'s `Attributes:` block declares both. The docstring claims neither more nor less than the Protocol delivers.
- **"any other attribute is read directly only where both shapes carry it, and a ``FieldMeta``-only attribute must never be read off this map without a ``getattr(..., default)``".** True, and I proved the *rule* rather than re-counting the population. Every attribute read off a map-value holder in the whole file: `grep -n -o -E '(django_field|db_field)\.[a-zA-Z_]+' …walker.py` -> **`related_model` x6, `is_relation` x2, and nothing else**; plus `field.name` (`:181`, holder `plan_relation(django_field, …)`) and `f.name` (`:549`, over `field_map.values()`) = **10 plain occurrences over 3 attributes**, which reproduces the ruling's, Worker 2's, and Worker 3's pass-2 tables. Defensive reads: `getattr(django_field, "related_model", None)` `:342`, `getattr(f, "attname", None)` `:549`, `getattr(db_field, "attname", None)` `:565`, `getattr(django_field, "attname", None)` `:853`. **The decisive check is the negative one: not one `FieldMeta`-only attribute — `nullable`, `relation_kind`, `is_many_side`, `target_pk_name`, `target_field_name`, `target_field_attname`, `fk_id_elision_eligible`, `many_to_many`, `one_to_many`, `one_to_one` — is read off a map value anywhere, plainly or otherwise, and `attname` (present on forward fields but not on every reverse descriptor) is `getattr`-defended at all three of its sites.** The rule the docstring states is exactly the rule the file obeys.
- **"That rule, not a blanket ``getattr`` discipline, is what lets the two shapes coexist safely".** True: it is the sentence the 10 plain reads prove rather than falsify. The false absolute it replaced is gone — `grep -c 'ONLY reason the two coexist safely'` -> `0`, exit 1.
- **"Treat the values as ``FieldMeta | Any`` until the registry-coverage gate lands".** Unchanged in substance from `HEAD`; still true.
- **"``types/resolvers.py::_field_meta_for_resolver`` shares the policy … but not this dual return shape: it returns a ``FieldMeta`` unconditionally, so its callers read every attribute directly".** True on all three clauses, read from `types/resolvers.py` at this pass: the function is annotated `-> FieldMeta` with three exits (canonical `registry.get_definition(parent_type)` -> `definition.field_map.get(field.name)` returned only when not `None`; `FieldMeta._from_field_shape(field, is_relation=True)` under `not hasattr(field, "is_relation")`; `FieldMeta.from_django_field(field)` otherwise), so no branch lets a raw Django field escape. Consumer side: `grep -n -o -E 'field_meta\.[a-zA-Z_]+' …types/resolvers.py` -> **11 plain reads** (`attname` x5, `related_model` x4, `relation_kind`, `is_many_side`) and `grep -rn 'getattr(field_meta' django_strawberry_framework/` -> **nothing, exit 1**. Zero defensive reads of a `_field_meta_for_resolver` result exist in the package.
- **The pass-1 clause the ruling condemned is gone, not reworded around it.** `grep -c 'need no ``getattr`` default'` -> `0`, exit 1.

**Verdict: no clause is false, and the rule-not-a-safe-list shape held under temptation** — `related_model` is 6 of the 10 direct reads and appears **nowhere** in the landed text, which is right, because `walker.py:342` hedges that very attribute with a `getattr` default and `_DjangoFieldLike` does not promise it. A three-item list would have been contradicted by the module's own code.

### 3. F8's cross-reference: one spelling, no third form in any `.py`

- `grep -rn "optimizer/resolvers" django_strawberry_framework/` -> nothing, **exit 1** (3a reproduced).
- `grep -rIn --include='*.py' -o -E '[A-Za-z_/.]*resolvers\.py::_field_meta_for_resolver' .` -> **exactly two occurrences, both `types/resolvers.py::_field_meta_for_resolver`**: `optimizer/walker.py:315` and `optimizer/field_meta.py:204`. No bare-basename, dotted, or `optimizer/`-prefixed variant exists in any `.py`.
- Folder segment still load-bearing: `find django_strawberry_framework -name resolvers.py` -> **four** paths (`types/`, `forms/`, `mutations/`, `rest_framework/`), re-measured.
- **One reference to the symbol was missed by all three prior censuses and is recorded here rather than left to be re-found:** `optimizer/field_meta.py:310` carries the **bare symbol name** `` ``_field_meta_for_resolver`` `` with no path, inside `_target_pk_name`'s docstring. It is not a third spelling of the F8 reference (it is not a path reference at all) and it is **pre-existing at `HEAD`** in a file clean at baseline (`git grep -n … HEAD -- …/field_meta.py` returns it), so it is neither a defect of this round nor in any round's writable set. It is the bare-symbol edge of the acquitted shorthand convention; catalogued for the final gate as item 12.
- 3d regression guards reproduced: `_record_pending_relation` and `extension\.check_schema` both absent from package source, **exit 1** each.

### 4. Ruling on the `### Dispatched findings checklist` — both ticks stand, and no marker should have changed

**Audited against `git diff HEAD -- django_strawberry_framework/optimizer/walker.py`, not against the reports.**

- **`- [x]` F8 — CONFIRMED.** The contract is "the reference reads `types/resolvers.py::_field_meta_for_resolver` and 3a prints nothing". Both re-measured above. The reword moved the occurrence `:312` -> `:315` and did not un-land it.
- **`- [x]` F8-sweep — CONFIRMED**, including its second assertion. All four sweep commands re-run by me. No near-miss site changed, confirmed two ways: `git diff HEAD --name-only` lists no `registry.py`, `types/converters.py`, `types/resolvers.py`, `optimizer/field_meta.py`, `tests/test_registry.py`, `CHANGELOG.md`, or `docs/builder/DONE/**`; and by content `walker.py:584` still carries the `finalizer.py::` shorthand and `walker.py:776` still `utils.relations.instance_accessor`.
- **Worker 2 changing no marker in pass 2 was CORRECT, and Worker 3 agreeing was correct.** The ruling created a **new obligation on an already-ticked round**, not a new dispatched box. Adding a box would have mis-recorded a custodian ruling as a dispatched finding; re-ticking an already-`- [x]` box is a no-op edit; and un-ticking would have been false, since both contracts survived the reword — the one thing worth checking, and it was checked. **No box remains `- [ ]`, so no deferral reason is owed under `## Final verification job` step 3.**
- **Required-amendment lists discharged** (`## Review-round custody`): Worker 0's mid-flight amendment (correct the over-claim in the same edit as F8) is on disk in pass 1's half of the hunk; the pass-2 ruling's amendment is on disk as the ruling's verbatim 13 lines. Both present, not merely recorded.

### 5. Corrections made to my own prose in this pass — the plan text is mine, so the defects in it are mine to fix

Three edits, all inside `## Plan (Worker 1)` and my pass-1 `## Final verification (Worker 1)`. **No prior Worker 2 or Worker 3 entry was edited** (`docs/builder/ARTIFACT.md` `## Re-pass sections`), which is why their sections still carry the superseded forms and this section is the reconciling record.

1. **`### Dispatched findings checklist`, the F8-sweep box's stated success condition.** It read "3c prints six rows with zero `*** UNRESOLVED ***`", which Worker 3 correctly reports is **unachievable as written** (the loop tries only package-root-relative and `optimizer/`-sibling candidate paths, so `types/`-relative shorthand can never resolve) and is **now two rows off** (seven rows since the ruling added a `field_meta.py::_DjangoFieldLike` citation). It does not stand: a proof condition no correct file can meet is not a proof condition. **Corrected to the form that is both true and provable**, re-measured at this pass: with `types/`-sibling added as a third candidate root, **all seven rows resolve** —
   ```
   121  ``extension.py::_build_cache_key``                      -> optimizer-sibling OK
   308  ``field_meta.py::_DjangoFieldLike``                     -> optimizer-sibling OK
   315  ``types/resolvers.py::_field_meta_for_resolver``        -> root-relative OK
   368  ``utils/querysets.py::apply_type_visibility_sync``      -> root-relative OK
   382  ``nested_fetch.py::unwindowable_child_queryset_reason`` -> optimizer-sibling OK
   584  ``finalizer.py::finalize_django_types``                 -> types-sibling OK
   745  ``plans.py::prune_unsupportable_select_related``        -> optimizer-sibling OK
   ```
   — and the box now also states the equivalent condition for the plan's two-root loop run verbatim (**seven rows, exactly one `*** UNRESOLVED ***`, and it is `:584`**). The 3b half of the same box is corrected too: its "only hits are the two per-cycle artifacts" prediction was non-distinguishing (`git grep` cannot see untracked files) and its total is a moving figure, so the condition is restated as **zero `.py` files, survivors all per-cycle artifacts, measured with a plain recursive grep**. Both of Worker 2's and Worker 3's corrections to the plan are thereby folded into the plan rather than left as findings against it.
2. **`#### The `#"substring"` citation this reword breaks`, the re-point target.** My ruling recorded **#"lets the two shapes coexist safely"** for `docs/builder/DONE/build-004-optimizer_beyond-0_0_3.md:257`. Worker 3's escalated Low is **upheld on my own measurement**: `grep -c 'lets the two shapes coexist safely' …walker.py` -> **0, exit 1** — the phrase spans `walker.py:312`/`:313` because of the wrapping in my own fixed text — while `grep -c 'lets the two shapes coexist'` -> **1**, `walker.py:312`. Corrected to the greppable form. This matters precisely because the target sits inside a *decided* deferral whose stated value is that a maintainer reversing it "has no work to re-derive": as recorded, that maintainer would have pasted a citation that greps to nothing, reproducing the class of defect F8 fixed inside the record of the decision not to fix it.
3. **The same box's clearance of the rationale companion's quotation.** I cleared #"until the registry-coverage gate lands" as "preserved verbatim". The words are preserved; the **line break is not** — `grep -c 'until the registry-coverage gate lands'` -> **0, exit 1**, the phrase now spanning `walker.py:313`/`:314`; the greppable form is **#"registry-coverage gate lands"** (`grep -c` -> 1, `walker.py:314`). The rationale's use is narrative prose quotation rather than a rule-27 citation, so nothing normative broke, but the clearance's **basis** was wrong: I measured it phrase-wise when the standing rule is line-wise. The companion's quotation is re-pointed in R3.

**The lesson, stated once for the final gate:** a `#"substring"` sweep is a **line-wise** grep of the exact bytes, run as precondition *and* postcondition, and the postcondition must be run against the text you yourself wrote — this cycle cleared a phrase as safe and broke it with its own wrapping in the same ruling.

**One citation that greps to zero and is CORRECT to leave that way, recorded so the final gate does not read it as a fourth break:** the F8 box's own `#"keep the two in"` and the F8 row's quotation of the old sentence cite the **pre-fix** source. They identify the defect that was removed; a citation into deleted text is the intended record of a fix, not a broken pointer.

### 6. Postcondition citation sweep — run line-wise over every phrase in or adjacent to the replaced block

Phrases swept: `Both shapes are read via`, `ONLY reason the two coexist`, `keep the two in sync`, `keep the two in`, `registry-coverage gate`, `Keep the policy in sync`, `lets the two shapes coexist`, `Treat the values as`, `DUAL CONTRACT`. Survivors outside this cycle's own per-cycle artifacts:

| Site | Phrase | Disposition |
|---|---|---|
| `docs/builder/DONE/build-004-optimizer_beyond-0_0_3.md:257` | #"ONLY reason the two coexist safely" | **Stale by design**, Worker 0's decided disposition. Verified **not edited** and clean (`git status --short -- docs/builder/DONE/` prints nothing; absent from `git diff HEAD --name-only`). I agree on the merits: the row quotes what the source said at that closed cycle, and rewriting a historical quotation to track a later reword falsifies the record it exists to preserve. The escape hatch is now executable (item 2 above). |
| `docs/dry/dry-0_0_11.md:387,506` | `registry-coverage gate` | Per-cycle scratchpad (`START.md` `## Temp artifact conventions`), and both hits **paraphrase** the gate rather than cite a substring. Nothing owed. |
| `docs/SPECS/appx/…-rationale.md:245` | #"DUAL CONTRACT (read before consuming the returned map)" | **Still greps**, `walker.py:304`, outside the replaced block. Unbroken. |
| `docs/SPECS/appx/…-rationale.md:263` | "until the registry-coverage gate lands" | **Wrapped, greps to zero.** Prose quotation, not a rule-27 citation, so nothing normative broke. **R3 re-points it** to the greppable form. |

No other file in the repository points into the replaced block.

### 7. What the round did not touch, re-verified

- **No baseline-dirty path edited or reverted.** `git diff HEAD --name-only -- django_strawberry_framework/` lists `connection.py`, `mutations/resolvers.py`, `optimizer/walker.py`, `orders/inputs.py`, `orders/sets.py`, `relay.py`, `templates/…/debug_toolbar.html` — every entry but `walker.py` a concurrent session's, `connection.py` the one that arrived mid-cycle. None carries a hunk attributable to this build.
- **The index is still swept.** `walker.py` remains `MM`. No worker may unstage it; `git add`/`git reset`/`git restore` were not run in this pass. The maintainer-facing hazard stands unchanged and is catalogued: a `git commit` on this index would place this round's docstring inside a commit describing another session's work.
- **Public surface unchanged.** `git diff HEAD -- django_strawberry_framework/__init__.py` -> no output.
- **No spec-016 staged anchor anywhere.** `grep -rIn -E 'TODO\(spec-016|TODO-(ALPHA|BETA|STABLE)-016' .` finds nothing outside this cycle's own artifacts describing the sweep. `walker.py`'s two `TODO(spec-035)` anchors belong to another card and are present and untouched.
- **No generated doc regenerated and none owed.** `docs/TREE.md` renders **module** docstrings; this is a **function** docstring. `KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md`, `examples/fakeshop/db.sqlite3` untouched.

### DRY re-check against prior accepted rounds

None owed and none found. R1 wrote only the spec and its companion; R2 adds no helper, constant, literal, branch, or parallel data flow — its hunk contains no executable token. The one cross-round shape is the **sentence pair** (this docstring paragraph and the spec's first bounded-exception bullet), two prose statements of one contract that must read as one; that is why the ruling fixed both texts verbatim instead of leaving either to a writer's discretion, and it is R3's remaining half.

The existence challenge is answered and stays answered: the two sites share one *policy* and share neither a return shape nor a read discipline, so a prose pointer is the DRY-correct form — a helper factoring their commonality would factor a statement, and a statement is what a cross-reference already is. The exit condition is in the source itself; when the registry-coverage gate lands, the walker's fallback disappears, the dual contract ends, and this cross-reference plus the whole `DUAL CONTRACT` paragraph plus the spec's first bounded exception should be **deleted**, not re-pointed. No refactor proposed.

### Focused test run

**None, and structurally rather than as a skip.** No assertion in any of the three test trees can change pass/fail on a hunk with no executable token; `grep -rn "_resolve_field_map\|DUAL CONTRACT\|__doc__" tests/ examples/` finds one hit, `tests/optimizer/test_walker.py:2105`, a test's own explanatory comment asserting nothing about this docstring. No `pytest` run and **no coverage-shaped flag anywhere in this pass** (`docs/builder/BUILD.md` `## Coverage is the maintainer's gate, not a worker's tool`). Hot-path budget not owed — the plan declares none and nothing executable changed. Floor verification not owed: **no floor-verification scope is declared for any round in this cycle**; floor facts quoted from `docs/builder/BUILD.md` `## Floor verification` rather than restated from memory — Django **5.2.16** on Python **3.10** with strawberry-graphql **0.316.0**, and the shared `.venv` is not the floor. Nothing was installed into the shared `.venv`.

### Spec changes made (Worker 1 only)

**None in this pass.** The spec's status lines are accurate. The one spec change this round decided — the `### Bounded exceptions to the single-source rule` first-bullet replacement, text fixed verbatim in `#### Exact replacement text — the spec bullet` — is **R3's**, so the docstring and the spec reach the maintainer in one commit. That is the same reason Worker 0 gave for landing R2's over-claim correction inside R2, and editing it here would strand the pair again.

Recorded for R3: two candidate replacements for that one bullet exist in this artifact, and **R3 must land the later one** (`#### Exact replacement text — the spec bullet`, under the pass-1 ruling). Pass 1's earlier recommendation corrects only the bullet's closing sentence and leaves the false premise clause standing, which is exactly the defect Worker 3 escalated.

### Deferred work — this round's complete catalog input

Items 1-11 as recorded in the pass-1 ruling stand, re-verified at this pass, with two amendments and one addition:

- **Item 10 amended.** `docs/builder/DONE/build-004-…md:257`'s citation is **decided stale by design** (Worker 0), not a deferral by omission, and the recorded re-point target is **#"lets the two shapes coexist"** — the greppable single-line form, corrected from the longer phrase this cycle's own wrapping broke.
- **New: the rationale companion's `:263` prose quotation** of #"until the registry-coverage gate lands" is wrapped in the landed source; **R3 re-points it** to #"registry-coverage gate lands". Not a deferral — it closes this cycle.
- **New item 12: `django_strawberry_framework/optimizer/field_meta.py:310`** carries the **bare symbol** `` ``_field_meta_for_resolver`` `` with no path, inside `_target_pk_name`'s docstring. Pre-existing at `HEAD`, file clean at baseline, outside every round's writable set. The bare-symbol edge of the acquitted shorthand convention (item 6) — recorded so the next sweep neither re-discovers it as new nor "fixes" it in isolation.

### Summary

The round shipped one docstring hunk in `django_strawberry_framework/optimizer/walker.py::_resolve_field_map`, `-8 / +13`, no executable token: F8's cross-reference now reads `types/resolvers.py::_field_meta_for_resolver` (one spelling, two `.py` occurrences, zero of the never-existent module), and the `DUAL CONTRACT` paragraph's false absolute is replaced by the rule the file actually obeys — `name` and `is_relation` guaranteed on both shapes and read directly, any other attribute read directly only where both shapes carry it, a `FieldMeta`-only attribute never read off the map without a `getattr(..., default)`. Every clause verified true against source at this pass; the negative check (no `FieldMeta`-only attribute read off a map value anywhere) is what proves the rule rather than the count. Three defects in my own plan/ruling prose are corrected in place — an unachievable proof condition and two `#"substring"` citations my own reflow broke. The spec half of the pair is R3's, with its text fixed.
