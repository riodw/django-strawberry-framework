# Review: `django_strawberry_framework/filters/` (folder pass)

Status: verified

Folder-pass scope: cross-file concerns within `filters/` only — duplicated helpers, naming / error-handling drift, repeated ORM/queryset patterns, repeated string literals across siblings, one-way import direction, misplaced responsibilities, export issues in `__init__.py`, circular-import risk, comment consistency. All four in-scope files (`base.py`, `factories.py`, `inputs.py`, `sets.py`) are individually `verified` this cycle; `__init__.py` is covered here in the folder pass. `git diff 8bedf04f91d280b4241d35b662aa26b13d002d26 -- django_strawberry_framework/filters/` and `git diff HEAD -- django_strawberry_framework/filters/` are both empty (whole folder, including `__init__.py`).

## DRY analysis

- **Defer-with-trigger (forward to project pass) — cross-family `inputs.py` mirror (`filters/inputs.py` vs `orders/inputs.py`).** Forwarded up from `rev-filters__inputs.md`. The two families run parallel scaffolds (`materialize_input_class`, `clear_*_input_namespace`, `_build_input_fields`, `normalize_input_value`, `_field_specs` / `FieldSpec` ledger), but the mechanics are already single-sited in `utils/inputs.py` (0.0.9 DRY pass); each module's wrapper only pins family constants (`module_path`, `family_label="FilterSet"` vs `"OrderSet"`, ledger, factory/set class names). **This is a cross-family / cross-module concern (`filters/` paired with `orders/`), so it does not belong at the folder level — it is forwarded to `docs/review/rev-django_strawberry_framework.md` (project pass).** Verbatim trigger: "a third generated-input family lands (e.g. the aggregates `AggregateSet` set)" — then fold the three `materialize_*` / `clear_*` wrappers through a single `(module_path, family_label, ledger, factory_module, factory_class_name, collision_registry_attr, set_module, set_class_name)` family descriptor. Do not act now (the wrappers already bottom out in single-sited `utils` mechanics; only two families exist).

- **Defer-with-trigger (forward to project pass) — filter/order apply-pipeline scaffold (`filters/sets.py` vs `orders/sets.py`).** Forwarded up from `rev-filters__sets.md`. The `apply_sync` / `apply_async` / `apply` + `_apply_common_prelude` / `_apply_common_finalize` dispatch scaffold is shared structurally with `orders/sets.py::OrderSet`; the shared steps (permission core, request resolution, input traversal, sync-misuse routing) already route through single-sited `utils/permissions.py` / `utils/input_values.py` / `utils/querysets.py` cores, leaving only the prelude/finalize/dispatch shell. `docs/GLOSSARY.md:971` pins the filter/order apply-pair parity as intentional sibling design. **Cross-family / cross-module (`filters/` paired with `orders/`) — forwarded to `docs/review/rev-django_strawberry_framework.md` (project pass), not a folder-level finding.** Verbatim trigger: "a third `*Set.apply_*` family (e.g. `AggregateSet`) landing — then fold the prelude/finalize/dispatch scaffold through a shared mixin." Do not act now.

- **Defer-with-trigger (folder-internal candidate, no twin yet) — Layer-6 dynamic-cache hashing primitives.** Forwarded up from `rev-filters__factories.md`. `filters/factories.py::_make_hashable` and the `(model, fields_key, extra)` key body of `::_make_cache_key` are the only concrete implementation of the model-keyed cache shape; `orders/factories.py:85-103` reserves `_dynamic_orderset_cache` / `get_orderset_class` as a TODO-anchored deferred non-goal with no implementation, so no twin exists. **Carried to the project-pass level because the eventual consolidation site (`utils/inputs.py::make_set_meta_cache_key`) and the twin both live outside `filters/` — forwarded to `docs/review/rev-django_strawberry_framework.md`.** Verbatim trigger: "when a card revives the orders Layer-6 surface (i.e. `orders/factories.py` gains a real `get_orderset_class` + `_dynamic_orderset_cache` implementation)". A single concrete site is not duplication; do not act now.

The two file-local `base.py` and `inputs.py` candidates (the `method` setter + `*FilterMethod` subclass pair; the `_pascal_case` no-word-character guard pair) are NOT re-promoted here — both are correctly defer-with-trigger inside their own files (`rev-filters__base.md`, `rev-filters__inputs.md`) with single-file or `sets_mixins`-paired scope; neither crosses two `filters/` siblings, so they stay at the file level rather than the folder level.

