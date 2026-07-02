"""Planned package-internal auth query tests for spec-040."""

# TODO(spec-040 Slice 2): cover ``current_user`` internals not suited to live
# acceptance tests. Pseudocode:
# verify the ``CurrentUserAlias`` namespace materializes through
# ``make_input_namespace``; verify its clear is a pre-bind
# ``register_subsystem_clear`` row; verify the injected resolver return annotation
# resolves to ``UserType | None``; verify async ``current_user`` forces
# ``request.user`` inside one sync boundary; and verify gated anonymous ``me``
# raises ``GraphQLError`` while AllowAny returns null.
