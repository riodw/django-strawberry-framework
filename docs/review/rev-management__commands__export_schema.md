# Review: `django_strawberry_framework/management/commands/export_schema.py`

Status: verified

## DRY analysis

- None — single management-command file with no parallel siblings in `management/commands/`, the `(ImportError, AttributeError)` → `CommandError` and `OSError` → `CommandError` wrap pairs are different exception domains caught at different statements (no shared helper would consolidate them without obscuring the distinct call sites), and the upstream `strawberry_django/management/commands/export_schema.py:1-39` is the canonical shape this file deliberately mirrors so cross-package consolidation is out of scope.

## High:

None.

## Medium:

### `--path ""` (empty-string value) silently routes to stdout, contradicting the CHANGELOG-pinned "requires a value" contract

`handle()` at `django_strawberry_framework/management/commands/export_schema.py:39-47` gates the file-write path with `if path:`, which is a truthy-string check. An empty string is falsy in Python, so a user (or CI script) that resolves `--path` from an empty environment variable — `manage.py export_schema config.schema --path "$SCHEMA_OUT"` where `SCHEMA_OUT=""` — passes `--path ""` to argparse, which sets `options["path"] = ""`, and the command silently emits SDL to stdout without the `Wrote schema to ...` success message. The user thinks they wrote a file; nothing was written; there is no error.

`CHANGELOG.md:23` (the 0.0.7 "Changed" entry that documents dropping `nargs="?"`) frames the contract as: "`--path` now requires a value when the flag is given … Dropping `nargs="?"` makes argparse raise `CommandError` at parse time when the user gives `--path` without a value, catching the obvious typo." The empty-string case is the same typo class (the user gave a value, the value was empty, the user expected a file write) but slips through argparse and through the truthy-string gate alike. The CHANGELOG's stated motivation — catching the obvious typo — does not cover the path-value-resolves-to-empty case the contract was tightened to catch.

Why it matters: the failure mode is silent — schema export is a CI/release-time operation, and a silent "no file written, SDL printed to terminal log instead" produces a release artifact whose downstream tools (`graphql-codegen`, schema-diff jobs) get nothing to read, often only surfaced after the next pipeline step fails. The clearer contract uses an explicit `path is not None` gate and an empty-string rejection so a user who passes `--path ""` gets a `CommandError("--path requires a non-empty value")` consistent with the "no silent typo" framing.

Recommended change: replace the `if path:` gate at line 40 with an explicit two-step check —

```django_strawberry_framework/management/commands/export_schema.py:39-47
        path = options.get("path")
        if path is None:
            self.stdout.write(schema_output)
            return
        if not path:
            raise CommandError("--path requires a non-empty value")
        try:
            pathlib.Path(path).write_text(schema_output, encoding="utf-8")
        except OSError as e:
            raise CommandError(str(e)) from e
        self.stdout.write(self.style.SUCCESS(f"Wrote schema to {path}"))
```

Add a test under `tests/management/test_export_schema.py` pinning the new contract:

```tests/management/test_export_schema.py
def test_export_schema_raises_command_error_when_path_flag_is_empty_string(monkeypatch):
    _make_test_module(monkeypatch, schema=_make_schema())
    with pytest.raises(CommandError, match="--path requires a non-empty value"):
        call_command("export_schema", "test_module:schema", "--path", "")
```

If the maintainer prefers to keep `if path:` truthy-string-permissive (treating `--path ""` as "no path given, route to stdout"), the CHANGELOG entry 23 wording should be narrowed to "bare `--path` flag with no following value" so the contract and the implementation agree. The Medium tracks "implementation does not enforce the contract the CHANGELOG describes" either way; the recommended fix is the stricter, root-cause shape per `AGENTS.md` line 4.

## Low:

### Stdout-path SDL write is not UTF-8-encoding-pinned, asymmetric with the explicit-UTF-8 file-write path

