# [Definition-order independence][glossary-definition-order-independence]

Deliberation, rejected alternatives, and this spec's change record live in the companion file [`spec-008-definition_order_independence-0_0_4-rationale.md`][spec-008-rationale]: the per-line tours of the two upstream implementations, the Pros and Cons weighed for each, the criteria the design was judged against, the four candidate designs and why three lost, the four candidate finalization triggers and the leading one the implementation rejected, and the four sets of open questions this spec once asked with the answers each received.

## Problem
Eager relation resolution at class-definition time cannot represent a bidirectional Django model graph.

The eager pipeline this design had to replace resolved relation targets during `DjangoType` subclass creation:

1. `DjangoType.__init_subclass__` selects Django fields.
2. Annotation building dispatches relation fields through a relation converter.
3. The converter immediately asks the registry for `field.related_model`.
4. If the related model has no registered [`DjangoType`][glossary-djangotype], [`ConfigurationError`][glossary-configurationerror] is raised.

Under that pipeline a bidirectional model graph cannot be represented as one rich `DjangoType` per model without careful ordering or field omission. For example:

- `ItemType.category` requires `CategoryType` to already exist.
- `CategoryType.items` requires `ItemType` to already exist.

Both cannot be true at Python class-definition time.

## Why this matters for the goal
`GOAL.md` defines the destination as a DRF-shaped, `class Meta`-driven Strawberry/Django framework that recreates the practical capabilities of `django-graphene-filters` without carrying Graphene runtime dependencies.

Definition-order independence is not just a convenience feature. It is a foundation requirement for that goal.

The end state this foundation has to support:

- `Meta.fields = "__all__"` on rich primary model types
- concrete related `DjangoType`s for automatic relation fields
- root and nested connection fields
- related filters
- related orders
- related aggregates
- fieldsets
- cascade permissions
- [Relay node][glossary-relay-node-integration] lookup
- automatic optimizer planning across nested selections
- cookbook-style schemas with minimal resolver boilerplate

All of those features assume that the package can build a stable graph of model-backed types before the GraphQL schema is served. Under eager relation resolution, users must choose between declaration-order workarounds, omitted relation fields, generic fallback types, or manual annotations for every cycle — which undercuts the package's core goal: a Django-native, model-driven schema authoring experience.

The design question is therefore broader than "how do we avoid one import-order error?" It is five questions at once:

- how do we let users declare normal Django model graphs naturally?
- how do we preserve concrete rich relation types?
- how do we finalize those types safely in Strawberry?
- how do we keep optimizer, filters, orders, aggregates, permissions, and connection fields aligned with the finalized graph?
- how do we fail loudly when the schema is incomplete?

## Package behavior before this decision
The eager pipeline lived across:

- `django_strawberry_framework/types/base.py`
- `django_strawberry_framework/types/converters.py`
- `django_strawberry_framework/registry.py`

Its behavior is intentionally fail-loud:

- relation target types must be declared first
- one `DjangoType` may register per Django model
- unresolved relation targets raise during type creation

That is simple and safe, and it blocks fully automatic bidirectional schemas for normal Django model graphs.

Fail-loud is not the part to give up. The goal is not to replace fail-loud errors with silent degradation; it is to move the failure point from "too early, during class creation" to "late enough to allow imports to complete, but still before schema construction or serving."

Eager resolution also gives the optimizer a useful invariant: relation fields point to concrete registered target types. Any acceptable design must preserve that invariant after finalization.

## Prior art: Graphene-Django
Graphene-Django solves definition-order independence with lazy relation fields.

Its relation converters do not return the target Graphene object type. They return a `graphene.Dynamic` placeholder closing over the Django `related_model`, which resolves the target through `registry.get_type_for_model(model)` during Graphene schema construction — after more modules have had a chance to import and register their `DjangoObjectType` classes. Bidirectional graphs therefore work in either declaration order, and relation fields still become the concrete related type when one is registered.

The cost of that design is the failure mode: when a target type was never imported or registered by schema-construction time, the dynamic function returns nothing and Graphene silently omits the field from the schema. Import order can therefore change the public schema shape without raising.

The per-line source tour of the `Dynamic` mechanism, and the full Pros / Cons weighing of the approach, are in [the rationale][spec-008-rationale].

### Relevance to this package
Graphene-Django proves that automatic concrete relation typing and declaration-order independence can coexist. That is the most important lesson to carry forward.

The parts this package borrows are conceptual:

- relation declarations may be recorded before their target type is available
- a model/type registry can resolve those declarations later
- schema construction is a natural boundary for final validation
- concrete target types are preferred over generic placeholders

The parts it avoids are implementation-specific:

- `graphene.Dynamic`
- Graphene's field mounting lifecycle
- silent field skipping
- dependency on Graphene's old schema builder

Graphene-Django is evidence for the desired behavior, not an implementation substrate.

## Prior art: Strawberry-Django
Strawberry-Django solves the problem differently. It does not generally perform eager model-to-type lookup for relation fields. It has two effective relation modes.

