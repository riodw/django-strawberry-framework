# Review: `django_strawberry_framework/mutations/resolvers.py`

Status: verified

## Understanding

The resolver module owns the model write pipeline and the shared model-backed
create/update skeleton used by ModelForm and serializer riders. It enforces the
managed `DjangoSchema` transaction, alias pinning, locate-before-authorize and
authorize-before-decode ordering, relation visibility, scalar/null decoding,
validation envelopes, forced-update conflict handling, optimizer re-fetch, and
delete snapshot-before-delete semantics. Async resolution runs the synchronous
pipeline in one thread-sensitive boundary.

## Verification

Read the complete orchestration, model decode/write, delete, authorization,
payload, async, and conflict paths. Traced form and DRF callbacks, auth register,
`utils/write_transaction.py`, `utils/write_values.py`, optimizer mutation
selection, and schema response-completion transactions. Package validation:
`uv run pytest --no-cov tests/mutations` — 290 passed. Live fakeshop HTTP
validation/authorization/Upload/optimizer mutation coverage passed 57 tests; the
dedicated `test_mutation_atomicity.py` suite was also inspected as the proof of
completion-spanning rollback.

## Improvements

### High

None.

### Medium

None.

### Low

None.


## Summary

The model-backed skeleton and its flavor callbacks have distinct ownership while
sharing the transaction, authorization, alias, payload, and async boundaries.
Delete and plain-form orchestration intentionally remain separate until their
model-less/tail seams are co-designed outside this pass. The independent
NodeID alias finding is fixed by the revision recorded below.

## Implementation (Worker 1)

Revision implemented after independent verification found that custom
`relay.NodeID[...]` payloads were mapped to real primary keys through
`model._default_manager` without the mutation's pinned write alias. The fix adds
an optional alias to `relay.py::decode_model_global_id`, recovers the active
pipeline alias for relation riders, and threads the explicit alias from
`run_write_pipeline_sync` through `coerce_lookup_id`. A package regression test
asserts the manager is routed to the supplied alias. `uv run ruff format .` and
`uv run ruff check --fix .` passed after the source/test edits. No changelog
entry is warranted.

## Independent verification (Worker 2)

Status: revision-needed

The normal model/form/serializer/auth pipelines and their adversarial package
coverage are broadly green:

- `uv run pytest --no-cov tests/mutations` — 290 passed.
- `uv run pytest --no-cov tests/forms tests/rest_framework` — 595 passed.
- `uv run pytest --no-cov tests/auth/test_mutations.py` — 93 passed.
- `uv run pytest --no-cov examples/fakeshop/test_query/test_products_api.py` —
  118 passed.
- `uv run pytest --no-cov examples/fakeshop/test_query/test_mutation_atomicity.py` —
  6 passed.
- `uv run pytest --no-cov examples/fakeshop/test_query/test_uploads_api.py` —
  9 passed.

### High

**Observation:** A valid custom Relay `NodeID` update can be reported as
not-found on a divergent read/write router.

**Evidence:** The disposable probe
`docs/review/temp-tests/mutations/test_custom_nodeid_alias_probe.py` was run
with:
`FAKESHOP_SHARDED=1 PYTHONPATH=examples/fakeshop uv run pytest --no-cov docs/review/temp-tests/mutations/test_custom_nodeid_alias_probe.py`.
It declares `CategoryNode.name: relay.NodeID[str]`, stores the target only on
`shard_b`, and routes product reads to `default` and writes to `shard_b`.
`global_id_for(CategoryNode, "write-shard-target")` then returns the in-band
`FieldError(field="id", messages=["No matching row found."])` instead of updating
the existing write-shard row.

The call chain is
`mutations/resolvers.py::coerce_lookup_id` →
`relay.py::decode_model_global_id` →
`relay.py::_resolve_real_pk`. The latter resolves a non-pk NodeID through
`model._default_manager.filter(...).values_list("pk", flat=True).first()`.
`run_write_pipeline_sync` performs this coercion before
`locate_instance` and before `pipeline_alias_guard`; the lookup therefore uses
the router's read/default alias, not the already-resolved write alias from
`utils/write_transaction.py::resolve_write_alias`.

**Impact:** Valid writes on sharded/read-replica deployments fail closed as
not-found; if same-pk rows differ between aliases, NodeID resolution can also
select the wrong row before visibility and authorization run. This violates the
one-alias transaction contract and custom-NodeID mutation parity with default-pk
IDs.

**Recommendation:** Make the NodeID-to-real-PK resolution alias-aware and perform
it on the mutation's pinned write alias inside the managed pipeline before
visibility lookup. Thread the alias through the decode primitive (or provide an
alias-pinned resolver owned by the write transaction layer); do not rely on the
default manager or defer pinning until after coercion.

**Proof:** Add a permanent sharded live mutation test with a non-pk
`relay.NodeID` target whose row exists only on the write alias, asserting the
update succeeds and the read-alias twin is untouched. Re-run the existing
default-pk and custom-NodeID update/delete tests to preserve both paths.

### Medium

None.

### Low

None.

