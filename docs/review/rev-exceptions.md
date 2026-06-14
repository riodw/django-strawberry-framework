# Review: `django_strawberry_framework/exceptions.py`

Status: verified

> Release 0.0.9 review cycle. This artifact supersedes the prior 0.0.7-cycle
> contents (which closed `verified` against `review-0_0_7.md`). The findings
> below are new drift accrued since: the 0.0.7 fix's `Current raise sites in
> 0.0.7:` label is now version-stale at 0.0.9, and the `ConfigurationError`
> deferred-key example went stale when `filterset_class` / `orderset_class`
> shipped in 0.0.8.

## DRY analysis

- None — the three-class hierarchy carries no executable code, no repeated literals (shadow overview: 0 repeated string literals), and no duplicated logic; each docstring is unique prose. The base/subclass factoring is already minimal and the package consistently imports these three names rather than redefining error types (confirmed across `conf.py`, `registry.py`, `types/`, `optimizer/`, `filters/`, `orders/`, `utils/`, `testing/` — every raise site imports from `.exceptions`). `utils/querysets.py::SyncMisuseError` correctly extends `ConfigurationError` rather than duplicating it. Cross-file DRY of `raise ConfigurationError(...)` literals is a folder/project-pass concern, not a local one.

## High:

None.

## Medium:

None.

## Low:

### Stale `OptimizerError` version label, now non-exhaustive

The `OptimizerError` docstring (`django_strawberry_framework/exceptions.py #"Current raise sites in 0.0.7"`) pins its raise-site inventory to "0.0.7", but `pyproject.toml` and `django_strawberry_framework/__init__.py` are both at `0.0.9`. The inventory is also now incomplete: `grep -rn "raise OptimizerError" django_strawberry_framework/` returns four sites, and the docstring names only two. Beyond the listed `FieldMeta.from_django_field` guard (`optimizer/field_meta.py:156`) and the relation-resolver N+1 guard (`types/resolvers.py:188`), `0.0.9` added the connection-path N+1 raise (`django_strawberry_framework/connection.py #"unplanned, unserved nested-connection access fires"`, GLOSSARY line 1263) and `optimizer/plans.py::` raises `OptimizerError` for a single-valued forward relation (`plans.py:567`, `plans.py:575`) — neither is named.

Recommended change (root-cause): retitle the block to a version-agnostic `Raise sites:` so the label stops accruing per-release staleness debt, and either enumerate all four current sites or describe the two families (typed input-guard at construction; strictness-`"raise"` N+1 guard covering both list and connection relation paths). Version-agnostic phrasing is the higher-quality fix — re-pinning to `0.0.9` only defers the same drift to the next bump.

```django_strawberry_framework/exceptions.py:36:44
    Current raise sites in 0.0.7:
        - ``FieldMeta.from_django_field`` rejects an input that is not a
          Django field descriptor (missing ``name`` / ``is_relation``),
          converting an otherwise late ``AttributeError`` into a typed,
          call-site failure naming the bad input.
        - The relation resolver's N+1 guard fires when optimizer
          ``strictness`` is ``"raise"`` and a request reaches an unplanned
          relation that would lazy-load.
```

### Stale `ConfigurationError` deferred-key example

The `ConfigurationError` docstring (`django_strawberry_framework/exceptions.py #"A deferred-surface key"`) lists `filterset_class` and `orderset_class` among the "deferred-surface key[s] ... declared before the spec that owns it has shipped." Both have since shipped: `types/base.py:60-61` shows `DEFERRED_META_KEYS` now holds only `{"aggregate_class", "fields_class", "search_fields"}`, while `filterset_class` (`types/base.py:70`) and `orderset_class` (`types/base.py:77`) live in the ALLOWED set with working validators (`types/base.py::_validate_filterset_class`, `types/base.py::_validate_orderset_class`). GLOSSARY line 808 confirms `orderset_class` is "no longer in `DEFERRED_META_KEYS` since `0.0.8`." The example now names two keys that no longer raise on declaration, misdescribing the contract.

Recommended change: drop `filterset_class` and `orderset_class` from the parenthetical so it reads `(aggregate_class, fields_class, search_fields)` — matching the current `DEFERRED_META_KEYS` exactly.

