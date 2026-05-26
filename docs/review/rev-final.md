# Review: final test-run gate (`uv run pytest`)

Status: verified

## Gate scope

Final test-run gate per `docs/review/REVIEW.md` "Final test-run gate" and `worker-1.md` "Final test-run gate job". One full sweep of `uv run pytest` across all three test trees (`tests/`, `examples/fakeshop/tests/`, `examples/fakeshop/test_query/`) per `AGENTS.md`. Coverage is NOT inspected at this gate; CI owns `fail_under = 100`. Coverage-shortfall exit codes are NOT test failures — the gate parses the `=== N passed ... ===` summary line as the source of truth.

## Command

```shell
uv run pytest
```

Invoked from repo root (`/Users/riordenweber/projects/django-strawberry-framework`). Default `pyproject.toml` / `pytest.ini` configuration; no test selection, no marker filtering, no `FAKESHOP_SHARDED` (per `AGENTS.md` line 28 sharded-specific tests stay behind that env flag and do not run under the default invocation).

## Result

**PASS.** Pytest summary line verbatim:

```
================= 800 passed, 3 skipped, 6 warnings in 37.61s ==================
```

- `passed`: 800
- `skipped`: 3
- `failed`: 0
- `errored`: 0 (no collection errors)
- Runtime: 37.61s
- Warnings: 6 (informational; see Notes)

Gate-criteria parse: pass count > 0 AND zero `failed` / `errored` count → gate passes per `worker-1.md` "Coverage-gate vs test-failure: read the summary line, not the exit code".

## Notes

### Coverage shortfall (informational only — NOT a gate failure)

Pytest emitted a coverage-shortfall message on top of the passing summary line:

```
ERROR: Coverage failure: total of 99 is less than fail-under=100
FAIL Required test coverage of 100.0% not reached. Total coverage: 99.95%
```

Per-module table shows one missing line:

```
django_strawberry_framework/_django_patches.py    28    1    96%   179
```

All other 31 in-scope source modules report 100%. Total: 1836 statements, 1 missed, 99.95% coverage.

Per `REVIEW.md` "Final test-run gate" and `worker-1.md` final-gate subsection, coverage gating belongs to CI and the maintainer. This signal is recorded here as a follow-up for the maintainer; it does NOT flip the gate. The `_django_patches.py:179` miss is logged for maintainer triage outside this review run.

### Warnings (informational)

Six warnings in the summary line; all pre-existing and unrelated to the gate:

- `examples/fakeshop/tests/test_commands.py::test_seed_shards_command_runs_when_shard_alias_present` and `::test_seed_shards_command_raises_when_shard_alias_missing` — two `UserWarning: Overriding setting DATABASES can lead to unexpected behavior` warnings from intentional `settings.DATABASES` overrides in seed_shards command tests.
- Four `tests/types/test_converters.py` tests — `RuntimeWarning: Model 'test_choice_enums._owner' was already registered` from intentional test-time model re-registration.

No new warning categories; no new deprecation surfaces.

### Skipped tests (informational)

3 skipped tests in the run; pre-existing skips. No change to skip surface in this gate.

## Gate disposition

Tests pass. Worker 1 sets `Status: verified` directly per `REVIEW.md` "Artifact `Status:` legend" (`rev-final.md` is the documented exception where Worker 1 owns the terminal status and Worker 0 marks the checklist box afterward). Worker 2 and Worker 3 are not involved in this gate.

## Summary

Full pytest sweep across all three test trees passes cleanly: 800 passed, 3 skipped, 0 failed, 0 errored, 37.61s runtime. Coverage shortfall (99.95% vs CI's `fail_under = 100`) is recorded here as an informational follow-up for the maintainer per the gate's explicit charter; it does NOT constitute a test failure. Gate verified.
