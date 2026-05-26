# Review: `django_strawberry_framework/types/converters.py`

Status: verified

## DRY analysis

- Defer until a third postgres-soft-import lands (no current spec home): generalize the `_resolve_array_field` / `_resolve_hstore_field` pair (`converters.py:87-110`) through a single `_resolve_postgres_field(symbol_name: str) -> type[models.Field] | None` helper. Two call sites with explicit names today give test-side `monkeypatch.setattr(converters, "_ARRAY_FIELD_CLS", ...)` / `..._HSTORE_FIELD_CLS` a stable name to bind, so the explicit pair is correct at N=2; act when the third soft-import target (e.g. `RangeField`, `CICharField`) gains a converter branch.

## High:

None.

## Medium:

### GLOSSARY drift: shipped scalar list claims `DurationField` and `BinaryField` are mapped

`docs/GLOSSARY.md:902` lists "date / datetime / time / **duration** fields → Python-native time types" and `docs/GLOSSARY.md:904` lists "**binary fields → `bytes`**" under the [Scalar field conversion] *shipped* mapping table. The implementation does the opposite — `DurationField` and `BinaryField` are **intentionally absent** from `SCALAR_MAP` (`converters.py:54-81`); the module docstring at `converters.py:27-31` explicitly names them as the documented non-default cases, and `tests/types/test_converters.py:408-448` pins that both raise `Unsupported Django field type` at type-creation time. Worker-1 memory pattern "GLOSSARY-quoted spec contracts" applies: the GLOSSARY is the public spec consumers grep against, and "shipped (`0.0.1`+)" framing makes any consumer reading line 902 reasonably expect `models.DurationField()` to resolve to `datetime.timedelta`. Recommended change — replace the two bullets:

```
- date / datetime / time fields → Python-native time types (note: ``DurationField`` is intentionally absent from the default map because Strawberry has no first-party scalar for ``datetime.timedelta``; register a custom scalar via ``SCALAR_MAP[DurationField] = MyDurationScalar``)
- UUID fields → `uuid.UUID`
- ``BinaryField`` is intentionally absent from the default map (no first-party Strawberry scalar for ``bytes``); the conventional plug is ``SCALAR_MAP[BinaryField] = strawberry.scalars.Base64``
```

Same wording as the module docstring at `converters.py:27-31` so the GLOSSARY and the source narrative converge on a single phrasing. No source edit needed in this file; the canonical resolution site is `docs/GLOSSARY.md:902-904`.

## Low:

### Sanitization ordering: `True` / `False` capitalized values keyword-prefix BEFORE reserved-name guard

`_sanitize_member_name` at `converters.py:221-241` runs the Python-keyword guard at L237-238 before the GraphQL-reserved-name guard at L239-240. A value `"True"` is a Python keyword, so it becomes `"_True"` at L238 and then L239's `casefold()` lookup against `frozenset({"false", "null", "true"})` does **not** match (the `_` prefix prevents it). End state: `"_True"` — which IS a safe GraphQL enum member (Strawberry tolerates `_True`), so this is cosmetic, not a correctness bug. But the docstring at L228-232 says "GraphQL-reserved enum values (`true`, `false`, `null`) … are also prefixed so Strawberry can build the schema" — a consumer reading the docstring would reasonably expect `"True"` (one of the three reserved-name shapes after `casefold()`) to produce `MEMBER_True`, not `_True`. Two equally-valid resolutions: (a) tighten the docstring to say "values that casefold to the reserved set on the post-keyword-mangling form are prefixed", or (b) reorder L237-240 so the reserved guard runs first against the raw sanitized form. Option (b) costs one swap and changes the output for `"True"` / `"False"` / `"Null"` from `_True` / `_False` / `_Null` to `MEMBER_True` / `MEMBER_False` / `MEMBER_Null`, which is a consumer-visible schema shift; deferring to the docstring tweak is the lower-risk fix. Defer until the next consumer report; no current evidence the wire-format drift bites in practice.

### `_resolve_postgres_field` helper signature deferred-trigger restated

Restating the prior-cycle DRY trigger verbatim (per worker-1 memory pattern "Unchanged-file releases. … restate the prior cycle's deferred forwards explicitly"): when the third postgres-contrib soft-import lands (`RangeField` / `CICharField` / etc.), collapse `_resolve_array_field` (`converters.py:87-97`) + `_resolve_hstore_field` (`converters.py:100-110`) + the new third through a single `_resolve_postgres_field(symbol_name)` helper plus three module-level sentinel constants. The explicit pair stays correct at N=2 because tests still need `_ARRAY_FIELD_CLS` / `_HSTORE_FIELD_CLS` as stable monkey-patch targets — the generalization must preserve the module-level constant names, not just the resolver function.

