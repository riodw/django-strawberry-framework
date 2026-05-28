# Distilled Dicta: django_strawberry_framework
Use these prompts to explore one file at a time. They are priorities for investigation, not pass/fail rules; escalate only defects confirmed against the original source.

## Probing Questions for Code Exploration
The hunter should ask these questions while reading each file, focusing on exploration and hidden defects rather than simple checklist confirmation.

### 1. DRY & Duplication Risks
- **Is this pattern truly unique?** What functions, classes, validators, resolver helpers, metaclass branches, or test fixtures already exist in `django_strawberry_framework` that this logic could reuse or extend?
- **Are we creating premature helpers?** Does extracting a new helper make the code harder to follow, or does it serve a clear, single responsibility with multiple current or planned call-sites?
- **Are there hardcoded literals?** Do we repeat string keys, error fragments, database query keys, tuple shapes, or cache keys that should be named constants or centralized maps?
- **Is there a near-duplicate structure?** Are there branch structures, validation loops, queryset plans, or test setups that duplicate an existing code path with only minor differences?
- **Is ownership drifting?** Does this logic blur responsibilities between filters, types, registry, optimizer, schema loading, and example-project glue?

### 2. Django ORM, Optimizer, & Database Safety
- **Does this queryset logic risk returning incorrect or incomplete data?** Check nullable relations, many-valued relations, custom querysets, filtered prefetches, and result ordering.
- **Is there an N+1 query risk?** Are we missing required `select_related`, `prefetch_related`, `Prefetch`, or `only()` calls, or duplicating prefetch work already planned elsewhere?
- **Are we executing DB queries too early?** Is database access triggered at import time, class-definition time, metadata generation, or registry binding instead of resolver/query execution?
- **Does the optimizer plan align with Strawberry types?** Is there unclear ownership between optimizer plans, type metadata, registry lookup, and resolver behavior?
- **Does the branch run after binding is complete?** Can it observe a half-built Django model, Strawberry type, filterset, or framework metadata object?

### 3. Logic, Edge Cases, & Runtime Correctness
- **How does this branch handle `None` or empty collections?** Include empty tuples/lists/dicts, missing `Meta` attributes, inherited defaults, and locally overridden `None` values.
- **How are local overrides detected?** Are we using `vars(cls)` or another local-definition check when inherited attributes should not count?
- **Are we mutating global, thread, or request-scope state?** Could mutable defaults, caches, module registries, or context objects leak between consumers or concurrent async/sync resolver execution?
- **Are sync and async paths equivalent?** Do they preserve the same contract without double evaluation, swallowed exceptions, or stale context?
- **Are error messages descriptive enough?** Do exception strings cite the model, type, field, or setting the consumer needs to find the source of the error in logs?

### 4. Public API & Compatibility
- **Are we modifying the public API footprint?** Does the diff modify `django_strawberry_framework/__init__.py::__all__`, re-exports, consumer-facing Meta APIs, or shipped names without explicit spec authorization?
- **Are we introducing breaking changes?** Does this change break compatibility with the existing shipped `0.0.x` API surface or documented behavior?
- **Are documented public contracts still accurate?** Do `docs/GLOSSARY.md`, `docs/TREE.md`, README prose, comments, and docstrings describe the final behavior rather than an earlier slice label or planned TODO?
- **Are CHANGELOG dispositions honest?** If behavior is consumer-visible, should the result be `Warranted and edited` or `Warranted but deferred to maintainer` rather than silently `Not warranted`?

### 5. Comments, Docstrings, & Stale Code
- **Do comments describe the final, actual behavior?** Are there stale docstrings promising behavior the implementation no longer provides?
- **Are there obsolete TODOs?** Do TODOs reference deleted specs, missing KANBAN cards, or follow-up anchors that no active design doc owns?
- **Is it only comment polish?** Logic must be correct before comments are polished; do not let wording edits distract from a behavior bug.
- **Would a documentation fix be load-bearing?** Stale prose on a documented public-contract symbol should be treated as more than cosmetic.

