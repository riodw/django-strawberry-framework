# TODO(spec-039 Slice 2): Add package tests for `SerializerMutation` Meta
# validation, registration, and bind lifecycle.
# Pseudo cases:
#   - missing `serializer_class` raises `ConfigurationError`;
#   - non-serializer and plain serializer classes are rejected;
#   - `ModelSerializer` without `Meta.model` is rejected;
#   - delete operation is rejected;
#   - `permission_classes` remains an allowed key;
#   - `fields`/`exclude` mutual exclusion and unknown-key errors are preserved;
#   - serializer mutations register and ride `bind_mutations()`;
#   - retry idempotence clears serializer input namespace before bind;
#   - no registered primary type raises the existing model-flavor error;
#   - model-flavor seam defaults remain unchanged.
#
# Boundary: this file covers build-time lifecycle only; live create/update
# behavior belongs in products HTTP tests.
