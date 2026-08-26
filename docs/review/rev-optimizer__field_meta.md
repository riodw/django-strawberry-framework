# Review: `django_strawberry_framework/optimizer/field_meta.py`

Status: verified

## Understanding

`django_strawberry_framework/optimizer/field_meta.py` defines `FieldMeta`, the canonical single source of truth for Django field and relation metadata across the framework. It precomputes and encapsulates:
- Field naming and relation status (`name`, `is_relation`).
- Cardinality indicators (`many_to_many`, `one_to_many`, `one_to_one`).
- Classifier delegation (`relation_kind`, `is_many_side`) via `django_strawberry_framework.utils.relations`.
- Database column names and reverse accessors (`attname`, `reverse_connector_attname`, `accessor_name`).
- Relation targets and PK names (`related_model`, `target_field_name`, `target_field_attname`, `target_pk_name`).
- Forward single-relation FK-id elision eligibility (`fk_id_elision_eligible`).
- Concrete/virtual/auto-created flags (`concrete`, `auto_created`).
- Generic relation hooks (`content_type_field_name`, `object_id_field_name`).
- Cardinality-gated nullability (`nullable`).

It is constructed once per field during `DjangoType` class construction (stored on `DjangoTypeDefinition.field_map`) and used across the optimizer walker, nested query planner, schema generators, and relation resolvers. Unregistered models and test doubles construct `FieldMeta` via `FieldMeta.from_django_field` or `FieldMeta._from_field_shape`.

## Verification

1. **Focused Test Suite**: Examined and ran `tests/optimizer/test_field_meta.py` (28 existing tests + new permanent test = 29 passed in 5.99s).
2. **Scratch Experiments**: Created `docs/review/temp-tests/optimizer/test_field_meta_scratch.py` to verify relation nullability behaviors and duck-typed descriptors (e.g., duck-typed `GenericRelation` with `null=True`).
3. **AST and Cross-Module Tracing**: Traced `FieldMeta` consumption across `django_strawberry_framework/optimizer/walker.py`, `django_strawberry_framework/types/base.py`, `django_strawberry_framework/types/converters.py`, `django_strawberry_framework/types/definition.py`, `django_strawberry_framework/types/finalizer.py`, and `django_strawberry_framework/types/resolvers.py`.

## Improvements

### High

None.

### Medium

- **Observation:** `FieldMeta._from_field_shape` determined relation nullability by checking `if is_m2m or is_o2m:` rather than delegating directly to `is_many_side_relation_kind(kind)`.
- **Evidence:** `utils.relations.is_many_side_relation_kind` is the canonical classifier for list-valued relations (`"many"`, `"reverse_many_to_one"`, `"generic"`). A duck-typed `GenericRelation` (or any custom descriptor reporting `relation_kind == "generic"` or `"many"`) with `null=True` but lacking the `one_to_many` flag fell through to the scalar branch and evaluated to `nullable=True`, contradicting `is_many_side=True`.
- **Impact:** Potential schema inconsistency (generating `list[T] | None` instead of `list[T]`) for many-side relation shapes if descriptors lack standard boolean flags.
- **Recommendation:** Align `FieldMeta._from_field_shape` to branch directly on `is_many_side_relation_kind(kind)`:
  ```python
  if is_many_side_relation_kind(kind):
      nullable = False
  elif kind == "reverse_one_to_one":
      nullable = True
  else:
      nullable = _relation_bool(field, "null", False)
  ```
- **Proof:** Permanent test `test_from_django_field_many_side_nullability_short_circuits` in `tests/optimizer/test_field_meta.py` pins that duck-typed generic relations, M2Ms, and reverse FKs with `null=True` evaluate to `nullable=False` and `is_many_side=True`.

### Low

- **Observation:** `fk_id_elision_eligible` computation in `_from_field_shape` contained redundant checks (`and not is_m2m and not is_o2m and kind == "forward_single"`).
- **Evidence:** `relation_kind(field) == "forward_single"` is mutually exclusive with `many_to_many=True` and `one_to_many=True`.
- **Impact:** Redundant boolean operations during field metadata construction.
- **Recommendation:** Simplify the condition to `and kind == "forward_single"` as `kind` is the authoritative relation classifier.
- **Proof:** All FK elision tests in `tests/optimizer/test_field_meta.py` continue to pass.

