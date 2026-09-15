# Review: the DRY condenser design

## Verdict and the vision

Yes. I understand the purpose: **make a change to one piece of knowledge propagate through the
system by construction, instead of relying on the next developer or agent to remember every copy.**
The desired result is not a bag of small helpers. It is a smaller, more expressive program in which
declarations describe the variations and shared machinery owns their meaning.

The settings example demonstrates this particularly well. The interesting achievement is not that
a loop saves some HTML. A model declaration supplies enough information for the UI to discover a
setting, place it, label it, choose an input, and save it without another hand-maintained screen.
That removes an entire category of synchronized edits. The endpoint records and generic fetch
driver demonstrate the same idea at a different boundary.

That is exactly relevant to a Meta-driven framework. Its implementation should embody the same
economy it promises consumers. Adding a supported variation should usually extend an existing
description, not commission another implementation of the surrounding lifecycle.

The position among the major documents should be:

- [GOAL][goal] defines the destination; [TODAY][today] states the current capability boundary;
  [KANBAN][kanban] schedules delivery and acceptance.
- [AGENTS][agents] governs work; [START][start] maps the repository and its mechanisms.
- [The consumer guide][guide], [glossary][glossary], and [tree][tree] explain use, contracts, and
  ownership. [CHANGELOG][changelog] records releases; [BACKLOG][backlog] holds uncommitted ideas.
- Spec authoring and the builder must use DRY's design principles before creating another owner.
  Review and bug hunt challenge correctness. A dedicated DRY run challenges whether the current
  representation, machinery, or branch needs to exist, and consolidates what does.

DRY is therefore both a **construction discipline** and a **consolidation flow**. Its principles
should influence the other flows without automatically starting a DRY cycle, granting new scope,
or becoming another copy of their dispatch instructions.

[The prototype][proto] is a substantial improvement in direction: explicit target forms, rule-first
investigation, ownership records, and keeping the speculative consumer Rule system outside this
refactor are all sound. But it is not ready to become standing instructions verbatim. Several of
its absolutes would train agents to remove valuable distinctions or to produce more convincing
paperwork rather than better code.

## Findings

### 1. High — distinguish one rule owner from one enforcement site and one oracle

Locations: prototype sections 1, 4.6, 7.3, and question 4; current DRY's single-edit-site test.

The proposed tests/docs row says to cite the owner and never restate the rule. The retained test
says that any change requiring more than one site is duplication. Together, these classify an
independent regression expectation as an ownership defect.

A test that expects the public spelling `iContains` must not obtain its expected spelling from
`django_strawberry_framework/filters/inputs.py::LOOKUP_NAME_MAP`. An accidental change to that map
should fail the test, not update its oracle. Likewise, a live request test must establish that an
adapter actually invokes a shared permission policy; coverage of the policy alone cannot do that.

Separate the inventory into:

- **authoritative definitions** — independently maintained implementations or declarations of the rule;
- **consumers/enforcement sites** — invoke or derive from that definition at the necessary boundary;
- **independent oracles** — externally specified expectations that can contradict a broken owner;
- **explanations and generated projections** — describe or render the contract without owning it.

The desired multiplicity of authoritative definitions is one. The other populations need not be
one. An intentional contract change can legitimately change production, tests, and documentation.
That is not the same problem as fixing four independent implementations.

Replace “consolidation deletes tests as well as code” with a conditional obligation: remove tests
of deleted internals when their distinct behaviors have demonstrably survived, and retain each
necessary boundary test at the repository-mandated tier. The existing DRY text already protects
intentional test repetition; do not lose that qualification when lifting the slogan.

### 2. High — the proposed ladder cannot determine a valid owner

Locations: prototype sections 4.7, 7.1, and 7.3; whitepaper placement drafts.

A constant, a function, and a module are not successively higher architectural layers. A function
can live in a transport module and legitimately own a transport-only rule. A data table can belong
to a flavor-specific adapter. Moving either into shared utilities can make ownership worse.

