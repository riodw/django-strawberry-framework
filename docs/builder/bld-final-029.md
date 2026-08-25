# Build: Final test-run gate — 029 (consumer_dx_cleanup / 0.0.9)

Spec reference: `docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md` (whole file; the cycle's reconciled contract)
Build plan: `docs/builder/build-029-consumer_dx_cleanup-0_0_9.md`
Status: final-accepted

Last checklist item of the residual / reconciliation cycle on `DONE-029-0.0.9`. All four slices and
the cross-slice integration pass are `final-accepted`. This pass runs the gate, verifies the
floor-verification backstop, derives the deferred-work catalog from the five closed artifacts, and
hands off to the maintainer.

---

## Plan (Worker 1)

### DRY analysis

**Helper inventory checked — not applicable to this pass.** `worker-1.md` `### Package-wide helper
inventory before helper planning` binds a *planning* pass that proposes helper-like logic. This pass
writes no `.py`, no spec, no rationale and no test; it runs read-only commands and writes two
Markdown files. Recording the dismissal rather than manufacturing an inventory nothing would consume.

- **Existing patterns reused.** The gate command set is `BUILD.md` `## Final test-run gate` verbatim
  and the artifact shape is `docs/builder/ARTIFACT.md` plus the sibling precedent
  `docs/builder/bld-003-final.md`. Nothing is invented here.
- **New helpers justified.** None. Four throwaway instruments were written for this pass (a
  forbidden-form AST classifier, a docstring-stripped AST identity comparator, a module-docstring
  comparator, and an out-of-repo copy of `check_citations.py`), all under the scratchpad **outside
  the repo** and all discarded. None is a repo artifact and none is proposed as one.
- **Duplication risk avoided.** The one real risk was copying the integration pass's assembled
  catalog instead of deriving it. Every catalog row below was re-derived from the artifacts and from
  disk; three rows changed as a result (see `### Corrections to the handed-down catalog`).

### Implementation steps

1. Read the required-reading set for Worker 1, the build plan, and all five closed artifacts.
2. Run the gate commands in `BUILD.md` order, firing a known-bad control on each instrument first.
3. Confirm Slice 2's floor verification ran and was recorded; confirm Slices 1/3/4 and integration
   declared `none` correctly.
4. Re-prove, rather than accept, the three mechanical claims the cycle's product rests on.
5. Derive `### Deferred work catalog` from the artifacts; verify the integration pass's raw material
   rather than copying it.
6. Set `Status:` and append a memory entry.

### Test additions / updates

None. This pass adds no test and modifies none. The suite is executed, not extended.

### Implementation discretion items

None. There is no downstream worker; nothing is delegated.

### Dispatched findings checklist

- [x] `uv run pytest --no-cov` — full sweep across all three test trees
- [x] `uv run python examples/fakeshop/manage.py check`
- [x] `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run`
- [x] `uv run ruff format --check .`
- [x] `uv run ruff check .`
- [x] `git diff --check`
- [x] `uv run python scripts/check_spec_glossary.py --spec <spec-029>`
- [x] `uv run python scripts/check_citations.py`
- [x] `uv run python scripts/check_trailing_commas.py --check`
- [x] Floor-verification backstop confirmation (Slice 2 owner; Slices 1/3/4 + integration `none`)
- [x] Hot-path budget, failability proofs, fail-open shapes — dismissals confirmed, not manufactured
- [x] Staged-anchor sweep for `TODO(spec-029`
- [x] `### Deferred work catalog` derived from all five artifacts and verified against disk

---

## Gate report (Worker 1)

### Environment, read rather than remembered

`BUILD.md` `## Floor verification` forbids stating the shared environment's versions from memory or
from a written-down number. Read at this pass with `uv pip list` and `.venv/bin/python -V`:

| Component | Shared `.venv` at this gate | Supported floor (`BUILD.md`) |
|---|---|---|
| Python | 3.14.2 | 3.10 |
| Django | 6.1 | 5.2.16 |
| strawberry-graphql | 0.323.2 | 0.316.0 |
| channels | 4.3.2 | — |
| pytest | 9.0.3 | — |

The gate below runs in the shared `.venv`. The floor is a separate, already-executed run recorded
under `### Floor verification`.

### Working tree, attributed

`git status --short` at this pass. Attribution is by the build plan's per-slice ownership table,
never by `git status` itself.

**This cycle's, modified:** `django_strawberry_framework/types/base.py` (Slices 3-4 + integration),
`docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md` (Slices 1, 3),
`docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md` (Slice 1, citation repair only),
`examples/fakeshop/strategy_schemas.py`, `examples/fakeshop/test_query/test_products_visibility_api.py`,
`tests/forms/test_resolvers.py`, `tests/mutations/test_resolvers.py`,
`tests/mutations/test_write_transaction.py`, `tests/optimizer/test_extension.py`,
`tests/test_ci_governance.py`, `tests/test_relay_connection.py`, `tests/types/test_resolvers.py`
(all Slice 2).

**This cycle's, new:** `docs/SPECS/appx/spec-029-consumer_dx_cleanup-0_0_9-rationale.md`, the build
plan, and the five `bld-*-029` artifacts.

**A concurrent session's, neither edited nor reverted** (`AGENTS.md` rule 34, rule 22):
`docs/review/review-0_0_14.md` (modified), `docs/review/rev-django_strawberry_framework.md`,
`docs/review/rev-final.md`, `docs/review/rev-management.md`,
`docs/review/rev-mutations__operations.md`, `tests/mutations/test_operations.py` (all new).

Nothing is staged (`git diff --cached` = 0 lines). No branch was created or switched, no `git stash`
/ `checkout` / `restore` / `worktree` was used at any point, and every pristine read went through
`git show HEAD:<path>` into a scratch path outside the repo.

### Gate commands, in `BUILD.md` order

| # | Command | Result |
|---|---|---|
| 1 | `uv run pytest --no-cov` | **PASS** — `6525 passed, 42 skipped in 63.74s`, exit 0 |
| 2 | `uv run python examples/fakeshop/manage.py check` | **PASS** — `System check identified no issues (0 silenced).`, exit 0 |
| 3 | `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` | **PASS** — `No changes detected`, exit 0 |
| 4 | `uv run ruff format --check .` | **PASS** — `429 files already formatted`, exit 0 |
| 5 | `uv run ruff check .` | **PASS** — `All checks passed!`, exit 0 |
| 6 | `git diff --check` | **PASS** — no output, exit 0, over a live 1,791-line diff |
| 7 | `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md` | **PASS** — `OK: 44 terms - all have glossary entries and at least one spec link.`, exit 0 |
| 8 | `uv run python scripts/check_citations.py` | **PASS** — `OK: 789 citations resolve (712 in 426 .py files, 77 in KANBAN.md).`, exit 0 |
| 9 | `uv run python scripts/check_trailing_commas.py --check` | **PASS** — no output, exit 0 |

**No `--cov*` flag was used in any command of this pass.** `--no-cov` is the only coverage-shaped
flag anywhere here, and no line-coverage figure was read, inspected, or asserted
(`BUILD.md` `## Coverage is the maintainer's gate, not a worker's tool`).

**No lint/format/diff failure**, so the pre-flight baseline-exception clause in
`worker-1.md` `## Final test-run gate` is not reached. Neither of the build plan's two recorded
pre-flight exceptions concerns lint or formatting.

**Sweep scope, measured rather than assumed.** `uv run pytest --no-cov -q --collect-only` at this
pass reports **6,565 tests collected** across the four `pytest.ini` `testpaths`
(`tests`, `examples/fakeshop/tests`, `examples/fakeshop/test_query`, `examples/fakeshop/apps`) and
the collection listing carries `<Module test_operations.py>` at its line 2925 — so the concurrent
session's new file **was** inside the sweep, and "no failure in their files" is a reading rather than
a vacuous statement. The collect-only reading (6,565) and the sweep's row total (6,525 + 42 = 6,567)
differ by 2; both are stated as measured, and the difference is not explained here rather than being
explained by guess. Neither figure is a coverage reading.

### Instrument controls — every gate fired on a known-bad input first

`worker-1.md` and this cycle's standing caution: a control that did not run reads identically to a
passing proof. Ten instruments died silently earlier in this cycle. Each gate below was therefore
fired on a known-bad input, **outside the repo**, before its clean reading was believed.

| Instrument | Control | Fired? |
|---|---|---|
| `ruff format --check` | badly-formatted scratch `.py` | yes — exit 1, `1 file would be reformatted` |
| `ruff check` | same file | yes — exit 1, `Found 5 errors.` |
| `git diff --check` | `git diff --no-index` over two scratch files carrying trailing whitespace and a `<<<<<<< HEAD` marker | yes — exit 3, both classes named |
| `check_spec_glossary.py` | **both arms**: an unmutated out-of-repo copy of the spec + its terms CSV under a scratch `GLOSSARY.md` (exit 0, `OK: 44 terms`), then the same copy with one `GLOSSARY.md#` anchor repointed to `#bogus-anchor-xyz` | yes — exit 1, `AggregateSet` reported missing |
| `check_citations.py` | **both arms**: an out-of-repo copy of the script over a two-file scratch tree (the script derives its root from its own location, so no repo mutation was needed) — resolving citation exit 0, then the same file citing `::vanished_symbol` | yes — exit 1, `defines no vanished_symbol` |
| `check_trailing_commas.py --check` | an out-of-repo `.py` carrying one non-ASCII character | yes — exit 1, `non-ASCII U+00E9` |
| staged-anchor sweep | liveness: the same grep for `TODO(spec-` of **any** number returns 9 hits in `.py` and 96 in `.md` tree-wide, so the pattern class is findable and the `spec-029` zero is a reading | yes |

`git diff --check` structurally cannot see an untracked file. This cycle's seven new files were
therefore checked separately with `git diff --no-index --check /dev/null <path>`: all seven returned
exit 1 (differences, as expected against `/dev/null`) with **zero** whitespace or conflict-marker
lines.

### Floor verification — backstop confirmation, not a second owner

The build plan's `## Floor-verification scope` assigns the floor run to **Slice 2, owning pass:
Worker 2's build pass**, and declares `none` for Slices 1, 3, integration (Slice 4 was opened
mid-cycle and declared `none` in its own plan). `BUILD.md` makes this gate the backstop that
confirms it happened. **It happened and it is recorded**, so it is not re-run here.

