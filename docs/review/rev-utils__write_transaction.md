# Review: `django_strawberry_framework/utils/write_transaction.py`

Status: verified

## Understanding

`django_strawberry_framework/utils/write_transaction.py` provides the cross-flavor database transaction discipline, alias pinning, row-locking, permission-phase containment, target drift detection, and disappearing-row conflict handling across all mutation subsystems (model, form, serializer):

1. **Managed Write Transaction & Scope Enforcement (`_MANAGED_WRITE_ALIAS`, `managed_write_transaction`, `require_managed_write`, `open_write_pipeline`)**:
   - Manages a contextvar `_MANAGED_WRITE_ALIAS` set by `DjangoSchema`'s execution context around top-level mutation fields to span GraphQL value completion.
   - Rejects unmanaged schema execution (`require_managed_write`) before any database operations when executed under a plain `strawberry.Schema`, preventing silent commits behind failed serialization.
   - Opens nested `transaction.atomic` and initializes `WriteAliasContext` in `open_write_pipeline`.

2. **Router Write Alias Resolution & Pinning (`resolve_write_alias`, `pin_write_queryset`, `check_instance_write_alias`, `make_cross_alias_save_guard`, `pipeline_alias_guard`)**:
   - Resolves the write alias once per operation via `router.db_for_write` (`DEFAULT_DB_ALIAS` fallback for model-less forms).
   - Re-checks instance-sensitive write router divergence (`check_instance_write_alias`) post-locate, failing closed on mismatch.
   - Pushes alias pinning across custom `get_queryset` hooks (`pin_write_queryset`), raising `ConfigurationError` if `.using(...)` was explicitly rerouted.
   - Installs database connection `execute_wrapper`s and thread-scoped `pre_save` signal listeners (`pipeline_alias_guard`, `make_cross_alias_save_guard`) enforcing that non-pinned connections reject all statements outside authorization phases and pinned connections permit writes only during explicit `pipeline_write_phase()`.

3. **Authorization Phase Containment (`authorization_phase`, `_enforce_read_only_barrier`)**:
   - Provides scoped read access for divergent read/write router auth aliases (`AUTH_USER_MODEL`, permissions, groups, content types) during permission evaluation.
   - Isolates non-pinned auth connections in rolled-back `transaction.atomic` blocks backed by database-level read-only modes (PostgreSQL `SET TRANSACTION READ ONLY`, SQLite `PRAGMA query_only` with state save/restore). Fails closed on unsupported database backends.

4. **Lexical SQL Classification (`is_read_only_sql`, `_sql_statement_token`)**:
   - Normalizes SQL strings (including stripping comments, whitespace, and leading parentheses) and checks against an allow-list (`SELECT`, `SAVEPOINT`, `RELEASE`, `ROLLBACK`) while neutralizing custom `str` subclasses.

5. **Canonical PK Comparison & Substitution Backstop (`canonical_pk`, `pks_match`, `reject_substituted_row`)**:
   - Normalizes PK values through the model's PK field `to_python` (supporting UUID, integer, string variations) and fails closed on malformed values.
   - Enforces PK immutability between locate and save steps to prevent row substitution.

6. **Target State Snapshotting & Drift Rejection (`snapshot_target_state`, `assert_no_target_drift`, `_field_fingerprint`)**:
   - Captures pre-save snapshots of loaded concrete fields on located instances.
   - Uses an iterative, non-recursive stack with a bounded node budget (`_SNAPSHOT_NODE_BUDGET = 100_000`) to fingerprint nested containers (`dict`, `list`, `set`, `frozenset`, `tuple`, `bytes`), detecting in-place mutations without risk of `RecursionError`.
   - Captures `FieldFile` by filename string to catch in-place descriptor mutations.
   - Ignores deferred fields at both snapshot and verification phases to prevent unexpected lazy loading queries.

7. **Base Row Locking & Relation Scoping (`base_locked_queryset`, `pipeline_scoped_queryset`)**:
   - Applies `SELECT ... FOR UPDATE` via `model._base_manager` constrained by a PK subquery over the visibility queryset, avoiding join/union syntax errors on advanced querysets.
   - Connects relation checks in `utils/querysets.py` to write alias pinning and conditional row locking.

8. **Disappearing-Row Conflicts & Version Compatibility (`conflict_error`, `not_updated_exceptions`, `forced_update_conflict_errors`)**:
   - Detects zero-row forced updates and vanishing rows, mapping them to the in-band `conflict` `FieldError` on `id` when the transaction is unpoisoned and the row is verified absent.
   - Seamlessly handles Django 6.0's typed `Model.NotUpdated` vs Django 5.2's untyped `DatabaseError`.

