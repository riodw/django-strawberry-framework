# Rationale: spec-001 — DjangoType foundation (deliberation, rejected alternatives)

Deliberative companion to [`spec-001-django_types-0_0_1.md`][spec-001]. The spec is the contract;
this file records why the foundation is shaped as it is. The spec has no numbered Decisions, so each
entry is keyed to a spec section.

## Why type generation and the optimizer share one foundation

Bears on [Goal][spec-001-goal] and [N+1 strategy][spec-001-n1].

An N+1 fix cannot be specced in isolation: the problem exists only once a type system resolves
relations across the ORM graph, and the `get_queryset` + `Prefetch` rule is what keeps per-type
visibility filtering intact across joins. A type layer shipped without it is broken by default, so
the foundation names the optimizer and the shape the type system owes it.

- **Two specs in lockstep from the start.** Rejected: the type layer would have shipped broken until
  its partner landed.
- **Where the cut falls.** The optimizer's architecture and implementation belong to
  [`spec-002`][spec-002] and its family. This spec keeps what only the type system can answer:
  `has_custom_get_queryset()` (the planner asks; only the type knows), the cardinality rules the type
  system is planned against, and the reasons for the downgrade and projection rules, which no
  optimizer spec states.

## Why illustrative code names consumer surface only

Bears on [DjangoType][spec-001-djangotype], [Registry][spec-001-registry], and
[Files to add][spec-001-files].

The `Meta` examples illustrate the consumer surface this spec owns. Package internals are cited by
`path::QualifiedName` instead of reproduced: an illustrative copy of `TypeRegistry`'s methods or of
`SCALAR_MAP` is a second copy of the source that nothing keeps in sync.

## Scalar field conversion

Spec: [Scalar field conversion][spec-001-scalars].

- **`typing.Any` for an unmapped field type.** Rejected: a silent `Any` masks an unsupported column
  at schema-build time and surfaces it later as an opaque type error (Strawberry has no native `Any`
  scalar), where `ConfigurationError` fails fast with the field path and a one-line fix.

## Choice field enum generation

Spec: [Choice field enum generation][spec-001-enums].

- **Label-based member names.** Labels often read better (`"Active"` -> `ACTIVE`) than opaque
  values (`"M"`, `1` -> `MEMBER_1`). Rejected: labels are display strings consumers translate or
  restyle, and coupling the schema to them is fragile. The `MEMBER_<digit>` prefix is the accepted
  cost. This is parity, not divergence: graphene-django (`graphene_django/converter.py::get_choices`)
  and strawberry-graphql-django both build member names from the value and use the label only as the
  member description.
- **Why import order picks the enum name.** The cache is keyed on `(model, field_name)` so two types
  over one column share one enum; the first type to read the column names it. The spec states the
  consequence as consumer instruction (declare the type you want to win first).

## Relation field conversion and the registry

Spec: [Relation field conversion][spec-001-relations] and [Registry][spec-001-registry].

Three ways to make definition order irrelevant were weighed: `Annotated["T", strawberry.lazy(...)]`
for cross-module references, string annotations rewritten once every sibling registers, and
registry-tracked pending relations resolved by a pass over every collected type. The package takes
the third: subclass creation records a `PendingRelation`, and `finalize_django_types()` resolves
every target after all types exist, so the consumer writes no annotation at all. A consumer who does
write a string or stringified annotation keeps it, because a consumer-authored field skips deferral.

## `get_queryset`

Spec: [`get_queryset`][spec-001-getqueryset].

The sentinel is computed by walking the MRO to `DjangoType`, and stamped before the `Meta`-absent
early return, so an abstract scoping base that declares `get_queryset` without a `Meta` is visible
through its concrete subclasses. A `"get_queryset" in cls.__dict__` test on the subclass alone would
silently drop exactly the shared-scoping base the abstract-intermediate rule invites consumers to
write.

## N+1 strategy

Spec: [N+1 strategy][spec-001-n1].

- **The downgrade exists because a join bypasses visibility.** strawberry-graphql-django hit this in
  issue #572 and fixed it in PR #583: a `select_related` join to a target type with a custom
  `get_queryset` returns rows the hook would exclude. Converting it to a `Prefetch` over the target's
  filtered queryset closes the leak.
- **A projection over a join keeps the local FK column.** Masking it makes Django treat the joined
  attributes as deferred and re-query on first access, the N+1 the projection exists to remove
  (`django_strawberry_framework/optimizer/plans.py #"including the FK columns required to materialize"`).
- **Visibility is applied to every queryset the planner builds.**
  `django_strawberry_framework/optimizer/walker.py::_build_child_queryset` applies the target's
  `get_queryset` to the child queryset of every planner-built `Prefetch`, independent of why the
  prefetch branch fired. The claim is bounded to planner-built querysets on purpose: a
  consumer-supplied `Prefetch` hint is taken as authoritative and appended as given
  (`django_strawberry_framework/optimizer/walker.py::_apply_hint #"if hint.prefetch_obj is not None:"`).
- **Why the callable-factory opt-in.** The factory hands Strawberry the same instance per operation,
  preserving the instance-bound plan cache, and avoids Strawberry's warning on a bare instance in
  `extensions=`.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->
[spec-001]: ../spec-001-django_types-0_0_1.md
[spec-001-djangotype]: ../spec-001-django_types-0_0_1.md#djangotype
[spec-001-enums]: ../spec-001-django_types-0_0_1.md#choice-field-enum-generation
[spec-001-files]: ../spec-001-django_types-0_0_1.md#files-to-add
[spec-001-getqueryset]: ../spec-001-django_types-0_0_1.md#get_queryset
[spec-001-goal]: ../spec-001-django_types-0_0_1.md#goal
[spec-001-n1]: ../spec-001-django_types-0_0_1.md#n1-strategy
[spec-001-registry]: ../spec-001-django_types-0_0_1.md#registry
[spec-001-relations]: ../spec-001-django_types-0_0_1.md#relation-field-conversion
[spec-001-scalars]: ../spec-001-django_types-0_0_1.md#scalar-field-conversion
[spec-002]: ../spec-002-optimizer-0_0_2.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
