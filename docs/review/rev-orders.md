# Review: `django_strawberry_framework/orders/` (folder pass)

Status: verified

## DRY analysis

- **Cross-folder filters↔orders family-wrapper set — forward to the project pass (`docs/review/rev-django_strawberry_framework.md`); do NOT merge at folder level.** Four order-side surfaces are byte-symmetric twins of their `filters/` counterparts, each already a thin parameterization over a single-sited shared primitive, so the only residue is per-family config tokens:
  - **`inputs.py` materialize/clear/build family mirror.** `orders/inputs.py::materialize_input_class` / `clear_order_input_namespace` / `_build_input_fields` mirror `filters/inputs.py`'s same-named surface; both delegate to `utils/inputs.py` + `utils/input_values.py`. Order side deliberately omits the operator bag / `_build_logic_fields` / `HIDE_FLAT_FILTERS` skip.
  - **Apply-pipeline scaffold (`sets.py`).** `orders/sets.py::OrderSet.apply_sync` / `apply_async` mirror `FilterSet`'s sync/async-split tail (normalize → early-return → flatten → resolve → conditional `annotate` → terminal call), diverging only in the permission-check `sync_to_async` wrap.
  - **Permission-wrapper layer (`sets.py`).** The six `OrderSet` permission delegates (`_request_from_info`, `_extract_branch_value`, `_active_permission_field_paths`, `_active_permission_targets`, `_invoke_permission_method`, `_run_permission_checks`) are one-line delegates into `utils/permissions.py`, byte-symmetric with `FilterSet`'s same-named methods; only the family-label / `related_attr`+`target_attr` tokens / `logic_keys` differ.
  - **Layer-6 cache primitives (`factories.py`).** The dynamic-cache machinery (`_make_hashable` / `_make_cache_key` / `_create_dynamic_*_class` / `get_*set_class`) ships only on the filter side (`filters/factories.py`); the order side is the TODO-anchored deferred non-goal (`orders/factories.py` `#"TODO(spec-028-orders-0_0_8 Decision 12"`).

  All four span two Layer-3 sibling folders (`filters/` ↔ `orders/`) and must preserve each family's documented public method/class names (`bind_orderset`/`.orderset`/`OrderSet` vs `bind_filterset`/`.filterset`/`FilterSet`). A shared mixin/config-object hoist is a project-wide triage, not a per-folder fold. The per-file artifacts correctly left all four cross-folder; the project pass triages the whole filter+order+utils family-wrapper set together. **Confirmed forwarded; nothing folder-level here.**

- **No folder-internal (orders-only) DRY candidate remains.** Within `orders/` every shared mechanic is already single-sited (in `sets_mixins`, `utils/inputs`, `utils/input_values`, `utils/permissions`, `utils/relations`) and imported/re-aliased, not re-spelled. The two prior-cycle act-now twins are resolved in HEAD (see `### DRY recap`). No new folder-level consolidation shape exists.

## High:

None.

## Medium:

None.

## Low:

None.

## What looks solid

### DRY recap

- **Existing patterns reused.** Every order file is a thin parameterization of a package-level shared primitive — no machinery is re-implemented inside `orders/`:
  - `base.py::RelatedOrder` → `sets_mixins.py::RelatedSetTargetMixin` (`_target_attr`/`_owner_attr` + three family-named wrappers).
  - `factories.py::OrderArgumentsFactory` → `utils/inputs.py::GeneratedInputArgumentsFactory` (6 hook attrs + 2 ClassVar caches + one `_build_input_triples` override).
  - `inputs.py` → `utils/inputs.py` + `utils/input_values.py` (six imports re-aliased: `FieldSpec`/`build_input_class`/`_camel_case`/`_iter_orderset_subclasses`; `materialize_input_class` / `clear_order_input_namespace` / `normalize_input_value` are thin family wrappers).
  - `sets.py::OrderSet` → `sets_mixins.py` (`collect_related_declarations`, `expanded_once`, `SetLifecycleAttrs`, `ClassBasedTypeNameMixin`), `utils/permissions.py` (six-primitive core incl. the now-public `verbatim_path`), `utils/relations.py` (`relation_kind`/`is_many_side_relation_kind`), `.inputs.normalize_input_value`, `Ordering.resolve`.
  - `__init__.py::order_input_type` → `utils/inputs.py::build_lazy_input_annotation` (the Decision-11 consumer-helper body shared with `filters/__init__.py::filter_input_type`).
