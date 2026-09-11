# Package build plan: channels_router / 0.0.14 (041)

Spec source: `docs/SPECS/spec-041-channels_router-0_0_14.md` (already archived; it never
received a `-rationale.md` companion, and its contract has drifted from HEAD)
Target release: `0.0.14` (shipped; the card is `DONE-041-0.0.14`)
Cycle type: **post-ship reconciliation round**, not a forward build. The code shipped; this
cycle proves nothing was skipped, and reconciles the spec with what actually landed.
Build rule: one slice at a time. Plan first, execute second, review third, reconcile fourth.
DRY rule: every slice must justify shared/duplicated patterns before merging.
Ownership partition: single cohort; see `## Ownership partition`.
Hot-path declaration: none. No slice changes executable code.
Floor-verification scope: none. No slice changes executable code, so no Django / Strawberry /
channels integration seam moves.
Pre-flight: passed on 2026-09-11 with two recorded deviations (below); baseline: dirty with a
concurrent cycle; cleanup: **not performed** — see deviation 1.

## Pre-flight deviations (recorded, maintainer-authorized)

1. **Step 3's artifact reset was NOT performed.** A concurrent session is mid-cycle on
   `spec-050` and its `docs/builder/build-050-*.md` / `bld-*.md` artifacts are live work,
   two of them dirty in the working tree. Deleting them is the one irreversible pre-flight
   mistake `worker-0.md` names. Instead, every path this cycle creates is verified absent and
   carries the `041` segment, so no 050 artifact can collide. Step 5's scratch clearing was
   likewise skipped for the same reason.
2. **Steps 1's "stop and ask" branch was waived by the maintainer** ("Ignore others concurrent
   work"). The dirty files are recorded below as baseline-dirty out-of-scope.

Steps 2 (`review_inspect.py` smoke on `routers.py`), 4 (`.gitignore` scratch paths), and 6
(`check_spec_glossary.py --spec docs/SPECS/spec-041-channels_router-0_0_14.md` → `OK: 30 terms`)
all passed. Step 7 (rationale extraction) is this cycle's Slice 1 deliverable rather than a
pre-flight gate, because the extraction and the reconciliation are one custodian judgement:
what a decision now says and what it used to say are decided together.

## Baseline-dirty out-of-scope files

Concurrent `spec-050` work. **Never edit, never revert, never stage.**

```
START.md
django_strawberry_framework/list_field.py
django_strawberry_framework/orders/sets.py
django_strawberry_framework/utils/querysets.py
docs/GLOSSARY.md
docs/builder/bld-final.md
docs/builder/bld-slice-3-sql_and_unit_contracts.md
docs/feedback.md
docs/spec-050-list_field_arguments-0_0_15.md
examples/fakeshop/db.sqlite3
examples/fakeshop/test_query/test_list_field_api.py
examples/fakeshop/test_query/test_list_field_async_api.py
examples/fakeshop/test_query/test_multi_db.py
tests/orders/test_sets.py
tests/test_list_field.py
tests/utils/test_querysets.py
```

`examples/fakeshop/db.sqlite3`, `docs/GLOSSARY.md`, `KANBAN.md` / `KANBAN.html` are the
tracked generated/binary files a concurrent writer rewrites; their churn is never this
cycle's output.

## Cycle scope

**Spec files and `.py` source only.** Out of scope by maintainer instruction: `docs/GLOSSARY.md`,
`docs/TREE.md`, `KANBAN.md` / `KANBAN.html`, `examples/fakeshop/db.sqlite3`, `CHANGELOG.md`,
`README.md`, every closeout / agentflow doc (`BUILD.md`, `ARTIFACT.md`, `worker-*.md`), and the
`docs/builder/worker-memory/` retrospective fold-in. Anything this cycle finds in those surfaces
is recorded in the final artifact's `### Deferred work catalog`, never edited.

