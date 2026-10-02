# Rationale: spec-009 — rich schema architecture (deliberation, rejected alternatives)

Deliberative companion to [`spec-009-rich_schema_architecture-0_0_4.md`][spec-009]. The spec states
the layered architecture; each layer's own spec owns its shipped contract, and
[`docs/GLOSSARY.md`][glossary] catalogs the shipped surface. This file records why the architecture
is shaped the way it is and which alternatives lost.

## `### Layer 3: Finalization trigger`

The only trigger is the consumer's explicit `finalize_django_types()` call. `DjangoConnectionField`,
`DjangoNodeField` and `DjangoSchema` exist and none of them calls the finalizer.

**Rejected: constructor-triggered finalization** (`DjangoConnectionField(Type)`,
`DjangoNodeField(Type)` or `DjangoSchema(...)` finalizing before it returns). Two reasons, the first
fatal on its own.

1. *It reintroduces import-order coupling.* If constructing a connection field finalizes, whether a
   `DjangoType` is included depends on whether its module was imported before that construction. A
   trigger that fires on the first construction of any of three unrelated objects makes the
   finalization boundary implicit and position-dependent, which is the failure
   [definition-order independence][glossary-definition-order-independence] exists to remove.
2. *It puts a process-global mutation behind three constructors.* `finalize_django_types()` mutates
   a deliberately lockless registry and the classes it holds, so it is pinned to a single-threaded
   setup window. Three auto-trigger sites multiply the places that window can be violated, and no
   constructor is in a position to enforce it.

**Rejected: a schema extension as the trigger.** Extensions run after the schema is built, so a
trigger there would need post-schema patching of frozen types.

## `## Target outcome`

