# Build: final test-run gate — serializer_mutations / 0.0.13 (039), residual-reconciliation cycle

Spec reference: [`docs/SPECS/spec-039-serializer_mutations-0_0_13.md`][spec-039] (archived; shipped
in `0.0.13`). Rationale companion: [`docs/SPECS/appx/spec-039-serializer_mutations-0_0_13-rationale.md`][spec-039-rationale].
Build plan: [`docs/builder/build-039-serializer_mutations-0_0_13.md`][build-039].

Status: final-accepted

## Artifact shape: one Worker 1 pass

This is the final test-run gate of `docs/builder/BUILD.md` `## Final test-run gate`. It runs
every command that section names, records each one's pass/fail, attributes every failure, and
carries the `### Deferred work catalog`. Worker 1 is its only author; it has no build report and
no review section.

**The headline: the gate is green, and the cycle's own expectation that it would be red is
falsified.** The dispatch that opened this pass instructed it to expect a red full sweep from the
concurrent `spec-050` cycle and to attribute rather than fix it. The sweep is green. `### 1` and
`## Escalation C is resolved in the working tree` record what changed and prove it was not this
cycle that changed it.

## Gate results

| # | Command | Result |
|---|---|---|
| 1 | `uv run pytest --no-cov` | **PASS** — `7651 passed, 40 skipped in 70.27s` |
| 2a | `uv run python examples/fakeshop/manage.py check` | **PASS** — `System check identified no issues (0 silenced).` exit 0 |
| 2b | `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` | **PASS** — `No changes detected`, exit 0 |
| 3a | `uv run ruff format --check .` | **PASS** — `445 files already formatted`, exit 0 |
| 3b | `uv run ruff check .` | **PASS** — `All checks passed!`, exit 0 |
| 3c | `git diff --check` | **PASS** — exit 0, zero output lines |
| 4 | Floor verification (Django 5.2.16 / Python 3.10 / strawberry-graphql 0.316.0) | **PASS** — confirmed and independently re-run; see `### 4` |

No `--cov*` flag appears in any command in this pass. No write-mode `ruff` run was issued — a
`ruff format` or `ruff check --fix` here would have rewritten the concurrent session's dirty
files.

### 1. `uv run pytest --no-cov` — full sweep across all four test trees

```text
platform darwin -- Python 3.14.2, pytest-9.1.1, pluggy-1.6.0
django: version: 6.1, settings: config.test_settings (from ini)
testpaths: tests, examples/fakeshop/tests, examples/fakeshop/test_query, examples/fakeshop/apps
8 workers [7689 items], scheduling tests via LoadScopeScheduling
================= 7651 passed, 40 skipped in 70.27s (0:01:10) ==================
```

Exit 0. `0` lines matching `^FAILED` or `^ERROR` in the full 15,394-line log. Interpreter and
Django here are the shared `.venv`'s ceiling, read from pytest's own banner rather than restated:
Python 3.14.2 / Django 6.1. That is the ceiling, not the floor; `### 4` covers the floor.

**Attribution verdict: vacuous, and stated as such.** There are zero failures, therefore zero
tracebacks, therefore no traceback names a file this cycle touched. The dispatch's condition for a
genuine blocker — "a failure that does name one of this cycle's files" — has an empty population.
This is a stronger result than the attributed-external-failure record the dispatch anticipated,
and it is worth naming that it is stronger for a reason outside this cycle's control.

## Escalation C is resolved in the working tree, and this cycle did not resolve it

Escalation C (recorded in `bld-039-slice-3-code_gaps.md` `### Escalation C` and carried by every
later artifact) held that `HEAD` at `4c483b6b` was red in four modules from the concurrent
`spec-050` cycle, with two deliberately-unreconciled scope figures: **7** failures in the full
parallel sweep and **12** over those four modules in isolation. Both figures are now historical.

**What changed.** `git log --oneline -1` still reads `4c483b6b` — **`HEAD` has not moved since the
integration pass**. The change is entirely in the working tree: the concurrent cycle kept editing
its own uncommitted files after the integration pass closed. The gate measures the working tree
(`docs/builder/BUILD.md` `## Final test-run gate` runs the commands against the tree as it stands,
and `START.md` "Pre-commit and CI gates" states the same for every `--check`), so a green tree is
a green gate.

**Proof that the resolution is the concurrent cycle's and not this one's.** Four independent
measurements, none of them a reading:

1. **Every one of Escalation C's seven node ids now passes.** Six pass under the same node id.
   The seventh, `tests/test_list_field.py::test_list_arguments_immutability_and_slots`, no longer
   exists: the concurrent cycle **renamed** it — it is `test_list_arguments_immutability` at
   `tests/test_list_field.py:3585` in the working tree against
   `test_list_arguments_immutability_and_slots` at `:3582` in `git show HEAD:tests/test_list_field.py`
   — and the successor passes (`[gw7] [ 45%] PASSED tests/test_list_field.py::test_list_arguments_immutability`).
   A rename by a party this cycle may not edit is itself evidence of authorship.
2. **The four previously-red modules still carry zero `rest_framework` references.** Re-measured
   this pass: `tests/test_list_field.py` 0, `tests/utils/test_querysets.py` 0,
   `tests/orders/test_sets.py` 0, `examples/fakeshop/test_query/test_list_field_api.py` 0. The
   dispatch asked that this premise be verified rather than re-derived; it still holds.
