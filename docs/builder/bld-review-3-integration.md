# Build: Worker 3 adversarial review — the integration consolidation and the concurrent claim-audit custodian pass (card 046, transport_security / 0.0.15)

Spec reference: `docs/spec-046-transport_security-0_0_15.md` (whole file) and its rationale
companion. Build plan: `docs/builder/build-046-transport_security-0_0_15.md`.
Artifacts reviewed: `docs/builder/bld-integration.md` (cohort A, Worker 2) and
`docs/builder/bld-custodian-3-claim_audit.md` (cohort B, Worker 1).
Status: review-accepted

## Scope, method, and what this pass did NOT do

Two cohorts, reviewed side by side because cross-cohort convergence is invisible to either.
**Every claim below was settled by anchor string or by execution; no claim was accepted on
either artifact's prose, and no line number was trusted** (both cohorts wrote into a tree the
other was reading).

Files written by this pass: this artifact, the two reviewed artifacts' `Status:` lines, and
`docs/builder/worker-memory/worker-3.md`. **No source, no test, no spec, no DB.** Nothing was
reverted; no `git` write command ran (`status`, `diff`, `show` only). `docs/GLOSSARY.md` was
verified by rendering to a scratchpad path (`--md <scratch>`) rather than over the tree, so the
verification itself wrote nothing.

`scripts/review_inspect.py` was **skipped, with reason**: the diff adds **zero** lines of new
logic to any package file (proved by AST identity below) and 39 insertions to one test file, so
none of `worker-3.md`'s three triggers fires. No shadow file was used or cited.

M4 and M5 are pending maintainer decisions and are not re-litigated. `conf.py:117`,
`auth/mutations.py`, `auth/sessions.py`, `docs/feedback.md`, `docs/feedback2.md`, `drys.md`,
`vulns.md`, `TODAY.md`, `tests/test_views.py` were read only.

---

## Verdicts

| Cohort | Artifact | Verdict (pass 1) | Verdict (pass 2, after remediation) |
|---|---|---|---|
| A — integration consolidation (Worker 2) | `docs/builder/bld-integration.md` | revision-needed (2 Low) | **review-accepted** |
| B — spec custodian, nine corrections (Worker 1) | `docs/builder/bld-custodian-3-claim_audit.md` | revision-needed (1 Low) | **review-accepted** |

**All three Lows are closed, verified against disk in pass 2 below.** The pass-1 findings are
left as written — this artifact is append-only — and each carries a `**CLOSED (pass 2)**` line.

