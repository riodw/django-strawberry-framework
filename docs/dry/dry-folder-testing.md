# DRY folder integration: `django_strawberry_framework/testing/`

Status: verified

## System trace

The `django_strawberry_framework/testing/` subsystem provides consumer test utilities for executing GraphQL operations over HTTP, managing transactional and live client test cases, safely instrumenting database connection methods, and minting/asserting Relay GlobalIDs ([spec-032][spec-032], [spec-043][spec-043]).

It consists of 4 modular components:

1. **Public Testing Surface & Exports ([`django_strawberry_framework/testing/__init__.py`][testing-init]):**
   - Re-exports: [`TestClient`][testing-init], [`AsyncTestClient`][testing-init], [`Response`][testing-init], [`GraphQLTestMixin`][testing-init], [`GraphQLTestCase`][testing-init], [`GraphQLTransactionTestCase`][testing-init], and [`safe_wrap_connection_method`][testing-init].

2. **Connection Method Instrumentation Safety ([`django_strawberry_framework/testing/_wrap.py`][testing-wrap]):**
   - [`safe_wrap_connection_method`][testing-wrap] (`django_strawberry_framework/testing/_wrap.py::safe_wrap_connection_method`): Wraps database connection methods safely during test setup by consulting [`_is_database_failure`][django-patches].

3. **HTTP GraphQL Test Client & Unittest Family ([`django_strawberry_framework/testing/client.py`][testing-client]):**
   - Response representation: [`Response`][testing-client] (`django_strawberry_framework/testing/client.py::Response`, [`Response.response`][testing-client]).
   - Synchronous client: [`TestClient`][testing-client] (`django_strawberry_framework/testing/client.py::TestClient`) with pytest collection guard [`TestClient.__test__`][testing-client], constructor [`TestClient.__init__`][testing-client], client accessor [`TestClient.client`][testing-client], query dispatch [`TestClient.query`][testing-client], response finishing [`TestClient._finish_response`][testing-client], request implementation [`TestClient.request`][testing-client], multipart payload synthesis [`TestClient._build_body`][testing-client], placeholder validation [`TestClient._assert_file_placeholders`][testing-client], and authentication context [`TestClient.login`][testing-client].
   - Asynchronous client: [`AsyncTestClient`][testing-client] (`django_strawberry_framework/testing/client.py::AsyncTestClient`) with constructor [`AsyncTestClient.__init__`][testing-client], client accessor [`AsyncTestClient.client`][testing-client], query dispatch [`AsyncTestClient.query`][testing-client], and async login [`AsyncTestClient.login`][testing-client].
   - Unittest mixin and test cases: [`GraphQLTestMixin`][testing-client] (`django_strawberry_framework/testing/client.py::GraphQLTestMixin`, [`GraphQLTestMixin.GRAPHQL_URL`][testing-client], [`GraphQLTestMixin.query`][testing-client], [`GraphQLTestMixin.assertResponseNoErrors`][testing-client], [`GraphQLTestMixin.assertResponseHasErrors`][testing-client]), [`GraphQLTestCase`][testing-client], and [`GraphQLTransactionTestCase`][testing-client].

4. **Relay GlobalID Test Utilities ([`django_strawberry_framework/testing/relay.py`][testing-relay]):**
   - [`global_id_for`][testing-relay] (`django_strawberry_framework/testing/relay.py::global_id_for`): Mints encoded `GlobalID` strings for finalized `DjangoType` instances using [`encode_typename`][types-relay] and [`STRING_GLOBALID_STRATEGIES`][types-base].
   - [`decode_global_id`][testing-relay] (`django_strawberry_framework/testing/relay.py::decode_global_id`): Direct re-export of [`types/relay.py::decode_global_id`][types-relay].

