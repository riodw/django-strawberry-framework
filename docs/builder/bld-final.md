````text
# Build: Final test-run gate — build-017 (apps / 0.0.7)

Spec reference: `docs/SPECS/spec-017-apps-0_0_7.md`
Build plan: `docs/builder/build-017-apps-0_0_7.md`
Status: final-accepted

This artifact is the Worker 1-owned final test-run gate that closes build-017. Per `docs/builder/BUILD.md` "Final test-run gate" lines 533-555 and `docs/builder/worker-1.md` "Final test-run gate" lines 124-141, the gate runs six narrow commands and walks every per-slice and integration artifact for a deferred-work catalog. Per the build plan's preamble (`docs/builder/build-017-apps-0_0_7.md:6`), the pre-flight baseline is `clean`; no pre-flight baseline exception is recorded, so any gate failure here blocks `final-accepted` and is routed back through the owning slice loop.

## Gate results

| # | Command | Result |
|---|---|---|
| 1 | `uv run pytest --no-cov` | **pass** — 764 passed, 2 skipped, 5 warnings in 26.82s |
| 2 | `uv run python examples/fakeshop/manage.py check` | **pass** — `System check identified no issues (0 silenced).` |
| 3 | `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` | **pass** — `No changes detected` |
| 4 | `uv run ruff format --check .` | **pass** — `105 files already formatted` (the standing `COM812`-vs-formatter conflict warning is the pre-existing repo-wide notice, not introduced by this build) |
| 5 | `uv run ruff check .` | **pass** — `All checks passed!` |
| 6 | `git diff --check` | **pass** — exit 0; no whitespace errors or conflict markers in the working tree |

### Per-command details

