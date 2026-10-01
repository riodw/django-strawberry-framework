# Spec: Test client helper — `TestClient` / `AsyncTestClient` + the `GraphQLTestMixin` test-case family in `testing/client.py`, the package's live-HTTP test ergonomics

Built for `0.0.14` (card [`DONE-043-0.0.14`][kanban]). The package's
**consumer-facing GraphQL test client**:
`django_strawberry_framework/testing/client.py` exposes `TestClient` /
`AsyncTestClient` (thin wrappers over Django's `django.test.Client` /
`AsyncClient` that post GraphQL operations with the right content type, decode
the response, and return a typed `Response`) plus the unittest-flavored
`GraphQLTestMixin` and its two concrete combinations `GraphQLTestCase`
(`(Mixin, TestCase)`) and `GraphQLTransactionTestCase`
(`(Mixin, TransactionTestCase)`), and a project-wide endpoint settings key
(`TESTING_ENDPOINT` under `DJANGO_STRAWBERRY_FRAMEWORK`, Decision 7). It is a
Required **dual-upstream** parity item: 🍓
[`strawberry_django/test/client.py`][upstream-client] ships `TestClient` /
`AsyncTestClient` over Strawberry's
[`strawberry.test.BaseGraphQLTestClient`][venv-strawberry-test-client], and ⚛️
[`graphene_django/utils/testing.py`][upstream-testing] ships the
`graphql_query` function, `GraphQLTestMixin`, `GraphQLTestCase`, and
`GraphQLTransactionTestCase` with a `TESTING_ENDPOINT` settings knob
([`graphene_django/settings.py`][upstream-settings] `#"TESTING_ENDPOINT"`,
default `/graphql`). The package's own live acceptance tier
([`examples/fakeshop/test_query/`][test-query-readme]) is its largest consumer:
the shared JSON helpers in [`graphql_client.py`][graphql-client]
(`examples/fakeshop/graphql_client.py::post_graphql`) route through
`TestClient`, and live rows call the clients directly for typed results,
`login()` brackets, and multipart uploads.

