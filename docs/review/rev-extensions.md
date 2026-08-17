# Review: `django_strawberry_framework/extensions/`

Status: verified

## Understanding

The extensions package exposes three distinct surfaces. `DjangoDebugExtension` is
opt-in and intentionally not root-exported because it publishes SQL parameters
and unmasked tracebacks. `DjangoErrorPolicyExtension` and
`DjangoResourcePolicyExtension` are root-exported and automatically installed by
`DjangoSchema`.

`DjangoSchema` resolves both immutable policy objects once, prepends the error
policy extension, and appends the resource policy extension unless the consumer
already supplied an instance/class of that family. The ordering matches the
lifecycle owners: resource policy must gate before execution, while error policy
must mask after execution and after diagnostic extensions have read original
exceptions. The debug extension's documented placement after masking preserves
that same teardown ordering.

The package-level boundaries agree with the surrounding system: resource context
is stashed/cleared around each operation, error masking is reused by WebSocket
per-event transport code, and debug capture remains an explicit diagnostic
surface rather than an accidental default.

## Verification

- Re-read `extensions/__init__.py` and all three modules as one component.
- Traced root exports through `django_strawberry_framework/__init__.py`, automatic
  schema installation through `schema.py`, and transport integration through
  `consumers.py`, `views.py`, and the fakeshop GraphQL mounts.
- Package validation before the integration fixes: 197 extension/error/resource
  tests passed; post-fix validation passed 203.
- Live validation before the integration fixes: 12 debug tests plus 53 combined
  error/resource tests passed; post-fix serial live validation passed 65 tests.
- All extension modules compiled; targeted Ruff checks passed.
- A final repository-wide `uv run ruff check --fix .` was also attempted; it
  reported six unrelated `F821` errors in `filters/sets.py`. The extension-scoped
  Ruff check remained clean, and no unrelated files were changed.
- No full repository test gate was run; it remains owned by the final review-plan
  item.

## Improvements

### High
- **Nested resource context could bypass the outer policy.** The resource
  extension now snapshots and restores policy/deadline values around nested
  operations; package regressions cover both sync and async execution.

### Medium

- **Callable error-policy factories were not suppressed at construction.**
  Runtime resolution now removes only the automatic duplicate while preserving
  consumer factory order and lifecycle.

### Low

None.

## Summary

Public exports, automatic installation, extension ordering, policy context
lifecycle, streamed masking, resource enforcement, and debug disclosure controls
are coherent across the package. The debug exact-boolean gate, callable policy
suppression, and nested resource-context restoration were fixed at their owning
boundaries; no additional folder-level finding remains.

## Implementation (Worker 1)

- Integrated the module-level debug gate fix and its regression test into the
  package review result.
- Integrated callable error-policy suppression and nested resource-context
  restoration, with package regressions for both.
- Preserved all unrelated concurrent source/test changes.
- No changelog entry was requested.

## Independent verification (Worker 2)

- Confirmed policy extension ordering does not introduce duplicate masking or
  duplicate resource charging when consumer entries are supplied.
- Re-ran package/live validation and compile/Ruff checks; no further integrated
  finding remains.
