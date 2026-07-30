# Build: custodian pass 3 — the nine-claim audit (card 046, transport_security / 0.0.15)

Status: final-accepted

Spec reference: `docs/spec-046-transport_security-0_0_15.md` (whole file) and its rationale
companion `docs/spec-046-transport_security-0_0_15-rationale.md`. Both are the only files this
pass wrote, plus this artifact.

## Scope and ownership

Nine verified factual corrections, each already proved against source by an independent auditor
and re-verified by Worker 0. **None was re-litigated.** Every one was re-confirmed by anchor
string or by execution before it was written — never by line number — because a concurrent
Worker 2 was editing `routers.py`, `_strawberry_patches.py`, `views.py`, `exceptions.py`,
`docs/README.md`, `examples/fakeshop/test_query/test_transport_api.py` and the fakeshop DB
throughout this pass. Those files were read, never written. `git status --short` was **28** rows
at the end of the pass (23 modified, 5 untracked); the two spec files are the only rows this pass
put there, and `_strawberry_patches.py`, `exceptions.py`, `routers.py`, `test_transport_api.py`
and `build-046-…md` appeared under Worker 2 while it ran.

Already applied by Worker 0 in Decision 6 (the phantom `subscriptions_enabled` kwarg; four hooks
with the placement split delegated to the DRY section) was **verified present and left exactly as
it stands** — neither redone nor reverted.

Sizes, measured in characters: spec `229,630 -> 233,292`; rationale `73,718 -> 89,195`.

## Correction 1 (HIGH) — the over-reported-position shape is refused, not read

**4 spec sites.** The falsified telling existed in two places and its narrow companion in two
more.

Before, `## Edge cases and constraints`:

> Both make the probed difference zero or negative, and zero taken at face value reads as
> "within the limit" with no byte read anywhere […] The cost in the over-reporting direction is
> disclosed rather than papered over: the restored position lands past the end, so the request
> reaches Strawberry with an **empty** body and is a `400` at the parse — never a bypass.

After (excerpt):

> The two are refused differently, because the restore is verified **before** the two answers
> are ever subtracted. An over-reported position cannot survive that verification — the
> restoring seek is issued in the same lying coordinates and the verifying `tell()` disagrees —
> so the probe reports a position it could not prove it put back and the request is refused with
> the package's own `413` on **zero bytes read**, plus the one server-side `WARNING` […] An
> under-reported end restores cleanly, so its answer *is* judged, and it comes out at or below
> zero […]

Re-verification: `_measured_remaining` calls `_position_restored(stream, position)` before
`remaining = end - position` is reached; `_position_restored` returns `False` when the verifying
`tell()` disagrees; `body_exceeds_limit` then logs `_CORRUPTED_PROBE_LOG_MESSAGE` and returns
`True`. `tests/test_views.py::test_a_stream_reporting_a_position_past_its_end_is_refused_rather_than_read`
asserts `413`, `stream.requested == []`, `stream.delivered == 0`, `_body` absent and the single
log record; `_MisreportingSizeStream` (the under-reported end) restores cleanly, so `remaining`
comes out `0` and it reaches the bounded read.

Also fixed, same correction:

- **Test-plan row 15.** Rewritten so the two directions are separate rows. One additional
  precision beyond the brief: the row previously paired the under-reported end with "the
  genuinely-empty one (allowed, one bounded read)" as if both were the same stream shape. They
  are not — `test_a_genuinely_empty_body_is_allowed_by_one_bounded_read` uses
  `_UndeclaredSeekableStream(b"")`, an **honest** stream. The row now names the genuinely-empty
  body as the *control* for the under-reported end rather than as the same shape. It also no
  longer calls the four `seekable()`/seek/subtraction/restore stand-ins "the **third** probe
  outcome", since three of the four are second-outcome shapes.
- **Widening the restore, at both sites that narrowed it to "raises".** Row 15's list and the
  `## Edge cases` capability-call bullet now read "a **restore the probe cannot prove** — the
  restoring seek raised, or the `tell()` that verifies it answered something other than the
  position the probe started from", and Decision 7's canonical outcome 3 says the same and adds
  that an over-reported position takes the second route. `_position_restored` returns `False` for
  both and `body_exceeds_limit` refuses them identically.