The spec is already archived at `docs/SPECS/`; no further move is owed. Its rationale companion
belongs at `docs/SPECS/appx/spec-041-channels_router-0_0_14-rationale.md`, the location every
other archived spec's companion uses.

## Worker-0 verification: the code conformance sweep

`docs/builder/BUILD.md` `### Worker 0 verifies every finding against source before dispatching`
requires the dispatcher to read the source behind every finding first. Done; the verified
result is the finding list below, and it splits cleanly in two.

### Nothing was skipped in the code — every spec-041 deliverable landed

Verified at HEAD, symbol-qualified:

| Spec-041 deliverable | Landed at |
| --- | --- |
| `require_optional_module(module_name, *, install_hint)`, no `feature_label` | `django_strawberry_framework/utils/imports.py::require_optional_module` |
| its unit tests | `tests/utils/test_imports.py` (success, hint + chained cause, non-memoization, hostile hint) |
| `require_channels()` as a thin wrapper, no memoization | `django_strawberry_framework/routers.py::require_channels` |
| one `_CHANNELS_INSTALL_HINT` string | `django_strawberry_framework/routers.py` #"_CHANNELS_INSTALL_HINT" |
| split present-but-incompatible hints (channels half / strawberry half) | `routers.py` #"_CHANNELS_BROKEN_HINT", #"_STRAWBERRY_CHANNELS_BROKEN_HINT" |
| PEP 562 lazy `__getattr__` + `_ROUTER_CLASS` cache | `routers.py::__getattr__`, `routers.py::_build_router_class` |
| `__all__ = ("DjangoGraphQLProtocolRouter",)` with the scoped `# noqa: F822` | `routers.py` #"PEP 562 lazy export" |
| `request_from_info()` Channels branch + wrapping adapter | `utils/permissions.py::ChannelsRequestAdapter`, `utils/permissions.py::_channels_request_adapter` |
| its unit tests beside the helper's suite | `tests/utils/test_permissions.py` (recognition, delegation, scope fields, permission-hook read, rejection) |
| `channels[daphne]>=4.3.2` in `[dependency-groups].dev` | `pyproject.toml` #"channels[daphne]>=4.3.2" |
| Test plan rows 1, 4, 5, 6, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18 | `tests/test_routers.py` — all present, several widened |

**Conclusion: no code change is owed by this cycle.** No deliverable was dropped, no feature
forgotten. Test-plan rows 2, 3, 7 and 8 are the only ones with no live counterpart, and their
absence is correct: each asserted the HTTP GraphQL branch `spec-046` deliberately removed, and
`tests/test_routers.py::test_graphql_http_consumer_left_the_router_module_entirely` now pins
that removal positively.

### The spec has drifted from HEAD — twelve verified findings

Each was read against source before being written down. All are **spec-only**; none describes
a code defect.

- **F1 — the constructor signature.** Spec (Decision 6, `## User-facing API`,
  `## Implementation plan`, `## Definition of done`) pins
  `(schema, django_application=None, url_pattern="^graphql")`. HEAD's
  `routers.py::_build_router_class_uncached` inner `DjangoGraphQLProtocolRouter.__init__` is
  `(schema, django_application, *, websocket_url_pattern=r"^graphql/?$",
  websocket_consumer_class=None, websocket_revalidation_window=...)`. Superseded by `spec-046`.
- **F2 — the `http` branch.** Spec composes
  `AuthMiddlewareStack(URLRouter([graphql, *django_fallback]))`. HEAD assigns the consumer's
  Django ASGI application verbatim: `routers.py` #'"http": django_application'.
- **F3 — the `websocket` branch.** Spec composes
  `AllowedHostsOriginValidator(AuthMiddlewareStack(URLRouter([graphql])))`. HEAD wraps a fourth
  layer outermost: `consumers.py::DjangoWebSocketHostValidator`.
- **F4 — which consumers are imported.** Spec (Decision 7, Error shapes, the Strawberry-floor
  gate, DoD) names `GraphQLHTTPConsumer` **and** `GraphQLWSConsumer`. HEAD imports only
  `GraphQLWSConsumer`.
