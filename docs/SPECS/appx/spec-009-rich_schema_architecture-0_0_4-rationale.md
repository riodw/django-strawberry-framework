# Rationale: spec-009 — rich schema architecture (deliberation, rejected alternatives, change record)

Deliberative companion to [`spec-009-rich_schema_architecture-0_0_4.md`][spec-009]. The spec states
the long-term layered architecture the package is built toward; everything that explains **how a
claim in it came to be falsified and corrected** lives here — the text cut out of the spec, the
evidence that falsified it, and the alternative each correction rejected.

Created by the [`docs/builder/BUILD.md`][build] `## Spec rationale extraction` pass, long after the
release rather than before the build. Card `DONE-009-0.0.4` shipped many minor versions ago and the
rule that gates a build on this move did not exist then. Text marked *Moved* below was cut out of the
spec, not copied: it exists here and nowhere else.

## How to read this file

- **One entry per spec section**, named by the section's own heading. A section with no entry here
  lost nothing to this pass — that is not an omission.
- **This spec is a design horizon, not a contract.** It describes eleven layers, most of which have
  since shipped under their own specs. It is deliberately not the owner of any shipped behavior, so
  a reader looking for what the package *does* wants [`docs/GLOSSARY.md`][glossary] and the
  per-feature specs, never this one.
- **The corrections here are unusually load-bearing for a horizon document.** One of them —
  `### Layer 3: Finalization trigger` — described a mechanism that was rejected before the
  foundation slice shipped, and described it as preferred. Two further sections repeated it. A
  reader designing against the spec would have designed against a mechanism that has never existed.
- **In-repo citations are symbol-qualified**, per `AGENTS.md` rule 27. The spec carried twelve raw
  `path:NN` citations, one per line, all of them in-repo; every one was converted.

## Provenance of this record

Every claim below was re-derived against the working tree at the time of the pass. The central
one — that nothing in the package auto-triggers finalization — was established by grepping the whole
package for calls to `finalize_django_types()` and confirming that the only occurrences are prose in
docstrings, with no call site outside the consumer's own code. It was *not* carried from the
spec-008 cycle's report, though that cycle reached the same conclusion independently.

## Entries keyed to the spec

### `### Layer 3: Finalization trigger` — the rejected mechanism, stated as preferred

*Moved.* The spec carried this:

> Preferred triggers:
>
> 1. `DjangoConnectionField(Type)` calls `finalize_django_types()` before it returns a field.
> 2. `DjangoNodeField(Type)` calls `finalize_django_types()` before it returns a field.
> 3. `DjangoSchema(...)` calls `finalize_django_types()` before constructing `strawberry.Schema`.
> 4. `finalize_django_types()` remains public for advanced users.
>
> Why this combination:
>
> - cookbook-style schemas define node types first and root fields after, so `DjangoConnectionField`
>   can finalize naturally
> - direct manual schemas can use `DjangoSchema`
> - advanced users can call the finalizer explicitly in tests or unusual import layouts

**What actually shipped.** Only item 4. `DjangoConnectionField`, `DjangoNodeField` and `DjangoSchema`
all exist and none of them calls the finalizer; the explicit consumer call is the sole trigger, and
`spec-010-foundation-0_0_4.md` #"## Strawberry finalization strategy" states so in terms — "no
shipped helper auto-triggers finalization". Items 1-3 were rejected before the foundation slice
landed.

**Why the combination lost.** Two reasons, and the first is fatal on its own.

1. *It reintroduces the coupling the architecture exists to remove.* If constructing a connection
   field finalizes, then whether a given `DjangoType` is included depends on whether its module was
   imported before that construction — which is import-order coupling wearing a different hat. The
   package's whole premise is that schema shape must never depend on declaration or import order.
   A trigger that fires on the first construction of any of three unrelated objects makes the
   finalization boundary implicit and position-dependent, which is precisely the failure mode
   [definition-order independence][glossary-definition-order-independence] is named after.
2. *It puts a process-global mutation behind three constructors.* `finalize_django_types()` mutates a
   process-global registry and mutates class objects, and the registry is deliberately lockless.
   Spec-010 pins the finalizer to a single-threaded setup window for that reason. Three separate
   auto-trigger sites multiply the number of places that window can be violated, and none of the
   three constructors is in a position to enforce it.

**What was kept.** The fourth bullet of "Why this combination" — that finalization must happen before
Strawberry schema conversion, so no post-schema patching is needed — is a genuine requirement rather
than an argument for the rejected mechanism, and it survives in the rewritten section alongside the
reason a schema extension cannot be the trigger.

**The constraint the rejection leaves behind** is stated in the spec rather than here, because it
binds future work: any helper that ever auto-triggers finalization must also enforce the
single-threaded setup window, by being constrained to schema-construction time or by acquiring a real
lock.

### `### Decision 2: explicit package finalizer` — the same falsification, in one clause

*Moved.* The decision read:

> Add `finalize_django_types()` and call it from package-owned schema/field helpers.

The first half shipped; the second half is the rejected auto-trigger in six words. It is recorded
separately from the Layer 3 entry because of how it was found: the Layer 3 correction was made first,
and this clause survived it, three hundred lines away in a section a reader would reasonably treat as
the authoritative summary. A correction applied at the site where a claim is *argued* does not reach
the site where it is *asserted*, and the numbered-decision list is exactly where a hurried reader
looks.

### `## Open questions` — two answers falsified, one settled by shipping

Three of the five questions had been overtaken by shipped work.

- *Should plain `strawberry.Schema` remain fully supported?* The old answer — "yes for simple
  schemas, but rich schemas should use `DjangoSchema` or package-owned fields that finalize before
  schema construction" — is the Layer 3 falsification a third time, and it carried a real cost: it
  told consumers that plain `strawberry.Schema` was a second-class path. It is not. Because the
  trigger lives in neither the schema nor the field objects, every schema shape works identically
  once the consumer has called the finalizer, and choosing `DjangoSchema` is a richness decision with
  no bearing on finalization.
- *Should multiple `DjangoType`s per model be allowed?* Settled by [`Meta.primary`][glossary-metaprimary]
  in `0.0.6`. The rewritten answer states the shipped shape — many types per model, exactly one
  primary, ambiguity refused rather than guessed — and points at
  [`spec-018-meta_primary-0_0_6.md`][spec-018] for the contract. The three refusal sites were
  verified in `registry.py` and `types/finalizer.py` rather than taken from the card.
