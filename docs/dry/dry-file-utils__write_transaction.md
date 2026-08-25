# DRY review: `django_strawberry_framework/utils/write_transaction.py`

Status: verified

## System trace

`django_strawberry_framework/utils/write_transaction.py` implements the centralized write-transaction boundary, router alias resolution and pinning, SQL phase/alias containment guards, pre-save row substitution and drift detection, and disappearing-row conflict resolution ([spec-036][spec-036], [spec-040][spec-040], [spec-046][spec-046]).

It owns the following architectural responsibilities:

1. **Transaction & Context State Management:**
   - Context variables & messages: [`_MANAGED_WRITE_ALIAS`][utils-write-transaction], [`_WRITE_PIPELINE`][utils-write-transaction], and [`_UNMANAGED_SCHEMA_MESSAGE`][utils-write-transaction].
   - Context record: [`WriteAliasContext`][utils-write-transaction] (`django_strawberry_framework/utils/write_transaction.py::WriteAliasContext` with `django_strawberry_framework/utils/write_transaction.py::WriteAliasContext.alias`, `django_strawberry_framework/utils/write_transaction.py::WriteAliasContext.auth_aliases`, `django_strawberry_framework/utils/write_transaction.py::WriteAliasContext.auth_phase`, `django_strawberry_framework/utils/write_transaction.py::WriteAliasContext.authorized_pk`, `django_strawberry_framework/utils/write_transaction.py::WriteAliasContext.lock`, `django_strawberry_framework/utils/write_transaction.py::WriteAliasContext.target_state`, `django_strawberry_framework/utils/write_transaction.py::WriteAliasContext.write_phase`, `django_strawberry_framework/utils/write_transaction.py::WriteAliasContext.__init__`).
   - Context managers: [`managed_write_transaction`][utils-write-transaction] (`django_strawberry_framework/utils/write_transaction.py::managed_write_transaction`), [`write_pipeline`][utils-write-transaction] (`django_strawberry_framework/utils/write_transaction.py::write_pipeline`), [`open_write_pipeline`][utils-write-transaction] (`django_strawberry_framework/utils/write_transaction.py::open_write_pipeline`), and [`pipeline_write_phase`][utils-write-transaction] (`django_strawberry_framework/utils/write_transaction.py::pipeline_write_phase`).
   - Pipeline state accessors: [`require_managed_write`][utils-write-transaction] (`django_strawberry_framework/utils/write_transaction.py::require_managed_write`), [`current_write_pipeline`][utils-write-transaction] (`django_strawberry_framework/utils/write_transaction.py::current_write_pipeline`), and [`require_write_pipeline`][utils-write-transaction] (`django_strawberry_framework/utils/write_transaction.py::require_write_pipeline`).

2. **Authorization Phase & Read-Only Barrier:**
   - Barrier constants: [`_READ_ONLY_BARRIER_VENDORS`][utils-write-transaction].
   - Barrier enforcer: [`_enforce_read_only_barrier`][utils-write-transaction] (`django_strawberry_framework/utils/write_transaction.py::_enforce_read_only_barrier`).
   - Phase context manager: [`authorization_phase`][utils-write-transaction] (`django_strawberry_framework/utils/write_transaction.py::authorization_phase`).

3. **SQL Statement Classification & Alias Guards:**
   - SQL classification constants: [`_READ_ONLY_SQL_PREFIXES`][utils-write-transaction].
   - Lexical token parser: [`_sql_statement_token`][utils-write-transaction] (`django_strawberry_framework/utils/write_transaction.py::_sql_statement_token`) and [`is_read_only_sql`][utils-write-transaction] (`django_strawberry_framework/utils/write_transaction.py::is_read_only_sql`).
   - Signal and execution guards: [`make_cross_alias_save_guard`][utils-write-transaction] (`django_strawberry_framework/utils/write_transaction.py::make_cross_alias_save_guard`) and [`pipeline_alias_guard`][utils-write-transaction] (`django_strawberry_framework/utils/write_transaction.py::pipeline_alias_guard`).

4. **Router Resolution & Queryset Pinning:**
   - Router resolution: [`resolve_write_alias`][utils-write-transaction] (`django_strawberry_framework/utils/write_transaction.py::resolve_write_alias`).
   - Queryset pinning & re-routing check: [`pin_write_queryset`][utils-write-transaction] (`django_strawberry_framework/utils/write_transaction.py::pin_write_queryset`) and [`check_instance_write_alias`][utils-write-transaction] (`django_strawberry_framework/utils/write_transaction.py::check_instance_write_alias`).
   - Locking helpers: [`base_locked_queryset`][utils-write-transaction] (`django_strawberry_framework/utils/write_transaction.py::base_locked_queryset`) and [`pipeline_scoped_queryset`][utils-write-transaction] (`django_strawberry_framework/utils/write_transaction.py::pipeline_scoped_queryset`).

5. **Canonical PK & Row Substitution Backstops:**
   - Canonical PK coercion: [`canonical_pk`][utils-write-transaction] (`django_strawberry_framework/utils/write_transaction.py::canonical_pk`) and [`pks_match`][utils-write-transaction] (`django_strawberry_framework/utils/write_transaction.py::pks_match`).
   - Row substitution rejection: [`reject_substituted_row`][utils-write-transaction] (`django_strawberry_framework/utils/write_transaction.py::reject_substituted_row`).

