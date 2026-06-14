# Review: `django_strawberry_framework/filters/inputs.py`

Status: verified

Supersedes the stale 0.0.7 `rev-filters__inputs.md` (committed Jun 4, `Status: verified`) — the active plan box for this file was unchecked, so this is a fresh 0.0.9 review of the shipped 0.0.8 source. The file last changed at commit `edab6806` (2026-06-13, "DRY pass … set-family substrates"), which moved the neutral materialization / namespace-clear / camel-case / subclass-iteration mechanics into `utils/inputs.py`; this module now keeps the domain-named aliases plus the filter-specific converter pair, builders, and constants.

## DRY analysis

- **Defer: the converter-vs-normalizer `isinstance`-ladder twin.** `convert_filter_to_input_annotation` (inputs.py:340-404) and `normalize_input_value` (inputs.py:407-455) each dispatch on the same six filter-class predicates (`GlobalIDMultipleChoiceFilter` / `GlobalIDFilter` / `BaseCSVFilter` / `RangeFilter|_DjangoRangeFilter` / `ChoiceFilter` / `ListFilter|ArrayFilter`). They are intentional twins, not duplication: the two ladders use *different* branch orders (the converter splits `TypedFilter` out as its own branch and orders `ChoiceFilter` last; the normalizer folds `ChoiceFilter` ahead of `ListFilter` and has no `TypedFilter` branch because at runtime a typed-leaf value normalizes via the scalar tail) and produce different outputs (a type vs a form-data value). Collapsing them behind a shared classifier would re-hide the per-branch divergence. Defer until a third consumer needs the same filter-class -> kind classification; then extract a single `classify_filter(filter_instance) -> FilterKind` enum and let both ladders switch on it.
- **Defer: the `_owner_type_name(owner) or "Filter"` literal appears twice** (inputs.py `_element_annotation` line 323 and `convert_filter_to_input_annotation` line 381), both feeding `_choice_enum_from_filter`'s `type_name`. Two sites, one literal. Defer until a third site needs the same "owner name or `Filter` fallback" derivation; then lift a `_choice_type_name(owner_definition)` one-liner. Not act-now: two sites of a four-character literal is below this package's constant-extraction bar (cf. registry.py's intentional 2x module-string).

## High:

None.

## Medium:

None.

## Low:

### `"Filter"` choice-enum name fallback can collide across models on the None-owner path (forward-looking)

When `owner_definition is None`, `_element_annotation` (inputs.py:323) and the `ChoiceFilter` branch (inputs.py:381) pass the literal `"Filter"` as `type_name` into `_choice_enum_from_filter` -> `convert_choices_to_enum`, which computes the GraphQL enum name as `f"{type_name}{PascalCase(field.name)}Enum"` (`types/converters.py::convert_choices_to_enum` #"enum_name = f"). So two choice fields named identically on *different* models, both first converted with a None owner, would both want the GraphQL name `Filter<Field>Enum`. This does not bite today because (a) `convert_choices_to_enum` checks its `(field.model, field.name)` cache *before* computing the name (`types/converters.py` #"cached = registry.get_enum"), so same model+field always shares one enum regardless of `type_name`, and (b) the finalize path always binds `_owner_definition` before conversion, so the real `DjangoType` name wins; the `None` owner only occurs on a direct-Python converter call. The in-code docstrings at `_element_annotation` and `_choice_enum_from_filter` already document the model-field-as-source-of-truth contract, so this is a recorded-intent edge, not a silent gap. Defer until a `Meta.filterset_class`-less direct converter call over choice columns becomes a supported public entry point; then thread a non-None owner or a per-filterset disambiguator instead of the `"Filter"` literal.

### `_unwrap_enum_member` single-level unwrap is documented but untriggered for nested shapes (forward-looking)

`_unwrap_enum_member` (inputs.py:486-505) unwraps one level; the docstring explicitly notes nested-list / nested-dict inputs are not recursively unwrapped and that "no current consumer produces such shapes." The `BaseCSVFilter` / `ListFilter` / `ArrayFilter` branches map it per-element over a flat iterable, which is correct for every shape the `django-filter` form-field hierarchy yields today. Defer until a nested-collection filter primitive (a `list[list[...]]` or `dict`-valued `ListFilter`) lands; that primitive must add its own per-level walk. No action now — the limit is real but unreachable from the current filter surface.

## What looks solid

### DRY recap

- **Existing patterns reused.** The neutral generated-input mechanics are single-sited in `utils/inputs.py` and re-exported here under the spec-027 Decision 9 names: `FieldSpec`/`build_input_class`/`_camel_case`/`_iter_filterset_subclasses` aliases (inputs.py:56-59), `materialize_input_class` delegating to `materialize_generated_input_class` (inputs.py:805-821), and `clear_filter_input_namespace` delegating to `clear_generated_input_namespace` (inputs.py:824-878). The clear path reads binding attrs from `FilterSet._lifecycle` (`SetLifecycleAttrs`) rather than a re-spelled tuple — verified against `utils/inputs.py::clear_generated_input_namespace` #"binding_attrs = set_root._lifecycle". `INPUTS_MODULE_PATH` (inputs.py:69) is the single pinned module-path constant shared by the factory, `_build_logic_fields`, and `__init__.py`'s `filter_input_type`. `_owner_type_name` (inputs.py:575-583) delegates to `DjangoTypeDefinition.graphql_type_name`, shared with `filters/base.py` and `types/finalizer.py`. `LOOKUP_NAME_MAP` / `_LOGIC_KEYS` are single-sourced here and imported by `filters/sets.py` (verified sets.py:61) — no re-spelling of the python-attr/wire-name pairing.
- **New helpers considered.** Two candidate consolidations evaluated (the converter/normalizer dispatch twin and the `"Filter"` fallback literal) — both deferred-with-trigger above; neither clears the act-now bar this cycle.
- **Duplication risk in the current file.** The repeated `isinstance` ladders across the two public converters are intentional sibling design (different branch order and output domain, see DRY analysis). The repeated `list[_element_annotation(...)]` at inputs.py:372 and 377 is two genuinely distinct branches (CSV-expanded vs typed list primitive) that happen to share an element-derivation call; folding them would mask the CSV-vs-typed semantic split the comments call out.

### Other positives

- **Converter branch order is provably correct.** The most-specific-first ordering in `convert_filter_to_input_annotation` is load-bearing and verified at runtime: `_DjangoRangeFilter` is NOT a `BaseCSVFilter` subclass (confirmed via `issubclass`), so it correctly skips the CSV branch (line 361) and reaches the `RangeFilter` branch (line 373); django-filter's auto-expanded `BaseInFilter`/`BaseRangeFilter` ARE `BaseCSVFilter` and correctly route to the list branch; the package's `RangeFilter`/`ListFilter`/`ArrayFilter` all subclass `TypedFilter`, so the `TypedFilter` catch (line 378) correctly sits *after* them. The Relay-aware `GlobalID*` primitives (subclasses of `Filter`/`MultipleChoiceFilter`) are matched first so they don't fall through to scalar/list.
- **GlobalID type-validation preservation.** `_encode_global_id_input` (inputs.py:463-483) re-encodes a `relay.GlobalID` object back to its base64 wire string rather than decoding to a bare `node_id`, so the bound `GlobalIDFilter.filter` can validate `type_name` before any queryset clause runs (spec-027 L603). String inputs pass through untouched. The docstring records the prior bug (eager decode stripped `type_name` pre-validation) — a real correctness invariant, well-pinned by `test_normalize_input_value_encodes_globalid_object_to_wire_form`.
- **UNSET/None entry guard is single-sited and correct.** `normalize_input_value` short-circuits `None`/`UNSET` at line 438 before any branch indexes/iterates `raw_value`, and `sets.py::_normalize_input` mirrors the same `is_inactive_value` rule per-lookup (sets.py:733) so a partially-supplied operator bag never leaks the sentinel.
- **Range patch contract is coherent end-to-end.** `_normalize_range_value` returns a positional `{<base>_0, <base>_1}` dict, dropping `None` axes (inputs.py:567-572); the `field_name=form_key` override threads the form-key prefix from the caller (sets.py:748/763), and `sets.py::_normalize_input` merges the dict via `data.update(normalized)` (sets.py:751/768) — the multi-key return shape consumed exactly as the docstring promises, no sentinel-pair object.
- **`_unwrap_enum_member` uses structural `isinstance(value, enum.Enum)`** rather than `.value`-truthiness, correctly unwrapping members whose `.value` is legitimately `None` (pinned by `test_normalize_input_value_unwraps_enum_member_with_none_value`) and not misfiring on `decimal.Decimal`-like objects.
- **`_model_field_for_filter` narrowed its except clause** to `FieldDoesNotExist` (inputs.py:769) — a prior broad `except Exception` that masked unrelated `_meta.get_field` failures is gone; unknown names degrade to `None`, any other failure surfaces. Relation traversal walks one `_meta.get_field` hop at a time so the final-hop model field is returned.
- **`_scalar_from_form_field` form-field ordering** matches `bool < bool < Decimal < float < int < datetime < date < time < UUID < str`, with the load-bearing comment that `DecimalField`/`FloatField` subclass `IntegerField` in `django.forms` and MUST precede the `int` catch — pinned by `test_scalar_from_form_field_maps_each_recognized_shape`.
- **`clear_filter_input_namespace` parks materialized classes** rather than `delattr`-ing them, with a thorough docstring explaining the LazyType-survival contract for consumer modules whose autouse-reload fixture doesn't reload the holder. The cleanup contract for `_field_specs` / `_materialized_names` is documented at the module-constant definitions (inputs.py:132-150).
- **Test discipline.** 56 tests in `tests/filters/test_inputs.py` cover every converter branch, both partial-range axes, the CSV/list/enum unwrap paths, the `_pascal_case` no-word-char raises, `HIDE_FLAT_FILTERS` at flat / single-hop / multi-hop depths, the clear-namespace unimportable-submodule tolerance, and the full `LOOKUP_NAME_MAP` table against spec.

### Summary

`filters/inputs.py` is logic-clean at 0.0.9: no High and no Medium. The filter-class dispatch ladders, GlobalID wire-form preservation, UNSET guard, range-patch merge contract, and enum unwrap are all correct and well-tested, and the 0.0.9 DRY pass has already moved the neutral mechanics into `utils/inputs.py` with the domain-named aliases preserved here for spec-027 Decision 9 addressability. The two Lows are forward-looking edge contracts (the `"Filter"` enum-name fallback on the None-owner path, harmless today because of the `(model, field)` enum cache; and the documented single-level enum unwrap), and both DRY candidates are deferred-with-trigger. No GLOSSARY drift: the target's public symbols are not named in `docs/GLOSSARY.md`, and the module-path string plus the lazy-resolution architecture prose (GLOSSARY:470/480/674) accurately describe the shipped behavior. This is a no-source-edit (shape #5) cycle.

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format --check django_strawberry_framework/filters/inputs.py` — `1 file already formatted` (no changes).
- `uv run ruff check django_strawberry_framework/filters/inputs.py` — `All checks passed!`

### Notes for Worker 3
- Two Lows, both forward-looking and intentionally not acted on:
  1. `"Filter"` choice-enum name fallback on the `owner_definition is None` path — deferred-with-trigger ("until a `Meta.filterset_class`-less direct converter call over choice columns becomes a supported public entry point"); harmless today because `convert_choices_to_enum` cache-checks on `(field.model, field.name)` before computing the name and the finalize path always binds a non-None owner.
  2. `_unwrap_enum_member` single-level unwrap — deferred-with-trigger ("until a nested-collection filter primitive lands"); unreachable from the current flat filter surface.
- Two DRY candidates, both deferred-with-trigger (converter/normalizer dispatch twin; `"Filter"` literal 2x). Neither acted on.
- No GLOSSARY-only fix in scope — the target's public symbols are not defined in `docs/GLOSSARY.md`; GLOSSARY prose at lines 470/480/674 referencing the lazy module path is accurate, no drift.
- Branch-order correctness was verified at runtime via `issubclass` (`_DjangoRangeFilter` is NOT `BaseCSVFilter`; package primitives subclass `TypedFilter`) — record for re-verification if django-filter's class hierarchy changes across a dependency bump.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern. No comment/docstring edits warranted — the module docstring, the constant-definition contract comments (`_field_specs` / `_materialized_names` cleanup contracts), the converter branch-order rationale, the GlobalID re-encode bug history, and the `_unwrap_enum_member` / `_element_annotation` known-contract-limit notes are all accurate against the shipped logic.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

Not warranted — no source, test, GLOSSARY, or behavior change this cycle (AGENTS.md: "Do not update CHANGELOG.md unless explicitly instructed"; the active `docs/review/review-0_0_9.md` plan carries no changelog directive for this item).

---

## Verification (Worker 3)

Shape #5 no-source-edit cycle. Baseline `0872a20f` diff for `filters/inputs.py` EMPTY (true no-op). Worker 1 filled all three Worker 2 sections with the `Filled by Worker 1 per no-source-edit cycle pattern.` prefix; both Lows are forward-looking deferred-with-trigger (no GLOSSARY-only fix in scope); changelog `Not warranted` cites BOTH AGENTS.md and the active plan's silence. Ruff format-check (`1 file already formatted`) + check (`All checks passed!`) pass.

### Logic verification outcome
- **Converter branch-order invariants re-confirmed LIVE via `issubclass`** (django setup, `config.settings`): `_DjangoRangeFilter is BaseCSVFilter` -> `False` (so it correctly skips the CSV branch at :361 and reaches the RangeFilter branch :373); package `RangeFilter`/`ListFilter`/`ArrayFilter` ALL `issubclass TypedFilter` -> `True` (so the `TypedFilter` catch :378 correctly sits AFTER them); `GlobalIDFilter is TypedFilter` -> `False` and `GlobalIDMultipleChoiceFilter is BaseCSVFilter` -> `False` (so the Relay primitives matched first at :357/:359 do not fall through, and the auto-expanded django-filter `BaseInFilter`/`BaseRangeFilter`, which ARE `BaseCSVFilter`, route to the list branch). The "most-specific-first" ladder is load-bearing and correct.
- **`"Filter"` choice-enum fallback collision ruled harmless — both legs verified at source.** (a) `types/converters.py::convert_choices_to_enum` does its cache check on `registry.get_enum(field.model, field.name)` at :353-355 and returns the cached enum BEFORE computing `enum_name = f"{type_name}{pascal_case(field.name)}Enum"` at :357 — so for the same `(model, field)` the `type_name` (and thus the `"Filter"` literal) never produces a divergent enum. (b) The finalize path always binds a non-None owner before conversion: `_bind_filtersets` subpass 1 binds `_owner_definition` via `_bind_filterset_owner` (finalizer.py:1303-1359) before subpass-4 materialization; `utils/inputs.py:399-400` reads `getattr(set_cls, "_owner_definition", None)` and threads it through `_build_input_triples` (factories.py:90-97) -> `_build_input_fields` -> `convert_filter_to_input_annotation`. The `None` owner (and thus `"Filter"`) only arises on a direct-Python converter call with no filterset_class — exactly the deferral trigger named. Forward-looking Low correctly deferred.
- **`_unwrap_enum_member` single-level unwrap (forward-looking Low):** docstring (:497-501) documents the limit; the CSV/List/Array branches map it per-element over a flat iterable, correct for every shape the django-filter form-field hierarchy yields today. Correctly deferred with trigger ("until a nested-collection filter primitive lands").
- High 0 / Medium 0; no High-fix-without-test obligation.

### DRY findings disposition
- **Converter/normalizer `isinstance`-ladder twin — deferred-with-trigger, confirmed real.** Verified at source the two ladders genuinely diverge: the converter (:340-404) splits `TypedFilter` into its own branch (:378) and orders `ChoiceFilter` LAST (:380); the normalizer (:407-455) has NO `TypedFilter` branch and folds `ChoiceFilter` (:451) AHEAD of `ListFilter` (:453). Collapsing behind a shared classifier would re-hide the per-branch divergence. Trigger (third consumer) correctly named.
- **`_owner_type_name(owner) or "Filter"` literal 2x (:323, :381) — deferred-with-trigger.** Two sites of a four-char literal, below this package's constant-extraction bar (cf. registry.py 2x module-string). Correctly deferred.

### Temp test verification
- None — no new behavior shipped; branch-order and cache-key invariants confirmed via a direct `issubclass`/`convert_choices_to_enum`-source probe rather than a temp test file.

### Sibling-cycle attribution
Dirty tracked paths in the owned-paths `--stat` (conf.py, exceptions.py, list_field.py, docs/GLOSSARY.md) attribute to CLOSED sibling cycles: rev-conf.md / rev-exceptions.md / rev-list_field.md (all `Status: verified`, `[x]` at review-0_0_9.md:70/72/73); the 1-line GLOSSARY hunk is the `DjangoConnection` entry owned by rev-connection.md (`Status: verified`, `[x]` at review-0_0_9.md:71). Deleted root `feedback2.md`/`feedback3.md` = AGENTS.md #33 concurrent-maintainer work. This cycle's "Files touched: None" claim holds — `filters/inputs.py` baseline diff is empty.

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the checklist box at `docs/review/review-0_0_9.md`.
