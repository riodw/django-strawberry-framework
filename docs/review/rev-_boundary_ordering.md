# Review: `django_strawberry_framework/_boundary_ordering.py`

Status: verified

## Understanding

The module is the vocabulary two modules need to agree on and neither may own. `views.py` owns the
request-body boundary (spec-046 Decisions 7 and 9); `middleware/request_body.py` owns where in the
lifecycle it runs (Decision 18). Neither imports the other - confirmed, `views.py` imports only
`_boundary_ordering`, `_request_body`, `conf`, `exceptions`, and nothing under
`django_strawberry_framework/` imports `middleware.request_body` - so the target holds the four
things they exchange:

- `_BOUNDARY_MARKER`: stamped on the callback by `views.py::_RequestBodyBoundaryMixin.as_view`, read
  by `middleware/request_body.py::_package_view_instance`. Attribute rather than `issubclass`, so
  recognition costs no import of the view classes.
- `_BOUNDARY_ENFORCED`: stamped on the request by
  `middleware/request_body.py::GraphQLRequestBodyBoundaryMiddleware.process_view` after it has run
  the boundary; read by `views.py::_RequestBodyBoundaryMixin._enforce_request_boundary_once` (skip
  the second measurement) and by `_CsrfOrderingExemption` (withdraw the exemption).
- `_BOUNDARY_METHOD`: the *name* of the boundary method, probed on a marked callback's `view_class`
  before construction so a foreign class can never reach `process_view`'s uncaught call.
- `_boundary_middleware_request` + `_CSRF_ORDERING_EXEMPTION`: the per-request half of the answer
  `CsrfViewMiddleware.process_view` reads as `getattr(callback, "csrf_exempt", False)`.

Behavior traced end to end in both arrangements. Chain-supplied: `__call__`/`__acall__` publishes the
request, `process_view` builds `view_class(**view_initkwargs)` (so the mount's own
`max_request_body_bytes` applies), runs the boundary, stamps; the exemption is then false, the
project's *configured* CSRF class runs in full, `run` skips its own boundary and its `csrf_protect`
continuation no-ops on `csrf_processing_done`. View-local: no publication or no stamp, exemption
true, the chain's CSRF middleware skips the callback, `run` measures the body and re-enters CSRF -
which degrades the CSRF *class* to Django's stock one, never the ordering. A declined callback, a
chain without the boundary middleware, and a chain without any CSRF entry all land in the second
arrangement; the misordered chain is refused at startup by `_require_boundary_before_csrf`.

Both readers of `csrf_exempt` in the installed dependency set are truthiness reads, so an object with
`__bool__` is a legal value there: `django/middleware/csrf.py::CsrfViewMiddleware.process_view`
(`if getattr(callback, "csrf_exempt", False)`) and `django/contrib/admin/sites.py::AdminSite.admin_view`
(`if not getattr(view, "csrf_exempt", False)`). Nothing in `strawberry`, `cross_web`, or
`debug_toolbar` reads it at all.

Existing description of the behavior: the ordering block in `tests/test_views.py` (marks, chain rows,
recognition rows, the `ContextVar` reset row), the live rows in
`examples/fakeshop/test_query/test_transport_api.py`, the `MIDDLEWARE` comment in
`examples/fakeshop/config/settings.py` (fakeshop installs the boundary entry ahead of CSRF, so the
withdrawal is a shipped-deployment behavior, not a synthetic one), and `docs/TREE.md`.

## Verification

Scratch: `docs/review/temp-tests/_boundary_ordering/test_probe.py`, six rows, all green.

- `csrf_exempt(DjangoGraphQLView.as_view(...)).csrf_exempt is _CSRF_ORDERING_EXEMPTION`. Django's
  `csrf_exempt` sets `True` and *then* runs `wraps(view_func)`, which copies `__dict__`, so the
  package's object wins. A mount of that shape is still refused (`403`) for an untokened POST under
  `enforce_csrf_checks=True`, so the overwrite is not a bypass in either arrangement.
- A marked callback whose `view_class` carries a callable installed under `_BOUNDARY_METHOD` (via
  `setattr` from the constant) and defines nothing else: `process_view` recognizes it, runs that
  callable, and stamps the request. The same class with the boundary under a different name is
  declined, never built, never run.
- Live, against fakeshop's real `/graphql/` with the shipped chain and the CSRF entry swapped for a
  recording `CsrfViewMiddleware` subclass: the subclass is handed the callback in a checkable state
  and the request still answers `200`.
