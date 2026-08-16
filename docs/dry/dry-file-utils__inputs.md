# DRY review: `django_strawberry_framework/utils/inputs.py`

Status: verified

## System trace

`utils/inputs.py` is the **generated-input construction / lifecycle substrate**
shared by the set families (filter / order) and the write families (model
mutation / form / DRF serializer), plus auth's current-user alias namespace.
Charter: **mechanics only**. Domain leaf semantics stay at the family
`inputs.py` / converter / resolver call sites.

**Owned surfaces (grouped):**

| Cluster | Symbols | Role |
| --- | --- | --- |
| Set emission | `GeneratedInputFieldSpec`, `optional_field_kwargs`, `emit_set_input_field_triples` | Filter/order field triples + provenance rows; early attr/GraphQL collision fail |
| Write reverse-map | `SCALAR` / `RELATION_*` / `FILE`, `FieldConversionBase`, `InputFieldSpec`, `optional_input_field` | Decode-kind vocabulary + reverse-map record + optional-widen tail |
| Naming | `pascalize_token`, `generated_input_type_name`, re-export `graphql_camel_name` | Injective type-name / token machinery; camel owner stays `utils/strings.py` |
| Meta narrowing | `normalize_field_name_sequence`, `resolve_effective_fields`, `guard_dropped_required` | Write-flavor `fields`/`exclude` shape + effective-set spine + create-required drop |
| Build / materialize | `build_strawberry_input_class`, `materialize_generated_input_class`, `duplicate_name_message`, `make_input_namespace`, `make_shape_build_cache` | `@strawberry.input` construction, parked-global ledger, light write-namespace trio, shape caches |
| Collision / lazy | `iter_input_field_collisions`, `build_lazy_input_annotation` | Write-input collision messages; Decision-11 lazy annotation for set helpers |
| Set lifecycle | `iter_set_subclasses`, `_safe_import`, `clear_generated_input_namespace`, `GeneratedInputArgumentsFactory` | Heavy set-namespace clear + BFS factory substrate |

**Confirmed consumers (already delegated — no leftover parallel builders):**

- **Set re-exports:** `filters/inputs.py` / `orders/inputs.py` alias
  `FieldSpec` / `build_input_class` / `_camel_case` / `_iter_*set_subclasses`;
  both call `emit_set_input_field_triples`, `materialize_generated_input_class`,
  `clear_generated_input_namespace`. Factories subclass
  `GeneratedInputArgumentsFactory`. `__init__.py` helpers use
  `build_lazy_input_annotation`.
- **Write materialize:** `mutations/inputs.py`, `forms/inputs.py`,
  `rest_framework/inputs.py` use `make_input_namespace` (light clear),
  `build_strawberry_input_class`, `optional_input_field`,
  `iter_input_field_collisions`, `generated_input_type_name` /
  `pascalize_token`. Forms + serializer also use `resolve_effective_fields` /
  `guard_dropped_required`. Auth `auth/queries.py` uses `make_input_namespace`.
- **Write Meta:** `mutations/sets.py`, `forms/sets.py`,
  `rest_framework/sets.py` / `inputs.py` call `normalize_field_name_sequence`
  and `make_shape_build_cache`. `reject_unknown_meta_keys` lives on
  `mutations/sets.py` (write Meta typo guard owner — traced, not claimed here).
- **Decode walk:** `iter_provided_input_fields` consumed by mutations /
  forms / DRF resolvers and `utils/write_values.py`.
- **Traversal (different module):** `utils/input_values.py` owns set-input
  active-field classification (`iter_active_fields`); not a second builder.

Item baseline `0715b79d974fdd0da9451a0e824f5728c615d755`: target hash matches
baseline (empty item-scoped diff for the target). No production edits.

## Verification

Searches across `django_strawberry_framework/`:

- `build_strawberry_input_class` / `strawberry.input(` — every triple-built
  generated input routes through this builder. The only other
  `strawberry.input(type(...))` site is `mutations/sets.py`'s consumer+remainder
  **inheritance merge** (not field-triple construction).
- `materialize_generated_input_class` / `make_input_namespace` /
  `clear_generated_input_namespace` — set families keep hand wrappers + heavy
  clear (factory caches + `_lifecycle` binding); write/auth use the light
  `make_input_namespace` trio. No third ledger shape.
- `seen_attr` / `seen_graphql` / collision walks — only
  `emit_set_input_field_triples`, `build_strawberry_input_class`,
  `iter_input_field_collisions` (generated inputs) plus
  `types/finalizer.py::_audit_field_surface` (DjangoType output surface under
  Strawberry `to_camel_case`).
- `normalize_field_name_sequence` vs `types/base.py::_normalize_fields_spec` /
  `_normalize_sequence_spec` — separate contracts (see rejected).
- `graphql_camel_name` vs `to_camel_case` — package injective naming vs
  Strawberry default converter (scratch below).
