# Review: `django_strawberry_framework/mutations/resolvers.py`

Status: verified

## Understanding

`django_strawberry_framework/mutations/resolvers.py` owns the write-side runtime execution pipeline for GraphQL mutations. It serves as the single shared foundation (`run_write_pipeline_sync`) powering all mutation flavors: model mutations (`DjangoMutation` create, update, delete), form mutations (`DjangoFormMutation`, `DjangoModelFormMutation`), serializer mutations (`DjangoSerializerMutation`), and authentication mutations (`Register`).

Key responsibilities and load-bearing invariants traced:
1. **Single atomic transaction & async boundary:** Opens and pins a single `transaction.atomic()` boundary on the designated write alias (`open_write_pipeline`, `pipeline_alias_guard`). The async runtime (`run_pipeline_async`) wraps the entire synchronous ORM pipeline in a single `sync_to_async(thread_sensitive=True)` invocation, preventing async/await interleaving across database transactions.
2. **Authorize-before-decode security ordering:** Enforces the strict lifecycle `locate -> authorize -> decode -> validate -> write -> refetch/snapshot -> payload`. Authorizing prior to decoding prevents unauthorized callers from probing relation visibility via relation queries in the decode phase.
3. **Visibility-scoped locate & relation resolution:** Lookups on `update` and `delete` route through `locate_instance`, querying the target's primary `DjangoType.get_queryset` so that hidden and missing rows return identical not-found `FieldError`s (no existence leak). Similarly, relation decoding (`_decode_single_relation_id`, `_decode_relation_id_list`) type-checks GlobalIDs against related target models and queries visibility querysets via `decode_visible_relation_ids`.
4. **Server-side GlobalID decode & pk coercion:** `coerce_lookup_id` decodes GlobalIDs server-side; invalid formats and wrong-model IDs map to `_invalid_lookup_id_error`, while uncoercible pk literals map to `not_found_error`, preventing raw Django `ValueError` leaks.
5. **Anti-drift & substitution guards:** `authorized_pk` and `target_state` are captured immediately after locate. `reject_substituted_row` verifies that neither permission hooks nor write steps switch or drift the target row's primary key.
6. **Constraint-aware partial update exclude:** `_unprovided_exclude` computes `full_clean(exclude=...)` for partial updates while retaining fields that co-participate in `UniqueConstraint`, `unique_together`, or `field.unique` with any provided field.
7. **Concurrency hardening:** Employs base-manager `SELECT ... FOR UPDATE` row locks on locate (`locate_instance`, `base_locked_queryset`) and handles concurrent delete/race conditions with in-band `conflict` envelopes (`forced_save_or_field_errors`, `_delete_or_field_errors`).
8. **Snapshot-before-delete:** Pre-fetches and materializes the optimized snapshot before executing `instance.delete()`, preserving the original node ID on the detached instance for client-side cache eviction.
9. **Atomic error payload handling:** `error_payload_builder` marks `transaction.set_rollback(True, using=using)` on any validation or decode failure before assembling the `FieldError` envelope.

## Verification

1. **Existing Test Suite:** Examined all 74 unit and integration tests in `tests/mutations/test_resolvers.py`. The suite comprehensively tests:
   - Create, partial update, and delete happy paths.
   - Delete snapshot relation materialization and node ID preservation.
   - Custom `relay.NodeID[str]` lookup resolution with real pk disambiguation.
   - `full_clean` validation error envelopes and unique constraint multi-field `__all__` keys.
   - Partial update exclude calculation and co-participating unique constraint preservation.
   - GlobalID rejection of raw pks, malformed values, wrong-model IDs, and uncoercible literals.
   - Relation visibility enforcement on single and multi-relation branches.
   - Naive datetime timezone-awareness coercion under `USE_TZ`.
   - Explicit `null` rejection on non-nullable scalar, file, and relation fields.
   - Atomic rollback behavior on post-save step failures.
   - Async pipeline execution and `SyncMisuseError` rejection of async `get_queryset`.
   - Pk drift detection during authorization and write execution.
   - Protected and restricted deletion reference handling.
2. **Scratch Experiments:** Created `docs/review/temp-tests/mutations__resolvers/test_resolvers_scratch.py` verifying timezone coercion, explicit null error detection, model unique constraint grouping, and entry factory generation (`4 passed`).
3. **Focused Suite Runs:**
   - Ran `pytest tests/mutations/test_resolvers.py --no-cov` (74 passed in 3.81s).
   - Ran full `pytest tests/mutations/ --no-cov` (346 passed in 7.18s).

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

`django_strawberry_framework/mutations/resolvers.py` provides a robust, battle-tested, and secure write-pipeline orchestration. All contracts (atomicity, authorize-before-decode, GlobalID type safety, visibility isolation, anti-drift protection, concurrency locking, and snapshot-before-delete) are cleanly implemented and thoroughly verified.

## Implementation (Worker 1)

- **Changed files:**
  None — zero-edit cycle.
- **Permanent tests:**
  Existing test suite (`tests/mutations/test_resolvers.py`, 74 tests) comprehensively pins all runtime pipeline behaviors and error boundaries.
- **Scratch / Focused verification:**
  - `pytest docs/review/temp-tests/mutations__resolvers/test_resolvers_scratch.py --no-cov` (4 passed).
  - `pytest tests/mutations/test_resolvers.py --no-cov` (74 passed).
  - `pytest tests/mutations/ --no-cov` (346 passed).
- **Formatter and linter results:**
  None — zero-edit cycle.
- **Evidence for rejected findings:**
  No findings were rejected; the implementation satisfies all architectural requirements.
- **Changelog entry:**
  None — zero-edit cycle.

## Independent verification (Worker 2)

1. **Cycle Verification & Baseline Check:**
   - Confirmed target file `django_strawberry_framework/mutations/resolvers.py` is zero-edit against baseline `HEAD` (`12779c99`) via `git diff 12779c99 -- django_strawberry_framework/mutations/resolvers.py` (empty output).
2. **Path Tracing & Invariant Audits:**
   - Re-traced `open_write_pipeline` -> `coerce_lookup_id` -> `locate_instance` (with `base_locked_queryset` row locking) -> `authorize_or_raise` -> `reject_substituted_row` -> `decode_step` -> `write_step` -> `tail_step` / `refetch_optimized`.
   - Verified authorize-before-decode invariant prevents unauthorized callers from probing relation existence / visibility.
   - Verified `coerce_lookup_id` rejects malformed or wrong-model GlobalIDs prior to DB lookup, and coercing invalid pk literals cleanly maps to `not_found_error` avoiding Django `ValueError` leaks.
   - Verified `_unprovided_exclude` computes `full_clean(exclude=...)` while keeping fields participating in `UniqueConstraint`, `unique_together`, or `field.unique` with provided fields.
   - Verified `forced_save_or_field_errors` and `_delete_or_field_errors` conflict handling for concurrent delete/race conditions.
   - Verified `error_payload_builder` ensures `transaction.set_rollback(True, using=using)` on any decode/validation/write error.
3. **Focused & Scratch Test Execution:**
   - `uv run pytest tests/mutations/test_resolvers.py --no-cov` (74 passed).
   - `uv run pytest docs/review/temp-tests/mutations__resolvers/test_resolvers_scratch.py --no-cov` (4 passed).
   - `uv run pytest tests/mutations/ --no-cov` (346 passed).
4. **Outcome:**
   - All findings and architectural invariants independently confirmed.
   - Target is complete, correct, and fully verified.

