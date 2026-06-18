# Build: Final test-run gate — mutations / 0.0.11 (036)

Spec reference: `docs/spec-036-mutations-0_0_11.md` (Status **COMPLETE**, card `DONE-036-0.0.11`; all five slices `final-accepted`, integration pass `final-accepted`)
Build plan: `docs/builder/build-036-mutations-0_0_11.md`
Status: final-accepted

> **GATE CAVEAT — 2 pre-existing kanban-example test failures (NOT a build regression).** The full `pytest` sweep reports `2 failed, 2089 passed, 4 skipped`. Both failures are the maintainer-surfaced baseline kanban tests, byte-identical to HEAD and failing identically at committed HEAD independent of this build. They are recorded in the Deferred work catalog below with the one-line maintainer fix. The build delivered the spec end-to-end; these 2 failures predate it. The gate does NOT re-loop any slice over them (`AGENTS.md` rule 33 / task framing). Every other gate command is green.

This is the Worker-1 final test-run gate per `BUILD.md` "Final test-run gate" / `worker-1.md` "Final test-run gate". The integration pass (`docs/builder/bld-integration.md`) is `final-accepted`. This pass runs the narrow gate (full `pytest --no-cov` sweep, Django consistency checks, lint/format/diff), classifies the 2 known pre-existing failures, builds the `### Deferred work catalog`, and sets the build's final `Status:`. It is read-only verification — no source/test/doc/spec edit, no commit.

## Spec status-line re-verification (this spawn)

Spec line 5 reads `Status: **COMPLETE** (card DONE-036-0.0.11; all five slices shipped — build complete)`. Accurate for the current state (all five slices + integration pass `final-accepted`; only this final gate remained). No header edit needed this spawn.

## Gate command results (exact)

Run from the repo root, in the `BUILD.md`-mandated order. Each line records the exact command, raw exit code, and pass/fail classification.

| # | Command | Exit | Result |
| --- | --- | --- | --- |
| 1 | `uv run pytest --no-cov` | non-zero | **fail (raw)** — `2 failed, 2089 passed, 4 skipped in 103.11s`; the 2 failures are the confirmed pre-existing-at-HEAD kanban tests (classified below as a maintainer-surfaced baseline failure, NOT a build regression) |
| 2a | `uv run python examples/fakeshop/manage.py check` | 0 | **pass** — `System check identified no issues (0 silenced).` |
| 2b | `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` | 0 | **pass** — `No changes detected` |
| 3a | `uv run ruff format --check .` | 0 | **pass** — `282 files already formatted` (the `COM812`-may-conflict line is a pre-existing non-fatal config advisory ruff always prints; exit 0) |
| 3b | `uv run ruff check .` | 0 | **pass** — `All checks passed!` |
| 3c | `git diff --check` | 0 | **pass** — no whitespace errors / conflict markers |

The explicit `--no-cov` on the `pytest` invocation is required: `pytest.ini` auto-applies `--cov`, and plain `uv run pytest` is a coverage run, forbidden by "Coverage is the maintainer's gate, not a worker's tool". No `--cov*` flag was passed; line coverage was not inspected or asserted.

## The 2 pytest failures — rigorous pre-existing-at-HEAD verification

Both failures are exactly the two tests the Slice-5 final-verification, the integration pass, and the task framing predicted. Verified pre-existing (not a build regression) by four independent checks:

### The exact failing test ids

1. `examples/fakeshop/apps/kanban/tests/test_commands.py::test_import_card_predicted_files_command_marks_directories`
   - `assert planned_dir.is_current is False` → `assert True is False` where `True = <TrackedPath: django_strawberry_framework/mutations/>.is_current` (`test_commands.py:160`).
2. `examples/fakeshop/apps/kanban/tests/test_services.py::test_create_card_from_spec_creates_planned_rows_for_future_paths`
   - `assert planned_dir.is_current is False` → `assert True is False` where `True = <TrackedPath: django_strawberry_framework/mutations/>.is_current` (`test_services.py:122`).

### Check 1 — the build never touched the failing files (`git diff HEAD` empty)

`git diff HEAD -- examples/fakeshop/apps/kanban/tests/test_commands.py examples/fakeshop/apps/kanban/tests/test_services.py examples/fakeshop/apps/kanban/constants.py examples/fakeshop/apps/kanban/services.py` is **empty (exit 0)**. The two failing test files, the `constants.py` allowlist that drives the failure, and the `services.py` under test are all **byte-identical to committed HEAD** — none is in this build's authored diff (the build's diff is the `django_strawberry_framework/mutations/*`, `types/finalizer.py`, `registry.py`, `optimizer/extension.py`, `__init__.py`, the products example wiring, the `tests/mutations/*` + `tests/optimizer/test_walker.py` + `tests/base/test_init.py` re-pins, and the Slice-5 doc/DB regenerations — none of which is a kanban file).