Both cohorts' *substance* is verified correct end to end: every dispatched box landed, every
factual correction reproduces against source or under execution, and neither introduced a new
false statement. Both verdicts rest **only** on unresolved Low findings that carry no recorded
rejection reason, which `worker-3.md` `### Acceptance gate` does not permit me to wave through
("Never accept a slice with unresolved High, Medium, or Low findings that lack a recorded
rejection reason"). Each fix is one clause or one number.

---

## Review (Worker 3)

### High:

None.

### Medium:

None.

### Low:

#### A-L1 — `bld-integration.md`'s recorded net line delta for the test file is wrong (`-49`; measured `-21`)

`### Files touched` states, for
`examples/fakeshop/test_query/test_transport_api.py`: "Net -49 lines, no assertion changed."

```
$ git diff --stat -- examples/fakeshop/test_query/test_transport_api.py
 1 file changed, 39 insertions(+), 60 deletions(-)
```

Net is **-21**. The file was clean at HEAD before this pass (it is one of the four `M` lines the
build report itself attributes to this pass), so no concurrent writer can absorb the difference,
and **CLOSED (pass 2)** — the bullet now reads `` `+39 / -60 (net -21)` ``, verified by anchor string
at `bld-integration.md #"(net -21)"`, and `Net -49` has no remaining occurrence in the file.

`git diff HEAD --stat` gives the same numbers. Nothing behavioural turns on it — the
*measurable* claims in the same bullet ("no assertion changed", the helper extraction, the nine
rewired sites) all verified true. It matters because this artifact is the record the maintainer
reads at commit, and this build's own recurring lesson (`### Seven further spec/code
divergences`, F3/F8) is that **a count stated in prose replicates**. Recommended change: replace
`Net -49 lines` with the measured `+39 / -60 (net -21)`, or drop the figure.

#### A-L2 — the L-A comment landed in `exceptions.py` contradicts itself within six lines: "two siblings use" one spelling, then "Three spellings"

```django_strawberry_framework/exceptions.py:74:80
        # Deliberately NOT the ``<unprintable {T}>`` spelling its two siblings use
        # (``_safe_arg_repr`` and ``DjangoStrawberryFrameworkError.__str__``): those
        # render STANDALONE, while this one is a FRAGMENT interpolated into prose
        # ("got an unprintable Foo."). Three spellings of one placeholder is the
        # cost of that grammatical difference - do not unify them, or one of the
        # three reads wrongly at its own site.
```

**CLOSED (pass 2)** — the last sentence now reads "Three **sites** carrying two **spellings** is
the cost of that grammatical difference - do not unify them, or one of the three **sites** reads
wrongly." Read at the site: the two-siblings clause is unchanged and now agrees with it, the
three sites and two spellings are counted correctly, and the spellings are still deliberately
NOT unified. `exceptions.py` remains AST-identical to `HEAD` modulo docstrings (re-run), still
0 non-ASCII, scoped `ruff format --check` / `ruff check` clean.

Measured: `exceptions.py` carries **three sites** and **two distinct spellings** —
`<unprintable {T}>` at `_safe_arg_repr` (`:33`) and at
`DjangoStrawberryFrameworkError.__str__` (`:115`), and `an unprintable {T}` at
`describe_value` (`:80`). The comment's own first clause says so ("the spelling its **two
siblings** use"), then its fourth sentence prices the cost as "**Three** spellings". Both
cannot be true. The inherited finding L-A carries the same slip in the plan section ("three
spellings of one placeholder"), so this is inherited rather than invented — but a comment whose
entire job is to bind a future writer must not be internally refutable, or the writer resolves
the contradiction by editing. Recommended change: "Three sites, two spellings" (or "the third
site of one placeholder, in a second spelling"); do not unify the spellings, which remains the
correct call. No test expectation is affected.

**Attribution note, in Worker 2's favour:** the plan's step 5 mis-attributed the `:33` site to
`_safe_type_name`'s own fallback. It is in `_safe_arg_repr`. The landed comment names
`_safe_arg_repr` — Worker 2 corrected the plan rather than inheriting it, and did not record
having done so. That is the right direction and the reason A-L2 is Low rather than Medium.

#### B-L1 — `bld-custodian-3`'s not-fixed item 1 says the six guarded probe calls are "each in its own `try`"; two of the six share one

`## Divergences noticed and NOT fixed`, item 1: "the code guards six call sites.
`_declares_seekable`'s `seekable()`, the position `tell()`, `stream.seek(0, SEEK_END)`,
`_position_restored`'s restoring `seek`, its verifying `tell()`, and the `end - position`
subtraction — **each in its own `try`**."

**CLOSED (pass 2)** — item 1 now reads "six guarded call sites across **five** `try` blocks
(`_position_restored` guards its restoring `seek` and its verifying `tell()` together in one
`try`; `_declares_seekable` carries one; `_measured_remaining` carries three)". That is exactly
the distribution `_request_body.py` has, and it is more precise than the replacement I
recommended. The record's load-bearing half (four in prose, six in code) is unchanged, and the
two spec sites remain deliberately un-edited, so no new falsity enters. One cosmetic short
line-wrap remains where the sentence was extended ("repeats the same / four-item list"); a
per-cycle artifact needs no stylistic cleanup (`START.md` "Temp artifact conventions"), so it is
not a finding.

Measured against `_request_body.py`: `_declares_seekable` guards `seekable()` in its own `try`;
`_measured_remaining` carries three (`tell()`, `seek(0, SEEK_END)`, the subtraction); and
`_position_restored` wraps **`seek` and the verifying `tell()` in a single `try`**. Six guarded
calls in **five** `try` blocks. The load-bearing half of the record — that the prose count of
four is a measured undercount, and that the two omitted calls are the ones correction 1 turns on
— is **correct and verified**; only the "each in its own `try`" clause is false.

It is Low, and it is recorded rather than waved through because this item exists to save the
next pass from re-deriving the measurement, and the next pass will dispatch a fix against the
number and shape stated here. Recommended change: "six guarded call sites across five `try`
blocks (`_position_restored` guards its restoring `seek` and its verifying `tell()` together)".
This is `bld-custodian-3-claim_audit.md` prose only; no spec edit follows from it.

#### B-L2 (routed to Worker 0 / Worker 1, NOT to cohort B) — the custodian artifact is absent from the plan's artifact list and its filename is outside `BUILD.md`'s naming scheme

`BUILD.md` `## Build artifact naming` licenses `bld-slice-<N>-…`, `bld-review-<R>-…`,
`bld-integration.md`, `bld-final.md`, and "The build plan must list every artifact before build
work starts." `docs/builder/bld-custodian-3-claim_audit.md` matches no form and does not appear
in the plan's `## Artifact list` (`build-046-…md:98-112`), while every other artifact of this
build does. It is nonetheless driven through a legal `Status:` chain and is `Status:`-legible, so
**CLOSED (pass 2) by Worker 0, along resolution path (a).** The plan's `## Artifact list` now
carries `docs/builder/bld-custodian-3-claim_audit.md` and
`docs/builder/bld-review-3-integration.md`, each with a one-line note stating that the list is
corrected rather than the file renamed because the name predates the finding. Read at the list;
both entries are present and every other artifact entry is unchanged. Whether `BUILD.md` gains a
fourth legal artifact-name form is a closeout question and stays with the maintainer.

no dispatch decision is impaired. **Not cohort B's to fix** — a worker may not edit the build
plan or rename its own artifact path mid-chain. Recorded here so it reaches the maintainer and
`bld-final.md`'s `### Deferred work catalog` rather than dying in this pass.

---

## Cohort A — every box verified, and how

`### Dispatched findings checklist` carries nine `- [x]`, plus a tenth box for `### Item C`.
Every tick has a matching landed fix; **no over-tick, no silently-unaddressed box.**

| box | verification | result |
|---|---|---|
| DRY-1 `_user_who_can_add_categories()` | `grep -c` → 3 occurrences (`:409` def, `:825`, `:1268`); the seven-line block appears **0** times; the function-local `Permission` import moved inside; the perm-cache-drop comment survives on the `return` | landed |
| DRY-2 `_post_bytes` rewiring | `grep -nE 'await \w+\(?\)?\.post\('` → **0**; the only surviving `.post(` sites are `:379` (the helper's own body) and `:1243` (posts a `dict`, so Django multipart-encodes it — correctly not routed through a helper that forces raw + `application/json`). The ninth (sync) site at `:1706` is genuinely the same duplication and its rewiring is right | landed, incl. the +1 site |
| M1 `routers.py` docstring | all four corrections present and each verified against `consumers.py` (below) | landed |
| L3 (a) `docs/README.md:360` | `multipart/form-data` **POST** + the one clause, verbatim | landed |
| L3 (b) glossary `request-body-cap` | ORM read: body contains "on a POST is a carve-out" **and** "The carve-out is POST-scoped" | landed |
| L3 (c) `views.py` `**Multipart, on a POST.**` | clause present, cites `_is_multipart_form_post` | landed |
| L1 `GlossaryTerm` id 529 | ORM: `'scope,.' in body` → **False**; anchor still `channels-request-adapter`; `grep -c "scope,\." docs/GLOSSARY.md` → **0** | landed |
| L-A `exceptions.py` | comment landed (see A-L2 for its internal inconsistency) | landed, with a Low |
| Floor verification | the scratch venv still exists and reports **Python 3.10.19 / Django 5.2**, exactly as recorded; the recorded focused scope reproduces **69 passed** | reproducible |
| Item C `_strawberry_patches.py` | verified by execution (below) | landed |

**M1, sentence by sentence against `consumers.py` — I re-derived each rather than reading the
build report's verdict.** Two checkpoints: `consumers.py:1-30` names admission and the outbound
information-bearing frame, and states why admission alone can never see a running subscription.
Socket close: `_REVOCATION_CLOSE_CODE = 4403` / `_REVOCATION_CLOSE_REASON = "Forbidden"`
(`:197-198`), and `:52-58` states frame suppression with no preceding operation error at either
checkpoint — "the close IS the rejection". `0.0` default: `:81-83` "revalidates at every
operation admission and every `next` / `data` / operation-scoped `error` frame". Cost:
`:269` "one session read per authenticated **checkpoint**". All four landed sentences match, and
the three genuinely-true window sentences (positive-value trade, construction error, the
`consumers.py` pointer) survive. `grep -rn "before every operation"` over `.py` / `.md` outside
per-cycle `bld-*.md` → **no hit**, so the drifted telling is gone tree-wide.

**Item C / correction 8, settled by execution** (`DJANGO_SETTINGS_MODULE=config.test_settings`,
`PYTHONPATH=examples/fakeshop`, a real `DjangoGraphQLView(schema=None)`; in-process only, no
file mutated):

```
mro parse_json owners: ['_RequestBodyBoundaryMixin', 'BaseView']
patch installed: True
patched   b'42'    -> HTTPException 400 'The GraphQL request body must be a JSON object ...'
patched   b'[1,2]' -> HTTPException 400 (same)
unpatched b'42'    -> 42
unpatched b'[1,2]' -> [1, 2]
unpatched utf-16 body -> HTTPException 400 'Unable to parse request body as JSON'
```

The gate is mount-blind for the body-envelope guard and the wire contract is view-owned and
ungated — which is exactly what the corrected `_strawberry_patches.py` docstring and spec
`:1287-1288` / `:1318-1322` now say. The live row it cites
(`test_the_upstream_bug_workaround_still_respects_its_own_opt_out`) exists and asserts `500`
opted-out / `400` patched against the **package** mount. Verified, not accepted.

### Zero-boundary claim, proved rather than read

`### Failability proofs` reads the required literal `None; this pass introduced no new
boundary.` I did not take that on prose. For each of the four touched package files I parsed
HEAD's copy and the working copy, normalised every module / class / function docstring to a
constant, and compared the ASTs:

```
routers.py            AST-equal (docstrings normalized): True
views.py              AST-equal (docstrings normalized): True
exceptions.py         AST-equal (docstrings normalized): True
_strawberry_patches.py AST-equal (docstrings normalized): True
```

So the production diff is **exclusively** docstring and comment text: no guard, gate, cap,
rejection path, or validation branch, and no statement added, removed, or reordered inside any
function body. That also independently discharges the `### Hot-path budget` literal (`Not
applicable`) and both of the plan's stated falsification conditions.

**Failability-proof re-run set: EMPTY, and legally so.** `worker-3.md`'s mandatory floor binds
"every boundary whose recorded failing-row count is 3 or fewer, and every boundary on a security
or data-isolation decision"; an empty re-run set is legal exactly when the diff introduces no
boundary meeting the floor. The AST identity above is the proof that it introduces **none** —
this is not a subset I chose, it is the whole population being zero. Boundaries accepted on
Worker 2's record: none, because none was recorded and none was owed.

### Fail-open shape review

Nothing to hunt: no executable production line changed, and the one executable test-tier change
is `await _post_bytes(client, X, path=P)` for `await client.post(P, data=X,
content_type="application/json")` — the helper's default supplies the identical content type
(`_post_bytes` body read at `:377-379`). No clamp, `getattr` default, `or` fallback, bare
`except`, or truthiness-on-absent was introduced or touched.

### Cross-cohort duplication review

The two cohorts corrected the **same** contract (Decision 9's "only mount" scoping) on opposite
sides of the partition — cohort B in the spec, cohort A in `_strawberry_patches.py`'s docstring.
I read both tellings against each other and against the executed behaviour: they agree, and
neither is a paraphrase of a third shape. Cohort A recorded that it read spec `:1275-1292` for
the contract and did not write it; the spec's `:1287-1288` wording it reports is exactly what is
on disk, so the cross-boundary flow was read-only as required.

No convergent rejection paths, status codes, or error-message shapes were added by either cohort
(zero executable change across the round), so the class of finding that produced three near-copy
400/413 shapes in a prior round cannot exist here. The L3 clause is **one** clause across four
surfaces, confirmed by reading all four; no fifth phrasing entered the tree. Punctuation differs
between the glossary's colon form and `docs/README.md`'s dash form; the wording is identical, so
this is not a fifth phrasing.

### DRY findings

- **None new.** `_user_who_can_add_categories()` has two real callers, is module-local to the
  live tier, and matches the file's own helper idiom — it survives the existence challenge
  (deleting it and inlining restores a verbatim seven-line duplicate at two sites).
- The plan's three verified-and-rejected non-consolidations (`_JSON_PARSE_REASON` double-naming,
  the sync/async colour pairs, the cross-tree test-helper class ruling) were spot-checked and I
  do not re-open any of them; the reasons recorded at their sites are sound and mechanical.
- The three surviving `.post(` sites are correctly non-callers, enumerated above.

---

## Cohort B — the nine corrections, and the ten not-fixed records

**All nine landed, none re-litigated, and none introduced a new falsity.** Four were settled by
execution rather than reading.

| # | verification | result |
|---|---|---|
| 1 (HIGH) — the over-reported-position inversion | source: `_measured_remaining` calls `_position_restored(stream, position)` **before** `remaining = end - position` is reachable; `_position_restored` returns `False` when the verifying `tell()` disagrees; `body_exceeds_limit` then logs `_CORRUPTED_PROBE_LOG_MESSAGE` (`warning`) and returns `True` with nothing read. Spec `## Edge cases` (`:2397-2403`) and test-plan row 15 (`:2589-2610`) now state exactly that, with the two directions as separate rows and the genuinely-empty body named as the *control*. `tests/test_views.py::test_a_stream_reporting_a_position_past_its_end_is_refused_rather_than_read` asserts `413`, `_BODY_LIMIT_REASON`, `stream.requested == []`, `stream.delivered == 0`, `hasattr(request, "_body") is False`, and the single log record. The widened "a **restore the probe cannot prove**" wording landed at both narrowed sites | **correct** |
| 2 — lock on the consumer, not the adapter | `consumers.py:656-657` assigns `self._revocation_lock` / `self._revocation_observed` inside `GraphQLWebSocketConsumer.__init__`; the class docstring says "per-INSTANCE … one consumer instance is exactly one connection"; nothing is assigned on `_RevocationGatedWebSocketAdapter`. Spec `:1895-1896` now reads "owned by the package's consumer instance (Channels constructs exactly one per connection…)". `grep "adapter instance\|on the adapter"` over the spec → **0 hits** | **correct** |
| 3 — DRY bullet, two homes | timestamp is `scope[_REVALIDATED_AT_SCOPE_KEY]` (`:214`, read `:453`, written `:485`, only when `window > 0.0`); spec `:2257-2259` now names the two homes and keeps the protocol-cache contrast verbatim | **correct** |
| 4 — "two-line delegate" at three sites | `grep -c "two-line\|two line"` over the spec → **0**. Both admission overrides have three-line bodies (`if not await revalidate_operation_actor(self): / return / await super()…`), matching the new "two three-line subclasses … returns without admitting the operation if it refused". Spec `:209`, `:2000`, `:1446` all corrected; the DRY telling they were matched to is untouched | **correct** |
| 5 — `AllowedHostsOriginValidator` is not "only a factory" | **executed** at the installed channels 4.3.2: it substitutes `["localhost", "127.0.0.1", "[::1]"]` under `DEBUG` with an empty `ALLOWED_HOSTS`; Django's `get_host()` substitutes `[".localhost", …]`. The no-leading-dot divergence the correction adds to Decision 19 is real. `OriginValidator.__call__` reads `Origin` only — the kept claim holds | **correct** |
| 6 — the `DEBUG` + empty `ALLOWED_HOSTS` default | **executed**: `HttpRequest.get_host` source shows `allowed_hosts = [".localhost", "127.0.0.1", "[::1]"]`. Spec `:2461` now states it | **correct** |
| 7 — the upstream views' import list | **executed**: `strawberry/django/views.py` module-level imports are `json`, `typing`, `asgiref.sync.markcoroutinefunction`, `cross_web`, four `django.*`, three `strawberry.http.*`, and `.context`. Spec `:660-662` now lists precisely "the standard library, `asgiref`, `cross_web`, `django`, `strawberry.http`, and their own `strawberry.django.context` sibling"; the surviving conclusion (no optional-import guard, `asgiref` is Django's own hard dep) is right | **correct** |
| 8 — Decision 9's "only mount" | **executed** (the probe table above). `grep "only mount"` over the spec → **0 hits**; all three sites now state it per mount. This was the one unsafe-direction correction and it is now right | **correct** |
| 9 — `APPEND_SLASH` unqualified | **executed**: `CommonMiddleware.get_full_path_with_slash` raises `RuntimeError` when `settings.DEBUG` and the method is `DELETE` / `POST` / `PUT` / `PATCH`. Spec `:2339` now says so, and `### Consumer-visible behavior` carries the `DEBUG`-split | **correct** |

**Recorded sizes reproduce exactly.** The artifact states spec `229,630 -> 233,292` and rationale
`73,718 -> 89,195`, "measured in characters". Measured: **233,292** and **89,195** characters
(`len(open(p, encoding="utf-8").read())`). `wc -c` gives 234,176 / 89,577, i.e. the multi-byte
dash count — the artifact's unit label is correct and the numbers are exact. That also proves
**no write landed on either file after the pass closed.**

**The rationale companion** carries all nine change records, each keyed to the decision named in
the artifact's table (Decisions 6, 7, 9, 11, 16, 17, 19, the DRY section, and the non-decision
sections), read at their headings. The non-decision opener does read "**Four** corrections" as
claimed. The three new link definitions (`s65-borrowing-posture`, `s65-consumer-visible`,
`s65-current-state`) are defined and used, and `[s65-dry]` resolves.

