# Rationale: spec-044 — Response-extensions debug middleware (deliberation, rejected alternatives, change record)

Deliberative companion to [`spec-044-debug_extension-0_0_14.md`][spec-044]. The spec is the
contract and states only what is currently true; everything that explains **how it got there**
lives here: the alternatives each decision rejected and why each lost, the derivations that do
not change how a decision is implemented, every change a decision has undergone with the
revision that caused it, and any claim a decision once made and may no longer make.

Created by the `docs/builder/BUILD.md` `## Spec rationale extraction` pass. The text below was
**moved** out of the spec, not copied: it exists here and nowhere else. Only the links were
rewritten — the moved text's in-page anchors into spec headings became reference-style links back
into the spec, because the same text now lives in a different file.

## How to read this file

- **One entry per spec decision**, under the decision's own heading, with a `Spec:` line linking
  the decision it belongs to. A citation such as "Decision 6's rejected alternatives" therefore
  resolves to exactly one place; an entry that named no decision could not be looked up and would
  be worthless however well argued.
- **Worker 3 reads this during review** — it is what stops a reviewer re-raising a settled
  alternative, and it is the reasoning the finished implementation is checked against.
  **Worker 1 owns it** as spec custodian and audits it at final verification. **Worker 2 never
  reads it**: that is the point of the move.
- **Append-only during the build.** A new round's decisions land in the spec; their rejected
  alternatives, derivations and retractions append here in the same custodian pass.
- **Round attribution.** spec-044 had no review rounds during its build: all twelve decisions
  were authored in **Revision 1** and corrected in place by **Revisions 2-8**, every one of them
  a pre-build authoring pass (2026-07-10 to 2026-07-11). The spec's three slices were then built,
  reviewed, and released at `0.0.14`. The full revision history is reproduced below, followed by
  a per-decision index of which revision changed what.
- **The move happened after the release, not before the build.** The shipped cycle skipped it;
  this pass supplies it. So nothing here was withheld from the builder who implemented the spec —
  a reader comparing the shipped code against these entries is reading them for the first time in
  the same order Worker 3 would have.

### What deliberately stayed in the spec, and why

The carve-out is load-bearing: implementation-relevant rationale — the "why" that changes HOW a
thing is built — stays in the spec, and where a sentence is ambiguous between deliberation and
instruction it stays. These rulings are recorded so a later pass does not re-open them:

