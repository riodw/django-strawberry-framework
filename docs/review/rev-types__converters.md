# Review: `django_strawberry_framework/types/converters.py`

Status: verified

## DRY analysis

- None — this module IS the single-source field-shape converter. `scalar_for_field` is already the one canonical field-class→scalar lookup, consumed by `convert_scalar` AND by the filter-input side via a deliberate LOCAL import (`filters/inputs.py:267` `from ..types.converters import scalar_for_field`), so the selected-field and filter-input sides resolve a column to the same scalar without a second map. The two soft-import helpers (`_resolve_array_field` / `_resolve_hstore_field`) are near-identical 4-line bodies but each names a DISTINCT field class and a distinct module-level sentinel (`_ARRAY_FIELD_CLS` / `_HSTORE_FIELD_CLS`); folding them through a parametrized `_resolve_postgres_field(name)` would trade two self-documenting one-liners for an indirection that obscures the import targets — net-negative at N=2. The four `f"... {field.model.__name__}.{field.name} ..."` error prefixes are distinct human messages (different rejection causes, different remediation), not a dispatch key — the shadow's "Repeated string literals: None" confirms no literal is shared even textually.

## High:

None.

## Medium:

None.

## Low:

### `_GRAPHQL_RESERVED_ENUM_VALUES` literal pinned to the GraphQL spec's three reserved names