Nor does a rule's read footprint determine its owner. Lifetime, authority, effects, permitted
dependencies, ordering, and framework execution constraints also matter. A request-specific access
decision and a schema-construction shape check can read similarly shaped objects while having
entirely different valid owners.

Replace the numbered ladder with an ownership decision:

1. State the contract and its actual consumers.
2. Record inputs, effects, lifetime, and enforcement authority.
3. Prefer an existing owner with that responsibility.
4. Otherwise choose the narrowest cohesive owner all legitimate consumers may depend on, without
   reversing dependencies or importing a sibling flavor merely to reuse its machinery.
5. Preserve distinct decisions at the adapters; share only the mechanism genuinely common to them.

“Lowest valid owner” is useful shorthand after these conditions are defined. It is not a
mechanical answer supplied by the number of fields a function reads.

### 3. High — splitting predicates is not automatically behavior-preserving

Locations: prototype section 7.1, “a rule whose conjuncts have different floors is split”; the
whitepaper's expired-discount example.

The earlier AI drafts provide a particularly important counterexample: a discount being unexpired
is an eligibility condition at a time, not necessarily an invariant that every stored discount
must satisfy forever. Expired discounts may legitimately remain as historical data. Moving the
condition to a database CHECK changes its meaning, and time passing does not trigger a row check.
PostgreSQL documents the immutability assumption and insert/update evaluation of CHECK constraints.
[PostgreSQL constraint documentation][pg-constraints]

Similarly, `NOT NULL` is not a complete translation of “title required” if that means non-empty
text, and defining `Model.clean()` does not ensure every `save()` invokes it. Django explicitly
documents that `full_clean()` is not called automatically by `save()`.
[Django model validation documentation][django-validation]

For the package flow, require equivalence of observable behavior, not just Boolean truth on a
happy input: short-circuit order, exceptions, query effects, transaction boundaries, cancellation,
and the point at which actor/time/state are observed. Extracting a predicate must not hoist its
evaluation out of the boundary that makes it valid.

The useful whitepaper seed survives: compose explicitly owned rules. The stronger claims that
free variables uniquely determine placement, or that factorization itself proves a safe rewrite,
do not. Treat the drafts' novelty and mathematical guarantees as research hypotheses, not established
foundations for instructions an agent will execute.

### 4. High — “derive once and store” needs an explicit lifetime

Location: prototype section 4.4 and its `_filters` example.

One implementation of a derivation is desirable. One cached result for all contexts is not.
Schema metadata, request permissions, database-alias selection, and transaction state have
different validity periods. A shared derivation must still run again when its inputs change.

The exemplar itself distinguishes these concepts: `get()` replaces `_filters` on each invocation,
whereas `cache.filters` is initialized separately. `_filters` is the normalized requested query;
it can describe a cache hit without a new request being sent. Calling it the query “actually sent”
is too strong, particularly while a new request is pending or after a failure.

Add to every stateful consolidation: who owns the value, its validity key, when it is published,
who may mutate it, and when it is invalidated or discarded. For a pure derivation, this can simply
say “not cached.” Never turn an anti-duplication rule into a requirement for new shared state.

### 5. High — the generic driver needs a closed contract, not unlimited permissiveness

Locations: prototype sections 4.1, 4.3, 4.5, and section 8's constructive instructions.

“Adding a member adds a record, never a method,” “prefer a no-op,” and “make yourself the second
caller” are too absolute. They invite agents to invent a generic engine before proving a second
real use, or to represent an unsupported case as a successful no-op.

Distinguish **another member of a supported family** from **a new semantic capability**. Adding a
setting of an existing supported kind should be declarative. Adding a fundamentally new kind may
properly extend the driver once, with explicit validation and tests. An absent permission hook
cannot automatically mean the same thing as an optional presentation hook.

The exemplar's URL-specific post-processing also remains inside `get()`: settings pairing,
schedule grouping, and dashboard follow-up requests. That is a common pipeline with local dispatch,
not yet a generic named hook supplied by the endpoint record. A record-bound callback is one
possible improvement; it is not something the current files already demonstrate.

