"""Planned package-internal auth mutation tests for spec-040."""

# TODO(spec-040 Slice 1): cover the auth declaration ledger and login/logout
# internals that live GraphQL cannot isolate. Pseudocode:
# verify declarations survive the pre-bind emit reset; verify ``registry.clear()``
# drains the auth declaration ledger; verify ``bind_auth_mutations`` raises the
# auth-specific no-UserType error; verify post-finalize factory calls raise
# ``ConfigurationError``; verify async login/logout use one sync boundary; and
# verify async permission hooks raise ``SyncMisuseError`` through ``check_permission``.

# TODO(spec-040 Slice 2): cover the ``Register`` rider internals. Pseudocode:
# verify same-args factory calls return the cached rider and re-record both
# ledgers; verify conflicting permission classes raise ``ConfigurationError``;
# verify ``Register.__name__`` produces ``RegisterPayload`` through the unchanged
# machinery; verify default and custom username-field shapes; verify model decode
# never receives password on either resolver path; verify weak-password errors use
# ``field_error("password", ...)``; and verify reload keeps register's auth error.
