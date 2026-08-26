# DRY review: `django_strawberry_framework/_request_body.py`

Status: verified

## System trace

The module owns the package's entire contact surface with Django's private
request-body internals — `HttpRequest._stream`, `_body`, `_read_started`
(grep-verified unique in the package) — and exports exactly one answer,
`body_exceeds_limit(request, limit) -> bool` (spec-046 Decision 7): is this body
over limit, answered without materializing the body it may refuse. Four rungs in
one function: a cached `_body` is measured directly; a seekable stream is
size-probed by `_measured_remaining` (three outcomes: positive int,
`_Probe.UNMEASURABLE`, `_Probe.CORRUPTED`; exact-`int` positions only); anything
else is bounded-read through `request.read` in chunks up to `limit + 1` and
handed back as a closed-stream-plus-rewound-`BytesIO` replacement
(`_measured_by_bounded_read`), leaving Django's own ceilings intact; and the two
unmeasurable shapes fail closed as `True` plus one server-side WARNING each
(`_CORRUPTED_PROBE_LOG_MESSAGE`, `_UNREADABLE_STREAM_LOG_MESSAGE`). By design it
holds no policy: no `HTTPException`, no settings reads, no multipart handling.

Consumers traced: exactly one production importer —
`views.py::_RequestBodyBoundaryMixin._enforce_request_body_limit` (import at
`views.py` #"from django_strawberry_framework._request_body import") — reached
by both view classes through the mixin-first bases and by
`middleware/request_body.py::GraphQLRequestBodyBoundaryMiddleware.process_view`
through the same boundary-method name (`_boundary_ordering.py::_BOUNDARY_METHOD`,
probed then invoked under that name, so the chain cannot run a divergent copy).
`_cross_web_patches.py` is adjacent but disjoint: it replaces cross_web's public
adapter property over `self.request.body` and never touches Django privates.
Tests pinning it: `tests/test_views.py` (imports `_position_restored` and both
log-message constants; the "HOW the body is measured" block with Django-shape
fakes `_UnreadableSpool`, `_RecordingNonSeekableStream`,
`_UndeclaredSeekableStream`, `_NonCallableSeekableMarkerStream`,
`_UnmeasurableStream`, `_MisreportingSizeStream`) and live `/graphql` rows in
`examples/fakeshop/test_query/test_transport_api.py`. Prose media: the module's
own contract docstrings, spec-046 (+ rationale appx), GLOSSARY's Request-body cap
entry.

## Verification

Axis discharge:

1. **Cross-flavor policy mirroring** — searched
   `grep -rn '_stream\|_read_started\|\._body\|CONTENT_LENGTH\|max_request_body'`
   across `django_strawberry_framework/`: the declared-length rung lives in
   `views.py::_declared_content_length` (header only — a different fact, client
   claim vs measured bytes, feeding the same gate's earlier arm);
   `_strawberry_patches.py::_patched_parse_query_params` read in full — the GET
   `variables`/`extensions` shield routes parse errors only and carries no size
   policy; `consumers.py` has no request-body concept (WebSocket frames). No
   second flavor of "measure without materializing" exists to mirror.
2. **Sync and async twins** — `grep -c 'async def' _request_body.py` = 0: the
   module is colorless by design; one function serves both transports because
   both views share the mixin and the middleware invokes the same named method.
   Both transports are parametrized on the measurement rows (`view_class` in
   `tests/test_views.py`), so there is no drift lane. Ruled inapplicable.
3. **Derived rather than repeated knowledge** — the 1 MiB default appears only
   in its owner `conf.py` (`grep -rn '1_048_576'`); `views.py` explicitly
   disclaims restating it. `limit + 1` occurs only as arithmetic inside
   `_measured_by_bounded_read`. The exact-type idiom (`type(x) is int`) shared
   with `views.py::_resolved_max_request_body_bytes` guards different objects —
   a validated config value vs foreign stream positions/chunks/returns — with
   different reasons to change; the docstrings cross-reference rather than
   restate. No derived fact is stored twice.
4. **Inverse and round-trip pairs** — the consume→replace pair (close the
   consumed stream, install the rewound `BytesIO`) is one straight line in
   `_measured_by_bounded_read`; the seek-to-end→verify-restore pair lives in
   `_measured_remaining` + `_position_restored`, adjacent in this module. The
   other half of the substitution grammar is Django's own `HttpRequest.body`,
   which the module deliberately mimics in shape instead of reimplementing. No
   pack/unpack grammar is split across modules. Ruled inapplicable.
5. **Contracts restated in another medium** — counted: implementation (owner),
   contract prose (module + function docstrings), spec-046 Decisions 7/9 +
   rationale, GLOSSARY "Request-body cap", unit fakes + live HTTP tests. Prose
   describes policy and points here; nothing but the test fakes restates the
   private-attribute mechanics, and constructing those states is inherent to
   pinning a foreign private API — which centralization exists to make auditable
   from one file.

Rejected candidates (disproofs):

- *Exact-int guards duplicated* (`_measured_remaining` line #"type(position) is
  not int" vs `_position_restored` line #"if type(position) is not int"): not
  duplication — each guards a distinct foreign call's return at a distinct
  moment, and the helper's own check is load-bearing for direct callers (the
  test suite exercises it standalone); removing it would narrow the helper's
  contract to "whatever my one caller checked".
- *Fail-closed arms share a shape* (CORRUPTED arm vs bounded-read failure arm):
  two lines each, distinct messages, deliberately asymmetric `exc_info`
  (documented inline and at the constants). A shared helper would hide the
  distinction — the outcome DRY.md warns against.
- *Multipart carve-out could move into `body_exceeds_limit`*: it would need
  `_is_multipart_form_post` from `views.py`, which imports this module — a
  cycle, or a duplicated discriminator. When-to-measure in views,
  how-to-measure here is the acyclic ownership.
- *`consumers.py` fail-closed revalidation mirrors the fail-closed bool*: same
  pattern, different domain (session actor vs body bytes), and its logging
  difference (`logger.exception` vs WARNING) is documented at
  `_request_body.py` #"consumers.py's fail-closed revalidation". Not one rule
  twice.

Single-edit-site counts (posited changes):

- "Django renames `_stream` or changes `_read_started` initialization" → forced
  production sites: **1** (this module; its contract docstring rides in the same
  file). Mechanically verified: no other file names the three attributes.
- "Change how bodies are measured (new rung, different chunking, different
  fail-closed direction)" → **1** site; every caller holds only the `bool`.
- "Change which limit applies, the wire reason, or when the cap runs" → **1**
  site (`views.py`), this module untouched — the policy/mechanics seam answers
  one in both directions.
- Interpreter spot-check of the pinned capability facts (scratch, untracked):
  SpooledTemporaryFile declares `seekable` and subclasses `io.IOBase` at
  3.14.2, matching the module's floor-vs-modern claims; behavioral rows stay
  owned by the existing tests.

## Opportunities

None — every candidate consolidation was disproved at verification, and the
posited changes above came back with single-edit-site counts of one at their
natural owners. The module already is the consolidation a finding would propose:
one boolean contract, one grep-auditable private-attribute surface, one
fail-closed direction, and an acyclic split that leaves policy in `views.py`.

## Judgment

This is the rare file whose responsibility is already fully collapsed: the
dangerous knowledge (Django privates) has exactly one spelling, the dangerous
behavior (unbounded reads) has exactly one implementation, and the neighboring
modules consume it without restating any of it. Textual neighbors
(`_cross_web_patches.py`, `middleware/request_body.py`, `consumers.py`) were
each traced and rejected with domain-level reasons, not token counts. Zero-edit
result, proved; pytest run deferred per standing rule.

## Independent verification (Worker 2)

Scoped diff against cycle baseline `0202857` for this file: empty (exit 0).

Independently re-traced and confirmed:

- **Private-attribute surface, recounted repo-wide** including `examples/`:
  `_stream` / `_read_started` / `_body` appear in production only in this
  module — both attribute-access forms (`request._body`, `getattr(request,
  "_stream")`) and quoted-string spellings. `examples/fakeshop/test_query/
  test_transport_api.py` names `request._body` in a docstring witness only;
  `tests/test_views.py` names the privates throughout as assertions on the
  contract, which is inherent to pinning a foreign private API. Count of one
  holds.
- **Single production importer**: grep confirms `views.py:102` is the only
  import of `_request_body`; `body_exceeds_limit` is called exactly once at
  `views.py::_RequestBodyBoundaryMixin._enforce_request_body_limit`
  #"if body_exceeds_limit". The middleware reaches the same boundary through
  `_boundary_ordering.py::_BOUNDARY_METHOD = "_enforce_request_boundary"`,
  so no second invocation path can carry a divergent copy.
- **Acyclic seam re-proved mechanically**: this module imports only stdlib and
  `from . import logger`, where `logger` is a bare `logging.getLogger(...)` in
  `__init__.py` — no transitive reach into `views.py`. Moving the multipart
  carve-out here would therefore require either a back-import (cycle),
  duplicating `_is_multipart_form_post` (two spellings of "multipart", which
  the mixin's own docstring says must not drift), or relocating a when-to-
  measure policy into the module whose docstring disclaims all policy. The
  rejected candidate stands.

Re-ran the strongest rejected candidates; none is real duplication:

- *Exact-int guards*: four sites inside this module plus
  `views.py::_resolved_max_request_body_bytes`. Each guards a different
  foreign object with a different failure action (`ConfigurationError` for
  config vs sentinel-downgrade/fail-closed for stream returns), so they do not
  share one change axis; `_position_restored`'s own guard is load-bearing
  because tests exercise it standalone (`tests/test_views.py` imports it).
  Positing "admit int subclasses" does not move these sites together — the
  probe decision is about operator overrides inside a security boundary, the
  config decision about what counts as a limit.
- *Fail-closed log arms*: CORRUPTED arm logs without `exc_info` (no exception
  exists — a restore may return a wrong position without raising); bounded-read
  arm always has one. A shared helper would parameterize exactly the
  distinction the constants document.
- *consumers.py revalidation*: fail-closed-on-unverifiable is a shared security
  posture, not shared knowledge — session actor via `except` + 
  `logger.exception` vs body bytes via bool-returning measurement + WARNING.
  Different domains, mechanisms, log contracts, and change axes.

Matrix discharged against the real surface, independently: axis 1 searched
(`_patched_parse_query_params` read in full — parse-error routing only, no size
policy; `CONTENT_LENGTH` measured-bytes vs client-declared are intentionally
different facts); axis 2 ruled out by zero `async def` plus the single named
boundary method both transports share; axis 3 verified (`1_048_576` appears
only in `conf.py`; `limit + 1` arithmetic exists only here); axes 4–5 hold as
recorded — the consume→replace and probe→restore pairs are internal to this
file, and the prose media (spec-046, GLOSSARY "Request-body cap") point here
rather than restating mechanics; live `/graphql` coverage rows exist in
`test_transport_api.py`.

All three posited changes recount to one forced production site each. Verdict:
zero-edit result proved; Status set to `verified`. Plan checkbox checked.