The package translation should specify validated records, explicit defaults, supported variants,
and a loud unsupported-case path. Share lifecycle orchestration; let genuinely different work live
in named adapters. Neither “always eliminate branches” nor “always add hooks” is the principle.

### 6. High — the grammar is valuable, but the draft blesses hidden coupling as its ideal form

Locations: prototype sections 3.3, 3.4, 3.10, and 4.2.

The settings design successfully makes UI structure data-driven. However, its current grammar
also mixes display prose with structural identifiers. `settings.html #"pairSettings(fields)"`
splits labels on ` - `, identifies child-like labels through underscores, and suppresses labels
containing specific product words. `settings.html #"fields(key, int = false)"` uses substring
matching, while `settings.html #"isChildOf(fieldKey, parentKey)"` uses an exact parent-prefix test.
These are already two interpretations of the relationship grammar.

For example, a parent key `enable_chat` can substring-match a child labeled for a hypothetical
`enable_chat_extra` parent in `fields()`, while the exact boolean-child matcher distinguishes them.
A display-label rewrite can also change grouping without touching a field's behavior.

Keep the achievement; improve the formulation: declare structural relationships once using stable
identifiers, parse/validate once, and render from that representation. Display wording need not
serve as the structural protocol. Validate missing parents, unsupported kinds, ambiguous names,
and cycles rather than silently hiding controls.

“No translation table” is not a universal virtue. The prototype correctly cites
`LOOKUP_NAME_MAP`, which is precisely a useful authoritative mapping between different naming
conventions. The target is **one owned translation**, not the absence of translation.

### 7. High — `rule.js` is an enforcement attempt, not proof that copies cannot drift

Location: prototype sections 3.8 and 4.8.

The actual matcher in `rule.js #"Program(node)"` compares trimmed lines, recognizes a block with
`includes`, and counts matches in `total_found`. It does not establish that each required block
identity appeared exactly once. If one one-line block is absent and another valid one-line block
appears twice, the total can still equal `jss.length`. The `passed` array is printed, not used to
enforce unique coverage. A matching start near EOF can also reach `.trim()` on a missing line.

Thus “every copy is proven against it” overstates this checker. It also covers selected text
regions only, and the external file list and HTML-processing configuration are absent here; I
cannot verify the population actually linted or whether this rule was enabled when drift occurred.

If this enforcement pattern is carried over, require an independently enumerated population,
per-region identity/cardinality, rejected parse failures, and controls for a missing region,
duplicated region, truncated region, renamed entry, and omitted file. A passing count is not a
proof of completeness. These are proposed validation cases, not tests I ran in this review.

The premise “inline template JavaScript cannot import a shared module” is also false as a general
language constraint: an inline `script type="module"` can import JavaScript modules.
[MDN JavaScript module documentation][js-modules]
These files also already use shared scripts and `sweetAlertMixin`. Specific deployment constraints
may prevent a particular extraction, but they must be demonstrated. Prefer a real shared source;
if physical copies are necessary, generate or check them from one owner under a verified scope.

### 8. Medium — rule-first investigation should replace the work unit, not the source census

Locations: prototype sections 5.2, 8.4, and question 2.

The current flow explicitly says that its file target is only an entry point and its search is
system-wide. Describing it as a reviewer correctly finding no duplication “within the file”
misrepresents the written instructions. The more defensible criticism is that file-sized dispatch
encourages repeated local reasoning and expensive rediscovery despite that instruction.

Switch the actionable unit to a responsibility family, but retain an exhaustive source inventory
as the coverage backstop. Otherwise agents can pick familiar names, prove those single-owned,
and never discover a lifecycle or rule absent from their vocabulary.

Build a lightweight responsibility index while investigating: associate source areas with named
rule families, track unresolved areas, and audit the unassigned remainder. Allow discovery and
consolidation in the same cycle. A mandatory catalog-only first cycle would repeat the current
problem of extensive preparation without demonstrated implementation benefit.

