# Review: `django_strawberry_framework/management/commands/export_schema.py`

Status: verified

## DRY analysis

- None — the file is a single 32-line `handle()` plus a 7-line `add_arguments()`; the only repeated shape is the `raise CommandError(str(e)) from e` pattern (two call sites: `export_schema.py:39-40` import-symbol wrap, `export_schema.py:54-55` write `OSError` wrap), and those two `except` blocks catch different exception families against different operations. Folding them into a shared `_reraise_as_command_error` helper would hide the per-branch exception tuple at the only two sites that need to see it; not a consolidation win. The sibling command `inspect_django_type.py` is the cross-file comparison point (folder pass `rev-management__commands.md`), not a local hoist.

## High:

None.

## Medium:

None.

## Low:

### Docstring mis-attributes the empty-string `--path` branch to the wrong CHANGELOG contract

The `handle()` docstring (`export_schema.py:26-33`) describes the `--path ""` (empty-string value) branch and cites the `CHANGELOG.md` `[0.0.7] Changed` "manage.py export_schema --path now requires a value when the flag is given" line as its governing contract. That CHANGELOG entry (`CHANGELOG.md:117`) governs a *different* code path: dropping `nargs="?"` so a **bare** `--path` (flag with no following token) is rejected by **argparse at parse time**. The bare-flag case never reaches `handle()` — it short-circuits in the parser (pinned by `tests/management/test_export_schema.py:64-67`, whose comment at `tests/management/test_export_schema.py:73-74` explicitly notes "it short-circuits in argparse, before any project schema matters").

The branch the docstring actually describes — the runtime `if not path: raise CommandError("--path requires a non-empty value")` guard at `export_schema.py:50-51` — handles the empty-string `--path ""` value, a distinct concern pinned by `examples/fakeshop/tests/test_export_schema.py:50-53`. The docstring also quotes the error text as "...requires a value when the flag is given," which is the CHANGELOG prose, not the code's actual message ("--path requires a non-empty value").

Why it matters: a reader auditing the empty-string branch against the cited CHANGELOG line finds a non-matching contract and a non-matching message string, and could mistake the parse-time bare-flag rejection for the runtime empty-string guard (or wrongly conclude the runtime guard is redundant with argparse). Comment-pass tier only — no logic change.

Recommended change (comment pass): rewrite the third clause of the `handle()` docstring so the `--path ""` branch points at its real contract. Suggested replacement text for the docstring body (Worker 2 lifts verbatim):

```django_strawberry_framework/management/commands/export_schema.py:26:33
        """Resolve the dotted-path schema symbol and emit SDL.

        Routes through three branches: ``--path`` omitted prints SDL to
        stdout; ``--path ""`` (empty-string value) raises ``CommandError``
        with "--path requires a non-empty value"; ``--path <file>`` writes
        UTF-8 SDL to the named path. A bare ``--path`` with no following
        value is rejected earlier by argparse, before ``handle`` runs (the
        ``[0.0.7] Changed`` "--path now requires a value when the flag is
        given" contract).
        """
```

## What looks solid

### DRY recap

- **Existing patterns reused.** Reuses Strawberry's own `import_module_symbol(default_symbol_name="schema")` for dotted-path resolution (`export_schema.py:35-38`) and `print_schema` for SDL emission (`export_schema.py:45`) — no re-implemented importer or printer. `CommandError` / `BaseCommand` / `CommandParser` are Django's canonical management-command surface; no local wrappers.
- **New helpers considered.** A `_reraise_as_command_error(exc)` helper over the two `raise CommandError(str(e)) from e` sites (`export_schema.py:39-40`, `:54-55`) was evaluated and rejected — the two sites catch unrelated exception families (`ImportError`/`AttributeError` from symbol resolution vs `OSError` from file write) against unrelated operations; a shared helper would obscure the per-branch `except` tuple without removing real duplication.
- **Duplication risk in the current file.** The two `str(e)`-wrapping `except` blocks are intentional sibling shapes, not near-copies (different caught types, different operations); correct as written.

### Other positives

