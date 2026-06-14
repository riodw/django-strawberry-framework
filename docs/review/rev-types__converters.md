# Review: `django_strawberry_framework/types/converters.py`

Status: verified

(Supersedes the prior 0.0.7 artifact wholesale: that revision referenced `review-0_0_7.md`, carried `Status: verified`, and its five comment-pass Lows are ALL already merged into live source — the `convert_choices_to_enum` three-bullet `Raises:` block, the interleaved seven-step numbered list, the recursive-`base_field` `type_name` `Args:` note, and the `_sanitize_member_name` load-bearing ordering paragraph are present at the cited symbols today. Re-raising any of them would be a resolved-Low regression. This 0.0.9 pass re-reviews against live source with the `nullable_overrides` / `required_overrides` → `force_nullable` override seam as the focus.)

## DRY analysis

- Defer until a third soft-imported postgres-contrib field lands (next candidates: `CIText`, range fields); collapse `converters.py::_resolve_array_field` (`converters.py:89-99`) and `converters.py::_resolve_hstore_field` (`converters.py:102-112`) into one `_resolve_postgres_field(attr_name: str) -> type[models.Field] | None`, with module-level `_X_FIELD_CLS = _resolve_postgres_field("X")`. Two verbatim-except-symbol six-line bodies (plus a one-word-swapped docstring mirror) are below the extraction threshold today; the differing token is load-bearing for the `monkeypatch.setattr(converters, "_ARRAY_FIELD_CLS", ...)` test ergonomics, and per-field naming keeps the binding greppable. Trigger: third postgres soft-import.
- Defer until the `convert_scalar` ArrayField / HStoreField branches gain a third sentinel-guarded postgres branch (next candidate: `CIText` family → `str`); extract `_postgres_branch(field, sentinel, *, on_choices_message, build)` from `convert_scalar`'s ArrayField block (`converters.py:228-241`) and HStoreField block (`converters.py:246-255`). Both share the five-step shape (sentinel-None short-circuit / `isinstance` test / outer-`choices` rejection with field-shape-specific message / per-branch synthesis / outer-`effective_null` widening). At two sites the parameterized signature (the choices-rejection message body and the `list[inner]`-vs-`strawberry.scalars.JSON` synthesis) adds weight without payoff. Trigger fires when the third branch lands and synthesis-step diversity justifies the abstraction.
- Defer until a fourth `_sanitize_member_name` rewrite rule lands (current four: ASCII-non-ident → leading-digit/empty → keyword → GraphQL-reserved/dunder); convert the sequential rewrite chain at `converters.py:291-297` to a table-driven `_MEMBER_NAME_RULES: tuple[tuple[Callable[[str], bool], Callable[[str], str]], ...]` loop. Four rules with a step-3/step-4 ordering dependency read cleaner inline than as a tuple-of-callables; a fifth conditional-prefix rule would tip the balance.

## High:

None.

## Medium:

None.

## Low:

### `convert_scalar` `Raises:` block does not enumerate the `force_nullable`/override-driven non-raise paths — recorded, no edit

The 0.0.9 `force_nullable` tri-state (`converters.py::convert_scalar` `Args:` at `converters.py:183-192`, body at `converters.py:218`) is fully and accurately documented in the `Args:` and the algorithm steps 0/3 and the inline comment at `converters.py:212-227`. No `Raises:` gap exists for the override itself — the override only changes which boolean drives widening; it adds no new raise site. Recorded here only to make explicit that the `force_nullable` path was scrutinized and the docstring is complete (steps 0, 0b, 3 all read `effective_null`; the `Args: force_nullable` entry names the `None`/`True`/`False` tri-state and the source `Meta.nullable_overrides` / `Meta.required_overrides`; the recursion-left-unset contract is stated at `converters.py:190-192` and `:225-227`). No edit in scope.

### `convert_scalar` choices-vs-override interaction for a `required_overrides`'d nullable choice field is correct but undocumented at the step level — forward-looking, no edit

