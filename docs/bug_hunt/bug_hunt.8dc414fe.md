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

- Read the `.overview.md` shadow first. It is a structural index -
  quick-scan counts, imports, symbols, control-flow hotspots, executable
  Django/ORM marker lines, calls of interest, and repeated executable
  string literals - pulled from the AST without executing the file. Use
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
  prompt names - if the fix needs sibling changes, surface that as a
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
    - Result: No issues. Files changed: none; validation: none run (no source edit). Hunter reconciled the module against Django 6.0.5 upstream `_remove_databases_failures` and the existing pinning tests; the `_is_database_failure` guard, idempotent `apply()`, and missing-symbol fallback are all correct.
    - docs/shadow/current/django_strawberry_framework___django_patches.stripped.py
    - docs/shadow/current/django_strawberry_framework___django_patches.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework___django_patches.stripped.py and docs/shadow/current/django_strawberry_framework___django_patches.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/_django_patches.py

- [x] django_strawberry_framework/apps.py
    - Result: No issues. Files changed: none; validation: none run (no source edit). Minimal correct AppConfig: `name` matches INSTALLED_APPS, `ready()` lazily imports and calls the idempotent `apply()`; docstring claims accurate.
    - docs/shadow/current/django_strawberry_framework__apps.stripped.py
    - docs/shadow/current/django_strawberry_framework__apps.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__apps.stripped.py and docs/shadow/current/django_strawberry_framework__apps.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/apps.py

- [x] django_strawberry_framework/conf.py
    - Result: No issues. Files changed: none; validation: none run (no source edit). Traced every branch of `_normalize_user_settings`, the `Settings` singleton, `__getattr__` recursion guards, and the `setting_changed` receiver; consumers rely on the AttributeError-on-missing contract which is upheld and pinned by tests/base/test_conf.py.
    - docs/shadow/current/django_strawberry_framework__conf.stripped.py
    - docs/shadow/current/django_strawberry_framework__conf.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__conf.stripped.py and docs/shadow/current/django_strawberry_framework__conf.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/conf.py

- [x] django_strawberry_framework/connection.py
    - Result: No issues. Files changed: none; validation: `uv run ruff check connection.py` -> All checks passed (read-only baseline). Traced windowed fast-path page flags/cursor math, empty/ambiguous classification, sync/async pipeline symmetry, and the `UnwindowableConnection` branch (confirmed unreachable: walker leaves after+last unplanned so no windowed wrapper is built).
    - docs/shadow/current/django_strawberry_framework__connection.stripped.py
    - docs/shadow/current/django_strawberry_framework__connection.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__connection.stripped.py and docs/shadow/current/django_strawberry_framework__connection.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/connection.py

- [x] django_strawberry_framework/exceptions.py
    - Result: No issues. Files changed: none; validation: none run (no source edit). Pure declarative exception hierarchy; `__all__` correct; docstring contract claims cross-checked against real `ConfigurationError`/`OptimizerError` raise sites (field_meta.py, types/resolvers.py:188, plans.py:567/575).
    - docs/shadow/current/django_strawberry_framework__exceptions.stripped.py
    - docs/shadow/current/django_strawberry_framework__exceptions.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__exceptions.stripped.py and docs/shadow/current/django_strawberry_framework__exceptions.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/exceptions.py

- [x] django_strawberry_framework/filters/base.py
    - Result: No issues. Files changed: none; validation: none run (no source edit). Verified ArrayFilter/ListFilter empty-value ports (graphene-django faithful), `_target_definition_for` PK/relation resolution, GlobalID strategy routing, and `RelatedFilter` MRO + live `_has_explicit_queryset` read (filters/sets.py:1560); all pinned by tests/filters/test_base.py.
    - docs/shadow/current/django_strawberry_framework__filters__base.stripped.py
    - docs/shadow/current/django_strawberry_framework__filters__base.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__filters__base.stripped.py and docs/shadow/current/django_strawberry_framework__filters__base.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/filters/base.py

