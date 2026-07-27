# W3 adversarial review — review round 1 remediation (card 065 transport security)

Reviewer: Worker 3, deliberately isolated from both builders. Nothing in
`bld-review-1-http_boundary.md` / `bld-review-1-ws_boundary.md` was taken on trust; every claim
below is backed by source read at the raise site, a runtime probe, or an observed test failure.

Baseline at review start: `uv run pytest --no-cov -q` -> **4977 passed, 40 skipped** (62s). Floor
(`/tmp/dsf-floor-r5`, Python 3.10.19 / Django 5.2.0, `-o addopts=""`): `tests/test_views.py`
`tests/test_strawberry_patches.py` `tests/test_cross_web_patches.py` -> **158 passed**;
`examples/fakeshop/test_query/test_transport_api.py` -> **36 passed**.

Working tree at review end is byte-identical to review start (every failability edit restored and
verified by md5 against a pre-edit copy; `git status --short` unchanged apart from
`docs/spec-065-*.md`, which the concurrent spec-reconciliation pass is editing).

## Verdicts

| Review finding | Verdict |
| --- | --- |
| Blocker 1 — counted cap materializes the body | **CLOSED** (one Medium residual, W3-1) |
| High 2 — wire policy on the upstream-patch kill switch | **CLOSED for the required regression; WEAKENED for the broad switch** (W3-2) |
| High 3 — factory contract accepts a non-ASGI result | **CLOSED** |
| Medium 4 — auth opt-in import boundary | **CLOSED** |
| Medium 5 — real separate-request revocation | **CLOSED** |
| Numeric — enormous integer window | **CLOSED** (docstring residual, W3-4) |
| Explicit-zero rule / multi-database claim | spec-only; on the WS artifact's amendment list, not judged |
| Deleted tests (3 rows) | **No property lost** — audited per assertion |

## Blocker 1 — CLOSED. It is a real bound, not a relabelled detection.

**Reachable-path audit.** `_request_body.py::body_exceeds_limit` has five outcomes and none of them
materializes an over-limit body:

1. `_body` present -> `len(request._body) > limit`. The allocation predates `run`; the request is
   refused, not processed.
2. seekable -> `seek`/`tell` probe, position restored, nothing read.
3. not measurable -> bounded read to at most `limit + 1`; over the limit the chunks are **never**
   joined and the remainder is left unread.
4. no `_stream` -> defer (synthetic `HttpRequest`; Django itself would `AttributeError`).
5. `_read_started` true with `_body` absent -> defer. Verified there is no bypass here:
   `request.body` then raises `RawPostDataException`, so nothing downstream can process the request
   either.

Branch (1) is the only remaining unbounded allocation, and it is honestly disclosed. I additionally
verified it is **not** reachable on the JSON GraphQL path in a stock middleware stack:
`CsrfViewMiddleware` reads `request.POST`, and Django's `_load_post_and_files` builds an empty
`QueryDict` without touching `self.body` for any content type other than
`application/x-www-form-urlencoded` / `multipart/form-data`. So the branch is exactly the urlencoded
case the docstring names.

**The chunked branch is genuinely capped at `limit + 1`.** Measured with `limit = 256` against a
4096-byte payload: `delivered == 257`, `max(requested) <= 257`, bytes still unread in the stream,
`_body` absent. Boundary, both measuring branches, `limit-1 / limit / limit+1`:

```
spool size=255: exceeds=False      nonseek size=255: exceeds=False delivered=255
spool size=256: exceeds=False      nonseek size=256: exceeds=False delivered=256
spool size=257: exceeds=True       nonseek size=257: exceeds=True  delivered=257
```

`>` and not `>=`, on both branches. A body exactly at the limit is legal.

