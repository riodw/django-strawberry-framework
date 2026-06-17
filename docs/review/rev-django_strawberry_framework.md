# Review: `django_strawberry_framework/` (project-level pass + top-level `__init__.py`)

Status: verified

Project-level synthesis pass over the whole package, covering the public API surface in
`django_strawberry_framework/__init__.py`. All 7 folder passes are `verified`
(`rev-filters.md`, `rev-management.md`, `rev-optimizer.md`, `rev-orders.md`,
`rev-testing.md`, `rev-types.md`, `rev-utils.md`). Baseline HEAD (`14910230`).
`git diff HEAD -- django_strawberry_framework/__init__.py` is empty; the only since-baseline
top-level commit (`06966aa2`) is the `0.0.10` version bump, already merged. Concurrent
dirty files (spec-036 / management `_imports.py`, GOAL.md, TREE.md, etc.) are another dev's
in-progress work, ignored per AGENTS.md #33.

## DRY analysis

- **Cross-folder `filters/`↔`orders/` family-wrapper layer — defer-with-trigger, do NOT
  merge.** Every order-side sibling artifact (`rev-orders__base.md`, `rev-orders__inputs.md`,
  `rev-orders__sets.md`, `rev-orders.md`) and the filters folder pass (`rev-filters.md`)
  independently forwarded the same observation: the two families carry byte-symmetric
  *wrapper shapes* over already-single-sited cores. The logic is NOT duplicated — it is
  single-sited in `utils/` and `sets_mixins/`:
  - permission delegates: `OrderSet._request_from_info` / `_extract_branch_value` /
    `_active_permission_field_paths` / `_active_permission_targets` /
    `_invoke_permission_method` / `_run_permission_checks` (`orders/sets.py:302-455`) vs the
    same-named `FilterSet` twins (`filters/sets.py:1285-...`), each a thin delegate to
    `utils/permissions.py`.
  - input-namespace materialize/clear + domain aliases (`orders/inputs.py:323-391`,
    `49-52`) vs `filters/inputs.py`, both delegating to `utils/inputs.py`.
  - `OrderArgumentsFactory` / `FilterArgumentsFactory` 7-attr parameterizations over
    `utils/inputs.py::GeneratedInputArgumentsFactory`.
  - `RelatedOrder` / `RelatedFilter` parameterizations over
    `sets_mixins.py::RelatedSetTargetMixin` (`sets_mixins.py:142-187`).
  - `order_input_type` / `filter_input_type`, both one-line delegates to
    `utils/inputs.py::build_lazy_input_annotation`.

  The residual per-family residue is the family-label string (`"OrderSet"`/`"orderset"`/
  `"related_orders"` vs `"FilterSet"`/`"filterset"`/`"related_filters"`) and `logic_keys`
  (`frozenset()` vs the filter operator bag). The wrapper method names ARE the documented
  consumer-facing public surface (`bind_orderset` / `.orderset` / `bind_filterset` /
  `.filterset`), so any `PermissionDelegateMixin`-style hoist must preserve every public
  method name and would couple two folders to one new shared abstraction.
  **Defer until a third declarative set family lands (e.g. `AggregateSet`,
  `WIP-ALPHA-028` / `0.1.3`); then triage the whole filters+orders+utils wrapper layer
  through one shared mixin parameterized by a per-family config object.** At N=2 the
  family-named wrappers are the correct readable shape; folding now trades a documented,
  greppable public surface for a config-indirection that two consumers do not yet justify.

