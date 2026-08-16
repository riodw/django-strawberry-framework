# DRY review: `django_strawberry_framework/testing/client.py`

Status: verified

## System trace

`testing/client.py` owns the consumer-facing GraphQL **HTTP test-client
family**: sync `TestClient`, async `AsyncTestClient`, typed `Response`, and the
graphene-shaped `GraphQLTestMixin` / `GraphQLTestCase` /
`GraphQLTransactionTestCase`.

Ownership map (present-day source):

| Concern | Owner |
| --- | --- |
| Endpoint ladder (constructor `path=` / settings / `"/graphql/"`) | `TestClient.__init__` via `conf.testing_endpoint_setting` |
| Class-attr rung (`GRAPHQL_URL`) | `GraphQLTestMixin` → passes into `TestClient(...)` |
| Per-call `url=` | `TestClient.request` / both `query` colors |
| JSON + multipart body build, `operationName`, path-keyed file map, placeholder / reserved-key guards | `TestClient._build_body` + `_assert_file_placeholders` (shadows engine base) |
| Transport POST (JSON `content_type` vs omit for multipart) | `TestClient.request` |
| Decode + typed `Response` + `assert_no_errors` raise | `TestClient._finish_response` (uses engine `_decode`) |
| Sync/async `query` orchestration | Color twins; uncolored tail already in `_finish_response` |
| Sync/async `login` brackets | Color twins (`force_login` / `logout`; async via `sync_to_async`) |
| Unittest `self.query` + assertion helpers | `GraphQLTestMixin` delegates body/decode to `TestClient` |
| Engine `Response` field schema (`errors`/`data`/`extensions`) | `strawberry.test.client.Response`; package subclass adds raw `HttpResponse` |

Connected surfaces examined (evidence only; siblings not absorbed):

- `testing/__init__.py` — re-exports the client family; keeps Relay helpers on the
  dotted `testing.relay` path; `_wrap` is a separate concern.
- `testing/_wrap.py` — Trac #37064 wrap helper; no HTTP / body / multipart overlap.
- `testing/relay.py` — still-open sibling; GlobalID mint/decode only.
- `conf.testing_endpoint_setting` — thin settings reader; single consumer for the
  lowest endpoint rungs.
- Engine `strawberry.test.BaseGraphQLTestClient` — abstract `request`, `_decode`,
  base `_build_body` / folder-heuristic `_build_multipart_file_map` (deliberately
  shadowed: no `operationName`, empty map for nested input-object uploads).
- Upstream `strawberry_django.test.client` — same inheritance shape; uses inert
  `format="multipart"`; package drops that and owns path-keyed maps +
  `operation_name=` / `url=` / raw `response` on `Response`.
- Upstream `graphene_django.utils.testing` — mixin + `graphql_query` + assertion
  helpers; package keeps the mixin vocabulary but returns typed `Response` and
  routes through `TestClient` so body build exists once.
- `examples/fakeshop/graphql_client.py` — live-suite JSON path already goes
  through `TestClient`; `post_graphql_raw` is a documented raw-envelope
  exemption.
- Live / package tests: `tests/testing/test_client.py` (DB-free mechanics),
  `examples/fakeshop/test_query/test_client_api.py` and other `test_query/`
  suites that call `TestClient` / `AsyncTestClient` / `GraphQLTestCase`.

Item-scoped baseline
`git diff af358720f9215fc38990aab5b8d4d75415c57677 --
django_strawberry_framework/testing/client.py` is empty (and no other paths
were edited).

## Verification

Searches / checks on present source:

- Package-wide GraphQL HTTP posting: production body/decode for the test-client
  family lives only in this module. Example `post_graphql` delegates here.
  Remaining raw `client.post("/graphql/", ...)` sites are either (a) raw-envelope
  / arbitrary-label multipart exemptions documented in-suite, (b) view/middleware
  `RequestFactory` probes, or (c) resource-policy mounts that are not the
  shipped `/graphql/` client contract.
- Multipart `operations`/`map` construction in package code: only
  `TestClient._build_body`. Views own server-side control-field validation
  (`_MULTIPART_CONTROL_FIELDS`); that is parse/refuse policy, not a second
  test-client builder.
- Sync/async query twins: both call `_build_body` then `request` then
  `_finish_response`. Color is required at `await`; further extraction would
  need mode flags. Mirrors upstream strawberry-django's async re-implementation.