`django_strawberry_framework/management/commands/export_schema.py:42` pins the file-write path to `encoding="utf-8"` (matching the upstream and the spec `Edge cases and constraints` "UTF-8 file write" bullet at `docs/SPECS/spec-018-export_schema-0_0_7.md:582`). The stdout path at line 47 (`self.stdout.write(schema_output)`) routes through Django's `OutputWrapper` to `sys.stdout`, whose encoding is process-locale-dependent. On modern macOS / Linux this is UTF-8 by default; on Windows shells without `PYTHONUTF8=1` it may be `cp1252`. A schema with non-ASCII characters in a `description=` or directive argument would `UnicodeEncodeError` on the stdout path but write cleanly to a file.

Why it's Low: the user-facing impact is bounded to Windows-shell consumers running `manage.py export_schema config.schema` (no `--path`), which is uncommon for the release-pipeline use case (`--path` is the canonical CI shape). The file-write path — the documented happy-path for CI — is already UTF-8-pinned.

Defer until a Windows-packaging or non-ASCII-description card lands; flag this Low as the trigger condition. When a future card touches stdout encoding, either pass `errors="replace"` through the `OutputWrapper` configuration or document the Windows-shell limitation in the README's "shipped today" bullet.

### Module-level `import pathlib` is the only `pathlib` import in the package; prefer `from pathlib import Path` for one-line consistency with the rest of the package's "import the symbol, not the module" convention

`django_strawberry_framework/management/commands/export_schema.py:3` is the only `import pathlib` (vs. `from pathlib import Path`) site under `django_strawberry_framework/`. Every other site in the package that needs `Path` imports the symbol directly. Switching to `from pathlib import Path` at line 3 lets line 42 read `Path(path).write_text(...)` — one fewer module-qualifier indirection, consistent with the package-wide convention.

Defer; trigger condition: a second `pathlib.Path` site lands in the package OR a project-pass DRY cycle picks this up. Cosmetic-but-greppable; not worth a one-line cycle on its own.

## What looks solid

### DRY recap

- **Existing patterns reused.** The command body mirrors `strawberry-django/strawberry_django/management/commands/export_schema.py:1-39` end-to-end — same `import_module_symbol(..., default_symbol_name="schema")` resolution, same `(ImportError, AttributeError)` → `CommandError(str(e)) from e` wrap, same verbatim error message `"The `schema` must be an instance of strawberry.Schema"` at line 36, same `print_schema(...)` SDL output, same `pathlib.Path(path).write_text(..., encoding="utf-8")` file-write shape, same `self.stdout.write` capture-friendly stdout emit at line 47. The deltas (Title-Cased `GraphQL` in `help`, module / class / method docstrings, `parser: CommandParser` and `-> None` annotations, dropped `nargs=1` / `nargs="?"`, added `OSError` → `CommandError` wrap, added `Wrote schema to {path}` success line) are each pinned in `docs/SPECS/spec-018-export_schema-0_0_7.md` Decision 2 / Decision 4 / Decision 5 and in `CHANGELOG.md:21-26`.
- **New helpers considered.** A shared `_wrap_as_command_error(callable)` decorator was considered for the two `try/except` blocks at lines 27-33 and 41-44; rejected — the two catch tuples (`(ImportError, AttributeError)` vs. `OSError`) span different exception domains and the wrapped statements are different I/O surfaces, so a shared helper would obscure the call site for no DRY win at this scale (`scripts/review_inspect.py` reports zero repeated string literals across the file).
- **Duplication risk in the current file.** None — the `CommandError(str(e)) from e` shape appears at lines 33 and 44 but the catch tuples differ, and both sites are part of the upstream `strawberry-django` shape verbatim, intentionally mirrored per `docs/SPECS/spec-018-export_schema-0_0_7.md` Borrowing posture line 132.

### Other positives

