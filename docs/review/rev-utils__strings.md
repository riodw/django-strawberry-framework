# Review: `django_strawberry_framework/utils/strings.py`

## High:

None.

## Medium:

None.

## Low:

### `snake_case` produces underscore-per-letter for all-upper acronyms

`snake_case("HTMLParser")` returns `"h_t_m_l_parser"`. The docstring scopes the function to "reversing Strawberry's default camelCase," and Strawberry's default name converter only emits camelCase from snake_case Python attributes (so `XML` would already be `xml` in source), making this edge case unreachable through the documented call chain. But if a consumer or a future spec ever feeds an acronym-style GraphQL name through `snake_case`, the result will be unexpected. Either narrow the docstring further ("strict camelCase reversal; acronyms not handled") or add an acronym-aware branch (group runs of uppercase letters as a single boundary). Comment polish — defer.

```django_strawberry_framework/utils/strings.py:31:36
out: list[str] = []
for i, c in enumerate(name):
    if i > 0 and c.isupper():
        out.append("_")
    out.append(c.lower())
return "".join(out)
```

### `pascal_case` silently swallows leading/trailing/double underscores

`pascal_case("_leading")` returns `"Leading"`, `pascal_case("status_")` returns `"Status"`, `pascal_case("double__underscore")` returns `"DoubleUnderscore"`. The docstring documents this on purpose ("keeps generated GraphQL type names stable when consumers use names like `_legacy_id`"), so it is intentional, not a bug. But two distinct Django field names like `status` and `_status` would generate the same enum class name (`<TypeName>StatusEnum`), and the registry's enum cache keys on `(model, field_name)` so the collision would not fire there — the enum *names* would clash in the GraphQL schema but the registry would store both. Pin this trade-off in the docstring or add a check at the converter layer that two fields on the same type do not produce the same `pascal_case` result. Cross-cutting concern — track for the future spec.

```django_strawberry_framework/utils/strings.py:39:53
def pascal_case(name: str) -> str:
    """Convert a ``snake_case`` Django field name to ``PascalCase``.
    ...
```

## What looks solid

- Both functions are pure, deterministic, and have docstring examples covering the typical and edge cases.
- `snake_case` handles the four-shape range from the docstring ("name", "isPrivate", "createdDate", combinations) correctly, which is what the optimizer's selection-tree walker needs to look up Django field names from Strawberry-camelCase response keys.
- `pascal_case` collapses underscores deliberately so generated enum names stay stable when consumers use `_legacy_id`-style fields.
- Module docstring pins the "kept minimal on purpose" rule and names the two consumer paths (optimizer walker, choice-to-enum converter), which is the right amount of context for a small utility module.
- 22% file-level line coverage from this file's own tests, full coverage via integration paths across the suite.

---

### Summary:

Two small, pure case-conversion helpers used at the GraphQL/Django boundary. No correctness bugs. The two Low items are an edge-case narrowing for `snake_case` (all-upper acronyms produce surprising output, but the documented call chain never reaches that input) and a design trade-off note for `pascal_case` (intentional underscore collapsing produces stable but potentially-colliding GraphQL names). Both are deferrable to comment polish or a future spec.

---

### Worker 3 verification

- No source changes this cycle. Both Low items are documentation polish flagged for the comment pass; deferring keeps the change minimal.
- Validation: `uv run pytest -q` -> 353 passed, 4 skipped, 100% coverage.
- Checkbox in `docs/review/review-0_0_3.md`: marked `- [x]`.
