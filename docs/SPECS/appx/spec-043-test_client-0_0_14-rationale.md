# Rationale: spec-043 — Test client helper (deliberation, rejected alternatives, change record)

Deliberative companion to [`spec-043-test_client-0_0_14.md`][spec-043]. The spec is the contract
and states only what is currently true; everything that explains **how it got there** lives here:
the alternatives each decision rejected and why each lost, the derivations that do not change how
a decision is implemented, every change a decision has undergone with the round that caused it,
and every claim a decision once made and may no longer make.

Created by the [`docs/builder/BUILD.md`][build] `## Spec rationale extraction` pass. **The move
happened long after the release, not before the build.** Card `DONE-043-0.0.14` shipped with no
companion at all — the spec carried its deliberative layer inline, including a three-entry
`Revision history` block that opened "kept inline so the spec is self-contained" and whose last
entry instructed the reader to reinterpret earlier text the spec still carried. Seven post-ship
commits then corrected and extended what the card shipped while the spec's prose stayed at the
ship-time contract. This pass supplies the companion and reconciles the spec in one custodian
judgement, because what a decision now says and what it used to say are decided together. Text
marked *Moved* below was cut out of the spec, not copied: it exists here and nowhere else.

## How to read this file

- **One entry per spec decision**, named by the decision's own heading and linked to its anchor,
  so a citation such as "Decision 9's rejected alternatives" resolves to exactly one place. An
  entry that named no decision could not be looked up and would be worthless however well argued.
  The three spec sections that carry deliberation without being numbered decisions —
  `## Borrowing posture`, `## Risks and open questions`, and the prediction clauses of
  `## Current state` — get their own entries under `## Non-decision entries`, keyed by section
  heading and anchor the same way.
- **Who reads it.** Worker 3 reads it during review; Worker 1 owns it; Worker 2 never reads it. A
  reader looking for what the package *does* wants the spec, not this file.