## Verification

1. **Codebase Call-Site Tracing**:
   - Traced all callers in `schema.py`, `mutations/resolvers.py`, `forms/resolvers.py`, `rest_framework/resolvers.py`, `relay.py`, and `utils/querysets.py`.
   - Verified that all write pipelines uniformly enter `open_write_pipeline` and `pipeline_alias_guard`, guard saves with `pipeline_write_phase`, snapshot targets via `snapshot_target_state`, and enforce `assert_no_target_drift`.

2. **Existing Test Suite Review**:
   - Reviewed tests in `tests/mutations/test_write_transaction.py` (53 test cases) and `tests/mutations/test_resolvers.py`.
   - Validated coverage across plain `strawberry.Schema` refusal, async/sync completion rollback, concurrent async mutation serialization, Postgres/SQLite read-only barrier arming/restoring, fail-closed router divergence, iterative container fingerprinting, file descriptor drift, SQL comment-stripping allow-list, and disappearing-row conflict mapping.

3. **Focused Verification**:
   - Ran `uv run pytest tests/mutations/test_write_transaction.py tests/mutations/test_resolvers.py --no-cov` (127 passed in 5.20s).
   - Ran targeted coverage check confirming 100% test coverage over `django_strawberry_framework.utils.write_transaction`.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

`django_strawberry_framework/utils/write_transaction.py` is a robust, mature, and thoroughly tested foundation for atomic multi-flavor write operations, alias isolation, database-level authorization containment, and target drift detection. No defects or design issues were identified.

## Implementation (Worker 1)

None — zero-edit cycle.

## Independent verification (Worker 2)

1. **Scoped Diff Verification**:
   - Executed `git diff 12779c99 -- django_strawberry_framework/utils/write_transaction.py` and confirmed zero modifications against baseline `HEAD`.

2. **System Behavior & Invariant Tracing**:
   - Traced managed write transaction lifecycle (`_MANAGED_WRITE_ALIAS`, `managed_write_transaction`, `require_managed_write`, `open_write_pipeline`), verifying fail-before-write guard for unmanaged schemas and completion-spanning atomicity across async/sync boundaries.
   - Traced write alias resolution and fail-closed guards (`resolve_write_alias`, `pin_write_queryset`, `check_instance_write_alias`, `make_cross_alias_save_guard`, `pipeline_alias_guard`), verifying database connection wrappers, thread-scoped `pre_save` interceptors, and strict single-alias write containment.
   - Traced authorization phase containment (`authorization_phase`, `_enforce_read_only_barrier`), confirming database-enforced read-only modes on PostgreSQL (`SET TRANSACTION READ ONLY`) and SQLite (`PRAGMA query_only` with state save/restore) along with unconditional rollback and fail-closed behavior on unsupported database engines.
   - Traced lexical SQL classification (`is_read_only_sql`, `_sql_statement_token`), confirming comment-stripping (`--`, `/* ... */`), whitespace normalization, parenthesized queries, and string subclass neutralization against allow-listed prefixes.
   - Traced canonical PK comparison (`canonical_pk`, `pks_match`, `reject_substituted_row`), verifying field-level `to_python` normalization and fail-closed substitution prevention.
   - Traced target state snapshotting and drift detection (`snapshot_target_state`, `assert_no_target_drift`, `_field_fingerprint`), validating iterative non-recursive structural container hashing with bounded node budget (`_SNAPSHOT_NODE_BUDGET = 100_000`), `FieldFile` name-by-value capture, and deferred-field bypassing.
   - Traced base row locking (`base_locked_queryset`, `pipeline_scoped_queryset`), confirming `SELECT ... FOR UPDATE` query construction via `_base_manager` over PK subqueries without attaching locks directly to complex consumer querysets.
   - Traced disappearing-row conflict mapping (`conflict_error`, `not_updated_exceptions`, `forced_update_conflict_errors`), confirming typed `Model.NotUpdated` (Django 6.0+) vs untyped `DatabaseError` (Django 5.2) handling and usable-transaction / row-absent probe verification.

3. **Focused Test Execution & Coverage**:
   - Ran `uv run pytest tests/mutations/test_write_transaction.py tests/forms/test_resolvers.py tests/rest_framework/test_resolvers.py --no-cov` (276 passed in 5.05s).
   - Validated 100% line coverage (289/289 statements covered) of `django_strawberry_framework/utils/write_transaction.py`.

4. **Disposition of Findings**:
   - Confirmed zero open findings or defects; module is robust, well-tested, and verified.