### 6. Test Integrity & Branch Coverage
- **Are we missing tests for critical failure or rejection branches?** High-severity behavior fixes need permanent pinning tests unless the finding proves a test is impossible.
- **Do the tests actually pin success and rejection requirements?** Prefer real package or example-project usage over mock-only shortcuts.
- **Are tests placed in the right tree?** Avoid frozen or conflicting locations such as new files under `tests/base/` or package-colliding `examples/fakeshop/test_query/` layouts.
- **Can the finding be verified without coverage chasing?** Confirm from source or a focused probe; do not rely on coverage output or speculative reasoning.

## Severity Calibration Priorities
The hunter should prioritize findings by severity, escalating confirmed critical issues immediately and documenting maintainability issues with clear follow-up conditions.

### Priority 1: High (Correctness, Security, & API Stability)
- Confirmed correctness bugs or logic failures in the implementation.
- Violations of the core spec contract or API breakages against the shipped `0.0.x` surface.
- Django ORM errors that return incorrect or incomplete data.
- DRY violations that would entrench duplicated logic across the package.
- Runtime exceptions or crashes under normal async/sync usage.
- Security or data-isolation regressions.

*Action:* Fix the root cause directly and back it with a robust, permanent pinning test unless the finding itself proves a test is impossible.

### Priority 2: Medium (Performance, Redundancy, & Fragility)
- Likely performance regressions, N+1 query risks, or excessive database queries.
- Redundant logic or helper duplication that should be consolidated.
- Missing test coverage for important conditional or exceptional branches.
- Brittle edge-case behavior or unclear module ownership.
- Silently unaddressed spec checklist sub-items.
- Repeated string literals, keys, or tuple shapes that should be named constants.
- Stale public-contract docs or docstrings that could mislead consumers.

*Action:* Address during implementation when local to the prompted file, or record the exact sibling/spec dependency that blocks a one-file fix.

### Priority 3: Low (Style, Clarity, & Polish)
- Minor maintainability, naming clarity, or localized typing polish.
- Stale or minor comment/docstring inaccuracies that are not load-bearing.
- Localized code simplifications that do not alter behavior.

*Action:* Polish inline when safe and scoped, or frame with a clear, verbatim **trigger condition** (for example, *"Defer until a third walker lands"*) so future passes can find and consolidate it.

## How to review a single file
Each prompt below targets exactly one source file. Treat it as a focused
review pass, not a tour:

- Read the `.overview.md` shadow first. It is a structural index —
  quick-scan counts, imports, symbols, control-flow hotspots, executable
  Django/ORM marker lines, calls of interest, and repeated executable
  string literals — pulled from the AST without executing the file. Use
  it to plan the read, not as the source of truth.
- Read the `.stripped.py` shadow next. Comments and docstring statements
  are removed, and other string literals are replaced, so the executable
  structure is easier to scan. **Line numbers in the stripped file are
  not canonical.** Cite original source-file line numbers in every
  finding and every fix.
- Open the original source file alongside (named in the prompt) and
  reconcile the shadow view against the real code before declaring a
  defect.
- Confirm every defect against the actual source. No speculation, no
  "this might be wrong". If you cannot reproduce the failure shape
  mentally or with a quick read, drop the finding and move on. Silence
  on a marker line is acceptable; speculative defects pollute the
  checklist.

For each confirmed defect:

- Classify severity using the criteria in the dicta header above.
- Edit the original source file directly. Stay within the file the
  prompt names — if the fix needs sibling changes, surface that as a
  question rather than expanding the diff unilaterally.
- For **High**-severity fixes, add or update a test that pins the
  corrected behavior under the correct test tree per AGENTS.md
  "Test placement is mandatory". Do not rely on validation alone.
- For **Medium** / **Low** fixes that change a documented contract,
  update the relevant docstring or comment in the same pass so the
  prose matches the final behavior.