- **F5 — the Strawberry floor in the DoD.** The DoD still says
  `strawberry-graphql==0.262.0`. HEAD: `pyproject.toml` #"strawberry-graphql>=0.316.0",
  `utils/imports.py::STRAWBERRY_FLOOR`, and the re-typed test literal
  `tests/test_routers.py` #"_STRAWBERRY_FLOOR_SUBSTRING" all read `0.316.0`. The spec's own
  preamble reconciled this elsewhere and missed the DoD line, so the spec contradicts itself.
- **F6 — the floors are no longer written inside the hint strings.** Helper-reuse D2 describes
  a hint constant carrying the floor as text. HEAD interpolates `utils/imports.py::CHANNELS_FLOOR`
  and `utils/imports.py::STRAWBERRY_FLOOR` into every hint, leaving `pyproject.toml` as the one
  other written copy. A later DRY consolidation the spec never absorbed.
- **F7 — first construction is serialized.** HEAD carries `routers.py` #"_ROUTER_CLASS_LOCK"
  and a double-checked `_build_router_class` / `_build_router_class_uncached` pair, pinned by
  `tests/test_routers.py::test_concurrent_first_class_access_returns_one_cached_class`. The
  spec describes only the unsynchronized `_ROUTER_CLASS` cache.
- **F8 — the Channels adapter grew a second shape and a fail-closed read.** Decision 11
  describes the HTTP consumer's `ChannelsRequest` (`consumer.scope`). HEAD's
  `utils/permissions.py::_channels_scope` also resolves the WebSocket consumer-as-request
  shape (`request.scope`), and `ChannelsRequestAdapter._scope_value` converts a hostile scope
  mapping into a `ConfigurationError` rather than letting it escape raw.
- **F9 — auth over Channels is no longer wholly deferred.** Decision 11 defers session-mutating
  auth to a follow-on card. HEAD ships the transport-owned boundary in
  `django_strawberry_framework/auth/sessions.py`: a Channels HTTP scope supports `login` and
  `logout`, a WebSocket scope rejects `login` before authentication, and WebSocket `logout`
  turns on the session engine.
  **Corrected after Worker 1's pass, re-verified at source by Worker 0.** Two errors in the
  wording above. (a) **Attribution:** the boundary is `spec-040`'s subsystem, not `spec-046`'s —
  `auth/sessions.py` #"subsystem (spec-040 Decision 3)" names it, and the file's only
  `spec-046` citation is Decision 11's per-operation revalidation, a different contract.
  (b) **Precision:** `auth/sessions.py::login_supported` returns `False` for **any** WebSocket
  transport regardless of session engine; only `auth/sessions.py::logout_supported` is
  engine-conditional. "Rejects `login` before authentication" is the right shape but the
  engine plays no part in it. Worker 1's spec text carries the corrected version.
- **F10 — the test plan.** Rows 2, 3, 7 and 8 describe the removed HTTP GraphQL branch. Rows 16
  and 18 are specified over `HttpCommunicator`; HEAD proves both over the WebSocket branch
  (`tests/test_routers.py::test_request_contract_resolves_over_the_websocket_branch`,
  `::test_authenticated_session_round_trip_reaches_the_resolver`).
- **F11 — the edge cases.** The `^graphql` prefix semantics, the "HTTP fallback runs inside
  `AuthMiddlewareStack`" paragraph, the async-HTTP-consumer sync-ORM paragraph, and the
  multipart-over-the-Channels-HTTP-consumer paragraph all describe a branch that no longer
  exists.
- **F12 — the slice checklist and implementation-plan rows** restate F1-F4 and inherit their
  drift.

### The contract-level question, and the maintainer's own answer

Whether an archived spec should be rewritten to the current contract at all — as against
keeping the amendment banner it carries today — is a contract choice, not a worker's call.
The maintainer decided it in the dispatch: the spec must match what exists, and the
explanation of what changed goes in the rationale companion, never in the spec. Rejected
alternatives, recorded so the round is not re-fought:

- **Keep the amendment banner, edit nothing.** Lost because `docs/builder/BUILD.md`
  `## Spec rationale extraction` makes a spec a contract that never narrates its own history,
  and because a reader currently has to apply a three-item chronology to the document to learn
  what is true.
- **Delete the superseded decisions outright.** Lost because it would strand every inbound
  citation and erase the reasoning the rationale file exists to preserve.

## Ownership partition

One cohort; no concurrent dispatch. Declared because `worker-0.md` requires the mapping even
for a single cohort.

| Cohort | Files it may write |
| --- | --- |
| `041-reconciliation` | `docs/SPECS/spec-041-channels_router-0_0_14.md`, `docs/SPECS/appx/spec-041-channels_router-0_0_14-rationale.md`, `docs/builder/bld-041-*.md`, `docs/builder/worker-memory/worker-*.md` (own file only) |

No `.py` file is writable by any cohort, because the verification sweep found no code defect.
Should review surface one, the cycle stops and re-partitions rather than letting a worker write
outside this list.

## Retired at closeout — this plan is the cycle's only surviving file

Every artifact this cycle produced was deleted once the work was committed, so each
`docs/builder/bld-041-…` filename below is a **retrieval key, not a live path**. All three were
introduced in the same commit, `623639dc`, which is the one retrieval id:

- `git show 623639dc:docs/builder/bld-041-slice-1-rationale_and_spec_reconciliation.md`
- `git show 623639dc:docs/builder/bld-041-slice-2-deferral_homing.md`
- `git show 623639dc:docs/builder/bld-041-final.md` — note this is the copy **before** the
  closeout pass repointed its references away from the two slice artifacts, so it is the fuller
  one; the amended copy that followed was never committed.

Everything those three held that lived nowhere else is folded into `## Final gate, folded in`
below, or moved onto the board. Nothing else survived them by design.

## Artifact list

All three retired at cycle close, retrieval keys above:

- Slice 1 — rationale extraction and spec reconciliation.
- Slice 2 — deferral homing and the cross-surface range claim.
- The final gate — folded into `## Final gate, folded in` below.

## Worker sequence for Slice 1 (deviation from `## Per-slice dispatch`, recorded)

The spec is Worker-1-only property (`docs/builder/BUILD.md` `## Spec reconciliation`), and the
maintainer authorized Worker 1 alone to carry a spec-only change. So there is no Worker 2 pass:
Worker 1 plans **and** executes, then sets `Status: built`. Worker 3 still reviews — isolation
is non-waivable, and the point of it is that the author never approves their own work. Worker 1
then performs final verification.

1. Worker 1 — plan + rationale extraction + spec reconciliation → `Status: built`.
2. Worker 3 — independent review of the rewritten spec against HEAD source → `Status:
   review-accepted` or `revision-needed`.
3. Worker 1 — final verification → `Status: final-accepted`.

## Final gate scope (deviation from `## Final test-run gate`, recorded)

No `.py` file changes in this cycle, so `uv run pytest --no-cov` measures nothing this cycle
caused — and the tree is dirty with a concurrent cycle's in-flight source edits, so a failing
row would not be attributable to this build at all. `AGENTS.md` #"No pytest after edits"
independently forbids it absent a maintainer request. The gate therefore runs the read-only
checks that CAN see this cycle's output:

- `uv run ruff format --check .` and `uv run ruff check .` (baseline exceptions from the
  concurrent cycle recorded, not fixed)
- `git diff --check`
- `uv run python scripts/check_citations.py --check`
- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-041-channels_router-0_0_14.md`
- `uvx pre-commit run --files <the two spec paths>`

## Checklist

- [x] Slice 1: rationale extraction + spec reconciliation (artifact retired at close)
- [x] Final gate (artifact retired at close; folded into `## Final gate, folded in`)
- [x] Slice 2: deferral homing + the cross-surface range claim (artifact retired at
      close)