### 9. Medium — the historical yield supports concern, not the claimed causal conclusion

Location: prototype section 5.3.

The 0.0.11 closeout explicitly records no source/test changes. The 0.0.12 plan was generated from
builder artifacts and even contains sections titled “Existing patterns reused”; those are not
equivalent to fresh consolidation opportunities. The 0.0.13 checklist lacks enough retained
outcome evidence to establish zero implementation yield. The 0.0.14 plan is incomplete; the plan
alone establishes an unfinished run, not why it stopped.

These runs also do not all evaluate today's procedure. Git history dates the current probing-matrix
addition to `0bcc92fb` on 2026-08-23; the 0.0.13 plan was generated on 2026-07-12, and the 0.0.12
plan on 2026-06-24. Worker roles and test-authorization instructions changed between them.

Say: **the surviving records do not demonstrate sustained consolidation yield, and their
comparability and evidence retention are inadequate.** File-first dispatch and weak target-form
instruction are plausible contributors, not proven causes. This is enough justification to improve
the method without overstating the retrospective.

### 10. Medium — a multiplicity gate is easy to satisfy without reducing maintenance risk

Locations: prototype sections 7.1 and 8.6; current DRY's single-edit-site test.

“Max multiplicity is one” is meaningful only for an explicitly identified population of rules.
Agents choose rule names and boundaries; they can split one duplicated responsibility into two
names, call a large pipeline one rule, or prove one trivial constant single-owned while overlooking
the important candidates. One hypothetical change with one edit site is not proof of independence.
Two authorization decisions may happen to agree today yet have separate future reasons to change.

Keep the change thought experiment, but exercise the shared rule and its important variation axes.
Count definitions separately from call sites, oracles, and generated output. Report named
before/after ownership reductions, eliminated machinery, remaining candidates, and newly introduced
coupling. A zero-edit result needs credible coverage and rejected-candidate evidence, not a token
single-owned rule as admission ticket.

Treat the 20% line reduction as a hypothesis worth investigating, not a quota or a gate. Measure
net source reduction over a fixed baseline and population, including added drivers, tables, and
adapters; do not claim savings merely by relocating code or deleting independent tests. A real
reduction in change obligations may initially add some lines. The point is not to excuse bloat,
but to make the measurement reward the thing you actually want.

### 11. Medium — sync/async unification needs case-by-case execution contracts

Locations: prototype sections 4.5, 4.6, and question 5.

An async function is not inherently a duplicated sync function, and a count of `async def` is not
the duplication population. Sharing pure decisions is often straightforward; sharing orchestration
requires preserving await points, cancellation, thread affinity, ORM execution, and cleanup.

Inventory actual paired responsibilities. Classify each as a shared pure computation, a common
orchestration with execution adapters, or genuinely distinct execution machinery. Choose the
smallest design that preserves the contract; do not predetermine a generator, pipeline object, or
sync wrapper for the entire package. Verify each entry path still reaches the owner and preserves
its execution-specific obligations.

### 12. Medium — retention, freshness, and authorization need concrete closure rules

Locations: prototype sections 8.5, 8.9, and 10.3; existing DRY workers and planner.

The proposal correctly asks for retained evidence and fewer repeated instructions, but leaves the
operational contract underspecified:

- Release-only plan names collide with another run of the same release; existing item artifact
  names have no run identity either. Separate run identity from package version, which is now
  single-sourced in `__init__.py`, not a second matching literal in `pyproject.toml`.
- `worker-0.md` uses `git stash create` as a baseline. Although this does not perform a destructive
  stash push, it does not capture untracked source. HEAD alone likewise does not represent this
  concurrently dirty checkout. Include relevant tracked and untracked bytes, inputs, and scope.
- A verification becomes stale when its inspected inputs change. Define which change reopens a
  responsibility family and which invalidates the final integration result.
