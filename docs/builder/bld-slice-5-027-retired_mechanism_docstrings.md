# Build: Post-final residual cohort — retired-mechanism test docstrings (027)

Spec reference: `docs/SPECS/spec-027-filters-0_0_8.md` `### Decision 9 — Input-class namespace vs \`TypeRegistry\` and lifecycle` (spec line 659). Cited by heading, not by `#"substring"`: this cycle has twice shipped a citation whose target a later move deleted, and Decision 9's body is the surface Slices 1 and 3 rewrote most heavily. The spec was **WRONG** on this mechanism — Decision 9's lifecycle bullet pinned a `delattr` walk the code deliberately does not perform — and Worker 1 corrected it across three surfaces; see `## Final verification (Worker 1)` `### Spec changes made (Worker 1 only)`. No builder pass edited it.
Status: final-accepted

## Plan (Worker 1)

### Planning lives in `build-027-filters-0_0_8.md`

This cohort has no Worker 1 planning pass of its own. The contract is the build plan's dispatch brief:

- [`build-027-filters-0_0_8.md`][plan] `### Post-final residual cohort — retired-mechanism test docstrings (added 2026-08-20)` — the population, the declared ownership partition, the pre-dispatch mechanism measurement, and the cross-cohort seam routing.
- [`build-027-filters-0_0_8.md`][plan] `### Baseline-dirty out-of-scope files (never edit, never revert)` and `### Scope fence set by the maintainer`.
- [`bld-slice-4-027-broken_substring_citations.md`][slice4] `#### Comment-and-docstring-only proof (executable-token identity)` — the format precedent for a prose-only pass in this cycle, reproduced below.

**Ownership partition (single cohort, declared):** `tests/test_registry.py` and `tests/filters/test_inputs.py`, plus this artifact. No other cohort ran concurrently. `tests/filters/test_inputs.py` already carried this cycle's Slice 2 edits, so `HEAD` is not its pre-pass baseline; `tests/test_registry.py` was clean at `HEAD` `5c6fdd71`.

Section placement follows [`ARTIFACT.md`][artifact]: `### Dispatched findings checklist` sits in `## Plan (Worker 1)`, where Worker 1 audits the ticks at final verification.

### DRY analysis

**Not applicable, and the reason is not "small diff".** [`BUILD.md`][build] `## DRY implementation rules` gates *logic*: whether an existing helper already owns a responsibility, whether a literal should be named once, whether a branch duplicates another slice's shape. This diff contains no executable statement — proven mechanically under `#### Comment-and-docstring-only proof`, not asserted — so there is no helper, constant, branch, or fixture for a DRY question to attach to.

One DRY-shaped question does exist and is answered deliberately in the negative: the two corrected docstrings state **different** contracts and must not be unified into one shared phrasing. Site 1's entry point performs no import at all; site 2's reaches two submodules through a guarded lookup. A single sentence covering both would be false at one of them — which is precisely the defect this pass repairs. See `### Notes for Worker 1 (spec reconciliation)` item 1.

### Dispatched findings checklist

Built from the finding table in [`build-027-filters-0_0_8.md`][plan] `### Post-final residual cohort`. Box 2's text is quoted as dispatched; the measurement that contradicts half of it is recorded under `### Notes for Worker 1 (spec reconciliation)` item 1 rather than by editing the box.

- [x] `tests/test_registry.py::test_clear_tolerates_unimportable_filter_submodules` (docstring) | "Both ``except ImportError`` guards in ``clear()``"; "The filter-namespace co-clear uses cycle-safe local imports"; "``clear()`` skips that block" | 0 guards in `registry.py`; `clear()` replays resolved callbacks; no block to skip
- [x] the inline comment inside the same test body — "``None`` in ``sys.modules`` makes ``from <name> import ...`` raise ImportError, exercising both guards" — carrying the same false claim
- [x] `tests/filters/test_inputs.py::test_clear_filter_input_namespace_tolerates_unimportable_submodules` (docstring + inline comment) | "Both ImportError guards are best-effort"; "makes ``from ... import ...`` raise ImportError, exercising both ``except ImportError`` guards" | `clear_filter_input_namespace` imports nothing at call time; the named `from ... import ...` does not execute, so the stated premise cannot fire — **the second half of this measurement does not hold; see `### Notes for Worker 1` item 1**
- [x] the `# ---` section banner above the site-2 test reading `clear_filter_input_namespace - cycle-safe import guards` — **left unchanged, deliberately**: it is accurate at `HEAD`. Reasoning in `### Implementation notes`

---

## Build report (Worker 2)

### Files touched

Grounded in `git status --porcelain` taken before and after the pass, and in a `diff` of each file against a pre-pass copy held outside the repo. Four hunks total, all comment / docstring text.

- `tests/test_registry.py` — two hunks in `test_clear_tolerates_unimportable_filter_submodules`: the docstring, and the inline comment above the two `sys.modules[...] = None` assignments. Clean at `HEAD` before this pass; this cohort is the only writer.
- `tests/filters/test_inputs.py` — two hunks in `test_clear_filter_input_namespace_tolerates_unimportable_submodules`: the one-line docstring (now four lines) and the inline comment above the two `sys.modules[...] = None` assignments. Already carried this cycle's Slice 2 comment-only edits.
- `docs/builder/bld-slice-5-027-retired_mechanism_docstrings.md` — this artifact.

No test was renamed, no assertion, fixture, import, or `sys.modules` manipulation changed, and no production file was touched — transiently or otherwise.

**Churn classification.** `git status --porcelain` before and after this pass differ by exactly two paths:

| Path | Classification |
|---|---|
| `tests/test_registry.py` | **(a) mine** — newly opened by this cohort |
| `tests/filters/test_inputs.py` | **(a) mine**, on top of **(b)** this cycle's Slice 2 |
| `docs/builder/build-028-orders-0_0_8.md` (new `??`) | **(c) concurrent** — a `spec-028` session's build plan, appeared mid-pass; not touched, not reverted |
| `docs/builder/bld-slice-5-027-retired_mechanism_docstrings.md` (new `??`) | **(a) mine** — this artifact |
| the other 20 ` M` paths and 8 `??` paths | **(b)** this cycle's Slices 1-4, their artifacts, and the spec + rationale |

Totals re-derived rather than asserted: `git status --porcelain \| grep -c '^ M'` = **22**, `grep -c '^??'` = **10**. Of the 22 modified, 2 are mine; of the 10 untracked, 1 is mine and 1 is the concurrent `build-028` plan.

The two baseline-dirty paths [`build-027-filters-0_0_8.md`][plan] lists (`examples/fakeshop/apps/scalars/models.py`, `examples/fakeshop/test_query/test_scalars_api.py`) are no longer dirty — a concurrent session landed them before this pass began. Recorded rather than acted on; `HEAD` is unchanged at `5c6fdd71`.

### Hunks applied, full before/after text

#### Hunk 1 — `tests/test_registry.py::test_clear_tolerates_unimportable_filter_submodules`, docstring

Before:

```python
    """Both ``except ImportError`` guards in ``clear()`` are best-effort.

    The filter-namespace co-clear uses cycle-safe local imports. If either
    submodule cannot be imported (forced here by poisoning ``sys.modules``),
    ``clear()`` skips that block and still clears the registry's own state
    rather than raising.
    """
```

After:

```python
    """``clear()`` imports nothing, so a broken ``sys.modules`` cannot break it.

    Every subsystem binds its own teardown callback at ITS import time via
    ``register_subsystem_clear``, and ``clear()`` replays the already-resolved
    callables. No import runs on the clear path, so poisoning the filter
    modules in ``sys.modules`` (done here) cannot make ``clear()`` raise: the
    registry's own state is dropped either way (spec-027 Decision 9).
    """
```

#### Hunk 2 — same test, inline comment

Before:

```python
        # ``None`` in ``sys.modules`` makes ``from <name> import ...`` raise
        # ImportError, exercising both guards.
```

After:

```python
        # ``None`` in ``sys.modules`` is the shape that makes an import of
        # either module raise ImportError. ``clear()`` itself runs no import,
        # so the poisoning can only reach a replayed callback's own
        # best-effort lookup, which skips rather than propagates.
```

"can only reach a replayed callback's own best-effort lookup" is deliberately weaker than "is never consulted at all", and the weakening is measured, not hedging. Site 1 poisons the **package** `django_strawberry_framework.filters` as well as `filters.inputs`. The filter callback `clear_filter_input_namespace` still runs (it is an already-resolved callable), and it reaches `filters.factories` / `filters.sets` through `utils/inputs.py::_safe_import`. Whether that lookup even notices the poison is **process-state-dependent**: `importlib._bootstrap._find_and_load` returns a cached submodule without consulting its parent, so if those two modules are already in `sys.modules` when this row runs, the poison is invisible; if they are not, the poisoned parent makes the lookup raise internally and return `None`. Both branches satisfy the contract the docstring states (`clear()` does not raise), and pytest ordering decides which one a given run takes. A comment asserting "never consulted" would be false in one of the two, order-dependently — the class [`BUILD.md`][build] `### Example-project schema changes must sync every schema-module list` records as invisible below a full parallel run.

#### Hunk 3 — `tests/filters/test_inputs.py::test_clear_filter_input_namespace_tolerates_unimportable_submodules`, docstring

Before:

```python
    """Both ImportError guards are best-effort: a broken import is skipped."""
```

After:

```python
    """Both submodule lookups on the clear path are best-effort: skip, never raise.

    The heavy clear reaches ``FilterArgumentsFactory`` and ``FilterSet``
    through ``utils/inputs.py::_safe_import``, so an unimportable module
    yields ``None`` and only its dependent reset is skipped; the reachable
    ledger reset still completes (spec-027 Decision 9).
    """
```

#### Hunk 4 — same test, inline comment

Before:

```python
        # Setting the module entry to ``None`` makes ``from ... import ...``
        # raise ImportError, exercising both ``except ImportError`` guards.
```

After:

```python
        # Setting the module entry to ``None`` makes the best-effort lookup of
        # each module raise ImportError internally, exercising both skips.
```

### Tests added or updated

None. This pass adds no executable statement and no contract; there is nothing new for a test to pin. Both target tests still pass unchanged (see `### Validation run`), and both were shown to be **live** regression guards rather than merely green (see `#### Guard-liveness demonstration`).

### Validation run

Every command run from the repository root. No `--cov*` flag anywhere.

| Check | Command | Result |
|---|---|---|
| Format (scoped, never `.`) | `uv run ruff format tests/test_registry.py tests/filters/test_inputs.py` | `2 files left unchanged`, exit 0 |
| Lint (scoped) | `uv run ruff check --fix tests/test_registry.py tests/filters/test_inputs.py` | `All checks passed!`, exit 0 |
| Source layout / ASCII-only | `uv run python scripts/check_trailing_commas.py --check <the same two files>` | exit 0 |
| Citation gate | `uv run python scripts/check_citations.py` | `OK: 743 citations resolve (666 in 422 .py files, 77 in KANBAN.md).` exit 0 — see the delta analysis below |
| Pre-commit (all five hooks) | `uvx pre-commit run --files <the same two files>` | all five **Passed**: kanban tracked path constants, source layout, ruff format, ruff check, citations resolve |
| Churn classification | `git status --porcelain` before and after | see `### Files touched`; nothing unexpected, nothing reverted |
| Focused tests | `uv run pytest tests/test_registry.py tests/filters tests/orders tests/types tests/utils/test_inputs.py --no-cov -q` | **1316 passed in 14.82s** |
| Guard liveness (scratchpad, no repo file mutated) | `uv run pytest <scratchpad>/test_guard_liveness.py --no-cov -q -p no:cacheprovider` | **2 passed in 0.31s** |

`pre-commit` is not on `PATH` in this environment (`uv run pre-commit` fails to spawn); `.pre-commit-config.yaml`'s own header names `uvx pre-commit` as the invocation, which is what ran. All five hooks are `language: system` shelling out to `uv run`, so the hook bodies are the repo's pinned tools either way.

**Citation-count delta, re-derived rather than compared to a number in a document.** [`bld-slice-4-027-broken_substring_citations.md`][slice4] recorded `740 (665 in .py, 75 in KANBAN.md)`. This pass reads `743 (666, 77)`. The `.py` half rose by exactly **1**, which is this pass's one added `path::Symbol` citation, `utils/inputs.py::_safe_import` in hunk 3. Measured per file against the pre-pass copies with `grep -oE '[A-Za-z0-9_./]*\.py::[A-Za-z_][A-Za-z0-9_.]*'`:

| File | `path::Symbol` refs before | after |
|---|---|---|
| `tests/test_registry.py` | 2 | 2 |
| `tests/filters/test_inputs.py` | 0 | **1** |

The KANBAN half's `+2` is **not this pass**: `KANBAN.md` is not in this cohort's writable set, is not dirty in `git status`, and is generated from `examples/fakeshop/db.sqlite3` by a concurrent session ([`build-027-filters-0_0_8.md`][plan] lists both as concurrent-writable). The gate's count did not drop, which is the property the dispatch required.

**Scope choice for the focused run**, derived from the importing surface rather than picked:

```shell
grep -rln 'clear_filter_input_namespace\|register_subsystem_clear\|iter_subsystem_clears\|_safe_import\|clear_generated_input_namespace' tests/ examples/
```

returns ten files: `tests/test_registry.py`, `tests/filters/{test_finalizer,test_inputs}.py`, `tests/orders/{test_composition,test_inputs}.py`, `tests/utils/test_inputs.py`, `tests/auth/{test_mutations,test_queries}.py`, `tests/mutations/test_sets.py`, `tests/rest_framework/test_sets.py`. The run covers both edited files, both package mirrors (`tests/filters/`, `tests/types/`), the sibling set family that shares the same `make_set_input_namespace` quartet and holds the order twin of site 2 (`tests/orders/`), the shared substrate that owns `_safe_import` and `clear_generated_input_namespace` (`tests/utils/test_inputs.py`), and the registry lifecycle that drives every subsystem clear (`tests/test_registry.py`). `tests/auth/`, `tests/mutations/`, `tests/rest_framework/` reference the seam only as consumers of `registry.clear()` in fixtures; they are unreachable from a diff with zero executable tokens, and the final gate's full sweep is their backstop.

#### Comment-and-docstring-only proof (executable-token identity)

Claimed mechanically, per [`BUILD.md`][build] `## Claims are proven mechanically, never accepted on prose`. No `git checkout` / `git stash` / `git restore` / `git worktree` was used; concurrent sessions are writing this tree. Read-only baselines came from `git show HEAD:<path> > <scratchpad>` plus a working-tree copy taken **before** the first edit. Script and copies live outside the repo, in this session's scratchpad.

The instrument tokenizes with `tokenize`, drops `COMMENT` / `NL` / `ENCODING` tokens and every statement-position `STRING` (i.e. docstrings), and compares the remaining `(type, string)` sequence.