### `convert_relation` task-context naming vs `resolved_relation_annotation` public surface

Worker 0's task prompt names the relation helper `convert_relation`; the file exports only `resolved_relation_annotation` (`converters.py:315-327`). The prior 0.0.6 artifact's `### DRY recap` (carried into this artifact's recap below) also used the `convert_relation` name. The historical name appears to have been renamed to `resolved_relation_annotation`; no live `convert_relation` symbol exists in `django_strawberry_framework/` or `tests/` (grep returns one comment hit at `tests/types/test_base.py:525` referring to the conceptual operation). Recommended: do not chase the rename through every artifact, but treat the task-prompt name as the conceptual contract and the public symbol as the implementation. Defer; no action unless a future cycle re-introduces a separate `convert_relation` symbol.

## What looks solid

### DRY recap

- **Existing patterns reused.** `convert_scalar` raises `ConfigurationError` from `..exceptions` (the canonical error type — see `rev-exceptions.md`); `_resolve_array_field` / `_resolve_hstore_field` follow the soft-import + module-level sentinel idiom (`converters.py:87-114`). `convert_choices_to_enum` uses `pascal_case` from `..utils.strings` for the enum name (`converters.py:292`) and threads the `(model, field_name)` cache through `registry.get_enum` / `register_enum` at `registry.py:358-393`. `resolved_relation_annotation` delegates cardinality classification to `FieldMeta.from_django_field` (`optimizer/field_meta.py:114-163`) so the relation-shape rule is single-sited; `finalize_django_types()` at `types/finalizer.py` re-uses `resolved_relation_annotation` to write back the resolved annotation, keeping the production rewrite-path and the public test surface in sync.
- **New helpers considered.** `_field_label(field) -> str` for `f"{field.model.__name__}.{field.name}"` (repeats at `converters.py:172`, `176-178`, `190-193`, `210-211`, `268-270`, `282-285`, `306-307`) — rejected because each substring is locally formatted into a longer custom message and tests grep on the message body; collapsing would inflate the diff without changing consumer-visible shape. Folder-pass candidate when paired with the three sibling formatters carried forward from `rev-types__base.md`. `_resolve_postgres_field` helper deferred-with-trigger as the single DRY analysis bullet.
- **Duplication risk in the current file.** Two intentional near-copies: (1) `converters.py:174-179` (ArrayField outer-choices reject) vs `converters.py:188-194` (HStoreField outer-choices reject) — both gate `field.choices` and raise a near-parallel `ConfigurationError`, but the bodies differ enough that collapsing through a shared helper would lose the per-branch wording (the ArrayField message names `base_field` and `FilterSet` as recourse; the HStoreField message names the `dict[str, str | None]` shape rationale). (2) The `field.null` post-widening pattern (`return result | None if field.null else result` at L182, `return py_type | None if field.null else py_type` at L196, `if field.null: py_type = py_type | None` at L216-217) appears three times in `convert_scalar`; collapsing is not worth the readability hit because the surrounding context differs (recursive inner, sentinel return, MRO-walked py_type), and the imperative form at L216 is structurally required because it follows the choice substitution at L214-215.

### Other positives

- Static helper ran cleanly (328 lines, two hotspots at `convert_scalar` and `convert_choices_to_enum`, both adequately documented; zero repeated literals ≥ 8 chars; zero TODOs). Both hotspots are well-pinned: `tests/types/test_converters.py` covers every branch — ArrayField nested / outer-choices / inner-null / outer-null / unsupported-base / sentinel-none, HStoreField outer-choices / sentinel-none / serializer-roundtrip, BigInt mapping for `BigIntegerField` + `PositiveBigIntegerField` + `BigAutoField`-stays-Int, JSON for `JSONField`, choice grouped-form / sanitize-collision / keyword-prefix-collision / reserved-name-collision / null-widening, MRO subclass resolution with and without null, intentional `DurationField` / `BinaryField` rejection.
- `SCALAR_MAP` ordering is correct (`converters.py:54-81`): `AutoField` / `BigAutoField` / `SmallAutoField` precede the generic `IntegerField` family so the dict-lookup ordering doesn't matter (`__mro__` walk is explicit), and `BigIntegerField` / `PositiveBigIntegerField` map to `BigInt` per the spec-015 carry-forward from `rev-scalars.md`. `BigInt` imported once from `..scalars` at L51 and consumed at exactly L66 + L70 — no parallel `strawberry.scalar(...)` calls leaked into this module.
- Sentinel-guarded `ArrayField` / `HStoreField` dispatch runs BEFORE the MRO walk at L169 / L187 — the comment block at L163-168 explicitly calls out the test-double bypass risk that the ordering defends against. The `_ARRAY_FIELD_CLS is not None` / `_HSTORE_FIELD_CLS is not None` short-circuit pattern is symmetric and pinned by `test_array_field_sentinel_none_path` (`tests/types/test_converters.py:1194-1215`) / `test_hstore_field_sentinel_none_path` (`tests/types/test_converters.py:1454-1475`).
- Sanitization detects post-rewriting collisions via the explicit `collisions` dict accumulation (`converters.py:294-308`), raising `ConfigurationError` rather than letting the dict comprehension silently drop one value — pinned by three test shapes: hyphen-vs-underscore at `test_converters.py:282-300`, keyword-prefix at `test_converters.py:303-320`, and GraphQL-reserved-prefix at `test_converters.py:323-334`. This is exactly the Medium fix described in the prior 0.0.6 artifact's High section.
- The `convert_choices_to_enum` cache contract — first `DjangoType` to read `(model, field_name)` wins the enum name; sibling types reuse the cached object — is pinned by `test_two_djangotypes_reading_same_choice_field_share_one_enum` (`test_converters.py:147-172`), and the cache key shape is the `(field.model, field.name)` tuple, matching `registry.py:47`'s `_enums: dict[tuple[type[models.Model], str], type[Enum]]`.
- `resolved_relation_annotation` is a four-line cardinality router (`converters.py:315-327`) that defers entirely to `FieldMeta.is_many_side` / `FieldMeta.nullable`; the `field_meta=None` keyword-only parameter lets the deferred-resolution path in `types/finalizer.py` thread a pre-computed `FieldMeta` snapshot through without re-running `from_django_field`, which is the canonical single-site for relation cardinality.

### Summary

`converters.py` is unchanged between 0.0.6 and 0.0.7; the prior cycle verified High-severity correctness, sanitization-collision detection, MRO subclass walk, and SCALAR_MAP ordering. This re-pass surfaces one Medium GLOSSARY drift (lines 902, 904 list `DurationField` / `BinaryField` under shipped Scalar field conversion, contradicting both the module docstring and the `Unsupported Django field type` test pins) and three trigger-gated Lows (docstring-vs-implementation ordering note on capitalized Python-keyword reserved-name values; the deferred postgres-soft-import helper restated verbatim per the unchanged-file-release pattern; the historical `convert_relation` naming preserved for task-prompt continuity). The DRY analysis carries one act-now-deferred candidate; the recap restates the prior cycle's pattern reuse without re-finding any defect, per worker-1 memory rule on unchanged-file releases.

---

## Fix report (Worker 2)

Consolidated single-spawn — Medium 1 is a GLOSSARY-only drift fix with no source-code surface; L1-L3 are all explicitly forward-looking per Worker 1's own prose ("Defer until the next consumer report", "Restating the prior-cycle DRY trigger verbatim", "Defer; no action unless a future cycle re-introduces…"). Qualifies under the consolidated-single-spawn shape (artifact's only in-cycle edit is the GLOSSARY drift fix; no `converters.py` change required).

