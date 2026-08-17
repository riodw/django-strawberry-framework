# Review: `django_strawberry_framework/views.py`

Status: verified

## Understanding

`views.py` owns the package's Django HTTP GraphQL mounts: `DjangoGraphQLView` and
`AsyncDjangoGraphQLView`. They subclass Strawberry's sync/async Django views and preserve
the upstream schema, IDE, GET, multipart, context, root-value, result, and response hooks.
The shared `_RequestBodyBoundaryMixin` owns the package-specific request boundary:
per-mount/settings/default cap resolution, pre-parse body measurement, strict UTF-8 JSON
decoding, multipart control-field encoding/loss detection, and the CSRF ordering protocol.

The sync view's `_RawBodyRequestAdapter` is the one deliberate transport asymmetry. It
returns raw bytes so `parse_json` owns strict decoding even when the optional upstream
patches are disabled; the async upstream adapter already returns bytes. Both concrete
views enforce the boundary before the inherited Strawberry `run`, then use Django's
`csrf_protect` continuation. The callback's withdrawable CSRF mark and the
`GraphQLRequestBodyBoundaryMiddleware` / `_boundary_ordering.py` protocol ensure the
configured CSRF middleware can run behind the boundary when installed, while the
view-local fallback remains protected when it is absent.

The body-cap path delegates private request-stream measurement to
`django_strawberry_framework/_request_body.py::body_exceeds_limit`. Multipart framing,
upload handlers, and parser limits remain Django-owned. Schema execution, context,
resource/error policy, debug extensions, response headers, cache behavior, host checks,
and routing remain inherited or supplied by Django and Strawberry; live fakeshop mounts
exercise those integration boundaries.

The scoped comparison `git --no-pager diff 40445021bde4b5116f97cb22f90046f9c4a2176d --
django_strawberry_framework/views.py` is empty. The target and its connected tests are
dirty relative to `HEAD` from earlier verified work, but no concurrent changes were
adopted or reverted.

## Verification

- Read the complete target and connected `_request_body.py`, `_boundary_ordering.py`,
  `middleware/request_body.py`, `conf.py`, Strawberry sync/async HTTP base views,
  cross-web Django adapters, fakeshop URL/settings, package tests, live transport tests,
  transport specification, and deployment documentation.
- `uv run pytest tests/test_views.py --no-cov -q -n0` — 219 passed.
- `uv run pytest examples/fakeshop/test_query/test_transport_api.py --no-cov -q -n0` —
  77 passed.
- Disposable probe `docs/review/temp-tests/views/probe_views.py` executed method scope,
  codec aliases/string subclasses, and HEAD/OPTIONS declared-length behavior:
  over-limit PUT → `413`, non-UTF-8 PUT declaration → the shared controlled `400`,
  hostile charset subclasses resolved through `codecs.lookup`, and hostile declared
  lengths on HEAD/OPTIONS → `413`. These outcomes match the documented boundary
  ordering and method scope.
- A live malformed-multipart experiment with missing/empty/oversized boundaries
  produced Django's handled `400 Bad Request`; no parser exception escaped as a view
  `500`.
- Upstream source inspection confirmed the package delegates schema execution,
  multipart framing, response construction, and sync/async streaming to the installed
  Strawberry implementation, while the package overrides only the documented boundary
  seams.

## Improvements

### High

None.

### Medium

None.

### Low

None.

### Rejected findings

- **Unsupported methods should bypass the cap and always return `405`.** Rejected:
  the transport specification explicitly scopes only the multipart carve-out to POST
  and requires a multipart body on other methods to take the counted path. The
  boundary therefore runs before Strawberry's method check and an over-limit
  non-GET/POST body correctly receives the package's `413`; a body within the cap
  reaches upstream's `405`.
- **A malformed multipart boundary should be translated by `parse_multipart`.**
  Rejected: Django's `HttpRequest._load_post_and_files` raises
  `MultiPartParserError`, and Django's exception handler converts it to the handled
  `400` before Strawberry's adapter can proceed. Adding a private parser catch in
  this view would duplicate Django's ownership.
- **The body cap should count multipart bytes when `Content-Length` is absent or
  understated.** Rejected: the declared multipart gate plus Django's parser/upload
  settings is the explicit contract; reading multipart bodies here would defeat
  streaming upload handlers and the shipped `Upload` path.
- **The view should translate an already-consumed uncached request stream into `413`.**
  Rejected: `_request_body.py::body_exceeds_limit` deliberately defers when
  `_read_started` is true without `_body`, preserving Django's `RawPostDataException`
  semantics rather than mislabeling another middleware's consumed stream as a body-limit
  refusal. The documented ordering limitation belongs to the surrounding middleware
  stack, not this view.