- Failability of that live row: with `_CsrfOrderingExemption.__bool__` monkeypatched to `True` the
  recorder sees nothing while the response stays `200` - the status code alone proves nothing, the
  call log is the witness.

Existing tests read rather than trusted: `test_the_async_chain_resets_the_ordering_mark_around_the_downstream_call`
pins all three states of `__bool__` through the object itself, including the reset after a raising
chain; `test_the_probed_boundary_method_is_the_one_the_package_views_define` pins the constant against
`views.py`; `test_the_shipped_chain_supplies_the_ordering_for_fakeshops_real_mount` pins the chain
order and the marker but makes no request.

Also confirmed by execution during the implementation below: reverting the boundary invocation to a
literal that differs from the probed name turns the newly recognized class into
`AttributeError: '_MinimalBoundaryViewClass' object has no attribute ...` out of `process_view` -
the uncontrolled failure the recognition exists to remove.

## Improvements

### High

None.

### Medium

**1. The boundary method's name was stated twice, and the recognition's soundness rested on the two
statements agreeing.**

- Observation: `_package_view_instance` accepted a class by probing `_BOUNDARY_METHOD`, then
  `process_view` invoked the boundary as a literal `view._enforce_request_boundary(request)`. The
  target's own docstring says the name lives here because "a name held in the consumer of the
  protocol rather than in the protocol itself is a fact stated twice" - and it was.
- Evidence: `middleware/request_body.py::_package_view_instance` reads
  `callable(getattr(view_class, _BOUNDARY_METHOD, None))`;
  `middleware/request_body.py::GraphQLRequestBodyBoundaryMiddleware.process_view` spelled the name
  out. No test could see the difference, because the two happened to agree.
- Impact: latent, not live. The two sites must change together, and if they ever did not, the probe
  would vouch for a class whose boundary the hook then cannot find - an unhandled `500` from a hook
  whose every other outcome is a controlled response, produced for exactly the input the probe had
  just accepted. That is the failure mode `_package_view_instance`'s guard exists to eliminate.
- Recommendation: the protocol module keeps sole ownership of the name; the middleware invokes
  through `_BOUNDARY_METHOD` rather than restating it. Owner is the target for the constant and
  `middleware/request_body.py` for the call site.
- Proof: `tests/test_views.py::test_the_middleware_runs_the_boundary_it_probed_the_class_for` - a
  minimal class carrying a callable only under the constant's name; `process_view` must run it and
  stamp the request. Fails in both drift directions, verified by breaking the call site.

**2. The exemption's withdrawal on the shipped mount had no behavioral proof at the live tier.**

- Observation: fakeshop installs the boundary middleware, so `__bool__`'s false branch is reachable
  from a real `/graphql/` request - but the only row about it,
  `test_the_shipped_chain_supplies_the_ordering_for_fakeshops_real_mount`, asserts the chain order and
  the marker without sending a request; every other live ordering row runs against a probe mount that
  deliberately carries only the exemption and therefore measures the view-local fallback.
- Evidence: that row's own docstring names the failure it cannot see ("the only observable loss would
  be that the project's configured CSRF class no longer runs on this endpoint"), and the scratch
  failability run confirms it: with the withdrawal disabled every status code in the live file is
  unchanged. The behavior was pinned only at the package tier, over a synthetic `ROOT_URLCONF` and a
  hand-built chain, which `AGENTS.md` treats as the fallback tier rather than the first choice.
- Impact: a settings edit, a wrapper change, or a regression in `__bool__` could move the shipped
  deployment onto the fallback arrangement - the exact substitution Decision 18 exists to prevent -
  without any live row failing.
- Recommendation: earn it over fakeshop's real chain, deriving the `MIDDLEWARE` override from
  `settings.MIDDLEWARE` the way `_without_the_global_csrf_middleware` does, so the row changes one
  entry and leaves the boundary entry where the shipped chain puts it.
- Proof: `examples/fakeshop/test_query/test_transport_api.py::test_the_configured_csrf_class_checks_fakeshops_real_mount_behind_the_boundary`.

### Low

**3. A test docstring described a dependency the target exists to make unnecessary, and described it
wrongly.**

- Observation: `tests/test_views.py::test_the_middleware_passes_a_non_package_view_through_untouched`
  claimed marker-based recognition "keeps the dependency one-way: `views.py` imports the middleware
  module, never the reverse".
