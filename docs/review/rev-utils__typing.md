# Review: `django_strawberry_framework/utils/typing.py`

Status: verified

## DRY analysis

- Existing patterns reused: `unwrap_return_type` uses Python's standard annotation-introspection APIs, `get_origin` and `get_args`, directly in `django_strawberry_framework/utils/typing.py:12-43`. It is re-exported from the utils package in `django_strawberry_framework/utils/__init__.py:16-26` and pinned by focused tests in `tests/utils/test_typing.py:6-33`.
- New helpers a fix might justify: one shared wrapper-unwrapping helper with an explicit contract for "one Python annotation layer" versus "all Strawberry/graphql-core `.of_type` layers"; the call sites it would serve are `django_strawberry_framework/utils/typing.py:15-43` and the optimizer helper/call sites in `django_strawberry_framework/optimizer/extension.py:299-308`, `django_strawberry_framework/optimizer/extension.py:347-383`, and `django_strawberry_framework/optimizer/extension.py:387-412`.
- Duplication risk in the current file: `django_strawberry_framework/utils/typing.py:5-8` says this helper exists so the optimizer and future factories do not reimplement the same unwrap, but the optimizer currently keeps a parallel `_unwrap_gql_type` loop in `django_strawberry_framework/optimizer/extension.py:299-308`; `rg` found no package source caller of `unwrap_return_type` outside the utils re-export.

## High:

None.

## Medium:

### Shared unwrap ownership has already drifted

The module-level contract says the optimizer uses this shared helper so list / wrapper unwrapping is not reimplemented per consumer, but the optimizer currently implements and calls its own recursive `.of_type` unwrapper. That leaves two wrapper-unwrapping concepts with different behavior: this helper peels one `list[T]` or one `.of_type` layer, while `_unwrap_gql_type` peels all graphql-core `.of_type` layers. Because `unwrap_return_type` has no package source callers today, tests can keep passing while the documented shared utility continues to drift from the optimizer path. Consolidate the ownership: either make `utils.typing` expose the helper contract the optimizer actually needs and switch the optimizer call sites to it, or narrow this module's docstring/tests to an annotation-only helper and remove the optimizer claim.

```django_strawberry_framework/utils/typing.py:5:8
wrapper object that carries an ``of_type`` attribute. Subsystems that
need to introspect a resolver's return type — the optimizer today, and
the connection-field / filter argument factories tomorrow — all need
the same one-layer unwrap, so it lives here rather than re-implemented
```

```django_strawberry_framework/optimizer/extension.py:299:308
def _unwrap_gql_type(gql_type: Any) -> Any:
    """Peel graphql-core ``GraphQLNonNull`` / ``GraphQLList`` wrappers.

    Centralises the ``while hasattr(t, "of_type")`` loop so the
    schema-reachability walker and the return-type tracer share one
    implementation.
    """
    while hasattr(gql_type, "of_type"):
        gql_type = gql_type.of_type
    return gql_type
```

## Low:

None.

## What looks solid

- Static helper skipped: `django_strawberry_framework/utils/typing.py` is 44 lines, outside `optimizer/` and `types/`, and has a small single-function surface.
- The helper has no import-time side effects and only uses standard-library typing APIs in `django_strawberry_framework/utils/typing.py:12-43`.
- The current one-layer behavior is explicitly documented in the function docstring and covered for `list[T]`, Strawberry-style `of_type`, and bare classes in `tests/utils/test_typing.py:6-33`.
- No additional stale comments or docstring concerns beyond the shared-ownership drift called out above.

### Summary

The local implementation is tiny and tested, but its documented role as the shared optimizer/future-factory unwrap utility is not true in the current package. The main fix is to make the unwrap ownership explicit and single-sourced before the next consumers build against this helper.

---

## Fix report (Worker 2)

### Files touched

- `django_strawberry_framework/utils/typing.py` — added `unwrap_graphql_type()` as the shared recursive `.of_type` unwrapper while keeping `unwrap_return_type()` as the one-layer annotation helper.
- `django_strawberry_framework/utils/__init__.py` — exported `unwrap_graphql_type()` from the utils package and updated the utils subpackage description.
- `django_strawberry_framework/optimizer/extension.py` — replaced the private `_unwrap_gql_type()` helper with the shared `unwrap_graphql_type()` import at the schema-reachability and return-type model-resolution call sites.
- `tests/utils/test_typing.py` — pinned the separate one-layer annotation contract and full recursive GraphQL wrapper contract.