1. **`uv run pytest --no-cov`** — full sweep across all three test trees (`tests/`, `examples/fakeshop/tests/`, `examples/fakeshop/test_query/`) per `AGENTS.md` line 6. The explicit `--no-cov` opts out of `pytest.ini`'s auto-applied `--cov` per `BUILD.md` line 109 ("the only permitted coverage-shaped flag"). Result: `764 passed, 2 skipped, 5 warnings in 26.82s`. The 2 skips are the pre-existing `tests/types/test_converters.py` parametrized cases (unchanged by this build); the 5 warnings are the standing `Overriding setting DATABASES` notice from `examples/fakeshop/tests/test_commands.py::test_seed_shards_command_runs_when_shard_alias_present` plus the four `RuntimeWarning: Model 'test_choice_enums._owner' was already registered` model-reload notices in `tests/types/test_converters.py` (all four pre-existing, none introduced by this build). The 5 Slice 2 tests at `tests/test_apps.py` are part of the 764 passed count.
2. **`uv run python examples/fakeshop/manage.py check`** — Django's system-check framework against the fakeshop example. Catches model/admin/url-config drift that `pytest` does not. Output: `System check identified no issues (0 silenced).`. Confirms the explicit `DjangoStrawberryFrameworkConfig` registered cleanly under the existing `examples/fakeshop/config/settings.py:48` `INSTALLED_APPS` entry (Decision 7 contract held).
3. **`uv run python examples/fakeshop/manage.py makemigrations --check --dry-run`** — confirms no pending migrations exist. Output: `No changes detected`. The build introduced zero Django models (per Decision 5 — package ships zero Django models), so this gate confirms model state remains migration-consistent.
4. **`uv run ruff format --check .`** — read-only formatter check (NO `--fix`, NO auto-format). Output: `105 files already formatted`. The single `warning: The following rule may cause conflicts ...` line about `COM812` is the standing repo-wide notice surfaced on every ruff invocation; it is not a failure, not introduced by this build, and is explicitly tracked at `AGENTS.md` line 17 ("COM812 enabled: trailing comma on multi-arg calls expands the layout and locks it in; do not remove").
5. **`uv run ruff check .`** — read-only lint check (NO `--fix`). Output: `All checks passed!`. Confirms no `D100` / `D101` / line-length / COM812 / ERA001 violations across the working tree.
6. **`git diff --check`** — exit 0, no output. Confirms zero whitespace errors (trailing whitespace, tab/space mismatches per the repo's `.gitattributes`) and zero conflict markers (`<<<<<<<` / `=======` / `>>>>>>>`) anywhere in the modified working tree.

Every gate command passed; no command failed; no slice needs a re-loop.

### Deferred work catalog

Walked every per-slice and integration artifact's `### Spec changes made (Worker 1 only)`, `### Notes for Worker 1 (spec reconciliation)`, `### What looks solid`, and `### DRY findings` sections looking for explicit deferrals to a future slice, a future spec, or maintainer follow-up:

- **`docs/builder/bld-slice-1-module_appconfig.md`** — Worker 2 `### Notes for Worker 1 (spec reconciliation)`: `None.`. Worker 3 `### Notes for Worker 1 (spec reconciliation)`: `None.`. Worker 1 final-verification `### Spec changes made (Worker 1 only)`: `None.`. `### What looks solid` and `### DRY findings` surface no deferrals — every observation describes work that landed in-slice.
- **`docs/builder/bld-slice-2-tests.md`** — Worker 2 `### Notes for Worker 1 (spec reconciliation)`: "No spec gaps, conflicts, or unstated assumptions surfaced during implementation." Worker 3 `### Notes for Worker 1 (spec reconciliation)`: `None. The diff matches the plan exactly; no spec ambiguity, no implementation drift, no follow-up slice candidate surfaced.` Worker 1 final-verification `### Spec changes made (Worker 1 only)`: `None.`. `### What looks solid` and `### DRY findings` surface no deferrals.
- **`docs/builder/bld-slice-3-promotion_docs.md`** — Worker 2 `### Notes for Worker 1 (spec reconciliation)`: `None.`. Worker 3 `### Notes for Worker 1 (spec reconciliation)`: `None. The diff matches the spec verbatim where verbatim was required and matches the plan-authorized discretion items where discretion was allowed. No spec edits are warranted from this review pass.` Worker 1 final-verification `### Spec changes made (Worker 1 only)`: `None.`. `### What looks solid` and `### DRY findings` surface no deferrals.
- **`docs/builder/bld-integration.md`** — `### Findings`: `None. Every check above lands clean.`. `### Consolidation work needed?`: `No.`. `### Spec changes made (Worker 1 only)`: `None.`. No carried-over deferred work; no consolidation loop dispatched.

**Known spec-licensed deferral (carried into this catalog per the required walk):**

- **Version bump to `0.0.7`** — deferred to the last `0.0.7` card to ship. Source artifact section: `docs/builder/bld-slice-3-promotion_docs.md` Slice 3 spec checklist box "Version bump (deferred to **the last `0.0.7` card to ship**, NOT this card; per [Decision 6](#decision-6--joint-0_0_7-cut))" and the corresponding plan / build-report / review / final-verification confirmations that `pyproject.toml`, `django_strawberry_framework/__init__.py`'s `__version__`, and `tests/base/test_init.py`'s version assertion all remain at `0.0.6`. Licensing spec line: `docs/SPECS/spec-017-apps-0_0_7.md:301-316` ([Decision 6 — Joint `0.0.7` cut](../SPECS/spec-017-apps-0_0_7.md#decision-6--joint-0_0_7-cut)) and the Slice 3 checklist version-bump sub-bullet at `docs/SPECS/spec-017-apps-0_0_7.md:74` ("Version bump (deferred to **the last `0.0.7` card to ship**, NOT this card; per [Decision 6](#decision-6--joint-0_0_7-cut)): see [`spec-016`](SPECS/spec-016-list_field-0_0_7.md) Decision 10. This card does NOT bump `pyproject.toml`, `django_strawberry_framework/__init__.py`'s `__version__`, or `tests/base/test_init.py`'s version assertion."). One-line description: the joint-cut `0.0.7` release groups four WIP cards (017 / 018 / 019 / 045) into one version-string bump; whichever of the remaining three (018 / 019 / 045) merges last owns the bump to `0.0.7` in `pyproject.toml`, `__version__`, and `tests/base/test_init.py`'s version assertion, plus the corresponding `[Unreleased]` → `[0.0.7]` release-date wording in `CHANGELOG.md` if any wording-level reconcilation is needed. This deferral is the only explicit one across the build.

No build-017-introduced deferrals beyond the spec-licensed version-bump pin above. The build delivered the spec end-to-end at the slice level.

### Summary

Build-017 closes clean: all three slices reached `final-accepted` per `docs/builder/build-017-apps-0_0_7.md:20-22`; the cross-slice integration pass reached `final-accepted` per `docs/builder/bld-integration.md` with no consolidation work needed; this final test-run gate's six commands all pass with no failures, no pre-flight baseline exceptions exercised, and no slice re-loop dispatched. The build shipped `django_strawberry_framework/apps.py` (10 lines: D100 module docstring, `from django.apps import AppConfig`, `DjangoStrawberryFrameworkConfig(AppConfig)` with D101 class docstring, `name = "django_strawberry_framework"`, `verbose_name = "Django Strawberry Framework"`; no `ready()`, `label`, `default_auto_field`, or `default`); `tests/test_apps.py` (39 lines: 4 positive contract pins + 1 consolidated negative-shape test iterating the four-key forbidden behavioral set as a single pytest item per rev4 Informational #2); and six Markdown promotion edits across `docs/GLOSSARY.md`, `docs/README.md`, `docs/TREE.md`, `KANBAN.md`, and `CHANGELOG.md` (status flip, heading bump, bullet add, surgical removal, current-tree + target-layout updates, KANBAN column move as `DONE-017-0.0.7`, CHANGELOG verbatim append). Public surface (`__init__.py` `__all__`) is unchanged per Decision 3; package version stays pinned at `0.0.6` per Decision 6's joint-cut deferral; the only deferral in the catalog is the version bump itself, which is spec-licensed and will be owned by whichever of the remaining `0.0.7` cards (018 / 019 / 045) ships last. Artifact `Status:` set to `final-accepted`; Worker 0 may mark the final checkbox `- [x]` in `docs/builder/build-017-apps-0_0_7.md:24`.
````
