# TEMP — Trac #37064 Test Plan

Status: temporary verification plan for the current branch. Delete or fold into the numbered
spec once the Trac #37064 hardening ships.

## Sources checked

- Django Trac #37064: `SimpleTestCase._remove_databases_failures()` assumes every
  disallowed connection method still exposes `.wrapped`; Django closed the proposed
  guard as invalid because a third party replaced Django's wrapper.
- Demo reproducer:
  `django-remove_databases_failures-demo/demo/repro/tests.py` replaces
  `connections["other"].cursor` with a plain callable in `TransactionTestCase.setUp`;
  the test body passes and class teardown crashes.
- Old package workaround:
  `/Users/riordenweber/projects/django-graphene-filters/conftest.py` widens
  `TransactionTestCase.databases` and `TestCase.databases` to `"__all__"`. That avoids
  Django installing disallowed-database wrappers, but it is the wrong layer for this
  package because every consumer would need project-local boilerplate.
- `django-debug-toolbar` SQL panel:
  `debug_toolbar.panels.sql.tracking.wrap_cursor` returns before wrapping when
  `connection.cursor` is already Django's `_DatabaseFailure`.
- `django-debug-toolbar` cache panel PR #1770:
  the cache fix stopped trying to undo monkey patches and used an active-panel sentinel
  because multiple parties wrapping the same method cannot be perfectly unwound without
  a shared ordering protocol.

## Test Placement

Put the coverage in `tests/`, not `examples/fakeshop/test_query/`, because the failure
is Django test-class setup/teardown behavior and is not reachable through a live
`/graphql/` query. The example project remains useful as fixtures for package tests, but
this bug is below the GraphQL API layer.

## Required Tests

1. `tests/test_django_patches.py` pins the automatic unwrap-time backstop:
   `AppConfig.ready()` installs the patch on `SimpleTestCase`, `TransactionTestCase` and
   `TestCase` inherit it, a direct `SimpleTestCase` subclass is covered, a real
   `_DatabaseFailure` unwraps normally, a plain callable does not crash, the unpatched
   upstream body still crashes, `apply()` is idempotent and self-healing, and a missing
   private `_DatabaseFailure` symbol no-ops with one log notice.
2. `tests/test/test_wrap.py` pins the wrap-time mirror:
   `safe_wrap_connection_method` installs into a free slot, declines when Django's
   `_DatabaseFailure` is present, handles arbitrary disallowed method names, composes
   with the unwrap-time patch, and remains usable if Django moves/removes the private
   `_DatabaseFailure` symbol.
3. No root `conftest.py`, base test class, or settings key is acceptable as the fix.
   Consumers get the backstop by installing `django_strawberry_framework`.

## Efficient Mixed Strategy

Use both debug-toolbar-inspired patterns, but only where this package controls the
lifecycle point.

- Wrap-time guard is cheapest: a single predicate check avoids allocating or installing a
  wrapper. This is what `django-debug-toolbar` does in SQL tracking and what
  `safe_wrap_connection_method` exposes for consumer code.
- Unwrap-time guard is still necessary: this package cannot force every third-party
  cursor wrapper to call the helper, so Django teardown must not crash when a foreign
  callable already replaced Django's wrapper.
- Sentinel-over-uninstall is the right pattern for future package-owned instrumentation:
  if this package ever owns a persistent connection/cache wrapper, leave the wrapper in
  place and toggle an active owner/recorder sentinel instead of trying to restore a
  method stack it cannot order.

## Verification Commands

Do not run pytest unless the maintainer asks. When requested, run the focused checks:

```bash
uv run pytest --no-cov tests/test_django_patches.py tests/test/test_wrap.py
```

Then, if the focused checks pass and the maintainer wants broader confidence:

```bash
uv run pytest --no-cov
FAKESHOP_SHARDED=1 uv run pytest --no-cov
```
