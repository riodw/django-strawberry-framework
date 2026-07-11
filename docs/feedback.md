# Spec-044 deep architectural review

## Scope and verdict

Reviewed `docs/spec-044-debug_extension-0_0_14.md` against the current
package, the staged TODO anchors, the installed Strawberry 0.316.0, Django
6.0.5 and asgiref 3.11.1 sources, the fakeshop acceptance fixtures, and the
CI/generated-document workflows.

**Verdict: the core design is directionally sound, but production work should
not start from Revision 7 unchanged.** The public placement, class-form opt-in,
per-operation stash, saved-value coordinator, response-extension merge model,
masking order, and deliberate sync-first SQL scope all fit the repository.
However, five issues are implementation blockers:

1. the optimizer acceptance scenario asserts a query shape the existing
   visibility architecture deliberately prevents;
2. the required Strawberry floor is a release-wide compatibility change, so
   the spec's off-by-default/byte-identical claims are false;
3. a diagnostic serialization failure can currently replace the real GraphQL
   result;
4. `force_debug_cursor` brackets cursor creation, not the lifetime of every
   cursor execution, so the claimed SQL interval is too broad; and
5. the Slice-3 term-import/render order would leave generated KANBAN output
   stale.

The remaining findings require explicit constraints and test/doc amendments,
not a redesign of the extension.

## 1. Inconsistencies and contradictions

### F1 — P0: optimizer scenario 2 requires an impossible joined-query shape

Spec locations: Goals item 5, Test plan scenario 2, the live-test TODO anchor,
and the coverage ownership text.

The spec says the nested `allItems { ... category { name } }` selection should
produce a joined single query. That contradicts the package's visibility
contract:

- `examples/fakeshop/apps/products/schema.py::CategoryType.get_queryset`
  defines a custom visibility hook.
- The optimizer intentionally converts a forward FK whose target has a custom
  `get_queryset` into a `Prefetch`, rather than `select_related`, so target
  visibility is not bypassed.
- The existing live proof
  `examples/fakeshop/test_query/test_products_api.py::test_products_optimizer_merges_duplicate_root_field_nodes_over_http`
  pins the correct result: one `products_item` slice plus one
  `products_category` prefetch, with no inter-products JOIN and no N+1.

Required correction:

- Rewrite Goals item 5 and scenario 2 to assert the established two-query
  shape: exactly one item slice and one category prefetch after filtering to
  SELECT rows; assert no item/category JOIN and no per-item category queries.
- Reuse the semantic assertions from the existing acceptance test rather than
  inventing a conflicting optimizer expectation.
- Update `examples/fakeshop/test_query/test_debug_extension_api.py`'s anchor
  from “joined single-query shape” to the visibility-safe prefetch shape.

If a one-query JOIN is essential to the demonstration, choose a relation whose
target has no custom visibility hook. The current `ItemType.category` relation
cannot honestly prove that shape.

### F2 — P0: “off by default / byte-identical / nothing else changes” conflicts with the mandatory dependency floor

Spec locations: Goals item 3, User-facing API's “Nothing else changes,”
Decision 6, Decision 12, the off-by-default DoD row, and the engine-ordering
risk.

The debug class is off by default, but Slice 1 globally raises
`strawberry-graphql>=0.262.0` to `>=0.316.0`. That changes engine behavior even
for schemas that never import `DjangoDebugExtension`:

- pre-0.316 sync execution cached extension instances;
- 0.316 constructs class/factory entries per operation;
- 0.316 invokes factories/classes with zero arguments, rebuilds the middleware
  manager per operation, and warns for direct instance entries.

A consumer factory that relied on the old `execution_context=` call shape can
fail after the upgrade. Direct instance users also see a lifecycle/deprecation
change. The floor is justified—the old lifecycle is unsafe for the new
extension—but it is not a debug-only no-op and should not be described as a
byte-identical patch when the extension is absent.

Required correction:

- Replace “response bytes/behavior are identical to 0.0.13” with the narrower
  claim: when absent, **no debug instrumentation or `debug` response key is
  added**.
- Add a release/migration note covering zero-argument extension factories,
  direct-instance deprecation, and per-operation class/factory construction.
- Describe `>=0.316.0` as excluding the known cached-sync lifecycle. Do not say
  an open lower bound “pins today's semantics”; `uv.lock` plus regression tests
  verify the resolved version.
- Add `django_strawberry_framework/optimizer/extension.py` to the affected-file
  map. Its `DjangoOptimizerExtension.__init__` comment still says Strawberry
  constructs class entries with `execution_context=`. The parameter may remain
  for direct-construction compatibility, but the rationale must be corrected.

### F3 — P0: “read-only window / nothing else changes” conflicts with teardown failures replacing the operation result

Spec locations: User-facing API, Error shapes, Decision 7, D-N7, and the
teardown-failure discussion.

The current design lets `_build_payload`, query-log materialization, SQL-row
serialization, exception stringification, or traceback formatting raise from
`on_operation` teardown. Strawberry catches an exception escaping the
operation context and constructs a replacement `PreExecutionError`. The
diagnostic observer can therefore discard the original GraphQL `data` and
`errors`, even though the spec calls it a read-only window.

Flag restoration is protected, but result preservation is not.

Required correction:

- Define a two-phase failure policy:
  - setup/acquisition failures before `yield` remain fail-loud, after
    `ExitStack` restores every previously acquired wrapper;
  - after execution has produced a result, diagnostic collection must not
    replace it. Snapshot/row/exception failures are caught as `Exception`
    (never `BaseException`), logged server-side, and degrade to the rows that
    were captured successfully or an empty list.
- Keep the wire contract unchanged: a completed payload still owns `sql` and
  `exceptions` lists; do not add an unplanned third error shape.
- Add a mechanics test that injects a malformed backend log entry or failing
  snapshot/serializer and proves the original `data`/`errors` and every saved
  flag survive.
- Qualify the generic-recovery claim. A recovery response can contain `debug`
  only if the debug hook was entered and its teardown completed enough to
  publish a stash. An earlier hook setup failure can occur before the debug
  hook enters.

### F4 — P1: the SQL capture interval is defined by cursor construction, not only operation entry/exit

Spec locations: Goals 1–2, Decision 4, the restore edge case, and the module
docstring requirements.

Django chooses `CursorDebugWrapper` in
`BaseDatabaseWrapper._prepare_cursor()` when `connection.cursor()` is called.
`CursorDebugWrapper.execute()` does not re-check `queries_logged`.
Consequently:

- a normal cursor created before the extension enters remains uninstrumented
  if executed during the operation; and
- a debug cursor created while the flag is true remains a debug wrapper and
  can continue appending to `queries_log` if retained and executed after the
  extension restores the flag.

The coordinator correctly owns the flag, but flag restoration alone does not
define a perfect logging interval.

Required correction:

- State that the SQL guarantee covers normally short-lived cursors acquired
  while the operation hook is active.
- Explicitly document pre-opened normal cursors and retained debug cursors as
  boundary cases in Decision 4, Edge cases, the class docstring, and GLOSSARY.
- Add a focused mechanics test for both directions. Do not “fix” this by
  porting the rejected cursor monkey-patch; documenting the Django-native
  boundary is consistent with the chosen fidelity source.

### F5 — P1: Slice-3 term import and KANBAN render ordering is reversed

Spec locations: Slice 3 checklist, Implementation plan, Doc updates, and the
Definition of done.

The spec currently says to mark card 044 Done, render `KANBAN.md` and
`KANBAN.html`, then run `manage.py import_spec_terms`.
`import_spec_terms` writes the card's glossary-link rows, and the KANBAN
builders render those rows. Rendering first leaves both generated KANBAN
artifacts stale.

Required correction:

1. Apply all card, `SpecDoc`, `TrackedPath`, glossary-status, and version DB
   updates.
2. Mark card 044 Done; the importer processes only Done cards.
3. Run `manage.py import_spec_terms`.
4. Render `docs/GLOSSARY.md` and `docs/TREE.md` after their final DB mutations.
5. Render `KANBAN.md` and `KANBAN.html` **after** the terms import.
6. Finish with every available importer/builder `--check` mode.

The spec must also enumerate every spec-044 glossary entry whose
`planned for 0.0.14` status changes, preferably deriving the list from
`docs/spec-044-debug_extension-0_0_14-terms.csv`, rather than naming only the
four headline release surfaces.

## 2. Missing edge cases

### F6 — P1: transaction visibility is overclaimed

Spec locations: Goals item 1, User-facing API SQL behavior, the transaction
edge case, and mutation scenario 3.

The extension captures transaction statements only when Django's
`debug_transaction` bracket completes while the operation hook is active.
An `atomic()` block entered and exited inside a resolver is in scope.
`ATOMIC_REQUESTS`, however, wraps the view outside Strawberry execution:
its outer `BEGIN` occurs before the extension and its final
`COMMIT`/`ROLLBACK`, commit failure, and resulting `on_commit` work occur after
the extension.

Required correction:

- Replace the unconditional transaction statement claim with “transaction
  boundaries whose logging completes while the debug hook is active.”
- Explicitly exclude enclosing `ATOMIC_REQUESTS`/middleware transactions and
  post-view work.
- Test an inner resolver-owned `atomic()` block and a schema execution wrapped
  by an outer `transaction.atomic()` to prove the inclusion/exclusion boundary
  without rebuilding the HTTP test infrastructure.

### F7 — P1: multi-database capture is a documented contract with no real multi-database proof

Decision 10 and the GLOSSARY plan promise per-alias capture, but the live suite
asserts only `alias == "default"`. Serializer units and fake partial-acquisition
tests do not prove that a real query on a second alias appears in the response.

Required correction:

- Add a sharded-tier integration case using the existing
  `FAKESHOP_SHARDED=1` infrastructure in
  `examples/fakeshop/test_query/test_multi_db.py` (or a dedicated gated debug
  module).
- Execute a real `shard_b` query through a debug-enabled probe schema and
  assert the captured row reports `alias == "shard_b"` and the correct vendor.
- Assert restoration for both configured aliases.
- Add the touched sharded test/workflow paths to the spec's file map.

### F8 — P1: incremental query execution is neither supported nor excluded

The spec excludes subscriptions but broadly claims query/mutation support.
With Strawberry's experimental incremental execution enabled,
`Schema._handle_execution_result` returns incremental result objects before
the ordinary extension-result assignment. The current two-list, one-final-map
contract does not define whether initial and subsequent `@defer`/`@stream`
payloads carry debug data.

Required correction:

- Add experimental incremental execution to Non-goals/Out of scope for
  `0.0.14`, and state that the contract covers non-incremental query/mutation
  `ExecutionResult`s.
- Do not imply transport-universal behavior until initial/subsequent payload
  semantics are designed and tested.

### F9 — P2: extension ordering affects SQL scope as well as masking and key collisions

`on_operation` hooks enter in list order and unwind in reverse. SQL performed
by another extension's setup/teardown is captured only when that work occurs
inside the debug hook's active interval. The spec documents masking order and
result-key precedence but not this SQL-scope dependency.

Required correction:

- Document that SQL from sibling extension lifecycle hooks is order-dependent;
  resolver/engine SQL remains the stable core contract.
- Add one small mechanics case with a sibling operation hook that performs
  marker SQL before/after `yield`, then prove which markers are included in
  both list orders.

### F10 — P2: the `original_error` walk is cycle-safe but not bounded

An identity set terminates a cycle; it does not bound a long acyclic chain.
Calling that shape “bounded” conflicts with the repository's explicit
Power-of-Ten loop discipline in `utils/typing.py`.

