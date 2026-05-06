# Current diff review feedback
Reviewed the current package diff against the `docs/review/rev-*.md` artifacts. The major correctness fixes are present, but the items below are still unresolved, partially covered, or intentionally deferred and should be tracked before closeout.

## Open items
### Stale settings reload wording remains after the mutation-based fix
- Review reference: `docs/review/rev-conf.md:9`
- Source references: `django_strawberry_framework/conf.py:13`, `django_strawberry_framework/conf.py:64`, `tests/base/test_conf.py:51`
- The implementation now mutates the existing `settings` singleton so direct imports stay fresh. The module docstring still says the instance is "rebuilt", and the existing test name/docstring still says reload "replaces" the module-level instance.

### Cache-key AST printing is still recomputed on every root resolver call
- Review references: `docs/review/rev-optimizer__extension.md:22`, `docs/review/rev-optimizer__extension.md:137`
- Source reference: `django_strawberry_framework/optimizer/extension.py:498`
- The hash-collision issue was fixed by storing `print_ast(operation)` in the cache key, but the Medium performance item to memoize the printed AST on cache hits was deferred.

### Aliased selections with divergent arguments still have no runtime signal
- Review references: `docs/review/rev-optimizer__walker.md:24`, `docs/review/rev-optimizer__walker.md:109`
- Source reference: `django_strawberry_framework/optimizer/walker.py:429`
- `_merge_aliased_selections` still keeps the first occurrence's `arguments` and only has a source comment warning future optimizer slices. The recommended debug/assertion signal for differing later arguments was reverted.

### Choice enum collision coverage is incomplete
- Review reference: `docs/review/rev-types__converters.md:18`
- Source references: `django_strawberry_framework/types/converters.py:198`, `tests/types/test_converters.py:233`
- The implementation now detects all sanitized enum-member collisions, but the review requested tests for both value-vs-value collisions and keyword-prefix collisions. The current test only covers `"a-b"` vs `"a_b"`; add a case such as `"if"` vs `"_if"`.

### Review plan references missing artifacts
- Review references: `docs/review/review-0_0_3.md:75`, `docs/review/review-0_0_3.md:103`, `docs/review/REVIEW.md:34`
- The active plan lists and checks off artifacts like `docs/review/rev-__init__.md`, `docs/review/rev-optimizer____init__.md`, `docs/review/rev-types____init__.md`, `docs/review/rev-utils____init__.md`, and `docs/review/rev-py.typed.md`, but those files are not present. This also conflicts with `REVIEW.md`, which says `__init__.py` and non-Python files are out of standalone scope.

## Deferred review items still not fixed
### Project-level Medium follow-ups remain open
- Review references: `docs/review/rev-django_strawberry_framework.md:16`, `docs/review/rev-django_strawberry_framework.md:33`
- The validation-hardening thread and shared context read/write helper are still forward-looking. The current code still keeps context writing in `django_strawberry_framework/optimizer/extension.py:52` and context reading in `django_strawberry_framework/types/resolvers.py:35`.

### `optimizer/extension.py` keeps `check_schema` as `@classmethod`
- Review references: `docs/review/rev-optimizer__extension.md:57`, `docs/review/rev-optimizer__extension.md:143`
- Source reference: `django_strawberry_framework/optimizer/extension.py:438`
- This was intentionally retained for subclass-override compatibility, but it remains an unimplemented Low recommendation.

### `optimizer/plans.py` Low items remain
- Review references: `docs/review/rev-optimizer__plans.md:40`, `docs/review/rev-optimizer__plans.md:63`
- Source references: `django_strawberry_framework/optimizer/plans.py:83`, `django_strawberry_framework/optimizer/plans.py:306`
- The defensive `queryset.query` access and tuple-driven `is_empty` refactor were deferred.

### `optimizer/walker.py` connector fallback remains debug-only
- Review reference: `docs/review/rev-optimizer__walker.md:102`
- Source reference: `django_strawberry_framework/optimizer/walker.py:377`
- `_ensure_connector_only_fields` still logs an unresolved connector column at `DEBUG` and continues. This was explicitly deferred, but it is still not fixed.

### `types/base.py` Low items remain
- Review references: `docs/review/rev-types__base.md:37`, `docs/review/rev-types__base.md:87`
- Source references: `django_strawberry_framework/types/base.py:183`, `django_strawberry_framework/types/base.py:255`
- The inherited-`Meta` unknown-key guard still only reads `meta.__dict__`, and the consumer-annotation override behavior remains a known non-contract.

### `types/converters.py` Low items remain
- Review references: `docs/review/rev-types__converters.md:30`, `docs/review/rev-types__converters.md:43`, `docs/review/rev-types__converters.md:55`
- Source references: `django_strawberry_framework/types/converters.py:47`, `django_strawberry_framework/types/converters.py:246`
- Choice-shape defensive polish, the registration-order error hint about `lazy_ref`, and `SCALAR_MAP` mutability were all deferred.

### `types/resolvers.py` Low items remain
- Review references: `docs/review/rev-types__resolvers.md:19`, `docs/review/rev-types__resolvers.md:35`, `docs/review/rev-types__resolvers.md:47`
- Source references: `django_strawberry_framework/types/resolvers.py:75`, `django_strawberry_framework/types/resolvers.py:94`, `django_strawberry_framework/types/resolvers.py:155`
- `_check_n1` still reads context repeatedly, the forward resolver still captures `field` instead of `attname`, and `_will_lazy_load` still relies on Django private cache shape assumptions.

### `registry.py` `lazy_ref` docstring remains design-note heavy
- Review reference: `docs/review/rev-registry.md:61`
- Source reference: `django_strawberry_framework/registry.py:79`
- The deferred `lazy_ref` surface still reads as design notes plus `NotImplementedError`; this was intentionally left for the future definition-order-independence slice.

### Utils review polish remains outside the current source diff
- Review references: `docs/review/rev-utils__strings.md:13`, `docs/review/rev-utils__strings.md:26`, `docs/review/rev-utils__typing.md:9`, `docs/review/rev-utils__typing.md:24`, `docs/review/rev-utils.md:13`
- The utility package low-severity documentation/edge-case notes were not addressed in this diff. This is fine if the closeout scope is only the changed package files, but not if every review artifact must be fully resolved.
