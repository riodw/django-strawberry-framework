# Final test-run gate: export_schema / 0.0.7 (018)

Spec source: `docs/SPECS/spec-018-export_schema-0_0_7.md`
Build plan: `docs/builder/build-018-export_schema-0_0_7.md`
Integration artifact: `docs/builder/bld-integration.md`
Status: final-accepted

## Spec slice checklist (verbatim)

No spec-level checklist for the final gate; the build plan's "Final test-run gate" checkbox is the contract.

## Gate runs

### `uv run pytest --no-cov`

Command (exact): `uv run pytest --no-cov`

Outcome: **pass**. `772 passed, 2 skipped, 5 warnings in 29.10s` (774 tests collected; 2 are `FAKESHOP_SHARDED=1`-guarded sharded tests that skip under the default invocation per `AGENTS.md` line 28). The explicit `--no-cov` opts out of `pytest.ini`'s auto-applied `--cov` per `docs/builder/BUILD.md` lines 537-549 — coverage is the maintainer's gate, not a worker's tool.

Interpretation: every test in all three trees (`tests/`, `examples/fakeshop/tests/`, `examples/fakeshop/test_query/`) passes; the 5 warnings are pre-existing baseline noise (one `DATABASES` override warning in `test_seed_shards_command_runs_when_shard_alias_present` and four `Model already registered` warnings in `tests/types/test_converters.py` for model-reload-pattern tests), unchanged by the export_schema build. The new Slice 2 surface — `tests/management/test_export_schema.py` (7 tests) and `examples/fakeshop/tests/test_commands.py::test_export_schema_command_against_fakeshop_schema` (1 test) — is included in the green.

### `uv run python examples/fakeshop/manage.py check`

Command (exact): `uv run python examples/fakeshop/manage.py check`

Outcome: **pass**. Output: `System check identified no issues (0 silenced).`

Interpretation: Django's `INSTALLED_APPS` resolves cleanly (including the explicit `DjangoStrawberryFrameworkConfig` shipped under `DONE-017-0.0.7` plus the new `django_strawberry_framework.management.commands` discovery the export_schema build enables); no model / admin / url-config drift surfaced by the system check framework.

### `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run`

Command (exact): `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run`

Outcome: **pass**. Output: `No changes detected`.

Interpretation: the example project's model state is migration-consistent — the management command this card ships reads the schema only and does not introduce model state, so confirming zero pending migrations matches the spec's "no DB access" pin (spec lines 587, 624) and Slice 1's body design (no ORM markers — verified by the static-inspection helper output cited in `bld-integration.md`).

### `uv run ruff format --check .`

Command (exact): `uv run ruff format --check .`

