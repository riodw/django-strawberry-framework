# Final test-run gate

Status: verified

## Gate

`uv run pytest`

Per `docs/review/REVIEW.md` "Final test-run gate", the only requirement is that the existing test suite passes across all three test trees (`tests/`, `examples/fakeshop/tests/`, `examples/fakeshop/test_query/`). Line coverage is intentionally **not** inspected at this stage; coverage gating belongs to CI (`pyproject.toml` `[tool.coverage.report] fail_under = 100`).

## Run

Command: `uv run pytest`
Result: PASS (722 passed, 2 skipped, 3 warnings in 25.35s)

Verbatim summary line:

```
================= 722 passed, 2 skipped, 3 warnings in 25.35s ==================
```

## Failing tests (if any)

None.

## Notes

- All 722 tests pass; 2 skipped (pre-existing, not regressions introduced by the review cycle).
- The pytest run also emits `ERROR: Coverage failure: total of 99 is less than fail-under=100` (`TOTAL 99.76%`, four uncovered lines at `django_strawberry_framework/optimizer/plans.py:288,291-292,296`). This is the coverage gate, **not** a test failure, and is explicitly out of scope for this gate per `REVIEW.md`: "Do NOT inspect or assert line coverage at this stage. The only requirement is that the existing test suite passes. Coverage gating belongs to CI ... and to the maintainer, not to this gate."
- Worker 0 should be aware of the coverage shortfall as a separate follow-up for the maintainer / CI gate, but it does not block setting `Status: verified` on the final test-run gate.
- Three pre-existing warnings (one `DATABASES` override warning in the shards-command test; two `Model 'test_choice_enums._owner' was already registered` warnings from converter tests) are unchanged background noise — not regressions.
- Ready for Worker 0 to mark the final checklist box in `docs/review/review-0_0_6.md`.
