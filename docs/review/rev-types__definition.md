# Review: `django_strawberry_framework/types/definition.py`

Status: verified

## Understanding

`django_strawberry_framework/types/definition.py` defines the canonical `DjangoTypeDefinition` dataclass and its associated helper functions (`origin_has_custom_id_resolver`, `_resolves_id_off_pk`, `_class_has_custom_id_resolver`, `_is_framework_relay_id_resolver`, and `_normalize_pk_name`).

### Key Responsibilities & Traced Behavior:
1. **Canonical Type Metadata Record (`DjangoTypeDefinition`)**:
   - Built and populated exclusively during `DjangoType.__init_subclass__` (`types/base.py`).
   - Carries origin type, backing Django model, name, description, field and exclude specifications, selected Django model fields, field meta mapping (`field_map`), optimizer hints (`optimizer_hints`), custom `get_queryset` detection, consumer authored/annotated/assigned field frozensets, primary designation, interfaces, sidecar class references (`filterset_class`, `orderset_class`, `fields_class`), connection and keyset cursor configuration (`connection`, `cursor_field`), relation shape mappings (`relation_shapes`, `relation_connections`), and GlobalID strategies (`globalid_strategy`, `effective_globalid_strategy`).
   - Maintained as immutable post-construction across all consumers (registry, finalizer, optimizer walker, relation resolvers).
   - Dataclass equality (`d1 == d2`) is configured via `field(compare=False, repr=False)` to ignore private memoization caches (`_related_target_cache`, `_custom_id_resolver_cache`), preventing cyclic equality failures and cache pollution side effects.
2. **GraphQL Type Name Resolution (`graphql_type_name`)**:
   - Centralized property defining Strawberry's type name derivation (`self.name` fallback to `self.origin.__name__`).
   - Validates the resulting name against `_GRAPHQL_NAME_RE` (`^[_A-Za-z][_0-9A-Za-z]*$`) and rejects GraphQL reserved introspection prefixes (`__`) and empty or non-string names with typed `ConfigurationError` and safe diagnostics (`_safe_type_name`, `_safe_arg_repr`).
3. **Relation Target Resolution (`related_target_for`)**:
   - Resolves `(target_definition, model_field)` for a given model relation name.
   - Handles forward FKs, forward M2Ms, reverse FKs (via `ManyToOneRel`), OneToOne in both directions, scalar non-relation fields, missing fields, `GenericForeignKey` (no `related_model`), unregistered target types, and primary-wins target resolution (`registry.get(target_model)`).
   - Memoizes results in `_related_target_cache` post-finalization (`registry.is_finalized() == True`), ensuring fast repeated lookups during query planning and filter evaluation.
4. **Relay Custom ID Resolver Detection (`has_custom_id_resolver_for`, `origin_has_custom_id_resolver`)**:
   - Detects whether a `DjangoType` or Strawberry type overrides ID resolution away from the model primary key, used by the optimizer's FK-id elision optimization to safely bypass unnecessary joins.
   - Checks MRO class dictionaries for consumer `resolve_{pk_name}` or `resolve_id` methods, distinguishing consumer overrides from framework-installed Relay defaults (`_resolve_id_default`, `strawberry.relay.Node.resolve_id`).
   - Checks for `strawberry.relay.NodeID[...]` annotations targeting non-pk columns.
   - Memoizes check results per PK name on `DjangoTypeDefinition._custom_id_resolver_cache`.
   - Shared between `DjangoTypeDefinition.has_custom_id_resolver_for` and `optimizer/walker.py` definition-less fallback to ensure consistent behavior across registered and unregistered types.

## Verification