- Run `uv run ruff format <file>` and `uv run ruff check <file>` on
  any source file you touched.

When the file is done, tick its checkbox `- [x]` so the next prompt is
obvious.

## Per-file prompts

- [x] django_strawberry_framework/_django_patches.py
    - docs/shadow/django_strawberry_framework___django_patches.stripped.py
    - docs/shadow/django_strawberry_framework___django_patches.overview.md
    - Prompt:
        - Read docs/shadow/django_strawberry_framework___django_patches.stripped.py and docs/shadow/django_strawberry_framework___django_patches.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/_django_patches.py
    - Result: No issues. Files changed: none; validation: no ruff run because no edits. Hunter ran `uv run pytest tests/test_django_patches.py --no-cov` (12 passed) and `uv run pytest tests/test/test_wrap.py --no-cov` (6 passed) before scope correction.

- [x] django_strawberry_framework/apps.py
    - docs/shadow/django_strawberry_framework__apps.stripped.py
    - docs/shadow/django_strawberry_framework__apps.overview.md
    - Prompt:
        - Read docs/shadow/django_strawberry_framework__apps.stripped.py and docs/shadow/django_strawberry_framework__apps.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/apps.py
    - Result: No issues. Files changed: none; validation: no ruff run because no edits.

- [x] django_strawberry_framework/conf.py
    - docs/shadow/django_strawberry_framework__conf.stripped.py
    - docs/shadow/django_strawberry_framework__conf.overview.md
    - Prompt:
        - Read docs/shadow/django_strawberry_framework__conf.stripped.py and docs/shadow/django_strawberry_framework__conf.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/conf.py
    - Result: Fixed High recursion guard in `Settings.__getattr__`; changed `django_strawberry_framework/conf.py` and `tests/base/test_conf.py`; validation: `uv run pytest tests/base/test_conf.py --no-cov` passed (17 passed), ruff format/check on both touched files passed.

- [x] django_strawberry_framework/exceptions.py
    - docs/shadow/django_strawberry_framework__exceptions.stripped.py
    - docs/shadow/django_strawberry_framework__exceptions.overview.md
    - Prompt:
        - Read docs/shadow/django_strawberry_framework__exceptions.stripped.py and docs/shadow/django_strawberry_framework__exceptions.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/exceptions.py
    - Result: No issues. Files changed: none; validation: `uv run pytest --no-cov` passed (975 passed).

- [x] django_strawberry_framework/filters/base.py
    - docs/shadow/django_strawberry_framework__filters__base.stripped.py
    - docs/shadow/django_strawberry_framework__filters__base.overview.md
    - Prompt:
        - Read docs/shadow/django_strawberry_framework__filters__base.stripped.py and docs/shadow/django_strawberry_framework__filters__base.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/filters/base.py
    - Result: Fixed High `GlobalIDMultipleChoiceFilter.filter` crash on `None`; changed `django_strawberry_framework/filters/base.py` and `tests/filters/test_base.py`; validation: `uv run pytest tests/filters/test_base.py --no-cov` passed (31 passed), `uv run pytest --no-cov` passed (976 passed), ruff format/check on both touched files passed.

- [x] django_strawberry_framework/filters/factories.py
    - docs/shadow/django_strawberry_framework__filters__factories.stripped.py
    - docs/shadow/django_strawberry_framework__filters__factories.overview.md
    - Prompt:
        - Read docs/shadow/django_strawberry_framework__filters__factories.stripped.py and docs/shadow/django_strawberry_framework__filters__factories.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/filters/factories.py
    - Result: Fixed High dynamic FilterSet cache crash on unhashable Meta values; changed `django_strawberry_framework/filters/factories.py` and `tests/filters/test_factories.py`; validation: `uv run pytest tests/filters/test_factories.py` passed (17 passed), `uv run pytest --no-cov` passed (982 passed), ruff format/check on both touched files passed.