**Node lookup is nullable.** Node dispatch is `required=False` unconditionally (`relay.py`
#"Resolution is **nullable by contract**"), so a hidden row, a missing row and an uncoercible pk
all resolve to `null`. The alternative, raising on a row the client may not see, lost: a raise on a
hidden row is itself a disclosure, and it makes the hidden and missing cases distinguishable to the
client.

**Three `Meta` keys are refused, not reserved.** `aggregate_class`, `fields_class` and
`search_fields` sit in `types/base.py::DEFERRED_META_KEYS` and raise `ConfigurationError` at class
creation until the subsystem that applies each one end to end ships. Accepting a key nothing
applies would make it a silent no-op on the consumer's class. The target example keeps the three
keys because they are the destination this document describes, and the spec names the card that
promotes each one.

## ``#### Take `fields_class` `` and `### Layer 9: FieldSet and field-level permissions`

Field-level behavior wraps the generated resolver. Two alternatives lost.

- *Strawberry's `permission_classes`.* `BasePermission.has_permission` is class-per-policy with a
  fixed message contract, cannot express the gate-then-override cascade Layer 9 orders, and would
  synthesize one permission class per managed field.
- *A custom field class.* It is machinery whose only job would be to host a wrapper that a wrapper
  can host directly, and it charges every generated field for a feature most fields do not use.

Resolver wrapping costs nothing on an unmanaged field, keeps the cascade in one body, and is
upstream-parity. [`spec-059-fieldset-0_1_1.md`][spec-059] owns the mechanism.

## ``### Borrow `StrawberryDjangoDefinition` ``

The sketch is an explicit **subset** of `types/definition.py::DjangoTypeDefinition`. Reproducing the
dataclass field for field lost: the slots later specs added would bury the ones the section argues
for, and this spec owns none of them, so a copy would drift the first time a slot is added.

- `fields_spec` / `exclude_spec` carry the `_spec` suffix because they hold the `Meta` declaration,
  not the resolved selection (`selected_fields`); without the suffix the two read as synonyms.
- A sidecar slot is a plain `type | None`, never a lazy class reference:
  `types/base.py::_validate_filterset_class` and its `_validate_orderset_class` twin accept only an
  already-resolved subclass at class creation, so no unresolved reference reaches the slot. What
  the finalizer resolves lazily is a `RelatedFilter`'s or `RelatedOrder`'s target inside an
  already-resolved set class, never the `Meta` value itself.
- `aggregate_class` and `search_fields` have no slot, because declaring storage for a key the
  package refuses would have the dataclass and `_validate_meta` disagree about the same key.

## `### Track annotation provenance structurally, not by re-collecting annotations`

Provenance is recorded at authorship, not reconstructed afterwards: the `consumer_*_fields`
frozensets on `DjangoTypeDefinition` are derived in `types/base.py::DjangoType.__init_subclass__`
and record both that a field was consumer-authored and in which spelling. Postponed annotations are
handled by deferring `strawberry.type` to finalization, when every target type exists.

**Rejected: borrowing upstream's dataclass-MRO annotation collector**
(`strawberry_django/utils/typing.py::get_strawberry_annotations`). It would be a second provenance
system, and two independently derived answers to "where did this annotation come from" eventually
disagree. A collector re-walking the namespace can only infer what collection already knows.

## ``### Borrow `StrawberryDjangoFieldBase` and `StrawberryDjangoField` `` and `### Layer 4: Generated relation fields`

**Rejected: a package field class modelled on `StrawberryDjangoField`.** Upstream's public API is
decorator-first, so the decorator's return value is the only object it owns and every
responsibility must attach to it. This package's public API is `class Meta`, so the finalizer owns
generation and each responsibility lives at its own seam: annotation in
`types/converters.py::resolved_relation_annotation`, access in
`types/resolvers.py::_make_relation_resolver`, visibility at the queryset-owning seams, and
arguments through the synthesized resolver `__signature__` on `connection.py::DjangoConnectionField`.
The class would close no consumer-visible gap: `StrawberryDjangoField` is upstream plumbing and
graphene-django has no analogue. The risk a field class usually prevents, metadata scattered across
annotations, class attributes, closures and optimizer maps, is answered by `DjangoTypeDefinition`
being the one object every seam reads.

Resolver generation is permanent, not transitional: a relation field cannot be generated at class
creation (its target may not exist) or after `strawberry.type` (the type is frozen), so finalizer
Phase 2 is the only window.

## ``### Borrow `resolve_type`, but change relation fallback behavior``

No placeholder tier exists, as a default, an internal reserve or an opt-in; an unresolved target
raises at finalization (`types/finalizer.py::_format_unresolved_targets_error`). Upstream's
`DjangoModelType` is a pk-only placeholder and graphene-django's counterpart silently skips the
field; a weaker schema is not a missing capability. **Rejected: keeping a reserved internal tier "in
case".** It is a documented promise a subsystem could be designed against, which
`### The unresolved-relation contract is error-only` rules out.

## ``### Borrow `field` and `connection` as implementation patterns``

**Rejected: a `DjangoField(...)` advanced-field factory.** It is the decorator-first surface wearing a
factory's clothes. Its capabilities ship split across `DjangoListField` (graphene-django's symbol, so
that migration site needs no shape change), `DjangoConnectionField`, `DjangoNodeField` and plain
`@strawberry.field`. Filter and order arguments on a bare non-connection list exist in one upstream
library only, which makes them optional by the both-libraries rule. Renaming the factory keeps the
objection; the problem is the surface, not the name.

## `### Keep the current optimizer's strengths, and borrow its nested-prefetch lessons`

**Rejected: an upstream-style field-level optimizer store** with request-scoped callable hints.

1. graphene-django ships no optimizer, so the store is single-library and optional.
2. A callable hint is forbidden, not merely unbuilt: `optimizer/hints.py::OptimizerHint` pins that
   strategy selection never depends on request-varying data, which is what makes the cross-request
   plan cache sound. Request-varying shaping belongs to `get_queryset`, which runs per request.
