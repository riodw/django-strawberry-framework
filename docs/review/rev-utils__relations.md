# Review: `django_strawberry_framework/utils/relations.py`

Status: verified

## DRY analysis

- Existing patterns reused: `relation_kind` is the shared relation-shape classifier consumed by pending relation creation in `django_strawberry_framework/types/base.py:663-680`, annotation conversion in `django_strawberry_framework/types/converters.py:234-237`, generated resolver dispatch in `django_strawberry_framework/types/resolvers.py:189-203`, optimizer relation planning in `django_strawberry_framework/optimizer/walker.py:62-64`, and `FieldMeta` nullability derivation in `django_strawberry_framework/optimizer/field_meta.py:163-167`. The public utility contract is re-exported from `django_strawberry_framework/utils/__init__.py:16-25` and pinned by `tests/utils/test_relations.py:12-58`.
- New helpers a fix might justify: add a single package-owned many-side helper or constant, such as `is_many_side_relation_kind(kind: RelationKind) -> bool` or `MANY_SIDE_RELATION_KINDS`, for the call sites that currently repeat `("many", "reverse_many_to_one")`: `django_strawberry_framework/types/base.py:669-672`, `django_strawberry_framework/types/converters.py:234-237`, `django_strawberry_framework/types/resolvers.py:45-45` and `django_strawberry_framework/types/resolvers.py:191-197`, plus `django_strawberry_framework/optimizer/walker.py:62-64`.
- Duplication risk in the current file: none inside `django_strawberry_framework/utils/relations.py` itself beyond the necessary `RelationKind` literals and return values at `django_strawberry_framework/utils/relations.py:7-12` and `django_strawberry_framework/utils/relations.py:50-58`; the current export shape still forces consumers to duplicate the many-side grouping, which is the Medium finding below.

## High:

None.

## Medium:

### Many-side relation grouping is duplicated outside the classifier

`relation_kind` centralizes the four relation labels, but it does not centralize the package's second-level grouping for list-valued/many-side relations. Consumers repeatedly spell `("many", "reverse_many_to_one")` or a local equivalent, so adding or splitting a many-side relation shape would require synchronized edits across type collection, conversion, resolver generation, strictness checking, and optimizer planning. Move that grouping into `utils/relations.py` as one helper or exported constant, then update the current consumers and `tests/utils/test_relations.py` to pin the shared contract.

```django_strawberry_framework/utils/relations.py:7:12
RelationKind: TypeAlias = Literal[
    "many",
    "reverse_many_to_one",
    "reverse_one_to_one",
    "forward_single",
]
```

```django_strawberry_framework/types/base.py:663:672
kind = relation_kind(field)
if kind in ("many", "reverse_many_to_one"):
    nullable = False
else:
    nullable = kind == "reverse_one_to_one" or bool(getattr(field, "null", False))
```

```django_strawberry_framework/types/converters.py:234:237
kind = relation_kind(field)
if kind in ("many", "reverse_many_to_one"):
    return list[target_type]
if kind == "reverse_one_to_one" or getattr(field, "null", False):
```

```django_strawberry_framework/types/resolvers.py:45:45
_MANY_SIDE_KINDS: frozenset[str] = frozenset({"many", "reverse_many_to_one"})
```

```django_strawberry_framework/optimizer/walker.py:62:64
if relation_kind(field) in ("many", "reverse_many_to_one"):
    return ("prefetch", "default")
return ("select", "default")
```

## Low:

None.

## What looks solid

- Static helper skipped: the file is 58 lines, outside `optimizer/` and `types/`, and the direct source plus call-site trace gave the needed review surface without producing shadow output.
- The classifier orders checks safely for current Django relation shapes: `many_to_many` is classified before `one_to_many`, reverse FK is distinguished by `auto_created`, and reverse OneToOne gets its own label before all remaining forward single relations fall through.
- The public re-export and focused utility tests cover the existing label contract.
- Comments and docstrings accurately describe the shipped behavior; no comment/docstring concern is separate from the DRY finding above.

### Summary

`utils/relations.py` is small and correct for the relation shapes it classifies, but the module stops one abstraction short: every caller that needs the many-side grouping rebuilds that grouping locally. Centralizing the grouping in this utility module would keep relation-shape evolution DRY and make future changes less brittle.

---

## Fix report (Worker 2)

### Files touched

- `django_strawberry_framework/utils/relations.py` — added `MANY_SIDE_RELATION_KINDS` and `is_many_side_relation_kind()` as the shared package-owned contract for list-valued relation kinds.
- `django_strawberry_framework/utils/__init__.py` — re-exported `is_many_side_relation_kind()` from the utilities package surface.
- `django_strawberry_framework/types/base.py` — replaced pending-relation nullable derivation's duplicated many-side tuple with the shared helper.
- `django_strawberry_framework/types/converters.py` — replaced relation annotation conversion's duplicated many-side tuple with the shared helper.
- `django_strawberry_framework/types/resolvers.py` — removed the resolver-local many-side set and routed strictness and resolver dispatch through the shared helper.
- `django_strawberry_framework/optimizer/walker.py` — replaced optimizer relation planning's duplicated many-side tuple with the shared helper.

