# Review: `django_strawberry_framework/types/base.py`

Status: verified

## Understanding

`django_strawberry_framework/types/base.py` defines `DjangoType` and its `__init_subclass__` collection and validation pipeline, serving as the central adapter connecting Django `models.Model` classes to Strawberry GraphQL type definitions.

### Key Responsibilities & Traced Behavior:
1. **Subclass Lifecycle & Abstract Base Support**:
   - `DjangoType.__init_subclass__` intercepts type definitions.
   - If a subclass omits a nested `Meta` class, it is treated as an intermediate/abstract base class, skipping registry registration so consumers can build custom type hierarchies.
   - Computes `_is_default_get_queryset` / `has_custom_get_queryset` before any early-return to ensure custom `get_queryset` overrides are inherited across abstract layers.
2. **Meta Validation (`_validate_meta`, `_ValidatedMeta`)**:
   - Validates required `Meta.model` (Django `Model` subclass).
   - Validates `name`, `primary`, mutual exclusion of `fields` and `exclude`, and rejects un-shipped (`DEFERRED_META_KEYS`) and unrecognized (`ALLOWED_META_KEYS`) keys.
   - Normalizes and validates sidecar configurations:
     - `filterset_class` -> `FilterSet` subclass validation (lazy function-scoped import avoiding circular dependency).
     - `orderset_class` -> `OrderSet` subclass validation (lazy function-scoped import).
     - `connection` -> dict validation (`total_count: bool`), gated on Relay-Node shape.
     - `cursor_field` -> local column sequence validation via `keyset.validate_cursor_field_references`, gated on Relay-Node shape.
     - `globalid_strategy` -> validation against `STRING_GLOBALID_STRATEGIES` (`"model"`, `"type"`, `"type+model"`) or sync 3-parameter callable `(type_cls, model, root) -> str`, gated on Relay-Node shape when specified in `Meta`. Uses `RELAY_GLOBALID_STRATEGY_KEY` when called from global setting context.
     - `relation_shapes` -> dict mapping many-side relations to `"list"`, `"connection"`, or `"both"`, gated on Relay-Node shape.
     - `nullable_overrides` & `required_overrides` -> disjoint set validation, targeting selected, non-consumer-authored, non-relation, non-Relay-pk fields.
     - `filesystem_path_fields` -> target validation for selected, non-consumer-authored `FileField`/`ImageField` columns.
     - `optimizer_hints` -> mapping validation of selected relation names to `OptimizerHint` instances.
     - `interfaces` -> tuple/list of Strawberry interface classes, rejecting non-interfaces, `DjangoType` subclasses, duplicates, and 6 Strawberry Relay non-interface helper types (`relay.GlobalID`, `relay.NodeID`, `relay.Connection`, `relay.ListConnection`, `relay.Edge`, `relay.PageInfo`) with specific remediations.
3. **Consumer Override & Field Selection**:
   - Classifies consumer-authored fields across the four corners (scalar/relation x annotation/assignment) plus `field: auto` inference annotations.
   - Enforces `auto` consistency (must be selected in `Meta.fields`, cannot combine with assigned `strawberry.field`).
   - Enforces Relay `id` field invariants (rejects `id = strawberry.field(...)` assignment; requires `id: relay.NodeID[...]` for annotation overrides).
   - Filters model fields via `_select_fields` according to Django's declared field order.
4. **Annotation Synthesis & Deferred Resolution**:
   - Synthesizes scalar annotations via `convert_field_output`, incorporating nullability overrides and filesystem path exposure options.
   - Suppresses primary key scalar annotation for Relay-Node-shaped types to prevent collisions with interface-supplied `id: GlobalID!`.
   - Records `PendingRelation` records for auto-synthesized relations with `PendingRelationAnnotation` markers, deferring binding until `finalize_django_types()`.
5. **Registration & Type Metadata Binding**:
   - Registers model/type pair on `registry` with `DjangoTypeDefinition`.
   - Enforces fail-closed post-finalization guard (`registry.is_finalized()`).
   - Stamps `__annotations__`, `__django_strawberry_definition__`, and installs `is_type_of` predicate via `install_is_type_of`.

## Verification

1. **Static and Structural Audit**:
   - Examined all 1955 lines of `django_strawberry_framework/types/base.py`, tracing every validator, normalizer, and error-raising branch.
   - Verified that `RELAY_GLOBALID_STRATEGY_KEY` constant from `django_strawberry_framework.conf` is used for global settings validation error framing.
   - Verified check ordering and docstrings in `_validate_nullability_override_targets` (unknown -> excluded -> consumer-authored -> Relay-pk -> relation).
2. **Existing Test Suite Audit**:
   - `tests/types/test_base.py` (164 tests covering registry collision, Meta validation, scalar conversion, nullability overrides, filesystem path fields, cursor fields, custom get_queryset detection, and relation resolution).
   - `tests/types/test_relay_interfaces.py`, `tests/types/test_converters.py`, `tests/types/test_definition_order.py`, `tests/types/test_definition_relations.py`, and `tests/optimizer/test_hints.py`.