| Item | Recorded at | Value |
|---|---|---|
| Scratch venv, outside the repo | `bld-slice-2-…md` `### Floor verification` (pass 1) | `/tmp/dsf-floor-029` |
| Python | read with `/tmp/dsf-floor-029/bin/python -V` | **3.10.19** |
| Django | read with `uv pip list --python /tmp/dsf-floor-029/bin/python` | **5.2.16** |
| strawberry-graphql | same reading | **0.316.0** |
| Focused scope, 9 files | `… -m pytest <8 edited files> tests/test_ci_governance.py --no-cov -q` | **PASS** — `550 passed in 15.21s` |
| Second focused scope | `… test_optimizer_auto_api.py tests/test_lateral_pg_parity.py` | **PASS** — `2 passed, 35 skipped` |
| Hot-path scope | `… docs/builder/temp-tests/slice-2-029/test_hot_path_budget.py` | **PASS** — both readings identical to head |
| Re-run at pass 4 | `bld-slice-2-…md` pass-4 `### Floor verification` | **PASS** — `86 passed`, same three resolved versions |
| Shared `.venv` unmutated | recorded in both floor sections | confirmed there, and re-confirmed here: `.venv` reads Django 6.1 / strawberry 0.323.2 / Python 3.14.2, and `git status --short -- pyproject.toml uv.lock` is empty |