**Two baselines for `test_inputs.py`, because `HEAD` is not "before this pass".** It already carried this cycle's Slice 2 edits. Slice 2 was also comment-only, so the `HEAD` comparison is expected to hold too — and it does, which independently re-confirms Slice 2's own claim.

| File | vs `git show HEAD:<path>` | vs the pre-pass working-tree copy | Token count |
|---|---|---|---|
| `tests/test_registry.py` | IDENTICAL (0 divergences) | IDENTICAL (0 divergences) | 7737 |
| `tests/filters/test_inputs.py` | IDENTICAL (0 divergences) | IDENTICAL (0 divergences) | 7028 |

**The instrument was itself proven, in all four directions, before its verdict was believed.** A tokenizer comparison that reports IDENTICAL is worthless if it would report IDENTICAL for a real code change too, and the first attempt at this check was exactly that failure: a `sed '^import sys$'` sanity mutation silently failed to land (every `import sys` in these files is indented, inside a test body), so the instrument returned `IDENTICAL` on a file it had never actually been challenged with. The landing of each mutation is now asserted before its verdict is read:

| Sanity case | Mutation | Expected | Measured |
|---|---|---|---|
| S1 | `assert fresh_registry.get(Category) is None` -> `... is not None` (1 of 7 occurrences) | DIVERGENT | **DIVERGENT**, 7021 divergences, `(1, 'None') != (1, 'not')` at index 627, exit 1 |
| S4 | one extra `pass` statement inserted into the test body | DIVERGENT | **DIVERGENT**, token count 7737 -> 7739, exit 1 |
| S2 | docstring summary line replaced wholesale | IDENTICAL | **IDENTICAL**, exit 0 |
| S3 | inline comment replaced wholesale | IDENTICAL | **IDENTICAL**, exit 0 |

S1 and S4 prove the instrument can fail; S2 and S3 prove it ignores exactly the two token classes this pass edits. The lesson generalizes past this cohort and is the reason the table is here rather than in a footnote: **`sed` reports success when its pattern matched nothing**, so a sanity mutation driven by `sed` and unverified is indistinguishable from a vacuous proof — the same "the anchor check is first because nothing else in the loop can tell that its own reference is already mutated" hazard [`BUILD.md`][build] `## Failability proofs: prove the test can fail` records for the mutation loop itself.

#### Guard-liveness demonstration

The corrected docstrings assert that each test is a **live** regression guard. That is a claim, so it was measured rather than argued — but without mutating any repository file: `registry.py` and `utils/inputs.py` are outside this cohort's declared partition, concurrent sessions are writing this tree, and [`BUILD.md`][build] `### What needs a proof, and what does not` exempts a doc-only diff from the mutation loop. A scratchpad pytest file monkeypatches the in-process seam each corrected sentence names and lets pytest restore it, so no on-disk mutation exists at any point and none can survive the run.

| Case | The corrected claim | Demonstration | Result |
|---|---|---|---|
| A (site 1) | `clear()` imports nothing, so poisoned `sys.modules` cannot make it raise | `TypeRegistry().clear()` under the row's own poison, then the same poison shown to make a call-time `importlib.import_module` of `filters.inputs` raise | passes, then `pytest.raises(ImportError)` holds |
| B (site 2) | the clear path's two submodule lookups are best-effort | `clear_filter_input_namespace()` under the row's own poison, then `utils.inputs.import_attr_if_importable` monkeypatched to an unguarded `getattr(import_module(...), ...)` and the same call re-run | passes, then `pytest.raises(ImportError)` holds |

Both rows pass. Case A shows reintroducing a call-time import inside `clear()` would break site 1; case B shows removing the guard from the lookup would break site 2. Neither test is vacuous, and neither should be deleted as "pinning nothing".

### Failability proofs

None; this pass introduced no new boundary.

Discharged mechanically rather than on prose: the executable-token identity table above shows the diff contains no statement, branch, guard, comparison, or raise for the mandatory floor to select. The liveness demonstration above is a separate, voluntary check that the two **pre-existing** boundaries these tests cover are still pinned — it is not a failability proof and claims no such status.

### Hot-path budget

Not applicable; plan declares no hot path. Confirmed against the diff: zero executable tokens changed, so no path gained cost.

### Floor verification

Not applicable; plan declares floor-verification scope none. Confirmed against the diff for the same reason.

### Implementation notes

- **The section banner was left unchanged, and that is a decision.** The dispatch put `# clear_filter_input_namespace - cycle-safe import guards` in scope. It is **accurate at `HEAD`**: `utils/inputs.py::_safe_import`'s own docstring opens "Cycle-safe import of ``module_path.attr`` returning ``None`` on ImportError", and there are two guarded lookups on the clear path. Editing it would have added a third hunk that corrects nothing and reflowed a line adjacent to text this pass is otherwise not touching — the mechanism this cycle has twice watched break a `#"substring"` citation.
- **No rename, and the reason is a contract not a cost.** See `### Test-name recommendation`.
- **`spec-027 Decision 9` is cited without a `#"substring"`, at both sites.** Rule 27 permits the substring form, but Decision 9's body is the single most heavily rewritten passage of this cycle (Slices 1 and 3 both moved text out of it), and this cycle has already shipped two citations whose targets a move deleted. `### Decision 9` occurs exactly once in the spec (`grep -c` = 1, spec line 659) and is stable under any reword inside the decision.
- **The citation was verified to state the contract, not merely to resolve.** Decision 9's body reads: "`registry.py` must reach into `filters` by no route at all — not a module-top import, and not a function-local one inside `clear()`" and "only an imported owner can register ... with no `except ImportError: pass` branch to keep covered". That is site 1's corrected docstring, in the spec's own words. For site 2, Decision 9 owns `clear_filter_input_namespace()` as the ledger-reset entry point ("Public `clear_filter_input_namespace()` helper ... `registry.clear()` calls this helper internally").
- **Site 1's docstring summary line is written so the three sibling twins' cross-references survive it.** `test_clear_tolerates_unimportable_order_submodules`'s docstring says "Order twin of ``test_clear_tolerates_unimportable_filter_submodules``" — a reference to the **name**, which this pass does not change. Nothing in the new wording is quoted or relied on by a sibling, so the seam below is a difference in prose only, never a dangling pointer.

### Notes for Worker 1 (spec reconciliation)

1. **The dispatch brief's measurement for site 2 does not hold, and the corrected prose therefore differs from the prose the brief prescribed.** This is the loudest item in this artifact. [`build-027-filters-0_0_8.md`][plan] `### Post-final residual cohort` states, as verified-at-`HEAD` fact: "`filters/inputs.py::clear_filter_input_namespace` is a bare delegate to `_clear_input_namespace` ... **Neither call site imports anything, so poisoning `sys.modules` cannot reach either one.**" The first clause is true; the sentence in bold is **false for site 2**. The full call chain, read rather than inferred:

   `filters/inputs.py::clear_filter_input_namespace` -> `_clear_input_namespace` (the `clear_fn` closure `utils/inputs.py::make_set_input_namespace` returns at module scope) -> `utils/inputs.py::clear_generated_input_namespace` -> **`utils/inputs.py::_safe_import`, twice** -> `utils/imports.py::import_attr_if_importable` -> `importlib.import_module` wrapped in `try / except ImportError: return None`.

   The two `_safe_import` targets are `factory_module="django_strawberry_framework.filters.factories"` and `set_module="django_strawberry_framework.filters.sets"` (`filters/inputs.py` lines 166 and 169) — **exactly the two module names the site-2 test poisons**. So the test's premise fires, one layer down. `utils/imports.py::import_attr_if_importable`'s own docstring says so explicitly: "A ``None`` entry in ``sys.modules`` (the test-isolation shape for simulating an unimportable submodule) raises ``ImportError`` inside ``import_module``, same as the previous inline guards".

   Consequences Worker 1 should weigh:

   - **Site 2 is not a member of the declared population.** The mechanism was **relocated and single-sited** into the shared substrate by the `OrderSet` / DRY-squeeze work (the same cause [`build-027-filters-0_0_8.md`][plan] `D4` records for `FieldSpec` / `build_input_class` / `_input_type_name_for`), not retired. The plan's finding table row for site 2 — "the named `from ... import ...` does not execute, so the stated premise cannot fire" — is wrong in its second half and should be corrected in the plan, per [`BUILD.md`][build] `### Worker 0 verifies every finding against source before dispatching`: "for a finding that does not hold, the evidence that it does not — reported to the maintainer rather than quietly dropped. It still matters: it says the maintainer's model of the code is off somewhere."
   - **Writing the prescribed wording would have installed a NEW false claim.** The brief's `### What the corrected prose must say` directs both docstrings to state "that the entry point performs no call-time import, so a poisoned `sys.modules` cannot make it raise". True at site 1; false at site 2, where the entry point reaches two call-time imports and the test's value is precisely that it tolerates them failing. A prescribed fix is a hypothesis, not an instruction ([`BUILD.md`][build] same section), so site 2's replacement states the mechanism that is actually there.
   - **What site 2's docstring was, graded honestly.** "Both ImportError guards are best-effort: a broken import is skipped" is **substantively true** at `HEAD` and says nothing about where the guards live. The genuinely wrong text was the inline comment's `from ... import ...` spelling (that statement form does not execute on this path; it is `importlib.import_module`) and its "both ``except ImportError`` guards" (there is one `except ImportError` clause, in `utils/imports.py`, reached twice). Site 2 is therefore a **Low**-severity stale-spelling fix, not the retired-mechanism class — [`BUILD.md`][build] `## Severity definitions` Low, "comments or docstrings stale or wrong but not load-bearing". Site 1 is the real member of the class: `registry.py` carries **0** `except ImportError` (measured), `clear()` executes no import, and "skips that block" named a block that does not exist.
   - This did not change an executable token, widen the partition, or touch the spec, so it was implemented and recorded rather than paused as structural drift ([`worker-2.md`][w2] `## Plan-vs-implementation drift`). If Worker 1 reads it as plan-level rather than slice-level, the pause is Worker 1's to declare.

2. **A separate spec divergence found while verifying the Decision 9 citation — NOT repaired, and outside this cohort's fence.** Decision 9's third bullet states that `clear_filter_input_namespace()` "walks `_materialized_names.items()` and `delattr(sys.modules["django_strawberry_framework.filters.inputs"], name)` for each, then resets the ledger to `{}`". At `HEAD` the implementation does the **opposite** and deliberately so: `filters/inputs.py::clear_filter_input_namespace`'s own docstring says "Materialized class objects stay parked in ``filters.inputs.__dict__``", and `utils/inputs.py::clear_generated_input_namespace` states "**Materialized class objects are intentionally left parked** ... Stripping it via ``delattr`` here would break any ``strawberry.lazy(...)`` LazyType held by a consumer module whose autouse-reload fixture did NOT also reload the holder." So the spec pins `delattr`; the code deliberately does not `delattr`; the reason is recorded in the code and is a real contract. This survived Slice 3's reconciliation. Worker 1 owns whether it is a spec edit; this cohort may not edit any spec file and did not.

   - **Where it lives:** `docs/SPECS/spec-027-filters-0_0_8.md` `### Decision 9 — Input-class namespace vs \`TypeRegistry\` and lifecycle`, the bullet beginning "**`registry.clear()` (the model-to-`DjangoType` registry's clear) clears the filter input lifecycle ledger**".
   - **Current wording:** "`clear_filter_input_namespace()` walks `_materialized_names.items()` and `delattr(sys.modules["django_strawberry_framework.filters.inputs"], name)` for each, then resets the ledger to `{}`."
   - **Recommended replacement:** "`clear_filter_input_namespace()` resets the lifecycle ledger and the per-`FilterSet` binding state, and leaves the materialized class objects parked as module globals: the next finalize replaces each in place via `setattr`. Stripping them with `delattr` would break any `strawberry.lazy(...)` LazyType held by a consumer module whose reload fixture did not also reload the holder."

3. **The section banner at site 2 was deliberately not edited** even though the dispatch listed it in scope, because it is accurate at `HEAD`. Reasoning in `### Implementation notes`. Flagged here so Worker 1 does not read it as a silently-skipped checklist item; box 4 records the same.

4. **The plan's cross-cohort seam paragraph names a test that does not exist.** It lists `test_clear_tolerates_unimportable_node_field_ledger` (spec-032) as the fourth `test_registry.py` twin. `grep -n '^def test_.*unimportable' tests/test_registry.py` returns exactly five rows, and the real fourth is `test_clear_tolerates_unimportable_relay_module` (line 1724) — `_node_field_ledger` is what its docstring is *about* (`_node_fields_declared.clear()`), not its name. The routing is unaffected; the name in the plan is not resolvable by grep and should be corrected so the 051 pass can find its population. **The same defect shape as item 1** — a stated finding whose subject is right and whose identifier is wrong; `AGENTS.md` rule 27 exists for exactly this, and a `path::Symbol` spelling in the plan would have failed to resolve and been caught. Its docstring is stale by the same proof as site 1 ("uses a cycle-safe local import ... `clear()` skips that block"), so it is a genuine member of the 051 population — only its name is misrecorded.

### Cross-cohort seam (deliberate, recorded)

This cohort leaves **one of four twins reading differently from the other three, on purpose.** The population and its routing are the plan's ([`build-027-filters-0_0_8.md`][plan] `### Post-final residual cohort`, final paragraph); this section records that the seam was created knowingly and re-derives its membership rather than restating it.

| Test | Subsystem / card | Disposition |
|---|---|---|
| `tests/test_registry.py::test_clear_tolerates_unimportable_filter_submodules` | filters, spec-027 | **repaired here** — spec-027's own surface, inside this cycle's fence |
| `tests/test_registry.py::test_clear_tolerates_unimportable_order_submodules` | orders, spec-028 | untouched; routed to `TODO-ALPHA-051-0.0.15` |
| `tests/test_registry.py::test_clear_tolerates_unimportable_connection_submodule` | connection, spec-030 | untouched; routed to `TODO-ALPHA-051-0.0.15` |
| `tests/test_registry.py::test_clear_tolerates_unimportable_relay_module` | node-field ledger, spec-032 | untouched; routed to `TODO-ALPHA-051-0.0.15`. **The plan names this row `..._node_field_ledger`, which does not exist** — `grep -n '^def test_.*unimportable' tests/test_registry.py` returns exactly five rows and this is the fourth clear-side one. `_node_field_ledger` is the *subject* of its docstring, not its name |
| `tests/orders/test_inputs.py::test_clear_order_input_namespace_tolerates_unimportable_submodules` | orders, spec-028 | untouched; routed to `TODO-ALPHA-051-0.0.15`. **Note for whoever takes 051:** this is site 2's twin, so item 1 above applies to it verbatim — it is a relocated-mechanism spelling fix, not a retired-mechanism one, and the `_safe_import` chain absorbs its poison too |

