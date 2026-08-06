# DRY review: `django_strawberry_framework/schema.py`

Status: verified

## System trace

The target owns the GraphQL execution seam that makes generated mutations
safe under response completion, and the `DjangoSchema` construction seam that
installs that context plus the two default deployment policies.

Symbols:

- `DjangoMutationExecutionContext` — graphql-core `ExecutionContext` subclass.
  For each TOP-LEVEL field whose resolver carries
  `mutations/fields.py::MUTATION_CLASS_MARKER`, opens
  `transaction.atomic(using=<write alias>)` before resolve and exits it only
  after graphql-core finishes completing that field's value; publishes the
  managed alias via `utils/write_transaction.py::managed_write_transaction`;
  marks rollback when the execution's error list grew during the window.
- `DjangoMutationExecutionContext.execute_field` — gate + sync/async dispatch
  (`strawberry.utils.inspect.in_async_context`).
- `DjangoMutationExecutionContext._marked_mutation_class` — mutation-root +
  marker recognition (nested payload fields and unmarked consumer mutations
  pass through unwrapped).
- `DjangoMutationExecutionContext._execution_errors` — graphql-core
  `<3.2.9` / `>=3.2.9` error-list shape bridge.
- `DjangoMutationExecutionContext._execute_mutation_field_sync` — calling-thread
  enter/exit around `super().execute_field` (completion is synchronous).
- `DjangoMutationExecutionContext._execute_mutation_field_async` — open/close
  the atomic inside `utils/querysets.py::run_in_one_sync_boundary` workers so
  ORM work and the connection share one `thread_sensitive` thread across the
  completion `await`.
- `DjangoSchema` — `strawberry.Schema` subclass; default
  `execution_context_class=DjangoMutationExecutionContext`; resolves
  `resource_policy` / `error_policy` once at construction; installs the matching
  extensions unless the consumer already supplied one.
- `_with_resource_policy_extension` — append `DjangoResourcePolicyExtension`
  class if absent (per-request instance / charge counters).
- `_with_error_policy_extension` — PREPEND `DjangoErrorPolicyExtension` if
  absent (LIFO teardown: masking last; load-bearing vs debug extension).

Connected ownership (traced, not re-owned here):

- `utils/write_transaction.py` — managed-alias ContextVar, `require_managed_write`
  gate, alias pin / pipeline phase / row-lock helpers. Schema is the only
  production publisher of `managed_write_transaction`; the pipeline is the
  consumer.
- `mutations/fields.py` — stamps `MUTATION_CLASS_MARKER` on the synthesized
  `_resolve`; schema is the sole reader for transaction wrapping.
- `mutations/resolvers.py` / `forms/resolvers.py` / serializer path — open an
  INNER `transaction.atomic` + `write_pipeline` after `require_managed_write`,
  and `set_rollback` on in-band `FieldError` envelopes. Nested savepoint under
  the schema outer window (see Verification).
- `utils/querysets.py::run_in_one_sync_boundary` — shared one-worker async
  bridge; schema uses it only for atomic enter/exit on the async path.
- `error_policy.py` / `resource_policy.py` — resolve + validate policy objects;
  schema only calls them and installs the enforcers.
- `management/commands/export_schema.py` — SDL export; accepts any
  `strawberry.Schema` (including `DjangoSchema`). No transaction / execution-
  context overlap.
- `auth/mutations.py` — rides `DjangoMutationField` + write pipeline / session
  sync boundary; does not open a completion-spanning transaction of its own.
- `examples/fakeshop/config/schema.py` — consumer `DjangoSchema(...)` wiring.
- Proof tiers: live HTTP
  `examples/fakeshop/test_query/test_mutation_atomicity.py`; package async +
  refusal + error-shape + unmarked-field coverage in
  `tests/mutations/test_write_transaction.py`; policy install in
  `tests/test_error_policy.py` / resource-policy tests.

Item-scoped baseline
`git diff c80ca6f43ccf073ac722199c4aa3abf8c6597a00 -- django_strawberry_framework/schema.py`
is empty. No production edits for this item.

## Verification

Searched package-wide for `DjangoSchema`, `DjangoMutationExecutionContext`,
`managed_write_transaction`, `require_managed_write`, `MUTATION_CLASS_MARKER`,
`execution_context_class`, `transaction.atomic`, `set_rollback`,
`run_in_one_sync_boundary`, `_with_resource_policy_extension`,
`_with_error_policy_extension`, `resolve_write_alias`, and `execute_field`.

Compared contracts:

1. **Outer (schema) vs inner (pipeline) `transaction.atomic`.** Outer spans
   resolve + GraphQL *completion* and is the only layer that sees
   completion-raised located errors. Inner wraps the write pipeline so an
   in-band `FieldError` envelope can `set_rollback` without becoming a
   graphql-core execution error (soft validation / conflict paths). Nested
   savepoint semantics: inner release leaves the write in the still-open outer
   transaction; a later completion failure still rolls the write back. Same
   mechanism, different contracts and change axes — not one responsibility
   duplicated.

2. **Sync vs async execution-context paths.** Shared steps (alias resolve,
   managed publish, error-count rollback, manual atomic enter/exit) diverge on
   thread ownership: sync holds the atomic on the calling thread; async must
   enter/exit via `run_in_one_sync_boundary` and `await` an awaitable result.
   A unified helper would need a mode flag or dual closures that obscure the
   asgiref connection invariant. Kept separate.

