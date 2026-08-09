# Spec: DjangoType Contract & Boundary

Deliberation, rejected alternatives, and this spec's change record live in the companion file [`spec-005-django_type_contract-0_0_3-rationale.md`][spec-005-rationale]: the two mechanisms predicted here and how each prediction fared, the alternatives weighed and dropped behind each decision below, the release-gating judgement an `Open questions` section once recorded, and the retracted claims of every section that has been reconciled against the shipped package.

## Problem statement

The [`DjangoType`][glossary-djangotype] pipeline generates a GraphQL type from a Django model out of a nested `Meta` class. That generator is only as trustworthy as its boundary: what it accepts, what it refuses, and what a consumer may rely on. Four failure classes corrupt that boundary, and keeping all four out of it is what this spec is for.

1. **Ambiguous model-to-type resolution.** Relation targets, and every other question of which type stands for a given model, are answered from the registry. If a model is reachable through more than one type and nothing declares which one answers, the answer falls to import order — a property that must never be part of the API contract.
2. **A promise the implementation does not keep.** A docstring, a `docs/README.md` line, or a spec sentence claiming behavior the pipeline does not deliver is worse than the missing feature itself: it costs the consumer the debugging session that discovers the gap.
3. **A silently dropped name.** A [`Meta.fields`][glossary-metafields] or [`Meta.exclude`][glossary-metaexclude] entry that matches no model field is a typo. Dropping it quietly turns a typo into a partial type — a bug with no error attached to it.
4. **A supported-looking surface that does nothing.** A `Meta` key the validator accepts but the pipeline never applies reads as shipped and is not.

The unifying thread: a Meta-driven generator must be narrow and explicit about what it accepts. Silent acceptance of unwired surfaces, silent drops of unknown names, and unlabeled hard constraints all corrupt user feedback and break the Meta-class clarity pitch the package is built around.

## Goal

Make the DjangoType contract precise and honest:

- Every knob accepted by `Meta` is either applied end-to-end or rejected with a clear error naming what it refused.
- Consumer-visible promises — override behavior, registry rules, error shapes — match the implementation. Nothing in a docstring or in `docs/README.md` says "X works" when X does not.
- A constraint the package intends to lift is labeled as temporary where the surface is published, and names what lifting it waits on.

## Non-goals

This spec does not cover filtering, ordering, aggregation, permissions, the optimizer rebuild, the `Meta.primary` mechanism itself (`docs/SPECS/spec-018-meta_primary-0_0_6.md`), or the consumer-overrides mechanism itself (`docs/SPECS/spec-010-foundation-0_0_4.md` for relation fields, `docs/SPECS/spec-019-consumer_overrides_scalar-0_0_6.md` for scalar fields). Those belong to their own specs. This spec pins only the contract shape they plug into.

## Topics

### One model, many types, one primary

A Django model may carry more than one `DjangoType`. `registry.py::TypeRegistry.register` appends each type to that model's list; the other direction stays one-to-one, so `model_for_type` resolves every registered type back to exactly one model and the optimizer can always trace a resolver's return type to a model.

Reverse lookup in the model-to-type direction needs exactly one answer per model — which type a relation binds to, which type a bare `registry.get(model)` returns — and this spec's requirement on it is that the answer never depend on import order. The mechanism that supplies it is [`Meta.primary`][glossary-metaprimary], owned by `docs/SPECS/spec-018-meta_primary-0_0_6.md`: one type per model may declare it, relation targets bind to it at finalization rather than at class creation, and this spec does not restate its rules.

**Contract.** Ambiguity is an error, never a default. Two types claiming primary for one model is rejected; several types claiming none is rejected; no path through registration or finalization breaks a tie by declaration order. A single type over a model still registers without declaring `Meta.primary` at all, so the narrow case costs a consumer nothing.

The friction argument for lifting the original one-model-one-type constraint, the `Meta.primary` design this spec predicted, the rejection of first-registered-wins, and why the two rejections above fire at different points are recorded in [the rationale][spec-005-rationale].