**Both halves of the `_body`-vs-`_stream` claim verified.** The module never writes `_body` (read at
the raise site; the only write is `request._stream = BytesIO(...)` plus
`request._read_started = False`). And Django's own ceiling still fires on the allowed path — proved,
not read: pre-filling `request._body` in the bounded branch makes the live row
`test_transport_api.py::test_the_two_body_ceilings_are_distinguishable_by_the_response_they_produce`
go **400 -> 200** (`DATA_UPLOAD_MAX_MEMORY_SIZE = 64` silently stops applying). See failability
proof P3. Django 5.2.0's `HttpRequest.body` was read on the floor interpreter and its ceiling is a
`CONTENT_LENGTH` comparison against unmodified `META`, so the substituted `BytesIO` cannot defeat it;
Django 6.0's additional seekable-size check sees the substituted buffer.

**Hunted shapes the builder did not enumerate.**

| Shape | Result |
| --- | --- |
| `_read_started` true, `_body` absent | Defer; `request.body` raises `RawPostDataException`. No bypass. |
| `tell()` lies (over-reports) | **Bound lost.** See W3-1. |
| `seek(0, SEEK_END)` under-reports | **Bound lost.** See W3-1. |
| `Content-Length` far exceeding the real body | `413` at the declared gate. Fail-safe direction; a lying-large declaration cannot buy a larger body and self-rejects. |
| body exactly at `limit` / `limit + 1` | Allowed / refused, on both branches (table above). |
| GET with an over-limit body | Documented no-op; upstream reads no body on GET. `_body` stays absent. |
| HEAD with an over-limit body | `413` (the cap runs; upstream would have answered `405`). Harmless, undocumented; a HEAD has no body by spec. |
| multipart declared under the cap, streaming over | Passes the package cap by design, then Django's `MultiPartParser` bounds its own reads at `CONTENT_LENGTH` (`django/http/multipartparser.py` #"content_length = int(META.get(\"CONTENT_LENGTH\", 0))" and the `LimitedStream` it builds from it). The declaration is the bound. Consistent with the docstring; no new gap. |

## The Python 3.10 floor claim — independently CONFIRMED, and load-bearing

Direct probe on `/tmp/dsf-floor-r5`:

```
py (3, 10, 19)
hasattr seekable: False          isinstance IOBase: False
tell: 0                          seek end: 100
rolled hasattr seekable: False   rolled tell: 0 end: 100
```

`tempfile.SpooledTemporaryFile` at 3.10.19 has **no** `seekable` attribute at all (in-memory and
rolled-to-disk alike) while `tell()` / `seek()` work and return positions. A `hasattr`-gated probe
would therefore drop the ASGI body file onto the read branch at the floor.

That this matters is not an argument, it is failability proof **P9**. Rewriting the probe as
`if not callable(seekable) or not seekable(): return None`:

- at Python 3.14.2 the **real-spool** rows still pass (`2 failed, 8 passed` — only the
  `_UndeclaredSeekableStream` stand-in catches it);
- at Python 3.10.19 / Django 5.2.0 the real-spool rows **all fail** (`10 failed`), i.e. the ASGI
  spool silently degrades onto the read branch at exactly the floor the card protects.

So the `callable(seekable)`/`tell()` shape is correct, and `_UndeclaredSeekableStream` is what keeps
the property asserted from the dev stack. Clean axis.

## High 2 — CLOSED for the required regression, WEAKENED for the broad switch

**What is genuinely closed.** With `APPLY_UPSTREAM_PATCHES = {"strawberry": False}`:

- package tier, 9 wire shapes x 2 views x `__cause__` type
  (`test_the_wire_contract_holds_with_the_upstream_patches_opted_out`);
- live sync (`test_the_utf8_wire_contract_survives_the_upstream_patch_kill_switch`) and live async
  (`test_the_async_view_keeps_the_utf8_wire_contract_with_the_patch_opted_out`), each with a
  valid-UTF-8 control in the same opted-out state;
- the inverse pinned at the patch tier (`test_patched_parse_json_leaves_upstreams_bytes_semantics_alone`,
  4 encodings) and the switch proved behaviorally live
  (`test_the_gated_workarounds_really_stop_hardening_when_opted_out`,
  `test_the_upstream_bug_workaround_still_respects_its_own_opt_out`).