3. **The fix is visible in a MIXED file and it is not in this cycle's half.**
   `django_strawberry_framework/utils/querysets.py` is MIXED. `git diff` over it separates cleanly
   into two authorships: this cycle's four docstring label strips (`spec-039 Md2` → `spec-039` at
   `::sync_pipeline_recourse`, `Md3` at `::related_visibility_queryset`, `Md4` at
   `::stringified_pks_present` and `::pks_all_present`), and the concurrent cycle's
   `"unevaluated"` → `"evaluated"` defect-code rename at five sites
   (`::_validate_post_orderset_result`, `::_seal_or_defect` ×2, `::_visibility_result_error`,
   `::_prepared_visibility_source`). That rename is exactly what
   `tests/utils/test_querysets.py::test_validate_post_orderset_result_routing_hints_none_vs_empty`
   asserts. **This cycle's half of that file is comment-only and cannot have turned a red row
   green.**
4. **The authorship split over the whole dirty `.py` population is mechanical.** Instrument:
   per-file `git diff -U0 -- <path> | grep -c '^[+-].*spec-039'`. Every file the concurrent cycle
   owns scores **0** — `_strawberry_patches.py`, `list_field.py` (118+/75-), `orders/sets.py`
   (40+/37-), `resource_policy.py`, `tests/test_list_field.py` (160+/6-),
   `tests/utils/test_querysets.py` (112+/6-), `tests/orders/test_sets.py` (92+/17-),
   `tests/test_graphql_core_patches.py`, `examples/fakeshop/test_query/test_list_field_api.py` —
   and every `.py` file this cycle's label strip touched scores non-zero. The split needs no
   judgement call.