- **New helpers considered.** No folder-internal helper warranted: there is no orders-only duplicated logic to factor — every method body is already one delegating call. The only cross-folder candidates (the four family-wrapper twins above) are forwarded to the project pass, not foldable at folder scope.
- **Duplication risk in the current file.** The cross-sibling repeated-literal sweep (five shadow overviews incl. `__init__.py`) found only family attribute-name tokens appearing in 2+ files, all intentional sibling design: `"OrderSet"` (`inputs.py` 2x as distinct `family_label=`/`set_class_name=` substrate kwargs; `__init__.py` as the `expected_base`/brand name), `"related_orders"` (`sets.py` 4x: metaclass `collection_attr`, `_active_permission_targets` `related_attr`, two `get_fields` `__dict__`/`getattr` reads), `"orderset"` (`factories.py` 2x: `_rename_noun` error-wording vs `_related_target_attr` attr resolution), `"order_input_type"` (`__init__.py` 2x: the def name + the `family_name=` kwarg). Each is read/passed against distinct objects or carries a distinct role; hoisting would couple semantically-separate slots and cannot reduce drift because the two families differ here by design (the `filters/` twins carry `"FilterSet"`/`"related_filters"`/`"filterset"`/`"filter_input_type"`). Not duplication.
- **Two prior-cycle act-now twins resolved in HEAD.** (a) `sets.py`'s `_verbatim_attr` (byte-identical to `utils/permissions.py::verbatim_path`) was eliminated by promoting `verbatim_path` into `utils/permissions.__all__` (imported at `orders/sets.py` line 47, used as `fallback_path` at line 362; `grep -rn "_verbatim_attr"` → zero). (b) The `_can_elide_fk_id`-class predicate twins are an optimizer concern, out of folder. These are part of why this cycle's `git diff` is empty; recap only, not candidates.

### Other positives