## Iterations

### Revision 2026-08-17 — pinned NodeID lookup alias

Worker 2 reproduced the defect under `FAKESHOP_SHARDED=1`: a valid custom
NodeID update row present only on `shard_b` returned
`FieldError(field="id", messages=["No matching row found."])` because
`_resolve_real_pk` queried the default manager before the pipeline alias was
applied. The root fix keeps `decode_model_global_id` usable outside mutations,
but when a write pipeline is active its non-pk NodeID lookup uses the pinned
alias; top-level mutation lookup passes that alias explicitly. Permanent proof:
`tests/mutations/test_resolvers.py::test_custom_node_id_real_pk_lookup_uses_pinned_alias`.
Permanent live proof now also runs:
`FAKESHOP_SHARDED=1 uv run pytest --no-cov examples/fakeshop/test_query/test_multi_db.py -k custom_nodeid`
— 1 passed. The package mutation suite remains green at 291 passed.

### Worker 2 re-verification

Status: verified

The corrected alias propagation was independently inspected and exercised. The
active write-pipeline alias is threaded from
`mutations/resolvers.py::coerce_lookup_id` through
`relay.py::decode_model_global_id` to `relay.py::_resolve_real_pk`, whose
manager uses `.using(using)` before resolving the real primary key. Evidence:

- `FAKESHOP_SHARDED=1 PYTHONPATH=examples/fakeshop uv run pytest --no-cov docs/review/temp-tests/mutations/test_custom_nodeid_alias_probe.py`
  — 1 passed (the exact pre-fix failure now succeeds).
- `FAKESHOP_SHARDED=1 uv run pytest --no-cov examples/fakeshop/test_query/test_multi_db.py -k custom_nodeid`
  — 1 passed (permanent live regression).
- `uv run pytest --no-cov tests/mutations` — 291 passed.
- `uv run pytest --no-cov tests/forms tests/rest_framework` — 595 passed.
- `uv run pytest --no-cov tests/auth/test_mutations.py` — 93 passed.
- `uv run pytest --no-cov examples/fakeshop/test_query/test_products_api.py -k 'mutation or form or serializer or g2'`
  — 42 passed.
- `uv run pytest --no-cov examples/fakeshop/test_query/test_mutation_atomicity.py examples/fakeshop/test_query/test_uploads_api.py examples/fakeshop/test_query/test_optimizer_auto_api.py -k 'mutation or upload or optimizer or g2'`
  — 16 passed.
- `uv run pytest --no-cov tests/testing/test_relay.py tests/utils/test_write_values.py`
  — 21 passed.
- `git diff --check -- django_strawberry_framework/relay.py django_strawberry_framework/mutations/resolvers.py tests/mutations/test_resolvers.py examples/fakeshop/test_query/test_multi_db.py`
  — clean.

Default-pk, custom-NodeID, malformed/wrong-model, hidden-row, relation,
authorization, transaction, conflict, form/serializer, async, upload, and
optimizer paths remain green. No resolver-owned finding remains.

### Coordinator review of the revision — the recorded mechanism did not match the code

- **Observation:** This artifact and `rev-mutations.md` both stated that the top-level mutation
  resolver passes the pinned alias explicitly. It did not: `mutations/resolvers.py` called
  `coerce_lookup_id(id, primary_type)` with no alias from inside
  `with open_write_pipeline(mutation_cls) as using:`, where the alias was already bound. The fix
  worked only through `coerce_lookup_id`'s own context-variable recovery.
- **Impact:** Low, and correctness was never affected - the recovered alias is read from the same
  `current_write_pipeline()` context variable that `relay.py::_resolve_real_pk` already consults, so
  the two reads could never disagree. The cost was a duplicated recovery block at a seam that holds
  the answer in scope, and a record that described a mechanism the source did not implement.
- **Root-cause fix:** The call site now threads `using=using`, and `coerce_lookup_id`'s recovery
  block is deleted. `_resolve_real_pk` keeps its recovery, which is load-bearing for the relation
  riders in `utils/write_values.py` that cannot thread an alias through the flavor handlers. The
  docstring records why the alias is threaded at this seam rather than recovered.
- **Permanent proof:** `test_custom_node_id_real_pk_lookup_uses_pinned_alias` continues to pin the
  explicit-alias path, and the live sharded regression continues to pin the recovered-alias path.
  Five pipeline-harness doubles in `tests/mutations/test_resolvers.py` had pinned the old
  two-argument signature and were failing loudly on the threaded keyword; the shared harness double
  now absorbs it with `**_kwargs` so the harness keeps asserting drift handling rather than alias
  propagation.

Validation: `uv run pytest --no-cov tests/optimizer tests/mutations` — 1075 passed;
`uv run pytest --no-cov tests/forms tests/rest_framework tests/auth/test_mutations.py tests/test_relay_node_field.py tests/utils/test_write_values.py tests/testing/test_relay.py`
— 756 passed;
`FAKESHOP_SHARDED=1 uv run pytest --no-cov examples/fakeshop/test_query/test_multi_db.py` — 10
passed.
