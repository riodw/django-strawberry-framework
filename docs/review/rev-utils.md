# Review: django_strawberry_framework/utils/

Status: verified

## DRY analysis

- Existing patterns reused: `utils.__init__` exposes the currently shared helper surface from the focused submodules at `django_strawberry_framework/utils/__init__.py:17-29`. Relation-shape classification and many-side grouping are centralized in `relation_kind` and `is_many_side_relation_kind` at `django_strawberry_framework/utils/relations.py:39-70`, then reused by type collection, conversion, resolver generation, and optimizer planning at `django_strawberry_framework/types/base.py:663-680`, `django_strawberry_framework/types/converters.py:234-239`, `django_strawberry_framework/types/resolvers.py:188-194`, and `django_strawberry_framework/optimizer/walker.py:62-64`. String conversion is centralized in `snake_case` / `pascal_case` at `django_strawberry_framework/utils/strings.py:19-60` and reused by optimizer/type/converter code at `django_strawberry_framework/optimizer/walker.py:121-122`, `django_strawberry_framework/types/base.py:89-94`, and `django_strawberry_framework/types/converters.py:204-204`. GraphQL wrapper unwrapping is centralized in `unwrap_graphql_type` at `django_strawberry_framework/utils/typing.py:14-18` and reused by optimizer return-type/schema tracing at `django_strawberry_framework/optimizer/extension.py:336-390`. Utility re-export contracts are pinned by `tests/utils/test_relations.py:46-58` and `tests/utils/test_typing.py:40-56`.
- New helpers a fix might justify: none for this folder pass. The previous sibling findings already added the shared many-side relation helper and recursive GraphQL unwrap helper. The remaining relation-cardinality/nullability consolidation belongs to the existing `FieldMeta` SSoT backlog, which is source-anchored at `django_strawberry_framework/types/base.py:657-672`, `django_strawberry_framework/types/converters.py:229-239`, and `django_strawberry_framework/types/resolvers.py:181-190` rather than needing a new `utils/` helper.
- Duplication risk in the current folder: none unanchored. Static helper runs on `__init__.py`, `relations.py`, `strings.py`, and `typing.py` showed no cross-sibling repeated literals or control-flow hotspots. The repeated relation-kind literals inside `relations.py` are the defining `RelationKind` contract at `django_strawberry_framework/utils/relations.py:7-19` plus classifier return values at `django_strawberry_framework/utils/relations.py:57-65`, not duplicated implementation logic.

## High:

None.

## Medium:

None.

## Low:

None.

## What looks solid

- The folder has one-way dependencies: `utils/__init__.py` imports local submodules only, while `relations.py`, `strings.py`, and `typing.py` depend only on the standard library or no imports at all.
- The public-vs-private subpackage contract is narrow and explicit: `__all__` re-exports only the helpers currently used or tested at `django_strawberry_framework/utils/__init__.py:21-29`; implementation details such as `_RelationFieldLike` and `MANY_SIDE_RELATION_KINDS` stay in the relation submodule.
- Completed sibling artifacts already closed the confirmed folder-local DRY drift: many-side relation grouping is now shared through `is_many_side_relation_kind`, and optimizer `.of_type` recursion is now shared through `unwrap_graphql_type`.
- Comments and docstrings are coherent across the folder: each module describes its narrow helper responsibility, and there are no TODO comments in the folder-level static helper output.
- Mandatory static helper coverage was completed with `--output-dir docs/review/shadow --stdout` for `django_strawberry_framework/utils/__init__.py`, `relations.py`, `strings.py`, and `typing.py`; artifacts cite original source line numbers, not shadow line numbers.

### Summary

No confirmed folder-local issues found. The `utils/` package now matches its intended role as a small cross-cutting helper layer: relation-shape labels, case conversion, and type unwrapping each have a focused owner, and `utils.__init__` exposes a deliberate contract without adding import-time side effects or circular-import pressure. The broader FieldMeta relation-shape migration remains already anchored outside this folder and should not be duplicated as a new utils finding.

---

## Fix report (Worker 2)

### Files touched