Required correction:

- Add a local maximum-hop constant (64 is the existing type-wrapper ceiling)
  and combine it with identity-cycle detection.
- Define deterministic stop behavior: return the last unique candidate seen
  before a repeated identity or the hop ceiling.
- Test a self-cycle, a multi-node cycle, and a long acyclic chain.
- Separately acknowledge that traceback cause/context formatting and string
  byte size remain unbounded; the hop cap bounds only the
  `original_error` traversal.

### F11 — P2: cross-thread-shared wrappers are unscoped

Django permits explicit wrapper sharing through `inc_thread_sharing()`. The
coordinator protects flag/depth transitions but not concurrent
`queries_log` appends versus deque materialization, and it cannot provide
operation-local attribution.

Required correction:

- Mark explicitly cross-thread-shared database wrappers unsupported/best
  effort.
- The non-interference rule in F3 must still prevent concurrent deque mutation
  from corrupting the GraphQL response.

## 3. Configuration and performance risks

### F12 — scope correction: spec 044 has no `types/relay.py` setting anchor

The question's `types/relay.py` versus `conf.py` premise does not occur in
spec 044:

- the spec explicitly rejects a v1 debug settings key;
- its `types/relay.py` discussion is only an analogy to existing bounded
  chain-walk style; and
- `utils/connections.py` is discussed only to prevent database instrumentation
  from being placed in the Relay-window helper module.

Therefore spec 044 introduces no lazy setting lookup, repeated value
validation, or settings-related thread-safety issue during query execution.
The extension is enabled once in the schema's `extensions=` list.

The premise matches the already-shipped GlobalID strategy path:
`types/relay.py::_resolve_globalid_strategy` reads through `conf.settings` and
performs domain validation in the Relay module. That function runs during type
finalization, not per resolver/query. `conf.py` owns top-level settings-map
normalization/caching; `types/relay.py` owns domain-specific validation. Under
the repository's single-threaded schema-finalization discipline, the lazy
settings singleton's documented test-only reload race is not a query-path
problem.

If a future debug configuration knob is added, put the key/default and
top-level mapping access in `conf.py`, validate the debug-specific value in
the debug module, and resolve it once at schema/extension construction—not
inside row serialization. No such knob is needed for this revision.

### F13 — P1: the enabled cost is only cardinality-bounded, not generally bounded

Spec locations: Decision 10, D5, “Zero cost when disabled, bounded cost when
enabled,” and the payload-size risk.

Corrections needed:

- `connections.all()` materializes a Django wrapper for every configured
  alias. It does not open a raw DB connection, but it can import a backend,
  construct an otherwise-unused wrapper, and surface an invalid alias/backend
  configuration.
- Teardown performs `list(connection.queries_log)` for every alias, copying up
  to `queries_limit` references even when an old, already-full log contains no
  rows from this operation.
- The synchronous teardown also runs on the event-loop thread for async schema
  execution and can stall it.
- Row count is capped per alias by Django's deque, but SQL string length,
  exception count/message/traceback size, alias count, and total response bytes
  are not usefully bounded.
- Query-log rows remain in Django's deque after the response. In non-HTTP
  in-process execution there is no `request_started` reset, so interpolated
  values can persist until reset/eviction.

Required correction:

- Replace “one attribute write” and “bounded cost” with exact complexity and
  retention language.
- Keep row/byte caps as a follow-on if desired, but do not claim a bound the v1
  implementation does not enforce.
- State that disabled means no debug hook/instrumentation; it does not undo the
  global Strawberry floor change in F2.

### F14 — P1: the async follow-on is rejected using a false universal-executor premise

The Risks section says `sync_to_async(thread_sensitive=True)` always uses one
process-wide shared thread. That is only the fallback. Django's ASGI handler
wraps each HTTP request in asgiref `ThreadSensitiveContext`, which selects a
per-context single-thread executor.

Required correction:

- Keep v1's honest “async SQL is typically empty” limitation.
- Replace the categorical rejection with: worker-thread bracketing may be
  viable for normal ASGI HTTP inside the inherited request context, but is not
  universal for direct `schema.execute()`, batching, or work escaping that
  context.
- Require a real ASGI-request prototype before accepting or rejecting the
  follow-on design.

### F15 — P2: the security warning must name SQL-value exposure, retention, and downstream copies

The spec loudly warns about unmasked exception messages/stacks, but Django's
`last_executed_query` output can also interpolate secrets, tokens, email
addresses, and other PII. The response may then be copied into browser
DevTools, HTTP logs, tracing systems, caches, bug reports, or snapshots; the
query log can also retain it in process after in-process execution.

Required correction:

- Expand the class docstring, GLOSSARY, and security section to name
  interpolated SQL values, filesystem/source paths in tracebacks, in-process
  query-log retention, and downstream response copies.
- The off-by-default, code-level opt-in remains an acceptable v1 boundary; a
  settings gate or redaction subsystem is not required for this card.

## 4. Test and documentation gaps

### F16 — P0: the recorded targeted pytest commands will fail the repository coverage gate

`pytest.ini` always adds `--cov`, while `pyproject.toml` enforces
repository-wide `fail_under = 100`. Running one test file or scenario-13 node
ID with the commands currently recorded in the spec will fail global coverage
even when every selected test passes.

Required correction:

- Record targeted development commands with replaced addopts, e.g.
  `uv run pytest -o addopts="-v -n0" <target>`.
- Keep a separate full-suite command/CI node as the owner of the 100% coverage
  gate.
- Apply the same addopts override to any isolated Strawberry-floor node-ID
  run.

### F17 — P1: the Strawberry floor is not durably exercised

The CI matrix varies Python and Django but always resolves Strawberry from
`uv.lock`; no job force-installs `strawberry-graphql==0.316.0`. A one-time
throwaway run does not maintain the advertised minimum.

Required correction:

- Prefer making the existing minimum-support CI node install exactly
  Strawberry 0.316.0 and run the full suite without coverage. The latest node
  continues to own coverage.
- At minimum, add a repeatable floor job that installs project/dev
  dependencies, force-installs 0.316.0, records versions, and runs the
  lifecycle/isolation node ID with coverage disabled.
- Add `.github/workflows/django.yml` to the spec's affected-file map.

### F18 — P1: live DB markers and mutation inputs are underspecified

Scenarios 1–3 perform ORM work. The spec does not pin the required
pytest-django markers, and scenario 3 still omits required domain input:
`Item.category` is non-null and `createItem` requires `categoryId`.

Required correction:

- Mark read scenarios 1–2 with `django_db`.
- Mark mutation scenario 3 with `django_db(transaction=True)`.
- In scenario 3, run `create_users(1)`, `seed_data(1)`, grant `add_item` to
  non-staff `view_item_1`, re-fetch the user, derive a visible category
  GlobalID, and pass `categoryId`.
- Clarify that the “first domain setup” rule applies to product/catalog setup;
  auth setup may precede `seed_data` when the scenario needs a user first.

### F19 — P1: concurrent floor scenario 13 should not introduce unnecessary threaded ORM

Scenario 13 currently requires a “query-derived marker.” Actual concurrent
SQLite ORM in executor threads adds transaction visibility, locking, and
connection-lifetime problems unrelated to the lifecycle regression.

Required correction:

- Use distinct resolver exception/argument markers plus captured wrapper
  identities and restored flags to prove fresh extension instances.
- Perform no ORM in those executor threads.
- If SQL is retained as a requirement, then the spec must instead require
  `transactional_db`, committed seed data, and closing each thread-local
  database connection inside its owning worker before that thread exits.

The no-ORM shape is simpler and proves the intended 0.315-vs-0.316 lifecycle
contract without adding flaky database concurrency.

### F20 — P2: generated-document status scope and final checks are incomplete

