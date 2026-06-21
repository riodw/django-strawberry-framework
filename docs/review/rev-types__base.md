# Review: `django_strawberry_framework/types/base.py`

Status: verified

## DRY analysis

- **Defer-with-trigger: hoist the shared "target validation" two-stage shape (`_validate_X` stage-1 + `_validate_X_targets` stage-2) into a generic Meta-target validator pair.** Two families already follow byte-identical staging — `_validate_nullability_override_targets` (base.py:1242-1330) and `_validate_relation_shape_targets` (base.py:1333-1401) — and both already route their unknown/excluded halves through the shared `_selected_meta_targets` helper (base.py:1199-1239). The per-name domain checks (consumer-authored / relation / Relay-pk / many-side) legitimately differ, so the remaining duplication is only the iterate-sorted-targets scaffold around them. Defer until a **third** `Meta.*`-target feature lands (e.g. `Meta.search_fields` field-level validation); at that point fold the three stage-2 loops through a shared `(name, field) -> str | None` per-name-check callback list. Acting now would over-abstract two call sites whose per-name checks share no logic.
- **Defer-with-trigger: collapse the three Relay-Node gate compose sites onto one helper.** `_validate_connection` (base.py:217-221), `_validate_globalid_strategy` (base.py:342-345), and `_validate_relation_shapes` (base.py:269-273) each compose `_RELAY_NODE_GATE_LEAD` + a tail (`_RELAY_NODE_GATE_INHERIT_TAIL` for the first two, `"or remove the key."` for the third) into an identical `if not relay_shaped: raise ConfigurationError(f"{subject} {LEAD} {tail}")` shape. The literals are already single-sourced; only the three-line raise scaffold repeats. Defer until a **fourth** Relay-Node-gated `Meta` key lands; then extract `_require_relay_shaped(subject, relay_shaped, tail)`. The two-tail split (inherit-tail vs remove-key-tail) means a premature helper would need the tail threaded anyway, so the win today is marginal.

## High:

None.

## Medium:

None.

## Low:

None.

## What looks solid

### DRY recap

- **Existing patterns reused.** The module is itself the resolution point for several cross-cutting DRY contracts and reuses canonical helpers throughout: `_selected_meta_targets` (base.py:1199-1239) single-sources the unknown/excluded guard for both override families; `_format_unknown_fields_error` (base.py:801-815) single-sources the "unknown fields … Available:" message across `Meta.fields` / `Meta.exclude` / `Meta.optimizer_hints` / `nullable_overrides` / `relation_shapes`; `_is_relay_shaped` (base.py:446-457) is the single Relay-shape predicate read by the H1 collision guard, all three Meta-key gates, and the pk-suppression branch in `_build_annotations`; the Relay-Node gate literals (`_RELAY_NODE_GATE_LEAD` / `_RELAY_NODE_GATE_INHERIT_TAIL`), the strategy vocab (`STRING_GLOBALID_STRATEGIES` / `DEFAULT_GLOBALID_STRATEGY`), the relation-shape vocab (`RELATION_SHAPE_VALUES` / `DEFAULT_RELATION_SHAPE`), and the interfaces lead-in (`_INTERFACES_SHAPE_ERROR_LEAD_IN`) are all named once and composed at their sites. `FieldMeta.from_django_field` / `FieldMeta.is_many_side` / `FieldMeta.relation_kind` / `.nullable` are the single classifiers feeding both validation and synthesis; `convert_field_output` (signature confirmed at converters.py:414-418) owns the file/image vs scalar routing so `_build_annotations` carries no file/image branch of its own.
- **New helpers considered.** Two generic-validator candidates evaluated and **deferred with explicit triggers** (see DRY analysis): the two-stage Meta-target validator pair (fold on a third target feature) and the Relay-Node gate composer (fold on a fourth gated key). Neither acts now — both call counts are at two/three and the per-site differences (per-name checks, two-tail split) would force argument threading that cancels the win.
- **Duplication risk in the current file.** The repeated literals flagged by the static overview (`optimizer_hints` 4x, `total_count` 4x, `connection` 3x, `relation_shapes` 3x, the `Meta.*` key names 2x each) are Meta-key name tokens read off `getattr(meta, …)` plus their matching `_ValidatedMeta`/`DjangoTypeDefinition` field names — intentional sibling spellings of the same public key across the read site, the snapshot field, and the error text, not hoistable string-keyed dispatch. The two MRO-vs-own-dict reads in `_validate_meta` (`meta.__dict__` for the typo guard at base.py:1052, `getattr` for mutual-exclusion at base.py:1061-1062) are deliberately different and documented as such (base.py:1045-1051) — must not be "unified".

