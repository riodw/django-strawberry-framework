# Worker 3 residual review — spec-065 review round 2, remediation of M1 / M2 / M3

Reviewer: Worker 3 (isolated from all three builder cohorts and from the predecessor W3 pass).
Subject: the **remediation** of `docs/builder/bld-review-2-w3_review.md`'s five Medium findings, which
went builder -> commit with no independent review pass. Reviewed against
`docs/spec-065-transport_security-0_0_15.md` (custodian-corrected 2026-07-28),
`docs/spec-065-transport_security-0_0_15-rationale.md`, and the working tree as it stands.

Status: final-accepted

Scope of the diff reviewed: `git diff 511aec8a..HEAD -- django_strawberry_framework/ tests/` plus
`examples/fakeshop/test_query/test_transport_api.py`. The maintainer squashed round 2 **and** its
remediation into one commit (`10c50722`), so the remediation is not separable by `git`; it was
reviewed as the current state of the four production files and three test files, cross-read against
the three cohorts' `## Build report (Worker 2, pass 2)` sections.

**M4 and M5 are pending maintainer decisions** (`docs/builder/build-065-transport_security-0_0_15.md`
`## Open maintainer decisions`). Neither is re-litigated here. The one new unpinned boundary below is
the **thirteenth**, not one of the twelve censused.

Baseline reproduced myself, in the shared `.venv` (Python **3.14.2**, django **6.0.5**,
strawberry-graphql **0.316.0**, channels **4.3.2**, daphne **4.2.2**, asgiref **3.11.1** — read with
`uv pip list`, never from memory or from a number in a document):

- `uv run pytest --no-cov` -> **5199 passed, 40 skipped**
- `uv run pytest tests/test_views.py examples/fakeshop/test_query/test_transport_api.py --no-cov` -> **210 passed**
- `uv run pytest tests/test_routers.py --no-cov` -> **122 passed** (run 3x consecutively: 122 each time, no flake)
- `uv run ruff format --check .` -> 405 files already formatted; `uv run ruff check .` -> All checks passed
- `git diff --check` -> clean (exit 0)
- `uv run python scripts/check_trailing_commas.py --check <the 9 files this round touched, explicit paths>` -> clean
- `uv run python examples/fakeshop/manage.py check` -> no issues; `… makemigrations --check --dry-run` -> No changes detected

**The +100 rows against the cohorts' recorded 5099 are fully attributed and are nobody's error:**
`tests/test_prove_failability.py` collects exactly **100** (`--collect-only`), and it landed in
`a5e8e91f`, a commit the builders' sweeps predate. `5099 + 100 = 5199`.

Method: source reading against the installed Django 6.0.5 **and** against a purpose-built floor venv
(Python 3.10.19 / Django 5.2 / strawberry-graphql 0.316.0 / channels 4.3.2 — `uv pip list --python`
reading cited below); **15 independent production mutants**, 11 of them driven by
`scripts/prove_failability.py` and 4 by hand; and one throwaway probe under
`docs/builder/temp-tests/review-2-residual/`. No `--cov*` flag. No `git` command that writes.

---

## The three verdicts, first

| Finding | Closed by a real bound, or a relabelling? | The input now refused that was previously accepted |
|---|---|---|
| **M1** — `_form_encoding_is_utf8`'s `or`-chain lets a declared `charset=utf-8` mask a middleware-set `request.encoding` | **real bound** | a multipart POST declaring `charset=utf-8` whose `request.encoding` a consumer middleware set to `iso-8859-1`. Previously `200` with the raw `0xe9` decoded as Latin-1 and **no** `U+FFFD` for the loss detector to see; now `400`. Reverting the function to the exact round-2 `or`-chain fails **3** rows, on the package tier and on **both** live transports |
| **M2** — the `run_task` guard's one production path has no test, and the recorded reason is false | **real bound, and the predecessor's own secondary ruling is wrong** | nothing is newly *refused* — this finding asked for a row, and the row exists and bites. Removing the guard fails **2** rows, and the failing assertion is `assert not consumer.run_task.cancelled()`, i.e. the guard's **DIRECTION**, which the predecessor recorded as unobservable in this harness. Confirmed by traceback, both protocols |
| **M3** — the no-`server` `SERVER_NAME` fallback is a 0-row mutant | **real bound** | a handshake with no `Host`, no `X-Forwarded-Host` and no `scope["server"]`. The predecessor's own mutation (`"unknown"` -> an allowed host) now fails **7** rows on current **and the same 7 at the floor**, where the predecessor measured **0** |

All three are bounds rather than relabellings, and none rests on a detection after the harm.

---

## Findings by severity

### High:

None.

### Medium:

#### M6 — `_canonicalizes_to_utf8`'s `TypeError` arm is a new rejection path with **zero** pinning rows

`django_strawberry_framework/views.py::_canonicalizes_to_utf8`:

```python
    try:
        return codecs.lookup(encoding).name == _UTF8_CODEC_NAME
    except (LookupError, TypeError):
        return False
```

`_canonicalizes_to_utf8` is **new in this remediation** — it is the helper the conjunctive M1 fix
extracted — so its rejection path owes a failability proof under `BUILD.md`
`### What needs a proof, and what does not`. The `LookupError` half is well pinned (5 rows, see proof
4 below). The `TypeError` half is not pinned at all:

- mutation: `except (LookupError, TypeError):` -> `except LookupError:`
- scope as run: `uv run pytest tests/test_views.py examples/fakeshop/test_query/test_transport_api.py --no-cov`
- pre-mutation state of that scope: **210 passed**, exit 0, 0 pre-existing failures
- **failing node ids: (none). 0 rows.** collection/setup errors: 0
- revert proved: `filecmp.cmp(shallow=False)` True and sha256 `dedcecec16874127…` == pristine

**why 0: weakly pinned, not harness-impossible.** The harness can exhibit it trivially, which is the
point — I wrote the row in four lines. `docs/builder/temp-tests/review-2-residual/test_typeerror_arm.py`
(**5 passed**) drives the real production method with `request.encoding` set to `object()`, `42`,
`b"utf-8"` and `["utf-8"]` and gets a controlled `400` on all four.

**Reachable from supported public API, not synthetic.** `HttpRequest.encoding` has a public setter and
is Django's documented per-request override — the very deployment shape M1's own fix exists for. A
middleware assigning bytes lifted off a header (`b"utf-8"`) is the plausible slip.

**Direction, stated so nobody reads this as a reopened bypass.** The arm fails **closed**: removing it
converts a controlled `400` into a bare `TypeError` that escapes `_enforce_multipart_form_encoding` ->
`_enforce_request_boundary` -> `run`, which upstream's `dispatch` (`except HTTPException`) does not
catch, so the wire answer becomes an unhandled `500`. **Nothing that is refused today becomes
accepted.** This is a missing-row finding on a new rejection path, not a fail-open.

Why Medium rather than Low: `BUILD.md` `### Acceptance rule: weakly pinned is revision-needed` is
arithmetic on purpose and says a 0-row boundary is "never a recorded exception"; `## Severity
definitions` lists "missing tests for important branches" at Medium; and a temp test that catches a
real untested edge case is, per `worker-3.md` `## Temp test rules`, "a Medium or High finding so
Worker 2 will promote it".

**Recommended change.** Promote the probe. One parametrized row in `tests/test_views.py` beside
`test_only_codecs_that_canonicalize_to_utf8_are_accepted_as_a_form_encoding`:

```python
@pytest.mark.parametrize("encoding", [b"utf-8", 42, object()])
def test_a_non_string_effective_encoding_is_refused_rather_than_escaping_as_a_typeerror(encoding):
    ...
    with pytest.raises(HTTPException) as excinfo:
        view._enforce_multipart_form_encoding(_multipart_request(encoding=encoding))
    assert (excinfo.value.status_code, excinfo.value.reason) == (400, _JSON_PARSE_REASON)
```

`_multipart_request(encoding=…)` already exists (`tests/test_views.py:1630`) and applies the value
after construction, which is the only order a middleware can act in — so the row needs no new
fixture. **Test expectation:** with `except LookupError:` substituted, that row fails; with the
shipped tuple it passes. No live sibling is required — the reachable trigger is a consumer
middleware, and the package-tier row exercises the same shared mixin method both transports call.

### Low:

None. (Every Low the predecessor raised — L1 through L9 — is dispositioned; see
`## The predecessor's L1-L9, walked` below. Two items that would otherwise be Lows belong to Slice 5
and to the plan rather than to a builder, and are routed under
`### Notes for Worker 1 (spec reconciliation)` instead of being filed against a cohort that cannot
close them.)

### nits

- **`views.py::_form_encoding_is_utf8`'s docstring numbers the two conditions in the reverse of the
  code's evaluation order.** The docstring (and Decision 17) call the effective encoding
  "requirement 1" and the declaration "requirement 2", while the code tests the declaration first.
  Harmless — both conditions are pure, `and` is commutative here, and the spec explicitly says they
  are "not rungs of a fallback chain" — but the spec's outcome table *attributes* refusals by
  requirement number, and for the rows that fail **both** (a usable `charset=iso-8859-1`, promoted
  onto `request.encoding`) only the evaluation order makes the attribution determinate. The table
  says "refused at requirement 2" for exactly those rows, so the spec and the code agree; it is the
  docstring's numbering that reads as a sequence it is not. One clause would fix it.
- **`SERVER_NAME` / `SERVER_PORT` are the only repeated string literals in any file this round
  touched** (`scripts/review_inspect.py`, 2x each, `consumers.py::_host_validation_request`), and
  they should **not** be consolidated. The if/else writes the same two keys twice because it mirrors
  `django/core/handlers/asgi.py::ASGIRequest.__init__`'s own if/else item for item, and that mirror
  is the documented contract the projection's oracle row asserts against. Collapsing it to one
  dict-assign would make the correspondence harder to audit, not easier. Recorded as examined so it
  is not "tidied" later.

---

## Failability proofs — the independent re-run

`worker-3.md` `### Reading is necessary, not sufficient` sets the mandatory floor at **every boundary
whose recorded failing-row count is 3 or fewer, and every boundary on a security or
data-isolation decision.** Every boundary in this remediation is on a security decision, so the floor
is the whole set; I re-ran **all of it** at the scope each cohort recorded and compared **node-id
sets**, not totals.

Mechanism: `uv run python scripts/prove_failability.py <manifest> --output <report>` for 11 entries
(manifests and full reports at `docs/builder/temp-tests/review-2-residual/proofs.json`,
`proofs2.json`, `proofs-report.md`, `proofs2-report.md`), which enforces `BUILD.md`'s loop order —
anchor-matches-exactly-once first, pristine copy to a scratch root **outside** the repo
(`/tmp/dsf-w3resid-proofs*`), unmutated baseline run, mutant run, restore in a `finally`, restore
proved by `filecmp.cmp(shallow=False)` **plus** sha256. Four further mutants by hand, following the
fenced loop (`grep -c` anchor check -> `cp` outside the repo -> mutate -> run -> restore -> `cmp`).
**One mutation live at a time.** No `git` command that writes; no revert verified by an empty
`git diff`.

Every entry below: **pre-mutation state of that scope = green, 0 pre-existing failing rows, exit 0;
collection/setup errors = 0.**

### Scope A — `uv run pytest tests/test_views.py examples/fakeshop/test_query/test_transport_api.py --no-cov` (210 rows)

| # | Boundary | Mutation applied | Rows | Cohort's record |
|---|---|---|---|---|
| 1 | `views.py::_form_encoding_is_utf8` — **the whole M1 fix** | the conjunctive form replaced by the exact round-2 `or`-chain (`encoding = declared or request.encoding or settings.DEFAULT_CHARSET`) | **3** | not recorded (the cohort proved the sub-rungs instead); this is the finding's own regression mutant |
| 2 | `views.py::_form_encoding_is_utf8` #`"request.encoding or settings.DEFAULT_CHARSET"` | the `request.encoding` term dropped | **6** | proof A: 6. **same set** |
| 3 | the same expression's `settings.DEFAULT_CHARSET` term | -> `request.encoding or _UTF8_CODEC_NAME` | **2** | proof B: 2. **same set** |
| 4 | `views.py::_form_encoding_is_utf8` condition 2 | the three-line declared-charset block deleted | **5** | proof C: 5. **same set** |
| 5 | the same, narrower spelling | `declared = (request.content_params or {}).get("charset")` -> `declared = None` | **5** | not recorded; same set as 4, which is the honest reading (the read and the check are one decision) |
| 6 | `views.py::_is_multipart_form_post` — the POST scoping (L1) | `and request.method == "POST"` dropped, restoring pre-L1 behaviour | **2** | proof D: 2. **same set** |
| 7 | `views.py::_canonicalizes_to_utf8` — the `TypeError` arm | `except (LookupError, TypeError):` -> `except LookupError:` | **0** | **not recorded at all — finding M6** |

Node ids, entry 1 (the M1 regression mutant), because this is the finding that reopened the round's
own High 2:

- `tests/test_views.py::test_a_declared_utf8_charset_does_not_mask_a_middleware_set_request_encoding`
- `examples/fakeshop/test_query/test_transport_api.py::test_a_middleware_set_request_encoding_is_not_masked_by_a_declared_utf8_charset`
- `examples/fakeshop/test_query/test_transport_api.py::test_the_async_view_is_not_masked_by_a_declared_utf8_charset_either`

Node ids, entry 2 (6): the three above minus the two live M1 rows, plus
`tests/test_views.py::test_a_middleware_set_non_utf8_request_encoding_is_refused_on_its_own`,
`tests/test_views.py::test_a_reconfigured_default_charset_is_refused_but_a_declared_utf8_still_wins`,
`…test_transport_api.py::test_a_project_that_reconfigured_default_charset_is_refused_unless_the_client_declares_utf8`
and both live M1 rows. Entry 3 (2): the `…_reconfigured_default_charset…` pair, package + live.
Entries 4/5 (5): `…_only_codecs_that_canonicalize_to_utf8…[unknown-name]`,
`…_a_declared_non_utf8_charset_is_refused_even_when_django_would_decode_utf8[usable-name-django-promoted]`
and `[unusable-name-django-dropped]`, plus
`…test_transport_api.py::test_a_multipart_request_declaring_a_non_utf8_form_encoding_is_refused[unusable-codec-name]`
and its async twin. Entry 6 (2): the two `…stray_multipart_content_type…` rows, package + live.

### Scope B — `uv run pytest tests/test_views.py --no-cov` (141 rows)

