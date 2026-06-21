# Review: `django_strawberry_framework/management/commands/inspect_django_type.py`

Status: verified

## DRY analysis

- None — the file's one cross-module dedupe (the import-rewrap tail) already bottoms out in `management/commands/_imports.py::import_or_command_error`, consumed at both `inspect_django_type.py::Command.handle` (the `--schema` import-for-side-effect, `lambda: import_module_symbol(...)`) and `inspect_django_type.py::Command._resolve_type` (the dotted-path `lambda: import_string(arg)`); and the file/image converter-naming path delegates to the single canonical MRO walk `types/converters.py::_field_output_type_for` rather than re-deriving the FileField/ImageField map, so the maintainer's recent `_scalar_row` change is itself a DRY consolidation (one map-walk site shared with `convert_field_output` and `resolvers._attach_file_resolvers`), not a new candidate. The two render helpers `_render_annotation` (typing annotations) and `_render_strawberry_type` (Strawberry wrappers) are deliberately separate — they walk different object models (`typing.get_origin`/`get_args` vs `StrawberryOptional`/`StrawberryList` isinstance), share the leaf `_scalar_name`, and a forced merge would reintroduce a type-dispatch branch on every node; correct as siblings.

## High:

None.

## Medium:

None.

## Low:

None.

## What looks solid

### DRY recap

- **Existing patterns reused.** Import-rewrap delegated to `_imports.py::import_or_command_error` (both call sites: `Command.handle` `--schema` import + `Command._resolve_type` dotted path). The new file/image converter-label path reuses the canonical `types/converters.py::_field_output_type_for` MRO walk (the same site `convert_field_output` and `resolvers._attach_file_resolvers` use) instead of indexing `FIELD_OUTPUT_TYPE_MAP` locally, so ImageField-before-FileField ordering can never drift between this command and the runtime read path. `snake_case` (utils/strings), `registry.iter_types`/`model_for_type`, `SCALAR_MAP` reused as-is.
- **New helpers considered.** A merged renderer over `_render_annotation` + `_render_strawberry_type` — rejected: they walk two distinct object models (raw `typing` vs Strawberry wrappers) and already share the `_scalar_name` leaf; merging would add a per-node dispatch branch with no call-site reduction. A shared "nullable token" helper over `_yes_no`/`_consumer_nullable`/`_annotation_is_optional` — rejected: each maps a different input shape (bool vs Strawberry field type vs typing annotation) onto the same three tokens; no duplicated body to hoist.
- **Duplication risk in the current file.** Repeated literals `__name__` (2x), `relation:` (2x in `_relation_row`/`_connection_only_relation_row` — two halves of one converter-label family that intentionally diverge on the `(connection-only)` suffix), `no (list)` (2x in `_relation_row`/`_consumer_nullable` — the relation-row many-side convention deliberately shared by the consumer path). All intentional family self-naming, not extractable.

### Other positives

- The recent maintainer change to `_scalar_row` is correct and root-cause-shaped. A FileField/ImageField column's displayed GraphQL type comes from the read-side `DjangoFileType`/`DjangoImageType` output object (via `FIELD_OUTPUT_TYPE_MAP`), while `SCALAR_MAP`'s file rows deliberately stay `str` for the filter-input path. Naming a `SCALAR_MAP[FileField]` row would mis-attribute the converter to a row that did NOT produce the shown type. The code now reports `convert_field_output -> {output_type.__name__}` only when `_field_output_type_for(field)` returns non-None, and otherwise falls through to the choice-enum / `SCALAR_MAP[<MRO-ancestor>]` label. `graphql_type` and `nullable` still come from the annotation (`DjangoFileType | None` → `DjangoFileType`, nullable `yes`), so the type/nullability columns stay annotation-sourced and only the converter column was corrected. This is the highest-quality fix (single shared MRO walk, no local map copy).
- Test discipline on the changed path is strong: `tests/management/test_inspect_django_type.py::test_scalar_row_names_file_output_converter_not_scalar_map` parametrizes both `(FileField, DjangoFileType)` and `(ImageField, DjangoImageType)`, asserts all three returned columns, AND asserts the negative `"SCALAR_MAP" not in converter` — pinning both the correct label and the regression it replaced. The ImageField case proves the FileField-subclass resolves to `DjangoImageType` via the shared walk rather than falling through to `DjangoFileType`.
- Dispatch ordering in `_resolve_row` is correct and documented most-specific-first: suppressed Relay pk → consumer-authored → relation → scalar. The suppressed-pk guard precedes the relation branch precisely so a relation pk on a Relay type (`OneToOneField(primary_key=True)`) cannot reach `_relation_row` and `KeyError` on the absent annotation.
- The connection-only relation path (`_suppressed_connection_name` + `_connection_only_relation_row`) reads the resolved type from `origin.__strawberry_definition__` for the synthesized `<rel>_connection` sibling rather than indexing the popped `origin.__annotations__[field.name]`, and is covered by `tests/management/test_inspect_django_type.py` (`relation: reverse FK (connection-only)`).
- Error messages are concrete and recovery-oriented (unfinalized hint, ambiguous-bare-name candidate list with module + model, UNRESOLVED forward-ref hint pointing at `--schema`). The dotted-path failure surfaces the original `import_string` error unmasked rather than a registry fallback.

