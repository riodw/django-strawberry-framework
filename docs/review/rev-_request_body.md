# Review: `django_strawberry_framework/_request_body.py`

Status: verified

## Understanding

`body_exceeds_limit` is the single private-Django boundary used by
`views.py::_RequestBodyBoundaryMixin._enforce_request_body_limit`. The view resolves
the mount/setting cap, rejects a declared `CONTENT_LENGTH` above it before touching
the stream, exempts multipart POSTs from the counted read so Django's upload handlers
retain streaming ownership, and delegates all other bodies here. A GET returns before
the body gate. The boundary raises `HTTPException(413, _BODY_LIMIT_REASON)`, which
both the view dispatch and `GraphQLRequestBodyBoundaryMiddleware.process_view`
translate to the same `text/plain` response.

The target first measures an existing `_body` cache, then inspects `_stream` unless
Django has already marked `_read_started`; the latter two states defer to Django's
own `RawPostDataException` behavior rather than inventing a body-limit refusal. A
seekable ASGI `SpooledTemporaryFile` is measured with `tell()` / `seek(0, SEEK_END)`
and restored without reading. A WSGI `LimitedStream`, async test-client stream, or
unmeasurable/custom stream falls back to `request.read()` in chunks no larger than
`_READ_CHUNK_BYTES`, stopping at `limit + 1`. An allowed bounded read closes the
consumed stream, installs a rewound `BytesIO`, and resets `_read_started`; it does not
write `_body`, so Django's own `DATA_UPLOAD_MAX_MEMORY_SIZE` check still runs.

The probe has explicit `UNMEASURABLE` and `CORRUPTED` outcomes. Probe failures before
movement use bounded reading; a failed or unverifiable restoration fails closed as
over-limit and emits one warning. A read/close/replacement failure likewise fails
closed with a warning and traceback. `Exception` is contained, while cancellation
and other `BaseException` control flow remains propagating.

The complete caller lifecycle was traced through both `DjangoGraphQLView` and
`AsyncDjangoGraphQLView`, their sync/async CSRF continuations, the package's raw-body
sync adapter, `GraphQLRequestBodyBoundaryMiddleware`, `_boundary_ordering.py`, and
the fakeshop URL/HTTP tests. Multipart POST encoding is checked from headers before
Django parses it; non-multipart bodies use the strict UTF-8 `parse_json` path. The
package setting accessor supplies the 1 MiB default or `None` disable, while a
per-mount positive exact `int` narrows it. Existing live tests cover status/reason,
middleware ordering, multipart upload-handler preservation, chunked/understated
lengths, Django's second ceiling, sync/async parity, and the UTF-8/BOM contract.

## Verification

- Ran the existing package-tier request-body matrix before implementation:
  `uv run pytest tests/test_views.py -q --no-cov -k 'cap or probe or position or stream or body_already or body_boundary or wire_contract or utf8 or multipart or charset or request_body'`
  — 139 passed.
- Disposable experiment under `docs/review/temp-tests/_request_body/` demonstrated
  that the pre-fix probe accepted a restored `int` subclass whose equality lied
  (`4`), and treated a non-callable `seekable=False` marker as probeable (`4`).
  After the fix it returns `_Probe.CORRUPTED` and `_Probe.UNMEASURABLE`, respectively.
- Added package-tier regression tests with both sync and async view classes:
  `test_a_foreign_initial_position_uses_the_bounded_read_without_seeking`,
  `test_position_restored_rejects_a_foreign_position_before_calling_the_stream`,
  `test_a_foreign_restored_position_is_not_allowed_to_lie_about_the_stream` and
  `test_a_non_callable_seekable_marker_uses_the_bounded_read`.
- Ran the focused package matrix after implementation:
  `uv run pytest tests/test_views.py -q --no-cov -k 'cap or probe or position or stream or body_already or body_boundary or wire_contract or utf8 or multipart or charset or request_body'`
  — 144 passed.
