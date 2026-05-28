# ruff: noqa: ERA001
"""Filter primitives planned by ``spec-021-filters-0_0_8``."""

# TODO(spec-021-filters-0_0_8 Slice 1): Port the filter primitives from
# graphene-django and django-graphene-filters onto django-filter's
# ``filterset.BaseFilterSet`` foundation.
# Pseudocode:
#   class Filter(django_filters.Filter): ...
#   class TypedFilter(Filter): coerce values through a typed form field.
#   class ArrayFilter(TypedFilter): accept list-shaped ArrayField values.
#   class RangeFilter(TypedFilter): emit RangeWidget-compatible name_0/name_1 data.
#   class ListFilter(TypedFilter): accept native Strawberry list inputs for "in".
#   class GlobalIDFilter(Filter): parse str or relay.GlobalID, validate type_name,
#       and pass only node_id into django-filter.
#
# TODO(spec-021-filters-0_0_8 Slice 1): Add RelatedFilter and lazy class
# resolution without making consumers spell Strawberry decorators.
# Pseudocode:
#   class LazyRelatedClassMixin:
#       def resolve_lazy_class(self):
#           try import_string(self._filterset)
#           except ImportError: import_string(f"{bound_class.__module__}.{self._filterset}")
#   class RelatedFilter(LazyRelatedClassMixin):
#       def bind_filterset(self, owner): self.bound_class = owner
#       @property
#       def filterset(self): return resolved FilterSet subclass
