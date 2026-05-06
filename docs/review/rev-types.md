# Folder review: `django_strawberry_framework/types/`

Sibling artifacts read for this pass:

- `docs/review/rev-types__base.md`
- `docs/review/rev-types__converters.md`
- `docs/review/rev-types__resolvers.md`

## High:

None.

## Medium:

None at the folder level. The per-file Medium fixes are mutually consistent:

- `base.py` rejects `optimizer_hints` for fields not in the type's selected set, matching `converters.py`'s fail-loudly stance and `OptimizerHint`'s typed-wrapper validation in the optimizer subpackage.
- `converters.py` rejects sanitized-member collisions in choice enums, matching the registry's same-class-is-idempotent enum guard from the registry review.
- `resolvers.py` consolidates onto the framework-wide `logger` from `optimizer/__init__.py`, completing the logger deduplication for the third call site.

## Low:

### One-way dependency direction is honored, but the `..optimizer` cross-folder reach is not documented in the subpackage `__init__`

Both `base.py` and `resolvers.py` import from `..optimizer.*` (FieldMeta, OptimizerHint, plans helpers, the framework logger). That is the correct direction — the optimizer subpackage owns those primitives, and `types/` consumes them — but the original `types/__init__.py` docstring did not mention this dependency. The review-cycle fix added a one-line note pinning that `types/` may consume `optimizer/` and the reverse must not happen.

## What looks solid

- **Public surface is narrow.** `types/__init__.py` re-exports only `DjangoType`; converter and resolver helpers remain implementation details at their dotted submodule paths.
- **Dependency direction is one-way.** `base.py` imports `_attach_relation_resolvers` from `resolvers.py`, while `resolvers.py` imports nothing from `base.py`.
- **Cross-folder optimizer integration is centralized.** `resolvers.py` imports context readers and sentinel constants from `optimizer/_context.py` instead of repeating raw context-key strings or reader dispatch.
- **Relation-cardinality classification is shared.** `converters.py` and `resolvers.py` now use `utils.relations.relation_kind`; they still own their caller-specific payloads (annotation type vs. resolver closure).
- **All Django imports are concentrated in the expected files.** `base.py`, `converters.py`, and `resolvers.py` own the type-system Django interactions; no unexpected import direction was introduced.
- **`Meta` validation is layered.** `_validate_meta` runs first, `_validate_optimizer_hints_against_selected_fields` runs after `_select_fields`, and scalar/relation conversion raises during annotation synthesis when a field cannot be mapped.
- **Resolver attachment is exactly per-relation.** `_attach_relation_resolvers` skips scalar fields so they keep Strawberry's default attribute resolver.
- **Cross-file cache contracts are consistent.** `convert_choices_to_enum` defers to the registry; relation resolvers defer to optimizer context sentinels for elision and strictness.
- **Coverage is exhaustive.** Public branches are covered through `tests/types/test_base.py`, `tests/types/test_converters.py`, and `tests/types/test_resolvers.py`.

---

### Summary:

The types subpackage is well-shaped: narrow public surface, one-way dependency direction, layered `Meta` validation, shared relation-cardinality classification, and centralized optimizer context-sentinel use. The earlier context helper duplication and cardinality-dispatch repetition were addressed during closeout; the remaining Low item was docstring polish and has been completed.

---

### Worker 3 verification

- Low fix 1: `types/__init__.py` docstring now states the cross-folder dependency direction explicitly.
- Closeout DRY fixes: `resolvers.py` imports context helpers and sentinel constants from `optimizer/_context.py`; `converters.py` and `resolvers.py` use `utils.relations.relation_kind` for shared cardinality classification.
- Validation: `uv run ruff format`, `uv run ruff check`, and `uv run pytest -q` passed; tests reported 360 passed, 4 skipped, 100% coverage.
- CHANGELOG: not updated. Internal refactors only; no consumer-visible behavior change.
- Checkbox in `docs/review/review-0_0_3.md`: marked `- [x]`.
