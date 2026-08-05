# Build: Round R1 — remediation review of `2701f41a` + `ba66ab49`

Review reference: `docs/feedback.md` — four findings: `[P1]` "A contradictory JSON charset
declaration restores the parser differential", `[P1]` "The CSRF reorder bypasses the project's
configured CSRF middleware class", `[P2]` "A foreign position object's arithmetic still escapes
the fail-closed body gate", `[P2]` "Cancellation of disconnect lets the connection-owned close
task outlive the connection".
Spec reference: `docs/spec-046-transport_security-0_0_15.md` — Decision 7 (the counted body cap
and the three probe outcomes), Decision 9 (the strict UTF-8 wire contract), Decision 10 (the BOM
refusal), Decision 16 (connection-scoped revocation and the close state machine), Decision 17
(multipart control fields), Decision 18 (the body gate ahead of Django's multipart parser).
Build plan: `docs/builder/build-046-transport_security-0_0_15.md`, `# Closeout cycle (card 046)`,
round R1.
Status: final-accepted

## Round preamble

This is a **review round** in the `BUILD.md` `## Review rounds` sense: the input is
already-built, already-**committed** work. The maintainer's review document is `docs/feedback.md`
and the remediation of all four of its findings landed in two commits outside the worker cycle,
so **no Worker 3 pass has ever seen the diff** (plan V8). R1 is that audit.

### The diff under audit, exactly

`git show 2701f41a` and `git show ba66ab49`. Equivalently `git diff ccfe17e1..HEAD`, because
`ccfe17e1` is `2701f41a`'s parent.

**Do not use `git diff 89cfa974..HEAD`.** Measured with `git diff --numstat 89cfa974..HEAD`, that
range also sweeps in `ccfe17e1` (the spec-045 archive) and with it
`django_strawberry_framework/utils/querysets.py` (+109/-32), `tests/utils/test_querysets.py`
(+298/-21), the `docs/SPECS/` moves, and the `bld-045-*` artifacts — none of which is R1's to
audit, and several of which the cycle's `## Do-not-touch` names.

R1's own diff, by `git show --numstat`:

| File | 2701f41a | ba66ab49 |
| --- | --- | --- |
| `django_strawberry_framework/views.py` | +135/-26 | — |
| `django_strawberry_framework/middleware/request_body.py` | +264/-0 (new file) | — |
| `django_strawberry_framework/_request_body.py` | +22/-7 | — |
| `django_strawberry_framework/consumers.py` | — | +80/-29 |
| `examples/fakeshop/apps/kanban/constants.py` | +1/-0 | — |
| `tests/test_views.py` | +578/-21 | — |
| `tests/test_routers.py` | — | +207/-0 |
| `docs/feedback.md` | — | +109/-107 (maintainer's own; never touch) |

### Baseline, measured this pass

- `git status --short` reports exactly one modified path:
  `docs/builder/build-046-transport_security-0_0_15.md` — Worker 0's appended closeout section,
  uncommitted. Not R1's to edit and not to revert (`AGENTS.md` #34).
- `uv run pytest tests/test_views.py tests/test_routers.py --no-cov` — **324 passed**.
- `uv run pytest examples/fakeshop/test_query/test_transport_api.py --no-cov` — **69 passed**.
  This file is **not** in either commit's diff and its scaffolding reads
  `view_class.as_view().csrf_exempt` off the package callback, which `2701f41a` turned from `True`
  into an object; it is green at `HEAD`, so the live transport tier is a valid reference rather
  than a pre-existing failure to difference out.
- Every failability-proof baseline in this round therefore starts green, and a mutant's failing
  set needs no differencing.
- The shared `.venv` is far above the floor: the pytest header printed
  `Python 3.14.2` / `django: version: 6.0.5` (read from the run, never stated from memory). That
  gap is exactly why the floor run below is R1's and not the final gate's.

### Worker-0-verified facts this round consumes

V8 (all four findings remediated at `HEAD`, unaudited) is R1's whole remit. V1, V2, V3, V5, V6,
V7 are documentation gaps owned by **R3**; V4 (the spec still asserts the `CLOSING` ruling
`ba66ab49` retracted) is owned by **R2**. R1 records anything it notices about those under
`### Notes for Worker 1 (spec reconciliation)` and fixes none of them: this pass may write only
this artifact, and a defect-fixing pass may write only the files the plan's R1 ownership list
names.

---

## Plan (Worker 1)

### Why there is no Worker 2 pass ahead of the review

**This round's "build pass" is `2701f41a` + `ba66ab49`.** The maintainer wrote and committed the
remediation outside the cycle, so there is no builder to dispatch first and no builder-authored
`## Build report (Worker 2)` in this artifact. Three consequences, all mechanical:

1. **Every box in `### Dispatched findings checklist` stays `- [ ]` at planning.** Worker 2 is the
   only role that ticks during a build pass and there is no such pass; **Worker 1 ticks the landed
   boxes at final verification** under `ARTIFACT.md`'s "tick any landed box Worker 2 left open".
   Worker 0 never writes to that list, and never to `Status:`.
2. **The obligations a build pass owes are unfilled, not waived.** Ten landed boundaries carry
   **zero** failability proofs, and no hot-path number was ever captured. `### Failability proof
   set (owner: Worker 3)` and `### Hot-path budget` below assign both, because an obligation with
   no owner is one the round closes without.
3. **A confirmed defect routes forward, not backward.** Worker 3 sets `revision-needed`, Worker 0
   dispatches Worker 2 against the R1 ownership list (`views.py`, `consumers.py`,
   `middleware/request_body.py`, `_request_body.py`, `tests/test_views.py`, `tests/test_routers.py`
   and `docs/builder/temp-tests/r1/**`), Worker 3 re-reviews, and only then does Worker 1's final
   verification run.

### DRY analysis

**Helper inventory checked.** Refreshed for the **whole package** this pass
(`docs/shadow/helper-inventory.md`, 1,696 lines, regenerated from the `worker-1.md` snippet).
Shapes searched: `charset`, `encoding`, `csrf`, `middleware`, `content_type`, `text/plain`,
`exempt`, `marker`, `process_view`, `settle`, `cancel`, `position`, `measur`. Relevant
candidates found: `views.py::_canonicalizes_to_utf8`, `views.py::_form_encoding_is_utf8`,
`views.py::_is_multipart_form_post`, `_request_body.py::_declares_seekable`,
`_request_body.py::_position_restored`, `_request_body.py::_measured_remaining`, and
`middleware/debug_toolbar.py::DebugToolbarMiddleware.process_view` — the package's **other**
middleware, which answers "is this one of our views?" a different way (see (c) below).
`scripts/review_inspect.py --output-dir docs/shadow` was also run against all four production
files in the diff; the new module's overview reports **0 repeated string literals, 0 control-flow
hotspots, 0 Django/ORM markers**, so the usual DRY signals are absent and the questions below are
placement questions instead.

**Existing patterns the landed diff reuses (correctly, verified by reading):**

- `views.py::_RequestBodyBoundaryMixin._enforce_body_charset_declaration` calls the existing
  `views.py::_canonicalizes_to_utf8` rather than name-matching a codec, so every UTF-8 alias is
  accepted and `utf-8-sig` is refused by the same rule `_form_encoding_is_utf8` uses.
- It is scoped by the existing single discriminator `views.py::_is_multipart_form_post`, the same
  one the cap's carve-out and the multipart encoding guard use, so the three guards cannot drift
  apart on what "multipart" means.
- `middleware/request_body.py::GraphQLRequestBodyBoundaryMiddleware.process_view` states **no
  policy**: it instantiates the resolved view and calls the view's own
  `_enforce_request_boundary`, so the limit is the mount's.
- The set-token / reset-in-`finally` ContextVar idiom is package-wide already: measured
  `grep -rn '\.reset(' django_strawberry_framework/` returns **11 sites across 4 modules**
  (`permissions.py`, `optimizer/extension.py`, `utils/write_transaction.py`, and now
  `middleware/request_body.py`). No shared helper exists and none is justified — **decided: do not
  extract.** The condition that would change the answer is a fifth module needing the same
  set-around-a-downstream-call shape *with* an async twin.

**Placement / duplication questions Worker 3 must answer (this is the round's DRY read):**

- **(a) Where the marker constants and the exemption object live.** `_BOUNDARY_MARKER`,
  `_BOUNDARY_ENFORCED`, `_boundary_middleware_active` and `_CsrfOrderingExemption` sit in
  `middleware/request_body.py`, and `views.py` now imports three of them from there — a core view
  module importing from the `middleware/` subpackage. The module docstring justifies the direction
  ("`views.py` imports this module for the exemption object, so this module must never import
  `views.py`"), but that only rules out the *reverse* import; it does not establish that either
  direction is needed. The alternative is the already-private, already-view-imported
  `django_strawberry_framework/_request_body.py` as the home for the two attribute names, the
  ContextVar and the exemption class, leaving `middleware/request_body.py` holding only the
  middleware — after which neither module imports the other. Answer it as an **existence
  challenge** on the coupling, not as a style preference; if the current placement is right, say
  what makes it right.
- **(b) Two modules named the same thing.** `django_strawberry_framework/_request_body.py`
  (measurement primitives) and `django_strawberry_framework/middleware/request_body.py` (lifecycle
  ordering) now coexist. Is the collision a maintainability cost worth a rename, or is the
  `middleware/` prefix disambiguation enough? A rename touches `views.py`, `tests/test_views.py`,
  `examples/fakeshop/apps/kanban/constants.py` and R3's doc work, so decide it here or explicitly
  defer it to R3 rather than leaving it unanswered.
- **(c) Two "is this one of our views?" mechanisms in one package.**
  `middleware/debug_toolbar.py::DebugToolbarMiddleware.process_view` uses
  `getattr(view_func, "view_class", None)` plus `isinstance(view, type) and issubclass(view,
  BaseView)`; `middleware/request_body.py::process_view` uses a stamped marker attribute and
  *then* reads `view_func.view_class(**view_func.view_initkwargs)`. Both middleware run for all
  global traffic and both depend on `view_class`. Is one shared recognizer justified, or does the
  one-way-dependency argument (a marker cannot import the view classes) make them genuinely two
  decisions? Note the asymmetry to check: `debug_toolbar` guards `issubclass` against a non-class
  `view_class` because "an unrelated decorator" may attach one, while `request_body` reads
  `view_func.view_class(...)` **unguarded** after the marker test — decide whether the marker is a
  strong enough precondition for that.
- **(d) `__call__` / `__acall__` twin bodies.** Identical apart from the `await`. Consistent with
  the package's established sync/async twin idiom (`views.py::_run_after_csrf_check` /
  `::_async_run_after_csrf_check`, and both `run` overrides), and the docstring names the reason
  sharing is wrong (a synchronous `finally` would reset the mark before the CSRF middleware read
  it). **Decided: not a finding.** It becomes one only if a *third* copy of the shape appears.
- **(e) The `HTTPException` -> `text/plain` translation.** `process_view` rebuilds the response
  upstream's `dispatch` produces for the same exception. Measured: `text/plain` occurs **3 times**
  in the package across 2 files, of which exactly **1 is executable**
  (`middleware/request_body.py::process_view`), so this is not a repeated literal — the duplication
  is of *upstream's* logic, and the deliberate reason is that a client must not be able to tell
  which side of the CSRF check refused it. Confirm the two shapes actually agree (status, reason
  body, content type) rather than only claiming to.

No new helper is proposed by this plan: R1 writes no production code unless it confirms a defect,
and any fix then reuses the shapes above.

### Implementation steps

There is no implementation. These are the **verification steps Worker 3 owns**, in review order,
with the commands to run.

1. **Read the diff as scoped above** — `git show 2701f41a`, `git show ba66ab49`. Read the full
   current body of each touched symbol, not only the `+` lines: three of the four fixes changed a
   docstring contract as well as code, and one of those claims is a floor question (step 10).
2. **Walk the four per-finding contracts below**, in order, answering each named property with
   evidence (a row, a command, or a read). A property answered by prose alone is not answered.
3. **Walk `### Fail-open shapes to read for`.** Nothing else in this process can see these.
4. **Walk `### Non-weakening checks`.** These are the already-accepted contracts the remediation
   could have silently traded away.
5. **Run the failability proof set** (`### Failability proof set (owner: Worker 3)`) via
   `scripts/prove_failability.py`, manifest at `docs/builder/temp-tests/r1/proofs.json`, and paste
   the emitted block into the review section.
6. **Answer the DRY read** (a)-(e) above, each with a decision.
7. **Public-surface check.** `git diff ccfe17e1..HEAD -- django_strawberry_framework/__init__.py`
   is expected to be **empty**; the new public name is reached only by its full dotted
   `MIDDLEWARE` path, which matches `middleware/__init__.py`'s documented "deliberately NO
   re-export here". Confirm, and confirm `__all__` in the new module is the single-name tuple.
8. **Capture the hot-path number** (`### Hot-path budget`).
9. **Test-staleness sweep** (`### Test additions / updates`, last bullet).
10. **Run the floor verification** (`### Floor verification scope`), including its five named
    floor questions.
11. **Record `scripts/review_inspect.py` disposition.** `BUILD.md` `### When to run the helper
    during build` requires it for a new `.py` file of any size; Worker 1 generated
    `docs/shadow/django_strawberry_framework__middleware__request_body.overview.md` this pass, so
    Worker 3 may read that rather than regenerate, and records which it did.

Line-free by design: every citation in this plan is symbol-qualified, so no step needs re-pinning
against a shifted file.

### Per-finding verification contracts

#### P1a — the declared JSON charset

*Landed at* `views.py::_RequestBodyBoundaryMixin._enforce_body_charset_declaration`, composed
third in `::_enforce_request_boundary`.

*Properties that must hold.* (i) A non-multipart, non-GET request whose content type declares a
charset that does not canonicalize to UTF-8 is refused **before the body is parsed**, with
`400` and `_JSON_PARSE_REASON` — the same reason every other refusal on this boundary carries, so
a caller cannot attribute a rejection by message. (ii) Absent declaration passes. (iii) Every
UTF-8 alias passes; `utf-8-sig` and an unknown codec name do not. (iv) A multipart POST is left to
`::_enforce_multipart_form_encoding` and a GET is left alone — the two guards own disjoint request
shapes, and neither a gap nor an overlap is acceptable. (v) Both transports enforce it, from the
one composed method.

*Rows that pin it.* `tests/test_views.py::test_the_endpoint_refuses_a_json_charset_it_will_not_
decode_with` — 6 declarations x 2 transports = **12 rows** (measured by collection), driven over
the real endpoint with `Client().generic` / `AsyncClient().generic` so the declared charset does
not re-encode the body, and carrying a non-ASCII UTF-8 document whose `C3 A9` is the cross-hop
differential itself; `::test_a_non_multipart_request_is_not_subject_to_the_form_encoding_check`
(both halves asserted on one request); `::test_a_multipart_declaration_is_left_to_the_form_
encoding_guard`.

*Failability question.* Would deleting the refusal fail rows? Proof entries 1 and 2.

*Open questions Worker 3 must answer.* (1) **Method scope.** The guard excludes `GET` only, so a
`HEAD`, `PUT` or `DELETE` carrying `charset=iso-8859-1` now gets `400` where upstream would have
answered `405`. `::_enforce_request_body_limit` skips `GET` the same way and
`::_is_multipart_form_post` documents "counted like any other body, which is the stricter
direction" for non-GET/POST methods, so the shapes are consistent — but the `HEAD` asymmetry
(no body, yet refused where `GET` is not) is either deliberate or an oversight. Decide against
Decision 9, and record which. (2) Confirm the `400` really reaches the wire as upstream's
`text/plain` translation on **both** transports and in **both** CSRF arrangements (the middleware
path builds the response itself — see (e)).

#### P1b — the project's configured CSRF class

*Landed at* the new `middleware/request_body.py` (`::GraphQLRequestBodyBoundaryMiddleware`,
`::_CsrfOrderingExemption`, `::_require_boundary_before_csrf`, `::_boundary_middleware_active`)
plus `views.py::_RequestBodyBoundaryMixin.as_view` (which now stamps two marks instead of applying
`csrf_exempt`) and `::_enforce_request_boundary_once`.

*Properties that must hold.* (i) **With the middleware installed ahead of the CSRF entry**, the
boundary runs from `process_view` before any later `process_view`, and the project's *configured*
CSRF class — base or subclass — then runs in full. (ii) **Without it**, behaviour is byte-for-byte
what it was: the callback's exemption is truthy, the project's CSRF middleware skips the callback,
and the view enforces the boundary then re-enters CSRF through `csrf_protect`. (iii) **Exactly one
complete CSRF check** runs on every request that passes the boundary, in **both** arrangements —
in the installed arrangement the view's continuation must be the no-op
`csrf_processing_done` makes it, not a second check and not a skipped one. (iv) **The boundary can
never run zero times**: neither arrangement, nor the pair of them interleaved in one process, may
produce a request that reaches Strawberry unmeasured. (v) A chain listing the boundary *after* a
CSRF entry fails at startup rather than serving requests whose parse precedes the cap. (vi) A
non-package view is passed through untouched. (vii) The ordering mark is request-scoped and
cannot leak into the next request the worker handles, on either chain, including when the
downstream chain raised.

*Rows that pin it.* `tests/test_views.py::test_the_chain_refuses_an_over_limit_multipart_before_
any_csrf_read` (2 — empty CSRF call log is the ordering witness);
`::test_the_projects_own_csrf_middleware_runs_when_the_chain_supplies_the_ordering` (2 — the
subclass's own refusal, not a package response, is what the client gets);
`::test_without_the_middleware_the_view_keeps_its_own_ordering_and_exemption` (2);
`::test_the_middleware_passes_a_non_package_view_through_untouched` (1);
`::test_the_view_does_not_measure_a_body_the_chain_already_measured` (2);
`::test_a_chain_that_lists_the_boundary_after_csrf_is_refused_at_startup` (1, plus three
accepting chains inside the same row); `::test_the_async_chain_resets_the_ordering_mark_around_
the_downstream_call` (1); `::test_the_view_callback_of_both_views_carries_the_csrf_exempt_mark`
(re-pinned to `bool(view.csrf_exempt) is True` plus the marker).

*Failability question.* Would removing each of the four decision points fail rows? Proof entries
3, 4a, 4b, 5, 6.

*Open questions Worker 3 must answer.*

1. **The exemption is withdrawn chain-wide, but the boundary is run per-marked-view.**
   `__call__` / `__acall__` set `_boundary_middleware_active` for **every** request travelling the
   chain, while `process_view` runs the boundary only for a callback carrying `_BOUNDARY_MARKER`.
   So any request where the marker is absent but the middleware is installed has the exemption
   withdrawn **and** the boundary un-run at `process_view` time: the configured CSRF middleware
   reads `request.POST` (parsing a multipart body) and the view's own
   `_enforce_request_boundary_once` then measures a body that is already materialized. That is the
   ordering failing open by exactly the route `_require_boundary_before_csrf` exists to close off.
   Is the marker loss reachable? `views.py::as_view`'s own docstring names "a wrapper that drops
   the attributes" as a live shape, and `functools.wraps` copies `__dict__` (so both marks travel
   together, which is the mitigating fact). Decide whether the two facts — "exemption withdrawn"
   and "boundary actually run" — should be one fact rather than two, i.e. whether the exemption
   should key off the per-request `_BOUNDARY_ENFORCED` stamp instead of the chain-wide ContextVar.
   A temp test under `docs/builder/temp-tests/r1/` with a marker-dropping wrapper mount is the
   cheap way to answer it.
2. **Boundary installed, no CSRF middleware in the chain.** `_require_boundary_before_csrf`
   deliberately permits it, and the exemption is withdrawn anyway, so the endpoint's only CSRF
   check is the view's unconditional continuation. `::test_a_chain_that_lists_the_boundary_after_
   csrf_is_refused_at_startup` accepts that chain at **startup** only; no row drives a **request**
   through it. Confirm the endpoint is still CSRF-protected there, and if nothing pins it, that is
   a missing row rather than an accepted gap.
3. **`_require_boundary_before_csrf` reads `settings.MIDDLEWARE` and `import_string`s every
   entry** at chain-build time — including entries Django has not imported yet, since the chain is
   built in reverse. Confirm that forcing those imports early is harmless (no double side effects,
   no ordering surprise) and that a `MIDDLEWARE` entry that fails to import produces a
   comprehensible failure rather than one attributed to this middleware.
4. **The audit records only the FIRST CSRF entry** (`elif ... and csrf_index is None`) and the
   **last** boundary entry. Enumerate what a duplicated entry of either kind does and whether the
   refusal still holds.
5. **Async chain mechanics.** In an ASGI chain Django adapts the sync `process_view` through
   `sync_to_async`, so the boundary runs in a thread while the ContextVar was set on the event
   loop, and `setattr(request, _BOUNDARY_ENFORCED, True)` crosses back on the shared request
   object. The async rows pass, so it works in this asgiref; name the mechanism that makes it work
   rather than treating the green run as the explanation, because the floor's asgiref is older
   (step 10).

#### P2a — the foreign position object

*Landed at* `_request_body.py::_measured_remaining` `#"if type(end) is not int or type(position)
is not int"`, replacing a `try: remaining = end - position / except TypeError`.

*Properties that must hold.* (i) **No foreign numeric protocol executes inside the gate** — not
`__sub__`, not `__le__`, not on an `int` subclass (which is what gets past an `isinstance` check).
(ii) The verdict for any non-exact-`int` position or end is `_Probe.UNMEASURABLE`, which routes to
`::_bounded_read_exceeds_limit` and still supplies a bound — verified by reading
`::body_exceeds_limit`: `CORRUPTED` -> `True` (refuse), `UNMEASURABLE` -> bounded read, otherwise
`remaining > limit`. (iii) The type test happens **after** the verified restore, so the bounded
read that follows starts where the request started. (iv) The exact-`int` rule matches the rule
`views.py::_resolved_max_request_body_bytes` already applies, for the same stated reason.

*Rows that pin it.* `tests/test_views.py::test_a_position_object_whose_numeric_protocol_raises_
never_runs_inside_the_gate` — 2 hostile streams x 2 view classes = 4 rows, asserting the `413`
**and** the `limit + 1` read ceiling, bytes left unread, and `_body` never materialized;
`::test_a_probe_that_fails_without_moving_the_stream_falls_back_to_the_bounded_read`
[`unnumbered-end-position`] (2).

*Failability question.* Proof entry 7.

*Open questions Worker 3 must answer.* (1) The new docstring claims "`SpooledTemporaryFile` and
`LimitedStream` both do [report exact `int` positions], on both supported interpreters". That is a
floor claim about Python 3.10 / Django 5.2.0 asserted from a 3.14 / 6.0 environment — step 10
carries the one-liner that answers it. If it is false, the docstring is wrong even though the
behaviour is fail-safe, and a load-bearing wrong comment is a finding. (2) `_position_restored`
still runs a foreign `__eq__` and a foreign `seek(position)` — both inside `except Exception`, so
total, but confirm the exception boundary is still complete now that the type test moved
downstream of it.

#### P2b — the orphaned close task

*Landed at* `consumers.py::_ConnectionRevocation.settle` (the cancel-and-await-and-re-raise arm),
`::_attempt_close` (a `CancelledError` arm recording `ABANDONED` before re-raising), the
`_ConnectionRevocation` class docstring (the `CLOSING` ruling retracted), and
`::build_revalidating_consumer_class`'s generated `disconnect` (`try` / `finally`).

*Properties that must hold.* (i) A cancellation delivered to `settle()` **ends** the attempt:
cancel, await to completion, re-raise, so the caller's cancellation is honoured and no task
retains the adapter, consumer, scope, session or stale actor past the connection. (ii) A cancelled
attempt is **terminal** — `ABANDONED`, never resting in `CLOSING`, which claims an attempt is in
flight. (iii) `ABANDONED` permits no second close: a later `settle()` puts no second `4403` on the
wire. (iv) `disconnect` reaches settlement through `finally`, so a cancelled **or raising**
upstream teardown cannot skip it, and the upstream exception still propagates. (v) The
**mid-connection** shield is untouched: a bystander checkpoint's cancellation must still not kill
a nearly-committed close.

*Rows that pin it.* `tests/test_routers.py::test_cancelling_the_teardown_ends_the_close_attempt_
instead_of_orphaning_it` (helper level, both halves asserted);
`::test_a_cancelled_disconnect_leaves_no_task_retaining_the_connection` (through the router's own
generated consumer, with upstream's `disconnect` patched on upstream's class);
`::test_a_teardown_that_raises_still_settles_the_close_and_propagates` (asserts the *ordering*,
not just the outcome: the teardown cannot complete while the transport holds the close parked).

*Failability question.* Proof entries 8, 9, 10.

*Open questions Worker 3 must answer.*

1. **`settle`'s `except asyncio.CancelledError` cannot distinguish who was cancelled.**
   `asyncio.shield(task)` raises `CancelledError` into the waiter both when the *waiter* is
   cancelled and when the *inner task* is cancelled by a third party. In the second case `settle`
   would cancel an already-cancelled attempt, suppress, and then `raise` — propagating a
   `CancelledError` out of `disconnect`'s `finally`, where it **replaces** a `RuntimeError` a
   failing upstream teardown had raised. Is a third-party cancellation of the attempt reachable
   (loop shutdown, a task group, `Channels`' own teardown), or is it out of contract because "only
   the connection's final teardown cancels this task"? If it is out of contract, say what enforces
   that; if it is reachable, the masking is a finding.
2. **A never-started attempt.** `_attempt_close` records `ABANDONED` from inside its own
   `except`, so a task cancelled *before its first step ran* leaves the state at `CLOSING` —
   contradicting property (ii). Establish whether the interleaving is reachable given that
   `close()` creates the task and immediately awaits it (so the loop schedules the task's first
   step before anything `disconnect` could queue). If it is harness-impossible, say so in those
   words and record the limitation (`BUILD.md` `### Harness-impossible interleavings`) rather than
   adding a wire-level row that cannot fail.
3. **The unbounded wait in `finally`.** `docs/feedback.md`'s prescribed fix offered "an equivalent
   structured-concurrency owner with a **bounded final wait**"; the landed fix has no bound and
   relies on the server's own application-close timeout to deliver the cancellation it now handles.
   A prescribed remediation is a hypothesis, not an instruction (`BUILD.md` `### Worker 0 verifies
   every finding against source`), and the pre-change code awaited the same shielded task just as
   unboundedly — so record this as **deliberate and unchanged**, or as a finding, but do not leave
   it unaddressed.
4. **`settle`'s new `self.attempt.done()` early return** must not skip a state transition: confirm
   every terminal state is written by the attempt itself, so a completed-then-settled attempt needs
   nothing from `settle`.

### Failability proof set (owner: Worker 3)

Ten landed boundaries, **zero** proofs on record, and no builder pass to owe them — so **Worker 3
performs them**, under the narrow source carve-out that exists so an independent re-run is
possible (`BUILD.md` `### Who performs it`; `worker-3.md` "Scope"): record the mutation before
making it, revert inside the same pass, prove the revert by byte comparison. Use
`scripts/prove_failability.py` so the loop is mechanized and the anchor check runs first:

```shell
uv run python scripts/prove_failability.py docs/builder/temp-tests/r1/proofs.json \
    --scratch-root /tmp/dsf-r1-proofs \
    --output docs/builder/temp-tests/r1/proofs.md
```

The manifest lives at `docs/builder/temp-tests/r1/proofs.json` (inside R1's declared writable
paths; `--scratch-root` must be **outside** the repo). Every anchor below was measured with
`grep -c -F` this pass and matches **exactly once**; the two `except asyncio.CancelledError:`
anchors match twice alone, so both are given as two-line blocks (the tool joins a list of lines
with newlines).

| # | Boundary | Anchor (exact) | Mutation | Scope |
| --- | --- | --- | --- | --- |
| 1 | `views.py::_RequestBodyBoundaryMixin._enforce_body_charset_declaration` (the refusal) | `        if declared is not None and not _canonicalizes_to_utf8(declared):` + its `raise` line | delete both lines | `tests/test_views.py` |
| 2 | the same method's carve-out | `        if request.method == "GET" or _is_multipart_form_post(request):` + `            return` | delete both lines (the guard claims every shape) | `tests/test_views.py` |
| 3 | `middleware/request_body.py::GraphQLRequestBodyBoundaryMiddleware.process_view` | `        if not getattr(view_func, _BOUNDARY_MARKER, False):` | replace with `        if True:` (never run the boundary, never stamp) | `tests/test_views.py` |
| 4a | `middleware/request_body.py::_CsrfOrderingExemption.__bool__` (withdrawal) | `        return not _boundary_middleware_active.get()` | `        return True` (never withdraws) | `tests/test_views.py` |
| 4b | the same, opposite direction | same anchor | `        return False` (always withdrawn) | `tests/test_views.py` |
| 5 | `middleware/request_body.py::_require_boundary_before_csrf` | `    boundary_index = csrf_index = None` | prepend `    return` (no ordering audit) | `tests/test_views.py` |
| 6 | `views.py::_RequestBodyBoundaryMixin._enforce_request_boundary_once` | `        if getattr(request, _BOUNDARY_ENFORCED, False):` | replace the body with `        return` (the view never enforces) | `tests/test_views.py` |
| 7 | `_request_body.py::_measured_remaining` (the exact-`int` gate) | `    if type(end) is not int or type(position) is not int:` + its `return` | delete both lines | `tests/test_views.py` |
| 8 | `consumers.py::_ConnectionRevocation.settle` (the cancellation arm) | `        except asyncio.CancelledError:` + `            self.attempt.cancel()` | delete the whole `except` block (bare shielded await) | `tests/test_routers.py` |
| 9 | `consumers.py::_ConnectionRevocation._attempt_close` (the terminal record) | `        except asyncio.CancelledError:` + `            self.state = _REVOCATION_ABANDONED` | delete the arm | `tests/test_routers.py` |
| 10 | `consumers.py::build_revalidating_consumer_class`'s `disconnect` | `                await super().disconnect(code)` | flatten `try`/`finally` back to two sequential awaits | `tests/test_routers.py` |

Entry 6 is the round's **"the boundary cannot run zero times"** proof: with the view's own
enforcement gone, every no-middleware row must fail. Entry 3 is its counterpart for the chain
arrangement, and its witness is the *empty CSRF call log*, not the status code — the over-limit
request is still refused after the mutation, just too late.

**Predictions, not measurements.** Worker 3 measures the failing node-id set for every entry and
records it; nothing here is a count to be trusted. My reading predicts >= 2 rows for entries 1, 2,
3, 4a, 4b, 7, 8, 9, 10 and a large set for 6, with **entry 5 predicted at exactly 1 row** — a
misordered chain raises at construction, so no behavioural row can exist beyond the startup one.

**Weakly-pinned handling.** 0 rows is unambiguous: nothing pins the boundary, `revision-needed`,
and the fix is more rows in `tests/test_views.py` / `tests/test_routers.py` (never a weaker
boundary). For **exactly 1** row, record the measurement and the merit judgement and route it to
the maintainer under the plan's still-open **M4** decision (`build-046-…` `## Open maintainer
decisions`) — do **not** re-litigate the rule itself, in either direction.

### Fail-open shapes to read for

Read for the shape; a fail-open expression is not a branch, so the green suite above says nothing
about any of these (`BUILD.md` `### Fail-open shapes`). My plan-time read is given so Worker 3 can
disagree with something specific.

- **`getattr(view_func, _BOUNDARY_MARKER, False)`** (`process_view`) — **the live suspect.** The
  default converts "this callback lost its marks" into "not our view, pass through", while the
  exemption has already been withdrawn chain-wide. Fail-open direction: the parse precedes the
  cap. See P1b open question 1.
- **`getattr(request, _BOUNDARY_ENFORCED, False)`** (`_enforce_request_boundary_once`) — reads
  fail-**closed** to me: absent means the boundary runs. The direction that would be fail-open is
  a request arriving already stamped without the boundary having run; a client cannot set an
  attribute on `HttpRequest` (headers become `META` keys), so confirm that and confirm no other
  package or Django code sets a same-named attribute.
- **`_measured_remaining`'s `if not probed` and `remaining <= 0` returns** — both answer
  `UNMEASURABLE`, which `body_exceeds_limit` routes to the bounded read, i.e. "cannot determine"
  becomes "measure by reading", not "permit". This is the corrected shape the prior round's
  `max(end - position, 0)` lacked. Confirm by following the call chain, not by reading the names.
- **`(request.content_params or {}).get("charset")`** — an `or` fallback whose left operand can be
  legitimately falsy, but both branches yield an empty mapping and the same answer. Pre-existing
  in `_form_encoding_is_utf8`. Benign on my read; confirm `content_params` cannot be a non-mapping.
- **`_declares_seekable`'s `return True` when `seekable` is absent** — a `getattr` default
  standing in for a meaningful absence, deliberately, because Python 3.10's
  `SpooledTemporaryFile` has no `seekable`. Unchanged by this diff; re-read it against the floor
  answer from step 10.
- **`_require_boundary_before_csrf`'s three-way early `return`** — `boundary_index is None or
  csrf_index is None or csrf_index > boundary_index` permits, everything else refuses. Enumerate
  the chains each disjunct admits and confirm none of them is a chain that parses before the cap.
- **`settle`'s `if self.attempt is None or self.attempt.done(): return`** — a truthiness-shaped
  early exit on a value whose two absent-ish cases mean different things ("never started" vs
  "already finished"). Confirm neither needs a state transition.
- **`contextlib.suppress(asyncio.CancelledError)` around `await self.attempt`** — a suppression
  wrapped around a wait, i.e. exactly the "the check blew up" -> "the check passed" shape, made
  safe only by the `raise` that follows. Confirm the `raise` is unconditional on every path
  through that arm.
- **`_CsrfOrderingExemption.__bool__` reading a ContextVar whose `default=False`** — a process
  default that resolves to "the view must supply the ordering itself", i.e. the backward-compatible
  arrangement. Confirm that is the safe default for a request that never travelled the chain.

### Non-weakening checks

Each of these is a contract a prior round already accepted, which this remediation could have
traded away silently.

1. **The mid-connection shield in `close()` is still there.** `consumers.py::_ConnectionRevocation
   .close` must still `await asyncio.shield(self.attempt)` — a bystander operation's cancellation
   (`complete` / `stop`) must not kill a nearly-committed close. Read it, and confirm the existing
   mid-connection rows still pin it (the round-2 revocation rows in `tests/test_routers.py`).
2. **Exactly one complete CSRF check, in both arrangements.** Installed: the configured class runs
   and the view's continuation becomes a no-op via `csrf_processing_done`. Not installed: the
   callback is exempt from the chain and the continuation is the check. Neither zero nor two.
   The `csrf_processing_done` half is a claim about Django internals — confirm it at the floor
   too (step 10).
3. **The boundary cannot run zero times.** Proof entries 3 and 6 together; plus the nesting shape
   (`as_view()` called from inside another view) which loses the *ordering* but must keep the
   *measurement*.
4. **The cap's declared/counted rungs and the multipart carve-out are unchanged.**
   `_enforce_request_body_limit` was not touched by this diff; confirm the middleware path reaches
   the same rungs with the same mount cap, since it builds its own view instance
   (`view_func.view_class(**view_func.view_initkwargs)`) without `setup()`.
5. **Upstream's coroutine marking and Django's `view_class` / `view_initkwargs` bookkeeping
   survive.** `as_view` now sets attributes on upstream's callback instead of wrapping it with
   `csrf_exempt`; `::test_the_view_callback_of_both_views_carries_the_csrf_exempt_mark` pins
   `view_class` and `view_initkwargs`, and the async transport's coroutine marking is what
   `csrf_protect` branches on. Confirm both.

### Test additions / updates

R1 adds no production code and therefore no tests unless a defect or a weakly-pinned boundary is
confirmed. What the pass owes instead:

- **Temp tests** under `docs/builder/temp-tests/r1/` (R1-owned, deleted or promoted at review
  close): a marker-dropping wrapper mount (P1b open question 1); a request driven through a chain
  carrying the boundary and **no** CSRF middleware (P1b open question 2); a third-party
  cancellation of `_ConnectionRevocation.attempt` (P2b open question 1). Each exists to show
  whether an existing assertion is non-distinguishing — if one demonstrates a real gap, the row it
  justifies belongs in `tests/test_views.py` / `tests/test_routers.py`, written by the fixing pass.
- **Rows a weakly-pinned verdict requires**, per `### Failability proof set`.
- **Staleness sweep** (`BUILD.md` `### Test staleness a focused run cannot see`). `2701f41a`
  changed a value every tree can read — `view.csrf_exempt` is no longer `True` but an object — and
  the live tier was **not** in the diff. Run `grep -rn 'csrf_exempt' tests examples --include='*.py'`
  and re-read every hit: measured this pass, 8 hits in `tests/test_views.py`, 1 in
  `tests/test_prove_failability.py` (prose), 1 in `examples/fakeshop/config/urls.py` (prose), and
  7 in `examples/fakeshop/test_query/test_transport_api.py`, of which
  `#"mark = view_class.as_view().csrf_exempt"` copies the object onto a probe mount. That file is
  green at `HEAD` (69 passed, above), so the sweep is a correctness read rather than a red-test
  hunt: confirm each surviving assertion still asserts what it meant to, and that none of them
  now passes only because a truthy object is truthy.

### Boundary count and the split question

Ten boundaries are under audit (the table above enumerates them: one charset refusal, one
carve-out, four in the new middleware, one view-side idempotence gate, one probe type gate, three
in the revocation/teardown path). Above the "roughly five" prompt, so the question is answered
rather than assumed.

**Decided: R1 stays one round.** The ten are one contract delivered in two commits, and the load
here is *reading plus one mechanized proof run*, not ten hand-written builder loops — which is the
overload `BUILD.md` `### Slice splitting` is guarding against. **The trigger for splitting is a
fixing pass:** if Worker 3 confirms defects in more than one of the three subsystems
(`views.py` + `middleware/request_body.py`; `_request_body.py`; `consumers.py`), Worker 0
dispatches one builder cohort per subsystem — their production files are disjoint, but
`tests/test_views.py` is shared by the first two, so those two **serialize** under
`BUILD.md` `### Parallel cohorts under a declared ownership partition` and only the
`consumers.py` / `tests/test_routers.py` cohort may run concurrently.

### Hot-path budget

**R1 as an audit: not applicable** — it writes no production code.

**But the landed remediation added per-request cost that no pass ever measured**, because there
was no builder pass to owe a number. Every request through a chain carrying the middleware now
pays a `ContextVar` set + `reset`, one `getattr` in `process_view`, and — on every non-multipart,
non-GET request, in both arrangements — one `content_params` lookup plus a `codecs.lookup` in
`_canonicalizes_to_utf8`. That is per-request work by `BUILD.md` `## Hot-path budget`'s
definition, so **Worker 3 records a post-hoc number** in its review section under a
`### Hot-path budget` heading:

- **Metric:** median wall-clock per request, `Client().post` against the sync mount with a small
  JSON body, >= 200 iterations, measured twice — once with `_ORDERED_CHAIN` installed and once
  with the CSRF-only chain — so the middleware's own cost is the difference.
- **Plus one micro-number** for the charset guard: `timeit` over >= 100,000 calls of
  `_canonicalizes_to_utf8("utf-8")`, since `codecs.lookup` is the only new call on the common
  path.
- State the command or snippet, the iteration count, the statistic, before, after, delta. A
  single-shot reading is not a number.

Whether the cost is acceptable is the maintainer's call and no worker's; the obligation is only
that it exists and reaches them. **M5** (the round-2 WS-revocation lock number) stays exactly as
the plan's `## Open maintainer decisions` leaves it — untouched, not re-argued, and unrelated to
this measurement.

If a fixing pass touches a per-request or per-outbound-frame path, that pass inherits this
declaration and owes its own before/after number for the change it makes.

### Floor verification scope

**R1 owns one floor run, and the owner is Worker 3's review pass** — the natural owner, since
there may be no builder pass at all. If a fixing pass lands, it re-runs the same scope and records
its own result; the final gate is the backstop that confirms the run happened, never a second
owner.

Scope: `tests/test_views.py` and `tests/test_routers.py` — the remediation changes
request-lifecycle and ASGI-teardown plumbing, a Django/Channels integration seam. No `--cov*`
flags. Build the venv **outside** the repo and never mutate the shared `.venv`
(`BUILD.md` `## Floor verification`, the single canonical statement of the floor: Django
**5.2.0** on Python **3.10** with strawberry-graphql **0.316.0**):

```shell
uv venv /tmp/dsf-floor --python 3.10
uv pip install --python /tmp/dsf-floor/bin/python -e . --group dev
uv pip install --python /tmp/dsf-floor/bin/python 'django==5.2.0' 'strawberry-graphql==0.316.0'
uv pip list --python /tmp/dsf-floor/bin/python
/tmp/dsf-floor/bin/python -m pytest tests/test_views.py tests/test_routers.py --no-cov
```

Record the resolved versions and each command's pass/fail. Five floor questions this diff makes
specific — the run is not just a green sweep:

1. **`SpooledTemporaryFile`'s reported positions at Python 3.10**, against
   `_measured_remaining`'s new claim that production streams report exact `int`s "on both
   supported interpreters":
   `/tmp/dsf-floor/bin/python -c "import tempfile, io; f = tempfile.SpooledTemporaryFile(max_size=10); f.write(b'abc'); print(repr(f.seek(0, io.SEEK_END)), repr(f.tell()), hasattr(f, 'seekable'))"`.
   If `seek` answers `None` there, the claim is false at the floor even though the *behaviour*
   stays fail-safe (`UNMEASURABLE` -> bounded read), and a load-bearing wrong comment is a
   finding.
2. **`LimitedStream.tell()` / `seek()` return types at Django 5.2.0** — the WSGI half of the same
   claim.
3. **`CsrfViewMiddleware.process_view` at Django 5.2.0** still reads the exemption as
   `getattr(callback, "csrf_exempt", False)` (truthiness, which is what makes a lazily-evaluated
   object work at all) and still short-circuits on `request.csrf_processing_done` (which is what
   makes "exactly one complete check" true in the installed arrangement).
4. **asgiref at the floor propagates the ContextVar into the `sync_to_async`-adapted
   `process_view`** and back — the async chain rows depend on it, and the floor's asgiref is older
   than the one the 324-row baseline ran under.
5. **Cancellation semantics on Python 3.10** for `settle`'s cancel-and-await-and-re-raise arm.
   3.11 changed task-cancellation bookkeeping (`Task.uncancel` / `cancelling` do not exist at the
   floor), and this arm is precisely a shielded await plus a re-raise, so confirm it by execution
   rather than by reasoning from current.

### Implementation discretion items

Choices assessed and left to Worker 3:

- **Proof breadth beyond the ten entries.** The ten are the round's mandatory population; whether
  to add an eleventh (for example a second mutation shape on `_require_boundary_before_csrf`) is
  Worker 3's.
- **Temp test versus a reasoned read** for each of the three probes named in
  `### Test additions / updates`, where reading the source answers the question conclusively.
- **The iteration count and statistic** for the hot-path number, above the stated floor of 200
  requests / 100,000 micro-calls.
- **Whether to regenerate `scripts/review_inspect.py` output** or read the overviews Worker 1
  generated this pass under `docs/shadow/`.

Nothing architectural is delegated here. The four contract-level questions this pass surfaced are
routed to Worker 0 / the maintainer under `### Notes for Worker 1 (spec reconciliation)`, not left
for a reviewer to decide.

### Dispatched findings checklist

One box per `docs/feedback.md` finding, quoting the finding as the review states it, with the
symbol-qualified site Worker 0's verification pass recorded (plan V8). **All four stay `- [ ]` at
planning:** this round's build pass is `2701f41a` + `ba66ab49`, so no Worker 2 pass exists to tick
them, and **Worker 1 ticks each landed box at final verification** (`ARTIFACT.md`, "tick any
landed box Worker 2 left open"). A tick means *the finding's contract is landed **and** audited* —
so a box whose boundary Worker 3 grades weakly pinned, or whose property Worker 3 cannot confirm,
stays open until the fixing pass closes it.

- [x] "**[P1] A contradictory JSON charset declaration restores the parser differential.**" "The
      root fix is to make the ordinary JSON content type part of the wire boundary before the body
      is parsed: an absent declaration or a name that canonicalizes to UTF-8 may pass; an unknown
      codec, `utf-8-sig`, or a non-UTF-8 declaration must receive the same controlled `400` as
      every other encoding refusal. Add sync and async raw-envelope regressions with a non-ASCII
      UTF-8 document, using a driver that does not helpfully re-encode the body from its declared
      charset. Pin UTF-8 aliases as successes and contradictory, unknown, and `utf-8-sig`
      declarations as refusals." — landed at
      `django_strawberry_framework/views.py::_RequestBodyBoundaryMixin._enforce_body_charset_declaration`,
      composed in `::_enforce_request_boundary`.
- [x] "**[P1] The CSRF reorder bypasses the project's configured CSRF middleware class.**" "The
      root fix needs an ordering mechanism in the actual middleware chain. Put a narrowly scoped
      package body-boundary middleware before the configured CSRF middleware (keyed by a marker on
      package views), then remove the outer exemption and stock-class re-entry. A view-local
      decorator cannot reproduce an arbitrary installed middleware subclass. Add a regression with
      a custom `CsrfViewMiddleware` subclass in `MIDDLEWARE`: an over-limit multipart body must
      still be refused before parsing, while an under-limit request must reach and obey the
      subclass's additional rejection on both view variants." — landed at
      `django_strawberry_framework/middleware/request_body.py::GraphQLRequestBodyBoundaryMiddleware`
      with `::_CsrfOrderingExemption`, `::_require_boundary_before_csrf`, and
      `views.py::_RequestBodyBoundaryMixin.as_view` / `::_enforce_request_boundary_once`. **Note
      the deliberate deviation from the prescription:** the exemption and the stock-class re-entry
      were **withdrawn conditionally, not removed** — a deployment that has not changed its
      `MIDDLEWARE` keeps the old arrangement. Worker 3 audits that as a contract choice, since a
      prescribed fix is a hypothesis and not an instruction.
- [x] "**[P2] A foreign position object's arithmetic still escapes the fail-closed body gate.**"
      "The root fix is to stop executing arbitrary numeric protocols from this foreign object.
      Production Django streams report exact built-in integer positions, so accept that measured
      shape explicitly; after a verified restore, any other position/end type or unusable result
      should be `_Probe.UNMEASURABLE` and take the bounded-read path. … Regressions should cover
      exceptions from both `__sub__` and the ordering comparison, not only the current `None - int`
      `TypeError` case." — landed at
      `django_strawberry_framework/_request_body.py::_measured_remaining`
      `#"if type(end) is not int or type(position) is not int"`.
- [x] "**[P2] Cancellation of disconnect lets the connection-owned close task outlive the
      connection.**" "The root fix is to make final teardown the terminal owner, not another
      shielded waiter. `disconnect` must enter settlement through `finally`, and cancellation
      while settling must cancel and await the owned attempt (or use an equivalent
      structured-concurrency owner with a bounded final wait). … Add regressions that cancel
      `disconnect` with a parked close and that make `super().disconnect` fail, then assert the
      close task is done, no task retains the consumer, and no second close is attempted." —
      landed at `django_strawberry_framework/consumers.py::_ConnectionRevocation.settle`,
      `::_ConnectionRevocation._attempt_close`, and
      `::build_revalidating_consumer_class`'s generated `disconnect`.

### Notes for Worker 1 (spec reconciliation)

**Nothing here is fixed in R1.** This pass may write only this artifact; the spec and the rationale
are **R2**'s and the standing docs are **R3**'s. Recorded so neither round has to re-derive it.

**For R2 (spec + rationale reconciliation):**

1. **Decision 18's own heading is now false.** It reads "The body gate runs before Django's
   multipart parser, **via view-local CSRF re-entry**", which at `HEAD` describes the *fallback*
   arrangement only. Measured cost of renaming it: the slugged anchor
   `#decision-18--the-body-gate-runs-before-djangos-multipart-parser-via-view-local-csrf-re-entry`
   occurs **15 times in the spec** and **1 time in the rationale** (`grep -c -F`), so the rename is
   a 16-site sweep — plus `csrf_exempt` itself occurs **13 times in the spec** and **0 times in the
   rationale**, all describing the pre-`2701f41a` shape (plan V2). A half-reconciled Decision 18 is
   worse than an un-updated one.
2. **Decision 9 has no declaration half.** The shipped refusal
   (`views.py::_enforce_body_charset_declaration`) is a wire boundary no spec sentence states
   (plan V3). It needs to read as the current contract with no chronology: absent passes, aliases
   pass, `utf-8-sig` / unknown / non-UTF-8 are refused with the shared `400`, multipart is the
   other guard's, GET is out of scope. The `HEAD`-vs-`GET` method-scope question in P1a is a
   contract question the spec should answer explicitly rather than leave to the code.
3. **V4 stands as Worker 0 recorded it** — the `CLOSING` ruling the class docstring has already
   retracted, plus the `ABANDONED` definition, the test-plan line, and the DoD line naming
   `asyncio.shield`. Add: the DoD/test-plan sentences should also state that `disconnect` enters
   settlement through `finally` and that a cancelled attempt is terminal.
4. **A new public name exists that no spec sentence mentions** — `GraphQLRequestBodyBoundaryMiddleware`
   (plan V1). Decision 18 (or a new decision) owns the deployment contract: install it immediately
   before the project's CSRF entry; a chain listing it after one is refused at startup; a
   deployment without it keeps the old arrangement unchanged. The **rejected alternative** worth
   recording beside it, from the review itself: "remove the outer exemption and stock-class
   re-entry" outright — rejected because that would change behaviour for every deployment that has
   not edited `MIDDLEWARE`.

**For R3 (documentation), routed via Worker 0 where it is a decision:**

5. **The example project does not install the new middleware.** Measured:
   `examples/fakeshop/config/settings.py`'s `MIDDLEWARE` lists
   `django_strawberry_framework.middleware.debug_toolbar.DebugToolbarMiddleware` and
   `django.middleware.csrf.CsrfViewMiddleware`, and **no** boundary middleware — so the new
   consumer-facing module is exercised only from package `tests/`, and the live tier
   (`examples/fakeshop/test_query/test_transport_api.py`) still runs the fallback arrangement.
   `AGENTS.md` #10 wants any line reachable from a real fakeshop query covered live, and the
   standing maintainer preference is to retire a package-only stand-in once the live tier can reach
   it — but installing it in fakeshop changes the example's whole chain and every live CSRF row.
   **Contract-level: the maintainer's call, not a worker's.** Both paths, with what each costs:
   (a) install it in fakeshop and re-pin the live transport rows, which makes the recommended
   deployment the one the example demonstrates; (b) leave fakeshop on the fallback arrangement and
   state in `docs/README.md` that both arrangements are supported, keeping package-tier coverage as
   the middleware's only home. R3's `docs/README.md` work (plan V2, V3) depends on the answer.
6. **`middleware/__init__.py` is correct as it stands** — its "deliberately NO re-export here"
   docstring and the new module's single-name `__all__` are consistent, and
   `django_strawberry_framework/__init__.py` is untouched. Recorded so R3 does not "fix" a
   non-problem.
7. **`_measured_remaining`'s docstring claim about both supported interpreters** (floor question 1)
   is a **code-comment** correction if the floor read falsifies it, owned by whichever pass runs
   the floor — not a spec edit, and not R2's.

---

## Build report (Worker 2)

**What this pass is.** The remediation under audit landed as the maintainer's `2701f41a` +
`ba66ab49`, so this pass wrote no production code and fixed no defect. Its whole subject is the
obligation `BUILD.md` `## Failability proofs: prove the test can fail` puts on a build pass and
that nobody had discharged: **ten landed boundaries with zero proofs on record**, reassigned to
Worker 2 by the build plan's `## Worker-0 dispatch decision D-1`. All ten are now proved, and the
two boundaries that came in weakly pinned were closed with three new test rows rather than routed
as exceptions.

### Files touched

Grounded in `git status --short` run after both ruff invocations, not from memory:

- `tests/test_routers.py` — one new row, `::test_a_teardown_cancelled_before_it_returns_still_settles_the_close`, plus nothing else. It closes the weakly-pinned verdict on the generated `disconnect`'s `try`/`finally` (proof entry 11).
- `tests/test_views.py` — one new helper class `::_DerivedBoundaryMiddleware` with its `_DERIVED_BOUNDARY_MIDDLEWARE_PATH` constant, and two new rows, `::test_a_boundary_subclass_listed_after_csrf_is_refused_at_startup` and `::test_the_first_csrf_entry_is_the_one_the_ordering_is_measured_against`. They close the weakly-pinned verdict on `middleware/request_body.py::_require_boundary_before_csrf` (proof entry 6).
- `docs/builder/bld-046-r1-remediation_review.md` — this section, and the `Status:` transition to `built`.
- `docs/builder/temp-tests/r1/proofs.json`, `…/proofs.md`, `…/run.log` — the proof manifest, the emitted record, and the run log. Gitignored scratch (`BUILD.md`: `docs/builder/temp-tests/` is an untracked scratch path), so they do not appear in `git status`.

**No production file was changed.** Every mutation this pass made was transient and reverted
inside the same entry, and the four production files are byte-identical to `HEAD` at the end of the
pass — proved read-only, without `git checkout`/`restore`/`stash`, by `git show HEAD:<path>` into a
scratch path outside the repository followed by `cmp`:

```shell
git show "HEAD:$f" > "$SCRATCH/$n"; cmp "$f" "$SCRATCH/$n"
```

`IDENTICAL-TO-HEAD` for all four of `django_strawberry_framework/views.py`,
`django_strawberry_framework/consumers.py`,
`django_strawberry_framework/middleware/request_body.py`,
`django_strawberry_framework/_request_body.py`. The scratch root also holds **no**
`ACTIVE-MUTATION.json` and no `RESTORE-FAILED.json` marker, so no mutation survived any entry.

### Tests added or updated

- `tests/test_routers.py::test_a_teardown_cancelled_before_it_returns_still_settles_the_close` — pins the half of the `finally` contract nothing pinned: a cancellation landing **inside** upstream's teardown (an ASGI shutdown arriving while the message-loop task is torn down) still reaches settlement. Upstream's `disconnect` is patched to park and to re-raise the `CancelledError` it receives, so the row's input is the cancellation itself rather than a teardown that returned first; the ordering is the measurement (`assert not disconnecting.done()` while the transport still holds the `4403` parked), and after release the attempt is `CLOSED`, uncancelled, with the caller's `CancelledError` propagating unchanged.
- `tests/test_views.py::test_a_boundary_subclass_listed_after_csrf_is_refused_at_startup` — pins the audit's documented "compared by class rather than by dotted path" contract on the boundary side (the CSRF side was already covered, since `_CSRF_MIDDLEWARE_PATH` is a `CsrfViewMiddleware` subclass). Both directions asserted, so a blanket refusal cannot satisfy it.
- `tests/test_views.py::test_the_first_csrf_entry_is_the_one_the_ordering_is_measured_against` — pins the `elif … and csrf_index is None` guard: a chain carrying two CSRF entries is judged against the **first**, because that is the entry whose `request.POST` read parses the body. This is the first half of the plan's P1b open question 4; the duplicated-*boundary* case is deliberately left unpinned (see `### Notes for Worker 3`).

Placement per `AGENTS.md`: both files are package tests of `django_strawberry_framework` itself, and
each new row exercises a seam no live fakeshop query can reach — a misordered `MIDDLEWARE` chain and
a cancelled ASGI teardown are not request-shaped inputs.

### Validation run

- `uv run ruff format tests/test_views.py tests/test_routers.py` — pass (`2 files left unchanged`; scoped to this pass's files, never `.`).
- `uv run ruff check --fix tests/test_views.py tests/test_routers.py` — pass (`All checks passed!`, no fixes applied).
- `uv run python scripts/check_trailing_commas.py --check tests/test_views.py tests/test_routers.py` — pass (exit 0). Run because the build gate's ruff step does not cover the source-layout hook that gates commits.
- `git status --short` after both ruff invocations — exactly four entries: `M tests/test_routers.py`, `M tests/test_views.py`, `M docs/builder/build-046-transport_security-0_0_15.md` (Worker 0's uncommitted closeout section, the baseline-dirty path the round preamble already records; not this pass's and not reverted, per `AGENTS.md` #34), and `?? docs/builder/bld-046-r1-remediation_review.md` (this artifact). Nothing unexpected.
- Focused runs, all without any `--cov*` flag: `uv run pytest --no-cov -q -rfE tests/test_routers.py::test_a_teardown_cancelled_before_it_returns_still_settles_the_close` — 1 passed; `uv run pytest --no-cov -q -rfE tests/test_views.py::test_a_boundary_subclass_listed_after_csrf_is_refused_at_startup tests/test_views.py::test_the_first_csrf_entry_is_the_one_the_ordering_is_measured_against tests/test_views.py::test_a_chain_that_lists_the_boundary_after_csrf_is_refused_at_startup` — 3 passed. The whole-scope state of both files is recorded per entry in the proof block below (`182 passed` for `tests/test_views.py`, `145 passed` for `tests/test_routers.py`, i.e. the round preamble's 324 plus this pass's 3 rows).
- No test-staleness sweep is owed by this pass: it changes no model field set and no wire shape (`BUILD.md` `### Test staleness a focused run cannot see`). The `csrf_exempt` staleness read the plan assigns stays R1's review pass's.

### Failability proofs

All eleven manifest entries (the plan's ten boundaries, with 4a/4b as two entries against the same
anchor) were performed with the mechanized runner, one mutation live at a time:

```shell
uv run python scripts/prove_failability.py docs/builder/temp-tests/r1/proofs.json \
    --scratch-root <session scratchpad>/dsf-r1-proofs \
    --output docs/builder/temp-tests/r1/proofs.md
```

Final run **exit 0**: every entry proved, no boundary weakly pinned, no collection or setup error,
every restore proved by byte comparison. The manifest is at
`docs/builder/temp-tests/r1/proofs.json` and the run log at `docs/builder/temp-tests/r1/run.log`.
Anchor verification was run first and separately as well (`--check-anchors-only`, exit 0: all
eleven matched exactly once **before** any copy was taken), re-derived this pass rather than taken
on the plan's recorded `grep -c -F`.

**why 0: not applicable to any entry — no entry measured zero rows.** The lowest count in the final
record is 2. So neither the weakly-pinned reading nor the harness-impossible reading
(`BUILD.md` `### Harness-impossible interleavings`) is invoked anywhere below, and this pass records
no harness limitation.

**Two entries were weakly pinned on the first run and were closed with rows, not with an
exception** (`BUILD.md` `### Acceptance rule`; the first-run record is superseded by the block below
and is preserved in `run.log`):

- **Entry 6** (`middleware/request_body.py::_require_boundary_before_csrf`) measured **1 row** — `tests/test_views.py::test_a_chain_that_lists_the_boundary_after_csrf_is_refused_at_startup`, exactly as the plan predicted. Closed at **3 rows** by the two new startup rows above. See `### Notes for Worker 1` item 1 for why this was not routed to the plan's M4 decision.
- **Entry 11** (`consumers.py::build_revalidating_consumer_class`'s `disconnect`) measured **1 row** — `::test_a_teardown_that_raises_still_settles_the_close_and_propagates` — where the plan predicted >= 2. Closed at **2 rows** by the new cancelled-teardown row. The gap was real and specific: of the two inputs the `finally` exists for, only the *raising* one was pinned, and the *cancelled* one — which is the one the finding named — was not (see `### Notes for Worker 3` item 1).

Procedure, mechanized by `scripts/prove_failability.py`: the target is copied to a scratch path OUTSIDE the repo before any mutation; the mutation site is located by an exact anchor asserted to match exactly once (any other count aborts the entry without writing); the same focused scope is run unmutated first, so rows already failing before the mutation are differenced out of the count; both runs' pytest exit codes are read, because a run that collected nothing or blew up emits no `FAILED` lines and would otherwise be recorded as a measured zero; both runs use `--no-cov`; the file is restored from the pre-mutation copy in a `finally` and the restore is proved by `filecmp.cmp(shallow=False)` plus a SHA-256 comparison. One boundary at a time, restored before the next. `git` is never invoked - the tree is legitimately dirty, so an empty `git diff` is unachievable and forcing one would destroy the build's own work.

| # | Boundary | File mutated | Mutation applied | Rows failed | Errors | Scope as run | Restore proof |
|---|---|---|---|---|---|---|---|
| 1 | `django_strawberry_framework/views.py::_RequestBodyBoundaryMixin._enforce_body_charset_declaration` | `django_strawberry_framework/views.py` | deleted: `if declared is not None and not _canonicalizes_to_utf8(declared): raise HTTPException(400, _JSON_PARSE_REASON)` - builder's description (unverified prose): the charset refusal itself deleted: a declared non-UTF-8 charset is read and then ignored | **7** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_views.py` | filecmp.cmp(shallow=False) True; sha256 eaaa9a15f33d8622... == eaaa9a15f33d8622... (vs pre-mutation copy) |
| 2 | `django_strawberry_framework/views.py::_RequestBodyBoundaryMixin._enforce_body_charset_declaration #"if request.method == \"GET\" or _is_multipart_form_post(request)"` | `django_strawberry_framework/views.py` | deleted: `if request.method == "GET" or _is_multipart_form_post(request): return` - builder's description (unverified prose): the GET / multipart carve-out deleted, so the guard claims every request shape including the ones the multipart encoding guard owns | **2** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_views.py` | filecmp.cmp(shallow=False) True; sha256 eaaa9a15f33d8622... == eaaa9a15f33d8622... (vs pre-mutation copy) |
| 3 | `django_strawberry_framework/middleware/request_body.py::GraphQLRequestBodyBoundaryMiddleware.process_view` | `django_strawberry_framework/middleware/request_body.py` | `if not getattr(view_func, _BOUNDARY_MARKER, False):` -> `if True:` - builder's description (unverified prose): the marker test inverted into an unconditional pass-through: the chain never runs the boundary and never stamps the request | **4** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_views.py` | filecmp.cmp(shallow=False) True; sha256 991e574a02d6cba1... == 991e574a02d6cba1... (vs pre-mutation copy) |
| 4 | `django_strawberry_framework/middleware/request_body.py::_CsrfOrderingExemption.__bool__` | `django_strawberry_framework/middleware/request_body.py` | `return not _boundary_middleware_active.get()` -> `return True` - builder's description (unverified prose): the withdrawal removed: the exemption is always truthy, so the configured CSRF middleware always skips the callback | **3** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_views.py` | filecmp.cmp(shallow=False) True; sha256 991e574a02d6cba1... == 991e574a02d6cba1... (vs pre-mutation copy) |
| 5 | `django_strawberry_framework/middleware/request_body.py::_CsrfOrderingExemption.__bool__ (opposite direction)` | `django_strawberry_framework/middleware/request_body.py` | `return not _boundary_middleware_active.get()` -> `return False` - builder's description (unverified prose): the exemption is always withdrawn, so the view-local arrangement loses its ordering on a chain that does not supply one | **5** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_views.py` | filecmp.cmp(shallow=False) True; sha256 991e574a02d6cba1... == 991e574a02d6cba1... (vs pre-mutation copy) |
| 6 | `django_strawberry_framework/middleware/request_body.py::_require_boundary_before_csrf` | `django_strawberry_framework/middleware/request_body.py` | `boundary_index = csrf_index = None` -> `return boundary_index = csrf_index = None` - builder's description (unverified prose): the ordering audit short-circuited before it reads MIDDLEWARE, so a misordered chain is accepted at startup | **3** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_views.py` | filecmp.cmp(shallow=False) True; sha256 991e574a02d6cba1... == 991e574a02d6cba1... (vs pre-mutation copy) |
| 7 | `django_strawberry_framework/views.py::_RequestBodyBoundaryMixin._enforce_request_boundary_once` | `django_strawberry_framework/views.py` | `if getattr(request, _BOUNDARY_ENFORCED, False): return self._enforce_request_boundary(request)` -> `return` - builder's description (unverified prose): the view's own enforcement removed entirely: the body boundary runs zero times on any chain that does not carry the middleware | **8** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_views.py` | filecmp.cmp(shallow=False) True; sha256 eaaa9a15f33d8622... == eaaa9a15f33d8622... (vs pre-mutation copy) |
| 8 | `django_strawberry_framework/_request_body.py::_measured_remaining` | `django_strawberry_framework/_request_body.py` | deleted: `if type(end) is not int or type(position) is not int: return _Probe.UNMEASURABLE` - builder's description (unverified prose): the exact-int gate deleted, so a foreign position/end object's own numeric protocol executes inside the gate | **6** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_views.py` | filecmp.cmp(shallow=False) True; sha256 5b8a9d4752004db5... == 5b8a9d4752004db5... (vs pre-mutation copy) |
| 9 | `django_strawberry_framework/consumers.py::_ConnectionRevocation.settle` | `django_strawberry_framework/consumers.py` | `try: await asyncio.shield(self.attempt) except asyncio.CancelledError: self.attempt.cancel() # Suppressed, not swallo...` -> `await asyncio.shield(self.attempt)` - builder's description (unverified prose): the cancel-and-await-and-re-raise arm removed, leaving the bare shielded await this fix replaced: a cancelled settlement leaves the attempt running | **2** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_routers.py` | filecmp.cmp(shallow=False) True; sha256 1bdf298c473fd1a0... == 1bdf298c473fd1a0... (vs pre-mutation copy) |
| 10 | `django_strawberry_framework/consumers.py::_ConnectionRevocation._attempt_close` | `django_strawberry_framework/consumers.py` | deleted: `except asyncio.CancelledError: self.state = _REVOCATION_ABANDONED raise` - builder's description (unverified prose): the terminal-record arm deleted, so a cancelled attempt rests in CLOSING instead of ABANDONED | **2** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_routers.py` | filecmp.cmp(shallow=False) True; sha256 1bdf298c473fd1a0... == 1bdf298c473fd1a0... (vs pre-mutation copy) |
| 11 | `django_strawberry_framework/consumers.py::build_revalidating_consumer_class #"await super().disconnect(code)"` | `django_strawberry_framework/consumers.py` | `try: await super().disconnect(code) finally: await self._revocation.settle()` -> `await super().disconnect(code) await self._revocation.settle()` - builder's description (unverified prose): the try/finally flattened back to two sequential awaits, so a cancelled or raising upstream teardown skips settlement | **2** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_routers.py` | filecmp.cmp(shallow=False) True; sha256 1bdf298c473fd1a0... == 1bdf298c473fd1a0... (vs pre-mutation copy) |

Verdicts:

1. `django_strawberry_framework/views.py::_RequestBodyBoundaryMixin._enforce_body_charset_declaration` - pinned
2. `django_strawberry_framework/views.py::_RequestBodyBoundaryMixin._enforce_body_charset_declaration #"if request.method == \"GET\" or _is_multipart_form_post(request)"` - inside Worker 3's mandatory re-run floor (<= 3 rows)
3. `django_strawberry_framework/middleware/request_body.py::GraphQLRequestBodyBoundaryMiddleware.process_view` - pinned
4. `django_strawberry_framework/middleware/request_body.py::_CsrfOrderingExemption.__bool__` - inside Worker 3's mandatory re-run floor (<= 3 rows)
5. `django_strawberry_framework/middleware/request_body.py::_CsrfOrderingExemption.__bool__ (opposite direction)` - pinned
6. `django_strawberry_framework/middleware/request_body.py::_require_boundary_before_csrf` - inside Worker 3's mandatory re-run floor (<= 3 rows)
7. `django_strawberry_framework/views.py::_RequestBodyBoundaryMixin._enforce_request_boundary_once` - pinned
8. `django_strawberry_framework/_request_body.py::_measured_remaining` - pinned
9. `django_strawberry_framework/consumers.py::_ConnectionRevocation.settle` - inside Worker 3's mandatory re-run floor (<= 3 rows)
10. `django_strawberry_framework/consumers.py::_ConnectionRevocation._attempt_close` - inside Worker 3's mandatory re-run floor (<= 3 rows)
11. `django_strawberry_framework/consumers.py::build_revalidating_consumer_class #"await super().disconnect(code)"` - inside Worker 3's mandatory re-run floor (<= 3 rows)

Failing node ids, per boundary (the count above is `len()` of this list):

1. `django_strawberry_framework/views.py::_RequestBodyBoundaryMixin._enforce_body_charset_declaration`
   - file mutated: `django_strawberry_framework/views.py`
   - pytest summary: `======================== 7 failed, 175 passed in 1.66s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 182 passed in 1.67s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_views.py::test_a_non_multipart_request_is_not_subject_to_the_form_encoding_check`
   - `tests/test_views.py::test_the_endpoint_refuses_a_json_charset_it_will_not_decode_with[sync-latin-1]`
   - `tests/test_views.py::test_the_endpoint_refuses_a_json_charset_it_will_not_decode_with[sync-utf-8-sig]`
   - `tests/test_views.py::test_the_endpoint_refuses_a_json_charset_it_will_not_decode_with[sync-unknown-name]`
   - `tests/test_views.py::test_the_endpoint_refuses_a_json_charset_it_will_not_decode_with[async-latin-1]`
   - `tests/test_views.py::test_the_endpoint_refuses_a_json_charset_it_will_not_decode_with[async-utf-8-sig]`
   - `tests/test_views.py::test_the_endpoint_refuses_a_json_charset_it_will_not_decode_with[async-unknown-name]`
2. `django_strawberry_framework/views.py::_RequestBodyBoundaryMixin._enforce_body_charset_declaration #"if request.method == \"GET\" or _is_multipart_form_post(request)"`
   - file mutated: `django_strawberry_framework/views.py`
   - pytest summary: `======================== 2 failed, 180 passed in 1.75s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 182 passed in 1.57s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_views.py::test_a_get_carrying_a_stray_multipart_content_type_is_not_a_multipart_form`
   - `tests/test_views.py::test_a_multipart_declaration_is_left_to_the_form_encoding_guard`
3. `django_strawberry_framework/middleware/request_body.py::GraphQLRequestBodyBoundaryMiddleware.process_view`
   - file mutated: `django_strawberry_framework/middleware/request_body.py`
   - pytest summary: `======================== 4 failed, 178 passed in 1.57s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 182 passed in 1.60s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_views.py::test_the_chain_refuses_an_over_limit_multipart_before_any_csrf_read[sync]`
   - `tests/test_views.py::test_the_chain_refuses_an_over_limit_multipart_before_any_csrf_read[async]`
   - `tests/test_views.py::test_the_view_does_not_measure_a_body_the_chain_already_measured[sync]`
   - `tests/test_views.py::test_the_view_does_not_measure_a_body_the_chain_already_measured[async]`
4. `django_strawberry_framework/middleware/request_body.py::_CsrfOrderingExemption.__bool__`
   - file mutated: `django_strawberry_framework/middleware/request_body.py`
   - pytest summary: `======================== 3 failed, 179 passed in 1.57s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 182 passed in 1.59s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_views.py::test_the_projects_own_csrf_middleware_runs_when_the_chain_supplies_the_ordering[sync]`
   - `tests/test_views.py::test_the_projects_own_csrf_middleware_runs_when_the_chain_supplies_the_ordering[async]`
   - `tests/test_views.py::test_the_async_chain_resets_the_ordering_mark_around_the_downstream_call`
5. `django_strawberry_framework/middleware/request_body.py::_CsrfOrderingExemption.__bool__ (opposite direction)`
   - file mutated: `django_strawberry_framework/middleware/request_body.py`
   - pytest summary: `======================== 5 failed, 177 passed in 1.58s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 182 passed in 1.60s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_views.py::test_the_view_callback_of_both_views_carries_the_csrf_exempt_mark[sync]`
   - `tests/test_views.py::test_the_view_callback_of_both_views_carries_the_csrf_exempt_mark[async]`
   - `tests/test_views.py::test_without_the_middleware_the_view_keeps_its_own_ordering_and_exemption[sync]`
   - `tests/test_views.py::test_without_the_middleware_the_view_keeps_its_own_ordering_and_exemption[async]`
   - `tests/test_views.py::test_the_async_chain_resets_the_ordering_mark_around_the_downstream_call`
6. `django_strawberry_framework/middleware/request_body.py::_require_boundary_before_csrf`
   - file mutated: `django_strawberry_framework/middleware/request_body.py`
   - pytest summary: `======================== 3 failed, 179 passed in 1.63s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 182 passed in 1.60s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_views.py::test_a_chain_that_lists_the_boundary_after_csrf_is_refused_at_startup`
   - `tests/test_views.py::test_a_boundary_subclass_listed_after_csrf_is_refused_at_startup`
   - `tests/test_views.py::test_the_first_csrf_entry_is_the_one_the_ordering_is_measured_against`
7. `django_strawberry_framework/views.py::_RequestBodyBoundaryMixin._enforce_request_boundary_once`
   - file mutated: `django_strawberry_framework/views.py`
   - pytest summary: `======================== 8 failed, 174 passed in 1.59s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 182 passed in 1.59s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_views.py::test_the_endpoint_refuses_a_json_charset_it_will_not_decode_with[sync-latin-1]`
   - `tests/test_views.py::test_the_endpoint_refuses_a_json_charset_it_will_not_decode_with[sync-utf-8-sig]`
   - `tests/test_views.py::test_the_endpoint_refuses_a_json_charset_it_will_not_decode_with[sync-unknown-name]`
   - `tests/test_views.py::test_the_endpoint_refuses_a_json_charset_it_will_not_decode_with[async-latin-1]`
   - `tests/test_views.py::test_the_endpoint_refuses_a_json_charset_it_will_not_decode_with[async-utf-8-sig]`
   - `tests/test_views.py::test_the_endpoint_refuses_a_json_charset_it_will_not_decode_with[async-unknown-name]`
   - `tests/test_views.py::test_without_the_middleware_the_view_keeps_its_own_ordering_and_exemption[sync]`
   - `tests/test_views.py::test_without_the_middleware_the_view_keeps_its_own_ordering_and_exemption[async]`
8. `django_strawberry_framework/_request_body.py::_measured_remaining`
   - file mutated: `django_strawberry_framework/_request_body.py`
   - pytest summary: `======================== 6 failed, 176 passed in 1.61s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 182 passed in 1.60s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_views.py::test_a_probe_that_fails_without_moving_the_stream_falls_back_to_the_bounded_read[sync-unnumbered-end-position]`
   - `tests/test_views.py::test_a_probe_that_fails_without_moving_the_stream_falls_back_to_the_bounded_read[async-unnumbered-end-position]`
   - `tests/test_views.py::test_a_position_object_whose_numeric_protocol_raises_never_runs_inside_the_gate[sync-subtraction-raises]`
   - `tests/test_views.py::test_a_position_object_whose_numeric_protocol_raises_never_runs_inside_the_gate[sync-comparison-raises]`
   - `tests/test_views.py::test_a_position_object_whose_numeric_protocol_raises_never_runs_inside_the_gate[async-subtraction-raises]`
   - `tests/test_views.py::test_a_position_object_whose_numeric_protocol_raises_never_runs_inside_the_gate[async-comparison-raises]`
9. `django_strawberry_framework/consumers.py::_ConnectionRevocation.settle`
   - file mutated: `django_strawberry_framework/consumers.py`
   - pytest summary: `======================== 2 failed, 143 passed in 7.52s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 145 passed in 7.52s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_routers.py::test_cancelling_the_teardown_ends_the_close_attempt_instead_of_orphaning_it`
   - `tests/test_routers.py::test_a_cancelled_disconnect_leaves_no_task_retaining_the_connection`
10. `django_strawberry_framework/consumers.py::_ConnectionRevocation._attempt_close`
   - file mutated: `django_strawberry_framework/consumers.py`
   - pytest summary: `======================== 2 failed, 143 passed in 7.52s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 145 passed in 7.50s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_routers.py::test_cancelling_the_teardown_ends_the_close_attempt_instead_of_orphaning_it`
   - `tests/test_routers.py::test_a_cancelled_disconnect_leaves_no_task_retaining_the_connection`
11. `django_strawberry_framework/consumers.py::build_revalidating_consumer_class #"await super().disconnect(code)"`
   - file mutated: `django_strawberry_framework/consumers.py`
   - pytest summary: `======================== 2 failed, 143 passed in 7.52s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 145 passed in 7.55s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_routers.py::test_a_teardown_cancelled_before_it_returns_still_settles_the_close`
   - `tests/test_routers.py::test_a_teardown_that_raises_still_settles_the_close_and_propagates`

A boundary whose removal fails 0 or 1 rows is **weakly pinned** and is `revision-needed` per `docs/builder/BUILD.md` - the fix is more or better-targeted rows, never a weaker boundary. A boundary at 3 rows or fewer is inside Worker 3's mandatory independent re-run floor. A proof carrying collection or setup errors, or whose pytest run exited anything but 0 or 1 (nothing collected, interrupted, internal error, usage error), is not a valid count at all - and a 0 from such a run is not a zero-row result: resolve it and re-run.

Every `<fill in ...>` above is a judgement no tool can make and MUST be replaced by hand before this subsection is submitted: weakly pinned and harness-impossible are the two possible readings of a zero-row result and they prescribe opposite responses (more rows, versus a production-call-site invariant assertion plus a recorded harness limitation), so a record that does not name one reads as self-contradictory.

### Hot-path budget

`Not applicable; plan declares no hot path.` The plan states it directly: "**R1 as an audit: not
applicable** - it writes no production code", and this pass wrote none. The post-hoc number the
plan requires for the per-request cost the landed remediation added stays where the plan assigns
it, Worker 3's review section; nothing in this pass's diff touches a per-request or
per-outbound-frame path, so the plan's inheritance clause ("if a fixing pass touches a per-request
... path, that pass inherits this declaration") does not fire.

### Floor verification

Owned by Worker 3's review pass per the plan's declaration.

### Implementation notes

- **Three manifest anchors were widened from the plan's table so the mutated file stays valid Python.** The plan's anchors are correct sites; two of them, applied literally, produce a file that cannot be imported, which is a collection error rather than a measurement (and `BUILD.md` `### What gets recorded` rules an error-bearing run no valid count at all). Entry 7 (`views.py::_enforce_request_boundary_once`) takes the method's whole three-line body as the anchor and replaces it with `        return`, because replacing only the `if` line orphans its indented `return` into an `IndentationError`. Entry 9 (`consumers.py::_ConnectionRevocation.settle`) takes the whole `try`/`except` block and replaces it with `        await asyncio.shield(self.attempt)`, because deleting only the `except` arm leaves a `try` with no handler; that replacement is literally the "bare shielded await" the plan names as the mutation. Both still **remove** their boundary rather than perturb code near it. Entry 11 likewise takes the four-line `try`/`finally` block and replaces it with the two sequential awaits.
- **The scratch root is the session scratchpad, not `/tmp/dsf-r1-proofs`.** Both are outside the repository, which is the property the rule protects; the path itself is not load-bearing and the runner records the resolved root in `run.log`.
- **The new `tests/test_routers.py` row reuses the file's existing teardown fixtures rather than adding any** — `_ParkedCloseWebSocket`, `_revocation_with_a_parked_attempt`, `_consumer_with_a_controlled_teardown`, `_reached` — so it differs from its two siblings only in the teardown it supplies, which is where the contract difference is.
- **The row observes the cancellation through a positive signal, not a sleep.** Upstream's patched teardown sets a second `Event` from its own `except asyncio.CancelledError:` before re-raising, so `_reached(teardown_cancelled, …)` waits for the state the production code is about to produce (the file's established `_reached` discipline: a failure bound, never a timing assumption) rather than yielding a fixed number of times and hoping.
- **`_DerivedBoundaryMiddleware` is body-less on purpose.** The property under test is the audit's `issubclass` comparison, so a subclass that adds behaviour would let a reader wonder whether the behaviour mattered.

### Notes for Worker 3

1. **The `finally` in the generated `disconnect` was pinned on its secondary input only.** Before this pass, flattening the `try`/`finally` back to two sequential awaits failed exactly one row, the *raising* teardown. `::test_a_cancelled_disconnect_leaves_no_task_retaining_the_connection` does not distinguish the two shapes: its patched teardown returns immediately, so the cancellation it delivers lands while `settle()` is already awaiting, which the flattened form also survives. `docs/feedback.md`'s finding is about cancellation, so the input the fix exists for was the unpinned one. The new row supplies it. Worth an independent re-run at the recorded scope: it is one of the two entries whose first measurement disagreed with the plan's prediction.
2. **The plan's live fail-open suspect now has a measured consequence, though not a reachability answer.** Entry 3 mutates `process_view`'s marker test to `if True:`, which reproduces exactly the state P1b open question 1 describes — the exemption withdrawn chain-wide by `__call__` while the boundary does not run — and **4 rows** fail, including both `::test_the_chain_refuses_an_over_limit_multipart_before_any_csrf_read` rows. So if a callback can lose `_BOUNDARY_MARKER` while the middleware is installed, the suite says the outcome is a real ordering loss and not a benign pass-through. Which assertion inside those rows broke is not in the record (the runner runs `--tb=no` by design), and **whether marker loss is reachable is still open** — the temp test the plan proposes is unwritten, and reachability, not consequence, is what decides the finding.
3. **The duplicated-*boundary* case of P1b open question 4 is deliberately left unpinned.** A chain `[boundary, csrf, boundary]` is currently **refused**, because the audit keeps the *last* boundary index while keeping the *first* CSRF index. That may be the right strict answer or may be over-refusal — the first boundary entry does precede the CSRF read — and it is a contract question the plan routes to you, so pinning it in this pass would have frozen an unreviewed answer. The duplicated-*CSRF* case is unambiguous (the first entry parses the body) and is what the new row pins.
4. **Entry 9's mutation is not distinguished by the new row.** Removing `settle`'s cancel-and-await-and-re-raise arm fails `::test_cancelling_the_teardown_ends_the_close_attempt_instead_of_orphaning_it` and `::test_a_cancelled_disconnect_leaves_no_task_retaining_the_connection` and **not** the new row — correctly, since the new row's cancellation is answered by the `finally` reaching `settle()` at all, and its attempt is then released rather than cancelled. The two boundaries stay separately pinned, which is what `### Mutations are transient`'s one-boundary-one-mutation rule is for.
5. **`scripts/review_inspect.py` was not run or re-run by this pass**, and no shadow file was read. The plan leaves the regenerate-or-read choice to the review pass and Worker 1 already generated the new module's overview.

### Notes for Worker 1 (spec reconciliation)

1. **The plan's merit premise for proof entry 5/6 does not hold, so the M4 route was not taken — and no exception is recorded either way.** The plan predicts that entry at exactly 1 row and routes an exactly-1 result to the maintainer's still-open **M4** decision, on the reasoning that "a misordered chain raises at construction, so no behavioural row can exist beyond the startup one". The first half is right and the conclusion does not follow: no *behavioural* row can exist, but two further *startup* rows could, and both pin contracts the audit's own docstring states and nothing exercised — comparison by class on the boundary side, and the `csrf_index is None` guard that makes the first CSRF entry the one measured. They are now in `tests/test_views.py` and the boundary measures 3 rows. This is not a re-litigation of the weakly-pinned rule in either direction (`BUILD.md`'s "the fix is more rows, never a recorded exception" was simply available here); recorded so that M4's population is not read as including this entry.
2. **Nothing in `### Dispatched findings checklist` is ticked by this pass, deliberately.** No box's fix landed in this pass's diff — the four fixes are the maintainer's two commits — and the plan reserves the ticks for Worker 1's final verification, where a tick means "landed **and** audited". Both boundaries this pass strengthened belong to the second and fourth boxes, so neither is closable until Worker 3's audit runs.
3. **The spec still states no contract for either property the two new `tests/test_views.py` rows pin**, which matters for R2's Decision 18 rewrite: that the ordering audit compares middleware entries **by class**, so a subclass of either side is recognized; and that a chain with several CSRF entries is judged against the **first**. Both are load-bearing deployment contracts a consumer can violate by editing `MIDDLEWARE`, and R2's item 4 (the new middleware's deployment contract) is where they belong. Recommended wording to add to that decision, after the "a chain listing it after one is refused at startup" sentence: "Entries are compared by resolved class, so a subclass of either the boundary middleware or `CsrfViewMiddleware` is recognized as what it is; a chain listing more than one CSRF entry must place the boundary before the **first** of them, since that is the entry whose `request.POST` read parses the body."
4. **No spec gap or conflict was surfaced by the proofs themselves.** Every boundary the plan named exists at the site the plan named, with the anchor matching exactly once, so the plan's symbol-qualified citations are all current at `HEAD`.

---

## Review (Worker 3)

### Independent re-run: the mutations, declared before they were made

`worker-3.md` "Reading is necessary, not sufficient" requires this declaration to precede the
mutation. **Re-run set: all eleven entries**, not the arithmetic floor's six. The floor by row count
alone would be entries 2, 4, 6, 9, 10, 11 (<= 3 rows); the floor's second clause — "every boundary on
a **security or data-isolation** decision" — takes in the other five as well, because every boundary
on this diff is one (a body cap, two encoding refusals, a CSRF-ordering guarantee, a close-ownership
invariant). Nothing here is accepted on Worker 2's record alone.

Each mutation is exactly the one `docs/builder/temp-tests/r1/proofs.json` records, re-run at exactly
the scope Worker 2 recorded, with the runner performing the anchor-matches-once check **before** any
copy is taken:

```shell
uv run python scripts/prove_failability.py docs/builder/temp-tests/r1/proofs.json \
    --scratch-root <session scratchpad>/dsf-w3-rerun \
    --output docs/builder/temp-tests/r1/w3-rerun.md
```

The eleven mutations, as declared in the manifest and re-applied by this pass:

| # | Target | Mutation re-applied |
| --- | --- | --- |
| 1 | `views.py::_enforce_body_charset_declaration` | delete the `if declared is not None and not _canonicalizes_to_utf8(declared):` + `raise` pair |
| 2 | the same method's carve-out | delete the `if request.method == "GET" or _is_multipart_form_post(request):` + `return` pair |
| 3 | `middleware/request_body.py::…process_view` | `if not getattr(view_func, _BOUNDARY_MARKER, False):` -> `if True:` |
| 4 | `::_CsrfOrderingExemption.__bool__` | `return not _boundary_middleware_active.get()` -> `return True` |
| 5 | the same, opposite direction | -> `return False` |
| 6 | `::_require_boundary_before_csrf` | prepend `return` before `boundary_index = csrf_index = None` |
| 7 | `views.py::_enforce_request_boundary_once` | whole three-line body -> `return` |
| 8 | `_request_body.py::_measured_remaining` | delete the `type(end) is not int or type(position) is not int` gate |
| 9 | `consumers.py::_ConnectionRevocation.settle` | whole `try`/`except` -> bare `await asyncio.shield(self.attempt)` |
| 10 | `consumers.py::_ConnectionRevocation._attempt_close` | delete the `except asyncio.CancelledError:` / `ABANDONED` / `raise` arm |
| 11 | `consumers.py::build_revalidating_consumer_class`'s `disconnect` | flatten `try`/`finally` to two sequential awaits |

Results are recorded under `### Failability proof audit` below, node-id set against node-id set.

### Baseline verified independently, not accepted on the build report

Worker 2 claims all four production files are byte-identical to `HEAD` at the end of its pass. Verified
read-only, no `git checkout` / `restore` / `stash` / `worktree`, into a scratch path **outside** the
repository:

```shell
git show "HEAD:$f" > "$SCRATCH/$n"; cmp "$f" "$SCRATCH/$n"
```

`IDENTICAL-TO-HEAD` for `django_strawberry_framework/views.py`, `…/consumers.py`,
`…/middleware/request_body.py`, `…/_request_body.py`. Worker 2's scratch root
(`…/dsf-r1-proofs/`) holds `pristine/` only — **no** `ACTIVE-MUTATION.json` and no
`RESTORE-FAILED.json` — so no mutation survived any entry. `git status --short` at the start of this
pass: `M docs/builder/build-046-transport_security-0_0_15.md` (Worker 0's uncommitted closeout
section, baseline-dirty, not reverted), `M tests/test_routers.py`, `M tests/test_views.py`,
`?? docs/builder/bld-046-r1-remediation_review.md`. Nothing unexpected.

The diff was read at the correct range (`git show 2701f41a`, `git show ba66ab49`) and every touched
symbol was read in full at `HEAD`, not only its `+` lines.

### Failability proof audit

**Every one of the eleven records was audited and every one was independently re-run.** No boundary
was accepted on Worker 2's record alone, for the reason stated above: the arithmetic floor (<= 3 rows)
selects entries 2, 4, 6, 9, 10, 11, and the floor's second clause — every boundary on a security or
data-isolation decision — takes in 1, 3, 5, 7, 8 as well.

Runner exit **0**. Anchors: all eleven matched exactly once **before** any copy was taken. Restores:
`filecmp.cmp(shallow=False) True` plus SHA-256 equality, **11/11**. Collection/setup errors: **0** on
all 22 runs (11 pre-mutation baselines + 11 mutants). Pre-mutation baselines all green
(`182 passed` for `tests/test_views.py`, `145 passed` for `tests/test_routers.py`), so no differencing
was needed. Restore re-proved after the whole run by the byte comparison above.

**Node-id set comparison, W2's record against W3's re-run, computed mechanically rather than eyeballed:**

| # | Boundary | W2 rows | W3 rows | Node-id sets |
| --- | --- | --- | --- | --- |
| 1 | `views.py::_enforce_body_charset_declaration` | 7 | 7 | **MATCH** |
| 2 | the same method's GET/multipart carve-out | 2 | 2 | **MATCH** |
| 3 | `middleware/request_body.py::…process_view` | 4 | 4 | **MATCH** |
| 4 | `::_CsrfOrderingExemption.__bool__` -> `True` | 3 | 3 | **MATCH** |
| 5 | `::_CsrfOrderingExemption.__bool__` -> `False` | 5 | 5 | **MATCH** |
| 6 | `::_require_boundary_before_csrf` | 3 | 3 | **MATCH** |
| 7 | `views.py::_enforce_request_boundary_once` | 8 | 8 | **MATCH** |
| 8 | `_request_body.py::_measured_remaining` | 6 | 6 | **MATCH** |
| 9 | `consumers.py::_ConnectionRevocation.settle` | 2 | 2 | **MATCH** |
| 10 | `consumers.py::_ConnectionRevocation._attempt_close` | 2 | 2 | **MATCH** |
| 11 | `consumers.py::build_revalidating_consumer_class`'s `disconnect` | 2 | 2 | **MATCH** |

All eleven sets are set-equal, not merely equal in size (the comparison was a symmetric difference over
the parsed node-id lists in `docs/builder/temp-tests/r1/proofs.md` versus
`docs/builder/temp-tests/r1/w3-rerun.md`, printing `only W2:` / `only W3:` on any difference; none
printed). Lowest count is 2, so **nothing is weakly pinned** and no zero-row **why 0** judgement is
owed anywhere. Full re-run record: `docs/builder/temp-tests/r1/w3-rerun.md`, log at `…/w3-rerun.log`.

**The three widened anchors judged, one at a time.** `BUILD.md` requires a mutation to *remove* the
boundary rather than perturb code near it, and Worker 2 re-expressed three of the plan's anchors to
whole syntactic blocks. All three widenings are accepted:

- **Entry 7** (`_enforce_request_boundary_once`): the plan's own stated mutation was already "replace
  the body with `return` (the view never enforces)", so taking the three-line body as the anchor is
  the plan's mutation, not a widening of it. The literal one-line anchor would orphan an indented
  `return` into an `IndentationError`, which is a collection error rather than a measurement. The
  result removes the view-side boundary entirely; its 8 rows include both
  `::test_without_the_middleware_the_view_keeps_its_own_ordering_and_exemption` halves, which is the
  "boundary cannot run zero times" witness.
- **Entry 9** (`settle`): replacing the whole `try`/`except` with `await asyncio.shield(self.attempt)`
  reproduces, character for character, the code `ba66ab49` replaced — the strongest possible form of
  "the boundary is gone", since the mutant *is* the defective predecessor. Deleting only the `except`
  arm would leave a `try` with no handler (a `SyntaxError`).
- **Entry 11** (`disconnect`): flattening the `try`/`finally` to two sequential awaits likewise
  reproduces the pre-`ba66ab49` code exactly.

None of the three merely perturbs adjacent code; each restores the defective predecessor or removes
the enforcing statement. The one thing entry 7's widening costs is that the *idempotence gate*
(`getattr(request, _BOUNDARY_ENFORCED, False)`) is not separately mutated — but its only fail-open
direction (always treating the request as already enforced) is exactly what entry 7 measures, and its
fail-closed direction (never believing the stamp) costs a second measurement rather than a missed one,
so no entry is missing.

### Floor verification (owned by this pass per the plan's declaration)

Built outside the repo with an explicit `--python`; the shared `.venv` was never touched.

```shell
uv venv /tmp/dsf-floor --python 3.10                                    # pass
uv pip install --python /tmp/dsf-floor/bin/python -e . --group dev      # pass
uv pip install --python /tmp/dsf-floor/bin/python 'django==5.2.0' 'strawberry-graphql==0.316.0'  # pass
uv pip list --python /tmp/dsf-floor/bin/python                          # pass (recorded below)
/tmp/dsf-floor/bin/python -m pytest tests/test_views.py tests/test_routers.py --no-cov  # PASS
```

Resolved versions, read from the environment rather than stated from memory: **Python 3.10.19**,
**django 5.2**, **strawberry-graphql 0.316.0**, asgiref 3.12.1, channels 4.3.2, pytest 9.1.1. Result:
**327 passed in 8.10s** — the round preamble's 324 plus Worker 2's 3 new rows, so the floor agrees with
the shared environment row for row. Re-run after this pass's docstring correction: **327 passed** again.

Noted, because a later pass will otherwise mis-read it: the floor venv resolved a **newer** asgiref
(3.12.1) than the shared `.venv` (3.11.1). The plan's premise for floor question 4 ("the floor's
asgiref is older") does not hold. That does not weaken the run — 3.10 and Django 5.2.0 are the pinned
axes — but it means the floor is not an "everything older" environment and floor question 4 was
answered by reading the mechanism rather than by an older asgiref exhibiting a difference.

**The five floor questions, answered.**

1. **`SpooledTemporaryFile`'s reported positions at Python 3.10 — exact `int`, claim holds for this
   stream.** `/tmp/dsf-floor/bin/python -c "…"` at 3.10.19: unrolled spool `seek(0, SEEK_END) -> 3`,
   `tell() -> 3`; rolled-to-disk spool `-> 6` / `-> 6`; both `type(...) is int`. `hasattr(f, "seekable")`
   is **`False`** at 3.10, which independently re-confirms why `_declares_seekable` must believe the
   absence (and why a narrower test would drop the ASGI spool onto the read branch at the floor).
2. **`LimitedStream` at Django 5.2.0 — the claim is FALSE for this stream, on both Django versions.**
   `LimitedStream` subclasses `io.IOBase` and overrides neither `seek`, `tell`, nor `seekable`, so
   `seekable()` answers **`False`** and `tell()` raises **`io.UnsupportedOperation: seek`**. Measured
   identically at Django 5.2.0 and at the shared environment's 6.0.5. `LimitedStream` therefore never
   reaches `_measured_remaining`'s arithmetic at all: `_declares_seekable` sends it to the bounded read
   on the first line. Behaviour is fail-safe, and the module docstring already states this correctly
   (`_request_body.py` `#"LimitedStream`` subclasses ``io.IOBase``"`) — it is
   `_measured_remaining`'s new docstring that contradicts it. **Corrected in this pass** (Low finding 3).
3. **`CsrfViewMiddleware.process_view` at Django 5.2.0 — both mechanisms present.** Read from
   `inspect.getsource`: `if getattr(request, "csrf_processing_done", False): return None` precedes
   `if getattr(callback, "csrf_exempt", False): return None`. So (a) the exemption is read for
   **truthiness**, which is what lets a lazily-evaluated object be the value at all, and (b) the
   `csrf_processing_done` short-circuit exists, which is what makes the view's continuation a genuine
   no-op in the installed arrangement — `_accept` is what sets the attribute. Non-weakening check 2 is
   confirmed at the floor and not merely at current.
4. **asgiref at the floor propagates the ContextVar across the `sync_to_async`-adapted
   `process_view`, in both directions.** The mechanism, named rather than inferred from a green run:
   `SyncToAsync.__call__` copies the caller's `contextvars` context into the executor thread and then
   calls `asgiref.sync._restore_context(context)` on return, which writes back every var the thread
   changed. Verified present and called at the floor (asgiref 3.12.1) and in the shared environment
   (3.11.1). So the *read* direction the shipped code depends on (`__acall__` sets on the loop, the
   adapted `CsrfViewMiddleware.process_view` reads in a thread) works by context copy-in, and the
   *write* direction (a value set inside an adapted hook and read by a later adapted hook) works by
   `_restore_context`. The second half matters for the recommended fix to High finding 1.
5. **Cancellation semantics on Python 3.10 for `settle`'s cancel-and-await-and-re-raise arm — confirmed
   by execution.** All of `tests/test_routers.py` passes at 3.10.19, including
   `::test_cancelling_the_teardown_ends_the_close_attempt_instead_of_orphaning_it`,
   `::test_a_cancelled_disconnect_leaves_no_task_retaining_the_connection`,
   `::test_a_teardown_that_raises_still_settles_the_close_and_propagates` and Worker 2's new
   `::test_a_teardown_cancelled_before_it_returns_still_settles_the_close`. The arm uses only
   `Task.cancel()`, `asyncio.shield`, `contextlib.suppress` and a bare `raise` — none of `Task.uncancel`
   / `Task.cancelling` / `TaskGroup`, the 3.11 additions — so nothing in it depends on the newer
   bookkeeping, and the floor run is the evidence rather than the reasoning.

### High:

#### The exemption is withdrawn chain-wide while the boundary is run per-marked-callback, so a callback that lost only the marker has Django parse an over-limit multipart body

`middleware/request_body.py::GraphQLRequestBodyBoundaryMiddleware.__call__` /
`::__acall__` set `_boundary_middleware_active` for **every** request travelling the chain, which makes
`::_CsrfOrderingExemption.__bool__` answer `False` for every package callback. But
`::process_view` runs the boundary only for a callback carrying `_BOUNDARY_MARKER`. The two facts are
independent, and the gap between them is the exact ordering failure `_require_boundary_before_csrf`
exists to close off: **the exemption is gone and the boundary has not run**, so the project's
configured `CsrfViewMiddleware` reads `request.POST` — the `MultiPartParser` invocation — on a body
no cap has looked at.

This is not a reading; it is measured. `docs/builder/temp-tests/r1/test_r1_probes.py`, with a
`MultiPartParser.parse` counter wrapped around a real request through the real chain and an
**enforcing** test client (a non-enforcing one short-circuits on `_dont_enforce_csrf_checks` and never
reads `request.POST` at all — the fixture would otherwise answer the question for the code):

| Mount | Chain | Status | `MultiPartParser.parse` calls |
| --- | --- | --- | --- |
| `/marked-capped/` (stamped callback) | `[boundary, stock CSRF]` | `413` | **0** |
| `/wrapped-capped/` (wrapper copies `csrf_exempt`, `view_class`, `view_initkwargs`, not the marker) | `[boundary, stock CSRF]` | `403` | **1** |
| `/marked-capped/` | `[stock CSRF]` | `413` | **0** |
| `/wrapped-capped/` | `[stock CSRF]` | `413` | **0** |

Rows 2 and 4 are the same mount, the same view class, the same `max_request_body_bytes=32`, the same
over-limit multipart body. **Installing the middleware is what turns a request that was refused before
the parse into a request that is parsed first.** So this is a behaviour regression introduced by
`2701f41a`, not a pre-existing hole — the wrapper shape that kept the ordering before now loses it.
With `_RejectingCsrfMiddleware` in place of stock CSRF the same probes show the project's CSRF class
**entered** on the over-limit body (`calls == ['/wrapped-capped/']`), which is the identical witness
`tests/test_views.py::test_the_chain_refuses_an_over_limit_multipart_before_any_csrf_read` uses in the
affirmative.

**Reachability is settled, and it is not hypothetical.** `views.py::_RequestBodyBoundaryMixin.as_view`'s
own docstring names "a wrapper that drops the attributes" as a live shape.
`functools.wraps` copies `__dict__`, so both marks travel together and a `wraps`-based decorator is
safe — but a hand-written wrapper that copies the one mark that existed before `2701f41a` is not, and
**the repository already contains one**:
`examples/fakeshop/test_query/test_transport_api.py::_carrying_the_packages_csrf_mark` copies
`view_class.as_view().csrf_exempt` onto a probe mount and knows nothing about `_BOUNDARY_MARKER`. Its
docstring even states the rule it is now half-following: "*every Django view decorator carries it
onward through `functools.wraps`*". Any consumer who wrote a wrapper against the shipped `0.0.14`
surface wrote that shape.

Severity is High for two independent reasons in `BUILD.md` `## Severity definitions`: it is a
**security regression** (the cap stops being a gate on the precise input the cap exists for), and it is
a **spec-contract violation** — three shipped docstrings state a contract that is false in this state:
`middleware/request_body.py`'s module docstring ("Both arrangements enforce CSRF and both enforce the
cap"), `::_CsrfOrderingExemption`'s ("It is never a bypass in either state"), and
`views.py::_RequestBodyBoundaryMixin._enforce_request_boundary`'s (the `413` "is raised before
`request.POST`, `request.FILES`, `MultiPartParser`, or any upload handler is entered — because
[the middleware] runs this boundary from a chain position ahead of the CSRF middleware, **or**, where it
is not installed, because the package view is exempt"). In the marker-lost-and-installed state neither
limb of that "or" holds, so the sentence is not merely imprecise, it is false.

It is also `BUILD.md` `### Fail-open shapes` verbatim: `getattr(view_func, _BOUNDARY_MARKER, False)`
converts "this callback lost its marks" into "not our view, pass through" — a `getattr` default standing
in for an absence that is meaningful, on a security decision. Worker 1's plan-time read named it "the
live suspect" and Worker 2 measured its consequence (proof entry 3, 4 rows); what neither established is
reachability, which is what this finding supplies.

**Recommended change — make the two facts one fact, and key the withdrawal off the boundary having
actually run for *this* request.** The narrowest shape that does not need a new context-propagation
direction: have `__call__` / `__acall__` set a ContextVar to the **request object** rather than to a
bare `True`, and have `__bool__` answer

```python
request = _boundary_middleware_request.get()
return request is None or not getattr(request, _BOUNDARY_ENFORCED, False)
```

`process_view` already stamps `_BOUNDARY_ENFORCED` immediately after enforcing, and the stamp is an
attribute on the shared request object, so it crosses the `sync_to_async` boundary for free — this
reuses exactly the propagation direction the shipped async rows already prove (floor question 4). The
resulting failure mode for a marker-less callback is the **fallback** arrangement: the exemption stays
truthy, the chain's CSRF middleware skips the callback, the view enforces the boundary itself and
re-enters CSRF through `csrf_protect`. That degrades the *class* (stock instead of the configured
subclass, which is the pre-`2701f41a` behaviour and is what the wrapper already got) instead of
degrading the *ordering*, and the ordering is the one the `413` depends on.

Two docstring corrections follow the fix, in the same change: the `or` in
`views.py::_enforce_request_boundary` becomes true again, and
`::_CsrfOrderingExemption`'s "true only when needed" should say *needed for this request* rather than
*needed on this chain*.

**Test expectation.** New rows in `tests/test_views.py`, driven through `_chain` against a mount whose
callback carries `csrf_exempt` but not `_BOUNDARY_MARKER`: an over-limit multipart must be refused
`413` with `_RejectingCsrfMiddleware.calls == []` on **both** transports, and an under-limit request
must still reach a CSRF check. The `MultiPartParser.parse` counter in
`docs/builder/temp-tests/r1/test_r1_probes.py` is the stronger witness and is worth promoting with it,
because the CSRF-call-log witness depends on the stand-in class reading `request.POST` at all. The
probe file is the promotion source; see `### Temp test verification`.

### Medium:

#### No row drives a request through a chain that carries the boundary and no CSRF middleware

`_require_boundary_before_csrf` deliberately permits `MIDDLEWARE` with the boundary and no CSRF entry,
and `__call__` withdraws the exemption on that chain anyway — so the endpoint's only CSRF check is the
view's unconditional continuation. `tests/test_views.py::test_a_chain_that_lists_the_boundary_after_csrf_is_refused_at_startup`
accepts that chain at **startup** only; no permanent row sends a request through it. The plan
(P1b open question 2) fixes the disposition in advance: "*if nothing pins it, that is a missing row
rather than an accepted gap*."

The behaviour is correct — `docs/builder/temp-tests/r1/test_r1_probes.py::test_boundary_installed_with_no_csrf_middleware_still_checks_csrf`
passes: on `MIDDLEWARE=[boundary]`, a non-enforcing client gets `200` on both transports and an
`enforce_csrf_checks=True` client gets **`403`** on both. So this is `BUILD.md`'s "missing tests for
important branches", not a defect. Note the fixture trap it walks past, which is why the row must be
written this way: with a non-enforcing client both arrangements answer `200` and the assertion is
non-distinguishing.

**Recommended change.** Promote that probe into `tests/test_views.py` as a permanent row, both
transports, both client strictnesses, so the disjunct `_require_boundary_before_csrf` admits is pinned
by a request and not only by a constructor call.

### Low:

#### `_measured_remaining`'s docstring named a stream that can never reach the code it justifies — CORRECTED IN THIS PASS

`_request_body.py::_measured_remaining` claimed "production Django streams report positions as the
built-in `int` (`SpooledTemporaryFile` and `LimitedStream` both do, on both supported interpreters)".
Floor question 2 falsifies the `LimitedStream` half at Django 5.2.0 **and** at 6.0.5: it declares
`seekable()` `False` and its `tell()` raises `io.UnsupportedOperation`, so `_declares_seekable` returns
it to the bounded read on the function's first line and it never reaches the arithmetic the sentence
is justifying. The sentence also contradicted the module docstring 200 lines above, which states the
`LimitedStream` behaviour correctly — so the file asserted both.

Load-bearing, because the parenthetical is the entire evidence offered for "that exact type is what
this function accepts": a reader who believed it would think WSGI requests are measured by the probe,
when they are measured by the bounded read. Behaviour is unaffected and fail-safe either way.

Corrected under `worker-3.md` "Scope"'s carve-out for a code-comment correction the floor read
falsifies, which the round's own plan assigns to "whichever pass runs the floor"
(`### Notes for Worker 1` item 7). The edit is **docstring text only**, proved mechanically: the
module's AST with every docstring stripped is byte-identical to `HEAD`'s
(`ast.dump` comparison after removing each `Module`/`ClassDef`/`FunctionDef` docstring node), and
`grep -c -F` on proof entry 8's anchor still returns exactly `1`. `ruff format`, `ruff check`, and
`scripts/check_trailing_commas.py --check` all pass on the file; both the shared-environment and floor
runs of the focused scope are still **327 passed**.

Left untouched deliberately: the same docstring's **pre-existing** "(`ASGIRequest`'s spool and
`WSGIRequest`'s `LimitedStream` both measure honestly on both supported interpreters)" — it is not in
this diff, and "does not lie" is true of a stream that declines to answer, so it is imprecise rather
than false. Recorded for a future pass rather than edited outside the carve-out.

#### `process_view` reads `view_func.view_class(**view_func.view_initkwargs)` unguarded, where the package's other middleware guards the same read

`middleware/request_body.py::GraphQLRequestBodyBoundaryMiddleware.process_view` treats the marker as a
sufficient precondition for three attributes and dereferences two of them directly. Its sibling
`middleware/debug_toolbar.py::DebugToolbarMiddleware.process_view` — same package, same hook, same
global traffic — guards the identical read (`getattr(view_func, "view_class", None)` plus
`isinstance(view, type)`) precisely because an unrelated decorator may attach a `view_class`. A
callback carrying the marker but not `view_class`, or one whose `view_initkwargs` a wrapper replaced,
turns into an `AttributeError`/`TypeError` inside `process_view`, which is an unhandled `500` rather
than one of the controlled responses this module is careful to produce. Not reachable through any
supported seam (the marker name is package-specific), which is why this is Low and not higher.

**Recommended change.** Fold the attribute check into the recognition rather than adding a second
branch: `view_class = getattr(view_func, "view_class", None)` and treat a missing one as "not ours",
so the marker test and the attribute test are one predicate — and note that after High finding 1's fix
the "not ours" arm is the safe fallback arrangement rather than a bare pass-through, which is what
makes folding them together correct instead of merely tidier.

#### The charset guard excludes GET on a rationale that applies verbatim to HEAD

`views.py::_RequestBodyBoundaryMixin._enforce_body_charset_declaration` states "GET is excluded because
this endpoint reads no body on GET, so a content type on one describes nothing the package parses."
That is equally true of HEAD, which the guard does not exclude — so a `HEAD` carrying
`Content-Type: application/json; charset=iso-8859-1` now receives `400` where upstream's `dispatch`
would have answered `405`. The direction is strictly stricter and the reason string is the shared
`_JSON_PARSE_REASON`, so nothing is attributable and nothing fails open; and it is *consistent with the
cap*, since `::_enforce_request_body_limit` also skips only GET and `::_is_multipart_form_post`
documents the non-GET/POST case as "counted like any other body, which is the stricter direction". So
the two guards agree with each other; the mismatch is between this guard's scope and its own stated
reason.

Not resolvable in R1: spec Decision 9 has **no declaration half at all** (plan V3), so there is no
contract to check the method scope against. Routed to R2 under `### Notes for Worker 1`; the code change,
if any, is one method name in a tuple and belongs with the spec sentence that authorizes it.

### DRY findings

**(a) Where the marker constants and the exemption object live — the existence challenge answered, the
layering question escalated.**

*Should `_CsrfOrderingExemption` exist at all, in that module?* **Yes, and the class is the minimal
shape available.** Django reads the mark as `getattr(callback, "csrf_exempt", False)` and consumes it
for truthiness at request time (verified at the floor, question 3). Nothing simpler can answer a
per-request question at that read site: a plain `True` cannot; a function object is unconditionally
truthy; a `SimpleLazyObject` would evaluate once and cache. A one-method `__bool__` class with one
shared instance is the whole mechanism. `BUILD.md`'s deletion precedent does not apply — there is no
machinery here to narrow away, only the one object the read site requires. **Decided: keep.**

*Where it lives* is a different question and a real cost. `views.py` — the package's core view module —
now imports three private names from the `middleware/` subpackage, which reverses the natural layering:
a deployment that installs no middleware still imports `middleware/request_body.py` (and through it
`django.middleware.csrf` and `django.utils.module_loading`) whenever it imports a view. The module
docstring's justification ("`views.py` imports this module for the exemption object, so this module
must never import `views.py`") rules out the reverse import; it does not establish that either direction
is needed. Worker 1's proposed alternative — move them into `_request_body.py` — trades one mismatch
for another: that module's own docstring scopes it to stream measurement ("the only file in the package
that names `HttpRequest._stream`"), and CSRF-ordering state is not measurement. The shape that removes
the inversion without that mismatch is a **third private module** owning only the two attribute names,
the ContextVar and the exemption class, imported by both `views.py` and `middleware/request_body.py`,
after which neither of those two imports the other.

Which of the three is right is a **package-layering contract call**, not a defect, so it is escalated
rather than held at `revision-needed` (`worker-3.md` `### The existence challenge`). It also interacts
with High finding 1: the recommended fix changes what the ContextVar holds, so if the placement is
going to move, moving it in the same pass is cheaper than moving it twice.

**(b) Two modules named `request_body.py`. Decided: no rename.** The bare basename collides; no import
site does. Every reader reaches them as `django_strawberry_framework._request_body` and
`django_strawberry_framework.middleware.request_body`, the leading underscore already marks one as
private primitives, and `docs/TREE.md` will render them in different subtrees. A rename would touch
`views.py`, `tests/test_views.py`, `examples/fakeshop/apps/kanban/constants.py` and R3's doc work for a
cost paid only by someone reading a `git status` line rather than code. Not a finding, and explicitly
not deferred to R3 either.

**(c) Two "is this one of our views?" mechanisms. Decided: genuinely two decisions; no shared
recognizer.** They answer different questions on purpose. `debug_toolbar` must recognize *any*
Strawberry view (`issubclass(view, BaseView)`), package or consumer-defined, and can afford to import
the class. `request_body` must recognize *a package callback carrying this package's boundary* and must
not import the view classes at all, because `views.py` imports it — the one-way dependency is the
constraint, and a shared recognizer would have to satisfy both, so it would end up being two functions
in one file. The asymmetry the plan flags is real and is filed separately as Low finding 2 (the
unguarded attribute read), which is a one-line fix inside `request_body.py` rather than a
consolidation.

**(d) `__call__` / `__acall__` twin bodies. Agreed with the plan: not a finding.** Read at `HEAD` and
confirmed: the docstring names the reason sharing is wrong (a synchronous `finally` would reset the
mark before the CSRF middleware read it) and the shape matches the package's established twin idiom
(`views.py::_run_after_csrf_check` / `::_async_run_after_csrf_check`). Re-verified that there is no
third copy: `grep -rn '\.reset(' django_strawberry_framework/` returns 11 sites across 4 modules and
none is a third instance of the set-around-a-downstream-call-with-an-async-twin shape.

**(e) The `HTTPException` -> `text/plain` translation. Confirmed to agree exactly; not a finding.**
Read out of upstream at the floor: both `strawberry.django.views.GraphQLView.dispatch` and
`AsyncGraphQLView.dispatch` build `HttpResponse(content=e.reason, status=e.status_code,
content_type="text/plain")`, which is the identical three-argument construction
`middleware/request_body.py::process_view` builds. Status, body and content type all agree, so a client
genuinely cannot tell which side of the CSRF check refused it. Consolidating would mean importing an
upstream private handler to save three arguments, which is a worse dependency than the duplication.

**(f) NEW — the declared-charset read is duplicated, and Worker 1's DRY analysis did not catch it.**
`views.py::_form_encoding_is_utf8 #"declared = (request.content_params or {}).get(\"charset\")"` and
`::_enforce_body_charset_declaration #"declared = (request.content_params or {}).get(\"charset\")"` are
now the same two lines with different consequents:

```
declared = (request.content_params or {}).get("charset")
if declared is not None and not _canonicalizes_to_utf8(declared):
    return False                                  # _form_encoding_is_utf8
    raise HTTPException(400, _JSON_PARSE_REASON)   # _enforce_body_charset_declaration
```

The plan's DRY read credits the new guard with reusing `_canonicalizes_to_utf8` (correct) but treats the
declaration read as new code; it is a near-copy, and it is the kind that drifts, because the two sites
must keep agreeing about what "declared" means for the two guards not to disagree about a request shape
— the same argument `_is_multipart_form_post`'s docstring makes for naming the multipart discrimination
once. **Recommended shape:** one module-level `_declared_charset_is_unhonourable(request) -> bool`
returning `declared is not None and not _canonicalizes_to_utf8(declared)`, called by both. Low
severity — two lines, no behavioural risk — but it should land with High finding 1's pass rather than
be deferred, since that pass is already in `views.py`.

### Fail-open shape hunting (all nine read independently, against Worker 1's plan-time reads)

1. **`getattr(view_func, _BOUNDARY_MARKER, False)`** — Worker 1 called it "the live suspect" and was
   right. **Confirmed fail-open, measured, and filed as High finding 1.** The answer that must be
   refused is not an input spelling: it is *"the boundary has not run for this request, and the CSRF
   ordering has been withdrawn anyway"* — and that answer is currently reachable and permitted.
2. **`getattr(request, _BOUNDARY_ENFORCED, False)`** (`views.py::_enforce_request_boundary_once`) —
   **agreed fail-closed.** The fail-open direction would be a request arriving pre-stamped without the
   boundary having run. Client-controlled input cannot set an attribute on `HttpRequest` (headers become
   `META` keys), and a package-wide grep for the attribute name
   (`graphql_request_body_boundary_enforced` and `_BOUNDARY_ENFORCED`) finds exactly one writer,
   `middleware/request_body.py::process_view #"setattr(request, _BOUNDARY_ENFORCED, True)"`, and two
   readers (`views.py` and one test). Nothing in Django writes a same-named attribute. Not a finding.
3. **`_measured_remaining`'s `if not probed` and `remaining <= 0` returns** — **confirmed by following
   the call chain, not the names.** Both answer `_Probe.UNMEASURABLE`, and
   `::body_exceeds_limit` routes it to `_bounded_read_exceeds_limit(request, stream, limit)`, i.e.
   "cannot determine" becomes "measure by reading" — while `CORRUPTED` returns `True` (refuse) and only a
   positive `int` reaches `remaining > limit`. This is the corrected shape the prior round's
   `max(end - position, 0)` lacked, and the new exact-`int` gate sits between them in the same
   fail-safe direction. Not a finding.
4. **`(request.content_params or {}).get("charset")`** — **benign, confirmed at the floor.**
   `HttpRequest._set_content_type_params` assigns `content_params` unconditionally from
   `parse_header_parameters(meta.get("CONTENT_TYPE", ""))`, which returns a `dict` (empty for an absent
   header), so the left operand is always a mapping and the `or {}` arm is unreachable-but-harmless.
   Both branches yield the same answer. Recorded as a DRY item (f), not a fail-open one.
5. **`_declares_seekable`'s `return True` when `seekable` is absent** — **re-read against the floor
   answer and still correct.** `hasattr(spool, "seekable")` is `False` at 3.10.19 (measured, floor
   question 1), so a narrower test would drop the ASGI spool onto the read branch at exactly the floor
   the card protects. The `getattr` default stands in for a meaningful absence *deliberately*, and the
   answer it produces is "probe further", not "permit". Not a finding.
6. **`_require_boundary_before_csrf`'s three-way early `return`** — **all three disjuncts enumerated;
   none admits a chain that parses before the cap.**
   - `boundary_index is None` — this middleware is being constructed but is not in `MIDDLEWARE`
     (direct instantiation, which the rows themselves do). Then `__call__` never runs from the chain,
     the ContextVar stays at its `False` default, the exemption stays truthy, and the view-local
     ordering holds. Safe.
   - `csrf_index is None` — no CSRF entry. Probe 2 confirms the endpoint is still protected (`403` to
     an enforcing client); this is the Medium finding's missing row, not a hole.
   - `csrf_index > boundary_index` — the documented order. Correct.
   Two edge cases worth naming and neither unsafe: an entry subclassing **both** middleware registers
   only as the boundary (the `elif` never runs), which permits; and a `CsrfViewMiddleware` subclass that
   raises `MiddlewareNotUsed` — so Django drops it — is still counted by index, which over-refuses.
   Both are contrived and both fail in the safe direction. Not findings.
7. **`settle`'s `if self.attempt is None or self.attempt.done(): return`** — **confirmed: neither
   absent-ish case needs a state transition,** which is exactly the plan's open question 4. Every
   terminal state is written by the attempt itself: `_attempt_close` sets `CLOSED` after its own await
   returns, `ABANDONED` on cancellation or on a spent attempt bound, and `DECIDED` on a raise. `None`
   means no attempt ever started, and `settle` explicitly never starts one. `done()` means the attempt
   already recorded its own outcome. Not a finding.
8. **`contextlib.suppress(asyncio.CancelledError)` around `await self.attempt`** — **the `raise` is
   unconditional on every path through the arm.** Read at `HEAD`: the `except asyncio.CancelledError:`
   block is exactly `self.attempt.cancel()`, the `with contextlib.suppress(...)` statement, and a bare
   `raise` as the block's last statement, with no `return`, no branch and no nested `try` between them.
   The suppression is scoped to the one `await` and cannot swallow the caller's cancellation. Not a
   finding.
9. **`_CsrfOrderingExemption.__bool__` reading a ContextVar whose `default=False`** — **the default is
   the safe one.** `False` resolves to "the view must supply the ordering itself", which is the
   backward-compatible fallback arrangement: the callback is exempt from the chain's CSRF middleware and
   the view enforces the boundary then re-enters CSRF. A request that never travelled the chain is
   exactly the request that needs that. Proof entry 5 (`return False`, i.e. always-withdrawn) fails 5
   rows including both
   `::test_without_the_middleware_the_view_keeps_its_own_ordering_and_exemption` halves, so the default
   is pinned in the direction that matters. Not a finding on its own — but note that High finding 1 is
   the *other* half of this object's decision, and the recommended fix makes this default and the
   per-request answer one mechanism.

### Non-weakening checks

1. **The mid-connection shield in `close()` is unchanged — confirmed by reading, not by the commit
   message.** `consumers.py::_ConnectionRevocation.close` still ends
   `if self.state == _REVOCATION_CLOSING: await asyncio.shield(self.attempt)`, and `ba66ab49`'s diff
   touches `settle`, `_attempt_close`, two docstrings and the generated `disconnect` — never `close`.
   The mid-connection rows in `tests/test_routers.py` still pin it: proof entry 9 (removing `settle`'s
   new arm) fails `::test_cancelling_the_teardown_ends_the_close_attempt_instead_of_orphaning_it` and
   `::test_a_cancelled_disconnect_leaves_no_task_retaining_the_connection` and **not** the round-2
   bystander rows, which is the correct separation — the two shields answer different questions and are
   pinned by different rows.
2. **Exactly one complete CSRF check on every request that passes the boundary, in both arrangements —
   confirmed, and the Django-internals half confirmed at the floor.** Installed: the configured class's
   `process_view` runs the check and `_accept` sets `request.csrf_processing_done`, so the view's
   `csrf_protect` continuation hits `if getattr(request, "csrf_processing_done", False): return None`
   (read from Django 5.2.0's source, floor question 3) and is a no-op — one check, by the configured
   class. Not installed: `getattr(callback, "csrf_exempt", False)` is truthy, the chain's middleware
   returns before `_check_token`, and the view's continuation performs the only check — one check, by
   the stock class. Neither zero nor two. Pinned in both directions by proof entries 4 (`return True`:
   3 rows, the configured class stops running) and 5 (`return False`: 5 rows, the fallback loses its
   ordering).
3. **The boundary cannot run zero times — confirmed for both arrangements and for the nesting shape.**
   Proof entry 7 removes the view's own enforcement: **8 rows** fail, including every
   no-middleware row. Proof entry 3 removes the chain's: **4 rows** fail, with the empty CSRF call log
   as the witness rather than the status code. For the nesting shape (`as_view()` called from inside
   another view) the *ordering* is lost but the *measurement* is not, because
   `_enforce_request_boundary_once` runs unless the request is stamped and only `process_view` stamps.
   **One qualification, and it is High finding 1:** the *ordering* half of this check does not hold for
   a marker-less callback on an installed chain. The measurement still happens; the gate does not.
4. **The cap's declared/counted rungs and the multipart carve-out are unchanged, and the middleware
   path reaches the same rungs with the same mount cap.** `_enforce_request_body_limit` is not in
   `2701f41a`'s diff and its rungs read unchanged at `HEAD`: resolve the cap, skip GET, refuse on a
   declared `CONTENT_LENGTH` over the limit, return for a multipart form, then the counted rung. The
   middleware builds `view_func.view_class(**view_func.view_initkwargs)`, which is character-for-character
   what Django's own `View.as_view` does, and `View.__init__` sets each initkwarg as an attribute — so
   `self.max_request_body_bytes` is the mount's. `setup()` is not called and is not needed: nothing on
   the boundary path reads `self.request`, `self.args` or `self.kwargs`. Pinned live rather than
   argued: `::test_the_chain_refuses_an_over_limit_multipart_before_any_csrf_read` refuses against the
   `_MOUNTED_CAP = 32` mount through the middleware path, which only happens if the mount's keyword
   reached the instance the middleware built.
5. **Upstream's coroutine marking and Django's `view_class` / `view_initkwargs` bookkeeping survive.**
   `as_view` no longer wraps at all — it sets two attributes on upstream's own callback and returns it —
   so the originals are the untouched originals rather than something carried through a decorator.
   `::test_the_view_callback_of_both_views_carries_the_csrf_exempt_mark` asserts
   `iscoroutinefunction(view) is (view_class is AsyncDjangoGraphQLView)`, `view.view_class is view_class`
   and `view.view_initkwargs == {"schema": SCHEMA}`; proof entry 5 fails both halves of that row, so it
   is live and not vacuous. `csrf_protect` branching on the coroutine marking is what the async
   `_csrf_protected_async_run` path depends on, and the async rows pass at the floor.

### The plan's remaining open questions, answered

**P1a.** (i)-(v) all hold: the refusal is composed third in `_enforce_request_boundary`, runs from
`_enforce_request_boundary_once` on both transports through the one shared method, reads headers only,
carries `_JSON_PARSE_REASON`, and is scoped by the same `_is_multipart_form_post` discriminator the cap's
carve-out and the multipart encoding guard use — so the three guards cannot drift on what "multipart"
means, and the two encoding guards own disjoint request shapes with neither a gap nor an overlap (a
multipart POST goes to `_enforce_multipart_form_encoding` and nothing else; everything non-GET
non-multipart goes here and nothing else). Proof entry 2 (deleting the carve-out) fails
`::test_a_get_carrying_a_stray_multipart_content_type_is_not_a_multipart_form` and
`::test_a_multipart_declaration_is_left_to_the_form_encoding_guard`, which is precisely the
disjointness. *Open question 1* (method scope) is Low finding 3 above, routed to R2. *Open question 2*
(the `400` on the wire in both arrangements, both transports): confirmed — the middleware path builds
the same `HttpResponse(content=..., status=..., content_type="text/plain")` upstream's `dispatch`
builds, read out of both upstream classes at the floor, and the view path *is* upstream's translation.

**P1b.** *Open question 1* is High finding 1. *Open question 2* is the Medium finding. *Open question 3*
(early `import_string` of every `MIDDLEWARE` entry): harmless. Django's `load_middleware` iterates
`reversed(settings.MIDDLEWARE)`, so entries listed *before* ours have not been imported when our
`__init__` runs and our audit forces them; `import_string` resolves through `sys.modules`, so Django's
own import moments later is a cache hit and no module-level side effect runs twice. A failing entry
raises the underlying `ImportError`/`ModuleNotFoundError` naming the offending dotted path, from a
traceback that shows `_require_boundary_before_csrf` -> `import_string` — attributed to our
construction rather than to Django's `load_middleware`, which is a legibility cost and not a
correctness one, and the message still names the real culprit. *Open question 4* (duplicate entries):
a duplicated **CSRF** entry is judged against the first, which is the correct rung because the first
one Django reaches is the one whose `request.POST` read parses the body — now pinned by Worker 2's
`::test_the_first_csrf_entry_is_the_one_the_ordering_is_measured_against`. A duplicated **boundary**
entry is judged against the *last*, so `[boundary, csrf, boundary]` is refused even though the first
boundary does precede the CSRF read: **over-refusal, in the safe direction**, and I agree with
Worker 2's decision to leave it unpinned rather than freeze an unreviewed answer — the strictness is
defensible (a chain that lists the boundary twice is a chain nobody meant to write) and it is a
contract sentence for R2, listed under `### Notes for Worker 1`. *Open question 5* (async chain
mechanics) is floor question 4 above: the mechanism is asgiref's context copy-in plus
`_restore_context`, verified present at the floor, and `setattr(request, _BOUNDARY_ENFORCED, True)`
crosses back because the request object is shared rather than copied.

**P2a.** (i)-(iv) all hold. No foreign numeric protocol executes inside the gate: `type(x) is int`
runs no consumer code, and an `int` subclass — which is what gets past `isinstance` — is refused, so
neither `__sub__` nor `__le__` can be reached from a foreign object. The verdict for any other shape is
`UNMEASURABLE`, which `body_exceeds_limit` routes to the bounded read, so a bound is still supplied
(read out of `body_exceeds_limit` rather than inferred: `CORRUPTED` -> `True`, `UNMEASURABLE` -> bounded
read, otherwise `remaining > limit`). The type test sits **after** `_position_restored`, so the bounded
read starts where the request started. And the rule matches `views.py::_resolved_max_request_body_bytes`'s
for the stated reason. *Open question 1* (the interpreter claim) is Low finding 1, corrected.
*Open question 2* (`_position_restored`'s exception boundary): still complete. Read at `HEAD` — the
whole body, the foreign `seek(position)` and the foreign `==` included, sits inside one
`except Exception: return False`, and moving the type test downstream of it changed nothing about that
scope. `BaseException` is deliberately not caught, so cancellation still propagates.

**P2b.** (i)-(v) all hold; the shield in `close()` is non-weakening check 1. *Open question 1*
(who was cancelled): **out of contract, and here is what enforces it.** `attempt.cancel()` occurs
**once** in the whole package, inside `settle`; `self.attempt` is created and referenced only within
`_ConnectionRevocation`, which is package-private and reachable only as a consumer's
`consumer._revocation.attempt`. So no supported seam cancels it. The one reachable third-party
canceller is loop teardown (`asyncio.runners._cancel_all_tasks`, an ASGI server's shutdown), and that
cancels the *settling* task too — in which case the caller's own cancellation is the one that matters
and re-raising it is right. **The masking is real if it ever becomes reachable**, and I measured it
rather than reasoning about it:
`docs/builder/temp-tests/r1/test_r1_probes.py::test_a_third_party_cancellation_of_the_attempt_masks_the_callers_exception`
cancels only the attempt while a `RuntimeError` is in flight through the `finally`, and a
`CancelledError` comes out in the `RuntimeError`'s place. Not a finding, because it is unreachable
through any supported seam; recorded so the next reader does not have to re-derive it, and worth one
spec sentence in R2 ("only the connection's final teardown cancels this task") since that premise is
currently only a code comment. *Open question 2* (a never-started attempt resting in `CLOSING`):
**harness-impossible, in those words.** `close()` creates the task and immediately
`await asyncio.shield(self.attempt)`, so the loop schedules the task's first step before anything
`disconnect` could queue; a cancellation arriving before that first step would have to be queued
before the task exists. No wire-level row can exhibit it, and per
`BUILD.md` `### Harness-impossible interleavings` the right response is to record the limitation rather
than add a row that cannot fail — which is what this bullet does. The invariant is already asserted at
the production call site by the existing `ABANDONED` rows. *Open question 3* (the unbounded wait in
`finally`): **deliberate and unchanged**, recorded rather than left open. `docs/feedback.md`'s
prescribed "bounded final wait" is one of two offered alternatives ("or"), the pre-change code awaited
the same shielded task just as unboundedly, and the bound that actually exists is the server's own
application-close timeout — which is the cancellation this fix now handles rather than ignores. A
prescribed remediation is a hypothesis (`BUILD.md` `### Worker 0 verifies every finding against
source`), and adding a package-chosen timeout here would mean the package deciding how long a
deployment's transport may take to flush a close. Not a finding. *Open question 4* is fail-open item 7.

### Dispatched findings checklist walk

Worker 2 deliberately ticked nothing and the plan reserves the ticks for Worker 1's final verification;
that is correct and is not read as unaddressed work. Walking the four boxes for whether the
**contract** is delivered by the diff, which is what `BUILD.md` `### Dispatched findings checklist`
asks of this pass:

1. **P1 charset — delivered.** The refusal exists at the named site, before any parse, with the shared
   `400`; absent passes, every alias passes, `utf-8-sig` and an unknown codec do not; sync and async
   raw-envelope rows drive it over the real endpoint with `Client().generic` / `AsyncClient().generic`
   (so the driver does not re-encode from the declared charset) carrying a non-ASCII UTF-8 document.
   Proof entry 1 removes it and 7 rows fail. Every property the review asked for is refused that was
   previously accepted. Ready for Worker 1 to tick, subject only to Low finding 3's method-scope note,
   which changes no shipped behaviour.
2. **P1 CSRF class — delivered for the shape the review named, NOT delivered for one shape it created.**
   The configured class does now run in full behind the boundary (`::test_the_projects_own_csrf_middleware_runs_when_the_chain_supplies_the_ordering`
   gets the *subclass's* refusal, not a package response), on both view variants, with an over-limit
   multipart still refused before parsing. The deliberate deviation from the prescription — the
   exemption and stock re-entry **withdrawn conditionally rather than removed** — is a sound contract
   choice and is the one M-A's rejected-alternative list also settles: removing them outright would
   change behaviour for every deployment that has not edited `MIDDLEWARE`. **But High finding 1 is a new
   ordering loss this box's own mechanism introduced**, so the box stays open until the fixing pass
   closes it. A tick means landed *and* audited, and this one does not yet audit clean.
3. **P2 foreign position — delivered.** No numeric protocol of a foreign object executes inside the
   gate; regressions cover `__sub__` **and** the ordering comparison, not only the `None - int`
   `TypeError` case (`::test_a_position_object_whose_numeric_protocol_raises_never_runs_inside_the_gate`
   parametrizes `subtraction-raises` and `comparison-raises` across both view classes and asserts the
   `413`, the `limit + 1` read ceiling, bytes left unread, and `_body` never materialized). Proof entry
   8 removes it and 6 rows fail. The input now refused and previously accepted: a position or end object
   of any non-exact-`int` type, which previously reached `end - position` and `remaining <= 0`. Ready to
   tick; the docstring that justified it was wrong and is corrected in this pass.
4. **P2 orphaned close — delivered.** `disconnect` enters settlement through `finally`; a cancellation
   delivered to `settle` cancels the attempt, awaits it, and re-raises; a cancelled attempt records
   `ABANDONED` and permits no second close. Rows exist for both inputs the review named — a cancelled
   `disconnect` with a parked close and a failing `super().disconnect` — and Worker 2 correctly
   identified that only the *raising* one had been pinned, which is not the input the finding was about,
   and closed the gap with `::test_a_teardown_cancelled_before_it_returns_still_settles_the_close`.
   Proof entries 9, 10 and 11 each fail 2 rows and each fails a *different* pair, so the three
   boundaries are separately pinned rather than jointly. Ready to tick.

This is also the round-specific check `worker-3.md` "Review-round duties" adds — *the fix is a real bound,
not a relabelled detection*. Named per box: (1) a declared non-UTF-8 / `utf-8-sig` / unknown charset on
a non-multipart body is now refused and was previously served `200`; (2) a chain listing the boundary
after a CSRF entry is now refused at startup and previously served requests, and a project's CSRF
subclass now runs where the stock class previously replaced it; (3) a foreign non-`int` position is now
routed to the bounded read and previously propagated an unrelated `500`; (4) a cancelled or raising
teardown now reaches settlement and previously skipped it. Nothing here is a widened error message or a
new log line.

### Public-surface check

`git diff ccfe17e1..HEAD -- django_strawberry_framework/__init__.py` is **empty**, and so is
`git diff -- django_strawberry_framework/__init__.py` for the working tree — `__all__` and the
re-export list are unchanged. Measured against spec **Decision 5**, not against "no API breakage":
this card's authorized break is the transport surface, and no new name was added to the package's
top-level export. The new consumer-facing name is reached only by its full dotted `MIDDLEWARE` path,
which matches `middleware/__init__.py`'s documented "deliberately NO re-export here"; the new module's
`__all__` is the single-name tuple `("GraphQLRequestBodyBoundaryMiddleware",)`, confirmed by reading.
Per the plan's `### Notes for Worker 1` item 6, `middleware/__init__.py` is correct as it stands and was
not "fixed".

### Static inspection helper

Run rather than read, because `BUILD.md` `### When to run the helper during build` requires it for a new
`.py` file of any size and this one is not a pure-class-definition module:

```shell
uv run python scripts/review_inspect.py django_strawberry_framework/middleware/request_body.py \
    --output-dir docs/shadow
```

Output: `docs/shadow/django_strawberry_framework__middleware__request_body.overview.md` and
`….stripped.py`. Regenerated rather than reading Worker 1's, so the overview matches `HEAD`.

- **Django / ORM markers: `None`.** The entry set is empty, so there is nothing to walk. Recorded
  explicitly rather than silently, because an empty section and an unread section look identical in an
  artifact.
- **Repeated string literals: 0. Control-flow hotspots: 0.** The usual DRY and complexity signals are
  genuinely absent; DRY item (f) is a duplicated *expression* across two files, which this
  single-file section structurally cannot see — noted so the integration pass does not treat the zero
  as coverage.
- **Calls of interest (5), walked, since they are where this module's decisions live.** `getattr()` at
  line 225 — High finding 1. `setattr()` at line 236 — fail-open item 2, justified. `isinstance()` at
  256 — the non-class `MIDDLEWARE` entry guard, without which `issubclass` raises `TypeError` on a
  function middleware; pinned by `_passthrough_middleware`. `issubclass()` at 258 and 260 — the
  by-class comparison, now pinned on both sides
  (`::test_a_boundary_subclass_listed_after_csrf_is_refused_at_startup` and `_RejectingCsrfMiddleware`).
- **Imports (12): one cross-folder direction worth flagging** — `from django_strawberry_framework.exceptions
  import ConfigurationError` is fine, but the *inbound* edge the section cannot show is
  `views.py` -> `middleware/request_body.py`. That is DRY item (a). No sibling imports from outside the
  documented boundary.

The helper was not run against `views.py`, `consumers.py` or `_request_body.py`: all three are
pre-existing files, none is under `optimizer/` or `types/`, and the plan records Worker 1's smoke-run
against `views.py` at pre-flight. `2701f41a` adds more than 30 lines of logic to `views.py`
(+135/-26), so per `BUILD.md` that file would qualify — the skip is recorded here with its reason: the
diff's new logic in `views.py` is two small methods whose whole surface is read line by line in the
per-finding sections above and in the fail-open walk, and Worker 1's overview for that file exists from
pre-flight.

### Hot-path budget

The plan assigns the post-hoc number to this pass, since no builder pass existed to owe it. Whether the
cost is acceptable is the maintainer's call and no worker's; the obligation discharged here is that the
number exists, is reproducible as recorded, and reaches them.

**Metric 1 — median wall-clock per request**, `Client().post` against a sync package mount with a small
JSON body, **400 iterations** after one discarded warm-up request (Django's `ClientHandler` builds the
middleware chain lazily on first request, so an un-warmed sample measures chain construction).
Both arms use stock `CsrfViewMiddleware` so both return `200` and the paths are comparable.
Snippet: `docs/builder/temp-tests/r1/test_r1_hotpath.py`, run as
`uv run pytest docs/builder/temp-tests/r1/test_r1_hotpath.py -s -o addopts="" --no-cov`.

| Run | `[CsrfViewMiddleware]` (before) | `[boundary, CsrfViewMiddleware]` (after) | delta |
| --- | --- | --- | --- |
| 1 | 333.02 us | 310.52 us | **-22.50 us** |
| 2 | 323.27 us | 319.58 us | **-3.69 us** |
| 3 | 312.10 us | 308.87 us | **-3.23 us** |
| 4 | 334.48 us | 316.23 us | **-18.25 us** |

Four independent 400-iteration medians rather than one reading. The delta's **sign is stable and
negative**: installing the middleware is not measurably more expensive and is slightly cheaper. The
plausible mechanism, stated so the number is interpretable rather than just recorded: the added work is
one `ContextVar` set + `reset`, one `getattr`, and one view instantiation, while the same request stops
paying for the view's own boundary run (the `_BOUNDARY_ENFORCED` stamp) and its `csrf_protect`
continuation collapses to the `csrf_processing_done` short-circuit. The magnitude is inside run-to-run
noise on a ~320 us request either way.

**Metric 2 — the charset guard's own micro-cost**, `timeit` over **200,000** calls of
`views.py::_canonicalizes_to_utf8("utf-8")`, the only new call on the common non-multipart path:
**0.0203 s total, 0.0974-0.1021 us per call** across the four runs. `codecs.lookup` is cached in
CPython, which is why it is a tenth of a microsecond rather than a lookup.

### Test-staleness sweep

Run independently, not against the diff's file list (`worker-3.md` "Test staleness"), because the tree
the diff missed is by definition the one that cannot appear in it. Neither `BUILD.md` shape applies
structurally — no example-model field set changed and no wire shape converted — but `2701f41a` changed a
*value every tree can read*: `view.csrf_exempt` is no longer `True` but an object.

`grep -rn 'csrf_exempt' tests examples --include='*.py'` returns 16 hits, each re-read:

- **`tests/test_views.py`** — 8 hits. The only assertions are
  `::test_the_view_callback_of_both_views_carries_the_csrf_exempt_mark #"assert bool(view.csrf_exempt) is True"`
  and `#"assert getattr(function, \"csrf_exempt\", False) is False"` on the two continuations. The first
  is re-pinned to `bool(...)` and does **not** pass merely because a truthy object is truthy: proof entry
  5 (`__bool__` -> `return False`) fails both its parametrizations, so it discriminates. The second is
  about the continuations, which carry no mark in either arrangement.
- **`tests/test_prove_failability.py`** and **`examples/fakeshop/config/urls.py`** — prose only.
- **`examples/fakeshop/test_query/test_transport_api.py`** — 7 hits, of which
  `::_carrying_the_packages_csrf_mark #"mark = view_class.as_view().csrf_exempt"` copies the object onto a
  probe mount. Green at `HEAD` (**69 passed**, re-run this pass) because fakeshop runs the fallback
  arrangement, and every surviving assertion there still asserts what it meant to: under the fallback the
  object is truthy, so `csrf_exempt` still "skips `process_view` only" (line 2416) and the mechanism prose
  is still accurate. **Two things about that file are now stale in prose rather than in assertions**, and
  both are R3's under M-A: its docstring's "*every Django view decorator carries it onward through
  `functools.wraps`*" is now describing **two** marks while the wrapper beside it copies one, and that
  wrapper is the very shape High finding 1 identifies. Recorded under `### Notes for Worker 1` for R3
  rather than edited, since M-A already assigns that file's re-pin to R3.

No other grep shape applies: `_BOUNDARY_MARKER` appears in exactly two test sites (an import and the
assertion above), and no schema-module list or app was added, so
`BUILD.md` `### Example-project schema changes` does not fire.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity (only when the slice touches docs, release metadata, KANBAN, or archived specs)

Not applicable; slice did not modify docs/release/KANBAN/archive surfaces. `2701f41a`'s one
`examples/fakeshop/apps/kanban/constants.py` line adds the new module to `TRACKED_FILE_PATHS` in correct
alphabetical position (read and confirmed), which is the tracked-path allowlist rather than a rendered
doc; the `docs/TREE.md` regenerate it enables is R3's (plan V5). `docs/feedback.md`'s own churn in the
range is the maintainer's and was neither read for review purposes beyond its four findings nor touched.

### Receipt of maintainer decision M-A

- **Received and applied as a constraint on this pass.** The coverage gap R1's planning pass escalated —
  `examples/fakeshop/config/settings.py` does not install `GraphQLRequestBodyBoundaryMiddleware`, so a
  shipped `__all__`-exported consumer-facing module has package-tier coverage only — is **decided**:
  install it in fakeshop immediately before `CsrfViewMiddleware`, keep the fallback arrangement covered
  live under an `override_settings(MIDDLEWARE=...)` suite, and enact it in **R3**. It is therefore **not
  raised as a finding here and not enacted here**. One thing this pass owes back to it, because the
  decision's cost accounting changes: M-A records that exactly one live row genuinely breaks
  (`::test_the_async_view_also_refuses_before_djangos_parser_runs`, "whose probe wrapper copies
  `csrf_exempt` but not the boundary marker, so the parse would beat the boundary"). That is the same
  mechanism as High finding 1, now measured — so once High finding 1 is fixed as recommended, that row
  does **not** break under the shipped chain and moving it to a fallback-override chain may no longer be
  required. R3 should re-measure after the fix rather than enacting M-A's re-pin from the pre-fix
  measurement.

### What looks solid

- **The ordering was moved to the only place that can own it, and the audit that protects it is a
  startup raise rather than a documented requirement.** A chain that looks correct and is not fails at
  chain-build time, compared by resolved class so a subclass of either side is recognized — and Worker 2
  found and closed the fact that the boundary side of that comparison was unexercised.
- **The withdrawable exemption is a genuinely better answer than the review's own prescription.** It
  keeps every un-edited deployment byte-identical while giving an edited one its configured class, and
  the two arrangements are pinned against each other in both directions rather than one being asserted
  and the other assumed.
- **`_measured_remaining`'s new gate is the corrected shape, not a re-spelling of the old one.** It
  refuses the *answer* (a position that is not exactly an `int`) rather than enumerating input spellings,
  which is exactly the lesson `BUILD.md` `### Fail-open shapes` draws from the `max(end - position, 0)`
  incident, and `type(...) is int` rather than `isinstance` closes the `int`-subclass-with-overridden-
  operators route an `isinstance` check leaves open.
- **`ba66ab49` retracted a ruling instead of working around it.** The old class docstring argued that a
  cancelled attempt resting in `CLOSING` was "the ruling rather than an omission"; the new one separates
  the mid-connection question (shield, do not touch the attempt) from the teardown question (end it), and
  the separation is what makes both correct. The two shields are pinned by disjoint row sets.
- **Worker 2's judgement on the two weakly-pinned verdicts was right in substance, not just in
  procedure.** Both were closed with rows rather than routed as exceptions, and in both cases the missing
  row pinned the input the finding was actually about — the *cancelled* teardown for the `finally`, and
  the two startup contracts the audit's own docstring states. The plan's reasoning that no second row
  could exist for entry 6 was wrong in a way worth noticing: no *behavioural* row could, but two further
  *startup* rows could.
- **Every refusal on this boundary carries the same reason string**, so a caller cannot attribute a
  rejection by message — and the middleware's own response construction is byte-identical to upstream's,
  so it cannot be attributed by wire shape either.

### Temp test verification

Files used, all under `docs/builder/temp-tests/r1/` (gitignored):

- **`test_r1_probes.py`** — the three probes the plan names plus two controls and the regression half.
  Results: `test_marker_loss_lets_multipartparser_run_on_an_over_limit_body[/wrapped-capped/]` **fails**
  (1 real `MultiPartParser.parse` on an over-limit body) while `[/marked-capped/]` passes with 0, and
  `test_without_the_boundary_middleware_no_parse_precedes_the_cap` passes for **both** mounts — the three
  together are the proof for High finding 1 and for its being a regression rather than a pre-existing
  hole. `test_boundary_installed_with_no_csrf_middleware_still_checks_csrf` **passes** — the Medium
  finding is a missing row, not a defect.
  `test_a_third_party_cancellation_of_the_attempt_masks_the_callers_exception` **fails**, demonstrating
  the masking, which is nonetheless out of contract (P2b open question 1).
  **Disposition: noted for promotion.** The `MultiPartParser.parse`-counting rows and the boundary-only-chain
  row are the permanent rows High finding 1 and the Medium finding require; the fixing pass writes them
  into `tests/test_views.py` with the assertions inverted to the fixed behaviour. The third-party-cancellation
  probe is **not** promoted — it pins a shape no supported seam can produce, so a permanent row would
  manufacture confidence; its finding is a spec sentence for R2 instead.
- **`test_r1_hotpath.py`** — the hot-path measurement snippet. **Disposition: kept as the reproducible
  record behind `### Hot-path budget`; not promoted** (it is a measurement, not an assertion — it asserts
  nothing about whether the numbers are good, which is the maintainer's call).
- **`w3-rerun.md` / `w3-rerun.log`** — this pass's independent proof re-run record.

Two fixture traps were hit and are worth recording, because both would have produced a wrong answer that
read as clean: a non-enforcing `Client()` makes `CsrfViewMiddleware.process_view` short-circuit on
`_dont_enforce_csrf_checks` and never read `request.POST` (so a parse-ordering probe measures nothing),
and an enforcing client *without a well-formed `csrftoken` cookie* is rejected on
`REASON_NO_CSRF_COOKIE` before the POST read (same result). Only an enforcing client **with** a
well-formed cookie reaches `_check_token`'s `request.POST` access. That is the same class of fixture
defect the rationale records against the original spec-046 ordering row.

### Notes for Worker 1 (spec reconciliation)

Everything Worker 1 and Worker 2 recorded stands; these are additions, and nothing here is fixed in R1.

1. **`Escalated:` DRY item (a) — where the marker constants, the ContextVar and the exemption object
   live.** A package-layering contract call, not a defect, so it is escalated rather than held at
   `revision-needed` (`worker-3.md` `### The existence challenge`). Three resolution paths, with what each
   costs: **(i)** keep them in `middleware/request_body.py` and accept that `views.py` imports from the
   `middleware/` subpackage — zero churn, and the module docstring already argues the direction, but the
   inversion is real and every view import pulls in `django.middleware.csrf`; **(ii)** move them into
   `_request_body.py` (Worker 1's proposal) — removes the inversion, but puts CSRF-ordering state into the
   module whose docstring scopes it to stream measurement; **(iii)** a third private module owning only
   the marks, the ContextVar and the exemption class — removes the inversion with no responsibility
   mismatch, at the cost of one more file and one more import line in each of the two modules. My
   recommendation is (iii), and the decision is cheapest to take **in the same pass as High finding 1**,
   because that fix changes what the ContextVar holds. The existence question underneath it is already
   answered and needs no decision: the class must exist, because Django reads truthiness.
2. **`Escalated:` the duplicated-boundary-entry over-refusal is a contract sentence, not a defect.** A
   chain `[boundary, csrf, boundary]` is refused, because the audit keeps the *last* boundary index and
   the *first* CSRF index. The refusal is in the safe direction and I agree with Worker 2's decision not
   to freeze an answer by pinning it. R2's Decision-18 rewrite should say which it is — strict on
   purpose, or corrected to the first boundary entry — and only then should a row pin it. My read: strict
   on purpose is defensible and cheaper to explain than "the earliest boundary wins".
3. **For R2 — the rationale's Decision 18 entry now contradicts `HEAD`, and in the most load-bearing way
   possible.** Its rejected-alternatives list records "*A narrow package middleware placed before
   `CsrfViewMiddleware`, plus a system check that detects missing or wrong ordering* (the review's own
   first suggestion). **Rejected**: it adds a required deployment entry …" — which is, in substance, what
   `2701f41a` shipped. Two things the reconciliation needs beyond a status flip: the reason the
   alternative lost ("a `MIDDLEWARE` line every consumer must add") is *answered* by the withdrawable
   exemption, which makes the entry optional rather than required, and that is the sentence that turns a
   reversal into a resolution; and what shipped is a **startup raise from `__init__`**, not a Django
   system check, which is a different mechanism from the one the entry rejected. Treated as an R2 note
   and not a code finding, per this pass's contract.
4. **For R2 — one premise currently living only in a code comment deserves a spec sentence.**
   `consumers.py::_ConnectionRevocation._attempt_close`'s new docstring asserts "only the connection's
   final teardown cancels this task", and the whole correctness of `settle`'s cancel-and-re-raise arm
   rests on it (see P2b open question 1 above: if a third party could cancel the attempt, `settle` would
   propagate a `CancelledError` in place of a caller's exception — measured). It is true at `HEAD` and
   nothing enforces it but the class being private. Decision 16 should state it as a contract.
5. **For R3 — M-A's re-pin cost should be re-measured after High finding 1 is fixed**, not enacted from
   the pre-fix measurement. See `### Receipt of maintainer decision M-A` above.
6. **For R3 — `examples/fakeshop/test_query/test_transport_api.py::_carrying_the_packages_csrf_mark` is
   stale in prose.** Its docstring describes one mark and "every Django view decorator carries it onward
   through `functools.wraps`" where there are now two, and the wrapper itself copies one. It is the shape
   High finding 1 names. Already in R3's write set under M-A; recorded so the prose fix is not missed
   alongside the row moves.
7. **Floor-fact correction for whoever reads this plan next:** the plan's floor question 4 assumes "the
   floor's asgiref is older than the one the 324-row baseline ran under". Measured, it is **newer**
   (3.12.1 at the floor, 3.11.1 in the shared `.venv`). The question was still answered, by naming
   `_restore_context` and verifying it in both, but a later pass should not rely on the floor venv being
   uniformly older than `.venv`.
8. **Not a finding, recorded so it is not re-derived:** `_measured_remaining`'s pre-existing
   "(`ASGIRequest`'s spool and `WSGIRequest`'s `LimitedStream` both measure honestly on both supported
   interpreters)" is imprecise for the same reason Low finding 1 corrected the sentence above it —
   `LimitedStream` declines to measure rather than measuring honestly. Not in this diff, so left
   untouched by the carve-out.

### Review outcome

`revision-needed`.

One **High** finding — a measured security regression: with the middleware installed, a callback that
kept `csrf_exempt` but lost `_BOUNDARY_MARKER` has the exemption withdrawn and the boundary un-run, and
Django's `MultiPartParser` runs on an over-limit multipart body that the same mount refuses before any
parse on a chain without the middleware. It is the fail-open shape Worker 1's plan named as the live
suspect; what this pass adds is reachability, a repository-resident instance of the shape, and a
mechanical parse-counter proof.

One **Medium** finding — no permanent row drives a request through the boundary-with-no-CSRF chain that
`_require_boundary_before_csrf` deliberately admits; the behaviour is correct, so it is a missing row.

Three **Low** findings, one of which (the falsified `LimitedStream` docstring claim) is corrected in this
pass under the floor-verification carve-out; the other two (the unguarded `view_class` read, the
HEAD/GET method-scope inconsistency) are one-line changes for the fixing pass and for R2 respectively.
One new **DRY** finding, item (f), to land with the same pass.

Everything else audits clean: eleven proof records audited and **all eleven independently re-run with
set-equal node-id sets**, no boundary weakly pinned, no collection errors, every restore proved by byte
comparison and the tree re-proved byte-identical to `HEAD` afterwards; the floor run green at 327 rows
with all five floor questions answered by execution; all nine fail-open shapes read, eight benign and
one filed; all five non-weakening checks confirmed, with the single qualification that non-weakening
check 3's *ordering* half is what High finding 1 breaks; the public-surface check clean against
Decision 5; and the hot-path number captured, reproducible, and negative.

Per the plan's `### Boundary count and the split question`, the confirmed defects fall in **one**
subsystem pair (`views.py` + `middleware/request_body.py`) whose tests share `tests/test_views.py`, so a
single builder cohort is correct and nothing needs to run concurrently.

---

## Plan (Worker 1, pass 2 — revision)

The round's audit is complete and its verdict stands: one High, one Medium, three Low, one new DRY
item. This section is the **contract for the fixing pass** (Worker 2), and it exists as a second
plan rather than an edit to the first because the first plan's subject was a review and this one's
subject is a diff. Nothing above this heading is edited.

Ownership for this pass is `views.py`, `middleware/request_body.py`, one **new** private module,
`tests/test_views.py`, `docs/builder/temp-tests/r1/**`, and — see
`### Write-set corrections Worker 0 must record` — `examples/fakeshop/apps/kanban/constants.py`.
`consumers.py` and `tests/test_routers.py` are **not** touched: every `consumers.py` finding audited
clean and its three proofs are untouched by this pass. The spec and the rationale stay R2's; the
standing docs stay R3's; `docs/feedback.md` is never edited, annotated, or named in code.

### Architectural decision A-1: where the boundary-ordering marks live

**Decided: a third private module, `django_strawberry_framework/_boundary_ordering.py`**, owning the
two attribute-name constants, the ContextVar, `_CsrfOrderingExemption`, and the shared
`_CSRF_ORDERING_EXEMPTION` instance. After the move `views.py` imports it and
`middleware/request_body.py` imports it, and **neither of those two imports the other**.

This is DRY item (a)'s resolution and it is mine to make (`worker-0.md` `## Per-slice dispatch`
step 6a). It is **not consumer-visible** and therefore needs no maintainer escalation: the module is
private, `middleware/request_body.py`'s `__all__` stays the single-name tuple
`("GraphQLRequestBodyBoundaryMiddleware",)`, the documented `MIDDLEWARE` string
(`django_strawberry_framework.middleware.request_body.GraphQLRequestBodyBoundaryMiddleware`) is
unchanged, `django_strawberry_framework/__init__.py` is untouched, and the two stamped attribute
*string values* (`"graphql_request_body_boundary"`,
`"graphql_request_body_boundary_enforced"`) are carried over verbatim so nothing a wrapper or a
test reads by name changes.

Worker 3's existence challenge is **not re-opened**: `_CsrfOrderingExemption` must exist, because
Django consumes the mark as `getattr(callback, "csrf_exempt", False)` for truthiness at request time
(confirmed at the floor, its floor question 3), and a one-method `__bool__` class with one shared
instance is the minimal shape that read site permits. This decision is only about *where*.

**Why (iii) and not (i), the status quo.** Two reasons, and neither is the one Worker 3 costed:

- The import cost Worker 3 attributes to (i) **is not real, measured this pass.** `views.py` imports
  `django.views.decorators.csrf` on its own account (for `csrf_protect`), and that module's first
  lines are `from django.middleware.csrf import CsrfViewMiddleware, get_token` — verified by
  execution: `python -c "import django.views.decorators.csrf, sys; print('django.middleware.csrf' in
  sys.modules, 'django.utils.module_loading' in sys.modules)"` prints `True True`. So *both* modules
  Worker 3 names are already imported by `views.py` whatever this decision is, and the incremental
  import cost of (i) is **two package module objects**, not two Django subsystems: measured with a
  `sys.modules` difference around `import django_strawberry_framework.views` after `django.setup()`,
  the package modules added are exactly `_request_body`, `middleware`, `middleware.request_body`,
  `views`. The real argument had to be found elsewhere.
- **(i) is the sole cause of a DRY consolidation Worker 3 had to reject.** Its item (c) concluded "no
  shared recognizer" because `middleware/request_body.py` "must not import the view classes at all,
  **because `views.py` imports it** — the one-way dependency is the constraint." That constraint is
  manufactured by the placement, not by the problem: under (iii) the middleware module is free to
  import `views.py`, and whether to share a recognizer with
  `middleware/debug_toolbar.py::DebugToolbarMiddleware.process_view` becomes a decidable question
  instead of a foreclosed one. A placement that forecloses a consolidation is a placement that costs
  DRY, which is the axis `BUILD.md` puts first.
- Secondary, and the reason the inversion reads as one: `middleware/__init__.py` documents the
  subpackage as leaves whose *import is the deployment's opt-in* ("there is deliberately NO
  re-export here - importing the leaf module is the soft-dependency opt-in"). Under (i) a core view
  module imports one of those leaves unconditionally, so that sentence is true of `debug_toolbar.py`
  and false of `request_body.py`. Under (iii) it is true of both again.

**Rejected: (ii) move them into `_request_body.py`** — my own pass-1 suggestion, and Worker 3's
objection is correct. That module's docstring scopes it to one thing ("the only file in the package
that names `HttpRequest._stream`, `HttpRequest._body`, or `HttpRequest._read_started`", "the one
place the package touches Django's private request-body internals"), and its whole value is that the
private-Django compatibility surface is auditable from one file. CSRF-ordering state is not stream
measurement, and adding it dilutes exactly the property the file exists to have.

**Rejected: (i) status quo** — for the two reasons above. Recorded so it is not re-proposed on the
grounds that it is zero-churn: it is zero-churn and it keeps a manufactured import constraint.

**Rejected: (iv) invert — put the marks in `views.py` and have the middleware import them.** Not on
Worker 3's list; considered because it also removes the inversion, at zero new files. It loses
because it puts CSRF-ordering ContextVar machinery into the package's core, largest, most-read view
module, and because the middleware would then import `strawberry.django.views` at chain-build time
(before the URLconf is imported) for three constants. It also does not remove the split-narrative
cost that (iii) is charged with, so it pays (iii)'s cost without (iii)'s benefit.

**The costs of (iii), stated rather than discovered later.** One new file (a module docstring, ~60
lines); one line in `docs/TREE.md`, which R3 regenerates, so no doc pass is created and no spec
sentence changes; one regenerate of `examples/fakeshop/apps/kanban/constants.py`; three import
re-points in `tests/test_views.py`. And one real readability cost: `middleware/request_body.py`'s
module docstring argues at length why the exemption is a lazily-evaluated object, while the object
moves out. **That is answered by splitting the prose along the same seam as the code, not by leaving
it behind:** `_boundary_ordering.py` owns *what each mark means and who may write it*, and
`middleware/request_body.py` keeps *why the chain is the right owner of the ordering* plus a pointer.
Step 2 below makes that a requirement rather than a hope.

One consequence to note in passing, because it is the strongest argument that the seam is real: the
protocol is already **bidirectional**. `views.py::_RequestBodyBoundaryMixin.as_view` writes
`_BOUNDARY_MARKER` and `middleware/request_body.py` reads it; `middleware/request_body.py` writes
`_BOUNDARY_ENFORCED` and `views.py::_RequestBodyBoundaryMixin._enforce_request_boundary_once` reads
it. Two-way shared state between two modules with a one-way import is what a protocol module is for.

### Architectural decision A-2: the High fix's predicate — accepted, with the answer named

Worker 3's recommended shape is **accepted as the shape**, on judgement rather than transcription
(`BUILD.md` `## Review rounds`: a prescribed remediation is a hypothesis). What follows is the
answer being guarded, the predicate, and the state enumeration that shows the predicate guards the
answer rather than one spelling of the incoherent input (`BUILD.md` `### Fail-open shapes`).

**The answer being guarded.** Not "did the callback keep its marker" and not "is the middleware
installed", both of which are input spellings. The answer is: *has the body boundary already run for
**this** request, so that the callback's CSRF exemption may be withdrawn?* Only an established "yes"
may withdraw the exemption; every other state — including every state nobody has thought of — must
answer "no", which is the **fallback arrangement** (exemption truthy, the chain's CSRF middleware
skips the callback, the view runs the boundary itself and re-enters CSRF through `csrf_protect`).
That degrades the CSRF *class* to Django's stock implementation, which is the pre-`2701f41a`
behaviour; the shipped defect degrades the *ordering*, and the ordering is what the `413` depends on.

**The predicate**, in `_boundary_ordering.py::_CsrfOrderingExemption.__bool__`:

```python
request = _boundary_middleware_request.get()
return request is None or not getattr(request, _BOUNDARY_ENFORCED, False)
```

with `__call__` / `__acall__` setting `_boundary_middleware_request` to the **request object** (a
`ContextVar[HttpRequest | None]` with `default=None`), set and reset around the downstream call
exactly as today.

Two clauses, deliberately, and **not** collapsed into the shorter
`not getattr(_boundary_middleware_request.get(), _BOUNDARY_ENFORCED, False)`: that one-liner leans on
`getattr(None, ...)`'s default to fold "no chain" and "no stamp" into one expression, which is the
`getattr`-default-standing-in-for-a-meaningful-absence shape from `BUILD.md`'s catalogue even where
both absences happen to want the same answer. Two named cases stay readable when a third appears.

**Reachable states, enumerated. Every row that is not an established "yes" lands on the fallback.**

| State | `_boundary_middleware_request` | `_BOUNDARY_ENFORCED` on the request | `__bool__` | Arrangement |
| --- | --- | --- | --- | --- |
| Middleware not installed | unset (`None`) | absent | `True` | fallback: view orders, stock class checks |
| Installed, marked callback, boundary ran | the request | `True` | `False` | configured class checks, behind the boundary |
| Installed, marker-less callback | the request | absent | `True` | **fallback** — the fix |
| Installed, callback with the marker but no usable `view_class` / `view_initkwargs` | the request | absent | `True` | fallback (see step 2's recognizer) |
| Installed, non-package view | the request | absent | never consulted (`csrf_exempt` absent) | Django's own default |
| Installed, boundary refused the request | the request | absent | never consulted (`process_view` returned a response) | refused before CSRF |
| Two adjacent boundary entries | the request (token-nested set/reset) | `True` after the first | `False` | configured class checks |
| `[boundary, csrf, boundary]` | n/a | n/a | n/a | refused at startup (contract question routed to R2) |
| A middleware that passes a *different* request object downstream | the outer request | absent on it | `True` | fallback |

The ordering that makes row 2 possible is guaranteed, not assumed: Django's `load_middleware`
iterates `reversed(settings.MIDDLEWARE)` and `insert(0, ...)`s each `process_view`, so
`_view_middleware` runs in `MIDDLEWARE` order, and `_require_boundary_before_csrf` refuses at startup
any chain whose CSRF entry precedes ours. So the stamp is always written before the exemption is
read, in every chain that is allowed to serve.

**Propagation.** The read direction is the one the shipped async rows already prove and Worker 3
confirmed at the floor (its floor question 4): `SyncToAsync` copies the caller's context into the
executor thread, so a var set on the loop by `__acall__` is visible to the `sync_to_async`-adapted
`CsrfViewMiddleware.process_view`. The stamp needs no context propagation at all — it is an attribute
on the shared request object. **This is why the shape was chosen over the obvious alternative**
(`process_view` setting a bool ContextVar after enforcing), which would depend on the *write-back*
direction through `asgiref.sync._restore_context` and would need token bookkeeping across two hooks
for the reset. Rejected on both counts.

**Rejected alternative: broaden recognition instead** — recognize a package callback by
`issubclass(getattr(view_func, "view_class", None), _RequestBodyBoundaryMixin)`, which the
repository-resident wrapper (`examples/fakeshop/test_query/test_transport_api.py
::_carrying_the_packages_csrf_mark`, which copies `view_class` and `view_initkwargs`) would satisfy.
Rejected as **the** fix: it enlarges the recognized set without guarding the answer, so a wrapper
that copies only `csrf_exempt` — the exact shape `views.py::_RequestBodyBoundaryMixin.as_view`'s
docstring names as live — still gets the exemption withdrawn with the boundary un-run. A guard
written against a set of recognizable inputs is a guess; this one is also strictly larger in blast
radius (it makes the middleware import the view classes and re-opens DRY (c)). It stays available as
a *separate* future question, which A-1 is what unblocks.

### DRY analysis

**Helper inventory checked.** `docs/shadow/helper-inventory.md` (1,696 lines, whole package) is
**reused rather than regenerated, and it is current**: `git status --short
django_strawberry_framework/` reports exactly one modified file, `_request_body.py`, whose change
Worker 3 proved docstring-only by a docstring-stripped `ast.dump` comparison against `HEAD`, so no
symbol, signature, or module in the index moved. Shapes searched this pass: `charset`, `declared`,
`encoding`, `exempt`, `recogni`, `view_class`, `process_view`, `contextvar`, `marker`, `protocol`.
Relevant candidates: `views.py::_canonicalizes_to_utf8`, `::_form_encoding_is_utf8`,
`::_enforce_body_charset_declaration`, `::_is_multipart_form_post`,
`middleware/debug_toolbar.py::DebugToolbarMiddleware.process_view`,
`middleware/request_body.py::_CsrfOrderingExemption`. **No existing helper answers "is the declared
charset unhonourable?" or "is this callback one whose boundary I can run?"** — those are the two new
helpers below, and no candidate module already owns an inter-module mark protocol.

**Existing patterns reused.**

- `views.py::_canonicalizes_to_utf8` stays the single codec authority; DRY (f)'s helper wraps the
  declaration *read* around it and invents no second rule.
- `views.py::_is_multipart_form_post` stays the single multipart discriminator; the charset guard's
  scope is untouched by this pass (Low (c) is R2's — see `### Routing confirmations`).
- The package's own ContextVar idiom. Measured: **ten** `ContextVar(` declarations across six modules
  (`permissions.py`, `optimizer/extension.py` x4, `optimizer/selections.py`,
  `optimizer/nested_fetch.py`, `utils/write_transaction.py` x2, `middleware/request_body.py`), and
  `_boundary_middleware_active` is the only one declared `ContextVar[bool]`; every other module-level
  declaration is `X | None` with `default=None`. So carrying the request is a move *onto* the
  package's established shape, not away from it.
- The set-token / reset-in-`finally` idiom and the sync/async twin bodies are unchanged, and pass 1's
  decisions (d) and (e) stand: no third copy appears, so no extraction is triggered.

**New helpers justified — exactly two, both single-responsibility, both with two call sites or a
named answer.**

1. `views.py::_declared_charset_is_unhonourable(request) -> bool` (DRY item (f)). Single
   responsibility: *what the client declared about the body's charset, and whether this endpoint will
   honour it.* Call sites: `views.py::_form_encoding_is_utf8` (condition 1) and
   `views.py::_enforce_body_charset_declaration`. Worker 3's proposed name is adopted. Body is the
   two lines both sites carry today, character-for-character, `(request.content_params or {})`
   included — the extraction is behaviour-preserving by construction and must be provable as such
   (step 3).
2. `middleware/request_body.py::_package_view_instance(view_func)` (Low item (b)). Single
   responsibility: *the instance of the package view this callback mounts, or `None` when there is no
   such instance to build.* One call site, and the reason it is a named function rather than four
   lines inside `process_view` is that it is the answer the hook branches on, and a proof needs a
   symbol to anchor to.

**Duplication risk this plan prevents.**

- A naive High fix writes the "has the boundary run for this request?" test twice — once in
  `__bool__` and once in `_enforce_request_boundary_once`. It stays **one** fact, the
  `_BOUNDARY_ENFORCED` stamp, read by both from the one module that defines what it means.
- A naive Low (b) fix adds a second `if` branch beside the marker test, giving `process_view` two
  recognition predicates that can disagree. Folded into one.
- A naive DRY (f) fix inlines a third copy of the declaration read into the new helper's caller.
  Prevented by naming the two call sites above.
- A naive placement move copies the constants instead of moving them. `_BOUNDARY_MARKER` /
  `_BOUNDARY_ENFORCED` must exist in exactly one module afterwards, and step 5's grep proves it.

**Decided and not delegated:** no shared "is this one of our views?" recognizer is introduced with
`middleware/debug_toolbar.py` in this pass. A-1 removes the import constraint that forced Worker 3's
(c) verdict, but acting on that in the same pass as a security fix would enlarge the diff for a
readability gain; the condition that justifies revisiting it is a **third** middleware needing the
same recognition, or `debug_toolbar` and `request_body` needing to agree on the answer for one
callback.

### Implementation steps

Ordered, and the order is load-bearing in two places (step 0 before any edit; step 10 after the file
is final). Every citation is symbol-qualified, so nothing needs re-pinning against a shifted file.

0. **Capture the hot-path "before" numbers first, on the unmodified tree**, per
   `### Hot-path budget`. This is the only chance: the "before" arm is `HEAD`.
1. **Create `django_strawberry_framework/_boundary_ordering.py`.** Moves in, from
   `middleware/request_body.py`: `_BOUNDARY_MARKER` and `_BOUNDARY_ENFORCED` (string values
   verbatim), the ContextVar — **renamed** to `_boundary_middleware_request`, typed
   `ContextVar[HttpRequest | None]`, ContextVar name string
   `"django_strawberry_framework_boundary_middleware_request"`, `default=None` — plus
   `_CsrfOrderingExemption` (with A-2's predicate) and the shared `_CSRF_ORDERING_EXEMPTION`
   instance. Runtime imports: `contextvars` only; `HttpRequest` under `TYPE_CHECKING` with
   `from __future__ import annotations`, so the module stays standard-library-only at runtime and
   cannot participate in an import cycle with anything. No `__all__` (every name is private). The
   module docstring owns the **protocol**: what each mark means, that `views.py` writes the marker
   and reads the stamp while the boundary middleware reads the marker and writes the stamp, and the
   invariant the exemption rests on — *the stamp is written only by a chain participant that has
   already run the boundary for that request, so an absent stamp means the view still owns the
   ordering*. Cite `spec-046` Decision 18 as the design pointer; carry **no** process provenance (no
   round, finding, severity, or review-document references — that ban is standing).
2. **`middleware/request_body.py`.** (a) Delete the four moved definitions and import the three names
   it still needs (`_BOUNDARY_ENFORCED`, `_BOUNDARY_MARKER`, `_boundary_middleware_request`) from
   `_boundary_ordering`; `__all__` unchanged. (b) Add `_package_view_instance(view_func)`: return
   `None` unless `getattr(view_func, _BOUNDARY_MARKER, False)` **and** `view_class` is a class and
   `view_initkwargs` is a `dict`, both obtained with `getattr(..., None)`; otherwise return
   `view_class(**view_initkwargs)`. No `or {}` / `or ()` fallback anywhere in it — an absent
   attribute means "not a callback whose boundary I can run", which is a `None`, not a default.
   (c) `process_view` becomes `view = _package_view_instance(view_func)` / `if view is None: return
   None` / the existing `try` / `except HTTPException` / `setattr(request, _BOUNDARY_ENFORCED, True)`
   unchanged. (d) Module docstring: keep the whole "why a middleware entry is the right owner"
   argument and the ordering-audit paragraph; **rewrite** the paragraph beginning "The exemption is a
   lazily-evaluated object rather than the usual `True`" so it no longer says "Where this middleware
   is installed the exemption is `False`" — the exemption is false for a request whose boundary this
   middleware has **run**, and a callback it does not recognize keeps the fallback arrangement
   intact. The sentence "Both arrangements enforce CSRF and both enforce the cap" becomes true again
   and stays; point at `_boundary_ordering.py` for the object.
3. **`views.py`.** (a) Re-point the three-name import from `middleware.request_body` to
   `_boundary_ordering`; nothing else about `as_view` or `_enforce_request_boundary_once` changes.
   (b) Add `_declared_charset_is_unhonourable(request)` beside `_form_encoding_is_utf8` and call it
   from both sites (DRY (f)). (c) `_RequestBodyBoundaryMixin._enforce_request_boundary`'s docstring:
   the "or" limb is true again after the fix, and must also be *accurate* — the second limb's "where
   it is not installed" is narrower than the fact that now holds, so it must read as "or, where the
   chain did not run it for this request, because the package view's callback is exempt from that
   middleware and re-enters CSRF after this boundary". (d) `_CsrfOrderingExemption`'s own class
   docstring (now in `_boundary_ordering.py`) says *needed for this request* rather than *needed on
   this chain*; its closing claim "It is never a bypass in either state" stays and is now true in
   every state of the A-2 table. These are **the two corrections the fix makes true again**, named by
   symbol: `views.py::_RequestBodyBoundaryMixin._enforce_request_boundary` and
   `_boundary_ordering.py::_CsrfOrderingExemption`; the middleware module docstring in step 2(d) is a
   third, and it is required too — Worker 3's High finding names all three as currently false.
4. **`tests/test_views.py`** — see `### Test additions / updates`. Re-point imports, re-pin the one
   row the new predicate falsifies, add the High / Medium / Low(b) rows.
5. **Prove the move mechanically, not in prose.** `grep -c -F` each of `_BOUNDARY_MARKER =`,
   `_BOUNDARY_ENFORCED =`, `class _CsrfOrderingExemption`, `_CSRF_ORDERING_EXEMPTION =` across
   `django_strawberry_framework/` and record **1** for each; and confirm
   `grep -rn 'middleware.request_body import' django_strawberry_framework/` returns nothing and
   `grep -rn 'import views' django_strawberry_framework/middleware/` returns nothing, i.e. neither
   module imports the other. Record the commands and outputs in the build report.
6. `uv run ruff format` and `uv run ruff check --fix` **scoped to this pass's files**, then
   `uv run python scripts/check_trailing_commas.py --check` on the same list (the build gate's ruff
   step does not cover the source-layout hook that gates commits), then `git status --short` — every
   modified path must be in `### Files touched`; anything else is a stop-and-report, never a revert.
7. **Failability proofs**, per `### Failability proofs (pass 2)`.
8. **Hot-path "after" numbers**, same snippet, same iteration counts, per `### Hot-path budget`.
9. **Floor verification**, per `### Floor verification scope`. This pass owns it.
10. **Kanban tracked-path constants, last, after the new module's content is final.**
    `examples/fakeshop/apps/kanban/constants.py` is script-rendered from `git ls-files` — never
    hand-edited — and an untracked file is invisible to it. So: `git add
    django_strawberry_framework/_boundary_ordering.py` (that one path only; never `git add -A`, and
    never commit), then `uv run python scripts/build_kanban_tracked_path_constants.py`, then confirm
    the diff is exactly one added `TRACKED_FILE_PATHS` line in alphabetical position. Doing this
    inside the pass is what stops the pre-commit hook regenerating it at commit time, which is a
    recorded failure mode that stash-conflicts and rolls back the whole commit.
11. Focused runs (no `--cov*` flag ever; `--no-cov` is required):
    `uv run pytest tests/test_views.py --no-cov` and `uv run pytest tests/test_routers.py --no-cov`.
    `tests/test_routers.py` is run despite being untouched, because `_boundary_ordering.py` changes
    the package's import graph.

Not changed by this pass, decided rather than left silent: `process_view` keeps calling
`view._enforce_request_boundary` rather than `::_enforce_request_boundary_once`. Switching it would
make two adjacent boundary entries measure once instead of twice, but the duplicated-entry contract
is the question Worker 3 routed to R2 (over-refusal versus strict-on-purpose), and changing the
behaviour here would freeze half of an answer R2 owns. It is a cost (a second probe on a chain nobody
meant to write), not a correctness break.

### Test additions / updates

All in `tests/test_views.py`. Package-tier placement is correct and unchanged: a misordered chain, a
marker-dropping wrapper mount, and a marked-but-classless callback are not request shapes any live
fakeshop query can reach (`AGENTS.md` #10). Every row drives the real handler through
`tests/test_views.py::_chain` with `ROOT_URLCONF` pointed at the test module, on both transports via
`::_post`, which builds a fresh `Client` / `AsyncClient` per call — required, because
`ClientHandler.__call__` builds the middleware chain lazily on first request and a reused client
keeps a stale chain.

1. **Re-point the imports.** `_BOUNDARY_ENFORCED` / `_BOUNDARY_MARKER` (module-level, currently from
   `django_strawberry_framework.middleware.request_body`) and the function-local
   `_CSRF_ORDERING_EXEMPTION` inside
   `::test_the_async_chain_resets_the_ordering_mark_around_the_downstream_call` now come from
   `django_strawberry_framework._boundary_ordering`. `GraphQLRequestBodyBoundaryMiddleware` and
   `_BOUNDARY_MIDDLEWARE_PATH` keep their current source and value.
2. **Re-pin `::test_the_async_chain_resets_the_ordering_mark_around_the_downstream_call` — the one
   row the new predicate falsifies, and it must be strengthened, never weakened.** It asserts today
   `bool(_CSRF_ORDERING_EXEMPTION) is False` inside a downstream call driven from a bare
   `RequestFactory().get("/graphql/")`, which under A-2 is `True`, because that request carries no
   stamp. The row's intent — the mark is request-scoped, set around the downstream call, and reset
   even when the chain raised — survives intact and gains a half: inside `downstream`, assert `True`
   **before** stamping (the chain is active but the boundary has not run, so the view still owns the
   ordering), then `setattr(request, _BOUNDARY_ENFORCED, True)` exactly as `process_view` does and
   assert `False`, then raise; after the `pytest.raises`, assert `True` again (the reset). That pins
   both clauses of the predicate and the reset in one row. Never soften it to
   `bool(...) in (True, False)` or drop a half to make it pass.
3. **The High fix's permanent rows, promoted from
   `docs/builder/temp-tests/r1/test_r1_probes.py`** with the assertions inverted to the fixed
   behaviour. Promote `::_wrapper_copying_only_csrf_exempt` and the `/wrapped-capped/` +
   `/wrapped-async-capped/` mounts into the test module's `urlpatterns`, and promote
   `::_counting_multipart_parses`. Required assertions, both transports: on `_ORDERED_CHAIN`, an
   over-limit multipart to the wrapped mount answers **413**, `MultiPartParser.parse` is called
   **0** times, and `_RejectingCsrfMiddleware.calls == []`; and an under-limit request to the wrapped
   mount still reaches a complete CSRF check. Keep `::test_the_unwrapped_mount_still_orders_correctly`'s
   control (the stamped mount is unchanged) and the regression half
   (`::test_without_the_boundary_middleware_no_parse_precedes_the_cap`, both mounts, 0 parses) so the
   row set says *installing the middleware no longer changes the answer for either mount* — which is
   the property the finding is about. The parse counter is the primary witness; the CSRF call log is
   the secondary one, because it depends on the stand-in class reading `request.POST` at all.
4. **The Medium finding's permanent row**, promoted from
   `::test_boundary_installed_with_no_csrf_middleware_still_checks_csrf`: a request through
   `_chain([_BOUNDARY_MIDDLEWARE_PATH])` — the disjunct `_require_boundary_before_csrf` deliberately
   admits — on **both transports** and **both client strictnesses**: a non-enforcing client gets
   `200`, an `enforce_csrf_checks=True` client gets `403`. Both strictnesses are the row's substance,
   not thoroughness: **a non-enforcing client makes the assertion non-distinguishing**, because
   `CsrfViewMiddleware.process_view` short-circuits on `_dont_enforce_csrf_checks` and both
   arrangements answer `200`. Worker 3's second fixture trap applies to any row whose witness is the
   `request.POST` read: an enforcing client *without* a well-formed `csrftoken` cookie is rejected on
   `REASON_NO_CSRF_COOKIE` before that read. Whichever client a row uses, state in the row's
   docstring why it distinguishes.
5. **Low (b)'s rows** — at least two, so the boundary is not weakly pinned: a callback stamped with
   `_BOUNDARY_MARKER` but carrying no `view_class`, and one carrying a `view_initkwargs` that is not
   a `dict`, each mounted in the test URLconf and requested through `_chain(_ORDERED_CHAIN)`. Both
   must be passed through to their own response rather than producing a `500`. The docstring states
   the answer: an unrecognizable callback is not one this middleware can run a boundary for, and
   after A-2 declining it leaves the fallback arrangement intact rather than a bare pass-through.
6. **No staleness sweep is owed.** No example-model field set changes and no wire shape converts
   (`BUILD.md` `### Test staleness a focused run cannot see`). The `csrf_exempt`-value sweep was
   performed by the review pass and its two prose-stale sites in
   `examples/fakeshop/test_query/test_transport_api.py` are R3's under M-A; this pass does not touch
   `examples/**`. One check is owed instead, because the fix changes what `bool(view.csrf_exempt)`
   answers *in flight*: confirm `::test_the_view_callback_of_both_views_carries_the_csrf_exempt_mark`
   still means what it says (it reads the mark outside any request, where the ContextVar is unset, so
   `True` remains correct).

Temp tests: `docs/builder/temp-tests/r1/test_r1_probes.py` is the promotion **source** and stays as
the pass's scratch record; its third-party-cancellation probe is **not** promoted (Worker 3's
disposition, and `consumers.py` is untouched here). `::test_r1_hotpath.py` is reused unmodified as
the hot-path snippet.

### Failability proofs (pass 2)

Owner: **Worker 2**, mechanized, per `BUILD.md` `### Mechanized: scripts/prove_failability.py`, with
Worker 3 auditing every record and re-running its own subset. Write the pass-2 manifest to
`docs/builder/temp-tests/r1/proofs-pass2.json` and the emitted block to `…/proofs-pass2.md`:
**do not overwrite `proofs.json` / `proofs.md`**, which are the pass-1 record Worker 3's node-id set
comparison referenced.

**Re-run the whole manifest, all thirteen entries, in one invocation.** It is one command and a few
minutes, and it removes the ambiguity `BUILD.md` `### What gets recorded` warns about: when a row set
changes, only a full re-measurement distinguishes "the fix moved it" from "someone measured wrong".

Pass-1 entry numbers 1-11 keep their identity so the sets stay comparable. Measured this pass with
`grep -c -F` against `HEAD`: **all eleven pass-1 anchors currently match exactly once.** After the
fix:

| Pass-1 # | Boundary | Anchor after this pass | Row set |
| --- | --- | --- | --- |
| 1 | `views.py::_RequestBodyBoundaryMixin._enforce_body_charset_declaration` (the refusal) | **invalidated by DRY (f)** — re-anchor to the new `if _declared_charset_is_unhonourable(request):` + its `raise` line (two lines: the bare `raise HTTPException(400, _JSON_PARSE_REASON)` occurs twice in the file) | expected identical (7) |
| 2 | the same method's GET / multipart carve-out | survives unchanged | expected identical (2) |
| 3 | the chain's recognition of a package callback | **invalidated by Low (b)** — re-anchor inside `middleware/request_body.py::_package_view_instance`; mutation: make it always answer `None` (the chain never recognizes, never runs the boundary, never stamps) | **expected to SHRINK** — after A-2 an unrecognized callback falls back to the view's own boundary, so the over-limit rows still answer `413`; predicted survivors are the "already measured" pair and the configured-CSRF-class pair. That shrink is the fix working, not a regression |
| 4 | `_CsrfOrderingExemption.__bool__` -> never withdraws | **invalidated** (predicate rewritten, file moved) — re-anchor in `_boundary_ordering.py`, mutation `return True` | expected to change |
| 5 | the same -> always withdrawn | **invalidated** — same file, mutation `return False` | expected to change (grows: the new marker-less rows also fail) |
| 6 | `middleware/request_body.py::_require_boundary_before_csrf` | survives unchanged | expected identical (3) |
| 7 | `views.py::_RequestBodyBoundaryMixin._enforce_request_boundary_once` | survives unchanged | **expected to GROW** — the new marker-less rows and the boundary-only-chain row all depend on the view being the enforcer |
| 8 | `_request_body.py::_measured_remaining` (exact-`int` gate) | survives unchanged | expected identical (6) |
| 9, 10, 11 | the three `consumers.py` boundaries | survive unchanged, file untouched | expected **identical**; a set difference here means contamination, not improvement |

**New entries, both boundaries this pass adds:**

| New # | Boundary | Mutation | Why it is the right mutation |
| --- | --- | --- | --- |
| 12 | `middleware/request_body.py::_package_view_instance` (the attribute guard) | delete the `isinstance` conjunct so the attributes are dereferenced unguarded | removes the guard rather than perturbing it; the marked-but-classless rows must fail with the `AttributeError`/`TypeError` the guard exists to prevent |
| 13 | `_boundary_ordering.py::_CsrfOrderingExemption.__bool__` (the per-request key) | `return _boundary_middleware_request.get() is None` | **the mutant IS the defective predecessor**: it restores "the chain is installed, therefore withdraw", which is exactly the shipped defect. Worker 3 accepted the same reasoning for pass-1 entries 9 and 11. Its failing rows must be the new marker-less rows, which is what proves those rows pin the fix rather than merely accompanying it |

Entry 13 is the pass's load-bearing proof. Entries 4 and 5 keep both blunt directions because they
pin the two arrangements against each other; 13 pins the boundary *between* them.

Rules that are not negotiable here: the anchor check runs first and must match **exactly once**
(`grep -c -F` while writing the manifest, and the runner re-checks before any copy is taken); the
scratch root is **outside** the repository; one mutation live at a time, reverted inside its own
entry, restore proved by byte comparison; `git` is never invoked to restore. **0 or 1 failing rows is
`revision-needed`, and the fix is more or better-targeted rows, never a weaker boundary** — for a
zero-row result, name which case it is (weakly pinned versus harness-impossible) in those words.
Every entry's record carries its pre-mutation baseline of the same scope, the listed failing node
ids, and a separate collection/setup-error count of **0**; a run with errors is no valid count.

**One proof obligation that is not a failability proof.** DRY (f) is an *extraction*, so
`BUILD.md` `## Claims are proven mechanically, never accepted on prose` applies instead: prove that
both call sites reproduce their originals by a character diff of the extracted condition against
`HEAD`'s two copies, obtained read-only with `git show HEAD:django_strawberry_framework/views.py`
into a scratch path outside the repo. The same rule covers the A-1 move: the four moved definitions
must be character-identical to `HEAD`'s apart from the ContextVar's declared type, name, and default,
and `_CsrfOrderingExemption.__bool__`'s body, all four of which this plan specifies as deliberate
changes.

### Hot-path budget

**Declared hot-path.** `__bool__` is consulted by `CsrfViewMiddleware.process_view` on every request
that reaches the endpoint through an installed chain, and `_declared_charset_is_unhonourable` runs on
every non-multipart, non-GET request. Per-request work either way.

The metric is **the same measurement Worker 3 recorded**, so before and after are comparable numbers
rather than two different experiments. Reuse `docs/builder/temp-tests/r1/test_r1_hotpath.py`
unmodified.

- **Metric 1 — median wall-clock per request.** `Client().post` against the sync package mount with
  a small JSON body, **400 iterations** after one discarded warm-up request (the chain is built
  lazily on the first request), median, **four independent runs**, for both arms
  (`[CsrfViewMiddleware]` and `[boundary, CsrfViewMiddleware]`). Report the installed arm before and
  after; keep the CSRF-only arm in both captures as the control. Command:
  `uv run pytest docs/builder/temp-tests/r1/test_r1_hotpath.py -s -o addopts="" --no-cov`.
  Worker 3's pre-fix reading, for reference and not to be inherited: four medians of 310.52 /
  319.58 / 308.87 / 316.23 us installed against 333.02 / 323.27 / 312.10 / 334.48 us not installed,
  i.e. the installed chain measured 3-22 us **faster**.
- **Metric 2 — the charset guard's micro-cost.** `timeit` over **200,000** calls of
  `views.py::_canonicalizes_to_utf8("utf-8")` (Worker 3's pre-fix reading: 0.0974-0.1021 us/call).
  After DRY (f) the common path also pays one function call, so add the same 200,000-iteration
  `timeit` over `views.py::_declared_charset_is_unhonourable(request)` on a request with no declared
  charset.
- **Metric 3 — the predicate's own micro-cost, new this pass.** `timeit` over **200,000** calls of
  `bool(_CSRF_ORDERING_EXEMPTION)` in each of the two states that matter: the ContextVar unset, and
  the ContextVar set to a stamped request. Before the fix the second state is a ContextVar `get` plus
  a `not`; after it is a `get` plus a `getattr`, so this is the one number the change could move on
  the read Django performs per request.

Record metric, exact command, iteration count, statistic, before, after, delta. A single-shot reading
is not a number. **Whether the cost is acceptable is the maintainer's call and no worker's**, and no
correctness boundary is weakened to buy a number back.

### Floor verification scope

**Owner: this fixing pass (Worker 2).** The final gate is the backstop that confirms it happened,
never a second owner, and a planned floor run no pass performed is `revision-needed`.

Scope: `tests/test_views.py` and `tests/test_routers.py` — the fix changes request-lifecycle
plumbing and the package's import graph, a Django integration seam. No `--cov*` flags. Floor facts
are `BUILD.md` `## Floor verification`'s, taken from there and never restated from memory: the
supported floor is **Django 5.2.0 on Python 3.10 with strawberry-graphql 0.316.0**. The shared
`.venv` is never the floor and is **never** mutated — always an explicit `--python <venv>/bin/python`
into a venv built **outside** the repository (`/tmp/dsf-floor` is the established path and Worker 3's
run there is still on disk; rebuild it rather than assume its state). Record the resolved versions as
read by `uv pip list --python <venv>/bin/python`, and each command's pass/fail.

Two floor questions this pass creates, on top of the green sweep:

1. **The ContextVar now carries the request across the `sync_to_async`-adapted
   `CsrfViewMiddleware.process_view`, and the stamp crosses back on the shared request object.** The
   mechanism is asgiref's context copy-in (Worker 3 verified `_restore_context` present at the
   floor); confirm by **execution** that the async rows still pass at the floor, since the async
   arrangement is where a propagation assumption would fail silently.
2. **`getattr(callback, "csrf_exempt", False)` is still read for truthiness at Django 5.2.0**, which
   is what lets a lazily-evaluated object be the value at all. Worker 3 confirmed it from
   `inspect.getsource` at the floor; re-confirm it holds for the new predicate by the rows rather
   than by re-reading.

Floor fact correction to carry, so it is not re-derived: the floor venv resolved a **newer** asgiref
(3.12.1) than the shared `.venv` (3.11.1). The floor is not an "everything older" environment.

### Boundary count and the split question

Answered rather than assumed. **New** boundaries: two (the per-request exemption key; the recognizer's
attribute guard). Re-anchored existing boundaries: four. Untouched proofs re-run for set stability:
seven. Plus one extraction, three docstring corrections, one module move, and roughly seven new or
re-pinned test rows.

**Decided: one cohort, one pass.** Two new boundaries is below the "roughly five" prompt, and the
partition question is moot in any case: every production file (`views.py`,
`middleware/request_body.py`, the new `_boundary_ordering.py`) and every test change lands in the one
test file, `tests/test_views.py`, so no two cohorts could run concurrently even if the work were
split (`BUILD.md` `### Parallel cohorts under a declared ownership partition`: one shared file
serializes). Worker 3 reached the same conclusion from the finding side.

### Routing confirmations

- **Low (c) — the charset guard's GET-only exclusion — stays routed to R2, confirmed rather than
  overruled.** Worker 3's reasoning is right: Decision 9 has no declaration half at all, so there is
  no contract for a method-scope change to be checked against, and the code change (one method name
  in a condition) belongs in the same pass as the spec sentence that authorizes it. Worker 2 **does
  not** change `views.py::_RequestBodyBoundaryMixin._enforce_body_charset_declaration`'s method scope
  on a review's prose, and pass-1 proof entry 2's anchor and row set therefore survive unchanged.
  R2's item 2 already carries it.
- **M-A's re-pin cost must be re-measured by R3, not inherited.** M-A records exactly one live row
  breaking (`examples/fakeshop/test_query/test_transport_api.py
  ::test_the_async_view_also_refuses_before_djangos_parser_runs`, whose probe wrapper copies
  `csrf_exempt` but not the boundary marker); that is the same mechanism as the High finding, so once
  this fix lands the row may not break under the shipped chain at all and the move to a
  fallback-override chain may be unnecessary. R3 re-measures against the fixed code before enacting
  any re-pin.
- **`### Dispatched findings checklist` is unchanged by this pass and nothing is ticked here.** The
  boxes stay `- [ ]` at planning by the same rule as pass 1; Worker 2 ticks only a box whose fix
  lands in its diff (boxes 2 for the High fix, and the `views.py` half of box 1 only if it considers
  DRY (f) part of that contract — it is not, so box 1 stays for Worker 1), and Worker 1 ticks the
  rest at final verification, where a tick means *landed **and** audited*.

### Write-set corrections Worker 0 must record

The plan's R1 write list predates this decision and does not cover two paths this pass must write.
A worker never silently writes outside its cohort's ownership (`BUILD.md` `### Parallel cohorts under
a declared ownership partition`), so Worker 0 records the extension in
`build-046-transport_security-0_0_15.md` `## Round shapes and per-round ownership` before dispatch:

1. `django_strawberry_framework/_boundary_ordering.py` — **new file**, created by this pass (A-1).
2. `examples/fakeshop/apps/kanban/constants.py` — script-rendered, one added
   `TRACKED_FILE_PATHS` line, regenerated by step 10 and never hand-edited.

Neither is consumer-visible and neither is on the cycle's `## Do-not-touch` list.
`examples/fakeshop/config/settings.py` and `examples/fakeshop/test_query/**` stay **R3's** under M-A;
this pass does not touch `examples/**` beyond the generated constants file. One downstream note for
R3, recorded so it is not missed: the new module adds one row to `docs/TREE.md`, which R3 regenerates
(`START.md` `## Rendered docs`) — its module docstring must therefore carry no staging language.

### Implementation discretion items

Assessed and decided to belong to Worker 2:

- The **wording** of the three docstring rewrites, provided each states the fact this plan names.
- Whether `_package_view_instance` returns the instance or a `(view_class, initkwargs)` pair for
  `process_view` to instantiate — equivalent shapes; the answer it must give is `None` for a callback
  whose boundary cannot be run.
- The order of the two Low (b) rows and whether they parametrize over the transports or over the two
  malformed callbacks.
- Where in `views.py` `_declared_charset_is_unhonourable` sits among the module-level predicates, and
  its docstring's length.
- Iteration counts **above** the floors stated in `### Hot-path budget` (400 requests / 200,000
  micro-calls), and whether to add a fifth run.
- Whether to rebuild `/tmp/dsf-floor` or use a fresh scratch venv path for the floor run.

Nothing architectural is delegated. A-1 and A-2 are decided above; Low (c) is routed; the duplicated
-boundary-entry contract and the `[boundary, csrf, boundary]` over-refusal are R2's. If implementation
reveals that A-2's predicate cannot hold in a state this plan's table does not list, that is a
plan-level question: set `revision-needed` naming the structural-drift pause and route it back to
Worker 1 rather than choosing a different predicate.

---

## Build report (Worker 2, pass 2)

**What this pass is.** The fixing pass for the round's verdict, built against
`## Plan (Worker 1, pass 2 - revision)`: the **High** security regression, the **Medium**
missing row, **Low (b)**, **DRY (f)**, and the docstring contracts the fix makes true again.
`Low (a)` was already corrected by the review pass and `Low (c)` is routed to R2
(`### Routing confirmations`), so neither is in this diff. `consumers.py` and
`tests/test_routers.py` carry no production change from this pass; their three proofs were
re-run only to show the row sets did not move.

The High fix is A-2's two-clause predicate, with the marks relocated into the new
`_boundary_ordering.py` per A-1. Measured after the fix, on the chain the finding used: an
over-limit multipart to a callback carrying `csrf_exempt` but not the boundary marker now
answers `413` with `MultiPartParser.parse` called **0** times, where the same request on the
same mount was parsed once before.

### Files touched

Grounded in `git status --short` run after both ruff invocations, not from memory:

- `django_strawberry_framework/_boundary_ordering.py` - **new**, 111 lines. Owns
  `_BOUNDARY_MARKER`, `_BOUNDARY_ENFORCED`, the ContextVar (now
  `_boundary_middleware_request`, `ContextVar[HttpRequest | None]`, `default=None`),
  `_CsrfOrderingExemption` with A-2's predicate, and the shared `_CSRF_ORDERING_EXEMPTION`.
  Runtime imports: `contextvars` and `typing` only, with `HttpRequest` under `TYPE_CHECKING`,
  so the module cannot participate in an import cycle. No `__all__` - every name is private.
  Its docstring owns the protocol: what each mark means, who writes and who reads each, and
  the invariant the exemption rests on.
- `django_strawberry_framework/middleware/request_body.py` - the four definitions removed and
  the three surviving names imported from `_boundary_ordering`; `__call__` / `__acall__` now
  set the ContextVar to the **request**; `_package_view_instance` added and `process_view`
  reduced to branching on its answer; four docstring passages rewritten (the module
  docstring's exemption paragraph, its "what it deliberately does not do" recognition
  sentence, `__call__`'s reason-for-the-mark paragraph, and `process_view`'s
  declined-callback clause). `__all__` unchanged at
  `("GraphQLRequestBodyBoundaryMiddleware",)`.
- `django_strawberry_framework/views.py` - the three-name import re-pointed to
  `_boundary_ordering`; `_declared_charset_is_unhonourable` added and called from both sites
  (DRY (f)); three docstring corrections (the module docstring's withdrawal sentence,
  `_RequestBodyBoundaryMixin`'s honest-boundary "or" limb, `::as_view`'s exemption paragraph)
  plus `::_enforce_body_charset_declaration`'s declaration paragraph re-pointed at the helper
  instead of restating its rule.
- `tests/test_views.py` - imports re-pointed; the one row the new predicate falsifies re-pinned
  and strengthened; the marker-dropping wrapper, the two malformed marked callbacks, four new
  mounts, `_WRAPPED_PATHS`, `_STOCK_CSRF_MIDDLEWARE_PATH`, `_csrf_enforcing_client`,
  `_counting_multipart_parses`, a `client=` parameter on `_post`, and six new rows (12 node
  ids).
- `examples/fakeshop/apps/kanban/constants.py` - **regenerated, never hand-edited**; exactly
  one added `TRACKED_FILE_PATHS` line in alphabetical position (diff quoted below).
- `docs/builder/bld-046-r1-remediation_review.md` - this section, the tick on
  `### Dispatched findings checklist` box 2, and the `Status:` transition to `built`.
- `docs/builder/temp-tests/r1/proofs-pass2.json`, `.../proofs-pass2.md`, `.../run-pass2.log`,
  `.../test_r1_hotpath_predicate.py`, `.../test_r1_ma_remeasure.py` - gitignored scratch, so
  they do not appear in `git status`. Pass 1's `proofs.json` / `proofs.md` / `run.log` were
  **not** overwritten; the node-id set comparison below is against them.

**The one authorized staging, performed and reported.**
`git add django_strawberry_framework/_boundary_ordering.py` - that single path and nothing
else, because `scripts/build_kanban_tracked_path_constants.py` renders from `git ls-files`,
which reads the index and so cannot see an untracked file. `git diff --cached --name-status`
after it reads exactly `A	django_strawberry_framework/_boundary_ordering.py`. No
`git add -A`, no commit, no branch, nothing else staged.

### Tests added or updated

All in `tests/test_views.py`. Package-tier placement per `AGENTS.md` #10: a marker-dropping
wrapper mount, a marked-but-unbuildable callback, and a chain carrying no CSRF entry are not
request shapes a live fakeshop query can reach.

- `::test_the_async_chain_resets_the_ordering_mark_around_the_downstream_call` - **re-pinned,
  strengthened, never weakened.** The one row the new predicate falsifies. It asserted one
  thing inside the downstream call (`bool(...) is False`); it now asserts three, and they are
  the predicate's two clauses plus the reset: `True` before the stamp (the chain is handling
  this request but has not run the boundary, so the view still owns the ordering), `False`
  after `setattr(request, _BOUNDARY_ENFORCED, True)` exactly as `process_view` does, and
  `True` again after the raising chain unwinds. Proof entry 13 fails this row, so it
  discriminates the fix from its defective predecessor rather than merely accompanying it.
- `::test_installing_the_middleware_parses_no_body_on_either_mount` (2) - the High fix's
  decisive row. Chain `[boundary, stock CSRF]`, `_csrf_enforcing_client`, an over-limit
  multipart to the stamped mount **and** to the marker-less one: both `413`, with
  `MultiPartParser.parse` called 0 times. The parse counter is the witness, not the status
  code - the over-limit request was refused before the fix too; what the defect changed was
  *when*.
- `::test_the_same_two_mounts_parse_nothing_without_the_middleware_either` (2) - the regression
  half. Same two mounts, chain `[stock CSRF]`, same assertions. Held together with the row
  above, the pair states the property the finding is about: **installing the middleware does
  not change the answer for either mount**, so no deployment loses an ordering by installing
  it.
- `::test_a_declined_callbacks_over_limit_body_never_reaches_the_csrf_class` (2) - the
  secondary witness, against `_RejectingCsrfMiddleware` on `_ORDERED_CHAIN`: `413`, the shared
  `_BODY_LIMIT_REASON` on the wire, and an empty CSRF call log for the *declined* mount - the
  same assertion `::test_the_chain_refuses_an_over_limit_multipart_before_any_csrf_read`
  already makes for the stamped one.
- `::test_a_declined_callback_still_gets_a_complete_csrf_check` (2) - falling back costs the
  class, never the protection. Both strictnesses, because either alone is non-distinguishing:
  a passing client cannot show a check ran, a rejected one cannot show the request would
  otherwise reach the schema.
- `::test_a_chain_with_the_boundary_and_no_csrf_middleware_still_checks_csrf` (2) - the
  **Medium** finding, promoted from
  `docs/builder/temp-tests/r1/test_r1_probes.py::test_boundary_installed_with_no_csrf_middleware_still_checks_csrf`.
  Both transports, both strictnesses; the docstring states why a default client would make the
  assertion say nothing.
- `::test_a_marked_callback_the_middleware_cannot_build_is_declined_not_crashed` (2) - **Low
  (b)**, parametrized over a marked callback with no `view_class` and one whose
  `view_initkwargs` is not a mapping. Both are passed through to their own `200`, which is
  what an unhandled `500` out of `process_view` would break; proof entry 12 fails both.

`::test_the_view_callback_of_both_views_carries_the_csrf_exempt_mark` was re-read and left
alone, as the plan's test item 6 requires: it reads the mark outside any request, where the
ContextVar is unset, so `bool(view.csrf_exempt) is True` is still correct **and** still
discriminating - proof entry 5 (`__bool__` -> `return False`) fails both its
parametrizations.

No staleness sweep is owed: no example-model field set changed and no wire shape converted
(`BUILD.md` `### Test staleness a focused run cannot see`). The `csrf_exempt`-value sweep was
performed by the review pass and its two prose-stale sites in
`examples/fakeshop/test_query/test_transport_api.py` stay R3's under M-A.

### Validation run

- `uv run ruff format django_strawberry_framework/_boundary_ordering.py django_strawberry_framework/middleware/request_body.py django_strawberry_framework/views.py tests/test_views.py`
  - pass (`4 files left unchanged` on the final run; scoped to this pass's files, never `.`).
- `uv run ruff check --fix <the same four>` - pass (`All checks passed!`).
- `uv run ruff format --check examples/fakeshop/apps/kanban/constants.py` (`1 file already
  formatted`) and `uv run ruff check examples/fakeshop/apps/kanban/constants.py`
  (`All checks passed!`) - read-only on the generated file, since a write-mode run on it would
  be a hand-edit of script-rendered output.
- `uv run python scripts/check_trailing_commas.py --check <the four plus the generated file>`
  - exit 0. Run because the gate's ruff step does not cover the source-layout hook that gates
  commits (line length 100, ASCII-only `.py`, trailing-comma explode-at-threshold).
- `uv run python scripts/build_kanban_tracked_path_constants.py` after the one authorized
  `git add`, producing exactly:

```diff
     TRACKED_FILE_PATHS = (
         "django_strawberry_framework/__init__.py",
    +    "django_strawberry_framework/_boundary_ordering.py",
         "django_strawberry_framework/_cross_web_patches.py",
```

- `git status --short` after both ruff invocations - eight entries, every one accounted for:
  `A  django_strawberry_framework/_boundary_ordering.py` (the authorized stage),
  `M django_strawberry_framework/middleware/request_body.py`,
  `M django_strawberry_framework/views.py`, `M examples/fakeshop/apps/kanban/constants.py`,
  `M tests/test_views.py`, `?? docs/builder/bld-046-r1-remediation_review.md` (this artifact),
  plus two **baseline-dirty paths this pass neither wrote nor reverted** (`AGENTS.md` #34):
  `M django_strawberry_framework/_request_body.py` (the review pass's docstring-only Low (a)
  correction) and `M docs/builder/build-046-transport_security-0_0_15.md` (Worker 0's closeout
  section). `M tests/test_routers.py` is pass 1's own added row, still uncommitted. Nothing
  unexpected.
- Focused runs, every one without any `--cov*` flag: `uv run pytest tests/test_views.py
  --no-cov` - **194 passed** (182 before this pass, plus 12 node ids);
  `uv run pytest tests/test_routers.py --no-cov` - **145 passed**, run despite being untouched
  because the new module changes the package's import graph.
- Sibling scope, per `worker-2.md` `## Apply-changes verification scope` - every test file
  that imports the changed surface, found with
  `grep -rln 'django_strawberry_framework.views\|middleware.request_body\|_boundary_ordering\|csrf_exempt' tests examples --include='*.py'`:
  `uv run pytest examples/fakeshop/test_query/test_transport_api.py
  tests/test_cross_web_patches.py tests/test_prove_failability.py --no-cov` - **182 passed**,
  so the live transport tier is green against the fixed code.

### Relocation and extraction proofs

Not failability proofs: `BUILD.md` `## Claims are proven mechanically, never accepted on
prose`, second shape. Pristine `HEAD` was obtained **read-only** with
`git show HEAD:<path>` into a scratch path outside the repository - no `git checkout`,
`restore`, `stash` or `worktree` anywhere in this pass - and compared with comments,
docstrings and whitespace stripped, i.e. on the executable token stream
(`ast` + `tokenize`).

- **The two attribute-name string values are carried verbatim**, which is the load-bearing
  half: a changed string silently unpairs the writer from the reader. Both assignment lines
  are **byte-identical** to `HEAD`'s:
  `_BOUNDARY_MARKER = "graphql_request_body_boundary"` and
  `_BOUNDARY_ENFORCED = "graphql_request_body_boundary_enforced"`.
- **`_CsrfOrderingExemption` + `_CSRF_ORDERING_EXEMPTION`**: token-identical to `HEAD`'s once
  `__bool__`'s two-line body is replaced by A-2's predicate - 37 tokens vs 37, no other
  difference. Compared **without** that substitution the two differ, and the first differing
  token is the first token of `__bool__`'s body, which localizes the whole delta to the one
  place the plan authorizes it.
- **The ContextVar declaration** carries exactly the three deltas A-1 specifies and nothing
  else: `_boundary_middleware_active: ContextVar[bool]` /
  `"..._boundary_middleware_active"` / `default=False` becomes
  `_boundary_middleware_request: ContextVar[HttpRequest | None]` /
  `"..._boundary_middleware_request"` / `default=None`.
- **The move is a move, not a copy.** `grep -rn -F` over `django_strawberry_framework/`
  returns exactly **1** hit each for `_BOUNDARY_MARKER =`, `_BOUNDARY_ENFORCED =`,
  `class _CsrfOrderingExemption` and `_CSRF_ORDERING_EXEMPTION =`, all four in
  `_boundary_ordering.py`.
- **Neither of the two modules imports the other**, which is the whole point of A-1:
  `grep -rn 'middleware.request_body import' django_strawberry_framework/` and
  `grep -rn 'import views' django_strawberry_framework/middleware/` both return nothing.
- **DRY (f) is behaviour-preserving by construction.** `HEAD`'s `views.py` carried the two
  lines verbatim at both sites (confirmed by substring search at both indentations), and the
  extracted helper's condition is token-identical to `HEAD`'s copy re-spelled as a `return`
  (26 tokens vs 26), `(request.content_params or {})` included.
- **`consumers.py` is byte-identical to `HEAD`** (`git show HEAD:... | cmp`), and independently
  so: its pre-mutation SHA-256 prefix in the proof record below, `1bdf298c473fd1a0`, is the
  same value pass 1 recorded.

### Failability proofs

**All thirteen manifest entries were re-run in one invocation**, as the plan requires, so a
moved row set is distinguishable from a re-measurement artifact:

```shell
uv run python scripts/prove_failability.py docs/builder/temp-tests/r1/proofs-pass2.json \
    --scratch-root <session scratchpad>/dsf-r1-proofs2 \
    --output docs/builder/temp-tests/r1/proofs-pass2.md
```

Final run **exit 0**: every entry proved, **no boundary weakly pinned**, **0 collection or
setup errors on every entry**, every restore proved by byte comparison. Anchor verification
was run first and separately (`--check-anchors-only`, exit 0: all thirteen anchors matched
**exactly once before any copy was taken**), and every anchor was additionally measured by
hand with `grep -c -F` while the manifest was written - which is how the re-anchor for entry 1
was chosen: the bare `raise HTTPException(400, _JSON_PARSE_REASON)` line occurs **4** times in
`views.py`, so that entry's anchor is the two-line block.

**why 0: not applicable to any entry - no entry measured zero rows.** The lowest count in the
record is 2. So neither the weakly-pinned reading nor the harness-impossible reading is
invoked anywhere below, and this pass records no harness limitation.

**Node-id set movement against pass 1, per the plan's predictions.** Compared as sets, not as
counts.

| # | Pass 1 | Pass 2 | Direction | Plan predicted | Verdict |
| --- | --- | --- | --- | --- | --- |
| 1 | 7 | 7 | **set-equal** | identical (7) | matches |
| 2 | 2 | 2 | **set-equal** | identical (2) | matches |
| 3 | 4 | 4 | **moved**, same size | SHRINK, survivors = "already measured" pair + configured-CSRF-class pair | **content matches exactly**, size does not |
| 4 | 3 | 3 | **set-equal** | "expected to change" | did not change |
| 5 | 5 | 13 | **grew** (+8, none lost) | grows | matches |
| 6 | 3 | 3 | **set-equal** | identical (3) | matches |
| 7 | 8 | 14 | **grew** (+6, none lost) | GROW | matches |
| 8 | 6 | 6 | **set-equal** | identical (6) | matches |
| 9, 10, 11 | 2, 2, 2 | 2, 2, 2 | **set-equal** | identical; a difference means contamination | matches, no contamination |
| 12 | - | 2 | new | new boundary | pinned |
| 13 | - | 7 | new | the load-bearing entry | pinned |

Three readings the sets give that the counts alone would hide:

- **Entry 3 moved to precisely the set the plan predicted, at the same size.** It lost
  `::test_the_chain_refuses_an_over_limit_multipart_before_any_csrf_read[sync|async]` and
  gained `::test_the_projects_own_csrf_middleware_runs_when_the_chain_supplies_the_ordering[sync|async]`,
  leaving `{configured-CSRF-class pair, already-measured pair}` - the plan's two predicted
  survivor pairs exactly. The loss **is the fix working**: with recognition gone, an
  over-limit body is now caught by the view's own boundary and still answers `413`, which is
  the fallback A-2 installs. The gain is that the configured-CSRF-class rows now depend on
  recognition, because recognition is what writes the stamp the withdrawal keys off.
- **Entry 4 did not change**, against the plan's expectation. `return True` (never withdraws)
  fails the same three rows as before, which is right: those rows are about the *stamped*
  mount, whose answer the fix does not alter.
- **Entry 7 grew by the six marker-less rows but NOT by the boundary-only-chain row.** The
  plan predicted that row would fail too; it does not, and the reason is worth recording
  rather than leaving as a discrepancy: `_enforce_request_boundary_once` is the body
  enforcer, while what protects the boundary-only chain is the view's separate CSRF
  continuation. That row is pinned by entry 3's and entry 13's mutants instead, not by this
  one.

Entry 13 is the pass's load-bearing proof and its mutant **is** the shipped defect
(`return _boundary_middleware_request.get() is None`, i.e. "the chain is installed, therefore
withdraw"). It fails **7** rows, six of them the rows written for the High finding plus the
re-pinned async row - so those rows pin the fix rather than accompany it. A small count there
would have been a signal; 7 is not small.

The emitted record follows verbatim, every measured field filled in by the runner.


Procedure, mechanized by `scripts/prove_failability.py`: the target is copied to a scratch path OUTSIDE the repo before any mutation; the mutation site is located by an exact anchor asserted to match exactly once (any other count aborts the entry without writing); the same focused scope is run unmutated first, so rows already failing before the mutation are differenced out of the count; both runs' pytest exit codes are read, because a run that collected nothing or blew up emits no `FAILED` lines and would otherwise be recorded as a measured zero; both runs use `--no-cov`; the file is restored from the pre-mutation copy in a `finally` and the restore is proved by `filecmp.cmp(shallow=False)` plus a SHA-256 comparison. One boundary at a time, restored before the next. `git` is never invoked - the tree is legitimately dirty, so an empty `git diff` is unachievable and forcing one would destroy the build's own work.

| # | Boundary | File mutated | Mutation applied | Rows failed | Errors | Scope as run | Restore proof |
|---|---|---|---|---|---|---|---|
| 1 | `django_strawberry_framework/views.py::_RequestBodyBoundaryMixin._enforce_body_charset_declaration` | `django_strawberry_framework/views.py` | deleted: `if _declared_charset_is_unhonourable(request): raise HTTPException(400, _JSON_PARSE_REASON)` - builder's description (unverified prose): the charset refusal itself deleted: a declared non-UTF-8 charset is read and then ignored (re-anchored onto the DRY (f) helper call; the bare raise line alone occurs 4 times in the file, so the anchor is the two-line block) | **7** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_views.py` | filecmp.cmp(shallow=False) True; sha256 e8aeb156550fc45a... == e8aeb156550fc45a... (vs pre-mutation copy) |
| 2 | `django_strawberry_framework/views.py::_RequestBodyBoundaryMixin._enforce_body_charset_declaration #"if request.method == \"GET\" or _is_multipart_form_post(request)"` | `django_strawberry_framework/views.py` | deleted: `if request.method == "GET" or _is_multipart_form_post(request): return` - builder's description (unverified prose): the GET / multipart carve-out deleted, so the guard claims every request shape including the ones the multipart encoding guard owns | **2** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_views.py` | filecmp.cmp(shallow=False) True; sha256 e8aeb156550fc45a... == e8aeb156550fc45a... (vs pre-mutation copy) |
| 3 | `django_strawberry_framework/middleware/request_body.py::_package_view_instance #"if not getattr(view_func, _BOUNDARY_MARKER, False)"` | `django_strawberry_framework/middleware/request_body.py` | `if not getattr(view_func, _BOUNDARY_MARKER, False):` -> `if True:` - builder's description (unverified prose): the recognition made unconditionally negative: _package_view_instance always answers None, so the chain never runs the boundary and never stamps the request | **4** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_views.py` | filecmp.cmp(shallow=False) True; sha256 0c022a860cb31d6e... == 0c022a860cb31d6e... (vs pre-mutation copy) |
| 4 | `django_strawberry_framework/_boundary_ordering.py::_CsrfOrderingExemption.__bool__` | `django_strawberry_framework/_boundary_ordering.py` | `request = _boundary_middleware_request.get() return request is None or not getattr(request, _BOUNDARY_ENFORCED, False)` -> `return True` - builder's description (unverified prose): the withdrawal removed: the exemption is always truthy, so the configured CSRF middleware always skips the callback | **3** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_views.py` | filecmp.cmp(shallow=False) True; sha256 b2c25d9a66a6090c... == b2c25d9a66a6090c... (vs pre-mutation copy) |
| 5 | `django_strawberry_framework/_boundary_ordering.py::_CsrfOrderingExemption.__bool__ (opposite direction)` | `django_strawberry_framework/_boundary_ordering.py` | `request = _boundary_middleware_request.get() return request is None or not getattr(request, _BOUNDARY_ENFORCED, False)` -> `return False` - builder's description (unverified prose): the exemption is always withdrawn, so the view-local arrangement loses its ordering on a chain that does not supply one | **13** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_views.py` | filecmp.cmp(shallow=False) True; sha256 b2c25d9a66a6090c... == b2c25d9a66a6090c... (vs pre-mutation copy) |
| 6 | `django_strawberry_framework/middleware/request_body.py::_require_boundary_before_csrf` | `django_strawberry_framework/middleware/request_body.py` | `boundary_index = csrf_index = None` -> `return boundary_index = csrf_index = None` - builder's description (unverified prose): the ordering audit short-circuited before it reads MIDDLEWARE, so a misordered chain is accepted at startup | **3** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_views.py` | filecmp.cmp(shallow=False) True; sha256 0c022a860cb31d6e... == 0c022a860cb31d6e... (vs pre-mutation copy) |
| 7 | `django_strawberry_framework/views.py::_RequestBodyBoundaryMixin._enforce_request_boundary_once` | `django_strawberry_framework/views.py` | `if getattr(request, _BOUNDARY_ENFORCED, False): return self._enforce_request_boundary(request)` -> `return` - builder's description (unverified prose): the view's own enforcement removed entirely: the body boundary runs zero times on any chain that does not carry the middleware | **14** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_views.py` | filecmp.cmp(shallow=False) True; sha256 e8aeb156550fc45a... == e8aeb156550fc45a... (vs pre-mutation copy) |
| 8 | `django_strawberry_framework/_request_body.py::_measured_remaining` | `django_strawberry_framework/_request_body.py` | deleted: `if type(end) is not int or type(position) is not int: return _Probe.UNMEASURABLE` - builder's description (unverified prose): the exact-int gate deleted, so a foreign position/end object's own numeric protocol executes inside the gate | **6** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_views.py` | filecmp.cmp(shallow=False) True; sha256 2c1fd48618d4b01c... == 2c1fd48618d4b01c... (vs pre-mutation copy) |
| 9 | `django_strawberry_framework/consumers.py::_ConnectionRevocation.settle` | `django_strawberry_framework/consumers.py` | `try: await asyncio.shield(self.attempt) except asyncio.CancelledError: self.attempt.cancel() # Suppressed, not swallo...` -> `await asyncio.shield(self.attempt)` - builder's description (unverified prose): the cancel-and-await-and-re-raise arm removed, leaving the bare shielded await this fix replaced: a cancelled settlement leaves the attempt running | **2** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_routers.py` | filecmp.cmp(shallow=False) True; sha256 1bdf298c473fd1a0... == 1bdf298c473fd1a0... (vs pre-mutation copy) |
| 10 | `django_strawberry_framework/consumers.py::_ConnectionRevocation._attempt_close` | `django_strawberry_framework/consumers.py` | deleted: `except asyncio.CancelledError: self.state = _REVOCATION_ABANDONED raise` - builder's description (unverified prose): the terminal-record arm deleted, so a cancelled attempt rests in CLOSING instead of ABANDONED | **2** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_routers.py` | filecmp.cmp(shallow=False) True; sha256 1bdf298c473fd1a0... == 1bdf298c473fd1a0... (vs pre-mutation copy) |
| 11 | `django_strawberry_framework/consumers.py::build_revalidating_consumer_class #"await super().disconnect(code)"` | `django_strawberry_framework/consumers.py` | `try: await super().disconnect(code) finally: await self._revocation.settle()` -> `await super().disconnect(code) await self._revocation.settle()` - builder's description (unverified prose): the try/finally flattened back to two sequential awaits, so a cancelled or raising upstream teardown skips settlement | **2** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_routers.py` | filecmp.cmp(shallow=False) True; sha256 1bdf298c473fd1a0... == 1bdf298c473fd1a0... (vs pre-mutation copy) |
| 12 | `django_strawberry_framework/middleware/request_body.py::_package_view_instance #"if not isinstance(view_class, type)"` | `django_strawberry_framework/middleware/request_body.py` | deleted: `if not isinstance(view_class, type) or not isinstance(initkwargs, dict): return None` - builder's description (unverified prose): the attribute guard deleted, so a marked callback's view_class and view_initkwargs are dereferenced unguarded and a callback carrying neither becomes an unhandled 500 out of process_view | **2** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_views.py` | filecmp.cmp(shallow=False) True; sha256 0c022a860cb31d6e... == 0c022a860cb31d6e... (vs pre-mutation copy) |
| 13 | `django_strawberry_framework/_boundary_ordering.py::_CsrfOrderingExemption.__bool__ (the per-request key)` | `django_strawberry_framework/_boundary_ordering.py` | `request = _boundary_middleware_request.get() return request is None or not getattr(request, _BOUNDARY_ENFORCED, False)` -> `return _boundary_middleware_request.get() is None` - builder's description (unverified prose): the per-request key removed and the defective predecessor restored: the exemption is withdrawn because a boundary middleware is handling the request, whether or not it ran the boundary for it | **7** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_views.py` | filecmp.cmp(shallow=False) True; sha256 b2c25d9a66a6090c... == b2c25d9a66a6090c... (vs pre-mutation copy) |

Verdicts:

1. `django_strawberry_framework/views.py::_RequestBodyBoundaryMixin._enforce_body_charset_declaration` - pinned
2. `django_strawberry_framework/views.py::_RequestBodyBoundaryMixin._enforce_body_charset_declaration #"if request.method == \"GET\" or _is_multipart_form_post(request)"` - inside Worker 3's mandatory re-run floor (<= 3 rows)
3. `django_strawberry_framework/middleware/request_body.py::_package_view_instance #"if not getattr(view_func, _BOUNDARY_MARKER, False)"` - pinned
4. `django_strawberry_framework/_boundary_ordering.py::_CsrfOrderingExemption.__bool__` - inside Worker 3's mandatory re-run floor (<= 3 rows)
5. `django_strawberry_framework/_boundary_ordering.py::_CsrfOrderingExemption.__bool__ (opposite direction)` - pinned
6. `django_strawberry_framework/middleware/request_body.py::_require_boundary_before_csrf` - inside Worker 3's mandatory re-run floor (<= 3 rows)
7. `django_strawberry_framework/views.py::_RequestBodyBoundaryMixin._enforce_request_boundary_once` - pinned
8. `django_strawberry_framework/_request_body.py::_measured_remaining` - pinned
9. `django_strawberry_framework/consumers.py::_ConnectionRevocation.settle` - inside Worker 3's mandatory re-run floor (<= 3 rows)
10. `django_strawberry_framework/consumers.py::_ConnectionRevocation._attempt_close` - inside Worker 3's mandatory re-run floor (<= 3 rows)
11. `django_strawberry_framework/consumers.py::build_revalidating_consumer_class #"await super().disconnect(code)"` - inside Worker 3's mandatory re-run floor (<= 3 rows)
12. `django_strawberry_framework/middleware/request_body.py::_package_view_instance #"if not isinstance(view_class, type)"` - inside Worker 3's mandatory re-run floor (<= 3 rows)
13. `django_strawberry_framework/_boundary_ordering.py::_CsrfOrderingExemption.__bool__ (the per-request key)` - pinned

Failing node ids, per boundary (the count above is `len()` of this list):

1. `django_strawberry_framework/views.py::_RequestBodyBoundaryMixin._enforce_body_charset_declaration`
   - file mutated: `django_strawberry_framework/views.py`
   - pytest summary: `======================== 7 failed, 187 passed in 2.26s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 194 passed in 1.65s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_views.py::test_a_non_multipart_request_is_not_subject_to_the_form_encoding_check`
   - `tests/test_views.py::test_the_endpoint_refuses_a_json_charset_it_will_not_decode_with[sync-latin-1]`
   - `tests/test_views.py::test_the_endpoint_refuses_a_json_charset_it_will_not_decode_with[sync-utf-8-sig]`
   - `tests/test_views.py::test_the_endpoint_refuses_a_json_charset_it_will_not_decode_with[sync-unknown-name]`
   - `tests/test_views.py::test_the_endpoint_refuses_a_json_charset_it_will_not_decode_with[async-latin-1]`
   - `tests/test_views.py::test_the_endpoint_refuses_a_json_charset_it_will_not_decode_with[async-utf-8-sig]`
   - `tests/test_views.py::test_the_endpoint_refuses_a_json_charset_it_will_not_decode_with[async-unknown-name]`
2. `django_strawberry_framework/views.py::_RequestBodyBoundaryMixin._enforce_body_charset_declaration #"if request.method == \"GET\" or _is_multipart_form_post(request)"`
   - file mutated: `django_strawberry_framework/views.py`
   - pytest summary: `======================== 2 failed, 192 passed in 1.88s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 194 passed in 2.05s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_views.py::test_a_get_carrying_a_stray_multipart_content_type_is_not_a_multipart_form`
   - `tests/test_views.py::test_a_multipart_declaration_is_left_to_the_form_encoding_guard`
3. `django_strawberry_framework/middleware/request_body.py::_package_view_instance #"if not getattr(view_func, _BOUNDARY_MARKER, False)"`
   - file mutated: `django_strawberry_framework/middleware/request_body.py`
   - pytest summary: `======================== 4 failed, 190 passed in 1.82s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 194 passed in 1.77s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_views.py::test_the_projects_own_csrf_middleware_runs_when_the_chain_supplies_the_ordering[sync]`
   - `tests/test_views.py::test_the_projects_own_csrf_middleware_runs_when_the_chain_supplies_the_ordering[async]`
   - `tests/test_views.py::test_the_view_does_not_measure_a_body_the_chain_already_measured[sync]`
   - `tests/test_views.py::test_the_view_does_not_measure_a_body_the_chain_already_measured[async]`
4. `django_strawberry_framework/_boundary_ordering.py::_CsrfOrderingExemption.__bool__`
   - file mutated: `django_strawberry_framework/_boundary_ordering.py`
   - pytest summary: `======================== 3 failed, 191 passed in 1.74s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 194 passed in 1.77s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_views.py::test_the_projects_own_csrf_middleware_runs_when_the_chain_supplies_the_ordering[sync]`
   - `tests/test_views.py::test_the_projects_own_csrf_middleware_runs_when_the_chain_supplies_the_ordering[async]`
   - `tests/test_views.py::test_the_async_chain_resets_the_ordering_mark_around_the_downstream_call`
5. `django_strawberry_framework/_boundary_ordering.py::_CsrfOrderingExemption.__bool__ (opposite direction)`
   - file mutated: `django_strawberry_framework/_boundary_ordering.py`
   - pytest summary: `======================== 13 failed, 181 passed in 1.76s ========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 194 passed in 1.74s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_views.py::test_the_view_callback_of_both_views_carries_the_csrf_exempt_mark[sync]`
   - `tests/test_views.py::test_the_view_callback_of_both_views_carries_the_csrf_exempt_mark[async]`
   - `tests/test_views.py::test_without_the_middleware_the_view_keeps_its_own_ordering_and_exemption[sync]`
   - `tests/test_views.py::test_without_the_middleware_the_view_keeps_its_own_ordering_and_exemption[async]`
   - `tests/test_views.py::test_the_async_chain_resets_the_ordering_mark_around_the_downstream_call`
   - `tests/test_views.py::test_installing_the_middleware_parses_no_body_on_either_mount[sync]`
   - `tests/test_views.py::test_installing_the_middleware_parses_no_body_on_either_mount[async]`
   - `tests/test_views.py::test_the_same_two_mounts_parse_nothing_without_the_middleware_either[sync]`
   - `tests/test_views.py::test_the_same_two_mounts_parse_nothing_without_the_middleware_either[async]`
   - `tests/test_views.py::test_a_declined_callbacks_over_limit_body_never_reaches_the_csrf_class[sync]`
   - `tests/test_views.py::test_a_declined_callbacks_over_limit_body_never_reaches_the_csrf_class[async]`
   - `tests/test_views.py::test_a_declined_callback_still_gets_a_complete_csrf_check[sync]`
   - `tests/test_views.py::test_a_declined_callback_still_gets_a_complete_csrf_check[async]`
6. `django_strawberry_framework/middleware/request_body.py::_require_boundary_before_csrf`
   - file mutated: `django_strawberry_framework/middleware/request_body.py`
   - pytest summary: `======================== 3 failed, 191 passed in 1.82s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 194 passed in 1.75s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_views.py::test_a_chain_that_lists_the_boundary_after_csrf_is_refused_at_startup`
   - `tests/test_views.py::test_a_boundary_subclass_listed_after_csrf_is_refused_at_startup`
   - `tests/test_views.py::test_the_first_csrf_entry_is_the_one_the_ordering_is_measured_against`
7. `django_strawberry_framework/views.py::_RequestBodyBoundaryMixin._enforce_request_boundary_once`
   - file mutated: `django_strawberry_framework/views.py`
   - pytest summary: `======================== 14 failed, 180 passed in 1.80s ========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 194 passed in 1.77s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_views.py::test_the_endpoint_refuses_a_json_charset_it_will_not_decode_with[sync-latin-1]`
   - `tests/test_views.py::test_the_endpoint_refuses_a_json_charset_it_will_not_decode_with[sync-utf-8-sig]`
   - `tests/test_views.py::test_the_endpoint_refuses_a_json_charset_it_will_not_decode_with[sync-unknown-name]`
   - `tests/test_views.py::test_the_endpoint_refuses_a_json_charset_it_will_not_decode_with[async-latin-1]`
   - `tests/test_views.py::test_the_endpoint_refuses_a_json_charset_it_will_not_decode_with[async-utf-8-sig]`
   - `tests/test_views.py::test_the_endpoint_refuses_a_json_charset_it_will_not_decode_with[async-unknown-name]`
   - `tests/test_views.py::test_without_the_middleware_the_view_keeps_its_own_ordering_and_exemption[sync]`
   - `tests/test_views.py::test_without_the_middleware_the_view_keeps_its_own_ordering_and_exemption[async]`
   - `tests/test_views.py::test_installing_the_middleware_parses_no_body_on_either_mount[sync]`
   - `tests/test_views.py::test_installing_the_middleware_parses_no_body_on_either_mount[async]`
   - `tests/test_views.py::test_the_same_two_mounts_parse_nothing_without_the_middleware_either[sync]`
   - `tests/test_views.py::test_the_same_two_mounts_parse_nothing_without_the_middleware_either[async]`
   - `tests/test_views.py::test_a_declined_callbacks_over_limit_body_never_reaches_the_csrf_class[sync]`
   - `tests/test_views.py::test_a_declined_callbacks_over_limit_body_never_reaches_the_csrf_class[async]`
8. `django_strawberry_framework/_request_body.py::_measured_remaining`
   - file mutated: `django_strawberry_framework/_request_body.py`
   - pytest summary: `======================== 6 failed, 188 passed in 1.80s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 194 passed in 1.94s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_views.py::test_a_probe_that_fails_without_moving_the_stream_falls_back_to_the_bounded_read[sync-unnumbered-end-position]`
   - `tests/test_views.py::test_a_probe_that_fails_without_moving_the_stream_falls_back_to_the_bounded_read[async-unnumbered-end-position]`
   - `tests/test_views.py::test_a_position_object_whose_numeric_protocol_raises_never_runs_inside_the_gate[sync-subtraction-raises]`
   - `tests/test_views.py::test_a_position_object_whose_numeric_protocol_raises_never_runs_inside_the_gate[sync-comparison-raises]`
   - `tests/test_views.py::test_a_position_object_whose_numeric_protocol_raises_never_runs_inside_the_gate[async-subtraction-raises]`
   - `tests/test_views.py::test_a_position_object_whose_numeric_protocol_raises_never_runs_inside_the_gate[async-comparison-raises]`
9. `django_strawberry_framework/consumers.py::_ConnectionRevocation.settle`
   - file mutated: `django_strawberry_framework/consumers.py`
   - pytest summary: `======================== 2 failed, 143 passed in 7.79s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 145 passed in 7.80s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_routers.py::test_cancelling_the_teardown_ends_the_close_attempt_instead_of_orphaning_it`
   - `tests/test_routers.py::test_a_cancelled_disconnect_leaves_no_task_retaining_the_connection`
10. `django_strawberry_framework/consumers.py::_ConnectionRevocation._attempt_close`
   - file mutated: `django_strawberry_framework/consumers.py`
   - pytest summary: `======================== 2 failed, 143 passed in 7.81s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 145 passed in 7.86s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_routers.py::test_cancelling_the_teardown_ends_the_close_attempt_instead_of_orphaning_it`
   - `tests/test_routers.py::test_a_cancelled_disconnect_leaves_no_task_retaining_the_connection`
11. `django_strawberry_framework/consumers.py::build_revalidating_consumer_class #"await super().disconnect(code)"`
   - file mutated: `django_strawberry_framework/consumers.py`
   - pytest summary: `======================== 2 failed, 143 passed in 7.41s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 145 passed in 8.02s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_routers.py::test_a_teardown_cancelled_before_it_returns_still_settles_the_close`
   - `tests/test_routers.py::test_a_teardown_that_raises_still_settles_the_close_and_propagates`
12. `django_strawberry_framework/middleware/request_body.py::_package_view_instance #"if not isinstance(view_class, type)"`
   - file mutated: `django_strawberry_framework/middleware/request_body.py`
   - pytest summary: `======================== 2 failed, 192 passed in 1.58s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 194 passed in 1.69s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_views.py::test_a_marked_callback_the_middleware_cannot_build_is_declined_not_crashed[/marked-no-view-class/]`
   - `tests/test_views.py::test_a_marked_callback_the_middleware_cannot_build_is_declined_not_crashed[/marked-bad-initkwargs/]`
13. `django_strawberry_framework/_boundary_ordering.py::_CsrfOrderingExemption.__bool__ (the per-request key)`
   - file mutated: `django_strawberry_framework/_boundary_ordering.py`
   - pytest summary: `======================== 7 failed, 187 passed in 1.63s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 194 passed in 1.56s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_views.py::test_the_async_chain_resets_the_ordering_mark_around_the_downstream_call`
   - `tests/test_views.py::test_installing_the_middleware_parses_no_body_on_either_mount[sync]`
   - `tests/test_views.py::test_installing_the_middleware_parses_no_body_on_either_mount[async]`
   - `tests/test_views.py::test_a_declined_callbacks_over_limit_body_never_reaches_the_csrf_class[sync]`
   - `tests/test_views.py::test_a_declined_callbacks_over_limit_body_never_reaches_the_csrf_class[async]`
   - `tests/test_views.py::test_a_declined_callback_still_gets_a_complete_csrf_check[sync]`
   - `tests/test_views.py::test_a_declined_callback_still_gets_a_complete_csrf_check[async]`

A boundary whose removal fails 0 or 1 rows is **weakly pinned** and is `revision-needed` per `docs/builder/BUILD.md` - the fix is more or better-targeted rows, never a weaker boundary. A boundary at 3 rows or fewer is inside Worker 3's mandatory independent re-run floor. A proof carrying collection or setup errors, or whose pytest run exited anything but 0 or 1 (nothing collected, interrupted, internal error, usage error), is not a valid count at all - and a 0 from such a run is not a zero-row result: resolve it and re-run.

Every `<fill in ...>` above is a judgement no tool can make and MUST be replaced by hand before this subsection is submitted: weakly pinned and harness-impossible are the two possible readings of a zero-row result and they prescribe opposite responses (more rows, versus a production-call-site invariant assertion plus a recorded harness limitation), so a record that does not name one reads as self-contradictory.

### Hot-path budget

The plan declares this pass hot-path: `__bool__` is consulted by
`CsrfViewMiddleware.process_view` on every request that reaches the endpoint through an
installed chain, and `_declared_charset_is_unhonourable` runs on every non-multipart, non-GET
request. Both numbers below are the same experiment before and after - same snippet, same
iteration count, same statistic, four independent runs - captured on the unmodified tree
**first** (plan step 0), because the "before" arm is `HEAD` and there is no second chance at
it. Whether the cost is acceptable is the maintainer's call and no worker's.

**Metric 1 - median wall-clock per request.** `Client().post` against the sync package mount
with a small JSON body, **400 iterations** after one discarded warm-up request (Django's
`ClientHandler` builds the chain lazily on the first request), median, four independent runs,
both arms. Snippet reused unmodified:
`docs/builder/temp-tests/r1/test_r1_hotpath.py`, run as
`uv run pytest docs/builder/temp-tests/r1/test_r1_hotpath.py -s -o addopts="" --no-cov`.

| Run | before: `[CsrfViewMiddleware]` | before: `[boundary, CSRF]` | after: `[CsrfViewMiddleware]` | after: `[boundary, CSRF]` |
| --- | --- | --- | --- | --- |
| 1 | 304.40 us | 309.75 us | 307.81 us | 309.06 us |
| 2 | 316.90 us | 315.29 us | 315.54 us | 315.08 us |
| 3 | 321.77 us | 316.02 us | 313.75 us | 312.15 us |
| 4 | 318.77 us | 314.15 us | 314.00 us | 313.31 us |

Installed-arm medians: **309.75 / 315.29 / 316.02 / 314.15 us before**, **309.06 / 315.08 /
312.15 / 313.31 us after**. Per-run delta on the installed arm: **-0.69 / -0.21 / -3.87 /
-0.84 us**, i.e. no measurable change and inside run-to-run noise on a ~313 us request (the
CSRF-only control arm moved by a comparable amount in the same captures, which is what says
the spread is noise rather than signal). The mechanism is that the fix adds no per-request
work to this path at all: `__call__` sets the same ContextVar to a request object instead of
to `True`, and `process_view`'s recognition gained two `getattr`s and two `isinstance`s on the
package-view path only.

**Metric 2 - the charset guard's micro-cost.** `timeit` over **200,000** calls, same snippet.
`_canonicalizes_to_utf8("utf-8")`: **0.0184-0.0190 s total, 0.0922-0.0950 us/call before**;
**0.0198-0.0222 s, 0.0990-0.1112 us/call after** (unchanged code; the spread is the machine).
DRY (f) adds one function call on the common path, measured directly:
`_declared_charset_is_unhonourable(request)` on a request with **no** declared charset -
which is the overwhelmingly common case and the one where the helper returns without calling
`_canonicalizes_to_utf8` at all - is **0.0110-0.0117 s / 0.0549-0.0584 us per call** over
200,000 iterations, four runs. There is no "before" for a function that did not exist; the
before-comparable is that both call sites previously executed the same two lines inline, so
the added cost is one Python call frame, and this is its size.

**Metric 3 - the predicate's own micro-cost, in both ContextVar states.** This is the read
Django performs per request, so it is the one number the rewrite could move. `timeit` over
**200,000** calls of `bool(_CSRF_ORDERING_EXEMPTION)`, four runs, snippet
`docs/builder/temp-tests/r1/test_r1_hotpath_predicate.py`, run as
`uv run pytest docs/builder/temp-tests/r1/test_r1_hotpath_predicate.py -s -o addopts="" --no-cov`.
The snippet detects which shape the tree carries, so the iteration count and the statistic are
identical across the two captures; only the way "a chain is handling this request" is
expressed differs, which is exactly what the rewrite changes.

| State | before (`ContextVar[bool]`) | after (`ContextVar[HttpRequest \| None]`) | delta |
| --- | --- | --- | --- |
| var unset | 0.0463 / 0.0484 / 0.0463 / 0.0477 us per call | 0.0513 / 0.0530 / 0.0624 / 0.0546 us per call | **+0.006 us** on the medians |
| chain active | 0.0460 / 0.0467 / 0.0469 / 0.0436 us per call | 0.0778 / 0.0694 / 0.0718 / 0.0720 us per call | **+0.025 us** on the medians |

The active-state cost roughly doubles in relative terms and is **+25 nanoseconds** in
absolute terms - one `getattr` on a request object plus one `is None` test, against a request
that costs ~313 microseconds, i.e. about 0.008% of it. Nothing was weakened to buy it back.

### Floor verification

**This pass owns the floor run** per the plan's `### Floor verification scope`. Floor facts
taken from `BUILD.md` `## Floor verification`, its single canonical statement, and never from
memory: the supported floor is **Django 5.2.0 on Python 3.10 with strawberry-graphql
0.316.0**. Worker 3's `/tmp/dsf-floor` was on disk with plausible versions and was
**rebuilt anyway** rather than assumed, as the plan directs. The shared `.venv` was never
mutated - every install carried an explicit `--python /tmp/dsf-floor/bin/python`.

```shell
rm -rf /tmp/dsf-floor
uv venv /tmp/dsf-floor --python 3.10
uv pip install --python /tmp/dsf-floor/bin/python -e . --group dev
uv pip install --python /tmp/dsf-floor/bin/python 'django==5.2.0' 'strawberry-graphql==0.316.0'
uv pip list --python /tmp/dsf-floor/bin/python
/tmp/dsf-floor/bin/python -m pytest tests/test_views.py tests/test_routers.py --no-cov
```

- `uv venv ... --python 3.10` - pass (`Using CPython 3.10.19`).
- `uv pip install ... -e . --group dev` - pass.
- `uv pip install ... 'django==5.2.0' 'strawberry-graphql==0.316.0'` - pass; it **downgraded
  both**, which is the point of the pin: `- django==5.2.16 / + django==5.2` and
  `- strawberry-graphql==0.323.2 / + strawberry-graphql==0.316.0`.
- Resolved versions, as read by `uv pip list --python /tmp/dsf-floor/bin/python`:
  `django 5.2`, `strawberry-graphql 0.316.0`, `asgiref 3.12.1`, `channels 4.3.2`,
  `daphne 4.2.3`, `pytest 9.1.1`, `pytest-django 4.12.0`, `pytest-asyncio 1.4.0`,
  `django-strawberry-framework 0.0.14` (editable, this checkout); interpreter
  `Python 3.10.19`. The floor venv's asgiref (3.12.1) is again **newer** than the shared
  `.venv`'s - the review pass's floor-fact correction holds and is not re-derived.
- `/tmp/dsf-floor/bin/python -m pytest tests/test_views.py tests/test_routers.py --no-cov` -
  **pass, 339 passed** (194 + 145, the same totals as the shared environment).

The two floor questions this pass created, both answered **by execution** rather than by
reading current:

1. **The ContextVar carries the request across the `sync_to_async`-adapted
   `CsrfViewMiddleware.process_view`, and the stamp crosses back on the shared request
   object.** Confirmed: every async row that depends on it passes at the floor - re-run
   individually and named, since a green aggregate is not the answer -
   `::test_installing_the_middleware_parses_no_body_on_either_mount[async]`,
   `::test_the_same_two_mounts_parse_nothing_without_the_middleware_either[async]`,
   `::test_a_declined_callbacks_over_limit_body_never_reaches_the_csrf_class[async]`,
   `::test_a_declined_callback_still_gets_a_complete_csrf_check[async]`,
   `::test_a_chain_with_the_boundary_and_no_csrf_middleware_still_checks_csrf[async]`,
   `::test_the_projects_own_csrf_middleware_runs_when_the_chain_supplies_the_ordering[async]`
   and `::test_the_async_chain_resets_the_ordering_mark_around_the_downstream_call`, all
   **PASSED** at Python 3.10.19 / Django 5.2 / asgiref 3.12.1.
2. **`getattr(callback, "csrf_exempt", False)` is still read for truthiness at Django
   5.2.0**, which is what lets a lazily-evaluated object be the value at all - re-confirmed
   **by the rows** rather than by re-reading upstream, as the plan directs:
   `::test_the_projects_own_csrf_middleware_runs_when_the_chain_supplies_the_ordering[sync]`
   and `[async]` require the new predicate to evaluate false at that read site for the
   deployment's own class to run, and both pass at the floor; the `[/marked-no-view-class/]`
   and `[/marked-bad-initkwargs/]` rows require it to be consulted at all.

### Implementation notes

- **`_package_view_instance` returns the instance rather than a `(view_class, initkwargs)`
  pair** - the plan left the shape to discretion. The instance is what the caller wants and
  makes `process_view`'s branch a single `if view is None`, whereas a pair would put the
  `**` splat back in `process_view`, i.e. back at the site whose unguarded dereference was the
  finding.
- **Ordering of the guard.** The marker is tested first and the two attributes second, in one
  function, so there is one recognition predicate rather than two that can disagree. Both
  attributes are read with `getattr(..., None)` and tested with `isinstance`; there is
  deliberately no `or {}` / `or ()` fallback anywhere in it, because an absent attribute means
  "not a callback whose boundary I can run", which is a `None`, not a default.
  `isinstance(initkwargs, dict)` rather than `Mapping` - it is spliced with `**` and it is
  Django's own `as_view` bookkeeping, which is always a `dict`; widening the accepted type
  would widen the recognized set without widening what can safely be built.
- **`_declared_charset_is_unhonourable` sits immediately before `_form_encoding_is_utf8`**,
  its first caller, among the module-level predicates. Its docstring carries the "absent is
  not a declaration" rule once, and
  `::_enforce_body_charset_declaration`'s docstring now points at it instead of restating it -
  the prose was duplicated in the same way the code was.
- **The two clauses in `__bool__` are deliberately not collapsed** into
  `not getattr(_boundary_middleware_request.get(), _BOUNDARY_ENFORCED, False)`, per A-2. The
  method's own docstring states why in the terms `BUILD.md` uses, so the next reader does not
  "simplify" it back.
- **`tests/test_views.py::_post` gained a `client=` parameter** rather than a second posting
  helper: four of the six new rows need a non-default client and the transport branch is
  already there. The default still builds a fresh client per call, which the docstring now
  states as a requirement rather than an incidental.
- **The marker-dropping wrapper is written without `functools.wraps`** and says so: `wraps`
  copies `__dict__`, so both marks would travel together and the interesting callback would
  not exist. That is also the mitigating fact the finding records, now pinned in a docstring.
- **Docstrings**: every rewritten passage states the invariant and cites `spec-046` decisions
  where the design pointer helps. None names a review round, a finding, a severity, or a
  review document - `docs/feedback.md` is neither edited nor named anywhere in this diff.

### Notes for Worker 3

- **Read `_boundary_ordering.py` as a protocol module, not a constants module.** The two-way
  shared state is the argument for it: `views.py::as_view` writes the marker and the middleware
  reads it, the middleware writes the stamp and
  `views.py::_enforce_request_boundary_once` plus `_CsrfOrderingExemption` read it. The
  relocation proof above is mechanical; what is worth an independent read is whether the
  docstring's statement of the invariant is the one the code enforces.
- **The re-anchor for proof entry 1 is not cosmetic.** DRY (f) invalidated the old anchor, and
  the replacement is a two-line block because the bare `raise` line occurs 4 times in
  `views.py`. Worth re-deriving with `grep -c -F` if you re-run that entry.
- **Entry 3's row set moved without changing size.** Compare sets, not counts, or it reads as
  unchanged. The analysis above names the four rows and why two left and two arrived.
- **Entry 7's prediction was partly wrong and I did not chase it.** The plan expected the
  boundary-only-chain row to fail under that mutant; it does not, because that row's subject is
  the view's CSRF continuation rather than its body enforcement. The row is pinned by entries 3
  and 13. I record this rather than adding a row to make a prediction come true.
- **Fixture traps, now encoded in helpers rather than in comments.** `_csrf_enforcing_client`
  exists because both an enforcing-client-without-a-cookie and a default client stop short of
  the `request.POST` read, either of which turns a parse-ordering assertion into a measurement
  of the fixture. Every row whose witness is that read goes through it, and rows whose witness
  is the CSRF call log deliberately do not.
- **`_marked_callback_with_unusable_initkwargs` carries a real `view_class`** so that only the
  `view_initkwargs` half of the guard stands between `**` and a `TypeError`; the other row's
  callback carries neither attribute. Two shapes, so the guard is not pinned by one.
- **The duplicated-*boundary*-entry case is still deliberately unpinned**, as pass 1 left it and
  R2 owns it; `process_view` still calls `view._enforce_request_boundary` rather than
  `::_enforce_request_boundary_once`, unchanged by this pass and for the plan's stated reason.
- `scripts/review_inspect.py` was **not** re-run this pass. The new module is a
  pure-definitions module (two string constants, one ContextVar, a one-method class, one
  instance) with no control flow and no repeated literal, and Worker 1's existing overview for
  `middleware/request_body.py` is the one file with new logic in it. Recorded as an explicit
  skip with its reason, per `BUILD.md` `### When to run the helper during build`; regenerate it
  if you want the `_package_view_instance` entry in an overview.
- **One docstring-only edit landed in `middleware/request_body.py` after the proof run**, so
  the record is not stale by accident: `__call__`'s docstring lost a `:data:` cross-reference to
  a name that now lives in another module. No executable line changed, and all thirteen
  manifest anchors were **re-verified after it** (`--check-anchors-only`, exit 0, each matching
  exactly once), so every recorded entry is re-runnable as written.

### Notes for Worker 1 (spec reconciliation)

Everything pass 1 and the review pass recorded stands. These are additions, and nothing here
is fixed in this pass.

1. **M-A's re-pin cost is now measured, and the answer is that the row does not break.** W-1
   made this an inherited obligation and the plan's `### Routing confirmations` assigned the
   re-measurement to R3; it was cheap enough to do here, so R3 does not have to guess.
   `docs/builder/temp-tests/r1/test_r1_ma_remeasure.py` drives
   `examples/fakeshop/test_query/test_transport_api.py::test_the_async_view_also_refuses_before_djangos_parser_runs`
   verbatim, with `override_settings(MIDDLEWARE=...)` supplying fakeshop's shipped chain plus
   `GraphQLRequestBodyBoundaryMiddleware` inserted immediately before
   `django.middleware.csrf.CsrfViewMiddleware` - the chain M-A would enact. The row **passes**.
   So the one live row M-A expects to break breaks by exactly the mechanism this fix removes,
   and **R3's re-pin of that row to a fallback-override chain is not required**; only the
   prose corrections and the new shipped-chain assertion M-A also names are. `examples/**` was
   not edited by this pass - the probe is scratch and supplies the chain at runtime.
2. **A new private module exists that no document mentions.** `_boundary_ordering.py` is
   private, unexported, and not consumer-visible, so it needs no spec sentence - but it is one
   row in the script-rendered `docs/TREE.md`, which **R3 regenerates**. Its module docstring
   carries no staging language ("planned", "Slice N", `TODO(`), so the regenerate is
   safe as-is. Also: R3's `docs/README.md` work should describe the withdrawal in the narrow
   form the code now implements - the exemption is false for a request whose boundary a chain
   entry **ran**, not for any request travelling an installed chain. The broad form is the
   sentence the High finding falsified.
3. **A contract sentence R2 should carry, surfaced by the fix rather than by the review.** The
   fallback is now reachable in a state the spec never describes: *the middleware is installed
   and declines a callback it cannot recognize.* Decision 18 should say what that state is, in
   the current-contract voice: a callback the boundary middleware does not recognize keeps its
   exemption, so the view supplies the ordering and Django's stock CSRF class performs the
   check - the class degrades, the ordering does not. That sentence is what makes
   "Both arrangements enforce CSRF and both enforce the cap" true of three states rather than
   two, and it is the property this pass's row pair
   (`::test_installing_the_middleware_parses_no_body_on_either_mount` +
   `::test_the_same_two_mounts_parse_nothing_without_the_middleware_either`) pins.
4. **The plan's entry-7 prediction was wrong in a way worth recording**, since a later reader
   will otherwise re-derive it: `_enforce_request_boundary_once` is not what protects a chain
   carrying the boundary and no CSRF entry. The view's unconditional CSRF continuation is.
   Nothing needs changing; the prediction does.

---

## Review (Worker 3, pass 2)

Re-review of Worker 2's pass-2 diff against `## Plan (Worker 1, pass 2 - revision)`. Read end to
end first: `AGENTS.md`, `START.md`, `BUILD.md`, `ARTIFACT.md`, `worker-3.md`, `docs/README.md`,
`examples/fakeshop/test_query/README.md`, `docs/spec-046-transport_security-0_0_15.md`, its
`-rationale.md`, `docs/builder/build-046-transport_security-0_0_15.md` (`# Closeout cycle (card
046)`: V1-V9, M-A, W-1, D-1), this artifact's pass-1 plan / pass-1 build report / pass-1 review /
pass-2 plan / pass-2 build report, and `docs/builder/worker-memory/worker-3.md`. Worker 0's, 1's
and 2's memory files were not read.

### Independent re-run: the mutations, declared before they were made

Recorded here **before** any edit, per `worker-3.md` `## Scope` and `BUILD.md`
`### Who performs it`. Every mutation below is transient, one at a time, reverted inside this pass,
each revert proved by byte comparison against a pre-mutation copy taken to a scratch path
**outside** the repository. No `git checkout` / `restore` / `stash` / `worktree` anywhere in this
pass; the tree is legitimately dirty with the build's own work.

Scratch root: `<session scratchpad>/w3p2` (outside the repo).

1. **W3-M1, hand-applied, my own witness for the High finding.**
   `django_strawberry_framework/_boundary_ordering.py::_CsrfOrderingExemption.__bool__` - replace
   the two-line body with `return _boundary_middleware_request.get() is None`, i.e. restore the
   shipped defective predecessor ("a boundary middleware is handling this request, therefore
   withdraw"). Run against my own from-scratch probe
   `docs/builder/temp-tests/r1/test_w3p2_parse_witness.py` (its own URLconf, its own mounts, its
   own cap, its own marker-dropping wrapper, its own `MultiPartParser.parse` counter, its own
   enforcing client carrying a token-shaped cookie) plus `tests/test_views.py`. The point is not to
   re-derive entry 13 - it is to establish that **my** probe can exhibit the defect, so its
   all-zero reading on the fixed tree is evidence about the code rather than about my fixture.
2. **The whole thirteen-entry manifest**, re-run mechanically through
   `scripts/prove_failability.py` from Worker 2's own
   `docs/builder/temp-tests/r1/proofs-pass2.json`, at the scopes recorded there
   (`tests/test_views.py` for entries 1-8 and 12-13, `tests/test_routers.py` for 9-11), into my own
   scratch root and my own `--output docs/builder/temp-tests/r1/w3p2-rerun.md`. Worker 2's
   `proofs-pass2.json` / `.md` are **not** overwritten. Each entry's mutation is the one the
   manifest declares and the build report's table quotes; the runner performs the anchor check
   first, one mutation live at a time, and proves each restore by `filecmp.cmp(shallow=False)` plus
   SHA-256.

Both are reverted and proved reverted below under `### Revert proof`.

**W3-M2, declared here before it was made** (a fourteenth mutation, not in Worker 2's manifest,
added because the audit below found a build-report claim that measurement contradicts).
`django_strawberry_framework/views.py #"_csrf_protected_run = csrf_protect(_run_after_csrf_check)"`
and its async twin - drop the `csrf_protect(...)` wrapper from both, so the view's unconditional CSRF
continuation is gone while every other boundary stands. Scope as run: `tests/test_views.py`. The
question it answers is whether the pass's **Medium** row
(`::test_a_chain_with_the_boundary_and_no_csrf_middleware_still_checks_csrf`) is a row that can fail
at all, since it fails under **none** of the thirteen manifest mutants.

### Independent re-measurement of the High finding's own witness

Pass 1's probe table is the strongest evidence in this artifact, so it was re-derived from
scratch rather than accepted. `docs/builder/temp-tests/r1/test_w3p2_parse_witness.py` is a new
file written for this pass, independent of both `tests/test_views.py` and pass 1's
`test_r1_probes.py`: its own URLconf, its own two capped mounts (`max_request_body_bytes=32`),
its own hand-written marker-dropping wrapper (copies `csrf_exempt`, `view_class`,
`view_initkwargs`, not `_BOUNDARY_MARKER`; deliberately not `functools.wraps`), its own
`multipartparser.MultiPartParser.parse` counter wrapped around the real call, and its own
**enforcing** client carrying a token-shaped `csrftoken` cookie — both fixture traps pass 1
named are avoided, so the read the counter observes is reachable.

Measured on the fixed tree, `uv run pytest … -o addopts="" --no-cov -q -s`:

| Mount | Chain | Status | `MultiPartParser.parse` calls |
| --- | --- | --- | --- |
| `/w3-marked/` (stamped) | `[boundary, stock CSRF]` | `413` | **0** |
| `/w3-wrapped/` (marker dropped) | `[boundary, stock CSRF]` | `413` | **0** |
| `/w3-marked/` | `[stock CSRF]` | `413` | **0** |
| `/w3-wrapped/` | `[stock CSRF]` | `413` | **0** |

and the identical four cells on the async mounts. So the property the finding asked for holds:
**installing the middleware no longer changes the answer for either mount.**

**The probe is capable of exhibiting the defect**, which is what makes the zeros evidence about
the code rather than about my fixture. Under **W3-M1** (declared above; `__bool__` reduced to
`return _boundary_middleware_request.get() is None`, the shipped defective predecessor) the same
probe reproduces pass 1's row 2 exactly:

```
  marked   [boundary, stock CSRF]   status=413 parses=0
  wrapped  [boundary, stock CSRF]   status=403 parses=1     <-- the shipped defect
  marked   [stock CSRF]             status=413 parses=0
  wrapped  [stock CSRF]             status=413 parses=0
```

**0 where it was 1, re-derived independently.** Worker 2's claim stands.

### Failability proof audit, and the independent re-run

**Audited: all thirteen records.** Every entry carries the boundary by symbol-qualified path, the
exact mutation, the scope as run, the pre-mutation state of that same scope, the listed node ids,
a separate collection/setup-error count, and a restore proved by `filecmp.cmp(shallow=False)` plus
SHA-256. **Collection/setup errors: 0 on every one of the thirteen** (verified by parsing the
emitted record, not by reading prose). **No entry measured zero rows** — the lowest count in the
record is 2 — so neither the weakly-pinned nor the harness-impossible reading is invoked anywhere,
and the build report says so in those words. **No boundary is weakly pinned** (0 or 1 rows):
lowest is 2. Every mutation removes its boundary rather than perturbing code near it; entry 6's
inserted `return` short-circuits the audit before it reads `MIDDLEWARE`, entry 12 deletes the
`isinstance` conjunct rather than weakening it, entry 13 restores the defective predicate verbatim.

**Re-run: all thirteen, at the scopes Worker 2 recorded**, through
`scripts/prove_failability.py` on Worker 2's own `proofs-pass2.json`, into my own scratch root
outside the repo and my own `--output docs/builder/temp-tests/r1/w3p2-rerun.md` (Worker 2's
`proofs-pass2.json` / `.md` untouched). `--check-anchors-only` first: exit 0, all thirteen anchors
matched **exactly once before any copy was taken**. Full run: **exit 0**. The mandatory floor
(`worker-3.md` "Reading is necessary, not sufficient") is satisfied with room: entries 2, 4, 6, 9,
10, 11 and 12 are at 3 rows or fewer and every one of the thirteen sits on a security decision, so
the floor here is effectively the whole manifest and the whole manifest was re-run. **Nothing was
accepted on Worker 2's record alone.**

**Node-id sets, mine vs Worker 2's — compared as sets, not counts:**

| # | Worker 2 | This pass | set-equal | errors |
| --- | --- | --- | --- | --- |
| 1 | 7 | 7 | yes | 0 |
| 2 | 2 | 2 | yes | 0 |
| 3 | 4 | 4 | yes | 0 |
| 4 | 3 | 3 | yes | 0 |
| 5 | 13 | 13 | yes | 0 |
| 6 | 3 | 3 | yes | 0 |
| 7 | 14 | 14 | yes | 0 |
| 8 | 6 | 6 | yes | 0 |
| 9 / 10 / 11 | 2 / 2 / 2 | 2 / 2 / 2 | yes | 0 |
| 12 | 2 | 2 | yes | 0 |
| 13 | 7 | 7 | yes | 0 |

**Thirteen of thirteen set-equal.** The four movements the build report reports were re-derived
against pass 1's own `proofs.md` and each is exactly as recorded:

- **Entry 13, the load-bearing proof.** 7 rows, and they are the six rows written for the High
  finding plus the re-pinned async row — not an accompanying set. Its mutant **is** the shipped
  defect, and my own W3-M1 (the same mutation, applied by hand against my own probe) independently
  produces the parse-count regression. The two together are what say those rows discriminate the
  fix from its predecessor.
- **Entry 3, 4 -> 4 by losing one pair and gaining another.** Measured: lost
  `::test_the_chain_refuses_an_over_limit_multipart_before_any_csrf_read[sync|async]`, gained
  `::test_the_projects_own_csrf_middleware_runs_when_the_chain_supplies_the_ordering[sync|async]`,
  leaving `{configured-CSRF-class pair, already-measured pair}`. That is the plan's predicted
  survivor set, and the loss is the fix working: with recognition gone the over-limit body is
  caught by the view's own boundary and still answers `413`. A count comparison would have read
  this as "unchanged".
- **Entry 5, 5 -> 13 (+8, none lost)** and **entry 7, 8 -> 14 (+6, none lost)** — confirmed by set
  difference, gains only.
- **Entries 9, 10, 11 set-equal to pass 1's** at 2 rows each: no contamination of the
  `consumers.py` boundaries.

**The two prediction corrections are honest, and I verified no row was added to make a prediction
come true.** Entry 4 did not change against the plan's expectation (its three rows are about the
stamped mount, whose answer the fix does not alter) — confirmed set-equal to pass 1's. Entry 7 did
**not** gain the boundary-only-chain row the plan predicted — confirmed: that node id appears in
entry 7's set in neither pass. See Low finding 2 for what it *is* pinned by, which is not what the
build report says.

**One disclosure audited rather than taken on faith.** Worker 2 records a docstring-only edit to
`middleware/request_body.py` landing *after* its proof run. Its recorded pre-mutation SHA for that
file (`0c022a860cb31d6e`) accordingly differs from mine (`0627ab89a4a8381b`) — which is what a
post-run edit looks like, and the reason to distrust the record. What settles it is that my re-run
against the **current** bytes produced set-equal node ids for all four entries that mutate that
file (3, 6, 12, and the `setattr` site's readers), all thirteen anchors still match exactly once,
and the focused scope is green. A behavioural change in that edit could not have left every set
identical. The disclosure is accurate and the record is re-runnable as written.

### Revert proof

Two hand-applied mutations, both mine, both reverted inside this pass, each proved by byte
comparison against a pre-mutation copy taken to `<session scratchpad>/w3p2` (outside the repo):

- **W3-M1** (`_boundary_ordering.py`): `cmp` exit **0**; SHA-256
  `b2c25d9a66a6090c…` on both sides — which is also the value Worker 2's record carries for that
  file, so the tree I reviewed is byte-identical to the tree it proved against.
- **W3-M2** (`views.py`): `cmp` exit **0**; SHA-256 `e8aeb156550fc45a…`, likewise matching Worker
  2's record.

The mechanized run restored its own five targets and proved each restore itself; re-measured after
the fact, every one matches the pre-mutation reference its own record names:
`views.py e8aeb156550fc45a`, `middleware/request_body.py 0627ab89a4a8381b`,
`_boundary_ordering.py b2c25d9a66a6090c`, `_request_body.py 2c1fd48618d4b01c`,
`consumers.py 1bdf298c473fd1a0`. No `ACTIVE-MUTATION.json` and no `RESTORE-FAILED.json` anywhere
under the scratch root. `git status --short` after everything is the eight-entry baseline,
unchanged, and `git diff --cached --name-status` is still exactly
`A django_strawberry_framework/_boundary_ordering.py` — the one path W-1 authorizes. No `git`
checkout / restore / stash / worktree was used at any point; no `--cov*` flag was passed to any
`pytest` invocation.

Post-revert green: `uv run pytest tests/test_views.py tests/test_routers.py --no-cov` —
**339 passed**.

### Relocation and extraction: verified, not read

`BUILD.md` `## Claims are proven mechanically, never accepted on prose`, second shape. Pristine
`HEAD` obtained read-only with `git show HEAD:<path>` into a scratch path outside the repo.

- **Both attribute *string values* are byte-identical to `HEAD`'s** — the load-bearing half,
  because a changed string silently unpairs the writer from the reader.
  `_BOUNDARY_MARKER = "graphql_request_body_boundary"` and
  `_BOUNDARY_ENFORCED = "graphql_request_body_boundary_enforced"`, compared as whole statements.
- **`_CsrfOrderingExemption` is AST-identical to `HEAD`'s modulo the one authorized delta.**
  Method: parse both class bodies, strip every docstring node, substitute `HEAD`'s `__bool__` body
  into the new class, compare `ast.dump`. **Equal with the substitution, unequal without it**, and
  the sole difference localizes to `__bool__`'s body. `_CSRF_ORDERING_EXEMPTION =
  _CsrfOrderingExemption()` is byte-identical.
- **The ContextVar carries exactly the three deltas A-1 specifies and nothing else**: name
  (`_boundary_middleware_active` -> `_boundary_middleware_request`), annotation
  (`ContextVar[bool]` -> `ContextVar[HttpRequest | None]`), the var-name string, and
  `default=False` -> `default=None`.
- **A move, not a copy.** `grep -rn -F` over `django_strawberry_framework/` returns exactly one
  hit each for `_BOUNDARY_MARKER =`, `_BOUNDARY_ENFORCED =`, `class _CsrfOrderingExemption` and
  `_CSRF_ORDERING_EXEMPTION =`, all four in `_boundary_ordering.py`, and **zero** hits anywhere in
  the repository for `_boundary_middleware_active`.
- **The layering inversion is gone.** `grep -rn 'middleware.request_body import'
  django_strawberry_framework/` and `grep -rn 'import views' django_strawberry_framework/middleware/`
  both return nothing. Verified further by execution: exec'ing `_boundary_ordering.py` in a fresh
  interpreter adds **no** `django*` module to `sys.modules` — the docstring's "imports nothing but
  the standard library" is true at runtime, `HttpRequest` being under `TYPE_CHECKING`.
- **DRY (f) is behaviour-preserving.** `HEAD` carried the two lines verbatim at both sites; the
  extracted `_declared_charset_is_unhonourable` returns that same condition, `(request.content_params
  or {})` included, and both call sites now read it. Both replaced sites' surrounding logic is
  otherwise untouched in the diff.
- **`consumers.py` is byte-identical to `HEAD`** (`cmp` against `git show HEAD:…`, exit 0). No
  contamination.

### High:

None.

The pass-1 High is **answered**, and answered at the level it was raised: not by widening
recognition (an input-spelling fix the plan rejected in writing) but by keying the withdrawal off
the `_BOUNDARY_ENFORCED` stamp, so the answer being guarded is *has the boundary run for **this**
request*. Verified state by state against the code rather than against A-2's table (below).

### Medium:

None.

The pass-1 Medium is **answered**:
`tests/test_views.py::test_a_chain_with_the_boundary_and_no_csrf_middleware_still_checks_csrf`
drives a real request through `_chain([_BOUNDARY_MIDDLEWARE_PATH])` on both transports and both
client strictnesses, and the docstring states why a default client would make the assertion say
nothing. I confirmed the row is not vacuous by mutation rather than by reading — see Low 2.

### Low:

#### `_package_view_instance` guards the *shape* of the bookkeeping, not the answer — a marked callback whose `view_initkwargs` is a `dict` the class rejects still raises out of `process_view`

`middleware/request_body.py::_package_view_instance` now tests
`isinstance(view_class, type) and isinstance(initkwargs, dict)` and then splats. A `dict` whose
keys the class rejects passes both tests, so `view_class(**initkwargs)` raises and the hook answers
an unhandled `500` — the exact outcome the guard was added to prevent, and the outcome
`middleware/request_body.py`'s own module docstring rules out ("a hook whose every other outcome is
a controlled response", restated in `_package_view_instance`'s docstring).

Measured, not reasoned. `docs/builder/temp-tests/r1/test_w3p2_unbuildable_instance.py` mounts a
callback carrying `_BOUNDARY_MARKER`, `view_class = DjangoGraphQLView` and
`view_initkwargs = {"not_a_view_kwarg": 1}` on `[boundary, stock CSRF]`:

```
django_strawberry_framework/middleware/request_body.py::_package_view_instance
    return view_class(**initkwargs)
TypeError: BaseView.__init__() missing 1 required positional argument: 'schema'
ERROR django.request: Internal Server Error: /w3-bad-dict/
```

This is `BUILD.md` `### Fail-open shapes`'s own rule applied to the recognizer: the guard is
written against two **spellings** of the incoherent input (attribute absent; attribute not a
`dict`) and the answer it is supposed to produce — *the instance whose boundary I can run, or
`None`* — is left unguarded for the third. A-2 makes precisely this argument for `__bool__` and it
was not carried across to the sibling helper the same pass added. Note that pass 1's own
recommended change was itself written against a spelling ("treat a missing one as 'not ours'"), so
the finding's origin is partly the review's; the rule is the standard either way.

**Severity Low, for the reason pass 1 graded the original Low**: not reachable through any
supported seam (the marker name is package-specific, and Django's `View.as_view` validates
`initkwargs` at `as_view` time, so a genuine package mount cannot carry a rejected `dict`). It
fails **loud**, not open: nothing reaches the schema and no body is parsed, because `process_view`
raises before the CSRF entry's own `process_view` runs. So Low (b) is **partially** answered — two
of three shapes refused.

**Recommended change**, either of two, and the second is a legitimate close:

1. Guard the answer: attempt the construction inside `_package_view_instance` and treat a failure
   to produce an instance as `None`, i.e. "not a callback whose boundary I can run". A narrow
   `except TypeError` there is not the `BUILD.md` bare-except shape — the construction *is* the
   check, and its failure arm is the safe fallback rather than a permit. It masks no real
   misconfiguration, because `as_view` already rejects bad kwargs for a genuine mount.
2. Record an intentional rejection and **narrow the two docstring claims** so the module no longer
   promises a controlled response for a forged callback. Whether the package owes one at all is a
   contract call, not a builder's.

**Test expectation** for path 1: extend
`::test_a_marked_callback_the_middleware_cannot_build_is_declined_not_crashed` with a third
parametrization — a marked callback whose `view_initkwargs` is a `dict` the class rejects — and add
the widened guard to the manifest so it is proved rather than asserted. Proof entry 12's current
anchor and its two rows survive either way. The probe file above is the promotion source.

#### The build report's attribution of the Medium row to entries 3 and 13 is false as measured

`### Notes for Worker 3` and the entry-7 analysis both state that
`::test_a_chain_with_the_boundary_and_no_csrf_middleware_still_checks_csrf` "is pinned by entry 3's
and entry 13's mutants instead, not by this one." Measured across all thirteen entries of my own
re-run, that node id appears in **no** entry's failing set — not entry 3's, not entry 13's, not
any.

It is not unpinned; it is pinned by a boundary that is not in this manifest. Under **W3-M2**
(declared above; `csrf_protect(...)` dropped from both `_csrf_protected_run` and
`_csrf_protected_async_run`, so the view's unconditional CSRF continuation is gone) it fails on
both transports, in a 5-row set with 0 errors:

```
FAILED tests/test_views.py::test_each_csrf_continuation_matches_the_transport_it_protects
FAILED tests/test_views.py::test_a_declined_callback_still_gets_a_complete_csrf_check[sync]
FAILED tests/test_views.py::test_a_declined_callback_still_gets_a_complete_csrf_check[async]
FAILED tests/test_views.py::test_a_chain_with_the_boundary_and_no_csrf_middleware_still_checks_csrf[sync]
FAILED tests/test_views.py::test_a_chain_with_the_boundary_and_no_csrf_middleware_still_checks_csrf[async]
```

So the row is a real bound and the Medium finding is genuinely closed; what is wrong is the record
of *which* boundary it bounds. That matters because the sentence is the only thing standing between
a later reader and "this row is unpinned" — and because the true answer is the more interesting
one: the boundary-only chain is protected by the view's `csrf_protect` continuation, which is
exactly what the build report's own note 4 to Worker 1 says and what its proof analysis contradicts
two paragraphs earlier. **No proof obligation is missed** — that continuation is not new in this
pass, so it owes none — and `BUILD.md` `### What needs a proof` scopes the obligation to new
boundaries.

**Recommended change.** Correct the two sentences (a build-report correction is a re-pass's to
make, or Worker 1's to record at final verification), naming
`views.py #"_csrf_protected_run = csrf_protect(_run_after_csrf_check)"` as the boundary the row
bounds. Optionally add it to the manifest as a fourteenth entry, since W3-M2 shows it measures 5
rows cleanly. No code change.

#### `_declared_charset_is_unhonourable`'s docstring is the only place `spec-046` Decision 10 is now cited for the `utf-8-sig` refusal

`views.py::_enforce_body_charset_declaration`'s docstring correctly stops restating the rule and
points at the helper (DRY (f) done right — the prose was duplicated the same way the code was).
The consequence is that the `utf-8-sig` / Decision 10 justification now lives only on the
module-level predicate, one screen away from the method that raises the `400`. Purely a
readability observation on a fix I otherwise like; no contract is unstated and nothing is wrong.
Recorded rather than raised as a change request — the alternative (restating it in both places) is
the duplication the extraction removed.

### Nine-state walk: against the code, not against A-2's table

Every row re-derived by reading `middleware/request_body.py::GraphQLRequestBodyBoundaryMiddleware`
(`__call__` / `__acall__` / `process_view`), `_boundary_ordering.py::_CsrfOrderingExemption.__bool__`,
`views.py::_RequestBodyBoundaryMixin.as_view` / `::_enforce_request_boundary_once`, and Django's
`CsrfViewMiddleware.process_view`. `__bool__` returns `False` **only** when the ContextVar holds a
request *and* that request carries the stamp; the stamp has exactly one writer
(`process_view #"setattr(request, _BOUNDARY_ENFORCED, True)"`, confirmed by a package-wide grep on
both the constant and its string value), written only after `view._enforce_request_boundary`
returned. Every other state is the fallback.

1. **Not installed** — var `None` -> `True`; view orders, stock class checks. Pinned by
   `::test_without_the_middleware_the_view_keeps_its_own_ordering_and_exemption` (entry 5, 2 rows).
2. **Installed, marked callback, boundary ran** — var set, stamp `True` -> `False`; configured
   class checks behind the boundary, and `_enforce_request_boundary_once` skips the second measure.
   Pinned by `::test_the_projects_own_csrf_middleware_runs_when_the_chain_supplies_the_ordering` and
   `::test_the_view_does_not_measure_a_body_the_chain_already_measured` (entry 3, 4 rows).
3. **Installed, marker-less callback** — the fix. `True` -> fallback. Pinned by the new row pair and
   independently re-measured above.
4. **Installed, marked but unbuildable callback** — `True` -> fallback, for the two shapes the guard
   covers (entry 12, 2 rows). **The third shape raises instead** — Low finding 1.
5. **Installed, non-package view** — `csrf_exempt` absent, never consulted; Django's own default.
   Pinned by `::test_the_middleware_passes_a_non_package_view_through_untouched`.
6. **Installed, boundary refused** — `process_view` returns a response, so Django never reaches the
   CSRF entry's `process_view`. Pinned by the `413` rows with the empty CSRF call log.
7. **Two adjacent boundary entries** — token-nested set/reset; stamp after the first; `False`. The
   second entry re-measures the body, because `process_view` calls
   `view._enforce_request_boundary` rather than `::_enforce_request_boundary_once`. A cost, not a
   correctness break, deliberately unchanged and routed to R2 with a stated reason.
8. **`[boundary, csrf, boundary]`** — refused at startup; pinned by
   `::test_the_first_csrf_entry_is_the_one_the_ordering_is_measured_against` (entry 6, 3 rows).
9. **A middleware that substitutes the request downstream** — the one row that could put a stale
   stamped request in the var while an unmeasured one reaches the parse. **Driven rather than
   reasoned**: `docs/builder/temp-tests/r1/test_w3p2_substituted_request.py` inserts a middleware
   that rebuilds a second `WSGIRequest` from the same environ and hands it downstream, in both
   positions relative to the boundary entry, and asserts the substitution really happened (distinct
   object ids recorded). All three chains answer `413` with **0** parses:

```
[boundary, csrf]                 -> status=413 parses=0 substitutions=[]
[boundary, substitute, csrf]     -> status=413 parses=0 substitutions=[(4496844880, 4496845200)]
[substitute, boundary, csrf]     -> status=413 parses=0 substitutions=[(4496919600, 4496919904)]
```

The mechanism is that Django runs **every** `process_view` with the one request that reaches
`_get_response`, so the request the boundary stamps is always the request the CSRF entry judges;
a substitution upstream of `_get_response` desynchronizes the ContextVar from that request and the
predicate then answers `True`, which is the fallback. **Row 9 holds, by execution.**

**The one state A-2's table does not list, recorded because I looked for it and it is not
closable at that read site.** A nested Django handler invoked from inside a boundary-handled
request, whose own chain carries a CSRF entry but **not** the boundary entry, would read the outer
request out of the ContextVar (stamped) while judging an inner request (unmeasured), and would
withdraw. `__bool__` receives no arguments — Django reads
`getattr(callback, "csrf_exempt", False)` with no request in hand — so the ContextVar is the only
channel available and no predicate shape can distinguish that case. It is strictly narrower than
both `HEAD` and the defective predecessor (which withdrew for *every* request on an installed
chain), needs a hand-built partial handler rather than any supported seam, and `django.test.Client`
does not produce it (it builds the project's full chain, so `__call__` re-sets the var). Not a
finding; recorded so the next reader does not re-derive it, and noted for R2 below.

### Fail-open shape hunting: the new and changed surfaces

`BUILD.md` `### Fail-open shapes`. Read for the shape wherever this pass computes an input to a
limit, a size, a permission decision, or a rejection — not only where it fixed one.

1. **`getattr(request, _BOUNDARY_ENFORCED, False)` in `__bool__`** — now on the **decision path**
   rather than beside it, so re-derived from scratch. The fail-open direction is a request arriving
   pre-stamped without the boundary having run. Writers: exactly one
   (`process_view #"setattr(request, _BOUNDARY_ENFORCED, True)"`), confirmed by grepping both the
   constant and the string value `graphql_request_body_boundary_enforced` across the whole
   repository — one writer, three readers (`__bool__`, `_enforce_request_boundary_once`, tests).
   Client-controlled input cannot set an attribute on `HttpRequest` (headers become `META` keys) and
   nothing in Django writes a same-named attribute. A consumer middleware *could* set it — that is
   deliberate and unchanged from `HEAD`. **Not a finding.**
2. **`request is None` as the first clause** — two named cases rather than one `getattr` on a
   possibly-`None` receiver, which is the catalogue shape the plan explicitly refused to write. Both
   arms answer the fallback. The method's docstring states why, so the next reader does not
   "simplify" it back. **Not a finding — and the right call.**
3. **`_package_view_instance`'s two `getattr(..., None)` defaults** — the defaults stand in for
   meaningful absence *deliberately*, and the answer produced is `None` = decline = fallback, which
   after A-2 is the safe arm rather than a bare pass-through. No `or {}` / `or ()` anywhere in it,
   as the plan required. **The guard's coverage is the finding, not its direction** — Low 1.
4. **`(request.content_params or {})` in the extracted helper** — unchanged from `HEAD` and still
   benign: `HttpRequest._set_content_type_params` assigns `content_params` unconditionally from
   `parse_header_parameters`, which returns a `dict`, so the `or {}` arm is unreachable and both
   branches yield the same answer. **Not a finding.**
5. **`_declared_charset_is_unhonourable`'s own answer** — `declared is not None and not
   _canonicalizes_to_utf8(declared)`. An unknown codec makes `_canonicalizes_to_utf8` answer
   `False`, so the helper answers `True` and the request is refused; absent answers `False` and
   leaves the strict decode as the contract. The refusing direction is the "cannot resolve"
   direction. **Not a finding.**
6. **The `try` / `except HTTPException` in `process_view`** — narrow, on the package's own exception
   type, and it converts the raise into the identical `text/plain` response upstream's `dispatch`
   produces. Not an over-broad except around a check. **Not a finding**, and pass 1's item (e)
   already confirmed the two shapes agree.
7. **The set-token / reset-in-`finally` around the downstream call** — unchanged in structure; the
   `finally` is what makes the var request-scoped, and the async twin exists because a synchronous
   `finally` would reset before the CSRF middleware read it. Pinned by
   `::test_the_async_chain_resets_the_ordering_mark_around_the_downstream_call`, which now asserts
   both predicate clauses plus the reset in one row (entries 4, 5 and 13 all fail it). **Not a
   finding.**

### DRY findings

**(a) — pass 1's escalation, resolved and verified.** The layering inversion is gone, measured
three ways: neither module imports the other, `_boundary_ordering.py` pulls in no `django*` module
at runtime, and `views.py`'s import section now reaches only `_boundary_ordering`, `_request_body`,
`conf` and `exceptions`. A-1 also removed the *manufactured* constraint that forced pass 1's item
(c) verdict, and correctly declined to act on that in the same pass as a security fix, naming the
condition that would justify revisiting it. `middleware/__init__.py`'s "importing the leaf module
is the soft-dependency opt-in" sentence is true of both leaves again.

**(b) `_boundary_ordering.py` as a new module — no existence challenge raised, and here is the
ground for not raising one.** It has two real importers, not one, and the state it owns is
genuinely bidirectional (`views.py::as_view` writes the marker, the middleware reads it; the
middleware writes the stamp, `views.py::_enforce_request_boundary_once` and `__bool__` read it).
Deleting it and inlining would require one of the two modules to import the other, which is the
cost A-1 paid to remove. Nothing here is a token, fingerprint, or registry with one caller.

**(c) `_declared_charset_is_unhonourable`** — two call sites, single responsibility, name adopted
from the finding, body token-identical to the two lines it replaces. Exactly the shape recommended.
No third copy exists: `grep -n 'content_params' django_strawberry_framework/` shows the read is now
named once.

**(d) `_package_view_instance`** — one caller, which pass 1's DRY heuristic would flag; justified
anyway, because it is the answer the hook branches on and a proof needs a symbol to anchor to
(entry 12 does). Not an early extraction hiding readable logic; it replaced an unguarded
dereference at the call site.

**(e) Repeated string literals across the three files, measured by the helper rather than by eye:**
`_boundary_ordering.py` **0**, `middleware/request_body.py` **0**. No convergent literal was
introduced by the move. No new duplication found anywhere in the diff.

### Non-weakening checks

- **Nothing was weakened to buy a number back.** The only structural change on the hot path is
  `__call__` setting the var to a request instead of `True`; the guard was *widened*, not narrowed.
- **The fallback arrangement is byte-for-byte the pre-`2701f41a` behaviour** for a chain without the
  middleware: entry 5's mutant (`return False`) fails
  `::test_without_the_middleware_the_view_keeps_its_own_ordering_and_exemption` on both transports,
  so it is pinned rather than assumed.
- **Exactly one complete CSRF check, in all three arrangements.** Recognized: the chain's configured
  class runs and the view's continuation is the no-op `csrf_processing_done` makes it. Declined and
  not-installed: the chain skips and the view's `csrf_protect` runs. W3-M2 shows removing the
  continuation costs 5 rows, i.e. the "one check" claim is bounded in both directions.
- **Pass 1's non-weakening check 3 (the *ordering* half), which the High finding broke, is
  restored** — that is what the new row pair asserts and what my parse counter re-measures.
- **Low (c)'s routing held and no method scope was smuggled in.**
  `views.py::_enforce_body_charset_declaration #"if request.method == \"GET\" or
  _is_multipart_form_post(request)"` is **character-identical to `HEAD`'s** (compared against
  `git show HEAD:…`), and proof entry 2's anchor and 2-row set survive unchanged. The GET/HEAD
  asymmetry is untouched, as R2 requires.
- **Pass-1 Low (a) is still docstring-only.** `_request_body.py`'s AST with every docstring node
  stripped is **identical to `HEAD`'s** (`ast.dump` comparison); raw bytes differ. Entry 8's anchor
  and 6-row set are unchanged.

### Dispatched findings checklist walk

- **Box 2** (the CSRF-class finding) is ticked `- [x]` by this pass, and the tick is **warranted**:
  the box's contract is "an over-limit multipart is refused before parsing while an under-limit
  request reaches and obeys the project's own `CsrfViewMiddleware` subclass", and until this pass
  that contract was false for a marker-less callback. It is now true for every state I walked, and
  the entry-13 mutant proves the rows discriminate it. The box's recorded deliberate deviation
  (conditional withdrawal rather than removal of the exemption) is still a deviation and is still
  the right one; A-2's fallback is what preserves an unedited `MIDDLEWARE`.
- **Boxes 1, 3, 4** stay `- [ ]`, with the deferral recorded at plan level twice (pass-1 plan's
  checklist preamble and pass-2 plan `### Routing confirmations`): their contracts landed in
  `2701f41a` / `ba66ab49`, not in a Worker 2 diff, so Worker 1 ticks them at final verification
  where a tick means *landed **and** audited*. That is a recorded deferral, not a silent one — no
  Medium finding. Box 1's `views.py` site is touched by this pass only for DRY (f), which the plan
  states is not part of box 1's contract; I agree, and the box's own contract (the refusal, its
  reason string, the alias matrix) is unchanged and still pinned by entry 1's 7 rows.
- No box is ticked without a matching fix.

### Public-surface check

`git diff HEAD -- django_strawberry_framework/__init__.py` is **empty**: `__all__` and the
re-export list are unchanged. Measured against **spec Decision 5** rather than against "no API
breakage": Decision 5's `What is explicitly *not* broken` list (the router symbol name and import
path, the soft-`channels` guard, the PEP 562 lazy export shape, the WebSocket composition, the
schema pass-through, the Channels adapter read path) is untouched by this diff, and the diff
introduces no new break of its own. `_boundary_ordering.py` is private by design and confirmed so:
no `__all__` (every name underscore-prefixed), no `__init__.py` export in either the package root
or `middleware/`, and no reference to it from any public surface.
`middleware/request_body.py`'s `__all__` is still the single-name tuple
`("GraphQLRequestBodyBoundaryMiddleware",)`, and the documented `MIDDLEWARE` string
`django_strawberry_framework.middleware.request_body.GraphQLRequestBodyBoundaryMiddleware` is
unchanged — so no consumer's settings line moves.

### Static inspection helper

Run this pass, all three with `--output-dir docs/shadow` as every build-cycle invocation must:

```shell
uv run python scripts/review_inspect.py django_strawberry_framework/_boundary_ordering.py --output-dir docs/shadow
uv run python scripts/review_inspect.py django_strawberry_framework/middleware/request_body.py --output-dir docs/shadow
uv run python scripts/review_inspect.py django_strawberry_framework/views.py --output-dir docs/shadow
```

No skips. Worker 2's recorded skip is its own and is fine — `BUILD.md` `### When to run the helper`
puts the review-time obligation on Worker 3, and Worker 2 "may re-run".

- **Django / ORM markers: `_boundary_ordering.py` 0, `middleware/request_body.py` 0.** Nothing to
  justify on either, and no ORM surface was introduced.
- **Repeated string literals: 0 and 0.** Compared across all three overviews since the pass moved
  names between modules; no literal appears in two of them.
- **Control-flow hotspots: 0** in the new module.
- **Calls of interest**, walked: `_boundary_ordering.py` has one, the `getattr` in `__bool__`
  (item 1 above). `middleware/request_body.py` has `3x getattr`, `3x isinstance`, `2x issubclass`,
  `1x setattr` — the `setattr` is the stamp's single writer, two `getattr`s plus two `isinstance`s
  are `_package_view_instance`'s recognition, and the `issubclass` pair is
  `_require_boundary_before_csrf`'s compare-by-class audit (pinned by entry 6's 3 rows, including
  the subclass row).
- **Imports**, compared across the three: the cross-folder import that used to run
  `views.py` -> `middleware/request_body.py` is gone; `_boundary_ordering.py`'s only django-shaped
  import (`from django.http import HttpRequest`) sits inside the `if TYPE_CHECKING` block, which the
  helper lists flat and which I confirmed by execution. Dependency direction is now one-way from
  both importers into the protocol module.

Original-source line numbers cited throughout; no shadow-file line number appears in this review.

### Hot-path budget

**The numbers exist, all three metrics, before and after, and the metric is the same experiment on
both arms.** That is the whole of my obligation; whether the cost is acceptable is the maintainer's
call, and no boundary was weakened to buy any of it back.

- **Same-experiment check, metric 3.** `docs/builder/temp-tests/r1/test_r1_hotpath_predicate.py`
  **detects which shape the tree carries** (`_boundary_ordering` import succeeds -> `SHAPE=request`;
  falls back to `middleware.request_body` -> `SHAPE=bool`) and runs the identical
  `timeit(lambda: bool(_CSRF_ORDERING_EXEMPTION), number=200_000)` either way, in the same two
  ContextVar states. So the iteration count, the statistic and the measured expression are identical
  across the two captures by construction — only the value `__call__` would set differs, which is
  what the rewrite changes. This is the right shape for a before/after and it is why the two arms
  are comparable rather than two experiments.
- **Reproduced as recorded** (after-arm; the before arm is `HEAD` and is by construction no longer
  runnable, which is why the plan's step 0 ordered it first). Two independent runs of my own:
  active state **0.0720** and **0.0741** us/call against the recorded 0.0694-0.0778; var unset
  **0.0551** and **0.0572** against the recorded 0.0513-0.0624; `_declared_charset_is_unhonourable`
  **0.0528** and **0.0581** against the recorded 0.0549-0.0584. Every reading lands in the recorded
  band.
- **Metric 1 reproduced**: `docs/builder/temp-tests/r1/test_r1_hotpath.py` unmodified, 400
  iterations after a discarded warm-up, median, both arms — installed median **302.83 us** against
  the recorded 309.06-315.08, with the CSRF-only control at 298.31 us in the same capture. Same
  snippet, same iteration count, same statistic as the before capture.
- The recorded `+25 ns` on the active-state read is therefore a real, reproducible number sitting
  next to the change that caused it, on a request that costs ~313 us. Recorded; not judged.

### Floor verification

**The floor run happened as declared, and I re-ran it.** Floor facts taken from `BUILD.md`
`## Floor verification`, its single canonical statement, never from memory: the supported floor is
**Django 5.2.0 on Python 3.10 with strawberry-graphql 0.316.0**.

- `/tmp/dsf-floor/bin/python -V` -> **Python 3.10.19**.
- `uv pip list --python /tmp/dsf-floor/bin/python`, read rather than recalled: **django 5.2**,
  **strawberry-graphql 0.316.0**, asgiref 3.12.1, channels 4.3.2, daphne 4.2.3, pytest 9.1.1,
  pytest-django 4.12.0, pytest-asyncio 1.4.0, `django-strawberry-framework 0.0.14` editable at this
  checkout. Every version matches the build report's record exactly.
- `/tmp/dsf-floor/bin/python -m pytest tests/test_views.py tests/test_routers.py --no-cov` —
  **339 passed**, my own run, matching the declared 339 (194 + 145).
- **The shared `.venv` is unmutated**, which is the claim most worth checking: `uv pip list` reads
  **django 6.0.5**, asgiref 3.11.1, and `.venv/bin/python -V` is **Python 3.14.2** — i.e. still far
  above the floor, so no floor install leaked into it.
- Both floor questions the plan created are answered by **execution** rather than by reading, as it
  required, and the async rows are named individually rather than hidden inside a green aggregate.
  The propagation question is the substantive one and the async rows carry it.

### Test-staleness sweep

Run independently, never against the artifact's file list (`worker-3.md`: the tree it missed is by
definition the one that cannot appear in the diff).

- **No example-model field set changed and no wire shape converted**, so neither
  `BUILD.md` shape applies.
- **The module move's stranded-importer sweep**, the one this pass could actually strand:
  `grep -rn '_boundary_middleware_active\|_CSRF_ORDERING_EXEMPTION\|_BOUNDARY_MARKER\|_BOUNDARY_ENFORCED'
  --include='*.py' .` over the whole repository. Every hit outside
  `django_strawberry_framework/` is in `tests/test_views.py` and reads from
  `django_strawberry_framework._boundary_ordering`; `_boundary_middleware_active` has **zero** hits
  anywhere. No stranded importer in any of the three test trees, and none in `scripts/`.
- **`csrf_exempt` readers across all three trees**, since the pass changes what
  `bool(view.csrf_exempt)` answers in flight: the only in-flight readers are in
  `tests/test_views.py` (re-pinned) and `examples/fakeshop/test_query/test_transport_api.py`'s
  probe wrapper, whose prose staleness is **R3's under M-A** and unchanged here.
  `::test_the_view_callback_of_both_views_carries_the_csrf_exempt_mark` reads the mark outside any
  request, where the var is unset, so `True` is still correct **and** still discriminating (entry 5
  fails both its parametrizations) — the plan's test item 6 check, confirmed.
- **Live tier green against the fixed code, my own run**:
  `uv run pytest examples/fakeshop/test_query/test_transport_api.py --no-cov` — **69 passed**.
- **M-A's re-pin re-measurement independently confirmed.**
  `docs/builder/temp-tests/r1/test_r1_ma_remeasure.py` — **1 passed** on my run. I checked the row
  it drives builds a **fresh** `AsyncClient` per request, so the `override_settings` chain is the
  one actually exercised rather than a cached one; the probe is therefore valid and the row M-A
  expects to break does not break. R3 does not need the fallback-override move for that row.
- No `--cov*` flag was used in any run in this pass; every invocation carried `--no-cov`.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

The diff's only doc/generated surface is `examples/fakeshop/apps/kanban/constants.py`, and W-1
authorizes it.

- **Regenerated by its script, not hand-edited — proved, not assumed.** I copied the file aside,
  re-ran `uv run python scripts/build_kanban_tracked_path_constants.py`, and `cmp`'d: **byte-stable**.
  A hand-edit would have been reverted by that render.
- **Exactly one added line, in alphabetical position, and nothing else moved.** The diff is
  `+1/-0`; parsed, `TRACKED_FILE_PATHS` holds **281** paths and is fully sorted, with
  `django_strawberry_framework/_boundary_ordering.py` between `__init__.py` and
  `_cross_web_patches.py`.
- **The new module's docstring carries no staging language** — `grep -iE
  'planned|slice [0-9]|TODO\(|coming soon'` over both changed production modules returns nothing —
  so **R3's `docs/TREE.md` regenerate is safe**. Verified end to end rather than by inspection: I
  rendered `docs/TREE.md` into a scratch copy, confirmed the render succeeds and adds exactly
  `├── _boundary_ordering.py  # The two marks the request-body boundary's ordering is negotiated
  with.` in both tree blocks, then **restored the original bytes** — `git status --short
  docs/TREE.md` is empty, since `docs/TREE.md` is R3's file and not this pass's. The same render
  also surfaces two pre-existing drifts (`middleware/request_body.py` absent, `utils/sessions.py`'s
  docstring) which are V5's and R3's, not this pass's.
- **No process provenance anywhere in the diff.** `git diff HEAD -- django_strawberry_framework
  tests examples` filtered for added lines mentioning a review document, round, finding, severity,
  artifact filename or worker returns **nothing**; `docs/feedback.md` is neither edited, annotated,
  nor named. The `spec-046 Decision N` pointers that remain are the legitimate kind and stay.
- `scripts/check_trailing_commas.py --check` exits 0 on all five changed paths (ASCII-only, line
  length, trailing-comma layout); `ruff format --check` reports the four source files already
  formatted; `ruff check` over `django_strawberry_framework/` and `tests/test_views.py` passes.
  The generated constants file was checked read-only, correctly — a write-mode ruff run on it would
  be a hand-edit of rendered output.

### What looks solid

- **The fix answers the question I asked, not the question that was easiest to answer.** A-2 names
  the answer being guarded in the plan's own words, enumerates nine states, and explicitly rejects
  the recognition-widening alternative *as* an input-spelling guess. I re-derived all nine against
  the code and drove the one I most distrusted (row 9, the substituted request). The predicate's
  failure mode in every state I could construct is the fallback, i.e. it degrades the CSRF *class*
  and never the *ordering* — which is the trade the finding asked for by name.
- **A-1 turned a review escalation into a real structural improvement rather than a placement
  shuffle**, and its rejected alternatives are recorded with reasons, including a correction of my
  own pass-1 cost estimate (the `django.middleware.csrf` import cost I attributed to the status quo
  was not real, measured by execution — I re-derived that and it is right).
- **The relocation proof is the strongest in this artifact.** "I only moved it" is `BUILD.md`'s
  cheapest claim and this one is proved on the executable token stream with the one authorized delta
  substituted in, plus a grep that the move is not a copy, plus the two string values byte-compared
  because those are what pair the writer to the reader.
- **The proof pass is honest where honesty costs something.** Two predictions are recorded as wrong
  (entry 4 did not change; entry 7 did not gain the predicted row) with the mechanism explained and
  **no row added to make either come true** — I verified both by set difference. The
  after-the-proof-run docstring edit is disclosed rather than hidden, and it is the disclosure that
  let me check it.
- **The fixture traps are encoded in a helper rather than a comment.** `_csrf_enforcing_client`'s
  docstring names both traps and every row whose witness is the `request.POST` read goes through it,
  while rows whose witness is the CSRF call log deliberately do not. That is the difference between
  a lesson learned and a lesson kept.
- **The new module reads as a protocol, and the invariant its docstring states is the one the code
  enforces** — I checked that specifically, since it is what the build report asked me to check
  independently. "The stamp has one writer" is true by grep; "an absent stamp means the view still
  owns the ordering" is true by the predicate; "installed is a property of the chain, ordered is a
  property of the request" is exactly the distinction the defect conflated.

### Temp test verification

Files used, all under `docs/builder/temp-tests/r1/` (gitignored):

- `test_w3p2_parse_witness.py` — **written this pass**, my independent parse-ordering witness.
  Passes on the fixed tree; reproduces the defect under W3-M1. **Disposition: not for promotion** —
  `tests/test_views.py::test_installing_the_middleware_parses_no_body_on_either_mount` and its
  regression twin are the permanent form of the same assertion and are already in the diff. Kept as
  this pass's scratch record.
- `test_w3p2_substituted_request.py` — **written this pass**, drives A-2 table row 9. Passes.
  **Disposition: recorded as a follow-up candidate, not a finding** — the behaviour is correct and
  the state is exotic; a permanent row would pin a property of Django's `process_view` dispatch more
  than of this package. Worth mentioning to Worker 1 in case a row is wanted.
- `test_w3p2_unbuildable_instance.py` — **written this pass**, demonstrates Low finding 1. **Fails
  by design**: its assertion is the *desired* behaviour (a controlled `200`) and the current code
  raises `TypeError`. **Disposition: promotion source for Low 1's fix** — inverted to pass, it is
  the third parametrization of
  `::test_a_marked_callback_the_middleware_cannot_build_is_declined_not_crashed`.
- `test_r1_hotpath.py`, `test_r1_hotpath_predicate.py`, `test_r1_ma_remeasure.py`,
  `proofs-pass2.json` — Worker 2's / pass 1's, **read and re-run, not modified**. My own outputs went
  to `w3p2-rerun.md` / `w3p2-rerun.log` so no prior record was overwritten.
- `test_r1_probes.py` — pass 1's; left as the promotion source it was.

### Notes for Worker 1 (spec reconciliation)

Everything pass 1 recorded stands. These are additions, and none is fixed in this pass.

1. **Escalated to R2 — the rationale's Decision 18 entry rejects, by name, the design the code now
   ships.** `docs/spec-046-transport_security-0_0_15-rationale.md` `### Decision 18` lists as a
   **rejected alternative**: "*A narrow package middleware placed before `CsrfViewMiddleware`, plus
   a system check that detects missing or wrong ordering* (the review's own first suggestion).
   Rejected: it adds a **required deployment entry** …". `2701f41a` shipped exactly that, minus the
   "required" (the entry is optional and the fallback is what makes it so), and
   `::_require_boundary_before_csrf` is the ordering check. **This is not caught by V1**, whose grep
   is on `GraphQLRequestBodyBoundaryMiddleware` and returns 0 in the rationale — the bullet never
   names the class. A rejected-alternative entry that describes the shipped design is the single
   most misleading shape a rationale can carry, because it tells the next reader not to do the thing
   the code does. Resolution paths for R2: (i) move the bullet from "rejected" to a keyed change
   record naming the round that adopted it and the fact that made the "required entry" objection
   dissolve (the withdrawable exemption), or (ii) keep it as rejected in its *original* form —
   middleware **plus** a required entry — and state alongside it what the shipped design does
   differently. Path (i) reads better; either beats leaving it.
2. **Escalated to R2 — spec Decision 18's own text still opens "No package middleware … and no
   required `MIDDLEWARE` entry."** Already inside V1/V2's remit, but recorded by symbol so R2 does
   not have to find it: the sentence is now false in its first clause and true only in its second.
   The pass-2 build report's note 3 names the additional sentence Decision 18 needs (the declined-
   callback state); this is the sentence it needs to *lose*. Worker 2's note 3 and this item are one
   edit.
3. **For R2, a state the spec should name and the fix made reachable, beyond note 3's.** The nested-
   handler case under `### Nine-state walk` above: a partial chain invoked inside a boundary-handled
   request cannot be distinguished at the `getattr(callback, "csrf_exempt", False)` read site, since
   that read receives no request. It is strictly narrower than both `HEAD` and the predecessor and
   unreachable through any supported seam, so it is documentation rather than code — one sentence
   in Decision 18 scoping the guarantee to the chain that handles the request, which is what the
   code implements.
4. **For R3, a live-tier home that will exist after M-A.** Once fakeshop's `MIDDLEWARE` gains the
   boundary entry, the live file's existing `_carrying_the_packages_csrf_mark` wrapper **is** the
   marker-dropping shape this fix is about, and the M-A remeasure shows the row now passes for the
   right reason. So R3 can earn the High fix's central assertion at the live tier by adding a parse
   or upload-handler witness to that row. That is a genuine live-first opportunity, not a
   requirement: the six new package rows are correctly placed under `AGENTS.md` #10 (a marker-
   dropping wrapper mount, a marked-but-unbuildable callback, a chain with no CSRF entry, and
   misordered chains are none of them shapes a live fakeshop query can reach), and the package rows
   for the misordered and unbuildable cases stay whatever R3 does.
5. **Low finding 1 is the one open decision, and it has a non-code resolution.** If the maintainer's
   view is that a callback forging the package's private marker is not a supported seam, then
   recording that rejection reason and narrowing the two docstring claims closes it without touching
   the guard. That is a contract call, which is why I state both paths rather than one.
6. **The duplicated-boundary-entry double measure (state 7 above) remains R2's**, unchanged and
   correctly unchanged: `process_view` still calls `view._enforce_request_boundary` rather than
   `::_enforce_request_boundary_once`, and switching it would freeze half of an answer R2 owns.

### Review outcome

`revision-needed`.

**Both of pass 1's substantive findings are answered, and answered well.** The **High** is closed by
a predicate that guards the answer rather than an input spelling; I re-derived its witness
independently, from a probe written from scratch, and measured **0 parses where pass 1 measured 1**,
with the probe proved capable of showing the 1 under the defective predicate. The **Medium** is
closed by a permanent row driven through the boundary-with-no-CSRF chain on both transports and both
strictnesses, and I proved by mutation that the row can fail. Pass-1 **Low (a)** stays docstring-only
(AST-minus-docstrings identical to `HEAD`), **Low (c)** stayed routed to R2 with its guard character-
identical to `HEAD`'s, and **DRY (f)** landed as one helper with two call sites, token-identical to
the lines it replaced. All thirteen proof records audit clean and **all thirteen re-ran with
set-equal node-id sets, 0 collection or setup errors, no zero-row and no weakly-pinned entry**; the
relocation is proved mechanically with `consumers.py` byte-identical to `HEAD`; the floor run
happened as declared and re-runs at **339 passed** with the shared `.venv` unmutated; all three
hot-path metrics exist, are the same experiment on both arms, and reproduce inside their recorded
bands.

**What holds it at `revision-needed` is two Low findings, neither of which existed before this
pass:**

1. `_package_view_instance`'s guard covers two spellings of "cannot build the view" and not the
   answer, so a marked callback whose `view_initkwargs` is a `dict` the class rejects still raises
   an unhandled `500` out of `process_view` — measured, and contrary to two shipped docstrings.
   Low (b) is therefore **partially** answered. One line plus one parametrization plus one manifest
   entry, in files this pass already owns; or a recorded rejection plus a narrowed docstring, which
   is Worker 1's call and is why both paths are stated.
2. The build report claims the Medium row is "pinned by entry 3's and entry 13's mutants"; measured,
   it fails under **none** of the thirteen. It is pinned by the view's `csrf_protect` continuation
   instead (5 rows under W3-M2), which is what the report's own note 4 says two sections later. No
   code change and no missed proof obligation — a record correction, but a record that currently
   argues with itself about the only row closing a finding.

`worker-3.md`'s acceptance gate is explicit that a Low finding must be addressed or intentionally
rejected with a recorded reason, and neither of these has one yet. Both are cheap, both sit inside
this pass's own ownership, and finding 1 owes a proof only a builder pass can produce — so the
honest routing is one more short cycle rather than an acceptance with the work described as
outstanding. Nothing above needs spec context, so nothing is escalated in place of being fixed;
items 1-4 under `### Notes for Worker 1` are genuinely R2's and R3's and are recorded there rather
than held against this pass.

---

## Build report (Worker 2, pass 3)

An apply-changes pass whose whole scope is the two Low findings
`## Review (Worker 3, pass 2)` left open: the recognizer's guard covering two spellings of
"cannot build the view" rather than the answer, and a false attribution in the pass-2 build
report. The third Low is acknowledged below and deliberately not "fixed".

Read end to end first: `AGENTS.md`, `START.md`, `docs/builder/BUILD.md`,
`docs/builder/ARTIFACT.md`, `docs/builder/worker-2.md`, `docs/TREE.md`,
`docs/spec-046-transport_security-0_0_15.md`,
`docs/builder/build-046-transport_security-0_0_15.md` (`# Closeout cycle (card 046)`), this
artifact's pass-1 and pass-2 plans, both prior build reports, both reviews, and
`docs/builder/worker-memory/worker-2.md`. The spec's `-rationale.md` was **not** read, nor was
any other worker's memory file.

### Files touched

Grounded in `git status --short` after both ruff invocations, not in memory.

- `django_strawberry_framework/middleware/request_body.py` — `::_package_view_instance` now
  attempts the construction and answers `None` when the class will not build from the
  callback's `view_initkwargs`, so the recognizer's answer is guarded rather than two spellings
  of its input. Its docstring and the module docstring's one-line description of the
  recognition were rewritten to state what the recognition now is.
- `tests/test_views.py` — a third mount, callback and parametrization for
  `::test_a_marked_callback_the_middleware_cannot_build_is_declined_not_crashed`, plus that
  test's docstring.
- `docs/builder/bld-046-r1-remediation_review.md` — this report appended at top level; the
  artifact's `Status:` line set to `built`. No prior section edited.

Untracked / gitignored scratch this pass wrote: `docs/builder/temp-tests/r1/proofs-pass3.json`,
`proofs-pass3.md`, `run-pass3.log`, `proofs-pass3-aux.json`, `proofs-pass3-aux.md`,
`run-pass3-aux.log`, `test_w2p3_decline_arm_is_the_fallback.py`,
`test_w2p3_hotpath_recognizer.py`, and `docs/builder/worker-memory/worker-2.md`.

Baseline-dirty and **untouched by this pass**: `django_strawberry_framework/views.py`,
`django_strawberry_framework/_request_body.py`, `django_strawberry_framework/consumers.py` (byte-
identical to `HEAD`, re-confirmed by `cmp` against `git show HEAD:` after the proof run),
`tests/test_routers.py`, `examples/fakeshop/apps/kanban/constants.py`,
`docs/builder/build-046-transport_security-0_0_15.md`. **Nothing was staged or unstaged**:
`git diff --cached --name-status` is still exactly
`A django_strawberry_framework/_boundary_ordering.py`, the one path W-1 authorizes, and that
file's bytes are unchanged by this pass. No new tracked file was created.

### Tests added or updated

- `tests/test_views.py::test_a_marked_callback_the_middleware_cannot_build_is_declined_not_crashed[/marked-rejected-initkwargs/]`
  — the third shape, and the only one no test of the bookkeeping's *shape* can reach: the
  callback carries the marker, a real `view_class`, and a `view_initkwargs` that is a `dict` the
  class rejects. It pins that the recognition runs as far as the instance: a controlled `200`
  from the mounted callback with the boundary middleware installed, rather than the `TypeError`
  out of `process_view` the finding measured. Promoted from Worker 3's
  `docs/builder/temp-tests/r1/test_w3p2_unbuildable_instance.py` (its assertion inverted from
  "record what happens" to the desired behaviour), which is the promotion source the review
  named.
- `tests/test_views.py::_marked_callback_with_initkwargs_the_class_rejects` and the
  `marked-rejected-initkwargs/` URL pattern — the fixture behind that row, docstringed with what
  makes it the shape a shape-test cannot reach.
- The parent test's docstring now states the three shapes as one recognition rather than two.

Nothing else changed: no existing assertion was weakened, renamed, or re-scoped.

### Validation run

- `uv run ruff format django_strawberry_framework/middleware/request_body.py tests/test_views.py`
  — pass (`2 files left unchanged`). Scoped to this pass's own two files, never `.`.
- `uv run ruff check --fix django_strawberry_framework/middleware/request_body.py tests/test_views.py`
  — pass (`All checks passed!`), nothing to fix.
- `uv run python scripts/check_trailing_commas.py <the same two files>` — **`Fixed 1 file(s)`**:
  it collapsed the three-element `parametrize` list back onto one line, since the explode
  threshold is 4. Re-run in `--check` mode afterwards: **exit 0**. `ruff format --check` on both
  files afterwards: `2 files already formatted`.
- `git status --short` after both ruff invocations: the eight tracked entries plus the untracked
  artifact listed under `### Files touched`, every one accounted for. **Nothing unexpected**, so
  there is nothing to report as churn and nothing was reverted.
- Focused runs, all without any `--cov*` flag:
  - `uv run pytest tests/test_views.py --no-cov` — **195 passed** (194 before this pass).
  - `uv run pytest tests/test_views.py tests/test_routers.py --no-cov` — **340 passed**, the
    proof scopes green after every mutation was reverted.
  - `uv run pytest examples/fakeshop/test_query/test_transport_api.py --no-cov` — **69 passed**;
    the live tier reaches `_package_view_instance` through its probe wrapper, so it is the
    sibling tree this change could have stranded.
  - `uv run pytest docs/builder/temp-tests/r1/test_w2p3_decline_arm_is_the_fallback.py -s -o addopts="" --no-cov`
    — **3 passed** (the decline-arm verification below).
- **Test staleness** (`BUILD.md` `### Test staleness a focused run cannot see`): neither shape
  applies — no example-model field set changed and no wire shape converted — so the full sweep
  is not owed by this pass. The one staleness this change could create is a stranded importer of
  the changed helper: `grep -rn '_package_view_instance' --include='*.py' .` returns hits only
  inside `middleware/request_body.py` itself (three docstring/call references plus the
  definition) and in this pass's own gitignored scratch probes. No test tree imports it.

### Failability proofs

**All fourteen manifest entries were re-run in one invocation**, into a pass-3 output path so
pass 1's and pass 2's records survive untouched:

```shell
uv run python scripts/prove_failability.py docs/builder/temp-tests/r1/proofs-pass3.json \
    --scratch-root <session scratchpad>/w2p3 \
    --output docs/builder/temp-tests/r1/proofs-pass3.md
```

Anchor verification was run **first and separately** (`--check-anchors-only`, **exit 0**: all
fourteen anchors matched **exactly once before any copy was taken**). Final run **exit 0**: every
entry proved, **no boundary weakly pinned**, **0 collection or setup errors on every one of the
fourteen**, every restore proved by `filecmp.cmp(shallow=False)` plus SHA-256 against the
pre-mutation copy. No `ACTIVE-MUTATION.json` and no `RESTORE-FAILED.json` anywhere under either
scratch root afterwards; `consumers.py` re-verified byte-identical to `HEAD` by `cmp` against
`git show HEAD:`; no `git checkout` / `restore` / `stash` / `worktree` at any point.

**why 0: not applicable to any entry — no entry in the record measured zero rows.** The lowest
count is 2. So neither the weakly-pinned nor the harness-impossible reading is invoked below.

**Two entries moved from pass 2, and the other twelve are set-equal.** Compared as node-id sets
by differencing pass 2's own emitted `proofs-pass2.md` against this pass's, never as counts:

| # | Pass 2 | Pass 3 | Direction | Why |
| --- | --- | --- | --- | --- |
| 1-11, 13 | 7, 2, 4, 3, 13, 3, 14, 6, 2, 2, 2, 7 | identical sets | **set-equal** | this pass changes one helper in one module; a movement anywhere else would have been contamination |
| 12 | 2 | **3** | **grew** (+1, none lost) | gained exactly `::test_a_marked_callback_the_middleware_cannot_build_is_declined_not_crashed[/marked-rejected-initkwargs/]`, the row this pass added. The anchor was **widened** — see below |
| 14 | — | **5** | new entry | the view's unconditional CSRF continuation, added because the pass-2 report attributed a row to it wrongly (`### Correction to the pass-2 build report`) |

**Entry 12's anchor was widened, and the review's expectation that its old anchor and its two
rows would "survive either way" is false as measured.** The widened guard **subsumes** the two
`isinstance` clauses' answer: with the construction attempt in place, deleting the clauses alone
changes no answer for any row, because `None(**None)` and `**[…]` both raise the `TypeError` the
new arm catches. Measured rather than reasoned, as a separate auxiliary run on pass 2's
*unchanged* entry-12 anchor:

```shell
uv run python scripts/prove_failability.py docs/builder/temp-tests/r1/proofs-pass3-aux.json \
    --scratch-root <session scratchpad>/w2p3-aux \
    --output docs/builder/temp-tests/r1/proofs-pass3-aux.md
```

exit **1** — `**WEAKLY PINNED**`, **0 rows**, 0 collection/setup errors, pre-mutation state
`195 passed` (exit 0), mutant run `195 passed` (exit 0), restore proved
(`filecmp.cmp(shallow=False) True; sha256 6ef3ad5e35ebc9e7… == 6ef3ad5e35ebc9e7…`). Keeping that
anchor in the pass-3 record would therefore have shipped a 0-row entry, which the acceptance rule
forbids. The clauses and the construction are **one decision with one answer** — "the instance
whose boundary I can run, or `None`" — reached at one site, which is `BUILD.md`
`### Slice splitting`'s own criterion for one unit; so the record measures them as one boundary,
with the mutation removing the whole recognition after the two `getattr`s, and it fails 3 rows.
The clauses are not thereby dead: they keep the `except` arm scoped to the constructor call and
keep the recognized `view_initkwargs` type to the `dict` Django's `as_view` actually produces
(pass 2's recorded reason, unchanged), and they are what stops a non-class `view_class` being
*called* at all.

**Entry 14 is not a new boundary and owes no proof** (`BUILD.md` `### What needs a proof` scopes
the obligation to boundaries a pass introduces, and the continuation predates this round). It is
in the record because it is cheap and because it makes the correction below a measurement of mine
rather than an inherited claim: dropping `csrf_protect` from both continuations fails **5** rows,
0 errors, including both parametrizations of
`::test_a_chain_with_the_boundary_and_no_csrf_middleware_still_checks_csrf` — the row whose
attribution pass 2 got wrong. The set is identical to the one the review measured under its own
W3-M2.

The emitted record follows verbatim, every measured field filled in by the runner.


Procedure, mechanized by `scripts/prove_failability.py`: the target is copied to a scratch path OUTSIDE the repo before any mutation; the mutation site is located by an exact anchor asserted to match exactly once (any other count aborts the entry without writing); the same focused scope is run unmutated first, so rows already failing before the mutation are differenced out of the count; both runs' pytest exit codes are read, because a run that collected nothing or blew up emits no `FAILED` lines and would otherwise be recorded as a measured zero; both runs use `--no-cov`; the file is restored from the pre-mutation copy in a `finally` and the restore is proved by `filecmp.cmp(shallow=False)` plus a SHA-256 comparison. One boundary at a time, restored before the next. `git` is never invoked - the tree is legitimately dirty, so an empty `git diff` is unachievable and forcing one would destroy the build's own work.

| # | Boundary | File mutated | Mutation applied | Rows failed | Errors | Scope as run | Restore proof |
|---|---|---|---|---|---|---|---|
| 1 | `django_strawberry_framework/views.py::_RequestBodyBoundaryMixin._enforce_body_charset_declaration` | `django_strawberry_framework/views.py` | deleted: `if _declared_charset_is_unhonourable(request): raise HTTPException(400, _JSON_PARSE_REASON)` - builder's description (unverified prose): the charset refusal itself deleted: a declared non-UTF-8 charset is read and then ignored (re-anchored onto the DRY (f) helper call; the bare raise line alone occurs 4 times in the file, so the anchor is the two-line block) | **7** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_views.py` | filecmp.cmp(shallow=False) True; sha256 e8aeb156550fc45a... == e8aeb156550fc45a... (vs pre-mutation copy) |
| 2 | `django_strawberry_framework/views.py::_RequestBodyBoundaryMixin._enforce_body_charset_declaration #"if request.method == \"GET\" or _is_multipart_form_post(request)"` | `django_strawberry_framework/views.py` | deleted: `if request.method == "GET" or _is_multipart_form_post(request): return` - builder's description (unverified prose): the GET / multipart carve-out deleted, so the guard claims every request shape including the ones the multipart encoding guard owns | **2** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_views.py` | filecmp.cmp(shallow=False) True; sha256 e8aeb156550fc45a... == e8aeb156550fc45a... (vs pre-mutation copy) |
| 3 | `django_strawberry_framework/middleware/request_body.py::_package_view_instance #"if not getattr(view_func, _BOUNDARY_MARKER, False)"` | `django_strawberry_framework/middleware/request_body.py` | `if not getattr(view_func, _BOUNDARY_MARKER, False):` -> `if True:` - builder's description (unverified prose): the recognition made unconditionally negative: _package_view_instance always answers None, so the chain never runs the boundary and never stamps the request | **4** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_views.py` | filecmp.cmp(shallow=False) True; sha256 6ef3ad5e35ebc9e7... == 6ef3ad5e35ebc9e7... (vs pre-mutation copy) |
| 4 | `django_strawberry_framework/_boundary_ordering.py::_CsrfOrderingExemption.__bool__` | `django_strawberry_framework/_boundary_ordering.py` | `request = _boundary_middleware_request.get() return request is None or not getattr(request, _BOUNDARY_ENFORCED, False)` -> `return True` - builder's description (unverified prose): the withdrawal removed: the exemption is always truthy, so the configured CSRF middleware always skips the callback | **3** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_views.py` | filecmp.cmp(shallow=False) True; sha256 b2c25d9a66a6090c... == b2c25d9a66a6090c... (vs pre-mutation copy) |
| 5 | `django_strawberry_framework/_boundary_ordering.py::_CsrfOrderingExemption.__bool__ (opposite direction)` | `django_strawberry_framework/_boundary_ordering.py` | `request = _boundary_middleware_request.get() return request is None or not getattr(request, _BOUNDARY_ENFORCED, False)` -> `return False` - builder's description (unverified prose): the exemption is always withdrawn, so the view-local arrangement loses its ordering on a chain that does not supply one | **13** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_views.py` | filecmp.cmp(shallow=False) True; sha256 b2c25d9a66a6090c... == b2c25d9a66a6090c... (vs pre-mutation copy) |
| 6 | `django_strawberry_framework/middleware/request_body.py::_require_boundary_before_csrf` | `django_strawberry_framework/middleware/request_body.py` | `boundary_index = csrf_index = None` -> `return boundary_index = csrf_index = None` - builder's description (unverified prose): the ordering audit short-circuited before it reads MIDDLEWARE, so a misordered chain is accepted at startup | **3** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_views.py` | filecmp.cmp(shallow=False) True; sha256 6ef3ad5e35ebc9e7... == 6ef3ad5e35ebc9e7... (vs pre-mutation copy) |
| 7 | `django_strawberry_framework/views.py::_RequestBodyBoundaryMixin._enforce_request_boundary_once` | `django_strawberry_framework/views.py` | `if getattr(request, _BOUNDARY_ENFORCED, False): return self._enforce_request_boundary(request)` -> `return` - builder's description (unverified prose): the view's own enforcement removed entirely: the body boundary runs zero times on any chain that does not carry the middleware | **14** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_views.py` | filecmp.cmp(shallow=False) True; sha256 e8aeb156550fc45a... == e8aeb156550fc45a... (vs pre-mutation copy) |
| 8 | `django_strawberry_framework/_request_body.py::_measured_remaining` | `django_strawberry_framework/_request_body.py` | deleted: `if type(end) is not int or type(position) is not int: return _Probe.UNMEASURABLE` - builder's description (unverified prose): the exact-int gate deleted, so a foreign position/end object's own numeric protocol executes inside the gate | **6** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_views.py` | filecmp.cmp(shallow=False) True; sha256 2c1fd48618d4b01c... == 2c1fd48618d4b01c... (vs pre-mutation copy) |
| 9 | `django_strawberry_framework/consumers.py::_ConnectionRevocation.settle` | `django_strawberry_framework/consumers.py` | `try: await asyncio.shield(self.attempt) except asyncio.CancelledError: self.attempt.cancel() # Suppressed, not swallo...` -> `await asyncio.shield(self.attempt)` - builder's description (unverified prose): the cancel-and-await-and-re-raise arm removed, leaving the bare shielded await this fix replaced: a cancelled settlement leaves the attempt running | **2** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_routers.py` | filecmp.cmp(shallow=False) True; sha256 1bdf298c473fd1a0... == 1bdf298c473fd1a0... (vs pre-mutation copy) |
| 10 | `django_strawberry_framework/consumers.py::_ConnectionRevocation._attempt_close` | `django_strawberry_framework/consumers.py` | deleted: `except asyncio.CancelledError: self.state = _REVOCATION_ABANDONED raise` - builder's description (unverified prose): the terminal-record arm deleted, so a cancelled attempt rests in CLOSING instead of ABANDONED | **2** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_routers.py` | filecmp.cmp(shallow=False) True; sha256 1bdf298c473fd1a0... == 1bdf298c473fd1a0... (vs pre-mutation copy) |
| 11 | `django_strawberry_framework/consumers.py::build_revalidating_consumer_class #"await super().disconnect(code)"` | `django_strawberry_framework/consumers.py` | `try: await super().disconnect(code) finally: await self._revocation.settle()` -> `await super().disconnect(code) await self._revocation.settle()` - builder's description (unverified prose): the try/finally flattened back to two sequential awaits, so a cancelled or raising upstream teardown skips settlement | **2** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_routers.py` | filecmp.cmp(shallow=False) True; sha256 1bdf298c473fd1a0... == 1bdf298c473fd1a0... (vs pre-mutation copy) |
| 12 | `django_strawberry_framework/middleware/request_body.py::_package_view_instance #"if not isinstance(view_class, type)"` | `django_strawberry_framework/middleware/request_body.py` | `if not isinstance(view_class, type) or not isinstance(initkwargs, dict): return None try: return view_class(**initkwa...` -> `return view_class(**initkwargs)` - builder's description (unverified prose): the whole recognition after the two getattrs deleted - both isinstance clauses and the construction attempt - so a marked callback's view_class and view_initkwargs are dereferenced and splatted unguarded and any callback the class cannot be built from becomes an unhandled 500 out of process_view | **3** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_views.py` | filecmp.cmp(shallow=False) True; sha256 6ef3ad5e35ebc9e7... == 6ef3ad5e35ebc9e7... (vs pre-mutation copy) |
| 13 | `django_strawberry_framework/_boundary_ordering.py::_CsrfOrderingExemption.__bool__ (the per-request key)` | `django_strawberry_framework/_boundary_ordering.py` | `request = _boundary_middleware_request.get() return request is None or not getattr(request, _BOUNDARY_ENFORCED, False)` -> `return _boundary_middleware_request.get() is None` - builder's description (unverified prose): the per-request key removed and the defective predecessor restored: the exemption is withdrawn because a boundary middleware is handling the request, whether or not it ran the boundary for it | **7** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_views.py` | filecmp.cmp(shallow=False) True; sha256 b2c25d9a66a6090c... == b2c25d9a66a6090c... (vs pre-mutation copy) |
| 14 | `django_strawberry_framework/views.py #"_csrf_protected_run = csrf_protect(_run_after_csrf_check)"` | `django_strawberry_framework/views.py` | `_csrf_protected_run = csrf_protect(_run_after_csrf_check) _csrf_protected_async_run = csrf_protect(_async_run_after_c...` -> `_csrf_protected_run = _run_after_csrf_check _csrf_protected_async_run = _async_run_after_csrf_check` - builder's description (unverified prose): the csrf_protect wrapper dropped from both continuations, so the view re-enters its delegate without performing a CSRF check of its own while every other boundary stands | **5** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_views.py` | filecmp.cmp(shallow=False) True; sha256 e8aeb156550fc45a... == e8aeb156550fc45a... (vs pre-mutation copy) |

Verdicts:

1. `django_strawberry_framework/views.py::_RequestBodyBoundaryMixin._enforce_body_charset_declaration` - pinned
2. `django_strawberry_framework/views.py::_RequestBodyBoundaryMixin._enforce_body_charset_declaration #"if request.method == \"GET\" or _is_multipart_form_post(request)"` - inside Worker 3's mandatory re-run floor (<= 3 rows)
3. `django_strawberry_framework/middleware/request_body.py::_package_view_instance #"if not getattr(view_func, _BOUNDARY_MARKER, False)"` - pinned
4. `django_strawberry_framework/_boundary_ordering.py::_CsrfOrderingExemption.__bool__` - inside Worker 3's mandatory re-run floor (<= 3 rows)
5. `django_strawberry_framework/_boundary_ordering.py::_CsrfOrderingExemption.__bool__ (opposite direction)` - pinned
6. `django_strawberry_framework/middleware/request_body.py::_require_boundary_before_csrf` - inside Worker 3's mandatory re-run floor (<= 3 rows)
7. `django_strawberry_framework/views.py::_RequestBodyBoundaryMixin._enforce_request_boundary_once` - pinned
8. `django_strawberry_framework/_request_body.py::_measured_remaining` - pinned
9. `django_strawberry_framework/consumers.py::_ConnectionRevocation.settle` - inside Worker 3's mandatory re-run floor (<= 3 rows)
10. `django_strawberry_framework/consumers.py::_ConnectionRevocation._attempt_close` - inside Worker 3's mandatory re-run floor (<= 3 rows)
11. `django_strawberry_framework/consumers.py::build_revalidating_consumer_class #"await super().disconnect(code)"` - inside Worker 3's mandatory re-run floor (<= 3 rows)
12. `django_strawberry_framework/middleware/request_body.py::_package_view_instance #"if not isinstance(view_class, type)"` - inside Worker 3's mandatory re-run floor (<= 3 rows)
13. `django_strawberry_framework/_boundary_ordering.py::_CsrfOrderingExemption.__bool__ (the per-request key)` - pinned
14. `django_strawberry_framework/views.py #"_csrf_protected_run = csrf_protect(_run_after_csrf_check)"` - pinned

Failing node ids, per boundary (the count above is `len()` of this list):

1. `django_strawberry_framework/views.py::_RequestBodyBoundaryMixin._enforce_body_charset_declaration`
   - file mutated: `django_strawberry_framework/views.py`
   - pytest summary: `======================== 7 failed, 188 passed in 1.70s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 195 passed in 1.63s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_views.py::test_a_non_multipart_request_is_not_subject_to_the_form_encoding_check`
   - `tests/test_views.py::test_the_endpoint_refuses_a_json_charset_it_will_not_decode_with[sync-latin-1]`
   - `tests/test_views.py::test_the_endpoint_refuses_a_json_charset_it_will_not_decode_with[sync-utf-8-sig]`
   - `tests/test_views.py::test_the_endpoint_refuses_a_json_charset_it_will_not_decode_with[sync-unknown-name]`
   - `tests/test_views.py::test_the_endpoint_refuses_a_json_charset_it_will_not_decode_with[async-latin-1]`
   - `tests/test_views.py::test_the_endpoint_refuses_a_json_charset_it_will_not_decode_with[async-utf-8-sig]`
   - `tests/test_views.py::test_the_endpoint_refuses_a_json_charset_it_will_not_decode_with[async-unknown-name]`
2. `django_strawberry_framework/views.py::_RequestBodyBoundaryMixin._enforce_body_charset_declaration #"if request.method == \"GET\" or _is_multipart_form_post(request)"`
   - file mutated: `django_strawberry_framework/views.py`
   - pytest summary: `======================== 2 failed, 193 passed in 1.61s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 195 passed in 1.59s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_views.py::test_a_get_carrying_a_stray_multipart_content_type_is_not_a_multipart_form`
   - `tests/test_views.py::test_a_multipart_declaration_is_left_to_the_form_encoding_guard`
3. `django_strawberry_framework/middleware/request_body.py::_package_view_instance #"if not getattr(view_func, _BOUNDARY_MARKER, False)"`
   - file mutated: `django_strawberry_framework/middleware/request_body.py`
   - pytest summary: `======================== 4 failed, 191 passed in 1.60s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 195 passed in 1.61s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_views.py::test_the_projects_own_csrf_middleware_runs_when_the_chain_supplies_the_ordering[sync]`
   - `tests/test_views.py::test_the_projects_own_csrf_middleware_runs_when_the_chain_supplies_the_ordering[async]`
   - `tests/test_views.py::test_the_view_does_not_measure_a_body_the_chain_already_measured[sync]`
   - `tests/test_views.py::test_the_view_does_not_measure_a_body_the_chain_already_measured[async]`
4. `django_strawberry_framework/_boundary_ordering.py::_CsrfOrderingExemption.__bool__`
   - file mutated: `django_strawberry_framework/_boundary_ordering.py`
   - pytest summary: `======================== 3 failed, 192 passed in 2.08s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 195 passed in 1.93s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_views.py::test_the_projects_own_csrf_middleware_runs_when_the_chain_supplies_the_ordering[sync]`
   - `tests/test_views.py::test_the_projects_own_csrf_middleware_runs_when_the_chain_supplies_the_ordering[async]`
   - `tests/test_views.py::test_the_async_chain_resets_the_ordering_mark_around_the_downstream_call`
5. `django_strawberry_framework/_boundary_ordering.py::_CsrfOrderingExemption.__bool__ (opposite direction)`
   - file mutated: `django_strawberry_framework/_boundary_ordering.py`
   - pytest summary: `======================== 13 failed, 182 passed in 1.61s ========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 195 passed in 1.69s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_views.py::test_the_view_callback_of_both_views_carries_the_csrf_exempt_mark[sync]`
   - `tests/test_views.py::test_the_view_callback_of_both_views_carries_the_csrf_exempt_mark[async]`
   - `tests/test_views.py::test_without_the_middleware_the_view_keeps_its_own_ordering_and_exemption[sync]`
   - `tests/test_views.py::test_without_the_middleware_the_view_keeps_its_own_ordering_and_exemption[async]`
   - `tests/test_views.py::test_the_async_chain_resets_the_ordering_mark_around_the_downstream_call`
   - `tests/test_views.py::test_installing_the_middleware_parses_no_body_on_either_mount[sync]`
   - `tests/test_views.py::test_installing_the_middleware_parses_no_body_on_either_mount[async]`
   - `tests/test_views.py::test_the_same_two_mounts_parse_nothing_without_the_middleware_either[sync]`
   - `tests/test_views.py::test_the_same_two_mounts_parse_nothing_without_the_middleware_either[async]`
   - `tests/test_views.py::test_a_declined_callbacks_over_limit_body_never_reaches_the_csrf_class[sync]`
   - `tests/test_views.py::test_a_declined_callbacks_over_limit_body_never_reaches_the_csrf_class[async]`
   - `tests/test_views.py::test_a_declined_callback_still_gets_a_complete_csrf_check[sync]`
   - `tests/test_views.py::test_a_declined_callback_still_gets_a_complete_csrf_check[async]`
6. `django_strawberry_framework/middleware/request_body.py::_require_boundary_before_csrf`
   - file mutated: `django_strawberry_framework/middleware/request_body.py`
   - pytest summary: `======================== 3 failed, 192 passed in 1.61s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 195 passed in 1.67s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_views.py::test_a_chain_that_lists_the_boundary_after_csrf_is_refused_at_startup`
   - `tests/test_views.py::test_a_boundary_subclass_listed_after_csrf_is_refused_at_startup`
   - `tests/test_views.py::test_the_first_csrf_entry_is_the_one_the_ordering_is_measured_against`
7. `django_strawberry_framework/views.py::_RequestBodyBoundaryMixin._enforce_request_boundary_once`
   - file mutated: `django_strawberry_framework/views.py`
   - pytest summary: `======================== 14 failed, 181 passed in 1.62s ========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 195 passed in 1.66s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_views.py::test_the_endpoint_refuses_a_json_charset_it_will_not_decode_with[sync-latin-1]`
   - `tests/test_views.py::test_the_endpoint_refuses_a_json_charset_it_will_not_decode_with[sync-utf-8-sig]`
   - `tests/test_views.py::test_the_endpoint_refuses_a_json_charset_it_will_not_decode_with[sync-unknown-name]`
   - `tests/test_views.py::test_the_endpoint_refuses_a_json_charset_it_will_not_decode_with[async-latin-1]`
   - `tests/test_views.py::test_the_endpoint_refuses_a_json_charset_it_will_not_decode_with[async-utf-8-sig]`
   - `tests/test_views.py::test_the_endpoint_refuses_a_json_charset_it_will_not_decode_with[async-unknown-name]`
   - `tests/test_views.py::test_without_the_middleware_the_view_keeps_its_own_ordering_and_exemption[sync]`
   - `tests/test_views.py::test_without_the_middleware_the_view_keeps_its_own_ordering_and_exemption[async]`
   - `tests/test_views.py::test_installing_the_middleware_parses_no_body_on_either_mount[sync]`
   - `tests/test_views.py::test_installing_the_middleware_parses_no_body_on_either_mount[async]`
   - `tests/test_views.py::test_the_same_two_mounts_parse_nothing_without_the_middleware_either[sync]`
   - `tests/test_views.py::test_the_same_two_mounts_parse_nothing_without_the_middleware_either[async]`
   - `tests/test_views.py::test_a_declined_callbacks_over_limit_body_never_reaches_the_csrf_class[sync]`
   - `tests/test_views.py::test_a_declined_callbacks_over_limit_body_never_reaches_the_csrf_class[async]`
8. `django_strawberry_framework/_request_body.py::_measured_remaining`
   - file mutated: `django_strawberry_framework/_request_body.py`
   - pytest summary: `======================== 6 failed, 189 passed in 1.62s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 195 passed in 1.62s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_views.py::test_a_probe_that_fails_without_moving_the_stream_falls_back_to_the_bounded_read[sync-unnumbered-end-position]`
   - `tests/test_views.py::test_a_probe_that_fails_without_moving_the_stream_falls_back_to_the_bounded_read[async-unnumbered-end-position]`
   - `tests/test_views.py::test_a_position_object_whose_numeric_protocol_raises_never_runs_inside_the_gate[sync-subtraction-raises]`
   - `tests/test_views.py::test_a_position_object_whose_numeric_protocol_raises_never_runs_inside_the_gate[sync-comparison-raises]`
   - `tests/test_views.py::test_a_position_object_whose_numeric_protocol_raises_never_runs_inside_the_gate[async-subtraction-raises]`
   - `tests/test_views.py::test_a_position_object_whose_numeric_protocol_raises_never_runs_inside_the_gate[async-comparison-raises]`
9. `django_strawberry_framework/consumers.py::_ConnectionRevocation.settle`
   - file mutated: `django_strawberry_framework/consumers.py`
   - pytest summary: `======================== 2 failed, 143 passed in 7.55s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 145 passed in 7.58s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_routers.py::test_cancelling_the_teardown_ends_the_close_attempt_instead_of_orphaning_it`
   - `tests/test_routers.py::test_a_cancelled_disconnect_leaves_no_task_retaining_the_connection`
10. `django_strawberry_framework/consumers.py::_ConnectionRevocation._attempt_close`
   - file mutated: `django_strawberry_framework/consumers.py`
   - pytest summary: `======================== 2 failed, 143 passed in 7.55s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 145 passed in 7.59s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_routers.py::test_cancelling_the_teardown_ends_the_close_attempt_instead_of_orphaning_it`
   - `tests/test_routers.py::test_a_cancelled_disconnect_leaves_no_task_retaining_the_connection`
11. `django_strawberry_framework/consumers.py::build_revalidating_consumer_class #"await super().disconnect(code)"`
   - file mutated: `django_strawberry_framework/consumers.py`
   - pytest summary: `======================== 2 failed, 143 passed in 7.63s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 145 passed in 7.54s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_routers.py::test_a_teardown_cancelled_before_it_returns_still_settles_the_close`
   - `tests/test_routers.py::test_a_teardown_that_raises_still_settles_the_close_and_propagates`
12. `django_strawberry_framework/middleware/request_body.py::_package_view_instance #"if not isinstance(view_class, type)"`
   - file mutated: `django_strawberry_framework/middleware/request_body.py`
   - pytest summary: `======================== 3 failed, 192 passed in 1.62s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 195 passed in 1.60s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_views.py::test_a_marked_callback_the_middleware_cannot_build_is_declined_not_crashed[/marked-no-view-class/]`
   - `tests/test_views.py::test_a_marked_callback_the_middleware_cannot_build_is_declined_not_crashed[/marked-bad-initkwargs/]`
   - `tests/test_views.py::test_a_marked_callback_the_middleware_cannot_build_is_declined_not_crashed[/marked-rejected-initkwargs/]`
13. `django_strawberry_framework/_boundary_ordering.py::_CsrfOrderingExemption.__bool__ (the per-request key)`
   - file mutated: `django_strawberry_framework/_boundary_ordering.py`
   - pytest summary: `======================== 7 failed, 188 passed in 1.66s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 195 passed in 1.64s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_views.py::test_the_async_chain_resets_the_ordering_mark_around_the_downstream_call`
   - `tests/test_views.py::test_installing_the_middleware_parses_no_body_on_either_mount[sync]`
   - `tests/test_views.py::test_installing_the_middleware_parses_no_body_on_either_mount[async]`
   - `tests/test_views.py::test_a_declined_callbacks_over_limit_body_never_reaches_the_csrf_class[sync]`
   - `tests/test_views.py::test_a_declined_callbacks_over_limit_body_never_reaches_the_csrf_class[async]`
   - `tests/test_views.py::test_a_declined_callback_still_gets_a_complete_csrf_check[sync]`
   - `tests/test_views.py::test_a_declined_callback_still_gets_a_complete_csrf_check[async]`
14. `django_strawberry_framework/views.py #"_csrf_protected_run = csrf_protect(_run_after_csrf_check)"`
   - file mutated: `django_strawberry_framework/views.py`
   - pytest summary: `======================== 5 failed, 190 passed in 1.71s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 195 passed in 1.89s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_views.py::test_each_csrf_continuation_matches_the_transport_it_protects`
   - `tests/test_views.py::test_a_declined_callback_still_gets_a_complete_csrf_check[sync]`
   - `tests/test_views.py::test_a_declined_callback_still_gets_a_complete_csrf_check[async]`
   - `tests/test_views.py::test_a_chain_with_the_boundary_and_no_csrf_middleware_still_checks_csrf[sync]`
   - `tests/test_views.py::test_a_chain_with_the_boundary_and_no_csrf_middleware_still_checks_csrf[async]`

A boundary whose removal fails 0 or 1 rows is **weakly pinned** and is `revision-needed` per `docs/builder/BUILD.md` - the fix is more or better-targeted rows, never a weaker boundary. A boundary at 3 rows or fewer is inside Worker 3's mandatory independent re-run floor. A proof carrying collection or setup errors, or whose pytest run exited anything but 0 or 1 (nothing collected, interrupted, internal error, usage error), is not a valid count at all - and a 0 from such a run is not a zero-row result: resolve it and re-run.

Every `<fill in ...>` above is a judgement no tool can make and MUST be replaced by hand before this subsection is submitted: weakly pinned and harness-impossible are the two possible readings of a zero-row result and they prescribe opposite responses (more rows, versus a production-call-site invariant assertion plus a recorded harness limitation), so a record that does not name one reads as self-contradictory.

### Hot-path budget

The plan's closeout declaration makes the fixing pass inherit R1's hot-path declaration, and
pass 2 declared this `views.py` / middleware path hot. This pass adds a `try` /
`except TypeError` around one construction inside `_package_view_instance`, which
`process_view` calls on **every** request that reaches the endpoint through an installed chain —
so the changed code does execute on the measured path and the second, "cannot execute here"
answer is not available. Two metrics, the declared one and one that can actually resolve a
change of this size. Both are the same experiment on both arms; whether the cost is acceptable
is the maintainer's call.

**Metric 1 — the declared metric: median wall-clock per `Client().post`.** 400 iterations after
one discarded warm-up request, median, four independent runs, both chain arms, snippet reused
unmodified from pass 2 (`docs/builder/temp-tests/r1/test_r1_hotpath.py`,
`uv run pytest … -s -o addopts="" --no-cov`). The **before** arm was captured on this tree
**before the edit was made**, since there is no second chance at it.

| Run | before: `[CsrfViewMiddleware]` | before: `[boundary, CSRF]` | after: `[CsrfViewMiddleware]` | after: `[boundary, CSRF]` |
| --- | --- | --- | --- | --- |
| 1 | 296.31 us | 305.87 us | 316.94 us | 313.96 us |
| 2 | 323.04 us | 321.56 us | 314.10 us | 314.92 us |
| 3 | 316.75 us | 313.10 us | 311.88 us | 309.35 us |
| 4 | 317.44 us | 317.44 us | 324.17 us | 322.33 us |

Installed-arm medians sorted: **305.87 / 313.10 / 317.44 / 321.56 us before**, **309.35 /
313.96 / 314.92 / 322.33 us after** — median-of-medians **315.27 us before**, **314.44 us
after**, delta **-0.83 us**, i.e. no measurable change and well inside run-to-run noise on a
~314 us request. The control arm moved comparably in the same captures (317.10 -> 315.52 us),
which is what says the spread is noise rather than signal.

**Metric 2 — the recognizer's own micro-cost, which is what a `try` block can actually move.**
The request median cannot resolve a nanosecond-scale change, so the added cost was measured
where it lands: one `_package_view_instance` call on a genuine package callback, `timeit` over
**200,000** iterations, four runs, both arms in the same process over the identical body — the
only difference being the `try` / `except TypeError`
(`docs/builder/temp-tests/r1/test_w2p3_hotpath_recognizer.py`).

| Run | without the guard | with the guard | delta per call |
| --- | --- | --- | --- |
| 1 | 0.5024 us | 0.5319 us | +0.0295 us |
| 2 | 0.5349 us | 0.5349 us | 0.0000 us |
| 3 | 0.5232 us | 0.5204 us | -0.0028 us |
| 4 | 0.5275 us | 0.5069 us | -0.0206 us |

Median delta **-0.0014 us**: no measurable cost on the shared environment's interpreter, which
is what a zero-cost `try` on the non-raising path predicts. **Re-measured at the floor**, where
the prediction does not hold and the `try` costs a real setup: `+0.0154 us` and `+0.0004 us` per
call over two runs at Python 3.10.19 (0.5481 -> 0.5636 and 0.5602 -> 0.5606 us/call). So the
worst reading anywhere is **~15 nanoseconds per request** against a ~314 microsecond request.
Nothing was weakened to buy it back — the guard is strictly wider than what it replaced.

### Floor verification

Floor facts taken from `BUILD.md` `## Floor verification`, its single canonical statement, never
from memory or from a number restated elsewhere: the supported floor is **Django 5.2.0 on Python
3.10 with strawberry-graphql 0.316.0**. Scope: `tests/test_views.py`.

`/tmp/dsf-floor` was on disk from the prior passes and was **reused only after reading its
versions**, per this pass's instruction:

- `/tmp/dsf-floor/bin/python -V` -> **Python 3.10.19**.
- `uv pip list --python /tmp/dsf-floor/bin/python`, read rather than recalled: **django 5.2**,
  **strawberry-graphql 0.316.0**, asgiref 3.12.1, channels 4.3.2, daphne 4.2.3, pytest 9.1.1,
  pytest-django 4.12.0, pytest-asyncio 1.4.0, `django-strawberry-framework 0.0.14` editable at
  this checkout. That is the canonical floor, so the venv is the floor and no rebuild was
  needed; the editable install points at this working tree, so it carries this pass's change.
- `/tmp/dsf-floor/bin/python -m pytest tests/test_views.py --no-cov` — **195 passed**.
- The three declined rows named individually rather than hidden inside a green aggregate, since
  the new one is this pass's whole subject:
  `::test_a_marked_callback_the_middleware_cannot_build_is_declined_not_crashed[/marked-no-view-class/]`,
  `[/marked-bad-initkwargs/]` and `[/marked-rejected-initkwargs/]` — **3 passed**, so the
  `TypeError` a rejected `dict` raises at Python 3.10 is caught by the same arm as at 3.14 (the
  message differs between interpreters; the type does not).
- `docs/builder/temp-tests/r1/test_w2p3_decline_arm_is_the_fallback.py` at the floor — **3
  passed**, so the decline arm's four links hold at the floor too.
- **The shared `.venv` is unmutated**, read rather than asserted: `uv pip list` reports **django
  6.0.5**, asgiref 3.11.1, and `.venv/bin/python -V` is **Python 3.14.2** — still far above the
  floor, so no floor install leaked into it. Every floor command carried an explicit
  `--python /tmp/dsf-floor/bin/python` or was invoked as `/tmp/dsf-floor/bin/python -m pytest`.

### Dispatched findings checklist

**No box is ticked by this pass, and none is untick-worthy.** The two findings this pass closes
are Worker 3 review findings, not `docs/feedback.md` findings, so neither has a box. Box 2 was
ticked in pass 2 and its contract — an over-limit multipart refused before parsing while an
under-limit request reaches and obeys the project's own `CsrfViewMiddleware` subclass — is
unchanged by this diff: entry 3's four rows and entry 13's seven rows are set-equal to pass 2's.
Boxes 1, 3 and 4 stay `- [ ]` as the plan defers them at plan level (their contracts landed in
`2701f41a` / `ba66ab49`, so Worker 1 ticks them at final verification where a tick means landed
**and** audited); this pass touches none of their sites, and entries 1, 2, 7, 8, 9, 10 and 11 are
all set-equal to pass 2's, which is the mechanical evidence for that.

### Implementation notes

- **The shape chosen, and why the `except` is not the catalogued fail-open shape.** The guard is
  `try: return view_class(**initkwargs) / except TypeError: return None`. `BUILD.md`
  `### Fail-open shapes` catalogues "a bare `except` (or an over-broad `except Exception`)
  **wrapped around a check**, which converts 'the check blew up' into 'the check passed'". Three
  things make this a different shape and I satisfied myself of each rather than inheriting the
  argument: the `except` is **narrow** and names the one type the two failing mechanisms raise
  (`**` on a non-mapping, and a signature that rejects the kwargs); the construction **is** the
  check rather than something wrapped around one — the answer this function returns *is* the
  instance, so failing to produce one is the negative answer and not a check that blew up; and
  the failure arm is the **safe** arm rather than a permit, which is the property the catalogue
  entry is really about. The direction test is what settles it: the catalogued shape converts
  "cannot determine" into "permit", and this arm converts "cannot build the view whose boundary
  I would run" into "decline to run a boundary", which enforces *more*, not less.
- **The decline arm was verified safe before it was written, by execution.** The chain that
  makes declining safe has four links, and `docs/builder/temp-tests/r1/test_w2p3_decline_arm_is_the_fallback.py`
  measures them at the site the CSRF middleware reads them (a `CsrfViewMiddleware` subclass that
  records what it sees in its own `process_view`, so the observation is taken from inside the
  chain rather than from a unit call):
  - `_package_view_instance` answers `None` for the rejected-`dict` callback — asserted directly.
  - `process_view` therefore returns `None` and writes no stamp — observed
    `_BOUNDARY_ENFORCED` absent (`stamp=False`) on the request the CSRF entry judges.
  - the exemption is therefore truthy at that read — observed `bool(_CSRF_ORDERING_EXEMPTION)`
    is `True`.
  - the view supplies both halves itself. This is the only link a *forged* callback cannot
    exhibit, because there is no package view behind it (and the forged callback carries no
    `csrf_exempt` at all, so Django's CSRF middleware applies to it in full — observed
    `callback_exempt=False`, i.e. declining loosens nothing). So it is measured on the one
    declined shape that does have a view behind it, a real capped mount reached through a
    marker-dropping wrapper: `status=413` with `stamp=False`, `exemption=True`,
    `callback_exempt=True` — the boundary ran in the view, the chain's CSRF skipped the callback,
    and the view's own `csrf_protect` continuation is what checks CSRF (entry 14's 5 rows are
    that continuation's bound). **The fallback arrangement, confirmed rather than assumed.**
- **What the arm cannot mask.** Declining a *genuine* mount would be the fail-open the finding
  warns about, and it cannot happen quietly: Django's own `as_view` closure constructs the same
  class with the same `initkwargs` for the same request, so a mount whose `__init__` truly
  cannot be called still raises there — exactly as it would with this middleware uninstalled.
  The arm moves such a failure's site, never its loudness. This is stated in the docstring, since
  it is the invariant that makes the arm legitimate.
- **The two `isinstance` clauses stay ahead of the construction.** Two reasons, and the first is
  the substantive one: it is what stops a non-class `view_class` being *called*. Behaviourally
  they are now subsumed for every input any row supplies (measured — the auxiliary 0-row run
  above), so they are a clause of one recognition rather than a boundary of their own, which is
  how the manifest measures them.
- **Docstrings state the invariant, never the process.** `_package_view_instance`'s docstring now
  says the recognition ends at the instance and why the `TypeError` arm is an absent answer
  rather than a swallowed failure; the module docstring's one-line description of the recognition
  changed from "the bookkeeping needed to build the instance" to "building the instance from the
  bookkeeping", which is what the code now does. No review round, finding, severity, artifact
  filename or review document is named anywhere in the diff.

### Correction to the pass-2 build report (Low 2)

`ARTIFACT.md` forbids editing a prior section, so the correction lands here.

**The pass-2 build report is wrong where it says
`::test_a_chain_with_the_boundary_and_no_csrf_middleware_still_checks_csrf` "is pinned by entry
3's and entry 13's mutants instead, not by this one"** (`### Failability proofs`, the entry-7
reading, repeated in `### Notes for Worker 3`). That sentence was not measured, and it is false:
the node id appears in the failing set of **none** of the thirteen pass-2 entries, and it is
set-equal in my own pass-3 re-run, so it is absent from all thirteen here too.

**The boundary that actually bounds that row is
`django_strawberry_framework/views.py #"_csrf_protected_run = csrf_protect(_run_after_csrf_check)"`
and its async twin** — the view's unconditional CSRF continuation. Measured by this pass as
manifest **entry 14**: dropping the `csrf_protect` wrapper from both continuations fails **5**
rows with 0 collection/setup errors, both parametrizations of that row among them. So the row is
a real bound and the pass-1 Medium finding is genuinely closed; what was wrong was the record of
*which* boundary it bounds. The true answer is also the more useful one, and it is what the same
report's own note 4 to Worker 1 says two sections later — so the pass-2 record argued with itself
about the only row closing that finding. It no longer does.

I added the continuation to the manifest rather than only correcting the prose, for two reasons:
the correction is then a measurement of mine rather than a claim inherited from a review, and a
5-row boundary that closes a finding is worth a permanent record even though `BUILD.md`
`### What needs a proof` does not require one (the continuation is not new in this round).

### The review's third Low, acknowledged and deliberately not changed

`_declared_charset_is_unhonourable`'s docstring being the only remaining citation of `spec-046`
Decision 10 for the `utf-8-sig` refusal is recorded by the review as a readability observation
with **no change requested**, and I am not "fixing" it: the only alternative is restating the
rule at `::_enforce_body_charset_declaration` as well, which is exactly the prose duplication
DRY (f) removed. The pointer from the method to the helper is intact, so the rule is one hop away
and stated once. Nothing in the diff touches either docstring.

### Notes for Worker 3

- **The interesting measurement in this pass is the auxiliary 0-row run**, not the 3-row entry
  12. It is what says the two `isinstance` clauses and the construction attempt are one boundary
  rather than two, and it is what falsifies the pass-2 review's "entry 12's current anchor and
  its two rows survive either way". `docs/builder/temp-tests/r1/proofs-pass3-aux.json` is one
  entry carrying pass 2's anchor verbatim; re-run it if you distrust the reading — expect exit
  **1** and `WEAKLY PINNED`, which is the intended result and not a failure of this pass.
- **Entry 12's mutation is a deletion of six lines, so read the replacement.** It leaves
  `return view_class(**initkwargs)` in place, i.e. it removes the recognition and keeps the
  dereference — which is what makes all three parametrizations `500`.
- **Entry 14 mutates `views.py`, which this pass does not otherwise touch.** Its restore is
  proved like every other (`sha256 e8aeb156550fc45a…`, the same value entries 1, 2 and 7 record
  for that file and the same value the pass-2 review recorded), and `views.py` is byte-unchanged
  by this pass — nothing in `### Files touched` names it.
- **The decline-arm probe observes from inside the chain**, via a `CsrfViewMiddleware` subclass
  recording `stamp` / `exemption` / `callback_exempt` in its own `process_view`. A unit call on
  `_package_view_instance` would have proved only the first of the four links, which is the trap
  worth knowing about if you re-derive it.
- **The hot-path metric that matters here is the micro one.** A `try` block is nanoseconds and
  the 400-iteration request median cannot resolve it; the request median is recorded because the
  plan declares it, and the micro A/B (including a floor re-measurement at Python 3.10.19, where
  a `try` is not free) is what actually bounds the cost.
- `scripts/review_inspect.py` was **not** re-run this pass. The diff is one `try` / `except`
  around an existing expression plus docstrings in a file whose overview Worker 3 regenerated in
  pass 2, and one fixture plus one parametrization in a test file. Recorded as an explicit skip
  with its reason per `BUILD.md` `### When to run the helper during build`; the review-time
  obligation is yours and the file is 30 lines of new logic short of the threshold either way.

### Notes for Worker 1 (spec reconciliation)

Everything pass 1, pass 2 and both reviews recorded stands. These are additions, and nothing
here is fixed in this pass.

1. **A sibling shape survives the widened guard, and closing it is a contract call rather than a
   builder's.** A callback that forges the marker onto a `view_class` that is a real class the
   middleware *can* build — measured with `view_class = dict`, `view_initkwargs = {}` — still
   raises out of `process_view` (`AttributeError`, since the built object has no
   `_enforce_request_boundary`), because recognition ends at "an instance was produced" and not
   at "an instance that carries the boundary". Measured, not reasoned, with a scratch probe under
   the session scratchpad. The finding this pass closed was about the construction *failing*;
   this is the construction *succeeding* on something that is not a package view. Closing it
   means recognition has to probe for the boundary itself (a `getattr` for
   `_enforce_request_boundary` on the built instance, since this module deliberately cannot
   import the view classes), which widens what the recognizer knows about the view and is
   therefore a design decision, not a fix — and the same question the review put as its Low 1
   path 2: whether the package owes a controlled response to a callback forging its private
   marker at all. If the answer is no, the two docstring claims ("a hook whose every other
   outcome is a controlled response") want narrowing in `middleware/request_body.py`'s module
   docstring and in `::_package_view_instance`, and nothing else changes. If the answer is yes,
   it is one `getattr` plus one row, and `spec-046` Decision 18 should say which of the two the
   contract is.
2. **Decision 18's recognition sentence, if R2 writes one.** The contract the code now
   implements is: *the boundary middleware runs a package view's boundary only for a callback it
   can build that view's instance from; any other callback keeps its exemption and the view-local
   arrangement.* Pass 2's note 3 asks Decision 18 for a sentence about the declined-callback
   state; this is the clause that makes "declined" precise, and the three
   `::test_a_marked_callback_the_middleware_cannot_build_is_declined_not_crashed` rows plus entry
   12's 3-row mutant are what pin it.
3. **The pass-2 build report carries one false sentence, corrected in this report rather than in
   place** (`### Correction to the pass-2 build report (Low 2)`). If final verification quotes
   either report's account of what pins
   `::test_a_chain_with_the_boundary_and_no_csrf_middleware_still_checks_csrf`, the correct
   boundary is `views.py #"_csrf_protected_run = csrf_protect(_run_after_csrf_check)"` at 5 rows,
   now manifest entry 14.

---

## Review (Worker 3, pass 3)

Re-review of Worker 2's pass-3 delta against `## Review (Worker 3, pass 2)`'s two open Lows. Read
end to end first: `AGENTS.md`, `START.md`, `BUILD.md`, `ARTIFACT.md`, `worker-3.md`,
`docs/README.md`, `examples/fakeshop/test_query/README.md`,
`docs/spec-046-transport_security-0_0_15.md`, its `-rationale.md`,
`docs/builder/build-046-transport_security-0_0_15.md` (`# Closeout cycle (card 046)`: V1-V9, M-A,
W-1, D-1), this artifact's three plans / three build reports / two prior reviews, and
`docs/builder/worker-memory/worker-3.md`. Worker 0's, 1's and 2's memory files were not read.

### The tree under review is the tree the builder proved against

Read before any mutation, and it is the check pass 2 learned to run: every file the pass-3 manifest
mutates hashes to exactly the pre-mutation SHA prefix the build report records for it, so no
post-proof edit landed between the proof run and this review.

| File | `shasum -a 256` (first 16) | Build report's recorded prefix | Entries |
| --- | --- | --- | --- |
| `django_strawberry_framework/views.py` | `e8aeb156550fc45a` | `e8aeb156550fc45a` | 1, 2, 7, 14 |
| `django_strawberry_framework/middleware/request_body.py` | `6ef3ad5e35ebc9e7` | `6ef3ad5e35ebc9e7` | 3, 6, 12 + aux |
| `django_strawberry_framework/_boundary_ordering.py` | `b2c25d9a66a6090c` | `b2c25d9a66a6090c` | 4, 5, 13 |
| `django_strawberry_framework/_request_body.py` | `2c1fd48618d4b01c` | `2c1fd48618d4b01c` | 8 |
| `django_strawberry_framework/consumers.py` | `1bdf298c473fd1a0` | `1bdf298c473fd1a0` | 9, 10, 11 |

`consumers.py` is additionally byte-identical to `HEAD`, verified read-only:
`git show HEAD:django_strawberry_framework/consumers.py` into the session scratchpad then `cmp` -
exit **0**. So `ba69`'s relocation-free half of the round is untouched by three build passes.

### Independent re-run: the mutations, declared before they were made

Recorded here **before** any edit, per `worker-3.md` `## Scope` and `BUILD.md`
`### Who performs it`. Every mutation is transient, one at a time, reverted inside this pass, each
revert proved by byte comparison against a pre-mutation copy taken to a scratch path **outside** the
repository. No `git checkout` / `restore` / `stash` / `worktree` anywhere in this pass; the tree is
legitimately dirty with the build's own work.

Scratch root: `<session scratchpad>/w3p3` (outside the repo).

1. **The whole fourteen-entry pass-3 manifest**, re-run mechanically through
   `scripts/prove_failability.py` from Worker 2's own
   `docs/builder/temp-tests/r1/proofs-pass3.json`, at the scopes recorded there
   (`tests/test_views.py` for 1-8 and 12-14, `tests/test_routers.py` for 9-11), into my own scratch
   root and my own `--output docs/builder/temp-tests/r1/w3p3-rerun.md`. Worker 2's
   `proofs-pass3.json` / `.md` are **not** overwritten.
2. **The auxiliary entry**, `docs/builder/temp-tests/r1/proofs-pass3-aux.json` — pass 2's entry-12
   anchor verbatim (the two `isinstance` lines deleted, construction attempt left standing), scope
   `tests/test_views.py`. Re-run because it is the measurement that decides whether my own pass-2
   sentence was wrong, and a claim that a reviewer's sentence is falsified is exactly the claim a
   reviewer must not accept on the builder's record.
3. **W3-M3, declared here before it was made** — the same narrow anchor as (2), re-measured at a
   **wider scope** that adds one probe file of my own,
   `docs/builder/temp-tests/r1/test_w3p3_isinstance_witness.py`
   (manifest `docs/builder/temp-tests/r1/proofs-w3p3-aux2.json`). The question (2) cannot answer is
   whether the zero means "no boundary here" or "no row supplies the distinguishing input", and
   `worker-3.md` `### Suspect the fixture before accepting "untestable"` puts that question on this
   pass. The probe supplies a callable non-class `view_class`, which the clause refuses before the
   call and the construction would call.

All three are reverted and proved reverted below under `### Revert proof`.

### Failability proof audit, and the independent re-run

**Audited: all fourteen records.** Every entry carries the boundary by symbol-qualified path, the
exact mutation, the scope as run, the pre-mutation state of that same scope, the listed node ids, a
separate collection/setup-error count, and a restore proved by `filecmp.cmp(shallow=False)` plus
SHA-256. **Collection/setup errors: 0 on every one of the fourteen**, parsed out of the emitted
record rather than read from prose. **No entry measured zero rows** — the lowest is 2 — so the
record's `why 0: not applicable` is correct as written. **No entry is weakly pinned** as recorded.

**Re-run: all fourteen, at the scopes Worker 2 recorded**, through `scripts/prove_failability.py`
on Worker 2's own `proofs-pass3.json`, into my own scratch root outside the repo and my own
`--output docs/builder/temp-tests/r1/w3p3-rerun.md` (Worker 2's files untouched).
`--check-anchors-only` first: **exit 0**, all fourteen anchors matched exactly once **before any
copy was taken**, which is also what says no prior pass left a live mutation. Full run: **exit 0**.
The mandatory floor is satisfied with room — entries 2, 4, 6, 9, 10, 11 and 12 are at 3 rows or
fewer and every entry sits on a security decision, so the floor is effectively the whole manifest
and the whole manifest was re-run. **Nothing was accepted on Worker 2's record alone.**

**Node-id sets, mine vs Worker 2's, and Worker 2's vs pass 2's — compared as sets, never as
counts** (parsed programmatically out of the three emitted `.md` records):

| # | W2 pass 3 | This pass | set-equal | errors | vs pass 2 |
| --- | --- | --- | --- | --- | --- |
| 1 | 7 | 7 | yes | 0 | set-equal |
| 2 | 2 | 2 | yes | 0 | set-equal |
| 3 | 4 | 4 | yes | 0 | set-equal |
| 4 | 3 | 3 | yes | 0 | set-equal |
| 5 | 13 | 13 | yes | 0 | set-equal |
| 6 | 3 | 3 | yes | 0 | set-equal |
| 7 | 14 | 14 | yes | 0 | set-equal |
| 8 | 6 | 6 | yes | 0 | set-equal |
| 9 / 10 / 11 | 2 / 2 / 2 | 2 / 2 / 2 | yes | 0 | set-equal |
| 12 | 3 | 3 | yes | 0 | **+1, none lost** (different anchor — below) |
| 13 | 7 | 7 | yes | 0 | set-equal |
| 14 | 5 | — new — | yes | 0 | n/a |

**Fourteen of fourteen set-equal.** The build report's two movement claims are exactly as recorded
and I re-derived both by set difference: entry 12 gained precisely
`::test_a_marked_callback_the_middleware_cannot_build_is_declined_not_crashed[/marked-rejected-initkwargs/]`
and lost nothing; entry 14 is new. **Entry 14's five rows are set-identical to the set my own pass-2
W3-M2 measured by hand** — the same node ids, in a run I did not perform the same way — which is
the strongest form of corroboration available for a correction.

**Entry 14 audited on its own terms.** It mutates `views.py`, which pass 3 does not otherwise
touch, and the audit question is whether that file came back. It did: `views.py` hashes to
`e8aeb156550fc45a` before and after my whole run, the same value entries 1, 2 and 7 record and the
same value pass 2's review recorded. The build report is right that entry 14 owes no proof
(`BUILD.md` `### What needs a proof` scopes the obligation to boundaries a pass introduces, and the
`csrf_protect` continuation predates the round); adding it anyway is the right call, because it
turns a corrected attribution into a measurement rather than a claim inherited from a review.

### Entry 12's widened anchor: my pass-2 sentence was wrong, and the widening is only half right

**Wrong, plainly.** My `## Review (Worker 3, pass 2)` Low 1 wrote *"Proof entry 12's current anchor
and its two rows survive either way."* Re-measured on Worker 2's own auxiliary manifest
(`docs/builder/temp-tests/r1/proofs-pass3-aux.json`, pass 2's anchor verbatim) into my own scratch
root and my own `--output docs/builder/temp-tests/r1/w3p3-aux.md`:

- exit **1**, verdict `**WEAKLY PINNED - revision-needed**`, **0 rows**, 0 collection/setup errors;
- pre-mutation state of that scope `195 passed` (exit 0), mutant run `195 passed` (exit 0);
- restore proved: `filecmp.cmp(shallow=False) True; sha256 6ef3ad5e35ebc9e7… == 6ef3ad5e35ebc9e7…`.

So the sentence is falsified exactly as the build report says. The mechanism is not subtle in
hindsight and I should have derived it before asserting it: with the construction attempt standing,
deleting the two clauses changes no answer for any row `tests/test_views.py` supplies, because
`None(**None)` and `view_class(**[…])` both raise the `TypeError` the new arm catches. **A sentence
about what a mutant will do is a measurement, not a prediction** — the same lesson my pass-2 Low 2
recorded against Worker 2's attribution claim, and I then broke it in the same section.

**The half that is right.** Keeping pass 2's narrow anchor in the pass-3 record would have shipped a
0-row entry, which the acceptance rule forbids, and the widened anchor's mutation genuinely removes
a boundary (the whole recognition after the two `getattr`s) and fails 3 rows. That entry is sound.

**The half that is not.** Re-scoping the anchor removed the round's only pinning of the two
`isinstance` clauses without replacing it, and the "one decision with one answer" argument that
licenses the re-scope is false as measured. See Medium below: there is an input for which the
clauses change the answer, `tests/test_views.py` does not supply it, and the direction of the
change is an uncontrolled `500`.

### The `try` / `except TypeError` shape, judged against the catalogue rather than against the argument

`BUILD.md` `### Fail-open shapes` catalogues "a **bare `except`** (or an over-broad
`except Exception`) **wrapped around a check**, which converts 'the check blew up' into 'the check
passed'". Read against `middleware/request_body.py::_package_view_instance` #"except TypeError:",
three tests and the direction test decide it, and I ran the direction test by execution rather than
by reading the build report's account of it:

1. **Not bare and not over-broad.** `except TypeError` names the one type both failure mechanisms
   raise — `**` on a non-mapping, and a signature that will not accept the kwargs.
2. **Not wrapped around a check.** The function's answer *is* the instance, so a failure to produce
   one is the negative answer, not a check that blew up. There is no separate predicate whose
   exception is being reinterpreted.
3. **The failure arm enforces more, not less.** The catalogued shape converts "cannot determine"
   into "permit". This arm converts "cannot build the view whose boundary I would run" into
   "decline to run a boundary", and declining routes the request onto the view-local arrangement,
   where the view runs the boundary itself and re-enters CSRF through `csrf_protect`.

**The one genuine risk in the shape, and it is measured rather than argued.** `except TypeError` is
wider than "the signature rejected the kwargs": it also catches a `TypeError` raised arbitrarily
deep inside a *genuine* consumer view's `__init__`, which is the input where declining could
actually skip a boundary. `docs/builder/temp-tests/r1/test_w3p3_decline_moves_no_failure.py` mounts
a real capped `DjangoGraphQLView` subclass whose `__init__` raises `TypeError` for a reason that is
not a signature mismatch, POSTs an over-limit multipart body through an **enforcing** client
carrying a token-shaped `csrftoken` cookie, and counts real
`django.http.multipartparser.MultiPartParser.parse` invocations on both chains:

| Chain | Outcome | `MultiPartParser.parse` calls |
| --- | --- | --- |
| `[boundary, stock CSRF]` | `TypeError('a consumer __init__ that cannot be called')` | **0** |
| `[stock CSRF]` (uninstalled) | `TypeError('a consumer __init__ that cannot be called')` | **0** |

Identical exception type, identical message, identical parse count. So the docstring's invariant —
Django's own `as_view` closure constructs the same class with the same kwargs for the same request,
so the arm moves such a failure's **site** and never its **loudness** — holds by execution, and no
body is parsed on the declined path. Both readings reproduce unchanged at the floor (Python
3.10.19 / Django 5.2).

**And the probe is proved capable of counting**, which is the half a zero is worthless without: the
same counter on the same chain with the same body against a mount carrying **no** exemption reads
`status=403 parses=1`. My first attempt at this probe used a default `Client()` and read `0` on the
control too — the `_dont_enforce_csrf_checks` short-circuit my pass-1 memory names — so the
capability check is what turned this table from a measurement of my fixture into a measurement of
the code.

**Verdict: this is not the catalogued shape, and the failure arm's direction is safe.**

### The decline arm's safety chain: the measurement supports three links, and the fourth needs a different argument

Worker 2's four links are read at the right site — a `CsrfViewMiddleware` subclass recording
`stamp` / `exemption` / `callback_exempt` inside its own `process_view`, so the observation is taken
from inside the chain. I re-ran `docs/builder/temp-tests/r1/test_w2p3_decline_arm_is_the_fallback.py`
unmodified: **3 passed** in `.venv` and **3 passed** at the floor. Django's
`CsrfViewMiddleware.process_view` reads `getattr(callback, "csrf_exempt", False)` *before* it
short-circuits on `_dont_enforce_csrf_checks`, so that subclass's readings are valid even on a
non-enforcing client — I checked, because a non-enforcing client is exactly what invalidates a
*parse-count* reading in the same file.

**Where the measurement does not support the claim it is used for.** The build report reads
`callback_exempt=False` on its forged callback as "declining loosens nothing". That is a property of
*that fixture*: its forged callback simply does not set `csrf_exempt`. A forger who copies the
marker can copy `csrf_exempt` too, and then the chain's CSRF entry skips the callback — the input
where declining could loosen something. Measured, in
`docs/builder/temp-tests/r1/test_w3p3_decline_arm.py`, on a marked callback with unbuildable
bookkeeping **and** its author's own `csrf_exempt = True`:

| Chain | Status | `stamp` | `callback_exempt` |
| --- | --- | --- | --- |
| `[boundary, observing CSRF]` | `200` | `False` | `True` |
| `[observing CSRF]` (uninstalled) | `200` | `False` | `True` |

**The two answers are identical.** That equivalence — not the fixture's exemption value — is what
makes declining safe: whatever the callback's own `csrf_exempt` says, the answer under the installed
chain is the answer the same request would get with the middleware absent, so the middleware is
never what dropped a check. A truthy `csrf_exempt` on a foreign callback is that callback author's
own chain-wide opt-out and predates this round entirely. **The claim is right; its recorded evidence
is narrower than the claim.** Recorded as prose here rather than as a change request, per
`ARTIFACT.md`'s rule that a correction of an earlier section lands in mine.

### High:

None.

### Medium:

#### The two `isinstance` clauses now have a distinguishing input, an uncontrolled-`500` failure direction, and **zero** permanent rows — the round's own guard lost its pinning in this pass

`middleware/request_body.py::_package_view_instance` #"if not isinstance(view_class, type)". Pass 2
pinned this guard at 2 rows. Pass 3's construction attempt subsumed both of those rows' answers, so
the guard now measures **0** (Worker 2's auxiliary run, which I reproduced above), and pass 3's
response was to widen the anchor onto the whole recognition rather than to add a row. The argument
offered for that — the clauses and the construction are "one decision with one answer", so measuring
them as one boundary is `BUILD.md` `### Slice splitting`'s one-unit criterion — is **false as
measured**. They answer different questions:

- the construction asks *does calling this produce an instance?*
- `isinstance(view_class, type)` asks *is this thing safe to **call** at all?*

A `view_class` that is **callable but not a class** distinguishes them, and the build report itself
names the behaviour ("they are what stops a non-class `view_class` being *called* at all") without
pinning it. Measured, not reasoned. `docs/builder/temp-tests/r1/test_w3p3_isinstance_witness.py`
mounts a marked callback whose `view_class` is a plain factory function and whose `view_initkwargs`
is `{}`; W3-M3 re-runs pass 2's narrow anchor at the scope
`tests/test_views.py docs/builder/temp-tests/r1/test_w3p3_isinstance_witness.py`:

```
2 failed, 195 passed        (pre-mutation: 197 passed, exit 0; collection/setup errors: 0)
FAILED docs/builder/temp-tests/r1/test_w3p3_isinstance_witness.py::test_a_callable_non_class_view_class_is_never_called
FAILED docs/builder/temp-tests/r1/test_w3p3_isinstance_witness.py::test_a_callable_non_class_view_class_is_declined_not_crashed
```

**Two rows fail, and both are mine — not one row comes from `tests/test_views.py`.** So this is
`worker-3.md` `### Suspect the fixture before accepting "untestable"` rather than
`BUILD.md` `### Harness-impossible interleavings`: an ordinary package test with a URLconf and a
`Client()` reaches it, so the zero is a gap in the suite, not an absence of boundary, and the
prescribed response is more rows.

**The failure direction is uncontrolled**, which is why this is not cosmetic. With the clauses gone
the factory is called, answers a foreign object, and `process_view` reaches
`view._enforce_request_boundary(request)` on it:

```
unguarded answer: <_NotAView object at 0x…>
process_view would raise: AttributeError '_NotAView' object has no attribute '_enforce_request_boundary'
```

— i.e. exactly the unhandled `500` from a hook the guard exists to prevent, measured against a local
copy of the unguarded body so no production file was mutated for that reading.

**Severity Medium** under `BUILD.md` `## Severity definitions` ("missing tests for important
branches"), and `revision-needed` independently of severity under
`### Acceptance rule: weakly pinned is revision-needed`, whose remedy is "more (or better-targeted)
rows — never a weaker boundary, and never a recorded exception". Re-scoping the anchor so the zero
leaves the record is the shape that rule exists to catch, even when — as here — the wider entry it
was replaced with is itself sound.

**Recommended change**, all three parts, all inside files this pass already owns:

1. **Promote the two probe rows** into `tests/test_views.py`: a
   `_marked_callback_with_a_callable_view_class` fixture (marker, `view_class` = a factory function,
   `view_initkwargs = {}`), a `marked-callable-view-class/` URL pattern, a fourth parametrization of
   `::test_a_marked_callback_the_middleware_cannot_build_is_declined_not_crashed` (its existing
   `startswith("marked, ")` assertion fits unchanged), **and** one unit-level row asserting
   `_package_view_instance(...) is None`. At least **two** rows are required, or the narrow anchor is
   weakly pinned at 1.
2. **Restore the narrow anchor as its own manifest entry**, alongside the widened one, so both
   answers are pinned separately. With (1) in place it fails 2 rows.
3. **Re-label the widened entry.** It is recorded as
   `::_package_view_instance #"if not isinstance(view_class, type)"` while its mutation deletes six
   lines including the construction, so a later reader who greps that label will conclude the
   `isinstance` clause is pinned at 3 rows — the precise false reading this finding is about. Name
   the whole recognition instead (e.g. `::_package_view_instance` with the anchor on `try:`).

**Not part of this finding: `isinstance(initkwargs, dict)`.** Its distinguishing input is a non-`dict`
*mapping*, and removing the clause makes recognition **wider** (the mapping splats, a real instance
is built, the boundary runs) rather than fail open. Worth one sentence of docstring if anything; no
row is owed. Naming it here so the fix does not over-build.

### Low:

#### `::_package_view_instance`'s rewritten docstring claims a property the code does not have, and the resolution is bound to the maintainer's open contract call

`middleware/request_body.py::_package_view_instance` #"a hook whose every other outcome is a
controlled response". Pass 3 rewrote this docstring and kept that clause. It is false, and the
escalated note in the same build report is what makes it false: recognition ends at *an instance was
produced*, not at *an instance carrying the boundary*, so a callback that forges the marker onto a
buildable-but-unrelated class reaches `view._enforce_request_boundary(request)` on a foreign object.
Measured independently in `docs/builder/temp-tests/r1/test_w3p3_decline_arm.py`, with
`view_class = dict` and `view_initkwargs = {}`:

```
forged-buildable recognizer answer: {} type=dict
forged-buildable raised: AttributeError("'dict' object has no attribute '_enforce_request_boundary'")
```

identically at the floor, so it is not interpreter-specific. Two sites carry the claim, and a third
and fourth restate it in test prose:

- `middleware/request_body.py::_package_view_instance` #"a hook whose every other outcome is a
  controlled response" — the production claim;
- `middleware/request_body.py` #"so no non-package view is touched" — pre-existing at `HEAD` and
  unchanged in substance, but now weaker than it reads: with a forged marker a non-package class is
  instantiated and an attribute is read off it;
- `tests/test_views.py::_marked_callback_without_a_view_class` and
  `::test_a_marked_callback_the_middleware_cannot_build_is_declined_not_crashed` restate it in their
  docstrings and would follow whichever way the contract goes.

**No code change is recommended and none is requested here.** Whether the package owes a controlled
response to a callback forging its private marker is a contract call that is with the maintainer,
and this docstring is *path 2* of that same decision: if the answer is "the package owes one", the
clause becomes true after a one-`getattr` probe and nothing needs narrowing; if the answer is "a
forged marker is not a supported seam", the clause wants narrowing at all four sites. Holding the
pass on the docstring would pre-empt the decision, so this is recorded and escalated rather than
raised as a change request. **My reading, for the record: the clause as written is a claim the code
does not keep, and it should not ship in either resolution without being made accurate.**

One piece of evidence for that decision that no pass has put in front of it yet: the sibling
middleware in the same package already answers "is this one of ours?" without constructing anything
— `middleware/debug_toolbar.py::GraphQLDebugToolbarMiddleware.process_view` #"issubclass(view,
BaseView)" reads `view_class` and tests `isinstance(view, type) and issubclass(view, BaseView)`,
importing `BaseView` from `strawberry.django.views`, i.e. from **upstream**, not from `views.py`. So
a narrower recognition is available without reintroducing the layering inversion A-1 removed. It
would still not establish *carries the boundary* (a consumer can subclass `BaseView` without the
package mixin), which is why the `getattr(instance, "_enforce_request_boundary", None)` probe is the
one that answers the question — but the precedent is worth having on the table.

### DRY findings

**(a) The pass-3 delta introduces no duplication.** Measured, not eyeballed:
`scripts/review_inspect.py` on `middleware/request_body.py` with `--output-dir docs/shadow` reports
**repeated string literals: 0** and **Django / ORM markers: 0**. No literal it emits appears in
`_boundary_ordering.py`'s or `views.py`'s overview either.

**(b) A new control-flow hotspot, walked rather than accepted.** The overview now flags
`_package_view_instance` as spanning 43 lines with 5 branch nodes — new relative to pass 2, and the
only entry in that section. Read against the source: 32 of the 43 lines are the docstring, the body
is ten lines with four early returns and one `try`, and the fifth "branch node" is the `or` inside
the `isinstance` conjunct. Not a complexity finding; recorded because the section requires every
entry to be walked.

**(c) Two sibling middlewares in `middleware/` answer "is this one of our views?" two structurally
different ways, and pass 3 widened the gap.** `debug_toolbar.py` answers by class
(`isinstance(view_class, type) and issubclass(view_class, BaseView)`, no instantiation);
`request_body.py` now answers by construction. My pass-1 memory flagged this pair as a watch item
and pass 1 escalated the layering half of it, which A-1 fixed. **No consolidation is recommended**:
the two need different answers (a tag for the toolbar, an instance whose `max_request_body_bytes` is
the mount's for the boundary), and folding them would put policy in the wrong module. Recorded under
Low above as evidence for the open contract call rather than as a DRY change request. **Not an
existence challenge either** — `_package_view_instance` has one caller but is the answer the hook
branches on and the anchor two manifest entries need; pass 2's ground for keeping it is unchanged.

**(d) The one duplication in the delta is deliberate and correct.**
`docs/builder/temp-tests/r1/test_w2p3_hotpath_recognizer.py::_without_the_construction_guard` is a
hand copy of the pre-guard body. It is a gitignored temp probe and the copy is what makes metric 2
one experiment with two arms rather than two experiments; nothing to consolidate.

### Fail-open shape hunting: the pass-3 delta

`BUILD.md` `### Fail-open shapes`, read over what this pass added or changed rather than over what it
fixed. Pass 2's seven items are unchanged and not re-litigated; these are the delta's.

1. **`try: return view_class(**initkwargs) / except TypeError: return None`** — judged in full above
   against all four catalogue tests, with the "wider than a signature mismatch" risk closed by
   execution on both chains with a proved-capable parse counter. **Not a finding.**
2. **The two `getattr(..., None)` defaults, re-read now that the answer downstream of them
   changed** — the defaults still stand in for meaningful absence deliberately, there is still no
   `or {}` / `or ()`, and the answer they feed is now `None` = decline = the fallback arm, which the
   measurement above shows is answer-identical to the middleware being absent. **Not a finding**;
   the guard's *coverage* is the Medium above, not its direction.
3. **No clamp, no `or` fallback, no truthiness test on a possibly-absent value, and no new default
   reached because an input was incoherent** anywhere in the delta — the delta is one `try`, one
   `except`, four docstrings and one test fixture. Read line by line rather than asserted.

### Non-weakening checks

- **The delta is additive.** `tests/test_views.py` collects **195** tests against the 194 pass 2
  recorded, and exactly one collected id is new
  (`::test_a_marked_callback_the_middleware_cannot_build_is_declined_not_crashed` now has 3
  parametrizations). Twelve of thirteen pass-2 proof entries re-ran **set-equal** across roughly
  forty distinct node ids, which is the mechanical evidence that no existing row was renamed,
  re-scoped or weakened — a rename would have moved at least one set.
- **The guard was widened, never narrowed.** Every input pass 2's `_package_view_instance` declined
  is still declined; the arm adds one more decline and removes none.
- **Nothing was weakened to buy the hot-path number back**, and the number was not bought: see
  below.
- **The other three findings' sites are untouched.** Entries 1, 2, 7, 8, 9, 10 and 11 are set-equal
  to pass 2's, and `consumers.py` is byte-identical to `HEAD`.
- **Exactly one complete CSRF check in all three arrangements still holds**, and the declined arm's
  half is now bounded in both directions: entry 14's 5 rows bound the view's continuation, and the
  installed-vs-uninstalled equivalence table above bounds the chain's.

### Dispatched findings checklist walk

- **Box 2** stays `- [x]` from pass 2 and the tick is still warranted: its contract (an over-limit
  multipart refused before parsing while an under-limit request reaches and obeys the project's own
  `CsrfViewMiddleware` subclass) is untouched by this diff — entry 3's four rows and entry 13's seven
  rows are set-equal to pass 2's in my own re-run.
- **Boxes 1, 3, 4** stay `- [ ]` under the plan-level deferral recorded twice (pass-1 plan checklist
  preamble, pass-2 plan `### Routing confirmations`): their contracts landed in `2701f41a` /
  `ba66ab49`, so Worker 1 ticks them at final verification where a tick means landed **and** audited.
  A recorded deferral, not a silent one — no Medium finding. Entries 1, 2, 7, 8, 9, 10 and 11, all
  set-equal, are the evidence that this pass touched none of their sites.
- **No box was ticked, unticked or edited by pass 3**, confirmed by reading the checklist rather than
  the report's account of it. **I ticked nothing** — the walk is an audit, per this pass's contract.

### Public-surface check

`git diff HEAD -- django_strawberry_framework/__init__.py` is **empty**: `__all__` and the re-export
list are unchanged. `middleware/request_body.py`'s `__all__` is still the single-name tuple
`("GraphQLRequestBodyBoundaryMiddleware",)`, so the documented `MIDDLEWARE` string is unchanged and
no consumer's settings line moves. `_package_view_instance` is private and has no importer outside
its own module (`grep -rn '_package_view_instance' --include='*.py' .` — the definition, one call
site, two docstring references, and this pass's gitignored probes; nothing in any test tree imports
it). `_boundary_ordering.py` remains private: no `__all__`, every name underscore-prefixed, no
`__init__.py` export in the package root or in `middleware/`.

### Static inspection helper

Run this pass, with `--output-dir docs/shadow` as every build-cycle invocation must:

```shell
uv run python scripts/review_inspect.py django_strawberry_framework/middleware/request_body.py --output-dir docs/shadow
```

**No skips.** `_boundary_ordering.py` and `views.py` were regenerated in pass 2 and are byte-
unchanged since (`b2c25d9a66a6090c` / `e8aeb156550fc45a`), so re-running them would emit identical
overviews; the one file the delta changed was regenerated. Worker 2's recorded skip is its own and
is legitimate — `BUILD.md` `### When to run the helper during build` puts the review-time obligation
on Worker 3, and Worker 2 "may re-run". On the trigger question Worker 2 is also right that the
delta is under the 30-new-logic-line threshold either way; I ran it regardless, because the delta
changes the branch structure of the file's only hotspot.

Findings from the output are recorded under `### DRY findings` (a) and (b). Original-source line
numbers cited throughout this review; no shadow-file line number appears anywhere in it.

### Hot-path budget

**Both numbers exist, before and after, same experiment on both arms — which is the whole of my
obligation.** Whether ~15 ns per request is acceptable is the maintainer's call and I do not judge
it; nothing was weakened to buy it back (the guard is strictly wider than what it replaced).

- **Metric 2, the one that can resolve a `try`, reproduced twice** on
  `docs/builder/temp-tests/r1/test_w2p3_hotpath_recognizer.py` unmodified, 200,000 iterations, both
  arms in one process: per-call **0.5435 -> 0.5402 us** (delta **-0.0033 us**) and **0.5393 ->
  0.5652 us** (delta **+0.0259 us**). Both deltas land inside the recorded band (-0.0206 to
  +0.0295). The experiment is genuinely one experiment: the "before" arm is a copy of the pre-guard
  body in the same module measured by the same `timeit` call over the same iteration count, which is
  the right shape when the before-code no longer exists on the tree.
- **Re-measured at the floor**, where a `try` is not free: **+0.0027 us** per call at Python
  3.10.19, between the two readings the report records (+0.0004 and +0.0154).
- **Metric 1, the declared per-request median, reproduced** on
  `docs/builder/temp-tests/r1/test_r1_hotpath.py` unmodified, 400 iterations after a discarded
  warm-up: installed **332.29 us**, fallback control **333.38 us**, delta **-1.08 us**. The absolute
  sits ~3% above the recorded 309-322 band while the arm-to-arm delta reproduces in sign and
  magnitude (recorded -0.83 us), which is the same conclusion the report draws from it — the
  per-request median cannot resolve a change this size, and the control arm moving with it is what
  says so. Recorded, not judged; not a finding.

### Floor verification

**The plan's declaration is R1's one floor run, and I re-ran it in full.** Floor facts taken from
`BUILD.md` `## Floor verification`, its single canonical statement, never from memory or from a
number restated in a document: the supported floor is **Django 5.2.0 on Python 3.10 with
strawberry-graphql 0.316.0**.

- `/tmp/dsf-floor` existed from the prior passes and was **reused only after reading its versions**.
  `/tmp/dsf-floor/bin/python -V` -> **Python 3.10.19**;
  `uv pip list --python /tmp/dsf-floor/bin/python` reads **django 5.2**, **strawberry-graphql
  0.316.0**, asgiref 3.12.1, channels 4.3.2, daphne 4.2.3, pytest 9.1.1, pytest-django 4.12.0,
  pytest-asyncio 1.4.0, and `django-strawberry-framework 0.0.14` editable at this checkout — so the
  venv is the floor and it carries this pass's change.
- `/tmp/dsf-floor/bin/python -m pytest tests/test_views.py tests/test_routers.py --no-cov` —
  **340 passed**, my own run, the full declared scope (the build report ran only `test_views.py`;
  the plan names both files, so the second half is re-established here rather than assumed).
- The three declined rows named individually rather than hidden in the aggregate:
  `[/marked-no-view-class/]`, `[/marked-bad-initkwargs/]`, `[/marked-rejected-initkwargs/]` —
  **3 passed** at the floor, so the `TypeError` a rejected `dict` raises is caught by the same arm at
  3.10 as at 3.14 (the message differs between interpreters; the type does not).
- Both decline-arm probes at the floor: Worker 2's **3 passed**, mine **2 passed**, with identical
  readings to `.venv` — including the forged-buildable `AttributeError`, so the Low above is not an
  artifact of the newer interpreter.
- **The shared `.venv` is unmutated**, read rather than asserted: `uv pip list` reports **django
  6.0.5**, asgiref 3.11.1, strawberry-graphql 0.316.0, and `.venv/bin/python -V` is **Python
  3.14.2** — still far above the floor, so no floor install leaked into it. Every floor command was
  invoked as `/tmp/dsf-floor/bin/python -m pytest` or carried an explicit
  `--python /tmp/dsf-floor/bin/python`.

### Test-staleness sweep

Run independently, never against the artifact's file list (`worker-3.md`: the tree it missed is by
definition the one that cannot appear in the diff).

- **Neither `BUILD.md` shape applies**: no example-model field set changed and no wire shape was
  converted.
- **The one staleness this delta could create is a stranded reader of the changed helper.**
  `grep -rn '_package_view_instance' --include='*.py' .` over the whole repository: hits only inside
  `middleware/request_body.py` and in gitignored probes. No test tree imports it.
- **The marker / stamp / exemption readers across all three trees**, since the delta changes what
  the recognizer answers: `grep -rln 'graphql_request_body_boundary\|_BOUNDARY_MARKER\|_BOUNDARY_ENFORCED\|_CSRF_ORDERING_EXEMPTION'`
  matches `_boundary_ordering.py`, `middleware/request_body.py`, `views.py`, `tests/test_views.py`
  and one false positive (`scripts/review_inspect.py`'s unrelated `_TOKEN_BOUNDARY_MARKERS`,
  confirmed by reading both hits). No per-app tree and no `examples/fakeshop/test_query/` file reads
  any of them.
- **No test tree asserts the behaviour this delta changed.** `grep -rn 'not_a_view_kwarg\|== 500'`
  across `tests/` and `examples/`: the only `not_a_view_kwarg` sites are the new fixture and
  `::test_an_unknown_as_view_kwarg_is_rejected_by_djangos_class_attribute_guard`, which is the
  standing pin that `as_view` refuses such a kwarg — i.e. the reason a *genuine* mount cannot carry a
  rejected `dict`, and corroboration for the row's shape rather than a staleness. The two `== 500`
  rows in the live tier are about unpatched upstream behaviour, unrelated.
- **The sibling tier the delta could have stranded is green**, my own run:
  `uv run pytest tests/test_views.py tests/test_routers.py examples/fakeshop/test_query/test_transport_api.py --no-cov`
  — **409 passed** (195 + 145 + 69). The live tier reaches `_package_view_instance` through its own
  probe wrapper, which is why it is in scope.
- No `--cov*` flag was used in any run in this pass; every invocation carried `--no-cov`.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Not applicable to the pass-3 delta; it modifies no docs, release metadata, KANBAN or archive
surface. Confirmed rather than assumed: the round's only generated-file change,
`examples/fakeshop/apps/kanban/constants.py`, is still the single added line
`"django_strawberry_framework/_boundary_ordering.py",` in `TRACKED_FILE_PATHS`
(`git diff HEAD` on that path), i.e. byte-unchanged since pass 2 and exactly what W-1 authorizes.
`git diff --cached --name-status` is still exactly `A django_strawberry_framework/_boundary_ordering.py`
— the one authorized staged path, nothing added, nothing removed.

### What looks solid

- **The fix does what the finding asked.** All three unbuildable shapes are now declined, the third
  is pinned by a permanent row, and the row is one an ordinary consumer could never produce
  (`as_view` refuses the kwarg), which is the right place for it.
- **The docstring rewrite is honest about the arm's nature** — it states the invariant (Django's own
  closure re-raises, so the site moves and the loudness does not) rather than the process, and that
  invariant survived the sharpest test I could aim at it, on both interpreters.
- **The correction to the pass-2 build report is the right shape**: prose in the current section per
  `ARTIFACT.md`, plus a manifest entry so the corrected claim is a measurement. Its 5-row set is
  set-identical to what I measured by hand in pass 2, from a different starting point.
- **The proof discipline is exemplary at the mechanical level.** Anchors checked first and separately,
  every restore proved by `filecmp` plus SHA-256, no `git` anywhere, `consumers.py` re-verified
  against `HEAD`, and all five files' pre-mutation SHAs match the record exactly — so the tree I
  reviewed is provably the tree the proofs were taken on, with no post-proof edit.
- **The pass volunteered its own most damaging measurement.** The auxiliary 0-row run exists only
  because Worker 2 went looking for it, and it is what falsifies my own pass-2 sentence. A build
  report that hands the reviewer the number that embarrasses the reviewer is doing the job.
- **The escalation is correctly routed**: the sibling forged-buildable shape is stated as a contract
  call with both resolution paths and no code written for it, which is exactly right.

### Temp test verification

Files used this pass, all under `docs/builder/temp-tests/r1/` (gitignored):

- `test_w3p3_decline_arm.py` — **new, mine.** Three rows: the recognizer's answer for the forged
  buildable shape, the `AttributeError` out of `process_view`, and the installed-vs-uninstalled
  equivalence on a chain-exempt forged callback. **Disposition: kept as review evidence.** Row 3's
  property (declining is answer-identical to the middleware being absent) is the strongest available
  statement of the arm's safety and is a promotion candidate; whether it lands depends on the same
  contract call, so it is recorded for Worker 1 rather than demanded of Worker 2.
- `test_w3p3_decline_moves_no_failure.py` — **new, mine.** The site-not-loudness invariant plus the
  parse-counter capability control. **Disposition: kept as review evidence**, promotion candidate
  alongside the above.
- `test_w3p3_isinstance_witness.py` — **new, mine, and the one that must not stay a temp test.** It
  catches a real gap (the Medium above), so `worker-3.md` `## Temp test rules` applies: it is
  recorded as a Medium finding and **Worker 2 must promote its two rows** into
  `tests/test_views.py`. Do not leave it as the only proof of a shipped guard.
- `proofs-w3p3-aux2.json`, `w3p3-aux2.md`, `w3p3-aux2.log` — W3-M3's manifest and record.
- `w3p3-rerun.md` / `.log`, `w3p3-aux.md` / `.log` — my re-runs of Worker 2's two manifests, written
  to my own paths; Worker 2's `proofs-pass3.json` / `.md` / `proofs-pass3-aux.*` are untouched.
- Worker 2's `test_w2p3_decline_arm_is_the_fallback.py`, `test_w2p3_hotpath_recognizer.py` and
  pass 1's `test_r1_hotpath.py` were **re-run unmodified**, in `.venv` and (the first two) at the
  floor. Not edited.

### Revert proof

Three mutation runs, all mechanized, all restored inside this pass, each proved by byte comparison
against a pre-mutation copy taken to a scratch path **outside** the repository:

- **Manifest re-run (14 entries)** — every entry `filecmp.cmp(shallow=False) True` plus matching
  SHA-256; runner exit **0**.
- **W3-M2 / the auxiliary entry** — `filecmp.cmp(shallow=False) True; sha256 6ef3ad5e35ebc9e7… ==
  6ef3ad5e35ebc9e7…`; runner exit 1 by design (`WEAKLY PINNED`), which is the measurement, not a
  restore failure.
- **W3-M3** — `filecmp.cmp(shallow=False) True; sha256 6ef3ad5e35ebc9e7… == 6ef3ad5e35ebc9e7…`;
  runner exit **0**.

Whole-tree confirmation after everything: all five source files hash to their pre-review values
(`views.py e8aeb156550fc45a`, `middleware/request_body.py 6ef3ad5e35ebc9e7`,
`_boundary_ordering.py b2c25d9a66a6090c`, `_request_body.py 2c1fd48618d4b01c`,
`consumers.py 1bdf298c473fd1a0`); no `ACTIVE-MUTATION.json` and no `RESTORE-FAILED.json` anywhere
under either scratch root; `git status --short` is unchanged from task start apart from this
artifact; and `uv run ruff format --check`, `uv run ruff check` and
`scripts/check_trailing_commas.py --check` on the two files this pass reviewed all pass (`2 files
already formatted`, `All checks passed!`, exit 0). No `git checkout` / `restore` / `stash` /
`worktree` at any point in this pass.

### Notes for Worker 1 (spec reconciliation)

Everything pass 1's, pass 2's and Worker 2's three reports recorded stands. These are additions, and
nothing here is fixed in this pass.

1. **Escalated: the forged-buildable shape and the docstring claim are one maintainer decision, and
   the docstring is the half that must move either way.** Worker 2's note 1 states the contract call
   correctly and I confirmed its measurement independently (`view_class = dict`,
   `view_initkwargs = {}` -> `AttributeError` out of `process_view`, at 3.14 and at the floor). What
   I add: whichever way the call goes, `middleware/request_body.py::_package_view_instance` #"a hook
   whose every other outcome is a controlled response" is currently a claim the code does not keep,
   and three further sites restate it (the module docstring's #"so no non-package view is touched",
   and two docstrings in `tests/test_views.py`). Resolution paths: **(i)** the package owes a
   controlled response -> one `getattr(instance, "_enforce_request_boundary", None)` probe plus at
   least two rows, and all four docstrings become true unchanged; **(ii)** a forged marker is not a
   supported seam -> record that rejection reason and narrow all four. New evidence for the choice:
   `middleware/debug_toolbar.py` already recognizes package views by class using an **upstream**
   `BaseView` import, so a narrower recognition needs no import of `views.py` and reintroduces no
   layering inversion — though it still would not establish *carries the boundary*, which only the
   `getattr` probe does. `spec-046` Decision 18 should say which contract it is.
2. **Decision 18's recognition sentence, with one clause added to Worker 2's.** Worker 2's proposed
   sentence is right and I would extend it: *the boundary middleware runs a package view's boundary
   only for a callback whose bookkeeping it can build that view's instance from, and it never calls
   anything that is not a class to try* — the second clause is the `isinstance(view_class, type)`
   contract, which is the Medium above and which R2 should state whether or not the row lands.
3. **The pass-2 build report's false attribution is corrected twice over** — in Worker 2's pass-3
   report and by my own measurement here — and the correct boundary is
   `views.py #"_csrf_protected_run = csrf_protect(_run_after_csrf_check)"` at 5 rows, now manifest
   entry 14, whose node-id set is identical to the one I measured by hand in pass 2. If final
   verification quotes any report's account of what pins
   `::test_a_chain_with_the_boundary_and_no_csrf_middleware_still_checks_csrf`, that is the answer.
4. **My own pass-2 review carries one false sentence, corrected in this section rather than in
   place** (`### Entry 12's widened anchor`): "entry 12's current anchor and its two rows survive
   either way" is falsified at 0 rows. Anyone auditing the pass-2 Low should read it with that
   correction attached.
5. **Items 1-6 of my pass-2 notes and items 1-2 of Worker 2's pass-3 notes remain R2's and R3's**,
   unchanged. In particular the rationale's Decision 18 rejected-alternative bullet that describes
   the shipped design is still the most misleading shape in the companion file, and M-A's live-tier
   opportunity for the High fix's central assertion is still R3's to take or decline.

### Review outcome

`revision-needed`.

**Both pass-2 Lows are genuinely closed, and the pass is strong everywhere it is mechanical.** The
recognizer now guards its answer rather than two spellings of its input, all three unbuildable shapes
are declined with a controlled response, and the third is pinned by a permanent row no consumer mount
could produce. The `try` / `except TypeError` is **not** the catalogued fail-open shape — narrow
type, the construction *is* the answer, and the failure arm enforces more rather than less — and its
one real risk, a `TypeError` from deep inside a genuine consumer `__init__`, is closed by execution:
identical exception, identical message and **0** real `MultiPartParser.parse` calls on the installed
and uninstalled chains, with the parse counter proved capable of reading 1. The decline arm is
answer-identical to the middleware being absent even for a callback carrying its own `csrf_exempt`,
which is a stronger statement than the build report's own evidence supports and I measured it rather
than accept it. All fourteen proof records audit clean, **all fourteen re-ran set-equal to Worker 2's
node-id sets** with 0 collection/setup errors and no zero-row entry, twelve are set-equal to pass 2's,
entry 14's five rows are set-identical to what I measured by hand in pass 2, every restore is proved
by `filecmp` plus SHA-256, and every file's pre-mutation SHA matches the record — so the tree I
reviewed is provably the tree the proofs were taken on. The floor run happened as declared and I
re-ran the plan's **full** declared scope at **340 passed**, with the shared `.venv` read and
unmutated. Both hot-path metrics exist, are one experiment on both arms, and reproduce inside their
recorded bands. **And my own pass-2 sentence was wrong**: entry 12's old anchor measures 0 rows, not
2, exactly as the build report says.

**What holds it at `revision-needed` is one Medium that this pass created:**

The two `isinstance` clauses were pinned at 2 rows before this pass and are pinned at **0** after it.
The re-scoping of entry 12 that removed the zero from the record rests on an argument — "one decision
with one answer" — that is false as measured: a **callable non-class `view_class`** distinguishes the
clauses from the construction, and with the clauses gone that input is *called*, answers a foreign
object, and reaches `view._enforce_request_boundary` on it, i.e. the uncontrolled `500` the guard
exists to prevent. My W3-M3 run shows pass 2's narrow anchor failing **2 rows** the moment one
distinguishing input exists — **both of them mine, none from `tests/test_views.py`**. So this is a gap
in the suite, not a harness limitation, and `BUILD.md` `### Acceptance rule: weakly pinned is
revision-needed` prescribes more rows, "never a weaker boundary, and never a recorded exception".
Widening the anchor so the zero leaves the record is precisely the move that rule exists to catch —
even though the wider entry it was replaced with is itself sound. The fix is a fixture, a URL
pattern, a fourth parametrization, one unit row and a restored manifest entry, all in files this pass
already owns, plus a re-label of entry 12 so its symbol-qualified path stops naming a line its
mutation is no longer about.

**The Low is escalated, not held against the pass.** `::_package_view_instance`'s rewritten docstring
claims "a hook whose every other outcome is a controlled response", and the forged-buildable shape
falsifies it at 3.14 and at the floor — but which way it should be made true is the maintainer's open
contract call, and demanding a docstring change now would pre-empt it. Recorded with both resolution
paths under `### Notes for Worker 1`, per `worker-3.md`'s escalation route.

`worker-3.md`'s acceptance gate turns on the Medium alone: a weakly-pinned boundary is not accepted
and not exceptable, the missing rows are cheap, and only a builder pass can produce the proof entry
that closes it. Everything else in this pass I would accept as it stands.

---

## Build report (Worker 2, pass 4)

An apply-changes pass whose whole scope is the one **Medium** `## Review (Worker 3, pass 3)`
left open: the two bookkeeping-shape tests in
`middleware/request_body.py::_package_view_instance` had a distinguishing input, an
uncontrolled-`500` failure direction, and - after pass 3 widened proof entry 12 onto the whole
recognition - **zero** permanent rows. It is closed the way
`BUILD.md` `### Acceptance rule: weakly pinned is revision-needed` prescribes: two permanent
rows supplying the distinguishing input, the narrow anchor restored as its own manifest entry
(now **2 rows**), and entry 12 re-labelled so its symbol-qualified path names the recognition its
mutation is actually about. The review's **Low** is bound to an open maintainer contract call and
is deliberately left untouched - `### The review's Low, left untouched, and why`.

Read end to end first: `AGENTS.md`, `START.md`, `docs/builder/BUILD.md`,
`docs/builder/ARTIFACT.md`, `docs/builder/worker-2.md`, `docs/TREE.md`,
`docs/spec-046-transport_security-0_0_15.md`,
`docs/builder/build-046-transport_security-0_0_15.md` (`# Closeout cycle (card 046)`, including
`## Maintainer decision M-A`, `## Write-set correction W-1` and
`## Worker-0 dispatch decision D-1`), this artifact's three plans, three build reports and three
reviews, and `docs/builder/worker-memory/worker-2.md`. The spec's `-rationale.md` was **not**
read - the required-reading matrix marks it `never` for this role - and no other worker's memory
file was read. The **W2** column of `BUILD.md` `## Required reading per worker` was walked rather
than accepted from the dispatch: it marks `yes` for `AGENTS.md`, `START.md`, `BUILD.md`,
`ARTIFACT.md`, the own role file, `docs/TREE.md`, the active spec, the active build plan, the
current `bld-*` artifact and own worker memory. Nothing was omitted and the matrix asks for
nothing the dispatch did not name.

**The production delta is empty**, and that is measured rather than asserted: every production
file this round touches hashes to exactly the value
`## Review (Worker 3, pass 3)` `### The tree under review is the tree the builder proved against`
recorded for it, re-read after this pass's proof run.

| File | `shasum -a 256` (first 16) | Pass-3 review's recorded prefix |
| --- | --- | --- |
| `django_strawberry_framework/views.py` | `e8aeb156550fc45a` | `e8aeb156550fc45a` |
| `django_strawberry_framework/middleware/request_body.py` | `6ef3ad5e35ebc9e7` | `6ef3ad5e35ebc9e7` |
| `django_strawberry_framework/_boundary_ordering.py` | `b2c25d9a66a6090c` | `b2c25d9a66a6090c` |
| `django_strawberry_framework/_request_body.py` | `2c1fd48618d4b01c` | `2c1fd48618d4b01c` |
| `django_strawberry_framework/consumers.py` | `1bdf298c473fd1a0` | `1bdf298c473fd1a0` |

`consumers.py` is additionally byte-identical to `HEAD`, verified read-only:
`git show HEAD:django_strawberry_framework/consumers.py` into a scratch path outside the
repository, then `cmp` - exit **0**. No `git checkout` / `restore` / `stash` / `worktree` at any
point in this pass.

### Files touched

Grounded in `git status --short` after both ruff invocations, not in memory.

- `tests/test_views.py` - the Medium's fixture and its two rows. Added: `_NotAPackageView`,
  `_view_class_factory` with its module-level call log `_VIEW_CLASS_FACTORY_CALLS`,
  `_marked_callback_with_a_callable_view_class` with its marker and two attribute assignments, a
  `marked-callable-view-class/` URL pattern, a fourth parametrization of
  `::test_a_marked_callback_the_middleware_cannot_build_is_declined_not_crashed` (that test's
  docstring rewritten to state four shapes as one recognition), the new row
  `::test_a_callable_view_class_that_is_not_a_class_is_never_called`, and `_package_view_instance`
  added to the existing `middleware.request_body` import.
- `docs/builder/bld-046-r1-remediation_review.md` - this report appended at top level; the
  artifact's `Status:` line set to `built`. **No prior section edited** (`ARTIFACT.md`); the
  correction this pass owes to an earlier section is prose here, under `### Failability proofs`.

Untracked / gitignored scratch this pass wrote: `docs/builder/temp-tests/r1/proofs-pass4.json`,
`proofs-pass4.md`, `run-pass4.log`, `proofs-pass4-only12-15.md`, `run-pass4-only12-15.log`, and
`docs/builder/worker-memory/worker-2.md`. Pass 1's, pass 2's and pass 3's manifests and emitted
records were **not** overwritten.

Baseline-dirty and **untouched by this pass** (`AGENTS.md` #34): all five production files above,
`tests/test_routers.py`, `examples/fakeshop/apps/kanban/constants.py`, and
`docs/builder/build-046-transport_security-0_0_15.md`. **Nothing was staged or unstaged**:
`git diff --cached --name-status` is still exactly
`A django_strawberry_framework/_boundary_ordering.py`, the one path `W-1` authorizes, and that
file's bytes are unchanged by this pass. No new tracked file was created, so `W-1`'s `git add` and
constants regenerate are not owed - verified rather than assumed under `### Validation run`.

### Tests added or updated

Both rows are in `tests/test_views.py`. Package-tier placement per `AGENTS.md` #10 is unchanged
and correct: a callback that forges the package's private marker onto a factory function is not a
request shape any live fakeshop query can reach, and
`views.py::_RequestBodyBoundaryMixin.as_view` never produces one.

- `::test_a_marked_callback_the_middleware_cannot_build_is_declined_not_crashed[/marked-callable-view-class/]`
  - the fourth shape, and the one neither a test of the bookkeeping's *shape* nor a test of the
  *construction* can reach: `view_class` is callable and is not a class and `view_initkwargs` is
  `{}`, so the construction would succeed and answer a foreign object. The row's assertions are
  the parent test's unchanged pair - a controlled `200` whose body starts `"marked, "` - which is
  exactly what an `AttributeError` out of `process_view` breaks.
- `::test_a_callable_view_class_that_is_not_a_class_is_never_called` - the unit answer,
  `_package_view_instance(...) is None`, **plus** the property that makes declining safe rather
  than merely quiet: the factory records every call it receives and the row asserts it received
  none while the recognizer ran. A recognition that called the factory and then rejected what came
  back would answer the same `None` and produce the same `200`, so the unrecorded call is as much
  of the contract as the `None` is.
- `_NotAPackageView`, `_view_class_factory`, `_VIEW_CLASS_FACTORY_CALLS` and
  `_marked_callback_with_a_callable_view_class` - the fixture behind both rows, each docstringed
  with what makes it the shape the other three routes cannot supply.

Nothing else changed. No existing assertion was weakened, renamed, or re-scoped, and the
mechanical evidence is in the proof record rather than in this sentence: `tests/test_views.py`
collects **197** against pass 3's 195, exactly two collected ids are new, and thirteen of
pass 3's fourteen entries re-ran **set-equal** across 47 distinct node ids - a rename or a
re-scope would have moved at least one set.

**Judged rather than transcribed** (`worker-2.md`'s standing rule). The review's recommended
change is right and is adopted, with one strengthening and two deliberate non-adoptions:

- **Strengthened.** The review's probe used an inert factory, so its unit row could assert only
  the answer. Recording the calls costs three lines and lets the row pin the clause's own contract
  - *nothing but a class is ever called* - rather than only the consequence of that contract
  holding today. The honest limit of that second assertion is stated in `### Notes for Worker 3`:
  it is not what discriminates entry 15's mutant.
- **Not adopted, on the review's own instruction:** `isinstance(initkwargs, dict)` gets no row.
  Its distinguishing input is a non-`dict` *mapping*, and removing the clause makes recognition
  **wider** rather than fail open, so a row there would pin a preference and not a boundary.
- **Not adopted:** the review's parenthetical that the same clause is "worth one sentence of
  docstring if anything". Every docstring in question lives in `middleware/request_body.py`, whose
  claims are the subject of the maintainer's open contract call, and adding a sentence there now
  would put this pass inside a decision it does not own - for a clause whose behaviour the
  docstring already states ("The two ``isinstance`` tests stay ahead of the construction so it is
  only ever a class that gets called"). Recorded rather than done silently.

### Validation run

- `uv run ruff format tests/test_views.py` - pass (`1 file left unchanged`). Scoped to this pass's
  one file, never `.`.
- `uv run ruff check --fix tests/test_views.py` - pass (`All checks passed!`), nothing to fix.
- `uv run python scripts/check_trailing_commas.py tests/test_views.py` - `Fixed 0 file(s)`; then
  `--check` - **exit 0**. Run because the gate's ruff step does not cover the source-layout hook
  that gates commits (line length 100, ASCII-only `.py`, trailing-comma explode-at-threshold - the
  new four-element `parametrize` list is written exploded for exactly that threshold).
- **`pre-commit` could not be run, and was substituted rather than skipped.** The binary is not on
  `PATH` here (`uv run pre-commit` fails to spawn; `.pre-commit-config.yaml` documents
  `uvx pre-commit`, which would fetch it). Its four hooks were run directly instead:
  `source-layout` (the `check_trailing_commas.py` invocation above), `ruff-format`, `ruff-check`,
  and `kanban-tracked-path-constants` - the last **verified as a no-op**, since it is the one that
  can roll a commit back: `examples/fakeshop/apps/kanban/constants.py` was copied to a scratch
  path outside the repository, `scripts/build_kanban_tracked_path_constants.py` was re-run, and
  `cmp` reports the file **byte-stable**. So this pass adds no tracked path and the commit-time
  regenerate cannot conflict.
- `git status --short` after both ruff invocations - the eight tracked entries and the one
  untracked artifact listed under `### Files touched`, every one accounted for. **Nothing
  unexpected**, so there is nothing to report as churn and nothing was reverted.
- Focused runs, every one without any `--cov*` flag:
  - `uv run pytest tests/test_views.py --no-cov` - **197 passed** (195 before this pass).
  - `uv run pytest tests/test_views.py tests/test_routers.py --no-cov` - **342 passed**, both proof
    scopes green after every mutation was reverted (run again after the final proof invocation, not
    only before it).
  - `uv run pytest examples/fakeshop/test_query/test_transport_api.py --no-cov` - **69 passed**.
    Run per `worker-2.md` `## Apply-changes verification scope`: the live tier reaches
    `_package_view_instance` through its own probe wrapper, so it is the sibling tree this change
    could have stranded.
- **Test staleness** (`BUILD.md` `### Test staleness a focused run cannot see`): neither shape
  applies - no example-model field set changed and no wire shape converted - so the full sweep is
  not owed. The one staleness this delta could create is a stranded reader of the changed surface,
  and this pass adds the first importer of `_package_view_instance` outside its own module:
  `grep -rn '_package_view_instance' --include='*.py' .` returns the definition, one call site and
  two docstring references in `middleware/request_body.py`, the new import plus its one use in
  `tests/test_views.py`, and gitignored probes. No per-app tree and no
  `examples/fakeshop/test_query/` file imports it.

### Failability proofs

**All fifteen manifest entries were run in one invocation.** The manifest,
`docs/builder/temp-tests/r1/proofs-pass4.json`, is pass 3's fourteen entries - derived from
`proofs-pass3.json` programmatically rather than retyped, so entries 1-11, 13 and 14 are
character-identical and the sets stay comparable - with two changes:

- **entry 12 re-labelled**, from
  `::_package_view_instance #"if not isinstance(view_class, type)"` to
  `::_package_view_instance (the whole recognition after the two getattrs: both
  bookkeeping-shape tests and the construction attempt)`. Its anchor, replacement and scope are
  untouched. The old label named a line its six-line mutation is no longer about, which is the
  false reading the Medium is about; the parenthesized-scope shape is the one entries 5 and 13
  already use.
- **entry 15 added**, restoring pass 2's narrow anchor - the two shape tests deleted with the
  construction attempt left standing - as its own boundary, so the two answers are pinned
  separately.

Anchor verification was run **first and separately** (`--check-anchors-only`, **exit 0**: all
fifteen matched exactly once **before any copy was taken**, which is also what says no prior pass
left a live mutation). Final run **exit 0**: every entry proved, **no boundary weakly pinned**
(the emitted record carries zero `WEAKLY PINNED` verdicts), **`collection/setup errors: 0` on all
fifteen**, and `filecmp.cmp(shallow=False) True` plus SHA-256 equality on all fifteen restores.

```shell
uv run python scripts/prove_failability.py docs/builder/temp-tests/r1/proofs-pass4.json \
    --scratch-root <session scratchpad>/w2p4 \
    --output docs/builder/temp-tests/r1/proofs-pass4.md
```

**why 0: not applicable to any entry - no entry in the record measured zero rows.** The lowest
count is 2, so neither the weakly-pinned nor the harness-impossible reading is invoked below.

**The record was taken twice, and the second run is the one recorded.** The first invocation
exited **0** with the same fifteen sets; one test docstring was then reworded (a positional "the
row above" replaced by the test's own name), so rather than disclose a post-proof edit the whole
manifest was re-run against the final bytes. The second run reproduced every set exactly. A
`--only 12 --only 15` re-run of the two moved entries afterwards carries a **captured exit 0**
(`docs/builder/temp-tests/r1/proofs-pass4-only12-15.md`, labelled `PARTIAL RECORD` by the runner
as it must be) - the second full invocation was launched detached, so its exit status was not
captured in the shell and the record's own fields plus that captured run stand in its place.

**Node-id set movement against pass 3, computed by symmetric difference** over the parsed node-id
lists of `proofs-pass3.md` versus `proofs-pass4.md`, never as counts:

| # | Pass 3 | Pass 4 | Direction |
| --- | --- | --- | --- |
| 1-11, 13, 14 | 7, 2, 4, 3, 13, 3, 14, 6, 2, 2, 2, 7, 5 | identical sets | **set-equal**; a movement anywhere here would be contamination, since this pass changes no production line |
| 12 | 3 | **5** | **grew** (+2, none lost) - gained exactly the two rows this pass added |
| 15 | - | **2** | new entry: the narrow anchor, no longer weakly pinned |

Three readings the sets give that the counts would hide:

- **Entry 15 is the Medium's close, and its two rows are the two the review's probe supplied**, now
  permanent: `::test_a_marked_callback_the_middleware_cannot_build_is_declined_not_crashed[/marked-callable-view-class/]`
  and `::test_a_callable_view_class_that_is_not_a_class_is_never_called`. Deleting the two shape
  tests while the construction stands **calls** the factory, answers a `_NotAPackageView`, and
  `process_view` then reads `_enforce_request_boundary` off it - the uncontrolled `500` the guard
  exists to prevent. At 2 rows the boundary is out of the weakly-pinned band and inside Worker 3's
  mandatory re-run floor.
- **Entry 12 grew rather than staying at 3, and that is the evidence the two entries are not
  redundant.** Its mutation removes the shape tests *and* the construction, so the new rows fail
  under it too - which is precisely why entry 12 alone cannot tell "refused before the call" from
  "the construction declined it": both answers are gone at once. Entry 15 removes only the first.
  Two sites' worth of answer, two entries.
- **Nothing else moved.** Entries 3, 4, 6 and 12 all mutate
  `middleware/request_body.py`; the first three are set-equal to pass 3's, so the re-label changed
  no measurement, and entries 9, 10 and 11 are set-equal at 2 each, so the `consumers.py`
  boundaries are uncontaminated.

**A correction this pass owes an earlier section, landing here because `ARTIFACT.md` forbids
editing it.** `## Build report (Worker 2, pass 3)` `### Implementation notes` states that the two
shape tests are "behaviourally now subsumed for every input any row supplies (measured - the
auxiliary 0-row run above), so they are a clause of one recognition rather than a boundary of
their own, which is how the manifest measures them." The parenthetical is true and the conclusion
does not follow: *for every input any row supplied* is not *for every input*, and the review found
the input the suite lacked. The clauses are a boundary of their own - a callable non-class
`view_class` is refused by them and accepted by the construction - and entry 15 now measures them
as one. The same sentence's other half stands unchanged and is the reason both entries exist: the
clauses are what stops a non-class `view_class` being *called* at all.

The emitted record follows verbatim, every measured field filled in by the runner.


Procedure, mechanized by `scripts/prove_failability.py`: the target is copied to a scratch path OUTSIDE the repo before any mutation; the mutation site is located by an exact anchor asserted to match exactly once (any other count aborts the entry without writing); the same focused scope is run unmutated first, so rows already failing before the mutation are differenced out of the count; both runs' pytest exit codes are read, because a run that collected nothing or blew up emits no `FAILED` lines and would otherwise be recorded as a measured zero; both runs use `--no-cov`; the file is restored from the pre-mutation copy in a `finally` and the restore is proved by `filecmp.cmp(shallow=False)` plus a SHA-256 comparison. One boundary at a time, restored before the next. `git` is never invoked - the tree is legitimately dirty, so an empty `git diff` is unachievable and forcing one would destroy the build's own work.

| # | Boundary | File mutated | Mutation applied | Rows failed | Errors | Scope as run | Restore proof |
|---|---|---|---|---|---|---|---|
| 1 | `django_strawberry_framework/views.py::_RequestBodyBoundaryMixin._enforce_body_charset_declaration` | `django_strawberry_framework/views.py` | deleted: `if _declared_charset_is_unhonourable(request): raise HTTPException(400, _JSON_PARSE_REASON)` - builder's description (unverified prose): the charset refusal itself deleted: a declared non-UTF-8 charset is read and then ignored (re-anchored onto the DRY (f) helper call; the bare raise line alone occurs 4 times in the file, so the anchor is the two-line block) | **7** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_views.py` | filecmp.cmp(shallow=False) True; sha256 e8aeb156550fc45a... == e8aeb156550fc45a... (vs pre-mutation copy) |
| 2 | `django_strawberry_framework/views.py::_RequestBodyBoundaryMixin._enforce_body_charset_declaration #"if request.method == \"GET\" or _is_multipart_form_post(request)"` | `django_strawberry_framework/views.py` | deleted: `if request.method == "GET" or _is_multipart_form_post(request): return` - builder's description (unverified prose): the GET / multipart carve-out deleted, so the guard claims every request shape including the ones the multipart encoding guard owns | **2** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_views.py` | filecmp.cmp(shallow=False) True; sha256 e8aeb156550fc45a... == e8aeb156550fc45a... (vs pre-mutation copy) |
| 3 | `django_strawberry_framework/middleware/request_body.py::_package_view_instance #"if not getattr(view_func, _BOUNDARY_MARKER, False)"` | `django_strawberry_framework/middleware/request_body.py` | `if not getattr(view_func, _BOUNDARY_MARKER, False):` -> `if True:` - builder's description (unverified prose): the recognition made unconditionally negative: _package_view_instance always answers None, so the chain never runs the boundary and never stamps the request | **4** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_views.py` | filecmp.cmp(shallow=False) True; sha256 6ef3ad5e35ebc9e7... == 6ef3ad5e35ebc9e7... (vs pre-mutation copy) |
| 4 | `django_strawberry_framework/_boundary_ordering.py::_CsrfOrderingExemption.__bool__` | `django_strawberry_framework/_boundary_ordering.py` | `request = _boundary_middleware_request.get() return request is None or not getattr(request, _BOUNDARY_ENFORCED, False)` -> `return True` - builder's description (unverified prose): the withdrawal removed: the exemption is always truthy, so the configured CSRF middleware always skips the callback | **3** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_views.py` | filecmp.cmp(shallow=False) True; sha256 b2c25d9a66a6090c... == b2c25d9a66a6090c... (vs pre-mutation copy) |
| 5 | `django_strawberry_framework/_boundary_ordering.py::_CsrfOrderingExemption.__bool__ (opposite direction)` | `django_strawberry_framework/_boundary_ordering.py` | `request = _boundary_middleware_request.get() return request is None or not getattr(request, _BOUNDARY_ENFORCED, False)` -> `return False` - builder's description (unverified prose): the exemption is always withdrawn, so the view-local arrangement loses its ordering on a chain that does not supply one | **13** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_views.py` | filecmp.cmp(shallow=False) True; sha256 b2c25d9a66a6090c... == b2c25d9a66a6090c... (vs pre-mutation copy) |
| 6 | `django_strawberry_framework/middleware/request_body.py::_require_boundary_before_csrf` | `django_strawberry_framework/middleware/request_body.py` | `boundary_index = csrf_index = None` -> `return boundary_index = csrf_index = None` - builder's description (unverified prose): the ordering audit short-circuited before it reads MIDDLEWARE, so a misordered chain is accepted at startup | **3** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_views.py` | filecmp.cmp(shallow=False) True; sha256 6ef3ad5e35ebc9e7... == 6ef3ad5e35ebc9e7... (vs pre-mutation copy) |
| 7 | `django_strawberry_framework/views.py::_RequestBodyBoundaryMixin._enforce_request_boundary_once` | `django_strawberry_framework/views.py` | `if getattr(request, _BOUNDARY_ENFORCED, False): return self._enforce_request_boundary(request)` -> `return` - builder's description (unverified prose): the view's own enforcement removed entirely: the body boundary runs zero times on any chain that does not carry the middleware | **14** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_views.py` | filecmp.cmp(shallow=False) True; sha256 e8aeb156550fc45a... == e8aeb156550fc45a... (vs pre-mutation copy) |
| 8 | `django_strawberry_framework/_request_body.py::_measured_remaining` | `django_strawberry_framework/_request_body.py` | deleted: `if type(end) is not int or type(position) is not int: return _Probe.UNMEASURABLE` - builder's description (unverified prose): the exact-int gate deleted, so a foreign position/end object's own numeric protocol executes inside the gate | **6** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_views.py` | filecmp.cmp(shallow=False) True; sha256 2c1fd48618d4b01c... == 2c1fd48618d4b01c... (vs pre-mutation copy) |
| 9 | `django_strawberry_framework/consumers.py::_ConnectionRevocation.settle` | `django_strawberry_framework/consumers.py` | `try: await asyncio.shield(self.attempt) except asyncio.CancelledError: self.attempt.cancel() # Suppressed, not swallo...` -> `await asyncio.shield(self.attempt)` - builder's description (unverified prose): the cancel-and-await-and-re-raise arm removed, leaving the bare shielded await this fix replaced: a cancelled settlement leaves the attempt running | **2** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_routers.py` | filecmp.cmp(shallow=False) True; sha256 1bdf298c473fd1a0... == 1bdf298c473fd1a0... (vs pre-mutation copy) |
| 10 | `django_strawberry_framework/consumers.py::_ConnectionRevocation._attempt_close` | `django_strawberry_framework/consumers.py` | deleted: `except asyncio.CancelledError: self.state = _REVOCATION_ABANDONED raise` - builder's description (unverified prose): the terminal-record arm deleted, so a cancelled attempt rests in CLOSING instead of ABANDONED | **2** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_routers.py` | filecmp.cmp(shallow=False) True; sha256 1bdf298c473fd1a0... == 1bdf298c473fd1a0... (vs pre-mutation copy) |
| 11 | `django_strawberry_framework/consumers.py::build_revalidating_consumer_class #"await super().disconnect(code)"` | `django_strawberry_framework/consumers.py` | `try: await super().disconnect(code) finally: await self._revocation.settle()` -> `await super().disconnect(code) await self._revocation.settle()` - builder's description (unverified prose): the try/finally flattened back to two sequential awaits, so a cancelled or raising upstream teardown skips settlement | **2** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_routers.py` | filecmp.cmp(shallow=False) True; sha256 1bdf298c473fd1a0... == 1bdf298c473fd1a0... (vs pre-mutation copy) |
| 12 | `django_strawberry_framework/middleware/request_body.py::_package_view_instance (the whole recognition after the two getattrs: both bookkeeping-shape tests and the construction attempt)` | `django_strawberry_framework/middleware/request_body.py` | `if not isinstance(view_class, type) or not isinstance(initkwargs, dict): return None try: return view_class(**initkwa...` -> `return view_class(**initkwargs)` - builder's description (unverified prose): the whole recognition after the two getattrs deleted - both isinstance clauses and the construction attempt - so a marked callback's view_class and view_initkwargs are dereferenced and splatted unguarded and any callback the class cannot be built from becomes an unhandled 500 out of process_view | **5** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_views.py` | filecmp.cmp(shallow=False) True; sha256 6ef3ad5e35ebc9e7... == 6ef3ad5e35ebc9e7... (vs pre-mutation copy) |
| 13 | `django_strawberry_framework/_boundary_ordering.py::_CsrfOrderingExemption.__bool__ (the per-request key)` | `django_strawberry_framework/_boundary_ordering.py` | `request = _boundary_middleware_request.get() return request is None or not getattr(request, _BOUNDARY_ENFORCED, False)` -> `return _boundary_middleware_request.get() is None` - builder's description (unverified prose): the per-request key removed and the defective predecessor restored: the exemption is withdrawn because a boundary middleware is handling the request, whether or not it ran the boundary for it | **7** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_views.py` | filecmp.cmp(shallow=False) True; sha256 b2c25d9a66a6090c... == b2c25d9a66a6090c... (vs pre-mutation copy) |
| 14 | `django_strawberry_framework/views.py #"_csrf_protected_run = csrf_protect(_run_after_csrf_check)"` | `django_strawberry_framework/views.py` | `_csrf_protected_run = csrf_protect(_run_after_csrf_check) _csrf_protected_async_run = csrf_protect(_async_run_after_c...` -> `_csrf_protected_run = _run_after_csrf_check _csrf_protected_async_run = _async_run_after_csrf_check` - builder's description (unverified prose): the csrf_protect wrapper dropped from both continuations, so the view re-enters its delegate without performing a CSRF check of its own while every other boundary stands | **5** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_views.py` | filecmp.cmp(shallow=False) True; sha256 e8aeb156550fc45a... == e8aeb156550fc45a... (vs pre-mutation copy) |
| 15 | `django_strawberry_framework/middleware/request_body.py::_package_view_instance #"if not isinstance(view_class, type)"` | `django_strawberry_framework/middleware/request_body.py` | deleted: `if not isinstance(view_class, type) or not isinstance(initkwargs, dict): return None` - builder's description (unverified prose): the two bookkeeping-shape tests deleted with the construction attempt left standing, so a view_class that is callable and is not a class is CALLED instead of refused and process_view reads the boundary off whatever it answers | **2** | 0 | `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_views.py` | filecmp.cmp(shallow=False) True; sha256 6ef3ad5e35ebc9e7... == 6ef3ad5e35ebc9e7... (vs pre-mutation copy) |

Verdicts:

1. `django_strawberry_framework/views.py::_RequestBodyBoundaryMixin._enforce_body_charset_declaration` - pinned
2. `django_strawberry_framework/views.py::_RequestBodyBoundaryMixin._enforce_body_charset_declaration #"if request.method == \"GET\" or _is_multipart_form_post(request)"` - inside Worker 3's mandatory re-run floor (<= 3 rows)
3. `django_strawberry_framework/middleware/request_body.py::_package_view_instance #"if not getattr(view_func, _BOUNDARY_MARKER, False)"` - pinned
4. `django_strawberry_framework/_boundary_ordering.py::_CsrfOrderingExemption.__bool__` - inside Worker 3's mandatory re-run floor (<= 3 rows)
5. `django_strawberry_framework/_boundary_ordering.py::_CsrfOrderingExemption.__bool__ (opposite direction)` - pinned
6. `django_strawberry_framework/middleware/request_body.py::_require_boundary_before_csrf` - inside Worker 3's mandatory re-run floor (<= 3 rows)
7. `django_strawberry_framework/views.py::_RequestBodyBoundaryMixin._enforce_request_boundary_once` - pinned
8. `django_strawberry_framework/_request_body.py::_measured_remaining` - pinned
9. `django_strawberry_framework/consumers.py::_ConnectionRevocation.settle` - inside Worker 3's mandatory re-run floor (<= 3 rows)
10. `django_strawberry_framework/consumers.py::_ConnectionRevocation._attempt_close` - inside Worker 3's mandatory re-run floor (<= 3 rows)
11. `django_strawberry_framework/consumers.py::build_revalidating_consumer_class #"await super().disconnect(code)"` - inside Worker 3's mandatory re-run floor (<= 3 rows)
12. `django_strawberry_framework/middleware/request_body.py::_package_view_instance (the whole recognition after the two getattrs: both bookkeeping-shape tests and the construction attempt)` - pinned
13. `django_strawberry_framework/_boundary_ordering.py::_CsrfOrderingExemption.__bool__ (the per-request key)` - pinned
14. `django_strawberry_framework/views.py #"_csrf_protected_run = csrf_protect(_run_after_csrf_check)"` - pinned
15. `django_strawberry_framework/middleware/request_body.py::_package_view_instance #"if not isinstance(view_class, type)"` - inside Worker 3's mandatory re-run floor (<= 3 rows)

Failing node ids, per boundary (the count above is `len()` of this list):

1. `django_strawberry_framework/views.py::_RequestBodyBoundaryMixin._enforce_body_charset_declaration`
   - file mutated: `django_strawberry_framework/views.py`
   - pytest summary: `======================== 7 failed, 190 passed in 5.82s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 197 passed in 8.30s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_views.py::test_a_non_multipart_request_is_not_subject_to_the_form_encoding_check`
   - `tests/test_views.py::test_the_endpoint_refuses_a_json_charset_it_will_not_decode_with[sync-latin-1]`
   - `tests/test_views.py::test_the_endpoint_refuses_a_json_charset_it_will_not_decode_with[sync-utf-8-sig]`
   - `tests/test_views.py::test_the_endpoint_refuses_a_json_charset_it_will_not_decode_with[sync-unknown-name]`
   - `tests/test_views.py::test_the_endpoint_refuses_a_json_charset_it_will_not_decode_with[async-latin-1]`
   - `tests/test_views.py::test_the_endpoint_refuses_a_json_charset_it_will_not_decode_with[async-utf-8-sig]`
   - `tests/test_views.py::test_the_endpoint_refuses_a_json_charset_it_will_not_decode_with[async-unknown-name]`
2. `django_strawberry_framework/views.py::_RequestBodyBoundaryMixin._enforce_body_charset_declaration #"if request.method == \"GET\" or _is_multipart_form_post(request)"`
   - file mutated: `django_strawberry_framework/views.py`
   - pytest summary: `======================== 2 failed, 195 passed in 8.91s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 197 passed in 10.85s =============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_views.py::test_a_get_carrying_a_stray_multipart_content_type_is_not_a_multipart_form`
   - `tests/test_views.py::test_a_multipart_declaration_is_left_to_the_form_encoding_guard`
3. `django_strawberry_framework/middleware/request_body.py::_package_view_instance #"if not getattr(view_func, _BOUNDARY_MARKER, False)"`
   - file mutated: `django_strawberry_framework/middleware/request_body.py`
   - pytest summary: `======================== 4 failed, 193 passed in 5.99s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 197 passed in 8.38s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_views.py::test_the_projects_own_csrf_middleware_runs_when_the_chain_supplies_the_ordering[sync]`
   - `tests/test_views.py::test_the_projects_own_csrf_middleware_runs_when_the_chain_supplies_the_ordering[async]`
   - `tests/test_views.py::test_the_view_does_not_measure_a_body_the_chain_already_measured[sync]`
   - `tests/test_views.py::test_the_view_does_not_measure_a_body_the_chain_already_measured[async]`
4. `django_strawberry_framework/_boundary_ordering.py::_CsrfOrderingExemption.__bool__`
   - file mutated: `django_strawberry_framework/_boundary_ordering.py`
   - pytest summary: `======================== 3 failed, 194 passed in 5.87s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 197 passed in 4.86s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_views.py::test_the_projects_own_csrf_middleware_runs_when_the_chain_supplies_the_ordering[sync]`
   - `tests/test_views.py::test_the_projects_own_csrf_middleware_runs_when_the_chain_supplies_the_ordering[async]`
   - `tests/test_views.py::test_the_async_chain_resets_the_ordering_mark_around_the_downstream_call`
5. `django_strawberry_framework/_boundary_ordering.py::_CsrfOrderingExemption.__bool__ (opposite direction)`
   - file mutated: `django_strawberry_framework/_boundary_ordering.py`
   - pytest summary: `======================== 13 failed, 184 passed in 3.72s ========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 197 passed in 3.73s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_views.py::test_the_view_callback_of_both_views_carries_the_csrf_exempt_mark[sync]`
   - `tests/test_views.py::test_the_view_callback_of_both_views_carries_the_csrf_exempt_mark[async]`
   - `tests/test_views.py::test_without_the_middleware_the_view_keeps_its_own_ordering_and_exemption[sync]`
   - `tests/test_views.py::test_without_the_middleware_the_view_keeps_its_own_ordering_and_exemption[async]`
   - `tests/test_views.py::test_the_async_chain_resets_the_ordering_mark_around_the_downstream_call`
   - `tests/test_views.py::test_installing_the_middleware_parses_no_body_on_either_mount[sync]`
   - `tests/test_views.py::test_installing_the_middleware_parses_no_body_on_either_mount[async]`
   - `tests/test_views.py::test_the_same_two_mounts_parse_nothing_without_the_middleware_either[sync]`
   - `tests/test_views.py::test_the_same_two_mounts_parse_nothing_without_the_middleware_either[async]`
   - `tests/test_views.py::test_a_declined_callbacks_over_limit_body_never_reaches_the_csrf_class[sync]`
   - `tests/test_views.py::test_a_declined_callbacks_over_limit_body_never_reaches_the_csrf_class[async]`
   - `tests/test_views.py::test_a_declined_callback_still_gets_a_complete_csrf_check[sync]`
   - `tests/test_views.py::test_a_declined_callback_still_gets_a_complete_csrf_check[async]`
6. `django_strawberry_framework/middleware/request_body.py::_require_boundary_before_csrf`
   - file mutated: `django_strawberry_framework/middleware/request_body.py`
   - pytest summary: `======================== 3 failed, 194 passed in 3.57s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 197 passed in 3.13s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_views.py::test_a_chain_that_lists_the_boundary_after_csrf_is_refused_at_startup`
   - `tests/test_views.py::test_a_boundary_subclass_listed_after_csrf_is_refused_at_startup`
   - `tests/test_views.py::test_the_first_csrf_entry_is_the_one_the_ordering_is_measured_against`
7. `django_strawberry_framework/views.py::_RequestBodyBoundaryMixin._enforce_request_boundary_once`
   - file mutated: `django_strawberry_framework/views.py`
   - pytest summary: `======================== 14 failed, 183 passed in 2.97s ========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 197 passed in 3.01s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_views.py::test_the_endpoint_refuses_a_json_charset_it_will_not_decode_with[sync-latin-1]`
   - `tests/test_views.py::test_the_endpoint_refuses_a_json_charset_it_will_not_decode_with[sync-utf-8-sig]`
   - `tests/test_views.py::test_the_endpoint_refuses_a_json_charset_it_will_not_decode_with[sync-unknown-name]`
   - `tests/test_views.py::test_the_endpoint_refuses_a_json_charset_it_will_not_decode_with[async-latin-1]`
   - `tests/test_views.py::test_the_endpoint_refuses_a_json_charset_it_will_not_decode_with[async-utf-8-sig]`
   - `tests/test_views.py::test_the_endpoint_refuses_a_json_charset_it_will_not_decode_with[async-unknown-name]`
   - `tests/test_views.py::test_without_the_middleware_the_view_keeps_its_own_ordering_and_exemption[sync]`
   - `tests/test_views.py::test_without_the_middleware_the_view_keeps_its_own_ordering_and_exemption[async]`
   - `tests/test_views.py::test_installing_the_middleware_parses_no_body_on_either_mount[sync]`
   - `tests/test_views.py::test_installing_the_middleware_parses_no_body_on_either_mount[async]`
   - `tests/test_views.py::test_the_same_two_mounts_parse_nothing_without_the_middleware_either[sync]`
   - `tests/test_views.py::test_the_same_two_mounts_parse_nothing_without_the_middleware_either[async]`
   - `tests/test_views.py::test_a_declined_callbacks_over_limit_body_never_reaches_the_csrf_class[sync]`
   - `tests/test_views.py::test_a_declined_callbacks_over_limit_body_never_reaches_the_csrf_class[async]`
8. `django_strawberry_framework/_request_body.py::_measured_remaining`
   - file mutated: `django_strawberry_framework/_request_body.py`
   - pytest summary: `======================== 6 failed, 191 passed in 3.90s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 197 passed in 3.93s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_views.py::test_a_probe_that_fails_without_moving_the_stream_falls_back_to_the_bounded_read[sync-unnumbered-end-position]`
   - `tests/test_views.py::test_a_probe_that_fails_without_moving_the_stream_falls_back_to_the_bounded_read[async-unnumbered-end-position]`
   - `tests/test_views.py::test_a_position_object_whose_numeric_protocol_raises_never_runs_inside_the_gate[sync-subtraction-raises]`
   - `tests/test_views.py::test_a_position_object_whose_numeric_protocol_raises_never_runs_inside_the_gate[sync-comparison-raises]`
   - `tests/test_views.py::test_a_position_object_whose_numeric_protocol_raises_never_runs_inside_the_gate[async-subtraction-raises]`
   - `tests/test_views.py::test_a_position_object_whose_numeric_protocol_raises_never_runs_inside_the_gate[async-comparison-raises]`
9. `django_strawberry_framework/consumers.py::_ConnectionRevocation.settle`
   - file mutated: `django_strawberry_framework/consumers.py`
   - pytest summary: `======================== 2 failed, 143 passed in 8.54s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 145 passed in 10.06s =============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_routers.py::test_cancelling_the_teardown_ends_the_close_attempt_instead_of_orphaning_it`
   - `tests/test_routers.py::test_a_cancelled_disconnect_leaves_no_task_retaining_the_connection`
10. `django_strawberry_framework/consumers.py::_ConnectionRevocation._attempt_close`
   - file mutated: `django_strawberry_framework/consumers.py`
   - pytest summary: `======================== 2 failed, 143 passed in 9.02s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 145 passed in 9.60s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_routers.py::test_cancelling_the_teardown_ends_the_close_attempt_instead_of_orphaning_it`
   - `tests/test_routers.py::test_a_cancelled_disconnect_leaves_no_task_retaining_the_connection`
11. `django_strawberry_framework/consumers.py::build_revalidating_consumer_class #"await super().disconnect(code)"`
   - file mutated: `django_strawberry_framework/consumers.py`
   - pytest summary: `======================== 2 failed, 143 passed in 9.29s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 145 passed in 8.83s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_routers.py::test_a_teardown_cancelled_before_it_returns_still_settles_the_close`
   - `tests/test_routers.py::test_a_teardown_that_raises_still_settles_the_close_and_propagates`
12. `django_strawberry_framework/middleware/request_body.py::_package_view_instance (the whole recognition after the two getattrs: both bookkeeping-shape tests and the construction attempt)`
   - file mutated: `django_strawberry_framework/middleware/request_body.py`
   - pytest summary: `======================== 5 failed, 192 passed in 3.82s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 197 passed in 2.18s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_views.py::test_a_marked_callback_the_middleware_cannot_build_is_declined_not_crashed[/marked-no-view-class/]`
   - `tests/test_views.py::test_a_marked_callback_the_middleware_cannot_build_is_declined_not_crashed[/marked-bad-initkwargs/]`
   - `tests/test_views.py::test_a_marked_callback_the_middleware_cannot_build_is_declined_not_crashed[/marked-rejected-initkwargs/]`
   - `tests/test_views.py::test_a_marked_callback_the_middleware_cannot_build_is_declined_not_crashed[/marked-callable-view-class/]`
   - `tests/test_views.py::test_a_callable_view_class_that_is_not_a_class_is_never_called`
13. `django_strawberry_framework/_boundary_ordering.py::_CsrfOrderingExemption.__bool__ (the per-request key)`
   - file mutated: `django_strawberry_framework/_boundary_ordering.py`
   - pytest summary: `======================== 7 failed, 190 passed in 3.70s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 197 passed in 2.99s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_views.py::test_the_async_chain_resets_the_ordering_mark_around_the_downstream_call`
   - `tests/test_views.py::test_installing_the_middleware_parses_no_body_on_either_mount[sync]`
   - `tests/test_views.py::test_installing_the_middleware_parses_no_body_on_either_mount[async]`
   - `tests/test_views.py::test_a_declined_callbacks_over_limit_body_never_reaches_the_csrf_class[sync]`
   - `tests/test_views.py::test_a_declined_callbacks_over_limit_body_never_reaches_the_csrf_class[async]`
   - `tests/test_views.py::test_a_declined_callback_still_gets_a_complete_csrf_check[sync]`
   - `tests/test_views.py::test_a_declined_callback_still_gets_a_complete_csrf_check[async]`
14. `django_strawberry_framework/views.py #"_csrf_protected_run = csrf_protect(_run_after_csrf_check)"`
   - file mutated: `django_strawberry_framework/views.py`
   - pytest summary: `======================== 5 failed, 192 passed in 3.06s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 197 passed in 3.44s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_views.py::test_each_csrf_continuation_matches_the_transport_it_protects`
   - `tests/test_views.py::test_a_declined_callback_still_gets_a_complete_csrf_check[sync]`
   - `tests/test_views.py::test_a_declined_callback_still_gets_a_complete_csrf_check[async]`
   - `tests/test_views.py::test_a_chain_with_the_boundary_and_no_csrf_middleware_still_checks_csrf[sync]`
   - `tests/test_views.py::test_a_chain_with_the_boundary_and_no_csrf_middleware_still_checks_csrf[async]`
15. `django_strawberry_framework/middleware/request_body.py::_package_view_instance #"if not isinstance(view_class, type)"`
   - file mutated: `django_strawberry_framework/middleware/request_body.py`
   - pytest summary: `======================== 2 failed, 195 passed in 3.19s =========================`
   - pytest exit code: 1
   - pre-mutation (unmutated) state of this scope: `============================= 197 passed in 3.55s ==============================` (pytest exit code 0); pre-existing failing rows excluded from the count: 0
   - collection/setup errors: 0
   - `tests/test_views.py::test_a_marked_callback_the_middleware_cannot_build_is_declined_not_crashed[/marked-callable-view-class/]`
   - `tests/test_views.py::test_a_callable_view_class_that_is_not_a_class_is_never_called`

A boundary whose removal fails 0 or 1 rows is **weakly pinned** and is `revision-needed` per `docs/builder/BUILD.md` - the fix is more or better-targeted rows, never a weaker boundary. A boundary at 3 rows or fewer is inside Worker 3's mandatory independent re-run floor. A proof carrying collection or setup errors, or whose pytest run exited anything but 0 or 1 (nothing collected, interrupted, internal error, usage error), is not a valid count at all - and a 0 from such a run is not a zero-row result: resolve it and re-run.

Every `<fill in ...>` above is a judgement no tool can make and MUST be replaced by hand before this subsection is submitted: weakly pinned and harness-impossible are the two possible readings of a zero-row result and they prescribe opposite responses (more rows, versus a production-call-site invariant assertion plus a recorded harness limitation), so a record that does not name one reads as self-contradictory.

### Hot-path budget

The plan's closeout declaration makes a fixing pass inherit R1's hot-path declaration, and pass 2
declared this `views.py` / middleware path hot. **This pass writes no production line at all** -
the five SHAs in the preamble are the pass-3 review's own recorded values - so before and after are
the same bytes and there is no new per-request cost to measure. That is stated rather than
answered with "not applicable", because the declaration is inherited and an empty answer reads the
same as an unmeasured one.

What the pass owes instead is evidence that the measured path is unchanged, and the standing number
stays pass 3's: worst reading anywhere **~15 ns per request** on a ~314 us request. Reproduced with
pass 2's snippet unmodified (`docs/builder/temp-tests/r1/test_w2p3_hotpath_recognizer.py`, 200,000
iterations, both arms in one process over the identical body, run as
`uv run pytest … -s -o addopts="" --no-cov`):

| Environment | without the guard | with the guard | delta per call |
| --- | --- | --- | --- |
| shared `.venv`, run 1 | 1.3045 us | 1.2558 us | **-0.0487 us** |
| shared `.venv`, run 2 | 0.6084 us | 0.6100 us | **+0.0017 us** |
| floor (Python 3.10.19) | 1.3234 us | 1.3148 us | **-0.0087 us** |

The absolute per-call readings run 1.2-2.6x above pass 3's recorded 0.50-0.53 us band on both
interpreters, and that is the machine rather than the code: the two arms are the same body measured
by the same `timeit` call in the same process, so the delta is what the metric is about and it is
inside pass 3's recorded band (-0.0206 to +0.0295 us) in all three readings, sign included. Metric
1, the declared 400-iteration request median, was **not** re-captured: both the pass-2 plan and the
pass-3 review record that it cannot resolve a change of this size, and this pass changes no
production line for it to resolve. Whether the cost is acceptable is the maintainer's call and no
worker's; nothing was weakened to buy any of it back, because nothing changed.

### Floor verification

**This pass owns the run**, and it is the plan's **full** declared scope -
`tests/test_views.py` **and** `tests/test_routers.py` - not the `test_views.py` half the pass-3
build report ran. Floor facts taken from `BUILD.md` `## Floor verification`, its single canonical
statement, never from memory or from a number restated in a document: the supported floor is
**Django 5.2.0 on Python 3.10 with strawberry-graphql 0.316.0**.

`/tmp/dsf-floor` existed from the prior passes and was **reused only after reading its versions**,
as this pass's dispatch requires:

- `/tmp/dsf-floor/bin/python -V` -> **Python 3.10.19**.
- `uv pip list --python /tmp/dsf-floor/bin/python`, read rather than recalled: **django 5.2**,
  **strawberry-graphql 0.316.0**, asgiref 3.12.1, channels 4.3.2, daphne 4.2.3, pytest 9.1.1,
  pytest-django 4.12.0, pytest-asyncio 1.4.0, and
  `django-strawberry-framework 0.0.14` editable at `/Users/riordenweber/projects/django-strawberry-framework`
  - so the venv **is** the floor and, being editable against this checkout, it carries this pass's
  change.
- `/tmp/dsf-floor/bin/python -m pytest tests/test_views.py tests/test_routers.py --no-cov` -
  **342 passed** (197 + 145), the full declared scope.
- The four decline parametrizations plus the new unit row, named individually rather than hidden
  inside a green aggregate since they are this pass's whole subject:
  `::test_a_marked_callback_the_middleware_cannot_build_is_declined_not_crashed` (all four routes)
  and `::test_a_callable_view_class_that_is_not_a_class_is_never_called` - **5 passed** at the
  floor. So the class test refuses a callable non-class `view_class` at 3.10 exactly as at 3.14,
  and the new row's factory-call assertion holds on both interpreters.
- **The shared `.venv` is unmutated**, read rather than asserted: `uv pip list` reports **django
  6.0.5**, asgiref 3.11.1, strawberry-graphql 0.316.0, and `.venv/bin/python -V` is **Python
  3.14.2** - still far above the floor, so no floor install leaked into it. Every floor command was
  invoked as `/tmp/dsf-floor/bin/python -m pytest` or carried an explicit
  `--python /tmp/dsf-floor/bin/python`, and no `uv pip install` was run in this pass at all.

### Dispatched findings checklist

**No box is ticked, unticked or edited by this pass, and none is untick-worthy.** The finding this
pass closes is a Worker 3 review finding, not a `docs/feedback.md` finding, so it has no box.
Box 2 stays `- [x]` from pass 2 and its contract - an over-limit multipart refused before parsing
while an under-limit request reaches and obeys the project's own `CsrfViewMiddleware` subclass - is
untouched by this diff: entries 3, 4, 5 and 13 are all set-equal to pass 3's. Boxes 1, 3 and 4 stay
`- [ ]` under the plan-level deferral recorded twice (pass-1 plan's checklist preamble, pass-2 plan
`### Routing confirmations`): their contracts landed in `2701f41a` / `ba66ab49`, so Worker 1 ticks
them at final verification where a tick means landed **and** audited. Entries 1, 2, 7, 8, 9, 10 and
11, all set-equal, are the mechanical evidence that this pass touched none of their sites.

### Implementation notes

- **Two rows, and each is a different kind of statement.** The parametrization is the wire answer -
  the request is answered rather than crashed, which is what an `AttributeError` out of a
  `process_view` breaks - and the unit row is the recognizer's own answer plus the property that
  makes the wire answer safe. One of the two alone satisfies the arithmetic (2 rows) but not the
  reason: a wire `200` is also what a recognition that called the factory and rejected its answer
  would produce.
- **The factory records rather than being inert.** Three lines, and they turn "the answer is
  `None`" into "nothing but a class was called", which is the clause's actual contract and the one
  a future refactor could break while keeping the answer.
- **The call assertion is written as a delta, not as an emptiness test.**
  `len(...) == calls_before` rather than `not _VIEW_CLASS_FACTORY_CALLS`, so the row cannot be made
  to pass or fail by whatever ran before it in the module - the wire row does exercise the same
  callback, and under a mutation it *would* call the factory.
- **Package-tier placement, unchanged and deliberate.** Both rows exercise a callback that forges
  the package's private marker; `AGENTS.md` #10's live-first rule does not reach a shape no
  fakeshop query can produce, and the mount that would produce it cannot be built through
  `as_view`.
- **The fourth parametrization reuses the parent test's assertions verbatim**, so the four shapes
  stay one row body with one docstring stating why no two of them are refused by the same test.
  Adding a separate test for the fourth shape would have split one recognition's contract across
  two names.
- **No production line moved**, and that is the choice rather than an accident: the Medium is a
  missing-rows finding, and the guard it is about already behaves correctly.

### The review's Low, left untouched, and why

`## Review (Worker 3, pass 3)`'s Low - `::_package_view_instance`'s docstring claiming "a hook
whose every other outcome is a controlled response", which the forged-buildable shape falsifies -
is **not acted on in this pass**, and the reason is that it is not a builder's to settle. It is
path 2 of the maintainer's **open contract call**: whether the package owes a controlled response
to a callback forging its private marker at all. The two resolutions change different things and
are mutually exclusive:

- if the package owes one, the clause becomes true after a
  `getattr(instance, "_enforce_request_boundary", None)` probe plus at least two rows, and no
  docstring needs narrowing;
- if a forged marker is not a supported seam, the clause and three further sites want narrowing and
  no code changes.

Writing either now would pre-empt the decision, and narrowing a docstring that a `getattr` probe
would make true is work the other resolution throws away. So `middleware/request_body.py` is
byte-unchanged by this pass and all four sites still read as they did. Both paths are small and sit
inside files this cohort already owns, so the decision costs nothing by arriving after this pass.
Recorded here rather than silently deferred, per `worker-2.md`'s requirement that a skipped plan
item say why.

### Notes for Worker 3

- **The two entries to re-run are 12 and 15**; expect **5** and **2** rows, and expect entry 15's
  two rows to be a subset of entry 12's. The other thirteen are the pass-3 records unchanged, and
  set-equality was established programmatically (a symmetric difference over the node-id lists
  parsed out of `proofs-pass3.md` and `proofs-pass4.md`), not by eye.
- **The unit row's second assertion is not what discriminates entry 15's mutant**, and it would be
  wrong to read it as such. Under that mutation the construction succeeds, so
  `_package_view_instance` answers a `_NotAPackageView` and the row fails on its *first* assertion.
  The factory-call assertion is a contract statement - it forbids an implementation that calls and
  then rejects, which no manifest mutation produces - and it is in the row because that
  implementation is the plausible refactor of this guard.
- **Entry 12's label changed and its measurement did not.** If you compare labels rather than
  anchors between pass 3 and pass 4, the path
  `::_package_view_instance #"if not isinstance(view_class, type)"` now names entry **15**, whose
  mutation is about exactly that line, and entry 12 names the whole recognition. Anchors, mutations
  and scopes for 1-14 are character-identical to `proofs-pass3.json` because the manifest was
  derived from it programmatically.
- **The record was taken twice and only the second is in the artifact**, because one test docstring
  was reworded between them; the disclosure and the captured-exit-0 `--only 12 --only 15` re-run
  are under `### Failability proofs`. If you distrust the detached run, that partial record and a
  fresh `--check-anchors-only` (exit 0) are both on disk.
- **`pre-commit` is not installed in this environment.** Its four hooks were run individually,
  including a byte-stability check of the generated kanban constants, which is the hook whose
  failure mode is a rolled-back commit rather than a lint message.
- `scripts/review_inspect.py` was **not** run this pass. The delta is one test fixture, one URL
  pattern, one parametrization and one test row - no production file changed, so every overview
  you regenerated in pass 3 is still current for the bytes on disk. Recorded as an explicit skip
  with its reason per `BUILD.md` `### When to run the helper during build`; the review-time
  obligation is yours and no production `.py` was touched for it to fire on.

### Notes for Worker 1 (spec reconciliation)

Everything the three prior build reports and three reviews recorded stands. These are additions,
and nothing here is fixed in this pass.

1. **Decision 18's recognition sentence now has both clauses pinned.** Worker 3's pass-3 extension
   of the pass-3 build report's proposed sentence is the right contract and is now measured on both
   halves: *the boundary middleware runs a package view's boundary only for a callback whose
   bookkeeping it can build that view's instance from, and it never calls anything that is not a
   class to try.* The first clause is pinned by entry 12 (5 rows) and the three earlier
   parametrizations; the **second** - the clause R2 was asked to state whether or not a row landed
   - is pinned by entry 15 (2 rows) and
   `::test_a_marked_callback_the_middleware_cannot_build_is_declined_not_crashed[/marked-callable-view-class/]`
   plus `::test_a_callable_view_class_that_is_not_a_class_is_never_called`. R2 can now write it as
   contract rather than as intention.
2. **The forged-buildable shape and the docstring claim remain one open maintainer decision**, and
   this pass changed nothing about either - see `### The review's Low, left untouched, and why`.
   The four sites Worker 3 enumerated are all still as they were, which is what keeps both
   resolutions available at the same cost.
3. **A correction to the pass-3 build report lands in this report's `### Failability proofs`**, not
   in place. If final verification quotes pass 3's `### Implementation notes` on the two
   `isinstance` clauses being "behaviourally now subsumed for every input any row supplies … so
   they are a clause of one recognition rather than a boundary of their own", the measured position
   is: subsumed for every input the suite then supplied, not for every input, and they are a
   boundary of their own now measured as entry 15 at 2 rows.
4. **Nothing in this pass bears on R2's or R3's other items.** No `examples/**` path, no doc, no
   spec sentence and no generated file was touched; M-A's re-pin re-measurement, the rationale's
   Decision 18 rejected-alternative bullet, and R3's live-tier opportunity are all exactly where
   pass 2 and pass 3 left them.

---

## Review (Worker 3, pass 4)

Re-review of Worker 2's pass-4 delta against the single **Medium** `## Review (Worker 3, pass 3)`
left open. Read end to end first, walking the **W3** column of `BUILD.md`
`## Required reading per worker` myself rather than accepting the dispatch's list of it: `AGENTS.md`,
`START.md`, `docs/builder/BUILD.md`, `docs/builder/ARTIFACT.md`, `docs/builder/worker-3.md`,
`docs/README.md`, `examples/fakeshop/test_query/README.md`,
`docs/spec-046-transport_security-0_0_15.md`, its `-rationale.md` (marked `yes` for this role and
`never` for Worker 2), `docs/builder/build-046-transport_security-0_0_15.md`
(`# Closeout cycle (card 046)` in full, including `## Maintainer decision M-A`,
`## Write-set correction W-1` and `## Worker-0 dispatch decision D-1`), this artifact's four plans /
four build reports / three prior reviews, and `docs/builder/worker-memory/worker-3.md`. The column
marks `yes` for exactly those, `—` for `GOAL.md`, `docs/GLOSSARY.md`, `CHANGELOG.md` and
`docs/TREE.md`; the dispatch omitted none of the `yes` rows. Workers 0, 1 and 2's memory files were
not read.

### Independent re-run: the mutations, declared before they were made

Recorded here **before** any edit, per `worker-3.md` `## Scope` and `BUILD.md`
`### Who performs it`. Every mutation is transient, one boundary at a time, reverted inside this
pass, each revert proved by byte comparison against a pre-mutation copy taken to a scratch path
**outside** the repository. No `git checkout` / `restore` / `stash` / `worktree` anywhere in this
pass; the tree is legitimately dirty with the round's own work.

Scratch root: `<session scratchpad>/w3p4` (outside the repo).

1. **The whole fifteen-entry pass-4 manifest**, re-run mechanically through
   `scripts/prove_failability.py` from Worker 2's own
   `docs/builder/temp-tests/r1/proofs-pass4.json`, at the scopes recorded there
   (`tests/test_views.py` for 1-8 and 12-15, `tests/test_routers.py` for 9-11), into my own scratch
   root and my own `--output docs/builder/temp-tests/r1/w3p4-rerun.md`. Worker 2's
   `proofs-pass4.json` / `.md` are **not** overwritten. The whole manifest rather than the two moved
   entries, because the pass's central claim is that the other thirteen did not move, and set-
   equality asserted by a builder over its own two records is exactly the claim this pass exists to
   re-derive.
2. **No hand mutation beyond the manifest.** Nothing this pass needs is unreachable through the
   runner; where a reading needed the unguarded body (none did this pass) it would be taken against
   a copy outside the repository rather than by mutating a production file.

Reverts are proved below under `### Revert proof`.

### The production delta is empty — verified by my own hashes, not accepted on the claim

The build report's central claim is that this pass wrote no production line. Taken independently,
`shasum -a 256` over every production file this round touches, before any mutation of mine:

| File | `shasum -a 256` (first 16) | Pass-3 review's own recorded prefix |
| --- | --- | --- |
| `django_strawberry_framework/views.py` | `e8aeb156550fc45a` | `e8aeb156550fc45a` |
| `django_strawberry_framework/middleware/request_body.py` | `6ef3ad5e35ebc9e7` | `6ef3ad5e35ebc9e7` |
| `django_strawberry_framework/_boundary_ordering.py` | `b2c25d9a66a6090c` | `b2c25d9a66a6090c` |
| `django_strawberry_framework/_request_body.py` | `2c1fd48618d4b01c` | `2c1fd48618d4b01c` |
| `django_strawberry_framework/consumers.py` | `1bdf298c473fd1a0` | `1bdf298c473fd1a0` |

The comparison is worth exactly as much as the right-hand column's provenance, so: those five values
were measured by **this reviewer role in pass 3**, not copied from a build report, which is what makes
this check able to catch an edit smuggled in under an "empty delta" claim. All five match. `git diff
HEAD --stat` additionally shows the round's production line counts unchanged from pass 3
(`_boundary_ordering.py` +111, `_request_body.py` 16, `middleware/request_body.py` 161,
`views.py` 69), and `consumers.py` is byte-identical to `HEAD` — `git show
HEAD:django_strawberry_framework/consumers.py` into the session scratchpad, then `cmp`, exit **0**.

**And the tree under review is the tree the proof run measured.** The pass-4 record notes it was
taken twice because a test docstring was reworded between runs, and that the second (recorded)
invocation was launched detached so its exit status was never captured. That leaves two questions a
recorded SHA would have closed and does not: the report records no hash for
`tests/test_views.py`, the one file it actually changed. Both are closed by measurement instead:

- my own full fifteen-entry re-run against the bytes now on disk reproduces **every** node-id set and
  both unmutated baselines (`197 passed` / `145 passed`) exactly, and it exited **0** with the status
  captured — which supersedes the detached run rather than trusting it;
- the reworded docstring is on disk in its final form: `::test_a_callable_view_class_that_is_not_a_class_is_never_called`
  names its sibling row by name, and `grep -n 'the row above' tests/test_views.py` matches only
  `::test_the_same_two_mounts_parse_nothing_without_the_middleware_either`, a pre-existing row this
  pass did not touch;
- `tests/test_views.py` hashes to `b1cfe55d50a6aa63` both before and after my whole mutation run.

Recommendation for future passes, not a finding: when a pass changes a file the manifest never
mutates, one line of `shasum` for that file costs nothing and removes the only gap this check had to
close by re-measurement.

### Failability proof audit, and the independent re-run

**Audited: all fifteen records.** Every entry carries the boundary by symbol-qualified path, the
exact mutation, the scope as run, the pre-mutation state of that same scope, the listed node ids, a
separate collection/setup-error count, and a restore proved by `filecmp.cmp(shallow=False)` plus
SHA-256. **Collection/setup errors: 0 on all fifteen**, parsed out of the emitted record rather than
read from prose. **No entry measured zero rows** — the lowest is 2 — so the record's
`why 0: not applicable` is correct as written, and neither the weakly-pinned nor the
harness-impossible reading is invoked. Every mutant run exited 1 and every unmutated run exited 0, so
no count is a count of a run that collected nothing.

**Re-run: all fifteen, at the scopes Worker 2 recorded** (`tests/test_views.py` for 1-8 and 12-15,
`tests/test_routers.py` for 9-11), through `scripts/prove_failability.py` on Worker 2's own
`proofs-pass4.json`, into my own scratch root outside the repo and my own
`--output docs/builder/temp-tests/r1/w3p4-rerun.md`. `--check-anchors-only` **first and separately:
exit 0**, all fifteen anchors matched exactly once **before any copy was taken**, which is also what
says no prior pass left a live mutation. Full run: **exit 0**. The mandatory floor is entries 2, 4, 6,
9, 10, 11 and 15 at 3 rows or fewer, and every entry sits on a security decision, so the floor is
effectively the whole manifest — and the whole manifest was re-run. **Nothing was accepted on Worker
2's record alone**, so there is no second column of boundaries to name.

Node-id sets compared as **sets**, parsed programmatically out of the three emitted records
(`proofs-pass3.md`, `proofs-pass4.md`, my `w3p4-rerun.md`), never as counts:

| # | W2 pass 4 | This pass | set-equal | errors | vs W2 pass 3 |
| --- | --- | --- | --- | --- | --- |
| 1 | 7 | 7 | yes | 0 | set-equal |
| 2 | 2 | 2 | yes | 0 | set-equal |
| 3 | 4 | 4 | yes | 0 | set-equal |
| 4 | 3 | 3 | yes | 0 | set-equal |
| 5 | 13 | 13 | yes | 0 | set-equal |
| 6 | 3 | 3 | yes | 0 | set-equal |
| 7 | 14 | 14 | yes | 0 | set-equal |
| 8 | 6 | 6 | yes | 0 | set-equal |
| 9 / 10 / 11 | 2 / 2 / 2 | 2 / 2 / 2 | yes | 0 | set-equal |
| 12 | 5 | 5 | yes | 0 | **+2, none lost** |
| 13 | 7 | 7 | yes | 0 | set-equal |
| 14 | 5 | 5 | yes | 0 | set-equal |
| 15 | 2 | 2 | yes | 0 | — new — |

**Fifteen of fifteen set-equal to Worker 2's record; thirteen of them set-equal to pass 3's.** The two
movement claims are exactly as recorded and I re-derived both by set difference rather than by
reading them: entry 12 gained precisely
`::test_a_marked_callback_the_middleware_cannot_build_is_declined_not_crashed[/marked-callable-view-class/]`
and `::test_a_callable_view_class_that_is_not_a_class_is_never_called` and lost nothing; entry 15's
two rows are exactly those two, and entry 15's set is a proper subset of entry 12's, as
`### Notes for Worker 3` predicts.

**The manifest itself was audited, not assumed.** A JSON comparison of `proofs-pass4.json` against
`proofs-pass3.json`, key by key: entries 1-11, 13 and 14 are **character-identical**; entry 12
differs in `label` **only** (anchor, replacement, `delete` flag and scope untouched, so the re-label
provably changed no measurement, which the set-equality then confirms); entry 15's `anchor`,
`target`, `scope` and `delete` are character-identical to pass 3's auxiliary manifest — i.e. pass 2's
narrow anchor, restored, with only its prose `mutation` description updated. That is precisely what
the pass-3 Medium's recommendation (2) asked for.

**Also re-run: Worker 2's own partial record.** `proofs-pass4-only12-15.md` (its captured-exit-0
`--only` re-run) parses to sets identical to mine for both entries, so the disclosure about the
detached run costs the record nothing.

### Entry 15 and entry 12 pin two different answers, and the re-label is now honest

The pass-3 Medium had three parts. All three landed, and each is verified at the level it was asked
for:

1. **Two permanent rows supplying the distinguishing input** — a callable non-class `view_class`.
   Both are in `tests/test_views.py`, both fail under entry 15's mutation, and neither existed in
   pass 3.
2. **The narrow anchor restored as its own entry** — entry 15, at **2 rows**, which clears
   `BUILD.md` `### Acceptance rule: weakly pinned is revision-needed`'s 0-or-1 band. My pass-3 text
   named two rows as the minimum for exactly that reason and two is what landed.
3. **Entry 12 re-labelled.** Its recorded path is now
   `::_package_view_instance (the whole recognition after the two getattrs: both bookkeeping-shape
   tests and the construction attempt)`, and the narrow
   `#"if not isinstance(view_class, type)"` path now names entry **15**, whose six-word mutation is
   about exactly that line. So the false reading the finding was about — grep the narrow path, read
   3 rows, conclude the `isinstance` clause is pinned — is gone: that path now resolves to the entry
   whose mutation removes it. The parenthesized-scope label shape is the one entries 5 and 13
   already use, and `prove_failability.py` enforces that a label's leading path is its target, which
   the run's exit 0 confirms.

**Neither entry is redundant, and that is a measurement rather than an argument.** Entry 12's mutation
removes the shape tests *and* the construction, so both answers vanish at once and the record cannot
distinguish "refused before the call" from "the construction declined it". Entry 15 removes only the
first. Entry 15's set being a strict subset of entry 12's is the shape that proves the two are nested
rather than duplicated: entry 12 is the union of both answers' rows, entry 15 is the narrow answer's.

One scope note for the next reader, since it is the only thing about entry 15 that could mislead:
its anchor is the whole two-line `if not isinstance(view_class, type) or not isinstance(initkwargs,
dict): return None` statement, so its 2 rows are attributed to the **pair** of clauses. The
`initkwargs` half remains deliberately unpinned, for the reason under `### The two declines` below.

### The unit row's second assertion pins a contract no mutation in the manifest reaches

The build report volunteers that
`::test_a_callable_view_class_that_is_not_a_class_is_never_called`'s second assertion — the factory
recorded no call — is **not** what fails under entry 15's mutant, and it is right: under that
mutation the construction succeeds, so the row fails on its *first* assertion. The question that
disclosure raises is whether the assertion therefore pins nothing. **Measured, not reasoned**, in
`docs/builder/temp-tests/r1/test_w3p4_call_then_reject.py`, which writes the alternative recognition
locally so no production file is mutated for the reading:

| Recognition | answer | factory calls recorded |
| --- | --- | --- |
| shipped `_package_view_instance` | `None` | **0** |
| construct-first, validate-the-answer-afterwards | `None` | **1** |

**Same answer, same wire `200`, foreign code run.** So the second assertion is the only thing in the
suite that separates the shipped contract — *nothing but a class is ever called* — from the plausible
refactor of this guard, and no manifest mutation produces that refactor. The row pins the clause's
**contract**, not only today's consequence, which is the strengthening the build report claims for
it. Both readings reproduce at the floor (Python 3.10.19 / Django 5.2), so neither is an artifact of
the newer interpreter.

The fourth parametrization is the other half and is the weaker of the two on its own — its
assertions are the parent test's unchanged `200` plus `startswith("marked, ")`, which is a
*consequence* statement. Kept as-is is the right call: it is the wire answer, an `AttributeError` out
of `process_view` is exactly what breaks it, and folding the fourth shape into a separate test would
have split one recognition's contract across two names. Between them the clause is bounded at the
recognizer and at the wire, which is what the pass-3 Medium asked for.

### The two declines, judged on their merits

**Decline 1 — no row for `isinstance(initkwargs, dict)`. Accepted, and now measured rather than
argued.** The stated reason is that removing the clause widens recognition rather than failing open.
`test_w3p4_call_then_reject.py`'s third row measures it on the distinguishing input, a non-`dict`
mapping (`types.MappingProxyType({"schema": SCHEMA})` behind a real `view_class`):

- shipped code: `_package_view_instance(...) is None` — declined;
- the same body with only the `dict` test removed: a real `_RequestBodyBoundaryMixin` instance —
  i.e. the boundary **runs**.

So the clause's removal moves enforcement from "the view-local arrangement" to "the chain runs the
boundary too", which is more enforcement, not less; and for a non-mapping the `**` raises `TypeError`
into the same decline either way, so there is no third direction. A row there would pin a preference.
The decline is correct, and it is also the review's own instruction being followed rather than
re-litigated. Reproduces at the floor.

**Decline 2 — no docstring sentence for the same clause. Accepted, but on the first of its two
stated grounds only.** The stronger ground is the one the report gives second: the docstring already
states the behaviour — `middleware/request_body.py::_package_view_instance` #"The two ``isinstance``
tests stay ahead of the construction" reads *"so it is only ever a class that gets called, and there
is deliberately no ``or {}`` default: an absent attribute means 'not ours', never 'ours, with nothing
configured'"*. Nothing is owed on top of that, and my pass-3 parenthetical said "if anything"
precisely because nothing was owed. The other ground — that any sentence added to that file would sit
inside the maintainer's open contract call — is **over-broad**: the contract call is about whether the
package owes a controlled response to a forged marker, and a factual sentence about which
`view_initkwargs` shapes are accepted would not touch it. The decline stands on the first ground
alone; recorded so a future reader does not inherit the wider version of the argument as precedent.

### The correction to the pass-3 build report: accepted, and its attribution corrected

The pass-4 report corrects a sentence in `## Build report (Worker 2, pass 3)`
`### Implementation notes`: that the two `isinstance` clauses are *"behaviourally now subsumed for
every input any row supplies … so they are a clause of one recognition rather than a boundary of
their own, which is how the manifest measures them."* **I accept the correction, plainly and
without reservation.** *For every input any row supplied* is not *for every input*; the clauses are a
boundary of their own; entry 15 now measures them at 2 rows; and the same sentence's other half —
that the clauses are what stops a non-class `view_class` being *called* — is exactly right and is why
both entries exist. The correction is filed in the right place (prose in the correcting pass's own
section, per `ARTIFACT.md`) and is the second time in this round a build report has handed the
reviewer the measurement that embarrasses its own earlier prose.

**One attribution correction, for the audit trail.** That sentence is Worker 2's, in the pass-3
**build report**; it is not a sentence of `## Review (Worker 3, pass 3)`. My pass-3 review's own
false sentence was a different one — the pass-2 claim that entry 12's old anchor and its two rows
"survive either way", which measured 0 rows — and I corrected that in pass 3 myself. Both corrections
now stand in the artifact; neither is outstanding.

### High:

None.

### Medium:

None. The single Medium `## Review (Worker 3, pass 3)` raised is closed: two permanent rows supplying
the distinguishing input, the narrow anchor restored at 2 rows and re-run set-equal by me, and the
mislabelled entry re-labelled onto the recognition its mutation is actually about.

### Low:

#### The docstring rewritten this pass claims the four routes are **the** four ways, and a fifth way exists and is not refused

`tests/test_views.py::test_a_marked_callback_the_middleware_cannot_build_is_declined_not_crashed`
#"The four routes are the four ways a callback". The rewritten docstring states the four
parametrizations are *the four ways a callback can carry the marker without a package view behind
it*. There is a fifth: a forged marker over a `view_class` that **is** a class and **is** buildable
but is not a package view. Re-measured on this tree rather than inherited from pass 3
(`docs/builder/temp-tests/r1/test_w3p3_decline_arm.py`, re-run unmodified):

```
forged-buildable recognizer answer: {} type=dict
forged-buildable raised: AttributeError("'dict' object has no attribute '_enforce_request_boundary'")
```

so the fifth way is not declined at all — it reaches `view._enforce_request_boundary(request)` on a
foreign object. The docstring's exhaustiveness claim is therefore false, and it is newly written text
rather than inherited.

**Recorded and escalated; no change is requested and this does not hold the pass.** It is the same
open maintainer contract call as the pass-3 Low — whether the package owes a controlled response to a
callback forging its private marker — and it resolves the same two ways: if the package owes one, a
fifth route joins the parametrization and the sentence becomes true by becoming five; if a forged
marker is not a supported seam, the sentence wants narrowing alongside the other four sites. Writing
either now would pre-empt the decision, exactly as Worker 2's own reasoning for leaving
`middleware/request_body.py` alone says. What this pass changes is the **inventory** the decision
needs: the sites carrying the over-claim are now **five**, not four, and the newest of them is in a
file this cohort owns rather than in the file under the contract call. Carried into
`### Notes for Worker 1` for that reason.

#### Two sentences in the pass-4 report are looser than the measurements behind them

Both are corrected here rather than requested as changes, because `ARTIFACT.md` forbids editing a
prior section and neither costs a reader anything once this section stands beside it. No builder
action is warranted for either, and I am recording that as the disposition rather than leaving them
unresolved.

- `### Tests added or updated` reads *"thirteen of pass 3's fourteen entries re-ran set-equal across
  47 distinct node ids"*. Re-derived from my own run: those thirteen entries span **42** distinct
  node ids; **47** is the union across all fifteen. The set-equality claim itself is exactly right —
  I re-derived all thirteen — so the number is incidental breadth, not a load-bearing count. Flagged
  because `BUILD.md` `## Claims are proven mechanically` is specifically about numbers that read as
  measured.
- `### The review's Low, left untouched, and why` reads *"all four sites still read as they did"*.
  Three do. The fourth —
  `::test_a_marked_callback_the_middleware_cannot_build_is_declined_not_crashed`'s docstring — was
  **rewritten by this pass**, as the same report's `### Files touched` discloses two sections
  earlier. The load-bearing clause ("a hook whose every other outcome is a controlled response") does
  survive verbatim, so the substance of the sentence holds and both resolutions of the contract call
  remain equally cheap; the letter of it does not, and an auditor walking the four sites should know
  one of them moved.

### DRY findings

**(a) The delta introduces no duplication a reader would want consolidated, measured rather than
eyeballed.** `scripts/review_inspect.py` on `tests/test_views.py` with `--output-dir docs/shadow`:
32 repeated string literals, and every one of them is pre-existing test data (`view_class` 24x,
`/graphql/` 17x, `application/json` 16x, `iso-8859-1` 10x, …). None was introduced by this pass —
the new fixture's only literal, `"marked, callable view_class"`, occurs once. Four control-flow
hotspots, all pre-existing rows (lines 135, 953, 1267, 1486); none is new code.

**(b) The four `_marked_callback_*` fixtures are near-copies by construction, and should stay that
way.** Each is three lines plus a docstring, and the docstrings are where the contract lives: what
makes *this* shape the one no other route can supply. A `_make_marked_callback(body, view_class,
view_initkwargs)` factory would compress twelve lines into four and delete the four explanations,
and the URLconf would stop naming which shape each route is. The attribute assignments are already
grouped into one block, which is the consolidation worth having. **Not a finding**; recorded because
a reviewer looking only at shape would call this duplication.

**(c) No existence challenge.** `_package_view_instance` acquired its first out-of-module reader this
pass (the unit row), which strengthens rather than weakens the case for it existing: it is the answer
the hook branches on, the anchor two manifest entries need, and now a directly-asserted contract.
`_VIEW_CLASS_FACTORY_CALLS` is a three-line module-level list with two readers in one row; nothing to
abstract.

**(d) One duplication in the delta is deliberate and correct**, and it is mine rather than Worker
2's: `test_w3p4_call_then_reject.py` hand-copies two variant recognition bodies. Both are gitignored
temp probes and the copies are what make each reading one experiment with two arms.

### Fail-open shape hunting: the pass-4 delta

`BUILD.md` `### Fail-open shapes`, read over what this pass added or changed. **The production
surface is byte-identical** (five SHAs above), so pass 2's and pass 3's readings stand unre-litigated
and there is no new production expression to hunt. What is new is test code, and it carries decisions
of its own:

1. **`len(_VIEW_CLASS_FACTORY_CALLS) == calls_before`, not `not _VIEW_CLASS_FACTORY_CALLS`.** This is
   the delta shape rather than an emptiness test, so module-level state left by an earlier row cannot
   make the assertion pass. It is also the *non*-fail-open choice of the two: an emptiness test on a
   list some other row had appended to would fail spuriously, and one on a list something had cleared
   would pass vacuously. Verified by execution rather than by reading: the row passes alone
   (`1 passed`), passes with the wire row ahead of it, passes with the wire row **behind** it
   (`5 passed`, reversed order), and passes under `-n 4` with the whole file (`197 passed`), so it is
   order-independent and xdist-safe.
2. **No clamp, no `or` fallback, no `getattr` default standing in for meaningful absence, no
   truthiness test on a possibly-absent value, and no bare/over-broad `except`** anywhere in the
   delta — read line by line over the fixture, the URL pattern, the parametrization and the row.
3. **`_view_class_factory` records before it returns**, which is the shape that lets the row observe
   the property rather than infer it. A factory that only returned would have made the second
   assertion unwritable, which is the fixture-shaped version of the same fail-open risk this section
   is about.

### Non-weakening checks

- **The delta is additive, and the arithmetic closes.** `tests/test_views.py` collects **197** against
  the **195** my own pass-3 review measured; the parametrized test now collects **4** ids where pass 3
  recorded 3, and `::test_a_callable_view_class_that_is_not_a_class_is_never_called` is new. 195 + 2 =
  197 with two new ids means **nothing was removed** — a deletion would have shown up as a lower
  total.
- **Thirteen entries re-ran set-equal across 42 distinct node ids** in my own run, which is the
  mechanical evidence that no existing row was renamed, re-scoped or weakened: a rename would have
  moved at least one set.
- **No assertion was weakened.** The fourth parametrization reuses the parent test's existing
  `200` / `startswith("marked, ")` pair unchanged, and entry 12's three pre-existing rows still fail
  under its mutation (set-equal, plus the two new ones), so their discriminating power is intact.
- **The guard was not touched at all**, so nothing was widened or narrowed: every input pass 3
  declined is declined by the identical bytes.
- **Nothing was weakened to buy back a hot-path number**, and nothing could have been: the measured
  path is the same bytes.
- **The other three findings' sites are untouched** — entries 1, 2, 7, 8, 9, 10 and 11 set-equal, and
  `consumers.py` byte-identical to `HEAD`.

### Dispatched findings checklist walk

- **Box 2** stays `- [x]` from pass 2 and the tick is still warranted: its contract (an over-limit
  multipart refused before parsing while an under-limit request reaches and obeys the project's own
  `CsrfViewMiddleware` subclass) is untouched by this diff — entries 3, 4, 5 and 13 are set-equal to
  pass 3's in my own re-run.
- **Boxes 1, 3, 4** stay `- [ ]` under the plan-level deferral recorded twice (pass-1 plan checklist
  preamble, pass-2 plan `### Routing confirmations`): their contracts landed in `2701f41a` /
  `ba66ab49`, so Worker 1 ticks them at final verification where a tick means landed **and** audited.
  A recorded deferral, not a silent one — no Medium finding. Entries 1, 2, 7, 8, 9, 10 and 11, all
  set-equal, are the evidence this pass touched none of their sites.
- **No box was ticked, unticked or edited by pass 4**, confirmed by reading the checklist itself
  rather than the report's account of it. **I ticked nothing** — the walk is an audit, per this pass's
  contract.

### Public-surface check

`git diff HEAD -- django_strawberry_framework/__init__.py` is **empty**: `__all__` and the re-export
list are unchanged. `middleware/request_body.py`'s `__all__` is still the single-name tuple
`("GraphQLRequestBodyBoundaryMiddleware",)`, so the documented `MIDDLEWARE` string is unchanged;
`_boundary_ordering.py` remains private (no `__all__`, every name underscore-prefixed, no
`__init__.py` export in the package root or in `middleware/`). No new public export, as the round's
Definition of Done requires.

**One surface fact worth recording rather than flagging:** `_package_view_instance` now has its first
importer outside its own module (`tests/test_views.py:91`). It stays private and no consumer path
reaches it, but a future rename must now sweep `tests/` as well as the module — which is exactly what
`AGENTS.md` #27's grep-sweep rule covers, and the sweep below confirms there is exactly one such
reader.

### Static inspection helper

Run this pass, with `--output-dir docs/shadow` as every build-cycle invocation must:

```shell
uv run python scripts/review_inspect.py tests/test_views.py --output-dir docs/shadow
```

**No skips.** Worker 2's recorded skip is legitimate on its own terms — no production `.py` changed,
so every overview regenerated in pass 3 still describes the bytes on disk, and
`BUILD.md` `### When to run the helper during build` puts the review-time obligation on Worker 3
anyway. I ran it on `tests/test_views.py` rather than reason about whether the delta clears the
50-line threshold for a file outside the package: the fixture, the class, the log list, the URL
pattern, the parametrization, the rewritten docstring and the new row sit around that threshold, and
measuring is cheaper than arguing. Findings are under `### DRY findings` (a). Original-source line
numbers are cited throughout this review; no shadow-file line number appears anywhere in it.

### Hot-path budget

**The number exists, before and after, from one experiment with two arms — which is the whole of my
obligation.** Whether the cost is acceptable is the maintainer's call and I do not judge it.

The declaration is inherited (the plan makes a fixing pass inherit R1's, and pass 2 declared this
path hot), and the report's answer is the right one: the production bytes are unchanged, so before
and after are the same bytes and the standing number is pass 3's. That is stronger than "not
applicable" and I verified its premise independently with the five SHAs above rather than accepting
it.

Reproduced anyway, since "reproducible as recorded" is the part I owe — pass 2's snippet unmodified
(`docs/builder/temp-tests/r1/test_w2p3_hotpath_recognizer.py`, 200,000 iterations, both arms in one
process):

| Environment | without the guard | with the guard | delta per call |
| --- | --- | --- | --- |
| shared `.venv`, my run | 0.5369 us | 0.5308 us | **-0.0061 us** |
| floor (Python 3.10.19), my run | 0.5801 us | 0.5776 us | **-0.0025 us** |

Both deltas land inside pass 3's recorded band (-0.0206 to +0.0295 us), sign included. My absolute
per-call readings (0.53 / 0.58 us) sit back inside pass 3's 0.50-0.53 us band rather than at the
1.2-1.3 us the pass-4 report measured, which independently supports that report's reading of its own
numbers: the absolute is the machine and the delta is the metric. Metric 1, the per-request median,
was not re-captured and is not owed — it cannot resolve a change of this size, and there is no change
to resolve.

### Floor verification

**The plan's declaration is R1's one floor run, and I re-ran the full declared scope myself.** Floor
facts taken from `BUILD.md` `## Floor verification`, its single canonical statement, never from
memory or from a number restated in a document: the supported floor is **Django 5.2.0 on Python 3.10
with strawberry-graphql 0.316.0**.

- `/tmp/dsf-floor` existed from the prior passes and was **reused only after reading its versions**.
  `/tmp/dsf-floor/bin/python -V` -> **Python 3.10.19**;
  `uv pip list --python /tmp/dsf-floor/bin/python` reads **django 5.2**, **strawberry-graphql
  0.316.0**, asgiref 3.12.1, channels 4.3.2, daphne 4.2.3, pytest 9.1.1, pytest-django 4.12.0,
  pytest-asyncio 1.4.0, django-filter 26.1, and `django-strawberry-framework 0.0.14` editable at this
  checkout — so the venv is the floor and it carries this pass's change.
- `/tmp/dsf-floor/bin/python -m pytest tests/test_views.py tests/test_routers.py --no-cov` —
  **342 passed** (197 + 145), the plan's **full** declared scope, my own run. Pass 3's review had to
  re-establish the `test_routers.py` half because the pass-3 build report ran only `test_views.py`;
  the pass-4 report ran both and so did I.
- The pass's own five subject rows named individually rather than hidden in the aggregate:
  `::test_a_marked_callback_the_middleware_cannot_build_is_declined_not_crashed` (all four routes)
  plus `::test_a_callable_view_class_that_is_not_a_class_is_never_called` — **5 passed** at the floor
  and **5 passed** in `.venv`. So the class test refuses a callable non-class `view_class` at 3.10
  exactly as at 3.14, and the factory-call assertion holds on both interpreters.
- My three review probes at the floor: `test_w3p4_call_then_reject.py` **3 passed** with identical
  readings to `.venv` (including the widened-recognition direction test), so neither the second
  assertion's value nor the `initkwargs` decline is an artifact of the newer interpreter.
- **The shared `.venv` is unmutated**, read rather than asserted: `uv pip list` reports **django
  6.0.5**, asgiref 3.11.1, strawberry-graphql 0.316.0, and `.venv/bin/python -V` is **Python
  3.14.2** — still far above the floor, so no floor install leaked into it. Every floor command was
  invoked as `/tmp/dsf-floor/bin/python -m pytest`, and I ran no `uv pip install` at all in this pass.

### Test-staleness sweep

Run independently, never against the artifact's file list (`worker-3.md`: the tree it missed is by
definition the one that cannot appear in the diff).

- **Neither `BUILD.md` shape applies**: no example-model field set changed and no wire shape was
  converted — and this time that is provable rather than argued, since no production byte moved.
- **The one staleness this delta can create is a stranded reader of a private helper**, because the
  delta *adds* one. `grep -rn '_package_view_instance' --include='*.py' .` over the whole repository:
  the definition, one call site and two docstring references in `middleware/request_body.py`; the
  import at `tests/test_views.py:91` and its single use in the new row; and gitignored probes. No
  per-app tree and no `examples/fakeshop/test_query/` file imports it.
- **The new fixture names are local to one file**: `grep -rln '_view_class_factory\|_NotAPackageView\|_VIEW_CLASS_FACTORY_CALLS\|marked-callable-view-class'`
  matches `tests/test_views.py` only.
- **The marker / stamp / exemption readers across all three trees** are unchanged from pass 3:
  `_BOUNDARY_MARKER` / `_BOUNDARY_ENFORCED` / `_CSRF_ORDERING_EXEMPTION` /
  `graphql_request_body_boundary` match `_boundary_ordering.py`, `middleware/request_body.py`,
  `views.py`, `tests/test_views.py` and the one known false positive
  (`scripts/review_inspect.py`'s unrelated `_TOKEN_BOUNDARY_MARKERS`).
- **The sibling tier the delta could have stranded is green**, my own run:
  `uv run pytest tests/test_views.py tests/test_routers.py examples/fakeshop/test_query/test_transport_api.py --no-cov`
  — **411 passed** (197 + 145 + 69), against pass 3's 409. The live tier is in scope because it
  reaches `_package_view_instance` through its own probe wrapper.
- **Module-level mutable state is the delta's one new staleness risk and it is closed by execution**,
  not by reading: see `### Fail-open shape hunting` item 1 for the four orderings run, including
  `-n 4`.
- No `--cov*` flag was used in any run in this pass; every invocation carried `--no-cov`.

### CHANGELOG sanity (only when the slice touches `CHANGELOG.md`)

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Not applicable to the pass-4 delta; it modifies no docs, release metadata, KANBAN or archive surface.
Confirmed rather than assumed: `git diff HEAD -- examples/fakeshop/apps/kanban/constants.py` is still
exactly the single added line `"django_strawberry_framework/_boundary_ordering.py",` in
`TRACKED_FILE_PATHS`, i.e. byte-unchanged since pass 2 and exactly what `W-1` authorizes; and
`git diff --cached --name-status` is still exactly
`A django_strawberry_framework/_boundary_ordering.py` — the one authorized staged path, nothing added,
nothing removed.

### The `pre-commit` substitution, audited

`pre-commit` genuinely is unavailable here — `command -v pre-commit` finds nothing and `uv run
pre-commit` fails to spawn (`.pre-commit-config.yaml`'s own header documents `uvx pre-commit`, which
would fetch it). **The substitution is adequate**, and I checked its adequacy against the config file
rather than against the report's description of it: `.pre-commit-config.yaml` declares exactly four
local hooks — `kanban-tracked-path-constants`, `source-layout`, `ruff-format`, `ruff-check` — and all
four were covered. My own read-only re-runs:

- `uv run python scripts/check_trailing_commas.py --check tests/test_views.py` — **exit 0** (the
  `source-layout` hook's `--fix` entry point, run in check mode so it cannot write);
- `uv run ruff format --check tests/test_views.py django_strawberry_framework/middleware/request_body.py`
  — `2 files already formatted`; `uv run ruff check` on the same two — `All checks passed!`;
- `git diff --check` over the whole tree — clean.

**The one hook whose failure mode is a rolled-back commit was verified two independent ways, neither
of which writes the repo file.** `scripts/build_kanban_tracked_path_constants.py --check` — **exit
0** — and a regenerate to a scratch `--output` outside the tracked file, byte-compared: `cmp` exit
**0** against the on-disk `examples/fakeshop/apps/kanban/constants.py`, which additionally still
matches the copy I took before running anything (`6761fadb49c4f285` throughout). Worker 2's method
(copy out, regenerate in place, `cmp`) reaches the same answer; the `--check` / `--output` pair
reaches it without ever writing a baseline-dirty file, and is worth preferring next time. Either way
the conclusion holds: this pass adds no tracked path, the hook's `files:` pattern does match
`tests/`, and the commit-time regenerate is a no-op.

The hook set also confirms the substitution has no gap in kind: all four are `language: system`
local hooks that shell out to `uv run`, so running their entry points directly *is* running the hook
— there is no pre-commit-managed environment, revision pin, or extra hook that the direct
invocations skip.

### What looks solid

- **The Medium is closed the way the acceptance rule prescribes** — more and better-targeted rows,
  no weaker boundary, no recorded exception — and closed at both levels the finding named: the
  recognizer's own answer and the wire answer.
- **The unit row is better than the one my pass-3 recommendation described.** My probe was inert, so
  its row could only assert the answer; recording the calls costs three lines and turns the row into
  a statement of the clause's contract. I measured that this is not decoration: a construct-first
  recognition answers the identical `None` and only the call record separates it.
- **The pass volunteered the limit of its own strengthening.** `### Notes for Worker 3` says outright
  that the second assertion is not what discriminates entry 15's mutant. That is the disclosure that
  let me test whether the assertion pins anything at all, and it turned out to pin the one thing no
  mutation in the manifest reaches. A report that hands the reviewer the weakness of its own best
  idea is doing the job.
- **The manifest was derived programmatically, and it shows.** Thirteen entries character-identical,
  entry 12 differing in `label` alone, entry 15 restoring pass 2's anchor character-for-character —
  so "the re-label changed no measurement" is provable from the manifest before a single test runs,
  and the set-equality then confirms it.
- **The proof discipline is again exemplary at the mechanical level**: anchors checked first and
  separately, every restore proved by `filecmp` plus SHA-256, no `git` anywhere in the pass,
  `consumers.py` re-verified against `HEAD`, and all five production SHAs matching the values *I*
  recorded in pass 3.
- **The declines are recorded with reasons rather than taken silently**, including the one that
  declines part of the review's own recommendation. Both are right on the merits, and the one whose
  argument I trimmed still lands.
- **The floor run is the full declared scope**, which is the second consecutive pass to close the gap
  pass 3's review found in the pass-3 build report.

### Temp test verification

Files used this pass, all under `docs/builder/temp-tests/r1/` (gitignored):

- `test_w3p4_call_then_reject.py` — **new, mine.** Three rows: the shipped recognition's answer and
  call record; a construct-first-then-validate recognition answering the same `None` while calling
  the factory once; and the `initkwargs`-clause direction test on a `MappingProxyType`.
  **Disposition: kept as review evidence, no promotion owed.** Two of its three rows exercise variant
  bodies written locally rather than shipped code, so they are not promotable in principle — the
  shipped half of each reading is already pinned by the permanent rows this pass added.
- `w3p4-rerun.md` / `.log`, `anchors.log` — my re-run of Worker 2's manifest, written to my own
  paths. Worker 2's `proofs-pass4.json` / `.md` / `proofs-pass4-only12-15.md` are **untouched**, and
  so are pass 1's, pass 2's and pass 3's records.
- Worker 2's `test_w2p3_hotpath_recognizer.py`, and pass 3's `test_w3p3_decline_arm.py`,
  `test_w3p3_decline_moves_no_failure.py` and `test_w3p3_isinstance_witness.py`, were **re-run
  unmodified** in `.venv` and (the first two) at the floor. Not edited.
- **`test_w3p3_isinstance_witness.py`'s disposition is now settled**: it was the probe that caught the
  pass-3 gap, and `worker-3.md` `## Temp test rules` required its rows to become permanent. They did
  — `[/marked-callable-view-class/]` and
  `::test_a_callable_view_class_that_is_not_a_class_is_never_called` are the permanent form, with the
  call-record assertion added. The probe is no longer the only proof of a shipped guard, which is the
  condition that rule exists to enforce.

### Revert proof

One mutation run this pass, mechanized, every entry restored before the next, each restore proved by
byte comparison against a pre-mutation copy taken to a scratch path **outside** the repository:

- **Manifest re-run (15 entries)** — `filecmp.cmp(shallow=False) True` plus matching SHA-256 on all
  fifteen (4x `e8aeb156550fc45a`, 4x `6ef3ad5e35ebc9e7`, 3x `b2c25d9a66a6090c`, 3x
  `1bdf298c473fd1a0`, 1x `2c1fd48618d4b01c`); runner exit **0**.

Whole-tree confirmation afterwards: all five production files hash to their pre-review values
(`views.py e8aeb156550fc45a`, `middleware/request_body.py 6ef3ad5e35ebc9e7`,
`_boundary_ordering.py b2c25d9a66a6090c`, `_request_body.py 2c1fd48618d4b01c`,
`consumers.py 1bdf298c473fd1a0`) and `tests/test_views.py` to `b1cfe55d50a6aa63`, its pre-review
value; no `ACTIVE-MUTATION.json` and no `RESTORE-FAILED.json` anywhere under the scratch root or the
repository; `git status --short` is unchanged from task start (the eight tracked entries and this
artifact) and `git diff --cached --name-status` is still the one authorized staged path; and
`uv run ruff format --check`, `uv run ruff check`, `scripts/check_trailing_commas.py --check` and
`git diff --check` all pass. **No `git checkout` / `restore` / `stash` / `worktree` at any point in
this pass.**

### Notes for Worker 1 (spec reconciliation)

Everything the four build reports and three prior reviews recorded stands. These are additions, and
nothing here is fixed in this pass.

1. **Escalated, and now five sites rather than four: the forged-buildable shape, the docstring claim,
   and the exhaustiveness claim are one maintainer decision.** Worker 2's pass-3 note 1, my pass-3
   note 1 and Worker 2's pass-4 note 2 all state the contract call correctly: does the package owe a
   controlled response to a callback forging its private marker? What this pass adds to the
   inventory the decision has to sweep is a **fifth** site, newly written here —
   `tests/test_views.py::test_a_marked_callback_the_middleware_cannot_build_is_declined_not_crashed`
   #"The four routes are the four ways a callback", which asserts an exhaustiveness the code does not
   have (re-measured on this tree: a forged marker over `view_class = dict` reaches
   `_enforce_request_boundary` on a `dict` and raises `AttributeError`). Resolution paths are
   unchanged: **(i)** the package owes a controlled response -> one
   `getattr(instance, "_enforce_request_boundary", None)` probe plus at least two rows, the four
   `middleware/request_body.py` / `tests/test_views.py` claims become true unchanged, and the
   parametrization grows a fifth route so this sentence becomes true by becoming five; **(ii)** a
   forged marker is not a supported seam -> record that rejection reason and narrow all five.
   `spec-046` Decision 18 should say which contract it is. **The Low is not held against the pass and
   no code change was requested for it**, per the same reasoning Worker 2 recorded for leaving
   `middleware/request_body.py` alone.
2. **Decision 18's recognition sentence is now measured on both clauses**, so R2 can write it as
   contract: *the boundary middleware runs a package view's boundary only for a callback whose
   bookkeeping it can build that view's instance from, and it never calls anything that is not a
   class to try.* First clause: entry 12 at 5 rows. Second clause: entry 15 at 2 rows plus the two
   named rows, re-run set-equal by me. **One clause of the sentence R2 should NOT write as a
   boundary:** the `view_initkwargs` `dict` test is a narrowing preference, not a bound — measured
   here, removing it makes the middleware run the boundary for a non-`dict` mapping rather than fail
   open — so a spec sentence should not present the two `isinstance` clauses as symmetric guards.
3. **Two loose sentences in the pass-4 report are corrected in this section** (`### Low`, second
   finding): the "47 distinct node ids" attribution (the thirteen unchanged entries span 42; 47 is
   the union over fifteen) and "all four sites still read as they did" (the fourth site's docstring
   was rewritten this pass, with its load-bearing clause verbatim). If final verification quotes
   either sentence, those are the corrected readings. My own pass-2 sentence's correction (pass 3)
   and Worker 2's pass-3 `### Implementation notes` correction (pass 4) both stand as recorded, and
   the latter's sentence is Worker 2's rather than a reviewer's.
4. **A record-completeness suggestion for future passes, not a finding.** A pass whose only changed
   file is one the manifest never mutates has no SHA anywhere in its record for that file, so
   "the tree under review is the tree the proofs were taken on" has to be re-established by a full
   re-run instead of by one line of `shasum`. It cost nothing here because the re-run was mandatory
   anyway; it would cost something in a pass whose floor is narrower.
5. **Items 1-6 of my pass-2 notes, 1-5 of my pass-3 notes, and Worker 2's pass-4 notes 1-4 remain
   R2's and R3's**, unchanged. In particular the rationale's Decision 18 rejected-alternative bullet
   that describes the shipped design is still the most misleading shape in the companion file; M-A's
   re-pin re-measurement after the High fix is still R3's obligation; and M-A's live-tier opportunity
   for the High fix's central assertion is still R3's to take or decline.

### Review outcome

`review-accepted`.

The one Medium `## Review (Worker 3, pass 3)` left open is closed, and closed the way
`BUILD.md` `### Acceptance rule: weakly pinned is revision-needed` prescribes rather than by any
route that would make the zero leave the record. The narrow anchor is back as its own manifest entry
at **2 rows**, its two rows are permanent rows in `tests/test_views.py`, entry 12 is re-labelled onto
the recognition its mutation is actually about so the narrow symbol path now resolves to the entry
that removes it, and entry 15's set is a strict subset of entry 12's — which is the shape that proves
the two entries are nested rather than redundant. **I re-ran all fifteen entries myself**, at the
scopes Worker 2 recorded, anchors checked first and separately (exit 0, so no live mutation was
inherited): fifteen of fifteen set-equal to Worker 2's node-id sets, thirteen set-equal to pass 3's,
entry 12 gained exactly the two new rows and lost none, **0 collection/setup errors on all fifteen**,
every unmutated run green, every restore proved by `filecmp` plus SHA-256, and the runner exit 0.
Nothing was accepted on Worker 2's record alone.

**The production delta really is empty.** All five production SHAs match the values this reviewer role
measured in pass 3 — not values copied out of a build report — `consumers.py` is byte-identical to
`HEAD`, and the diff's production line counts are unmoved. So the hot-path answer ("before and after
are the same bytes") rests on a premise I verified rather than accepted, and the standing ~15 ns
number reproduces inside pass 3's band in `.venv` (-0.0061 us) and at the floor (-0.0025 us).

**The new coverage pins the contract, not only today's consequence**, which was the part of this pass
most worth distrusting. The build report volunteers that the unit row's factory-call assertion is not
what fails under entry 15's mutant; measured, a construct-first-then-validate recognition answers the
identical `None` and the identical wire `200` while calling the factory once, so that assertion is
the only thing in the suite separating *nothing but a class is ever called* from the plausible
refactor of this guard. Both declines are right: the `initkwargs` clause's removal **widens**
recognition (measured on a `MappingProxyType` — a real instance is built and the boundary runs), so
no row is owed there, and the docstring already states the clause's behaviour so no sentence is owed
either — though that decline stands on "already stated" and not on the wider claim that any sentence
in that file would pre-empt the maintainer's contract call. The floor run is the plan's **full**
declared scope at **342 passed**, the five subject rows pass at 3.10 and 3.14, `pre-commit`'s absence
is substituted hook-for-hook against the config file rather than against its description, and the
kanban constants hook is verified a no-op two ways without writing a baseline-dirty file.

**Two Lows, neither of which holds the pass, both with their disposition recorded here.** The
rewritten parametrization docstring now claims its four routes are *the* four ways a marked callback
can lack a package view, and a fifth way exists and is not refused — the same open maintainer
contract call as the pass-3 Low, so it is escalated with both resolution paths and no change
requested, and it moves the site inventory that decision must sweep from four to five. And two
sentences in the pass-4 report are looser than their measurements (42 distinct node ids across the
thirteen unchanged entries, not 47; one of the "four sites" did have its docstring rewritten, with
the load-bearing clause verbatim) — corrected in prose here, which is the only remedy `ARTIFACT.md`
allows and one that costs a future reader nothing.

`worker-3.md`'s acceptance gate is met: every High/Medium/Low is addressed or intentionally rejected
with a recorded reason, every recorded proof is audited and every one re-run, none weakly pinned, the
DRY read is measured rather than eyeballed, the public-surface and documentation checks are performed,
the hot-path number exists and reproduces, the floor run happened as declared, and the temp test that
caught the pass-3 gap is superseded by permanent rows rather than left as the only proof of a shipped
guard. The pass-3 Low remains with the maintainer, carried forward under `### Notes for Worker 1` so
the decision has somewhere to land.

---

## Final verification (Worker 1)

Final-verification pass for round R1. Read end to end first, walking the **W1** column of
`BUILD.md` `## Required reading per worker` myself rather than accepting the dispatch's list of
it: `AGENTS.md`, `START.md`, `docs/builder/BUILD.md`, `docs/builder/ARTIFACT.md`,
`docs/builder/worker-1.md`, `GOAL.md`, `docs/GLOSSARY.md`, `CHANGELOG.md`,
`docs/spec-046-transport_security-0_0_15.md`, its `-rationale.md` (this role owns both),
`docs/builder/build-046-transport_security-0_0_15.md` (`# Closeout cycle (card 046)` in full,
including `## Maintainer decision M-A`, `## Write-set correction W-1`,
`## Worker-0 dispatch decision D-1` and `## Open maintainer decision M-B`), this artifact's four
plans / four build reports / four reviews, and `docs/builder/worker-memory/worker-1.md`. The
column marks `yes` for exactly those plus the relevant source and tests read-only, and `—` for
`docs/TREE.md`, `docs/README.md` and `examples/fakeshop/test_query/README.md`; the dispatch
omitted no `yes` row. Workers 0, 2 and 3's memory files were not read.

Two navigational corrections for the next reader, since the dispatch named headings that do not
exist: the build plan's per-round declarations live under `## Round shapes and per-round
ownership` as four bullets, not under `## Per-round shapes and ownership` with `### Round R1` /
`### Round R2` / `### Round R3` sub-headings; and the open contract call is recorded as
`## Open maintainer decision M-B`, which is the section this pass treats as canonical for it.

### Baseline, write set, and the things that must not have moved — measured this pass

- `git status --short`: the eight tracked entries and this artifact, unchanged from what every
  pass records. `django_strawberry_framework/consumers.py` is **absent** from it, i.e. clean
  against `HEAD`, so `ba66ab49`'s half of the round carries no working-tree change at all.
- **`git diff --cached --name-status` is exactly `A django_strawberry_framework/_boundary_ordering.py`** —
  the one path `W-1` authorizes, nothing added, nothing removed. Re-measured at the start and at
  the end of this pass.
- Version quintet untouched: `pyproject.toml` `version = "0.0.14"` and
  `django_strawberry_framework/__init__.py` `__version__ = "0.0.14"`. `CHANGELOG.md` carries no
  `0.0.15` heading and is not in the diff. Spec Decision 15 holds.
- The spec and the rationale are **clean against `HEAD`** — neither appears in `git status`, so no
  round-1 pass edited either, as the plan's write set requires.
- `docs/feedback.md` and `docs/feedback2.md` are clean and unnamed in the diff. Sweeping every
  added line of `git diff HEAD -- django_strawberry_framework tests examples` for a review
  document, round, pass, worker, finding, severity or artifact filename returns **nothing**, so
  the standing no-process-provenance rule held across four passes. The surviving `spec-046
  Decision N` pointers are the licensed kind.
- Lint and layout, read-only: `uv run ruff format --check django_strawberry_framework tests`
  (`229 files already formatted`), `uv run ruff check django_strawberry_framework tests`
  (`All checks passed!`), `scripts/check_trailing_commas.py --check` over all seven changed paths
  (exit 0), `git diff --check` clean.
- Focused scope in the shared environment, my own run, no `--cov*` flag:
  `uv run pytest tests/test_views.py tests/test_routers.py examples/fakeshop/test_query/test_transport_api.py --no-cov`
  — **411 passed** (197 + 145 + 69), matching the pass-4 review's figure row for row.

### Floor verification — re-run by this pass, at the plan's full declared scope

The plan assigns R1 one floor run and names both files. I did not accept any pass's record of
it. Floor facts taken from `BUILD.md` `## Floor verification`, its single canonical statement:
the supported floor is **Django 5.2.0 on Python 3.10 with strawberry-graphql 0.316.0**.

`/tmp/dsf-floor` was on disk from the earlier passes and was **reused only after reading its
resolved versions**, never from a number written down in this artifact:

```shell
/tmp/dsf-floor/bin/python -V
uv pip list --python /tmp/dsf-floor/bin/python
/tmp/dsf-floor/bin/python -m pytest tests/test_views.py tests/test_routers.py --no-cov
```

Read: **Python 3.10.19**, **django 5.2**, **strawberry-graphql 0.316.0**, asgiref 3.12.1,
channels 4.3.2, django-filter 26.1, pytest 9.1.1. Result: **342 passed in 8.15s** (197 + 145),
the plan's full declared scope. That is the number the pass-4 build report and the pass-4 review
each recorded, reproduced by a third party. No `uv pip install` was run in this pass, so nothing
could have leaked into the shared `.venv`; the floor commands were invoked as
`/tmp/dsf-floor/bin/python -m pytest` throughout.

### The four `docs/feedback.md` findings, audited at the contract level

Each was audited against source and the tests, not against a passing suite. Where a property is
mechanical I re-derived it; where it is behavioural I drove it.

**P1a — the declared JSON charset. Closed.** `views.py::_declared_charset_is_unhonourable`
answers `declared is not None and not _canonicalizes_to_utf8(declared)` — `is not None`, so
`charset=` (present and empty) is refused while absence passes, which is the discrimination the
contract needs. `::_RequestBodyBoundaryMixin._enforce_body_charset_declaration` raises
`HTTPException(400, _JSON_PARSE_REASON)`, the one literal every other refusal on this boundary
carries, so a caller cannot attribute a rejection by message. It is composed **third** in
`::_enforce_request_boundary`, behind two checks that measure or read headers and parse nothing,
and that method is reached from both `run` overrides (through
`::_enforce_request_boundary_once`) and from `middleware/request_body.py::…process_view`, so all
three entry points enforce it. Driven over the real request object across 7 declarations x 3
methods: every UTF-8 alias passes, `utf-8-sig` / `iso-8859-1` / an unknown name / an empty
declaration are refused on POST and PUT, GET passes, and a multipart POST is left to
`::_enforce_multipart_form_encoding`. Entry 1 removes the refusal (7 rows) and entry 2 the
carve-out (2 rows), both set-equal across all four passes.

**P1b — the project's configured CSRF class. Closed, and the round's own regression is closed
with it.** The fix is `_boundary_ordering.py::_CsrfOrderingExemption.__bool__`:

```python
request = _boundary_middleware_request.get()
return request is None or not getattr(request, _BOUNDARY_ENFORCED, False)
```

Read at the source, not from A-2's table: the ContextVar holds the **request object**
(`ContextVar[HttpRequest | None]`, `default=None`), set and reset around the whole downstream
call in `__call__` / `__acall__`; the stamp has exactly one writer,
`process_view #"setattr(request, _BOUNDARY_ENFORCED, True)"`, and it is the statement
immediately after a successful `view._enforce_request_boundary(request)`. So "the exemption is
withdrawn" and "the boundary ran" are now one fact about one request object rather than two
facts about a chain and a callback — which is precisely the conflation the shipped defect rested
on. The two clauses are kept apart deliberately and the docstring says why, so the catalogued
`getattr(None, ...)` fold cannot be reintroduced as a simplification. Every declining path in
`_package_view_instance` returns `None` **without stamping**, so a declined callback keeps the
truthy exemption and therefore the view-local ordering: declining degrades the CSRF *class*, never
the ordering the `413` depends on. The four states were driven independently (var unset -> `True`;
set + unstamped -> `True`; set + stamped -> `False`; after reset -> `True`), and
`_require_boundary_before_csrf` was driven over nine real chains via `override_settings`:
`[B, C]`, `[Sec, B, Sec, C]`, `[B]`, `[C]`, `[]` accepted; `[C, B]`, `[Sec, C, Sec, B]`,
`[B, C, B]`, `[C, B, C]` refused at startup. Django's `load_middleware` iterating
`reversed(settings.MIDDLEWARE)` with `insert(0, ...)` is what makes `_view_middleware` run in
`MIDDLEWARE` order, so the audit checks the ordering that actually applies. Neither `views.py` nor
`middleware/request_body.py` imports the other, and `_boundary_ordering.py` pulls in no
`django*` module at runtime.

**P2a — the foreign position object. Closed.** `_request_body.py::_measured_remaining` runs, in
this order: seekable declaration, `tell()` inside `except Exception`, the `SEEK_END` probe inside
`except Exception`, **then** `_position_restored`, **then** `if type(end) is not int or
type(position) is not int: return _Probe.UNMEASURABLE`, and only then `end - position` and
`remaining <= 0`. So the type gate sits after the verified restore, no foreign `__sub__` or
`__le__` can execute inside the gate, `type(...) is int` refuses the `int` subclass an
`isinstance` check admits, and the prior round's `max(end - position, 0)` clamp is gone —
"cannot determine" routes through `body_exceeds_limit` to `_bounded_read_exceeds_limit`, which
still supplies a bound (at most `limit + 1` bytes read, `_body` never materialized, so Django's
own `DATA_UPLOAD_MAX_MEMORY_SIZE` ceiling survives). The working-tree change to this file is
**docstring-only**, which I proved rather than accepted: parsing both `HEAD` (obtained read-only
via `git show HEAD:<path>` into a scratch path outside the repository) and the working tree,
stripping every module / class / function docstring node and comparing `ast.dump`, gives
**identical** ASTs while the raw bytes differ. The corrected sentence is also *right*: it now says
`ASGIRequest`'s `SpooledTemporaryFile` is the one production stream that reaches the arithmetic and
that `LimitedStream` declares `seekable()` `False` and raises `io.UnsupportedOperation` from
`tell()`, which is what the floor read established. Entry 8 pins it at 6 rows, set-equal across
all four passes.

**P2b — the orphaned close task. Closed.** Read at source, with `consumers.py` byte-identical to
`HEAD`: `::_ConnectionRevocation.settle` answers a cancellation by `self.attempt.cancel()`, a
`contextlib.suppress`-wrapped `await self.attempt`, and a bare unconditional `raise`;
`::_attempt_close` records `_REVOCATION_ABANDONED` from its own `except
asyncio.CancelledError` arm **before** re-raising, so a cancelled attempt is terminal rather than
resting in `CLOSING`; `::build_revalidating_consumer_class`'s generated `disconnect` is
`try: await super().disconnect(code) / finally: await self._revocation.settle()`, so neither a
cancelled nor a raising upstream teardown can skip settlement and the upstream exception still
propagates; and `::close`'s mid-connection `await asyncio.shield(self.attempt)` is untouched, with
no cancel arm, so a bystander checkpoint cannot kill a nearly-committed close. Entries 9, 10 and
11 each measure 2 rows and the floor run exercises all four teardown rows at Python 3.10.19.

### Dispatched findings checklist audit — boxes 1, 3 and 4 ticked

`ARTIFACT.md` and `BUILD.md` `### Dispatched findings checklist` put the tick on this pass for a
box whose contract landed and audited clean. The only characters this pass changes outside its
own section are the three `- [ ]` box markers in `## Plan (Worker 1)`; no prose in any prior
section is edited, and every correction of an earlier section is filed as prose below.

- **Box 1 (P1 charset) -> `- [x]`.** Contract landed in `2701f41a` at the site plan V8 names and
  audited above; the review's named properties (absent passes, aliases pass, `utf-8-sig` and an
  unknown codec refused with the shared `400`, sync **and** async raw-envelope rows driven with
  `Client().generic` / `AsyncClient().generic` over a non-ASCII UTF-8 document) all hold. The two
  residuals below change no shipped behaviour and neither is part of this box's contract.
- **Box 2 (P1b CSRF class) — stays `- [x]`, and the tick is warranted.** It was ticked in pass 2
  when the High regression's fix landed. Its contract — an over-limit multipart refused before
  parsing while an under-limit request reaches and obeys the project's own `CsrfViewMiddleware`
  subclass — is true in every state I walked, on both transports, in all three arrangements
  (installed and recognized, installed and declined, not installed).
- **Box 3 (P2a foreign position) -> `- [x]`.** Landed in `2701f41a`, audited above; the review's
  requirement that regressions cover `__sub__` **and** the ordering comparison is met by
  `::test_a_position_object_whose_numeric_protocol_raises_never_runs_inside_the_gate`'s
  `subtraction-raises` / `comparison-raises` parametrizations across both view classes.
- **Box 4 (P2b orphaned close) -> `- [x]`.** Landed in `ba66ab49`, audited above; rows exist for
  both inputs the review named (a cancelled `disconnect` with a parked close, and a failing
  `super().disconnect`), and the round found and closed the fact that only the *raising* one had
  been pinned.

No box is over-ticked and none is left silently open.

### Failability manifest — 15 entries, re-derived rather than accepted

The current manifest is `docs/builder/temp-tests/r1/proofs-pass4.json`. Measured this pass,
programmatically over the emitted records rather than by eye:

- **15 entries. Lowest row count 2** (entries 2, 9, 10, 11, 15), so **no entry is weakly
  pinned** by `BUILD.md` `### Acceptance rule`'s 0-or-1 band, and the record's
  `why 0: not applicable` is correct because no entry measured zero.
- **`collection/setup errors: 0` on all 15**, and `pre-existing failing rows excluded: 0` on all
  15, so every count is a valid count. Zero `WEAKLY PINNED` verdicts in the file.
- **Worker 2's `proofs-pass4.md` and Worker 3's independent `w3p4-rerun.md` are set-equal on all
  15 entries** — I parsed both records and differenced the node-id sets; the differing-entry list
  is empty. Against pass 3, only entry 12 differs, and it **grew** by exactly the two rows pass 4
  added.
- **All 15 anchors match exactly once against the working tree**, checked by exact-string count
  of each anchor's full block, not only its first line. Three anchors have generic first lines
  (`try:` occurs 5x and 2x, `except asyncio.CancelledError:` 2x in `consumers.py`) but each full
  block is unique and each contains its boundary's decision material, which is why the runner's
  block-level match is load-bearing rather than the first-line grep.
- **Entry 12's re-label is a correction, not a widening.** Its `anchor`, `replacement`, `target`
  and `scope` are byte-identical to pass 3's; only `label` changed. The anchor is verbatim the
  whole body of `_package_view_instance` after the two `getattr` reads — both `isinstance`
  clauses *and* the `try` / `except TypeError` construction — so the new parenthesized label
  describes exactly what the mutation removes, where the old narrow label promised a narrower
  property than the mutation measured.
- **Entry 15 is correctly paired with the narrow label it inherited**, matches once, and measures
  2 rows. Its two rows are a strict **subset** of entry 12's five, which is what makes the two
  entries nested rather than redundant: entry 12 removes both answers at once and cannot
  distinguish "refused before the call" from "the construction declined it".
- **The 47-vs-42 correction in `## Review (Worker 3, pass 4)` is right, re-derived here**: the
  thirteen entries unchanged from pass 3 span **42** distinct node ids; **47** is the union over
  all fifteen.

Two observations about the manifest that are not findings and that no pass has recorded:

- **Entry 6's anchor is an initialization line**, `boundary_index = csrf_index = None`, with the
  mutation *prepending* `return`. The mutation genuinely removes the boundary (the whole
  `_require_boundary_before_csrf` audit never runs, 3 rows fail) so it satisfies
  `BUILD.md`'s "remove the boundary, not merely perturb code near it", and the entry is compliant.
  But the anchor carries no part of the audit's decision expression, so it would survive a rewrite
  of `if boundary_index is None or csrf_index is None or csrf_index > boundary_index` untouched.
  If the manifest is ever re-derived, that line is the better anchor.
- **`proofs.json` (the pass-1 record, 11 entries) is superseded and is no longer runnable**: four
  of its anchors (1, 3, 4, 5) now match **zero** times, because the exemption class moved to
  `_boundary_ordering.py`, the marker test moved into `_package_view_instance`, and the charset
  predicate was extracted. That is the anchor-first rule working exactly as designed — such an
  entry aborts having written nothing — and the file remains valid as the historical record of
  the pre-fix tree. No pass should cite it as current.

### Prior-section corrections, checked in both directions

This round carries five corrections across sections. I checked each rather than reading them.

1. **Pass 3's build report correcting the pass-2 build report's attribution** of
   `::test_a_chain_with_the_boundary_and_no_csrf_middleware_still_checks_csrf` to entries 3 and
   13: **the correction is right.** That node id appears in no entry's failing set except
   entry 14's, and entry 14's five rows are
   `::test_each_csrf_continuation_matches_the_transport_it_protects`,
   `::test_a_declined_callback_still_gets_a_complete_csrf_check[sync|async]` and both
   parametrizations of the row in question — so the boundary that bounds it is
   `views.py #"_csrf_protected_run = csrf_protect(_run_after_csrf_check)"`. The code agrees:
   `::_enforce_request_boundary_once`'s docstring states in as many words that the CSRF
   continuation is deliberately left unconditional so the endpoint stays protected on a chain with
   neither the package middleware nor `CsrfViewMiddleware`.
2. **Pass 3's review correcting its own pass-2 sentence** ("entry 12's current anchor and its two
   rows survive either way"): **right, and honestly filed.** `w3p3-aux.md` records that anchor at
   **0 rows**, exit 1, `WEAKLY PINNED`, restore proved.
3. **Pass 4's build report correcting pass 3's `### Implementation notes`** ("subsumed for every
   input any row supplies … so they are a clause of one recognition"): **right.** *For every input
   any row supplied* is not *for every input*, and entry 15 now measures the clauses at 2 rows.
4. **Pass 4's review correcting the attribution of that correction** (the sentence is Worker 2's,
   in the pass-3 **build report**, not a sentence of the pass-3 review): **right**, and the
   pass-4 build report had attributed it correctly in the first place, so the correction is
   defensive rather than remedial. Both of the round's own false sentences — the pass-2 review's
   and the pass-3 build report's — now stand corrected in later sections; neither is outstanding.
5. **Pass 4's review's two loosenesses in the pass-4 report** (42 not 47 distinct node ids; one of
   the "four sites" did have its docstring rewritten this pass): **both right**, the first
   re-derived above, the second confirmed against that report's own `### Files touched`.

### One correction this pass files against an earlier section

`## Review (Worker 3)` `### Dispatched findings checklist walk` item 4 states that proof entries
9, 10 and 11 "each fail 2 rows and each fails a *different* pair, so the three boundaries are
separately pinned rather than jointly." **Measured, entries 9 and 10 fail the identical pair** —
`::test_cancelling_the_teardown_ends_the_close_attempt_instead_of_orphaning_it` and
`::test_a_cancelled_disconnect_leaves_no_task_retaining_the_connection` — in every one of the four
passes' records; only entry 11's pair differs. So `settle`'s cancellation arm and
`_attempt_close`'s `ABANDONED` arm are pinned *jointly*, by one pair of rows, not separately. The
same pass's non-weakening check 1 states the accurate half of this (entry 9 fails those two rows
and **not** the round-2 bystander rows, which is the separation that matters for the two shields).
Nothing in the acceptance arithmetic moves: both boundaries clear the 0-or-1 band at 2 rows.
What it costs is redundancy — one fixture change to that pair retires the pinning of both
`consumers.py` cancellation boundaries at once. Recorded as a deferred strengthening below rather
than as a re-loop: `consumers.py` is committed and byte-identical to `HEAD`, and a row that
distinguishes "the state was recorded as `ABANDONED`" from "the attempt was cancelled and awaited"
is a new test row for the card that next touches that file.

### Residuals this pass found, and why none of them holds the round

Each is recorded with its reachability, its failure direction, and where it goes.

1. **A wrapper that drops *both* marks still loses the ordering.** With `csrf_exempt` gone too,
   the chain's `CsrfViewMiddleware` applies to the callback in full and its `request.POST` read
   precedes the view. This is pre-`2701f41a` behaviour (dropping `csrf_exempt` always lost the
   ordering), the cap still refuses the already-materialized body, and
   `views.py::_run_after_csrf_check`'s docstring states it as one of three named non-guarantees.
   Not a defect and not new.
2. **`__bool__` cannot compare the ContextVar's request against the request the CSRF middleware is
   asking about**, because Django's `csrf_exempt` protocol passes no request. Driven: a stamped
   request in the var while an unstamped one is judged reads `False`. Reaching it needs a nested
   handler built from a *different* `MIDDLEWARE` list inside a boundary-handled request — any
   in-process sub-request re-enters `__call__` and re-points the var. Consequence is **ordering
   only**: the inner request is unstamped, so `::_enforce_request_boundary_once` runs the full
   boundary in the view and the unconditional `csrf_protect` continuation still performs exactly
   one complete check. `## Review (Worker 3, pass 2)`'s nine-state walk reached the same state and
   the same verdict independently. It is the tightest key that read site permits; it belongs in
   R2 as one scoping sentence, not in code.
3. **`views.py::_canonicalizes_to_utf8` catches `(LookupError, TypeError)` only.**
   `codecs.lookup` can also raise `ValueError` (embedded NUL) and `UnicodeEncodeError` (lone
   surrogate). Not wire-reachable: Django's own `HttpRequest._set_content_type_params` calls
   `codecs.lookup` on the declared charset during request construction under `except LookupError`,
   so such a value kills the request before any view or middleware runs. The residual is a
   consumer-set `request.encoding` or a `DEFAULT_CHARSET` carrying one, i.e. in-process
   misconfiguration, and the direction is an uncaught `500` rather than an acceptance. The helper
   is pre-existing at `HEAD` and outside this round's diff; a two-type widening is a deferred
   item.
4. **`settle`'s "awaits it to completion" is guaranteed under a single cancellation, not a
   repeated one.** A canceller that cancels twice (an `asyncio.timeout` around application
   shutdown) makes the `await self.attempt` inside `contextlib.suppress` re-raise immediately, so
   `settle` re-raises before the attempt reaches `done()`. Not a durable orphan: the task is
   already cancel-requested and `_attempt_close`'s `except asyncio.CancelledError` arm records
   `ABANDONED` on its next step, so nothing retains the adapter, consumer, scope or session past
   the loop's own teardown. This is the generic limit of cleanup-during-cancellation rather than a
   design error; it makes one docstring sentence and the settlement half of Decision 16 slightly
   stronger than what the code can promise, which is an R2 precision item.
5. **The multipart POST carve-out still skips the counted rung**, so a multipart body with an
   absent or understated `Content-Length` gets Django's upload settings and no package count.
   That is spec-046's stated boundary, symmetric in both arrangements, and untouched by this
   round.
6. **`_package_view_instance` uses `isinstance(initkwargs, dict)` where this repo's convention
   for a type gate on a decision value is `type(x) is int`** (`views.py::_resolved_max_request_body_bytes`,
   `_request_body.py::_measured_remaining`). The direction is safe — pass 4 measured that removing
   the clause makes recognition *wider*, not fail-open — so no row is owed, per the pass-3
   review's own instruction. Recorded only so the inconsistency is deliberate rather than
   unnoticed.

None of these is a correctness regression, none is reachable from the wire without in-process
code that could set the limit directly anyway, and every one of them fails closed or fails
loud. Each has a home in the list below.

### DRY, hot path, public surface

- **DRY across the round.** A-1's third private module removed the `views.py` -> `middleware/`
  inversion (proved three ways: neither module imports the other, `_boundary_ordering.py` adds no
  `django*` module to `sys.modules`, and each of the four moved definitions occurs exactly once in
  the package). DRY (f)'s `_declared_charset_is_unhonourable` has two call sites and a body
  token-identical to the two lines it replaced. `_package_view_instance` has one call site and
  earns its name as the answer the hook branches on and the anchor two manifest entries need. The
  one duplication left standing — the four `_marked_callback_*` fixtures — is where the contract
  lives per fixture, and collapsing it into a factory would delete four explanations. **No new
  duplication, and nothing outstanding.**
- **Hot path.** The declaration was inherited by the fixing passes and discharged: three metrics,
  same experiment on both arms, worst reading **~15 ns per request** against a ~314 us request,
  reproduced by Worker 3 in `.venv` and at the floor inside the recorded band. Whether that cost
  is acceptable is the maintainer's call; the obligation that it exists and reaches them is met.
- **Public surface.** `git diff HEAD -- django_strawberry_framework/__init__.py` is empty.
  `middleware/request_body.py`'s `__all__` is still `("GraphQLRequestBodyBoundaryMiddleware",)`,
  so the documented `MIDDLEWARE` string does not move; `_boundary_ordering.py` is private (no
  `__all__`, every name underscore-prefixed, no re-export in either `__init__.py`). No new public
  export.

### Consolidated hand-off for R2 and R3 — the authoritative, de-duplicated list

Four build reports and four reviews each carry a `### Notes for Worker 1 (spec reconciliation)`
section, several items are superseded by later measurements, and one is blocked on the
maintainer. This list replaces all eight for planning purposes: **R2's planning pass works from
here.** Every item carries its current status.

**R2 — spec (`docs/spec-046-transport_security-0_0_15.md`)**

- **R2-1. Decision 18's heading and opening sentence are both false at `HEAD`.** The heading
  reads "… **via view-local CSRF re-entry**", which now describes the *fallback* only, and the
  text opens "No package middleware … and no required `MIDDLEWARE` entry" — false in its first
  clause, true in its second. Measured rename cost: the slugged anchor occurs **15 times in the
  spec** and **1 time in the rationale**; `csrf_exempt` occurs **13 times in the spec**, all on
  the pre-`2701f41a` shape. A half-reconciled Decision 18 is worse than an un-updated one.
  *Status: open, unchanged since pass 1.*
- **R2-2. Decision 18 owes the new deployment contract**, since
  `grep -c GraphQLRequestBodyBoundaryMiddleware` returns **0** in the spec, the rationale,
  `docs/GLOSSARY.md`, `docs/README.md`, `docs/TREE.md`, `KANBAN.md` and the terms CSV (re-measured
  this pass). Install it immediately before the project's CSRF entry; a chain listing it after one
  is refused at startup; a deployment without it keeps the old arrangement unchanged. Rejected
  alternative to record beside it, from the review itself: remove the exemption and stock re-entry
  outright — rejected because it changes behaviour for every deployment that has not edited
  `MIDDLEWARE`. *Status: open.*
- **R2-3. Decision 18's ordering-audit clauses, now measured on both halves.** Entries are
  compared by **resolved class**, so a subclass of either side is recognized; a chain with more
  than one CSRF entry is judged against the **first**, since that is the entry whose
  `request.POST` read parses the body. Pinned by entry 6's three rows.
  *Status: open, wording proposed in the pass-1 build report's note 3.*
- **R2-4. Decision 18's recognition sentence, both clauses pinned.** *The boundary middleware
  runs a package view's boundary only for a callback whose bookkeeping it can build that view's
  instance from, and it never calls anything that is not a class to try.* First clause: entry 12
  at 5 rows. Second clause: entry 15 at 2 rows plus two named permanent rows. **Do not** write the
  `view_initkwargs` `dict` test as a symmetric guard — measured, removing it makes the middleware
  run the boundary for a non-`dict` mapping, i.e. it is a narrowing preference, not a bound.
  *Status: open, and this is the item three passes converged on.*
- **R2-5. Decision 18 owes the declined-callback state**, which the fix made reachable and the
  spec never describes: a callback the boundary middleware does not recognize keeps its exemption,
  so the view supplies the ordering and Django's stock CSRF class performs the check — the class
  degrades, the ordering does not. That sentence is what makes "both arrangements enforce CSRF and
  both enforce the cap" true of three states rather than two. *Status: open.*
- **R2-6. Decision 18 owes one scoping sentence for the nested-handler state** (residual 2 above):
  the guarantee is scoped to the chain that handles the request. *Status: open, corroborated
  twice.*
- **R2-7. Decision 9 has no declaration half at all.** The shipped refusal
  (`views.py::_RequestBodyBoundaryMixin._enforce_body_charset_declaration`, plan V3) is a wire
  boundary no spec sentence states. It needs the current contract with no chronology: absent
  passes, aliases pass, `utf-8-sig` / unknown / non-UTF-8 refused with the shared `400`, multipart
  is the other guard's, GET is out of scope. *Status: open.*
- **R2-8. The GET-only method scope is a contract question Decision 9 must answer**, not a code
  change on a review's prose. A `HEAD` carrying `charset=iso-8859-1` receives `400` where
  upstream would answer `405`; the direction is stricter, the reason string is shared, and the
  scope agrees with `::_enforce_request_body_limit`'s. Pass 2 confirmed the routing and left the
  guard **character-identical to `HEAD`**, so entry 2's anchor and rows are untouched and R2 is
  free either way. *Status: open, code deliberately unchanged.*
- **R2-9. V4 stands** — the spec still asserts the `CLOSING` ruling `ba66ab49` retracted, in four
  places (the ruling sentence, the `ABANDONED` state definition, a test-plan line, a DoD line
  naming `asyncio.shield`). Add that `disconnect` enters settlement through `finally` and that a
  cancelled attempt is terminal. **New from this pass:** state the settlement contract at the
  strength the code keeps — a single cancellation is cancelled-awaited-re-raised; under repeated
  cancellation the attempt is left cancel-requested and terminal rather than awaited to
  completion (residual 4). *Status: open, one clause added by this pass.*
- **R2-10. Decision 16 owes the premise `settle`'s correctness rests on** — "only the connection's
  final teardown cancels this task" — which currently lives only in a code comment. A third-party
  cancellation of the attempt would propagate a `CancelledError` in place of a caller's exception;
  measured, and unreachable through any supported seam (`attempt.cancel()` occurs once in the
  package, inside `settle`). *Status: open.*
- **R2-11. The spec's `Status:` block and opener need a re-read against `HEAD`.** It reads
  "Planned for `0.0.15`" and "**BUILT — all five slices …**", which is accurate for an uncut
  `0.0.15`, but the same block must not survive R2 asserting the pre-`2701f41a` CSRF arrangement
  around it. **This pass may not edit the spec** (the plan's R1 write set names neither file), so
  no status-line edit was made and none was needed on its own terms. *Status: R2's, at its first
  custodian pass.*

**R2 — rationale (`docs/spec-046-transport_security-0_0_15-rationale.md`)**

- **R2-12. The rationale's `### Decision 18` lists as a *rejected alternative* the design the code
  now ships**: "*A narrow package middleware placed before `CsrfViewMiddleware`, plus a system
  check that detects missing or wrong ordering*. **Rejected**: it adds a required deployment entry
  …". `2701f41a` shipped that, minus the "required" — the withdrawable exemption is what makes the
  entry optional, and that is the fact that turns a reversal into a resolution. Note also that
  what shipped is a **startup raise from `__init__`**, not a Django system check. V1's grep misses
  this because the bullet never names the class. Two resolutions: move it to a keyed change record
  naming the round that adopted it, or keep it rejected in its *original* form (middleware **plus**
  a required entry) and state what the shipped design does differently. Path one reads better.
  *Status: open, and the most misleading shape in the companion file.*
- **R2-13. The rationale has never been reconciled against any of the four post-gate reviews**
  (plan pre-flight step 7). Every decision the closeout touches needs its keyed entry: the
  alternatives rejected, every change the decision has undergone with the round that caused it,
  and every claim it may no longer make. *Status: open, the round-shape reason R2 exists.*

**R3 — documentation and archive**

- **R3-1. V1, V2, V3, V5, V6, V7 stand as Worker 0 recorded them**, re-measured this pass for V1
  (0 mentions of the middleware in any of the seven surfaces) and V6 (all six terms present in
  `docs/GLOSSARY.md` at `**Status:** shipped.` with no `CardGlossaryTerm` link from `KANBAN.md`).
- **R3-2. M-A is decided and is R3's to enact** (fakeshop installs the middleware immediately
  before `CsrfViewMiddleware`; the fallback stays covered live under `override_settings`). **M-A's
  re-pin estimate is superseded**: the one live row it expects to break
  (`::test_the_async_view_also_refuses_before_djangos_parser_runs`) breaks by exactly the mechanism
  the High fix removed, and pass 2 measured it **passing** under M-A's own chain, independently
  confirmed by the pass-2 review. So R3 owes the prose corrections and the new shipped-chain
  assertion, **not** the move to a fallback-override chain. *Status: measured, obligation reduced.*
- **R3-3. `examples/fakeshop/test_query/test_transport_api.py` is stale in prose**, not in
  assertions: `::_carrying_the_packages_csrf_mark`'s docstring describes one mark and "every
  Django view decorator carries it onward through `functools.wraps`" where there are now two, and
  the wrapper itself copies one. Already in R3's write set under M-A.
- **R3-4. A genuine live-first opportunity, not a requirement.** Once fakeshop's `MIDDLEWARE`
  carries the boundary, that same wrapper *is* the marker-dropping shape the High fix is about, so
  R3 can earn the fix's central assertion at the live tier by adding a parse or upload-handler
  witness to that row. The six new package rows stay correctly placed under `AGENTS.md` #10
  whatever R3 does — a marker-dropping wrapper mount, a marked-but-unbuildable callback, a chain
  with no CSRF entry and a misordered chain are none of them shapes a live fakeshop query can
  reach.
- **R3-5. `docs/README.md`'s withdrawal wording must be the narrow form the code implements** —
  the exemption is false for a request whose boundary a chain entry **ran**, never for any request
  travelling an installed chain. The broad form is the sentence the High finding falsified.
- **R3-6. `docs/TREE.md`'s regenerate gains one row** for `_boundary_ordering.py`; its module
  docstring carries no staging language, verified, so the render is safe. The same render also
  surfaces two pre-existing drifts (`middleware/request_body.py` absent, `utils/sessions.py`'s
  docstring) which are V5's.
- **R3-7. `middleware/__init__.py` is correct as it stands** — recorded so R3 does not "fix" a
  non-problem.

**Deferred beyond this cycle (candidates for the next card that touches these files)**

- **D-1. A row distinguishing `_attempt_close`'s `ABANDONED` record from `settle`'s
  cancel-and-await** — proof entries 9 and 10 currently fail the identical pair (this pass's
  correction above), so the two boundaries are jointly pinned at 2 rows each.
- **D-2. Widen `views.py::_canonicalizes_to_utf8` to catch `ValueError` and `UnicodeEncodeError`**
  (residual 3). Pre-existing, fail-loud, not wire-reachable.
- **D-3. Re-anchor manifest entry 6** onto the audit's decision expression rather than its
  initialization line, if the manifest is ever re-derived.
- **D-4. The duplicated-*boundary*-entry over-refusal** (`[boundary, csrf, boundary]` is refused
  because the audit keeps the *last* boundary index and the *first* CSRF index) and the **double
  measure** two adjacent boundary entries cause (`process_view` calls
  `view._enforce_request_boundary`, not `::_enforce_request_boundary_once`). Both are safe-direction
  costs, deliberately unpinned so R2's contract sentence is not frozen by a row. R2 says which it
  is; only then does a row pin it.
- **D-5. `_measured_remaining`'s pre-existing "(`ASGIRequest`'s spool and `WSGIRequest`'s
  `LimitedStream` both measure honestly on both supported interpreters)"** is imprecise for the
  same reason the sentence above it was corrected — a stream that declines to measure is not
  measuring honestly. Outside this round's carve-out.
- **D-6. A shared "is this one of our views?" recognizer with `middleware/debug_toolbar.py`** is
  now a *decidable* question rather than a foreclosed one, since A-1 removed the import
  constraint. Deliberately not acted on in a security-fix pass; the condition that justifies
  revisiting it is a third middleware needing the same recognition, or the two needing to agree on
  one callback. Note that `debug_toolbar` recognizes a package view by class through an
  **upstream** `BaseView` import, so a narrower recognition needs no import of `views.py`.

**Blocked on the maintainer — not settled here, and not written either way**

- **M-B (build plan `## Open maintainer decision M-B`). What recognition owes a forged boundary
  marker.** A callback carrying the package's private marker whose `view_class` is a real,
  buildable class that is not a package view (measured with `view_class = dict`,
  `view_initkwargs = {}`) reaches `view._enforce_request_boundary(request)` and raises
  `AttributeError` out of `process_view`, because recognition ends at *an instance was produced*
  rather than *an instance carrying the boundary*. Verified live this pass: the clause
  `#"a hook whose every other outcome is a controlled response"` is on disk in
  `middleware/request_body.py::_package_view_instance`. Nothing supported reaches the condition —
  the marker name is package-private and Django's `View.as_view` validates `initkwargs` at
  `as_view` time — and both R1 review passes graded it Low on that basis. **This pass settles
  nothing, writes no Decision 18 sentence for either outcome, and does not let it drive
  `revision-needed`.** What each candidate would change, so R2 enacts whichever lands:
  - **(a) recognition ends at an instance that carries the boundary** — one
    `getattr(instance, "_enforce_request_boundary", None)` probe in `_package_view_instance`, at
    least two new rows in `tests/test_views.py`, one new manifest entry, and a fifth
    parametrization of `::test_a_marked_callback_the_middleware_cannot_build_is_declined_not_crashed`.
    All five docstring claims then become true unchanged. Write set grows by
    `middleware/request_body.py` and `tests/test_views.py`. The `debug_toolbar` precedent says the
    probe may need no `views.py` import, so A-1's no-import property can survive.
  - **(b) declare the forged marker out of contract** — no code change; Decision 18 scopes the
    guarantee to genuine mounts and the five claims are narrowed. R2 and R3 absorb it with no new
    path.
  - **(c) refuse it outright** — a controlled refusal, or a `ConfigurationError` where detectable
    at startup. Loudest, but it changes the declined-callback contract passes 2-4 built and
    measured, so it reopens settled work.
  - **The site inventory the decision must sweep is five, not four**, and the fifth is newly
    written in a file this cohort owns:
    `middleware/request_body.py::_package_view_instance #"a hook whose every other outcome is a
    controlled response"`; `middleware/request_body.py #"so no non-package view is touched"`;
    `tests/test_views.py::_marked_callback_without_a_view_class`;
    `tests/test_views.py::test_a_marked_callback_the_middleware_cannot_build_is_declined_not_crashed`'s
    docstring; and that same docstring's newer
    `#"The four routes are the four ways a callback"` exhaustiveness claim, which is false because
    the fifth route exists and is not refused.

### Spec changes made (Worker 1 only)

**None.** The plan's R1 write set names neither `docs/spec-046-transport_security-0_0_15.md` nor
its `-rationale.md`, and `### Round R2`'s equivalent assigns both to a separate round whose
authoring pass is Worker 1's. Both files are clean against `HEAD` at the end of this pass. Every
spec and rationale item this round surfaced is consolidated above as R2's input rather than
enacted here.

Deferral reasons for everything left open, as `## Final verification job` step 3 requires: all
four `### Dispatched findings checklist` boxes are now `- [x]`, so no box carries a deferral. The
six residuals and six deferred items above are recorded with their targets — R2, R3, or the next
card that touches the file — and none of them is a `docs/feedback.md` finding's contract.

### Summary

R1 audited the remediation of `docs/feedback.md`'s four findings, which the maintainer committed
outside the worker cycle in `2701f41a` + `ba66ab49`, and it did what an audit is for: it found a
**High** security regression that the remediation itself introduced — the CSRF exemption withdrawn
chain-wide while the boundary ran only per-marked-callback, measured as a real
`MultiPartParser.parse` on an over-limit multipart body — plus a Medium missing row and four Lows
across four passes. All are closed. The fix keys the withdrawal off the per-request
`_BOUNDARY_ENFORCED` stamp rather than a chain-wide flag, so "the exemption is withdrawn" and "the
boundary ran" became one fact about one request; the marks, the ContextVar and the exemption moved
into a new private protocol module, `_boundary_ordering.py`, after which `views.py` and
`middleware/request_body.py` no longer import each other; the recognizer now guards its answer
rather than three spellings of its input; and the round left the four findings' own contracts
landed, audited, and pinned by a 15-entry failability manifest whose lowest row count is 2 and
which Worker 3 re-ran set-equal at every pass. The round also discharged two obligations a
maintainer commit cannot carry: the ten (now fifteen) landed boundaries' failability proofs, and a
post-hoc hot-path number for per-request cost the remediation added.

### Final status

`final-accepted`.

Nothing in this pass reaches the bar for `revision-needed`. The manifest is sound and
independently re-derived; the floor run is the plan's full declared scope, re-run here at **342
passed** on Python 3.10.19 / django 5.2 / strawberry-graphql 0.316.0 read from the venv rather
than recalled; `git diff --cached` is still the one path `W-1` authorizes; the version quintet,
`CHANGELOG.md`, the spec and the rationale are untouched; the lint, layout and whitespace gates
are clean; the focused scope is **411 passed** in the shared environment; every prior-section
correction checks out and the one inaccurate claim no later section caught is corrected in prose
above; and the six residuals I found are each unreachable from the wire, fail closed or fail loud,
and carry a named home in the hand-off list. The one open contract call, **M-B**, is the
maintainer's and is recorded as blocked with what each of its three candidate answers would change
in the code and in the spec — this pass wrote no Decision 18 sentence for any of them and did not
let it drive the verdict.
