# Package build plan: rich_schema_architecture / 0.0.4 (009)

Spec source: `docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md` (**already archived** — the spec sits at its post-archive path, its `-terms.csv` and `-rationale.md` companions at `docs/SPECS/appx/`, and `SpecDoc.path` already reads the archived path; item R3 verifies rather than performs the move)
Target release: `0.0.4` (**shipped long ago** — card `DONE-009-0.0.4`; the package is at `0.0.14` in `pyproject.toml`)
Date created: 2026-08-15
Build rule: one item at a time. Plan first, build second, review third, reconcile fourth.
DRY rule: every item must justify shared/duplicated patterns before merging. A fact told twice across the spec and its rationale sibling goes stale in one of them — the rationale carries the deliberation, the spec carries the contract, and neither restates the other. This cycle inherits `## The single-ownership law` from the spec-008 cycle, which extends the same rule ACROSS specs and standing docs.
Ownership partition: none; sequential residual items. Declared explicitly rather than omitted (`worker-0.md` `### Ownership partition`) so an interrupted item's output stays attributable against a tree several concurrent sessions are also writing. The writable sets are disjoint (R1 writes the spec + its rationale; R2 writes nothing outside the artifact unless the maintainer's escalation answer widens it; R3 writes nothing), but the items are **not** dispatched concurrently: R2 consumes R1's output and R3 audits both.
Hot-path declaration: none. No item touches an executable line — see `## Build-wide context flags`.
Floor-verification scope: none. No item changes package behavior at any version, so a floor run could not distinguish pass from fail. Declared deliberately with the reason stated (`BUILD.md` `## Floor verification` `### When it is required`), not omitted. If any item turns out to require a source edit, it re-loops with floor scope declared.
Pre-flight: passed on 2026-08-15 with three recorded deviations (below); baseline: 28 tracked-modified / 13 untracked entries, every one attributable to a concurrently-running REVIEW cycle or a package-source session — see `## Baseline-dirty out-of-scope files`; cleanup: **nothing deleted** (Deviations 1 and 2), every path this plan creates verified absent.

## This is the SECOND residual cycle on spec-009, and its subject is the code

The first spec-009 reconciliation already ran and is committed at `f3c94642` ("docs(specs): reconcile spec-009 and spec-010, and give each a rationale companion"). It discharged the deferral the spec-008 cycle opened at its `#### Maintainer decision 6`, and it produced `docs/SPECS/appx/spec-009-rich_schema_architecture-0_0_4-rationale.md`.

**So the maintainer's framing for this cycle — "the rationale was not done" — is factually superseded, and the gap it points at is real but sits elsewhere.** The rationale exists and is well formed; what it records is six *documentation-level* corrections, each keyed to a spec section:

- `### Layer 3: Finalization trigger` — the rejected auto-trigger mechanism, stated as preferred
- `### Decision 2: explicit package finalizer` — the same falsification in one clause
- `## Open questions` — two answers falsified, one settled by shipping
- `## Current local package baseline` → `## The 0.0.4 local package baseline`
- `### Status: deferred design idea, no card yet` → `### The unresolved-relation contract is error-only`
- `## Migration path from current package` → `## Migration path from the 0.0.4 baseline`

Every one of those is about a claim the spec makes concerning **finalization** or **its own framing**. **Not one of them audits Layers 4 through 11 against shipped code.** That audit is this cycle's subject, and it is exactly the maintainer's stated goal:

> the goal is make sure the code didn't deviate or drop or we just forget to implement a feature from what was planned in the spec, and then make sure that if later on they were implemented or changed to optimize for later features, thats fine, but the spec should then also be updated to reflect that.

### Residual scope (this cycle's actual work)

**This list grew as the maintainer widened the cycle three times** (decisions 3, 4, and 5). It is the authoritative item list; `## Checklist` is its checkbox form.

- **R1 — reconcile the spec's layer/decision/phase claims with what the code actually does**, and record every correction's reasoning in the existing rationale file (append-only during the cycle, per `worker-1.md` `### Performing the rationale move` rule 4). Worker 1 is the only role that may edit either file. **CLOSED `final-accepted`.**
- **R1b — clause-by-clause mechanism sweep of the whole spec**, not only this cycle's additions (`### Maintainer decision 4`).
- **R1c — promote the async `SyncMisuseError` row to a permanent test** (`### Maintainer decision 5`). The cycle's only code-writing item.
- **R2 — reconcile `spec-028` `### Decision 12`** and its echo sites, the orphaned `DISTINCT ON` deferral (`### Maintainer decision 3`, site 2).
- **R3 — fix card `TODO-BETA-054-0.1.1`'s two stale `DjangoModelField` / BACKLOG-item-38 references in the kanban DB and regenerate** (`### Maintainer decision 3` site 3, `### Maintainer decision 6`).
- **R4 — finish the documentation obligations and audit the archive** in all three cross-reference directions, in the kanban DB, and in the terms-CSV chain; run the `TODO(spec-009` / `TODO-<MILESTONE>-009` staged-anchor sweep.
- **Final test-run gate.**

**"Make sure the code is correct" is a read-only audit obligation.** Worker 0 discharges the verification half before any dispatch (`worker-0.md` `## Scope`: never dispatch a worker at an unverified finding). **No source file, test file, or example file is writable in this cycle** unless the maintainer's answer to an escalation below widens it. If any pass finds a genuine correctness defect in shipped source, it is recorded as a finding and escalated — it does not become a source edit inside a documentation cycle.

## The verification pass — findings

*(Worker 0, 2026-08-15, read-only against the working tree. Every row carries symbol-qualified evidence per `AGENTS.md` rule 27; no row cites a line number.)*

**Method.** A layer-by-layer sweep read the spec in full and verified each claim against `django_strawberry_framework/`, then Worker 0 independently re-derived the four highest-consequence rows (D1, D4, D6, D11) before this table was written — the sweep is evidence, not authority (`BUILD.md` `### Worker 0 verifies every finding against source before dispatching`). All four re-derivations matched.

**What the audit did NOT find, stated first because it is the load-bearing negative:** no correctness defect and no silent omission in shipped source. Every layer the spec describes that has a shipped subsystem is implemented **at or beyond** what the spec asked for — the nested-connection optimizer (D9), the visibility-aware related filter branches, and the keyset cursor surface all exceed their spec text. The divergences below are the spec describing mechanisms the architecture chose differently on, plus six never-built items. **Nothing was quietly dropped in a way that leaves a user-visible capability missing except the three already-carded beta subsystems** (search / aggregates / FieldSet) and whatever `## Contract-level findings` resolves.

### Group A — never built, NOT carded anywhere (disposition is the maintainer's; see the escalation below)