**Consequence for the gate.** The blocking condition Escalation C named ("the final gate cannot
record a green full sweep until the maintainer resolves it") no longer obtains. Escalation C is
carried into the catalog as **resolved in the working tree, unresolved at `HEAD`** rather than
struck out, for the reason `### The decision` gives.

### 2. Django's own consistency checks against the example project

```text
$ uv run python examples/fakeshop/manage.py check
System check identified no issues (0 silenced).            # exit 0

$ uv run python examples/fakeshop/manage.py makemigrations --check --dry-run
No changes detected                                        # exit 0
```

Both exit codes were captured in their own invocation rather than read through a pipe:
`START.md` "Instruments that lie" and this cycle's own integration-pass note 4 both record that a
piped exit status reports the pipe's, and `${PIPESTATUS[0]}` is empty in this shell. The figures
above are the direct `$?` of each command.

### 3. Read-only lint / format / diff

```text
$ uv run ruff format --check .
445 files already formatted                                # exit 0
$ uv run ruff check .
All checks passed!                                         # exit 0
$ git diff --check
                                                           # exit 0, 0 lines
```

`ruff format --check` emits its standing `COM812`-conflicts warning; that is configuration advice,
not a finding, and `scripts/check_trailing_commas.py` owns single-line explosion for exactly that
reason (`AGENTS.md` rule 17).

**`git diff --check` cannot see this cycle's one new file, so it was checked separately.**
`tests/rest_framework/test_dry_import_ratchet.py` is untracked, so no diff exists for the gate's
command to read — the same fail-open shape as the tracked-path pre-commit hook's, one tool over.
Measured directly:

```text
$ git diff --check --no-index /dev/null tests/rest_framework/test_dry_import_ratchet.py
                                                           # exit 1 (files differ), 0 output lines
```

**Control, because a checker that cannot fail is a passing proof** (`START.md` "Instruments that
lie"): the same file copied to scratch with `x = 1   ` appended reports
`ctrl.py:100: trailing whitespace.` and exits **3**. So exit 1 with empty output is this
instrument's clean verdict, not its silence.

### 3-supplementary. The three spec-side gates, read-only

Not part of `docs/builder/BUILD.md`'s narrow gate, recorded because this is a spec-heavy cycle and
every prior pass published these three figures:

```text
$ uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-039-serializer_mutations-0_0_13.md
OK: 38 terms - all have glossary entries and at least one spec link.
$ uv run python scripts/check_citations.py --check
OK: 965 citations resolve (810 in 442 .py files, 155 in KANBAN.md).
$ uv run python scripts/check_trailing_commas.py --check
                                                           # exit 0, 0 lines
```

`38 terms` and `965` are unchanged from the integration pass's pass-2 record. `--check` was
passed explicitly to `check_trailing_commas.py`: its default is repo-wide **auto-fix**
(`START.md` `scripts/` table), which in this tree would rewrite the concurrent session's
untracked files.

### 4. Floor verification — confirmed as recorded, then independently re-run

The plan's floor-verification declaration: `none` for Slices 0–2; **Slice 3 owns** a focused run
at Django **5.2.16** / Python **3.10** / strawberry-graphql **0.316.0**, taken from
`docs/builder/BUILD.md` `## Floor verification`, the single canonical statement of the floor. This
gate is the **backstop confirming it happened**, not a second owner.

**Three runs are recorded across this cycle's artifacts, and all three are confirmed:**

| Recorded in | Scratch venv | Resolved versions as recorded | Scope | Recorded result |
|---|---|---|---|---|
| `bld-039-slice-3-code_gaps.md:821` (Worker 2, the declared owner) | `<scratchpad>/dsf-floor` | CPython 3.10.19, django 5.2.16, strawberry-graphql 0.316.0, djangorestframework 3.18.0 | `test_resolvers.py` + `test_dry_import_ratchet.py` + the live G2 row | `193 passed` |
| `bld-039-slice-3-code_gaps.md:1216` (Worker 3, re-ran the owner's scope) | same | read back identical | same | `193 passed` |
| `bld-039-integration.md:781` (volunteered) | `<scratchpad>/dsf-floor` | 3.10.19 / 5.2.16 / 0.316.0, DRF 3.18.0 | `tests/rest_framework/` | `497 passed` |
| `bld-039-integration.md:1638` (volunteered, pass 2) | `<scratchpad>/dsf-floor-pass2`, asserted to BE a venv | 3.10.19 / 5.2.16 / 0.316.0, DRF **3.18.1** | `tests/rest_framework/` | `498 passed` (`+1` = the new ratchet row) |

**This pass's own confirmation.** No new venv was built; `dsf-floor-pass2` was verified to be a
genuine virtual environment and then reused, so nothing was installed anywhere this pass.

```text
$ <scratchpad>/dsf-floor-pass2/bin/python -c "import sys; print(sys.prefix, sys.base_prefix, sys.version)"
sys.prefix       <scratchpad>/dsf-floor-pass2
sys.base_prefix  ~/.local/share/uv/python/cpython-3.10-macos-aarch64-none
3.10.19 (main, Jan 27 2026, 23:32:40) [Clang 21.1.4]
$ cat <scratchpad>/dsf-floor-pass2/pyvenv.cfg
version_info = 3.10.19 ; implementation = CPython ; uv = 0.9.29 ; include-system-site-packages = false

$ uv pip list --python <scratchpad>/dsf-floor-pass2/bin/python
django 5.2.16 | django-filter 26.1 | djangorestframework 3.18.1 | pytest 9.1.1
pytest-django 4.14.0 | pytest-xdist 3.8.0 | strawberry-graphql 0.316.0
```

The resolved versions read back **exactly** what `bld-039-integration.md:1638` recorded, and they
are the canonical floor. `djangorestframework` is present — the load-bearing precondition, since
absent it every `rest_framework` module skips and the run proves nothing.

Both declared scopes re-run at the floor, no `--cov*` flag, `-p no:cacheprovider`:

```text
$ <venv>/bin/python -m pytest -n0 --no-cov -q -p no:cacheprovider \
    tests/rest_framework/test_resolvers.py tests/rest_framework/test_dry_import_ratchet.py \
    "examples/fakeshop/test_query/test_products_api.py::test_g2_serializer_mutation_response_keeps_relation_with_bounded_query_count"
194 passed in 7.26s                                        # exit 0

$ <venv>/bin/python -m pytest --no-cov -q -p no:cacheprovider tests/rest_framework/
498 passed in 4.49s                                        # exit 0
```

**The `+1` against Slice 3's recorded `193` is explained, not waved through.** Slice 3's owner run
predates its own pass 2, which added one row to the DRY import ratchet's parametrization.
Re-measured: `--collect-only tests/rest_framework/test_dry_import_ratchet.py` → **`21 tests
collected`** against the 20 the plan text still names (a stale plan figure the slice artifact
already filed twice). `193 + 1 = 194`. The `tests/rest_framework/` figure needs no adjustment: it
reproduces `498` to the row.

**Verdict: floor verification PASS, and it genuinely happened.** No declared scope is unrun, so
the `revision-needed` ground `docs/builder/BUILD.md` `## Floor verification` names ("a planned
floor verification no pass ran") does not apply.

**One recorded floor path is no longer re-derivable, and that is a known, already-routed hazard,
not a falsified claim.** `<scratchpad>/dsf-floor` — the path the Slice 3 and integration-pass-1
runs name — still holds `bin/` and `lib/` but has **no `pyvenv.cfg`**, exactly as
`bld-039-integration.md`'s notes recorded. Scratch decays; a floor record naming only a scratch
path cannot be audited later. This does not impeach those runs (a decayed venv fails loudly at the
first import, so the recorded `193` / `497` could not have come from the decayed state), and
pass 2's reconstruction reproduces both. It is carried as catalog item 6.

## The decision: `final-accepted`, and why the pre-flight-exception question is moot

`docs/builder/BUILD.md` `## Final test-run gate` blocks `final-accepted` on a gate failure "unless
a pre-flight baseline exception was recorded in the plan's preamble". The plan recorded no such
exception, because `HEAD` was green at pre-flight (2026-09-04) and nothing needed excusing.

**The clause is not reached.** An exception excuses a *failure*. Every one of the six gate
commands passes, floor verification passes, and the three supplementary spec gates pass. There is
no failure to excuse, attributed or otherwise. The cycle closes `final-accepted` on the plain
reading of the gate, not on an attributed-external-failure record.

**The reasoning, stated for both branches, because the dispatch asked for it either way.**

- **Had the sweep still been red** as the dispatch expected, the honest verdict would have been
  `final-accepted` *with* an attributed-external-failure record — not `revision-needed`. The
  ground: `docs/builder/BUILD.md` `## Claims are proven mechanically` states that a failing test
  is **not worker-verifiable at all**, that recording the evidence plus escalating **discharges**
  the obligation, and that the maintainer is the only party who can run a clean `HEAD` tree.
  Holding a cycle whose own work is complete, on four modules it may not edit under `AGENTS.md`
  rule 34, would route an external blocker into this cycle's status line where no worker could
  ever clear it. `revision-needed` is reserved for a blocker in **this** cycle's work; a concurrent
  cycle's redness is not that. This branch is recorded rather than exercised.
- **The sweep being green** removes even that argument. The one caveat a maintainer must carry
  forward is stated plainly below.

**What the green sweep does and does not prove about `HEAD`.** It proves the **working tree**
passes. It does **not** prove `4c483b6b` passes, and this pass makes no such claim: `HEAD` is
unchanged, the fix lives in the concurrent cycle's uncommitted files, and reproducing a failing
test at `HEAD` needs the whole tree at `HEAD`, which `docs/builder/BUILD.md` puts outside a
worker's reach and which `git stash` / `checkout` / `restore` / `worktree` — all four banned here
and none used in this pass — are the forbidden shortcuts to. **Operational consequence for the
maintainer: committing this cycle's files alone, without the concurrent cycle's
`unevaluated`→`evaluated` rename and its test edits, restores the seven red rows.** Those files
are the concurrent cycle's to commit; this cycle's `.py` fence never overlaps them except in the
two MIXED files, whose halves are separated above.

## Also record, because the maintainer needs it at commit time

### `examples/fakeshop/apps/kanban/constants.py` goes stale the moment the new test file is staged

Verified live rather than carried: `examples/fakeshop/apps/kanban/constants.py:243-248` lists six
`tests/rest_framework/` files and **not** `tests/rest_framework/test_dry_import_ratchet.py`, which
is new and untracked (`git status --porcelain` → `?? tests/rest_framework/test_dry_import_ratchet.py`).

The `kanban-tracked-path-constants` pre-commit hook rewrites that module from `git ls-files`, so it
**cannot see an untracked file**. Today's green `uvx pre-commit` is that hook's documented
fail-open (`START.md` "Pre-commit and CI gates" hook 1: "Sees a new file only once STAGED;
`--all-files` before `git add` proves nothing"), not coverage of the new file.

**Remedy, and why no worker can perform it.** `uv run python
scripts/build_kanban_tracked_path_constants.py` **after** `git add`, landed as a **constants-only
sync commit** — the hook's `files:` pattern does not match that module, so it cannot roll itself
back. `constants.py` is a `.py` file and therefore inside this cycle's fence, but the regeneration
is impossible before staging, and staging is the maintainer's step. Skipping it means the hook
rolls back every later commit until the sync commit lands.

### What this cycle proved versus what it merely reports

The dispatch asks for this split plainly, so it is stated plainly.

**Mechanically proven, re-derivable by a reader from the tree:**

- The six gate commands' results and the three supplementary gates' figures, above, each with its
  exit code.
- Floor verification: the venv's identity (`pyvenv.cfg`, `sys.prefix`), its resolved versions read
  from `uv pip list`, and both declared scopes re-run to `194` / `498`.
- The Escalation C authorship split: four independent measurements in
  `## Escalation C is resolved in the working tree`, including a `HEAD`-vs-tree rename and a
  per-file `spec-039`-diff-line census that separates the two cycles with no judgement call.
- The F3 census, re-derived a sixth time this pass with its pattern and a `HEAD` control:
  `"SerializerMutation ` occurrences across `rest_framework/{resolvers,sets,inputs}.py` =
  **43 / 14 / 14 = 71**, of which `f"SerializerMutation {` = **40 / 14 / 5 = 59**; **72** at
  `HEAD`. Reproduces the integration pass's settled figure exactly.
- The DRY import ratchet exists and collects **21** node ids — so audit 1a's D6, the cycle's one
  `DROPPED` row, is built.
- The four cohorts' grade arithmetic foots: 61+9+0+0+1 = **71**; 80+9+0+3 = **92**;
  33+8+3+3+0+3 = **50**; 90+10+5+0+0 = **105**; total **318** with exactly one `DROPPED`.

**A reviewer's reading, not a measurement — and the headline answer is in this half:**

- **"Nothing planned was skipped in the code."** This rests on 318 graded contract rows, of which
  exactly one was never built. The **row count** is re-derivable from each artifact's own
  grade-summary table, and audit 3's summary even enumerates its row IDs so its 50 can be counted
  member by member (33 + 8 + 3 + 3 + 0 + 3, each list's length matching its stated count). But
  the **grade on each row** is a reviewer reading a spec sentence against source and citing a
  `path::QualifiedName`. Nothing mechanical graded 318 rows, and nothing can: "does `HEAD` do what
  this sentence says" is not a measurement.
- **The census instrument for the 318 is fragile, and here is the negative control.** A naive
  table-cell census over the four artifacts — count any table row whose cells hold a grade token —
  returns **273**, not 318: it misses audit 3 entirely (which grades in `**A1a —
  BUILT-CONFORMANT.**` prose, not table cells, so it yields 6 rows against its real 50) and it
  double-counts each artifact's grading-vocabulary legend. The 318 is right; the obvious
  instrument for checking it is not. Anyone re-auditing this figure should use each artifact's own
  grade summary, not a glob.
- **`PARTIAL` is a reading with an unusual amount of measurement behind it.** Audit 3's three
  `PARTIAL` rows mean "behavior built, contract not pinned by a distinguishing test" — a claim
  about a *test*, which is checkable, and all three were then closed by Slice 3 (the G2
  `.only(...)` clause and the request-identity tolerance arm) with failability proofs.
- **The four audit cohorts closed at `review-accepted`, never `final-accepted`**, yet the plan
  ticks all four boxes. `docs/builder/ARTIFACT.md` makes `final-accepted` the signal Worker 0 marks
  a box on. These were read-only passes writing one artifact each and no source, and the plan's own
  `## Audit rollup` names them as `review-accepted`, so this was the cycle's deliberate shape
  rather than a lost step — but a maintainer reading only the checklist would not know that no
  Worker 1 final-verification pass ever ran over the four audits. Recorded, not re-opened;
  re-running four read-only audits at gate time would buy nothing.

## Deferred work catalog

The next spec author's reading list. Every artifact of this cycle was walked —
`bld-039-slice-0-rationale_extraction.md`, the four audits, `bld-039-slice-3-code_gaps.md`,
`bld-039-slice-2a-contract_fold_in.md`, `bld-039-slice-2b-label_strip_and_citers.md`,
`bld-039-slice-2c-rev6_retirement.md`, `bld-039-integration.md` — including every
`### Notes for Worker 1 (spec reconciliation)` and `### What looks solid` section (33 such sections
extracted and read). The integration pass's final verification assembled **13** items; this walk
confirms all 13 and adds **one** it missed. **Every bullet names an owner**: an item routed forward
without a named owner dies (`START.md` "Past mistakes").

**Open items — 14.**

1. **F3 — the `SerializerMutation ` message prefix.** **71** occurrences of the source text
   `"SerializerMutation ` across `rest_framework/{resolvers,sets,inputs}.py` (per file 43 / 14 /
   14), of which **59** are `f"SerializerMutation {` (40 / 14 / 5); **72 / 60** at `HEAD`
   (`4c483b6b`); counted as occurrences, not matching lines. Plus a fourth spelling in
   `utils/permissions.py::request_from_info(family_label="SerializerMutation")`. Several are
   `pytest.raises(match=…)` anchors, so a consolidation must byte-preserve the text.
   Source: `bld-039-audit-3-resolvers_and_live.md` `### DRY findings` finding 1 → integration pass
   `### Notes for Worker 1` item 6, census settled at pass 2 and re-derived here.
   No spec line licenses it; the spec describes the messages' contract, not their spelling.
   **Owner: the maintainer**, own card.
2. **The fourth provisional-name derivation**, `rest_framework/resolvers.py::_assert_field_agreement`
   #"'PartialInput' if operation == 'update' else 'Input'" — per-request, a third spelling of the
   partial test, an inline rebuild of `NON_DELETE_OPERATION_INPUT_KIND`, derived from the runtime
   rather than the `Meta` serializer class. The correct fix needs an import edge the spec's
   `### Import manifest` does not grant `resolvers.py`, so it is a **contract change**, not a
   consolidation, and the manifest row must move in the same change as the code.
   Source: `bld-039-integration.md` `### Notes for Worker 1` (Worker 2 pass 1) item 1.
   Same file and same card as item 1. **Owner: the maintainer.**
3. **Escalation A — which population the DRY import ratchet should hold.** The spec's **named
   promotions** (what shipped), the **whole measured shared substrate**, or the
   `### Import manifest` population — and, a second axis, whether the **forms** flavor gets one at
   all, since `forms/converter.py:71` binds the same `FieldConversionBase` and
   `::FormFieldConversion` subclasses it with no ratchet covering it. Three options with what each
   loses are enumerated in `bld-039-slice-3-code_gaps.md` `### Escalation A`. Two concrete rows for
   the answer to weigh, neither added by this cycle: `utils/inputs.py::generated_input_type_name`,
   now load-bearing at **four** `rest_framework/inputs.py` call sites and absent from
   `SHARED_BINDINGS`' 19 rows; and the three new `rest_framework/inputs.py` helpers that `sets.py`
   now imports and that `sets.py`'s manifest column does not name.
   **Carried exactly, not re-decided: this is contract-level and the maintainer's**
   (`docs/builder/BUILD.md` `### Contract-level findings are escalated as maintainer decisions
   before dispatch`). It does not block `final-accepted` — the one row the re-loop added is in
   **every** candidate population. **Owner: the maintainer**, contract-level.
4. **Escalation B — decided, with one open half.** The narrowed tolerated-meta shape at
   `rest_framework/resolvers.py::_assert_field_agreement` **is correct as shipped**: both
   incoherent spellings (attribute absent, attribute `None`) funnel into one `ConfigurationError`,
   and the narrowing rejects more while permitting nothing. Not re-litigated. The open half is the
   `isinstance(meta, _ValidatedMutationMeta)` tightening, a **seam-support** question — whether a
   duck-typed `_mutation_meta` is supported at that seam, given `auth/mutations.py::_AuthMutationMetaSnapshot`
   deliberately is one. Source: `bld-039-slice-3-code_gaps.md` `### Escalation B`. The cheap half
   is already discharged: Slice 2a's `J3` wrote the `operation` + `optional_fields` snapshot
   requirement into `### rev6 #1` as a contract sentence. **Owner: the maintainer.**
5. **Escalation C — resolved in the working tree, unresolved at `HEAD`.** Superseded as a blocker
   by `## Escalation C is resolved in the working tree` above: the full sweep is green and all
   seven node ids pass. It survives in this catalog for one operational reason — the green depends
   on the concurrent cycle's **uncommitted** files, so committing this cycle's work without theirs
   restores the seven red rows. Both historical scope figures (**7** in the full parallel sweep,
   **12** over the four modules in isolation) are recorded with their scopes and were deliberately
   never reconciled; they are a selection effect, not a disagreement. **Owner: the maintainer**,
   at commit sequencing.
6. **Instrument hazard: bare `/tmp` in three recipes across two standing docs.**
   `docs/builder/BUILD.md:528-531,536` (floor venv), `:228,231,232` (failability proof), and
   `START.md:96-99` (a second copy of the floor recipe). `START.md:42` forbids it, and repairing
   only `BUILD.md` leaves `START.md`'s copy prescribing it. `scripts/prove_failability.py:86` is a
   docstring-only fourth site whose code already honors `TMPDIR`. This pass supplies the
   confirming datum: the `dsf-floor` path two recorded runs name has lost its `pyvenv.cfg` while
   `dsf-floor-pass2` is intact, so the decay is real and a floor record naming only a scratch path
   is not auditable later. Source: `bld-039-integration.md` `### Instrument hazards` and
   `### Notes for Worker 1` (pass 2) item 3. **Owner: the maintainer**; the corpus ratchet applies.
7. **Instrument hazard: no recipe asks a floor run to prove its directory is a venv.** Measured
   **0** hits for `pyvenv.cfg` / `sys.prefix` across `BUILD.md`, `ARTIFACT.md`, and all four
   `worker-*.md`. Related: `uv venv … | tail -3 && …` reports the **pipe's** exit status
   (`false | tail -3` exits 0 and its `&&` successor runs — controlled in the integration pass, and
   this pass hit the same shell limitation on `${PIPESTATUS[0]}`). No recorded floor claim in this
   cycle is falsified by either. Source: `bld-039-integration.md` `### Instrument hazards`.
   **Owner: the maintainer**; the corpus ratchet applies.
8. **The owner-name asymmetry in the two `Meta.nested_fields` rejections.** The same
   `SerializerMutation <name>` slot renders the **mutation** class name from
   `rest_framework/sets.py` and the **serializer** class name from `rest_framework/inputs.py`,
   depending on which depth of the opt-in tree rejected. Pre-existing; preserved byte-for-byte by
   the consolidation because changing it inside a refactor would be a behavior change wearing a
   refactor's diff. Source: `bld-039-integration.md` `### Notes for Worker 1` (Worker 2 pass 1)
   item 4. **Owner: the maintainer**, worth a decision.
9. **`BACKLOG.md:31`** still reads `` (`mutations/inputs.py::FieldError`, spec-036 Decision 7 +
   spec-039 rev6 #4/#13) `` — the last `rev6`-vocabulary citer of `spec-039` in the tree, and a
   live stranded ordinal now that Slice 2c retired the numbering. Repair recorded by Slice 2c, one
   substitution: `spec-039 rev6 #4/#13` → *`spec-039`'s error-envelope `codes` / `path`
   improvements*. `BACKLOG.md` is outside the maintainer-set fence (spec files and `.py` files
   only). Source: `bld-039-slice-2c-rev6_retirement.md` `### Notes for Worker 1` item 1.
   **Owner: the maintainer.**
10. **`spec-036`'s severity-ordinal labels: 115 own-voice occurrences over 12 tokens** (`H1`-`H5`,
    `M1`-`M7`) — not the 146 first published, because 31 of the 147 both-bounded population are
    `G2` / `G2-handoff`, `spec-035`'s goal vocabulary that every strip deliberately kept as
    foreign-spec. This falsifies the build plan's own `## Known hazard` premise that "030, 036,
    037, 038 all carry zero"; `spec-039` was not the last spec holding the vocabulary. Whether
    `spec-036` owes the same strip is a scope question, not a custodial one.
    Source: `bld-039-slice-2b-label_strip_and_citers.md` `### Notes for Worker 1` item 2, figure
    corrected in `bld-039-integration.md` `### Notes for Worker 1` item 8. **Owner: the maintainer.**
11. **`KANBAN.md:375`'s `spec-039` inventory is discharged and the board does not know.** All 19
    stranded-ordinal sites across 10 package modules — measured by the `spec-038` cycle — are gone,
    and the same item's claim that `spec-039` "has no rationale companion" was falsified by
    Slice 0, which wrote it. Kanban-DB writes are outside the fence.
    Source: `bld-039-slice-2b-label_strip_and_citers.md` `### Notes for Worker 1` item 1.
    **Owner: the maintainer.**
12. **Nine `TODO-ALPHA-040-0.0.13` card ids in this spec** name a card that is `DONE-040-0.0.13`.
    Already an owned, measured board population (`KANBAN.md:618`) whose ruling is that the class
    splits three ways with only one third mechanical; not pre-empted here.
    Source: `bld-039-integration.md` `### Notes for Worker 1` item 11. **Owner: that card.**
13. **`tests/rest_framework/test_dry_import_ratchet.py:3-8`'s ragged docstring wrap** — cosmetic,
    no gate sees it, Worker 1 may not edit tests, and no consolidation pass remains to fold it
    into. Source: `bld-039-slice-3-code_gaps.md` `### Notes for Worker 1` (Worker 3 pass 2) item 3.
    **Owner: the maintainer**, or the next pass that opens that file.
14. **NEW — the inline-schema idiom in `tests/rest_framework/test_resolvers.py` is a consolidation
    candidate wanting its own card.** Re-measured this pass with the instrument stated: **19**
    `class CategoryT` / `class ItemT` declarations (the source note says "10 inline `CategoryT` /
    `ItemT` declarations", counting pairs), **12** `DjangoSchema(` calls and **14**
    `finalize_django_types()` calls — the latter two matching the source note exactly. Slice 3
    correctly followed the idiom rather than fighting it. Resolution paths, both legitimate: leave
    as-is (a test file where explicit local declaration aids readability), or extract a
    parametrizable schema builder on a dedicated cleanup card. Explicitly "not held" by the pass
    that raised it. Source: `bld-039-slice-3-code_gaps.md` `## Review (Worker 3)`
    `### Notes for Worker 1` item 3 — **the one item the integration pass's 13 did not carry.**
    **Owner: the maintainer**, own card.

**Recorded closed, not deferred — carried so no later pass re-derives them.**

- **The `cached_build_input` existence challenge: answered KEEP.**
  `mutations/sets.py::cached_build_input` has 1 executable caller (`forms/sets.py`) but **6
  in-code citations in four other modules**, each defining its own behavior relative to it.
  Inlining strands the citers and dissolves the named home of an ordering invariant two flavors
  test. Source: raised at `bld-039-audit-2-sets_and_bind.md` `### Notes for Worker 1` item 8 under
  `worker-3.md` `### The existence challenge`; answered in `bld-039-integration.md`
  `### Spec reconciliation` without escalating. **Carried exactly, not re-decided. No owner
  needed.**
- **`rest_framework/inputs.py:1617`'s `except ConfigurationError: return None` is a deliberate,
  deny-shaped swallow** specified by its own docstring — not a fail-open. Three independent
  readings agree. This is why a bare `grep -c 'except ConfigurationError:'` returns 3 where the
  `/ raise` predicate returns 2. Recorded so it is not re-derived a fourth time.
- **Two items the audits framed as escalations were the custodian's and were decided**, not
  routed: the import-manifest granularity choice and the public-surface enumeration ("one net-new
  public symbol" is seven: `SerializerMutation`, `register_serializer_field_converter`,
  `SerializerFieldConversion`, `describe_serializer_input`, `NestedSerializerConfig`,
  `SerializerHookContext`, `UploadMetadata`). Both turn on how to state an **existing** contract
  accurately rather than on which contract the package should offer. Source:
  `bld-039-slice-2a-contract_fold_in.md` `### Notes for Worker 1`, closing paragraph.
- **Audit 4's test-placement observation is discharged, not deferred.** It noted the spec's
  `## Test plan` named `test_products_api.py` as the live tier while the whole rev6 live surface and
  both golden-SDL rows live in `test_library_api.py`, and left the edit to Worker 1's discretion.
  Measured this pass: the spec now states the split at `docs/SPECS/spec-039-serializer_mutations-0_0_13.md:2998`
  ("… sit in `test_query/test_library_api.py`. Same tier"), inside `## Test plan`. No action.
- **Prior-artifact records that are now inaccurate are deliberately left alone.** Slice 2a's
  `#### E` and `#### D` change tables list two edits that measurement shows never landed; the
  integration pass's `## Divergence inventory` D1 / D4 is the correction of record. Per-cycle
  artifacts record what a pass believed when it ran and are never edited after the fact
  (`START.md` "Per-cycle scratch closes w/ cycle"; `docs/builder/ARTIFACT.md`
  `## Re-pass sections`). The same applies to every superseded figure this cycle corrected in a
  later section rather than in place.

## Spec changes made (Worker 1 only)

**None.** The gate obliges no spec edit and made none. Per-spawn status-line re-verification
(`docs/builder/worker-1.md` `## Spec status-line re-verification`) was performed: the spec is
archived under `docs/SPECS/` and carries no `Status:` line, opening "Shipped in `0.0.13` (card
`DONE-039-0.0.13`)", which is accurate at `HEAD` and which nothing in this pass falsifies. Its
head opener's frozen-vs-additive envelope divergence — the one status-adjacent defect Slice 2c
routed forward — was discharged by the integration pass across all seven sites.

The only files this pass writes are this artifact and
`docs/builder/worker-memory/039-worker-1.md`. No source file, no test file, and no spec byte moved.

## Final status

`final-accepted`.

Every command in `docs/builder/BUILD.md` `## Final test-run gate` passes: the full sweep at
`7651 passed, 40 skipped`, both Django consistency checks, all three read-only lint/format/diff
checks (plus a separately-measured, separately-controlled whitespace check on the one untracked
file the gate's own command cannot see), and floor verification confirmed as recorded and
independently re-run to `194` / `498` at Django 5.2.16 / Python 3.10.19 / strawberry-graphql
0.316.0. The three supplementary spec gates hold at `OK: 38 terms` and `OK: 965` with
`check_trailing_commas --check` silent.

The attribution verdict is vacuous because there is nothing to attribute: zero failures, zero
tracebacks. Escalation C, the red `HEAD` that was expected to be this gate's central problem, is
resolved in the working tree by the concurrent `spec-050` cycle's own continued work — proved four
independent ways, including a `HEAD`-vs-tree test rename and the `unevaluated`→`evaluated` rename
in the MIXED `utils/querysets.py` whose two authorships separate mechanically. This cycle neither
caused the redness nor cured it, and it edited none of the four modules. The one operational
caveat is recorded above and carried as catalog item 5: the green depends on the concurrent
cycle's uncommitted files, so `HEAD` itself is unproven and commit sequencing matters.

The deferred work catalog carries **14 open items**, each with a named owner — 8 to the maintainer
directly, 2 more to the maintainer as corpus-ratchet hazards, 1 to commit-time (the
`constants.py` sync), 1 to an already-owned board card, 1 to the maintainer-or-next-pass — plus
five recorded-closed items so the next cycle does not re-derive them. Escalation A is carried
exactly as contract-level and the maintainer's, Escalation B as decided with its `isinstance`
half still routed, and the `cached_build_input` challenge as answered **keep**.

The build cycle is closed pending Worker 0's final checkbox and the maintainer's commit, which
must include the `constants.py` regeneration as its own sync commit after `git add`.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

[spec-039]: ../SPECS/spec-039-serializer_mutations-0_0_13.md
[spec-039-rationale]: ../SPECS/appx/spec-039-serializer_mutations-0_0_13-rationale.md

<!-- docs/builder/ -->

[build-039]: build-039-serializer_mutations-0_0_13.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->

## Homing record (2026-09-10, after the catalog above was written)

The catalog's 14 open items were routed to owning cards, in the board DB, and
`KANBAN.md` / `KANBAN.html` were re-rendered. This section records where each went; the
catalog above is left as written, per `docs/builder/ARTIFACT.md` `## Re-pass sections`.

| Catalog item | Destination | Form |
|---|---|---|
| 1 + 2 (`SerializerMutation ` prefix; 4th provisional-name derivation) | `TODO-ALPHA-053-0.0.15` | new `scope` bullet, order 58 |
| 3 (Escalation A: ratchet population; forms flavor) | `TODO-ALPHA-053-0.0.15` | new `scope` bullet, order 59 |
| 4 (Escalation B open half: `isinstance` tightening) | `TODO-ALPHA-053-0.0.15` | new `scope` bullet, order 60 |
| 8 (owner-name asymmetry in the two `Meta.nested_fields` rejections) | `TODO-ALPHA-053-0.0.15` | new `scope` bullet, order 61 |
| 13 + 14 (ragged docstring wrap; inline-schema idiom) | `TODO-ALPHA-053-0.0.15` | new `scope` bullet, order 62 |
| 6 + 7 (bare `/tmp` in three recipes; no venv proof, pipe exit status) | `TODO-ALPHA-056-0.0.17` | new `scope` bullet, order 89 |
| 9 (`BACKLOG.md`'s `rev6 #4/#13` stranded ordinal) | `TODO-ALPHA-056-0.0.17` | new `scope` bullet, order 90 |
| 10 (`spec-036`'s 115 own-voice labels) | `TODO-ALPHA-056-0.0.17` | already owned - the 184-tag / 34-grammar ruling; the 115 are `AR-M#` x60 + `AR-H#` x54 + one bare `M6`, a subset of it |
| 11 (`KANBAN.md`'s `spec-039` stranded-ordinal inventory) | `TODO-ALPHA-053-0.0.15` | correction appended to the owning bullet |
| 12 (stale `TODO-ALPHA-040` ids in the spec) | discharged here | see below |
| 5 (Escalation C) | not a card | commit sequencing only |

**Item 12 was taken, not routed.** `TODO-ALPHA-056-0.0.17`'s ruling requires per-site
classification before editing, so the 12 sites in this spec were classified individually:
10 graded class (c), plain downstream pointers, flipped to `DONE-040-0.0.13` (x9) and
`DONE-043-0.0.14` (x1); 1 is the Slice 4 card-wrap instruction, a lifecycle-transition
sentence where neither prefix is true, rewritten to name the card by bare number and state
the settled `DONE-039-0.0.13` outcome; 1 is a verbatim quotation of `docs/TREE.md` inside
`## Current state` (whose opener is #"A true description of the repo as this spec is
authored") and is left, class (b) - `docs/TREE.md` carries 0 occurrences of the quoted
string today, so a flip would manufacture a quotation that never existed. The companion's
one `TODO-ALPHA-039-0.0.13` sits in a `- **Revision 1**` log bullet and is left as the
revision-log decided-non-edit that card's own `spec-034` clause establishes as precedent.

**Two census corrections this pass owes, both found by a second instrument.**

- **The `"SerializerMutation ` population is 73, not 71.** The catalog's census globbed
  `rest_framework/{resolvers,sets,inputs}.py` only and missed two members:
  `rest_framework/__init__.py` (the djangorestframework-absent install hint) and
  `utils/inputs.py` (a docstring naming the label as a `noun` parameter value). The
  f-string subset is unchanged at 59. Same too-narrow-population shape as the cycle's
  other six census errors.
- **A left-anchored `(^|[^A-Za-z0-9_-])TOKEN` alternation returns 0 under `ugrep` on a
  live population.** Pointed at `P2-3` / `P1-B` it reported 0 where a plain `grep -rn`
  finds 4. Every figure published here was re-derived in Python with lookarounds. This is
  a seventh blind spot on top of the six the cycle already graded, and it is the most
  dangerous shape of the set because it reads as a finished sweep.

Two board bullets `TODO-ALPHA-056-0.0.17` carries were also corrected against measurement:
the `tests/` / `examples/` stranded-ordinal population is 12, not 13 (`spec-039`'s `SR-3`
retired, together with an unlisted package-side sibling in
`rest_framework/serializer_converter.py` that was `TODO-ALPHA-053-0.0.15`'s), and the
rationale-companion census now reads 44 companions against 56 specs, 12 missing - a
different SHAPE from the recorded contiguous island, since `032` through `039` all carry
one today.
