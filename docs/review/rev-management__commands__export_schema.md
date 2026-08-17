# Review: `django_strawberry_framework/management/commands/export_schema.py`

Status: verified

## Understanding

`Command.handle` resolves a Strawberry `module[:symbol]`, validates `strawberry.Schema`, renders SDL once with `print_schema`, and emits either exact stdout bytes or UTF-8 file output. A missing/blank path is rejected, file writes replace existing targets without creating parent directories, and importer/I/O failures surface as `CommandError` with their causes preserved.

## Verification

Compared the target against `HEAD` baseline `852aa726ddeef716ddf3b36405cb53cc8a7dad3a`. A pre-existing concurrent working-tree hunk already broadened the file-write translation from `OSError` to `(OSError, ValueError)`; it was preserved unchanged. Traced Django `OutputWrapper`, Strawberry `print_schema`, `Path.write_text`, fakeshop `config.schema`, and package/example command tests.

Before implementation, `Path.write_text`'s default `newline=None` was confirmed to translate LF output to the host platform's newline sequence. That contradicts the command's documented stdout/file byte-equivalence on Windows.

Focused evidence before the fix: `uv run pytest --no-cov tests/management/test_export_schema.py` — 11 passed. After the fix: the same command — 12 passed, including the new newline-contract test.

## Improvements

### High

None.

### Medium

#### File output could change SDL bytes on newline-translating platforms

**Observation:** `Path.write_text(schema_output, encoding="utf-8")` left newline translation enabled even though stdout deliberately suppresses Django's extra ending and the command documents byte-identical SDL output.

**Evidence:** `pathlib.Path.write_text` defaults `newline=None`; the Python runtime reports that parameter and translates `\n` on platforms with a different native newline. The existing stdout/file comparison only distinguished the trailing command ending, not host newline translation.

**Impact:** Redirected stdout and `--path` artifacts could differ byte-for-byte on Windows, breaking schema diffs and generated-artifact reproducibility.

**Recommendation:** Pass `newline=""` at the owning file-write boundary so UTF-8 SDL preserves Strawberry's LF bytes exactly.

**Proof:** `tests/management/test_export_schema.py::test_export_schema_file_write_disables_newline_translation` spies on the write operation and asserts `encoding="utf-8"` and `newline=""`; the full package command test file passes.

### Low

None.

## Summary

The command's staged import, schema-type, rendering, and path-error boundaries are sound. The newline option is the root-cause fix for the only confirmed portability contract gap; the concurrent `ValueError` error-boundary improvement remains intact.

## Implementation (Worker 1)

- Updated `django_strawberry_framework/management/commands/export_schema.py::Command.handle` to call `Path.write_text(..., newline="")`.
- Added `tests/management/test_export_schema.py::test_export_schema_file_write_disables_newline_translation`.
- Preserved the pre-existing concurrent `(OSError, ValueError)` catch hunk and the unrelated dirty fakeshop test.
- Validation: `uv run ruff format .` (1 file reformatted), `uv run ruff check --fix .` (passed), and `uv run pytest --no-cov tests/management/test_export_schema.py` (12 passed).
- No changelog update is warranted for a portability correction to an existing command contract.

## Independent verification (Worker 2)

The current source contains Worker 1's `Path.write_text(..., newline="")` fix and the pre-existing concurrent `(OSError, ValueError)` catch; Worker 2 made no source changes. I re-read the command, Django `OutputWrapper`, Strawberry `print_schema`, `Path.write_text` on the Python 3.10 support floor, command discovery, and both command-test tiers.

Challenge results:

- `uv run pytest --no-cov tests/management/test_export_schema.py` is included in the package run and passes all 12 tests; `uv run pytest --no-cov examples/fakeshop/tests/test_export_schema.py` passes all 5 project tests. These cover malformed selectors, missing and blank `--path`, missing parent directories, embedded NUL paths, overwrite behavior, non-`Schema` symbols, and default-symbol imports.
- A real fakeshop probe compared stdout bytes and `--path` bytes with `print_schema(schema).encode("utf-8")`: `stdout_bytes_equal True`, `file_bytes_equal True`, `contains_crlf False`. The command was then called twice in the same process for both inspect and export; both calls returned the same title/output length (`281682` SDL characters for export).
- The Python 3.10 runtime reports `Path.write_text(self, data, encoding=None, errors=None, newline=None)`, so `newline=""` is compatible with the declared package floor and prevents host newline translation while retaining UTF-8 encoding. Real `manage.py` discovery exposes the expected positional `schema` and optional `--path`.

No remaining target-owned defect was reproduced. The newline option is the root-cause portability fix, and the file-write exception translation remains correctly local to the filesystem boundary.
