# Review: final test-run gate

Status: verified

## Command Run

- `uv run pytest`

## Result

- Pass.
- Exit code: 0.
- Summary: 564 passed, 1 skipped, 3 warnings in 24.71s.
- Testpaths exercised by configured pytest run: `tests`, `examples/fakeshop/tests`, `examples/fakeshop/test_query`.

## Relevant Output Summary

- Pytest collected 565 items.
- Final line: `564 passed, 1 skipped, 3 warnings in 24.71s`.
- Coverage output was emitted by the configured pytest run, but line coverage was not inspected for this gate.

## Warnings

- `examples/fakeshop/tests/test_commands.py::test_seed_shards_command_runs_when_shard_alias_present`
  emitted Django's warning that overriding `DATABASES` can lead to unexpected behavior.
- Two `tests/types/test_converters.py` cases emitted Django's runtime warning that a test model was already
  registered.

## Errors

None.