Why the seam is correct rather than tolerated: the other four are **other cards' surfaces** and the maintainer's `### Scope fence` limits this cycle to spec-027's. Repairing them here would put four cards' prose into a `DONE-027-0.0.8` commit and pre-empt 051, which already collects measured stale test docstrings. The three `test_registry.py` siblings sit in a file this cohort **owns**, which makes the restraint deliberate rather than incidental — physical access is not authorization.

`tests/test_registry.py::test_unregister_tolerates_unimportable_connection_submodule` is **not** in that population, re-verified rather than taken on trust: `registry.py::_clear_if_importable` is defined at line 34 and its single call site at line 331 sits inside `unregister` (the enclosing `def unregister` is at line 284), so that row's poisoned-`sys.modules` premise still fires against a real `except ImportError` on a real import. It was not touched.

### Test-name recommendation

**Do not rename either test. Route the question to `TODO-ALPHA-051-0.0.15` if it is to be reopened at all.** Three reasons, in decreasing order of force:

1. **Neither name is actually misleading.** `..._tolerates_unimportable_...` describes the row's **input condition and its required outcome** — modules that cannot be imported, and a call that must not raise — never the mechanism by which the outcome is achieved. Both hold at `HEAD`: site 1 tolerates the poison by never importing, site 2 by absorbing the ImportError in a guarded lookup. A name that survives a mechanism change is a well-chosen name, and renaming it would couple the name to an implementation detail, re-creating this exact defect class one layer up.
2. **A rename is an executable-token change, and it would destroy this pass's central proof.** A `def` name is a `NAME` token: renaming either test flips both rows of the identity table from IDENTICAL to DIVERGENT, and the "prose-only" claim this artifact rests on could no longer be made mechanically. That is not a reason to avoid a *needed* rename — it is a reason not to bundle an unneeded one into a prose pass.
3. **Site 1's name is a cross-file anchor with at least one live referent.** `test_clear_tolerates_unimportable_order_submodules`'s docstring reads "Order twin of ``test_clear_tolerates_unimportable_filter_submodules``", in a test this cohort may not edit. Renaming site 1 would leave a dangling name inside another card's surface — and rule 27's grep-sweep obligation ("renaming a symbol means grep-sweep `::OldName` in the same change") cannot be discharged when the sweep's hits are out of the writable set. A rename is only correct as part of the 051 pass that owns all five twins at once.

### Notes for Worker 3

- **Read `### Notes for Worker 1` item 1 first.** Half of the dispatch brief's mechanism measurement is wrong, and site 2's applied text deliberately differs from the text the brief prescribed. Reviewing hunks 3 and 4 against the brief rather than against the source will read as unauthorized drift; reviewing them against `filters/inputs.py` lines 158-172 -> `utils/inputs.py::clear_generated_input_namespace` -> `utils/inputs.py::_safe_import` -> `utils/imports.py::import_attr_if_importable` shows why they say what they say.
- **The token-identity instrument lives outside the repo**, at `<scratchpad>/token_identity.py`, with baselines under `<scratchpad>/base/`. It is re-runnable as `uv run python <scratchpad>/token_identity.py <baseline> <candidate> [label]`, exit 0 on IDENTICAL and 1 on DIVERGENT. Its four sanity cases are in the table above; **re-derive at least one DIVERGENT case before trusting a re-run**, for the reason that table records.
- **The guard-liveness file also lives outside the repo**, at `<scratchpad>/test_guard_liveness.py`. It is a review aid, not a candidate for promotion into a test tree: every contract it exercises is already pinned by the two permanent rows, and it reaches into `utils.inputs.import_attr_if_importable` by monkeypatch, which `AGENTS.md` rule 10 permits only when the real path is impossible. Disposition: leave in the scratchpad, delete with the cycle.
- No production file was touched, transiently or otherwise; no mutation existed on disk at any point in this pass.
- `git status --porcelain` gained one path from a concurrent session mid-pass (`docs/builder/build-028-orders-0_0_8.md`). Not touched, not reverted.

---

## Review (Worker 3)

Reviewed against `HEAD` `5c6fdd71` and against the **corrected** dispatch brief
([`build-027-filters-0_0_8.md`][plan] `### Post-final residual cohort`, as it stands on disk), not
against the brief the build report quotes. Every claim below was re-derived; nothing was accepted
from the build report's account of it. Two read-only probes and one token-identity instrument were
written for this pass, all outside the repo, all named `*_027*` in the review scratchpad. No
repository file was mutated at any point in this review, transiently or otherwise.

### High:

None.

### Medium:

#### Site 1's new docstring installs a fresh false claim: "No import runs on the clear path"

`tests/test_registry.py:1622` (hunk 1, third sentence). Measured at `HEAD`: `registry.clear()` runs
**two** `importlib.import_module` calls, both into the filter subsystem. Probe (read-only, spies the
`importlib.import_module` attribute the substrate calls through, then restores it):

```text
registered subsystem clear count: 10
importlib.import_module calls during registry.clear(): 2
    django_strawberry_framework.filters.factories
    django_strawberry_framework.filters.sets
```

Chain, traced rather than inferred: `registry.py::TypeRegistry.clear` #"for clear in
iter_subsystem_clears():" -> `iter_subsystem_clears()` with the default `before_bind=False`, which
returns **every** registered callback -> `filters/inputs.py::clear_filter_input_namespace` (registered
with `owner="filters.input_namespace"`) -> `_clear_input_namespace` ->
`utils/inputs.py::clear_generated_input_namespace` -> `utils/inputs.py::_safe_import` twice ->
`utils/imports.py::import_attr_if_importable` -> `importlib.import_module`.

So an import demonstrably *does* run on the clear path. What is true is the narrower statement the
same test's **inline comment already makes**, ten lines below: "``clear()`` itself runs no import, so
the poisoning can only reach a replayed callback's own best-effort lookup". The docstring and the
comment now contradict each other inside one function body, and the docstring is the wrong half.

Why this is Medium rather than Low. For an ordinary slice a wrong docstring sentence is Low
("stale or wrong but not load-bearing"). Here the unit's entire deliverable **is** prose truth: the
dispatched finding is that this docstring described a mechanism the package does not have, and the
repair re-describes a mechanism the package does not have, one scope level up. It is also
consequential in the same direction as the original defect — a reader who believes "no import runs on
the clear path" has no reason to keep the `except ImportError` in
`utils/imports.py::import_attr_if_importable` alive, which is precisely the guard that site 2's row
exists to pin.

Recommended change: state the scope the comment already states. E.g. `clear()` **itself** runs no
import, so the callback replay is the only place a poisoned `sys.modules` can be reached, and every
lookup there is best-effort. No other sentence in either docstring needs to move; the summary line
("``clear()`` imports nothing") is true of `clear()`'s own body and can stand.

Note the over-broad phrasing was inherited from the brief's own finding-table row ("`clear()` replays
resolved callbacks; no block to skip"), so this is not invention. The build report itself argues at
length that a prescribed fix is a hypothesis; the same standard applies to the half of the brief the
report accepted.

### Low:

#### L1 — the build report's loudest item quotes plan text that no longer exists

`### Notes for Worker 1` item 1 quotes the brief as saying "`filters/inputs.py::clear_filter_input_namespace`
is a bare delegate to `_clear_input_namespace` ... **Neither call site imports anything, so poisoning
`sys.modules` cannot reach either one.**" and asks Worker 1 to correct the plan. Measured:
`grep -n 'Neither call site imports anything\|bare delegate' docs/builder/build-027-filters-0_0_8.md`
returns **0**. Worker 0 already accepted the refutation and rewrote the section — its *Mechanism
truth* block now records site 2 as "misgraded by Worker 0 and NOT a member of the dispatched class",
regraded Low, with the `_safe_import` chain spelled out. The same item cites a brief section
`### What the corrected prose must say`; that heading has **0** hits in the plan. The refutation is
correct and was worth making; as written it now reads as an open action against a document that
already carries the fix, and one of its two citations does not resolve. Recommend rewriting the item
to record the correction as *landed* and drop or re-source the unresolvable heading citation.

#### L2 — the `..._node_field_ledger` finding is likewise already discharged in the plan

`### Notes for Worker 1` item 4 and the seam table's bolded row state that the plan "names a test that
does not exist". At `HEAD`-of-tree the plan's seam paragraph names `..._relay_module` in its list and
then records Worker 0's own correction verbatim, including the same `grep` and the same line 1724.
Independently re-derived: `grep -n '^def test_.*unimportable' tests/test_registry.py` returns five
rows — `test_unregister_tolerates_unimportable_connection_submodule:1435`,
`..._filter_submodules:1617`, `..._order_submodules:1654`, `..._connection_submodule:1690`,
`..._relay_module:1724` — so the naming claim is right and the "the plan says otherwise" framing is
stale. Same recommendation as L1.

#### L3 — the citation-delta baseline is the superseded reading of `bld-slice-4`

The report compares against "`740 (665 in .py, 75 in KANBAN.md)`". `bld-slice-4-027`'s **final**
recorded reading is `742 (665 in 422 .py files, 77 in KANBAN.md)` (three separate sites in that
artifact, including its own reviewer's independent reproduction); `740` was passes 1 and 2, before
the concurrent `KANBAN.md` regenerate. Against the correct baseline this pass moves `742 -> 743`, the
`.py` half `665 -> 666`, and the KANBAN half **does not move at all** — so the paragraph explaining
"the KANBAN half's `+2` is not this pass" is explaining a delta that predates this pass. My own
reading reproduces the report's triple exactly: `OK: 743 citations resolve (666 in 422 .py files, 77
in KANBAN.md).`, exit 0. The conclusion (this pass adds exactly one `path::Symbol` citation) is
correct and was re-derived per file rather than inferred from the total, so only the narration is
wrong. Recorded because this artifact's own precedent is that the previous number in a document is
the thing not to trust.

#### L4 — the order twin's cross-reference now points at contradicting prose

`tests/test_registry.py::test_clear_tolerates_unimportable_order_submodules:1655` opens "Both
order-side ``except ImportError`` guards in ``clear()`` are best-effort" and its second sentence is
"Order twin of ``test_clear_tolerates_unimportable_filter_submodules``". `### Implementation notes`
addresses only the *pointer* half (the name is unchanged, so nothing dangles) — correct as far as it
goes. The semantic half is untreated: a test declaring itself the twin of another now describes the
opposite mechanism from the test it names. Nothing to fix inside this cohort's fence; worth adding to
the `TODO-ALPHA-051-0.0.15` routing note so the 051 pass knows the twin relationship is now
prose-divergent, not merely stale.

### DRY findings

None, and the build report's reason for the "not applicable" holds under re-derivation rather than on
its word: my own token-identity instrument (below) confirms the diff contains no executable token, so
there is no helper, literal, branch, or fixture for a DRY question to attach to.

The one DRY-shaped judgement the pass *did* make — refusing to unify the two docstrings into one
phrasing — is correct, and I re-derived both halves independently rather than accepting the
argument (see `#### Guard-liveness, re-derived independently`). Site 1 pins that `clear()` performs no
import of the filter package; site 2 pins that the substrate's two lookups absorb an `ImportError`.
A single sentence covering both would be false at one of them.

**Existence challenge:** raised and answered in the negative. Both rows pin a live contract that
nothing else pins (measured below), so neither is a candidate for deletion, and there is no new
indirection layer, registry, or helper in this diff to challenge.

#### Executable-token identity, on my own instrument

Written fresh at `<scratchpad>/rev027/w3_tokens_027.py`; the build report's instrument was neither
read nor run. It tokenizes with `tokenize`, drops `COMMENT` / `NL` / `ENCODING` / `ENDMARKER`, drops
every **statement-position** `STRING` (preceded by `NEWLINE` / `INDENT` / `DEDENT` or start-of-file),
and compares the remaining `(type, string)` sequence. Baselines read read-only via
`git show HEAD:<path>` into the scratchpad; no `git checkout` / `stash` / `restore` / `worktree`.

| File | vs `git show HEAD:<path>` | exec tokens |
|---|---|---|
| `tests/test_registry.py` | **IDENTICAL** | 7737 |
| `tests/filters/test_inputs.py` | **IDENTICAL** | 7028 |

`HEAD` is a valid baseline for both: `tests/test_registry.py` was clean at `HEAD`, and for
`tests/filters/test_inputs.py` a `HEAD`-identity verdict is the *stronger* statement — it says no
executable token differs from `HEAD` at all, so neither this pass nor Slice 2 changed one.

**Instrument challenge — five cases, each mutation asserted to have landed before its verdict was
read.** Every mutation was applied to a scratchpad copy by a Python replace guarded with an
`assert` on anchor uniqueness, then confirmed to have landed by counting `diff` output lines. This is
the discipline the build report's own S1-S4 table exists to enforce, and it is why I did not reuse
its script.

| Case | Mutation (scratchpad copy of `tests/test_registry.py`) | landed | Expected | Measured |
|---|---|---|---|---|
| C1 | `assert fresh_registry.get(Category) is None` -> `is not None` in the site-1 row | 2 diff lines | DIVERGENT | **DIVERGENT**, `(1,'None') != (1,'not')` at index 7267, exit 1 |
| C2 | one extra `pass` inserted at the top of the site-1 body | 1 diff line | DIVERGENT | **DIVERGENT**, 7737 -> 7739 tokens, exit 1 |
| C3 | site-1 docstring summary line replaced wholesale | 2 diff lines | IDENTICAL | **IDENTICAL**, exit 0 |
| C4 | site-1 inline comment replaced wholesale | 2 diff lines | IDENTICAL | **IDENTICAL**, exit 0 |
| C5 | `inputs_name = "django_strawberry_framework.filters.inputs"` -> `"MUTATED.module.path"` | 2 diff lines | DIVERGENT | **DIVERGENT**, same token count, string mismatch at index 7185, exit 1 |

C5 is the case the build report's four sanity cases do not cover and the one I most wanted: a
**non**-statement-position string literal. An instrument that dropped all `STRING` tokens rather than
only docstrings would have reported IDENTICAL for a changed module path — the single most plausible
silent hole in this class of check, and the exact shape of edit this cohort's files are full of. It
diverges. The IDENTICAL verdicts above are therefore load-bearing.

#### Guard-liveness, re-derived independently

The corrected docstrings assert each row is a live guard. Re-derived with a second read-only probe
(`<scratchpad>/rev027/probe_027_liveness.py`) that re-enacts each row's poison in-process and then
removes the mechanism *around* it, with no on-disk mutation anywhere:

```text
A1 registry.clear() under site-1 poison: no raise (row passes)
A2 UNGUARDED call-time import of filters.inputs: ImportError -> import of
   django_strawberry_framework.filters.inputs halted; None in sys.modules
A3 import of filters.factories under poisoned parent: ImportError -> No module named
   'django_strawberry_framework.filters.factories'; '...filters' is not a package
B1 clear_filter_input_namespace() under site-2 poison: no raise (row passes)
B2 UNGUARDED import of ...filters.factories: ImportError -> halted; None in sys.modules
B2 UNGUARDED import of ...filters.sets: ImportError -> halted; None in sys.modules
```