**Kept, because it is true and load-bearing:** neither production stream lies; the unfixable case
is a *plausible* lie (an end that is wrong but still ahead of the position); rewinding to zero
would corrupt a legitimately mid-position stream; recovering an over-reporting stream's true
bytes is impossible.

**Already correct, left alone:** Decision 7's outcome 2 reads "the pair came out incoherent
**and the restore succeeded**". That qualifier is exactly what makes it true, and it is the only
route by which an incoherent pair reaches outcome 2. It was not touched.

**One enumeration I deliberately reverted mid-pass.** My first draft added the verifying `tell()`
as a fifth item to the edge-case bullet's list of guarded calls, which would have contradicted
Decision 7's "**four** capabilities". Both lists say four; the code guards six. Rather than create
an inconsistency I had no mandate to resolve, the list is untouched at both sites and the count is
reported below as unfixed.

## Correction 2 — the lock is on the consumer, not the adapter

**1 spec site** (Decision 16, *One connection-local lock, held through the send*).

Before: "A single `asyncio.Lock`, owned by the connection's adapter instance (upstream constructs
exactly one per connection, …)".
After: "A single `asyncio.Lock`, owned by the package's consumer instance (Channels constructs
exactly one per connection, …)".

Re-verified: `GraphQLWebSocketConsumer.__init__` assigns `self._revocation_lock` and
`self._revocation_observed`; the class docstring says "per-INSTANCE … one consumer instance is
exactly one connection"; `send_revalidated_operation_frame` reaches them through
`websocket.ws_consumer`, and `revalidate_operation_actor` through `handler.view`. Nothing is
assigned on the adapter subclass. The whole soundness argument after the parenthetical (holding
the lock through the send; the sibling-task interleaving it prevents) was re-read against
`send_revalidated_operation_frame` and is unchanged.

The other two "connection-local lock" mentions (`## Edge cases`, `## Risks`) name no owner and
were correct; the implementation-plan table's "its connection-local lock" is listed under unfixed
observations below.

## Correction 3 — the DRY bullet's "one set of state on the adapter instance"

**1 spec site** (`## Helper-reuse obligations (DRY)`).

Before: "are **one** set of state on the adapter instance upstream already creates per connection
— not three parallel caches keyed by protocol."
After: "are all **connection-scoped**, in the two homes a connection already has: the lock and
the flag on the one consumer instance Channels creates per connection, the timestamp on that
connection's ASGI `scope` — never three parallel caches keyed by protocol."

Re-verified: the timestamp is `scope[_REVALIDATED_AT_SCOPE_KEY]`, written in
`consumers.py` only when `window > 0.0`. So the claim was wrong about the object *and* about
there being one of them; the connection-scoped property is what is load-bearing and true, and the
protocol-cache contrast is kept verbatim.

## Correction 4 — "two-line delegate" at three sites, told correctly in a fourth

**4 spec sites found, 3 wrong, 1 already correct.**

- `## Slice checklist`: "`parse_multipart` with a two-line delegate over one shared mixin helper"
  -> "with a thin delegate over one shared mixin helper — two statements on the sync view, three
  on the async one, whose request adapter's form data must be awaited before it can be handed
  over".
- Decision 17: "with a two-line delegate that runs the helper and then calls `super()` — the sync
  view synchronously, the async view as a coroutine" -> "with a thin delegate … — the sync view
  synchronously in two statements, the async view as a coroutine in three, because its request
  adapter's form data must be awaited before it can be handed over".
- Decision 11: "those at two two-line subclasses, each of which awaits one shared package
  function and then delegates with `super()`" -> "those at two three-line subclasses, each of
  which awaits one shared package function, returns without admitting the operation if it
  refused, and otherwise delegates with `super()`".