`_GRAPHQL_RESERVED_ENUM_VALUES = frozenset({"false", "null", "true"})` (`converters.py` #"_GRAPHQL_RESERVED_ENUM_VALUES") is the verbatim set of enum values GraphQL forbids. The set is correct and complete against the current GraphQL spec; the casefold compare (`sanitized.casefold() in _GRAPHQL_RESERVED_ENUM_VALUES`) makes it case-insensitive, so `"TRUE"`/`"True"`-after-keyword-rewrite are handled. No defect today. Defer with trigger: "If a future GraphQL spec revision adds a fourth reserved literal, add it to this frozenset and a covering value to `tests/types/test_converters.py::test_choice_enum_with_graphql_reserved_and_non_ascii_values_builds_schema`." This is a standing-spec-tracking note, not an actionable change now.

### `resolved_relation_annotation` has a one-line docstring while its siblings carry full Args/Raises blocks

`resolved_relation_annotation` (`converters.py::resolved_relation_annotation`) documents only its summary line; the cardinality/null-widening contract (many-side → `list[target_type]`, nullable → `target_type | None`) lives only in the body and in the module docstring's "Public surface" bullet. Every other public function in the file carries an explicit algorithm/Args block. The body is three trivial branches sourced from `FieldMeta`, so the gap is low-impact, but a one-line note that `field_meta` defaults to `FieldMeta.from_django_field(field)` (the deferred-resolution reuse path named in the module docstring) would match the file's documentation bar. Comment-pass-tier polish only; defer to the next content edit touching this function.

## What looks solid

### DRY recap

- **Existing patterns reused.** `scalar_for_field` (`converters.py:119-139`) is the canonical field-class→scalar MRO-walk lookup; `filters/inputs.py:253-269` (`_scalar_from_model_field`) delegates to it via local import rather than re-mapping, so consumer-registered `SCALAR_MAP` entries are honored identically on both the selected-field and filter-input sides. `convert_scalar` reuses `convert_choices_to_enum` for the choice branch (`converters.py:262`) and `pascal_case` from `utils/strings` for enum naming (`converters.py:357`). Enum caching reuses the canonical `registry.get_enum` / `registry.register_enum` (`converters.py:353,377`) rather than a local dict.
- **New helpers considered.** Parametrized `_resolve_postgres_field(name)` folding the two soft-import helpers — rejected: the helpers name distinct classes/sentinels and reading the explicit import target is clearer than indirection at N=2. Shared null-widening helper (`x | None if effective_null else x` appears at four sites) — rejected: each site already collapses to a single readable ternary and `effective_null` is computed once at the top per the documented tri-state design; a helper would not shorten the call sites meaningfully and would hide the per-branch return shape.
- **Duplication risk in the current file.** The four `f"...{field.model.__name__}.{field.name}..."` error-message prefixes look like a near-copy but are intentional sibling messages — each states a different rejection cause (unsupported field / nested array / outer-array choices / HStore choices / grouped choices / collision) and a different remediation; consolidating to a shared prefix would force a generic message that loses the per-cause guidance.

### Other positives

- **Tri-state `force_nullable` is computed once and read uniformly.** `effective_null` is derived at the top of `convert_scalar` (`converters.py:218`) and every outer widening site (Array, HStore, scalar/choice) reads it, so an override flips nullability across all branches without per-branch logic — exactly as the docstring and GLOSSARY:784 promise.
- **Order-correctness is explicit and load-bearing.** Choice substitution runs BEFORE null widening so nullable choice fields become `EnumType | None` (not collapsed `str | None`); the ArrayField/HStoreField sentinel dispatch runs BEFORE the MRO walk so a `models.Field` test double can't accidentally match a parent in `SCALAR_MAP`. Both ordering decisions are documented inline.
- **Sanitization rules are ordered, documented, and unit-pinned.** `_sanitize_member_name`'s four-step rule order (ASCII rewrite → leading-digit/empty → keyword → reserved/`__`-prefix) is covered directly by `tests/types/test_converters.py::test_choice_member_name_sanitization` and end-to-end by `test_choice_enum_with_graphql_reserved_and_non_ascii_values_builds_schema` (reserved `true`/`FALSE`/`null`, non-ASCII, `__private` introspection prefix). Sanitizing the stored VALUE not the LABEL keeps the GraphQL contract stable against label edits — a real correctness property, tested.
- **Grouped-choices detection keys on the label slot, not the value slot.** `convert_choices_to_enum` checks `isinstance(label, (list, tuple))` (`converters.py:345`); the inline comment correctly explains that in the grouped form the value slot is the human group name (a string), so checking it would false-negative. Correct.
- **Postgres soft-imports keep package import working without the driver.** `_resolve_array_field` / `_resolve_hstore_field` return `None` on `ImportError` and the dispatch is sentinel-guarded (`is not None and isinstance(...)`), so the module imports cleanly on environments without `django.contrib.postgres`.
- **Collision detection reports all colliding values with sorted, deterministic output.** `convert_choices_to_enum` accumulates collisions and raises one `ConfigurationError` listing every offending member/value group sorted (`converters.py:366-374`) — deterministic message, actionable remediation.
- **GLOSSARY prose matches source.** Choice-enum generation (GLOSSARY:220-228), scalar conversion's `DurationField`/`BinaryField` intentional absences (GLOSSARY:1157-1159), the tri-state `force_nullable` (GLOSSARY:784), and the `convert_scalar`-bypass override semantics (GLOSSARY:1181) all read true against the current source. No drift.

### Summary

`converters.py` is a clean, single-responsibility field-shape converter: scalar mapping, choice→enum generation, postgres-array/hstore handling, and relation-annotation rendering, with all introspection kept here so `types/base.py` stays focused on Meta orchestration. It is unchanged since baseline `14910230` (empty `git log` and empty `git diff HEAD`), is not in the spec-035 changed set, carries zero ORM markers, and its reflective access (`isinstance` sentinel dispatch, `field.choices`/`field.model`/`field.name`/`base_field` reads) is all justified and documented. `scalar_for_field` is correctly the one shared lookup across the selected-field and filter-input sides. DRY=None is correct — this module is the consolidation point, not a duplicator. Two forward Lows (reserved-set spec-tracking note; one thin docstring), neither a current defect. No High or Medium. No-source-edit cycle (shape #5).

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — 270 files left unchanged.
- `uv run ruff check .` — All checks passed.

### Notes for Worker 3
- Low #1 (`_GRAPHQL_RESERVED_ENUM_VALUES` spec-tracking): forward-looking, trigger quoted verbatim ("If a future GraphQL spec revision adds a fourth reserved literal..."). Already complete+correct against the current GraphQL spec; covered by `tests/types/test_converters.py::test_choice_enum_with_graphql_reserved_and_non_ascii_values_builds_schema`. No edit.
- Low #2 (`resolved_relation_annotation` thin docstring): comment-pass-tier polish, deferred to next content edit on that function. No edit.
- No GLOSSARY-only fix in scope — GLOSSARY prose verified consistent (Choice enum generation, scalar conversion absences, `force_nullable` tri-state, `convert_scalar`-bypass). No drift to repair.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern.

No comment/docstring edits in scope. The two forward Lows are explicitly deferred (one spec-tracking, one to next content edit). The file's existing comments are accurate and load-bearing (tri-state collapse rationale, sentinel-before-MRO ordering, grouped-choices label-slot detection); none are stale or restating obvious code.

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern.

Not warranted — no source/test edits this cycle (review-only, file unchanged since baseline `14910230`). Per AGENTS.md #21 ("Do not update CHANGELOG.md unless explicitly instructed") and the active plan `docs/review/review-0_0_10.md` carrying no changelog directive for this item.

---

## Verification (Worker 3)

Shadow-file caveat applied: the stripped overview (`docs/shadow/django_strawberry_framework__types__converters.overview.md`) strips comments and string literals, so its line numbers are non-canonical; original source line numbers / symbol-qualified refs are treated as canonical. Used the shadow only to confirm control flow (7 symbols, 2 hotspots `convert_scalar`/`convert_choices_to_enum`, 0 ORM markers, 0 repeated literals, 0 TODOs — all matching source).

### Logic verification outcome
Shape #5 no-source-edit cycle; no High/Medium/Low required a source change. Independently re-confirmed conversion correctness against live source:
- **Scalar mapping** — `scalar_for_field` (`converters.py::scalar_for_field`) is the sole field-class→scalar MRO walk; `grep "def scalar_for_field"` returns exactly one def. The filter-input side delegates via a LOCAL import (`filters/inputs.py:267` `from ..types.converters import scalar_for_field`, called at `:269`), so both sides resolve a column identically including consumer `SCALAR_MAP` entries. DRY=None confirmed: this is the consolidation point, not a duplicator.
- **Nullability** — `effective_null` computed once (`converters.py #"effective_null = field.null"`) from the `force_nullable` tri-state and read at all four outer widening sites (Array `:241`, HStore `:255`, scalar/choice `:263`). `force_nullable` provenance verified live: sourced from `Meta.nullable_overrides`/`required_overrides` in `types/base.py` (`:576-577`), exactly as the docstring claims. Recursive `base_field` call (`:239`) is left `force_nullable`-unset so inner-element null follows `base_field.null` — correct asymmetry.
- **`auto`/ordering** — choice substitution (`:262`) runs BEFORE null widening (`:263`) so nullable choice fields become `EnumType | None`, not collapsed `str | None`; ArrayField/HStoreField sentinel dispatch (`:228`,`:246`) runs BEFORE the MRO walk so a `models.Field` test double cannot match a `SCALAR_MAP` parent. Both orderings load-bearing and inline-documented.
- **TextChoices→enum generation** — `convert_choices_to_enum` keys grouped-choices detection on the LABEL slot (`isinstance(label, (list, tuple))`, `:345`), correct because in grouped form the value slot is the group name string. Member names sanitized from VALUES not labels (`_sanitize_member_name`, four-step ordered rule). Collision detection accumulates and raises one sorted deterministic message (`:366-374`). Enum caching reuses `registry.get_enum`/`register_enum` (`:353`,`:377`). Covered by `tests/types/test_converters.py::test_choice_member_name_sanitization` (`:197`) and `::test_choice_enum_with_graphql_reserved_and_non_ascii_values_builds_schema` (`:214`) — both grep-confirmed present.
- **`resolved_relation_annotation`** — three trivial branches sourced from `FieldMeta` (`is_many_side`→`list[target_type]`; `nullable`→`target_type | None`; else `target_type`), confirmed against `optimizer/field_meta.py` (`is_many_side` property `:134`, `nullable` field `:117` with cardinality-gated rule `:192-196`, `from_django_field` `:139`). Consumed by `types/finalizer.py:607` deferred-resolution path, matching the docstring's "reused by `types/finalizer.py`" claim.

**Low #1** (`_GRAPHQL_RESERVED_ENUM_VALUES` spec-tracking): genuinely forward-looking. The frozenset `{"false","null","true"}` (`:84-86`) is complete+correct against the current GraphQL spec; the casefold compare (`:296`) handles case variants. Trigger phrasing is in-artifact and verbatim-actionable. No current defect — confirmed.
**Low #2** (`resolved_relation_annotation` thin docstring): genuinely forward-looking comment-pass polish. The one-line summary vs siblings' Args/Raises blocks is a documentation-bar gap, not a behavior defect; the cardinality/null contract is fully stated in the module docstring's "Public surface" bullet (`:13-17`). Deferral to next content edit is sound.

### DRY findings disposition
DRY=None confirmed sound. `scalar_for_field` single-sourced (one def, filter side delegates). The two postgres soft-import helpers (`_resolve_array_field`/`_resolve_hstore_field`) name distinct classes/sentinels — folding to a parametrized helper is net-negative at N=2 (rejected correctly). The four `f"...{field.model.__name__}.{field.name}..."` prefixes are distinct human messages (shadow confirms "repeated string literals: None"), not a dispatch key.

### Temp test verification
- None — no behavior suspicion required a temp test; the no-source-edit shape was provable by diff + grep + ruff.
- Disposition: n/a.

### Shape #5 checklist
1. `git diff HEAD -- django_strawberry_framework/types/converters.py` empty; last-touch `e6389922` predates HEAD `58ca2def` (stale baseline `14910230` in artifact is cosmetic — content verified by grep, per content-not-identifier rule). Zero this-cycle edits.
2. All four Worker 2 sections open `Filled by Worker 1 per no-source-edit cycle pattern.` ✓
3. Both Lows have in-artifact trigger phrasing / deferral; no GLOSSARY-only fix in scope. ✓
4. Changelog `Not warranted` cites BOTH AGENTS.md #21 AND active-plan silence; `git diff HEAD -- CHANGELOG.md` empty. ✓ Internal-only framing honest (zero diff, no public-API change).
5. `uv run ruff format --check` (1 file already formatted) + `uv run ruff check` (All checks passed) on the target. ✓

Status preamble note: artifact opens with a bare `Status: fix-implemented` → terminal-verify per the dispatch table. Correct for a closing no-source-edit cycle.

### Verification outcome
- `cycle accepted; verified` — sets top-level `Status: verified` AND marks the checklist box.