### Other positives

- **Fail-loud, fail-closed validation discipline.** Every Meta-shape violation raises `ConfigurationError` at type-creation time with the offending model/field named. Silent drops are avoided: `_validate_optimizer_hints` (base.py:1136-1196) rejects hints on excluded or scalar fields (not just unknown ones) because the walker only reads hints on the relation branch — the "validates A but not the intersection of A∩selected-relation" gap is explicitly closed (base.py:1181-1190).
- **Relay-`id` collision guard correctness.** `_id_annotation_is_relay_node_id` (base.py:402-443) reads `cls.__annotations__` directly (no `typing.get_type_hints`), which the docstring documents as the fix for an interpreter-divergent branch (3.10 vs 3.11+ forward-ref handling) — pinned by a named regression test. The string-form regex `_NODEID_STRING_RE` (base.py:384) anchors `(?:^|\.)NodeID\[` so qualified/unqualified spellings pass while prefixed lookalikes (`NotNodeID[int]`) are rejected. The precondition (`"id" in cls.__annotations__`) is gated by the only call site, and a future violator gets a loud `KeyError` rather than a misleading `False`.
- **Two-stage validation split is principled.** Shape-only checks that need just the raw `Meta` (mutual exclusion, both-sets collision, vocab membership, Relay-Node gate) run in `_validate_meta`; checks needing selected fields / consumer-override union / cardinality (`_validate_nullability_override_targets`, `_validate_relation_shape_targets`) run from `__init_subclass__` after `_select_fields`. This is the documented spec-029 two-stage precedent and keeps each guard at the earliest point its inputs exist.
- **`get_queryset` override detection is constant-time and inheritance-correct.** `_is_default_get_queryset` is stamped before the `meta is None` early return so an abstract base overriding `get_queryset` without a `Meta` still flips the flag for concrete descendants (pinned by `test_has_custom_get_queryset_inherits_through_abstract_base_without_meta`); `has_custom_get_queryset` reads the definition's frozen flag when present, falling back to the negated sentinel.
- **In-function imports for `FilterSet` / `OrderSet` are correct and load-bearing.** `_validate_filterset_class` / `_validate_orderset_class` import at function scope to dodge the `types -> filters/orders -> types` module-load cycle, with "Do NOT hoist" comments; validation runs at `_validate_meta` time, well after module load.
- **File/image output wiring preserved through the DRY change.** `_build_annotations` computes the `force_nullable` tri-state (nullable_overrides -> True, required_overrides -> False, else None) once and threads it verbatim into `convert_field_output`, which owns the `FileField`/`ImageField` -> `DjangoFileType`/`DjangoImageType` routing. The base.py side carries no file/image conditional; consumer-authored names short-circuit before reaching the converter. Matches GLOSSARY `#metarequired_overrides` (the "as of `0.0.11`" file/image default-nullable / `required_overrides`-opt-out prose) byte-for-byte.

### Summary

