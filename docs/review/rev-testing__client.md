# Review: `django_strawberry_framework/testing/client.py`

Status: verified

Cycle baseline: current `HEAD` `fa248bdf`. The target source and its permanent
mechanics tests were clean at dispatch. The scoped target diff was captured with
`git --no-pager diff HEAD -- django_strawberry_framework/testing/client.py
tests/testing/test_client.py`; it was empty. Existing unrelated and concurrent
dirty paths were preserved.

## Understanding

`testing/client.py` owns the complete consumer-facing HTTP test-client family:
the typed `Response`, synchronous `TestClient`, asynchronous
`AsyncTestClient`, and the graphene-shaped `GraphQLTestMixin` with its
`GraphQLTestCase` / `GraphQLTransactionTestCase` combinations.

`TestClient` resolves its endpoint once at construction through
`conf.py::testing_endpoint_setting`, preserving the documented precedence of
per-call `url`, constructor `path`, mixin `GRAPHQL_URL`, the settings key, and
`/graphql/`. Its package-owned `_build_body` adds `operationName`, validates
dotted dict/list placeholder paths, rejects reserved multipart envelope names,
and emits the uniform path-keyed `operations` / `map` envelope. `request` owns
the Django POST boundary: JSON explicitly sets `application/json`; multipart
deliberately omits `content_type` so Django selects its multipart encoder.

The client subclasses Strawberry's `BaseGraphQLTestClient` only for the
engine-owned `_decode`, response field schema, and abstract transport seam.
`_finish_response` attaches the raw Django response and raises explicitly when
`assert_no_errors` is enabled. The async client shares body construction and
response finishing while awaiting only the transport. Both login context
managers force-login on entry and logout in `finally`, including when the
protected block raises.

`GraphQLTestMixin.query` delegates to a fresh `TestClient` over the test case's
own `self.client`, so Django session/cookie state and client configuration are
preserved. Its assertion helpers retain graphene's HTTP-status/error semantics
while accepting the package `Response`. The testing package exports only the
testing family; the package root remains free of these names.

Connected contracts traced:

- Strawberry's `BaseGraphQLTestClient` and its JSON/multipart `_decode`;
- Django `Client` / `AsyncClient` POST signatures and multipart default;
- `conf.py::testing_endpoint_setting` and live settings reload behavior;
- fakeshop live JSON, operation-name, session-login, async, and nested
  two-file upload suites;
- package mechanics tests for endpoint precedence, body/map construction,
  placeholder and reserved-name guards, response extensions, falsy injection,
  exports, and assertion-helper failure directions.

## Verification

Focused permanent suites:

- `uv run pytest --no-cov -q tests/testing/test_client.py` — **31 passed**.
- `uv run pytest --no-cov -q examples/fakeshop/test_query/test_client_api.py`
  — **11 passed**.

Additional executable probes:

- Sync and async `login()` both executed `logout()` after a raised block error,
  while preserving explicitly supplied falsy transport objects.
- Sync and async JSON requests propagated custom headers and sent
  `content_type="application/json"`.
- Sync and async multipart requests omitted `content_type`, preserved headers,
  and emitted the expected path-keyed map.

The live upload suite proves nested input-object paths (`data.attachment` and
`data.image`) through Django's real multipart parser; package mechanics prove
top-level, nested, and list-index paths plus malformed path/placeholder
boundaries. Existing live auth tests prove session state before, during, and
after the login bracket. Existing live async tests prove awaited transport and
decode parity. The response decoder deliberately preserves Django's
`ValueError`/`JSONDecodeError` transport failures and keeps the raw response
available for status/header/cookie assertions.

## Improvements

### High

None. No correctness, security, data-isolation, or public-contract failure was
reproduced.

### Medium

None. Endpoint non-persistence, JSON/multipart content types, nested/list maps,
placeholder validation, operation-name placement, response assertions, sync /
async parity, login cleanup, mixin delegation, and collection/export boundaries
are each covered by source tracing plus focused tests or executable probes.

### Low

None. Sync/async duplication is limited to the unavoidable await and context
manager color boundaries; the shared body builder, response finisher, and
transport owner already provide the appropriate single sites.

## Summary

The client contract is internally consistent and matches its documented
Strawberry/Django/graphene boundaries. Both transport colors, upload map shapes,
endpoint precedence, response/error behavior, session cleanup, injection,
headers, and public collection/export behavior are verified. No production
root-cause fix or permanent regression test is warranted, and no cross-file
ownership expanded.

## Implementation (Worker 1)

No source or permanent-test changes were needed. The only changed file is this
artifact:

- `docs/review/rev-testing__client.md`

The scoped source/test diff against dispatch `HEAD` remains empty. The artifact
is marked `fix-implemented` for Worker 2's independent verification. No
changelog entry is warranted. `uv run ruff format .` and
`uv run ruff check --fix .` are required after this artifact edit; no full
pytest suite was run.

## Independent verification (Worker 2)

Independently re-traced the current target source against Strawberry
`BaseGraphQLTestClient` (`__init__`, `_decode`, `Response`, and the abstract
`request` seam), Django 6.1 `Client` / `AsyncClient` POST behavior, the settings
reader, the testing exports, the live fakeshop URLconf, and the sync/async
upload and auth call paths. No source or permanent-test diff exists for the
target; unrelated concurrent dirty paths were left untouched.

Focused test commands and results:

- `uv run pytest --no-cov -q tests/testing/test_client.py` — **31 passed**.
- `uv run pytest --no-cov -q examples/fakeshop/test_query/test_client_api.py` —
  **11 passed**.
- `uv run pytest --no-cov -q examples/fakeshop/test_query/test_uploads_api.py
  -k 'multipart_create_uploads_real_files_over_http or
  multipart_create_media_specimen_image_via_form_over_http'` — **2 passed**.
- `uv run pytest --no-cov -q examples/fakeshop/test_query/test_products_api.py
  -k 'create_item_login_bracket_via_test_client or
  operation_name_dispatch_via_test_client'` — **2 passed**.
- `uv run ruff check django_strawberry_framework/testing/client.py
  tests/testing/test_client.py examples/fakeshop/test_query/test_client_api.py &&
  uv run ruff format --check django_strawberry_framework/testing/client.py
  tests/testing/test_client.py examples/fakeshop/test_query/test_client_api.py` —
  **all checks passed; 3 files already formatted**.

Adversarial executable probes also passed:

- Sync and async recording transports preserved explicitly supplied falsy
  clients, propagated custom headers, used JSON
  `content_type="application/json"`, omitted `content_type` for multipart,
  routed one-call `url=` overrides without changing `path`, and preserved
  nested dict/list-index `map` paths plus `operationName` inside the encoded
  `operations` body.
- Missing, scalar, non-canonical/out-of-range list, non-`None`, and reserved
  `operations` / `map` placeholders all raised the intended `AssertionError`
  before transport; sync and async login logout cleanup ran after protected
  block exceptions.
- A malformed `application/json` response on both JSON and multipart decode
  paths preserved `json.JSONDecodeError`; no framework wrapper replaced the
  raw transport failure.

The requested endpoint precedence/non-persistence, response/error behavior,
headers/content types, multipart nested/list/reserved validation,
`operation_name`, falsy injection, mixin delegation/assertions, collection and
export boundaries, and live fakeshop async/auth/upload flows all remain sound.
No concrete issue was reproduced; status is **verified**. No full pytest suite
was run.

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