- Ran reachable fakeshop HTTP coverage:
  `uv run pytest examples/fakeshop/test_query/test_transport_api.py -q --no-cov -k 'multipart_request_over_the_declared_cap or over_cap_mutation or two_body_ceilings or async_package_view_enforces or async_view_keeps_the_utf8 or utf8_wire_contract_survives or stray_multipart_content_type or over_cap_multipart_request'`
  — 13 passed.
- `uv run ruff format .` completed; `uv run ruff check --fix .` reported all checks passed.

## Improvements

### High

None.

### Medium

#### Foreign restored positions could bypass the corruption verdict

- **Observation:** `_position_restored` compared the result of a foreign `tell()`
  directly with the original position before enforcing the exact built-in `int`
  contract. An `int` subclass can override `__eq__` and claim that a stream left
  at EOF was restored to offset zero. The probe then returned a numeric size and
  allowed an under-limit body from the wrong offset.
- **Evidence:** The disposable `LyingRestoredPositionStream` under
  `docs/review/temp-tests/_request_body/` reproduced the old `_measured_remaining`
  result (`4`) while its restore deliberately left the underlying `BytesIO` at EOF.
  Existing arithmetic tests protected `__sub__` and `__le__`, but not the restore
  equality protocol.
- **Impact:** A custom ASGI server or middleware stream could make the package
  hand Strawberry empty or wrong bytes instead of refusing an unprovable body;
  this violates the request-body boundary's position-integrity contract and can
  convert a valid request into a misleading parse result.
- **Recommendation:** Validate the initial position as an exact built-in `int`
  before any seek, and validate the restored `tell()` as an exact built-in `int`
  before comparing. Any foreign position becomes `UNMEASURABLE`/`CORRUPTED` and
  never runs consumer numeric/equality protocol inside the boundary.
- **Proof:** The permanent test uses a foreign equality-lie stream for both view
  classes, asserts a `413`, no read, the original stream remains installed, and
  the single `WARNING` carries the corrupted-probe message.

#### A non-callable `seekable` marker was mistaken for omission

- **Observation:** `_declares_seekable` treated every non-callable `seekable`
  attribute as if the method were absent. A stream explicitly exposing
  `seekable = False` was therefore probed with `tell`/`seek`, despite declaring
  itself non-seekable.
- **Evidence:** A disposable stream with working `tell`/`seek` and
  `seekable = False` returned a numeric measurement before the fix. The Python
  3.10 `SpooledTemporaryFile` compatibility case needs only the genuinely absent
  attribute (represented by `getattr(..., None)`), not arbitrary non-callable
  values.
- **Impact:** Foreign stream metadata could cause movement and an unnecessary
  compatibility risk at the probe boundary; the package should trust an explicit
  non-callable marker as non-seekable and use its bounded-read path.
- **Recommendation:** Treat `None` (the absent Python 3.10 shape) as the only
  fallback-to-`tell` case; treat any other non-callable marker as explicit
  non-seekable.
- **Proof:** The permanent test drives both view classes through a stream with
  `seekable = False` and asserts exactly `limit + 1` bytes are bounded-read with
  unread bytes remaining.

### Low

None.

## Summary

The request-body boundary already owns the correct policy and lifecycle: declared
length refusal, seekable versus bounded measurement, multipart streaming, Django
ceiling preservation, strict encoding, sync/async adapters, middleware ordering, and
fail-closed error/status contracts were all exercised by existing package and live
tests. The review found two foreign-stream probe-integrity gaps, fixed them at the
probe owner, and added permanent tests without changing the public wire contract.

## Implementation (Worker 1)

- Changed `django_strawberry_framework/_request_body.py`:
  - Reject non-built-in initial and restored positions before any foreign equality
    or arithmetic protocol runs.
  - Distinguish an absent `seekable` method (`None`) from a non-callable marker;
    the latter now takes the bounded-read path.
  - Updated the probe documentation to state the strengthened invariant.
