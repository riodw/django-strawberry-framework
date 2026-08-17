# Review: `django_strawberry_framework/_django_patches.py`

Status: verified

## Understanding

`django_strawberry_framework._django_patches` owns one dependency-local
compatibility patch. Import-time capture records Django's original
`SimpleTestCase._remove_databases_failures` classmethod and private
`_DatabaseFailure` type. `apply()` reads the package
`APPLY_UPSTREAM_PATCHES` gate, validates the descriptor, `(cls)` signature, and
the exact captured body against the two audited Django shapes, then installs a
classmethod replacement only when the patch is not already installed.

The replacement preserves Django's alias and disallowed-method loops while
checking `isinstance(method, _DatabaseFailure)` before reading `.wrapped`.
Django's `SimpleTestCase.setUpClass()` installs those wrappers and registers
the cleanup callback; patching `SimpleTestCase` therefore covers direct
subclasses and inherited `TransactionTestCase` / `TestCase` behavior. A
Django-owned wrapper is restored exactly; a foreign replacement is left
untouched rather than causing teardown to crash.

The method-list source is version-shaped rather than version-number-shaped:
Django 5.2.16 and 6.0.5 expose
`SimpleTestCase._disallowed_connection_methods`, while Django 6.1 exposes
`connection.features.disallowed_simple_test_case_connection_methods`.
`_disallowed_connection_methods()` selects the matching source at cleanup
time. `django_strawberry_framework/apps.py::DjangoStrawberryFrameworkConfig.ready` is the automatic caller
and dispatches this patch beside the Strawberry and cross-web patches.

The connected public seam is
`django_strawberry_framework.testing._wrap::safe_wrap_connection_method`.
It shares `_is_database_failure()` for wrap-time refusal; the target's
automatic patch is the unwrap-time backstop for third-party code or connection
recycling that did not preserve Django's wrapper.

## Verification

The item baseline was `314f7db8bb3224a82ca5121dd1042187402ad548`. The scoped
diff for the target and connected permanent-test paths is empty:

`git --no-pager diff 314f7db8bb3224a82ca5121dd1042187402ad548 -- django_strawberry_framework/_django_patches.py tests/test_django_patches.py tests/test_apps.py django_strawberry_framework/apps.py django_strawberry_framework/testing/_wrap.py tests/testing/test_wrap.py django_strawberry_framework/conf.py`

Focused permanent tests:

`uv run pytest --no-cov tests/test_django_patches.py tests/test_apps.py tests/testing/test_wrap.py`

Result: 33 passed on the installed Django 6.1. The tests cover app-load
dispatch and re-fire, idempotence and self-healing, direct and inherited test
case classes, real-wrapper restoration, foreign-wrapper preservation, the
original upstream crash, both method-list shapes, private-symbol/signature/
body/source drift, opt-outs, and the public wrap helper.

Disposable verification:

`uv run pytest --no-cov docs/review/temp-tests/_django_patches/test_lifecycle.py`

Result: 1 passed. The probe exercised every configured database alias,
verified that excluded aliases unwrap all disallowed methods, and verified
that an allowed alias remains wrapped.

Direct source probes confirmed the exact audited upstream body and list source
on Django 5.2.16, 6.0.5, and installed 6.1. The 6.1 probe also confirmed the
feature-flag list contains the four expected `(name, operation)` pairs.
Django's class cleanup order was traced from `SimpleTestCase.setUpClass()`:
the cleanup callback is registered immediately after `_add_databases_failures`,
so the patch runs at the intended teardown boundary.

The upstream Trac #37064 report documents both the plain-function /
connection-recycling failure and the exact `isinstance` guard proposal:
<https://code.djangoproject.com/ticket/37064>. Its eventual `invalid`
resolution assigns the invariant violation to the code replacing Django's
wrapper; this package's helper addresses cooperative callers, while the
automatic guard remains necessary for connection recycling and uncooperative
third-party instrumentation.

## Improvements

### High

None.

### Medium

None.

### Low

None.

## Summary

The target has a single clear owner for Django teardown compatibility, a
dependency-specific gate and shape validator, and a self-healing app-load
lifecycle. Both released method-list shapes in the declared Django range are
supported, and the cleanup behavior is verified across the configured
database aliases. No root-cause implementation change was proven necessary.

## Implementation (Worker 1)

None — zero-edit cycle.

The empty scoped diff above is the implementation result. No permanent tests
were added because the existing focused suites already cover the target's
behavior at the strongest reachable package-test tier. The disposable
multi-alias probe remains under
`docs/review/temp-tests/_django_patches/` as review evidence.

