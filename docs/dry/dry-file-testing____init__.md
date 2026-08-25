# DRY review: `django_strawberry_framework/testing/__init__.py`

Status: verified

## System trace

`django_strawberry_framework/testing/__init__.py` defines the public export facade for consumer test utilities, GraphQL test clients, test cases, and database connection wrapping ([spec-043][spec-043]).

It re-exports the following public symbols:

1. **GraphQL Test Clients & Response Primitives:**
   - [`TestClient`][testing-init] (`django_strawberry_framework/testing/__init__.py::TestClient`): Synchronous GraphQL test client wrapping `django.test.Client`.
   - [`AsyncTestClient`][testing-init] (`django_strawberry_framework/testing/__init__.py::AsyncTestClient`): Asynchronous GraphQL test client wrapping `django.test.AsyncClient`.
   - [`Response`][testing-init] (`django_strawberry_framework/testing/__init__.py::Response`): Typed GraphQL response carrying parsed `data`, `errors`, `extensions`, and raw HTTP response.

2. **Unittest Test Case Family:**
   - [`GraphQLTestMixin`][testing-init] (`django_strawberry_framework/testing/__init__.py::GraphQLTestMixin`): Mixin providing `query()`, `assertResponseNoErrors()`, and `assertResponseHasErrors()`.
   - [`GraphQLTestCase`][testing-init] (`django_strawberry_framework/testing/__init__.py::GraphQLTestCase`): Standard `TestCase` combining `GraphQLTestMixin` and `django.test.TestCase`.
   - [`GraphQLTransactionTestCase`][testing-init] (`django_strawberry_framework/testing/__init__.py::GraphQLTransactionTestCase`): Transactional `TransactionTestCase` combining `GraphQLTestMixin` and `django.test.TransactionTestCase`.

3. **Database Connection Safety:**
   - [`safe_wrap_connection_method`][testing-init] (`django_strawberry_framework/testing/__init__.py::safe_wrap_connection_method`): Cooperative wrapping helper defending against Django Trac #37064 unwrap issues.

Connected behavior examined:
- [`django_strawberry_framework/testing/client.py`][testing-client]: Live GraphQL HTTP test client implementation.
- [`django_strawberry_framework/testing/_wrap.py`][testing-wrap]: Safe connection method wrapper implementation.
- [`django_strawberry_framework/testing/relay.py`][testing-relay]: Relay GlobalID test helpers (kept separate at dotted submodule path to prevent unnecessary top-level type imports).
- [`tests/testing/`][tests-testing]: Acceptance tests for testing utilities.

## Verification

Static analysis and inventory (`export_dry_review.py check --target django_strawberry_framework/testing/__init__.py --include-constants`):
- Parsed 1 target file, 65 lines.
- Complete inventory across all 7 exported definitions.

### Mandatory 5-axis duplication probing matrix

1. **Cross-flavor policy mirroring:**
   `testing/__init__.py` acts as a pure re-export interface without declaring independent implementations. Relay helpers are intentionally excluded to keep the root import lightweight.

2. **Sync and async twins:**
   Re-exports both `TestClient` (sync) and `AsyncTestClient` (async) from their canonical definitions in `testing/client.py`.

3. **Derived rather than repeated knowledge:**
   All exported symbols are imported directly from submodules without redundant wrappers.

4. **Inverse and round-trip pairs:**
   `safe_wrap_connection_method` acts as the wrap-time companion to the unwrap-time patch in `_django_patches.py`.

5. **Contracts restated in another medium:**
   Codified across:
   - Code: [`django_strawberry_framework/testing/__init__.py`][testing-init], [`django_strawberry_framework/testing/client.py`][testing-client], [`django_strawberry_framework/testing/_wrap.py`][testing-wrap];
   - Specifications: [`docs/SPECS/spec-043-test_client-0_0_12.md`][spec-043];
   - Test suites: [`tests/testing/`][tests-testing];
   - Documentation: [`docs/README.md`][readme], [`docs/GLOSSARY.md`][glossary], [`docs/TREE.md`][tree].

### The single-edit-site test

- **Posited change 1 (Adding a new consumer test utility export):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/testing/__init__.py`][testing-init] (`__all__`).
  - *Propagation count:* 0 in other source files.
- **Posited change 2 (Modifying HTTP test client execution):**
  - *Production ownership count:* Exactly 1 site in [`django_strawberry_framework/testing/client.py`][testing-client] ([`TestClient`][testing-client]).
  - *Propagation count:* 0 in `testing/__init__.py`.

### Rejected candidates

1. **Re-exporting `global_id_for` and `decode_global_id` in `testing/__init__.py`:**
   - Disproved per [spec-043][spec-043]. Keeping them at the dotted `testing.relay` path avoids importing `types/` when only importing base testing clients.

## Opportunities

None — `django_strawberry_framework/testing/__init__.py` is a clean re-export facade.

## Judgment

Verified. `testing/__init__.py` exhibits zero duplicate code. All 5 axes of the mandatory duplication probing matrix are verified and discharged. Single-edit-site counts hold at 1 for all posited changes.

## Implementation (Worker 1)

Target verified clean and fully consolidated at root owners. Completeness verified with `docs/dry/export_dry_review.py check --target django_strawberry_framework/testing/__init__.py --review docs/dry/dry-file-testing____init__.md --include-constants`. Setting `Status: verified`.

## Independent verification (Worker 2)

Worker 2 performed an independent audit of [`django_strawberry_framework/testing/__init__.py`][testing-init] and Worker 1's DRY review.

1. **Public Exports & Submodule Isolation:**
   - Confirmed public symbols match the declared API in `spec-043`.
   - Confirmed `testing.relay` is preserved at its dedicated submodule path.
2. **Matrix & Single-Edit-Site Verification:**
   - Probed all 5 duplication matrix axes and confirmed all justifications are sound.
   - Verified single-edit-site counts hold at 1 for all posited changes.
3. **Static Check:**
   - Verified with `uv run python docs/dry/export_dry_review.py check --target django_strawberry_framework/testing/__init__.py --review docs/dry/dry-file-testing____init__.md --include-constants`. 100% coverage across all 7 definitions.

Confirmed: `django_strawberry_framework/testing/__init__.py` satisfies all DRY requirements with zero code changes needed.

<!-- LINK DEFINITIONS -->

<!-- docs/ -->
[glossary]: ../GLOSSARY.md
[readme]: ../README.md
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[spec-043]: ../SPECS/spec-043-test_client-0_0_12.md

<!-- package source -->
[testing-client]: ../../django_strawberry_framework/testing/client.py
[testing-init]: ../../django_strawberry_framework/testing/__init__.py
[testing-relay]: ../../django_strawberry_framework/testing/relay.py
[testing-wrap]: ../../django_strawberry_framework/testing/_wrap.py

<!-- tests -->
[tests-testing]: ../../tests/testing/