- `## Helper-reuse obligations (DRY)`: already stated per colour ("the sync one two statements,
  the async one three, because the async request adapter's form data must be awaited") and was
  **not** edited — it is the telling the other three were matched to.

Re-verified: `views.py`'s sync `parse_multipart` is two statements; the async one is three
(`form_data = await request.get_form_data()` first). `consumers.py`'s
`_RevalidatingTransportWSHandler.handle_subscribe` and `_RevalidatingGraphQLWSHandler.handle_start`
each have a three-line body. `grep -n "two-line\|two line"` over the spec now returns **zero**
rows.

## Correction 5 — `AllowedHostsOriginValidator` is not "only a factory"

**2 spec sites + 2 rationale sites (1 fixed, 1 deliberately left).**

Verified by execution at the installed channels 4.3.2: `AllowedHostsOriginValidator` substitutes
`["localhost", "127.0.0.1", "[::1]"]` when `settings.DEBUG` and `ALLOWED_HOSTS` is empty, and
Django's `HttpRequest.get_host()` substitutes `[".localhost", "127.0.0.1", "[::1]"]` in the same
situation — no leading dot on the Channels list.

- `## Current state`: now "is a factory that configures it with `settings.ALLOWED_HOSTS` — or,
  under `DEBUG` with that setting empty, with its own hardcoded
  `["localhost", "127.0.0.1", "[::1]"]` — and reads no `Host` under either".
- Decision 19, *Why call Django rather than narrow the claim*: same correction, **plus** the
  divergence stated where it earns its place — "Two boundaries a reader would both call 'allowed
  hosts' therefore already disagree about what the `DEBUG` default means, which is exactly why
  the package's Host answer must be Django's own `get_host()` and never a second expression of
  its own." That is additional evidence for the decision, which is why it went there and not
  into `## Current state`.
- Rationale, *Claim this decision falsified* (the rationale's own voice): corrected the same way.
- Rationale, the block introduced as "The spec's own record of the falsified claim, before it was
  rewritten…": **left untouched.** It is a verbatim record of the prior spec wording; editing it
  would destroy the record it exists to be. Flagged here so the next pass does not read it as a
  missed site.

**Kept, verified true:** `OriginValidator.__call__` reads `Origin` and nothing else and never
validates `Host`, so an allowed `Origin` with a hostile `Host` still connects.

## Correction 6 — the `DEBUG` + empty `ALLOWED_HOSTS` default

**1 spec site** (`## Edge cases and constraints`).

Before — makes Django accept `localhost` / `127.0.0.1` only.
After — makes Django substitute `[".localhost", "127.0.0.1", "[::1]"]`, so every `*.localhost`
subdomain is accepted, by virtue of the leading dot, and so is the IPv6 loopback.

Verified by reading `HttpRequest.get_host` out of the installed Django (identical text on 5.2 and
6.0). The bullet's remediation — do not depend on fakeshop's `DEBUG`, set `ALLOWED_HOSTS`
explicitly with `override_settings` — was correct and survives unchanged, which is why the fix
costs one clause and no test change. Two other `DEBUG`-default mentions (Decision 19's
`get_host()` ownership sentence, the DRY Host bullet) enumerate nothing and were left.

## Correction 7 — the upstream views' import list

**1 spec site** (`## Borrowing posture`).

Before: "their imports are `django`, `cross_web`, and `strawberry` only, verified in the installed
0.316.0".
After: "their imports are the standard library, `asgiref`, `cross_web`, `django`,
`strawberry.http`, and their own `strawberry.django.context` sibling — verified in the installed
0.316.0, and the same list `views.py`'s own module docstring states."

Verified by enumerating the module-level `import` / `from` lines of `strawberry/django/views.py`
in the installed 0.316.0: `json`, `typing`, `asgiref.sync.markcoroutinefunction`, `cross_web`,
four `django.*` modules, `strawberry.http.*`, and `.context`. **Conclusion kept:** no
optional-import guard applies, and the reason is now stated — `asgiref` is Django's own hard
dependency and every other name is already a hard dependency of this package.

## Correction 8 — Decision 9's "only mount" claim

**3 spec sites.** This is the one correction of the nine that was in the **unsafe** direction: the
false scoping told a consumer that disabling the Strawberry patch could not affect a package
mount.

Verified by execution (fakeshop settings, real `DjangoGraphQLView(schema=…)`):

```
b'42'   -> HTTPException 400 'The GraphQL request body must be a JSON object (or an array of …)'
b'[1,2]' -> HTTPException 400 (same)
# with BaseView.parse_json restored to _original_parse_json:
b'42'   -> 42
b'[1,2]' -> [1, 2]
```

so the body-envelope guard rides `APPLY_UPSTREAM_PATCHES` on a package mount too, because
`_RequestBodyBoundaryMixin.parse_json` ends in `super().parse_json(data)` and
`_strawberry_patches.apply` assigns `BaseView.parse_json`. The wire-level proof already exists at
`test_transport_api.py::test_the_upstream_bug_workaround_still_respects_its_own_opt_out`, which
posts `b"42"` to fakeshop's `/graphql/` (a **package** mount) and asserts `500` with the patch off.

- Decision 9, *Which docs, by surface*: "names the per-half consequence of disabling it **on
  Strawberry's own view**, the only mount the gate can still reach" -> a per-mount statement:
  the `cross_web` half reaches Strawberry's own view alone (a package mount is untouched because
  `_RawBodyRequestAdapter` shadows the patched property by identity), the Strawberry half reaches
  **both**.
- Decision 9, the `_patched_parse_json` paragraph: "and so is its subject — Strawberry's own
  view" -> "and so is its subject for the `cross_web` half — Strawberry's own view. Its subject
  is *both* mounts for the Strawberry half, whose body-envelope guard a package view still
  reaches through `super().parse_json`".
- `## Slice checklist`: "scope the per-half consequence of disabling it to Strawberry's own view"
  -> "scope the per-half consequence of disabling it **per mount** — the `cross_web` half reaches
  Strawberry's own view alone, the Strawberry half reaches a package mount too, through
  `super().parse_json`".

**Ownership argument kept and not weakened:** what rides the gate on neither mount is the wire
contract, because the strict decode and the body source are view-owned code. Both halves of that
sentence were re-read in place and are untouched.

**Swept for the same false scoping elsewhere and found correct:** Decision 9's "_patched_body …
the mount it serves is the *other* one" and "*What this means for `_patched_body` after S1*" (both
true — a package view never reaches that getter); the `_cross_web_patches.py` slice-checklist
bullet; test-plan row 24's "with the patches **on**, a mount of Strawberry's own view is proven to
keep upstream's RFC 8259 auto-detection". `## Edge cases` carries no instance.

