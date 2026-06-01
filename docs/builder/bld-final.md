# Build: Final test-run gate

Spec reference: `docs/spec-027-filters-0_0_8.md` (whole spec; all six in-scope slices + Slice 4a + cross-slice integration pass already at `final-accepted` in their respective artifacts).
Build plan: `docs/builder/build-021-filters-0_0_8.md`
Status: final-accepted

## Spec status-line re-verification

Per `worker-1.md` "Spec status-line re-verification (every Worker 1 spawn)" — re-read `docs/spec-027-filters-0_0_8.md` L4. The Status line already describes the shipped reality of the build: Slices 1-3 (core wiring), Slice 4 (live HTTP coverage), Slice 4a (tree-form logic substrate; `test_library_books_filter_combines_and_or_not` flipped from a strict xfail to a passing test in the same change), Slice 5 (docs / KANBAN / CHANGELOG, joint-cut safe-default path), Slice 6 (carried by sibling per Slice-checklist conditional). The line names the joint-cut deferrals (Decision 10) explicitly. No edit needed in this pass.

## Gate commands (run in order)

### 1. Full pytest sweep — `uv run pytest --no-cov`

PASS. `971 passed, 3 skipped, 103 warnings in 29.36s`. Explicit `--no-cov` opts out of `pytest.ini`'s auto-applied `--cov` per BUILD.md "Coverage is the maintainer's gate, not a worker's tool".

Specifically verified:

- `examples/fakeshop/test_query/test_library_api.py::test_library_books_filter_combines_and_or_not` — **PASSED naturally** (no `@pytest.mark.xfail` decorator remains; Slice 4a's substrate makes the test pass without the marker, matching Worker 2's Slice-4a build report which stripped the decorator).
- `tests/base/test_init.py::test_version` — PASSED. The pin asserts `__version__ == "0.0.7"` per Decision 10's joint-cut safe-default; the joint-cut version bump trio (`pyproject.toml [project].version`, `django_strawberry_framework/__init__.py __version__`, `tests/base/test_init.py` pin update) is correctly deferred and surfaces in the deferred-work catalog below.
- 3 skipped tests are pre-existing (one Slice-4a deferred-work skip plus two unrelated test-suite skips that predate this build, per integration-pass artifact's final-verification note).

### 2. Django system check — `uv run python examples/fakeshop/manage.py check`

PASS. `System check identified no issues (0 silenced).`

### 3. Migration consistency — `uv run python examples/fakeshop/manage.py makemigrations --check --dry-run`

PASS. `No changes detected`. Confirms the Slice-4 `examples/fakeshop/apps/library/migrations/0004_patron_email.py` migration covers the `Patron.email` field addition and no further migrations are required from this build's model edits.

### 4. Lint / format / diff gate

- `uv run ruff format --check .` — PASS. `148 files already formatted`. (The `COM812` warning about formatter-conflict is a pre-existing baseline notice from `pyproject.toml`'s ruff config, not a finding against this build.) Read-only check; no `--fix` passed.
- `uv run ruff check .` — PASS. `All checks passed!` Read-only check; no `--fix` passed.
- `git diff --check` — PASS. No output (no whitespace errors or conflict markers anywhere in the working tree).

The pre-flight baseline recorded `M docs/feedback.md` as the maintainer's in-progress review-iteration scratchpad (out-of-scope per AGENTS.md L33). `git diff --check` does not flag it, so the AGENTS.md L33 "do not auto-revert" disposition holds without escalation.

## Spec changes made (Worker 1 only)

None this pass. The spec L4 Status line is already current. Pre-recorded slice-level deferrals (catalogued below) remain explicit and out-of-scope.

## Deferred work catalog

This subsection walks every per-slice + integration artifact's `### Spec changes made (Worker 1 only)`, `### What looks solid`, and `### Notes for Worker 1 (spec reconciliation)` sections (per BUILD.md "Final test-run gate" requirement). One bullet per deferral.

### Slice-1 (Foundation) deferrals

- (none beyond what landed; Slice 1's spec-reconciliation notes that warranted documentation-clarity polish were either landed in spec edits during Slices 2-4 final-verification or absorbed by the implementation as designed — see `bld-slice-1-foundation.md::Spec changes made (Worker 1 only)`).

### Slice-2 (Factories) deferrals

- **Single-hop flat-grouping** — `bld-slice-2-factories.md::Spec changes made (Worker 1 only)`. Spec licenses (Edge cases and constraints, added by Slice 2 reconciliation): factory does NOT support multi-level transform chains. A nested `RelatedFilter`'s leaf-filter `__icontains` lookup currently materializes a single sub-input class; arbitrary chains (e.g. `branch__shelf__book__title__icontains`) belong to a future cookbook tree-form port. Defer: forward path is the cookbook tree-form algorithm port, owner TBD.
- **`{PascalCase(field_name)}RangeInputType` class-name collision** — `bld-slice-2-factories.md::Spec changes made (Worker 1 only)` + spec L997-L998. Range sub-input class names are derived from `filter_instance.field_name` only; two filtersets sharing a Range filter on the same field name would collide at Strawberry registration. Slice-2 ratified deferral: loud-not-silent (collision raises at registration); fix shape pinned (scope name by `(filterset_cls.__name__, field_name)`); apply the fix when a real consumer surfaces the collision.

### Slice-3 (Wiring) deferrals

- **`_target_type_for_related_filter` + `_resolve_relation_target_type` shared tail** (`registry.primary_for(model) or registry.get(model)`) — `bld-slice-3-wiring.md::Notes for Worker 1 (spec reconciliation)` + `bld-integration.md::Other items walked and explicitly NOT in scope`. Two call sites today; consolidation triggers when a third call site appears. Symbol clarity wins at two sites. Defer to whichever future card adds the third call site.
- **Spec L1030 test-name precision** — `bld-slice-3-wiring.md::Spec changes made (Worker 1 only)`. Spec line 1030 names `test_related_target_for_resolves_default_reverse_name`; Slice-3 substituted `test_related_target_for_resolves_one_to_one_relation` + `test_related_target_for_returns_none_when_target_unregistered` after determining the default-reverse-name branch is unreachable for test-function-local Django models. Spec L1028 last sentence already tightened to admit OneToOne forward+reverse + registry-miss substitution; L1030's test name itself reads `default_reverse_name` and was NOT tightened in lockstep. Defer to maintainer follow-up (one-word spec edit aligning L1030's test name with the shipped test names).

### Slice-4 (Live HTTP coverage) deferrals

- Slice 4's deferred items were absorbed by the Slice-4a carve (the tree-form-logic substrate) at Slice-4 final-verification per AGENTS.md L4 root-cause-fix rule. No standing Slice-4 deferrals carry forward beyond the items Slice 4a itself records below.

### Slice-4a (Tree-form logic substrate) deferrals

- **Nested form-validation skip in `_q_for_branch`** — `bld-slice-4a-tree_form_logic.md::Spec changes made (Worker 1 only)`. Tree-form substrate trade-off: nested `_q_for_branch` filtersets bypass `_validate_form_or_raise`, so per-leaf form-validation failures inside an `and` / `or` / `not` branch silently no-op instead of raising `FILTER_INVALID`. Consistent with spec L143's "operates only on data the top-level form already accepted" framing. Defer to maintainer follow-up — candidate scoping: a future spec slice (likely under the `0.0.9` `DjangoConnectionField` card) authorizing a uniform-across-depths `FILTER_INVALID` shape if the connection-field consumer surface requires it.
- **Tree-form-with-related-branch silent downgrade** — `bld-slice-4a-tree_form_logic.md::Spec changes made (Worker 1 only)`. A consumer-submitted `{"and": [{"shelves": {"code": {"exact": "X"}}}]}` shape has `shelves` stripped by `_normalize_input`'s related-keys strip path, so the child `_q_for_branch` `Q(pk__in=...)` no-ops. Slice 4a's contract is leaf-level `and` / `or` / `not` composition only; recursive `_apply_related_constraints` inside tree branches is contract expansion. Defer to maintainer follow-up — candidate scoping: a future sub-card "tree-form branches and `RelatedFilter` composition" explicitly authorizing the recursive `_apply_related_constraints` invocation inside `_q_for_branch`.

### Slice-5 (Docs + KANBAN + CHANGELOG) deferrals — joint-cut trio per Decision 10

- **`pyproject.toml [project].version` bump (`0.0.7 → 0.0.8`)** — `bld-slice-5-docs_kanban_changelog.md` + spec Decision 10 safe-default contingency. Worker 0 has NOT signaled "this is the last 0.0.8 card to ship"; safe-default no-bump path taken. Defer to whichever card actually owns the joint cut.
- **`django_strawberry_framework/__init__.py __version__` bump (`0.0.7 → 0.0.8`)** — `bld-slice-5-docs_kanban_changelog.md` + spec Decision 10. Same disposition as the `pyproject.toml` line; both must move in lockstep per AGENTS.md L31. Defer.
- **`tests/base/test_init.py` version-pin update (`0.0.7 → 0.0.8`)** — `bld-slice-5-docs_kanban_changelog.md` + spec Decision 10. Pin assertion stays at `0.0.7` until the bump trio lands. Defer.
- **`[Unreleased] → [0.0.8]` CHANGELOG promotion** — `bld-slice-5-docs_kanban_changelog.md` + spec Decision 10. `CHANGELOG.md`'s `[Unreleased]` `### Added` / `### Changed` bullets shipped this card; the `[0.0.8]` heading promotion lands at the joint-cut card. Defer.
- **`docs/README.md` shipped-version migration of `filter_input_type` + filter symbols** — `bld-slice-5-docs_kanban_changelog.md`. The Slice-5 narrative-rewrite path landed `GOAL.md`; the doc-README symbol-table move waits on the joint-cut card per Decision 10's safe-default contingency. Defer.
- **`README.md` shipped-symbol migration of `filter_input_type` + filter symbols** — `bld-slice-5-docs_kanban_changelog.md`. Same disposition as `docs/README.md`. Defer.

### Slice-5 housekeeping deferral

- **`docs/spec-027-filters-0_0_8-terms.csv` trailing-bytes artifact** — `bld-slice-5-docs_kanban_changelog.md`. Pre-existing trailing-bytes housekeeping noted at Slice 5 but not folded into the Slice-5 diff (out-of-scope for the doc-only slice). The file was modified by Slice 5 for the `filter_input_type` row addition; the trailing-bytes oddity predates this build. Defer to maintainer follow-up.

### Slice-6 (Composition smoke test) carry-forward

- **`tests/filters/test_composition.py` lands in `WIP-ALPHA-022-0.0.8`'s PR** — `bld-slice-6-composition_smoke_test.md` + spec L161 Slice-checklist conditional clause. This card shipped first; the cross-card composition smoke test is carried by the Ordering sibling card per the conditional. NOT a deferral to a future spec — it is a between-PR carry that the sibling card's spec already authorizes. Surfaced here so the next reader sees the full picture.

### Integration-pass deferrals (re-stated for completeness)

- **`_target_type_for_related_filter` + `_resolve_relation_target_type` shared tail** — re-listed under Slice-3 above. Integration pass walked the trigger condition (third call site) and confirmed not-met; deferral re-ratified, not re-introduced.
- **`inputs.py:423` Range sub-input class-name collision** — re-listed under Slice-2 above. Integration pass confirmed Slice-2's deferral disposition holds; not consolidation surface this pass.
- **Raw `"and" / "or" / "not"` literals in the Slice-4a tree walker at `sets.py::FilterSet._q_for_logic_tree`** — `bld-integration.md::Other items walked and explicitly NOT in scope`. Worker 1's integration plan walked the trade-off (branch-specific dispatch reads more cleanly than indirection through `dict(_LOGIC_KEYS).values()`); Worker 2's consolidation pass honored the stay-raw decision. Documented here as a "considered and intentionally kept raw" disposition, not a deferral that needs future work.

## Outcome and dispatch

`Status: final-accepted`. All five gate commands passed (full pytest sweep; Django system check; migration consistency check; ruff format read-only; ruff lint read-only; `git diff --check` — six gates total counting the lint sub-gates as separate). The deferred-work catalog enumerates 13 distinct deferrals + 1 carry-forward across six artifact sources, all explicitly licensed by either the spec body, the slice-plan `Spec changes made (Worker 1 only)` blocks, or the integration artifact's `Other items walked and explicitly NOT in scope` section. No silently-deferred work; no gate failures requiring slice re-loop.

Worker 0 may now mark the final test-run gate checkbox `- [x]` in `build-021-filters-0_0_8.md` and hand the build off to the maintainer for commit per BUILD.md "Slice handoff (no maintainer pause between slices)".