- [x] django_strawberry_framework/filters/inputs.py
    - docs/shadow/django_strawberry_framework__filters__inputs.stripped.py
    - docs/shadow/django_strawberry_framework__filters__inputs.overview.md
    - Prompt:
        - Read docs/shadow/django_strawberry_framework__filters__inputs.stripped.py and docs/shadow/django_strawberry_framework__filters__inputs.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/filters/inputs.py
    - Result: Fixed High traversed relation field grouping when the field name is also in `LOOKUP_NAME_MAP`; changed `django_strawberry_framework/filters/inputs.py` and `tests/filters/test_inputs.py`; validation: `uv run pytest --no-cov` passed (981 passed), ruff format/check on both touched files passed. Note: hunter committed/pushed this fix on branch `bugfix/inputs-lookup-token-grouping` despite the no-commit instruction; the fix (commit `a70f98b`) is now part of `build-021-filters-0_0_8`.

- [x] django_strawberry_framework/filters/sets.py
    - docs/shadow/django_strawberry_framework__filters__sets.stripped.py
    - docs/shadow/django_strawberry_framework__filters__sets.overview.md
    - Prompt:
        - Read docs/shadow/django_strawberry_framework__filters__sets.stripped.py and docs/shadow/django_strawberry_framework__filters__sets.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/filters/sets.py
    - Result: Fixed High logical-branch permission bypass and Medium request context loss in logical branches; changed `django_strawberry_framework/filters/sets.py` and `tests/filters/test_sets.py`; validation: `uv run pytest tests/filters/test_sets.py --no-cov` passed (44 passed), `uv run pytest --no-cov` passed (983 passed), ruff format/check on both touched files passed. Note: this Result records the round-1/2 fix only; review rounds 3–5 later added further `sets.py` hardening in the same areas — UNSET-in-operator-bag guards, cross-branch permission dedup via `_fired: dict[type, set[str]]`, the overridable `_MAX_LOGIC_DEPTH` recursion cap, and the proxy/MTI model-match carve-out — none of which are captured in the one-line summary above.

- [x] django_strawberry_framework/list_field.py
    - docs/shadow/django_strawberry_framework__list_field.stripped.py
    - docs/shadow/django_strawberry_framework__list_field.overview.md
    - Prompt:
        - Read docs/shadow/django_strawberry_framework__list_field.stripped.py and docs/shadow/django_strawberry_framework__list_field.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/list_field.py
    - Result: No issues. Files changed: none; validation: `uv run pytest tests/test_list_field.py --no-cov` passed (25 passed), `uv run pytest examples/fakeshop/test_query/test_library_api.py --no-cov` passed (26 passed), `uv run pytest --no-cov` passed (986 passed, 1 skipped).

- [x] django_strawberry_framework/management/commands/export_schema.py
    - docs/shadow/django_strawberry_framework__management__commands__export_schema.stripped.py
    - docs/shadow/django_strawberry_framework__management__commands__export_schema.overview.md
    - Prompt:
        - Read docs/shadow/django_strawberry_framework__management__commands__export_schema.stripped.py and docs/shadow/django_strawberry_framework__management__commands__export_schema.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/management/commands/export_schema.py
    - Result: No issues. Files changed: none; validation: `uv run ruff check django_strawberry_framework/management/commands/export_schema.py` passed, `uv run ruff format --check django_strawberry_framework/management/commands/export_schema.py` passed, `uv run pytest tests/management/test_export_schema.py --no-cov` passed (10 passed), `uv run pytest examples/fakeshop/tests/test_commands.py --no-cov` passed (18 passed), `uv run pytest --no-cov` passed (985 passed, 3 skipped).