- **Import DAG one-way acyclic (re-confirmed at source, incl. `__init__.py`).** Runtime sibling edges: `base.py` is a leaf (sibling imports: none; only `..sets_mixins`); `inputs.py` is a runtime leaf (its `.sets` import is `TYPE_CHECKING`-only, `orders/inputs.py` `#"if TYPE_CHECKING:"` line 40); `sets.py → .base, .inputs` (module-top) plus a **function-local** `.inputs._get_concrete_field_names_for_order` (`orders/sets.py` line 255, comment `#"Local import dodges any circular-import risk"`); `factories.py → .inputs`; `__init__.py → .base, .inputs, .sets`. The single potential cycle (`sets`↔`inputs`) is deliberately broken on both arcs — `inputs→sets` deferred to `TYPE_CHECKING`, the one runtime `sets→inputs` arc made function-local. Apex modules are `sets` and `factories`; no back-edge, no cycle.
- **`__init__.py` export surface correct.** `__all__` matches the documented spec-028 surface: `("OrderSet", "OrderSetMetaclass", "Ordering", "RelatedOrder", "order_input_type")`. Private `INPUTS_MODULE_PATH` / `_input_type_name_for` are re-exported at module scope for Slice 2/3 consumers but deliberately kept OUT of `__all__` (leading `_` flags them private), mirroring `filters/__init__.py`. `OrderArgumentsFactory` is intentionally NOT re-exported (advanced consumers import from `orders.factories` directly, one-for-one with `filters/__init__.py` keeping `FilterArgumentsFactory` out — spec-028 Decision 2). The `_helper_referenced_ordersets` ledger lives in `__init__.py` (line 40) co-located with its sole writer `order_input_type`; `registry.clear()` clears it in a SEPARATE block from `clear_order_input_namespace()` (the two-block layout matching the filter side — `registry.py:509-516`, grep-verified by the per-file artifacts). No private symbol leaks into the public surface.
- **No circular-import / import-time side effects across the folder.** `base.py` / `factories.py` / `inputs.py` carry zero module-level executable code beyond declarations + the `_helper_referenced_ordersets = set()` / provenance-table / ledger initializers; `__init__.py`'s only call-of-interest is `set()` at import. All `DjangoTypeDefinition` imports are `TYPE_CHECKING`-gated (`pragma: no cover`). No ORM access fires at import.
- **Naming / error-handling consistency across the folder.** Family tokens are consistent (`OrderSet`/`related_orders`/`orderset`/`Ordering`) and each is the documented sibling-twin of the filter token. Error handling is uniform and fail-loud where it must be: `ConfigurationError` naming the class for `Meta.fields="__all__"` without `Meta.model` (`sets.py`); raw `ImportError` propagation at the `RelatedOrder` lazy-resolution layer (rewrap deferred to `finalize_django_types()` a layer up); `TypeError` for non-`OrderSet` args to `order_input_type`. The to-many ordering guard (`sets.py::_resolve_order_expressions` → `Min`/`Max` annotate) and the fail-closed pre-mutation permission gate (both `apply_sync`/`apply_async`, sync/async parity) are the only genuinely order-local logic, both correct.
- **Comment / docstring consistency.** Every cross-reference to the filter twin, the governing spec-028 decision, the 0.0.9 DRY pass (`docs/feedback.md` Major 3, present on disk), and the Layer-6 deferral is accurate and AGENTS.md #26-compliant (the lone TODO anchor in `factories.py` names the active design doc + decision + forward-reserved symbols, no `NotImplementedError` needed since the default path is complete). Zero TODOs in the other four files; no stale spec references.
- **GLOSSARY contract accurate across the folder.** All five order-family public-contract entries verified accurate against live source by the per-file artifacts and re-confirmed present: `## Meta.orderset_class` (GLOSSARY.md:849), `## Ordering` (:957), `## OrderSet` (:965), `## order_input_type` (:975), `## RelatedOrder` (:1053). Private `_`-prefixed helpers (`OrderArgumentsFactory`, `_input_type_name_for`, `_helper_referenced_ordersets`, `_field_specs`, etc.) correctly carry no entry — absence is correct, not drift.

### Summary

`orders/` is a clean, maximally-DRY Layer-3 subsystem and a faithful symmetric twin of `filters/`. All four in-scope files (`base.py`, `factories.py`, `inputs.py`, `sets.py`) plus `__init__.py` are unchanged this cycle — `git diff 6ef39886 -- django_strawberry_framework/orders/` and `git diff HEAD -- django_strawberry_framework/orders/` are both empty (last touching commit `8d6ca99b`, cumulative-in-HEAD), and all four per-file artifacts are `verified` and were themselves shape-#5 no-source-edit cycles. The folder-pass cross-file checks all pass: the sibling import DAG is one-way acyclic with the lone `sets`↔`inputs` cycle deliberately broken on both arcs (TYPE_CHECKING + function-local); the `__init__.py` export surface is the documented spec-028 five-symbol set with private helpers correctly excluded; naming, error-handling, and comment cross-references are uniform and accurate; and the cross-sibling repeated-literal sweep surfaced only intentional family-token sibling design. Every shared mechanic is already single-sited in package-level helpers and imported, not re-spelled — the two prior-cycle act-now twins (`_verbatim_attr` and the FK-id predicate) are resolved in HEAD. No folder-internal DRY candidate remains; the four cross-folder filters↔orders twins (`inputs.py` family mirror, apply-pipeline scaffold, permission-wrapper layer, Layer-6 cache primitives) are all confirmed CROSS-FOLDER and forwarded to the project pass (`rev-django_strawberry_framework.md`), correctly kept None at folder level. No High / Medium / Low findings. Genuine no-source-edit cycle (shape #5).

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass; "289 files left unchanged" (only the pre-existing COM812-vs-formatter config warning).
- `uv run ruff check --fix .` — pass; "All checks passed!".