| # | Spec claim | Evidence | Truth today |
|---|---|---|---|
| **D1** | `types/fields.py::DjangoModelField` — the spine of `### Layer 4`, `### Decision 3`, `### Phase 3`, and `### Layer 9`, with a transition path ending "delete per-relation resolver generation once the field class covers all cardinalities" | no `types/fields.py`; zero occurrences package-wide; `docs/SPECS/spec-010-foundation-0_0_4.md` #"Custom Strawberry field class (`DjangoModelField`). Rich-schema spec layer 4."; `docs/SPECS/spec-054-fieldset-0_1_1.md` re-declines it | Never built and absent from `docs/TREE.md`'s target layout. `types/resolvers.py::_attach_relation_resolvers` — the spec's "transition path" — is the **permanent** finalizer Phase-2 mechanism (`types/finalizer.py` #"Phase 2: ``_attach_relation_resolvers`` installs the framework's auto"). Responsibilities are distributed instead: annotation → `types/converters.py::resolved_relation_annotation`; access + async safety + N+1 → `types/resolvers.py::_make_relation_resolver`; visibility → `utils/querysets.py::apply_type_visibility_sync`; argument injection → the synthesized resolver `__signature__` on `connection.py::DjangoConnectionField` |
| **D2** | `OptimizerStore` + `with_hints` / `with_prefix` / `apply`, and "callable prefetch/annotate hints scoped to `Info`" (`### Borrow \`OptimizerStore\``, `### Layer 11`) | zero occurrences of all four names; `optimizer/hints.py::OptimizerHint.__post_init__`; `optimizer/plans.py::OptimizationPlan` | Replaced by a frozen four-directive `OptimizerHint` plus a whole-query `OptimizationPlan`. The Info-scoped-callable bullet is not merely unbuilt but **contradicted**: `optimizer/hints.py` pins that strategy selection "MUST never depend on request-varying data". No `annotate` hint exists in any form |
| **D3** | Borrow `get_strawberry_annotations` into `utils/typing.py` (`### Borrow \`get_strawberry_annotations\``) | zero occurrences; `utils/typing.py` carries `strawberry_schema_from_schema`, `strawberry_schema_from_info`, `schema_config_from_info`, `is_async_callable`, `unwrap_graphql_type`, `unwrap_container_type`, `unwrap_return_type` | Never landed. The annotation-provenance problem the borrow was for is solved by the four `consumer_*_fields` frozensets on `types/definition.py::DjangoTypeDefinition`, consumed by `types/base.py::_build_annotations` |
| **D4** | `DjangoField(...)` "for explicit advanced fields" (`### Borrow \`field\` and \`connection\` as implementation patterns`) | absent from `__init__.py::__all__`; `list_field.py::DjangoListField` | The explicit non-Relay field shipped under a different name and a narrower contract |
| **D5** | Keep `DjangoModelType` "as an internal or explicitly requested fallback" (`### Borrow \`resolve_type\`, but change relation fallback behavior`) | zero occurrences; `types/finalizer.py::_format_unresolved_targets_error` | Does not exist even as the reserved internal fallback — resolution is strictly error-only, i.e. **stricter than the spec asked for**, and consistent with the spec's own `### The unresolved-relation contract is error-only` |
| **D6** | `ASC_DISTINCT` / `DESC_DISTINCT` + "PostgreSQL `DISTINCT ON` plus window-function fallback" (`### Layer 7`, and a `### Phase 5` acceptance test) | `orders/inputs.py::Ordering` = `ASC`, `DESC`, `ASC_NULLS_FIRST`, `ASC_NULLS_LAST`, `DESC_NULLS_FIRST`, `DESC_NULLS_LAST`; `orders/sets.py` #"models.Min if direction.is_ascending else models.Max" | The two `_DISTINCT` members were **replaced**, not supplemented: spec-028 Decision 5 took strawberry-django's six-member NULLS enum. The to-many fan-out the DISTINCT directives addressed is solved by a row-preserving `Min`/`Max` annotation ordered by alias. **`docs/SPECS/spec-028-orders-0_0_8.md` `### Decision 12` still defers `DISTINCT ON` to `0.0.9`, which shipped five versions ago with no successor card — an orphaned deferral in a sibling spec** (read-only here; recorded for the maintainer). Phase 5's `ASC_DISTINCT` acceptance test can never pass as written |

### Group B — diverged; spec is wrong about shipped code (R1 fixes, no maintainer decision needed)