Steps 2 and 3 of the algorithm (`converters.py:261-264`) run choice substitution (`py_type = convert_choices_to_enum(...)`) BEFORE the `if effective_null` widen, so a `required_overrides` entry (`force_nullable=False`) on a `null=True` choice column yields bare `EnumType` (not `EnumType | None`) — the enum is built regardless, then NOT widened. This is the documented and intended behavior (GLOSSARY `Meta.nullable_overrides` at `docs/GLOSSARY.md:761` — "the enum's nullability flips; its members are unchanged"), and it is pinned by `tests/types/test_converters.py::test_convert_scalar_force_nullable_on_choice_field` (1591), which asserts both the widen (`force_nullable=True`) and the narrow (`force_nullable=False`) directions on a choice fixture. The algorithm docstring's "Order matters" paragraph (`converters.py:170-174`) already states the override flips the choice enum's nullability "for free." No per-step gap worth an edit; recorded for the next reviewer as the load-bearing interaction.

## What looks solid

### DRY recap

- **Existing patterns reused.** `convert_scalar` (`converters.py:260`) delegates the MRO walk to the single shared `scalar_for_field` helper (`converters.py:119-139`), which is the same field-class → scalar lookup consumed by the filter-input converter via a LOCAL import (`filters/inputs.py::_scalar_from_model_field` at `filters/inputs.py:248-264`, `from ..types.converters import scalar_for_field`) — so a column resolves to the SAME scalar on the selected-field side and the filter-input side, including consumer-registered `SCALAR_MAP` entries. `convert_choices_to_enum` (`converters.py:353`, `:377`) routes all enum-cache reads/writes through `registry.get_enum` / `register_enum`; no direct `_enums` manipulation, so the cache-vs-storage split lives in `registry.py`. `resolved_relation_annotation` (`converters.py:388`) reuses `FieldMeta.from_django_field` for cardinality / nullable rules, sharing the relation-annotation shape with `optimizer/walker.py` and `types/finalizer.py`'s deferred-resolution path. The ArrayField branch's recursive `convert_scalar(field.base_field, type_name)` (`converters.py:239`) reuses the entire converter pipeline (choice substitution + inner-null widening) on the inner element, so the branch is a thin outer-wrap-and-widen.
- **New helpers considered.** `_postgres_branch(field, sentinel, ...)`, `_resolve_postgres_field(attr_name)`, and a `_MEMBER_NAME_RULES` table were each considered and deferred-with-trigger (see DRY analysis) — all gate on a third-site landing; at the current two-/four-site footprint each abstraction adds parameter weight or obscures the per-field/per-rule grep target without saving real bytes.
- **Duplication risk in the current file.** The paired `_resolve_array_field` / `_resolve_hstore_field` body+docstring shape AND the paired ArrayField / HStoreField branch shape in `convert_scalar` are intentional sibling design — the second site of each pair is load-bearing for postgres-contrib soft-import symmetry, and the cross-method DRY triggers fire at the third-site landing. The repeated `f"{field.model.__name__}.{field.name}"` error-prefix across the seven raise sites (`converters.py:136`, `:231`, `:235`, `:249`, `:333`, `:347`, `:372`) is the canonical Django-field error shape used package-wide; duplicating it is cleaner than a `_field_qualname(field)` helper that would obscure the consumer-visible error grep target.

### Other positives