### Summary

`inspect_django_type.py` is a strict reader of the post-finalize introspection surface; the only logic touched this cycle is the maintainer's `_scalar_row` correction, which routes FileField/ImageField converter-column naming through the canonical `_field_output_type_for` MRO walk so the displayed-type source and the named converter agree (`convert_field_output -> DjangoFileType`/`DjangoImageType`), never the filter-path `SCALAR_MAP` row. The change is correct, minimal, root-cause-shaped, and pinned by a parametrized regression test asserting both the positive label and the negative SCALAR_MAP exclusion. `git diff` is empty vs both the cycle baseline (`87265f05`) and HEAD — the maintainer's edits already landed in HEAD — so this cycle produces zero source/test/doc edits. GLOSSARY (entry near line 1234) is accurate and undrifted: it describes the converter-row contract at the level of "SCALAR_MAP is re-walked only to NAME the converter row" without promising a specific file/image label, so the internal label change introduces no contract drift. No High / Medium / Low findings.

---

## Fix report (Worker 2)

Filled by Worker 1 per no-source-edit cycle pattern.

### Files touched
- None — no-source-edit cycle.

### Tests added or updated
- None — no-source-edit cycle.

### Validation run
- `uv run ruff format .` — pass; `289 files left unchanged`.
- `uv run ruff check --fix .` — pass; `All checks passed!`.

### Notes for Worker 3
- Zero findings; all severities `None.`. No source, test, GLOSSARY, or CHANGELOG edits.
- `git diff 87265f05a49a79995ded92a5c3e515fdb579224d -- <target>` and `git diff HEAD -- <target>` both empty — the maintainer's file/image `_scalar_row` change already in HEAD.
- No GLOSSARY-only fix in scope. The GLOSSARY entry near `docs/GLOSSARY.md` line 1234 is accurate vs current source; it documents the converter-row contract without a file/image-specific label, so the maintainer's internal label change is not a drift.
- Load-bearing claims re-verified this cycle (re-grep, do not trust line numbers): (1) `_field_output_type_for` is the single shared MRO walk in `types/converters.py` consumed by `convert_field_output` + `resolvers._attach_file_resolvers`; (2) `FIELD_OUTPUT_TYPE_MAP` lists `ImageField` before `FileField` so the subclass resolves to `DjangoImageType`; (3) `SCALAR_MAP` file rows stay `str` (filter-input path) — confirmed at `converters.py` `# FileField / ImageField stay ``str`` here on purpose`. Regression pinned by `tests/management/test_inspect_django_type.py::test_scalar_row_names_file_output_converter_not_scalar_map`.

---

## Comment/docstring pass

Filled by Worker 1 per no-source-edit cycle pattern. No comment/docstring edits — the inline comment block in `_scalar_row` (`# A FileField / ImageField column is converted on the read side by convert_field_output via FIELD_OUTPUT_TYPE_MAP ... NOT by SCALAR_MAP ...`) accurately describes the current logic and the `_matched_scalar_key` docstring's unreachable-fallback note remains true. No stale TODO anchors (overview: 0 TODO comments).

---

## Changelog disposition

Filled by Worker 1 per no-source-edit cycle pattern. Not warranted — no edits this cycle (zero source/test/doc changes); the maintainer's file/image work already landed in HEAD outside this review. Per `AGENTS.md` ("Do not update CHANGELOG.md unless explicitly instructed") and the active plan `docs/review/review-0_0_11.md` (silent on changelog), no entry.

