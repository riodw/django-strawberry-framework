# Spec 039 Review Feedback - Pass 3

Review target: [Spec 039][spec-039]. Additional gate this pass:
[live-query README][test-query-readme].

The prior core design fixes still hold on paper. The remaining blocker is test
placement: the current test plan says the right rule, then assigns
live-reachable resolver behavior to root package tests.

## Findings

### [P1] Resolver acceptance coverage is still planned under `tests/rest_framework/`

The test-query README's coverage rule is absolute: any
`django_strawberry_framework/` line that can be earned by a real fakeshop
`/graphql/` request must be earned in `examples/fakeshop/test_query/` first.
Spec 039 says the live surface owns reachable behavior, but its Slice 3 / Test
plan still puts create/update happy paths, serializer error envelopes,
`categoryId` reverse mapping, partial update, visibility-scoped update,
relation visibility, write authorization, authorize-before-decode, and the G2
re-fetch shape under `tests/rest_framework/test_resolvers.py`.

Those are all consumer-visible paths once `products/schema.py` exposes
`createItemViaSerializer` / `updateItemViaSerializer`. The spec already plans
the products mutation and [live `test_products_api.py` coverage][test-products-api],
so keeping duplicate resolver acceptance tests in root `tests/` violates
`examples/fakeshop/test_query/README.md #"Coverage rule."` and the
`docs/TREE.md #"Coverage priority."` statement.

Root fix: merge or reorder the resolver and products surface slices so the
first slice that lands `rest_framework/resolvers.py` also lands the fakeshop
serializer mutation and live tests. Make `test_products_api.py` the required
harness for every Relay-products resolver branch: create/update success, field
and `"__all__"` serializer errors, `categoryId` reverse-map write, partial
update and unique-together validation, hidden update row, write-auth
denial/success, hidden category relation error, authorize-before-decode, and
optimizer re-fetch query shape.

Then narrow `tests/rest_framework/test_resolvers.py` to genuinely unreachable
internals only: pure recursive flattener shapes that no fakeshop serializer
exposes, raw-pk/non-Relay relation decoding if no live non-Relay serializer
mutation is added, many-relation decoding if no live many relation exists,
call-once save capture, sync/async boundary, `SyncMisuseError`, and hermetic
constructor/kwargs seams that cannot be observed over HTTP.

Update the Slice checklist, Implementation plan, Test plan, and Definition of
done so the same behavior is not listed in both places.

### [P2] The shipped serializer `Upload` and request-context branches need live ownership

The spec ships serializer `FileField` / `ImageField` -> `Upload`, routes
`Upload` values into serializer `data`, drops `HiddenField`, injects
`context={"request": ...}`, and tests `Upload in data` plus default request
context under package resolver tests. Existing products live tests already
prove raw GraphQL multipart upload is testable with `django.test.Client`, so
this is not blocked by the future `TestClient` helper.

If those branches ship in `0.0.13`, they are real `/graphql/` behavior and
should be in Slice 4. Root fix: extend `ItemSerializer` or a second products
serializer mutation so `test_products_api.py` covers a multipart serializer
upload to `Item.attachment` and an observable request-context path, such as a
`HiddenField` or `validate()` branch that depends on `request.user`. Keep
package tests for the converter's synthetic field matrix and serializer-only
helper details, but do not let `tests/rest_framework/test_resolvers.py` be the
only proof that the runtime upload/context path works.

### [P3] The spec should name the residual package-test boundary explicitly

The current "Package-internal" section is too broad after the README
tightening. It should say package tests are for schema/build invalid
configurations, field-class conversion matrix rows not exposed by fakeshop,
registry/finalizer lifecycle, soft dependency import simulation, pure
flattening helper edge cases, and runtime branches that are impossible to
drive through the sync `/graphql/` view.

That explicit boundary matters because `tests/rest_framework/` is a planned new
tree; without a narrow rule in the spec, implementers will naturally put
resolver coverage there and then backfill a thin live smoke test. That is the
inverse of the test-query README.

## Checks

- `uv run python scripts/check_spec_glossary.py --spec docs/spec-039-serializer_mutations-0_0_13.md`
  passed: `OK: 30 terms - all have glossary entries and at least one spec link.`

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[spec-039]: spec-039-serializer_mutations-0_0_13.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->
[test-products-api]: ../examples/fakeshop/test_query/test_products_api.py
[test-query-readme]: ../examples/fakeshop/test_query/README.md

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