- A rejected-candidate register must carry the concrete contract difference and a reconsideration
  trigger. “Reviewed once” must not make a decision permanent after its evidence changes.
- Preserve a compact durable outcome and evidence references before deleting only this run's
  explicit scratch paths. Broad scratch cleanup can erase another run's evidence.
- Keep static-reviewed, execution-deferred, and execution-verified distinguishable. The canonical
  flow requires explicit pytest authorization; worker prose must not convert dispatch into that
  authorization. Any source-mutation proof needs an isolated workspace, not restore-over-concurrent
  source editing.

These are a small shared execution contract, not a reason to build another orchestration platform.
Keep author/verifier separation. Reviewing this flow does not itself invoke its workers.

### 13. Medium — constructive integration already exists; consolidate it rather than duplicate it

Locations: prototype section 5.2 item 6 and question 8.

The absence of a direct DRY.md reading requirement is real, but “no constructive half” overstates
the repository-wide gap. `docs/builder/worker-2.md` already has “DRY implementation rules”: look
for the existing owner before adding logic, consider shared responsibilities and repeated literals,
and reject extraction that reduces readability. BUILD's opening also makes DRY a build-time duty.

Have DRY own the sharper design principles and let planner, implementer, and reviewer link to that
section, each adding only its role-specific obligation. Reading design principles must not mean
running the whole consolidation flow during every slice. This is also a test of the refactor's
own thesis: replace repeated policy, do not append another authoritative version.

### 14. Medium — correct the exemplar and tooling claims before using them as foundations

Locations: prototype sections 3.1–3.2, 7.4, and pickup notes.

- `optimizer/plans.py::resolver_key` builds a branch-sensitive string from type, field, and runtime
  path. It is not the printed-AST plan-cache canonicalizer. Document printing lives at
  `django_strawberry_framework/optimizer/extension.py::_print_operation_with_reachable_fragments`.
  Neither establishes semantic predicate equivalence; shared technique is not a ready rule engine.
- `docs/dry/export_dry_review.py::_function_fingerprint` hashes a docstring-stripped AST body and
  distinguishes sync/async node kinds. It does not normalize variable names or prove equivalent
  responsibilities. `::check_review` checks textual mentions of symbols/topics, not the substance
  of their review. The draft mostly acknowledges this; retain that limit in every gate description.
- The boot loops express the same algorithm, but settings uses `function (api_obj)` and the other
  three use an arrow function. “Identical” should mean behavior here, not verbatim text.
- The page-reset condition checks page equality; it does not establish that the other filters
  changed. Describe the actual condition instead of supplying an unimplemented predicate.
- `whitepaper.md` is tracked in this checkout. The pickup note calling it untracked is stale.
- The exemplar files establish current differences, not who introduced each one or whether every
  difference is wrong. Attribute their common origin to the maintainer's account; verify endpoint
  contracts before standardizing search thresholds, date formats, or request cancellation scope.

In particular, mapping's `course_objectives` and `session_objectives` records share a URL, while
the driver indexes cancellation by URL. That is a concrete reason a future consolidation must
decide whether request ownership is per endpoint URL or per independent consumer. Uniform text
alone cannot answer the contract question.

## Answers to the prototype's nine questions

1. **Line count:** useful secondary evidence under a fixed scope, not the correctness criterion.
   Primary evidence is fewer independently maintained decisions and simpler ownership.
2. **Rule-first without a catalog:** yes, with a source-inventory backstop and an index built during
   real investigations. Do not require a no-consolidation reconnaissance cycle.
3. **Placement ladder:** reject this total ordering. Use responsibility, dependencies, effects,
   authority, and lifetime to choose a valid owner.
4. **Tests as sites:** inventory them, but separate independent oracles from duplicated production
   definitions. Keep real boundary coverage and mandated placement.
5. **Sync/async shape:** no universal answer. Share semantic decisions first; preserve execution
   machinery unless equivalence supports a common driver.