- **Site 1 is live, not a tautology.** A2 is the retired mechanism re-enacted: reintroducing a
  call-time import of `filters.inputs` inside `clear()` raises under the row's own poison, so the row
  would fail. The row's assertion is doing work.
- **Site 2 is live, not a tautology.** B2 shows both lookups raise once the guard is removed, so
  deleting the `except ImportError` in `utils/imports.py::import_attr_if_importable` breaks the row.
  A `None` entry in `sys.modules` raises regardless of prior caching, so site 2's premise fires
  deterministically — no order dependence there.
- **A3 confirms the build report's order-dependence analysis** for site 1 and vindicates the
  deliberately weakened comment wording. Site 1 poisons the *parent* package, so whether the replayed
  callback's lookup notices depends on whether `filters.factories` / `filters.sets` are already
  cached in that process; in a process where they are not, the lookup raises internally and returns
  `None`. Both branches satisfy the row's contract. A comment claiming the lookup is "never
  consulted" would have been order-dependently false, and the report was right to refuse it. That
  same measurement is what makes the Medium above a defect rather than a quibble: the poison reaches
  a real import.

### Failability proofs audited

**None to audit, and the empty re-run set is legal here.** The diff introduces no boundary, guard,
gate, or rejection path — established by the token-identity table above, not by the report's
assertion of it — so the mandatory floor (`worker-3.md` "Reading is necessary, not sufficient")
selects nothing. Boundaries re-run: none. Boundaries accepted on Worker 2's record: none; no proof
was recorded, correctly.

The report's `#### Guard-liveness demonstration` claims no failability-proof status, and I agree with
that framing: both boundaries it exercises are **pre-existing at `HEAD`** and outside this cohort's
partition. I re-derived it anyway, above, because "these two rows are live guards" is the load-bearing
claim behind "do not delete or rename them".

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` produces **0** lines. `__all__` and the
re-export list are unchanged. No new public exports.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md. Confirmed: `CHANGELOG.md` is absent from
`git status --porcelain`.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. The only non-`.py` path
this cohort writes is its own artifact. Confirmed against `git status --porcelain`: no version string,
card id, KANBAN row, or spec file moved in this pass, and `docs/SPECS/spec-027-filters-0_0_8.md`
carries only Slices 1 and 3's edits.

### Validation re-run (mine, not the report's)

| Check | Command | Result |
|---|---|---|
| Format (scoped, read-only) | `uv run ruff format --check tests/test_registry.py tests/filters/test_inputs.py` | `2 files already formatted`, exit 0 |
| Lint (scoped, read-only) | `uv run ruff check <same two>` | `All checks passed!`, exit 0 |
| Source layout / ASCII-only | `uv run python scripts/check_trailing_commas.py --check <same two>` | exit 0 |
| Citation gate | `uv run python scripts/check_citations.py` | `OK: 743 citations resolve (666 in 422 .py files, 77 in KANBAN.md).` exit 0 |
| Pre-commit, five hooks | `uvx pre-commit run --files <same two>` | all five **Passed** |
| Whitespace / conflict markers | `git diff --check` | exit 0, no output |
| Focused tests | `uv run pytest tests/test_registry.py tests/filters tests/orders tests/types tests/utils/test_inputs.py --no-cov -q` | **1316 passed in 14.89s** |

Every figure the report states in its own validation table reproduced exactly, the `1316` included.
No `--cov*` flag was passed at any point.

### Rule-27 compliance of the added references

- `utils/inputs.py::_safe_import` (`tests/filters/test_inputs.py:1421`) — resolves. The gate accepts
  a package-relative file half by design (`scripts/check_citations.py` `SOURCE_TREES`), the symbol is
  defined at `django_strawberry_framework/utils/inputs.py::_safe_import`, and there is no competing
  `tests/utils/inputs.py` to make the short form ambiguous (`ls tests/utils/` lists only `test_*.py`).
  It sits entirely on one line, so it is not the wrap-invisible shape.
- `spec-027 Decision 9`, twice (`tests/test_registry.py:1624`, `tests/filters/test_inputs.py:1423`) —
  correct card. `027` is the filters card (`DONE-027-0.0.8`); the 2026-07-30 renumber trap (`spec-021`
  now naming the AppConfig spec) is not tripped, and `grep -c '### Decision 9'` over
  `docs/SPECS/spec-027-filters-0_0_8.md` returns **1** (line 659). No `#"substring"` form was added
  anywhere in this diff, so the broken-target class this cycle has already shipped twice cannot recur
  here. The decision to cite by heading is right.
- **No process provenance.** `git diff -U0 | grep '^+' | grep -Ei 'round|slice|pass [0-9]|review|finding|worker|cycle'`
  returns nothing. The pass also *removed* one such reference in its file's Slice 2 hunk ("the Finding
  2 rule"), which is the correct direction.

One dependency worth naming: site 2's docstring cites Decision 9 for a lifecycle whose Decision 9
bullet is currently **wrong** at `HEAD` (the `delattr` claim — the report's own item 2). The citation
resolves and the decision is the right owner, so this is not a finding against the docstring; it is a
reason Worker 1 should land item 2 rather than defer it, since a docstring now points a reader at the
false bullet.

### Ownership-partition discipline

Re-derived from `git status --porcelain`, not from the report's table. **22** ` M` paths and **10**
`??`. Against this session's start-of-cycle snapshot the delta caused by this pass is exactly:

- ` M tests/test_registry.py` — newly opened, in the declared writable set;
- ` M tests/filters/test_inputs.py` — already dirty from Slice 2, in the declared writable set;
- `?? docs/builder/bld-slice-5-027-retired_mechanism_docstrings.md` — this artifact.

Nothing else moved. `?? docs/builder/build-028-orders-0_0_8.md` is a concurrent `spec-028` session's
plan, correctly classified and correctly left alone. The two baseline-dirty paths the plan lists
(`examples/fakeshop/apps/scalars/models.py`, `examples/fakeshop/test_query/test_scalars_api.py`) are
indeed no longer dirty and were not touched. No production file, spec file, or other card's test file
changed. `HEAD` is still `5c6fdd71`.

**On the three untouched siblings inside a file this cohort owns — leaving them is correct.** Judged
rather than deferred to the report's reasoning. All three (`..._order_submodules`,
`..._connection_submodule`, `..._relay_module`) are stale by exactly the proof above: each says
`clear()` "uses cycle-safe local imports" and "skips that block", and `clear()` has no block and no
import of its own. Repairing them here would put spec-028, spec-030 and spec-032 prose into a
`DONE-027-0.0.8` commit, which the maintainer's scope fence forbids, and would pre-empt
`TODO-ALPHA-051-0.0.15` — a card that demonstrably already collects measured stale-docstring
populations (`KANBAN.md:353`, `:359`, `:360`, `:361` all route source/test halves to it). Physical
write access is not authorization. The resulting one-of-four divergence inside one file is the lesser
defect, and it is recorded in two places. The judgement would flip only if the routing had no home —
see the escalation below.

### What looks solid

- **Site 2's corrected prose is right, and it is right against the source rather than against the
  brief.** I traced the whole chain independently before reading the report's account of it and
  arrived at the same place, including that the two `_safe_import` targets are exactly the two names
  the row poisons, and that the ledger reset (`materialized_names.clear()` / `field_specs.clear()`)
  precedes both lookups — which is what licenses "the reachable ledger reset still completes".
  Refusing the brief's prescribed wording here was the correct call and is the single best judgement
  in this pass.
- **Refusing to unify the two docstrings** — verified, both halves, above.
- **Refusing the rename** — the three reasons hold. Reason 3 is the strongest and I confirmed it:
  `..._order_submodules`'s docstring names site 1 by name, in a file-region this cohort must not edit,
  so rule 27's grep-sweep obligation could not be discharged inside the fence.
- **Leaving the `# ---` section banner alone.** Verified accurate at `HEAD`:
  `utils/inputs.py::_safe_import`'s docstring opens "Cycle-safe import of ``module_path.attr``
  returning ``None`` on ImportError", and there are two guarded lookups on the clear path. Editing it
  would have bought nothing and reflowed an adjacent line.
- **Item 2 (the Decision 9 `delattr` divergence) is real, and was correctly *not* repaired here.**
  Re-derived: `grep -rn delattr django_strawberry_framework/` shows `delattr` only inside
  `clear_generated_input_namespace`'s per-subclass binding-attr reset, never against the `inputs`
  module namespace; the spec bullet at `docs/SPECS/spec-027-filters-0_0_8.md:678` says
  `clear_filter_input_namespace()` "walks `_materialized_names.items()` and
  `delattr(sys.modules[...], name)` for each"; and `utils/inputs.py::clear_generated_input_namespace`
  states the opposite as a deliberate contract with its `strawberry.lazy` reason. The recommended
  replacement wording is accurate. This is a genuine find that Slice 3 missed.
- **`test_unregister_tolerates_unimportable_connection_submodule` correctly excluded.** Re-derived:
  `registry.py::_clear_if_importable` is called from inside `unregister`, so that row's premise still
  fires against a real guarded import.
- Churn classification, the concurrent-file handling, and the scoped write-mode ruff runs are all
  exactly per contract; nothing was reverted.

### Temp test verification

- No temp test under `docs/builder/temp-tests/` was needed. Three throwaway files were written to the
  review scratchpad outside the repo, all carrying `027` in their names:
  `rev027/w3_tokens_027.py` (the token-identity instrument plus its five challenge copies
  `c1.py`-`c5.py`), `rev027/probe_027_clearpath.py` (the `importlib.import_module` spy that produced
  the Medium's measurement), and `rev027/probe_027_liveness.py` (the guard-liveness probe).
- Disposition: **not** candidates for promotion. `probe_027_liveness.py` duplicates contracts the two
  permanent rows already pin, and both probes monkeypatch in-process seams, which `AGENTS.md` rule 10
  permits only when the real path is impossible. They close with this cycle.

### Notes for Worker 1 (spec reconciliation)

1. **The Medium above is a wording fix inside this cohort's own writable set** and needs no spec
   context. It routes back to Worker 2 as a normal revision, not to you.
2. **Escalated: the build report's item 2 (Decision 9's `delattr` bullet) is confirmed and is yours.**
   Independently re-derived above. Spec files are inside this cycle's fence, so this is actionable
   now; the recommended replacement wording reads correctly against the code. It matters slightly
   more than a routine stale bullet because both corrected docstrings now cite Decision 9, so a
   reader following the citation lands on the false claim.
3. **Escalated: this cohort's deferred items currently have no durable home.**
   `bld-final-027.md` reached `final-accepted` before this cohort existed, so its
   `### Deferred work catalog` cannot contain: the three `test_registry.py` twins, the
   `tests/orders/test_inputs.py` twin, L4's prose-divergent cross-reference, and the two plan
   corrections (L1, L2). The maintainer's fence bars this cycle from touching `KANBAN.md`, so no
   worker can file them onto `TODO-ALPHA-051-0.0.15`. Resolution paths: (a) you re-open
   `bld-final-027.md` with an addendum catalog naming this cohort's deferrals; (b) the maintainer
   files them onto 051 at commit time; (c) they are accepted as living only in this artifact. (c) is
   the weakest — this artifact is a per-cycle scratchpad that the next build's pre-flight deletes.
4. **L1 and L2 are corrections to the build report, not to the plan.** The plan is already right on
   both points. If you audit the `### Dispatched findings checklist` ticks, note that box 3's quoted
   text is the *pre-correction* brief wording; quoting as dispatched is what `ARTIFACT.md` asks for,
   so the box is correctly formed even though the plan now reads differently.

### Review outcome

`revision-needed`.

One Medium, and it is the one failure mode this cohort existed to prevent: the repaired docstring
states a mechanism the package does not have. Everything else in the pass is sound — the token-identity
claim survives an independently built and independently challenged instrument, both rows are
demonstrably live guards, every validation figure reproduces, the ownership partition held exactly,
and site 2's refusal of the brief's prescribed wording was correct. The fix is one sentence in
`tests/test_registry.py`'s site-1 docstring, scoped to language the same test's inline comment already
uses. The four Lows are artifact-narration corrections and one routing note; none of them alone would
have blocked acceptance.

---

## Build report (Worker 2, pass 2)

Addresses Worker 3's one Medium and four Lows. The Medium is a real defect in pass 1's own repair and
is fixed in source; the four Lows are corrections to pass 1's narration and are made here rather than
by editing pass 1, per [`ARTIFACT.md`][artifact] `## Re-pass sections` ("never edit prior entries").
**Read pass 1's `### Notes for Worker 1` items 1 and 4 as superseded by `#### L1` and `#### L2` below.**

### Files touched

- `tests/test_registry.py` — one hunk re-edited: the site-1 docstring's third sentence. The inline
  comment from pass 1 is unchanged; it was already the correct half.
- `docs/builder/bld-slice-5-027-retired_mechanism_docstrings.md` — this section.

No other file. `tests/filters/test_inputs.py` is untouched by this pass: Worker 3 accepted site 2's
prose as correct against source, and pass 1's DRY-in-the-negative conclusion (do not unify the two
docstrings) was re-derived and upheld by the review.

### Medium — fixed: "No import runs on the clear path"

**Worker 3 is right and pass 1 was wrong.** Re-derived independently before touching the file, with my
own probe rather than by reading either account — `<scratchpad>/test_clearpath_probe.py`, a read-only
spy on `importlib.import_module` restored in a `finally`:

```text
registered subsystem clears (before_bind=False): 10
import_module calls during registry.clear(): 2
    django_strawberry_framework.filters.factories
    django_strawberry_framework.filters.sets
import statements inside TypeRegistry.clear body: []
except ImportError in registry.py source: 0
```

Same count, same two module names, same registered-callback total Worker 3 measured. Imports do run on
the clear path; what runs no import is `clear()`'s **own body**. Pass 1 established exactly this
distinction in the inline comment ten lines below and then failed to carry it into the docstring — so
the function contradicted itself, and the docstring held the wrong half. This is the same over-broad
inference pass 1 refuted at site 2, reproduced one scope level up at site 1: the half of the brief
pass 1 *accepted* deserved the same distrust as the half it refuted.

**A third process state, which neither the review nor the brief measured.** My first probe run returned
**0** import calls, and that was the probe's own flaw rather than a contradiction: it never imported
the filter subsystem, so nothing had registered a callback. Corrected by importing
`filters.inputs` first, as the real harness's conftest does. The invariant the docstring must state
therefore has to hold across three states, not two:

| Process state | Imports on the clear path | `clear()` raises? |
|---|---|---|
| filter subsystem never imported (no callback registered) | **0** | no |
| subsystem imported, both lookup targets already cached | **2**, both succeed, poison never consulted | no |
| subsystem imported, lookup targets evicted | 2 attempted, both raise internally, absorbed to `None` | no |

