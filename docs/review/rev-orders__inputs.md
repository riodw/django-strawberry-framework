# Review: `django_strawberry_framework/orders/inputs.py`

Status: verified

## DRY analysis

- **Filter/order `normalize_input_value` pair — NOT a shared traversal; do not merge.** `orders/inputs.py::normalize_input_value` (orders/inputs.py:260-320) and `filters/inputs.py::normalize_input_value` (filters/inputs.py:412-460) share a name and a high-level role but operate at different abstraction levels: the order side is a **whole-input walker** that delegates its dataclass/list/`None`-skip/leaf-vs-related traversal to the shared `utils/input_values.py::iter_active_fields` substrate (orders/inputs.py:304) and emits `(field_path, Ordering | None)` tuples; the filter side is a **per-leaf value coercion** (`isinstance`-dispatch into scalar/list/dict form-data shapes, filters/inputs.py:446-460) that does no traversal at all and is itself CALLED from inside the filter walker. Confirmed from the order side per the project-pass forward: the only common mechanics are already single-sited in `iter_active_fields`, and the order side already consumes them. No further consolidation; this is a documented intentional sibling-naming, not duplication. Forwarded as a recorded-not-acted note to the project pass (cross-folder), do not force-merge.

- **Family-wrapper consolidation (`materialize_input_class` / `clear_order_input_namespace` / domain-local aliases) is cross-folder — defer to project pass.** These are thin order-side wrappers pinning the module path / family label / ledger over `utils/inputs.py` (orders/inputs.py:323-339, 342-391, 49-52). Their exact filter twins live in `filters/inputs.py`. The wrappers ARE the spec-028 Decision 9 public surface (named symbols tests + `factories.py` import from this module), and the mechanics are already single-sited in `utils/inputs.py` per the 0.0.9 DRY pass. Defer until a project-pass cross-folder family-wrapper survey runs (`rev-django_strawberry_framework.md`); a same-folder hoist would re-add an import edge for no gain. Forwarded to the project pass — consolidation, if any, spans `filters/` + `orders/` + `utils/`.

## High:

None.

## Medium:

None.

## Low:

### Reserved `model_field` / `owner_definition` parameters carry forward-extension affordances that ship nothing today

`convert_order_field_to_input_annotation(model_field, owner_definition)` (orders/inputs.py:172-192) and `_build_input_fields(..., owner_definition=None)` (orders/inputs.py:195-257) both immediately `del` their forward-reserved args (orders/inputs.py:191, 223). This is correct today — the args are kept for signature symmetry with the filter twin (`filters/inputs.py::convert_filter_to_input_annotation`) and as a Spec Decision 12 future-extension affordance (per-type direction enum / `DISTINCT ON`), and both are documented as such in the docstrings. No action now. Defer until Spec Decision 12 (`0.0.9`-era per-type direction enum / DISTINCT-ON extension) lands and a converter body actually consults `model_field` / `owner_definition`; at that point the `del` lines disappear and the params become live. Quoted trigger: "a future DISTINCT ON extension or per-type direction enum in `0.0.9` would consult them".

### `_input_type_name_for` annotated `type` not `type[OrderSet]` to dodge the circular import

`_input_type_name_for(orderset_class: type)` (orders/inputs.py:131-144) widens the param to bare `type` rather than `type[OrderSet]` and documents the reason: `OrderSet` is only a `TYPE_CHECKING` import (orders/inputs.py:43) and the mixin guarantees `type_name_for` is in the MRO at runtime. Correct and documented. Defer until `OrderSet` can be imported at module scope without a circular-import risk (e.g. if `sets.py` stops importing back through the inputs/factory chain); then narrow to `type[OrderSet]`. No action now.

## What looks solid

### DRY recap