- [x] django_strawberry_framework/filters/factories.py
    - Result: No issues. Files changed: none; validation: none run (no source edit). Examined the cache-key hashing invariant; `_make_hashable` correctly uses key=repr on unordered branches, and the `_make_cache_key` bare-`sorted` asymmetry is unreachable (sorts tuples keyed by unique strings). Realistic cases pinned by tests/filters/test_factories.py.
    - docs/shadow/current/django_strawberry_framework__filters__factories.stripped.py
    - docs/shadow/current/django_strawberry_framework__filters__factories.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__filters__factories.stripped.py and docs/shadow/current/django_strawberry_framework__filters__factories.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/filters/factories.py

- [x] django_strawberry_framework/filters/inputs.py
    - Result: No issues. Files changed: none; validation: none run (no source edit). Verified converter branch ordering against django-filter MRO (BaseCSV before Range; GlobalIDMultipleChoice not misrouted by ChoiceFilter), range/enum/GlobalID normalization symmetry, and module-global `_field_specs` cleanup contract. /tmp probe (outside repo) smoke-tested all shipped primitives; removed.
    - docs/shadow/current/django_strawberry_framework__filters__inputs.stripped.py
    - docs/shadow/current/django_strawberry_framework__filters__inputs.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__filters__inputs.stripped.py and docs/shadow/current/django_strawberry_framework__filters__inputs.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/filters/inputs.py

- [x] django_strawberry_framework/filters/sets.py
    - Result: No issues. Files changed: none; validation: none run (no source edit). Adversarial checks on sync/async permission-walk symmetry, the id()-keyed nested-visibility map, logic-depth caps, the duplicate-safe `pk__in` related-constraint subquery, and the `get_filters` forward-ref cache guard all hold; the apparent shadow line-1302 anomaly is a string-strip artifact.
    - docs/shadow/current/django_strawberry_framework__filters__sets.stripped.py
    - docs/shadow/current/django_strawberry_framework__filters__sets.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__filters__sets.stripped.py and docs/shadow/current/django_strawberry_framework__filters__sets.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/filters/sets.py

- [x] django_strawberry_framework/list_field.py
    - Result: No issues. Files changed: none; validation: none run (no source edit). Verified load-bearing validation guard ordering, own-class `definition.origin is target_type` invariant, per-call (`in_async_context`) vs per-construction async dispatch, intentional `-> Any` annotation, and immutable `directives=()` default.
    - docs/shadow/current/django_strawberry_framework__list_field.stripped.py
    - docs/shadow/current/django_strawberry_framework__list_field.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__list_field.stripped.py and docs/shadow/current/django_strawberry_framework__list_field.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/list_field.py

- [x] django_strawberry_framework/management/commands/export_schema.py
    - Result: No issues (one Low deferred). Files changed: none; validation: none run (no source edit). All three `--path` branches (stdout / empty-string CommandError / file-write OSError-wrap) correct and tested; argparse no-value rejection matches the [0.0.7] contract. Deferred Low: `handle()` docstring (lines 28-32) misattributes the empty-string rejection to the [0.0.7] CHANGELOG no-value entry — trigger: fold in if the empty-string behavior gets its own CHANGELOG entry or the docstring is touched for another reason.
    - docs/shadow/current/django_strawberry_framework__management__commands__export_schema.stripped.py
    - docs/shadow/current/django_strawberry_framework__management__commands__export_schema.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__management__commands__export_schema.stripped.py and docs/shadow/current/django_strawberry_framework__management__commands__export_schema.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/management/commands/export_schema.py

