# System-wide bug hunt

The bug-hunt agentflow. The per-file two-role method it replaces is at
`git show 58114254:docs/bug_hunt/HUNT.md`; section 1 records what that method found and what it
missed. Contracts and a pilot come first, orchestration second. The first deliverable is a
three-scenario pilot specification plus a runner that provably rejects bad evidence. The full
workflow rewrite, generators, dependency groups, and any second profile are built only from what
the pilot earns.

## 1. What the three hunts did

Sources: `docs/bug_hunt/bug_hunt-0_0_13.md`, `bug_hunt-0_0_14.md`, `bug_hunt-0_0_15.md`,
`CHANGELOG.md`, `git log`, `KANBAN.md`, `docs/bug_hunt/pbugs.md`, root `vulns.md`.

### 1.1 Observations (recorded facts)

| | 0.0.13 | 0.0.14 (surviving record) | 0.0.15 |
|---|---|---|---|
| items | 34 checked | 11 of 96 checked, stalled | 96 of 96 |
| items with a `Result: Fixed` line | ~24 | 6 | 52 (+1 recorded in a non-`Result:` line) |
| headline severity grades of fixed items | - | - | 4 High, 27 Medium, 48 Low |
| blocked | 0 | 0 | 0 |
| landed as | 2 commits | 6 scoped commits | 1 commit, 154 files, empty body |

Counting method: one row per checklist item; "fixed items" counts items with a `Result: Fixed`
line; "headline grades" counts every severity token in those lines (an item may carry several, e.g.
`Fixed Low x4`), so the two populations differ by design. `pbugs.md` speaks of 27 verified fixes in
a 0.0.14 run; the surviving 0.0.14 record names a prior run whose progress file was deleted, so the
two numbers describe different runs of the same release. Principle 15 addresses that collision.

- About 45 of the 0.0.15 fixed items share one shape: a hostile or broken *consumer-supplied
  object* (raising `__eq__`/`__iter__`/`__repr__`, a descriptor, a metaclass, a one-shot generator)
  escapes a declaration or schema-construction seam as a raw `TypeError` instead of a typed
  `ConfigurationError`.
- Client-reachable isolation or authorization findings across all three hunts: the
  `utils/querysets.py` Prefetch-over-foreign-model leak (first fix failed open on reverse relations
  without `related_name`), the `mutations/permissions.py` awaitable-truthiness silent allow, the
  `optimizer/_context.py` cross-execution sentinel leak.
- The four-card security program `DONE-046`..`DONE-049` came from a maintainer audit run through
  the builder. Wide-blast-radius contract fixes (`74e8cbe1`, `597dbbb4`) came from the review flow;
  one-rule-two-sites divergences (`f92c1944`, `6500fd3c`) from DRY.
- The 0.0.15 record shows Worker 0 rejecting five submissions whose claimed probes had not run
  (a drafted-never-executed battery, a placeholder-failing scratch file, a concealed fourth failing
  file, a 50,000-depth claim whose probe never reached the scanner, a prose-only analysis). It also
  shows Worker 0 erring: an empty-scope read attributed to a tool error, and a post-closeout
  six-agent review that regraded six items, reverted an undisclosed `utils/__init__.py` export
  removal, and corrected "spec-050 concurrent work" labels on hunks when spec-050 had zero slices
  built.
- The `optimizer/hints.py` containment fix was later superseded by a `nested_fetch` owner fix;
  the earlier item stayed checked.
- Every probe in every hunt ran on one cell: Python 3.14 / Django 6.1 / SQLite / single-DB.
  `pbugs.md` item 11: `utils/relations.py::is_forward_concrete_relation` had 100% coverage,
  survived 39 probes in an item closed `no-bugs`, and was wrong on a push/PR cell.
- `dicta.md` is 0 bytes for all three hunts. `pbugs.md` (20 ranked targets) and root `vulns.md`
  (12 ranked targets, 7 open) were never fed back into a hunt.
- Debris: the 0.0.15 header still reads `Status: in-progress`; `docs/shadow/current/` does not
  exist in the tree so every shadow citation dangles; the generated per-item prompt is one sentence
  while the method lived only in this file; `AGENTS.md` spells the glob `bug_hunt.*.md` while the
  files are `bug_hunt-*.md`.