3. The store's role is filled by frozen `OptimizerHint` directives plus a whole-query
   `OptimizationPlan`.

Annotation dependencies as an optimizer input belong to `FieldSet`'s `Meta.depends_on`
(`TODO-BETA-059-0.1.1`).

## ``### Borrow `DjangoListConnection` ``

**`totalCount` is opt-in per type** (`Meta.connection = {"total_count": True}`) because a count is a
second query, and a base that declares the field makes every connection pay for it. Every node type
resolves through a generated concrete `<TypeName>Connection` subclass
(`connection.py::_connection_type_for`); the opt-in decides only whether that subclass carries the
member. The subclass is required: a bare generic alias loses the `resolve_connection` override at
Strawberry's generic specialization. `aggregates` lands through the same mechanism for the same
reason.

## `### Layer 6: Filter system`

The base is `FilterSet`, not the reference's `AdvancedFilterSet`: it subclasses django-filter's own
`BaseFilterSet`, so a DRF-shaped surface reads as the class a consumer already has, and an `Advanced`
prefix would signal a distinction that does not exist. Unshipped classes follow the same `*Set`
convention (`AggregateSet`, `FieldSet`). `Meta.fields` is canonical because it is django-filter's key;
`filters/sets.py::FilterSetMetaclass.__new__` aliases `Meta.filter_fields` onto it when `fields` is
absent, for cookbook parity, and documenting the alias as primary would teach two vocabularies.
Graphene class names that refer to the upstream reference (`AdvancedAggregateSet`,
`AdvancedFieldSet`, the `file:///` citations) name real upstream classes and stay.

## `### Layer 7: Order system`

**Rejected: `ASC_DISTINCT` / `DESC_DISTINCT` directives and `DISTINCT ON`.** The shipped six-member
[`Ordering`][glossary-ordering] enum matches `strawberry_django/ordering.py::Ordering` member for
member; graphene-django has no DISTINCT directives, and the reference-only members are optional by
the both-libraries rule. The problem they addressed, a to-many join fanning out parent rows, is
solved by annotating `Min(path)` for ascending terms and `Max(path)` for descending and ordering by
the alias (`orders/sets.py` #"models.Min if direction.is_ascending else models.Max"): one row per
parent, `totalCount` uninflated, NULL positioning preserved. The annotation composes with the
connection's primary-key tiebreaker; `DISTINCT ON`'s leftmost-expression constraint fights the
cursor ordering. Keeping the directives as an opt-in lost: two orderings producing the same rows by
different SQL are two contracts, one of them broken under pagination.

## `### Layer 2: Pending relation registry`

`types/relations.py::PendingRelation` carries no relation kind and no nullability. Finalization reads
both from the owning definition's `field_map`, so the annotation the finalizer writes cannot disagree
with the metadata the optimizer plans against.

## `## Module layout` and `## Build order`

Multi-module subsystems are packages because the package layout fixes import paths, public-surface
promotion and test-tree mirroring. The build order names a card for each unshipped phase and no
version for a shipped one: a card for open work has one owner, while a shipped-version annotation
would be a second, unowned copy of the board.

## ``### Should plain `strawberry.Schema` remain fully supported?``

Finalization lives in no schema or field object, so the read surface needs nothing from
`DjangoSchema`. Generated mutations do: graphql-core completes a payload only after the resolver
returns, so only an execution context can hold the write transaction open through completion and
roll back an unserializable payload (`schema.py::DjangoMutationExecutionContext`). The write
pipeline refuses to run outside that window rather than commit behind a `data: null` response.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[glossary]: ../../GLOSSARY.md
[glossary-definition-order-independence]: ../../GLOSSARY.md#definition-order-independence
[glossary-ordering]: ../../GLOSSARY.md#ordering

<!-- docs/SPECS/ -->
[spec-009]: ../spec-009-rich_schema_architecture-0_0_4.md
[spec-059]: ../spec-059-fieldset-0_1_1.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