Re-derived for the third row, with site 1's own poison applied (parent package + `inputs`):

```text
already cached in THIS process: {'...filters.factories': True, '...filters.sets': True}
  cached branch:   ...filters.factories imported WITHOUT touching poisoned parent
  uncached branch: ...filters.factories -> ImportError: No module named
                   '...filters.factories'; '...filters' is not a package
```

This confirms the order-dependence pass 1 recorded and is why the fix does not reach for a stronger
claim: site 1 poisons the **parent** package and `filters.inputs`, never the two names the replayed
callback looks up, so whether that lookup notices is import-cache-order dependent. The new wording is
true in all three rows.

Before (pass 1):

```python
    """``clear()`` imports nothing, so a broken ``sys.modules`` cannot break it.

    Every subsystem binds its own teardown callback at ITS import time via
    ``register_subsystem_clear``, and ``clear()`` replays the already-resolved
    callables. No import runs on the clear path, so poisoning the filter
    modules in ``sys.modules`` (done here) cannot make ``clear()`` raise: the
    registry's own state is dropped either way (spec-027 Decision 9).
    """
```

After:

```python
    """``clear()`` itself imports nothing, so a broken ``sys.modules`` cannot break it.

    Every subsystem binds its own teardown callback at ITS import time via
    ``register_subsystem_clear``, and ``clear()`` replays the already-resolved
    callables. That replay is the only place a poisoned ``sys.modules`` can be
    reached at all, and every submodule lookup it makes is best-effort, so
    poisoning the filter modules (done here) cannot make ``clear()`` raise:
    the registry's own state is dropped either way (spec-027 Decision 9).
    """
```

Three deliberate choices in the wording:

- **The summary line gained `itself`.** Worker 3 judged the old summary ("``clear()`` imports nothing")
  true of `clear()`'s own body and said it could stand. It can, but only when read in the scope the
  body sentence sets — and the body sentence is what was wrong, so the summary was the one line a
  reader could take away unqualified. Scoping it costs one word and removes the ambiguity at its
  source. This is the only change to a line Worker 3 did not require.
- **"That replay is the only place a poisoned ``sys.modules`` can be reached at all"** replaces "No
  import runs on the clear path". It states the same protective fact the false sentence was reaching
  for — the poison has exactly one route inward — without denying that route exists.
- **"every submodule lookup it makes is best-effort"** is the clause that makes the sentence survive
  rows 2 and 3 above, and it is deliberately *not* site 2's phrasing. Site 1 pins that `clear()`'s own
  body imports nothing; site 2 pins that the substrate's two lookups absorb an `ImportError`. Unifying
  them would make one of the two false, which is the conclusion pass 1 reached and the review
  independently confirmed by proof.

Not weakened into vagueness, and no executable token moved (re-proved below).

### Lows — closed

#### L1 — pass 1's item 1 quotes plan text that no longer exists

Confirmed, re-derived rather than accepted: over `docs/builder/build-027-filters-0_0_8.md`,
`grep -c 'Neither call site imports anything'` = **0**, `grep -c 'bare delegate'` = **0**,
`grep -c 'What the corrected prose must say'` = **0**. Worker 0 had already landed the site-2 regrade
into the plan before the review reached it.

**The plan as it now stands** carries a `*Site 2 was misgraded by Worker 0 and is NOT a member of the
dispatched class.*` paragraph that traces the full `_safe_import` chain, names the two poisoned
modules as the two lookup targets, attributes the cause ("inferring the whole chain from the one-line
delegate body without following `_clear_input_namespace` into `utils/`"), regrades the site **Low,
stale spelling**, and rewrites the finding table's site-2 row to match. Its "Mechanism truth" block
also now splits site 1 (holds as dispatched) from site 2 explicitly.

So the refutation is **landed, not open**. Pass 1's item 1 should be read as the record of how the
correction was derived, not as an action against the plan. Nothing further is owed to it, and its
citation of a `### What the corrected prose must say` heading does not resolve — that text was in the
dispatch prompt, never in the plan, so it was never a rule-27-citable surface and pass 1 should not
have quoted it as one.

**One residual, and it is the same defect this Medium was:** the plan's post-table paragraph still
reads "Site 1 pins that `clear()` imports nothing, so a poisoned `sys.modules` cannot make it raise".
Unqualified, that is the sentence Worker 3 graded Medium in my docstring. The plan is Worker 0's file
and outside my writable set, so it is recorded here rather than edited. Recommended replacement:
"Site 1 pins that `clear()`'s own body imports nothing, so the callback replay is the only route a
poisoned `sys.modules` has inward, and every lookup on it is best-effort."

#### L2 — pass 1's item 4 and seam-table row are likewise stale

Confirmed. `grep -c 'node_field_ledger' docs/builder/build-027-filters-0_0_8.md` = **1**, and that one
occurrence *is* Worker 0's own correction ("Worker 0 also named the third registry twin
`..._node_field_ledger`, which is the docstring's subject, not the function"); `..._relay_module` now
appears twice in the plan, in the seam list and in that correction. Independently re-derived here:
`grep -n '^def test_.*unimportable' tests/test_registry.py` returns five rows —
`test_unregister_tolerates_unimportable_connection_submodule:1435`, `..._filter_submodules:1617`,
`..._order_submodules:1654`, `..._connection_submodule:1690`, `..._relay_module:1724`.

The naming claim was right; the "the plan says otherwise" framing is stale and is retracted. The seam
table's bolded row and item 4 both stand corrected to: **the plan already names `..._relay_module`
correctly and records the earlier mis-naming itself.**

The plan additionally corrected something pass 1 got wrong and the review did not flag: pass 1's seam
table lists all four twins as stale "by the same proof". They are not. The split is **3 + 1** — the
three `test_registry.py` twins describe `TypeRegistry.clear` and are stale by site 1's proof; the
`tests/orders/test_inputs.py` twin routes through the same shared substrate and therefore carries
site 2's regraded **Low stale-spelling** defect, not the false-mechanism one. Pass 1's own note on
that row said as much in prose while the table's framing did not. The 051 pass inherits two
populations, not one.

#### L3 — citation-delta baseline corrected

Confirmed and re-measured across the whole of `bld-slice-4-027`: the string
`OK: 742 citations resolve (665 in 422 .py files, 77 in KANBAN.md)` occurs **8** times and
`OK: 740 ... (665 ..., 75 in KANBAN.md)` occurs **3** times, so `742/665/77` is that artifact's final
reading and `740/665/75` was its passes 1-2, before a concurrent `KANBAN.md` regenerate.

Corrected delta, against the right baseline:

| Half | `bld-slice-4` final | this cohort | delta | attribution |
|---|---|---|---|---|
| total | 742 | **743** | +1 | this pass |
| `.py` | 665 | **666** | **+1** | this pass's one added `path::Symbol`, `utils/inputs.py::_safe_import` |
| `KANBAN.md` | 77 | **77** | **0** | — |

The KANBAN half **does not move at all**, so pass 1's paragraph explaining "the KANBAN half's `+2` is
not this pass" was explaining a delta that predates this pass entirely. Retracted. The per-file
conclusion is unaffected and was re-derived per file rather than inferred from the total, which is why
a wrong baseline corrupted only the narration. The lesson is this cycle's own: **the previous number
in a document is the thing not to trust** — and pass 1 read the first figure it found in a
4,000-line artifact instead of the last.

#### L4 — the order twin's cross-reference is prose-divergent, not merely stale

Confirmed and added to the routing record. `tests/test_registry.py::test_clear_tolerates_unimportable_order_submodules`
opens "Both order-side ``except ImportError`` guards in ``clear()`` are best-effort" and its second
sentence is "Order twin of ``test_clear_tolerates_unimportable_filter_submodules``". Pass 1 treated
only the **pointer** half (the name is unchanged, so nothing dangles) and that remains true. The
**semantic** half is now recorded: after this pass, a test that declares itself the twin of site 1
describes the opposite mechanism from the test it names — it still claims `except ImportError` guards
inside `clear()` and a block to skip, both of which `clear()` has neither of.

Not fixed here: it is spec-028's surface and outside the writable set. See
`### Deferred items this cohort owns` for the routing entry.

### Deferred items this cohort owns

Stated explicitly so they survive re-homing, per Worker 3's escalation 3 — `bld-final-027.md` reached
`final-accepted` before this cohort existed, so its `### Deferred work catalog` cannot contain these,
and the maintainer's fence bars this cycle from `KANBAN.md`. Nothing here is actionable by me.

1. **`tests/test_registry.py::test_clear_tolerates_unimportable_order_submodules`** (spec-028) — stale
   by site 1's proof; **and** its "Order twin of ..." cross-reference is now prose-divergent (L4).
   Routes to `TODO-ALPHA-051-0.0.15`.
2. **`tests/test_registry.py::test_clear_tolerates_unimportable_connection_submodule`** (spec-030) —
   stale by site 1's proof. Routes to 051.
3. **`tests/test_registry.py::test_clear_tolerates_unimportable_relay_module`** (spec-032) — stale by
   site 1's proof. Routes to 051. Not `..._node_field_ledger`; that is its docstring's subject.
4. **`tests/orders/test_inputs.py::test_clear_order_input_namespace_tolerates_unimportable_submodules`**
   (spec-028) — site 2's twin, so **Low stale-spelling**, a different defect from items 1-3. Routes
   to 051. Whoever takes 051 must not repair it with site 1's wording.
5. **`spec-027` `### Decision 9`'s `delattr` bullet** — with Worker 1; confirmed by Worker 3 and
   carried in the plan as "one spec edit IS owed". Both corrected docstrings cite Decision 9, so a
   reader following either citation currently lands on the false bullet.
6. **The plan's own residual over-broad sentence** ("Site 1 pins that `clear()` imports nothing") —
   replacement wording in `#### L1`. Worker 0's file.

### Validation run

Re-run in full. Every command from the repository root; no `--cov*` flag anywhere.

| Check | Command | Result |
|---|---|---|
| Format (scoped) | `uv run ruff format tests/test_registry.py tests/filters/test_inputs.py` | `2 files left unchanged`, exit 0 |
| Lint (scoped) | `uv run ruff check --fix <same two>` | `All checks passed!`, exit 0 |
| Source layout / ASCII-only | `uv run python scripts/check_trailing_commas.py --check <same two>` | exit 0 |
| Citation gate | `uv run python scripts/check_citations.py` | `OK: 743 citations resolve (666 in 422 .py files, 77 in KANBAN.md).` exit 0 — unchanged from pass 1, and this pass added no citation |
| Pre-commit, five hooks | `uvx pre-commit run --files <same two> <this artifact>` | all five **Passed** |
| Focused tests | `uv run pytest tests/test_registry.py tests/filters tests/orders tests/types tests/utils/test_inputs.py --no-cov -q` | **1316 passed in 7.63s** |
| Guard liveness (scratchpad, nothing on disk mutated) | `uv run pytest <scratchpad>/test_guard_liveness.py --no-cov -q` | **2 passed** — both rows still live after the reword |
| Clear-path probe (scratchpad) | `uv run pytest <scratchpad>/test_clearpath_probe.py --no-cov -q -s` | **3 passed**; output quoted under the Medium |
| Longest line in the edited region | `awk` over `tests/test_registry.py:1617-1650` | 87 chars, under the 99 limit; no E501 grace needed |
| Churn | `git status --porcelain` | unchanged from pass 1 apart from this artifact; nothing new, nothing reverted |

#### Executable-token identity, re-proved for both files and both baselines

Same instrument, re-run after the fix. Baselines untouched since pass 1 (`git show HEAD:` copies and
the pre-pass working-tree copies, both outside the repo). No `git checkout` / `stash` / `restore` /
`worktree`.

| File | vs `git show HEAD:<path>` | vs the pre-pass working-tree copy | Token count |
|---|---|---|---|
| `tests/test_registry.py` | IDENTICAL (0 divergences) | IDENTICAL (0 divergences) | 7737 |
| `tests/filters/test_inputs.py` | IDENTICAL (0 divergences) | IDENTICAL (0 divergences) | 7028 |

**Worker 3's C5 challenge case added to my own challenge set — and my instrument does not have the
hole.** The case is a **non**-statement-position `STRING`: an instrument that dropped every `STRING`
rather than only docstrings would report IDENTICAL for a changed module path, which is the most
plausible silent hole for this file class and the exact shape of literal these tests are full of. Run
against a scratchpad copy with the mutation's landing asserted first (anchor unique, then 2 `diff`
lines confirmed):

| Case | Mutation | landed | Expected | Measured |
|---|---|---|---|---|
| C5 | `inputs_name = "django_strawberry_framework.filters.inputs"` -> `"MUTATED.module.path"` | 2 diff lines | DIVERGENT | **DIVERGENT**, 1 divergence, token count unchanged at 7737, `(3, '"django_strawberry_framework.filters.inputs"') != (3, '"MUTATED.module.path"')` at index **7185**, exit 1 |

Index 7185 is the same index Worker 3's independently written instrument reported, which is a stronger
result than either verdict alone: two instruments built separately agree on the position, so the
IDENTICAL verdicts above rest on a check proven to see string-literal changes. My challenge set is now
five cases (pass 1's S1/S4 DIVERGENT, S2/S3 IDENTICAL, plus C5 DIVERGENT). Worker 3 was right that
four was one short, and the omission was in the direction that would have made a real defect invisible.

### Failability proofs

None; this pass introduced no new boundary. The token-identity table above establishes it mechanically
rather than by assertion: the diff contains no statement, branch, guard, comparison, or raise.

### Hot-path budget

Not applicable; plan declares no hot path. Zero executable tokens changed.

### Floor verification

Not applicable; plan declares floor-verification scope none. Zero executable tokens changed.

### Implementation notes

- **No production file was mutated, transiently or otherwise, in either pass.** The Medium's
  measurement came from a scratchpad pytest that patches `importlib.import_module` in-process and
  restores it in a `finally`, so no on-disk mutation existed at any point and none could survive a
  crash. `registry.py` and `utils/` are outside this cohort's partition and were only read.
- **My first probe was wrong in a way worth recording**, because it is the same class as the Medium: it
  reported 0 imports and I nearly had a measurement that appeared to contradict the review. The cause
  was the probe's own missing precondition (it never imported the subsystem, so nothing registered a
  callback). A probe that measures the absence of something must first establish that the thing had a
  chance to be present — otherwise it measures its own setup. Fixing it turned a false contradiction
  into the third row of the state table above.

### Notes for Worker 3

- The only source change in this pass is the site-1 docstring's summary line and third sentence.
  Everything else is artifact narration.
- The three-row state table under the Medium is the thing to check the new wording against; a
  reword that is true in rows 2 and 3 but false in row 1 (or vice versa) is the trap here.
