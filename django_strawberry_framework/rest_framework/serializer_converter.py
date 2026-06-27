# ruff: noqa: D100

# TODO(spec-039 Slice 1): Implement the DRF serializer-field to Strawberry input
# converter using `utils/converters.py`, not a local dispatch fork.
# Pseudo flow:
#   - Guard DRF import before touching serializer field classes.
#   - Model conversions as `scalar`, `relation_single`, `relation_multi`, or `file`.
#   - Carry annotation, kind, requiredness, declared GraphQL name, serializer field
#     name, and optional source in the conversion/spec records.
#   - `convert_serializer_field(...)` ignores `is_input` for 0.0.13.
#   - Convert `ManyRelatedField` from its child relation, `PrimaryKeyRelatedField`
#     as a single id, file/image fields as `Upload`, and scalar list children
#     recursively.
#   - Resolve relation targets from either a backing model field via one-segment
#     `source` or a serializer-only relation's `field.queryset.model`.
#   - Reject nested serializer children and relation children inside `ListField`.
#   - Delegate scalar fallback to `convert_with_mro(...)` with a fail-loud
#     unsupported handler.
#
# Reverse-map obligations:
#   - GraphQL names come from the declared serializer field name, not `source`.
#   - Relation names obey the id-like suffix rule:
#       category -> categoryId
#       category_id -> categoryId
#       category_pk -> categoryPk
#   - Backing Django fields are resolved through one-segment `source`.
#   - Dotted `source` and `source="*"` fail loudly for model-column conversions.
#   - A relation field with neither a resolvable backing field nor
#     `queryset.model` fails loudly because it cannot be typed or visibility
#     checked.
