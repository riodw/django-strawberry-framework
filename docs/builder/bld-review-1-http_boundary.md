# Build: Review round 1 — the HTTP body / parsing boundary findings

Review reference: the maintainer's round-1 transport review — Blocker 1 (the counted body cap materializes the unbounded
body before rejecting it) and High 2 (a package security policy is disabled by the unrelated
upstream-patch kill switch).
Spec reference: `docs/spec-046-transport_security-0_0_15.md` — Decision 7 (the counted cap),
Decision 8 (the deployment-layer co-requirement), Decision 9 (the strict UTF-8 wire contract),
Decision 10 (the rejected UTF-8 BOM); Slice 2 and Slice 3 checklists; Test plan S2 rows 13-18 and
S9 rows 19-24.

Scope note: the WebSocket / router / auth findings (High 3, Medium 4, Medium 5, the numeric window)
are a concurrent agent's — see `bld-review-1-ws_boundary.md`. This artifact touches none of
`routers.py`, `consumers.py`, `auth/`, `utils/`, `exceptions.py`, or `tests/test_routers.py`.

Status: built

## Files touched

| File | Why |
| --- | --- |
| `django_strawberry_framework/_request_body.py` | **New.** The one compatibility helper that touches `HttpRequest._stream` / `_body` / `_read_started`, with the Django-5.2.0-vs-6.0.5 contract it pins written out (Blocker 1). |
| `django_strawberry_framework/views.py` | `_RequestBodyLimitMixin` renamed `_RequestBodyBoundaryMixin` and given the second half of the boundary: the counted check now reads one boolean from `body_exceeds_limit` (Blocker 1), and `parse_json` now owns the strict UTF-8 decode (High 2). New `_JSON_PARSE_REASON`. |
| `django_strawberry_framework/_strawberry_patches.py` | The `data.decode("utf-8")` line is **gone** from `_patched_parse_json`; the `UnicodeDecodeError` translation stays. Docstrings rewritten: "Three lifecycles" becomes two, the gate paragraph no longer claims to carry the wire contract, and the gap-1 live-diagnostic instructions are corrected (they no longer diagnose anything). New `_UPSTREAM_JSON_PARSE_REASON`. |
| `django_strawberry_framework/_cross_web_patches.py` | Docstring only: the gate paragraph and `_patched_body`'s "what raw bytes no longer mean" section no longer say the wire contract travels with `APPLY_UPSTREAM_PATCHES`. |
| `tests/test_views.py` | 11 new rows / row families for Blocker 1's bounded measurement and 7 for High 2's relocated wire policy, including the nine-shape `__cause__` matrix and the patch-opted-out composition; 2 existing rows re-witnessed; the mixin-shape row renamed. |
| `tests/test_strawberry_patches.py` | The nine-shape matrix and the "delegate receives a `str`" attribution row **deleted** (they asserted the old ownership); replaced by a row asserting the *opposite* — upstream's `bytes` semantics survive here — plus a behavioral opt-out proof. `views` import dropped. |
| `tests/test_cross_web_patches.py` | The two rows that followed the adapter's bytes into `_patched_parse_json` now follow them into the package view, which is what actually refuses them. |
| `examples/fakeshop/test_query/test_transport_api.py` | New live section: the wire contract holds on both transports with `APPLY_UPSTREAM_PATCHES = {"strawberry": False}`, and the workaround the switch does own is genuinely off in the same state. Four docstrings re-attributed. |
| `examples/fakeshop/test_query/test_products_api.py` | Comment block and two docstrings re-attributed to the view boundary. No assertion changes — every row still passes unchanged, which is itself the point. |
| `docs/builder/bld-review-1-http_boundary.md` | This artifact. |

`conf.py` was **not** touched: no new setting is required. The cap's configuration surface
(`MAX_REQUEST_BODY_BYTES`, the `max_request_body_bytes=` kwarg, the precedence ladder) is unchanged,
and the wire contract has no knob by design — a security policy a consumer can switch off is the
finding, not the fix.

## Blocker 1 — the cap measures instead of materializing

### What was actually wrong

`_enforce_request_body_limit` ended with `if len(request.body) > limit`. `HttpRequest.body`
(verified by reading `django/http/request.py` at both supported versions, not from memory):

- **Django 6.0.5** — checks `CONTENT_LENGTH` against `DATA_UPLOAD_MAX_MEMORY_SIZE`, then, *if the
  stream is seekable*, seeks to the end and checks the real buffered size, then reads.
- **Django 5.2.0** — checks `CONTENT_LENGTH` only, then reads. **No seekable-stream check exists at
  the floor.**

So at the required floor, an absent `Content-Length`, an understated one, or
`DATA_UPLOAD_MAX_MEMORY_SIZE = None` left the read genuinely unbounded, and the `>` comparison could
only fire after the allocation. On ASGI the read also copies back a `SpooledTemporaryFile` that
`ASGIHandler.read_body` may already have rolled to disk — synchronously, on the event loop, for
`AsyncDjangoGraphQLView`.

### Design: one helper, three branches, in descending order of cheapness

`_request_body.py::body_exceeds_limit(request, limit) -> bool`. `views.py` names none of the three
private attributes; it reads one boolean and decides policy (which limit, what the `413` says).

1. **`_body` already present** → `len(request._body) > limit`. This is the
   `CsrfViewMiddleware`-read-a-urlencoded-body case: the allocation happened before `run` was
   entered and cannot be undone, so the only thing left is to refuse to *process* it.
2. **Stream measurable without reading** → `seek`/`tell` probe, original position restored, nothing
   read. This is the ASGI spool, and it is the branch that makes an over-limit ASGI request cost no
   allocation at all.
3. **Neither** → bounded chunked read to at most `limit + 1` bytes.

Two states return `False` without measuring, both documented at the call site: no `_stream` at all
(a synthetic `HttpRequest`, which sets neither `_stream` nor `_read_started` — only `WSGIRequest` /
`ASGIRequest` do), and `_read_started` true with no `_body`. In the second, `HttpRequest.body` itself
raises `RawPostDataException`, so nothing downstream can process the request either — there is no
bypass to close, and the previous implementation's behavior (calling `request.body` and surfacing
*another* component's exception as a body-limit failure) was strictly worse.