- [x] django_strawberry_framework/optimizer/_context.py
    - docs/shadow/django_strawberry_framework__optimizer___context.stripped.py
    - docs/shadow/django_strawberry_framework__optimizer___context.overview.md
    - Prompt:
        - Read docs/shadow/django_strawberry_framework__optimizer___context.stripped.py and docs/shadow/django_strawberry_framework__optimizer___context.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/optimizer/_context.py
    - Result: No issues. Files changed: none; validation: `uv run pytest tests/optimizer/` passed (286 passed), `uv run ruff check django_strawberry_framework/optimizer/_context.py` passed, `uv run ruff format --check django_strawberry_framework/optimizer/_context.py` passed.

- [x] django_strawberry_framework/optimizer/extension.py
    - docs/shadow/django_strawberry_framework__optimizer__extension.stripped.py
    - docs/shadow/django_strawberry_framework__optimizer__extension.overview.md
    - Prompt:
        - Read docs/shadow/django_strawberry_framework__optimizer__extension.stripped.py and docs/shadow/django_strawberry_framework__optimizer__extension.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/optimizer/extension.py
    - Result: No issues. Files changed: none; validation: `uv run pytest --no-cov` passed (987 passed).

- [x] django_strawberry_framework/optimizer/field_meta.py
    - docs/shadow/django_strawberry_framework__optimizer__field_meta.stripped.py
    - docs/shadow/django_strawberry_framework__optimizer__field_meta.overview.md
    - Prompt:
        - Read docs/shadow/django_strawberry_framework__optimizer__field_meta.stripped.py and docs/shadow/django_strawberry_framework__optimizer__field_meta.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/optimizer/field_meta.py
    - Result: No issues. Files changed: none; validation: `uv run pytest tests/optimizer/ --no-cov` passed (286 passed), `uv run ruff check django_strawberry_framework/optimizer/field_meta.py` passed.

- [x] django_strawberry_framework/optimizer/hints.py
    - docs/shadow/django_strawberry_framework__optimizer__hints.stripped.py
    - docs/shadow/django_strawberry_framework__optimizer__hints.overview.md
    - Prompt:
        - Read docs/shadow/django_strawberry_framework__optimizer__hints.stripped.py and docs/shadow/django_strawberry_framework__optimizer__hints.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/optimizer/hints.py
    - Result: No issues. Files changed: none; validation: `uv run pytest tests/optimizer/test_hints.py --no-cov` passed (23 passed), `uv run pytest --no-cov` passed (985 passed, 3 skipped), `uv run ruff check django_strawberry_framework/optimizer/hints.py` passed, `uv run ruff format --check django_strawberry_framework/optimizer/hints.py` passed.

- [x] django_strawberry_framework/optimizer/plans.py
    - docs/shadow/django_strawberry_framework__optimizer__plans.stripped.py
    - docs/shadow/django_strawberry_framework__optimizer__plans.overview.md
    - Prompt:
        - Read docs/shadow/django_strawberry_framework__optimizer__plans.stripped.py and docs/shadow/django_strawberry_framework__optimizer__plans.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/optimizer/plans.py
    - Result: No issues. Files changed: none; validation: `uv run pytest --no-cov tests/optimizer/test_plans.py` passed (52 passed), `uv run pytest --no-cov tests/` passed (874 passed, 2 skipped), `uv run pytest --no-cov examples/fakeshop/` passed (111 passed, 1 skipped), `uv run ruff format --check django_strawberry_framework/optimizer/plans.py` passed, `uv run ruff check django_strawberry_framework/optimizer/plans.py` passed.

- [x] django_strawberry_framework/optimizer/walker.py
    - docs/shadow/django_strawberry_framework__optimizer__walker.stripped.py
    - docs/shadow/django_strawberry_framework__optimizer__walker.overview.md
    - Prompt:
        - Read docs/shadow/django_strawberry_framework__optimizer__walker.stripped.py and docs/shadow/django_strawberry_framework__optimizer__walker.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/optimizer/walker.py
    - Result: No issues. Files changed: none; validation: `uv run ruff format django_strawberry_framework/optimizer/walker.py` passed, `uv run ruff check django_strawberry_framework/optimizer/walker.py` passed, `uv run pytest tests/optimizer/test_walker.py --no-cov` passed (77 passed), `uv run pytest --no-cov` passed (985 passed, 3 skipped).

