# DRY review: `django_strawberry_framework/testing/client.py`

Status: verified

## System trace

`django_strawberry_framework/testing/client.py` implements the consumer-facing GraphQL test client family, including synchronous and asynchronous HTTP clients, unittest mixins, and response data structures ([spec-043][spec-043]).

It owns the following architectural responsibilities:

1. **Decoded Response Dataclass:**
   - [`Response`][testing-client] (`django_strawberry_framework/testing/client.py::Response`): Subclasses `strawberry.test.client.Response` and houses the raw `HttpResponse` on [`Response.response`][testing-client].

2. **Synchronous GraphQL Test Client:**
   - [`TestClient`][testing-client] (`django_strawberry_framework/testing/client.py::TestClient`): Subclasses `strawberry.test.BaseGraphQLTestClient`.
   - Class guard: [`TestClient.__test__`][testing-client] preventing pytest collection.
   - Initialization & Endpoint: [`TestClient.__init__`][testing-client] resolving endpoints via [`testing_endpoint_setting`][conf] and exposing [`TestClient.client`][testing-client].
   - Execution & Body Synthesis: [`TestClient.query`][testing-client], [`TestClient._finish_response`][testing-client], [`TestClient.request`][testing-client], [`TestClient._build_body`][testing-client], and [`TestClient._assert_file_placeholders`][testing-client].
   - Authentication context: [`TestClient.login`][testing-client].

3. **Asynchronous GraphQL Test Client:**
   - [`AsyncTestClient`][testing-client] (`django_strawberry_framework/testing/client.py::AsyncTestClient`): Subclasses `TestClient` over `django.test.AsyncClient`.
   - Async lifecycle & execution: [`AsyncTestClient.__init__`][testing-client], [`AsyncTestClient.client`][testing-client], [`AsyncTestClient.query`][testing-client], and [`AsyncTestClient.login`][testing-client] (using `sync_to_async`).

4. **Unittest Test Case Mixin & Combinations:**
   - [`GraphQLTestMixin`][testing-client] (`django_strawberry_framework/testing/client.py::GraphQLTestMixin`): Unittest integration class declaring [`GraphQLTestMixin.GRAPHQL_URL`][testing-client], delegating execution in [`GraphQLTestMixin.query`][testing-client] to `TestClient`, and providing assertions [`GraphQLTestMixin.assertResponseNoErrors`][testing-client] and [`GraphQLTestMixin.assertResponseHasErrors`][testing-client].
   - Concrete test cases: [`GraphQLTestCase`][testing-client] (mixing with `django.test.TestCase`) and [`GraphQLTransactionTestCase`][testing-client] (mixing with `django.test.TransactionTestCase`).

Connected behavior examined:
- [`django_strawberry_framework/conf.py`][conf]: Centralized configuration resolver (`testing_endpoint_setting`).
- [`django_strawberry_framework/testing/__init__.py`][testing-init]: Public export interface.
- [`tests/testing/test_client.py`][tests-testing-client]: Complete test suite verifying sync/async queries, multipart file uploads, login context managers, and unittest mixin assertions.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/testing/client.py --include-constants`):
- Parsed 1 target file, 541 lines.
- Complete inventory across all 19 definitions / constants.

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   `TestClient` and `AsyncTestClient` share all uncolored body preparation (`_build_body`), placeholder verification (`_assert_file_placeholders`), and response extraction (`_finish_response`). `GraphQLTestMixin` delegates directly to `TestClient` rather than maintaining a redundant implementation of HTTP posting or multipart formatting.

2. **Sync and async twins:**
   Sync and async clients reuse identical body construction, file placeholder checks, and response packaging. The async client re-implements only the transport await (`await self.request`) and async login context manager (`sync_to_async`).

3. **Derived rather than repeated knowledge:**
   Multipart variable path resolution dynamically generates the `map` payload from `files=` dictionary keys without schema-specific boilerplate. Endpoint defaults derive from `testing_endpoint_setting()`.

4. **Inverse and round-trip pairs:**
   `login()` brackets in both sync and async clients pair `force_login` and `logout` inside try/finally blocks.

5. **Contracts restated in another medium:**
   Codified across:
   - Code: [`django_strawberry_framework/testing/client.py`][testing-client], [`django_strawberry_framework/conf.py`][conf];
   - Specifications: [`docs/SPECS/spec-043-test_client-0_0_12.md`][spec-043];
   - Test suites: [`tests/testing/test_client.py`][tests-testing-client];
   - Documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree].

### The single-edit-site test

- **Posited change 1 (Modifying the multipart body mapping format or reserved field checking):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/testing/client.py`][testing-client] ([`TestClient._build_body`][testing-client] / [`TestClient._assert_file_placeholders`][testing-client]).
  - *Propagation count:* 0 in other source files.
- **Posited change 2 (Adjusting the default testing endpoint configuration):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/conf.py`][conf] ([`testing_endpoint_setting`][conf]).
  - *Propagation count:* 0 in `testing/client.py`.
- **Posited change 3 (Modifying error assertion formatting in GraphQLTestMixin):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/testing/client.py`][testing-client] ([`GraphQLTestMixin.assertResponseNoErrors`][testing-client]).
  - *Propagation count:* 0 in other files.

### Rejected candidates

1. **Re-implementing query posting inside `GraphQLTestMixin`:**
   - Disproved per [spec-043][spec-043] Decision 10. Delegating to `TestClient` eliminates duplication between pytest and unittest testing ergonomics.
2. **Duplicating multipart body building across sync and async clients:**
   - Disproved per [spec-043][spec-043] Decision 9. Inheriting `_build_body` and `_finish_response` ensures uniform behavior across transport colors.

## Opportunities

None — `django_strawberry_framework/testing/client.py` is fully consolidated.

## Judgment

Verified. `testing/client.py` exhibits zero duplicate code and complete policy consolidation between sync and async clients and unittest mixins. All 5 axes of the mandatory duplication probing matrix are verified and discharged. Single-edit-site counts hold at 1 for all posited changes.

## Implementation (Worker 1)

Target verified clean and fully consolidated at root owners. Completeness verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/testing/client.py --review docs/dry/dry-file-testing__client.md --include-constants`. Setting `Status: verified`.

## Independent verification (Worker 2)

Worker 2 performed an independent audit of [`django_strawberry_framework/testing/client.py`][testing-client] and Worker 1's DRY review.

1. **Client Ergonomics & Shared Body Construction:**
   - Confirmed `GraphQLTestMixin` delegates to `TestClient` cleanly.
   - Confirmed `AsyncTestClient` inherits uncolored body and decoding logic from `TestClient`.
2. **Matrix & Single-Edit-Site Verification:**
   - Probed all 5 duplication matrix axes and confirmed all justifications are sound.
   - Verified single-edit-site counts hold at 1 for all posited changes.
3. **Static Check:**
   - Verified with `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/testing/client.py --review docs/dry/dry-file-testing__client.md --include-constants`. 100% coverage across all 19 definitions.

Confirmed: `django_strawberry_framework/testing/client.py` satisfies all DRY requirements with zero code changes needed.

<!-- LINK DEFINITIONS -->

<!-- docs/ -->
[glossary]: ../GLOSSARY.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-043]: ../SPECS/spec-043-test_client-0_0_12.md

<!-- package source -->
[conf]: ../../django_strawberry_framework/conf.py
[testing-client]: ../../django_strawberry_framework/testing/client.py
[testing-init]: ../../django_strawberry_framework/testing/__init__.py

<!-- tests -->
[tests-testing-client]: ../../tests/testing/test_client.py
