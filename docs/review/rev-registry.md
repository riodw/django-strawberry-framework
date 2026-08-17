# Review: `django_strawberry_framework/registry.py`

Status: verified

## Understanding

`TypeRegistry` owns the process-local model/type index (`_types`, `_models`, and
`_primaries`), collected `DjangoTypeDefinition` objects, pending auto-synthesized relation
annotations, choice-enum reuse, finalization state, the schema-wide GlobalID setting snapshot,
and teardown callbacks. `registry` is the singleton used by the package; independent
`TypeRegistry` instances keep independent state.

`DjangoType.__init_subclass__` validates and collects a definition, then uses
`register_with_definition` to atomically add the model/type pair and definition. Duplicate
definitions and reverse type/model collisions fail with `ConfigurationError`; duplicate primary
declarations fail before a second type is appended. The rollback removes only state added by that
call and preserves an existing definition/primary when an idempotent re-registration fails.

`finalize_django_types()` first audits multi-type models for an explicit primary and resolves all
pending relations only after every declaration is registered. It then attaches relation/file
resolvers, applies Relay interfaces and GlobalID strategy snapshots, synthesizes relation
connections, binds filters/orders/mutations/auth declarations, and finally decorates each
`DjangoType`; the registry becomes immutable through the public mutators only after all phases
succeed. A failed phase leaves the finalized flag false for the documented retry path, while
`clear()` is the explicit test/reload reset.

Lookup callers use the registry consistently: relation finalization and mutation/auth binding use
`get()` for the primary (or the sole type), optimizer root planning carries the resolver's
origin type while nested relations intentionally use the primary, Relay model-label decoding
routes through the primary, and type-name decoding uses
`definition_for_graphql_name()` over finalized Relay definitions. Subsystem-owned generated-input,
connection, Relay, mutation, form, order/filter, serializer, and auth ledgers register their own
clear callbacks, preserving optional/lazy module boundaries.

The registry is process-local by design. Production mutations occur during single-threaded
module/schema setup and request-time mutation is rejected after finalization; concurrent finalized
reads are ordinary immutable dictionary reads. A worker/process receives its own module state, and
`clear()` is the supported test/reload boundary rather than a request operation.

## Verification

- The assigned scoped diff is empty:
  `git --no-pager diff 1541e4d86602f76f2aac00a8b2c90ca9639e8fcb -- django_strawberry_framework/registry.py`.
- `uv run pytest --no-cov tests/test_registry.py -q` — 80 passed.
- `uv run pytest --no-cov tests/types/test_definition_order.py
  tests/optimizer/test_definition_order.py tests/test_relay_node_field.py
  tests/mutations/test_inputs.py -q` — 137 passed.
- Real fakeshop HTTP callers:
  `uv run pytest --no-cov examples/fakeshop/test_query/test_products_api.py
  examples/fakeshop/test_query/test_library_api.py
  examples/fakeshop/test_query/test_auth_api.py -q` — 334 passed.
- Disposable probes in `docs/review/temp-tests/registry/test_isolation.py` verified that fresh
  registry instances do not share model/type state and that concurrent finalized reads preserve
  their registered lookups — 2 passed.
- Existing registry tests exercise duplicate/conflicting definitions, primary ambiguity,
  registration rollback, pending-relation identity removal, teardown retry/LIFO behavior,
  subsystem callback replacement, enum reuse/collision, finalization idempotency, Relay
  GraphQL-name lookup, and connection-cache eviction. The import-order and live tests above
  exercise those contracts through actual schema and HTTP paths.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

No reachable registry defect was confirmed. Model/type multiplicity and primary resolution are
explicit and fail closed, pending relations are import-order independent, registration rollback
and teardown lifecycles preserve their invariants, and Relay, optimizer, mutation, sidecar, and
lazy-lookup callers agree on the primary/origin split. The documented process-local and
single-threaded setup boundary is consistent with the implementation. This is a zero-edit source
cycle.

## Implementation (Worker 1)

None — zero-edit cycle.

- Production source and permanent tests are unchanged from the assigned baseline; no root-cause
  fix or test addition was justified.
- Created this fresh artifact and the disposable isolation probe under
  `docs/review/temp-tests/registry/`; the probe remains untracked per review conventions.
- Focused and live verification results are recorded above. No full test run was performed.
- Formatter/linter: no production edit required; the disposable probe was checked with targeted
  Ruff formatting/linting after creation.
- Rejected speculative change: adding a lock around registry mutators would alter the documented
  import-time-only lifecycle without a reachable production caller. Finalized request-time
  mutators already fail through `_check_mutable()`, and separate registry instances plus
  finalized concurrent reads were verified.
- Changelog: no entry requested; no behavior changed.

## Independent verification (Worker 2)

- Reconfirmed the assigned source scope is empty against baseline `1541e4d86602f76f2aac00a8b2c90ca9639e8fcb`; permanent registry tests are also unchanged.
- Re-read `registry.py` end to end and traced `DjangoType.__init_subclass__`, finalizer pending-relation phases and retry behavior, Relay model-label/type-name decoding, optimizer root-origin versus nested-primary planning, connection-cache eviction, mutation/auth primary binding, sidecar/filter/order lazy lookup, and subsystem callback teardown. Import-order cycles and circular relation graphs are covered by the focused definition-order suite.
- Reran `uv run pytest --no-cov tests/test_registry.py -q` — 80 passed; `uv run pytest --no-cov tests/types/test_definition_order.py tests/optimizer/test_definition_order.py tests/test_relay_node_field.py tests/mutations/test_inputs.py -q` — 137 passed; and the live fakeshop HTTP callers — 334 passed.
- Reran disposable `docs/review/temp-tests/registry/test_isolation.py` — 2 passed. Two separate `uv run python -c ...` interpreter probes each observed an empty singleton registry, confirming process isolation; finalized concurrent reads remained stable across worker threads.
- Tried to disprove the zero-edit result through duplicate/primary collisions, atomic definition rollback, pending identity cleanup, teardown retry/LIFO, lazy/unimportable subsystem paths, Relay GraphQL-name lookup, and connection-cache eviction; existing focused tests pass. The rejected lock candidate remains unjustified because production mutation is import-time/single-threaded, finalized mutators fail closed, and only immutable finalized reads are concurrent.
- No correctness, isolation, lifecycle, import-order, or caller-contract finding remains. Item 15 is complete with no source or permanent-test edit.

## Iterations

### Post-verification concurrent correction

- After Worker 2's verification, a concurrent maintenance edit corrected one module-docstring
  reference in `django_strawberry_framework/registry.py` from
  `types.finalizer.resolved_relation_annotation` to
  `types.converters.resolved_relation_annotation`.
- The scoped source diff remains documentation-only; no registry behavior, permanent test, or
  verification conclusion changed. The concurrent edit was preserved untouched.