### Files touched
- `docs/GLOSSARY.md:902-904` — replaced the two drifted bullets verbatim per Worker 1's recommended-change block at rev-types__converters.md:19-23. Now matches the module docstring at `django_strawberry_framework/types/converters.py:27-31` and the `Unsupported Django field type` pins at `tests/types/test_converters.py:408-448`.

### Tests added or updated
None — GLOSSARY-only edit; the `DurationField`/`BinaryField` rejection contract is already pinned at `tests/types/test_converters.py:408-448` per the artifact.

### Validation run
- `uv run ruff format .` — pass (118 files left unchanged)
- `uv run ruff check --fix .` — pass (All checks passed)
- No focused test run (GLOSSARY-only edit; per AGENTS.md "Do not run pytest after edits").

### Notes for Worker 3
- No shadow file consulted — the recommended-change block in the artifact was self-contained and verbatim.
- Intentionally-rejected findings: none. All three Lows are explicitly forward-looking per Worker 1's own prose:
  - L1 (sanitization ordering): Worker 1 self-recommends "deferring to the docstring tweak is the lower-risk fix. Defer until the next consumer report; no current evidence the wire-format drift bites in practice." (rev-types__converters.md:31)
  - L2 (`_resolve_postgres_field` helper): Worker 1 self-recommends restating-verbatim per the unchanged-file-release pattern, with trigger "when the third postgres-contrib soft-import lands (`RangeField` / `CICharField` / etc.)" (rev-types__converters.md:35); preserves `_ARRAY_FIELD_CLS` / `_HSTORE_FIELD_CLS` constant names as stable monkey-patch targets.
  - L3 (`convert_relation` task-context naming): Worker 1 self-recommends "Defer; no action unless a future cycle re-introduces a separate `convert_relation` symbol." (rev-types__converters.md:39)
