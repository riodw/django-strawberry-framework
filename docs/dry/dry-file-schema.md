# DRY review: `django_strawberry_framework/schema.py`

Status: fix-implemented → verified

## System trace

The target owns two lifecycles. **The completion-spanning mutation transaction**
(`DjangoMutationExecutionContext`): for each TOP-LEVEL field whose resolver carries
`MUTATION_CLASS_MARKER` it opens one `transaction.atomic(using=<write alias>)` before the
resolver runs and exits it only after graphql-core finished completing that field's value;
any error the execution collects during the window (resolver-raised or
completion-raised) marks the transaction for rollback, so an unserializable payload rolls
the write back instead of committing behind `data: null`. The window publishes the managed
alias through `utils/write_transaction.py::managed_write_transaction`, which the write
pipeline REQUIRES (`require_managed_write` fails a plain-`strawberry.Schema` execution
before any database work). Sync execution holds atomic + marker context directly on the
calling thread; async execution opens/closes them inside the one
`thread_sensitive=True` worker (`utils/querysets.py::run_in_one_sync_boundary`) and
serializes windows per effective alias through a process-wide `_AsyncAliasLock` whose
`_AcquireHandoff` makes a cancelled acquisition end unowned. **The schema-construction
policy** (`DjangoSchema`): resolves `resource_policy=` / `error_policy=` once via
`resolve_resource_policy` / `resolve_error_policy` (both delegating to
`utils/policies.py::resolve_policy`), exposes them as attributes, installs
`DjangoResourcePolicyExtension` APPENDED and `DjangoErrorPolicyExtension` PREPENDED unless
the consumer supplied an entry (matching shared through `_extension_entry_matches`),
defaults `execution_context_class`, and deduplicates only a factory-produced automatic
error-policy instance in `get_extensions`.

Consumers: every transport reaches this code through `schema.execute` /
`schema.execute_sync` — grep confirms `views.py`, `consumers.py`, and `routers.py`
contain NO transaction or extension-assembly code of their own, so HTTP sync, HTTP async,
and WebSocket all share the ONE window implementation.
`examples/fakeshop/config/schema.py #"schema = DjangoSchema("` builds the live singleton
with `config=strawberry_config()` — pure constructor pass-through; `DjangoSchema` never
touches `StrawberryConfig` or scalar maps. ~77 construction sites across package tests,
live probes, and example schemas exercise it. The marker round trip:
`mutations/fields.py:303` stamps `MUTATION_CLASS_MARKER` on the synthesized `_resolve`;
`schema.py::_marked_mutation_class` reads it back through Strawberry's
`strawberry-definition` → `base_resolver.wrapped_func` chain; the constant is imported by
both, single-sourcing the name.

Lockstep surfaces: changing window semantics moves `schema.py` plus the
`write_transaction.py` docstring contract, its tests, GLOSSARY/README prose; changing
which fields get wrapped moves the stamp+read pair; changing extension install position
moves `DjangoSchema.__init__` plus spec-048/047 prose and the position-pinning test rows.

## Verification

Axis 1 — cross-flavor policy mirroring (searched, ruled out). The three write flavors'
database discipline converges on ONE owner, `utils/write_transaction.py` (its module
docstring states exactly that); `schema.py` carries zero flavor-specific logic — gating is
marker-only and the alias derives once per operation from
`resolve_write_alias(model)` (`write_transaction.py::resolve_write_alias`). The
policy-resolution idiom is shared through `utils/policies.py::resolve_policy`. Transport
mirroring does not exist: no `transaction` or extension-list code in views/consumers/
routers (grep: zero hits). Posited change "route writes on a second alias" forces 1
production site (`resolve_write_alias`).

Axis 2 — sync and async twins (searched; one hit, fixed). `_execute_mutation_field_sync`
vs `_execute_mutation_field_async`, compared behaviorally not textually. FOUND: the
window's FAILURE RULE — "any located error collected during the window marks the
transaction for rollback" — was spelled twice, at `schema.py:270-271` (sync) and inside
the async `_exit_clean` closure (`schema.py:322-323`). Posited change "restrict the
rollback trigger to errors whose GraphQL path belongs to this field" forced BOTH sites →
count 2 → became the finding below. The rest of the twin differences are load-bearing
lifecycles, not duplication: async hops every DB-touching step through
`run_in_one_sync_boundary`, awaits the awaitable completion, takes the per-alias mutex,
and must run `atomic.__exit__` in worker-thread closures (an exception's name is cleared
when its except block exits). Both colors are independently tested:
`tests/mutations/test_write_transaction.py` carries explicit sync/async twin pairs
(BaseException exit rows, same-loop and cross-event-loop serialization rows), the async
completion-failure rollback is a package unit row, and the sync one is pinned live over
HTTP in `examples/fakeshop/test_query/test_mutation_atomicity.py` — so the twins cannot
drift silently even where their code differs.