**MRO.** `_RequestBodyBoundaryMixin` is first in both views' base lists and
`[k for k in view.__mro__ if "parse_json" in vars(k)] == [mixin, BaseView]` for both. The patch
state does not touch the MRO — it rebinds `BaseView.parse_json` only — so the override is in the
resolution path for sync and async in both states. `__cause__` discrimination survived and is
asserted in both states. All of this is failable (P4): removing the decode from the mixin fails 18
package rows and 6 live rows.

**Where it is weakened: see W3-2.** With the broad `APPLY_UPSTREAM_PATCHES = False` the SYNC package
view answers **500**, not `400`, for the BOM'd multi-byte shapes. No test covers that state.

## High 3 — CLOSED

Every regression the review required is present and correct:

- `None`, a non-callable scalar, a mapping, and an unrenderable `10**10000` -> `ConfigurationError`
  naming the contract and the received value;
- `async def factory` -> rejected, with `cr_frame is None` proving the refused coroutine was closed
  (and a second wrapper shape so the object can be inspected);
- valid synchronous factory returning an async ASGI callable -> mounted by identity, with
  `inspect.iscoroutinefunction(callback)`;
- the two wrappers stay outside the validated result — `_mounted_ws_callback` unwraps
  `AllowedHostsOriginValidator` and `AuthMiddlewareStack` and pins the route regex before returning
  the callback, so the accepted row is also the wrapper-nesting row;
- plus the calling-convention pre-bind with the `TypeError` as `__cause__`, non-normalization of a
  `TypeError` raised inside the factory body, and pass-through for an un-introspectable callable.

Failable: P7 (5 rows fail when the result check is removed), P8 (the close row fails when
`application.close()` is removed, and CPython then emits the "never awaited" `RuntimeWarning` the
docstring predicts).

Informational only: the deliberately narrow "callable is the floor" contract admits a consumer class
that was never `as_asgi()`-ed and an async **generator** (the latter is rejected but gets neither the
`_ASYNC_FACTORY_HINT` addendum nor a `close()`). Both are the documented floor and neither leaks a
warning. Not a finding.

## Medium 4 — CLOSED, proved in a genuinely fresh process

Not module eviction — a new interpreter:

```
after django.setup():          auth modules = []
after import consumers:        auth modules = []   (channels in sys.modules: False)
after import utils.sessions:   auth modules = []
resolved store: django.contrib.sessions.backends.db.SessionStore
FINAL                          auth modules = []
```

`django_strawberry_framework.utils.sessions` also imports standalone in a bare interpreter with no
cycle (both Django imports are function-local, so the module body pulls nothing), and neither
`consumers` nor `views` puts `channels` in `sys.modules` at import time. The eviction-based
regression row is failable (P5): repointing the import back to `.auth.sessions` fails it with all
four `auth` modules listed in the assertion message.

## Medium 5 — CLOSED

`test_a_real_second_request_logout_denies_the_next_operation_on_the_open_socket` runs a genuine
second HTTP request (`AsyncClient` -> probe URLConf -> `django.contrib.auth.logout`) while the
communicator stays open, asserts the second request resolved the **same** `session_key`, the same
username and `authenticated_before is True`, asserts the flush (`session_key_after is None`) and the
cookie expiry, and only then denies operation 2 on the original socket. That is the property the
review asked for, and the three direct mutators are kept as unit controls. Failable: P6 (a
short-circuited `revalidate_operation_actor` turns operation 2 from `error` into `next`).