### The seekability probe, and the measurement that forced its shape

```
seekable = getattr(stream, "seekable", None)
if callable(seekable) and not seekable():
    return None
try:
    position = stream.tell()
except (AttributeError, OSError, ValueError):
    return None
```

Measured, not assumed:

| stream | `hasattr(seekable)` | `seekable()` | `tell()` |
| --- | --- | --- | --- |
| `LimitedStream` (WSGI, `AsyncRequestFactory`) — py3.10 **and** py3.14 | True | **False** | raises `io.UnsupportedOperation` |
| `SpooledTemporaryFile` (ASGI) — **py3.10.19** | **False** | — | 0, and `seek(0, SEEK_END)` returns `4096` |
| `SpooledTemporaryFile` (ASGI) — py3.14.2 | True | True | 0 |

`SpooledTemporaryFile` only became an `io.IOBase` subclass in 3.11, so **at the supported Python 3.10
floor the ASGI body file does not declare `seekable` at all**. A probe written as
`if stream.seekable():` would have `AttributeError`-ed there; one written as
`if getattr(stream, "seekable", lambda: False)():` would have silently dropped the ASGI spool onto
the read branch at exactly the interpreter this card protects — passing on the dev stack, losing the
guarantee where it matters. Hence: believe `seekable()` when the method exists (a `seek` on a stream
that says no is undefined, and a silently-misbehaving one would corrupt the read position), and
otherwise let `tell()` decide, which `io.UnsupportedOperation` — an `OSError` *and* a `ValueError`
at once — reports for a pipe-backed stream. Once `tell()` has answered, `seek` is trusted unguarded,
exactly as Django 6.0's own `body` trusts it.

### The bounded read, and the bug the live suite caught

```
while read_so_far <= limit:
    chunk = request.read(min(_READ_CHUNK_BYTES, limit + 1 - read_so_far))
    ...
if read_so_far > limit:
    return True            # chunks never joined
stream.close()
request._stream = BytesIO(b"".join(chunks))
request._read_started = False
return False
```

`limit + 1` is the least information that distinguishes "exactly at the limit" (legal, `>` not `>=`)
from "over it". Over the limit the collected chunks are **never joined**, so no over-limit `bytes`
value is allocated even transiently, and the remainder of the request is left unread. Reads go
through `request.read` rather than `stream.read` so Django keeps its own bookkeeping
(`_read_started`, `OSError` → `UnreadablePostError`).

The first version of the allowed path wrote `request._body = b"".join(chunks)` — mirroring what
`HttpRequest.body` leaves behind, which is what the review's step 4 ("preserve those bytes in the
request shape Django expects") most literally suggests. **That was a real regression, and the live
suite caught it**:
`test_transport_api.py::test_the_two_body_ceilings_are_distinguishable_by_the_response_they_produce`
went 400 → 200. Pre-filling the cache makes `HttpRequest.body` short-circuit, which silently
disables **Django's own** `DATA_UPLOAD_MAX_MEMORY_SIZE` ceiling for every request that took the
bounded branch. A project whose Django knob is lower than the package cap would have lost it.

The fix hands the bytes back as a *stream* instead: close the consumed one, install a rewound
`BytesIO` over the exact bytes, and reset `_read_started` to the `False` the request was constructed
with — which is true again, because the installed stream is complete and unread. `HttpRequest.body`
then runs in full: byte-for-byte the original bytes, Django's ceiling applied in whatever form the
installed Django implements it, and on 6.0 the substituted `BytesIO` even satisfies its
seekable-size check. **This module now never writes `_body`.** A package cap adds a ceiling; it must
not remove one.

### Alternatives rejected

