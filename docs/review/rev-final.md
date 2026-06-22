# Review: final test-run gate (`uv run pytest`)

Status: verified

## DRY analysis

- None — final test-run gate, no code under review.

## Gate scope

Terminal gate for the `0.0.11` package review. Every per-file, folder, and project
checkbox in `docs/review/review-0_0_11.md` is `- [x]`; this is the last box. Worker 2
and Worker 3 are not involved (per `REVIEW.md` "Final test-run gate"). Worker 0 marks
the final checklist box.

Per-cycle baseline SHA: `d02e9a436cff9b644ed5a6a74f67234c231651fb`.
HEAD at gate run: `82666eac429c363df856655c5e52df20c4045080`.
Working tree at gate start was clean of source — only `docs/review/*` scratchpads and
`docs/feedback2.md` were dirty (out-of-scope per AGENTS.md #34; no source/test edits).

## Gate result

**PASS.** The summary line reports `2221 passed, 4 skipped, 4 xfailed` — zero failed,
zero errored, no collection errors. The process exit code was non-zero, driven solely
by `--cov-fail-under` reporting a coverage shortfall (99.88% < 100%); per the gate
rule that is NOT a test failure and does not flip the gate.

### Exact pytest summary line

```
============ 2221 passed, 4 skipped, 4 xfailed in 113.80s (0:01:53) ============
```

- passed: 2221
- failed: 0
- errors: 0
- collection errors: 0
- skipped: 4
- xfailed: 4

### Invocation

- Command: `uv run pytest` (project default). Run once.
- Full sweep across the test trees per `AGENTS.md`. `pytest.ini` `testpaths` collects:
  - `tests` — package tests (system-under-test is `django_strawberry_framework`)
  - `examples/fakeshop/tests` — project/config-level example tests
  - `examples/fakeshop/test_query` — live `/graphql` HTTP tests via `django.test.Client`
  - `examples/fakeshop/apps` — per-app example tests (models/admin/services/commands/in-process schema)
- `FAKESHOP_SHARDED` tests are excluded from the default invocation by design
  (AGENTS.md) — not collected here, as expected.

## Notes (follow-up signals only — NOT gate failures)

A coverage-shortfall exit code DID occur. `pytest-cov` with `[tool.coverage.report]
fail_under = 100` printed:

```
FAIL Required test coverage of 100.0% not reached. Total coverage: 99.88%
```

Package-source misses reported by `--cov-report=term-missing` (TOTAL 5915 stmts, 7 missed):

- `django_strawberry_framework/mutations/permissions.py` — 1 line: 97 (94%)
- `django_strawberry_framework/mutations/resolvers.py` — 2 lines: 206, 691 (99%)
- `django_strawberry_framework/mutations/sets.py` — 4 lines: 287, 332-333, 799 (98%)

Per `REVIEW.md` ("Do NOT inspect or assert line coverage") and `worker-1.md`
("read the summary line, not the exit code"), this coverage shortfall is recorded as a
follow-up signal for CI and the maintainer ONLY. It is NOT a test failure and does NOT
flip the gate. The non-zero process exit from `uv run pytest` is `--cov-fail-under`,
not any failing test.

- **Skips (4) / xfails (4):** expected; no failures, no errors, no collection errors.
  No owning cycle item to re-loop.

## What looks solid

### DRY recap

- None — final test-run gate, no source under review.

### Other positives

- Full suite green across all four default test trees; 2221 tests pass in ~114s.

### Summary

The full suite passes (2221 passed, 0 failed, 0 errored, 0 collection errors) across
all test trees the default invocation collects. The only non-zero signal is a
`--cov-fail-under` coverage shortfall (99.88%), which the gate explicitly discounts and
records as a CI/maintainer follow-up. Gate PASSES; `Status: verified`.