1. **Static and Structural Audit**:
   - Examined all lines of `django_strawberry_framework/types/definition.py`.
   - Traced callers and consumers across `types/base.py`, `types/finalizer.py`, `types/relay.py`, `types/resolvers.py`, `optimizer/walker.py`, `registry.py`, `filters/base.py`, `filters/inputs.py`, and `orders/inputs.py`.
   - Verified that `_GRAPHQL_NAME_RE` is reused by `types/base.py`.
   - Verified that private caches (`_related_target_cache`, `_custom_id_resolver_cache`) do not alter dataclass comparison or hash contracts.
2. **Existing Test Suite Audit**:
   - `tests/types/test_definition_relations.py` (23 tests covering `related_target_for` forward/reverse/M2M/OneToOne/GFK/unregistered/primary resolution and memoization, `graphql_type_name` formatting and invalid name rejections, `has_custom_id_resolver_for` memoization, default exemption, `NodeID` column tracking, and fail-closed hostile metadata handling).
3. **Scratch Experiments**:
   - Executed `docs/review/temp-tests/types_definition/test_scratch.py` probing hostile class metadata with broken `__class__` property during `isinstance(origin, type) and issubclass(origin, relay.Node)` inspection in `_resolves_id_off_pk`. Confirmed that unhandled exceptions escaped instead of failing closed to `True`.
4. **Focused Test Runs**:
   - `uv run pytest tests/types/test_definition_relations.py --no-cov` (23 passed in 1.62s).
   - `uv run pytest tests/types/test_base.py tests/types/test_definition_relations.py tests/types/test_finalizer.py --no-cov` (206 passed in 1.86s).

## Improvements

### High

None.

### Medium

None.

### Low

#### 1. Unhandled exception in `_resolves_id_off_pk` when inspecting hostile class metadata

- **Observation:** `_resolves_id_off_pk` evaluated `isinstance(origin, type) and issubclass(origin, relay.Node)` outside of exception handling, allowing unexpected metadata inspection errors (e.g., broken `__class__` or `__bases__`) to escape rather than failing closed to `True`.
- **Evidence:** Calling `origin_has_custom_id_resolver` with an object whose `__class__` property raised `RuntimeError` caused the exception to escape to the caller, in contrast to all other hostile metadata checks in `origin_has_custom_id_resolver` which catch exceptions and fail closed (`return True`).
- **Impact:** Unhandled exceptions during Relay Node identification could crash query planning and FK-id elision checks when encountering dynamic or hostile type descriptors.
- **Recommendation:** Wrap `isinstance(origin, type) and issubclass(origin, relay.Node)` in `try...except BaseException:` and fail closed (`return True`) on error.
- **Proof:** Unit test in `tests/types/test_definition_relations.py::test_custom_id_detection_fails_closed_for_hostile_class_metadata` asserting that `_HostileClassProperty` evaluates to `True`.

## Summary

`django_strawberry_framework/types/definition.py` provides a clean, robust, and centralized metadata representation for `DjangoType`. It effectively unifies GraphQL naming rules, relation target lookups, and Relay ID customization detection with strong fail-closed defenses and memoized query-path performance.

## Implementation (Worker 1)

- **Changed files:**
   - `django_strawberry_framework/types/definition.py`: wrapped `isinstance` and `issubclass` in `try...except BaseException:` within `_resolves_id_off_pk` to guarantee fail-closed handling on hostile class metadata.
   - `tests/types/test_definition_relations.py`: added test assertion in `test_custom_id_detection_fails_closed_for_hostile_class_metadata` pinning that an object with a broken `__class__` property fails closed to `True`.
- **Permanent tests:**
   - `tests/types/test_definition_relations.py::test_custom_id_detection_fails_closed_for_hostile_class_metadata` pins that hostile class inspection in `origin_has_custom_id_resolver` fails closed.
- **Verification:**
   - `uv run pytest tests/types/test_definition_relations.py --no-cov` (23 passed).
   - `uv run pytest tests/types/test_base.py tests/types/test_definition_relations.py tests/types/test_finalizer.py --no-cov` (206 passed).
