# DRY review: `django_strawberry_framework/_django_patches.py`
Status: verified

## System trace
Callers, settings, and sibling patches are traced below as parts of the shared app-load lifecycle.
`_django_patches.py` owns one dependency-local compatibility patch. At import it captures
Django's original `SimpleTestCase._remove_databases_failures` classmethod descriptor and private
`_DatabaseFailure` class. `apply()` then reads the package-wide `APPLY_UPSTREAM_PATCHES` policy
through `conf.py::upstream_patches_enabled`, calls `_validate_upstream_shape()` for the captured
descriptor, `(cls)` signature, and exact upstream source, checks the live class attribute through
`_patch_is_installed()`, and installs `_patched_remove_databases_failures()` as a classmethod only
when needed. That makes application opt-out-aware, fail-loud on dependency drift, idempotent, and
self-healing after a third-party revert.

The replacement preserves Django's alias and disallowed-method loops and changes only ownership
checking at unwrap time: it restores `method.wrapped` only when the current method is still
Django's `_DatabaseFailure`. Django installs those wrappers from
`SimpleTestCase._add_databases_failures()` during `setUpClass()` and registers removal as a class
cleanup. Patching `SimpleTestCase` therefore covers direct subclasses plus inherited
`TransactionTestCase` and `TestCase` behavior. The observable effect is confined to Django test
cleanup for database aliases excluded by a test class: Django-owned wrappers still unwrap, while a
foreign replacement is left untouched instead of crashing cleanup.

`apps.py::DjangoStrawberryFrameworkConfig.ready` is the sole automatic caller and invokes this
module beside the Strawberry and cross_web patch modules after Django app loading. Consumers get
the patch by listing `django_strawberry_framework` in `INSTALLED_APPS`; setting
`DJANGO_STRAWBERRY_FRAMEWORK["APPLY_UPSTREAM_PATCHES"]` false disables all three patch modules
before validation or mutation. The module remains private and is not a package-root export.

The one connected public surface is
`testing/_wrap.py::safe_wrap_connection_method`. It imports this module's
`_is_database_failure` predicate, so Django-private wrapper recognition is already single-sited.
The helper prevents a cooperative consumer wrapper from replacing `_DatabaseFailure` at wrap
time; the automatic patch handles uncooperative replacement at cleanup time. These are distinct
lifecycle phases with distinct effects, not duplicate implementations.

Permanent coverage follows the same boundaries:

- `tests/test_django_patches.py` covers application, live installation, inheritance, original
  upstream failure, guarded cleanup, opt-out, private-shape/signature drift, exact-source drift,
  and unreadable-source refusal.
- `tests/test_apps.py` pins AppConfig discovery and the `ready()` hook.
- `tests/testing/test_wrap.py` covers the public wrap-time helper and its composition with patched
  cleanup.
- `tests/base/test_conf.py` owns the package-wide toggle's default and explicit values.
- `docs/GLOSSARY.md`, `docs/README.md`, and `docs/TREE.md` describe the public effect and test
  placement; they do not implement the lifecycle.

## Verification
The item baseline `8ac07ad6e8b8e932929a3faf9f0a901b990150af` and the current checkout are
identical for `_django_patches.py`, `tests/test_django_patches.py`, and the connected app/testing
paths. Thus the baseline-captured target and test work was preserved, and this review introduced
no package-source or permanent-test diff.

The active environment runs Django 6.0.5. Direct `inspect` reads showed that Django 5.2's stable
source, 6.0's stable source, and the installed 6.0.5 body all use the exact class-level
`_disallowed_connection_methods` loop pinned by the module and still perform unconditional
`method.wrapped` access. Current Django `main` has moved the method list to
`connection.features.disallowed_simple_test_case_connection_methods` but retains the same
unguarded unwrap. The source pin therefore correctly accepts the advertised released 5.2/6.0
shapes and deliberately forces re-audit before a future changed shape can be patched. Django Trac
#37064 is currently closed `invalid`; no upstream fix removes the package's current behavior.

An isolated configured-Django subprocess temporarily restored the captured upstream descriptor and
placed a plain function at `connections["default"].cursor`; upstream raised
`AttributeError: 'function' object has no attribute 'wrapped'`. Restoring the package descriptor
made the same call preserve the foreign function, and Django app setup reported the patch
installed. Inspection of installed django-debug-toolbar also confirmed its complementary
wrap-time `isinstance(connection.cursor, django.test.testcases._DatabaseFailure)` guard.

No pytest invocation was run: this is not the final gate, and `AGENTS.md` forbids pytest unless
explicitly requested. The executable subprocess probe and existing focused permanent tests were
sufficient to resolve the DRY judgment.

Strongest rejected candidates:

1. **The three patch-module `apply()` sequences.** They share the visible order “toggle, validate,
   installed check, install,” but not one install responsibility. Each module defines a different
   dependency shape, a different atomic installed state (one classmethod, one property, or a
   two-method pair), and different drift/remediation errors. A callback-based coordinator would
   hide those dependency-local operations and add a fourth abstraction without removing policy:
   the only shared setting decision is already owned once by
   `conf.py::upstream_patches_enabled`.
2. **Signature and source validation mechanics.** The Django target validates a classmethod
   descriptor; cross_web validates a property getter; Strawberry validates two ordinary methods.
   Only reimplementers pin source. A parameterized helper would need target counts, descriptor
   modes, expected bodies, and caller-owned error text, leaving the knowledge duplicated while
   obscuring which dependency contract failed.
3. **The replacement body and pinned upstream source.** They intentionally represent related but
   different facts: executable guarded behavior versus the exact unguarded body approved for
   supersession. Deriving one from the other or delegating to upstream would weaken the fail-loud
   drift boundary; wrapping cannot intercept upstream's internal `method.wrapped` access safely.
4. **The repeated `_database_failure` test builders.** The patch and public-helper suites construct
   the same private wrapper, but keeping that tiny setup local makes each lifecycle boundary
   independently legible and avoids a shared fixture coupled to a private Django class. Production
   recognition itself is already consolidated in `_is_database_failure`.

## Opportunities
None — the target has one authoritative owner for the Django cleanup replacement, the shared
toggle and wrapper predicate are already single-sited, and the remaining repetition is either
dependency-local lifecycle code or deliberate drift/test evidence. No proven root-owner
consolidation remains.

## Judgment
The current design is DRY at responsibility boundaries and needs no tracked implementation change.
The item is a proved zero-edit result; Worker 3 is next for independent verification, not Worker 2.

## Independent verification (Worker 3)
Verified as a zero-edit item. Blob comparison against item baseline
`8ac07ad6e8b8e932929a3faf9f0a901b990150af` found the target, both sibling patch
modules, `apps.py`, `conf.py`, the public testing wrapper/export, all connected tests, declared
Django support/configuration, and the connected standing docs byte-identical to baseline. The
item-scoped source and permanent-test diff is therefore empty; only this active artifact and its
plan state are being written.

The lifecycle was independently reproduced in isolated configured-Django processes. Listing only
`"django_strawberry_framework"` in `INSTALLED_APPS` resolved
`DjangoStrawberryFrameworkConfig`, ran `ready()`, and installed the classmethod patch; setting
`APPLY_UPSTREAM_PATCHES` false left Django's original method installed. On installed Django 6.0.5,
the captured target is a `(cls)` classmethod with the exact pinned body. Direct probes showed the
unpatched method raising `AttributeError` on a foreign cursor, the patched method preserving that
cursor, `safe_wrap_connection_method` declining to replace a real `_DatabaseFailure`, and patched
cleanup still restoring the wrapper's original callable.

The declared support floor is Django 5.2 and the classifiers name 5.2/6.0. Current upstream
`stable/5.2.x`, `stable/6.0.x`, and installed 6.0.5 retain the exact pinned class-level-method-list
body. Django `main` has moved the list to connection features while retaining the unguarded unwrap,
so rejection by the source pin is the correct future-version re-audit boundary rather than silent
installation of a stale reimplementation. Trac #37064 is currently closed `invalid`; that status
does not alter the reproduced failure or the package-local defensive contract.

All rejected candidates remain rejected after challenge:

1. The three `apply()` bodies share a short ordering skeleton, but their validated dependency
   shapes, installed-state atoms, and mutation operations differ. The common user policy is already
   single-owned by `upstream_patches_enabled()`; a callback coordinator would relocate explicit
   control flow without consolidating dependency knowledge.
2. Signature/source checks likewise carry different descriptor, arity, delegation, and
   reimplementation contracts. A generic validator would require caller-supplied modes, expected
   bodies, and dependency-specific errors, obscuring the owner without removing policy.
3. The executable guarded replacement and exact unguarded source pin are intentionally different
   evidence. Delegation cannot intercept Django's internal `.wrapped` access, and deriving either
   representation from the other would weaken drift detection.
4. Wrap-time refusal and unwrap-time recovery have different callers, timing, mutations, and
   outcomes. Their only shared rule—recognizing `_DatabaseFailure`—is already single-sited in
   `_is_database_failure`.
5. The two local test builders intentionally keep private-Django setup legible at each lifecycle
   boundary; sharing them would couple otherwise independent public-helper and automatic-cleanup
   suites without creating a production owner.

No missed implementation, bypass, stale predicate, or clearer root-owner consolidation was found.
No pytest invocation was run because `AGENTS.md` reserves pytest for explicit requests; installed
source inspection, upstream source comparison, isolated app-load probes, direct behavior probes,
and baseline blob comparison provide the focused verification for this documentation-only closeout.
