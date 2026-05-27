# Build: Final test-run gate

Spec reference: `docs/spec-020-scalar_map_helper-0_0_7.md`
Build plan: `docs/builder/build-020-scalar_map_helper-0_0_7.md`
Status: final-accepted

## Gate commands

Each command was run from the repository root with the working tree in the post-integration state (every slice's source/test/doc edits applied; all five slice artifacts plus `bld-integration.md` final-accepted). Commands ran in the order pinned by `docs/builder/BUILD.md` "Final test-run gate" and `docs/builder/worker-1.md` "Final test-run gate".

### `uv run pytest --no-cov`

- Exit code: 0
- Summary: 817 passed, 3 skipped, 6 warnings in 46.94s. Full sweep across all three test trees per `AGENTS.md` (package `tests/`, example non-HTTP `examples/fakeshop/tests/`, live HTTP `examples/fakeshop/test_query/`). The explicit `--no-cov` flag is REQUIRED here because `pytest.ini`'s `addopts` auto-applies `--cov`; coverage is the maintainer's gate, not a worker's. The skips are pre-existing (sharded-mode tests gated by `FAKESHOP_SHARDED=1` per `AGENTS.md` line 29) and the warnings are pre-existing (Django `RuntimeWarning` from test-time model re-registration plus two `UserWarning`s from `settings.DATABASES` overrides inside `seed_shards` tests). No new pytest items were added or removed by this gate; the sweep confirms every test added across Slices 1–5 plus the consolidation pass still passes against the live tree.

### `uv run python examples/fakeshop/manage.py check`

- Exit code: 0
- Summary: `System check identified no issues (0 silenced).` Django's system-check framework against the example project confirms the `INSTALLED_APPS` resolution, the `django_strawberry_framework` AppConfig's `ready()` body, and the example app schemas remain consistent. Catches model/admin/url-config drift that `pytest` does not.

### `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run`

- Exit code: 0
- Summary: `No changes detected`. The example project's model state matches the on-disk migrations; this build delivered zero model changes, which matches the spec (Slice 3's two-edit migration on `examples/fakeshop/config/schema.py` is a schema-construction-site rewrite, not a model change).

### `uv run ruff format --check .`

- Exit code: 0
- Summary: `118 files already formatted`. Read-only format check (no `--fix` passed per gate contract). The pre-existing `COM812`-with-formatter conflict warning is unchanged from the pre-build baseline and is not a gate failure. Every source / test / doc edit across Slices 1–5 plus the integration consolidation pass landed in already-formatted shape.

### `uv run ruff check .`

- Exit code: 0
- Summary: `All checks passed!` Read-only lint check (no `--fix` passed per gate contract). Confirms every new line of logic across `django_strawberry_framework/scalars.py`, `django_strawberry_framework/__init__.py`, `tests/test_scalars.py`, `tests/base/test_init.py`, `tests/types/test_converters.py`, and `examples/fakeshop/config/schema.py` complies with the project's lint rules including `COM812` (trailing comma on multi-arg calls) and `ERA001` (no orphan commented-out code).

### `git diff --check`

- Exit code: 0
- Summary: No whitespace errors or conflict markers anywhere in the working tree. The full mutation surface across Slices 1–5 plus the consolidation pass (`CHANGELOG.md`, `GOAL.md`, `KANBAN.md`, `TODAY.md`, `django_strawberry_framework/__init__.py`, `django_strawberry_framework/scalars.py`, `docs/GLOSSARY.md`, `docs/README.md`, `docs/spec-020-scalar_map_helper-0_0_7-terms.csv`, `docs/spec-020-scalar_map_helper-0_0_7.md`, `examples/fakeshop/config/schema.py`, `tests/base/test_init.py`, `tests/test_scalars.py`, `tests/types/test_converters.py`) plus the seven untracked build artifacts under `docs/builder/` are diff-clean.

## Deferred work catalog

