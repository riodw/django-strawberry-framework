# Build: Review round 2 — the HTTP boundary findings (multipart wire contract, CSRF ordering, stream probe)

Review reference: the maintainer's round-2 transport review — High 2 (multipart `operations` / `map` bypass the strict
UTF-8 wire contract), High 3 (the multipart declared cap runs after CSRF has already parsed the
body), Low 6 (stream capability failures escape the body boundary as raw errors).
Spec reference: `docs/spec-046-transport_security-0_0_15.md` — Decision 7 (the counted cap and the
three probe outcomes), Decision 8 (the deployment-layer co-requirement), Decision 9 (the strict
UTF-8 wire contract), Decision 17 (multipart control fields), Decision 18 (the CSRF re-entry);
Slice 2 / Slice 3 checklists; acceptance criteria 15, 39-42.

Scope note: Blocker 1 (active-subscription revocation), Medium 4 (the WebSocket `Host` boundary) and
Medium 5 (the Strawberry install hint) are other workers'. This artifact touches none of
`routers.py`, `consumers.py`, `auth/`, `conf.py`, `tests/test_routers.py`, `docs/README.md`, or the
spec.

Status: built (pass 2), dirty, uncommitted.

## Files touched

| File | Why |
| --- | --- |
| `django_strawberry_framework/views.py` | High 2: `_form_encoding_is_utf8` + `_enforce_multipart_form_encoding` + `_reject_lossy_multipart_control_fields` on the mixin, and a thin `parse_multipart` override per transport. High 3: `_RequestBodyBoundaryMixin.as_view` returns `csrf_exempt(super().as_view(...))`, and both `run` overrides call `_enforce_request_boundary` and then delegate through `_csrf_protected_run` / `_csrf_protected_async_run`. New constants `_MULTIPART_CONTROL_FIELDS`, `_REPLACEMENT_CHARACTER`, `_UTF8_CODEC_NAME`. |
| `django_strawberry_framework/_request_body.py` | Low 6: the probe is a three-state model (`_Probe.UNMEASURABLE` / `_Probe.CORRUPTED` / a positive `int`), every capability call is guarded, and the restore is *verified* with a second `tell()`. New `_declares_seekable` and `_position_restored`. |
| `tests/test_views.py` | 4 new stream stand-ins + 2 new row families for Low 6; 1 existing row's expectation changed (see below); the declared-charset matrix, the fallback rungs, the non-multipart carve-out, the `bytes` carve-out, the `csrf_exempt` mark on both callbacks, and the sync/async continuation shapes. |
| `examples/fakeshop/test_query/test_transport_api.py` | New live sections for High 2 (lossy control documents, declared charsets, genuine UTF-8 / escapes, field scoping) and High 3 (413-before-parser with an upload-handler sentinel, the full CSRF matrix on both transports, the middleware-removed invariant, cookie/`Vary`, accepted file streaming). New scaffolding: raw multipart builder, `_carrying_the_packages_csrf_mark`, `_RecordingUploadHandler`, `_csrf_failure_probe`, three probe mounts. |
| `docs/builder/bld-review-2-http_boundary.md` | This artifact. |

`conf.py` was **not** touched: no new setting. Both new boundaries are unconditional package policy
by design — a security contract with a kill switch is the finding, not the fix.

## High 2 — the multipart control-document contract

Implemented exactly as decided: Django keeps owning multipart framing, limits and file streaming,
and the package adds two conditions at its own boundary.

1. **Effective form encoding must canonicalize to UTF-8**, resolved as *declared top-level
   `charset`* -> `request.encoding` -> `settings.DEFAULT_CHARSET` and answered by
   `codecs.lookup(...).name == codecs.lookup("utf-8").name`. Enforced in `run`, from
   `_enforce_request_boundary`, i.e. **before** the form is parsed at all and before the CSRF
   re-entry.
2. **No replacement marker in `operations` / `map`**, checked after `request.POST` is populated and
   before `json.loads`, from the two `parse_multipart` overrides.

Both refuse with `HTTPException(400, _JSON_PARSE_REASON)` — upstream's own literal, so no caller can
attribute a rejection by message (Decision 9).

Three deliberate implementation details the decision did not spell out:

- **`request.encoding` is a third rung, not a redundant one.** Django's
  `HttpRequest._set_content_type_params` promotes a *usable* declared charset onto
  `request.encoding`, and `parse_file_upload` hands `request.encoding or DEFAULT_CHARSET` to
  `MultiPartParser` — so a consumer middleware that sets `request.encoding` with no charset declared
  changes how `operations` is decoded. Checking only the declaration and `DEFAULT_CHARSET` would
  leave the promise untrue in that deployment.
- **A declared charset is checked even when Django dropped it.** For an unusable codec name Django
  silently ignores the declaration and decodes with `DEFAULT_CHARSET`; the package refuses instead,
  because accepting would mean honouring a declaration nobody honoured. Verified live:
  `charset=no-such-codec` -> `400`.
- **A `bytes` control value is left alone**, deliberately: it still carries its own encoding, so
  `parse_json`'s strict decode is its correct owner. Django never produces one; the adapter protocol
  permits it.

`FileUploadHandler.receive_data_chunk`, `handle_raw_input`, a `MultiPartParser._parse` copy and a
`force_str` monkeypatch were all avoided; the escalation path (an upstream public hook for strict
non-file field decoding) is written into
`views.py::_RequestBodyBoundaryMixin._reject_lossy_multipart_control_fields`.

## High 3 — the ordering fix

`_RequestBodyBoundaryMixin.as_view` returns `csrf_exempt(super().as_view(**initkwargs))`; `run`
calls `_enforce_request_boundary(request)` and then `_csrf_protected_run(request, super().run, args,
kwargs)` (async: `_csrf_protected_async_run`, awaited). The two continuations are module-level
functions decorated **once at import**, so each transport carries one long-lived
`CsrfViewMiddleware` instance — the lifetime a `MIDDLEWARE` entry has — instead of building one per
request.

**Why the mark is on the `as_view` callback rather than on `dispatch`.** Both work — Django's
`View.as_view` copies `cls.dispatch.__dict__` onto the callback — but stamping the callback is a
single override on the shared mixin (which is what the spec asks for), costs no per-request wrapper
rebuild, and survives a consumer subclass that overrides `dispatch`. `method_decorator(csrf_exempt,
name="dispatch")` on each view class was implemented first and replaced for those reasons.

