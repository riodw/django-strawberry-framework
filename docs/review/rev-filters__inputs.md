# Review: `django_strawberry_framework/filters/inputs.py`

Status: verified

## DRY analysis

- **Defer-with-trigger: cross-family `inputs.py` mirror (`filters/inputs.py` vs `orders/inputs.py`).** The two modules run parallel scaffolds — family-wrapper `materialize_input_class` (`filters/inputs.py::materialize_input_class` / `orders/inputs.py::materialize_input_class`), `clear_*_input_namespace` (`filters/inputs.py::clear_filter_input_namespace` / `orders/inputs.py:380` `clear_order_input_namespace`), `_build_input_fields`, `normalize_input_value`, and the `_field_specs` / `FieldSpec` provenance ledger. The mechanics are already single-sited in `utils/inputs.py` (the 0.0.9 DRY pass); each module's wrapper only pins family-specific constants (`module_path` / `family_label="FilterSet"` vs `"OrderSet"` / `ledger` / factory + set class names). Consolidating the wrappers further would re-introduce a per-family parameter object for no readability gain. **Trigger: a third generated-input family lands (e.g. the aggregates `AggregateSet` set), making the family-constant variation a 3-way table** — at that point fold the three `materialize_*` / `clear_*` wrappers through a single `(module_path, family_label, ledger, factory_module, factory_class_name, collision_registry_attr, set_module, set_class_name)` family descriptor. This is a folder/project-pass concern, not a local defect — forwarded to `docs/review/rev-filters.md` (folder pass) and `docs/review/rev-django_strawberry_framework.md` (project pass). Do not re-flag as act-now until the third family exists.

- **Defer-with-trigger: `_pascal_case` no-word-character guard vs `sets_mixins.py::ClassBasedTypeNameMixin.type_name_for`'s sibling guard.** `filters/inputs.py::_pascal_case` (lines 166-190) wraps `utils.strings.pascal_case` with a "no word characters -> `ConfigurationError`" guard whose message names the `RangeFilter` consumer specifically; `sets_mixins.py::ClassBasedTypeNameMixin.type_name_for` pairs the same shared helper with its own sibling guard for the indirect callers. Two near-identical guards over one shared helper, differing only by error-message wording (direct `RangeFilter` caller vs indirect class-naming callers). **Trigger: a third direct `pascal_case`-with-guard caller appears** — then extract `_pascal_case_or_raise(name, *, subject: str)` to `utils/strings.py` taking the caller-specific subject string. Today the two messages are intentionally caller-specific and the divergence is load-bearing for the error surface (the docstring at lines 176-181 documents exactly this), so not act-now.

## High:

None.

## Medium:

None.

## Low:

None.

## What looks solid

### DRY recap

- **Existing patterns reused.** The module is a textbook thin-wrapper-over-`utils` shape. `FieldSpec` / `build_input_class` / `_camel_case` / `_iter_filterset_subclasses` are domain-local aliases over the shared `utils/inputs.py` substrate (lines 58-61). `_pascal_case` delegates case conversion to `utils.strings.pascal_case` (line 183, confirmed at `utils/strings.py:55`). `_scalar_from_model_field` / `_choice_enum_from_filter` route through `types.converters.scalar_for_field` / `convert_choices_to_enum` (confirmed at `types/converters.py:249,493`) so a filter input and the selected `DjangoType` field resolve a column to the SAME GraphQL scalar/enum. `_owner_type_name` single-sites `DjangoTypeDefinition.graphql_type_name` (`types/definition.py:199`) for its three callers (this helper, `filters/base.py::_accepted_globalid_type_names` at `base.py:257`, `types/finalizer.py::_bind_filterset_owner`). `materialize_input_class` / `clear_filter_input_namespace` delegate lifecycle to `utils/inputs.py::materialize_generated_input_class` / `clear_generated_input_namespace` (confirmed at `utils/inputs.py:103,215`). `is_inactive_value` (`utils/input_values.py:74`) backs the UNSET/None short-circuit in `normalize_input_value`. `_input_type_name_for` pins to `FilterSet.type_name_for()` (the shared `ClassBasedTypeNameMixin`, `sets_mixins.py:77`).
- **New helpers considered.** Two evaluated and deferred-with-trigger (see `## DRY analysis`): the cross-family `inputs.py` mirror (trigger: third generated-input family) and the `_pascal_case` guard pair (trigger: third direct guarded caller). Neither is act-now: the family wrappers already bottom out in single-sited `utils` mechanics and only differ by family constants; the guard pair's messages are intentionally caller-specific.
- **Duplication risk in the current file.** `LOOKUP_NAME_MAP` (lines 92-119) is a single-source-of-truth lookup table consumed by reference from `filters/sets.py:62,81-88` (reverse map built once at import) — not a duplicated literal. `_LOGIC_KEYS` (line 131) is likewise the single source for the `and_`/`or_`/`not_` pairing, imported by `filters/sets.py:62,66,94,1084`. The repeated `isinstance` branches in `convert_filter_to_input_annotation` / `normalize_input_value` are an intentional most-specific-to-least-specific dispatch ladder, not a near-copy (the two ladders serve opposite directions: annotation-build vs value-normalize). The static helper's "5 repeated literals" are all `LOOKUP_NAME_MAP` keys/values (`contains`, `istartswith`, `week_day`) and the family labels (`field_name`, `FilterSet`) — table content and self-naming, not extractable.

