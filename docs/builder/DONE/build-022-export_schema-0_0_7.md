# Package build plan: export_schema / 0.0.7 (022) — residual-completion cycle

Spec source: `docs/SPECS/spec-022-export_schema-0_0_7.md` (already archived; the card shipped in `0.0.7` on 2026-05-27)
Target release: `0.0.7` (shipped; the package is at `0.0.14`)
Build rule: one cohort at a time. Plan first, build second, review third, reconcile fourth.
DRY rule: every cohort must justify shared/duplicated patterns before merging.
Pre-flight: passed on 2026-08-18; baseline: a concurrent `spec-021` residual cycle is mid-flight (below); cleanup: **no artifact deletion, no worker-memory reset** — see "Pre-flight exceptions".

## Cycle shape: this is a review round, not a fresh build

`docs/builder/BUILD.md` `## Review rounds` is the governing shape. The three spec slices shipped in `0.0.7`; their code is on `main`. The input to this cycle is **Worker 0's own verification of the spec against `HEAD`**, recorded verbatim under `## Verified findings` below, standing in for a maintainer review document. Two obligations the original cycle never discharged drive it:

1. `docs/builder/BUILD.md` `## Spec rationale extraction` — the pre-flight step-7 rationale MOVE never ran for this spec. `docs/SPECS/appx/spec-022-export_schema-0_0_7-rationale.md` does not exist, and the spec still carries its whole deliberative layer.
2. `docs/builder/BUILD.md` `## Spec reconciliation` — the command's shipped contract moved under the spec in **eight** post-ship commits between 2026-05-22 and 2026-08-16 and was never reconciled.

The maintainer's standing instruction for this cycle, recorded here because it decides every finding's resolution direction: **the spec states the current contract; how it got there goes in the rationale file.** No escalation is therefore open on F1-F5.

### Pre-flight exceptions (steps 3 and 5 deliberately not performed)

A round's pre-flight explicitly skips step 3's artifact reset (`BUILD.md` `### Cohorting, naming, and closure`, "Pre-flight for a round"), and `worker-0.md` names artifact deletion "the one irreversible pre-flight mistake". Two further reasons apply here, both concurrent-session facts:

- **Step 3 (artifact reset) not run.** A concurrent session is mid-flight on the `spec-021` residual cycle: `docs/builder/build-021-apps-0_0_7.md` and `docs/builder/bld-review-1-rationale_and_spec_reconciliation.md` are untracked and live, and `docs/builder/build-020-list_field-0_0_7.md` is staged-deleted with an untracked copy under `docs/builder/DONE/`. `AGENTS.md` rule 34 forbids touching any of them.
- **Step 5 (scratch clear) partially not run.** `docs/shadow/` and `docs/builder/temp-tests/` are already empty. `docs/builder/worker-memory/worker-1.md` (1713 B) and `worker-3.md` (1334 B) hold the concurrent `spec-021` cycle's live state; clearing them would destroy it. Left in place. The contamination risk is acceptable and one-directional: a worker reads only its **own** role's file, and `spec-021` is the immediately-preceding residual cycle of the same shape, so its entries are continuity rather than noise.

Verified instead, as the round's pre-flight requires: none of this cycle's five artifact paths already exists.

### Artifact naming departs from `BUILD.md`'s fixed integration/final names

`BUILD.md` `## Build artifact naming` pins `docs/builder/bld-integration.md` and `docs/builder/bld-final.md` as exact paths. This cycle uses `bld-integration-022.md` and `bld-final-022.md`, and names its round artifacts `bld-review-<R>-spec_022_*.md`. Reason: the concurrent `spec-021` cycle's plan lists the unsuffixed paths in its own artifact list and has not yet created them. Two cycles cannot both own one path. The `022` suffix is the smallest change that keeps both cycles' artifacts attributable; recorded here rather than silently taken.

### Baseline-dirty, out-of-scope (never edit, never revert — `AGENTS.md` rule 34)

