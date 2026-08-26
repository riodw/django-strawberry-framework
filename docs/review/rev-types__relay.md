# Review: `django_strawberry_framework/types/relay.py`

Status: verified

## Understanding

`django_strawberry_framework/types/relay.py` owns the Relay integration machinery for `DjangoType` definitions across class-creation, schema finalization, and runtime query execution phases:

1. **Class-Creation Phase (`__init_subclass__`)**:
   - `install_is_type_of(type_cls: type)`: Installs concrete type resolution for Strawberry interface dispatch. Respects `_NODE_TYPE_HINT_ATTR` on fetched model instances to disambiguate multi-type models sharing the same underlying Django model, while defensively handling hostile descriptors. Preserves consumer-declared `is_type_of` via `cls.__dict__` membership.

2. **Finalization Phase 2.5 (`finalize_django_types`)**:
   - `implements_relay_node(type_cls: type)`: Evaluates `issubclass(type_cls, relay.Node)` across registration and finalization steps.
   - `apply_interfaces(type_cls: type, definition: DjangoTypeDefinition)`: Injects uninherited interfaces from `definition.interfaces` into `type_cls.__bases__`, wrapping Python MRO resolution failures into user-friendly `ConfigurationError` diagnostics.
   - `_check_composite_pk_for_relay_node(type_cls: type)`: Gates models with `CompositePrimaryKey` against `relay.Node` unless an explicit `id: relay.NodeID[...]` annotation is declared.
   - `install_relay_node_resolvers(type_cls: type)`: Resolves and stamps the ID attribute once on `_dsf_relay_id_attr` to eliminate redundant per-row MRO annotation rescans; injects the four Relay resolver defaults (`resolve_id`, `resolve_id_attr`, `resolve_node`, `resolve_nodes`) via `__func__` identity comparison against `relay.Node`.
   - `install_globalid_typename_resolver(type_cls, definition, globalid_setting)`: Resolves the effective GlobalID strategy using three-tier precedence (`Meta.globalid_strategy` -> schema-wide setting snapshot -> `"model"` default), handles re-entrancy, detects conflicting override configurations, and installs framework closures stamped with `_FRAMEWORK_CLOSURE_MARKER`.

3. **GlobalID Encoding & Decoding**:
   - `encode_typename(definition, strategy, type_cls, root)`: Computes the typename slot (`model`, `type`, `type+model`, or custom callable), enforcing non-empty string return values and normalizing string subclasses.
   - `decode_global_id(gid: relay.GlobalID | str)`: Decodes `GlobalID` instances or strings to `(DjangoType, node_id)`, verifying base64 integrity, extracting non-empty tokens, routing via Django model registry or GraphQL type name, and enforcing strategy compatibility (`_accepts_model_label_decode` and `_accepts_type_name_decode`).

4. **Node Resolution Defaults**:
   - `_resolve_node_default` and `_resolve_node_async`: Dispatches single-node queries with `get_queryset` visibility filtering and async context support via `in_async_context()`.
   - `_resolve_nodes_default` and `_resolve_nodes_async`: Handles plural queries, returning unfiltered querysets when `node_ids=None` or order-preserving node lists via `_order_nodes`, raising `Model.DoesNotExist` when `required=True` on missing records.

## Verification

1. **Static & Structural Audit**:
   - Verified lifecycle separation: class creation (`install_is_type_of`), finalization Phase 2.5 (`apply_interfaces`, `_check_composite_pk_for_relay_node`, `install_relay_node_resolvers`, `install_globalid_typename_resolver`), and query execution (`decode_global_id`, `_resolve_node_default`, `_resolve_nodes_default`).
   - Confirmed cycle-safe in-function imports for `base.py`, `conf.py`, and `registry.py`.
   - Audited exception safety and typing bounds on all public and private functions.

2. **Scratch Experiments**:
   - Executed `docs/review/temp-tests/types_relay/test_scratch.py` validating `implements_relay_node`, `_order_nodes` (order matching, missing holes, `required=True` raising `DoesNotExist`), `_coerce_node_id`/`_coerce_node_ids`, and strategy predicate memberships (`MODEL_LABEL_STRATEGIES`, `TYPE_NAME_STRATEGIES`).

3. **Focused Test Execution**:
   - `uv run pytest tests/types/test_relay_interfaces.py tests/test_relay_node_field.py tests/test_relay_connection.py tests/testing/test_relay.py tests/optimizer/test_relay_id_projection.py --no-cov` (297 passed in 8.37s).

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

