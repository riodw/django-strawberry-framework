# Feedback

## Findings

1. **[P1] The new public file/image wire contract has no live `/graphql/`
   acceptance coverage.**

   The [`test_query` README][test-query-readme] says package coverage that can be
   earned through the fakeshop `/graphql/` endpoint must be earned in
   `examples/fakeshop/test_query/`. The implementation currently keeps every
   file/image read-path assertion in package-level synthetic schemas:
   [`tests/types/test_resolvers.py::_make_asset_model`][test-type-resolver-asset]
   builds an in-process unmanaged model, then calls `schema.execute_sync(...)` for
   the `DjangoFileType` / `DjangoImageType` output object, empty-file parent-null
   behavior, image dimensions, and storage-failure degradation.

   That is useful internal coverage, but it does not prove the consumer-visible
   HTTP contract the README reserves for `test_query`: the fakeshop project schema
   has no selected `FileField` / `ImageField`, no `DjangoFileType` /
   `DjangoImageType` introspection assertion, and no live JSON response selecting
   `name`, `path`, `size`, `url`, `width`, or `height`. The existing scalars app is
   the local precedent: [`examples/fakeshop/apps/scalars/models.py`][scalars-models]
   and [`examples/fakeshop/test_query/test_scalars_api.py`][test-scalars-api]
   deliberately expose converter-table rows over HTTP when SQLite can support
   them. File/image output is SQLite-compatible, so the happy-path and empty-file
   object-null cases should be exposed the same way.

   **Root fix:** add a minimal fakeshop acceptance surface with a real
   `FileField` and `ImageField` model, schema type, and live tests under
   `examples/fakeshop/test_query/` using the documented schema-reload fixture
   pattern. Keep the storage-backend fault injection and corrupt-image edges in
   package tests, but move at least the public SDL shape and representative HTTP
   response behavior into live fakeshop coverage.

2. **[P1] The `Upload` mutation path is verified only below the HTTP boundary.**

   The write side has the same placement problem. The implementation proves
   `FileField` / `ImageField` input generation in
   [`tests/mutations/test_inputs.py`][test-mutation-inputs] and proves assignment
   of `SimpleUploadedFile` through `schema.execute_sync(...)` in
   [`tests/mutations/test_resolvers.py::_make_asset_model`][test-mutation-resolver-asset].
   Those tests bypass the exact pipeline the README calls out: URL routing,
   `GraphQLView`, request parsing, schema execution, and JSON response
   serialization.

   If this package now publicly maps mutation file columns to Strawberry's
   `Upload`, the fakeshop schema should contain one real file-backed mutation and
   a live `examples/fakeshop/test_query/` test should prove the generated input
   type exposes `Upload` over HTTP. If Strawberry's current Django view can accept
   GraphQL multipart requests, the test should also post a real multipart create
   or update. If multipart transport is intentionally deferred, the live suite
   should still introspect the fakeshop mutation input shape over `/graphql/`, and
   the resolver-level `SimpleUploadedFile` tests can remain as the lower-level
   assignment proof.

   **Root fix:** promote one file-backed create/update surface into the example
   project, extend the top-level fakeshop `Mutation` if needed, and add live HTTP
   assertions for `Upload` input SDL plus the strongest transport path available
   today.

## Notes

- I did not run `pytest`, per the repo instruction not to run it unless
  explicitly asked.
- The existing package tests still have value. The compliance gap is that the
  public GraphQL contract is not represented in the live acceptance suite.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->
[test-mutation-inputs]: ../tests/mutations/test_inputs.py
[test-mutation-resolver-asset]: ../tests/mutations/test_resolvers.py
[test-type-resolver-asset]: ../tests/types/test_resolvers.py

<!-- examples/ -->
[scalars-models]: ../examples/fakeshop/apps/scalars/models.py
[test-query-readme]: ../examples/fakeshop/test_query/README.md
[test-scalars-api]: ../examples/fakeshop/test_query/test_scalars_api.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