| # | Boundary | Mutation applied | Rows | Cohort's record |
|---|---|---|---|---|
| 8 | `_request_body.py::body_exceeds_limit` — the `_Probe.CORRUPTED` server-side record (L2) | the `logger.warning(_CORRUPTED_PROBE_LOG_MESSAGE, …)` line deleted | **4** | proof E: 4. **same set** (`…position_past_its_end…[sync|async]`, `…cannot_restore_the_position…[sync|async]`) |

### Scope C — `uv run pytest tests/test_routers.py --no-cov` (122 rows)

| # | Boundary | Mutation applied | Rows | Cohort's record |
|---|---|---|---|---|
| 9 | `consumers.py::send_revalidated_operation_frame` #`"if task is not consumer.run_task:"` — **M2** | the whole guard replaced by `asyncio.current_task().cancel()` (the predecessor's own mutation) | **2** | revocation cohort: 2. **same set**. Predecessor measured **0** |
| 10 | `consumers.py::_host_validation_request` #`"SERVER_NAME\"] = \"unknown\""` — **M3** | `"unknown"` / `"0"` -> `"testserver"` / `"80"` (the predecessor's own mutation) | **7** | host cohort: 7. **same set**. Predecessor measured **0** |
| 11 | `consumers.py::_host_validation_request` #`raw_name.decode("latin1").lower()` | `.lower()` dropped | **2** | host cohort: 2. **same set** |
| 12 | `consumers.py::_host_validation_request` #`",".join(values)` | -> `values[-1]` (last-value-wins) | **2** | host cohort: 2. **same set** |
| 13 | `consumers.py::_HOST_META_KEYS_BY_HEADER` | the `"x-forwarded-host"` entry removed | **3** | host cohort: 3. **same set** |
| 14 | `consumers.py::_host_validation_request` #`raw_value.decode("latin1")` | codec -> `utf-8` | **2** | host cohort: 2. **same set** |
| 15 | `consumers.py::DjangoWebSocketHostValidator.__call__` #`except DisallowedHost:` | widened to `except Exception:` | **2** | host cohort: 2. **same set** |

Node ids, entry 9 (M2):
`tests/test_routers.py::test_the_subscription_limit_error_frame_is_gated_from_the_connections_own_task[graphql-transport-ws]`
and `[graphql-ws]`.
Node ids, entry 10 (M3): `…test_a_handshake_carrying_no_host_information_at_all_is_denied` plus
`test_the_host_projection_matches_djangos_asgi_adapter_key_for_key[odd-cased-header-name | duplicate-host-headers | forwarded-host-only | latin-1-only-host-bytes | no-host-and-no-server | only-headers-that-do-not-participate]`.

### The one place my re-run overturns the predecessor's ruling

The predecessor's Q2 recorded that a row on the `run_task` path "pins the *path*, not the guard's
*direction*", because `channels.testing`'s app future absorbs the self-cancellation. The revocation
cohort's pass-2 §4.1 disputes that. **The cohort is right, and I confirmed it by traceback rather than
by reading its claim.** With the guard removed, both protocols fail at
`tests/test_routers.py:3651` with

```
assert not consumer.run_task.cancelled()
E   AssertionError: assert not True
E    +  where True = <Task cancelled name='Task-4' coro=<AsyncBaseHTTPView.run() ...>>.cancelled()
```

`consumer.run_task` is a plain `asyncio.Task` on a production object, `gate.consumers[0]` hands the
row that object, and `disconnect()` drives it to completion — so the invariant is asserted at the
production object's final state, which is `BUILD.md`'s "assert the invariant at the production call
site" rule applied one step out. The direction IS pinned. Recorded here because the predecessor's
ruling would otherwise stand as the reason a future reader believes it cannot be.

### Restores, and tree integrity

All 15 restores byte-proved. Start-of-review sha256 of all seven files recorded before any mutation
and re-read after the last one — **identical**, and `git status --porcelain` diffed start vs now:
**no change**.

```
dedcecec1687412785af2add94b42599e45c3205056ae4f8d4de21bcf623e09a  django_strawberry_framework/views.py
1817cfa7dbf5de94181fdfaf369e9765e00c7bc635998b1771302e2e0cd38075  django_strawberry_framework/consumers.py
55543436f4176097555cdd9c610272c7eb3e96155d025d8afdef7b65db72bec5  django_strawberry_framework/_request_body.py
2bb05280607266c8ada01d5ace3fe88c07d9b3ae36932cca5211f324bb217d2e  django_strawberry_framework/routers.py
fec3eb4135a91f73a2954fa10594740860ab1288a1f052fbeef90caae5f7286a  tests/test_views.py
3df71013c5dca26eacc6d21f185374b5f6dcb6be06e41965b3063d105bdcc5a0  tests/test_routers.py
721e0e45f491c7a7a3e40fe76cd8074792bbf7ca9ba8144e902d6990671d2f8a  examples/fakeshop/test_query/test_transport_api.py
```

`git checkout` / `git restore` / `git stash` were never used; every restore came from a pre-mutation
copy under `/tmp`, outside the repository.

---

## Floor verification: audited, and one boundary re-proved at the floor myself

The plan's floor-verification scope is an open escalation and is not mine to settle. Both cohorts
recorded a floor run with resolved versions and a focused pass, which is what `worker-3.md` asks me
to audit. I went one step further on the **one** boundary whose verdict depends on a Django literal,
because `BUILD.md` is explicit that reading a newer version's source is not verification.

Floor venv built outside the repo, with an explicit `--python`, and the shared `.venv` re-read
afterwards to confirm it was not mutated:

```shell
uv venv /tmp/dsf-w3resid-floor --python 3.10
uv pip install --python /tmp/dsf-w3resid-floor/bin/python -e . --group dev
uv pip install --python /tmp/dsf-w3resid-floor/bin/python 'django==5.2.0' 'strawberry-graphql==0.316.0' 'channels[daphne]==4.3.2'
```

Resolved versions (`uv pip list --python /tmp/dsf-w3resid-floor/bin/python`): Python **3.10.19**,
django **5.2**, strawberry-graphql **0.316.0**, channels **4.3.2**, daphne **4.2.3**, asgiref
**3.12.1**, pytest **9.1.1**, pytest-django **4.12.0**, pytest-asyncio **1.4.0**. Shared `.venv`
after: still django **6.0.5** / Python **3.14.2** — **not mutated**.

- `/tmp/dsf-w3resid-floor/bin/python -m pytest tests/test_routers.py tests/test_views.py --no-cov` -> **263 passed** (122 + 141)
- **M3 mutant re-run at the floor** (`"unknown"` / `"0"` -> `"testserver"` / `"80"`, applied from a
  `/tmp` pristine copy, restored, `cmp` exit 0, sha256 back to `1817cfa7…`): **7 failed, 115 passed**
  — the **same seven node ids** as on current. So the M3 bound holds at Python 3.10 / Django 5.2.0
  and is not an artefact of 6.0.5.
- Django's own literals read **at the floor**, not on current:
  `django/core/handlers/asgi.py:83-84` -> `SERVER_NAME = "unknown"` / `SERVER_PORT = "0"`;
  `django/http/multipartparser.py:113` -> `self._encoding = encoding or settings.DEFAULT_CHARSET`;
  `django/http/request.py:356` -> `MultiPartParser(META, post_data, self.upload_handlers, self.encoding)`.
  Identical to what I read in the installed 6.0.5 (`asgi.py:84-85`, `multipartparser.py:113`,
  `request.py:377`), which is what makes both cohorts' "at both supported versions" claim true rather
  than asserted.

---

## Does the corrected spec match the code?

Yes, everywhere I could falsify it. Both of the custodian's corrections land, and I checked the
**code** against them rather than the prose against itself.

**Decision 17 (`:1897-1936`), three independent requirements "emphatically not rungs of a fallback
chain".** The code is `if declared is not None and not _canonicalizes_to_utf8(declared): return False`
followed by `return _canonicalizes_to_utf8(request.encoding or settings.DEFAULT_CHARSET)` — a
conjunction, with the second term **verbatim** the expression
`HttpRequest.parse_file_upload` + `MultiPartParser.__init__` produce between them (read at both
versions above). I walked all **ten** rows of the outcome table (`:1968-1979`) against the code and
against Django's promotion rule in `_set_content_type_params`; all ten are correct, including the two
that a "every value in sight must be UTF-8" reading would get wrong:

- `charset=utf-8` with `DEFAULT_CHARSET` reconfigured to Latin-1 -> **success**, because the
  declaration is promoted onto `request.encoding` and genuinely is what `MultiPartParser` receives;
- `charset=no-such-codec` -> `400` at requirement 2, because Django drops the unusable name and
  requirement 1 would otherwise be satisfied by a UTF-8 `DEFAULT_CHARSET`.

The `declared is not None` test (rather than truthiness) is also load-bearing and correct: a bare
`charset=` yields `""`, `codecs.lookup("")` raises `LookupError`, and the round-2 `or`-chain would
have treated `""` as absent. Stricter, and consistent with requirement 2 as written.

**Decision 19 (`:2095-2103`) and test-plan row 46 (`:2681-2691`) now name `"unknown"` / `"0"` and the
`"unknown:0"` denial.** The code installs exactly that pair, the projection row asserts it against
`ASGIRequest.__init__`'s own output for the same scope rather than a typed-out table, and the
behavioral row asserts the denial with an allowed-`Host` control. The derivation the spec spells out
holds: port `"0" != "80"`, `_get_raw_host` reconstructs `"unknown:0"`, `split_domain_port` yields
domain `"unknown"`, `validate_host` refuses under any `ALLOWED_HOSTS` without `"unknown"` or `"*"` —
and `is_secure()` on a bare `HttpRequest` answers `"http"` rather than raising, which is what makes
the `"80"` comparison the live one.

Nothing in the spec overstates or understates the code that I could find. The one **spec-adjacent**
divergence I did find is in the docstring's requirement numbering, filed as a nit above, and in the
build plan rather than the spec — routed to Worker 1 below.

I read the rationale companion's Decision 17 and Decision 19 entries first, and they did their job:
they are why I did not re-raise "validate the declaration instead" or "project
`HTTP_X_FORWARDED_PORT` / the `SECURE_PROXY_SSL_HEADER` header for symmetry" — both are recorded
rejected alternatives with reasons that still hold against the shipped code.

---

## Fail-open shape hunt

`BUILD.md` "Fail-open shapes" hunted across every expression the remediation introduced or touched
that computes an input to a limit, a size, a permission decision, or a rejection. Findings: **one
zero-row rejection arm (M6, fail-CLOSED)** and no fail-open.

| Shape | Site | Verdict |
|---|---|---|
| `or` fallback | `views.py` #`(request.content_params or {})` | not fail-open. `content_params` is always a dict; empty dict and `{}` give the same answer, and mutating the read to `None` outright fails the same 5 rows as deleting condition 2 (entry 5) |
| `or` fallback | `views.py` #`request.encoding or settings.DEFAULT_CHARSET` | **required**, not a fail-open: it is Django's own `or`, reproduced. A middleware assigning `""` makes Django fall through to `DEFAULT_CHARSET` too. Each term separately pinned (entries 2 and 3) |
| over-broad `except` around a check | `views.py::_canonicalizes_to_utf8` | converts "cannot prove this is UTF-8" into **refuse**, the fail-closed direction. Its `TypeError` half is unpinned -> **M6** |
| `getattr` default | `_request_body.py` #`getattr(request, "_read_started", False)` | round-1 code, not this remediation. Unreachable with `_stream` present in production, and a wrong `False` there would still be corrected by the position measurement |
| `getattr` default | `_request_body.py::_declares_seekable` | round-2 code, already reviewed; the `True`-on-absent arm is the Python 3.10 `SpooledTemporaryFile` shape and defers to `tell()` |
| clamp | `_request_body.py` #`remaining <= 0` | this is the round-1 `max(end - position, 0)` **fix**, and it guards the *answer* rather than an input spelling. Intact |
| removed `getattr` default | `consumers.py` #`window = consumer.revalidation_window` | the L4 remediation, and the right direction: a dropped attribute now raises loudly instead of silently switching the deployment to "revalidate at every checkpoint" |

One shape I chased and cleared rather than assumed: `codecs.lookup` on a **client-controlled** string
caches negative lookups in `encodings._cache`, so a hostile client sending millions of distinct
`charset=` values grows a process-lifetime dict. That is **not** package-introduced and not new here:
`HttpRequest._set_content_type_params` calls `codecs.lookup(self.content_params["charset"])` for every
request carrying a `charset` at all, under exactly the same condition, on every Django deployment.
The package adds no reachability. Recorded so it is not re-raised.

---

## Concurrency review

The remediation added **no production concurrency code**. `consumers.py`'s lock discipline,
`_revocation_observed` transition and `_revoke_connection` idempotence are unchanged from the
already-reviewed round-2 shape; the M2 and M3 closures are test-side.

The one concurrency-shaped risk the remediation *did* add is the M2 row's 100 in-flight operations per
protocol. Checked rather than assumed: `tests/test_routers.py` ran **122 passed** on three consecutive
invocations under the default 8-worker xdist run, and the full sweep is green; the row is bounded by
`_wait_until` / `_reached` / `timeout=10` failure bounds rather than sleeps, and its two protocol
params cost ~0.1 s each. `_record_outbound_gate` monkeypatches the **module attribute**
`consumers_module.send_revalidated_operation_frame`, which is how
`_RevocationGatedWebSocketAdapter.send_json` resolves it at call time — so the probe wraps the
production coroutine rather than substituting a stand-in, and `sends_under_lock` reads the production
lock at the production call site.

---

## Hot-path budget

Not mine to accept or reject; my obligation is that the number **exists** and is reproducible as
recorded. It does now: `docs/builder/bld-review-2-ws_revocation.md` §3 carries a three-arm before/after
measurement (upstream consumer / window `0.0` / window `3600.0`), median of 9 over 50 frames and over
100 frames on two concurrent operations, plus a harness-independent session-read count (51 vs 1), with
the instrument named and the environment stated. The **HTTP** cohort captured one too
(`bld-review-2-http_boundary.md` `### Hot-path budget`: `timeit.repeat(number=10_000, repeat=200)`,
+123.7 ns worst case per multipart POST) even though its path was never declared hot.

The remaining half of M5 — the plan's own missing hot-path **declaration**, and whether the maintainer
waives it — is a pending maintainer decision and is left alone. I note only the factual state, because
the plan's wording ("the round owes a number") now under-describes what is on disk.

---

## Cross-cohort duplication review

Re-checked on the remediation specifically, since each cohort's pass-2 diff is blind to the others'.
The mechanical half agrees with the reading: `scripts/review_inspect.py` across all four production
files reports **zero string literals shared between files**, and the only intra-file repeats are the
two `SERVER_NAME` / `SERVER_PORT` pairs (nit above).

