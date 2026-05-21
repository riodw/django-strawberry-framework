# Build: Final test-run gate

Spec reference: `docs/spec-016-list_field-0_0_7.md`
Status: final-accepted

## Plan (Worker 1)

The final test-run gate is Worker-1-only. Per `docs/builder/BUILD.md` "Final test-run gate" (BUILD.md:533-555) and `docs/builder/worker-1.md` "Final test-run gate" (worker-1.md:124-141), the gate is narrow: run the six mandated commands in order, record pass/fail for each, surface deferred work in a catalog subsection (input from every slice + the integration artifact), and set the top `Status:` line to `final-accepted` (every command passes) or `revision-needed` (any failure, with the owning slice named so Worker 0 can dispatch the re-loop).

`AGENTS.md` line 4 directive applies: any failure routes back through the owning slice with a root-cause fix recommendation; never `pragma: no cover` or a test-only patch.

Inherited maintainer state at the start of this spawn (`git status --short`): `M AGENTS.md`, `M CHANGELOG.md`, `M GOAL.md`, `M KANBAN.md`, `M README.md`, `M TODAY.md`, `M docs/GLOSSARY.md`, `M docs/README.md`, `M docs/TREE.md`, `M docs/builder/bld-slice-3-optimizer_get_queryset_tests.md`, `M docs/builder/build-016-list_field-0_0_7.md`, `M docs/spec-016-list_field-0_0_7.md`, `M examples/fakeshop/apps/library/schema.py`, `M examples/fakeshop/test_query/test_library_api.py`, `M tests/test_list_field.py`, plus untracked `docs/builder/bld-integration.md`, `docs/builder/bld-slice-4-live_http_coverage.md`, `docs/builder/bld-slice-5-promotion_docs_version.md`. Every entry is either Slice-1-through-Slice-5 ship state or the pre-existing AGENTS.md root-cause-fix directive maintainer-state baked into prior spawns. `git diff --check` exits 0 against this set, so no whitespace damage anywhere in the diff (see Gate runs below).

## Gate runs

The six BUILD.md-mandated commands, run in order from the repo root:

1. `uv run pytest --no-cov` — **PASS**. Result: `754 passed, 2 skipped, 5 warnings in 26.00s`. The `--no-cov` explicitly opts out of `pytest.ini`'s auto-applied `--cov` per `BUILD.md` "Coverage is the maintainer's gate, not a worker's tool" (BUILD.md:98-111). The 2 skipped tests are the standing `FAKESHOP_SHARDED=1`-gated sharded-mode tests per `AGENTS.md` line 28 (do not run under the default invocation). Warnings are the standing `DATABASES`-override and `RuntimeWarning` `Model '_owner' was already registered` (test-fixture setup; not in this card's diff).

2. `uv run python examples/fakeshop/manage.py check` — **PASS**. Result: `System check identified no issues (0 silenced).`. Catches model/admin/url-config drift that `pytest` does not.

3. `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run` — **PASS**. Result: `No changes detected`. Confirms Slice 4's `DjangoListField`-on-`Query` add did not implicitly trigger any model-state mutation in `examples/fakeshop/apps/library/`.

4. `uv run ruff format --check .` — **PASS**. Result: `103 files already formatted`. The standing `COM812`-vs-formatter conflict warning is informational only and pre-dates this card. Read-only invocation per the gate contract (no `--fix`).

5. `uv run ruff check .` — **PASS**. Result: `All checks passed!`. Read-only invocation per the gate contract (no `--fix`).

6. `git diff --check` — **PASS**. Exit 0; no whitespace errors or conflict markers across the 15 modified + 3 untracked files in the working tree.

All six gate commands pass.

## Deferred work catalog

Walking every per-slice and integration artifact's `### Notes for Worker 1 (spec reconciliation)`, `### What looks solid`, `### Implementation notes`, `### DRY findings`, and the integration artifact's `### Deferred follow-ups` and `### Spec changes made (Worker 1 only)` sections, the following items were explicitly deferred to a future slice, future spec, or maintainer follow-up. Each bullet cites the source artifact section, the spec line that licenses the deferral (if any), and a one-line description.