### Other positives

- **Branch-order correctness re-verified at runtime.** `convert_filter_to_input_annotation` places the `BaseCSVFilter` branch (line 367) ahead of the `(RangeFilter, _DjangoRangeFilter)` branch (line 379). Confirmed via `issubclass`: `django_filters.RangeFilter` is NOT a `BaseCSVFilter` subclass, while the auto-expanded `BaseInFilter` / `BaseRangeFilter` (from `Meta.fields` `in`/`range` lookups) ARE. So the CSV branch correctly catches only the list-shaped auto-expansions and the package's `{start, end}` `RangeFilter` primitive falls through to its own branch — the comment at lines 367-377 is accurate. The `DecimalField`/`FloatField`-before-`IntegerField` ordering in `_scalar_from_form_field` (lines 230-235) is likewise load-bearing and documented (both subclass `IntegerField` in `django.forms`).
- **Defensive entry guards single-sited.** `normalize_input_value` short-circuits UNSET/None via `is_inactive_value(..., unset_sentinel=UNSET)` (line 444) as the one place every future caller benefits from. `_encode_global_id_input` preserves the `relay.GlobalID` `type_name` by re-encoding to base64 wire form (lines 487-489) so `GlobalIDFilter.filter` can validate before decoding — the docstring documents the prior eager-decode bug this prevents.
- **`_model_field_for_filter` narrowed exception contract.** Catches only `FieldDoesNotExist` (lines 775-781), surfacing any other `_meta.get_field` failure loudly rather than degrading to `None` — the docstring records the prior broad-`except` that masked unrelated failures.
- **Cross-module wiring all live.** Every public symbol has confirmed first-party callers: `normalize_input_value` (`filters/sets.py:765,780`), `materialize_input_class` (`types/finalizer.py:1375,1385`), `clear_filter_input_namespace` (`registry.py:500` co-clear), `_build_input_fields`/`_build_logic_fields` (`filters/factories.py:36,112`), `_field_specs`/`_LOGIC_KEYS`/`LOOKUP_NAME_MAP` (`filters/sets.py:62`). `construct_search` has only a future-wiring reference (`filters/sets.py:362` comment) but is kept live by the `LOOKUP_PREFIXES` constant + direct tests, exactly as its docstring states (the `Meta.search_fields` card is deferred to `0.1.2`).
- **`clear_filter_input_namespace` non-destructive-delattr contract.** Materialized class objects are intentionally left parked in `__dict__` (the `materialize_input_class` next-finalize `setattr` overwrites in place) so a consumer-held `strawberry.lazy(...)` LazyType does not resolve to `AttributeError` — the docstring (lines 847-868) carries the load-bearing rationale.

### Summary