The plan's declaration also asked for the load-bearing mechanism to be re-derived **by execution** at
the floor rather than inferred; Slice 2 recorded `Schema.get_extensions`'s source as read out of the
0.316.0 venv with `inspect.getsource`, identical in its load-bearing clause to the 0.323.2 reading.
That closes Decision 3's mechanism across the whole supported range.

**Slices 1, 3, 4 and integration each declared `none`, and each declaration is correct** — confirmed
by reading all four rather than by trusting the plan:

- Slice 1 — `### Floor verification`: `Not applicable; the build plan declares Slice 1 none (no framework surface).` The diff contains zero `.py` bytes.
- Slice 3 — plan `### Scope declarations`: `Floor-verification scope: none. No framework surface.` Writes only `docs/SPECS/**`.
- Slice 4 — plan `### Scope declarations` and build report `### Floor verification`: `none`, on the ground that no Django / Strawberry / channels seam is touched and a docstring cannot diverge across framework or interpreter versions. Executable-byte identity (re-proved below) is what makes that non-arguable.
- Integration — `### Scope declarations`: `none`. Its one source edit is a `#` comment.

**No planned floor verification went unrun**, so no `revision-needed` is owed under
`BUILD.md` `### When it is required`.

### Hot-path budget

The build plan declares Slice 2 hot-path-adjacent with a **required number**, and `none` for Slices
1, 3, 4, integration and final. This pass is `none` and adds no per-item work, no lock, no
serialization point and no extra pass over a result set — it runs read-only commands.

Slice 2's required number exists and is not a proxy: `DjangoOptimizerExtension.cache_info()` across
two executions of one query on one schema reads **`misses=2, hits=0`** before the migration (a fresh
instance per request) and **`misses=1, hits=1`** after (one shared instance). That reading is the
proof the repair is a repair, and it was reproduced at the floor as well as at head.

### Failability proofs

**None; this pass introduces no boundary, guard, gate, or rejection path.** The dismissal is recorded
rather than a proof manufactured, per the dispatch and `BUILD.md`
`### What needs a proof, and what does not`. The pass writes two Markdown files and refuses no input
that was previously accepted.

Worker 1's two confirmations under `### Failability and fail-open checks`, discharged across the
cycle rather than inherited from prose:

- **The records EXIST for every boundary the cycle added.** The only new boundary in the cycle is
  Slice 2's governance pin, and `bld-slice-2-…md` carries a `### Failability proofs` subsection in
  every one of its four build passes, each with the anchor check, the pre-mutation scope state, the
  failing node ids listed rather than counted, the collection/setup error count, and the revert
  proved by byte comparison. Worker 3 re-registered its own mutations **before** making them in all
  four review passes. Slices 1, 3, 4 and integration each record `None; …no new boundary`, which is
  true of each diff.
- **No fail-open shape landed.** Read from the diff rather than inferred from a green suite. The
  cycle's only production-file diff is `django_strawberry_framework/types/base.py`, and that file is
  **executably identical** to HEAD (re-proved below), so no production expression changed at all.
  The one substantive new logic body is `tests/test_ci_governance.py` (+590 / −8): scanned for the
  catalogued shapes — bare `except`, `or []` / `or ()` / `or {}` fallbacks, silent `.get(` /
  `getattr(` defaults, `pass` / `continue` swallows, `# noqa`, `pragma` — and **zero** matched. The
  file is written explicitly against the class (a git-oracle guard that asserts `returncode == 0` and
  refuses to reason from an empty answer, and an inline note to *guard the answer, not one spelling
  of the incoherent input*).

### Staged-anchor sweep

`grep -rn "TODO(spec-029" --include="*.py" --include="*.md" .` returns **no live anchor**. The hits
are prose *about* the scaffold convention inside the spec (`:420`, `:424`, `:425`) and the companion
(`:48`, `:344`), plus the four prior passes' own sweep records inside `bld-*-029.md`. Zero `.py`
hits. Liveness control fired (above): the same grep with the number generalized finds 9 `.py` and 96
`.md` anchors tree-wide.

### Claims re-proved mechanically rather than accepted on prose

`worker-1.md` `### Verifying relocation / promotion claims` requires Worker 1 to run the proof itself
rather than read Worker 3's acceptance as discharge. The three claims the cycle's product rests on:

**1. The forbidden-form population: 25 sites in 8 files at HEAD, 0 on disk.** Re-derived here with an
AST classifier of my own, controlled at **9/9** before its reading was believed — 4 must-flag
snippets (bare class; bare constructing lambda; keyword-carrying constructing lambda; the
conditional `… if optimizer else []` form) and 5 must-not-flag (`lambda: _optimizer`;
`DjangoDebugExtension` bare; `DjangoDebugExtension` constructing lambda; a singleton assignment; the
deprecated instance form, which is a different rule). Corpus:
`git ls-files --cached --others --exclude-standard '*.py'` minus `*/temp-tests/*`.

| File | HEAD | bare | lambda | Disk |
|---|---|---|---|---|
| `tests/test_relay_connection.py` | 10 | 0 | 10 | 0 |
| `tests/optimizer/test_extension.py` | 7 | 0 | 7 | 0 |
| `examples/fakeshop/test_query/test_products_visibility_api.py` | 2 | 2 | 0 | 0 |
| `tests/mutations/test_resolvers.py` | 2 | 2 | 0 | 0 |
| `tests/forms/test_resolvers.py` | 1 | 1 | 0 | 0 |
| `tests/mutations/test_write_transaction.py` | 1 | 1 | 0 | 0 |
| `tests/types/test_resolvers.py` | 1 | 1 | 0 | 0 |
| `examples/fakeshop/strategy_schemas.py` | 1 | 0 | 1 | 0 |
| **total** | **25 in 8 files** | **7** | **18** | **0 in 0 files** |

Independent agreement with Slice 2's figure in every digit **and** in its 7-bare / 18-lambda
decomposition. The standing pin
`tests/test_ci_governance.py::test_no_active_source_uses_a_forbidden_optimizer_extensions_form`
exists at `:791` and passed inside gate command 1.

