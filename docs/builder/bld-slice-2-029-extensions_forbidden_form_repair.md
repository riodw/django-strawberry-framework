# Build: Slice 2 — `extensions=` forbidden-form regression repair + standing governance pin

Spec reference: `docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md` (Decision 3 at `:264-283`; `## Slice checklist` Slice 1 at `:55-58`; `## Definition of done` items 2-4 at `:521-523`)
Status: final-accepted

## Plan (Worker 1)

### Preamble — declarations carried from the build plan

**Hot-path declaration** (copied as written from `docs/builder/build-029-consumer_dx_cleanup-0_0_9.md` `## Hot-path declaration`):

> **Slice 2 — declared hot-path-adjacent, number required.** Its whole subject is the optimizer's per-request plan-cache lifecycle. The change is confined to test-file schema construction (no production line changes), so the metric is not wall-clock: **Worker 2 records, for at least one migrated site per form, the `DjangoOptimizerExtension.cache_info()` reading before and after the migration across two executions of the same query on one schema** — the direct observation that the bare class / constructing `lambda` yields `misses=2, hits=0` (a fresh instance per request) and the singleton-factory yields `misses=1, hits=1`. That number IS the proof the repair is a repair. Slices 1, 3, integration, and final: `none` (documentation and artifacts only).

