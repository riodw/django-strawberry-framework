# Rationale: spec-010 — foundation slice (deliberation, rejected alternatives)

Deliberative companion to [`spec-010-foundation-0_0_4.md`][spec-010]. The spec states the
foundation layer's contract; this file records why each part of it is shaped the way it is and which
alternatives lost.

## Scope: the foundation names seams, it does not restate their owners

Spec-010 owns the definition object, pending relations, the finalization lifecycle, the relation half
of the consumer-override contract, and the registry extensions. Filters, orders, Relay, connections,
mutations, GlobalID encoding and file/image output all hang off that layer, and all of it is visible in
the code spec-010 describes. Where a slot or a phase belongs to another document, the spec names the
seam and points at the owner rather than transplanting the paragraph: a contract told twice goes stale
in one of the tellings.

## `### Collection phase` — every auto-synthesized relation defers

Collection never consults the target's registration state
(`django_strawberry_framework/types/base.py::_build_annotations`). Once a model may carry more than one
`DjangoType`, an eager bind would freeze the annotation against whichever type was registered when the
class body executed, which is import-order-dependent schema shape.

- *Rejected: defer only when the target model already has two or more types.* The second registration
  arrives after the first bind, so at the moment of the bind the ambiguity is not observable. A rule
  that sees only the registry's current state cannot decide what depends on its final state.
- *Rejected: an eager "single registered type" fast path.* Collection runs once per class at import;
  there is no hot path to buy back, and the finalizer performs the same lookup anyway.

## `### TypeRegistry extensions` — the type map is many-valued

`_types` maps a model to a list of types so that several registrations are representable; the
foundation owns that shape, and `spec-018-meta_primary-0_0_6.md` owns the rule that picks among them.
Restating spec-018's resolution order here lost: the order, the ambiguity audit's message and the
`primary=` collision rules are one contract with one owner, and a copy in the foundation spec would go
stale while looking authoritative.

## `### TypeRegistry extensions` — registration is one atomic call

`registry.py::TypeRegistry.register_with_definition` registers and attaches the definition as one
call. A two-call sequence has a window in which a type is reachable by relation resolution with no
definition behind it, and every reader of `iter_definitions()` / `get_definition()` would have to
tolerate a half-registered type.

*Rejected: unconditional rollback of every map on failure.* `register` is idempotent for an
already-stored type, so a failed re-register with a different definition would tear down a valid
registration this call never created. Rolling back only what the call added keeps "fully succeeds or
leaves the registry untouched" true in both the fresh and the idempotent case.

## `### TypeRegistry extensions` and `## Idempotency and lifecycle contract` — the second guard and the reset

`registry.py::TypeRegistry._check_mutable` refuses every mutator once the registry is finalized, with
`clear()` the single exception. It is not redundant with `__init_subclass__`'s guard, which sees only
consumers arriving by class creation; any other route into the registry would otherwise corrupt a
finalized snapshot with no error. `clear()` runs the teardowns that registered types and loaded
subsystems announce, so each subsystem undoes its own class artifacts rather than the registry
guessing.

*Rejected: `clear()` also stripping `__strawberry_definition__` and attached resolvers.* Those
artifacts are not identity-safe to remove: Strawberry and the consumer may hold references, and a
partially un-decorated class is worse than a decorated one. The contract states its limit instead, and
tests declare fresh classes.

## `## Where the contract lives` — one store for field metadata

`DjangoTypeDefinition.field_map` and `.optimizer_hints` have no class-attribute copy. The walker
resolves them per planning entry (`django_strawberry_framework/optimizer/walker.py::_resolve_field_map`),
which is what lets a nested branch plan against the type it descends into; a class attribute is a
per-class read and would answer the wrong question at depth.

## `## Where the contract lives` — the sentinel that outlives the definition

`_is_default_get_queryset` is stamped before the `meta is None` early return, because an abstract base
that overrides `get_queryset` without declaring `Meta` returns before any definition exists, and its
concrete subclasses must still inherit the signal. A definition-only carrier cannot hold the flag for
the one class that most needs it.

- *Rejected: synthesizing a definition for `Meta`-less bases.* It would put a non-type into
  `iter_definitions()`, which every finalizer phase loops over.
- *Rejected: walking the MRO at read time and dropping the stamp.* `has_custom_get_queryset()` is
  consulted by the optimizer per relation traversal per plan; an import-time computation would become a
  planning-time one.

## `### Manual annotation contract for relation fields` — the detection rule is positive

