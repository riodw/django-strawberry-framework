# Pre-BETA review: management/

Scope: management commands -- `commands/export_schema.py`,
`commands/inspect_django_type.py`, `commands/_imports.py`.

Method: full logic read of all three in `docs/shadow/current/`. Read-only;
no tests run.

Bottom line: both commands are read-only diagnostics (print a type table / print
or write the schema SDL) with clean `CommandError` handling and no unintended
mutation. No P0/P1. Only minor polish.

## P0 -- correctness suspicions

None found.

## P1 -- fix before BETA

None found.

## P2 -- polish / hardening

### `export_schema.py` -- confirm `--path` write encoding and overwrite behavior are documented
Confidence: low. `pathlib.Path(path).write_text(schema_output, encoding=...)`
overwrites the target unconditionally and wraps `OSError` in `CommandError`.
That is fine for an operator-run command (the path is a trusted CLI arg, so
traversal is not a concern), but document that `--path` overwrites without
prompting and note the encoding used, so CI usage is predictable.

### `inspect_django_type.py::_resolve_bare_name` -- ambiguity is handled; keep the message actionable
Confidence: low. A bare type name that matches multiple registered types raises
`CommandError` listing candidates -- good. Just ensure the message shows the
fully-qualified import path for each candidate so the operator can copy one
directly into the disambiguated form.

## API & consistency notes

- `inspect_django_type` imports the `--schema` symbol purely for its
  finalization side effect and then reads the registry. That coupling to
  "importing the schema finalizes types" is the same global-finalization
  contract flagged in the root/registry review -- consistent, but it means the
  command must be pointed at the project's real schema module to see finalized
  types. Worth stating in `--help`.
- Both commands route imports through `_imports.py::import_or_command_error`, so
  a bad dotted path yields a clean `CommandError` rather than a traceback. Keep
  new commands on this helper.

## Verified sound (do not re-flag)

- Neither command mutates the database or the registry beyond the import-time
  finalization side effect; `export_schema` only reads + prints/writes, and
  `inspect_django_type` only reads + prints.
- `export_schema` validates the resolved symbol `isinstance(..., Schema)` before
  printing, so a wrong `--schema` target fails with a clear message.
- `inspect_django_type` guards the unfinalized-definition and non-`DjangoType`
  cases with specific `CommandError`s.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