The Slice-3 text names headline surfaces but does not fully enumerate the
spec-044 glossary terms whose status/body changes, the exact tracked-path DB
updates, or the final check sequence.

Required correction:

- Derive the spec-044 term set from
  `docs/spec-044-debug_extension-0_0_14-terms.csv`.
- Explicitly update every applicable planned/shipped status in the glossary
  DB, not only the response-extension headline.
- Synchronize `TrackedPath.is_current` for all new files/directories before
  rendering `docs/TREE.md`.
- Run the glossary, tree, KANBAN Markdown, KANBAN HTML, and spec-term importer
  check modes after the last DB mutation, in the ordering defined by F5.

### F21 — P2: the temporary fail-loud coverage guard is unnecessary

This is a staging-anchor correction rather than a production-spec defect.
`pyproject.toml` already excludes `raise NotImplementedError` from coverage,
so the fail-loud planning stub does not need
`tests/extensions/test_debug.py::test_planning_stub_fails_loudly_on_import` to
keep the gate green. The earlier feedback premise that the raise was an
uncovered executable line was incorrect.

Required correction:

- Remove the temporary import guard before implementation work; it adds no
  coverage value.
- Keep the real Slice-1 mechanics tests as the first imports of the completed
  module.

## Contracts verified as sound

The following should remain unchanged except where qualified above:

- `DjangoDebugExtension` belongs in
  `django_strawberry_framework.extensions`, not the package root.
- Class-form opt-in is the correct per-operation lifecycle at the 0.316 floor.
- A sync `on_operation` generator can serve both sync and async execution.
- Saved-value restoration, `ExitStack` partial unwind, and same-wrapper
  reference counting are appropriate.
- Concrete wrapper identity—not database alias—is the correct coordination
  unit.
- Django `queries_log` is an acceptable v1 fidelity source when its cursor
  lifetime, rollover, reset, async, and attribution boundaries are explicit.
- `callproc()` exclusion and raw `executemany()` format match Django.
- Nested same-thread and same-wrapper overlap restore safely but cannot provide
  operation-local SQL attribution.
- Merge precedence, async `ExecutionContext.extensions_results` precedence,
  and replacement of an existing result extensions map are correctly derived
  from Strawberry 0.316.
- `[MaskErrors, DjangoDebugExtension]` is the correct order when the debug
  payload must retain unmasked original exceptions.
- Probe URLconf activation, schema reload discipline, and repeated
  `finalize_django_types()` are supported by the existing fixtures; no test
  infrastructure rewrite is required.
- Off-by-default code-level schema wiring is a reasonable v1 security and
  performance posture once the dependency-wide caveat and disclosure wording
  are corrected.

## Required Revision-8 update set

Before Slice 1 starts, revise the spec and staged TODOs as one coherent pass:

1. Fix optimizer scenario 2 to the visibility-safe two-query prefetch shape.
2. Replace byte-identical/off-by-default overclaims and document the global
   Strawberry lifecycle migration.
3. Define setup fail-loud versus post-execution non-interfering diagnostic
   failure behavior.
4. Document and test the cursor-construction lifetime boundary.
5. Correct transaction scope, sibling-hook SQL ordering, generic-recovery
   qualification, incremental-execution scope, and cross-thread sharing.
6. Add a bounded `original_error` hop policy and tests.
7. Add real sharded capture coverage.
8. Correct performance, async-follow-on, retention, and sensitive-data
   language.
9. Fix DB markers, mutation setup, targeted pytest commands, and scenario-13
   concurrency scope.
10. Add durable Strawberry-floor CI and the necessary affected files.
11. Correct the Done → terms import → generated-render ordering and enumerate
    all glossary/tracked-path updates.
12. Remove the unnecessary temporary planning-stub import guard.

After these corrections, the implementation remains a focused private
coordinator plus serializers and one public extension class; none of the
findings requires a package-wide abstraction, new runtime dependency, or
settings subsystem.
