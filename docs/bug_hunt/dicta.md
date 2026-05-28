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