### Notes for Worker 3
- Shape #5 (no-source-edit folder pass): `git diff 6ef39886acbdd49ad03931d6ca88179a12fbd825 -- django_strawberry_framework/orders/` AND `git diff HEAD -- django_strawberry_framework/orders/` BOTH empty; last touching commit `8d6ca99b`, cumulative-in-HEAD. All four per-file artifacts (`rev-orders__base.md`, `rev-orders__factories.md`, `rev-orders__inputs.md`, `rev-orders__sets.md`) are `verified`.
- No High / no Medium / no Low findings — nothing to disposition per-severity.
- No GLOSSARY-only fix in scope. All five order-family public-contract entries (`## Meta.orderset_class`:849, `## Ordering`:957, `## OrderSet`:965, `## order_input_type`:975, `## RelatedOrder`:1053) verified accurate against source by the per-file artifacts; private `_`-helpers correctly carry no entry. No drift, no edit warranted.
- All DRY items at folder level are cross-folder (filters↔orders) and FORWARDED to the project pass (`rev-django_strawberry_framework.md`): `inputs.py` materialize/clear/build family mirror, apply-pipeline scaffold, permission-wrapper layer, Layer-6 cache primitives. The two prior-cycle act-now twins (`_verbatim_attr`, FK-id predicate) are resolved in HEAD — recap only.
- Import DAG one-way acyclic confirmed at source (not just shadow tags): `inputs→sets` is `TYPE_CHECKING`-only; the one runtime `sets→inputs._get_concrete_field_names_for_order` is function-local (`orders/sets.py` line 255). No cycle.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern.