### The ten not-fixed records — accuracy verified

Asked to verify at least 1, 2, 5, 7; **all four verified, plus 3, 4, 10.**

1. **Accurate in substance, imprecise in one clause** — the count of guarded calls is six against
   the spec's four (both spec sites are internally consistent at four, so leaving them was
   right); the "each in its own `try`" clause is false. **This is finding B-L1.**
2. **Accurate.** `consumers.py:371` says "lets the derived adapter stay a two-line delegation";
   `_RevocationGatedWebSocketAdapter.send_json`'s body is four lines (type test, delegating
   `await super()`, `return`, the gated call). `consumers.py` is in neither cohort's write list —
   the record's own conclusion, that it needs routing, is right.
3. **Accurate.** Spec `:2250` prices the handler subclasses at "a single `await` and a
   `super()` call each"; each body literally holds two `await` expressions. The natural reading
   defence is fair, and the record correctly predicts a literal-counting reviewer will raise it.
4. **Accurate.** `## Implementation plan` row 4 (`:2213`) reads "the adapter-level outbound-frame
   gate, its connection-local lock and its one close code"; with corrections 2 and 3 landed the
   "its" invites a reading the spec makes nowhere else, and the cell states no ownership
   location, so it is not false.
5. **Accurate.** `consumers.py:209-214`'s comment explains only the key's collision-safe
   namespacing; no "why the scope rather than the consumer" reason exists in `consumers.py`, the
   spec, or the rationale. Correction 3 records the fact and invents no reason, correctly.