```django_strawberry_framework/exceptions.py:26:30
        - A deferred-surface key (``filterset_class``, ``orderset_class``,
          ``aggregate_class``, ``fields_class``, ``search_fields``)
          declared before the spec that owns it has shipped.
```

## What looks solid

### DRY recap

- **Existing patterns reused.** The module is the single source of truth for the package's exception types; every raise site across the package imports `ConfigurationError` / `OptimizerError` from `.exceptions` rather than redefining (verified by grep across `conf.py`, `registry.py`, `types/`, `optimizer/`, `filters/`, `orders/`, `utils/`, `testing/`). `utils/querysets.py::SyncMisuseError` extends `ConfigurationError` (multiple-inherits `RuntimeError`) instead of forking a parallel error family — the DRY win is realized.
- **Duplication risk in the current file.** None — three unique docstrings, no repeated literals (shadow overview confirms 0), no near-copy class bodies. The "Raised when ..." prose pattern across the two subclasses is intentional sibling design: each class needs to be greppable and IDE-hoverable in isolation for its own raise context.

### Other positives

- **review_inspect helper skipped — justified.** Per `REVIEW.md` "Static review helper", the helper may be skipped for pure-class-definition modules. The plan-time `--all` overview already exists (`docs/shadow/django_strawberry_framework__exceptions.overview.md`) and confirms the skip-artifact shape: 0 imports, 0 executable marker lines, 0 control-flow hotspots, 0 calls of interest, 3 symbols all class definitions. No re-run needed.
- **Bottom-of-import-graph placement.** The module docstring's promise (no Django / Strawberry / internal imports → no circulars) is enforced: shadow overview reports `imports: 0`. The breadth of raise sites across the package confirms the hierarchy can be raised from anywhere.
- **`__all__` is explicit and alphabetized** (`exceptions.py:8`), covering all three public classes; matches the three defined symbols exactly.
- **Hierarchy design is sound.** Single base (`DjangoStrawberryFrameworkError`) with two cause-distinguishing subclasses; consumers catch broad or narrow. Docstrings document the catch-this-to-handle-all contract.
- **Ruff clean.** `uv run ruff format --check django_strawberry_framework/exceptions.py` → already formatted; `uv run ruff check django_strawberry_framework/exceptions.py` → all checks passed.
- **GLOSSARY drift quick-check.** `ConfigurationError` glossary entry (`docs/GLOSSARY.md:212`, shipped `0.0.1`) is consistent with the source-class contract (unknown / deferred `Meta` keys, post-finalize declaration, primary collisions, choice / array / hstore rejections, `CompositePrimaryKey` + `relay.Node`); no GLOSSARY-only fix in scope for `ConfigurationError`. `OptimizerError` and `DjangoStrawberryFrameworkError` carry no standalone GLOSSARY entries — non-contract symbols, no drift to fix; if the project pass decides to enforce uniform `__all__` ↔ GLOSSARY coverage, that belongs in `rev-django_strawberry_framework.md`, not here.

### Summary