**2. `types/base.py`'s executable bytes are unchanged from HEAD.** Re-proved on a fourth independent
implementation: parse both files, strip the docstring from every `Module` / `FunctionDef` /
`AsyncFunctionDef` / `ClassDef`, `ast.dump(include_attributes=False)`, hash.

| Row | Result |
|---|---|
| pristine HEAD | `8382eb52608bb1a0` (118,250 dump chars) |
| working tree | `8382eb52608bb1a0` (118,250) — **IDENTICAL** |
| CONTROL A — a docstring-only mutation | `8382eb52608bb1a0` — correctly **invisible** |
| CONTROL B — a real executable change (one `def` renamed) | `11e3b2883bffec60` (118,258) — correctly **visible** |

Both arms fired, so the identity row is a reading and not a silent no-op. The hash matches Slice 4's
independently recorded `sha256=8382eb52608bb1a0` exactly. `git diff --stat` for the file is
**14 insertions / 11 deletions** over 5 sites: four docstring sites (Slice 4) plus one `#` comment
(the integration pass).

**3. The cycle changed no module docstring that `docs/TREE.md` renders.** Measured rather than
argued, because it is what licenses leaving `docs/TREE.md` alone. Of the 10 modified `.py` files, 9
have a byte-identical module docstring against HEAD; `tests/test_ci_governance.py`'s module docstring
grew (10 → 16 lines), but its **first line** — the only part `docs/TREE.md` renders, at `:455` and
`:681` — is unchanged: `Governance tests for the CI workflow definitions.` The comparator's control
(two differing docstrings) fired.

### Byte deltas, as measured at this gate

Stated as read from disk now, not as remembered from any artifact.

| File | HEAD | This gate | Delta vs HEAD |
|---|---|---|---|
| `docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md` | 170,042 bytes / 823 lines | **153,973 / 717** | **−16,069 / −106** |
| `docs/SPECS/appx/spec-029-consumer_dx_cleanup-0_0_9-rationale.md` | does not exist at HEAD | **77,032 / 459** | **+77,032 / +459** (new file) |
| `django_strawberry_framework/types/base.py` | 94,225 / 1,953 | **94,225 / 1,953** | **0 / 0** |

`types/base.py`'s zero delta is a real edit, not an unedited file: both changed enumerations are
same-length two-word swaps and the four docstring rewrites happen to balance. Saying so is the point
— a 0-byte delta and an untouched file read alike.

**The spec GREW, and here is why.** Slice 1's move took the deliberative layer out (a 40,781-byte
excision, leaving the spec at 133,713 bytes / 679 lines). Slice 3's reconciliation then put
**+20,260 bytes / +38 lines** back — because a corrected claim is longer than the false one it
replaces. "Scalar-only" becomes "non-relation model fields — scalar columns and file/image output
objects"; "calls `convert_scalar`" becomes the `convert_field_output` routing with both branches
named; a bare check-order list gains the clause saying *why* Relay-pk precedes relation. **A residual
cycle is not a size-reduction exercise.** The net against HEAD is still −16,069 bytes, and all of
that net is the rationale move, not the reconciliation.

### Corrections to the handed-down catalog

`BUILD.md` makes this artifact the catalog's only author and the dispatch requires verifying the
integration pass's raw material rather than copying it. Three rows changed on re-derivation.

1. **The terms CSV carries the retired scope claim on THREE rows, not two.** The hand-down names
   rows 44-45. Row **14** carries it too: `Relation handling,relation-handling,… Decision 10 scopes
   overrides to scalars and rejects relation override-targets.` That is C1's retired claim, in C1's
   own subject, stated about the very Decision C1 renamed. It survived four passes' sweeps because
   every one of them keyed on the *string* `scalar-only` or on the two `Meta.` rows, and row 14
   spells it `scopes overrides to scalars`. The spec's own corresponding bullet (`:28`) was corrected
   and now reads `scopes Slice 3's overrides to non-relation model fields`, so the CSV row is the
   stale mirror of a sentence the cycle already fixed. Same lesson, one more time: **sweep for what
   the claim is about, not for how the finding spelled it.**
2. **A new, un-graded site inside the fence** — see `### One finding this gate found that no prior
   pass graded` below.
3. **A two-byte disagreement between two artifacts' spec byte figures.** Slice 3's
   `### Byte counts, measured` closes at **153,975**; the integration pass's opens at **153,973** and
   asserts every "before" figure "matches the prior pass's recorded close" — for this row it does
   not. Disk at this gate reads **153,973**, agreeing with the integration pass. Neither figure
   appears in any durable document (`grep` for both spellings outside `docs/builder/bld-*` returns
   nothing), so nothing shipped is wrong; the defect is confined to two per-cycle scratchpads that
   close with the cycle. Recorded so a later reader does not treat the join as verified.

Everything else in the integration pass's raw material re-derived unchanged, including every line
number it cites: `CHANGELOG.md:101`, `:173`, `:184`, `:186`; `docs/GLOSSARY.md:1360`;
`docs/README.md:120`; `docs/SPECS/spec-034-permissions-0_0_10.md:419`; `KANBAN.md:366`, `:3597`,
`:3598`, `:3604`; `docs/TREE.md:455`, `:681`.

### One finding this gate found that no prior pass graded

**`docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md:27` enumerates 4 of the 5 per-name rejection
rules under an "every" quantifier.** The `ConfigurationError` gloss in `## Glossary terms used`
reads:

> raised at type-creation time for every Slice 3 validation failure (unknown / excluded /
> consumer-authored / relation override-target, both-sets collision) and by Slice 2's command for a
> bad type path.

The **Relay-suppressed pk** rule is absent. The shipped code rejects five (`types/base.py`
`unknown -> excluded -> consumer-authored -> Relay-pk -> relation`) plus the both-sets collision, and
every *normative* statement in the same spec is complete and correct (`:72`, `:250`, `:368`, DoD 11,
`## Implementation plan` `:413`). It is the only site in the spec that omits the rule rather than
merely ordering it late — which is exactly why every C4 instrument missed it: they all keyed on the
ordering vocabulary `relation / Relay-pk`, and a site that omits `Relay-pk` cannot match an ordering
grep.