- **Formatter & Linter:**
   - `uv run ruff format .` (clean).
   - `uv run ruff check --fix .` (clean, all checks passed).
- **Changelog:**
   - Internal robustness improvement for hostile class metadata handling; does not alter public API or merit a separate changelog entry.

## Independent verification (Worker 2)

- **Independent Behavior Retrace & Audit**:
  - `DjangoTypeDefinition` dataclass design:
    - Verified all metadata fields, defaults, immutable post-construction contracts, and usage across `types/base.py`, `types/finalizer.py`, `types/relay.py`, `types/resolvers.py`, and `optimizer/walker.py`.
    - Verified `field(compare=False, repr=False)` on `_related_target_cache` and `_custom_id_resolver_cache`, ensuring clean dataclass comparisons and preventing cyclic equality failures.
  - `graphql_type_name` property:
    - Verified derivation logic (`self.name` fallback to `self.origin.__name__`).
    - Verified validation against `_GRAPHQL_NAME_RE` (`^[_A-Za-z][_0-9A-Za-z]*$`) and rejection of `__` prefixes, non-strings, and empty strings with clear `ConfigurationError` messages and safe type/arg representations.
  - `related_target_for` method:
    - Verified relation target resolution covering forward FK, forward M2M, reverse FK (`ManyToOneRel`), OneToOne in both directions, scalar non-relation fields, missing fields, GFKs without `related_model`, and unregistered target types.
    - Verified primary target precedence (`registry.get(target_model)` honoring `_primaries`).
    - Verified memoization behavior: lookups are only cached when `registry.is_finalized() == True`, preventing stale caching of pre-finalization state.
    - Verified defensive degradation to `None` across malformed model `_meta`, unreadable fields, unreadable relation flags, and registry lookup exceptions.
  - Relay ID Customization Detection (`has_custom_id_resolver_for`, `origin_has_custom_id_resolver`, `_resolves_id_off_pk`, `_class_has_custom_id_resolver`, `_is_framework_relay_id_resolver`):
    - Verified detection of custom `resolve_id` and `resolve_{pk_name}` methods on origin and MRO.
    - Verified correct exemption of framework-installed Relay defaults (`_resolve_id_default` and `strawberry.relay.Node.resolve_id`).
    - Verified non-pk `relay.NodeID[...]` detection causing safe fail-over for FK-id elision.
    - Verified fail-closed behavior returning `True` (indicating custom resolver) across all hostile class metadata, unreadable MROs, unreadable `__dict__`, and dynamic descriptors with broken `__class__` properties.
    - Verified memoization in `_custom_id_resolver_cache` keyed by normalized PK name.
- **Independent Verification Scratch Test**:
  - Authored `docs/review/temp-tests/types_definition/test_independent_scratch.py` covering:
    - GraphQL type name derivation, valid/invalid identifiers, leading digit rejection, and reserved prefix rejection.
    - Dataclass equality ignoring private cache fields and cyclic references.
    - Related target resolution with pre-finalization bypass and post-finalization cache hits.
    - Complete custom ID resolver detection matrix (plain origin, custom resolve_id, custom resolve_uuid, framework relay default exemption, strawberry relay node exemption, pk vs slug NodeID annotations).
    - Hostile metadata fail-closed guarantees across `__class__`, `__mro__`, and `__dict__` exceptions.
- **Test Executions**:
  - `uv run pytest docs/review/temp-tests/types_definition/test_independent_scratch.py tests/types/test_definition_relations.py --no-cov` (28 passed in 1.66s).
  - `uv run pytest tests/types/test_base.py tests/types/test_definition_relations.py tests/types/test_finalizer.py --no-cov` (206 passed in 1.92s).
- **Target File Status**:
  - `django_strawberry_framework/types/definition.py` is fully verified and clean.
- **Conclusion**:
  - Implementation is robust, well-tested, adheres strictly to architecture and safety contracts, and satisfies all requirements. Status updated to `verified`.
