# Review: `django_strawberry_framework/types/relations.py`

Status: verified

## Understanding

`django_strawberry_framework/types/relations.py` owns the internal relation scaffolding objects that decouple `DjangoType` collection order from schema construction and close the import-order trap (spec-010, spec-018):
1. **`PendingRelation`**:
   - A `@dataclass(frozen=True)` capturing an auto-synthesized relation field whose target `DjangoType` may not yet be registered at collection time (`source_type`, `source_model`, `field_name`, `django_field`, `related_model`, `relation_kind`, `nullable`).
   - Implements custom `__hash__` using a 3-step component ladder (`_hash_component`: `hash(value)` -> `hash(type(value))` -> `id(type(value))`) so that equal relation records have identical hashes and can reside in sets even when `django_field` is an unhashable relation descriptor (e.g., `ForeignObjectRel` or descriptors with `__hash__ = None`).
   - Handled by identity (`id()`) when discarded via `TypeRegistry.discard_pending()`.
2. **`PendingRelationAnnotation`**:
   - A sentinel class carrying metaclass `_PendingRelationAnnotationMeta`.
   - Installed in `cls.__annotations__` by `_build_annotations` (`types/base.py`) for every auto-synthesized relation during `DjangoType.__init_subclass__`.
   - Rewritten to the resolved relation type by `finalize_django_types()` (`types/finalizer.py`).
   - If `finalize_django_types()` is skipped before Strawberry schema construction, `_PendingRelationAnnotationMeta.__repr__` emits a clear, actionable diagnostic message (`"<unfinalized DjangoType relation; call finalize_django_types() before constructing strawberry.Schema>"`).

## Verification

1. **Static & Structural Audit**:
   - Analyzed `django_strawberry_framework/types/relations.py` across producers (`types/base.py`), consumers (`types/finalizer.py`), and storage (`registry.py`).
   - Confirmed `_hash_component` defensive fallback steps for hashable objects, unhashable descriptors, and hostile type metadata.
   - Confirmed dataclass value equality and frozen immutability contracts.
2. **Scratch Verification**:
   - Executed `docs/review/temp-tests/types_relations/test_scratch.py` verifying `_hash_component` 3-rung ladder, `PendingRelationAnnotation` class/metaclass representation, and `PendingRelation` field access and immutability.
3. **Focused Test Runs**:
   - `uv run pytest tests/types/test_relations.py --no-cov` (7 passed in 1.62s).
   - `uv run pytest tests/types/test_relations.py tests/test_registry.py tests/types/test_definition_order.py tests/types/test_finalizer.py --no-cov` (153 passed in 1.81s).

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

`django_strawberry_framework/types/relations.py` is a compact, robust, and well-isolated scaffolding module. Its custom hashing gracefully handles unhashable Django model relation descriptors while preserving dataclass immutability, and its sentinel metaclass produces diagnostic error messages when finalization is omitted.

## Implementation (Worker 1)

- **Changed files:**
  - `tests/types/test_relations.py`: added direct unit tests pinning `PendingRelationAnnotation` diagnostic representation and `PendingRelation` frozen dataclass immutability (`FrozenInstanceError`).
- **Permanent tests:**
  - `tests/types/test_relations.py::test_pending_relation_annotation_repr` pins diagnostic `__repr__` for unfinalized schemas.
  - `tests/types/test_relations.py::test_pending_relation_is_frozen_dataclass` pins `PendingRelation` frozen immutability contract.
- **Verification:**
  - `uv run pytest docs/review/temp-tests/types_relations/test_scratch.py --no-cov` (3 passed).
  - `uv run pytest tests/types/test_relations.py tests/test_registry.py tests/types/test_definition_order.py tests/types/test_finalizer.py --no-cov` (153 passed).
- **Formatter & Linter:**
  - `uv run ruff format .` (clean).
  - `uv run ruff check --fix .` (clean, all checks passed).
- **Changelog:**
  - Test suite expansion pinning sentinel representation and dataclass immutability; no runtime behavior change or public API modification.

## Independent verification (Worker 2)

- **Scoped diff verification**:
  - `git diff 12779c99 -- django_strawberry_framework/types/relations.py` is empty (zero-edit on production target).
- **Behavior re-traced**:
  - `_hash_component`: confirmed the 3-rung ladder (`hash(val)` -> `hash(type(val))` -> `id(type(val))`) catches `BaseException` (including hostile exceptions like `KeyboardInterrupt` or `GeneratorExit`) to ensure hash stability across arbitrary descriptor implementations.
  - `PendingRelation`: confirmed `@dataclass(frozen=True)` value equality across duplicate records, custom `__hash__` hashing all 7 attributes, and `FrozenInstanceError` upon mutation attempts.
  - `PendingRelationAnnotation`: confirmed sentinel metaclass `__repr__` provides the diagnostic message for unfinalized schema definitions.
- **Independent scratch testing**:
  - Authored `docs/review/temp-tests/types_relations/test_independent_scratch.py` validating 3-rung ladder under `BaseException`, real Django relation descriptors (`ManyToOneRel`, `ForeignKey`), set insertion/deduplication, and sentinel metaclass representation.
  - `uv run pytest docs/review/temp-tests/types_relations/ --no-cov` (6 passed in 1.51s).
- **Permanent test execution**:
  - `uv run pytest tests/types/test_relations.py tests/test_registry.py tests/types/test_definition_order.py tests/types/test_finalizer.py --no-cov` (153 passed in 1.86s).
- **Verdict**:
  - Production module is clean, sound, and fully verified. Zero findings remain.