**Pre-existing at HEAD, byte-identical.** `git show HEAD:<spec>` carries the same sentence verbatim at
its line 73 (the pre-move numbering). No pass of this cycle introduced or worsened it, and no
`bld-*-029.md` grades it — `grep -rln "every Slice 3 validation failure" docs/builder/` returns
nothing.

**Routed to the catalog, not to `revision-needed`.** The criterion, stated so the maintainer can
overturn it: it is pre-existing rather than introduced (the standing ruling is that a pre-existing
gap merely *documented* by a pass is a catalog item, one *introduced* by it is `revision-needed`); it
violates no code contract and every gate is green; it is a one-line gloss in a terms index, and the
spec's normative statements of the same rule set are complete. **It is inside the maintainer's
spec-files fence and the fix is one clause**, so the maintainer can direct it at commit time far more
cheaply than reopening four `final-accepted` slices. Suggested replacement, verified against source:
add `/ Relay-suppressed pk` before `/ relation override-target`.

### DRY check across the cycle

No new duplication. The cycle's only production diff is comment text in one file. Slice 2's 91
changed lines across eight test files migrate to **one** shape (a singleton plus
`extensions=[lambda: _optimizer]`), with function-local singletons at the conditional sites — which
avoids the duplication a module-level singleton would have created by constructing an optimizer for
the no-optimizer parametrization too. The one DRY candidate the cycle surfaced
(`_validate_optimizer_hints` vs `_selected_meta_targets`) was **judged and declined with a recorded
reason** by the integration pass rather than deferred by default, and is carried below as a
future-spec candidate rather than as this cycle's residue.

### Spec status-line re-verification (owed by every Worker 1 spawn)

Read `docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md` lines 1-8 at this pass: title, the
`Shipped in 0.0.9` banner with its explanation of why the `## Slice checklist` stays unticked,
`Status: **SHIPPED (0.0.9)**` naming card `DONE-029-0.0.9` and the `CHANGELOG.md` `## [0.0.9]`
heading, `Owner:`, and `Predecessors:`. **Nothing there is falsified by this build**, the
rationale-companion pointer the header carries resolves to a file that now exists, and the falsified
`Risks and open questions` clause the header used to carry was already deleted by Slice 1. **No edit
made.**

### Deferred work catalog

The next spec author's reading list. Derived by walking every per-slice and integration artifact's
spec-reconciliation notes, `What looks solid`, `DRY findings` and `### Notes for Worker 1` sections,
plus the build plan's section D, and re-derived against disk at this gate.

#### Closures — work this cycle DID, which must NOT be read as deferred

A catalog that defers work the cycle actually did is the same false-description defect this cycle
exists to repair. These four are stated as closures.

- **CLOSED by Slice 4 — `django_strawberry_framework/types/base.py::_selected_meta_targets` named 2
  of its 3 callers.** Repaired by *deleting* the caller enumeration rather than extending it: the
  docstring now states the seam's contract ("every `Meta` key that targets a set of field names on
  the type"), which cannot rot when a fourth key lands. Source: `bld-slice-4-…md` plan, Decision 1.
- **CLOSED by Slice 4 — `types/base.py::_validate_nullability_override_targets`'s stated check order
  contradicted its own loop.** The docstring now reads
  `unknown -> excluded -> consumer-authored -> Relay-pk -> relation`, with a new clause saying *why*
  Relay-pk precedes relation, and the `Raises:` enumeration was brought into the same order. Source:
  `bld-slice-4-…md` Defects 2 / 2b.
- **CLOSED by the integration pass — `types/base.py::_validate_meta`'s third enumeration.** A `#`
  comment, not a docstring — the distinction is recorded rather than blurred, and the executable-byte
  identity proof is what carries it. Now reads the shipped order at `types/base.py:1297`. Source:
  `bld-integration-029.md` `### Spec changes made (Worker 1 only)`, obligation O2.
- **CLOSED by the integration pass — the thirteenth site, in the spec's `## Implementation plan`
  Slice-3 cell.** No module-scoped sweep could see it: both of Slice 4's enumerations were correctly
  scoped to `django_strawberry_framework/`, and this site is one surface over. Verified at this gate:
  spec `:413` now reads `… consumer-authored / Relay-pk / relation reject`. Source: same section.

One record correction, if a later reader quotes Slice 4's citation figures: the citations that
slice's diff broke are **one** (`#"The first half shared by"`) plus **one** from its final
verification (the retired `Every Meta key whose value is a set of field names…` phrase), not the "2
distinct" its first build report stated; the integration pass broke a third. All three live only
inside per-cycle artifacts that close with the cycle.

#### Deferred — outside the maintainer's spec-files-and-`.py`-files fence

- **`docs/SPECS/appx/spec-029-consumer_dx_cleanup-0_0_9-terms.csv` carries the retired *scalar-only*
  scope claim on THREE rows.** Row **44** twice ("forcing a **scalar** field nullable",
  "**scalar-only**, validated at type creation") and also describes the apply mechanism as "via the
  `convert_scalar` `force_nullable` tri-state", the narrow half of what C2 widened; row **45** once
  ("forcing a **scalar** field required"); row **14** once, in different words
  ("Decision 10 scopes overrides to scalars"). Row 14 is new at this gate — see
  `### Corrections to the handed-down catalog`. Source: `bld-slice-3-…md` `### Notes for Worker 1`
  item 3 (rows 44-45) plus this pass (row 14). Licensing: the cycle's fence excludes the CSV
  explicitly.
- **`CHANGELOG.md:101` carries the same retired claim** — "decouple a **scalar field's** GraphQL
  nullability" and "**scalar-only**". It corrects Slice 3's recorded conclusion that the CSV is "the
  only stale surface left anywhere". Licensing: `AGENTS.md` rule 21 plus the maintainer fence keep
  `CHANGELOG.md` closed to this cycle.