- [x] django_strawberry_framework/registry.py
    - docs/shadow/django_strawberry_framework__registry.stripped.py
    - docs/shadow/django_strawberry_framework__registry.overview.md
    - Prompt:
        - Read docs/shadow/django_strawberry_framework__registry.stripped.py and docs/shadow/django_strawberry_framework__registry.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/registry.py
    - Result: No issues. Files changed: none; validation: `uv run pytest tests/test_registry.py --no-cov` passed (60 passed), `uv run pytest --no-cov` passed (991 passed), `uv run ruff check django_strawberry_framework/registry.py` passed, `uv run ruff format --check django_strawberry_framework/registry.py` passed.

- [x] django_strawberry_framework/scalars.py
    - docs/shadow/django_strawberry_framework__scalars.stripped.py
    - docs/shadow/django_strawberry_framework__scalars.overview.md
    - Prompt:
        - Read docs/shadow/django_strawberry_framework__scalars.stripped.py and docs/shadow/django_strawberry_framework__scalars.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/scalars.py
    - Result: No issues. Files changed: none; validation: `uv run pytest tests/test_scalars.py --no-cov` passed (43 passed), `uv run ruff check django_strawberry_framework/scalars.py` passed, `uv run ruff format --check django_strawberry_framework/scalars.py` passed.

- [x] django_strawberry_framework/types/base.py
    - docs/shadow/django_strawberry_framework__types__base.stripped.py
    - docs/shadow/django_strawberry_framework__types__base.overview.md
    - Prompt:
        - Read docs/shadow/django_strawberry_framework__types__base.stripped.py and docs/shadow/django_strawberry_framework__types__base.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/types/base.py
    - Result: No issues. Files changed: none; validation: `uv run pytest tests/types/test_base.py tests/types/test_relay_interfaces.py tests/types/test_definition_order.py --no-cov` passed (160 passed), `uv run ruff check django_strawberry_framework/types/base.py` passed, `uv run ruff format --check django_strawberry_framework/types/base.py` passed.

- [x] django_strawberry_framework/types/converters.py
    - docs/shadow/django_strawberry_framework__types__converters.stripped.py
    - docs/shadow/django_strawberry_framework__types__converters.overview.md
    - Prompt:
        - Read docs/shadow/django_strawberry_framework__types__converters.stripped.py and docs/shadow/django_strawberry_framework__types__converters.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/types/converters.py
    - Result: No issues. Files changed: none; validation: `uv run pytest tests/types/ -v --no-cov` passed (247 passed), `uv run coverage report -m django_strawberry_framework/types/converters.py` passed.

- [x] django_strawberry_framework/types/definition.py
    - docs/shadow/django_strawberry_framework__types__definition.stripped.py
    - docs/shadow/django_strawberry_framework__types__definition.overview.md
    - Prompt:
        - Read docs/shadow/django_strawberry_framework__types__definition.stripped.py and docs/shadow/django_strawberry_framework__types__definition.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/types/definition.py
    - Result: No issues. Files changed: none; validation: `uv run pytest tests/types/test_definition_relations.py --no-cov` passed (3 passed), `uv run ruff check django_strawberry_framework/types/definition.py` passed, `uv run ruff format --check django_strawberry_framework/types/definition.py` passed.

- [x] django_strawberry_framework/types/finalizer.py
    - docs/shadow/django_strawberry_framework__types__finalizer.stripped.py
    - docs/shadow/django_strawberry_framework__types__finalizer.overview.md
    - Prompt:
        - Read docs/shadow/django_strawberry_framework__types__finalizer.stripped.py and docs/shadow/django_strawberry_framework__types__finalizer.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/types/finalizer.py
    - Result: No issues. Files changed: none; validation: `pytest --no-cov` passed (992 passed, 3 skipped), `ruff check django_strawberry_framework/types/finalizer.py` passed, `ruff format --check django_strawberry_framework/types/finalizer.py` passed.