## High:

None.

## Medium:

None.

## Low:

None.

## What looks solid

### DRY recap

- **Existing patterns reused (cross-file, single direction).** The folder is a clean layered stack with every shared mechanic single-sited in `utils/` or `sets_mixins`, never re-implemented per sibling: the generated-input BFS algorithm lives once in `utils/inputs.py::GeneratedInputArgumentsFactory` and `factories.py::FilterArgumentsFactory` supplies only family hooks; case-conversion / scalar / enum / owner-name resolution in `inputs.py` all delegate to `utils/strings.pascal_case`, `types/converters`, `types/definition.DjangoTypeDefinition`; the materialize/clear lifecycle bottoms out in `utils/inputs.py::materialize_generated_input_class` / `clear_generated_input_namespace`; the apply-pipeline permission/traversal/sync-misuse cores in `sets.py` route through `utils/permissions.py`, `utils/input_values.py`, `utils/querysets.py`; `RelatedFilter` owner-bind / lazy-target machinery delegates to `sets_mixins.RelatedSetTargetMixin`. The `LOOKUP_NAME_MAP` / `_LOGIC_KEYS` tables are declared once in `inputs.py` and consumed by reference from `sets.py:62` (reverse map built once at import) — single source of truth, not a duplicated literal.
- **New helpers considered.** Three cross-file consolidation candidates evaluated; all three are cross-family / cross-module (pairing `filters/` with `orders/` or with `utils/`) rather than `filters/`-internal, so all three forward to the project pass with verbatim triggers (above). No folder-local helper is warranted — there is no helper duplicated between two `filters/` siblings that a folder-scoped extraction would resolve.
- **Duplication risk in the current folder.** The one cross-sibling repeated literal is `FilterSet` (appears in `inputs.py` and `sets.py` per the static helper) — self-naming of the family base class, not extractable. `field_name` (`inputs.py`) and `related_filters` (`sets.py` x6) are distinct attribute references, not a shared literal across siblings. `base.py` reports zero repeated literals; `factories.py`'s `2x filterset` is a within-file hook-noun pair (`_rename_noun` / `_related_target_attr`), not cross-file. No folder-level literal table needs hoisting.

### Other positives

- **Import direction is strictly one-way and acyclic.** Runtime intra-folder edges: `base.py` is a leaf (no `.`-relative siblings imported); `inputs.py` imports `.base` at module top and `.sets` only under `TYPE_CHECKING` (`inputs.py:64-65`) plus one in-function `from .base import RelatedFilter` (`inputs.py:630`); `sets.py` imports `.base` + `.inputs` at module top; `factories.py` imports `.inputs` + `.sets`; `__init__.py` imports `.base` + `.inputs` + `.sets`. The apparent `inputs.py <-> sets.py` pair is not a runtime cycle — `inputs.py`'s `.sets` reference is type-checking-only. The static helper's "local" tag does not distinguish deferred from module-top imports; verified directly in source that no runtime cycle exists.
- **`__init__.py` exports are consistent and complete.** `__all__` (16 names) is alphabetically ordered and every entry resolves to a re-exported symbol from `.base` / `.sets` or the locally-defined `filter_input_type`; the module's `_helper_referenced_filtersets` ledger is the Decision-11 orphan-check set cleared by `registry.clear()` via a cycle-safe local import and read by the finalizer phase 2.5 subpass 4. The `Filter` re-export is documented as a deliberate plain re-export of `django_filters.Filter` (not a subclass) surfaced under the package namespace. `filter_input_type` delegates its body to the shared `utils/inputs.py::build_lazy_input_annotation` (the 0.0.9 DRY pass shared with `orders/__init__.py::order_input_type`), so the consumer-helper logic is single-sited across families.
- **Error-handling discipline is uniform across the folder.** Every sibling raises the package's typed `ConfigurationError` on real misuse (`factories.py` missing `model`; `inputs.py::_pascal_case` no-word-character guard; `sets.py` mixed-model `RelatedFilter`, unsupported own-PK GlobalID lookup, depth cap) and narrows broad `except` to the specific Django exception (`inputs.py::_model_field_for_filter` catches only `FieldDoesNotExist`). GlobalID validation in `base.py` is consistently defense-in-depth (returns `None` / falls back, never raises) with `decode` owning the uniform-error contract. No naming or error-handling drift between siblings.
- **Comment / docstring consistency.** Spec/decision anchors are cited uniformly (spec-027 layers, Decision-9 named caches, Decision-11 consumer helper, the 0.0.9 DRY pass); the lone TODO (`sets.py:361`, `Meta.search_fields` planned `0.1.2`) is live and matches `GLOSSARY.md:898-902`. No stale or restating comments surfaced across the folder.

