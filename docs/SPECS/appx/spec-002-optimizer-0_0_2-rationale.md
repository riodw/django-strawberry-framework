# Rationale: spec-002 — Optimizer & reverse-relation resolution (deliberation, rejected alternatives)

Deliberative companion to [`spec-002-optimizer-0_0_2.md`][spec-002]. The spec is the contract; this
file records why the optimizer is shaped as it is. The spec has no numbered Decisions, so each entry
is keyed to a spec section.

## Why the optimizer is its own document

Bears on [Problem statement][spec-002-problem] and [Purpose][spec-002-purpose].

A type layer that resolves relations across the ORM graph is broken by default without an N+1
answer, and the two problems that define this subsystem (reverse managers are not iterable; planning
must see the selection tree before relation resolvers run) share one seam: getting from Strawberry
field resolution to the Django relation. That seam is the optimizer's, so the optimizer family has
its own specs and [`spec-001`][spec-001] keeps the type-system pieces the optimizer consumes.

## Why this spec records the family at a high level only

Bears on [Purpose][spec-002-purpose].

Nested prefetch chains (O4) are specified in [`spec-003`][spec-003], and later optimizer surfaces in
`spec-004`, `spec-033`, and `spec-035`. This spec names the behavior that holds and the spec that owns
it, and never restates another spec's rules: a parent spec that summarizes its children carries a
second copy of every rule, which goes stale in one place and not the other.

## Why generated relation resolvers are not subsumed by the optimizer

Bears on [Architecture decision][spec-002-architecture].

A root-gated planner that already attaches `select_related` / `prefetch_related` looks as if it makes
per-relation resolvers redundant. It does not, on two independent conditions the package cannot
control:

- **The optimizer can be absent.** [`DjangoOptimizerExtension`][glossary-djangooptimizerextension] is
  an extension the consumer adds to the schema; a schema without it is supported, and every relation
  field must still resolve.
- **A relation can be unplanned with the optimizer installed.** A relation reached by any path the
  root plan did not cover arrives with nothing prefetched.

The resolver layer is therefore the correctness floor the planner sits on, which is why the spec
states the two conditions as a requirement on the resolvers. The resolvers also host the B2/B3
runtime sentinels that later optimizer behavior reads.

## Why a consumer-declared resolver wins

Bears on [Shipped slices][spec-002-shipped], O1.

A consumer who assigns a resolver to a relation field has stated the field's behavior, so the
generated resolver must not replace it. The skip set is
`DjangoTypeDefinition.consumer_assigned_relation_fields`, passed to
`django_strawberry_framework/types/resolvers.py::_attach_relation_resolvers`; the file/image twin
`_attach_file_resolvers` takes the broader `consumer_authored_fields`, so an annotation-only override
also wins there.

- **A per-field `only()` opt-out in this spec.** Not this spec's contract: `Meta.optimizer_hints` with
  `OptimizerHint` ([`spec-004`][spec-004] B4) covers it, with positive overrides as well as opt-out, and
  the scope rule keeps another spec's option out of this one.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[glossary-djangooptimizerextension]: ../../GLOSSARY.md#djangooptimizerextension

<!-- docs/SPECS/ -->
[spec-001]: ../spec-001-django_types-0_0_1.md
[spec-002]: ../spec-002-optimizer-0_0_2.md
[spec-002-architecture]: ../spec-002-optimizer-0_0_2.md#architecture-decision
[spec-002-problem]: ../spec-002-optimizer-0_0_2.md#problem-statement
[spec-002-purpose]: ../spec-002-optimizer-0_0_2.md#purpose
[spec-002-shipped]: ../spec-002-optimizer-0_0_2.md#shipped-slices
[spec-003]: ../spec-003-optimizer_nested_prefetch_chains-0_0_2.md
[spec-004]: ../spec-004-optimizer_beyond-0_0_3.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