- Deferred findings and trigger conditions are restated verbatim under each Low in the per-finding dispositions below.

---

## Comment/docstring pass

Consolidated into this same spawn — M1 is a GLOSSARY-only fix (no `converters.py` source edit); the comment/docstring contract on `converters.py:27-31` already names `DurationField` and `BinaryField` as the documented non-default cases and the GLOSSARY edit converges on that same phrasing. No `converters.py` docstring edit needed; the source narrative was already correct and the GLOSSARY now matches it.

### Files touched
None — comment/docstring pass is structurally a no-op because M1's fix surface is `docs/GLOSSARY.md`, not `converters.py`. The `converters.py:27-31` module docstring was the canonical source of phrasing for the M1 edit; no further docstring change is warranted.

### Per-finding dispositions
- Medium 1 (GLOSSARY drift): logic-pass landed the GLOSSARY edit; comment pass is a no-op because the source-side docstring (`converters.py:27-31`) was already correct and the artifact explicitly states the canonical resolution site is `docs/GLOSSARY.md:902-904` not the source file (rev-types__converters.md:25).
- Low 1 (sanitization ordering): no edit — Worker 1 self-recommends "deferring to the docstring tweak is the lower-risk fix. Defer until the next consumer report; no current evidence the wire-format drift bites in practice." (rev-types__converters.md:31). Trigger: next consumer report of `_True` / `_False` / `_Null` member name drift, OR consumer evidence that the wire-format drift bites in practice; at that point either tighten the `_sanitize_member_name` docstring at `converters.py:228-232` to say "values that casefold to the reserved set on the post-keyword-mangling form are prefixed", OR reorder L237-240 so the reserved guard runs first against the raw sanitized form (changes `_True`/`_False`/`_Null` to `MEMBER_True`/`MEMBER_False`/`MEMBER_Null` — consumer-visible schema shift, requires release-note coordination).
- Low 2 (`_resolve_postgres_field` helper): no edit — Worker 1 self-recommends restating verbatim per the unchanged-file-release pattern (rev-types__converters.md:35). Trigger verbatim: "when the third postgres-contrib soft-import lands (`RangeField` / `CICharField` / etc.), collapse `_resolve_array_field` (`converters.py:87-97`) + `_resolve_hstore_field` (`converters.py:100-110`) + the new third through a single `_resolve_postgres_field(symbol_name)` helper plus three module-level sentinel constants. The explicit pair stays correct at N=2 because tests still need `_ARRAY_FIELD_CLS` / `_HSTORE_FIELD_CLS` as stable monkey-patch targets — the generalization must preserve the module-level constant names, not just the resolver function."
- Low 3 (`convert_relation` naming): no edit — Worker 1 self-recommends "Defer; no action unless a future cycle re-introduces a separate `convert_relation` symbol." (rev-types__converters.md:39). Trigger: future cycle re-introduces a separate `convert_relation` symbol distinct from `resolved_relation_annotation`. Conceptual contract stays the task-prompt name; implementation symbol stays `resolved_relation_annotation` per `converters.py:315-327`.

### Validation run
- `uv run ruff format .` — pass (118 files left unchanged)
- `uv run ruff check --fix .` — pass (All checks passed)

### Notes for Worker 3
All three Lows are explicitly forward-looking with Worker 1's own self-assessment language; trigger phrases above are verbatim from Worker 1's prose. The M1 fix surface is `docs/GLOSSARY.md:902-904` only; `converters.py` is untouched this cycle per the artifact's explicit "No source edit needed in this file; the canonical resolution site is `docs/GLOSSARY.md:902-904`" (rev-types__converters.md:25).