| # | Spec claim | Evidence | Truth today |
|---|---|---|---|
| **D7** | `## Target outcome` root field `object_type: ObjectTypeNode = DjangoNodeField(ObjectTypeNode)` | `relay.py` #"Resolution is **nullable by contract**" — dispatch is `required=False` unconditionally | The supported spelling is `ObjectTypeNode \| None`. A copied non-null annotation builds a schema that violates non-null on every hidden or missing row. **The single most consequential copy-paste defect in the spec** |
| **D8** | `## Target outcome` `Meta` carrying `aggregate_class`, `fields_class`, `search_fields` | `types/base.py::DEFERRED_META_KEYS` = `{"aggregate_class", "fields_class", "search_fields"}` | All three are **hard-rejected at class creation today**, so the spec's flagship example raises `ConfigurationError`. `Meta` also grew eight keys the spec never named (`connection`, `cursor_field`, `globalid_strategy`, `relation_shapes`, `nullable_overrides`, `required_overrides`, `filesystem_path_fields`, `primary`) |
| **D9** | `### Borrow \`DjangoListConnection\`` sketch: `DjangoConnection` carrying `total_count: int \| None` and `aggregates: AggregateType \| None` | `connection.py::DjangoConnection` #"The base carries no ``total_count`` field"; `connection.py::_connection_type_for`; `connection.py::_build_total_count_connection` | **Wrong in both fields.** The base is a bare `relay.ListConnection` subclass adding the `first`+`last` guard, window consumption, and keyset dispatch. `totalCount` is opt-in per type via `Meta.connection = {"total_count": True}`, which emits a generated concrete `<TypeName>Connection`. `aggregates` does not exist |
| **D10** | `### Borrow \`StrawberryDjangoDefinition\`` dataclass sketch | `types/definition.py::DjangoTypeDefinition` | Storage attr `__django_strawberry_definition__` **matches exactly** (`types/base.py` #"cls.__django_strawberry_definition__ = definition"). But `fields`→`fields_spec`, `exclude`→`exclude_spec`; `aggregate_class` / `search_fields` / the `LazyClassRef` union are absent; ~20 slots and three methods were added |
| **D11** | `### Layer 6` filter API: `class ObjectFilter(AdvancedFilterSet)` with `Meta.filter_fields` | `filters/sets.py::FilterSet`; `examples/fakeshop/apps/library/filters_genre.py::GenreFilter.Meta` uses `fields = {...}`; `filters/sets.py` #"``filter_fields = {"field": "__all__"}`` parity" | Shipped base is `FilterSet`, and the Meta key is django-filter's `fields`. The per-field `"__all__"` value **is** supported. The spec's example is uncopyable as written |
| **D12** | `### Layer 7` / `### Layer 8` base names `AdvancedOrderSet` / `AdvancedAggregateSet` | `orders/sets.py::OrderSet`; `orders/base.py::RelatedOrder` | `OrderSet` shipped; `RelatedOrder` kept its upstream name. `AdvancedAggregateSet` is unshipped and carded, but its name should follow the shipped `*Set` convention |
| **D13** | `### Layer 5` item 2, "finalize pending types" | `connection.py::DjangoConnectionField` contains no finalizer call; the spec's own `### Layer 3` says "The trigger is the explicit consumer call, and nothing else." | **The spec contradicts itself.** Layer 3 was corrected by the first residual cycle; Layer 5 item 2 is the same falsification's fourth site, which that cycle's own `## Standing notes` predicted ("a horizon document states its positions more than once") |
| **D14** | `## Proposed module layout` | `docs/TREE.md` #"fieldset/    # planned by TODO-BETA-054-0.1.1"; `KANBAN.md` #"Implement `django_strawberry_framework/fieldset/` (package, mirroring the `filters/` shape)"; `orders/inputs.py` exists | Three errors: `types/fields.py` is a dead proposal (D1); `fieldset.py` is listed flat although the section's own preamble declares the package layout canonical; `orders/inputs.py` is omitted although shipped code requires it. `permissions.py` exists but `docs/TREE.md` plans a `permissions/` package at `TODO-BETA-059-0.1.4` |
| **D15** | `## Migration path` Phases 1-8 | P1 `spec-010`; P2 `spec-008` + `types/converters.py::resolved_relation_annotation`; P3 **never shipped** (D1); P4 `spec-015`/`030`/`031`/`032`/`033`; P5 `spec-027`/`028` **minus** D6; P6 `TODO-BETA-057-0.1.3`; P7 split — `spec-034` shipped cascade, `spec-054` + `TODO-BETA-059-0.1.4` unshipped; P8 `spec-033`/`035` minus aggregate reuse | Phase 3's five acceptance tests all pass today **via other machinery**, which is the evidence that D1 was superseded rather than skipped |
| **D16** | `## Success criteria` (11 bullets) | see D8 | **8 of 11 met.** Unmet: `search` (`TODO-BETA-055-0.1.2`), aggregate output on connections (`TODO-BETA-057-0.1.3`), field-level permission masking (`TODO-BETA-054-0.1.1`) — each carded, none silently dropped |

### Group C — verified accurate; recorded so no later pass re-opens them

- `## The 0.0.4 local package baseline` — **every** listed symbol still exists at its named path; the two "retired since" markers are correct and no third is needed.
- `#### Take class-based generated type naming` — all three name shapes are literally the shipped derivations (`sets_mixins.py::ClassBasedTypeNameMixin`, `filters/sets.py` `_field_type_suffix`, `orders/inputs.py::_input_type_name_for`).
- `### Layer 2` `PendingRelation` sketch — matches `types/relations.py::PendingRelation` field-for-field; the most accurate code sketch in the spec.
- `## Target outcome` `class ObjectTypeNode(DjangoType, relay.Node)` — **valid**, not drift: `types/relay.py::apply_interfaces` #"already inherits a listed interface directly" filters against `__mro__`, so declaring the base and `Meta.interfaces` together is a documented no-op.
- The ~60 upstream `file:///...#LNN` citations — spot-checked three (`object_type.py#L119` → `class AdvancedDjangoObjectType`, `type.py#L73` → `def _process_type`, `optimizer.py#L1694` → `class DjangoOptimizerExtension`); all resolve exactly. Out-of-repo, so `AGENTS.md` rule 27 does not reach them. **Not a drift row** — do not "fix" them.
- The spec carries **zero** in-repo raw `path:NN` citations, so rule 27 compliance is a property to preserve here, not establish.

## Contract-level findings escalated to the maintainer before dispatch

`BUILD.md` `### Contract-level findings are escalated as maintainer decisions before dispatch` governs: these turn on which contract the package *should* offer, not on whether the code matches a contract, so they are not a worker's call.

### Maintainer decision 1 — Group B is reconciled, and deferred layers are corrected in place

**Decision** (maintainer, 2026-08-15): R1 corrects every name and shape the shipped package contradicts — `AdvancedFilterSet` → `FilterSet`, `Meta.filter_fields` → `Meta.fields`, the `Ordering` directions, the node-field nullability, the `DjangoConnection` shape, the `Meta` example — **and** states which card owns each still-unshipped layer, so the spec stays a usable design horizon rather than a museum piece.

**Rejected alternative.** *Reconcile only layers whose subsystems shipped, leaving deferred layers aspirational as written.* Lost because the falsified names are not aspirational — `AdvancedFilterSet` was never this package's name at any version, so leaving it costs a reader a working example while buying no historical fidelity.

### Maintainer decision 2 — Group A's disposition is decided by a parity investigation, not by this plan

**Decision** (maintainer, 2026-08-15). The maintainer's rule, verbatim:

> I do not want to drop any features that should have been added, but I also don't want to add any more features that are not parity features of graphene-django and strawberry-django. If these features are parity then they should have been implemented at the time of building spec-009 and were therefore missed and we then need to build them in now. If they are not parity then they need to be investigated to find out if these features should be added at all based on their usefulness (if they should be added, then they need to be pushed to a future card) and if the features are not useful, then they need to be dropped, and the spec needs to be reshaped to not mention the features at all.

A dedicated research pass was dispatched on 2026-08-15 to answer, per Group A item: is it a parity capability; if so what is the user-visible gap and what would building it entail; if not, is it useful enough to card; and a one-line verdict of `BUILD NOW` / `CARD FOR FUTURE` / `DROP AND SCRUB FROM SPEC`. Its brief carries the whole `AGENTS.md` reading list and both upstream reference checkouts.

**The crux the investigation must not fumble**, recorded here so the finding is auditable: the parity test is **consumer-visible capability**, not symbol presence. `StrawberryDjangoField` and `OptimizerStore` are upstream *internal plumbing*; the question is never "does upstream have this class" but "does it give upstream's users something a `django-strawberry-framework` user cannot get today". D15 is the standing evidence that at least D1 is a mechanism rather than a capability: Phase 3's five acceptance tests all pass today via other machinery.

**Consequence for R1, which is not optional either way.** Whatever the verdict, no Group A item may keep its current spec text: a `BUILD NOW` item is restated as an unbuilt contract with its card; a `CARD FOR FUTURE` item is restated pointing at the new card; a `DROP` item is **removed from the spec entirely**, with the rationale recording why it lost. The spec may not go on describing a mechanism the package chose against as though it were the plan.

#### Results — all six verdicts are `DROP AND SCRUB FROM SPEC`

Returned 2026-08-15. **No item is a missed parity build, and no item earns a new card.** Worker 0 independently re-derived every load-bearing claim before recording it (the four upstream/sibling checks are quoted in-line); all matched.

| Item | Parity? | Why it is not a missed build | Verdict |
|---|---|---|---|
| **D1** `DjangoModelField` | No | Upstream-*internal* plumbing. Every consumer capability it carries already ships through this package's own grain (D1's evidence column). graphene-django has no analogue class at all. Declined three times, the last decisively: `docs/SPECS/spec-054-fieldset-0_1_1.md` #"a custom \`DjangoModelField\` field class is unnecessary machinery" — and spec-054 pins **resolver wrapping** as the FieldSet mechanism, removing the last surface (Layer 9's `get_result`) the class was reserved for | DROP AND SCRUB |
| **D2** `OptimizerStore` + Info-scoped callable hints | No | graphene-django ships **no optimizer module at all** (verified: no `optim*` under the installed `graphene_django/`), so it fails the both-libraries test outright. Info-scoped callables are not merely unbuilt but **forbidden** by the invariant that buys the cross-request plan cache (`optimizer/hints.py` #"MUST never depend on request-varying data"); request-varying shaping already has its seam in `get_queryset`. The one live fragment — annotation dependencies — is **already carded**: `KANBAN.md` #"the expanded dependency kinds (relation traversals, annotations" on `TODO-BETA-053-0.1.1` | DROP AND SCRUB |
| **D3** `get_strawberry_annotations` | No | A dataclass-MRO annotation collector — pure mechanism, no consumer capability. The provenance problem it solves is solved here structurally and more explicitly by the `consumer_*_fields` frozensets; landing the borrow now would be a **second** provenance system | DROP AND SCRUB |
| **D4** `DjangoField(...)` | No | It *is* the decorator-first API — the surface `AGENTS.md` line 3 names as "the reason this package exists" to avoid, and a `GOAL.md` non-goal. Its capabilities ship as `DjangoListField` (deliberately graphene-django's symbol), `DjangoConnectionField`, `DjangoNodeField`, and plain `@strawberry.field`. The one upstream-only extra (filter/order args on a bare list) is single-library = optional by `START.md`'s own test | DROP AND SCRUB |
| **D5** `DjangoModelType` fallback | No | A *weaker* schema is not a missing capability. Verified upstream as a pk-only placeholder (`strawberry_django/fields/types.py::DjangoModelType` → `pk: strawberry.ID`); graphene-django's counterpart is silently skipping the field, which `### Decision 6: fail loudly` exists to refuse. **Scrubbing also resolves a live self-contradiction** — the spec says both "keep `DjangoModelType` as a fallback" and "the contract is error-only; no subsystem may be designed against it" | DROP AND SCRUB |
| **D6** `*_DISTINCT` / `DISTINCT ON` | No | The shipped six-member `Ordering` is **member-for-member identical** to `strawberry_django/ordering.py::Ordering` (verified in the checkout) — exact parity — and graphene-django has no DISTINCT ordering directives anywhere. The `_DISTINCT` members exist only in the DGF *reference*, and reference-only = optional. **The shipped `Min`/`Max` design already delivers the same user-visible result** (one row per parent ordered by the extreme child value, uninflated `totalCount`, NULLS preserved) and composes with cursor pk-tiebreak ordering, which `DISTINCT ON`'s leftmost-expression constraint does not | DROP AND SCRUB + sibling reconciliation (Decision 3 below) |

**The framing correction this produced, recorded because it changes R1's sweep:** these are not six unbuilt features. Five are upstream *internal mechanisms* whose consumer capability this package already delivers through a different grain, and one is a reference-only surface whose motivating problem shipped under a better design. That is why the disposition is scrub-not-card: a card would promise a user-visible capability that already exists.

### Maintainer decision 3 — the scrub covers ALL THREE sites

**Decision** (maintainer, 2026-08-15): **all three sites**, on the standing instruction quoted in the spec-008 cycle — *"since we did not fix every inbound reference in the same change last time, do that now"*. The dropped claims live in three documents, and this cycle fixes every one:

1. **`docs/SPECS/spec-009-…md`** — the six scrubs plus Group B. Item **R1**.
2. **`docs/SPECS/spec-028-orders-0_0_8.md`** — `### Decision 12` and its echo sites still defer `DISTINCT ON` to `0.0.9`. Worker 0 verified the deferral is genuinely orphaned: `grep -rn "DISTINCT ON\|distinct_on" KANBAN.md BACKLOG.md` returns **nothing**, so no card carries it and `0.0.9` shipped five versions ago. The correction is a **reconciliation, not a card** — the deferral was *discharged by an alternative* (the row-preserving `Min`/`Max` ordering now in `orders/sets.py`), not by the `Meta.distinct` design it anticipated. Item **R2**.
3. **The fakeshop kanban DB — card `TODO-BETA-054-0.1.1`'s body.** Two stale references, both verified by Worker 0: `KANBAN.md` #"item 38 for the \`DjangoModelField\` custom Strawberry field class" and #"See [\`BACKLOG.md\`][backlog] item 38 for the \`DjangoModelField\` direction". Both point at a BACKLOG item 38 that is now the *test-policy* entry (`BACKLOG.md` #"Layered manual relation override test policy"), and `spec-054` already flagged the staleness. `KANBAN.md` is script-rendered, so this is an **ORM edit + regenerate**, never a hand-edit. Item **R3**.

**Rejected alternatives.**

- *Spec-009 only.* Lost because it would leave two documents asserting claims this cycle just proved false, and the standing instruction exists precisely to stop that.
- *Spec-009 + spec-028, defer the DB.* Lost on the maintainer's explicit choice. It was the recommended option on concurrency grounds, and the risk it named is real but **measured and currently absent**: `examples/fakeshop/db.sqlite3`, `KANBAN.md`, `KANBAN.html`, and `docs/GLOSSARY.md` are all **clean** at this decision point (`git status --porcelain` over those four paths → empty), so attribution by diff **is** available to this cycle. R3 re-checks that immediately before writing and **stops and escalates rather than writing** if any of the four has gone dirty — the spec-008 cycle could not do this, which is why it deferred.

**Scope limit.** This authorizes exactly: the six scrubs and Group B in spec-009; `### Decision 12` and its in-file echo sites in spec-028; and card 054's two stale `CardItem` references in the DB plus the regenerate. **No other sibling spec, no other card, no source file, and no test file becomes writable.** A defect found outside that set is recorded for the maintainer.

### Maintainer decision 4 — the clause-by-clause sweep extends to the WHOLE spec, as a split sub-item

**Decision** (maintainer, 2026-08-16): extend the mechanism sweep to all 1,096 spec lines, not only the ~112 this cycle added.

**What raised it.** R1's review pass 7 escalated that the cycle's passes had read the *added* text clause-by-clause against source but that **984 of 1,096 lines are pre-existing text no pass had re-verified at the mechanism level**. Those lines were audited at the *claim* level by this plan's opening verification pass — that is what produced the D1-D16 table and the `### Group C` verified-accurate rows — but never clause-by-clause. The base-rate argument is what carried it: **ten defects of one class** (a sentence stating a mechanism, seam, cause, or recourse the code does not have) were found in the added text alone, so the rate in pre-existing text is unlikely to be zero.

**Rejected alternatives.**

- *Added lines only; card the rest.* Was the recommended option on cost grounds and lost on the maintainer's explicit choice. It would have held the declared contract and kept R2-R4 nearer, at the price of leaving a known-nonzero defect population in a shipped spec.
- *Sample the pre-existing text.* Lost as a half-measure: it buys an estimate, and the maintainer wants the defects fixed rather than counted.

**Split, per `BUILD.md` `### Slice splitting`.** The sweep is not folded into R1. R1's contract is the D1-D16 reconciliation and it closes on that; the whole-spec audit lands as **R1b**, its own artifact and its own full worker chain. Two reasons: the remediation set is unbounded at dispatch time and would make one un-reviewable diff, and mixing a bounded finding-loop with an open-ended audit destroys the ability to say what either one delivered. R1b inherits R1's method — enumerate every causal / mechanism / seam-attribution / recourse clause, open the symbol each names, cut or replace what is false, and **report the denominator** (enumerated / opened / changed / judgement) so a reviewer audits coverage instead of re-deriving it.

**Two method corrections R1b inherits, both learned the expensive way here:**

- **Wrapped phrases defeat multi-word greps.** A rationale twin survived six passes because the phrase broke across a line; `grep 'cascade helpers'` missed it and `grep cascade` found it instantly. Search the shortest distinctive token and count occurrences (`BUILD.md` `## Claims are proven mechanically`).
- **An invariant comment validates the RULE, not the REASON.** Five passes confirmed a rule by citing a docstring while never opening the mechanism the *because* clause described. Verify every causal clause separately from the rule it supports.

### Maintainer decision 5 — the async `SyncMisuseError` coverage gap is closed NOW, as a real test

**Decision** (maintainer, 2026-08-16): promote the gap's ready-made body to a permanent test in this cycle rather than carding it.

**What raised it.** Five separate passes flagged it, and it is the only escalation whose **evidence inaction destroys**: `docs/builder/temp-tests/r1/test_async_execution_default_connection.py` is gitignored and clears with the cycle. It pins a real gap — `tests/test_connection.py::test_sync_context_async_get_queryset_raises_sync_misuse` covers only `execute_sync`, so **no permanent row pins `async def get_queryset` → `SyncMisuseError` for a *default* `DjangoConnectionField` under `await schema.execute`**. That distinction is not incidental: it is the exact fact R1's `:417` correction turned on (`connection.py::_build_connection_resolver` fixes the sync/async choice at **construction**, so a default connection field runs the sync pipeline even under async execution).

**Rejected alternatives.**

- *Card it in the kanban DB.* Lost because the DB is contended by a concurrent writer (see R3) and a card defers work the cycle can finish.
- *Record it in the deferred catalog only.* Lost because a body inlined in an artifact is not a test — it never runs, and the next reader must re-derive that it is correct.

**Consequence: this is the cycle's ONLY item that writes code**, so `## Build-wide context flags`' source/test read-only rule is amended for it and for nothing else. It lands as item **R1c**, the cycle's only full `W1 → W2 → W3 → W1` chain over a test file, and it carries two obligations the documentation items did not:

- **A failability proof** (`BUILD.md` `## Failability proofs: prove the test can fail`). The new row pins an existing production boundary rather than introducing one, so the proof is the ideal shape here: mutate the guard so the boundary is gone, confirm the new row is among the failures, revert, and prove the revert by byte-comparison. A row that cannot fail is not coverage.
- **Floor verification** (`BUILD.md` `## Floor verification`). The row exercises a Django/Strawberry async-execution seam, which is squarely in scope, so the plan's blanket `none` does not reach it — R1c re-runs its focused scope in an isolated floor venv. This **amends the preamble's floor-verification declaration for R1c alone**.

### Maintainer decision 6 — R3 proceeds, and waits for its precondition rather than skipping it

**Decision** (maintainer, 2026-08-16): do R3's card-054 DB edit in this cycle, not the deferred catalog — confirming `### Maintainer decision 3`'s three-site scope after its precondition failed.

**The precondition failed after decision 3 was taken.** `examples/fakeshop/db.sqlite3`, `KANBAN.md`, and `KANBAN.html` were clean when the three-site scope was authorized and have since gone dirty under a concurrent session. This plan's own rule is that R3 **stops and escalates rather than writing** in that state, so the maintainer was asked again and confirmed.

**How R3 proceeds under a live concurrent writer:** re-check all four DB-backed paths immediately before writing. If clean, write and regenerate normally. **If still dirty, do not revert and do not skip** — `BUILD.md` `### Tracked binary / generated files` licenses applying the slice's writes **on top** of concurrent state and handing the mixed diff to the maintainer to reconcile at commit. Two-consecutive-regenerate byte-stability cannot distinguish this cycle's write from theirs while theirs is in flight, so R3 records that limitation explicitly rather than claiming a verification it cannot perform, and hands the maintainer the mixed diff with the two intended `CardItem` changes named exactly.

### Maintainer decision 7 — R2's scope widens by exactly one source docstring clause

**Decision** (Worker 0, 2026-08-16, on the maintainer's standing instruction rather than a fresh escalation; flagged to the maintainer in the same turn).

**What raised it.** R2's review found a **third** shipped-source citation of `spec-028` `### Decision 12`: `django_strawberry_framework/orders/sets.py::OrderSet.get_flat_orders`'s docstring reads *"cookbook's DISTINCT ON tuple-half dropped (spec-028 Decision 12 -- DISTINCT ON deferred to `0.0.9`)"*. R2's rewrite retired that deferral, so **this cycle's own edit falsified a line of shipped source**, leaving the package asserting a retired deferral to any reader who meets it inside the code. The pass had proved the inbound *anchor* population exhaustively (0) but asserted the *name* population without the grep — a rename protects neither.

**Why decided rather than escalated.** The maintainer has answered five consecutive scope questions on this cycle by widening (`### Maintainer decision 3`, `4`, `5`, `6`, and the parity disposition), and the governing instruction is theirs, quoted in the spec-008 cycle: *"since we did not fix every inbound reference in the same change last time, do that now."* Leaving it would reproduce precisely the failure this item exists to correct — a stale deferral surviving five versions because the claim sat one document over from whoever was editing.

**Precedent.** The spec-008 cycle's `#### Maintainer decision 4` made the identical carve-out: a **comment-and-message-only** source edit, dispatched through the full unmodified worker chain, when that cycle's work falsified source prose. This follows it exactly.

**Scope limit — comment-and-docstring-only, across the shipped citations of Decision 12.** No behavior change, no signature change, no test change, no source file outside `django_strawberry_framework/orders/`. Each edited clause states what is true now (the DISTINCT ON surface is **rejected**, not deferred), matching the rewritten Decision 12.

**Amendment, 2026-08-16 — the population is FOUR, and the operative word was always "all".** This decision first said "the three shipped citations". That count was **asserted without the grep**, and R2's apply-changes pass measured it mechanically: `grep -ro "Decision 12" django_strawberry_framework/` returns 20, of which four cite spec-028, all under `orders/`. The fourth — `orders/inputs.py::convert_order_field_to_input_annotation` — escaped every earlier sweep because it spells the reference **`Spec Decision 12`**, so a grep requiring `spec-028` and `Decision 12` on one line could not see it. R2's review reproduced the same defect one spelling further out, which is the sixth grep-shape trap catalogued on this cycle.

R2's review graded the widening question and this amendment adopts its reasoning: **"three" was a cardinality asserted about the world, not a scope election.** A wrong count mis-describes the set a predicate quantifies over; it does not narrow the predicate, and the maintainer instruction this decision rests on carries no count at all. The widening test is met identically, and more sharply: before R2 that clause was merely stale-by-date; **after R2 it is contradicted by the very Decision it names**, because it justifies two unused parameters by "a future DISTINCT ON extension … in `0.0.9`" while `spec-028` now records that port as **Rejected**. This cycle created that contradiction.

**The fourth citation is TWO sites, not one** — the trap that would otherwise produce a fourth one-site fix of the same shape. `orders/inputs.py` carries the docstring clause **and**, two lines below the corrected line, `del model_field, owner_definition  # reserved for future-extension (see docstring).` — a code comment pointing at the docstring for exactly the rationale being cut. Cutting one without the other leaves a dangling pointer. Both are in scope; nothing else in that module is.

**Consequence for the plan's flags.** `## Build-wide context flags`' source read-only rule is amended by this decision and by `### Maintainer decision 5` (R1c's test) and by nothing else. R2 does **not** become a code item: it stays `W1 → W3 → W1`, since a docstring is spec-custody-shaped prose and Worker 1 already owns the surrounding reconciliation.

### Constraint binding R1 and R2 — do not break inbound anchors while scrubbing

`### Decision 3: custom Strawberry field class` and `### Phase 3: DjangoModelField` are a numbered decision and a numbered phase, so removing their content raises a renumbering question. **Renumbering the Decision list is forbidden**: `docs/SPECS/spec-010-foundation-0_0_4.md` #"### Decision 6: fail loudly" cites spec-009's Decision 6 by heading anchor, and a shift would silently dangle it. Worker 1 keeps every surviving Decision's number and heading text stable and chooses how to handle the vacated slots; the same care applies to `## Migration path`'s phase numbering, which `### Phase 5`'s acceptance list also references.

## Pre-flight outcome (7 steps, `worker-0.md` `## Pre-flight procedure`)

1. **Working-tree baseline is explicit.** `git status --short` → 41 entries, every one attributable to another session. See `## Baseline-dirty out-of-scope files`. HEAD is `054de9dd`.
2. **`scripts/review_inspect.py` runs.** `uv run python scripts/review_inspect.py django_strawberry_framework/types/definition.py --output-dir docs/shadow --stdout` emitted its overview (13 imports, 8 symbols). Exit 0. Run against `types/definition.py` deliberately: `DjangoTypeDefinition` is the object the spec's `### Borrow \`StrawberryDjangoDefinition\`` sketches, so the smoke test doubles as a read of the shipped shape.
3. **Build artifacts are reset — DEVIATION 1, see below.** Verified instead that every path this plan creates is absent: no `docs/builder/build-009*`, no `docs/builder/bld-009*`.
4. **`.gitignore` lists the untracked scratch paths.** `docs/shadow/` (line 174), `docs/builder/worker-memory/` (188), `docs/builder/temp-tests/` (192). Present.
5. **Scratch directories are cleared — DEVIATION 2, see below.** `docs/builder/temp-tests/` was already empty; the four `docs/builder/worker-memory/worker-<N>.md` files were already present and zero-length; `docs/shadow/` was not emptied.
6. **Spec-doc consistency check.** `uv run python scripts/check_spec_glossary.py --spec docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md` → `OK: 23 terms - all have glossary entries and at least one spec link.` Exit 0.
7. **Spec rationale is extracted.** **Already done** — `docs/SPECS/appx/spec-009-rich_schema_architecture-0_0_4-rationale.md` exists and is committed at `f3c94642`. The gate is satisfied: every spawn in this cycle reads the post-extraction spec, which is what the rule protects. R1 **appends** to the rationale rather than performing the move.

Two further baselines recorded at pre-flight, both re-checked by any pass that writes:

- `uv run python scripts/check_trailing_commas.py --check` over the spec and its rationale → exit 0 (link-definition scaffold and the 10 canonical group headers intact in both).
- Archive completeness, verified against the live DB rather than the rendered board: `Card.objects.get(number=9)` reads `status.key == "done"`; its `SpecDoc` is `spec-009-rich_schema_architecture-0_0_4` with `path == "docs/SPECS/spec-009-rich_schema_architecture-0_0_4.md"`; `card.glossary_links.count()` is **23**, matching the 23 terms `check_spec_glossary` counted. **The archive is already complete**, so R2 verifies rather than performs it.

### Deviation 1 — other cycles' `bld-*.md` artifacts are PRESERVED

Pre-flight step 3 deletes old `build-*.md` / `bld-*.md`. `docs/builder/bld-003-final.md` is **not** deleted: it is committed (`20a9752f`, the spec-003 residual cycle) and is that closed cycle's record. `BUILD.md` `### Cohorting, naming, and closure` ("Pre-flight for a round") already establishes that when a cycle's input is already-built work, the prior artifacts are the record of that work and must survive; every item here operates on already-built, already-released work. **Collision is avoided by naming, not by deletion** — every artifact this plan creates is `bld-009-`-prefixed and the plan is `build-009-`-prefixed, and none of those paths exists.

### Deviation 2 — `docs/shadow/` was not emptied, and worker memory is NAMESPACED

`docs/shadow/` holds prior cycles' overviews plus this cycle's step-2 smoke. Not emptied, and safe: it is gitignored, regenerable, and per `AGENTS.md` rule 23 each generator clears its own folder before writing, so a stale overview cannot be read as fresh output by any pass that runs the helper.

Worker memory: the four un-namespaced `docs/builder/worker-memory/worker-<N>.md` files are present and zero-length, so re-seeding them would be a no-op — but a concurrent session could adopt them at any point. This cycle therefore uses its own namespace, **`docs/builder/worker-memory/spec-009-worker-<N>.md`**, seeded empty by Worker 0 at plan creation. The rule's intent — a private notebook per worker, persisting across one build, invisible to every other worker — is preserved exactly; what changes is only that concurrent builds no longer collide in one file. Every dispatch prompt names the namespaced path, carries the standing "do not read the other workers' memory files" instruction, and additionally forbids reading the un-namespaced files and any other cycle's namespace.

### Deviation 3 — the `built` state is skipped where the deliverable is Worker-1-exclusive

`ARTIFACT.md` `## Status field ownership` gives `built` to Worker 2, and `worker-0.md` `## Per-slice dispatch` maps `planned` → Worker 2. Item **R1** has no Worker 2 role that could set it: `BUILD.md` `## Spec reconciliation` and `worker-1.md` `## Scope` make Worker 1 the **only** role that may mutate the spec, and R1's entire deliverable is spec and rationale edits — the rationale being a file `BUILD.md` states outright that **Worker 2 never reads**.

So for R1 the chain is **Worker 1 (plan + perform, `planned`) → Worker 3 (audit, `review-accepted` | `revision-needed`) → Worker 1 (final verification, `final-accepted`)**, and Worker 0 reads `planned` on that artifact as "dispatch Worker 3", not Worker 2. Declared here, before dispatch, so no pass improvises the mapping.

**Corollary, carried forward from the six prior residual cycles:** `worker-0.md` `## Per-slice dispatch` step 4 routes a Worker-3 `revision-needed` to Worker 2 for the apply-changes pass. On R1 that route does not exist — the same two rules that remove Worker 2 from the perform pass remove it from the fix. **The apply-changes pass for R1 is Worker 1's, and it sets `planned` again**, returning the artifact to the `planned` → Worker 3 mapping above. The loop is otherwise unchanged and repeats until Worker 3 has no unresolved finding.

The Worker 3 audit is **not** skippable alongside the Worker 2 build. `BUILD.md` names Worker 3 as a reader of the rationale file during review and as the pass that checks the finished work against it. A rewrite performed by its own author is reviewed by an agent with no memory of why a sentence was cut — the only vantage point from which an over-cut looks like an over-cut.

## Baseline-dirty out-of-scope files

Workers neither edit nor revert these, and never `git checkout` them (`AGENTS.md` rule 34). Attribution is positive, not inferred: this cycle's writable set is the archived spec-009 file, its rationale sibling, the `bld-009-*` artifacts, this plan, and the namespaced memory files — **no entry below is in any of them.**

41 entries at pre-flight, in two attributable groups:

- **A package-source session** (`M`): `_boundary_ordering.py`, `_cross_web_patches.py`, `_request_body.py`, `conf.py`, `connection.py`, `consumers.py`, `extensions/error_policy.py`, `extensions/resource_policy.py`, `list_field.py`, `middleware/request_body.py`, `permissions.py`, `relay.py`, `resource_policy.py`, plus the tests that pin them (`tests/base/test_conf.py`, `tests/test_connection.py`, `tests/test_error_policy.py`, `tests/test_list_field.py`, `tests/test_permissions.py`, `tests/test_relay_node_field.py`, `tests/test_resource_policy.py`, `tests/test_routers.py`, `tests/test_views.py`, `examples/fakeshop/test_query/test_transport_api.py`). Declared read-only here and unreachable from any Markdown pass in this cycle.
- **A REVIEW cycle**: `docs/review/rev-_cross_web_patches.md`, `rev-_django_patches.md`, `rev-_strawberry_patches.md`, `rev-apps.md`, `rev-conf.md` (`M`), plus twelve untracked `rev-*.md` and `review-0_0_14.md` (`??`). `AGENTS.md` rule 22 names `rev-*.md` committed source of truth; its prescribed `git checkout HEAD -- docs/review/` restore is banned in this cycle by the `git checkout` ban in `BUILD.md` `## Claims are proven mechanically` and by rule 34's no-auto-revert. **No worker in this cycle restores, reverts, or touches anything under `docs/review/`**, and no pass treats its state as its own output.

**Expect this list to grow.** `HEAD` may move during this cycle; **any pass quoting a commit hash from this plan re-derives it rather than trusting it**, and proves its own work was not swept into someone else's commit with `git log --stat` over this cycle's paths — never `git status` alone. If the list grows, workers **report it and never revert it**, and Worker 0 appends it here rather than a worker editing the plan.

**Baseline exception for the final test-run gate**, recorded here because `BUILD.md` `## Final test-run gate` requires it in the plan's preamble to be honoured: `uv run pytest --no-cov`, `uv run ruff format --check .`, `uv run ruff check .`, and `git diff --check` all read the whole tree, so they will see a concurrent session's 23 modified source/test files and a REVIEW cycle's uncommitted output. A failure attributable to a file this cycle never wrote does **not** block `final-accepted` and does **not** route back through a residual item's loop; it is reported to the maintainer. The gate still reports each command's real result — the exception governs what a result *blocks*, never whether it is recorded honestly.

## Concurrent-writable tracked binary / generated files

Churn in these is not proof a worker caused it (`BUILD.md` `### Tracked binary / generated files: churn and concurrent-writer handling`).

- `examples/fakeshop/db.sqlite3` — **no residual item is expected to write it.** Card 9 is already Done, its `SpecDoc.path` already points at the archived location, and its 23 glossary links already match the terms CSV. Compare `iterdump()` semantics, never file bytes.
- `KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md` — generated; this cycle writes neither the DB nor the rendered files. Never hand-edited. **Cite glossary entries by heading, symbol-qualified, never by line number.**

If any pass concludes a DB write is genuinely required, it **stops and escalates to Worker 0** rather than writing.

## Build-wide context flags

- **`0.0.4` shipped and the version quintet is at `0.0.14`.** No residual item touches `pyproject.toml`, `django_strawberry_framework/__init__.py`, `tests/base/test_init.py`, the GLOSSARY package-version line, or `uv.lock`.
- **Source and tests are read-only.** Spec-009 shipped no source of its own — it is an architecture horizon whose layers shipped under later specs — so there is no source prose it owns. A defect found in source is escalated, never edited here, unless the maintainer's answer to an escalation widens the scope.
- **`CHANGELOG.md` is closed.** `AGENTS.md` rule 21 governs.
- **`README.md`, `docs/README.md`, `docs/TREE.md`, `docs/GLOSSARY.md`, `AGENTS.md`, `START.md`, and `docs/builder/BUILD.md` are read-only.** Where the spec disagrees with a durable doc, the spec is what moves.
- **Sibling specs are read-only EXCEPT `spec-028` as `### Maintainer decision 3` names.** The three inbound references to spec-009 — `spec-008` #"the higher-level target outcome", `spec-010` #"No shipped helper auto-triggers finalization", `spec-010` #"### Decision 6: fail loudly" — are all already heading-anchored rather than line-ranged, so no rewrite of spec-009 can silently dangle them; the third is why `### Constraint binding R1 and R2` forbids renumbering. A pass that finds a defect in an unnamed sibling records it for the maintainer and does not widen.
- **The kanban DB is writable for R3 ONLY, and for exactly two `CardItem` references.** `### Maintainer decision 3` site 3 authorizes it. Everything in `worker-0.md` `## Closing out a kanban card` about ORM-not-SQL writes, the `post_save` side-row, and two-consecutive-regenerate verification applies; the relevant steps are embedded in R3's dispatch prompts because Workers 1-3 may not read `worker-0.md`. **No card status flips, no `SpecDoc` changes, no glossary rows are touched** — card 9 is already Done and correct, and card 054 stays `TODO`.
- **The spec is already archived.** `BUILD.md` `### Spec stays at its working location` requires a move be plan-declared as a Worker-1-owned final-verification step. There is no move to perform.
- **Only the maintainer commits.** No worker commits, and none creates or switches a branch.

## Artifact list

- `docs/builder/bld-009-r1-spec_code_reconciliation.md`
- `docs/builder/bld-009-r1b-whole_spec_clause_sweep.md`
- `docs/builder/bld-009-r1c-async_syncmisuse_test_row.md`
- `docs/builder/bld-009-r2-spec028_distinct_reconciliation.md`
- `docs/builder/bld-009-r3-card054_db_references.md`
- `docs/builder/bld-009-r4-docs_archive_audit.md`
- `docs/builder/bld-009-final.md`

No `bld-integration.md`: no item lands package source, so there is no cross-slice DRY scan to run. The integration pass's two live obligations are folded in — the staged-anchor sweep into R4, the cross-artifact read into the final gate.

**Per-item worker chain**, declared before dispatch so no pass improvises it (`### Deviation 3`):

| Item | Chain | Why |
|---|---|---|
| R1 | W1 → W3 → W1 | Deliverable is spec + rationale edits; Worker 1 is the only role that may make them, and Worker 2 may never read the rationale |
| R1b | W1 → W3 → W1 | Same — spec + rationale edits only (`### Maintainer decision 4`). Dispatched only after R1 reaches `final-accepted`, so the two never write the same file concurrently |
| R1c | W1 → W2 → W3 → W1 | **The cycle's only code-writing item** (`### Maintainer decision 5`). Worker 2 writes the test, owes a failability proof, and owns the floor run |
| R2 | W1 → W3 → W1 | Same — a sibling-spec reconciliation is still spec custody |
| R3 | W1 → W2 → W3 → W1 | **The one full chain.** DB-backed card-body work is Worker 2's (ORM edits + regenerate), per `worker-0.md` `## Closing out a kanban card`; Worker 0 embeds the relevant procedure steps into the dispatch because Workers 1-3 may not read `worker-0.md` |
| R4 | W1 → W3 → W1 | Audit + sweep; writes only its artifact unless it finds a defect, which it escalates |

## Checklist

- [x] R1: Scrub the six dropped features from spec-009 and reconcile Group B with shipped code; record every correction's reasoning in the rationale -> `docs/builder/bld-009-r1-spec_code_reconciliation.md`
- [x] R1b: Clause-by-clause mechanism sweep of the whole spec (all 1,096 lines, not only this cycle's additions) per `### Maintainer decision 4` -> `docs/builder/bld-009-r1b-whole_spec_clause_sweep.md`
- [x] R1c: Promote the async `SyncMisuseError` row to a permanent test per `### Maintainer decision 5` -> `docs/builder/bld-009-r1c-async_syncmisuse_test_row.md`
- [x] R2: Reconcile `spec-028` `### Decision 12` and its echo sites — the orphaned `DISTINCT ON` deferral, discharged by the row-preserving `Min`/`Max` design -> `docs/builder/bld-009-r2-spec028_distinct_reconciliation.md`
- [x] R3: Fix card `TODO-BETA-054-0.1.1`'s two stale `DjangoModelField` / BACKLOG-item-38 references in the kanban DB and regenerate -> `docs/builder/bld-009-r3-card054_db_references.md`
- [x] R4: Finish the documentation obligations, audit the archive, run the staged-anchor sweep, **and fix the one clause R2 falsified in the spec-009 rationale** (see `### R4 inherits`) -> `docs/builder/bld-009-r4-docs_archive_audit.md`
- [x] Final test-run gate -> `docs/builder/bld-009-final.md`

## Baseline growth, recorded 2026-08-15 after the parity pass

`git status --porcelain | wc -l` → **68**, up from 41 at pre-flight. `HEAD` unchanged at `054de9dd`. **Nothing was reverted and no worker may revert any of it.** The growth is in three concurrent groups, none of which intersects this cycle's writable set:

- a **DRY cycle** started (`docs/dry/`, 8 entries) — new since pre-flight;
- the **REVIEW cycle** widened (`docs/review/`, 19 entries);
- the **package-source session** widened to `optimizer/` (4), `rest_framework/` (2), `extensions/` (2) and their tests.

The four DB-backed / generated paths R3 needs — `examples/fakeshop/db.sqlite3`, `KANBAN.md`, `KANBAN.html`, `docs/GLOSSARY.md` — were **clean** at this reading, which is what makes R3 dispatchable at all. **R3 re-checks all four immediately before writing and stops rather than writing if any has gone dirty.**

### Second growth, recorded at the close of R1 (2026-08-15) — a CONCURRENT SPEC-010 CYCLE

Reported by Worker 1, verified and appended by Worker 0. Not reverted; `HEAD` still `054de9dd`. **A second residual cycle is running this same workflow on `spec-010` in parallel:**

- `docs/SPECS/spec-010-foundation-0_0_4.md` and `docs/SPECS/appx/spec-010-foundation-0_0_4-rationale.md` (`M`)
- `docs/builder/build-010-foundation-0_0_4.md`, `docs/builder/bld-010-r1-spec_reconciliation.md`, `docs/builder/bld-010-r2-lazy_override_coverage.md` (`??`)

**This is the highest-coupling concurrency this cycle faces, and it is not the ordinary out-of-scope case.** Spec-009 and spec-010 cross-reference each other by **heading anchor in both directions**, and this plan's `### Constraint binding R1 and R2` rests on one of them: `spec-010` #"### Decision 6: fail loudly" cites a spec-009 heading, which is *why* renumbering was forbidden. The reverse coupling is live too — spec-009 cites `spec-010` #"## Strawberry finalization strategy" and #"### Unresolved-target error format".

Standing instruction for every remaining pass in this cycle:

- **Never edit, revert, or `git checkout` either spec-010 file or any `bld-010`/`build-010` artifact.** They belong to the other cycle (`AGENTS.md` rule 34).
- **Re-verify, do not assume, every cross-spec anchor you depend on**, at the moment you depend on it — the other cycle may retitle a heading between one pass and the next. R1 verified spec-010's two inbound anchors as byte-identical after its edits; that verification is timestamped, not permanent.
- **A broken cross-spec anchor found later is reported, never unilaterally repaired**, because the correct fix may belong to the other cycle's spec rather than ours. Route it to Worker 0 for maintainer escalation.

Worker 0 has flagged the collision to the maintainer: two cycles editing a mutually-anchored spec pair cannot both own the reconciliation of the pair's shared claims, and only the maintainer can sequence them at commit.

## R4 inherits — a cross-reference this cycle's own work falsified

Found by R2's final verification, recorded here because R1 is `final-accepted` and closed:

**`docs/SPECS/appx/spec-009-rich_schema_architecture-0_0_4-rationale.md` still says `spec-028` `### Decision 12` "still defers `DISTINCT ON`".** R2 retired that deferral, so the clause is false. It is **R1's own text**, in a tracked and committed permanent document — the exact `### Maintainer decision 7` shape, one *document* over instead of one *module* over, and found by the one corpus no pass had swept: spec to other permanent documents.

**R4 fixes it.** That is a one-clause correction inside a file this cycle already owns, and leaving it would reproduce precisely the failure this cycle exists to correct — a stale claim surviving because it sat one document away from whoever was editing. Reopening `R1` is the wrong route: its contract is discharged and its artifact is closed; R4's contract is *the cross-reference audit*, which is exactly what this is.

**R4 also inherits the corpus lesson**, which is the transferable half: this cycle swept spec→spec, spec→source, and spec→board, and missed spec→permanent-companion. R4's audit must enumerate **all four directions** explicitly rather than sweeping the three it already has instruments for.

### Maintainer decision 8 — R4's writable set widens by two clauses in files this cycle falsified

**Decision** (Worker 0, 2026-08-16, on the same standing maintainer instruction as `### Maintainer decision 7`; flagged to the maintainer in the same turn).

R3's final verification caught a real gap in `## R4 inherits`: inheriting an item does **not** make its file writable. `## R4 inherits` transfers only files this cycle already owns. So R4 gets an explicit, enumerated widening for the two clauses **this cycle's own work falsified**, and nothing else:

1. **`docs/SPECS/appx/spec-009-rich_schema_architecture-0_0_4-rationale.md`** — its claim that `spec-028` `### Decision 12` "still defers `DISTINCT ON`", falsified by R2. Already this cycle's file; listed here so the pair is enumerated in one place.
2. **`docs/SPECS/spec-054-fieldset-0_1_1.md` #"BACKLOG.md item 38"** — its present-tense claim that card 054 cites `BACKLOG.md` item 38, falsified by R3. A sibling spec, excluded by `### Maintainer decision 3`'s enumerated limit, so it needs this widening. **After R3, `spec-054` is the only document in the repo asserting the retired citation.**

**Same test, third application.** Decision 7's standard was: this cycle's own edit falsified a line, so the cycle fixes it rather than shipping a contradiction it authored. Both clauses meet it exactly. The governing instruction is the maintainer's, quoted in the spec-008 cycle: *"since we did not fix every inbound reference in the same change last time, do that now."*

**Recommended shape for site 2**, from R3's final verification: a **past-tense** rewrite that keeps the live rejection rationale and adds a back-pointer to card 054. **Do not de-duplicate** — the board renders for readers who do not hold the spec, so the near-copy is load-bearing rather than a DRY defect.

**Scope limit — exactly these two clauses.** No other sibling spec, no other card, no source, no test. A third instance of this class found by R4 is **recorded for the maintainer, not fixed**: three unilateral widenings on one standing instruction is the ceiling, and a fourth needs the maintainer's own word.

**The transferable lesson, which R4 must act on rather than merely record.** This cycle swept spec→spec, spec→source, and spec→board, and was bitten twice by the corpus it did not sweep: **spec→permanent-companion** and **board→spec**. R4's audit enumerates **all four directions explicitly**, including the reverse direction of every edit this cycle made — every fix creates a potential inbound falsification at the other end, and that is precisely how both of these were born.