- My challenge set now includes your C5 and reproduces your index 7185. Instrument and probes are at
  `<scratchpad>/token_identity.py`, `<scratchpad>/test_clearpath_probe.py`,
  `<scratchpad>/test_guard_liveness.py` — all outside the repo, all disposable with the cycle, none a
  promotion candidate (each monkeypatches an in-process seam, which `AGENTS.md` rule 10 permits only
  where the real path is impossible; the permanent rows already pin the contracts).
- Pass 1's `### Notes for Worker 1` items 1 and 4 are superseded by `#### L1` and `#### L2` here. Items
  2 (the Decision 9 `delattr` bullet) and 3 (the banner) stand unchanged.

### Notes for Worker 1 (spec reconciliation)

1. **Item 2 from pass 1 stands and is unchanged**: `spec-027` `### Decision 9`'s bullet claiming
   `clear_filter_input_namespace()` walks `_materialized_names.items()` and `delattr`s each is false at
   `HEAD`; the code parks them deliberately. Worker 3 re-derived it and the plan now carries it as "one
   spec edit IS owed". Recommended replacement wording is in pass 1, unchanged. It matters slightly
   more after this pass than before: **both** corrected docstrings cite Decision 9.
2. **No new spec issue surfaced by this pass.** No spec file was read for edit and none was touched.
3. **`### Deferred items this cohort owns` above is the explicit list** Worker 3's escalation 3 asked
   for, so whichever re-homing path you or the maintainer choose has a single place to read from.
   Item 6 is a correction to the build plan rather than the spec, and is Worker 0's.

---

## Review (Worker 3, pass 2)

Re-reviewed against `HEAD` `5c6fdd71`. Everything below was re-derived on this pass; nothing was
carried over from my pass-1 verdict and nothing was accepted from the pass-2 report's account of it.
No repository file was mutated at any point, transiently or otherwise. `docs/SPECS/spec-027-filters-0_0_8.md`,
its rationale companion, `bld-final-027.md`, and the concurrent spec-028 session's files are out of
scope and were read only where a claim in *this* artifact depends on their current state.

### High:

None.

### Medium:

#### The `### Deferred items this cohort owns` list carries two already-discharged items and one that is materially understated

This is the only finding of the round, and it is graded Medium for one reason: Worker 1 is homing this
list into `bld-final-027.md`'s `## Deferred work catalog`, so an item that is wrong here becomes wrong
in the durable record. **Neither staleness was the builder's error at write time** — both were
discharged concurrently, after the pass-2 report was written. This is a reviewer's catch, not a
builder's defect.

