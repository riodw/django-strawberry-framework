# Review feedback — Python diff `8cec18a` + fixes in local diff (`98302e6`)

Scope: re-reviewed only Python files changed by commit `8cec18a3890d2b2c0a0e60acecd3e83501aaed27`, with the follow-up fixes in commit `98302e6` ("apply feedback") included.

## Prior findings — status

Both items from the previous review of `8cec18a` are now resolved by `98302e6`:

- **H1 (origin-missing branch uncovered)** — fixed. [tests/optimizer/test_extension.py:544](tests/optimizer/test_extension.py:544) (`test_resolve_model_returns_none_when_definition_has_no_origin`) now drives `_resolve_model_from_return_type` through a fake `get_type_by_name(...)` that returns a definition without `origin`, exercising [django_strawberry_framework/optimizer/extension.py:415](django_strawberry_framework/optimizer/extension.py:415). Full pytest now passes the 100% line-coverage gate (`683 passed, 3 skipped`; total coverage 100.00%).
- **M1 (`scripts/check_spec_glossary.py` ruff failures)** — fixed. The module docstring is now raw (`r"""..."""`) at [scripts/check_spec_glossary.py:1](scripts/check_spec_glossary.py:1), and `main(...)` carries a docstring at [scripts/check_spec_glossary.py:268](scripts/check_spec_glossary.py:268). `uv run ruff check .` reports `All checks passed!`.

Verification commands run locally after applying `98302e6`:

- `uv run ruff check .` → All checks passed.
- `uv run ruff format --check .` → 100 files already formatted.
- `uv run pytest --cov=django_strawberry_framework --cov-report=term-missing` → 683 passed, 3 skipped, 100.00% line coverage (meets `pyproject.toml` `fail_under = 100`).
- `uv run pytest examples/` → 72 passed (no regression in the fakeshop example).

No new high- or medium-severity findings on this pass.

## Low-Severity / Code-Hygiene Observations

### L1. Tests reach into `TypeRegistry` private state for multi-type fixtures

References: [tests/optimizer/test_walker.py:1566](tests/optimizer/test_walker.py:1566), [tests/optimizer/test_walker.py:1614](tests/optimizer/test_walker.py:1614), [tests/optimizer/test_walker.py:1666](tests/optimizer/test_walker.py:1666), [tests/optimizer/test_extension.py:2999](tests/optimizer/test_extension.py:2999), [tests/optimizer/test_extension.py:3047](tests/optimizer/test_extension.py:3047).

The new Slice 4 tests mutate `registry._primaries[...]`, `registry._types`, and `registry._models` directly to set up or tear down multi-type scenarios (e.g., `registry._primaries[Item] = ItemType` after `_register_type_definition` to flag the primary without going through the public `register(..., primary=True)` path; `registry._types.pop(Category, None)` to simulate an unregistered relation target after a class has already been declared).

This matches a pre-existing pattern in the same files (the older `check_schema` tests around [tests/optimizer/test_extension.py:1810](tests/optimizer/test_extension.py:1810) already used the `_types.pop` / `_models.pop` shape), so the new tests are not a regression — they extend a pattern that was already there. But the coupling to private attributes makes the registry shape harder to refactor (any future rename of `_types` / `_primaries` would silently break tests). Consider adding small public helpers (e.g., `registry.set_primary(model, type_cls)` and `registry.unregister(type_cls)`) and porting these tests over when convenient.

### L2. `register_with_definition` rollback contains an unreachable inner guard

References: [django_strawberry_framework/registry.py:247-250](django_strawberry_framework/registry.py:247).

```python
if appended:
    types = self._types.get(model, [])
    if type_cls in types:        # always True when appended is True
        types.remove(type_cls)
```

The `appended` snapshot is the return value of `self.register(model, type_cls, primary=primary)`. `register` returns `True` only after `existing_types.append(type_cls)` runs on the same list that `_types[model]` references, so `type_cls in types` is guaranteed inside the `if appended:` block. Branch coverage confirms the False arm is unreachable (`registry.py 249->251` partial under `--cov-branch`). Drop the inner `if` and call `types.remove(type_cls)` unconditionally — that documents the rollback's atomicity invariant instead of hiding it behind a defensive check that can't fail.