- **Keep `len(request.body)` and rely on `DATA_UPLOAD_MAX_MEMORY_SIZE`.** Rejected: it is a
  project-wide knob shared with uploads (the spec's own Decision 7 rationale for not inheriting it),
  it is `None`-able, and at the 5.2.0 floor it only ever compares `CONTENT_LENGTH` — the one number
  the review's threat model says is absent or lying.
- **Copy Django 6.0's `body` implementation into the package.** Rejected: a full reimplementation of
  a property whose behavior differs across supported versions, and it would still have to make the
  same `_body`-vs-`_stream` decision. Probing the size and letting Django's own property do the
  reading is strictly less code and strictly more forward-compatible.
- **Reject with `RequestDataTooBig` / re-check `DATA_UPLOAD_MAX_MEMORY_SIZE` inside the helper.**
  Rejected once the stream hand-back landed: duplicating Django's ceiling logic would drift the
  moment Django changes it (it already differs 5.2 → 6.0). Leaving the property in charge means
  there is nothing to keep in sync.
- **A single `request.read(limit + 1)` instead of a chunk loop.** Bounded, but it turns one hostile
  request on a mount with a large configured cap into one large allocation attempt. The 64 KiB chunk
  ceiling costs two extra `read` calls on a typical body.
- **Spreading `_stream` / `_body` / `_read_started` across the two view classes.** Explicitly
  forbidden by the review, and correct: the version-divergent knowledge is the whole risk, and it now
  lives in one module docstring next to the code that depends on it.
- **A `pragma: no cover` on the deferral branches.** Not needed — every branch is reached by a real
  row (see per-test intent).

### Per-test intent (`tests/test_views.py`)

Stand-ins are module-level and each documents which production stream it *is*, not merely what it
does:

- `_UnreadableSpool(tempfile.SpooledTemporaryFile)` — the genuine ASGI body-file class with `read`
  replaced by an assertion. Subclassing rather than faking is what makes the rows statements about
  production: `seek` / `tell` behave exactly as they do live, and the 3.10-vs-3.11 `seekable`
  difference is *inherited*, so whichever capability path the running interpreter takes is the one
  exercised.
- `_RecordingNonSeekableStream` — declares `seekable() -> False` like `LimitedStream`, and records
  every `read` size and the running delivered total, which is what turns "bounded" into an assertion.
- `_UndeclaredSeekableStream` — no `seekable`, working `seek`/`tell`: the py3.10 spool shape,
  reproduced so the floor's behavior stays asserted from any interpreter.
- `_UnmeasurableStream` — no `seekable`, `tell()` raises `io.UnsupportedOperation`: a raw WSGI pipe.
- `_asgi_request` — a real `ASGIRequest` from `AsyncRequestFactory` with `_stream` replaced by a
  spool. That moves the request *closer* to production, not further: the `LimitedStream` the factory
  installs is the test-client artifact, and a spooled file is what `ASGIHandler.create_request`
  actually assigns.

| Row | What it proves that nothing else can |
| --- | --- |
| `test_a_seekable_over_limit_body_is_refused_without_ever_being_read` (2 view classes x in-memory/rolled-to-disk x absent/understated `Content-Length` = 8) | The review's headline regression. The `413` is reached with `read` wired to raise, so it cannot pass unless the rejection is size-probe-only. Rolled-to-disk covers the case where the bypassed read is also a *disk* read; both `Content-Length` shapes are the ones the declared gate structurally cannot see. Position restored and `_body` absent stop the row from degrading into a bare status check. |
| `test_a_seekable_under_limit_body_reaches_strawberry_byte_for_byte` | The control that makes the above meaningful, and the seekable branch's own risk: a probe that forgot to rewind would leave every legitimate body empty. Payload carries NULs and high bytes, so a stray decode / text-mode round trip would fail it. |
| `test_an_undeclared_seekable_stream_is_still_size_probed_rather_than_read` | The py3.10 floor's spool shape takes the probe, not the read. Empty `requested` list is the evidence. |
| `test_a_non_seekable_over_limit_body_reads_at_most_one_byte_past_the_limit` | `delivered == limit + 1` exactly, `max(requested) <= limit + 1`, bytes demonstrably still unread, no `_body`. This is the "no allocation/read larger than `limit + 1`" row. |
| `test_a_non_seekable_under_limit_body_is_handed_back_as_a_rewound_stream` | The `_body`-vs-`_stream` decision, pinned: `_body` absent, `_read_started` False, `_stream` a `BytesIO`, old stream closed, and then `request.body` / `request.read()` both answering byte-for-byte. |
| `test_an_unmeasurable_stream_falls_back_to_the_bounded_read` | "Unmeasurable" resolves to "read it", never to "assume it fits". |
| `test_a_body_already_cached_by_middleware_is_measured_from_the_cache_and_refused` | The middleware-prepopulated `_body` row: refused from the cache, with an unreadable stream proving the cache — not a re-read — is what was measured. The under-limit half shows it is a measurement, not a blanket rejection. |
| `test_the_cap_defers_on_a_stream_some_other_component_already_consumed` | The cap does not translate another component's `RawPostDataException` into a misleading `413`; the honest error still reaches whoever asks for the body. |
| `test_the_cap_defers_on_a_request_that_carries_no_stream_at_all` | A hand-built `HttpRequest` has no `_stream`, and Django tolerates that, so the cap must too. |
| `test_a_declared_over_limit_request_is_refused_without_touching_the_stream` (rewritten) | Same intent as before; the witness changed because the counted path no longer leaves a `_body`. The stream object's identity is now the discriminator — unchanged on the declared-gate rejection, replaced on the counted control. |

## High 2 — the wire policy moved to the view; the kill switch kept only the bug fixes

### Design

The strict decode now lives on `views.py::_RequestBodyBoundaryMixin.parse_json`:

```
if isinstance(data, bytes):
    try:
        data = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(400, _JSON_PARSE_REASON) from exc
return super().parse_json(data)
```

Four properties make this the right seam rather than a second ad-hoc hook:

1. **One owner for both transports.** The mixin is first in both views' bases, so it is the MRO
   owner of `parse_json` for sync and async alike — no duplication, no possible drift. `super()`
   delegates to upstream's `parse_json` (patched or not), so upstream remains the only JSON parser in
   the path; nothing is reimplemented.
2. **`str` passes through untouched**, by identity — the GET `variables` / `extensions` parses and
   the multipart `operations` / `map` form fields arrive already decoded by Django.
3. **It composes with either patch state.** With the patch installed the delegate only ever receives
   `str`; with it un-installed, `super().parse_json` is upstream's own, whose `except
   json.JSONDecodeError` raises the byte-identical `400` for the five inherited rejections. The whole
   nine-shape matrix — including which mechanism fired — is unchanged either way.
4. **It is the same boundary as Blocker 1.** The cap decides which bytes reach the parse; the parse
   decides how those exact bytes become text. One mixin, one subject: the raw request body.

`_patched_parse_json` keeps its `UnicodeDecodeError` translation, which is a genuine upstream bug
fix and is still reachable — `json.loads(bytes)` raises it whenever the bytes are undecodable under
the encoding `detect_encoding` picks — and therefore stays opt-out-able. Its module docstring's
"Three lifecycles, not one" section became "Two lifecycles, and one that left", with the
consequence stated plainly: **the module can now be deleted outright once both upstream bugs
retire**, and the migration is the only reason that deletion is safe.

### What upstream-mounted consumers now get, deliberately

With the decode removed from the patch, `_patched_parse_json` no longer narrows encodings. Measured
on both stacks: `json.loads` accepts UTF-16 (BOM and BOM-less), UTF-32 (BOM and BOM-less), and a
UTF-8 BOM as `bytes`. So a consumer who mounts `strawberry.django.views.GraphQLView` directly keeps
upstream's RFC 8259 semantics — which the review explicitly sanctions ("Consumers mounting an
upstream view directly may retain upstream semantics"), and which
`test_patched_parse_json_leaves_upstreams_bytes_semantics_alone` now pins as a *requirement*, so the
ownership split cannot silently collapse back into one site.

### The duplicated wire reason, and why it is not an import

`"Unable to parse request body as JSON"` is now named in two places: `views._JSON_PARSE_REASON` and
`_strawberry_patches._UPSTREAM_JSON_PARSE_REASON`. This is deliberate, and the alternatives were
considered:

- **`_strawberry_patches` imports it from `views`** — rejected. It would make `apps.py::ready()`
  import `views.py` (and `strawberry.django.views`) at every startup for every consumer including
  channels-only ones, and it would break the patch module's deliberate design of surviving import
  with a missing dependency long enough for `apply()` to report the precise unsupported shape.
- **A third module owning the literal** — rejected: whichever module holds it becomes an import
  `_strawberry_patches` must keep, defeating the deletability the lifecycle split just bought.
- **What is actually load-bearing** is that the two stay byte-identical *and* identical to
  upstream's. `test_the_wire_reason_is_upstreams_own_parse_json_literal` asserts both against what
  upstream's captured `parse_json` really raises, so an upstream message change fails loudly rather
  than splitting one contract into two. That is a stronger guard than an import, which would only
  have kept our two copies in step with each other.

### Alternatives rejected

- **Override `decode_json` instead of `parse_json`.** Rejected: a `UnicodeDecodeError` raised there
  lands in upstream's `except json.JSONDecodeError`, which does not catch it — so the translation
  would depend on the patch being installed, i.e. exactly the coupling being removed.
- **Reimplement Strawberry's parser in the package.** Rejected by the review and on the merits:
  adding a second parser to close a parser differential is self-defeating (the spec's own Decision 9
  rationale). The override decodes and delegates.
- **A `STRICT_UTF8_BODY` setting so consumers can opt out of the policy too.** Rejected: a security
  policy a consumer can switch off is the finding. AGENTS.md also forbids adding settings keys
  speculatively.
- **Leaving the decode in the patch and merely documenting the consequence.** That is the shipped
  state the review rejected as an architectural ownership defect, and it is right: an upstream shape
  change can *force* a consumer to disable the patch.

### Per-test intent (High 2)

| Row | Tier | Intent |
| --- | --- | --- |
| `test_the_package_view_rejects_every_non_utf8_wire_shape` (9 shapes x 2 views) | package | The relocated matrix. `__cause__` is the only discriminator, because status and message are identical across all nine by design; pinning the five `json.JSONDecodeError` rows matters because that rejection is *inherited*, so a future stdlib tolerating U+FEFF or NUL-studded text would turn them into 200s with no package change to review. |
| `test_the_wire_contract_holds_with_the_upstream_patches_opted_out` (9 x 2) | package | The finding, executable — the identical matrix with the patch pair un-installed and the setting set. |
| `test_the_utf8_wire_contract_survives_the_upstream_patch_kill_switch` (3 bodies) | **live** | The review's required regression: the package view **mounted**, `{"strawberry": False}`, UTF-16 / UTF-32 / UTF-8-BOM all 400. The valid-UTF-8 control in the same opted-out state is what makes the rejection attributable rather than a broken-endpoint artifact. |
| `test_the_async_view_keeps_the_utf8_wire_contract_with_the_patch_opted_out` (3) | **live** | The transport where a gated contract would have meant silent *success*, not a 500: `_cross_web_patches` touches only the sync adapter, so async bytes reach `parse_json` raw with or without any patch. |
| `test_the_upstream_bug_workaround_still_respects_its_own_opt_out` | **live** | What stops a bad fix. The two rows above would also be satisfied by moving everything somewhere ungated; this asserts a JSON scalar body is a 500 with the patch off and a 400 with it on, i.e. the envelope guard really is a switchable workaround. `raise_request_exception=False` is what lets the unhandled case be observed as the 500 a deployment would return. |
| `test_the_gated_workarounds_really_stop_hardening_when_opted_out` | package | The same claim at unit level, on `BaseView` directly: scalar and non-object-batch bodies pass straight through and an undecodable body raises the raw `UnicodeDecodeError`. |
| `test_both_package_views_resolve_parse_json_to_the_one_shared_mixin_method` | package | Replaces the old `owners == [BaseView]` row with a strictly stronger one: the exact two-owner MRO chain in order, so an intermediate class defining `parse_json` on one transport fails immediately, and the mixin is pinned as *delegating* rather than replacing. |
| `test_the_package_view_hands_upstream_a_str_for_a_bytes_body` / `..._passes_a_str_body_through_by_identity` / `..._parses_valid_utf8_including_multibyte_unchanged` | package | The attribution and success-path rows, relocated from the patch module. Identity (not equality) on the `str` path rules out an incidental encode/decode cycle; the multibyte body carries a real `C3 A9` so the contract is pinned as UTF-8 rather than ASCII. |

### Tests retired or re-aimed, and why

Swept `tests/`, `examples/fakeshop/`, and every package-tier module for assertions of the old
ownership:

- **Deleted** `tests/test_strawberry_patches.py::test_patched_parse_json_rejects_every_non_utf8_wire_shape`
  (9 rows) — it asserted the patch module owns the encoding narrowing. After the move the same call
  *succeeds* for 6 of its 9 inputs, because `json.loads` auto-detects `bytes`. Relocated to
  `tests/test_views.py` against the view, which is where the property now lives. Not a duplicate:
  the patch module's replacement row asserts the inverse property on purpose.
- **Deleted** `..._hands_the_delegate_a_str_for_a_bytes_body` — same reason; the equivalent
  attribution now belongs to the view boundary and is there.
- **Deleted** `..._test_both_package_views_resolve_parse_json_to_the_one_patched_wrapper` — moved
  and strengthened into `tests/test_views.py` (see table). It is a statement about the package view
  surface, which is now that file's subject.
- **Re-aimed** `tests/test_cross_web_patches.py::test_body_returns_raw_bytes_for_utf8_bom` and
  `..._for_utf16_le_without_bom` — their raw-bytes half is unchanged; their "and these bytes reach a
  400" half now goes through the package view. For the BOM row this is load-bearing rather than
  cosmetic: `json.loads` on `bytes` detects `utf-8-sig` and strips the BOM itself, so the patch
  module alone would have *accepted* that body.
- **Kept unchanged** every live row in `test_products_api.py` (UTF-16, UTF-16-LE, UTF-8-BOM, the
  four remaining multi-byte shapes, invalid-UTF-8, raw binary, the multibyte success control). That
  they all still pass with no edit is the clearest evidence the wire behavior is byte-identical after
  the move; only their prose attribution changed.
- **Kept unchanged** `test_apply_no_ops_when_toggle_disabled` and
  `test_apply_no_ops_when_strawberry_dependency_opted_out` — the install-gate rows the review asked
  to preserve, now joined by the two behavioral opt-out rows above.
- **No package-tier stand-in was left as a duplicate of a now-live path**, and none needed deleting
  for that reason: the relocated rows assert `__cause__`, which no live response exposes (status and
  message are identical across all nine shapes by design).

## Verification transcript

Formatting and layout, on the touched files only (`check_trailing_commas.py` defaults to repo-wide
auto-fix, so paths are always explicit):

```
$ uv run ruff format django_strawberry_framework/ tests/test_views.py
102 files left unchanged
$ uv run ruff check django_strawberry_framework/ tests/test_views.py
All checks passed!
$ uv run ruff format examples/fakeshop/test_query/ && uv run ruff check examples/fakeshop/test_query/
19 files left unchanged
All checks passed!
$ uv run python scripts/check_trailing_commas.py --check <the 9 touched .py files>
exit=0
```

ASCII-only re-verified per file with an explicit `ord(c) > 127` scan: no non-ASCII lines in
`_request_body.py`, `views.py`, `_strawberry_patches.py`, `_cross_web_patches.py`, or
`tests/test_views.py`.

Package tier, current stack (Python 3.14.2 / Django 6.0.5 / strawberry 0.316.0):

```
$ uv run pytest tests/test_views.py tests/test_strawberry_patches.py tests/test_cross_web_patches.py --no-cov -q
156 passed in 3.28s
```

Live tier:

```
$ uv run pytest examples/fakeshop/test_query/test_transport_api.py examples/fakeshop/test_query/test_products_api.py --no-cov -q
154 passed in 60.05s (0:01:00)
```

Whole suite (`pytest.ini` `testpaths`, so the known narrowed-invocation `Section`-seed trap does not
apply). This run also carries the concurrent WS-boundary agent's changes:

```
$ uv run pytest --no-cov -q
4975 passed, 40 skipped in 127.41s (0:02:07)
```

The **Django 5.2.0 / Python 3.10.19 floor**, in the isolated `/tmp/dsf-floor-r5` venv (never the
shared `.venv`). That venv has no `xdist` / `pytest-cov`, so `pytest.ini`'s `addopts` is neutralized
with `-o addopts=""`:

```
$ /tmp/dsf-floor-r5/bin/python -c "import django; print(django.VERSION)"
(5, 2, 0, 'final', 0)
$ /tmp/dsf-floor-r5/bin/python -m pytest tests/test_views.py tests/test_strawberry_patches.py tests/test_cross_web_patches.py -o addopts="" -q --no-header
156 passed in 0.42s
$ /tmp/dsf-floor-r5/bin/python -m pytest examples/fakeshop/test_query/test_transport_api.py -o addopts="" -q --no-header
36 passed in 34.66s
```

The floor run includes the **live** transport tier, which is the strongest available floor evidence:
the seekable-probe branch there is reached through a real `ASGIHandler` against a real
`SpooledTemporaryFile` that does not declare `seekable`, i.e. the capability path that only exists at
the floor.

### The regression that was proved, then fixed

Not a claim — an observed failure. With the allowed bounded read pre-filling `request._body`:

```
$ uv run pytest examples/fakeshop/test_query/test_transport_api.py --no-cov -q
>       assert djangos.status_code == 400
E       assert 200 == 400
E        +  where 200 = <HttpResponse status_code=200, "application/json">.status_code
FAILED ...::test_the_two_body_ceilings_are_distinguishable_by_the_response_they_produce
1 failed, 35 passed in 138.98s
```

`DATA_UPLOAD_MAX_MEMORY_SIZE = 64` against a mount whose cap is 8 MiB used to be Django's rejection;
pre-filling the cache made `HttpRequest.body` short-circuit past it. Handing the bytes back as a
rewound stream restored it, and the row passes unmodified — the shipped live test caught the
regression, which is why the fix needed no new test of its own.

### The Blocker-1 rows were proved to fail against the old implementation

`test_a_seekable_over_limit_body_is_refused_without_ever_being_read` fails on the pre-change
`len(request.body) > limit` with `AssertionError: the cap read a stream it was supposed to
size-probe`, raised from `_UnreadableSpool.read` — i.e. the row's negative witness is genuinely
load-bearing and not vacuous.

### The pre-move behavior of the deleted rows was measured, not assumed

```
$ uv run python .../probe1.py       # and the same script on /tmp/dsf-floor-r5/bin/python
utf-8-bom -> {'a': 1}
utf-16-le-no-bom -> {'a': 1}
utf-16-with-bom -> {'a': 1}
utf-32-with-bom -> {'a': 1}
invalid-byte -> RAISE UnicodeDecodeError
raw-binary -> RAISE JSONDecodeError
```

Identical on 3.10.19 and 3.14.2. This is what made the nine-row matrix's relocation mandatory rather
than optional, and what `test_patched_parse_json_leaves_upstreams_bytes_semantics_alone` now pins.

### Read-only source probes

Django's own `http/request.py` was read at both versions rather than recalled:
`.venv/.../django/http/request.py` (6.0.5) has the `_check_data_too_big` + `self._stream.seekable()`
pair inside `body`; `/tmp/dsf-floor-r5/.../django/http/request.py` (5.2.0) has only the inline
`CONTENT_LENGTH` comparison. `_read_started = False` appears in `core/handlers/asgi.py` and
`core/handlers/wsgi.py` and in neither `HttpRequest.__init__`, at both versions.

## Notes for the spec custodian

The spec is not edited here (custodian-only). Required amendments, with the sentences that are now
wrong, are in the report handed to the dispatcher; the headline items are Decision 9's title and
anchor (`...-is-enforced-once-in-_patched_parse_json`, referenced from five places), Decision 9's
shared-gate paragraph, Decision 7's "Pre-reading the stream in chunks and stashing `request._body`"
rejected alternative (now half-required, half-rejected-for-a-different-reason), and the Slice 3
checklist line.

`docs/TREE.md` will need the new `django_strawberry_framework/_request_body.py` module at Slice 5's
doc-wrap regenerate (`scripts/build_tree_md.py`); it is deliberately not regenerated here, since
Slice 5 is unbuilt and TREE.md is script-rendered.

---

# W3 residual remediation

Review reference: `docs/builder/bld-review-1-w3_review.md` — findings W3-1 (Medium), W3-2
(Low/Medium), W3-3, W3-4, W3-6. W3-5 is note-only and no action was taken (the two test trees are
deliberately separate; both copies of `_strawberry_patch_opted_out` still restore both methods).

Baseline at start: `4977 passed, 40 skipped`. After: **`4991 passed, 40 skipped`** (+14 rows).

## Files touched in this pass

| File | Why |
| --- | --- |
| `django_strawberry_framework/_request_body.py` | W3-1. `_measured_remaining` no longer clamps; a probed count of zero or less is a measurement failure and returns `None`. |
| `django_strawberry_framework/views.py` | W3-2. New `_RawBodyRequestAdapter`, installed as `DjangoGraphQLView.request_adapter_class`. W3-6 nit 1 in the mixin docstring. |
| `django_strawberry_framework/_strawberry_patches.py` | W3-2. The "whatever this setting says" paragraph rewritten: the gate governs what a consumer gets on **upstream's own** view; a package view owns both halves of the contract. |
| `django_strawberry_framework/_cross_web_patches.py` | W3-2. Same re-scoping, plus a new "Who this patch is for" section and a corrected `_patched_body` docstring (a package view never reaches that getter). |
| `django_strawberry_framework/conf.py` | W3-2 fallout, comment only: `UPSTREAM_PATCH_DEPENDENCIES`'s note said disabling one half "leaves the sync transport unfixed", which my change made ambiguous. Out of the dispatched file list — flagged in the report. |
| `django_strawberry_framework/exceptions.py` | W3-3. `describe_value`'s "single owner" claim replaced by the measured scope. |
| `django_strawberry_framework/consumers.py` | W3-4. `resolved_revalidation_window`'s stated reason for rejecting `inf` corrected, and the accepted astronomical window disclosed. |
| `tests/test_views.py` | W3-1: two lying-stream stand-ins + 3 rows x 2 views. W3-2: 2 adapter rows. W3-6 nit 2: `_asgi_request`. |
| `tests/test_routers.py` | W3-4: two accepted-window rows and a corrected Test-23 docstring. |
| `examples/fakeshop/test_query/test_transport_api.py` | W3-2: `_every_upstream_patch_opted_out`, an `/upstream-graphql/` attribution mount, 3+1 live rows. |

## W3-1 — the fail-open clamp, and why the fix is wider than the one proposed

**Reproduced first, on both directions W3 named** (declared-seekable stand-ins, `limit = 256`,
4096-byte body):

```
seek(0,END) under-reports  _measured_remaining -> 0
                           exceeds=False reads_by_the_cap=0 -> request.body materialized 4096 bytes (unbounded: True)
tell() over-reports        _measured_remaining -> 0
                           exceeds=False reads_by_the_cap=0 -> request.body materialized 4096 bytes (unbounded: True)
```

**The recommended guard does not close its own second case.** W3's suggested fix is
`if end < position: return None`. The realistic under-reporting shape is a stream that can report a
position but cannot take one — `seek` returns the offset it was handed and never moves — which is
exactly what the module's own comment warns about and is reachable through the `tell()` capability
fallback at the py3.10 floor. That stream answers `seek(0, SEEK_END) -> 0` from `position == 0`, so
`end < position` is **False** and the clamp's fail-open survives the patch. Verified above: the
under-reporting row measures `0`, not a negative.

The root cause is one step up from the arithmetic: **`0` is the one answer a size probe must never
hand back**, because `body_exceeds_limit` reads it as "within the limit" while nothing has been read,
which is precisely what the docstring two lines up forbids ("`None` means 'ask the bounded read
instead', never 'the body is empty'"). So the guard is on the *answer*, not on one spelling of an
incoherent pair:

```python
    remaining = end - position
    if remaining <= 0:
        return None
    return remaining
```

That covers `end < position` (both of W3's directions when the position is non-zero) **and**
`end == position` (the "empty" answer, which is the fail-open value itself). Verifying a zero costs
exactly one `read` call — a genuinely empty body is the cheapest request there is — so the
fail-safe direction is affordable, and the docstring's promise becomes enforced rather than
intended. The position is restored unconditionally *before* the pair is judged, so the bounded read
that follows starts where the request started.

Post-fix, measured:

```
seek(0,END) under-reports  _measured_remaining -> None   exceeds=True  REFUSED (413); one bounded read
tell() over-reports        _measured_remaining -> None   exceeds=False -> request.body is 0 bytes (bounded)
```

The over-reporting direction is honestly disclosed rather than papered over, and the row says so:
once a stream lies about *where it is*, the restored position lands past the end and the request
ends up with an **empty** body (a `400` at the parse, never a bypass). Recovering the true bytes is
impossible, and rewinding to zero instead would corrupt a stream that was legitimately mid-position.
The security property — the application never receives bytes the cap did not count — holds in both
directions.

What no probe can catch is stated in the docstring instead of being implied away: a *plausible* lie
(an `end` that is wrong but still ahead of `position`) is indistinguishable from a measurement
without reading the bytes it describes, which is the work the probe exists to avoid.

### The sibling-expression audit W3 asked for

Every non-branch expression in `_request_body.py` that could convert an untrusted input into an
allow, checked at the raise site:

| Expression | Direction on a hostile / broken input |
| --- | --- |
| `max(end - position, 0)` | **Fail-OPEN.** The finding. Fixed. |
| `len(request._body) > limit` | Fail-loud (a non-sized `_body` raises); no allow. |
| `getattr(request, "_read_started", False)` | Absent -> "not started" -> proceeds to **measure**, not to allow. |
| `stream is None -> return False` | Documented deferral (a synthetic `HttpRequest`); audited and accepted by W3 as branch 4. |
| `callable(seekable) and not seekable()` | A stream lying "unseekable" -> bounded read. Fail-bounded. |
| `except (AttributeError, OSError, ValueError): return None` | -> bounded read. Fail-bounded. |
| `min(_READ_CHUNK_BYTES, limit + 1 - read_so_far)` | The loop guard keeps `read_so_far <= limit`, so the second term is >= 1; it cannot degenerate into `read(0)` (which would look like EOF and under-count). |
| `if not chunk: break` | A stream returning `b""` early ends the count, but the withheld bytes are also the bytes it never delivers — the installed `BytesIO` holds exactly the counted prefix. Truncating, not bypassing. |
| `read_so_far += len(chunk)` | A stream returning MORE than requested pushes past `limit` -> refused. Fail-closed. |

One expression had the blind spot; it is now a branch, so the `fail_under = 100` gate can see both
arms.

## W3-2 — outcome (a): the package view owns its body source

**Chosen: (a), fixed properly.** Option (b) was not needed and would have been the wrong answer
here, because the fix is neither a fork of the adapter nor a reimplementation of upstream's HTTP
engine — it is upstream's own documented per-view seam.

`strawberry.http.sync_base_view` reads the request body at exactly **one** site,
`data = self.parse_json(request.body)` (grepped: the only `.body` read in `strawberry/http/`), and
which object answers that is `self.request_adapter_class`, a class attribute every integration sets
(`django`, `flask`, `asgi`, `aiohttp`, `quart`, `chalice`, `sanic`, `litestar`, `fastapi`,
`channels`). So:

```python
class _RawBodyRequestAdapter(DjangoHTTPRequestAdapter):
    @property
    def body(self) -> bytes:
        return self.request.body


class DjangoGraphQLView(_RequestBodyBoundaryMixin, GraphQLView):
    request_adapter_class = _RawBodyRequestAdapter
```

One property, inherited from upstream's own adapter so every other member stays upstream's. The
async view needs no counterpart — `AsyncDjangoHTTPRequestAdapter.get_body` already returns
`self.request.body` untouched, which is why the contract never degraded there — and a row pins that
so the asymmetry cannot silently become a gap.

This completes High 2's premise rather than restating it. The finding was that a permanent security
policy must not be reachable only through a switchable workaround; owning the *decode* was only half
of that, because **a decode the bytes never reach is not an enforcement**. Both halves are now
view-owned, and the patch state cannot matter to a package mount even by install order: the subclass
property shadows the (patched or unpatched) class attribute by identity.

Measured before and after, live, on mounted views with `APPLY_UPSTREAM_PATCHES = False`:

```
before:  SYNC utf-16-bom -> 500   utf-32-bom -> 500   (assert 500 == 400, x3 rows)
after:   SYNC utf-16-bom -> 400   utf-32-bom -> 400   utf-8-bom -> 400   valid -> 200
```

The dishonest sentences are gone, and their replacements are load-bearing and tested rather than
merely softened: `_strawberry_patches.py` and `_cross_web_patches.py` now scope the gate to what a
consumer gets on **Strawberry's own** view and name the two view-owned halves;
`_cross_web_patches.py` gains a "Who this patch is for" section; `_patched_body`'s "what raw bytes
no longer mean on a package view" section was factually wrong after the change (a package view never
reaches that getter) and was rewritten.

`_cross_web_patches.py` keeps its full purpose — hardening the installed Strawberry for consumers who
mount its own view — and the live attribution row now records what that is worth, including the part
nobody had pinned live: with the patches ON, upstream's own view answers **200** to a BOM'd UTF-16
body, because `_patched_parse_json` no longer narrows encodings and `json.loads` auto-detects. Four
answers across two mounts and two patch states, and only the package mount is constant.

## W3-3 / W3-4 / W3-6

- **W3-3.** `describe_value`'s opener no longer claims to be "the single owner of the tail every
  typed configuration rejection in the package appends". It is now "the shared renderer", plus an
  explicit scope paragraph: every typed rejection on the **transport boundary** routes through it
  (the five sites in `views.py` / `consumers.py` / `routers.py`), dozens of other `got {...}` tails
  elsewhere still interpolate their own values, and routing them is a separate DRY pass deliberately
  not claimed here. Re-measured: still 50 hand-rolled tails. **No conversion pass was done.**
- **W3-4.** Restated the rationale rather than adding a ceiling, and justified: a ceiling would be an
  invented constant, and `GraphQLWebSocketConsumer` already declines to impose a maximum connection
  lifetime for exactly that reason (Decision 12 — no correct default, the deployment owns the
  number). The rejection is now stated as being about values the package cannot *use* — `nan` loses
  every comparison so it would silently never expire and never say why; `inf` is a saturation
  sentinel rather than a number of seconds anyone chose — with the accepted case disclosed in the
  same breath: `10**300` and `1e308` are accepted and a window that large *is* "never revalidate
  again", which is the deployment's call. Two new accepted-window rows make that executable, so the
  prose cannot drift, and Test 23's own docstring (which carried the same overclaim) is corrected.
- **W3-6 nit 1.** The mixin's `limit + 1` guarantee now carries its exception inline.
- **W3-6 nit 2.** W3's diagnosis was half right and the correction is different from the one
  recommended: `content_type="application/json"` is **not** dead in `_asgi_request` — dropping it
  makes `RequestFactory.post` take the `MULTIPART_CONTENT` path and raise
  `AttributeError: 'bytes' object has no attribute 'items'` (observed: 27 rows failed). The kwarg
  selects the raw-body encoding path; it is `RequestFactory.generic`'s `if data:` guard that then
  omits both `CONTENT_TYPE` and `CONTENT_LENGTH` for an empty payload. The helper now installs the
  header verbatim (like the length), asserts both absences so the factory's behavior is stated
  rather than assumed, and the docstring says all of this. The rows now run as a real
  `application/json` request, which is the content type the multipart carve-out has to not match.

## Failability proofs (every new row broke for its claimed reason)

| # | Break | Observed |
| --- | --- | --- |
| R1 | `_measured_remaining` restored to `max(end - position, 0)` | `..._probes_as_empty_is_read_rather_than_believed` 2/2 `Failed: DID NOT RAISE HTTPException`; `..._reporting_a_position_past_its_end...` 2/2 `assert [] != []`; `..._genuinely_empty_body_is_allowed_by_one_bounded_read` 2/2 `assert [] == [257]` |
| R2 | `DjangoGraphQLView.request_adapter_class` line deleted | package: `AssertionError: assert <class 'cross_web.request._django.DjangoHTTPRequestAdapter'> is _RawBodyRequestAdapter`; live: `assert 500 == 400` x3 (the two BOM'd shapes + the attribution row) |
| R3 | `_RawBodyRequestAdapter.body` property deleted | `UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff in position 0: invalid start byte` inside the package row |
| R4 | `AsyncDjangoGraphQLView` "symmetrized" onto the sync adapter | `assert <class 'django_strawberry_framework.views._RawBodyRequestAdapter'> is AsyncDjangoHTTPRequestAdapter` |
| R5 | an invented `window > 86400` ceiling added | `test_the_revalidation_window_accepts_and_coerces_numbers` `[astronomical-int-with-a-float-image]` and `[largest-order-of-magnitude-float]` FAIL with the `ConfigurationError` rendering the value |

Production files were restored from a pre-proof copy after each proof and the suites re-run green.

## Verification transcript

```
$ uv run ruff format <the 10 touched .py files>          -> 10 files left unchanged
$ uv run ruff check django_strawberry_framework/ tests/ examples/fakeshop/test_query/
All checks passed!
$ uv run python scripts/check_trailing_commas.py --check <the 10 touched .py files>   -> exit=0
ASCII-only re-verified per file with an explicit ord(c) > 127 scan: none.

$ uv run pytest tests/test_views.py tests/test_strawberry_patches.py \
      tests/test_cross_web_patches.py tests/test_routers.py --no-cov -q
236 passed in 3.94s
$ uv run pytest examples/fakeshop/test_query/test_transport_api.py \
      examples/fakeshop/test_query/test_products_api.py --no-cov -q
158 passed in 35.80s
$ uv run pytest --no-cov -q
4991 passed, 40 skipped in 62.85s (0:01:02)
```

Django 5.2.0 / Python 3.10.19 floor (`/tmp/dsf-floor-r5`, `-o addopts=""` — no xdist / pytest-cov
there), re-run because `_request_body.py` changed:

```
$ /tmp/dsf-floor-r5/bin/python -c "import sys, django; print(sys.version.split()[0], django.VERSION)"
3.10.19 (5, 2, 0, 'final', 0)
$ ... -m pytest tests/test_views.py tests/test_strawberry_patches.py tests/test_cross_web_patches.py
166 passed in 0.22s
$ ... -m pytest tests/test_routers.py
70 passed in 2.04s
$ ... -m pytest examples/fakeshop/test_query/test_transport_api.py
40 passed in 15.06s
```

The floor's live transport run is the load-bearing one: the seekable probe there runs against a real
`SpooledTemporaryFile` that does **not** declare `seekable`, i.e. the capability path that exists
only at the floor, and it now runs through the coherence guard.

## Notes for the spec custodian (not edited here)

`docs/spec-046-transport_security-0_0_15.md` is custodian-owned and was being edited concurrently.
The amendments this pass requires:

1. **Decision 9, the `_patched_body` paragraph.** "Keeping the adapter's bytes raw is what lets the
   strict decode run in a scope that can translate its failure" is the spec-level form of W3-2: it
   makes the package view's wire contract depend on a gated patch, while the next paragraph claims
   the gate does not carry the policy. The package view now supplies its own body source,
   `views.py::_RawBodyRequestAdapter`, installed through upstream's `request_adapter_class` seam;
   `_patched_body` still returns raw bytes, but for consumers who mount **upstream's own** view.
2. **Decision 9, "Which docs, by surface".** "without the `cross_web` half an undecodable body is an
   unhandled `500`" must be scoped to upstream's own view, and "names the view boundary that owns the
   wire contract whatever the setting says" becomes the two view-owned halves (the strict decode
   **and** the body source).
3. **Decision 9's title / anchor** (`...-is-enforced-once-on-the-package-views-parsing-boundary`,
   cross-referenced from at least four places) now describes half the enforcement. Custodian's call
   whether the anchor churn is worth it.
4. **Slice 3 checklist** (the `_cross_web_patches.py::_patched_body` and both-docstrings lines) needs
   a line for `_RawBodyRequestAdapter` + `DjangoGraphQLView.request_adapter_class`.
5. **Decision 7 / Slice 2 prose** ("A measurable stream (the ASGI spool) is size-probed with `seek` /
   `tell`, its original position restored, with **nothing read**") should record that a probe whose
   answer is zero or less is a measurement failure and falls through to the bounded read — otherwise
   the spec still describes the fail-open shape.
6. **Decision 11's window paragraph** ("`nan` and `inf` are refused for the same reason as a negative
   value: one silently disables the window ... and the other silently disables revalidation") is
   softer than the code docstring was but has the same gap: a finite `1e300` disables revalidation
   just as effectively and is accepted. Recommend adding the no-ceiling sentence and its Decision-12
   rationale.
7. **Test plan.** Row 3 / S9's file list should gain `_RawBodyRequestAdapter` and the
   `APPLY_UPSTREAM_PATCHES = False` live rows; the S2 rows should gain the incoherent-measurement
   rows.
8. Decision 9's rejected alternative "**Set a strict codec on the adapter...**" is still correct and
   is *not* contradicted by `_RawBodyRequestAdapter` (which removes a decode rather than adding one),
   but it is close enough that the custodian should re-read it alongside amendment 1.

`docs/TREE.md` still needs `_request_body.py` at Slice 5's doc-wrap regenerate.