### Tests added or updated

- `tests/utils/test_typing.py::test_unwrap_return_type_peels_only_one_layer` — pins that the annotation helper remains a one-layer unwrap.
- `tests/utils/test_typing.py::test_unwrap_graphql_type_peels_all_of_type_layers` — pins the shared optimizer helper's recursive `.of_type` contract.

### Validation run

- `uv run ruff format django_strawberry_framework/utils/typing.py django_strawberry_framework/utils/__init__.py django_strawberry_framework/optimizer/extension.py tests/utils/test_typing.py` — passed, 4 files unchanged.
- `uv run ruff check --fix django_strawberry_framework/utils/typing.py django_strawberry_framework/utils/__init__.py django_strawberry_framework/optimizer/extension.py tests/utils/test_typing.py` — passed.
- `uv run pytest tests/utils/test_typing.py --no-cov` — passed, 5 tests.
- `uv run pytest tests/optimizer/test_extension.py::test_resolve_model_from_return_type_unwraps_nested_wrappers tests/optimizer/test_extension.py::test_resolve_model_returns_none_for_non_object_leaf tests/optimizer/test_extension.py::test_resolve_model_returns_none_when_no_strawberry_schema tests/optimizer/test_extension.py::test_resolve_model_returns_none_when_type_not_in_schema --no-cov` — passed, 4 tests.

### Notes for Worker 3

- No shadow file was used.
- The optimizer semantics should be unchanged: the new helper uses the same `while hasattr(gql_type, "of_type")` loop as the removed private helper.
- Existing `unwrap_return_type()` callers/tests keep the annotation-only one-layer behavior.

---

## Verification (Worker 3)

### Logic verification outcome

Medium finding is logically addressed: recursive GraphQL ``.of_type`` unwrapping now lives in
``django_strawberry_framework/utils/typing.py::unwrap_graphql_type()``, and
``django_strawberry_framework/optimizer/extension.py`` imports that helper instead of keeping the
private ``_unwrap_gql_type()`` loop. The optimizer call sites for schema-reachability walking and
return-type model resolution both use the shared utility.

``unwrap_return_type()`` remains a one-layer annotation helper. The permanent tests now pin the
split contract with ``test_unwrap_return_type_peels_only_one_layer`` and
``test_unwrap_graphql_type_peels_all_of_type_layers``.

### DRY findings disposition

Accepted for code ownership: the duplicated optimizer unwrap loop was removed and replaced by the
shared utility helper.

Revision needed for comment/docstring disposition: ``tests/test_registry.py`` still has a stale
docstring on ``test_model_for_type_returns_none_for_none`` that says
``DjangoOptimizerExtension`` chains ``unwrap_return_type`` -> ``model_for_type``. After this fix,
the optimizer return-type path uses ``unwrap_graphql_type``. Worker 2 should update that docstring
to describe the current return-type tracing pipeline, or make it helper-agnostic, then return this
artifact for verification.

### Temp test verification

- Temp test files used: none.
- Disposition: permanent tests were sufficient.

### Verification outcome

revision-needed

Validation run by Worker 3:

- ``uv run pytest tests/utils/test_typing.py --no-cov`` — passed, 5 tests.
- ``uv run pytest tests/optimizer/test_extension.py::test_resolve_model_from_return_type_unwraps_nested_wrappers tests/optimizer/test_extension.py::test_resolve_model_returns_none_for_non_object_leaf tests/optimizer/test_extension.py::test_resolve_model_returns_none_when_no_strawberry_schema tests/optimizer/test_extension.py::test_resolve_model_returns_none_when_type_not_in_schema --no-cov`` — passed, 4 tests.
- ``uv run ruff format --check django_strawberry_framework/utils/typing.py django_strawberry_framework/utils/__init__.py django_strawberry_framework/optimizer/extension.py tests/utils/test_typing.py`` — passed, 4 files already formatted.
- ``uv run ruff check django_strawberry_framework/utils/typing.py django_strawberry_framework/utils/__init__.py django_strawberry_framework/optimizer/extension.py tests/utils/test_typing.py`` — passed.
- ``uv run ruff format --check django_strawberry_framework/utils/typing.py django_strawberry_framework/utils/__init__.py django_strawberry_framework/optimizer/extension.py tests/utils/test_typing.py docs/review/rev-utils__typing.md docs/review/review-0_0_5.md`` — not applicable for Markdown: Ruff reported Markdown formatting requires preview mode, while the 4 Python files were already formatted.