- [x] django_strawberry_framework/management/commands/inspect_django_type.py
    - Result: No issues. Files changed: none; validation: none run (no source edit). Reconciled against registry/converters/field_meta/finalizer + both test tiers; relation-kind label coverage (no raw-token fallback), JSON NewType scalar key, `rstrip("!")` list handling, connection-only dispatch, relay-pk suppression, and import error catches all sound. /tmp `python -c` probes were read-only.
    - docs/shadow/current/django_strawberry_framework__management__commands__inspect_django_type.stripped.py
    - docs/shadow/current/django_strawberry_framework__management__commands__inspect_django_type.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__management__commands__inspect_django_type.stripped.py and docs/shadow/current/django_strawberry_framework__management__commands__inspect_django_type.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/management/commands/inspect_django_type.py

- [x] django_strawberry_framework/optimizer/_context.py
    - Result: No issues. Files changed: none; validation: none run (no source edit). Runtime-verified read/write symmetry across dict/object/slots/MappingProxy/frozen-dataclass contexts, `_MISSING` vs stashed `None`, and exception discipline (swallow TypeError/AttributeError on write, surface KeyError/RuntimeError). /tmp probe removed.
    - docs/shadow/current/django_strawberry_framework__optimizer___context.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer___context.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__optimizer___context.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer___context.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/optimizer/_context.py

- [x] django_strawberry_framework/optimizer/extension.py
    - Result: Fixed High. Files changed: django_strawberry_framework/optimizer/extension.py, tests/optimizer/test_extension.py. Defect: `_walk_cache_relevant_vars` used a name-only `set[str]` fragment cycle guard, but nested-pagination-var collection is depth-sensitive — a fragment spread at root depth (pagination excluded) would mark it visited and suppress a later nested spread of the same fragment, dropping its `first/last/before/after` var from the plan-cache key so two requests differing only in that var shared one cached plan and served the wrong windowed prefetch (Decision 7 under-collection). Fix: key the guard on `(fragment_name, spread-site depth)` via a local `_unvisited_fragment_at_depth` (stayed in-file; did not touch selections.py). Pinned by new `test_fragment_spread_at_two_depths_collects_nested_pagination_variable` (both spread orders) + updated sibling-spread test to `{("F", 1)}`. Follow-up: the initial fix left one uncovered statement (the standalone `frag_name is None` defensive return at extension.py:231, unreachable for a valid AST), dropping coverage to 99.98%; collapsed it into a combined `frag_name is None or key in visited_fragments` guard mirroring `selections.resolve_unvisited_fragment` (behavior unchanged). Validation: ruff format + ruff check pass; full `uv run pytest` -> 1908 passed, 3 skipped, coverage back to 100.00% (0 missed).
    - docs/shadow/current/django_strawberry_framework__optimizer__extension.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__extension.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__optimizer__extension.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer__extension.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/optimizer/extension.py

- [x] django_strawberry_framework/optimizer/field_meta.py
    - Result: No issues. Files changed: none; validation: none run (no source edit). Verified cardinality-gated `nullable` rule (blocks ForeignObjectRel null=True leak), fail-closed composite-PK `fk_id_elision_eligible` gate (`_has_composite_pk` access guarded by prior short-circuits), and `_target_pk_name` defensive None/_meta handling mirroring walker.py. Frozen+slots immutable; no early DB access.
    - docs/shadow/current/django_strawberry_framework__optimizer__field_meta.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__field_meta.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__optimizer__field_meta.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer__field_meta.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/optimizer/field_meta.py

- [x] django_strawberry_framework/optimizer/hints.py
    - Result: No issues. Files changed: none; validation: none run (no source edit). Verified all four hint shapes (SKIP/select/prefetch/prefetch(obj)) construct cleanly, all conflict combos raise ConfigurationError, validation ordering (type-check before combo-check), `hint_is_skip` None/identity/getattr safety, and the frozen-dataclass ClassVar SKIP rebind. Sibling consumers (walker/extension/types.base) read the contract consistently.
    - docs/shadow/current/django_strawberry_framework__optimizer__hints.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__hints.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__optimizer__hints.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer__hints.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/optimizer/hints.py