- **0.0.9 `force_nullable` override seam is the cleanest possible factoring.** The tri-state collapses to ONE boolean at `converters.py:218` (`effective_null = field.null if force_nullable is None else force_nullable`), and every outer widening site reads `effective_null` — the ArrayField outer-`list[inner]` widen (`converters.py:241`), the HStoreField widen (`converters.py:255`), and the scalar/choice widen (`converters.py:263`). No per-branch override logic, no second read of `field.null` after line 218. The override is sourced and applied entirely in `types/base.py::_build_annotations` (`base.py:1617-1627`: membership in `nullable_overrides` → `True`, `required_overrides` → `False`, else `None`), validated disjoint + scalar-only by `_validate_nullability_override_targets` (`base.py:1241+`) BEFORE the loop, so the elif at `base.py:1619` is exhaustive. The recursion into `base_field` (`converters.py:239`) is deliberately left `force_nullable`-unset so inner element nullability follows `base_field.null` and is unaffected by the outer override — pinned by `test_convert_scalar_force_nullable_on_array_field` (`tests/types/test_converters.py:1613`).
- **Override contract comprehensively test-pinned.** `test_convert_scalar_force_nullable_true_widens_non_null_column` (1561), `_false_narrows_nullable_column` (1567), `_none_honors_field_null` (1573), `_on_choice_field` (1591), `_on_array_field` (1613), `_on_hstore_field` (1646) cover all four branches × both override directions × the inner-follows-`base_field.null` contract. The choice test pins the strict-equality enum-flip; the array test pins outer-flips-inner-follows.
- **Sentinel-None short-circuit guards the `isinstance(field, _X_FIELD_CLS)` calls.** `_ARRAY_FIELD_CLS is not None` (`converters.py:228`) and `_HSTORE_FIELD_CLS is not None` (`converters.py:246`) prevent `TypeError: isinstance() arg 2 must be a type` on dev environments without the postgres driver; the soft-imports (`converters.py:89-116`) return `None` on `ImportError` so package import succeeds driverless.
- **ArrayField sentinel dispatch runs BEFORE the MRO walk.** The `isinstance` dispatch at `converters.py:228` precedes `scalar_for_field` at `converters.py:260`, so a `subclass-of-models.Field` test double does not accidentally match a `SCALAR_MAP` parent — comment at `converters.py:219-227` documents this load-bearing ordering.
- **MRO walk is the canonical Django field extension path.** `scalar_for_field` walks `type(field).__mro__` (`converters.py:132-134`) so consumer subclasses of supported fields resolve to the parent's scalar without registration; an unmatched field raises a consumer-actionable `ConfigurationError` naming the model.field and the `SCALAR_MAP` / `Meta.exclude` recourses (`converters.py:135-139`).
- **Choices-then-null ordering documented as load-bearing.** `convert_scalar`'s algorithm doc (`converters.py:170-174`) states choices replaces `py_type` BEFORE null widening so nullable choice fields end up `EnumType | None`, not `(str | None)`-collapsed.
- **Grouped-choices detection on `label` not `value`.** The loop at `converters.py:337-351` rejects Django's grouped form by testing the SECOND tuple element (`label`), with the inline comment (`converters.py:338-344`) explaining that the value slot is the human-readable group name in the grouped form, so checking it produces a false negative.
- **Enum members preserve raw DB values, not sanitized member names.** `convert_choices_to_enum` builds the enum from `members[member] = value` (`converters.py:360-365`) so `enum_cls.value` is the raw DB string while the GraphQL-side member name is sanitized — the wire boundary stays stable across label edits. Collision detection (`converters.py:362-374`) raises a `ConfigurationError` naming each colliding member and its source values.
- **Choice enum cached on `(model, field.name)`.** `convert_choices_to_enum` (`converters.py:353-355`, `:377`) keys the registry cache on `(field.model, field.name)`; first-`DjangoType`-wins-the-name documented at `converters.py:314-316`. Model-identity key (not type-identity) means sibling types pointing at the same column receive the cached enum unchanged.
- **`resolved_relation_annotation` is a thin three-line `FieldMeta` dispatch.** `converters.py:388-393` delegates cardinality (`is_many_side` → `list[T]`) and nullability (`nullable` → `T | None`) to `FieldMeta`; reused by `types/finalizer.py`'s deferred-resolution path per the module docstring (`converters.py:13-17`).
- **No `OptimizerError` raise site exists in this file.** The dispatch named `OptimizerError`/`ConfigurationError` raise sites; this file raises only `ConfigurationError` (seven sites: `converters.py:135`, `:230`, `:234`, `:248`, `:332`, `:346`, `:371`). `OptimizerError` is an `optimizer/`-folder symbol (field_meta + plans per worker memory) and does not appear here.
- **GLOSSARY drift quick-check: clean.** `Scalar field conversion` (`docs/GLOSSARY.md:1118-1144`) lists every shipped scalar row including `BigInt` / `JSON` / `ArrayField` / `HStoreField`, the subclass-MRO walk, the `DurationField` / `BinaryField` intentional absences, and `null=True` widening — all match `SCALAR_MAP` (`converters.py:54-81`) and the body. `Specialized scalar conversions` (`docs/GLOSSARY.md:1198+`) lists the five 0.0.6 rows accurately. `Choice enum generation` (`docs/GLOSSARY.md:203-211`) correctly documents the `(model, field_name)` cache key, value-not-label sanitization, and grouped-choices rejection. `Meta.nullable_overrides` (`docs/GLOSSARY.md:746-774`) and `Meta.required_overrides` (`docs/GLOSSARY.md:840-848`) accurately describe the `force_nullable` tri-state seam, the scalar-only scope, the choice-enum / ArrayField-outer / HStoreField flip behavior, and the inner-follows-`base_field.null` carve-out — all verified against the source. `Scalar field override semantics` (`docs/GLOSSARY.md:1146-1160`) covers the consumer-annotation short-circuit that bypasses `convert_scalar` entirely (a `types/base.py` concern, not this file). No GLOSSARY edit in scope.

