# Feedback: `docs/spec-020-scalar_map_helper-0_0_7.md`

Rigorous review of the spec as of revision 3. Architectural direction is sound and the central Strawberry-source claim (no-warning `cls is None and name is not None` overload) is verified. Two **must-fix** errors and several smaller inconsistencies follow.

---

## Critical issues (must fix before implementation)

### C1. Test-migration count for `tests/types/test_converters.py` is wrong — 11 vs 10

**Locations:** [Slice 2 line 46](spec-020-scalar_map_helper-0_0_7.md#slice-checklist), [DoD item 6a](spec-020-scalar_map_helper-0_0_7.md#definition-of-done), [Slice 5 Done-body line 575](spec-020-scalar_map_helper-0_0_7.md#doc-updates).

The bullet says "11 schema-construction sites are migrated in this section" and then lists eleven test names, one of which is `test_big_auto_field_still_maps_to_int`. Immediately afterwards the same bullet states:

> "Schemas outside the BigInt section that do NOT involve a `BigInt` field (the `BigAutoField → ID`-mapping test and the JSONField / Choice-enum / Relation / Boolean tests in later sections) are NOT migrated"

`test_big_auto_field_still_maps_to_int` *is* the `BigAutoField → ID` test (verified in [tests/types/test_converters.py:615-644](../tests/types/test_converters.py) — `assert terminal["name"] == "Int"`). It lives inside the `# BigInt scalar — schema-execution field-mapping tests` banner (line 452-776) but maps to upstream `Int`, never touches `BigInt`, and therefore must NOT be migrated.

Correct count is **10** sites:

1. `test_big_integer_field_maps_to_bigint_in_schema`
2. `test_big_integer_field_nullable_in_schema`
3. `test_positive_big_integer_field_maps_to_bigint_in_schema`
4. `test_bigint_serializes_query_result_as_string_via_schema_execution`
5. `test_bigint_parses_string_argument_via_schema_execution`
6. `test_bigint_parses_int_argument_via_schema_execution`
7. `test_bigint_in_input_position_with_null_via_schema_execution`
8. `test_bigint_rejects_bool_argument_via_schema_execution`
9. `test_bigint_rejects_float_argument_via_schema_execution`
10. `test_bigint_resolver_returning_bool_raises_via_schema_execution`

`test_big_auto_field_still_maps_to_int` must be removed from the migration list and the count updated to 10 in Slice 2, DoD 6a, and the Slice 5 Done-body (which currently says "the BigInt-section schemas migrate to `config=strawberry_config()`" — fine if the section is interpreted as "BigInt-using schemas in the section").

### C2. `__all__` ordering is not alphabetical under any standard sort

**Locations:** [Slice 1 line 40](spec-020-scalar_map_helper-0_0_7.md#slice-checklist), [Edge cases line 444](spec-020-scalar_map_helper-0_0_7.md#edge-cases-and-constraints), [Test plan / DoD item 6](spec-020-scalar_map_helper-0_0_7.md#test-plan), [Doc updates GLOSSARY Public exports line 510](spec-020-scalar_map_helper-0_0_7.md#doc-updates).

The spec pins the new tuple as:

```python
("BigInt", "DjangoListField", "DjangoOptimizerExtension", "DjangoType",
 "OptimizerHint", "strawberry_config", "__version__", "auto", "finalize_django_types")
```

and calls the placement "between `OptimizerHint` and `__version__` alphabetically."

The existing tuple in [django_strawberry_framework/__init__.py:28-37](../django_strawberry_framework/__init__.py) is sorted by Python's default `sorted()` (ASCII case-sensitive): uppercase letters (66–90) → underscore (95) → lowercase letters (97–122). Under that ordering:

- `OptimizerHint` → `O` = 79
- `__version__` → `_` = 95
- `auto` → `a` = 97
- `finalize_django_types` → `f` = 102
- `strawberry_config` → `s` = **115**

`s` (115) > `f` (102), so `strawberry_config` belongs at the **end** of the tuple, after `finalize_django_types`, not between `OptimizerHint` and `__version__`. The spec's stated placement is unsorted under both `sorted(...)` and `sorted(..., key=str.casefold)`.

Correct edits:

- `__init__.py`: `__all__` tuple ends `..., "auto", "finalize_django_types", "strawberry_config")`.
- `tests/base/test_init.py`: same — `"strawberry_config"` is appended as the ninth element, not inserted between `"OptimizerHint"` and `"__version__"`.

(Note: the **GLOSSARY** `## strawberry_config` heading placement between `Specialized scalar conversions` and `Strictness mode` *is* correct — the GLOSSARY uses case-insensitive alphabetical, under which `specialized < strawberry_config < strictness`. The mistake is specific to `__all__`, which uses a different sort convention.)

---

## Notable inconsistencies

### N1. Two integration tests in `tests/test_scalars.py` largely duplicate `tests/types/test_converters.py` coverage post-Slice-2

The two integration tests added in Slice 2 (`test_bigint_serializes_int_via_strawberry_config_schema`, `test_bigint_parses_decimal_string_via_strawberry_config_schema`) construct `strawberry.Schema(query=Q, config=strawberry_config())` and assert the BigInt round-trip — but [Slice 2 line 46](spec-020-scalar_map_helper-0_0_7.md#slice-checklist) *also* migrates `tests/types/test_converters.py`'s `test_bigint_serializes_query_result_as_string_via_schema_execution` and `test_bigint_parses_string_argument_via_schema_execution` to use `config=strawberry_config()`. Once that migration lands, the integration tests in `tests/test_scalars.py` cover the same registration-path regression surface.

[Decision 7 line 373](spec-020-scalar_map_helper-0_0_7.md#decision-7--test-placement-and-shape) justifies the duplication as "a regression at the schema-construction layer is caught before the fakeshop tree runs," but the converter tests run in the same pytest invocation and would catch the same regression. The duplication is not harmful (cheap, well-localized), but the rationale should be revised. Either:

- Acknowledge the redundancy and keep both as defense-in-depth (current behavior, just say it plainly), or
- Drop the two integration tests from `tests/test_scalars.py` and rely on the migrated converter tests, dropping the count from 15 → 13.

### N2. Slice 1 bullet does not enumerate the new imports

[Slice 1 line 39](spec-020-scalar_map_helper-0_0_7.md#slice-checklist) describes the helper but does not call out that `scalars.py` must add three new imports:

```python
from collections.abc import Mapping
from strawberry.schema.config import StrawberryConfig
from strawberry.types.scalar import ScalarDefinition
```

The pinned shape at [Decision 3 lines 255-260](spec-020-scalar_map_helper-0_0_7.md#decision-3--bigint-redefinition-as-bare-newtype--scalardefinition) shows them, so the implementer can derive them, but for a spec this prescriptive it's worth listing them as an explicit step. Same for `from typing import Any` — already present in `scalars.py:15` but the spec's snippet imports it again, which would be a duplicate. The Slice 1 bullet should also note that `import warnings` is dropped *and* `from typing import Any, NewType` stays as-is.

### N3. Slice 5 KANBAN Done-body is unusually long

The past-tense body at [Doc updates line 575](spec-020-scalar_map_helper-0_0_7.md#doc-updates) is ~600 words — longer than most prior Done-bodies (compare `DONE-019-0.0.7`'s `Multi-database cooperation` note in [CHANGELOG.md:35](../CHANGELOG.md), which is one paragraph). For an alpha repo where KANBAN is read frequently, consider tightening to:

1. one-sentence outcome,
2. consumer migration snippet,
3. breaking-change callout,
4. cross-links (spec, GLOSSARY, related cards).

Not a correctness issue but the long form drowns the actually load-bearing facts.

### N4. The error message format in [Decision 4](spec-020-scalar_map_helper-0_0_7.md#decision-4--conflict-resolution-for-extra_scalar_map-collisions) uses `getattr(k, '__name__', repr(k))`

`NewType` instances expose `__name__`, so the `BigInt` collision case prints `"BigInt"` cleanly. Plain `type` keys also expose `__name__`. The `repr(k)` fallback only triggers for a key that is neither a class nor a `NewType` — an unusual but legal value per Strawberry's `Mapping[object, ScalarDefinition]` contract. The test `test_strawberry_config_collision_with_package_scalar_raises_value_error` only exercises the `NewType` path. If the spec wants the fallback to be load-bearing it should add a third assertion using a non-named key (e.g., an integer or string key); otherwise note that the fallback is defensive-only.

### N5. `parse_value=str` test snippet relies on Strawberry's `Callable | None` default

The test snippets `strawberry.scalar(name="CustomScalar", serialize=str, parse_value=str)` and `strawberry.scalar(name="AltBigInt", serialize=str, parse_value=int)` work against the verified overload at [.venv/.../strawberry/types/scalar.py:121-132](../.venv/lib/python3.10/site-packages/strawberry/types/scalar.py). Fine, but note that if `parse_value` is omitted (defaults to `None` on this overload — unlike the `cls`-passing branch which falls back to `parse_value = cls`), a `ScalarDefinition.parse_value=None` slips through and Strawberry will explode at schema-execution time on input. The factory does not check; that's defensible (Strawberry owns the contract), but the spec could mention this asymmetry between the two overloads as part of [Edge cases](spec-020-scalar_map_helper-0_0_7.md#edge-cases-and-constraints).

---

## Smaller observations

### S1. `_BIGINT_SCALAR_DEFINITION` is private — but the schema construction path needs to look it up

The map is keyed by the bare `NewType("BigInt", int)`. When a consumer writes `id: BigInt` in their resolver, Strawberry consults `StrawberryConfig.scalar_map[BigInt]` to resolve the type. That key identity is `BigInt` — the same `NewType` object exported from `django_strawberry_framework`. The spec correctly handles this (the public `BigInt` symbol and the dict key are the same object). Verified correct, just calling out that this is the load-bearing invariant: **the exported `BigInt` and the `_PACKAGE_SCALAR_MAP` key must be the same object**, not two distinct `NewType` constructions.

### S2. `_unsafe_disable_same_type_validation` is a real `StrawberryConfig` field

[StrawberryConfig source at .venv/.../strawberry/schema/config.py:47](../.venv/lib/python3.10/site-packages/strawberry/schema/config.py) declares `_unsafe_disable_same_type_validation: bool = False` — a (private-leading-underscore) dataclass field that *is* a valid kwarg. The spec's `**config_kwargs` passthrough will silently accept it. Probably fine — the helper doesn't have to enumerate every Strawberry field — but worth a one-line note in [Edge cases](spec-020-scalar_map_helper-0_0_7.md#edge-cases-and-constraints) that underscore-prefixed Strawberry kwargs pass through unchanged.

### S3. Risk #6 ("Strawberry version pin compatibility") doesn't quote `pyproject.toml`

The constraint is [`strawberry-graphql>=0.262.0`](../pyproject.toml) (line 30). The spec should quote the actual line so a future change to the constraint is grep-discoverable from the risk callout.

### S4. The "Note (terms CSV completeness)" callout in [Key glossary references](spec-020-scalar_map_helper-0_0_7.md#key-glossary-references) is self-referential

The callout says `strawberry_config` is deliberately omitted from the CSV "until [Slice 4 lands]" and then says the callout itself is removed in Slice 4. That's fine while the spec is being authored, but a future reader stumbling onto the spec post-merge will be confused by the half-removed self-reference. Consider re-phrasing to "CSV completeness note — removed when Slice 4 lands; left here for the active spec only" or marking it explicitly as `(REMOVE IN SLICE 4)`.

### S5. Slice 4 `docs/README.md` "Wrong order" anti-example update

[Line 137 and 143 of docs/README.md](../docs/README.md) carry two `strawberry.Schema(query=Query, extensions=[DjangoOptimizerExtension()])` lines (the "Wrong order" and "Right order" examples). The spec says to update the anti-example so the contrast still illustrates finalize-order — but if both lines get `config=strawberry_config()` added in the same shape, then the only difference between the two examples is the position of `finalize_django_types()`. That's the intent, but be explicit: both lines change identically and the only contrast is the placement of `finalize_django_types()` relative to `strawberry.Schema(...)`.

---

## Verified correct (sample)

- **Strawberry no-warning overload**: [.venv/.../strawberry/types/scalar.py:121-132](../.venv/lib/python3.10/site-packages/strawberry/types/scalar.py) defines `scalar(cls: None = None, *, name: str, ...) -> ScalarDefinition`. The `cls is None and name is not None` branch at line 254 returns a `ScalarDefinition` directly. The `DeprecationWarning` lives in `wrap()` at line 274 and fires only when `cls is not None`. ✓
- **`auto_camel_case` is an `InitVar`**: [.venv/.../strawberry/schema/config.py:39, 51-56](../.venv/lib/python3.10/site-packages/strawberry/schema/config.py) confirms it's an `InitVar[bool] = None` that lands on `name_converter.auto_camel_case` via `__post_init__`. The spec's assertion target `result.name_converter.auto_camel_case` is correct, and `NameConverter.__init__` defaults `auto_camel_case=True` (verified at [.venv/.../strawberry/schema/name_converter.py:32-34](../.venv/lib/python3.10/site-packages/strawberry/schema/name_converter.py)), so the default-case assertion `is True` will hold.
- **GLOSSARY heading placement** between `Specialized scalar conversions` and `Strictness mode` matches the GLOSSARY's existing case-insensitive alphabetical convention. ✓
- **`import warnings` removable**: scalars.py imports `warnings` only for the suppression block at lines 92-97 — no other use. ✓
- **`[0.0.6]` "Migration to a `scalar_map`-based design" line**: confirmed at [CHANGELOG.md:78](../CHANGELOG.md). ✓
- **`[Unreleased]` currently has only `### Changed` and `### Fixed`**: confirmed at [CHANGELOG.md:19-26](../CHANGELOG.md). Adding `### Added` and `### Removed` is correct.
- **`examples/fakeshop` does not reference `BigInt`**: `grep -rn "BigInt" examples/fakeshop/` returns no matches. ✓
- **`test_big_auto_field_still_maps_to_int` maps to `Int`, not `BigInt`**: confirmed at [tests/types/test_converters.py:644](../tests/types/test_converters.py). ✓ (This is the same fact that makes C1 a counting error.)
- **CSV term count delta**: 16 → 17 after adding the `strawberry_config` row. ✓
- **KANBAN card status**: `WIP-ALPHA-020-0.0.7` is the only remaining `0.0.7` WIP per [KANBAN.md:50, 76](../KANBAN.md). ✓
- **CSV completeness check**: [scripts/check_spec_glossary.py](../scripts/check_spec_glossary.py) is the right script.
- **No-pytest-after-edits rule**: per AGENTS.md, worker-local validation is `uv run ruff format .` + `uv run ruff check --fix .`. Spec correctly defers pytest to CI.

---

## Summary

Two real corrections to land before implementation:

1. **C1** — drop `test_big_auto_field_still_maps_to_int` from the 11-test migration list; correct the count to 10 across Slice 2, DoD 6a, and the Slice 5 Done-body.
2. **C2** — fix `__all__` placement: `"strawberry_config"` goes at the **end** of the tuple (after `"finalize_django_types"`), not between `"OptimizerHint"` and `"__version__"`. Affects Slice 1 bullet, Edge case at line 444, DoD item 6, and the GLOSSARY Public exports re-ordering claim.

Plus a handful of N/S items above worth folding in. Once those are addressed, the spec is implementation-ready — the architectural direction (no-warning overload + `extra_scalar_map=` merge + `**config_kwargs` passthrough + hard-error collision policy) is sound, well-justified, and the cross-reference accounting is otherwise solid for a ~120-line code change.
