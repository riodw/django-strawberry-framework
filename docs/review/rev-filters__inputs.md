# Review: `django_strawberry_framework/filters/inputs.py`

Status: verified

## DRY analysis

- None — the shared generated-input substrate is already single-sited in `utils/inputs.py` (the 0.0.9 DRY pass): `FieldSpec`/`build_input_class`/`_camel_case`/`_iter_filterset_subclasses` are domain-local aliases (`inputs.py:57-60`) of `GeneratedInputFieldSpec`/`build_strawberry_input_class`/`graphql_camel_name`/`iter_set_subclasses`, and `materialize_input_class`/`clear_filter_input_namespace` (`inputs.py:810-883`) are thin delegations to `materialize_generated_input_class`/`clear_generated_input_namespace`. The order twin (`orders/inputs.py`) shares the identical alias block and delegation pair — the convergence is complete, not a residual. The two same-named `normalize_input_value` functions are NOT a shared traversal: the filter version is a flat isinstance-ladder mapping ONE raw value to django-filter form-data by filter class (`inputs.py:412-460`), while the order version walks the input dataclass structure via `utils/input_values.py::iter_active_fields` (`orders/inputs.py:298-319`). Different abstraction levels (value-shape adapter vs. structure walker); folding them would invent a false abstraction. Cross-file shape overlap with `orders/inputs.py` is noted for the folder pass but must not be force-merged here.

## High:

None.

## Medium:

None.

## Low:

### `_iter_filterset_subclasses` alias has no production source consumer

`_iter_filterset_subclasses = iter_set_subclasses` (`inputs.py:60`) is referenced only by tests (`tests/filters/test_inputs.py:44`, `tests/utils/test_inputs.py:85` identity assertion) — no production call site in `django_strawberry_framework/`. It is part of the spec-027 Decision 9 "stay addressable here" alias block whose stated purpose (`inputs.py:53-56`) is keeping these names importable from this module for `factories.py` and tests; the order twin keeps the symmetric `_iter_orderset_subclasses` alias (`orders/inputs.py:53`) for the same reason. Correct as a deliberate family-symmetry surface, not dead code to strip. No action: removing it would break the documented addressability contract and the cross-family parity. Recorded only to pre-empt re-flagging in the folder pass.

### `construct_search` is a deferred-card helper landed early

`construct_search` (`inputs.py:789-802`) and its `LOOKUP_PREFIXES` constant (`inputs.py:75-80`) serve the `Meta.search_fields` card deferred to `0.1.2`; the docstring documents the early-landing rationale (the prefix vocabulary would otherwise be dead code) and `filters/sets.py:345` carries the TODO-anchored wiring comment for the future consumer. Exercised directly by `tests/filters/test_inputs.py:545-567`. No action — this is the package's standing pattern (land the constant + helper with tests when it would otherwise be unreachable dead code), correctly documented. Recorded to pre-empt re-flagging.

## What looks solid

### DRY recap

