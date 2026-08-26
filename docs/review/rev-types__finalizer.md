# Review: `django_strawberry_framework/types/finalizer.py`

Status: verified

## Understanding

`django_strawberry_framework/types/finalizer.py` implements `finalize_django_types()`, the once-only build gate that processes all collected `DjangoType` definitions in `registry`, performs pre-decoration audits, attaches framework resolvers, validates interfaces and sidecar sets, synthesizes connections, and invokes `strawberry.type` decoration.

### Core Responsibilities & Pipeline Phases:

1. **Gate & Re-entrancy Lifecycle**:
   - Short-circuits immediately if `registry.is_finalized()` is `True`.
   - Flips `registry.mark_finalized()` only as the final statement after all phases succeed.
   - Preserves partial progress on intermediate errors, allowing safe in-place recovery on subsequent `finalize_django_types()` invocations via per-entry `if definition.finalized: continue` guards.

2. **Phase 1 (Failure-Atomic Target & Ambiguity Resolution)**:
   - Snapshot and validation of `RELAY_GLOBALID_STRATEGY` setting once per finalization. Re-validates against previous snapshot on retry to prevent mixed-strategy schemas.
   - Materializes `registry.models_with_multiple_types()` once for sharing between ambiguity and routing audits.
   - Rejects multi-type models lacking a primary type declaration via `_audit_primary_ambiguity`.
   - Iterates pending relations (`registry.iter_pending_relations()`), resolving targets against `registry.get(related_model)` and checking metadata.
   - Raises `ConfigurationError` (`_format_unresolved_targets_error`) if any target is unresolved before mutating any class annotations.
   - Rewrites relation annotations via `resolved_relation_annotation` and discards resolved pending records.

3. **Phase 2 (Resolver Attachment)**:
   - Attaches generated relation resolvers via `_attach_relation_resolvers`, skipping `consumer_assigned_relation_fields`.
   - Attaches generated file/image resolvers via `_attach_file_resolvers`, skipping `consumer_authored_fields`.

4. **Phase 2.5 (Interface, Relay, Sidecar Binding, Mutation, and Surface Audits)**:
   - Injects declared `Meta.interfaces` into `cls.__bases__` via `apply_interfaces`.
   - Checks composite PKs on Relay `Node` implementations via `_check_composite_pk_for_relay_node`.
   - Installs Relay Node resolvers (`resolve_id`, `resolve_node_id`, `resolve_node_type`, `resolve_reference`) and type name resolvers (`install_globalid_typename_resolver`).
   - Validates keyset cursor columns via `validate_cursor_field_columns`.
   - Validates that declared `DjangoNodeField` / `DjangoNodesField` require at least one Relay `Node` type.
   - Synthesizes `*_connection` relation fields for eligible many-side relations on Relay nodes (`_synthesize_relation_connections`) with collision detection and clean teardown registration.
   - Audits GlobalID model-label routing across multi-type models (`_audit_model_label_routing`) and logs warnings for secondary type collapse (`_warn_model_label_secondary_collapse`).
   - Pre-bind resets subsystem materialization ledgers (`iter_subsystem_clears(before_bind=True)`).
   - Binds mutations (`bind_auth_mutations`, `bind_mutations`, `bind_form_mutations`).
   - Executes 4-subpass sidecar binding for `FilterSet` (`_bind_filtersets`) and `OrderSet` (`_bind_ordersets`) via shared driver `_bind_sidecar_sets` and spec `_SidecarBindingSpec`:
     - Subpass 1: Bind owner definition (`_bind_set_owner_common` with model compatibility and target agreement checks; filterset additionally checks own-PK Relay identity and `get_queryset` scoping safety).
     - Subpass 2: Expand set fields and resolve lazy class references.
     - Subpass 2.5: FilterSet-specific post-expansion audits (`_audit_unregistered_related_filter_targets` and `_audit_globalid_filter_strategies`).
     - Subpass 3: Validate orphan sets referenced in input helpers (`filter_input_type`, `order_input_type`) but not wired to any `DjangoType`.
     - Subpass 4: Materialize generated input types into module globals.
   - Pre-decoration surface audit (`_audit_field_surface`): validates non-empty GraphQL field surface and detects camel-case name collisions across inherited and own fields.

5. **Phase 3 (Decoration & Finalization)**:
   - Invokes `strawberry.type(type_cls, name=definition.name, description=definition.description)`.
   - Flags `definition.finalized = True`.
   - Concludes with `registry.mark_finalized()`.

## Verification

1. **Static and Structural Audit**:
   - Examined all 2,014 lines of `django_strawberry_framework/types/finalizer.py`.
   - Verified that DRY consolidations between `FilterSet` and `OrderSet` binding (`_bind_set_owner_common`, `_SidecarBindingSpec`, `_bind_sidecar_sets`, `_format_owner_set_model_mismatch_error`, `_format_orphan_sets_error`, `_format_owner_target_mismatch_error`) maintain distinct error messages and strict family invariants.
   - Verified that hostile metadata handlers (`_safe_class_name`, `_safe_qualified_class_name`, `_safe_field_label`, `_safe_str`, `_annotation_names`) prevent unhandled exceptions during diagnostic formatting.
   - Checked re-entrancy and teardown handling in `_synthesize_relation_connections` across partial runs and `registry.clear()`.

