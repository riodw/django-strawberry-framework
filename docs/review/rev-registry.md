# Review: `django_strawberry_framework/registry.py`

Status: verified

## DRY analysis

- Existing patterns reused: `TypeRegistry._check_mutable()` centralizes post-finalization mutation rejection for every guarded mutator in `django_strawberry_framework/registry.py:49-62`, and `TypeRegistry._already_registered()` centralizes duplicate-registration message construction for type and enum collisions in `django_strawberry_framework/registry.py:64-72`. The collection/finalization path uses this single registry boundary from `django_strawberry_framework/types/base.py:81-134`, `django_strawberry_framework/types/finalizer.py:58-85`, `django_strawberry_framework/types/converters.py:195-219`, and optimizer lookup sites such as `django_strawberry_framework/optimizer/extension.py:260-271`.
- New helpers a fix might justify: none. The file already has the useful shared helpers for mutation-state checks and duplicate-registration errors; the remaining API methods are direct dictionary/list operations with single call-site responsibilities.
- Duplication risk in the current file: none found in executable logic. The static helper reported no control-flow hotspots and no repeated string literals for `django_strawberry_framework/registry.py`; the repeated collision/mutability concerns are already centralized through `_already_registered()` and `_check_mutable()`.

## High:

None.

## Medium:

None.

## Low:

### Stale module docstring references the old converter location

The module docstring still says the registry is used by `converters.convert_relation` and `converters.convert_choices_to_enum`, but those functions now live under the `types` subpackage. That is harmless at runtime, but it sends future maintainers to a module path that no longer exists in the current package layout. Update the docstring to reference `types.converters.convert_relation` and `types.converters.convert_choices_to_enum`, or describe the call sites without the obsolete module prefix.

```django_strawberry_framework/registry.py:6:9
- ``converters.convert_relation`` for relation resolution once target
  types are registered.
- ``converters.convert_choices_to_enum`` for enum reuse across multiple
  ``DjangoType`` subclasses reading the same choice column.
```

### Class docstring no longer names the full mutation surface

`TypeRegistry` now guards more mutators than the docstring names. `register_definition`, `add_pending_relation`, and `discard_pending` all call `_check_mutable()`, while the class docstring only names `register`, `register_enum`, and `clear`. This is a small documentation drift that can hide the actual registry lifecycle contract during future finalization changes. Update the docstring to describe the full mutation boundary rather than listing an incomplete subset.

```django_strawberry_framework/registry.py:34:38
Mutations (``register``, ``register_enum``, ``clear``) are not guarded
by a lock.  This is safe because every production-path mutation runs
at import time from ``DjangoType.__init_subclass__`` (single-threaded
module loading); ``clear`` is test-only.  Do not call ``register`` or
``register_enum`` from a request handler or async resolver.
```

### `clear()` docstring points at a removed test module

The `clear()` docstring cites `tests/test_django_types.py`, but the current package test tree has registry isolation in `tests/test_registry.py` and type-specific isolation under `tests/types/`. Since this method is the main sanctioned reset path for tests, the docstring should either cite the current fixture location or avoid naming a specific test file.

```django_strawberry_framework/registry.py:246:249
Test-only — production code should never need to call this.
Wire into a ``pytest`` autouse fixture (see
``tests/test_django_types.py``) so each test starts with a clean
registry.
```

## What looks solid

- Static helper was run with `python scripts/review_inspect.py django_strawberry_framework/registry.py --output-dir docs/review/shadow --stdout`; it reported no control-flow hotspots, no calls of interest, and no repeated string literals.
- The registry's executable logic is small and cohesive: type mapping, reverse model lookup, definitions, pending relation records, enum caching, and lifecycle finalization state stay in one process-global boundary.
- Collision handling preserves existing mappings, and `register_with_definition()` rolls back the model/type pair if definition registration fails.
- Pending relation removal uses identity matching, which fits the finalizer's hand-back contract and avoids equality-based accidental deletion of equal-but-distinct pending records.

### Summary

No confirmed logic or DRY defects found in `registry.py`. The only findings are Low-severity docstring drift around moved converter paths, the now-broader mutation surface, and the stale test-file reference in `clear()`.

---

## Fix report (Worker 2)

### Files touched

- `django_strawberry_framework/registry.py` — updated stale docstrings called out in the Low findings: converter module paths now point at `types.converters`, the class docstring describes the full mutation boundary, and `clear()` no longer cites a removed test module.

### Tests added or updated

- None. The changes are docstring-only and do not alter runtime behavior.

### Validation run

- `uv run ruff format .` — passed, 92 files left unchanged.
- `uv run ruff check --fix .` — passed.

### Notes for Worker 3

- Static helper overview was generated under `docs/review/shadow/django_strawberry_framework__registry.overview.md`; original source line numbers in this artifact are canonical.
- No shadow view was used during implementation; only the Worker 1 overview and original source were consulted.

---

## Verification (Worker 3)

### Logic verification outcome

All Low findings are addressed by the docstring-only diff in `django_strawberry_framework/registry.py`.

- Stale converter references: addressed by changing the module docstring to `types.converters.convert_relation` and `types.converters.convert_choices_to_enum`.
- Incomplete mutation-surface docstring: addressed by describing the full mutating-method boundary rather than naming only a subset.
- Removed test module reference: addressed by replacing the old `tests/test_django_types.py` citation with generic pytest autouse fixture guidance.

There were no High or Medium findings, no executable logic changes, and no required tests.

### DRY findings disposition

Accepted. Worker 1 found no executable DRY defect, and Worker 2 did not add any new helper or duplicate flow. The existing `_check_mutable()` and `_already_registered()` centralization remains unchanged.

### Temp test verification

- Temp test files used: none.
- Disposition: not needed for docstring-only Low findings.

### Verification outcome

cycle accepted; verified

Focused validation rerun by Worker 3:

- `uv run ruff format --check django_strawberry_framework/registry.py` — passed.
- `uv run ruff check django_strawberry_framework/registry.py` — passed.

Comment/docstring pass accepted: the final source docstrings describe the current converter paths, mutation boundary, and test-isolation guidance without stale file references. Changelog disposition accepted: no `CHANGELOG.md` edit is warranted for internal docstring corrections, and `git diff -- CHANGELOG.md` is empty.

---

## Comment/docstring pass

Implemented in the same Worker 2 pass because every finding in the artifact was comment/docstring-only and there were no High or Medium logic findings awaiting a separate source-behavior fix. Updated:

- `django_strawberry_framework/registry.py:6-9` from obsolete `converters.*` references to current `types.converters.*` references.
- `django_strawberry_framework/registry.py:34-38` to describe all mutating methods rather than an incomplete list.
- `django_strawberry_framework/registry.py:246-248` to avoid the removed `tests/test_django_types.py` reference.

---

## Changelog disposition

Not warranted. The changes are internal docstring corrections only, with no user-visible behavior or public API change. `CHANGELOG.md` was not edited because the active instructions do not authorize a changelog edit for this item.

---

## Iteration log

No re-pass yet.