**Explicit annotation mode.** A consumer annotates the relation with the concrete target type and relies on Python's postponed annotations plus Strawberry's annotation resolver: `StrawberryAnnotation` stores the declaring module's namespace, so a forward reference written on either side of a cycle resolves later. Rich cyclic graphs work, at the cost of the consumer writing every relation annotation by hand.

**`auto` mode.** Under `strawberry.auto`, `fields="__all__"`, or a selected field with no explicit annotation, relation fields map to generic fallbacks — `ForeignKey` to `DjangoModelType`, reverse FK to `list[DjangoModelType]`, and relay-configured relations to `relay.Node` or lists of it. No concrete related type is needed, so declaration order never matters; the trade-off is that the automatic path exposes only the generic shape, and nested querying through it is limited.

The per-line source tour of the annotation-namespace and field-post-processing machinery, the two mode examples, and the full Pros / Cons weighing of the approach are in [the rationale][spec-008-rationale].

### Relevance to this package
Strawberry-Django proves that Strawberry can support cyclic graphs through annotation namespaces, postponed annotations, and post-processing of Strawberry fields. Those mechanics are the ones worth borrowing.

The parts this package borrows are implementation patterns:

- namespace-aware annotation handling
- preserving user-authored annotations
- injecting generated annotations before Strawberry finalization
- custom Strawberry field classes with Django metadata
- field post-processing after `strawberry.type`
- async-safe resolver and queryset handling

The parts it avoids as the default public behavior are product choices that do not match this package's goal:

- requiring explicit annotations for ordinary rich relations
- using generic `DjangoModelType` or `relay.Node` fallback for automatic relation fields
- making decorator-first type declarations the primary API

Explicit annotations remain an escape hatch. They are not required for the normal [`Meta.fields`][glossary-metafields] `= "__all__"` path.

## Design options for this package
This package has a DRF-shaped goal: consumers should be able to declare model-backed GraphQL types with `class Meta` and get useful relation fields without writing every relation annotation by hand.

The thirteen criteria the four candidate designs were judged against are recorded in [the rationale][spec-008-rationale].

### Features that depend on this decision
Definition-order independence is the shared foundation for later systems, and every one of them makes the same demand of it — a stable, concrete relation graph available before the schema is built:

- [`DjangoConnectionField`][glossary-djangoconnectionfield] needs the target node and nested relation types to be concrete before argument and return types are built.
- [`DjangoNodeField`][glossary-djangonodefield] needs a finalized primary type per model for Relay lookup.
- related filters need stable related model/type metadata.
- related orders need stable relation paths and generated input types.
- related aggregates need stable related aggregate class graphs and output types.
- fieldsets need generated fields that point back to Django model metadata.
- cascade permissions need a predictable graph of relation fields.
- the optimizer needs to know when a selected field is a forward relation, reverse relation, many-to-many relation, or scalar.

Six of the eight are built on this foundation and shipped in the alpha line; related aggregates and fieldsets are Beta cards and make the same demand when they land. If this layer is weak, every later rich-schema subsystem needs its own workaround.

### Option 1: Keep eager resolution
Keep the eager pipeline unchanged.

### Option 2: Strawberry-Django-style explicit relation annotations
Allow or require consumers to provide explicit relation annotations when they want rich cyclic relations.

### Option 3: Generic relation fallback
When the related `DjangoType` is not registered, emit a generic relation type similar to Strawberry-Django's `DjangoModelType`.

### Option 4: Graphene-style deferred relation resolution
Record unresolved relation fields during `DjangoType` class creation and resolve them after all relevant `DjangoType`s are registered, before or during Strawberry schema construction.

The Pros and Cons weighed for each of the four options, and the reason each of the three rejected ones lost, are recorded in [the rationale][spec-008-rationale].

## The decision
Option 4 wins: a Graphene-style deferred relation model adapted to Strawberry's type lifecycle. [`spec-010-foundation-0_0_4.md`][spec-010] narrows it into one shippable slice and is the contract for everything that slice ships.

The behavior this decision fixes:

- `DjangoType` class creation does not raise just because a related model has not registered yet.
- The package still fails loudly before serving a schema if an exposed relation target remains unresolved.
- Resolved relation fields become the concrete target `DjangoType`, never a generic placeholder.
- Explicit user annotations remain available as an escape hatch.
- The optimizer continues to see concrete registered target types for selected relations.
- Rich-schema systems read one shared finalized model/type graph.

### The finalization trigger
An explicit consumer call to [`finalize_django_types()`][glossary-finalize-django-types] is the trigger this decision chose. The alternative — finalizing implicitly, inside the rich-schema field and schema constructors — was weighed and not adopted, so the explicit call is the ordinary path rather than a hatch beside a set of implicit triggers. Which constructors do not finalize, and the package-wide guarantee that none of them does, are [`spec-010`][spec-010-trigger]'s.

The pass itself — its phases, its idempotency, its single-threaded setup window, and its earliest safe call point — is [`spec-010`][spec-010-finalization]'s. The primary-type selection question this decision leaves open is answered by [`Meta.primary`][glossary-metaprimary] at `0.0.6`, in [`spec-018-meta_primary-0_0_6.md`][spec-018].