What the three cohorts added in remediation, side by side:

| Cohort | New guard / rejection shape | Convergent with another cohort's? |
|---|---|---|
| HTTP | `_canonicalizes_to_utf8` + a conjunctive gate + `_is_multipart_form_post`; both refusals funnel to the two existing constants (`_JSON_PARSE_REASON`, `_BODY_LIMIT_REASON`) | no |
| HTTP | one `logger.warning` at `_Probe.CORRUPTED`, message a module constant, asserted **by identity** rather than by a re-typed string | partially — see L9 below |
| WS-revocation | no new production shape; one test row + one probe attribute | no |
| WS-host | no new production shape; one `META` oracle + six oracle params | no |

The predecessor's L9 (three fail-closed paths, one logs, two silent) is **one third closed and two
thirds routed**: `_request_body.py` now logs, `consumers.py::_actor_is_current` already did, and the
`Host` denial deliberately still does not — `bld-review-2-ws_host_boundary.md` §5 declines to build it
and routes it to the maintainer as amendment A4, on the ground that Decision 19 fixes wire
indistinguishability and says nothing about server-side observability. I agree with the routing and
with the builder's own recommendation (log all three at `warning` / `exception`, no wire change):
adding an observability surface to a fixed design is a contract-level call, and the third path lives
in another cohort's file, so no builder could have made it wholly.

One genuine cross-cohort **consistency win** worth recording, because it is the opposite of the risk
this section exists for: the two cohorts independently arrived at the same discipline for pinning an
upstream constant — `_UPSTREAM_SUBSCRIPTION_LIMIT = 100` and `_DENIED_HANDSHAKE_CLOSE_CODE = 1000`
are both **re-typed** rather than imported, each with a comment saying an upstream change must fail a
row rather than silently widen the expectation. That is the module's stated discipline applied twice
without coordination.

---

## The existence challenge

Raised where I have grounds, not on a schedule. Two new abstractions in the remediation.

**`views.py::_canonicalizes_to_utf8` — must it exist?** *Yes.* It has two real callers (the two
conditions of the conjunctive gate), and the alternative is duplicating a `try` / `codecs.lookup` /
`.name ==` triple inside one function — which is precisely the shape whose divergence M1 was. Six
lines with an eight-line docstring is the right ratio for the one place the package decides "is this
UTF-8".

**`views.py::_is_multipart_form_post` — must it exist?** *Yes*, and this is the more interesting half:
it has two callers, but its value is not the deduplication. It is that the cap's multipart carve-out
and the encoding guard's scope are now **one** definition, so they cannot drift apart on a request
shape — which is exactly how L1 happened (the cap already returned for GET; the guard did not). Its
own docstring names the one shape it excludes (a multipart content type on a method other than
GET/POST, which upstream answers `405` to) and states that such a request is counted like any other
body, i.e. the stricter direction. I verified that against `511aec8a`: the pre-remediation carve-out
was a bare `request.content_type == _MULTIPART_CONTENT_TYPE`, so the narrowing is real and is toward
strictness.

**`tests/test_routers.py`'s third oracle (`_django_asgi_host_verdict`) — must it exist beside
`_django_http_host_verdict` and `_django_asgi_host_meta`?** *Yes*, with one real caller, and the
docstring is the reason: `RequestFactory` unconditionally installs `SERVER_NAME = "testserver"`, so
the HTTP oracle **cannot express** "this request carries no server information" and its no-host leg
silently answers a different question. That is the trap the predecessor hit while writing its own
probe, now written down. Deleting it and inlining would put the trap back one refactor away.

---

## The predecessor's L1-L9, walked

Every Low is dispositioned; none is silently unaddressed.

| # | Disposition | Evidence |
|---|---|---|
| L1 | **fixed** | `_is_multipart_form_post`; mutant entry 6 -> 2 rows, package + live |
| L2 | **fixed** | `logger.warning` + message constant; mutant entry 8 -> 4 rows, asserted by message **identity** and `record.args`, with `exc_info is None` |
| L3 | **documented option taken**, recorded with the reason (a) was unavailable on the row that reads `sends_under_lock` (single operation, no contender; `asyncio.Lock` exposes no holder) |
| L4 | **fixed** | the `getattr` default deleted for plain attribute access, with the comment stating that a dropped attribute must fail loudly rather than switch the deployment to "revalidate always" |
| L5 | **fixed** | the DEBUG divergence now parametrized over two subdomain depths; host cohort's narrow `OriginValidator` mutant -> 2 rows |
| L6 | **fixed** (docstring): "private" now means unsupported-to-import, an `__all__`-and-docs contract, and the absent underscore is explained rather than left inconsistent |
| L7 | **recorded** in the async row's docstring (scaffolding asymmetry) |
| L8 | **still open, owned by Slice 5** — see `### Notes for Worker 1` |
| L9 | **one third built, two thirds routed** — see `## Cross-cohort duplication review` |
| nit 1 | **fixed** (the duplicated multipart discrimination is now `_is_multipart_form_post`) |
| nit 2 | **reasoned rejection** recorded at `bld-review-2-ws_host_boundary.md` §9 |

## Dispatched findings checklist

This artifact carries no `## Plan (Worker 1)` section, so there is no
`### Dispatched findings checklist` to walk; the dispatch was M1 / M2 / M3, and each is
dispositioned in `## The three verdicts, first` with a mutation and a node-id set. The predecessor's
own audit of the six `docs/feedback.md` round-2 findings against "name the input now refused" stands
unchanged except for its one open entry, **High 2**, which it graded "partially — not closed" on M1's
account. **M1 is now closed**, so all six round-2 findings are closed by real bounds.

## DRY findings

- None requiring change. The only repeated literal in the round's four production files is the
  `SERVER_NAME` / `SERVER_PORT` pair, and consolidating it would weaken the audit against
  `ASGIRequest.__init__` (nit above, recorded as examined so it is not "tidied").
- Examined and cleared: `tests/test_views.py::_multipart_request` / `_multipart_body` versus
  `test_transport_api.py::_multipart_bytes` / `_multipart_fields` / `_post_multipart` are **not** a
  near-copy. The package-tier pair must use `RequestFactory.generic` precisely so an *unusable* codec
  name can be put on the wire (`post` re-encodes the payload with the declared charset and cannot
  express it), and the live pair drives `django.test.Client` against the shipped mount. Two tiers,
  two jobs, both mandated by `AGENTS.md`.
- Examined and cleared: `test_views.py:456`'s `RequestFactory().post(data={...})` multipart builder is
  not duplication of `_multipart_request` — that row needs Django to *actually parse* a form.

## Public-surface check

`git diff 511aec8a..HEAD -- django_strawberry_framework/__init__.py` -> **empty**;
`git diff -- django_strawberry_framework/__init__.py` -> **empty**. `__all__` and the re-export list
are unchanged, so nothing needs spec authorization. `views.py::__all__` is unchanged at
`("AsyncDjangoGraphQLView", "DjangoGraphQLView")`; `_request_body.py::__all__` at
`("body_exceeds_limit",)`; `routers.py::__all__` at `("DjangoGraphQLProtocolRouter",)`. The
remediation's three new names (`_canonicalizes_to_utf8`, `_is_multipart_form_post`,
`_CORRUPTED_PROBE_LOG_MESSAGE`) are all underscore-private and exported by nothing.
`DjangoWebSocketHostValidator` remains unexported, which Decision 19 and its L6 docstring now define
as "unsupported to import or subclass" rather than import-time private.

## CHANGELOG sanity

Not applicable; the remediation did not modify `CHANGELOG.md`.

## Documentation / release sanity

Not applicable to this cohort's diff — the remediation modified no docs, release metadata, KANBAN or
archived specs. `docs/README.md`, `README.md` and `docs/TREE.md` are Slice 5's, are baseline-dirty
with concurrent work, and are routed below rather than reviewed here.

## Static helper use

`uv run python scripts/review_inspect.py <file> --output-dir docs/shadow` run on all four production
files (`views.py`, `consumers.py`, `_request_body.py`, `routers.py`) — required, since the remediation
adds 30+ lines of logic under `django_strawberry_framework/`. No skips. Django/ORM markers: **none**
in either main file. Control-flow: no new hotspot entries. Imports: no new cross-folder import
(`_request_body.py`'s new `from . import logger` is the same relative form
`_strawberry_patches.py` / `_cross_web_patches.py` already use). Repeated literals: as above. Shadow
files were read for control flow only; no shadow line number is cited anywhere in this artifact.

## What looks solid

- **M1's fix is the right shape and the docstring now earns its claims.** The second condition is
  `request.encoding or settings.DEFAULT_CHARSET` — Django's own expression, reproduced rather than
  re-invented — and the docstring's causal account (the declaration is consulted exactly once, at
  `_set_content_type_params`; `content_params` is never re-read at parse time) is *true*, which the
  round-2 version's "the order Django applies them" was not. I re-derived it from Django's source at
  **both** supported versions rather than grading the conclusion.
- **The M1 regression row keeps its own premise on disk.** It asserts not only the `400` but that the
  same request, allowed to parse, decodes `0xe9` to `U+00E9` with **no** `U+FFFD` — so the reason the
  loss detector cannot be the backstop is a measured fact in the suite rather than a sentence in a
  review. If a future Django starts replacing instead, that row says so instead of silently becoming
  a tautology.
- **M4's remediation replaced statement coverage with an oracle.** Six of the projection's items now
  assert equality against `ASGIRequest.__init__`'s own `META` output for the same scope. That is
  strictly better than the row-per-item the predecessor asked for: a hand-typed expectation would
  agree with a projection that had quietly reinvented casing, duplicate reduction or the codec, and
  this one cannot. The negative half (`set(projected) <= _HOST_META_KEYS`) closes the other direction.
- **The M2 row refuses the cheap version of itself.** `_UPSTREAM_SUBSCRIPTION_LIMIT = 100` is
  deliberately not lowered, because the router exposes no knob and a configured stand-in would test a
  path the deployment cannot produce; the cost is 0.1 s per protocol.
- **Both cohorts' floor runs are real and recorded**, with resolved versions read from
  `uv pip list --python`, an explicit `--python` on every install, and the shared `.venv` re-checked
  afterwards. The HTTP cohort re-ran its M1 mutant at the floor (6 rows, same 6) rather than only its
  suite.
- **`scripts/prove_failability.py` is a genuine upgrade to this loop** and I used it as the primary
  instrument. Its refusals are the right ones: it caught nothing wrong here, but the anchor-first
  ordering, the mandatory unmutated baseline, the node-id sets and the `--only` PARTIAL RECORD label
  are each a hand-run failure mode this build already paid for.

## Temp test verification

- `docs/builder/temp-tests/review-2-residual/test_typeerror_arm.py` — **5 passed**. Catches the M6
  branch: a non-string `request.encoding` (`object()`, `42`, `b"utf-8"`, `["utf-8"]`) is refused with
  the shared `400`, and no shipped row asserts it. **Disposition: promote.** Recorded as Medium M6 so
  Worker 2 promotes a parametrized form into `tests/test_views.py` beside the alias matrix; the temp
  file is not the proof of shipped behavior.
- `docs/builder/temp-tests/review-2-residual/proofs.json`, `proofs2.json`, `proofs-report.md`,
  `proofs2-report.md`, `run.log`, `run2.log` — the manifest-driven proof records above. Gitignored
  scratch; **disposition: keep for this cycle, cleared by `scripts/clean_up.py`.** Every measured
  field they carry is reproduced in this artifact, so nothing load-bearing lives only there.

## Notes for Worker 1 (spec reconciliation)

1. **`views.py::_form_encoding_is_utf8`'s docstring numbers its two conditions in the reverse of the
   code's evaluation order**, and Decision 17 inherits the numbering. Not a falsification — the spec's
   outcome table attributes the both-fail rows to "requirement 2", which IS the code's first test, so
   spec and code agree. But the docstring reads as a sequence where the spec says there is none. A
   builder-side clause on the docstring closes it; the spec needs nothing. Nit-severity.
2. **Escalated: L8 is still open and now includes a security-surface understatement.**
   `docs/README.md:360` says the default consumer "revalidates the session actor **before every
   operation**", which was true in round 1 and is now **understated**: round 2 added the outbound
   checkpoint, so revalidation also gates every information-bearing frame. And `docs/README.md:128`,
   `:283`, `:316`, `:390`, `:398` plus `README.md:62` still describe the WebSocket branch as
   `AllowedHostsOriginValidator` over `AuthMiddlewareStack` over `URLRouter`, omitting
   `DjangoWebSocketHostValidator` as the **outermost** wrapper — i.e. the whole of Decision 19 is
   absent from both READMEs. `docs/TREE.md` still has no `consumers.py` or `_request_body.py` row and
   `routers.py`'s description is spec-041's. All of this is Slice 5's ownership and both files are
   baseline-dirty with a concurrent pass, so it is deliberately **not** filed against a builder here.
   It must not close by omission: the `:360` sentence in particular now describes a weaker contract
   than the code enforces, on a page a consumer reads to decide whether the socket is safe.
3. **The build plan's `## Open maintainer decisions` under-describes what is on disk for M5.** It
   offers "(a) re-loop the cohort for a before/after number, or (b) a maintainer waiver". Option (a)'s
   *number* half is **already done** — `bld-review-2-ws_revocation.md` §3 carries the three-arm
   measurement, and the HTTP cohort captured one too. What remains genuinely open is the plan's own
   **hot-path declaration** and whether the maintainer wants the number formally accepted. Reported as
   factual state only; I take no position and did not re-litigate M5.
4. **The three round-2 `Status:` hygiene violations are still on disk** and, per the plan, are
   correctly not retro-fixed. Flagging only that `bld-review-2-http_boundary.md:16` still reads
   `Status: built (pass 2), dirty, uncommitted.` — an illegal shape — so a future automated read of
   the artifact chain will trip on it. Worker 1's final verification may want to note that the
   round's dispatch record lives in this residual review and in the plan rather than in that line.
5. **No spec edit is required by anything in this pass.** Decision 17 and Decision 19 both match the
   shipped code, and M6 is a missing test row, not a contract question.

## Review outcome

`revision-needed` — one Medium (**M6**), which is a zero-row rejection path on a new helper the M1
remediation introduced, closeable by one parametrized row whose working shape is already written and
measured. Everything the pass was dispatched to check is otherwise **closed by a real bound**:

- **M1 closed.** Reverting the whole conjunctive form to round-2's `or`-chain fails 3 rows, package
  tier plus both live transports; each of the three terms is separately pinned at 6 / 2 / 5 rows.
- **M2 closed**, and the predecessor's secondary ruling that the guard's *direction* is unobservable
  is **overturned by execution**: the failing assertion under the mutant is
  `assert not consumer.run_task.cancelled()`, on both protocols.
- **M3 closed.** The predecessor's own permissive mutation now fails 7 rows on current **and the same
  7 at Python 3.10 / Django 5.2.0**, where it previously failed 0.
- 15 mutants run, 15 restores byte-proved, every one of the seven touched files sha256-identical to
  its start-of-review state, `git status --porcelain` unchanged, no `git` write command run.

The re-run set covered **every** boundary this remediation touched — the whole mandatory floor, since
all of them sit on a security decision — plus two mutations no cohort recorded (the M1 whole-form
regression, and the M6 arm that produced the finding). Nothing was accepted on a builder's record
alone.

---

## Build report (Worker 2)

Dispatched scope: the single Medium finding **M6** above. One parametrized test row; **no production
change**. Nothing else in the artifact was widened, re-litigated, or touched.

### Dispatched findings checklist

`BUILD.md` `### Dispatched findings checklist` places this list in the artifact's
`## Plan (Worker 1)` section, and this artifact has none - Worker 3's own
`## Dispatched findings checklist` above records why (the round's dispatch was M1 / M2 / M3 and its
residual came out of the review itself rather than out of a Worker 1 plan). Rather than edit Worker
3's section to insert a box, the box is carried here so Worker 1 still has a tick to audit:

- [x] **M6** - "`_canonicalizes_to_utf8`'s `TypeError` arm is a new rejection path with **zero**
  pinning rows", `django_strawberry_framework/views.py::_canonicalizes_to_utf8`
  #`"except (LookupError, TypeError):"`. Landed as one parametrized row (3 params) in
  `tests/test_views.py`. The arm now fails **3** rows when narrowed to `except LookupError:`, on
  current **and** at the floor. Production code unchanged, per the finding's own direction analysis
  (fail-CLOSED: the finding is a missing row, not a reopened bypass).

### Files touched

Grounded in `git status --short`, not memory. **One** file in this pass's diff:

- `tests/test_views.py` - one parametrized regression row plus its param tuple, inserted directly
  after `test_only_codecs_that_canonicalize_to_utf8_are_accepted_as_a_form_encoding` where the
  finding asked for it. +33 lines, no existing row edited, no fixture changed.

Everything else `git status --short` reports is classified and is **not** this pass's churn - no
revert, no `git checkout`, no `git add`, no commit:

| Path | Owner |
|---|---|
| `README.md`, `docs/README.md`, `TODAY.md` | Slice 5 (`bld-slice-5-docs_foldin.md`), declared out of scope for this pass |
| `django_strawberry_framework/auth/mutations.py`, `auth/sessions.py`, `conf.py`, `drys.md`, `vulns.md` | baseline-dirty concurrent session |
| `docs/spec-065-transport_security-0_0_15.md`, `…-rationale.md` | Worker 1 (custodian) |
| `docs/builder/build-065-transport_security-0_0_15.md` | Worker 0 |
| `docs/feedback.md` | the maintainer's review document - evidence, never edited |
| `docs/builder/bld-review-2-w3_residual.md` (untracked), `bld-slice-5-docs_foldin.md` (untracked) | this artifact / Slice 5's |

One observation rather than a finding: **HEAD moved during this pass's dispatch window.**
`django_strawberry_framework/views.py`, `consumers.py`, `_request_body.py`, `routers.py`,
`tests/test_routers.py` and `examples/fakeshop/test_query/test_transport_api.py` were dirty when this
pass started and are clean now - the maintainer committed the round-2 remediation and the corpus work
(`10c50722`, `07e5de10`, `84c6075b`). `git diff -- django_strawberry_framework/views.py` is empty, so
the file this pass mutated and restored is byte-identical to `HEAD`, and Worker 3's start-of-review
sha256 for it (`dedcecec1687412785af2add94b42599e45c3205056ae4f8d4de21bcf623e09a`) still holds.
Recorded because the artifact chain's numbers were measured against the pre-commit tree.

### Tests added or updated

- `tests/test_views.py::test_a_non_string_effective_encoding_is_refused_rather_than_escaping_as_a_typeerror`
  - three params, `_NON_STRING_ENCODINGS` = `[bytes-lifted-off-a-header]` (`b"utf-8"`), `[int]`
  (`42`), `[arbitrary-object]` (`object()`). Each drives the shipped
  `DjangoGraphQLView._enforce_multipart_form_encoding` over a real multipart `RequestFactory`
  request whose `request.encoding` a middleware-shaped assignment set to a non-`str`, and asserts the
  **observable contract**: `HTTPException` with `status_code == 400` and `reason == _JSON_PARSE_REASON`
  (the shared indistinguishable reason, Decision 9). Node ids listed in `### Failability proofs`.

Assertion shape is the boundary's, not the helper's, deliberately: an `is False` assertion on
`_canonicalizes_to_utf8` would keep passing while the wire answer became a `500`, which is precisely
the gap the finding names. `pytest.raises(HTTPException)` is also what makes the row bite - with the
arm narrowed, the `TypeError` propagates and `raises` fails on the wrong exception type rather than on
a wrong status code.

### Validation run

- `uv run ruff format tests/test_views.py` -> `1 file left unchanged`
- `uv run ruff check --fix tests/test_views.py` -> `All checks passed!`
- `uv run python scripts/check_trailing_commas.py --check tests/test_views.py` -> exit 0 (explicit
  path, `--check`; a pathless invocation auto-fixes repo-wide and would rewrite the maintainer's
  untracked `drys.md` / `vulns.md`)
- `git diff --check tests/test_views.py` -> exit 0
- ASCII-only sweep over `tests/test_views.py` (`ord(c) > 127` per line, not by eye) -> 0 non-ASCII
- `git status --short` after both ruff invocations -> classified in `### Files touched`; the only
  modified path this pass owns is `tests/test_views.py`