---

## Comment/docstring pass

After Worker 3 records `logic accepted; awaiting comment pass`, Worker 2 returns for a comment/docstring pass and records the updates here.

Worker 2 disposition: comment/docstring updates were included with the logic fix because the finding itself was stale ownership documentation. `utils.typing` now documents the split contracts, `utils.__init__` lists both typing helpers, and the optimizer's existing return-type comments still describe behavior rather than the helper location.

---

## Changelog disposition

After Worker 3 records `comments accepted; awaiting changelog disposition`, Worker 2 records the changelog disposition here.

Worker 2 disposition: not warranted. This is a private ownership/DRY consolidation for optimizer internals plus a utils subpackage export, with no top-level package API or user-visible behavior change. `CHANGELOG.md` was not edited and changelog edits were not authorized for this pass.

---

## Iteration log

### 2026-05-15 — Worker 2 revision follow-up

- Updated `tests/test_registry.py::test_model_for_type_returns_none_for_none` to describe the current optimizer return-type path: `unwrap_graphql_type` resolves GraphQL wrappers before `model_for_type` receives the Strawberry origin.
- No source consolidation changes were made; Worker 3 accepted the logic and requested only the stale docstring/comment follow-up.
- Validation run for this follow-up: `uv run ruff format tests/test_registry.py` passed; `uv run ruff check --fix tests/test_registry.py` passed; `uv run pytest tests/test_registry.py::test_model_for_type_returns_none_for_none --no-cov` passed.

---

## Re-verification (Worker 3)

### 2026-05-15 — accepted

The Medium DRY/ownership finding is fixed. Recursive GraphQL `.of_type` unwrapping is centralized in `django_strawberry_framework/utils/typing.py::unwrap_graphql_type()`, exported through `django_strawberry_framework/utils/__init__.py`, and used by `django_strawberry_framework/optimizer/extension.py` for both schema-reachability walking and return-type model resolution. The optimizer no longer carries a parallel private unwrap loop.

`unwrap_return_type()` remains the separate one-layer annotation helper, and `tests/utils/test_typing.py` pins the split with `test_unwrap_return_type_peels_only_one_layer` and `test_unwrap_graphql_type_peels_all_of_type_layers`. The stale `tests/test_registry.py::test_model_for_type_returns_none_for_none` docstring now names the current `unwrap_graphql_type` -> `model_for_type` path. Utility export/docstring updates are coherent, Worker 2's fix report and revision follow-up are complete, and the no-changelog disposition is acceptable for this internal DRY consolidation.

Validation run by Worker 3:

- `uv run pytest tests/utils/test_typing.py --no-cov` — passed, 5 tests.
- `uv run pytest tests/test_registry.py::test_model_for_type_returns_none_for_none --no-cov` — passed, 1 test.
- `uv run pytest tests/optimizer/test_extension.py::test_resolve_model_from_return_type_unwraps_nested_wrappers tests/optimizer/test_extension.py::test_resolve_model_returns_none_for_non_object_leaf tests/optimizer/test_extension.py::test_resolve_model_returns_none_when_no_strawberry_schema tests/optimizer/test_extension.py::test_resolve_model_returns_none_when_type_not_in_schema --no-cov` — passed, 4 tests.
- `uv run ruff format --check django_strawberry_framework/utils/typing.py django_strawberry_framework/utils/__init__.py django_strawberry_framework/optimizer/extension.py tests/utils/test_typing.py tests/test_registry.py` — passed, 5 files already formatted.
- `uv run ruff check django_strawberry_framework/utils/typing.py django_strawberry_framework/utils/__init__.py django_strawberry_framework/optimizer/extension.py tests/utils/test_typing.py tests/test_registry.py` — passed.