- Evidence: `views.py` does not import `middleware/request_body.py`; there is no import in either
  direction. Both reach the marker through the target.
- Impact: the only prose stating why this module exists said something false about it, so a reader
  looking for the constraint would look in the wrong place.
- Recommendation: state the actual property - the two modules are independent and share the marker
  through `_boundary_ordering.py`.
- Proof: the corrected docstring on the same row; the property itself is visible in the import lists.

### Rejected findings

- **`csrf_exempt(package_view)` silently loses its `True`.** Real, and harmless: Django's decorator
  sets `csrf_exempt = True` before `functools.wraps` copies the view's `__dict__` over it, so the
  package's object wins. The endpoint was never exemptible - `views.py::_run_after_csrf_check` is
  package-owned and unconditional - so the outcome is unchanged from before Decision 18 (`403` for an
  untokened POST, verified in scratch); only which class refuses moves. A consumer who wants
  Strawberry's own CSRF semantics mounts Strawberry's own view.
- **`__bool__` does not verify that the published request is the request being checked.**
  Unactionable by construction: `CsrfViewMiddleware` reads the mark as a bare truthiness with no
  request in hand, so the `ContextVar` *is* the only available answer to "which request is this". The
  state that would matter - a stamped request published while a different package callback is
  CSRF-checked in the same context - needs a nested in-process handler dispatch, which is not a
  production shape; per-request contexts (one task per ASGI request, `sync_to_async`'s copied
  context) keep concurrent requests from sharing the variable.
- **The docstring claim "imports nothing but the standard library" is unpinned.** True but
  consequence-free: both consumers already import Django and Strawberry, so the property buys nothing
  a test could protect, unlike the `channels`-absence claim in `views.py`.
- **`_CsrfOrderingExemption` has no `__repr__`.** No reader: nothing in Django, Strawberry,
  `cross_web`, or `debug_toolbar` renders a callback's `csrf_exempt` value.

### DRY analysis

- The boundary method's name was written at two sites that must change together - `_BOUNDARY_METHOD`
  in the target and a literal attribute access in
  `middleware/request_body.py::GraphQLRequestBodyBoundaryMiddleware.process_view`. Consolidated onto
  the protocol module, which the target's docstring already claimed as sole owner (Medium 1).

## Summary

The module is sound: small, single-purpose, and the one design decision in it - keying the exemption
off a per-request stamp plus a published request rather than off "the middleware is installed" - holds
up against every state reachable in the chain, and both branches of `__bool__` behave as documented.
What the review found was not a defect in its behavior but two gaps in the guarantees around it: the
one name it exists to own was restated at the call site that consumes it, and the shipped deployment's
use of it was proven statically rather than by a request. Both are fixed at their owners, with tests
that fail in both drift directions.

## Implementation (Worker 1)

Changed files:

- `django_strawberry_framework/middleware/request_body.py` - `process_view` now invokes the boundary
  through `_BOUNDARY_METHOD` instead of a literal attribute access, and its docstring says why. This
  is the root-cause site for Medium 1: the target can only be the single owner of the name if its
  consumer reads the name from it. Named here as the deliberate cross-file expansion of ownership.
- `django_strawberry_framework/_boundary_ordering.py` - the module docstring and the
  `_BOUNDARY_METHOD` comment now state that the name is both probed and invoked from here, so the
  single-ownership claim is literally true rather than aspirational.