- **`docs/SPECS/spec-034-permissions-0_0_10.md:419` says "`Meta.nullable_overrides` is scalar-only
  (spec-029 Decision 10)"** — a cross-spec citation into a Decision this cycle renamed
  (`Scalar-only scope` → `Non-relation scope`) and restated. Its **conclusion** still holds (a
  non-nullable forward FK cannot be forced nullable, because relation targets are still rejected);
  only its cited reason is retired. Licensing: any other spec is out of fence.
- **Three standing docs enumerate the per-name rejection rules in the pre-repair order** —
  `CHANGELOG.md:101`, `docs/GLOSSARY.md:1360`, `docs/README.md:120`, each reading
  "unknown / excluded / consumer-authored / relation / Relay-suppressed-pk". All three re-verified on
  disk at this gate. **None is false** — each enumerates a rejected-target *set*, not an order — so
  this is the same coherence grade as the two sites the cycle fixed. `docs/GLOSSARY.md` is
  DB-generated: the fix is an ORM edit plus a regenerate, never a hand-edit
  (`START.md` "Rendered docs").
- **`KANBAN.md`'s `DONE-029` card body is stale in two ways.** `:3597` still names the **rejected**
  migration targets (`extensions=[DjangoOptimizerExtension]` class /
  `lambda: DjangoOptimizerExtension()` factory) as Slice 1's goal — both resolved *against* the card
  by Decision 3; `:3598` and `:3604` name the non-existent `examples/fakeshop/tests/test_commands.py`
  as Slice 2's test home, where the shipped tests are
  `examples/fakeshop/tests/test_inspect_django_type.py` and
  `tests/management/test_inspect_django_type.py`. DB-backed and out of fence. Source: build plan
  section D; Slice 2's carry-forward.
- **`KANBAN.md:366` already carries an open, unrelated item** against `docs/GLOSSARY.md`'s
  `## Schema introspection management command` entry, filed by the `spec-022` residual cycle. Noted
  so this cycle is not read as having missed it; **do not duplicate the filing.**
- **`docs/GLOSSARY.md`'s introspection entry owes three selector rejections, not two.** The same
  underlying item as `KANBAN.md:366`, kept as its own line because a catalog reader will look for it
  by this description rather than by the board reference.
- **`CHANGELOG.md:173`, `:184`, `:186`** carry `0.0.7`-era consumer snippets showing the deprecated
  instance form `extensions=[DjangoOptimizerExtension()]`. `:109` correctly *describes* the `0.0.9`
  migration and is fine as history. Source: Slice 2.
- **`tests/test_ci_governance.py`'s first docstring line under-describes the module** now that it
  carries a first-party-source pin — it still reads "Governance tests for the CI workflow
  definitions." Rewriting it requires regenerating `docs/TREE.md`, where it renders at `:455` and
  `:681`, and CI runs `build_tree_md.py --check`. That is Slice 2's **Amendment 1**; the recommended
  replacement is recorded in that artifact's pass-1 `### Notes for Worker 1`. Licensing:
  `docs/TREE.md` is outside the fence.
- **`docs/TREE.md` is stale at HEAD by exactly two lines**, both for the concurrent session's
  untracked `tests/mutations/test_operations.py`. The two insertion positions (`:515`, `:745`) are
  **carried from the integration pass, not re-measured here** — measuring them would mean rendering
  the file, and this cycle runs `build_tree_md.py` only with `--check`. Re-verified read-only at this
  gate:
  `build_tree_md.py --check` exits 1 and wrote nothing (`git status --short -- docs/TREE.md` is
  empty afterwards); `test_operations.py` appears **0** times in `docs/TREE.md` and the file is
  untracked. Attribution proved rather than asserted — this cycle changed no module docstring
  `docs/TREE.md` renders (see claim 3 above). **Not this cycle's and not to be fixed here**, and
  `build_tree_md.py` must only ever be run with `--check` in this cycle.
- **`docs/bug_hunt/temp-tests/resolvers_async_parity/` holds four forbidden-form entries** (two bare
  class in `test_connection_and_mutation_async.py:206` / `:271`, two constructing lambdas in
  `test_async_probes.py:264` / `:294`). Gitignored scratch, outside the pin's corpus **by design** —
  a pin walking the filesystem indiscriminately would pass in CI and fail on a developer machine.
  Listed so its exclusion is not mistaken for a miss.
- **`docs/builder/DONE/build-004-optimizer_beyond-0_0_3.md:239` carries a real `path #"substring"`
  citation that no longer resolves** — `docs/SPECS/spec-029-…md #"P1.1 — stale extension-lifecycle
  model"`. Slice 1's move relocated that string into the companion; the `spec-004` *companion*'s
  prose citation was repaired in-cycle under Worker 0's re-partition, but this archived per-cycle
  artifact was deliberately not. The same file's read-only-sibling assessment ("spec-029 (6 hits) |
  P1 / P1.1 / Decision 3 / Risks") is drifted for the same reason. No gate sees either.

#### Deferred — new at this gate, inside the fence

- **`docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md:27`'s `ConfigurationError` gloss enumerates 4
  of the 5 per-name rejection rules**, omitting the Relay-suppressed pk, under an "every Slice 3
  validation failure" quantifier. Pre-existing at HEAD byte-identical; graded by no pass of this
  cycle; inside the maintainer's spec-files fence and fixable in one clause. Full reasoning, and the
  criterion for not routing it to `revision-needed`, under
  `### One finding this gate found that no prior pass graded`. **The maintainer may overturn that
  routing.**

#### Deferred — test coverage and instrument integrity

