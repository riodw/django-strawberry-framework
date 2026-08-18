# Review: `django_strawberry_framework/mutations/`

Status: verified

## Understanding

The six-module write subsystem separates declaration/bind (`sets.py`), generated
types and namespace lifecycle (`inputs.py`), field construction (`fields.py`),
authorization (`permissions.py`), and runtime model pipelines (`resolvers.py`),
with the package marker re-exporting the four stable mutation symbols. Forms and
serializers ride the shared model-backed skeleton where their contracts match;
plain forms keep a model-less ledger and `{ok, errors}` payload. Auth fixed
fields and register reuse mutation helpers without becoming generated mutation
fields. `DjangoSchema` owns the outer completion-spanning transaction, while
`write_transaction.py` owns alias/phase guards and nested pipeline state.

## Verification

Re-read all five target modules as an integrated component and traced boundaries
through forms, DRF serializer inputs/resolvers, auth mutations, schema execution,
registry/finalizer phase 2.5, optimizer mutation selection, write transaction and
write-value utilities, package exports, and fakeshop product schemas/tests.
Focused package validation: `uv run pytest --no-cov tests/mutations` — 290
passed. Live HTTP fakeshop model/form/serializer/plain-form mutation validation,
authorization, relation errors, uploads, optimizer re-fetch, and transaction
coverage: 57 passed with the focused product mutation selection.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

The integrated mutation subsystem has no unresolved folder-owned correctness
finding. The NodeID alias defect discovered by independent verification is
fixed and covered by package and live sharded regressions. Shared transaction/auth/async policy is already centralized; the
remaining plain-form/delete orchestration differences are deliberate payload and
lifecycle contracts and should not be forced into mode-flagged code in this
review.

## Implementation (Worker 1)

Revision implemented after independent verification found a sharded integration
gap in custom `relay.NodeID[...]` mutation lookup. `decode_model_global_id` now
honors the active/passed write alias, and the top-level mutation resolver passes
that alias explicitly before locate/authorization while the relation riders rely
on the active-pipeline recovery inside `relay.py::_resolve_real_pk`. (The
explicit pass was added in the coordinator follow-up recorded in
`rev-mutations__resolvers.md`; before it, this seam relied on a duplicate
recovery of the same context variable.) The folder remains otherwise unchanged;
status is `fix-implemented` after the revision.

## Independent verification (Worker 2)

Status: revision-needed

Focused integration evidence:

- `uv run pytest --no-cov tests/mutations` — 290 passed.
- `uv run pytest --no-cov tests/forms tests/rest_framework` — 595 passed.
- `uv run pytest --no-cov tests/auth/test_mutations.py` — 93 passed.
- `uv run pytest --no-cov examples/fakeshop/test_query/test_products_api.py` —
  118 passed.
- `uv run pytest --no-cov examples/fakeshop/test_query/test_mutation_atomicity.py` —
  6 passed.
- `uv run pytest --no-cov examples/fakeshop/test_query/test_uploads_api.py` —
  9 passed.

One integration defect remains: custom non-pk Relay `NodeID` mutation lookup
does not honor the write alias. The disposable sharded probe
`docs/review/temp-tests/mutations/test_custom_nodeid_alias_probe.py`, run as
`FAKESHOP_SHARDED=1 PYTHONPATH=examples/fakeshop uv run pytest --no-cov docs/review/temp-tests/mutations/test_custom_nodeid_alias_probe.py`,
gets `FieldError(field="id", messages=["No matching row found."])` for a row
present only on `shard_b` while reads route to `default` and writes to
`shard_b`. `relay.py::_resolve_real_pk` uses the default manager before
`mutations/resolvers.py::run_write_pipeline_sync` enters the alias guard.

This is a High resolver/integration finding, fully detailed in
`rev-mutations__resolvers.md`. The folder remains `revision-needed` until
NodeID-to-PK resolution is performed on the pinned write alias and a permanent
sharded live regression proves the fix.

## Iterations

### Revision 2026-08-17 — write-alias NodeID lookup

The source of truth was `relay.py::_resolve_real_pk`: its non-pk NodeID lookup
used the default manager even though `run_write_pipeline_sync` had already
opened and pinned a different write alias. The fix is owned at that decode
boundary, with explicit propagation for top-level ids and active-pipeline
fallback for relation riders. Added package and live sharded regression
coverage; unrelated sharding and review work remains untouched. The folder is
ready for Worker 2 re-verification.

### Worker 2 re-verification

Status: verified

The exact disposable shard probe and the permanent live sharded custom-NodeID
regression both pass after the alias-aware decode fix:

- `FAKESHOP_SHARDED=1 PYTHONPATH=examples/fakeshop uv run pytest --no-cov docs/review/temp-tests/mutations/test_custom_nodeid_alias_probe.py`
  — 1 passed.
- `FAKESHOP_SHARDED=1 uv run pytest --no-cov examples/fakeshop/test_query/test_multi_db.py -k custom_nodeid`
  — 1 passed.
- `uv run pytest --no-cov tests/mutations` — 291 passed.
- `uv run pytest --no-cov tests/forms tests/rest_framework` — 595 passed.
- `uv run pytest --no-cov tests/auth/test_mutations.py` — 93 passed.
- `uv run pytest --no-cov examples/fakeshop/test_query/test_products_api.py -k 'mutation or form or serializer or g2'`
  — 42 passed.
- `uv run pytest --no-cov examples/fakeshop/test_query/test_mutation_atomicity.py examples/fakeshop/test_query/test_uploads_api.py examples/fakeshop/test_query/test_optimizer_auto_api.py -k 'mutation or upload or optimizer or g2'`
  — 16 passed.

The folder integration is verified; no mutation-owned revision remains.