Rejected candidates and evidence:

1. **Move the fix entirely to consumer wrappers.** Rejected because the
   upstream report reproduces the mismatch when a database connection is
   recycled between `setUpClass()` and teardown; no consumer wrapper can
   restore a wrapper on a newly replaced connection. The existing
   `safe_wrap_connection_method` tests cover the cooperative case, while the
   target tests cover the teardown backstop.
2. **Replace the three patch modules with a shared generic `apply()` helper.**
   Rejected because each module validates a different private dependency
   shape and has a different installed-state atom (classmethod, property, or
   method pair). The only shared policy is already single-sited in
   `django_strawberry_framework/conf.py::upstream_patches_enabled`.
3. **Drop exact source pinning in favor of signature-only validation.**
   Rejected because this module reimplements Django's complete private loop;
   signature-only validation could overwrite an upstream-fixed or otherwise
   reshaped body with stale behavior. Existing drift and sourceless-source
   tests prove the fail-loud boundary.
4. **Use a generic `.wrapped`/attribute check instead of
   `isinstance(_DatabaseFailure)`.** Rejected because the target must restore
   only Django-owned wrappers; the upstream report and the existing public
   helper contract explicitly avoid chasing arbitrary third-party objects
   that happen to expose `.wrapped`.

Formatting and linting were not run because this was a zero-edit cycle.
No changelog entry is warranted.

## Independent verification (Worker 2)

The target and every connected production/test path named by the artifact have
an empty scoped diff against baseline `314f7db8bb3224a82ca5121dd1042187402ad548`:

`git --no-pager diff --name-status 314f7db8bb3224a82ca5121dd1042187402ad548 -- django_strawberry_framework/_django_patches.py tests/test_django_patches.py tests/test_apps.py django_strawberry_framework/apps.py django_strawberry_framework/testing/_wrap.py tests/testing/test_wrap.py django_strawberry_framework/conf.py`

No source or permanent-test edit was made during this verification.

The app-loading and kill-switch lifecycle was checked independently in fresh
configured-Django processes. With only
`INSTALLED_APPS = ["django_strawberry_framework"]`, `django.setup()` ran
`DjangoStrawberryFrameworkConfig.ready()` and installed the patch by default;
with `{"APPLY_UPSTREAM_PATCHES": False}`, the upstream classmethod remained
untouched. Repeated `ready()` / `apply()` calls remain idempotent, and the
existing focused tests also confirm self-healing after a foreign classmethod
replacement. The patch is intentionally an app-load gate, not a runtime
uninstaller: disabling the setting before app load prevents installation.

The current installed Django 6.1 source was inspected directly: the captured
method is a `(cls)` classmethod, its four disallowed pairs come from
`connection.features.disallowed_simple_test_case_connection_methods`, and
the package replacement matches the upstream alias-skip / per-connection
loop with only the ownership guard added. Disposable `setUpClass()` plus
`doClassCleanups()` probes exercised the actual Django callback lifecycle:
all four Django-owned methods (`connect`, `temporary_connection`, `cursor`,
`chunked_cursor`) restored to their original bound callables; a foreign
`cursor` callable and a foreign object exposing a misleading `.wrapped`
attribute were both preserved. Django 5.2.16 and 6.0.5 were independently
inspected in isolated environments and both matched the class-attribute body
already audited by the artifact. The package declares those releases and 6.1
as supported; an un-audited future body remains fail-loud.

Re-run focused evidence:

- `uv run pytest --no-cov tests/test_django_patches.py tests/test_apps.py tests/testing/test_wrap.py` — **33 passed**.
- `uv run pytest --no-cov docs/review/temp-tests/_django_patches/test_lifecycle.py` — **1 passed**; excluded aliases unwrap every disallowed method and an allowed alias retains its wrappers.

Each rejected candidate remains independently disposed of. The real
class-cleanup probe demonstrates why consumer-only wrap helpers cannot cover
uncooperative replacements; the module-local shape/source validation remains
necessary because the replacement supersedes Django's complete private loop;
the distinct patch-module descriptors and installed-state atoms do not share a
safe generic `apply()` owner; and a generic `.wrapped` check would incorrectly
unwrap the foreign lookalike that the `isinstance(_DatabaseFailure)` guard
preserves. No correctness, lifecycle, alias, sync/async, version, idempotence,
or documentation-contract finding remains.