- `tests/test_views.py` - the new package-tier row and its scaffolding (Medium 1's proof), plus the
  corrected dependency-direction docstring (Low 3).
- `examples/fakeshop/test_query/test_transport_api.py` - the recording CSRF subclass, the
  chain-derivation helper, the `_SAFE_METHODS` tuple, and the live row (Medium 2's proof).

Permanent tests:

- `tests/test_views.py::test_the_middleware_runs_the_boundary_it_probed_the_class_for` pins that the
  name the recognition accepts a class for is the name `process_view` invokes, using a class whose
  only package-view property is a callable installed under `_BOUNDARY_METHOD`, and asserts the stamp
  as well so the row states `process_view`'s whole promise. Package tier because its input is a
  synthetic non-package class, unreachable from any real GraphQL request.
- `examples/fakeshop/test_query/test_transport_api.py::test_the_configured_csrf_class_checks_fakeshops_real_mount_behind_the_boundary`
  pins the withdrawal behaviorally over the shipped chain: a live `/graphql/` POST, the project's own
  CSRF class recorded as having been handed the callback in a checkable state, and a `200` behind it.
  Live tier, which is where `AGENTS.md` puts anything a real request can earn.

Verification:

- Scratch: `docs/review/temp-tests/_boundary_ordering/test_probe.py`, 6 passed - see Verification
  above for what each row proved. Untracked and disposable.
- Drift experiment: with `process_view` temporarily calling a name the probe does not accept, the new
  package-tier row fails with `AttributeError: '_MinimalBoundaryViewClass' object has no attribute
  '_enforce_request_boundary_drifted'`. Reverted immediately; the scoped diff carries no trace.
- Failability of the live row: proven in scratch by pinning `__bool__` to `True` - the recorder sees
  nothing while the response stays `200`.
- Focused runs: `uv run pytest tests/test_views.py examples/fakeshop/test_query/test_transport_api.py
  --no-cov -n0` - 278 passed. `uv run pytest tests/test_build_tree_md.py tests/test_ci_governance.py
  --no-cov -n0` - 42 passed (the docstring edits touch no module's first line, so `docs/TREE.md` stays
  in sync). No full suite run.
- `uv run ruff format .` - 418 files unchanged. `uv run ruff check --fix .` - 2 fixed, 0 remaining
  (an unnecessary `noqa` on the new recorder function). `scripts/check_trailing_commas.py` reformatted
  the live file's new tuple and signature and then passes `--check`; `ruff format --check .` and
  `ruff check .` both clean.

Rejected findings: evidence recorded under `### Rejected findings` above, each with the caller, source
line, or scratch row that contradicts it.

Changelog: no entry earned and none written. The only production change is which expression reaches an
identically-named method; no consumer-visible behavior moves.

## Independent verification (Worker 2)

Re-traced from the constants outward rather than from the diff: both marks and the method name back
to their readers (`views.py::_RequestBodyBoundaryMixin.as_view`,
`views.py::_RequestBodyBoundaryMixin._enforce_request_boundary_once`,
`middleware/request_body.py::_package_view_instance`,
`middleware/request_body.py::GraphQLRequestBodyBoundaryMiddleware.process_view`, and Django's
`csrf.py::CsrfViewMiddleware.process_view`), then forward again through fakeshop's shipped chain with
real requests. Scratch: `docs/review/temp-tests/_boundary_ordering/test_worker2_probe.py` (12 rows)
and `docs/review/temp-tests/_boundary_ordering/test_worker2_live_failability.py` (3 rows), all green,
written without reading Worker 1's scratch file.

### The production change

Behavior-equivalence checked rather than assumed: the lookup sits inside the same `try`, so a
descriptor that raises still leaves `process_view` exactly where it did, and an `HTTPException` raised
by the lookup is still translated. Confirmed by execution that the invoked name now follows the
constant - with `_BOUNDARY_METHOD` rebound in the middleware's namespace, `process_view` runs a class
whose only callable sits under the *new* name and stamps the request, and a class carrying only the
old name is declined with no stamp and no boundary run. The refusal arm still works through the
indirection (a real mount at `max_request_body_bytes=10` answers `413 text/plain` and leaves the
request unstamped), and the real `/graphql/` callback is still recognized, run, and stamped.

No literal spelling of the boundary method survives in the middleware: the only remaining occurrence
there is a prose symbol reference to `_enforce_request_boundary_once`. `views.py` keeps its
definition-site spellings, which is not the duplication the finding was about.

### Findings disposed

- **Medium 1 - accepted, with one honest qualification.** The pre-fix failure mode is real, not
  hypothetical: on the identical input the probe accepts, the pre-fix call site raises
  `AttributeError` (reproduced in scratch by running the literal against the instance
  `_package_view_instance` returned). The qualification the artifact already states plainly is worth
  restating as a verification result: `tests/test_views.py::test_the_middleware_runs_the_boundary_it_probed_the_class_for`
  does **not** fail on the pre-fix tree, because the constant and the literal agreed there - a latent
  duplication has no observable regression to witness. It is a drift guard, and it fails in both
  drift directions (constant renamed with a literal call site -> `AttributeError`; call site renamed
  -> the boundary never runs and the stamp assertion fails). Verified by rebinding the constant
  rather than by trusting the report.
- **Medium 2 - accepted, and the row is genuinely failable.** Re-ran the permanent row's own
  scaffolding (the real `_RecordingCsrfMiddleware` and the real `_with_the_projects_own_csrf_class`,
  imported from the live module) under `_CsrfOrderingExemption.__bool__` pinned to `True`: the call
  log comes back empty while the response stays `200`, so the log is the whole witness and the status
  code sees nothing - exactly as claimed. Dropping the boundary entry out of the derived chain empties
  the log the same way, so the row also catches the settings-edit regression it was written for. The
  recorder's two deferrals are the right ones: recording requires the callback to be non-exempt at
  check time, which is the property under test.
- **Low 3 - accepted.** There is no import in either direction between `views.py` and
  `middleware/request_body.py`; every mention is prose. The corrected docstring states the property
  the module actually has.
- **Rejected: `csrf_exempt(package_view)` loses its `True`.** Confirmed independently from Django's
  source (`views/decorators/csrf.py`: `_view_wrapper.csrf_exempt = True` precedes
  `wraps(view_func)(_view_wrapper)`, whose `__dict__.update` copies the package's object over it) and
  by request: a `csrf_exempt`-wrapped package mount still answers `403` to an untokened POST under
  `enforce_csrf_checks=True`. Harmless, as recorded.
- **Rejected: `__bool__` does not verify request identity.** Confirmed unactionable by construction -
  `csrf.py::CsrfViewMiddleware.process_view` reads `getattr(callback, "csrf_exempt", False)` with no
  request in hand, so no signature exists in which the object could compare one. Probed the state
  matrix directly through the `ContextVar`: unpublished -> true, published-and-unstamped -> true,
  published-and-stamped -> false and true again after the reset, a stamped request that is not the
  published one -> true, a falsey stamp value -> true. Also reasoned through the one production-shaped
  way the two could diverge - a chain entry that substitutes the request object for downstream - and
  it degrades to the view-local arrangement (exemption true, boundary already run, view's own CSRF
  continuation) rather than to a premature parse.
- **Rejected: the standard-library-only claim is unpinned.** Confirmed consequence-free: the module
  imports `contextvars` and `typing` plus a `TYPE_CHECKING`-only `HttpRequest`, and both consumers
  already import Django, so no consumer gains anything a test could defend.
- **Rejected: no `__repr__`.** Confirmed by grepping the installed dependency set: the only
  `csrf_exempt` readers are `django/middleware/csrf.py:420` and
  `django/contrib/admin/sites.py:254`, both truthiness reads; `strawberry`, `cross_web`, and
  `debug_toolbar` never read it (debug-toolbar only decorates its own views).

### Tier, coverage, and scope

The changed production line is reachable from a real query and is exercised live by every
`/graphql/` POST through fakeshop's shipped chain, including the new row; what the package-tier row
adds is a statement about a synthetic class, which no real request can express, so `tests/` is the
correct tier for it under `AGENTS.md` rather than a fallback. Coverage spot check with the two owning
files alone: `_boundary_ordering.py` 12/12 and `middleware/request_body.py` 71/71 statements, both
100%, 278 passed - so the edit left no line unreached. `ruff format --check`, `ruff check`, and
`scripts/check_trailing_commas.py --check` are clean on all four changed files.

Scope is clean. `git diff 6eaeff95 --` over the four files shows only the fix, the two new rows and
their scaffolding, and the corrected docstring; nothing unrelated was absorbed. The wider diff also
carries `docs/SPECS/spec-002-*`, `spec-006-*`, and `spec-007-*` edits, which are other sessions' work
and were left untouched. Changed comments and docstrings describe the final behavior: the target and
the middleware now both say the name is probed *and* invoked from here, which is what the code does.

### Forwarded, not blocking

- A chain listing the boundary middleware twice ahead of CSRF passes `_require_boundary_before_csrf`
  and runs the boundary twice, because `process_view` calls `_enforce_request_boundary` rather than
  the `_once` variant. Idempotent and same-verdict, so not a defect of this target; it belongs to
  `docs/review/rev-middleware__request_body.md`.
- The new live row is sync-only. `__acall__`'s publication and reset are pinned at package tier by
  `test_the_async_chain_resets_the_ordering_mark_around_the_downstream_call`, and an async twin was
  not part of Medium 2, so this is an observation rather than a gap to fix here.

Verdict: complete. Both accepted findings are fixed at their owners, every rejection holds under
independent checking, the tests fail for the reasons they claim, and I could not construct an input,
ordering, or state sequence that breaks the result.