Cross-walked every per-slice artifact (`bld-slice-1` through `bld-slice-5`) and `bld-integration.md` for `### Notes for Worker 1 (spec reconciliation)`, `### What looks solid`, and explicit deferral language. Confirmed via `bld-integration.md` lines 107–122 (Deferred work surfaced) and 272–276 (post-consolidation retained catalog).

- **`docs/TREE.md` lines 201 / 246 — stale "Strawberry deprecation suppressed at definition site" wording at the entries describing `scalars.py`.** Source: Slice 4 final-verification + Slice 4 build-report `### Notes for Worker 1 (spec reconciliation)` #3 + `bld-integration.md` Deferred work surfaced #1 + integration re-pass carry-forward. License: spec DoD item 13 forbids editing `docs/TREE.md` in this card (`docs/spec-020-scalar_map_helper-0_0_7.md` Slice 4 sub-bullet "`docs/TREE.md`: no edit. The helper is added to the existing `django_strawberry_framework/scalars.py` module... the current-on-disk-layout enumeration in `docs/TREE.md` already mentions `scalars.py`; the entry stays as-is since the file's role is unchanged"). Recommendation: future maintainer-led `docs/TREE.md` refresh card to retire the now-obsolete wording (Slice 1 removed the suppression block and migrated to the no-warning `strawberry.scalar(name=..., serialize=..., parse_value=...)` overload, so the "suppressed at definition site" claim is factually stale post-`[Unreleased]`).

- **`KANBAN.md` line 50 — `### In progress` paragraph carries the forward-looking sentence "The last `0.0.7` card to ship owns the version bump from `0.0.6` per Decision 10 of `docs/SPECS/spec-016-list_field-0_0_7.md`."** Source: Slice 5 Worker 3 review + Slice 5 Worker 1 final-verification + `bld-integration.md` Deferred work surfaced #3. License: dispositioned at Slice 5 review as "no spec edit needed; informational maintainer-cut-time content" (no spec-level license required because the wording is informational and forward-looking, not a contract). Now mildly stale because `DONE-047-0.0.7` is the last `0.0.7` card per Decision 8 of `docs/spec-020-scalar_map_helper-0_0_7.md` and explicitly defers the version bump to a future maintainer cut. Recommendation: maintainer cleanup at the next version cut (when `[Unreleased]` is promoted to `[0.0.8]` and `pyproject.toml` + `django_strawberry_framework/__init__.py` + `tests/base/test_init.py` version pins are bumped in one atomic commit per Decision 8).

No other deferrals surfaced by the cross-slice walk. Integration finding #2 (the `docs/GLOSSARY.md` line 40 stale `_Note:_` paragraph) was cleared in-cycle by the Worker 2 consolidation pass under `bld-integration.md` and is intentionally NOT in this catalog — the consolidation routed the `_Note:_` text through the `strawberry_config` factory anchor and named the no-warning overload verbatim, leaving zero matches for `"suppressed at the definition site"` in `docs/GLOSSARY.md`.

## Summary

The build delivered the spec end-to-end across all five slices plus a Worker 2 consolidation pass that resolved the single coherence-of-story finding the cross-slice integration scan surfaced. Every gate command exits 0: the 817-test sweep passes (skips are pre-existing sharded-mode tests; warnings are pre-existing test fixtures), the Django consistency check and migrations-drift check both report no issues, both ruff invocations confirm the working tree is already formatted and lint-clean, and `git diff --check` finds no whitespace damage. Two stale-wording sites in standing docs (`docs/TREE.md` lines 201 / 246 and `KANBAN.md` line 50) are explicitly deferred to future maintainer-led cleanup — the spec's DoD scope forbids touching either in this card. Status: `final-accepted`. Worker 0 may now mark the final checkbox `- [x]` on `docs/builder/build-020-scalar_map_helper-0_0_7.md` and hand the build off to the maintainer for commit.