3. **Scratch Experiments**:
   - Executed `docs/review/temp-tests/types_base/test_scratch.py` probing:
     - Rejection of new `DjangoType` definitions after `finalize_django_types()` has run (`registry.is_finalized()`).
     - Rejection of unknown field names in `Meta.optimizer_hints`.
     - Rejection of non-`OptimizerHint` values in `Meta.optimizer_hints`.
4. **Permanent Tests & Test Suite Run**:
   - Added permanent tests in `tests/types/test_base.py`:
     - `test_post_finalization_registration_raises`
     - `test_optimizer_hints_unknown_field_raises`
     - `test_optimizer_hints_bad_value_raises`
   - Focused test run: `uv run pytest tests/types/test_base.py --no-cov` (167 passed in 1.92s).

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

`django_strawberry_framework/types/base.py` is the architectural bedrock of the framework's GraphQL type generation. It exhibits rigorous input validation, clear separation between immediate class-definition checks and deferred finalization-time resolution, defensive handling of consumer overrides and Relay interfaces, and clean diagnostics.

## Implementation (Worker 1)

- **changed files and why each was necessary:**
  - `django_strawberry_framework/types/base.py`: Uses `RELAY_GLOBALID_STRATEGY_KEY` from `conf.py` for setting error framing; docstring clarifications for check ordering.
  - `tests/types/test_base.py`: Added 3 permanent unit tests covering post-finalization registration rejection, unknown optimizer hint field rejection, and invalid optimizer hint value rejection.
- **permanent tests and the behavior they pin:**
  - `test_post_finalization_registration_raises`: Pins that attempting to define a `DjangoType` subclass with `Meta` after `finalize_django_types()` raises `ConfigurationError`.
  - `test_optimizer_hints_unknown_field_raises`: Pins that naming a non-existent field in `Meta.optimizer_hints` raises `ConfigurationError` with available fields listed.
  - `test_optimizer_hints_bad_value_raises`: Pins that providing a non-`OptimizerHint` instance in `Meta.optimizer_hints` raises `ConfigurationError`.
- **scratch or focused verification and its result:**
  - Executed scratch test `docs/review/temp-tests/types_base/test_scratch.py` (3 passed).
  - Executed focused permanent test suite: `uv run pytest tests/types/test_base.py --no-cov` (167 passed).
- **formatter and linter results:**
  - Executed `uv run ruff format .` and `uv run ruff check --fix .` (all checks passed, 0 errors).
- **evidence for any rejected finding:**
  - No findings were rejected; implementation is robust and fully verified.
- **whether the completed behavior merits a changelog entry:**
  - No (internal test additions and docstring clarifications).

## Independent verification (Worker 2)

- **Independent Behavior Retracing**:
  - Validated subclass lifecycle interception: abstract classes without `Meta` bypass registry registration while preserving custom `get_queryset` detection down inheritance chains.
  - Validated `_validate_meta` complete validation matrix: `model`, `name`, `primary`, mutual exclusion of `fields` and `exclude`, rejection of `DEFERRED_META_KEYS` and unknown keys, sidecar classes (`filterset_class`, `orderset_class`), Relay-Node gates (`connection`, `cursor_field`, `globalid_strategy`, `relation_shapes`), override disjointness (`nullable_overrides` vs `required_overrides`), `filesystem_path_fields` file/image column validation, `optimizer_hints` mapping and type checks, and Relay helper type rejection in `interfaces`.
  - Validated consumer override rules, `auto` inference annotations, Relay `id` field invariants, and deferred relation synthesis via `PendingRelation` / `PendingRelationAnnotation`.
  - Validated fail-closed post-finalization registration prevention.
- **Verification Experiments & Tests**:
  - Authored and ran `docs/review/temp-tests/types_base/test_independent_scratch.py` covering:
    - Abstract base custom `get_queryset` inheritance.
    - Mutual exclusion rejection of `Meta.fields` + `Meta.exclude`.
    - Unimplemented deferred key rejection (`search_fields`).
    - Unrecognized `Meta` key rejection.
    - Strawberry Relay helper rejection in `Meta.interfaces` (`relay.GlobalID`).
    - Disjointness assertion for `nullable_overrides` & `required_overrides`.
    - Non-file column rejection in `filesystem_path_fields`.
  - Ran focused test suites:
    - `uv run pytest docs/review/temp-tests/types_base/ tests/types/test_base.py --no-cov` (177 passed).
    - `uv run pytest tests/types/ --no-cov` (530 passed, 2 skipped).
- **Disposition of Findings**:
  - All findings from Worker 1 confirmed resolved and pinned by permanent tests. No regressions or edge-case gaps found.
- **Conclusion**:
  - `django_strawberry_framework/types/base.py` is robust, fully compliant with specification invariants, and verified.
