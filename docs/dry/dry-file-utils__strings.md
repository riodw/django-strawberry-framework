# DRY review: `django_strawberry_framework/utils/strings.py`

Status: verified

## System trace

`utils/strings.py` owns four package naming transforms at the GraphQL/Django boundary:

| Symbol | Direction / rule | Primary consumers |
| --- | --- | --- |
| `snake_case` | GraphQL camel/Pascal → Django attr (memoized) | `optimizer/walker.py` selection resolve; `types/base.py` / `types/finalizer.py` `field_map` keys; `inspect_django_type` |
| `pascal_case` / `pascal_case_or_raise` | Django snake → type-name stem (+ empty-token guard) | `types/converters.py` / `rest_framework/serializer_converter.py` choice enums; `filters/inputs.py::_pascal_case`; `sets_mixins.py::ClassBasedTypeNameMixin.type_name_for` |
| `graphql_camel_name` | Django snake → injective GraphQL field wire name | Generated filter/order/mutation/form/serializer inputs via `utils/inputs.py`, family `inputs.py` modules, `mutations/resolvers.py` |
| `flatten_lookup_path` | `LOOKUP_SEP` (`__`) → single `_` identifier | `utils/inputs.py::emit_set_input_field_triples` python-attr; `utils/permissions.py` `check_<field>_permission`; `orders/sets.py` `_dst_order_*` aliases |

Public re-exports: `utils/__init__.py` exposes only `snake_case` / `pascal_case`. `graphql_camel_name` is also re-exported from `utils/inputs.py` for historical import paths; ownership stays here. Filters/orders keep `_camel_case = graphql_camel_name` aliases for spec-era names.

Connected but intentionally separate naming owners examined:

- Strawberry `to_camel_case` — default schema/auto-camel wire prediction (`types/finalizer.py::_audit_field_surface`, `optimizer/walker.py` forward-resolve, mutation input surface audit when `field.graphql_name` is unset).
- `utils/inputs.py::pascalize_token` — injective single-leading-capital shape-suffix tokens for write-input class names; not a Pascal type stem.
- `filters/inputs.py::LOOKUP_NAME_MAP` — fixed django-filter lookup vocabulary (`icontains` → `iContains`); not field-name camelization.

Item-scoped baseline `e97ca44d…` diff for `utils/strings.py`: empty.

## Verification

Searches: all `from …strings import` sites; package-wide `.replace("__", "_")` (only the owner body remains); `to_camel_case` / `graphql_camel_name` / `pascalize_token` / `pascal_case` call sites; no `to_snake_case` imports in package code.

Scratch (`uv run python`): compared `graphql_camel_name` vs `to_camel_case` and `snake_case` vs Strawberry `to_snake_case`.

**Rejected — unify `graphql_camel_name` with Strawberry `to_camel_case`.** Contracts diverge on load-bearing edges:

- Digit boundary injectivity: `field_2` → `field_2` vs `field2` (also `parent_2`, `line_2`, `version_2_value`).
- Leading underscores: `_legacy_id` → `_legacyId` vs `LegacyId`; `__dunder__` → `__dunder__` vs `_Dunder__`.
- Round-trip: `snake_case(graphql_camel_name(x)) == x` for normalized Django identifiers; `snake_case(to_camel_case("field_2")) == "field2"` loses the separator.

Generated inputs pin `graphql_camel_name` (and `strawberry.input(name=…)`) so Strawberry’s lossy converter never owns the wire name. Walker/finalizer/mutation audits must use `to_camel_case` (or the schema `name_converter`) because that is what DjangoType fields emit under default `auto_camel_case`. Unifying would either break injectivity on generated inputs or mis-predict schema wire names.

**Rejected — replace `snake_case` with Strawberry `to_snake_case`.** Same outputs on ordinary camelCase, but diverge when an underscore already precedes an uppercase (`a_B` → `a__b` vs `a_b`; `_A` → `__a` vs `_a`). Ours is documented as the inverse of `graphql_camel_name`, and is `lru_cache`d for the walker hot path. Package never imports `to_snake_case`.

