# Feedback: `docs/spec-019-multi_db-0_0_7.md` and multi-DB example-project changes

Reviewed the current `main` state after the completed spec + example-project changes, focusing on:

- `docs/spec-019-multi_db-0_0_7.md`
- `examples/fakeshop/config/settings.py`
- `examples/fakeshop/apps/products/management/commands/seed_shards.py`
- `examples/fakeshop/tests/test_commands.py`
- `examples/fakeshop/test_query/test_multi_db.py`
- `tests/optimizer/test_multi_db.py`
- `tests/types/test_resolvers.py`
- related docs / release notes

Validation spot-checks run during review:

- `FAKESHOP_SHARDED=1 uv run pytest --no-cov examples/fakeshop/test_query/test_multi_db.py -q` — **passed** (`2 passed`).
- `FAKESHOP_SHARDED=1 uv run pytest --no-cov examples/fakeshop/tests/test_commands.py::test_seed_shards_command_raises_when_shard_alias_missing -q` — **failed**, confirming H1 below. Failure was `RuntimeError: Database access not allowed...` after the command proceeded past the missing-alias guard under sharded settings.

---

## High

### H1 — The documented sharded example test command fails because `test_seed_shards_command_raises_when_shard_alias_missing` is environment-dependent

Two docs now advertise running the example suite in sharded mode:

- `examples/fakeshop/README.md #"FAKESHOP_SHARDED=1 uv run pytest examples/fakeshop"` — `FAKESHOP_SHARDED=1 uv run pytest examples/fakeshop`
- `examples/fakeshop/config/settings.py #"FAKESHOP_SHARDED=1 uv run pytest                              # sharded"` — `FAKESHOP_SHARDED=1 uv run pytest  # sharded`

But `examples/fakeshop/tests/test_commands.py::test_seed_shards_command_raises_when_shard_alias_missing` defines `test_seed_shards_command_raises_when_shard_alias_missing()` without forcing the alias-missing condition. Under default settings this test passes because `shard_b` is absent and `seed_shards` raises before DB access. Under `FAKESHOP_SHARDED=1`, `shard_b` is present, so the command proceeds to `migrate` / seeding. The test is not marked for DB access, so the advertised sharded pytest invocation fails with pytest-django's database-access guard instead of the intended `CommandError` assertion.

Fix options:

1. Make the test independent of the process environment by using the `settings` fixture to remove `shard_b` before calling the command, e.g. set `settings.DATABASES` to a default-only mapping for this test. This is the strongest fix because the test name promises missing-alias behavior regardless of how pytest was launched.
2. Alternatively, mark/skip this test when `FAKESHOP_SHARDED=1`, but that preserves an environment-dependent hole in the command tests.
3. If the intended supported sharded command is only the live HTTP file, narrow the docs to `FAKESHOP_SHARDED=1 uv run pytest examples/fakeshop/test_query/test_multi_db.py`; otherwise make the whole advertised `examples/fakeshop` sharded suite pass.

### H2 — The spec still contains stale mutually-exclusive / no-settings-change claims after the additive DATABASES refactor

The implementation and user-facing docs now correctly describe an additive layout: `default → db.sqlite3` in both modes, and `FAKESHOP_SHARDED=1` adds `shard_b → db_shard_b.sqlite3`.

However the spec still has old statements:

- `docs/spec-019-multi_db-0_0_7.md #"ships an additive `DATABASES` layout: `default → db.sqlite3` is declared unconditionally in both single-DB and sharded modes"` says the sharded layout is “mutually exclusive with the single-DB `db.sqlite3` mode.” That contradicts the current implementation and the revised Problem statement.
- `docs/spec-019-multi_db-0_0_7.md #"5. `examples/fakeshop/config/settings.py` ships an additive `DATABASES` layout"` says `examples/fakeshop/config/settings.py` is NOT modified. It is now deliberately modified to implement/document the additive layout.

Fix: update the Current state bullet and Definition of done item 5 so the spec consistently says `settings.py` is modified to keep `default` on `db.sqlite3` and add `shard_b` only under `FAKESHOP_SHARDED=1`. The DoD should no longer require `settings.py` to be untouched.

### H3 — Decision 5 still describes two optimizer-plan tests even though the current contract has one

Most of the spec now reflects the rev5 decision to drop the package-internal `OptimizationPlan.apply` test and verify axis 2 through the live HTTP test. A few stale references remain:

- `docs/spec-019-multi_db-0_0_7.md #"Slice 1: Package-internal tests (split across two files"` says `tests/optimizer/test_multi_db.py` holds `OptimizationPlan.apply` / consumer-`Prefetch` round-trip tests.
- `docs/spec-019-multi_db-0_0_7.md #"`tests/optimizer/test_multi_db.py` (new; optimizer-plan-level)"` says `tests/optimizer/test_multi_db.py` contains “the two `OptimizationPlan.apply` / `OptimizerHint.prefetch` round-trip tests.”

The actual file contains only `test_consumer_provided_prefetch_via_optimizer_hint_round_trips_using_alias()`, and the Test plan / DoD later say one optimizer-plan-level test.

Fix: update Decision 5 and the Slice checklist intro to say the optimizer file contains exactly one optimizer-plan test for consumer-provided `OptimizerHint.prefetch(Prefetch(queryset=...using...))`; axis 2 is verified by `examples/fakeshop/test_query/test_multi_db.py::test_using_shard_b_resolver_returns_rows_seeded_on_shard_b`.

---

## Medium

### M1 — Top-level spec metadata still says draft / WIP after the card moved to Done

The spec front matter still says:

- `docs/spec-019-multi_db-0_0_7.md #"Status: shipped"` — `Status: draft`
- `docs/spec-019-multi_db-0_0_7.md #"Predecessors: [`docs/GLOSSARY.md`]"` — predecessor references the `WIP-ALPHA-019-0.0.7` card

But `KANBAN.md` now records `DONE-019-0.0.7` and the implementation is finished. If this repo intentionally leaves active specs as “draft” forever, add a short note explaining that convention; otherwise update the status and card reference to match the Done state so future readers do not think this is still pre-implementation.

### M2 — Fakeshop README still documents the old test-user count and omits `view_entry`

`examples/fakeshop/README.md #"Each set creates"` says each `create_users` set creates 5 users, and the following list includes only:

- `staff_N`
- `regular_N`
- `view_category_N`
- `view_item_N`
- `view_property_N`

Current `create_users()` creates 6 users per set: staff, regular, and one user for each of the four `VIEW_PERMISSIONS`, including `view_entry`. `docs/README.md` already has the correct “6 users” wording.

Fix: update the fakeshop README to say 6 users per set and include `view_entry_N` in the bullet list.

### M3 — `seed_shards` stress-test guidance encourages mutating a tracked SQLite fixture without warning

`examples/fakeshop/apps/products/management/commands/seed_shards.py #"The committed shard file is not touched"` says the committed shard file is not touched by the test suite and therefore growing it with millions of rows for load testing is safe.

That is safe from pytest isolation, but `examples/fakeshop/db_shard_b.sqlite3` is a tracked fixture. Running `seed_shards --count 5000` against the default path mutates a tracked binary file and can leave a huge dirty diff that is easy to commit accidentally.

Fix: keep the stress-testing note, but add a VCS warning and a safer workflow. For example: tell developers to copy the shard DB to a scratch path / temporary checkout before high-volume loads, or explicitly discard `examples/fakeshop/db_shard_b.sqlite3` after stress testing unless they intend to refresh the committed fixture.

---

## What looks solid

- The new live sharded HTTP tests in `examples/fakeshop/test_query/test_multi_db.py` are structurally sound and pass under `FAKESHOP_SHARDED=1`. The holder-pattern schema fixture, module-level URLConf, `override_settings(ROOT_URLCONF=__name__)`, and copied reload fixture line up with the spec’s R4/R5 decisions.
- The additive `DATABASES` layout in `examples/fakeshop/config/settings.py` is simpler than the earlier mutually-exclusive shard-a/shard-b shape and matches the updated docs in `docs/README.md` and `examples/fakeshop/README.md`.
- The package-internal tests in `tests/types/test_resolvers.py` and `tests/optimizer/test_multi_db.py` match the narrowed contract: FK-id elision is tested at resolver level with a mocked router, strictness uses `kind="forward_single"`, and consumer-provided `Prefetch(queryset=...using...)` is tested at the optimizer-plan layer.
- The `Meta.optimizer_hints` / `OptimizerHint.prefetch` path is now explicit enough in the spec and tests to avoid the earlier generated-prefetch `_db` overclaim.

End of feedback.