### Summary

`types/converters.py` (394 lines) is the scalar / choice-enum / relation-annotation conversion home. The 0.0.9 focus — `nullable_overrides` / `required_overrides` → `force_nullable` — is implemented at the cleanest possible altitude: a single `effective_null` boolean computed once at `converters.py:218` and read by every outer widening site across the scalar, choice-enum, ArrayField, and HStoreField branches, with the ArrayField recursion deliberately left override-unset so inner-element nullability follows `base_field.null`. The override is sourced/validated/applied entirely in `types/base.py::_build_annotations`; `convert_scalar` is a faithful consumer of the tri-state. All four branches × both directions × the inner-follows carve-out are test-pinned. The shared `scalar_for_field` MRO walk is the single field-class → scalar lookup consumed by both this module and `filters/inputs.py` via local import. The prior-cycle's five comment-pass Lows (`Raises:` block, seven-step list, recursive-`type_name` note, ordering paragraph) are all already merged into live source and were NOT re-raised. Zero High, zero Medium; two Lows both recorded-only / forward-looking (no edit warranted — the `force_nullable` documentation is already complete and the choice-vs-override step interaction is correct and test-pinned). GLOSSARY drift quick-check clean across all six relevant anchors. Three defer-with-explicit-trigger DRY items, all gating on a third postgres-contrib site. No-source-edit cycle (shape #5).

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched

None — no-source-edit cycle.

### Tests added or updated

None — no-source-edit cycle.

### Validation run

- `uv run ruff format django_strawberry_framework/types/converters.py` — `1 file left unchanged`.
- `uv run ruff check django_strawberry_framework/types/converters.py` — `All checks passed!`.

### Notes for Worker 3

- Shadow overview: `docs/shadow/django_strawberry_framework__types__converters.overview.md` (+ `.stripped.py`) — Django/ORM markers: none; calls-of-interest: 4× `isinstance` (the two postgres-sentinel dispatches + the grouped-choices `label` check + the nested-ArrayField check), all reflective-access-audited and justified above; repeated string literals: none.
- Per-Low dispositions: (1) `convert_scalar` `Raises:`/`force_nullable` documentation — recorded only; the docstring is already complete, no gap, no edit. (2) `required_overrides`'d nullable-choice step interaction — forward-looking / recorded only; behavior is correct and pinned by `test_convert_scalar_force_nullable_on_choice_field` (`tests/types/test_converters.py:1591`); the "Order matters" paragraph (`converters.py:170-174`) already documents it. Neither Low warrants a source edit.
- No GLOSSARY-only fix in scope — all six relevant anchors verified accurate against live source.
- Prior-cycle Lows confirmed already-merged into live source (do not re-raise): three-bullet `Raises:` block at `converters.py:318-328`, interleaved seven-step list at `converters.py:303-312`, recursive-`base_field` `type_name` `Args:` note at `converters.py:181-185`, `_sanitize_member_name` load-bearing ordering paragraph at `converters.py:283-289`.
- `git status` at task start: treat any unrelated dirty paths as concurrent maintainer work per AGENTS.md #33; left untouched. `CHANGELOG.md` not touched.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern. No comment/docstring edit warranted — the prior-cycle comment-pass edits are already merged and the `force_nullable` documentation added in 0.0.9 (`Args:` tri-state entry, algorithm steps 0/0b/3, the `effective_null` inline comment) is complete and accurate.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern. `Not warranted`.

- **AGENTS.md #21**: "Do not update CHANGELOG.md unless explicitly instructed."
- **Active plan silence**: `docs/review/review-0_0_9.md` does not authorize a CHANGELOG edit for this cycle.