### Tests added or updated

- `tests/utils/test_relations.py::test_is_many_side_relation_kind_matches_list_valued_shapes` — pins the shared many-side grouping and the non-many relation kinds.
- `tests/utils/test_relations.py::test_utils_init_reexports_match_submodule` — pins the public `django_strawberry_framework.utils` re-export.

### Validation run

- `uv run ruff format django_strawberry_framework/utils/relations.py django_strawberry_framework/utils/__init__.py django_strawberry_framework/types/base.py django_strawberry_framework/types/converters.py django_strawberry_framework/types/resolvers.py django_strawberry_framework/optimizer/walker.py tests/utils/test_relations.py` — passed, 7 files left unchanged.
- `uv run ruff check --fix django_strawberry_framework/utils/relations.py django_strawberry_framework/utils/__init__.py django_strawberry_framework/types/base.py django_strawberry_framework/types/converters.py django_strawberry_framework/types/resolvers.py django_strawberry_framework/optimizer/walker.py tests/utils/test_relations.py` — passed after fixing 1 import-order issue.
- `uv run pytest tests/utils/test_relations.py --no-cov` — passed, 8 passed.
- `uv run pytest tests/utils/test_relations.py tests/types/test_base.py tests/types/test_converters.py tests/types/test_resolvers.py tests/optimizer/test_walker.py --no-cov` — passed, 159 passed, 1 skipped, 2 existing model-registration warnings.

### Notes for Worker 3

- Static helper shadow was not used; Worker 1 explicitly skipped it for this small utility file.
- The larger FieldMeta relation-shape SSoT backlog item was left untouched. Existing TODO anchors in the consumers remain in place.
- The workspace had pre-existing dirty review/source/test files before this pass; this fix stayed within the assigned ownership and did not edit the active plan, changelog, KANBAN, or unrelated scratch files.

---

## Verification (Worker 3)

### Logic verification outcome

- Accepted. The Medium DRY finding is addressed: `utils/relations.py` now owns `MANY_SIDE_RELATION_KINDS` and
  `is_many_side_relation_kind()`, and the package consumers in `types/base.py`, `types/converters.py`,
  `types/resolvers.py`, and `optimizer/walker.py` route many-side branching through the shared helper instead of
  repeating the tuple/local set.
- The public utility surface is pinned: `django_strawberry_framework/utils/__init__.py` re-exports
  `is_many_side_relation_kind()`, and `tests/utils/test_relations.py` verifies both the re-export identity and the
  list-valued relation-kind contract.
- The broader FieldMeta SSoT backlog item was not implemented here. The existing `TODO(spec-fieldmeta-ssot)` anchors
  in `types/base.py`, `types/converters.py`, and `types/resolvers.py` remain in place, and `KANBAN.md` still tracks the
  follow-up under `BACKLOG-031-0.0.6`.
- Worker 2's fix report, comment/docstring disposition, changelog disposition, and validation notes are complete. The
  no-changelog decision is acceptable because this is an internal DRY refactor and the workflow did not authorize a
  `CHANGELOG.md` edit.

### DRY findings disposition

- Resolved for this cycle. The repeated many-side grouping has one package-owned helper now. Remaining relation-shape
  duplication belongs to the already-anchored FieldMeta SSoT backlog item, not this utility DRY finding.

### Temp test verification

- None used.

### Verification outcome

- cycle accepted; verified
- Validation run:
  - `uv run ruff format --check django_strawberry_framework/utils/relations.py django_strawberry_framework/utils/__init__.py django_strawberry_framework/types/base.py django_strawberry_framework/types/converters.py django_strawberry_framework/types/resolvers.py django_strawberry_framework/optimizer/walker.py tests/utils/test_relations.py` — passed, 7 files already formatted.
  - `uv run ruff check django_strawberry_framework/utils/relations.py django_strawberry_framework/utils/__init__.py django_strawberry_framework/types/base.py django_strawberry_framework/types/converters.py django_strawberry_framework/types/resolvers.py django_strawberry_framework/optimizer/walker.py tests/utils/test_relations.py` — passed.
  - `uv run pytest tests/utils/test_relations.py --no-cov` — passed, 8 passed.
  - `uv run pytest tests/utils/test_relations.py tests/types/test_base.py tests/types/test_converters.py tests/types/test_resolvers.py tests/optimizer/test_walker.py --no-cov` — passed, 159 passed, 1 skipped, 2 existing model-registration warnings.

---

## Comment/docstring pass

- Added a narrow docstring for `is_many_side_relation_kind()` and updated the utilities package docstring to list the new re-export. No other comment/docstring changes were warranted; existing FieldMeta SSoT TODO comments are still accurate and intentionally retained.

---

## Changelog disposition

- Not warranted. This is an internal DRY refactor plus utility re-export used by package internals; it does not change consumer-visible behavior. `CHANGELOG.md` edits were not authorized and were not made.

---

## Iteration log
