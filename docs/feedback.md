# Review feedback — local diff

Scope: reviewed the current uncommitted local diff, including `django_strawberry_framework/registry.py`, the related optimizer/type/registry tests, `CHANGELOG.md`, and the untracked `docs/plan-registry-helpers.md`.

## Findings

### H1. `unregister()` breaks the finalized-registry invariant

References: [django_strawberry_framework/registry.py:177](../django_strawberry_framework/registry.py:177), [django_strawberry_framework/registry.py:187](../django_strawberry_framework/registry.py:187), [tests/test_registry.py:1297](../tests/test_registry.py:1297), [tests/optimizer/test_extension.py:1807](../tests/optimizer/test_extension.py:1807).

`TypeRegistry.unregister()` is documented as a public mutator and intentionally skips `_check_mutable()`, including after `finalize_django_types()` has run. That leaves `registry.is_finalized()` as `True` while removing entries from `_types`, `_models`, `_primaries`, and `_definitions`. The finalized registry is still the runtime lookup source for optimizer planning, schema audit, relation target lookup, and reverse type/model lookup, so this can silently disable planning or produce false missing-target warnings for types that still exist in the already-built Strawberry schema.

The current tests pin this as desired behavior because they need to simulate a missing registration after finalization, but that is a test fixture need, not a safe public API contract. Either make `unregister()` obey `_check_mutable()` like the other registry mutators and keep the post-finalize corruption in a test-local helper, or explicitly design a real late-unregistration story that invalidates/rebuilds the finalized snapshot.

### H2. `set_primary()` adds a public API that spec-014 explicitly excludes

References: [django_strawberry_framework/registry.py:137](../django_strawberry_framework/registry.py:137), [docs/spec-014-meta_primary-0_0_6.md:303](spec-014-meta_primary-0_0_6.md:303), [CHANGELOG.md:26](../CHANGELOG.md:26).

Spec-014 says `Meta.primary` is a per-class declaration and explicitly lists `set_primary(model, type)` as a non-goal. The local diff adds `TypeRegistry.set_primary(model, type_cls)` as a public helper for "consumer code" and documents it in the changelog. That changes the API contract from declaration-time primary selection to post-registration promotion.

This also creates two sources of truth: `DjangoTypeDefinition.primary` remains whatever the class declared, while `registry._primaries` can be changed later by `set_primary()`. Today most code reads `registry.primary_for()`, but the definition field exists and tests already assert it, so this is an avoidable inconsistency.

If the goal is only to remove direct private-map pokes from tests, update the synthetic test helper to call `registry.register(model, type_cls, primary=True)` instead of adding a public mutator. If this is intentionally new public surface, the spec, KANBAN design notes, and changelog need to be updated together, and the implementation should keep `DjangoTypeDefinition.primary` coherent.

## Verification

- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed.
- `git diff --check` passed.
- `uv run pytest` passed: 693 passed, 3 skipped, 100.00% package coverage.