- [x] django_strawberry_framework/types/relations.py
    - docs/shadow/django_strawberry_framework__types__relations.stripped.py
    - docs/shadow/django_strawberry_framework__types__relations.overview.md
    - Prompt:
        - Read docs/shadow/django_strawberry_framework__types__relations.stripped.py and docs/shadow/django_strawberry_framework__types__relations.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/types/relations.py
    - Result: No issues. Files changed: none; validation: `ruff check django_strawberry_framework/types/relations.py` passed, `ruff format --check django_strawberry_framework/types/relations.py` passed, `pytest tests/types/test_relations.py --no-cov` passed (3 passed).

- [x] django_strawberry_framework/types/relay.py
    - docs/shadow/django_strawberry_framework__types__relay.stripped.py
    - docs/shadow/django_strawberry_framework__types__relay.overview.md
    - Prompt:
        - Read docs/shadow/django_strawberry_framework__types__relay.stripped.py and docs/shadow/django_strawberry_framework__types__relay.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/types/relay.py
    - Result: No issues. Files changed: none; validation: `tests/types/test_relay_interfaces.py` tests passed, full pytest suite passed (996 passed), Ruff lint/format passed.

- [x] django_strawberry_framework/types/resolvers.py
    - docs/shadow/django_strawberry_framework__types__resolvers.stripped.py
    - docs/shadow/django_strawberry_framework__types__resolvers.overview.md
    - Prompt:
        - Read docs/shadow/django_strawberry_framework__types__resolvers.stripped.py and docs/shadow/django_strawberry_framework__types__resolvers.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/types/resolvers.py
    - Result: No issues. Files changed: none; validation: `pytest tests/types/test_resolvers.py --no-cov` passed (26 passed), `pytest --no-cov` passed (994 passed, 3 skipped), `ruff check django_strawberry_framework/types/resolvers.py` passed, `ruff format --check django_strawberry_framework/types/resolvers.py` passed.

- [x] django_strawberry_framework/utils/relations.py
    - docs/shadow/django_strawberry_framework__utils__relations.stripped.py
    - docs/shadow/django_strawberry_framework__utils__relations.overview.md
    - Prompt:
        - Read docs/shadow/django_strawberry_framework__utils__relations.stripped.py and docs/shadow/django_strawberry_framework__utils__relations.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/utils/relations.py
    - Result: No issues. Files changed: none; validation: Ruff checks passed and full pytest suite passed (997 passed).

- [x] django_strawberry_framework/utils/strings.py
    - docs/shadow/django_strawberry_framework__utils__strings.stripped.py
    - docs/shadow/django_strawberry_framework__utils__strings.overview.md
    - Prompt:
        - Read docs/shadow/django_strawberry_framework__utils__strings.stripped.py and docs/shadow/django_strawberry_framework__utils__strings.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/utils/strings.py
    - Result: No issues. Files changed: none; validation: `ruff check django_strawberry_framework/utils/strings.py` passed, `ruff format --check django_strawberry_framework/utils/strings.py` passed, `tests/utils/test_strings.py` passed.

- [x] django_strawberry_framework/utils/typing.py
    - docs/shadow/django_strawberry_framework__utils__typing.stripped.py
    - docs/shadow/django_strawberry_framework__utils__typing.overview.md
    - Prompt:
        - Read docs/shadow/django_strawberry_framework__utils__typing.stripped.py and docs/shadow/django_strawberry_framework__utils__typing.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/utils/typing.py
    - Result: No issues. Files changed: none; validation: `ruff check django_strawberry_framework/utils/typing.py` passed, `ruff format --check django_strawberry_framework/utils/typing.py` passed, `pytest --no-cov tests/utils/test_typing.py` passed (8 passed), `pytest --no-cov` passed (994 passed).
