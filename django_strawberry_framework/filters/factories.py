# ruff: noqa: ERA001
"""Filter input factory planned by ``spec-021-filters-0_0_8``."""

# TODO(spec-021-filters-0_0_8 Slice 2): Port the cookbook
# FilterArgumentsFactory BFS while deriving Strawberry input annotations
# from resolved django-filter filter instances, not from a parallel map.
# Pseudocode:
#   class FilterArgumentsFactory:
#       def _ensure_built(self):
#           queue = [root_filterset]
#           while queue:
#               filterset = queue.pop(0)
#               filters = filterset.get_filters()
#               field_specs = [
#                   convert_filter_to_input_annotation(filter_instance, model_field, owner)
#                   for each resolved filter
#               ]
#               input_cls = build_input_class(f"{filterset.__name__}InputType", field_specs)
#               materialize_input_class(input_cls.__name__, input_cls)
#
# TODO(spec-021-filters-0_0_8 Slice 2): Add dynamic FilterSet generation for
# future connection-field callers without widening the consumer surface yet.
# Pseudocode:
#   cache_key = (model, normalized_fields, extra_meta)
#   if cache_key not in _dynamic_filterset_cache:
#       _dynamic_filterset_cache[cache_key] = type(name, (FilterSet,), {"Meta": meta})