### Summary

The `filters/` folder is a mature, cleanly-layered subsystem: `base.py` (primitives + `RelatedFilter`) -> `inputs.py` (converters/materialize, type-checking-only back-edge to `sets`) -> `sets.py` (`FilterSet` + metaclass + apply pipeline) -> `factories.py` (BFS input factory + deferred Layer-6 cache), re-exported through a consistent `__init__.py`. The whole-folder diff is empty against both the per-cycle baseline (`8bedf04f`) and HEAD; every sibling is individually `verified`. Import direction is strictly one-way and acyclic (the only `inputs <-> sets` back-edge is `TYPE_CHECKING`-only), exports are complete and ordered, error handling and comment conventions are uniform, and there is no folder-level helper duplication — every shared mechanic already bottoms out single-sited in `utils/` or `sets_mixins`. The three forwarded DRY candidates are all cross-family / cross-module (pairing `filters/` with `orders/` or `utils/`), so they are carried onward to the project pass `rev-django_strawberry_framework.md` rather than held at the folder level. No High/Medium/Low findings. Genuine no-source-edit folder pass (shape #5).

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass; `289 files left unchanged` (standing COM812-vs-formatter advisory only).
- `uv run ruff check --fix .` — pass; `All checks passed!`.

### Notes for Worker 3
- Folder pass over `django_strawberry_framework/filters/`. `git diff 8bedf04f91d280b4241d35b662aa26b13d002d26 -- django_strawberry_framework/filters/` and `git diff HEAD -- django_strawberry_framework/filters/` are both empty (whole folder, including `__init__.py`); zero edits to any tracked file.
- All four siblings (`base.py`, `factories.py`, `inputs.py`, `sets.py`) are individually `Status: verified`; their per-file artifacts are the inputs to this pass.
- All five shadow overviews exist under `docs/shadow/` (including `__init__.py`); the helper ran on every `.py` in the folder. No re-run needed.
- No High; no Medium; no Low. Three DRY bullets, all defer-with-trigger and all cross-family / cross-module — forwarded to `docs/review/rev-django_strawberry_framework.md` (project pass), NOT held as folder-level findings: (1) cross-family `inputs.py` mirror; (2) filter/order apply-pipeline scaffold; (3) Layer-6 dynamic-cache hashing primitives. The two file-local `base.py` / `inputs.py` defer-with-trigger candidates are not re-promoted (single-file or `sets_mixins`-paired scope).
- No GLOSSARY-only fix in scope: every `filters/` public symbol's GLOSSARY prose was confirmed accurate in the per-file passes this cycle (`FilterSet`, `RelatedFilter`, `Meta.filterset_class`, `Meta.search_fields` planned-0.1.2, `filter_input_type`, `SyncMisuseError` rewrap). No folder-pass GLOSSARY drift.
- Import-direction confirmed acyclic at runtime: `inputs.py`'s `.sets` reference is `TYPE_CHECKING`-only (`inputs.py:64-65`); the `.base` import in `inputs.py:630` is in-function deferred. The static helper's "local" tag conflates deferred with module-top imports — verified in source, no runtime cycle.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern.

No source edits, so no comment/docstring changes. Folder-level comment/docstring consistency is sound: spec/decision anchors (spec-027 layers, Decision-9/11, the 0.0.9 DRY pass) are cited uniformly across siblings; the single live TODO (`sets.py:361`, `Meta.search_fields` planned `0.1.2`) matches `GLOSSARY.md:898-902`; the `__init__.py` `Filter` plain-re-export note is accurate. Nothing to change.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

Not warranted — no source, test, GLOSSARY, or other tracked-file edits this cycle (AGENTS.md: "Do not update CHANGELOG.md unless explicitly instructed"; the active plan `docs/review/review-0_0_11.md` is silent on any changelog entry for this folder pass).

---

## Verification (Worker 3)

### Logic verification outcome
No source edits this cycle (shape #5 folder pass). All High / Medium / Low are genuine `None.` — verified independently, not accepted on the artifact's word:

- **No missed cross-sibling helper duplication.** Every shared `filters/` mechanic already bottoms out single-sited outside the folder: `utils/inputs.py::materialize_generated_input_class` (@103), `::clear_generated_input_namespace` (@215), `::GeneratedInputArgumentsFactory` (@277), `::build_lazy_input_annotation` (@142); `sets_mixins.RelatedSetTargetMixin` / `LazyRelatedClassMixin`. `factories.py` supplies only family hooks to the BFS factory. No helper is duplicated between two `filters/` siblings, so no folder-scoped extraction is warranted.
- **Import direction is one-way / acyclic — verified in source.** `base.py` is a leaf (no `.`-relative sibling imports; only `..sets_mixins`, `..types.*`). `inputs.py` imports `.base` at module top (line 45); its `.sets` reference is inside `if TYPE_CHECKING:` (line 63, `from .sets import FilterSet` @65) and its `.base` reference at line 630 is in-function deferred. `sets.py` imports `.base` + `.inputs` at module top (lines 61-62). `factories.py` imports `.inputs` + `.sets` (lines 36-37). Runtime edges: `base ← inputs ← sets ← factories`; the only `inputs → sets` edge is TYPE_CHECKING-only, so no runtime cycle. The artifact cites `inputs.py:64-65`; live guard is at 63 / `FilterSet` at 65 — a one-line cosmetic drift in a per-cycle scratchpad artifact (AGENTS.md #27), content verified by the quoted substring under the `TYPE_CHECKING` guard.
- **`__init__.py` exports complete and ordered.** `__all__` (16 names, lines 86-103) is alphabetically ordered; every entry resolves to a re-export from `.base` / `.sets` or the locally-defined `filter_input_type`, whose body delegates to `utils/inputs.py::build_lazy_input_annotation` (single-sited consumer helper). The `Filter` plain-re-export note (`Filter is django_filters.Filter`, not a subclass) is accurate.

### DRY findings disposition
Three forwarded defer-with-trigger items — all confirmed genuinely cross-module (consolidation site and/or twin live outside `filters/`), so all correctly routed to the project pass `docs/review/rev-django_strawberry_framework.md` rather than fixable at folder level now:

1. **Cross-family `inputs.py` mirror** (`filters/inputs.py` vs `orders/inputs.py`) — twin lives in `orders/`; shared mechanics already single-sited in `utils/inputs.py` (confirmed above). Trigger: third generated-input family (`AggregateSet`). Forwarded.
2. **Apply-pipeline scaffold** (`filters/sets.py` vs `orders/sets.py`) — twin `orders/sets.py::apply_sync` (@525) / `apply_async` (@566) confirmed present. Cross-module. Trigger: third `*Set.apply_*` family. Forwarded.
3. **Layer-6 cache primitives** (`filters/factories.py::_make_hashable` / `_make_cache_key` key-body) — `orders/factories.py` reserves `_dynamic_orderset_cache` / `get_orderset_class` as a TODO-anchored standing non-goal with NO implementation (lines 18-19, 85-91). No twin exists → a single concrete site is not duplication. Eventual consolidation site (`utils/inputs.py`) and twin both live outside `filters/`. Trigger: orders Layer-6 surface gains a real implementation. Forwarded.

The two file-local `base.py` (`*FilterMethod` setter+subclass) and `inputs.py` (`_pascal_case` no-word-character guard) candidates are correctly NOT re-promoted — neither crosses two `filters/` siblings; they stay at the file level per `rev-filters__base.md` / `rev-filters__inputs.md`.

### Temp test verification
- No temp tests needed — no-source-edit cycle; verification was source-read + grep of import edges and DRY twins.
- Disposition: none.

### Verification outcome
- `cycle accepted; verified` — sets top-level `Status: verified` AND marks the filters folder-pass checklist box.

Zero-edit proof (two ways): `git diff 8bedf04f91d280b4241d35b662aa26b13d002d26 -- django_strawberry_framework/filters/` empty AND `git diff HEAD -- django_strawberry_framework/filters/` empty; `git diff --stat 8bedf04f -- django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md` fully empty this run (no #33 concurrent-maintainer dirt). `git diff -- CHANGELOG.md` empty (consistent with "Not warranted", both citations present). All three Worker 2 sections open with "Filled by Worker 1 per no-source-edit cycle pattern." (lines 52, 76, 84). Ruff format-check (5 files already formatted) + check (all passed) clean — standing COM812-vs-formatter advisory only.
