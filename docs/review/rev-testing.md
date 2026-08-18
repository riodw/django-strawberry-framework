# Review: `django_strawberry_framework/testing/`

Status: verified

## Understanding

The testing folder is three deliberately separate consumer seams behind one dotted package path:

- `testing/client.py` owns the sync/async Django HTTP clients, typed `Response`, multipart
  `operations`/`map` construction, endpoint precedence, login brackets, and the
  graphene-shaped mixin. The mixin delegates body building and decoding to `TestClient`;
  async code is only the required transport/context-manager color.
- `testing/_wrap.py` owns the public wrap-time `safe_wrap_connection_method` protocol. It
  shares `_django_patches.py::_is_database_failure` with the app-load unwrap backstop, so
  consumers decline to clobber Django's `_DatabaseFailure` while the patched
  `SimpleTestCase._remove_databases_failures` remains safe when a foreign wrapper was
  installed anyway.
- `testing/relay.py` owns only the consumer minting facade. `global_id_for` validates the
  exact active registry definition, finalization, Relay-Node shape, and encode-only
  strategy boundary before delegating the payload to `types/relay.py::encode_typename`;
  `decode_global_id` is an identity re-export of the production decoder.

The public boundary is intentional: `testing/__init__.py` exports the client family and
wrap helper, while Relay helpers remain at `testing.relay`; the package root exports neither.
`conf.py::testing_endpoint_setting` is a live settings reader, but `TestClient` resolves and
stores its endpoint at construction. `GraphQLTestMixin` constructs a delegate per call, so
its `GRAPHQL_URL` and current settings are re-read without mutating an existing client's
`path`; a per-call `url=` remains non-persistent.

The connected lifecycle is complete: `registry.clear()` co-clears generated connection and
node-field ledgers; finalization stamps Relay strategies before `finalized` and the helper
rejects inherited or stale definitions; fakeshop schema reload rebuilds every contributing
app after a registry reset. The client envelope is consumed by Django's package view, whose
multipart parser owns the same external `operations` / `map` wire fields. Fakeshop's ordinary
JSON helper routes through `TestClient`; raw-envelope transport tests intentionally remain
bare Django posts.

## Verification

- Read the complete package (`testing/__init__.py`, `_wrap.py`, `client.py`, and `relay.py`),
  all three verified file artifacts, `conf.py`, `_django_patches.py`, package-root
  exports, `registry.py`, finalization and Relay strategy paths, the package test files,
  fakeshop schema reload/URL/view wiring, and live client/Relay acceptance usage.
- `uv run pytest --no-cov -q tests/testing tests/base/test_conf.py tests/test_django_patches.py`
  — **118 passed**. This jointly exercises endpoint settings reload, constructor-time
  endpoint resolution, client/mixin exports and assertions, multipart guards, Relay helper
  strategy/registry gates, `registry.clear()` isolation, and Django's real
  wrap/unwrap patch boundary.
- `uv run pytest --no-cov -q examples/fakeshop/test_query/test_client_api.py
  examples/fakeshop/test_query/test_library_api.py -k 'client or node or global_id or
  genre_books_connection'` — **47 passed**. The live run covers sync/async JSON and
  multipart transport, login cleanup, endpoint overrides, HTTP error decoding, Relay
  node/nodes dispatch, GlobalID strategy parity, and connection behavior.
- A fresh-process import probe for `import django_strawberry_framework.testing` showed
  `testing.relay` is not imported, while the parent package had already loaded
  `django_strawberry_framework.types` and 63 package modules. This confirms the Relay
  submodule exclusion but also disproves any claim that the testing import is globally
  lightweight while the package root remains eager.
- Existing fakeshop isolation rebuilds all app schemas after `registry.clear()`, and the
  permanent Relay regression rejects both inherited-only and post-clear stale definitions.
  Existing client tests prove settings changes affect newly constructed clients while
  explicit `path` and per-call `url` retain their documented precedence and state.

## Improvements

### High

None.

### Medium

None. No correctness, security, session/cookie isolation, lifecycle, transport, or public
contract failure was reproduced when the three testing seams were exercised together.

### Low

#### Make the import-weight contract match the package-root architecture

**Observation:** `testing/__init__.py` and `testing/relay.py` describe the dotted Relay
submodule as keeping the testing import light, but Python executes the eager
`django_strawberry_framework/__init__.py` before any `testing` submodule. The root already
imports `types`, `connection`, optimizer, mutations, and the other public graph; importing
`testing` then eagerly adds `client` and `_wrap`.

**Evidence:** The fresh-process probe reported 63 `django_strawberry_framework.*` modules,
`django_strawberry_framework.types` present, and `django_strawberry_framework.testing.relay`
absent immediately after `import django_strawberry_framework.testing`.

**Impact:** This is a bounded startup-cost/documentation mismatch, not a runtime correctness
failure. A folder-local lazy export would not deliver the promised end-to-end light import
while the parent root remains eager, and could make the public surface less consistent with
the sibling subpackages.

