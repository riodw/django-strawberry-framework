# Review: `django_strawberry_framework/utils/write_transaction.py`

Status: fix-implemented

## Understanding

Owns managed completion-spanning write transactions, router alias resolution/pinning, row locks, read/write phases, divergent-auth barriers, cross-alias SQL/save guards, target-state snapshots, canonical pk comparison, and conflict mapping.

## Verification

Traced model/form/serializer/auth write pipelines through locate, visibility, relation checks, authorization, validation, save/delete, refetch, rollback, and response completion. Challenged reused ContextVars, divergent routers, nested authorization barriers, SQLite/PostgreSQL read-only behavior, pk drift, mutable JSON/file values, deferred fields, and forced-update conflicts. Mutation write-transaction and form/DRF suites passed.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

The write substrate keeps all ordinary pipeline work on one managed alias and preserves atomicity, lock, drift, and conflict contracts across flavors.
## Iterations

An additional phase-boundary pass found that `django_strawberry_framework/utils/write_transaction.py::_sql_statement_token` retained a `str` subclass while lexically inspecting it. An overridden indexing/slicing method could present `SELECT` to the read-only phase classifier while the database adapter retained the base `DELETE` text. The classifier now normalizes through `str.__str__` before any string operation. `tests/mutations/test_write_transaction.py::test_is_read_only_sql_uses_base_string_content_for_subclasses` pins the boundary; all mutation transaction tests and the 2,220-test integrated caller run passed.

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