`exceptions.py` is a clean, correctly-placed pure-class-definition module — the textbook skip-artifact shape (0 imports, 0 executable code, 3 class definitions; static helper skip justified). No logic defects, no DRY opportunities, no `ConfigurationError` GLOSSARY contract drift. The only findings are two stale docstring examples accrued since the 0.0.7 cycle: the `OptimizerError` "raise sites in 0.0.7" label is version-stale and now non-exhaustive (the `0.0.9` connection path and the `optimizer/plans.py` forward-relation site both raise `OptimizerError` and go unnamed), and the `ConfigurationError` deferred-key list still names `filterset_class` / `orderset_class`, both of which shipped (no longer in `DEFERRED_META_KEYS` as of `0.0.8`). Both are Low (comment-pass, non-contract for these exact symbols) but real — they misdescribe current shipped behavior — so this routes as a standard `under-review` cycle for Worker 2 to make the docstring edits, NOT a no-source-edit (shape #5) collapse. Shape #2 (skip artifact) holds for the *code structure*, but the live docstring corrections require a real source edit, so the artifact does not collapse to a no-findings skip.

---

## Fix report (Worker 2)

Consolidated single-spawn (2 Lows, docstring-only, no logic/behaviour change;
both real comment-pass findings, both premises verified against source). Logic +
comment + changelog disposition collapsed per role-file rule "the artifact's only
in-cycle edit is a single trivially-localised docstring sentence with no logic
change" (here two such docstring blocks, both in one file, no logic touched).

### Files touched
- `django_strawberry_framework/exceptions.py:26-28` — `ConfigurationError`
  docstring: dropped the now-shipped `filterset_class` / `orderset_class` from the
  deferred-surface-key parenthetical so it reads exactly the current
  `DEFERRED_META_KEYS` membership `(aggregate_class, fields_class, search_fields)`.
- `django_strawberry_framework/exceptions.py:36-47` — `OptimizerError` docstring:
  retitled the version-pinned `Current raise sites in 0.0.7:` to a version-agnostic
  `Raise sites:` (root-cause fix; stops per-release staleness debt) and described
  the two raise-families rather than re-enumerating, so the block stays accurate as
  sites are added: (1) typed input-guard at construction; (2) strictness-`"raise"`
  N+1 guard covering BOTH the list-relation resolver and the nested-connection
  window-partition path.

### Tests added or updated
- None. Pure docstring text; no behaviour change, no branch added/removed. Per
  role-file Low dicta ("avoid adding tests for purely internal refactors") and the
  shadow overview (0 executable lines, 3 class defs) no test is possible or
  warranted — the module has no runtime to assert against.

### Validation run
- `uv run ruff format .` — pass / no-changes (265 files left unchanged).
- `uv run ruff check --fix .` — pass / all checks passed.
- Diff vs baseline `0872a20`: exceptions.py was UNCHANGED since baseline (these
  docstrings are stale-since-0.0.7, not newly-introduced drift); the only post-edit
  diff to exceptions.py is this cycle's two docstring blocks.

### Notes for Worker 3
- Premises verified against source-of-truth before editing:
  - `OptimizerError` raise sites = 4 via `grep -rn "raise OptimizerError"`:
    `optimizer/field_meta.py:156`, `types/resolvers.py:188`, and
    `optimizer/plans.py:567` + `:575`. The artifact attributed the connection-path
    raise to `connection.py`; the actual `raise OptimizerError` lives in
    `optimizer/plans.py::window_partition_for_prefetch` (plans.py:567/575), which
    `connection.py` reaches downstream. I described it as the "nested-connection
    window-partition path" to be accurate to the real raise site. Chose the
    two-families description (artifact's offered alternative) over enumerating four
    sites — keeps the docstring stable across future site additions.
  - `DEFERRED_META_KEYS` = `frozenset({"aggregate_class", "fields_class",
    "search_fields"})` at `types/base.py:60-62`; `filterset_class` (base.py:70) and
    `orderset_class` (base.py:77) are in `ALLOWED_META_KEYS` with live validators
    `_validate_filterset_class` / `_validate_orderset_class`. New parenthetical
    matches the frozenset exactly.
- No false-premise rejections — both Lows held.
- Shadow file consulted: `docs/shadow/django_strawberry_framework__exceptions.overview.md`
  (confirmed skip-artifact shape; not used for line numbers).
- `uv.lock` untouched after both `uv run` commands.

---

## Verification (Worker 3)

### Logic verification outcome
Both Worker 1 Lows independently re-verified against source-of-truth; both held.

- **Low 1 (`OptimizerError` raise sites).** `grep -rn "raise OptimizerError"` returns
  exactly 4 sites: `optimizer/field_meta.py:156`, `types/resolvers.py:188`,
  `optimizer/plans.py:567` + `:575`. Read each:
  - `field_meta.py:156` — `if not hasattr(field, "name") or not hasattr(field, "is_relation")`
    guard, converting a late `AttributeError` into a typed call-site failure naming the
    bad input. Matches docstring family (1) "typed input-guard at construction".
  - `resolvers.py:188` — `if strictness == "raise": raise OptimizerError(f"Unplanned N+1: ...")`.
    The list/many-side relation resolver N+1 guard. Matches docstring family (2),
    "list-relation resolver" arm.
  - `plans.py:567`/`:575` — both inside `window_partition_for_prefetch` (def at
    `plans.py:542`): `:567` raises for a relation kind not in
    `("many","reverse_many_to_one","reverse_one_to_one")` (single-valued forward / no
    windowable partition); `:575` raises when the parent partition can't be resolved.
    Matches docstring family (2), "nested-connection window-partition path (a single-valued
    forward relation or any kind without a windowable parent partition)". Worker 2's
    correction of the artifact's `connection.py` attribution to the real `plans.py` raise
    site is accurate — `connection.py` reaches this downstream. The retitle to
    version-agnostic `Raise sites:` and the two-families phrasing are faithful and
    version-agnostic (root-cause fix; no per-release staleness debt).
- **Low 2 (`ConfigurationError` deferred-key example).** `types/base.py:60-62` is
  `DEFERRED_META_KEYS = frozenset({"aggregate_class", "fields_class", "search_fields"})`
  exactly. `filterset_class` (base.py:70) and `orderset_class` (base.py:77) are in
  `ALLOWED_META_KEYS`, no longer deferred. New docstring parenthetical lists exactly the
  three frozenset members (`aggregate_class`, `fields_class`, `search_fields`) — no shipped
  `filterset_class`/`orderset_class`. Matches source-of-truth.

Diff vs baseline `0872a20` is docstring-only: two blocks (`ConfigurationError` parenthetical,
`OptimizerError` raise-sites). No logic, no executable lines, no `__all__`/class-body change.

### DRY findings disposition
Worker 1 reported None; confirmed — pure-class-definition module, 0 imports / 0 executable
lines / 3 class defs (shadow overview), 0 repeated literals. No DRY action.

### Temp test verification
- None created. Pure docstring text, no runtime to assert against (per AGENTS.md "no test
  possible" — module has 0 executable lines). pytest not run (correct; no test introduced).

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the checklist box.
Changelog `Not warranted` verified: `git diff -- CHANGELOG.md` empty; disposition cites BOTH
AGENTS.md #21 and the plan's silence; internal-only framing honest (typed-error runtime
contracts unchanged). Ruff: `format --check` already formatted, `check` all passed.

---

## Comment/docstring pass

(Folded into the consolidated spawn — the two findings ARE the docstring pass.)

### Files touched
- `django_strawberry_framework/exceptions.py:26-28` and `:36-47` — see Fix report.

### Per-finding dispositions
- Low 1 (`OptimizerError` stale `0.0.7` label, now non-exhaustive): FIXED.
  Retitled to version-agnostic `Raise sites:` and switched to a two-families
  description (typed input-guard at construction; strictness-`"raise"` N+1 guard
  covering list-relation + nested-connection window-partition paths). Root-cause
  fix per the artifact's recommendation — re-pinning to `0.0.9` only defers drift.
- Low 2 (`ConfigurationError` stale deferred-key example): FIXED. Dropped the
  shipped `filterset_class` / `orderset_class`; parenthetical now exactly mirrors
  `DEFERRED_META_KEYS = {aggregate_class, fields_class, search_fields}`.

### Validation run
- `uv run ruff format .` — pass / no-changes.
- `uv run ruff check --fix .` — pass.

### Notes for Worker 3
See Fix report Notes — both premises confirmed against source; no rejections.

---

## Changelog disposition

### State
`Not warranted`.

### Reason
- `AGENTS.md` #21: "Do not update CHANGELOG.md unless explicitly instructed."
- The dispatch prompt explicitly forbids CHANGELOG edits and instructs recording
  disposition in the artifact; this is a per-file cycle, which is NEVER the
  authorising scope (role-file changelog dicta: per-file/folder passes forward
  drift to the project pass). The edits are docstring-only with no
  consumer-visible behaviour, typed-error-contract, or public-symbol change — the
  `OptimizerError` / `ConfigurationError` runtime contracts are unchanged.

### What was done
No `CHANGELOG.md` edit.

### Validation run
- `uv run ruff format .` — pass / no-changes.
- `uv run ruff check --fix .` — pass.

---

## Iteration log
