# Build: Slice 1 — rationale extraction + spec reconciliation (spec-041)

Spec reference: `docs/SPECS/spec-041-channels_router-0_0_14.md` (whole file; 2210 lines at HEAD)
Status: final-accepted

Cycle type: **post-ship reconciliation round**, per `docs/builder/build-041-channels_router-0_0_14.md`.
Card `DONE-041-0.0.14` shipped long ago; Worker 0's code-conformance sweep established that
**nothing was skipped in the code**. This slice creates the rationale companion the card never
got and reconciles the spec with HEAD.

Worker sequence deviation (recorded in the build plan's `## Worker sequence for Slice 1`): there
is no Worker 2 pass. Worker 1 plans **and** executes in this one pass and sets `Status: built`;
Worker 3 reviews independently; Worker 1 then performs final verification.

---

## Plan (Worker 1)

### DRY analysis

**Helper inventory checked.** Not applicable in its usual form and the reason is not a skip: this
slice writes no `.py` file, so there is no helper to plan, no shared shape to assign, and no
package-wide AST inventory that could prevent a duplication this pass can commit. The
inventory's own purpose — "a duplication the inventory cannot see is one the plan cannot
prevent" — has a documentary analogue that **was** run, and it is the one that matters here: the
inbound-citation sweep in `### Anchor and citation discipline` below, plus the five-homes
cross-check in `### Spec changes made (Worker 1 only)`.

- **Existing patterns reused.** The rationale companion is modelled on the two existing
  post-ship companions, read in full before writing: `docs/SPECS/appx/spec-046-transport_security-0_0_14-rationale.md`
  (opening paragraph, `## How to read this file`, `Change record` blocks, per-decision entries
  keyed by heading and anchor, the ten-group link block) and
  `docs/SPECS/appx/spec-047-resource_policy-0_0_14-rationale.md` (the *post-ship* variant of the
  same form: a move performed after the release rather than at pre-flight, with a
  `Moved` / `Reconstructed` / `Deleted` provenance split). `spec-047`'s is the closer model and
  its shape is the one followed.
- **New shared shapes justified.** One, and it is the reason this file is not a flat timeline:
  the spec's nine-entry `Revision history` is redistributed into per-decision
  `**Change record — …**` blocks, with a single `## Round vocabulary` section naming the nine
  rounds once so no block restates what "Revision 5" was. Without that section every block would
  carry its own three-line gloss of the same round — nine decisions times four rounds of
  duplication.
- **Duplication risk avoided.** The dominant risk in this cycle is **duplicating `spec-046`'s
  contract into `spec-041`**. Four surfaces are `spec-046`'s (the required `django_application`
  and direct HTTP dispatch, the `websocket_url_pattern` rename, the Host validator, the
  `websocket_consumer_class` / `websocket_revalidation_window` pair) and a naive reconciliation
  would restate each one's rules here, creating a second copy that rots the next time
  `spec-046` moves. The rule applied throughout: **state the shape a `routers.py` reader needs,
  attribute the ownership, point at the owner.** `Decision 6` says this in one paragraph, and
  every other site that touches those surfaces carries the attribution rather than the contract.

### Implementation steps

1. Read the whole spec (2210 lines) and verify F1-F12 against source independently of Worker 0's
   list: `django_strawberry_framework/routers.py`, `consumers.py`, `utils/imports.py`,
   `utils/permissions.py`, `auth/sessions.py`, `tests/test_routers.py`, `tests/utils/test_imports.py`,
   `tests/utils/test_permissions.py`, `pyproject.toml`, and `docs/SPECS/spec-046-transport_security-0_0_14.md`.
2. Sweep inbound citations before touching any heading (`### Anchor and citation discipline`).
3. Write `docs/SPECS/appx/spec-041-channels_router-0_0_14-rationale.md`: banner + revision
   history + rejected alternatives + Risks + the F1-F12 record.
4. Reconcile the spec section by section, cross-checking all five homes per contract.
5. Run the gates; record each result.

### Test additions / updates

None. No `.py` file is writable by this cohort and the code-conformance sweep found no defect.
The spec's `## Test plan` is *described* accurately against the live suite (see F10), which is a
documentation change, not a test change.

### Implementation discretion items

None delegated — this pass is both plan and execution, so every judgement is recorded in
`### Spec changes made (Worker 1 only)` rather than deferred.

### Boundary count and split question

Zero new boundaries: no executable code changes. The split question is answered *no* — the
rationale move and the reconciliation are one custodian judgement (what a decision now says and
what it used to say are decided together), and splitting them would produce a spec briefly
describing a contract whose history lived nowhere.

### Hot-path declaration

Not applicable; the build plan declares hot-path scope `none` for this cycle, and the silence is
deliberate rather than an omission: no slice changes executable code.

### Floor-verification scope

`none`, per the build plan. The supported floor is Django **5.2.16** on Python **3.10** with
strawberry-graphql **0.316.0** (`docs/builder/BUILD.md` `## Floor verification`), and no slice in
this cycle touches a Django / Strawberry / channels integration seam.

### Dispatched findings checklist

One box per verified finding F1-F12 from `docs/builder/build-041-channels_router-0_0_14.md`
`### The spec has drifted from HEAD — twelve verified findings`, quoted as the plan states it
with the symbol-qualified path. A box is ticked only where the reconciliation landed in this
pass's diff.

- [x] **F1 — the constructor signature.** Spec (Decision 6, `## User-facing API`,
      `## Implementation plan`, `## Definition of done`) pins
      `(schema, django_application=None, url_pattern="^graphql")`. HEAD's
      `routers.py::_build_router_class_uncached` inner `DjangoGraphQLProtocolRouter.__init__` is
      `(schema, django_application, *, websocket_url_pattern=r"^graphql/?$",
      websocket_consumer_class=None, websocket_revalidation_window=...)`. Superseded by `spec-046`.
- [x] **F2 — the `http` branch.** Spec composes
      `AuthMiddlewareStack(URLRouter([graphql, *django_fallback]))`. HEAD assigns the consumer's
      Django ASGI application verbatim: `routers.py` #'"http": django_application'.
- [x] **F3 — the `websocket` branch.** Spec composes
      `AllowedHostsOriginValidator(AuthMiddlewareStack(URLRouter([graphql])))`. HEAD wraps a fourth
      layer outermost: `consumers.py::DjangoWebSocketHostValidator`.
- [x] **F4 — which consumers are imported.** Spec (Decision 7, Error shapes, the Strawberry-floor
      gate, DoD) names `GraphQLHTTPConsumer` **and** `GraphQLWSConsumer`. HEAD imports only
      `GraphQLWSConsumer`.
- [x] **F5 — the Strawberry floor in the DoD.** The DoD still says
      `strawberry-graphql==0.262.0`. HEAD: `pyproject.toml` #"strawberry-graphql>=0.316.0",
      `utils/imports.py::STRAWBERRY_FLOOR`, and the re-typed test literal
      `tests/test_routers.py` #"_STRAWBERRY_FLOOR_SUBSTRING" all read `0.316.0`. The spec's own
      preamble reconciled this elsewhere and missed the DoD line, so the spec contradicts itself.
- [x] **F6 — the floors are no longer written inside the hint strings.** Helper-reuse D2 describes
      a hint constant carrying the floor as text. HEAD interpolates `utils/imports.py::CHANNELS_FLOOR`
      and `utils/imports.py::STRAWBERRY_FLOOR` into every hint, leaving `pyproject.toml` as the one
      other written copy. A later DRY consolidation the spec never absorbed.
- [x] **F7 — first construction is serialized.** HEAD carries `routers.py` #"_ROUTER_CLASS_LOCK"
      and a double-checked `_build_router_class` / `_build_router_class_uncached` pair, pinned by
      `tests/test_routers.py::test_concurrent_first_class_access_returns_one_cached_class`. The
      spec describes only the unsynchronized `_ROUTER_CLASS` cache.
- [x] **F8 — the Channels adapter grew a second shape and a fail-closed read.** Decision 11
      describes the HTTP consumer's `ChannelsRequest` (`consumer.scope`). HEAD's
      `utils/permissions.py::_channels_scope` also resolves the WebSocket consumer-as-request
      shape (`request.scope`), and `ChannelsRequestAdapter._scope_value` converts a hostile scope
      mapping into a `ConfigurationError` rather than letting it escape raw.
- [x] **F9 — auth over Channels is no longer wholly deferred.** Decision 11 defers session-mutating
      auth to a follow-on card. HEAD ships the transport-owned boundary in
      `django_strawberry_framework/auth/sessions.py`: a Channels HTTP scope supports `login` and
      `logout`, a WebSocket scope rejects `login` before authentication, and WebSocket `logout`
      turns on the session engine.
- [x] **F10 — the test plan.** Rows 2, 3, 7 and 8 describe the removed HTTP GraphQL branch. Rows 16
      and 18 are specified over `HttpCommunicator`; HEAD proves both over the WebSocket branch
      (`tests/test_routers.py::test_request_contract_resolves_over_the_websocket_branch`,
      `::test_authenticated_session_round_trip_reaches_the_resolver`).
- [x] **F11 — the edge cases.** The `^graphql` prefix semantics, the "HTTP fallback runs inside
      `AuthMiddlewareStack`" paragraph, the async-HTTP-consumer sync-ORM paragraph, and the
      multipart-over-the-Channels-HTTP-consumer paragraph all describe a branch that no longer
      exists.
- [x] **F12 — the slice checklist and implementation-plan rows** restate F1-F4 and inherit their
      drift.

### Independent verification of the finding list

Worker 0's list is a verified hypothesis, not an instruction. Every finding was re-read against
source in this pass before any edit; all twelve hold. Two refinements, recorded because they
changed what the reconciliation wrote:

- **F9's cause is `spec-040`, not `spec-046`.** The build plan names the finding but not its
  owner. `django_strawberry_framework/auth/sessions.py` was added by commit `c8346750`
  ("feat(auth): harden the session lifecycle across transports", 2026-07-21) alongside
  `auth/mutations.py`, `tests/auth/test_sessions.py` and the README transport-contract pass, and
  `docs/SPECS/spec-040-auth_mutations-0_0_13.md` describes the classification / capability /
  session layer as its own. So the spec attributes the discharged deferral to `spec-040`
  throughout, never to `spec-046`. Had it gone the other way, `spec-041` would now point readers
  at a spec that does not carry the contract.
