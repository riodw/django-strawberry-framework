# Rationale: spec-008 — definition-order independence (deliberation, rejected alternatives)

Deliberative companion to [`spec-008-definition_order_independence-0_0_4.md`][spec-008]. The spec
states the problem and the decision; [`spec-010`][spec-010] owns every shipped contract. This file
records the weighing behind the decision.

## Prior art: Graphene-Django

Spec: [Prior art: Graphene-Django][spec-008-graphene].

Graphene-Django's relation converters return a `graphene.Dynamic` placeholder
(`graphene_django/converter.py::convert_field_to_djangomodel` and its two siblings) that resolves
the target through `graphene_django/registry.py::Registry.get_type_for_model` while the schema
builds, after every module has registered.

- **Pros.** Bidirectional graphs in either declaration order; relation fields stay the concrete
  related type; no generic fallback object.
- **Cons.** A never-registered target becomes a silently skipped field; errors move from class
  creation to schema build; the placeholder relies on Graphene's field-mounting lifecycle, which
  Strawberry does not have; the registry must tolerate incomplete graphs.
- **What the package took.** The pattern, not the substrate: a sentinel annotation
  (`django_strawberry_framework/types/relations.py::PendingRelationAnnotation`) that the finalizer
  rewrites in place, the later error point, and a registry that tolerates pending records until
  finalization. The silent skip is refused outright.

## Prior art: Strawberry-Django

Spec: [Prior art: Strawberry-Django][spec-008-strawberry].

Strawberry-Django resolves cycles through hand-written annotations whose declaring-module namespace
`StrawberryAnnotation` keeps (`strawberry_django/utils/typing.py::get_strawberry_annotations`), and
under `auto` maps relations to generic types (`ForeignKey` to `DjangoModelType`, reverse FK to
`list[DjangoModelType]`).

- **Pros.** Fits Strawberry's annotation-driven design; explicit annotations support rich cycles;
  `auto` never blocks type creation.
- **Cons.** Automatic relations do not become the concrete related type; rich relations must be
  annotated by hand; `fields="__all__"` does not produce a rich graph; a generic type limits nested
  querying.
- **What the package took.** Namespace-aware annotation handling and the post-`strawberry.type`
  field rewrite. The generic fallback is not taken: automatic relations resolve to the concrete
  related `DjangoType`, and no generic relation type exists in the package.

## Design criteria

Spec: [Design options for this package][spec-008-options].

The four options are judged against thirteen criteria: cookbook-style rich schemas; fakeshop-style
bidirectional graphs; concrete related `DjangoType`s by default; a useful `Meta.fields = "__all__"`;
failing loudly before an incomplete schema is served; no Graphene runtime dependency; no generic
placeholder as the default shape; working with Strawberry's type lifecycle; explicit annotations as
an override path; concrete relation metadata for the optimizer; a foundation for related filters,
orders, aggregates, fieldsets, permissions, and connections; minimal boilerplate; and no fragile
post-schema mutation where a pre-schema lifecycle is possible. Six of them prohibit the two upstream
shapes, and they come from `GOAL.md`, which is why Options 1 to 3 cannot win.

## Options 1 to 4

Spec: [Option 1][spec-008-option1], [Option 2][spec-008-option2], [Option 3][spec-008-option3],
[Option 4][spec-008-option4].

- **Option 1, eager resolution, loses by definition.** It cannot expose both `Category.items` and
  `Item.category` on the primary types, which is the problem statement. Its virtues survive in the
  winner: failure is still loud, and the optimizer still sees concrete targets, after finalization.
- **Option 2, explicit annotations, loses against the DRF-first goal.** It also leaves
  `Meta.fields = "__all__"` needing a fallback, so it relocates the problem rather than solving it.
  Its mechanisms survive as the escape hatch: same-module string annotations,
  `from __future__ import annotations`, cross-module `Annotated[..., strawberry.lazy(...)]`, and
  annotation-only overrides that keep the generated resolver.