A class-dict value counts as an override only if it is a `StrawberryField`; any other shadow of a
selected field name raises `ConfigurationError` naming the field and both supported forms
(`django_strawberry_framework/types/base.py::_consumer_assigned_fields`). An exclusionary test
("anything that is not Django's own descriptor") would accept a typo, a stray default or a plain
function as a silent override and defer the failure to schema build, where it no longer names the
field.

*Rejected: accepting `StrawberryField` plus any callable.* An undecorated method is the near-miss the
error exists to catch: the consumer meant `@strawberry.field`, and accepting it produces a field
Strawberry will not resolve.

## `### Manual annotation contract for relation fields` — one union for both branches

The four split sets and their union live on the definition, and `_build_annotations` short-circuits on
the union at both its relation and its scalar branch, so the same consumer gesture behaves the same on
either kind of column. Spec-010 asserts only that the scalar branch feeds the union; what a scalar
override may do to conversion is `spec-019-consumer_overrides_scalar-0_0_6.md`'s. Storing a set and
owning its semantics are different things.

## `### Manual annotation contract for relation fields` — where the lazy marker goes

The marker annotates the target type inside the collection parameter. Strawberry converts a lazy
reference into a `LazyType` only when the annotated type is itself a `ForwardRef`
(`strawberry/utils/typing.py::eval_type`); with the marker outside, `list["ItemType"]` is a generic
alias, the marker is discarded, and the string resolves against the declaring module. That spelling
raises `UnresolvedFieldTypeError` when the target is not importable at module scope and works when it
is, so it fails only in the case the escape hatch exists for.

*Rejected: documenting the outer spelling as a rejection path with its error.* The package rejects
nothing there (the error is Strawberry's, from an ordinary unresolvable forward reference), and pinning
an upstream message buys a suite failure on a Strawberry release for no contract gain.

## `### DjangoTypeDefinition` — reserved slots

`fields_class` is a slot whose `Meta` key is still rejected; `aggregate_class` and `search_fields` are
rejected keys with no slot. Declaring a slot before its subsystem exists guesses the shape it will
hold, and only `fields_class` has a designed shape. The spec carries a table naming each later slot's
owner rather than an inventory of the dataclass, because an inventory would be a second copy of seven
other specs' contracts.

## `### Finalization phase` — the resolution call reads the precomputed projection

The finalizer passes the owning definition's `FieldMeta` to
`django_strawberry_framework/types/converters.py::resolved_relation_annotation`, so the annotation it
writes and the metadata the optimizer plans against come from one object and cannot disagree.

*Rejected: making `field_meta` required.* The helper's other callers hold a Django field and no
definition; the keyword default keeps that path while the finalizer passes the projection.

## `### Finalization phase` — two passes, one window, two skip sets

Phase 2 attaches relation resolvers and file/image resolvers. It is the only window in which a
resolver may attach (after phase 1 settles every annotation, before `strawberry.type` freezes the
class), so every resolver-installing subsystem shares it. The relation pass skips
`consumer_assigned_relation_fields`, the file pass the broader `consumer_authored_fields`: an
annotation-only relation override still receives its generated resolver, while an annotation-only file
override must suppress the generated file resolver.

## `### Finalization phase` and `## Idempotency and lifecycle contract` — the scope of failure-atomicity

Phase 1 mutates no class object. One registry write precedes it: the per-build
`RELAY_GLOBALID_STRATEGY` snapshot, read and validated once before the loop that consumes it, so an
invalid value raises even with zero Relay types and a retry after a partial finalize cannot produce a
mixed-strategy schema (`django_strawberry_framework/types/finalizer.py::finalize_django_types`). The
spec states that write rather than an unqualified "nothing has happened yet", because `registry.clear()`
resets it precisely because it is state.

## `### Finalization phase` — the consumer-authored arm in phase 1

The arm is unreachable under the documented call graph: `_build_annotations` never records a pending
relation for a consumer-authored name. It stays because the invariant lives in a different function; a
future collection path that records pending for an overridden name would otherwise overwrite the
consumer's annotation with no guard between the two.

*Rejected: deleting it as dead code.* Keeping three unreachable lines costs a reader one paragraph;
deleting them turns a future collection-side change into a silent consumer-override clobber.

## `## What we take from strawberry-graphql-django` — third-party line citations

Pinned upstream snapshots cannot move, so a line number is the most precise address for them; in-repo
source moves under the repository's own commits and is cited by symbol. Converting the third-party
citations would replace exact addresses with vaguer ones.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->
[spec-010]: ../spec-010-foundation-0_0_4.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