- **No timeline.** The spec's three-entry `Revision history` block moved here and was
  **decomposed into per-decision `Change record` blocks**. A reader asking "what did Decision 11
  used to say?" finds the answer under
  [Decision 11](#decision-11--test-strategy-the-live-switchover-is-the-primary-coverage), not by
  reading a chronology and applying it. `## Revision vocabulary` below names the three revisions
  once so each block can cite one without restating it — and because the names have inbound
  citers the move would otherwise strand: the spec's three sentences citing "spec-042 Revision 8"
  by name for the shipped-spec closeout convention travelled with the block and now live in this
  file, which is where [`spec-042`][spec-042]'s own companion expects to find that population,
  and [`spec-031`][spec-031]'s companion cites "spec-043 Rev 3" for the same convention.
- **Three kinds of change are recorded, and they are not the same kind.** A *pre-implementation
  revision* changed a decision before any code existed (Revision 1 is the only one of that kind
  here). A *closeout-consistency revision* realigned the shipped spec to the shipped card
  (Revision 2). A *post-ship correction* is the shipped code having moved while the spec's prose
  did not. `## Post-ship corrections` carries the third kind for the whole spec, keyed by the
  finding numbers the post-ship reconciliation cycle's build plan assigned them, and each decision
  entry cross-links the ones that touch it.
- **Where a change record and the spec disagree, the spec is the contract** and the change record
  is why it moved. A claim the decision may no longer make is named in the record rather than
  deleted silently.
- **What deliberately stayed in the spec even though it reads like deliberation.** Decision 9's
  account of why the `content_type` argument is *omitted* rather than passed (and its instruction
  not to "fix" upstream's inert `format="multipart"` kwarg back in), the `operationName`
  omitted-never-`null` reasoning, the explicit-`raise`-not-bare-`assert` reasoning that makes
  every guard survive `python -O`, Decision 7's "`self.path` is never mutated" non-persistence
  reasoning, and Decision 11's live-first placement rule are all instructions to a builder rather
  than records of thinking: a builder who never reads them passes the constant explicitly, sends
  `operationName: null`, writes a bare `assert`, mutates `self.path` per call, or restates a live
  behaviour as a package-tier stand-in. When it was unclear whether a sentence was deliberation or
  instruction, it stayed.

## Revision vocabulary

The spec's `Revision history` block named three revisions. They were not three of the same thing,
and the distinction is what makes the per-decision records readable:

- **Revision 1** — the initial draft, authored from the `TODO-ALPHA-043-0.0.14` card body via the
  [`docs/SPECS/NEXT.md`][next] flow (2026-07-08). It pinned Decisions 1–12 and recorded one
  card-vs-source conflict in `## Risks and open questions` rather than reconciling it silently
  (the card's `.mutate()` claim — see the
  [Decision 6 entry](#decision-6--query-returns-the-typed-response)).
  Nothing in it recorded what the build discovered, which is why moving it costs the spec nothing
  a builder needed.
- **Revision 2** — the closeout-consistency pass (2026-07-09), absorbing a maintainer follow-up
  review. Its three items were all *release-evidence* rather than contract: the opener and
  `Status:` line still said "Planned" / "PLANNED — no slice built yet" for a card that was Done
  (realigned to the shipped-spec convention, past-tense "Built for" plus the `DONE-` id); the
  kanban `TrackedPath` row for `testing/client.py` still carried `is_current=False`, so the
  DB-backed board exports rendered the live file `historical` (fixed at the DB source and both
  exports regenerated); and the three `unittest`-family live cases called
  `reload_all_project_schemas()` inside each `setUp()` ahead of `seed_data(1)`, duplicating the
  file's autouse fixture (the manual reloads were removed so `seed_data(1)` is the first
  domain-setup line after `super().setUp()`, per the [`AGENTS.md`][agents] seed-helper rule).
  The review's implicit expectation that the *unticked checklist* was itself the defect was **not
  adopted** — see [F8](#f8--the-unticked-checkboxes-are-the-convention-not-a-defect).
- **Revision 3** — the post-ship adversarial review (2026-07-10, shipped as commit `dbe8e77e`).
  Four findings, all addressed at the source; each is recorded under the decision it corrected —
  F1 (async multipart) under
  [Decision 11](#decision-11--test-strategy-the-live-switchover-is-the-primary-coverage), F2
  (test-placement lag) under the same entry, F3 (`operation_name=""`) and F4 (reserved envelope
  keys) under
  [Decision 9](#decision-9--multipart-uploads-files-maps-variable-paths-to-file-parts). Its F2
  entry was the acute case for the move: it instructed the reader to reinterpret four named
  sections to learn what was currently true, which is the exact shape
  [`docs/builder/BUILD.md`][build] forbids ("a reader must never reconstruct what is currently
  true by applying a chronology to it").

Revisions 1 and 2 both happened **before** the post-ship commits that this reconciliation cycle
folded into the contract.

## Post-ship corrections

Findings from the spec-custody cohort of the spec-043 post-ship reconciliation cycle, each read
against source at HEAD before being written down, and each recorded as *what the spec used to
claim* / *what HEAD does* / *which change caused it*. All are spec-only: no code change was owed
by that pass, and [F5](#f5--decision-9-and-error-shapes-described-a-guard-the-code-does-not-have)
is the one place the spec text — not the code — was the defect.

The spec's own `## Current state` section is exempt from part of this by the vintage rule in
[`docs/builder/BUILD.md`][build] `### `## Current state`: observations stand, predictions do not`:
a bullet that dates an observation of the pre-build repo stays even when later work falsified it.
Where one of its bullets carried a *prediction* as well, the prediction was rewritten and the
observation kept — graded clause by clause, never bullet by bullet
([Current state entry](#current-state--the-prediction-clauses)).

### F1 — the `-rationale.md` companion did not exist

*Claimed:* nothing; the spec simply had no companion, and its `Revision history` block opened
"kept inline so the spec is self-contained".
*HEAD:* `docs/SPECS/appx/` carried only `spec-043-test_client-0_0_14-terms.csv`, where every
shipped spec from 001 through 048 except 043 and 049 carries both files.
*Cause:* the card shipped before [`docs/builder/BUILD.md`][build] `## Spec rationale extraction`
made the move pre-flight step 7. This file is the discharge.

### F2 — the spec narrated its own history in three inline revisions

*Claimed:* three inline revisions, ≈130 lines, the last of them a supersession note.
*HEAD:* the spec carries a one-line pointer to this file and no chronology at all.
*Cause:* as F1. Revision 3's F2 entry was the acute case (see `## Revision vocabulary`).

### F3 — six post-ship behaviour families were absent from the spec

*Claimed:* the ship-time contract. Grepping the spec for `_finish_response`, `_safe_arg_repr`,
`_assert_file_placeholders`, `tuple`, `empty dotted`, and `unreadable` returned **0 hits** each.
*HEAD:* seven commits touched `django_strawberry_framework/testing/client.py` after the card's own
two (`2db331cf` feat, `653a3841` review fixes + Slice 2/3 wrap). Two were comment-only
(`5a74d803`, `8bab7ea8`), one was Revision 3's own landing (`dbe8e77e`), and the remaining four
carry six behaviour families:

1. **`TestClient._finish_response` extracted** (`8bac47be`, the cross-family DRY review's item
   B4). The decode → `Response` construction → `assert_no_errors` raise tail, previously
   duplicated verbatim between `TestClient.query` and `AsyncTestClient.query`, is now one
   un-colored helper both colors call. Folded into
   [Decision 5](#decision-5--subclass-strawberrys-basegraphqltestclient).
2. **A falsy consumer-supplied client is honored** (`f7fbead4`). Both constructors moved from
   `client or Client()` to `client if client is not None else Client()`. Folded into
   [Decision 5](#decision-5--subclass-strawberrys-basegraphqltestclient).
3. **Diagnostics render through `_safe_arg_repr`** (`f7fbead4`), a new cross-module dependency on
   `django_strawberry_framework/exceptions.py`. Folded into
   [Decision 9](#decision-9--multipart-uploads-files-maps-variable-paths-to-file-parts) and the
   spec's `## Helper-reuse obligations (DRY)` list as **D5**.
4. **Tuple variables are walked as arrays** (`a8f31a2d`): `isinstance(current, (list, tuple))`,
   matching what `json.dumps` actually serializes as a JSON array.
5. **The empty-dotted-segment guard and the unreadable-`__len__` guard** (`a8f31a2d`).
6. **Canonical object-path index validation** (`b4d0c8ae`): a guarded `int()` conversion plus
   `index >= 0 and str(index) == segment`, because digit-like Unicode and very long decimal
   strings do not share `int()`'s acceptance domain and `isdigit()` accepts superscripts `int()`
   rejects.

Families 4–6 are folded into
[Decision 9](#decision-9--multipart-uploads-files-maps-variable-paths-to-file-parts).
*Cause:* post-ship hardening commits made for later work, none of which re-opened this spec.

### F4 — the module-level accessor's `__test__ = False` was absent from the spec

*Claimed:* the spec named the `__test__ = False` guard in nine places, all of them on the *class*
(`TestClient` / `AsyncTestClient`).
*HEAD:* `django_strawberry_framework/conf.py` #"testing_endpoint_setting.__test__ = False" carries
the same idiom on the **module-level accessor**, whose name also matches pytest's default `test*`
function pattern and which returns a `str` — collected, it fails the run under
`filterwarnings = error` via `PytestReturnNotNoneWarning`.
*Cause:* commit `a62d6dca` added it post-ship. Folded into
[Decision 7](#decision-7--endpoint-resolution-the-settings-key-is-testing_endpoint) and the spec's
`## Edge cases and constraints`.

### F5 — Decision 9 and Error shapes described a guard the code does not have

**This is the one finding where the spec text, not the code, was the defect.** Both disagreements
were verified against
`django_strawberry_framework/testing/client.py::TestClient._build_body` and
`::TestClient._assert_file_placeholders`.

- *Claimed:* `## Error shapes` said the guard is
  `if files is not None and variables is None: raise AssertionError(...)`.
  *HEAD:* the multipart entry condition is `if not files: return body` — **truthiness** — and
  the guard beside it reads the built envelope, `if "variables" not in body:` (respelled from
  `if not variables:` by the correction recorded under
  [Decision 9](#decision-9--multipart-uploads-files-maps-variable-paths-to-file-parts); the
  verdicts are identical either way, because the emission that writes the member is itself
  truthiness). The observable
  difference from the spec's claimed spelling is real: `files={}` posts JSON (the spec's spelling
  would build a multipart envelope
  with an empty map), and `variables={}` raises (the spec's spelling would not). The shipped
  truthiness is the correct behaviour, is documented in the code's own comments, and is pinned by
  `tests/testing/test_client.py::test_empty_files_dict_is_a_plain_json_post`.
- *Claimed:* Decision 9 said `_build_body` "enforces this with an explicit `raise AssertionError`
  guard" — singular, describing only the `variables is None` case.
  *HEAD:* the shipped contract is a **recursive path walker**,
  `TestClient._assert_file_placeholders`, with five distinct rejection branches (empty segment,
  invalid array index, unreadable array length, non-descendable value, non-`None` value at the
  resolved path) plus the reserved-envelope-key guard in `_build_body`. The walker existed at ship
  time; Decision 9 never described it, and Revision 3 only added the reserved-key guard beside it.

*Cause:* the spec described an intended guard shape rather than the built one, and no later pass
re-read the two against each other. **The claim these sections may no longer make:** that the
multipart entry condition is `files is not None`, or that one guard covers the placeholder
contract.

### F6 — the Strawberry floor the spec named is stale

*Claimed:* `strawberry-graphql==0.262.0` as "the package's pinned floor", in seven places.
*HEAD:* `pyproject.toml` pins `strawberry-graphql>=0.316.0`, and
[`docs/builder/BUILD.md`][build] `## Floor verification` — declared there as "the single canonical
statement of the floor versions" — records `0.316.0` as the policy point a floor run installs.
*Cause:* the floor moved after the card shipped, and the spec had restated a number instead of
naming its source. The spec now names the source in every one of those places, per
[`docs/builder/BUILD.md`][build]'s own rule that "the role files name this section rather than
restate the numbers". **No floor re-run was owed:** the floor-presence question the Slice-1 gate
covers (`strawberry.test.BaseGraphQLTestClient` importable) is settled by the module importing
successfully at HEAD.

### F7 — post-ship test-tier additions were absent from the spec's Test plan

*Claimed:* a `## Test plan` numbering scenarios 1–14 whose coverage paragraph asserts every branch
has a named owner.
*HEAD:* five commits added package-tier rows and three added live-tier rows after the card closed,
so the branches [F3](#f3--six-post-ship-behaviour-families-were-absent-from-the-spec) introduced
have owners in the suite but had **no scenario number** — which made the every-branch-has-an-owner
claim false as written even though it was true of the suite.
*Cause:* as F3. The spec grew scenario 15 (the hardened placeholder walker and the transport
selection) so the claim is true again.

### F8 — the unticked checkboxes are the convention, not a defect

*Claimed:* nothing; this is recorded so it is not re-raised. Per the shipped-spec convention the
Slice and Definition-of-done checkboxes stay `- [ ]` and the `Status:` line is the completion
source of truth. The spec settled this once already in Revision 2, where a review's implicit
expectation that the unticked checklist was itself the defect was **not adopted** — every shipped
spec leaves its boxes unticked, matching the point spec-042 settled in its own Revision 8 and
spec-040 before it.
*HEAD:* the `Status:` line reads COMPLETE and matches the tree. No cohort ticked a box.

## Decision entries

### Decision 1 — Spec filename and canonical naming

Spec: [Decision 1][d1].

**Alternatives rejected.** *Moved from the spec.*

- **`spec-043-test_client_helper-0_0_14.md`.** The `_helper` suffix adds length without
  disambiguation — no other card touches the test-client surface.
- **`spec-043-testing_client-0_0_14.md`.** The slug names the card's subject (the test client),
  not the module path; the established slug style is subject-first (`debug_toolbar`,
  `channels_router`, `auth_mutations`).

**Change record — Revision 1.** The stem was pinned at authoring time via the
[`docs/SPECS/NEXT.md`][next] flow and has not moved since.

### Decision 2 — Card-scope boundary

Spec: [Decision 2][d2].

**Alternatives rejected.** *Moved from the spec.*

- **Adopt the Channels session-auth verification here** (the other arm of the glossary's
  disjunction). Wrong vehicle (communicators, not test clients), wrong dependency posture (soft
  `channels` in a zero-new-dependency card), and an M card would swell past its size for a
  deliverable the router card already scoped out of itself.
- **Adopt the toolbar async smoke.** It would make this card's test suite import a soft dependency
  (`django-debug-toolbar`) and reproduce spec-042's settings fixture for one assertion a follow-on
  can add by reusing 042's now-landed fixture and machinery.

**Justification, moved because it argues for the boundary rather than stating it.** The card's DoD
names exactly the in-scope set; the two adjacent handoffs are disjunctions this spec must resolve
but not absorb — [`START.md`][start]'s "resist scope creep" rule applied to a card that two
sibling specs point at.

### Decision 3 — The symbols are upstream's own names

Spec: [Decision 3][d3].

**Alternatives rejected.** *Moved from the spec.*

- **`DjangoTestClient` / package-prefixed names.** The package's `Django*` prefix marks
  schema-side public API (`DjangoType`, `DjangoConnectionField`); test utilities are namespaced by
  their module path, and a renamed symbol breaks the one-line migration for zero gain.
- **`GraphQLTransactionTestCase` shortened to `GraphQLTxTestCase`.** Graphene migrants grep for
  the upstream name; abbreviation saves nothing.
- **A single `GraphQLTestCase` with a class flag for transaction behavior.** Django's own
  `TestCase` / `TransactionTestCase` are distinct classes with distinct semantics; flattening them
  into a flag would be a package-invented indirection over a Django concept.

**Derivation, moved because it does not change how the classes are named.** The decision reuses
[`spec-042`][spec-042] Decision 3's argument — a symbol whose public identity is "the thing you
import from the package" needs no invented name — and the concrete pair keeps graphene's exact
`TestCase` / `TransactionTestCase` split because that split is Django's own testing vocabulary
rather than a graphene-ism.

**Change record — the `Django*`-prefix rule became normative when its alternative left.** The
`DjangoTestClient` rejection above was the only place the spec linked the two schema-side glossary
terms it contrasts against, so moving it here stranded both — `check_spec_glossary.py` fails on a
[`docs/SPECS/appx/spec-043-test_client-0_0_14-terms.csv`][terms] row with no surviving spec link,
and it did. The rule those terms illustrate is a naming contract rather than deliberation, so the
spec now states it directly (the prefix marks schema-side public API; test utilities are
namespaced by import path, so a `DjangoTestClient` spelling is out of contract) and this entry
keeps only why the alternative lost. **The general lesson:** a rejected alternative can be the sole
carrier of a gated cross-reference, and the gate is the instrument that says so — run it after the
move, never before.

### Decision 4 — Module, export, and test locations

Spec: [Decision 4][d4].

**Alternatives rejected.** *Moved from the spec.*

- **Submodule-only (`from django_strawberry_framework.testing.client import TestClient`), the
  `relay` posture.** It contradicts the subpackage docstring's standing promise, and the
  light-import rationale that justified the `relay` exception does not apply: the client module
  imports `django.test` and `strawberry.test`, both already imported by any process running Django
  tests, which is the only process that imports `testing` at all.
- **Package-root export.** Pollutes the schema-building `__all__` with test-only names; neither
  upstream does it.
- **A new top-level `test/` subpackage mirroring upstream's path exactly.** The `testing/`
  subpackage exists, is documented, and already carries the "Future exports" plan; two
  test-utility subpackages is a migration aid for nobody.

**Derivation, moved because it does not change where the module lands.** The subpackage is named
`testing/`, not `test/`, because a top-level `test/` would shadow the Python stdlib `test`
package — the reason recorded for the package's own earlier `test/` → `testing/` rename. The three
postures the subpackage now holds at once (root-re-exported `safe_wrap_connection_method`,
deliberately submodule-only `relay`, and this card's root-re-exported family) are a locality
contrast worth reading before proposing a fourth.

### Decision 5 — Subclass Strawberry's `BaseGraphQLTestClient`

Spec: [Decision 5][d5].

**Alternatives rejected.** *Moved from the spec.*

- **Roll a package-owned base.** Rejected on the decision's three grounds; the only surface it
  would free is already free in the subclass.
- **Wrap (compose) instead of subclass.** Composition would re-declare `query()`'s full signature
  just to delegate, and the base is an ABC designed for exactly this subclass shape.
- **Subclass but keep the base's `_build_multipart_file_map` (no owned builder).** The base's
  folder heuristic returns an empty map for fakeshop's nested input-object uploads, so keeping it
  would force the existing upload suites to stay on raw `client.post(...)` and shrink the
  consumer-facing contract this card is meant to ship.
- **Fork/patch the base's map builder into the package.** It forks engine-internal code and
  inherits its folder-key guessing; the public path-keyed `files=` contract lets the package's own
  builder be ~15 lines and independent of the base's heuristic.

**The card's counterargument, and the answer — moved because it argues for the decision rather
than stating it.** The card observed that "the package's DRF-first stance argues for considering
the from-scratch alternative". The answer is the coupling actually at stake: the base pins
`_decode` and `Response` field names, both of which the package **wants** pinned to the engine
(the wire format is the engine's); the body build the package owns outright, and the
package-shaped surface (endpoint resolution, `operation_name`, the raw-response field, the
unittest family) all lands in the subclass anyway. DRF-first governs the *consumer configuration
surface* (`class Meta`, settings keys) — which this card does shape itself — not the reuse of the
engine `_decode` / `Response` seams the package's own read/write paths already treat as the wire
contract.

**Change record — the shared response tail was factored out
([F3](#f3--six-post-ship-behaviour-families-were-absent-from-the-spec) family 1).** The decision
argued at length that the package owns `query()` in **both colors**, and the code still does. What
it never recorded is that commit `8bac47be` later lifted the *un-colored tail* of both overrides —
the `_decode` → `Response` construction → `assert_no_errors` raise — into one
`TestClient._finish_response` helper both colors call. **This does not weaken the decision:** the
factoring sits BELOW the not-calling-`super().query()` call, not around it, and the async color
still owns its own `await self.request(...)`. The spec now states the helper as part of the
decided contract; the DRY review that produced it is recorded here.

**Change record — a falsy consumer-supplied client is honored
([F3](#f3--six-post-ship-behaviour-families-were-absent-from-the-spec) family 2).** Both
constructors shipped as `client or Client()`, so a caller-supplied client whose `__bool__` /
`__len__` reports false was silently discarded onto a fresh client with a different session —
precisely the `or`-fallback-on-a-legitimately-falsy-left-operand shape
[`docs/builder/BUILD.md`][build] `### Fail-open shapes` catalogues. Commit `f7fbead4` moved both
to `client if client is not None else Client()`. **The claim the constructor text may no longer
make:** that the `client=` seam is honored by truthiness. The spec states the `is not None`
selection directly.

**Change record — the floor number
([F6](#f6--the-strawberry-floor-the-spec-named-is-stale)).** Ground 1 named
`strawberry-graphql>=0.262.0` as the hard dependency the base rides inside. The number moved; the
ground did not. The spec now names `pyproject.toml` and [`docs/builder/BUILD.md`][build]
`## Floor verification` as the source instead of restating a version.

### Decision 6 — `.query()` returns the typed `Response`

Spec: [Decision 6][d6].

**Alternatives rejected.** *Moved from the spec.*

- **Raw `HttpResponse` return (graphene's flavor).** The card recommends against it; every
  consumer then re-decodes the body, and the "200 plus an `errors` key" trap returns to every call
  site.
- **Strawberry's `Response` unmodified (no raw-response field).** Strands status/header/cookie
  assertions on raw posts and shrinks the Slice-2 switchover — without the field the card's "live
  HTTP tests switch to the helper" DoD would quietly shrink.
- **Two return flavors behind a flag (`raw=True`).** The card says pick one; a mode flag is both
  flavors' costs with neither's clarity.
- **A `mutate()` alias for `query()`.** Rejected as scope (no upstream has it; an alias that
  changes nothing invites the false belief it does something — e.g. auto-prefixing `mutation`),
  and named as the fallback in the
  [Risks entry](#risks-and-open-questions--the-preferred-answer--fallback-weighing).

**The card-vs-source conflict, moved.** The card attributed a `.mutate()` surface twice — its
"Verified in upstream" section to the upstream base (`BaseGraphQLTestClient`), its "Why it
matters" to the `strawberry_django.test.client.TestClient` subclass — but the base read for this
spec has no `mutate()`, and neither does that subclass or graphene's mixin. Recorded per the
[`docs/SPECS/NEXT.md`][next] prefer-the-card rule rather than silently reconciled; on a *factual
claim about upstream source* the source wins, so the card shipped no `mutate()`. The spec keeps
the normative half ("there is deliberately no `mutate()`"); the conflict's history is here.

**Derivation, moved.** The `response` field takes a `None` default as a deliberate choice — the
parent's three fields carry no defaults, so a defaultless child field would have been legal too —
but the client always populates it, so the default is never observed in practice. That trade is
recorded here; the field and its contract stay in the spec.

**Why the default is kept, stated correctly (post-ship reconciliation cycle).** A verification
round proposed removing it and then kept it on the ground that the default "is load-bearing for
dataclass field ordering against the engine base". **That reason is false, and the reason is what
a later reader acts on.** The engine's `Response` declares three fields and none of them carries a
default, so a subclass appending a non-defaulted field constructs fine — executed, not reasoned.
The disposition is still right, for a different reason: `Response` is one of the names this
package re-exports from its `testing` root, so it is **shipped public surface on an `0.0.x`
line**, and removing a default narrows a constructor consumers may already be calling. Both
in-repo construction sites pass `response=` explicitly, so the default is genuinely never
exercised — which is what the field's own docstring already says. Recorded because a reader who
acts on the field-ordering rationale will discover it is untrue and conclude the constraint has
evaporated.

### Decision 7 — Endpoint resolution: the settings key is `TESTING_ENDPOINT`

Spec: [Decision 7][d7].

**Alternatives rejected.** *Moved from the spec.*

- **`GRAPHQL_TESTING_ENDPOINT` (the card's working name).** A redundant prefix inside the
  namespaced dict; it breaks the graphene name parity the card itself cites. The card text
  explicitly delegated the final name ("final name pinned during implementation" — pinned in the
  spec instead, where the alternatives could be recorded).
- **A Django-global settings name (top-level `GRAPHQL_TESTING_ENDPOINT`).** The package's one
  settings surface is the `DJANGO_STRAWBERRY_FRAMEWORK` dict (`conf.py`'s documented contract); a
  second top-level name fragments it.
- **Default `"/graphql"` (graphene's).** Fakeshop and Strawberry both use the trailing slash; a
  slash-less default would not match that `/graphql/` mount — under `APPEND_SLASH` a body-bearing
  POST raises `RuntimeError` in `DEBUG` (or is 301-redirected in a way that drops the body), never
  cleanly reaching the view.
- **Re-reading the settings key on every request.** The settings-derived default resolves once at
  construction (upstream's posture); the explicit per-call `url=` override covers the legitimate
  per-request need without a settings read per call.
- **Dropping the card's per-call override entirely** (constructor + class attribute only). The
  card explicitly names a per-call override; honoring it is one keyword-only parameter on the
  package-owned `query()` plus the widened `request(..., *, url=None)` transport hook, so there is
  no cost worth trading the card constraint away for.

**Naming derivation, moved because it argues for the name rather than stating it.** Inside a
settings dict named `DJANGO_STRAWBERRY_FRAMEWORK` every key is about this package's GraphQL
surface, so a `GRAPHQL_` prefix is pure redundancy — and the unprefixed name is byte-identical to
graphene's own `TESTING_ENDPOINT` key, which is the knob's lineage. Existing keys set the style:
none carry a `GRAPHQL_` prefix (`NESTED_CONNECTION_STRATEGY`, `APPLY_UPSTREAM_PATCHES`;
`RELAY_GLOBALID_STRATEGY`'s prefix names the Relay subsystem, not GraphQL).

**Change record — the accessor carries its own pytest collection guard
([F4](#f4--the-module-level-accessors-__test__--false-was-absent-from-the-spec)).** The decision
specified the key constant and the thin accessor and stopped there. Commit `a62d6dca` added
`testing_endpoint_setting.__test__ = False` post-ship: the accessor's name matches pytest's
default `test*` *function* pattern, so a test module importing it unaliased gets it collected, and
it returns a `str`, which fails the run via `PytestReturnNotNoneWarning` under the repo's
`filterwarnings = error` posture. Same hazard class and same idiom as the class-level guards the
spec already named nine times — which is exactly why it was easy to miss. The spec now states it
as part of the accessor's contract.

**Change record — no validation is added; the docstring and the spec's matching sentences are
restated (post-ship reconciliation cycle, maintainer decision).** A verification round reported
the accessor as having a validation gap: a non-`str` `TESTING_ENDPOINT` would post an object and
fail somewhere unhelpful. **The premise was false, and the investigation overturned the finding
that prompted it.** `django.test.RequestFactory.generic` coerces the path —
`urlsplit(str(path))`, on a line whose own comment reads that the path can be lazy, present at
two sites in every release across the audited range `5.2.0` through `6.1.0` — so `None`, `7` and
`["/graphql/"]` post to `/None`, `/7`, `/['graphql/']` and produce the **identical** 404 plus
non-JSON `ValueError` a typo'd string does. There is no gap to close. The accessor census
confirms the module's practice rather than an aspiration: of its key readers, all but one are
thin, the one validator documents a four-consumer DRY reason this key does not have, and two
toggles are deliberately unvalidated.

- **Rejected — reject a non-`str` at the accessor.** It would ship a concrete regression:
  `TESTING_ENDPOINT = reverse_lazy(...)` is a lazy proxy, not a `str`, and works today precisely
  because Django coerces lazily. A `str` gate breaks it; widening the gate to admit the proxy
  means importing a Django-internal type into [`conf.py`][conf] and making this key the module's
  first shape gate, against four sibling docstrings that describe the module as a thin reader.
- **Rejected — leave both as they are.** The docstring was genuinely false, just not for the
  input class anyone suspected: `TESTING_ENDPOINT = ""` is the value that does **not** 404 — it
  routes to the URLconf root, which in the example project serves a 200 HTML page. The old
  wording's "a wrong endpoint *string* is an ordinary 404" was therefore false for a *string* and
  true for the non-strings it excluded. "Ordinarily a 404" is the load-bearing hedge that makes
  the restated sentence true; the reviewer's proposed narrowing to "a wrong endpoint *string*"
  would have made it **less** true and was not applied.

**A second defect this discharges, previously unknown:** `## Error shapes` claimed "the traceback
carries the failing status". Django's non-JSON message has never carried it — the status is
visible only because the runner renders the failing frame's locals, and the path only in the
captured `django.request` log. The clause was false on its own date, before any post-ship commit,
so it needed a correction rather than a re-description of moved code. The spec now says what is
actually observable in each of the three places.

**Considered and not taken — two rows that would make the restated claim mechanically failable:**
a live parametrization of the wrong-endpoint row over `None`, and a package-tier row asserting the
accessor returns a non-`str` verbatim. Both are cheap and both would flip if a future pass added
an accessor gate. Neither landed: the claim they would pin is a statement about *Django's* own
coercion, already established across the audited release range by reading every cached wheel, and
the package-tier row's home is `tests/base/test_conf.py`, which sat outside the write set of the
cohort that restated the docstring. Recorded here rather than dropped, so a later pass adding
either knows why they are absent and not merely missing.

### Decision 8 — Async shape: `AsyncTestClient` subclasses `TestClient`

Spec: [Decision 8][d8].

**Alternatives rejected.** *Moved from the spec.*

- **A flat `AsyncTestClient(BaseGraphQLTestClient)`.** It re-declares the constructor,
  `request()`, and `login()` just to avoid an is-a relationship that is actually true (the async
  client IS the sync client with an awaited transport).
- **One class with sync/async auto-detection** (the package's `is_async_callable` machinery from
  `DjangoListField`). That machinery exists for *consumer-supplied* resolvers whose color the
  package cannot know; here the caller chooses the color explicitly by picking the class, and a
  dual-color `query()` would return `Response | Coroutine` — the exact ambiguity the typed helper
  exists to remove.

**Measurement recorded so it is not re-derived (post-ship reconciliation cycle).** The async
constructor has two contracts on one line, and only one of them is reachable by the mutation that
looks like it tests both. Weakening the *selection* (`client if client is not None else
AsyncClient()` → `client or AsyncClient()`) leaves the **default arm** intact, because
`None or AsyncClient()` still yields an `AsyncClient`; the mutation is orthogonal to the arm
rather than evidence about it. Replacing the arm itself (`AsyncClient()` → the sync `Client()`)
fails exactly one row, the one named for that arm, so the arm **is** pinned. Both contracts are
covered; they simply are not covered by the same mutation, and a reader comparing a row list
against a failing-node list will otherwise read the difference as a miscount.

### Decision 9 — Multipart uploads: `files=` maps variable paths to file parts

Spec: [Decision 9][d9].

**Alternatives rejected.** *Moved from the spec.*

- **Infer file paths from the `variables` structure** (the base's approach — walk the dict, guess
  folders, number lists). That heuristic is exactly what returns an empty map for nested input
  objects; an explicit path-keyed `files=` is unambiguous, trivially recursive, and self-documents
  where each file lands.
- **Copy `format="multipart"` verbatim.** Knowingly shipping an inert kwarg that implies a DRF
  client is in play misleads every future reader; the borrow is of behavior, not typos.
- **Explicit `content_type=MULTIPART_CONTENT`.** Considered — it states the intent — but Django's
  test client treats the *default* argument specially (it encodes the data dict itself only when
  `content_type` is the default sentinel value); passing the constant explicitly is equivalent
  today but couples to the constant's identity. The omission, plus the comment, is the documented
  idiom, and that instruction stayed in the spec.

**Change record — `operation_name=""` is sent, not dropped (Revision 3 F3).** `_build_body`
originally gated on truthiness (`if operation_name:`), so an explicit empty string was silently
reinterpreted as "no operation name". It now gates on `is not None` and sends `operationName: ""`
for the server to reject with a real GraphQL error — the module's fail-at-the-source posture.
**The claim the decision may no longer make:** that the key's presence tracks truthiness rather
than provision.

**Change record — reserved envelope keys are refused (Revision 3 F4).** A pathological
`files={"operations": f}` / `files={"map": f}` (with a matching `None` placeholder) would
overwrite the envelope via the trailing `**files` spread. `_build_body` now rejects a `files` key
named `operations` or `map` at the source, matching the sibling guards' shape.

**Change record — the walker was never described, and the entry condition was described wrongly
([F5](#f5--decision-9-and-error-shapes-described-a-guard-the-code-does-not-have)).** The decision
said `_build_body` "enforces this with an explicit `raise AssertionError` guard", singular. The
shipped contract was always a recursive path walker with several rejection branches, plus
truthiness — not `is not None` — as the multipart entry condition. **The claim the decision may no
longer make:** that one guard covers the placeholder contract, or that `files is not None`
switches the envelope. The code was correct throughout; only the description moved.

**Change record — the walker hardened three times post-ship
([F3](#f3--six-post-ship-behaviour-families-were-absent-from-the-spec) families 3–6).**

- `a8f31a2d` widened the array branch from `isinstance(current, list)` to `(list, tuple)`, because
  `json.dumps` renders both as JSON arrays and the map points into the POST-serialization shape,
  not into the Python type.
- `a8f31a2d` added the **empty dotted segment** rejection (a `""` key's `variables.` path, or
  `variables.data.` for a `""` field): such a map entry could never name a GraphQL variable, so
  emitting it would produce an opaque server-side 400 naming no path.
- `a8f31a2d` added the **unreadable `__len__`** rejection, raised with the guard's uniform
  `AssertionError` type so a hostile `__len__` cannot replace the guard with a raw exception
  escape.
- `b4d0c8ae` replaced `segment.isdigit() and int(segment) < len(current)` with a guarded `int()`
  conversion plus `index >= 0 and str(index) == segment`. The old spelling's two domains disagree:
  `isdigit()` accepts superscripts `int()` rejects, and digit-like Unicode and very long decimal
  strings do not share `int()`'s acceptance domain, so a non-canonical index could be accepted
  where the emitted `object-path` segment could not name it.
- `f7fbead4` moved every diagnostic in `_build_body` and `_assert_file_placeholders` from `{x!r}`
  to `_safe_arg_repr(x)`, so a hostile `__repr__` on a consumer-supplied path or value cannot
  escape the guard as a raw exception. This is a **new cross-module dependency** on
  `django_strawberry_framework/exceptions.py` that the spec's `## Helper-reuse obligations (DRY)`
  list did not carry; it is now **D5** there, a reuse rather than a non-reuse.

Each of these is a *tightening* of the same contract, not a change to it: every one converts a
shape the old code would have emitted into a rejection at the source.

**Change record — the empty-`variables` guard is respelled to an envelope-coherence
check, not deleted (post-ship reconciliation cycle, maintainer decision).** A verification round reported the guard fully
subsumed by `TestClient._assert_file_placeholders` and therefore a DRY violation. **The premise
was false, and the investigation that tested it overturned the finding that prompted it.** For a
*falsy container carrying real placeholders* — a `dict` subclass whose `__bool__` returns `False`
holding `{"file": None}`, which is inside the annotated `dict[str, Any] | None` domain — the
guard rejects and the walker **accepts**: with the guard removed the builder emits `operations`
carrying no `variables` member beside a `map` pointing into `variables.file`, a spec-invalid
envelope Strawberry rejects with "File(s) missing in form data", a message that blames the files,
which are present. So the guard decides a verdict, and the pair that was actually duplicated was
never guard-and-walker but **guard-and-emission**: both spelled the same truthiness test, so a
change to the emission rule had to move two sites. Decided: keep the raise and the message bytes,
and respell the predicate as `if "variables" not in body:` so the guard derives from the envelope
it protects. Verdict-identical on every probed input, and the emission becomes the single owner of
when the member exists.

- **Rejected — delete the guard and let the walker own every rejection.** The evidence rules it
  out: the walker does not catch the falsy-container class at all, so deletion fails that class
  open.
- **Rejected — keep `if not variables:` and only add rows.** The smallest diff, and its
  conclusion is right, but it leaves a truthiness test on a value where *absent* and *empty*
  differ — [`docs/builder/BUILD.md`][build] `### Fail-open shapes`' first-named suspect — correct
  today only because the walker happens to catch the neighbouring cases.
- **Superseded — the verification round's own keep-and-pin reasoning.** Its conclusion survives;
  its argument does not. It invoked "never a weaker boundary" while simultaneously asserting the
  guard decides no verdict, which as written would forbid deleting **any** dead branch. The
  corrected premise — the guard *does* decide a verdict — is what actually saves it.

Two further findings folded in. The walker's message for `variables=None` is **actively
misleading** ("the value there is not a dict or list" when there is no value at any path), so the
call-level wording is materially better rather than cosmetically. And the rows that pinned the
guard matched on `"placeholder"`, a word every walker message also carries, so they could not
distinguish the call-level rejection from the path-level one; they now match the guard's own
phrase. **The claim this decision may no longer make:** that the guard tests the `variables`
argument's truthiness. It tests the built envelope; the truthiness is the emission's, one line
above.

### Decision 10 — Mixin-first: `GraphQLTestMixin` composes over `TestClient`

Spec: [Decision 10][d10].

**Alternatives rejected.** *Moved from the spec.*

- **Concrete test cases only, no mixin.** The card pins mixin-first and names the custom-base
  composition use case.
- **The mixin re-implements the POST (graphene's actual internals).** Two body-builders drift; the
  delegate costs one object per call in test code.
- **Renamed assertion helpers (`assert_no_errors` snake_case).** The helpers exist for graphene
  migrants; unittest's own assertion vocabulary is camelCase (`assertEqual`), so the graphene names
  are also the idiomatic unittest names.
- **`assert_no_errors=True` on the mixin's `query()` for family-wide uniformity.** It silently
  breaks the graphene migration's central pattern — auto-raising from inside `query()` breaks every
  ported `assertResponseHasErrors` test at the call site, before the assertion helper runs;
  uniformity of defaults is worth less than both migrations working.

**Derivation, moved.** The keyword-only signature after `query` is a deliberate trade of graphene
positional-call fidelity for one uniform keyword signature across the pytest client and the mixin:
graphene's own positional order `(query, operation_name, input_data, variables, headers)` cannot
survive dropping `input_data` intact anyway. The flipped `assert_no_errors=False` default is the
same trade in the other direction — each flavor defaults to its own upstream's behavior — and its
live weighing is in the
[Risks entry](#risks-and-open-questions--the-preferred-answer--fallback-weighing).

### Decision 11 — Test strategy: the live switchover is the primary coverage

Spec: [Decision 11][d11].

**Alternatives rejected.** *Moved from the spec.*

- **A package-only test suite with the switchover deferred.** The card's DoD names the switchover,
  and without it the package tests would duplicate live coverage the live-first mandate says
  belongs in the live tier — the exact "package-only stand-in" pattern the live-first promotion
  rule exists to retire.
- **Switch only one representative live file.** The DoD says "live HTTP tests … switch to the
  helper", plural; a partial switchover leaves two idioms in the tree indefinitely, which is worse
  for readers than either.
- **Mock-based unit tests for `request()`.** Real fakeshop requests are available in-process
  (`pytest.ini` runs the suite against fakeshop settings); mock only when the real path is
  impossible.

**Change record — the shipped split moved more live than the plan first anticipated (Revision 3
F2).** The spec's Decision 11, `## Test plan` (scenarios 2 and 9–12), the Slice-1 checklist, and
the `## Definition of done` all described the `AsyncTestClient` real-request paths, the unittest
family end to end, and the `assert_no_errors=True` raising direction as *package-tier
request-driving tests*. The implementation moved all three **live** — they proved live-reachable
under the live-first mandate — leaving `tests/testing/test_client.py` entirely DB-free. All four
sites were realigned to the shipped split, and the spec now states that split directly rather than
as a correction applied to an earlier list. **The claim the decision may no longer make:** that any
package-tier test in this card drives a request.

**Change record — Scenario 3's premise was false (Revision 3 F2).** The spec had claimed an absent
`operationName` "fails GraphQL-side". It does not: Strawberry's HTTP layer defaults an absent
`operationName` to the document's *first* operation, which is the behaviour
`examples/fakeshop/test_query/test_products_api.py::test_operation_name_dispatch_via_test_client`
pins. Corrected at the source rather than annotated.

**Change record — the async multipart round trip was unproven (Revision 3 F1).** The DoD claimed
multipart "on both clients" while no test drove `AsyncTestClient.query(..., files=...)`: the sync
multipart path was proven live twice and the builder's shapes pinned package-tier, but nothing
exercised the ASGI-scope multipart parse through `AsyncClientHandler`. The async color of the sync
nested two-file upload was added live in
`examples/fakeshop/test_query/test_client_api.py::test_async_multipart_upload_creates_media_specimen`
(`createMediaSpecimen` under `transactional_db` sync seeding with `MEDIA_ROOT=tmp_path`), so the
"both clients" claim is earned live on both.

**Change record — the Test plan grew a fifteenth scenario
([F7](#f7--post-ship-test-tier-additions-were-absent-from-the-specs-test-plan)).** The
post-ship branches of [F3](#f3--six-post-ship-behaviour-families-were-absent-from-the-spec) had
owners in the suite but no scenario number, so the plan's every-branch-has-a-named-owner claim was
false as written while being true of the suite. Scenario 15 names them.

**Change record — the "custom-view plumbing" exemption class is dropped and its sites are
converted (post-ship reconciliation cycle, maintainer decision).** A verification round flagged
ten live-tier raw posts carrying no exemption declaration and judged them all honest exemptions,
leaning on this decision's `test_multi_db.py` custom-view-plumbing class. **The premise was false
in the direction that matters, and the investigation overturned the finding that prompted it:**
that class's only named exemplar had itself been converted — `test_multi_db.py` posts through the
client and retains no raw post — so the class had no surviving exemplar, and nine of the ten
flagged sites met no class at all. They were unconverted, not exempt. Decided: convert them, and
drop the class from both places the spec named it (the Slice-2 checklist and this decision's
"switchover's own discipline" paragraph).

- **Rejected — write the nine exemption comments.** It would assert an exemption class those
  sites do not meet. A declaration that is false is worse than a missing one, because it
  forecloses the next reader's question.
- **Rejected — defer the conversions to a later card.** Defensible on the merits — every
  undeclared file postdates this card's ship by a month or more, so it is later cards' drift
  rather than a Slice-2 miss — but naming the owning card requires a board edit the cycle's
  fence excluded, and an item routed forward without a named owner dies.

**Two census corrections travelled with it, both against the round that raised the finding.** The
swept population is 16 raw posts across eight files, not nine; the ninth "file" was the shared
live-tier helper module, which sits outside the population being swept. And a raw multipart POST
spelled `client.generic("POST", ...)` is **invisible to a `.post(` grep** — the
vocabulary-is-not-population failure, committed inside the census that was checking for it.

**What the surviving exemption list is, measured rather than inherited.** The
hand-built-multipart class survives with three exemplars in
[`test_products_api.py`][test-products-api], each keeping a raw envelope because the *arbitrary
file label* is the assertion — a wire shape the path-keyed builder never emits. A proposed
replacement sentence saying no live file claims that class was measured on the converting
cohort's own four files and is false of the tree; the spec states the class with its actual
warrant instead. One undeclared raw async post remains in the live tier, in a file belonging to a
concurrently running cycle and therefore outside this cycle's fence. That is why the `## Test
plan` and `## Definition of done` sentences are now stated as a **rule about the switchover's
own population** — a retained raw post names the class it claims, and a call meeting no class
converts — rather than as a tree-wide census, which a file this cycle may not touch would
falsify on the day it was written.

**Change record — the live tier's async rows drive the package's own async client.** The same
cycle moved nine call sites in four live modules off `django.test.Client` / `AsyncClient` onto
`TestClient` / `AsyncTestClient`, with every assertion preserved. Two conversion traps are worth
recording because they are invisible until a row inverts: `assert_no_errors=False` is required
even where **no** error is expected, or the client's own raise silently relocates the row's
`errors is None` assertion; and a row asserting `"errors" not in payload` needs the decoded dict,
not a payload rebuilt from the typed `Response`, which inverts it. A shared awaited live-tier post
helper is the shape those conversions now want — five near-identical awaited call bodies across
four modules, a sixth waiting in the concurrently-owned file — but the live tier's shared helper
module is declared sync-only and belonged to no cohort's write set, so nothing was extracted.

### Decision 12 — Version bumps are owned by the joint `0.0.14` cut

Spec: [Decision 12][d12].

**Alternatives rejected.** *Moved from the spec.*

- **Bump to `0.0.14` in Slice 3.** The open sibling (and this card) still shipped into `0.0.14`; a
  per-card bump races the joint cut and would be reconciled twice over.

**Justification, moved.** Per [`docs/SPECS/NEXT.md`][next] Step 3 / Step 6, when multiple cards
target one patch version the bump belongs to the joint cut, not any individual card's spec. At
authoring time one other non-Done card (`TODO-ALPHA-044-0.0.14`) sat at `0.0.14` beside this one;
whichever `0.0.14` card landed last owned the version quintet. This card was not the last.

## Non-decision entries

### Borrowing posture — the two-upstream split

Spec: [Borrowing posture][borrowing].

**What stayed in the spec, and why it is not deliberation.** The per-item borrowed / owned /
deliberately-not-borrowed lists are a live contract: they state what the package must and must not
do, and the `## Helper-reuse obligations (DRY)` checklist cites them item by item. The section was
graded clause by clause rather than moved as a block.

**The upstream source readings, moved because they argue rather than state.** The section's
account of *why* the package cannot ride the base's `query()` — that its signature is fixed
(`query(query, variables=None, headers=None, files=None, assert_no_errors=True)`: no
`operation_name`, no `url`), that it calls `request(body, headers, files)` with no target
argument, and that it constructs the base `Response` directly — is the derivation behind
Decision 5 ground 2, which the spec states normatively. So is the observation that this is not a
new posture: upstream's own `AsyncTestClient.query()` already fully re-implements the flow rather
than calling `super().query()`, so owning the **sync** `query()` is the same move applied to both
colors.

**The full upstream inventories, moved.** The 90-line read of
`strawberry_django/test/client.py` and the 162-line read of
`graphene_django/utils/testing.py` — `graphql_query`'s envelope building and `input_data`
convenience, the mixin's deprecated `_client` property shim, graphene's `TESTING_ENDPOINT` default
of `"/graphql"` — are the evidence the borrow decisions rest on. The decisions themselves, and the
non-borrow list they produced, stay in the spec.

**Change record — the shipped module grew one borrow the posture did not list
([F3](#f3--six-post-ship-behaviour-families-were-absent-from-the-spec) family 3).** Neither
upstream contributes `_safe_arg_repr`; it is the package's own hostile-metadata containment helper
from `django_strawberry_framework/exceptions.py`, adopted post-ship so guard diagnostics cannot be
hijacked by a consumer-supplied `__repr__`. It is a package-internal reuse rather than an upstream
borrow, which is why it lands in `## Helper-reuse obligations (DRY)` as D5 rather than here.

### Risks and open questions — the preferred-answer / fallback weighing

Spec: [Risks and open questions][risks].

**The weighing, moved.** Each risk the spec carried was recorded with a preferred posture and a
fallback. The constraints that are still live stay in the spec; the weighing is here, and the
risks this card closed are recorded as closed.

- **The card's `.query()` / `.mutate()` claim vs. the read source.** *Preferred:* ship no
  `mutate()` — on a factual claim about upstream source, the source wins. *Fallback:* if the
  maintainer wants the card's wording honored literally, `mutate = query` as a documented alias is
  a one-line follow-up, deliberately not shipped by default (an alias implies a behavioral
  difference that does not exist). **Closed in the preferred direction:** the shipped module
  carries no `mutate()`, and `TestClient`'s docstring says a mutation posts through `query()`.
- **`BaseGraphQLTestClient` presence and shape at the Strawberry floor.** *Preferred:* present and
  shape-stable (the class long predates the floor). *Fallback:* bump the project's Strawberry
  floor — the same recourse [`spec-041`][spec-041] / [`spec-042`][spec-042] named for their engine
  gates. **Closed in the preferred direction**, and the version the risk named is what later
  rotted — see [F6](#f6--the-strawberry-floor-the-spec-named-is-stale).
- **Upstream reshapes the base later.** *Preferred:* accept the remaining coupling; the
  request-driving tests fail loudly under a refreshed lock and the fix tracks upstream's change.
  *Fallback:* pin the reshaped pieces locally — `_decode` is small enough to own too if it ever
  moves. Still live; the constraint stays in the spec.
- **The switchover's breadth.** *Preferred:* the Decision 11 rule — assertions unchanged or the
  test takes the wire-shape exemption — plus the raw `response` field existing precisely so no
  assertion *needs* weakening; the maintainer's diff review is the gate. *Fallback:* any file
  whose conversion proves contentious stays unconverted with the exemption comment. The switchover
  landed; the rule stays in the spec as the standing conversion discipline.
- **Async DB tests joining a suite with known async-connection hazards.** *Preferred:* the
  `AsyncTestClient` tests mark `django_db`, follow `tests/conftest.py`'s existing hygiene, and
  stay few. *Fallback:* a surfaced flake is fixed at source in the shared conftest, never by
  weakening `-W error`. The preferred posture held; the count in the original wording ("two
  tests") was a ship-time reading and is not a contract — the live tier carries more async rows
  today.
- **The debug-toolbar async handoff.** *Preferred for `0.0.14`:* the vehicle ships here; with 042
  landed without the smoke, it is a small follow-on inside the toolbar card's now-landed test
  module (or the joint cut), where its soft-dependency fixture already lives. *Fallback:* if the
  joint cut wants it bundled here after all, it is one test reusing spec-042's fixture — an
  addition, not a redesign. Still live as a handoff; the spec keeps it in `## Out of scope`.
- **The mixin's flipped `assert_no_errors=False` default.** *Preferred:* each flavor matches its
  own upstream's behavior (the property that makes both migrations work unchanged); both
  docstrings state the other's default. *Fallback:* if real-world confusion outweighs migration
  fidelity, a future minor can align the mixin to `True` — a deliberate breaking change for
  graphene-ported error tests, acceptable only pre-`1.0.0`. Still live.

### Current state — the prediction clauses

Spec: [Current state][current-state].

The section's header dates it ("A true description of the repo as this spec is authored"), so its
**observations stand** even where later work falsified them — that is the vintage rule in
[`docs/builder/BUILD.md`][build]. Its **prediction** clauses do not, and one bullet carried both.

- **"The engine base is present, at a hard dependency."** The observation — what
  `strawberry/test/client.py` defines, and why its `_build_body` /
  `_build_multipart_file_map` are insufficient for this repo — stands as a dated reading. The
  clause naming the package's floor as `strawberry-graphql>=0.262.0` was not an observation of the
  pre-build repo's *state so much as* a restatement of a moving number, and it is now false; the
  spec names the source instead
  ([F6](#f6--the-strawberry-floor-the-spec-named-is-stale)).
- **"`docs/TREE.md` reserves the module."** A dated observation that stands; the prediction "the
  regenerated tree adds both in Slice 3" was discharged and now reads as what Slice 3 did.
- **Everything else in the section** is a dated observation and was left untouched.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../../../AGENTS.md
[start]: ../../../START.md

<!-- docs/ -->

<!-- docs/SPECS/ -->
[borrowing]: ../spec-043-test_client-0_0_14.md#borrowing-posture
[current-state]: ../spec-043-test_client-0_0_14.md#current-state
[d1]: ../spec-043-test_client-0_0_14.md#decision-1--spec-filename-and-canonical-naming
[d10]: ../spec-043-test_client-0_0_14.md#decision-10--mixin-first-graphqltestmixin-composes-over-testclient-the-graphene-assertion-helpers-keep-their-names-typed-response-shaped
[d11]: ../spec-043-test_client-0_0_14.md#decision-11--test-strategy-the-live-switchover-is-the-primary-coverage-teststestingtest_clientpy-owns-the-rest
[d12]: ../spec-043-test_client-0_0_14.md#decision-12--version-bumps-are-owned-by-the-joint-0014-cut
[d2]: ../spec-043-test_client-0_0_14.md#decision-2--card-scope-boundary-the-test-client-family-ships-channels-session-auth-verification-the-toolbars-async-smoke-and-fakeshop-runtime-changes-stay-out
[d3]: ../spec-043-test_client-0_0_14.md#decision-3--the-symbols-are-upstreams-own-names--testclient--asynctestclient--graphqltestmixin--graphqltestcase--graphqltransactiontestcase-distinctly-ours-import-path
[d4]: ../spec-043-test_client-0_0_14.md#decision-4--module-export-and-test-locations-testingclientpy-re-exported-from-the-testing-root-teststestingtest_clientpy
[d5]: ../spec-043-test_client-0_0_14.md#decision-5--subclass-strawberrys-basegraphqltestclient--engine-owned-base-over-a-hard-dependency-no-soft-dependency-machinery
[d6]: ../spec-043-test_client-0_0_14.md#decision-6--query-returns-the-typed-response-dataclass-extended-with-the-raw-httpresponse-operation_name-is-supported
[d7]: ../spec-043-test_client-0_0_14.md#decision-7--endpoint-resolution-the-settings-key-is-testing_endpoint-default-graphql--resolving-the-cards-graphql_testing_endpoint-working-name
[d8]: ../spec-043-test_client-0_0_14.md#decision-8--async-shape-asynctestclient-subclasses-testclient-ported-as-is
[d9]: ../spec-043-test_client-0_0_14.md#decision-9--multipart-uploads-files-maps-variable-paths-to-file-parts-the-package-owns-the-bodymultipart-builder-upstreams-no-op-format-kwarg-is-dropped
[next]: ../NEXT.md
[risks]: ../spec-043-test_client-0_0_14.md#risks-and-open-questions
[spec-031]: ../spec-031-globalid_encoding-0_0_9.md
[spec-041]: ../spec-041-channels_router-0_0_14.md
[spec-042]: ../spec-042-debug_toolbar-0_0_14.md
[spec-043]: ../spec-043-test_client-0_0_14.md
[terms]: spec-043-test_client-0_0_14-terms.csv

<!-- docs/builder/ -->
[build]: ../../builder/BUILD.md

<!-- django_strawberry_framework/ -->
[conf]: ../../../django_strawberry_framework/conf.py

<!-- tests/ -->

<!-- examples/ -->
[test-products-api]: ../../../examples/fakeshop/test_query/test_products_api.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
