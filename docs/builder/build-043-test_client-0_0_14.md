# Build plan: spec-043 GraphQL test-client family (`0.0.14`)

Input contract: `docs/spec-043-test_client-0_0_14.md`. Three slices per the
spec's slice checklist: Slice 1 (the Strawberry test-module gate +
`TESTING_ENDPOINT` + `testing/client.py` + re-exports +
`tests/testing/test_client.py` + the targeted Slice-1 live conversions),
Slice 2 (remaining live-suite switchover), Slice 3 (docs + card wrap; no
version bump - the joint `0.0.14` cut owns it). This build ran Slice 1 only.

## Slice 1 - Strawberry test-module gate record

- **No dependency delta**: `[project].dependencies`,
  `[dependency-groups].dev`, and `uv.lock` untouched - the clients subclass
  the engine-owned `strawberry.test.BaseGraphQLTestClient` over the package's
  existing hard `strawberry-graphql` dependency (Decision 5).
- **Strawberry-floor gate** (spec DoD item): in an isolated throwaway venv
  (never the shared `.venv`):

  ```
  uv venv "$SCRATCH/floorenv043" --python 3.12
  uv pip install --python "$SCRATCH/floorenv043/bin/python" \
      'strawberry-graphql==0.262.0' 'django>=5.2'
  "$SCRATCH/floorenv043/bin/python" -c "
  from strawberry.test import BaseGraphQLTestClient
  from strawberry.test.client import Response, Body
  import dataclasses, inspect
  fields = [f.name for f in dataclasses.fields(Response)]
  assert fields == ['errors', 'data', 'extensions'], fields
  assert getattr(BaseGraphQLTestClient.request, '__isabstractmethod__', False)
  print('sig:', inspect.signature(BaseGraphQLTestClient.__init__))
  "
  ```

  Outcome: **PASS** at `strawberry-graphql==0.262.0` -
  `BaseGraphQLTestClient` / `Response` / `Body` all import; the `Response`
  field names are exactly `errors` / `data` / `extensions`; `request()` is
  abstract; `__init__` is `(client, url='/graphql/')` (so forwarding the
  resolved endpoint as the base's `url` is floor-safe). No Strawberry floor
  bump needed.

## Slice 1 - file delta (per the spec's Implementation plan table)

- `django_strawberry_framework/conf.py` - `TESTING_ENDPOINT_KEY` +
  `testing_endpoint_setting()` (default `"/graphql/"`).
- `django_strawberry_framework/testing/client.py` - `Response`, `TestClient`,
  `AsyncTestClient`, `GraphQLTestMixin`, `GraphQLTestCase`,
  `GraphQLTransactionTestCase` (Decisions 5-10).
- `django_strawberry_framework/testing/__init__.py` - the six re-exports.
- `tests/testing/test_client.py` - the package-tier scenarios (raising/guard
  directions, the endpoint ladder, the builder map rule, the async client,
  the unittest family, the surface guards).
- `examples/fakeshop/test_query/test_uploads_api.py` - converted onto
  `TestClient` (JSON reads + the two nested-input multipart mutations with
  `operation_name=`, the Slice-1 `files=` vehicles).
- `examples/fakeshop/test_query/test_products_api.py` - the `login()` bracket
  and `operation_name` dispatch live scenarios added via `TestClient`.

## Slice 1 - adversarial review round (post-build)

Independent reviewer verified all 12 spec decisions against the
implementation, the installed strawberry 0.316.0, upstream
`strawberry_django/test/client.py`, and `graphene_django/utils/testing.py`.
Four real findings, all fixed and pinned by new tests, re-verified by
revert-probe (each pin fails on the pre-fix shape):

1. `files={}` built a multipart envelope but posted/decoded it as JSON
   (`is None` vs truthiness switch mismatch) - `_build_body` now guards
   `if not files`.
2. `variables={}` with `files=` slipped past the placeholder guard into a
   spec-invalid envelope - guard now `if not variables`.
3. The inherited base `url` attribute read the base default while `path`
   read the real endpoint - the resolved endpoint is now forwarded to
   `super().__init__`.
4. `assertResponseNoErrors` on a non-200 without an `errors` key failed with
   a bare message - failures now carry `{"errors": ..., "data": ...}`.

Plus the spec Test-plan `res.extensions` assertion (added) and an accepted
letter-deviation: the endpoint ladder is pinned by four named tests instead
of one parametrized test (rung-specific assertions; coverage equivalent).

## Slice 1 - verification

- `uv run pytest tests/testing/test_client.py
  examples/fakeshop/test_query/test_uploads_api.py
  examples/fakeshop/test_query/test_products_api.py` - **124 passed**;
  `testing/client.py` **100%** (87/87 statements) from the spec-043 test set
  alone.
- Full sweep (`uv run pytest`): **3038 passed, 15 skipped, 4 xfailed** (run
  pre-review-round; the aggregate coverage number in that run was corrupted
  by a concurrent session's worker files - re-run the gate on a quiet tree).
- `ruff check` / `ruff format --check` / ASCII-only: clean on the touched
  files.