- **CSRF should not be re-entered when the global middleware is missing or a callback
  wrapper loses the marker.** Rejected: the package-owned `csrf_protect` continuation
  is unconditional, and the live CSRF matrix proves missing/wrong tokens still return
  `403` while valid tokens succeed on both transports.
- **A wrapper that preserves the private boundary marker but drops its mount token should
  be treated as a package mount.** Rejected: the marker and mount token are private
  callback protocol attributes; supported Django decorators copy the callback
  dictionary (including both), while the documented hand-written-wrapper fallback
  deliberately drops the marker and stays on the view-local arrangement. A synthetic
  marker-only wrapper does cause duplicate setup, but it is a forged/incoherent
  callback outside the supported protocol; making the mount token mandatory would
  weaken the existing marker-probe isolation tests without improving a supported
  deployment.
- **The inherited resource/error/debug extension behavior needs a view-specific
  reimplementation.** Rejected: Strawberry's `run`, `process_result`, streaming
  response, and context seams remain the execution owners; fakeshop live tests exercise
  real HTTP responses and the package's extension suites exercise the schema policies.

## Summary

The current `views.py` implementation is coherent and complete for its ownership:
both transports preserve upstream behavior while enforcing the package cap, strict
UTF-8/BOM contract, multipart loss guard, and CSRF ordering without depending on the
upstream-patch switch. The connected middleware and private stream helper provide the
remaining lifecycle guarantees, and the focused package/live tests plus disposable
experiments found no accepted root-cause defect.

## Implementation (Worker 1)

None — zero-edit cycle.

Changed files: only this review artifact was created. `views.py`, its permanent tests,
settings, middleware, and connected source remain unchanged relative to the scoped
baseline. No production finding required a permanent test.

Permanent tests and focused verification: existing package and live suites passed as
recorded above; the disposable probe was not promoted because it found no defect.

Formatter/linter: no source or permanent test edits were made, so the repository edit
format/lint commands were not run. The scratch probe is disposable and remains outside
the tracked implementation scope.

Changelog: no entry is warranted; this review made no consumer-visible or production
change, and `CHANGELOG.md` was untouched.

## Independent verification (Worker 2)

The required scoped comparison
`git --no-pager diff 40445021bde4b5116f97cb22f90046f9c4a2176d -- django_strawberry_framework/views.py`
returned an empty diff (`exit 0`). The separate 46-addition/10-deletion working-tree delta is
the pre-existing implementation relative to `HEAD`, as documented above; it was not adopted,
reverted, or otherwise changed during this verification.

Re-traced `DjangoGraphQLView` and `AsyncDjangoGraphQLView` through the shared mixin, raw sync
adapter, `_request_body.py`, `_boundary_ordering.py`, and
`GraphQLRequestBodyBoundaryMiddleware`, including cap precedence and mount overrides, declared
and counted body limits, strict UTF-8/BOM handling, multipart form encoding and replacement
loss detection, and the two CSRF ordering arrangements. Connected fakeshop URL/settings and
live callers confirm the package view is the mounted endpoint. Strawberry source inspection
confirmed inherited schema execution, context/root-value hooks, error/resource/debug extension
execution, response header/cookie propagation, and sync/async response construction remain
the owners; no view-specific reimplementation masks or alters them.

Independent commands and outcomes:

- `uv run pytest tests/test_views.py --no-cov -q -n0` — 219 passed.
- `uv run pytest examples/fakeshop/test_query/test_transport_api.py --no-cov -q -n0` — 77
  passed.
- `uv run pytest tests/test_error_policy.py examples/fakeshop/test_query/test_resource_policy_api.py tests/middleware/test_debug_toolbar.py --no-cov -q -n0` — 96 passed.
- A disposable Python probe exercised HEAD/OPTIONS over-limit declarations (`413`), UTF-8
  codec aliases versus `utf-8-sig`/Latin-1/unknown names, and missing/empty/oversized
  multipart boundaries. The method and codec outcomes matched the contract; malformed
  boundaries were handled as Django `400 Bad Request` responses with no view `500`.
- A focused products run reached unrelated concurrent `mutations/resolvers.py` work and
  reported two `NameError: is_update` failures in mutation/upload tests; nine selected
  products rows passed. Those failures are outside this target and were neither changed nor
  absorbed.

The rejected hypotheses remain disposed of: unsupported-method cap ordering, Django-owned
malformed multipart parsing, the documented multipart declared-length carve-out, already
consumed streams, CSRF marker/wrapper fallback, mount-token protocol, and inherited response
and extension behavior all agree with the specification and executable evidence. No
production finding or permanent test promotion is required. Item 22 is verified.
