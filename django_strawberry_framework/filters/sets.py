# ruff: noqa: ERA001
"""FilterSet class hierarchy planned by ``spec-021-filters-0_0_8``."""

# TODO(spec-021-filters-0_0_8 Slice 1): Implement the FilterSet metaclass
# and FilterSet subclass on top of ``django_filters.filterset.BaseFilterSet``.
# Pseudocode:
#   class FilterSetMetaclass(filterset.FilterSetMetaclass):
#       collect RelatedFilter declarations into cls.related_filters
#       bind each RelatedFilter to the new class
#
#   class FilterSet(filterset.BaseFilterSet, metaclass=FilterSetMetaclass):
#       _owner_definition = None
#       FILTER_DEFAULTS = {... FK/PK -> owner-aware GlobalID or scalar PK ...}
#       def get_filters(cls): expand related filters with _is_expanding_filters guard
#       def filter_for_field(cls, field, field_name, lookup_expr): choose runtime filter
#       def filter_for_lookup(cls, field, lookup_type): keep django-filter and input shape aligned
#
# TODO(spec-021-filters-0_0_8 Slice 1): Keep resolver-facing filtering split
# by sync/async context so async get_queryset hooks cannot be used from sync
# resolvers silently.
# Pseudocode:
#   @classmethod
#   def apply_sync(cls, input_value, queryset, info):
#       data = cls._normalize_input(input_value)
#       child_qs = cls._derive_related_visibility_querysets_sync(input_value, info)
#       request = cls._request_from_info(info)
#       cls._run_permission_checks(input_value, request)
#       filterset = cls(data=data, queryset=queryset, request=request)
#       cls._validate_form_or_raise(filterset)
#       queryset = cls._apply_related_constraints(input_value, queryset, child_qs)
#       return filterset.qs
#
#   @classmethod
#   async def apply_async(cls, input_value, queryset, info):
#       same pipeline, but await child get_queryset visibility hooks.