- Spec-pinned upstream parity. The command is the textbook "borrow upstream, narrow forced divergences" shape: every behavioral pin matches `strawberry-django/strawberry_django/management/commands/export_schema.py`, every divergence is documented in either the spec or `CHANGELOG.md:21-26`. A migrant from `strawberry-django` running `manage.py export_schema config.schema [--path schema.graphql]` gets identical behavior.
- Narrow exception catching. The `(ImportError, AttributeError)` tuple at line 32 is exactly the surface `import_module_symbol` raises (`importlib.import_module` → `ImportError`, `getattr` → `AttributeError`); the `OSError` catch at line 43 is the documented Python superclass for `FileNotFoundError` / `PermissionError` / `IsADirectoryError`. Neither catch is `except Exception` — broad-except masking is correctly avoided per `docs/SPECS/spec-018-export_schema-0_0_7.md` Decision 5 "Alternatives considered (and rejected)".
- `from e` chain preservation. Both `raise CommandError(str(e)) from e` sites at lines 33 and 44 preserve the original exception via `__cause__`, so a maintainer reading a failed CI log via `traceback.print_exc()` sees both the `CommandError` summary and the underlying `ImportError` / `OSError` shape that produced it.
- `isinstance(schema_symbol, Schema)` over duck-typing. The explicit instance check at line 35 catches "user pointed `--schema` at the wrong symbol" with a clean attributable error before `print_schema(...)` would surface a deep Strawberry-internal `TypeError`, per `docs/SPECS/spec-018-export_schema-0_0_7.md` Decision 5 failure mode 2.
- `self.stdout.write` (not `print(...)`). Django's `OutputWrapper` is used so `call_command(..., stdout=StringIO())` captures cleanly without `sys.stdout` monkey-patching — load-bearing for the test suite's `test_export_schema_writes_sdl_to_stdout_by_default` capture pattern (rev2 H1 / `docs/SPECS/spec-018-export_schema-0_0_7.md` Decision 4).
- `self.style.SUCCESS` for the post-write line. The success message at line 45 uses Django's standard `OutputWrapper.style.SUCCESS` (green when the terminal supports color), matching the convention every shipped Django management command follows (`makemigrations`, `migrate`, `collectstatic`).
- `default_symbol_name="schema"` fallback exercised. The package-internal test `tests/management/test_export_schema.py:116-120` (`test_export_schema_falls_back_to_default_symbol_name_schema`) pins the no-`:symbol` selector path so a future refactor that drops the kwarg fails this test — per spec `docs/SPECS/spec-018-export_schema-0_0_7.md` Decision 3 and Test plan test (g).
- Eight tests + fakeshop live test. The package-internal suite covers happy-stdout (line 43), happy-`--path` (line 50), `ImportError` (line 71), `AttributeError` (line 76), non-`Schema` (line 82), missing-positional (line 88), missing-path-directory `OSError` (line 93), bare-`--path` with no value (line 105), and default-symbol fallback (line 116) — eight tests pinning each branch including the two implementation-additive `OSError` / `nargs="?"`-drop branches; the fakeshop test at `examples/fakeshop/tests/test_commands.py:199` exercises the full real-`DjangoOptimizerExtension`-bearing schema end-to-end via `call_command`. The `monkeypatch.setitem(sys.modules, ...)` cleanup contract at lines 22-27 keeps the seven `test_module`-using tests order-independent.
- `tests/management/__init__.py` ships. The package marker exists with the one-line docstring (`tests/management/__init__.py:1`) per spec Decision 7, allowing pytest to collect the tests as `tests.management.<module>`.
- `import_module_symbol`'s third raise (`ValueError`) is correctly unreachable. The selector signature `(selector, default_symbol_name)` raises `ValueError("Selector does not include a symbol name")` only when both no `:` is present AND `default_symbol_name` is falsy. The command always passes `default_symbol_name="schema"`, so the `ValueError` branch is statically unreachable through this call site; the narrow `(ImportError, AttributeError)` catch is exhaustive for the actual reachable failure modes.
- Lint gates covered at the root-cause level. Module docstring (`D100`), class docstring (`D101`), two method docstrings (`D102`), `parser: CommandParser` parameter annotation (`ANN001`), and `-> None` return annotations on both methods (`ANN201`) — every gate is satisfied by adding real documentation/annotations, not by `# noqa` suppressions (per `AGENTS.md` line 4 / spec Borrowing posture lines 189-190).