- **filter/order `normalize_input_value` same-name pair — NOT a shared traversal; record,
  do not merge.** `orders/inputs.py::normalize_input_value` (`orders/inputs.py:260-320`) is a
  whole-input *walker* delegating its dataclass/list/`None`-skip/leaf-vs-related traversal to
  the single-sited `utils/input_values.py::iter_active_fields` (`orders/inputs.py:304`),
  emitting `(field_path, Ordering | None)`. `filters/inputs.py::normalize_input_value`
  (`filters/inputs.py:412-460`) is a per-leaf value *coercion* (`isinstance`-dispatch into
  scalar/list/dict form-data) that does no traversal and is called from inside the filter
  walker. Same name, different abstraction level; the only common mechanics
  (`iter_active_fields`) are already single-sited and consumed by the order side. Confirmed
  from both sides in `rev-orders__inputs.md`. **No trigger — this is intentional sibling
  naming, not a deferred merge.** Renaming one to disambiguate is the only conceivable
  action and is net-negative (both names match their family's spec vocabulary).

## High:

None.

## Medium:

None.

## Low:

### GLOSSARY `DjangoListField` entry under-describes the async-resolver predicate (`iscoroutinefunction` vs `is_async_callable`)

`docs/GLOSSARY.md:355` (the `DjangoListField` entry) describes async-resolver detection as
"detected at construction time via `inspect.iscoroutinefunction` (checked on the resolver
itself AND on its `__call__` ...)". The source routes through
`utils/typing.py::is_async_callable` (`list_field.py:176`, `connection.py:1005`), which is a
strict superset: besides the resolver and its `__call__`, it also unwraps a one-hop
`functools.partial` (`utils/typing.py::is_async_callable`
#"value.func if isinstance(value, functools.partial)" at `utils/typing.py:40`). The prose is
not wrong about what it lists — it is incomplete: a `functools.partial(async_callable)`
resolver IS detected, but the wording implies it is not. This is descriptive prose on a
public-contract symbol.

Scope correction vs the forward: the rev-list_field.md / rev-utils.md forwards predicted the
same `iscoroutinefunction` phrasing "recurs across the connection-field and relay-node
entries", making it a package-wide sweep. It does NOT. `grep -n iscoroutinefunction
docs/GLOSSARY.md` returns exactly one hit — line 355. The connection-field, node-field, and
relay entries describe async via the generic "sync and async resolver paths" /
"async resolvers await the latter" phrasing and never name `iscoroutinefunction`. So this is
a **single-entry** accuracy fix, not a three-entry sweep. The source comments already lead
the docs correctly (`list_field.py:156-158` names the "`__call__`/`functools.partial`-aware
superset of `inspect.iscoroutinefunction`"); only GLOSSARY:355 lags.

Disposition: **act-now GLOSSARY accuracy fix** (real edit on a public-contract symbol →
shape #4 doc-fix through Worker 2), because the fix is a single-line clause swap on one
documented public symbol and the source/GLOSSARY drift is confirmed, not speculative. Lift
this replacement clause verbatim (replaces the existing "Async consumer resolvers are
detected at construction time via `inspect.iscoroutinefunction` (checked on the resolver
itself AND on its `__call__` so callable-instance resolvers with `async def __call__` are
also covered)" sentence):

```docs/GLOSSARY.md:355
Async consumer resolvers are detected at construction time via the partial-aware
`is_async_callable` predicate (checked on the resolver, on its `__call__` so
callable-instance resolvers with `async def __call__` are covered, and through a one-hop
`functools.partial`) and routed through an `async def` wrapper that awaits the coroutine
before applying the isinstance check.
```

Worker 2: this is the only GLOSSARY entry to touch — do NOT sweep the connection/node
entries (they do not name `iscoroutinefunction`).

## What looks solid

### DRY recap

- **Existing patterns reused.** The top-level `__init__.py` is a pure re-export façade: it
  re-exports each public symbol from its owning module (`connection`, `list_field`,
  `optimizer`, `optimizer.hints`, `permissions`, `relay`, `scalars`, `types`) and re-exports
  `auto` straight from `strawberry` — zero re-declaration. The package logger string
  `"django_strawberry_framework"` is declared in exactly one source location
  (`__init__.py:13`) and subpackages re-export it via `from .. import logger`
  (documented at `__init__.py:7-12`, e.g. `optimizer/__init__.py`), so the logger name is
  single-sited.
- **New helpers considered.** None warranted at project scope. The cross-folder
  family-wrapper layer (see DRY analysis) is the only package-wide consolidation candidate
  and is correctly deferred at N=2 — extracting a shared mixin now would couple two folders
  to one abstraction for no readability or correctness gain.
- **Duplication risk in the current file.** The eight `# noqa: E402` markers on the local
  imports are an intentional, self-documented sibling pattern, not duplication: the logger
  must be constructed before any subpackage import runs (subpackages do
  `from .. import logger` at import time), so the imports are deliberately placed after the
  `logging.getLogger(...)` line, and E402 is suppressed per-line with the rationale comment
  at `__init__.py:15`. This is the correct ordering, not a smell.

### Other positives

- **Public API surface is coherent and matches the docs.** `__all__` (16 entries) resolves
  cleanly — a live `import django_strawberry_framework` succeeds (no circular-import
  failure), `__version__ == "0.0.10"`, every `__all__` name has a resolvable attribute, and
  `auto` is both in `__all__` and present. The GLOSSARY "Symbols re-exported from
  `django_strawberry_framework`" list (`docs/GLOSSARY.md:24-41`) is a one-to-one match with
  `__all__`: BigInt, DjangoConnection, DjangoConnectionField, DjangoListField,
  DjangoNodeField, DjangoNodesField, DjangoType, DjangoOptimizerExtension, OptimizerHint,
  SyncMisuseError, apply_cascade_permissions, aapply_cascade_permissions,
  finalize_django_types, strawberry_config, auto, `__version__`. (Note: `DjangoListField` is
  documented in the GLOSSARY list but lands in the package namespace via its own import at
  `__init__.py:18` and IS in `__all__` — consistent.)
- **Version consistency holds.** `pyproject.toml` `version = "0.0.10"` ==
  `__init__.py::__version__ = "0.0.10"` == GLOSSARY current-version banner
  (`docs/GLOSSARY.md:20`) == README (`README.md:61`). AGENTS.md #31's dual-bump invariant is
  satisfied.
- **`logger` declaration is correctly out of `__all__` but documented as public.** The
  comment (`__init__.py:7-12`) explains it is the key consumers use in Django's `LOGGING`
  config — consumer-facing surface, deliberately not an `__all__` star-export. Correct
  treatment of a public-but-non-star symbol.
- **Dependency direction is one-way and acyclic.** Layering holds: `utils/` ←
  {`filters/`, `orders/`, `optimizer/`, `types/`} ← top-level. The two in-source
  `from django_strawberry_framework import ...` hits are both safe — a comment
  (`connection.py:916`) and a `TYPE_CHECKING`-guarded self-import in `optimizer/hints.py:8`
  (no runtime cycle; the clean live import confirms it). The per-folder passes confirmed
  strictly-inward intra-folder DAGs; the project import succeeds, so no import-time cycle
  exists across folders.
- **Naming / error-handling consistency across folders.** Error types are single-sited and
  re-exported, never re-declared: `SyncMisuseError` defined in `utils/querysets.py`,
  re-exported from `types/relay.py` and `permissions.py` and out the package root;
  `ConfigurationError` / family errors single-sited in `exceptions.py`. `verbatim_path` is
  the single public consolidation point in `utils/permissions.py` (`:149`) consumed by
  `orders/sets.py:47,362` with zero `_verbatim_*` orphans anywhere in source or tests
  (forward #3 below — already resolved upstream).

### Summary

The package presents a clean, coherent public surface. The top-level `__init__.py` is a
pure re-export façade with single-sited logger declaration, a self-documented E402
import-ordering dance justified by the logger-before-subpackages constraint, an `auto`
re-export that keeps consumers off a direct Strawberry import, version `0.0.10` consistent
across pyproject / `__init__` / GLOSSARY / README, and an `__all__` that is a one-to-one
match with the GLOSSARY export table and imports cleanly with no circular-import failure.
Dependency direction is strictly inward (`utils/` ← families ← top-level) and acyclic at
runtime. The only project-scope finding is one Low: a single GLOSSARY entry
(`docs/GLOSSARY.md:355`, `DjangoListField`) under-describes the async-resolver predicate as
`inspect.iscoroutinefunction` when the source uses the partial-aware `is_async_callable`
superset — a confirmed source/doc drift on a public-contract symbol, dispositioned as an
act-now single-entry doc fix (shape #4 via Worker 2). The forward's "recurs across
connection/relay entries" framing was corrected: `iscoroutinefunction` appears in exactly
one GLOSSARY entry. The cross-folder filters↔orders family-wrapper consolidation is
correctly deferred-with-trigger (third set family), and the `normalize_input_value`
same-name pair is a confirmed different-abstraction non-merge. Because the GLOSSARY fix is a
real tracked-file edit, this artifact is `under-review` and routes to Worker 2.

---

## Fix report (Worker 2)

Consolidated single-spawn pass (shape #4, GLOSSARY-accuracy doc-only fix): logic + comment +
changelog disposition recorded together; Worker 3 verifies once.

### Files touched
- `docs/GLOSSARY.md:355` — `DjangoListField` entry: replaced the inaccurate
  `inspect.iscoroutinefunction` async-detection clause with the artifact's verbatim
  replacement naming the partial-aware `is_async_callable` predicate. Single-clause swap; rest
  of the entry untouched.

### Tests added or updated
- None. Doc-accuracy fix on a GLOSSARY entry; no behavior change. AGENTS.md/worker-2.md test
  rules do not apply to markdown prose, and the artifact dispositioned this as a single-line
  clause swap.

### Validation run
- `uv run ruff format .` — pass / no-changes (270 files left unchanged; markdown untouched).
- `uv run ruff check --fix .` — pass / no-changes (All checks passed!).
- `git status --porcelain uv.lock` — clean (uv.lock not touched).

### Notes for Worker 3
- Source confirmed before editing: `utils/typing.py::is_async_callable` (`utils/typing.py:40`)
  does `value.func if isinstance(value, functools.partial) else value`, then
  `iscoroutinefunction(target) or iscoroutinefunction(target.__call__)` — i.e. one-hop partial
  unwrap + resolver + `__call__`. Corrected GLOSSARY prose matches all three.
- Scope confirmed: `grep -n iscoroutinefunction docs/GLOSSARY.md` → exactly ONE hit (line 355);
  one changed. Connection/node/relay entries use generic "sync and async resolver paths"
  wording (correct) and were NOT touched, per the artifact's explicit scope instruction.
- Edit is link-neutral: only in-page anchors (`](#...)`) appear in the entry; they stay inline
  per START.md and were not disturbed. No reference-style cross-file links in scope.
- No shadow file used (markdown target).

---

## Verification (Worker 3)

Consolidated shape-#4 single terminal verify (logic + comment + changelog in one pass).

### Logic verification outcome
- **Diff is exactly the one GLOSSARY clause.** `git diff HEAD -- docs/GLOSSARY.md` = a single
  line-355 change (the `DjangoListField` entry); no other GLOSSARY entry swept. `git diff HEAD --
  CHANGELOG.md` empty. The `git diff --stat HEAD` source/test hunks (orders/sets.py,
  utils/permissions.py, optimizer/selections.py, management/commands/{_imports,export_schema,
  inspect_django_type}.py, tests/management/test_imports.py, tests/orders/test_factories.py) are
  uncommitted working-tree work owned by CLOSED sibling cycles — `rev-orders.md`,
  `rev-utils.md`, `rev-optimizer.md`, `rev-management__commands.md` all `Status: verified`. None
  is GLOSSARY/CHANGELOG; none is this project cycle's. No source/test change attributable here.
- **Corrected clause is ACCURATE against source.** `utils/typing.py::is_async_callable`
  (`utils/typing.py:40-45`) does `target = value.func if isinstance(value, functools.partial)
  else value` then `iscoroutinefunction(target) or iscoroutinefunction(target.__call__)` — i.e.
  one-hop `functools.partial` unwrap + resolver + `__call__`. The detection site routes through
  it (`list_field.py:176 if is_async_callable(user_resolver)`; import at `list_field.py:27`). The
  new prose ("partial-aware `is_async_callable` ... checked on the resolver, on its `__call__`
  ..., and through a one-hop `functools.partial`") matches all three. The old
  `inspect.iscoroutinefunction` claim was genuinely incomplete: per the docstring
  (`utils/typing.py:29-31`) bare `iscoroutinefunction` only unwraps a partial whose `.func` is
  itself `async def`, NOT a partial around an async callable instance — so a
  `functools.partial(async_callable_instance)` resolver IS detected by the source but the old
  wording implied it was not. Confirmed inaccurate, now correct.
- **Zero stale `iscoroutinefunction` in GLOSSARY.** `grep -n iscoroutinefunction docs/GLOSSARY.md`
  → ZERO hits post-edit; `grep -n is_async_callable` → exactly ONE hit (line 355, the corrected
  entry). No same-defect residue elsewhere.
- **Project `__init__.py` findings sound (independently spot-checked).** `import
  django_strawberry_framework` succeeds with no circular-import failure; `__version__ ==
  "0.0.10"` consistent across pyproject.toml:4 / `__init__.py`:29 / GLOSSARY:20 / README:61
  (AGENTS.md #31 dual-bump satisfied); `__all__` = 16 entries, every name resolves, `auto`
  present and in `__all__`. Layering claim holds: `grep -rE "from \.\.(filters|orders|optimizer|
  types|management|testing)"` over `utils/` = ZERO sibling back-edges (utils imports nothing from
  sibling subsystems; strictly inward, acyclic).
- **4 forward dispositions reasonable; nothing deferred is a dodged act-now defect.** (1) GLOSSARY
  async-predicate = act-now, done; (2) filters↔orders family-wrapper DRY = defer-with-trigger
  (third set family) — correct at N=2, the logic is already single-sited in utils/sets_mixins and
  the residue is family-label strings; folding now trades a greppable public surface for
  config-indirection (net-negative); (3) `normalize_input_value` same-name pair = confirmed
  different-abstraction (order=whole-input walker, filter=per-leaf coercion), non-merge, no
  trigger; (4) utils `__all__`/`instance_accessor`/`is_async_callable` submodule-direct
  asymmetries = forward-defer (a package-root import would be the trigger). None hides a
  correctness/permission defect.

### DRY findings disposition
Both project-scope DRY items carried forward as the artifact dispositioned: filters↔orders
wrapper layer deferred-with-trigger (N=2 → third family); `normalize_input_value` recorded as an
intentional sibling-naming non-merge. Neither warranted an edit this cycle.

### Temp test verification
- None. Doc-accuracy clause swap on a public-contract symbol; no behavior change, no test owed
  (AGENTS.md/worker rules do not apply to markdown prose).

### Changelog disposition (verified)
`Not warranted` accepted. `git diff HEAD -- CHANGELOG.md` empty (matches the state). The cycle's
only edit is an internal GLOSSARY accuracy correction — no consumer-visible behavior or
public-symbol change (the source already behaves as the corrected prose describes), so
"internal-only" framing is honest, not an under-statement of a public-API change. Both required
citations present: AGENTS.md #21 ("Do not update CHANGELOG.md unless explicitly instructed") AND
active-plan/dispatch silence on changelog authorization.

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the project-level pass
checklist box.

---

## Comment/docstring pass

Folded into the consolidated single-spawn. The single in-cycle edit IS the descriptive-prose
correction; there is no separate code comment/docstring to revise. The leading source comments
(`list_field.py:156-158`) already name the "`__call__`/`functools.partial`-aware superset of
`inspect.iscoroutinefunction`" correctly — only GLOSSARY:355 lagged, and it is now corrected.

### Files touched
- None beyond the GLOSSARY:355 clause swap recorded in `## Fix report (Worker 2)`.

### Per-finding dispositions
- Low (GLOSSARY `DjangoListField` async-predicate under-description): fixed — clause swapped to
  the partial-aware `is_async_callable` wording per the artifact's verbatim replacement.

### Validation run
- `uv run ruff format .` — pass / no-changes.
- `uv run ruff check --fix .` — pass / no-changes.

### Notes for Worker 3
Old → new clause:
- OLD: "Async consumer resolvers are detected at construction time via
  `inspect.iscoroutinefunction` (checked on the resolver itself AND on its `__call__` so
  callable-instance resolvers with `async def __call__` are also covered) and routed through an
  `async def` wrapper that awaits the coroutine before applying the isinstance check."
- NEW: "Async consumer resolvers are detected at construction time via the partial-aware
  `is_async_callable` predicate (checked on the resolver, on its `__call__` so
  callable-instance resolvers with `async def __call__` are covered, and through a one-hop
  `functools.partial`) and routed through an `async def` wrapper that awaits the coroutine
  before applying the isinstance check."

---

## Changelog disposition

### State
`Not warranted`.

### Reason
The cycle's only edit is an internal documentation-accuracy correction to a GLOSSARY entry —
no consumer-visible behavior, public-symbol, or typed-error change; the source already behaves
as the corrected prose now describes. Cited per the Not-warranted rule:
- AGENTS.md #21 — "Do not update CHANGELOG.md unless explicitly instructed."
- Active plan silence — this cycle's dispatch/artifact carry no CHANGELOG authorization, and
  the dispatch prompt explicitly states changelog is Not-warranted here and CHANGELOG.md must
  not be edited. A per-file/folder/project doc-accuracy fix is never an authorising scope.

### What was done
No `CHANGELOG.md` edit. `git diff HEAD -- CHANGELOG.md` is empty.

### Validation run
- `uv run ruff format .` — pass / no-changes.
- `uv run ruff check --fix .` — pass / no-changes.

---

## Iteration log

_Empty._