- **Existing patterns reused.** Generated-input substrate fully delegated to `utils/inputs.py` via the alias block (`inputs.py:57-60`) and the two thin wrappers `materialize_input_class`/`clear_filter_input_namespace` (`inputs.py:820-826`, `inputs.py:875-883`); scalar resolution delegated to `types.converters.scalar_for_field` (`inputs.py:267-269`) and enum derivation to `convert_choices_to_enum` (`inputs.py:292-301`), so a filter input and the selected `DjangoType` resolve a column to the SAME scalar/enum; pascal-casing delegated to `utils.strings.pascal_case` (`inputs.py:182`) with only the no-word-character guard added locally; owner-name derivation delegated to `DjangoTypeDefinition.graphql_type_name` (`inputs.py:588`) shared with two other call sites named in the docstring.
- **New helpers considered.** Unifying the filter/order `normalize_input_value` pair — rejected: different abstraction levels (raw-value adapter vs. dataclass-structure walker), no shared body. Hoisting the `convert_filter_to_input_annotation` / `normalize_input_value` isinstance-ladders into a shared filter-family dispatch table — rejected: the two ladders carry divergent per-branch logic (annotation construction vs. form-data coercion) and the branch ORDER is a load-bearing correctness contract (Relay primitives → typed family → ChoiceFilter → scalar catch-all, documented at `inputs.py:350-359`); a table indirection would obscure the order without removing a real near-copy.
- **Duplication risk in the current file.** Repeated literals are all incidental: `"contains"`/`"istartswith"`/`"week_day"` recur inside `LOOKUP_NAME_MAP` keys vs. their tuple values (`inputs.py:91-118`) — distinct roles (django-filter lookup token vs. python attr/graphql name), not a hoist; `"FilterSet"` appears as the family label passed to `materialize_generated_input_class` (`inputs.py:824`) and the `set_class_name` clear arg (`inputs.py:882`) — same family, two call shapes, not a const candidate; `"field_name"` is the reflective `getattr` key for the django-filter attribute (`inputs.py:524`, `inputs.py:761`), the standard attribute name. The `_element_annotation` model-field-first / form-field-fallback duplication across the `BaseCSVFilter` / `ListFilter`/`ArrayFilter` / `TypedFilter` / catch-all branches (`inputs.py:377-405`) is already single-sited in the `_element_annotation` helper (`inputs.py:304-337`).

### Other positives

- **Edge-case correctness is carefully sited and documented.** The `forms.DecimalField`/`forms.FloatField`-before-`forms.IntegerField` ordering in `_scalar_from_form_field` (`inputs.py:229-234`) is correct against the django.forms hierarchy (both subclass `IntegerField`, unlike the model-field hierarchy) and the inline comment explains why; the `isnull`-is-`bool`-regardless-of-column-type branch (`inputs.py:400-403`); the `BaseCSVFilter` list-shape branch that prevents a lone scalar mis-parsing as a 1-element list (`inputs.py:366-377`); the `bool(... required ...)` → `annotation | None` nullability gate (`inputs.py:407-408`) applied uniformly after the type ladder.
- **GlobalID type-preservation is a real fixed bug, documented.** `_encode_global_id_input` (`inputs.py:468-488`) re-encodes a `relay.GlobalID` object back to its base64 wire form rather than decoding to a bare `node_id`, so the bound filter can validate `type_name` BEFORE any queryset clause (spec-027 L603); the docstring records the prior eager-decode defect that silently passed wrong-type GlobalIDs. A `str` passes through unchanged.
- **`_unwrap_enum_member` uses structural `isinstance(value, enum.Enum)`** (`inputs.py:508-510`) not `.value`/`.name` duck-typing — correctly unwraps a member whose `.value` is legitimately `None` and never misfires on plain objects exposing a `.value` (e.g. `decimal.Decimal`); the prior value-truthiness guard is documented as the fixed defect.
- **`_model_field_for_filter` narrows to `FieldDoesNotExist`** (`inputs.py:774-780`) rather than the prior broad `except Exception` that masked unrelated `_meta.get_field` failures; relation traversal walks one `_meta.get_field` hop at a time (`inputs.py:771-785`) so `galaxy__name` resolves through to `Galaxy.name`.
- **`_normalize_range_value` drops `None`-valued axes** (`inputs.py:573-576`) so partial-range inputs surface only the supplied positional `{<name>_0}`/`{<name>_1}` key, matching Django's `RangeWidget.value_from_datadict` positional-key contract (NOT `_from`/`_to`); handles both attribute-object and dict raw values.
- **`normalize_input_value` short-circuits `UNSET` alongside `None`** at the single entry guard (`inputs.py:443-444`) so the sentinel never reaches the iterate/coerce branches — the documented single defensive line every caller inherits.
- **`_build_input_fields` skips expanded `RelatedFilter` duplicates** (`inputs.py:642-643`) before they reach the leaf branch and trip the ChoiceFilter guard; `HIDE_FLAT_FILTERS` (default `False`, matching django-graphene-filters) is a single in-loop skip rather than upstream's throwaway trimmed-subclass + flat-args merge (`inputs.py:659-687`).
- **Local imports break the `types.converters` cycle** (`inputs.py:267`, `inputs.py:292`, `inputs.py:629`, `inputs.py:756`) — the documented pattern, not a smell.
- **Cross-references verified on disk:** `DjangoTypeDefinition.graphql_type_name` (`types/definition.py:193`), `FilterSet.type_name_for` via `sets_mixins.py:77`, `scalar_for_field` (`types/converters.py:119`), `convert_choices_to_enum` (`types/converters.py:301`), and the six `utils/inputs.py` exports (`GeneratedInputFieldSpec:39`, `graphql_camel_name:53`, `build_strawberry_input_class:66`, `materialize_generated_input_class:103`, `iter_set_subclasses:177`, `clear_generated_input_namespace:215`) all resolve.
- **No GLOSSARY drift.** `FilterSet` (GLOSSARY.md:482), `filter_input_type` (494), `RelatedFilter` (1014), `Meta.filterset_class` (692), and the `SyncMisuseError` FilterSet-related-visibility entry (1295) all describe behavior this module participates in accurately; no symbol from this file has stale GLOSSARY prose.