### Summary

`export_schema.py` is a 47-line Django management command that mirrors `strawberry-django`'s upstream shape verbatim while adding gate-forced docstrings/annotations (pydocstyle + flake8-annotations) and four documented behavioral refinements (success message via `self.style.SUCCESS`; `nargs=1`-drop on positional `schema`; `nargs="?"`-drop on `--path`; `OSError` → `CommandError` wrap). Every documented behavior is pinned by a test; every divergence from upstream is captured in either `docs/SPECS/spec-018-export_schema-0_0_7.md` Decisions 2/4/5 or `CHANGELOG.md:21-26`. One Medium worth surfacing: `if path:` truthy-string-gates the file-write path, so `--path ""` (empty-string value, e.g. from an unset CI env var) silently routes to stdout, contradicting the CHANGELOG-23 "requires a value when the flag is given" contract — the obvious-typo case the `nargs="?"`-drop was added to catch. Two Lows defer until trigger conditions land: stdout-path UTF-8 asymmetry (Windows shell), and the single-site `import pathlib` vs. `from pathlib import Path` cosmetic.

---

## Fix report (Worker 2)

### Files touched
- `django_strawberry_framework/management/commands/export_schema.py:38-49` — Replaced the `if path:` truthy-string gate with a two-step check: `if path is None: <stdout branch>; return` short-circuits the no-flag case, then `if not path: raise CommandError("--path requires a non-empty value")` rejects the empty-string typo case before the `pathlib.Path(path).write_text(...)` write. Flattened the trailing `else:` branch since the `path is None` path returns early. Behaviour: `manage.py export_schema config.schema` (no `--path`) still routes to stdout; `manage.py export_schema config.schema --path ""` (empty-string value from an unset CI env var) now raises `CommandError("--path requires a non-empty value")` instead of silently emitting SDL to stdout. The CHANGELOG-23 "requires a value when the flag is given" contract is now enforced end-to-end (argparse rejects bare `--path`; the explicit `not path` check rejects `--path ""`).

### Tests added or updated
- `tests/management/test_export_schema.py::test_export_schema_raises_command_error_when_path_flag_is_empty_string` — Pins the new contract: `call_command("export_schema", "test_module:schema", "--path", "")` raises `CommandError` whose message matches `"--path requires a non-empty value"`. Placed immediately after the existing `test_export_schema_raises_command_error_when_path_flag_has_no_value` (bare `--path` argparse rejection) so the two related typo-class tests sit adjacent for grep-discoverability. The pre-existing eight tests are unchanged; their behaviour is unaffected by the gate rewrite (no-`--path` still routes to stdout via the `path is None` short-circuit; non-empty `--path` still writes the file via the same `pathlib.Path(path).write_text(...)` call).

### Validation run
- `uv run ruff format .` — pass / 118 files left unchanged
- `uv run ruff check --fix .` — pass / All checks passed
- pytest not run per `START.md` standing rule and `AGENTS.md` line 14; the cycle introduced a test but its run is deferred to the maintainer

### Notes for Worker 3
- Shadow file: `docs/shadow/management__commands__export_schema.stripped.py` exists (Worker 0 ran `--all` at plan time) but was not consulted during fix implementation — the original source file is 48 lines and reads cleanly without the shadow's `#` / docstring stripping.
- L1 (stdout-path UTF-8 asymmetry) and L2 (`import pathlib` vs. `from pathlib import Path`) are explicit Worker 1 defers with named trigger conditions (Windows-packaging / non-ASCII-description card; second `pathlib.Path` site or project-pass DRY cycle). Neither lands in this cycle's logic pass; both can land in the comment pass only if Worker 3's verification surfaces a wording nit on them.
- The Medium's "If the maintainer prefers to keep `if path:` truthy-string-permissive…" branch (CHANGELOG-23 wording narrowed instead) is the alternative path Worker 1 surfaced. This cycle takes the stricter root-cause fix per `AGENTS.md` line 4; the CHANGELOG-23 wording is left as-is because the implementation now enforces what the wording describes.

