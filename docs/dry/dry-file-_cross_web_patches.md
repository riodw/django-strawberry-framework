# DRY review: `django_strawberry_framework/_cross_web_patches.py`

Status: verified

## System trace

The module owns one dependency-specific compatibility boundary. At import it captures
`cross_web.DjangoHTTPRequestAdapter.body`'s genuine getter; `_validate_upstream_shape` verifies that
delegation target still exists with the expected getter signature; `_patched_body` preserves the
upstream UTF-8 success path and returns raw request bytes only after `UnicodeDecodeError`;
`_patch_is_installed` checks the live descriptor; and `apply` gates, validates, and installs the
property idempotently.

`django_strawberry_framework/apps.py::DjangoStrawberryFrameworkConfig.ready` is the only production
caller. `django_strawberry_framework/conf.py::upstream_patches_enabled` already owns the shared
`APPLY_UPSTREAM_PATCHES` policy. Strawberry's sync view selects this adapter and reads `.body`
before JSON parsing; the async adapter already returns bytes. The companion
`django_strawberry_framework/_strawberry_patches.py::_patched_parse_json` owns the later
`UnicodeDecodeError`-to-HTTP-400 translation. Dedicated mechanics live in
`tests/test_cross_web_patches.py`; real endpoint outcomes live in
`examples/fakeshop/test_query/test_products_api.py`. The module has no package-root export.

## Verification

- The target, `tests/test_cross_web_patches.py`, `django_strawberry_framework/apps.py`, and
  `tests/test_apps.py` have an empty worktree diff from item baseline
  `cd6c914d919f9f353ea358867d9811beef947e79`; their current dirty state is baseline work, with no
  later item-scoped change.
- Package-wide searches found the target symbols only in the target, its app-load caller, and its
  dedicated tests. The shared setting is already single-sited in `conf.py`; sibling patch modules
  consume it rather than reimplementing it.
- Installed-upstream inspection (`cross-web 0.7.0`) confirmed the sync getter still calls bare
  `.decode()` and raises `UnicodeDecodeError` for invalid UTF-8 and UTF-16, while
  `AsyncDjangoHTTPRequestAdapter.get_body` returns raw bytes.
- A direct AppConfig probe confirmed the wrapper is installed, valid UTF-8 still returns `str`,
  invalid UTF-8 falls back to `bytes`, and UTF-16 bytes remain JSON-decodable.
- A real Django `/graphql/` probe produced `patched: invalid=400, utf16=200`; temporarily restoring
  the captured upstream getter in the isolated process produced `upstream: invalid=500,
  utf16=500`. The descriptor was restored in `finally`.
- No pytest run: Worker 1 is not assigned the final gate, and repository policy forbids an
  unsolicited suite run.

## Opportunities

None — the current target has one owner for each rule and no tracked consolidation is warranted.

Strongest rejected candidates:

- **Shared patch-application helper.** `_cross_web_patches.py`, `_django_patches.py`, and
  `_strawberry_patches.py` all spell the short gate → validate → installed-check → install
  lifecycle. Their contracts do not otherwise coincide: they patch a property, a classmethod, and
  a coupled method pair; delegation versus source-pinned reimplementation drives different drift
  validation; and each dependency retires independently. A callback-only helper would hide the
  mutation site without removing dependency-specific policy, tests, or reasons to change.
- **Shared callable-signature validator.** The modules all use `inspect.signature`, but each pins a
  different private upstream object and must emit a dependency-specific remediation message.
  Parameterizing callable, arity, label, and error text would move little knowledge while weakening
  the fail-loud audit at the patch owner.
- **Merge the cross_web and Strawberry request-body patches.** They cooperate on invalid bytes but
  repair different upstream layers. The cross_web patch also independently establishes sync/async
  parity for UTF-16/32 success, while the Strawberry patch covers async and multipart parsing and
  has separate retirement conditions. Keeping one module per patched dependency is the clearer
  ownership and retirement boundary.
- **Deduplicate sibling patch tests.** Their similar idempotency, reinstall, drift, and opt-out
  tests intentionally prove each monkey-patched dependency boundary independently. Shared
  parameterization would obscure distinct restoration mechanics and failure contracts without
  reducing production duplication.

## Judgment

The current module is narrow, necessary against the installed upstream, and already composes
through single-sited settings and app-load owners. This is a proved zero-edit result; Worker 3 is
next for independent verification.
## Independent verification (Worker 3)

Verified. An independent trace confirmed that `ready()` is the sole production installer and
`conf.py` is the sole setting owner; Strawberry's sync view reads
`DjangoHTTPRequestAdapter.body`, while its async sibling already awaits raw bytes. Installed
cross-web 0.7.0 and current upstream `main` still bare-decode the sync body, so the wrapper remains
necessary. The Strawberry sibling owns only the later `UnicodeDecodeError`-to-400 translation, and
the Django sibling patches an unrelated test teardown lifecycle.

Package- and test-wide searches found no second body fallback, patch installer, setting
interpretation, or bypass. The rejected shared lifecycle/signature helpers remain weaker owners:
the three dependency patches differ in mutation shape, validation depth, coupled installation,
and retirement trigger, while their parallel tests intentionally preserve those distinct
contracts.

A fresh process confirmed app-load installation, `str` preservation for valid UTF-8, raw-byte
fallback for invalid UTF-8 and UTF-16, and the captured upstream getter's
`UnicodeDecodeError`. A live `/graphql/` comparison under an isolated host override produced
patched statuses `400` (invalid bytes) and `200` (UTF-16), versus upstream `500` and `500`; the
descriptor was restored in `finally`.

The initial item-scoped comparison to `cd6c914d919f9f353ea358867d9811beef947e79` was empty across
the target, hook, setting/export owners, sibling modules, dependency metadata, endpoint wiring,
and relevant tests. A concurrent documentation-only edit then appeared in
`_strawberry_patches.py`, correcting its own call-site count without changing executable behavior
or this boundary; it was re-read and left untouched. Every other scoped path remains
baseline-identical. No pytest run, per repository policy.

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
