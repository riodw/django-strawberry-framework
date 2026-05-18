# Review feedback - spec-014-meta_primary-0_0_6.md revision 5

Scope: final pass on `docs/spec-014-meta_primary-0_0_6.md` after adding TODO anchors in the package files.

## Medium-Severity Findings

### M1. `_selected_scalar_names` is specified as a possible root scalar-only path, but the current call graph shows it is only a nested FK-id elision helper

References: `docs/spec-014-meta_primary-0_0_6.md:136`, `docs/spec-014-meta_primary-0_0_6.md:155`, `docs/spec-014-meta_primary-0_0_6.md:563`, `django_strawberry_framework/optimizer/walker.py:139`, `django_strawberry_framework/optimizer/walker.py:275`, `django_strawberry_framework/optimizer/walker.py:481`

The spec still frames `_selected_scalar_names` as the likely helper that must be threaded with `source_type` for scalar-only secondary root resolvers. In the current code, root scalar projection is handled directly in `_walk_selections` after `_resolve_field_map(model)` runs at `walker.py:139`; `_selected_scalar_names` is only called from `_plan_select_relation` at `walker.py:275`, where the model argument is `django_field.related_model` for nested FK-id elision. That nested path should keep `source_type=None` and use the primary, because it is not the resolver's root return type.

If Worker 2 follows the current wording literally, they may add unnecessary origin threading to `_selected_scalar_names`, or worse, treat nested FK-id elision as a root-origin lookup. Tighten the spec to state the post-audit decision explicitly: with today's call graph, `_selected_scalar_names` remains nested-only and should continue to resolve via the primary. The scalar-only secondary regression should pin `_walk_selections` / root `_resolve_field_map(..., source_type=origin)`, not `_selected_scalar_names`.

### M2. `_resolve_model_from_return_type` failure behavior is underspecified after changing the success return shape

References: `docs/spec-014-meta_primary-0_0_6.md:139`, `docs/spec-014-meta_primary-0_0_6.md:140`, `django_strawberry_framework/optimizer/extension.py:371`, `tests/optimizer/test_extension.py:499`, `tests/optimizer/test_extension.py:508`, `tests/optimizer/test_extension.py:517`

The spec says to rewrite the helper to return both origin and model, then says all four existing tests should assert against the new tuple or named-tuple shape and preserve the model assertion as the second element. Three of those tests are failure cases that currently assert `None` for non-object leaf, missing Strawberry schema, and missing schema type. The spec should not imply those failures become `(origin, None)` or a pair-like object.

Please specify the exact failure contract: return `None` whenever either leg is not usable, and return the pair only when both `origin` and `model` are resolved. Then update the stale-test instruction so the success test asserts the pair shape, while the failure tests continue to assert `None`. This avoids a truthy `(origin, None)` result being unpacked in `_optimize` and passed into the walker/cache path as a model.

## Low-Severity Findings

### L1. The plan-cache wording describes `origin=None` for nested planning, but the extension cache is root-only today

References: `docs/spec-014-meta_primary-0_0_6.md:141`, `docs/spec-014-meta_primary-0_0_6.md:588`, `django_strawberry_framework/optimizer/extension.py:556`, `django_strawberry_framework/optimizer/walker.py:336`

The spec says the new cache-key member is the resolver's origin type for root-path planning and `None` for nested planning. In the current implementation, `DjangoOptimizerExtension._plan_cache` is only used by `_get_or_build_plan` for root resolver optimization. Nested plans are constructed inside walker recursion / `_build_prefetch_child_queryset`, not inserted through `DjangoOptimizerExtension._build_cache_key`.

This is not a behavioral bug if implementers infer the right thing, but the wording invites over-engineering a nested extension-cache path or threading a `None` origin through surfaces that do not currently use the extension cache. Rephrase to: the extension cache key always receives the concrete root origin; direct/test-only calls that deliberately build a plan without an origin may use `None`. Nested walker recursion remains uncached by `DjangoOptimizerExtension` and keeps `source_type=None`.

### L2. The `model_for_type(origin)` "no change" bullet conflicts with the helper-return refactor unless the intended scope is made explicit

References: `docs/spec-014-meta_primary-0_0_6.md:139`, `docs/spec-014-meta_primary-0_0_6.md:144`, `docs/spec-014-meta_primary-0_0_6.md:590`, `django_strawberry_framework/optimizer/extension.py:396`

Slice 4 correctly says `_resolve_model_from_return_type` must stop discarding `origin` and return both origin and model. A few lines later, the spec says `optimizer/extension.py:396 registry.model_for_type(origin)` is "unchanged" / "no change", and Decision 9 says the extension's `origin -> model` path stays one line. That is probably meant to preserve `registry.model_for_type` itself, not the helper's old return shape.

Make that explicit so Worker 2 does not read the no-change bullet as permission to leave `_resolve_model_from_return_type` returning only the model. Suggested wording: "`registry.model_for_type(origin)` remains the model leg inside the expanded origin+model helper; the registry API and lookup semantics are unchanged, but the helper return shape is changed."

## Notes

Revision 5 resolves the earlier contradictions around already-shipped relation overrides, the KANBAN all-relations wording, finalizer line references, the version no-op language in the DoD, and `DjangoTypeDefinition.primary` authority. I do not see remaining registry or relation-finalization spec issues beyond the optimizer wording above.
