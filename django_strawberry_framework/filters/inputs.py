# ruff: noqa: ERA001
"""Filter input namespace planned by ``spec-021-filters-0_0_8``.

Generated input classes must become real globals of this module because
``strawberry.lazy("django_strawberry_framework.filters.inputs")`` resolves
through ``module.__dict__``.
"""

# TODO(spec-021-filters-0_0_8 Slice 2): Build Strawberry input classes with
# explicit lookup-name mapping and correct lazy self-reference placement.
# Pseudocode:
#   LOOKUP_NAME_MAP = {
#       "icontains": ("i_contains", "iContains"),
#       "isnull": ("is_null", "isNull"),
#       "in": ("in_", "in"),
#       ...
#   }
#   and_: list[Annotated["NameInputType", strawberry.lazy(MODULE)]] | None
#   or_: list[Annotated["NameInputType", strawberry.lazy(MODULE)]] | None
#   not_: Annotated["NameInputType", strawberry.lazy(MODULE)] | None
#
# TODO(spec-021-filters-0_0_8 Slice 2): Add the symmetric converter pair
# between resolved django-filter instances and Strawberry input values.
# Pseudocode:
#   def convert_filter_to_input_annotation(filter_instance, model_field, owner_definition):
#       match filter_instance:
#           case GlobalIDFilter(): return str
#           case RangeFilter(): return RangeInput[start: T | None, end: T | None]
#           case ListFilter(): return list[T]
#           case ChoiceFilter(): return generated Strawberry enum
#           case _: return scalar annotation from model field/form field
#
#   def normalize_input_value(filter_instance, raw_value):
#       Enum member -> enum.value
#       relay.GlobalID or encoded string -> decoded node_id after type validation
#       RangeInput -> {"<field>_0": start, "<field>_1": end}
#
# TODO(spec-021-filters-0_0_8 Slice 3): Materialize and clear input classes
# through this module's global namespace, with provenance tracked for
# idempotent finalizer reruns.
# Pseudocode:
#   _materialized_names: dict[str, type[FilterSet]] = {}
#   def materialize_input_class(name, cls):
#       if name already belongs to the same FilterSet: return cls
#       if name belongs to another FilterSet: raise ConfigurationError
#       setattr(sys.modules[__name__], name, cls)
#       _materialized_names[name] = owning_filterset
#   def clear_filter_input_namespace():
#       for name in _materialized_names: delattr(sys.modules[__name__], name)
#       _materialized_names.clear()