The four candidate triggers weighed here, the tradeoff recorded for each, and the four sets of questions this record asked about the registry, user annotations, generic fallback, and the rich-schema subsystems — each with the answer it eventually received — are recorded in [the rationale][spec-008-rationale].

### Hard invariants
The invariants any acceptable design must preserve are carried, with enforcement teeth and acceptance tests, by [`spec-010`][spec-010-invariants]: "Any change that violates one of them is a rejected change." The list this record set, the failure criteria that were its negation, and how each fared are in [the rationale][spec-008-rationale]. A second copy here would be a list to keep in sync, not a second guarantee.

### The shape that shipped
The collection-then-finalization split this record proposes — pending relation records written at class creation, resolved against the registry before schema construction, concrete annotations computed per relation shape and merged with user-authored ones, Django relation metadata attached for the optimizer, and a fail-loud raise naming the source model, source field, and related model — shipped whole. Its step-by-step form is in [the rationale][spec-008-rationale]; the finalization contract is [`spec-010`][spec-010-finalization]'s and what subclass creation collects is [`spec-001-django_types-0_0_1.md`][spec-001]'s.

Those three elements are the one part of the shape this record still states as a requirement: any implementation must name the source model, the source field, and the target model when it raises. That is a design constraint, not a message — the canonical wording, the message format, and the substring assertions that pin them are [`spec-010`][spec-010-error]'s, which is why spec-010 cites this section as the requirement's source rather than restating the constraint as its own. The split is deliberate and is stated in both documents.

## Acceptance criteria
The checkable acceptance inventory — the cyclic fixtures declared in either order, all six relation shapes, `Meta.fields = "__all__"` over a bidirectional graph, the unresolved-target `ConfigurationError`, optimizer plans that still see concrete targets, [schema audit][glossary-schema-audit] distinguishing unresolved targets from intentionally skipped fields, and the idempotency and isolation tests — is [`spec-010`][spec-010-acceptance]'s.

The design-gating criteria this record judged the four options against are in [the rationale][spec-008-rationale], including the one criterion the implementation deliberately made unmeetable by choosing an explicit trigger over an implicit one.

## Fakeshop implication
The fakeshop product graph is this record's chosen acceptance fixture: eight relations across four models, which eager resolution cannot represent as one rich primary type per model without omitting fields. The deferred model can, and the fixture inventory is [`spec-010`][spec-010-acceptance]'s.

The wire shape each many-side relation exposes is not this record's to state, and it has two owners rather than one. Per-field declarability through `Meta.relation_shapes` is [`spec-032-full_relay-0_0_9.md`][spec-032]'s. The default a many-side relation falls back to when no such declaration is made is [`spec-047-resource_policy-0_0_14.md`][spec-047]'s, which narrowed it as part of the bounded-output work.

## Cookbook implication
The `django-graphene-filters` cookbook recipes schema is the higher-level target outcome, and it is [`spec-009-rich_schema_architecture-0_0_4.md`][spec-009]'s: that spec names the node surface a Strawberry equivalent needs, several members of which are still unshipped Beta work.

This record's obligation stops at making the relation graph strong enough to carry filters, orders, aggregates, fieldsets, and permissions without a later redesign. It does not solve them, and it does not need to.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[glossary-configurationerror]: ../GLOSSARY.md#configurationerror
[glossary-definition-order-independence]: ../GLOSSARY.md#definition-order-independence
[glossary-djangoconnectionfield]: ../GLOSSARY.md#djangoconnectionfield
[glossary-djangonodefield]: ../GLOSSARY.md#djangonodefield
[glossary-djangotype]: ../GLOSSARY.md#djangotype
[glossary-finalize-django-types]: ../GLOSSARY.md#finalize_django_types
[glossary-metafields]: ../GLOSSARY.md#metafields
[glossary-metaprimary]: ../GLOSSARY.md#metaprimary
[glossary-relay-node-integration]: ../GLOSSARY.md#relay-node-integration
[glossary-schema-audit]: ../GLOSSARY.md#schema-audit

<!-- docs/SPECS/ -->
[spec-001]: spec-001-django_types-0_0_1.md
[spec-008-rationale]: appx/spec-008-definition_order_independence-0_0_4-rationale.md
[spec-009]: spec-009-rich_schema_architecture-0_0_4.md
[spec-010]: spec-010-foundation-0_0_4.md
[spec-010-acceptance]: spec-010-foundation-0_0_4.md#test-fixtures-and-acceptance-criteria
[spec-010-error]: spec-010-foundation-0_0_4.md#unresolved-target-error-format
[spec-010-finalization]: spec-010-foundation-0_0_4.md#finalization-phase-finalize_django_types
[spec-010-invariants]: spec-010-foundation-0_0_4.md#invariants-this-slice-must-protect
[spec-010-trigger]: spec-010-foundation-0_0_4.md#strawberry-finalization-strategy
[spec-018]: spec-018-meta_primary-0_0_6.md
[spec-032]: spec-032-full_relay-0_0_9.md
[spec-047]: spec-047-resource_policy-0_0_14.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