6. **Rule record:** useful when it supports a decision. Prefer “contract + variation; sites + roles;
   owner + lifetime; migration; evidence + freshness.” Add fields only when applicable; do not
   manufacture a formal catalog of every local expression.
7. **Role files and size ratchet:** keep tiny role deltas if they improve dispatch; otherwise fold
   them. Either way, one canonical procedure. Measure the entire instruction corpus before/after
   and name what was subsumed, not merely the size of DRY.md.
8. **Builder implementer required reading:** yes, the design-principles section, also read by the
   planner. Replace corresponding restatements in role files with pointers.
9. **Opening example:** use a maintained package example, not a table whose evidence disappears
   with temporary files. Keep the four-copy drift story as motivation in these working notes.

## A concrete shape worth teaching

Use `django_strawberry_framework/sets_mixins.py::SetLifecycleAttrs` as a small worked example,
not a blanket endorsement of every abstraction in that module. A family declares the names of
its owner/cache/guard slots once; `binding_attrs` derives the reset population, including `extra`.
The construction and clearing paths can then agree without independently spelling their slot sets.

Show three things in the future document:

1. **Before:** expansion and reset each maintain their own list of lifecycle attributes.
2. **After:** one family record owns the names; the shared lifecycle consumes that record.
3. **Change challenge:** add a family-specific cached slot. Only the declaration gains its identity;
   generic reset code discovers it, while an independent regression test proves reset actually
   removes its state. A supported new family should not copy the lifecycle body.

Pair it with one intentional separation: a field's `"__all__"` lookup expansion and a model's
top-level `"__all__"` field selection share a token but not a contract, as
`django_strawberry_framework/filters/sets.py` documents. This teaches creative compression and the
boundary of that compression in a few paragraphs.

The resulting DRY.md can be compact: purpose and owner distinctions; the worked example and design
idioms; responsibility-first discovery with a coverage backstop; consolidation and verification;
thin cycle mechanics and closeout. Do not retain problematic slogans verbatim merely because the
current file already contains them. A new dependency, DSL, numerical enforcement setting, or
formal proof engine is not a prerequisite for this refactor.

## Bottom line

The direction is right: **reduce the number of independently maintained decisions, and make the
remaining decisions more expressive.** That captures the powerful part of the examples more
accurately than “everything must be a record” or “all rules must live lower.”

The biggest improvement now is to turn the intuition into instructions that distinguish an owned
rule from its necessary adapters, enforcement points, state instances, and independent proofs.
Otherwise an agent can satisfy the prose while making the system less trustworthy. With those
distinctions, DRY can become the condenser you intend rather than another review checklist.

## Review scope and validation

Reviewed the prototype and whitepaper, current DRY flow and worker instructions, exemplar settings
model/template and the four pages' fetching/declaration patterns, the text checker, historical DRY
records and relevant history, builder integration, and selected package owners cited above. This is
a design review, not an exhaustive bug hunt of the temporary frontend application or a proof of
every package census candidate. External documentation was consulted for the specific platform
claims linked above. No frontend application, package tests, or mutation experiments were run.
No implementation, flow, board, or temporary exemplar changes are part of this review.

<!-- LINK DEFINITIONS -->

<!-- Root -->
[agents]: ../AGENTS.md
[backlog]: ../BACKLOG.md
[changelog]: ../CHANGELOG.md
[goal]: ../GOAL.md
[kanban]: ../KANBAN.md
[proto]: ../proto_dry.md
[start]: ../START.md
[today]: ../TODAY.md

<!-- docs/ -->
[glossary]: GLOSSARY.md
[guide]: README.md
[tree]: TREE.md

<!-- docs/SPECS/ -->

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
[django-validation]: https://docs.djangoproject.com/en/5.2/ref/models/instances/#validating-objects
[js-modules]: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Modules
[pg-constraints]: https://www.postgresql.org/docs/current/ddl-constraints.html#DDL-CONSTRAINTS-CHECK-CONSTRAINTS