**Floor-verification scope** (copied as written from the same plan's `## Floor-verification scope`):

> - **Slice 2 — required. Owning pass: Worker 2's build pass.** It touches a Strawberry integration seam (`Schema(extensions=...)` construction and the per-request `get_extensions` contract). Focused scope at the floor: the six test files it edits. Floor per `BUILD.md` `## Floor verification`: **Django 5.2.16, Python 3.10, strawberry-graphql 0.316.0**, built in a scratch venv **outside** the repo (`uv venv /tmp/dsf-floor-029 --python 3.10`; install with an explicit `--python`; never mutate the shared `.venv`). Record the resolved `uv pip list --python /tmp/dsf-floor-029/bin/python` output and each focused command's pass/fail. The floor is the version the spec's own Decision 3 was derived against, so it is the version that must confirm the repair.
> - Slices 1, 3, integration: `none` (no framework surface).
> - Final gate: confirms Slice 2's floor run happened and was recorded; it does not own it.

**Worker 1's amendment to the floor scope.** "the six test files it edits" was written against Worker 0's twelve-site hypothesis. The re-derived population (below) is **25 sites in 8 files**, and one of them is not a test file. The floor scope is therefore the eight edited files plus `tests/test_ci_governance.py`, plus the two readers of the one non-test file changed (`examples/fakeshop/strategy_schemas.py::build_strategy_schema`): `examples/fakeshop/test_query/test_optimizer_auto_api.py` and `tests/test_lateral_pg_parity.py`. Everything else in the declaration — the floor versions, the scratch venv outside the repo, the never-mutate-`.venv` rule, the owning pass, and the recording obligation — stands exactly as written.

**Coverage.** No `--cov*` flag in any command of this slice. `--no-cov` only (`pytest.ini`'s `addopts` auto-applies `--cov`).

---

### Mechanism re-derivation at HEAD (performed by Worker 1, not taken from the plan or the spec)

The spec pins every mechanism claim to strawberry-graphql `0.316.0`. Re-derived against what the shared environment actually resolves today, read rather than remembered:

```
$ uv pip list | grep -iE '^(strawberry-graphql|django) '
django                      6.1
strawberry-graphql          0.323.2
$ .venv/bin/python -V
Python 3.14.2
```

`.venv/lib/python3.14/site-packages/strawberry/schema/schema.py::Schema.get_extensions` at 0.323.2:

```python
resolved: list[SchemaExtension] = [
    ext if isinstance(ext, SchemaExtension) else ext()
    for ext in self.extensions
]
```

Its two callers are `Schema.execute` (`schema.py:747`) and `Schema.execute_sync` (`schema.py:821`) — **per operation, both modes**, exactly as the spec describes for 0.316.0. `Schema.__init__` (`schema.py:319-333`) still materializes `self.extensions = tuple(extensions)` and emits the `DeprecationWarning` only when `any(isinstance(ext, SchemaExtension) for ext in self.extensions)`.

So, unchanged at HEAD: a **bare class** and a **constructing `lambda`** are both re-invoked per operation and yield a fresh instance each time; a **`lambda` closing over a singleton** returns the same object every time and trips no deprecation check. **This is a genuine regression repair, not a stale-contract relaxation.** The claim now holds at both ends of the supported range once Worker 2's floor run executes the migrated files at 0.316.0.

The instance-bound state is real, not inferred: `django_strawberry_framework/optimizer/extension.py::DjangoOptimizerExtension.__init__` sets `self._plan_cache` (`extension.py:939`) and `::DjangoOptimizerExtension.cache_info` reports `size=len(self._plan_cache)` (`extension.py:956-971`). A fresh instance per operation is a cold cache with a structurally zero hit rate.

### Scope boundary — why the finding is the optimizer and nothing else

A bare-class entry is **not** automatically a violation. The boundary was established from source, not from the prompt:

| Extension | Bare class in `extensions=[...]` | Established at |
|---|---|---|
| `DjangoOptimizerExtension` | **forbidden** — carries the cross-request `self._plan_cache` | `optimizer/extension.py:939` + `:956-971` |
| `DjangoDebugExtension` | **required** — "Opt-in is the **class** … per-operation capture state lives in plain instance attributes … Never pass a pre-built instance" | `extensions/debug.py:525-538` |
| `DjangoErrorPolicyExtension` | **fine** — "this extension holds no configuration of its own, so a bare class entry and a factory entry behave identically" | `extensions/error_policy.py:280-283` |
| consumer test extensions (`_FirstProbe`, `_CountingDebug`, `RecordingExtension`, …) | **fine** — stateless per operation | `tests/extensions/test_debug.py`, `tests/test_routers.py` |

A census of every element appearing in an `extensions=` sequence across the tree confirms the size of the over-report a `extensions=[`-vocabulary sweep would produce: 14 bare `DjangoDebugExtension`, ~20 bare consumer-extension classes and named factories, and 66 already-correct `lambda: ext` entries — **none** of which is a violation. Scoping to `DjangoOptimizerExtension` is what makes the finding true.

### Population re-derivation — the finding is 25 sites in 8 files, not 12 in 6

Worker 0's hypothesis listed 12 sites in 6 files. **It is a subset.** The list was assembled with the vocabulary `DoD item 4` itself uses — the literal spelling `lambda: DjangoOptimizerExtension()` — so every `strictness=` / `nested_connection_strategy=` variant of the same form fell outside the grep. This is the standing "a grep phrase samples a claim's vocabulary rather than establishing its population" failure (`BUILD.md` `## Claims are proven mechanically, never accepted on prose`).

The expansion is licensed by the spec's own normative text, not only by the mechanism. The `## Slice checklist` Slice 1 sub-bullet (`:56`) reads: *"Do NOT use the bare class or a constructing-`lambda` `lambda: DjangoOptimizerExtension()` (re-instantiated per request → cold cache, both modes, and a cache-hit-test failure)."* The rule is stated by **form**; the parenthetical is one spelling of it.

**Instrument.** An AST classifier, not a grep — the forms wrap across lines, carry arbitrary keyword arguments, and appear inside conditional expressions. Two rules, over the four first-party source trees (`django_strawberry_framework`, `tests`, `examples`, `scripts` — the definition `scripts/check_citations.py::SOURCE_TREES` already uses, which excludes `.venv` and the gitignored `docs/*/temp-tests/` scratch by construction):

1. any `ast.Lambda` whose body is a `Call` constructing `DjangoOptimizerExtension`;
2. any bare `DjangoOptimizerExtension` `Name`/`Attribute` load that is an **element of a list or tuple literal** and is not the `func` of a `Call`.

```python
import ast
from pathlib import Path

TARGET = "DjangoOptimizerExtension"
SOURCE_TREES = ("django_strawberry_framework", "tests", "examples", "scripts")


def forbidden_entries(source, label):
    """Yield (lineno, form, snippet) for each forbidden optimizer extensions entry."""
    tree = ast.parse(source)
    call_funcs = {id(n.func) for n in ast.walk(tree) if isinstance(n, ast.Call)}
    sequence_elements = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.List, ast.Tuple)):
            sequence_elements.update(id(element) for element in node.elts)
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Lambda):
            body = node.body
            if isinstance(body, ast.Call) and TARGET in ast.unparse(body.func):
                found.append((node.lineno, "constructing lambda", ast.unparse(node)))
        if (
            isinstance(node, ast.Name)
            and node.id == TARGET
            and isinstance(node.ctx, ast.Load)
            and id(node) not in call_funcs
            and id(node) in sequence_elements
        ):
            found.append((node.lineno, "bare class in a sequence", TARGET))
    return sorted(found)
```

**The instrument was controlled in both directions before its reading was believed** — 9 must-flag snippets (bare single / tuple / multi-element / multiline / assigned-to-a-variable; constructing lambda with no args, with kwargs, inside a conditional expression, dotted) and 9 must-not-flag snippets (`lambda: ext`, `lambda: _optimizer`, bare `DjangoDebugExtension`, bare `DjangoErrorPolicyExtension`, `lambda: DjangoDebugExtension(allow_unsafe_production=True)`, `class _CaptureExt(DjangoOptimizerExtension)`, `DjangoOptimizerExtension.check_schema(schema)`, `assert DjangoOptimizerExtension is Other`, a bare instance assignment). **18/18, zero control failures.** A control that did not run reads identically to a passing proof, so the control set is not optional here — it becomes the pin's own test rows (below).

Cross-check on the bare-class rule's precision: an exhaustive sweep of *every* non-call `DjangoOptimizerExtension` reference in the four trees returns **52** — 7 of them elements of a sequence literal (the 7 below), and the other 45 are `check_schema(...)` / `_build_cache_key(...)` / `_stash_union(...)` classmethod calls, `class _CaptureExt(DjangoOptimizerExtension)` subclassing, and one `is`-identity assertion. The sequence-literal qualifier is what turns a 52-site over-report into the 7 real ones.

**The population (line numbers pinned at write time — re-derive before editing):**

| File | Line | Form | Current source |
|---|---|---|---|
| `examples/fakeshop/strategy_schemas.py` | 65 | constructing lambda | `lambda: DjangoOptimizerExtension(nested_connection_strategy=strategy)` |
| `examples/fakeshop/test_query/test_products_visibility_api.py` | 160 | bare class | `strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension])` |
| `examples/fakeshop/test_query/test_products_visibility_api.py` | 192 | bare class | same |
| `tests/forms/test_resolvers.py` | 123 | bare class | `extensions=[DjangoOptimizerExtension],` |
| `tests/mutations/test_resolvers.py` | 107 | bare class | same |
| `tests/mutations/test_resolvers.py` | 970 | bare class | same |
| `tests/mutations/test_write_transaction.py` | 180 | bare class | same |
| `tests/optimizer/test_extension.py` | 5386 | constructing lambda | `lambda: DjangoOptimizerExtension(strictness="raise")` |
| `tests/optimizer/test_extension.py` | 5448 | constructing lambda | same |
| `tests/optimizer/test_extension.py` | 5502 | constructing lambda | same |
| `tests/optimizer/test_extension.py` | 5550 | constructing lambda | same |
| `tests/optimizer/test_extension.py` | 5600 | constructing lambda | same |
| `tests/optimizer/test_extension.py` | 5608 | constructing lambda | `lambda: DjangoOptimizerExtension(strictness="off")` |
| `tests/optimizer/test_extension.py` | 5648 | constructing lambda | `lambda: DjangoOptimizerExtension(strictness="raise")` |
| `tests/test_relay_connection.py` | 1030 | constructing lambda | `lambda: DjangoOptimizerExtension(strictness=strictness)` (conditional) |
| `tests/test_relay_connection.py` | 1074 | constructing lambda | `lambda: DjangoOptimizerExtension(strictness=strictness)` |
| `tests/test_relay_connection.py` | 1109 | constructing lambda | `lambda: DjangoOptimizerExtension(strictness=strictness)` (conditional) |
| `tests/test_relay_connection.py` | 1497 | constructing lambda | `lambda: DjangoOptimizerExtension()` (conditional) |
| `tests/test_relay_connection.py` | 1696 | constructing lambda | `lambda: DjangoOptimizerExtension()` (conditional) |
| `tests/test_relay_connection.py` | 1830 | constructing lambda | `lambda: DjangoOptimizerExtension()` |
| `tests/test_relay_connection.py` | 2170 | constructing lambda | `lambda: DjangoOptimizerExtension()` |
| `tests/test_relay_connection.py` | 2274 | constructing lambda | `lambda: DjangoOptimizerExtension()` |
| `tests/test_relay_connection.py` | 2507 | constructing lambda | `lambda: DjangoOptimizerExtension(strictness="raise")` |
| `tests/test_relay_connection.py` | 2801 | constructing lambda | `lambda: DjangoOptimizerExtension(strictness=strictness)` |
| `tests/types/test_resolvers.py` | 169 | bare class | `extensions=[DjangoOptimizerExtension],` |

7 bare-class + 18 constructing-lambda = **25**, in 8 files. Two of those files are absent from Worker 0's hypothesis and from the build plan's ownership table — see the amendment request below.

**Not in the population, and deliberately so:** `docs/bug_hunt/temp-tests/resolvers_async_parity/*.py` carries 2 bare-class and 2 constructing-lambda entries. `.gitignore:202` ignores `docs/bug_hunt/temp-tests/`, so it is untracked scratch, not active source, and it lies outside all four `SOURCE_TREES`. Neither the repair nor the pin reaches it — and that is the correct answer, not an omission: a pin that walked the filesystem indiscriminately would pass in a clean CI checkout and fail on a developer machine holding scratch, which is an environment-dependent gate.

Also clean at HEAD, re-derived rather than assumed: the **deprecated instance form** (`extensions=[DjangoOptimizerExtension()]`, `ext = …; extensions=[ext]`, `extensions=[_CaptureExt()]`) has **zero** occurrences in the four trees. Every element the census found is a lambda, a class, or a named factory function. Only forms A and B regressed.

### Ownership-partition amendment required (Worker 0 — before dispatching Worker 2)

`BUILD.md` `### Parallel cohorts under a declared ownership partition`: a cohort that needs to write a file it does not own is a mid-flight collision Worker 0 resolves and records in the plan. Slice 2's writable-file list must gain two files:

- **`tests/optimizer/test_extension.py`** — 7 constructing-lambda sites.
- **`examples/fakeshop/strategy_schemas.py`** — 1 constructing-lambda site, plus the one docstring sentence it falsifies.

Both are `.py`, so both are inside the maintainer's fence (*spec files and `.py` files only*). Both are genuine violations of the same contract as the other 23, and `AGENTS.md` rule 4 forbids the defer-the-real-fix sequencing that leaving them would be. The only thing putting them out of reach is the plan's ownership table, which is Worker 0's to correct. **Worker 2 must not begin until the table is amended**; if it is dispatched against the un-amended table, that is a stop-and-report, not a silent widening.

### Slice-splitting answer (`BUILD.md` `### Slice splitting`)

**One unit.** Written out rather than assumed, and answered against a counted boundary estimate:

- **New boundaries: one.** The governance pin's classifier — the single thing in this slice whose job is to say "no". Everything else is behavior-preserving substitution.
- **The 25 site migrations owe no failability proof.** `BUILD.md` `### What needs a proof, and what does not`: renamed symbols, relocated bodies, added annotations, and refactors that move existing behavior need none. Each migration replaces one expression with an equivalent that resolves to the same extension object; it introduces no guard, no rejection path, and no invariant. **Worker 2 must not manufacture twenty-five proofs, and must not skip the one that is owed.**
- **Diff shape.** 25 two-to-four-line local edits plus ~70 lines in one test module. Large in site count, trivial in per-site depth, and uniform: one reviewer reading one shape 25 times, not 25 shapes. A split would cost an extra artifact and a full worker cycle to separate edits that share a single contract and a single verification (the pin's sweep is green only once *all* 25 have landed — splitting would leave the first sub-slice's pin red).
- **What makes them one decision:** the pin defines the population and the population defines the pin. Landing either half alone leaves the repo in a state neither half can verify.

### DRY analysis

**Helper inventory checked.** Refreshed **for the whole package** (`django_strawberry_framework/`, 1,941 lines, written to `docs/shadow/helper-inventory.md` on this pass, not reused from a prior one). Shapes searched: `extension`, `factory`, `singleton`, `source_tree`, `iter_python`, `sweep`, `scan`. Relevant candidates: **none.** The package exposes `DjangoConnectionField` (a field factory) and the three extension classes, and holds no extension-construction helper and no repository-scanning helper — correctly, since repository sweeps live in `scripts/`. Nothing in the package is reusable by this slice, and this slice adds nothing to it.

**Existing patterns reused.**

- **The singleton-factory literal itself is the established repo idiom, at ~75 already-correct sites.** The element census returns `lambda: ext` 66 times, `lambda: optimizer` 5, `lambda: _optimizer` 2, plus `lambda: capture_ext` / `lambda: cascading_ext` / `lambda: plain_ext` / `lambda: extension`. Canonical worked example: `tests/optimizer/test_extension.py::test_cache_hit_on_repeated_query` (`:991` declares `ext = DjangoOptimizerExtension()`, `:1000` passes `extensions=[lambda: ext]`, `:1004-1010` asserts `misses == 1` then `hits == 1`). Every repaired site adopts that exact shape.
- **The governance module's own idiom** (`tests/test_ci_governance.py`): a `REPO_ROOT` constant, module-level private `_helper()` collectors, `@pytest.mark.parametrize` over a collected corpus with readable `ids=`, one test per property, a docstring on each test saying *why the property is invisible to the rest of the suite*, and an assertion message naming the offending file and the fix. `::test_container_images_are_pinned_by_digest` is the closest structural precedent — it strips comments before matching precisely because it cares about false positives from prose.
- **`scripts/check_citations.py::SOURCE_TREES` / `::iter_python_sources`** is this repo's existing definition of "every first-party `.py` file". `tests/test_build_tree_md.py:5` already imports from `scripts.` in this suite, so the import path is proven. Reusing it is the decided answer over re-listing the trees: one definition of active source, and if it ever narrows, the pin narrows with it visibly rather than the two drifting apart. Worker 2 records the coupling in a comment at the import.

**New helpers justified.** Exactly one: a module-private classifier in `tests/test_ci_governance.py`, single responsibility *"given one module's source text, return every forbidden `DjangoOptimizerExtension` extensions entry in it"*. It takes **source text plus a label**, never a path — that is what lets the control rows feed it literal snippets, and the control rows are what pin it. Call sites: the repo-wide sweep test, and the parametrized control tests.

**Duplication risk avoided, and the shared-test-helper question answered explicitly.**

- **No shared `optimizer_factory()` test helper. Decided, not deferred.** It looks like the obvious win at 25 sites and is the wrong shape here, for four reasons: (1) it would make the 25 repaired sites read differently from the ~75 already-correct ones, so the file would carry two spellings of one idiom — the duplication would be *created* by the helper, not removed; (2) no importable home serves all three test trees without either widening the package's public surface (which `## Definition of done` forecloses) or planting a package-test helper inside `examples/`; (3) several sites need the instance *by name* (a strictness value per site, and the existing cache tests assert on `cache_info()`), so a helper returning only the callable would be bypassed exactly where the mechanism matters; (4) the two-line literal *is* the mechanism the spec mandates and the docs teach — hiding it behind a helper hides the thing the test is about. **The condition that would change this answer:** a site needing more than the instance-plus-lambda pair — a shared teardown, a cache-counter reset between tests, or an assertion helper over `cache_info()` used at three or more sites. None exists today.
- **No second enforcement mechanism.** Maintainer decision D1 already rejected a `scripts/` + pre-commit gate on placement; the pin lives only in `tests/test_ci_governance.py`. Worker 2 adds nothing to `scripts/`, `.pre-commit-config.yaml`, or CI.
- **No per-file copy of the classifier.** One function, two call sites.

### Implementation steps

Line numbers are pin-at-write-time navigational hints. Re-run the sweep above before editing; another session's pass may have shifted these files.

**Step 0 — re-derive the population.** Run the classifier over the four `SOURCE_TREES` and confirm the site table. If the count differs from 25, that is the finding: report it, do not quietly adopt either number.

**Step 1 — migrate the 25 sites.** Three shapes, all **function-local**. No site in this population is a one-schema-per-module case, so **no module-level singleton is introduced anywhere in this slice**: three of the sites sit inside module-level helper functions that build a *fresh schema per call* (`tests/mutations/test_resolvers.py::_schema`, `tests/mutations/test_write_transaction.py`'s schema builder, `tests/forms/test_resolvers.py`'s schema builder), and a module-level instance shared across every schema those helpers build would put unrelated schemas' plans in one cache.

*Shape S1 — unconditional site.* Declare the singleton in the smallest scope that encloses the `Schema(...)` call, immediately above it, carrying the **same constructor arguments the current expression carries**:

```python
optimizer = DjangoOptimizerExtension(strictness="raise")
schema = strawberry.Schema(
    query=Query,
    extensions=[lambda: optimizer],
)
```

*Shape S2 — conditional site* (`tests/test_relay_connection.py:1030, 1109, 1497, 1696`; `examples/fakeshop/strategy_schemas.py:65`). **The `else` branch must keep doing exactly what it does today: construct nothing.** A conditional expression that builds the instance unconditionally and only conditionally wraps it is a behavior change and is rejected:

```python
extensions = []
if optimizer:
    optimizer_ext = DjangoOptimizerExtension(strictness=strictness)
    extensions = [lambda: optimizer_ext]
```

Note the name: at four of these five sites the enclosing function already binds `optimizer` as the **boolean flag**, so the singleton takes a non-shadowing name. Check the enclosing scope before choosing one.

*Shape S3 — two schemas in one function* (`tests/optimizer/test_extension.py:5600` + `:5608`, one `strictness="raise"` and one `strictness="off"` in the same test). Two separately-named locals, one per schema. One instance cannot carry two strictness values, and this pair is the clearest live illustration of Decision 3's per-construction-site granularity.

**Step 2 — `examples/fakeshop/strategy_schemas.py::build_strategy_schema` also owes a docstring correction.** Its current docstring says the strategy is *"mounted on a fresh per-execution `DjangoOptimizerExtension`"* — a sentence the repair falsifies. Rewrite it to say the strategy is mounted on one `DjangoOptimizerExtension` per built schema, wrapped in a factory so `get_extensions` returns that same instance on every request. Only the function docstring changes; the **module** docstring is what `docs/TREE.md` renders and it stays untouched (`docs/TREE.md` is out of this cycle's fence and must not be regenerated).

**Step 3 — add the governance pin to `tests/test_ci_governance.py`.** Follow the module's existing idiom rather than inventing one:

1. Extend the **module docstring**. It currently scopes the file to `.github/` workflow YAML, and its "Coverage note" says the assertions target YAML rather than `django_strawberry_framework`. Both sentences become inaccurate the moment a Python-source pin lands. The coverage note's *conclusion* still holds — reading `.py` files adds no package coverage surface either — so widen the subject, keep the note.
2. Add the module-private classifier (see `### DRY analysis`), taking source text plus a label.
3. Add the repo-wide sweep test. Name it for the property, in the module's voice — e.g. `test_no_active_source_uses_a_forbidden_optimizer_extensions_form`. Its docstring states the two forbidden forms, *why* each is forbidden (both are re-invoked by `Schema.get_extensions` per operation, cold-caching the instance-bound plan cache), and the fix in one line (`ext = DjangoOptimizerExtension(...)` then `extensions=[lambda: ext]`). Its assertion message names the file, the line, and the offending snippet.
4. Add the **control rows** as parametrized tests over the 18 snippets listed under `### Population re-derivation`, split into a must-flag set and a must-not-flag set. These are what pin the classifier: they are the mechanism that makes the boundary strongly pinned and they are the durable form of the standing lesson that a sweep instrument dies silently on shape drift.
5. Scope the sweep with `scripts.check_citations.iter_python_sources()`, with a comment naming the coupling.

**Step 4 — deliberate non-extensions of the pin, recorded so a later reader knows they were considered.** Maintainer decision D1 names two forms; the pin implements those two and no more.

- The **deprecated instance form** (`extensions=[DjangoOptimizerExtension()]`) is not pinned. It is outside D1's wording, it has zero occurrences at HEAD, and `pytest.ini`'s `filterwarnings = error` already makes it fail every test that builds such a schema at runtime.
- A **subclass** entry (`extensions=[_CaptureExt]`) is not pinned. The classifier matches the optimizer's own name; a subclass spelled otherwise evades it. No such site exists, and D1 scopes the gate by name.
- A **named module-level function** that constructs the optimizer (`def make(): return DjangoOptimizerExtension()`) is not pinned. It would require resolving a name to its definition; no such site exists.

**Step 5 — accept the pin's false-positive direction knowingly.** The bare-class rule flags the class appearing in *any* list or tuple literal, not only in an `extensions=` argument. Measured at HEAD this over-flags nothing (all 7 sequence-literal occurrences are extensions entries), but a future `for cls in [DjangoOptimizerExtension, DjangoDebugExtension]:` would trip it. That trade is deliberate: a false positive on a governance pin is one loud, one-line-to-fix failure, while a false negative is precisely the rot D1 exists to stop. Say so in the test docstring so the next reader repairs the rule rather than deleting the test.

**Step 6 — `uv run ruff format <the nine files>` then `uv run ruff check --fix <the same files>`**, scoped to Slice 2's own files, never `.` (`AGENTS.md`; a repo-wide write-mode run would rewrite a concurrent session's work). Then `git status --short`: every modified path must be slice-intended and listed in `### Files touched`. Anything else is a stop-and-report, never a revert.

**What Worker 2 must not do.**

- **Never repair by weakening a test.** If a migrated site changes an assertion's meaning, that is a finding to record, not an edit to make. The one behavior-adjacent consequence to watch: a shared instance now serves the second and later executions on the same schema from `_plan_cache`, where the forbidden form re-planned each time. No site in the population holds the instance, so no existing assertion reads `cache_info()` at any of the 25 — verified — but the strictness tests in `tests/optimizer/test_extension.py:5386-5648` execute more than once on one schema, and they are where a cached-plan difference would surface first. If one of them changes behavior, report it; do not adjust the assertion.
- No production line changes. `django_strawberry_framework/` is not in this slice's scope.
- No `KANBAN.md` / `KANBAN.html` / `docs/GLOSSARY.md` / `docs/TREE.md` / `CHANGELOG.md` / `db.sqlite3` edits (the maintainer's fence).
- Never touch `docs/review/**` or `tests/mutations/test_operations.py` — a concurrent session's work.

### Test additions / updates

**Owed, and permanent:**

- `tests/test_ci_governance.py::test_no_active_source_uses_a_forbidden_optimizer_extensions_form` — the standing gate. **This is itself the durable test for the rule**; nothing further is owed on that axis.
- `tests/test_ci_governance.py` control rows — parametrized must-flag (9 cases) and must-not-flag (9 cases) tests over the classifier. They are the pin's positive and negative controls and they carry the failability weight (below).

**Placement** (`AGENTS.md` test-placement rules): `tests/` is the package tree, and `tests/test_ci_governance.py` already lives there as a repo-wide structural pin whose target is not the package. Same file, same rationale, no new module. No live-tier (`examples/fakeshop/test_query/`) test is owed: the property is static repository structure, unreachable from any GraphQL request.

**Not owed:**

- **No new test for the singleton-factory mechanism.** `tests/optimizer/test_extension.py::test_cache_hit_on_repeated_query` already pins `misses == 1` / `hits == 1` on a singleton-factory schema. Adding a second is duplication.
- **No per-site test.** The 25 migrations are behavior-preserving; each site's existing tests are its tests, and they re-run at Step 6 and at the floor.

**Failability proof — one entry, and it is owed** (`ARTIFACT.md` `### Failability proofs`; `BUILD.md` `## Failability proofs`).

The one new boundary is the classifier. Mutate **the boundary**, not the test file's presence: delete one of the classifier's two branches (e.g. drop the `ast.Lambda` arm, or drop the `id(node) in sequence_elements` qualifier so the bare-class arm stops discriminating) and record which rows fail. Expected: the must-flag control rows for that form fail (≥4 rows for the bare-class arm across the five bare-class snippets; ≥4 for the lambda arm), and widening the bare-class qualifier additionally fails the must-not-flag rows. That is a multi-row count by construction, so the boundary is not weakly pinned. Then revert and **prove the revert by byte-comparison**, not in prose.

Run it with `uv run python scripts/prove_failability.py docs/builder/temp-tests/slice-2/proofs.json`, which enforces the anchor-matches-exactly-once precondition and emits the subsection with every measured field filled in. Record the **pre-mutation state of the same scope** and the **collection/setup error count separately**; a proof carrying collection errors is not a valid count.

An **end-to-end control** is worth one further entry and is cheap: transiently revert one repaired site (say `tests/forms/test_resolvers.py`) to `extensions=[DjangoOptimizerExtension]`, confirm the sweep row fails and names that file and line, revert, byte-compare. That row count is 1 by construction — the sweep is one repo-wide assertion — which is exactly why the classifier's control rows, not the sweep, carry the failability weight. Record it as an end-to-end control alongside the boundary proof, not as the boundary proof.

**Hot-path number — the recipe, since the plan requires the metric to be reproducible as recorded.**

Both readings come from one temp test under `docs/builder/temp-tests/slice-2/` (per-cycle, gitignored, cleared by `scripts/clean_up.py`), modelled on `tests/optimizer/test_extension.py::test_cache_hit_on_repeated_query`:

1. **Structural reading, no execution needed.** On one schema built with a forbidden form, `schema.get_extensions()[0] is schema.get_extensions()[0]` → `False`; on the singleton-factory form → `True`. This is `Schema.get_extensions` observed directly rather than inferred.
2. **Cache reading, two executions of one query on one schema.** Singleton factory: hold the instance, execute twice, read `optimizer.cache_info()` → `misses=1, hits=1` on the second run. Forbidden form: the instances are unreachable by construction, so capture them without altering the form under test — pass `lambda: _record(DjangoOptimizerExtension())` where `_record` appends to a list and returns its argument, which is still a constructing lambda. Execute twice: **two** instances recorded, each reading `misses=1, hits=0`, aggregate `hits=0`.

Record both numbers, the exact snippet, and the query used. Do **not** promote this temp test into the permanent suite (see "Not owed" above).

**Floor verification** (Worker 2's build pass owns it): `uv venv /tmp/dsf-floor-029 --python 3.10`, install with an explicit `--python` — never into the shared `.venv` — then run the focused scope named in the amended declaration above with `--no-cov`. Record `uv pip list --python /tmp/dsf-floor-029/bin/python` and each command's pass/fail. One free extra worth a line: with the floor venv built, quote 0.316.0's own `Schema.get_extensions` body into the build report. That is not the verification (executing the tests is), but it closes the supported range against the 0.323.2 reading above with a fact rather than an inference.

### Implementation discretion items

Assessed and decided to belong to Worker 2:

- **The singleton's local variable name at each site** — `optimizer`, `optimizer_ext`, `extension`, or a site-descriptive name (`raising_optimizer` / `silent_optimizer` at the `:5600`/`:5608` pair). Constraint, not discretion: it must not shadow an existing binding in that scope, and the four conditional sites in `tests/test_relay_connection.py` already bind `optimizer` as the boolean flag.
- **Where in the enclosing function the singleton is declared** — immediately above the `Schema(...)` call, or grouped with the other local setup. Constraint: same scope as the `Schema(...)` call, never module level.
- **The test-function names and `ids=` for the control rows**, and whether must-flag and must-not-flag are two parametrized tests or one with an expected-outcome parameter. The module's existing style leans toward one test per property with readable ids.
- **The exact wording of the pin's assertion message**, provided it names the file, the line, the snippet, and the corrective form.

Not discretionary and settled above: the population (all 25), function-local-everywhere, the conditional shape that constructs nothing on the `else` branch, no shared test helper, the pin's home and its two-form scope, and reuse of `scripts.check_citations` for source enumeration.

### Spec slice checklist (verbatim)

This is a residual-cycle repair slice, so there is no matching sub-bullet block in the spec's `## Slice checklist` to copy — the spec's Slice-1 block describes the original 0.0.9 build, which shipped. Each box below is one sub-check Worker 2 must land, and each names the spec text that licenses it, quoted verbatim. Boxes stay `- [ ]` at planning; Worker 2 ticks **only** a box whose contract landed in its diff; Worker 1 audits every tick at final verification.

Licensing spec text, quoted verbatim from `## Slice checklist` (`:56`):

> Rewrite **every** instance-form `extensions=` entry — anonymous `[DjangoOptimizerExtension()]`, **named** (`ext = DjangoOptimizerExtension(); extensions=[ext]`), and the bare class `[DjangoOptimizerExtension]` — to a factory over a singleton **scoped to that construction site**: `extensions=[lambda: <instance>]`. This preserves the instance-bound [Plan cache][glossary-plan-cache] (same instance per request under 0.316.0's `get_extensions`) AND drops the `Schema.__init__` instance-form `DeprecationWarning`. Do NOT use the bare class or a constructing-`lambda` `lambda: DjangoOptimizerExtension()` (re-instantiated per request → cold cache, both modes, and a cache-hit-test failure).

and from `## Definition of done` item 4 (`:523`):

> a **forbidden-form grep** (`extensions=[DjangoOptimizerExtension()]` / `[DjangoOptimizerExtension]` / `[ext]` / `[_CaptureExt()]` / `lambda: DjangoOptimizerExtension()`) finds zero hits in active source/docs (only this spec's quoted examples + historical prose remain).

- [x] The population was re-derived by Worker 2 against HEAD before editing, and the site count and file list are recorded in the build report (a differing count is reported, not silently adopted).
- [x] All 7 bare-class sites are migrated to a factory over a singleton scoped to that construction site.
- [x] All 18 constructing-`lambda` sites are migrated to a factory over a singleton scoped to that construction site, the `strictness=` and `nested_connection_strategy=` variants included.
- [x] Every migrated singleton is **function-local**; no module-level singleton is introduced by this slice.
- [x] Each of the five conditional sites keeps its `else` branch constructing nothing (no optimizer is built for the no-optimizer parametrization).
- [x] The `tests/optimizer/test_extension.py` `:5600`/`:5608` pair carries two separate singletons, one per strictness value.
- [x] `examples/fakeshop/strategy_schemas.py::build_strategy_schema`'s docstring no longer claims a fresh per-execution extension; its module docstring is unchanged.
- [x] No assertion anywhere was weakened, inverted, or deleted to make a migrated site pass; any assertion whose meaning changed is recorded as a finding instead.
- [x] `tests/test_ci_governance.py` carries the classifier plus the repo-wide sweep test asserting no active `.py` constructs a schema with either forbidden optimizer form.
- [x] The pin's must-flag and must-not-flag control rows are present and green, covering at minimum the 9 + 9 snippet set enumerated in `### Population re-derivation`.
- [x] The pin scopes its corpus through `scripts/check_citations.py`'s first-party source-tree definition, with the coupling named in a comment.
- [x] `tests/test_ci_governance.py`'s module docstring is widened to cover the Python-source pin, and its coverage note remains accurate.
- [x] The pin's deliberate non-extensions (deprecated instance form, subclass entries, named constructing functions) and its false-positive direction are recorded, in the test docstring or the build report, as considered rather than missed.
- [x] `### Failability proofs` carries one entry for the classifier boundary — mutation, scope as run, pre-mutation state, listed failing node ids, collection/setup errors separately, revert proved by byte-comparison — plus the end-to-end control that reintroduces one forbidden site and observes the sweep row fail.
- [x] `### Hot-path budget` carries both readings: the `get_extensions` identity comparison and the two-execution `cache_info()` numbers for the forbidden form (`misses=2, hits=0` in aggregate) and the singleton factory (`misses=1, hits=1`), with the exact snippet and query.
- [x] `### Floor verification` records the scratch venv path outside the repo, the resolved versions as read by `uv pip list --python <venv>/bin/python`, the focused scope run, and pass/fail — with `.venv` unmutated.
- [x] `uv run ruff format` and `uv run ruff check --fix` were run **scoped to this slice's own files**, and `git status --short` after them shows only slice-intended paths.

### Carry-forward to Slice 3 (spec reconciliation — recorded here, not enacted)

The spec is **not** edited by this pass. Two items Slice 3 owns, surfaced now while the evidence is in hand:

1. **`## Definition of done` item 4 states the gate as a list of five literal spellings.** That is precisely the instrument that under-reported this regression: `lambda: DjangoOptimizerExtension()` matched 5 of the 18 constructing-lambda sites, because the other 13 carry keyword arguments. Slice 3 should restate item 4 by **form** — a bare class entry and any entry that constructs the optimizer per call — matching the normative sentence `## Slice checklist` `:56` already uses, and should name the standing pin as the gate rather than a one-shot grep.
2. **The census figures in item 2 and the `## Slice checklist` sub-bullets** ("≈48 entries across the 5 package test files", "41", "(3)", "(2)") are stale, and one of them is load-bearing in a *completion* claim rather than a `## Current state` snapshot. Build-plan divergence 9 already flags this; the population measured here (25 forbidden entries; ~75 already-correct `lambda: <instance>` entries; the element census by spelling) is the current reading if Slice 3 wants one.

**Spec status-line re-verification** (`worker-1.md`, every Worker 1 spawn): `docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md:1-9` re-read this pass. Lines 1-7 describe a shipped card and a version boundary that this slice does not touch; line 9's rationale-companion pointer resolves (Slice 1 created the file). **Nothing this slice falsifies, so no spec edit is made** — and DoD item 4's text must be reconciled against what Slice 2 actually lands, which is Slice 3's job, not this one's.

### Out of fence — for `bld-final-029.md`'s deferred-work catalog

Found while re-deriving the population; **not** repaired, per the maintainer's spec-files-and-`.py`-files-only fence:

- `CHANGELOG.md:173` and `:184`/`:186` carry consumer-facing snippets showing the deprecated instance form `extensions=[DjangoOptimizerExtension()]` (0.0.7-era entries). `CHANGELOG.md:109` correctly *describes* the 0.0.9 migration and is fine as history.
- `KANBAN.md:3597` and `:3603` — the `DONE-029` card body still names the rejected migration targets as Slice 1's goal. Already recorded in the build plan's section D; noted here so the two records agree.
- `docs/bug_hunt/temp-tests/resolvers_async_parity/` carries 4 forbidden-form entries in gitignored scratch. Outside active source and outside the pin's corpus by design; listed so a later reader does not mistake its exclusion for a miss.

---

## Build report (Worker 2)

### Files touched

Grounded in `git status --short` after both ruff invocations (below). Nine files, all in Slice 2's writable list as amended by re-partition #2.

- `tests/forms/test_resolvers.py` — `::_schema`: 1 bare-class site -> function-local singleton + `[lambda: optimizer]`.
- `tests/types/test_resolvers.py` — 1 bare-class site inside `::test_o1_prefetch_related_onetoone_reverse_matches_unoptimized` -> function-local singleton declared immediately above the `strawberry.Schema(...)` call.
- `tests/mutations/test_write_transaction.py` — the module's schema builder: 1 bare-class site -> function-local singleton.
- `tests/mutations/test_resolvers.py` — 2 bare-class sites (`::_schema` and the async leak-probe test) -> function-local singletons.
- `examples/fakeshop/test_query/test_products_visibility_api.py` — 2 bare-class sites -> function-local singletons.
- `tests/optimizer/test_extension.py` — 7 constructing-lambda sites -> function-local singletons; the `strictness="raise"` / `strictness="off"` pair in one test carries **two** separately-named locals (`raising_optimizer` / `silent_optimizer`).
- `tests/test_relay_connection.py` — 10 constructing-lambda sites; 6 unconditional -> `optimizer = ...` above the `Schema(...)` call, 4 conditional -> the `if optimizer:` block shape (`optimizer_ext`, non-shadowing, because those four functions already bind `optimizer` as the boolean flag).
- `examples/fakeshop/strategy_schemas.py` — `::build_strategy_schema`: 1 conditional constructing-lambda site -> `if strategy is not None:` block; **plus** the function-docstring correction (the sentence claiming a "fresh per-execution `DjangoOptimizerExtension`", which the repair falsifies). The **module** docstring is byte-unchanged.
- `tests/test_ci_governance.py` — the standing governance pin: widened module docstring, the `scripts.check_citations.iter_python_sources` import with its coupling comment, `_forbidden_optimizer_entries`, the 9 + 9 control rows, and the repo-wide sweep test.

### Tests added or updated

Added, all permanent, all in `tests/test_ci_governance.py` (this repo's established home for standing repo-wide structural pins — same file, same rationale, no new module; `AGENTS.md` test placement is satisfied because `tests/` is the package tree and this module already sits there as a repo-wide pin whose target is not the package):

- `tests/test_ci_governance.py::test_no_active_source_uses_a_forbidden_optimizer_extensions_form` — the gate itself: sweeps every first-party `.py` (via `scripts/check_citations.py::iter_python_sources`) and fails naming the file, the line, the offending snippet, and the corrective form.
- `tests/test_ci_governance.py::test_forbidden_optimizer_form_classifier_flags_every_forbidden_shape` — 9 parametrized positive-control rows: `bare-single`, `bare-tuple`, `bare-multi-element`, `bare-multiline`, `bare-assigned-to-a-variable`, `lambda-no-args`, `lambda-with-kwargs`, `lambda-in-a-conditional-expression`, `lambda-dotted`.
- `tests/test_ci_governance.py::test_forbidden_optimizer_form_classifier_ignores_the_permitted_shapes` — 9 parametrized negative-control rows: `factory-over-a-singleton`, `factory-over-a-module-singleton`, `bare-debug-extension`, `bare-error-policy-extension`, `lambda-constructing-another-extension`, `subclass-declaration`, `classmethod-call`, `identity-assertion`, `bare-instance-assignment`.

No test was updated, weakened, inverted, or deleted. Mechanically confirmed over the eight migrated files:

```shell
git diff -U0 -- <the 8 migrated files> | grep -E '^[-+]' | grep -v '^[-+][-+][-+]' \
  | grep -iE 'assert|pytest\.|skip|xfail'
# exit 1 (no match): not one assertion, marker, skip, or xfail line appears in the diff
```

Per the plan's "Not owed": no new test for the singleton-factory mechanism (already pinned by `tests/optimizer/test_extension.py::test_cache_hit_on_repeated_query`) and no per-site test (the migrations are behavior-preserving; each site's existing tests are its tests, and they re-ran here and at the floor).

### Population re-derivation (Step 0)

Re-derived at HEAD with Worker 1's AST classifier, run from a scratch copy at `docs/builder/temp-tests/slice-2-029/classify.py` over the four `SOURCE_TREES`, **before** any edit:

```
--- total 25 sites in 8 files
```

**25 sites in 8 files. The count and every line number match Worker 1's table exactly** — 7 bare-class + 18 constructing-lambda, and the per-file distribution is identical (`test_relay_connection.py` 10, `test_extension.py` 7, `test_resolvers.py` (mutations) 2, `test_products_visibility_api.py` 2, `forms/test_resolvers.py` 1, `types/test_resolvers.py` 1, `write_transaction` 1, `strategy_schemas.py` 1). Nothing differed, so nothing was silently adopted.

After the migration the same instrument returns `--- total 0 sites in 0 files`, and the permanent pin re-derives the same reading through its own independent copy of the rule.

### Validation run

- `uv run ruff format <the 9 slice files>` — pass (`9 files left unchanged` on the final invocation; earlier invocations reformatted only `tests/test_ci_governance.py`). Never `.`.
- `uv run ruff check --fix <the same 9 files>` — pass (`All checks passed!`).
- `uv run python scripts/check_trailing_commas.py --check <the same 9 files>` — pass (silent).
- `uv run python scripts/check_citations.py` — pass, `OK: 789 citations resolve`.
- `git status --short` after both ruff invocations — the nine slice files, plus exactly the out-of-scope paths the build plan already records: Slice 1's `docs/SPECS/spec-029-*.md` / `docs/SPECS/appx/spec-004-*-rationale.md` / `spec-029-*-rationale.md` / `bld-slice-1-*.md` / `build-029-*.md`, and the concurrent session's `docs/review/review-0_0_14.md`, `docs/review/rev-*.md`, `tests/mutations/test_operations.py`. **No unexpected churn**; nothing reverted.
- Focused test runs (all without any `--cov*` flag):
  - `uv run pytest tests/test_ci_governance.py --no-cov -q` — **54 passed** (36 pre-existing + the 18 new rows).
  - `uv run pytest tests/test_relay_connection.py tests/optimizer/test_extension.py tests/forms/test_resolvers.py tests/types/test_resolvers.py tests/mutations/test_write_transaction.py tests/mutations/test_resolvers.py examples/fakeshop/test_query/test_products_visibility_api.py tests/test_ci_governance.py --no-cov -q` — **550 passed**.
  - `uv run pytest examples/fakeshop/test_query/test_optimizer_auto_api.py tests/test_lateral_pg_parity.py --no-cov -q` — **2 passed, 35 skipped** (the 35 are the `pg`-marked lateral rows, which self-skip off Postgres; that skip is pre-existing and unrelated to this slice).
- **Test-staleness full sweep: not owed.** `BUILD.md` `### Test staleness a focused run cannot see` scopes it to a slice that changes an example-model field set or a wire shape. This slice changes neither: no model, no `fields=`/`exclude=` list, no schema field, no argument envelope. Every changed line is a local expression substitution inside an existing test body.

### Failability proofs

Two boundary entries plus one end-to-end control. Produced by `uv run python scripts/prove_failability.py docs/builder/temp-tests/slice-2-029/proofs.json --output docs/builder/temp-tests/slice-2-029/proofs.md` (the tool enforces the anchor-matches-exactly-once precondition before taking the pristine copy, keeps the scratch root at `/private/tmp/dsf-failability-slice-2-029` **outside** the repo, runs the unmutated baseline by default, and proves each restore by `filecmp.cmp(shallow=False)` + SHA-256).

**The one new boundary this pass introduces is the classifier** `tests/test_ci_governance.py::_forbidden_optimizer_entries`. It has two arms and each is mutated separately, because a mutation that removed only one arm while the record claimed "the classifier" would leave half the boundary unproved. The 25 site migrations introduce no boundary and owe none (`BUILD.md` `### What needs a proof, and what does not`: refactors that move existing behavior).

- `tests/test_ci_governance.py::_forbidden_optimizer_entries` (**constructing-lambda arm**) — mutation applied: the arm's `if isinstance(node, ast.Lambda):` guard replaced by `if False:` with the body left intact, so no `lambda: DjangoOptimizerExtension(...)` in any spelling is classified as forbidden; scope as run: `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_ci_governance.py`; pre-mutation state of that scope: **green, `54 passed`, pytest exit 0** (0 pre-existing failing rows differenced out); failing node ids:
  - `tests/test_ci_governance.py::test_forbidden_optimizer_form_classifier_flags_every_forbidden_shape[lambda-no-args]`
  - `tests/test_ci_governance.py::test_forbidden_optimizer_form_classifier_flags_every_forbidden_shape[lambda-with-kwargs]`
  - `tests/test_ci_governance.py::test_forbidden_optimizer_form_classifier_flags_every_forbidden_shape[lambda-in-a-conditional-expression]`
  - `tests/test_ci_governance.py::test_forbidden_optimizer_form_classifier_flags_every_forbidden_shape[lambda-dotted]`

  collection/setup errors: **0**; mutant pytest exit code 1 (`4 failed, 50 passed`); revert proved by byte-comparison: `filecmp.cmp(shallow=False) True; sha256 c843c74100c6dcb3... == c843c74100c6dcb3...` against the pre-mutation copy. Verdict: **pinned** (4 rows).

- `tests/test_ci_governance.py::_forbidden_optimizer_entries` (**bare-class-in-a-sequence arm**) — mutation applied: the whole five-clause `isinstance(node, ast.Name) and node.id == OPTIMIZER_EXTENSION and … and id(node) in sequence_elements` condition replaced by `if False:`, so `extensions=[DjangoOptimizerExtension]` is no longer classified as forbidden; scope as run: the same invocation as above; pre-mutation state of that scope: **green, `54 passed`, pytest exit 0** (0 pre-existing failing rows); failing node ids:
  - `tests/test_ci_governance.py::test_forbidden_optimizer_form_classifier_flags_every_forbidden_shape[bare-single]`
  - `tests/test_ci_governance.py::test_forbidden_optimizer_form_classifier_flags_every_forbidden_shape[bare-tuple]`
  - `tests/test_ci_governance.py::test_forbidden_optimizer_form_classifier_flags_every_forbidden_shape[bare-multi-element]`
  - `tests/test_ci_governance.py::test_forbidden_optimizer_form_classifier_flags_every_forbidden_shape[bare-multiline]`
  - `tests/test_ci_governance.py::test_forbidden_optimizer_form_classifier_flags_every_forbidden_shape[bare-assigned-to-a-variable]`

  collection/setup errors: **0**; mutant pytest exit code 1 (`5 failed, 49 passed`); revert proved by byte-comparison: `filecmp.cmp(shallow=False) True; sha256 c843c74100c6dcb3... == c843c74100c6dcb3...`. Verdict: **pinned** (5 rows).

**End-to-end control — recorded as a control, NOT as the boundary proof** (`docs/builder/temp-tests/slice-2-029/control.json` -> `control.md`). One repaired site is put back into the forbidden form and the sweep is observed to catch it:

- `tests/forms/test_resolvers.py::_schema` — mutation applied: `extensions=[lambda: optimizer],` -> `extensions=[DjangoOptimizerExtension],`; scope as run: `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_ci_governance.py`; pre-mutation state of that scope: **green, `54 passed`, pytest exit 0**; failing node ids: `tests/test_ci_governance.py::test_no_active_source_uses_a_forbidden_optimizer_extensions_form`; collection/setup errors: **0**; revert proved by byte-comparison: `filecmp.cmp(shallow=False) True; sha256 9cb2e51742aae0a0... == 9cb2e51742aae0a0...`.

  **This entry is 1 row by construction and is deliberately not the classifier's pin.** The sweep is a single repo-wide assertion, so *any* reintroduced site anywhere in the tree fails exactly that one row; more rows are unobtainable without splitting one property into several assertions, which would be a weaker boundary, not a stronger one. That is precisely why the plan puts the failability weight on the 18 control rows — which measure 4 and 5 — and why the tool's automatic "weakly pinned" verdict on this entry is a verdict about a control, not about the boundary. Both boundary arms are strongly pinned above.

  The message the failing row prints was captured separately, without mutating the tree (the classifier applied in-process to an in-memory mutated copy of the file):

  ```
  forbidden DjangoOptimizerExtension extensions= form(s) in active source:
  tests/forms/test_resolvers.py:124: bare class in a sequence: DjangoOptimizerExtension
  Use a factory over a singleton scoped to that construction site: optimizer = DjangoOptimizerExtension(...) then extensions=[lambda: optimizer]
  ```

  So the row names the file, the line, the form, the snippet, and the fix.

**No mutation is live.** After the last proof the AST classifier re-run over all four source trees returns `--- total 0 sites in 0 files`, `/private/tmp/dsf-failability-slice-2-029/` holds only its `pristine/` directory (no `ACTIVE-MUTATION.json`, no `RESTORE-FAILED.json`), and the full focused suite is green.

One recorded process note: the first draft of the constructing-lambda mutation deleted the arm's body outright, which is a `SyntaxError` and produced **1 collection error / 0 failures** — the tool refused it as `INVALID COUNT` rather than recording a measured zero. The mutation was rewritten to keep the body and neutralize the guard, and re-run. Recorded because the fail-open direction is exactly the one `BUILD.md` `### What gets recorded` warns about: a catastrophic mutation reads as an unpinned boundary.

### Hot-path budget

Plan declares this slice hot-path (the optimizer's per-request plan-cache lifecycle). Both readings the plan names were captured from one temp test, `docs/builder/temp-tests/slice-2-029/test_hot_path_budget.py` (per-cycle, gitignored, **not** promoted into the permanent suite), run as:

```shell
uv run pytest docs/builder/temp-tests/slice-2-029/test_hot_path_budget.py --no-cov -q -n0 -s
```

The query is the one `tests/optimizer/test_extension.py::test_cache_hit_on_repeated_query` uses: `{ allItems { name category { name } } }` over `ItemType`/`CategoryType`, `services.seed_data(1)`.

**Reading 1 — metric: does one schema hand back the SAME extension object on two `get_extensions()` calls?** (`Schema.get_extensions` observed directly, no execution needed.)

| Form | `get_extensions()[0] is get_extensions()[0]` |
|---|---|
| BEFORE — bare class `extensions=[DjangoOptimizerExtension]` | `False` |
| BEFORE — constructing lambda `extensions=[lambda: DjangoOptimizerExtension()]` | `False` |
| AFTER — singleton factory `extensions=[lambda: optimizer]` | `True` |

Delta: `False` -> `True`. A fresh instance per operation becomes one instance for the life of the schema.

**Reading 2 — metric: `DjangoOptimizerExtension.cache_info()` after two `execute_sync` of ONE query on ONE schema.** The forbidden form's instances are unreachable by construction, so they are captured without altering the form under test: `extensions=[lambda: _record(DjangoOptimizerExtension())]`, where `_record` appends to a list and returns its argument — still a constructing lambda.

| | instances built | per-instance `cache_info()` | aggregate misses | aggregate hits |
|---|---|---|---|---|
| **BEFORE** (constructing lambda) | **2** | `CacheInfo(hits=0, misses=1, size=1)` twice | **2** | **0** |
| **AFTER** (singleton factory) | **1** | `CacheInfo(hits=1, misses=1, size=1)` | **1** | **1** |

**Delta: misses 2 -> 1 (-1), hits 0 -> 1 (+1); plan-cache hit rate 0/2 -> 1/2 over two executions**, and the miss count stops scaling with request count. That is the number that makes this a repair rather than a rewrite.

Both readings were **also captured at the floor** (Python 3.10.19 / Django 5.2.16 / strawberry-graphql 0.316.0) with `/tmp/dsf-floor-029/bin/python -m pytest … -n0 -s`, and are **identical** — same `False/False/True`, same `misses=2, hits=0` before and `misses=1, hits=1` after. The behavior therefore holds at both ends of the supported range, not only at the resolved head.

### Floor verification

Owned by this pass per the plan's declaration. Scratch venv **outside** the repo; the shared `.venv` was never installed into (every install carried an explicit `--python`, and `.venv` still reports Django 6.1 / Python 3.14.2 afterwards; `uv.lock` is unmodified).

```shell
uv venv /tmp/dsf-floor-029 --python 3.10
uv pip install --python /tmp/dsf-floor-029/bin/python -e . --group dev
uv pip install --python /tmp/dsf-floor-029/bin/python 'django==5.2.16' 'strawberry-graphql==0.316.0'
```

Resolved versions, read with `uv pip list --python /tmp/dsf-floor-029/bin/python` (full listing saved to `docs/builder/temp-tests/slice-2-029/floor-pip-list.txt`); interpreter read with `/tmp/dsf-floor-029/bin/python -V`:

```
Python 3.10.19
channels                    4.3.2
django                      5.2.16
django-strawberry-framework 0.0.14      /Users/riordenweber/projects/django-strawberry-framework
graphql-core                3.2.11
pytest                      9.1.1
pytest-django               4.14.0
strawberry-graphql          0.316.0
```

Focused scope as run, per the plan's amended declaration:

| Command | Result |
|---|---|
| `/tmp/dsf-floor-029/bin/python -m pytest tests/test_relay_connection.py tests/optimizer/test_extension.py tests/forms/test_resolvers.py tests/types/test_resolvers.py tests/mutations/test_write_transaction.py tests/mutations/test_resolvers.py examples/fakeshop/test_query/test_products_visibility_api.py examples/fakeshop/strategy_schemas.py tests/test_ci_governance.py --no-cov -q` | **PASS** — `550 passed in 15.21s` |
| `/tmp/dsf-floor-029/bin/python -m pytest examples/fakeshop/test_query/test_optimizer_auto_api.py tests/test_lateral_pg_parity.py --no-cov -q` | **PASS** — `2 passed, 35 skipped in 7.83s` (the 35 are `pg`-marked; they self-skip off Postgres at head too) |
| `/tmp/dsf-floor-029/bin/python -m pytest docs/builder/temp-tests/slice-2-029/test_hot_path_budget.py --no-cov -q -n0 -s` | **PASS** — both hot-path readings identical to head |

**The free extra the plan asked for.** `Schema.get_extensions` as it actually exists in strawberry-graphql **0.316.0**, read out of the floor venv (`inspect.getsource`), not inferred:

```python
def get_extensions(self, sync: bool = False) -> list[SchemaExtension]:
    # Deprecated instances are passed through as-is. The DeprecationWarning
    # is emitted once at ``Schema.__init__``; users are expected to migrate
    # to a class or factory for per-request isolation.
    resolved: list[SchemaExtension] = [
        ext if isinstance(ext, SchemaExtension) else ext()
        for ext in self.extensions
    ]
    if self.directives:
        resolved.append(
            DirectivesExtensionSync() if sync else DirectivesExtension()
        )
    return resolved
```

Identical in the load-bearing clause to Worker 1's 0.323.2 reading. The mechanism Decision 3 rests on is confirmed at the floor by execution, and the contract is closed across the whole supported range.

### Implementation notes

- **Local variable naming.** `optimizer` at every site whose enclosing scope does not already bind it; `optimizer_ext` at the four conditional `tests/test_relay_connection.py` sites, whose enclosing functions bind `optimizer` as the boolean flag; `raising_optimizer` / `silent_optimizer` at the `test_extension.py` two-schema pair, where a generic name at both would read as one instance. Non-shadowing was verified mechanically, not by eye: an AST pass collected every `Store`-context `Name` and every `arg` in each enclosing function and confirmed neither chosen name was already bound.
- **Conditional shape.** `extensions = []` then `if <flag>:` with the construction *inside* the block, exactly as planned — the `else` path constructs nothing, so the no-optimizer parametrization is byte-for-byte unchanged in behavior. The tempting one-liner (`ext = DjangoOptimizerExtension(...)` above, `[lambda: ext] if flag else []` below) would build an optimizer for the no-optimizer rows and is a behavior change; it was not used.
- **Declaration placement.** Immediately above the `Schema(...)` call in every case, so the instance and the factory that closes over it read as one unit. Never module level: the plan's rule, and correct here because three of the sites sit in helpers that build a *fresh schema per call*, where one shared instance would put unrelated schemas' plans in one cache and make per-test `cache_info()` counters order-dependent.
- **The pin takes source text plus a label, never a path.** That is what lets the 18 control rows feed it literal snippets; a path-only signature would make the controls unwritable, and the controls are the whole reason the boundary is strongly pinned.
- **`OPTIMIZER_FIX` is a plain literal, not derived from `OPTIMIZER_EXTENSION.lower()`.** The derived spelling rendered `djangooptimizerextension = DjangoOptimizerExtension(...)` in the failure message — technically valid, unreadable as guidance. Caught by printing the message rather than by reading the code.
- **The classifier is a second copy of the rule by design, not by oversight.** `docs/builder/temp-tests/slice-2-029/classify.py` is the per-cycle scratch instrument and dies with the cycle; `tests/test_ci_governance.py::_forbidden_optimizer_entries` is the durable one. Both agreeing on 25-before / 0-after is two independent readings, which is the point.
- **No shared `optimizer_factory()` test helper**, per the plan's decided answer. The two-line literal is the mechanism the spec mandates, it matches the ~75 already-correct sites in these same files, and several sites need the instance by name.
- **Nothing was added to `scripts/`, `.pre-commit-config.yaml`, or CI** — maintainer decision D1 settled the placement.

### Notes for Worker 3

- **A generator write happened and was undone, byte-identically. Recorded rather than hidden.** Early in the pass, while establishing whether widening `tests/test_ci_governance.py`'s module docstring would strand `docs/TREE.md`, `uv run python scripts/build_tree_md.py` was run **without** `--check` and rewrote `docs/TREE.md`, which is outside this slice's fence. It was restored immediately with `git show HEAD:docs/TREE.md > /tmp/dsf-tree-head.md && cp /tmp/dsf-tree-head.md docs/TREE.md`, proved by `cmp` (exit 0), and `git status --short -- docs/TREE.md` is empty. No `git checkout` / `git restore` / `git stash` was used. `docs/TREE.md` is **not** in this slice's diff.
- **`docs/TREE.md` is stale at HEAD, and it is not this slice's doing.** `scripts/build_tree_md.py --check` fails on a clean-of-this-slice tree; the whole delta is two lines adding `tests/mutations/test_operations.py`, the concurrent session's new untracked file. Out of scope, not reverted, recorded so the final gate does not attribute it here.
- **Why the pin's module docstring keeps its first line.** `build_tree_md.py` renders **only the first docstring line** into `docs/TREE.md` (`scripts/build_tree_md.py::first_python_docstring_sentence`), and CI runs `build_tree_md.py --check` (`.github/workflows/django.yml`). Changing `"""Governance tests for the CI workflow definitions."` would therefore demand a `docs/TREE.md` regeneration, which is out of this cycle's fence. The line is byte-unchanged; the widening landed in the paragraphs below it and in the coverage note, which is what the checklist box asks for. See the amendment under `### Notes for Worker 1` — the summary line now under-describes the module and owes a first-line rewrite in a pass that owns `docs/TREE.md`.
- **`scripts/review_inspect.py` was not run**, and no shadow file was read or written by this pass. `docs/shadow/` is untouched. Skip reason: the slice adds no `.py` file, touches nothing under `optimizer/` or `types/`, and its only >30-line addition is to `tests/test_ci_governance.py`, which is outside `django_strawberry_framework/` and under the 50-line threshold for logic (the addition is dominated by control-row data and docstrings). Worker 3's own trigger list should be evaluated independently.
- **Temp artifacts for review**, all under the gitignored `docs/builder/temp-tests/slice-2-029/`: `classify.py` (the re-derivation instrument), `proofs.json` / `proofs.md` (the two boundary proofs), `control.json` / `control.md` (the end-to-end control), `test_hot_path_budget.py` (both hot-path readings), `floor-pip-list.txt` (the floor's full resolved version list). None is promoted; `scripts/clean_up.py` clears them with the cycle.
- **Re-running the proofs.** `uv run python scripts/prove_failability.py docs/builder/temp-tests/slice-2-029/proofs.json` reproduces both boundary entries at the recorded scope; add `--check-anchors-only` first if you want the precondition without the runs. The control is a separate manifest so the tool's `--output` block for the boundaries is not labelled by a control's 1-row verdict.
- **Where to look hardest.** The four conditional sites in `tests/test_relay_connection.py` (`_genres_list_schema`, `_genres_distinct_book_schema`, `_genres_expression_ordered_schema`, and the nested `_build`) are the only places where a wrong rewrite would be silently *behavioral* rather than loud: an optimizer constructed on the no-optimizer branch still passes every assertion in those tests while changing what they exercise.

### Notes for Worker 1 (spec reconciliation)

**Amendment 1 — `tests/test_ci_governance.py`'s first docstring line, and the `docs/TREE.md` entry it feeds. (Small, mechanically obvious drift from the plan; implemented as described and surfaced here per `worker-2.md`.)**

- **Where it lives:** the plan's `### Implementation steps`, Step 3, sub-step 1 (this artifact) — not the spec.
- **Current wording (the plan's):** *"Extend the **module docstring**. It currently scopes the file to `.github/` workflow YAML, and its 'Coverage note' says the assertions target YAML rather than `django_strawberry_framework`. Both sentences become inaccurate the moment a Python-source pin lands. The coverage note's *conclusion* still holds — reading `.py` files adds no package coverage surface either — so widen the subject, keep the note."*
- **What was implemented and why it deviates:** the second paragraph and the coverage note were widened as instructed. The docstring's **first line** was left byte-identical, because `scripts/build_tree_md.py::first_python_docstring_sentence` renders exactly that line into `docs/TREE.md` and `.github/workflows/django.yml` runs `build_tree_md.py --check`; rewriting it without regenerating `docs/TREE.md` breaks CI, and `docs/TREE.md` is outside this cycle's maintainer fence.
- **Recommended replacement (for a pass that owns `docs/TREE.md`):** change the first line to *"Governance tests for the CI workflow definitions and first-party source posture."* and regenerate `docs/TREE.md` in the same change (the entry appears twice, at `docs/TREE.md:455` and `:681`). Until then the summary line under-describes the module. Routing note: this is a `docs/TREE.md` item, so it belongs in `bld-final-029.md`'s deferred-work catalog rather than in the spec, unless the maintainer widens the fence.

**Amendment 2 — `## Definition of done` item 4 now states a gate this slice has replaced.**

- **Where it lives:** `docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md`, `## Definition of done`, item 4 (at `:523` when this was written).
- **Current wording, quoted:** *"a **forbidden-form grep** (`extensions=[DjangoOptimizerExtension()]` / `[DjangoOptimizerExtension]` / `[ext]` / `[_CaptureExt()]` / `lambda: DjangoOptimizerExtension()`) finds zero hits in active source/docs (only this spec's quoted examples + historical prose remain)."*
- **Recommended replacement:** *"the two forbidden optimizer `extensions=` **forms** — a bare `DjangoOptimizerExtension` class entry, and any entry that constructs the optimizer per call (a constructing `lambda`, in any keyword spelling) — are absent from active first-party source, enforced continuously by [`tests/test_ci_governance.py::test_no_active_source_uses_a_forbidden_optimizer_extensions_form`][test-ci-governance] rather than by a one-shot grep. The forms are stated by shape because a literal-spelling grep is what let the regression back in: `lambda: DjangoOptimizerExtension()` matched 5 of the 18 constructing-`lambda` sites, the other 13 carrying `strictness=` or `nested_connection_strategy=`. Only this spec's quoted examples and historical `CHANGELOG.md` / archived-spec prose still show the forbidden shapes."*
- **Link definitions the replacement needs:** `[test-extension]` already resolves in the spec's bottom block; `[test-ci-governance]` is new and needs `[test-ci-governance]: ../../tests/test_ci_governance.py` added under the spec's `<!-- tests/ -->` group (alphabetical).
- **Why:** Worker 1 already flagged this under `### Carry-forward to Slice 3` item 1. This restates it against what actually landed, so Slice 3 can drop it in rather than re-derive it. The measured population is 25 forbidden entries in 8 files before the repair and 0 after, alongside ~75 already-correct `lambda: <instance>` entries.

**Amendment 3 — Decision 3's granularity sentence has a live counterexample worth naming, and the spec's own example is now the weaker one.**

- **Where it lives:** `docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md`, `### Decision 3 — Slice 1 adopts the singleton-factory `extensions=` form`, the "Granularity is per construction site, not per file" bullet list.
- **Current wording, quoted:** *"A single module-level instance shared across that file's ~41 schema-building entries would **pollute the per-test cache counters** (order-dependent failures) and could not carry per-site `strictness=` ([`tests/optimizer/test_relay_id_projection.py`][test-relay-id-projection] mixes `strictness=\"raise\"` and the default in one module)."*
- **Recommended replacement:** *"A single module-level instance shared across that file's schema-building entries would **pollute the per-test cache counters** (order-dependent failures) and could not carry per-site `strictness=`. The sharpest case is a single test function that builds two schemas at once — one `strictness=\"raise\"` and one `strictness=\"off\"` — where per-file granularity is not merely undesirable but impossible: [`tests/optimizer/test_extension.py`][test-extension] holds exactly that pair, and it carries two separately-named function-local singletons."*
- **Why:** the cross-module example (`test_relay_id_projection.py`) illustrates a preference; the same-function pair is a proof. The `~41` figure is also one of the stale census numbers already flagged as build-plan divergence 9. Fold at Slice 3's discretion.

**Not an amendment, recorded so it is not re-derived:** no spec text this slice touched turned out to be false, and the mechanism Decision 3 rests on was confirmed by **execution** at the floor (0.316.0's `get_extensions` body, quoted above), not merely by reading a newer version. Nothing in the diff conflicts with the spec. No structural-drift pause was triggered; `Status: built`.

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

---

## Review (Worker 3)

### Failability re-run — mutations pre-registered BEFORE they are made

`worker-3.md` "Reading is necessary, not sufficient": the mutation is recorded here before it is applied, reverted inside this same pass, and the revert proved by byte-comparison. Anchor check precedes every pristine copy (`scripts/prove_failability.py` enforces the order). Scratch roots are outside the repository. No `git checkout` / `git restore` / `git stash` / `git worktree` at any point.

Worker 2's recorded row counts are **4** (constructing-lambda arm) and **5** (bare-class arm), both above the mandatory re-run floor of 3-or-fewer, and neither boundary is a security or data-isolation decision — so an empty re-run set would be *legal*. It is not taken. Grounds to distrust, stated before measuring: the end-to-end control measures **1** row and the pass itself asks whether that framing is legitimate, and the two arms live in one function so a mutation could plausibly remove more (or less) than the arm it names.

Mutations to be applied, one at a time, each reverted before the next:

1. `tests/test_ci_governance.py::_forbidden_optimizer_entries` (constructing-lambda arm) — replace the arm's `if isinstance(node, ast.Lambda):` guard with `if False:`, body intact.
2. `tests/test_ci_governance.py::_forbidden_optimizer_entries` (bare-class-in-a-sequence arm) — replace the five-clause `isinstance(node, ast.Name) and ...` condition with `if False:`.
3. End-to-end control: `tests/forms/test_resolvers.py::_schema` — `extensions=[lambda: optimizer],` -> `extensions=[DjangoOptimizerExtension],`.

Scope as run, matching Worker 2's recorded scope exactly: `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_ci_governance.py`.

**Fourth mutation, pre-registered before it is made (Worker 3's own probe, not a re-run of a Worker 2 record).** Hunting the fail-open shape in the gate itself: the sweep's corpus comes from `scripts/check_citations.py::iter_python_sources`, and `for path in iter_python_sources(): ...` over an EMPTY corpus yields `violations == []`, which passes. The 18 control rows feed the classifier literal snippets and never touch the corpus, so nothing in the diff pins that the corpus is non-empty. Mutation: in `scripts/check_citations.py`, replace the four-element `SOURCE_TREES` tuple with `()`. Scope as run: the same `tests/test_ci_governance.py` invocation. Reverted inside this pass, proved by byte-comparison.

**Fifth mutation, pre-registered before it is made.** The whole-corpus emptying above is caught elsewhere (`scripts/check_citations.py::main` raises `No .py sources found`, and pre-commit + `.github/workflows/django.yml:53` run it), so it is not the realistic narrowing. The realistic one is dropping a single tree. Mutation: replace `"examples",` with nothing inside `SOURCE_TREES`, which removes 159 files — including the two `examples/` sites this slice just repaired — from the sweep while leaving `check_citations` green. Scope as run: the same `tests/test_ci_governance.py` invocation, then a second reading at `tests/test_ci_governance.py tests/test_bug_hunt.py tests/test_clean_up.py`. Reverted inside this pass, proved by byte-comparison.

**Sixth mutation, pre-registered before it is made — the one that matters.** Dropping `"examples"` or `"scripts"` or `"django_strawberry_framework"` from `SOURCE_TREES` is caught by `check_citations` itself (unresolvable citations); dropping **`"tests"`** is not — `check_citations` returns `OK: 649 citations resolve`, exit 0. `tests/` holds 21 of this slice's 25 repaired sites. Mutation: remove `"tests",` from `SOURCE_TREES`. Scope as run: the same `tests/test_ci_governance.py` invocation. Reverted inside this pass, proved by byte-comparison.

#### Re-run results — node-id SETS, not totals

Instruments and manifests under `docs/builder/temp-tests/slice-2-029/`: `w3-classify.py` (my own classifier, a different formulation from Worker 2's), `w3-rerun-proofs.json` / `.md`, `w3-rerun-control.json` / `.md`, `w3-corpus-empty.json`, `w3-corpus-dropexamples.json`, `w3-corpus-droptests.json` / `.md`. Scratch roots `/tmp/dsf-w3-*`, all outside the repo.

| Boundary re-run | W2 rows | W3 rows | node-id sets | pre-mutation | coll/setup errors | restore |
|---|---|---|---|---|---|---|
| classifier, constructing-lambda arm | 4 | **4** | **identical** (`[lambda-no-args]`, `[lambda-with-kwargs]`, `[lambda-in-a-conditional-expression]`, `[lambda-dotted]`) | green, 54 passed, exit 0 | 0 | `filecmp.cmp(shallow=False) True; sha256 fdb087cf34cc8057... == fdb087cf34cc8057...` |
| classifier, bare-class arm | 5 | **5** | **identical** (`[bare-single]`, `[bare-tuple]`, `[bare-multi-element]`, `[bare-multiline]`, `[bare-assigned-to-a-variable]`) | green, 54 passed, exit 0 | 0 | `filecmp.cmp(shallow=False) True; sha256 fdb087cf34cc8057... == fdb087cf34cc8057...` |
| end-to-end control (one repaired site reverted) | 1 | **1** | **identical** (`::test_no_active_source_uses_a_forbidden_optimizer_extensions_form`) | green, 54 passed, exit 0 | 0 | `filecmp.cmp(shallow=False) True; sha256 9cb2e51742aae0a0... == 9cb2e51742aae0a0...` |
| **corpus, whole tuple emptied** (W3's own probe) | — | **0** | (none) | green, 54 passed, exit 0 | 0 | `sha256 699e24912655f011... == 699e24912655f011...` |
| **corpus, `"examples"` dropped** (W3's own probe) | — | **0** | (none) | green, 54 passed, exit 0 | 0 | `sha256 699e24912655f011... == 699e24912655f011...` |
| **corpus, `"tests"` dropped** (W3's own probe) | — | **0** | (none) | green, 54 passed, exit 0 | 0 | `sha256 699e24912655f011... == 699e24912655f011...` |

**Where the second pair of eyes landed.** Re-run: both classifier arms, the end-to-end control, and three corpus probes of my own. Accepted on Worker 2's record: nothing — every recorded entry was re-run. `git status --porcelain -- scripts/ django_strawberry_framework/` is empty after the last probe, no `ACTIVE-MUTATION.json` or `RESTORE-FAILED.json` exists anywhere under `/tmp` or the repo, and my classifier over the four source trees returns `--- TOTAL 0 sites in 0 files`. **No mutation is live.**

#### Ruling on the 1-row end-to-end control

**Worker 2's framing is legitimate for the object it names, and incomplete.**

Legitimate: `test_no_active_source_uses_a_forbidden_optimizer_extensions_form` is one repo-wide assertion by construction, so *any* reintroduced site anywhere fails exactly one row. More rows are unobtainable except by splitting one property across several assertions, which `BUILD.md` `### Acceptance rule` forbids as a fix ("never a weaker boundary"). The thing that can silently stop discriminating is the **classifier**, and that measures 4 and 5 with disjoint node-id sets I reproduced exactly. Labelling the 1-row entry a control rather than the boundary's pin is the correct call, and the acceptance rule does not bite on it.

Incomplete: the 4+5 rows pin the classifier **against literal snippets**; the 1 row pins the sweep **against the tree as it stands**. Neither pins that the corpus the sweep walks is the corpus it claims to walk. That third surface is new in this diff (`for path in iter_python_sources():`) and it measures **0** — see finding M1. So the answer to "weakly-pinned boundary wearing a different label" is: not the one Worker 2 named, but there is one, and it is measurable.

### High:

None.

### Medium:

#### M1 — the governance sweep's corpus is unpinned: a narrowed corpus makes the gate pass vacuously, and nothing fails

`tests/test_ci_governance.py::test_no_active_source_uses_a_forbidden_optimizer_extensions_form` iterates `scripts/check_citations.py::iter_python_sources()` and asserts the collected `violations` list is empty. `violations` is empty both when the corpus is clean and when the corpus is **empty or narrowed** — the classic fail-open shape `BUILD.md` `### Fail-open shapes` names: "cannot enumerate" is converted into "permit". The 18 control rows feed the classifier literal snippets and never touch the corpus, so no row in this diff can tell the two readings apart.

Measured, not reasoned (`docs/builder/temp-tests/slice-2-029/w3-corpus-droptests.md`). Removing `"tests",` from `scripts/check_citations.py` #"SOURCE_TREES = (":

- **0 rows fail**, 0 collection/setup errors, pre-mutation `54 passed` exit 0, mutant `54 passed` exit 0;
- 136 files leave the gate, **21 of this slice's 25 repaired sites among them**;
- `scripts/check_citations.py` itself stays green — `OK: 649 citations resolve`, exit 0 — so the pre-commit / `.github/workflows/django.yml:53` gate does not catch it either.

The comment at the import claims the coupling means "this pin narrows **visibly** with it". That is true for three of the four trees by accident, not by design: dropping `"examples"`, `"scripts"`, or `"django_strawberry_framework"` happens to break a citation and fail `check_citations` (measured: exit 1 with 2, 1, and 21 unresolvable citations respectively), while dropping `"tests"` — the tree that matters most here — breaks none. The pin's protection is a side effect of where citations happen to point, which is not a contract.

**Why it matters:** this pin's entire reason for existing (maintainer decision D1) is that *a rule with no gate rots*. A gate that can go vacuous without a single failing row is a rule with no gate wearing a gate's name, and it would rot exactly as the one-shot grep did.

**What closes it** (more rows, never a weaker boundary, never a recorded exception — both are Worker 2's own file and need no spec context):

1. A row pinning the corpus against known representatives, one per tree, so a dropped tree fails loudly and by name — e.g. assert that `iter_python_sources()` contains `django_strawberry_framework/optimizer/extension.py`, `tests/test_ci_governance.py`, `examples/fakeshop/strategy_schemas.py`, and one `scripts/*.py`. Under the measured mutation this row fails; today it passes.
2. A row pinning the **find** path independently of the live tree being clean: factor the collection so the sweep's per-path loop is callable with an explicit path list (e.g. `_forbidden_entries_in(paths)` returning the formatted violation strings), then assert it reports a `tmp_path`-written file containing `extensions=[DjangoOptimizerExtension]` **with file and line**. Today the only thing exercising that formatting is the transient end-to-end control, which dies with this cycle.

Test expectation: with (1) in place, the `"tests"`-dropped mutation must fail at least one row; with (2) in place, a classifier that returns `[]` for everything must fail the synthetic-corpus row as well as the 9 snippet rows.

### Low:

#### L1 — the recorded restore hash for both classifier proofs is not the shipped file's hash, and the artifact does not say why

`### Failability proofs` records `sha256 c843c74100c6dcb3... == c843c74100c6dcb3...` for both `tests/test_ci_governance.py` entries. The shipped file hashes `fdb087cf34cc8057...`. The restore itself was genuine — Worker 2's pristine copies at `/tmp/dsf-failability-slice-2-029/pristine/` both hash `c843c741...`, so the byte-comparison proved what it claims — but the file was edited **after** the proofs ran (proofs at 01:39:01, file mtime 01:39:40).

Reconciled by diff: the delta is one constant, `tests/test_ci_governance.py::OPTIMIZER_FIX`, changed from the `OPTIMIZER_EXTENSION.lower()`-derived form to the plain literal — the change Worker 2 records under `### Implementation notes`. It is a failure-message string, outside both mutated arms, so the proofs remain valid for the boundary under review, and my re-run reproduces the same node-id sets against the shipped bytes (`fdb087cf...`).

**What closes it:** one line in `### Failability proofs` saying the proofs were taken before the `OPTIMIZER_FIX` message edit and naming the shipped hash, so a later reader re-deriving the hash does not find a bare mismatch. Nothing in the code changes.

#### L2 — the sweep docstring enumerates the bare-class arm's over-match but not the lambda arm's

`tests/test_ci_governance.py::test_no_active_source_uses_a_forbidden_optimizer_extensions_form`'s "false-positive direction" paragraph names one over-match (the bare-class rule flags the class in any list or tuple literal). The lambda arm has a second, undocumented one: `OPTIMIZER_EXTENSION in ast.unparse(body.func)` is a **substring** test, so `lambda: MyDjangoOptimizerExtensionWrapper()` and any dotted or affixed spelling also flag. The direction is safe and consistent with the stated trade, but the paragraph is the exact place a future reader looks before deciding whether a flag is a bug in the rule — an incomplete enumeration there reads as an exhaustive one.

**What closes it:** extend that sentence to name the substring match on the lambda arm.

#### L3 — three tracked first-party `.py` files sit outside the pin's corpus

`iter_python_sources()` resolves to 426 files across the four `SOURCE_TREES`. `git ls-files '*.py'` outside those trees returns `conftest.py`, `line_count.py`, and `docs/dry/export_dry_review.py`. None constructs a schema today (verified: no `DjangoOptimizerExtension` and no `extensions=` in `conftest.py` or `line_count.py`), but the repo-root `conftest.py` is a plausible future home for a shared schema fixture, and the sweep's docstring and the import comment both read as "every first-party `.py`".

**What closes it:** name the exclusion in the import comment (the corpus is `SOURCE_TREES`, not literally every tracked `.py`), or widen the corpus. Either is fine; the current text is what is inaccurate, not the scope choice.

### DRY findings

**None new.** Checked, with evidence:

- **Consistency with the existing population, re-derived.** `lambda: <name>` elements of a sequence literal across the pin's corpus now number **106** by name: `ext` 66, `optimizer` 24, `_optimizer` 4, `optimizer_ext` 4, `capture_ext` 2, and one each of `cascading_ext` / `plain_ext` / `raising_optimizer` / `silent_optimizer` / `extension` / `MRO_CONTINUE` (the last is an unrelated `lambda: NAME` my broad census sweeps up). Subtracting this slice's 25 — 19 `optimizer`, 4 `optimizer_ext`, `raising_optimizer`, `silent_optimizer` — leaves **81** pre-existing, of which `ext` 66 and `optimizer` 5 are the plurality. Worker 1's "~75 already-correct sites" is the same census under a narrower definition, and its `lambda: _optimizer` figure of 2 re-measures as 4; neither is load-bearing (the slice adds no `_optimizer`). The 25 new sites introduce **no new spelling of the shape**: `optimizer` was already the second-commonest name, and `optimizer_ext` / `raising_optimizer` / `silent_optimizer` are site-descriptive variants of the same two-line idiom, not a second idiom. Worker 1's decision against a shared `optimizer_factory()` helper is not re-litigated; I re-derived its load-bearing premise instead and it holds.
- **The existence challenge is not raised.** The pin's existence is maintainer decision D1, already recorded with its rejected alternatives. The classifier has two real callers (the sweep and the parametrized controls) and the controls are what make the boundary strongly pinned, so inlining it would delete the pin's own test surface.
- **`docs/builder/temp-tests/slice-2-029/classify.py` is a second copy of the pin's rule, not an independent instrument.** Worker 2 says so plainly under `### Implementation notes`, so this is not a finding — but it does mean the "two independent readings" phrase in the build report overstates by one. My `w3-classify.py` is an independent formulation (parent/field-position walk rather than an `id()`-set pre-pass) and it agrees: 25 sites in 8 files at HEAD across the entire `git archive HEAD` tree, 0 in the current four trees, and row-for-row agreement on all 18 control snippets.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` is **empty**; `__all__` and the re-export list are unchanged. `git status --porcelain -- django_strawberry_framework/` is empty — the slice changes no package source at all, consistent with the plan's "No production line changes."

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity (only when the slice touches docs, release metadata, KANBAN, or archived specs)

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. Two adjacent claims verified anyway, because both concern a **script-rendered** doc:

- **`docs/TREE.md` is byte-clean.** `git show HEAD:docs/TREE.md` into a scratch path outside the repo, then `cmp` — identical; `git status --porcelain -- docs/TREE.md` empty; absent from the diff. Worker 2's disclosure of the accidental non-`--check` render and its byte-identical restore is verified true.
- **`docs/TREE.md`'s staleness at HEAD is exactly the concurrent session's, and none of it is this slice's.** Rendered to a scratch copy (`--md <scratch>`, so the real file is never written) and diffed: the entire delta is two lines, both `test_operations.py  # Tests for canonical mutation operation descriptors (operations.py).` at `docs/TREE.md:515` and `:745`, for the concurrent session's untracked `tests/mutations/test_operations.py`. Confirmed and routed, not fixed.
- **Disclosure 3's constraint is real.** `scripts/build_tree_md.py::first_python_docstring_sentence` renders `tests/test_ci_governance.py`'s first docstring line into `docs/TREE.md` at `:455` and `:681`, and `.github/workflows/django.yml` runs `build_tree_md.py --check`. The first line is byte-identical to HEAD. Leaving it and widening the paragraphs below is the correct call under the maintainer's fence; the summary line does now under-describe the module, which Worker 2 already surfaced as Amendment 1 with a replacement and the right routing (deferred catalog, not the spec). Adequate as recorded — see L-tier note under `### Notes for Worker 1`.

### What looks solid

- **Population.** Re-derived independently with my own classifier over the whole `git archive HEAD` tree: **25 sites in 8 files**, 7 bare-class + 18 constructing-lambda, and every line number matches Worker 1's table digit-for-digit. Positive control fired (it found the real sites); current four trees return **0**. Worker 0's original 12-in-6 was indeed a vocabulary sample, and the correction stands.
- **Behavior preservation, verified line by line rather than by grep.** The 8 migrated files' diff is **91 changed lines** and I read all of them: `extensions=` expression substitutions, singleton declarations, `if` blocks, and the one function-docstring rewrite. Not one assertion, marker, skip, or xfail. (Worth recording: the obvious grep for this class is itself unreliable — my first pass with an unquoted `$FILES` in zsh silently diffed nothing and printed a clean "NONE", and my second pass matched `mark` inside the word `benchmark`. The exhaustive changed-line dump is the instrument that actually measures.)
- **No module-level singleton anywhere.** AST audit over all 8 files: every `DjangoOptimizerExtension(...)` construction resolves to a `FunctionDef` / `AsyncFunctionDef` scope; zero at module scope.
- **Non-shadowing, re-derived.** An AST pass over each enclosing function's `Store` names and `arg`s: `optimizer_ext`, `raising_optimizer`, `silent_optimizer` are bound exactly once and are not arguments. The four conditional `tests/test_relay_connection.py` functions (`_genres_list_schema`, `_genres_distinct_book_schema`, `_genres_expression_ordered_schema`, and the nested `_build`) do bind `optimizer` — as the boolean flag, which is exactly why the singleton there is named `optimizer_ext`. No collision.
- **The five conditional sites construct nothing on the `else` path.** All five are `extensions = []` then `if <flag>:` with the construction inside the block — the no-optimizer parametrization builds no optimizer. The rejected one-liner (build always, wrap conditionally) does not appear.
- **The `strictness="raise"` / `strictness="off"` pair carries two separately-named locals** (`raising_optimizer` / `silent_optimizer`) in `tests/optimizer/test_extension.py::test_strictness_flags_a_relation_under_an_unplannable_root`. One instance genuinely could not have carried both values.
- **Scope boundary held.** `git status --porcelain -- django_strawberry_framework/extensions/` is empty; `DjangoDebugExtension` and `DjangoErrorPolicyExtension` are untouched. The pin cannot flag either: both are in the must-not-flag control set, both classifiers return `[]` for them, and the repo-wide sweep is green with the tree's existing bare `DjangoDebugExtension` entries in place. A rule that broke the debug extension's documented required form would have been a High finding; this one does not.
- **The control rows genuinely discriminate.** Cross-checked snippet by snippet against my own classifier: 5 rows fire only the bare arm, 4 fire only the lambda arm, disjoint, and all 9 must-not-flag rows return `[]` under both. All 18 snippets are distinct strings. The 4+5 mutation split is therefore a partition of the must-flag set, not an overlap — which is why neither arm can hide behind the other.
- **Corpus scoping does exclude what it claims.** `iter_python_sources()` resolves to 426 absolute paths across exactly the four `SOURCE_TREES`; zero under `docs/`, zero under any `temp-tests/`. The gitignored `docs/bug_hunt/temp-tests/` (4 forbidden entries) and Worker 2's own `docs/builder/temp-tests/slice-2-029/test_hot_path_budget.py` (which deliberately builds both forbidden forms as its BEFORE reading) are outside by construction — so the gate cannot pass in CI and fail on a developer machine. That is the right answer, not an omission.
- **The import boundary has precedent.** `from scripts.check_citations import ...` joins four existing `tests/ -> scripts/` imports (`test_build_tree_md.py`, `test_build_kanban_html.py`, `test_pg_explain_artifact_footer.py`, and others). Not a structural change.
- **Hot-path number exists and reproduces exactly as recorded.** Re-ran `docs/builder/temp-tests/slice-2-029/test_hot_path_budget.py`: identity `False / False / True`; two instances built under the constructing lambda, `CacheInfo(hits=0, misses=1, size=1)` each, aggregate `misses=2, hits=0`; one instance under the factory, `CacheInfo(hits=1, misses=1, size=1)`, `misses=1, hits=1`. Whether the trade is acceptable is the maintainer's call, not mine.
- **"No new test owed for the mechanism" is true.** `tests/optimizer/test_extension.py::test_cache_hit_on_repeated_query` does assert `misses == 1` then `hits == 1` on a singleton-factory schema, and `::test_singleton_factory_extensions_form_emits_no_deprecation_warning` still pins the no-warning half of Decision 3. A second copy would be duplication.
- **Floor run is verifiable later, and the shared `.venv` is genuinely unmutated.** `/tmp/dsf-floor-029` still exists and reads Python 3.10.19 / Django 5.2.16 / strawberry-graphql 0.316.0 — the recorded numbers, re-read rather than trusted. The shared `.venv` reads Django 6.1 / strawberry-graphql 0.323.2 / Python 3.14.2, i.e. head, not floor; `uv.lock` and `pyproject.toml` are clean.
- **Gates green, independently.** `ruff format --check` (9 files already formatted), `ruff check` (all checks passed), `check_trailing_commas.py --check` (exit 0), `check_citations.py` (`OK: 789 citations resolve`), and the focused suite — `550 passed`, matching Worker 2's number at the same scope.
- **The disclosed `SyntaxError` mutation is the right kind of record.** Worker 2's first constructing-lambda mutation deleted the arm's body, collection-errored, and the tool refused it as `INVALID COUNT` rather than banking a measured zero. That is the fail-open direction `BUILD.md` `### What gets recorded` exists to catch, caught, and disclosed.

### Spec slice checklist audit (all 17 boxes ticked by Worker 2)

Every tick has a matching fix in the diff. Walked individually: population re-derivation (matches my independent 25/8); 7 bare-class migrated; 18 constructing-lambda migrated including all `strictness=` / `nested_connection_strategy=` variants; function-local everywhere (AST-verified, zero module-level); five conditional `else` branches construct nothing; the two-strictness pair carries two locals; `strategy_schemas.py`'s function docstring corrected with its **module** docstring byte-identical to HEAD (`diff` of the first 12 lines: identical); no assertion weakened (91-line exhaustive dump); classifier + sweep present; 9+9 control rows present, green, and discriminating; corpus scoped through `check_citations` with the coupling comment; module docstring widened and the coverage note still accurate; deliberate non-extensions and false-positive direction recorded in the sweep docstring; failability proofs present, audited, and re-run; hot-path budget carries both readings and reproduces; floor verification recorded with `.venv` unmutated; ruff scoped to the nine files with `git status --short` showing only slice-intended paths. **No over-tick, no silently-unaddressed sub-check.**

### Static helper use

`uv run python scripts/review_inspect.py tests/test_ci_governance.py --output-dir docs/shadow` — run. Trigger: the slice adds 213 lines to a `.py` file outside `django_strawberry_framework/`, which crosses the 50-line threshold in `BUILD.md` `### When to run the helper during build`; Worker 2's argument that the addition is "dominated by control-row data and docstrings" is reasonable but is a judgement, so I ran it rather than inherit it. Output: 3 control-flow hotspots (`_forbidden_optimizer_entries` at 36 lines / 8 branch nodes, the sweep at 42 lines / 1 branch node, and one pre-existing workflow test), no Django/ORM markers, 2 repeated string literals (`permissions`, `contents` — both pre-existing YAML keys), and the single new cross-folder import already covered above. Nothing that changes a finding.

**Skips, recorded with reasons.** `tests/optimizer/test_extension.py` and `tests/types/test_resolvers.py` sit under directories named `optimizer/` and `types/`, but that trigger targets `django_strawberry_framework/optimizer/` and `django_strawberry_framework/types/` (Worker 1's clause in the same section spells the package prefix out), and this slice's contribution to each is 1-3 lines of expression substitution with no new logic. The other six files are 2-8 changed lines each, all under both thresholds.

### Temp test verification

- `docs/builder/temp-tests/slice-2-029/w3-classify.py` — my independent population classifier. Kept for this cycle; **not** promoted (it duplicates the permanent pin's rule by construction, which is the point of it being a second instrument and the reason it must not become a second permanent one).
- `docs/builder/temp-tests/slice-2-029/w3-rerun-proofs.json` / `.md`, `w3-rerun-control.json` / `.md` — independent re-runs of Worker 2's three recorded entries at the recorded scope.
- `docs/builder/temp-tests/slice-2-029/w3-corpus-empty.json`, `w3-corpus-dropexamples.json`, `w3-corpus-droptests.json` / `.md` — the three corpus probes behind M1. **These caught a real gap**, so per the temp-test rule the disposition is: recorded as Medium finding M1 for Worker 2 to close with permanent rows; the manifests themselves die with the cycle.
- Worker 2's `test_hot_path_budget.py` re-run unchanged; correctly not promoted.

### Notes for Worker 1 (spec reconciliation)

- **Worker 2's three amendments are sound and correctly routed; I judged them, did not enact them.** Amendment 1 (`tests/test_ci_governance.py`'s first docstring line): the constraint is real — verified that `build_tree_md.py` renders that line into `docs/TREE.md:455` and `:681` and that CI runs `--check` — and routing it to `bld-final-029.md`'s deferred catalog rather than the spec is right, because it is a `docs/TREE.md` item. Amendment 2 (DoD item 4 restated by form, naming the standing pin): well-evidenced, and its measured population (25 in 8 files before, 0 after) matches my independent re-derivation exactly; the new `[test-ci-governance]: ../../tests/test_ci_governance.py` link def resolves correctly from `docs/SPECS/`. Amendment 3 (Decision 3's granularity example): the same-function `strictness="raise"` / `"off"` pair is real and is a strictly better example than the cross-module one; the spec's `~41` in that sentence is one of the stale census figures already flagged as build-plan divergence 9.
- **Escalated: Amendment 2 names one of two parallel sites.** The one-shot-grep framing lives in the spec **twice** — `## Definition of done` item 4 (which Amendment 2 quotes) and `## Slice checklist` `#"Post-migration forbidden-form gate:"`, which says "after the rewrite, a grep for the **exact forbidden forms** finds zero hits". Restating only item 4 leaves the checklist still describing the instrument that under-reported this regression by 13 of 18 sites. Resolution paths for Slice 3: (a) restate both sites by form and point both at the standing pin; (b) restate item 4 and delete the checklist bullet's gate clause as superseded; (c) leave the checklist bullet as a `## Current state`-style historical snapshot and say so explicitly. I have no preference the spec context does not decide — but leaving it unnamed would be the parallel-site skip this cycle's own memory calls the dominant residual defect, so it should be a decided answer either way.
- **M1 is Worker 2's to close and needs no spec context** — it lands entirely in `tests/test_ci_governance.py`. Noted here only so final verification can check the follow-through: whatever Slice 3 writes into DoD item 4 will claim the gate is "enforced continuously", and that claim is only as strong as the corpus the gate walks.
- **L3 touches nothing the spec says**, but if Slice 3's DoD replacement uses the phrase "active first-party source", it is worth making that phrase mean `SOURCE_TREES` explicitly rather than "every tracked `.py`", since three tracked `.py` files sit outside it.

### Review outcome

`revision-needed`.

One Medium (M1) and three Lows (L1, L2, L3), all closable inside `tests/test_ci_governance.py` and the artifact, none requiring spec context. Routes back to **Worker 2**.

The repair itself is correct and I found nothing wrong with it: the population is right, the migration is behavior-preserving line by line, no module-level singleton exists, the conditional `else` branches construct nothing, the scope boundary around `DjangoDebugExtension` holds, and the classifier is strongly pinned at 4 and 5 rows with node-id sets I reproduced exactly. What is not yet pinned is the gate's reach: with `"tests"` dropped from `SOURCE_TREES`, 21 of the 25 sites this slice just repaired silently leave the gate's corpus, all 54 rows pass, and `check_citations` stays green. That is a 0-row boundary in the diff, and `BUILD.md` `### Acceptance rule` makes it `revision-needed` — the fix being more rows, never a weaker boundary and never a recorded exception.

---

## Build report (Worker 2, pass 2)

Apply-changes pass closing Worker 3's M1 plus L1, L2 and L3. **The eight migrated files were not touched**: no Low required it, and nothing Worker 3 verified as already correct (the 25-site population, the 91 changed lines, the five conditional `else` branches, the scope boundary around `DjangoDebugExtension`, the hot-path number, the floor venv) was re-done or disturbed. The whole diff of this pass is one file.

### Files touched

Grounded in `git status --short` after both ruff invocations (below).

- `tests/test_ci_governance.py` — the only changed file. Four additions: the widened corpus (`EXTRA_SOURCE_FILES`, `_sweep_corpus`), the git-derived corpus census (`_committable_python_files`), the extracted reporter (`_forbidden_entries_in`), and 15 new test rows (1 census + 11 named-reach + 2 planted-violation + 1 planted-permitted). Two docstring/comment corrections (L2, L3).

Unchanged and deliberately so: `scripts/check_citations.py` (byte-identical to HEAD — verified by `git show HEAD:scripts/check_citations.py` into `/tmp/dsf-p2-check-citations-head.py` then `cmp`, exit 0, after it was transiently mutated for proof #1), `docs/TREE.md`, every `django_strawberry_framework/**` module, and all eight migrated test files.

### M1 — the governance gate's corpus is unpinned (closed)

**Re-derived before acting, not accepted.** The finding's measurement reproduces exactly: `git ls-files --cached --others --exclude-standard -- '*.py'` returns **429** committable `.py` files, `iter_python_sources()` returned **426**, `tests/` contributes **136** of them and `examples/` **159** — Worker 3's figures, digit for digit. The three-file gap is L3's, below.

**What was built, and why it is not the two sentences.** Worker 3 named two rows; `BUILD.md` `### Fail-open shapes` says to **guard the answer, not one spelling of the incoherent input**, and a representative-per-tree row is four spellings of "a tree was dropped" — it survives a *depth* narrowing (`rglob` to `glob`, a filter added) that keeps the representative and loses the subdirectories. The answer the gate gives is "no forbidden form exists in first-party source", and that answer is only as true as the corpus is **complete**. So the guard is a **census against an independent oracle**:

1. **`test_the_sweep_corpus_covers_every_committable_python_file`** — asserts every `.py` path git reports as *tracked, plus untracked but not ignored* is inside the sweep's corpus, and names the missing files when it is not. The oracle is git, not the sweep's own tree list, which is what makes the row a measurement rather than a restatement of the corpus by itself. Precedent for the flag set: `scripts/check_trailing_commas.py` #"``--cached --others --exclude-standard`` is exactly" already uses it as this repo's definition of "the set of paths a commit can contain".
   - **Only the missing direction is asserted.** A path the corpus holds and git does not list (gitignored scratch inside a source tree) makes the gate *stricter*, never blinder; asserting set equality would fail on a developer machine and pass in CI, which is the environment-dependent gate the plan's corpus choice exists to avoid.
   - **No fallback when git cannot answer.** A missing `git` raises rather than reducing the census to nothing — the exact fail-open reading this section exists to make impossible.
2. **`test_the_sweep_corpus_reaches_each_load_bearing_file`** — 11 parametrized rows naming, individually, the files the gate's answer rests on: the optimizer's own module, the module that defines the corpus, one file per source tree, the file the widening adds, and all eight modules the repair edited. These say *which* files a narrowing cost, and they hold on a machine without git.
3. **`test_the_sweep_reports_a_planted_violation_with_its_file_and_line`** (2 rows) and **`test_the_sweep_reports_nothing_for_a_planted_permitted_form`** (1 row) — Worker 3's second ask. The collection loop is factored into `_forbidden_entries_in(paths)`, so a synthetic one-file corpus under `tmp_path` exercises the find-and-format path with file and line. Until now the only thing exercising that formatting was the transient end-to-end control, which dies with this cycle.

**Two instruments, proved to be two rather than one written twice.** They differ in oracle (git subprocess vs. hardcoded names), in failure text, and — measurably — in what they catch: proof #1 fails the census *and* 6 reach rows; proof #2 fails the census *and* exactly 1 reach row. Neither is a copy of the other's reading.

**The census's own positive control fired.** Proof #2 restores the pre-widening corpus exactly (the `EXTRA_SOURCE_FILES` half removed) and the census fails, naming `conftest.py`, `docs/dry/export_dry_review.py`, `line_count.py`. So the census demonstrably detects the state the repository was in one hour ago; it is not a row that has never discriminated anything.

**Worker 3's stated test expectation, met:** with the corpus rows in place, the `"tests"`-dropped mutation fails **7** rows where it previously failed 0; with the reporter row in place, a classifier that reports nothing fails **2** rows the live-tree sweep cannot.

**The sweep's own row now says what it cannot see**, in its docstring: it is green over an empty corpus, and the census plus the reach rows are what make its silence mean something.

### L1 — the recorded restore hash did not match the shipped file (closed by re-proving)

Worker 3's reconciliation is confirmed and the record is corrected rather than annotated, because re-proving was the cleaner half: **this pass's additions change the classifier arms' failing-row sets** (the planted-violation rows route through the classifier), so pass 1's node-id lists would have been stale as well as its hashes. Both arms were therefore re-run in this pass against the shipped bytes and are recorded fresh under `### Failability proofs` below.

For the record a later reader will re-derive: pass 1's `c843c741…` is the pre-`OPTIMIZER_FIX`-edit content of `tests/test_ci_governance.py`; the file was edited after those proofs ran (the message-literal change pass 1 records under `### Implementation notes`), which is why the shipped bytes hashed `fdb087cf…` as Worker 3 measured. Neither hash describes the file any more: **the shipped file after this pass hashes `e56acf972ef67c6fb561419704c7d65b163cb6cc317c8b8e4a74d1ae1e150a15`**, and every proof entry below was taken against those bytes. The mutation sites were outside the edited constant in both cases, which is why pass 1's *verdicts* stood; the pass-2 re-runs replace them anyway so the record and the file agree without a reader having to apply a chronology.

### L2 — the sweep docstring's false-positive enumeration was incomplete (closed)

`test_no_active_source_uses_a_forbidden_optimizer_extensions_form`'s "false-positive direction" paragraph now names **both** arms' over-matches: the bare-class rule flagging the class in any list or tuple literal (as before), and the lambda arm's `OPTIMIZER_EXTENSION in ast.unparse(body.func)` **substring** test, which catches a dotted spelling on purpose and an affixed one (`lambda: MyDjangoOptimizerExtensionWrapper()`) as a side effect. The paragraph is the place a future reader looks before deciding whether a flag is a bug in the rule, so it now reads as the exhaustive enumeration it presented itself as.

### L3 — three tracked `.py` files sat outside a corpus the docstring called "every first-party `.py`" (closed by widening)

Worker 3 offered either half; the corpus was **widened**, because that makes the claim true instead of narrowing it, and because the repo-root `conftest.py` — the file Worker 3 named as a plausible future home for a shared schema fixture — is worth covering on its merits, not only for the docstring's sake. `EXTRA_SOURCE_FILES` adds `conftest.py`, `docs/dry/export_dry_review.py`, `line_count.py`; `_sweep_corpus()` is the union, filtered to files that exist. None of the three contains `DjangoOptimizerExtension` or `extensions=` today (re-verified by grep, exit 1), so the widening adds reach and no new violation.

The import comment is corrected in the same change: it now states the true scope (the four `SOURCE_TREES`, which is not literally every first-party `.py`), names the three modules that sit outside them, and points at the census as what pins the union. **The hardcoded three-tuple cannot rot silently**: a new `.py` landing outside the trees fails the census by name, with the message saying to add the tree to `SOURCE_TREES` or the file to `EXTRA_SOURCE_FILES`.

### Tests added or updated

All permanent, all in `tests/test_ci_governance.py`. 54 rows before this pass, **69 after**; no row was removed, weakened, renamed, or re-scoped.

- `::test_the_sweep_corpus_covers_every_committable_python_file` — pins that no `.py` a commit can contain sits outside the sweep's corpus.
- `::test_the_sweep_corpus_reaches_each_load_bearing_file` — 11 rows, ids are the repo-relative paths, pinning corpus membership by name.
- `::test_the_sweep_reports_a_planted_violation_with_its_file_and_line` — 2 rows (`bare-class`, `constructing-lambda`) over a `tmp_path` corpus, asserting exactly one violation reported and that it starts with `<file>:3: <form>: `.
- `::test_the_sweep_reports_nothing_for_a_planted_permitted_form` — the reporter's negative direction.

`::test_no_active_source_uses_a_forbidden_optimizer_extensions_form` keeps its name, its assertion message and its contract; its body now reads `violations = _forbidden_entries_in(_sweep_corpus())`, which is the same computation through the two named seams the new rows pin.

### Validation run

- `uv run ruff format tests/test_ci_governance.py` — pass (`1 file left unchanged` on the final invocation). Never `.`.
- `uv run ruff check tests/test_ci_governance.py` — pass (`All checks passed!`); the earlier `--fix` invocation fixed 1.
- `uv run python scripts/check_trailing_commas.py tests/test_ci_governance.py` then `--check` — pass. The auto-fixer collapsed the 3-element `EXTRA_SOURCE_FILES` tuple to one line (under the explode threshold of 4); run rather than guessed, per the scope notes.
- `uv run python scripts/check_citations.py` — pass, `OK: 789 citations resolve (712 in 426 .py files, 77 in KANBAN.md)`.
- `git status --short` after both ruff invocations — `tests/test_ci_governance.py` plus exactly the out-of-scope paths already recorded (Slice 1's spec/rationale/artifact/plan files, and the concurrent session's `docs/review/review-0_0_14.md`, `docs/review/rev-*.md`, `tests/mutations/test_operations.py`), plus the eight migrated files still dirty from pass 1. **No unexpected churn; nothing reverted.**
- `uv run pytest tests/test_ci_governance.py --no-cov -q -p no:cacheprovider` — **69 passed**.
- `uv run pytest tests/test_ci_governance.py tests/test_relay_connection.py tests/optimizer/test_extension.py tests/forms/test_resolvers.py tests/types/test_resolvers.py tests/mutations/test_write_transaction.py tests/mutations/test_resolvers.py examples/fakeshop/test_query/test_products_visibility_api.py --no-cov -q -p no:cacheprovider` — **565 passed** (pass 1's 550 plus this pass's 15 rows; no pre-existing row changed state).
- **Sibling importers, per `## Apply-changes verification scope`:** `grep -rln check_citations tests/ scripts/ examples/` returns only `tests/test_ci_governance.py` and the script itself, so the focused run above is the complete importer set. The changed surface is otherwise module-private.
- **Test-staleness full sweep: not owed.** This pass changes no example-model field set and no wire shape; every changed line is inside one governance test module.
- **`docs/TREE.md` untouched and unaffected.** `git status --short -- docs/TREE.md` is empty; the generator was run only through `--check`, and once against a **copy outside the repo** (`cp docs/TREE.md /tmp/dsf-p2-tree.md` then `--md /tmp/dsf-p2-tree.md`) to confirm the delta is still exactly the concurrent session's two `test_operations.py` lines at `:515` and `:745` and nothing of this pass's.

### Failability proofs

Five entries, produced by `uv run python scripts/prove_failability.py docs/builder/temp-tests/slice-2-029/proofs-pass2.json --output docs/builder/temp-tests/slice-2-029/proofs-pass2.md` (tool exit **0** — no entry weakly pinned, no collection/setup error). Anchors were checked with `--check-anchors-only` first; all five matched exactly once. Scratch root `/tmp/dsf-failability-slice-2-029-pass2`, **outside** the repo. One mutation live at a time, each restored and byte-proved before the next. **Scope as run, identical for all five:** `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_ci_governance.py`. **Pre-mutation state of that scope, for all five:** green, `69 passed`, pytest exit 0, 0 pre-existing failing rows differenced out. **Collection/setup errors: 0 in every entry.**

Entries 1-3 are this pass's new boundaries. Entries 4-5 re-prove the classifier arms against the shipped bytes, because this pass's additions changed their failing-row sets (see L1).

1. **Corpus completeness — `scripts/check_citations.py::SOURCE_TREES` narrowed by one tree.** Mutation applied: `"tests",` removed from the four-element tuple, so 136 files — most of the sites this slice repaired — leave the sweep's corpus while `check_citations` itself stays green. This is the exact narrowing Worker 3 measured at **0** failing rows. Failing node ids (**7**):
   - `tests/test_ci_governance.py::test_the_sweep_corpus_covers_every_committable_python_file`
   - `tests/test_ci_governance.py::test_the_sweep_corpus_reaches_each_load_bearing_file[tests/forms/test_resolvers.py]`
   - `tests/test_ci_governance.py::test_the_sweep_corpus_reaches_each_load_bearing_file[tests/mutations/test_resolvers.py]`
   - `tests/test_ci_governance.py::test_the_sweep_corpus_reaches_each_load_bearing_file[tests/mutations/test_write_transaction.py]`
   - `tests/test_ci_governance.py::test_the_sweep_corpus_reaches_each_load_bearing_file[tests/optimizer/test_extension.py]`
   - `tests/test_ci_governance.py::test_the_sweep_corpus_reaches_each_load_bearing_file[tests/test_relay_connection.py]`
   - `tests/test_ci_governance.py::test_the_sweep_corpus_reaches_each_load_bearing_file[tests/types/test_resolvers.py]`

   Mutant `7 failed, 62 passed`, pytest exit 1. Revert proved by byte-comparison: `filecmp.cmp(shallow=False) True; sha256 699e24912655f011... == 699e24912655f011...`, and independently re-checked against HEAD with `git show HEAD:scripts/check_citations.py` + `cmp` (exit 0) because that file is outside this slice's writable list and was only borrowed for the mutation.

2. **`tests/test_ci_governance.py::_sweep_corpus` — the outside-the-trees half removed.** Mutation applied: `EXTRA_SOURCE_FILES` replaced by `()` in the corpus union, so `conftest.py`, `docs/dry/export_dry_review.py` and `line_count.py` leave the gate — i.e. the corpus is restored to exactly its pre-L3 shape. Failing node ids (**2**):
   - `tests/test_ci_governance.py::test_the_sweep_corpus_covers_every_committable_python_file`
   - `tests/test_ci_governance.py::test_the_sweep_corpus_reaches_each_load_bearing_file[conftest.py]`

   Mutant `2 failed, 67 passed`, exit 1. Revert: `filecmp.cmp(shallow=False) True; sha256 e56acf972ef67c6f... == e56acf972ef67c6f...`. This entry doubles as the census's positive control: it reproduces the repository's state before this pass and the census detects it.

3. **`tests/test_ci_governance.py::_forbidden_entries_in` — the find-and-format path stops reporting.** Mutation applied: `return violations` replaced by `return []`, so no corpus ever produces a violation — a state textually indistinguishable from a clean tree at the sweep's own row. Failing node ids (**2**):
   - `tests/test_ci_governance.py::test_the_sweep_reports_a_planted_violation_with_its_file_and_line[bare-class]`
   - `tests/test_ci_governance.py::test_the_sweep_reports_a_planted_violation_with_its_file_and_line[constructing-lambda]`

   Mutant `2 failed, 67 passed`, exit 1. Revert: `filecmp.cmp(shallow=False) True; sha256 e56acf972ef67c6f... == e56acf972ef67c6f...`. Note the sweep's own row passes under this mutation, which is precisely why the boundary needed a synthetic corpus.

4. **`tests/test_ci_governance.py::_forbidden_optimizer_entries` (constructing-lambda arm), re-proved.** Mutation applied: the arm's `if isinstance(node, ast.Lambda):` guard replaced by `if False:` with the body intact. Failing node ids (**5**, up from pass 1's 4):
   - `…::test_forbidden_optimizer_form_classifier_flags_every_forbidden_shape[lambda-no-args]`
   - `…::test_forbidden_optimizer_form_classifier_flags_every_forbidden_shape[lambda-with-kwargs]`
   - `…::test_forbidden_optimizer_form_classifier_flags_every_forbidden_shape[lambda-in-a-conditional-expression]`
   - `…::test_forbidden_optimizer_form_classifier_flags_every_forbidden_shape[lambda-dotted]`
   - `…::test_the_sweep_reports_a_planted_violation_with_its_file_and_line[constructing-lambda]`

   Mutant `5 failed, 64 passed`, exit 1. Revert: `filecmp.cmp(shallow=False) True; sha256 e56acf972ef67c6f... == e56acf972ef67c6f...`. The set is pass 1's four rows **plus** the new planted row; nothing was lost.

5. **`tests/test_ci_governance.py::_forbidden_optimizer_entries` (bare-class-in-a-sequence arm), re-proved.** Mutation applied: the whole five-clause condition replaced by `if False:`. Failing node ids (**6**, up from pass 1's 5):
   - `…::test_forbidden_optimizer_form_classifier_flags_every_forbidden_shape[bare-single]`
   - `…::test_forbidden_optimizer_form_classifier_flags_every_forbidden_shape[bare-tuple]`
   - `…::test_forbidden_optimizer_form_classifier_flags_every_forbidden_shape[bare-multi-element]`
   - `…::test_forbidden_optimizer_form_classifier_flags_every_forbidden_shape[bare-multiline]`
   - `…::test_forbidden_optimizer_form_classifier_flags_every_forbidden_shape[bare-assigned-to-a-variable]`
   - `…::test_the_sweep_reports_a_planted_violation_with_its_file_and_line[bare-class]`

   Mutant `6 failed, 63 passed`, exit 1. Revert: `filecmp.cmp(shallow=False) True; sha256 e56acf972ef67c6f... == e56acf972ef67c6f...`.

**No zero-row entry**, so no `why 0` judgement is owed anywhere in this record. **No mutation is live:** `/tmp/dsf-failability-slice-2-029-pass2/` holds only `pristine/` (no `ACTIVE-MUTATION.json`, no `RESTORE-FAILED.json`), `scripts/check_citations.py` is byte-identical to HEAD, the shipped `tests/test_ci_governance.py` hashes `e56acf97…`, and the focused suite is green at 69.

**The end-to-end control from pass 1 is not repeated.** It reintroduced a forbidden form at one repaired site and observed the sweep's single repo-wide row fail; it was 1 row by construction, Worker 3 ruled that framing legitimate for the object it names, and nothing in this pass changes it. Its incompleteness — that it pinned the sweep against the tree as it stands, not the corpus against itself — is exactly what entries 1-3 now cover.

### Hot-path budget

**No new number is owed.** This pass adds test-only guard rows and changes no production line; the plan's declared metric (`DjangoOptimizerExtension.cache_info()` across two executions on one schema) stands from pass 1 at `misses 2 -> 1`, `hits 0 -> 1`, and Worker 3 reproduced it exactly. Nothing this pass touches is on a request path: the census shells out to `git` once per test session, inside `tests/test_ci_governance.py` only.

### Floor verification

Re-run **only** the scope this pass's rows touch, per the apply-changes instruction. The venv from pass 1 was reused as-is; **no install was performed in this pass**, so the shared `.venv` could not be reached — it still reads Django 6.1 / strawberry-graphql 0.323.2 (`uv pip list`), i.e. head, not floor, and `uv.lock` and `pyproject.toml` are unmodified.

Versions re-read rather than trusted, with `uv pip list --python /tmp/dsf-floor-029/bin/python` and `/tmp/dsf-floor-029/bin/python -V`:

```
Python 3.10.19
django                      5.2.16
pytest                      9.1.1
strawberry-graphql          0.316.0
```

| Command | Result |
|---|---|
| `/tmp/dsf-floor-029/bin/python -m pytest tests/test_ci_governance.py --no-cov -q -p no:cacheprovider` | **PASS** — `69 passed in 3.02s` |

The new rows use `subprocess.run(..., text=True)`, `Path.is_relative_to` (3.9+) and `str.split("\0")` — all available at the floor, confirmed by execution rather than by reading a version table.

### Implementation notes

- **Why a git oracle rather than a filesystem walk.** The census needs a definition of "first-party source" that is *not* the sweep's own, or it restates the corpus by itself. Walking the filesystem from the repo root would reintroduce exactly the environment-dependence the plan's corpus choice avoids (a developer's gitignored scratch would enter the census). `--cached --others --exclude-standard` is "tracked, plus untracked but not ignored" — the set of paths a commit can contain — and `scripts/check_trailing_commas.py` already establishes it as this repo's answer to that question, so the shape is borrowed, not invented.
- **Subset, not equality, and the asymmetry is deliberate.** `oracle - corpus` is the defect direction; `corpus - oracle` (today empty, but non-empty the moment anyone drops a gitignored `.py` inside a source tree) can only make the gate stricter. Asserting equality would have made the row fail on a developer machine and pass in CI — the failure mode the plan's Step 4 already calls out for the gate itself.
- **`_sweep_corpus()` exists as a named seam, not for tidiness.** Three callers (the sweep, the census, the reach rows) and it is the object the census makes a claim about. It also gives the corpus a single mutation site, which is what let proof #2 remove the widening cleanly without touching `check_citations`.
- **`_forbidden_entries_in(paths)` takes paths, while `_forbidden_optimizer_entries(source, label)` keeps taking text.** The split is the same reasoning the plan gave for the text-plus-label signature: the classifier's controls need literal snippets, and the reporter's controls need real files with real line numbers. Two seams, two control sets, and the proofs show they fail on disjoint mutations.
- **`display = path.relative_to(REPO_ROOT) if path.is_relative_to(REPO_ROOT) else path`.** A `tmp_path` corpus is outside the repository, so the unconditional `relative_to` the sweep used would have raised. The fallback is the absolute path, which is what a synthetic corpus should print anyway; the planted rows assert on it, so the branch is pinned rather than merely present.
- **Corpus widening vs. the plan's DRY decision.** The plan (and the ticked checklist box) says the pin scopes its corpus *through* `check_citations`'s source-tree definition, with the coupling named in a comment. That is still exactly what it does — `iter_python_sources()` remains the corpus's spine and the comment still names the coupling. `EXTRA_SOURCE_FILES` adds three named files the shared definition does not reach; it is not a second definition of the trees, and the census is what stops it becoming one. Surfaced under `### Notes for Worker 1` so the box audit is not left to inference.
- **Row count kept honest.** 15 new rows for one Medium and three Lows is more than Worker 3's two sentences asked for; 11 of them are one parametrization whose data is a list of paths. The alternative — a single set-comparison row — is what produced a 7-row proof collapsing to 1, and a 1-row boundary is what the acceptance rule refuses.

### Notes for Worker 3

- **Where to look hardest.** The census row is the one thing in this diff that can go quietly vacuous in the other direction: if `_committable_python_files()` ever returned an empty set, `missing` would be empty and the row would pass. It cannot today — `returncode != 0` asserts, a missing `git` raises `FileNotFoundError`, and an empty repository is not a state this suite runs in — but that is the shape to attack. A useful probe: make the helper return `set()` and confirm the row passes, then decide whether that is a finding or the boundary's floor (my reading: the reach rows are the second instrument that still fails in that world, which is why they exist).
- **Proof #1 mutates a file outside this slice's writable list**, `scripts/check_citations.py`, transiently and by the tool. It is the realistic narrowing the finding was measured on, so proving the guard anywhere else would have proved a different thing. It is restored, byte-proved by the tool, and *additionally* re-checked against `git show HEAD:` (exit 0) — recorded here rather than left for you to notice.
- **Re-running:** `uv run python scripts/prove_failability.py docs/builder/temp-tests/slice-2-029/proofs-pass2.json` reproduces all five entries at the recorded scope; `--check-anchors-only` gives the precondition without the runs. Pass 1's `proofs.json` / `control.json` still exist and still reproduce *their* verdicts, but their node-id sets are pre-this-pass and entries 4-5 above supersede them.
- **`scripts/review_inspect.py` was not run by this pass.** The addition is ~130 lines to a `.py` file outside `django_strawberry_framework/` — above the 50-line trigger — but you ran the helper on this exact module last pass and its findings (3 control-flow hotspots, no ORM markers, 2 pre-existing repeated literals) are recorded in your own review section. Re-running it is yours to judge; I did not inherit the skip, I am naming that the trigger fires and that I left it to the pass that owns the independent reading.
- **Temp artifacts**, under the gitignored `docs/builder/temp-tests/slice-2-029/`: `proofs-pass2.json` / `proofs-pass2.md` are this pass's; everything else there is pass 1's or yours. None is promoted.

### Notes for Worker 1 (spec reconciliation)

- **No spec text was read as false by this pass and no spec edit is requested.** Pass 1's Amendments 1-3 stand exactly as written; Worker 3 judged all three sound and correctly routed, and nothing here changes them.
- **Checklist-box wording, for the final-verification audit (small, mechanically obvious drift — implemented, not paused).** Box 11 reads *"The pin scopes its corpus through `scripts/check_citations.py`'s first-party source-tree definition, with the coupling named in a comment."* It stays ticked and stays true: `iter_python_sources()` is still the corpus's spine and the comment still names the coupling. What the box does not anticipate is that the corpus is now that definition **plus three named files outside those trees** (`conftest.py`, `docs/dry/export_dry_review.py`, `line_count.py`), which is the fix Worker 3's L3 offered as one of two acceptable halves. **Recommended replacement, should you want the box to describe what shipped:** *"The pin scopes its corpus through `scripts/check_citations.py`'s first-party source-tree definition plus the tracked modules outside those trees, with the coupling named in a comment and the union pinned by a census against git."* Recorded rather than edited, because box text is not Worker 2's to change.
- **Worker 3's escalation about Amendment 2's parallel site is Slice 3's and was not acted on**, per the dispatch. Noting only that its premise is now stronger, not weaker: whatever Slice 3 writes into `## Definition of done` item 4 will claim the gate is enforced continuously, and after this pass that claim rests on a corpus that fails loudly when it narrows rather than on where citations happen to point.
- **If Slice 3's DoD replacement uses the phrase "active first-party source"** (Worker 3's L3 note), it can now mean something exact: every `.py` path `git ls-files --cached --others --exclude-standard` reports, which is what `tests/test_ci_governance.py::test_the_sweep_corpus_covers_every_committable_python_file` asserts the gate covers.

---

## Review (Worker 3, pass 2)

### Failability re-run — mutations pre-registered BEFORE they are made

`worker-3.md` "Reading is necessary, not sufficient". Every mutation below is recorded here before it is applied, applied one at a time, reverted inside this same pass, and the revert proved by byte-comparison. Anchor check precedes every pristine copy (`scripts/prove_failability.py` enforces the order; all anchors verified to match exactly once first). Scratch roots are outside the repository. No `git checkout` / `git restore` / `git stash` / `git worktree` at any point.

**Mandatory floor.** Worker 2 records five entries at **7 / 2 / 2 / 5 / 6** rows. Entries 2 and 3 are at or under the 3-or-fewer floor, so both are mandatory. Entry 1 is above the floor and is re-run anyway: it is the single measurement that proves M1 closed, and my predecessor measured that exact narrowing at **0**. Entries 4 and 5 are re-run as well, because this pass's new rows are claimed to have changed their failing-row **sets** (4 -> 5 and 5 -> 6) and a set claim is not auditable from a number.

Re-runs of Worker 2's records (manifest `docs/builder/temp-tests/slice-2-029/w3p2-rerun.json`, scratch root `/tmp/dsf-w3p2-rerun`):

1. `scripts/check_citations.py` #"SOURCE_TREES = (" — drop `"tests",` from the four-element tuple. (Worker 2 entry 1; expected 7.)
2. `tests/test_ci_governance.py::_sweep_corpus` — `EXTRA_SOURCE_FILES` replaced by `()` in the union. (Worker 2 entry 2; expected 2.)
3. `tests/test_ci_governance.py::_forbidden_entries_in` — `return violations` replaced by `return []`. (Worker 2 entry 3; expected 2.)
4. `tests/test_ci_governance.py::_forbidden_optimizer_entries` (constructing-lambda arm) — the arm's guard replaced by `if False:`, body intact. (Worker 2 entry 4; expected 5.)
5. `tests/test_ci_governance.py::_forbidden_optimizer_entries` (bare-class arm) — the five-clause condition replaced by `if False:`. (Worker 2 entry 5; expected 6.)

**Narrowings neither pass has tried** (manifest `docs/builder/temp-tests/slice-2-029/w3p2-probes.json`, scratch root `/tmp/dsf-w3p2-probes`). `BUILD.md` `### Fail-open shapes` — a guard written against one *spelling* of incoherent input is a guess, so the new corpus guard is tested against narrowings other than the tree-drop it was built on:

6. **Empty tuple.** `scripts/check_citations.py` #"SOURCE_TREES = (" -> `SOURCE_TREES = ()`. Measured at **0 rows** by my predecessor before this pass.
7. **Depth narrowing.** `scripts/check_citations.py::iter_python_sources` #"rglob" -> `glob`, so each tree contributes only its top-level `.py` files. This is the narrowing Worker 2 argues a representative-per-tree row would survive; the claim is that the census does not.
8. **A glob that matches nothing.** `scripts/check_citations.py::iter_python_sources` #"rglob" pattern `"*.py"` -> `"*.nomatch"`, so all four trees contribute nothing while the tuple still names them.
9. **An oracle that answers nothing.** `tests/test_ci_governance.py::_committable_python_files` #"return {name for name in completed.stdout" -> `return set()`. The census's own fail-open direction: an empty oracle makes `oracle - corpus` empty and the row passes.
10. **An oracle that raises.** `tests/test_ci_governance.py::_committable_python_files` — the `"git"` argv element replaced by a binary that does not exist, so `subprocess.run` raises `FileNotFoundError`. Tests whether "no fallback when git cannot answer" is genuinely fail-closed.

**Scope as run, identical for all ten and identical to Worker 2's recorded scope:** `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_ci_governance.py`.

#### Re-run results — node-id SETS, not totals

Instruments under `docs/builder/temp-tests/slice-2-029/`: `w3p2-rerun.json` / `.md`, `w3p2-probes.json` / `.md` (failability manifests), `w3p2-corpus.py` (independent corpus/oracle re-derivation), `w3p2-claims.py` (docstring-claim controls). Scratch roots `/tmp/dsf-w3p2-rerun`, `/tmp/dsf-w3p2-probes`, both outside the repo. All ten anchors verified to match **exactly once** with `--check-anchors-only` before any mutation was applied.

| Entry | W2 rows | W3 rows | node-id sets | pre-mutation | coll/setup errors | restore |
|---|---|---|---|---|---|---|
| 1 — `SOURCE_TREES` drops `"tests"` | 7 | **7** | **identical** (census + the 6 `tests/` reach rows) | green, 69 passed, exit 0 | 0 | `filecmp.cmp(shallow=False) True; sha256 699e24912655f011... == 699e24912655f011...` |
| 2 — `_sweep_corpus` drops `EXTRA_SOURCE_FILES` | 2 | **2** | **identical** (census + `[conftest.py]`) | green, 69 passed, exit 0 | 0 | `... e56acf972ef67c6f... == e56acf972ef67c6f...` |
| 3 — `_forbidden_entries_in` returns `[]` | 2 | **2** | **identical** (both planted-violation rows) | green, 69 passed, exit 0 | 0 | `... e56acf972ef67c6f... == e56acf972ef67c6f...` |
| 4 — classifier, constructing-lambda arm | 5 | **5** | **identical** (4 lambda control rows + `planted…[constructing-lambda]`) | green, 69 passed, exit 0 | 0 | `... e56acf972ef67c6f... == e56acf972ef67c6f...` |
| 5 — classifier, bare-class arm | 6 | **6** | **identical** (5 bare control rows + `planted…[bare-class]`) | green, 69 passed, exit 0 | 0 | `... e56acf972ef67c6f... == e56acf972ef67c6f...` |

**Where the second pair of eyes landed.** Re-run: **all five** of Worker 2's entries, at the recorded scope, compared as node-id sets. Accepted on Worker 2's record: **nothing**. The headline number is confirmed: the `"tests"`-dropped narrowing my predecessor measured at **0 rows** now fails **7**, and the failing set is the census plus every `tests/` reach row — i.e. the rows name which files left, which is the property the fix claimed. The 4 -> 5 and 5 -> 6 growth on the classifier arms is real and is exactly the planted row of the matching form joining each set; nothing from pass 1's sets was lost.

Two entries measure 2 rows and I satisfied myself they are two independent rows, not one assertion parametrized twice: entry 2's rows come from **different tests with different oracles** (the git census, and the hardcoded `[conftest.py]` reach row); entry 3's two rows are one parametrization but over **different classifier arms** — `[bare-class]` and `[constructing-lambda]` — and entries 4 and 5 prove those arms are separable, since each kills exactly one of the two.

#### Narrowings neither pass had tried

The point of `BUILD.md` `### Fail-open shapes` is that a guard proved against one *spelling* of incoherent input is a guess. Four narrowings other than the tree-drop, plus the oracle's own two failure modes:

| Probe | Rows | Failing set (abbreviated) | Reading |
|---|---|---|---|
| 6 — `SOURCE_TREES = ()` | **11** | census + all 10 in-tree reach rows | was **0** before this pass |
| 7 — depth narrowing, `rglob` -> `glob` | **9** | census + 8 reach rows | **Worker 2's depth claim verified**: the corpus keeps every tree name and every top-level file, and the census still fails |
| 8 — a glob matching nothing (`*.py` -> `*.nomatch`) | **11** | census + all 10 in-tree reach rows | trees still named, corpus empty, caught |
| 9 — the git oracle answers nothing (`return set()`) | **0** | (none) | **finding M2 below** |
| 10 — the git oracle raises (`git` -> a binary that does not exist) | **1** | census | **fail-closed confirmed**: a missing `git` errors the row rather than reducing the census to nothing |

Probe 7 is the one Worker 2 predicted and it holds: a representative-per-tree row alone would have survived it only partially (8 of the 11 named files sit below the top level), and the census fails it outright. So the choice to build a census rather than the two sentences my predecessor sketched is vindicated by measurement, not only by argument.

**No mutation is live.** `tests/test_ci_governance.py` hashes `e56acf972ef67c6fb561419704c7d65b163cb6cc317c8b8e4a74d1ae1e150a15` (Worker 2's recorded shipped hash); `scripts/check_citations.py` hashes `699e2491...` and is byte-identical to `git show HEAD:` (`cmp` exit 0). No `ACTIVE-MUTATION.json` or `RESTORE-FAILED.json` exists under `/tmp`, `/private/tmp`, or the repo. The live corpus re-derives **0 violations**, and `git status --porcelain` after my last probe is identical to its state before this pass.

### High:

None.

### Medium:

#### M2 — the corpus census can be retired by its own oracle: an empty `git ls-files` answer makes the row pass whatever the corpus holds, and nothing fails

`tests/test_ci_governance.py::test_the_sweep_corpus_covers_every_committable_python_file` computes `missing = sorted(_committable_python_files() - swept)` and asserts `not missing`. When the oracle returns an **empty set**, `missing` is empty for *every* corpus — the row stops being a measurement and cannot fail again. `tests/test_ci_governance.py::_committable_python_files` refuses two of the three ways git can fail to answer and not the third:

- git absent -> `FileNotFoundError` -> **fail-closed** (measured: probe 10, 1 row fails);
- git exits non-zero -> the `returncode` assert fires -> **fail-closed**;
- git exits **0 with empty stdout** -> `set()` -> **fail-open**, 0 rows fail (measured: probe 9, `69 passed`, exit 0, 0 collection/setup errors).

**This is not hypothetical, and it is not a mutation-only state.** `git ls-files --cached --others --exclude-standard -- '*.py'` genuinely answers empty-with-exit-0 whenever it is run in a directory that is untracked-and-ignored inside an enclosing repository. Measured in this very tree:

```shell
$ git -C docs/shadow ls-files --cached --others --exclude-standard -- '*.py'   # docs/shadow is gitignored
$ echo $?
0
$ ls docs/shadow/*.py | head -1
docs/shadow/tests__test_ci_governance.stripped.py
```

Exit 0, no output, with a real `.py` file sitting there. Any checkout whose `REPO_ROOT` lands in such a position — an export or vendored copy without its own `.git`, unpacked under another repository's ignored path — reproduces it for the whole suite.

**Why it matters:** this is the same shape as M1 one level up. M1 was "the sweep's corpus is unpinned"; this is "the census's oracle is unpinned", and the census is what closed M1. The docstring's own claim — *"No fallback when git cannot answer: a missing `git` raises here rather than quietly reducing the census to nothing"* — is true of the raising case and false of the empty-answer case, which reduces the census to nothing precisely as quietly. `BUILD.md` `### Fail-open shapes` puts a fail-open shape on a decision path at a **Medium** floor, and `### Acceptance rule` reads a 0-row mutation as nothing pinning the boundary; both point the same way. (I weighed Low — the trigger is environmental rather than an ordinary edit, and the 11 reach rows stay live in that world — but the fix is identical under either tier, so the grading is not worth re-litigating.)

**What closes it** (one line, in this module's own existing idiom — `::_workflow_paths` already asserts `paths, f"no workflow files found under {WORKFLOW_DIR}"` for exactly this reason):

Guard the **answer**, not the empty spelling of it. A bare `assert names` refuses only a totally empty enumeration; an oracle that under-enumerates partially walks straight through it. Assert instead that the enumeration contains a file that must always be in it — the census's own module is the obvious one:

```python
names = {name for name in completed.stdout.split("\0") if name}
assert "tests/test_ci_governance.py" in names, (
    "git listed no .py files (or not this module); the census cannot be taken"
)
return names
```

**Test expectation:** with the guard in place, probe 9's mutation (`_committable_python_files` returning `set()`) must fail at least one row, and so must an oracle truncated to a partial set such as `{"conftest.py"}`. Today both fail zero.

### Low:

None new.

### Verdicts on the prior pass's findings

- **M1 — the governance sweep's corpus is unpinned: CLOSED.** Re-derived, not accepted. My predecessor's figures reproduce digit for digit (429 committable `.py`, `iter_python_sources()` 426, `tests/` 136, `examples/` 159, `django_strawberry_framework/` 109, `scripts/` 22, and exactly three tracked `.py` outside the trees). The narrowing that measured 0 now measures **7**, with the failing set naming every `tests/` file that left. Three further narrowings nobody had tried — an emptied tuple, a glob matching nothing, and the depth narrowing Worker 2 predicted a representative-per-tree row would survive — measure 11, 11 and 9. The finding's stated test expectations are both met: the `"tests"`-dropped mutation fails 7 rows, and a reporter that returns nothing fails 2 rows the live-tree sweep cannot (`::test_the_sweep_reports_a_planted_violation_with_its_file_and_line`, both ids, while `::test_no_active_source_uses_a_forbidden_optimizer_extensions_form` passes under that same mutation — confirmed in entry 3's run).
- **L1 — the recorded restore hash did not match the shipped file: CLOSED.** Re-proving was the right half rather than annotating, and the reason given is verifiable: this pass's planted rows really do join the classifier arms' failing sets (4 -> 5, 5 -> 6), so pass 1's node-id lists were stale as well as its hashes. The shipped file hashes `e56acf97…` exactly as recorded, and all five pass-2 entries were taken against those bytes — my own re-runs reproduce the same hash in every restore proof.
- **L2 — the false-positive enumeration was incomplete: CLOSED.** The paragraph now names both arms' over-matches, and I controlled the new sentence rather than reading it: `_forbidden_optimizer_entries("extensions = [lambda: MyDjangoOptimizerExtensionWrapper()]")` returns a `constructing lambda` hit, and the dotted spelling does too. The claim is true in the direction stated.
- **L3 — three tracked `.py` outside the corpus: CLOSED, and widening was the right half.** The three files are exactly `conftest.py`, `docs/dry/export_dry_review.py`, `line_count.py` (re-derived from `git ls-files` independently), and none contains `DjangoOptimizerExtension` or `extensions=` (grep exit 1). **It does not enlarge the gate beyond maintainer decision D1:** D1 authorizes a pin asserting that "no active `.py` constructs a schema with" the two forbidden forms, and defines its scope by that phrase rather than by `SOURCE_TREES`; adding three tracked first-party modules moves the corpus *toward* D1's wording, not past it. D1's rejected alternative was about **placement** (a second mechanism in `scripts/` + pre-commit), and nothing was added to `scripts/`, `.pre-commit-config.yaml`, or CI — verified: the diff is one test file. The `EXTRA_SOURCE_FILES` tuple also cannot rot silently, which I measured rather than took on the comment's word: proof entry 2 removes it and the census names the three files by hand.

### DRY findings

**None new.** Checked, with evidence:

- **Is the gate now a second spelling of its own corpus?** No. `_sweep_corpus()` is the single definition (`iter_python_sources()` plus three named files); `CORPUS_REACH_FILES` is a **sample** asserted against that definition, not a competing definition of it — 11 named paths out of 429, and no code reads the corpus from it. `EXTRA_SOURCE_FILES` is the only hardcoded corpus *input*, and the census is what pins it.
- **No dead machinery, measured rather than argued.** Every new seam has a mutation that fails rows only it can fail: `_sweep_corpus` -> 2, `_forbidden_entries_in` -> 2, the shared `SOURCE_TREES` spine -> 7, each classifier arm -> 5 and 6. The one exception is `_committable_python_files`'s return value at 0, which is finding M2 — and stating it that way is what makes M2 a gap rather than a preference.
- **Existence challenge raised and answered against measurement, not taste.** The candidate was the 11 reach rows: under every corpus narrowing I ran, the census fails too, so they never fail alone. What decides for keeping them is that they are the only instrument that remains **live** when the oracle is dead (probe 9) and the only one that says *which* files a narrowing cost. Deleting them would also be the "weaker boundary" `BUILD.md` `### Acceptance rule` refuses as a fix. Not escalated.
- **Repeated literals are the right kind.** `scripts/review_inspect.py` reports six: `permissions` / `contents` (pre-existing YAML keys), `constructing lambda` and `bare class in a sequence` (once produced by the classifier, once asserted by the planted rows), `conftest.py` (once in the corpus definition, once in the reach sample), `planted_schema.py` (two `tmp_path` bodies). In each new case, sharing the literal through a constant would make the assertion restate the code instead of checking it. Correctly left duplicated.
- **The plan's decided answers are not re-litigated and were not disturbed:** no shared `optimizer_factory()` helper, no module-level singleton, no second enforcement mechanism.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` is **empty**; `__all__` and the re-export list are unchanged. `git status --porcelain -- django_strawberry_framework/` is empty — this pass, like pass 1, changes no package source.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity (only when the slice touches docs, release metadata, KANBAN, or archived specs)

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. `docs/TREE.md` re-verified byte-clean (`git status --porcelain -- docs/TREE.md` empty), and `tests/test_ci_governance.py`'s first docstring line is still byte-identical to HEAD, so the `--check` render is unaffected — the widening again landed only in the paragraphs below it.

### Scoping claim — the apply pass touched one file

Confirmed independently of Worker 2's assertion, since everything the prior review certified would be stale if it were false:

- The eight migrated files' diff against HEAD is **91 changed lines**, the same total my predecessor measured, and I dumped and read all 91 rather than grepping them: they are `extensions=` expression substitutions, singleton declarations, four `if <flag>:` blocks, and the one `::build_strategy_schema` docstring rewrite. Not one assertion, marker, skip, or xfail.
- `scripts/check_citations.py` — the disclosed out-of-list transient borrow for proof #1 — is byte-identical to HEAD: `git show HEAD:scripts/check_citations.py` into a scratch path outside the repo, then `cmp`, exit 0, `sha256 699e2491...` both sides. The four pristine copies left under `/tmp/dsf-w3-*` and `/tmp/dsf-failability-slice-2-029-pass2/` also each `cmp` clean against HEAD, so no proof in either pass ever copied a mutated reference.
- Corroborating: the eight files' mtimes are 01:33-01:35 (and 01:51 for `tests/forms/test_resolvers.py`, the pass-1 end-to-end control site), while `tests/test_ci_governance.py` is 02:12 and `scripts/check_citations.py` 02:11 — the apply pass's window.
- The live corpus re-derives **0 forbidden entries** through the shipped classifier, and the whole 25-site population remains repaired.

### What looks solid

- **The corpus guard answers the question rather than one spelling of it.** Four structurally different narrowings — one tree dropped, all trees dropped, a glob matching nothing, and a depth narrowing that keeps every tree name — fail 7, 11, 11 and 9 rows. Before this pass the first two measured 0.
- **The two instruments are genuinely two.** Different oracles (a `git` subprocess vs. hardcoded names), different failure text, and measurably different readings: entry 1 fails census + 6 reach rows, entry 2 census + 1, probe 7 census + 8. Neither is the other written twice.
- **The census's positive control is real.** Entry 2 restores the repository's pre-widening corpus exactly and the census fails naming `conftest.py`, `docs/dry/export_dry_review.py`, `line_count.py` — so the row demonstrably discriminates a state this repo was in an hour before it was written.
- **The reporter seam is pinned where the live tree cannot pin it.** Under entry 3's mutation `::test_no_active_source_uses_a_forbidden_optimizer_extensions_form` still passes while the two planted rows fail — which is the precise argument for the seam existing.
- **The gitignored-scratch exclusion still holds, and this pass tested it by accident and on purpose.** My own `docs/builder/temp-tests/slice-2-029/w3p2-*.py` instruments sat in the tree across every run; the census stayed green, confirming that ignored scratch enters neither the corpus nor the oracle.
- **Floor and hot-path both reproduce as recorded.** `/tmp/dsf-floor-029/bin/python -m pytest tests/test_ci_governance.py --no-cov -q -p no:cacheprovider` -> **69 passed**, venv re-read as Python 3.10.19 / Django 5.2.16 / strawberry-graphql 0.316.0. The pass-1 hot-path temp test re-runs to the same numbers (`False / False / True`; two instances at `CacheInfo(hits=0, misses=1, size=1)` -> aggregate `misses=2, hits=0`; one instance at `CacheInfo(hits=1, misses=1, size=1)` -> `misses=1, hits=1`). No new number is owed: the pass changes no production line.
- **The shared `.venv` is unmutated.** `uv pip list` reads Django **6.1** / strawberry-graphql **0.323.2**, `.venv/bin/python -V` reads 3.14.2 — head, not floor — and `uv.lock` / `pyproject.toml` are clean. Consistent with "no install was performed in this pass".
- **Counts re-derived.** `tests/test_ci_governance.py` **69 passed** (54 + 15); the slice scope **565 passed** (550 + 15); `check_citations.py` -> `OK: 789 citations resolve (712 in 426 .py files, 77 in KANBAN.md)`, whose own `426` agrees with the corpus reading.
- **Gates green, read-only:** `ruff format --check` (already formatted), `ruff check` (all checks passed), `check_trailing_commas.py --check` (exit 0).
- **The docstrings say what the code does.** Every claim I could control, I controlled: the affixed and dotted lambda spellings both flag, the reporter is empty for an empty corpus, all 18 control snippets are distinct strings, and every path in `CORPUS_REACH_FILES` and `EXTRA_SOURCE_FILES` exists on disk.

### Spec slice checklist audit — box 11

**Ticked and true, and Worker 2's flag is the right call.** Box 11 reads *"The pin scopes its corpus through `scripts/check_citations.py`'s first-party source-tree definition, with the coupling named in a comment."* Both halves still hold literally: `iter_python_sources()` is the corpus's spine (`::_sweep_corpus`), and the import comment names the coupling. The box asserts a positive property, not an exclusive one, so three named files added beside that definition do not falsify it — the box is simply silent about them. Worker 2's recommended replacement is an improvement and is correctly routed to Worker 1 (box text is neither Worker 2's nor mine to edit). No other box's tick changed state this pass; the eight migrated files are untouched, so the seventeen ticks my predecessor audited stand.

### Static helper use

`uv run python scripts/review_inspect.py tests/test_ci_governance.py --output-dir docs/shadow` — **run**, not inherited. Trigger fires (~130 new lines to a `.py` outside `django_strawberry_framework/`, over the 50-line threshold), and Worker 2 explicitly left the judgement to this pass rather than claiming the skip. Output: 3 control-flow hotspots (`_forbidden_optimizer_entries` 36 lines / 8 branch nodes; `test_no_active_source_uses_a_forbidden_optimizer_extensions_form` 45 lines / **0** branch nodes, i.e. the growth is docstring; one pre-existing workflow test), **no Django/ORM markers**, one cross-folder import (`from scripts.check_citations import iter_python_sources`, precedent established), and the six repeated literals discussed under `### DRY findings`. Nothing that changes a finding. **Skips:** none owed — this pass touched exactly one file.

### Temp test verification

- `docs/builder/temp-tests/slice-2-029/w3p2-rerun.json` / `.md` — independent re-runs of all five recorded entries at the recorded scope. Die with the cycle.
- `docs/builder/temp-tests/slice-2-029/w3p2-probes.json` / `.md` — the five narrowings neither pass had tried. **Probe 9 caught a real gap**, so per the temp-test rule its disposition is: recorded as Medium finding M2 for Worker 2 to close with a guard plus rows; the manifest itself is not promoted.
- `docs/builder/temp-tests/slice-2-029/w3p2-corpus.py`, `w3p2-claims.py` — corpus/oracle re-derivation and docstring-claim controls. Not promoted; both duplicate assertions the permanent rows now carry.
- Worker 2's `test_hot_path_budget.py` re-run unchanged and correctly not promoted.

### Notes for Worker 1 (spec reconciliation)

- **Carried forward, not acted on: the Amendment 2 parallel-site escalation is Slice 3's.** `## Definition of done` item 4 and the `## Slice checklist` #"Post-migration forbidden-form gate:" bullet both describe the one-shot grep; restating only item 4 leaves the checklist naming the instrument that under-reported this regression. The resolution paths recorded in pass 1 stand unchanged.
- **The census makes "active first-party source" mean something exact**, as Worker 2 notes — every `.py` that `git ls-files --cached --others --exclude-standard` reports. If M2 is closed as recommended, that phrase also gains a guard against the oracle answering emptily, which is worth knowing before the spec asserts the gate is "enforced continuously".
- **A trade-off worth naming, not a finding.** The census fires on any **untracked-but-not-ignored** `.py` that lands outside the corpus — a root-level scratch file, say. That is the gate doing its job (such a file is committable and outside the pin), and the failure message says how to resolve it, but in a repo worked by concurrent sessions it means one session's stray `.py` can red another's suite. Recorded so the behavior is a decided answer rather than a surprise.
- **No spec text was read as false by this pass**, and I requested no spec edit. Pass 1's Amendments 1-3 stand exactly as my predecessor judged them.

### Review outcome

`revision-needed`.

One Medium (**M2**), no Lows, no Highs. M1 and all three Lows from pass 1 are **closed** and I re-derived each rather than accepting it; the apply pass's scoping claim is confirmed independently, the disclosed out-of-list borrow of `scripts/check_citations.py` fully reverted (byte-identical to HEAD), no mutation is live, and every one of Worker 2's five recorded proofs reproduces at the recorded scope with **identical node-id sets** — including the 7 that proves M1 closed.

M2 lands entirely in `tests/test_ci_governance.py`, needs no spec context, and closes with one guarded line plus the rows that pin it. Routes back to **Worker 2**.

---

## Build report (Worker 2, pass 3)

Apply-changes pass closing Worker 3's **M2** and nothing else. Everything Worker 3 re-derived and confirmed closed - M1, L1, L2, L3, the 25-site population, the 91 changed lines across the eight migrated files, the five conditional `else` branches, the hot-path number, the floor venv, box 11 - was neither re-done nor disturbed. The whole diff of this pass is again one file, and inside that file it is five hunks.

### M2 - the corpus census could be retired by its own oracle (closed)

**Re-derived before acting.** Both halves of the finding reproduce in this tree:

- The empty-with-exit-0 answer is real, not hypothetical: `git -C docs/shadow ls-files --cached --others --exclude-standard -- '*.py'` exits **0** with **no output** while `docs/shadow/tests__test_ci_governance.stripped.py` sits there. The repo-root oracle answers **429** paths for the same command, so the difference is entirely git's position, not the pathspec.
- The consequence measures as stated. I ran the finding's own mutation against the pass-2 bytes **before** editing anything (`docs/builder/temp-tests/slice-2-029/w2p3-prefix.json` / `.md`, scratch root `/private/tmp/dsf-w2p3-prefix`, target hash `e56acf97...` - Worker 3's recorded shipped hash): `_committable_python_files` returning `set()` failed **0 rows**, `69 passed`, pytest exit 0, 0 collection/setup errors. Restore byte-proved by the tool. So the row genuinely could not fail again once the oracle went empty.

**What was built, and why it is not the one line as sketched.** Worker 3's recommendation - a self-membership assert inside `_committable_python_files`, immediately before the return - is the right *rule* and the wrong *position*. Placed there it guards the parse, not the answer as consumed: any way the enumeration is lost after the check (including the very mutation the finding was measured with, which replaces the function's returned value) leaves the census reading a corpus-shaped nothing again, with the guard passing on the discarded good answer. `BUILD.md` `### Fail-open shapes` says to guard the ANSWER; here the answer is the set the census actually subtracts from. Three changes, one seam each:

1. **`ORACLE_REQUIRED_FILES`** - what any coherent answer must report: `CENSUS_MODULE` (this module's own repo-relative path, derived from `__file__` so a rename cannot strand it) plus the eleven `CORPUS_REACH_FILES`. Self-membership is the floor Worker 3 named and is strictly stronger than non-empty; requiring the load-bearing files on top is what a **partially** truncated answer cannot walk through. All twelve verified `--cached` **tracked** in this tree, so the requirement cannot be satisfied only by an `--others` accident.
2. **`_unreported_required_files(answer)`** - a pure function over one git answer, returning the required paths it failed to report. It exists so the refusing branch can be exercised at all: the live tree cannot produce an empty or truncated answer, and *a guard that never ran reads exactly like a guard that found nothing*. This is the same seam shape the module already uses twice (`_forbidden_optimizer_entries` takes source text so snippets can be fed to it; `_forbidden_entries_in` takes paths so a `tmp_path` corpus can).
3. **The census consumes the checked answer.** `test_the_sweep_corpus_covers_every_committable_python_file` now binds `committable = _committable_python_files()`, refuses it if `_unreported_required_files` names anything, and only then subtracts the corpus from that same object.

**Rows, and why more than one.** `test_the_git_oracle_enumerates_this_module` states the self-membership property in its own name against the live oracle; the census's own guard refuses to conclude from an unchecked input. They are the two halves Worker 3's finding names ("the oracle is unpinned" and "the census draws a conclusion from it"), and both fail together on any emptied or truncated oracle - which is what takes the finding's own mutation from 0 rows to 2.

**Worker 3's stated test expectation, met and exceeded.** Both mutations it named now fail rows where "today both fail zero":

| Mutation | Before this pass | After |
|---|---|---|
| `_committable_python_files` returns `set()` | **0** (measured by me, above) | **2** |
| `_committable_python_files` returns `{"conftest.py"}` | **0** (derived: pre-pass the oracle had exactly **one** consumer - line `:527` of the pass-2 bytes, grep over the pristine copy - and `{"conftest.py"} - swept` is empty because `conftest.py` is in the corpus, which pass-2 proof entry 2 measured) | **2** |
| the guard itself removed (`_unreported_required_files` returns `[]`) | n/a (did not exist) | **4** |

**The docstring that M2 falsified is corrected, not annotated.** `_committable_python_files`'s "No fallback when git cannot answer" paragraph claimed a completeness it did not have. It now enumerates all three of git's failure modes and says which mechanism refuses each, and names the third for what it is: an answer that reports no error of any kind because it is coherent-looking and merely wrong. The census's own docstring gains the matching paragraph - this row subtracts the corpus *from* git's answer, so an empty answer leaves nothing missing whatever the corpus holds.

**Prior proofs re-measured rather than assumed.** Adding rows to a file whose boundaries were already proved can change those proofs' failing-row **sets**, which is exactly how L1 arose. I re-ran pass 2's whole manifest against the shipped bytes (`--scratch-root /tmp/dsf-w2p3-recheck`, output `docs/builder/temp-tests/slice-2-029/w2p3-pass2-recheck.md`, tool exit 0): **7 / 2 / 2 / 5 / 6**, every node-id set **identical** to the recorded one. None of this pass's rows joins them, because none of them touches the corpus, the reporter, or the classifier.

### Files touched

Grounded in `git status --short` after both ruff invocations (below).

- `tests/test_ci_governance.py` - the only changed file, +105 / -4 lines against the pass-2 bytes. Five hunks: the two new constants, the corrected `_committable_python_files` docstring, the new `_unreported_required_files` seam, the census test's guard plus its docstring paragraph, and the three new tests.

Unchanged and deliberately so: `scripts/check_citations.py` (byte-identical to HEAD - `git show HEAD:scripts/check_citations.py` into `/tmp/dsf-w2p3-cc-head.py` then `cmp`, exit 0, after the pass-2 recheck borrowed it transiently for entry 1), `docs/TREE.md` (clean, and this pass again changed only paragraphs below the module docstring's first line), every `django_strawberry_framework/**` module, and all eight migrated test files.

### Tests added or updated

All permanent, all in `tests/test_ci_governance.py`. 69 rows before this pass, **75 after**; no row was removed, weakened, renamed, or re-scoped.

- `::test_the_git_oracle_enumerates_this_module` - the live oracle answered about this checkout at all.
- `::test_the_corpus_census_refuses_an_incoherent_oracle_answer` - 4 rows (`enumerates-nothing`, `only-this-module`, `only-one-load-bearing-file`, `every-load-bearing-file-but-this-module`), each asserting the guard names a specific path the answer failed to report. The last three are the rows a bare `assert answer` would pass.
- `::test_the_corpus_census_accepts_a_complete_oracle_answer` - the guard's negative direction, so a guard that refused everything would also fail.

`::test_the_sweep_corpus_covers_every_committable_python_file` keeps its name and its contract; its body now checks its input before drawing the conclusion, and subtracts from the same object it checked.

### Validation run

- `uv run ruff format tests/test_ci_governance.py` - pass (`1 file left unchanged`). Never `.`.
- `uv run ruff check --fix tests/test_ci_governance.py` - pass (`All checks passed!`, 0 fixed).
- `uv run python scripts/check_trailing_commas.py tests/test_ci_governance.py` then `--check` - pass, exit 0, `Fixed 0 file(s)`. Run rather than guessed, per the scope notes; the new 4-tuple and the 3-tuples were already at the layout the script wants.
- `uv run python scripts/check_citations.py` - pass, `OK: 789 citations resolve (712 in 426 .py files, 77 in KANBAN.md)`. This pass adds no `path::Symbol` citation, and none of its docstring text wraps an existing one.
- `git status --short` after both ruff invocations - `tests/test_ci_governance.py` plus exactly the paths already recorded as out of scope: Slice 1's spec / rationale / artifact / plan files, the concurrent session's `docs/review/review-0_0_14.md`, `docs/review/rev-*.md` and `tests/mutations/test_operations.py`, and the eight migrated files still dirty from pass 1. **No unexpected churn; nothing reverted.**
- `uv run pytest tests/test_ci_governance.py --no-cov -q -p no:cacheprovider` - **75 passed**.
- `uv run pytest tests/test_ci_governance.py tests/test_relay_connection.py tests/optimizer/test_extension.py tests/forms/test_resolvers.py tests/types/test_resolvers.py tests/mutations/test_write_transaction.py tests/mutations/test_resolvers.py examples/fakeshop/test_query/test_products_visibility_api.py --no-cov -q -p no:cacheprovider` - **571 passed** (pass 2's 565 plus this pass's 6 rows; no pre-existing row changed state).
- **Sibling importers, per `## Apply-changes verification scope`:** every symbol this pass adds is module-private and `grep -rln` over `tests/ scripts/ examples/ django_strawberry_framework/ conftest.py` for `_unreported_required_files` / `ORACLE_REQUIRED_FILES` / `CENSUS_MODULE` / `test_ci_governance` returns only this module itself and one **path string** in `examples/fakeshop/apps/kanban/constants.py:245` (the kanban predicted-path list, not an import). The focused run above is therefore the complete importer set.
- **Test-staleness full sweep: not owed.** This pass changes no example-model field set and no wire shape; every changed line is inside one governance test module.

### Failability proofs

Three entries, produced by `uv run python scripts/prove_failability.py docs/builder/temp-tests/slice-2-029/proofs-pass3.json --output docs/builder/temp-tests/slice-2-029/proofs-pass3.md` (tool exit **0** - no entry weakly pinned, no collection/setup error). Anchors were checked with `--check-anchors-only` first; all three matched exactly once. Scratch root `/private/tmp/dsf-failability-slice-2-029-pass3`, **outside** the repo. One mutation live at a time, each restored and byte-proved before the next. **Scope as run, identical for all three:** `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_ci_governance.py`. **Pre-mutation state of that scope, for all three:** green, `75 passed`, pytest exit 0, 0 pre-existing failing rows differenced out. **Collection/setup errors: 0 in every entry.** Shipped-file hash for all three: `1eb94c2dd194edbc621b8875269d38e31b4185aa81275054d89959e4f9b3e38e`.

Entry 1 is this pass's new boundary. Entries 2 and 3 are the finding's own two mutations, kept as positive controls that M2 is closed.

1. **`tests/test_ci_governance.py::_unreported_required_files` - the guard removed.** Mutation applied: `return sorted(set(ORACLE_REQUIRED_FILES) - set(answer))` replaced by `return []`, so every answer is accepted as complete while every call site still reads as guarded. Failing node ids (**4**):
   - `tests/test_ci_governance.py::test_the_corpus_census_refuses_an_incoherent_oracle_answer[enumerates-nothing]`
   - `tests/test_ci_governance.py::test_the_corpus_census_refuses_an_incoherent_oracle_answer[only-this-module]`
   - `tests/test_ci_governance.py::test_the_corpus_census_refuses_an_incoherent_oracle_answer[only-one-load-bearing-file]`
   - `tests/test_ci_governance.py::test_the_corpus_census_refuses_an_incoherent_oracle_answer[every-load-bearing-file-but-this-module]`

   Mutant `4 failed, 71 passed`, pytest exit 1. Revert proved by byte-comparison: `filecmp.cmp(shallow=False) True; sha256 1eb94c2dd194edbc... == 1eb94c2dd194edbc...`.

2. **`tests/test_ci_governance.py::_committable_python_files` - the oracle enumerates nothing (M2 reproduced).** Mutation applied: `return {name for name in completed.stdout.split("\0") if name}` replaced by `return set()` - what git returns, at exit 0 with no error, from inside an enclosing repository's ignored path. **The identical mutation measured 0 rows against the pass-2 bytes** (`w2p3-prefix.md`). Failing node ids (**2**):
   - `tests/test_ci_governance.py::test_the_sweep_corpus_covers_every_committable_python_file`
   - `tests/test_ci_governance.py::test_the_git_oracle_enumerates_this_module`

   Mutant `2 failed, 73 passed`, exit 1. Revert: `filecmp.cmp(shallow=False) True; sha256 1eb94c2dd194edbc... == 1eb94c2dd194edbc...`.

3. **`tests/test_ci_governance.py::_committable_python_files` - the oracle truncated to a partial answer.** Mutation applied: the same anchor replaced by `return {"conftest.py"}` - one real file instead of 429, so it is **non-empty** and every size-shaped or truthiness-shaped guard accepts it, while the census's subtraction is still empty for every corpus. This is the second half of Worker 3's stated expectation and the reason the guard requires named files rather than a count. Failing node ids (**2**):
   - `tests/test_ci_governance.py::test_the_sweep_corpus_covers_every_committable_python_file`
   - `tests/test_ci_governance.py::test_the_git_oracle_enumerates_this_module`

   Mutant `2 failed, 73 passed`, exit 1. Revert: `filecmp.cmp(shallow=False) True; sha256 1eb94c2dd194edbc... == 1eb94c2dd194edbc...`.

**No zero-row entry**, so no `why 0` judgement is owed anywhere in this record. **No mutation is live:** no `ACTIVE-MUTATION.json` or `RESTORE-FAILED.json` under `/tmp` or `/private/tmp`, `scripts/check_citations.py` is byte-identical to HEAD (`cmp` exit 0), the shipped `tests/test_ci_governance.py` hashes `1eb94c2d...`, and the focused suite is green at 75.

**Pass 2's five entries re-run in this pass** (`docs/builder/temp-tests/slice-2-029/w2p3-pass2-recheck.md`, scratch root `/private/tmp/dsf-w2p3-recheck`, tool exit 0): **7 / 2 / 2 / 5 / 6** rows, 0 collection/setup errors each, pre-mutation green at 75, and every failing node-id **set identical** to the record. So this pass's rows leave the prior boundaries' pins exactly where Worker 3 measured them.

### Hot-path budget

**No new number is owed**, per the dispatch and per the change's shape. This pass adds test-only guard rows and changes no production line; the plan's declared metric (`DjangoOptimizerExtension.cache_info()` across two executions on one schema) stands from pass 1 at `misses 2 -> 1`, `hits 0 -> 1`, reproduced by Worker 3 in both review passes. Nothing this pass touches is on a request path: the oracle shells out to `git` inside `tests/test_ci_governance.py` only, and this pass adds exactly one further invocation of it (the new live row), in a governance module that runs once per session.

### Floor verification

Re-run **only** `tests/test_ci_governance.py` at the floor, per the dispatch. The venv from pass 1 was reused as-is; **no install was performed in this pass**, so the shared `.venv` could not be reached - it still reads Django 6.1 / strawberry-graphql 0.323.2 (`uv pip list`), i.e. head, not floor, and `git status --short -- pyproject.toml uv.lock` is empty.

Versions re-read rather than trusted, with `uv pip list --python /tmp/dsf-floor-029/bin/python` and `/tmp/dsf-floor-029/bin/python -V`:

```
Python 3.10.19
django                      5.2.16
pytest                      9.1.1
strawberry-graphql          0.316.0
```

| Command | Result |
|---|---|
| `/tmp/dsf-floor-029/bin/python -m pytest tests/test_ci_governance.py --no-cov -q -p no:cacheprovider` | **PASS** - `75 passed in 3.07s` |

The new code uses `Path.relative_to` / `PurePath.as_posix` and set arithmetic only - nothing version-sensitive - and the floor run is the confirmation rather than the reading.

### Implementation notes

- **Why the guard sits at the consumer rather than inside the helper.** Stated under M2 above because it is the one place this pass departs from the finding's wording: a guard inside `_committable_python_files` validates the parse and then hands the caller whatever the function returns, so it is a guard on one *spelling* of the incoherent input. The census subtracts from the object it checked, which is the answer as used. It also means the finding's own measurement instrument (probe 9) now fails rows, which a parse-side guard would have left at 0 - and a fix that leaves the finding's measurement unchanged is a fix nobody can audit.
- **Why `CENSUS_MODULE` is derived, not written.** `Path(__file__).resolve().relative_to(REPO_ROOT).as_posix()` cannot rot on a rename, and a hardcoded `"tests/test_ci_governance.py"` would silently stop being self-membership the moment the file moved - it would become one more named file, which is what `CORPUS_REACH_FILES` already provides eleven of.
- **Why the required set is self plus the reach files, not self alone.** Self-membership answers "did git talk about this repository"; it does not answer "did git finish". A truncated answer containing this module and nothing else passes a self-only check and still empties the census. Entry 3's mutation is that case in the other direction and fails 2 rows.
- **`CORPUS_REACH_FILES` reused rather than a second list written.** The census's claim rests on those files being in the corpus; a git answer that does not report them cannot support that claim either. One list, two different assertions over two different objects (corpus membership; oracle membership), so this is not the corpus getting a second definition.
- **The refusal rows assert *which* path was unreported, not merely that something was.** `assert expected in _unreported_required_files(answer)` fails a guard that returns a non-empty but wrong list, which a truthiness assertion would accept - the same distinction the guard itself makes.
- **Row count.** 6 rows for one Medium: 4 of them are one parametrization whose data is four literal answers, and the other two are the live-oracle row and the guard's negative control. The alternative - the single assert Worker 3 sketched - pins the boundary at 0 rows, because nothing in a healthy tree ever hands the guard an answer to refuse.

### Notes for Worker 3

- **Where to look hardest.** The remaining reading I could not close from inside the module: `ORACLE_REQUIRED_FILES` is satisfiable by an answer that reports those twelve paths and nothing else. That is not a fail-open the way M2 was - such an answer is not something git produces from any position, and the twelve include one file per tree so a real narrowing loses at least one of them - but it is the shape to attack if you want the next level. What I deliberately did **not** do is assert a count or a floor size: a number rots on every file added, and `429` in an assertion is the kind of literal that gets "fixed" rather than investigated.
- **Re-running:** `uv run python scripts/prove_failability.py docs/builder/temp-tests/slice-2-029/proofs-pass3.json` reproduces all three entries at the recorded scope; `--check-anchors-only` gives the precondition without the runs. `w2p3-prefix.json` reproduces the **pre-fix** 0-row reading only against the pass-2 bytes, which no longer exist in the tree - its value is the record, not a re-run. `w2p3-pass2-recheck.md` is my re-run of your pass-2 manifest against the shipped file.
- **No file outside this pass's writable list was mutated by this pass's own proofs.** Entries 1-3 all target `tests/test_ci_governance.py`. `scripts/check_citations.py` was mutated once more, transiently, by the pass-2 manifest re-run (its entry 1 owns that anchor); it is restored and byte-proved against HEAD, and that check is recorded under `### Files touched` rather than left for you to notice.
- **`scripts/review_inspect.py` was not run by this pass.** The addition is ~105 lines to a `.py` outside `django_strawberry_framework/`, so the trigger fires; you ran it on this exact module last pass and its readings (3 control-flow hotspots, no ORM markers, six repeated literals, one cross-folder import) are unchanged in kind by this diff - the new seam is a one-line set subtraction with no branch. Naming the trigger rather than claiming the skip, as last pass did.
- **Temp artifacts**, under the gitignored `docs/builder/temp-tests/slice-2-029/`: `w2p3-prefix.json` / `.md`, `proofs-pass3.json` / `.md`, `w2p3-pass2-recheck.md` are this pass's; everything else there is an earlier pass's or yours. None is promoted.

### Notes for Worker 1 (spec reconciliation)

- **No spec text was read as false by this pass and no spec edit is requested.** Pass 1's Amendments 1-3 stand exactly as written, and Worker 3 judged all three sound in both reviews.
- **No checklist box changed state this pass.** All 17 were ticked in pass 1 and audited by Worker 3 in both reviews; M2's fix lands inside the contract box 9 and box 14 already describe (the pin, and the failability record for it), and adds no sub-check of its own. Nothing here is a new tick and nothing here should be un-ticked.
- **Pass 2's box-11 wording recommendation stands unchanged** and is not re-argued here. This pass adds no further corpus input: `ORACLE_REQUIRED_FILES` is a requirement on git's *answer*, not a third source of corpus paths.
- **The Amendment 2 parallel-site escalation remains Slice 3's** and was not acted on, per the dispatch. One fact worth carrying into it: after this pass, "active first-party source" can be stated exactly - every `.py` that `git ls-files --cached --others --exclude-standard` reports - **and** the gate now refuses to reason from that phrase when git did not actually answer about this repository, which is the property a spec sentence claiming continuous enforcement is really asserting.


---

## Review (Worker 3, pass 3)

### Failability re-run — mutations pre-registered BEFORE they are made

`worker-3.md` "Reading is necessary, not sufficient". Every mutation below is written here before it is applied, applied one at a time, reverted inside this same pass, and the revert proved by byte-comparison. Anchors are checked with `--check-anchors-only` before any pristine copy is taken. Scratch roots are outside the repository. No `git checkout` / `git restore` / `git stash` / `git worktree` at any point. The one source file touched by any mutation is `tests/test_ci_governance.py`, which is this slice's own file.

**Mandatory floor.** Worker 2's pass-3 record carries three entries at **4 / 2 / 2** rows. Entries 2 and 3 are at or under the 3-or-fewer floor and are therefore mandatory. Entry 1 is re-run as well: it is the only entry pinning the new boundary, 4 is one row above the floor, and its four rows are a single parametrization, which is exactly the shape the floor exists to distrust.

Re-runs of Worker 2's pass-3 records (manifest `docs/builder/temp-tests/slice-2-029/w3p3-rerun.json`, scratch root `/private/tmp/dsf-w3p3-rerun`):

1. `tests/test_ci_governance.py::_unreported_required_files` — `return sorted(set(ORACLE_REQUIRED_FILES) - set(answer))` replaced by `return []`. (Worker 2 entry 1; expected 4.)
2. `tests/test_ci_governance.py::_committable_python_files` — the return replaced by `return set()`. (Worker 2 entry 2; expected 2.)
3. `tests/test_ci_governance.py::_committable_python_files` — the return replaced by `return {"conftest.py"}`. (Worker 2 entry 3; expected 2.)

**Probes this pass adds** (manifest `docs/builder/temp-tests/slice-2-029/w3p3-probes.json`, scratch root `/private/tmp/dsf-w3p3-probes`). The dispatch asks specifically whether a **truncated-but-non-empty** answer is caught, and the standing caution asks for a third instance of "a mechanism that measures nothing reads exactly like one that finds nothing", one level up from where M2 sat. One level up from the oracle is the **data the guard is built from**, so that is where these aim:

4. **A realistic partial truncation.** `_committable_python_files` returns the real 429-name answer minus one required file (`scripts/check_citations.py`). Non-empty, 428 names, indistinguishable from a healthy answer by any size or truthiness test.
5. **The guard's own requirement emptied.** `ORACLE_REQUIRED_FILES = (CENSUS_MODULE, *CORPUS_REACH_FILES)` -> `ORACLE_REQUIRED_FILES = ()`, i.e. the guard still runs and requires nothing.
6. **The guard weakened to self-membership only.** `ORACLE_REQUIRED_FILES = (CENSUS_MODULE,)` — precisely the guard my predecessor prescribed, in the position Worker 2 chose. Measures whether "self plus the reach files" is pinned as a distinct claim from "self alone".
7. **`CORPUS_REACH_FILES` emptied** (the whole tuple literal -> `()`). Eleven parametrized rows then collect as zero rows, which is the classic silent-row-loss shape; this measures what, if anything, notices.

**Scope as run, identical for all seven and identical to Worker 2's recorded scope:** `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_ci_governance.py`.

**Counterfactual (no source mutation).** The dispatch's decisive question — would my predecessor's prescribed one-line fix have left the finding's own mutation at 0 rows — is answered by a standalone temp module under `docs/builder/temp-tests/slice-2-029/`, which reconstructs the pass-2 census shape with and without the prescribed guard. No production file is mutated for it.

**Pass-2 manifest subset, pre-registered.** Worker 2 reports re-running pass 2's whole manifest against the shipped bytes at 7 / 2 / 2 / 5 / 6 with identical node-id sets. I re-run **all five** rather than a subset (manifest `docs/builder/temp-tests/slice-2-029/w3p3-pass2-subset.json`, scratch root `/private/tmp/dsf-w3p3-p2`), because pass 3 added rows to the same module and only a set comparison distinguishes "unaffected" from "differently affected". Entry 1 mutates `scripts/check_citations.py` — the same disclosed out-of-list transient borrow both prior passes made; that file is byte-identical to HEAD before I start (`git show HEAD:` into a scratch path outside the repo, then `cmp`, exit 0) and is byte-proved restored afterwards.

1. `scripts/check_citations.py` #"SOURCE_TREES = (" — drop `"tests",`. (Expected 7.)
2. `tests/test_ci_governance.py::_sweep_corpus` — `EXTRA_SOURCE_FILES` replaced by `()`. (Expected 2.)
3. `tests/test_ci_governance.py::_forbidden_entries_in` — `return violations` replaced by `return []`. (Expected 2.)
4. `tests/test_ci_governance.py::_forbidden_optimizer_entries`, constructing-lambda arm — guard replaced by `if False:`. (Expected 5.)
5. `tests/test_ci_governance.py::_forbidden_optimizer_entries`, bare-class arm — condition replaced by `if False:`. (Expected 6.)

#### Re-run results — node-id SETS, not totals

Instruments under `docs/builder/temp-tests/slice-2-029/`: `w3p3-rerun.json` / `.md`, `w3p3-probes.json` / `.md`, `w3p3-probes2.json` / `.md`, `w3p3-pass2-subset.json` / `.md`, `w3p3-counterfactual.py`. Scratch roots `/private/tmp/dsf-w3p3-rerun`, `/private/tmp/dsf-w3p3-probes`, `/private/tmp/dsf-w3p3-probes2`, `/private/tmp/dsf-w3p3-p2`, all outside the repo. Every anchor verified to match **exactly once** with `--check-anchors-only` before any mutation was applied. Pre-mutation state for every entry: green, `75 passed`, pytest exit 0, 0 pre-existing failing rows. Collection/setup errors: **0 in every entry**.

| Entry | W2 rows | W3 rows | node-id set | restore |
|---|---|---|---|---|
| 1 — `_unreported_required_files` -> `return []` | 4 | **4** | **identical** (all four `…refuses_an_incoherent_oracle_answer[…]` ids) | `filecmp.cmp(shallow=False) True; sha256 1eb94c2dd194edbc... == 1eb94c2dd194edbc...` |
| 2 — oracle -> `set()` | 2 | **2** | **identical** (`…covers_every_committable_python_file`, `…git_oracle_enumerates_this_module`) | same, `1eb94c2d...` |
| 3 — oracle -> `{"conftest.py"}` | 2 | **2** | **identical** (same two ids) | same, `1eb94c2d...` |

Tool exit **0** on the re-run manifest: no entry weakly pinned, no entry carrying a collection or setup error. The shipped-file hash reproduces Worker 2's recorded `1eb94c2d…` in all three restores.

**Probes this pass added.** Scope identical to the above.

| Probe | Rows | Failing set | Reading |
|---|---|---|---|
| P4 — oracle drops **one** required file from an otherwise complete 429-name answer | **1** | `…covers_every_committable_python_file` | **the truncated-but-non-empty case is genuinely caught**, and by a realistic truncation rather than the artificial one-file answer. The live-oracle row correctly stays green (this module IS still reported), which is what proves the two rows are not one assertion twice |
| P5 — `ORACLE_REQUIRED_FILES = ()` | **4** | all four refusal ids | the guard's data emptied is equivalent to the guard removed |
| P6 — `ORACLE_REQUIRED_FILES = (CENSUS_MODULE,)` (my predecessor's rule, in Worker 2's position) | **1** | `…[only-this-module]` | self-membership alone is a **strictly weaker** guard and exactly one row says so. The four refusal ids therefore discriminate rather than restate each other |
| P7 — `CORPUS_REACH_FILES = ()` | **1** | `…[only-this-module]` | `65 passed, 1 skipped`; the eleven reach rows collapse to one skip |
| P8 — `CORPUS_REACH_FILES` narrowed 11 -> 1, keeping `conftest.py` | **0** | (none) | **`65 passed`, pytest exit 0.** Ten rows vanish, `ORACLE_REQUIRED_FILES` drops from 12 files to 2, and nothing fails — finding L1 below |

**Pass-2 manifest, re-run in full against the shipped bytes** (`w3p3-pass2-subset.md`, tool exit 0): **7 / 2 / 2 / 5 / 6**, every node-id set identical to the record — census + the six `tests/` reach rows; census + `[conftest.py]`; both planted rows; the four lambda controls + the planted lambda; the five bare controls + the planted bare. Worker 2's re-measurement claim is confirmed, not accepted. `scripts/check_citations.py` was byte-identical to HEAD before entry 1's transient borrow and is byte-identical to HEAD after it (`git show HEAD:` into a scratch path outside the repo, then `cmp`, exit 0).

**Where the second pair of eyes landed.** Re-run: **all three** of Worker 2's pass-3 entries, plus **all five** of pass 2's, plus five probes of my own, all at the recorded scope and compared as node-id sets. Accepted on Worker 2's record: **nothing**.

**No mutation is live.** `tests/test_ci_governance.py` hashes `1eb94c2dd194edbc621b8875269d38e31b4185aa81275054d89959e4f9b3e38e`; `scripts/check_citations.py` `cmp`s clean against HEAD; no `ACTIVE-MUTATION.json` or `RESTORE-FAILED.json` exists under `/tmp`, `/private/tmp`, any scratch root, or the repo; the focused suite is green at **75 passed**; `git status --porcelain` after my last probe is identical to its state before this pass.

#### The counterfactual: my predecessor's prescribed fix, decided by measurement

`BUILD.md` `## Review rounds` — a prescribed remediation is a hypothesis, never an instruction — so Worker 2's departure is the thing to audit, and the audit is empirical. `docs/builder/temp-tests/slice-2-029/w3p3-counterfactual.py` reconstructs the **pass-2** census shape (one oracle consumer, no guard at the consumer) and runs the prescribed guard against it. It mutates no production file.

```
A  pass-2 shape, oracle -> set()            : census row passes = True
B  pass-2 shape, oracle -> {'conftest.py'}  : census row passes = True
C  prescribed fix + mutation at the return  : guard fired = False | caller saw set() | census row passes = True
C' prescribed fix + truncated return        : guard fired = False | census row passes = True
D  prescribed fix + git really answers empty: guard fired = True
E  prescribed fix, healthy tree             : guard fired = False (so no row ever exercises the refusing branch)
```

**Worker 2's reasoning holds, and C is only the second-best reason for it.** C/C' confirm the stated claim directly: with the prescribed guard in place and the finding's own mutation applied — that mutation replaces the function's *returned value* — the guard passes on the discarded good answer and the census row still passes. The finding's measurement would have stayed at 0 and the fix would have been unauditable.

**E is the decisive one, and it is a rule, not a preference.** With the guard inside the producer, its refusing branch is unreachable from any healthy tree: nothing in this repository can hand `_committable_python_files` an answer to refuse. The boundary would therefore have been pinned at **0 rows** — weakly pinned, and `revision-needed` under `BUILD.md` `### Acceptance rule` — so the prescribed fix would have failed this build's own gate. The pure seam is the minimum structure that makes the refusal exercisable, and `worker-3.md`'s own standing lesson ("a guard that never ran reads exactly like a guard that found nothing") is the reason it has to be.

**In fairness to my predecessor, D says the finding and its rule were right.** With the prescribed guard in place and git *genuinely* answering empty — the real environmental case M2 named — the assert fires. The prescribed remediation would have closed the hazard; it would not have been provable that it had. Position, not rule, was the error, and Worker 2 named it correctly.

**The "0 before" figures both check out.** The `set()` row's 0 is a genuine measurement against the pass-2 bytes (`w2p3-prefix.md`, target hash `e56acf97…`, the hash pass 2 recorded as shipped). The `{"conftest.py"}` row's 0 is labelled **derived** rather than dressed as measured, which is the disclosure `BUILD.md` `## Claims are proven mechanically` asks for — and the derivation is sound, which I established rather than granted: `conftest.py` is in the sweep corpus (verified live), so `{"conftest.py"} - swept` is empty; and the shipped module has exactly **two** call sites of `_committable_python_files` (`:566`, `:595`), of which `:595` is this pass's own new row, so pass 2 had exactly one consumer. Scenario B then measures the pass-2 census body against that answer directly and it passes. Derived, checkable, and now also measured.

### High:

None.

### Medium:

None.

#### M2 — verdict: CLOSED

Named explicitly per the artifact contract. `M2 — the corpus census can be retired by its own oracle` is **closed**, re-derived rather than accepted:

- the finding's own mutation moves **0 -> 2** rows, node-id set identical to the record, and I reproduced the pre-fix 0 both from the pass-2 measurement record and by reconstructing the pass-2 census body;
- the property that distinguishes this guard from the weak `assert answer` spelling — that a **truncated-but-non-empty** answer is refused — holds against an answer I constructed myself: 428 of 429 real names, one required file missing, caught (P4). A size- or truthiness-shaped guard accepts that answer;
- the guard's removal fails **4** rows (entry 1), above the weakly-pinned threshold and above my mandatory floor, and P5/P6 show the four ids discriminate rather than restate one another;
- every one of the twelve `ORACLE_REQUIRED_FILES` members is `git ls-files --error-unmatch --cached` **tracked** and present on disk, with no duplicates, and all twelve appear in the live 429-name answer — so the guard cannot degrade into a false alarm through a member that was never tracked;
- the environmental trigger the finding named (git answering empty at exit 0 from inside an enclosing repo's ignored path) is refused;
- the docstring that M2 falsified was **corrected rather than annotated**, and I read the correction against the code: `_committable_python_files` now enumerates all three failure modes and names the mechanism refusing each, and the census's own docstring carries the matching paragraph.

**M1-era findings, against the shipped bytes.** M1, L1, L2 and L3 all remain **closed**. Pass 2's five entries re-run at 7 / 2 / 2 / 5 / 6 with node-id sets identical to the record, so pass 3's six new rows joined none of the prior boundaries' pins and retired none of them; `scripts/check_citations.py` is byte-identical to HEAD; the corpus census still re-derives 429 committable `.py` against a 429-file corpus; and the three `EXTRA_SOURCE_FILES` are still pinned by the census (pass-2 entry 2, 2 rows, reproduced).

### Low:

#### L1 — the reach list's own population is unpinned: narrowing `CORPUS_REACH_FILES` deletes ten rows and weakens the M2 guard, and nothing fails

`tests/test_ci_governance.py #"CORPUS_REACH_FILES = ("` is now load-bearing twice: it drives the eleven `::test_the_sweep_corpus_reaches_each_load_bearing_file` rows, and — new in this pass — it supplies eleven of the twelve entries of `ORACLE_REQUIRED_FILES`. Nothing pins its own contents.

**Measured** (probe P8, `w3p3-probes2.md`): narrowing the tuple from eleven entries to one, keeping `"conftest.py"`, gives `65 passed`, pytest exit **0**, **0 failing rows**, 0 collection/setup errors, against a green pre-mutation `75 passed`. Ten rows disappear and `ORACLE_REQUIRED_FILES` drops from twelve required files to two — so the guard that closed M2 is silently weakened by the same edit — and the suite reads exactly as it does today.

This is the third instance of the pattern the two prior findings are instances of, one level up from where M2 sat: M1 was "the sweep's corpus is unpinned", M2 "the census's oracle is unpinned", and this is "the guard's own requirement is unpinned". Each fix moved the fail-open shape up one level.

**Why Low and not Medium, stated so the grading is auditable.** The shipped gate measures everything it claims to right now; this is about a future edit's silent cost, not the current state. The environmental hazard M2 named stays refused after any such narrowing — git's empty answer still fails the guard while one required file remains, and git produces no *partial* truncation from any position — so what degrades is the partial-truncation protection plus ten diagnostics. And the trigger is a deliberate edit to this module's own constant, visible in the same diff as the rows it deletes, unlike M1 (an edit in another file) and M2 (no edit at all).

**What would close it,** in the module's own established idiom — `::_workflow_paths` already asserts `paths, f"no workflow files found under {WORKFLOW_DIR}"` for precisely this reason: a row asserting that `ORACLE_REQUIRED_FILES` still names at least one file **per source tree** plus this module. Worker 2's own caution against a literal count (`429` in an assertion gets "fixed" rather than investigated) is right and this shape avoids it — it asserts structure, not size.

**Test expectation:** with such a row in place, P8's mutation must fail at least one row. Today it fails zero.

**Disposition — recorded, not held.** I am not routing this back to Worker 2, and the reason is on the record rather than implied: it changes no shipped behaviour and no production line; the constant it concerns shipped in pass 2 and was accepted by two prior reviews; and *how much instrument-integrity machinery this gate should carry* is the contract-level question `worker-3.md` "The existence challenge" routes to the maintainer rather than settling inside a build loop. It is escalated under `### Notes for Worker 1 (spec reconciliation)` with resolution paths.

### DRY findings

**None new.** Checked with evidence rather than asserted:

- **Has the gate accreted across three passes?** No, and the answer is measured. The pin now carries five module-private helpers, four data tuples and roughly forty rows, and **every group has a mutation that kills only it**: the classifier arms 5 and 6 (disjoint sets), the reporter 2, the corpus spine 7, the outside-the-trees half 2, the oracle guard 4, the oracle itself 2. My own probes add the discrimination evidence a third pass owes: P5 kills all four refusal ids, P6 kills exactly one of them, P4 kills the census alone and leaves the live-oracle row green. Nothing here is dead machinery and nothing is one assertion written twice.
- **Existence challenge, raised and answered.** The candidate is `::test_the_git_oracle_enumerates_this_module`: its assertion is logically **entailed** by the census's guard, since `CENSUS_MODULE` is the first element of `ORACLE_REQUIRED_FILES`, and under every mutation I ran it fails only alongside the census row. What earns it its place is that it is the backstop for the guard's *call site* rather than for the guard — remove the census's two guard lines and the live-oracle row is the only thing left standing between an emptied oracle and a green suite. That is reasoning, not a measurement (it needs two simultaneous mutations, which `BUILD.md` `### Mutations are transient` forbids), and I record it as reasoning. Cost is one row. Not escalated.
- **Is `ORACLE_REQUIRED_FILES` a third definition of the corpus?** No. It is a requirement on git's *answer*; `_sweep_corpus()` remains the single definition of the corpus and `EXTRA_SOURCE_FILES` the single hardcoded corpus input. One list read by two assertions over two different objects.
- **Repeated literals** (`scripts/review_inspect.py`, run this pass): `conftest.py` **4x** — up from 2x, the two new uses being literal oracle answers in `INCOHERENT_ORACLE_ANSWERS`; then `permissions` / `contents` (pre-existing YAML keys) 2x, `constructing lambda` and `bare class in a sequence` 2x, `planted_schema.py` 2x. Reading the four `conftest.py` sites: two are corpus definitions, two are fabricated answers a row asserts against. Routing the fabricated ones through `CORPUS_REACH_FILES[0]` would couple the test data to the thing under test and make the assertion restate the code. Correctly left duplicated.
- **The plan's decided answers were not disturbed:** no shared `optimizer_factory()` helper, no module-level singleton, no second enforcement mechanism — nothing was added to `scripts/`, `.pre-commit-config.yaml`, or `.github/` (all clean in `git status --porcelain`).

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` is **empty**; `__all__` and the re-export list are unchanged. `git status --porcelain -- django_strawberry_framework/` is empty — this pass, like both before it, changes no package source. Every symbol the pass adds is module-private; `grep -rn` for `ORACLE_REQUIRED_FILES` / `_unreported_required_files` / `CENSUS_MODULE` / `INCOHERENT_ORACLE_ANSWERS` across `.py` and `.md` outside `docs/builder/` and `docs/shadow/` returns nothing but the module itself.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity (only when the slice touches docs, release metadata, KANBAN, or archived specs)

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. `docs/TREE.md` is clean and its two `test_ci_governance.py` rows still read `# Governance tests for the CI workflow definitions.`, byte-identical to the module docstring's first line — so the `--check` render is unaffected, as Worker 2 states. The module docstring and the coupling comment above the `check_citations` import were both re-read end-to-end and both remain true of the shipped code.

### Scoping claim — the apply pass touched one file

Confirmed independently, first, because everything two prior reviews certified would be stale if it were false:

- The eight migrated files' diff against HEAD is **91 changed lines** (`7/4, 4/2, 2/1, 4/2, 2/1, 14/7, 28/10, 2/1` by `--numstat`) — the same total both prior passes measured, digit for digit. My first attempt at this measurement returned a clean `0` because **zsh does not word-split an unquoted variable**, so the pathspec expanded to a single non-existent path; a positive control through the same pipe caught it and the number above is from an explicit path list. A "no match" from an instrument that never ran reads identically to a passing one, which is this slice's own lesson.
- `scripts/check_citations.py` byte-identical to HEAD (`git show HEAD:` into a scratch path outside the repo, `cmp` exit 0), both before and after my own transient borrow of it.
- `django_strawberry_framework/`, `docs/TREE.md`, `pyproject.toml`, `uv.lock`, `.pre-commit-config.yaml`, `.github/` and `scripts/` are all clean in `git status --porcelain`.
- The only tracked file dirty beyond Worker 2's recorded out-of-scope list is `docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md` (+4/-2), whose diff is a `[spec-029-rationale]` link-def addition and a repointed sentence — Slice 1's rationale-extraction sweep, inside `docs/SPECS/**` and out of this slice's scope in both directions. Recorded, not touched.
- **Test staleness, swept independently** rather than against the slice's file list: this pass changes no example-model field set and no wire shape (`git diff HEAD --name-only` over `examples/fakeshop/apps/*/models.py` and `django_strawberry_framework/**` is empty), so neither staleness shape `BUILD.md` `### Test staleness a focused run cannot see` names is in play. No tree is stranded.

### What looks solid

- **The departure from the prescribed fix is the right call and is now proved, not argued.** The prescribed guard would have left the finding's own measurement at 0 (C) and would itself have been pinned at 0 rows (E), i.e. `revision-needed` under this build's own acceptance rule. Worker 2 led with the weaker of its two reasons.
- **A truncated-but-non-empty answer is genuinely refused**, against a truncation I built rather than the one the tests ship: 428 of 429 real names, one required file dropped, caught.
- **The four refusal ids discriminate.** P6 kills exactly one of them and P5 kills all four, so they respond differently to different weakenings rather than being one literal written four times.
- **The two 2-row entries are two rows.** P4 separates them: the census fails alone on a partial truncation while the live-oracle row stays green.
- **`CENSUS_MODULE` cannot rot.** Derived from `__file__` against the same `REPO_ROOT` the module already defines, so it is this module's path by construction and a rename carries it.
- **All twelve required files are tracked, present, and in the live answer** — the guard cannot become a false alarm through a member git would never report.
- **Prior boundaries are exactly where they were measured.** Pass 2's full manifest re-runs at 7 / 2 / 2 / 5 / 6 with identical node-id sets, so six new rows joined no prior pin and retired none.
- **Gates green, read-only:** `ruff format --check` (`1 file already formatted`), `ruff check` (`All checks passed!`), `check_trailing_commas.py --check` (exit 0), `check_citations.py` (`OK: 789 citations resolve (712 in 426 .py files, 77 in KANBAN.md)`, whose 426 agrees with the corpus reading).
- **Counts re-derived:** `tests/test_ci_governance.py` **75 passed**; slice scope **571 passed**; live oracle **429** names; corpus 426 + 3.
- **Floor reproduces as recorded, and `.venv` is unmutated.** `/tmp/dsf-floor-029/bin/python -m pytest tests/test_ci_governance.py --no-cov -q -p no:cacheprovider` -> **75 passed**, venv re-read at Python 3.10.19 / Django 5.2.16 / strawberry-graphql 0.316.0. The shared `.venv` reads Django **6.1** / strawberry-graphql **0.323.2** at Python 3.14.2 — head, not floor — and `pyproject.toml` / `uv.lock` are clean, consistent with "no install performed".
- **No new number is owed on the hot path.** The pass changes no production line; the plan's declared metric stands from pass 1 and was reproduced in both prior reviews.

### Spec slice checklist audit — boxes 9 and 14

**No box changed state, and all 17 remain ticked and true.** Worker 2's claim checks out on the two it names:

- **Box 9** ("`tests/test_ci_governance.py` carries the classifier plus the repo-wide sweep test asserting no active `.py` constructs a schema with either forbidden optimizer form") asserts a positive property about what the module carries. Both halves still hold literally, and this pass adds to the chain that makes the sweep's silence mean something rather than altering the sweep. Still true.
- **Box 14** ("`### Failability proofs` carries one entry for the classifier boundary … plus the end-to-end control") is a claim about the artifact, not about any single pass's subsection — `ARTIFACT.md` scopes each `### Failability proofs` block to the boundaries *that pass* introduced, and pass 3 introduced one. The classifier entry and the end-to-end control are carried by pass 1's block and were re-measured in pass 2 and again by Worker 2 and by me this pass at 5 / 6 with identical sets. Still true.
- Pass 2's box-11 wording recommendation stands unchanged and is Worker 1's to enact; this pass adds no further corpus input, so nothing about it moved.

### Static helper use

`uv run python scripts/review_inspect.py tests/test_ci_governance.py --output-dir docs/shadow` — **run** this pass, not inherited. The trigger fires (~105 new lines to a `.py` outside `django_strawberry_framework/`, over the 50-line threshold), and Worker 2 correctly named the trigger rather than claiming the skip. Output: **4 control-flow hotspots** (`_forbidden_optimizer_entries` 36 lines / 8 branch nodes and `test_checkout_steps_do_not_persist_credentials` 19 / 8, both pre-existing; `test_the_sweep_corpus_covers_every_committable_python_file` 44 lines / **0** branch nodes and the gate row 45 / 0 — the growth in both is docstring, and the new seam adds no branch); **no Django/ORM markers**; 7 imports with the one cross-folder import unchanged; and the six repeated literals discussed above, of which only `conftest.py`'s count moved. Nothing that changes a finding. **Skips:** none owed — this pass touched exactly one file.

### Temp test verification

- `docs/builder/temp-tests/slice-2-029/w3p3-rerun.json` / `.md` — independent re-runs of all three of Worker 2's pass-3 entries at the recorded scope. Die with the cycle.
- `docs/builder/temp-tests/slice-2-029/w3p3-probes.json` / `.md`, `w3p3-probes2.json` / `.md` — five narrowings no pass had tried. **Probe P8 caught a real gap**, recorded as Low finding L1 with the disposition stated there; the manifests are not promoted.
- `docs/builder/temp-tests/slice-2-029/w3p3-pass2-subset.json` / `.md` — pass 2's full manifest re-run against the shipped bytes. Not promoted.
- `docs/builder/temp-tests/slice-2-029/w3p3-counterfactual.py` — the prescribed-fix counterfactual. It proves a fact about a shape that was never shipped, so there is nothing to promote; its value is the record.
- Earlier passes' artifacts in that directory are theirs; none is promoted, and `test_hot_path_budget.py` is correctly still unpromoted.

### Notes for Worker 1 (spec reconciliation)

- **Escalated: the reach list's own population is unpinned (Low finding L1).** Narrowing `tests/test_ci_governance.py #"CORPUS_REACH_FILES = ("` from eleven entries to one gives `65 passed`, exit 0, **0 failing rows** — ten rows deleted and the M2 guard's requirement cut from twelve files to two, silently. Resolution paths, for the maintainer through you: **(a)** add one structural row asserting `ORACLE_REQUIRED_FILES` still names at least one file per source tree plus this module — the module's own `::_workflow_paths` idiom, one line, no literal count; **(b)** accept it as the level at which this gate stops chasing its own instruments, on the ground that any such narrowing is an edit to the gate module itself and visible in the same diff as the rows it deletes; **(c)** fold it into Slice 3 alongside the Amendment 2 work. I did not hold the slice on it — no shipped behaviour or production line is affected, the constant shipped in pass 2 under two prior accepted reviews, and "how much instrument-integrity machinery this gate should carry" is the contract-level question `worker-3.md` routes to the maintainer rather than settling in a build loop.
- **The Amendment 2 parallel-site escalation remains Slice 3's** and was not acted on, per the dispatch. Pass 1's Amendments 1-3 stand exactly as both prior reviews judged them.
- **`docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md` is dirty (+4/-2)** from Slice 1's link sweep — a `[spec-029-rationale]` definition and one repointed sentence. Out of Slice 2's scope in both directions; flagged only so the final gate's file inventory does not read it as Slice 2 churn.
- **No spec text was read as false by this pass, and I requested no spec edit.**

### Review outcome

`review-accepted`.

**M2: closed** — verdict given by name above, re-derived rather than accepted. The M1-era findings (M1, L1, L2, L3) all remain closed against the shipped bytes, proved by re-running pass 2's whole manifest at 7 / 2 / 2 / 5 / 6 with identical node-id sets. No High, no Medium.

One Low (**L1**), measured at 0 failing rows, recorded above with its reason for not being held and escalated to Worker 1 under `### Notes for Worker 1 (spec reconciliation)` with three resolution paths.

The scoping claim is confirmed independently at 91 changed lines across the eight migrated files with `scripts/check_citations.py` byte-identical to HEAD; no mutation is live; all three of Worker 2's pass-3 proofs reproduce at the recorded scope with identical node-id sets and the shipped hash `1eb94c2d…`; the floor run reproduces at 75 passed on Python 3.10.19 / Django 5.2.16 / strawberry-graphql 0.316.0 with the shared `.venv` unmutated at head; the slice scope is 571 passed; and all 17 checklist boxes remain ticked and true.

Status set to `review-accepted`; routes to **Worker 1** for final verification.

---

## Final verification (Worker 1)

Every figure below was re-derived in this pass. Nothing is carried on the chain's word, including Worker 3's grading of L1 and its assurance that the seventeen boxes are true.

### Spec status-line re-verification

`docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md:1-9` re-read. Lines 1-7 describe a shipped card and a version boundary this slice does not touch; line 9's rationale-companion pointer resolves. Nothing this slice landed falsifies a status line, so **no spec edit is made in this pass** — and DoD item 4's text is Slice 3's to reconcile, not this slice's.

### Contract delivered

- **The forbidden-form regression is repaired at every site.** Re-derived with my own AST classifier (built in this pass, not Worker 1's plan copy and not Worker 2's `classify.py`), run twice: once over `git ls-tree -r HEAD` content read through `git show HEAD:<path>`, once over the working tree. **HEAD: 25 entries in 8 files — 18 constructing lambdas + 7 bare-class-in-a-sequence**, distributed `test_relay_connection.py` 10, `optimizer/test_extension.py` 7, `test_products_visibility_api.py` 2, `mutations/test_resolvers.py` 2, and one each in `strategy_schemas.py`, `forms/test_resolvers.py`, `mutations/test_write_transaction.py`, `types/test_resolvers.py`. **Working tree: 0.** Digit-for-digit agreement with the plan's table, Worker 2's Step 0, and Worker 3's independent re-derivation — four instruments, one reading.
- **Maintainer decision D1's standing pin shipped.** `tests/test_ci_governance.py::test_no_active_source_uses_a_forbidden_optimizer_extensions_form` plus the classifier, the 9+9 controls, the corpus census, the eleven reach rows, the reporter seam, and the oracle guard. Nothing was added to `scripts/`, `.pre-commit-config.yaml`, or `.github/` — D1's placement decision holds (`git status --porcelain -- scripts/ .github/` empty; `.pre-commit-config.yaml` absent from the diff).

### Spec slice checklist audit — all 17 boxes

Audited against the diff, not against the two prior audits. **No box is un-ticked and no box needed ticking.** How each load-bearing tick was proved in this pass:

| Box | Proof run here |
|---|---|
| 1 population re-derived | my own AST classifier over HEAD and the working tree: 25/8 -> 0 |
| 2 seven bare-class migrated | classifier by kind at HEAD: `bare class in sequence` **7**; 0 now |
| 3 eighteen lambdas migrated, kwargs variants included | classifier by kind at HEAD: `constructing lambda` **18**; 0 now |
| 4 function-local everywhere | AST walk over all 8 files for a `DjangoOptimizerExtension(...)` construction at module scope: **none** |
| 5 five conditional sites construct nothing on `else` | read all five: four `if optimizer:` blocks in `test_relay_connection.py` (`:1031`, `:1114`, `:1505`, `:1707`) and `strategy_schemas.py`'s `if strategy is not None:`, each with `extensions = []` above and the construction inside the block |
| 6 the two-strictness pair carries two locals | `tests/optimizer/test_extension.py:5602` `raising_optimizer` / `:5611` `silent_optimizer`, each behind its own `lambda:` |
| 7 `build_strategy_schema` docstring corrected, module docstring unchanged | function docstring now reads "mounted on ONE `DjangoOptimizerExtension` per built schema"; `diff` of the file's first 20 lines against `git show HEAD:` — **identical** |
| 8 no assertion weakened | `git diff -U0` over the 8 migrated files, added/removed lines only, grepped for `assert` / `@pytest` / `pytest.mark` / `skip` / `xfail` — **exit 1, no match**. `--numstat` totals 63 added / 28 removed = **91 changed lines**, the figure both prior passes measured |
| 9 classifier + repo-wide sweep present | read `::_forbidden_optimizer_entries` and `::test_no_active_source_uses_a_forbidden_optimizer_extensions_form` end to end |
| 10 9+9 controls present and green | `MUST_FLAG_SNIPPETS` 9 / `MUST_NOT_FLAG_SNIPPETS` 9, both parametrized, both green in the 75-row run |
| 11 corpus scoped through `check_citations`, coupling in a comment | `from scripts.check_citations import iter_python_sources` under a 10-line coupling comment; `_sweep_corpus()` unions it with `EXTRA_SOURCE_FILES`. See the note below |
| 12 module docstring widened, coverage note accurate | first line byte-identical to HEAD (the `build_tree_md --check` constraint), paragraphs below name both corpora, coverage note now reads "YAML under `.github/` and the text of first-party `.py` files" — true of the shipped assertions |
| 13 deliberate non-extensions + false-positive direction recorded | both in the sweep's docstring, and both arms' over-matches are enumerated (L2's fix) |
| 14 failability record | present in all three build reports; every field `BUILD.md` `### What gets recorded` requires, byte-comparison evidence included, zero collection/setup errors, no zero-row entry |
| 15 hot-path both readings | re-run here, reproduces exactly (below) |
| 16 floor verification recorded, `.venv` unmutated | re-read here (below) |
| 17 ruff scoped, `git status --short` slice-intended | `git status --short` shows exactly the 9 slice files plus the recorded out-of-scope set; `pyproject.toml`, `uv.lock`, `django_strawberry_framework/`, `docs/TREE.md`, `scripts/` all clean |

**Box 11 is ticked and true as written, and its text is deliberately left alone.** Worker 2 (pass 2) recommended widening it to mention the three files `EXTRA_SOURCE_FILES` adds, and Worker 3 ruled the box a positive property the addition does not falsify. I agree on both counts: `iter_python_sources()` is still the corpus's spine and the comment still names the coupling, so the tick is not an over-tick. Rewriting the box text now would falsify two prior audits of a box whose contract did land; the recommendation is carried forward below instead of enacted.

### L1 — verdict: **NOT ACCEPTED. Closed in code, routed back to Worker 2.**

**The measurement is true, re-derived here rather than accepted.** `scripts/prove_failability.py` over my own manifest (scratch root outside the repo; anchor matched exactly once; unmutated baseline `75 passed`, exit 0; restore byte-proved `sha256 1eb94c2d… == 1eb94c2d…`):

| Narrowing of `tests/test_ci_governance.py #"CORPUS_REACH_FILES = ("` | Rows failed | Result |
|---|---|---|
| 11 entries -> 1, keeping `"conftest.py"` (Worker 3's P8) | **0** | `65 passed`, pytest exit 0, 0 collection/setup errors |
| 11 entries -> 1, keeping `"django_strawberry_framework/optimizer/extension.py"` (mine) | **1** | `1 failed, 64 passed`; the row is `::test_the_corpus_census_refuses_an_incoherent_oracle_answer[only-this-module]` |

Worker 3's figure reproduces exactly. Ten rows vanish and `ORACLE_REQUIRED_FILES` falls from twelve required files to two, with nothing failing.

**The second row is mine and it is what decides the ruling.** The only thing that fires on *any* narrowing is a row that fires by accident: `INCOHERENT_ORACLE_ANSWERS`'s `only-this-module` entry hardcodes the literal `"conftest.py"` as the path it expects to be reported unmet, so a narrowing that *keeps* `conftest.py` is silent while one that drops it trips a control row written for an unrelated purpose. That is the identical shape this build already ruled insufficient at M1 — *"the pin's protection is a side effect of where citations happen to point, which is not a contract."* Having ruled once that side-effect protection is not protection, this cycle cannot accept it one level up without contradicting itself.

**On whether this instance is genuinely different from the two that were fixed — it is, and not enough.** Worker 3's grading is honest about the difference and it is real: M1's trigger was an edit in *another* file (`scripts/check_citations.py`) that left `check_citations` itself green, and M2's was no edit at all — an environmental condition. L1's trigger is an edit to this module's own constant, nine lines above the `ORACLE_REQUIRED_FILES` that consumes it, visible in the same diff as the rows it deletes. That is a materially weaker threat model and it is why Low rather than Medium is the right tier. It is not why the finding can be left open: visibility to a reviewer is not a gate, and "a rule with no gate rots" is the whole premise maintainer decision D1 rests on. A pin whose own requirement can be halved by a one-tuple edit is the same argument the pin was built to answer.

**The right closure is one guard that covers the class, not a third point-guard — and the class terminates here.** The framing I was handed, that the two prior guards were each written against the narrowing that had just been measured, does not survive reading them: Worker 2 explicitly rejected the representative-per-tree row at M1 as "four spellings of *a tree was dropped*" and built a census against an independent oracle, then verified it against three narrowings nobody had tried (11, 11, 9 rows); at M2 it explicitly rejected `assert answer` as one spelling and required *named* files, verified against a realistic 428-of-429 truncation. Both were answer-shaped. What actually recurs is narrower and is the class to guard: **every hardcoded tuple this gate reads must have an independent contradictor.** Measured against the shipped module:

- `EXTRA_SOURCE_FILES` — contradicted by the git census (pass-2 entry 2: emptying it fails 2 rows). Pinned.
- `check_citations.SOURCE_TREES` — contradicted by the census and the reach rows (pass-2 entry 1: 7 rows). Pinned.
- `CORPUS_REACH_FILES` / `ORACLE_REQUIRED_FILES` — contradicted by **nothing**. It is the only one of the three that feeds assertions without also feeding the answer, so no oracle disagrees with it.

The property to guard is the answer that tuple gives: *this requirement is strong enough that no corpus narrowing and no oracle truncation can pass it*. The structure that makes that true is that `ORACLE_REQUIRED_FILES` names this module, at least one file inside **every** tree the corpus is built from, and at least one of the modules `EXTRA_SOURCE_FILES` adds outside them. Stated that way the guard writes down **no new data of its own** — it derives its expectations from `check_citations.SOURCE_TREES` and `EXTRA_SOURCE_FILES`, both already independently contradicted above, exactly as `CENSUS_MODULE` is derived from `__file__` rather than written. That is what ends the regress rather than extending it by one level, and it is the reason a deferral is not the cheaper option: the fix is cheap and final *now*, and every pass that defers it pays the same cost later with one more level of machinery on top.

**Required of Worker 2** (a prescribed fix is a hypothesis — `BUILD.md` `## Review rounds`; Worker 2 owns the shape):

- One row set asserting the structural property above, in the module's own idiom (`::_workflow_paths`'s `assert paths, …`), deriving its expectations from `SOURCE_TREES` and `EXTRA_SOURCE_FILES` rather than from a fourth literal list, and **never** from a count — Worker 2's own caution that `429` in an assertion gets "fixed" rather than investigated is right and applies here.
- **Test expectation, derived here so it is auditable rather than asserted:** with the guard in place, *both* narrowings in my table must fail. Narrowing to `conftest.py` alone leaves `django_strawberry_framework`, `examples` and `scripts` unrepresented (3 rows); narrowing to the optimizer module alone leaves `examples`, `scripts` and the `EXTRA_SOURCE_FILES` half unrepresented (3 rows). Neither is 0 or 1, so the new boundary is not itself weakly pinned. Today both fail 0 and 1.
- Nothing else in the slice is reopened. The 25-site repair, the 91 changed lines, the conditional `else` branches, the classifier, the census, the oracle guard, the hot-path number and the floor run are all verified here and none of them is disturbed by this fix.

Recorded against the alternative I am refusing: a deferral to `bld-final-029.md`'s `### Deferred work catalog` is the "recorded exception" `BUILD.md` `### Acceptance rule` names, and `AGENTS.md` rule 4's ban on defer-the-real-fix sequencing applies with the fix already designed, scoped to one open file, and needing no spec context. Three build passes and three reviews already spent is an argument for making the fourth the last one, not for stopping one row short.

### Obligations the plan declared

- **Hot-path number — exists and reproduces exactly as recorded.** `uv run pytest docs/builder/temp-tests/slice-2-029/test_hot_path_budget.py --no-cov -q -n0 -s` re-run in this pass: identity reading `False / False / True`; cache reading — constructing lambda builds **2** instances, each `CacheInfo(hits=0, misses=1, size=1)`, aggregate `misses=2, hits=0`; singleton factory builds **1**, `CacheInfo(hits=1, misses=1, size=1)`, aggregate `misses=1, hits=1`. **misses 2 -> 1, hits 0 -> 1**, the plan's declared metric. Whether the trade is acceptable is the maintainer's call, not mine; the obligation is that the number exists next to the change and reaches them.
- **Floor verification — ran, recorded, and still verifiable.** `/tmp/dsf-floor-029/bin/python -V` reads **3.10.19**; `uv pip list --python /tmp/dsf-floor-029/bin/python` reads **django 5.2.16**, **strawberry-graphql 0.316.0**, pytest 9.1.1 — the recorded numbers, re-read rather than trusted, and the floor `BUILD.md` `## Floor verification` names. The plan assigned the run to Worker 2's build pass and it happened there; this gate is the backstop and confirms it.
- **The shared `.venv` is unmutated.** `uv pip list` reads django **6.1** / strawberry-graphql **0.323.2** and `.venv/bin/python -V` reads **3.14.2** — head, not floor. `git status --short -- pyproject.toml uv.lock` is empty.
- **No mutation is live.** `tests/test_ci_governance.py` hashes `1eb94c2dd194edbc621b8875269d38e31b4185aa81275054d89959e4f9b3e38e`, the hash Worker 2 and Worker 3 both recorded as shipped, and it hashes the same *after* my own two probes. `scripts/check_citations.py` `cmp`s byte-identical against `git show HEAD:` into a scratch path outside the repo. No `ACTIVE-MUTATION.json` or `RESTORE-FAILED.json` exists under `/tmp`, `/private/tmp`, or the repo. Three passes ran failability proofs in this tree and all three left it clean.

### Failability and fail-open checks (Worker 1's two confirmations)

- **The record exists for every new boundary.** Pass 1: the classifier's two arms, mutated separately (4 and 5 rows). Pass 2: the corpus spine (7), `_sweep_corpus`'s outside-the-trees half (2), the reporter seam (2), plus both arms re-proved against the shipped bytes (5 and 6). Pass 3: `_unreported_required_files` (4) plus the finding's own two mutations as controls (2 and 2). Every entry carries the mutation, the scope as run, the pre-mutation state, the failing node ids **listed**, collection/setup errors **separately** at 0, and the revert proved by byte-comparison. No zero-row entry anywhere, so no `why 0` is owed. The one refused mutation (a `SyntaxError` that collection-errored and was reported as `INVALID COUNT` rather than banked as a measured zero) is disclosed in pass 1 — the right kind of record.
- **No fail-open shape landed, with one exception, and it is L1.** I read the shipped gate for the catalogued shapes rather than trusting the green run. `_committable_python_files` uses `check=False` with an explicit `returncode` assert (fail-closed), raises on a missing `git` (fail-closed), and its empty-but-exit-0 answer is refused by `_unreported_required_files` (M2's fix). `_forbidden_optimizer_entries` calls `ast.parse` with **no** `try` / `except SyntaxError`, so an unparseable file errors the row rather than being silently skipped — the obvious fail-open in a source sweep, and it is absent. `_sweep_corpus`'s `if path.is_file()` filter drops a vanished `EXTRA_SOURCE_FILES` entry, but git's `--cached` still lists a tracked-and-deleted path, so the census fails rather than narrowing: fail-closed. `_forbidden_entries_in`'s `is_relative_to` fallback is not on a decision path and is pinned by the planted rows. The remaining shape is the unpinned requirement tuple, which is L1.

### Gates re-run in this pass

| Command | Result |
|---|---|
| `uv run ruff format --check .` | **pass** — `429 files already formatted` |
| `uv run ruff check .` | **pass** — `All checks passed!` |
| `uv run python scripts/check_trailing_commas.py --check` | **pass** — exit 0 |
| `uv run python scripts/check_citations.py` | **pass** — `OK: 789 citations resolve (712 in 426 .py files, 77 in KANBAN.md)` |
| `uv run pytest tests/test_ci_governance.py --no-cov -q -p no:cacheprovider` | **pass** — `75 passed` |
| slice scope, the 8 migrated files + the pin | **pass** — `571 passed` |

No `--cov*` flag in any command of this pass. Staged-anchor sweep for `TODO(spec-029` / `TODO-…-029` across the tree: **no live anchor** — every hit is prose inside the spec's scaffolding section, the rationale companion's rev7 record, or a sibling spec's superseded-card list.

### DRY check across this slice and prior accepted slices

No new duplication. Slice 1 touched only `docs/SPECS/**`, so there is no shared code surface between the two slices to duplicate. Within this slice, the 25 repaired sites adopt the idiom already carried by the ~81 pre-existing `lambda: <instance>` entries rather than introducing a second spelling, and the plan's decided answer against a shared `optimizer_factory()` helper was not disturbed. `docs/builder/temp-tests/slice-2-029/classify.py` is a second copy of the pin's rule and dies with the cycle; the build report says so plainly, which is the right disposition.

### Spec changes made (Worker 1 only)

**None.** No box is left `- [ ]`, so no deferral reason is owed under this heading. No spec text was falsified by what this slice landed; DoD item 4's reconciliation against what shipped is Slice 3's, per the plan's ownership table and the sequencing that makes Slices 2 and 3 ordered rather than parallel.

### Notes for Worker 1 (spec reconciliation) — what Slice 3 inherits

1. **Amendment 2 — DoD item 4 restated by FORM, and the one-shot-grep framing lives at TWO sites.** `## Definition of done` item 4 is the site Amendment 2 quotes; the second is the spec's `## Slice checklist` `#"Post-migration forbidden-form gate:"` bullet, which says a grep for the **exact forbidden forms** finds zero hits. Restating only item 4 leaves the checklist still naming the instrument that under-reported this regression by 13 of 18 sites — the parallel-site skip this repo's residual cycles call their dominant defect. **Both sites are restated or the divergence is not discharged.** Worker 3's three resolution paths stand: (a) restate both by form and point both at the standing pin; (b) restate item 4 and delete the checklist bullet's gate clause as superseded; (c) keep the checklist bullet as an explicit historical snapshot and say so. Any of the three is a decided answer; silence on the second site is not.
2. **The pin's own name for Slice 3 to cite** is `tests/test_ci_governance.py::test_no_active_source_uses_a_forbidden_optimizer_extensions_form`, and the new link definition it needs is `[test-ci-governance]: ../../tests/test_ci_governance.py` under the spec's `<!-- tests/ -->` group. Measured population for the replacement text: **25 forbidden entries in 8 files before the repair, 0 after**, alongside ~81 already-correct `lambda: <instance>` entries.
3. **"Active first-party source" now means something exact** — every `.py` that `git ls-files --cached --others --exclude-standard` reports, which the census asserts the gate covers, and which the oracle guard refuses to reason from when git did not answer about this checkout. Worth saying precisely if the DoD replacement uses the phrase, since three tracked `.py` files sit outside `SOURCE_TREES` and are carried by `EXTRA_SOURCE_FILES`.
4. **Amendment 3 — Decision 3's granularity example.** The same-function `strictness="raise"` / `strictness="off"` pair at `tests/optimizer/test_extension.py:5602`/`:5611` is a strictly better example than the cross-module one the spec currently uses, and the `~41` figure in that same sentence is one of the stale census numbers (build-plan divergence 9). Verified present in this pass.
5. **Amendment 1 is NOT Slice 3's.** `tests/test_ci_governance.py`'s first docstring line under-describes the module, but rewriting it requires regenerating `docs/TREE.md`, which is outside the maintainer's fence. It belongs in `bld-final-029.md`'s `### Deferred work catalog`, not the spec. The recommended replacement and the two `docs/TREE.md` sites are recorded in pass 1's `### Notes for Worker 1`.
6. **Box 11's wording recommendation** (pass 2) is likewise a note for the record, not a spec item: the box is true as written and is deliberately unedited.

### For `bld-final-029.md`'s `### Deferred work catalog`

Carried, not fixed — all outside the maintainer's spec-files-and-`.py`-files fence:

- `tests/test_ci_governance.py`'s first docstring line and the two `docs/TREE.md` rows it renders (`:455`, `:681`) — Amendment 1.
- `docs/TREE.md` is stale at HEAD by exactly two lines, both for the concurrent session's untracked `tests/mutations/test_operations.py`. Not this slice's, verified byte-clean and absent from the diff.
- `CHANGELOG.md:173`, `:184`, `:186` carry 0.0.7-era consumer snippets showing the deprecated instance form.
- `KANBAN.md:3597`, `:3603` — the `DONE-029` card body still names the rejected migration targets as Slice 1's goal.
- `docs/bug_hunt/temp-tests/resolvers_async_parity/` holds 4 forbidden-form entries in gitignored scratch, outside the pin's corpus by design.

### Summary

The slice delivered its contract: the `extensions=` forbidden-form regression is repaired at all 25 sites in 8 files with 0 remaining anywhere in first-party source, no assertion was weakened across 91 changed lines, and maintainer decision D1's standing governance pin shipped with a classifier, 9+9 controls, a git-oracle corpus census, per-file reach rows, a reporter seam and an oracle-completeness guard. All 17 checklist boxes are ticked and true. The hot-path number exists and reproduces at `misses 2 -> 1`, `hits 0 -> 1`; the floor run happened at Django 5.2.16 / Python 3.10.19 / strawberry-graphql 0.316.0 with the shared `.venv` unmutated; no mutation is live; every gate is green.

One finding blocks acceptance. **L1 is not accepted.** Its measurement reproduces at 0 failing rows, and a second narrowing I ran shows the only protection that exists is an accident of a `"conftest.py"` literal in an unrelated control row — the same side-effect-is-not-a-contract shape this build already ruled insufficient at M1. It closes with one structural row deriving its expectations from `SOURCE_TREES` and `EXTRA_SOURCE_FILES` rather than a fourth literal list, which guards the class instead of the third spelling and ends the regress rather than extending it.

### Final status

`revision-needed` — routed to **Worker 2** for L1 only. Nothing else in the slice is reopened. The artifact's top-level `Status:` line is set to match.

---

## Build report (Worker 2, pass 4)

Scope of this pass: **L1 and nothing else.** No migrated file is reopened, no assertion is
re-pinned, no box state is changed. One file is edited, `tests/test_ci_governance.py`.

### L1 — `CORPUS_REACH_FILES` / `ORACLE_REQUIRED_FILES` had no independent contradictor (closed)

The finding, restated as measured rather than as inherited: `ORACLE_REQUIRED_FILES` is the
only hardcoded tuple this gate reads that feeds **assertions without also feeding an
answer**. `EXTRA_SOURCE_FILES` is contradicted by the git census; `check_citations`'s
`SOURCE_TREES` is contradicted by the census and the reach rows; the requirement tuple was
contradicted by nothing, so halving it deleted ten reach rows and cut the oracle guard from
twelve required files to two with the module still green. The one row that fired on Worker
1's second narrowing fired because `INCOHERENT_ORACLE_ANSWERS`'s `only-this-module` entry
hardcodes the literal `"conftest.py"` for an unrelated purpose — protection by side effect,
the shape this build already ruled insufficient at M1.

**What landed** — one structural property, asserted per region, deriving every expectation
from definitions this module already contradicts:

- `tests/test_ci_governance.py #"CORPUS_REGIONS = ("` — the region vocabulary, `(CENSUS_MODULE,
  *SOURCE_TREES, EXTRA_FILES_REGION)`. `CENSUS_MODULE` is already derived from `__file__`;
  `SOURCE_TREES` is imported from `scripts/check_citations.py` (the import at `:37` widens to
  `SOURCE_TREES, iter_python_sources`); `EXTRA_FILES_REGION` is a **label**, not a path, so it
  cannot be mistaken for one. **No fourth literal list was introduced** — that was the point
  of the shape, since a fourth list would need a fifth contradictor.
- `tests/test_ci_governance.py::_unrepresented_corpus_regions` — a pure function over one
  requirement tuple returning the regions it names no file inside. Pure, because the shipped
  requirement can never exercise the refusing branch, and a branch that never ran reads
  exactly like one that found nothing. Third instance of the seam shape this module already
  uses twice (`_forbidden_entries_in`, `_unreported_required_files`).
- `tests/test_ci_governance.py::test_the_oracle_requirement_reaches_every_corpus_region` —
  6 rows, one per region, asserting the live `ORACLE_REQUIRED_FILES` reaches it. A narrowing
  now fails **by naming the region it cost**, not by a count and not by a copy of the tuple.
- `tests/test_ci_governance.py::test_a_narrowed_oracle_requirement_names_the_region_it_lost` —
  5 rows over `NARROWED_REQUIREMENTS`, the refusing direction. The narrowed requirements are
  themselves built from `SOURCE_TREES` / `EXTRA_SOURCE_FILES` (`f"{tree}/anything.py"`,
  `SOURCE_TREES[0]`), so they keep narrowing in a real direction if the corpus definitions
  move.

**The numbers I measured, against the two Worker 1 handed me.** Worker 1 derived 3 rows under
each narrowing. Narrowing A reproduces exactly; narrowing B measures **4**, not 3 — three new
region rows plus the pre-existing `only-this-module` control that was the accidental
protection all along. Worker 1's derivation of *the new boundary's* contribution is right in
both cases (3 and 3); the total for B is one higher because the accidental row is still there
and still fires. Reported as measured:

| Narrowing of `#"CORPUS_REACH_FILES = ("` | Before this pass | After | New rows | Pre-existing |
|---|---|---|---|---|
| 11 entries -> 1, keeping `"conftest.py"` | **0** | **3** | 3 | 0 |
| 11 entries -> 1, keeping the optimizer module | **1** | **4** | 3 | 1 (`::test_the_corpus_census_refuses_an_incoherent_oracle_answer[only-this-module]`) |

Neither is 0 or 1, so the new boundary is not itself weakly pinned, and neither result rests
on the accidental row: narrowing A's three rows fire with `conftest.py` still present.

### Files touched

- `tests/test_ci_governance.py` — the only file this pass writes. Added `SOURCE_TREES` to the
  `check_citations` import, `EXTRA_FILES_REGION` / `CORPUS_REGIONS`,
  `_unrepresented_corpus_regions`, `NARROWED_REQUIREMENTS`, and the two test functions above.
  Nothing existing was edited, removed, or re-worded — `CORPUS_REACH_FILES`,
  `ORACLE_REQUIRED_FILES`, `INCOHERENT_ORACLE_ANSWERS` and every prior row are byte-unchanged.

`git status --short` after both ruff invocations lists the same nine slice files plus the
recorded out-of-scope set (`docs/SPECS/appx/spec-004-…-rationale.md`,
`docs/review/review-0_0_14.md`, `docs/review/rev-*.md`, `tests/mutations/test_operations.py`,
and this cycle's own untracked artifacts). `docs/TREE.md`, `scripts/`, `pyproject.toml`,
`uv.lock`, `django_strawberry_framework/` are all clean.

### Tests added or updated

- `tests/test_ci_governance.py::test_the_oracle_requirement_reaches_every_corpus_region` — 6
  rows (`tests/test_ci_governance.py`, `django_strawberry_framework`, `tests`, `examples`,
  `scripts`, `outside-the-source-trees`). Pins that the requirement the census's oracle guard
  enforces stays as wide as the corpus it is asked about.
- `tests/test_ci_governance.py::test_a_narrowed_oracle_requirement_names_the_region_it_lost` —
  5 rows (`names-nothing`, `only-this-module`, `only-outside-the-trees`,
  `every-tree-but-nothing-outside-them`, `every-region-but-one-tree`). Pins the refusing
  direction the live tree cannot produce.

Module row count: **75 -> 86** (+11). Slice scope: **571 -> 582** (+11). No row was removed.

### Validation run

- `uv run ruff format tests/test_ci_governance.py` — pass (`1 file left unchanged`).
- `uv run ruff check --fix tests/test_ci_governance.py` — pass (`All checks passed!`).
- `uv run python scripts/check_trailing_commas.py tests/test_ci_governance.py` — pass
  (`Fixed 0 file(s)`), run rather than guessed at, per the layout rule.
- `git status --short` after both ruff invocations — every modified path slice-intended or in
  the recorded out-of-scope set. No stop-and-report.
- `uv run pytest tests/test_ci_governance.py --no-cov -q -p no:cacheprovider` — **86 passed**.
- Slice scope (the 8 migrated files + the pin) — **582 passed**.
- `uv run ruff format --check .` — pass (`429 files already formatted`).
- `uv run ruff check .` — pass. `scripts/check_trailing_commas.py --check` — exit 0.
- `uv run python scripts/check_citations.py` — pass (`789 citations resolve`).
- `uv run python scripts/build_tree_md.py --check` — reports `docs/TREE.md` not up to date, as
  it did at HEAD. Rendered into a scratch copy **outside** the generated doc
  (`--md /tmp/dsf-p4-tree-copy.md`) and diffed: exactly the two pre-existing
  `tests/mutations/test_operations.py` rows from the concurrent session. **This pass adds no
  `docs/TREE.md` row** and the file is absent from the diff. The generator was never run
  against `docs/TREE.md`.

No `--cov*` flag in any command of this pass.

### Failability proofs

Run with `uv run python scripts/prove_failability.py
docs/builder/temp-tests/slice-2-029/proofs-pass4.json --output
docs/builder/temp-tests/slice-2-029/proofs-pass4.md`; scratch root
`/tmp/dsf-failability-slice-2-029-pass4`, **outside** the repo; anchors verified with
`--check-anchors-only` first (all three matched exactly once **before** any copy was taken);
tool exit **0**. Pre-mutation baseline for every entry: `86 passed`, pytest exit 0, 0
pre-existing failing rows. Restore proved for every entry by
`filecmp.cmp(shallow=False) True` plus `sha256 307dbd9a02f59e69… == 307dbd9a02f59e69…` against
the pre-mutation copy. No zero-row entry, so no `why 0` is owed.

- `tests/test_ci_governance.py::_unrepresented_corpus_regions` — mutation applied:
  `return unrepresented` -> `return []`, so the guard reports every requirement as reaching
  the whole corpus and no narrowing is ever named (the boundary is **gone**, not perturbed,
  while both call sites still read as guarded); scope as run:
  `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE
  tests/test_ci_governance.py`; pre-mutation state of that scope: `86 passed`, exit 0;
  failing node ids: `::test_a_narrowed_oracle_requirement_names_the_region_it_lost[names-nothing]`,
  `[only-this-module]`, `[only-outside-the-trees]`, `[every-tree-but-nothing-outside-them]`,
  `[every-region-but-one-tree]` — **5 rows**; collection/setup errors: **0**; revert proved by
  byte-comparison: `filecmp.cmp(shallow=False) True; sha256 307dbd9a… == 307dbd9a…`.
- `tests/test_ci_governance.py #"CORPUS_REACH_FILES = ("` (L1 narrowing **A**) — mutation
  applied: the eleven-entry tuple replaced wholesale by `CORPUS_REACH_FILES =
  ("conftest.py",)`, i.e. the requirement the guard defends is removed down to one entry —
  Worker 3's P8 and Worker 1's first probe, **0 failing rows before this pass**; scope as run:
  as above; pre-mutation state: `86 passed`, exit 0; failing node ids:
  `::test_the_oracle_requirement_reaches_every_corpus_region[django_strawberry_framework]`,
  `[examples]`, `[scripts]` — **3 rows**, all new; collection/setup errors: **0**; revert
  proved by byte-comparison: `filecmp.cmp(shallow=False) True; sha256 307dbd9a… == 307dbd9a…`.
- `tests/test_ci_governance.py #"CORPUS_REACH_FILES = ("` (L1 narrowing **B**) — mutation
  applied: the same tuple replaced by
  `CORPUS_REACH_FILES = ("django_strawberry_framework/optimizer/extension.py",)` — Worker 1's
  decisive second probe, the one that exposed the accidental protection, **1 failing row
  before this pass**; scope as run: as above; pre-mutation state: `86 passed`, exit 0; failing
  node ids: `::test_the_corpus_census_refuses_an_incoherent_oracle_answer[only-this-module]`
  (the pre-existing accidental row), `::test_the_oracle_requirement_reaches_every_corpus_region[examples]`,
  `[scripts]`, `[outside-the-source-trees]` — **4 rows**, three of them new;
  collection/setup errors: **0**; revert proved by byte-comparison:
  `filecmp.cmp(shallow=False) True; sha256 307dbd9a… == 307dbd9a…`.

**Prior passes' entries re-run in this pass**, because adding rows to a module can move the
node-id sets a prior proof recorded — an argument that they cannot is not a measurement.
`proofs.json` (pass 1), `proofs-pass2.json` and `proofs-pass3.json` re-run unchanged, all
three at tool exit **0**, reports written to
`docs/builder/temp-tests/slice-2-029/w2p4-rerun-*.md`: **5 / 6** (pass 1), **7 / 2 / 2 / 5 / 6**
(pass 2), **4 / 2 / 2** (pass 3) — digit-for-digit the recorded figures, and the node-id sets
`diff` **identical** for pass 2 and pass 3. Pass 1's own two entries differ from its original
record by the two `::test_the_sweep_reports_a_planted_violation_with_its_file_and_line` rows
pass 2 added and already re-recorded there; nothing in this pass moved them.

**No mutation is live.** `tests/test_ci_governance.py` hashes
`307dbd9a02f59e6939ebf4e6b15c09b4e395a56e891cc4b94bad07127296198a` — the shipped bytes of this
pass — and hashes the same after all four manifest runs. No `ACTIVE-MUTATION.json` or
`RESTORE-FAILED.json` exists under `/tmp`, `/private/tmp`, or the repo. Every mutation was
reverted before the next proof began, never at the end.

### Hot-path budget

**No new number owed.** This pass changes no schema construction and no production line; it
adds test rows to `tests/test_ci_governance.py` only. Pass 1's declared metric stands and has
now been reproduced three times: constructing lambda `misses=2, hits=0` aggregate over two
executions, singleton factory `misses=1, hits=1` — **misses 2 -> 1, hits 0 -> 1**.

### Floor verification

Re-run at the floor for this pass, scoped to the one file it edits, per the dispatch.

- Scratch venv, outside the repo: `/tmp/dsf-floor-029`.
- Resolved versions, read rather than restated: `/tmp/dsf-floor-029/bin/python -V` ->
  **Python 3.10.19**; `uv pip list --python /tmp/dsf-floor-029/bin/python` -> **django
  5.2.16**, **strawberry-graphql 0.316.0**, pytest 9.1.1. The floor `BUILD.md`
  `## Floor verification` names.
- Focused scope: `/tmp/dsf-floor-029/bin/python -m pytest tests/test_ci_governance.py --no-cov
  -q -p no:cacheprovider` — **86 passed**. Pass.
- **The shared `.venv` is unmutated**: `uv pip list` reads django **6.1** /
  strawberry-graphql **0.323.2**, `.venv/bin/python -V` reads **3.14.2**, and
  `git status --short -- pyproject.toml uv.lock` is empty. Every floor command carried an
  explicit `--python /tmp/dsf-floor-029/bin/python` or invoked that interpreter directly; `uv
  pip install` was not run at all in this pass.

### Implementation notes

- **A label, not a path, for the extras region.** `EXTRA_FILES_REGION =
  "outside-the-source-trees"` sits in the same tuple as real repo-relative paths and tree
  names. Making it hyphenated and un-path-like means a future reader (and a future `startswith`
  predicate) cannot mistake it for a location, and it reads cleanly as a pytest id.
- **Membership by `startswith(f"{tree}/")`, not by `Path.is_relative_to`.** The requirement
  tuple holds repo-relative *strings* that need not exist on disk — the narrowed control rows
  feed it `f"{tree}/anything.py"` deliberately. A filesystem-touching predicate would make the
  guard depend on the tree it is auditing, which is the coupling the whole finding is about.
- **Region rows parametrized rather than one row asserting a list is empty.** One row would be
  weakly pinned by construction (`BUILD.md` `### Acceptance rule`) — it is the same trap the
  repo-wide sweep row carries, recorded in pass 2. Per-region rows are what make narrowing A
  measure 3 instead of 1.
- **`SOURCE_TREES[0]` in `NARROWED_REQUIREMENTS`, not a tree name typed out.** The
  `every-region-but-one-tree` entry needs to name the one tree it withholds; taking it by index
  from the imported tuple keeps the entry correct if `check_citations` reorders or renames a
  tree, where a literal would quietly stop testing anything.
- **Nothing was deleted or rewritten.** `INCOHERENT_ORACLE_ANSWERS`'s `only-this-module` entry
  still hardcodes `"conftest.py"` and still fires under narrowing B. It is a legitimate control
  for its own purpose (a truncated oracle answer); the finding was that it was the *only* thing
  firing, not that it is wrong. Removing it would have cost a real row.

### Notes for Worker 3

- The three proof entries are in `docs/builder/temp-tests/slice-2-029/proofs-pass4.json`; the
  prior-pass re-runs are the same manifests as before, reports at `w2p4-rerun-*.md`. Every
  count above is `len()` of a listed node-id set at one scope, `tests/test_ci_governance.py`.
- **Narrowing B measures 4, where Worker 1's final verification derived 3.** Both readings are
  in the table above: 3 new rows plus the 1 pre-existing accidental row. If you re-run at the
  recorded scope you will see 4; that is agreement, not a discrepancy.
- The new rows never touch git, the filesystem, or the corpus — they are pure-function rows
  over tuples, so they are order-independent and hold on a machine without git, like the reach
  rows they sit beside.
- No production module, no migrated file, and no box state was touched this pass.

### Notes for Worker 1 (spec reconciliation)

- **Nothing new for the spec.** This pass adds test rows to `tests/test_ci_governance.py`
  only; no spec sentence is falsified or newly supported by it, and the four items already
  carried to Slice 3 (Amendment 2's two parallel sites, the `[test-ci-governance]` link def,
  the measured 25-in-8 -> 0 population, Amendment 3's granularity example) are untouched and
  still owed there.
- **One figure to correct if it is ever quoted downstream:** narrowing B fails **4** rows with
  the guard in place, not 3. The new boundary contributes 3 under each narrowing, exactly as
  final verification derived; the fourth row is the pre-existing `only-this-module` control.
- **No structural drift.** The designed fix landed in the shape final verification prescribed —
  derived from `SOURCE_TREES` and `EXTRA_SOURCE_FILES`, no fourth literal list, no count in an
  assertion — so this is not a structural-drift pause and the artifact returns `built`, not
  `revision-needed`.

---

## Review (Worker 3, pass 4)

### Failability re-run — mutations pre-registered BEFORE they are made

`worker-3.md` "Reading is necessary, not sufficient". Every mutation below is written here
before it is applied, applied one at a time, reverted inside this same pass, and the revert
proved by byte-comparison. Anchors are checked with `--check-anchors-only` before any pristine
copy is taken. Scratch roots are outside the repository. No `git checkout` / `git restore` /
`git stash` / `git worktree` at any point. The one source file any mutation touches is
`tests/test_ci_governance.py`, this slice's own file.

**Mandatory floor.** Worker 2's pass-4 record carries three entries at **5 / 3 / 4** rows. The
3-row entry (narrowing A) is at the floor and is mandatory. I re-run all three: the 4-row entry
is one above the floor and is the one whose total Worker 2 reports as disagreeing with final
verification's derivation, and the 5-row entry is the only one pinning the new boundary itself.

Re-runs of Worker 2's pass-4 records (manifest `docs/builder/temp-tests/slice-2-029/w3p4-rerun.json`,
scratch root `/private/tmp/dsf-w3p4-rerun`):

1. `tests/test_ci_governance.py::_unrepresented_corpus_regions` — `return unrepresented` replaced
   by `return []`. (Worker 2 entry 1; expected 5.)
2. `tests/test_ci_governance.py #"CORPUS_REACH_FILES = ("` — the eleven-entry tuple replaced by
   `("conftest.py",)`. (Worker 2 entry 2, narrowing A; expected 3.)
3. `tests/test_ci_governance.py #"CORPUS_REACH_FILES = ("` — the same tuple replaced by
   `("django_strawberry_framework/optimizer/extension.py",)`. (Worker 2 entry 3, narrowing B;
   expected 4 = 3 new + 1 pre-existing.)

**Probes this pass adds** (manifest `docs/builder/temp-tests/slice-2-029/w3p4-probes.json`,
scratch root `/private/tmp/dsf-w3p4-probes`). The dispatch asks two questions the re-runs cannot
answer: whether the 3-row entry is three genuinely independent rows, and whether `CORPUS_REGIONS`
is itself contradicted or is the fifth place this pattern reappears.

4. **One region withheld, all others kept.** `CORPUS_REACH_FILES` replaced by a four-entry tuple
   naming `conftest.py`, one `django_strawberry_framework/` file, one `tests/` file and one
   `scripts/` file — everything except `examples`. If the three rows under narrowing A are three
   independent region assertions, exactly one row fails here and it is `[examples]`.
5. **The region vocabulary narrowed.** `CORPUS_REGIONS = (CENSUS_MODULE, *SOURCE_TREES, EXTRA_FILES_REGION)`
   replaced by `CORPUS_REGIONS = (CENSUS_MODULE,)` — five of the six region rows then collect as
   zero rows. This is the question one level up from L1, asked of L1's own fix.
6. **The extras arm of the contradictor removed.** `_unrepresented_corpus_regions`'s
   `if not named.intersection(EXTRA_SOURCE_FILES):` replaced by `if False:`, so the
   outside-the-trees region can never be reported unreached.
7. **The census-module arm of the contradictor removed.** The same function's
   `unrepresented = [] if CENSUS_MODULE in named else [CENSUS_MODULE]` replaced by
   `unrepresented = []`, so a requirement that omits this module reads as reaching it.

**Scope as run, identical for all seven and identical to Worker 2's recorded scope:**
`uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_ci_governance.py`.

**One further probe, pre-registered after reading P2's result** (manifest
`docs/builder/temp-tests/slice-2-029/w3p4-probes2.json`, scratch root `/private/tmp/dsf-w3p4-probes2`).
P2 shows `CORPUS_REGIONS` loses rows silently when the tuple expression itself is replaced. The
question that decides whether that matters is whether the tuple is genuinely *derived* — i.e.
whether a change to `SOURCE_TREES` moves it — so:

8. **A fifth source tree added upstream.** `scripts/check_citations.py #"SOURCE_TREES = ("` gains a
   fifth entry (`"benchmarks"`). This is the same disclosed out-of-list transient borrow of
   `scripts/check_citations.py` that passes 2, 3 and 4 each made; the file is byte-identical to
   HEAD before I start (verified above by `git show HEAD:` into a scratch path outside the repo,
   then `cmp`, exit 0) and is byte-proved restored afterwards. If `CORPUS_REGIONS` is derived
   rather than decorative, a seventh region row appears and fails, because
   `ORACLE_REQUIRED_FILES` names nothing inside the new tree.

**A ninth probe, pre-registered after reading the shipped predicate.** The region guard asks
whether the requirement *names* a path under each tree, not whether that path exists — the
narrowed control rows feed it `f"{tree}/anything.py"` deliberately. So the adversarial question
is whether the new guard can be satisfied vacuously: a requirement of four tree-shaped paths
that name nothing real would reach every region. Manifest
`docs/builder/temp-tests/slice-2-029/w3p4-probes3.json`, scratch root `/private/tmp/dsf-w3p4-probes3`.

9. **A requirement that reaches every region and names nothing real.** `CORPUS_REACH_FILES`
   replaced by `("conftest.py", "django_strawberry_framework/nothing.py", "examples/nothing.py",
   "scripts/nothing.py")`. All six region rows are then satisfied. If nothing else catches it,
   the new guard is satisfiable without a real requirement.

#### Re-run results — node-id SETS, not totals

Instruments under `docs/builder/temp-tests/slice-2-029/`: `w3p4-rerun.json` / `.md`,
`w3p4-probes.json` / `.md`, `w3p4-probes2.json` / `.md`, `w3p4-probes3.json` / `.md`, and
`w3p4-rerun-proofs*.md` (the three prior manifests re-run). Scratch roots
`/private/tmp/dsf-w3p4-rerun`, `/private/tmp/dsf-w3p4-probes`, `/private/tmp/dsf-w3p4-probes2`,
`/private/tmp/dsf-w3p4-probes3`, `/private/tmp/dsf-w3p4-prior` — all outside the repo. Every
anchor verified to match **exactly once** with `--check-anchors-only` before any mutation was
applied. Pre-mutation state for every entry: green, `86 passed`, pytest exit 0, **0** pre-existing
failing rows. Collection/setup errors: **0 in every entry**.

| Entry | W2 rows | W3 rows | node-id set | restore |
|---|---|---|---|---|
| 1 — `_unrepresented_corpus_regions` -> `return []` | 5 | **5** | **identical** (all five `…names_the_region_it_lost[…]` ids) | `filecmp.cmp(shallow=False) True; sha256 307dbd9a02f59e69… == 307dbd9a02f59e69…` |
| 2 — narrowing A (`CORPUS_REACH_FILES` -> `("conftest.py",)`) | 3 | **3** | **identical** — `…reaches_every_corpus_region[django_strawberry_framework]`, `[examples]`, `[scripts]`; **all three new, zero pre-existing** | same, `307dbd9a…` |
| 3 — narrowing B (`CORPUS_REACH_FILES` -> the optimizer module) | 4 | **4** | **identical** — `…refuses_an_incoherent_oracle_answer[only-this-module]` (pre-existing) + `…reaches_every_corpus_region[examples]`, `[scripts]`, `[outside-the-source-trees]` (new) | same, `307dbd9a…` |

Tool exit **0** on the re-run manifest: no entry weakly pinned, none carrying a collection or
setup error. The shipped-file hash reproduces Worker 2's recorded `307dbd9a…` in all three
restores.

**The decomposition is confirmed, not the totals.** Worker 2 reported narrowing B at 4 where
final verification derived 3, and flagged it so a re-run reads as agreement. It is agreement, and
the parts are what say so:

- **Narrowing A contributes exactly 3, and 0 of them are pre-existing.** The three ids are region
  rows for `django_strawberry_framework`, `examples` and `scripts` — the three regions a
  requirement of `(CENSUS_MODULE, "conftest.py")` stops naming. `tests` and
  `tests/test_ci_governance.py` stay reached through `CENSUS_MODULE`; `outside-the-source-trees`
  stays reached through `conftest.py`.
- **Narrowing B contributes exactly 3 new rows, and the fourth is the accidental control firing.**
  The new three are `examples`, `scripts` and `outside-the-source-trees` — a different set from
  narrowing A's three, which is a stronger reading than a matching total would have been: the
  region rows respond to *which* region was lost, not to the fact that something was. The fourth,
  `test_the_corpus_census_refuses_an_incoherent_oracle_answer[only-this-module]`, is the
  pre-existing row that hardcodes `"conftest.py"` — the accidental protection L1 named, still
  present and still firing, exactly as Worker 2 records.

**Probes this pass added.** Scope identical to the above.

| Probe | Rows | Failing set | Reading |
|---|---|---|---|
| P1 — requirement narrowed to withhold **exactly one** region (`examples`), every other region still named | **1** | `…reaches_every_corpus_region[examples]` | the three rows under narrowing A are **three independent region assertions**, not one assertion parametrized three ways: withhold one region and exactly its row fires |
| P2 — `CORPUS_REGIONS` narrowed from six entries to `(CENSUS_MODULE,)` | **0** | (none) | `81 passed`, pytest exit 0. Five region rows collapse and nothing fails — the region vocabulary has no row-count contradictor of its own. Read against P5 and P9 below before grading it; see `### The escalated question` |
| P5 — a **fifth** source tree added upstream (`scripts/check_citations.py #"SOURCE_TREES = ("` gains `"benchmarks"`) | **1** | `…reaches_every_corpus_region[benchmarks]` | `1 failed, 86 passed` — **87 rows collected**. `CORPUS_REGIONS` is genuinely derived and fails **closed** when the corpus definition widens: a seventh region appears and fires immediately, because `ORACLE_REQUIRED_FILES` names nothing inside it |
| P3 — the contradictor's extras arm (`if not named.intersection(EXTRA_SOURCE_FILES):`) replaced by `if False:` | **2** | `…names_the_region_it_lost[only-this-module]`, `[every-tree-but-nothing-outside-them]` | the outside-the-trees arm is separately pinned |
| P4 — the contradictor's census-module arm replaced by `unrepresented = []` | **2** | `…names_the_region_it_lost[names-nothing]`, `[only-outside-the-trees]` | the this-module arm is separately pinned, by **different** rows from P3 — the five refusing rows discriminate rather than restate one another |
| P9 — a requirement that **reaches every region and names nothing real** (`conftest.py` + three `<tree>/nothing.py`) | **4** | `…covers_every_committable_python_file` + `…reaches_each_load_bearing_file[django_strawberry_framework/nothing.py]`, `[examples/nothing.py]`, `[scripts/nothing.py]` | the new guard **cannot be satisfied vacuously**. The region rows check that the requirement *names* a path per tree, not that it exists — and the census (git's answer) and the reach rows (the corpus) both refuse the fiction |

**Prior passes' manifests, re-run in full against the shipped bytes** (`w3p4-rerun-proofs.md`,
`w3p4-rerun-proofs-pass2.md`, `w3p4-rerun-proofs-pass3.md`; tool exit **0** on all three):
**5 / 6** (pass 1), **7 / 2 / 2 / 5 / 6** (pass 2), **4 / 2 / 2** (pass 3) — digit-for-digit
Worker 2's pass-4 figures, and the node-id sets `diff` **identical to Worker 2's own re-run
reports** for all three manifests. Against the *original* records: pass 2 and pass 3 identical;
pass 1 differs by exactly the two `…reports_a_planted_violation_with_its_file_and_line` rows pass
2 added, which is the difference Worker 2 disclosed. So pass 4's eleven new rows joined no prior
boundary's pin and retired none.

**Where the second pair of eyes landed.** Re-run: **all three** of Worker 2's pass-4 entries, plus
**all ten** entries of the three prior manifests, plus six probes of my own, every one at the
recorded scope and compared as node-id sets. Accepted on Worker 2's record: **nothing**.

**No mutation is live.** `tests/test_ci_governance.py` hashes
`307dbd9a02f59e6939ebf4e6b15c09b4e395a56e891cc4b94bad07127296198a` — Worker 2's recorded shipped
bytes — before and after every probe. `scripts/check_citations.py`, transiently borrowed by P5 and
by pass 2's entry 1, `cmp`s byte-identical against `git show HEAD:` into a scratch path outside the
repo, both before and after. No `ACTIVE-MUTATION.json` or `RESTORE-FAILED.json` exists under
`/tmp`, `/private/tmp`, any scratch root, or the repo; every scratch root holds only its
`pristine/` directory. `git status --porcelain` after my last probe is identical to its state
before this pass, line for line.

### The escalated question — is `CORPUS_REGIONS` the fifth place this reappears?

Asked because four findings in this one gate have shared one shape, each invisible until someone
looked one level up. Answered by measurement, not by argument.

**Is any element of `CORPUS_REGIONS` a new literal in disguise?** Traced one at a time:

| Element | Source | New data? |
|---|---|---|
| `CENSUS_MODULE` | `Path(__file__).resolve().relative_to(REPO_ROOT).as_posix()` | no — derived from `__file__`, shipped in pass 3 |
| `*SOURCE_TREES` | `from scripts.check_citations import SOURCE_TREES` (`tests/test_ci_governance.py:37`), read at `scripts/check_citations.py::SOURCE_TREES` | no — the same tuple `iter_python_sources()` walks, already contradicted by the census (pass-2 entry 1: 7 rows) |
| `EXTRA_FILES_REGION` | `"outside-the-source-trees"` | a **label**, not a path or a selector. It names the region; membership in it is decided by `named.intersection(EXTRA_SOURCE_FILES)`, and `EXTRA_SOURCE_FILES` is itself contradicted by the census (pass-2 entry 2: 2 rows) |

**No fourth hardcoded list was introduced.** The one new string is a region name that selects
nothing; every predicate in `::_unrepresented_corpus_regions` reads `CENSUS_MODULE`,
`SOURCE_TREES` and `EXTRA_SOURCE_FILES` directly. Worker 1's design constraint holds in the
shipped bytes.

**Is `CORPUS_REGIONS` itself contradicted? No — and it is measured at 0 rows (P2).** Narrowing it
to `(CENSUS_MODULE,)` deletes five rows and nothing fails. Stated plainly rather than rounded off,
because that is the same number L1 was filed on. Three measurements say it is nevertheless where
the class terminates:

1. **It cannot drift.** P5: adding a fifth tree upstream immediately produces a seventh region row
   that *fails*. The vocabulary tracks `SOURCE_TREES` live and fails closed when the corpus
   definition widens. `CORPUS_REACH_FILES` had no such property — it was a hand-written path list
   that could go stale silently.
2. **Narrowing it weakens nothing but its own rows.** This is the structural difference from L1
   and it is visible in P2's run: `ORACLE_REQUIRED_FILES`, the census, the oracle guard and the
   eleven reach rows are all untouched (`81 passed` = 86 minus the five collapsed rows, everything
   else green). Narrowing `CORPUS_REACH_FILES` cut the M2 guard's requirement from twelve files to
   two — it weakened a *different* boundary. That was the defect; this is not the same shape one
   level up, it is the point at which "you can always delete a test" takes over, and that point
   exists in every suite.
3. **It has no maintenance motive.** Every entry is derived or a label; nothing in it can be
   renamed, deleted or made wrong by a change elsewhere, so there is no legitimate edit that
   shortens it. `CORPUS_REACH_FILES` by contrast listed eleven real paths, any of which a rename
   would have made someone edit.

And P9 closes the remaining hole in the other direction: the new guard cannot be satisfied by
naming fictions — a requirement reaching all six regions with three non-existent paths fails 4
rows, because the census and the reach rows contradict the same tuple the region rows measure.
The three tuples now form a closed loop rather than a chain, which is what a terminating fix looks
like.

**Verdict: not a finding, and not deferred either — the question is answered.** I record the 0
rather than suppressing it, and the reason it is not L1 again is P2's own row list plus P5, not a
judgement about how likely someone is to make the edit.

### High:

None.

### Medium:

None.

### Low:

None.

### Verdicts on the prior passes' findings, by name

- **L1 (pass 3) — `CORPUS_REACH_FILES` / `ORACLE_REQUIRED_FILES` had no independent contradictor:
  CLOSED.** Re-derived, not accepted. The finding's own two narrowings move **0 -> 3** and
  **1 -> 4**; the new boundary contributes exactly **3** under each and the fourth row under B is
  the pre-existing accidental control, so the closure does not rest on the accident it named
  (narrowing A's three rows fire with `conftest.py` still present). The contradictor itself is
  pinned at **5** rows, its two arms separately at **2** and **2** on disjoint sets, and the
  requirement it defends cannot be satisfied vacuously (P9, 4 rows). Worker 1's design constraint
  — no fourth hardcoded literal list — holds in the shipped bytes: every expectation is derived
  from `SOURCE_TREES`, `EXTRA_SOURCE_FILES` or `__file__`, and no assertion carries a count.
- **M1 (pass 1) — the sweep's corpus is unpinned: CLOSED, against the shipped bytes.** Pass 2's
  entry 1 re-runs at **7** rows with an identical node-id set (`scripts/check_citations.py`
  transiently borrowed, byte-proved pristine before and after), and the corpus still re-derives at
  429 committable `.py` against a 429-file corpus — measured this pass with my own enumerator.
- **M2 (pass 2) — the census can be retired by its own oracle: CLOSED, against the shipped bytes.**
  Pass 3's entry 1 re-runs at **4** rows, identical set; the two oracle entries at **2** and **2**,
  identical sets. Pass 4 added rows to the same module and moved none of them.
- **L1 / L2 / L3 (pass 1) — CLOSED.** L1 (the recorded restore hash) is discharged by every
  pass-4 restore reproducing the shipped `307dbd9a…`. L2 (the docstring enumerated only one arm's
  over-match) — I read
  `tests/test_ci_governance.py::test_no_active_source_uses_a_forbidden_optimizer_extensions_form`
  end to end this pass: **both** arms' false-positive directions are stated, the bare-class
  any-sequence-literal case and the lambda substring/dotted/affixed case. L3 (three tracked `.py`
  outside the trees) — `EXTRA_SOURCE_FILES` still carries all three and pass-2 entry 2 still fails
  **2** rows when it is emptied.

### DRY findings

**None new.** Checked with evidence rather than asserted, and the existence challenge is weighed
rather than skipped.

- **Has the gate accreted one guard per finding across four passes?** No — and every group has a
  mutation that kills **only** it, which is the measurement that answers it: classifier arms 5 and
  6 (disjoint), the reporter 2, the corpus spine 7, the outside-the-trees half 2, the oracle guard
  4, the oracle itself 2, and now the region contradictor 5 with its two arms at 2 and 2 on
  disjoint sets. Nothing is dead machinery and nothing is one assertion written twice.
- **Are the two new tests one test written twice?** No, and the boundary entry proves it rather
  than arguing it: gutting `_unrepresented_corpus_regions` fails all five
  `…names_the_region_it_lost` rows and **zero** of the six `…reaches_every_corpus_region` rows.
  The six pin the *requirement's width* against the live tuple; the five pin the *contradictor's
  correctness* against tuples the live tree can never hold. Neither detects the other's failure.
- **Existence challenge — the candidate I weighed is `CORPUS_REGIONS` itself.** It is read by
  exactly one call site (the `@pytest.mark.parametrize` on the region test);
  `_unrepresented_corpus_regions` does not read it. Inlining the expression into the decorator
  would delete the name and change nothing measurable. Not raised as a finding: the constant is
  one derived line, its name is what makes the region test's ids readable, and deleting it buys no
  simplification worth a fourth loop. Recorded so the question is visibly asked rather than
  visibly skipped. The candidate a prior pass raised — `::test_the_git_oracle_enumerates_this_module`,
  logically entailed by the census guard — was examined and kept with reasoning in pass 3; nothing
  this pass measured disturbs that, and I am not re-fighting it.
- **Repeated literals** (`scripts/review_inspect.py`, run this pass): `conftest.py` 4x (unchanged
  from pass 3), `permissions` / `contents` 2x (pre-existing YAML keys), `constructing lambda` and
  `bare class in a sequence` 2x, `planted_schema.py` 2x, and three new to this pass —
  `only-this-module` 2x, `expected` 2x, `/anything.py` 2x. Read individually: `expected` is a
  `parametrize` argname in two unrelated decorators; `/anything.py` is the deliberately-fake path
  suffix in two generator expressions of one constant, where a named constant would add a name to
  save twelve characters; `only-this-module` is a pytest id shared by one
  `INCOHERENT_ORACLE_ANSWERS` row (a git *answer* of only this module) and one
  `NARROWED_REQUIREMENTS` row (a *requirement* of only this module). The two are semantically the
  same narrowing of two different objects, and pytest node ids always carry the test name, so both
  are unambiguous in a failure list — narrowing B's own report above shows the two side by side and
  reads cleanly. Correctly left duplicated; no finding.
- **The plan's decided answers were not disturbed:** no shared `optimizer_factory()` helper, no
  module-level singleton, no second enforcement mechanism. `scripts/`, `.pre-commit-config.yaml`
  and `.github/` are clean in `git status --porcelain`.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` is **empty**; `__all__` and the re-export
list are unchanged. `git status --porcelain -- django_strawberry_framework/` is empty — this pass,
like the three before it, changes no package source. Every symbol pass 4 adds
(`EXTRA_FILES_REGION`, `CORPUS_REGIONS`, `_unrepresented_corpus_regions`, `NARROWED_REQUIREMENTS`)
is module-private or module-local to `tests/test_ci_governance.py`.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity (only when the slice touches docs, release metadata, KANBAN, or archived specs)

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. Worker 2's
`build_tree_md.py --check` claim is confirmed independently and without touching the generated
doc: `docs/TREE.md` is copied to a scratch path **outside** the repo and rendered there
(`--md <scratch>`), and the diff is exactly the two pre-existing
`tests/mutations/test_operations.py` rows belonging to the concurrent session. `docs/TREE.md` is
clean in `git status --porcelain` and hashes `bb1268a7…` unchanged; the module docstring's first
line is untouched, so the two rendered rows for this module still match.

### Scoping claim — the apply pass touched one file

Confirmed independently and first, because three prior reviews and a final verification would all
be stale if it were false:

- The eight migrated files' diff against HEAD is **91 changed lines**, per-file `--numstat`
  `7/4, 4/2, 2/1, 4/2, 2/1, 14/7, 28/10, 2/1` — the same totals every prior pass measured, digit
  for digit. The path list is passed explicitly, never through a shell variable (`zsh` does not
  word-split an unquoted one, and a pipe that never ran prints a clean zero); the positive control
  through the same invocation returns `590/8` for `tests/test_ci_governance.py`, so the instrument
  ran.
- **Re-derived the contract itself rather than the diff:** my own AST classifier over the four
  `SOURCE_TREES` plus the three `EXTRA_SOURCE_FILES` finds **0** forbidden entries in a 429-file
  corpus, with a synthetic positive control returning one `bare` and one `lambda`. The repair
  still holds at every site.
- `tests/test_ci_governance.py` hashes Worker 2's recorded `307dbd9a…`; `scripts/check_citations.py`
  is byte-identical to HEAD; `django_strawberry_framework/`, `docs/TREE.md`, `pyproject.toml`,
  `uv.lock`, `.pre-commit-config.yaml`, `.github/` and `scripts/` are all clean.
- mtimes corroborate: all eight migrated files last written between 01:33 and 01:52 (pass 1),
  `tests/test_ci_governance.py` at 03:20:54 (pass 4).
- **No box state changed:** 17 `- [x]`, 0 `- [ ]`, unchanged from final verification's audit.
- The only tracked files dirty beyond Worker 2's recorded out-of-scope list are
  `docs/SPECS/spec-029-…md` and `docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md`,
  both Slice 1's, plus `docs/review/**` and `tests/mutations/test_operations.py`, the concurrent
  session's. Recorded, not touched, not judged.
- **Test staleness, swept independently** rather than against the slice's file list: this pass
  changes no example-model field set and no wire shape (`git status --porcelain` over
  `examples/fakeshop/apps/*/models.py` and `django_strawberry_framework/**` is empty), so neither
  staleness shape `BUILD.md` `### Test staleness a focused run cannot see` names is in play. No
  tree is stranded.

### What looks solid

- **L1's fix guards the class rather than the third spelling, and the constraint that makes that
  true holds in the bytes.** Every expectation is derived — `__file__`, the imported
  `SOURCE_TREES`, `EXTRA_SOURCE_FILES` — and the one new string is a region label that selects
  nothing. No fourth list, no count in any assertion.
- **The regress terminates, and P5 and P9 are why, not the prose.** P5: the vocabulary tracks
  `SOURCE_TREES` live and fails closed when the corpus widens. P9: the requirement cannot be
  satisfied by naming fictions, because the census and the reach rows contradict the same tuple.
- **The three region rows discriminate.** P1 withholds exactly one region and exactly its row
  fires; narrowing A and narrowing B produce *different* three-row sets.
- **The five refusing rows discriminate.** P3 and P4 kill the contradictor's two arms separately,
  on disjoint pairs.
- **Worker 2 reported a discrepancy instead of rounding it.** Narrowing B is 4, not 3, and the
  decomposition it published is exactly what I measured. A pass that had quietly written 3 would
  have read identically to this one and been wrong.
- **Prior boundaries are exactly where they were measured.** All ten entries of the three prior
  manifests reproduce at 5/6, 7/2/2/5/6 and 4/2/2 with node-id sets identical to Worker 2's
  re-runs, and identical to the original records except the two rows pass 1 pre-dates.
- **Gates green, read-only:** `ruff format --check .` (`429 files already formatted`),
  `ruff check .` (`All checks passed!`), `check_trailing_commas.py --check` (exit 0),
  `check_citations.py` (`OK: 789 citations resolve (712 in 426 .py files, 77 in KANBAN.md)`),
  `git diff --check` (exit 0).
- **Counts re-derived:** module **86 passed** (75 -> 86, +11 as recorded); slice scope **582
  passed**; corpus 429 = 426 + 3.
- **Floor reproduces as recorded, `.venv` unmutated.**
  `/tmp/dsf-floor-029/bin/python -m pytest tests/test_ci_governance.py --no-cov -q
  -p no:cacheprovider` -> **86 passed** at Python **3.10.19** / django **5.2.16** /
  strawberry-graphql **0.316.0**, re-read with `uv pip list --python …` rather than restated. The
  shared `.venv` reads django **6.1** / strawberry-graphql **0.323.2** at Python **3.14.2** — head,
  not floor — and `pyproject.toml` / `uv.lock` are clean.
- **No new hot-path number is owed.** The pass changes no schema construction and no production
  line; pass 1's declared metric (`misses 2 -> 1`, `hits 0 -> 1`) stands and has now been
  reproduced in three prior passes.

### Spec slice checklist audit

**No box changed state; all 17 remain ticked and true.** Pass 4 lands under boxes 9 and 14 as
prior passes did — box 9 asserts a positive property about what the module carries (still true,
and this pass only adds to it), and box 14 is a claim about the artifact's failability record,
which pass 4 satisfies with three entries carrying every field `BUILD.md` `### What gets recorded`
requires at 5 / 3 / 4 rows, 0 collection/setup errors, and byte-proved restores. Box 11's wording
recommendation remains Worker 1's to enact or carry; nothing this pass added moved it.

### Static helper use

`uv run python scripts/review_inspect.py tests/test_ci_governance.py --output-dir docs/shadow` —
**run** this pass, not inherited. The trigger fires (pass 4 adds ~105 lines to a `.py` outside
`django_strawberry_framework/`, over the 50-line threshold). Output: **4 control-flow hotspots**,
all pre-existing or docstring-only growth — `_forbidden_optimizer_entries` 36 lines / 8 branch
nodes and `test_checkout_steps_do_not_persist_credentials` 19 / 8 are unchanged, and the two
44/45-line rows carry **0** branch nodes; `_unrepresented_corpus_regions` does **not** appear as a
hotspot. **No Django/ORM markers.** 7 imports, the single cross-folder import
(`from scripts.check_citations import SOURCE_TREES, iter_python_sources`) widened by one name and
still under its ten-line coupling comment. Nine repeated literals, discussed under `### DRY
findings`. Nothing that changes a finding. **Skips:** none owed — this pass touched exactly one
file.

### Temp test verification

- `docs/builder/temp-tests/slice-2-029/w3p4-rerun.json` / `.md` — independent re-runs of all three
  of Worker 2's pass-4 entries at the recorded scope. Die with the cycle.
- `w3p4-probes.json` / `.md`, `w3p4-probes2.json` / `.md`, `w3p4-probes3.json` / `.md` — six
  narrowings and widenings no pass had tried (P1-P5, P9). **None caught a bug**, so none is
  promoted; their value is the discrimination evidence and the answer to the escalated question.
- `w3p4-rerun-proofs.md`, `w3p4-rerun-proofs-pass2.md`, `w3p4-rerun-proofs-pass3.md` — the three
  prior manifests re-run against the shipped bytes. Not promoted.
- Earlier passes' artifacts in that directory are theirs; none is promoted, and
  `test_hot_path_budget.py` is correctly still unpromoted.

### Notes for Worker 1 (spec reconciliation)

- **`CORPUS_REGIONS` measures 0 failing rows under its own narrowing (probe P2), and I am not
  filing it.** Recorded here in full so the decision is yours to overturn rather than mine to
  bury. The three measurements that distinguish it from L1 are in `### The escalated question`:
  it cannot drift (P5 — a fifth upstream tree produces a seventh region row that fails), narrowing
  it weakens no other boundary (P2's run leaves `ORACLE_REQUIRED_FILES`, the census, the oracle
  guard and the eleven reach rows all green, where narrowing `CORPUS_REACH_FILES` cut the M2
  guard's requirement from twelve files to two), and it has no maintenance motive because every
  entry is derived or a label. If you read those as insufficient, the fix is not another guard —
  it is inlining the tuple into the `parametrize` decorator so there is no constant to narrow.
- **The Amendment 2 parallel-site escalation remains Slice 3's** and was not acted on, per the
  dispatch. Pass 1's Amendments 1-3 stand exactly as the three prior reviews judged them, and the
  four items already carried to Slice 3 (Amendment 2's two parallel sites, the
  `[test-ci-governance]` link def, the measured 25-in-8 -> 0 population, Amendment 3's granularity
  example) are untouched and still owed there.
- **The artifact carried two `Status:` lines** — the header and a trailing restatement at the end
  of pass 4's build report, both reading `built`. `worker-0.md`'s status hygiene rule treats two
  values as unreadable, so I normalized the artifact to exactly one, the header, as part of
  setting this verdict. Pass 4's report text is otherwise unaltered.
- **`docs/SPECS/spec-029-…md` and `docs/SPECS/appx/spec-004-optimizer_beyond-0_0_3-rationale.md`
  are dirty** from Slice 1's work, correctly, and out of Slice 2's scope in both directions.
  Flagged only so the final gate's file inventory does not read them as Slice 2 churn.
- **No spec text was read as false by this pass, and I requested no spec edit.**

### Review outcome

`review-accepted`.

**L1: closed** — verdict given by name above, re-derived rather than accepted. Its two narrowings
move 0 -> 3 and 1 -> 4, the new boundary contributes exactly 3 under each, and the fourth row
under B is the pre-existing accidental control, so the closure does not rest on the accident the
finding named. The contradictor is pinned at 5 rows with its two arms separately at 2 and 2 on
disjoint sets, the three region rows discriminate (P1), and the requirement cannot be satisfied
vacuously (P9). Worker 1's design constraint — no fourth hardcoded literal list — holds in the
shipped bytes: every element of `CORPUS_REGIONS` traces to `__file__`, to the imported
`SOURCE_TREES`, or to a region label that selects nothing.

**M1, M2 and pass 1's L1 / L2 / L3 all remain closed against the shipped bytes**, proved by
re-running all ten entries of the three prior manifests at 5/6, 7/2/2/5/6 and 4/2/2 with node-id
sets identical to Worker 2's re-runs — so pass 4's eleven new rows joined no prior pin and retired
none.

**No High, no Medium, no Low.** The escalated question the dispatch put — whether `CORPUS_REGIONS`
is itself contradicted or is the fifth place this pattern reappears — is answered with a
measurement rather than an argument, its 0-row result reported rather than rounded, and recorded
under `### Notes for Worker 1` for the maintainer to overturn if they read it differently.

The scoping claim is confirmed independently: 91 changed lines across the eight migrated files
with per-file totals matching every prior pass, `scripts/check_citations.py` byte-identical to
HEAD, no box state changed, and 0 forbidden entries in a 429-file corpus under my own classifier.
No mutation is live. The floor run reproduces at 86 passed on Python 3.10.19 / Django 5.2.16 /
strawberry-graphql 0.316.0 with the shared `.venv` unmutated at head; the module is 86 passed and
the slice scope 582 passed; every read-only gate is green.

Status set to `review-accepted`; routes to **Worker 1** for final verification.

---

## Final verification (Worker 1, pass 2)

Second final-verification pass. My first one set `revision-needed` on L1 and refused a deferral;
Worker 2's pass 4 closed it and Worker 3's third re-review accepted with no High, Medium or Low,
escalating one question to me. Everything below is re-derived in **this** pass with my own
instruments. Nothing is carried on the chain's word — not Worker 3's three termination
measurements, not its clean bill of health on the seventeen boxes, and not my own prior section's
figures.

### Spec status-line re-verification

`docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md:1-9` re-read. Lines 1-7 describe a shipped card
and a version boundary this slice does not touch; line 9's rationale-companion pointer resolves.
Nothing pass 4 landed falsifies a status line. **No spec edit is made in this pass**, and DoD item
4's reconciliation against what shipped is Slice 3's, per the plan's ownership table.

### Contract delivered

- **The forbidden-form regression is repaired at every site.** Re-derived with an AST classifier
  written in this pass and control-checked before its reading was believed (constructing lambda
  with kwargs -> flag; bare class in a sequence -> flag; `lambda: ext` -> no; a `check_schema`
  classmethod call -> no). Run over the same corpus definition the shipped gate uses — the four
  `SOURCE_TREES` plus the three `EXTRA_SOURCE_FILES` — once against `git show HEAD:<path>` and
  once against the working tree. **HEAD: 25 entries in 8 files (18 constructing lambdas + 7
  bare-class-in-a-sequence)**, distributed `test_relay_connection.py` 10,
  `optimizer/test_extension.py` 7, `test_products_visibility_api.py` 2,
  `mutations/test_resolvers.py` 2, and one each in `strategy_schemas.py`, `forms/test_resolvers.py`,
  `mutations/test_write_transaction.py`, `types/test_resolvers.py`. **Working tree: 0.** Five
  instruments now agree digit for digit.
  Corpus size reads **428** here against the gate's **429** because my enumerator is
  `git ls-files` (tracked only) where `_committable_python_files` is
  `git ls-files --cached --others --exclude-standard`; the one file between them is the concurrent
  session's untracked `tests/mutations/test_operations.py`. Different populations, not a
  discrepancy.
- **Maintainer decision D1's standing pin shipped.**
  `tests/test_ci_governance.py::test_no_active_source_uses_a_forbidden_optimizer_extensions_form`
  plus the classifier, the 9+9 controls, the corpus census, the eleven reach rows, the reporter
  seam, the oracle guard, and pass 4's region contradictor. `git status --short` shows `scripts/`,
  `.github/` and `.pre-commit-config.yaml` absent from the diff — D1's placement decision holds.

### The escalated question — `CORPUS_REGIONS`: **ACCEPTED as terminal**

Worker 3 measured that narrowing `CORPUS_REGIONS` fails 0 rows, reported it rather than rounding
it, and argued the class nevertheless terminates. I own the decision. I ran five probes of my own
through `scripts/prove_failability.py` (manifests
`docs/builder/temp-tests/slice-2-029/w1fv2-probes.json` and `w1fv2-probes2.json`; scratch roots
`/private/tmp/dsf-w1fv2-probes` and `…-probes2`, both **outside** the repo; every anchor verified
to match exactly once with `--check-anchors-only` before any copy was taken; pre-mutation baseline
`86 passed`, pytest exit 0, 0 pre-existing failing rows on every entry; collection/setup errors 0
on every entry; tool exit **0**; every restore proved by `filecmp.cmp(shallow=False) True` plus
SHA-256).

| Probe | Mutation | Rows | Failing set |
|---|---|---|---|
| **W1-A** (re-derives Worker 3's P5) | `scripts/check_citations.py` `SOURCE_TREES` gains a fifth entry `"benchmarks"` | **1** | `::test_the_oracle_requirement_reaches_every_corpus_region[benchmarks]` — `87` rows collected, `1 failed, 86 passed` |
| **W1-B** — *the direction no pass measured* | `SOURCE_TREES` **loses** `"examples"` | **3** | `::test_the_sweep_corpus_covers_every_committable_python_file`, `::test_the_sweep_corpus_reaches_each_load_bearing_file[examples/fakeshop/strategy_schemas.py]`, `[examples/fakeshop/test_query/test_products_visibility_api.py]` |
| **W1-C** (re-derives P2) | `CORPUS_REGIONS` -> `(CENSUS_MODULE,)` | **0** | none; `81 passed`, exit 0 |
| **W1-D** — *a probe no pass ran* | `EXTRA_FILES_REGION` replaced by `"a-region-that-selects-nothing"`, keeping the tuple's arity | **0** | none; **`86 passed`** — the collected row count is unchanged |
| **W1-E** (re-derives P9) | `CORPUS_REACH_FILES` -> `conftest.py` + three `<tree>/nothing.py` | **4** | `::test_the_sweep_corpus_covers_every_committable_python_file` + `::…reaches_each_load_bearing_file[django_strawberry_framework/nothing.py]`, `[examples/nothing.py]`, `[scripts/nothing.py]` |

**Argument 1 re-derived, and what it actually proves.** W1-A reproduces P5 exactly: the region
vocabulary is a live expression over the imported `SOURCE_TREES`, a fifth tree upstream
immediately produces a seventh region row, and that row fails because `ORACLE_REQUIRED_FILES`
names nothing inside it. W1-B closes the direction Worker 3 did not measure — a tree **removed**
upstream also fails, at 3 rows, and **none of them is a region row**: the census and two reach
rows catch it while the `[examples]` region row simply vanishes. So the claim "a divergence
between the constant and its upstream cannot persist" holds in both directions, but by different
mechanisms, and the prose implies only one of them. Verified in the bytes as well: `CORPUS_REGIONS
= (CENSUS_MODULE, *SOURCE_TREES, EXTRA_FILES_REGION)` at `tests/test_ci_governance.py:469`, where
`CENSUS_MODULE` derives from `__file__`, `SOURCE_TREES` is the imported tuple at `:37`, and
`EXTRA_FILES_REGION` is a label that selects nothing — membership in that region is decided by
`named.intersection(EXTRA_SOURCE_FILES)` inside the guard.

**So argument 1 IS different in kind from the L1 accident — and it is not what decides this.**
L1's residual protection was a coincidence: an unrelated control row hardcoding the literal
`"conftest.py"`. Derivation is not a coincidence. But derivation rules out exactly one failure
mode — **staleness**. A hand-written list can silently become wrong (a rename makes an entry
bogus; someone "fixes" it by deleting the entry, and the loss is invisible), and
`CORPUS_REACH_FILES` had precisely that exposure. `CORPUS_REGIONS` has no maintenance edit that
shortens it. Naming which of the two things argument 1 proves is what keeps it from being the same
reasoning in better clothes: it does **not** prove the narrowing is pinned. Nothing does. W1-C and
W1-D both measure 0.

**What decides it is argument 2, stated mechanically rather than by degree.**

`CORPUS_REGIONS` has **exactly one reader**, established by grep over `tests/`, `scripts/`,
`django_strawberry_framework/`, `examples/` and `conftest.py`: `tests/test_ci_governance.py:469`
(the definition) and `:675` (`@pytest.mark.parametrize("region", CORPUS_REGIONS, ids=CORPUS_REGIONS)`).
That reader is a **row-generating position, not an assertion's data**. The guard,
`::_unrepresented_corpus_regions`, reads `CENSUS_MODULE`, `SOURCE_TREES` and `EXTRA_SOURCE_FILES`
directly and never reads `CORPUS_REGIONS` at all. Narrowing it can therefore only **delete rows**;
it cannot leave a surviving assertion running, green, and enforcing less.

That is exactly what `CORPUS_REACH_FILES` did, and it is why L1 was refused. It was a parametrize
list **and** the data of `ORACLE_REQUIRED_FILES = (CENSUS_MODULE, *CORPUS_REACH_FILES)`, which
`::_unreported_required_files` — the M2 oracle guard — consumes. Halving it left that guard alive
and enforcing two files instead of twelve. **A surviving assertion silently enforcing less is the
defect; a deleted row is not.**

W1-D sharpens this rather than weakening it. The vacuous row it plants does survive and does
assert nothing — but it asserts nothing about a region that does not exist, and the real check it
displaced (`[outside-the-trees]`) was deleted, not degraded. Its value is that it shows the
narrowing is invisible to a row-count check too (`86 passed`, arity preserved), which is a stronger
adversarial reading than P2's and still lands in the same taxonomy.

**And no fix exists here that is not subject to the identical edit.** Worker 3's own alternative —
inline the tuple into the decorator — moves the bytes and changes nothing; the narrowing target
becomes the inline expression. At L1 a terminating fix existed and was cheap (derive the
expectation from a definition already independently contradicted), which is why refusing the
deferral there was right and why refusing it a second time here would not be. The object being
narrowed here is the row set itself. That is the floor every test suite has, and it is a property
of the object, not a forecast about who would make the edit.

**The licence this acceptance does not grant.** Stated as a rule so a future reader cannot
generalize from it, and mechanically checkable in three greps:

> An unpinned constant in this gate is acceptable **only** when all three hold: (a) grep shows
> exactly one reader; (b) that reader is a `parametrize` / row-generating position; (c) **no
> surviving assertion reads the constant as data**. If any of the three fails — as all three
> failed for `CORPUS_REACH_FILES`, which also fed `ORACLE_REQUIRED_FILES` — the constant must be
> given an independent contradictor, and a deferral is not the cheaper option.

**Verdict: accepted, no fix required, and the acceptance is recorded rather than silent.** It is
routed below to `bld-final-029.md`'s `### Deferred work catalog` as a maintainer-facing item, so
the maintainer can overturn it without reading this artifact. No `revision-needed`, and this is
not a `BUILD.md` `### Acceptance rule` recorded exception: that rule governs a **boundary** whose
removal fails 0 or 1 rows, and every boundary this slice introduced is pinned above 1 (classifier
arms 4 and 5, reporter 2, corpus spine 7, extras half 2, oracle guard 4, oracle itself 2, region
contradictor 5 with arms at 2 and 2, region rows 3 under either narrowing). `CORPUS_REGIONS` is
not a boundary; it is the row set of one.

### Spec slice checklist audit — all 17 boxes

Audited against the diff in this pass, not against the three prior audits. **No box is un-ticked
and no box needed ticking; all 17 are `- [x]` and true.** Pass 4 changed no box state, which I
confirmed by count (`17` `- [x]`, `0` `- [ ]`). What I re-proved here:

| Box | Proof run in this pass |
|---|---|
| 1 population re-derived | my own controlled AST classifier over HEAD and the working tree: 25 in 8 files -> 0 |
| 2 seven bare-class migrated | classifier by kind at HEAD: `bare class in sequence` **7**; 0 now |
| 3 eighteen lambdas migrated, kwargs variants included | classifier by kind at HEAD: `constructing lambda` **18**; 0 now |
| 4 function-local everywhere | AST walk over all 8 files for a `DjangoOptimizerExtension(...)` call in a module-scope statement: **none** |
| 5 five conditional sites construct nothing on `else` | read all five: `test_relay_connection.py:1030-1033`, `:1113-1116`, `:1504-1507`, `:1706-1709` (each `extensions = []` then `if optimizer:`) and `strategy_schemas.py`'s `if strategy is not None:` |
| 6 the two-strictness pair carries two locals | `tests/optimizer/test_extension.py:5602` `raising_optimizer` / `:5611` `silent_optimizer`, each behind its own `lambda:` |
| 7 `build_strategy_schema` docstring corrected, module docstring unchanged | function docstring reads "mounted on ONE `DjangoOptimizerExtension` per built schema"; module docstring compared by `ast.get_docstring` against `git show HEAD:` — **identical** |
| 8 no assertion weakened | `git diff -U0` over the 8 migrated files, added/removed lines only, grepped for `assert` / `@pytest` / `pytest.mark` / `skip` / `xfail` — **no match**. `--numstat` per file `7/4, 4/2, 2/1, 4/2, 2/1, 14/7, 28/10, 2/1` = 63 added / 28 removed = **91 changed lines**, the figure every prior pass measured |
| 9 classifier + repo-wide sweep present | read `::_forbidden_optimizer_entries` and the sweep test end to end |
| 10 9+9 controls present and green | AST-counted: `MUST_FLAG_SNIPPETS` **9**, `MUST_NOT_FLAG_SNIPPETS` **9**; both parametrized; green in the 86-row run |
| 11 corpus scoped through `check_citations`, coupling in a comment | `from scripts.check_citations import SOURCE_TREES, iter_python_sources` at `:37` under a ten-line coupling comment; `_sweep_corpus()` unions it with `EXTRA_SOURCE_FILES`. Text deliberately unedited — see below |
| 12 module docstring widened, coverage note accurate | read: it names both corpora, and the coverage note reads "YAML under `.github/` and the text of first-party `.py` files" — true of the shipped assertions. First line unchanged, so `docs/TREE.md`'s two rendered rows still match |
| 13 deliberate non-extensions + false-positive direction recorded | the sweep docstring carries the three non-extensions (deprecated instance form, subclass entry, named constructing function) and **both** arms' false-positive directions |
| 14 failability record | present in all four build reports, each entry carrying the mutation, scope as run, pre-mutation state, listed node ids, collection/setup errors separately at 0, and a byte-compared revert. No zero-row entry, so no `why 0` is owed. The end-to-end control (`tests/forms/test_resolvers.py` reverted to the bare class -> the sweep row fails, naming file, line, form, snippet and fix) is recorded as a control, not as the boundary proof |
| 15 hot-path both readings | re-run here, reproduces exactly (below) |
| 16 floor verification recorded, `.venv` unmutated | re-run and re-read here (below) |
| 17 ruff scoped, `git status --short` slice-intended | `git status --short` shows exactly the nine slice files plus the recorded out-of-scope set; `docs/TREE.md`, `scripts/`, `.github/`, `pyproject.toml`, `uv.lock` and `django_strawberry_framework/` all clean |

**Box 11 stays ticked and its text stays unedited**, for the third time and the same reason:
`iter_python_sources()` is still the corpus's spine and the coupling is still named in a comment,
so the tick is not an over-tick, and rewriting a box whose contract landed would falsify three
prior audits of it. Worker 2's pass-2 recommendation to mention the three `EXTRA_SOURCE_FILES`
modules is carried below, not enacted.

### Obligations the plan declared

- **Hot-path number — exists and reproduces exactly as recorded.** `uv run pytest
  docs/builder/temp-tests/slice-2-029/test_hot_path_budget.py --no-cov -q -n0 -s` re-run here:
  identity reading `False` (bare class) / `False` (constructing lambda) / `True` (singleton
  factory); cache reading over two `execute_sync` of one query on one schema — constructing lambda
  builds **2** instances, each `CacheInfo(hits=0, misses=1, size=1)`, aggregate `misses=2, hits=0`;
  singleton factory builds **1**, `CacheInfo(hits=1, misses=1, size=1)`, aggregate `misses=1,
  hits=1`. **misses 2 -> 1, hits 0 -> 1**, the plan's declared metric. Whether the trade is
  acceptable is the maintainer's call; the obligation is that the number exists next to the change
  and reaches them.
- **Floor verification — ran, recorded, and re-executed here.** `/tmp/dsf-floor-029/bin/python -V`
  reads **Python 3.10.19**; `uv pip list --python /tmp/dsf-floor-029/bin/python` reads **django
  5.2.16**, **strawberry-graphql 0.316.0**, pytest 9.1.1 — the floor `BUILD.md`
  `## Floor verification` names, read rather than restated. `/tmp/dsf-floor-029/bin/python -m
  pytest tests/test_ci_governance.py --no-cov -q -p no:cacheprovider` -> **86 passed**. The plan
  assigned the run to Worker 2's build pass and it happened there; this gate is the backstop.
- **The shared `.venv` is unmutated.** `uv pip list` reads django **6.1** / strawberry-graphql
  **0.323.2**, `.venv/bin/python -V` reads **3.14.2** — head, not floor — and
  `git status --short -- pyproject.toml uv.lock` is empty. My own five probes ran `uv pip install`
  not once.

### Failability and fail-open checks (Worker 1's two confirmations)

- **The record exists for every new boundary, across four passes.** Pass 1: the classifier's two
  arms mutated separately (4 and 5 rows) plus the end-to-end control (1 row, correctly recorded as
  a control). Pass 2: corpus spine 7, `_sweep_corpus`'s outside-the-trees half 2, reporter seam 2,
  both classifier arms re-proved against the shipped bytes 5 and 6. Pass 3: `_unreported_required_files`
  4, plus the finding's own two mutations as controls at 2 and 2. Pass 4:
  `_unrepresented_corpus_regions` 5, narrowing A 3, narrowing B 4. Every entry carries all six
  fields `BUILD.md` `### What gets recorded` requires. No zero-row entry anywhere. The one refused
  mutation — a `SyntaxError` that collection-errored and was reported as `INVALID COUNT` rather
  than banked as a measured zero — is disclosed in pass 1, which is the right kind of record.
- **No mutation is live.** `tests/test_ci_governance.py` hashes
  `307dbd9a02f59e6939ebf4e6b15c09b4e395a56e891cc4b94bad07127296198a` — the shipped bytes Worker 2
  and Worker 3 both recorded — before and after all five of my probes.
  `scripts/check_citations.py` hashes `699e24912655f011c215391b2b65170f8e37f5596fa460c2ce9b6acbfdeff0c9`
  and is **byte-identical to `git show HEAD:`**, read into a scratch path outside the repo, both
  before and after the two probes that transiently borrowed it. No `ACTIVE-MUTATION.json` or
  `RESTORE-FAILED.json` exists under `/tmp`, `/private/tmp`, any scratch root, or the repo. Four
  build passes, four reviews and two final verifications have run failability proofs in this tree
  and all of them left it clean.
- **No fail-open shape landed.** Re-read the shipped gate for the catalogued shapes rather than
  trusting a green run. `_committable_python_files` uses `check=False` with an explicit
  `returncode` assert and raises on a missing `git` — fail-closed both ways; its empty-but-exit-0
  answer is refused by `_unreported_required_files`. `_forbidden_optimizer_entries` calls
  `ast.parse` with **no** `try` / `except SyntaxError`, so an unparseable file errors its row
  rather than being silently skipped — the obvious fail-open in a source sweep, and it is absent.
  `_sweep_corpus`'s `if path.is_file()` filter drops a vanished `EXTRA_SOURCE_FILES` entry, but
  git's `--cached` still lists a tracked-and-deleted path, so the census fails rather than
  narrowing. `_unrepresented_corpus_regions` returns a list of names, never a boolean, and both
  call sites assert on membership rather than truthiness. The one remaining unpinned datum is
  `CORPUS_REGIONS`, ruled on above.

### Gates re-run in this pass

| Command | Result |
|---|---|
| `uv run ruff format --check .` | **pass** — `429 files already formatted` |
| `uv run ruff check .` | **pass** — `All checks passed!` |
| `uv run python scripts/check_trailing_commas.py --check` | **pass** — exit 0 |
| `uv run python scripts/check_citations.py` | **pass** — `OK: 789 citations resolve (712 in 426 .py files, 77 in KANBAN.md)` |
| `git diff --check` | **pass** — exit 0 |
| `uv run pytest tests/test_ci_governance.py --no-cov -q -p no:cacheprovider` | **pass** — `86 passed` |
| slice scope (the 8 migrated files + the pin) | **pass** — `582 passed` |
| `/tmp/dsf-floor-029/bin/python -m pytest tests/test_ci_governance.py --no-cov -q -p no:cacheprovider` | **pass** — `86 passed` at the floor |

No `--cov*` flag in any command of this pass. **Staged-anchor sweep** for `TODO(spec-029` /
`TODO-(ALPHA|BETA|STABLE)-029` across the tree: **no live anchor** — every hit is prose inside the
spec's scaffolding section, the rationale companion's rev7 record, a sibling spec's
superseded-card list, or a prior artifact's own record of this sweep.

**`docs/TREE.md` staleness confirmed as not this slice's, read-only.** `docs/TREE.md` was copied to
`/private/tmp/dsf-w1fv2-tree/` and the generator run **against the scratch copy** (`--md <scratch>`);
the diff is exactly two lines, both
`tests/mutations/test_operations.py` rows belonging to the concurrent session, at `:515` and `:745`.
`git status --short -- docs/TREE.md` is empty; the generated doc was never written.

### Artifact hygiene

**Exactly one `Status:` line.** `grep -n '^Status:'` returns one hit, line 4. The three other
occurrences of the string are prose: an inline backticked `Status: built` inside pass 1's build
report at `:566`, my prior section's sentence at `:1602`, and Worker 3's note at `:2257`. Worker 3's
normalization took.

### DRY check across this slice and prior accepted slices

No new duplication. Slice 1 touched only `docs/SPECS/**`, so the two slices share no code surface.
Within this slice the 25 repaired sites adopt the idiom already carried by the pre-existing
`lambda: <instance>` entries rather than introducing a second spelling — measured here rather than
asserted: non-constructing `lambda: <name>` entries in a sequence literal number **81 at HEAD** and
**106 in the working tree**, a delta of exactly the 25 migrated sites. The plan's decided answer
against a shared `optimizer_factory()` helper was not disturbed, and pass 4 added no `scripts/` or
pre-commit mechanism. `docs/builder/temp-tests/slice-2-029/` holds a second copy of the pin's rule
in `classify.py` and my own probe manifests; all of it is gitignored per-cycle scratch that
`scripts/clean_up.py` clears, which is the right disposition.

### Spec changes made (Worker 1 only)

**None.** No box is left `- [ ]`, so no deferral reason is owed under this heading. No spec text
was falsified by what this slice landed. DoD item 4's reconciliation against what shipped is
Slice 3's, per the plan's ownership table and the sequencing that makes Slices 2 and 3 ordered
rather than parallel.

### Notes for Worker 1 (spec reconciliation) — the complete Slice 3 inheritance list

Restated here in full rather than by pointer, because a pointer into a 2,000-line artifact is how
the second site gets missed. Items 1-6 restate and complete my prior section's list; nothing in it
is retracted.

1. **Amendment 2 — DoD item 4 restated by FORM, and the one-shot-grep framing lives at TWO spec
   sites. This is BLOCKING; restating one is the parallel-site skip this repo's residual cycles
   call their dominant defect.** Both verified present in this pass:
   - `docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md:523` — `## Definition of done` item 4, the
     site Amendment 2 quotes: *"a **forbidden-form grep** (`extensions=[DjangoOptimizerExtension()]`
     / `[DjangoOptimizerExtension]` / `[ext]` / `[_CaptureExt()]` / `lambda: DjangoOptimizerExtension()`)
     finds zero hits in active source/docs"*.
   - `docs/SPECS/spec-029-consumer_dx_cleanup-0_0_9.md:60` — `## Slice checklist`
     `#"Post-migration forbidden-form gate:"`: *"a grep for the **exact forbidden forms** finds zero
     hits in active source/docs"*, enumerating the same five literal spellings.

   Both enumerate spellings where the normative sentence at `:56` states the rule by **form**, and
   that is the exact instrument that under-reported this regression by 13 of 18 constructing-lambda
   sites. **Both sites are restated or the divergence is not discharged.** Worker 3's three
   resolution paths stand: (a) restate both by form and point both at the standing pin; (b) restate
   item 4 and delete the checklist bullet's gate clause as superseded; (c) keep the checklist bullet
   as an explicit historical snapshot and say so. Any of the three is a decided answer; silence on
   the second site is not.
2. **The pin's name to cite, and the link definition it needs.**
   `tests/test_ci_governance.py::test_no_active_source_uses_a_forbidden_optimizer_extensions_form`.
   The spec has no `[test-ci-governance]` definition today (verified: `grep` returns nothing); add
   `[test-ci-governance]: ../../tests/test_ci_governance.py` under the `<!-- tests/ -->` group,
   alphabetically before `[test-extension]: ../../tests/optimizer/test_extension.py` at `:651`.
   Note the spec's own link block sorts by `ref-id]`, so check it against its own existing order.
3. **The exact measured population for the replacement text**, re-derived in this pass: **25
   forbidden entries in 8 files before the repair, 0 after** (18 constructing lambdas + 7
   bare-class-in-a-sequence), alongside **81** already-correct `lambda: <instance>` sequence entries
   at HEAD, 106 after. Do not restate the spec's own `~48 entries across five package test files` or
   `41` figures in a completion claim; those are build-plan divergence 9.
4. **"Active first-party source" now means something exact.** It is every `.py` that
   `git ls-files --cached --others --exclude-standard` reports — which the census asserts the gate
   covers, and which the oracle guard refuses to reason from when git did not answer about this
   checkout. Say it precisely if the DoD replacement uses the phrase: the gate walks the four
   `check_citations.SOURCE_TREES`, and three tracked `.py` files outside them
   (`conftest.py`, `line_count.py`, `docs/dry/export_dry_review.py`) are carried back by
   `EXTRA_SOURCE_FILES`. The gitignored `docs/*/temp-tests/` scratch is excluded by construction,
   which is deliberate and not an omission.
5. **Amendment 3 — Decision 3's granularity example.** The same-function `strictness="raise"` /
   `strictness="off"` pair at `tests/optimizer/test_extension.py:5602` / `:5611`
   (`raising_optimizer` / `silent_optimizer`) is a strictly better example of per-construction-site
   granularity than the cross-module one the spec currently uses. Verified present in this pass. The
   `~41` figure in that same sentence is one of the stale census numbers.
6. **Two items that are NOT Slice 3's and must not be routed into the spec.**
   - **Amendment 1** — `tests/test_ci_governance.py`'s first docstring line under-describes the
     module, but rewriting it requires regenerating `docs/TREE.md`, which is outside the
     maintainer's spec-files-and-`.py`-files fence. It belongs in `bld-final-029.md`'s
     `### Deferred work catalog`. The recommended replacement and the two `docs/TREE.md` sites are
     recorded in pass 1's `### Notes for Worker 1`.
   - **Box 11's wording recommendation** (Worker 2, pass 2) — the box is true as written and is
     deliberately unedited at three audits. A note for the record, not a spec item.

### For `bld-final-029.md`'s `### Deferred work catalog`

Carried, not fixed. The first item is new and is the reason this pass exists; the rest are outside
the maintainer's spec-files-and-`.py`-files fence.

- **ACCEPTED RESIDUAL, maintainer-facing: `tests/test_ci_governance.py` `#"CORPUS_REGIONS = ("` is
  unpinned — narrowing it fails 0 rows (measured, W1-C), and a same-arity substitution fails 0 rows
  while leaving the collected row count unchanged (W1-D).** Accepted as terminal by Worker 1's
  second final verification on the criterion recorded in `### The escalated question` above: the
  constant has exactly one reader, that reader is a `parametrize` position, and no surviving
  assertion reads it as data — so narrowing it deletes rows rather than degrading a live boundary,
  and no fix exists that is not subject to the identical edit. Not a `BUILD.md`
  `### Acceptance rule` exception (that rule governs boundaries; every boundary this slice added is
  pinned above 1 row). **The maintainer may overturn this**; if they do, the change is inside
  `tests/test_ci_governance.py` and the shape would be to inline the tuple into the decorator,
  which moves the narrowing target rather than removing it.
- `tests/test_ci_governance.py`'s first docstring line and the two `docs/TREE.md` rows it renders —
  Amendment 1.
- `docs/TREE.md` is stale at HEAD by exactly two lines (`:515`, `:745`), both for the concurrent
  session's untracked `tests/mutations/test_operations.py`. Verified read-only in this pass;
  not this cycle's and not to be fixed here.
- `CHANGELOG.md:173`, `:184`, `:186` carry 0.0.7-era consumer snippets showing the deprecated
  instance form `extensions=[DjangoOptimizerExtension()]`.
- `KANBAN.md:3597`, `:3603` — the `DONE-029` card body still names the rejected migration targets
  as Slice 1's goal.
- `docs/bug_hunt/temp-tests/resolvers_async_parity/` holds 4 forbidden-form entries in gitignored
  scratch, outside the pin's corpus by design.

### Summary

The slice delivered its contract. The `extensions=` forbidden-form regression is repaired at all
**25** sites in 8 files with **0** remaining anywhere in first-party source, re-derived here with a
controlled classifier against both HEAD and the working tree; no assertion was weakened across 91
changed lines; and maintainer decision D1's standing governance pin shipped with a classifier, 9+9
controls, a git-oracle corpus census, eleven per-file reach rows, a reporter seam, an
oracle-completeness guard, and pass 4's region contradictor. All 17 checklist boxes are ticked and
true. The hot-path number reproduces at `misses 2 -> 1`, `hits 0 -> 1`; the floor run reproduces at
86 passed on Python 3.10.19 / Django 5.2.16 / strawberry-graphql 0.316.0 with the shared `.venv`
unmutated; no mutation is live; the artifact carries one `Status:` line; every gate is green.

The escalated `CORPUS_REGIONS` question is **accepted as terminal**, on a criterion that is
structural and mechanically checkable rather than a judgement about likelihood: one reader, a
row-generating position, no surviving assertion reading it as data. That is what separates it from
`CORPUS_REACH_FILES`, which also fed `ORACLE_REQUIRED_FILES` and therefore left the M2 oracle guard
running and enforcing less — the defect L1 was filed on. The acceptance is routed to the final
gate's deferred catalog so the maintainer can overturn it without reading this artifact.

### Final status

`final-accepted`. The slice closes; Slice 3 inherits the six-item list above, item 1 blocking.