Outcome: **pass**. Output: `110 files already formatted` (plus one pre-existing `COM812`-vs-formatter conflict warning that is a repo-config artifact, not a slice introduction — `AGENTS.md` line 17 explicitly keeps `COM812` enabled on purpose; the warning has been present across `DONE-016` / `DONE-017` / now `DONE-018` builds and is the maintainer's documented choice).

Interpretation: no file requires reformatting; the read-only check holds. Slice 1's source module, Slice 2's test file + fakeshop extension, and Slice 3's doc edits all conform to `ruff format`'s expected layout. No `--fix` was passed (per the gate's read-only contract).

### `uv run ruff check .`

Command (exact): `uv run ruff check .`

Outcome: **pass**. Output: `All checks passed!`.

Interpretation: zero lint violations across the working tree. The Slice 1 source module's two forced-divergence categories (pydocstyle `D100` / `D101` / `D102` and flake8-annotations `ANN001` / `ANN201` — see spec rev2 H1 / rev3 L2) are all root-cause-fixed in source per `AGENTS.md` line 4; no `# noqa` suppressions. Slice 2's test file is exempted from `D` / `ANN` by the `tests/**/*.py` per-file ignore at `pyproject.toml:102` and still passes the residual rule set. No `--fix` was passed.

### `git diff --check`

Command (exact): `git diff --check`

Outcome: **pass**. Exit code 0; empty output.

Interpretation: no whitespace errors (trailing whitespace, tab-in-leading-space, end-of-file blank lines) and no leftover conflict markers anywhere in the working tree.

## Deferred work catalog

Walked every per-slice artifact's `### Notes for Worker 1 (spec reconciliation)` and `### What looks solid` sections plus the integration artifact's `### Notes for Worker 0` and `### Notes for Worker 1 (spec reconciliation)` (where present). Bullets below are the next spec author's reading list per `docs/builder/BUILD.md` line 553.

- **Spec status-line flip deferred to joint-cut closeout.** Source: `bld-slice-3-promotion_docs.md` `### Spec changes made (Worker 1 only)` (Worker 1 final-verification disposition of Worker 3 note 3) + `bld-integration.md` `### Notes for Worker 0` bullet 2. The spec at `docs/SPECS/spec-018-export_schema-0_0_7.md:4` still reads `Status: draft (revision 5, post-rev4 feedback against docs/feedback.md).`. The flip to `shipped (0.0.7)` belongs to whichever Worker 1 spawn closes out the joint bundle once `WIP-ALPHA-019-0.0.7` and `WIP-ALPHA-020-0.0.7` have shipped; not licensed by a specific spec line (spec Decision 9 lines 526-541 implicitly defers all joint-cut closeout state to the last-card-to-ship).
- **Spec line-citation drift left as pin-at-write-time hints.** Source: `bld-slice-3-promotion_docs.md` `### Spec changes made (Worker 1 only)` per-note disposition of Worker 3 note 2. The spec cites a number of file-line positions (`docs/README.md` "line 113", `docs/TREE.md` "line 190" / "lines 309-313", `docs/GLOSSARY.md` "line 104") that have drifted against the live files (live positions 122 / 193 / 320-322 / 105 respectively). Worker 1 declined to refresh — `docs/builder/BUILD.md` "Plan template" Implementation steps note explicitly classifies these as pin-at-write-time navigational hints, not load-bearing contracts. Refreshing would force a rev6 for non-load-bearing cleanup and misalign the spec's revision history with the slices already shipped against rev5.
- **Joint-cut version bump deferred to last-`0.0.7`-card-to-ship.** Source: `bld-slice-3-promotion_docs.md` `### Spec slice checklist (verbatim)` sub-bullet at spec line 80 + Worker 1 final-verification pass; Decision 9 spec lines 526-541. `pyproject.toml [project].version`, `django_strawberry_framework/__init__.py.__version__`, and `tests/base/test_init.py`'s pinned version assertion all stay at `0.0.6`. The bump to `0.0.7` plus the `## [0.0.7] - <date>` date-line finalization in `CHANGELOG.md:21` is owned by whichever card under the joint cut ships last (currently `WIP-ALPHA-019-0.0.7` and `WIP-ALPHA-020-0.0.7` are still queued).
- **`--watch` follow-up if consumer demand surfaces.** Source: spec Decision 6 spec line 482 + spec Non-goals spec line 123 + `bld-slice-1-module.md` `### What looks solid` (no scope creep). Not shipped in 018; explicitly deferred as "reasonable post-`1.0.0` differentiator if consumer demand surfaces." No spec line authorizing a `0.0.8`-`0.1.0` slot; whichever spec author adds it picks the slot.
- **`--indent` SDL pretty-printing flag.** Source: spec Decision 6 spec line 469 + spec Non-goals spec line 125. Explicitly NOT on the roadmap — SDL is whitespace-agnostic; consumer-side formatting (`prettier --parser graphql`, `graphql-cli`) is the spec's pinned downstream answer. Not a deferral to a future card so much as a permanent posture; included here so a future spec author searching the catalog for "indent" finds the rationale.
- **`--json` introspection mode.** Source: spec Decision 6 spec line 470 + spec Decision 4 spec line 420 + spec Non-goals spec line 122. Explicitly deferred to a follow-up card under consumer demand; the spec at Decision 6 alternatives bullet (spec line 491) records the design surface ("emit the introspection-query result, which requires running the schema with its extensions and context dependencies") as non-trivial and unsettled. No spec line authorizes a specific slot.
- **Settings-backed default schema dotted path.** Source: spec Decision 6 spec line 471 + spec Non-goals spec line 127 + `AGENTS.md` line 20 ("Add settings keys only when the feature that needs them lands"). Permanent posture — consumers wrap the command in a `Makefile` entry per spec Decision 6 alternatives bullet (spec lines 483-490). Catalog-included for the same reason as `--indent`: a future spec author searching for "schema settings key" finds the rationale.
- **`dump_schema` / `print_schema` alias.** Source: spec Decision 6 spec line 472 + spec Non-goals spec line 126. Explicitly rejected ("one command name, one canonical invocation; aliasing fragments documentation and consumer mental models"). Permanent posture.
- **Multi-database cooperation contract — `WIP-ALPHA-019-0.0.7`.** Source: spec Decision 9 spec lines 526-541 + spec line 88 (Doc updates → GLOSSARY entries referenced) + `KANBAN.md:50` `### In progress` summary. Still queued for `0.0.7` under the joint cut. Pre-existing in `docs/GLOSSARY.md` Index ("Multi-database cooperation | planned for 0.0.7"); the GLOSSARY entry body already exists. Spec authorship belongs to whichever Worker 1 spawn picks up the card.
- **Warning-free scalar registration via `StrawberryConfig.scalar_map` — `WIP-ALPHA-020-0.0.7`** (or whatever the maintainer's renumber resolves to). Source: spec Decision 9 spec lines 526-541 + `KANBAN.md:50` `### In progress` summary + `CHANGELOG.md` `[0.0.6]` "Notes" bullet at line 68. Still queued for `0.0.7` under the joint cut. The `[0.0.6]` Notes bullet already records the deprecation-warning suppression at the BigInt definition site as a follow-up — that's the card's seed.

## Out-of-scope working-tree files at gate time

Per the build plan baseline (`docs/builder/build-018-export_schema-0_0_7.md` lines 17-23) and `AGENTS.md` line 31 (presumptively maintainer or another-dev in-progress work; not auto-reverted, not flagged as build issues):

- `M django_strawberry_framework/scalars.py` — out-of-scope; recorded as maintainer working file in the build plan's pre-flight baseline and mid-build drift addendum.
- `M docs/review/rev-django_strawberry_framework.md` — out-of-scope; recorded as maintainer working file in the build plan.
- `M docs/review/rev-scalars.md` — out-of-scope; recorded as maintainer working file in the build plan.

Untracked-but-in-scope artifacts (Worker 0 / Worker 1 build artifacts; the build plan and the four `bld-*.md` files are not committed by workers per `AGENTS.md` line 30 — only the maintainer commits):

- `?? docs/builder/build-018-export_schema-0_0_7.md` (build plan; Worker 0)
- `?? docs/builder/bld-slice-2-tests.md` (slice artifact; Worker 1)
- `?? docs/builder/bld-slice-3-promotion_docs.md` (slice artifact; Worker 1)
- `?? docs/builder/bld-integration.md` (integration artifact; Worker 1)

In-scope working-tree modifications that are this build's deliverables and stay until the maintainer commits:

- `M CHANGELOG.md` (Slice 3)
- `M KANBAN.md` (Slice 3; column move landed via maintainer commit `216e6ba` ahead of Worker 2's build pass + Worker 2's single-line cleanup at line 62 per `bld-integration.md` audit walkthrough)
- `M django_strawberry_framework/management/__init__.py` (Slice 1)
- `M django_strawberry_framework/management/commands/__init__.py` (Slice 1)
- `M django_strawberry_framework/management/commands/export_schema.py` (Slice 1)
- `M docs/GLOSSARY.md` (Slice 3)
- `M docs/README.md` (Slice 3)
- `M docs/TREE.md` (Slice 3)
- `M docs/builder/bld-slice-1-module.md` (Slice 1 artifact; pre-existing untracked-state was promoted to tracked during the maintainer's `216e6ba` commit per the build plan addendum)
- `M examples/fakeshop/tests/test_commands.py` (Slice 2)
- `M tests/management/__init__.py` (Slice 2)
- `M tests/management/test_export_schema.py` (Slice 2)

## Notes for Worker 0

- **Final test-run gate is clean.** All six commands return green; mark `- [x]` on the build plan's "Final test-run gate" checkbox.
- **Joint-cut bundle is not yet complete.** `WIP-ALPHA-019-0.0.7` (multi-database cooperation contract) and `WIP-ALPHA-020-0.0.7` (warning-free scalar registration) are still queued per `KANBAN.md:50`'s `### In progress` summary and per Decision 9 (spec lines 526-541). The version bump (`pyproject.toml`, `__version__`, `tests/base/test_init.py`) and the spec status-line flip (`Status: shipped (0.0.7)` on `docs/SPECS/spec-018-export_schema-0_0_7.md:4`) both stay deferred to whichever card under the bundle ships last. Worker 0 should not flip either at this closeout.
- **Out-of-scope files in the working tree are presumptively maintainer-baseline.** The three `M` entries (`docs/review/rev-django_strawberry_framework.md`, `docs/review/rev-scalars.md`, `django_strawberry_framework/scalars.py`) are recorded in the build plan's baseline (lines 17-23). Per `AGENTS.md` line 31 they are NOT auto-reverted and NOT flagged as build issues.
- **No consolidation loop needed at this gate.** The integration pass already returned `final-accepted` with zero High/Medium/Low findings; the final gate confirms the test suite still passes against that state. Worker 0 hands off directly to maintainer commit.

## Final status

`final-accepted`. Every gate command passes:

- `uv run pytest --no-cov` → 772 passed, 2 skipped, 5 warnings.
- `uv run python examples/fakeshop/manage.py check` → `System check identified no issues (0 silenced).`
- `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` → `No changes detected`.
- `uv run ruff format --check .` → `110 files already formatted`.
- `uv run ruff check .` → `All checks passed!`.
- `git diff --check` → exit 0, no whitespace / conflict-marker issues.

The export_schema build (018) closes cleanly. Worker 0 marks the final build-plan checkbox `- [x]` and hands off to maintainer for commit. Joint-cut state (spec status-line flip + version bump) stays deferred to the last-`0.0.7`-card closeout per Decision 9.