- `iter_provided_input_fields` vs `input_values.iter_active_fields` — UNSET-only
  write decode walk vs set active-input classification.

Scratch (`uv run python`, in-process):

```text
field_2 / field2: to_camel_case collapses both to field2;
                  graphql_camel_name keeps field_2 distinct from field2
foo_bar / fooBar: both algorithms collapse (true GraphQL collision either way)
```

Optional `export_dry_review.py audit` used for orientation only; judgments are
from call-graph + contract comparison.

Permanent pins already live in `tests/utils/test_inputs.py` (plus family
`tests/{filters,orders,forms,mutations,rest_framework}/test_inputs.py`).
Pytest not run (AGENTS.md); deferred for W2 / final gate.

## Opportunities

None — this module is already the single owner of generated-input mechanics.
Connected families are thin wrappers / re-exports / parameterized hooks.
Independent re-check of the named prior rejections (from this file's side)
confirms they must stay separate; no leftover parallel builder or ledger was
found.

## Judgment

Proved zero-edit. The set/write split (heavy vs light clear, FieldSpec vs
InputFieldSpec, emission scaffold vs reverse-map) is intentional ownership,
not unfinished consolidation. Strongest rejected candidates below.

### Rejected: unify `types/finalizer.py::_audit_field_surface` with
`iter_input_field_collisions`

- **Seemed shared:** both fail loud when two names collapse to one GraphQL
  wire name so Strawberry cannot silently drop a field.
- **Disproof:** different surfaces and **different camel algorithms**.
  Finalizer audits the DjangoType **output** field set under Strawberry's
  `to_camel_case` (what default `auto_camel_case=True` would do on undeclared
  names). Generated inputs pin wire names with package
  `graphql_camel_name` and audit via `iter_input_field_collisions` /
  `emit_set_input_field_triples` / `build_strawberry_input_class`. Scratch
  shows `field_2` vs `field2` collapses under `to_camel_case` but not under
  `graphql_camel_name`. Unifying would either false-positive injective
  generated names or miss Strawberry-default DjangoType collisions.
- **Keep separate.** Finalizer owns type-surface audit; this module owns
  generated-input collision messaging.

### Rejected: unify `types/base.py` Meta fields/exclude normalize with
`normalize_field_name_sequence`

- **Seemed shared:** both coerce `Meta.fields` / `Meta.exclude` declarations.
- **Disproof:** `normalize_field_name_sequence` is write-flavor sequence
  shape (reject bare string, non-string entries, duplicates; no `__all__`).
  `types/base.py::_normalize_fields_spec` accepts `__all__` and stores on
  `DjangoTypeDefinition`; `_normalize_sequence_spec` also accepts sets for
  unordered Meta keys. Field-existence / model-selection stays in
  `_select_fields`. Same English words, different contracts and change axes.
- **Keep separate.** Write narrowing stays here; DjangoType Meta stays in
  `types/base.py`.

### Rejected: fold `emit_set_input_field_triples` collision into
`iter_input_field_collisions`

- **Seemed shared:** both maintain `seen_attr` / `seen_graphql` and reject
  silent overwrite before `build_strawberry_input_class`.
- **Disproof:** emit runs **during** set-member emission (identity =
  Django path `top_name`, attributes = `python_attr` after
  `flatten_lookup_path`, also records `GeneratedInputFieldSpec`). Iter walks
  already-built write specs (`.input_attr` / `.graphql_name` / optional
  `source_of`, yield-vs-raise policy at call site, split
  `check_input_attrs` / `check_graphql_names`). Forcing emit through iter
  needs adapter objects or mode flags and couples set emission to the write
  reverse-map shape. Last-line defense in `build_strawberry_input_class`
  remains a third, intentional layer (generic wording, annotation-dict keys).
- **Keep layered.** Domain early-fail (emit) → write-spec audit (iter) →
  builder last-line (build).

### Rejected: route set families through `make_input_namespace`

- **Seemed shared:** filters/orders still hand-wrap
  `materialize_generated_input_class` + own `_materialized_names`.
- **Disproof:** `make_input_namespace` is the **light** clear
  (`ledger.clear()` only). Set families need
  `clear_generated_input_namespace` (ledger + `field_specs` + factory caches +
  `_lifecycle` binding attrs). Half-adopting the light trio and ignoring its
  clear would obscure the heavy/light split the module docstring already
  documents.
- **Keep.** Thin family wrappers + heavy clear remain correct.

### Rejected: merge `GeneratedInputFieldSpec` with `InputFieldSpec` /
`optional_field_kwargs` with `optional_input_field` /
`iter_provided_input_fields` with `input_values.iter_active_fields`

- Set provenance (`python_attr` / `graphql_name` / `django_source_path`) vs
  write reverse-map (`input_attr` / `target_name` / `kind` / `source` /
  `related_model` / `nested_specs`) — different decode contracts.
- Optional `default=None` (set fields always omittable) vs widen-to-`UNSET`
  (write required-vs-optional) — opposite presence rules under
  `build_strawberry_input_class`.
- Write UNSET-strip over `__strawberry_definition__.fields` vs set
  active-input classification (`None` / family sentinel, leaf/related/logic)
  — already split across this module and `utils/input_values.py`.

### Rejected: absorb `reject_unknown_meta_keys` into this module

Traced as connected Meta hygiene. Owner is `mutations/sets.py` (write
declaration typo guard; forms/serializer call it). Parallel own-keys scan in
`types/base.py::_validate_meta` also handles `DEFERRED_META_KEYS`. Neither
belongs in generated-input construction.

## Implementation (Worker 1)

Zero-edit. No production or test changes. Item-scoped diff vs
`0715b79d974fdd0da9451a0e824f5728c615d755` for
`django_strawberry_framework/utils/inputs.py` is empty; only this artifact is
new.

Deferred pytest: none required for a zero-edit; existing
`tests/utils/test_inputs.py` (+ family input tests) remain the permanent pins
for W2 spot-check if desired.

## Independent verification (Worker 2)

**Outcome:** verified. Zero-edit claim holds. Plan checkbox marked `[x]`.

**Item-scoped diff:**
`git diff 0715b79d974fdd0da9451a0e824f5728c615d755 -- django_strawberry_framework/utils/inputs.py`
is empty (confirmed).

**Re-trace (independent):** Full present-day `utils/inputs.py` (~1163 lines).
Materialization ledger (`materialize_generated_input_class` + light
`make_input_namespace` vs heavy `clear_generated_input_namespace`), set emission
(`emit_set_input_field_triples`), write reverse-map / collision walk
(`InputFieldSpec` / `iter_input_field_collisions`), Meta narrowing
(`normalize_field_name_sequence` / `resolve_effective_fields`), and
`build_strawberry_input_class` last-line defense all live here once. Consumers
are thin wrappers / re-exports (filters/orders/mutations/forms/rest_framework/auth).
Only other `strawberry.input(type(...))` site is
`mutations/sets.py` consumer+remainder **inheritance merge** — not field-triple
construction.

**Independent leftover search:** No parallel generated-input builder, second
ledger shape, or bypass of `build_strawberry_input_class` for triple-built
inputs. Set families still hand-wrap materialize + call heavy clear; write/auth
use the light trio — intentional.

**Challenges to rejected candidates (source evidence):**

1. **Finalizer `_audit_field_surface` vs `iter_input_field_collisions`** —
   Confirmed separate. Finalizer groups under Strawberry `to_camel_case`;
   generated inputs pin/audit via `graphql_camel_name`. Fresh scratch:
   `field_2`/`field2` → both `field2` under `to_camel_case`, distinct under
   `graphql_camel_name`; `foo_bar`/`fooBar` collapse both ways. Unifying would
   false-positive injective generated names or miss DjangoType default-camel
   collisions. Keep separate.

2. **`types/base` Meta normalize vs `normalize_field_name_sequence`** —
   Confirmed separate contracts. `_normalize_fields_spec` accepts `__all__` and
   does not duplicate-check; `_normalize_sequence_spec` accepts sets for
   unordered Meta keys. Write helper rejects bare string / non-string /
   duplicates and has no `__all__`. Same English words, different change axes.
   Keep separate.

3. **`emit_set_input_field_triples` collision vs `iter_input_field_collisions`** —
   Confirmed layered, not duplicative. Emit identity is Django path `top_name`
   → `python_attr` after `flatten_lookup_path`, records `GeneratedInputFieldSpec`.
   Iter walks write specs (`.input_attr` / `.graphql_name`, optional `source_of`,
   yield-vs-raise + `check_input_attrs`/`check_graphql_names` split). Folding
   needs adapter objects/mode flags. Builder last-line remains intentional third
   layer. Keep layered.

4. **Set families through `make_input_namespace` vs heavy clear** —
   Confirmed. Light clear is `ledger.clear()` only. Filters/orders
   `clear_*_input_namespace` pass factory caches + `_lifecycle.binding_attrs`
   into `clear_generated_input_namespace`. Half-adopting the light trio would
   obscure the documented heavy/light split. Keep.

5. **Additional candidate challenged (not in W1 list):**
   `mutations/inputs.py::_audit_mutation_input_surface` walks a built
   `__strawberry_definition__.fields` surface with
   `field.graphql_name or to_camel_case(...)` at materialize time so merged
   consumer+remainder collisions are visible. Single caller; post-build /
   inheritance-merge timing; Strawberry-default fallback camel — not the same
   contract as pre-build `iter_input_field_collisions` or injective
   `graphql_camel_name` emission. Not a consolidation into this module.
   Keep at mutation materialize boundary.

**Remaining issues:** none for this item.