---

## Verification (Worker 3)

### Logic verification outcome
All severities `None.` confirmed genuine, not lazy. Independently re-verified every load-bearing claim against live source (re-grep, not line numbers):

- **Zero-edit proof (target):** `git diff 87265f05a49a79995ded92a5c3e515fdb579224d -- <target>` empty AND `git diff HEAD -- <target>` empty. The maintainer's `_scalar_row` file/image change is already in HEAD.
- **Maintainer change correct & root-cause-shaped:** `inspect_django_type.py::Command._scalar_row` routes the file/image converter-column label through `_field_output_type_for(field)` → reports `convert_field_output -> {output_type.__name__}` only when non-None, else falls through to `choice enum` / `SCALAR_MAP[<MRO-ancestor>]`. It does NOT name `SCALAR_MAP[FileField]`. Confirmed `graphql_type` and `nullable` stay annotation-sourced (read from `definition.origin.__annotations__[field.name]` via `_render_annotation` / `_annotation_is_optional`) — only the converter column changed.
- **Single shared MRO walk:** `types/converters.py::_field_output_type_for` (lines 398-411) is the one map-walk site, consumed by `convert_field_output` (line 443) and `resolvers._attach_file_resolvers`; `inspect_django_type.py` imports and reuses it rather than indexing `FIELD_OUTPUT_TYPE_MAP` locally — ordering can never drift.
- **ImageField-before-FileField ordering:** `FIELD_OUTPUT_TYPE_MAP` (converters.py 208-210) lists `models.ImageField: DjangoImageType` before `models.FileField: DjangoFileType`, so the `__mro__` walk resolves an `ImageField` (a `FileField` subclass) to `DjangoImageType` first. Confirmed.
- **SCALAR_MAP file rows stay `str`:** converters.py 191-198 — `models.FileField: str`, `models.ImageField: str` with the verbatim comment "FileField / ImageField stay ``str`` here on purpose" (filter-input path). The mis-attribution the fix prevents is real.
- **Regression test pins all three columns:** `tests/management/test_inspect_django_type.py::test_scalar_row_names_file_output_converter_not_scalar_map` (lines 156-183) parametrizes `(FileField, DjangoFileType)` and `(ImageField, DjangoImageType)`, asserts `graphql_type == output_type.__name__`, `nullable == "yes"`, `converter == f"convert_field_output -> {output_type.__name__}"`, AND the negative `"SCALAR_MAP" not in converter`. The ImageField case proves the subclass resolves to `DjangoImageType` via the shared walk, not a fall-through to `DjangoFileType`.

### Shape #5 gate
Genuine #5, not a missed #4. Each Worker 2 section opens "Filled by Worker 1 per no-source-edit cycle pattern." GLOSSARY entry at `docs/GLOSSARY.md` (~1234) reads accurate vs live source: it describes the converter-row contract as "`SCALAR_MAP` is re-walked only to NAME the converter row" without promising any file/image-specific label, so the maintainer's internal label change introduces no contract drift — no GLOSSARY fix owed. The inline `_scalar_row` comment block accurately describes the current logic.

### Sibling-cycle attribution
Owned-paths `--stat` vs baseline shows three NON-target dirty hunks: `mutations/inputs.py`, `mutations/resolvers.py`, `utils/relations.py`. `rev-utils__relations.md` is `Status: verified`; the mutations hunks are in-flight sibling / AGENTS.md #33 concurrent-maintainer work. Per diff-scoping, any non-target hunk is out of scope when the target diff is clean (the closed-sibling carve-out only matters when attributing a hunk that touches the target itself). The target diff is clean both ways — these are informational only, not a rejection trigger.

### Changelog disposition
"Not warranted" verified: `git diff -- CHANGELOG.md` empty; both citations present (`AGENTS.md` "Do not update CHANGELOG.md unless explicitly instructed" + active plan `review-0_0_11.md` silence). Cycle is zero-edit / internal-only, so "Not warranted" is the correct state.

### Validation
`uv run ruff format --check .` → 289 files already formatted (pass). `uv run ruff check .` → All checks passed!

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the `inspect_django_type.py` checkbox in `docs/review/review-0_0_11.md`.