1. **14-site `_isolate_global_registry` autouse fixture repo-wide consolidation.** Source: `docs/builder/bld-integration.md` "Deferred follow-ups" item 1 (lines 98-101); originally surfaced as a Low in Slice 2 review (`bld-slice-2-validation.md:207-220`) and re-confirmed in Slice 3 review (`bld-slice-3-optimizer_get_queryset_tests.md:308` — "13 sites" at Slice-3-review time, became 14 once Slice 2 added `tests/test_list_field.py`). No spec line licenses this deferral; it is accepted-with-reason at this build cycle under `AGENTS.md` line 4 (the root-cause-fix directive forbids partial consolidation when the right shape is a separate refactor spec with the full-tree blast radius). The right shape is a separate refactor spec that creates `tests/conftest.py` and lifts the autouse-`registry.clear()` fixture once for the whole `tests/` tree.

2. **`BranchType.shelves` consumer-override resolver prefetch-cache bypass.** Source: `docs/builder/bld-integration.md` "Deferred follow-ups" item 2 (lines 103); originally surfaced by Worker 3 in Slice 4 review (`bld-slice-4-live_http_coverage.md:268-272`) and recorded by Worker 1's Slice 4 final verification under `### Spec changes made (Worker 1 only)` (`bld-slice-4-live_http_coverage.md:296-300`). The override resolver at `examples/fakeshop/apps/library/schema.py:65-67` (`return list(self.shelves.order_by("-code"))`) bypasses `self._prefetched_objects_cache` and is the documented `+2` contributor to the N=4 baseline in Slice 4's `test_library_branches_via_djangolistfield_optimized_nested_selection`. No spec line licenses this deferral; spec line 17 (rev2 M2) explicitly establishes the cross-test blast-radius reason for not touching `BranchType` in this card. The right shape is a separate follow-up card that refactors the override to consult the prefetch cache before re-evaluating the relation manager, with its own contract for the cross-test impact.

3. **`utils/get_queryset.py` relocation of `_apply_get_queryset_sync` / `_apply_get_queryset_async` per Decision 3 Option B.** Source: `docs/builder/bld-integration.md` "Deferred follow-ups" item 7 (line 113); licensed by spec line 513 (Decision 3 — "Option B becomes the right move when a third call site needs the helpers"). Two call sites today: `types/relay.py:199` / `:225` (defining) and `django_strawberry_framework/list_field.py` (consuming). The natural trigger is `TODO-ALPHA-022-0.0.9` `DjangoConnectionField` shipping as the third call site; relocate at that point, not now.