- focused: `uv run pytest tests/test_views.py examples/fakeshop/test_query/test_transport_api.py --no-cov`
  -> **213 passed** (Worker 3's recorded baseline for this scope was 210; +3 reconciles exactly)
- focused, narrower: `uv run pytest tests/test_views.py --no-cov` -> **144 passed** (was 141)
- full sweep: `uv run pytest --no-cov` -> **5202 passed, 40 skipped** (baseline 5199 / 40; +3
  reconciles exactly, and the 40 skips are unchanged)

No `--cov*` flag was used anywhere in this pass. No `git` command that writes was run.

**Open reconciliation, raised not resolved:** the scoped `ruff format` / `ruff check --fix` above run
on `tests/test_views.py` only, per `worker-2.md` step 5 and this artifact's `### Validation run`
contract, while `AGENTS.md:15` mandates `uv run ruff format .` and `uv run ruff check --fix .` after
every edit. The role files defer to `AGENTS.md` on conflict (`worker-2.md` "Required reading"), yet
the repo-wide write-mode run would reformat the concurrent session's dirty files and this build's
other cohorts' files, and that churn is explicitly not a builder's to revert. This pass followed the
scoped form. **The reconciliation is the maintainer's**, and it is the fourth consecutive pass to
note it.

### Failability proofs

One entry: the boundary this pass pins. Instrument: `scripts/prove_failability.py` (manifest at
`docs/builder/temp-tests/review-2-w2-residual/proofs.json`, full report at
`…/proofs-report.md`, scratch root `/tmp/dsf-w2resid-proofs`, i.e. **outside** the repo). It enforced
`BUILD.md`'s loop order: anchor matched exactly once before the copy, pristine copy outside the tree,
unmutated baseline run, mutant run, restore in a `finally`, restore proved by
`filecmp.cmp(shallow=False)` **plus** sha256. Exit code **0**. No `git` command was involved in the
mutation, the restore, or the proof.

- `django_strawberry_framework/views.py::_canonicalizes_to_utf8` #`"except (LookupError, TypeError):"`
  - **mutation applied:** the line `    except (LookupError, TypeError):` replaced by
  `    except LookupError:`, i.e. the `TypeError` half of the rejection arm narrowed away so
  `codecs.lookup`'s `TypeError` on a non-`str` escapes the helper instead of becoming a refusal.
  This removes the boundary rather than perturbing code near it: it is the whole of what M6 measured
  as unpinned.
  - **scope as run:**
  `uv run pytest --no-cov --color=no -p no:cacheprovider --tb=no -q -rfE tests/test_views.py examples/fakeshop/test_query/test_transport_api.py`
  - the same scope Worker 3 recorded its **0**, so the two measurements are comparable by node-id set
  rather than by number.
  - **pre-mutation state of that scope:** `213 passed`, pytest exit code 0, **0** pre-existing
  failing rows differenced out.
  - **failing node ids** (the count is `len()` of this list = **3**):
    - `tests/test_views.py::test_a_non_string_effective_encoding_is_refused_rather_than_escaping_as_a_typeerror[bytes-lifted-off-a-header]`
    - `tests/test_views.py::test_a_non_string_effective_encoding_is_refused_rather_than_escaping_as_a_typeerror[int]`
    - `tests/test_views.py::test_a_non_string_effective_encoding_is_refused_rather_than_escaping_as_a_typeerror[arbitrary-object]`
  - mutant summary: `3 failed, 210 passed`, pytest exit code 1.
  - **collection / setup errors: 0** (so the count is a valid count).
  - **revert proved by byte-comparison:** `filecmp.cmp(shallow=False)` -> `True`, and sha256
  `dedcecec1687412785af2add94b42599e45c3205056ae4f8d4de21bcf623e09a` == the pre-mutation copy's.
  Confirmed independently afterwards with `shasum -a 256 django_strawberry_framework/views.py`, and
  `grep -c 'except (LookupError, TypeError):'` is back to **1**. No `ACTIVE-MUTATION.json` marker
  remains under the scratch root.
  - 3 rows is above the weakly-pinned threshold (0 or 1) and **inside** Worker 3's mandatory
  independent re-run floor (<= 3), which the tool labelled explicitly.

**The failure mode is measured, not argued.** A second, separately-restored application of the same
mutation was run with `--tb=long` on the `[bytes-lifted-off-a-header]` param to capture what actually
escapes. The traceback is `TypeError: lookup() argument must be str, not bytes` raised at
`django_strawberry_framework/views.py::_canonicalizes_to_utf8` #`"return codecs.lookup(encoding).name"`
and propagating through `_form_encoding_is_utf8`
#`"return _canonicalizes_to_utf8(request.encoding or settings.DEFAULT_CHARSET)"` - so the row's
docstring claim about direction is a reading of an execution, not a deduction. That mutation was
restored in a `finally` from its own pristine `/tmp` copy, with `filecmp.cmp(shallow=False)` `True`
and the same sha256. **One mutation live at a time throughout**; three mutations were applied across
this pass (current x1, floor x1, traceback x1) and each was reverted and byte-proved before the next
began.

### Hot-path budget

Not applicable; this pass adds no production code, so there is no before/after to measure. The
build plan's build-wide hot-path **declaration** remains the open half of M5 and is a pending
maintainer decision, not a gap this pass could close.

### Floor verification

Required and run: multipart request/body parsing is squarely a Django integration seam
(`BUILD.md` `## Floor verification` `### When it is required`). The plan's floor-verification
**scope** is an open escalation (M5) and is not settled here - the run was performed anyway, because
the escalation is about scope breadth, not about whether this seam owes one.

- scratch venv, outside the repo: `/tmp/dsf-w2resid-floor`, built with an explicit `--python`:
  `uv venv /tmp/dsf-w2resid-floor --python 3.10`, then
  `uv pip install --python /tmp/dsf-w2resid-floor/bin/python -e . --group dev`, then
  `uv pip install --python /tmp/dsf-w2resid-floor/bin/python 'django==5.2.0' 'strawberry-graphql==0.316.0' 'channels[daphne]==4.3.2' faker pillow`.
  A fresh venv of my own rather than reusing another worker's.
- **resolved versions, read with `uv pip list --python /tmp/dsf-w2resid-floor/bin/python`** (never
  restated from a document): Python **3.10.19**, django **5.2** (`django==5.2.0` normalizes to `5.2`),
  strawberry-graphql **0.316.0**, channels **4.3.2**, daphne **4.2.3**, asgiref **3.12.1**,
  django-filter **26.1**, pytest **9.1.1**, pytest-django **4.12.0**, pytest-asyncio **1.4.0**,
  pytest-xdist **3.8.0**.
- **the shared `.venv` was not mutated**: re-read afterwards with `uv pip list` -> django **6.0.5**,
  strawberry-graphql **0.316.0**, channels **4.3.2**, daphne **4.2.2**, asgiref **3.11.1**, and
  `.venv/bin/python -V` -> Python **3.14.2**. Every install carried `--python <floor>/bin/python`.
- `/tmp/dsf-w2resid-floor/bin/python -m pytest tests/test_views.py --no-cov -o addopts=""` ->
  **144 passed** (Worker 3's floor number for this file was 141; +3).
- `/tmp/dsf-w2resid-floor/bin/python -m pytest tests/test_views.py tests/test_routers.py --no-cov -o addopts=""`
  -> **266 passed** (Worker 3's recorded floor pair was 263; +3, reconciling exactly).
- **the mutant re-run at the floor**, by hand following `BUILD.md`'s fenced loop (`grep -c` anchor ->
  `cp` to `/tmp/dsf-w2resid-floormutant.orig` outside the repo, pristine copy compared to the live
  file before mutating, mutate, run, restore in a `finally`, `filecmp.cmp(shallow=False)` + sha256):
  **3 failed, 141 passed**, pytest exit code 1, **the same three node ids** as on current. Restore
  proved: `filecmp` `True`, sha256 back to `dedcecec1687412785af2add94b42599e45c3205056ae4f8d4de21bcf623e09a`.
  So the bound holds at Python 3.10 / Django 5.2.0 and is not an artefact of 3.14.2 / 6.0.5.
- **the row's premise read at the floor rather than inferred from a newer CPython:**
  `/tmp/dsf-w2resid-floor/bin/python -c "import codecs; codecs.lookup(...)"` on `b"utf-8"`, `42` and
  `object()` raises `TypeError: lookup() argument must be str, not bytes|int|object` on **3.10.19**.
  `TypeError` for a non-`str`, on every shape, at the floor - which is what makes the row's three
  params meaningful there and not only on current.

### Implementation notes

- **Param tuple as a module-level `pytest.param` tuple with explicit ids**, named
  `_NON_STRING_ENCODINGS` and placed immediately above its one consumer. That is the file's existing
  idiom (`_DECLARED_CHARSETS`, `_UNHONOURED_DECLARATIONS`) rather than an inline
  `@pytest.mark.parametrize([...])` list, and explicit ids are what let the failability record cite
  `[bytes-lifted-off-a-header]` instead of pytest's positional `[encoding2]`.
- **Three params, not Worker 3's four.** The probe carried `["utf-8"]` as a fourth. It is dropped:
  it is a `list`, so it exercises the identical `TypeError` path as `42` and `object()` with no new
  failure mode, and `object()` already covers "an arbitrary non-string". `bytes` is kept as its own
  param and given the load-bearing id because it is the one shape a real middleware plausibly
  produces (a value lifted off a header), and it reads differently in a failure report than `42`.
  Three params is also the honest row count: each fails independently, so none of the three is
  carrying another.
- **`_multipart_request(encoding=…)` reused unchanged**, verified rather than assumed - it applies the
  value **after** construction (`tests/test_views.py::_multipart_request`
  #`"if encoding is not None:"`), which is the only order a middleware can act in, and Django's
  `HttpRequest.encoding` setter performs no coercion, so a non-`str` lands intact. No new fixture, no
  fixture edit.
- **`DjangoGraphQLView(schema=SCHEMA)`, not `schema=None`.** The probe used `None`; the surrounding
  rows all pass `SCHEMA`, and matching them keeps the row from depending on the guard running before
  anything touches the schema.
- **No live sibling added.** The reachable trigger is consumer middleware rather than a wire shape a
  client can send, so `examples/fakeshop/test_query/` cannot express it without inventing middleware
  the example project does not have; the package-tier row exercises the same shared mixin method both
  transports call. This is `AGENTS.md:9`'s "genuinely unreachable from a real-world query" case, and
  it is Worker 3's own recorded judgement on the finding.

### Notes for Worker 3

- The proof scope is deliberately Worker 3's **own** recorded M6 scope
  (`tests/test_views.py examples/fakeshop/test_query/test_transport_api.py`), so the independent
  re-run differences node-id sets against a 0 measured at the same scope. Pre-mutation state of that
  scope is now 213, not 210.
- Scratch lives under `docs/builder/temp-tests/review-2-w2-residual/` (fresh subdirectory, not
  Worker 3's `review-2-residual/`): `proofs.json` and `proofs-report.md`. Gitignored; every measured
  field they carry is reproduced above, so nothing load-bearing lives only there.
  `docs/builder/temp-tests/review-2-residual/test_typeerror_arm.py` is the temp test this pass
  **promoted**; it is Worker 3's file and was left in place for it to dispose of.
- No shadow file was used - `scripts/review_inspect.py` was not run, because this pass adds no
  production logic. No shadow-file line number is cited anywhere in this section.
- **Nit 1 was NOT fixed, by scope.** Worker 3's first nit is on
  `django_strawberry_framework/views.py::_form_encoding_is_utf8`'s docstring numbering (conditions
  numbered in the reverse of the code's evaluation order). `views.py` is production code and this
  pass's writable list excludes it; the finding is fail-CLOSED and needs no production change, so
  editing the docstring would have meant touching a file this pass was told not to. Reported, not
  fixed, and already routed to Worker 1 as its own note 1. Confirmed on read that the nit is on
  `_form_encoding_is_utf8` and not on `_canonicalizes_to_utf8` - the latter's docstring numbers
  nothing and its sentence "An unknown name raises `LookupError` and a non-string raises `TypeError`;
  both mean 'the package cannot prove this is UTF-8', which is a rejection" already describes exactly
  what the new row pins.
- **Nit 2 was NOT consolidated**, as instructed: the repeated `SERVER_NAME` / `SERVER_PORT`
  assignment in `consumers.py::_host_validation_request` mirrors
  `django/core/handlers/asgi.py::ASGIRequest.__init__`'s own if/else and that mirror is the audited
  contract. Untouched, and re-recorded here as examined so a later pass does not "tidy" it.

### Notes for Worker 1 (spec reconciliation)

1. **No spec edit is required by this pass**, and I checked the code against the spec rather than
   taking Worker 3's word for it. `docs/spec-065-transport_security-0_0_15.md` Decision 17
   requirement 1 says "The encoding Django will actually decode with must canonicalize to UTF-8", and
   requirements 1 and 2 "accept exactly the codec aliases `codecs.lookup` canonicalizes to UTF-8 …
   and a name Python cannot resolve cannot be proven UTF-8 and is therefore a refusal." A non-`str`
   `request.encoding` is that same case - `codecs.lookup` cannot resolve it, so it cannot be proven
   UTF-8, so it is refused at requirement 1 - and the new row's `400` is the outcome table's
   "refused at requirement 1" cell. The spec already covers the behavior at the level it legislates;
   adding a bytes-specific clause would narrate an implementation detail. **No amendment offered**,
   deliberately, rather than an amendment without a recommended replacement.
2. **Carried forward unchanged, not re-raised:** Worker 3's notes 1 (the `_form_encoding_is_utf8`
   docstring numbering, nit-severity, needs a `views.py` edit no builder in this pass could make),
   2 (L8 / Slice 5's README + TREE understatement, including the `docs/README.md` #`"before every
   operation"` sentence that now describes a weaker contract than the code enforces), 3 (M5's
   hot-path declaration) and 4 (the round-2 `Status:` hygiene violations, including
   `bld-review-2-http_boundary.md:16`'s illegal `Status: built (pass 2), dirty, uncommitted.`) are all
   still open and all still owned by Worker 1 or the maintainer. This pass changed nothing about any
   of them.
3. **The `AGENTS.md:15` vs scoped-ruff conflict is the one process item I would put in front of the
   maintainer.** `AGENTS.md:15` reads "Run uv run ruff format . and uv run ruff check --fix . after
   every edit"; `worker-2.md` step 5 and `ARTIFACT.md` `### Validation run` both require the scoped
   form, and `worker-2.md` "Required reading" says `AGENTS.md` wins on conflict. Those cannot both be
   followed in a tree carrying concurrent work. Recommended replacement for `AGENTS.md:15`, offered so
   this is an amendment rather than a complaint: "Run `uv run ruff format` and `uv run ruff check
   --fix` on the files you touched after every edit; the repo-wide read-only check
   (`ruff format --check .`, `ruff check .`) is the gate." This is `AGENTS.md`, not the spec, so it is
   the maintainer's line to change rather than the custodian's - routed here only because this is the
   channel that reaches a human.

---

## Review (Worker 3, pass 2)

Reviewer: a **fresh** Worker 3, isolated from the builder and from the pass that wrote the sections
above. Everything the predecessor recorded was treated as a claim to spot-check, not as a finding of
mine. **Scope, deliberately narrow:** the round's whole-diff review is already done above and was not
redone. This pass reviews (a) the builder's **M6 remediation** and (b) the two builder claims Worker 0
asked to be checked independently, and then closes the round.

Not re-litigated, by dispatch: **M4** and **M5** (pending maintainer decisions), **L8** (Slice 5's,
correctly escalated above), the `SERVER_NAME` / `SERVER_PORT` mirror (must not be consolidated), and
the spec (Decision 17 already covers the non-`str` case - I checked, and I agree; see
`### Does Decision 17 still cover this?` below. No spec edit requested.)

Environment read, never restated from a document: shared `.venv` -> Python **3.14.2**, django
**6.0.5**, strawberry-graphql **0.316.0**, channels **4.3.2** (`uv pip list`, `.venv/bin/python -V`).
Floor venv built fresh for this pass, outside the repo, with an explicit `--python`: Python
**3.10.19**, django **5.2**, strawberry-graphql **0.316.0**, channels **4.3.2**, daphne **4.2.3**,
asgiref **3.12.1**, django-filter **26.1**, pytest **9.1.1**, pytest-django **4.12.0**,
pytest-asyncio **1.4.0**, pytest-xdist **3.8.0**
(`uv pip list --python /tmp/dsf-w3resid2-floor/bin/python`). The shared `.venv` was re-read after every
floor command and is **unmutated** (still django 6.0.5 / Python 3.14.2); every install carried
`--python <floor>/bin/python`.

### Verdict on the M6 row

**The row is correct, it bites, and it asserts the right thing.** Accepted.

- **It pins the arm.** I re-ran the mutation myself rather than reading the record:
  `    except (LookupError, TypeError):` -> `    except LookupError:`, at the builder's own recorded
  scope, via `scripts/prove_failability.py`. **3 rows**, and the **same three node ids** the builder
  listed. Pre-mutation state of that scope **213 passed**, exit 0; collection/setup errors **0**;
  restore proved by `filecmp.cmp(shallow=False)` **plus** sha256 back to `dedcecec16874127…`. Tool
  exit **0**. Both the count and the ids **confirmed**, not merely reproduced in total. Full record:
  `docs/builder/temp-tests/review-2-w3-residual-2/proofs.json` / `proofs-report.md`, scratch root
  `/tmp/dsf-w3resid2-proofs` (outside the repo).
- 3 rows is above the weakly-pinned threshold (0 or 1) and inside my mandatory re-run floor (<= 3),
  which is why it was re-run rather than accepted on the record.
- **It asserts the observable contract, not the helper's return value.** The row drives the shipped
  `DjangoGraphQLView._enforce_multipart_form_encoding` - a method on the **shared**
  `_RequestBodyBoundaryMixin` (`views.py::_RequestBodyBoundaryMixin._enforce_multipart_form_encoding`)
  that both `DjangoGraphQLView.parse_multipart` and `AsyncDjangoGraphQLView.parse_multipart` delegate
  to - and asserts `HTTPException` with `status_code == 400` **and** `reason == _JSON_PARSE_REASON`,
  i.e. the status and the shared indistinguishable reason Decision 9 requires. That is the rejection
  *path*, which is what M6 said was unpinned, and it is the same shape the sibling row
  `test_only_codecs_that_canonicalize_to_utf8_are_accepted_as_a_form_encoding` uses. `pytest.raises`
  is narrowed to `HTTPException`, so the mutant's escaping `TypeError` fails on the wrong exception
  type rather than sliding through a broad `except`.
- **It does not weaken, shadow or duplicate any existing row.** Checked every other row in
  `tests/test_views.py` that touches this seam: `_multipart_request(encoding=…)` appears at
  `:1756`, `:1762`, `:1796`, `:1816` and all four pass a **`str`** (`"iso-8859-1"` / `"utf-8"`), so
  none reaches the `TypeError` arm; `_DECLARED_CHARSETS`' `unknown-name` param exercises the
  **`LookupError`** half through a declared charset, a different arm of the same tuple. The row it was
  inserted after is untouched, no fixture changed, and `_multipart_request` is reused unchanged.
- **No fail-open shape in the row.** The assertions are on a status code and a message constant read
  by identity, not on a truthiness or a substring; the shared module-level `object()` param carries no
  state; `_NON_STRING_ENCODINGS` follows the file's existing `pytest.param`-tuple-above-its-consumer
  idiom (`_DECLARED_CHARSETS`, `_UNHONOURED_DECLARATIONS`) and has exactly one reader.

### Ruling on the dropped `["utf-8"]` param

**The builder is right: it is the same path, and dropping it loses no failure mode.** Settled by
execution rather than by argument, at **both** versions:

- current (3.14.2) and floor (3.10.19): `codecs.lookup` refuses `b"utf-8"`, `42`, `object()`,
  `["utf-8"]`, `bytearray(b"utf-8")`, `("utf-8",)` and `{"utf-8": 1}` with the **identical**
  `TypeError: lookup() argument must be str, not <type>`. There is one argument check and every
  non-`str` hits it; a `list` is not a distinguishable class of input at that check.
- so the boundary has exactly two input classes - `str` (resolved, then compared to the canonical
  name) and everything else (`TypeError` -> refuse) - and three params over the second class is
  already redundant rather than short. The three that were kept are the right three:
  `b"utf-8"` is the shape a real middleware produces, and its id says so.

**One thing recorded so a later pass does not "fix" it:** a **falsy** non-`str` -
`b""`, `0`, `[]`, `bytearray()` - never reaches this arm at all, because
`request.encoding or settings.DEFAULT_CHARSET` short-circuits past it. That is **correct** and must
not be "closed": `MultiPartParser.__init__` performs the identical `or`, so Django decodes such a
request with `DEFAULT_CHARSET` too, and the package agrees with what Django actually does. The params
therefore cover the whole of the reachable arm.

### Floor verification: re-executed, not spot-checked

Stated plainly because the dispatch asked which I did: I **re-executed** it, in a floor venv of my own
rather than reusing the builder's. Multipart body parsing is a Django integration seam, and the row's
premise (`HttpRequest.encoding`'s setter performing no coercion, `RequestFactory.generic` putting the
header on untouched) is Django behavior, not only CPython's.

- `/tmp/dsf-w3resid2-floor/bin/python -m pytest tests/test_views.py --no-cov -o addopts="" -q`
  -> **144 passed**. Confirms the builder's floor number.
- **the mutant at the floor**, by hand following `BUILD.md`'s fenced loop (anchor `grep`-equivalent
  count = 1 **before** the copy; pristine copy to `/tmp/dsf-w3resid2-floormutant.orig`, outside the
  repo; unmutated baseline run; mutate; run; restore in a `finally`): **3 failed, 141 passed**, exit
  1, and the **same three node ids** as on current. Restore proved:
  `filecmp.cmp(shallow=False)` -> `True`, sha256 back to `dedcecec16874127…`, anchor count back to
  **1**. Driver kept in the session scratchpad, outside the repo; no `git` command was involved in the
  mutation, the run, the restore or the proof.
- the row's premise read **at the floor**: `codecs.lookup` raises `TypeError` for all four candidate
  shapes on 3.10.19, django 5.2 (executed, not read from 6.0.5's source).

So the bound holds at Python 3.10 / Django 5.2.0 and is not an artefact of 3.14.2 / 6.0.5. Two
independent floor measurements now agree, on node-id sets rather than on totals.

### The two builder claims Worker 0 asked to be checked

**1. `views.py` byte-identical to `HEAD` - CONFIRMED.**
`shasum -a 256 django_strawberry_framework/views.py` ->
`dedcecec1687412785af2add94b42599e45c3205056ae4f8d4de21bcf623e09a`, and
`git show HEAD:django_strawberry_framework/views.py | shasum -a 256` -> the **same** digest. The path
appears in neither `git status --porcelain` nor `git diff --stat`. Read three ways, agreeing. No
production change was smuggled into this test-only pass: the only tracked file this pass owns is
`tests/test_views.py`, and the only other modified tracked source paths are `auth/mutations.py`,
`auth/sessions.py` and `conf.py`, the declared baseline-dirty concurrent session.

**2. "HEAD moved mid-pass" - REFUTED. Worker 0 is right; the artifact records an event that did not
happen.** Evidence, all read-only:

- `git rev-parse HEAD` -> `84c6075bd666a05e2a3cab3e363d95a1e2d421cc`, and
  `git reflog --date=iso` places `84c6075b` at **17:45:07**, `07e5de10` at 17:44:45, `10c50722` at
  17:44:31, `a5e8e91f` at 17:44:00 - and records **no entry after** `84c6075b`. `HEAD` has not moved
  since 17:45:07.
- those commits predate the **predecessor review**, let alone the builder pass that followed it: this
  artifact's own opening section (written by the predecessor) already says "the maintainer squashed
  round 2 **and** its remediation into one commit (`10c50722`)" and attributes +100 rows to
  `a5e8e91f` as "a commit the builders' sweeps predate". A pass cannot narrate as a commit that
  landed *during* it a commit the previous pass already reasoned from.
- corroborating wall-clock: `docs/builder/temp-tests/review-2-residual/` (predecessor) mtime 18:32 and
  `review-2-w2-residual/` (builder) mtime 18:44, both roughly an hour **after** the last commit.

So the production files were already committed and clean when the builder's pass began; they were
never "dirty when this pass started and clean now". The builder's *conclusion* from the observation
(the mutated-and-restored file is byte-identical to `HEAD`) is true anyway and I verified it above -
only the causal narration is wrong. Filed as a record correction because a false baseline note is
precisely what a later pass reasons from, and this one would have told a reader that the artifact
chain's numbers were measured against a tree that no longer exists.

One coupled observation, not a violation: `bld-review-2-w3_residual.md:687` uses
`git diff -- django_strawberry_framework/views.py` being empty to establish identity **with `HEAD`**,
which is a question `git diff` does answer, and the **restore** was separately proved by
`filecmp.cmp(shallow=False)` + sha256 at `:764-768`. So it is not `BUILD.md`'s forbidden
restore-by-empty-`git diff` shortcut. It is worth rewording anyway, because it sits inside the
sentence carrying the misattribution: had the file really been dirty with concurrent work as that
sentence claims, an empty `git diff` would have been an incoherent test rather than a passing one.

### Does Decision 17 still cover this?

Yes, and I read the code against the spec rather than taking either prior pass's word for it.
Decision 17's requirement 1 is "the encoding Django will actually decode with must canonicalize to
UTF-8", and the closing clause of the requirements 1-and-2 paragraph is "a name Python cannot resolve
cannot be proven UTF-8 and is therefore a refusal". A non-`str` `request.encoding` is exactly that
case, and `400` is the outcome table's "refused at requirement 1" cell. The outcome table owes no new
row: its column is "multipart `operations` **on the wire**", and a non-`str` `request.encoding` is not
a wire shape a client can send. **No spec edit requested, and none made** - the spec and its rationale
companion were not opened for writing by this pass.

### Findings by severity

#### High:

None.

#### Medium:

None. **M6 is closed by a real bound** - 3 rows on current and 3 at the floor, same node-id set,
measured twice independently at the scope the finding recorded its 0 against.

#### Low:

None.

#### nits

Three, all record/prose corrections with **no** behavioral consequence, none blocking. Two are the
same pattern this reviewer's memory already names: *the choice is right and the stated reason is
false.* Recording them because a false reason on disk is what the next reader reasons from.

- **The new row's docstring justifies its assertion shape with a claim that is false.** It says: "A
  row asserting only ``is False`` would still pass while that happened." Measured, not argued: I wrote
  a probe carrying **both** candidate shapes side by side
  (`docs/builder/temp-tests/review-2-w3-residual-2/test_assertion_shape.py`) and re-applied the same
  arm mutation. Pre-mutation **6 passed**; under the mutant **6 failed / 0 errors**, including all
  three `test_helper_level_shape[...]` rows - because with the arm gone
  `_canonicalizes_to_utf8(b"utf-8")` *raises* rather than returning, so an `is False` assertion errors
  out and fails too. Restore proved (`filecmp` `True`, sha256 `dedcecec16874127…`). The **choice** of
  the boundary-level shape is still right, on a true reason the docstring could state instead: it pins
  the *status code* and the *shared Decision-9 reason*, which a helper-level assertion pins neither
  of, and it matches the sibling row's idiom. One clause fixes it.
- **The build report's reason for adding no live sibling is also false, and its conclusion still
  stands.** `### Implementation notes` says `examples/fakeshop/test_query/` "cannot express it without
  inventing middleware the example project does not have". That file already has it:
  `test_transport_api.py::_LatinOneEncodingMiddleware` (a class attribute `encoding = "iso-8859-1"`
  assigned onto `request.encoding`) plus `_with_a_middleware_that_sets_the_encoding()`, both added by
  **this same round** for M1's live rows. A non-`str` live sibling is a three-line subclass and one
  more `override_settings` helper, not an invention. The conclusion is nevertheless correct on the
  right ground, which is why this is a nit and not a finding: the refusal lives on the **shared** mixin
  method both transports call, and the funnel from that `HTTPException` to a `400` on the wire is
  already pinned by the M1 live rows travelling the identical path - so a live non-`str` row would
  re-prove the funnel rather than the arm. No coverage line is at stake either
  (`AGENTS.md:9` is about lines earnable live; this line is already earned by the `LookupError` rows).
- **`### Files touched` records "+33 lines"; `git diff --numstat -- tests/test_views.py` reads
  `34 0`.** Trivial, and recorded only because every other number in this artifact chain has been
  audited by set or by digest rather than by eye.

### Fail-open shape hunt

The pass adds **no production code**, so there is no new expression computing an input to a limit,
size, permission decision or rejection. The one shape in scope is the row's own coverage of the arm,
and it is examined under `### Ruling on the dropped ["utf-8"] param` above: the arm converts "cannot
prove this is UTF-8" into **refuse**, the falsy-non-`str` short-circuit agrees with Django's own `or`
rather than widening anything, and nothing that is refused today becomes accepted. **No fail-open
shape found, and none introduced.**

### Hot-path budget

Not applicable to this pass: no production code, so no before/after exists to carry. M5's open half
(the plan's hot-path **declaration**) is a pending maintainer decision and was not re-litigated.

### Static helper use

`scripts/review_inspect.py` **not run**, and the skip is recorded with its reason: the pass adds no
production logic - the diff is one parametrized test row in `tests/test_views.py` and nothing under
`django_strawberry_framework/`, so there is no new control flow, import boundary or repeated literal
for it to report on. The predecessor's run across all four production files stands and those files are
byte-identical to it. No shadow-file line number is cited anywhere in this section.

### Test staleness sweep

Run independently rather than against the pass's enumerated file list, per `worker-3.md`. The change
adds no example-model field, renames nothing, and converts no wire shape, so neither staleness class
applies; the full parallel sweep below is the backstop and is green.

### Cross-cohort duplication review

Nothing new to compare: this pass is one cohort and adds no guard, rejection shape, status code or
error message. The predecessor's cross-cohort table stands unchanged.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` -> **empty** (0 lines);
`git diff 511aec8a..HEAD -- django_strawberry_framework/__init__.py` -> **empty**. `__all__` and the
re-export list are unchanged, so nothing needs spec authorization. The pass adds one test-module
private name (`_NON_STRING_ENCODINGS`) and no package name at all.

### CHANGELOG sanity

Not applicable; the pass did not modify `CHANGELOG.md`.

### Documentation / release sanity

Not applicable; the pass did not modify docs, release metadata, KANBAN or archived specs.

### Validation run (independent)

Everything below re-executed by me, in the shared `.venv`, with no `--cov*` flag anywhere and no
`git` command that writes:

- `uv run pytest --no-cov` -> **5202 passed, 40 skipped**. Matches the dispatch baseline exactly, and
  reconciles as +3 on the predecessor's 5199 / 40 with the 40 skips unchanged.
- `uv run pytest tests/test_views.py examples/fakeshop/test_query/test_transport_api.py --no-cov`
  -> **213 passed** (the proof run's own unmutated baseline).
- `uv run pytest tests/test_views.py --no-cov` -> **144 passed** on current, and **144 passed** at the
  floor.
- `uv run ruff format --check .` -> `405 files already formatted`; `uv run ruff check .` ->
  `All checks passed!`. **Read-only mode only** - no `--fix`, no bare `ruff format`; this pass touches
  no source, so the open `AGENTS.md:15`-vs-scoped-`ruff` conflict is sidestepped rather than resolved,
  and it is left where the builder routed it.
- `uv run python scripts/check_trailing_commas.py --check tests/test_views.py` -> exit 0 (**explicit
  path**; a pathless invocation auto-fixes repo-wide and would rewrite the maintainer's untracked
  `drys.md` / `vulns.md`).
- `git diff --check` -> exit 0. ASCII sweep over `tests/test_views.py` by codepoint (`ord(c) > 127`),
  not by eye -> **0** non-ASCII lines.
- `git status --porcelain` diffed start-of-review vs now -> **identical**. Four mutations were applied
  across this pass (current x1, assertion-shape probe x1, floor x1, and the arm re-count inside the
  tool's own baseline pairing), **one live at a time**, each restored from its own pristine `/tmp`
  copy before the next began, each restore proved by `filecmp.cmp(shallow=False)` **plus** sha256. No
  `ACTIVE-MUTATION.json` marker remains under either scratch root.
- final digest of the only production file this pass touched:
  `dedcecec1687412785af2add94b42599e45c3205056ae4f8d4de21bcf623e09a  django_strawberry_framework/views.py`
  - identical to its start-of-review value and to `HEAD`'s.

### Temp test verification

- `docs/builder/temp-tests/review-2-w3-residual-2/test_assertion_shape.py` - **6 passed** unmutated,
  **6 failed** under the arm mutation. It catches no production bug: it settles a **docstring claim**,
  and its finding is the first nit above. **Disposition: not promoted, deliberately** - the shipped row
  already pins the arm at 3 rows, and promoting the helper-level shape alongside it would add three
  rows that fail for the same reason as three that already exist. Throwaway; cleared by
  `scripts/clean_up.py`.
- `docs/builder/temp-tests/review-2-w3-residual-2/proofs.json` / `proofs-report.md`,
  `proofs2.json` / `proofs2-report.md` - the two manifest-driven proof records. Gitignored scratch;
  **keep for this cycle.** Every measured field they carry is reproduced above, so nothing
  load-bearing lives only there. Fresh subdirectory, per dispatch: neither `review-2-residual/` nor
  `review-2-w2-residual/` was reused or modified, and the predecessor's `test_typeerror_arm.py` was
  left in place.

### Notes for Worker 1 (spec reconciliation)

1. **No spec edit is required by this pass, and none was made.** Decision 17's requirement 1 covers a
   non-`str` effective encoding through "a name Python cannot resolve cannot be proven UTF-8 and is
   therefore a refusal", verified against the code rather than against the prose; the outcome table
   owes no row because its column is a wire shape. `docs/spec-065-transport_security-0_0_15.md` and
   its rationale companion were not opened for writing.
2. **Escalated: three one-clause prose corrections, bundled.** All three nits above are text, not
   behavior, and none is a builder-blocking gap - but two of them are *false statements on disk about
   why a correct choice was made*, which is the class a later pass reasons from. They are (a) the new
   row's docstring claim that an `is False` assertion "would still pass" - refuted by execution here;
   (b) the build report's claim that the live tier cannot express a middleware-set encoding - refuted
   by `test_transport_api.py::_LatinOneEncodingMiddleware`, which that same round added; and (c)
   predecessor nit 1, the `views.py::_form_encoding_is_utf8` docstring numbering, still open because
   `views.py` was outside the builder's writable list. Resolution paths, in the order I would pick
   them: **(i)** fold all three into one short Worker 2 docstring pass whose writable list includes
   `views.py` and `tests/test_views.py` - cheapest, and it retires predecessor nit 1 at the same time;
   **(ii)** accept as-is and let Slice 5's docs pass carry (a) and (c) - Slice 5 already owns prose
   corrections and (b) is a `bld-*.md` sentence no future reader needs; **(iii)** accept as-is
   permanently, recording here that the reasons are wrong and the choices are right, which this
   section does either way. I take no position beyond the ordering; none of the three blocks
   `final-accepted`.
3. **Carried forward unchanged, not re-raised:** the predecessor's notes 2 (L8 / Slice 5's README +
   `docs/TREE.md` omissions, including `docs/README.md`'s "before every operation" understatement),
   3 (M5's hot-path declaration) and 4 (the three round-2 `Status:` hygiene violations, including
   `bld-review-2-http_boundary.md:16`'s illegal `Status: built (pass 2), dirty, uncommitted.`), plus
   the builder's note 3 (the `AGENTS.md:15`-vs-scoped-`ruff` conflict). All still open and all still
   owned by Worker 1 or the maintainer. This pass changed nothing about any of them.
4. **One correction to the record, for the final-verification reader:** the builder's
   "HEAD moved during this pass's dispatch window" observation is a **misattribution** and is refuted
   under `### The two builder claims Worker 0 asked to be checked` above. `HEAD` is `84c6075b` and has
   not moved since 17:45:07; all four relevant commits predate the predecessor review. The artifact's
   recorded numbers were measured against the tree as it stands, not against a pre-commit tree, so no
   number needs re-taking - only the sentence needs not to be believed.

### Review outcome

`review-accepted`. **No High, no Medium, no Low.** M6 - the only finding this artifact left open - is
closed by a real bound: narrowing `except (LookupError, TypeError):` to `except LookupError:` fails
**3** rows, and I measured that myself at the builder's recorded scope, with the same three node ids,
against a pre-mutation state of 213 passed and 0 collection errors, **and again at Python 3.10 /
Django 5.2.0** where it fails the same three of 144. The row asserts the boundary's observable
contract (`400` + the shared Decision-9 reason) on the mixin method both transports call, duplicates
and weakens nothing, introduces no fail-open shape, and the dropped fourth param is genuinely the
same `codecs.lookup` argument check - verified by execution at both versions, so no failure mode was
lost. No production file changed: `views.py` is byte-identical to `HEAD` by digest, read three ways.
The full sweep matches the baseline at **5202 passed, 40 skipped**, hygiene is green in read-only
mode, and `git status --porcelain` is unchanged from start-of-review. Three nits, all prose, all
routed to Worker 1 with resolution paths; two of them are false *reasons* attached to correct
*choices*, and one is the builder's baseline note recording a `HEAD` move that did not occur.

---

## Final verification (Worker 1)

Custodian and final QA, spawned fresh. Everything below was **re-derived**, not inherited: the
dispatch told me two independent passes had already ruled "no spec edit required" and told me to
verify that rather than accept it. I did, and it is **almost** right - see
`### Spec changes made (Worker 1 only)`.

Environment read, never restated from a document: shared `.venv` -> Python **3.14.2**, django
**6.0.5**, strawberry-graphql **0.316.0**, channels **4.3.2** (`uv pip list`). I did **not** build a
floor venv; per `BUILD.md` `## Floor verification` the final gate is the **backstop that confirms a
planned floor verification happened**, and two passes independently executed
`tests/test_views.py` at Python **3.10.19** / django **5.2** / strawberry-graphql **0.316.0** /
channels **4.3.2**, each recording **144 passed** and each recording the M6 mutant failing **the
same three node ids** - `…[bytes-lifted-off-a-header]`, `…[int]`, `…[arbitrary-object]`. Two
measurements agreeing on a node-id **set** rather than a total is what makes that record coherent,
so I confirmed the record and re-executed only the current-version tier. Stated plainly because the
dispatch asked which I did.

### The round, finding by finding

`docs/feedback.md`'s six dispatched findings. For each I read the shipped code and the row that
pins it, rather than the artifact's claim about them.

| Finding | Closed by | Verified how |
|---|---|---|
| **Blocker 1** — revocation does not stop an already-running subscription | the outbound checkpoint at the seam both protocols share: `consumers.py::_RevocationGatedWebSocketAdapter.send_json` gates `_INFORMATION_BEARING_FRAME_TYPES` through `send_revalidated_operation_frame`, which validates, sends **inside** the connection lock, or revokes and cancels the operation task | read the gate, `_revoke_connection` (transition set **before** the close, idempotent) and `_actor_is_current`. The review's required regression exists in full and is the exact sequence it named: `tests/test_routers.py::test_a_running_subscription_cannot_emit_a_result_after_revocation`, parametrized over **both** protocols - multi-yield subscription, result 1 received, revocation through a **real second HTTP request**, result 2 released, `frames == []`, `4403`, `controller.emitted == ["running-1", "running-2"]` (the payload existed and was suppressed), `controller.finalized` (cancellation unwound the generator), and an empty task set. Plus the required valid-session control, `test_a_valid_session_keeps_a_running_subscription_emitting_every_result`, both protocols |
| **High 2** — multipart `operations` / `map` bypass the UTF-8 wire contract | the "detect the loss" contract of Decision 17: `views.py::_form_encoding_is_utf8` (requirements 1 + 2, conjunctive) plus `_reject_lossy_multipart_control_fields` (requirement 3, a literal `U+FFFD` refused before `json.loads`) | read all three requirements in code. The review demanded real multipart requests for malformed-UTF-8-with-no-charset, explicit Latin-1, escaped Unicode and genuine multibyte, on **both** views: `test_transport_api.py` carries `…lost_bytes_to_djangos_decode_is_refused`, `…declaring_a_non_utf8_form_encoding_is_refused` + its `…async_view…` twin, `…genuine_utf8_and_escaped_unicode_survive…`, and the M1 pair `…not_masked_by_a_declared_utf8_charset` + `…async_view_is_not_masked…` |
| **High 3** — the declared cap runs after CSRF has parsed the body | Decision 18's `csrf_exempt`-outside / `csrf_protect`-inside re-entry: `views.py::as_view` stamps `csrf_exempt` once on the shared mixin, `run` calls `_enforce_request_boundary` and only then enters `_csrf_protected_run` / `_csrf_protected_async_run` | read `as_view`, both `run` overrides and the two module-level `csrf_protect(...)` continuations. The review said "status `413` alone is not evidence of ordering" and demanded `Client(enforce_csrf_checks=True)` + a parser/upload sentinel: `test_transport_api.py::test_an_over_cap_multipart_request_is_refused_before_djangos_parser_runs` uses exactly that, against fakeshop's **own** `/graphql/`, and the witness is `_UPLOAD_EVENTS == []` with an under-cap control in the same row that fires `handle_raw_input`. Async twin present |
| **Medium 4** — `AllowedHostsOriginValidator` never reads `Host` | `consumers.py::DjangoWebSocketHostValidator` (Decision 19), composed by `routers.py` as the **outermost** WebSocket wrapper | read the projection and the validator, and `routers.py:458-460`'s composition. The missing direction now has its row: `tests/test_routers.py::test_the_websocket_host_and_origin_checks_are_independent` - allowed `Origin` + hostile `Host`, its converse, and the both-allowed control, with the denial's close code asserted so a `Host` refusal is wire-indistinguishable from an `Origin` refusal |
| **Medium 5** — the install hint advertises an unsupported floor | `routers.py::_STRAWBERRY_CHANNELS_BROKEN_HINT` now says `strawberry-graphql>=0.316.0` | read the constant; `tests/test_routers.py::_STRAWBERRY_FLOOR_SUBSTRING` pins `"strawberry-graphql>=0.316.0"` and the stale `0.262.0` is gone from both. `spec-041`'s historical `0.262.0` prose is Slice 5's, per the finding's own text |
| **Low 6** — stream capability failures escape as raw errors | `_request_body.py::_Probe`'s **three** outcomes; `_measured_remaining` returns `UNMEASURABLE` (position provably intact -> bounded read) or `CORRUPTED` (position unknown -> refuse), and `body_exceeds_limit` logs `_CORRUPTED_PROBE_LOG_MESSAGE` and returns `True` | read `_measured_remaining` end to end plus `_declares_seekable`. Stand-in rows exist for each failing capability: `tests/test_views.py::test_a_probe_that_fails_without_moving_the_stream_falls_back_to_the_bounded_read`, `…test_a_probe_that_cannot_restore_the_position_refuses_instead_of_reading`, `…test_a_stream_reporting_a_position_past_its_end_is_refused_rather_than_read`, `…test_a_stream_that_probes_as_empty_is_read_rather_than_believed` |

**The W3 review's M1 / M2 / M3, and M6 with them.** All four closed, and I checked the property each
mutation was supposed to demonstrate rather than the count:

- **M1** - the shipped `_form_encoding_is_utf8` is a **conjunction**
  (`if declared is not None and not _canonicalizes_to_utf8(declared): return False` then
  `return _canonicalizes_to_utf8(request.encoding or settings.DEFAULT_CHARSET)`), and its second
  term is verbatim what `parse_file_upload` + `MultiPartParser.__init__` produce between them. The
  `declared is not None` test rather than truthiness is load-bearing and correct: a bare `charset=`
  yields `""`, which `codecs.lookup` refuses.
- **M2** - the guard is `if task is not consumer.run_task: task.cancel()`, outside the lock, and
  `tests/test_routers.py::test_the_subscription_limit_error_frame_is_gated_from_the_connections_own_task`
  exists for both protocols with `assert not consumer.run_task.cancelled()`. The predecessor's
  "direction is unobservable in this harness" ruling really is overturned by execution, and the
  overturn is on disk where a future reader will look.
- **M3** - `"unknown"` / `"0"` are installed in the `else` arm of `_host_validation_request`, and
  `test_a_handshake_carrying_no_host_information_at_all_is_denied` plus six `…matches_djangos_asgi_adapter_key_for_key`
  params pin them.
- **M6** - `tests/test_views.py:1695-1726`: `_NON_STRING_ENCODINGS` (3 params, explicit ids) driving
  the shipped `_enforce_multipart_form_encoding` and asserting `(400, _JSON_PARSE_REASON)`. It
  asserts the boundary's observable contract, not the helper's return value.

**No finding was closed by a relabelling.** Each of the six names an input that is refused now and
was accepted before, or a required regression that now exists and bites. The one finding whose
prescribed remediation was a *choice* (High 2's three candidate contracts) is answered by a spec
decision that says which was taken and why the other two lost - i.e. narrowed **deliberately and in
writing**, which is the opposite of a relabelling.

**No fail-open shape landed.** Read for the catalogued shapes rather than trusted to a green suite:

- `_canonicalizes_to_utf8`'s `except (LookupError, TypeError): return False` - an over-broad
  `except` around a check, and it converts "cannot prove UTF-8" into **refuse**. Fail-closed.
- `_actor_is_current`'s `except Exception` around `_refreshed_actor` sets `refreshed = None`, which
  falls into `return False` and revokes. `Exception` not `BaseException`, so `CancelledError`
  propagates. Fail-closed, and the direction is stated in the comment.
- `_measured_remaining`'s `if remaining <= 0: return _Probe.UNMEASURABLE` guards the **answer**, not
  one spelling of an incoherent input - the round-1 `max(end - position, 0)` fix, intact.
- `body_exceeds_limit`'s `_Probe.CORRUPTED -> return True` refuses; it does not fall through.
- `consumer.revalidation_window` is a **plain attribute** now, the `getattr` default deleted, with
  the reason written at the site: a dropped attribute must fail loudly rather than silently switch
  the deployment to "revalidate at every checkpoint".
- `if server := scope.get("server")` / `else "unknown"` / `"0"` - the fallback **denies** under any
  `ALLOWED_HOSTS` lacking `"unknown"` or `"*"`. Fail-closed.
- `except DisallowedHost:` is narrow; every other exception propagates, so a projection bug stays
  visible instead of masquerading as "that host is not allowed".

### Does the spec match the shipped code? Decision 17 and Decision 19, re-derived

**Decision 17 - yes, and I walked the outcome table against the code rather than against itself.**
All ten rows follow from the conjunction plus Django's promotion rule in
`_set_content_type_params`, including the two a "everything in sight must be UTF-8" reading gets
wrong: `charset=utf-8` with `DEFAULT_CHARSET` reconfigured to Latin-1 **succeeds** (the declaration
is promoted onto `request.encoding` and genuinely is what `MultiPartParser` receives), and
`charset=no-such-codec` is **refused at requirement 2** (Django drops the unusable name, so
requirement 1 would otherwise be satisfied by a UTF-8 `DEFAULT_CHARSET`). `utf-8-sig` is refused
because `codecs.lookup("utf-8-sig").name` is not `"utf-8"` - the decision's own near-miss claim,
which is true of `codecs.lookup` and would not be true of a name comparison. Requirement 3 is
`_reject_lossy_multipart_control_fields`, and it inspects **only** `_MULTIPART_CONTROL_FIELDS` and
only `str` values, exactly as written.

**Decision 19 - yes, item by item.** `_HOST_META_KEYS_BY_HEADER` covers `host` and
`x-forwarded-host`; names are `.lower()`ed after a Latin-1 decode (casing normalized, not trusted);
duplicates are `",".join`ed (so two `Host` headers become an invalid host and are refused rather
than one being picked); values are Latin-1 decoded; `scope["server"]` supplies
`SERVER_NAME` / `SERVER_PORT` with Django's own `"unknown"` / `"0"` in the `else`; only
`DisallowedHost` becomes a denial; the denial is Channels' own `WebsocketDenier`; and
`routers.py` really does apply it **outermost**, so an injected consumer sits inside it by
construction. The two deliberately-unprojected `META` keys are verdict-neutral for the reason the
docstring gives - both feed only the no-host branch's `":port"` suffix, which `split_domain_port`
strips before `ALLOWED_HOSTS` is matched.

**So the two custodian corrections from earlier today land, and the two passes that said "no
further spec edit is required" were right about Decision 17 and Decision 19.** They were checking
the two decisions the round amended. I checked the round's whole shipped boundary against the spec,
and that is where the one divergence is.

### The extra check `worker-1.md` gives me: were the builders' on-disk amendment lists discharged?

Six `## Required spec amendments` sections across the three cohort artifacts (pass 1 and pass 2).
Audited every item against the spec and the rationale companion by **whitespace-normalized string
probe**, not by eye, because these are multi-line prose claims a line-oriented `grep` misses.

**Discharged** - every amendment that named a spec/code **divergence**:

- revocation **A1** (the lock's owner is the **adapter** instance, not the consumer's) - Decision 16
  now says "owned by the connection's adapter instance". This one was a genuine falsification.
- HTTP **P2-1** (Decision 17's condition 1 stated a fallback chain) - now three independent
  requirements, "emphatically **not** rungs of a fallback chain", outcome table 6 -> 10 rows.
- the M3 literal (Decision 19 + test-plan row 46 name `"unknown"` / `"0"` and the `"unknown:0"`
  denial).
- plus the five falsified sentences the custodian pass found that no finding named, including the
  **inverted** edge-case bullet.

**Not discharged**, and each is an **enrichment** rather than a falsification - the spec is silent,
not wrong. Dispositions, so none closes by omission:

| Amendment | Disposition |
|---|---|
| revocation **A3** - name `revalidate_operation_actor` / `send_revalidated_operation_frame` in the spec | **declined.** `## Helper-reuse obligations` already binds the contract ("every decision … lives in the shared function"); pinning private symbol spellings in a contract document couples it to internal naming, and the spec is already 226KB against `## Spec rationale extraction`'s explicit size concern |
| revocation **A4** - name `_INFORMATION_BEARING_FRAME_TYPES` | **declined**, same ground. Decision 16 already enumerates the gated types normatively, which is the contract; the constant is its implementation |
| revocation **A5** - name row 27's revoked-idle fixture | **declined.** A test-plan row states the property to prove; which fixture proves it most strongly is the builder's, and `tests/test_routers.py` records it at the row |
| revocation **A6** - row 37 should say the lock's *placement* is asserted at the production call site because `channels.testing`'s `base_send` never suspends | **carry-forward, recommended.** This is the one I would land: it is a `BUILD.md` `### Harness-impossible interleavings` note, and without it a future reader deletes the call-site assertion as redundant with the wire checks - which is precisely how the "release early" mutant passed the whole suite once already |
| revocation **A7** - row 34 should name the two observables (`emitted`, the generator's `finally`) instead of "cancelled or completed" | **carry-forward, recommended.** "Never delivered" alone is satisfiable by an implementation that never generated the result. The shipped row already asserts both observables; the spec row is weaker than what is pinned |
| revocation **A9** - a test-plan row for the outbound checkpoint reached from the connection's **own** task | **carry-forward, recommended.** `test_the_subscription_limit_error_frame_is_gated_from_the_connections_own_task` is a shipped security row with no spec row, i.e. deletable by a future pass with nothing to appeal to |
| revocation **A10** - Decision 16 should carry the measured hot-path number | **not mine.** This is the substance of **M5**, a pending maintainer decision the dispatch forbids re-litigating. The number exists on disk (`bld-review-2-ws_revocation.md` §3); whether it belongs in the spec is the same question as whether the round owes a declaration |
| revocation **A11** - Decision 11 should say the window is read as a plain attribute, never through a `getattr` default | **declined, because the rule already lives where it binds.** `consumers.py::_actor_is_current` carries it as an eight-line comment at the exact line, naming the performance cliff and why a default would be unreachable. A builder reads the site, not Decision 11 |
| HTTP **P2-2** - Decision 17 and Decision 7 must state the multipart **POST** scoping | **this one is a genuine divergence, and I fixed it.** See below |
| host cohort **A4** (log the third fail-closed path) | **maintainer's**, correctly routed by the builder as a contract-level observability question; recorded, not built |
| revocation **A8** / L8 (`docs/README.md`, `README.md`, `docs/TREE.md`) | **Slice 5's**, and confirmed captured - see below |

The recorded-not-implemented rule exists so an amendment cannot vanish silently. Recording each
disposition here is how it is discharged; none of A3-A11 is a false statement on disk, so none is
`revision-needed`, and `revision-needed` would in any case route to Worker 2, which cannot edit the
spec. **A6, A7 and A9 are a single short custodian pass** if the maintainer wants them - three
test-plan sentences, no code, no re-loop.

### The one genuine spec/code divergence, found by running the check rather than inheriting it

`views.py::_is_multipart_form_post` is `request.method == "POST" and request.content_type ==
_MULTIPART_CONTENT_TYPE`, and `_enforce_request_body_limit` returns outright on `GET` before it
reads anything. Against that:

- **Decision 7 step 3 said "For a multipart request the view applies step 1 and then hands off to
  Django's `MultiPartParser`."** For a multipart request on any method other than POST that is
  **false**: `_is_multipart_form_post` is `False`, so the request takes the *counted* path (step 2)
  and is bounded like any other body. The code's direction is the stricter one and is right - Django
  parses no form there - but a reader deriving behaviour from Decision 7 got the wrong answer for a
  concrete request shape, and it is the shape **this round changed** (L1). Decision 7 also never
  said `GET` is outside the cap at all.
- **Decision 17 stated its three requirements with no scope**, while the shipped guard is scoped by
  the same discriminator.

Both are now stated. This is exactly the class `worker-1.md`'s extra final-verification check exists
for: the code was right and the contract document was wrong, which no `Status:` chain catches - and
neither prior pass looked at Decision 7, because the round's amendments pointed at 17 and 19.

### Ruling on the three prose corrections Worker 3 escalated, and the routing

All three are **false reasons attached to correct choices**, and I confirmed each rather than
accepting it.

1. **The M6 row's docstring** (`tests/test_views.py:1717-1718`) claims "A row asserting only
   ``is False`` would still pass while that happened." Worker 3 measured that false - with the arm
   removed, `_canonicalizes_to_utf8(b"utf-8")` *raises*, so an `is False` assertion errors and fails
   too (probe: 6 passed -> 6 failed). The **choice** of the boundary-level shape is right on a true
   reason the docstring should state instead: it pins the status code **and** the shared Decision-9
   reason, neither of which a helper-level assertion pins, and it matches the sibling row's idiom.
2. **The build report's `### Implementation notes`** says the live tier "cannot express it without
   inventing middleware the example project does not have." **False, and I verified it on disk:**
   `test_transport_api.py::_LatinOneEncodingMiddleware` (a class attribute `encoding =
   "iso-8859-1"` assigned onto `request.encoding`) and `_with_a_middleware_that_sets_the_encoding()`
   both exist, added by **this same round** for M1's live rows and used at `:1995` and `:2020`. The
   conclusion stands on the right ground: the refusal lives on the **shared** mixin method both
   transports call, and the funnel from that `HTTPException` to a wire `400` is already pinned by
   the M1 live rows travelling the identical path, so a live non-`str` row would re-prove the funnel
   rather than the arm.
3. **`### Files touched` says "+33 lines"; `git diff --numstat -- tests/test_views.py` reads
   `34 0`.** Confirmed by running it. **Closed here**, by this sentence: that number lives only in a
   per-cycle `bld-*.md` scratchpad, which `START.md` says the next cycle regenerates, so it needs no
   pass of its own - it needs a correct number on disk beside it, which it now has.

Plus the predecessor's open nit: **`views.py::_form_encoding_is_utf8`'s docstring numbers its two
conditions in the reverse of the code's evaluation order** (docstring condition 1 = the effective
encoding; the code tests the declaration first). Confirmed by reading both. Harmless - `and` is
commutative over two pure predicates - and the spec's outcome table attributes the both-fail rows to
"requirement 2", which **is** the code's first test, so spec and code agree. Only the docstring
reads as a sequence the spec explicitly says does not exist.

**Routing, recorded on disk so it cannot be lost.** Items 1 and the `views.py` nit are routed into
**Slice 5**, per Worker 0's ruling, and I agree with the routing on the merits: Slice 5's plan
already names `django_strawberry_framework/views.py` and `tests/test_views.py` in its writable list
and already carries a "Slice-2 prose corrections" checklist sub-check, so this avoids a spawn for
cosmetics and puts prose edits in the pass that owns those files.

**One caveat that must reach Worker 0 or the routing will be refused exactly as it was here.**
Slice 5's plan scopes those two files narrowly - `views.py` to "the one authorized docstring re-word
(sub-check 7)" and `tests/test_views.py` to "the docstring first line". These two corrections are a
**second** edit in each file. This round's builder declined the `views.py` nit for precisely that
reason ("`views.py` is production code and this pass's writable list excludes it"), which is correct
behaviour, so the widening has to be written into Slice 5's plan or its dispatch prompt - naming
`_form_encoding_is_utf8`'s condition numbering and the M6 row's `is False` sentence - or Slice 5's
builder will decline them on the same ground and the routing will have bought nothing.

### The false baseline note in the record, corrected

The builder's `### Files touched` states "**HEAD moved during this pass's dispatch window** …
the maintainer committed (`10c50722`, `07e5de10`, `84c6075b`)". I did not rewrite that section;
this is the correction beside it, and I re-measured rather than relaying two prior refutations:

- `git rev-parse HEAD` -> `84c6075bd666a05e2a3cab3e363d95a1e2d421cc`.
- `git reflog --date=iso` places `84c6075b` at **2026-07-28 17:45:07**, `07e5de10` at 17:44:45,
  `10c50722` at 17:44:31, `a5e8e91f` at 17:44:00, and records **no entry after** `84c6075b`. `HEAD`
  has not moved since 17:45:07. `git log --format='%h %ad'` agrees with the reflog on all four.
- Those commits predate the **predecessor review**, let alone the builder pass after it: the
  predecessor's own opening section already reasons from `10c50722` ("the maintainer squashed round 2
  **and** its remediation into one commit") and attributes +100 rows to `a5e8e91f` as "a commit the
  builders' sweeps predate". A pass cannot narrate as mid-pass a commit the previous pass already
  reasoned from.

**So the production files were already committed and clean when the builder's pass began.** The
builder's *conclusion* - the mutated-and-restored `views.py` is byte-identical to `HEAD` - is true,
and I re-confirmed it: `shasum -a 256 django_strawberry_framework/views.py` and
`git show HEAD:django_strawberry_framework/views.py | shasum -a 256` both give
`dedcecec1687412785af2add94b42599e45c3205056ae4f8d4de21bcf623e09a`, and the path appears in neither
`git status --porcelain` nor `git diff --stat`. Only the causal narration is false. It is corrected
here rather than in place because a false baseline note is what a later pass reasons from, and the
sentence as written would tell a reader the artifact chain's numbers were measured against a tree
that no longer exists. **They were not: every number in this artifact was measured against the tree
as it stands.**

### Gates

All read-only; no `--cov*` flag anywhere; no `git` command that writes; no `ruff --fix`, no bare
`ruff format`, and `check_trailing_commas.py` always with explicit paths.

- `uv run pytest --no-cov` -> **5202 passed, 40 skipped**. Matches the dispatch baseline exactly.
- `uv run pytest tests/test_views.py tests/test_routers.py --no-cov` -> **266 passed** = 144 + 122,
  both baselines matched.
- `uv run python scripts/check_spec_glossary.py --spec docs/spec-065-transport_security-0_0_15.md`
  -> `OK: 37 terms`, exit **0** - re-run **after** my spec edit.
- `uv run ruff format --check .` -> `405 files already formatted`; `uv run ruff check .` ->
  `All checks passed!`. Read-only only; this pass touches no source, so the open
  `AGENTS.md:15`-vs-scoped-`ruff` conflict is sidestepped rather than resolved.
- `git diff --check` -> exit **0**.
- `uv run python scripts/check_trailing_commas.py --check docs/spec-065-transport_security-0_0_15.md docs/spec-065-transport_security-0_0_15-rationale.md docs/builder/bld-review-2-w3_residual.md`
  -> exit **0**.
- Spec integrity after my edit, checked mechanically rather than by eye: every in-page `](#anchor)`
  resolves against a real heading (**0** unresolved); every `][ref]` use has a definition in both
  the spec and the rationale companion (**0** undefined); no inserted line exceeds 100 characters;
  and the spec still contains **zero** occurrences of "review round", "Worker ", "pass 2" or
  "final verification", so `BUILD.md` `## Spec rationale extraction`'s "the spec never narrates its
  own history" still holds by measurement.
- `git status --short` start vs end: **identical set of paths.** The only files I wrote are my three
  writable ones, two of which were already dirty. No unexpected churn, nothing reverted, no
  `git checkout`.

### Carried, not re-litigated

- **M4** and **M5** remain pending **maintainer** decisions in the build plan's
  `## Open maintainer decisions`. Untouched. (A10 above is M5's substance and is left there.)
- **L8** is Slice 5's and **is captured** - I verified it cannot close by omission:
  `bld-slice-5-docs_foldin.md` carries the `docs/README.md` #`"before every operation"`
  understatement at `:251`, the READMEs' three-wrapper corrections and their
  `DjangoWebSocketHostValidator` omission at `:218-224` and `:375`, and the `docs/TREE.md` missing
  rows at `:32-40` with the regenerate as sub-check 4.
- The `SERVER_NAME` / `SERVER_PORT` repetition in `consumers.py::_host_validation_request` **must
  not** be consolidated; it mirrors `django/core/handlers/asgi.py::ASGIRequest.__init__`'s own
  if/else item for item and that mirror is what the projection's oracle row asserts against.
  Re-recorded as examined.
- The `AGENTS.md:15`-vs-scoped-`ruff` conflict is the maintainer's line to reconcile. It is the
  fifth consecutive pass to note it.

### One correction to the plan's own record

`build-065-transport_security-0_0_15.md` `### Artifact Status: hygiene lapse in round 2` says
**three** violations. There are **four**: `bld-review-2-ws_revocation.md` and
`bld-review-2-ws_host_boundary.md` have no `Status:` line at all (2), `bld-review-2-http_boundary.md`
reads the illegal `Status: built (pass 2), dirty, uncommitted.` (3), and
`bld-review-2-w3_review.md:8` reads `Status: **revision-needed** - five Medium findings …`, which is
a legal value with commentary appended and therefore not one of the five bare legal values either
(4). Not fixed here: those artifacts are committed, the passes that owed the lines are closed, and
the plan is Worker 0's file. Reported so the count in the record is right. This artifact's own
`Status:` is one bare legal value, set by me, and is the fourth round-2 artifact to carry a
well-formed one.

### Summary

Review round 2 of card 065 is **closed**. Its six dispatched findings (Blocker 1, High 2, High 3,
Medium 4, Medium 5, Low 6) are each closed by a real bound with a regression that bites; the W3
review's M1 / M2 / M3 and this artifact's own M6 are closed with them; no finding was closed by a
relabelling and no fix introduced a fail-open shape. The shipped transport boundary and the spec now
agree everywhere I could falsify either - after one custodian correction of my own, which is the
whole reason the check is run rather than inherited. The three escalated prose corrections are ruled
on and routed, with the scope caveat Slice 5 needs; the builder's false "HEAD moved mid-pass" note
is corrected beside itself rather than in place. All gates green at the dispatch baselines.

### Spec changes made (Worker 1 only)

Two edits, both to close the **one** genuine spec/code divergence this pass found, plus their
change records. Nothing else in either file was touched; no decision was renumbered; no test-plan
row, slice-checklist sub-bullet or DoD box was edited.

1. **`docs/spec-065-transport_security-0_0_15.md`, `### Decision 7`** - a new paragraph,
   "**Method scoping, stated because steps 2 and 3 split on it**", inserted after the four numbered
   steps and before "**How the body is measured…**". Reason: step 3 claimed a hand-off to
   `MultiPartParser` for "a multipart request", which is false for a multipart request on any method
   other than POST - `views.py::_is_multipart_form_post` is `False` there, so the code takes the
   counted path instead - and the decision never stated that `GET` is outside the cap at all
   (`views.py::_enforce_request_body_limit` #`'request.method == "GET"'`). Triggered by the HTTP
   cohort's undischarged pass-2 amendment **P2-2**, whose divergence I re-verified against the code.
2. **`docs/spec-065-transport_security-0_0_15.md`, `### Decision 17`** - one paragraph inserted
   after requirement 3 and before "Requirements 1 and 2 accept exactly the codec aliases…", stating
   that all three requirements apply to a multipart **POST** and nothing else, through the same
   discriminator, and why a stale `multipart/form-data` `Content-Type` on a `GET` must not be
   refused. Reason: the requirements were stated with no scope while the shipped guard
   (`views.py::_enforce_multipart_form_encoding` #`"if not _is_multipart_form_post(request):"`) is
   scoped. Same amendment, same divergence, the other half of it.
3. **`docs/spec-065-transport_security-0_0_15-rationale.md`** - one **Change record** appended to the
   `### Decision 7` entry and one to the `### Decision 17` entry, each naming what changed, the round
   that caused it, and (for Decision 7) that no alternative was rejected because the only alternative
   was leaving the spec silent. Required by `BUILD.md` `## Spec rationale extraction`: the companion
   is keyed to the spec decisions and must carry every change a decision has undergone.

Spec `224,788 -> 226,343` bytes (+1,555); rationale companion grew by the two change records. The
corpus ratchet governs `BUILD.md`, `ARTIFACT.md` and the four `worker-*.md` role files, none of
which this pass edited.

No other spec edit was needed: **Decision 17 and Decision 19 match the shipped code**, verified
against the code and not against the prose, and the two passes that said so were right about the two
decisions they checked.

### Final status

`final-accepted`.