- **[Decision 4][s44-d4]'s cursor-wrap-port and direct-`CaptureQueriesContext` rejections stay in
  the spec.** Only its bare-`connection.queries` rejection moved. The cursor-wrap-port bullet names
  the concrete cursor-wrapping hazard the package has already paid for (the
  [Django Trac #37064 hardening][glossary-django-trac-37064]) and the structural constraint that
  keeps a richer fidelity source "one private function swap away" — both bind a future writer at
  the site. The direct-`CaptureQueriesContext` bullet carries three constraints an implementer must
  not rediscover the hard way (`ensure_connection()` opening every alias, the process-global
  `request_started → reset_queries` signal toggle, and the refcount-free single-context restore)
  plus the normative sentence about reusing the class's semantic contract without its side effects
  — and [Decision 10][s44-d10] cites it ("per Decision 4's rejection of wrapping
  `CaptureQueriesContext` directly, no connection is force-opened"), so moving it would leave a
  cross-reference pointing out of the spec. Both citations name the alternative instead of
  numbering it, here and in the spec: dropping one bullet from a list renumbers every bullet after
  it, which is exactly how this move falsified the citation on its first attempt.
- **Every numbered `Grounds:` list stays in full.** Two grounds are pure derivation on their own
  merits — [Decision 3][s44-d3]'s and [Decision 4][s44-d4]'s "the card pre-picked it" — but the
  moved alternative bullets cite grounds *by number* ("everything in ground 2", "Rejected per
  ground 1"), so the numbering is load-bearing across the file boundary. Stability of that
  numbering is worth more than two sentences.
- **`## Current state` stays whole**, despite reading like a survey of deliberation. Every bullet
  is a source-verified fact that a decision cites as its premise — the engine's verified
  `get_results` call ordering ([Decision 7][s44-d7] ground 2), the `queries_logged` /
  `CursorDebugWrapper` mechanics ([Decision 4][s44-d4]), the old floor's `_sync_extensions` cache
  ([Decision 6][s44-d6]) — and the `DEBUG=False`-silent-empty trap stated there is the canonical
  instruction-shaped "why" the whole bracket exists.
- **`## Problem statement`, `## Borrowing posture`, and `## Goal and cookbook cross-reference`
  stay whole.** Borrowing posture is the parity contract (what is borrowed, what is refused, and
  the reason each refusal must not be re-borrowed by a later card), and the cookbook section is a
  doc obligation plus the consumer-facing migration recipe.
- **`## Risks and open questions` keeps its preferred-answer / fallback pairs.** Instruction cites
  them: DRY D4 pins the serializers at module level so the section's `_debug`-facade fallback can
  import them, and the Test plan pins the overlap-safety suite against the same fallback. Only the
  resolved card-vs-shape conflict and the retracted async premise moved.

## Change record — revision history

Moved in full from the spec's header, where it stood under the line "Revision history (kept
inline so the spec is self-contained):". It is the chronology of how the twelve decisions reached
their current form; the spec now states only the form they reached.

- **Revision 1** — initial draft authored from the [`WIP-ALPHA-044-0.0.14`][kanban]
  card body via the [`docs/SPECS/NEXT.md`][next] flow (2026-07-10). Pinned:
  the canonical structured filename
  ([Decision 1][s44-d1]); the
  card-scope boundary — the extension ships alone, with no Django middleware,
  no schema-level field, and no fakeshop always-on wiring
  ([Decision 2][s44-d2]);
  the card's first "pick one before writing the spec" choice resolved **for**
  the response-`extensions` map (the card's own proposed Strawberry-native
  shape and its named default), with the graphene schema-level `_debug` field
  rejected with reasons
  ([Decision 3][s44-d3]);
  the card's second choice resolved **for** `connection.queries` fidelity (the
  card's named default), sharpened to Django's own debug-cursor bracket
  (`force_debug_cursor`, the `CaptureQueriesContext` mechanism) so capture
  does not silently depend on `settings.DEBUG`, with the cursor-wrap port
  rejected with reasons
  ([Decision 4][s44-d4]);
  the symbol pinned as `DjangoDebugExtension` at the
  `django_strawberry_framework.extensions` subpackage — never the package
  root
  ([Decision 5][s44-d5]);
  the opt-in shape pinned as passing the **class** (one fresh instance per
  operation), explicitly not the optimizer's singleton-in-a-factory pattern,
  and the Strawberry floor raised to `0.316.0` because earlier sync execution
  cached extension instances
  ([Decision 6][s44-d6]);
  the hook shape — one sync `on_operation` generator serving both execution
  colors, payload assembly at teardown, `get_results` returning the stash,
  with the pre-execution-error no-`debug`-key consequence derived from the
  engine's verified call ordering
  ([Decision 7][s44-d7]);
  the SQL row shape — graphene's wire names, narrowed to the six fields
  Django's own log supports, every omission named
  ([Decision 8][s44-d8]);
  exception capture off the result's `original_error` chain
  ([Decision 9][s44-d9]);
  the multi-database bracket over `connections.all()`
  ([Decision 10][s44-d10]);
  the test strategy — real HTTP through a probe URLconf in
  `examples/fakeshop/test_query/test_debug_extension_api.py`, with only
  request-impossible mechanics in `tests/extensions/test_debug.py`
  ([Decision 11][s44-d11]);
  and the joint-cut ownership
  ([Decision 12][s44-d12]).
  One card-vs-shipped-shape conflict is recorded in
  [Risks][s44-risks] rather than silently reconciled: the
  card's **title** says "middleware" while its own Architectural posture
  section says the Strawberry-native shape is a `SchemaExtension`, not a
  Django (or Graphene) middleware — resolved per the card's own posture, with
  the title's word kept only as the card-facing feature name.
- **Revision 2** — validation pass against the installed `0.316.0` engine,
  the cached `0.262.0` wheel, Django's query-log implementation, graphene's
  exception middleware, and the repository's test-placement law
  (2026-07-10). Corrected six implementation-blocking defects: raised the
  Strawberry floor to `0.316.0` because the old floor and verified `0.315.3`
  cache sync extension instances and race `execution_context`; split live HTTP
  tests into `examples/fakeshop/test_query/` and retained only
  request-impossible mechanics under `tests/extensions/`; required traceback
  serialization from `exc.__traceback__`; required walking nested
  `GraphQLError.original_error` links so explicitly raised GraphQL errors
  retain graphene parity; replaced the inaccurate bounded-log clamp guarantee
  with Django's actual best-effort length-snapshot semantics; and added a
  lock-protected reference-counted flag bracket so overlapping async
  operations cannot restore `force_debug_cursor` out of order. Added
  concurrent sync isolation, concurrent async restore, and nested-error-chain
  tests as regression gates.
- **Revision 3** — cross-checked the corrected design against
  [`GOAL.md`][goal], the requested
  [`cookbook/recipes/schema.py`][upstream-cookbook-recipes-schema], the
  cookbook's aggregate [`cookbook/schema.py`][upstream-cookbook-schema], and
  its Graphene settings (2026-07-10). Added the explicit goal/cookbook mapping
  and migration diff; confirmed that debug is project-level aggregate-schema
  configuration rather than recipe-app schema surface; and recorded the one
  deliberate wire migration (`_debug` selection → `response.extensions.debug`)
  required to remain Strawberry-native and avoid a Graphene compatibility
  runtime.
- **Revision 4** — DRY-review fold-in (2026-07-11). Applied the maintainer's
  review of the planned module against all thirteen
  `django_strawberry_framework/utils` modules: the
  [DRY section][s44-dry] gains D4–D6 (module-level
  wire serializers with one `_SLOW_QUERY_SECONDS` constant; the
  single-sited collector / two-seam coordinator / log-slice /
  payload-builder inventory; idiom conformance — no `__init__`, the
  optimizer's generator-hook shape, the bounded-walk posture for the
  `original_error` peel, the eager-subpackage export shape, and the
  "database connection" docstring vocabulary) and D-N5–D-N7 (the
  `utils/connections.py` Relay-vocabulary disambiguation with the
  coordinator-placement constraint; the no-utils-import posture with its
  named near-misses; no `exceptions.py` addition), and D-N1 gains the
  sharper ground (at the `0.316.0` floor a ContextVar stash has no shared
  instance left to coordinate). Downstream: Decision 8 records the
  casing-helper rejection and the wire keys as serializer-and-test
  literals; Decision 9 records the bounded-walk conformance; Decisions 5
  and 7 record the export-shape and no-`__init__` / two-seam notes; the
  [Test plan][s44-test-plan] pins the anti-DRY literal rule and the
  seam-targeting rule; [Non-goals][s44-non-goals] records the `conf.py`
  non-surface reason. One review citation was corrected during
  verification: `middleware/__init__.py` deliberately re-exports nothing
  (spec-042's soft-dependency boundary), so the eager-export precedent
  cited is `utils/__init__.py` / `testing/__init__.py`.
- **Revision 5** — second-review reconciliation (2026-07-11). A parallel
  DRY review, written at the same time against the same Revision-3 text,
  was squared with Revision 4's fold-in; its suggested checklist items map
  onto this spec's D3–D6 / D-N5–D-N8 numbering. Genuinely new pins carried
  in: the direct-`CaptureQueriesContext` rejection gains two stronger
  grounds (the process-global `request_started → reset_queries` signal
  toggle — verified at `django/test/utils.py`
  `#"reset_queries_disconnected"` — and the refcount-free single-context
  restore); the coordinator map is keyed by connection object identity,
  never by alias; teardown iterates immutable per-alias snapshot records
  (connection + starting length) and never re-calls `connections.all()` to
  match by position; the collector also guards `errors is None`, preserves
  result-error order, and never speculatively dedups; `get_results` never
  writes `execution_context` or an existing `ExecutionResult.extensions`,
  and the stash's absent sentinel is `None`; D-N6's import list gains
  `graphql`; the new D-N8 rejects the premature abstractions (package base
  extension class, merged row dispatcher, dataclass/Strawberry wire rows,
  per-key constants); D3 gains the named acceptance-reload fixture,
  `create_users`, the one-holder probe-module shape with its
  copy-not-promote ground (`FAKESHOP_SHARDED` gating), and the
  never-sort-the-`extensions=`-list rule; and the Test plan gains the
  real-objects and parametrization rules, the happy-path-only debug
  accessor, the bracket-boundary-only fake (scenario 8), and the
  floor run selected by node id (scenario 13). Where the two reviews
  differed, the reconciliation is recorded in place: the coordinator may
  surface its two seams as methods or as one per-connection context
  manager (the pin is single ownership, not the callable shape), and the
  no-`__init__` rule keeps the first review's default with the second's
  constrained escape (`execution_context` passthrough only, no `**kwargs`
  sink).

- **Revision 6** — round-3 DRY review fold-in (2026-07-11). The review
  confirmed the Revision-4/5 shape (its audit re-ran clean against all
  thirteen `utils/` modules) and required three pins, none a design change:
  [Test plan][s44-test-plan] scenario 2 composes the optimizer through the
  **canonical consumer shape** — one module-local
  `DjangoOptimizerExtension()` singleton returned by `lambda: _optimizer`
  (the shipped [`config/schema.py`][config-schema] wiring, plan cache
  retained) beside the debug **class** entry, with no helper normalizing
  the two deliberately different lifetimes into one factory form; the
  probe module's URLconf **activation** is single-sited in
  [DRY D3][s44-dry] — one module-level
  `pytest.mark.urls(__name__)` application (or one module-wide fixture),
  never per-test `override_settings(ROOT_URLCONF=...)` /
  `clear_url_caches()` blocks; and the no-`__init__` stash sentinel got a
  concrete home in
  [Decision 7][s44-d7]
  — one immutable class-level `_payload = None` default, read directly by
  `get_results` and overridden on the instance only at successful
  teardown.
- **Revision 7** — source-verification correction pass (2026-07-11).
  Corrected seven contracts against Strawberry 0.316.0, Django 6.0.5, and
  asgiref internals: Strawberry constructs extensions with zero arguments and
  assigns `execution_context` afterward; response-extension merging includes
  async context-result precedence and replacement of any pre-existing result
  map; repeated `get_results()` calls are tied to the early-result plus
  teardown-failure recovery path rather than generic recovery; final card wrap
  moves behind the mandatory Slice-3 cut; SQL scope is narrowed to Django's
  `queries_log` and explicitly excludes `callproc()`; async overlap coverage
  pre-materializes and proves shared wrapper identity; and nested same-thread
  sync execution is documented as restoration-safe but cross-attributed.
- **Revision 8** — deep architectural review fold-in (2026-07-11; the
  review's 21 findings applied as one coherent pass, each verified against
  the installed Strawberry 0.316.0, Django 6.0.5, asgiref, and repository
  sources before editing). The five implementation blockers: Test plan
  scenario 2 and Goals item 5 rewritten to the **visibility-safe two-query
  prefetch shape** (`CategoryType.get_queryset` makes the optimizer plan
  `Prefetch`, never a joined single query — the existing
  `test_products_api.py` proof is the assertion precedent); the
  byte-identical / off-by-default overclaim replaced with the narrow
  no-instrumentation/no-key claim plus
  [Decision 6][s44-d6]'s
  release-wide floor **migration notes** (zero-argument construction,
  direct-instance deprecation, per-operation lifecycle; `uv.lock` + tests —
  not the open bound — pin semantics; the stale `optimizer/extension.py`
  `__init__` comment joins the Slice-1 file map); a **two-phase failure
  policy** in [Error shapes][s44-error-shapes] (setup fail-loud after
  `ExitStack` unwind; post-execution diagnostic failures caught as
  `Exception`, logged, degrading the payload — never replacing the real
  result — with the generic-recovery claim qualified to
  stash-published-only); the **cursor-construction capture-interval
  boundary** documented in Decision 4 / Edge cases (Django selects the
  wrapper at `connection.cursor()` time and never re-checks — pre-opened
  and retained cursors are named boundary cases, not fixed by a wrap port);
  and the Slice-3 wrap re-ordered **DB-mutations → Done flip →
  `import_spec_terms` → GLOSSARY/TREE renders → KANBAN renders → `--check`
  modes**, with the glossary flips enumerated from the companion terms CSV.
  Also folded: transaction scope narrowed to brackets completing inside the
  hook (enclosing `ATOMIC_REQUESTS` excluded); a real sharded-tier capture
  proof (scenario 16); experimental incremental execution and
  `inc_thread_sharing()` cross-thread wrappers excluded explicitly;
  sibling-hook SQL ordering documented and tested; the `original_error`
  walk gains a 64-hop ceiling with deterministic stop; the enabled-cost
  language replaced with exact complexity/retention wording; the async
  follow-on's false universal-executor premise corrected
  (`ThreadSensitiveContext` is per-request under ASGI HTTP — a prototype,
  not prose, decides the follow-on); the security disclosure enumerates
  interpolated SQL values, traceback paths, retention, and downstream
  copies; targeted pytest commands gain the coverage-free
  `-o addopts="-v -n0"` override; the Strawberry floor gains a durable CI
  node (`.github/workflows/django.yml` joins the file map); live scenarios
  gain their `django_db` / `django_db(transaction=True)` markers and
  scenario 3 its full permitted-writer + required-`categoryId` setup;
  scenario 13 drops threaded ORM in favor of exception/identity markers;
  and scenarios 17–21 add the non-interference, cursor-lifetime,
  transaction-boundary, sibling-order, and hop-policy regressions. Two
  findings required no spec change, recorded so they are not re-litigated:
  the settings-lookup concern (F12) does not occur — this spec introduces
  no settings key, and the shipped `conf.py` / `types/relay.py` split is
  correct as-is; and the temporary fail-loud stub needs no import-guard
  test (F21) — `pyproject.toml` already excludes `raise
  NotImplementedError` from coverage, so the staged
  `tests/extensions/test_debug.py` guard is deleted rather than kept.

### Which revision changed which decision

Derived from the entries above so a decision's change record is reachable from the decision
rather than only from the chronology. "None" means the decision has stood as Revision 1 wrote it.
**Retracted** marks a claim the decision once made and is no longer permitted to make; the spec
carries only the replacement. Three exist in the chronology — two in the table below, plus the
async follow-on's universal-executor premise under
[Change record for Risks and open questions](#change-record-for-risks-and-open-questions).

| Spec decision | Changed by |
| --- | --- |
| [Decision 1][s44-d1] | none |
| [Decision 2][s44-d2] | none |
| [Decision 3][s44-d3] | Revision 3 — the one deliberate wire migration recorded (`_debug` selection → `response.extensions.debug`) |
| [Decision 4][s44-d4] | Revision 2 — the lock-protected reference-counted flag bracket, and **retracted** the bounded-log clamp *guarantee* in favour of Django's actual best-effort length-snapshot semantics (the replacement is normative in `## Edge cases and constraints` and [DRY D5][s44-dry]); Revision 5 — two stronger grounds against wrapping `CaptureQueriesContext` directly; Revision 8 — the cursor-construction capture-interval boundary |
| [Decision 5][s44-d5] | Revision 4 — the eager-subpackage export shape (and the corrected `middleware/__init__.py` citation) |
| [Decision 6][s44-d6] | Revision 2 — the floor raised to `0.316.0`; Revision 8 — the release-wide migration notes and the durable CI floor node, and **retracted** the byte-identical / off-by-default overclaim in favour of the narrow no-instrumentation / no-`debug`-key claim the spec now states |
| [Decision 7][s44-d7] | Revision 2 — the reference-counted bracket; Revision 4 — the no-`__init__` and two-seam notes; Revision 5 — `get_results` purity and the `None` sentinel; Revision 6 — the immutable class-level `_payload = None` home; Revision 7 — zero-argument construction and the double-`get_results()` recovery path |
| [Decision 8][s44-d8] | Revision 2 — explicit `exc.__traceback__` serialization; Revision 4 — the casing-helper rejection and the wire keys as literals; Revision 7 — SQL scope narrowed to `queries_log`, `callproc()` excluded |
| [Decision 9][s44-d9] | Revision 2 — the nested `original_error` walk; Revision 4 — bounded-walk conformance; Revision 5 — the collector's `errors is None` guard, result-error order, no speculative dedup; Revision 8 — the 64-hop ceiling with a deterministic stop |
| [Decision 10][s44-d10] | none |
| [Decision 11][s44-d11] | Revision 2 — the live/mechanics split itself |
| [Decision 12][s44-d12] | Revision 7 — the final card wrap moved behind the mandatory Slice-3 cut; Revision 8 — the wrap's re-ordered DB-mutations-first sequence |

## Change record for the spec's non-decision sections

Corrections made by this move rather than by a review round, kept here because they belong to no
single decision entry:

- **The header's revision history** was moved in full (above) and replaced by a pointer naming
  this file. The spec is a contract, not a changelog: a reader must never have to reconstruct what
  is currently true by applying a chronology to it.
- **[`## Test plan`][s44-test-plan] carried two labels naming a revision.** The scope line read
  "scenarios 8–15 and the Revision-8 additions 17–21 live in `tests/extensions/test_debug.py`", and
  the group heading read "**Revision-8 additions (16 live-sharded; 17–21 mechanics):**". Both were
  cross-references into the chronology that no longer lives in the spec, so both were reworded to
  name the scenarios instead. The numbering rule they sat beside — "numbering appends rather than
  renumbers so every existing scenario reference stays stable" — is instruction and stayed.
- **Three surviving cross-references cited moved text by list position or by list slot**, and the
  move falsified all three. [Decision 10][s44-d10] said "per Decision 4's **third** alternative"
  when the removal of one bullet left Decision 4 with two; [Decision 9][s44-d9] ground 1 and
  [DRY D-N4][s44-dry] pointed at `Decision 7 alternatives` and `Decision 8's rejected
  alternative`, whose lists moved here in full. All three now name what they cite — the
  `CaptureQueriesContext` rejection, the `resolve`-hook rejection, the casing-helper rejection —
  and the latter two carry a link to this file. A name survives a move and a relocation; an ordinal
  or a bare "alternatives" does not, so none of them should be turned back into one.
- **[`## Helper-reuse obligations (DRY)`][s44-dry] narrated its own provenance twice.** Its preamble
  said the headline was what "two independent, simultaneously-written reviews of the planned module
  against all thirteen `django_strawberry_framework/utils` modules (2026-07-11) reached", and
  obligation D3 introduced its own specifics with "Sharpened by the DRY review:". Both
  attributions moved here; every claim they introduced stayed. The headline itself (`almost nothing
  in utils/ is directly callable from debug.py, and that is the correct outcome, not a gap`), the
  utils-charter reason, and the (a)/(b)/(c) map of where the real DRY work lives are all
  instruction — a builder who never reads them re-derives the wrong reuse. The one thing lost from
  the spec is *who* said it, which changes nothing about what must be built.
- **[DRY D6][s44-dry]'s no-`__init__` escape regained one clause the move had briefly left only in
  the chronology.** Revision 5's reconciliation constrained the escape to "`execution_context`
  passthrough only, no `**kwargs` sink", and that constraint had never been restated in D6 itself —
  so moving the chronology took it out of the spec entirely. It binds a future writer at the site,
  which is the carve-out's own test, so D6's escape now carries it. Revision 5's account above is
  the provenance, not a second copy of the rule.

## Decision entries

### Decision 1 — Spec filename and canonical naming

Spec: [Decision 1][s44-d1]. Authored in Revision 1; unchanged since.

Alternatives considered (and rejected):

- **`spec-044-response_extensions_debug-0_0_14.md`.** Rejected: the long
  slug restates the mechanism twice (`response_extensions` + `debug`); the
  established slug style is short subject-first (`debug_toolbar`,
  `channels_router`, `test_client`).
- **`spec-044-debug_middleware-0_0_14.md`.** Rejected: "middleware" is the
  card title's graphene-inherited word, and the card's own Architectural
  posture disavows it for our shape — naming the file after the rejected
  shape would mislead every future grep.

### Decision 2 — Card-scope boundary: the extension ships alone — no Django middleware, no schema field, no fakeshop always-on wiring

Spec: [Decision 2][s44-d2]. Authored in Revision 1; unchanged since. The three exclusions
themselves are normative and stayed in the spec; what moved is the scope justification behind
them and the one alternative it rejects.

Justification: the card is an M and each excluded piece has its own owner —
the toolbar card is Done, the schema-field exposure is a rejected
alternative, and the fakeshop activation line item already exists on the
beta board. Alternatives considered (and rejected): **bundling a fakeshop
demo field or dev-settings toggle** — rejected as scope creep that turns a
one-module card into an example-project design discussion; the probe-URLconf
tests demonstrate the wiring shape a consumer copies.

### Decision 3 — Exposure: the response-`extensions` map under the `debug` key, not a schema-level `_debug` field

Spec: [Decision 3][s44-d3]. Grounds 1-5 stayed in the spec (they are what a reader needs to
understand the seam being used); the two rejected exposures moved here.

Alternatives considered (and rejected):

- **The graphene schema-level `_debug` field.** Rejected: everything in
  ground 2, plus a mechanism problem — a field resolver cannot know when the
  operation's *other* fields have finished executing, which is why graphene
  needs its promise-chained `get_debug_result()` dance
  ([`middleware.py`][upstream-debug-middleware] `::DjangoDebugContext`); the
  operation hook gets completion for free. The selectivity loss (the map is
  all-or-nothing per enabled schema, where graphene consumers pull only
  `{ _debug { sql } }` per query) is real and recorded in
  [Risks][s44-risks].
- **Both at once.** Rejected: two exposure surfaces for one payload doubles
  the documentation and test matrix for zero new capability; a future card
  can add the field flavor over the same capture core if a consumer asks.

### Decision 4 — Fidelity: Django's own debug cursor via a `force_debug_cursor` bracket, not a cursor-wrap port

Spec: [Decision 4][s44-d4]. **Only the bare-`connection.queries` rejection moved** — one of the
three alternatives Decision 4 originally listed; see
[What deliberately stayed in the spec](#what-deliberately-stayed-in-the-spec-and-why) for why the
cursor-wrap-port rejection and the direct-`CaptureQueriesContext` rejection are instruction rather
than deliberation. The moved bullet is pure redundancy: the trap it names is stated normatively
twice in the spec already, in Decision 4's own body and in `## Current state`. Its closing
"trap above" therefore points at those two statements, which the sentence before this list names.

**Alternative considered (and rejected).**

- **Read bare `connection.queries` without the bracket.** Rejected: the
  `DEBUG=False` silent-empty trap above — a correctness bug dressed as
  simplicity.

### Decision 5 — Symbol and home: `DjangoDebugExtension` in `extensions/debug.py`, exported from the `extensions` subpackage — never the package root

Spec: [Decision 5][s44-d5]. Ground 3's eager-re-export instruction stayed (it is what the
subpackage `__init__.py` must be written as); the three rejected homes moved.

Alternatives considered (and rejected):

- **Package-root export beside `DjangoOptimizerExtension`.** Rejected per
  ground 2 — and the asymmetry is informative rather than confusing: the
  import path itself signals "this one is not part of the default recipe".
- **`optimizer/debug.py`.** Rejected: the debug extension is not optimizer
  machinery (it reports *all* SQL, planned or not) and the card's predicted
  path pins `extensions/`; parking it under `optimizer/` would also block
  the `extensions/` subpackage the target tree already reserves.
- **Naming the module `extensions/debug_extension.py`.** Rejected: the
  subpackage already says `extensions`; `debug.py` matches upstream
  strawberry-django's `middlewares/debug_toolbar.py` leaf-naming style the
  package adopted for `middleware/debug_toolbar.py`.

### Decision 6 — Opt-in shape: pass the class — one fresh instance per operation requires Strawberry 0.316.0

Spec: [Decision 6][s44-d6]. The release/migration notes stayed — they are a doc obligation the
`CHANGELOG.md` and GLOSSARY entries discharge. What moved is the three rejected opt-in shapes,
including the runtime-tripwire alternative whose rejection is the one a future reader is most
likely to re-propose.

Alternatives considered (and rejected):

- **Singleton-in-a-factory, ContextVar state (the optimizer's shape).**
  Rejected: buys nothing (there is no cache to preserve) and costs a
  ContextVar lifecycle with reset-token hygiene — machinery whose only
  consumer would be a usage pattern the docs steer away from anyway.
- **Retain `strawberry-graphql>=0.262.0` and rely on the class form.**
  Rejected: the sync path still caches the resulting instance before 0.316.0;
  class syntax alone does not provide isolation at the old floor.
- **Guard against shared instances at runtime** (e.g. detect a second
  concurrent `on_operation` on one instance and raise). Rejected: the
  engine already owns instance lifecycle and deprecation signaling for the
  bare-instance form; a package-side tripwire would fire only in the
  misuse case it documents away, and false-positive risk (serialized
  sequential operations on one instance are harmless) outweighs the catch.

### Decision 7 — Hook shape: one sync `on_operation` generator, assembly at teardown, `get_results` returns the stash

Spec: [Decision 7][s44-d7]. The two seams, the sentinel's home, and the three grounds stayed.

Alternatives considered (and rejected):

- **Assemble inside `get_results`.** Rejected per ground 2: on the
  early-error paths it would read a bracket that has not restored yet, and
  it would need its own idempotence guard for the paths where the engine
  calls it after teardown anyway.
- **`resolve`-hook accumulation (graphene's mechanism).** Rejected: the
  per-resolver hook exists for per-field concerns; SQL is per-operation and
  exceptions already accumulate on the result. A `resolve` implementation
  would also put the extension on the engine's per-field hot path
  (`_implements_resolve` adds the middleware wrapper) for pure overhead.
- **An `async def on_operation` twin class** for async schemas. Rejected:
  ground 1 makes it unnecessary; the async-color SQL fidelity gap is a
  thread-locality property, not a hook-color property
  ([Edge cases][s44-edge-cases]), so an async hook would not
  close it anyway.

### Decision 8 — The SQL row shape: graphene's wire names, narrowed to what Django's log supports

Spec: [Decision 8][s44-d8]. The six-key table, the named omissions, the exception triple, and the
load-bearing explicit-traceback rule all stayed. Note that the fourth moved bullet — the
casing-helper rejection — is *also* stated as an instruction in the spec's DRY D4 ("the six wire
keys spelled as **literals**") and in the Test plan's independent-literals rule, which is why
moving the argument for it costs the builder nothing.

Alternatives considered (and rejected):

- **snake_case keys** (the Python-side names). Rejected: the payload is
  wire, not Python; a migrant's existing DevTools formatter reads `isSlow`.
- **Carrying `startTime` / `stopTime` measured by the extension around the
  whole operation.** Rejected: per-operation stamps on per-query rows would
  be actively misleading — worse than absent.
- **A `time` string field mirroring Django's raw log entry.** Rejected:
  duplicates `duration` in a worse type; anyone needing Django's exact
  string can reformat.
- **Deriving the camelCase keys through `utils/strings.graphql_camel_name`.**
  Rejected: the six keys are a **wire contract** — a graphene migrant's
  existing DevTools formatter parses these exact bytes — so they must not be
  a function of a casing helper's future acronym/underscore behavior. They
  are spelled as literals inside the one row serializer
  ([DRY D4][s44-dry]), and the mechanics tests
  re-spell them as independent literals for the same reason
  ([Test plan][s44-test-plan]).

### Decision 9 — Exception capture: the result's `original_error` chain, serialized like graphene's `wrap_exception` — no resolver wrapping

Spec: [Decision 9][s44-d9]. The `None`-guard, the doubly-bounded walk, the deterministic stop, and
the LIFO masking dependency stayed.

Alternatives considered (and rejected):

- **A `resolve` hook capturing exceptions per field.** Rejected per
  ground 1.
- **Serializing every outer result `GraphQLError`** (no `original_error`
  gate). Rejected per ground 2 — it would spam the list with validation
  entries the standard `errors` array already carries. This is distinct from
  retaining a terminal `GraphQLError` reached through a non-`None` original
  link, which proves it was raised during resolver execution.
- **Capturing exceptions the resolvers swallowed** (graphene cannot either).
  Out of scope by construction: only errors that reached the result exist
  to report.

### Decision 10 — Multi-database capture: every alias in `connections.all()`, one bracket each

Spec: [Decision 10][s44-d10]. Authored in Revision 1; unchanged since.

Alternatives considered (and rejected): **bracketing only
`connections["default"]`** — rejected, silently blind on sharded setups;
**lazily bracketing on first use via the `connection_created` signal** —
rejected, misses the common case of aliases whose connections already exist
from prior requests, and signal (dis)connection per operation is its own
leak surface.

### Decision 11 — Test strategy: split live HTTP behavior from package-tier mechanics

Spec: [Decision 11][s44-d11]. The placement rule and the live-first application stayed; the three
rejected placements moved.

Alternatives considered (and rejected):

- **Enable the extension in fakeshop's shipped schema so tests go live.**
  Rejected in
  [Decision 2][s44-d2]
  — every acceptance response pays body weight and capture cost, and the
  example stops modeling the off-by-default posture.
- **Put all scenarios in the card's predicted `tests/extensions/` path.**
  Rejected: a live `/graphql/` request belongs to `test_query/` under the
  explicit repository rule. Predicted paths guide planning; they do not
  authorize a placement exception.
- **In-process `schema.execute_sync` instead of HTTP.** Rejected for the
  request-driving group (the card says "request", and HTTP exercises the
  serialization of `extensions` into the response body — JSON round-trip
  included); retained where it is the *point* — the async-color scenario
  drives in-process async execution precisely because Django's async test
  client cannot change the thread-locality story the scenario documents.

### Decision 12 — This card completes the joint `0.0.14` cut and owns the version bump

Spec: [Decision 12][s44-d12]. The quintet, the flips, and the "only in Slice 3" rule stayed.

Alternatives considered (and rejected):

- **Defer to yet another card.** Rejected: no later `0.0.14` card exists; a
  deferral would orphan the cut the three predecessors are waiting on.
- **Bump in Slice 1.** Rejected: the version should move only after the
  feature and docs are complete (the [`spec-038`][spec-038] rule), and a
  Slice-1 bump would publish `0.0.14` identity while `044`'s own surface is
  mid-flight.

## Change record for Risks and open questions

Spec: [Risks and open questions][s44-risks]. Two items moved; the other five risks keep their
preferred-answer / fallback pairs in the spec because instruction cites them.

**Resolved, and therefore no longer a risk — the card's "middleware" word vs. the shipped
shape.** The conflict is settled in the spec's `## Non-goals` first bullet ("A Django (or
Graphene) middleware") and in the spec's own title, so the risk entry was a record of a closed
deliberation. Revision 1 says this conflict "is recorded in Risks rather than silently
reconciled" — that record is the bullet immediately below, which moved here with it:

- **The card's "middleware" word vs. the shipped shape.** The card title
  (and the feature's board name) says middleware; the shipped unit is a
  `SchemaExtension`, per the card's own Architectural posture ("our
  Strawberry-native shape is a `SchemaExtension` (operation-scoped), not a
  Django middleware"). Recorded per the
  [`docs/SPECS/NEXT.md`][next] prefer-the-card rule rather than silently
  reconciled — but the card resolves its own title here, so **preferred
  answer:** ship the extension, keep "Response-extensions debug middleware"
  as the card-facing feature name (the GLOSSARY heading stays, its body
  names the class). **Fallback:** none needed — no reading of the card asks
  for an actual Django middleware.

**Retracted — the async follow-on's false universal premise.** Revision 8's correction to the
"Cross-operation SQL attribution" risk: a claim an earlier draft made and the spec is no longer
permitted to make. It moved as a retraction, and it carries one live obligation for whoever picks
the follow-on up: **decide it against a real ASGI-request prototype, not against prose.** The
spec's surviving fallback sentence ("a per-operation-isolated instrumentation design — worth its
own card if async consumers report gaps") is what remains there.

(An earlier draft's categorical rejection of
routing the bracket through `sync_to_async(thread_sensitive=True)` rested
on a **false universal premise** — that thread-sensitive work always
shares one process-wide thread. That is only asgiref's *fallback*:
Django's ASGI handler wraps each HTTP request in a
`ThreadSensitiveContext`, which selects a per-request single-thread
executor, so worker-thread bracketing **may be viable** for normal ASGI
HTTP inside the inherited request context. It is still not universal —
direct `schema.execute()`, batching, and work escaping that context lack
the per-request executor — so the follow-on must be accepted or rejected
against a **real ASGI-request prototype**, not this spec's prose. v1's
honest "async SQL is typically empty" limitation stands either way.)

<!-- LINK DEFINITIONS -->

<!-- Root -->
[goal]: ../../../GOAL.md
[kanban]: ../../../KANBAN.md

<!-- docs/ -->
[glossary-django-trac-37064]: ../../GLOSSARY.md#django-trac-37064-hardening

<!-- docs/SPECS/ -->
[next]: ../NEXT.md
[s44-d1]: ../spec-044-debug_extension-0_0_14.md#decision-1--spec-filename-and-canonical-naming
[s44-d10]: ../spec-044-debug_extension-0_0_14.md#decision-10--multi-database-capture-every-alias-in-connectionsall-one-bracket-each
[s44-d11]: ../spec-044-debug_extension-0_0_14.md#decision-11--test-strategy-split-live-http-behavior-from-package-tier-mechanics
[s44-d12]: ../spec-044-debug_extension-0_0_14.md#decision-12--this-card-completes-the-joint-0014-cut-and-owns-the-version-bump
[s44-d2]: ../spec-044-debug_extension-0_0_14.md#decision-2--card-scope-boundary-the-extension-ships-alone--no-django-middleware-no-schema-field-no-fakeshop-always-on-wiring
[s44-d3]: ../spec-044-debug_extension-0_0_14.md#decision-3--exposure-the-response-extensions-map-under-the-debug-key-not-a-schema-level-_debug-field
[s44-d4]: ../spec-044-debug_extension-0_0_14.md#decision-4--fidelity-djangos-own-debug-cursor-via-a-force_debug_cursor-bracket-not-a-cursor-wrap-port
[s44-d5]: ../spec-044-debug_extension-0_0_14.md#decision-5--symbol-and-home-djangodebugextension-in-extensionsdebugpy-exported-from-the-extensions-subpackage--never-the-package-root
[s44-d6]: ../spec-044-debug_extension-0_0_14.md#decision-6--opt-in-shape-pass-the-class--one-fresh-instance-per-operation-requires-strawberry-03160
[s44-d7]: ../spec-044-debug_extension-0_0_14.md#decision-7--hook-shape-one-sync-on_operation-generator-assembly-at-teardown-get_results-returns-the-stash
[s44-d8]: ../spec-044-debug_extension-0_0_14.md#decision-8--the-sql-row-shape-graphenes-wire-names-narrowed-to-what-djangos-log-supports
[s44-d9]: ../spec-044-debug_extension-0_0_14.md#decision-9--exception-capture-the-results-original_error-chain-serialized-like-graphenes-wrap_exception--no-resolver-wrapping
[s44-dry]: ../spec-044-debug_extension-0_0_14.md#helper-reuse-obligations-dry
[s44-edge-cases]: ../spec-044-debug_extension-0_0_14.md#edge-cases-and-constraints
[s44-error-shapes]: ../spec-044-debug_extension-0_0_14.md#error-shapes
[s44-non-goals]: ../spec-044-debug_extension-0_0_14.md#non-goals
[s44-risks]: ../spec-044-debug_extension-0_0_14.md#risks-and-open-questions
[s44-test-plan]: ../spec-044-debug_extension-0_0_14.md#test-plan
[spec-038]: ../spec-038-form_mutations-0_0_12.md
[spec-044]: ../spec-044-debug_extension-0_0_14.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->
[config-schema]: ../../../examples/fakeshop/config/schema.py

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
[upstream-cookbook-recipes-schema]: ../../../../django-graphene-filters/examples/cookbook/cookbook/recipes/schema.py
[upstream-cookbook-schema]: ../../../../django-graphene-filters/examples/cookbook/cookbook/schema.py
[upstream-debug-middleware]: ../../../../django-graphene-filters/.venv/lib/python3.14/site-packages/graphene_django/debug/middleware.py