Both patch-module docstrings already told this correctly — `_strawberry_patches.py` in the words
"What the gate does NOT scope is the **mount**". The spec was the stale telling.

## Correction 9 — the `APPEND_SLASH` bullet was unqualified

**2 spec sites.**

Verified by reading `CommonMiddleware.get_full_path_with_slash` out of the installed Django: it
raises `RuntimeError` when `settings.DEBUG` and the method is `DELETE` / `POST` / `PUT` / `PATCH`.

- `## Edge cases`: now "under `DEBUG=False` a `POST` to `/graphql` also gets a `301` … Under
  `DEBUG=True` it is not a redirect at all: `CommonMiddleware.get_full_path_with_slash` raises
  `RuntimeError` … so the same request is a `500` on the stack a reader is most likely to test it
  on."
- `### Consumer-visible behavior` (the bullet the migration note is written from): now "a `301`
  most clients will not re-`POST` under `DEBUG=False`, and a `RuntimeError` rather than a
  redirect at all under `DEBUG=True`".

`docs/README.md` line 310 already carried both halves. Test-plan row 6 and the `## Doc updates`
bullet reference "the documented `APPEND_SLASH` policy" without restating it, and were left.

## The rationale companion

Nine change-record entries, in the file's existing `**Change record — …**` style and keyed to the
decision each belongs to so it can be looked up:

| Correction | Rationale home |
|---|---|
| 1 | Decision 7 |
| 2 | Decision 16 |
| 3 | `### Change record for `## Helper-reuse obligations (DRY)`` (4th bullet) |
| 4 | Decision 17 (primary, all three sites) + a cross-reference under Decision 11 |
| 5 | Decision 19 |
| 6 | Decision 19 (separate entry) |
| 7 | `### Change record for the spec's non-decision sections` (`## Borrowing posture`); its opener updated `Three corrections` -> `Four` |
| 8 | Decision 9 |
| 9 | Decision 6 (which owns the URLconf mount; it had no change record before) |

