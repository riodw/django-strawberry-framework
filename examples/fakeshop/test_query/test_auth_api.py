"""Live ``/graphql/`` auth API acceptance tests planned by spec-040."""

# TODO(spec-040 Slice 1): add login/logout live tests. Pseudocode: seed users
# first, execute login with the seeded username and password, assert the payload
# user plus session cookie, then cover wrong credentials, inactive user, and
# anonymous/authenticated logout.
# Every auth test's first executable line must be ``create_users(N)`` from
# ``apps.products.services``. Do not hand-roll ``User`` rows in this file.

# TODO(spec-040 Slice 2): add register/current_user live tests. Pseudocode:
# seed users first, register a fresh username with a strong password, assert
# hashed storage with ``check_password``, then execute login, me, logout, and
# final me -> null.
# Also cover duplicate username, weak-password keyed to ``password`` not
# ``__all__``, anonymous me -> null, and permission-gated auth fields with exact
# top-level GraphQLError denial strings.