**Recommendation:** In the project-level public-export pass, either revise the “light import”
rationale to say precisely that only `testing.relay` is excluded from the testing package's
additional imports, or redesign the package-root/subpackage exports together. Do not add a
testing-only shim that implies it solved the root import graph.

**Proof:** The import probe above is a reproducible measurement; no production change is
owned by this folder and no permanent regression test is warranted until the project-level
export decision is made.

## Summary

The testing folder has coherent ownership and no integrated production defect. Client body
construction/decoding, async and mixin colors, settings reload versus construction state,
connection wrap/unwrap recovery, Relay registry/finalization gates, and live fakeshop
transport/refetch behavior agree across their boundaries. The only improvement is the
documented import-weight claim, which belongs to the project public-export pass rather than
to a folder-local fix.

## Implementation (Worker 1)

No production or permanent-test edit was needed. The prior Relay helper hardening and its
regression test were present and passed; all unrelated and concurrent dirty paths were
preserved. This integrated artifact is the only Worker 1 addition, and its status is
`fix-implemented` for independent verification. No changelog entry is warranted.

The scoped review evidence is:

`uv run pytest --no-cov -q tests/testing tests/base/test_conf.py tests/test_django_patches.py`

→ 118 passed

`uv run pytest --no-cov -q examples/fakeshop/test_query/test_client_api.py examples/fakeshop/test_query/test_library_api.py -k 'client or node or global_id or genre_books_connection'`

→ 47 passed

No full pytest run was performed.

## Independent verification (Worker 2)

No production or permanent-test edit was made during this pass. I independently
re-traced the integrated testing folder through `testing/__init__.py`, `_wrap.py`,
`client.py`, `relay.py`, `conf.py`, package-root exports, `_django_patches.py`,
`apps.py`, registry/finalization, the complete fakeshop schema reload helper,
`config.schema`, `config.urls`, and the live client/Relay acceptance paths.
Unrelated concurrent dirty paths were preserved.

Focused commands and results:

- `uv run pytest --no-cov -q tests/testing tests/base/test_conf.py tests/test_django_patches.py`
  — **118 passed in 5.05s** on Django 6.1 / Python 3.14.2.
- `uv run pytest --no-cov -q examples/fakeshop/test_query/test_client_api.py
  examples/fakeshop/test_query/test_library_api.py -k 'client or node or global_id or
  genre_books_connection'` — **47 passed in 14.41s**. This includes the live sync
  and async client paths, auth brackets, endpoint/error behavior, multipart
  uploads, Relay node/refetch behavior, and nested connection requests.
- `uv run pytest --no-cov -q examples/fakeshop/apps/products/tests/test_schema.py
  examples/fakeshop/apps/library/tests/test_schema.py` — **5 passed in 7.15s**.
  These in-process tests exercise the composed schema after the complete
  app-registration rebuild.

Fresh-process probes:

- `PYTHONPATH=examples/fakeshop DJANGO_SETTINGS_MODULE=config.test_settings uv run
  python` import probe: after `django.setup()` and `import
  django_strawberry_framework.testing`, `testing.relay` was absent while
  `testing.client` and `testing._wrap` were loaded; the package had 65
  `django_strawberry_framework.*` modules and `types` was already loaded.
  Explicitly importing `testing.relay` then loaded only that submodule and its
  `decode_global_id` remained the exact `types.relay` function. This confirms
  the narrow Relay exclusion and routes the broader import-weight observation to
  the project public-export pass.
- A fresh schema probe imported `config.schema`, recorded 60 definitions,
  called `registry.clear()`, then ran `schema_reload.reload_all_project_schemas()`.
  The rebuilt schema was a distinct object with 60 definitions, a finalized
  registry, and `schema.execute_sync('{ __typename }')` returned
  `{'__typename': 'Query'}`.
- A fresh Relay lifecycle probe minted an ID for the initial fakeshop
  `GenreType`, rejected that finalized class with
  `ConfigurationError` after `registry.clear()`, rebuilt all app schemas, then
  minted and decoded successfully for the distinct fresh `GenreType`.
- A fresh Django 6.1 wrap/unwrap probe exercised the actual feature list
  (`connect`, `temporary_connection`, `cursor`, `chunked_cursor`): the public
  helper declined to replace a real `_DatabaseFailure`, the patched teardown
  preserved a foreign `cursor` callable even when it exposed `.wrapped`, and
  unwrapped every remaining genuine `_DatabaseFailure` instance.

The combined import/export, settings reload and endpoint precedence, registry
isolation, Relay strategy/finalization gates, sync/async transport and multipart
maps, Django wrap/unwrap lifecycle, and fakeshop schema/live-route behavior
remain consistent. No High, Medium, or Low folder-level correctness issue was
reproduced; the existing Low import-weight note is correctly routed to the
project-level export pass. No full pytest suite was run.

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