**Verified at the floor by execution, not by reading current.** An isolated venv
(`uv pip install --python <scratchpad>/floor310/bin/python "django==5.2.0"
"strawberry-graphql==0.316.0"`, never the shared `.venv`) ran a probe driving both package views
through `Client` / `AsyncClient` with `enforce_csrf_checks=True`. **23/23 checks passed at Python
3.10.19 / Django 5.2**: the async wrapper is a coroutine function (so
`make_middleware_decorator`'s async branch was taken), both callbacks are `csrf_exempt`, over-cap
multipart -> `413` with the upload sentinel silent, accepted multipart -> `200` with the sentinel
fired, no token -> `403`, form token -> `200`, malformed UTF-8 -> `400`, `charset=iso-8859-1` ->
`400`, genuine multibyte UTF-8 -> `200`. The same rows are standing regressions in
`test_transport_api.py` for the current stack.

**Limits, all three now written into the code documentation** (`views.py::_run_after_csrf_check` and
`_async_run_after_csrf_check`):

- the package reorders **its own** CSRF check only. A consumer middleware that touches
  `request.POST` / `request.body` inbound still precedes the gate; the cap then measures the already
  materialized body and refuses it, which is all that is left to do.
- the async wrapper's pre-processing is synchronous, so the token check's `request.POST` read
  happens on the event loop — for a request that has already passed the size gate, which is the
  mitigation rather than an oversight.
- a rejection raised *inside* the continuation never reaches `csrf_protect`'s `process_response`, so
  that response carries no rotated cookie from the decorator. The project's global
  `CsrfViewMiddleware.process_response` still runs and still honours `CSRF_COOKIE_NEEDS_UPDATE`, so
  only a project without the middleware sees the difference. The `413` and the multipart-encoding
  `400` are raised *outside* the continuation and never had one.
- a hand-written wrapper mount that calls the view without copying its `__dict__` loses the
  ordering (not the protection). The live probe mounts hit exactly this, which is why
  `_carrying_the_packages_csrf_mark` exists — and why the load-bearing sync ordering row runs
  against fakeshop's **real** `/graphql/` mount with the cap turned down through the setting rung.

## Low 6 — three probe outcomes

`_measured_remaining` now returns a positive `int`, `_Probe.UNMEASURABLE`, or `_Probe.CORRUPTED`;
`body_exceeds_limit` maps `CORRUPTED` to `True`, i.e. the package's own controlled `413`. Guards
catch `Exception` (not `BaseException`) around `seekable()`, `tell()`, the seek to the end, the
subtraction, and the restore. `_position_restored` verifies with a second `tell()`.

**One behavior change, deliberate.** A stream whose `tell()` **over-reports** its position (the
existing `_OverReportingPositionStream`) now lands in outcome 3 and is refused with `413`, nothing
read. Previously it fell through to a bounded read that started past the body's end, so Strawberry
received an **empty** body and answered `400` at the parse. The review's constraint is "never fall
through to a bounded read after a failed restore unless the original position is **known** to be
intact", and for that stream the position is objectively *not* intact after the probe — the
verifying `tell()` is what makes "known" mean measured rather than "the `seek` call did not raise".
`tests/test_views.py::test_a_stream_reporting_a_position_past_its_end_is_refused_rather_than_read`
(renamed from `..._is_not_waved_through`) carries the new expectation and the rationale. The
under-reporting shape (`_MisreportingSizeStream`, probe answers `0`) is unchanged: restore verifies,
outcome 2, bounded read.

## Verification

- `uv run pytest tests/test_views.py examples/fakeshop/test_query/test_transport_api.py --no-cov`
  -> **201 passed** (136 + 65).
- `uv run pytest --no-cov` (whole repo) -> **5052 passed, 40 skipped**. No regressions from the CSRF
  re-entry anywhere, including `test_uploads_api.py`'s real `Upload`-scalar multipart mutations
  (acceptance criterion 40) and the cookie-auth CSRF row 4.
- Floor probe: **23/23** at Python 3.10.19 / Django 5.2 (isolated venv, shared `.venv` untouched).
- `uv run ruff format` / `uv run ruff check` / `scripts/check_trailing_commas.py --check` clean on
  the four touched source files.
- **Not run:** `--cov` (the brief forbids it), so the `fail_under = 100` gate is unverified by me.
  Every new branch has an intended row — including both arms of the `isinstance(value, str)` guard
  (a multipart request without `map` supplies the `None` arm) and all four probe-failure sites — but
  the gate itself needs the maintainer's coverage run.

## Required spec amendments

Every item below is a sentence in `docs/spec-046-transport_security-0_0_15.md` (custodian-owned, not
edited here) that the shipped code makes false, over-claiming, or incomplete. Line numbers are
against the working tree at the time of writing.

### 1. Decision 17, condition 1 — the encoding resolution has three rungs, not two

`docs/spec-046-transport_security-0_0_15.md:2253-2257` (current):

> The package resolves it the way Django does — the declared top-level `charset` (which Django has
> already promoted onto `request.encoding` from `content_params`), else `settings.DEFAULT_CHARSET` —
> and accepts only codec aliases that canonicalize to UTF-8.

Recommended replacement:

> The package resolves it the way Django does, in Django's own order — the declared top-level
> `charset`, else `request.encoding`, else `settings.DEFAULT_CHARSET` — and accepts only codec
> aliases that canonicalize to UTF-8. The middle rung is not redundant: Django promotes a *usable*
> declared charset onto `request.encoding`, and `parse_file_upload` hands `request.encoding or
> DEFAULT_CHARSET` to `MultiPartParser`, so a consumer middleware that sets `request.encoding` with
> no charset declared decides how `operations` is decoded. The declaration is also checked when
> Django **dropped** it: for an unusable codec name Django ignores the declaration and decodes with
> `DEFAULT_CHARSET`, and accepting that would mean honouring a declaration nobody honoured.

### 2. Decision 17 — the two conditions are enforced at two different sites, and condition 1 is earlier than the spec says

`docs/spec-046-transport_security-0_0_15.md:2263-2265` (current):

> The guard is one shared helper on `_RequestBodyBoundaryMixin`; each view overrides upstream's
> `parse_multipart` with a two-line delegate that runs the helper and then calls `super()` — the
> sync view synchronously, the async view as a coroutine

and the same claim in the Slice 3 checklist, `docs/spec-046-transport_security-0_0_15.md:221-226`:

> The multipart control-document guard: each view overrides upstream's `parse_multipart` with a
> two-line delegate over one shared mixin helper, which accepts only an effective form encoding that
> canonicalizes to UTF-8 and refuses a `operations` / `map` value carrying Django's replacement
> marker `U+FFFD`, both with the same controlled `400`, **before** either value reaches `parse_json`

Recommended replacement (both sites): the guard is **two** shared helpers on
`_RequestBodyBoundaryMixin`, at two sites, because the two conditions can be answered at different
times:

> Condition 1 needs only headers, so `_enforce_multipart_form_encoding` runs from
> `_enforce_request_boundary` at the top of `run` — **before** the form is parsed at all, and before
> the CSRF re-entry — and an unhonourable declaration therefore costs nothing to refuse. Condition 2
> needs the decoded form, so `_reject_lossy_multipart_control_fields` runs from a thin
> `parse_multipart` override per transport (two lines sync, three async, because the async override
> awaits `get_form_data()` before delegating), which is the narrowest seam: it fires only when
> Strawberry is actually about to parse the control documents.

This matters beyond precision: as shipped, a `charset=iso-8859-1` multipart request is refused
without Django's parser or upload handlers running at all — a stronger property than "before either
value reaches `parse_json`".

### 3. Decision 17 — the `bytes` carve-out is unstated

Add after `docs/spec-046-transport_security-0_0_15.md:2260` (condition 2):

> A `bytes` control value — which Django never produces, but the adapter protocol upstream's
> `parse_multipart` reads permits — is deliberately **not** marker-checked: no replacement has
> happened yet, so its encoding is `parse_json`'s strict decode to own, and the two guards must not
> overlap.

### 4. Decision 17's table — two rows missing

The table at `docs/spec-046-transport_security-0_0_15.md:2292-2299` has no row for the two
declared-charset shapes the implementation and the live matrix cover:

| multipart `operations` on the wire | Django's decode | package guard | outcome |
|---|---|---|---|
| declared `charset=utf-8-sig` | clean, BOM-eating codec | refused at condition 1 | `400` |
| declared charset Django cannot load (`no-such-codec`) | clean, `DEFAULT_CHARSET` silently used | refused at condition 1 | `400` |

The second row is the interesting one: Django's own fallback is what the package refuses to inherit.

### 5. Decision 7, probe outcome 2 — an incoherent pair does not always stay in outcome 2

`docs/spec-046-transport_security-0_0_15.md:1234-1238` (current):

> 2. **Safely unmeasurable, original position intact** — the stream declared itself unseekable, or
>    `tell()` refused, or the pair came out incoherent and the restore succeeded.

Recommended replacement:

> 2. **Safely unmeasurable, original position intact** — the stream declared itself unseekable (or
>    `seekable()` raised), or `tell()` refused, or the subtraction could not be produced, or the pair
>    came out incoherent **and the restore was verified** to land back where the request started.
>    The under-reported-end shape (a `seek` that returns the offset it was handed) is the one that
>    stays here: it never moved, so the verification passes and the bounded read supplies the bound.

### 6. Decision 7, probe outcome 3 — "the restoring seek failed" is too narrow

`docs/spec-046-transport_security-0_0_15.md:1244-1250` (current):

> 3. **Position potentially corrupted** — the seek to the end succeeded (or raised after moving) and
>    the restoring seek then failed, so the stream's read position is no longer known to be where the
>    request started.

Recommended replacement:

> 3. **Position potentially corrupted** — the seek to the end succeeded (or raised after moving) and
>    the restore then failed **or could not be verified**. The restore is confirmed with a second
>    `tell()`, because "known to be intact" has to mean measured: a stream whose coordinates are
>    incoherent (a `tell()` answering in the coordinates of the whole HTTP message) accepts the
>    restoring `seek` without raising and still ends up somewhere else, and a bounded read from there
>    returns bytes the client never sent.

### 7. Decision 7's rejected-alternatives block — the disclosed cost is no longer the cost

`docs/spec-046-transport_security-0_0_15.md:2688-2692` (current):

> The cost in the over-reporting direction is disclosed rather than papered over: the restored
> position lands past the end, so the request reaches Strawberry with an **empty** body and is a
> `400` at the parse — never a bypass.

That empty-body fall-through is exactly what the verified restore removes. Recommended replacement:

> The over-reporting direction is not read at all: the restoring seek lands where the lie points, the
> verifying `tell()` disagrees, and the request is refused with the package's own `413` (probe
> outcome 3) rather than reaching Strawberry with an **empty** body it never sent. That is a change
> from the round-1 behavior, and it is the point: silently substituting an empty body for the
> client's is safe but dishonest, while "the package could not measure this body" is a body-limit
> rejection.