- Changed `tests/test_views.py`:
  - Added foreign-position and malformed-seekability stream fixtures.
  - Added sync/async regression tests for fail-closed corruption and bounded fallback.
- Scratch verification:
  `DJANGO_SETTINGS_MODULE=config.settings uv run python docs/review/temp-tests/_request_body/probe_foreign_positions.py`
  returned `_Probe.CORRUPTED` and `_Probe.UNMEASURABLE` after the fix.
- Focused package tests: 144 passed.
- Focused fakeshop HTTP tests: 13 passed.
- Formatter/linter: `uv run ruff format .` and `uv run ruff check --fix .` passed.
- No changelog entry is warranted; this is an internal hardening correction with
  unchanged endpoint status/reason and no new consumer-facing feature.

## Independent verification (Worker 2)

- Scoped baseline comparison against `c9d17f71c3c6ac0a32f734ab8a541260bb6d23bc`
  found only the target and its package-tier permanent tests changed for this
  item; unrelated dirty and untracked work was left untouched.
- Re-ran the focused package matrix:
  `uv run pytest tests/test_views.py -q --no-cov -k 'cap or probe or position or stream or body_already or body_boundary or wire_contract or utf8 or multipart or charset or request_body'`
  — 144 passed.
- Re-ran reachable fakeshop HTTP coverage for declared and chunked lengths,
  cumulative fragments, sync/async body caps, Django's second ceiling,
  multipart parser ordering, uploads, UTF-8 aliases/BOM and lossy-form
  rejection — 44 passed. The narrower endpoint selection in the implementation
  record also passed 13 tests.
- Replayed the baseline implementation in a disposable module against the
  adversarial streams: the old probe moved before rejecting a foreign initial
  position, accepted a foreign equality-lie after restoration, and probed an
  explicit non-callable `seekable = False` marker. The current implementation
  avoided the movement, returned `CORRUPTED` for the lying restoration, and
  selected bounded fallback for the marker. Repeated calls on both the bounded
  success path and a seekable spool preserved the original bytes and position.

### Remaining medium finding: seekability attribute lookup is not guarded

- **Observation:** `_declares_seekable` calls `getattr(stream, "seekable", None)`
  outside its `Exception` boundary. A foreign stream can expose `seekable` as a
  property or descriptor that raises; the exception escapes before the bounded
  fallback and turns the request-body boundary into an unhandled server error.
- **Evidence:** A disposable `RaisingSeekable` stream with a raising
  `seekable` property reproduced a raw `RuntimeError` from
  `body_exceeds_limit`. This is distinct from the existing
  `seekable()`-raises test, which is caught by the current implementation.
- **Impact:** A custom ASGI/WSGI stream or middleware-installed wrapper can
  produce a `500` rather than the documented controlled `413`; the package has
  neither measured nor safely refused the body, and the foreign exception is
  logged as an application failure.
- **Recommendation:** Guard the capability attribute lookup itself with
  `except Exception` and treat a failed lookup as `UNMEASURABLE`, preserving the
  existing bounded-read path while continuing to propagate `BaseException`
  cancellation/control flow.
- **Proof:** Add package-tier sync and async tests with a raising `seekable`
  descriptor. Assert the stream is bounded-read to `limit + 1`, the view raises
  the ordinary `HTTPException(413)` without materializing `_body`, and the
  stream's unread suffix remains. The current package test tier is the strongest
  reachable level because fakeshop cannot install an arbitrary request stream.

The two Worker 1 findings and their permanent tests are independently verified,
but this remaining foreign-stream failure means the item is not yet complete.

## Iterations

### Revision pass (Worker 1)

- **Finding accepted:** Worker 2 reproduced a third foreign-stream failure:
  `_declares_seekable` performed `getattr(stream, "seekable", None)` outside its
  `Exception` boundary. A descriptor that raises therefore escaped as a raw
  `RuntimeError` instead of selecting the existing bounded-read fallback.