- *Should filters/orders/aggregates copy Graphene names exactly?* Settled for filters and orders,
  which shipped in `0.0.8` under [`spec-027`][spec-027] and [`spec-028`][spec-028] following exactly
  the rule this section stated. Left open for aggregates, which have not shipped. Splitting the
  answer was deliberate: collapsing it to "settled" would have claimed a record for a subsystem that
  does not exist yet.

The two remaining questions — generic fallback, and whether sentinel redaction is required — were
re-checked and left alone. Both answers still hold.

### `## Current local package baseline` → `## The 0.0.4 local package baseline`

The section is a snapshot of the package as it stood when the spec was authored, and it was headed
and worded as though it described the package now. Every line number in it had rotted, and two of the
thirteen functions it listed as "Important current functions" no longer exist.

The correction anchors the section to the moment it describes rather than rewriting it to the present.
That is the right direction for a design horizon: the layers below were designed against *that*
baseline, so replacing it with today's inventory would break the argument the rest of the document
makes. The rejected alternative was deleting the section outright, which would have left the layer
designs with no stated starting point.

Two entries carry an explicit **retired since** marker rather than being repointed:
`types/converters.py::convert_relation`, whose work is now done by
`types/converters.py::resolved_relation_annotation`, and `registry.py::TypeRegistry.lazy_ref`, the
`NotImplementedError` placeholder the 0.0.4 slice deleted. Marking beats deleting because both names
appear in the layer arguments further down; marking beats repointing because neither replacement is
what the baseline argument was about.

### `### Status: deferred design idea, no card yet` → `### The unresolved-relation contract is error-only`

Two problems, one edit. The heading was status-shaped, which the board has been retiring from specs
since the spec-002 residual cycle — a spec states its contract, and a status line inside it is a
second place for the truth to live. And the status it stated, "no card yet", is a claim about the
board that no spec can keep true.

The substance was re-measured and kept: `Meta.unresolved_relations` is still uncarded, and the
error-only contract still holds. Only the framing changed, from a status report about a deferred idea
to a statement of the contract that is actually in force, with the wording delegated to
[`spec-010`][spec-010].

### `## Migration path from current package` → `## Migration path from the 0.0.4 baseline`

Eight numbered phases, several of them long since shipped, presented as a forward plan. The
correction adds one sentence establishing what the list is — a dependency order drawn from the
baseline above, not a schedule — and stating that the spec does not track which phases have shipped.

This follows the disposition the spec-003 residual cycle set and recorded in its own companion: a
spec states its contract and never narrates its own shipping status. The rejected alternative was
annotating each phase with its shipped version, which would have made the section a second, unowned
copy of the board and guaranteed it would drift.

### `## Target outcome` — the node field's nullability, and three keys that are not declarable

*Moved.* The root-field sketch read `object_type: ObjectTypeNode = DjangoNodeField(ObjectTypeNode)`.