6. **Target State Snapshotting & Drift Detection:**
   - Snapshot types & budget: [`_MUTABLE_SNAPSHOT_TYPES`][utils-write-transaction] and [`_SNAPSHOT_NODE_BUDGET`][utils-write-transaction].
   - Structural records: [`_FileNameSnapshot`][utils-write-transaction] (`django_strawberry_framework/utils/write_transaction.py::_FileNameSnapshot` with `django_strawberry_framework/utils/write_transaction.py::_FileNameSnapshot.name`, `django_strawberry_framework/utils/write_transaction.py::_FileNameSnapshot.__init__`), [`_SnapshotClose`][utils-write-transaction] (`django_strawberry_framework/utils/write_transaction.py::_SnapshotClose` with `django_strawberry_framework/utils/write_transaction.py::_SnapshotClose.token`, `django_strawberry_framework/utils/write_transaction.py::_SnapshotClose.__init__`), and [`_FieldFingerprint`][utils-write-transaction] (`django_strawberry_framework/utils/write_transaction.py::_FieldFingerprint` with `django_strawberry_framework/utils/write_transaction.py::_FieldFingerprint.digest`, `django_strawberry_framework/utils/write_transaction.py::_FieldFingerprint.__init__`).
   - Fingerprint & snapshot builders: [`_field_fingerprint`][utils-write-transaction] (`django_strawberry_framework/utils/write_transaction.py::_field_fingerprint`), [`_snapshot_field_value`][utils-write-transaction] (`django_strawberry_framework/utils/write_transaction.py::_snapshot_field_value`), and [`snapshot_target_state`][utils-write-transaction] (`django_strawberry_framework/utils/write_transaction.py::snapshot_target_state`).
   - Target drift assertion: [`assert_no_target_drift`][utils-write-transaction] (`django_strawberry_framework/utils/write_transaction.py::assert_no_target_drift`).

7. **Conflict Mapping & Forced Update Disambiguation:**
   - Conflict error builder: [`conflict_error`][utils-write-transaction] (`django_strawberry_framework/utils/write_transaction.py::conflict_error`).
   - Version-aware exception resolver: [`not_updated_exceptions`][utils-write-transaction] (`django_strawberry_framework/utils/write_transaction.py::not_updated_exceptions`).
   - Disappearing-row conflict handler: [`forced_update_conflict_errors`][utils-write-transaction] (`django_strawberry_framework/utils/write_transaction.py::forced_update_conflict_errors`).

Connected behavior examined:
- [`django_strawberry_framework/mutations/base.py`][mutations-base]: Model mutation pipeline coordination, managed transaction checks, and alias guarding.
- [`django_strawberry_framework/forms/resolvers.py`][forms-resolvers]: Form mutation pipeline execution and alias containment.
- [`django_strawberry_framework/rest_framework/resolvers.py`][rest-framework-resolvers]: Serializer mutation execution, drift assertion, and save witness.
- [`django_strawberry_framework/utils/querysets.py`][utils-querysets]: Relation visibility queryset pinning and row locking via `pipeline_scoped_queryset`.
- [`django_strawberry_framework/schema.py`][schema]: Execution context managing completion-spanning atomic transaction.
- [`tests/mutations/`][tests-mutations]: Test suite validating atomic boundaries, cross-alias rejection, and drift detection.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/utils/write_transaction.py --include-constants`):
- Parsed 1 target file, 1036 lines.
- Complete inventory across all 53 definitions / constants.

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   `utils/write_transaction.py` establishes the unified transactional and security discipline across Model, ModelForm, and DRF Serializer mutations:
   - `open_write_pipeline` provides the single nesting structure (`require_managed_write` + `transaction.atomic` + `write_pipeline`) for all mutation execution.
   - `pipeline_alias_guard` uniformly polices SQL across all database connections and execution phases.
   - `assert_no_target_drift` prevents in-memory corruption before `serializer.save()`.
   - `forced_update_conflict_errors` normalizes disappearing row error mapping across Django 5.2 and 6.0+.

2. **Sync and async twins:**
   Database transactions, router resolution, signal registration, and connection wrappers are synchronous Django ORM operations; `_MANAGED_WRITE_ALIAS` and `_WRITE_PIPELINE` are `ContextVar`s that safely propagate across `sync_to_async` thread boundaries.

3. **Derived rather than repeated knowledge:**
   - `resolve_write_alias` derives the write alias once per mutation operation.
   - `_field_fingerprint` iteratively builds deterministic digests without recursive stack exhaustion.
   - `base_locked_queryset` reduces consumer visibility querysets into `pk__in` subqueries to avoid invalid `FOR UPDATE` joins.

4. **Inverse and round-trip pairs:**
   - `managed_write_transaction`, `write_pipeline`, `pipeline_write_phase`, and `authorization_phase` follow strict RAII context manager semantics with state restoration in `finally` blocks.
   - `_enforce_read_only_barrier` captures prior SQLite connection flags and reliably restores them via disarm callbacks.

5. **Contracts restated in another medium:**
   Codified across:
   - Code: [`django_strawberry_framework/utils/write_transaction.py`][utils-write-transaction], [`django_strawberry_framework/mutations/base.py`][mutations-base], [`django_strawberry_framework/forms/resolvers.py`][forms-resolvers], [`django_strawberry_framework/rest_framework/resolvers.py`][rest-framework-resolvers], [`django_strawberry_framework/schema.py`][schema];
   - Specifications: [`docs/SPECS/spec-036-mutation_visibility_contracts-0_0_10.md`][spec-036], [`docs/SPECS/spec-040-bulk_mutations-0_0_12.md`][spec-040], [`docs/SPECS/spec-046-composite_pk_support-0_0_14.md`][spec-046];
   - Test suites: [`tests/mutations/`][tests-mutations], [`tests/forms/`][tests-forms], [`tests/rest_framework/`][tests-rest-framework];
   - Documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree].

### The single-edit-site test

- **Posited change 1 (Supporting a new database vendor for the read-only authorization barrier):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/utils/write_transaction.py`][utils-write-transaction] ([`_READ_ONLY_BARRIER_VENDORS`][utils-write-transaction] and [`_enforce_read_only_barrier`][utils-write-transaction]).
  - *Propagation count:* 0 in other source files.