---

## Verification (Worker 3)

### Logic verification outcome

- **M1 (`--path ""` silently routes to stdout)** — accepted. Diff at `django_strawberry_framework/management/commands/export_schema.py:39-49` replaces the `if path:` truthy-string gate with the recommended two-step shape exactly as the artifact prescribed at lines 26-36: `if path is None: self.stdout.write(schema_output); return` short-circuits the no-flag case (since `options.get("path")` returns `None` when `--path` is omitted), then `if not path: raise CommandError("--path requires a non-empty value")` rejects the empty-string typo case before the `pathlib.Path(path).write_text(...)` write. Logic correctness re-checked by re-reading the post-edit file at `export_schema.py:39-49`: (a) no-`--path` → `options.get("path")` returns `None` → enters `if path is None:` branch → writes SDL to stdout via `self.stdout.write(schema_output)` and returns (unchanged behaviour vs. pre-edit); (b) `--path ""` → `options.get("path")` returns `""` → `path is None` is False → falls into `if not path:` (since `not ""` is True) → raises `CommandError("--path requires a non-empty value")` (new behaviour, fixes the silent-typo case); (c) `--path /tmp/schema.graphql` → `path is None` False → `not path` False → falls through to `pathlib.Path(path).write_text(schema_output, encoding="utf-8")` with the existing `OSError` → `CommandError` wrap (unchanged behaviour). The flattened `else:` is correct since the `path is None` branch returns early — control flow is identical to the artifact-recommended snippet.
- **L1 (stdout-path UTF-8 asymmetry)** — accepted as deferred per Worker 1's named trigger condition quoted verbatim at `rev-management__commands__export_schema.md:58`: "Defer until a Windows-packaging or non-ASCII-description card lands; flag this Low as the trigger condition. When a future card touches stdout encoding, either pass `errors=\"replace\"` through the `OutputWrapper` configuration or document the Windows-shell limitation in the README's 'shipped today' bullet." Neither trigger condition has landed; deferral is correct.
- **L2 (`import pathlib` vs. `from pathlib import Path`)** — accepted as deferred per Worker 1's named trigger condition quoted verbatim at `rev-management__commands__export_schema.md:64`: "Defer; trigger condition: a second `pathlib.Path` site lands in the package OR a project-pass DRY cycle picks this up. Cosmetic-but-greppable; not worth a one-line cycle on its own." Neither trigger condition has landed; deferral is correct.

### DRY findings disposition

Worker 1's "## DRY analysis" reported `None` at artifact line 7 with three cited reasons (single management-command file with no parallel siblings; the two `try/except` wraps span different exception domains; upstream `strawberry-django` shape is the deliberate borrow point). Worker 2's M1 fix does not introduce new duplication — the new `if not path: raise CommandError(...)` site is a single statement with no upstream parallel, and Worker 2's "Files touched" entry explicitly preserves the existing `OSError` → `CommandError` wrap unchanged. No carry-forward.

### Temp test verification

No temp tests created. The new permanent test at `tests/management/test_export_schema.py:111-114` (`test_export_schema_raises_command_error_when_path_flag_is_empty_string`) pins the new contract: `pytest.raises(CommandError, match="--path requires a non-empty value")` matches the new error message verbatim, the call shape `call_command("export_schema", "test_module:schema", "--path", "")` reproduces the artifact's failure-mode trigger (empty-string `--path` value from an unset CI env var), and placement at lines 111-114 sits immediately after the related `test_export_schema_raises_command_error_when_path_flag_has_no_value` (bare `--path` argparse rejection) at lines 105-108 per Worker 2's "grep-discoverability" rationale — the two typo-class tests now sit adjacent.

### Validation run