The annotation was copied from the Graphene cookbook, where node lookup is non-null. It is wrong here for a
reason that is a contract rather than a style preference: node dispatch is `required=False`
unconditionally (`relay.py` #"Resolution is **nullable by contract**"), so a hidden row, a missing row,
and an uncoercible pk all resolve to `null`. A consumer copying the non-null spelling builds a schema
that violates non-null the first time a visibility hook hides a row — which is exactly the case a
privacy-first package expects to be common. The rejected alternative was making dispatch match the
annotation (raise instead of returning `null`); it lost because a raise on a hidden row is itself a
disclosure, and because the row-missing and row-hidden cases are then indistinguishable to a client only
by accident.

The three deferred `Meta` keys are a different failure. `aggregate_class`, `fields_class`, and
`search_fields` are in `types/base.py::DEFERRED_META_KEYS`, so the spec's flagship example raised
`ConfigurationError` on the whole class. Two alternatives lost. *Delete the three keys from the example*
would have made the target outcome stop being the target — those keys are the destination this document
exists to describe. *Mark the example "aspirational" and move on* leaves the reader no way to find out
which keys are which. What landed instead names, per key, the card that promotes it, so the example
stays the destination and a reader can act on it today. Naming the card is not a shipping record: it
points forward at open work, which is the opposite of the board-duplication the `## Migration path`
entry below rejected.

### ``#### Take `fields_class` `` and `### Layer 9: FieldSet and field-level permissions` — the mechanism is resolver wrapping

*Moved.* Both sections routed field-level behavior through "a custom Strawberry field class", Layer 9
naming `DjangoModelField.get_result` as the site.

Three mechanisms were live for this: a custom field class, Strawberry's `permission_classes`, and
wrapping the generated resolver. `permission_classes` lost first — `BasePermission.has_permission` is
class-per-policy with a fixed message contract, cannot express the gate-then-override cascade ordering
Layer 9 specifies, and would synthesize one permission class per managed field. The custom field class
lost for the same reason, one level up: it is machinery whose only job is to host a wrapper that a
wrapper can host directly, and it charges every generated field for a feature most fields do not use.
Resolver wrapping costs nothing on an unmanaged field, keeps the cascade in one readable body, and is
upstream-parity. `spec-054-fieldset-0_1_1.md` pinned it, and pinning it is what removed the last surface
`DjangoModelField` was being reserved for.

### ``### Borrow `StrawberryDjangoDefinition` `` — the sketch declared five things the dataclass never grew

*Moved.* The sketch declared `fields:` / `exclude:`, an `aggregate_class:` and a `search_fields:` slot,
and typed every sidecar as `type | LazyClassRef | None`.

Four separate falsifications, and the sketch sits in a fenced `python` block a reader will copy. The
storage attribute matched exactly, which is what made the rest easy to trust. `fields_spec` /
`exclude_spec` carry the `_spec` suffix because the slot holds the *declaration* from `Meta`, not the
resolved selection — `selected_fields` is that, and the two would read as synonyms without the suffix.
`LazyClassRef` has zero occurrences package-wide, and its absence is a design outcome rather than an
omission: `types/base.py::_validate_filterset_class` and its `_validate_orderset_class` twin refuse
anything but an already-resolved subclass at **class creation**, so no unresolved reference can reach
the slot. `aggregate_class` and `search_fields` have no slot
because their `Meta` keys are still in `DEFERRED_META_KEYS` and rejected at class creation — declaring
storage for a key the package refuses would be the spec asserting two different things about the same
key in two sections, which is exactly what it was doing.

**The rejected alternative was reproducing the shipped dataclass field-for-field.** It lost twice over:
twenty-nine slots would bury the five the section is arguing for, and this spec owns none of that
record, so the copy would drift the first time a later spec adds a slot. The sketch is therefore stated
as an explicit **subset**, with one sentence naming what the shipped record adds and one citation to
where it actually lives — the shape a horizon document can keep true.

Recorded in this pass's own review as an over-tick rather than a miss: the drift row was marked closed
while the section was byte-unchanged. The lesson is narrower than "check your ticks" — every other row
in that table produced a visible edit somewhere in the diff, so the tick was auditable and was audited;
what a self-reviewed pass cannot do is notice the row it never opened.

**The replacement clause was itself wrong, and pass 2 cut it.** The first apply-changes pass explained
the missing `LazyClassRef` with a *reason* — that a sidecar binds at finalization rather than at class
creation — which shipped code contradicts in both halves: the validators named above run at class
creation, and deferred binding is what would *permit* a lazy reference, not what removes the need for
one. It also read as a denial of the spec's own `RelatedFilter` lazy-ref lines, which describe a
different object entirely: what the finalizer resolves lazily is a `RelatedFilter`'s related-set target
*inside* an already-resolved set class (`types/finalizer.py::_expand_filterset`), never the
`Meta.filterset_class` value itself. The finalization algorithm's lazy-ref step is therefore accurate
and no drift row was opened against it. The lesson is the four-seam rule below arriving one section
early: a fluent subordinate clause explaining *why* is a claim about shipped code, and when it is
wrong the correct repair is to cut it, not to qualify it.

### ``### Borrow `get_strawberry_annotations` `` → `### Track annotation provenance structurally, not by re-collecting annotations`

*Moved.* The section directed that upstream's dataclass-MRO annotation collector be borrowed "closely"
into `django_strawberry_framework/utils/typing.py`, to preserve annotation namespaces across inheritance
and postponed annotations and to let "a future override system distinguish package-generated fields from
consumer-authored annotations".

It never landed, and the problem it was for was solved differently and better. Provenance here is
**recorded at the moment of authorship** rather than **reconstructed afterwards**: the four
spelling-specific `consumer_*_fields` frozensets on `types/definition.py::DjangoTypeDefinition` — a
fifth slot, `consumer_authored_fields`, carries their union — are derived in
`types/base.py::DjangoType.__init_subclass__` at collection time and know not only that a field was
consumer-authored but in which spelling — annotated or assigned, relation or scalar. Their first
readers are the three override-target validators, `_build_annotations` after them; every one reads the
same union rather than deriving its own. A collector re-walking the namespace can
only ever infer that. Postponed annotations are handled by deferring `strawberry.type` to finalization,
which is when every target type exists, so no eval-time namespace capture is needed at all.

The alternative — land the borrow anyway, since it is small and proven upstream — lost on the same
ground the `## The single-ownership law` inherited from the spec-008 cycle states: it would be a
**second** provenance system, and two independently-derived answers to "where did this annotation come
from" disagree eventually. The rewritten section therefore states the invariant (one provenance system)
rather than the borrow.

### ``### Borrow `StrawberryDjangoFieldBase` and `StrawberryDjangoField` `` and `### Layer 4` — the field class lost to the finalizer

*Moved.* Layer 4 was headed "Strawberry-native field class" and instructed: create `DjangoModelField`
based on upstream's `StrawberryDjangoField`, migrate generated relation fields onto it, and "delete
per-relation resolver generation once the field class covers all cardinalities". The borrow section
carried its dataclass sketch and a five-behavior borrow list. `### Decision 3`, `### Phase 3`, the
`## Definition-order strategy` finalization algorithm's step 6, and `## Proposed module layout`'s
`types/fields.py` were the same claim's other five sites.

It was never built, is absent from `docs/TREE.md`'s target layout, and has now been declined three
times, the last decisively (`spec-054-fieldset-0_1_1.md` #"field class is unnecessary machinery").
The parity test it fails is **consumer-visible capability, not symbol
presence**: `StrawberryDjangoField` is upstream *internal plumbing*, graphene-django has no analogue
class at all, and every capability the class was to carry already ships through this package's own
grain — annotation via `types/converters.py::resolved_relation_annotation`, access and N+1 cooperation
via `types/resolvers.py::_make_relation_resolver`, visibility via
`utils/querysets.py::apply_type_visibility_sync`, async safety via its
`utils/querysets.py::apply_type_visibility_async` twin on the fields that own the queryset, and
argument injection via the synthesized resolver `__signature__` on
`connection.py::DjangoConnectionField`. The standing evidence is that Phase 3's five acceptance tests
all pass today, through that machinery.

**Why upstream needs the class and this package does not** is the whole argument, and it is now stated in
the spec because it is implementation-relevant: upstream's public API is decorator-first, so the
decorator's return value is the only object it owns and every responsibility must attach to it. This
package's public API is `class Meta`, so the finalizer owns generation and each responsibility can live
where it is cheapest to reason about. The real risk of distributing them — metadata scattering across
annotations, class attributes, resolver closures and optimizer maps — is answered by
`DjangoTypeDefinition` being single-sourced, not by a field object.

Two alternatives lost. *Build it now as a missed parity feature* lost because there is no user-visible
gap to close; a card for it would promise a capability that already exists. *Keep the section, marked
deferred* lost on the maintainer's explicit instruction that a dropped feature is scrubbed rather than
softened — a spec that goes on describing a mechanism the architecture chose against will be designed
against by someone.

**The claim `### Layer 4` may no longer make:** that `_attach_relation_resolvers` is transitional, or
that per-relation resolver generation is to be deleted. It is the permanent finalizer Phase-2
mechanism, and the rewritten section states the constraint that makes it permanent — generation cannot
happen at class creation (the target may not exist) or after `strawberry.type` (the type is frozen), so
Phase 2 is the only window.

**One of the four seams was restated in the apply-changes pass, and the correction is a rule.** The
visibility bullet said the composition happens on the relation queryset "so a nested traversal cannot
see a row a root query would hide". The seam is real, the absolute is not:
`types/resolvers.py::_make_relation_resolver` never calls `apply_type_visibility_sync` — it imports
nothing from `utils/querysets` — and the composition runs on the connection pipeline, on
`list_field.py::DjangoListField`, and on the optimizer's prefetch child
(`optimizer/walker.py::_build_child_queryset`), the last of which is opt-in at schema construction.
That is not a source defect and none was escalated: the default many-side shape is the connection, and a
raw `list[T]` relation is an explicit `Meta.relation_shapes` opt-in whose rows are capped by
`resource_policy.py::bounded_rows`. **No recourse may be named for that path**: `permissions.py`'s
cascade helpers are not one — `permissions.py::_is_cascadable_edge` admits only single-column concrete
forward FK / OneToOne edges, so it refuses every kind in `utils/relations.py::MANY_SIDE_RELATION_KINDS`
(`"many"`, `"reverse_many_to_one"`, `"generic"`) — exactly the kinds
`types/converters.py::resolved_relation_annotation` emits `list[T]` for. Refusing them all is not the
same as covering the rest: `"reverse_one_to_one"` is in neither set — it is annotated
`target_type | None`, and the cascade skips it too. The rule is that **naming the seam that implements
a guarantee is not the same as establishing where the guarantee holds** — a bullet listing four seams
invites exactly that slip, because the other three really are unconditional.

**And the spec had two of those bullets, not one.**
``### Borrow `StrawberryDjangoFieldBase` and `StrawberryDjangoField` `` carries a twin four-seam list,
whose visibility bullet the same pass left unqualified — a rule stated in the general and applied in
the particular to only the copy that was already being edited. Pass 2 pointed the twin at this section rather than restating the paths there:
one section owns the seam map, the other cites it, which is the same single-ownership split that keeps
the spec and this file from arguing with each other. Where a claim appears twice, correcting it once is
a half-correction, and the reader cannot tell which half is current.

**Pass 3 deleted the twin list instead of correcting a fourth bullet, and that is the settled shape:
`### Layer 4: Generated relation fields` is the sole owner of the responsibility-to-seam map, and
``### Borrow `StrawberryDjangoFieldBase` and `StrawberryDjangoField` `` states the borrow argument and
points at it.** The finding that forced the decision was the twin's second bullet claiming
`types/resolvers.py::_make_relation_resolver` carries **async safety**; that module contains no async
machinery at all — a `grep -cE` for `async`, `sync_to_async`, `SynchronousOnly` or `await ` over
`django_strawberry_framework/types/resolvers.py` returns 0 — and all three generated shapes are plain
sync callables. Correcting the bullet was rejected: three passes had each closed one
bullet of that list and each time the next pass found another, and the list existed only because this
cycle rewrote two HEAD sections — one borrow list, one transition path — into two four-seam lists, so
three of the four bullets said the same thing twice. A duplicate map has no correct state; it has a
current half and a stale half. Cutting it retires the fourth defect and the duplication in one edit,
and leaves nothing for a fifth pass to find. Layer 4's four bullets were each re-derived against source
before being declared the survivor.

**Async-safe queryset access is not a generated relation field's seam, which is why the answer is not a
fifth Layer 4 bullet.** Putting it there would repeat the misattribution one section over. The
generated resolver is sync; the colored runner pair in `utils/querysets.py`
(`apply_type_visibility_sync` / `apply_type_visibility_async`, with
`utils/querysets.py::SyncMisuseError` closing the sync path against an `async def get_queryset`) is
applied by `connection.py`, `list_field.py`, and `types/relay.py` — the fields that own the
queryset, and the same family the visibility bullet was corrected to name. The alternative
considered and rejected was **dropping `async-safe queryset access` from the upstream-requirement list
at the top of the borrow section**: it is a real upstream behavior and a real requirement, and deleting
a requirement to close a mis-attribution is how a spec stops describing something the code has to do.
A third alternative, **saying nothing** — cutting the false clause and leaving the requirement
unanswered — lost because the section's whole job is to say where each borrowed behavior lives; an
unanswered member of that list reads as an oversight rather than a decision.

**The vacated `### Decision 3` slot was repurposed, not left empty.** Renumbering is forbidden —
`spec-010-foundation-0_0_4.md` cites `### Decision 6: fail loudly` by heading anchor — and the choice
was between a numbered gap and a decision that occupies the slot on its own merits. A gap lost: it is a
scar that invites a later reader to re-fill it with the thing that was removed, and it says nothing. The
replacement decision states the positive contract (generated field behavior belongs to the finalizer,
composability comes from a single readable definition) without naming the mechanism that lost, per the
rule that the spec never narrates its own history. The same reasoning repurposed `### Phase 3`, whose
five acceptance tests describe a contract that is still exactly right.

### ``### Borrow `resolve_type`, but change relation fallback behavior`` and `## Open questions` — the placeholder tier is gone

*Moved.* The section ended: "Keep `DjangoModelType` only as an internal or explicitly requested
fallback, not as the default for `Meta.fields = "__all__"`." `## Open questions` carried the matching
"Should generic fallback exist? Not for 1.0 by default. Consider an explicit opt-in after concrete
relation finalization ships."

Both are **self-contradictory against this spec's own
`### The unresolved-relation contract is error-only`**, which says the contract is error-only and that no
subsystem may be designed against a relaxation. A reader had two answers and no way to tell which was
current — the failure mode the review-round custody rule calls worse than an un-updated spec.

The shipped behavior is stricter than either: no placeholder exists at any tier, and unresolved targets
raise at finalization (`types/finalizer.py::_format_unresolved_targets_error`). That is correct, not an
oversight. Upstream's `DjangoModelType` is a pk-only placeholder
(`strawberry_django/fields/types.py::DjangoModelType` → `pk: strawberry.ID`) and graphene-django's
counterpart is silently skipping the field — which `### Decision 6: fail loudly` exists to refuse. **A
weaker schema is not a missing capability**, so there is nothing to card.

The alternative — keep the reserved internal tier "in case", since it costs nothing unbuilt — lost
because it is not free: it is a documented promise that a subsystem may one day be designed against,
and `### The unresolved-relation contract is error-only` had already ruled that out. What was
deliberately **kept** is every mention of upstream's `DjangoModelType` as the design this package
refuses: those citations are load-bearing to `### Decision 1` and
`## Why not use generic relation fallback by default?`, and scrubbing them would have removed the
argument along with the rejected feature.

### ``### Borrow `field` and `connection` as implementation patterns`` — `DjangoField(...)` was the decorator API

*Moved.* The section offered "`DjangoField(...)` for explicit advanced fields" beside the connection and
node factories, with "Internally those should use a custom `DjangoModelField`."

`DjangoField(...)` *is* the decorator-first surface — the API `AGENTS.md` names as "the reason this
package exists" to avoid and `GOAL.md` lists as a non-goal — wearing a factory's clothes. Its
capabilities ship, split across `DjangoListField` (deliberately graphene-django's symbol, so that
migration site needs no shape change), `DjangoConnectionField`, `DjangoNodeField`, and plain
`@strawberry.field`. The single upstream-only extra — filter and order arguments on a bare
non-connection list — is available in one library only, which is `START.md`'s own test for *optional,
probably a later spec* rather than foundational.

The rejected alternative was renaming it (`DjangoAdvancedField`, `DjangoModelField(...)` as a factory) and
keeping the surface. That loses the objection entirely: the problem was never the name.

### ``### Borrow `OptimizerStore`, but keep the current optimizer's strengths`` → `### Keep the current optimizer's strengths, and borrow its nested-prefetch lessons`

*Moved.* The heading named the borrow, and the borrow list carried `OptimizerStore` as field-level
optimization metadata, `with_hints` / `with_prefix` / `apply`, and "callable prefetch/annotate hints
scoped to `Info`". `### Layer 11` repeated the first two as "lessons to add".

Three separate reasons, and the second is the interesting one.

1. *It fails the both-libraries test outright.* graphene-django ships **no optimizer module at all**, so
   an upstream optimizer store is single-library and therefore optional by `START.md`'s rule.
2. *The Info-scoped callable is not merely unbuilt but forbidden.* `optimizer/hints.py` pins that
   strategy selection "MUST never depend on request-varying data", and that invariant is what buys the
   cross-request plan cache. A callable hint that can read the request makes every cached plan unsound
   and un-cacheable at once. This is a case where the spec's direction and the shipped invariant were in
   direct opposition, so leaving the bullet would eventually have produced a change that silently broke
   the cache. The requirement it was reaching for — request-varying queryset shaping — already has its
   seam in `get_queryset`, which runs per request by construction.
3. *The store's own shape was replaced, not skipped.* A frozen four-directive `OptimizerHint` plus a
   whole-query `OptimizationPlan` is what shipped; there is no `annotate` hint in any form.

The one live fragment — annotation dependencies as an optimizer input — is **already carded** on
`TODO-BETA-053-0.1.1`, so it needed no new card here either. The rewritten section states the
value-not-callable rule positively, because that rule changes how a future hint is designed and
therefore belongs in the spec rather than here.

**A claim that rewrite may no longer make:** that `get_queryset` is *already composed into every path*.
It is not, and the direction of the error is fail-open. `types/resolvers.py` imports nothing from
`utils/querysets`, so the generated relation resolver composes no target-type `get_queryset`; the
composition runs on the fields that own the queryset and on the optimizer's prefetch child. Cut rather
than qualified — the value-not-callable rule stands on `get_queryset` running per request, which is all
it needs.

### ``### Borrow `django_resolver` and `django_getattr` `` — the same async mis-attribution, one section away

*Corrected in place, not moved.* This cycle rewrote the section's two closing sentences: HEAD's "Borrow
these patterns for `DjangoModelField.get_result`" became "Borrow these patterns into the generated
relation resolver", and HEAD's future-conditional "This will be more robust … once fields also need
filtering, ordering, pagination, permissions, and optimizer hooks" became the assertion "Centralizing
them there is what lets one resolver body **also carry** filtering, ordering, pagination, permissions,
and optimizer cooperation".

Both were wrong against shipped code, and both are the same shape as the `### Layer 4` finding — a
fluent clause explaining *why* that is really a claim about a module. `django_getattr`'s five
centralized patterns include **async contexts**, so "borrow these patterns into
`types/resolvers.py::_make_relation_resolver`" told an implementer to put async handling in a module
that has none; and the generated relation resolver carries no filtering, no ordering, no pagination and
no permission check — those are the connection field's. What its three bodies do carry is the N+1 probe
(`types/resolvers.py::_check_n1`), the `_prefetched_objects_cache` read, the FK-id elision
(`types/resolvers.py::_build_fk_id_stub`) and the `resource_policy.py::bounded_rows` call.

Sweeping this section was not in the finding, and finding it is the whole point of the rule the prior
passes wrote down: **grep for the shape the rule names, not for the site the finding names.** The site
the finding named was one bullet; the shape was "a seam sentence attributing async safety to the
generated relation resolver", and it had a third instance here. Leaving it would have contradicted the
corrected borrow section two screens later and guaranteed a fifth pass. The alternative — deferring it
as out of scope for a finding about two lists — lost for exactly that reason.

**A later sweep cut one more clause from that same replacement**: the generated relation resolver is not
*the single place every cardinality's access passes through*. Under the shipped `"connection"` default
for a many-side relation, finalizer Phase 2.5
(`types/finalizer.py::_synthesize_relation_connections`) deletes the generated list form and the
connection resolver owns that access; `_make_relation_resolver` is the single place only for the shapes
that survive Phase 2.5. The borrow instruction needs no such superlative, so it was cut.

### `### Layer 7: Order system` and `### Phase 5` — DISTINCT directives lost to a row-preserving annotation

*Moved.* Layer 7 listed `ASC`, `DESC`, `ASC_DISTINCT`, `DESC_DISTINCT` and "PostgreSQL `DISTINCT ON`
plus window-function fallback"; `### Phase 5` carried an `ASC_DISTINCT` / `DESC_DISTINCT` acceptance
test.

The two `_DISTINCT` members were **replaced, not skipped**. The shipped six-member
[`Ordering`][glossary-ordering] enum is member-for-member identical to
`strawberry_django/ordering.py::Ordering` — exact parity with the one library that has the feature — and
graphene-django has no DISTINCT ordering directives anywhere. The `_DISTINCT` members exist only in the
`django-graphene-filters` reference, and reference-only is optional by the same rule.

More decisively, the **problem** they addressed shipped under a better design. The directives existed to
stop a to-many join fanning parent rows out; the shipped answer annotates `Min(path)` for ascending
terms and `Max(path)` for descending and orders by the alias (`orders/sets.py`
#"models.Min if direction.is_ascending else models.Max"). It delivers the same user-visible result — one
row per parent, ordered by the extreme child value, with `totalCount` uninflated and NULL positioning
preserved — and it **composes with the connection's primary-key tiebreaker**, which `DISTINCT ON` cannot:
its leftmost-expression constraint fights the cursor ordering directly. So `DISTINCT ON` is not a
deferred better answer; it is a worse one for a cursor-paginated schema.

The rejected alternative was keeping the directives as an opt-in beside the annotation. It lost because
two orderings that produce the same rows by different SQL is two contracts to test, two interactions
with cursors to reason about, and one of them known-broken under pagination. `### Phase 5`'s acceptance
line was rewritten to assert the property (a to-many order path duplicates no parent rows and inflates
no count) rather than the mechanism, which is what the tests actually pin.

`spec-028-orders-0_0_8.md` `### Decision 12` was the same claim's sibling site and has since been
reconciled to match: no `DISTINCT ON` surface ships, and that spec now records the port as rejected
rather than deferred.

### ``### Borrow `DjangoListConnection` `` — the connection sketch was wrong in both fields

*Moved.* The sketch declared `total_count: int | None` and `aggregates: AggregateType | None` directly on
`DjangoConnection`.

Both are wrong, and for different reasons worth keeping apart. **`totalCount` is opt-in per type**
(`Meta.connection = {"total_count": True}`) because a count is a second query, and a base class that
declares the field makes every connection pay for a capability most schemas do not select. It resolves
through a generated concrete `<TypeName>Connection` — which is not a naming convenience: a bare generic
alias loses the `resolve_connection` override at Strawberry's generic specialization, so the concrete
subclass is what keeps package pagination dispatch reachable at all. That mechanism is stated in the
spec because a future field added to a connection must go the same way.

The first wording of that correction scoped the *generation* to the opt-in, when only the *member* is
opt-in: `connection.py::_connection_type_for` always returns a generated concrete subclass, and
`Meta.connection` "only controls the shape". Corrected in the apply-changes pass. The trap is worth
naming — an opt-in mentioned in the same sentence as a mechanism reads as governing it, so a sentence
introducing a flag should state what the flag does **not** decide.

**`aggregates` does not exist yet**, and this is the one place in this pass where a spec claim was kept
rather than corrected: it is the Graphene reference's shape, it is genuinely owed, and
`TODO-BETA-057-0.1.3` owns it. The correction is only that it lands through the generated-subclass
mechanism rather than by widening the generic base. The rejected alternative — deleting `aggregates`
because it is unshipped — would have dropped a real target-outcome commitment on a technicality about
today's code.

### `### Layer 5: Connection field` — the fourth site of the finalization falsification

*Moved.* Item 2 of Layer 5's numbered list read "finalize pending types".

This is the auto-trigger direction the first residual cycle corrected in `### Layer 3` and
`### Decision 2` — surviving, unnoticed, in a third section, exactly as this file's
`## Standing notes` predicted it would. It is also directly contradicted by this spec's own corrected
Layer 3 ("The trigger is the explicit consumer call, and nothing else") and by shipped code
(`connection.py::DjangoConnectionField` contains no finalizer call).

Removing the item left a hole worth filling: a reader who knew connection fields once finalized needs to
be told they must not, and why. The replacement states the negative contract with the failure it
prevents — a connection field constructed before every `DjangoType` module is imported would fix the
schema's shape to whatever had been imported by then, which is the import-order coupling this
architecture exists to remove.

**Method note for the next pass:** the count is now four sites, not three. Assume a claim in this
document is stated in a layer section, a decision line, an open-question answer **and** an
implementation list, and grep for the mechanism rather than for the sentence.

### `### Layer 6: Filter system`, `### Layer 8`, `### Phase 7` — names that were never this package's

*Moved.* The public-API examples declared `class ObjectFilter(AdvancedFilterSet)` with
`Meta.filter_fields`, `class ObjectAggregate(AdvancedAggregateSet)`, and `### Phase 7` added
`AdvancedFieldSet`.

`AdvancedFilterSet` was never this package's name at any version, so the example was uncopyable while
buying no historical fidelity — the reason the maintainer's decision reconciles deferred layers in place
rather than leaving them aspirational as written. The shipped base is
[`FilterSet`][glossary-filterset], and the reason is worth stating: it subclasses django-filter's own
`BaseFilterSet`, so a DRF-shaped surface should read as the class a consumer already has, and the
Graphene package's `Advanced` prefix would signal a distinction that does not exist here. The same
argument settles the two unshipped names: an unshipped-but-carded class follows the shipped `*Set`
convention (`AggregateSet`, `FieldSet`) rather than preserving a prefix from the reference
implementation, since the convention is what a reader will pattern-match against.

**One correction the drift table understated, verified in source rather than inferred.**
`Meta.filter_fields` is **not** rejected: `filters/sets.py::FilterSetMetaclass.__new__` aliases it onto
`Meta.fields` when `fields` is absent, deliberately, for cookbook parity. So the spec's example failed
on the base-class name alone. `Meta.fields` is nevertheless what the rewritten example uses and what the
spec now calls canonical — it is django-filter's key, it is what `GOAL.md` and `docs/GLOSSARY.md` show,
and a package documenting the alias as its primary spelling would teach two vocabularies. The alias is
stated in one sentence beside it so a cookbook migrant is not left guessing.

Where the Graphene class name refers to the **upstream** class as a reference it was left alone. The
complete list of survivors, so a later pass can tell deliberate from missed: `AdvancedAggregateSet` in
`#### Take aggregate semantics`, `AdvancedFieldSet` in ``#### Take `fields_class` `` **and** in
`### Layer 9: FieldSet and field-level permissions` ("Use `AdvancedFieldSet` semantics.", the same
prior-art shape as Layer 6's "Use `django-graphene-filters` semantics"), and the `file:///` citation
list. Those name a real class in a real checkout; renaming them would have made the citations false.

### `## Proposed module layout` — three errors, one of them self-contradicting

*Moved.* The layout listed `django_strawberry_framework/types/fields.py`, listed `fieldset.py` as a flat
module, and omitted `orders/inputs.py`.

`types/fields.py` is the dead `DjangoModelField` proposal and went with it. `fieldset.py` contradicted
the section's **own preamble**, which declares the package layout canonical because it determines import
paths, public-surface promotion, and test-tree mirroring — and `docs/TREE.md` plans `fieldset/` at
`TODO-BETA-054-0.1.1`. `orders/inputs.py` ships and is required by shipped code (it owns the direction
enum), so a layout omitting it would have a reader believe the order inputs live somewhere they do not.

`permissions.py` was correct and is now annotated with its planned migration to a `permissions/` package
at `TODO-BETA-059-0.1.4`, on the same forward-looking-ownership principle as the deferred `Meta` keys.
The rejected alternative was regenerating the whole layout from `docs/TREE.md`: that would make this
section a second copy of a script-rendered document and guarantee drift, when the section's job is to
state the *intended* shape of the Layer 3 subsystems and nothing more.

### `## Migration path from the 0.0.4 baseline` and `## Success criteria` — cards for open work, never versions for shipped work

*Moved.* `### Phase 6`, `### Phase 7`, and three of the eleven success criteria (search, aggregate output
on connections, field-level permission masking) named capabilities with no owner in the text.

The maintainer's decision requires the spec to "state which card owns each still-unshipped layer" so it
stays a usable design horizon. The entry above for `## Migration path from current package` rejected
annotating each phase with its shipped version, and both hold at once because they are different
operations: **naming a card for open work points forward and has exactly one owner; naming a version for
shipped work is a second, unowned copy of the board.** Only the unshipped items are annotated, and the
sentence establishing that the list is a dependency order rather than a schedule is untouched.

Eight of the eleven success criteria are met today. That number is deliberately **not** in the spec: it
would be true for one release, and a criterion carrying no card is one a reader can check against the
code in a minute.

### `### Phase 1`, `### Layer 3`, `## Proposed module layout`, `## Open questions` — convention corrections made beside the drift rows

Standing-rule violations fixed where the pass was already reading the surrounding text, each too small
to be its own finding and every one invisible to the checkers this cycle runs.

- `### Phase 1` carried the spec's only inline cross-file Markdown link,
  `[docs/SPECS/spec-010-foundation-0_0_4.md](spec-010-foundation-0_0_4.md)`, against `AGENTS.md` rule 28
  and `START.md` "Markdown link convention". It is now the reference-style `[spec-010]`, with its
  definition under the `<!-- docs/SPECS/ -->` group. `scripts/check_trailing_commas.py` enforces the
  scaffold and the group headers, not the inline-versus-reference choice, which is why it passed either
  way.
- `### Phase 1` also read "Earlier drafts of this spec listed `DjangoSchema` here; the foundation
  contract has narrowed" — the spec narrating its own history, which
  [`docs/builder/BUILD.md`][build] `## Spec rationale extraction` forbids in terms. *Moved* here and
  replaced with the contract stated directly: a later wrapper phase owns `DjangoSchema`. The
  falsification itself is genuine and already recorded — the foundation slice ships the finalizer and
  not the schema wrapper.

**Three larger narration sites the first sweep of this rule missed**, deleted in the apply-changes pass
after the review caught them. They matter more than the `### Phase 1` instance because two of them sat
in a section the pass had already edited twice, which is how a rule applied by accident looks from the
outside:

- `### Layer 3` carried a full paragraph of "an earlier direction had … that combination was
  **rejected**" prose. Its substance is this file's own `### Layer 3` entry, so nothing was lost by
  deleting rather than re-moving it; what stayed in the spec is the forward-looking constraint the
  rejection leaves behind, now stated as a property of the lockless registry rather than as the moral
  of a story, plus the one-line pointer here that `worker-1.md` `### Performing the rationale move`
  requires.
- `## Proposed module layout` said the flat-module names "in older drafts of this spec have been
  migrated to packages below", and closed by naming the eight flat modules the layout "replaces". Both
  are chronology, and the second was also redundant against the section's own preamble, which already
  declares the package layout canonical. Deleted, not moved: a list of module names that were never
  built records nothing a reader can act on.
- `## Open questions` pointed at `### Layer 3` "for why the auto-triggering alternative was rejected",
  which after the deletion above pointed at a section that no longer argues it. It now cites the spec
  section for the contract and this file for the alternative — the split the extraction rule intends.

**What was deliberately not touched.** The `## Standing notes` bullet below still says the Layer 3
falsification had three sites. It is pre-existing text and this file is append-only for the cycle; the
`### Layer 5: Connection field` entry above records the fourth site and the sweep method that found it,
and the spec's own opener now says four.

### `### Layer 2: Pending relation registry` — a sketch comment claiming a mirror it was not

The `PendingRelation` sketch annotated `relation_kind` as
`Literal["forward_single", "many", "reverse_one_to_one"]` and commented that it "mirrors
`utils.relations.RelationKind`". The alias has **five** members —
`"many"`, `"reverse_many_to_one"`, `"reverse_one_to_one"`, `"forward_single"`, `"generic"` — so the
comment asserted a correspondence the line did not have. Many-side classification is decided through
`utils/relations.py::MANY_SIDE_RELATION_KINDS`, which is a **three**-member frozenset —
`frozenset({"many", "reverse_many_to_one", "generic"})` — so the two members the sketch dropped
(`"reverse_many_to_one"` and `"generic"`) are **two of those three**, and the sketch's own `"many"` is
the third: it enumerated one many-side kind and dropped the other two. A reader trusting the mirror
would conclude a `GenericRelation` has no pending-relation kind at all.

The enumeration was **replaced by the alias name itself** rather than re-spelled with all five members.
Re-spelling would have been true today and false again on the next member; naming the alias is one grep
from the authority and cannot drift. A replacement beat a cut here because the sketch needs a type for
the slot, and `RelationKind` is checkable from the cited symbol at the reader's desk.

**Rejected alternative.** *Spell the five members inline.* Lost on drift: the same sentence has now been
wrong once, and an enumeration copied out of a `Literal` is a copy that no test compares.

### ``### Borrow `StrawberryDjangoDefinition` `` — a benefit the schema audit cannot deliver

The `Benefits:` list claimed the schema audit "can report exact unfinalized or unresolved fields".
`DjangoOptimizerExtension.check_schema` walks the `DjangoType`s **reachable from a built schema** and
returns one warning per exposed relation whose target model has no registered `DjangoType`. It cannot
report an unfinalized field, and not for want of a feature: a type reachable from a built schema has
already been through Phase 3, so "unfinalized" is not a state the audit can observe.

The clause was **narrowed to the capability the symbol has**, not cut, because the bullet's true half is
the reason the definition object is worth having and is verifiable from the linked glossary entry, which
names the reported condition exactly. This decision may no longer claim that any audit surface reports
unfinalized fields; the finalizer's own `ConfigurationError` is the only thing that speaks to
unresolved targets before a schema exists, and nothing reports unfinalized ones.

### `### Phase 3: Generated relation fields` and `### Decision 3: generated field behavior belongs to the finalizer` — the visibility seam is not generated for every cardinality

Both summarised `### Layer 4`'s four-seam map without Layer 4's per-seam scoping, and both were
therefore false in the same direction. The finalizer generates the annotation
(`types/converters.py::resolved_relation_annotation`) and the resolver
(`types/resolvers.py::_attach_relation_resolvers`) for every exposed relation, in the
cardinality-correct spelling, at finalization. It generates **no** visibility composition for any
of them:
`grep -c apply_type_visibility django_strawberry_framework/types/finalizer.py
django_strawberry_framework/types/resolvers.py` returns **0** for both, and each of the three shapes
`types/resolvers.py::_make_relation_resolver` emits — `many_resolver`, `reverse_one_to_one_resolver`,
`forward_resolver` — returns the row-bound accessor with no visibility call in it.

Row-level visibility reaches a relation only through a seam that **owns a queryset**. `### Layer 4`
names those seams and this entry does not re-spell them; what the two corrected sentences got wrong is
that they read as unconditional, when which seam applies depends on the relation's shape and on two
conditions the finalizer does not control:

- a **many-side** relation is read through the synthesized connection pipeline, which composes
  visibility — but `types/finalizer.py::_synthesize_relation_connections` synthesizes that connection
  only for a Relay-Node-shaped target under the `"connection"` (default) or `"both"` shape. Under
  `Meta.relation_shapes = {"<field>": "list"}` it synthesizes nothing and that pipeline is never entered.
- **any** relation, a **forward single** included, is composed by
  `optimizer/walker.py::_build_child_queryset` inside the generated `Prefetch` — but only when the
  target type overrides `get_queryset` **and** the optimizer extension is installed.
  `optimizer/walker.py::plan_relation` tests `_target_has_custom_get_queryset(target_type)` *before* the
  many-side test and returns `("prefetch", "custom_get_queryset")` for any relation whose target
  overrides the hook; `_plan_prefetch_relation` has no early return except `related_model is None`, so
  the downgrade reaches `_build_child_queryset`, whose `has_custom_qs` branch calls
  `apply_type_visibility_sync(target_type, queryset, info, allow_sliced=True)`. That walk runs only
  under `DjangoOptimizerExtension`: `plan_optimizations` is imported by no package module but
  `optimizer/extension.py`.

`### Phase 3` was **cut** to the two seams the finalizer does generate, and its "across every
cardinality" absolute replaced by Layer 4's own "cardinality-correct spelling" — the same absolute the
rule below condemns, left standing by the cut that produced the sentence. Its `— Layer 4` pointer
already carried a reader to the scoped statement. `### Decision 3` was **replaced** rather than cut,
because "generated field behavior belongs to the finalizer" is the decision's whole title and a bare cut
would have left the other two seams unaccounted for where a reader most expects the full map: it now
attributes them to the queryset-owning **components** and points at `### Layer 4`. Components, not
fields — `optimizer/walker.py::_build_child_queryset` is one of the seams Layer 4 names and is not a
field. Neither decision may any longer claim that a relation field's visibility composition is
generated, at finalization or anywhere else.

**Why these were carried here rather than fixed in the prior item.** Both sentences were judged
non-findings during the added-text sweep on three grounds — they restate an accepted map, they name no
symbol, and the scoped truth is one explicit pointer away. The first and third hold and are why the
remedies above are small. The second is what decided it: an unscoped absolute about a **row-level
visibility** boundary is read as a security property, and "names no symbol" is not protection when the
sentence's subject is the finalizer and the whole document is about what the finalizer generates. The
generalisable rule this document has now produced twice: **an absolute over "every cardinality" or
"every path" in this package is false by construction, because Phase 2.5 re-shapes what Phase 2
attached.**

**Rejected alternative.** *Leave both as a wording preference on accepted text.* Lost because the
direction of the error is fail-open: a reader who believes the finalizer composes visibility for every
cardinality stops asking which seam actually does, and so never learns that the two conditions above
gate it — leaving a forward single relation whose target **does** override `get_queryset`, read through
a schema built without `DjangoOptimizerExtension`, unfiltered on a path the sentence claimed was
covered.

### ``### Borrow `StrawberryDjangoFieldBase` and `StrawberryDjangoField` `` — a third copy of the seam map, two lines after declaring the map single-sourced

The section's closing paragraph named the visibility pair's appliers as "whichever field owns the
queryset: `connection.py`, `list_field.py`, `types/relay.py`" — **three of the eight modules** that
invoke `apply_type_visibility_sync` / `_async` (`connection.py`, `filters/sets.py`, `list_field.py`,
`mutations/resolvers.py`, `optimizer/walker.py`, `permissions.py`, `types/relay.py`,
`utils/querysets.py`), and a **different** incomplete triple than
`### Layer 4`'s own visibility bullet gives. It sat two lines below the sentence declaring that Layer 4
"states that seam map once; it is not repeated here", which the paragraph then repeated. Replaced by a
pointer at Layer 4, which is what the preceding sentence had already promised.

This is the same single-ownership remedy applied to `### Phase 3` and `### Decision 3` above, and the
reason it is the remedy rather than a longer list: a duplicated map has no correct state, only a current
half and a stale half, and this document had accumulated three halves that disagreed. `### Layer 4` is
the one telling; every other site points at it.

**Rejected alternative.** *Complete the list to all eight modules.* Lost on the same ground as the
`RelationKind` re-spelling above — a copied enumeration is true on the day it is written and false on
the next call site — and worse here, because most of the eight are not relation read seams at all
(`permissions.py` is the cascade, `filters/sets.py` the related-filter scope boundary,
`mutations/resolvers.py` the write path), so a complete list would be complete and misleading.

## Standing notes

- **The Layer 3 falsification had three sites, not one.** It was argued in `### Layer 3`, asserted in
  `### Decision 2`, and assumed in an `## Open questions` answer. Any future correction to a claim in
  this spec should assume the same shape: a horizon document states its positions more than once, in
  a layer section, a decision line and an open-question answer, and fixing only the argued site
  leaves the assertion standing where readers are most likely to trust it.
- **This spec owns no shipped behavior.** Every correction above moved it further from describing the
  package and closer to describing the design intent. That is the correct direction for it. If a
  future reader finds this document and the code disagreeing, the code and the owning spec win, and
  the fix is here rather than there.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[glossary]: ../../GLOSSARY.md
[glossary-definition-order-independence]: ../../GLOSSARY.md#definition-order-independence
[glossary-filterset]: ../../GLOSSARY.md#filterset
[glossary-metaprimary]: ../../GLOSSARY.md#metaprimary
[glossary-ordering]: ../../GLOSSARY.md#ordering

<!-- docs/SPECS/ -->
[spec-009]: ../spec-009-rich_schema_architecture-0_0_4.md
[spec-010]: ../spec-010-foundation-0_0_4.md
[spec-018]: ../spec-018-meta_primary-0_0_6.md
[spec-027]: ../spec-027-filters-0_0_8.md
[spec-028]: ../spec-028-orders-0_0_8.md

<!-- docs/builder/ -->
[build]: ../../builder/BUILD.md

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