### Consumer override semantics

A field a consumer authors on the class body is authoritative: the generator does not synthesize over it. This holds across the whole four-corner surface — a re-annotation (`category: AdminCategoryType`, `name: str`) and an assigned `strawberry.field`, on relation fields and on scalar fields alike — and it stops there. An annotation that asks for the model-inferred type (`name: auto`, the declare-but-infer marker) is routed back into synthesis rather than overriding it: the boundary is what a consumer authored a *type* for, not everything that appears on the class body. `DjangoType.__init_subclass__` merges consumer-declared annotations on top of the synthesized ones, but the merge order is not the contract: the field name's membership in the consumer-authored set is what short-circuits synthesis, and the merge alone would leave the consumer winning only by dictionary ordering.

The mechanism is owned by its own specs — relation fields by `docs/SPECS/spec-010-foundation-0_0_4.md`, scalar fields by `docs/SPECS/spec-019-consumer_overrides_scalar-0_0_6.md` — and this spec does not restate their rules.

**Contract.** The package documents the override surface it actually delivers, and no more. A docstring or `docs/README.md` line describing override behavior is corrected or removed in the same change that shows the behavior does not hold, and a test that exists only to pin an unfulfilled promise is not left standing as if it pinned a contract.

The three candidate implementations this spec weighed before the mechanism shipped, the diagnosis they were aimed at, and the fate of the placeholder test are recorded in [the rationale][spec-005-rationale].

### Invalid `Meta.fields` and `Meta.exclude` names

`_select_fields` validates that every name in `Meta.fields` or `Meta.exclude` corresponds to a real field on [`Meta.model`][glossary-metamodel]. Unknown names raise [`ConfigurationError`][glossary-configurationerror] whose message names the model, lists the unknowns, and lists the available fields so typos are obvious. Implementation lives in `django_strawberry_framework/types/base.py`; tests in `tests/types/test_base.py` (`test_meta_fields_unknown_name_raises`, `test_meta_fields_unknown_name_includes_model_and_available`, `test_meta_exclude_unknown_name_raises`).

This rule is final. The error shape — model + unknowns + available — is part of the public contract: a consumer can rely on every `ConfigurationError` from this code path naming both the bad input and the valid surface.

The shape is not this section's alone. `types/base.py::_format_unknown_fields_error` is its single source, and every later `Meta` key whose value names model fields reuses it, so `Meta.optimizer_hints`, `Meta.nullable_overrides` / `Meta.required_overrides`, `Meta.filesystem_path_fields`, and `Meta.relation_shapes` all owe a consumer the same message shape. A new field-naming key adopts that helper rather than formatting its own.

### Accepted vs deferred Meta keys

The Meta validator partitions every key a consumer declares on its own `Meta` into one of three buckets:

- **Accepted** — the key's feature is shipped and applied. `types/base.py::ALLOWED_META_KEYS` is the authoritative set; `docs/GLOSSARY.md` carries the per-key status and usage. This spec names neither roster on purpose: a roster restated here is a second source of truth that goes stale silently, which is exactly what this section exists to prevent.
- **Deferred** — the key is reserved for a feature that has not shipped. `types/base.py::DEFERRED_META_KEYS` holds them, and `_validate_meta` raises a `ConfigurationError` naming the offending keys and saying the feature that owns them has not shipped. The message names a *feature*, never a spec document: a consumer reading an exception has no access to `docs/SPECS/`.
- **Unknown** — anything in neither set raises a typo-guard `ConfigurationError` listing the bad keys.

The promotion rule from deferred to accepted is **strict**: a key moves only when both of these are true.

1. The validator accepts it.
2. The pipeline applies it to the resulting class / type end-to-end.

A key that is validated but never applied is a bug — failure class 4 of `## Problem statement`, and the reason this rule has teeth. The reverse is fine: a key applied through a different mechanism — consumers subclassing `relay.Node` directly, for example — needs no `Meta` key at all.