7. **Accurate as a record, and I refute it as a defect.** Both phrases exist —
   spec `:1152` ("This is the only new refusal…") and `:1337` ("previously a Channels-routed
   deployment never reached that adapter at all"). Both describe **shipped `0.0.14` behaviour**,
   not a spec revision, which is precisely the distinction `BUILD.md` `## Spec rationale
   extraction` draws ("a reader must never reconstruct what is currently true by applying a
   chronology **to it**"). A reader applying no chronology reads both correctly. The record's own
   judgement ("legitimate … worth a ruling, not a silent edit") is the right disposition; I do
   not raise it, and recommend Worker 1 close it as no-change.
10. **Accurate.** The surviving "only a factory" occurrence at `-rationale.md:1163` is inside the
    block introduced as the prior spec wording; editing it would destroy the record.

### On the alleged internal contradiction — refuted, no revision owed for it

The dispatch asks whether cohort B's artifact needs a revision because its verification section
claims "zero chronology phrases" while its own item 7 names two. It does not. The artifact's
actual claim is **phrase-specific**: "the spec contains zero instances of `review round`,
`Worker `, `round 3`, `now states`, `now says`, `was rewritten` or `custodian`". Executed:
`grep -inE "review round|Worker |round 3|now states|now says|was rewritten|custodian"` over the
spec returns **exactly one** line, `:2702`, and it is a **pytest-xdist** worker inside a
test-plan row — not a build worker. The claim holds as written. Item 7 flags a *different* class
(implicit changelog voice in shipped-version history), explicitly declines to fix it, and asks
for a ruling. Two claims about two different sets are not a contradiction, and the artifact is
more careful here than a paraphrase of it would be.

---

## Ownership partition — held, verified rather than assumed

The plan's partition (`build-046-…md:582-585`) gives cohort B the spec, the rationale, and its
own artifact; cohort A `routers.py`, `_strawberry_patches.py`, `views.py`, `exceptions.py`,
`test_transport_api.py`, `docs/README.md`, the glossary DB rows + regenerated `GLOSSARY.md`, and
`bld-integration.md`. **No violation found.**

- **`conf.py` was not touched by either cohort.** `conf.py:117` still reads
  `# declaration - EXCEPT for a multipart request, whose bound is the declaration` with **no**
  POST scoping — i.e. the fifth L3 surface is genuinely still open and genuinely still routed to
  the maintainer, not quietly fixed across the boundary. `grep "POST-scoped"` over `conf.py`,
  `tests/test_views.py`, `TODAY.md`, `README.md` → **no hit**.
- `auth/mutations.py`, `auth/sessions.py`, `docs/feedback.md`, `docs/feedback2.md`, `drys.md`,
  `vulns.md`, `TODAY.md`, `tests/test_views.py`, `KANBAN.*`, `docs/TREE.md`, `CHANGELOG.md`,
  `pyproject.toml`, `__init__.py`, `consumers.py` are all consistent with their pre-round state
  (`consumers.py` is not even dirty; the others carry only prior-slice or maintainer content, and
  `L-B`'s deferral is intact — `tests/test_views.py:1320`'s helper still lacks the live copy's
  `_patch_is_installed() is False` assertion).
- **Cohort B wrote no source and cohort A wrote no spec**, corroborated by the exact
  character-count reproduction above and by the AST identity of the four package files against
  HEAD modulo docstrings.
- Cohort A's tenth box (`### Item C`) sits in its build report rather than in Worker 1's
  `### Dispatched findings checklist`, which is the correct handling — Worker 2 may not edit
  Worker 1's list — and it is flagged for Worker 3 in `### Notes for Worker 3`. Worker 1 should
  audit it as a tenth tick at final verification.

---

## Gates run in this pass

| gate | result |
|---|---|
| `uv run pytest <the 6 touched/adjacent test modules> --no-cov` | **401 passed** — exactly the count cohort A recorded |
| `uv run pytest examples/fakeshop/test_query/test_transport_api.py --no-cov` | **69 passed** — the declared count, unmoved by the refactor |
| `uv run pytest tests/test_views.py --no-cov` / `tests/test_routers.py --no-cov` | **144** / **122** — the declared counts, unmoved |
| `uv run ruff format --check <the 5 touched .py paths>` | `5 files already formatted` |
| `uv run ruff check <the same 5 paths>` | `All checks passed!` |
| `uv run python scripts/check_trailing_commas.py --check <5 .py + docs/README.md + docs/GLOSSARY.md + both spec files>` | exit 0, no output — **explicit paths on every invocation**, so `drys.md` / `vulns.md` were unreachable |
| ASCII-only sweep over the 5 `.py` files (`ord(c) > 127`) | **0** in each |
| `uv run python scripts/build_glossary_md.py --check` | up to date, exit 0 |
| two-consecutive-regenerate byte-stability (`--md <scratch>/g1.md`, `--md <scratch>/g2.md`) | `cmp g1 g2` identical **and** `cmp g1 docs/GLOSSARY.md` identical — stable, and the tree was not written |
| `uv run python scripts/check_spec_glossary.py --spec docs/spec-046-…md` | `OK: 37 terms …` exit 0 |
| `uv run python examples/fakeshop/manage.py import_spec_terms --check` | `OK: 46 done cards have glossary links.` exit 0 |
| `uv run python examples/fakeshop/manage.py check` (via the ORM shell session) | no issues |
| `uv run python scripts/build_tree_md.py --check` | `docs/TREE.md is up to date.` exit 0 |
| `git diff --check` | exit 0 |
| `git status --short docs/spec-046-…-terms.csv` | clean — the CSV was not touched, as cohort B claims |
| glossary DB attribution, re-run | `GlossaryTerm` ordered by `-updated_date`: **only two** rows after Slice 5's `2026-07-29T00:37` batch — id 560 `request-body-cap` and id 529 `channels-request-adapter`, both `17:14`. Cohort A's attribution method reproduces exactly |
| floor venv spot-check | `<scratch>/floor/bin/python -c "import django,sys"` → **3.10.19 / 5.2**, as recorded |

No `--cov*` flag was used anywhere. No write-mode `ruff` ran, so the open `AGENTS.md:15`
conflict was not touched. No repo-wide `ruff` of any kind ran.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` is **empty** — `__all__` and the re-export
list are unchanged. (The build's authorized break is spec Decision 5's router constructor, which
this round does not touch: the four production files are docstring-only, proved by AST identity.)

### CHANGELOG sanity

Not applicable; neither cohort modified `CHANGELOG.md` (`git status --short` shows it clean, and
spec Decision 15 defers the quintet to the joint `0.0.15` cut).

### Documentation / release sanity

Both cohorts touched documentation surfaces, so read end to end:

- `docs/README.md:360`'s multipart paragraph now leads with **POST** and carries the one clause;
  its previously self-inconsistent third sentence ("on a multipart POST") now agrees with the
  lead. Nothing else in the file moved by this round (the remainder of its diff is Slice 5's
  transport section, already `final-accepted`).
- `docs/GLOSSARY.md` is **generated** and was verified only by two-consecutive-regenerate
  byte-stability plus the DB-row read, never by a clean `git diff` and never hand-edited. Both
  DB writes went through `GlossaryTerm.body`; `title`, `anchor`, and `status_text` are untouched
  (the seven `status_text` stamps remain the joint cut's, per Decision 15).
- No version string, card id, or shipped/planned status changed; `DONE-046-0.0.15` and
  `build_tree_md.py --check` are both still green; no "coming soon" / "planned" residue entered a
  file this round edited.
- No spec archival, no KANBAN movement.

### What looks solid

- **The zero-executable-change discipline.** A consolidation pass that corrects four docstrings
  and a comment and provably changes not one executable token is the cleanest possible shape for
  this work, and it is what makes the empty failability-proof set legitimate rather than
  convenient.
- **Both cohorts refused to inherit a number.** Cohort A re-measured the routed inline-`post`
  count to eight and then found a ninth the routed regex structurally could not see, and it
  rejected the routing record's "true and must survive" constraint after checking each sentence
  against `consumers.py` itself. Cohort B reverted its own draft edit rather than create a
  four-versus-five inconsistency it had no mandate to resolve. Both are the behaviour this build
  plan's own retrospective asks for.
- **Cohort B's execution-first method.** Corrections 5, 6, 7, 8, and 9 each rest on reading or
  running the installed dependency rather than on the spec's or the code's account of it, and all
  five reproduce.
- **The glossary DB discipline** — an idempotent guarded ORM script applied on top of concurrent
  churn, verified by byte-stability and an `updated_date` attribution that a reviewer can re-run.
  I re-ran it and it gives the same two rows.
- **`### Divergences noticed and NOT fixed`** is the highest-value section in either artifact, and
  seven of the ten records verified accurate on inspection (item 1 with the one clause noted).

### Temp test verification

None written. Every suspicion this pass had was settled by a focused run, a grep at an anchor
string, an ORM read, or an in-process execution probe, so a temp test would have proved nothing a
permanent row does not already pin. Nothing under `docs/builder/temp-tests/` was created, and
nothing needs promoting.

### Notes for Worker 1 (spec reconciliation)

- **Escalated: `B-L2`** — `docs/builder/bld-custodian-3-claim_audit.md` is outside `BUILD.md`
  `## Build artifact naming` and absent from the plan's `## Artifact list`. Resolution paths:
  (a) Worker 0 adds it to the artifact list under its current name and `BUILD.md` gains
  `bld-custodian-<N>-<slug>.md` as a fourth legal form at closeout (bounded by the corpus
  ratchet); (b) it is treated as a one-off out-of-chain pass and recorded as such in
  `bld-final.md`'s deferred catalog. Not a worker's call and not fixable inside the cohort.
- **Not-fixed item 7 should be closed as no-change.** I refute it as a defect above: both phrases
  describe shipped `0.0.14` behaviour, which the spec is entitled to state. A ruling recorded once
  stops it being re-raised every sweep.
- **Not-fixed item 2 still needs routing.** `consumers.py:371`'s "two-line delegation" against a
  four-line `send_json` body is correction 4's defect class in source, and `consumers.py` is in
  neither cohort's write list. It is a Low in a private module docstring, so it can ride the next
  pass that legitimately opens `consumers.py`; it should not be lost.
- **Cohort A's tenth tick.** `### Item C`'s box lives in the build report, not in the
  `### Dispatched findings checklist`. Audit it as a tick like the other nine; the fix it names is
  landed and verified by execution.
- **L9 and the `conf.py:117` fifth surface** remain maintainer items exactly as routed; I add no
  new evidence and re-litigate neither. M4 and M5 untouched.
- For the record: cohort A's `### Notes for Worker 1` forward-note (that the spec's DRY section
  should not restate a site count at all, since the routed count moved 6 → 8 → the measured 9) is
  well-founded — this pass found a third prose-count defect in the same build.

### Review outcome

`revision-needed` for **both** cohorts, on Low findings only.

- **Cohort A (`bld-integration.md`)** — A-L1 (the recorded `-49` net line delta; measured `-21`)
  and A-L2 (the `exceptions.py` comment's "two siblings … Three spellings" self-contradiction).
  Both are one-line edits inside files cohort A already owns. Everything else in the pass is
  verified correct: nine boxes plus Item C landed, zero executable change, no partition breach,
  every declared test count and the floor result reproduced.
- **Cohort B (`bld-custodian-3-claim_audit.md`)** — B-L1 only (not-fixed item 1's "each in its own
  `try`"; six guarded calls sit in five `try` blocks). All nine spec corrections are verified
  correct, four of them by execution, with no new falsity anywhere and the recorded character
  counts reproducing exactly.

Neither verdict reflects doubt about the work; both reflect `worker-3.md`'s acceptance gate,
which does not let a Low pass without a fix or a recorded rejection reason. If the maintainer
prefers to record a rejection reason for any of the three instead, that closes them equally.

---

## Review (Worker 3, pass 2) — re-verification of the remediation

Worker 0 reported all three Lows remediated, plus B-L2 closed by a build-plan edit. **Every
remediation was re-verified against disk by anchor string, never by line number, and the
production edit was re-verified by execution.** Each pass-1 finding above now carries its own
`**CLOSED (pass 2)**` line with the evidence; this section carries what is new.

### High: / Medium: / Low:

None. No new finding of any severity. Nothing outside the three remediated sites moved.

### The remediations, and how each was settled

| finding | remediation verified | verdict |
|---|---|---|
| A-L1 | `bld-integration.md #"(net -21)"` present in `### Files touched`; `grep "Net -49"` over the file → **no hit**; the surrounding claims in that bullet are textually unchanged. The new `### Remediation of review round 3 (Cohort A Lows)` section states the re-measurement (`39 60`) and matches what `git diff --stat` still reports | **closed** |
| A-L2 | read at `exceptions.py::describe_value`: "Three sites carrying two spellings is the cost of that grammatical difference - do not unify them, or one of the three sites reads wrongly." The `#"its two siblings use"` clause is unchanged and now consistent; three sites / two spellings is the measured truth; both `<unprintable {T}>` sites survive un-unified | **closed** |
| B-L1 | read at `bld-custodian-3-claim_audit.md` item 1: "six guarded call sites across **five** `try` blocks (`_position_restored` guards its restoring `seek` and its verifying `tell()` together in one `try`; `_declares_seekable` carries one; `_measured_remaining` carries three)". Matches `_request_body.py` exactly, and is more precise than my recommended wording | **closed** |
| B-L2 | the plan's `## Artifact list` now carries both previously-absent artifacts, each with its own justification note | **closed** |
| item 7 no-change ruling | recorded at `bld-custodian-3-claim_audit.md` item 7, "**Ruling recommendation (source: `docs/builder/bld-review-3-integration.md`…", explicitly "Recorded, not enacted: no spec edit made" — the correct handling: a recommendation attributed to its source, with the decision left to final verification | **as recommended** |

### Nothing else moved — proved, not assumed

- **The one production edit is still comment-only.** Re-ran the AST-identity probe against
  `git show HEAD:<path>` for all four package files, docstrings normalised:
  `exceptions.py`, `routers.py`, `views.py`, `_strawberry_patches.py` → **all True**. So the
  remediation added no executable token either, the zero-boundary and no-hot-path literals still
  hold unchanged, and my failability re-run set is still legally empty by population.
- **Cohort B touched only its artifact.** Spec and rationale character counts are **233,292** and
  **89,195** — bit-for-bit the pass-1 readings and the values cohort B recorded, so no spec or
  rationale byte changed during the remediation.
- `git status --short` is **33 lines**, identical to the count at the end of pass 1: no file was
  added, removed, or newly dirtied by the remediation.

### Gates re-run in this pass

| gate | result |
|---|---|
| `uv run pytest tests/test_exceptions.py examples/fakeshop/test_query/test_transport_api.py --no-cov` | **83 passed** — reproduces Worker 2's reported count exactly |
| `uv run ruff format --check django_strawberry_framework/exceptions.py` | `1 file already formatted` |
| `uv run ruff check django_strawberry_framework/exceptions.py` | `All checks passed!` |
| `uv run python scripts/check_trailing_commas.py --check <exceptions.py + both reviewed artifacts>` | exit 0, no output — explicit paths only, so `drys.md` / `vulns.md` stayed unreachable |
| ASCII-only sweep over `exceptions.py` (`ord(c) > 127`) | **0** |
| AST identity vs `HEAD` (4 package files, docstrings normalised) | all **True** |
| spec / rationale character counts | **233,292** / **89,195** — unchanged |
| `git diff --check` | exit 0 |

No `--cov*` flag. No write-mode `ruff`. No `git` write command — `status`, `diff`, `show` only.
No files written beyond this artifact, the two reviewed artifacts' `Status:` lines, and
`docs/builder/worker-memory/worker-3.md`.

### Public-surface check (re-run)

`git diff -- django_strawberry_framework/__init__.py` is still **empty** — `__all__` and the
re-export list unchanged.

### Notes for Worker 1 (spec reconciliation) — carried forward from pass 1, unchanged

The four items pass 1 routed to Worker 1 still stand and none was enacted by the remediation, as
intended: **item 7's no-change ruling** (now recorded with this artifact cited, awaiting Worker 1's
decision at final verification), **not-fixed item 2** (`consumers.py:371`'s "two-line delegation"
against a four-line `send_json` body — still in neither cohort's write list and still needing a
route), **cohort A's tenth tick** (`### Item C`, to be audited like the other nine), and **L9 /
`conf.py:117`** as maintainer items. M4 and M5 remain untouched and un-relitigated. The
`BUILD.md` artifact-naming question B-L2 surfaced is a closeout item for the maintainer, bounded
by the corpus ratchet.

### Review outcome (pass 2)

`review-accepted` for **both** cohorts.

- **Cohort A (`bld-integration.md`)** — A-L1 and A-L2 closed at their sites; the pass-1 body of
  verified work (nine dispatched boxes plus `### Item C`, zero executable production change,
  partition held, every declared test count and the floor result reproduced) is unaffected.
- **Cohort B (`bld-custodian-3-claim_audit.md`)** — B-L1 closed, and closed more precisely than
  recommended; all nine spec corrections remain verified, four of them by execution, with the
  recorded character counts still reproducing exactly.

No High, Medium, or Low finding is unresolved in either cohort, and none was closed by a recorded
rejection reason rather than a fix. Both artifacts advance to Worker 1's final verification.
