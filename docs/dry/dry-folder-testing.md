# DRY review: folder `django_strawberry_framework/testing/`

Status: verified

## System trace

`testing/` is the consumer-facing test surface (~847 lines, four modules).
It does not participate in schema bind or request handling; it helps
consumer suites drive live `/graphql/` HTTP, mint/assert Relay GlobalIDs,
and wrap Django connection methods without clobbering `_DatabaseFailure`.

Present-day folder as one component (fresh integration of current source,
not a recap of file artifacts):

| Role | Owner | Symbols |
| --- | --- | --- |
| Package surface | `__init__.py` | Re-exports client family + `safe_wrap_connection_method`; documents Relay helpers as dotted-submodule-only |
| HTTP client family | `client.py` | `Response`, `TestClient`, `AsyncTestClient`, `GraphQLTestMixin` / `GraphQLTestCase` / `GraphQLTransactionTestCase` |
| Cooperative DB wrap | `_wrap.py` | `safe_wrap_connection_method` (wrap-time half of Trac #37064 defense) |
| Relay GlobalID helpers | `relay.py` | `global_id_for` (mint); `decode_global_id` (re-export of production decode) |

Public import flavors (intentional, not competing):

- `from django_strawberry_framework.testing import …` — client family + wrap.
- `from django_strawberry_framework.testing.relay import …` — GlobalID helpers
  only. Keeps `import django_strawberry_framework.testing` free of
  `types`-package imports. Package root never re-exports this folder.

Connected evidence re-traced (not rewritten unless this folder owns the rule):

- `_django_patches.py` — unwrap-time `_patched_remove_databases_failures` +
  shared `_is_database_failure` predicate consumed by `_wrap.py`.
- `types/relay.py::encode_typename` / `decode_global_id` — production encode
  / decode; `global_id_for` calls encode; testing re-exports decode by
  identity.
- `types/base.py` — `STRING_GLOBALID_STRATEGIES`, `_RELAY_NODE_GATE_*`
  fragments shared with `global_id_for` gate messages.
- `conf.testing_endpoint_setting` — sole reader of
  `DJANGO_STRAWBERRY_FRAMEWORK["TESTING_ENDPOINT"]` (default `"/graphql/"`);
  `TestClient.__init__` is the only construction consumer.
- `views.py` — server multipart (`operations` / `map`); client builds the
  complementary envelope.
- Package `__init__.py` — no testing re-exports.
- Contract evidence: `tests/testing/` (`test_client` / `test_relay` /
  `test_wrap`); live `examples/fakeshop/test_query/test_client_api.py` and
  other `TestClient` consumers; package suites importing
  `testing.relay.global_id_for`.

Folder axes: policy split across modules; state ownership (endpoint ladder,
connection wrap restore); competing helper layers (pytest client vs unittest
mixin vs raw Django client; wrap vs unwrap); public flavor consistency
(init vs dotted relay); lifecycle work at several phases; vs production
encode/decode/HTTP when the same wire or GlobalID rule is split.

## Verification

- ITEM_BASELINE `31550ab942f3b74c48d274b0ce40cf2c36767868`:
  `git diff 31550ab9… -- django_strawberry_framework/testing/` empty at pass
  start and after this review. This pass creates only
  `docs/dry/dry-folder-testing.md`. Concurrent dirt outside the item left
  untouched. Plan checkbox not edited (Worker 2).
- Re-read all four modules end-to-end (~847 lines). Grepped package for
  `safe_wrap_connection_method` / `_is_database_failure`,
  `testing_endpoint_setting` / `TESTING_ENDPOINT` / `GRAPHQL_URL`,
  `_build_body` / `_finish_response` / `assert_no_errors`,
  `global_id_for` / `decode_global_id` / `encode_typename`, multipart
  `operations`/`map`, and consumer import paths.
- Did not seed findings from prior file DRY artifacts; used present-day
  source + connected production surfaces only.
- Confirmed endpoint ladder collapses to one construction path:
  `GraphQLTestMixin.query` builds `TestClient(self.GRAPHQL_URL, client=…)`;
  `path is None` falls through `testing_endpoint_setting()`; per-call
  `url=` never mutates stored `path`. Default `"/graphql/"` lives only in
  `conf.testing_endpoint_setting`.
- Confirmed body build / decode / `assert_no_errors` raise exist once in
  `TestClient` (`_build_body`, `_assert_file_placeholders`,
  `_finish_response`); mixin and async color delegate.
- Confirmed wrap/unwrap share `_is_database_failure`; wrap declines, unwrap
  hardens — complementary halves, not parallel predicates.
- Confirmed `testing.relay.decode_global_id is types.relay.decode_global_id`
  (identity re-export; permanent proof in `tests/testing/test_relay.py`).
- Confirmed `global_id_for` mints via `encode_typename` + `relay.GlobalID`
  after finalized / Relay-Node / string-strategy gates — no parallel mint
  policy inside the package.
- No production `.py` edit. No ruff run required for this item. No pytest
  (none deferred for a zero-edit pass).

## Opportunities

None — folder responsibilities are already partitioned by audience and
change axis; every cross-module candidate either shares a single owner
already or intentionally differs (see Judgment / rejected list).

## Judgment

`testing/` is three cooperating public seams under one package path, not
one lifecycle with duplicated phases:

1. **HTTP ergonomics** (`client.py`) — one body/decode owner; unittest mixin
   and async twin are flavor/color delegates, not second implementations.
2. **DB wrap hygiene** (`_wrap.py`) — consumer-facing wrap-time API over the
   package-internal unwrap patch; predicate already single-sited in
   `_django_patches`.
3. **Relay ID mint/assert** (`relay.py`) — thin test facade over production
   encode/decode; dotted import keeps the heavy `types` graph off the light
   testing import.

No folder-owned consolidation remains. Strongest rejects and out-of-remit
defers below are for Worker 2 challenge, not unfinished work.

### Strongest rejected candidates

1. **Merge pytest `TestClient` with unittest `GraphQLTestMixin` into one
   API.** Mixin already delegates body/decode to `TestClient`. Remaining
   differences are upstream flavor contracts: keyword-only graphene-shaped
   `query`, flipped `assert_no_errors` default (`False` vs `True`), and
   `assertResponseNoErrors` (HTTP 200 **and** no `errors`) vs the client's
   errors-only raise. Unifying would need mode flags and break both
   upstreams' documented flows. Reject.

2. **Collapse sync/async `query` / `login` into one helper.** Uncolored
   work already lives in `_build_body` / `_finish_response` / `request`.
   Remaining split is required `await` color (`AsyncClient.post`,
   `sync_to_async` around session writes). Further extraction obscures the
   color boundary. Reject.

3. **Re-export Relay helpers from `testing/__init__.py` (or fold `relay.py`
   into client).** Deliberate dual public path: dotted submodule keeps
   `types` imports off every `testing` import. `__init__` documents the
   helpers without exporting them. Collapsing would tax every client-only
   suite. Reject.

4. **Move `safe_wrap_connection_method` into `_django_patches` (or merge
   wrap+unwrap into one module).** Wrap is consumer-facing test
   instrumentation (public under `testing`); unwrap is unconditional
   `AppConfig.ready` hardening. Shared predicate already lives in the patch
   module. Merging would either expose private patch internals as the
   public import path or pull ready-time patch code into the test surface.
   Reject.

5. **Treat `assert_no_errors` raise and `assertResponseNoErrors` as one
   assertion policy.** Different contracts (errors-only vs status+errors);
   different default postures; graphene parity for the mixin. Reject.

6. **Share multipart `operations`/`map` vocabulary with `views.py` by
   importing views into the client (or hoisting into `testing/`).** Same
   external GraphQL-multipart field names appear as the client's reserved-key
   guard and views' `_MULTIPART_CONTROL_FIELDS`. True owner is the wire /
   server side (or a neutral package constant), not this folder. Coupling
   `testing` → `views` is the wrong direction; hoisting into `testing/`
   would make production import a test package. Defer to project pass if a
   neutral shared constant is worth the churn for a stable external spec.
   Not this folder's remit.

7. **Force example/package tests that hand-roll `relay.GlobalID(...)` onto
   `global_id_for`.** Many sites intentionally mint malformed, wrong-type,
   or fixed-label ids. Strategy-aware minting already has one package owner
   (`testing.relay.global_id_for` → `encode_typename`). Sweeping call sites
   is project/test-hygiene, not a folder-internal duplicate implementation.
   Defer.

### Deferred (out of folder remit)

- Neutral multipart control-field constant (`operations` / `map`) shared by
  `views.py` and `testing/client.py` — project pass.
- Broader adoption of `global_id_for` in examples/tests that currently
  hardcode model-label GlobalIDs — project / test-placement hygiene.
- Docstring framing in `__init__.py` lists Relay helpers under "Currently
  exports" while clarifying they are not re-exported — editorial only;
  behavior and `__all__` already match the dotted-submodule contract.

### Implementation (Worker 1)

Zero-edit proved. No production migration, no permanent-test delta, no
changelog candidate. Artifact created at
`docs/dry/dry-folder-testing.md`.

Item-scoped diff statement:

```text
git diff 31550ab942f3b74c48d274b0ce40cf2c36767868 -- \
  django_strawberry_framework/testing/ docs/dry/dry-folder-testing.md
```

→ only the new artifact (testing/ tree unchanged vs ITEM_BASELINE).

Ready for Worker 2 independent verification.

## Independent verification (Worker 2)

Verified zero-edit. Independently re-read all four modules, confirmed
`git diff 31550ab942f3b74c48d274b0ce40cf2c36767868 -- django_strawberry_framework/testing/`
empty, and re-traced folder seams against production neighbors and
consumers without seeding from file-level DRY artifacts.

### Baseline and surface

- Item-scoped `testing/` tree unchanged vs ITEM_BASELINE.
- Package `__init__.py` does not re-export `testing` (grep empty).
- `testing/__init__.__all__` is client family + `safe_wrap_connection_method`
  only; `global_id_for` / `decode_global_id` absent from `__all__`.
- Runtime check: `testing.relay.decode_global_id is types.relay.decode_global_id`
  (`True`); permanent proof already in `tests/testing/test_relay.py`.

### Seam re-trace (folder as one component)

1. **HTTP** — `TestClient` owns `_build_body` / `_assert_file_placeholders` /
   `_finish_response` / `request`. `AsyncTestClient.query` / `login` are
   color-only. `GraphQLTestMixin.query` constructs `TestClient(self.GRAPHQL_URL,
   client=self.client)` and delegates; endpoint ladder collapses to
   `TestClient.__init__` → `testing_endpoint_setting()` when `path`/`GRAPHQL_URL`
   is `None`. Default `"/graphql/"` lives only in `conf.testing_endpoint_setting`.
2. **Wrap** — `_wrap.safe_wrap_connection_method` declines via
   `_django_patches._is_database_failure`; unwrap-time
   `_patched_remove_databases_failures` uses the same predicate. Complementary
   halves, one owner of the isinstance rule.
3. **Relay** — `global_id_for` mints through production `encode_typename` +
   `relay.GlobalID` after finalize / Node / string-strategy gates; decode is
   identity re-export. Gate fragments / `STRING_GLOBALID_STRATEGIES` already
   single-sited in `types/base.py`.

### Rejected candidates challenged

1. **Merge `TestClient` + `GraphQLTestMixin`.** Mixin already delegates body/
   decode. Remaining differences are upstream flavor: keyword-only `query`,
   `assert_no_errors` default `False` vs `True`, and `assertResponseNoErrors`
   (HTTP 200 **and** `errors is None`) vs client's errors-only raise. Both
   flavors are live-exercised (`examples/fakeshop/test_query/test_client_api.py`).
   Unifying needs mode flags. Reject stands.

2. **Collapse sync/async `query` / `login`.** Shared uncolored work already in
   `_build_body` / `_finish_response`. Remaining split is required `await`
   (`AsyncClient.post`, `sync_to_async` session writes). Reject stands.

3. **Re-export Relay from `testing/__init__`.** `relay.py` pulls `types.base` /
   `types.relay`; dotted path keeps that graph off client-only imports.
   `__init__` documents without exporting; `__all__` matches. Reject stands.

4. **Merge wrap into `_django_patches`.** Public consumer wrap API under
   `testing` vs unconditional `AppConfig.ready` unwrap hardening. Shared
   predicate already single-sited. Merging would either expose patch internals
   as the public path or drag ready-time patch code into the test surface.
   Reject stands.

5. **Unify `assert_no_errors` raise with `assertResponseNoErrors`.** Different
   contracts (errors-only vs status+errors) and default postures; graphene
   parity for the mixin. Reject stands.

6. **Share multipart `operations`/`map` with `views.py` inside this folder.**
   Client reserved-key guard `{"operations", "map"}` vs views
   `_MULTIPART_CONTROL_FIELDS = ("operations", "map")` — same external wire
   names, opposite sides of the envelope. True owner is wire/server (or a
   neutral package constant). `testing` → `views` is wrong direction; hoisting
   into `testing/` would make production import a test package. Defer to
   project pass stands — not a folder-owned consolidation.

7. **Force hand-rolled `relay.GlobalID(...)` onto `global_id_for`.** Many
   call sites intentionally mint wrong-type, empty, or fixed-label ids
   (e.g. `tests/test_relay_node_field.py`, `examples/fakeshop/test_query/test_products_api.py`).
   Strategy-aware mint already has one package owner. Sweep is project/test
   hygiene. Defer stands.

### Missed consolidations searched

- Competing Response / body-build / endpoint readers outside `client.py` +
  `conf.testing_endpoint_setting`: none in package source.
- Parallel `_DatabaseFailure` predicates: only `_is_database_failure`.
- Parallel GlobalID mint policy inside the package: none beyond
  `global_id_for` → `encode_typename`.
- Example helper `examples/fakeshop/graphql_client.py` routes JSON posts
  through `TestClient` and keeps raw posts as a deliberate exemption — not a
  second package body-builder.
- Editorial docstring "Currently exports" listing Relay helpers while not
  re-exporting them: behavior/`__all__` already correct; not a consolidation.

No folder-owned consolidation remains. Plan checkbox marked `[x]`.