- Instruments absent from `pyproject.toml`/`uv.lock`/`.github/workflows/`: hypothesis,
  hypothesis-graphql, schemathesis, ruff `S`, bandit, semgrep, CodeQL, any type checker
  (`ANN` enforced, nothing checks), mutation testing beyond the manual-manifest
  `scripts/prove_failability.py`, `pytest-randomly`, `pytest-timeout`, `freezegun`. Push/PR CI runs
  2 of 20 matrix cells; Postgres is dispatch-only; fakeshop settings make `FAKESHOP_PG_DSN` and
  `FAKESHOP_SHARDED` mutually exclusive, so Postgres x multi-DB is never built.

### 1.2 Causal claims (inferences, each with its confidence)

- **The hunt's incentives favor local containment defects.** High confidence: the per-file entry
  point, the "break things" mandate, and the blanket exception rule reward exactly the shape that
  dominates the fix table. This is a property of the rules, not of the agents.
- **The single execution cell hides real defects.** Demonstrated once (item 11 above); the size of
  the class is inferred from `pbugs.md` items 12-15 and 20, not measured.
- **Self-reported evidence is the weak link.** High confidence that it *was* weak: five rejected
  submissions. Low confidence that a third role alone fixes it: Worker 0 caught those five, so the
  record does not show the two-role design failing at detection. What it does show is anchoring
  (the verifier reads the hunter's diagnosis first) and a post-closeout regrade that a fresh
  verifier would plausibly have caught earlier. The fresh-verifier case rests on those two, not on
  the fabrication cases.
- **The uniform sweep is the wrong unit.** High confidence for transaction, authorization,
  pagination, and session bugs, which live in cross-file contracts. Not a reason to make unchanged
  code invisible (principle 7).
- **The historical record is not a controlled comparison of designs.** Any claim that a new
  mechanism would have found more is a hypothesis for the pilot, not a conclusion.

## 2. Design principles

1. **An error-contract table replaces the blanket containment rule.** The old rule "every
   unhandled `TypeError`/`ValueError`/... out of a resolver is a defect, invalid input becomes a
   `FieldError` envelope" is not this package's universal contract. Parse and coercion errors,
   deliberate `GraphQLError` rejections including authorization denials, mutation validation
   envelopes, masked unexpected exceptions under `error_policy.py::ErrorPolicy`, and transport
   rejections have different owners and different promised wire shapes (`docs/README.md`, the
   consumer guide, distinguishes them). The 0.0.15 post-closeout review had to *remove* a bare
   `AttributeError` containment that swallowed a consumer descriptor bug. Rule: before probing a
   boundary, the hunter records the row of the contract table that governs it: boundary, failure
   class, promised wire shape, masking, logging, rollback, and absence of unauthorized effects. An
   unexpected internal exception is a lead to investigate; its Python class alone never justifies
   converting it to `FieldError`, and masking alone never proves the underlying behavior correct.
2. **A property is validated before it can define a fix.** An invented `pascal_case` idempotence property is the
   cautionary case: `utils/strings.py::pascal_case` is documented for snake_case input and
   `pascal_case("PaymentMethod")` is `"Paymentmethod"` by design. A hunter obeying it would
   have changed the implementation to satisfy an invented contract. Rule: every property records,
   before it runs, the authoritative contract (doc or code citation), the valid input domain, the
   transformation, the observable result, an *independent* oracle (querying through the same
   implementation is not one), and known exceptions. The verifier approves the premise, not just
   the rerun. "Bigger document never charges less" must name the charge dimension and ordering;
   cursor round trips must fix schema, order, and key context; filter algebra must state null,
   duplicate, visibility, and ordering semantics. A contract nobody can cite goes to the maintainer
   as a decision, never to a fix.
3. **Per-example state isolation is designed before Hypothesis touches a write path.** pytest-django
   wraps a test in one transaction; Hypothesis runs many examples inside it, so generated writes,
   users, sessions, registry entries, caches, and failed transactions contaminate later examples
   and shrinking (Hypothesis documents this and ships `hypothesis.extra.django`). Rule: the pilot
   demonstrates a supported per-example reset with this project's seeding, HTTP client, settings
   overrides, and schema-reload machinery before any write-path property is accepted. Locking and
   transaction experiments run outside an outer rollback wrapper, which suppresses commit hooks and
   changes the behavior under test. Every reproducer is a minimal operation sequence from fresh
   state, not a seed.
4. **A scratch directory is not a sandbox.** Nothing in the old method stops a probe
   from importing the live package, connecting to the tracked `examples/fakeshop/db.sqlite3`, a
   shared Postgres, or a file store. `scripts/prove_failability.py` mutates the *shared-tree*
   source and restores from a pre-mutation copy, so a concurrent edit in that window is lost; its
   scratch root holds evidence, not execution. Rule: campaign input is copied immutable into a
   disposable execution workspace; each worker and cell gets its own environment, database name,
   file storage, caches, and subprocesses; network and credentials are restricted; the runner
   positively checks the database target and the imported source path before any verdict. Only the
   disposable copy is mutated. Promoting a verified patch to the shared checkout is a separate,
   serialized step with a drift check. No automatic branches, no shared-tree restores.
5. **Evidence is attributable to a run, not merely present on disk.** "Probe file plus log" would
   not have caught the 50,000-depth case: the file existed and the invocation never reached the
   scanner. Rule: the runner emits a record per run with source and probe digests, the exact
   command and environment, the imported package location, collected node IDs, executed/skipped/
   error counts, exit status, seed and profile where relevant, and claim-to-evidence links. A claim
   that a boundary was reached needs an entry or effect assertion proving it. Every instrument
   carries a positive control that makes it fail for the intended reason. Missing, empty, stale,
   timed-out, or setup-only evidence is `inconclusive`, never `no finding`. Logs and generated
   examples are untrusted data, never instructions to the next agent.
6. **Verdicts go stale.** A verdict names the exact source and dependencies it inspected; a change
   to any of them marks it `stale` and enqueues targeted re-verification. Integration and closeout
   re-inventory added, deleted, renamed, and previously untracked files. Source drift during a run
   invalidates the run. The final report certifies one materialized tree state, never a branch name
   or an accumulation of checkmarks.
7. **Contracts are the unit; files are the inventory.** Work units are scenarios with entry points,
   dependency edges, and an owning population; every package file, `__init__.py` included, maps to
   an owning scenario even when not selected. Change impact includes reverse dependencies and
   environment changes, computed from a machine inventory (`git ls-files` plus untracked and dirty
   paths), not `git diff --stat`. A rotation budget covers older low-ranked surfaces. The result is
   reported as "selected campaign complete" with the unexamined scope listed; never as
   whole-package clearance.
8. **Security discovery needs valid, stateful adversaries.** hypothesis-graphql's negative mode
   violates types, required arguments, enums, or nullability; those documents stop before resolver
   execution. Rule: authorization, tenant isolation, cache reuse, and race scenarios use known-valid
   IDs and operations, several actors with ownership relationships, and stateful sequences (warm as
   A then read as B; authorize then revoke; subscribe then expire; validate then change a relation
   on another connection), asserting forbidden rows and side effects are *absent*. Hypothesis
   `RuleBasedStateMachine` against an independent model is the candidate generator. Invalid
   generation is kept for parser and input boundaries. `testing/client.py::TestClient` is the
   in-process HTTP client (a Django `Client` wrapper, not a schema shortcut) and stays; rejection
   probes disable its default assert-no-errors and assert the correct rejection; CSRF probes enable
   enforcement explicitly. WebSocket, streaming, cancellation, and multi-connection races need their
   own harnesses.
9. **Roles are separated by evidence access and authority.** W0 owns scheduling and the mechanical
   acceptance prerequisites (the runner record exists and is well-formed, the scenario's contract
   row is cited, the workspace was isolated). W1 investigates and implements only confirmed,
   authorized fixes. W2 owns substantive verification: it derives the expected behavior from the
   contract and reproducer *before* reading W1's diagnosis where practical, records that
   expectation, then verifies the exact patch. **Passing W0's mechanical checks never implies the
   finding is correct; only W2's verification does.** W0 cannot override a W2 rejection.
   Disagreement about product semantics goes to the maintainer. For selected high-risk scenarios,
   two independent hunters with different lenses (contract and state transitions vs implementation
   and failure paths) work before exchanging results; this is not required for every scenario, and
   extra agents earn their place by unique confirmed findings or stronger rejection of false ones.
10. **Severity is impact-based; no origin floors or caps.** Separate reachability, actor
    prerequisites, likelihood, confidentiality/integrity/availability impact, blast radius, and
    confidence. Developer-robustness defects and security vulnerabilities are distinct categories,
    but a fail-open authorization outcome triggered by a plausible integration mistake is still
    High. Claiming CVSS means supplying the vector and rationale.
11. **Each environment cell states what it can prove.** Scenarios map to axes: interpreter and
    dependency semantics, SQL vendor, database aliasing, optional-dependency presence, sync/async
    transport, process order. The identical minimized reproducer runs on each applicable cell; the
    record lists resolved versions and *executed* tests. Locking and race claims use real separate
    connections and synchronization barriers. Postgres x multi-DB needs fixture and settings work
    first (the modes are mutually exclusive today). An unavailable cell is `unverified`, never
    passed. Pure helpers are not rerun on every vendor.
12. **Mutation testing is a pilot lead, not a per-item tax.** A surviving mutant is a lead about
    test discrimination, never a product defect; equivalent, unexecuted, timed-out, and
    mis-imported mutants are classified separately. mutmut needs explicit test discovery for this
    repo's four test trees and proof of mutated-import provenance and one known killed mutant
    before any survivor list is read. `scripts/prove_failability.py` keeps its purpose: proving the
    regression test detects the actual correction.
13. **Permanent regression dependencies live where CI installs them.** Hypothesis in an optional
    group alongside permanent property tests fails: ordinary CI installs `dev`, so those tests
    would fail collection or be skipped silently. Rule: either a dependency a
    permanent test imports is in `dev` and exercised in CI, or the generator stays in the optional
    campaign and only minimized deterministic regressions are promoted to the suite. Heavy discovery
    tools stay optional. Clean-dev collection and the floor cell are proved when implementation is
    authorized. A Hypothesis profile is registered and loaded in code, not merely named in
    `pytest.ini`.
14. **Static warnings are calibrated before they become policy.** Enabling all of ruff `S` flags
    `S101` on every test assertion; the first step is reporting without gating, then selecting
    reviewed rules with justified exclusions. A rule banning resolver `except` arms without
    `FieldError` conversion inherits principle 1's error; `getattr` outside `utils/canonical.py` is
    not a defect. Custom static rules ship with known-positive and legitimate-negative fixtures. A
    type checker is advertised as catching the awaitable-truthiness class only after it demonstrably
    reports the 0.0.13 `mutations/permissions.py` case on a pre-fix copy. `freezegun` freezes
    monotonic clocks and needs its asyncio option; controlled time is applied at the owned seam and
    real timeout and cancellation behavior is proved with an external watchdog. Seeds, scheduling
    mode, and timeout mechanism are recorded in evidence.
15. **Run identity is separate from release identity.** Two runs of one release collide under both
    `bug_hunt-<release>.md` and any other release-keyed name; the 0.0.14 record already
    describes a deleted predecessor. Rule: unique run id, item id, iteration; an immutable source
    and environment manifest per run; run-owned outputs. Before cleanup the run retains a durable
    bounded bundle: minimal probe, required fixtures, runner record, relevant logs, regression-test
    mapping. Cleanup deletes only enumerated disposable resources the run owns and repairs
    references. Resume validates schema version, inputs, ownership, and evidence; it never trusts a
    `Status:` line alone. `docs/shadow/current/` is regenerable by other tasks and is not immutable
    input.
16. **Leads keep provenance and never become oracles.** Banning historical seeding discards useful
    failure patterns; merging maintainer questions, `pbugs.md`, and root `vulns.md` into one
    required `dicta.md` and deleting the sources overcorrects, because it turns old hypotheses and
    stale `pending` labels into expected results. Rule: maintainer questions stay in `dicta.md`,
    separate from generated or history-derived leads. Each lead carries provenance, contract,
    last-tested tree state, and disposition, and is revalidated on current source. An independent
    discovery pass runs before prior diagnoses are exposed. Every numbered item in `pbugs.md` and
    `vulns.md` is reconciled with an explicit counting method before either file retires;
    `vulns.md` lives at the repository root.
17. **Pilot before infrastructure.** No dependency, generator, artifact, custom rule, or second
    flow is adopted before its benefit is measured. Review mode is read-only;
    fix mode is explicitly authorized. A shipped, sensitive finding gets restricted evidence
    handling and the `SECURITY.md` maintainer path before any reproducer lands in a tracked public
    document; a card plus a failing test is not a parked vulnerability without a named owner and a
    containment step.

## 3. Design

### 3.1 One engine, campaign profiles

One dispatch, evidence, state-machine, verifier, revision, and archive mechanism. Profiles change
the scenario population, the oracles, and the disclosure handling, not the machinery:

- **Correctness:** public API, lifecycle, schema construction, portability across cells, error
  behavior per the contract table, performance budgets.
- **Security:** actor, asset, and trust-boundary model; unauthorized effects; isolation; resource
  exhaustion; disclosure handling. Valid-client attacks and plausible integration misconfiguration
  are in scope. The threat model and the confidential-handling policy are a separate standing
  document; they do not own a second dispatch engine.
- **Change-focused:** changed contracts and their dependency closure plus a rotation slice of
  unchanged coverage.

`BUILD.md` mechanisms (`<scratch>`, floor venv, corpus ratchet, closing record) are linked only
after checking that their source-mutation and role assumptions hold for hunts; `prove_failability.py`
in particular is not reused in a shared tree (principle 4).

### 3.2 Scenario record

Each scenario carries: id; entry points; authoritative contract citations and the governing rows of
the error-contract table; actors; input domain; lifecycle and state; observations and independent
oracle; dependency edges (forward and reverse); applicable cells and what each proves; permitted
tools; exploration budget; owning files.

### 3.3 Lifecycle

`planned -> investigating -> candidate -> reproduced -> fix proposed -> independently verified`

Terminal alternatives: `no finding within scope`, `rejected candidate`, `inconclusive`,
`blocked on authority/environment`. Changed inputs produce `stale` then re-verification. Budget
exhaustion is `inconclusive`, never `no finding`, and never a reason to abandon a confirmed,
authorized root-cause correction. Every unresolved confirmed defect has a named owner.

### 3.4 Agent allocation

Default W0 / W1 / W2 per principle 9. Read-only discovery across disjoint scenarios runs in parallel
in isolated workspaces. Shared-tree promotion is serialized; file-disjoint entry points are not
dependency-disjoint changes. Dual independent hunters only for selected high-risk scenarios.

### 3.5 Instruments: initial use and what each does not establish

| Instrument | Initial use | Does not establish |
|---|---|---|
| Hypothesis | contract-backed pagination and input transformations; then stateful scenarios | a correct oracle, DB isolation, or realistic authorization by itself |
| hypothesis-graphql | valid and invalid document strategies through `TestClient` | tenant semantics, other transports, race behavior |
| `scripts/prove_failability.py` | exact regression discrimination, in an isolated source copy | general discovery; safe shared-tree mutation |
| mutmut | bounded test-discrimination pilot on one module | that a survivor is a bug; declaration-time completeness |
| pyright / selected ruff `S` / semgrep | advisory leads, calibrated on known positives and legitimate negatives | soundness through `Any` or dynamic ORM hooks; a severity score |
| Schemathesis | optional comparison for HTTP transport campaigns (replay, reporting, pytest integration) | domain authorization correctness; OpenAPI-grade stateful support for GraphQL |
| CrossHair | optional later experiment on explicitly contracted pure functions (parsing, window arithmetic) | anything on the ORM path |

A third-party plugin or hosted scanner is an integration choice, not an oracle. Evaluating one later
requires measured additional findings, reproducible exports, bounded permissions, explicit
source-upload approval, and a retention and disclosure policy; agentflow correctness never depends
on a vendor UI or an unreplayable report. No plugin is needed to start the pilot.

## 4. First deliverable: pilot specification and runner rejection cases

Nothing in sections 5 or 6 is built until this deliverable is accepted and the pilot has run.

### 4.1 Three scenarios

Each is specified to the section 3.2 record before any code, with its oracle approved by the
maintainer.

1. **Pagination window semantics.** Entry points: `connection.py`, `keyset.py`,
   `utils/connections.py`, `optimizer/single_parent_fetch.py`. Contract: the Relay window laws the
   consumer guide states, with `UNSET` vs `None` semantics per `74e8cbe1`. Independent oracle: a
   pure-Python model of the window over a materialized ordered list, with a nullable ordering key.
   Cells: SQLite and Postgres (NULL collation differs); floor and latest Django.
2. **Authorization and visibility across actors.** Entry points: `utils/querysets.py` seal,
   `permissions.py`, `filters/sets.py` nested combinators, `relay.py` GlobalID decode. Contract:
   rows outside actor A's `get_queryset` visibility are never returned, counted, filtered on, or
   revealed through existence oracles, for any valid document. Independent oracle: a per-actor
   allowed-row set computed directly from the ORM outside the framework. Stateful sequence: warm
   caches and plans as A, then query as B. Cells: single-DB and sharded SQLite; Postgres.
3. **Transaction or session lifecycle under interruption.** Entry points:
   `utils/write_transaction.py`, `mutations/resolvers.py`, `auth/sessions.py`, `consumers.py`
   revalidation. Contract: the conflict envelope, rollback-on-error, and session invalidation
   promises as documented. Independent oracle: database state read on a second real connection after
   a deterministic interleaving (barrier-synchronized), and session store state. Runs outside any
   outer rollback wrapper. Cells: Postgres for `select_for_update` (a no-op on SQLite); SQLite for
   the lockless conflict path.

### 4.2 Runner rejection cases

The runner (principle 5) is accepted only when each of these produces a non-success verdict with
the correct classification, demonstrated by a fixture:

| Case | Expected verdict |
|---|---|
| probe imports the package from the shared checkout instead of the workspace copy | `invalid: wrong import path` |
| zero tests collected | `inconclusive: nothing executed` |
| setup or fixture failure before the target boundary | `inconclusive: setup-only` |
| timeout | `inconclusive: timed out`, with the watchdog record |
| an applicable cell unavailable | that cell `unverified`; run not `passed` |
| source digest changed between manifest and execution | `invalid: stale source` |
| known-failing positive control passes | `invalid: instrument` |
| probe connects to a database other than the workspace's | `invalid: database target` |
| evidence record missing a claim's link | `inconclusive` for that claim |

### 4.3 Comparison protocol

- Matched inputs and budgets: the old per-file method and this method each run the three
  scenarios.
- Sensitivity: historical pre-fix trees for the three client-reachable findings in section 1.1 are
  materialized in disposable copies; hunters are not shown the old diagnosis. Rediscovery measures
  sensitivity, not new yield.
- Current-source exploration on the three scenarios measures new yield.
- Metrics: unique confirmed root causes; false positives rejected by W2; severity and reachability
  mix; time to minimal reproducer; W1/W2 disagreement rate; agent and execution cost; evidence
  replay success rate. Test count, log volume, mutant count, and Low-finding count are not metrics.
- Acceptance: replayable evidence for every claim, at least one bad oracle or instrument correctly
  rejected, no shared-state damage, and a detection benefit justified against cost. A quiet run
  proves neither tool ineffectiveness nor package safety.

## 5. Built only from pilot results

- The full workflow text replacing sections 4-6 of this file, the scenario-record template, the
  generator and its tests, `START.md` and `AGENTS.md` references, cleanup and link rules, all in
  one change; active records migrated explicitly, historical runs never overwritten.
- Dependency and CI placement per principle 13, decided by whether generated tests stay permanent
  or reduce to deterministic regressions.
- The security profile's standing threat-model document and its confidential-handling policy.
- Instrument adoption per the section 3.5 table, each with its calibration fixtures.
- Debris fixes from section 1.1 (status closeout, shadow regeneration or removal, glob spelling,
  generator role text).

## 6. Recommended maintainer decisions

1. One engine with correctness and security profiles, threat-model content separate.
2. Fresh W2 verifier with authority as in principle 9; independent parallel hunters reserved for
   high-risk scenarios.
3. Isolated runner and the three-scenario pilot approved before any workflow rewrite.
4. Hypothesis through the existing HTTP client first; hypothesis-graphql evaluated inside the
   pilot; every other tool advisory or optional until demonstrated useful.
5. Permanent regression dependencies in ordinary CI; heavy discovery opt-in.
6. Severity impact-based; disputed contracts resolved by the maintainer before any edit.
7. Which Postgres a pilot workspace may use, and whether sharded x Postgres fixture work is in the
   pilot's scope or deferred.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
