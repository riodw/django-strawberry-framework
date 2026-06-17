# TODO(spec-036 Slice 3): cover create, update, and delete resolver behavior.
# Pseudocode:
# - run create, update, and delete happy paths against real Django models;
# - assert full_clean ValidationError maps to ``errors: [FieldError!]`` with a
#   null payload object;
# - assert UniqueConstraint duplication is caught by validate_constraints before
#   save and a mocked save-time IntegrityError covers the race fallback;
# - assert partial update calls full_clean with unprovided fields excluded;
# - assert hidden update/delete rows return a not-found id error without leaking
#   existence;
# - assert create/update response refetch is by pk without the visibility filter;
# - assert delete loads selected relations before deleting the row;
# - assert sync and async paths both work, including SyncMisuseError for an
#   async get_queryset hook from a sync resolver.