3. **Extension install twins (append vs prepend).** Detection loop is similar;
   insert position is the contract (resource setup last / error masking last on
   LIFO teardown). Collapsing into one parameterized helper would hide the
   load-bearing position difference for a few lines of loop. Rejected.

4. **`resolve_write_alias` call site.** Schema resolves once from
   `_mutation_meta.model` (None → `DEFAULT_DB_ALIAS` for model-less forms) and
   publishes; pipeline reads via `require_managed_write` and never re-resolves
   for the outer window. No second owner of "which alias the completion
   transaction uses."

5. **Marker detection.** Only `mutations/fields.py` stamps;
   only `DjangoMutationExecutionContext` reads for wrapping. Auth / form /
   serializer mutations share the stamp through `DjangoMutationField`.

6. **`export_schema`.** Instantiates nothing about transactions or policies;
   `isinstance(..., Schema)` accepts `DjangoSchema` by inheritance. Sibling
   item; no duplication with this file.

7. **`run_in_one_sync_boundary` reuse.** Shared neutral primitive across
   filters / orders / permissions / auth / mutation pipelines; schema's use
   for atomic enter/exit is a legitimate consumer, not a parallel bridge.

Strongest rejected candidates: (1) merge outer+inner atomics, (2) unify
sync/async field executors, (3) parameterize the two extension installers.

## Opportunities

None — ownership boundaries hold under present-day source. The completion-
spanning transaction, managed-alias publish, mutation-field gating, and
default policy/extension install each have a single authoritative site in
this module or a clearly separated neighbor (`write_transaction`, policy
modules, `mutations/fields`). Apparent structural twins (nested atomics,
sync/async paths, append/prepend extension helpers) encode distinct contracts
that should not change together.

## Judgment

Zero-edit. `schema.py` is the correct owner of mutation-atomicity execution
context and of `DjangoSchema` construction-time policy/extension wiring.
Connected write-pipeline atomics and soft-error rollback stay in the mutation
resolvers; the managed-alias ContextVar and refuse-to-write gate stay in
`utils/write_transaction.py`. Ready for Worker 2.

Deferred pytest: none required (no production or permanent-test edits).
Existing coverage at live + package tiers already pins the contracts traced
above; maintainer has not authorized a pytest run for this item.

## Independent verification (Worker 2)

Re-traced against present-day source; scoped production diff vs
`c80ca6f43ccf073ac722199c4aa3abf8c6597a00` is empty (303/303 lines).

**Ownership (confirmed):**

- Sole production publisher of `managed_write_transaction`: only
  `schema.py::_execute_mutation_field_sync` / `_async` enter it; package
  tests wrap direct pipeline calls. `require_managed_write` /
  `_MANAGED_WRITE_ALIAS` stay in `utils/write_transaction.py`.
- Marker: only `mutations/fields.py` stamps `MUTATION_CLASS_MARKER` on
  synthesized `_resolve`; only `DjangoMutationExecutionContext._marked_mutation_class`
  reads it for wrapping. Nested payload fields fail the mutation-root gate.
- Outer atomic: schema opens `transaction.atomic(using=alias)` around
  `super().execute_field` (+ await on async) and `set_rollback` when
  `_execution_errors()` grew. Inner atomic: `run_write_pipeline_sync`,
  delete branch, plain-form path (and serializer via shared skeleton) open
  nested `transaction.atomic` after `require_managed_write`, with
  `set_rollback` on in-band `FieldError` envelopes.
- `resolve_write_alias` once at schema from `_mutation_meta.model`; pipeline
  never re-resolves for the outer window.
- `DjangoSchema` resolves policies via `resolve_*_policy`, default
  `execution_context_class`, append resource / prepend error extensions.
- `export_schema` is SDL-only (`isinstance(..., strawberry.Schema)`); no
  transaction/policy overlap. Auth mutations ride `DjangoMutationField` +
  pipeline; no second completion-spanning atomic.

**Rejected candidates challenged:**

1. **Merge outer+inner atomics — reject stands.** Outer must see
   completion-located errors; inner must roll back soft envelopes that are
   not graphql-core execution errors. Nested savepoint: inner release leaves
   the write in the outer window so a later completion failure still rolls
   back. Different contracts / change axes.
2. **Unify sync/async field executors — reject stands.** Sync enters/exits
   atomic on the calling thread; async must `__enter__`/`__exit__` via
   `run_in_one_sync_boundary` and `await` awaitable results so ORM + connection
   share one `thread_sensitive` thread. A mode-flag helper would obscure that
   invariant.
3. **Parameterize extension installers — reject stands.** Detection loops
   look alike; insert position is the contract (resource append / error
   prepend for LIFO teardown). Collapsing hides a load-bearing difference.

**Missed consolidations searched:** package-wide
`managed_write_transaction`, `require_managed_write`, `MUTATION_CLASS_MARKER`,
`execution_context_class`, `transaction.atomic` in mutation/form/serializer
resolvers, policy installers, `run_in_one_sync_boundary` consumers. No second
owner of completion-spanning atomicity or managed-alias publish; no bypass
of the marker gate for generated fields. Zero-edit stands.
