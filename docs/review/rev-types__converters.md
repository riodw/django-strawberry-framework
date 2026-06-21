# Review: `django_strawberry_framework/types/converters.py`

Status: verified

## DRY analysis

- **Defer-with-trigger: collapse the twin MRO-walk lookups `scalar_for_field` and `_field_output_type_for` onto a shared `_mro_lookup(field, table, default)` helper.** Both walk `type(field).__mro__` against a module-level `dict[type[models.Field], …]` (`scalar_for_field` at `converters.py::scalar_for_field` against `SCALAR_MAP`, `_field_output_type_for` at `converters.py::_field_output_type_for` against `FIELD_OUTPUT_TYPE_MAP`). The bodies differ only in the table and the miss behavior (`scalar_for_field` raises `ConfigurationError`; `_field_output_type_for` returns `None`), so a single `_mro_lookup` with a sentinel/`default` parameter would fold them. **Defer until a third `type(field).__mro__`-walked lookup table lands** (e.g. a dedicated relation-output or input-scalar map); at two sites the miss-semantics divergence (raise vs `None`) makes the shared helper carry a branch that costs more clarity than the seven-line duplication saves. Quote the trigger verbatim for the next DRY cycle: "a third `type(field).__mro__` lookup table is added to converters.py".

## High:

None.

## Medium:

None.

## Low:

### `_safe_file_attr` `self`-truthiness invariant rests on a sibling-module contract with no in-module assertion

