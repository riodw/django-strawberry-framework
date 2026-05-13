# Python TODO Comment Audit

Status: reviewed

## Scope

- Audited TODO occurrences in project `.py` files.
- Current actionable count is 13 actual `# TODO...` comment blocks.
- Raw `TODO` string count is 18 when including docstrings/string literals.
- I do not see 21 actionable TODO comments in the current working tree. The old count appears to include stale Relay TODOs that are now already removed or rewritten in the working tree.

## Still valid TODOs

### Deferred scalar conversions

These remain correct and map to documented deferred scalar-conversion work in `docs/FEATURES.md` and `KANBAN.md`.

- `django_strawberry_framework/types/converters.py:32` — `BigIntegerField` → JSON-safe `BigInt`.
- `django_strawberry_framework/types/converters.py:41` — `ArrayField` conversion.
- `django_strawberry_framework/types/converters.py:45` — `JSONField` / `HStoreField` conversion.

### Deferred Layer 3 metadata typing

- `django_strawberry_framework/types/definition.py:32` — tighten `Any | None` slots once filter/order/aggregate/fieldset/search features ship.

This is still valid. Those Meta subsystems are still planned/deferred, not shipped.

### FieldMeta single-source-of-truth cleanup

These remain valid. The code still re-derives relation shape/cardinality/nullability via `relation_kind(...)` and raw Django field attributes instead of consistently reading `FieldMeta`.

- `django_strawberry_framework/types/base.py:610`
- `django_strawberry_framework/types/converters.py:224`
- `django_strawberry_framework/types/resolvers.py:180`

### FieldMeta mirror-retirement cleanup

These remain valid. The code still writes/reads `_optimizer_field_map` and `_optimizer_hints` compatibility mirrors.

- `django_strawberry_framework/types/base.py:137`
- `django_strawberry_framework/optimizer/extension.py:227`
- `django_strawberry_framework/optimizer/extension.py:487`
- `django_strawberry_framework/optimizer/walker.py:75`
- `django_strawberry_framework/optimizer/walker.py:153`

## Valid concept, but cleanup recommended

### `optimizer/field_meta.py` docstring is inaccurate

- `django_strawberry_framework/optimizer/field_meta.py:27`

The mirror-retirement TODO is conceptually valid, but the docstring says: “The walker already prefers `DjangoTypeDefinition.field_map`.” That is not true in the current code: `optimizer/walker.py:75` still prefers `_optimizer_field_map`.

Recommended change: either fix the docstring wording or actually move the walker to `registry.get_definition(type_cls).field_map`.

### `optimizer/field_meta.py` cross-reference is not actionable

- `django_strawberry_framework/optimizer/field_meta.py:12`

This is not an actionable TODO comment. It is a docstring cross-reference to the SSoT TODOs. It is okay to keep, but it contributes to raw `TODO` line counts.

## Vague / aspirational TODO

### Product filters permission TODO

- `examples/fakeshop/apps/products/filters.py:47`

`# TODO: Implement permission check?` is not a missed current implementation. Filters and permissions are still unshipped, and this file uses aspirational APIs.

Recommended change: rewrite this as a proper anchored comment pointing to the future filters/permissions specs/cards, or remove it until the filters/permissions slice is active. The current wording is too vague to be useful.

## Not real TODO comments

These are string/code references for the review-inspection script’s own output and require no action.

- `scripts/review_inspect.py:662`
- `scripts/review_inspect.py:665`
- `scripts/review_inspect.py:668`

## Missed current implementation check

One previously missed implementation item has already been addressed in the current working tree:

- Relay async `get_queryset` handling is now implemented in `django_strawberry_framework/types/relay.py`.
- The focused test file passes with `uv run pytest tests/types/test_relay_interfaces.py --no-cov` (`59 passed`).

No other current TODO indicates work accidentally missed from the Relay implementation.

## Recommended next actions

1. Fix the inaccurate sentence in `django_strawberry_framework/optimizer/field_meta.py` about the walker already preferring `DjangoTypeDefinition.field_map`.
2. Decide whether to create/anchor a real `spec-fieldmeta-*` document/card for the FieldMeta SSoT and mirror-retirement TODO family.
3. Rewrite or remove the vague TODO in `examples/fakeshop/apps/products/filters.py`.