- **The Relay-pk-before-relation precedence is a shipped contract pinned by no test** (Slice 4, L3).
  Spec `## Decision 8` failure-mode rule 4 states it, the repaired docstring states it, the code
  holds it, and no fixture pairs a relation pk with a Relay-shaped type and an override, so no row
  fails if the precedence is lost. **Owed row:** a test naming such a pk in `nullable_overrides` and
  asserting the **Relay** message rather than the relation one. Both halves of the fixture already
  exist and were confirmed present at this gate — the pattern at
  `tests/optimizer/test_walker.py::test_plan_relay_id_projects_attname_when_pk_is_relation`
  (`OneToOneField(..., primary_key=True)`) and the assertion neighbourhood at
  `tests/types/test_base.py::test_override_relay_suppressed_pk_raises`. **Explicitly not
  harness-impossible.** Licensing: the gap is **pre-existing at HEAD** and no slice of this cycle
  introduced a boundary, so neither `BUILD.md` `### Acceptance rule: weakly pinned is
  revision-needed` nor `### Harness-impossible interleavings` applies. `fail_under = 100`
  structurally cannot see it: both guards' statements are covered; what is unpinned is which wins
  when both are true.
- **ACCEPTED RESIDUAL, maintainer-facing — `tests/test_ci_governance.py` #"CORPUS_REGIONS = (" is
  unpinned.** Narrowing it fails **0** rows, and a same-arity substitution fails 0 rows while
  leaving the collected row count unchanged. Accepted as terminal by Slice 2's second final
  verification on a criterion that is structural and mechanically checkable, and re-confirmed at this
  gate: the constant has exactly **one** reader (`:675`,
  `@pytest.mark.parametrize("region", CORPUS_REGIONS, ids=CORPUS_REGIONS)`), that reader is a
  row-generating position, and no surviving assertion reads it as data — so narrowing it deletes
  rows rather than leaving a live boundary enforcing less, and no fix exists that is not subject to
  the identical edit. **The maintainer may overturn this**; the change would be inside
  `tests/test_ci_governance.py` and would inline the tuple into the decorator, which moves the
  narrowing target rather than removing it.
- **`types/base.py::_format_unknown_fields_error` enumerates its callers** and is currently complete
  and correct (`Meta.fields`, `Meta.exclude`, `Meta.optimizer_hints`, `nullable_overrides`,
  `required_overrides`, `filesystem_path_fields`, `relation_shapes`). It carries the same rot risk
  Slice 4's Decision 1 removed from `_selected_meta_targets`, and the argument for replacing it with
  a contract statement is already made there. Left alone deliberately, not overlooked.
- **`types/base.py::_validate_optimizer_hints` duplicates the unknown/excluded shape.** Judged by the
  integration pass and **declined for this cycle with the reason recorded**: the shapes are not
  near-copies, the genuinely common piece is already extracted as `_format_unknown_fields_error`,
  consolidating would widen the seam for one non-conforming caller, and the difference is the
  measurement that makes Slice 4's L2 ruling non-arbitrary. Candidate for a future spec's DRY pass,
  not a residue of this one.

#### Deferred — process and tooling blind spots

- **No gate validates a `path::Symbol` citation inside a `.md` file.** `scripts/check_citations.py`
  reports `712 in 426 .py files, 77 in KANBAN.md`; `docs/` is out of scope by design, stated in the
  script's own module docstring and re-confirmed at this gate by the out-of-repo control (its corpus
  is `SOURCE_TREES` plus `KANBAN.md` and nothing else). The spec's ~25 and the companion's ~6
  `path::Symbol` citations are checked by a reviewer or by nobody, and a symbol rename breaks them
  silently exactly as the `#"substring"` class does. Open since Slice 3's first review, and the
  integration pass depended on the blind spot three times (its O1 parenthetical, its O2 comment, and
  the A1 phrase are all prose or comments no gate can see).
- **The `## Current state` observation-vs-prediction rule's generalization is unrouted.** Slice 3
  established that a vintage-framed section's licence covers dated **observations** of the pre-build
  repo and not **predictions** about what the build would do, and gave it a durable home in the
  companion's `### Documentation-coherence passes`. The rule is not spec-029-specific: any spec with
  a vintage-framed section meets it. `docs/builder/BUILD.md` and `docs/builder/worker-1.md` are
  outside this cycle's fence and are corpus-ratchet-bound, so this is a **maintainer proposal that
  must name the bytes it retires**, not a worker edit.
- **The underscore-stripping slugger trap killed three instruments in this cycle**, each author
  reaching for the same reflex character class independently. `_` is a `\w` character GitHub's
  slugger keeps. It does not transmit by being written down — it transmits by a positive control on
  an **underscore-bearing** anchor. Worth one line wherever anchor-checking is described.
- **The zsh no-word-splitting trap killed a fourth**, three times in one cycle: an unquoted `$FILES`
  in a `--numstat`; four anchors shell-quoted into one argument; and a `for` loop whose `set -- $row`
  did not split. In every case a non-run read like a result. **Pass path lists and anchors as
  explicit separate arguments, never through a variable.** This pass hit the same family once more —
  `${PIPESTATUS[0]}` is a bash spelling and reads empty in zsh, which briefly made a gate's exit code
  unreadable; every exit code above is captured with a plain `$?` on the command's own line.
- **`docs/builder/build-029-consumer_dx_cleanup-0_0_9.md`'s section C under-describes the cycle.** It
  lists nine divergences; Slice 3 discharged eleven, its final verification added a twelfth site, and
  the integration pass added a thirteenth. Worker 0's file; the artifacts are the complete record.
- **Slice 2's static-helper skip reason is imprecise for one file.** Worker 3 wrote "The other six
  files are 2-8 changed lines each"; `tests/test_relay_connection.py` is **28** added lines. The
  skip's conclusion re-derives (28 is under the 50-line trigger for a file outside the package), so
  no trigger fires and nothing needs re-running — only the sentence is wrong.
- **`tests/test_ci_governance.py`'s corpus census fires on any untracked-but-not-ignored `.py`
  outside the corpus.** That is the gate doing its job, but in a repo worked by concurrent sessions
  one session's stray root-level `.py` can red another's suite. Recorded so the behavior is a decided
  answer rather than a surprise.
- **Slice 2's Amendment 1 and box-11 wording recommendations are records, not spec items.** Box 11 is
  true as written and was deliberately left unedited across three audits; Amendment 1 is the
  `docs/TREE.md`-gated docstring rewrite listed above. Both are noted so a later pass does not
  re-open them as omissions.