`types/base.py` is the central `DjangoType` adapter and the package's largest public surface; it is in excellent shape. This cycle is a no-source-edit re-review: both `git diff 54b518c8 -- types/base.py` and `git diff HEAD -- types/base.py` are empty, so the DRY cycle's `+21`-line work is fully cumulative-in-HEAD (`git log 54b518c8..HEAD -- types/base.py` returns nothing). The DRY changes preserve semantics — verified at source that `convert_field_output`'s signature matches the `_build_annotations` call, that `FieldMeta.is_many_side` backs the relation-shapes cardinality check, and that the Relay-shape predicate / unknown-field-error / Meta-target-guard helpers are genuinely single-sourced. No High, Medium, or Low findings. GLOSSARY `#djangotype` and the override/connection/globalid/relation_shapes key entries are accurate with no drift (the "shipped (`0.0.9`)" rows are historical ship versions, not stale; the file/image extension is correctly documented "as of `0.0.11`"). Two DRY consolidation candidates are recorded, both defer-with-trigger (third target feature; fourth Relay-gated key). Genuine shape #5.

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — `289 files left unchanged`.
- `uv run ruff check --fix .` — `All checks passed!`.

### Notes for Worker 3
- Genuine shape #5: both `git diff 54b518c8a152cc4321b223ab1056faae6f4d53f5 -- django_strawberry_framework/types/base.py` and `git diff HEAD -- django_strawberry_framework/types/base.py` are empty; the DRY-cycle changes are cumulative-in-HEAD.
- All severities `None.`; both DRY items are defer-with-trigger (no act-now).
- No GLOSSARY-only fix in scope — `#djangotype` and the Meta-key entries (`#metaconnection`, `#metaglobalid_strategy`, `#metarelation_shapes`, `#metanullable_overrides`, `#metarequired_overrides`) are accurate, no drift. The "shipped (`0.0.9`)" version rows are historical ship versions; the file/image extension is correctly documented "as of `0.0.11`".
- Semantics-preservation spot-checks: `convert_field_output(field, type_name, *, force_nullable=None)` (converters.py:414-418) matches the `_build_annotations` call; `FieldMeta.is_many_side` (field_meta.py:139) backs the `relation_shapes` cardinality guard.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern. No source edits this cycle, so no comment/docstring changes. Docstrings and inline comments were read in full and are accurate (the in-function-import "Do NOT hoist" notes, the `meta.__dict__`-vs-`getattr` "do not unify" note, and the file/image routing comment in `_build_annotations` all match the live behavior).

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern. Not warranted — no source, test, GLOSSARY, or CHANGELOG edits this cycle. AGENTS.md: "Do not update CHANGELOG.md unless explicitly instructed". Active plan (`docs/review/review-0_0_11.md`) records no changelog requirement for this item.

---

## Verification (Worker 3)

### Logic verification outcome
No High / Medium / Low findings to address — all severities `None.`, genuine shape #5 (no-source-edit). Independently confirmed the `What looks solid` claims at live source:
- **`convert_field_output` signature ↔ `_build_annotations` call.** `convert_field_output(field, type_name, *, force_nullable=None)` at `converters.py::convert_field_output` (read lines 414-419) matches the call site `_build_annotations` at `types/base.py #"annotations[field.name] = convert_field_output("` (1651-1655: `convert_field_output(field, cls.__name__, force_nullable=force_nullable)`). Base carries NO file/image branch — the converter owns the `FileField`/`ImageField` → `DjangoFileType`/`DjangoImageType` routing via `FIELD_OUTPUT_TYPE_MAP` (`converters.py::_field_output_type_for`); base only computes the tri-state and threads it.
- **force_nullable tri-state threaded verbatim.** `_build_annotations` computes `True` when `field.name in nullable_overrides`, `False` when `in required_overrides`, else `None` (`types/base.py #"if field.name in nullable_overrides:"`, 1634-1639), passed unchanged into the converter. Disjointness/non-relation of the two sets validated upstream in `_validate_nullability_override_targets` so the elif is exhaustive.
- **`FieldMeta.is_many_side` backs the relation_shapes cardinality guard.** `is_many_side` property at `optimizer/field_meta.py::FieldMeta.is_many_side` (139-141, delegates to `is_many_side_relation_kind`); consumed at `types/base.py #"if not field_map[snake_case(name)].is_many_side:"` (1389) inside `_validate_relation_shape_targets` — single-valued relations rejected with a connection-shape error.
- **Single-sourcing confirmed by grep.** `_is_relay_shaped` defined once (base.py:446), read by the H1 collision guard (570), the `Meta.connection` / `relation_shapes` / `globalid_strategy` gates (1084) and the pk-suppression branch (1567). `_format_unknown_fields_error` defined once (801), routed by all field-name error sites (fields/exclude/optimizer_hints/nullable_overrides/relation_shapes). `_selected_meta_targets` defined once (1199), the shared stage-1 for both override-target validators (1297, 1370).
- **Relay-`id` collision handling.** `_id_annotation_is_relay_node_id` (402-443) reads `cls.__annotations__["id"]` directly (no `get_type_hints`) — the interpreter-divergence fix is documented and the precondition (`"id" in __annotations__`, gated by the lone call site) gives a loud `KeyError` on violation, not a misleading `False`.
- **`Meta.primary`.** Bool-validated at `_validate_meta` (1066-1068: `getattr(meta, "primary", False)` → `ConfigurationError("Meta.primary must be a bool")`), threaded to the definition and `registry.register_with_definition(..., primary=...)`.

