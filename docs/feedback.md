# Spec Review Feedback: Permissions Subsystem (0.0.10)

**Target Spec**: [spec-034-permissions-0_0_10.md](file:///Users/riordenweber/projects/django-strawberry-framework/docs/spec-034-permissions-0_0_10.md)  
**Companion CSV**: [spec-034-permissions-0_0_10-terms.csv](file:///Users/riordenweber/projects/django-strawberry-framework/docs/spec-034-permissions-0_0_10-terms.csv)  
**Status**: **Approved / Verified** (with minor recommendations)

---

## Executive Summary

The proposed specification for the `0.0.10` permissions subsystem is exceptionally thorough, structurally sound, and matches the high design standards of the codebase. It resolves key tensions between the cascade design, the connection pipelines, and the future per-field permission gates without introducing premature complexity.

---

## DRY Analysis & Structural Soundness

- **Single-Source walk**: The walk logic is centralized within a single helper `apply_cascade_permissions`. 
- **Sync/Async Twin Alignment**: Wrapping the sync walk in `sync_to_async(thread_sensitive=True)` for `aapply_cascade_permissions` avoids dual-maintenance walk logic and guarantees thread-safety and database-safety under ASGI.
- **Seam Preservation**: The cascade operates entirely inside the type's `get_queryset` method. No pipelines or middlewares need to be altered or duplicated to support row-level permissions.

---

## Key Architectural Strengths

### 1. Performance: Lazy Subquery Composition
By composing lazy `__in` subqueries, the database compiles the cascade walk into a single SQL statement. This successfully avoids the "one extra round-trip per FK" trap, requiring zero alterations to the optimizer while preserving `Prefetch` downgrade logic.

### 2. Multi-DB Alias Pinning
Using `queryset.db` correctly propagates the resolved database alias (including routed databases) down to target subqueries. This is a robust improvement over the private `_db` attribute, which could return `None` in routed multi-DB setups.

### 3. ContextVar seen-set Cycle Guard
The module-level `ContextVar[set | None]` seen-set successfully prevents infinite recursion in self-referential or mutually-cascading graphs. The use of a `finally` block to discard the class frame and reset the token at the root guarantees WSGI/ASGI request isolation.

---

## Findings & Recommendations

### High / Medium Findings
None.

### Low Findings / Refinements

#### 1. String validation on `fields=` parameter
- **Context**: `fields=` accepts an iterable of model field names.
- **Risk**: Since a string is a valid iterable in Python, if a developer accidentally writes `fields="item"` instead of `fields=["item"]`, the code will iterate over the characters `'i'`, `'t'`, `'e'`, `'m'`. The loud validation check will then look up these individual characters as field names, causing a `ConfigurationError` stating that `'i'` is not a cascadable field on the model.
- **Recommendation**: Although a `ConfigurationError` is successfully raised, the developer may find the error message confusing. Consider explicitly guarding against string inputs at the start of validation:
  ```python
  if isinstance(fields, str):
      raise ConfigurationError(
          f"fields parameter must be a list, tuple, or other non-string iterable of field names; got string {fields!r}"
      )
  ```

#### 2. Caching cascadable fields per model
- **Context**: The walk dynamically determines which model fields are cascadable by filtering fields with `related_model` and `hasattr(field, "column")`.
- **Risk**: Django model metadata (e.g., `_meta.get_fields()`) is static after application startup. Iterating over all fields on every `get_queryset` call introduces minor, unnecessary overhead.
- **Recommendation**: Cache the set of cascadable fields per model in a module-level dictionary or class property after the first computation:
  ```python
  _cascadable_fields_cache: dict[type[models.Model], set[str]] = {}

  def get_cascadable_fields(model: type[models.Model]) -> set[str]:
      if model not in _cascadable_fields_cache:
          _cascadable_fields_cache[model] = {
              f.name for f in model._meta.get_fields()
              if f.related_model is not None and hasattr(f, "column")
          }
      return _cascadable_fields_cache[model]
  ```

#### 3. Django 5.2 Composite PKs
- **Observation**: Skipping composite PK/FK relations is a sensible constraint for `0.0.10` since they lack a single `column` attribute. This is correctly cataloged in the spec under "Edge cases and constraints" and will be skipped by construction.

---

## Glossary & CSV Verification

- `check_spec_glossary.py` passed with `OK: 43 terms`.
- The CSV note on `aapply_cascade_permissions` sharing `apply_cascade_permissions`'s glossary entry is logical and keeps the glossary concise.
- Updating `docs/GLOSSARY.md` in Slice 5 to correct the pre-existing "FK / M2M" scope error to "FK / OneToOne" aligns the documentation with the actual shipped code.
