# Rationale: spec-019 — Consumer override semantics for scalar fields (reasons and rejected alternatives)

Companion to [`spec-019-consumer_overrides_scalar-0_0_6.md`][spec-019]. The spec states the contract; this file records why each Decision is shaped the way it is and which alternatives it rejected.

## [Decision 1 — Annotation-only scalar override collection][spec-019-d1]

- **A single walk-and-bucket loop rejected.** One `for` loop with an `if`/`else` would compress the two comprehensions, but it loses the visual symmetry with the relation collection one line above and makes the two override paths look like they do different things. They are the same logic with a polarity flip.
- **`field.is_relation is False` rejected.** The `not` form is bool-coercion-safe, and `_build_annotations` uses bare `if field.is_relation:`.

## [Decision 2 — `consumer_authored_fields` union shape][spec-019-d2]

**Passing the four sets individually to `_build_annotations` rejected.** The function only needs the union — it does not distinguish the four corners; four parameters would force it to recompute the union or switch on provenance. The override-target validators ask the same single question, so one union serves every reader.

## [Decision 3 — `DjangoTypeDefinition.consumer_annotated_scalar_fields` field][spec-019-d3]

The grouped-by-style order (annotated-relation, annotated-scalar, assigned-relation, assigned-scalar) keeps the dataclass and the collection code reading in the same order.

## [Decision 5 — Test placement and the skipped test's fate][spec-019-d5]

**A smoke-test sibling in `tests/types/test_base.py` rejected.** It adds no coverage the matrix does not already have, and a one-line test sitting alone in another file invites drift between two locations for one contract. The end-to-end SDL check sits at the live tier because a real query observes it.

## [Decision 6 — Why `_consumer_assigned_fields` stays the way it is][spec-019-d6]

Assignments come from `cls.__dict__`, annotations from `cls.__annotations__`: two independent input channels, so the annotation collection is a parallel of the helper rather than an extension of it.

## [Decision 7 — Relay `id` override collision][spec-019-d7]

- **Placement in `_validate_meta` rejected** — too early. It runs over the `Meta` class only and sees neither `consumer_annotations` nor `cls.__dict__`; threading the check through would widen its signature for a single-purpose check.
- **Placement in `_build_annotations` rejected** — too late and wrong-layered. Its job is annotation synthesis; detecting the collision there would entangle consumer override, Relay suppression, and conflict detection inside one per-field loop.
- **A finalize-time `cls.resolve_id_attr()` probe rejected.** It cannot satisfy the class-creation-time raise contract.
- **Raw `typing.get_args(cls.__annotations__["id"])` rejected.** Under PEP 563 or an explicit string annotation the value is a string, `get_args` returns `()`, and the guard would reject the documented escape hatch in stringified form; hence the explicit `isinstance(raw, str)` arm.
- **`typing.get_type_hints` rejected.** It evaluates every annotation on the class, so an unrelated forward reference could mask the `id` verdict, and it handles nested forward references differently on Python 3.10 and 3.11+, which would leave a branch reachable on one interpreter only under a 100% coverage gate. Reading `cls.__annotations__["id"]` directly is interpreter-independent and makes sibling annotations irrelevant by construction.
- **A plain `"NodeID[" in raw` substring test rejected.** It accepts `"NotNodeID[int]"` and `"MyNodeID[int]"`; the `(?:^|\.)` boundary in `_NODEID_STRING_RE` rejects them.
- **Keying the guard on the model's pk name rejected.** It fires against `id: relay.NodeID[int]` (the advertised escape hatch, since `id` is a pk field and lands in `consumer_annotated_scalar_fields`) and against non-`id` pk overrides such as `code: str` on a `CharField(primary_key=True)`, which produce no `Node.id` collision.
- **Allowing assigned `relay.GlobalID` / `strawberry.ID` `id` fields rejected** for a uniform ban: a simpler guard, consistent with the annotation side's "use the supported escape hatch" framing, with `resolve_id` named as the alternative.
- **Loosening the ban for metadata-only `id = strawberry.field(...)` rejected.** The ban removes the only route for attaching `description` / `deprecation_reason` / `directives` to the Relay-supplied `id`; a resolver-backed sibling field is the documented workaround for a rare use case. A metadata-only sibling without a resolver is not one: Strawberry's default resolver looks the name up as an attribute on the model instance and fails at query time.

## [Decision 7a — Converter validation bypass][spec-019-d7a]

1. **Consistency with the relation override path.** Annotation-only relation overrides bypass `convert_relation` through the same `consumer_authored_fields` short-circuit; the scalar contract matches rather than inventing an asymmetry.
2. **Override is escape, not augmentation.** If `convert_scalar`'s validations still fired on overridden fields, an unsupported scalar would keep raising even when the consumer supplied a valid manual annotation — defeating the purpose.

<!-- LINK DEFINITIONS -->

<!-- Root -->

<!-- docs/ -->

<!-- docs/SPECS/ -->
[spec-019-d1]: ../spec-019-consumer_overrides_scalar-0_0_6.md#decision-1--annotation-only-scalar-override-collection
[spec-019-d2]: ../spec-019-consumer_overrides_scalar-0_0_6.md#decision-2--consumer_authored_fields-union-shape
[spec-019-d3]: ../spec-019-consumer_overrides_scalar-0_0_6.md#decision-3--djangotypedefinitionconsumer_annotated_scalar_fields-field
[spec-019-d5]: ../spec-019-consumer_overrides_scalar-0_0_6.md#decision-5--test-placement-and-the-skipped-tests-fate
[spec-019-d6]: ../spec-019-consumer_overrides_scalar-0_0_6.md#decision-6--why-_consumer_assigned_fields-stays-the-way-it-is
[spec-019-d7]: ../spec-019-consumer_overrides_scalar-0_0_6.md#decision-7--relay-id-override-collision
[spec-019-d7a]: ../spec-019-consumer_overrides_scalar-0_0_6.md#decision-7a--converter-validation-bypass
[spec-019]: ../spec-019-consumer_overrides_scalar-0_0_6.md

<!-- docs/builder/ -->

<!-- django_strawberry_framework/ -->

<!-- tests/ -->

<!-- examples/ -->

<!-- scripts/ -->

<!-- .venv/ -->

<!-- External -->