### DRY findings disposition
Both items are **defer-with-trigger**, no act-now:
1. Two-stage Meta-target validator pair (`_validate_X` + `_validate_X_targets`) — trigger is a **third** `Meta.*`-target feature. Both current families (`_validate_nullability_override_targets`, `_validate_relation_shape_targets`) already route through `_selected_meta_targets`; the per-name domain checks legitimately differ (relation / many-side / consumer-authored), so the remaining duplication is only the sorted-iterate scaffold. Correct to defer.
2. Relay-Node gate composer — trigger is a **fourth** Relay-Node-gated `Meta` key. Confirmed exactly three compose sites at live source: `Meta.connection` (base.py:219-220, lead + `_RELAY_NODE_GATE_INHERIT_TAIL`), `Meta.relation_shapes` (271-272, lead + `"or remove the key."`), `_validate_globalid_strategy` (344, lead + inherit-tail). The two-tail split (inherit-tail vs remove-key-tail) means a premature helper would thread the tail anyway; literals already single-sourced (`_RELAY_NODE_GATE_LEAD`/`_RELAY_NODE_GATE_INHERIT_TAIL` at 107/113). Correct to defer.

No GLOSSARY-only fix present (would be disqualifying for a #5). `#djangotype` (GLOSSARY.md:453-492) is accurate vs live source: `Meta.primary` multi-type support, the Relay-`id` collision guard escape hatches matching `_id_annotation_is_relay_node_id`, the consumer-authored short-circuit, and the unknown/deferred Meta-key rejection all match. "shipped (`0.0.5`)" is the historical ship version (not stale); the file/image extension is documented "as of `0.0.11`" under `#metarequired_overrides`. Private `_`-prefixed helpers correctly carry no entry — absence is not drift. Genuine #5, not a missed #4.

### Temp test verification
- None — no behavior suspicion to prove; no temp tests created.

### Verification outcome
- `cycle accepted; verified` — sets top-level `Status: verified` AND marks the checklist box.

Zero-edit proof: `git diff 54b518c8 -- types/base.py`, `git diff HEAD -- types/base.py`, `git log 54b518c8..HEAD -- types/base.py`, owned-paths `--stat` (`django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md`), and `git diff -- CHANGELOG.md` all empty. Each Worker 2 section opens "Filled by Worker 1 per no-source-edit cycle pattern." Changelog `Not warranted` cites both AGENTS.md and active-plan silence. `uv run ruff format --check` (1 file already formatted) and `uv run ruff check` (All checks passed!) on base.py both pass.

---

## Iteration log

(none)