The helper is deliberately **thin and engine-riding**. Strawberry's
`BaseGraphQLTestClient` (inside the package's **hard** `strawberry-graphql`
dependency — no [soft dependency][glossary-soft-dependency], no guard, no
install hint) is the engine-owned base for the response decode (`_decode`),
the typed-result field schema (`Response`), and the abstract `request()` seam.
The package subclasses it once, in the private generic base
`django_strawberry_framework/testing/client.py::_GraphQLTestClientBase`, which
owns everything both colors share: endpoint resolution, the Django-shaped
`request()` (JSON POST, multipart when `files=` is provided, a keyword-only
`url=` routing one call), the body/multipart builder (the base's cannot express
nested input-object uploads, Decision 9), and the decode-to-`Response` tail.
`TestClient` and `AsyncTestClient` are siblings over that base (Decision 8),
each owning its own `query()` (the signature and return type both differ from
the base's, Decision 5) and its `login()` context manager. The typed
`Response` carries the raw `HttpResponse` beside `data` / `errors` /
`extensions` (Decision 6), and the graphene-shaped unittest family delegates
to `TestClient` (Decision 10). `Upload`-scalar multipart mutations
([`DONE-037-0.0.11`][kanban], the card's declared dependency) drive through the
same `query(..., files=...)` call.

**Version boundary** (Decision 12): no slice of this card bumps the version;
the `0.0.14` release belonged to the [joint `0.0.14`
cut][glossary-joint-version-cut].

Status: **COMPLETE (card `DONE-043-0.0.14`) — all three slices built; the `0.0.14` version release rode the joint cut.**
Three slices: Slice 1 (the `TESTING_ENDPOINT` settings key,
`testing/client.py`, the `testing` root re-exports, the request-driving live
coverage, and the DB-free `tests/testing/test_client.py`), Slice 2 (the live
tier's ordinary GraphQL posts moved onto the client), and Slice 3 (docs + card
wrap).

Owner: package maintainer.

Predecessors: [`spec-042-debug_toolbar-0_0_14.md`][spec-042] (whose Risks named
`AsyncTestClient` the natural vehicle for the toolbar's async verification —
not adopted here, Decision 2);
[`spec-041-channels_router-0_0_14.md`][spec-041] (the Channels router; this
card's clients are not its transport); and
[`spec-037-upload_file_image_mapping-0_0_11.md`][spec-037] (the
[`Upload` scalar][glossary-upload-scalar] inputs the multipart path drives).
[`docs/GLOSSARY.md`][glossary] carries the shipped contract under
[`TestClient`][glossary-testclient] and
[`GraphQLTestCase`][glossary-graphqltestcase].

Rejected alternatives and the derivations behind each decision live in the
companion [`spec-043-test_client-0_0_14-rationale.md`][rationale]; this spec is
the contract.

## Key glossary references

Skim these [`docs/GLOSSARY.md`][glossary] entries first:

- [`TestClient`][glossary-testclient] — the subject: `TestClient` /
  `AsyncTestClient` and the typed `Response`, mirroring `strawberry-django`'s
  `test/client.py` shape.
- [`GraphQLTestCase`][glossary-graphqltestcase] — the unittest family whose
  name and mixin-first shape come from `graphene-django`'s `utils/testing.py`
  and whose HTTP client is the package `TestClient`.
- [`Upload` scalar][glossary-upload-scalar] — the multipart `files=` path
  exists so `Upload`-scalar mutations drive through the helper (Decision 9).
- [Live-first coverage mandate][glossary-live-first-coverage-mandate] — the
  rule Decision 11 applies: the request-driving coverage lives in the live
  tier; `tests/testing/test_client.py` covers only what a live request cannot
  pin (endpoint-resolution precedence against recording transports, the
  assertion helpers' failure directions, the owned builder's guards, the
  surface guards).
- [Schema reload discipline][glossary-schema-reload-discipline] — the live
  request-driving tests inherit [`test_query/conftest.py`][test-query-conftest]'s
  autouse reload through
  [`schema_reload.reload_all_project_schemas()`][schema-reload].
- [`seed_data`][glossary-seed-data] — every catalog test's first executable
  line is `seed_data(N)` / `create_users(N)` from `apps.products.services`.
- [Joint version cut][glossary-joint-version-cut] — why no slice here bumps
  the version (Decision 12).
- [Soft dependency][glossary-soft-dependency] — the **contrast**:
  `strawberry.test` ships inside the hard `strawberry-graphql` dependency and
  `django.test` inside Django, so there is no guard, no install hint, no
  [eviction-simulated absence][glossary-eviction-simulated-absence] fixture
  (Decision 5).
- [Auth mutations][glossary-auth-mutations] — session-mutating auth over
  Channels consumers is the auth / router surface's own, tested with Channels
  communicators; this card's clients wrap Django's HTTP test clients and do
  not drive it (Decision 2).
- [Debug-toolbar middleware][glossary-debug-toolbar-middleware] — its live
  suite posts through `TestClient`; its async-path smoke is not this card's
  (Decision 2).
- [`DjangoGraphQLProtocolRouter`][glossary-djangographqlprotocolrouter] — not
  this card's transport: `TestClient` wraps `django.test.Client`,
  `AsyncTestClient` wraps `django.test.AsyncClient` (Django's own in-process
  ASGI handler); neither is a Channels communicator.
- [`FieldError` envelope][glossary-fielderror-envelope] — mutation tests read
  `res.data["createItem"]["errors"]` through the same decoded `data` mapping,
  so the helper needs no envelope-specific surface.
- [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] — live tests
  assert query counts via `CaptureQueriesContext` around the HTTP call; the
  helper is transport only and adds no queries.
- [`ConfigurationError`][glossary-configurationerror] — not raised by this
  card: a malformed `DJANGO_STRAWBERRY_FRAMEWORK` dict already raises it
  through [`conf.py`][conf]'s shared reader, and the endpoint key adds no
  validation of its own ([Error shapes](#error-shapes)).

## Slice checklist

Each top-level item maps to one commit / PR.

- [ ] **Slice 1 — `TESTING_ENDPOINT` + `testing/client.py` + re-exports +
  live coverage + `tests/testing/test_client.py`**
  - [ ] No dependency change: `strawberry.test.BaseGraphQLTestClient` (and its
        `Response` dataclass) ships in the hard `strawberry-graphql`
        dependency at the floor the `strawberry-graphql>=` pin in
        [`pyproject.toml`][pyproject] declares (floor-run policy:
        [`docs/builder/BUILD.md`][build] `## Floor verification`).
  - [ ] [`django_strawberry_framework/conf.py`][conf] — the
        `TESTING_ENDPOINT_KEY = "TESTING_ENDPOINT"` constant and the
        `django_strawberry_framework/conf.py::testing_endpoint_setting`
        accessor defaulting to `"/graphql/"`, following the
        `django_strawberry_framework/conf.py::nested_connection_strategy_setting`
        precedent (key constant + thin accessor), with its own
        `__test__ = False` collection guard (Decision 7).
  - [ ] `django_strawberry_framework/testing/client.py` — the package
        `Response` dataclass (subclassing `strawberry.test.client.Response`,
        adding the raw `response`); the private
        `_GraphQLTestClientBase(BaseGraphQLTestClient, Generic[_ClientT])`
        with `__test__ = False`, the endpoint-resolving constructor, the
        `client` property, the Django-shaped `request(body, headers=None,
        files=None, *, url=None)`, the owned `_build_body` + path-keyed
        file-map builder + placeholder walker, and the shared
        `_finish_response` tail; `TestClient(_GraphQLTestClientBase[Client])`
        and `AsyncTestClient(_GraphQLTestClientBase[AsyncClient])`, each with
        `__init__(path=None, client=None)`, its own `query()` (adds
        `operation_name=` and a per-call `url=`, returns the package
        `Response`), and its own `login(user)` context manager;
        `GraphQLTestMixin` (class-attr `GRAPHQL_URL = None`, `.query(...)`
        delegating to a `TestClient` over the test case's own `self.client`,
        and the `assertResponseNoErrors` / `assertResponseHasErrors` helpers);
        `GraphQLTestCase(GraphQLTestMixin, TestCase)` and
        `GraphQLTransactionTestCase(GraphQLTestMixin, TransactionTestCase)`
        (Decisions 3–10).
  - [ ] [`django_strawberry_framework/testing/__init__.py`][testing-init] —
        re-export `TestClient`, `AsyncTestClient`, `Response`,
        `GraphQLTestMixin`, `GraphQLTestCase`, `GraphQLTransactionTestCase` in
        `__all__`; the `relay` submodule stays submodule-only, and nothing is
        re-exported from the **package root** (Decision 4).
  - [ ] Request-driving live coverage in
        [`examples/fakeshop/test_query/`][test-query-readme] — JSON happy path
        + typed `Response`, the errors outcome both directions,
        `operation_name` dispatch, `login()` scoping, the nested multipart
        upload, the async client, and the unittest family end to end
        (Decision 11, [Test plan](#test-plan)).
  - [ ] `tests/testing/test_client.py` — the **DB-free** package-tier tests
        for only what a live request cannot pin: endpoint-resolution
        precedence, both mixin assertion-helper FAILURE directions against
        canned responses, the owned builder's map rule and guards, the
        transport-selection contracts, and the collection guard + export
        surface (Decision 11).
  - [ ] Every new symbol carries its docstring (the [`docs/TREE.md`][tree]
        render fails on a missing module docstring).
- [ ] **Slice 2 — the live tier on the client**
  - [ ] Ordinary JSON posts under `examples/fakeshop/test_query/` go through
        `TestClient` — directly, or through
        [`graphql_client.py`][graphql-client]'s helpers, which route through
        it; file-local post wrappers that remain are thin wrappers over the
        client. Multipart uploads use `.query(..., files=...)`; authenticated
        flows use `.login(...)` or the wrapped `client`.
  - [ ] The documented exemption: a test whose **subject is the raw HTTP
        envelope** (an arbitrary-label multipart `operations` / `map`
        envelope, malformed bodies, content-type negotiation, GET) keeps its
        raw post with a comment naming the exemption;
        `examples/fakeshop/graphql_client.py::post_graphql_raw` is the shared
        raw-envelope helper (Decision 11).
  - [ ] Query-count assertions (`CaptureQueriesContext` blocks) unchanged —
        the helper is transport-only.
- [ ] **Slice 3 — docs + card wrap**
  - [ ] [`docs/GLOSSARY.md`][glossary] [`TestClient`][glossary-testclient] and
        [`GraphQLTestCase`][glossary-graphqltestcase] entry bodies describe the
        implemented contract (import path, endpoint resolution, the typed
        `Response` + raw-response field, multipart, login, async, the mixin
        family, the no-new-dependency posture) — DB edit + render, never a
        hand-edit.
  - [ ] [`docs/TREE.md`][tree] regenerated via
        [`scripts/build_tree_md.py`][build-tree-md]: the `testing/client.py`
        and `tests/testing/test_client.py` rows come from their module
        docstrings.
  - [ ] [`KANBAN.md`][kanban] card wrap: `043` → Done (kanban DB edit +
        [`scripts/build_kanban_md.py`][build-kanban-md] /
        `build_kanban_html.py` re-render).
  - [ ] The version bump, the GLOSSARY status flips to `shipped (0.0.14)`,
        the [`README.md`][readme] / [`docs/README.md`][docs-readme] moves, and
        `CHANGELOG.md` belong to the joint `0.0.14` cut, not this card
        (Decision 12).

## Problem statement

Testing a GraphQL endpoint over Django's test client is the same six lines
every time: build the `{"query": ..., "variables": ...}` envelope, `json.dumps`
it, POST it with `content_type="application/json"`, assert 200, decode the
body, and split `data` from `errors` — remembering that GraphQL returns **200
with an `errors` key** for most failures, so a status assertion alone proves
nothing. Multipart uploads are worse: the GraphQL multipart request spec's
`operations` / `map` envelope is fiddly to hand-build. Both reference
libraries ship exactly this helper — 🍓 `strawberry-graphql-django` as
`strawberry_django.test.client.TestClient` / `AsyncTestClient` (a thin wrapper
over `django.test.Client` returning a typed `Response`), ⚛️ `graphene-django`
as `graphene_django.utils.testing`'s `graphql_query` / `GraphQLTestMixin` /
`GraphQLTestCase` / `GraphQLTransactionTestCase` family (raw `HttpResponse` +
parsing assertion helpers, endpoint from a `TESTING_ENDPOINT` settings knob) —
so without it a consumer migrating from either upstream loses their test
ergonomics at the door, against [`GOAL.md`][goal] success criterion 7 (migrate
"without bringing the source package along"). The surface needs **no new
dependency** — the Strawberry engine already ships the base client — so the
design weight is in the two API decisions (the `.query()` return type;
base-class reuse vs. from-scratch), the endpoint settings key, and moving the
package's own live suites onto it without changing what any of them proves.

## Current state

The repo facts the design rests on:

- **The engine base is present, at a hard dependency.**
  [`strawberry/test/client.py`][venv-strawberry-test-client] defines
  `BaseGraphQLTestClient` — an ABC whose `__init__(client, url="/graphql/")`
  stores `self._client` / `self.url`, whose `query()` builds the body, calls
  the abstract `request()`, decodes, and returns the
  `Response(errors, data, extensions)` dataclass behind a bare-`assert`
  `assert_no_errors` gate — plus `_build_body`, the static
  `_build_multipart_file_map(variables, files)`, and `_decode` (multipart →
  `json.loads(response.content.decode())`, json → `response.json()`). **The
  base's `_build_body` / `_build_multipart_file_map` are insufficient for this
  repo:** the map builder treats any dict-valued variable as a single "folder"
  (keying off `next(iter(values.keys()))`) and drops any map entry whose key is
  not itself a `files` key, so it returns an **empty map** for fakeshop's
  nested `variables.data.attachment` / `variables.data.image` shape, and
  `_build_body` sends no `operationName` at all. The base's `query()` takes no
  `operation_name` / `url` and builds the base `Response` directly. `_decode`,
  the `Response` field schema, and the `request()` seam are what the package
  reuses (Decisions 5 and 9).
- **Async test infrastructure.** [`pytest.ini`][pytest-ini] sets
  `asyncio_mode = auto` and the dev group carries `pytest-asyncio`.
  `django.test.AsyncClient` drives Django's own `AsyncClientHandler`
  in-process, so `AsyncTestClient` runs against the WSGI-only fakeshop example
  (no `asgi.py`).
- **The endpoint is `/graphql/`.** Fakeshop's [`config/urls.py`][config-urls]
  mounts `graphql/`; Strawberry's base defaults its `url` to `"/graphql/"`;
  graphene defaults `TESTING_ENDPOINT` to `"/graphql"` (no trailing slash —
  against a slash-mounted endpoint a body-bearing POST never cleanly reaches
  the view under `APPEND_SLASH`: `RuntimeError` in `DEBUG`, a body-dropping 301
  otherwise).
- **[`conf.py`][conf]'s accessor shape.** Settings keys are module constants
  with thin accessor functions
  (`django_strawberry_framework/conf.py::nested_connection_strategy_setting`,
  `django_strawberry_framework/conf.py::upstream_patches_enabled`); the reader
  fails loud on a malformed non-mapping settings dict via
  `django_strawberry_framework/conf.py::_normalize_user_settings`, and a
  `setting_changed` receiver keeps reads fresh under `override_settings`.
- **The `testing/` subpackage holds three export postures.**
  [`testing/__init__.py`][testing-init] root-re-exports
  [`safe_wrap_connection_method`][glossary-safe-wrap-connection-method] and this
  card's family; the `relay` helpers are submodule-only.
- **The live tier shares one request module.**
  [`graphql_client.py`][graphql-client] single-sites the live JSON posts
  (through `TestClient`) and the raw-envelope post; the acceptance suites
  share the [schema-reload][glossary-schema-reload-discipline] autouse fixture
  through [`test_query/conftest.py`][test-query-conftest].

## Goals

1. **One import replaces the boilerplate.** A consumer posts a GraphQL
   operation, gets back a typed `Response(errors, data, extensions, response)`,
   and asserts on it — no `json.dumps`, no content-type string, no manual
   envelope split (Decision 6).
2. **Both upstream migration paths keep their shape.** A
   `strawberry-graphql-django` migrant's `TestClient("/graphql/")` /
   `client.query(...)` / `client.login(user)` calls work with the import line
   changed; a `graphene-django` migrant's `GraphQLTestCase` subclass keeps
   `self.query(...)`, `self.assertResponseNoErrors(...)`,
   `self.assertResponseHasErrors(...)`, and the `GRAPHQL_URL` /
   `TESTING_ENDPOINT` knobs — with three documented deltas
   ([Out of scope](#out-of-scope-explicitly-tracked-elsewhere)): `query()`
   returns the typed `Response` rather than a raw `HttpResponse`, graphene's
   `input_data=` convenience is not carried, and everything after `query` is
   keyword-only (graphene's positional `operation_name` becomes
   `operation_name=`) (Decisions 3 and 10).
3. **Multipart uploads ride the same call, including nested input objects.**
   `query(..., variables={"file": None}, files={"file": f})` for a top-level
   file, and `query(..., variables={"data": {"attachment": None, "image":
   None}}, files={"data.attachment": f1, "data.image": f2})` for a nested
   two-file input object — the path-keyed `files=` contract the owned builder
   makes possible, so [`Upload`-scalar][glossary-upload-scalar] mutations are
   one call (Decision 9).
4. **The endpoint is configurable once, project-wide, with overrides at every
   layer.** `DJANGO_STRAWBERRY_FRAMEWORK["TESTING_ENDPOINT"]` with
   per-instance (constructor `path=`), per-class (`GRAPHQL_URL`), and per-call
   (`url=`) overrides (Decision 7).
5. **The package's own live suites post through it**, each still proving
   exactly what it proves (query counts included) (Decision 11).
6. **Zero new dependencies.** The family imports only the package's hard
   dependencies (Decision 5).

## Non-goals

- **Channels / WebSocket test transport.** `TestClient` wraps
  `django.test.Client`; `AsyncTestClient` wraps `django.test.AsyncClient`.
  Neither drives a Channels communicator, so session-mutating
  [auth mutations][glossary-auth-mutations] through Channels consumers are not
  exercised by this family (Decision 2).
- **The debug-toolbar async smoke test.** The vehicle ships here; a toolbar
  async smoke would couple this card to a soft-dependency middleware it never
  imports (Decision 2).
- **A `mutate()` method.** Neither upstream ships one; a GraphQL mutation posts
  through `query()` like any operation, and the docstring says so.
- **graphene's `input_data=` convenience.** `graphql_query`'s `input_data`
  kwarg injects `variables["input"]` — graphene's Relay mutation convention
  (`$input`). The package's mutations take `data:` (and `id:`), so a migrant
  writes `variables={"input": ...}` explicitly
  ([Borrowing posture](#borrowing-posture)).
- **Fakeshop runtime changes.** The family needs no URLs, settings, or app
  changes in the example project.
- **Response-shape helpers beyond the envelope.** No assertion DSL, no
  snapshot helpers, no `FieldError`-envelope-specific accessors — `res.data`
  is a plain decoded mapping.
- **A package-root export.** The family stays under
  `django_strawberry_framework.testing` (Decision 4).

## Borrowing posture

Per the [`START.md`][start] "do both libraries provide it?" test this card is
**dual-upstream, foundational**: both reference libraries ship the surface,
and the borrow splits cleanly — the **client** shape comes from
`strawberry-graphql-django`, the **unittest family and settings knob** from
`graphene-django`.

### From `strawberry-graphql-django` — the client pair

[`strawberry_django/test/client.py`][upstream-client]:

- **`TestClient(BaseGraphQLTestClient)`** with `__test__ = False` (the pytest
  collection guard — the class name starts with `Test`), a
  `__init__(path, client=None)` storing `self.path` and defaulting the wrapped
  client to `django.test.Client()`, a `client` property over the base's
  `self._client`, and `request(body, headers=None, files=None)`: multipart
  kwargs when `files` is provided, else `content_type="application/json"`,
  posted to `self.path`.
- **`login(user)`** — a `contextlib.contextmanager` that `force_login`s the
  wrapped Django client, yields, and `logout()`s.
- **`AsyncTestClient(TestClient)`** — defaults the wrapped client to
  `django.test.AsyncClient`, **fully re-implements** `query()` as an
  `@override`-decorated `async def` (it does not call the base `query()`; the
  sync `request()` is reused via `cast("Awaitable", ...)`), and re-implements
  `login()` as an `asynccontextmanager` wrapping `force_login` / `logout` in
  `sync_to_async`.

Borrowed: the class names, `__test__ = False`, the `login` context managers,
`_decode`, the `Response` field schema, the `request()` ABC seam, and
`typing_extensions.override` on every overriding method (`typing-extensions`
is a hard dependency of the package). Owned outright: the sync **and** async
`query()` orchestration (the signature and return type both change, Decision
5) and the body/multipart-map build (Decision 9). The deltas from upstream's
concrete client: the two clients are **siblings over one private base**
rather than async-subclasses-sync (Decision 8); the constructor's `path`
becomes optional (endpoint resolution, Decision 7); the concrete `request()`
gains a keyword-only `url=` (default `self.path`) so `query()` can route a
single call without mutating stored state (Decision 7); `query()` gains
`operation_name=` and the per-call `url=` and returns the package `Response`
carrying the raw `HttpResponse` (Decision 6); the `files=` contract becomes
path-keyed for nested uploads; and upstream's inert `format="multipart"` extra
is dropped (Decision 9).

### From `graphene-django` — the unittest family and the settings knob

[`graphene_django/utils/testing.py`][upstream-testing]:

- **`graphql_query(...)`** — module-level function building the JSON envelope
  (`query`, optional `operationName`, optional `variables`, the `input_data`
  convenience) and posting it with `content_type="application/json"` to
  `graphql_url or graphene_settings.TESTING_ENDPOINT`.
- **`GraphQLTestMixin`** — class attribute `GRAPHQL_URL =
  graphene_settings.TESTING_ENDPOINT`, a `query(...)` method delegating to
  `graphql_query` with `client=self.client`, the deprecated `_client`
  property shim, and the two assertion helpers — `assertResponseNoErrors`
  (status 200 **and** no `errors` key) and `assertResponseHasErrors` (an
  `errors` key present; GraphQL returns status 200 even with errors).
- **`GraphQLTestCase(GraphQLTestMixin, TestCase)`** and
  **`GraphQLTransactionTestCase(GraphQLTestMixin, TransactionTestCase)`**.
- [`graphene_django/settings.py`][upstream-settings] `#"TESTING_ENDPOINT"` —
  the project-wide endpoint default (`"/graphql"`).

Borrowed: the mixin-first shape and all three class names, the assertion
helper names and their **semantics** (no-errors asserts HTTP 200 too; both
raise with the decoded content as the failure message), `operation_name`
support, and the settings-knob idea under the package's own dict. The mixin's
`query()` delegates to the package `TestClient` rather than a module-level
function, so the body-building logic exists once (Decision 10).

### Explicitly do not borrow

- **graphene's raw-`HttpResponse` return.** The typed dataclass wins, with the
  raw response carried as a field so nothing the raw flavor could do is lost
  (Decision 6).
- **graphene's `input_data=` kwarg** — the `$input` Relay-mutation convention
  is not this package's mutation shape ([Non-goals](#non-goals)).
- **graphene's `_client` deprecation shim** — legacy compatibility for
  graphene's own history.
- **graphene's module-level `graphql_query` function** — it would duplicate
  the client's body building; consumers who want a bare function instantiate
  `TestClient()` in a fixture (Decision 10).
- **upstream strawberry-django's `AsyncTestClient(TestClient)` inheritance** —
  the async client's `query()` / `login()` are coroutine-colored, so it is not
  substitutable for the sync client (Decision 8).
- **upstream strawberry-django's `format="multipart"` kwarg** — inert against
  Django's test client (the multipart behavior comes from omitting
  `content_type`); dropped, with the real mechanism documented (Decision 9).
- **graphene's `"/graphql"` default** — the package default is `"/graphql/"`
  (Decision 7).

The upstream source readings behind these choices are in the
[rationale][rationale-borrowing].

## User-facing API

The pytest-flavored client:

```python
from django_strawberry_framework.testing import TestClient

def test_items(db):
    client = TestClient()  # endpoint: DJANGO_STRAWBERRY_FRAMEWORK["TESTING_ENDPOINT"], default "/graphql/"
    res = client.query(
        "query Items($first: Int) { allItems(first: $first) { edges { node { name } } } }",
        variables={"first": 2},
    )
    assert res.errors is None          # already asserted by default (assert_no_errors=True)
    assert res.data["allItems"]["edges"]
    assert res.response.status_code == 200   # the raw django.http.HttpResponse rides along
```

Expecting errors, authenticated flows, and multipart uploads:

```python
res = client.query("{ nope }", assert_no_errors=False)
assert res.errors and res.errors[0]["message"]

with client.login(user):               # force_login / logout around the block
    res = client.query(CREATE_ITEM, variables={"data": {...}})

# Upload-scalar mutation — a nested input object with two file fields.
# Each files= key is the variable path the file binds to; variables carries
# a None placeholder at each path.
res = client.query(
    """
    mutation Create($data: MediaSpecimenInput!) {
      createMediaSpecimen(data: $data) {
        result { label attachment { name size } image { name width } }
        errors { field messages }
      }
    }
    """,
    variables={"data": {"label": "uploaded", "attachment": None, "image": None}},
    files={
        "data.attachment": SimpleUploadedFile("up.txt", b"hi"),
        "data.image": SimpleUploadedFile("up.png", png_bytes),
    },
    operation_name="Create",
)
assert res.data["createMediaSpecimen"]["errors"] == []
```

The async twin (Django's in-process ASGI handler — no `asgi.py` required):

```python
from django_strawberry_framework.testing import AsyncTestClient

async def test_items_async(db):
    client = AsyncTestClient()
    res = await client.query("{ allItems(first: 1) { edges { node { name } } } }")
    assert res.data["allItems"]["edges"]
```

The unittest family (graphene-django's shape):

```python
from django_strawberry_framework.testing import GraphQLTestCase

class ProductsTests(GraphQLTestCase):
    # GRAPHQL_URL = "/graphql/"        # optional per-class override of the settings key

    def test_items(self):
        res = self.query("query Items { allItems(first: 1) { edges { node { name } } } }",
                         operation_name="Items")
        self.assertResponseNoErrors(res)   # HTTP 200 AND res.errors is None

    def test_bad_selection(self):
        res = self.query("{ nope }")
        self.assertResponseHasErrors(res)
```

The project-wide endpoint knob, the overrides, and both migration diffs:

```python
# settings.py (only needed when the endpoint is not /graphql/)
DJANGO_STRAWBERRY_FRAMEWORK = {
    "TESTING_ENDPOINT": "/api/graphql/",
}
```

```python
# Overrides, highest precedence first: per-call > constructor > class attr > settings > default
res = client.query("{ __typename }", url="/other/graphql/")   # this one request only
client = TestClient("/api/graphql/")                          # this client instance
class MyTests(GraphQLTestCase):
    GRAPHQL_URL = "/api/graphql/"                             # this test-case class
```

```diff
- from strawberry_django.test.client import TestClient
+ from django_strawberry_framework.testing import TestClient
```

```diff
- from graphene_django.utils.testing import GraphQLTestCase
+ from django_strawberry_framework.testing import GraphQLTestCase
```

Consumer-visible behavior:

- **`query()` posts and decodes.** The body is `{"query": ...}` plus
  `variables` when non-empty and `operationName` when `operation_name` is not
  `None`; the POST carries `content_type="application/json"`; the return is
  the typed `Response(errors, data, extensions, response)`. With
  `assert_no_errors=True` (the default) a response carrying `errors` raises
  `AssertionError` immediately.
- **The mixin's `query()` is the same call routed through the test case's own
  `self.client`** (so `self.client.force_login(...)`, cookie state, and
  per-test-case client configuration all apply), returning the same typed
  `Response`; the graphene-named assertion helpers take that `Response`.
- **`files=` switches to multipart.** Each `files=` key is the variable path
  the file binds to (`"file"`, `"data.image"`, `"tags.0"`); `variables` holds a
  matching `None` placeholder at each path; the owned builder emits the
  `operations` / `map` fields by one uniform `map[key] = ["variables." + key]`
  rule (Decision 9).
- **`login(user)`** wraps the block in `force_login` / `logout` (sync context
  manager on `TestClient`, async on `AsyncTestClient`); the logout runs even
  when the block raises.
- **The raw Django client stays reachable** as `.client` for anything the
  helper does not wrap (session-cookie inspection, `enforce_csrf_checks`
  clients passed into the constructor); per-POST headers go through
  `headers=`.

### Error shapes

- **GraphQL errors under the default `assert_no_errors=True`** —
  `AssertionError` carrying the errors list. The engine base uses a bare
  `assert response.errors is None` and strawberry-django's async override
  `assert response.errors is None, response.errors`; the package owns both
  `query()` overrides (Decision 5) and raises explicitly in
  `django_strawberry_framework/testing/client.py::_GraphQLTestClientBase._finish_response`
  — `raise AssertionError(response.errors)` — so the failure survives
  `python -O`. Tests that *expect* errors pass `assert_no_errors=False` and
  assert on `res.errors`.
- **A non-JSON response body** (wrong endpoint → 404 HTML page, a
  misconfigured middleware returning HTML) — on the JSON path `_decode` calls
  Django's `response.json()`, which checks the `Content-Type` header **first**
  and raises **`ValueError`**
  (`'Content-Type header is "text/html", not "application/json"'`) — not
  `json.JSONDecodeError` ([`django/test/client.py`][django-client]
  `::ClientMixin._parse_json`). `json.JSONDecodeError` (a `ValueError`
  subclass) surfaces only when the header *is* JSON but the body is malformed,
  or on the multipart decode path (`json.loads(response.content.decode())`,
  which does not sniff the header). Deliberately **not** wrapped: the raise
  happens before the `Response` is built, the failing `HttpResponse` is a
  local of Django's `_parse_json` frame (the runner's traceback renders it
  with its status), and the captured `django.request` log names the path; the
  exception message itself names only the `Content-Type`. The `query()`
  docstring names the two usual causes (endpoint typo; `TESTING_ENDPOINT` not
  matching the project's URLconf). Pinned live on both colors
  ([Test plan](#test-plan) scenario 11).
- **A malformed `DJANGO_STRAWBERRY_FRAMEWORK` settings value** (non-mapping) —
  [`ConfigurationError`][glossary-configurationerror] from
  `django_strawberry_framework/conf.py::_normalize_user_settings`; the
  endpoint accessor adds no validation of its own. A wrong endpoint value of
  **any** type behaves alike — Django's test client coerces the path with
  `str()`, so a `None` posts to `/None` — surfacing as whatever the URLconf
  serves at that path, ordinarily a 404 (the previous bullet).
- **`files=` without usable `variables`** — the owned `_build_body` enters the
  multipart envelope on **truthiness** (`files={}` posts plain JSON) and then
  raises `AssertionError` when the envelope it just built carries **no
  `variables` member** for the `map` to point into
  (`if "variables" not in body`). Because the `variables` emission is itself
  truthiness, `variables={}` and `variables=None` are refused alike, as is any
  falsy mapping whatever it contains. The per-path placeholder contract is
  enforced separately by
  `django_strawberry_framework/testing/client.py::_GraphQLTestClientBase._assert_file_placeholders`
  (Decision 9).
- **Async misuse** — calling `AsyncTestClient.query(...)` without awaiting is
  the standard un-awaited-coroutine failure; the suite's `-W error` posture
  turns the `RuntimeWarning` into a loud failure. No package-specific guard.

## Architectural decisions

### Decision 1 — Spec filename and canonical naming

The stem is `spec-043-test_client-0_0_14`: card NNN `043`, topic slug
`test_client` (the card's subject), version segment `0_0_14` from the card's
trailing `-0.0.14`, per the [`docs/SPECS/NEXT.md`][next] convention.

Alternatives rejected: [rationale][rationale-d1].

### Decision 2 — Card-scope boundary: the test-client family ships; Channels session-auth verification, the toolbar's async smoke, and fakeshop runtime changes stay out

**In scope:** `testing/client.py` (the `TestClient` / `AsyncTestClient` /
`Response` / `GraphQLTestMixin` / `GraphQLTestCase` /
`GraphQLTransactionTestCase` surface), the `TESTING_ENDPOINT` settings key +
[`conf.py`][conf] accessor, the `testing` root re-exports,
`tests/testing/test_client.py`, and the live tier's move onto the client.

**Out of scope:**

- **Channels session-auth verification.** Session-mutating
  [auth mutations][glossary-auth-mutations] over Channels consumers need a
  communicator-based vehicle (`channels.testing.HttpCommunicator` /
  `WebsocketCommunicator`) with a soft-dependency posture (`channels` is soft;
  this family's dependencies are all hard). That verification belongs to the
  auth / router surface and lives with its communicator machinery in
  [`tests/test_routers.py`][test-routers] and
  [`tests/auth/test_mutations.py`][tests-auth-mutations].
- **The debug-toolbar async smoke.** The toolbar is a soft dependency this
  card's modules never import; an async smoke belongs in the toolbar's own
  test module, where its soft-dependency fixture lives.
- **Fakeshop runtime surface.** No settings, URL, or app changes.
- **Migration-guide prose.** The two import-diff rows and the three graphene
  deltas are handed to [`TODO-BETA-071-0.1.8`][kanban]
  ([Out of scope](#out-of-scope-explicitly-tracked-elsewhere)).

Alternatives rejected: [rationale][rationale-d2].

### Decision 3 — The symbols are upstream's own names — `TestClient` / `AsyncTestClient` / `GraphQLTestMixin` / `GraphQLTestCase` / `GraphQLTransactionTestCase`, distinctly-ours import path

All five public class names are taken verbatim from the upstream that ships
them: `TestClient` / `AsyncTestClient` from `strawberry_django.test.client`,
`GraphQLTestMixin` / `GraphQLTestCase` / `GraphQLTransactionTestCase` from
`graphene_django.utils.testing`. The distinguishing identity is the import
path — `django_strawberry_framework.testing` — so a migrant swaps only the
import line. For a `strawberry-graphql-django` client migrant that is the
entire change, [`GOAL.md`][goal] success criterion 7 in its most literal form;
a `graphene-django` mixin migrant swaps the same one import line and inherits
only the three documented behavioral deltas ([Goal 2](#goals)). `Response` is
likewise kept as the typed-result name (Strawberry core's own), re-exported so
consumers can annotate helpers.

None of the five carries the package's `Django*` prefix, and that is the rule:
the prefix marks **schema-side** public API
([`DjangoType`][glossary-djangotype],
[`DjangoConnectionField`][glossary-djangoconnectionfield]), while test
utilities are namespaced by their import path. A `DjangoTestClient` spelling is
out of contract.

The concrete test-case pair keeps graphene's `TestCase` /
`TransactionTestCase` split because that split is Django's own testing
vocabulary: consumers reach for the transaction flavor when the code under
test uses `transaction.on_commit` or needs real commits (the package's own
[`test_mutation_atomicity.py`][test-mutation-atomicity] concern).

Alternatives rejected: [rationale][rationale-d3].

### Decision 4 — Module, export, and test locations: `testing/client.py`, re-exported from the `testing` root, `tests/testing/test_client.py`

The module is `django_strawberry_framework/testing/client.py` — the mirror of
upstream's `test/client.py` under the package's `testing/` subpackage (named
`testing/`, not `test/`, because a top-level `test/` would shadow the Python
stdlib `test` package). The public import path is the `testing` **root**:
[`testing/__init__.py`][testing-init] re-exports `TestClient`,
`AsyncTestClient`, `Response`, `GraphQLTestMixin`, `GraphQLTestCase`, and
`GraphQLTransactionTestCase` in `__all__`.

The subpackage holds three locality postures:
`safe_wrap_connection_method` is root-re-exported, the `relay` helpers are
deliberately submodule-only (keeping their `types`-package imports out of
`import django_strawberry_framework.testing`), and this family is
root-re-exported. The import-weight argument that keeps `relay` out does not
bite here: the client module imports `django.test` and `strawberry.test`, both
already imported by any process running Django tests — the only process that
imports `testing` at all.

Tests are `tests/testing/test_client.py`, beside the subpackage's
`test_relay.py` / `test_wrap.py`.

Nothing is exported from the **package root**:
`getattr(django_strawberry_framework, "TestClient")` raises `AttributeError`
(the root's [`__getattr__`][init] PEP 562 seam), and the
`from django_strawberry_framework import TestClient` **statement form**
surfaces that as `ImportError` — Python's import machinery converts a module
`__getattr__`'s `AttributeError` into `ImportError` for `from ... import ...`.
The [Test plan](#test-plan) (scenario 14) pins both shapes. Both upstreams
make the same separation (`strawberry_django.test`,
`graphene_django.utils.testing`).

Alternatives rejected: [rationale][rationale-d4].

### Decision 5 — Subclass Strawberry's `BaseGraphQLTestClient` — engine-owned base over a hard dependency; no soft-dependency machinery

The card's second open item — subclass `strawberry.test.BaseGraphQLTestClient`
vs. roll an own base — resolves **for subclassing**, upstream
strawberry-django's own choice. The package subclasses it exactly once, in
the private generic base
`django_strawberry_framework/testing/client.py::_GraphQLTestClientBase`
(`BaseGraphQLTestClient, Generic[_ClientT]`, `_ClientT` bound to `Client` /
`AsyncClient`), which both public clients extend (Decision 8).

Three grounds:

1. **The base is engine-owned over a hard dependency.** `strawberry.test`
   ships inside `strawberry-graphql`, whose lower bound lives in
   [`pyproject.toml`][pyproject] and whose floor-run point is recorded in
   [`docs/builder/BUILD.md`][build] `## Floor verification` — so riding it
   costs no guard, no install hint, no
   [eviction-simulated absence][glossary-eviction-simulated-absence] fixture,
   and no lockfile change. The base is *designed* for subclassing: an ABC whose
   one abstract method is `request()`.
2. **The package owns the `query()` orchestration and the body/map build; the
   base owns the decode, the `Response` field schema, and the `request()`
   seam.** The base's `query()` takes no `operation_name` and no `url`, calls
   `request(body, headers, files)` with no target, and constructs the base
   `Response` directly, so a client that adds those keywords and returns the
   raw-response-carrying package `Response` owns its own `query()` in both
   colors (upstream already re-implements the async one). The base's
   `_build_multipart_file_map` returns an empty map for this repo's nested
   input-object uploads and its `_build_body` sends no `operationName`
   ([Current state](#current-state)), so the package owns `_build_body` and
   the path-keyed file map too (Decision 9). Subclassing still lets the package
   ride the engine's `_decode` and `Response` field schema rather than
   re-declaring those wire-format seams.
3. **Migration parity.** `.query()`'s first five positional parameters and
   `Response`'s field names stay byte-compatible with what a strawberry-django
   migrant's test suite already calls.

The `assert_no_errors` gate is package code, an explicit
`raise AssertionError(response.errors)` rather than a bare `assert`, so it
survives `python -O`; the `AssertionError` type and the errors-in-the-message
form match both upstreams.

Owning `query()` in both colors does **not** mean writing the flow twice. Only
the `request()` call is sync/async-colored, so the shared tail — `_decode` →
package `Response` construction → the `assert_no_errors` raise — is one
un-colored helper,
`django_strawberry_framework/testing/client.py::_GraphQLTestClientBase._finish_response`,
that both `query()` overrides call; the async color still owns its own
`await self.request(...)`.

The base constructor resolves the endpoint (Decision 7), stores it as
`self.path`, and forwards the same value to the engine base as its `url`, so
the inherited attribute never reads the base's default while `path` reads the
real endpoint. The `client=` seam is honored by identity, never by
truthiness: both clients select `client if client is not None else Client()` /
`AsyncClient()`, so a caller-supplied client whose `__bool__` / `__len__`
reports false is used as given rather than silently replaced by a fresh client
with a different session.

**No soft-dependency machinery:** no `require_*()` guard, no install-hint
constant, no [PEP 562 export][glossary-pep-562-lazy-export], no absence
tests — the [Test plan](#test-plan) has no absence matrix.

Alternatives rejected: [rationale][rationale-d5].

### Decision 6 — `.query()` returns the typed `Response` dataclass, extended with the raw `HttpResponse`; `operation_name=` is supported

The card's first open item — the typed `Response` dataclass
(strawberry-django) vs. the raw Django `HttpResponse` + parsing assertion
helpers (graphene-django), "pick one and pin it" — is **pinned to the typed
dataclass**, per the card's own recommendation, with one extension that makes
the pick total:

```python
@dataclass
class Response(strawberry.test.client.Response):   # errors / data / extensions
    response: Any = None   # the raw django.http.HttpResponse the operation rode
```

The `response` field is what lets every consumer of the raw flavor use the
typed one: the graphene mixin's `assertResponseNoErrors` asserts HTTP 200
(needs `status_code`); the package's own live suites assert session cookies,
response headers, and status codes around GraphQL calls (the
[`graphql_client.py`][graphql-client] helpers return `Response.response` for
exactly that). The typed shape is a strict superset of both upstream flavors:
`res.data` / `res.errors` / `res.extensions` for the strawberry-django
migrant, `res.response.<anything>` for the graphene migrant. The clients
always populate `response`; assert on fields, never on whole `Response`
objects.

`query()` is defined on `TestClient` (sync) and `AsyncTestClient` (async) with
two keyword-only extensions **after** the base's positional parameters
(`query, variables, headers, files, assert_no_errors`), so strawberry-django
migrants' positional calls keep working: **`operation_name=`** and a per-call
**`url=`** endpoint override (Decision 7). The Strawberry base cannot send
`operationName` at all; multi-operation documents need it. The body carries
`operationName` whenever `operation_name` is not `None` — the default `None`
omits the key (never an explicit `null`, a validation error against a
multi-operation document), and an explicit `""` is a *provided* value and is
sent, for the server to reject as malformed.

**No `mutate()`.** Neither upstream ships one. A mutation is an operation; it
posts through `query()`.

Alternatives rejected: [rationale][rationale-d6].

### Decision 7 — Endpoint resolution: the settings key is `TESTING_ENDPOINT`, default `"/graphql/"` — resolving the card's `GRAPHQL_TESTING_ENDPOINT` working name

The project-wide endpoint knob is
`DJANGO_STRAWBERRY_FRAMEWORK["TESTING_ENDPOINT"]`, read through
`django_strawberry_framework/conf.py::testing_endpoint_setting` (key constant
`TESTING_ENDPOINT_KEY`, default `"/graphql/"`) — the shape of
`django_strawberry_framework/conf.py::nested_connection_strategy_setting`. The
name carries no `GRAPHQL_` prefix: inside a settings dict named
`DJANGO_STRAWBERRY_FRAMEWORK` the prefix is redundant, and the unprefixed name
is byte-identical to graphene's own `TESTING_ENDPOINT` key.

The accessor carries the same pytest collection guard the client classes do:
[`conf.py`][conf] `#"testing_endpoint_setting.__test__ = False"`. Its name
matches pytest's default `test*` **function** pattern, so a test module
importing it unaliased gets it collected, and it returns a `str`, which fails
the run via `PytestReturnNotNoneWarning` under the repo's
`filterwarnings = error` posture.

Resolution precedence, highest first, uniform across the family:

1. **Per-call:** `query(..., url=...)` (on both clients and the mixin) —
   honored for that one request only and never persisted; `url=None`
   (default) falls through.
2. **Per-instance:** `TestClient(path=...)` / `AsyncTestClient(path=...)` —
   strawberry-django's `path` argument kept positional-first; `path=None`
   (default) falls through.
3. **Per-class (mixin family):** the `GRAPHQL_URL` class attribute (graphene's
   name), default `None` → falls through.
4. **Project-wide:** `testing_endpoint_setting()` →
   `DJANGO_STRAWBERRY_FRAMEWORK["TESTING_ENDPOINT"]`.
5. **Default:** `"/graphql/"` — fakeshop's real path, Strawberry core's own
   base default, trailing slash per Django convention.

The construction-time endpoint (rungs 2, 4, 5) is resolved **once** and stored
as `self.path`. The transport is explicit: the base's `request(body,
headers=None, files=None, *, url=None)` posts to `url` when given, else
`self.path`, and `query()` threads its per-call `url=` through for that single
call. `self.path` is **never mutated**, so a per-call override never persists
and concurrent or async calls cannot race on shared state. The mixin builds a
fresh delegate `TestClient(self.GRAPHQL_URL, client=self.client)` per
`query()` call, so rungs 3–5 resolve per call and a settings override observed
mid-class applies; [`conf.py`][conf]'s `setting_changed` receiver keeps the
accessor fresh under `override_settings`.

No validation beyond [`conf.py`][conf]'s malformed-dict guard. The value is
handed to Django's test client unchanged, which coerces the path with `str()`
— so a `reverse_lazy()` endpoint works and a `None` posts to `/None` — and a
wrong value of any type surfaces at request time as whatever the URLconf
serves at that path, ordinarily a 404 ([Error shapes](#error-shapes)). A type
gate would reject the lazy spelling Django accepts by design.

Alternatives rejected: [rationale][rationale-d7].

### Decision 8 — Async shape: `AsyncTestClient` is a sibling of `TestClient` over one shared base

`TestClient(_GraphQLTestClientBase[Client])` and
`AsyncTestClient(_GraphQLTestClientBase[AsyncClient])` are **siblings**, not
parent and child. The async `query()` and `login()` are coroutine-colored, so
an `AsyncTestClient` standing in for a `TestClient` would hand back an
un-awaited coroutine from `query()`; the is-a relationship upstream's
`AsyncTestClient(TestClient)` declares is false for the methods that matter,
and `isinstance(AsyncTestClient(), TestClient)` is `False` here.

Only the transport is colored. `request()` is written once on the base and
returns whatever the wrapped client's `post()` returns — an awaitable over
`AsyncClient` — typed per color by its two overloads, so the async `query()`
awaits it (upstream's `cast("Awaitable", ...)` becomes a plain `await`). The
endpoint resolution, `_build_body`, the file-map builder and placeholder
walker, the per-call `url=` routing, and `_finish_response` are the base's;
each client owns its `__init__` default transport (`Client()` /
`AsyncClient()`), its `query()`, and its `login()`. The async `login()` wraps
`force_login` / `logout` in `sync_to_async` (session writes are ORM work).

`AsyncClient` drives Django's `AsyncClientHandler` in-process, so the async
client works against the WSGI-only fakeshop example without an `asgi.py` —
which is what makes the [Test plan](#test-plan)'s async tests real requests.
It is **not** a Channels transport (Decision 2).

Alternatives rejected: [rationale][rationale-d8].

### Decision 9 — Multipart uploads: `files=` maps variable paths to file parts; the package owns the body/multipart builder; upstream's no-op `format` kwarg is dropped

When `files=` is provided, the owned `_build_body` produces the GraphQL
multipart request spec envelope — `operations` (the JSON-encoded
`{query, operationName?, variables}` body), `map` (the file-part →
variable-path mapping), plus the file parts — and `request()` posts it
**without** a `content_type` argument, so `django.test.Client.post` falls back
to its default `MULTIPART_CONTENT` encoding, which is what turns the dict into
a multipart body.

**The public `files=` contract: each key is the variable path the file binds
to.** A key `"data.attachment"` means "the file at
`variables.data.attachment`"; the builder emits a multipart part named
`"data.attachment"` and a `map` entry `{"data.attachment":
["variables.data.attachment"]}`. Every path is one uniform rule —
`map[key] = ["variables." + key]` — covering a top-level file (`"file"`), a
nested input-object field (`"data.image"`), and a list index (`"tags.0"`). The
caller carries a matching `None` placeholder at each path inside `variables`.

**The multipart envelope is entered on truthiness, and the placeholder
contract is enforced by a recursive walker.**
`django_strawberry_framework/testing/client.py::_GraphQLTestClientBase._build_body`
returns the plain JSON body when `files` is falsy — so `files={}` posts JSON —
and then raises when the built body carries no `variables` member for the
`map` to point into. The guard's subject is the envelope, not the argument:
the emission above it is the one owner of when that member exists. Under
truthiness emission that is every falsy `variables` — including a falsy
mapping carrying real placeholders, which the per-path walker alone would
accept while the `map` pointed into a member the envelope never wrote. Next,
`_build_body` refuses a `files` key named `operations` or `map` — the
envelope's own field names, which the trailing `**files` spread would
silently clobber — and then hands the call to
`django_strawberry_framework/testing/client.py::_GraphQLTestClientBase._assert_file_placeholders`,
which walks every dotted path and rejects at the source:

- an **empty dotted segment** (the `""` key's `variables.` path, or
  `variables.data.` for a `""` field) — such a map entry could never name a
  GraphQL variable;
- an **array index that is not its canonical non-negative decimal rendering**
  or is out of range, checked by a guarded `int()` conversion plus
  `index >= 0`, `str(index) == segment`, and `index < len(array)` — digit-like
  Unicode and very long decimal strings do not share `int()`'s acceptance
  domain, so an index the emitted `object-path` segment could not name is
  refused;
- an **array whose length cannot be read**, so a hostile `__len__` cannot
  replace the guard with a raw exception escape;
- a **missing key** at a mapping level;
- a **value that cannot be descended into** (neither array nor mapping);
- a **non-`None` value at the resolved path**.

The walk models the POST-serialization shape the map points into:
`json.dumps` renders dicts as JSON objects and **both lists and tuples** as
JSON arrays, so both array flavors carry indexed placeholders alike. Every
guard is an explicit `raise AssertionError` (not the base's bare
`assert variables is not None`), so all of them hold under `python -O` and
share one type for `pytest.raises(AssertionError)`. Every diagnostic renders
consumer-supplied paths and values through [`exceptions.py`][exceptions]
`::_safe_arg_repr` rather than `{x!r}`, so a hostile `__repr__` cannot escape a
guard as a raw exception (D5).

The builder is **owned, not inherited** (Decision 5 ground 2): with the path
explicit in the public contract it needs none of the base's folder-key
guessing. `operationName` is injected into the `operations` body **before**
JSON-encoding, so a named upload operation lands in the right field.

The `content_type` omission is a deliberate divergence from upstream's letter
while keeping its behavior: strawberry-django's `request()` sets
`kwargs["format"] = "multipart"` — a DRF-`APIClient`-shaped kwarg Django's test
client does not accept; it lands in `Client.post(...)`'s `**extra` as an inert
WSGI-environ entry, while the real multipart switch is the *omission* of
`content_type`. The package's `request()` keeps the real mechanism and drops
the inert kwarg, with a docstring note so a future diff against upstream does
not "fix" it back in (verified against
[`strawberry_django/test/client.py`][upstream-client] `::TestClient.request`
and Django's `Client.post` signature).

The live `Upload`-scalar mutations (fakeshop's `createMediaSpecimen`,
`updateMediaSpecimen`, `createMediaSpecimenImageViaForm`, the products
`updateItem` attachment path) drive through `query(..., files=...)` in
[`test_uploads_api.py`][test-uploads-api] and
[`test_products_api.py`][test-products-api], including the nested two-file
(`attachment` + `image`) shape. The wire-shape exemption (Decision 11) is
reserved for tests whose subject IS a hand-crafted envelope: the raw multipart
posts in [`test_products_api.py`][test-products-api] assert an arbitrary file
label, a wire shape the path-keyed builder never emits.

Alternatives rejected: [rationale][rationale-d9].

### Decision 10 — Mixin-first: `GraphQLTestMixin` composes over `TestClient`; the graphene assertion helpers keep their names, typed-Response-shaped

The reusable unittest piece is `GraphQLTestMixin` (graphene's convention:
consumers with their own custom TestCase base compose the mixin in directly);
`GraphQLTestCase` and `GraphQLTransactionTestCase` are the two-line concrete
combinations. The mixin's surface:

- **`GRAPHQL_URL = None`** — the per-class endpoint override (Decision 7).
- **`query(query, *, variables=None, operation_name=None, headers=None,
  files=None, url=None, assert_no_errors=False)`** — delegates to a
  `TestClient(self.GRAPHQL_URL, client=self.client)` built per call over the
  test case's **own `self.client`** (so `force_login`, cookies, and
  `enforce_csrf_checks` state on the case's client all apply), forwards the
  per-call `url=` to that client's `query()`, and returns the typed
  `Response`. The signature is keyword-only after `query`, so graphene's
  positional `operation_name` (its 2nd positional arg) becomes
  `operation_name=` — one uniform keyword signature across the pytest client
  and the mixin (graphene's positional order
  `(query, operation_name, input_data, variables, headers)` cannot survive
  dropping `input_data` intact anyway). The default is
  **`assert_no_errors=False` on the mixin** — graphene's mixin never
  auto-asserted, and its documented flow is "call `self.query(...)`, then
  `assertResponseNoErrors` / `assertResponseHasErrors`"; auto-raising inside
  `query()` would break every ported `assertResponseHasErrors` test at the
  call site. The pytest-flavored `TestClient` keeps the base's `True` default
  (strawberry-django parity); each flavor defaults to its own upstream's
  behavior, and both docstrings say so.
- **`assertResponseNoErrors(resp, msg=None)`** — asserts
  `resp.response.status_code == 200` **and** `resp.errors is None`, failing
  with `msg` or the decoded `{"errors": ..., "data": ...}` content, so a
  non-200 whose body has no `errors` key still fails readably.
- **`assertResponseHasErrors(resp, msg=None)`** — asserts `resp.errors` is
  non-empty, failing with `msg` or the decoded `data`; deliberately no status
  assertion (GraphQL returns 200 with errors).

The mixin is state-free beyond `GRAPHQL_URL` and reads only `self.client`; it
owns **no** body-building, decoding, or endpoint logic — that is the delegate
client's, so the logic exists once.

Alternatives rejected: [rationale][rationale-d10].

### Decision 11 — Test strategy: the live switchover is the primary coverage; `tests/testing/test_client.py` owns the rest

Per the [live-first mandate][glossary-live-first-coverage-mandate], the
helper's request-driving behaviour is covered **by being used** against real
fakeshop `/graphql/` requests: the live tier posts its ordinary operations
through `TestClient` (directly or via [`graphql_client.py`][graphql-client]),
and [`test_client_api.py`][test-client-api], [`test_products_api.py`][test-products-api],
and [`test_uploads_api.py`][test-uploads-api] carry the targeted rows — the
JSON happy path, both errors directions, `operation_name` dispatch, `login()`
in both colors, multipart in both colors, the non-JSON transport error in both
colors, and the unittest family end to end. The async request tests seed
through sync `transactional_db` fixtures (the executor-thread SQLite
visibility constraint) so no ORM work runs in the event loop.

`tests/testing/test_client.py` owns only what a live request cannot (or need
not) pin, and is **entirely DB-free** — no schema reload, no `seed_data`, no
real request:

- **Endpoint-resolution precedence** (per-call > constructor > class attr >
  settings key > default), proven against recording transports so a
  mis-resolved target cannot pass on a 404 body; the live tier proves the
  mixin rungs end-to-end against a probe URLconf besides.
- **Both mixin assertion helpers' FAILURE directions** against canned
  `Response` objects (their PASSING directions ride the live unittest tests).
- **The owned builder's map rule and its guards** — the uniform path-keyed
  rule (the top-level and list-index shapes no fakeshop mutation takes), the
  empty-`variables` guard, the placeholder walker's rejections, the
  reserved-envelope-key guard, `files={}` as a JSON post, and the
  `operation_name=""`-is-sent contract.
- **The transport-selection contracts and the surface guards** — an explicit
  falsy transport is kept, the async default is a `django.test.AsyncClient`,
  `__test__ = False`, and the export surface.

**The live-tier conversion rule.** A live test posts raw only when the raw
envelope is its subject (an arbitrary-label multipart `operations` / `map`
envelope, malformed bodies, content-type probes, GET); such a post carries a
comment naming the exemption, and a call that meets no exemption class goes
through the client. A conversion never weakens an assertion — the raw
`response` field exists so none needs to — and `CaptureQueriesContext` counts
are unchanged because the helper adds no queries.

No absence matrix, no eviction fixture, no hint tests — there is no optional
dependency (Decision 5).

Alternatives rejected: [rationale][rationale-d11].

### Decision 12 — Version bumps are owned by the joint `0.0.14` cut

No slice in this card edits the package-version state (`__version__` in
[`__init__.py`][init] and [`tests/base/test_init.py::test_version`][test-base-init]).
The card shared the `0.0.14` patch line with `DONE-041-0.0.14`,
`DONE-042-0.0.14`, and `DONE-044-0.0.14`; per [`docs/SPECS/NEXT.md`][next]
Step 3 / Step 6, when several cards target one patch version the bump, the
public `shipped (0.0.14)` status flips, the [`README.md`][readme] /
[`docs/README.md`][docs-readme] moves, and the `CHANGELOG.md` bullets belong
to the **[joint `0.0.14` cut][glossary-joint-version-cut]** (the last `0.0.14`
card to land), not any individual card. This card touches no lockfile either:
there is no dependency to add (Decision 5).

Alternatives rejected: [rationale][rationale-d12].

## Implementation plan

The file-level delta map (no slice bumps the version, Decision 12):

| File | Change | Slice |
| --- | --- | --- |
| [`django_strawberry_framework/conf.py`][conf] | `TESTING_ENDPOINT_KEY` constant + `testing_endpoint_setting()` accessor (default `"/graphql/"`, `__test__ = False`) (Decision 7) | 1 |
| `django_strawberry_framework/testing/client.py` | `Response` (typed + raw response); `_GraphQLTestClientBase` (endpoint resolution, `client` property, `request(..., *, url=None)`, owned `_build_body` + path-keyed map + placeholder walker, `_finish_response`); sibling `TestClient` / `AsyncTestClient` (own `__init__`, `query()`, `login()`); `GraphQLTestMixin` + `GraphQLTestCase` + `GraphQLTransactionTestCase` (Decisions 3–10) | 1 |
| [`django_strawberry_framework/testing/__init__.py`][testing-init] | Re-export the six public names in `__all__` (Decision 4) | 1 |
| `tests/testing/test_client.py` | The DB-free package-tier scenarios per the [Test plan](#test-plan) | 1 |
| `examples/fakeshop/test_query/` (targeted rows) | The request-driving live rows: [`test_client_api.py`][test-client-api] plus the `TestClient` rows in [`test_products_api.py`][test-products-api] and [`test_uploads_api.py`][test-uploads-api] | 1 |
| `examples/fakeshop/test_query/` (the rest) + [`graphql_client.py`][graphql-client] | Ordinary posts through the client; raw-envelope exemptions commented; query counts unchanged (Decision 11) | 2 |
| [`docs/GLOSSARY.md`][glossary] | [`TestClient`][glossary-testclient] + [`GraphQLTestCase`][glossary-graphqltestcase] entry bodies (DB edit + render) | 3 |
| [`docs/TREE.md`][tree] | Regenerated (script-rendered) | 3 |
| [`KANBAN.md`][kanban] / `KANBAN.html` | Card wrap via DB edit + re-render | 3 |

## Helper-reuse obligations (DRY)

Reuse is named per item, and deliberate *non*-reuse carries its reason.

- [ ] **D1** — the response decode, the `Response` field schema, and the
  `request()` ABC seam ride Strawberry's `BaseGraphQLTestClient` (`_decode`,
  the `Response` base, the abstract `request()`) — never re-implemented
  (Decision 5). The sync **and** async `query()` orchestration and the
  body/file-map build are the **owned** exceptions (D-N4).
- [ ] **D2** — the settings accessor follows the [`conf.py`][conf] key-constant
  + thin-accessor precedent
  (`django_strawberry_framework/conf.py::nested_connection_strategy_setting`)
  (Decision 7).
- [ ] **D3** — one body-builder, one decoder, one response tail: the two
  clients share them through `_GraphQLTestClientBase`, and the mixin delegates
  to `TestClient` (Decisions 8 and 10).
- [ ] **D4** — the live request-driving tests reuse the single-sited
  [`schema_reload.reload_all_project_schemas()`][schema-reload] (through the
  live tier's autouse fixture) and the [`seed_data`][glossary-seed-data] /
  `create_users` helpers — never private reloads or hand-built catalog rows
  (Decision 11).
- [ ] **D5** — every guard diagnostic in the owned builder and the placeholder
  walker renders consumer-supplied paths and values through
  [`exceptions.py`][exceptions] `::_safe_arg_repr`, never `{x!r}` — the
  package's hostile-metadata containment helper (Decision 9).
- [ ] **D-N1** (non-reuse) — the client does **not** route through
  [`request_from_info`][glossary-request-from-info]: that helper decodes
  resolver-context shapes server-side; this module *originates* HTTP requests
  from the test process.
- [ ] **D-N2** (non-reuse) — no shared "GraphQL post" helper is factored into
  `utils/`: the surface is consumer-facing test API under `testing/`, and no
  package runtime module may import test utilities.
- [ ] **D-N3** (non-reuse) — the async client does not reuse the
  `is_async_callable` construction-time detection from
  [`DjangoListField`][glossary-djangolistfield]: the caller picks the color by
  class here; detection exists for consumer-supplied callables whose color the
  package cannot know
  ([Decision 8](#decision-8--async-shape-asynctestclient-is-a-sibling-of-testclient-over-one-shared-base)).
- [ ] **D-N4** (non-reuse) — the body build and multipart file map do **not**
  reuse the base's `_build_body` / `_build_multipart_file_map`: the base's
  builder returns an empty map for nested input-object uploads and carries no
  `operationName` (Decisions 5 and 9).

## Edge cases and constraints

- **`__test__ = False` on the clients.** Without it, pytest collects any
  imported name matching `Test*` as a suite and emits
  `PytestCollectionWarning` — a hard failure under the repo's `-W error`
  posture. The guard sits on `_GraphQLTestClientBase`, so both `TestClient` and
  `AsyncTestClient` inherit it; the [Test plan](#test-plan) pins it (scenario
  13). The mixin family needs no guard (`GraphQL*` names do not match pytest's
  collection patterns).
- **`__test__ = False` on the settings accessor too** — the same hazard at
  function level ([`conf.py`][conf]
  `#"testing_endpoint_setting.__test__ = False"`, Decision 7).
- **CSRF.** `django.test.Client(enforce_csrf_checks=False)` is Django's
  default, so the helper posts without a token. A consumer testing CSRF
  enforcement passes `TestClient(client=Client(enforce_csrf_checks=True))` —
  the constructor's `client=` seam exists for exactly this.
- **Session state and cookies.** `login()` covers the force-login block and
  logs out even when the block raises, so a failing assertion inside it cannot
  leak session state; for cookie/session assertions the raw client rides
  along (`test_client.client.cookies`, and `res.response.cookies` per
  response).
- **`files=` requires placeholder variables.** `_build_body` raises when a
  truthy `files` arrives and the envelope carries no `variables` member, and
  `_GraphQLTestClientBase._assert_file_placeholders` enforces a `None`
  placeholder at each file's path (Decision 9). The `query()` docstring carries
  the single-file and nested-input-object examples.
- **Multi-file, nested-input-object, and list uploads** are handled by the
  owned path-keyed builder — `files={"data.attachment": f1, "data.image": f2}`
  for a nested input object, `files={"tags.0": f1, "tags.1": f2}` for a list —
  one uniform rule.
- **GET is not supported.** Both upstreams' helpers POST unconditionally;
  queries-via-GET stay on the raw client — one of the wire-shape exemptions.
- **`headers=` passes through** to Django's `Client.post(headers=...)`; the
  package's `Django>=` floor in [`pyproject.toml`][pyproject] has that
  parameter, so no `HTTP_`-prefixed-extra fallback is carried.
- **The raw-response field under multipart decode.** `_decode` reads
  `response.content` directly for multipart posts; `Response.response` carries
  the same `HttpResponse` either way, so status/header assertions are uniform
  across JSON and multipart calls.
- **`AsyncTestClient` + the ORM.** Async tests reaching the view mark
  `django_db(transaction=True)` (or seed through a `transactional_db` sync
  fixture) and rely on [`tests/conftest.py`][tests-conftest]'s async-connection
  hygiene, as every async DB test does.
- **`operationName` is omitted when `None`, never `null`** — a `null`
  `operationName` against a multi-operation document is a GraphQL validation
  error, and an absent key against a single anonymous operation is the
  spec-correct shape. An explicit `""` is sent (Decision 6).
- **`Response` equality / reprs.** The dataclass carries a live
  `HttpResponse`; reprs stay readable (dataclass default) and tests assert
  fields, never whole `Response` objects.
- **Mixin on a custom TestCase base.** The mixin reads only `self.client` and
  its own class attribute; composing it over a consumer's custom base works
  exactly as graphene documents.

## Test plan

The numbered scenarios split across two tiers per Decision 11. The live rows
run under the live tier's autouse schema reload and seed with `seed_data` /
`create_users`; every row in `tests/testing/test_client.py` is DB-free.

**Sync request shapes (live):**

1. **Happy path + typed `Response`.**
   `examples/fakeshop/test_query/test_products_api.py::test_operation_name_dispatch_via_test_client`'s
   named call doubles as the JSON happy path: `res.errors is None`, `res.data`
   carries edges, `res.response.status_code == 200` and
   `res.response["Content-Type"].startswith("application/json")`. The
   `extensions` leg (decoded value when present, `None` when absent) is
   package-tier, `::test_response_extensions_surface_decoded_or_none`, since
   fakeshop's live responses carry none.
2. **Errors, both directions.** The `assert_no_errors=False` outcome
   (`res.errors` non-empty, `res.data` `None`) rides the denied legs of
   `examples/fakeshop/test_query/test_products_api.py::test_create_item_login_bracket_via_test_client`;
   the raising direction (the default `assert_no_errors=True` raises
   `AssertionError` carrying the errors list on a real invalid selection) is
   `examples/fakeshop/test_query/test_client_api.py::test_assert_no_errors_default_raises_with_the_errors_list`.
3. **`operation_name` dispatch.** A two-operation document with
   `operation_name="ItemNames"` executes only the named second operation; the
   same document with **no** `operation_name` executes the *first* operation
   (Strawberry's HTTP layer defaults an absent `operationName` to it) —
   `::test_operation_name_dispatch_via_test_client`, proving the key is sent
   when given and absent when not. The explicit-`""`-is-sent contract is
   package-tier, `::test_build_body_sends_empty_operation_name_instead_of_dropping_it`.
4. **`login()` scoping.** A write-auth-gated `createItem`: denied anonymous,
   succeeds inside `with client.login(user_with_perm):`, denied again after the
   block, on one client instance —
   `::test_create_item_login_bracket_via_test_client`. The logout-on-raise leg
   is `examples/fakeshop/test_query/test_client_api.py::test_sync_login_bracket_logs_out_when_the_block_raises`.
5. **Multipart upload — nested input object, two files, with
   `operation_name`.** `createMediaSpecimen` through
   `query(mutation, variables={"data": {"label": ..., "attachment": None,
   "image": None}}, files={"data.attachment": ..., "data.image": ...},
   operation_name="Create")` → success payload, both files persisted —
   `examples/fakeshop/test_query/test_uploads_api.py::test_multipart_create_uploads_real_files_over_http`,
   the shape the base's map builder cannot produce, with `operationName` riding
   inside `operations`. The top-level and list-index shapes and the walker's
   success path are package-tier,
   `::test_build_body_map_rule_is_uniform_across_path_shapes`; `files={}` as a
   plain JSON post is `::test_empty_files_dict_is_a_plain_json_post`.

**Endpoint resolution (package-tier, DB-free):**

6. **Default.** `::test_default_endpoint_is_graphql_with_trailing_slash` —
   `TestClient().path == "/graphql/"` with no settings key.
7. **Settings key.**
   `::test_settings_key_sets_the_endpoint_and_the_default_restores_after_override`
   — under `override_settings(DJANGO_STRAWBERRY_FRAMEWORK={"TESTING_ENDPOINT":
   "/alt/"})` a fresh `TestClient` and `AsyncTestClient` both read `/alt/`, and
   after the override exits a fresh client is back on the default (the
   `setting_changed` receiver).
8. **Precedence ladder.** `::test_constructor_path_outranks_the_settings_key`
   (constructor > settings; the base's inherited `url` mirrors `path`) and
   `::test_per_call_url_outranks_the_constructor_and_never_persists` (a
   recording stand-in for the wrapped Django client records each `post`
   target: `/percall/` for the overridden call, `/constructor/` for the next,
   `self.path` unchanged). The stand-in replaces the **transport**, never
   `request()`, so the real `request()` selects the target the row reads. The
   mixin: `::test_mixin_query_delegates_to_the_test_cases_own_client` (posts
   through `self.client`, default rung) and one row per rung —
   `::test_mixin_class_attr_rung_beats_the_settings_key_and_the_default`,
   `::test_mixin_per_call_url_rung_beats_the_class_attr`,
   `::test_mixin_settings_rung_applies_when_the_class_attr_is_unset`.

**The async client (live, in [`test_client_api.py`][test-client-api]):**

9. **Async happy path + raise direction.**
   `::test_async_query_happy_path_and_raise_direction` — the scenario-1 typed
   assertions through the awaited transport, plus the async
   `assert_no_errors=True` raise.
10. **Async `login()`.** `::test_async_login_brackets_the_write_authorized_mutation`
    (the scenario-4 bracket through `async with client.login(user):`) and
    `::test_async_login_bracket_logs_out_when_the_block_raises`.

10b. **Async multipart upload.**
    `::test_async_multipart_upload_creates_media_specimen` — the scenario-5
    nested two-file upload through `AsyncTestClient` (superuser seeded in a
    sync `transactional_db` fixture, `MEDIA_ROOT=tmp_path`), the ASGI-scope
    multipart parse the sync path cannot exercise.

**The unittest family (live, in [`test_client_api.py`][test-client-api]) and
the transport error:**

11. **`GraphQLTestCase` end-to-end.** `GraphQLTestCaseEndToEndTests` — a seeded
    `self.query(...)` passes `assertResponseNoErrors`
    (`::test_seeded_query_via_self_client_passes_no_errors`); an invalid query
    returns rather than raising, then passes `assertResponseHasErrors`
    (`::test_invalid_query_returns_instead_of_raising_then_has_errors`); a
    per-call `self.query(..., url="/alt/")` reaches the alternate endpoint
    (`::test_per_call_url_routes_to_the_probe_endpoint`) — and
    `GraphQLTestCaseClassAttrEndpointTests::test_class_attr_endpoint_hits_the_real_view`
    pins the `GRAPHQL_URL = "/alt/"` rung. Both endpoint rows run against a
    **probe URLconf** that maps `"/alt/"` to the same schema view and stamps a
    marker response header the real `/graphql/` mount does not set, so a
    request that fell back to `/graphql/` cannot pass. The wrong-endpoint shape
    is pinned on both colors —
    `::test_wrong_configured_endpoint_surfaces_django_non_json_decode_error`
    and `::test_async_wrong_endpoint_surfaces_the_same_non_json_decode_error`
    — as Django's `ValueError` naming the non-JSON `Content-Type`
    ([Error shapes](#error-shapes)).
12. **Assertion-helper failure directions (package-tier) + the transaction
    smoke (live).** `tests/testing/test_client.py::AssertionHelperFailureDirectionTests`
    — `assertResponseNoErrors` fails on an errors response, fails readably on
    a non-200 without errors, and carries a custom `msg`;
    `assertResponseHasErrors` fails on a clean response and carries a custom
    `msg` — composed over `unittest.TestCase` against canned `Response`
    objects so the file stays DB-free.
    `GraphQLTransactionTestCaseSmokeTests::test_one_clean_seeded_query_round_trips`
    proves the second concrete combination is wired.

**Surface guards (package-tier, DB-free):**

13. **Collection guard.** `::test_clients_carry_the_pytest_collection_guard` —
    `TestClient.__test__ is False` and `AsyncTestClient.__test__ is False`.
14. **Export surface.**
    `::test_export_surface_is_the_testing_root_not_the_package_root` — the six
    names are in `django_strawberry_framework.testing.__all__`; the package
    root has none (`not hasattr(...)`, `pytest.raises(AttributeError)` around
    `getattr(...)`, and `pytest.raises(ImportError)` around the
    `from django_strawberry_framework import TestClient` statement)
    (Decision 4).

**The hardened builder and the transport selection (package-tier, DB-free):**

15. **Every rejection branch of the placeholder walker, plus the call-level
    guards and the selection contracts, carries its own named owner** in
    `tests/testing/test_client.py` (Decisions 5 and 9). The walker:

    - tuples walk like lists —
      `::test_files_placeholder_tuple_arrays_walk_and_map_like_lists`;
    - the empty dotted segment —
      `::test_files_placeholder_empty_segment_raises_instead_of_emitting`,
      parametrized over the `""`-key and trailing-dot shapes;
    - the non-canonical array index —
      `::test_files_placeholder_noncanonical_list_index_raises`, parametrized
      over the digit-like spellings `int()` and `str.isdigit()` disagree on,
      with `::test_files_placeholder_out_of_range_list_index_raises` for the
      range leg;
    - the unreadable array length —
      `::test_files_placeholder_hostile_len_container_fails_closed`,
      parametrized over `list` and `tuple`, asserting the uniform
      `AssertionError` and that the hostile exception's text does not escape;
    - the non-descendable value —
      `::test_files_placeholder_cannot_descend_into_a_scalar_raises`,
      including a case past the first segment;
    - the non-`None` value — `::test_files_placeholder_present_but_not_none_raises`;
    - the missing key — `::test_files_placeholder_missing_top_level_path_raises`
      / `::test_files_placeholder_missing_nested_key_raises`.

    The call-level guards, the diagnostics, and the selection contracts:

    - the empty-`variables` guard —
      `::test_files_without_variables_raises_the_placeholder_guard`,
      parametrized over `variables=None`, `variables={}`, and a **falsy `dict`
      subclass carrying real placeholders** (the input the walker alone would
      accept), plus `::test_async_files_without_variables_raises_the_same_guard`
      for the async color; each matches the guard's own phrase rather than a
      word every walker message carries;
    - the reserved-envelope-key guard —
      `::test_files_key_shadowing_a_reserved_envelope_field_raises`,
      parametrized over `operations`, `map`, and both (which also pins the
      sorted rendering of the offending names);
    - `_safe_arg_repr` containment of a hostile consumer `__repr__` on the
      placeholder value
      (`::test_files_placeholder_hostile_repr_keeps_assertion_error_boundary`)
      and on the `files=` key
      (`::test_files_placeholder_hostile_repr_key_keeps_assertion_error_boundary`);
    - the transport is selected by presence, not truthiness —
      `::test_clients_preserve_an_explicit_falsy_transport` (both colors),
      `::test_async_client_defaults_to_djangos_async_transport` (the async
      default arm is a `django.test.AsyncClient`, never the sync client), and
      `::test_async_client_posts_a_real_query_through_a_falsy_transport`
      (one awaited request through a `__bool__`-falsy and an empty-`__len__`
      transport).

    `_GraphQLTestClientBase._finish_response` has no row of its own: it sits on
    the only path either color's `query()` takes, so every request-driving row
    above exercises it in both colors.

Coverage: the package gate is `fail_under = 100` and `testing/client.py` is
package code. The live rows reach the JSON and multipart `request()`
branches, both `query()` overrides, `login()` in both colors, the mixin
delegate, and the assertion helpers' passing directions; the DB-free package
rows reach the builder's map rule and guards, the walker's rejection branches,
the selection contracts, both helpers' failure directions, the endpoint
ladder, and the export / guard surface.

## Doc updates

- [`docs/GLOSSARY.md`][glossary] — the [`TestClient`][glossary-testclient]
  entry body carries the implemented contract (the
  `django_strawberry_framework.testing` import path, the
  `BaseGraphQLTestClient` subclassing and zero-dependency posture, the typed
  `Response` + raw `response` field, endpoint resolution, `operation_name=`,
  multipart `files=`, `login()`, the async twin); the
  [`GraphQLTestCase`][glossary-graphqltestcase] entry body carries the
  mixin-first family, the flipped `assert_no_errors` default, the assertion
  helpers, and the `GRAPHQL_URL` rung. Both render from the glossary DB.
- [`docs/TREE.md`][tree] — regenerated via
  [`scripts/build_tree_md.py`][build-tree-md] from the module docstrings.
- [`KANBAN.md`][kanban] / `KANBAN.html` — card wrap via the DB + re-render.
- The release-status wording ([`README.md`][readme] /
  [`docs/README.md`][docs-readme], the GLOSSARY status lines, `CHANGELOG.md`)
  belongs to the joint `0.0.14` cut (Decision 12).

## Risks and open questions

The live constraints against the shipped contract; the preferred-answer /
fallback weighing is in the [rationale][rationale-risks].

- **Upstream reshapes the base later.** The subclass couples to `_decode`, the
  `Response` field names, and the `request()` seam — the same upstream-coupling
  class as every engine seam the package rides, milder here because `query()`
  and `Response` are documented public test API upstream. The body build is
  owned, so a reshape of `_build_body` / `_build_multipart_file_map` upstream
  cannot break the package. The request-driving tests fail loudly under a
  refreshed lock.
- **Async DB tests and async-connection hazards.** The `AsyncTestClient` rows
  follow [`tests/conftest.py`][tests-conftest]'s hygiene; a flake that surfaces
  is fixed at source in the shared conftest, never by weakening `-W error`.
- **The mixin's flipped `assert_no_errors=False` default.** Two defaults in one
  family is a documented asymmetry (Decision 10) and a foreseeable confusion
  source; each flavor matches its own upstream, which is what makes both
  migrations work unchanged, and both docstrings state the other's default.

## Out of scope (explicitly tracked elsewhere)

- **Channels session-auth verification** — the auth / router surface's own,
  with its communicator tests (Decision 2).
- **The debug-toolbar async smoke test** — the toolbar's own test module
  (Decision 2); this card ships the vehicle only.
- **The migration guide itself** — [`TODO-BETA-071-0.1.8`][kanban]; this card
  hands it two import-diff rows (`strawberry_django.test.client.TestClient` →
  `django_strawberry_framework.testing.TestClient`;
  `graphene_django.utils.testing.GraphQLTestCase` →
  `django_strawberry_framework.testing.GraphQLTestCase`) plus the three
  graphene deltas: (1) the mixin's `query()` returns the typed `Response`, not
  a raw `HttpResponse`; (2) graphene's `input_data=` kwarg is not carried —
  write `variables={"input": ...}`; (3) the mixin's `query()` is keyword-only
  after the query string, so graphene's positional `operation_name` becomes
  `operation_name=`.
- **The `0.0.14` version bump and release-status flips** — the joint `0.0.14`
  cut (Decision 12).

## Definition of done

- [ ] `django_strawberry_framework/testing/client.py` exists, with module +
      symbol docstrings, exposing `TestClient` / `AsyncTestClient` (siblings
      over `_GraphQLTestClientBase`, which subclasses
      `strawberry.test.BaseGraphQLTestClient` and carries `__test__ = False`,
      Decisions 5 and 8), the package `Response` carrying the raw
      `HttpResponse`, `login()` in both colors, `GraphQLTestMixin`, and the two
      concrete `(Mixin, TestCase)` / `(Mixin, TransactionTestCase)`
      combinations (Decisions 6 and 10).
- [ ] The mixin carries `assertResponseNoErrors` / `assertResponseHasErrors`
      typed for the `Response`.
- [ ] The endpoint settings key is live:
      `DJANGO_STRAWBERRY_FRAMEWORK["TESTING_ENDPOINT"]` (Decision 7), default
      `"/graphql/"`, with the constructor (`path=`), class-attribute
      (`GRAPHQL_URL`), and per-call (`url=`) rungs and the full precedence
      ladder tested.
- [ ] Multipart file upload works through `query(..., files=...)` on both
      clients — a live `Upload`-scalar mutation drives through the helper on
      the **sync** client ([`test_uploads_api.py`][test-uploads-api]) and the
      **async** client ([`test_client_api.py`][test-client-api]); the
      `variables`-placeholder contract is documented and enforced, and a
      `files=` key may not shadow the reserved `operations` / `map` fields.
- [ ] `from django_strawberry_framework.testing import TestClient,
      AsyncTestClient, Response, GraphQLTestMixin, GraphQLTestCase,
      GraphQLTransactionTestCase` all resolve; nothing is added to the package
      root (Decision 4).
- [ ] **No new dependencies**: the family imports only the package's hard
      dependencies; `strawberry.test.BaseGraphQLTestClient` is importable at
      the Strawberry floor the `strawberry-graphql>=` pin in
      [`pyproject.toml`][pyproject] declares.
- [ ] `tests/testing/test_client.py` covers the package-tier scenarios per the
      [Test plan](#test-plan), **entirely DB-free**; the request-driving
      scenarios are earned live; the package coverage gate
      (`fail_under = 100`) holds with `testing/client.py` included.
- [ ] The live tier posts its ordinary operations through the client; every
      raw post a live file retains carries the wire-shape-exemption comment
      naming the class it claims; assertions and `CaptureQueriesContext`
      counts are unchanged by the move (Decision 11).
- [ ] The migration-guide handoff rows are recorded for
      [`TODO-BETA-071-0.1.8`][kanban]
      ([Out of scope](#out-of-scope-explicitly-tracked-elsewhere)).
- [ ] Slice 3 doc updates land per [Doc updates](#doc-updates).
- [ ] **No slice bumps the version** — the joint `0.0.14` cut owns it
      (Decision 12).

<!-- LINK DEFINITIONS -->

<!-- Root -->
[goal]: ../../GOAL.md
[kanban]: ../../KANBAN.md
[pyproject]: ../../pyproject.toml
[pytest-ini]: ../../pytest.ini
[readme]: ../../README.md
[start]: ../../START.md

<!-- docs/ -->
[docs-readme]: ../README.md
[glossary]: ../GLOSSARY.md
[glossary-auth-mutations]: ../GLOSSARY.md#auth-mutations
[glossary-configurationerror]: ../GLOSSARY.md#configurationerror
[glossary-debug-toolbar-middleware]: ../GLOSSARY.md#debug-toolbar-middleware
[glossary-djangoconnectionfield]: ../GLOSSARY.md#djangoconnectionfield
[glossary-djangographqlprotocolrouter]: ../GLOSSARY.md#djangographqlprotocolrouter
[glossary-djangolistfield]: ../GLOSSARY.md#djangolistfield
[glossary-djangooptimizerextension]: ../GLOSSARY.md#djangooptimizerextension
[glossary-djangotype]: ../GLOSSARY.md#djangotype
[glossary-eviction-simulated-absence]: ../GLOSSARY.md#eviction-simulated-absence
[glossary-fielderror-envelope]: ../GLOSSARY.md#fielderror-envelope
[glossary-graphqltestcase]: ../GLOSSARY.md#graphqltestcase
[glossary-joint-version-cut]: ../GLOSSARY.md#joint-version-cut
[glossary-live-first-coverage-mandate]: ../GLOSSARY.md#live-first-coverage-mandate
[glossary-pep-562-lazy-export]: ../GLOSSARY.md#pep-562-lazy-export
[glossary-request-from-info]: ../GLOSSARY.md#request_from_info
[glossary-safe-wrap-connection-method]: ../GLOSSARY.md#safe_wrap_connection_method
[glossary-schema-reload-discipline]: ../GLOSSARY.md#schema-reload-discipline
[glossary-seed-data]: ../GLOSSARY.md#seed_data
[glossary-soft-dependency]: ../GLOSSARY.md#soft-dependency
[glossary-testclient]: ../GLOSSARY.md#testclient
[glossary-upload-scalar]: ../GLOSSARY.md#upload-scalar
[tree]: ../TREE.md

<!-- docs/SPECS/ -->
[next]: NEXT.md
[rationale-borrowing]: appx/spec-043-test_client-0_0_14-rationale.md#borrowing-posture--the-two-upstream-split
[rationale-d10]: appx/spec-043-test_client-0_0_14-rationale.md#decision-10--mixin-first-graphqltestmixin-composes-over-testclient
[rationale-d11]: appx/spec-043-test_client-0_0_14-rationale.md#decision-11--test-strategy-the-live-switchover-is-the-primary-coverage
[rationale-d12]: appx/spec-043-test_client-0_0_14-rationale.md#decision-12--version-bumps-are-owned-by-the-joint-0014-cut
[rationale-d1]: appx/spec-043-test_client-0_0_14-rationale.md#decision-1--spec-filename-and-canonical-naming
[rationale-d2]: appx/spec-043-test_client-0_0_14-rationale.md#decision-2--card-scope-boundary
[rationale-d3]: appx/spec-043-test_client-0_0_14-rationale.md#decision-3--the-symbols-are-upstreams-own-names
[rationale-d4]: appx/spec-043-test_client-0_0_14-rationale.md#decision-4--module-export-and-test-locations
[rationale-d5]: appx/spec-043-test_client-0_0_14-rationale.md#decision-5--subclass-strawberrys-basegraphqltestclient
[rationale-d6]: appx/spec-043-test_client-0_0_14-rationale.md#decision-6--query-returns-the-typed-response
[rationale-d7]: appx/spec-043-test_client-0_0_14-rationale.md#decision-7--endpoint-resolution-the-settings-key-is-testing_endpoint
[rationale-d8]: appx/spec-043-test_client-0_0_14-rationale.md#decision-8--async-shape-sibling-clients-over-one-shared-base
[rationale-d9]: appx/spec-043-test_client-0_0_14-rationale.md#decision-9--multipart-uploads-files-maps-variable-paths-to-file-parts
[rationale-risks]: appx/spec-043-test_client-0_0_14-rationale.md#risks-and-open-questions--the-preferred-answer--fallback-weighing
[rationale]: appx/spec-043-test_client-0_0_14-rationale.md
[spec-037]: spec-037-upload_file_image_mapping-0_0_11.md
[spec-041]: spec-041-channels_router-0_0_14.md
[spec-042]: spec-042-debug_toolbar-0_0_14.md

<!-- docs/builder/ -->
[build]: ../builder/BUILD.md

<!-- django_strawberry_framework/ -->
[conf]: ../../django_strawberry_framework/conf.py
[exceptions]: ../../django_strawberry_framework/exceptions.py
[init]: ../../django_strawberry_framework/__init__.py
[testing-init]: ../../django_strawberry_framework/testing/__init__.py

<!-- tests/ -->
[test-base-init]: ../../tests/base/test_init.py
[test-routers]: ../../tests/test_routers.py
[tests-auth-mutations]: ../../tests/auth/test_mutations.py
[tests-conftest]: ../../tests/conftest.py

<!-- examples/ -->
[config-urls]: ../../examples/fakeshop/config/urls.py
[graphql-client]: ../../examples/fakeshop/graphql_client.py
[schema-reload]: ../../examples/fakeshop/schema_reload.py
[test-client-api]: ../../examples/fakeshop/test_query/test_client_api.py
[test-mutation-atomicity]: ../../examples/fakeshop/test_query/test_mutation_atomicity.py
[test-products-api]: ../../examples/fakeshop/test_query/test_products_api.py
[test-query-conftest]: ../../examples/fakeshop/test_query/conftest.py
[test-query-readme]: ../../examples/fakeshop/test_query/README.md
[test-uploads-api]: ../../examples/fakeshop/test_query/test_uploads_api.py

<!-- scripts/ -->
[build-kanban-md]: ../../scripts/build_kanban_md.py
[build-tree-md]: ../../scripts/build_tree_md.py

<!-- .venv/ -->
[django-client]: ../../.venv/lib/python3.14/site-packages/django/test/client.py
[venv-strawberry-test-client]: ../../.venv/lib/python3.14/site-packages/strawberry/test/client.py

<!-- External -->
[upstream-client]: ../../../strawberry-django-main/strawberry_django/test/client.py
[upstream-settings]: ../../../django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/settings.py
[upstream-testing]: ../../../django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/utils/testing.py
