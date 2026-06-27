# TODO(spec-039 Slice 3): Keep this file limited to resolver internals that a
# real products `/graphql/` request cannot drive.
# Pseudo cases:
#   - recursive error flattener handles list indexes and nested dict paths;
#   - nested non-field errors normalize to the path-all sentinel;
#   - non-Relay raw-pk relation decode reports visibility errors;
#   - many-relation decode reports visibility errors;
#   - wrong-model and uncoercible raw-pk relation ids become field errors;
#   - integrity errors map to the field-error envelope;
#   - save-time DRF validation errors use the recursive flattener;
#   - serializer `save()` is called once and refetch uses the returned object;
#   - `get_serializer_kwargs(...)` remains the constructor seam;
#   - bare `HttpRequest` context fallback works;
#   - async boundary and sync misuse errors match existing mutation behavior.
#
# Explicit exclusions: do not duplicate live happy paths, envelopes,
# reverse-map writes, partial update, visibility, write authorization,
# authorize-before-decode, Upload, request context, or G2 SQL-shape tests.