- **Existing patterns reused.** The whole-input traversal is delegated to the shared `utils/input_values.py` substrate — `SetInputTraversal` + `iter_active_fields` + the `RELATED` kind constant (orders/inputs.py:31, 298-304), the 0.0.9 DRY-pass consolidation point (`docs/feedback.md` Major 1). The generated-input mechanics (`build_strawberry_input_class`, `graphql_camel_name`, `iter_set_subclasses`, `materialize_generated_input_class`, `clear_generated_input_namespace`, `GeneratedInputFieldSpec`) are all imported single-sited from `utils/inputs.py` (orders/inputs.py:32-39) and exposed under domain-local aliases (orders/inputs.py:49-52) so tests and `factories.py` keep stable import targets.
- **New helpers considered.** `_input_type_name_for` (orders/inputs.py:131-144) and `INPUTS_MODULE_PATH` (orders/inputs.py:60) each centralize a single derivation/constant for multiple callers — correctly already factored, no further extraction warranted. A free function fusing `materialize_input_class` + `clear_order_input_namespace` was rejected: they wrap two distinct `utils/inputs.py` lifecycle entry points with opposite write/clear contracts; folding loses the per-call family-label pinning for no win.
- **Duplication risk in the current file.** The 2x `OrderSet` string literal flagged by the static helper is the `family_label="OrderSet"` arg to `materialize_input_class` (orders/inputs.py:337) and the `set_class_name="OrderSet"` arg to `clear_order_input_namespace` (orders/inputs.py:390) — two distinct keyword roles (collision family label vs. dynamic-import class name) into two distinct `utils/inputs.py` helpers, not a single shared key. Intentional sibling design, correctly NOT hoisted to a module constant.

### Other positives

- **`Ordering.resolve` NULLS semantics are exactly correct and well-documented.** `nulls_first = True if "NULLS_FIRST" in self.name else None` / `nulls_last` likewise (orders/inputs.py:103-104) yields Django's True-or-None sentinel contract: bare `ASC`/`DESC` pass `nulls_first=None, nulls_last=None` (database-default null ordering), the four `*_NULLS_*` members force exactly one sentinel. The docstring's portability note (orders/inputs.py:74-82) correctly flags the cross-backend NULL-partition divergence (SQLite NULLs-first vs Postgres/MySQL NULLs-last on bare `ASC`) and the cursor-stability nuance — this is the kind of non-obvious Django behavior comments should carry.
- **Six-member enum shape matches the GLOSSARY contract.** The `Ordering` members (orders/inputs.py:85-90) and `resolve` mapping match `docs/GLOSSARY.md::Ordering` (GLOSSARY.md:932-938) verbatim — six members, bare `ASC`/`DESC` "no NULLS positioning", four NULLS-positioning members map to the corresponding `.asc(nulls_first=True)` / `.asc(nulls_last=True)` / `.desc(...)` calls. No GLOSSARY drift.
- **`_get_concrete_field_names_for_order` documents a real empirical Django divergence.** The `not getattr(f, "many_to_many", False)` clause beyond the cookbook's bare `hasattr(f, "column")` (orders/inputs.py:165-169) is justified in the docstring against Django 6.0.5 (`ManyToManyField.column is None` so `hasattr` returns `True`); the `getattr(..., False)` default keeps the comprehension safe for field objects lacking the attr. Correct reflective-access discipline.
- **Order-side deliberate simplifications vs. the filter twin are explicit.** `_build_input_fields` (orders/inputs.py:216-221) and `normalize_input_value` (orders/inputs.py:281-285) both document the three/one removed layers vs. their filter twins (no operator-bag class, no logic fields, no `HIDE_FLAT_FILTERS`, no per-leaf shape divergence) — the subset relationship is stated, not silently divergent.
- **`normalize_input_value` defensive `field.spec is None` skip is honestly labelled.** orders/inputs.py:305-306 marks the branch "should be impossible after a finalize" — a defensive guard with accurate provenance, not a silently-dead branch.

### Summary