- **Root-cause fix:** Wrapped the capability attribute lookup in the same narrow
  `except Exception` boundary as the capability call. A failed lookup now returns
  `False`, which maps to `_Probe.UNMEASURABLE` and the bounded `limit + 1` read;
  `BaseException` remains uncaught for cancellation/control-flow semantics.
- **Permanent proof:** Added `_SeekableAttributeRaisingStream` and included it in
  `test_a_probe_that_fails_without_moving_the_stream_falls_back_to_the_bounded_read`
  for both sync and async views. It asserts the ordinary `413` path, exactly
  `limit + 1` bytes, and unread suffix preservation.
- **Independent reproduction:** A direct `RequestFactory` experiment with a
  raising `seekable` property now returns `True` from `body_exceeds_limit` rather
  than escaping the descriptor exception.
- **Validation:** `uv run pytest tests/test_views.py -q --no-cov -k 'cap or probe or position or stream or body_already or body_boundary or wire_contract or utf8 or multipart or charset or request_body'`
  — 146 passed. Reachable fakeshop HTTP subset — 13 passed.
  `uv run ruff format .` and `uv run ruff check --fix .` both passed.
- **Scoped diff:** `django_strawberry_framework/_request_body.py` gains only the
  guarded lookup; `tests/test_views.py` gains the descriptor fixture and one
  matrix parameter. No unrelated files were adopted, and the plan item remains
  unchecked for Worker 2/Worker 0 disposition.

### Independent verification (Worker 2, pass 2)

- Re-read the complete target, its sync/async view callers, middleware ordering
  path, live fakeshop mounts, focused package tests, and the transport spec.
  `body_exceeds_limit` has one production caller in
  `views.py::_RequestBodyBoundaryMixin._enforce_request_body_limit`; both
  `DjangoGraphQLView.run` and `AsyncDjangoGraphQLView.run` reach the same
  boundary before CSRF and parsing. The middleware invokes that same boundary
  before Django's CSRF parser when installed.
- Rechecked probe invariants: absent `seekable` (`None`) keeps the Python 3.10
  `tell`/`seek` fallback; an explicit non-callable marker (including
  `False`) selects bounded reading; a raising descriptor or `seekable()` is
  contained as `UNMEASURABLE`; exact built-in `int` checks protect initial/end
  positions and restoration from foreign arithmetic/equality hooks; failed
  restoration remains `CORRUPTED` and refuses without reading. Only
  `Exception` is caught, and a `KeyboardInterrupt` from a foreign capability
  still propagates as intentional `BaseException` behavior.
- Replayed the exact baseline helper from
  `c9d17f71c3c6ac0a32f734ab8a541260bb6d23bc` in the disposable request-body
  scratch area. The baseline raising-`seekable` descriptor escaped
  `RuntimeError` with zero reads, and its explicit `seekable = False` marker
  performed a seek probe with zero reads; the current helper bounded-read both
  streams exactly to `limit + 1` bytes, leaving an unread suffix. These are the
  concrete no-fix failures exercised by the new permanent regression matrix.
- Ran the focused package matrix:
  `uv run pytest tests/test_views.py -q --no-cov -k 'cap or probe or position or stream or body_already or body_boundary or wire_contract or utf8 or multipart or charset or request_body'`
  — 146 passed.
- Ran reachable fakeshop transport coverage for declared, understated, chunked,
  and cumulative-fragment lengths; sync/async caps; Django's second ceiling;
  multipart parser ordering and upload preservation; UTF-8 aliases/BOM; and
  lossy/non-UTF-8 form handling — 49 passed.
- Scoped comparison against `c9d17f71c3c6ac0a32f734ab8a541260bb6d23bc` contains
  only `_request_body.py` and its package-tier test changes; `git diff --check`
  is clean. No remaining finding.