## Summary

`django_strawberry_framework/optimizer/field_meta.py` provides a robust, immutable, and slotted metadata representation for Django fields and relations. Nullability rule gating was refined to delegate to `is_many_side_relation_kind`, ensuring complete consistency across all relation shapes and test doubles.

## Implementation (Worker 1)

- **Changed files**:
  - `django_strawberry_framework/optimizer/field_meta.py`: Aligned `FieldMeta._from_field_shape` nullability rule to use `is_many_side_relation_kind(kind)` and simplified `fk_id_elision_eligible` condition.
  - `tests/optimizer/test_field_meta.py`: Added `test_from_django_field_many_side_nullability_short_circuits` covering duck-typed many-side relations with `null=True`.
- **Permanent tests**:
  - `tests/optimizer/test_field_meta.py::test_from_django_field_many_side_nullability_short_circuits` verifies that generic relations, M2Ms, and reverse FKs force `nullable=False`.
- **Scratch verification**:
  - `docs/review/temp-tests/optimizer/test_field_meta_scratch.py` passed (1 test, 0 failures).
- **Formatter and linter**:
  - `uv run ruff format .` and `uv run ruff check --fix .` completed cleanly with 0 errors.
- **Evidence for rejected findings**: None.
- **Changelog**: Minor internal consistency fix; does not require a changelog entry.

## Independent verification (Worker 2)

- **Scoped diff against baseline**:
  - `django_strawberry_framework/optimizer/field_meta.py`: Aligned `FieldMeta._from_field_shape` nullability rule to use `is_many_side_relation_kind(kind)` directly and simplified `fk_id_elision_eligible` by removing redundant `not is_m2m` and `not is_o2m` conditions (subsumed by `kind == "forward_single"`).
  - `tests/optimizer/test_field_meta.py`: Added `test_from_django_field_many_side_nullability_short_circuits` asserting duck-typed many-side relations (generic, M2M, reverse FK) evaluate to `nullable=False` even when `null=True` attribute is set on descriptor.
- **Paths and behavior independently traced**:
  - **Field and relation metadata computation**:
    - `FieldMeta.from_django_field` validates input exposes `name` and `is_relation`, converting malformed descriptors to typed `OptimizerError` at stamp time.
    - Defensive extraction of `target_field`, `target_field_name`, `target_field_attname`, `related_model`, `target_pk_name` (via `_target_pk_name`), `attname`, `reverse_connector_attname`, and `accessor_name` (via `instance_accessor`).
  - **Cardinality & classifier delegation**:
    - `relation_kind` and `is_many_side` properties correctly delegate to `django_strawberry_framework.utils.relations`.
  - **Nullability rules**:
    - `is_many_side_relation_kind(kind)` -> `nullable = False` (list fields are never `None`).
    - `kind == "reverse_one_to_one"` -> `nullable = True` (related row may legitimately be absent).
    - Other single relations follow `_relation_bool(field, "null", False)`.
  - **Reverse connector discovery**:
    - `reverse_connector_attname` extracts `field.field.attname` from reverse relations, ensuring reverse joins target the correct parent FK column.
  - **FK-id elision eligibility**:
    - Verified strict eligibility requirements: `attname is not None`, `related_model is not None`, `target_pk_name is not None`, `target_field_name == target_pk_name`, `kind == "forward_single"`, and `not has_composite_pk(related_model)`.
- **Focused & scratch test verification**:
  - `tests/optimizer/test_field_meta.py` (29 passed).
  - Created and executed `docs/review/temp-tests/optimizer/test_field_meta_w2.py` (3 passed) verifying real models (`Book`, `Shelf`, `Branch`), duck-typed custom descriptors (reverse O2O, non-PK `to_field`, missing `_meta`), and validation guards.
- **Linters & formatters**:
  - Ruff check, ruff format check, and trailing comma check verified clean on `django_strawberry_framework/optimizer/field_meta.py` and `tests/optimizer/test_field_meta.py`.
- **All findings disposed of**: Target is sound, well-tested, and verified.

