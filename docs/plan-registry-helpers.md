# Plan — registry public helpers for primary promotion + unregistration

Working doc for resolving feedback **L1** ([docs/feedback.md](feedback.md)). Not a spec, not a KANBAN card. The shipped change is recorded only in [`CHANGELOG.md`](../CHANGELOG.md) under `[Unreleased]`.

## Context

The Slice 4 multi-type tests (`tests/optimizer/test_walker.py:1566/:1614/:1666`, `tests/optimizer/test_extension.py:2999/:3047`) mutate `TypeRegistry._primaries`, `_types`, and `_models` directly. This extends a pre-existing pattern in the older `check_schema` tests around `tests/optimizer/test_extension.py:1810`. The coupling makes the registry's internal shape hard to refactor — any future rename of `_types` / `_primaries` / `_models` / `_definitions` silently breaks tests.

The reviewer marked this Low. Risk justifies acting now: the multi-type contract is new (build-014, 0.0.6), additional tests in 0.0.7+ will follow the same fixture pattern, and locking the private surface in test code makes the registry's internal-shape evolution more expensive each cycle.

## Design

### `TypeRegistry.set_primary(model, type_cls)`

Promote an already-registered type to primary for `model`.

- **Precondition.** `type_cls` must already be registered for `model`. Raises `ConfigurationError("X is not registered for Y")` otherwise.
- **Idempotent** when `type_cls` is already the primary for `model` — no-op return.
- **Raises** `ConfigurationError` when a *different* class is already the primary, with the same wording as `register(..., primary=True)`: `"X is already declared primary as Y"`. Single source of truth for the message.
- **Mutates** only `_primaries[model]`. Does not touch `_types` or `_models`.
- **Guards.** `_check_mutable()` first; post-finalize calls raise.

### `TypeRegistry.unregister(type_cls)`

Remove all traces of a type from the registry.

- **No-op** when `type_cls` is not registered (returns silently). Test teardown often wants "clean up if present" semantics; consumers needing strictness can layer a check on top.
- **Removes** `type_cls` from `_types[model]`; pops the `model` entry when the list empties.
- **Removes** `_models[type_cls]`.
- **Removes** `_primaries[model]` when `type_cls` was the primary. The model loses its primary even if siblings remain — caller is expected to re-promote a sibling via `set_primary(...)` if needed.
- **Removes** `_definitions[type_cls]`.
- **Removes** any pending relations whose `source_type` is `type_cls` (consistent with `discard_pending` semantics).
- **Guards.** `_check_mutable()` first; post-finalize calls raise.

## Implementation tasks

- [ ] Add `set_primary` and `unregister` to [django_strawberry_framework/registry.py](../django_strawberry_framework/registry.py). Reuse `_check_mutable()` and `_already_registered("primary as", ...)` (or extract a shared format for the duplicate-primary message — choose during implementation).
- [ ] Add focused unit tests in `tests/test_registry.py`:
  - `set_primary` happy path (registered type → becomes primary)
  - `set_primary` idempotent (same type already primary → no-op)
  - `set_primary` raises when type not registered for that model
  - `set_primary` raises when a different type is already primary
  - `set_primary` raises after `finalize_django_types()`
  - `unregister` removes from `_types`, `_models`, `_primaries`, `_definitions`
  - `unregister` removes pending relations sourced from the type
  - `unregister` keeps siblings intact (multi-type case)
  - `unregister` no-op on unknown type
  - `unregister` raises after `finalize_django_types()`
- [ ] Port the Slice 4 test sites to use the helpers:
  - `tests/optimizer/test_walker.py:1566`
  - `tests/optimizer/test_walker.py:1614`
  - `tests/optimizer/test_walker.py:1666`
  - `tests/optimizer/test_extension.py:2999`
  - `tests/optimizer/test_extension.py:3047`
- [ ] Port the pre-existing `check_schema` test sites that use `_types.pop` / `_models.pop` (around `tests/optimizer/test_extension.py:1810`).
- [ ] Confirm `git grep -nE "registry\._(types|primaries|models|definitions)" tests/` returns nothing after the port.

## CHANGELOG entry (draft, lands under `[Unreleased]` → `### Added`)

> - `TypeRegistry.set_primary(model, type_cls)` and `TypeRegistry.unregister(type_cls)` public helpers. The first promotes an already-registered type to the primary slot for its model (idempotent; raises on a different existing primary). The second removes all traces of a type from the registry (types list, model index, primary slot, definition, and pending relations sourced from the type). Test fixtures that previously poked private registry state now go through these helpers.

## Open questions

1. **Should `set_primary` auto-register an unregistered type?** Default plan: no — it's a *promote* operation, not a *register-and-promote*. Auto-register would make the method do two unrelated jobs. Confirm before implementation.
2. **Should `unregister` be strict (raise on unknown) instead of no-op?** Default plan: no-op (matches test-teardown need; mirrors `dict.pop(key, None)`). Confirm before implementation.
3. **Export from `django_strawberry_framework/__init__.py`?** Default plan: no. The registry singleton is already reachable as `django_strawberry_framework.registry`; keeping the top-level surface narrow matches policy. Internal-shaped helpers, not consumer-shaped.
4. **Do we also add `clear_primary(model)`?** Default plan: no, YAGNI. None of the test sites need it; add later if a real call site emerges.

## Acceptance

- Full `uv run pytest` sweep passes; 100% coverage gate holds.
- New helper tests added in `tests/test_registry.py`.
- `git grep -nE "registry\._(types|primaries|models|definitions)" tests/` returns nothing.
- `git grep -nE "registry\._(types|primaries|models|definitions)" django_strawberry_framework/` is limited to the registry module itself (the helpers' implementation).
- CHANGELOG entry lands under `[Unreleased]` → `### Added`.
- Lint / format / diff gate clean (`ruff format --check .`, `ruff check .`, `git diff --check`).
