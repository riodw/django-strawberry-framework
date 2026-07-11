# Pre-BETA review: auth/

Scope: authentication surface -- `mutations.py` (login/logout/register + auth
surface declaration/binding) and `queries.py` (`current_user`).

Method: full logic read of both modules in `docs/shadow/current/`. Read-only;
no tests run.

Bottom line: the login/logout/register/current_user semantics are correct and
security-aware (no user enumeration, session rotation via `auth.login`, password
validated + hashed on register, inactive users rejected by the auth backend).
No P0 or P1. The notes are about the things a framework deliberately leaves to
the consumer -- make them explicit before BETA.

## P0 -- correctness suspicions

None found.

## P1 -- fix before BETA

None found.

## P2 -- polish / hardening

### `mutations.py` -- document that throttling/rate-limiting is the consumer's responsibility
Confidence: low (documentation). `_login_resolve_body` returns a single generic
`_INCORRECT_CREDENTIALS_MESSAGE` on failure (good -- no enumeration), but there is
no built-in brute-force throttle. That is a reasonable framework boundary
(consumers attach throttling via `permission_classes` or middleware), but the
auth docs should say so explicitly so nobody ships a login mutation assuming the
framework rate-limits it.

### `mutations.py::derive_register_fields` -- bound the auto-derived register surface
Confidence: low. Register exposes `USERNAME_FIELD + REQUIRED_FIELDS + password`.
For a stock user model this is exactly right and excludes `is_staff`/
`is_superuser`. But a custom user model that (unusually) lists a privilege flag
in `REQUIRED_FIELDS` would expose it on the public register input. Consider a
guard that refuses to auto-expose known privilege fields (or documents the
derivation clearly) so a custom user model cannot accidentally open a
privilege-escalation input.
Verify: define a user model with `is_staff` in `REQUIRED_FIELDS` and inspect the
generated register input fields.

## API & consistency notes

- CSRF/session behavior over GraphQL POST depends on the strawberry view + Django
  middleware, not this module. The test client exposes
  `Client(enforce_csrf_checks=True)` for testing it. Worth a docs cross-link so
  consumers verify CSRF enforcement on their login endpoint.
- `bind_auth_mutations` resolves the user primary type from the registry and
  fails loud (`_resolve_user_primary_or_raise`) when the user model has no
  registered primary type but auth surfaces were declared. Good -- a
  misconfiguration surfaces at build time.

## Verified sound (do not re-flag)

- `_login_resolve_body`: `auth.authenticate` returns `None` for bad credentials
  *and* for inactive users (ModelBackend's `user_can_authenticate`), both mapped
  to the same generic error -- no user enumeration and no inactive-user login.
  Success calls `auth.login`, which cycles the session key (session-fixation
  defense).
- `register`: `validate_password(raw_password, user)` runs before
  `set_password`, and the raw password is captured via the excluded-field path
  and never persisted in the clear.
- Permission checks run through `authorize_or_raise` on every auth surface
  (login/logout/current_user), so consumer `permission_classes` apply uniformly.
- Async parity: auth bodies run through `run_in_one_sync_boundary`
  (`sync_to_async`), so session/ORM writes stay in a sync boundary.
- `current_user` returns the authenticated user or `None` (unauthenticated),
  with the actor passed to the permission check as the instance.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