`filters/inputs.py` is a mature, heavily-delegated module: every case-conversion, scalar/enum derivation, owner-name resolution, and materialize/clear lifecycle bottoms out in a single-sited `utils/` or `types/converters` helper, and the public converter pair (`convert_filter_to_input_annotation` / `normalize_input_value`) is a clean most-specific-first dispatch ladder. The git diff is empty against both the per-cycle baseline (`286873d8`) and HEAD; the source's newer mtime is a content-identical touch (re-ran the static helper to refresh the stale overview). GLOSSARY shows no drift on any filter-input public-contract symbol (`FilterSet`, `filter_input_type`, `RelatedFilter`, `Meta.search_fields` "planned for 0.1.2", `Meta.filterset_class` all current vs impl). Zero High/Medium/Low findings; two DRY opportunities, both defer-with-trigger and both cross-family/cross-module (forwarded to the folder + project passes, not local defects). This is a genuine no-source-edit cycle (shape #5).

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass; 289 files left unchanged (only the standing COM812-vs-formatter advisory warning, pre-existing).
- `uv run ruff check --fix .` — pass; "All checks passed!", zero fixes applied.

### Notes for Worker 3
- Shape #5 no-source-edit cycle: git diff empty vs both cycle baseline `286873d8` and HEAD; source mtime newer than overview was a content-identical touch (verified by empty diff), so the static helper was re-run to refresh `docs/shadow/django_strawberry_framework__filters__inputs.overview.md`.
- Per-Low disposition: no Lows raised. Two DRY bullets, both defer-with-trigger, both cross-family/cross-module — forwarded to `docs/review/rev-filters.md` (folder) and `docs/review/rev-django_strawberry_framework.md` (project), NOT local findings.
- No GLOSSARY-only fix in scope: GLOSSARY filter-input symbols (`FilterSet`, `filter_input_type`, `RelatedFilter`, `Meta.search_fields`, `Meta.filterset_class`) all current vs impl; the unrelated 1-line `docs/GLOSSARY.md` working-tree edit does not touch any filter-input symbol and is presumptively concurrent maintainer/worker work (AGENTS.md rule 34).
- Load-bearing claims re-verified this cycle: (1) `convert_filter_to_input_annotation` branch order correct — `django_filters.RangeFilter` is NOT a `BaseCSVFilter` subclass, `BaseInFilter`/`BaseRangeFilter` ARE (confirmed via `issubclass`); (2) all public symbols have live first-party callers; (3) all delegation targets exist in `utils/strings`, `utils/inputs`, `utils/input_values`, `types/converters`, `sets_mixins`. Re-run the `issubclass` check and the caller greps each cycle — they are the silent-rot surface.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern.

No source edits, so no comment/docstring changes. The module's docstrings are accurate and load-bearing (notably the `_encode_global_id_input` prior-bug record, the `_pascal_case` caller-specific-guard rationale, the `clear_filter_input_namespace` non-destructive-delattr contract, and the `convert_filter_to_input_annotation` branch-order comment, all re-verified above). No stale TODO anchors (static helper: 0 TODO comments).

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

Not warranted. No source/test/doc edits in scope (AGENTS.md "Do not update CHANGELOG.md unless explicitly instructed"); the active plan `docs/review/review-0_0_11.md` is silent on any changelog entry for this item.

---

## Verification (Worker 3)

### Logic verification outcome
Zero-edit cycle confirmed two ways: `git diff 286873d8 -- django_strawberry_framework/filters/inputs.py` empty AND `git diff HEAD -- django_strawberry_framework/filters/inputs.py` empty (the source is byte-identical to baseline and HEAD; the content-identical touch Worker 1 noted left no diff). `git diff --stat 286873d8 -- django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md` is empty — no source/test dirt in any owned path. All High / Medium / Low are genuine `None.`:

- **Branch-order correctness (the load-bearing claim) re-verified at runtime.** `uv run python` `issubclass` checks confirm `django_filters.RangeFilter` is NOT a `BaseCSVFilter` subclass (False) while the auto-expanded `BaseInFilter` / `BaseRangeFilter` ARE (both True). So `convert_filter_to_input_annotation`'s `BaseCSVFilter` branch (line 367) ahead of the `(RangeFilter, _DjangoRangeFilter)` branch (line 379) is correct: the CSV branch catches only the list-shaped `in`/`range` auto-expansions; the package's `{start, end}` `RangeFilter` primitive falls through to its own branch. The `DecimalField`/`FloatField`-before-`IntegerField` ordering in `_scalar_from_form_field` (lines 230-235) is likewise confirmed — both subclass `forms.IntegerField` (True), so they must be matched first.
- **Lookup-name scaffolding spot-checked.** `LOOKUP_NAME_MAP` (lines 92-119) and `_LOGIC_KEYS` (line 131) are single sources of truth — `filters/sets.py:62` imports them by reference, builds the reverse map once at import (`sets.py:88`), and `sets.py:66,94,1084` consume `_LOGIC_KEYS`. Not duplicated literals.
- **`normalize_input_value` dispatch ladder** mirrors the annotation ladder in opposite direction with the `is_inactive_value(..., unset_sentinel=UNSET)` UNSET/None short-circuit (line 444) as the single defensive entry point. Confirmed `is_inactive_value` exists at `utils/input_values.py:74`.
- **All delegation targets exist:** `utils/strings.py::pascal_case` (line 55), `utils/inputs.py::materialize_generated_input_class` (103) / `clear_generated_input_namespace` (215), `utils/input_values.py::is_inactive_value` (74), `types/converters.py::scalar_for_field` (249) / `convert_choices_to_enum` (493), `types/definition.py::DjangoTypeDefinition.graphql_type_name` (199).
- **All public symbols have live first-party callers:** `normalize_input_value` (`filters/sets.py:765,780`), `materialize_input_class` (`types/finalizer.py:1375,1385`), `clear_filter_input_namespace` (`registry.py:500`), `_build_input_fields`/`_build_logic_fields` (`filters/factories.py:36,112`), `LOOKUP_NAME_MAP`/`_LOGIC_KEYS`/`_field_specs` (`filters/sets.py:62`).

Each Worker 2 section opens with `Filled by Worker 1 per no-source-edit cycle pattern.` (shape #5 gate met).

### DRY findings disposition
Two DRY items, both correctly **defer-with-trigger** and both cross-family/cross-module — forwarded to folder + project passes, NOT local fixes:
1. Cross-family `inputs.py` mirror (`filters/inputs.py` vs `orders/inputs.py`). Confirmed the mirror is real: `orders/inputs.py` carries the parallel `materialize_input_class` (323), `_field_specs` (115), `_build_input_fields` (195), and `normalize_input_value` (260) scaffold; the mechanics already bottom out single-sited in `utils/inputs.py`. Verbatim trigger: "a third generated-input family lands (e.g. the aggregates `AggregateSet` set)". Forwarded to `rev-filters.md` (folder) + `rev-django_strawberry_framework.md` (project) — both artifacts exist.
2. `_pascal_case` no-word-character guard vs `sets_mixins.py::ClassBasedTypeNameMixin.type_name_for`'s sibling guard. Verbatim trigger: "a third direct `pascal_case`-with-guard caller appears". The two messages are intentionally caller-specific (the `RangeFilter` consumer vs indirect class-naming callers) and the divergence is load-bearing for the error surface — not act-now.

### Temp test verification
- No temp tests created — zero-edit cycle, no new behavior to pin; the existing suite (`tests/filters/test_inputs.py`) already exercises the helpers.
- Disposition: n/a.

### GLOSSARY / sibling-attribution
Genuine #5 — no GLOSSARY drift on any filter-input symbol. GLOSSARY filter-input entries all current vs impl: `filter_input_type` shipped `0.0.8` (line 91), `Meta.filterset_class` shipped `0.0.8` (105), `Meta.search_fields` planned `0.1.2` (116), `RelatedFilter` shipped `0.0.8` (127), `FilterSet` shipped (511). The single GLOSSARY working-tree hunk is at line 305 (the `apps.py` three-patch-module / Trac #37064 entry) = concurrent sibling/maintainer work per AGENTS.md #33/#34, untouched. No `django_strawberry_framework/` or `tests/` source dirt at all; the rest of the working tree is per-cycle docs scratchpad. `git diff -- CHANGELOG.md` empty.

Changelog `Not warranted` cites BOTH AGENTS.md ("Do not update CHANGELOG.md unless explicitly instructed") AND the active plan's silence — internal-only framing matches the zero-edit scope.

Ruff: `ruff format --check` reports "1 file already formatted"; `ruff check` reports "All checks passed!" (only the standing COM812-vs-formatter advisory).

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the `filters/inputs.py` checklist box.
