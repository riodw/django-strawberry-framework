"""Planned tests for ``OrderArgumentsFactory``."""

# TODO(spec-028-orders-0_0_8 Slice 2): Cover BFS input-class generation.
# Pseudocode:
#   - assert every reachable ``RelatedOrder`` target is visited once, even across
#     cycles.
#   - assert leaf fields accept ``Ordering | None`` and related fields use lazy
#     ``Annotated["TargetInputType", strawberry.lazy(...)] | None`` annotations.
#   - assert repeated factories share cached input classes.
#   - assert two distinct ``OrderSet`` classes with the same generated name raise
#     ``ConfigurationError``.
#   - assert no dynamic orderset / Layer-6 cache is present in ``0.0.8``.