- **`handle(self, *args, **options)` signature is correct.** Matches `BaseCommand.handle`'s contract; reads the positional via `options["schema"]` (scalar, post the 0.0.7 `nargs=1` removal recorded at `CHANGELOG.md:116`) and the flag via `options.get("path")`. The `["schema"]` direct-index vs `.get("path")` asymmetry is correct: `schema` is a required positional argparse always populates, while `--path` is optional and absent-by-default — `.get` returns `None` when the flag is omitted, which is exactly the stdout-routing sentinel the `if path is None` branch keys on (`export_schema.py:47-49`).
- **Exhaustive, correctly-scoped exception wrapping.** `import_module_symbol` raises `ModuleNotFoundError`/`ImportError` (bad module) or `AttributeError` (bad symbol) — both caught and re-raised as `CommandError` (`export_schema.py:39-40`). Verified against the installed Strawberry source: with `default_symbol_name="schema"` always truthy, the importer's `ValueError("Selector does not include a symbol name")` branch is unreachable from this call site, so the `(ImportError, AttributeError)` tuple is complete. File-write failures are wrapped to `CommandError` (`export_schema.py:54-55`), closing the consistency gap noted at `CHANGELOG.md:135`.
- **Three-way `--path` dispatch is clean and ordered correctly.** `None` (flag omitted) → stdout; falsy-but-not-None (empty string) → `CommandError`; truthy → UTF-8 write with explicit `encoding="utf-8"` and a `self.style.SUCCESS` confirmation (`CHANGELOG.md:115`). The `Schema`-instance guard (`export_schema.py:42-43`) rejects a resolved-but-wrong symbol before printing.
- **Test discipline across two trees.** Package-side `tests/management/test_export_schema.py` pins the four parse/resolution failure modes (unimportable module, missing attribute, non-`Schema` symbol, missing positional, bare `--path`); the fakeshop project suite `examples/fakeshop/tests/test_export_schema.py` pins stdout default, file write, missing-parent-dir `OSError`, and empty-string `--path` against the real `config.schema`. The split honors AGENTS.md "prefer the example project" — the parse-only bare-flag case stays package-side because it short-circuits before any project schema matters (documented at `tests/management/test_export_schema.py:70-74`).
- **GLOSSARY accurate.** `docs/GLOSSARY.md:1193` describes the full `CommandError` surface (unimportable path, non-`Schema` symbol, missing positional, bare `--path`, empty-string `--path`, file-write `OSError`) and the stdout/file/`SUCCESS` routing verbatim against the source; no drift.

### Summary

A 56-line management command that is logically clean: correct `BaseCommand.handle` signature, scalar positional read, a correctly-ordered three-way `--path` dispatch (omitted→stdout, empty→`CommandError`, file→UTF-8 write+`SUCCESS`), and exhaustive exception wrapping (`ImportError`/`AttributeError` from symbol resolution, `OSError` from write) into `CommandError`. The `Schema`-instance guard and explicit UTF-8 encoding are correct. Test coverage is thorough across both the package and fakeshop trees with a well-reasoned split, and the GLOSSARY entry matches the source. The single finding is a Low comment-pass defect: the `handle()` docstring attributes the runtime empty-string `--path` branch to the `[0.0.7] Changed` CHANGELOG line that actually governs the parse-time bare-flag rejection, and quotes the CHANGELOG prose instead of the code's real error message. No logic change required.

---

## Fix report (Worker 2)

Logic pass (first Worker 2 pass for this standard `under-review` cycle).