### L3. `audit_primary_ambiguity` is module-public but only called internally

References: [django_strawberry_framework/types/finalizer.py:66](django_strawberry_framework/types/finalizer.py:66).

`audit_primary_ambiguity` is defined at module scope without an underscore prefix, while its siblings in the same file (`_format_unresolved_targets_error`, `_format_ambiguity_error`) follow the project's `_private` convention. The function has no caller outside `finalize_django_types()` and is not exported from any package `__init__.py`. Either prefix it (`_audit_primary_ambiguity`) to match neighbours, or export it intentionally if it's meant as a pre-finalize validation hook for consumers.

### L4. Ambiguity-audit error lists offenders in dict-insertion order

References: [django_strawberry_framework/types/finalizer.py:80-86](django_strawberry_framework/types/finalizer.py:80).

`audit_primary_ambiguity` walks `registry.models_with_multiple_types()` and appends offenders in the order they were registered. The error body therefore depends on consumer import order. The existing tests (e.g. [tests/test_registry.py:1051](tests/test_registry.py:1051), [tests/types/test_definition_order.py:396](tests/types/test_definition_order.py:396)) only assert substring presence, so this is not a test-stability bug, but sorting `offenders` by `model.__name__` before formatting would give a deterministic message that's easier to scan when several models are flagged at once. Cosmetic.

### L5. Mixed "already registered" phrasings between `register` and the helper

References: [django_strawberry_framework/registry.py:65-73](django_strawberry_framework/registry.py:65), [django_strawberry_framework/registry.py:120-130](django_strawberry_framework/registry.py:120).

The static `_already_registered` helper produces `"X is already registered against Y"` / `"X is already registered as Y"` and is now used only by the reverse-collision branch and `register_enum`. The two new primary-related errors (`"already registered for ...; primary flag cannot be flipped on re-register"` and `"already declared primary as ..."`) skip the helper and inline their own phrasing. The strings are stable for the new tests, but if you ever centralise the consumer-surface error formatters (the way `finalizer.py` does for `_format_ambiguity_error` / `_format_unresolved_targets_error`), the registry side would be the next candidate. Low priority.

## Notes

- The Slice 1–4 implementation is internally consistent: `registry.iter_types()`'s new "one yield per registered type" contract is matched by the `check_schema` dedupe in [django_strawberry_framework/optimizer/extension.py:653](django_strawberry_framework/optimizer/extension.py:653); the H2 origin-aware planning thread (`source_type=` keyword-only through `plan_optimizations` → `_walk_selections` → `_resolve_field_map`) leaves nested traversal on the primary-routing path (`_plan_select_relation` and `_build_prefetch_child_queryset` deliberately omit `source_type`); and the H1 always-defer change keeps consumer-authored overrides intact through the `consumer_authored_fields` short-circuit in `_build_annotations` ([django_strawberry_framework/types/base.py:621](django_strawberry_framework/types/base.py:621)).
- The "consumer-authored pending record" branch in `finalize_django_types` ([django_strawberry_framework/types/finalizer.py:113-116](django_strawberry_framework/types/finalizer.py:113)) initially looked unreachable post-H1 (`_build_annotations` short-circuits before `_record_pending_relation` for consumer-authored fields), but [tests/test_registry.py:240](tests/test_registry.py:240) (`test_finalize_discards_consumer_authored_pending_relation_without_rewriting_annotation`) deliberately constructs a stale pending record via `registry.add_pending_relation(...)` to pin that defensive branch. It is intentional defense-in-depth, not dead code.
- `_OriginAndModel`'s pair-or-`None` contract is implemented consistently: every early-return in `_resolve_model_from_return_type` returns `None`, including the new `origin is None` branch added in `8cec18a` and now covered in `98302e6`.