- `git diff -- django_strawberry_framework/management/commands/export_schema.py` — confirms the M1 rewrite matches the artifact's recommended shape (lines 26-36) exactly.
- `git diff -- tests/management/test_export_schema.py` — confirms the new test at lines 111-114 sits immediately after the bare-`--path` argparse-rejection test, matches the `CommandError` message verbatim.
- `git diff -- CHANGELOG.md` — empty (no edits; changelog disposition deferred to the next sub-pass).
- `uv run ruff format --check .` — pass / 118 files already formatted (the `COM812`-vs-formatter warning is the long-standing pyproject configuration nit, unrelated to this cycle's edits).
- `uv run ruff check .` — pass / All checks passed.
- pytest deliberately not run per the dispatch instructions and `AGENTS.md` line 14.

### Verification outcome

`logic accepted; awaiting comment pass`

Top-level `Status:` line stays `fix-implemented (awaiting comment pass)` (Worker 2's value); no checkbox tick in `docs/review/review-0_0_7.md` until the comment pass and changelog disposition land and verify.

---

## Comment/docstring pass

### Files touched
- `django_strawberry_framework/management/commands/export_schema.py:20-23` — Sharpened the `--path` argparse `help` from "Optional path to export" to "Optional file path to write the SDL to; rejects empty values" so a user running `manage.py help export_schema` sees both the optional-flag framing and the empty-string rejection up front. The help text now signposts the three-branch contract before the user reads the docstring.
- `django_strawberry_framework/management/commands/export_schema.py:30-37` — Expanded the `handle()` one-line docstring "Resolve the dotted-path schema symbol, print SDL to stdout or write it to --path." into a three-branch summary that names each gate explicitly: ``--path`` omitted → stdout; ``--path ""`` → ``CommandError`` per CHANGELOG-23; ``--path <file>`` → UTF-8 SDL write. The old wording only described two implicit branches (stdout-or-write); the new wording matches the post-fix three-branch gate at `export_schema.py:39-49`.

### Per-finding dispositions
- Medium 1 (`--path ""` silently routes to stdout): docstring updated to name all three branches and cite the CHANGELOG-23 contract by name; `--path` argparse `help` updated to signal the empty-value rejection.
- Low 1 (stdout-path UTF-8 asymmetry): no comment edit — Worker 1's deferral note at artifact line 58 is a forward-looking trigger condition (Windows-packaging / non-ASCII-description card), not a comment that the file currently misdocuments.
- Low 2 (`import pathlib` vs. `from pathlib import Path`): no comment edit — Worker 1's deferral note at artifact line 64 is a forward-looking trigger condition (second `pathlib.Path` site or project-pass DRY cycle), not a comment that the file currently misdocuments.

### Validation run
- `uv run ruff format .` — pass / 118 files left unchanged
- `uv run ruff check --fix .` — pass / All checks passed

### Notes for Worker 3
- The expanded `handle()` docstring is four lines (a short opening sentence + a three-clause description); the line-length budget is comfortable at 110.
- The new `--path` help string is 60 characters and fits the existing argparse triple-quoted block without rewrapping.
- No source-logic edits in this sub-pass; the three-branch gate at `export_schema.py:39-49` is unchanged from the logic-pass diff Worker 3 already verified at `## Verification (Worker 3)` line 118.

---

## Changelog disposition

### State
`Not warranted`.

### Reason
The cycle's M1 fix is a correctness fix on NEW (intra-cycle) code shipped in the 0.0.7 release that this review cycle itself is gating — the `if path:` truthy-string gate landed in commit `300e281` / `5f0ffa5` (the 0.0.7 cut) and the `--path ""` silent-stdout failure mode it introduced has never been exposed to a consumer because 0.0.7 has not been released. Cycle 1 (`rev-_django_patches.md`) established the intra-cycle pre-release correction precedent: when a review finding fixes NEW code that has not yet shipped, the fix is folded into the same release's correction set without a `CHANGELOG.md` entry because the consumer-visible release notes describe the post-correction shape, not the intermediate buggy intra-cycle state. The same precedent applies here: the 0.0.7 `CHANGELOG.md` "Added" / "Changed" entries at `CHANGELOG.md:19-26` already describe `export_schema` as the post-correction shape (`--path` "requires a value when the flag is given"), so the M1 fix tightens the implementation to match what the release notes already say — no new consumer-visible delta to record.

Three lined-up citations (cycle-1 intra-cycle precedent + AGENTS.md "Do not update CHANGELOG.md unless explicitly instructed" at line 21 + `docs/review/review-0_0_7.md` silence on changelog authorization for this cycle's M1) close the disposition.

### What was done
No `CHANGELOG.md` edit. The CHANGELOG-23 entry already reads as the post-correction contract; the implementation now enforces what the release notes already say.

### Validation run
- `uv run ruff format .` — pass / 118 files left unchanged
- `uv run ruff check --fix .` — pass / All checks passed

---

## Iteration log

## Verification (Worker 3, pass 2)

### Comment-pass verification outcome

- `git diff -- django_strawberry_framework/management/commands/export_schema.py` confirms the comment-pass diff is exactly two hunks: argparse `--path` `help` at line 22 changed from `"Optional path to export"` to `"Optional file path to write the SDL to; rejects empty values"`, and the `handle()` docstring at lines 26-32 expanded from the one-line summary to a four-line three-branch description naming each gate (``--path`` omitted → stdout; ``--path ""`` → `CommandError` per CHANGELOG-23; ``--path <file>`` → UTF-8 SDL write). No logic edit in this sub-pass — the three-branch gate at lines 33-55 is byte-identical to the logic-pass diff Worker 3 already verified.
- Comment accuracy re-checked against the post-edit source at `django_strawberry_framework/management/commands/export_schema.py:25-55`: the docstring's three-branch description is faithful to the actual control flow (line 46 `if path is None:` → stdout + return; line 49 `if not path:` → `CommandError("--path requires a non-empty value")`; line 52 fall-through → `pathlib.Path(path).write_text(...)`); the CHANGELOG-23 citation in the docstring matches `CHANGELOG.md:23` verbatim ("requires a value when the flag is given"); the `--path` help string signals the empty-value rejection up front so `manage.py help export_schema` users see the contract before reading the docstring.
- L1 (stdout-path UTF-8 asymmetry) and L2 (`import pathlib` vs. `from pathlib import Path`) per-finding dispositions correctly recorded as "no comment edit" — both are forward-looking deferrals with named trigger conditions, not comments that the file currently misdocuments.

### Changelog verification outcome

`git diff -- CHANGELOG.md` empty, matching the `Not warranted` state. Three citations recorded:
1. AGENTS.md line 21 ("Do not update CHANGELOG.md unless explicitly instructed") — quoted verbatim.
2. `docs/review/review-0_0_7.md` silence on changelog authorization for this cycle's M1 — confirmed by absence of any changelog-authorization clause for `export_schema.py` in the active plan.
3. Cycle 1 (`rev-_django_patches.md`) intra-cycle pre-release correction precedent — the M1 fix tightens NEW code (the `if path:` truthy gate) that shipped in the same 0.0.7 cut at `300e281` / `5f0ffa5` and has not been released externally, so the consumer-visible CHANGELOG entries at `CHANGELOG.md:19-26` already describe the post-correction shape.

Three-leg citation comfortably clears the two-citation bar; the cycle-1 precedent is the load-bearing leg (pre-release intra-cycle correction).

### Validation run
- `git diff -- django_strawberry_framework/management/commands/export_schema.py` — comment-pass diff matches the artifact's claim exactly (argparse help + handle docstring; no logic edit).
- `git diff -- CHANGELOG.md` — empty, matching `Not warranted` disposition.
- `uv run ruff format --check .` — pass / 118 files already formatted.
- `uv run ruff check .` — pass / All checks passed.

### Verification outcome

`cycle accepted; verified`

Top-level `Status: verified`; checkbox for `export_schema.py` ticked at `docs/review/review-0_0_7.md:102`.