- Mixin vs pytest client: `GraphQLTestMixin.query` constructs
  `TestClient(self.GRAPHQL_URL, client=self.client)` — no parallel body builder.
  Flipped `assert_no_errors` defaults match distinct upstream flavors
  (strawberry-django vs graphene).
- `"operations"`/`"map"` string pair in client reserved-key guard vs
  `views._MULTIPART_CONTROL_FIELDS`: same wire-spec names, different
  responsibilities (clobber guard while building a test envelope vs server
  lossless-decode checks). Sharing a constant would couple `testing` to
  `views` (or invent a third module) for an external, stable GraphQL-multipart
  literal — rejected.
- `login` sync/async: intentional color split; logout-in-`finally` is the shared
  rule, expressed twice because context managers cannot share a body across
  sync/async without flags.

Scratch pytest: none (inspection + call-graph sufficient; no behavioral
ambiguity on ownership).

## Opportunities

None — body build, file-map rule, decode/`Response` assembly, and endpoint
settings read already have single owners; sync/async and mixin/pytest splits are
intentional dual surfaces over that owner; remaining raw multipart posts in
examples/tests are documented wire-shape exemptions, not a second production
builder.

### Strongest rejected candidates

1. **Further sync/async `query` / `login` unification** — uncolored work is
   already in `_build_body` / `_finish_response` / `request`. Remaining
   duplication is the await/color boundary; consolidating would add mode flags
   without a new shared rule.
2. **Share multipart control-field names with `views.py`** — wire-spec
   literals at independent boundaries (test builder vs server parse), not one
   package lifecycle that must change together.
3. **Fold example `_multipart` / raw `{operations,map,"0"}` posts into
   `TestClient`** — those suites pin arbitrary file-field labels or non-client
   mounts; comments name the raw-multipart exemption. The path-keyed client
   path is already earned live in `test_uploads_api` / `test_client_api`. Not
   this file's ownership gap; leave for a testing-folder pass only if a suite
   is still re-spelling the *path-keyed* contract by hand.

## Judgment

Zero-edit. Spec-043's "body building and decoding exist exactly once" contract
holds: mixin and async twin are thin surfaces over `TestClient`. No
consolidation is warranted at this owner.

## Implementation (Worker 1)

No tracked source changes. Item-scoped diff remains empty relative to
`af358720f9215fc38990aab5b8d4d75415c57677` for
`django_strawberry_framework/testing/client.py` and this artifact is the only
new path.

Deferred pytest: none required for a proved zero-edit; full suite stays at the
cycle gate.

Ready for Worker 2.

## Independent verification (Worker 2)

Re-traced present-day `testing/client.py` end to end: `TestClient._build_body` /
`_assert_file_placeholders` / `request` / `_finish_response` are the sole package
owners; `AsyncTestClient.query` / `login` and `GraphQLTestMixin.query` only
delegate (await/color and unittest `self.client` + flipped `assert_no_errors`
default). Endpoint ladder bottoms out at `conf.testing_endpoint_setting`.

Item-scoped check: `git diff af358720f9215fc38990aab5b8d4d75415c57677 --
django_strawberry_framework/testing/client.py` is empty (0 bytes; 539-line file
unchanged vs baseline).

Challenged rejected candidates with source evidence — all hold:

1. **Sync/async `query` / `login` merge** — both `query` colors already share
   `_build_body` → `request` → `_finish_response`; remaining split is the
   `await` / `asynccontextmanager` + `sync_to_async` color boundary. Further
   merge needs mode flags, not a missing shared rule.
2. **Share `"operations"`/`"map"` with `views._MULTIPART_CONTROL_FIELDS`** —
   views tuple is server-side lossless-decode policy
   (`_reject_lossy_multipart_control_fields`); client set is a builder clobber
   guard before `**files` spreads. Same wire-spec literals, independent
   boundaries; sharing would couple `testing` → `views` for a stable external
   name pair.
3. **Fold example raw multipart into `TestClient`** —
   `test_products_api` comments name the raw `{operations,map,"0"}` arbitrary-label
   exemption; `test_resource_policy_api._multipart` posts to `/rp-uploads/` with
   `(name, path)` tuples (not path-keyed `files=`). Path-keyed contract is already
   earned live in `test_uploads_api` / `test_client_api`. Not this file's gap.

Independent consolidation search (package + examples): no second production
body/decode owner. `graphql_client.post_graphql` routes through `TestClient`;
`post_graphql_raw` and transport-suite `_post_multipart` / `_multipart_bytes` are
documented wire-envelope / view-boundary probes. No missed consolidation at this
owner.

Outcome: verified. Plan checkbox marked.

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