`orders/inputs.py` is a clean, well-factored module: empty `git log 14910230..HEAD` and empty `git diff HEAD` (not in the spec-035 change set, as the change context predicted). It is the order-side input namespace pairing the public `Ordering` direction enum (six members, correct Django True-or-None NULLS sentinels) with the Slice-2 input-data adapters and the module-global materialize/clear pair, all of which delegate their real mechanics to the single-sited `utils/input_values.py` + `utils/inputs.py` substrate from the 0.0.9 DRY pass. No High or Medium findings. The two Lows are both forward-looking deferrals (reserved future-extension params; a circular-import-driven type widening). The filter/order `normalize_input_value` pair was re-confirmed from the order side as an intentional NOT-a-shared-traversal sibling (different abstraction levels — whole-input walk vs. per-leaf coercion); the family-wrapper DRY is cross-folder and forwarded to the project pass. Landed as a no-source-edit cycle (shape #5).

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass; 270 files left unchanged (only the pre-existing COM812-vs-formatter config warning).
- `uv run ruff check --fix .` — pass; All checks passed.

### Notes for Worker 3
- No-source-edit cycle (shape #5): clean file, empty `git log 14910230..HEAD`, empty `git diff HEAD`, no High/Medium, both Lows forward-looking with explicit triggers.
- Low #1 (reserved `model_field`/`owner_definition` params): defer trigger — "a future DISTINCT ON extension or per-type direction enum in `0.0.9` would consult them". No edit.
- Low #2 (`_input_type_name_for` typed `type` not `type[OrderSet]`): defer trigger — `OrderSet` becomes importable at module scope without circular-import risk. No edit.
- DRY: both items are cross-folder (filter/order `normalize_input_value` confirmed NOT-a-shared-traversal from the order side per the project-pass forward; family-wrapper survey) — forwarded to the project pass `rev-django_strawberry_framework.md`, not acted here.
- No GLOSSARY-only fix in scope — `GLOSSARY.md::Ordering` (932-938) and `OrderSet` (940-948) verified accurate against the source, no drift.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern.

No comment/docstring edits warranted. Module docstring, `Ordering` portability note, the `_get_concrete_field_names_for_order` empirical-divergence rationale, and the per-function "mirror of filter twin with N removed layers" notes are all accurate and non-stale. The two `del ... # reserved` comments correctly point at the converter docstring. No TODO anchors in this file (static helper: 0 TODO comments).

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

Not warranted. No source/test/doc edit was made (no-source-edit cycle), so there is no behavior change to record. Per `AGENTS.md` #21 (do not update CHANGELOG.md unless explicitly instructed) and the active plan `docs/review/review-0_0_10.md` (silent on changelog for this item), no changelog entry is produced.

---

## Verification (Worker 3)

No-source-edit cycle (shape #5), terminal verify. Baseline HEAD `58ca2defaf012333cb06a06e484c7a48514657fe`.

### Logic verification outcome

High 0 / Medium 0 — confirmed. Both Lows independently verified as genuinely forward-looking deferrals:

- **`Ordering.resolve` NULLS positioning — exhaustively re-derived all six members against Django's True-or-None sentinel contract.** `nulls_first = True if "NULLS_FIRST" in self.name else None` / `nulls_last` likewise; `"ASC" in self.name` selects `.asc()` else `.desc()` (inputs.py:103-107). Member-by-member: `ASC` -> `F.asc(None, None)` (bare); `DESC` -> `F.desc(None, None)` (`"ASC"` not in `"DESC"`); `ASC_NULLS_FIRST` -> `F.asc(nulls_first=True)`; `ASC_NULLS_LAST` -> `F.asc(nulls_last=True)`; `DESC_NULLS_FIRST` -> `F.desc(nulls_first=True)` (`"ASC"` correctly NOT a substring of `"DESC_NULLS_FIRST"`); `DESC_NULLS_LAST` -> `F.desc(nulls_last=True)`. Maps verbatim onto `GLOSSARY.md::Ordering` (six members; bare = no NULLS positioning; four NULLS members -> the exact `asc/desc(nulls_first/last=True)` calls). Test-pinned by `tests/orders/test_inputs.py` (member-value asserts :67-81; bare-ASC/DESC `nulls_first is None and nulls_last is None` :85-99; FK-path resolve :104). No GLOSSARY drift.
- **OrderBy input generation + normalization correct.** `_build_input_fields` (inputs.py:195-257) emits leaf `Ordering | None` triples and `Annotated[target_name, strawberry.lazy(INPUTS_MODULE_PATH)] | None` for related branches, populating `_field_specs[(orderset_cls, python_attr)]` with the django source path (flat `shelf__code` shorthand handled :214). `normalize_input_value` (inputs.py:260-320) delegates the dataclass-vs-list walk / None-skip / leaf-vs-related classification to `utils/input_values.py::iter_active_fields` via `SetInputTraversal(field_specs=_field_specs, related_attr="related_orders", handle_top_level_list=True)`. Verified the `ActiveField` contract (`.kind`/`.spec`/`.related_obj`/`.raw_value`) against the producer (input_values.py:120-180, `RELATED="related"` :49); `related_attr="related_orders"` is the genuine collection attr (finalizer.py:1003, orders/sets.py:131). Leaf appends `(django_source_path, Ordering|None)`; related recurses with `f"{prefix}__{child_path}"`. The `field.spec is None` skip (inputs.py:305-306) is honestly labelled defensive. Normalization test-pinned at test_inputs.py:285-287.
- **Low #1 (reserved `model_field`/`owner_definition` `del`'d).** Both `convert_order_field_to_input_annotation` (:191) and `_build_input_fields` (:223) immediately `del` their forward-reserved args; correct today, kept for filter-twin signature symmetry + spec Decision 12 affordance. Verbatim trigger present: "a future DISTINCT ON extension or per-type direction enum in `0.0.9` would consult them". Forward-looking, no action.
- **Low #2 (`_input_type_name_for(orderset_class: type)` widened to bare `type`).** `OrderSet` is `TYPE_CHECKING`-only (:43); the param is widened to dodge the circular import, documented at :140-142; trigger is `OrderSet` becoming module-scope importable without circular risk. Forward-looking, no action.

### DRY findings disposition

Both DRY items confirmed genuinely cross-folder and correctly forwarded to the project pass (`rev-django_strawberry_framework.md`), not force-merged:

- **filter/order `normalize_input_value` NOT-a-shared-traversal — independently confirmed from BOTH sides.** Order side (inputs.py:260) is a whole-input walker `(orderset_cls, input_value)` delegating traversal to `iter_active_fields`. Filter side (filters/inputs.py:412-460) is a per-leaf value coercion `(filter_instance, raw_value, field_name)` doing pure `isinstance`-dispatch into scalar/list/dict form-data shapes with ZERO traversal and NO `iter_active_fields` call — read it directly to confirm. Different abstraction levels; only the name is shared. The one common substrate (`iter_active_fields`) is already single-sited and consumed by the order side. Non-merge sound.
- **Family-wrapper consolidation** (`materialize_input_class` / `clear_order_input_namespace` / domain-local aliases) — spans `filters/` + `orders/` + `utils/`; mechanics already single-sited in `utils/inputs.py`; a same-folder hoist would re-add an import edge for no gain. Correctly cross-folder-forwarded.
- The 2x `OrderSet` repeated literal is two distinct keyword roles (`family_label="OrderSet"` collision label :337 vs `set_class_name="OrderSet"` dynamic-import class name :390) into two distinct `utils/inputs.py` helpers — correctly NOT hoisted to a constant.

### Temp test verification

- None used — the load-bearing claims (six-member NULLS resolution, the `iter_active_fields` traversal contract, the filter-twin abstraction divergence) were all confirmable by reading source + existing tests directly; no behavior question required a temp probe.

### Verification outcome

`cycle accepted; verified` — sets top-level `Status: verified` AND marks the `orders/inputs.py` checklist box. Shape #5 gates all met: `git diff HEAD -- orders/inputs.py` empty; `git log 14910230..HEAD -- orders/inputs.py` empty; the file is ABSENT from the cycle-wide diff stat against `14910230` (the zero-edit proof); every Worker 2 section opens with the no-source-edit preamble line; both Lows carry verbatim in-source triggers (no GLOSSARY-only fix); changelog `Not warranted` cites BOTH `AGENTS.md` #21 AND the active plan's silence, and `git diff -- CHANGELOG.md` is empty; `ruff format --check` (1 file already formatted) + `ruff check` (All checks passed) clean on the target. The cycle-wide diff-stat dirty paths (filters/sets.py, management/commands/*, optimizer/*, permissions, types/*, utils/*, GLOSSARY, CHANGELOG, and their tests) belong to OTHER planned cycle items, not this one — verified per-item.

---

## Iteration log

(none)
