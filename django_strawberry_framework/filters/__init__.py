# ruff: noqa: ERA001
"""Planned filter subsystem entry point.

The module is intentionally not a public surface yet. ``spec-021`` ships
the concrete exports when the filter implementation applies end-to-end.
"""

# TODO(spec-021-filters-0_0_8 Slice 1): Export the filter subsystem only
# after the primitives, FilterSet metaclass, input factory, and finalizer
# binding pass all exist.
# Pseudocode:
#   from .base import Filter, RelatedFilter, GlobalIDFilter, ...
#   from .sets import FilterSet
#   from .inputs import filter_input_type
#   __all__ = ("FilterSet", "RelatedFilter", "filter_input_type", ...)
__all__: tuple[str, ...] = ()