---

## Changelog disposition

### State
Not warranted.

### Reason
Cite BOTH:

- `AGENTS.md` ("Do not update CHANGELOG.md unless explicitly instructed"), AND
- the active plan `docs/review/review-0_0_7.md` does not authorize a CHANGELOG edit for cycle 21 (rev-types__converters.md); the dispatch prompt for this spawn also does not authorize one.

Additionally, the chain depth is now twenty-one consecutive cycles closing `Not warranted` across the 0.0.7 release — the precedent chain itself reinforces the AGENTS.md rule for zero-source-edit consolidated spawns. This cycle's only edit is a GLOSSARY drift correction (documentation-only), which is internal documentation alignment and not a consumer-visible behaviour change.

### What was done
No `CHANGELOG.md` edit. The GLOSSARY edit at `docs/GLOSSARY.md:902-904` aligns documentation with already-shipped behaviour (`DurationField` and `BinaryField` have been intentionally absent from `SCALAR_MAP` since 0.0.1+ per `tests/types/test_converters.py:408-448`); the GLOSSARY drift was the documentation-side bug, not a behaviour change.

### Validation run
- `uv run ruff format .` — pass (118 files left unchanged)
- `uv run ruff check --fix .` — pass (All checks passed)

---

## Verification (Worker 3)

### Logic verification outcome
- M1 (GLOSSARY drift, lines 902-904): verified. `git diff -- docs/GLOSSARY.md` shows the two bullets replaced verbatim per the artifact's recommended-change block at lines 19-23 — `date/datetime/time` bullet now carries the `DurationField` intentionally-absent note with the `SCALAR_MAP[DurationField] = MyDurationScalar` plug; the `binary fields → bytes` bullet replaced with the `BinaryField` intentionally-absent note plus `SCALAR_MAP[BinaryField] = strawberry.scalars.Base64` plug. Converges on the `converters.py:27-31` module docstring phrasing. Out-of-scope GLOSSARY hunks at lines ~668 (registry primary-collision message wording) and ~1000 (`_django_patches` SimpleTestCase prose) are attributable to prior verified cycles (cycle 6 registry, cycle 1 `_django_patches`) per AGENTS.md "Unexpected file modifications ... ignore them as out-of-scope".
- L1 (sanitization ordering): verbatim trigger preserved at fix-report disposition line 98 — "next consumer report of `_True` / `_False` / `_Null` member name drift, OR consumer evidence that the wire-format drift bites in practice" with both resolution arms (docstring tighten at L228-232 OR L237-240 reorder) named. Multi-arm disjunctive preserved.
- L2 (`_resolve_postgres_field` helper restatement): verbatim trigger preserved at fix-report disposition line 99 — "when the third postgres-contrib soft-import lands (`RangeField` / `CICharField` / etc.)" with the `_ARRAY_FIELD_CLS` / `_HSTORE_FIELD_CLS` monkey-patch-target preservation constraint intact.
- L3 (`convert_relation` naming): verbatim trigger preserved at fix-report disposition line 100 — "future cycle re-introduces a separate `convert_relation` symbol distinct from `resolved_relation_annotation`". Conceptual-vs-implementation framing maintained.

### DRY findings disposition
Single DRY bullet (`_resolve_postgres_field` helper at N=3) restated verbatim in L2 disposition. Act-on-third-postgres-soft-import trigger carries forward unchanged.

### Temp test verification
- None used. GLOSSARY-only edit; existing pins at `tests/types/test_converters.py:408-448` cover the `DurationField`/`BinaryField` rejection contract.

### Verification outcome
cycle accepted; verified

### Changelog verification
`git diff -- CHANGELOG.md` empty. Disposition cites both AGENTS.md ("Do not update CHANGELOG.md unless explicitly instructed") AND active plan silence (review-0_0_7.md does not authorize a CHANGELOG edit for cycle 21). Twenty-one-cycle precedent chain reinforces. Internal-only framing honest — GLOSSARY drift correction is documentation alignment with already-shipped behavior (`DurationField`/`BinaryField` absent from `SCALAR_MAP` since 0.0.1+).

### Ruff
Worker 2's logic-pass + comment-pass + changelog-pass each ran `uv run ruff format .` (118 files unchanged) and `uv run ruff check --fix .` (all checks passed). GLOSSARY-only edit; no Python source touched this cycle.

---

## Iteration log

_Append-only._