Slice 2 was dispatched after the final gate, on a writable set the maintainer widened to
include the fakeshop board and glossary databases. It discharges three of the four items in
the final gate's `## Deferred work catalog` — two by correcting the surfaces slice 1 could
not reach, one by homing a decision and two card-id populations on the board — and corrects
two count errors that catalog carried. `pyproject.toml` stayed out of scope throughout; its
one site is homed, not edited. No `.py` file changed in either slice, so no Worker 2 pass and
no `pytest` run, per the deviations this plan already records.

## Final gate, folded in from the retired `bld-041-final.md`

Gate scope is `## Final gate scope` above; this is what the run produced.

| Instrument | What it actually read | Result |
| --- | --- | --- |
| `ruff format --check .` | every `.py` in the tree, this cycle's and the concurrent cycle's alike | 445 files already formatted, exit 0 |
| `ruff check .` | same | All checks passed, exit 0 |
| `git diff --check` | whitespace in the unstaged diff, whole tree | clean |
| `scripts/check_citations.py` | first-party `.py` and `KANBAN.md` **only** | OK, 981 citations at the gate; 983 after the closeout board edits |
| `scripts/check_spec_glossary.py --spec <the spec>` | the spec plus its `-terms.csv` (30 rows) | OK, all 30 terms resolve |
| `scripts/check_kanban_anchors.py` | the board DB | OK, 76 card anchors, no glossary collision |
| all four generators `--check` | working tree vs the DBs they render from | all fresh |
| `uvx pre-commit run --files <cycle paths>` | those paths, explicitly | all hooks Passed on the first run |

**What the greens do not establish, and it matters for the next pass.**
`check_citations.py` reads `.py` and `KANBAN.md`; it is **blind to every markdown file this cycle
wrote**, so its green means only that no existing `path::Symbol` citation elsewhere was broken.
The pair's own citations were verified separately, by AST resolution of all 46 occurrences.
`check_spec_glossary.py` compares term and anchor only — that caveat now sits on the alpha
documentation-debt card's `notes`-column ruling, because it is not specific to this cycle. Two
gates agreeing is not corroboration when neither can see the other's failure mode.

**Staged-anchor sweep.** `grep -rEn 'TODO\(spec-041|TODO-(ALPHA|BETA|STABLE)-041'` over `.py` and
`.md`: **0 in `.py`**. No source file carries a staged anchor for this spec or card, so nothing
shipped left one behind and nothing names a still-open slice. Every hit was prose describing an
anchor rather than a live one. The count moved between Worker 0's run and the gate's because the
artifacts being written were themselves inside the corpus — a census run over a corpus it is being
written into reports a different number each time it is recorded.

**Floor verification: scope `none`, deliberately.** No slice touched executable code, so no
Django / Strawberry / channels integration seam was opened and no floor run was owed. No floor
claim in this cycle rests on an unrun gate, and the shared `.venv` was never installed into,
downgraded, or otherwise mutated. The floor read from `docs/builder/BUILD.md` and never from
memory: Django 5.2.16 on Python 3.10 with strawberry-graphql 0.316.0. The shared `.venv` is not
the floor; it read `channels 4.3.2`, `daphne 4.2.2`, `django 6.1`, `strawberry-graphql 0.324.0`,
and that reading is load-bearing for the dependency finding now on the boundary-hardening card.

**Hot-path budget: scope `none`**, for the same reason — no serialization point, no lock, no extra
pass over a result set, no per-item work, because no executable code changed.

**Deferred work catalog: superseded, all four items homed on the board.** The dependency decision
and its parallel sites went to the boundary-hardening / DRY-squeeze card, which owns the
dependency-group and extras surface; the two card-id populations and the `-terms.csv` `notes`
ruling went to the alpha documentation-debt card. The catalog itself carried two count errors,
both corrected before it was retired: a phrase count reported as a claim count, and an inverted
statement of which `pyproject.toml` row the classifier comment belongs to.