- **A two-byte disagreement between two artifacts' recorded spec byte figures** (Slice 3's close
  153,975 vs the integration pass's open 153,973, with disk at 153,973). Confined to per-cycle
  scratchpads; no durable document quotes either figure. Detail under
  `### Corrections to the handed-down catalog`.

---

## Final verification (Worker 1)

### Summary — what this cycle delivered

For the maintainer reading this cold at commit time.

`DONE-029-0.0.9` shipped its three functional slices long ago. This was a **residual /
reconciliation** cycle: it did not re-build the card, it closed the card's durable record and
repaired what later cards had broken. Four things landed.

1. **The rationale companion was authored** —
   `docs/SPECS/appx/spec-029-consumer_dx_cleanup-0_0_9-rationale.md`, 77,032 bytes / 459 lines, the
   one durable artifact the original build never produced. It is a **move**, not a copy: every
   `Justification:` and `Alternatives considered` block, the seven-revision chronology, and the
   preferred-answer/fallback layer of `## Risks and open questions` left the spec. The spec now
   reads as a clean current contract with no chronology, and each of the twelve Decisions keeps a
   one-line pointer to its deliberation.
2. **The spec was reconciled with HEAD across thirteen-plus divergences.** The build plan named nine;
   Slice 3 discharged eleven, its own final verification found a twelfth, and the integration pass
   found a thirteenth in a surface no module-scoped sweep could reach. The largest are the scope
   widening (overrides apply to non-relation model fields — scalar columns *and* file/image output
   objects — not "scalar-only"), the apply call site (`convert_field_output`, not `convert_scalar`),
   three `#"substring"` citations that resolved to zero occurrences, the shipped helper's real name
   and signature, and the corrected rejection check order.
3. **A live regression was root-caused and repaired: 25 forbidden `extensions=` entries in 8 files →
   0.** Decision 3 forbids the bare class and the constructing `lambda` because both re-instantiate
   the optimizer per request and give its instance-bound plan cache a zero hit rate; four later cards
   reintroduced them across five patch releases and nothing noticed, because the original
   definition-of-done used a one-shot build-time grep. All 25 sites are migrated to the
   singleton-factory form with **no assertion weakened** across 91 changed lines, and the number
   proving it is a repair reads `misses=2, hits=0` → `misses=1, hits=1`. Maintainer decision D1 also
   shipped a **standing governance pin**
   (`tests/test_ci_governance.py::test_no_active_source_uses_a_forbidden_optimizer_extensions_form`)
   so the rule stops depending on someone remembering a five-year-old spec. The mechanism was
   re-derived by execution at both ends of the supported range (0.316.0 at the floor, 0.323.2 in the
   shared `.venv`), so the repair rests on a measurement rather than on the spec's vintage.
4. **Four docstring sites in `django_strawberry_framework/types/base.py` were corrected** — a caller
   enumeration that named 2 of 3 (fixed by *deleting* the enumeration in favour of a contract
   statement, so it cannot rot again), a stated check order that contradicted its own loop, that
   paragraph's `Raises:` clause, and one `#` comment carried by the integration pass. **The
   executable bytes are unchanged**, proved here on a fourth independent implementation with both
   control arms fired: docstring-stripped `ast.dump` hashes `8382eb52608bb1a0` for pristine HEAD and
   for the working tree alike.

**Byte deltas, as measured at this gate, not as remembered.** The spec is **153,973 bytes / 717
lines** against **170,042 / 823** at HEAD — a net **−16,069 / −106**, all of which is the rationale
move. `types/base.py` is **94,225 / 1,953** at both ends: a real edit with a 0-byte delta, because
both enumeration fixes are same-length two-word swaps.

**The spec GREW, and that is correct.** After Slice 1's move it stood at 133,713 bytes; Slice 3's
reconciliation added **+20,260 bytes / +38 lines** back. A corrected claim is longer than the false
one it replaces — "scalar-only" becomes "non-relation model fields (scalar columns and file/image
output objects)", and a bare check-order list gains the clause explaining why Relay-pk precedes
relation. A residual cycle is not a size-reduction exercise, and a spec that shrank here would have
shrunk by dropping a correction.

**Gate outcome.** All nine gate commands pass, each on an instrument fired against a known-bad input
first. Slice 2's floor verification ran and is recorded at Python 3.10.19 / Django 5.2.16 /
strawberry-graphql 0.316.0 in `/tmp/dsf-floor-029` with the shared `.venv` unmutated; Slices 1, 3, 4
and integration correctly declared `none`. No staged anchor survives. No fail-open shape landed. The
one new finding this gate produced is a pre-existing one-clause spec gloss, catalogued rather than
re-looped, with the criterion stated so it can be overturned.

**Two things the maintainer may want to overturn**, both flagged deliberately rather than buried: the
`CORPUS_REGIONS` acceptance, and the routing of `spec-029:27` to the catalog instead of back through
Slice 3.

### Spec changes made (Worker 1 only)

**None.** This pass edited no spec, no rationale companion, no terms CSV, no `.py` file, no test, no
`CHANGELOG.md`, no `KANBAN.md` / `KANBAN.html`, no `docs/GLOSSARY.md`, no `docs/TREE.md`, no
`pyproject.toml` / `uv.lock`, no `examples/fakeshop/db.sqlite3`, no `docs/review/**`, none of the
five closed artifacts, `docs/builder/bld-003-final.md`, or Worker 0's build plan. Its only writes are
`docs/builder/bld-final-029.md` and `docs/builder/worker-memory/worker-1.md`. Nothing was committed,
and no branch was created or switched.

No checklist box in this artifact is left `- [ ]`, so no deferral reason is owed under this heading.

### Final status

`final-accepted`. Every gate command passes, the floor-verification backstop is confirmed rather than
re-run, and the deferred-work catalog is derived and verified. Worker 0 may mark the build plan's
final checkbox and hand off to the maintainer.

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