No source-behaviour change, no public-API change, no typed-error contract change — nothing to record.

---

## Verification (Worker 3)

### Logic verification outcome
Shape #5 no-source-edit, terminal-verify. Owned-file diff empty: `git diff --stat 0872a20 -- types/converters.py` byte-unchanged. Independently re-derived the 0.0.9 override seam LIVE (`docs/review/temp-tests/types_converters/grid.py` + `array_hstore.py`, `config.settings`):
- **`effective_null` single boolean (converters.py:218)** — confirmed every outer widening site reads it: scalar (:263), choice (:262→:263), ArrayField list-wrap (:241), HStoreField (:255). No second `field.null` read after :218.
- **true/false/none × scalar/choice/array/hstore grid** — 14 array/hstore + 11 scalar/choice assertions, 0 fails. none honors `field.null`; true forces optional regardless of column; false forces bare regardless. Choice false-direction yields bare `EnumType` (not widened), true/none widen — matches the GLOSSARY enum-flip claim.
- **ArrayField recursion drops the override (headline correctness)** — drove BOTH directions: outer `force_nullable=False` with inner `base_field.null=True` → bare outer list, inner element STILL optional; outer `force_nullable=True` with inner `base_field.null=False` → optional outer, inner element STILL bare. The recursive `convert_scalar(field.base_field, type_name)` (:239) is genuinely override-unset so inner follows `base_field.null` independently of the outer override.
- **Override source** — `types/base.py::_build_annotations` (base.py:1617-1627) byte-clean (not in `git status`); `field.name in nullable_overrides`→True / `in required_overrides`→False / else None, validated disjoint+scalar-only by `_validate_nullability_override_targets` before the loop → exhaustive elif. Matches artifact.
- **scalar→type mapping** — `CharField`→`str`, `BigIntegerField`→`BigInt` via the shared `scalar_for_field` MRO walk.
- **choice→enum caching keyed on `(model, field.name)`** — the false-direction and none-direction calls return the SAME enum class (`MCNullEnum`), confirming `registry.get_enum(field.model, field.name)` cache hit before name computation.
- **Outer-choices rejection** still fires under override on both ArrayField and HStoreField (ConfigurationError naming `M.arr`/`M.hf`).

Both Lows confirmed forward-looking / recorded-only: (1) `Raises:`/`force_nullable` doc — no new raise site, docstring complete (steps 0/0b/3 + Args tri-state); (2) `required_overrides`'d nullable-choice step interaction — correct and pinned by `test_convert_scalar_force_nullable_on_choice_field` (test_converters.py:1591, grep-confirmed). All six `test_convert_scalar_force_nullable_*` pins grep-match (1561/1567/1573/1591/1613/1646).

### DRY findings disposition
Three DRY items all defer-with-explicit-trigger, gating on a third postgres-contrib site (`_resolve_postgres_field` collapse; `_postgres_branch` extraction; `_MEMBER_NAME_RULES` table). Each below extraction threshold at current 2-/4-site footprint; carried forward.

### Temp test verification
- Temp tests: `docs/review/temp-tests/types_converters/grid.py`, `docs/review/temp-tests/types_converters/array_hstore.py` (gitignored).
- Disposition: deleted at cycle closeout (Worker 0). Behavior already permanently pinned by the six `test_convert_scalar_force_nullable_*` tests; no promotion needed.

### Sibling-cycle attribution
All dirty source/GLOSSARY paths in the diff stat attribute to CLOSED sibling cycles (conf/connection/exceptions/filters.factories/filters.sets/list_field/inspect_django_type/optimizer.extension/selections/walker/orders.factories/orders.inputs — each `rev-*.md` Status: verified). `feedback2/3.md` delete = AGENTS.md #33 concurrent-maintainer work. `examples/fakeshop/db.sqlite3` = test artifact. `types/converters.py` itself byte-unchanged → "Files touched: None" holds.

### Changelog verification
`git diff -- CHANGELOG.md` empty. `Not warranted` cites both AGENTS.md #21 and active-plan silence. No source/public-API/typed-error change — internal-only framing accurate.

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the `types/converters.py` checklist box in `docs/review/review-0_0_9.md`.

---

## Iteration log