Axis 3 — derived rather than repeated knowledge (searched, clean). The alias is derived at
one site per operation; graphql-core's two error-container shapes are bridged by one
compat shim (`_execution_errors`); consumer-extension suppression matching is factored
once into `_extension_entry_matches`; the factory-dedup bookkeeping
(`_auto_error_policy_extension`) lives only in `get_extensions`. No name concatenation,
field-set re-derivation, or settings recomputation exists on this surface.

Axis 4 — inverse and round-trip pairs (searched; rejected with evidence). The marker pair
(`mutations/fields.py:303` setattr ↔ `schema.py:226` getattr) shares the imported
constant `MUTATION_CLASS_MARKER`, so the token cannot drift; the strawberry-internals
traversal lives only at the read site and every generated-mutation test executes the full
path, so any change to either half fails loudly on first execution rather than drifting.
Posited change "stamp the marker on the `StrawberryField` instead of `wrapped_func`"
forces 2 sites (stamp + read chain) — but that is an inherent producer/consumer seam
across a module boundary; a shared registry object would be heavier machinery for a
two-party contract already exercised end-to-end. REJECTED. No encode/decode or
pack/unpack grammar otherwise.

Axis 5 — contracts restated in another medium (searched; counted, no drift). The
completion-spanning contract is held in the `schema.py` module docstring,
`write_transaction.py` docstrings, GLOSSARY entries (`DjangoSchema`,
`DjangoMutationExecutionContext`, both policy extensions),
`docs/README.md #"DjangoSchema is required for generated mutations"`, the spec-046/048
archives, and three executable tiers (unit twins, live `/graphql/` atomicity matrix,
plain-Schema refusal row). The install-position contract is pinned bidirectionally by
tests (`test_schema.py` shape rows; `test_error_policy.py`'s index-zero row) against the
LIFO-teardown rationale in `_with_error_policy_extension`. Posited change "mask tear down
FIRST instead of last" forces 1 production site + ≥3 prose media + ≥2 test trees: that
spread is documentation doing its job, conditioned on exactly one production statement of
each rule — which holds. Spot-checked the GLOSSARY entries against present-day code: they
agree (prepend-at-index-0, append-as-class, marker-driven wrapping).

Single-edit-site counts (posited changes):
- "Roll back only on field-owned path errors" → **2** production sites before this
  review's fix (both twins); **1** after (`_rollback_for_new_errors`).
- "Also wrap subscription root fields" → `execute_field` gating only: **1**.
- "Reword the plain-Schema refusal" → `write_transaction._UNMANAGED_SCHEMA_MESSAGE`
  only (**1**); `schema.py` carries no copy of the message.
- "Change how the write alias resolves" → `resolve_write_alias` only: **1**.
- "Add a third auto-installed extension" → `__init__` + one `_with_*` helper: **2**, the
  irreducible install+suppress pair sharing `_extension_entry_matches`.
- "Move where the mutation-class marker lives" → **2** (stamp/read pair); consolidation
  rejected under axis 4.

Strongest rejected candidates:
1. Merging the sync/async twins into one parameterized method — the shared part was ONLY
   the failure decision (extracted); everything else differs by thread-boundary mechanics
   each docstring owns, and a mode flag or closure web would hide which half runs where.
   DRY.md ground rules: a helper needing mode flags makes the system less DRY.
2. One `_with_policy_extension(extensions, cls, prepend)` engine for both installers —
   append-vs-prepend IS the contract (error masking must tear down last after every
   `original_error` reader, notably `extensions/debug.py::DjangoDebugExtension`; resource
   gating wants first setup), documented as spec-048 Decision 10; a flag would reconcile
   distinct rules behind one switch. The genuinely shared matching is already extracted.
3. Unifying `_AsyncAliasLock` with `write_pipeline`'s lock plumbing — different scopes
   and lifetimes: a process-wide completion-window mutex per alias vs a request-scoped
   `(alias, lock)` context; merging couples process concurrency control to request state.

Scratch experiments: none needed — every uncertain point was settled by reading the
admitted paths and by existing executable coverage across the three tiers.

## Opportunities

### 1. The window's rollback rule was spelled once per execution color

- **Repeated responsibility:** one failure rule — any located error the execution
  collected during the completion-spanning window marks the transaction for rollback —
  implemented twice because there are two execution modes.
- **Sites:** `django_strawberry_framework/schema.py:270-271` (sync twin, inline) and
  `django_strawberry_framework/schema.py:322-323` (async twin, inside the
  worker-thread `_exit_clean` closure).
- **Evidence:** posited change "restrict the trigger to errors whose GraphQL path belongs
  to this field" (or "ignore post-completion errors added by later hooks") forces BOTH
  sites to move together (count 2); they share inputs (the `errors_before` snapshot, the
  alias), share semantics (located errors are not exceptions, so exception-based rollback
  would miss them), and exist solely because execution has two colors. A fix applied to
  one twin only would leave the other mode rolling back on a different predicate.
- **Owner:** `DjangoMutationExecutionContext` itself — the object that owns the window
  lifecycle states the rule once as `_rollback_for_new_errors(errors_before, alias)`.
- **Consolidation:** added `_rollback_for_new_errors` next to `_execution_errors` (whose
  compat shim it builds on) carrying the moved rationale; the sync twin calls it before
  its inline `atomic.__exit__(None, None, None)` and the async `_exit_clean` calls it
  before its boundary-routed exit. The per-mode enter/exit MECHANICS stay untouched.
- **Proof:** the rule's both arms were already executed end-to-end on both colors
  (`tests/mutations/test_write_transaction.py` async completion-failure rollback +
  success-commit rows and BaseException-exit twins; the live sync tier in
  `examples/fakeshop/test_query/test_mutation_atomicity.py`), so drift stays caught; a new
  direct unit row, `tests/test_schema.py::test_rollback_for_new_errors_is_the_window_rule_for_both_executions`,
  pins the owner's true/false arms against a real atomic block
  (`connection.needs_rollback`) independent of any transport.
- **Risks / non-goals:** the two `atomic.__exit__` placements remain deliberately
  per-mode (sync inline; async routed through `run_in_one_sync_boundary` so the exit runs
  on the connection's worker thread) — only the DECISION moved into one owner. The other
  `set_rollback` sites are different rules and stay separate:
  `mutations/resolvers.py:357` (unconditional envelope-path rollback before payload build)
  and `write_transaction.py:382` (unconditional barrier rollback in `authorization_phase`).

## Implementation (Worker 1)

- `django_strawberry_framework/schema.py`: new
  `DjangoMutationExecutionContext._rollback_for_new_errors` (owner of the window's
  failure rule, rationale moved here); `_execute_mutation_field_sync` and the async
  `_exit_clean` now call it instead of restating the comparison; the sync docstring's
  duplicated rationale sentence replaced by a pointer.
- `tests/test_schema.py`: added
  `test_rollback_for_new_errors_is_the_window_rule_for_both_executions`.
- Orphan-import sweep: nothing removed; `transaction` remains used at the owner and the
  enter/exit sites; no imports changed in either file.
- `uv run ruff format .` + `uv run ruff check --fix .`: clean ("All checks passed!").
- pytest DEFERRED per AGENTS.md (no run without explicit maintainer authorization).
- Cycle baseline `97e5e84`: `schema.py` was identical to baseline before this review's
  edit; the only tracked changes in scope are the two files above.

## Judgment

`schema.py` sits at a genuine convergence point — every transport's generated-mutation
transaction and every auto-installed policy passes through it — and the surrounding system
has already consolidated what could be: flavor discipline in `utils/write_transaction.py`,
policy resolution in `utils/policies.py`, entry matching in `_extension_entry_matches`,
and transport-neutral boundaries in `run_in_one_sync_boundary`. What remained was the
classic axis-2 residue: one decision spelled in both color-specific twins. That is now
stated once on the class that owns the window, with both colors still free to own their
thread-boundary mechanics. Everything else probed — the twins' remaining asymmetry, the
extension installer pair, the marker round trip — came back as load-bearing structure
with counts of one or with drift already made loud by the test tiers.

## Independent verification (Worker 2)

Re-traced from cycle baseline `97e5e84` (scoped diff: exactly `schema.py` +21/−8 and
`tests/test_schema.py` +21; other dirty files in the tree — GLOSSARY, bug-hunt scripts/tests,
db artifacts — are concurrent work outside this item and untouched). Verdict: **verified**.

Equivalence, state by state (both former spellings extracted from the baseline; the helper body
is statement-for-statement identical to each):

- No new errors during the window → comparison false → committable. Identical before/after.
- Located resolver error collected during the window (not an exception — the case an
  exception-based rule would miss) → length delta > 0 → `set_rollback(True, using=alias)`.
  Identical.
- Completion-raised error (non-nullable null / corrupt scalar) lands inside
  `super().execute_field` on both colors before the decision point → rollback. Identical.
- Errors added BEFORE the window opens are absorbed by the unchanged `errors_before`
  snapshots (`schema.py::DjangoMutationExecutionContext._execute_mutation_field_sync`
  #"errors_before = len(self._execution_errors())" and its async twin) → no trigger. Identical.
- An exception ESCAPING resolve/completion consults neither spelling; both route through
  `atomic.__exit__(type(exc), exc, tb)` whose non-suppression marks rollback itself. Path
  untouched by this change.
- Ordering/threading: the sync call replaced the inline block at exactly its old position
  between the exception-path exit and the clean `atomic.__exit__`; the async call sits inside
  `_exit_clean`, still routed through `run_in_one_sync_boundary`, so `set_rollback` executes on
  the worker thread holding the thread-local connection — the position and thread affinity of
  the old code are preserved.

Proof tiers: the new row does NOT drive the twins through real execution paths — it pins the
owner's true/false arms directly against a real atomic block via a `__new__` instance. The twins
themselves remain driven end-to-end by untouched permanent rows: async true arm
`tests/mutations/test_write_transaction.py::test_async_update_completion_failure_rolls_back`
(real `await schema.execute` through `_exit_clean`) + async false arm
`test_async_update_success_commits`; sync true arm live over `/graphql` in
`examples/fakeshop/test_query/test_mutation_atomicity.py` (four completion-failure rows) plus
its success-commit row; BaseException exit twins at that file's `..._raised_base_exception`
rows. So behavioral drift of the rule fails loudly on both colors. One accepted residue: a
deliberate behavior-preserving re-inline at one call site would pass every test by construction
(behavior-identical); that regression class is caught by review process, not tests — pinning the
wiring with a spy would test implementation rather than behavior.

Remaining-spelling sweep (`set_rollback` across repo): package hits exactly three, each a
distinct rule — `schema.py` line 255 (THE window rule, now single-spelled);
`mutations/resolvers.py::error_payload_builder #"transaction.set_rollback(True, using=using)"`
(unconditional envelope invariant "an error envelope never commits", pipeline-pinned alias,
trigger = envelope construction);
`utils/write_transaction.py::authorization_phase #"set_rollback(True, using=barrier_alias)"`
(unconditional discard of read-only auth-barrier atomics on NON-pinned aliases).
Non-package hit: `scripts/capture_pg_predicate_explain.py` (EXPLAIN harness
discarding its own probe block, default alias); docs/review and bug_hunt mentions are prose.
No third spelling of the window rule remains.

Rejected candidates re-probed: read both install paths in full — the resource installer
None-normalizes the RAW constructor value under an explicit no-truthiness rule then APPENDS a
class; the error installer receives the already-normalized list and PREPENDS a class; the shared
matching already lives in `_extension_entry_matches`. A flag-unified engine would reconcile two
documented contracts (LIFO teardown: masking tears down last after `original_error` readers;
resource gates first so sets up last) behind one switch — rejection upheld. Wholesale twin merge
(mode-flag web over load-bearing thread-boundary mechanics) and `_AsyncAliasLock` vs request-
scoped pipeline `(alias, lock)` plumbing rejections also upheld against present-day source.

Matrix discharged against the real surface: axis 1 transports carry zero transaction/extension
assembly (grep: views/consumers/routers contain no transaction API call); axes 2–5 as recorded,
with GLOSSARY prose re-spot-checked against current code. Single-edit recount with my own posited
change ("restrict the trigger to located errors whose GraphQL path belongs to this field"):
forces exactly ONE site, `_rollback_for_new_errors` (snapshot lines need no change); pre-fix the
same change forced both twins. Recorded count holds. pytest deferred per AGENTS.md.