### Summary

`filters/inputs.py` is mature standing code (cycle diff against the baseline is empty — the file was not touched this cycle). It is the filter-side input namespace: a filter-instance → Strawberry-annotation converter pair, a runtime value normalizer, range/GlobalID/enum value helpers, the per-filterset input-field builder, and the module-global materialize/clear pair. Every reusable mechanism is already delegated to the shared `utils/inputs.py` substrate single-sited in the 0.0.9 DRY pass, and the converter's branch-order, nullability gate, and the several documented edge-case fixes (GlobalID type-preservation, structural enum unwrap, `FieldDoesNotExist` narrowing, partial-range axis dropping) are all correct. No High, Medium, or actionable Low findings; the two Lows are no-action pre-empt-re-flag notes on intentional forward-keeping surfaces (`_iter_filterset_subclasses` alias, `construct_search` deferred helper). This is a no-findings + no-source-edit cycle (shapes #1 → #5).

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
None — no-source-edit cycle.

### Tests added or updated
None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass, 267 files left unchanged.
- `uv run ruff check --fix .` — pass, all checks passed.

### Notes for Worker 3
- No GLOSSARY-only fix in scope (no GLOSSARY drift found).
- Low #1 (`_iter_filterset_subclasses` alias, no production consumer): no-action — deliberate spec-027 Decision 9 addressability/parity surface, tests assert its identity; recorded to pre-empt re-flag. Forwarded for the filters/ folder pass to confirm the alias-block symmetry with `orders/inputs.py` stays the intended two-family shape.
- Low #2 (`construct_search` deferred-card helper): no-action — landed early per the package's land-with-tests-to-avoid-dead-code pattern; `Meta.search_fields` card deferred to 0.1.2, wiring TODO anchored at `filters/sets.py:345`.
- Cross-file note for folder pass: the filter/order `normalize_input_value` pair and the alias block are intentional sibling design, NOT a consolidation target — the substrate is already single-sited in `utils/inputs.py`.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern. Logic-first review found no comment/docstring defects: module docstring, the per-helper docstrings, and the dense provenance comments on `LOOKUP_NAME_MAP` / `_LOGIC_KEYS` / `_field_specs` / `_materialized_names` accurately describe current behavior and their consumers; no stale TODOs (overview reports 0 TODO comments); the `construct_search` deferred-card note correctly names the 0.1.2 target.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

Not warranted — no source edit in this cycle (empty diff against the baseline). Per AGENTS.md "Do not update CHANGELOG.md unless explicitly instructed" and the active plan (`docs/review/review-0_0_10.md`) carrying no changelog directive for this item.

---

## Verification (Worker 3)

### Logic verification outcome
No High / Medium / actionable Low findings to adjudicate. Both Lows confirmed genuinely no-action against source + tests:

- **Low #1 (`_iter_filterset_subclasses` alias, `inputs.py:60`):** grep over `django_strawberry_framework/` returns ZERO production call sites; the only consumers are `tests/filters/test_inputs.py:44` (import) / `:1053` (call) and `tests/utils/test_inputs.py:85` (identity assertion `is iter_set_subclasses`). The order twin `_iter_orderset_subclasses` lives at `orders/inputs.py:52` with the symmetric test at `tests/utils/test_inputs.py:86` and `tests/orders/test_inputs.py:856/872`. Confirmed deliberate spec-027 Decision 9 addressability/parity surface (alias-block rationale at `inputs.py:53-56`), not dead code. No-action correct; forwarded to the folder pass to confirm two-family symmetry.
- **Low #2 (`construct_search`, `inputs.py:789`):** defined here, exercised directly by `tests/filters/test_inputs.py:545` / `:566`; future-consumer wiring TODO anchored verbatim at `filters/sets.py:345` ("wire `construct_search(all_filters)` from"). Land-with-tests-to-avoid-dead-code pattern; `Meta.search_fields` card deferred to 0.1.2. No-action correct.

Independently sanity-checked the Worker-1-cleared input-type shapes by reading source: (a) **branch order** in `convert_filter_to_input_annotation` (`inputs.py:362-405`) is most-specific-first — GlobalID primitives (subclass `Filter`/`MultipleChoiceFilter`) → `BaseCSVFilter` → `RangeFilter`/`_DjangoRangeFilter` → `ListFilter`/`ArrayFilter` → `TypedFilter` → `ChoiceFilter`/`TypedChoiceFilter` → scalar catch-all; the order is load-bearing (GlobalID/CSV would fall through to scalar/list otherwise). (b) **lookup-expr mapping** `LOOKUP_NAME_MAP` (`inputs.py:91-118`): `in` → `("in_", "in")` (Python-keyword guard), `icontains` → `("i_contains", "iContains")` (Strawberry can't camel-case without an underscore), `week_day` → `weekDay`; the shadow's "repeated literals" (`contains`/`istartswith`/`week_day`) are key-vs-value role splits, not hoist candidates. (c) **nullability gate** `if not required: annotation = annotation | None` (`inputs.py:407-408`) applied uniformly after the ladder; the `isnull`-is-`bool`-regardless-of-column branch (`inputs.py:400-403`) correctly sits inside the catch-all before the gate.

### DRY findings disposition
DRY = single justified `None`, confirmed sound. The filter-side `normalize_input_value` (`inputs.py:412-460`) is a flat isinstance-ladder mapping ONE raw value to django-filter form-data by filter class; the order-side `normalize_input_value` (`orders/inputs.py:260-320`) is a structure walker that recurses the input dataclass via `utils/input_values.py::iter_active_fields` and emits `list[(django_source_path, Ordering|None)]` (verified by reading both bodies). Different abstraction levels, no shared body — folding would invent a false abstraction. Cross-file shape overlap with `orders/inputs.py` correctly recorded for the folder pass, not force-merged here. The generated-input substrate is already single-sited in `utils/inputs.py` (the alias block `inputs.py:57-60` + the two thin delegations `materialize_input_class`/`clear_filter_input_namespace`).

### Temp test verification
None. No temp tests created; all claims verifiable by source read + grep.

### Shape #5 (no-source-edit) checks
1. `git diff --stat df19325d168107289eaf90fe1f6aa9de8b215852 -- django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md` — empty over all owned paths; no sibling-cycle attribution needed.
2. Both Worker 2 sections start with `Filled by Worker 1 per no-source-edit cycle pattern.` (Fix report, Comment/docstring pass, Changelog disposition all preambled).
3. Every Low has no-action verbatim phrasing (#1) or forward note (#1 folder pass); no GLOSSARY-only fix in scope.
4. Changelog `Not warranted` cites BOTH AGENTS.md and the active plan's silence; `git diff -- CHANGELOG.md` empty.
5. `uv run ruff format --check` (1 file already formatted) + `uv run ruff check` (all checks passed) on `filters/inputs.py`.

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the `filters/inputs.py` checklist box in `docs/review/review-0_0_10.md`.