Forward-looking only. `_safe_file_attr` (`converters.py::_safe_file_attr`) and every `DjangoFileType` / `DjangoImageType` subfield resolver assume `self` is a *truthy* bound `FieldFile` — the docstring states "always truthy here -- an empty file resolves the whole object to `None` before any subfield runs." That invariant is owned by `resolvers._make_file_resolver` (`types/resolvers.py::_make_file_resolver` #"return value if value else None"), a different module, and is enforced only there. Today this is correct and well-documented on both sides; the coupling is intentional (the guard deliberately lives per-subfield outside the parent resolver's reach, spec-037 Decision 4). No action now. **Defer until a second parent-resolver path can construct a `DjangoFileType` whose `self` is a falsy or non-`FieldFile` value** (e.g. a consumer-supplied custom file resolver bypassing `_make_file_resolver`); at that point the `name` resolver's direct `return self.name` and the unguarded `getattr` in `_safe_file_attr` would need a falsy-`self` defense. Until then the single-resolver invariant holds.

## What looks solid

### DRY recap

- **Existing patterns reused.** `_field_output_type_for` (`converters.py::_field_output_type_for`) is the single MRO-walk home for `FIELD_OUTPUT_TYPE_MAP`, consumed by `convert_field_output` (`converters.py::convert_field_output` #"output_type = _field_output_type_for(field)"), `resolvers._attach_file_resolvers` (`types/resolvers.py:488`), and `inspect_django_type` (`management/commands/inspect_django_type.py:302`) — the map walk is written once. `_safe_file_attr` is the single per-subfield storage guard reused by `path` / `size` / `url` on `DjangoFileType` and `width` / `height` on `DjangoImageType` (5 call sites, one body). `convert_field_output` is a thin router that delegates every non-file column to `convert_scalar` rather than re-deriving scalar logic. `convert_scalar` reuses `scalar_for_field` for the shared field-class→scalar lookup so the selected-field side and `filters/inputs._scalar_from_model_field` cannot drift.
- **New helpers considered.** `_mro_lookup` to fold `scalar_for_field` + `_field_output_type_for` — evaluated and deferred (see `## DRY analysis`; two sites with divergent miss-semantics). A shared "compute effective_null from tri-state" helper for `convert_scalar` (`effective_null = field.null if force_nullable is None else force_nullable`) and `convert_field_output` (`file_effective_null = True if force_nullable is None else force_nullable`) — rejected: the two differ in their `force_nullable is None` default (column `field.null` for scalars, hard `True` for file/image), which is the entire spec-037 Decision 4 distinction; a shared helper would have to parameterize the default and would obscure that the file/image branch is default-nullable-regardless-of-column. The one-line ternary at each site is clearer.
- **Duplication risk in the current file.** `DjangoImageType(DjangoFileType)` inherits `name` / `path` / `size` / `url` so the four shared subfields are defined once; `width` / `height` reuse `_safe_file_attr` verbatim — no copy. The two `_resolve_array_field` / `_resolve_hstore_field` soft-import helpers are near-identical but read intentionally as sibling postgres-field probes (different imported symbol, different module-level sentinel); folding them would need a string-keyed import indirection that costs more than it saves at two postgres fields. The `ImageField`-before-`FileField` ordering in `FIELD_OUTPUT_TYPE_MAP` mirrors the `PositiveBigIntegerField`-before-`IntegerField` ordering convention in `SCALAR_MAP` — intentional sibling design, documented inline.

### Other positives

- **`force_nullable` tri-state is correct and uniform.** `convert_scalar` collapses the tri-state to a single `effective_null` boolean read at every outer widening site (ArrayField `list[inner]`, HStoreField JSON, scalar, choice-enum), so an override flips the choice enum's nullability for free without per-branch override logic. `convert_field_output` threads the same `force_nullable` unchanged into `convert_scalar` for non-file columns, and for file/image computes `file_effective_null = True if force_nullable is None else force_nullable` — default-nullable, with `force_nullable=False` (`Meta.required_overrides`) the explicit non-null opt-in. Confirmed against `types/base._build_annotations` (`types/base.py:1651`), which swaps `convert_scalar` for `convert_field_output` and threads the override verbatim.
- **File/image read-output kept strictly off the filter-input path.** `SCALAR_MAP` keeps `FileField`/`ImageField` as `str` (with a load-bearing inline comment), and `FIELD_OUTPUT_TYPE_MAP` is a separate map consulted only by `_field_output_type_for` — never by `scalar_for_field`. A `FilterSet` over a file column yields a scalar `str` input and no output object can leak into a GraphQL input (spec-037 Decision 3). Verified: `grep` shows `scalar_for_field` walks only `SCALAR_MAP`, and `FIELD_OUTPUT_TYPE_MAP` has exactly two consumers, both on the read/diagnostic side.
- **`_safe_file_attr` catch list is correctly narrow.** Catches only `ValueError` / `OSError` / `NotImplementedError` (the storage-shaped errors), so `SuspiciousFileOperation` (a `SuspiciousOperation`, not a `ValueError`/`OSError`) propagates as a path-traversal security signal rather than degrading to a `null` subfield (spec-037 Decision 4). A broad `except Exception` would have swallowed genuine resolver bugs and the security signal — the narrow list is the right call.
- **Parent-resolver / subfield contract holds at source.** `_make_file_resolver` returns `None` for a falsy `FieldFile` (`return value if value else None`), so `_safe_file_attr`'s `self` is always a truthy bound `FieldFile` and `DjangoFileType.name`'s direct `return self.name` reads the `FieldFile.name` storage attribute (not the resolver method — no recursion). Both halves cross-checked.
- **Choice-enum generation is value-keyed and collision-safe.** `convert_choices_to_enum` sanitizes member names from choice *values* (not labels) so a label edit doesn't churn the schema, rejects empty/grouped choices with `ConfigurationError`, detects same-member collisions with a deterministic sorted error message, and caches via `registry.register_enum` keyed on `(field.model, field.name)` so sibling types share the enum. `_sanitize_member_name`'s four ordered rules (non-ident→`_`, leading-digit→`MEMBER_`, keyword→`_`, GraphQL-reserved/`__`→`MEMBER_`) are documented as order-load-bearing and the order is correct.
- **GLOSSARY is accurate, no drift.** `#djangofiletype` (line 330-336), `#djangoimagetype` (352-358), `#upload-scalar` (1361-1363), the scalar-conversion entries (1182-1185, 1206, 1261-1303), and `#metarequired_overrides` (894) all match the source: nullable-by-default-regardless-of-column, `name` non-null, `path`/`size`/`url`/`width`/`height` nullable & storage-safe via `_safe_file_attr`, `SuspiciousFileOperation` propagation, `ImageField`-precedes-`FileField` MRO precedence, `required_overrides` non-null opt-in, and file/image staying `str` on the filter/scalar-input side. Public symbols `DjangoFileType` / `DjangoImageType` are re-exported from the package root (`__init__.py:34,42-43`) and carry GLOSSARY contract entries; private symbols (`_safe_file_attr`, `_field_output_type_for`, `_sanitize_member_name`, the soft-import helpers) carry no entry — absence correct.

### Summary

`types/converters.py` is the Django-field→Strawberry-type conversion home and now carries the spec-037 file/image read-output surface. The cycle baseline (`f7bbb08571c41a269e0f5c65cd0aab452d382d35`) and `HEAD` diffs are both empty — the file/image work is fully cumulative in HEAD (last touch `7d39523b`, predating the baseline), and the prior artifact was `verified`. Full scrutiny of the new surface confirms the file/image objects are nullable-by-default in SDL regardless of column `null`/`blank`, `name` is non-null, `path`/`size`/`url`/`width`/`height` are nullable and storage-safe through the narrow-catch `_safe_file_attr` guard, the `ImageField`-before-`FileField` ordering resolves the MRO walk correctly, and the `force_nullable` tri-state is threaded uniformly. The read-output map is kept strictly off the shared `SCALAR_MAP`/filter-input path. No High, no Medium; one forward-looking Low (parent-resolver truthiness invariant) and one defer-with-trigger DRY candidate (twin MRO-walk lookups). Genuine no-source-edit cycle (shape #5).

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — `289 files left unchanged`.
- `uv run ruff check .` — `All checks passed!`.

### Notes for Worker 3
- No GLOSSARY-only fix in scope — GLOSSARY entries (`#djangofiletype`, `#djangoimagetype`, `#upload-scalar`, scalar-conversion entries, `#metarequired_overrides`) verified accurate, no drift.
- Low (parent-resolver `self`-truthiness invariant): forward-looking only, verbatim trigger recorded ("a second parent-resolver path can construct a `DjangoFileType` whose `self` is a falsy or non-`FieldFile` value"). Invariant currently enforced by `resolvers._make_file_resolver` (`return value if value else None`), cross-checked at source. No edit.
- DRY (twin MRO-walk lookups `scalar_for_field` / `_field_output_type_for`): defer-with-trigger ("a third `type(field).__mro__` lookup table is added to converters.py"). No edit.
- Both `git diff f7bbb08571c41a269e0f5c65cd0aab452d382d35 -- <target>` and `git diff HEAD -- <target>` empty; `git log baseline..HEAD -- <target>` returns nothing. The file/image surface is cumulative in HEAD.

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern. No comment or docstring edits — the module's docstrings and inline comments (SCALAR_MAP file/image rationale, FIELD_OUTPUT_TYPE_MAP ordering, effective_null tri-state, `_safe_file_attr` narrow-catch / security-signal note, spec-037 Decision references) are accurate against the source and the GLOSSARY. No stale TODOs (static overview: 0 TODOs).

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern. **Not warranted** — zero source/test/doc edits this cycle (`AGENTS.md`: "Do not update CHANGELOG.md unless explicitly instructed"; active plan `docs/review/review-0_0_11.md` is silent on changelog edits for review cycles).

---

## Verification (Worker 3)

### Logic verification outcome
Genuine shape #5 no-source-edit cycle, terminal-verify. Zero-edit proof holds: `git diff f7bbb08571c41a269e0f5c65cd0aab452d382d35 -- django_strawberry_framework/types/converters.py` empty, `git diff HEAD -- <target>` empty, `git log baseline..HEAD -- <target>` empty, and the owned-paths stat (`django_strawberry_framework/ tests/ docs/GLOSSARY.md CHANGELOG.md`) vs baseline is empty — no sibling-cycle attribution needed. The file/image surface is cumulative in HEAD (last touch `7d39523b`, confirmed `git merge-base --is-ancestor 7d39523b <baseline>` → ancestor). Each Worker 2 section opens "Filled by Worker 1 per no-source-edit cycle pattern." No High / no Medium claims — independently confirmed at source:

- **Default-nullable regardless of column.** `file_effective_null = True if force_nullable is None else force_nullable` (`converters.py::convert_field_output` #"file_effective_null = True"). Pinned by `test_convert_field_output_file_image_nullable_by_default` (required / `blank=True` / `null=True` columns all → `DjangoFileType | None`) AND `test_convert_field_output_force_nullable_overrides_default` (positive: `force_nullable=True` keeps `| None`; negative: `force_nullable=False` on a `blank=True` column → bare `DjangoFileType`).
- **`name` non-null; `path`/`size`/`url`/`width`/`height` nullable & storage-safe.** `_safe_file_attr` catch list is exactly `(ValueError, OSError, NotImplementedError)` (`converters.py::_safe_file_attr`). Independently confirmed via `uv run python` that `SuspiciousFileOperation` is NOT a subclass of any of the three (MRO: SuspiciousFileOperation → SuspiciousOperation → Exception), so it propagates as the path-traversal security signal — narrow catch correct, no broad `except Exception`.
- **ImageField-before-FileField MRO ordering.** `FIELD_OUTPUT_TYPE_MAP` lists `ImageField` first; `test_field_output_map_mro_precedence_image_subclass_wins` uses a real `ImageField` subclass and asserts `_field_output_type_for(field) is DjangoImageType` (not `DjangoFileType`).
- **Read-output map kept OFF the shared `SCALAR_MAP`/filter-input path.** `scalar_for_field` walks only `SCALAR_MAP`; `_field_output_type_for` walks only `FIELD_OUTPUT_TYPE_MAP`. Grep confirms `FIELD_OUTPUT_TYPE_MAP` has exactly two source consumers — `convert_field_output` and `resolvers._attach_file_resolvers` (plus the `inspect_django_type` diagnostic) — never `scalar_for_field`. Pinned by `test_file_columns_stay_scalar_on_the_filter_input_path`, which drives `filters/inputs._scalar_from_model_field` and asserts a file column → scalar `str` (spec-037 Decision 3 security separation). `SCALAR_MAP[FileField] = SCALAR_MAP[ImageField] = str` unchanged.
- **Parent-resolver / subfield truthiness contract.** `resolvers._make_file_resolver` (`types/resolvers.py:456` #"return value if value else None") returns `None` for a falsy `FieldFile`, so `_safe_file_attr`'s `self` is always truthy and `DjangoFileType.name`'s `return self.name` reads the storage attr (no recursion). Cross-checked at source.
- **Choice-enum generation & relation annotations.** Value-keyed sanitization, empty/grouped-choices rejection, deterministic collision error, `(model, field_name)` caching, four ordered `_sanitize_member_name` rules — all read at source and accurate against the docstrings.

### DRY findings disposition
Both deferrals correct. (1) Forward-looking **Low** (`_safe_file_attr` `self`-truthiness invariant) carries a verbatim trigger ("a second parent-resolver path can construct a `DjangoFileType` whose `self` is a falsy or non-`FieldFile` value") and is genuinely forward-looking — the invariant is currently enforced and cross-checked at `_make_file_resolver`; not a GLOSSARY-only fix. (2) **Defer-with-trigger DRY** (collapse twin MRO-walk lookups `scalar_for_field` / `_field_output_type_for` onto `_mro_lookup`) carries the verbatim trigger "a third `type(field).__mro__` lookup table is added to converters.py"; divergence is real (raise-`ConfigurationError` vs return-`None` miss-semantics at two sites). The rejected "shared effective_null helper" is correctly rejected — the `force_nullable is None` default differs (column `field.null` for scalars vs hard `True` for file/image), the spec-037 Decision 4 distinction.

### Temp test verification
- None used — claims verified against the permanent suite (`tests/types/test_converters.py`) and source grep/inspection.
- Disposition: n/a.

### GLOSSARY accuracy (#4-vs-#5 gate)
`#djangofiletype` (line 330-336), `#djangoimagetype` (352-358), `#upload-scalar` (1361-1363), the scalar-conversion entries (1185, 1261), and `#metarequired_overrides` (894) all read accurate vs live source: nullable-by-default-regardless-of-column, `name` non-null, `path`/`size`/`url`/`width`/`height` nullable via `_safe_file_attr`, `SuspiciousFileOperation` propagation, ImageField-precedes-FileField MRO, file/image stays `str` on the filter/scalar-input side, `required_overrides` non-null opt-in. Public `DjangoFileType` / `DjangoImageType` re-exported from package root (`__init__.py:34,42-43`) carry entries; private symbols (`_safe_file_attr`, `_field_output_type_for`, `_sanitize_member_name`, soft-import helpers) carry none — absence correct. No GLOSSARY-only fix in scope → genuine #5, not a missed #4.

### Validation
- `uv run ruff format --check django_strawberry_framework/types/converters.py` — `1 file already formatted`.
- `uv run ruff check django_strawberry_framework/types/converters.py` — `All checks passed!`.

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the `types/converters.py` checklist box in `docs/review/review-0_0_11.md`.