- **Option 3, generic fallback, loses to the fail-loud invariant.** A schema that silently degrades
  from a rich relation type to a generic placeholder is the failure the invariants refuse, so the
  fallback does not exist even as an emergency hatch; unresolved exposed relations raise instead.
- **Option 4, deferred resolution, wins.** Its stated costs are the shipped structure: a
  pending-relation registry (`django_strawberry_framework/types/relations.py::PendingRelation` and
  `django_strawberry_framework/registry.py::TypeRegistry.add_pending_relation`), errors at
  finalization, type definitions rewritten in place by the finalizer, and placeholder annotations
  until targets resolve.

## The finalization trigger

Spec: [The finalization trigger][spec-008-trigger].

Four triggers were weighed: delaying `strawberry.type` until targets resolve; finalizing immediately
and patching `__strawberry_definition__.fields`; a package helper that finalizes before the schema is
built; and a hybrid in which the connection field, the node field, and a schema constructor each
finalize implicitly, with `finalize_django_types()` as a hatch.

- **The hybrid is rejected.** If several constructors may each be the one that finalizes, the
  finalization point depends on which field a consumer declared first: import-order dependence
  re-entering through the trigger. The explicit call costs one documented line of setup and buys a
  single point where the graph is known complete.
- **Nothing finalizes implicitly.** `DjangoSchema` exists for unrelated contracts (mutation
  atomicity, error policy) and does not finalize; neither do the connection and node fields.
- **Patching after `strawberry.type`.** Rejected as the default: it couples the package to Strawberry
  internals where a pre-schema lifecycle is available.

## How the rest of the design sits on the decision

Spec: [The decision][spec-008-decision] and [Features that depend on this decision][spec-008-features].

- **Registry.** Several types may share a model; [`spec-018`][spec-018]'s `Meta.primary` names the
  one automatic relations bind to, ambiguity is a configuration error raised at finalization (a
  registration-time raise would depend on import order), and pending records live beside finalized
  ones on the same registry.
- **User annotations.** A consumer-authored relation annotation overrides synthesis and may target a
  non-primary type. Validating that a manual annotation matches the Django relation's cardinality is
  a published deferral in the glossary, not a silent gap.
- **Rich-schema subsystems.** Each consumes the one finalized graph rather than keeping its own
  relation map: filtersets and ordersets bind during finalization against the same definitions the
  optimizer and cascade permissions read. A `Meta` key's slot arrives with the feature that uses it,
  never reserved up front, so `DjangoTypeDefinition` carries no dead fields for unshipped features
  beyond the reserved `fields_class`.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->
[spec-008]: ../spec-008-definition_order_independence-0_0_4.md
[spec-008-decision]: ../spec-008-definition_order_independence-0_0_4.md#the-decision
[spec-008-features]: ../spec-008-definition_order_independence-0_0_4.md#features-that-depend-on-this-decision
[spec-008-graphene]: ../spec-008-definition_order_independence-0_0_4.md#prior-art-graphene-django
[spec-008-option1]: ../spec-008-definition_order_independence-0_0_4.md#option-1-keep-eager-resolution
[spec-008-option2]: ../spec-008-definition_order_independence-0_0_4.md#option-2-strawberry-django-style-explicit-relation-annotations
[spec-008-option3]: ../spec-008-definition_order_independence-0_0_4.md#option-3-generic-relation-fallback
[spec-008-option4]: ../spec-008-definition_order_independence-0_0_4.md#option-4-graphene-style-deferred-relation-resolution
[spec-008-options]: ../spec-008-definition_order_independence-0_0_4.md#design-options-for-this-package
[spec-008-strawberry]: ../spec-008-definition_order_independence-0_0_4.md#prior-art-strawberry-django
[spec-008-trigger]: ../spec-008-definition_order_independence-0_0_4.md#the-finalization-trigger
[spec-010]: ../spec-010-foundation-0_0_4.md
[spec-018]: ../spec-018-meta_primary-0_0_6.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