Each entry names the falsified claim, the measured truth, the **direction of the drift**, and —
where one existed — the rejected alternative. Chronology is in the rationale only; the spec
contains zero instances of `review round`, `Worker `, `round 3`, `now states`, `now says`,
`was rewritten` or `custodian`. Three link definitions were added to the rationale's
`<!-- docs/ -->` group, in alphabetical position — `s65-borrowing-posture`,
`s65-consumer-visible`, `s65-current-state` — and all three are used.

**On the pre-existing entry that was false when written.** The DRY change-record bullet claiming
"the delegate count is now stated per colour (two statements sync, three async …) instead of
'two-line' for both" was **verified, not edited**, exactly as instructed. It is now true:
`grep -n "two-line\|two line"` over the spec returns zero rows, and the DRY bullet does state the
split per colour. The verification is the product; no character of that bullet changed.

## Verification run

- `uv run python scripts/check_spec_glossary.py --spec docs/spec-046-transport_security-0_0_15.md`
  -> `OK: 37 terms` — **exit 0**.
- **No glossary anchor changed.** The set of `[glossary-…]` reference ids in the spec is
  bit-identical to `git show HEAD:…` (37 in, 37 out, added `set()`, removed `set()`), so
  `docs/spec-046-transport_security-0_0_15-terms.csv` needs no edit and was not touched.
- Every `](#anchor)` in both files resolves to a heading in that file (GitHub slug rules: keep
  `_`, strip backticks, one `-` per space, fences stripped line-by-line). Zero missing.
- Every `][ref]` has a definition and every definition is used, in both files. Zero orphans, zero
  unused. Every rationale `->` spec anchor resolves against the spec's real headings.
- `uv run python scripts/check_trailing_commas.py --check <the two explicit paths>` -> exit 0.
  Run with explicit paths only; the pathless default would have rewritten the maintainer's
  untracked `drys.md` / `vulns.md`.
- Line width: every prose line this pass added is <= 95 characters in the spec (its convention)
  and <= 98 in the rationale (its convention). The only long lines in the diff are anchor links
  and table rows, which the file cannot break.
