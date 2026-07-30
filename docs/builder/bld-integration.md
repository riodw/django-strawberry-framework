# Build: cross-slice integration pass — card 065 (transport_security / 0.0.15)

Spec reference: `docs/spec-065-transport_security-0_0_15.md` (whole file; the direct input is
`## Helper-reuse obligations (DRY)` at `:2192`, and Decisions 7-11 and 16-19)
Status: final-accepted

## Plan (Worker 1)

This is the cross-slice integration pass required by `BUILD.md` `## Cross-slice integration
pass`. All five spec slices and both maintainer review rounds are `final-accepted`. The pass
inherits a six-item scope from `bld-slice-5-docs_foldin.md` `### What the cross-slice
integration pass must own`, and it looks beyond that list for what no single slice could see.

**Nothing in this artifact was accepted on a prior pass's prose.** Every inherited item was
re-measured against the tree, and two of the six came back with a *larger* scope than the
routing record gave them. That is this pass's own recurring lesson, recorded again below.

### Required reading, discharged

- `AGENTS.md`, `START.md`, `GOAL.md`, `docs/GLOSSARY.md`, `CHANGELOG.md` (untouched — the
  version quintet is the joint cut's, spec Decision 15).
- `docs/builder/BUILD.md`, `docs/builder/ARTIFACT.md`, `docs/builder/worker-1.md`.
- `docs/spec-065-transport_security-0_0_15.md` and its rationale companion (both owned here).
- `docs/builder/build-065-transport_security-0_0_15.md`, `## Open maintainer decisions`
  included — **M4** and **M5** are the maintainer's and are not re-litigated here.
- Every closed artifact, in order: `bld-slice-1-protocol_split.md`,
  `bld-slice-2-body_cap.md`, `bld-slice-3-utf8_wire.md`, `bld-slice-4-ws_revalidation.md`,
  `bld-review-1-http_boundary.md`, `bld-review-1-ws_boundary.md`,
  `bld-review-1-w3_review.md`, `bld-review-2-ws_revocation.md`,
  `bld-review-2-http_boundary.md`, `bld-review-2-ws_host_boundary.md`,
  `bld-review-2-w3_review.md`, `bld-review-2-w3_residual.md`,
  `bld-slice-5-docs_foldin.md`.
- `docs/builder/worker-memory/worker-1.md`, read first and consolidated before appending.

**Spec status-line re-verification** (mandatory per `worker-1.md`): spec `:3` reads
`DONE-065-0.0.15`, `:36-42` reads `**BUILT — all five slices …**` with the joint-cut caveat.
Both are still true at the integration pass and neither was edited. No predecessor doc
reference is dangling.

**No subagent was dispatched.** My predecessor's background sweep returned nothing and it is
recorded there as contributing nothing; the reading below is this pass's own.

### Static inspection coverage (`BUILD.md` step 2)

Enumerated the build's own Python surface mechanically rather than from the artifacts:
`{ git diff --name-only 537e4951~1 HEAD; git diff --name-only HEAD; } | sort -u | grep '\.py$'`
returns 26 files. Two are the concurrent row-preserving work swept into `537e4951`
(`django_strawberry_framework/filters/sets.py`, `tests/filters/test_sets.py`) and one is the
kanban tracked-path sync (`examples/fakeshop/apps/kanban/constants.py`) — none of the three is
this build's.

`scripts/review_inspect.py … --output-dir docs/shadow` was run in this pass over every
remaining file with review-worthy logic. Coverage is now complete for the twelve package
files the build touched (`views.py`, `_request_body.py`, `consumers.py`, `routers.py`,
`conf.py`, `exceptions.py`, `_strawberry_patches.py`, `_cross_web_patches.py`,
`utils/sessions.py`, `utils/__init__.py`, `auth/sessions.py`, `auth/mutations.py`) plus
`tests/test_views.py`, `tests/test_routers.py`, `tests/test_strawberry_patches.py`,
`tests/test_cross_web_patches.py`, `examples/fakeshop/test_query/test_transport_api.py` and
`examples/fakeshop/config/urls.py`. **Skipped with reason:** `scripts/prove_failability.py`
and `tests/test_prove_failability.py` — `scripts/` sits outside the coverage gate and the
runner is a standalone tool with no package surface, so it is not part of the card's
integration seam; `tests/auth/test_mutations.py`, `tests/base/test_conf.py` and
`examples/fakeshop/test_query/test_products_api.py` carry re-pinned assertions only, no logic.

### Cross-file repeated-literal comparison (`BUILD.md` step 3)

**Production: every one of the named literals is single-sited in executable code.** Measured
per literal with the `--include='*.py'` grep, then read at each hit to separate executable
code from docstrings and `#:` comments:

| literal | executable sites | verdict |
|---|---|---|
| `1_048_576` | `conf.py:470` only (`:122` / `:462` are prose) | single-sited |
| `4403` / `"Forbidden"` | `consumers.py:197-198` only (`:54` / `:186` are prose) | single-sited |
| `r"^graphql/?$"` | `routers.py:424` (the kwarg default) only; `:373` is prose | single-sited |
| `413` | `views.py:515` / `:519`, both carrying `_BODY_LIMIT_REASON` | one reason constant |
| `400` | every raise carries `_JSON_PARSE_REASON` or upstream's own constant | one reason constant |
| `"Request body exceeded the configured GraphQL request-body limit."` | `views.py:100` | single-sited |
| the composition sentence | one telling per surface, all agreeing (see below) | consistent |

Test-tier restatements (`tests/test_routers.py:139-140`'s `_REVOKED_CLOSE_CODE` /
`_REVOKED_CLOSE_REASON`, `tests/test_views.py:295`, `tests/base/test_conf.py:397`,
`test_transport_api.py:1367` / `:1409`) are **independent pins and correct as they are** — a
test that imports the production constant asserts nothing about its value. The round-2
residual review recorded the two cohorts independently arriving at that same discipline; this
pass confirms it holds across all three trees.

The `SERVER_NAME` / `SERVER_PORT` pair in `consumers.py` is the one intra-file repeat in the
package and is **NOT** consolidated: it mirrors Django's own if/else and the audited contract,
and two reviewers have affirmed it. Not re-opened.

Cross-file repeated literals across the six **doc** surfaces were grep-verified clean by the
Slice 5 review (`client_max_body_size` at exactly one site; `README.md` / `TODAY.md`
prose-only). Cited rather than re-derived, per the routing record's item 6.

**One repeated literal the shadow report surfaced that no slice could have seen — see
`### Finding L-A` below.** `exceptions.py` now carries three spellings of one "cannot render
this value" placeholder, and this build added the third.

### Import-direction comparison (`BUILD.md` step 4)

One-way throughout, no cycle, no sibling reaching outside its documented boundary:

- `routers.py` → `consumers.py` (four symbols) → `utils/sessions.py`; `consumers.py` imports
  nothing from `routers.py`.
- `views.py` → `_request_body.py`, `conf.py`, `exceptions.py`. `_request_body.py` imports only
  the standard library, `HttpRequest` under `TYPE_CHECKING`, and the package logger — it
  reaches for no policy, which is the `## Helper-reuse obligations (DRY)` bullet that says so.
- `utils/sessions.py` imports two Django symbols and nothing from the package, which is what
  lets `auth/sessions.py` and `consumers.py` both import it without dragging the other in.
- The three deferred imports (`channels.auth` and the session-store resolver inside the
  revalidation coroutine, `channels.security.websocket` inside the denial arm) are the
  documented soft-dependency shape, not a boundary violation.

### Staged-anchor sweep (`BUILD.md` step 6)

`grep -rEn 'TODO\(spec-065|TODO-(ALPHA|BETA|STABLE)-065'` over the tree, excluding
`KANBAN.*` / `BACKLOG.md`: **zero anchors in shipped source, tests, or standing docs.** The
only hits are the spec's own line `:2188` describing the convention generically and the
per-cycle `bld-*.md` narrative of Slice 1's anchor and Slice 2's removal of it. Nothing to
discharge.

---

## Verdict on each of the six inherited items

### 1 — BINDING (DRY): `_user_who_can_add_categories()` — CONFIRMED, 2 sites, unchanged

Re-measured, not inherited: `src.count(block) == 2` for the exact seven-line block, at
`examples/fakeshop/test_query/test_transport_api.py:807-814` and `:1266-1273`. Slices 3-5 and
both review rounds added **no third site** (`test_products_api.py`'s row correctly reused that
module's own `_login_with_perm`). Scope is exactly as routed. Dispatched below.

### 2 — BINDING (DRY): the inline `await ….post(...)` blocks — CONFIRMED, but **8** sites, not 6

`re.compile(r'await \w+\(?\)?\.post\(')` over the current file matches **8** times, at `:959`,
`:995`, `:1000`, `:1005`, `:1439`, `:1444`, `:1554`, `:1559`, across **four** async rows. The
routing record says six across three rows; that count was measured mid-Slice-3 and the
patch-opted-out async row is the fourth. **The dispatch must say eight**, or two blocks close
by omission — this is the third time in this build that an escalation named fewer sites than
exist, and it is the reason the item is re-measured rather than copied.

`_post_bytes(client, raw, path=…, **extra)` needs no change to serve them: `AsyncClient.post`
returns an awaitable, so `await _post_bytes(client, raw, path="/async-graphql/")` is the
whole rewiring. **Precedent inside the same file:** `_post_multipart` already serves both
transports off one body (`client.generic`), and says so in its own docstring — "Sync callers
get a response, async callers get an awaitable". Dispatched below.

### 3 — M1: `routers.py`'s public constructor docstring — CONFIRMED, and **larger** than routed

Independently verified, read-only, both sides:

```shell
grep -n "revalidates the session" django_strawberry_framework/routers.py         # -> 405
git show HEAD:django_strawberry_framework/routers.py | grep -n "rejects the operation"  # -> 406
git diff HEAD --stat -- django_strawberry_framework/routers.py                   # -> empty
```

Byte-identical at `HEAD`, so **pre-existing at `HEAD`** and not a slice regression, exactly as
routed. The false clauses stand at `routers.py:404-407`.

**The routing record's constraint does not survive measurement.** It says "the two sentences
that follow, about `websocket_revalidation_window`, are true and must survive." The first half
is false: those sentences carry the *same* pre-round-2 single-checkpoint framing as the clauses
M1 names.

| `routers.py:409-411` says | the code says | verdict |
|---|---|---|
| "`0.0` (the default) revalidates every operation" | `consumers.py:81-83`: "`0.0` (the default) therefore revalidates at every operation admission **and every `next` / `data` / operation-scoped `error` frame**" | understates |
| "one session read per authenticated **operation**" | `consumers.py:269`: "one session read per authenticated **checkpoint**" | wrong word |

`docs/GLOSSARY.md:1846` states the correct form ("The number means the same thing at **both**
of the package consumer's security checkpoints"), so `routers.py` is the **only** surviving
drifted telling of the window's cost — and the whole paragraph `:404-411` is one drifted
telling, not two clauses inside a true one.

**Ruling.** The routing record's *purpose* — do not delete the window documentation, the
correction is not licence to rewrite the constructor's whole docstring — is honoured. Its
factual claim is corrected here rather than carried forward. The fix therefore spans
`:404-411`: two clauses replaced (the checkpoint count and the rejection scope) and two words
corrected (`operation` → `checkpoint`, and the `0.0` sentence naming both checkpoints).
`0.0.14`'s released docstring is not a compatibility surface, so nothing is preserved for
compatibility.

Severity stays **Medium and not Low**: a false claim about security behavior on a **public**
constructor docstring, which a consumer reads while choosing `websocket_revalidation_window=`.
A consumer reading it believes their socket survives revocation.

### 4 — L3: the four remaining multipart surfaces — CONFIRMED, all four, individually

Each read at its site this pass:

1. `docs/README.md:360` — "For a `multipart/form-data` request the bound is the declared
   `Content-Length` plus Django's own `MultiPartParser`, and nothing else." Unscoped. (The
   paragraph's *third* sentence does say "on a multipart POST", so the paragraph is
   self-inconsistent as well as wrong in its lead sentence.) **Actionable by this pass.**
2. `docs/GLOSSARY.md:1482`, `## Request-body cap` — "**`multipart/form-data` is a carve-out**:
   its bound is the declared `Content-Length` plus Django's own `MultiPartParser` and nothing
   else". **DB-backed**: `GlossaryTerm.body`, anchor `request-body-cap`. Fix in the DB, then
   `scripts/build_glossary_md.py`. Never as text — a hand-edit is reverted by the next render.
3. `django_strawberry_framework/conf.py:117` `#"EXCEPT for a multipart request"` — source,
   **and the maintainer's concurrent dirty file. Never edited, never reverted here.** Routed
   as a maintainer item below.
4. `django_strawberry_framework/views.py:407` `#"**Multipart.** Bounded by the declared-size
   gate"` — source, a cap-contract docstring paragraph. Actionable by this pass (`views.py` is
   dirty with Slice 5's own authorized docstring work, not the maintainer's).

**The one clause for all four**, reused rather than re-invented, lifted from
`views.py::_is_multipart_form_post`'s own docstring so no fifth phrasing appears:

> on a multipart **POST** — the carve-out is POST-scoped, and a multipart content type on any
> other method is counted like any other body, which is the stricter direction.

Spec Decision 8 and Decision 17 already state the scope (Slice 5's edits 4-5); the spec side
needs nothing further.

### 5 — L1: `GlossaryTerm` id 529 — CONFIRMED, one character

`grep -n "scope,\." docs/GLOSSARY.md` prints `327`, inside `## Channels request adapter`:
"…to split a Channels HTTP scope from a WebSocket scope**,.** Since spec-065…". Anchor
`channels-request-adapter`, column `body`. **This pass opens the glossary DB anyway** (for L3
surface 2), so per the routing record's own condition L1 travels with it here rather than to
the joint cut. `title` and `anchor` stay untouched.

### 6 — cross-file repeated literals — cited, not re-derived

Recorded under `### Cross-file repeated-literal comparison` above.

---

## What this pass found beyond the inherited list

### Finding S-1 (Medium, spec — **closed in this pass**): the DRY obligations section was never re-verified after two review rounds

`BUILD.md` asks this pass to "verify each obligation was actually honoured by the shipped code,
not merely asserted." Walked all fifteen bullets of `## Helper-reuse obligations (DRY)` against
source. **Twelve hold verbatim.** Three were wrong, all in the same direction and for the same
reason: the section was written before the rounds and no round revisited it.

1. **"Two overridden hooks" is four, and two of them are not on the mixin.** The shipped view
   overrides `as_view` (`views.py:462`, on the mixin), `parse_json` (`:590`, on the mixin),
   `run` (`:817` / `:868`, on each concrete view) and `parse_multipart` (`:829` / `:879`, on
   each concrete view), and substitutes `request_adapter_class` besides. The obligation claimed
   `run` and `parse_json` were the two overrides and that **both** sat on
   `_RequestBodyBoundaryMixin` "so the sync and async colours cannot diverge."
2. **The adjacent bullet already contradicted it.** The multipart obligation says both
   `parse_multipart` overrides are delegates "in the same shape the two `run` overrides already
   take" — i.e. per-view. Two adjacent bullets disagreed about where the hooks live, which is
   the half-reconciled state `worker-1.md` names as worse than an un-updated one.
3. **"No local `getattr(settings, ...)`" reads as covering every settings read**, and
   `views.py:267` reads `settings.DEFAULT_CHARSET` directly — which Decision 17 *requires*,
   because the check must reproduce the exact `encoding or settings.DEFAULT_CHARSET` pair
   `MultiPartParser.__init__` resolves.

**Fixed in the spec this pass** (see `### Spec changes made (Worker 1 only)`). Item 3 is
prophylactic and worth saying why: unscoped, it would be read as a violation by the next
reviewer to sweep the section, and a false finding argued against correct code costs more than
the clause does.

### Finding S-2 (Medium, spec — **closed in this pass**): Decision 11 priced the window per operation, contradicting its own opening

The same drift M1 found in `routers.py`, one surface further: spec `:1474` says the window
"means the same thing at both checkpoints" and `:1483` prices it "per authorized **event**",
while `:1504` — the astronomical-window paragraph — still priced it "one session read per
authenticated **operation**". A decision contradicting itself about its own cost model, twenty
lines apart, with the code (`consumers.py:269`, "per authenticated checkpoint") already right.

**So the drifted window telling had two surfaces, not one.** M1 named the docstring; nothing
named the spec. Fixed here; `routers.py` is dispatched below.

### Finding L-A (Low, source): this build added a third spelling of one "cannot render" placeholder

The shadow report for `exceptions.py` shows `2x <unprintable`. Attributed rather than assumed:
`git show 537e4951~1:django_strawberry_framework/exceptions.py | grep -c unprintable` is **2**
and the current file is **3**, and the build's diff on that file is `+41 lines` — i.e.
`describe_value`. So the two `<unprintable {T}>` renderings at `:33` and `:109` pre-date the
build and **this build added the third**, in a different shape: `an unprintable {T}` at `:74`.

**Not a consolidation.** The shapes serve different grammatical positions — `describe_value`
renders a fragment interpolated into prose ("got an unprintable Foo."), the other two are
standalone renderings — so collapsing them would produce one of them reading wrongly. The
defect is that **nothing at any of the three sites says so**, which is precisely how a future
reviewer either re-raises it or "fixes" it in the wrong direction. Dispatched as one comment
line at `describe_value`'s site, under this pass's own standing rule that a rule binding a
future writer belongs at the site.

### Finding L-B (Low, tests — recorded, deliberately NOT dispatched): the package-tier patch-opt-out helper does not assert the simulation is honest

`tests/test_views.py:1320::_strawberry_patch_opted_out` and
`test_transport_api.py:1477::_strawberry_patch_opted_out` are near-copies with two deliberate
deltas. One of them is a **strengthening the package-tier copy lacks**: the live copy asserts
`strawberry_patches._patch_is_installed() is False` inside the simulation, so a simulation that
silently stopped un-installing the patch would fail a row. The package-tier copy asserts
nothing about that, and its whole value rests on the simulation being honest.

Recorded, not dispatched: `tests/test_views.py` is in no other item's scope, and opening a
second test file for one assertion is the scope creep that turns a consolidation pass into a
slice. Routed to `bld-final.md`'s `### Deferred work catalog`.

### Ruling — L9: the fail-closed reporting inconsistency. It should be resolved, and the direction is now determined by evidence rather than preference

Measured, because the round-2 table is stale: it recorded "one logs, two silent", and the
current tree is **two log, one silent**. `_request_body.py:230` logs `warning` (the corrupted
probe), `consumers.py:465` logs `exception` (the revalidation read failed), and the `Host`
denial at `consumers.py:787` logs **nothing**. The `Host` third was declined in-build and
routed to the maintainer as amendment A4, on the ground that Decision 19 fixes wire
indistinguishability and says nothing about server-side observability.

**Is the asymmetry deliberate and defensible?** There is a real categorical argument for it:
the two that log are the package's own machinery *failing* (a probe that could not measure, a
session read that raised), while a `Host` denial is the boundary *working*. Logging an
anomaly and logging a policy decision are different things.

**That argument does not survive the card's own thesis, and this is the part no cohort could
see.** Card 065's thesis is that Django owns the Host decision. Django's ownership of that
decision *includes* reporting it: `django/core/handlers/exception.py::response_for_exception`
routes every `SuspiciousOperation` — `DisallowedHost` included — to a
`django.security.DisallowedHost` logger at `error` level, and Django's default `LOGGING`
config wires `django.security`. (Read at the version the shared `.venv` carries — **Django
6.0.5**, per `uv pip list`; I did not confirm it at the 5.2.0 floor, and whichever pass
implements this owns that confirmation. Reading a newer version's source is not floor
verification.) So a project that already monitors `django.security.DisallowedHost` sees HTTP
host attacks and silently drops WebSocket ones — the package took over a Django decision and
kept only half of Django's behavior. The WS-host cohort could not have seen this: its subject
was the handshake, and the baseline it diverges from lives in Django's HTTP path.

**Ruling: the inconsistency should be resolved, in the direction the round-2 reviewer and the
WS-host builder both already recommended (log all three, no wire change) — but it is the
maintainer's call, not this pass's, and NOT Worker 2's.** It adds an observability surface to
a fixed design, which `BUILD.md` `### Contract-level findings are escalated as maintainer
decisions` puts outside a worker's authority. It stays routed as A4, with this evidence
attached so the decision is made against Django's actual behavior rather than against a
preference. Recorded for `bld-final.md`'s `### Deferred work catalog`.

### Sweep: a contract told in more than one place

M1 is one instance of a general defect, so every multi-told contract in the card was walked
telling by telling. **Three of the four are consistent; the fourth is M1 plus S-2.**

- **The revocation contract — five tellings, one drifted.** `consumers.py:15-22` / `:52-58`
  (two checkpoints, connection-scoped, the close *is* the rejection),
  `docs/GLOSSARY.md:374-378`, `docs/README.md`, `README.md:62`, `TODAY.md:384` all agree.
  `routers.py:404-411` is the drifted one, and `grep -rn "before every operation"` over the
  tree confirms it is the **only** surviving occurrence outside per-cycle `bld-*.md`
  narrative. M1 + S-2 close it.
- **The Host boundary — six tellings, all agreeing.** `consumers.py:154-162` (two separate
  checks, in that order, only `DisallowedHost` normalized), the code comment at
  `routers.py:449-456` ("Host OUTSIDE Origin"), the composition itself at `routers.py:457-470`
  (`DjangoWebSocketHostValidator(AllowedHostsOriginValidator(AuthMiddlewareStack(URLRouter(…)))`),
  `routers.py:380-389`, `docs/GLOSSARY.md:1834-1836`, `docs/README.md`, `README.md:62` and
  `TODAY.md:384`. Composition order, the three-wrapper count, `get_host()` ownership,
  `USE_X_FORWARDED_HOST`, "no new setting", and privacy of the validator agree everywhere.
- **The body cap — eight tellings; the only disagreement is L3.** The `1_048_576` default, the
  `413` + `text/plain` + no-envelope shape, "received bytes never `Content-Length`", "never
  `len(request.body)`", the `413`-vs-`400` discrimination, and the `None`-in-the-setting versus
  `None`-as-the-keyword split are consistent across `conf.py`, `views.py`, `_request_body.py`,
  `docs/README.md`, `docs/GLOSSARY.md:1480-1484`, spec Decisions 7-8, `README.md`, `TODAY.md`.
  The multipart carve-out's POST scope is the one divergence, and it is L3.
- **The UTF-8 wire contract — six tellings, all agreeing, including the one most likely to
  have drifted.** This is the contract whose spec statement was a *fallback chain* until the
  round-2 custodian pass rewrote it conjunctively, so every downstream telling was written
  from the wrong shape. All of them are now right: `views.py:210-268` implements two
  independent conditions joined with `and` and says explicitly "deliberately not a fallback
  chain"; `docs/GLOSSARY.md:1808` says "two independent conditions joined with `and`, never a
  fallback chain" and puts the `U+FFFD` marker check "separately"; `docs/README.md`'s
  **Multipart control documents.** paragraph gives the same two-then-separately structure.
  Decision 17's "three independent requirements" reconciles exactly: two encoding conditions
  in `_form_encoding_is_utf8` plus the marker condition in
  `_reject_lossy_multipart_control_fields`. **Also confirmed landed:** the round-1 open nit on
  `_form_encoding_is_utf8`'s docstring numbering its conditions in reverse of evaluation order
  — the docstring now says "numbered in the order the body below evaluates them" and condition
  1 is the declared charset, which the body checks first. And the false claim in
  `tests/test_views.py`'s M6 row docstring is gone (`grep "would still pass"` → no hit). Both
  prose corrections the build plan routed into Slice 5 are discharged.

### Sweep: duplicated or near-duplicated logic across the modules the slices touched

Four builder cohorts wrote in parallel under an ownership partition, which licenses parallel
writes and does nothing about parallel duplication. Read the symbol inventory of `views.py`,
`_request_body.py`, `consumers.py`, `routers.py` and `utils/sessions.py` against each other.

**No duplicated logic across the five modules.** Every function is distinct in subject; no
module reimplements another's decision. The three convergence points are all single-sited by
construction: `describe_value` (five raise sites in three modules, one owner),
`session_store_class` (two importers, one `SESSION_ENGINE` expression, hosted outside the
opt-in `auth` package so neither caller drags the other in), and `_DEFAULT_REVALIDATION_WINDOW`
(spelled once in `consumers.py:179-181`, imported by `routers.py` for the kwarg default —
verified, and `docs/GLOSSARY.md:1846` states that property).

**Verified-and-rejected, with the reason recorded so it is not re-raised:**

- **`"Unable to parse request body as JSON"` is defined twice in production** —
  `views.py:114::_JSON_PARSE_REASON` and
  `_strawberry_patches.py:337::_UPSTREAM_JSON_PARSE_REASON`. This looks like the clearest DRY
  finding in the package and is the correct shape. Both sites already carry the reason in
  full: the value is *upstream's own* literal, byte-identity with upstream is the contract
  (one byte sequence, one interpretation at every hop, `__cause__` the only discriminator),
  and importing one from the other would make `apps.py::ready` load `views.py` and
  `strawberry.django.views` at every consumer's startup — channels-only ones included — and
  cost the patch module the import-time independence that lets it report an unsupported shape
  when a dependency is missing. `tests/test_views.py` pins **both** against what upstream
  actually raises, so a message change on either side fails loudly. The spec's DRY section
  states this deliberate double-naming explicitly. Correct as it stands.
- **The sync/async colour pairs.** `views.py`'s `_run_after_csrf_check` /
  `_async_run_after_csrf_check` bodies are, with docstrings stripped by AST,
  `return delegate(request, *args, **kwargs)` and
  `return await delegate(request, *args, **kwargs)` — a one-token difference, and the second
  function exists only because `csrf_protect` decides whether to await by inspecting the
  callable it wraps. The `run` and `parse_multipart` pairs are the same split, for upstream's
  own reason. Slice 2's DRY-2 verified this against upstream's `dispatch` pair; re-confirmed.
  Irreducible without a `super()`-dispatch trampoline less readable than the duplication.

### Sweep: duplicated logic across the test files, and a class-level ruling

Cross-file helper-name collisions across the three trees, computed by AST rather than grep:
`_capped_view`, `_strawberry_patch_opted_out`, `_MULTIPART_BOUNDARY`, `SCHEMA`, `class Query`.
Read all five.

**One ruling covers the whole class, so the next reviewer does not re-raise it per helper.**
Three of the five are genuine cross-tree near-copies —
`_capped_view`, `_strawberry_patch_opted_out`, and
`tests/test_views.py:1612::_multipart_body` versus
`test_transport_api.py:584::_multipart_bytes` (the former is a strict special case of the
latter, and the `f"multipart/form-data; boundary={…}"` line is character-identical between
`tests/test_views.py:1657` and `test_transport_api.py:577`). **No shared home exists, and
creating one is the wrong trade.** Mechanically, not by preference:

- `examples/fakeshop/test_query/` has **no `__init__.py`** — verified — so it is not a package
  and `from test_query.x import y` does not resolve. Adding one would change how pytest
  collects a tree that carries a live order-dependent schema-registry pollution hazard.
- `pytest.ini` sets `pythonpath = examples/fakeshop`, so the only cross-tree import direction
  that exists is `tests/` → `apps.*` — used by 19 files, and it points at example **domain**
  code (models, services), never at test helpers. The reverse direction does not exist at all.
- The subjects also differ by tier: `_strawberry_patch_opted_out` reaches into
  `BaseView.__dict__` and `_strawberry_patches._original_parse_json`, i.e. package internals.
  Hosting that in the example project would invert the dependency; hosting it in
  `django_strawberry_framework.testing` would grow the **public** surface for a test
  convenience, which the spec's definition of done forbids.

`_MULTIPART_BOUNDARY` is a name collision with **different values** (`"BoUnDaRy"` versus
`"BoUnDaRyFoRtHeWiReRoWs"`) — not a repeated literal. `SCHEMA` / `class Query` in
`tests/test_views.py` and `tests/test_routers.py` are two **different** schemas that overlap in
one three-line `ping` field; the router file's adds four probe fields and a `Subscription`.
Sharing three lines of fixture would couple a minimal HTTP-view schema to a full WebSocket
probe schema, and per-file schema locality is the mitigation for the registry-pollution
hazard, not a defect. All verified-and-rejected.

The two items that **are** live test duplication — inherited items 1 and 2 — are dispatched.

---

### DRY analysis

**Helper inventory checked.** Refreshed for the **whole package**, not just `utils/`:
`docs/shadow/helper-inventory.md` plus `scripts/review_inspect.py` Symbols sections for all
twelve touched package modules and the three test files. Shapes searched: `post`, `client`,
`multipart`, `boundary`, `perm`, `user`, `revalidat`, `checkpoint`, `unprintable`, `describe`,
`reason`, `parse`, `charset`, `encoding`, `session_store`, `logger`. Candidates found and
their disposition: `_post_bytes` (**reuse** — serves inherited item 2 unchanged),
`_post_multipart` (**precedent** for the one-helper-both-transports shape),
`_login_with_perm` in `test_products_api.py` (**not reusable** — different tree, and the
transport file's actor needs the refreshed-perm-cache step), `describe_value` /
`session_store_class` / `_DEFAULT_REVALIDATION_WINDOW` (already single-sited, no change).

**Existing patterns reused.** `examples/fakeshop/test_query/test_transport_api.py:377-379`
(`_post_bytes`) serves all eight async sites with no signature change; `:612-652`
(`_post_multipart`) is the in-file precedent that one helper legitimately serves both
transports, and its docstring already says so. `views.py:270-290`
(`_is_multipart_form_post`'s docstring) supplies L3's clause verbatim, so no fifth phrasing
enters the tree.

**New helpers justified.** Exactly one: a module-local
`_user_who_can_add_categories()` in `test_transport_api.py`, whose single responsibility is
"return a `view_category_1` user holding `add_category`, with the per-request permission cache
dropped". Two call sites. Not an abstraction — the most readable reusable shape, and the
file's own idiom (`_post`, `_sized_body`, `_assert_no_graphql_envelope`). **No new production
helper, no new constant, no new test-tier constant.**

**Duplication risk avoided.** Three, each pre-decided so Worker 2 cannot introduce a second
copy: (a) L3's four surfaces take **one** clause, quoted below, not four paraphrases — the
whole point of the finding is that four independent re-phrasings is how the scope was lost the
first time; (b) the async rewiring adds **no** `_async_post_bytes` twin — `_post_bytes` is
awaited directly, since introducing a twin would recreate the sync/async pair the file has
already proved unnecessary for `_post_multipart`; (c) `_user_who_can_add_categories()` is
module-local to the live tier and is **not** mirrored into `tests/` or into
`test_products_api.py`, which has its own helper.

### Boundary count, and the split question answered

**Zero new boundaries.** The consolidation introduces no guard, cap, gate, rejection path, or
validation branch: it is one test helper extraction, one test-call rewiring, four prose
corrections, and two DB text fixes. No failability proof is owed, and `### Failability proofs`
will read the required literal. No split: one cohort, one artifact, and the six items share a
single reviewable diff.

### Fail-open shape review at plan time

Nothing planned here can introduce a catalogued fail-open shape — no clamp, no `getattr`
default, no `or` fallback, no bare `except`, no truthiness test on a possibly-absent value —
because nothing planned here adds an executable decision. The one executable change is
`await _post_bytes(...)` replacing an inline `await client.post(...)` with the identical
arguments.

### Hot-path declaration

**None.** No production executable line changes: the only source edits are docstring and
comment text (`routers.py`, `views.py`, `exceptions.py`). The two conditions that would
falsify this are stated so Worker 2 and Worker 3 can check them rather than agree with them:
(a) no statement inside any function body is added, removed, or reordered, and (b) no
per-request, per-resolver, per-connection or per-outbound-message code path is touched. If
either turns out false, record it under `### Notes for Worker 1 (spec reconciliation)` rather
than declaring a number retroactively.

The build-wide **M5** escalation (the WS-revocation lock's per-outbound-message cost) is the
maintainer's open item and is untouched here.

### Floor-verification scope

**Required, one focused scope, owner named.** The consolidation changes how four async rows
drive Django's `AsyncClient` — a request/response and ASGI-plumbing seam, which is inside
`BUILD.md` `## Floor verification`'s "when it is required" list even though no production
behavior changes. The keyword shape `_post_bytes` uses (`client.post(path, data=…,
content_type=…)`) is a public Django test-client signature, and a signature difference at the
floor is precisely the class a shared-`.venv` green run cannot see.

- **Scope:** `examples/fakeshop/test_query/test_transport_api.py`, focused, `--no-cov`.
- **Owner: the consolidation pass's Worker 2**, in its `### Floor verification` subsection.
  Not the final gate — the gate is the backstop that confirms it happened.
- **Procedure:** `BUILD.md` `### How to build the floor venv`, in a scratch venv outside the
  repo, with the resolved versions read by `uv pip list --python <venv>/bin/python` and
  recorded. **Never install into the shared `.venv`.**

For the record, and read rather than recalled: the shared `.venv` currently carries **Django
6.0.5, channels 4.3.2, strawberry-graphql 0.316.0** (`uv pip list`), which is why it is not
the floor. The floor is Django 5.2.0 on Python 3.10 with strawberry-graphql 0.316.0.

One floor question is deliberately **not** answered here: whether Django 5.2.0's
`response_for_exception` logs `DisallowedHost` the way 6.0.5's does (the L9 ruling). It belongs
to whichever pass implements the L9 decision, and that decision is the maintainer's.

### Implementation steps

Line numbers are pin-at-write-time navigational hints; verify against the current source
before editing.

1. **`examples/fakeshop/test_query/test_transport_api.py` — extract
   `_user_who_can_add_categories()`.** Add it beside the other module-local helpers (after
   `_post`/`_sized_body`, before `_assert_body_limit_response`, or anywhere in that block —
   placement is Worker 2's). Body is the existing seven-line block verbatim, ending
   `return user`; keep the `# drop the stale per-request perm cache` comment on the refresh
   line, since it is the only thing that explains the second `objects.get`. Move the
   function-local `from django.contrib.auth.models import Permission` into the helper. Then
   replace the block at `:807-814` and `:1266-1273` with `user = _user_who_can_add_categories()`.
   Verify mechanically afterwards: the seven-line block appears **zero** times
   (`src.count(block) == 0`) and `_user_who_can_add_categories` appears three times (one def,
   two calls).
2. **Same file — rewire all EIGHT `await ….post(...)` blocks onto `_post_bytes`.** Sites:
   `:959`, `:995`, `:1000`, `:1005`, `:1439`, `:1444`, `:1554`, `:1559`. Shape:
   `await _post_bytes(client, <the same data expression>, path="<the same path>")` — the
   `content_type="application/json"` argument is `_post_bytes`'s own default and must not be
   restated. The `:959` site constructs its client inline (`await AsyncClient().post(...)`);
   either bind it first or pass `AsyncClient()` as the argument, Worker 2's choice.
   **Do not add an `_async_post_bytes` twin.** Verify afterwards: the
   `await \w+\(?\)?\.post\(` regex matches **zero** times.
3. **`django_strawberry_framework/routers.py:404-411` — correct the whole revocation paragraph
   in `DjangoGraphQLProtocolRouter.__init__`'s docstring** (M1 + the two words S-2's sibling
   drift left there). Four corrections, and nothing else in the docstring is touched:
   - "revalidates the session actor **before every operation**" → the two checkpoints:
     operation admission, and the outbound information-bearing frame. Cite
     `consumers.py::GraphQLWebSocketConsumer` for the detail rather than restating it — the
     module docstring is the canonical telling and this is a pointer, not a sixth copy.
   - "**rejects the operation - not the socket -** when the session is no longer valid" → the
     opposite, which is what happens: the first failed validation at either checkpoint closes
     the whole socket with upstream's own `4403` / `"Forbidden"`, with the pending frame
     suppressed and no preceding operation error — the close *is* the rejection, because the
     actor is connection-scoped.
   - "`0.0` (the default) revalidates every operation" → revalidates at **every checkpoint**:
     every admission and every information-bearing frame.
   - "one session read per authenticated **operation**" → "per authenticated **checkpoint**",
     matching `consumers.py:269` verbatim.
   The rest of the window sentences (the positive-value trade, the injected-consumer
   construction error, the pointer to the maximum-connection-lifetime statement) are **true
   and stay**. Keep the paragraph at roughly its current length: a public constructor
   docstring is not the place to re-narrate Decision 16.
4. **`django_strawberry_framework/views.py:407` — scope the multipart cap paragraph.** Insert
   the one clause into `#"**Multipart.** Bounded by the declared-size gate"`. Use the clause
   quoted under inherited item 4; do not re-phrase it. `views.py` is dirty with Slice 5's own
   authorized docstring work only, so this is an additional authorized docstring edit, not a
   maintainer file.
5. **`django_strawberry_framework/exceptions.py:74` — one comment line at `describe_value`'s
   return** (finding L-A), naming the sibling spelling and why it differs: `describe_value`
   renders a **fragment** interpolated into prose, so it reads `an unprintable {T}`, while
   `_safe_type_name`'s own fallback (`:33`) and `DjangoStrawberryFrameworkError.__str__`'s
   guard (`:109`) render **standalone** and read `<unprintable {T}>`. One line, inside the
   existing docstring or as a `#` comment above the `except` — Worker 2's choice. **Do not
   unify the three spellings.**
6. **`docs/README.md:360` — scope the `**Multipart is a carve-out, not a byte count.**` lead
   sentence** with the same clause. The paragraph's third sentence already says "on a
   multipart POST", so this also removes the paragraph's internal inconsistency. **Nothing
   else in `docs/README.md` changes.**
7. **The glossary DB — two writes, then ONE regenerate.** Via the Django ORM against
   `examples/fakeshop/db.sqlite3`, never raw SQL, never a hand-edit of `docs/GLOSSARY.md`:
   - `GlossaryTerm` anchor `request-body-cap` (`docs/GLOSSARY.md:1482` renders it), column
     `body`: scope the "**`multipart/form-data` is a carve-out**" sentence with the same
     clause.
   - `GlossaryTerm` **id 529**, anchor `channels-request-adapter`, column `body`: delete the
     stray comma so `"…from a WebSocket scope,. Since spec-065…"` reads
     `"…from a WebSocket scope. Since spec-065…"`.
   - `title` and `anchor` stay untouched on both rows. Then
     `uv run python scripts/build_glossary_md.py`.
   - **Concurrent-writer discipline:** the DB is a concurrent-writable tracked binary. Apply
     both writes **on top** of whatever state is there; never reset, never `git checkout` it.
     Verify by **two-consecutive-regenerate byte-stability** plus
     `grep -c "scope,\." docs/GLOSSARY.md` → `0`, not by a clean `git diff`.
   - `status_text` on the seven new entries is **NOT** touched: that is the joint `0.0.15`
     cut's (spec Decision 15), with the exact string already recorded in
     `bld-slice-5-docs_foldin.md`.

**`django_strawberry_framework/conf.py:117` is the fifth multipart surface and is NOT in this
list.** It is the maintainer's concurrent dirty file: never edited, never reverted. Routed as
a maintainer item.

### Files Worker 2 may write — this list is exhaustive

`examples/fakeshop/test_query/test_transport_api.py`, `django_strawberry_framework/routers.py`,
`django_strawberry_framework/views.py`, `django_strawberry_framework/exceptions.py`,
`docs/README.md`, `examples/fakeshop/db.sqlite3` (via the ORM) and the `docs/GLOSSARY.md`
regenerate it produces, `docs/builder/bld-integration.md`,
`docs/builder/worker-memory/worker-2.md`, `docs/builder/temp-tests/`.

**Worker 0 must declare `docs/README.md` into this cohort's ownership before dispatch.** It was
closed as Slice 5's, and the integration pass is the pass its own final verification routed
`:360` to; without the declaration Worker 2 would be writing outside a declared partition.

### Files Worker 2 must NOT touch

`django_strawberry_framework/conf.py`, `auth/mutations.py`, `auth/sessions.py`, `drys.md`,
`vulns.md` — never edited, **never reverted**. `docs/feedback.md`. Every `bld-*.md` but this
one. `docs/builder/build-065-transport_security-0_0_15.md` and every checkbox in it.
`docs/spec-065-*.md` and its rationale (Worker 1's alone). `docs/GLOSSARY.md` as **text** (it
is rendered), `docs/TREE.md`, `KANBAN.md`, `KANBAN.html`. `README.md`, `TODAY.md`,
`examples/fakeshop/test_query/README.md`, `docs/SPECS/spec-041-channels_router-0_0_14.md`.
`CHANGELOG.md`, `pyproject.toml`, `django_strawberry_framework/__init__.py`,
`tests/base/test_init.py`. `consumers.py` — including the `SERVER_NAME` / `SERVER_PORT` pair,
which is affirmed and not consolidated.

### Test additions / updates

**No new test, and no assertion weakened.** Both test edits are refactors that must leave every
existing assertion byte-identical in meaning:

- The two rewired permission sites keep every downstream assertion untouched; the only change
  is where `user` comes from.
- The eight rewired async posts keep their status-code, payload and header assertions exactly
  as they are.
- **Proof obligation instead of new rows:** `uv run pytest
  examples/fakeshop/test_query/test_transport_api.py --no-cov` must report the **same count it
  reports today**. Record the before and after counts in the build report — a count that
  moved means a row was lost or split, which is the one way this refactor can do damage.
- Then the full `uv run pytest --no-cov` at **5202 passed, 40 skipped**, and
  `tests/test_views.py` = 144, `tests/test_routers.py` = 122 (they should not move at all;
  neither file is in scope).
- No temp tests are needed or appropriate.

### Implementation discretion items

Assessed and decided to be Worker 2's: the placement of `_user_who_can_add_categories()`
within the file's helper block; whether the `:959` site binds `AsyncClient()` to a name or
passes it inline; whether finding L-A's note lands inside `describe_value`'s docstring or as a
`#` comment above its `except`; the exact sentence order inside the corrected `routers.py`
paragraph, provided all four corrections land and the surviving window sentences are unchanged.

Not discretionary, and not delegated: the L3 clause's wording (one clause, four surfaces,
quoted above), the decision not to add an `_async_post_bytes` twin, the decision not to unify
the three `unprintable` spellings, and the eight-site count.

### Dispatched findings checklist

- [x] **BINDING (DRY-1)** — extract `_user_who_can_add_categories()` in
      `examples/fakeshop/test_query/test_transport_api.py` and rewire both sites (`:807-814`,
      `:1266-1273`); the seven-line block must appear zero times afterwards.
- [x] **BINDING (DRY-2)** — rewire **all eight** inline `await ….post(...)` blocks (`:959`,
      `:995`, `:1000`, `:1005`, `:1439`, `:1444`, `:1554`, `:1559`) onto `_post_bytes`, with no
      `_async_post_bytes` twin; the `await \w+\(?\)?\.post\(` regex must match zero times.
- [x] **M1 (Medium)** — correct `routers.py:404-411`'s public constructor docstring: two
      checkpoints, the close IS the rejection, `0.0` revalidates at every checkpoint, and one
      session read per authenticated **checkpoint**. The surviving window sentences stay.
- [x] **L3 surface (a)** — `docs/README.md:360`, the multipart carve-out lead sentence, scoped
      with the one quoted clause.
- [x] **L3 surface (b)** — `GlossaryTerm` anchor `request-body-cap`, column `body`, scoped with
      the same clause **in the DB**, then `scripts/build_glossary_md.py`.
- [x] **L3 surface (c)** — `views.py:407`'s `**Multipart.**` cap-contract paragraph, scoped
      with the same clause.
- [x] **L1 (Low)** — `GlossaryTerm` id 529, anchor `channels-request-adapter`, column `body`:
      delete the stray comma in the DB; `grep -c "scope,\." docs/GLOSSARY.md` → `0`.
- [x] **L-A (Low)** — one note at `exceptions.py:74` naming the sibling `<unprintable {T}>`
      spelling and why `describe_value`'s differs. No unification.
- [x] **Floor verification** — focused
      `examples/fakeshop/test_query/test_transport_api.py --no-cov` in an isolated floor venv
      (Django 5.2.0 / Python 3.10 / strawberry-graphql 0.316.0), versions recorded from
      `uv pip list --python`. Owned by this pass, not the gate.

---

## Items routed OUT of this pass

Each is named individually with its owner, because a summary is how one gets dropped.

### To the maintainer

- **L9 — the third fail-closed path (`consumers.py:787`, the `Host` denial) logs nothing**,
  while the other two now log. Contract-level, already routed as amendment A4. The ruling and
  the new evidence — Django's own `django.security.DisallowedHost` `error`-level logging of
  every `SuspiciousOperation`, read at the installed 6.0.5 and unconfirmed at the 5.2.0 floor
  — are recorded above. Recommendation, from two prior passes and this one: log all three, no
  wire change.
- **`conf.py:117` `#"EXCEPT for a multipart request"`** — the fifth L3 surface. Source, and the
  maintainer's concurrent dirty file. The clause is quoted above so it can be applied without
  re-deriving it. **Maintainer-sequenced only; never reverted by a worker.**
- **M4** (whether the weakly-pinned rule applies literally) and **M5** (the build-wide hot-path
  declaration) — open, untouched, not re-litigated.
- **The `AGENTS.md:15`-vs-scoped-`ruff` conflict** — the maintainer's line; six-plus passes have
  raised it. No write-mode `ruff` ran in this pass.

### To `bld-final.md`'s `### Deferred work catalog`

Everything `bld-slice-5-docs_foldin.md` `### For bld-final.md's Deferred work catalog` lists
carries forward unchanged (the seven glossary `status_text` stamps at the joint cut with their
exact string and seven anchors; the terms CSV staying at 37 rows; `definition_of_done` order 5
unticked; **L4**; **L2**; **L5**; the do-not-act scratchpads asserting the old UTF-16
contract), plus this pass's own:

- **L9's remaining third**, as the maintainer item above.
- **L-B** — `tests/test_views.py:1320::_strawberry_patch_opted_out` lacks the live copy's
  `assert strawberry_patches._patch_is_installed() is False`, so nothing pins that the
  package-tier simulation really un-installed the patch. Recorded, deliberately not dispatched.
- **The cross-tree test-helper ruling** (`_capped_view`, `_strawberry_patch_opted_out`,
  `_multipart_body` / `_multipart_bytes`): no shared home exists, creating one is the wrong
  trade, and the mechanical reasons are recorded above so a future reviewer neither re-raises
  it per helper nor "fixes" it by adding an `__init__.py`.
- **`auth/mutations.py`'s repeated literals** (`password` 7x, `register` 4x, `current_user` 3x)
  are **pre-existing** to this card — the build touched only that file's three transport
  strings — and it is a maintainer dirty file. Named so the shadow report's entry is not read
  as this build's residue.

---

## Gates run in this pass

| gate | result |
|---|---|
| `uv run pytest --no-cov` | **5202 passed, 40 skipped** in 61.36s — exactly the declared baseline |
| `uv run pytest tests/test_views.py tests/test_routers.py --no-cov` | **266 passed** (144 + 122, both declared counts) |
| `uv run python scripts/check_spec_glossary.py --spec …spec-065…md` | `OK: 37 terms - all have glossary entries and at least one spec link.` exit 0, **after** the spec edits |
| `uv run python examples/fakeshop/manage.py check` | `System check identified no issues (0 silenced).` |
| `uv run python scripts/build_tree_md.py --check` | `docs/TREE.md is up to date.` exit 0 |
| `uv run python examples/fakeshop/manage.py import_spec_terms --check` | `OK: 46 done cards have glossary links.` exit 0 |
| `uv run ruff format --check .` / `uv run ruff check .` | `405 files already formatted` / `All checks passed!` — **read-only**; no write-mode `ruff` ran, so the open `AGENTS.md:15` conflict was not touched |
| `uv run python scripts/check_trailing_commas.py --check <2 explicit paths>` | exit 0, no output. Explicit paths on the only invocation, so `drys.md` / `vulns.md` were unreachable |
| `git diff --check` | exit 0 |
| `git status --short` | **19 `M` + 4 `??` = 23 lines**, the declared baseline. My two spec paths were already among the `M` entries; `bld-integration.md` is the one new `??`. Nothing else moved, so there was nothing to stop-and-report, and nothing was reverted |

No `--cov*` flag was used anywhere. No `git` write command ran — no commit, branch, stash,
`git add`, `git checkout`, or `git restore`. The `git show HEAD:` reads in the M1 and L-A
attributions are read-only by construction. `docs/shadow/` is gitignored, so the
`review_inspect.py` runs added nothing to the tree.

## Spec changes made (Worker 1 only)

Four edits across two files, all quoted or described above. Byte counts:
`docs/spec-065-transport_security-0_0_15.md` **227,601 → 229,630** (+2,029);
`docs/spec-065-transport_security-0_0_15-rationale.md` **69,226 → 73,718** (+4,492).

1. **`## Helper-reuse obligations (DRY)`, the view-subclassing obligation** (finding S-1, item
   1). Was "Two overridden hooks — `run` for the cap and `parse_json` for the wire contract —
   both on the one private `_RequestBodyBoundaryMixin` the two views share". Now states four
   overridden hooks, names which two are mixin-hosted (`as_view`, `parse_json`) and which two
   are per-view (`run`, `parse_multipart`) with upstream's colour split as the reason, notes
   the `request_adapter_class` substitution, and re-anchors the DRY property on the one that is
   both load-bearing and true — **every decision body is single-sited on the mixin, and each
   per-view override is a thin delegate onto it**. Each of the four cites its decision.
2. **The same section, the multipart obligation** (S-1 item 2). "two-line delegates" → "thin
   delegates … the sync one two statements, the async one three, because the async request
   adapter's form data must be awaited before it can be handed over". Fixes the contradiction
   with edit 1's bullet about where the hooks live.
3. **The same section, the settings-reader obligation** (S-1 item 3). Adds the scope: the rule
   is about the `DJANGO_STRAWBERRY_FRAMEWORK` keys, and a Django setting a decision requires be
   read verbatim to mirror Django's own expression is read where the mirroring happens —
   `views.py::_form_encoding_is_utf8`'s `settings.DEFAULT_CHARSET`, per Decision 17.
4. **Decision 11's astronomical-window paragraph** (finding S-2). "one session read per
   authenticated operation" → "per authenticated **checkpoint** … never per operation, since
   the outbound frame is a checkpoint too", matching `consumers.py:269` verbatim and the
   decision's own two other tellings at `:1474` and `:1483`.

**Rationale companion (append-only, same pass).** A new
`### Change record for ## Helper-reuse obligations (DRY)` keyed to that spec heading and anchor,
carrying all three corrections with the rejected alternative and drift direction for each; and a
`**Change record — the window's cost, priced per checkpoint rather than per operation.**` block
appended to the existing `### Decision 11` entry, with its own rejected alternative. One new
link definition, `[s65-dry]`.

### Mechanical verification of the spec edits — four ways, none by eye

- `check_spec_glossary.py --spec docs/spec-065-transport_security-0_0_15.md` → `OK: 37 terms`,
  exit 0.
- **Every in-page anchor resolves.** Slugified every heading in both files fence-aware (keeping
  `_`, stripping backticks, mapping each space to one `-`) and matched all `](#…)` uses:
  `spec-065` **44 anchors, 23 uses, 0 missing**; rationale **25 anchors, 0 in-page uses**.
  This check earned its keep immediately: my first draft of edit 1 invented two Decision
  anchors (`decision-7--a-cumulative-request-body-cap-…`,
  `decision-9--the-utf-8-wire-contract-…`) that do not exist, and the checker named both
  before anything shipped.
- **Every reference-style definition is used and every use is defined**, both files:
  `used-not-defined: []`, `defined-not-used: []` — after adding `[s65-dry]`, which the same
  check flagged as missing on the first run.
- **Zero self-narration.** `grep -inE "review round|worker |pass [0-9]"` over the spec returns
  exactly one line, `:2648`, and it is a **pytest-xdist** worker inside a test-plan row, not a
  build worker. No "review round", no "pass N".

## Verdict

`Status: planned`. Six inherited items all confirmed against the tree, **two of them with a
larger scope than the routing record gave them** — item 2 is eight sites rather than six, and
M1 is a four-correction paragraph rather than two clauses inside an otherwise-true one. Three
findings this pass added: two spec/code divergences in the section `BUILD.md` sent this pass to
verify (both closed here, in the spec), and one Low in `exceptions.py` that only the
cross-module literal comparison could surface. The three multi-told contracts the pass was
told to sweep beyond the revocation one — the body cap, the UTF-8 wire contract, the Host
boundary — are consistent telling by telling, with L3 the single exception. No production
duplication was found across the five modules the slices touched, and the two production
near-copies that look like findings are verified-and-rejected with their reasons recorded at
their own sites. The test-tier cross-tree duplication gets one class-level ruling instead of
three per-helper findings.

Worker 2 has a nine-box checklist, an exhaustive writable-file list, one quoted clause for the
four L3 surfaces, a named floor-verification scope it owns, and three explicit
do-not-consolidate decisions so the pass cannot expand into a refactor.

---

## Build report (Worker 2)

### Files touched

Grounded in `git status --short`, not memory. Four of the paths below were already `M` at the
pass's start (`views.py`, `docs/README.md`, `docs/GLOSSARY.md`, `examples/fakeshop/db.sqlite3`
— Slice 5's own uncommitted work); this pass added to them rather than replacing them.

- `examples/fakeshop/test_query/test_transport_api.py` — extracted
  `_user_who_can_add_categories()` (DRY-1) and rewired **nine** inline `.post(...)` blocks onto
  `_post_bytes` (DRY-2; eight `await` sites plus one sync site the routing record's regex could
  not see — see `### Implementation notes`). `+39 / -60 (net -21)`, no assertion changed.
- `django_strawberry_framework/routers.py` — M1: the four false / drifted sentences in
  `DjangoGraphQLProtocolRouter.__init__`'s public docstring, replaced.
- `django_strawberry_framework/_strawberry_patches.py` — the false "only mount" scoping in the
  module docstring's `APPLY_UPSTREAM_PATCHES` paragraph, replaced (the item the build plan's
  `### Seven further spec/code divergences` routed source-side into this cohort; it is **not**
  one of the nine boxes, so it carries its own box in `### Item C` below).
- `django_strawberry_framework/views.py` — L3 surface (c): the `**Multipart.**` cap-contract
  paragraph, scoped to POST.
- `django_strawberry_framework/exceptions.py` — L-A: a six-line comment above
  `describe_value`'s `except`, naming the two sibling `<unprintable {T}>` spellings and why
  this one differs. No unification.
- `docs/README.md` — L3 surface (a): the `**Multipart is a carve-out…**` lead sentence, scoped.
- `examples/fakeshop/db.sqlite3` — two `GlossaryTerm.body` writes through the ORM (L1 + L3
  surface (b)). No other row, and no `title` / `anchor` / `status_text`, was touched.
- `docs/GLOSSARY.md` — regenerated by `scripts/build_glossary_md.py`. Never hand-edited.
- `docs/builder/bld-integration.md` (this file), `docs/builder/worker-memory/worker-2.md`.

**Nothing was reverted and nothing outside the list moved.** `git status --short` reads 23 `M`
+ 5 `??`; the declared baseline was 19 `M` + 5 `??` and the four new `M` lines are
`_strawberry_patches.py`, `exceptions.py`, `routers.py`, `test_transport_api.py` — all
slice-intended. `conf.py`, `auth/mutations.py`, `auth/sessions.py`, `docs/feedback.md`,
`drys.md`, `vulns.md`, `tests/test_views.py`, `KANBAN.*`, `TODAY.md`, `README.md` were neither
read-modified nor cleaned. `pre-commit`'s `kanban-tracked-path-constants` hook (which runs
`pass_filenames: false`) reported **Passed** and wrote nothing, so no constants-sync commit is
owed.

### Tests added or updated

**No new test row, and no assertion weakened.** Both edits are refactors:

- `examples/fakeshop/test_query/test_transport_api.py::_user_who_can_add_categories` — new
  module-local helper (not a test). Its docstring carries the reason the grant is needed, which
  was previously only in one of the two rows' prose.
- The two permission rows (`test_csrf_is_enforced_on_a_cookie_authenticated_graphql_mutation`,
  `test_an_over_cap_mutation_is_rejected_before_any_parse_or_schema_execution`) now obtain
  `user` from the helper; every downstream assertion is byte-identical.
- The nine rewired POST sites keep their status-code, payload, header and content assertions
  exactly as they were.
- **Proof obligation the plan set, discharged:** the file reports the **same count** before and
  after — `69 passed` on the shared `.venv` and `69 passed` at the floor, measured before the
  first edit and again after the last. No row was lost, split, or renamed.

### Validation run

| command | result |
|---|---|
| `uv run ruff format <5 touched .py paths>` | `5 files left unchanged` |
| `uv run ruff check --fix <the same 5 paths>` | `All checks passed!` (no file rewritten) |
| `uv run python scripts/check_trailing_commas.py --check <the same 5 paths>` | exit 0, no output. Explicit paths on every invocation, so `drys.md` / `vulns.md` were unreachable |
| `uvx pre-commit run --files <the 5 .py paths + docs/README.md + docs/GLOSSARY.md>` | all four hooks **Passed** (`kanban tracked path constants`, `source layout`, `ruff format`, `ruff check`) |
| ASCII-only sweep (`ord(c) > 127` over the 5 `.py` files) | `0` non-ASCII characters in each |
| `uv run pytest examples/fakeshop/test_query/test_transport_api.py --no-cov` | **69 passed** (identical to the pre-edit measurement) |
| `uv run pytest tests/test_views.py tests/test_routers.py tests/test_strawberry_patches.py tests/test_exceptions.py tests/test_cross_web_patches.py examples/fakeshop/test_query/test_transport_api.py --no-cov` | **401 passed** |
| `uv run pytest tests/test_views.py --no-cov` / `tests/test_routers.py --no-cov` | **144** / **122** — the declared counts, unmoved |
| `uv run pytest --no-cov` (full sweep) | **5202 passed, 40 skipped** in 56.85s — exactly the declared baseline |
| `uv run python scripts/check_spec_glossary.py --spec …spec-065…md` | `OK: 37 terms - all have glossary entries and at least one spec link.` exit 0, run **after** the glossary regenerate |
| `uv run python examples/fakeshop/manage.py import_spec_terms --check` | `OK: 46 done cards have glossary links.` exit 0 |
| `uv run python examples/fakeshop/manage.py check` | `System check identified no issues (0 silenced).` |
| `uv run python scripts/build_tree_md.py --check` | `docs/TREE.md is up to date.` exit 0 |
| `git diff --check` | exit 0 |

No `--cov*` flag was used anywhere. No `git` write command ran: no commit, branch, checkout,
switch, stash, `git add`, or `git restore`. The only `git` reads were `status --short`,
`diff --stat`, `diff --check`, and one `git show HEAD:docs/GLOSSARY.md` into the scratchpad for
the diff-classification below.

### Failability proofs

`None; this pass introduced no new boundary.` Verified rather than asserted: the diff adds no
guard, gate, rejection path, cap, or validation branch. The only executable production change
is zero lines — `routers.py`, `views.py`, `_strawberry_patches.py` and `exceptions.py` changed
docstring and comment text only. The one executable test-tier change is
`await _post_bytes(client, X, path=P)` replacing `await client.post(P, data=X,
content_type="application/json")`, which is the same call with the content type supplied by the
helper's default.

### Hot-path budget

`Not applicable; plan declares no hot path.` The plan's two falsification conditions were
checked rather than agreed with: (a) no statement inside any function body was added, removed,
or reordered in production code — confirmed, all four production edits are inside a docstring
or a `#` comment; (b) no per-request, per-resolver, per-connection or per-outbound-message code
path is touched. Both hold.

### Floor verification

Owned by this pass per the plan's declaration, and run.

- **Scratch venv (outside the repo):**
  `/private/tmp/claude-501/-Users-riordenweber-projects-django-strawberry-framework/621704c0-ecb4-4bd1-8c80-bd3c071801fa/scratchpad/floor`,
  built fresh this pass with `uv venv … --python 3.10`, then
  `uv pip install --python <venv>/bin/python -e . --group dev` and
  `uv pip install --python <venv>/bin/python 'django==5.2.0' 'strawberry-graphql==0.316.0'
  'channels==4.3.2' faker pillow`. The explicit `--python` is what keeps `uv pip install` off
  the shared `.venv`.
- **Resolved versions, read with `uv pip list --python <venv>/bin/python`:** Python **3.10.19**,
  `django 5.2` (`django==5.2.0` resolves and prints as `5.2`), `strawberry-graphql 0.316.0`,
  `channels 4.3.2`, `asgiref 3.12.1`, `pytest 9.1.1`, `pytest-django 4.12.0`,
  `pytest-xdist 3.8.0`, `django-filter 26.1`, `faker 40.36.0`, `pillow 12.3.0`.
- **Scope and result:**
  `<venv>/bin/python -m pytest examples/fakeshop/test_query/test_transport_api.py --no-cov -o addopts=""`
  → **69 passed** in 21.14s. The same command was run **before** the first edit as a floor
  baseline (**69 passed** in 25.54s), so the floor result is a comparison rather than a bare
  green.
- **Shared `.venv` proved unmutated:** `uv pip list` afterwards still reads `django 6.0.5`,
  `strawberry-graphql 0.316.0`, `channels 4.3.2` — the same values read before the floor venv
  was built, and the reason the shared environment is not the floor.

### Implementation notes

- **DRY-2's real site count is nine, not eight and not six.** The `await \w+\(?\)?\.post\(`
  regex the plan gave matches **8** (`:959`, `:995`, `:1000`, `:1005`, `:1439`, `:1444`,
  `:1554`, `:1559` at plan-time numbering) and all eight were rewired; the regex now matches
  **0**. Located independently by a broad `grep -n "\.post(\|\.generic(\|AsyncClient"` sweep
  rather than by trusting either number, which surfaced a **ninth** site the `await`-anchored
  regex structurally cannot see:
  `test_the_upstream_bug_workaround_still_respects_its_own_opt_out` at `:1706` built
  `Client(raise_request_exception=False).post("/graphql/", data=scalar,
  content_type="application/json")` inline — `_post_bytes`'s exact shape, on `_post_bytes`'s
  own default path, two lines above a sibling line that already called `_post_bytes`. Rewired
  too: it is the same duplication, in the same file, in this pass's own scope, and leaving it
  would have re-created the finding for the next reviewer. **Three broad `.post(` sites remain
  and are correctly NOT `_post_bytes` callers:** `_post_bytes`'s own body (`:379`); `:1240`,
  which posts a `dict` so Django multipart-encodes it (the helper forces raw data +
  `application/json`, so routing it through would change the request); and `:1706` is now the
  helper call.
- **All four `routers.py` sentences needed correcting — the routing record's "true and must
  survive" constraint is wrong, and I verified each against `consumers.py` myself rather than
  inheriting the plan's verdict.** Independent verdict, sentence by sentence: (1) "revalidates
  the session actor **before every operation**" contradicts `consumers.py:1-30` and `:52-58`,
  which state **two** checkpoints — admission *and* the outbound information-bearing frame —
  and say in as many words that admission alone can never see a running subscription again;
  (2) "**rejects the operation - not the socket -**" is the exact inverse of
  `consumers.py:52-58` (`_REVOCATION_CLOSE_CODE = 4403`, "the close IS the rejection", frame
  suppressed, no preceding operation error); (3) "`0.0` (the default) revalidates every
  **operation**" understates `consumers.py:81-83` ("at every operation admission **and** every
  `next` / `data` / operation-scoped `error` frame"); (4) "one session read per authenticated
  **operation**" is the wrong word against `consumers.py:269` ("per authenticated
  **checkpoint**"). (3) and (4) carry the *same* single-checkpoint framing as (1) and (2), so
  correcting only the first two would have left the paragraph self-contradictory. The
  replacement matches `consumers.py`'s own telling, keeps the three genuinely-true window
  sentences (the positive-value trade, the construction error, the pointer), and folds the new
  frame-detail pointer into the existing `See consumers.py::GraphQLWebSocketConsumer` sentence
  rather than adding a second pointer.
- **The L3 clause is one clause across all four surfaces, not four paraphrases** — the same
  "the carve-out is POST-scoped, and a multipart content type on any other method is counted
  like any other body, which is the stricter direction", lifted from
  `views.py::_is_multipart_form_post`'s own docstring, plus a `POST` in each lead. No fifth
  phrasing entered the tree.
- **L-A landed as a `#` comment above the `except` rather than inside the docstring** (the
  plan's stated discretion): the divergent literal is on the line below it, and a rule binding
  a future writer is worth more at the site than in a docstring paragraph a reader may skip.
- **`_user_who_can_add_categories()` placement:** immediately after `_sized_body`, before
  `_assert_body_limit_response`, inside the existing module-local helper block. The
  function-local `from django.contrib.auth.models import Permission` moved into the helper, and
  the `# drop the stale per-request perm cache` comment moved onto the `return`.
- **Glossary DB discipline.** Both writes went through the ORM (`term.save()`, so `post_save`
  fires) from an idempotent, re-runnable script guarded on the old text still being present, so
  it applies on top of concurrent churn instead of overwriting it. Verified by
  **two-consecutive-regenerate byte-stability** (`cmp` of a scratchpad copy against the second
  render: identical) plus `grep -c "scope,\." docs/GLOSSARY.md` → `0`, never by a clean
  `git diff`.
- **The `docs/GLOSSARY.md` diff is wide and that is expected, not this pass's residue.** It is
  103 changed lines against `HEAD` because `HEAD`'s copy predates Slice 5's own uncommitted
  regeneration (seven new spec-065 terms, the router / auth-mutations rewrites, the seven index
  rows). Attributed mechanically rather than assumed: `GlossaryTerm.updated_date` ordering shows
  only **two** rows written after Slice 5's `2026-07-29T00:37` batch — `id 560 request-body-cap`
  and `id 529 channels-request-adapter`, both at `17:14`, both mine — so the render delta beyond
  Slice 5's work is exactly the two dispatched fixes. The mixed diff is handed over as-is.

### Item C — the `_strawberry_patches.py` "only mount" scoping (routed by the build plan, not one of the nine boxes)

- [x] **Item C** — `_strawberry_patches.py`'s module docstring no longer claims the
      `APPLY_UPSTREAM_PATCHES` consequence lands only on Strawberry's own view.

The plan's `### Dispatched findings checklist` was written before the build plan's
`### Seven further spec/code divergences` routed this item's source-side half into this cohort,
so it gets its own box here rather than an edit to Worker 1's list.

**Confirmed by execution before anything was written**, in the state
`APPLY_UPSTREAM_PATCHES = {"strawberry": False}` actually produces (`override_settings` alone
is not that state — the gate is read at `apply()` time, so the patch stays installed; the
simulation must restore `BaseView.parse_json = _original_parse_json`, which is exactly what
`test_transport_api.py::_strawberry_patch_opted_out` does):

| probe | result |
|---|---|
| `[k.__name__ for k in DjangoGraphQLView.__mro__ if "parse_json" in vars(k)]` | `['_RequestBodyBoundaryMixin', 'BaseView']` — the mixin delegates to `BaseView.parse_json`, the attribute `apply()` assigns |
| patch installed, `DjangoGraphQLView(schema=None).parse_json(b"42")` / `(b"[1,2]")` | `HTTPException 400` (the envelope reason) |
| patch un-installed, the same two calls on the same **package** view | return `42` and `[1, 2]` |
| upstream's `data.get("query")` on those returns | `AttributeError: 'int' object has no attribute 'get'` → unhandled `500` |
| the wire contract in the same un-installed state (`parse_json` of a UTF-16 body) | still `HTTPException 400 'Unable to parse request body as JSON'` — view-owned, ungated |

So the gate is **mount-blind for the body-envelope guard** and the distinction the docstring
had to keep sharp is *which contract*, not *which view*. The correction says exactly that,
names the `super().parse_json(data)` delegation as the mechanism, and cites the live row that
already pins it on the wire against the package mount
(`test_the_upstream_bug_workaround_still_respects_its_own_opt_out`, which posts `b"42"` to
`/graphql/` and asserts `500` with the patch off and `400` with it on). The second paragraph
now scopes its "unaffected in every state" claim to the **strict UTF-8 wire contract**, which
is the half that genuinely is view-owned and ungated.

**The spec side of item C needs nothing from Worker 1.** The build plan cited Decision 9
`:1300` as calling Strawberry's own view "the only mount the gate can still reach"; that string
no longer exists in the spec, and `:1288` now reads "Its subject is *both* mounts for the
Strawberry half, whose body-envelope guard a package view still reaches through
`super().parse_json`". Worker 1's concurrent rewrite has already corrected it, and the source
telling I landed matches it. Recorded so the custodian pass does not re-derive a fix that is
already in place.

### What this pass deliberately did NOT do, and why

- **`django_strawberry_framework/conf.py:117` `#"EXCEPT for a multipart request"` — the fifth
  L3 surface. Not edited, not reverted, not read-modified.** It is the maintainer's concurrent
  dirty file and the plan routes it to the maintainer. The clause to apply is quoted verbatim in
  `### 4 — L3` above and again in `### Implementation notes`, so it can be applied without
  re-deriving it. The same is true of `conf.py`'s `UPSTREAM_PATCH_DEPENDENCIES` comment, which
  the build plan records as mirroring item C's false scoping: **also a maintainer item.**
- **`docs/spec-065-transport_security-0_0_15.md` and its `-rationale.md` — not written, not
  read-modified.** A concurrent Worker 1 is rewriting both. I read the spec for the contract
  only (`:1275-1292`, Decision 9), and its state is reported above rather than edited.
- **`tests/test_views.py` — untouched**, so finding L-B (the package-tier
  `_strawberry_patch_opted_out` lacking the live copy's
  `assert strawberry_patches._patch_is_installed() is False`) stays deferred exactly as the plan
  routes it. Worth noting that I relied on that same assertion in the live copy while proving
  item C by execution, which is evidence for the deferred finding rather than against it.
- **The three `unprintable` spellings were not unified** and **no `_async_post_bytes` twin was
  added** — both plan-level decisions, both honoured.
- **`consumers.py` — untouched**, including the `SERVER_NAME` / `SERVER_PORT` pair. It is the
  canonical telling M1's correction now points at, and it needed no change to be that.
- **No test expectation was rewritten.** Nothing failed because the code became right: the
  focused count, the two package-tier counts, and the full sweep all landed on their declared
  numbers on the first run after the edits. No row encoded the old telling — `grep -rn "before
  every operation"` over `.py` and `.md` outside per-cycle `bld-*.md` returns nothing, so the
  drifted docstring was never pinned by a test.
- **No `pragma: no cover`, no coverage flag, no test-only fix for a production problem.**

### Notes for Worker 3

- The **ninth** POST site (`:1706`, sync) is the one line in the diff that is outside the
  routing record's literal wording. Rationale is in `### Implementation notes`; it is the same
  finding, and the three surviving `.post(` sites are enumerated there with the reason each is
  correctly not a `_post_bytes` caller.
- Item C is in the diff and has no box in Worker 1's checklist. Its box, its execution evidence,
  and the reason it belongs to this cohort are in `### Item C` above.
- The `docs/GLOSSARY.md` diff against `HEAD` is 103 lines. Only two of those are this pass's;
  the attribution method (`GlossaryTerm.updated_date` ordering, which shows Slice 5's batch at
  `00:37` and exactly two rows at `17:14`) is in `### Implementation notes` and is re-runnable.
- The floor venv was built fresh and the floor scope was run **twice** — once before any edit,
  once after — so the recorded `69 passed` is a before/after comparison. Re-running at the same
  scope will reproduce it; `-o addopts=""` is required because the repo's `addopts` carries
  coverage flags.
- No shadow file was used in this pass; `scripts/review_inspect.py` was not re-run.

### Notes for Worker 1 (spec reconciliation)

No amendment is owed by the diff itself: every source edit brings a docstring into line with a
spec contract that is already correct, and item C's spec half is already fixed (see
`### Item C`). Two items are recorded for the custodian pass rather than as amendments:

- **Where it lives:** `## Helper-reuse obligations (DRY)`, the test-tier helper bullet(s), if
  any names a count of inline `post` sites. **Current wording:** none found on a grep of the
  spec for `post_bytes` / "six" in that section — so this is a *forward* note, not a
  correction: **recommended replacement / addition** is that the spec's DRY section should not
  restate a site count at all, since two routing records in this build named one that had moved
  (`6` → `8` → the measured `9`). A helper's contract ("one `_post_bytes` serves both
  transports; no async twin") is stable; a count is not.
- **Where it lives:** `## Edge cases` / `### Error shapes`, wherever the multipart carve-out's
  method scope is stated. **Current wording:** Decisions 8 and 17 already state the POST scope
  (the plan confirms this and says the spec side needs nothing). **Recommended replacement:**
  none — recorded only so the custodian can confirm the four now-settled source/doc tellings
  (`views.py`, `docs/README.md`, `GlossaryTerm request-body-cap`, and the still-outstanding
  maintainer-owned `conf.py:117`) match the spec's wording verbatim rather than approximately.

### Remediation of review round 3 (Cohort A Lows)

Both Cohort A findings from `docs/builder/bld-review-3-integration.md` are closed; nothing else
was touched.

- **A-L1** — `### Files touched` said "Net -49 lines" for
  `examples/fakeshop/test_query/test_transport_api.py`. Re-measured:
  `git diff --numstat HEAD -- examples/fakeshop/test_query/test_transport_api.py` -> `39 60`
  (`1 file changed, 39 insertions(+), 60 deletions(-)`), i.e. **net -21**. The bullet now reads
  `+39 / -60 (net -21)`. No other claim in that bullet changed; the helper extraction, the nine
  rewired sites, and "no assertion changed" all still hold as reviewed.
- **A-L2** — the `describe_value` fallback comment in
  `django_strawberry_framework/exceptions.py::describe_value` said "the spelling its two
  siblings use" and then priced the cost as "Three spellings of one placeholder", which cannot
  both be true. Measured: **three sites, two spellings** — `<unprintable {T}>` at
  `django_strawberry_framework/exceptions.py::_safe_arg_repr` and at
  `django_strawberry_framework/exceptions.py::DjangoStrawberryFrameworkError.__str__`, and
  `an unprintable {T}` at `describe_value`. The last sentence now reads "Three sites carrying
  two spellings is the cost of that grammatical difference - do not unify them, or one of the
  three sites reads wrongly." The two-siblings clause is unchanged and now consistent with it;
  the spellings themselves are deliberately still NOT unified, and no test expectation moved.

Gates for a two-line documentation-only remediation (no `--cov`, no repo-wide write-mode ruff):

- `uv run pytest tests/test_exceptions.py examples/fakeshop/test_query/test_transport_api.py --no-cov`
  — the module that owns `exceptions.py` plus the transport tier whose messages render through
  `describe_value`.
- `uv run ruff format --check django_strawberry_framework/exceptions.py` and
  `uv run ruff check django_strawberry_framework/exceptions.py` — scoped, read-only.

---

## Final verification (Worker 1)

`Status: final-accepted` on this artifact and on
`docs/builder/bld-custodian-3-claim_audit.md`. Both were set only after the checks below, and
**nothing was accepted on either cohort's prose or on Worker 3's acceptance**: every
spot-verification was re-settled by anchor string, by reading source, or by execution — never by
line number, because three of the paths involved are concurrently written.

Files this pass wrote: the two `Status:` lines and this section. **No source, no test, no spec, no
rationale, no DB, no generated doc.** No `git` write command ran (`status`, `diff --check`,
`diff --numstat` only).

### Artifact-chain coherence

- **Every `Status:` in the round is a single bare legal value**, verified with `grep -n "^Status:"`
  across the three round artifacts: `bld-integration.md:5`, `bld-custodian-3-claim_audit.md:3`,
  `bld-review-3-integration.md:7`. No compound value, no trailing qualifier.
- **Every finding is closed with evidence or routed with a named owner.** The round's population
  is A-L1, A-L2, B-L1, B-L2 plus the ten not-fixed records and the inherited maintainer items.
  A-L1 / A-L2 / B-L1 are closed at their sites and re-verified below; B-L2 is closed by Worker 0
  in the build plan's `## Artifact list`, with the `BUILD.md` naming question left with the
  maintainer; the leftovers are ruled on below. Nothing was closed by a bare rejection reason.

### Spot-verifications (four required, five run)

| claim | how it was settled | result |
|---|---|---|
| **A-L1** — the net-count fix | `git diff --numstat HEAD -- examples/fakeshop/test_query/test_transport_api.py` -> `39 60`; `### Files touched` reads `+39 / -60 (net -21)` (2 occurrences of `#"(net -21)"`). The single surviving `Net -49` is inside `### Remediation of review round 3`, quoting the superseded figure, which is the record and not a residue | **holds** |
| **A-L2** — the `exceptions.py` comment | read at `django_strawberry_framework/exceptions.py::describe_value`: `#"its two siblings use"` at the comment's head and `#"Three sites carrying two spellings"` four lines down, now mutually consistent. Counted the population myself: **three sites** (`_safe_arg_repr`, `describe_value`, `DjangoStrawberryFrameworkError.__str__`) carrying **two** spellings, `<unprintable {T}>` twice and `an unprintable {T}` once. Still deliberately un-unified | **holds** |
| **B-L1** — the five-`try`-blocks clause | read `_request_body.py` end to end rather than the clause: `_declares_seekable` carries one `try` (`seekable()`); `_measured_remaining` carries three (`tell()`, `seek(0, SEEK_END)`, `end - position`); `_position_restored` carries **one** wrapping both its restoring `seek` and its verifying `tell()`. Six guarded call sites, five `try` blocks — exactly what item 1 now states. `grep "each in its own"` over the artifact -> **0** | **holds** |
| **Correction 1 (F6)** — the over-reported position is refused, not read | **source**: `_measured_remaining` calls `_position_restored(stream, position)` and returns `_Probe.CORRUPTED` *before* `remaining = end - position` is reachable; `_position_restored` returns `False` when the verifying `tell()` disagrees; `body_exceeds_limit` then logs `_CORRUPTED_PROBE_LOG_MESSAGE` at `warning` and returns `True` with nothing read. **tests**: `tests/test_views.py::test_a_stream_reporting_a_position_past_its_end_is_refused_rather_than_read` asserts `413`, `_BODY_LIMIT_REASON`, `stream.requested == []`, `stream.delivered == 0`, `hasattr(request, "_body") is False`, and the single log record. The spec's rewritten telling (`#"could not prove it put back and the request is refused with the package's own"` + `#"zero bytes read"`) matches both | **holds** |
| **Corrections 4 and 8** (my chosen extra, two rather than one) | `grep -c "two-line\|two line"` over the spec -> **0**; `grep -c "only mount"` over the spec -> **0**. Both falsified spellings are gone tree-wide from the spec, which is the mechanical form of the two corrections' claims | **holds** |

### The tenth tick, audited

**Item C — `_strawberry_patches.py`'s `APPLY_UPSTREAM_PATCHES` scoping — LANDED, and audited here
as the round's tenth item.** Its box lives in Worker 2's build report rather than in
`### Dispatched findings checklist`, which is the correct handling (Worker 2 may not edit Worker
1's list); it is audited exactly like the nine.

Settled at the source rather than from the report: `grep -n "only mount\|only the mount"` over
`django_strawberry_framework/_strawberry_patches.py` returns **no hit**, and the module docstring
now reads `#"What the gate does NOT scope is the **mount**"`, names
`views.py::_RequestBodyBoundaryMixin.parse_json`'s `super().parse_json(data)` delegation as the
mechanism, states the `b"42"` / `b"[1,2]"` consequence on a real `DjangoGraphQLView`, and cites
the live row that pins it on the wire against the **package** mount
(`test_the_upstream_bug_workaround_still_respects_its_own_opt_out`). The second paragraph scopes
its "in every state" claim to the strict UTF-8 **wire contract**, which is the half that genuinely
is view-owned and ungated. The spec side is already correct (correction 8, verified above by the
zero-hit grep), so source and spec now tell one story. **Ticked; no over-tick, and no box in
either list is silently un-ticked.**

### Rulings on the routed leftovers

Each is ruled on individually. None is dropped.

- **Item 2 — `consumers.py`'s `send_revalidated_operation_frame` docstring says "two-line
  delegation"; `send_json` is four lines. RULED: NOT a gate blocker. Routed to
  `bld-final.md`'s `### Deferred work catalog` AND named to the maintainer, with the fix
  pre-measured so no future pass re-derives it.** Measured myself rather than inherited:
  `consumers.py #"two-line delegation"` is one site, and
  `_RevocationGatedWebSocketAdapter.send_json`'s body is four statements (the frame-type test, the
  delegating `await super().send_json(message)`, the `return`, and the gated call). It is
  correction 4's defect class in source. Three facts make it a deferral rather than a
  micro-dispatch: `git status --short django_strawberry_framework/consumers.py` is **clean**, so
  the false clause is **committed and pre-existing** to this round rather than a regression this
  build introduced (`AGENTS.md:33`'s root-cause obligation is about correctness regressions, and
  a delegate line count is not one); it is a **private** module docstring with no consumer-facing
  surface, unlike M1's public constructor; and M1's corrected `routers.py` paragraph points at
  `consumers.py` for the **checkpoint** contract, not for the delegate's shape, so nothing the
  round shipped depends on the wrong number. **Improvement on the recorded routing:** the
  replacement is "a four-statement delegation - the frame-type test, the plain `super()`
  delegation for a non-information-bearing frame, its `return`, and the gated call", and it should
  ride the next pass that legitimately opens `consumers.py` rather than an opening of that file
  for its own sake.
- **Item 7 — the two residual history-narrating phrases. RULED: CLOSED as no-change, confirming
  Worker 3's recommendation.** Both phrases exist and I read them in place: spec `:1152`
  `#"This is the only new refusal"` and `:1337` `#"previously a Channels-routed deployment never
  reached that adapter at"`. Both describe **shipped `0.0.14`** behavior, which the spec is
  entitled to state; a reader applying no chronology reads each correctly, which is the exact
  distinction `BUILD.md` `## Spec rationale extraction` draws. No spec edit was made and none is
  owed. The ruling is recorded here so it is not re-raised every sweep.
- **Item 5 — why the last-validated timestamp lives on the ASGI `scope` rather than beside the
  lock and the flag on the consumer instance. RULED: confirmed as a spec gap, routed to the
  maintainer.** Verified the gap rather than the record: `consumers.py:209-214`'s comment on
  `_REVALIDATED_AT_SCOPE_KEY` explains only the key's collision-safe namespacing, and neither the
  spec nor the rationale states a reason. Correction 3 recorded the fact and correctly invented no
  reason — inventing one would be a worker asserting a design intent it does not hold. It belongs
  to whoever decided it.
- **Item 6 — the spec nowhere states how the outbound gate reaches the consumer's lock. RULED:
  confirmed as a spec gap, routed to the maintainer or a future custodian pass.** Verified
  mechanically: `grep -c "ws_consumer"` over the spec -> **0**, so neither of the two hops
  (`websocket.ws_consumer` for the adapter seam, `handler.view` for admission) is named anywhere
  in the spec, and a reader cannot derive the reachability from it. An omission rather than a
  divergence, so nothing in the spec is false and no `revision-needed` follows. It is a
  one-clause addition to Decision 16 whenever a pass legitimately opens that decision.
- **Item 9's process proposal — "a downstream doc more accurate than the spec means the contract
  moved" as a first-class sweep. RECORDED here as a `BUILD.md` closeout candidate. `BUILD.md` was
  not edited.** The evidence for it is this build's own: the tell fired four times, and on
  corrections 8 and 9 the shipped docstring and `docs/README.md` were right while the spec was
  stale — it located two of the nine corrections before an auditor did. As a candidate step it
  reads: at the integration pass, diff every consumer-facing or docstring telling of a contract
  against the spec's, and read a disagreement as **the spec being stale by default** rather than
  the doc. It is the maintainer's to adopt, and it is bounded by the corpus ratchet.

Also confirmed still routed, unchanged, and not re-litigated: **L9** and the **`conf.py:117`**
fifth L3 surface as maintainer items (`grep "POST-scoped"` over `conf.py` -> no hit, so it is
genuinely still open and was not quietly fixed across the partition); **L-B**; the cross-tree
test-helper class ruling; **B-L2**'s `BUILD.md` artifact-naming question; **M4** and **M5**, which
are the maintainer's pending decisions and were not touched.

### Gates run in this final-verification pass

| gate | result |
|---|---|
| `uv run pytest --no-cov` (FULL suite) | **5202 passed, 40 skipped** in 66.84s — exactly the declared baseline |
| `uv run python scripts/check_spec_glossary.py --spec docs/spec-065-transport_security-0_0_15.md` | `OK: 37 terms - all have glossary entries and at least one spec link.` **exit 0** |
| `git diff --check` | **exit 0** |
| `docs/GLOSSARY.md` two-consecutive-regenerate byte-stability, **rendered to scratch** | `build_glossary_md.py --md <scratch>/fv-g1.md` and `--md <scratch>/fv-g2.md`, both exit 0; `cmp fv-g1 fv-g2` **identical** and `cmp fv-g1 docs/GLOSSARY.md` **identical**. The tracked file was never written — it is still the `M` line the round left, byte-for-byte the current render |
| `git status --short` | **33 lines**, identical to Worker 3's pass-2 count. Nothing was added, removed, newly dirtied, or reverted |

No `--cov*` flag was used. No `ruff` of any mode ran, because this pass touched no `.py` file.

### Verdict

`final-accepted` for both cohorts. Ten of ten dispatched items landed (the nine boxes plus Item
C), all three round-3 Lows are closed at their sites with the evidence re-derived here rather than
inherited, the four required spot-verifications plus one extra all hold, every leftover carries a
ruling with a named owner, and every gate is green on the declared numbers.
