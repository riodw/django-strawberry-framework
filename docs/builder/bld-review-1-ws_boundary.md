# Build: Review round 1 — the WebSocket / router boundary findings

Review reference: `docs/feedback.md` — High 3 (the consumer factory contract accepts a non-ASGI
result), Medium 4 (the revalidation helper breaks the auth subsystem's opt-in import boundary),
Medium 5 (the revocation acceptance row does not reproduce the promised separate-request flow),
and the lower-severity "An enormous integer window escapes the typed configuration boundary".
Spec reference: `docs/spec-065-transport_security-0_0_15.md` Decision 11, Edge cases
#"`websocket_revalidation_window` is meaningless when a custom class is injected", Test plan S11
rows 25 and 29.

Scope note: the HTTP boundary findings (Blocker 1, High 2) are a concurrent agent's; this artifact
touches none of `views.py`, `_strawberry_patches.py`, `_cross_web_patches.py`, `tests/test_views.py`,
`tests/test_strawberry_patches.py`, `tests/test_cross_web_patches.py`.
Status: built

## Files touched

| File | Why |
| --- | --- |
| `django_strawberry_framework/exceptions.py` | New `describe_value` — the one safe renderer for the `got {type} {value!r}` tail every typed configuration rejection appends. Additive; no existing behavior changed. |
| `django_strawberry_framework/utils/sessions.py` | **New.** The cycle-neutral home of `session_store_class` (Medium 4). |
| `django_strawberry_framework/utils/__init__.py` | One docstring bullet for the new submodule (that docstring is the package's module inventory and is what `build_tree_md.py` renders). |
| `django_strawberry_framework/auth/sessions.py` | Resolver deleted here and imported from `utils/sessions.py`; module docstring's third bullet rewritten to say *why* the expression is single-sited outside this package. |
| `django_strawberry_framework/consumers.py` | `_refreshed_actor` reaches `.utils.sessions` (Medium 4); `resolved_revalidation_window` gains the guarded `float` conversion + one shared rejection builder (the numeric finding); module docstring states the import boundary. |
| `django_strawberry_framework/routers.py` | Factory result + calling convention validated before mounting (High 3); the unusable-candidate tail goes through `describe_value`. |
| `tests/test_routers.py` | 8 new rows / parametrize entries, the collection-time `auth.sessions` import removed, a probe URLConf added for the real second request. |
| `docs/builder/bld-review-1-ws_boundary.md` | This artifact. |

## High 3 — the factory result is validated before it is mounted

### Design

`routers.py::_factory_application` owns the whole factory shape now, and it rejects two things at
construction rather than at the first matching handshake:

1. **The calling convention**, pre-bound with `inspect.signature(factory).bind(schema=schema)` in
   `_require_factory_calling_convention` before the factory is invoked at all. The originating
   `TypeError` is preserved as `__cause__`.
2. **The returned object**, which must be callable. A coroutine object (the `async def factory`
   mistake) is `close()`d on the way out and earns an extra sentence in the message.

**What "a valid ASGI application" means at this seam**, stated in the helper's docstring rather
than implied: callability is the floor, and it is the *only* honest false-positive-free check
available at construction. ASGI conformance — accepting `(scope, receive, send)`, awaiting,
emitting the right event dicts — is observable only by running a real connection through the
object, which router construction must not do. So the validation converts every shape that
*cannot* be an ASGI application (`None`, a scalar, a mapping, a coroutine) into an actionable
`ConfigurationError`, and deliberately leaves a callable that merely misbehaves to fail at the
handshake where its own traceback is the useful signal.

Both messages share one `_FACTORY_CONTRACT_HINT` constant: a consumer who got either half wrong
needs the same whole contract restated. `_ASYNC_FACTORY_HINT` is appended only for the coroutine
shape, because that is the one mistake whose repair (drop the `async`) is not obvious from the
contract alone.

### Alternatives rejected

- **Catch `TypeError` around `factory(schema=schema)` instead of pre-binding.** Rejected: a
  `TypeError` raised by the call cannot be distinguished from one raised *inside* a correct
  factory's body, so a consumer bug would be reported as "your factory has the wrong signature" —
  the wrong diagnosis, with the real traceback buried under `__cause__`. Pinned by
  `test_a_factory_that_raises_from_its_body_is_not_normalized`.
- **Discriminate the same two cases by `exc.__traceback__.tb_next is None`.** Works (a binding
  failure never enters the body, so there is no second frame), but it encodes a CPython
  implementation detail in the middle of a configuration seam. Pre-binding says what it means.
- **Arity-check the RESULT with `bind(scope, receive, send)`.** Rejected: it would falsely reject
  legitimate `*args` middleware, `functools.partial` mounts and callable instances whose
  `__call__` is a C slot, for no security gain — a construction-time false rejection is worse than
  the deep failure this finding is about.
- **Normalize the factory's own body exceptions into `ConfigurationError`.** Rejected as above,
  and it also contradicts the module's existing posture that Python's own errors speak for
  themselves where they already say the right thing (`django_application` omission is deliberately
  a bare `TypeError`).
- **Validate `candidate.as_asgi(schema=schema)`'s result too (the class branch).** Rejected: that
  return value is upstream's contract, not the consumer's, so validating it would be asserting
  against Strawberry rather than against the injection seam.
- **Let `callable()` alone reject the coroutine and skip `close()`.** Rejected: it is already
  rejected by `callable()`, but *dropping* the coroutine makes CPython emit an unraisable
  "coroutine ... was never awaited" `RuntimeWarning` from the garbage collector at an unrelated
  moment — noise that points at the package in any consumer process, and a hard error under a
  `-W error` policy. Verified by deliberately removing the `close()` (transcript below).

### Per-test intent

- `test_an_injected_consumer_factory_is_called_with_the_schema_and_mounted` (Test 21, extended) —
  the ACCEPTED half: a sync factory returning an async ASGI callable is mounted by identity, is
  still a coroutine function, and `_mounted_ws_callback` re-asserts
  `AllowedHostsOriginValidator(AuthMiddlewareStack(URLRouter))` above it, so the new validation
  demonstrably neither moves nor unwraps the two wrappers.
- `test_a_factory_returning_a_non_application_fails_at_construction` (21b) — `None`, a scalar, a
  mapping, and a value whose `repr` cannot be rendered at all; each asserts the contract substring
  and the exact received tail.
- `test_an_async_factory_is_rejected_and_the_refused_coroutine_is_closed` (21c) — both the literal
  `async def factory` shape the review names and a sync wrapper that keeps a reference to the same
  coroutine, so `cr_frame is None` can prove the router closed what it refused. That reference is
  the only way a test can observe the close.
- `test_a_factory_that_cannot_accept_the_schema_keyword_fails_at_construction` (21d) — the
  convention rejection plus `__cause__` being the binding `TypeError`.
- `test_a_factory_that_raises_from_its_body_is_not_normalized` (21e) — the negative control for
  the pre-bind design.
- `test_a_factory_whose_signature_cannot_be_read_is_judged_by_the_call` (21f) — a lying
  `__signature__` skips the pre-check and mounts normally; covers the `except (TypeError,
  ValueError)` arm through a real seam rather than a unit poke.

## Medium 4 — the resolver left the eagerly-importing `auth` package

### Design

`session_store_class` now lives in `django_strawberry_framework/utils/sessions.py`, and both
callers import it from there: `auth/sessions.py::uses_signed_cookie_sessions` (module-level, so the
name stays in that module's namespace and its capability answer is unchanged) and
`consumers.py::_refreshed_actor` (still a call-time import, as the revalidation coroutine's other
import is). The `SESSION_ENGINE` expression is not duplicated — it is single-sited *outside* the
opt-in package, which is the only placement that satisfies both callers.

`utils/` is the right host: it is the package's declared home for "cross-cutting infrastructure
shared across subsystems", the transport layer and the auth layer both already depend on it, and
`utils/__init__` reaches only `relations` / `strings` / `typing` — no `channels`, no `strawberry`
type machinery, no `registry`, so `consumers.py`'s channels-free import property is untouched
(Test 15b still passes).

### Alternatives rejected

- **Keep the resolver in `auth/sessions.py` and make `auth/__init__` lazy (PEP 562).** Rejected:
  it changes the public opt-in surface `spec-040` Decision 3 pins for a transport-layer problem,
  and every existing `from django_strawberry_framework.auth import login_mutation` consumer would
  start resolving through a module `__getattr__`.
- **Duplicate the two-line `import_string(f"{SESSION_ENGINE}.SessionStore")` in `consumers.py`.**
  Rejected outright by the finding and by DRY: two places would have to agree about how a
  consumer-authored engine subclass resolves.
- **A new private root module (`_sessions.py`, beside `_django_patches.py`).** Viable, and the
  root's `_`-prefixed modules are the precedent for "private, package-owned". Rejected because
  those three are all *third-party patch* modules; a shared Django-session helper is exactly what
  `utils/` is for, and TREE.md renders the `utils/` inventory from its docstrings.
- **Import `auth.sessions` lazily but only once, memoized.** Rejected: memoizing does not remove
  the import, it only delays which operation pays for it.

### Per-test intent

`test_revalidation_resolves_its_session_store_outside_the_opt_in_auth_package` (Test 33) evicts the
whole `django_strawberry_framework.auth` prefix with the shared `evicted_modules` two-sided restore
(`tests/_soft_dependency.py`), runs one real authenticated operation over the package's own mount,
then asserts (a) the operation returned `next` with the real username — only reachable if the store
resolved, because a failed resolver fails closed — (b) `utils.sessions` IS in `sys.modules`, and
(c) nothing under the `auth` prefix is.

Strict eviction is what makes the row a proof rather than a coincidence: under `--dist loadscope` a
worker that already ran `tests/auth/` has those modules cached, so a bare `not in sys.modules`
assertion would pass regardless of what production imports — which is precisely the masking the
review found in this module (it imported `auth.sessions` at collection time; that import is now
gone, replaced by `utils.sessions` for the poisoning helper).

One caveat recorded deliberately: if this row ever fails because production re-points at
`.auth.sessions`, the re-import re-runs `auth/mutations.py`'s module-level
`register_subsystem_clear(...)`, which replaces that owner's callback in the process registry. The
assignment is keyed by owner so nothing accumulates, and the eviction restores `sys.modules`, but a
*failing* run of this row can leave the worker's subsystem-clear pointing at a discarded module
object. The failure is the signal; the fix is production, not the test.

## Medium 5 — a real second HTTP request now performs the revocation

### Design

`tests/test_routers.py` doubles as a probe URLConf: one `_logout_probe` view plus module-level
`urlpatterns`, reached through `override_settings(ROOT_URLCONF=__name__)` — the pattern
`examples/fakeshop/test_query/test_multi_db.py` already established in this repo. While the
communicator stays open, a `django.test.AsyncClient` carrying the socket's own session cookie
`POST`s to that view, which calls Django's own `django.contrib.auth.logout`: `SessionMiddleware`
loads the session from the cookie, the configured engine flushes the record, `request.session`
rotates to a fresh empty store, and the response expires the cookie. Operation 2 on the ORIGINAL
communicator is then denied.

The view returns what it *saw* — session key, username, `is_authenticated` — so the row asserts the
second request resolved the SAME session and the SAME actor before it asserts the denial. Without
that, "the next operation was denied" would not prove the logout was the cause.

The three direct mutators (`_flush_the_session`, `_disable_the_user`, `_rotate_the_password`) stay
exactly as they were: they are precise unit controls, one revocation shape each, and Test 26 keeps
its three parametrized rows. The section comment now says explicitly that neither row subsumes the
other — the mutators would stay green if the logout path broke, and the logout row alone cannot
isolate the disabled-user or password-rotation shapes.

### Alternatives rejected

- **A fakeshop `asgi.py` so the socket itself becomes live-tier.** Rejected here for the reason the
  spec's Risks section already records (it is the fakeshop-activation card's job), and because the
  review explicitly does not require it.
- **Driving `POST /logout` through the package's own auth `logout` mutation.** Rejected: that
  couples a transport regression to the `auth` GraphQL surface — and to the very package the Medium
  4 fix just kept out of this module's import graph.
- **`database_sync_to_async`-wrapped `django.test.Client`.** Equivalent in outcome; `AsyncClient`
  needs no wrapper on an async test and runs the same middleware stack, so it is the smaller shape.
- **Asserting only `session_key_after is None`.** Kept, but not alone: the before-values are what
  prove the request targeted the socket's session rather than minting its own.

## Lower-severity — the enormous integer window, and the message that could not render it

### Design

`resolved_revalidation_window` now converts before it judges:

1. reject `bool` / non-numeric (unchanged);
2. `float(value)` in its own `try`, with `OverflowError` chained into the `ConfigurationError`;
3. reject `window < 0` or non-finite, on the converted `float`.

All three arms raise one message through `_unusable_window_error`, because the arms differ in how
they *detect* an unusable value, not in what the deployment must change. The prose gained "finite"
and "that converts to a float" so an integer rejection reads as a rejection rather than a
contradiction.

**A second defect the review did not name, on the same path.** Guarding `math.isfinite` alone is
not sufficient: the rejection message interpolates `{value!r}`, and CPython 3.11+ refuses to
convert an integer of more than `sys.get_int_max_str_digits()` (4300) digits to a string. So
`resolved_revalidation_window(10**10000)` would still have raised `ValueError: Exceeds the limit
(4300 digits) for integer string conversion` — from inside the rejection, before the
`ConfigurationError` existed. The same exposure sat on `routers.py`'s unusable-candidate tail
(`websocket_consumer_class=10**10000`).

Root fix: `exceptions.py::describe_value`, the one owner of the `got {type} {value!r}` tail, which
degrades to `an unprintable {type}` when the value cannot be rendered. It sits beside the existing
private `_safe_type_name` / `_safe_arg_repr` pair, which already owns exactly this concern for the
*rendered exception* path — and cannot help here, because the tail is built by an f-string at the
raise site, before any exception object exists. Both of my raise sites use it.

### Alternatives rejected

- **Give the `OverflowError` arm its own message that never interpolates the value.** Fixes the
  window in isolation and leaves the identical exposure at the router's candidate tail, at
  `views.py`'s cap, and at every future `got {value!r}`. Rejected: same root cause, one owner.
- **`sys.set_int_max_str_digits()` around the format.** Rejected: a library must not mutate an
  interpreter-wide safety limit, and a 10 000-digit error message is not an improvement.
- **Truncate the repr to N characters.** Rejected as unnecessary machinery: the failure is not
  "long", it is "unrenderable", and the type is what makes the message actionable.
- **A predicate helper returning `float | None` with one raise site.** Slightly tidier, but it
  discards the `OverflowError` as `__cause__`, which is the part of the diagnosis that says *why*
  the number is unusable.

### Per-test intent

- Test 23 gains `10**10000` and `-(10**10000)` rows (the negative twin is there because the
  original `value < 0` check could never run on it either).
- `test_the_huge_window_rejection_chains_its_cause_and_still_renders` (23c) — the two properties a
  bare `pytest.raises` cannot see: `__cause__` is the `OverflowError`, and the message renders.
- Test 21b's `int-too-large-to-render` row earns the same `describe_value` degradation through the
  router's factory-result seam.

`views.py::_resolved_max_request_body_bytes` was checked (read-only, not edited — a concurrent agent
owns that file): it has no `math.isfinite` / `float()` and so no `OverflowError` sibling, but its
`got {type(value).__name__} {value!r}` tail has the *renderability* sibling —
`max_request_body_bytes=-(10**10000)` reaches the raise and formats the value. Reported to the
caller rather than edited.

## Verification transcript

```
$ uv run ruff format <the 6 production paths> ; uv run ruff check <same>
6 files left unchanged
All checks passed!

$ uv run ruff format tests/test_routers.py ; uv run ruff check tests/test_routers.py
1 file left unchanged
All checks passed!

$ uv run python scripts/check_trailing_commas.py --check \
      django_strawberry_framework/routers.py django_strawberry_framework/consumers.py \
      django_strawberry_framework/exceptions.py django_strawberry_framework/utils/sessions.py \
      django_strawberry_framework/utils/__init__.py django_strawberry_framework/auth/sessions.py \
      tests/test_routers.py
exit=0

$ uv run pytest tests/test_routers.py --no-cov -q -n0
68 passed in 2.91s

$ uv run pytest tests/test_routers.py tests/auth tests/test_exceptions.py tests/utils --no-cov -q -n0
655 passed in 7.94s

$ uv run pytest --no-cov -q          # full sweep, all testpaths (first run)
13 failed, 4895 passed, 40 skipped in 125.66s

$ uv run pytest --no-cov -q          # full sweep, re-run after the wording fix below
1 failed, 4967 passed, 40 skipped in 273.79s
```

Every failure in both sweeps belongs to the concurrent HTTP-boundary agent's in-flight work, not to
this change. First sweep: 10 in `tests/test_strawberry_patches.py` and 2 in
`tests/test_cross_web_patches.py` (their `_patched_parse_json` strict decode had just moved onto the
view per review High 2, tests not yet updated), plus
`examples/fakeshop/test_query/test_transport_api.py::test_the_two_body_ceilings_are_distinguishable_by_the_response_they_produce`.
Second sweep: they had landed their test updates, and only that last row remains — the Blocker 1
body-cap rework (`views.py` + the new untracked `_request_body.py`), asserting `400 == 200` on
`/cap-tiny/`. Nothing under `tests/test_routers.py`, `tests/auth/`, `tests/utils/` or
`tests/test_exceptions.py` fails in either sweep.

Between the two sweeps one wording change landed: `_ASYNC_FACTORY_HINT` was reworded to stop
repeating "the factory returned a coroutine" (the message already ends with the received value), and
Test 21c's re-typed substring moved with it. That is the only reason for the re-run.

### The Medium 4 regression was proved to fail

Production was deliberately reverted to the old import, the row was run, then production was
restored:

```
$ python3 -c "<replace .utils.sessions with .auth.sessions in consumers.py>"
BROKEN production import in place

$ uv run pytest "tests/test_routers.py::test_revalidation_resolves_its_session_store_outside_the_opt_in_auth_package" --no-cov -q -n0
E   AssertionError: the WebSocket revalidation imported the opt-in auth subsystem
    (('django_strawberry_framework.auth.mutations', 'django_strawberry_framework.auth.queries')
    must stay absent): ['django_strawberry_framework.auth',
    'django_strawberry_framework.auth.mutations', 'django_strawberry_framework.auth.queries',
    'django_strawberry_framework.auth.sessions']
1 failed in 2.70s

$ python3 -c "<restore>" ; uv run pytest <same row> --no-cov -q -n0
1 passed in 2.46s
```

### The coroutine-close assertion was proved to fail

```
$ python3 -c "<replace application.close() with a no-op in routers.py>"
$ uv run pytest "tests/test_routers.py::test_an_async_factory_is_rejected_and_the_refused_coroutine_is_closed" --no-cov -q -n0
E   AssertionError: the router must close the coroutine it refuses
    assert <frame at 0x10e2cd9c0, ... code async_factory> is None
1 failed in 0.15s
Exception ignored while finalizing coroutine <... async_factory>:
RuntimeWarning: coroutine '...async_factory' was never awaited      # the leak the close prevents
```

Restored, and the full `tests/test_routers.py` run above is post-restore.

### Read-only runtime probes

`scratchpad/probe_r1.py` (the window matrix: `10**10000`, `-(10**10000)`, `nan`, `inf`, `-1.0`,
`True`, `"1.0"` all `ConfigurationError`; `0`, `0.0`, `30`, `2.5`, `10**300` all accepted and
coerced) and `scratchpad/probe_r2.py` (the factory matrix under `warnings.simplefilter("error")`:
valid factory mounted by identity inside `OriginValidator`, five rejections with their causes, the
un-introspectable factory accepted, the huge-int *candidate* rejected, and no coroutine warning at
`gc.collect()`).

## Notes for the spec custodian

Not edited (the custodian owns `docs/spec-065-*.md`); see the caller report for the quoted
sentences. In summary: Decision 11's factory sentence needs the return-value contract; Edge cases'
`websocket_revalidation_window` bullet and Test plan row 29 must say "positive window"; Decision
11's "pinned to the operation's own resolved alias" and the matching Edge cases bullet overstate
what the code does; Decision 11 (or Helper-reuse) should name `utils/sessions.py` as the resolver's
home and the opt-in boundary as the reason; the numeric domain sentence should say the window must
convert to a `float`.

`docs/TREE.md` owes a `utils/sessions.py` row at Slice 5's doc-wrap (it is `build_tree_md.py`-
rendered from the module docstring's first line, so no hand-edit).