- `docs/review/rev-utils.md` — recorded the no-op Worker 2 disposition for the no-findings folder pass.
- `docs/review/worker-memory/worker-2.md` — appended the Worker 2 memory entry for this cycle item.

### Tests added or updated

- None. Worker 1 reported no confirmed High/Medium/Low folder-local findings, and this pass made no source behavior changes.

### Validation run

- `uv run ruff format --check django_strawberry_framework/utils tests/utils` — passed, 8 files already formatted.
- `uv run ruff check django_strawberry_framework/utils tests/utils` — passed.
- `uv run pytest tests/utils --no-cov` — passed, 15 tests.
- Repo-wide `uv run ruff format .` / `uv run ruff check --fix .` skipped because the shared workspace already contains unrelated dirty files outside Worker 2's ownership for this item; scoped check-only validation was used to avoid modifying other workers' files.

### Notes for Worker 3

- No source or test edits were made. The folder pass has no confirmed findings, and the verified sibling artifacts already resolved the local DRY issues for many-side relation grouping and recursive GraphQL unwrap ownership.
- Comment/docstring disposition: reviewed the folder-level comment/docstring surface in `utils/__init__.py`, `relations.py`, `strings.py`, and `typing.py`; no updates warranted because the current docs describe the resolved helper contracts and no stale TODO/comment surface remains in this folder.
- Changelog disposition: not warranted. This pass made no user-visible behavior, API, schema, or documentation change, and changelog edits are not authorized for this cycle item. `CHANGELOG.md` was not edited.
- The broader FieldMeta relation-shape SSoT item remains already anchored outside `utils/` and was intentionally left untouched.
---

## Verification (Worker 3)

### Logic verification outcome

- Accepted. The folder pass has no unresolved High, Medium, or Low findings. The current `utils/` source matches the
  folder artifact's no-op disposition: focused helpers live in `relations.py`, `strings.py`, and `typing.py`, and
  `utils/__init__.py` exposes the intended narrow public contract without extra side effects.
- Worker 2's no-op fix report is complete for this folder-level item. No source or test edits were required, scoped
  validation was recorded, and the report explains why repo-wide fix commands were avoided in the dirty shared
  workspace.
- Comment/docstring disposition is complete. The folder-level docs describe the resolved helper contracts, and no stale
  TODO/comment surface remains in `django_strawberry_framework/utils/`.
- Changelog disposition is complete and acceptable. This folder pass made no user-visible behavior, schema, API, or
  documentation change, and `CHANGELOG.md` edits were not authorized.

### DRY findings disposition

- Accepted. The sibling `utils/relations.py` and `utils/typing.py` DRY findings are already verified and treated as
  resolved context for this pass: many-side relation grouping is centralized through `is_many_side_relation_kind()`,
  and recursive GraphQL `.of_type` unwrapping is centralized through `unwrap_graphql_type()`.
- The broader FieldMeta relation-shape SSoT item remains outside this folder pass. It is already anchored in the
  type/optimizer consumer code and should not be duplicated as a fresh `utils/` finding.

### Temp test verification

- None used.

### Verification outcome

- cycle accepted; verified
- Validation run:
  - `uv run pytest tests/utils --no-cov` — passed, 15 tests.
  - `uv run ruff format --check django_strawberry_framework/utils tests/utils` — passed, 8 files already formatted.
  - `uv run ruff check django_strawberry_framework/utils tests/utils` — passed.

---

## Comment/docstring pass

- Reviewed the folder-level comments and docstrings in `django_strawberry_framework/utils/__init__.py`, `relations.py`, `strings.py`, and `typing.py` as part of the no-op disposition. No updates warranted: the helper ownership docs match the verified sibling fixes, and there are no stale TODO comments in the folder.

---

## Changelog disposition

- Not warranted. This was a no-op folder-pass disposition with no source, test, public API, schema, or user-visible behavior change. `CHANGELOG.md` edits were not authorized and were not made.

---

## Iteration log

- Worker 2 no-op disposition completed for the no-findings `utils/` folder pass with scoped validation only.