- **F9's capability answers are narrower than the plan's summary.** The plan says "a WebSocket
  scope rejects `login` before authentication, and WebSocket `logout` turns on the session
  engine". Read at source: `auth/sessions.py::login_supported` returns `False` for
  `Transport.CHANNELS_WEBSOCKET` **regardless of engine** (an established socket cannot send the
  replacement cookie login's key rotation produces), and
  `auth/sessions.py::logout_supported` returns `False` only for a **signed-cookie-engine**
  WebSocket. The spec states the narrow form.

### Findings beyond F1-F12 that this pass reconciled

Each was found by the five-homes cross-check or the citation sweep, each is the same class as an
F-finding (spec prose falsified by live state), and each is recorded here so Worker 3 can grade
it as in-scope rather than as unrelated scope:

- **F1's sibling in Decision 9 and Goal 3.** The finding list names Decision 6, the API section,
  the implementation plan and the DoD. The byte-compatibility claim also lives in **Decision 9**
  ("with the note that the constructor signature is unchanged" — the entire content of the
  migration-guide handoff row) and in **Goal 3** ("with zero call-site changes"). Both rewritten.
- **A `GOAL.md` quotation that rotted from the other end.** Goal 3 and `## Problem statement`
  quoted `GOAL.md` success criterion 7 as migrate "without bringing the source package along — …
  only the import line changes". `GOAL.md` criterion 7 today reads "…without bringing the source
  package along. The import-only promise covers `Meta`-driven domain declarations; project-level
  engine configuration … migrates by documented recipe" — the quoted clause is gone
  (`grep -c 'only the import line changes' GOAL.md` returns 0). Both quotations shortened to the
  surviving clause.
- **Test 10's consumer name.** The row's justification for keeping `DjangoOptimizerExtension` out
  read "under the async `GraphQLHTTPConsumer`" — the consumer F4 removed. The constraint survives
  on the equally-async WebSocket consumer; the name was corrected rather than the row dropped.
- **Nine process-provenance labels in standing prose** (`P1.1` ×6, `P1.2` ×1, `P1.4` ×2), which
  `AGENTS.md` #"No process provenance in code or standing prose" forbids. Each carried a real
  why, restated as a plain clause.
  *(Figure and vocabulary corrected in the apply-changes pass, which re-measured them; the
  sentence previously read "Three … `finding P1.1` twice, `finding P1.2` once". Derivation in
  `### Counts re-measured in this pass`.)*

### Notes for Worker 1 (spec reconciliation)

No code defect was found; the cohort wrote no `.py` file and the ownership partition was not
tested. See `### Deferred work` for the two populations this pass deliberately did not touch.

---

## Build report (Worker 1, acting in place of Worker 2)

### Files touched

- `docs/SPECS/appx/spec-041-channels_router-0_0_14-rationale.md` (new) — the rationale companion.
- `docs/SPECS/spec-041-channels_router-0_0_14.md` — reconciled to the HEAD contract.
- `docs/builder/bld-041-slice-1-rationale_and_spec_reconciliation.md` (new) — this artifact.
- `docs/builder/worker-memory/worker-1-041.md` — memory entry (untracked scratch).

No `.py` file, no test, no generated doc, no KANBAN surface.

### What moved to the rationale companion

A move, not a copy: every item below is gone from the spec.

1. **The amendment banner** (spec lines 1-38 at HEAD) — the three-item `spec-046` supersession
   notice plus the Strawberry-floor "not a supersession" paragraph. Now
   `## Supersession: what spec-046 took over`, with the maintainer's rejected alternatives for
   the reconciliation decision itself recorded beside it.
2. **The `Revision history` block** (spec lines 122-419 at HEAD; nine revisions). Restructured,
   not transcribed: `## Round vocabulary` names the nine rounds once, and every substantive item
   is redistributed into the decision it belongs to as a `**Change record — Revision N.**` block.
   Items with no owning decision (the conftest attribution withdrawal, the `docs/TREE.md` row
   quotations, the Test-4 isinstance mechanics, the glossary passes) sit under
   `## Change record for the spec's non-decision sections`, keyed by the spec section.
3. **Eleven `Alternatives considered (and rejected)` blocks** — one per Decision. Each spec
   decision keeps a one-line pointer at its entry, so a reviewer can see the deliberation exists
   without reading it (`worker-1.md` `### Performing the rationale move` rule 1).
4. **`## Risks and open questions` in full** — five preferred-answer / fallback pairs, each now
   carrying what it actually turned out to be. The spec keeps a four-line pointer in place of
   the section, because the section heading is cited from `## Current state` and elsewhere.
5. **Derivation narrative that does not change how a thing is built** — Decision 3's
   three-surfaces-already-carry-it naming derivation, Decision 10's `NEXT.md` Step 3 / Step 6
   justification, Decision 11's dict-context blast-radius derivation, and the Borrowing posture's
   upstream-vs-core comparison reasoning.
6. **The F1-F12 post-ship record** — `## Post-ship corrections`, one entry per finding, each
   stating what the spec used to claim, what HEAD does (symbol-qualified), which card caused the
   change, and why. This exists **only** in the companion; the spec never narrates it.

**What deliberately stayed in the spec**, under `worker-1.md`'s implementation-relevant-rationale
carve-out: Decision 5's "`require_channels()` runs *before* any `strawberry.channels` import"
ordering (a builder who skips it writes the bare-traceback path), Decision 11's wrap-don't-narrow
rule (a builder who skips it writes the two-field adapter), the missing-`Origin` denial reasoning,
and the Test-plan note that the structural walk is isolated behind one helper. The companion's
`## How to read this file` names all four so a later pass does not re-open them.

### Spec byte count, before and after

| File | Lines | Bytes |
| --- | --- | --- |
| spec at HEAD (`git show HEAD:…`) | 2210 | 150,224 |
| spec after this pass | 1814 | 122,117 |
| rationale companion (new) | 968 | 63,489 |

The spec is **28,107 bytes smaller**, which is what every future spawn stops paying. The pair is
larger than the old spec by 35,382 bytes, and that is the move working as intended: the F1-F12
record and the per-decision change records did not exist anywhere before.

### Validation run

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-041-channels_router-0_0_14.md`
  — **pass**, `OK: 30 terms - all have glossary entries and at least one spec link.` (exit 0;
  matches the `OK: 30 terms` pre-flight reading).
- `uv run python scripts/check_citations.py --check` (whole tree) — **pass**,
  `OK: 981 citations resolve (814 in 442 .py files, 167 in KANBAN.md).` Note the instrument's own
  input: this gate reads first-party `.py` files and `KANBAN.md` only, so it does **not** see the
  `path::Symbol` refs in either file this pass wrote. Its green is evidence that this pass broke
  no existing citation, not that the new ones resolve; those were checked by reading.
- `uvx pre-commit run --files …` — recorded in `### Pre-commit` below.
- No `pytest`, no `--cov*` flag, no `ruff --fix` on anything outside this cohort's files.

### Link-convention verification

Mechanical, over both files, with the population size printed rather than assumed:

- Every `][label]` use has a definition and every definition has a use: **0 undefined uses, 0
  unused defs** in each file (code spans and fenced blocks stripped before sweeping, per
  `START.md`).
- All **ten** canonical group headers present, in order, in both files.
- Every definition's target **exists on disk** from that file's own directory: 0 missing. The
  companion sits one level deeper than the spec, so its root paths are `../../../` and its
  `docs/` paths `../../`; disk-existence alone is fail-open (a same-named file one level up masks
  depth rot), so each definition's group header and intended target were checked as well.
  `docs/SPECS/appx/` definitions sit under `<!-- docs/SPECS/ -->` in both files, per `START.md`.
- **In-page anchors:** **17** distinct targets in the spec, 9 in the companion — **0 broken**,
  checked by slugging every heading in each file and differencing.
  *(Spec figure corrected in the apply-changes pass, which re-measured it; it previously read
  18. Derivation in `### Counts re-measured in this pass`.)*
- **Cross-file anchors:** every `…-rationale.md#…` definition in the spec resolves to a companion
  heading, and every `…spec-041-channels_router-0_0_14.md#…` definition in the companion resolves
  to a spec heading — **0 broken in both directions**.

### Anchor and citation discipline

**One heading was renamed, and only because it literally stated a superseded signature:**

```
- ### Decision 6 — Constructor parity: `(schema, django_application=None, url_pattern="^graphql")`; composition borrowed as-is
+ ### Decision 6 — Constructor and composition
```

The sweep run **before** the rename, not after:

- `grep -rn 'spec-041' docs tests django_strawberry_framework examples scripts *.md` — 33 files
  name the spec.
- `grep -rn 'spec-041-channels_router-0_0_14\.md#' docs/ KANBAN.md BACKLOG.md`, excluding the spec
  itself — **0 occurrences**. No document outside the spec cites any `spec-041` heading anchor, so
  the rename strands nothing outside the file.
- Inside the spec, the old anchor had **9** in-page uses; **4** in-page uses of
  `#decision-6--constructor-and-composition` survive and the other **5** retired with the
  passages that carried them. A repo-wide grep for the old slug returns exactly **1** hit — the
  companion's own record of what the anchor used to be, which is deliberate.
  *(Figure corrected in the apply-changes pass, which re-measured it; the sentence previously
  read "11 uses; all 11 now read". Derivation in `### Counts re-measured in this pass`.)*
- `docs/SPECS/spec-041-channels_router-0_0_14-terms.csv` was **not touched**. Its 30 rows carry
  *glossary* anchors, not spec anchors, so a spec heading rename cannot strand it; what could
  strand it is deleting the spec's only reference-style **use** of a glossary term, which the
  gate checks and which is recorded below.
- Every other decision heading was left **stable on purpose**, including two whose wording a
  reader could mistake for falsified: Decision 2's "WebSocket-auth semantics … stay out" and
  Decision 11's "auth *mutations* stay deferred". Both remain true statements about **this
  card's** scope — what changed is that another card later took the subject — so the bodies
  attribute the ownership and the headings do not move.

**The terms-CSV hazard this move created, and how it was closed.** The `FieldError` envelope row
(anchor `fielderror-envelope`) had exactly **two** reference-style uses in the spec, and **both
sat inside the Revision-6 and Revision-7 entries of the `Revision history` block** this pass
moved out. Moving the block would have left the CSV row with no spec link and failed
`check_spec_glossary.py`, and the CSV is not writable this cycle. Every other CSV anchor was
enumerated the same way before writing (each of the 30 mapped to its ref-id and to the line
numbers of its uses); `fielderror-envelope` was the only one whose entire use population lived in
moved text. The fix is a truthful `## Key glossary references` bullet on the precedent the
section already sets (`DjangoOptimizerExtension` is listed there as "untouched here, but worth
naming"): `request_from_info()` resolves the same object `build_serializer_kwargs` hands DRF as
`context["request"]`, and `rest_framework/resolvers.py` imports both `request_from_info` and
`field_error`, so a serializer override reading that request under Channels produces entries in
that envelope. Verified at source before writing the sentence, not asserted from the name.

### Pre-commit

`uvx pre-commit run --files docs/SPECS/spec-041-channels_router-0_0_14.md docs/SPECS/appx/spec-041-channels_router-0_0_14-rationale.md docs/builder/bld-041-slice-1-rationale_and_spec_reconciliation.md docs/builder/build-041-channels_router-0_0_14.md`
— explicit paths always, never the default, because `scripts/check_trailing_commas.py` defaults
to a repo-wide auto-fix that would rewrite the concurrent `spec-050` session's files.

Result: see `### Pre-commit result` at the end of this report.

### Failability proofs

None; this pass introduced no new boundary. No executable code changed.

### Hot-path budget

Not applicable; plan declares no hot path.

### Floor verification

Not applicable; plan declares floor-verification scope `none`.

### Implementation notes

- **Scope discipline, applied as a rule rather than case by case.** Where `spec-046` owns a
  surface, `spec-041` states the current shape, names the owner, and stops. The single place the
  shape is spelled out is `Decision 6`, which then says in one paragraph which four of its five
  facts are `spec-046`'s and which one is this card's. `## Out of scope` gained a matching bullet
  naming all five `spec-046` surfaces at once, so a reader who arrives from a search lands on the
  pointer rather than on a half-copy.
- **`## Current state` was graded clause by clause, and kept.** Its vintage framing licenses
  dated observations, so three falsified ones stay: "No `routers.py` exists", "`channels` is
  installed nowhere", and "The version line reads `0.0.13`". The sentence "its presence back at
  the pinned `strawberry-graphql>=0.262.0` floor is upstream history, spot-checked at the
  dependency gate" also stays — it is explicitly historical and makes no claim about live code,
  which is the carve-out `spec-046` Decision 14 named. The one **prediction** in the section
  ("the regenerated tree adds it in Slice 2") was fulfilled, so nothing there needed rewriting.
  By contrast the DoD's `strawberry-graphql==0.262.0` line got no such licence and was corrected
  (F5): a Definition-of-done item is a completion claim.
- **Checkbox state untouched.** Every `- [ ]` in the slice checklist, the helper-reuse ledger and
  the DoD stays unticked, per this repo's shipped-card convention; the `Status:` line is the
  source of truth. Only the *text* beside a box was corrected.
- **The status line was rewritten to a clean current statement.** It read
  `Status: **COMPLETE** (card DONE-041-0.0.14) — … Amended by spec-046; see the banner above.`
  The banner is gone, so the sentence now says the card is complete, the release rode the joint
  cut, and where later cards changed what shipped the spec states the current contract with the
  companion carrying the history.
- **The `F8 split` cross-reference in `## Doc updates`** referred to a finding label from a
  review round whose document is long gone — an unresolvable pointer, replaced by the plain
  statement of what the split is.
- **The spec's title changed** from "…the one-import ASGI / WebSocket migration aid" to "…the
  package's GraphQL WebSocket transport". "One-import" is false twice over: the router no longer
  serves HTTP GraphQL, and migration is a two-place recipe. No document cites the title.

### Notes for Worker 3

- **Read the pair, not just the spec.** The reconciliation's correctness argument is split
  across both files by design: a claim removed from the spec should be findable in the companion,
  and a companion `Change record` should describe text that is genuinely gone. Sweeping only one
  file leaves the other falsified.
- **The five homes per contract** (Decision, slice checklist, `## Edge cases`, `## Test plan`,
  `## Definition of done`) were cross-checked for every contract this pass touched; the per-home
  ledger is in `### Spec changes made (Worker 1 only)`. One contract deliberately does **not**
  appear in all five and the reason is stated there (the construction lock, F7).
- **Two card-id populations were deliberately not touched** — see `### Deferred work`. They are
  visible in the diff as unchanged stale ids and are not an oversight.
- The citation gate cannot see `docs/` prose (it reads `.py` files and `KANBAN.md`), so the
  `path::Symbol` and `path #"substring"` refs added in both files are ungated. They were written
  against source read in this pass; spot-checking them is worth a reviewer's time.

---

## Final verification (Worker 1)

To be completed in a later pass, after Worker 3's review. This pass sets `Status: built`.

### Summary

The spec-041 rationale companion now exists, and the spec states the contract that exists at
HEAD: the router's `"http"` value is the consumer's required Django ASGI application dispatched
directly, its `"websocket"` value is the package's composition inside Channels' origin check
inside the package's Host check, only `GraphQLWSConsumer` is imported, the floors are
interpolated rather than re-typed, first class construction is serialized, the request adapter
resolves both scope shapes with a contained read, and session-mutating auth over Channels is
`spec-040`'s. No amendment banner, no revision history, no retraction paragraph, no chronology a
reader must apply.

### Spec changes made (Worker 1 only)

Grouped by finding, with the five homes named per contract. "Home" means Decision / slice
checklist / `## Edge cases` / `## Test plan` / `## Definition of done`; sections outside that set
are named explicitly.

- **F1 — constructor.** Decision 6 rewritten (and renamed, see
  `### Anchor and citation discipline`); slice checklist `routers.py` row; `## Test plan` rows
  2, 3 and 5; DoD's composition item. Also outside the five homes: `## User-facing API`'s
  `asgi.py` example, constructor block and migration bullet; `## Implementation plan` row;
  `## Goals` Goal 1 and Goal 3; Decision 9's handoff-row content; the DoD's migration-guide item;
  the spec title.
- **F2 — the `http` branch.** Decision 6; slice checklist `routers.py` row;
  `## Edge cases` (the "HTTP fallback runs inside `AuthMiddlewareStack`" paragraph replaced by
  "No Channels middleware runs on HTTP at all"); `## Test plan` rows 2 and 8; DoD composition
  item. Also `## Borrowing posture` (the HTTP-branch paragraph became an explicit
  "what it does not borrow"), `## User-facing API`, `## Problem statement`.
- **F3 — the `websocket` branch.** Decision 6; slice checklist; `## Test plan` row 4; DoD; and
  `## Error shapes`, where the `Host` denial is now named beside the `Origin` one. Not added to
  `## Edge cases` as a separate bullet: the Host boundary's own edge cases are `spec-046`
  Decision 19's, and a second copy would rot.
- **F4 — one consumer.** Decision 7; slice checklist `routers.py` row and the Strawberry-floor
  gate row; `## Test plan` row 3 (the removal asserted positively) and row 7; DoD's floor-gate
  item. Also `## Error shapes`, `## Problem statement`, the preamble.
- **F5 — the DoD's Strawberry floor.** DoD floor-gate item, rewritten to name the pinned floor by
  its single site rather than a literal; slice-checklist gate row likewise. The historical
  `0.262.0` sentences in `## Current state` and Decision 7 were **kept** — see
  `### Implementation notes`.
- **F6 — interpolated floors.** Decision 5 points 1 and 3; Helper-reuse **D2**; `## Error shapes`;
  `## Edge cases` floor bullet; `## Test plan` rows 13 and 17; DoD dependency-gate item; slice
  checklist dependency-gate row. Every site now names
  `utils/imports.py::CHANNELS_FLOOR` / `::STRAWBERRY_FLOOR` and says the test literal is re-typed
  **on purpose** as the drift-catch.
- **F7 — the construction lock.** Decision 5 point 2; Helper-reuse **D3**; slice checklist
  `routers.py` row; `## Test plan` row 6. **Deliberately not added to the DoD**, and the omission
  is the judgement rather than a gap: the DoD is `spec-041`'s completion claim, and the lock is
  post-ship hardening this card did not ship. Adding it would make the spec claim credit for work
  it did not do — the same class of false completion claim the vintage licence denies a DoD line.
- **F8 — two scope shapes, contained read.** Decision 11 point 1; slice checklist
  `utils/permissions.py` row; `## Test plan` row 16 (unit-level shape tests); DoD's
  `request_from_info()` item; `## Implementation plan` row. Also the `## Key glossary references`
  Channels-request-adapter bullet.
- **F9 — auth over Channels.** Decision 2's auth bullet; Decision 11 point 2; `## Non-goals`;
  `## Out of scope`; the `## Key glossary references` Auth-mutations bullet; DoD's GLOSSARY
  re-wording item. Every one attributes `spec-040` and states the narrow capability answers
  verified at source. `## Current state`'s "the auth surface points here" bullet is a dated
  observation and stays, with its stale `[Risks]` pointer dropped.
- **F10 — the test plan.** `## Test plan` rows 1-18 rewritten where affected (2, 3, 5, 6, 7, 8,
  9, 10, 13, 16, 17, 18) plus the section preamble and the coverage paragraph; Decision 8's
  execution paragraph; slice checklist tests row; DoD's test item.
- **F11 — the edge cases.** Four `## Edge cases` bullets: the pattern bullet rewritten to
  `websocket_url_pattern`'s exact-at-both-ends semantics, the HTTP-fallback bullet replaced, the
  async-consumer bullet moved onto the WebSocket consumer (keeping the `SyncMisuseError` and
  `get_queryset` contract), and the multipart bullet retired to
  `views.py::DjangoGraphQLView` with `spec-046` Decisions 17 and 18 named.
- **F12 — checklist and plan rows.** `## Slice checklist` Slice-1 rows (dependency gate,
  Strawberry-floor gate, `routers.py`, `utils/permissions.py`, tests) and Slice-2 rows (the
  GLOSSARY body row, the KANBAN wrap row's tense); `## Implementation plan` table rows for
  `routers.py` and `utils/permissions.py`.
- **Beyond F1-F12** (see `### Findings beyond F1-F12 that this pass reconciled`): Decision 9 and
  Goal 3's byte-compatibility claims; the two `GOAL.md` criterion-7 quotations; Test 10's
  consumer name; three process-provenance labels; Decision 1's "this spec lives at `docs/…`"
  (the file is archived); Decision 4's "~60 lines with docstrings" size figure (replaced by a
  shape, not a new number — a present-tense line count of a file later slices edit is false by
  construction); the three `0.0.14` sibling cards' lifecycle prefixes.

### Deferred work

Neither item is in this cycle's scope, and both are recorded rather than half-swept.

- **Stale Beta card *numerals* inside this spec — 5 occurrences after this pass, deliberately
  left unrenumbered.** `TODO-BETA-062-0.1.5` (**2** occurrences in the spec; the live
  fakeshop-activation card is `TODO-BETA-066-0.1.5`) and `TODO-BETA-068-0.1.8` (**3**
  occurrences; the live migration-guides card
  is `TODO-BETA-071-0.1.8` — `068` today names "Structural optimization templates and nested
  sidecar batching"). The `062` family is an explicitly board-owned population: `KANBAN.md`
  carries the census, records `spec-041 3` in it, and requires **one pass over all
  34 spec-surface sites** rather than a per-spec share — renumbering this spec's share alone is
  exactly the partial fix that item warns against.
  *(Figures corrected in the apply-changes pass, which re-measured them; the bullet previously
  read "7 occurrences … 3 … 4", which was true at HEAD and not after this pass's own edits.
  Derivation, and what the board owner must reconcile, in `### Counts re-measured in this pass`.)* The `068` → `071` family is the same 2026-08-29 board-insert
  renumber and is **not yet enumerated** in that census; surfacing it is this cycle's contribution.
  Both are recorded in the companion's `## Doc updates` change record too, so the next custodian
  finds them from either file.
- **The three `0.0.14` sibling cards were flipped**, and the distinction from the above is
  deliberate: `TODO-ALPHA-043-0.0.14` / `TODO-ALPHA-044-0.0.14` now read `DONE-`, verified against
  `KANBAN.md` (`DONE-044-0.0.14`, `DONE-043-0.0.14`, `DONE-042-0.0.14` all in Done). That is a
  lifecycle prefix on a card whose number did not move, it belongs to no board-owned population,
  and leaving it would have had the spec assert that shipped cards are unshipped.

### Out-of-cycle observations (never edited)

Per the build plan's `## Cycle scope`, anything found in these surfaces is recorded, not touched.
Nothing here blocks the cycle.

- `docs/GLOSSARY.md`'s `DjangoGraphQLProtocolRouter` entry is **accurate and current** — it was
  read in full as a cross-check on the reconciliation and agrees with HEAD on the constructor,
  the three-wrapper chain, the soft-dependency matrix, and the split broken-install hints. No
  defect to report; worth saying, because a silent omission here would read as "not checked".
- `docs/TREE.md` carries two `spec-041` mentions, both on the `tests/test_imports.py` row and both
  correct.
- `CHANGELOG.md`'s `0.0.14` entry describes the router as `DONE-041`/`DONE-046` jointly and is
  accurate.

### Pre-commit result

`uvx pre-commit run --files docs/SPECS/spec-041-channels_router-0_0_14.md docs/SPECS/appx/spec-041-channels_router-0_0_14-rationale.md docs/builder/bld-041-slice-1-rationale_and_spec_reconciliation.md docs/builder/build-041-channels_router-0_0_14.md`

```
kanban tracked path constants...................................Passed
source layout (py trailing commas + ascii-only; md link-def
  scaffold; json/graphql brace explosion).......................Passed
ruff format.....................................(no files to check) Skipped
ruff check......................................(no files to check) Skipped
kanban anchors collision-free...................................Passed
citations resolve (AGENTS.md rule 27 path::Symbol refs).........Passed
```

Green on the **first** run — the `source-layout` hook auto-fixes by default and a rewrite fails
the run, so a re-run would have been expected; it did not rewrite anything, which is the evidence
that both new files were authored with the link-definition scaffold already correct. The two
`ruff` hooks skip because this pass touched no `.py` file.

`git status --short` after the run lists exactly four paths of this cohort's own:
`docs/SPECS/spec-041-channels_router-0_0_14.md` modified, and the rationale companion, this
artifact and the build plan untracked. Every other dirty path is the concurrent `spec-050`
cycle's, unchanged by this pass and never staged or reverted. Two paths dirty now were not in the
build plan's baseline list (`START.md`, `examples/fakeshop/test_query/README.md`); both are that
session's, both grew after this cycle's baseline snapshot, and neither is touched here.

---

## Review (Worker 3)

Scope reviewed: the three-file working-tree diff (`docs/SPECS/spec-041-channels_router-0_0_14.md`
modified, the rationale companion and this artifact new), against HEAD's spec obtained read-only
(`git show HEAD:… > <scratch>/spec-head.md`; never `stash` / `checkout --` / `restore` /
`worktree`) and against source at HEAD: `routers.py` (whole file), `consumers.py`
(`_DEFAULT_REVALIDATION_WINDOW`, `DjangoWebSocketHostValidator`,
`build_revalidating_consumer_class`, `resolved_revalidation_window`), `utils/imports.py`,
`utils/permissions.py`, `auth/sessions.py`, `tests/test_routers.py`, `tests/utils/test_imports.py`,
`tests/utils/test_permissions.py`, `pyproject.toml`, `docs/SPECS/spec-046-transport_security-0_0_14.md`,
plus `docs/TREE.md`, `docs/GLOSSARY.md`, `docs/README.md`, `KANBAN.md` and the shared `.venv`
(`uv pip list`).

### Failability proofs, hot path, floor verification

- **Failability proofs — N/A.** This cycle changes no executable code and introduces no boundary,
  guard, gate or rejection path, so none is owed and none is demanded. Boundaries re-run: **none**;
  boundaries accepted on a builder record: **none** (there are no records, correctly).
- **Hot-path budget — N/A.** The build plan declares hot-path scope `none`; the declaration is
  deliberate (no executable code moves), not an omission.
- **Floor verification — N/A.** The build plan declares floor-verification scope `none`; no
  Django / Strawberry / channels integration seam moves. Floor read for the record only, from
  `docs/builder/BUILD.md` `## Floor verification`: Django **5.2.16** on Python **3.10** with
  strawberry-graphql **0.316.0**. The shared `.venv` is not the floor; `uv pip list` reads
  `strawberry-graphql 0.324.0`, `django 6.1`, `channels 4.3.2`, `daphne 4.2.2` — cited because two
  findings below rest on it.

### High:

None.

No spec sentence asserts behavior the code does not perform; no spec-041 deliverable is absent
without the spec saying so; no contract's five homes contradict each other; no content vanished
from both files (see `What looks solid` for how each was checked).

### Medium:

#### M1 — The spec claims the advertised Django range stops at 6.0; `pyproject.toml` advertises 6.1, and Channels 4.3.2 does not

Five sites state that `channels>=4.3.2` is "the one floor that covers the package's whole advertised
Django range (through 6.0)", justified by "`pyproject.toml` advertises `Framework :: Django :: 6.0`,
and `4.3.2` is the first Channels release with the Django 6.0 classifier, so a lower public floor
would let a Django 6.0 user follow the package's own install hint into an unsupported state":

- `## Slice checklist`, the dependency-gate row (`"Framework :: Django :: 6.0", and 4.3.2 …"`)
- `### Error shapes`, the `channels` absent bullet (`"through 6.0"`)
- `### Decision 5` point 3 (`"pyproject.toml advertises Django 6.0"`)
- `## Edge cases and constraints`, "One Channels floor for the whole advertised Django range"
- `## Definition of done`, the `channels[daphne]` item (`"whole advertised Django range through 6.0"`)

Contradicted by source: `pyproject.toml` #"Framework :: Django :: 6.1" (the classifier landed in
`2b44819d`, 2026-08-06 — a month before this pass), and `.venv`'s installed Django reads **6.1**.
Sharper still, the installed `channels 4.3.2` dist-info carries classifiers only through
`Framework :: Django :: 6.0`, so by the spec's own stated rule — the public hint must name the first
Channels release carrying the classifier for the **highest** advertised Django — a Django 6.1 user
following `pip install 'channels>=4.3.2'` lands exactly where the rule exists to prevent.

The floor *value* is still consistent across its two written copies (`utils/imports.py::CHANNELS_FLOOR`
= `"4.3.2"`, `pyproject.toml` #"channels[daphne]>=4.3.2") and the re-typed drift-catch
`tests/test_routers.py` #"channels>=4.3.2", so nothing in the code is wrong. What is wrong is the
spec's range statement and its justification.

A correct statement would either (a) name the advertised range as it stands (through **6.1**) and
say what floor that range requires, or (b) drop the "whole advertised range" claim and state only
that `4.3.2` is the first Channels release carrying the Django 6.0 classifier. Which of the two, and
whether `CHANNELS_FLOOR` itself is now under-pinned, is a contract-level call — the hint is the
package's public error message — so it is escalated rather than prescribed (see
`### Notes for Worker 1`). Pre-existing at HEAD (the same two "through 6.0" occurrences are in
`git show HEAD:`), and outside F1-F12, but this cycle's stated mandate is that the spec state what
is true at HEAD.

#### M2 — The rationale states, in the rewritten spec's own numbering, that Test-plan rows 2, 3, 7 and 8 have no live counterpart — all four now do

`docs/SPECS/appx/spec-041-channels_router-0_0_14-rationale.md` `## Post-ship corrections`
preamble: "Test-plan rows 2, 3, 7 and 8 have no live counterpart because each asserted the HTTP
GraphQL branch `spec-046` deliberately removed", and `### F10` "*HEAD:* rows 2, 3, 7 and 8 are
correctly gone".

Both sentences describe the **HEAD** spec's rows while the companion sits beside the **rewritten**
spec, in which those four ordinals carry entirely different content — and all four are pinned live:

- row 2 → `tests/test_routers.py::test_http_branch_is_the_supplied_django_application_by_identity`
- row 3 → `::test_construction_rejects_an_omitted_or_unusable_django_application` +
  `::test_graphql_http_consumer_left_the_router_module_entirely`
- row 7 → the WebSocket round trip driven by `::_ws_graphql_data`
- row 8 → `::test_http_branch_delegates_every_path_to_the_supplied_application`

This is the ordinal-citation hazard `START.md` names ("cite contract by CONTENT, never ordinal;
heading rewrite strands every ordinal") landing inside the same pass that did the renumbering. A
correct statement would name the retired rows by content — "the four rows that asserted the HTTP
GraphQL branch (the `HttpCommunicator` GraphQL POST, the fallback-ordering row, and the two
`AuthMiddlewareStack`-on-HTTP rows)" — and say that the ordinals were reused by different content.

#### M3 — The pass reduced a board-owned card-id population from 7 to 5 while both files state it left all 7 untouched

This artifact `### Deferred work` and the rationale's `### `## Doc updates` and the Slice-2 wrap`
both state, present tense, that the spec carries `TODO-BETA-062-0.1.5` ×**3** and
`TODO-BETA-068-0.1.8` ×**4** — "7 occurrences, deliberately left" — precisely because `KANBAN.md`
owns that census and requires one pass over all 34 spec-surface sites rather than a per-spec share.

Re-derived by occurrence count (not matching lines) over both versions:

| id | HEAD spec | spec after this pass |
| --- | --- | --- |
| `TODO-BETA-062-0.1.5` | 3 (L802, L1044, L2044) | **2** (L506, L1623) |
| `TODO-BETA-068-0.1.8` | 4 (L153, L1378, L2047, L2108) | **3** (L1044, L1626, L1692) |

The two that disappeared were destroyed, not moved: HEAD L1044's "`TODO-BETA-062-0.1.5` territory"
sits in Decision 2's rejected alternative, which is now rationale L320-322 **without** the id; HEAD
L153's `068` sits in the Revision-1 log entry, condensed into `## Round vocabulary` **without** it.
Neither id appears anywhere in the companion.

So the pass discharged 2 of the 7 — the exact partial share `KANBAN.md` #"discharging 3 here is
exactly the partial fix" warns against — and `KANBAN.md`'s census, which records **spec-041 3** for
the `062` population, is now off by one with no record of why. A correct statement would either
report the post-pass counts (2 and 3) and note that two occurrences left with their enclosing text,
or restore the two ids so the board census stays true.

#### M4 — Four stated counts in this artifact read as measured and do not re-derive

`docs/builder/BUILD.md` `## Claims are proven mechanically, never accepted on prose` makes an
unverified count of this shape a Medium finding; each of these propagates as fact to the next
reader.

1. `### Anchor and citation discipline`: "Inside the spec, the old anchor had **11 uses**; all 11
   now read `#decision-6--constructor-and-composition`."
   Re-derived: `grep -c '](#decision-6--constructor-parity' <HEAD spec>` = **9**;
   `grep -o '](#decision-6--constructor-and-composition)' <current spec> | wc -l` = **4** (a fifth
   occurrence of that slug is the `[rationale-decision-6…]` link **definition**, which targets the
   companion, not the spec heading). Five of the nine citing passages were removed or rewritten by
   this same pass, which is legitimate — but "11, all 11 moved" is wrong in both halves. Correct:
   9 in-page uses at HEAD, 4 in-page uses now, 5 retired with their enclosing text.
2. `### Findings beyond F1-F12`: "Three process-provenance labels in standing prose (`finding P1.1`
   twice, `finding P1.2` once)."
   Re-derived: `grep -o 'P1\.[0-9]' <HEAD spec>` = **9** occurrences — `P1.1` ×6, `P1.2` ×1,
   `P1.4` ×2 — at HEAD L466, L584, L1489, L1525, L1871, L1886, L1899, L1994, L2104, every one in
   standing prose (none inside the `Revision history` block). The **removal is complete and
   correct** (0 remain in the spec, 0 in the companion, verified), and each removal restated the
   why rather than only deleting the label — only the count and the vocabulary are wrong.
3. `### Link-convention verification`: "In-page anchors: **18** in the spec, 9 in the companion."
   Re-derived over distinct `](#…)` targets: **17** in the spec, 9 in the companion; 0 broken in
   both (independently confirmed — see `What looks solid`).
4. M3 above is the fourth.

Two claims in the same section **did** re-derive and are recorded so they are not re-checked: the
repo-wide grep for the old Decision-6 slug returns exactly **1** hit (the companion's own record),
and "33 files name the spec" is exact once this cycle's four new files (rationale, artifact, build
plan, Worker 1's memory) are subtracted from today's 37.

### Low:

#### L1 — "verified at the installed strawberry 0.316.0" is no longer true of the installed strawberry

`docs/SPECS/spec-041-channels_router-0_0_14.md` L883 (Decision 5) and L974 (Decision 7) state
"verified at the installed strawberry 0.316.0". `uv pip list` reads **0.324.0**. The third
occurrence (L401) sits in `## Current state` and is licensed by the section's vintage framing; these
two are standing Decision prose. `0.316.0` is still the correct **floor**, so nothing downstream is
wrong; the sentence just names the wrong thing. Correct form: "verified at the pinned
`strawberry-graphql` floor" (single-sited as `utils/imports.py::STRAWBERRY_FLOOR`), which is what
the same pass already did for every other floor mention.

#### L2 — A citation in the companion names no resolvable path

Rationale, Decision 11's "Derivation of the blast radius": "verified at the installed strawberry
`0.316.0` in `handlers/http_handler.py::get_context`". No first-party `handlers/http_handler.py`
exists; the file is `strawberry/channels/handlers/http_handler.py` inside the venv. Every other
`path::Symbol` in both files resolves (18 checked, all OK — see `What looks solid`), so this one
reads like a first-party rule-27 citation and is not one. `scripts/check_citations.py` cannot see
it (it reads `.py` files and `KANBAN.md`). Correct form: name the upstream path in full and mark it
as upstream, as `## Borrowing posture` does for `strawberry/channels/router.py`.

#### L3 — The `## Test plan`'s ordered list renumbers 18 to 17 when rendered

Rows 16 and 18 sit in one ordered-list block under "the package request contract", so markdown
renders the second as **17**; the real row 17 then appears under a later heading. Eight prose
references to "Test 18" therefore point at a list item labelled 17 in any renderer. Pre-existing at
HEAD and unchanged by this pass, but the pass rewrote this section extensively and the numbering is
load-bearing for `## Definition of done` and for the companion's change records.

#### L4 — The stated reason for keeping `## Risks and open questions` as a heading is falsified by the same pass

This artifact `### What moved to the rationale companion` item 4: "The spec keeps a four-line
pointer in place of the section, because the section heading is cited from `## Current state` and
elsewhere." Both of those citations were removed in this diff (`## Current state`'s "and carried in
[Risks]" and the Predecessors' "and [Risks]"), and `grep -c 'risks-and-open-questions'` over the
spec now returns **1** — the `[rationale-risks]` link definition pointing at the **companion**. No
in-page citation of the spec's own Risks anchor survives, and the earlier sweep found no external
citer of any `spec-041` heading anchor. Keeping the section is fine; the recorded reason for it is
not the reason.

#### L5 — Slice-checklist row names the base consumer where the default is the package's subclass

`## Slice checklist`, the `routers.py` row: the `"websocket"` composition "over
`strawberry.channels`'s `GraphQLWSConsumer`". At HEAD `routers.py::_build_router_class_uncached`
mounts `build_revalidating_consumer_class(GraphQLWSConsumer)` by default — a subclass, which
`### Decision 7` states correctly ("The one consumer class the package does define is a *subclass*
of that engine consumer"). The two homes do not contradict each other outright (the subclass *is* a
`GraphQLWSConsumer`), but the checklist row reads as though the engine class is mounted directly.
Decision 6's `<consumer>` placeholder is the right spelling to mirror.

#### L6 — The pair spells source paths two ways

The spec uses package-relative `path::Symbol` (`views.py::DjangoGraphQLView`,
`utils/imports.py::CHANNELS_FLOOR`, `consumers.py::build_revalidating_consumer_class`); the
companion uses repo-relative (`django_strawberry_framework/views.py::DjangoGraphQLView`). Both
resolve; `AGENTS.md` rule 27's own examples are repo-relative. Pre-existing in the spec, new in the
companion, and worth one convention across a file pair that is read together.

### DRY findings

- **A third written copy of the revalidation-window default.** `## User-facing API`'s constructor
  block spells `websocket_revalidation_window=0.0`. The source of truth is
  `consumers.py` #"_DEFAULT_REVALIDATION_WINDOW = 0.0", which `routers.py`'s signature reads by
  name; `spec-046` Decision 11 is the owning contract. Decision 6 states the rule this violates in
  the same breath ("duplicating them here would create a second copy to rot"). The block's job — to
  show a `routers.py` reader the parameter *shape* — is served by the name and the comment without
  the literal. Same shape, weaker: `websocket_url_pattern=r"^graphql/?$"` duplicates
  `routers.py`'s default, though that one the spec's own `## Edge cases` bullet also has to state to
  be useful.
- **Scope discipline held everywhere else.** The four `spec-046`-owned surfaces are stated once, in
  Decision 6, with the ownership named and the contract pointed at; `## Out of scope` gained the
  matching single bullet. I looked specifically for a second copy of the Host-validator rules, the
  body/encoding bounds, the injection seam's rejection shapes and the revalidation semantics in
  `spec-041` — there is none. The `## Edge cases` decision not to add a Host bullet (recorded in
  `### Spec changes made`) is the right call for the same reason.
- **No duplication introduced between the pair.** Text in the companion is gone from the spec and
  vice versa; the one deliberate overlap (Decision 6's old heading, quoted in the companion) is the
  anchor record and is correct.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` is **empty** — `__all__` and the re-export list
are unchanged. Consistent with `## Definition of done`'s no-root-re-export item and with
`### Decision 3` ("the **root** package `__all__` stays unchanged and channels-free").

### CHANGELOG sanity

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

The slice touches only spec surfaces; everything below was read end-to-end.

- Version strings and card ids match HEAD: `KANBAN.md` carries `DONE-041-0.0.14`, and the three
  siblings the spec now names `DONE-042/043/044-0.0.14` are all in Done. `docs/GLOSSARY.md`'s
  `DjangoGraphQLProtocolRouter` entry reads `**Status:** shipped (0.0.14)`, which is what the spec's
  preamble now claims. `docs/TREE.md` carries the real docstring-derived `routers.py` row and the
  `tests/test_routers.py` row, so the Slice-2 doc obligations are genuinely discharged.
- Markdown links: every definition's target exists on disk **and** was checked for depth and group.
  The companion sits one level deeper and its paths re-relativize correctly (`../../../GOAL.md`,
  `../../GLOSSARY.md`, `../spec-046-….md`, and the external
  `../../../../strawberry-django-main/strawberry_django/routers.py` against the spec's
  `../../../…`) — I resolved each rather than trusting existence, because a same-named file one
  level up masks depth rot. `docs/SPECS/appx/` definitions sit under `<!-- docs/SPECS/ -->` in both
  files, per `START.md`.
- No obsolete "planned" / "coming soon" / old-version wording survives in the surfaces this slice
  updated. The three retained falsified observations in `## Current state` are licensed by the
  section's vintage framing and were graded clause by clause; the DoD's `0.262.0` line, which gets
  no such licence, is corrected (F5).
- No archival move was owed or performed: the spec is already at `docs/SPECS/`.
- No script-rendered doc is regenerated by this slice, so the staging-docstring check does not apply.
- The spec never narrates its own history: 0 hits for `P1.`, `High:`, `P0`, `review round`,
  `Revision history`, `previously`/`Previously`, `as of `, `amend`/`Amend`, `supersed`/`Superseded`,
  `retract`. The amendment banner, the nine-entry revision history and the retraction wording are
  all gone from the spec and all present in the companion.

### What looks solid

Each of these was verified mechanically or by reading the asserted property in the source body, not
by the presence of a citation.

- **Every reconciled contract matches HEAD.** F1 constructor
  (`routers.py::_build_router_class_uncached`'s inner `__init__`: `schema` positional,
  `django_application` required, three keyword-only params — matches the spec's block, and
  `_DEFAULT_REVALIDATION_WINDOW` is `0.0` so the rendered default is right); F2 `"http": django_application`
  verbatim; F3 `DjangoWebSocketHostValidator(AllowedHostsOriginValidator(AuthMiddlewareStack(URLRouter([...]))))`
  in that order; F4 only `GraphQLWSConsumer` imported; F5 `STRAWBERRY_FLOOR = "0.316.0"` and
  `pyproject.toml` #"strawberry-graphql>=0.316.0" and the re-typed
  `tests/test_routers.py` #"_STRAWBERRY_FLOOR_SUBSTRING"; F6 all three hints interpolate
  `CHANNELS_FLOOR` / `STRAWBERRY_FLOOR`; F7 `_ROUTER_CLASS_LOCK` with the double-check in
  `_build_router_class`; F8 `_channels_scope` resolving `consumer.scope` then `request.scope` and
  `ChannelsRequestAdapter._scope_value` converting a raising mapping into `ConfigurationError`.
- **F9 is stated at exactly the precision the source supports, and attributed correctly.**
  `auth/sessions.py::login_supported` returns `transport is not Transport.CHANNELS_WEBSOCKET` —
  `False` on any WebSocket, engine-independent; `::logout_supported` returns
  `not uses_signed_cookie_sessions()` for a WebSocket. The spec's `## Non-goals` and Decision 11
  say precisely that. The `spec-040` attribution holds at source:
  `auth/sessions.py` #"subsystem (spec-040 Decision 3)" is the file's only `spec-040` citation and
  its only `spec-046` citation is the per-operation revalidation, a different contract. Worker 1's
  correction of the build plan's wording was the right call.
- **Nothing was skipped in the code — re-derived independently of Worker 0's table.** I walked
  `## Slice checklist`, `## Implementation plan`, `## Test plan` and `## Definition of done` and
  found a live symbol or test for every deliverable: `pyproject.toml` #"channels[daphne]>=4.3.2";
  `utils/imports.py::require_optional_module` with no `feature_label` plus its four unit rows
  (`tests/utils/test_imports.py::test_require_optional_module_returns_the_real_module_on_success`,
  `::…_raises_the_hint_and_chains_the_original`, `::…_does_not_memoize`,
  `::…_normalizes_a_hostile_install_hint`); `routers.py::require_channels` as a thin wrapper;
  one `_CHANNELS_INSTALL_HINT` plus the split `_CHANNELS_BROKEN_HINT` /
  `_STRAWBERRY_CHANNELS_BROKEN_HINT`; `routers.py::__getattr__` with the scoped
  `# noqa: F822 - PEP 562 lazy export`; `utils/permissions.py::ChannelsRequestAdapter` /
  `::_channels_scope` / `::_channels_request_adapter`. Test-plan rows 1-18 map to live rows
  (1 → `test_router_is_a_protocol_type_router_mapping_exactly_http_and_websocket`, 4 →
  `test_websocket_branch_wraps_origin_validator_outside_the_auth_stack`, which unwraps the Host
  validator first exactly as the row now claims, 5, 6 (incl.
  `test_concurrent_first_class_access_returns_one_cached_class`), 8, 9 (three origin directions,
  parametrized), 10 (both halves — `consumer_initkwargs["schema"] is recording_schema` **and** the
  recording extension firing over the WebSocket branch), 11-15, 16 with all six unit-level shape
  rows in `tests/utils/test_permissions.py`, 17 parametrized over both halves, 18). Row 7 has no
  row of its own — the WebSocket GraphQL round trip it describes is exercised through
  `_ws_graphql_data` inside rows 10 and 16 — which satisfies the DoD's "at least one real
  `WebsocketCommunicator` GraphQL round trip" and is not a gap, only worth knowing.
- **The four `spec-046` decision numbers the spec cites all exist and say what it says they say**:
  Decisions 2/3/6 (direct HTTP dispatch, required `django_application`, package view), 4
  (`websocket_url_pattern`, exact default), 5 (the intentional breaking change), 11 (the injection
  seam), 13 (which tests change), 17/18 (multipart), 19 (the Host boundary). No duplicated contract
  in either direction.
- **Link and anchor integrity, measured rather than assumed.** Spec: 90 in-page anchor uses over 17
  distinct targets, **0 broken**; 82 link definitions, 82 uses, **0 undefined, 0 unused**; all
  definition targets exist from the spec's own directory, all cross-file anchors resolve into the
  companion. Companion: 21 uses over 9 distinct targets, 0 broken; 26 definitions, 26 uses, 0
  undefined, 0 unused; all 12 `[dN]` back-anchors resolve into the spec **as rewritten**, including
  the renamed Decision 6. Ten canonical group headers present, in order, in both files.
- **Citations resolve and none is wrapped.** All 18 distinct `path::Symbol` refs across the pair
  resolve to a real definition (L2 is the one exception, an upstream file). All four `#"substring"`
  citations still match a line of the named source: `routers.py` #'"http": django_application'
  (3 matches), `routers.py` #"_ROUTER_CLASS_LOCK" (2),
  `tests/test_routers.py` #"_STRAWBERRY_FLOOR_SUBSTRING" (2),
  `pyproject.toml` #"strawberry-graphql>=0.316.0" (1). No `path::Symbol` wraps across two lines in
  either file.
- **The move was a move.** I walked all nine revision entries item by item against the companion:
  every substantive item is homed (the daphne extra, both floor corrections, the two-sided restore,
  the conftest-attribution withdrawal, the Channels-vs-Django localhost list, the DEBUG
  unreachability, the `docs/TREE.md` quotations, the `~30 lines` tightening, the `BaseMiddleware`
  classification, the `GOAL.md` anchoring, the single-floor collapse, Decision 11's creation, the
  threadpooling retraction, `feature_label`'s removal, `__all__`, Test 10's recording extension,
  Test 18, the split wrap, the missing-`Origin` direction, both glossary passes with the CSV's
  16→22→30 growth). Eleven `Alternatives considered (and rejected)` blocks and
  `## Risks and open questions` in full are present in the companion and absent from the spec, each
  risk now carrying its outcome. Nothing that left the spec is missing from both files except the
  two card-ids of M3 and a handful of purely editorial revision notes ("root link definitions
  alphabetized", "durable review-document citations folded into Decision references") whose loss is
  correct.
- **The keying works as a review instrument.** Every companion entry names its decision by heading
  and anchor; the `## Post-ship corrections` block is keyed by finding number and cross-linked from
  the decision entries; `## Round vocabulary` earns its place by letting nine change records cite a
  round without re-glossing it. I used it twice during this review to check whether an alternative
  I was about to raise had already been decided (the narrow `.user`/`.session` adapter, and
  subclassing the consumers), and it answered both — which is the test that section is for.
- **Gates re-run at the working tree, with their inputs stated.**
  `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-041-channels_router-0_0_14.md`
  → `OK: 30 terms - all have glossary entries and at least one spec link.` (matches the 30 data rows
  in the untouched `…-terms.csv`, which is 31 lines with its header). Note what it compares — term
  and anchor only, never the `notes` prose — so its green says nothing about the glossary vocabulary
  *used* in the spec. `scripts/check_citations.py` reads `.py` files and `KANBAN.md` only, so it is
  blind to both files this pass wrote; Worker 1 stated that limitation correctly, and the manual
  resolution above is what stands in for it. No `pytest`, no `--cov*` flag, no write-mode `ruff`.
- **Deliverable hygiene.** No `TODO(spec-041 …)` anchor survives in any source file (the two
  repo-wide hits are prose mentions inside the spec and the companion). `git status --porcelain`
  shows exactly this cohort's four paths for this cycle; every other dirty path belongs to the
  concurrent `spec-050` session and was neither read as this cycle's output nor touched.

### Temp test verification

None created. `docs/builder/temp-tests/041/` was not used: this cycle changes no executable code, so
there was no behavior to demonstrate — every check above is a document-versus-source read or a
mechanical sweep, and both are recorded with their commands rather than with a scratch file.

### Notes for Worker 1 (spec reconciliation)

- **Escalated (M1): the Channels floor's advertised-range claim is contract-level.** The spec's
  rule is that the public install hint must name a floor covering the package's whole advertised
  Django range, because the hint is the error message a deploying consumer follows. `pyproject.toml`
  now advertises `Framework :: Django :: 6.1` and CI exercises it, while `channels 4.3.2`'s own
  classifiers stop at 6.0. Resolution paths, for the maintainer rather than a worker: **(a)** treat
  the range statement as the defect — restate the five sites as "`4.3.2` is the first Channels
  release carrying the Django 6.0 classifier", dropping the whole-range promise, and file the floor
  question on the card that owns `CHANNELS_FLOOR`; **(b)** treat the floor as the defect — a
  `CHANNELS_FLOOR` bump plus the `pyproject.toml` row, which is a `.py` + metadata change this
  cohort's ownership partition does not permit and which needs its own suite run; or **(c)** record
  a deliberate decision that the advertised 6.1 classifier outran the Channels ecosystem and the
  floor stays, with the reason written down so the next reader does not re-derive it. Only (a) is
  inside this cycle's write scope.
- **M3 crosses a board-owned population.** `KANBAN.md` records `spec-041 3` for the
  `TODO-BETA-062-0.1.5` census and explicitly forbids a per-spec partial discharge. Whichever way
  M3 is resolved, the board's figure for `spec-041` and the companion's deferred-work note must end
  up saying the same number, or the next custodian re-derives a population that has silently moved
  under them — the failure mode that census bullet was written to prevent.
- **M2 and M4 are the same root cause and deserve one habit, not four fixes:** an ordinal or a
  count written in the same breath as the lesson it illustrates. Each of the four figures is
  re-derivable in one command; none was re-derived after the edits that changed it.
- **Not a finding, recorded so it is not re-raised:** the DoD deliberately omits the construction
  lock (F7), and the reason given — the DoD is `spec-041`'s completion claim and the lock is
  post-ship hardening this card did not ship — is right and should stand. Same for the decision not
  to give the Host boundary its own `## Edge cases` bullet.

### Review outcome

`revision-needed` — four Medium findings (M1-M4) and six Low findings are unresolved and carry no
recorded rejection reason. The reconciliation itself is accurate: every contract the rewritten spec
states was checked against the source body rather than the citation, all five homes agree for every
contract the pass touched, the rationale carries everything that left the spec keyed to a resolvable
anchor, and no chronology survives in the spec. What fails the gate is a stale metadata claim the
reconciliation did not catch (M1), a companion sentence that is false about the spec it accompanies
(M2), a board-owned population silently reduced while both files say it was left alone (M3), and
four stated counts that do not re-derive (M4).

---

## Build report — apply-changes pass (Worker 1, acting in place of Worker 2)

Same pass continuing under Worker 3's review as the contract. Every Medium, every Low and the DRY
finding is closed below; none is rejected, and one half of M1 is escalated rather than acted on
because it is a dependency decision outside this cohort's writable set. Four of my own earlier
figures were re-measured and corrected in place, each marked at the site with a pointer here.

### Findings closed

- **M1 — the contract-level floor claim.** All five homes rewritten. They now state the current
  contract plainly, with no chronology: `4.3.2` is the declared floor and the first Channels
  release carrying the `Framework :: Django :: 6.0` classifier, while `pyproject.toml`'s
  advertised Django range runs `5.2` / `6.0` / `6.1` and no Channels release at this floor
  carries a 6.1 classifier, so the floor's coverage reaches 6.0 and stops there. The five homes:
  `## Slice checklist` dependency-gate row; `### Error shapes` `channels`-absent bullet;
  `### Decision 5` point 3; `## Edge cases and constraints` (the bullet's lead-in also changed,
  from "One Channels floor for the whole advertised Django range" to "One Channels floor, and
  what it does and does not classify" — it is a bold lead-in, not a heading, so it anchors
  nothing, and a repo-wide grep for the old phrase returns **0** hits outside this artifact,
  whose two occurrences are Worker 3's quotation of it and this sentence's own). `## Definition
  of done` `channels[daphne]` item.
  Post-sweep: `grep -o 'whole advertised Django range'` = **0**, `grep -o 'through 6.0'` = **0**
  over the spec. Both source facts re-read here rather than taken on trust: `pyproject.toml`
  lines 29-31 carry `Framework :: Django :: 5.2` / `6.0` / `6.1`, and
  `.venv/lib/python3.14/site-packages/channels-4.3.2.dist-info/METADATA` carries five
  `Framework :: Django` classifiers topping out at `6.0`. Whether the floor itself should move is
  escalated — see `### Escalated to the maintainer`.
- **M2 — the stale test-row ordinals in the companion.** Both sentences (the
  `## Post-ship corrections` preamble and the `### F10` entry) now name the four retired rows by
  content — the `AuthMiddlewareStack`-wraps-HTTP row, the HTTP fallback-route **ordering** row,
  the `HttpCommunicator` GraphQL POST round trip, and the non-GraphQL-path fallback row — read
  off HEAD's own `## Test plan` rather than off the finding text, and each says explicitly that
  the rewritten spec reuses those ordinals for different content. The two surviving ordinal
  citations in the companion (`Test 16`, `Test 18` in two Revision-8 change records) were checked
  and left: both ordinals carry the same content in the rewritten spec, so they point where they
  claim to.
- **M3 — the card-id population.** Both files now state the re-measured figures, and the
  companion additionally states *why* the spec-side count fell and where the two occurrences
  went. Counts, derivation and the board reconciliation are in
  `### Counts re-measured in this pass`. The two ids were **not** restored: the finding's own
  remedy set offers either, and restoring text into a deliberately condensed rejected-alternative
  and a deliberately condensed revision-log entry would re-inflate the move to keep a numeral
  that the board is going to renumber anyway.
- **M4 — four counts that did not re-derive.** All four re-measured by me, from the instrument
  up, and corrected at their sites: the Decision-6 anchor uses, the process-provenance labels,
  the spec's in-page anchor targets, and M3. Derivations below.
- **L1 — "verified at the installed strawberry 0.316.0".** Both standing-Decision occurrences
  (Decision 5's `channels.db` module-level-import claim, Decision 7's `strawberry.channels`
  export claim) now read "verified at the pinned `strawberry-graphql` floor, single-sited as
  `utils/imports.py::STRAWBERRY_FLOOR`" — the form the same pass already used for every other
  floor mention. The `## Current state` occurrence is untouched: that section's vintage framing
  licenses it, as Worker 3 said. Both underlying claims were re-read at the installed version
  before restating, so neither sentence is true only of the floor:
  `strawberry/channels/handlers/http_handler.py` still imports `channels.db` at module level and
  `strawberry/channels/__init__.py` still exports `GraphQLWSConsumer`.
  Shared `.venv` read with `uv pip list` at this pass: `channels 4.3.2`, `daphne 4.2.2`,
  `django 6.1`, `strawberry-graphql 0.324.0`. The `.venv` is not the floor; the floor is
  Django **5.2.16** on Python **3.10** with strawberry-graphql **0.316.0**, taken from
  `docs/builder/BUILD.md` `## Floor verification`.
- **L2 — the unresolvable citation.** The companion's `handlers/http_handler.py::get_context` now
  reads `strawberry/channels/handlers/http_handler.py::GraphQLHTTPConsumer.get_context`, marked
  in prose as the checked-out upstream and not first-party, with the sync twin named as
  `::SyncGraphQLHTTPConsumer.get_context`. Both were read at source before the rewrite:
  `http_handler.py` defines `GraphQLHTTPConsumer.get_context` and
  `SyncGraphQLHTTPConsumer.get_context`, and the two bodies return the same two-key dict. The
  version literal went with it rather than being corrected to `0.324.0` — the claim is about
  upstream's shape, which no version in standing prose helps a reader check.
- **L3 — the `## Test plan`'s renumbering.** The authenticated-session row shared an ordered-list
  block with the request-contract row, so markdown re-numbered it to 17 while the real row 17 sat
  under a later heading, and eight prose references to "Test 18" pointed at a list item labelled
  17. Fixed structurally rather than by renumbering: a bold group lead-in
  (`**Channels-present — the session actor over the handshake:**`) now separates the two, so the
  `18.` item starts its own list and renders as 18. No prose reference moved, and the `## Test
  plan`'s numbering stays what `## Definition of done` and the companion's change records cite.
- **L5 — the slice-checklist consumer.** The `routers.py` row now reads "over whatever consumer
  is mounted — by default the package's revalidating subclass of `strawberry.channels`'s
  `GraphQLWSConsumer`", mirroring Decision 6's `<consumer>` placeholder and agreeing with
  Decision 7's "the one consumer class the package does define is a *subclass*".
- **L6 — one path spelling across the pair.** The companion's package-file symbol paths were the
  outlier, not the spec's: measured before editing, the spec carried **17** package-relative
  package-file occurrences (`utils/imports.py::` ×9, `views.py::` ×6, `consumers.py::` ×1,
  `utils/inputs.py::` ×1) and the companion **16** repo-relative ones. The repo's own idiom
  settled it rather than a preference — `docs/SPECS/spec-046-transport_security-0_0_14.md` and
  `docs/SPECS/appx/spec-046-transport_security-0_0_14-rationale.md`, the model this companion was
  written from, both spell package files package-relative and everything else repo-relative — so
  the companion's 16 were converted down, together with its three `#"substring"` citations and
  three bare `django_strawberry_framework/…` file mentions. After the conversion the only
  repo-relative package path left in the companion is its `<!-- django_strawberry_framework/ -->`
  link definition, which must be a path from the file. `tests/…` stays repo-relative in both.
- **DRY — the third written copy of the revalidation-window default.** `## User-facing API`'s
  constructor block read `websocket_revalidation_window=0.0`; it now reads
  `websocket_revalidation_window=_DEFAULT_REVALIDATION_WINDOW`, which is what
  `routers.py::_build_router_class_uncached`'s inner `__init__` signature reads at HEAD, and the
  paragraph under the block names `consumers.py::_DEFAULT_REVALIDATION_WINDOW` as the one written
  value. The literal `0.0` no longer appears in the spec. The block's `websocket_url_pattern`
  default is kept as Worker 3 allowed: the `## Edge cases` bullet has to state the pattern to be
  useful, so removing it from the signature block would not retire the copy.
- **L4 — the recorded reason for keeping `## Risks and open questions` as a spec heading.** The
  finding is accepted and the reason is corrected here rather than in the prior section, which
  this pass is not otherwise licensed to rewrite. The reason given there — that the heading is
  cited from `## Current state` and elsewhere — was falsified by this same pass, which removed
  both citations. The real reason the four-line pointer stays: a decision's reader must be able to
  see that a risk ledger exists and where it went, which is rule 1 of the rationale move
  ("every decision keeps a one-line pointer naming what was moved and where"). Re-measured now:
  `grep -c 'risks-and-open-questions'` over the spec returns **1**, the `[rationale-risks]`
  definition pointing into the companion; **0** in-page uses of the spec's own Risks anchor
  survive, and the earlier sweep found **0** external citers of any `spec-041` heading anchor.

### Counts re-measured in this pass

Measured as written, by occurrence and not by matching line, over the working tree and over
`git show HEAD:docs/SPECS/spec-041-channels_router-0_0_14.md` written read-only to a scratch path
outside the repo. Populations printed rather than assumed.

| Claim | Earlier figure | Re-measured | Instrument |
| --- | --- | --- | --- |
| Decision-6 anchor, in-page uses at HEAD | 11 | **9** | `grep -o '](#decision-6--constructor-parity[^)]*)' <HEAD spec> \| wc -l` |
| Decision-6 anchor, in-page uses now | "all 11 moved" | **4** | `grep -o '](#decision-6--constructor-and-composition)' <spec> \| wc -l`; a 5th occurrence of the slug is the `[rationale-decision-6…]` definition, which targets the companion, and a 6th is that definition's use as a ref label — neither is an in-page anchor |
| Decision-6 anchor, retired with enclosing text | — | **5** | 9 − 4 |
| Process-provenance labels at HEAD | 3 (`P1.1` ×2, `P1.2` ×1) | **9** (`P1.1` ×6, `P1.2` ×1, `P1.4` ×2) | `grep -o 'P1\.[0-9]' <HEAD spec> \| sort \| uniq -c`; all 9 outside the `Revision history` block, so all 9 were standing prose |
| Process-provenance labels now | — | **0** spec, **0** companion | `grep -c 'P1\.[0-9]'` on each |
| Spec in-page anchor targets | 18 | **17** distinct over **90** uses, 0 broken | slug every heading, difference against `](#…)` uses with code spans and fenced blocks stripped |
| Companion in-page anchor targets | 9 | **9** distinct over **21** uses, 0 broken | same |
| `TODO-BETA-062-0.1.5` | 3 "deliberately left" | HEAD spec **3** → spec **2**, companion **1** | `grep -oF` per file |
| `TODO-BETA-068-0.1.8` | 4 "deliberately left" | HEAD spec **4** → spec **3**, companion **1** | `grep -oF` per file |

Worker 3's re-derived numbers and mine agree in every cell. They were measured independently:
the commands above were run in this pass against the working tree and the HEAD snapshot, not
copied from the review.

**What the board owner has to reconcile (M3's second obligation).** `KANBAN.md` is not writable
this cycle and was not touched. Its card-id census records `spec-041 3` inside the 34
spec-surface enumeration for the `TODO-BETA-062-0.1.5` population. That figure was taken when
`spec-041` was one file. The pair now carries **3** occurrences of that id — **2** in the spec and
**1** in the companion — so the census total still sums, but only **2** of the 3 are renumberable
sites: the companion's occurrence quotes the id inside a sentence declaring it stale, which is
the class the census already excludes from its own sweepable total for the board's own rows. The
`TODO-BETA-068-0.1.8` family, which that census does not yet enumerate, is **4** across the pair —
**3** in the spec, **1** in the companion, same split. Two spec-side occurrences (one of each id)
left with the passages that carried them: HEAD's `062` inside Decision 2's rejected alternative,
condensed into the companion's alternatives block without the numeral, and HEAD's `068` inside a
revision-log entry, condensed into `## Round vocabulary` without it. Nothing was renumbered.
Whoever runs the census pass should expect **5** renumberable sites in the `spec-041` pair.

### Escalated to the maintainer (not acted on)

**The Channels floor versus the advertised Django range.** Verified at source in this pass:
`pyproject.toml` advertises `Framework :: Django :: 5.2`, `6.0` **and `6.1`**; the installed
`channels 4.3.2` dist-info stops at `Framework :: Django :: 6.0`. The spec's own rule is that the
public install hint must name a floor covering the advertised range, because the hint is the
error message a deploying consumer follows — and at `6.1` that rule no longer terminates. The
spec now states what is verifiably true and makes no whole-range promise; whether the floor
itself should move is a dependency decision, and `pyproject.toml` is outside this cycle's
writable set regardless.

Alternatives considered for the escalated half, each with the reason it lost:

- **Bump `CHANNELS_FLOOR` and the `channels[daphne]` row to a 6.1-classifying Channels release.**
  Lost here, not on merit: it is a `.py` plus packaging-metadata change this cohort's ownership
  partition does not permit, it needs its own suite run and a `uv.lock` regeneration, and no
  Channels release carrying a 6.1 classifier exists at the version installed here to bump to.
- **Qualify or drop the `Framework :: Django :: 6.1` classifier.** Lost because it is a claim
  about the package's own tested surface, not about Channels: CI exercises 6.1, and withdrawing
  the classifier to make one soft dependency's range statement true would understate what the
  package supports for every consumer who never installs `channels`.
- **Leave the spec's whole-range wording and footnote the gap.** Lost because the wording is
  falsifiable and now false; a footnote leaves the reader two statements and no way to tell which
  is current, which is the half-reconciled state the custody rules forbid.
- **Say nothing about 6.1 in the spec at all.** Lost because the spec's stated justification for
  the floor is the advertised range; a reader who checks `pyproject.toml` finds 6.1 immediately
  and cannot tell whether the omission is a decision or an oversight.

**Also for the maintainer, not edited.** `pyproject.toml` carries a comment ending "…the
`Framework :: Django :: 6.0` classifier the package itself advertises", which the `6.1` addition
has made stale. It sits three lines below the `channels[daphne]>=4.3.2` row but belongs to the
`django-debug-toolbar>=7.0.0` row above it — the same reasoning, a different soft dependency, so
whoever settles the Channels question settles this one too. Out of scope here; recorded, not
touched.

### Out-of-cycle observations from this pass

- **No code defect found.** This pass read `routers.py`, `consumers.py`, `utils/imports.py`,
  `pyproject.toml` and the installed `channels` / `strawberry` metadata again, and wrote no `.py`
  file. Nothing for Worker 0 to re-partition.
- `docs/SPECS/spec-041-channels_router-0_0_14-terms.csv` untouched, as required; the glossary gate
  still reads 30 terms.

### Gate results (apply-changes pass)

Each recorded with the instrument's actual input, since two of the three cannot see the files
this pass wrote.

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-041-channels_router-0_0_14.md`
  → `OK: 30 terms - all have glossary entries and at least one spec link.`, exit **0**. Input: the
  spec plus its untouched `-terms.csv`. It compares term and anchor only — the `notes` prose
  beside them is ungated, so its green says nothing about the vocabulary this pass rewrote.
- `uv run python scripts/check_citations.py --check` (whole tree) →
  `OK: 981 citations resolve (814 in 442 .py files, 167 in KANBAN.md).`, exit **0**. Input: first-party
  `.py` files and `KANBAN.md` — **not** either markdown file this pass wrote. Its green is evidence
  that this pass broke no existing citation, nothing more.
- `uvx pre-commit run --files …` with the four explicit paths — recorded in
  `### Pre-commit result (apply-changes pass)` below. Never the default, which is a repo-wide
  auto-fix that would rewrite the concurrent `spec-050` session's untracked files.
- No `pytest`. No `--cov*` flag. No write-mode `ruff` on anything.

### Link, anchor and citation audit (apply-changes pass)

Re-run over both files after every edit, populations printed rather than assumed.

- **Spec:** 82 link definitions, 82 distinct labels used over **291** occurrences — **0 undefined
  uses, 0 unused definitions**. **90** in-page anchor uses over **17** distinct targets, **0
  broken**. All ten canonical group headers present, in order. Every definition target exists
  from the spec's own directory and every cross-file anchor into the companion resolves.
- **Companion:** 26 link definitions, 26 distinct labels used over **62** occurrences — **0
  undefined, 0 unused**. **21** in-page anchor uses over **9** distinct targets, **0 broken**.
  Ten group headers present, in order. Every definition target exists from
  `docs/SPECS/appx/`, checked by resolving the path rather than by existence alone, and every
  back-anchor into the spec resolves **as rewritten**.
- **Symbol citations:** **46** `path::Symbol` occurrences across the pair over **21** distinct
  refs; all resolve to a real definition by AST lookup except the one deliberate upstream ref
  (`strawberry/channels/handlers/http_handler.py::GraphQLHTTPConsumer.get_context`), which the
  prose marks as upstream. No `path::Symbol` wraps across two lines in either file.
- **`#"substring"` citations:** the three in the companion still match their named source —
  `routers.py` #'"http": django_application' (3 matches), `routers.py` #"_ROUTER_CLASS_LOCK" (2),
  `tests/test_routers.py` #"_STRAWBERRY_FLOOR_SUBSTRING" (2).
- **The spec still never narrates its own history**, re-swept after these edits: 0 hits for
  `previously` / `Previously`, `as of `, `Revision history`, `P1.`, `review round`.

### Pre-commit result (apply-changes pass)

Recorded below with the command that produced it.

`uvx pre-commit run --files docs/SPECS/spec-041-channels_router-0_0_14.md docs/SPECS/appx/spec-041-channels_router-0_0_14-rationale.md docs/builder/bld-041-slice-1-rationale_and_spec_reconciliation.md docs/builder/build-041-channels_router-0_0_14.md`

```
kanban tracked path constants...................................Passed
source layout (py trailing commas + ascii-only; md link-def
  scaffold; json/graphql brace explosion).......................Passed
ruff format.....................................(no files to check) Skipped
ruff check......................................(no files to check) Skipped
kanban anchors collision-free...................................Passed
citations resolve (AGENTS.md rule 27 path::Symbol refs).........Passed
```

Exit **0** on the first run. The `source-layout` hook auto-fixes by default and a rewrite fails
the run, so a green first run is the evidence that it rewrote nothing — the link-definition
scaffold in both files survived this pass's edits intact. The two `ruff` hooks skip because no
`.py` file was touched.

`git status --short` after the run lists this cohort's four paths and no others of its own:
`docs/SPECS/spec-041-channels_router-0_0_14.md` modified; the rationale companion, this artifact
and the build plan untracked. Every other dirty path is the concurrent `spec-050` cycle's — the
baseline list plus `CONTRIBUTING.md`, `START.md`, `django_strawberry_framework/connection.py`,
`examples/fakeshop/README.md`, `examples/fakeshop/test_query/README.md` and
`tests/test_connection.py`, which grew after this cycle's baseline snapshot. None was edited,
staged, reverted or stashed.

### Status

`Status: built`. Worker 3's four Medium, six Low and one DRY finding are all closed; no finding
is rejected. One half of M1 — whether the Channels floor should move or the `6.1` classifier be
qualified — is escalated to the maintainer above with its rejected alternatives, for Worker 0's
deferred-work catalog. Nothing else is open.

---

## Review (Worker 3, pass 2)

Input: Worker 1's `## Build report — apply-changes pass`, the current spec (1832 lines) and
companion (985 lines). My own pass-1 section was not re-read as new input. Every figure below was
re-derived in this pass — occurrences, not matching lines, populations printed — against the
working tree and against HEAD obtained read-only (`git show HEAD:… > <scratch>/spec-head.md`; no
`stash` / `checkout --` / `restore` / `worktree`).

### Every finding walked, one at a time

All eleven are closed **in the text**, not only in the report. Each was checked at the site.

- **M1 — the floor's advertised-range claim.** Closed. All five homes rewritten and read in full:
  `## Slice checklist` dependency-gate row (L204-211), `### Error shapes` `channels`-absent bullet
  (L694-699), `### Decision 5` point 3 (L921-929), `## Edge cases and constraints` (L1370-1378),
  `## Definition of done` `channels[daphne]` item (L1674-1681). **The five now say the same thing**
  in four spellings of one claim: `4.3.2` is the declared floor and the first Channels release
  carrying `Framework :: Django :: 6.0`; `pyproject.toml` advertises `5.2` / `6.0` / **`6.1`**; no
  Channels release at this floor classifies 6.1; the floor's guarantee reaches 6.0 and stops. No
  home promises more than another. **Both source facts re-verified here, not taken from the
  report:** `pyproject.toml` L29-31 carries `Framework :: Django :: 5.2`, `6.0`, `6.1`, and
  `.venv/lib/python3.14/site-packages/channels-4.3.2.dist-info/METADATA` carries five
  `Framework :: Django` classifiers topping out at `6.0`. Post-sweep over the spec:
  `whole advertised Django range` = **0**, `through 6.0` = **0**. The floor-raise decision is
  escalated with four rejected alternatives, each carrying its reason — per Worker 0's ruling I
  checked that the escalation is recorded and did not re-raise the decision.
- **M2 — the stale test-row ordinals.** Closed. The `## Post-ship corrections` preamble and
  `### F10` both name the four retired rows by content and both state that the rewritten test plan
  reuses their ordinals. I checked the four descriptions against HEAD's own rows rather than
  against the finding text: HEAD row 2 = "`http` branch is `AuthMiddlewareStack`-wrapped" →
  "the `AuthMiddlewareStack`-wraps-HTTP row"; HEAD row 3 = "carries the fallback route **after**
  the GraphQL route (ordering asserted)" → "the HTTP fallback-route **ordering** row"; HEAD row 7 =
  "`HttpCommunicator` POST of a GraphQL query … returns 200 with the expected `data`" → "the
  `HttpCommunicator` GraphQL POST round trip"; HEAD row 8 = "the same POST to a non-GraphQL path …
  reaches the fallback app" → "the non-GraphQL-path fallback row". Four for four.
  **The surviving ordinals were audited, not accepted:** the companion still cites Test 14, 13, 4,
  1, 10, 18 and 16 (×2) — eight occurrences — and every one carries the same content in the
  rewritten spec (row 14 the two-sided restore, 13 the re-typed literal, 4 the wrapper chain, 1 the
  `application_mapping` parity assertion, 10 schema pass-through, 16 the request contract, 18 the
  authenticated session). None strands.
- **M3 — the card-id population.** Closed, and the figures are mine independently. Re-derived with
  `grep -oF` per file: `TODO-BETA-062-0.1.5` = **2** in the spec + **1** in the companion;
  `TODO-BETA-068-0.1.8` = **3** + **1**. HEAD's spec carried 3 and 4. **Renumberable sites in the
  pair = 5** (2 + 3): each companion occurrence sits inside the deferred-work paragraph that
  declares the id stale, the class the board's own census already excludes. That matches Worker 1's
  claim in every cell. Both files now state it — the companion at L920-931 with the derivation and
  where the two lost occurrences went, the artifact's earlier `### Deferred work` corrected in place
  with a visible pointer. **The decision not to restore the two ids is sound and is the one I would
  have made:** re-inflating a deliberately condensed rejected-alternative and a condensed
  revision-log entry to preserve a numeral the board is about to renumber trades a real cost for
  nothing.
- **M4 — the four counts.** Closed. All four corrected at their original sites with an explicit
  in-place marker naming what the sentence previously read and pointing at the derivation, which is
  the right shape: my quotation of the old text in pass 1 stays checkable against the correction.
  Re-derived independently — see the table below; every cell agrees.
- **L1 — "verified at the installed strawberry 0.316.0".** Closed. `grep -n 'installed strawberry'`
  over the spec returns **1** occurrence, in `## Current state` (L405), which that section's vintage
  framing licenses exactly as pass 1 said. Both standing-Decision occurrences now read "verified at
  the pinned `strawberry-graphql` floor, single-sited as `utils/imports.py::STRAWBERRY_FLOOR`"
  (Decision 5's `channels.db` claim at L891-893, Decision 7's export claim at L985-987). I checked
  the substitution is not a stronger claim than the evidence: both properties are precisely what the
  card's own Strawberry-floor gate exercised — importing `GraphQLWSConsumer` from
  `strawberry.channels` in an isolated floor venv necessarily executes the module-level `channels.db`
  import — so "at the floor" is warranted by the gate this card ran, not by a floor run this cycle
  (which is correctly scoped `none`).
- **L2 — the unresolvable citation.** Closed. Now
  `strawberry/channels/handlers/http_handler.py::GraphQLHTTPConsumer.get_context`, with the prose
  marking it "read in the checked-out upstream (not first-party)" and naming
  `::SyncGraphQLHTTPConsumer.get_context` as the identical twin. Both symbols resolve in the venv;
  the version literal was dropped rather than refreshed, which is right — the claim is about
  upstream's shape.
- **L3 — the test-plan renumbering.** Closed structurally, which is better than renumbering. A bold
  group lead-in (`**Channels-present — the session actor over the handshake:**`) now separates the
  two ordered-list blocks, so the `18.` item starts its own list and renders as 18. Verified it is a
  **bold lead-in and not a heading**: the spec's heading count is unchanged at 34 and its distinct
  in-page anchor targets are unchanged at 17 with 0 broken, so no anchor moved and nothing citing
  `## Test plan` shifted. No prose reference to "Test 18" moved (4 occurrences in the spec, still
  matching the list item they name).
- **L4 — the recorded reason for keeping `## Risks and open questions`.** Closed. The corrected
  reason (a decision's reader must see that a risk ledger exists and where it went — rule 1 of the
  rationale move) is the true one, and it is recorded in the new section rather than by rewriting a
  prior one. Re-measured: `grep -c 'risks-and-open-questions'` over the spec = **1**, the
  `[rationale-risks]` definition pointing into the companion; **0** in-page uses of the spec's own
  Risks anchor.
- **L5 — the slice-checklist consumer.** Closed. The `routers.py` row (L248-251) now reads "over
  whatever consumer is mounted — by default the package's revalidating subclass of
  `strawberry.channels`'s `GraphQLWSConsumer`", which matches
  `routers.py::_build_router_class_uncached` (`build_revalidating_consumer_class(GraphQLWSConsumer)`),
  mirrors Decision 6's `<consumer>` placeholder, and agrees with Decision 7.
- **L6 — one path spelling across the pair.** Closed, and the direction chosen is defensible on
  evidence rather than preference (the `spec-046` pair, this companion's own model, spells package
  files package-relative). Verified by resolution, not by eyeball: **46** `path::Symbol` occurrences
  across the pair over **21** distinct refs, **every one resolves** to a real definition, and the
  only repo-relative package path left in the companion is
  `[utils-imports]: ../../../django_strawberry_framework/utils/imports.py`, which must be a path
  from the file. `tests/…` stays repo-relative in both, as stated. A 16-site conversion is where a
  typo hides; there is none.
- **DRY — the third copy of the revalidation default.** Closed. The constructor block now reads
  `websocket_revalidation_window=_DEFAULT_REVALIDATION_WINDOW`, byte-matching
  `routers.py::_build_router_class_uncached`'s signature at HEAD, and the paragraph beneath names
  `consumers.py::_DEFAULT_REVALIDATION_WINDOW` as the one written value. `grep -c '=0\.0\b'` over
  the spec = **0**. The new `[consumers]`-backed symbol ref resolves. Keeping the
  `websocket_url_pattern` default is the disposition pass 1 allowed.

### Counts re-derived, against Worker 1's table

Every cell measured in this pass. All agree.

| Claim | Worker 1's figure | Mine | Agree |
| --- | --- | --- | --- |
| Decision-6 anchor, in-page uses at HEAD | 9 | 9 | yes |
| Decision-6 anchor, in-page uses now | 4 | 4 | yes |
| Decision-6 anchor, retired with enclosing text | 5 | 5 (9 − 4) | yes |
| Process-provenance labels at HEAD | 9 (`P1.1` ×6, `P1.2` ×1, `P1.4` ×2) | same | yes |
| Process-provenance labels now | 0 spec, 0 companion | 0 / 0 | yes |
| `TODO-BETA-062-0.1.5` | spec 2, companion 1 (HEAD spec 3) | same | yes |
| `TODO-BETA-068-0.1.8` | spec 3, companion 1 (HEAD spec 4) | same | yes |
| Renumberable sites in the pair | 5 | 5 | yes |
| Spec: link definitions / distinct labels used / occurrences | 82 / 82 / 291 | same | yes |
| Spec: in-page anchor uses / distinct targets / broken | 90 / 17 / 0 | same | yes |
| Companion: definitions / labels / occurrences | 26 / 26 / 62 | same | yes |
| Companion: in-page uses / distinct / broken | 21 / 9 / 0 | same | yes |
| `path::Symbol` occurrences / distinct across the pair | 46 / 21 | same | yes |
| Undefined uses, unused definitions (each file) | 0 / 0 | 0 / 0 | yes |

Both files carry all ten canonical group headers in order. Every definition target resolves **from
that file's own directory** — checked by resolving the path, not by disk existence, because a
same-named file one level up masks depth rot — and every cross-file anchor resolves in both
directions against the files as they now stand.

### No new drift introduced

This is the specific risk of an apply-changes pass over a document pair, so I measured it rather
than reasoning about it.

- **The spec's edit set is exactly the eleven fixes and nothing else.** Instrument: a second
  HEAD-vs-working-tree diff, differenced against pass 1's diff of the same two files, so only this
  pass's hunks survive. Eleven regions changed — the five M1 homes, the L5 consumer row, the L1
  sentences in Decisions 5 and 7, the DRY constructor block plus its paragraph, the L3 group
  lead-in, and one added `[consumers]` link definition. No collateral edit, no neighbouring
  sentence falsified, no heading or anchor moved.
- **No count was corrected in one file and left in the other.** The card-id figures appear in the
  companion's deferred-work paragraph and in the artifact's `### Deferred work`; both now read 2 and
  3, and both derive the same 5.
- **No link definition orphaned and none left undefined** in either file, after edits that added one
  definition and rewrote sixteen symbol paths (audit above: 0 / 0 in both).
- **No chronology or process provenance reintroduced.** Spec swept for `P1.`, `previously`,
  `Previously`, `as of `, `review round`, `Revision history`, `AMENDED`, `Amended`, `retract`,
  `High:`, `finding P` — **0 hits for all eleven**. The companion carries `previously` ×1,
  `Revision history` ×2 and `retract` ×1, which is correct: it is the licensed home for round
  vocabulary.
- **`#"substring"` citations still match.** The companion's three resolve against their named
  source — `routers.py` #'"http": django_application', `routers.py` #"_ROUTER_CLASS_LOCK" (2
  matching lines), `tests/test_routers.py` #"_STRAWBERRY_FLOOR_SUBSTRING" (2). No `path::Symbol`
  wraps across two lines in either file.
- **Five homes over everything else the revision touched**, not only M1: the L5 consumer row agrees
  with Decision 6, Decision 7 and `routers.py`; the DRY block agrees with the signature at HEAD and
  with `## Edge cases`; the L3 lead-in changed no row's content, so the test plan still agrees with
  `## Definition of done` and with the companion's change records; Decision 5's and Decision 7's L1
  rewrites left both Decisions' contracts untouched.

### Gates re-run, with their inputs stated

- `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-041-channels_router-0_0_14.md`
  → `OK: 30 terms - all have glossary entries and at least one spec link.` Input: the spec plus its
  untouched `-terms.csv` (31 lines = 30 rows + header; `git status` on it is clean). It compares
  term and anchor only — the `notes` prose is ungated, so this says nothing about the vocabulary
  this pass rewrote; the reading above is what stands in for it.
- `uv run python scripts/check_citations.py --check` →
  `OK: 981 citations resolve (814 in 442 .py files, 167 in KANBAN.md).` Input: first-party `.py`
  files and `KANBAN.md` — **blind to both files under review**. Its green means this pass broke no
  existing citation, nothing more; the 46-occurrence symbol audit above is the evidence about these
  two files.
- Hygiene: `git diff -- django_strawberry_framework/__init__.py` empty (public surface unchanged);
  0 `TODO(spec-041 …)` anchors in any `.py`; `git status --porcelain` shows this cohort's four paths
  and no `.py` file. No `pytest`, no `--cov*`, no write-mode `ruff`, nothing of the concurrent
  `spec-050` session edited, staged or reverted.

### High / Medium / Low (pass 2)

### High:

None.

### Medium:

None. All four from pass 1 are closed in the text.

### Low:

None. All six from pass 1 are closed in the text.

### DRY findings

None new. The pass-1 item is closed; the scope discipline that kept `spec-046`'s contract out of
`spec-041` survived the revision intact — I re-checked that none of the eleven edits smuggled a
second copy of a `spec-046` rule back in, and none did.

### Public-surface check

`git diff -- django_strawberry_framework/__init__.py` is empty — `__all__` and the re-export list
unchanged, consistent with the DoD's no-new-public-exports item.

### CHANGELOG sanity

Not applicable; slice did not modify CHANGELOG.md.

### Documentation / release sanity

Re-checked over the revised files. Version strings and card ids still match HEAD; `docs/GLOSSARY.md`
reads `shipped (0.0.14)`, `docs/TREE.md` carries the real `routers.py` and `tests/test_routers.py`
rows, `KANBAN.md` carries `DONE-041-0.0.14`. Every link introduced or moved by this pass points at
an existing file. No obsolete "planned" / "coming soon" wording reintroduced. No archival move owed.
No script-rendered doc regenerated, so the staging-docstring check does not apply.

### Temp test verification

None created in either pass. `docs/builder/temp-tests/041/` was not used: no executable code
changed, so every check is a document-versus-source read or a mechanical sweep, each recorded with
the command that produced it.

### What looks solid

- **Eleven findings, eleven closures, zero rejections, and each fix addresses the finding's cause
  rather than its symptom.** L3 is the clearest case: renumbering the prose would have made the
  labels agree while leaving the structural defect, and the group lead-in fixes the renderer instead.
  M3's refusal to restore two numerals, with the reason written down, is the same judgement in the
  other direction.
- **Worker 1 re-measured its own figures from the instrument up rather than copying mine**, and the
  in-place corrections are marked with what the sentence used to read. That is what makes the
  correction auditable a year from now, and it is the habit whose absence produced M4.
- **The escalation is complete in form**: the decision named, both source facts verified in the
  pass, four alternatives each with the reason it lost, and the boundary of this cohort's writable
  set stated. It is the shape `BUILD.md` asks for.
- **The reconciliation's substance survived the revision.** I re-confirmed the contracts the fixes
  touched against source: the constructor signature and its `_DEFAULT_REVALIDATION_WINDOW` default,
  the mounted consumer being the revalidating subclass, `CHANNELS_FLOOR` / `STRAWBERRY_FLOOR` still
  single-sited with `pyproject.toml` as the one other written copy, and the installed
  `channels 4.3.2` classifier ceiling.

### Notes for Worker 1 (spec reconciliation)

- **Escalated: the M1 claim has three live parallel sites this cycle cannot edit, and the
  escalation currently names only one of them.** `START.md`'s "partial claim fix = dominant residual
  defect" is the exact hazard: `spec-041`'s five homes are now correct while the same falsified
  claim stands elsewhere. Enumerated so the maintainer settles them in one pass rather than
  rediscovering them:
  - `docs/GLOSSARY.md` L628, the `DjangoGraphQLProtocolRouter` entry body — "(one floor covering the
    package's whole advertised Django range through 6.0)". Consumer-facing and **rendered from the
    glossary DB**, so the fix is a DB edit plus a regenerate, never a hand-edit. Out of cycle scope
    by maintainer instruction.
  - `docs/SPECS/spec-042-debug_toolbar-0_0_14.md` L448 and L1063 — the same sentence shape for
    `django-debug-toolbar>=7.0.0`, a different card's spec.
  - `pyproject.toml`'s comment ending "the `Framework :: Django :: 6.0` classifier the package
    itself advertises", which Worker 1 already recorded — it belongs to the `django-debug-toolbar`
    row, so it and the `spec-042` pair are one question.
  All four sites turn on the single decision already escalated (does the advertised `6.1` classifier
  move the soft-dependency floors, or does the whole-range wording go?), so they should ride the
  same answer. For Worker 0's `### Deferred work catalog`.
- **Nothing else is open.** No finding was rejected, none is deferred, and no new one was raised.

### Review outcome

`review-accepted` — every High, Medium and Low finding from pass 1 is closed in the text and
verified at the site; the counts re-derive in every cell; the revision introduced no drift in
either file; and the one contract-level question is escalated with its rejected alternatives, with
its three unedited parallel sites enumerated above for Worker 1's final verification.

---

## Final verification (Worker 1)

Input: the whole artifact including both Worker 3 reviews, the working-tree diff of the three
cycle files, the spec and companion as they now stand, and source at HEAD. HEAD read read-only via
`git show HEAD:… > <scratch>/spec-head.md` outside the repo; no `stash` / `checkout --` /
`restore` / `worktree`. Every figure below was measured in this pass.

### Summary

The slice shipped the `spec-041` rationale companion and reconciled the spec to the contract that
exists at HEAD. Worker 3's eleven findings are closed and re-verified at the site here. The spec
carries no chronology, no amendment banner and no revision history; the companion carries all of
it keyed by decision heading and anchor. One contract-level question — whether the Channels floor
moves or the `Framework :: Django :: 6.1` classifier is qualified — is escalated to the maintainer
with its rejected alternatives and its three unedited parallel sites, and is catalogued in
`docs/builder/bld-041-final.md`.

### Dispatched findings checklist audit (F1-F12)

Every box in `### Dispatched findings checklist` is `- [x]`. Each was audited against the diff
rather than against the build report; none is over-ticked, none is under-ticked, and no box
remains `- [ ]`, so no deferral reason is owed. Instrument for each: the claim's shortest
distinctive token counted over HEAD's spec and the current spec.

| Finding | Probe | HEAD | Now | Verdict |
| --- | --- | --- | --- | --- |
| F1 | `url_pattern="^graphql"` / `django_application=None` | 6 / 6 | **1 / 1** | landed |
| F2 | "HTTP fallback runs inside" `AuthMiddlewareStack` | 0 hits of the old paragraph; `"http"` value "assigned verbatim" | 2 | landed |
| F3 | `Host validator` | 0 | **6** | landed |
| F4 | `GraphQLHTTPConsumer` | 20 | **2** | landed |
| F5 | `strawberry-graphql==0.262.0` in the DoD | 2 | **0** | landed |
| F6 | `CHANNELS_FLOOR` | 0 | **9** | landed |
| F7 | `_ROUTER_CLASS`, first construction serialized | 0 | **1** | landed |
| F8 | `consumer.scope` / both scope shapes | present, single-shape | both shapes + contained read | landed |
| F9 | `spec-040` attribution | 10 | **14** | landed |
| F10 | test-plan rows rewritten | HTTP-branch rows live | rewritten, ordinals reused | landed |
| F11 | multipart bullet retired to `views.py::DjangoGraphQLView` | Channels-HTTP-consumer framing | `MultiPartParser` under the package view | landed |
| F12 | checklist / implementation-plan rows | inherit F1-F4 drift | restated | landed |

**The three F1/F4 survivors are correct and were read, not counted.** All three describe someone
else's code, which is exactly what the reconciliation should have left standing:
`## Borrowing posture` quotes **upstream's** `AuthGraphQLProtocolTypeRouter` signature
`(schema, django_application=None, url_pattern="^graphql")` — verified character-for-character
against `~/projects/strawberry-django-main/strawberry_django/routers.py`'s `__init__`;
`## Current state` names `GraphQLHTTPConsumer` among what `strawberry.channels` ships, and
`## Out of scope` names `SyncGraphQLHTTPConsumer` as a sync variant the card deliberately does not
expose — both verified against `strawberry/channels/__init__.py`'s `__all__`, which lists
`ChannelsConsumer`, `ChannelsRequest`, `GraphQLHTTPConsumer`, `GraphQLProtocolTypeRouter`,
`GraphQLWSConsumer`, `SyncGraphQLHTTPConsumer`. A sweep that counted these as residual drift would
have deleted three true sentences.

### Five homes per contract, across the whole spec

Run over the spec as a whole, not only the contracts the revision touched — Decision /
`## Slice checklist` / `## Edge cases and constraints` / `## Test plan` / `## Definition of done`,
all four non-Decision homes read end to end in this pass. **No two homes disagree.** Where a
contract is absent from a home, the absence is silence rather than a contrary claim.

| Contract | Decision | Slice checklist | Edge cases | Test plan | DoD |
| --- | --- | --- | --- | --- | --- |
| `"http"` is `django_application`, verbatim | 6 | yes | yes ("No Channels middleware runs on HTTP at all") | rows 2, 8 | yes |
| `django_application` required, others keyword-only | 6 | yes | — | row 3 | yes |
| `websocket_url_pattern`, exact at both ends | 6 | yes | yes | row 5 | yes |
| Host validator outermost | 6 | yes | — (deliberate: `spec-046` D19 owns its edge cases) | row 4 | yes |
| Only `GraphQLWSConsumer` imported | 7 | yes | yes | rows 3, 7 | yes |
| Floors interpolated, single-sited | 5 | yes | yes | rows 13, 17 | yes |
| First construction serialized | 5 | yes | — | row 6 | — (deliberate) |
| Two scope shapes, contained read | 11 | yes | — | row 16 | yes |
| Session-mutating auth is `spec-040`'s | 2, 11 | — | — | — | yes |
| No package-root re-export | 3 | yes | yes | rows 11, 12 | yes |

Two deliberate asymmetries, both re-checked rather than accepted from the build report:

- **The construction lock is absent from the DoD on purpose**, and the DoD makes no contrary
  claim — verified by reading every `lock` and `serializ` hit in the section, which are `uv.lock`
  and "DRF serializer overrides". The reason recorded in `### Spec changes made (Worker 1 only)`
  stands: the DoD is this card's completion claim and the lock is later hardening the card did not
  ship, so adding it would make the spec claim credit for work it did not do.
- **The Host boundary has no `## Edge cases` bullet of its own** because `spec-046` Decision 19
  owns those edge cases; the spec states the shape and points. Both were flagged by Worker 3 as
  not-to-be-re-raised, and I reach the same answer independently.

### Structural claim 1 — the spec states no contract the code does not have

Checked against source bodies, not citations. Each property below was read in the named file at
HEAD in this pass:

- `routers.py` #'"http": django_application' — the `"http"` value is the parameter itself.
- The `"websocket"` value is
  `DjangoWebSocketHostValidator(AllowedHostsOriginValidator(AuthMiddlewareStack(URLRouter([re_path(…)]))))`
  in that nesting order.
- `routers.py` imports `GraphQLWSConsumer` from `strawberry.channels` and no HTTP consumer; the
  default mount is `build_revalidating_consumer_class(GraphQLWSConsumer)`, which is what the
  checklist row now says.
- `routers.py` #"DjangoGraphQLProtocolRouter",)" — the module's `__all__` — with the scoped
  `# noqa: F822 - PEP 562 lazy export`; `django_strawberry_framework/__init__.py` carries **0**
  mentions of `routers` or the router symbol, so the no-root-re-export contract holds.
- `websocket_url_pattern: str = r"^graphql/?$"` — the two pattern literals in the spec match it.
- `utils/imports.py::CHANNELS_FLOOR` = `"4.3.2"`, `::STRAWBERRY_FLOOR` = `"0.316.0"`, and all
  three hint strings f-string-interpolate them.
- `routers.py::_build_router_class` double-checks `_ROUTER_CLASS` around
  `routers.py` #"_ROUTER_CLASS_LOCK" before delegating to `_build_router_class_uncached`.
- `utils/imports.py::require_optional_module(module_name, *, install_hint)` — no `feature_label`,
  as the checklist row and Helper-reuse D-P1 both state.
- `utils/permissions.py::_channels_scope` resolves `consumer.scope` first, then a bare `scope`,
  each behind a contained read.
- `auth/sessions.py::login_supported` returns `transport is not Transport.CHANNELS_WEBSOCKET`
  (engine-independent) and `::logout_supported` returns `not uses_signed_cookie_sessions()` for a
  WebSocket — precisely the narrow form the spec's `## Non-goals` and Decision 11 state.

### Structural claim 2 — every named deliverable has a live symbol, a live test, or a stated removal

Resolved by AST lookup rather than by grep, over the four modules the spec's `## Slice checklist`,
`## Implementation plan`, `## Test plan` and `## Definition of done` name:

- `routers.py` — 9 of 9 named symbols present (`DjangoGraphQLProtocolRouter`, `require_channels`,
  `_build_router_class`, `_build_router_class_uncached`, `_ROUTER_CLASS`, `_ROUTER_CLASS_LOCK`,
  `_CHANNELS_INSTALL_HINT`, `__getattr__`, `__all__`).
- `utils/imports.py` — 3 of 3 (`require_optional_module`, `CHANNELS_FLOOR`, `STRAWBERRY_FLOOR`).
- `utils/permissions.py` — 4 of 4 (`ChannelsRequestAdapter`, `_channels_scope`,
  `_channels_request_adapter`, `request_from_info`).
- `consumers.py` — 3 of 3 (`_DEFAULT_REVALIDATION_WINDOW`, `DjangoWebSocketHostValidator`,
  `build_revalidating_consumer_class`).
- `tests/test_routers.py` defines **117** `test_` functions plus the three helpers the spec names
  by name (`unwrap_origin_validator`, `unwrap_auth_stack`, `_ws_graphql_data`); every
  `tests/test_routers.py::…` reference in the pair resolves.
  `tests/base/test_init.py::test_version` resolves in its own file.
- The one **removal** the spec asserts rather than a deliverable — the HTTP GraphQL branch — is
  stated as removed by the card that removed it (`spec-046`) in every home that mentions it, and
  is pinned positively by
  `tests/test_routers.py::test_graphql_http_consumer_left_the_router_module_entirely`.

### DRY check against prior accepted work

This cycle has one slice, so there is no prior slice to duplicate against. Re-checked the one
standing risk instead — a second copy of a `spec-046` contract inside `spec-041` — by reading
`## Out of scope`, `## Borrowing posture`, Decision 6 and the `## Edge cases` multipart and
pattern bullets: each states the shape, names `spec-046` and its decision number, and stops.
No second copy of the Host-validator rules, the body/encoding bounds, the injection seam's
rejection shapes or the revalidation semantics. The pass-1 DRY finding (the third written copy of
`0.0`) is closed: `grep -o 'revalidation_window=0\.0'` over the spec = **0**.

### Focused test run

None owed and none run. This slice changed no executable code, so there is no focused scope whose
result would be attributable to it, and `AGENTS.md` #"No pytest after edits" forbids a run absent a
maintainer request. The build plan's `## Final gate scope` records the same reasoning for the
cycle gate.

### Relocation / promotion claims

One, and I re-proved it rather than reading Worker 3's acceptance as discharge: the rationale move
is a **move**, not a copy. Instrument: for each of the six item classes the build report lists as
moved, grep the spec for its distinctive text and confirm 0, then grep the companion and confirm
it is there. The spec returns **0** for `Revision history`, `previously`, `Previously`, `as of `,
`P1.`, `review round`; the companion carries `Revision history` ×2, `previously` ×1 and `retract`
×1, which is correct — it is the licensed home.

### Failability and fail-open checks

- **Failability records.** None owed: this cycle added no boundary, guard, gate or rejection path,
  because it wrote no `.py` file. The artifact's `### Failability proofs` says exactly that, so the
  obligation is discharged by a recorded "none", not by a sampling gap.
- **Fail-open shapes.** None possible to introduce: no executable code changed.
  `git diff -- django_strawberry_framework/` is empty of this cycle's authorship; every dirty `.py`
  path belongs to the concurrent `spec-050` session.

### Spec changes made (Worker 1 only)

No spec edit was owed by this verification pass. The spec's status/header lines were re-read at
the start of this spawn per `worker-1.md` `## Spec status-line re-verification` and still describe
the build's state: `Status: **COMPLETE** (card `DONE-041-0.0.14`) — both slices built, the card
wrap landed, and the `0.0.14` release rode the joint cut`, with the sentence pointing later
readers at the companion for what changed. No predecessor doc this build deleted is referenced.
Every `- [ ]` in the spec's own `## Slice checklist`, helper-reuse ledger and `## Definition of
done` stays unticked, per this repo's shipped-card convention where the `Status:` line is the
source of truth.

### Final status

`final-accepted`. Eleven findings closed and re-verified at the site, twelve checklist boxes
audited against the diff with none over- or under-ticked, the five-homes cross-check clean across
the whole spec, and both structural claims confirmed against source. The one open item is a
maintainer decision, escalated with its alternatives and catalogued in the final gate artifact.