### 8. Acceptance criterion 15 — the incoherent-pair sentence now describes two different outcomes

`docs/spec-046-transport_security-0_0_15.md:2874-2879` (current):

> A stream whose `tell()` / `seek` pair is incoherent in either direction — an over-reported position,
> an under-reported end — is refused a measurement and bounded by the read instead, in both the
> over-limit direction (`413`, one bounded read) and the genuinely-empty one (allowed, one bounded
> read), so the probe's zero is never taken on trust.

Recommended replacement:

> A stream with an **under-reported end** (a `seek` that returns the offset it was handed) is refused
> a measurement and bounded by the read instead, in both the over-limit direction (`413`, one bounded
> read) and the genuinely-empty one (allowed, one bounded read), so the probe's zero is never taken on
> trust. A stream with an **over-reported position** is refused outright by probe outcome 3 (`413`,
> nothing read), because its restore cannot be verified.

### 9. Decision 18, step 1 and the stamping paragraph — name the site precisely

`docs/spec-046-transport_security-0_0_15.md:2341` says "the outer dispatch callback carries
`csrf_exempt`", and `:2350-2351` says it is "stamped by the package, once, on the callback
`as_view()` returns — a single override on the shared mixin". The second sentence is exactly what
shipped; the first is loose enough to be read as `dispatch`. Recommended: make step 1 say "the
callback `as_view()` returns carries `csrf_exempt`", and add the mechanism to the stamping
paragraph:

> `_RequestBodyBoundaryMixin.as_view` returns `csrf_exempt(super().as_view(**initkwargs))`, so the
> mark is on the object `process_view` actually reads it off. Decorating `dispatch` and letting
> `View.as_view` copy `cls.dispatch.__dict__` would also work; stamping the callback is preferred
> because it is one override for both transports, adds no per-request wrapper rebuild, and survives a
> consumer subclass that overrides `dispatch`. `functools.wraps` inside `csrf_exempt` carries
> `view_class` / `view_initkwargs` and the coroutine marking through.

### 10. Decision 18, "What this does not change" — the consumer-middleware limit is missing

`docs/spec-046-transport_security-0_0_15.md:2383-2387` names only the ASGI spooling. Add:

> The reorder also only moves the **package's own** CSRF check. Any consumer middleware that reads
> `request.POST` or `request.body` inbound still runs before the view and still precedes the gate; the
> cap then measures that already materialized body and refuses it rather than processing it
> ([Decision 7](#decision-7--the-app-level-body-cap-lives-in-the-package-django-view-counted-not-declared)'s
> first rung, which is now reachable **only** that way — Django's own `CsrfViewMiddleware` no longer
> gets there first). A project that needs the ordering for multipart must not parse the request in
> middleware. Likewise, a hand-written wrapper mount that calls the package view without copying its
> `__dict__` drops the `csrf_exempt` mark and loses the ordering (never the protection).

### 11. Decision 18, consequence (b) — incomplete in two ways

`docs/spec-046-transport_security-0_0_15.md:2392-2397` (current):

> (b) An `HTTPException` raised inside the continuation (a `400` from the wire contract, say) unwinds
> past `csrf_protect` without reaching its `process_response`, so those error responses do not carry a
> rotated CSRF cookie; the `413` is raised outside the continuation entirely and never did.

Recommended replacement:

> (b) An `HTTPException` raised inside the continuation (the multipart marker `400`, or upstream's own
> parse `400`) unwinds past `csrf_protect` without reaching its `process_response`, so that response
> carries no rotated CSRF cookie **from the decorator** — the project's global
> `CsrfViewMiddleware.process_response` still runs and still honours `CSRF_COOKIE_NEEDS_UPDATE`, so
> only a project that omitted the middleware sees a difference. The `413` **and** the multipart
> form-encoding `400` are raised outside the continuation entirely and never had one.

### 12. Decision 9 — "one step earlier" is two steps for half of Decision 17

`docs/spec-046-transport_security-0_0_15.md:1381-1383`: "The multipart control documents get their
own boundary, one step earlier, in Decision 17." Recommended: "…get their own boundary earlier:
their form **encoding** is checked in `run`, before the form is parsed at all, and their decoded
values are checked in `parse_multipart`, before `parse_json` — both in Decision 17."

### 13. Test plan / Decision 13 — record where the ordering row runs, and what the round added

`docs/spec-046-transport_security-0_0_15.md:1958-1964` describes the cap rows gaining "a
`Client(enforce_csrf_checks=True)` sibling with a parser sentinel". Two facts belong on disk, because
a later reader cannot re-derive either from the code:

- the sentinel is a `FILE_UPLOAD_HANDLERS` override recording `handle_raw_input` (called by
  `MultiPartParser.parse` for **any** multipart body, files or not) plus `new_file` /
  `receive_data_chunk` (files only), and the emptiness of that list is the ordering evidence;
- the **sync** ordering row deliberately runs against fakeshop's real `/graphql/` mount with the cap
  turned down through the `MAX_REQUEST_BODY_BYTES` setting rung, not against a probe mount, because
  every probe mount in that file wraps its view in a per-request resolver function that is itself the
  URL callback — and such a wrapper does not carry `csrf_exempt` unless it copies it. The probe mounts
  copy the mark from the package (`_carrying_the_packages_csrf_mark`), which is scaffolding; the
  shipped mount needs nothing, and that is the row that proves the deployment shape.

### 14. Acceptance criteria 39-42 — what landed, for the custodian to tick or widen

Implemented as specified, with these additions worth recording: criterion 39's matrix runs on both
transports and covers `map` as well as `operations`, and both the "malformed byte Django replaced"
and "client sent a literal `U+FFFD`" directions; the escaped-`�` direction additionally proves
the escape reaches the schema intact (upstream echoes `operationName` verbatim, so the response body
carries the exact bytes). Criterion 42's "with the global middleware removed entirely" row exists for
both transports. Criterion 40 is satisfied by `test_uploads_api.py`'s existing `Upload`-scalar
multipart mutations continuing to pass **plus** a new row asserting `new_file` /
`receive_data_chunk` fire on an accepted request through the shipped mount.

## Notes for the maintainer

- One existing test's expectation changed (item 7/8 above); no hunk written by another worker was
  reverted.
- `docs/TREE.md` / `docs/GLOSSARY.md` untouched (Slice 5's fold-in).
- The floor probe script lives in the session scratchpad, not the repo. It is reproducible from the
  command in the "Verified at the floor" paragraph above; nothing in the repo depends on it.

---

## Build report (Worker 2, pass 2) — remediating `docs/builder/bld-review-2-w3_review.md`

Round-2 Worker 3 review findings dispatched to this cohort: **M1** (the multipart
form-encoding gate lets a client-declared `charset` mask Django's real effective encoding,
reopening review High 2), the **HTTP half of M4** (two encoding rungs share one test row), **L1**
(the encoding gate is not method-scoped and the mixin's "**GET.** A no-op" sentence is false),
**L2** (the corrupted-stream `413` is silent server-side), **L7** (the async CSRF-ordering row
runs against repaired scaffolding), and the **first nit** (the multipart discrimination computed
twice in adjacent mixin methods).

This artifact has no `## Plan (Worker 1)` section and therefore no
`### Dispatched findings checklist` / `### Spec slice checklist (verbatim)` to tick; the list
above is the closest thing it carries, and every item is dispositioned below.

### Files touched

Grounded in `git status --short` after both ruff invocations. The four files below are this
cohort's; everything else `git status` reports (`README.md`, `TODAY.md`, `conf.py`, `auth/*`,
`consumers.py`, `routers.py`, `tests/test_routers.py`, `docs/README.md`, the incoming review,
`docs/spec-046-*.md`, `docs/builder/BUILD.md`, `docs/builder/worker-*.md`,
`docs/builder/build-046-*.md`, the three sibling `bld-review-2-*.md`, `drys.md`, `vulns.md`) is
the concurrent WS cohorts', the coordinator's, or the maintainer's, and was neither read for
modification nor written (`AGENTS.md` L34).

| File | What changed |
| --- | --- |
| `django_strawberry_framework/views.py` | **M1**: `_form_encoding_is_utf8` is now **conjunctive**. New `_canonicalizes_to_utf8` helper; the resolution is `declared (if present) must be UTF-8` **and** `request.encoding or settings.DEFAULT_CHARSET must be UTF-8`. Docstring rewritten: the "three rungs ... read in the order Django applies them" claim is deleted and replaced with what Django actually consumes. **L1 + nit**: new `_is_multipart_form_post` discriminator (`method == "POST" and content_type == multipart`), used by BOTH `_enforce_request_body_limit` and `_enforce_multipart_form_encoding`, so the duplicated comparison is gone and a stray multipart `Content-Type` on a GET is no longer refused. Mixin docstring's `**GET.** A no-op` sentence corrected to name both halves; `_enforce_request_boundary` docstring names the shared discriminator. |
| `django_strawberry_framework/_request_body.py` | **L2**: one `logger.warning(_CORRUPTED_PROBE_LOG_MESSAGE, type(stream).__name__)` at the `_Probe.CORRUPTED` site in `body_exceeds_limit`, plus the new module-level message constant carrying the level rationale. `from . import logger` added (the relative form the private siblings `_strawberry_patches.py` / `_cross_web_patches.py` already use). Module docstring and `body_exceeds_limit`'s outcome-4 bullet now state that this branch logs and that the wire is unchanged. |
| `tests/test_views.py` | **M1 / M4**: the one row that pinned two rungs is split into four independently-failing rows plus the M1 regression; new `_multipart_body` helper and `_multipart_request(..., encoding=, method=, data=)` parameters. **L1**: the GET carve-out row. **L2**: `_assert_the_corrupted_probe_was_recorded` and `caplog` on both `CORRUPTED` rows. |
| `examples/fakeshop/test_query/test_transport_api.py` | **M1**: `_LatinOneEncodingMiddleware` + `_with_a_middleware_that_sets_the_encoding`, and the exploit rows on both transports. **M4**: the live `DEFAULT_CHARSET` rung row. **L1**: the live GET row. **L7**: the async ordering row's docstring now records the scaffolding asymmetry. |

`conf.py` still untouched: no new setting. Both new behaviours are unconditional package policy.

### The M1 fix, and the Django behaviour it is derived from

Verified by **execution**, at the floor and on current, not by reading (script:
`<scratchpad>/probe_encoding.py`, `<scratchpad>/probe2.py`). Identical output at
Python 3.10.19 / Django 5.2.0 and Python 3.14.2 / Django 6.0.5:

| declared `charset` | middleware `request.encoding` | `DEFAULT_CHARSET` | `request.encoding` after construction | what Django decoded `operations` with |
|---|---|---|---|---|
| `utf-8` | — | `utf-8` | `'utf-8'` | UTF-8 |
| `iso-8859-1` | — | `utf-8` | `'iso-8859-1'` | Latin-1 |
| `no-such-codec` | — | `utf-8` | `None` (declaration **dropped**) | UTF-8 (`DEFAULT_CHARSET`) |
| **`utf-8`** | **`iso-8859-1`** | `utf-8` | **`'iso-8859-1'`** | **Latin-1, no `U+FFFD`** |
| — | — | `iso-8859-1` | `None` | Latin-1 |
| `utf-8` | — | `iso-8859-1` | `'utf-8'` | **UTF-8** |

The fourth row is the reviewer's exploit and it reproduces exactly: the declaration is read
once, at `HttpRequest._set_content_type_params`, and `content_params` is **never** consulted
again — `HttpRequest.parse_file_upload` hands `MultiPartParser` nothing but `self.encoding`
(`django/http/request.py` #"MultiPartParser(META, post_data, self.upload_handlers, self.encoding)",
line 356 at 5.2.0 / 368 at 6.0.5) and `MultiPartParser.__init__` resolves
`encoding or settings.DEFAULT_CHARSET` (line 113 at **both** versions). The Latin-1 decode
produced `'{"query": "{ __typename }", "note": "é"}'` with **no** replacement marker, so
`_reject_lossy_multipart_control_fields` was structurally blind to it, exactly as the review
states.

The **sixth** row is the one that decides the fix's shape, and it is why the fix is *not*
"every value in sight must be UTF-8": with `DEFAULT_CHARSET` at Latin-1 and the client
declaring `charset=utf-8`, Django promotes `utf-8` onto `request.encoding` and genuinely
decodes UTF-8. Refusing that request would refuse one Django handles exactly as the contract
promises. So the second condition is `request.encoding or settings.DEFAULT_CHARSET` — Django's
own `or`, reproduced rather than re-invented — and the package tracks Django's behaviour
instead of asserting a rung order of its own.

### Tests added or updated

Package tier (`tests/test_views.py`), 136 -> 141 collected:

- `test_a_declared_utf8_charset_does_not_mask_a_middleware_set_request_encoding` — the M1
  regression, **and** the premise: the same request allowed to parse decodes the raw `0xe9`
  to `U+00E9`, asserted as `"\ufffd" not in decoded` and
  `json.loads(decoded)["note"] == "\u00e9"` (escapes in the source, per the ASCII-only rule), so
  the blindness of the loss detector is on disk rather than asserted in prose.
- `test_a_declared_non_utf8_charset_is_refused_even_when_django_would_decode_utf8[usable-name-django-promoted|unusable-name-django-dropped]`
  — pins the **declared** condition independently, by forcing `request.encoding` to UTF-8 so
  condition 1 is satisfied and only the declaration can refuse.
- `test_a_middleware_set_non_utf8_request_encoding_is_refused_on_its_own` — the
  `request.encoding` sub-rung with nothing declared, plus the accepted control.
- `test_a_reconfigured_default_charset_is_refused_but_a_declared_utf8_still_wins` — the
  `DEFAULT_CHARSET` sub-rung, plus the accepted-declaration boundary from the table above.
- `test_a_get_carrying_a_stray_multipart_content_type_is_not_a_multipart_form` — L1, asserted
  through `_enforce_request_boundary` (both halves must be no-ops), with the POST direction as
  the control.
- `_assert_the_corrupted_probe_was_recorded` + `caplog` on
  `test_a_stream_reporting_a_position_past_its_end_is_refused_rather_than_read` and
  `test_a_probe_that_cannot_restore_the_position_refuses_instead_of_reading` — L2. The message
  object is asserted **by identity** (`record.msg is _CORRUPTED_PROBE_LOG_MESSAGE`) rather than
  by a re-typed string, `record.args == (type(stream).__name__,)` keeps the actionable detail,
  and `exc_info is None` pins that this is not an exception-context log.
- Removed: `test_an_undeclared_form_encoding_falls_through_request_encoding_to_default_charset`
  — the single row that pinned two rungs at once (review M4). Its two subjects are now the two
  rows above, and nothing it asserted was dropped.

Live tier (`examples/fakeshop/test_query/test_transport_api.py`), 65 -> 69 collected:

- `test_a_middleware_set_request_encoding_is_not_masked_by_a_declared_utf8_charset` — the M1
  deployment against fakeshop's **real** `/graphql/` mount: an ASCII control document refused
  under the middleware, the identical request **without** the middleware `200`, and the
  review's own raw-Latin-1 probe refused.
- `test_the_async_view_is_not_masked_by_a_declared_utf8_charset_either` — the async colour
  (`/async-multipart/`), with the same control.
- `test_a_project_that_reconfigured_default_charset_is_refused_unless_the_client_declares_utf8`
  — the `DEFAULT_CHARSET` rung live, with the accepted-declaration boundary.
- `test_a_get_carrying_a_stray_multipart_content_type_still_serves_the_query` — L1 live; the
  reviewer's own probe (`temp-tests/review-2/test_get_multipart_content_type.py`) promoted.
- `test_the_async_view_also_refuses_before_djangos_parser_runs` — docstring only (L7).

### Validation run

- `uv run ruff format <the four files>` — pass (1 reformatted, then stable).
- `uv run ruff check --fix <the four files>` — 1 COM812 fixed; `uv run ruff check` then **All
  checks passed**.
- `uv run python scripts/check_trailing_commas.py --check <the four files>` — 1 violation
  (`_multipart_request`'s signature), fixed with `--fix` **scoped to `tests/test_views.py`
  only**, then clean on all four. Never run repo-wide.
- ASCII-only: `LC_ALL=C grep -n '[^ -~\t]' <the four files>` -> no matches. (The first draft of
  the M1 row carried literal `U+00E9` / `U+FFFD` characters; both are now `\u00e9` / `\ufffd`
  escape sequences in the source.)
- `git status --short` after both ruff invocations: only the four files above plus the
  concurrent/maintainer set enumerated in `### Files touched`. **No** tool churn to revert, and
  no `git` write command of any kind was run this pass (no `commit`, `add`, `stash`, `branch`,
  `checkout`, `switch`, `restore`).
- Focused: `uv run pytest tests/test_views.py examples/fakeshop/test_query/test_transport_api.py --no-cov`
  -> **210 passed** (141 + 69).
- Full suite: `uv run pytest --no-cov` -> **5099 passed, 40 skipped**.

**Delta against the 5072 / 40 baseline: +27, fully attributed.** +9 are this cohort's
(`tests/test_views.py` 136 -> 141, `test_transport_api.py` 65 -> 69). The other +18 are the
concurrent WebSocket cohort's: `tests/test_routers.py` measured 104 at the reviewer's baseline
and collects **122** now, and this cohort wrote none of it. `5072 + 9 + 18 = 5099`.

`--cov` was not run (forbidden), so `fail_under = 100` is still the maintainer's gate. Every new
branch has an intended row, including both arms of `_is_multipart_form_post` and both arms of
the `declared is not None` guard.

### Failability proofs

Procedure, for all six: `cp` the target to `<scratchpad>/pristine/` **before** any mutation;
each mutation applied from that pristine copy by an exact-string anchor asserted to match
**exactly once** (`<scratchpad>/mutate.py`, which refuses on any other count, so a mutation can
never stack); focused suite run; restored by copying the pristine file back; restore proved by
`filecmp.cmp(..., shallow=False)` **and** `diff -q`. One boundary at a time, reverted before the
next. `git checkout` / `git restore` were never used and are never the right tool here — the
working tree is legitimately dirty with this cohort's work and the concurrent cohorts', so an
empty `git diff` is unachievable and forcing one would destroy other people's work.

| # | Boundary | Mutation applied | Rows failed | From |
|---|---|---|---|---|
| A | `views.py::_form_encoding_is_utf8` #"request.encoding or settings.DEFAULT_CHARSET" — the `request.encoding` sub-rung of condition 1 (**the M1 fix**) | `return _canonicalizes_to_utf8(request.encoding or settings.DEFAULT_CHARSET)` -> `return _canonicalizes_to_utf8(settings.DEFAULT_CHARSET)` | **6** | 3 `tests/test_views.py` + 3 `test_transport_api.py` |
| B | the same expression's `settings.DEFAULT_CHARSET` sub-rung (**was the 1-row half of M4**) | -> `return _canonicalizes_to_utf8(request.encoding or _UTF8_CODEC_NAME)` | **2** | 1 + 1 |
| C | `views.py::_form_encoding_is_utf8` condition 2 — the declared-charset check | the three-line `declared = ...` / `if declared is not None and not ...: return False` block deleted | **5** | 3 + 2 |
| D | `views.py::_is_multipart_form_post` — the POST scoping (**L1**) | `return request.method == "POST" and request.content_type == _MULTIPART_CONTENT_TYPE` -> `return request.content_type == _MULTIPART_CONTENT_TYPE` (i.e. the pre-fix behaviour restored) | **2** | 1 + 1 |
| E | `_request_body.py::body_exceeds_limit` — the `_Probe.CORRUPTED` server-side record (**L2**) | the `logger.warning(_CORRUPTED_PROBE_LOG_MESSAGE, type(stream).__name__)` line deleted | **4** | `tests/test_views.py`, both `CORRUPTED` stream shapes x both view classes |
| F | reference / whole gate: `views.py::_RequestBodyBoundaryMixin._enforce_multipart_form_encoding` | body replaced with `return` | **21** | 13 at the reviewer's measurement; the split rows are the difference |

Every revert: `RESTORED ...; byte-identical to pristine copy: True` **and** `diff -q` silent.

No boundary in this pass fails 0 or 1 rows. The two the reviewer named as **weakly pinned** —
"`views.py:226` rung 2 **and** rung 3, the same row pins both, worst case in the round" — are now
proof A (6 rows) and proof B (2 rows), and each has a live sibling as the review required.

Mutation A was **also re-run at the floor** (see `### Floor verification`): **6 rows, the same
6**, so the M1 boundary is failable at Python 3.10 / Django 5.2.0 and not only on current.

### Hot-path budget

`build-046-transport_security-0_0_15.md` declares no hot path (the requirement postdates the
plan, exactly as the review's M5 records for the WS cohort). This cohort's changed path meets
`BUILD.md`'s definition anyway — `_enforce_request_boundary` runs **per request** — so the number
is captured rather than argued about, and whether the trade is acceptable is the maintainer's.

Metric: median wall-clock per gate evaluation. `timeit.repeat(number=10_000, repeat=200)` =
2,000,000 calls per variant, median of the 200 samples divided by 10,000. Same metric, same
process, before and after; "before" is the round-2 shipped `or`-chain reimplemented in the bench
script so both run against the identical `HttpRequest`. Script:
`<scratchpad>/bench_gate.py`, `uv run python <scratchpad>/bench_gate.py`.

| request shape | before | after | delta |
|---|---|---|---|
| declared `charset=utf-8` (worst case: **two** `codecs.lookup` calls) | 133.1 ns | 256.8 ns | **+123.7 ns / request** |
| no declaration (one `codecs.lookup`) | 251.6 ns | 264.4 ns | **+12.8 ns / request** |

`_is_multipart_form_post` measures 39-47 ns, standing where one `request.content_type == ...`
comparison stood; the added cost is one string comparison plus a function call, and it is now
paid **once instead of twice** on a multipart POST because the two mixin methods share it.

Reading: the worst case adds ~0.12 microseconds to a request whose next step is Django's entire
multipart parse, and it is paid only on `multipart/form-data` POSTs — the gate returns before
any lookup on JSON bodies and on GET. Note the asymmetry in the "before" column is not noise:
the old chain short-circuited on the declaration and so **skipped** the `LazySettings.__getattr__`
for `DEFAULT_CHARSET`, which is most of the 251.6 ns in the second row. No allocation, no I/O,
no lock, no round trip added.

### Implementation notes

Design choices this pass made that the review did not fix:

- **`_canonicalizes_to_utf8` extracted rather than the `try` duplicated.** Two conditions need
  the same "does this codec name canonicalize to UTF-8, and is failure a rejection" answer, and
  inlining it twice would have duplicated the `except (LookupError, TypeError)` contract — the
  one part of this function that is a policy rather than a lookup.
- **`_is_multipart_form_post` is a module-level predicate, not a kwarg threaded down.** The
  review's nit suggested "one discriminator computed once in `_enforce_request_boundary` and
  passed down". That would change `_enforce_request_body_limit`'s signature, which **25 existing
  package rows call directly** — the tests would have had to be rewritten for a nit. A named
  predicate removes the duplicated literal, fixes L1, and leaves both methods independently
  callable.
- **`request.method == "POST"`, not `!= "GET"`** — see `### Notes for Worker 3` #1; this is a
  deliberate divergence from the review's prescribed fix, with executed evidence.
- **`logger.warning`, not `logger.exception`** — see `### Notes for Worker 3` #3.
- **The log message is a named module constant, not an inline literal.** It is asserted by
  identity from the test, so a reword cannot silently retire the assertion, and the level
  rationale lives next to the text it justifies rather than at the call site.
- **`type(stream).__name__` rather than `describe_value(stream)`** or `repr`. The culprit is a
  *class* installed by an ASGI server or a middleware; the instance's repr can be arbitrary,
  attacker-influenced, or expensive, and the class name is the whole actionable fact.
- **The M1 package row proves its own premise.** It parses a second, identical request to show
  the Latin-1 decode yields `U+00E9` and no `U+FFFD`. Without that, the row would silently
  become a tautology the day Django changed its field decode.
- **The live `DEFAULT_CHARSET` rows use ASCII bodies deliberately** — see
  `### Notes for Worker 3` #4, which is a fixture trap rather than a preference.

### Notes for Worker 3

1. **Deliberate divergence from L1's prescribed fix, with evidence.** The review recommended
   adding `request.method == "GET"` to the early return. I used the positive form
   `request.method == "POST"`, because `django/http/request.py::HttpRequest._load_post_and_files`
   installs an empty `QueryDict` and returns **for every method other than POST** before the
   content type is even looked at (line 392 at 5.2.0, 422 at 6.0.5) — so `!= "GET"` would still
   refuse a multipart-typed `PUT` / `PATCH` / `DELETE` whose fields Django never decodes.
   Executed at both versions: a `PUT` carrying a real multipart body yields
   `POST = {}`, `FILES = {}`. Strawberry answers `405` to every method other than GET and POST
   (`strawberry/http/sync_base_view.py::SyncBaseHTTPView.run` #"GraphQL only supports GET and POST requests."),
   so nothing reachable is loosened.
2. **A consequence of #1 worth checking rather than assuming.** `_enforce_request_body_limit`'s
   multipart carve-out now also requires POST, so a multipart-typed **non-POST** body is
   *counted* instead of carved out. That is the stricter direction and it is correct — Django
   streams nothing for it and upstream `405`s it — but it is a behaviour change beyond L1's
   literal scope, it is documented in `_is_multipart_form_post`'s docstring, and the full suite
   is green. Flagging it explicitly rather than letting it be discovered.
3. **`logger.warning`, and the review's `logger.exception` alternative is wrong here.** L2 offers
   "a `logger.warning` / `logger.exception`". `exception` is not available on this branch: the
   `CORRUPTED` verdict is reachable with **no active exception** — `_position_restored` returns
   `False` when the verifying `tell()` merely disagrees, without anything raising — so
   `logger.exception` outside an `except` block would emit `NoneType: None` as a traceback.
   `consumers.py:452` legitimately uses `exception` because it *is* inside an `except` block with
   a traceback worth carrying. `warning` is also the level the package already uses for
   "a deployment should look at this, but it is not this process's error"
   (`types/finalizer.py`, `optimizer/nested_planner.py`). The test pins `exc_info is None`.
4. **A fixture trap that would silently invalidate any `DEFAULT_CHARSET` row.**
   `RequestFactory.generic` runs its payload through
   `force_bytes(data, settings.DEFAULT_CHARSET)`, and `force_bytes` **transcodes** `bytes` when
   the encoding is not `utf-8` (`s.decode("utf-8").encode(encoding)`). So under
   `override_settings(DEFAULT_CHARSET="iso-8859-1")` a non-ASCII body byte is rewritten by the
   test client before it reaches the endpoint, and the row measures its own harness. This cost me
   one wrong assertion (`CONTENT_LENGTH` 91 vs `len(data)` 92 was the tell). Every
   `DEFAULT_CHARSET`-overriding row therefore uses an **ASCII** control document, and both
   docstrings say so. The reviewer's own probe files did not hit this because they did not
   override `DEFAULT_CHARSET`.
5. **What the M1 fix does NOT close, stated rather than implied.** A consumer middleware that
   assigns `request.encoding` *after* the view has entered `run` — i.e. from inside a
   `process_view` hook or a decorator between the gate and Django's parse — would still change
   the decode. No such seam exists in Django's ordering for this endpoint (the gate is the first
   statement of `run`, and `process_view` runs before the view), so this is a completeness note,
   not a gap.
6. **Where the declared condition is and is not independently load-bearing.** Because Django
   promotes every *usable* declared charset onto `request.encoding`, condition 2's only
   wire-realistic exclusive territory is the **unusable** codec name. That is why the new
   `..._even_when_django_would_decode_utf8` row forces `request.encoding = "utf-8"` — otherwise
   the two conditions cannot be separated by any request a client can send, and mutation C
   would have failed on the `no-such-codec` rows alone (it fails 5 rows as written, 3 of them the
   forced-encoding ones).
7. Shadow files: none used this pass. `scripts/review_inspect.py` output from the round-2 first
   pass was not re-read; the changed logic is 12 lines across two functions in a file this
   cohort already owns end to end.
8. Temp tests: none written. The reviewer's five probes under `docs/builder/temp-tests/review-2/`
   were **read** but not executed; the two that fall in this cohort
   (`test_encoding_rung_order.py`, `test_get_multipart_content_type.py`) are promoted as the
   permanent rows named in `### Tests added or updated`, so neither is left as the only proof of
   shipped behaviour.

### Floor verification

The change is squarely a Django integration seam (request/body parsing, `MultiPartParser`
encoding resolution, middleware ordering), so it is verified at the supported floor rather than
reasoned about.

- Venv: `/private/tmp/claude-501/-Users-riordenweber-projects-django-strawberry-framework/621704c0-ecb4-4bd1-8c80-bd3c071801fa/scratchpad/floor`,
  built with `uv venv --python 3.10 <path>` then
  `uv pip install --python <path>/bin/python -e . --group dev` and
  `uv pip install --python <path>/bin/python 'django==5.2.0' 'strawberry-graphql==0.316.0'`.
  The explicit `--python` is what keeps `uv` out of the shared `.venv`.
- Resolved versions (`uv pip list --python <path>/bin/python`): **Python 3.10.19**, **django
  5.2**, **strawberry-graphql 0.316.0**, channels 4.3.2, cross-web 0.7.0, asgiref 3.12.1,
  django-filter 26.1, pytest 9.1.1.
- Shared `.venv` re-checked afterwards: still **django 6.0.5 / Python 3.14.2**. Not mutated.
- **Django behaviour verified by execution at the floor, not by reading current.** The six-row
  table in `### The M1 fix` is floor output; the `.venv` run is byte-identical to it. Confirmed
  at the floor by source read as well:
  `MultiPartParser(META, post_data, self.upload_handlers, self.encoding)` at
  `http/request.py:356`, `self._encoding = encoding or settings.DEFAULT_CHARSET` at
  `http/multipartparser.py:113`, `if self.method != "POST":` at `http/request.py:392`,
  and `_set_content_type_params`'s promote-only-if-`codecs.lookup`-succeeds at
  `http/request.py:135-146`.
- Focused rows re-run at the floor:
  `<path>/bin/python -m pytest tests/test_views.py examples/fakeshop/test_query/test_transport_api.py --no-cov`
  -> **210 passed in 33.13s**.
- Failability at the floor: mutation A re-applied and re-run there -> **6 failed, 204 passed**,
  the same 6 rows as on current; restored and `diff -q`-clean.

### Notes for Worker 1 (spec reconciliation)

1. **`## Required spec amendments` item 1 of the FIRST pass is RETRACTED.** The reviewer is right
   (`bld-review-2-w3_review.md`, "Notes for Worker 1" item 1): the wording that pass proposed —
   "the declared top-level `charset`, else `request.encoding`, else `settings.DEFAULT_CHARSET`" —
   describes the **shipped bug**, not the contract. **Do not land it.** Its replacement is
   amendment **P2-1** below. I have not edited the prior section, per the artifact rules.
2. Amendments **P2-2** through **P2-6** below are new this pass (L1, L2, and the table rows the
   conjunctive resolution adds). Every item carries the current wording, where it lives, and a
   recommended replacement, as `BUILD.md` requires.
3. **Nothing in this pass is a plan-level architectural deviation**, but item #1 and #2 of
   `### Notes for Worker 3` are deliberate divergences from the review's *prescribed* remediation
   (a prescribed fix is a hypothesis, not an instruction — `BUILD.md` `## Review rounds`). Both
   are defended with executed evidence; if Worker 1 prefers the literal prescription, the change
   is one token in `_is_multipart_form_post` and two test rows.
4. **Out of this cohort's ownership, recorded so nothing is silently dropped.** Review findings
   L3, L4, L5, L6, the `routers.py` nit, and the WebSocket half of L9 live in `consumers.py` /
   `routers.py` / `tests/test_routers.py` — the concurrent cohorts' files, which this cohort did
   not open. M2, M3 and M5 are likewise not this cohort's. L8 is entirely `README.md`,
   `docs/README.md` and `examples/fakeshop/test_query/README.md`: the first two are on this
   cohort's never-touch list and all three are Slice 5's doc fold-in; none was edited.
5. **L9's cross-cohort recommendation is half-satisfied by this pass.** The reviewer asked for
   *one* decision across the three fail-closed paths that landed this round; the
   `_Probe.CORRUPTED` path now logs at `warning`, so two of the three log and only
   `consumers.py:772-774`'s `Host` denial is still silent. That is the WS cohort's file, and
   whether Channels' own `WebsocketDenier` path should log is a contract question for the
   maintainer (the builder's own A4 already flagged it), not something this cohort can settle.

## Required spec amendments (pass 2)

Every item is a sentence in `docs/spec-046-transport_security-0_0_15.md` (custodian-owned, not
edited here) that the code shipped this pass makes false, over-claiming, or incomplete. Line
numbers are against the working tree at the time of writing; each item also names its section so
the reference survives line drift.

### P2-1. Decision 17, condition 1 — the resolution is CONJUNCTIVE, not a fallback chain (replaces pass 1's item 1)

`docs/spec-046-transport_security-0_0_15.md:2254-2258`, section
`### Decision 17 - Multipart control fields stay Django-parsed, behind a strict loss-detection guard`,
numbered condition 1 (current):

> 1. **The effective multipart form encoding must canonicalize to UTF-8.** The package resolves
>    it the way Django does — the declared top-level `charset` (which Django has already
>    promoted onto `request.encoding` from `content_params`), else `settings.DEFAULT_CHARSET` —
>    and accepts only codec aliases that canonicalize to UTF-8. An explicit `charset=iso-8859-1`,
>    or anything else, is refused with the normal controlled `400`.

Recommended replacement:

> 1. **The effective multipart form encoding must canonicalize to UTF-8** — and so must any
>    declared one. These are **two independent conditions joined with `and`**, not a fallback
>    chain, because Django applies no order between them. The declaration is consulted exactly
>    once, at `HttpRequest._set_content_type_params`, which promotes a *usable* `charset` onto
>    `request.encoding` and silently ignores an unusable one; at parse time `content_params` is
>    never read again, because `HttpRequest.parse_file_upload` hands `MultiPartParser` nothing
>    but `self.encoding` and `MultiPartParser.__init__` resolves
>    `encoding or settings.DEFAULT_CHARSET`. So the package requires **both**:
>
>    (a) the encoding Django will actually use — `request.encoding or settings.DEFAULT_CHARSET`,
>    verbatim the expression those two sites produce between them — canonicalizes to UTF-8,
>    **whatever the client declared**; and
>
>    (b) a declared top-level `charset`, when one is present, canonicalizes to UTF-8 as well.
>
>    Condition (a) is what makes the promise true. Reading the declaration *instead* of it was a
>    bypass: `request.encoding` is Django's documented per-request override, so one line of
>    consumer middleware assigning it overwrites the promotion, and a client declaring
>    `charset=utf-8` while Django decoded Latin-1 got the declaration validated and the override
>    applied — a non-UTF-8-decoded control document reaching `json.loads`, invisible to the
>    replacement-marker check because a Latin-1 decode never fails (spec-046 review round 2, M1).
>
>    Condition (b) is not implied by (a): for a codec name Django cannot load, the promotion does
>    not happen, so `request.encoding` stays `None` and (a) is satisfied by `DEFAULT_CHARSET` —
>    accepting a request whose declaration nobody honoured. `charset=no-such-codec` is refused
>    for that reason, and so is a *usable* non-UTF-8 name, so the two conditions never have to be
>    reasoned about jointly.
>
>    One consequence is worth stating because it looks like an exception and is not: a project
>    that has reconfigured `DEFAULT_CHARSET` away from UTF-8 is refused when nothing else supplies
>    the encoding, and **accepted** when the client declares `charset=utf-8` — because that
>    declaration is promoted onto `request.encoding` and is genuinely what Django decodes with.
>    The gate tracks Django's real behaviour rather than asserting a rung order of its own. An
>    explicit `charset=iso-8859-1`, or anything else non-UTF-8 at either condition, is refused
>    with the normal controlled `400`.

### P2-2. Decision 17 — the encoding guard is scoped to a multipart **POST**, and Decision 7's carve-out with it

Nothing in Decision 17 currently states the method scoping, and the guard's absence of one was a
defect (spec-046 review round 2, L1): a `GET /graphql/?query=...` carrying a stale
`multipart/form-data; charset=iso-8859-1` header was answered `400` even though the view reads no
body on GET and Django decodes no field. Recommended: add after the two numbered conditions in
`### Decision 17`:

> Both conditions apply to precisely the requests whose fields Django decodes, which is a
> **multipart `POST`** and nothing else: `HttpRequest._load_post_and_files` installs an empty
> `QueryDict` without looking at the content type at all unless `request.method` is `"POST"`, so a
> stale `multipart/form-data` `Content-Type` on a GET describes a form nothing will parse, and
> this endpoint reads no body on GET either. The package therefore names the discrimination once —
> `views.py::_is_multipart_form_post` — and both the encoding guard and
> [Decision 7](#decision-7--the-app-level-body-cap-lives-in-the-package-django-view-counted-not-declared)'s
> multipart carve-out read it, so the two cannot drift apart on a request shape. One consequence
> of sharing it: a multipart content type on a method that is neither GET nor POST is no longer
> carved out of the counted check but *counted* like any other body — the stricter direction, and
> harmless, because Django streams no upload for it and Strawberry answers `405`.

### P2-3. Decision 17's table — three rows missing, and one row's mechanism is now attributable

The table at `docs/spec-046-transport_security-0_0_15.md:2292-2299` (`### Decision 17`) has no row
for the shapes the conjunctive resolution decides. Pass 1's item 4 asked for two rows; this pass
supersedes it with four, because the middleware and `DEFAULT_CHARSET` shapes are the interesting
ones:

| multipart `operations` on the wire | Django's decode | package guard | outcome |
|---|---|---|---|
| declared `charset=utf-8-sig` | clean, BOM-eating codec | refused at condition 1(b) | `400` |
| declared charset Django cannot load (`no-such-codec`) | clean, `DEFAULT_CHARSET` silently used | refused at condition 1(b) | `400` |
| declared `charset=utf-8`, middleware set `request.encoding = "iso-8859-1"` | Latin-1, **no `U+FFFD`** | refused at condition 1(a) | `400` |
| no charset, `DEFAULT_CHARSET = "iso-8859-1"` | Latin-1 | refused at condition 1(a) | `400` |
| declared `charset=utf-8`, `DEFAULT_CHARSET = "iso-8859-1"` | **UTF-8** (the declaration was promoted) | passes | **success** |
| GET carrying a stale `multipart/form-data` `Content-Type` | no form is parsed | not a multipart form (P2-2) | **served from the query string** |

The third row is the one the round reopened; the fifth is the boundary that makes the resolution
conjunctive-with-Django's-own-`or` rather than "every value in sight must be UTF-8".

### P2-4. Slice 3 checklist — "one shared mixin helper" is two helpers at two sites, and the encoding half is method-scoped

`docs/spec-046-transport_security-0_0_15.md:221-226`, `## Slice checklist`, Slice 3 (current):

> - [ ] The multipart control-document guard: each view overrides upstream's
>       `parse_multipart` with a two-line delegate over one shared mixin helper, which
>       accepts only an effective form encoding that canonicalizes to UTF-8 and refuses a
>       `operations` / `map` value carrying Django's replacement marker `U+FFFD`, both with
>       the same controlled `400`, **before** either value reaches `parse_json`

Recommended replacement (this supersedes pass 1's item 2 for this site, and folds the method
scoping in):

> - [ ] The multipart control-document guard, at **two** sites on the shared mixin because the
>       two conditions are answerable at different times. The encoding condition needs only
>       headers, so `_enforce_multipart_form_encoding` runs from `_enforce_request_boundary` at
>       the top of `run` — **before** the form is parsed at all and before the CSRF re-entry — and
>       it requires **both** that any declared `charset` canonicalize to UTF-8 and that
>       `request.encoding or settings.DEFAULT_CHARSET`, the value Django actually decodes with,
>       canonicalize to UTF-8. The marker condition needs the decoded form, so
>       `_reject_lossy_multipart_control_fields` runs from a thin `parse_multipart` override per
>       transport and refuses an `operations` / `map` value carrying `U+FFFD` before it reaches
>       `parse_json`. Both refuse with the same controlled `400`, and both apply only to a
>       multipart `POST` (`_is_multipart_form_post`).

### P2-5. Decision 7, probe outcome 3 — the fail-closed refusal now leaves a server-side record

`docs/spec-046-transport_security-0_0_15.md:1244-1250`, `### Decision 7`, probe outcome 3. Pass 1's
item 6 already proposes a replacement for the "the restoring seek then failed" clause and stands;
this item adds the observability sentence to whatever wording lands. Current tail:

> The package **fails closed** with its own controlled rejection rather than reading from an
> unknown offset or guessing a rewind to zero [...] This is the only new refusal, and it is a
> refusal rather than a `500`.

Recommended addition:

> Because that rejection is deliberately **indistinguishable on the wire** from an ordinary
> over-limit one — Decision 9's non-attributability applies to this branch as much as to the rest
> of the boundary — it is the one refusal an operator cannot diagnose from the response. So it is
> the one branch that emits a server-side record: a single `WARNING` on the package logger naming
> the probe outcome and the **class** of the stream that caused it, and nothing on the wire
> changes. A request that was not oversized and was refused anyway means the stream the ASGI
> server or a middleware installed does not report positions coherently, and the log is where
> that is said (spec-046 review round 2, L2).

### P2-6. Edge cases, "GET requests carry no body" — the sentence is now true of both halves and should say so

`docs/spec-046-transport_security-0_0_15.md:2738-2740`, `## Edge cases` (current):

> - **GET requests carry no body.** The cap is a no-op on GET; the `variables` /
>   `extensions` query-param size is a `TODO-ALPHA-047-0.0.16` concern (S4), and the
>   existing `_patched_parse_query_params` shield keeps the body contract off those parses.

Recommended replacement:

> - **GET requests carry no body.** The whole request-body boundary is a no-op on GET, both
>   halves: the cap returns early, and a stale `multipart/form-data` `Content-Type` on a GET is
>   not a form Django decodes, so the multipart encoding guard returns too (P2-2 /
>   `_is_multipart_form_post`). The `variables` / `extensions` query-param size is a
>   `TODO-ALPHA-047-0.0.16` concern (S4), and the existing `_patched_parse_query_params` shield
>   keeps the body contract off those parses.

### P2-7. Acceptance criteria 39 / 41-42 — three rows this pass adds, for the custodian to fold in

`docs/spec-046-transport_security-0_0_15.md:3012-3018` (criterion 39) enumerates the multipart
matrix but not the two deployments the conjunctive resolution decides, and there is no criterion
covering the GET carve-out. Recommended: extend criterion 39's list with

> ; a client-declared `charset=utf-8` **with a consumer middleware that set
> `request.encoding = "iso-8859-1"`** -> `400`, against the shipped `/graphql/` mount and on both
> transports, with the identical request minus the middleware as the `200` control (this is
> review round 2's M1, and the row also asserts that the Latin-1 decode produces **no** `U+FFFD`,
> so the replacement-marker check is proven unable to substitute for it); a project with
> `DEFAULT_CHARSET = "iso-8859-1"` -> `400` with no declaration and **`200`** with
> `charset=utf-8`; and a `GET` carrying a stale `multipart/form-data` `Content-Type` -> served
> from the query string rather than refused.

and note that the async ordering row for criteria 41-42 runs against a probe mount that copies
the package's `csrf_exempt` mark (there is no shipped async fakeshop mount), so only the **sync**
row is deployment-shape evidence — recorded in that row's own docstring per review round 2's L7.