- **Posited change 2 (Adjusting the iterative snapshot node budget or serialization format):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/utils/write_transaction.py`][utils-write-transaction] ([`_SNAPSHOT_NODE_BUDGET`][utils-write-transaction] and [`_field_fingerprint`][utils-write-transaction]).
  - *Propagation count:* 0 in other source files.
- **Posited change 3 (Modifying the disallowed SQL statement prefixes in the read-only phase):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/utils/write_transaction.py`][utils-write-transaction] ([`_READ_ONLY_SQL_PREFIXES`][utils-write-transaction]).
  - *Propagation count:* 0 in other source files.

### Rejected candidates

1. **Attaching `select_for_update()` directly to consumer-provided querysets:**
   - Disproved per [spec-036][spec-036]. Arbitrary consumer querysets with annotations or joins cause backend SQL syntax errors when combined with `FOR UPDATE`.

## Opportunities

None — `django_strawberry_framework/utils/write_transaction.py` is fully consolidated at root owners.

## Judgment

Verified. `utils/write_transaction.py` exhibits zero duplicate code and complete policy consolidation across database write transaction management, cross-alias containment, and pre-save verification. All 5 axes of the mandatory duplication probing matrix are verified and discharged. Single-edit-site counts hold at 1 for all posited changes.

## Implementation (Worker 1)

Target verified clean and fully consolidated at root owners. Completeness verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/utils/write_transaction.py --review docs/dry/dry-file-utils__write_transaction.md --include-constants`. Setting `Status: verified`.

## Independent verification (Worker 2)

Worker 2 performed an independent audit of [`django_strawberry_framework/utils/write_transaction.py`][utils-write-transaction] and Worker 1's DRY review.

1. **Transaction Lifecycle & Security Containment:**
   - Confirmed `require_managed_write` strictly validates that mutations execute within `DjangoSchema` completion-spanning atomic transactions.
   - Confirmed `pipeline_alias_guard` and `authorization_phase` cleanly isolate non-pinned auth database queries within rolled-back read-only barriers.
   - Confirmed `snapshot_target_state` and `assert_no_target_drift` iteratively fingerprint mutable attributes, preventing unauthorized in-memory state mutations.
2. **Matrix & Single-Edit-Site Verification:**
   - Probed all 5 duplication matrix axes and confirmed all justifications are sound.
   - Verified single-edit-site counts hold at 1 for all posited changes.
3. **Static Check:**
   - Verified with `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/utils/write_transaction.py --review docs/dry/dry-file-utils__write_transaction.md --include-constants`. 100% coverage across all 53 definitions / constants.

Confirmed: `django_strawberry_framework/utils/write_transaction.py` satisfies all DRY requirements with zero code changes needed.

<!-- LINK DEFINITIONS -->

<!-- docs/ -->
[glossary]: ../GLOSSARY.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-036]: ../SPECS/spec-036-mutation_visibility_contracts-0_0_10.md
[spec-040]: ../SPECS/spec-040-bulk_mutations-0_0_12.md
[spec-046]: ../SPECS/spec-046-composite_pk_support-0_0_14.md

<!-- package source -->
[forms-resolvers]: ../../django_strawberry_framework/forms/resolvers.py
[mutations-base]: ../../django_strawberry_framework/mutations/base.py
[rest-framework-resolvers]: ../../django_strawberry_framework/rest_framework/resolvers.py
[schema]: ../../django_strawberry_framework/schema.py
[utils-querysets]: ../../django_strawberry_framework/utils/querysets.py
[utils-write-transaction]: ../../django_strawberry_framework/utils/write_transaction.py

<!-- tests -->
[tests-forms]: ../../tests/forms/
[tests-mutations]: ../../tests/mutations/
[tests-rest-framework]: ../../tests/rest_framework/