**Rejected — merge `pascal_case` with `pascalize_token`.** Different products: human GraphQL type stems (`IsActive`, `Field_2`) vs uniquely concatenable escaped tokens (`Is_uprivate`, `Field_u2`). Spec-039 already keeps them distinct.

**Rejected — extract shared “digit-leading segment join” between `pascal_case` and `graphql_camel_name`.** Both retain `_` before a digit-leading part, but head/empty/leading-trailing underscore rules differ (Pascal collapses; camel preserves). A shared helper needs mode flags and obscures ownership.

**Rejected — inline leftover camel/snake/pascal/flatten.** No second `.replace("__", "_")` in package source. `_pascal_case` / `_camel_case` wrappers only supply family-specific errors or historical aliases over the shared owner. `LOOKUP_NAME_MAP` literals are a fixed lookup vocabulary, not a parallel case converter (spec-044 also rejects deriving wire-contract debug keys through `graphql_camel_name`).

## Opportunities

None — the four transforms already sit at the true owner; call sites import them; parallel-looking converters (`to_camel_case`, `pascalize_token`, lookup vocabulary) have distinct contracts proved by executable comparison and call-site roles.

## Judgment

Zero-edit. Naming responsibility is correctly concentrated in `utils/strings.py`. The strongest temptation — folding `graphql_camel_name` into Strawberry `to_camel_case` — fails on digit-boundary and leading-underscore injectivity that generated inputs require and that the optimizer must not assume when matching schema wire names.

## Implementation (Worker 1)

No production or test edits. Item-scoped diff vs `e97ca44d34f54ec1d5ab83b5e9eb5272e4be9404` for `django_strawberry_framework/utils/strings.py` and this artifact path: artifact create only; `strings.py` unchanged.

Deferred pytest: none required (no code change). Ready for Worker 2.

## Independent verification (Worker 2)

Re-traced ownership and consumers independently. Confirmed item-scoped diff vs
`e97ca44d34f54ec1d5ab83b5e9eb5272e4be9404` for `utils/strings.py` is empty
(163 lines unchanged).

Challenged every rejected candidate with a fresh scratch script
(`docs/dry/temp-tests/utils-strings/compare_case.py`, `uv run python …`):

- **`graphql_camel_name` ≢ `to_camel_case`:** diverges on `field_2` /
  `parent_2` / `line_2` / `version_2_value` (digit boundary), `_legacy_id` /
  `_leading` / `__dunder__` (leading underscores). Round-trip
  `snake_case(graphql_camel_name(x)) == x` holds for normalized Django ids;
  `snake_case(to_camel_case("field_2")) == "field2"` loses the separator.
  Package `to_camel_case` imports remain only where predicting Strawberry
  default auto-camel (`types/finalizer.py`, `optimizer/walker.py`,
  `mutations/inputs.py::_audit_mutation_input_surface`).
- **`snake_case` ≢ `to_snake_case`:** same on ordinary camelCase; diverges on
  `a_B` → `a__b` vs `a_b` and `_A` → `__a` vs `_a`. No package import of
  `to_snake_case`.
- **`pascal_case` ≢ `pascalize_token`:** e.g. `is_active` → `IsActive` vs
  `Is_uprivate`; `field_2` → `Field_2` vs `Field_u2`; `_leading` → `Leading`
  vs `X_lleading`. Distinct products (type stems vs concatenable tokens).
- **Shared digit-join helper:** `pascal_case` collapses empty/leading/trailing
  underscores; `graphql_camel_name` preserves them (`_legacy_id` → `LegacyId`
  vs `_legacyId`; `double__name` → `DoubleName` vs `double_Name`; `a__2__b` →
  `A_2B` vs `a__2_B`). A shared join needs mode flags.

Missed-consolidation search: sole `.replace("__", "_")` is the owner body;
`capitalize` / `isupper` case logic lives only in `strings.py`; leftover
`_camel_case` / `_pascal_case` are thin aliases or family error wrappers over
this owner; `LOOKUP_NAME_MAP` remains a fixed lookup vocabulary. No further
consolidation warranted.

Verdict: zero-edit claim stands. Status → verified; plan checkbox marked.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