- **Contradiction re-read.** Each of the nine passages was re-read from the top of its section.
  Three neighbours needed a matching widening and got it (Decision 7's outcome 3, the `## Edge
  cases` capability-call bullet, test-plan row 15's outcome labelling); one enumeration was
  reverted rather than left inconsistent (see correction 1). Sections re-read whole: `## Current
  state`, `## Borrowing posture`, `### Consumer-visible behavior`, `## Slice checklist` (Slice 3),
  Decisions 6 / 7 / 9 / 11 / 16 / 17 / 19, `## Helper-reuse obligations (DRY)`, `## Edge cases and
  constraints`, `## Test plan` S2.
- No test run. No commit, no `git add`, no branch, no stash, no revert. Nothing outside the three
  owned files was written.

## Divergences noticed and NOT fixed — outside the nine

The most valuable list in this artifact. None of these was fixed; each is stated with the
measurement so the next pass does not have to re-derive it.

1. **Decision 7 says the probe "reaches for **four** capabilities"; the code guards six call
   sites.** `_declares_seekable`'s `seekable()`, the position `tell()`, `stream.seek(0, SEEK_END)`,
   `_position_restored`'s restoring `seek`, its verifying `tell()`, and the `end - position`
   subtraction — six guarded call sites across **five** `try` blocks (`_position_restored` guards
   its restoring `seek` and its verifying `tell()` together in one `try`; `_declares_seekable`
   carries one; `_measured_remaining` carries three). The `## Edge cases` capability bullet repeats
   the same
   four-item list. Both are *internally consistent*, which is why I left them; the count is
   nevertheless a measured undercount, and the two omitted calls are precisely the ones
   correction 1 turns on. Fixing it means changing a number inside the paragraph whose bolded
   opener four other sites cite by `#"substring"`, so it wants its own dispatch.
2. **`consumers.py::send_revalidated_operation_frame`'s docstring says the change "lets the
   derived adapter stay a **two-line** delegation".** `_RevocationGatedWebSocketAdapter.send_json`
   has a four-line body (type test, delegating `await super()`, `return`, the gated call). This is
   correction 4's defect class in source, and `consumers.py` is in **neither** my partition nor
   Worker 2's — it needs routing.
3. **The DRY revalidation bullet prices the delegates by `await` count.** "The handler subclasses
   contain a single `await` and a `super()` call each, and the derived outbound-frame adapter
   contains one type test, one `await` and a `super()` call." Literally, each handler body has two
   `await` expressions and the adapter's `send_json` has two `await`s and two `super()`
   references. On the natural reading ("one await *of the shared decision*, plus the `super()`
   delegation") it is not false, so I left it — but it is the same shape as correction 4 and a
   reviewer checking counts literally will raise it.
4. **`## Implementation plan` row 4 reads "the adapter-level outbound-frame gate, its
   connection-local lock and its one close code".** With corrections 2 and 3 landed, "its" invites
   the adapter reading the spec no longer makes anywhere else. The cell states no ownership
   location, so it is not false; it wants one word if a later pass touches the table.
5. **Why the last-validated timestamp lives on the ASGI `scope` rather than beside the lock and
   flag on the consumer instance is stated nowhere** — not in the spec, not in the rationale, not
   in `consumers.py` (whose comment explains only the key's collision-safe namespacing). It is
   reachable either way from the consumer the shared function is handed. Correction 3 records the
   *fact* and deliberately invents no reason; the reason is a real gap and belongs to whoever
   decided it.
6. **The spec nowhere states how the outbound gate reaches the consumer's lock.** `ws_consumer`
   (adapter) and `handler.view` (admission) are the two hops. Decision 16 asserts the lock is
   connection-local and the gate is on the adapter without naming the link between them, so a
   reader cannot derive the reachability from the spec alone. An omission, not a divergence.
7. **Two residual history-narrating phrases in the spec.** Decision 7's outcome 3 ends "This is
   the only new refusal, and it is a refusal rather than a `500`", and Decision 9's
   `_patched_body` paragraph says "previously a Channels-routed deployment never reached that
   adapter at all". Both plausibly describe the *shipped 0.0.14 behavior* rather than a spec
   revision, which is legitimate; both read as changelog voice on a cold read. Worth a ruling, not
   a silent edit. **Ruling recommendation (source: `docs/builder/bld-review-3-integration.md`,
   `### On the alleged internal contradiction`):** Worker 3 refuted this as a defect — both phrases
   describe shipped `0.0.14` behavior, a reader applying no chronology reads both correctly — and
   recommends closing this item as **no-change**. Recorded, not enacted: no spec edit made.
8. **The DRY `parse_json` bullet attributes `_validate_upstream_shape` to "the upstream-mounted
   path".** That gate decides whether the patch installs at all, for every mount, so pairing it
   with the genuinely path-scoped `UnicodeDecodeError` translation under one prepositional phrase
   is loose. Not the same false scoping as correction 8 (it makes no "only mount" claim), so it
   was left.
9. **Pattern, not a defect: the shipped doc was more accurate than the spec on corrections 8 and
   9.** `_strawberry_patches.py`'s docstring already said "What the gate does NOT scope is the
   **mount**", and `docs/README.md` already split `APPEND_SLASH` by `DEBUG`. That is the third and
   fourth instance in this build of the "a downstream doc more accurate than the spec means the
   contract moved" tell, and it found two of these nine before an auditor did. It is now worth
   treating as a first-class search: diff every consumer-facing or docstring telling of a contract
   against the spec's, and read a disagreement as the spec being stale by default.
10. **The rationale's Decision 19 historical block still contains "only a factory".** Left on
    purpose — it is introduced as the prior spec wording. Recorded so a future grep for the phrase
    does not read it as a missed site.

## Notes for the maintainer

- Nothing in this pass changed a contract; all nine were prose reconciled to code that already
  shipped. **One was in the unsafe direction** (correction 8): the spec told consumers that
  disabling the Strawberry patch could not affect a package mount, and it turns a controlled
  `400` into an unhandled `500` there. The code and its tests were already right.
- The rejected alternative worth naming: correction 8 could have been "fixed" by rewiring
  `_RequestBodyBoundaryMixin.parse_json` to call `_original_parse_json` instead of `super()`,
  which would have made the old sentence true and made the envelope guard ungated. Rejected on
  the merits, not only on scope — the guard is a workaround for upstream defect #3398 and
  *should* stay opt-out-able, which is Decision 9's own lifecycle rule read in the other
  direction. Recorded in the rationale.