### Check 2 — the failure is rooted in committed HEAD state, demonstrated mechanically

The two tests hardcode the planned-path constants (`test_commands.py:14-15`, `test_services.py:11-12`):

```
PLANNED_PACKAGE_DIR = "django_strawberry_framework/mutations/"
PLANNED_TEST_FILE = "tests/mutations/test_inputs.py"
```

and assert each is created as a *planned* (`is_current is False`) `TrackedPath`. But `examples/fakeshop/apps/kanban/constants.py` at HEAD now lists those paths in its **tracked/current allowlist**:

- `constants.py:175` — `"django_strawberry_framework/mutations/"` inside `TRACKED_DIRECTORY_PATHS`
- `constants.py:193` — `"tests/mutations/"` inside `TRACKED_DIRECTORY_PATHS`
- `constants.py:114` — `"tests/mutations/test_inputs.py"` in the tracked file list

So when each test imports the card with those paths, the kanban services classify them as **current** (`is_current=True`), and the `assert … is False` fails with `assert True is False`. The failing assertion references `mutations/` planned-ness; `constants.py` at HEAD already lists `mutations/` as current — the two are in direct contradiction at HEAD, with no working-tree change from this build involved.

### Check 3 — the contradiction was authored by the maintainer's own commit

`git log -1 -- examples/fakeshop/apps/kanban/constants.py` → `a1713981 036 - Add TODO comments`. The maintainer's commit `a1713981` added `mutations/` to `TRACKED_DIRECTORY_PATHS`, while the two tests (last touched 2026-06-12, before this build) still hardcode it as planned. The tests would fail on a clean checkout of HEAD with **zero** of this build's working-tree changes applied.

### Check 4 — the full sweep result matches the prediction exactly

The only two `FAILED` lines in the sweep are these exact two tests; the other 2089 collected tests pass (4 skipped are the `FAKESHOP_SHARDED`-gated tests that do not run under the default invocation, per `AGENTS.md`). No test in `tests/` (package-internal), `examples/fakeshop/apps/*/tests/` (other apps), or `examples/fakeshop/test_query/` (live) — including every test this build added under `tests/mutations/` and `examples/fakeshop/test_query/test_products_api.py` — failed.

### Classification