- [x] django_strawberry_framework/optimizer/plans.py
    - Result: No issues. Files changed: none; validation: none run (no source edit). Verified `apply_window_pagination` reverse/forward bounds, non-mutating `_reverse_order_by` (entry.copy + NULLS swap), `ends_in_unique_column`, the `_diff_prefetch_related`/`_optimizer_can_absorb` consumer-wins logic (descendant-prefix guard), and the deliberate `_MAX_PATH_DEPTH` fail-loud bound. All pinned by tests/optimizer/test_plans.py + test_connection.py.
    - docs/shadow/current/django_strawberry_framework__optimizer__plans.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__plans.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__optimizer__plans.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer__plans.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/optimizer/plans.py

- [x] django_strawberry_framework/optimizer/selections.py
    - Result: No issues. Files changed: none; validation: none run (no source edit). Verified `ast_to_converted_selections` faithfully mirrors Strawberry convert_selections (anonymous-inline type_condition=None the only intended deviation), `prime_selected_fields` cached-property priming, `should_include` skip/include AND-logic, and that the name-only `resolve_unvisited_fragment` is correctly scoped to the reachable-fragment walk (depth-sensitivity owned by extension.py's fix). Read-only venv introspection confirmed Strawberry/graphql-core internals.
    - docs/shadow/current/django_strawberry_framework__optimizer__selections.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__selections.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__optimizer__selections.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer__selections.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/optimizer/selections.py

- [x] django_strawberry_framework/optimizer/walker.py
    - Result: No issues. Files changed: none; validation: none run (no source edit). Traced window-slice exception routing (UnwindowableConnection propagates to its dedicated except), window-None vs unwindowable resolver-key recording (Decision 5/6), the `fk_id_elision_eligible` early-return guarding `field.attname` (unreachable raw-field path acknowledged by DUAL CONTRACT comment), connection-recognition keying vs finalizer synth, and `_prefetch_hint_for_path` accessor rebasing. All test-pinned.
    - docs/shadow/current/django_strawberry_framework__optimizer__walker.stripped.py
    - docs/shadow/current/django_strawberry_framework__optimizer__walker.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__optimizer__walker.stripped.py and docs/shadow/current/django_strawberry_framework__optimizer__walker.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/optimizer/walker.py

- [x] django_strawberry_framework/orders/base.py
    - Result: No issues. Files changed: none; validation: none run (no source edit). Thin family-named wrapper over RelatedSetTargetMixin; slot parameterization (`_orderset`/`bound_orderset`) internally consistent and matching all consumers; `field_name=None` and `RelatedOrder(None,...)` placeholder paths handled. Low non-defect: `orderset` property `-> type` annotation omits None but intentionally mirrors the filter twin (filters/base.py:458) — left to avoid single-file divergence.
    - docs/shadow/current/django_strawberry_framework__orders__base.stripped.py
    - docs/shadow/current/django_strawberry_framework__orders__base.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__orders__base.stripped.py and docs/shadow/current/django_strawberry_framework__orders__base.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/orders/base.py

- [x] django_strawberry_framework/orders/factories.py
    - Result: No issues. Files changed: none; validation: none run (no source edit). Thin correct subclass of GeneratedInputArgumentsFactory; six hook attrs match base contract + runtime objects (related_orders, RelatedOrder.orderset), fresh-dict ClassVar caches per "MUST redefine", `_build_input_triples` override mirrors filter side with intended Spec Decision 8 divergence (no operator bag).
    - docs/shadow/current/django_strawberry_framework__orders__factories.stripped.py
    - docs/shadow/current/django_strawberry_framework__orders__factories.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__orders__factories.stripped.py and docs/shadow/current/django_strawberry_framework__orders__factories.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/orders/factories.py

- [x] django_strawberry_framework/orders/inputs.py
    - Result: No issues. Files changed: none; validation: `uv run ruff check orders/inputs.py` -> All checks passed (baseline). Verified enum `resolve` direction/nulls logic (DESC names never contain "ASC"), concrete-field filter excludes M2M/reverse, and the `_build_input_fields`/`normalize_input_value` provenance round-trip (`shelf` -> `shelf__code`) reconciles with sets/base/utils and tests/orders/test_inputs.py.
    - docs/shadow/current/django_strawberry_framework__orders__inputs.stripped.py
    - docs/shadow/current/django_strawberry_framework__orders__inputs.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__orders__inputs.stripped.py and docs/shadow/current/django_strawberry_framework__orders__inputs.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/orders/inputs.py

- [x] django_strawberry_framework/orders/sets.py
    - Result: No issues. Files changed: none; validation: none run (no source edit). Verified `_path_traverses_to_many` classification, the Min/Max aggregate choice for to-many ordering (`"ASC" in direction.name` discriminates ASC from DESC), alias `index` collision-guard, the `get_fields` cache-write gate, and sync/async permission-pipeline parity (async only wraps checks in sync_to_async). Apparent shadow line 515-516 garble is a strip artifact.
    - docs/shadow/current/django_strawberry_framework__orders__sets.stripped.py
    - docs/shadow/current/django_strawberry_framework__orders__sets.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__orders__sets.stripped.py and docs/shadow/current/django_strawberry_framework__orders__sets.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/orders/sets.py

- [x] django_strawberry_framework/registry.py
    - Result: No issues. Files changed: none; validation: none run (no source edit). Verified register/register_with_definition rollback mirrors all four side effects per branch, unregister lock-step invariant + connection-cache eviction keyed on type_cls (matches connection.py:739), definition_for_graphql_name match/ambiguity/relay branches, and clear() co-clear targets all exist. Pinned by tests/test_registry.py.
    - docs/shadow/current/django_strawberry_framework__registry.stripped.py
    - docs/shadow/current/django_strawberry_framework__registry.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__registry.stripped.py and docs/shadow/current/django_strawberry_framework__registry.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/registry.py

- [x] django_strawberry_framework/relay.py
    - Result: No issues. Files changed: none; validation: none run (no source edit). Verified `_coerce_pk_or_none` keys on resolve_id_attr (non-pk NodeID safe), typed-match runs before coercion in both factories (wrong-type-anywhere fails whole field), batch interleave index recorded before append (in-bounds), sync/async dispatch via isawaitable, and SyncMisuseError boundary. Pinned by tests/test_relay_node_field.py.
    - docs/shadow/current/django_strawberry_framework__relay.stripped.py
    - docs/shadow/current/django_strawberry_framework__relay.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__relay.stripped.py and docs/shadow/current/django_strawberry_framework__relay.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/relay.py

- [x] django_strawberry_framework/scalars.py
    - Result: No issues. Files changed: none; validation: none run (no source edit); /tmp probe "ALL PROBES PASSED" (removed). Verified BigInt regex under fullmatch (no trailing-newline bypass; Unicode/leading-zero/sign rejected), bool-before-int ordering, serialize/parse symmetry, and `strawberry_config` copy-then-update (no global-map mutation) + collision detection + scalar_map guard + kwargs forwarding.
    - docs/shadow/current/django_strawberry_framework__scalars.stripped.py
    - docs/shadow/current/django_strawberry_framework__scalars.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__scalars.stripped.py and docs/shadow/current/django_strawberry_framework__scalars.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/scalars.py

- [x] django_strawberry_framework/sets_mixins.py
    - Result: No issues. Files changed: none; validation: none run (no source edit). Verified `type_name_for` empty-collapse guard, `resolve_lazy_class` str/callable/class branching + scoped ImportError fallback, idempotent `_bind_owner` (no class-level default), and `expanded_once` own-`__dict__` cache read (no MRO leak) + reentry guard + finally-clear. Consumers reconcile.
    - docs/shadow/current/django_strawberry_framework__sets_mixins.stripped.py
    - docs/shadow/current/django_strawberry_framework__sets_mixins.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__sets_mixins.stripped.py and docs/shadow/current/django_strawberry_framework__sets_mixins.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/sets_mixins.py

- [x] django_strawberry_framework/types/base.py
    - Result: No issues. Files changed: none; validation: read-only `uv run python` import/regex/relay-attr probes passed (no source edit). Verified local-override detection (cls.__dict__/base.__dict__ at 476/587/694/763), None/empty short-circuits in all `_validate_*`, unhashable-shape guard ordering (264), relay-id collision regex (_NODEID_STRING_RE accepts relay.NodeID[int], rejects NotNodeID[int]), async-encoder rejection, and no import-time DB access. Two low-confidence items dropped per no-speculation rule.
    - docs/shadow/current/django_strawberry_framework__types__base.stripped.py
    - docs/shadow/current/django_strawberry_framework__types__base.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__types__base.stripped.py and docs/shadow/current/django_strawberry_framework__types__base.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/types/base.py

- [x] django_strawberry_framework/types/converters.py
    - Result: No issues. Files changed: none; validation: none run (no source edit); /tmp sanitizer/collision probe removed. Verified the four-step `_sanitize_member_name` ordering (probe across keywords/digits/unicode/reserved), N-way choice-collision accumulation (enum built only after raise), `convert_scalar` effective_null widening + ArrayField sentinel dispatch, and grouped-choices detection. Pinned by tests/types/test_converters.py.
    - docs/shadow/current/django_strawberry_framework__types__converters.stripped.py
    - docs/shadow/current/django_strawberry_framework__types__converters.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__types__converters.stripped.py and docs/shadow/current/django_strawberry_framework__types__converters.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/types/converters.py

- [x] django_strawberry_framework/types/definition.py
    - Result: No issues. Files changed: none; validation: none run (no source edit); /tmp probes removed. Strong candidate investigated: `origin_has_custom_id_resolver` (line 300) keys resolver detection on `(pk_name, resolve_<pk_name>)`, so a `resolve_id` override on a non-`id`-PK type isn't flagged — but this is deliberate pinned behavior per test_has_custom_id_resolver_for_caches_mro_result; dropped. Cache gating on registry.is_finalized() and framework-default exemptions reconcile.
    - docs/shadow/current/django_strawberry_framework__types__definition.stripped.py
    - docs/shadow/current/django_strawberry_framework__types__definition.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__types__definition.stripped.py and docs/shadow/current/django_strawberry_framework__types__definition.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/types/definition.py

- [x] django_strawberry_framework/types/finalizer.py
    - Result: No issues. Files changed: none; validation: read-only ast.parse clean (no source edit). Walked phase-1 `definition` dereference (non-None after register_with_definition), `field_map[snake_case(name)]` key presence, the raw `shapes.get` vs default-`shapes.get` re-entrancy/collision split (existing computed before attach), primary-label routing dereference (guarded by prior ambiguity audit), and filter/order sidecar None-safety (related_orders always OrderedDict). All contractually safe.
    - docs/shadow/current/django_strawberry_framework__types__finalizer.stripped.py
    - docs/shadow/current/django_strawberry_framework__types__finalizer.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__types__finalizer.stripped.py and docs/shadow/current/django_strawberry_framework__types__finalizer.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/types/finalizer.py

- [x] django_strawberry_framework/types/relations.py
    - Result: No issues. Files changed: none; validation: none run (no source edit); /tmp probes removed. Verified `PendingRelation` frozen-dataclass intentional identity `__hash__` (survives dataclass processing; instances only listed/`id()`-removed, never set-hashed), the sentinel meta `__repr__`, and all load-bearing docstring claims against producer (types/base.py:1591) and consumer (finalizer.py:607, registry.py).
    - docs/shadow/current/django_strawberry_framework__types__relations.stripped.py
    - docs/shadow/current/django_strawberry_framework__types__relations.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__types__relations.stripped.py and docs/shadow/current/django_strawberry_framework__types__relations.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/types/relations.py

- [x] django_strawberry_framework/types/relay.py
    - Result: No issues. Files changed: none; validation: none run (no source edit). Verified strategy-membership centralization, `decode_global_id` registry-return guarding (get_definition guarded; definition_for_graphql_name raises so .origin safe), MRO-aware override detection via _FRAMEWORK_CLOSURE_MARKER, installed resolver-default signatures vs strawberry.relay.Node (node_ids=None divergence intentional), and async/sync (SyncMisuseError) parity. Pinned by relay test suites.
    - docs/shadow/current/django_strawberry_framework__types__relay.stripped.py
    - docs/shadow/current/django_strawberry_framework__types__relay.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__types__relay.stripped.py and docs/shadow/current/django_strawberry_framework__types__relay.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/types/relay.py

- [x] django_strawberry_framework/types/resolvers.py
    - Result: No issues. Files changed: none; validation: none run (no source edit). Verified `_check_n1` strictness sentinels + accessor-keyed cache probe (connection.py:1148-1156 call site), the forward_resolver `getattr(root, field_name)` vs sibling `accessor_name` asymmetry (correct: forward FK/O2O field.name IS the attribute), FK-id elision stubs, and immutable defaults (_EMPTY_ELISIONS frozenset). Pinned by tests/types/test_resolvers.py.
    - docs/shadow/current/django_strawberry_framework__types__resolvers.stripped.py
    - docs/shadow/current/django_strawberry_framework__types__resolvers.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__types__resolvers.stripped.py and docs/shadow/current/django_strawberry_framework__types__resolvers.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/types/resolvers.py

- [x] django_strawberry_framework/utils/connections.py
    - Result: No issues. Files changed: none; validation: none run (no source edit). Traced `derive_connection_window_bounds` reverse/limit rules vs SliceMetadata.from_arguments (reverse branch expected=None so limit=last required); cross-module plan-time/resolve-time parity preserved (walker + connection.py call the same fn); `before=""` edge dropped as non-reproducible; the `limit: int|None` never-None nuance is at most Low and defensible.
    - docs/shadow/current/django_strawberry_framework__utils__connections.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__connections.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__utils__connections.stripped.py and docs/shadow/current/django_strawberry_framework__utils__connections.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/utils/connections.py

- [x] django_strawberry_framework/utils/input_values.py
    - Result: No issues. Files changed: none; validation: none run (no source edit). Verified `iter_input_items` dict/dataclass sniffing (None/[] returns), identity-based `is_inactive_value` (None/UNSET), and `iter_active_fields` LOGIC/RELATED/LEAF classification + list flattening + getattr-defended related lookup; logic-vs-related ordering provably immaterial. Pure traversal, no DB/async. Pinned by tests/utils/test_input_values.py.
    - docs/shadow/current/django_strawberry_framework__utils__input_values.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__input_values.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__utils__input_values.stripped.py and docs/shadow/current/django_strawberry_framework__utils__input_values.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/utils/input_values.py

- [x] django_strawberry_framework/utils/inputs.py
    - Result: No issues (one Low noted, not fixed). Files changed: none; validation: none run (no source edit); /tmp probe of graphql_camel_name. Verified idempotent materialization + family-labelled collision, iter_set_subclasses diamond dedup, `_ensure_built` BFS cycle/collision handling (per-family caches reset by clear), and clear_generated_input_namespace binding_attrs contract. Low non-defect: `__init_subclass__` (lines 330-331) reports `__bases__[0]` as rejected parent — could misname base under reordered MI; rejection still fires, wording-only, not warranting a one-file edit.
    - docs/shadow/current/django_strawberry_framework__utils__inputs.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__inputs.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__utils__inputs.stripped.py and docs/shadow/current/django_strawberry_framework__utils__inputs.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/utils/inputs.py

- [x] django_strawberry_framework/utils/permissions.py
    - Result: No issues. Files changed: none; validation: none run (no source edit). Verified request_from_info resolution, dict-vs-dataclass extract_branch_value, post-fire dedup, RELATED/LEAF filtering, and intentional parent-vs-child double dispatch (distinct per-class dedup scopes; getattr target_attr resolves RelatedSetTargetMixin property, None/hasattr-guarded). `iter_input_items` re-export load-bearing (filters/sets.py:51). Consistent across filter+order families.
    - docs/shadow/current/django_strawberry_framework__utils__permissions.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__permissions.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__utils__permissions.stripped.py and docs/shadow/current/django_strawberry_framework__utils__permissions.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/utils/permissions.py

- [x] django_strawberry_framework/utils/querysets.py
    - Result: No issues. Files changed: none; validation: read-only ast.parse OK (no source edit). Verified normalize_query_source Manager->QuerySet coercion ordering, sync `iscoroutine`+close() vs async `isawaitable`+await symmetry, SyncMisuseError single-string construction, and post_process sync/async symmetry; checked all six callers. The iscoroutine-vs-isawaitable asymmetry is a defensible documented design choice (drops per no-speculation).
    - docs/shadow/current/django_strawberry_framework__utils__querysets.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__querysets.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__utils__querysets.stripped.py and docs/shadow/current/django_strawberry_framework__utils__querysets.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/utils/querysets.py

- [x] django_strawberry_framework/utils/relations.py
    - Result: No issues. Files changed: none; validation: none run (no source edit). Verified `relation_kind` branch ordering vs Django per-class *Rel flags (OneToOneRel correctly reaches reverse_one_to_one; one_to_many-without-auto_created->many is test-pinned), MANY_SIDE_RELATION_KINDS/RelationKind consistency, and `instance_accessor` three-tier read matches all field shapes callers pass. Symmetrical-M2M get_accessor_name->None edge dropped as unreachable here.
    - docs/shadow/current/django_strawberry_framework__utils__relations.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__relations.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__utils__relations.stripped.py and docs/shadow/current/django_strawberry_framework__utils__relations.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/utils/relations.py

- [x] django_strawberry_framework/utils/strings.py
    - Result: No issues. Files changed: none; validation: none run (no source edit); /tmp probes "all passed", removed. Verified snake_case/pascal_case reproduce every docstring example (acronym caveats, underscore-collapse, digit handling, degenerate inputs) and snake_case idempotence (relied on by field_map build vs lookup). Cross-file DRY note (not acted on, sibling out of scope): filters/inputs.py:161 has a divergent `_pascal_case` that raises on word-char-free input — candidate for a future DRY pass.
    - docs/shadow/current/django_strawberry_framework__utils__strings.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__strings.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__utils__strings.stripped.py and docs/shadow/current/django_strawberry_framework__utils__strings.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/utils/strings.py

- [x] django_strawberry_framework/utils/typing.py
    - Result: No issues. Files changed: none; validation: none run (no source edit); /tmp probes removed. Verified `is_async_callable` partial-unwrap + __call__ async check (across partials/instances/builtins/non-callables), bounded `unwrap_graphql_type` peel loop (_MAX_TYPE_WRAPPER_DEPTH=64 + descriptive RuntimeError), and `unwrap_return_type` one-layer unwrap (list[T]/bare list->Any/of_type/None). of_type=None fall-through dropped as non-reproducible.
    - docs/shadow/current/django_strawberry_framework__utils__typing.stripped.py
    - docs/shadow/current/django_strawberry_framework__utils__typing.overview.md
    - Prompt:
        - Read docs/shadow/current/django_strawberry_framework__utils__typing.stripped.py and docs/shadow/current/django_strawberry_framework__utils__typing.overview.md and check for bugs, if any are found make edits to django_strawberry_framework/utils/typing.py