### Files touched
- None. Worker 1 recorded High 0 / Medium 0 / Low 1, and the single Low is a comment/docstring correction (the `handle()` docstring at `export_schema.py:26-33` mis-attributes the runtime empty-string `--path ""` branch to the `[0.0.7] Changed` CHANGELOG line that governs the parse-time bare-flag rejection, and quotes CHANGELOG prose instead of the code's real message "--path requires a non-empty value"). There are no logic (High/Medium/Low-logic) findings, so no source edits are made in the logic pass.

### Tests added or updated
- None. No behavior change in this pass.

### Validation run
- `uv run ruff format .` — pass (267 files left unchanged)
- `uv run ruff check --fix .` — pass (All checks passed; the standing COM812-vs-formatter warning is config noise, not a change)
- Cycle diff `git diff f3b8aef29da05ee97ff276fd1e0bc79d851b4363 -- django_strawberry_framework/management/commands/export_schema.py` is empty, confirming zero source edits.
- No pytest run (per hard rules).

### Notes for Worker 3
- No shadow file used during this pass.
- No false-premise rejections — the Low finding is acknowledged as valid and carried forward; it is a comment-pass defect and is intentionally NOT addressed in this logic pass (per worker-2.md "Do not update comments before logic is approved"). The docstring fix at `export_schema.py:26-33` is deferred to the comment pass, which runs only after Worker 3 accepts the logic pass. Suggested verbatim replacement text is recorded in the `## Low` section.
- `uv.lock` discipline: `uv.lock` was already modified in the working tree at pass start (pre-existing concurrent work, AGENTS.md #33); the two `uv run` invocations did NOT add further churn (diff stat unchanged at 1/1), so no `git restore uv.lock` was needed and nothing of mine touched it.
- Other working-tree dirt at pass start (`django_strawberry_framework/__init__.py`, `docs/bug_hunt/dicta.md`, `pyproject.toml`, untracked rev-*/review-* docs) is out-of-scope concurrent work, left untouched.

---

## Verification (Worker 3)

LOGIC VERIFY pass (interim; cycle is mid-flow, not terminal). Docstring text is intentionally NOT verified here — that is the later comment-verify. Verified the source logic only.

### Logic verification outcome

Independently re-derived every named logic invariant against source + upstream callee; no missed High/Medium found.

- **Exception-wrap completeness — confirmed complete.** Re-read the installed importer at `.venv/.../strawberry/utils/importer.py::import_module_symbol`. With `default_symbol_name="schema"` (always truthy), the no-`:` selector takes the `elif default_symbol_name:` branch, so the `else: raise ValueError("Selector does not include a symbol name")` is structurally unreachable from this call site — the artifact's claim holds against the real source, not just its prose. `importlib.import_module` raises `ModuleNotFoundError` (an `ImportError` subclass) for a bad module; `getattr` raises `AttributeError` for a bad symbol. The `except (ImportError, AttributeError)` tuple at `export_schema.py:39` catches both families exhaustively. File-write failures wrapped via `except OSError` at `export_schema.py:54`.
- **`handle()` signature — correct.** `BaseCommand.handle(self, *args, **options)` is the canonical contract (`.venv/.../django/core/management/base.py:616`); the source's `handle(self, *args: object, **options: object)` matches.
- **Argument parsing / `--path` branch behavior — correct.** `schema` is a required positional argparse always populates → direct `options["schema"]` index is safe. `--path` is optional with no `default`/`nargs`, so argparse stores `None` when omitted → `options.get("path")` returns `None`. The three-way dispatch is correctly ORDERED: `path is None` (omitted → stdout) is tested first, so the empty-string `""` value (falsy-but-not-None) can only reach the `not path` guard → `CommandError("--path requires a non-empty value")`; truthy → UTF-8 write + `SUCCESS`. A bare `--path` (no following token) is rejected by argparse at parse time before `handle` runs (no `nargs="?"`), so it never reaches the runtime guard — distinct from the empty-string path.
- **Schema import-path resolution — correct.** `import_module_symbol(options["schema"], default_symbol_name="schema")` resolves a dotted path; the `isinstance(schema_symbol, Schema)` guard (`export_schema.py:42`) rejects a resolved-but-wrong symbol before `print_schema`.
- **Low finding — correctly deferred, not a logic defect.** The single Low is a docstring mis-attribution (comment-pass tier); Worker 2 made zero source edits and carried it forward verbatim. No logic change is warranted, consistent with High 0 / Medium 0.

### DRY findings disposition
DRY = None. Re-confirmed the two `raise CommandError(str(e)) from e` sites catch unrelated exception families (`ImportError`/`AttributeError` from symbol resolution at `:39-40` vs `OSError` from file write at `:54-55`) against unrelated operations; a `_reraise_as_command_error` helper would obscure the per-branch `except` tuple without removing real duplication. No hoist warranted. Sibling-command cross-file comparison (`inspect_django_type.py`) is the folder-pass concern, not a local-cycle item.

### Temp test verification
- No temp test files created. The logic claims were verifiable by reading the source plus the upstream `import_module_symbol` and `BaseCommand.handle` definitions; no behavioral suspicion required a temp test.
- Disposition: n/a.

### Verification outcome
`logic accepted; awaiting comment pass` — sets top-level `Status: logic-accepted`. Zero source edits this pass confirmed: `git diff f3b8aef29da05ee97ff276fd1e0bc79d851b4363 -- django_strawberry_framework/management/commands/export_schema.py` is empty. Checklist box NOT marked (cycle is not terminal; routes back to Worker 2 for the comment pass).

---

## Comment/docstring pass

Comment pass (second Worker 2 pass; Worker 3 set `Status: logic-accepted`). Docstring/comment only — no logic change.

### Files touched
- `django_strawberry_framework/management/commands/export_schema.py:26-35` — rewrote the third clause of the `handle()` docstring. The `--path ""` (empty-string value) branch now cites the code's real error message verbatim (`"--path requires a non-empty value"`, matching the runtime guard at `export_schema.py:51`) instead of the `[0.0.7]` CHANGELOG prose. The `[0.0.7] Changed` "--path now requires a value when the flag is given" contract is re-attributed to its real subject: the parse-time argparse rejection of a **bare** `--path` (no following token), which short-circuits before `handle` runs. This is Worker 1's verbatim suggested replacement from the `## Low` section.

### Per-finding dispositions
- Low 1 (docstring mis-attributes the empty-string `--path` branch to the wrong CHANGELOG contract): fixed. Applied Worker 1's verbatim replacement. Verified against source: the three-way dispatch (`None`→stdout `:47-48`, empty-string→`CommandError("--path requires a non-empty value")` `:50-51`, file→UTF-8 write `:52-56`) and the parse-time bare-flag rejection (no `nargs="?"` on the `--path` arg, `:19-23`) both match the corrected docstring text. The real error-message string and the bare-flag-vs-empty-string distinction now read correctly.

### Validation run
- `uv run ruff format .` — pass (267 files left unchanged; the COM812-vs-formatter warning is standing config noise, not a change)
- `uv run ruff check --fix .` — pass (All checks passed)
- Cycle diff `git diff f3b8aef29da05ee97ff276fd1e0bc79d851b4363 -- django_strawberry_framework/management/commands/export_schema.py` shows ONLY the docstring hunk (lines 27-35), zero logic-line changes.
- No pytest run (per hard rules).

### Notes for Worker 3
- No shadow file used during this pass.
- No false-premise rejections — the Low finding was valid and is now fixed.
- The corrected docstring matches the real code behavior: the empty-string message string is `"--path requires a non-empty value"` (exact match to `export_schema.py:51`), and the `[0.0.7]` contract is correctly tied to the parse-time bare-`--path` rejection, not the runtime empty-string guard.
- `uv.lock` discipline: `uv.lock` was already modified in the working tree at pass start (pre-existing concurrent work, AGENTS.md #33). Diff-stat snapshotted before and after the two `uv run` invocations was unchanged (1 insertion / 1 deletion both times), so my ruff runs added no further churn and no `git restore uv.lock` was needed.

---

## Verification (Worker 3, pass — comment-verify)

COMMENT VERIFY pass (interim; cycle is mid-flow, not terminal — routes back to Worker 2 for the changelog disposition pass). Incoming `Status: fix-implemented (awaiting changelog disposition)` → comment-verify template per worker-3.md.

### Diff is docstring/comment-ONLY
`git diff f3b8aef29da05ee97ff276fd1e0bc79d851b4363 -- django_strawberry_framework/management/commands/export_schema.py` shows a single hunk, entirely inside the `handle()` docstring (lines 27-35 region). Zero logic-line changes — the `try`/`except`, the `isinstance` guard, the three-way `--path` dispatch, and both `CommandError` raises are byte-identical to baseline. Confirmed.

### Corrected docstring text verified TRUE against source
- **Quoted error string matches the real runtime guard.** Docstring (`export_schema.py:29-30`): `--path ""` (empty-string value) "raises ``CommandError`` with "--path requires a non-empty value"". Source `export_schema.py:53`: `raise CommandError("--path requires a non-empty value")` — exact, verbatim match. The branch the docstring describes is the genuine empty-string branch: `path is None` short-circuits to stdout at `:49-51` first, so a falsy-but-not-None `""` is the only value that reaches the `if not path:` guard at `:52-53`. Correct.
- **Re-attributed `[0.0.7] Changed` contract is correct.** Docstring (`:31-34`) now ties the "--path now requires a value when the flag is given" contract to "a bare ``--path`` with no following value is rejected earlier by argparse, before ``handle`` runs." Confirmed against source: the `--path` arg (`:19-23`) carries `type=str` with no `nargs`/`default`, so argparse requires a following token and rejects a bare `--path` at parse time — it never reaches `handle`. The empty-string `""` (a present token that is empty) is the distinct case the runtime guard handles. The bare-flag-vs-empty-string distinction is real and correctly drawn; this resolves the original Low's mis-attribution (the docstring no longer cites the CHANGELOG bare-flag contract for the runtime empty-string branch, and no longer quotes CHANGELOG prose as the error message).

### No NEW inaccuracy introduced
- The three-branch summary still matches source exactly: `--path` omitted → stdout (`:49-51`); `--path ""` → `CommandError` (`:52-53`); `--path <file>` → UTF-8 write (`:54-58`, explicit `encoding="utf-8"`). No claim was added that the source does not support, and no previously-accurate clause was broken.

### Verification outcome
`comments accepted; awaiting changelog disposition` — sets top-level `Status: comments-accepted`. Diff confirmed docstring-only; corrected text (real error string + re-attributed bare-flag contract) is TRUE against source; no new inaccuracy. Checklist box NOT marked (cycle is not terminal; routes back to Worker 2 for the changelog disposition pass).

---

## Changelog disposition

Changelog pass (third Worker 2 pass; Worker 3 set `Status: comments-accepted`). No source touches this pass.

### State
`Not warranted`.

### Reason
The only edit this cycle is an internal docstring correction (the `handle()` docstring re-attribution at `export_schema.py:26-35`): no behavior change, no public-API change, no consumer-visible surface change. The corrected docstring describes the *same* runtime behavior that already shipped — it only fixes which contract the empty-string `--path` branch is attributed to and quotes the real error string. This is squarely the "docstring polish / additive wording inside an existing pinned contract" case in worker-2.md's `Not warranted` clause. Both required citations apply:

- **`AGENTS.md` #21** — "Do not update CHANGELOG.md unless explicitly instructed." Neither the dispatch prompt nor the artifact authorizes a `CHANGELOG.md` edit this cycle.
- **Active plan's silence** — the active review plan (`docs/review/review-0_0_10.md`) does not authorize a changelog edit for this per-file cycle. Per the changelog dicta, per-file cycles are NEVER the authorising scope and forward any genuine `CHANGELOG.md` drift to the project pass; here there is no drift to forward, because no consumer-visible change occurred.

### What was done
No `CHANGELOG.md` edit. `git diff -- CHANGELOG.md` is empty; `git status` confirms `CHANGELOG.md` is not modified in the working tree.

### Validation run
- `uv run ruff format .` — pass (no-changes; no source touched this pass)
- `uv run ruff check --fix .` — pass (All checks passed; standing COM812-vs-formatter warning is config noise, not a change)
- No pytest run (per hard rules).
- `uv.lock` discipline: `uv.lock` was already modified at pass start (pre-existing concurrent work, AGENTS.md #33); diff-stat unchanged before/after the two `uv run` invocations, so no `git restore uv.lock` needed.

---

## Verification (Worker 3, pass — terminal-verify)

TERMINAL VERIFY pass. Incoming `Status: fix-implemented` (bare) → terminal-verify template per worker-3.md. This closes the cycle: confirms logic + comments + changelog disposition all hold together and nothing regressed. Sets top-level `Status: verified` and marks the checklist box.

### Whole-cycle finding accounting
- **High 0 / Medium 0** — confirmed in the prior logic-verify pass (re-derived exception-wrap completeness, `handle` signature, three-way `--path` dispatch order, schema-import resolution against source + upstream `import_module_symbol`/`BaseCommand.handle`). No new logic surface introduced this cycle to re-open.
- **Low 1 (docstring mis-attribution) — fixed via docstring.** Resolved in the comment pass and accepted in the comment-verify pass. Re-confirmed TRUE against source this pass (see below). This is the single edit of the cycle.
- No findings dispositioned as `rejected` / `false-premise` — nothing to re-audit for contradicting evidence.

### Final cycle diff is docstring-ONLY, no logic/test change
`git diff f3b8aef29da05ee97ff276fd1e0bc79d851b4363 -- django_strawberry_framework/management/commands/export_schema.py` shows a single hunk entirely inside the `handle()` docstring (lines 28-34 region, 5 insertions / 3 deletions). Every logic line — the `try`/`except (ImportError, AttributeError)`, the `isinstance(schema_symbol, Schema)` guard, the three-way `--path` dispatch, both `CommandError` raises, the UTF-8 write — is byte-identical to baseline. Broad `git diff --stat f3b8aef29da05ee97ff276fd1e0bc79d851b4363 -- django_strawberry_framework/ tests/ examples/ docs/GLOSSARY.md CHANGELOG.md` reports ONLY `export_schema.py` (1 file, 5/3). No test tree touched (none of `tests/`, `examples/fakeshop/tests/`, `examples/fakeshop/test_query/` appears in the stat) — correct, since the cycle was comment-only with zero behavior change.

### Corrected docstring re-confirmed TRUE against source (terminal re-read)
- Quoted error string `"--path requires a non-empty value"` (docstring `:30`) is the exact, verbatim match to the runtime guard `raise CommandError("--path requires a non-empty value")` at `export_schema.py:53`.
- The branch the docstring describes is the genuine empty-string branch: `path is None` (omitted) short-circuits to stdout at `:49-51` before the `if not path:` guard at `:52-53`, so a falsy-but-not-None `""` is the only value that reaches it.
- The re-attributed `[0.0.7] Changed` contract (docstring `:31-34`) is now correctly tied to the parse-time bare-`--path` rejection: the `--path` arg (`:19-23`) carries `type=str` with no `nargs`/`default`, so argparse requires a following token and rejects a bare `--path` before `handle` runs. The bare-flag-vs-empty-string distinction is real and correctly drawn; the original Low's two defects (wrong CHANGELOG contract attributed to the runtime branch, CHANGELOG prose quoted as the error message) are both resolved with no new inaccuracy introduced.

### Changelog `Not warranted` justified with both citations
`git diff f3b8aef29da05ee97ff276fd1e0bc79d851b4363 -- CHANGELOG.md` is EMPTY (confirmed this pass), consistent with `Not warranted`. The disposition cites BOTH required sources: `AGENTS.md` #21 ("Do not update CHANGELOG.md unless explicitly instructed") AND the active plan's silence (`docs/review/review-0_0_10.md` does not authorize a changelog edit for this per-file cycle; per-file cycles are never the authorising scope). The "internal-only" framing is honest — the cycle's sole edit is a docstring re-attribution describing the *same* shipped runtime behavior; no public-API surface changed, so `Not warranted` is the correct state (not `Warranted but deferred`). Both-citation and diff-empty and honest-framing checks pass.

### Nothing regressed
The diff touches only the docstring; the logic that the logic-verify pass independently re-derived is unchanged byte-for-byte. No test was added or modified (none required — no behavior change). Ruff format-check + check reported clean across all three Worker 2 passes. No `tests/`, `examples/`, `docs/GLOSSARY.md`, or `CHANGELOG.md` drift attributable to this cycle.

### Verification outcome
`cycle accepted; verified` — sets top-level `Status: verified` AND marks the checklist box for `management/commands/export_schema.py` in `docs/review/review-0_0_10.md`. The full standard cycle is sound for closure: H0/M0 confirmed, the single Low fixed via docstring and re-confirmed true against source, final cycle diff is docstring-only with no logic/test changes, `Not warranted` changelog disposition is justified with both citations against an honest internal-only framing, and nothing regressed.