A key may also enter as accepted **without ever having been deferred**, when its feature ships in the same change that adds the key. There is no promotion to make in that case, and the rule is satisfied trivially rather than waived; the distinction is worth keeping visible so a net-new accepted key is never mistaken for a promotion whose end-to-end check was skipped.

[`Meta.interfaces`][glossary-metainterfaces] is the key this partition is checked against most often, because it has occupied two of the three buckets. It is accepted today and applied end-to-end — validated by `types/base.py::_validate_interfaces` and injected into the generated type's bases by the finalizer's `apply_interfaces` step — and `tests/types/test_base.py::test_interfaces_is_shipped_not_deferred` pins that it is not also in `DEFERRED_META_KEYS`.

## Coordination with `spec-001-django_types-0_0_1.md` and `spec-002-optimizer-0_0_2.md`

`spec-001-django_types-0_0_1.md` defines the pipeline: Meta validation, scalar synthesis, relation conversion, choice enums, the `get_queryset` hook. This spec defines the boundary of that pipeline — what is rejected, what is reserved, what consumers can and cannot rely on.

`spec-002-optimizer-0_0_2.md` defines the N+1 optimizer subsystem, whose `Prefetch` downgrade rule reads the `has_custom_get_queryset` sentinel. It is not the only reader: the finalizer consults it as the "carries any override" predicate when two `DjangoType`s bind one shared `FilterSet`, and refuses the pairing if either does. This spec covers the type-system half of that sentinel. It is stamped in `__init_subclass__` **before** the `meta is None` early return, so an abstract base that overrides `get_queryset` without declaring `Meta` still flips it for the concrete subclasses beneath it; detection is an MRO walk terminating at `DjangoType`; and the authoritative value lives on `types/definition.py::DjangoTypeDefinition.has_custom_get_queryset`, with the class variable as the pre-definition fallback.

**A new or promoted `Meta` key is checked against this spec's rule, not filed against this document.** `ALLOWED_META_KEYS` / `DEFERRED_META_KEYS` are the authoritative sets and `docs/GLOSSARY.md` is where a key's status is published; a spec that adds or promotes a key satisfies `### Accepted vs deferred Meta keys` inside its own change and lands the glossary entry there. The obligation is on the code, which is checkable against source, rather than on an edit to this file, which nothing can enforce.

## References

- `docs/SPECS/spec-001-django_types-0_0_1.md` — the implementation spec this contract spec sits on top of.
- `docs/SPECS/spec-002-optimizer-0_0_2.md` — the optimizer-side consumer of the `has_custom_get_queryset` sentinel.
- `docs/SPECS/spec-006-public_surface-0_0_3.md` — companion spec covering the package-level public-surface and documentation-discipline rules that this contract feeds into; its status-marker vocabulary cites `### Accepted vs deferred Meta keys` by title.
- `docs/SPECS/spec-018-meta_primary-0_0_6.md` — owns `Meta.primary` and the ambiguity rules `### One model, many types, one primary` requires of it.
- `docs/SPECS/spec-010-foundation-0_0_4.md` and `docs/SPECS/spec-019-consumer_overrides_scalar-0_0_6.md` — own the relation and scalar halves of the consumer-override surface.
- `tests/types/test_base.py` — pins the accepted / deferred / unknown key partition, the `Meta.fields` / `Meta.exclude` unknown-name validation, and the `has_custom_get_queryset` sentinel.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->
[glossary-configurationerror]: ../GLOSSARY.md#configurationerror
[glossary-djangotype]: ../GLOSSARY.md#djangotype
[glossary-metaexclude]: ../GLOSSARY.md#metaexclude
[glossary-metafields]: ../GLOSSARY.md#metafields
[glossary-metainterfaces]: ../GLOSSARY.md#metainterfaces
[glossary-metamodel]: ../GLOSSARY.md#metamodel
[glossary-metaprimary]: ../GLOSSARY.md#metaprimary

<!-- docs/SPECS/ -->
[spec-005-rationale]: appx/spec-005-django_type_contract-0_0_3-rationale.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