- `docs/SPECS/spec-021-apps-0_0_7.md` (modified by the concurrent `spec-021` cycle)
- `docs/SPECS/appx/spec-021-apps-0_0_7-rationale.md` (untracked, concurrent)
- `docs/builder/build-021-apps-0_0_7.md` (untracked, concurrent)
- `docs/builder/bld-review-1-rationale_and_spec_reconciliation.md` (untracked, concurrent)
- `docs/builder/build-020-list_field-0_0_7.md` (staged deleted by a concurrent session)
- `docs/builder/DONE/build-020-list_field-0_0_7.md` (untracked, concurrent)
- `docs/builder/bld-003-final.md` (tracked leftover from the spec-003 residual cycle; not this cycle's)
- `docs/feedback.md` (modified, concurrent)

### Concurrent-writable tracked binary / generated files

Churn in these is **not** presumed to be this cycle's output (`BUILD.md` `### Tracked binary / generated files`): `examples/fakeshop/db.sqlite3`, `KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md`. R2 legitimately diverges all four; verify by two-consecutive-regenerate byte-stability, never by "`git diff` is clean".

**The concurrent `spec-021` cycle's own R2 targets the same DB and the same three rendered docs.** R2 here therefore applies its ORM writes **on top** of whatever state the DB is in, never reverting, and hands the mixed diff to the maintainer to reconcile at commit (`BUILD.md` `### Tracked binary / generated files`, final bullet). R2 touches exactly one `GlossaryTerm` row and must not touch any kanban table.

## Pre-flight record

| Step | Result |
|---|---|
| 1 working-tree baseline | Eight concurrent paths dirty (above); nothing else. |
| 2 `scripts/review_inspect.py` | Not run — no cohort adds or edits package `.py`. `BUILD.md` `### When to run the helper` scopes it to source logic; recorded skip. |
| 3 artifact reset | Deliberately skipped; see exceptions above. Confirmed the five new paths are free. |
| 4 `.gitignore` scratch paths | `docs/shadow/` (`.gitignore:174`), `docs/builder/worker-memory/` (`:188`), `docs/builder/temp-tests/` (`:192`) all listed. |
| 5 scratch cleared | `docs/shadow/` and `docs/builder/temp-tests/` already empty. `worker-memory/` deliberately preserved; see exceptions above. |
| 6 `check_spec_glossary` | `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-022-export_schema-0_0_7.md` -> `OK: 13 terms`, exit 0. |
| 7 rationale extracted | **NOT DONE — it is this cycle's R1.** |

## Verified findings

Worker 0 read the current source behind every finding before writing this plan (`BUILD.md` `### Worker 0 verifies every finding against source before dispatching`). Each carries whether the condition holds at `HEAD` and the symbol-qualified evidence. Counts are measured, not read (`BUILD.md` `## Claims are proven mechanically, never accepted on prose`); the command that produced each is cited inline.

**The whole of `## Findings that do NOT hold` is the load-bearing result: the code shipped the spec exactly.** `git show d780726f:django_strawberry_framework/management/commands/export_schema.py` is byte-for-byte the shape [Decision 2](../SPECS/spec-022-export_schema-0_0_7.md#decision-2--command-class-shape) pins, and `git show d780726f:tests/management/test_export_schema.py | grep -c '^def test_'` prints **7**, with all seven names matching the [Test plan](../SPECS/spec-022-export_schema-0_0_7.md#test-plan) verbatim. Every divergence below post-dates the ship commit. Nothing was skipped, dropped, or forgotten.

### F1 — HOLDS. The argparse shape diverged post-ship (`nargs` dropped on both arguments)

- **Spec claim:** [Decision 2](../SPECS/spec-022-export_schema-0_0_7.md#decision-2--command-class-shape) pins `parser.add_argument("schema", nargs=1, ...)` and `parser.add_argument("--path", nargs="?", ...)`, and [Decision 3](../SPECS/spec-022-export_schema-0_0_7.md#decision-3--symbol-resolution-through-the-shared-_imports-command-helper) pins the `options["schema"][0]` index. Propagated to the Slice 1 checklist, the `Method signatures` code block, [Decision 2](../SPECS/spec-022-export_schema-0_0_7.md#decision-2--command-class-shape)'s third rejected alternative ("Default `nargs=None` … Rejected: the upstream uses `nargs=1`"), and Definition of done item 2.
- **`HEAD`:** `django_strawberry_framework/management/commands/export_schema.py::Command.add_arguments` declares `parser.add_argument("schema", type=str, help="The schema location")` — no `nargs` — and `--path` likewise carries no `nargs`. `::Command.handle` reads `options["schema"]` directly.
- **Provenance:** `9e11eb30` (2026-05-22) "Refactor export_schema command argument handling and improve user feedback". Both changes are already published in `CHANGELOG.md`'s `[0.0.7] ### Changed` section as "Post-ship polish on `018-schema_export_management_command-0.0.7`" — the positional-scalar entry and the "`--path` now requires a value when the flag is given" entry.
- **Not a code defect.** The later contract is the correct one and is the one the consumer documentation describes. Resolution: R1 rewrites the spec to state it directly, with the chronology and the superseded rejected-alternative in the rationale file.

### F2 — HOLDS. `--path` grew two rejection boundaries and a success message the spec does not describe

- **Spec claim:** [Decision 4](../SPECS/spec-022-export_schema-0_0_7.md#decision-4--sdl-output-via-strawberryprinterprint_schema)'s pinned body is `if path: pathlib.Path(path).write_text(...)` / `else: self.stdout.write(...)` — no empty-value rejection, no write-failure wrap, no output on success. [Decision 5](../SPECS/spec-022-export_schema-0_0_7.md#decision-5--commanderror-is-the-commands-only-failure-surface) is titled "`CommandError` for **three** failure modes" and enumerates exactly three.
- **`HEAD` `::Command.handle`:** three further `CommandError` sources and one success write —
  - `if not isinstance(path, str) or not path.strip(): raise CommandError("--path requires a non-empty value")`;
  - `except (OSError, ValueError) as e: raise CommandError(str(e)) from e` around the write;
  - `self.stdout.write(self.style.SUCCESS(f"Wrote schema to {path}"))` after a successful write.
- **Provenance:** `f6238256` (2026-05-22) added the `OSError` wrap and the success message; `f274b2a4` (2026-05-26) added the empty-string `--path` rejection and split the `path is None` / `not path` branches; `7f04c5b2` (2026-07-15) widened the rejection from empty-string to empty-or-whitespace via `.strip()`; `fd3825a2` (2026-08-16) widened the catch to `(OSError, ValueError)` so a `pathlib`-rejected path (embedded null byte) reports as a command failure. `CHANGELOG.md` `[0.0.7]` publishes the first two families; the two widenings are post-`0.0.7` hardening and correctly carry no `[0.0.7]` entry.
- **Live-pinned, so the boundaries are real, not incidental:** `examples/fakeshop/tests/test_export_schema.py::test_export_schema_raises_command_error_when_path_directory_missing`, `::test_export_schema_raises_command_error_when_path_flag_is_empty_string`, `::test_export_schema_raises_command_error_when_path_contains_embedded_null`, and `tests/management/test_export_schema.py::test_export_schema_raises_command_error_when_path_flag_is_whitespace_only`.
- **Not a code defect.** Resolution: R1 restates [Decision 4](../SPECS/spec-022-export_schema-0_0_7.md#decision-4--sdl-output-via-strawberryprinterprint_schema) and [Decision 5](../SPECS/spec-022-export_schema-0_0_7.md#decision-5--commanderror-is-the-commands-only-failure-surface) — including the Decision's own title and every count propagated from it — against the shipped set.

### F3 — HOLDS. stdout output is now byte-identical to the `--path` file; the spec pins the divergent default

- **Spec claim:** [Decision 4](../SPECS/spec-022-export_schema-0_0_7.md#decision-4--sdl-output-via-strawberryprinterprint_schema) pins `self.stdout.write(schema_output)` and `write_text(schema_output, encoding="utf-8")`. The [Edge cases](../SPECS/spec-022-export_schema-0_0_7.md#edge-cases-and-constraints) `call_command` and `stdout` bullet states the opposite of what ships: "`self.stdout.write(schema_output)` appends a trailing newline by default; the test plan accounts for the newline in the captured-string assertions."
- **`HEAD`:** `self.stdout.write(schema_output, ending="")` with an in-source comment naming the reason (Django's `OutputWrapper` defaults `ending="\n"`, which would diverge stdout from `--path` by one byte and break redirect-vs-file diffs), and `write_text(schema_output, encoding="utf-8", newline="")` so a platform with non-LF native newlines cannot translate the SDL bytes.
- **Provenance:** `7f04c5b2` (2026-07-15) suppressed the stdout newline; `fd3825a2` (2026-08-16) disabled newline translation on the file write. Pinned by `tests/management/test_export_schema.py::test_export_schema_stdout_matches_path_file_and_print_schema` (a three-way byte-equality assertion against `print_schema`) and `::test_export_schema_file_write_disables_newline_translation`.
- **Not a code defect.** The byte-identity contract is strictly stronger than what the spec pinned. Resolution: R1 states it in [Decision 4](../SPECS/spec-022-export_schema-0_0_7.md#decision-4--sdl-output-via-strawberryprinterprint_schema) and corrects the falsified [Edge cases](../SPECS/spec-022-export_schema-0_0_7.md#edge-cases-and-constraints) bullet.

### F4 — HOLDS. Symbol resolution is delegated to a shared helper that also validates the selector

- **Spec claim:** [Decision 3](../SPECS/spec-022-export_schema-0_0_7.md#decision-3--symbol-resolution-through-the-shared-_imports-command-helper) pins an inline `import_module_symbol(...)` call inside a `try` / `except (ImportError, AttributeError)` in `handle()`, and its rejected-alternatives list rejects "hand-roll dotted-path resolution" on the grounds that the upstream importer already handles every edge case.
- **`HEAD`:** `::Command.handle` calls `django_strawberry_framework/management/commands/_imports.py::import_module_symbol_or_command_error`, which wraps the upstream importer **and** rejects two selector shapes before it runs — an empty module path and a relative (leading-`.`) module path — each with its own `CommandError` message from `::_validate_absolute_module_path`.
- **Provenance:** `79e2d117` (2026-07-11) extracted the wrapper into `_imports.py` so `inspect_django_type` (card `DONE-029-0.0.9`, a later card that needed the identical translation) could share it; `61f6726c` (2026-07-13) added the pre-import validation. Pinned by `tests/management/test_export_schema.py::test_export_schema_raises_command_error_for_malformed_selector` (three parametrized cases) and by `tests/management/test_imports.py` (15 tests).
- **Not a code defect, and the DRY direction is the one this process mandates.** The spec's rejected alternative is still correct as written — nothing hand-rolls dotted-path *resolution*; the added code validates the selector's *shape* before delegating resolution unchanged. Resolution: R1 restates [Decision 3](../SPECS/spec-022-export_schema-0_0_7.md#decision-3--symbol-resolution-through-the-shared-_imports-command-helper) around the shared helper and records the second-consumer trigger in the rationale file.

### F5 — HOLDS. The pinned test surface is stale in count, composition, and location

- **Spec claim:** [Test plan](../SPECS/spec-022-export_schema-0_0_7.md#test-plan), [Goals](../SPECS/spec-022-export_schema-0_0_7.md#goals) item 3, the Slice 2 checklist, the [Implementation plan](../SPECS/spec-022-export_schema-0_0_7.md#implementation-plan) table and Definition of done item 5 all pin **7** package tests by name, plus "single pytest item per test, NOT `pytest.mark.parametrize`". [Decision 10](../SPECS/spec-022-export_schema-0_0_7.md#decision-10--live-coverage-belongs-in-examplesfakeshoptests-not-test_query), the Slice 2 checklist, the [Test plan](../SPECS/spec-022-export_schema-0_0_7.md#test-plan) and Definition of done item 6 pin the live test as `examples/fakeshop/tests/test_commands.py::test_export_schema_command_against_fakeshop_schema`.
- **`HEAD` package tier:** `grep -c '^def test_' tests/management/test_export_schema.py` -> **10**, one of them (`::test_export_schema_raises_command_error_for_malformed_selector`) a 3-case `pytest.mark.parametrize`. Of the spec's seven names, four survive verbatim; three do not — `::test_export_schema_writes_sdl_to_stdout_by_default` and `::test_export_schema_writes_sdl_to_path_when_path_set` were merged into the strictly stronger `::test_export_schema_stdout_matches_path_file_and_print_schema` (F3's byte-identity assertion, which subsumes both happy paths), and `::test_export_schema_falls_back_to_default_symbol_name_schema` moved (below).
- **`HEAD` live tier:** `examples/fakeshop/tests/test_commands.py` **does not exist** — `31642c9c` (2026-05-29) "tests: relocate example app tests into per-app folders" moved the example-project command tests to `examples/fakeshop/apps/<app>/tests/`. The `export_schema` live coverage lives at `examples/fakeshop/tests/test_export_schema.py`, **5** tests, added by `35e3c26d` (2026-06-01).
- **The `default_symbol_name` fallback contract survived the move and is pinned twice**, so nothing was lost with the deleted test name: `examples/fakeshop/tests/test_export_schema.py` drives three tests through the bare `"config.schema"` selector (no `:schema` suffix), and `tests/management/test_imports.py::test_import_module_symbol_or_command_error_applies_default_symbol_name` pins it at the helper.
- **[Decision 10](../SPECS/spec-022-export_schema-0_0_7.md#decision-10--live-coverage-belongs-in-examplesfakeshoptests-not-test_query)'s ruling holds; only its file reference is stale.** The live coverage is still in `examples/fakeshop/tests/`, still not in `test_query/`, and the tier reasoning is unchanged. Two of its four justification bullets cite the now-nonexistent `test_commands.py`.
- **Not a code defect.** Resolution: R1 restates the test surface — count, names, tiers, the `parametrize` prohibition, and [Decision 10](../SPECS/spec-022-export_schema-0_0_7.md#decision-10--live-coverage-belongs-in-examplesfakeshoptests-not-test_query)'s citations — against `HEAD`.

### F6 — HOLDS. Spec status line says `draft`

`Status: draft (revision 5, post-rev4 feedback).` on a card that shipped in `0.0.7` on 2026-05-27 and whose spec is archived under `docs/SPECS/`.

### F7 — HOLDS. Renumber and forward-reference residue in the spec's own references

Measured 2026-08-18 against `docs/SPECS/spec-022-export_schema-0_0_7.md`:

- **40** occurrences of the `[spec-016]` / `[spec-017]` ref-id family (`grep -oE '\[spec-01[67]' | wc -l`) whose link definitions already point at the post-renumber filenames (`[spec-016]: spec-020-list_field-0_0_7.md`, `[spec-017]: spec-021-apps-0_0_7.md`). The ref-ids and the visible link text both name pre-renumber numbers while the `Predecessors:` line names `spec-020` / `spec-021`. Nothing is broken — the definitions resolve — so it is uniformly rather than divergently stale.
- **4** occurrences of `WIP-ALPHA-018-0.0.7` (Slice 3 checklist, [Doc updates](../SPECS/spec-022-export_schema-0_0_7.md#doc-updates) twice, Definition of done item 10). This card is `022`; the pre-renumber number was `018`.
- **3** prose sites naming `DONE-016` / `DONE-017` (Slice 3 checklist, [Doc updates](../SPECS/spec-022-export_schema-0_0_7.md#doc-updates) twice) — now `DONE-020-0.0.7` / `DONE-021-0.0.7`.
- **4** [Out of scope](../SPECS/spec-022-export_schema-0_0_7.md#out-of-scope-explicitly-tracked-elsewhere) bullets forward-referencing `TODO-ALPHA-029` / `031` / `032` / `033` "for `0.0.12`". All four shipped, at `0.0.14`, under post-renumber cards: Channels router `DONE-041`, debug-toolbar middleware `DONE-042`, test-client helpers `DONE-043`, response-extensions debug middleware `DONE-044`.

### F8 — HOLDS. The rationale file does not exist

`docs/SPECS/appx/spec-022-export_schema-0_0_7-rationale.md` is absent while all 21 lower-numbered specs have one. The spec still carries, measured 2026-08-18:

- a **5**-entry inline `Revision history` block (rev1 through rev5, ~19KB of the file's 139KB);
- a `Justification:` / `Justification for shape:` block under **11** sites (`grep -c '^Justification' -> 11`);
- an `Alternatives considered (and rejected):` list under **all 10** Decisions (`grep -c '^Alternatives considered' -> 10`);
- a **7**-bullet `## Risks and open questions` section;
- **40** `(revN Xn)` attribution parentheticals (`grep -oE '\(rev[0-9]+ [A-Z][0-9]+' | wc -l -> 40`) threaded through the checklist, decisions, edge cases, test plan, doc updates and DoD; **148** bare `rev[0-9]` token occurrences overall.

### F9 — HOLDS. `docs/GLOSSARY.md` `## Schema export management command` under-describes the shipped command

The entry is already ahead of the spec — it carries the success message, the destructive-overwrite contract, and the `OSError` wrap — but four shipped, live-pinned contracts are absent:

- **whitespace-only `--path`**. The entry says "empty-string `--path`"; `::Command.handle` rejects on `not path.strip()` (F2), and `tests/management/test_export_schema.py::test_export_schema_raises_command_error_when_path_flag_is_whitespace_only` pins it.
- **the `ValueError` half of the write-failure catch**. The entry names `OSError` only; `HEAD` catches `(OSError, ValueError)` and `examples/fakeshop/tests/test_export_schema.py::test_export_schema_raises_command_error_when_path_contains_embedded_null` pins the `ValueError` path.
- **the malformed-selector rejections** (F4) — empty module path, relative module path. No glossary entry mentions them; `grep -n "relative module path\|module path is empty" docs/GLOSSARY.md` returns nothing, so the `## Schema introspection management command` sibling does not carry them either.
- **the stdout/file byte-identity contract** (F3). The entry says `--path` omitted "writes SDL to `self.stdout`" without the suppressed-newline guarantee a consumer redirecting stdout to a file depends on.

**DB-backed** (`GlossaryTerm.body`); the fix is an ORM edit plus a regenerate, never a hand-edit of `docs/GLOSSARY.md`.

### F10 — HOLDS. The spec now contradicts itself on the shell-redirect claim (raised mid-cycle, verified 2026-08-18)

Not in the original finding list; surfaced by Worker 0 spot-checking R2's Worker 1 plan-revision pass, and verified against the file before being routed (`BUILD.md` `### Worker 0 verifies every finding against source before dispatching`).

- **What landed:** that pass added a paragraph to [Decision 4](../SPECS/spec-022-export_schema-0_0_7.md#decision-4--sdl-output-via-strawberryprinterprint_schema) marking that `ending=""` and `newline=""` do not reach the same place — the `--path` file is LF on every platform, while a shell redirect of the stdout form is still subject to the interpreter's own `sys.stdout` newline translation. It closes with an instruction to any doc text quoting the contract: state the three emitted byte sequences, "never an unqualified cross-platform equivalence between `manage.py export_schema … > out.graphql` and `--path out.graphql`".
- **What it did not reach:** `## User-facing API` in the same spec still reads "writes the SDL to stdout with **no trailing newline appended**. Shell redirection therefore produces a file byte-identical to the `--path` form:" — the unqualified equivalence the new paragraph forbids, stated three pages earlier and immediately above the `> schema.graphql` example that demonstrates it.
- **Same defect class, third occurrence in this cycle.** R2's High was this claim in the glossary; the fix corrected the Decision and the glossary body but skipped the spec's own parallel site. The spec's pre-reconciliation history names this pattern four times (rev2 L1, rev3 M1, rev3 L2, rev5 M1) — a wording fix landing at the primary site and skipping the parallel reference — and R1's own pass-1 High was an instance of it.
- **Severity: High.** A spec that states a contract and its negation is not a contract; and this is the surface a consumer reads first. Routed to Worker 1 under the same partition correction that put the spec in R2's scope.

### Findings that do NOT hold — nothing was skipped in the code

Reported rather than dropped, per `BUILD.md`. Every Definition-of-done item was delivered at the ship commit and holds at `HEAD`:

- **DoD 1** — `django_strawberry_framework/management/__init__.py` and `management/commands/__init__.py` both exist and carry a one-line module docstring and nothing else. The docstring wording differs from the spec's "Suggested:" text, which the spec offered as a suggestion rather than a pin; `commands/__init__.py` now names both shipped commands, correctly reflecting the later `inspect_django_type` addition.
- **DoD 2** — shipped verbatim at `d780726f`: `help = "Export the GraphQL schema"`, `add_arguments(self, parser: CommandParser) -> None`, `handle(self, *args: object, **options: object) -> None`, module + class + both method docstrings, no `# noqa` for any `D` or `ANN` rule, and none of `--watch` / `--indent` / `--json` / settings-backed defaults / an alias — all still true at `HEAD`. Only the two `nargs` declarations and the `handle` body are superseded (F1-F4).
- **DoD 3, 12** — `grep` over `django_strawberry_framework/__init__.py` for `management` / `export_schema` / `Command` finds nothing; `__all__` is unwidened; zero new public exports.
- **DoD 4** — `grep` over `tests/base/test_init.py` for `export_schema` / `management` finds nothing; the `__all__` assertion is untouched.
- **DoD 5** — `tests/management/__init__.py` exists with a one-line docstring. All seven named tests landed at `d780726f`; the surface has since grown and reorganized (F5).
- **DoD 6** — the live test landed at `d780726f` in `examples/fakeshop/tests/test_commands.py` under the pinned name, and no file was created under `examples/fakeshop/test_query/`. Both still hold in substance; only the file has since moved (F5).
- **DoD 7** — `examples/fakeshop/config/settings.py:71` still declares the bare `"django_strawberry_framework"` entry; the file was not modified by this card.
- **DoD 9** — every doc update landed and survives: the `- schema export management command` bullet is gone from `docs/README.md` (the whole `Coming in 0.1.0` section is now gone, removed by later cards) and the shipped bullet is present at `docs/README.md:113`; `grep -n "\[alpha\]" docs/TREE.md` returns nothing; `grep -n "and the management command" docs/TREE.md` returns nothing; `docs/TREE.md` lists the `management/` subtree in both package layouts and `tests/management/` in both test layouts; the `docs/GLOSSARY.md` index row reads `shipped (0.0.7)`; `CHANGELOG.md`'s `[0.0.7] ### Added` carries the entry.
- **DoD 10** — `KANBAN.md:3971` carries `DONE-022-0.0.7` in the Done column with its `docs/SPECS/spec-022-export_schema-0_0_7.md` spec link and a past-tense body.
- **DoD 11** — the version bump is not in this card's diff.
- **DoD 8, 13** — CI's gate; not worker-verifiable here.

**Conclusion: no code was skipped, dropped, or deviated at ship. Every finding above is post-ship evolution the spec never absorbed. No cohort in this cycle writes package source or tests.**

## Declarations

- **Ownership partition** — two cohorts, dispatched **sequentially** (R2's glossary body must describe the contract R1 reconciles):
  - **R1** — `docs/SPECS/spec-022-export_schema-0_0_7.md`, `docs/SPECS/appx/spec-022-export_schema-0_0_7-rationale.md`, `docs/builder/bld-review-1-spec_022_reconciliation.md`.
  - **R2** — `examples/fakeshop/db.sqlite3`, `docs/GLOSSARY.md`, `KANBAN.md`, `KANBAN.html`, `docs/builder/bld-review-2-spec_022_glossary_body.md`.
  - No file appears in both. No cohort writes `django_strawberry_framework/`, `tests/`, or `examples/fakeshop/apps/`.
  - `KANBAN.md` / `KANBAN.html` appear in R2's list because `scripts/build_glossary_md.py`'s sibling regenerates are run in the same pass, not because R2 edits any kanban row. R2 must not write a kanban table.

  **Partition correction: `docs/SPECS/spec-022-export_schema-0_0_7.md` folded into R2 after R2's review** (`BUILD.md` `### Parallel cohorts under a declared ownership partition`, "If a collision surfaces mid-flight … Worker 0 … records the correction in the plan"). R2's Worker 3 pass raised a High against the glossary body's cross-platform byte-identity clause and escalated a companion item: spec [Decision 4](../SPECS/spec-022-export_schema-0_0_7.md#decision-4--sdl-output-via-strawberryprinterprint_schema)'s two adjacent bullets are each true in their own scope — one describes the shell-redirect form, the next the `--path` form — and nothing marks the scope change, which is what invited the glossary's over-claim. The spec was R1's file and R1 is `final-accepted`, so the correction is recorded rather than assumed. Only Worker 1 may mutate a spec in any cohort (`BUILD.md` `## Spec reconciliation`), so this widens no role's authority; it moves one file's custody to the cohort that now needs it. R1's artifact stays closed and is not reopened.
- **Hot-path declaration** — none. No cohort touches executable package code.
- **Floor-verification scope** — none. No cohort touches a Django / Strawberry / channels integration seam (`BUILD.md` `### When it is required`).

### R1's worker sequence is Worker 1 -> Worker 3 -> Worker 1, with no Worker 2

Declared explicitly because it departs from `worker-0.md` `## Per-slice dispatch`'s default, and the departure is **forced by the role contracts**, not a convenience:

- `BUILD.md` `## Spec reconciliation` — only Worker 1 may mutate the spec.
- The Required-reading matrix — Worker 2 **never** reads the rationale file, and the rationale move is its authorship.

So R1's build phase is Worker 1's by definition. `### Isolation is non-waivable` is preserved intact: the agent that writes R1 is not the agent that reviews it — Worker 3 reviews, and a **fresh** Worker 1 invocation performs final verification. R2 runs the ordinary Worker 1 -> 2 -> 3 -> 1 chain.

## Artifact list

**All four were deleted at close, 2026-08-18, on the maintainer's instruction. This plan is the only surviving artifact of the cycle.** Each reached `final-accepted` first; the final gate's non-reproducible content was folded into `## Final gate record` below before deletion, and the deferred catalog's open items were homed on the board (`## Deferred-work homing`). Every `R1` / `R2` / `integration pass` attribution elsewhere in this file names a source that no longer exists on disk — the claim it supports is restated here rather than left as a pointer.

- `docs/builder/bld-review-1-spec_022_reconciliation.md` — `final-accepted`, deleted
- `docs/builder/bld-review-2-spec_022_glossary_body.md` — `final-accepted`, deleted
- `docs/builder/bld-integration-022.md` — `final-accepted`, deleted
- `docs/builder/bld-final-022.md` — `final-accepted`, deleted

## Checklist

- [x] R1: Rationale extraction + spec reconciliation (F1-F8) -> `docs/builder/bld-review-1-spec_022_reconciliation.md`
- [x] R2: DB-backed glossary-body reconciliation (F9) -> `docs/builder/bld-review-2-spec_022_glossary_body.md`
- [x] Cross-cohort integration pass -> `docs/builder/bld-integration-022.md`
- [x] Final test-run gate -> `docs/builder/bld-final-022.md`

## Final gate record (folded in from `bld-final-022.md` before its deletion)

The final-gate artifact was deleted at close along with the three round artifacts. Everything in it that is not reproducible from the spec, the rationale companion, the board, or the section below was folded here first. What was deliberately NOT kept: the cohort/checklist audit and the end-of-pass `git status` snapshot, both of which describe files that no longer exist or a tree state four commits stale.

### The gate, command by command

Run from the repository root, each with output redirected to a file and `$?` read directly afterwards. **Exit status was never read through a pipe** — `| tail` reports the pager's status, not the command's, and that has shipped a false PASS on this gate's first row in a prior cycle.

| # | Command | Result | Exit |
|---|---|---|---|
| 1 | `uv run pytest --no-cov` | `6178 passed, 40 skipped in 66.95s` | 0 |
| 2 | `uv run python examples/fakeshop/manage.py check` | `System check identified no issues (0 silenced).` | 0 |
| 3 | `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` | `No changes detected` | 0 |
| 4 | `uv run ruff format --check .` | `424 files already formatted` | 0 |
| 5 | `uv run ruff check .` | `All checks passed!` | 0 |
| 6 | `git diff --check` | no output | 0 |

`--no-cov` was the only coverage-shaped flag used anywhere in the cycle; plain `uv run pytest` is a coverage run in this repo and is forbidden by `BUILD.md` `## Coverage is the maintainer's gate, not a worker's tool`. Command 4's `COM812 may cause conflicts when used with the formatter` warning is standing configuration noise at exit 0. No attribution work was owed: the one failure the concurrent `spec-021` cycle's gate recorded, `tests/utils/test_write_values.py::test_form_and_serializer_decode_walks_share_field_handlers`, stopped reproducing once commit `31625ac7` landed that refactor's twelve `.py` files.

### Additional read-only gates, and why `--check` is the right instrument

- `scripts/check_spec_glossary.py --spec docs/SPECS/spec-022-export_schema-0_0_7.md` -> `OK: 13 terms`, exit 0.
- `build_glossary_md.py --check`, `build_kanban_md.py --check`, `build_kanban_html.py --check` -> all `up to date`, exit 0.

**The durable method, not just the result:** all three renderers were run in the non-writing `--check` form only. A 0 exit re-renders from the DB in memory and compares against the file on disk, which is the two-consecutive-regenerate proof *without a write* — the only safe form when a concurrent cycle owns the same DB and the same three rendered docs. It also proves no hand-edit is riding along on a mixed diff.

### Floor verification

**Declared scope `none`, vacuous rather than skipped, with the premise verified.** `BUILD.md` `### When it is required` scopes the obligation to a slice touching a Django / Strawberry / channels integration seam and names "docs, KANBAN / glossary regeneration" among the cases that declare `none`. No cohort in this cycle touched executable code, so there is no seam and no focused scope a floor run could have had. Verified rather than asserted: `git status --porcelain | grep '\.py$'` returned exactly one path, `tests/test_apps.py`, and it was the concurrent cycle's. No floor venv was built and nothing was installed into the shared `.venv`.

### Byte figures and the stale-twin sweep

Re-measured rather than read, because the rationale's self-reported table re-converged four times during the cycle. `wc -c`: spec **84,446**, rationale **74,218**; `git show HEAD:<spec> | wc -c` -> **139,523**; the net is `139,523 - 84,446 = 55,077`. Each current literal occurs exactly once across the pair. The sweep over every superseded literal the cycle produced — `84,802`, `73,498`, `54,721`, `84,149`, `72,031`, `55,374`, `84,728`, `54,795`, `83,174`, `70,672`, `56,349`, `82,461`, `68,216`, `57,062`, `82,477`, `67,639`, `57,046` — returned **0 occurrences** in both files. Note these figures are pre-commit; after the maintainer's commit they are re-derivable with `wc -c` and this record becomes history.

### Deferred items that take no card

Catalog items 7-9, which the homing table below marks "no action", kept here because deleting the artifact would otherwise drop their reasoning:

- **7 — the two source-side `byte-identical` statements in `export_schema.py` are permitted, not violations.** `Command.handle`'s docstring states the equality at the *emitted* level and names no redirect and no platform, which is what Decision 4 obliges; the inline `break redirect-vs-file diffs` comment states what would break *without* `ending=""` — a counterfactual, not an equivalence — and is the text Decision 4's pinned block quotes verbatim, correctly, since that block's fidelity to source is the point. Recorded so a reader applying Decision 4's own "forbids a framing while using it" reasoning to the block does not re-raise it. Rewording the comment would be an escalation, not a cohort's fix.
- **8 — instrument note.** The DB dump difference is 6 statements *or* 8 physical lines for the same 3 rows: `sqlite3.iterdump()` yields one string per SQL statement, while writing them out and running `diff` splits row 504's `INSERT` across the body's embedded newlines. Both readings are right; the load-bearing figure is the row set. State the instrument beside the digit.
- **9 — a population defined over "standing surfaces" has to enumerate which directories those are.** Of the sites the F10 sweeps surfaced, three sat in per-cycle or regenerable trees (`docs/dry/`, `docs/bug_hunt/`) and two in shipped source. Without the enumeration the next sweep re-argues the boundary from scratch. A `BUILD.md` proposal at the maintainer's discretion, bound by `## The corpus ratchet`.

### Closed items, kept so a later pass does not re-open them as new

- **Plan anchor citations** — repointed mid-cycle after Decisions 3 and 5 were renamed. The plan carries **27** `spec-022-...#…` citations, **0 dead**. Published upstream as 25; it moved because the F10 section added two more.
- **`spec-025-scalar_map_helper-0_0_7.md`'s `Status:` line** — DOES NOT REPRODUCE as a deferral. It now reads `shipped — Slices 1-5 all landed`. Dropped from this cycle's list and from the concurrent cycle's, which carried it too.
- **`spec-021`'s Decision 4 retitle** — landed. spec-022's only `spec-021` fragment is `#decision-3--no-public-export` and it resolves. Recorded so a later pass does not re-add a cross-reference to a heading a concurrent session is moving.
- **R1's F9 re-grade was an under-count** — the corrected figure is FOUR gaps, not three. R2 planned and built against four and all four landed.
- **The rationale's Decision 5 entry once claimed both the `CHANGELOG.md` and `KANBAN.md` `## Doc updates` texts were quotations of shipped prose.** Only the CHANGELOG half was true; the KANBAN half was a 496-character fabrication, fixed at both sites. The forbidden three-shape enumeration now has 0 occurrences in `KANBAN.md`.
- **The forbidden cross-platform redirect claim (F10)** — 0 standing-surface occurrences, swept on an instrument whose vocabulary is not the finding's. Every remaining hit is a per-cycle artifact quoting the deleted text, or one of the rationale's two sites that exist to record the claim as deleted.

### What the gate concluded

All six commands pass; no spec edit was owed at the gate and none was made. Re-deriving the three upstream deferred catalogs found **three published claims that do not reproduce**: `spec-025`'s `Status:` line, the `#"…"` citation pair published as 42/34 (it is 47 tokens / 44 parsed / 11 resolve / 33 not, under a stated rule), and the plan's anchor corpus at 27 rather than 25. Two further figures were corrected upstream and carried corrected: the glossary index substring 3 -> 5, and the F9 gap count 3 -> 4. **Final status was `final-accepted`.**


## Deferred-work homing (Worker 0, 2026-08-18, post-gate)

`docs/builder/bld-final-022.md` `### Open — carry these forward` lists nine items. Five had no home on any board card; they are now `CardItem` rows on `TODO-ALPHA-052-0.1.0`, written through the Django ORM and re-rendered (`KANBAN.md` +4 bullets and 1 replaced, `KANBAN.html` data block, `docs/GLOSSARY.md` byte-identical). **That artifact's `Open` list is superseded by this table; read this first.**

| Catalog item | Disposition | Where it now lives |
| --- | --- | --- |
| 1 — introspection entry's symmetric validator gap | homed | card 052 `scope` order 40 |
| 2 — `CHANGELOG.md` `[0.0.7]` pre-renumber labels | already homed before this cycle | card 052 `scope` order 38 |
| 3 — post-`0.0.7` `export_schema` behavior absent from every release section | homed | card 052 `scope` order 41 |
| 4 — interpreter-versioned `.venv` citation paths | homed | card 052 `scope` order 42 |
| 5 — citations whose target is a script-rendered doc | homed | card 052 `scope` order 43 |
| 6 — non-unique `docs/GLOSSARY.md` citation substrings | homed as an amendment, not a new bullet | card 052 `scope` order 34, which already scopes the cited-substring uniqueness check; item 6 is a third measured instance of that rule |
| 7 — source-side `byte-identical` statements | no action, graded permitted | — |
| 8 — DB-dump instrument note | no action | — |
| 9 — enumerate the directories a "standing surfaces" population covers | not card-shaped; a `BUILD.md` proposal at maintainer discretion | — |

**Two published populations were wrong and are corrected in the card text rather than carried.** Re-deriving before homing is the standing rule and it earned its place twice here:

- Item 4's population is **24 occurrences across 3 files**, not 5. The catalog's 5 counted only the two files this cycle owned; `docs/SPECS/spec-025-scalar_map_helper-0_0_7.md` carries 19 more and was never in view. Instrument: occurrences of `.venv/lib/python3.10` across `*.md` and `*.py`, excluding per-cycle `docs/builder/` artifacts.
- Item 6's population is **5**, not 3 — already corrected inside the catalog, and the five sites are now enumerated by line so the next pass does not re-measure them.

Item 5 is homed with **both** resolvers' figures and neither presented as the count. The catalog's resolver scored 47 tokens / 44 parsed / 11 resolve / 33 dead; an independent fence-aware resolver run at homing time parsed all 47 and scored 25 resolve / 22 dead. They diverge almost entirely on target attribution for a line naming two candidate files, which is the checker's first regression test rather than a number to publish.

Gates re-run after the write: all three build scripts `--check` up to date, `manage.py check` clean, `manage.py import_spec_terms --check` OK for all 49 done cards.

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