Minor note, not a finding: the second request's cookie is planted (`client.cookies[name] =
session_key`) rather than harvested from a login response — but the row then *proves* server-side
that it resolved the socket's own session and actor, which is the load-bearing half.

## Deleted tests — audited per assertion; no property lost

| Deleted assertion (from `git show HEAD:tests/test_strawberry_patches.py`) | Where it lives now |
| --- | --- |
| 9-row matrix: `status_code == 400` | `test_views.py::test_the_package_view_rejects_every_non_utf8_wire_shape` (9 x 2 views) **and** `..._holds_with_the_upstream_patches_opted_out` (9 x 2). Strictly stronger. |
| 9-row matrix: `reason == "Unable to parse request body as JSON"` (literal) | Same rows, via `_JSON_PARSE_REASON`, **plus** `test_the_wire_reason_is_upstreams_own_parse_json_literal` pinning the constant against upstream's live raise. Stronger. |
| 9-row matrix: `type(__cause__) is cause` | Same rows, both patch states, both views. Stronger. |
| The `raw-binary` row's `UnicodeDecodeError` cause **at the patch wrapper** | Deliberately gone: the patch no longer narrows encodings, and that is asserted as a requirement by `test_patched_parse_json_leaves_upstreams_bytes_semantics_alone`. The package-side property (raw binary -> 400 with a `UnicodeDecodeError` cause) is pinned at the view. No loss. |
| `..._hands_the_delegate_a_str_for_a_bytes_body`: `seen == ['{"a": 1}']`, `isinstance(seen[0], str)` | `test_views.py::test_the_package_view_hands_upstream_a_str_for_a_bytes_body`, both views. Equivalent (it patches `BaseView.parse_json`, i.e. the next MRO owner, which is the right interception point for the mixin's `super()` call). |
| `..._resolve_parse_json_to_the_one_patched_wrapper`: `view.parse_json is _patched_parse_json` | Split across two rows that together are stronger: `test_both_package_views_resolve_parse_json_to_the_one_shared_mixin_method` (`is mixin.parse_json`) and the surviving `test_patch_is_installed_on_base_view` (`BaseView.__dict__["parse_json"] is _patched_parse_json`). |
| `owners == [BaseView]` | `owners == [mixin, BaseView]` — exact chain, in order. Stronger. |

The re-aim in `tests/test_cross_web_patches.py` is also correct and load-bearing rather than
cosmetic: `json.loads` on `bytes` detects `utf-8-sig` and strips a UTF-8 BOM itself, so following the
adapter's bytes into `_patched_parse_json` would have **accepted** the BOM'd body. Routing them into
`DjangoGraphQLView.parse_json` is what refuses them, and the patch-tier row now asserts the
acceptance as the patch's documented contract.

I found nothing in `tests/`, `examples/`, or the package still asserting the old ownership.

## Failability proofs run (10 of 10 broke the production code, observed the failure, restored)

| # | Break | Observed |
| --- | --- | --- |
| P1 | `_measured_remaining` forced to `None` | `test_a_seekable_over_limit_body_is_refused_without_ever_being_read` 8/8 FAIL with `AssertionError: the cap read a stream it was supposed to size-probe` |
| P2 | `request.read(_READ_CHUNK_BYTES)` (drop the `limit + 1 - read_so_far` ceiling) | `..._reads_at_most_one_byte_past_the_limit` 2/2 FAIL, `assert 4096 == 257` |
| P3 | bounded branch writes `request._body` | live `test_the_two_body_ceilings_are_distinguishable_by_the_response_they_produce` FAIL, `assert 200 == 400` (Django's ceiling gone) |
| P4 | strict decode removed from `views.py::parse_json` | 18 package rows FAIL + 6 live opted-out rows FAIL (`assert 200 == 400`) |
| P5 | `_refreshed_actor` imports `.auth.sessions` again | `test_revalidation_resolves_its_session_store_outside_the_opt_in_auth_package` FAIL, listing all four `auth` modules |
| P6 | `revalidate_operation_actor` short-circuits to allow | `test_a_real_second_request_logout_denies_the_next_operation_on_the_open_socket` FAIL, `assert 'next' == 'error'` |
| P7 | `_factory_application` returns the result unvalidated | 4 result rows + the coroutine row FAIL (`5 failed, 4 passed`) |
| P8 | `application.close()` removed | `..._the_refused_coroutine_is_closed` FAIL on `cr_frame is None`, and CPython emits the predicted "never awaited" `RuntimeWarning` |
| P9 | probe requires a declared `seekable()` | **py3.14: real-spool rows still PASS** (`2 failed, 8 passed`); **py3.10.19/Django 5.2.0: 10 FAIL**. The floor claim is load-bearing. |
| P10 | `math.isfinite` restored ahead of the guarded `float()` | 3 window rows FAIL with a raw `OverflowError: int too large to convert to float` |

Restore verified: `md5` of `_request_body.py`, `views.py`, `consumers.py`, `routers.py` identical to
the pre-proof snapshot ("ALL FOUR BYTE-EXACT"), and the full suite re-run after all proofs gives
**4977 passed, 40 skipped**.

No test in the new surface was found to be unfailable.

## Findings

### W3-1 (Medium) — `_measured_remaining` clamps an incoherent measurement to "empty body, allowed"

`django_strawberry_framework/_request_body.py::_measured_remaining` #"return max(end - position, 0)".

The function's own docstring states the fail-safe direction: "``None`` means 'ask the bounded read
instead', never 'the body is empty'." The code does the opposite for an incoherent `tell()`/`seek()`
pair — it clamps to `0`, which `body_exceeds_limit` reads as "within the limit".

Measured:

```
=== lying tell() (over-reports position) ===
body_exceeds_limit -> False | reads: 0
  then request.body materialized 4096 bytes  (unbounded: True )