4. **Version bump deferred to "the last `0.0.7` card to ship".** Source: `docs/builder/bld-slice-5-promotion_docs_version.md` (the spec-516's Slice 5 final-verification artifact); licensed by spec Decision 10 (the "Joint `0.0.7` cut" policy as named in spec body) and rev3 M1 (the "the last `0.0.7` card to ship" wording rewrite). `pyproject.toml:4` stays `version = "0.0.6"`; `django_strawberry_framework/__init__.py:26` stays `__version__ = "0.0.6"`; `tests/base/test_init.py:11` stays `assert __version__ == "0.0.6"`. This is a build-level deferral, not a slice deferral — the maintainer (or whichever later `0.0.7` card ships last) owns the actual `0.0.6` → `0.0.7` bump.

5. **The `__django_strawberry_definition__` protocol-attribute literal does not get lifted to a module-level constant.** Source: `docs/builder/bld-integration.md` "Repeated string literals" cross-file analysis (line 61); accepted-with-reason under `bld-slice-2-validation.md:282`. The literal appears in `list_field.py:75` (Slice 2 guard) and `types/base.py:245` (assignment site referenced by Slice 2's planning citation); spec line 548 uses the literal verbatim. Lifting to a constant would obscure the directly-greppable protocol-style attribute name. No future-slice action; the deferral is the steady-state shape.

6. **The intra-file repeated literal `{ allCategories { id name } }` (9 occurrences inside `tests/test_list_field.py`) is not lifted to a module-level constant.** Source: `docs/builder/bld-integration.md` "Repeated string literals / dictionary keys / tuple shapes across slices" (line 173); accepted in Slice 3 review (`bld-slice-3-optimizer_get_queryset_tests.md:310`). Each of the nine sibling behavior tests has a per-test selection-shape difference that lifting to a single constant would obscure. No future-slice action; the deferral is the steady-state shape.

7. **The `isinstance(result, models.Manager)` / `isinstance(result, models.QuerySet)` post-process pair is duplicated across the sync and async `_post_process_consumer_*` helpers (`list_field.py:31-35` and `:39-43`).** Source: `docs/builder/bld-integration.md` "Repeated ORM/queryset patterns" (line 146); accepted-with-reason in Slice 1 review (`bld-slice-1-module_factory.md:390-391`); justified by spec Decision 2's "Async-detection asymmetry" subsection (spec lines 472-477). The duplication is intentional per rev6 H2 / rev6 H3; collapsing would force a runtime branch on `in_async_context()` inside what the spec pins as a per-construction-static choice. No future-slice action; the deferral is the steady-state shape.

Catalog count: **7 deferrals.** Two trigger a future card or refactor spec (items 1, 2). One is licensed by the spec for a future slice (item 3). One is a maintainer follow-up at the cut (item 4). Three are steady-state DRY-vs-readability decisions where the deferral is the right shape forever (items 5, 6, 7) — included for completeness so the next spec author sees the full reasoning surface, not just the action items.

## Final outcome

`final-accepted`. Every one of the six BUILD.md-mandated gate commands passes against the working tree composed of Slices 1-5 + the cross-slice integration pass. No slice re-loop is required.

### Summary

The build delivered spec-016 `DjangoListField` end-to-end across the six slices the spec checklist named: Slice 0 (pre-implementation verification spike), Slice 1 (`list_field.py` factory + public re-export), Slice 2 (four `ConfigurationError` validation guards), Slice 3 (14 package-internal optimizer + `get_queryset` cooperation tests), Slice 4 (live HTTP coverage via `all_library_branches_via_list_field` on `apps/library/schema.py`'s `Query` and the `assert len(captured) == 4` HTTP test), and Slice 5 (promotion + 8-surface docs sweep + KANBAN move to `DONE-016-0.0.7` + CHANGELOG `### Added` append). The integration pass found zero cross-slice DRY violations that warranted a Worker 2 consolidation loop. The final test-run gate runs all six commands clean: `pytest --no-cov` (754 passed, 2 skipped), Django `check` (no issues), `makemigrations --check --dry-run` (no changes), `ruff format --check` (103 files formatted), `ruff check` (all checks passed), `git diff --check` (exit 0). Seven deferrals are catalogued (two trigger a future card/refactor spec, one is spec-licensed for the third-call-site trigger, one is the maintainer's `0.0.7` cut version bump, three are steady-state DRY-vs-readability decisions). Version is intentionally left at `0.0.6` per Decision 10 / rev3 M1.

### Spec changes made (Worker 1 only)

No spec edits required at the final gate. The spec status line at line 4 (`draft (revision 6, post-rev5 scaffolding review)`) describes the spec's authoring state (the revision history kept inline in the spec), not the build's ship state — the per-slice ship state is tracked by the build plan's checkbox column, which Worker 0 owns. Spec line 6's `DONE-016-0.0.7 (was WIP-ALPHA-016-0.0.7 until Slice 5's column move)` already reflects the column move Slice 5 landed. The two spec edits Worker 1 made during Slice 5 (line 6 Predecessors flip; line 149 README sub-bullet tightening) and Slice 0 (line 96 lambda-vs-annotated-resolver shape) remain accurate after the final gate.