`django_strawberry_framework/types/relay.py` provides a comprehensive, robust, and well-tested foundation for Relay Node integration, interface injection, GlobalID strategy handling, and node query resolvers across sync and async contexts.

## Implementation (Worker 1)

- **Changed files:**
  - `None — zero-edit cycle` (Scoped diff against `12779c99` for `django_strawberry_framework/types/relay.py` is empty).
- **Permanent tests:**
  - Existing suite in `tests/types/test_relay_interfaces.py` (142 tests), `tests/test_relay_node_field.py` (52 tests), `tests/test_relay_connection.py` (67 tests), `tests/testing/test_relay.py` (30 tests), and `tests/optimizer/test_relay_id_projection.py` (6 tests) rigorously pin all Relay contracts, MRO injection, GlobalID strategies, hostile descriptors, and sync/async node resolvers.
- **Verification:**
  - `docs/review/temp-tests/types_relay/test_scratch.py` passed (4 tests).
  - Focused suite: `uv run pytest tests/types/test_relay_interfaces.py tests/test_relay_node_field.py tests/test_relay_connection.py tests/testing/test_relay.py tests/optimizer/test_relay_id_projection.py --no-cov` (297 passed in 8.37s).
- **Formatter & Linter:**
  - `None — zero-edit cycle` (no production changes).
- **Changelog:**
  - `None — zero-edit cycle`; no runtime behavior change or public API modification.

## Independent verification (Worker 2)

1. **Scoped Diff & Zero-Edit Confirmation**:
   - Confirmed `git diff 12779c99 -- django_strawberry_framework/types/relay.py` is empty (zero-edit cycle).

2. **Behavioral Re-trace & Static Audit**:
   - `install_is_type_of`: Verified `cls.__dict__` check to preserve explicit consumer declarations, extraction and evaluation of `_NODE_TYPE_HINT_ATTR` with catch-all defense against hostile descriptors, and reliable fallback to `isinstance(obj, (type_cls, model))`.
   - `implements_relay_node`: Verified `issubclass(type_cls, relay.Node)` checking across registration and Phase 2.5 finalization.
   - `apply_interfaces`: Verified filtering of interfaces already present in MRO, `__bases__` mutation, and conversion of layout/MRO errors into `ConfigurationError`.
   - `_check_composite_pk_for_relay_node`: Verified detection of `CompositePrimaryKey` on Django 5.2+ models, exempting models with explicit `relay.NodeID` annotations via `relay.Node.resolve_id_attr.__func__` scan catching `NodeIDAnnotationError`.
   - `install_relay_node_resolvers`: Verified `_stamp_relay_id_attr` one-time cache on `_dsf_relay_id_attr` slot to bypass per-row MRO annotation rescans and avoid inherited-cache collisions, and verified `__func__` identity comparison with `relay.Node` defaults to protect consumer method overrides.
   - `install_globalid_typename_resolver`: Verified 3-tier precedence (`Meta.globalid_strategy` -> schema-wide setting snapshot -> `"model"` default), re-entrancy safety via `definition.effective_globalid_strategy`, override conflict validation against explicit `Meta.globalid_strategy`, and closure tagging with `_FRAMEWORK_CLOSURE_MARKER`.
   - `encode_typename` and `decode_global_id`: Verified symmetric strategy mapping (`MODEL_LABEL_STRATEGIES`, `TYPE_NAME_STRATEGIES`), normalization of hostile string subclasses, fail-loud `ConfigurationError` handling on malformed base64 / invalid shapes / unregistered models, and enforcement that only permitted strategies decode.
   - `_resolve_node_default` and `_resolve_nodes_default`: Verified sync/async routing via `in_async_context()`, visibility filtering via `apply_type_visibility_sync`/`apply_type_visibility_async`, list order preservation in `_order_nodes`, and raising `Model.DoesNotExist` on missing records when `required=True`.

3. **Test Execution**:
   - Scratch tests: `uv run pytest docs/review/temp-tests/types_relay/test_scratch.py --no-cov` (4 passed).
   - Focused suite: `uv run pytest tests/types/test_relay_interfaces.py tests/test_relay_node_field.py tests/test_relay_connection.py tests/testing/test_relay.py tests/optimizer/test_relay_id_projection.py --no-cov` (297 passed in 8.36s).

4. **Disposition of Findings**:
   - Zero findings; implementation is robust, adheres to all architectural boundaries and error contracts, and is fully verified.