=== seek(0,END) under-reports size ===
body_exceeds_limit -> False | reads: 0
  then request.body materialized 4096 bytes  (unbounded: True )

_measured_remaining(<4096 unread bytes, lying tell>) -> 0
```

Why this is worse than parity with Django: on the measured branch the package installs **no bound of
its own** — it hands the stream straight to `HttpRequest.body`, whose only ceiling at the Django
5.2.0 floor is a `CONTENT_LENGTH` comparison, i.e. exactly the number this card's threat model says
is absent or lying. A mis-measuring stream therefore removes the only application-level bound at the
floor, silently, with no read recorded anywhere.

Reachability: **not** wire-reachable. `ASGIRequest`'s spool and `WSGIRequest`'s `LimitedStream` both
measure honestly on both supported interpreters (verified). This is a consumer-middleware /
custom-ASGI-server hazard and a fail-open default, which is why it is Medium and not High.

Root-cause fix (not a guard bolted on): return `None` when the measurement is incoherent, so the
request falls through to the bounded read that already exists —

```python
end = stream.seek(0, os.SEEK_END)
stream.seek(position)
if end < position:
    return None
return end - position
```

Note also that `max(..., 0)` is the one expression in the module with no covering row, and because it
is not a branch the `fail_under = 100` gate cannot see the gap. Add an incoherent-measurement row
alongside the fix.

### W3-2 (Low/Medium) — `APPLY_UPSTREAM_PATCHES = False` degrades the sync package view's wire contract to a 500, and no test covers that state

Measured end to end against **mounted package views**, patches never installed (setting applied
before `django.setup()`), middleware stripped so the toolbar does not mask the result:

```
strawberry patch installed: False
cross_web patch installed: False
SYNC  utf-16-bom         -> 500  b'\n<!doctype html>\n<html lang="en">...Server Err'
SYNC  utf-32-bom         -> 500  ...
SYNC  utf-16-le-nobom    -> 400  b'Unable to parse request body as JSON'
SYNC  utf-8-bom          -> 400  b'Unable to parse request body as JSON'
SYNC  valid              -> 200  b'{"data": {"ok": "ok"}}'
ASYNC utf-16-bom         -> 400  b'Unable to parse request body as JSON'
ASYNC utf-32-bom         -> 400  ...
ASYNC valid              -> 200  b'{"data": {"ok": "ok"}}'
```

Mechanism: with the `cross_web` half opted out, `DjangoHTTPRequestAdapter.body` decodes inside its
own property again, so the view's `parse_json` — and therefore the strict decode — is **never
entered** on the sync transport. The narrowed *success set* survives (the un-patched adapter's own
`.decode()` is strict UTF-8, so UTF-16 is still not accepted), which is why this is not a
reopening of the original finding. What is lost is the other half of Decisions 9/10: the controlled
`400` and "one byte sequence, one interpretation at every hop, `__cause__` the only discriminator".

The dishonest sentence is in `_strawberry_patches.py`'s module docstring (and echoed in
`views.py::_RequestBodyBoundaryMixin.parse_json`):

> The strict UTF-8 wire contract (spec-065 Decision 9) is **not** on this switch: it is enforced by
> ``views.py::_RequestBodyBoundaryMixin.parse_json``, so a consumer who mounts a package view keeps
> it whatever this setting says.

On the sync transport with `{"cross_web": False}` or `False`, the enforcement site is not reached.
`_cross_web_patches.py`'s own docstring is honest about this ("without this half ... an undecodable
body is an unhandled 500"); the two other docstrings are not.

Recommended: qualify the two claims to name the sync-transport dependency on the `cross_web` half
(the *success set* is what survives the switch; the *wire shape* additionally needs
`{"cross_web": True}`), and add an `APPLY_UPSTREAM_PATCHES = False` row so the degradation is pinned
rather than discovered. Do **not** move the decode into the adapter — that re-creates the original
upstream bug.

### W3-3 (Low) — `describe_value`'s "single owner" claim is false; the routing is four sites, not the package

`django_strawberry_framework/exceptions.py::describe_value` opens:

> The single owner of the ``got {type} {value!r}`` tail every typed configuration rejection in the
> package appends to its prose.

Measured: 5 `describe_value` call sites (`consumers.py` x1, `routers.py` x3, `views.py` x1) against
**50** remaining hand-rolled `got {...}` tails elsewhere in the package (`grep -rn "got {"
django_strawberry_framework/ | grep -v describe_value | wc -l`), plus ~40 separate
`type(...).__name__` interpolations. The builders converted exactly the four rejections on this
card's boundary, which is the right scope for the card — the docstring is what overreaches.

Of the 50, the two closest to a runtime value are
`filters/sets.py::_validate_logic_element_shape` #"({element!r})" and
`mutations/permissions.py` #"got {allowed!r}". I did not construct an exploit for either: GraphQL
input coercion rejects a scalar where an input object is expected, so both look reachable only from a
programmatic caller. Treat this as a docstring-scope fix now (say "every typed rejection on the
transport boundary"), and a separate DRY pass if the maintainer wants the other 50 routed — that is
out of card 065's scope and should not be smuggled in.

### W3-4 (Low) — the revalidation window's finiteness rejection does not deliver the property its docstring claims

`consumers.py::resolved_revalidation_window` docstring: "``inf`` would mean 'never revalidate
again', which is the one thing this card exists to prevent". Measured domain:

```
10**300 -> 1e+300         # ACCEPTED
1e308   -> 1e+308         # ACCEPTED
inf     -> ConfigurationError
10**10000 / -(10**10000) -> ConfigurationError (cause OverflowError)   # the fix, working
```

A finite `1e300`-second window is operationally identical to "never revalidate again" and is
accepted. Rejecting `inf` is still right (it is an error sentinel, and `nan` loses every comparison),
but the stated *reason* is not what the code enforces. Either restate the rationale (inf/nan are
unusable spellings, not a ceiling) or add a real upper bound; the former is almost certainly correct,
since a positive window is a deliberate consumer choice.

Pre-existing prose, but the builder rewrote this docstring while fixing the same function, so it is
in scope.

### W3-5 (Low) — `_strawberry_patch_opted_out` is duplicated across the two test trees

`tests/test_views.py` (line ~993) and `examples/fakeshop/test_query/test_transport_api.py` (line
~1136) each define a `_strawberry_patch_opted_out` context manager: save `BaseView.parse_json` and
`parse_query_params`, install the captured originals, `override_settings`, restore both. The live
copy adds `ROOT_URLCONF=__name__`.

The trees are deliberately separate (AGENTS.md), and there is no established cross-tier helper
module, so I am **not** recommending a shared helper. The real risk is drift in simulation fidelity —
if one copy later forgets to restore `parse_query_params`, the other tier's rows keep passing while a
worker is silently poisoned. Both currently restore both, so this is a note for whoever touches
either next, not a defect.

### W3-6 (informational) — two docstring precision nits

- `views.py::_RequestBodyBoundaryMixin` #"that it never allocates or reads more than ``limit + 1``
  bytes of one" is unqualified in its own sentence; the exception (an earlier middleware already
  materialized the body) is disclosed four sentences later in the same paragraph. An inline "except
  where an earlier middleware already materialized it" would stop the guarantee being quotable out
  of context.
- `tests/test_views.py::_asgi_request` documents building the request with
  `content_type="application/json"`, but Django's `RequestFactory.generic` sets neither
  `CONTENT_TYPE` nor `CONTENT_LENGTH` when `data` is empty, so every Blocker-1 row actually runs
  with `request.content_type == ""` (verified: `META keys: []`, `content_type: ''`). Harmless — the
  multipart carve-out is exercised with a real `multipart/form-data` request in
  `test_a_multipart_request_under_the_declared_gate_is_never_materialized`, and the docstring's
  `Content-Length` claim is accurate — but the content-type half of the sentence describes a header
  that is not present.

## Axes that are clean — stated so, not padded

- **DRY between the two `run` overrides** (`views.py`): irreducible (one `def`, one `async def`,
  each one line delegating to a shared `_enforce_request_body_limit`). Verified-and-rejected.
- **DRY between the two protocol handler subclasses** (`consumers.py`): each pre-hook is 6 lines and
  differs only in the upstream method name and `errors_as_list`; the decision function is already
  single-sited in `revalidate_operation_actor`. A generic factory would add indirection for nothing.
  Verified-and-rejected.
- **`_request_body.py` vs existing helpers**: no duplication. Grepped the whole package for
  `_stream` / `_body` / `_read_started` / `request.body` — the only other raw-body reader is
  `middleware/debug_toolbar.py::..._postprocess` #"json.loads(request.body)", which runs *after* the
  response, is `except Exception`-guarded, and returns early for any non-`application/json`
  response, so it cannot pre-materialize a body ahead of the cap.
- **`utils/sessions.py` cycle risk**: none. Imports standalone in a bare interpreter; both Django
  imports are function-local; `auth/sessions.py` re-exports the name so the old import path still
  resolves.
- **`consumers.py` / `views.py` channels-freedom**: verified in a fresh process, still holds.
- **`_factory_application` error chaining**: the convention `TypeError` is preserved as `__cause__`,
  the factory's own body exceptions are not normalized, and both are asserted.

## Spec reconciliation

Not judged, and deliberately not reported: `docs/spec-065-transport_security-0_0_15.md` was being
written **during** this review (one candidate residual I recorded — the DRY-reuse bullet "The UTF-8
decode is added to the existing `_patched_parse_json` wrapper" — had been removed from the file
within a minute of my reading it). Spec-prose findings from this review would be stale on arrival.
The one item I saw still present at 17:37 was Test plan row 24 ("the rejection is attributable to the
strict decode in `_patched_parse_json`"); if the concurrent pass's full list does not already carry
it, it needs the same re-attribution as row 19-23.

## Recommended order

1. W3-1 — the fail-open clamp in `_measured_remaining`, plus its covering row. This is the only
   finding that touches a security property.
2. W3-2 — qualify the two "whatever that switch says" docstrings and add the
   `APPLY_UPSTREAM_PATCHES = False` row.
3. W3-4, W3-3, W3-6 — docstring accuracy, in that order of load-bearingness.
4. W3-5 — note only; no action required now.