2. **Existing Test Suite Audit**:
   - `tests/types/test_finalizer.py` (16 tests covering hostile model/string/annotation handling, malformed annotation keys, pending relation diagnostics, model-label routing audits, and secondary owner mismatches).
   - `tests/filters/test_finalizer.py` (29 tests covering FilterSet 4-subpass binding, multi-owner target/PK/get_queryset checks, orphan validation, and GlobalID filter strategy validation).
   - `tests/orders/test_finalizer.py` (21 tests covering OrderSet binding, model compatibility, multi-owner target checks, and orphan validation).
   - `tests/test_connection.py`, `tests/test_keyset_connection.py`, and `tests/test_relay_connection.py` (187 tests verifying relation connection synthesis, pagination, and teardown).

3. **Focused Test Executions**:
   - `uv run pytest tests/types/test_finalizer.py --no-cov` (16 passed in 2.27s).
   - `uv run pytest tests/filters/test_finalizer.py tests/orders/test_finalizer.py --no-cov` (50 passed in 2.13s).
   - `uv run pytest tests/test_connection.py tests/test_keyset_connection.py tests/test_relay_connection.py --no-cov` (187 passed in 7.03s).

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

`django_strawberry_framework/types/finalizer.py` is an exceptionally well-engineered, robust finalization gate. It strictly maintains failure-atomicity in Phase 1, isolates sidecar and relation lifecycle states, defends against hostile/malformed metadata across all diagnostic formatters, and provides unified, DRY-compliant sidecar binding with comprehensive multi-owner safety guarantees.

## Implementation (Worker 1)

None — zero-edit cycle.

- **Changed files:**
  - None (scoped diff against HEAD is empty).
- **Permanent tests:**
  - Existing suite (`tests/types/test_finalizer.py`, `tests/filters/test_finalizer.py`, `tests/orders/test_finalizer.py`, `tests/test_connection.py`) fully covers all lifecycle, safety, and diagnostic invariants.
- **Verification:**
  - `uv run pytest tests/types/test_finalizer.py --no-cov` (16 passed).
  - `uv run pytest tests/filters/test_finalizer.py tests/orders/test_finalizer.py --no-cov` (50 passed).
  - `uv run pytest tests/test_connection.py tests/test_keyset_connection.py tests/test_relay_connection.py --no-cov` (187 passed).
- **Formatter & Linter:**
  - N/A (zero-edit cycle).
- **Changelog:**
  - No changes; no changelog entry required.

## Independent verification (Worker 2)

- **Behavior and Path Re-tracing:**
  - Re-traced `finalize_django_types()` lifecycle and re-entrancy: verified `registry.is_finalized()` top gate, per-entry `if definition.finalized: continue` recovery loops across phases, and terminal `registry.mark_finalized()`.
  - Re-traced Phase 1 failure-atomic target resolution and primary ambiguity audit: verified `_audit_primary_ambiguity` validation against multi-type models, `RELAY_GLOBALID_STRATEGY` setting snapshot consistency, pending relation inspection (`registry.iter_pending_relations()`), failure-atomic `_format_unresolved_targets_error` before class mutation, and subsequent relation annotation rewrite via `resolved_relation_annotation`.
  - Re-traced Phase 2 resolver attachment: confirmed `_attach_relation_resolvers` and `_attach_file_resolvers` skipping consumer-assigned/consumer-authored fields.
  - Re-traced Phase 2.5 interface injection and Relay Node resolvers: verified `apply_interfaces` injecting `cls.__bases__`, composite PK checks (`_check_composite_pk_for_relay_node`), installation of Relay Node resolvers (`resolve_id`, `resolve_node_id`, `resolve_node_type`, `resolve_reference`), typename resolver installation (`install_globalid_typename_resolver`), and cursor field column validations (`validate_cursor_field_columns`).
  - Re-traced connection synthesis (`_synthesize_relation_connections`): verified creation of `<field>_connection` relation fields for eligible many-side relations, collision detection against consumer-defined fields, and registration of clean per-type teardown handlers (`_register_relation_connection_teardown`).
  - Re-traced GlobalID model-label routing and secondary collapse audits: verified `_audit_model_label_routing` and `_warn_model_label_secondary_collapse`.
  - Re-traced mutation binding: verified pre-bind subsystem clears (`iter_subsystem_clears(before_bind=True)`), followed by `bind_auth_mutations`, `bind_mutations`, and `bind_form_mutations`.
  - Re-traced unified 4-subpass sidecar binding (`_bind_sidecar_sets`, `_bind_filtersets`, `_bind_ordersets`): verified owner binding (`_bind_set_owner_common`), multi-owner model compatibility, target alignment, FilterSet-specific PK identity / `get_queryset` scoping checks, recursive field expansion, post-expansion audits (`_audit_unregistered_related_filter_targets`, `_audit_globalid_filter_strategies`), orphan set rejection (`_format_orphan_sets_error`), and input class module global materialization.
  - Re-traced pre-decoration surface audit (`_audit_field_surface`): verified non-empty GraphQL field surface enforcement and camel-case name collision detection.
  - Re-traced Phase 3 decoration: verified `strawberry.type` application, `definition.finalized = True`, and final `registry.mark_finalized()`.
- **Scoped Diff Verification:**
  - Verified empty diff against baseline `12779c99` (`git diff 12779c99 -- django_strawberry_framework/types/finalizer.py`).
- **Test Executions:**
  - `uv run pytest tests/types/test_finalizer.py --no-cov`: 16 passed.
  - `uv run pytest tests/filters/test_finalizer.py tests/orders/test_finalizer.py --no-cov`: 50 passed.
  - `uv run pytest tests/test_connection.py --no-cov`: 137 passed.
- **Disposition:**
  - Zero findings confirmed. Implementation is robust, well-architected, and fully verified. Status set to `verified`.

