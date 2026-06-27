# ruff: noqa: D100

# TODO(spec-039 Slice 1): Promote the fail-loud converter dispatch skeleton here
# before adding `rest_framework/serializer_converter.py`.
# Pseudo flow:
#   - Run ordered prechecks first; the first non-null conversion wins.
#   - Walk the concrete field class MRO and call the first exact registry match.
#   - If neither path handles the field, raise the caller-provided unsupported
#     exception so every converter fails loudly.
#
# Required DRY contract:
#   - `forms/converter.py::convert_form_field` must call this helper after the
#     extraction, keeping its exact observable behavior.
#   - `rest_framework/serializer_converter.py::convert_serializer_field` must
#     supply only DRF-specific prechecks and registry rows.
#   - There must be no `serializers.Field -> str` catch-all; unsupported custom
#     fields raise `ConfigurationError`.
