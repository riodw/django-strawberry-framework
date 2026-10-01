# Rationale: spec-005 — DjangoType contract and boundary (deliberation, rejected alternatives)

Deliberative companion to [`spec-005-django_type_contract-0_0_3.md`][spec-005]. The spec is the
contract; this file records why the boundary is drawn where it is. The spec has no numbered
Decisions, so each entry is keyed to a spec section.

## One model, many types, one primary

Spec: [One model, many types, one primary][spec-005-onemodel].

DRF projects routinely define several serializers per model (public and admin, list and detail,
permission-scoped variants), so one type per model is friction a DRF-shaped package should not
impose. Several `DjangoType`s may register one model; [`spec-018`][spec-018] owns the `Meta.primary`
mechanism that picks the one a relation or a bare `registry.get(model)` resolves to.

- **First-registered wins.** Rejected: it makes import order part of the API contract, the one
  property this section forbids. Nothing in the registry or the finalizer reads registration order.
- **Why duplicate primaries and missing primaries fire at different points.** Two types claiming
  primary is knowable at registration. Ambiguity by omission is not: registration cannot know
  whether a later sibling will claim primary, so a registration-time raise would make the outcome
  depend on import order. It is caught at finalization by
  `django_strawberry_framework/types/finalizer.py::_audit_primary_ambiguity`, which sees the whole
  registry.
- **`TypeRegistry.get` returns `None` for the ambiguous case.**
  `django_strawberry_framework/registry.py::TypeRegistry.get` does not raise there; the raise belongs
  to the finalizer audit, and a caller that must tell ambiguity from absence checks `types_for(model)`.

## Consumer override semantics

Spec: [Consumer override semantics][spec-005-overrides].

`DjangoType.__init_subclass__` merges consumer annotations over synthesized ones
(`django_strawberry_framework/types/base.py::DjangoType.__init_subclass__ #"cls.__annotations__ = {**synthesized, **consumer_annotations}"`),
but the merge order is not what decides an override. A field name in the consumer-authored set
short-circuits synthesis, so the synthesized annotation is never computed for it; relying on the merge
alone would let the consumer win only by dictionary ordering. `name: auto` asks for the model-inferred
type, so it is kept out of the consumer-authored set and routed back into synthesis.

- **Reach into Strawberry internals, route overrides through `strawberry.field`, or add a
  `Meta.field_overrides` key.** None is needed: the plain annotation and the plain assigned field
  already express the override, and the consumer-authored set honors both without touching
  Strawberry internals or adding public API.
- **Restate the four-corner override matrix here.** Rejected: [`spec-010`][spec-010] (relation
  fields) and [`spec-019`][spec-019] (scalar fields) own it. A contract spec owes the edge of its
  claim, not a second telling of the mechanism.

## Invalid `Meta.fields` and `Meta.exclude` names

Spec: [Invalid `Meta.fields` and `Meta.exclude` names][spec-005-selection].

The model + unknowns + available shape lets a consumer fix a typo from the message alone. Because
every field-naming `Meta` key reuses `types/base.py::_format_unknown_fields_error`, the spec states
the obligation a new key inherits rather than listing the keys: a reader who finds a list short still
has the rule.

## Accepted vs deferred Meta keys

Spec: [Accepted vs deferred Meta keys][spec-005-metakeys].

- **Restate the accepted and deferred rosters.** Rejected: a roster in a spec is a copy of
  `ALLOWED_META_KEYS` / `DEFERRED_META_KEYS`, and a copy of an executable set is a second source of
  truth that silently disagrees with the first. `types/base.py` holds the sets and
  `docs/GLOSSARY.md` publishes per-key status; the spec holds the rule.
- **Why the promotion rule is strict.** A key the validator accepts but the pipeline never applies
  reads as shipped and is not, so a key moves only when it is both validated and applied
  end-to-end.
- **Why net-new accepted keys are named.** Most accepted keys never sat in the deferred set: their
  feature shipped in the same change that added the key. Without that route stated, those keys look
  as if they skipped the promotion rule.
- **Why a deferred key's error names a feature, not a spec.** A consumer reading an exception has no
  access to `docs/SPECS/`.

## Coordination

Spec: [Coordination][spec-005-coordination].

A standing instruction that every spec adding a `Meta` key must edit this document is unenforceable:
nothing fails when it is skipped. The obligation is on the code instead, where it is checkable: a
spec adding or promoting a key satisfies the promotion rule inside its own change and lands the
key's glossary entry.

- **Keep the instruction and add a check for it.** Rejected: the check could only compare this
  document's copy of the key set with the real one, which keeps the duplicate alive.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->
[spec-005]: ../spec-005-django_type_contract-0_0_3.md
[spec-005-coordination]: ../spec-005-django_type_contract-0_0_3.md#coordination-with-spec-001-django_types-0_0_1md-and-spec-002-optimizer-0_0_2md
[spec-005-metakeys]: ../spec-005-django_type_contract-0_0_3.md#accepted-vs-deferred-meta-keys
[spec-005-onemodel]: ../spec-005-django_type_contract-0_0_3.md#one-model-many-types-one-primary
[spec-005-overrides]: ../spec-005-django_type_contract-0_0_3.md#consumer-override-semantics
[spec-005-selection]: ../spec-005-django_type_contract-0_0_3.md#invalid-metafields-and-metaexclude-names
[spec-010]: ../spec-010-foundation-0_0_4.md
[spec-018]: ../spec-018-meta_primary-0_0_6.md
[spec-019]: ../spec-019-consumer_overrides_scalar-0_0_6.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
