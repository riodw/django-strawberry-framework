# TODO(spec-039 Slice 1): Add package tests for converter-only behavior that is
# not owned by the live products API.
# Pseudo cases:
#   - supported serializer fields map annotation and requiredness;
#   - primary-key relation fields generate one strategy-dependent annotation
#     (Relay GlobalID or raw-pk scalar), not a dual-shape GraphQL field;
#   - many-relation fields map to a list of ids;
#   - file/image serializer fields map to `Upload`;
#   - renamed `source` fields preserve the declared serializer name in reverse map;
#   - serializer-only relations resolve targets from `field.queryset.model`;
#   - id-like suffix rules avoid `categoryIdId`;
#   - dotted source and `source="*"` fail for model-column conversion;
#   - unknown custom serializer fields raise `ConfigurationError`;
#   - scalar `ListField` children map, while relation or nested children fail.
#
# Boundary: no create/update resolver acceptance tests here; reachable resolver
# behavior belongs in `examples/fakeshop/test_query/test_products_api.py`.