Connected behavior examined:
- [`django_strawberry_framework/_django_patches.py`][django-patches]: Central teardown backstop and `_is_database_failure` predicate.
- [`django_strawberry_framework/conf.py`][conf]: Configuration resolution for `TESTING_ENDPOINT`.
- [`django_strawberry_framework/types/relay.py`][types-relay]: Relay encoding and decoding implementation.
- [`django_strawberry_framework/types/base.py`][types-base]: `DjangoType` definitions, strategy constants, and error templates.
- [`tests/testing/`][tests-testing]: Acceptance test suite covering client requests, multipart uploads, unittest mixins, connection wrapping, and Relay helpers.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/testing/ --include-constants`):
- Parsed 4 target files across `django_strawberry_framework/testing/`.
- Total symbols covered across all 4 files.

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   `TestClient` and `AsyncTestClient` share all uncolored body preparation, placeholder verification, and response extraction. `GraphQLTestMixin` delegates directly to `TestClient` rather than maintaining a redundant implementation of HTTP posting or multipart formatting. Connection wrapping reuses `_django_patches._is_database_failure`. Relay test helpers reuse `types/relay.py` directly.

2. **Sync and async twins:**
   Sync and async clients reuse identical body construction, file placeholder checks, and response packaging. The async client re-implements only the transport await and async login context manager (`sync_to_async`).

3. **Derived rather than repeated knowledge:**
   Multipart variable path resolution dynamically generates the `map` payload from `files=` dictionary keys without schema-specific boilerplate. Endpoint defaults derive from `testing_endpoint_setting()`. Relay GlobalIDs derive from `definition.effective_globalid_strategy`.

4. **Inverse and round-trip pairs:**
   `login()` brackets in both sync and async clients pair `force_login` and `logout` inside try/finally blocks. `safe_wrap_connection_method` forms a wrap/unwrap defense pair with `_django_patches.py`. `global_id_for` and `decode_global_id` form an encode/decode test pair.

5. **Contracts restated in another medium:**
   Codified across:
   - Code: `django_strawberry_framework/testing/`, `django_strawberry_framework/conf.py`, `django_strawberry_framework/types/relay.py`;
   - Specifications: [`docs/SPECS/spec-032-full_relay-0_0_9.md`][spec-032], [`docs/SPECS/spec-043-test_client-0_0_12.md`][spec-043];
   - Test suites: [`tests/testing/`][tests-testing];
   - Documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree].

### The single-edit-site test

- **Posited change 1 (Modifying the multipart body mapping convention or reserved field checking):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/testing/client.py`][testing-client] ([`TestClient._build_body`][testing-client] / [`TestClient._assert_file_placeholders`][testing-client]).
  - *Propagation count:* 0 in other files.
- **Posited change 2 (Adjusting the default testing endpoint setting name or fallback):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/conf.py`][conf] ([`testing_endpoint_setting`][conf]).
  - *Propagation count:* 0 in `testing/`.
- **Posited change 3 (Modifying the GlobalID encoding implementation):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/types/relay.py`][types-relay] ([`encode_typename`][types-relay]).
  - *Propagation count:* 0 in `testing/`.

### Rejected candidates

1. **Re-implementing query posting inside `GraphQLTestMixin`:**
   - Disproved per [spec-043][spec-043] Decision 10. Delegating to `TestClient` eliminates duplication between pytest and unittest testing ergonomics.
2. **Duplicating `_is_database_failure` in `testing/_wrap.py`:**
   - Disproved per [spec-043][spec-043]. Sharing `_is_database_failure` between `_django_patches.py` and `testing/_wrap.py` prevents desynchronization.

## Opportunities

None — the `django_strawberry_framework/testing/` subsystem is completely integrated and consolidated at root owners.

## Judgment

Verified. `testing/` exhibits zero duplicate code and complete policy consolidation through shared configuration, patch, and Relay infrastructure. All 5 axes of the mandatory duplication probing matrix are verified and discharged. Single-edit-site counts hold at 1 for all posited changes.

## Implementation (Worker 1)

Target verified clean and fully consolidated at root owners. Completeness verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/testing/ --review docs/dry/dry-folder-testing.md --include-constants`. Setting `Status: verified`.

## Independent verification (Worker 2)

Worker 2 performed an independent audit of the `django_strawberry_framework/testing/` subsystem and Worker 1's DRY review.

1. **Subsystem Architecture & Shared Foundation Integration:**
   - Verified that all 4 files in `django_strawberry_framework/testing/` cleanly isolate test client, database instrumentation, and Relay test helper concerns.
   - Verified that `testing/client.py` delegates to `conf.py` for endpoint discovery and that `testing/relay.py` delegates to `types/relay.py` for ID encoding.
2. **Matrix & Single-Edit-Site Verification:**
   - Probed all 5 duplication matrix axes across the subsystem and confirmed all justifications are sound.
   - Verified single-edit-site counts hold at 1 for all posited changes.
3. **Static Check:**
   - Verified with `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/testing/ --review docs/dry/dry-folder-testing.md --include-constants`. 100% coverage across all target definitions in the folder.

Confirmed: `django_strawberry_framework/testing/` satisfies all DRY requirements with zero code changes needed.

<!-- LINK DEFINITIONS -->

<!-- docs/ -->
[glossary]: ../GLOSSARY.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-032]: ../SPECS/spec-032-full_relay-0_0_9.md
[spec-043]: ../SPECS/spec-043-test_client-0_0_12.md

<!-- package source -->
[conf]: ../../django_strawberry_framework/conf.py
[django-patches]: ../../django_strawberry_framework/_django_patches.py
[testing-client]: ../../django_strawberry_framework/testing/client.py
[testing-init]: ../../django_strawberry_framework/testing/__init__.py
[testing-relay]: ../../django_strawberry_framework/testing/relay.py
[testing-wrap]: ../../django_strawberry_framework/testing/_wrap.py
[types-base]: ../../django_strawberry_framework/types/base.py
[types-relay]: ../../django_strawberry_framework/types/relay.py

<!-- tests -->
[tests-testing]: ../../tests/testing/