No comment or docstring edits warranted. All module/class/method docstrings, the family-wrapper parameterization comment blocks, the spec-028 decision cross-references, the 0.0.9-DRY-pass / `docs/feedback.md` Major 3 citations, and the single Layer-6 TODO anchor (AGENTS.md #26-compliant) are accurate across all five files. No TODO straggler (one intentional, anchored), no stale spec references. `docs/feedback.md` referenced in `base.py` / `sets.py` / `inputs.py` exists on disk.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

Not warranted. No source/test/doc edits in this cycle (no-source-edit folder pass); AGENTS.md #21 ("Do not update CHANGELOG.md unless explicitly instructed") and the active plan (`docs/review/review-0_0_11.md`) is silent on changelog edits for review cycles. Nothing to record.

---

## Verification (Worker 3)

Shape #5 no-source-edit folder pass — terminal verify.

### Zero-edit proof
- `git diff 6ef39886acbdd49ad03931d6ca88179a12fbd825 -- django_strawberry_framework/orders/` — empty.
- `git diff HEAD -- django_strawberry_framework/orders/` — empty.
- `git diff --stat 6ef39886 -- django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md` — empty (no sibling-cycle attribution needed; owned-paths stat clean).
- Last commit touching `orders/`: `8d6ca99b` ("Finish REVIEW"), cumulative-in-HEAD. No this-cycle edit to any tracked file.
- Each Worker 2 section opens "Filled by Worker 1 per no-source-edit cycle pattern." — gate satisfied.

### Logic verification outcome
No High / Medium / Low findings to disposition. Folder reasoning confirmed sound at source:
- **Import DAG one-way acyclic.** `base.py` leaf (`..sets_mixins` only); `inputs.py` runtime leaf (its `.sets` import is `TYPE_CHECKING`-gated, `inputs.py:41-43`); `factories.py → .inputs`; `sets.py → .base, .inputs` (module-top, `sets.py:50-51`) plus the one runtime `sets→inputs._get_concrete_field_names_for_order` made **function-local** (`sets.py:255`, inside the `"__all__"` branch). `__init__.py → .base, .inputs, .sets` (grep-confirmed lines 27-30). The lone `sets`↔`inputs` apparent cycle is broken on BOTH arcs (TYPE_CHECKING + function-local). No back-edge.
- **`__init__.py` export surface correct.** `__all__ = ("OrderSet", "OrderSetMetaclass", "Ordering", "RelatedOrder", "order_input_type")` read verbatim at `__init__.py:87-93`. Private `INPUTS_MODULE_PATH` / `_input_type_name_for` re-exported at module scope but excluded from `__all__` (leading `_` / non-public); `OrderArgumentsFactory` intentionally not re-exported — one-for-one with the filter side, which keeps `FilterArgumentsFactory` out and `FilterSetMetaclass` in `__all__` (`filters/__init__.py:36,91`, grep-confirmed). No private symbol leaks.
- **No folder-internal duplicated helper missed.** Every order method body is a single delegating call into a package-level primitive (`sets_mixins`, `utils/inputs`, `utils/input_values`, `utils/permissions`, `utils/relations`). The two prior-cycle act-now twins are resolved in HEAD: `grep -rn "_verbatim_attr" django_strawberry_framework/` → NONE; `verbatim_path` is in `utils/permissions.__all__` (line 70), defined at :152, and consumed as `fallback_path` (`sets.py:362`). The FK-id predicate twin is an optimizer concern, out of folder.
- **Filter twins present (cross-folder symmetry, not drift).** All six `OrderSet` permission delegates have same-named `FilterSet` twins (`filters/sets.py:871,914,1145,1262,1280,1299`); `materialize_input_class` / `_build_input_fields` and the family clear (`clear_filter_input_namespace` ↔ `clear_order_input_namespace`) twins present (`filters/inputs.py:617,811,830`). Sibling design preserved on both sides.
- **Layer-6 deferral genuine.** `grep -rn "get_orderset_class\|_dynamic_orderset_cache" orders/` → only the docstring + TODO anchor in `factories.py` (lines 18, 90-91); zero shipped defs. AGENTS.md #26-compliant (names spec-028 Decision 12 + reason; default path complete, no NotImplementedError needed).

### DRY findings disposition
All four folder-level DRY items are cross-folder (filters↔orders) and correctly FORWARDED to the project pass (`rev-django_strawberry_framework.md`): (1) `inputs.py` materialize/clear/build family mirror, (2) apply-pipeline scaffold (`sets.py` `apply_sync`/`apply_async`), (3) permission-wrapper layer (six delegates), (4) Layer-6 cache primitives. Each must preserve its family's documented public method/class names (`bind_orderset`/`.orderset`/`OrderSet`) so a shared-mixin hoist is project-wide triage, not foldable folder-level. No folder-internal DRY candidate remains. Disposition correct — nothing folder-level.

### Temp test verification
None — no-source-edit cycle, no temp tests required.

### GLOSSARY accuracy
Five order-family entries present at cited lines (headings backtick-wrapped: `## \`Meta.orderset_class\`` :849, `## \`Ordering\`` :957, `## \`OrderSet\`` :965, `## \`order_input_type\`` :975, `## \`RelatedOrder\`` :1053). Prose spot-checked against live source: `Ordering`'s six members + `resolve()` True-or-None NULLS mapping match `inputs.py:85-107`; `OrderSet`'s `apply_sync`/`apply_async(input_value, queryset, info)` pair, active-input-only + double-dispatch per-class dedup, and Layer-6 deferral match `sets.py`; `order_input_type`'s element-type `Annotated[...]` + eager validation + `_helper_referenced_ordersets` ledger match `__init__.py:43-84`. Accurate, not merely untouched. Private `_`-prefixed helpers correctly carry no entry. No GLOSSARY-only fix in scope (not disqualifying).

### Changelog disposition
`git diff -- CHANGELOG.md` empty. "Not warranted" with BOTH citations (AGENTS.md #21 + active-plan silence). Internal-only framing matches the empty diff scope. Accepted.

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the orders/ folder-pass checklist box.

---

## Iteration log

(none)