**Item 5 (`spec-027` `### Decision 9`'s `delattr` bullet) is DISCHARGED.** Worker 1 landed it.
Measured: `grep -n delattr docs/SPECS/spec-027-filters-0_0_8.md` returns **one** hit, line 672, and it
is now the *negation* of the old claim, inside a bullet whose own title states the opposite —
"**Materialized class objects stay parked in the `django_strawberry_framework.filters.inputs` module
`__dict__`; no clear path strips them.** ... Stripping a global with `delattr` would break any
`strawberry.lazy(...)` LazyType ...". The neighbouring ledger bullet was rewritten too and now ends
"Both submodule lookups the clear needs are best-effort: an unimportable `filters.factories` or
`filters.sets` skips only its own dependent reset and never prevents the reachable ledger reset" —
which is site 2's docstring in the spec's own words. As written, item 5 would send a future pass to
re-fix a bullet that is already correct, and its stated consequence ("both corrected docstrings cite
Decision 9, so a reader following either citation currently lands on the false bullet") is no longer
true: a reader following either citation now lands on the *right* bullet.

**Item 6 (the plan's residual over-broad sentence) is DISCHARGED.** Worker 0 landed it. Measured:
`grep -n 'Site 1 pins' docs/builder/build-027-filters-0_0_8.md` now reads "Site 1 pins that
`clear()`'s **own body** imports nothing, so the only route a poisoned `sys.modules` can reach is a
replayed callback's best-effort lookup, which skips rather than propagates; reintroducing a call-time
import into `clear()` itself breaks it", followed by the probe measurement and an explicit note that
the unqualified form is FALSE. The replacement `#### L1` recommended is in effect, in substance and
nearly in wording.

**Item 4 is understated, and the understatement is the actionable half.** It reads "site 2's twin, so
**Low stale-spelling**". Measured at `tests/orders/test_inputs.py:903-911`, that docstring carries
three defects, only one of which is a spelling:

- **Three raw `path:NN` source refs in a `.py` docstring** — `` inputs.py:461-462 ``,
  `` inputs.py:476-477 ``, and "(lines 1009-1028)". `AGENTS.md` rule 27 permits raw `path:NN` only in
  per-cycle scratchpad artifacts, "never in code comments specs or standing docs". This is **this
  cycle's own D12/D13 class**, not a spelling issue, and `scripts/check_citations.py` is structurally
  blind to it (`path::Symbol` only).
- **A claim of guards that do not exist**: "exercising BOTH ``except ImportError: pass`` guards in
  ``clear_order_input_namespace``". Measured:
  `grep -c 'except ImportError' django_strawberry_framework/orders/inputs.py` = **0**. That is site
  1's false-mechanism shape, not site 2's spelling shape — so the 3+1 population split, correct as
  far as it goes, does not mean item 4 carries *only* the Low defect.
- **A rotted cross-reference range**: it cites the filter twin at "(lines 1009-1028)"; that function
  is at `tests/filters/test_inputs.py:1417`.

Left as written, item 4 licenses a 051 pass to close it with a `from ... import ...` wording tweak
while leaving three rule-27 violations and a false guard claim in place.

**Recommended edits, all to this artifact's deferred list — no source change:**

- Item 5: annotate `DISCHARGED by Worker 1` with the line-672 measurement, and strike the
  "both docstrings cite the false bullet" consequence.
- Item 6: annotate `DISCHARGED by Worker 0` with the corrected sentence quoted.
- Item 4: widen to "site 2's twin for the `from ... import ...` spelling, **plus** three raw `path:NN`
  refs (rule 27, this cycle's D13 class), **plus** a false `except ImportError: pass` guard claim
  (`grep -c` = 0 in `orders/inputs.py`), **plus** a rotted line-range cross-reference" — so 051
  inherits the whole surface rather than the smallest of its four defects.

**Escalated to Worker 1 rather than re-looped to Worker 2**, per `worker-3.md` "Worker 3 may also set
`review-accepted` with Medium-or-higher findings transparently escalated". The resolution needs spec
context Worker 2 cannot supply: item 5's status is Worker 1's own concurrent edit to a spec that is
**mid-flight right now** under a second Worker 1 round, item 6 is Worker 0's file which Worker 2 may
not write, and Worker 1 owns the homing that consumes the list. Sending Worker 2 to re-annotate a list
against a moving spec would race the edit. See `### Notes for Worker 1` below for the resolution paths.

### Low:

#### The state table's row-3 label says "evicted" where the measured cause is "never imported"

`### Medium — fixed` state table, row 3: "subsystem imported, lookup targets evicted". The measured
mechanism is absence from `sys.modules`, and in the probe output quoted directly beneath it the cause
is that the two targets were never imported in that process, not that anything evicted them. Absence
is absence, so the row's *behaviour* column is right and the verdict does not turn on it. Recorded
only because check 1 of this round makes that table load-bearing, and because a one-word imprecision
in a derived description is the defect class this cycle keeps re-shipping. Suggested: "lookup targets
absent from `sys.modules`".

### The Medium from pass 1 is closed, and the three-state claim holds — verified more strongly than claimed

Current text at `tests/test_registry.py:1618-1625`, checked sentence by sentence:

1. **"``clear()`` itself imports nothing"** — verified statically by AST, not by reading:
   `ast.walk` over `inspect.getsource(TypeRegistry.clear)` yields **0** `Import` / `ImportFrom` nodes.
   The added `itself` is the right scoping and closes the ambiguity I left open in pass 1 (I said the
   old summary "could stand"; scoping it is better than what I asked for).
2. **"That replay is the only place a poisoned ``sys.modules`` can be reached at all"** — verified.
   `clear()`'s body has 0 import nodes; `TypeRegistry._run_type_teardowns`, the *other* callable-replay
   on the clear path, also has **0**; and the package's single `register_type_teardown` call site
   (`django_strawberry_framework/types/finalizer.py::_attach_relation_connection_teardown` region,
   `#"registry.register_type_teardown(type_cls, teardown)"`) registers a closure that only mutates
   `__annotations__` and class attributes — no import. Dynamically, **every** `importlib.import_module`
   attempt observed during a real `clear()` arrived through the subsystem replay; caller frames
   captured per call, all four reading `clear_generated_input_namespace` -> `_safe_import` ->
   `import_attr_if_importable`.
3. **"every submodule lookup it makes is best-effort"** — this is the clause the whole three-state
   claim rests on, and it is a claim about the *entire* replay, not just the filter callback. I tested
   it at maximum subsystem load rather than at the load the report measured. Probe: `pkgutil.walk_packages`
   the whole package so every subsystem registers (0 modules failed to import), then force
   `importlib.import_module` to raise `ImportError` **unconditionally**, then `clear()`:

```text
registered subsystem clears: 17
import nodes inside TypeRegistry.clear body: []
import nodes inside TypeRegistry._run_type_teardowns body: []
clear() with EVERY import_module forced to raise -> NO RAISE
import_module attempts during that clear(): 4
    django_strawberry_framework.filters.factories  <- clear_generated_input_namespace/_safe_import/import_attr_if_importable
    django_strawberry_framework.filters.sets       <- clear_generated_input_namespace/_safe_import/import_attr_if_importable
    django_strawberry_framework.orders.factories   <- clear_generated_input_namespace/_safe_import/import_attr_if_importable
    django_strawberry_framework.orders.sets        <- clear_generated_input_namespace/_safe_import/import_attr_if_importable
```

   This is a **superset** of the report's state 3: not one poisoned module but every import on the
   replay forced to fail, at 17 registered callbacks rather than 10, and `clear()` still does not
   raise. Rows 1 and 2 follow trivially — with no callback registered the replay makes zero lookups
   and the clause is vacuously true; with both targets cached the lookups succeed. So the sentence is
   true in all three process states **and** in a fourth the report did not name (every subsystem
   loaded, every lookup failing).

   Two observations, neither a finding. The registered-callback count is itself process-state
   dependent — **10** with only the filter subsystem imported, **17** with the whole package imported —
   so the report's `10` is a correct reading of its own process, not a competing number. And the
   docstring's clause is now a *stronger* statement than what site 1's row deterministically pins:
   the row's own guaranteed failure mode is a call-time import inside `clear()` (proved below), while
   whether the replay's lookups hit the poison is import-cache-order dependent. The clause is
   nonetheless necessary for the sentence to be true in state 3, and it is true, so keeping it is
   right.

**The function no longer contradicts itself.** Docstring: "``clear()`` itself imports nothing" /
"That replay is the only place a poisoned ``sys.modules`` can be reached at all, and every submodule
lookup it makes is best-effort". Inline comment ten lines below: "``clear()`` itself runs no import,
so the poisoning can only reach a replayed callback's own best-effort lookup, which skips rather than
propagates." Same scope, same mechanism, same direction. The pass-1 contradiction is gone.

**The two sites remain deliberately distinct and neither has drifted.** Re-derived by re-running my
own liveness probe against the reworded file, not by re-reading the argument:

```text
A1 registry.clear() under site-1 poison: no raise (row passes)
A2 UNGUARDED call-time import of filters.inputs: ImportError -> halted; None in sys.modules
A3 import of filters.factories under poisoned parent: ImportError -> '...filters' is not a package
B1 clear_filter_input_namespace() under site-2 poison: no raise (row passes)
B2 UNGUARDED import of ...filters.factories / ...filters.sets: ImportError -> halted; None in sys.modules
```

Site 1 still fails if a call-time import is reintroduced into `clear()` (A2); site 2 still fails if
the guard is removed from `utils/imports.py::import_attr_if_importable` (B2). The shared vocabulary
("best-effort") describes the same substrate honestly at both sites without either docstring claiming
the other's pinned contract. `tests/filters/test_inputs.py` is byte-unchanged from the text I accepted
in pass 1 — the diff hunk reads verbatim as it did, and its executable-token count is unchanged at
7028.

### Every pass-1 Low re-checked as closed, not merely reworded

Each closure's own measurement re-derived, and **counted as occurrences rather than matching lines** —
the whole seam paragraph is a single line, so a `grep -c` here reports 1 for a term that appears twice.

| Low | Closure claim | My measurement |
|---|---|---|
| L1 | the three quoted plan strings have 0 hits | `Neither call site imports anything` **0**, `bare delegate` **0**, `What the corrected prose must say` **0** — and the plan's `*Site 2 was misgraded ...*` paragraph is present, tracing the `_safe_import` chain and regrading the site Low. Retraction correct; the "never a rule-27-citable surface" reading of the vanished heading is also correct — it was dispatch-prompt text |
| L2 | plan names `..._relay_module`, records its own earlier mis-naming | `_relay_module` **2 occurrences**, `node_field_ledger` **1 occurrence** (inside Worker 0's correction). `grep -n '^def test_.*unimportable' tests/test_registry.py` returns the same five rows I measured in pass 1. Retraction correct |
| L3 | `742/665/77` is `bld-slice-4`'s final reading, `740/665/75` its passes 1-2 | 742-string **8 occurrences**, 740-string **3 occurrences**. Corrected delta table is right: total 742->743, `.py` 665->666, KANBAN 77->**77 unchanged**. My own gate reading reproduces `OK: 743 citations resolve (666 in 422 .py files, 77 in KANBAN.md).` |
| L4 | the order twin's cross-reference is prose-divergent, recorded and routed | Verified at `tests/test_registry.py:1655`: opens "Both order-side ``except ImportError`` guards in ``clear()``" and calls itself "Order twin of ``test_clear_tolerates_unimportable_filter_submodules``". Both halves of the closure (pointer intact, semantics divergent) are accurate |

L2's closure also volunteers a correction pass 1 got wrong that I did not flag — the seam table framed
all four twins as stale "by the same proof" when the split is 3 + 1. That is a real self-catch and it
is right. The Medium above is where that same list still needs one more turn.

No new inaccuracy was introduced by any of the four closures. The one imprecision I did find in the
new narration is the Low above.

### DRY findings

None. Re-established mechanically rather than carried over: the token-identity table below shows the
diff still contains no executable token, so there remains no helper, literal, branch, or fixture for a
DRY question to attach to. The refusal to unify the two docstrings survives the reword — verified by
the A2/B2 measurements above, which show the two rows still fail for different reasons.

**Existence challenge:** raised again, answered in the negative again. Both rows pin a live contract
nothing else pins, and this pass adds no indirection to challenge.

#### Executable-token identity, re-established (not carried over) and re-challenged

My own instrument, re-run against baselines whose integrity I re-verified first — `git show HEAD:<path>
| cmp -` against each round-1 scratchpad copy passes, so the baselines have not drifted under a
concurrent session.

| File | vs `git show HEAD:<path>` | exec tokens |
|---|---|---|
| `tests/test_registry.py` | **IDENTICAL** | 7737 |
| `tests/filters/test_inputs.py` | **IDENTICAL** | 7028 |

**Instrument re-challenged against the pass-2 files — five cases, each mutation's landing asserted
before its verdict was read** (anchor-uniqueness `assert`, then `diff` line count). Re-challenging
rather than trusting round 1's challenge is the point: the file changed, and an instrument is only
proven against the bytes it is actually run on.

| Case | Mutation | landed | Expected | Measured |
|---|---|---|---|---|
| D1 | site-1 row's `assert ... is None` -> `is not None` | 2 diff lines | DIVERGENT | **DIVERGENT**, `(1,'None') != (1,'not')` at index 7267, exit 1 |
| D2 | one `sys.modules[...] = None` statement **deleted** | 1 diff line | DIVERGENT | **DIVERGENT**, 7737 -> 7728 tokens, exit 1 |
| D3 | the **new** pass-2 summary line replaced wholesale | 2 diff lines | IDENTICAL | **IDENTICAL**, exit 0 |
| D4 | `inputs_name = "...filters.inputs"` -> `"MUTATED.module.path"` | 2 diff lines | DIVERGENT | **DIVERGENT**, index **7185**, exit 1 |
| D5 | same shape in the **other** file: `factories_name` literal cased | 2 diff lines | DIVERGENT | **DIVERGENT**, index 6311, exit 1 |

D2 is new this round and covers the direction round 1 did not: a **deleted** statement rather than an
inserted one. D5 is new too — it challenges the second baseline, so the `tests/filters/test_inputs.py`
IDENTICAL verdict is no longer resting on an instrument only ever challenged against the other file.

**C5/D4 index agreement confirmed, not assumed.** My independently written instrument reports the
divergence at index **7185**; the report states index **7185** for the same mutation. I re-ran mine on
the pass-2 file to get that number rather than quoting my pass-1 figure. Two instruments written
separately, agreeing on a position and not merely a verdict, is the strongest form this check takes
here — and D3 confirms mine still ignores the very docstring the pass rewrote, so the agreement is not
an artefact of both instruments being blind in the same place.

### Failability proofs audited

**None to audit; the empty re-run set is still legal.** The diff introduces no boundary, guard, gate,
or rejection path — established by the token-identity table above rather than asserted — so the
mandatory floor selects nothing. Boundaries re-run: none. Boundaries accepted on Worker 2's record:
none; no proof was recorded, correctly. The report's own `### Failability proofs` says exactly this.

The report's guard-liveness and clear-path probes claim no failability-proof status, correctly: both
boundaries they exercise are pre-existing at `HEAD` and outside this cohort's partition. I re-derived
both independently anyway, above.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` produces **0** lines. `__all__` and the
re-export list unchanged. No new public exports.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md. `CHANGELOG.md` is absent from `git status --porcelain`.

### Documentation / release sanity

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. The only non-`.py` path
this cohort writes remains its own artifact. `docs/SPECS/spec-027-filters-0_0_8.md`,
`docs/SPECS/appx/spec-027-filters-0_0_8-rationale.md` and `bld-final-027.md` are dirty from Worker 1's
concurrent spec round and are explicitly out of my scope: read where a claim here depends on them,
never edited, never reverted.

### Validation re-run (mine)

| Check | Command | Result |
|---|---|---|
| Format (read-only) | `uv run ruff format --check tests/test_registry.py tests/filters/test_inputs.py` | `2 files already formatted`, exit 0 |
| Lint (read-only) | `uv run ruff check <same two>` | `All checks passed!`, exit 0 |
| Source layout / ASCII-only | `uv run python scripts/check_trailing_commas.py --check <same two>` | exit 0 |
| Non-ASCII sweep, independent | `LC_ALL=C grep -nP '[^\x00-\x7F]' <same two>` | no match (exit 1) |
| Citation gate | `uv run python scripts/check_citations.py` | `OK: 743 citations resolve (666 in 422 .py files, 77 in KANBAN.md).` exit 0 |
| Pre-commit, five hooks | `uvx pre-commit run --files <same two> <this artifact>` | all five **Passed** |
| Whitespace / conflict markers | `git diff --check` | exit 0, no output |
| Longest line, edited region | `awk` over `tests/test_registry.py:1617-1652` | **87** chars — reproduces the report's figure, under the 99 limit, no E501 grace needed |
| Focused tests | `uv run pytest tests/test_registry.py tests/filters tests/orders tests/types tests/utils/test_inputs.py --no-cov -q` | **1316 passed in 15.12s** |

Every figure the pass-2 report states reproduced: `1316`, `743 (666, 77)`, five hooks Passed, 87-char
longest line. No `--cov*` flag was passed at any point in this round.

### Rule 27 and provenance, re-checked on the changed lines

- **No citation was added or changed by pass 2.** The gate total is unchanged at 743/666/77, and the
  two `spec-027 Decision 9` refs plus the one `utils/inputs.py::_safe_import` ref are the same three I
  verified in pass 1: correct card (`027` is the filters card, so the `spec-021` renumber trap is not
  tripped), `### Decision 9` still unique in the spec, no `#"substring"` form anywhere in the diff, and
  each citation entirely on one line so none is the wrap-invisible shape.
- **No process provenance.** `git diff -U0 | grep '^+' | grep -cEi 'round|slice|pass [0-9]|review|finding|worker|cycle'`
  over both files = **0**. The pass-2 report discusses rounds and passes at length, which is correct —
  that belongs in the artifact and is banned only from `.py`.

### Ownership partition

Re-derived from `git status --porcelain`. Only `tests/test_registry.py` changed in this pass; the site-1
docstring is the only hunk, and its inline comment plus the whole of `tests/filters/test_inputs.py` are
byte-identical to what I accepted in pass 1. The tree has grown by a concurrent spec-028 session's
files (`docs/SPECS/spec-028-orders-0_0_8.md`, `docs/SPECS/appx/spec-028-orders-0_0_8-rationale.md`,
`docs/builder/bld-slice-1-028-rationale_extraction.md`, `build-028-orders-0_0_8.md`) and by Worker 1's
spec-027 round; none was touched or reverted by me. No production file, no spec file, no other card's
test file was written by this cohort. `HEAD` is still `5c6fdd71`.

The three untouched `test_registry.py` twins stay untouched, and my pass-1 judgement stands with one
addition: I re-read all three, and both the connection twin (`:1691`) and the relay twin (`:1725`)
assert a "cycle-safe local import" in `clear()` and a "block" for `clear()` to skip, which the AST
measurement above shows does not exist. They are genuine members of the 051 population, exactly as
routed — which is what makes the Medium's item-4 understatement worth fixing rather than tolerating.

### What looks solid

- **The Medium fix is better than what I asked for.** I said the summary line could stand; scoping it
  with `itself` removes the last unqualified reading, and "That replay is the only place a poisoned
  ``sys.modules`` can be reached at all" keeps the protective fact the false sentence was reaching for
  without denying the route exists. Both halves survive the strongest test I could build for them.
- **The three-state table is the right instrument for this defect**, and the report reached it by
  auditing its *own* probe rather than by defending it. The recorded lesson — "a probe that measures
  the absence of something must first establish that the thing had a chance to be present" — is the
  same failure shape as the Medium itself, one layer out, and naming it is worth more than the fix.
- **Every Low was closed by retraction with a re-derived measurement**, not by rewording. L2's closure
  volunteers a defect I missed (the 3 + 1 split framing).
- **The C5 case was adopted rather than argued with**, and adopting it produced a checkable
  cross-instrument agreement on index 7185.
- **Nothing was smuggled in.** One hunk, one file, prose only, and `tests/filters/test_inputs.py` left
  alone precisely because the review had accepted it.

### Temp test verification

- No temp test under `docs/builder/temp-tests/`. Four throwaway files in the review scratchpad outside
  the repo, all carrying `027`: `rev027/w3_tokens_027.py` (instrument) with challenge copies
  `d1.py`-`d5.py`, `rev027/probe_027_clearpath.py` (round-1 import spy), `rev027/probe_027_liveness.py`
  (re-run this round), and `rev027/probe_027_r2_allstates.py` (new: full-package load, AST import-node
  scan, and the forced-`ImportError` clear).
- Disposition: none is a promotion candidate. Each monkeypatches an in-process seam, which `AGENTS.md`
  rule 10 permits only where the real path is impossible, and the two permanent rows already pin the
  contracts. They close with the cycle.

### Notes for Worker 1 (spec reconciliation)

1. **Escalated: the `### Deferred items this cohort owns` list needs three edits before it is homed
   into `bld-final-027.md`'s catalog.** Full measurements in the Medium above. Items 5 and 6 are
   DISCHARGED (by your Decision 9 edit and Worker 0's plan correction respectively) and item 4
   understates its own surface by three defects. Resolution paths: **(a)** you annotate the three items
   during final verification, since you hold the authoritative spec state and own the homing — my
   preferred path, and the reason this is escalated rather than re-looped; **(b)** re-loop Worker 2 for
   an annotation-only pass, which races your in-flight spec round for item 5's status; **(c)** home the
   list as-is and correct it in `bld-final-027.md`, which leaves this artifact wrong on disk. Nothing
   in the source depends on the choice.
2. **Your Decision 9 correction is confirmed landed and correct.** Re-derived: `delattr` now appears
   once in the spec, in the negation, under a bullet titled "no clear path strips them"; the ledger
   bullet now states "Both submodule lookups the clear needs are best-effort", which matches site 2's
   docstring and `utils/inputs.py::clear_generated_input_namespace` exactly. Both docstring citations
   of Decision 9 now resolve to true text. Pass 1's escalation is closed.
3. **Escalation 3 from pass 1 (no durable home for this cohort's deferrals) is discharged in form** —
   the report now carries the explicit list — **and open in substance** until item 1 above is settled
   and the list is actually homed. `bld-final-027.md` is dirty in your hands right now, which is the
   moment to do it.
4. **No new spec issue surfaced by this review.** I read `spec-027` only to check the two citations and
   your Decision 9 edit, and edited nothing.

### Review outcome

`review-accepted`, with one Medium transparently escalated to Worker 1 per `worker-3.md`'s escalation
clause.

The pass-1 Medium is genuinely closed: the new sentence is true in all three process states the report
names and in a fourth it did not — every subsystem loaded, every import on the replay forced to fail,
`clear()` still not raising — and the docstring and inline comment now agree in scope and mechanism.
The two sites stay deliberately distinct, with both rows re-proved live and failing for different
reasons. All four Lows are closed by retraction with re-derived measurements, and no closure introduced
a new inaccuracy. The token-identity verdict was re-established on the changed bytes rather than
carried over, on an instrument re-challenged in five directions including two the round-1 challenge did
not cover, and it agrees with Worker 2's instrument on the divergence *index*.

The one open item is a deferred-catalog accuracy problem whose resolution needs the authoritative spec
state Worker 2 cannot supply while that spec is mid-edit, and whose consumer — the homing into
`bld-final-027.md` — is Worker 1's own next action. Holding the artifact at `revision-needed` for it
would send a builder to re-annotate a list against a moving target; the escalation puts it in front of
the only worker who can settle it correctly. Nothing in the source is wrong.

---

## Post-acceptance corrections (Worker 2)

**Not a new build pass, and it moves nothing in source.** No `.py` file is touched, so the
token-identity proof stands as recorded in pass 2 and was not re-run. `Status:` stays
`review-accepted`; the three items below are corrections to this artifact's own record, which
[`bld-final-027.md`][final] now reads from. Prior sections are left intact per
[`ARTIFACT.md`][artifact] `## Re-pass sections`; this section supersedes the passages it names.

### C1 — the process-state table was under-specified, and the fix is a row, not a word

Worker 3 recorded a Low against pass 2's row 3, reading "evicted" where it judged the measured cause
to be "never imported". **Verified before rewording rather than swapping the word.** The verification
splits the finding in two, and both halves matter:

- **"evicted" was accurate for what pass 2's probe measured.** That probe's row-3 branch is
  `sys.modules.pop(name, None)`, and the same run printed
  `already cached in THIS process: {factories: True, sets: True}` — the targets were present and the
  probe removed them. Eviction is what produced the row. On this half the Low does not hold.
- **But it points at a real gap, and a larger one than a wrong word.** Eviction is *artificial*. Asked
  which state is naturally reachable, a controlled process answers: importing
  `django_strawberry_framework.filters.inputs` alone leaves `filters.sets` present and
  `filters.factories` **absent** — never imported, because `filters/inputs.py` names both as *strings*
  passed to `make_set_input_namespace` and imports neither.

```text
before importing filters.inputs:  factories=False  sets=False
after  importing filters.inputs:  factories=False  sets=True
```

So the naturally-reachable state raises on **one** of the two lookups, and pass 2's row 3 ("2
attempted, both raise internally") described only the artificial one. Re-measured **through the real
clear path** — `<scratchpad>/row3_states.py`, one controlled subprocess per state, spying
`importlib.import_module` and counting which calls raised:

| Process state | registered callbacks | targets in `sys.modules` | lookups attempted | raised internally | `clear()` raised |
|---|---|---|---|---|---|
| filter subsystem never imported | **8** | neither | **0** | 0 | no |
| `filters.inputs` imported, nothing forced — **the natural state** | 10 | `sets` only | 2 | **1** (`factories`) | no |
| both targets forced present | 10 | both | 2 | 0 | no |
| both targets evicted | 10 | neither | 2 | **2** | no |

Three things this measurement establishes that pass 2's three-row table did not:

- **The natural state is the mixed one**, and it was missing entirely. A table whose only
  raising row required an artificial `pop` invites the reading that the guard is exercised only under
  test manipulation. It is exercised by an ordinary import order.
- **The registered-callback count itself moves** (8 vs 10), which is the laziness property
  `spec-027 Decision 9` states, measured rather than quoted.
- **The load-bearing clause holds in all four rows.** `clear()` raised in none of them, and the
  docstring's "every submodule lookup it makes is best-effort" is true across 0, 1, and 2 internal
  raises. Worker 3's higher-load re-test (17 callbacks, every import forced to raise, 4 attempted
  lookups, no raise) extends the same result further; these four rows and that one agree.

**No source change follows.** The shipped docstring never claimed a count — it says the lookups are
best-effort, which is exactly the invariant that survives all four rows. Had the docstring asserted
"both lookups raise", this would have been a second Medium rather than a table correction, which is
the argument for keeping load-bearing prose quantifier-free.

### C2 — two deferred items are discharged

Both are marked rather than deleted: a deferral that was live and got closed tells the next reader
more than a gap does. Verified independently, not accepted on report.

**Item 5 — `spec-027` `### Decision 9`'s `delattr` bullet: DISCHARGED by Worker 1.**
`grep -c delattr docs/SPECS/spec-027-filters-0_0_8.md` returns **1**, at line 672, and that single
occurrence is now the **negation** — the bullet is titled "Materialized class objects stay parked in
the `django_strawberry_framework.filters.inputs` module `__dict__`; **no clear path strips them**",
and `delattr` survives only inside the reason for *not* doing it ("Stripping a global with `delattr`
would break any `strawberry.lazy(...)` LazyType held by a consumer module whose autouse-reload fixture
did not also reload the holder"). Pass 1's stated consequence — that a reader following either
docstring's `Decision 9` citation lands on a false bullet — **is no longer true.**

Better than discharged, for this cohort specifically: Decision 9's `registry.clear()` bullet now also
carries "Both submodule lookups the clear needs are best-effort: an unimportable `filters.factories`
or `filters.sets` skips only its own dependent reset and never prevents the reachable ledger reset."
That is site 2's corrected docstring, in the spec's own words, so the citation added by this cohort
now resolves to text stating the same contract — the property pass 1 could only claim for site 1.

**Item 6 — the plan's post-table sentence: DISCHARGED by Worker 0.**
`grep -c 'Site 1 pins that \`clear()\` imports nothing' docs/builder/build-027-filters-0_0_8.md`
returns **0**. Line 185 now reads "Site 1 pins that `clear()`'s **own body** imports nothing", with the
probe measurement attached inline (the 2 calls, both module names, the route through the replayed
callback) and the unqualified form explicitly marked FALSE. The recommended replacement wording is in
effect.

Items 1-4 of `### Deferred items this cohort owns` remain **live** and unchanged in ownership; item 4's
description is sharpened below.

### C3 — item 4 sharpened: the orders twin carries three defect classes, not one

Worker 0 flagged pass 2's item 4 as understated, for awareness. Re-derived read-only rather than taken
on say-so; `tests/orders/test_inputs.py` was **not** modified and is not in this cohort's writable set.
The row is `tests/orders/test_inputs.py::test_clear_order_input_namespace_tolerates_unimportable_submodules`,
at line **903**. Its docstring:

```text
"""Closes ``inputs.py:461-462`` and ``inputs.py:476-477`` in ONE test.

Mirror of
``tests/filters/test_inputs.py::test_clear_filter_input_namespace_tolerates_unimportable_submodules``
(lines 1009-1028). Setting ``sys.modules[name] = None`` makes
``from ... import ...`` raise ``ImportError``, exercising BOTH
``except ImportError: pass`` guards in ``clear_order_input_namespace``.
"""
```

Measured against `HEAD`, it is a member of three classes at once, which is why pass 2's "site 2's twin,
Low stale-spelling" framing was too clean:

1. **Rule-27 violation (Slice 2's D13 class).** Three raw `path:NN` refs in a docstring —
   `inputs.py:461-462`, `inputs.py:476-477`, `lines 1009-1028`. `AGENTS.md` rule 27 permits raw
   `path:NN` only in per-cycle scratchpad artifacts, "never in code comments specs or standing docs".
   Slice 2 swept this class but swept `tests/filters/test_inputs.py`, not `tests/orders/test_inputs.py`
   — so this is a **missed member of a class this cycle already closed elsewhere**, not new work.
2. **Site 1's misattribution shape, not site 2's.** It places "BOTH ``except ImportError: pass``
   guards" **in ``clear_order_input_namespace``**;
   `grep -c 'except ImportError' django_strawberry_framework/orders/inputs.py` returns **0**. Naming
   guards inside a function that has none is exactly what site 1's docstring did, so the row needs
   site 1's *kind* of repair on this clause and site 2's on the `from ... import ...` spelling.
3. **A rotted cross-reference range.** It cites the filter twin at "lines 1009-1028"; that function is
   at `tests/filters/test_inputs.py:1417`. The symbol-qualified half of the reference is correct and
   survived, which is the argument for rule 27's form — the same reference carries one half that
   still resolves and one that does not.

Consequence for routing, and the reason this is worth the words: **whoever takes
`TODO-ALPHA-051-0.0.15` cannot repair this row by copying either corrected docstring.** It needs site
1's treatment for clause 2, site 2's for the spelling, and a rule-27 rewrite for the three raw
refs — and the `lines 1009-1028` range must not simply be renumbered to `1417`, since a raw line
number is the defect. Worker 1 owns the catalog entry; this is the measurement behind it.

The "3 + 1" split recorded in pass 2 and in the plan is therefore **too clean in both documents**. The
accurate split is: three `test_registry.py` twins stale by site 1's proof, and one `tests/orders/`
twin carrying a union of both proofs plus a rule-27 violation.

### Validation run

No `.py` file changed, so no source gate applies and the token-identity proof was not re-run (pass 2's
verdicts stand, and re-running it would compare identical inputs).

| Check | Command | Result |
|---|---|---|
| Citation gate | `uv run python scripts/check_citations.py` | `OK: 743 citations resolve (666 in 422 .py files, 77 in KANBAN.md).` exit 0 — unchanged from pass 2; this section adds no `path::Symbol` citation to any `.py` file |
| Source layout / md scaffold | `uvx pre-commit run --files <this artifact> tests/test_registry.py tests/filters/test_inputs.py` | all five hooks **Passed** |
| Whitespace / conflict markers | `git diff --check` | exit 0, no output |
| Churn | `git status --porcelain` | this artifact only; the concurrent `spec-028` session's paths were left alone |
| State measurement | `uv run python <scratchpad>/row3_states.py {never_imported,natural,cached,evicted}` | four runs, output tabulated under C1 |

### Notes for Worker 1 (spec reconciliation)

1. **Item 5 is closed on your edit and the closure is verified above** — one `delattr` occurrence, and
   it is the negation. Both of this cohort's `Decision 9` citations now resolve to text that states
   the contract they claim, site 2's included.
2. **C3 is the measurement behind the catalog entry you own.** The `3 + 1` framing understates the
   orders twin; the corrected description is in C3, and its practical consequence is that the row
   cannot be repaired by copying either docstring this cohort landed.
3. **No spec file was read for edit or touched by this section.** No new spec issue surfaced.

---

## Final verification (Worker 1)

Every claim below was re-derived from the working tree in this pass. Worker 2's and Worker 3's accounts were read for context and treated as hypotheses, not evidence — the cohort's own history is why: its round-1 repair installed a fresh false claim, and a pass that trusts the report cannot catch that class.

- **Dispatched findings checklist: four boxes, all `- [x]`, all audited against the files.** Box 1 (site 1 docstring) and box 2 (site 1 inline comment) landed — the docstring now opens "``clear()`` itself imports nothing, so a broken ``sys.modules`` cannot break it" and the comment states the poisoning "can only reach a replayed callback's own best-effort lookup, which skips rather than propagates". Box 3 (site 2 docstring + comment) landed — the docstring now attributes the guards to `utils/inputs.py::_safe_import` rather than to the local function, and the comment says the lookups "raise ImportError internally". Box 4 is a **deliberate no-change with recorded reasoning**, and the reasoning verifies: the banner `clear_filter_input_namespace - cycle-safe import guards` names the subject and the property under test without locating the guards, so it is accurate at `HEAD`. No box is over-ticked and none is silently un-ticked.
- **Both docstrings are true claim by claim, and the two contracts have not drifted into each other.** Site 1's four factual claims re-derived: `TypeRegistry.clear` (lines 580-607) contains **0** `Import` / `ImportFrom` nodes by AST, and so does `_run_type_teardowns` (270-282), the only helper it calls — so "`clear()` itself imports nothing" holds for the whole call, not just the body's first level; `_clear_if_importable` is reached from `unregister`, never from `clear`; the replay is therefore the only route a poisoned `sys.modules` can reach; and **every** registered teardown callback is import-free — an AST scan of all 19 `register_subsystem_clear` sites' callbacks returns **0** functions containing an `import` statement, so every module lookup on the replay path runs through `utils/imports.py::import_attr_if_importable`'s `try` / `except ImportError: return None`. Site 2's claims re-derived: the substrate makes exactly two lookups, both via `utils/inputs.py::_safe_import`, and `clear_generated_input_namespace` empties the ledger and the field-spec table **before** either lookup, which is what makes "the reachable ledger reset still completes" true. **Neither docstring states the other's property**: site 1 never locates a guard, site 2 never claims the clear entry point imports nothing.
- **The state-dependence measurement, re-derived in a clean subprocess rather than accepted.** `filters/inputs.py` passes `filters.factories` and `filters.sets` to `make_set_input_namespace` as strings and imports neither, so the natural state after importing `filters.inputs` is `factories=False sets=True` — two lookups attempted, **one** raising internally. Confirmed, and then extended across all four states: for `(factories, sets)` in `(F,F) (F,T) (T,F) (T,T)`, both `clear_filter_input_namespace()` and `registry.clear()` complete without raising in every one. **No quantifier crept into site 1's prose**: it says "every submodule lookup it makes is best-effort" — a universal over lookups, asserting no count of lookups or of raises — so it is state-independent by construction. Site 2's "Both submodule lookups on the clear path are best-effort" counts *lookups*, which is a structural property of the substrate (always two) and not a count of failures; its inline comment's "exercising both skips" is scoped to the state the test forces, `(F,F)`. Both true in all four states.
- **Focused tests run, and they pass.** `uv run pytest --no-cov -q` over the two repaired tests plus the four that pin the contracts this cohort's spec edits describe (`test_clear_filter_input_namespace_can_be_called_directly`, `test_registry_clear_clears_filter_input_namespace_and_helper_set`, `test_materialize_input_class_is_idempotent_on_same_pair`, `test_materialize_input_class_rejects_collision_on_distinct_classes`): **6 passed in 2.95s**. No `--cov*` flag. The full three-tree sweep is Worker 0's and is not duplicated here.
- **Artifact integrity after three rewrites.** `## Post-acceptance corrections (Worker 2)` names each passage it supersedes (`pass 2's item 4`, `Item 5`, `Item 6`) and leaves prior sections intact, which is what [`ARTIFACT.md`][artifact] `## Re-pass sections` requires — "never edit prior entries" — so the pass-2 `### Deferred items this cohort owns` list reading as live at its own location is the convention operating, not a defect, and it is **not** annotated here for the same reason. Reference integrity: **0** undefined refs, **0** orphan definitions, and all six definitions resolve on disk, `[final]` included — the dangling ref Worker 2 self-reported is closed.
- **DRY across the cohort:** nothing to check. The cohort changed no executable token in any file, so no helper, literal, or near-copy could be introduced.
- **Spec reconciliation:** owed and discharged, in three rounds, all recorded under `### Spec changes made (Worker 1 only)` below and keyed to `### Decision 9` in [`spec-027-filters-0_0_8-rationale.md`][spec-027-rationale]. Re-read as one document, the five touched spec surfaces are internally consistent: no sentence anywhere still implies the ledger is filterset-keyed (`(name, filterset_class)` = **0** occurrences, `(name, input_class)` = **8**) or that a clear path strips a materialized global (the spec's single surviving `delattr`, line 672, is the negation). The three surviving `type[FilterSet]` spellings are the genuinely filterset-typed `_field_specs` key, the `_helper_referenced_filtersets` element type, and `filter_input_type`'s parameter — each matching its declaration in source.
- **Gates:** `check_citations.py` `OK: 743 citations resolve (666 in 422 .py files, 77 in KANBAN.md).`; `check_spec_glossary.py --spec docs/SPECS/spec-027-filters-0_0_8.md` `OK: 48 terms`; `check_trailing_commas.py --check` on the spec pair, exit 0.
- **Floor verification:** `No floor-verification scope declared.`
- **Final status: `final-accepted`.**

### Summary

The cohort corrected two `.py` test docstrings that described a mechanism the package does not have, and it cost three rounds to get right because each round's *description* of the finding was wrong in a way the round could not see: round 1 misgraded site 2 and installed a fresh false claim at site 1; round 2 mis-scoped the ledger-spelling population; round 3 understated the orders twin to a wording fix. The shipped result changes **no executable token** in any file, and the two tests still pin different properties on purpose — site 1 that `clear()` runs no import, site 2 that the substrate's two lookups tolerate an unimportable submodule. Four items are homed on `bld-final-027.md`'s catalog as items 18-21, two of the cohort's own deferrals are recorded there as discharged, and one residual is left knowingly: the `TODO-ALPHA-051-0.0.15` cluster in `tests/orders/test_inputs.py`, which is spec-028's surface and outside this cycle's fence.

### Spec changes made (Worker 1 only)

All in `docs/SPECS/spec-027-filters-0_0_8.md`, with the reasoning keyed to `### Decision 9` under `## Post-final residual cohort — the clear path` in [`spec-027-filters-0_0_8-rationale.md`][spec-027-rationale]. No `.py` file was touched by any of them.

1. **The clear-path mechanism claim, three surfaces** (`### Decision 9`'s lifecycle bullet, now lines 671-672; `## Edge cases and constraints` line 841; `## Test plan` line 856). The spec pinned `delattr` on the clear path; the code deliberately parks materialized classes because stripping one would break a held `strawberry.lazy(...)` LazyType. The lifecycle bullet became two — what the clear resets, and why parking is load-bearing — and the clear's under-enumeration was closed in the same edit (`_field_specs`, the `FilterArgumentsFactory` caches, and each subclass's `_lifecycle.binding_attrs`, cited to `sets_mixins.py::SetLifecycleAttrs.binding_attrs` so a new binding slot cannot rot the spec).
2. **The ledger-keying claim, ten sentences across five surfaces** (`## Slice checklist` line 59; `### Decision 9` lines 663, 669, 670, 700; `## Edge cases and constraints` lines 835, 841; `## Test plan` lines 856, 860; closing summary item 6, line 977). `dict[str, type[FilterSet]]` / `class_name → filterset_class` / `(name, filterset_class)` were the wrong type: the ledger stores the materialized input class and idempotency is `is` identity on it. The worked example's `cls_a` / `cls_b` were part of the defect and are now `input_a` / `input_b`. Observable behavior is unchanged and the corrected text says why — input-class names are `FilterSet`-derived, so two same-`__name__` filtersets still collide.
3. **The `## Test plan` coverage mis-attribution** (lines 856, 860). `materialize_input_class` and the clear-lifecycle clauses were attributed to `tests/filters/test_inputs.py`, which contains **0** occurrences of that symbol against `test_finalizer.py`'s **11**. All four clauses moved to the `test_finalizer.py` bullet, named by test; `test_inputs.py`'s bullet now claims the one thing it does own, `::test_clear_filter_input_namespace_tolerates_unimportable_submodules`. The other eight symbols and all nine named tests in that bullet were re-measured and are correctly placed.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

[spec-027-rationale]: ../SPECS/appx/spec-027-filters-0_0_8-rationale.md

<!-- docs/builder/ -->

[artifact]: ARTIFACT.md
[build]: BUILD.md
[final]: bld-final-027.md
[plan]: build-027-filters-0_0_8.md
[slice4]: bld-slice-4-027-broken_substring_citations.md
[w2]: worker-2.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
