# Pre-BETA review: testing/

Scope: the consumer-facing GraphQL test-client family -- `client.py`
(`TestClient` / `AsyncTestClient` / `GraphQLTestMixin` / `GraphQLTestCase` /
`GraphQLTransactionTestCase`), `relay.py`, `_wrap.py`, `__init__.py`.

Method: full logic read of the real `client.py` (not in the stripped snapshot,
since the snapshot excludes paths containing `test`). Read-only; no tests run.

Bottom line: high-quality, defensively-written test ergonomics -- every
misconfiguration guard is an explicit `raise` (survives `python -O`), the
multipart contract is validated against the variables placeholders, and
`login()` logs out in `finally`. No P0/P1. Notes are documentation-level.

## P0 -- correctness suspicions

None found.

## P1 -- fix before BETA

None found.

## P2 -- polish / hardening

### `client.py` -- document the non-JSON transport-error shape
Confidence: low (already documented in the docstring; surface it in user docs).
When the endpoint is misconfigured (a `TESTING_ENDPOINT` that does not match the
URLconf, or a typo), the failure surfaces as Django's `response.json()` raising
`ValueError` naming the non-JSON content type of the 404/HTML body -- not a
wrapped framework error. That is a deliberate fail-at-the-source choice, but it
is the kind of thing that confuses first-time users; put the "endpoint typo ->
ValueError on decode" note in the testing docs, not only the docstring.

### `client.py::AsyncTestClient` -- the sync `request()` returning an awaitable is subtle
Confidence: low. `AsyncTestClient` reuses the sync `request()` (which returns
`self.client.post(...)`, an awaitable when the wrapped client is `AsyncClient`)
and awaits it in the async `query()`. This is correct and matches upstream, but
it is a sharp implicit contract: anyone adding a new code path that calls
`request()` on the async client without awaiting gets a silently-un-awaited
coroutine. A one-line comment at the `request()` seam noting "returns an
awaitable under AsyncTestClient" would prevent a future footgun.

## API & consistency notes

- The two flavors intentionally differ in `assert_no_errors` default
  (`TestClient` -> `True`, pytest-style; `GraphQLTestMixin.query` -> `False`,
  graphene-style). This is deliberate upstream parity but is a real trap for
  someone switching flavors -- keep it prominent in the docs.
- Endpoint precedence (per-call `url=` > constructor `path=` > class
  `GRAPHQL_URL` > `TESTING_ENDPOINT` setting > `/graphql/`) is a five-level
  chain. It is documented in the module docstring; make sure the public testing
  docs carry the same ordering so consumers do not guess.

## Verified sound (do not re-flag)

- All misconfiguration guards are explicit `raise AssertionError(...)` (not bare
  `assert`), so they hold under `python -O`: the empty-`variables` guard, the
  reserved multipart field-name guard (`operations`/`map`), and the
  per-path placeholder walk in `_assert_file_placeholders`.
- `login()` (sync and async) runs `logout()` in `finally`, so a failing
  assertion inside the block cannot leak session state into the next test.
- The multipart switch is the *omission* of `content_type` (so Django's test
  client falls back to `MULTIPART_CONTENT`), and the inert upstream
  `format="multipart"` kwarg is deliberately not carried -- do not "restore" it.
- `operationName` is sent only when `is not None`, so the default omits the key
  entirely (never `operationName: null`, which would be a validation error), and
  an explicit `""` is forwarded for the server to reject.
- `__test__ = False` prevents pytest from collecting `TestClient` as a suite
  (a hard failure under `-W error`).

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