**Maintainer-surfaced baseline failure — NOT a build regression.** Per the task framing and `AGENTS.md` rule 33 (a file dirty/failing independent of the worker's edits is presumptively concurrent maintainer work), the gate does **not** re-loop any slice over these 2 failures. The `pytest` step is "fail" in raw terms; these 2 specific failures are classified pre-existing-at-HEAD and out of this build's scope. **No build-caused failure exists.** Anything beyond these exact 2 tests would have been a potential build regression — none surfaced.

**The one-line maintainer fix** (NOT performed here — this gate is read-only; it belongs to the maintainer): repoint the two tests' `PLANNED_PACKAGE_DIR` / `PLANNED_TEST_FILE` constants (`test_commands.py:14-15`, `test_services.py:11-12`) at a path genuinely **absent** from `constants.py`'s tracked allowlist (a still-planned future subsystem), so the "planned row ⇒ `is_current is False`" behavior the tests actually exercise is asserted against a path the allowlist does not already promote to current.

## Status decision

Per `worker-1.md` / the task's status-decision rule: the ONLY failures are the 2 confirmed-pre-existing kanban tests, and every other gate command passes — full sweep otherwise green (2089 passed), `manage.py check` clean, `makemigrations --check` clean, `ruff format --check` clean, `ruff check` clean, `git diff --check` clean. Therefore:

**`Status: final-accepted`** with the prominent gate caveat recorded at the top of this artifact. The build delivered the spec; the 2 failures predate it and are surfaced to the maintainer, not re-looped.

## Deferred work catalog

The next spec author's reading list. Walked from every per-slice artifact's spec-reconciliation notes + `### What looks solid` / `### Notes for Worker 1` sections and `bld-integration.md`'s "Deferred follow-ups walked" + "Cross-slice integration findings", cross-checked against Worker-1 memory.

- **Pre-existing kanban-example test failures** (`bld-integration.md` "Deferred follow-ups walked"; `bld-slice-5-docs_wrap.md` Notes for Worker 1; Worker-1 memory carry (e)) — `examples/fakeshop/apps/kanban/tests/test_commands.py::test_import_card_predicted_files_command_marks_directories` and `examples/fakeshop/apps/kanban/tests/test_services.py::test_create_card_from_spec_creates_planned_rows_for_future_paths` assert `django_strawberry_framework/mutations/` (+ `tests/mutations/test_inputs.py`) are *planned* (`is_current=False`), but the maintainer's `constants.py` allowlist (commit `a1713981`) now lists `mutations/` as a tracked/current path. The 2 test files + `constants.py` + `services.py` are byte-identical to HEAD; the build never touched them; they fail identically at committed HEAD. **Maintainer fix:** repoint the two tests' `PLANNED_PACKAGE_DIR` / `PLANNED_TEST_FILE` constants at a path genuinely absent from `constants.py`'s tracked allowlist. (Surfaced to the maintainer by this gate; NOT a build regression, NOT re-looped.)

- **Card-DoD `docs/spec-mutations.md` vs `docs/spec-036-mutations-0_0_11.md` filename conflict** (`bld-slice-5-docs_wrap.md`; `bld-integration.md` "Deferred follow-ups walked"; spec **Risks and open questions ~line 555**, recorded-not-reconciled) — card-036's DoD CardItem 0 reads "Add `docs/spec-mutations.md`" while the spec actually lives at the canonical structured path `docs/spec-036-mutations-0_0_11.md` (Decision 1). The spec records the conflict in its Risks section and does not reconcile it; it is a maintainer follow-up (align the card DoD text to the canonical filename), not owed within this build.

- **`Upload`-input converter seam left for `TODO-ALPHA-037-0.0.11`** (spec **Non-goals** / **Out of scope**, Decision 13; spec lines 32 / 106) — the `0.0.11` joint-cut sibling card maps `FileField` / `ImageField` to the `Upload` scalar on the **input** side this card generates. This card ships the input generator for the shipped scalar/relation set and leaves a thin converter seam (`mutations/inputs.py` scalar conversion delegates to `types/converters.py`, which `037` extends for `Upload`); `037` plugs `Upload` in without re-opening the generator. Deferred to the sibling card by spec design.

- **Cross-subsystem forward-M2M idiom — 9-site `getattr(field, "many_to_many", False)`** (`bld-integration.md` "The standing forward-M2M idiom watch" + "Cross-slice integration findings" #1; Slices 1–3 watch; Worker-1 memory carry (a)) — the forward-M2M predicate appears at 9 sites package-wide: 5 inside `mutations/` (`inputs.py:184`/`:277`/`:420`, `resolvers.py:167`) and 4 pre-existing outside it (`permissions.py:110`, `filters/sets.py:614`, `optimizer/field_meta.py:188`, `utils/relations.py:69`, `orders/inputs.py:168`). A genuine consolidation is a **repo-wide "is forward M2M" predicate** touching `optimizer/` / `filters/` / `orders/` / `utils/` / `permissions/` — a cross-subsystem refactor that belongs in its own card, NOT a mutations-card integration item (a `mutations/`-local helper would diverge from the established package-wide convention). Recorded, not flagged for a Worker 2 pass. Not a DRY defect.

- **At-threshold example-test envelope-assert helper** (`bld-slice-4-products_live.md` deferred Low; `bld-integration.md` "Cross-slice integration findings" #2; Worker-1 memory carry (c)) — `examples/fakeshop/test_query/test_products_api.py` repeats the `result["errors"][0]["field"] == <key>` envelope-assert at 3 sites (`:323` / `:357` / `:515`). At-threshold for a `_assert_field_error` test-helper, but assessed by Worker 3 as acceptable consumer-test code (test-only convenience in the example tree, distinct field keys, divergent surrounding context). A minor maintainability nicety, not a DRY defect; left to a future slice if more envelope asserts accrue.

- **Ambiguous relation-target primary silent raw-pk fallback** (`bld-integration.md` "Deferred follow-ups walked"; Slices 1–2 note; Worker-1 memory carry (b)) — `mutations/inputs.py::relation_input_annotation` silently falls back to the raw-pk scalar when a *related* model is in the ambiguous "multiple types, no declared primary" state. Decision 11's no-primary `ConfigurationError` raise is deliberately scoped to the mutation's **own** model, not its relation targets. A possible future hardening (raise at bind for an ambiguous relation target rather than silently emitting a raw-pk id) — not a defect for this card; the spec's Decision 11 scopes the raise as shipped.

No other deferral surfaced across the five slice artifacts or the integration artifact. The above six are the complete catalog.

## Final status

`final-accepted` (with the documented gate caveat). The build delivered `spec-036-mutations-0_0_11.md` end-to-end across all five slices and the cross-slice integration pass. The final gate is green on every command except the raw `pytest` status, whose only 2 failures are the rigorously-verified pre-existing-at-HEAD kanban-example tests (byte-identical to HEAD, authored by maintainer commit `a1713981`, failing identically on a clean HEAD checkout) — a maintainer-surfaced baseline failure surfaced here for maintainer resolution, NOT a build regression and NOT cause to re-loop a slice. Worker 0 may mark the final checklist box `- [x]` and hand off to the maintainer.
